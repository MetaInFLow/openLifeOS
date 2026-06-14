#!/usr/bin/env python3
"""Create a LifeOS-safe inventory for a local external evidence drive.

The script writes raw file paths only to a private local intake directory.
The optional LifeOS repo output is a public-safe summary with counts, policy,
and routing rules, not file bodies or detailed private paths.
"""

from __future__ import annotations

import argparse
import os
import subprocess
from collections import Counter
from datetime import date
from pathlib import Path


DEFAULT_EXCLUDES = (
    "node_modules",
    ".git",
    "dist",
    "build",
    ".next",
    "__pycache__",
    ".venv",
    "venv",
    ".Trashes",
    ".Spotlight-V100",
    ".fseventsd",
    "System Volume Information",
)

DOC_EXTENSIONS = {
    ".md",
    ".pdf",
    ".doc",
    ".docx",
    ".ppt",
    ".pptx",
    ".xls",
    ".xlsx",
    ".csv",
    ".txt",
    ".url",
}

PROJECT_MARKERS = {
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "setup.py",
    "Cargo.toml",
    "go.mod",
    "pnpm-lock.yaml",
    "yarn.lock",
    "README.md",
    "readme.md",
}

SENSITIVE_KEYWORDS = (
    "contract",
    "contracts",
    "customer",
    "customers",
    "client",
    "feishu",
    "lark",
    "meeting",
    "transcript",
    "finance",
    "financial",
    "invoice",
    "id",
    "passport",
    "credential",
    "secret",
    "token",
    "cookie",
    "private",
    "chat",
    "合同",
    "客户",
    "飞书",
    "会议",
    "转写",
    "财务",
    "发票",
    "身份证",
    "护照",
    "凭证",
    "密钥",
    "私密",
    "聊天",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inventory an external drive for openLifeOS evidence intake."
    )
    parser.add_argument("source", help="Mounted drive path, for example /Volumes/AFElite")
    parser.add_argument(
        "--private-out",
        default="~/LifeOS_Intake/AnthonyHF/external-drive",
        help="Private local output directory for raw inventory files.",
    )
    parser.add_argument(
        "--lifeos-repo",
        help="Optional LifeOS repo path where a public-safe summary should be written.",
    )
    parser.add_argument(
        "--source-id",
        default=None,
        help="Stable source id. Defaults to external-drive-<volume>-<YYYYMMDD>.",
    )
    parser.add_argument(
        "--owner",
        default="AnthonyHF",
        help="Owner/display name used in generated summaries.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing generated inventory files.",
    )
    return parser.parse_args()


def safe_source_id(source: Path, explicit: str | None) -> str:
    if explicit:
        return explicit
    volume = source.name.lower().replace(" ", "-")
    return f"external-drive-{volume}-{date.today().strftime('%Y%m%d')}"


def is_excluded(path: Path) -> bool:
    parts = set(path.parts)
    return any(exclude in parts for exclude in DEFAULT_EXCLUDES)


def extension_for(path: Path) -> str:
    suffix = path.suffix.lower()
    return suffix if suffix else "[no_ext]"


def is_sensitive(path_text: str) -> bool:
    lowered = path_text.lower()
    return any(keyword.lower() in lowered for keyword in SENSITIVE_KEYWORDS)


def disk_info(source: Path) -> dict[str, str]:
    try:
        result = subprocess.run(
            ["diskutil", "info", str(source)],
            check=True,
            capture_output=True,
            text=True,
        )
        parsed: dict[str, str] = {}
        for line in result.stdout.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            parsed[key.strip()] = value.strip()
        filesystem = (
            parsed.get("File System Personality")
            or parsed.get("Name (User Visible)")
            or parsed.get("Type (Bundle)")
            or "unknown"
        )
        return {
            "filesystem": filesystem,
            "size_gb": first_token(parsed.get("Volume Total Space") or parsed.get("Disk Size")),
            "used_gb": first_token(parsed.get("Volume Used Space")),
            "available_gb": first_token(parsed.get("Volume Free Space")),
            "capacity": parsed.get("Capacity In Use By Volumes") or parsed.get("Volume Used Space", "unknown"),
            "mount": parsed.get("Mount Point", str(source)),
        }
    except Exception:
        pass

    try:
        result = subprocess.run(
            ["df", "-g", str(source)],
            check=True,
            capture_output=True,
            text=True,
        )
        lines = [line for line in result.stdout.splitlines() if line.strip()]
        if len(lines) >= 2:
            parts = lines[1].split()
            if len(parts) >= 6:
                return {
                    "filesystem": parts[0],
                    "size_gb": parts[1],
                    "used_gb": parts[2],
                    "available_gb": parts[3],
                    "capacity": parts[4],
                    "mount": parts[-1],
                }
    except Exception:
        pass
    return {
        "filesystem": "unknown",
        "size_gb": "unknown",
        "used_gb": "unknown",
        "available_gb": "unknown",
        "capacity": "unknown",
        "mount": str(source),
    }


