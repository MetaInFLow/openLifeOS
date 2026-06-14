#!/usr/bin/env python3
"""Refresh the structured avatar description from approved openLifeOS evidence.

The default synthesis pass is intentionally conservative: it refreshes source
refs, claim evidence, derived_from, evidence level and timestamp while preserving
existing product-facing claim text. Claim text changes are allowed only through
an explicit approved claims manifest.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import re
from pathlib import Path


CLAIM_FIELDS = ["one_line", "current_role", "operating_mode", "strengths", "boundaries"]
LIST_FIELDS = {"operating_mode", "strengths", "boundaries", "source_refs", "derived_from"}
SCALAR_FIELDS = {"schema", "display_name", "one_line", "current_role", "evidence_level", "maturity_notice", "updated_at"}


@dataclass
class SynthesisResult:
    path: Path
    changed_fields: list[str]
    source_refs: list[str]
    derived_from: list[str]


@dataclass
class ApprovedClaim:
    value: str
    evidence: list[str]


@dataclass
class ApprovedClaimsManifest:
    reviewer: str
    approved_at: str
    approval_ref: str
    claims: dict[str, ApprovedClaim]


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _path_exists(root: Path, rel: str) -> bool:
    if rel.startswith("active.") or rel.startswith("source_id:") or rel.startswith("owner-approved-summary:"):
        return True
    if rel.startswith("private:"):
        return False
    return (root / rel).exists()


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def parse_avatar_description(text: str) -> dict[str, object]:
    data: dict[str, object] = {"claim_evidence": {}}
    current_key: str | None = None
    current_claim_key: str | None = None
    in_claim_evidence = False

    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if not raw_line.startswith(" "):
            in_claim_evidence = False
            current_claim_key = None
            if ":" not in raw_line:
                continue
            key, value = raw_line.split(":", 1)
            key = key.strip()
            value = value.strip()
            current_key = key
            if key == "claim_evidence":
                in_claim_evidence = True
                data["claim_evidence"] = {}
            elif key in LIST_FIELDS:
                data[key] = []
            elif key in SCALAR_FIELDS:
                data[key] = _strip_quotes(value)
            else:
                data[key] = _strip_quotes(value)
            continue

        if in_claim_evidence:
            claim_match = re.match(r"^\s{2}([A-Za-z0-9_-]+):\s*$", raw_line)
            if claim_match:
                current_claim_key = claim_match.group(1)
                claim_evidence = data.setdefault("claim_evidence", {})
                assert isinstance(claim_evidence, dict)
                claim_evidence[current_claim_key] = []
                continue
            item_match = re.match(r"^\s{4}-\s+(.+?)\s*$", raw_line)
            if item_match and current_claim_key:
                claim_evidence = data.setdefault("claim_evidence", {})
                assert isinstance(claim_evidence, dict)
                values = claim_evidence.setdefault(current_claim_key, [])
                assert isinstance(values, list)
                values.append(_strip_quotes(item_match.group(1)))
            continue

        item_match = re.match(r"^\s{2}-\s+(.+?)\s*$", raw_line)
        if item_match and current_key in LIST_FIELDS:
            values = data.setdefault(current_key, [])
            assert isinstance(values, list)
            values.append(_strip_quotes(item_match.group(1)))

    return data


def parse_artifact_entrypoints(text: str) -> dict[str, dict[str, str]]:
    artifacts: dict[str, dict[str, str]] = {}
    current_artifact: str | None = None
    in_artifacts = False

    for raw_line in text.splitlines():
        if raw_line.startswith("artifacts:"):
            in_artifacts = True
            continue
        if not in_artifacts:
            continue
        artifact_match = re.match(r"^\s{2}([A-Za-z0-9_-]+):\s*$", raw_line)
        if artifact_match:
            current_artifact = artifact_match.group(1)
            artifacts[current_artifact] = {}
            continue
        field_match = re.match(r"^\s{4}([A-Za-z0-9_-]+):\s+(.+?)\s*$", raw_line)
        if field_match and current_artifact:
            artifacts[current_artifact][field_match.group(1)] = _strip_quotes(field_match.group(2))

    return artifacts


def parse_approved_claims(text: str) -> ApprovedClaimsManifest:
    claims: dict[str, ApprovedClaim] = {}
    current_field: str | None = None
    in_approved = False
    in_evidence = False
    in_approval = False
    reviewer = ""
    approved_at = ""
    approval_ref = ""

    for raw_line in text.splitlines():
        if raw_line.startswith("approval:"):
            in_approval = True
            in_approved = False
            continue
        if raw_line.startswith("approved_claims:"):
            in_approved = True
            in_approval = False
            continue
        if in_approval:
            approval_match = re.match(r"^\s{2}(reviewer|approved_at|approval_ref):\s+(.+?)\s*$", raw_line)
            if approval_match:
                key = approval_match.group(1)
                value = _strip_quotes(approval_match.group(2))
                if key == "reviewer":
                    reviewer = value
                elif key == "approved_at":
                    approved_at = value
                elif key == "approval_ref":
                    approval_ref = value
            continue
        if not in_approved:
            continue
        field_match = re.match(r"^\s{2}([A-Za-z0-9_-]+):\s*$", raw_line)
        if field_match:
            current_field = field_match.group(1)
            in_evidence = False
            claims[current_field] = ApprovedClaim(value="", evidence=[])
            continue
        value_match = re.match(r"^\s{4}value:\s+(.+?)\s*$", raw_line)
        if value_match and current_field:
            claims[current_field].value = _strip_quotes(value_match.group(1))
            in_evidence = False
            continue
        if re.match(r"^\s{4}evidence:\s*$", raw_line) and current_field:
            in_evidence = True
            continue
        item_match = re.match(r"^\s{6}-\s+(.+?)\s*$", raw_line)
        if item_match and current_field and in_evidence:
            claims[current_field].evidence.append(_strip_quotes(item_match.group(1)))

    filtered_claims = {
        field: claim
        for field, claim in claims.items()
        if field in CLAIM_FIELDS and claim.value and claim.evidence
    }
    if filtered_claims and not (reviewer and approved_at and approval_ref):
        raise ValueError("Approved avatar-description claims require approval.reviewer, approval.approved_at and approval.approval_ref")
    return ApprovedClaimsManifest(
        reviewer=reviewer,
        approved_at=approved_at,
        approval_ref=approval_ref,
        claims=filtered_claims,
    )


def active_evidence_refs(root: Path, artifacts: dict[str, dict[str, str]]) -> dict[str, list[str]]:
    wenxin = artifacts.get("wenxin", {})
    psp = artifacts.get("psp", {})
    evidence = artifacts.get("evidence_maturity", {})

    refs = {
        "one_line": [wenxin.get("current_entrypoint"), wenxin.get("active_artifact")],
        "current_role": [wenxin.get("current_entrypoint"), psp.get("current_entrypoint")],
        "operating_mode": [psp.get("current_entrypoint"), psp.get("active_artifact")],
        "strengths": [wenxin.get("current_entrypoint"), psp.get("current_entrypoint")],
        "boundaries": [
            psp.get("current_entrypoint"),
            evidence.get("current_entrypoint"),
        ],
    }
    return {
        field: [ref for ref in _dedupe([item for item in items if item]) if _path_exists(root, ref)]
        for field, items in refs.items()
    }


def write_avatar_description(path: Path, data: dict[str, object], evidence: dict[str, list[str]]) -> None:
    lines: list[str] = []
    lines.append(f"schema: {data.get('schema') or 'openlifeos.avatar-description.v1'}")
    lines.append(f"display_name: {data.get('display_name') or 'Unknown Avatar'}")
    lines.append(f"one_line: {_quote(str(data.get('one_line') or 'Current avatar description is not evidence-complete yet.'))}")
    lines.append(f"current_role: {_quote(str(data.get('current_role') or 'Current role is not structured yet.'))}")
    lines.append(f"evidence_level: {data.get('evidence_level') or 'insufficient'}")
    lines.append(
        "maturity_notice: "
        + _quote(
            str(
                data.get("maturity_notice")
                or "This product-facing description is a structured summary derived from multiple active openLifeOS artifacts, not a single markdown file."
            )
        )
    )

    for field in ["operating_mode", "strengths", "boundaries", "source_refs"]:
        lines.append(f"{field}:")
        values = data.get(field) or []
        assert isinstance(values, list)
        if values:
            for item in values:
                lines.append(f"  - {_quote(str(item))}" if field in {"operating_mode", "strengths", "boundaries"} else f"  - {item}")
        elif field != "source_refs":
            lines.append("  - \"Not structured yet.\"")

    lines.append("claim_evidence:")
    for field in CLAIM_FIELDS:
        lines.append(f"  {field}:")
        for ref in evidence.get(field, []):
            lines.append(f"    - {ref}")

    lines.append("derived_from:")
    derived_from = data.get("derived_from") or []
    assert isinstance(derived_from, list)
    for ref in derived_from:
        lines.append(f"  - {ref}")
    lines.append(f"updated_at: {_quote(str(data.get('updated_at') or ''))}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def append_changelog(root: Path, timestamp: str, changed_fields: list[str]) -> None:
    changelog = root / "identity" / "avatar-description" / "changelog.md"
    fields = ", ".join(changed_fields) if changed_fields else "none"
    entry = (
        f"\n## {timestamp} synthesis\n\n"
        f"- Refreshed structured avatar description source refs, derived_from, and field-level claim evidence.\n"
        f"- Changed claim fields from approved manifest: {fields}.\n"
        f"- Default synthesis preserves claim text unless explicitly approved evidence is provided.\n"
    )
    existing = _read_text(changelog)
    changelog.write_text(existing.rstrip() + entry + "\n", encoding="utf-8")


def synthesize_avatar_description(
    root: Path,
    approved_claims_path: Path | None = None,
    timestamp: str | None = None,
    write_changelog: bool = True,
) -> SynthesisResult:
    root = root.expanduser().resolve()
    timestamp = timestamp or datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    description_path = root / "identity" / "avatar-description" / "current.yml"
    artifacts_path = root / "artifacts" / "current.yml"

    if not description_path.exists():
        raise FileNotFoundError(f"Missing avatar description: {description_path}")
    if not artifacts_path.exists():
        raise FileNotFoundError(f"Missing artifacts registry: {artifacts_path}")

    data = parse_avatar_description(_read_text(description_path))
    artifacts = parse_artifact_entrypoints(_read_text(artifacts_path))
    evidence = active_evidence_refs(root, artifacts)
    changed_fields: list[str] = []

    if approved_claims_path:
        manifest = parse_approved_claims(_read_text(approved_claims_path))
        for field, claim in manifest.claims.items():
            missing_refs = [ref for ref in claim.evidence if not _path_exists(root, ref)]
            if missing_refs:
                raise ValueError(f"Approved claim {field} references missing or disallowed evidence: {', '.join(missing_refs)}")
            if data.get(field) != claim.value:
                changed_fields.append(field)
            data[field] = claim.value
            evidence[field] = _dedupe([f"approval:{manifest.approval_ref}", *claim.evidence])

    source_refs = _dedupe(
        ["identity/avatar-description/current.yml"]
        + [ref for refs in evidence.values() for ref in refs]
    )
    derived_from = _dedupe(
        [
            artifacts.get("wenxin", {}).get("active_artifact") or artifacts.get("wenxin", {}).get("current_entrypoint"),
            artifacts.get("psp", {}).get("active_artifact") or artifacts.get("psp", {}).get("current_entrypoint"),
            artifacts.get("design", {}).get("active_artifact") or artifacts.get("design", {}).get("current_entrypoint"),
            artifacts.get("evidence_maturity", {}).get("current_entrypoint"),
        ]
    )
    source_refs = [ref for ref in source_refs if _path_exists(root, ref)]
    derived_from = [ref for ref in derived_from if _path_exists(root, ref)]

    data["source_refs"] = source_refs
    data["derived_from"] = derived_from
    data["updated_at"] = timestamp
    if source_refs and data.get("evidence_level") == "insufficient":
        data["evidence_level"] = "partial"

    write_avatar_description(description_path, data, evidence)
    if write_changelog:
        append_changelog(root, timestamp, changed_fields)

    return SynthesisResult(
        path=description_path,
        changed_fields=changed_fields,
        source_refs=source_refs,
        derived_from=derived_from,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", help="Avatar repo directory")
    parser.add_argument(
        "--approved-claims",
        help="Optional approved avatar-description claim manifest. Without this, claim text is preserved.",
    )
    parser.add_argument("--timestamp", help="Override updated_at timestamp for repeatable runs")
    parser.add_argument("--no-changelog", action="store_true", help="Do not append synthesis entry to changelog")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = synthesize_avatar_description(
        Path(args.target),
        approved_claims_path=Path(args.approved_claims) if args.approved_claims else None,
        timestamp=args.timestamp,
        write_changelog=not args.no_changelog,
    )
    print(f"Updated {result.path}")
    print(f"Changed claim fields: {', '.join(result.changed_fields) if result.changed_fields else 'none'}")
    print(f"Source refs: {len(result.source_refs)}")
    print(f"Derived refs: {len(result.derived_from)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