def first_token(value: str | None) -> str:
    if not value:
        return "unknown"
    parts = value.split()
    if len(parts) >= 2 and parts[1] == "GB":
        return f"{parts[0]} GB"
    return parts[0] if parts else "unknown"


def write_text(path: Path, text: str, force: bool) -> None:
    if path.exists() and not force:
        raise SystemExit(f"Refusing to overwrite {path}; pass --force")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    args = parse_args()
    source = Path(args.source).expanduser().resolve()
    if not source.exists() or not source.is_dir():
        raise SystemExit(f"Source is not a mounted directory: {source}")

    private_out = Path(args.private_out).expanduser().resolve()
    private_out.mkdir(parents=True, exist_ok=True)
    source_id = safe_source_id(source, args.source_id)
    info = disk_info(source)

    raw_paths: list[str] = []
    filtered_paths: list[str] = []
    doc_candidates: list[str] = []
    sensitive_docs: list[str] = []
    project_roots: set[str] = set()
    top_counts: Counter[str] = Counter()
    ext_counts: Counter[str] = Counter()

    for root, dirs, files in os.walk(source):
        dirs[:] = [directory for directory in dirs if directory not in DEFAULT_EXCLUDES]
        root_path = Path(root)
        for file_name in files:
            absolute = root_path / file_name
            try:
                relative = absolute.relative_to(source).as_posix()
            except ValueError:
                continue
            raw_paths.append(relative)
            if is_excluded(Path(relative)):
                continue
            filtered_paths.append(relative)
            top = relative.split("/", 1)[0]
            top_counts[top] += 1
            ext = extension_for(Path(relative))
            ext_counts[ext] += 1
            if ext in DOC_EXTENSIONS:
                doc_candidates.append(relative)
                if is_sensitive(relative):
                    sensitive_docs.append(relative)
            if file_name in PROJECT_MARKERS:
                parent = str(Path(relative).parent)
                if parent != ".":
                    project_roots.add(parent)

    write_text(private_out / "source.yml", "\n".join(
        [
            f"source_id: {source_id}",
            f"owner: {args.owner}",
            f"mount: {source}",
            f"generated: {date.today().isoformat()}",
            "policy: local-private-inventory-no-body-copy",
            "",
        ]
    ), args.force)
    write_text(private_out / "file-list.txt", "\n".join(raw_paths) + "\n", args.force)
    write_text(private_out / "file-list.filtered.txt", "\n".join(filtered_paths) + "\n", args.force)
    write_text(private_out / "top-level-counts.txt", "\n".join(
        f"{count} {name}" for name, count in top_counts.most_common()
    ) + "\n", args.force)
    write_text(private_out / "extension-counts.txt", "\n".join(
        f"{count} {name}" for name, count in ext_counts.most_common()
    ) + "\n", args.force)
    write_text(private_out / "project-root-candidates.txt", "\n".join(sorted(project_roots)) + "\n", args.force)
    write_text(private_out / "document-candidates.txt", "\n".join(doc_candidates) + "\n", args.force)
    write_text(private_out / "sensitive-document-candidates.txt", "\n".join(sensitive_docs) + "\n", args.force)

    summary = render_private_summary(source, source_id, info, filtered_paths, top_counts)
    write_text(private_out / "intake-summary.md", summary, args.force)

    if args.lifeos_repo:
        repo = Path(args.lifeos_repo).expanduser().resolve()
        public_path = repo / "docs" / "evidence-intake" / f"{source_id}.md"
        write_text(
            public_path,
            render_public_summary(args.owner, source_id, source.name, info, private_out, filtered_paths, top_counts),
            args.force,
        )

    print(f"wrote private intake: {private_out}")
    if args.lifeos_repo:
        print(f"wrote public-safe LifeOS summary: {public_path}")
    print(f"filtered_files={len(filtered_paths)} project_roots={len(project_roots)} documents={len(doc_candidates)} sensitive_documents={len(sensitive_docs)}")
    return 0


def render_private_summary(
    source: Path,
    source_id: str,
    info: dict[str, str],
    filtered_paths: list[str],
    top_counts: Counter[str],
) -> str:
    top_lines = "\n".join(f"- {name}: {count:,} files" for name, count in top_counts.most_common(10))
    return f"""# {source.name} External Drive Intake Summary

Source ID: `{source_id}`
Source: `{source}`
Generated: {date.today().isoformat()}
Policy: inventory only, no body copy

## Disk

- Mount: `{info['mount']}`
- Filesystem: `{info['filesystem']}`
- Size: {info['size_gb']}
- Used: {info['used_gb']}
- Free: {info['available_gb']}
- Capacity: {info['capacity']}

## Inventory

- Filtered files: {len(filtered_paths):,}
- Excluded from filtered list: {', '.join(DEFAULT_EXCLUDES)}

## Top Buckets

{top_lines}

## Next Suggested Pass

1. Select 10-20 high-value project outputs from `project-root-candidates.txt`.
2. Select owner-approved public-safe documents from `document-candidates.txt`.
3. Avoid `sensitive-document-candidates.txt` unless processing is explicitly approved.
4. Write only summaries, provenance pointers, and abstracted patterns into LifeOS.
"""


def render_public_summary(
    owner: str,
    source_id: str,
    volume_name: str,
    info: dict[str, str],
    private_out: Path,
    filtered_paths: list[str],
    top_counts: Counter[str],
) -> str:
    top_lines = "\n".join(f"- `{name}`: {count:,} files" for name, count in top_counts.most_common(10))
    private_display = display_path(private_out)
    return f"""# External Drive Evidence Intake

Date: {date.today().isoformat()}
Owner: {owner}
Source ID: `{source_id}`
Status: `inventory_created_body_not_processed`
Visibility: `local-only-index`

## Summary

The local external drive `{volume_name}` is available as a private evidence source for LifeOS alignment and future synthesis.

This public LifeOS repo records only the intake summary and routing policy. It does not copy raw file bodies, private documents, customer material, contracts, Feishu exports, datasets, source repositories, or secrets from the drive.

## Local Intake Location

Local private inventory files are stored outside this repo:

- `{private_display}/source.yml`
- `{private_display}/file-list.txt`
- `{private_display}/file-list.filtered.txt`
- `{private_display}/top-level-counts.txt`
- `{private_display}/extension-counts.txt`
- `{private_display}/project-root-candidates.txt`
- `{private_display}/document-candidates.txt`
- `{private_display}/sensitive-document-candidates.txt`
- `{private_display}/intake-summary.md`

## Inventory Result

- Mounted volume: `{volume_name}`
- Mount: `{info['mount']}`
- Filesystem: `{info['filesystem']}`
- Size: {info['size_gb']}
- Used: {info['used_gb']}
- Free: {info['available_gb']}
- Filtered file count: {len(filtered_paths):,}

Top-level buckets after excluding dependency/build/system noise:

{top_lines}

Excluded from the filtered list:

- `{ "`, `".join(DEFAULT_EXCLUDES) }`

## Initial Routing

| Bucket | LifeOS Use | Policy |
| --- | --- | --- |
| Code | project evidence, IPO Reverse candidates, skill evidence | index first; do not copy repos into public LifeOS |
| Datasets | research/data source provenance | index only unless a specific approved skill needs dataset evidence |
| Documents | Wenxin/PSP/memory evidence candidates | private-by-default; owner approval required before summarization |

## Sensitive Zones

These categories are private-by-default and must not be copied into the public repo:

- contracts
- customer materials
- Feishu/Lark exports or links
- raw meeting transcripts
- financial records
- identity documents
- tokens, credentials, cookies, keys
- private chats
- dataset bodies
- source repository bodies

## Next Pass

Recommended next action is a selective, owner-approved evidence pass:

1. Pick 10-20 high-value project outputs from the Code bucket for IPO Reverse.
2. Pick explicitly approved public-safe documents for Wenxin/public profile.
3. Pick behavior or judgment samples for PSP only after owner approval.
4. Keep dataset material as provenance/index unless a specific skill needs it.

## Maturity Impact

This intake creates source availability but does not by itself increase LifeOS maturity beyond `scaffold`. Maturity can move to `evidence-limited-v0` after approved evidence bodies are summarized into Wenxin, PSP, skill recommendations, or memory pointers with provenance.
"""


def display_path(path: Path) -> str:
    try:
        home = Path.home().resolve()
        resolved = path.resolve()
        if resolved == home:
            return "~"
        return f"~/{resolved.relative_to(home).as_posix()}"
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
