#!/usr/bin/env python3
"""Migrate generated LifeOS repositories between schema revisions."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
REVISION_0002_PATH = ROOT / "migrations" / "versions" / "0002_lifeos_schema_v2.py"
REVISION_0003_PATH = ROOT / "migrations" / "versions" / "0003_lifeos_schema_v2_refine_living_fs.py"
REVISION_0004_PATH = ROOT / "migrations" / "versions" / "0004_root_agent_entrypoint.py"
REVISION_0005_PATH = ROOT / "migrations" / "versions" / "0005_lifeos_schema_v3_governed_artifact_repo.py"

BASE_REVISION = "0001_openlifeos_base"
REVISION_0002 = "0002_lifeos_schema_v2"
REVISION_0003 = "0003_lifeos_schema_v2_refine_living_fs"
REVISION_0004 = "0004_root_agent_entrypoint"
REVISION_0005 = "0005_lifeos_schema_v3_governed_artifact_repo"
HEAD_REVISION = REVISION_0005

REVISION_ORDER = (
    BASE_REVISION,
    REVISION_0002,
    REVISION_0003,
    REVISION_0004,
    REVISION_0005,
)

REVISION_ALIASES = {
    "v2": REVISION_0002,
    "v2-refined": REVISION_0003,
    "root-agent": REVISION_0004,
    "v3": REVISION_0005,
    "governed": REVISION_0005,
    "latest": HEAD_REVISION,
    "head": HEAD_REVISION,
}


def load_revision(path: Path, module_name: str) -> tuple[dict[str, str], dict[str, str]]:
    module = load_revision_module(path, module_name)
    return dict(module.STRUCTURAL_MOVES), dict(module.TEXT_REWRITES)


def load_revision_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load migration revision: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def merge_move(source: Path, target: Path) -> None:
    if not source.exists() and not source.is_symlink():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() or target.is_symlink():
        if source.is_dir() and not source.is_symlink() and target.is_dir() and not target.is_symlink():
            for child in source.iterdir():
                merge_move(child, target / child.name)
            source.rmdir()
            return
        raise FileExistsError(f"Refusing to overwrite existing target: {target}")
    shutil.move(str(source), str(target))


def rewrite_text_file(path: Path, rewrites: dict[str, str]) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False
    updated = text
    for old, new in rewrites.items():
        updated = updated.replace(old, new)
    updated = updated.replace("identity/identity/design/", "identity/design/")
    updated = updated.replace("runtime/runtime/profiles/", "runtime/profiles/")
    updated = updated.replace("work/work/apps/", "work/apps/")
    updated = updated.replace("integrations/integrations/agents/", "integrations/agents/")
    if updated == text:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def iter_text_candidates(root: Path):
    for path in root.rglob("*"):
        if ".git" in path.parts or path.is_dir() or path.is_symlink():
            continue
        if path.suffix in {"", ".md", ".yml", ".yaml", ".json", ".txt"}:
            yield path


def update_status(root: Path, revision: str, *, schema_version: str = "v2") -> bool:
    status = root / "LIFEOS_STATUS.yml"
    if not status.exists():
        return False
    text = status.read_text(encoding="utf-8")
    updated = text
    if "lifeos_schema:" not in updated:
        updated = updated.rstrip() + f"\nlifeos_schema: {schema_version}\n"
    else:
        lines = [f"lifeos_schema: {schema_version}" if line.startswith("lifeos_schema:") else line for line in updated.splitlines()]
        updated = "\n".join(lines) + "\n"
    if "schema_revision:" not in updated:
        updated = updated.rstrip() + f"\nschema_revision: {revision}\n"
    else:
        lines = [f"schema_revision: {revision}" if line.startswith("schema_revision:") else line for line in updated.splitlines()]
        updated = "\n".join(lines) + "\n"
    if updated == text:
        return False
    status.write_text(updated, encoding="utf-8")
    return True


def write_migration_report(root: Path, revision: str, report: dict[str, object]) -> None:
    report_dir = root / "legacy" / "migration-reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / f"{revision}.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def read_status_value(root: Path, key: str) -> str:
    status = root / "LIFEOS_STATUS.yml"
    if not status.exists():
        return ""
    for raw in status.read_text(encoding="utf-8").splitlines():
        if raw.startswith(f"{key}:"):
            return raw.split(":", 1)[1].strip().strip('"').strip("'")
    return ""


def infer_current_revision(root: Path) -> str:
    """Infer schema revision for repos created before schema_revision existed."""
    explicit = read_status_value(root, "schema_revision")
    if explicit in REVISION_ORDER:
        return explicit

    if read_status_value(root, "lifeos_schema") == "v3" or (
        (root / "sources" / "CATALOG.md").exists()
        and (root / "taste" / "current.yml").exists()
        and (root / "meta-skills" / "current.yml").exists()
        and (root / "publication" / "current.yml").exists()
    ):
        return REVISION_0005

    matrix = root / "matrix.yml"
    matrix_text = matrix.read_text(encoding="utf-8") if matrix.exists() else ""
    if (root / "AGENT.md").exists() and "root_agent:" in matrix_text:
        return REVISION_0004
    if (
        (root / "evolution" / "organ-systems").exists()
        and (root / "identity" / "memories").exists()
        and (root / "identity" / "cognition").exists()
        and not any((root / rel).exists() for rel in ("skills", "memory", "cognition", "intake", "roles"))
    ):
        return REVISION_0003
    if read_status_value(root, "lifeos_schema") == "v2" or (root / "integrations" / "agents").exists():
        return REVISION_0002
    return BASE_REVISION


def strip_skill_frontmatter(text: str) -> tuple[str, bool]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return text, False
    for index in range(1, min(len(lines), 80)):
        if lines[index].strip() == "---":
            stripped = "\n".join(lines[index + 1 :]).lstrip("\n")
            return stripped + ("\n" if text.endswith("\n") else ""), True
    return text, False


ZH_AGENT_STATUS_APPENDIX = """

## Skill 调用方式

`AGENT.md` 只做阅读、路由和状态判断。需要真正执行生产流程时，进入对应 Skill 的 `SKILL.md`：

- InnerAtlas / 问心：读取 `evolution/organ-systems/wenxin/SKILL.md`。
- PSP：读取 `evolution/organ-systems/psp/SKILL.md`。
- IPO Reverse：读取 `evolution/organ-systems/ipo-reverse/SKILL.md`。
- Taste Generator：读取 `evolution/organ-systems/taste-generator/SKILL.md`；用于生成审美选择页、汇总 owner 选择，先更新 `DESIGN_TASTE.xml`，再生成 `DESIGN.md`。
- Owner-grown capabilities：读取 `capabilities/<capability-id>/SKILL.md`；候选 Skill 未提升前不要当作可安装 Skill 调用。

## 当前状态和对齐判断

判断当前 avatar 是否对齐时，必须同时看五层：

1. 结构门禁：在 openLifeOS factory 中运行 `python scripts/doctor_avatar_repo.py <this-lifeos-repo> --json`，读取 `required_completion`、`overall_completion`、`life_stage`、`required_failed` 和 `next_actions`。
2. 内容成熟度：读取 doctor JSON 的 `content_maturity` 和 `skill_content_maturity`，重点看 InnerAtlas、PSP、skill_recommendations、avatar_description 和 Design 的字段完整度、证据覆盖和缺口。
3. Owner alignment：读取 `evolution/alignment/current.yml`、`docs/lifeos-content-review.md`，以及 artifact 中的 `pending-owner-response`、`interaction_needed` 或 `owner_confirmation_required`。
4. 证据成熟度：读取 `docs/evidence-sufficiency.md` 和 `identity/psp/<person-id>/current/EVIDENCE_MATURITY.xml`。
5. 运行活跃度：读取 `runtime/sessions/`、`runtime/runtime-skills/`、`runtime/runtime-lessons/`、`evolution/ipo/` 和 `capabilities/`。

输出状态时必须同时说明：结构完成度、内容成熟度、owner alignment 是否 pending、证据成熟度、当前 lifecycle stage、下一步最小动作。
"""

EN_AGENT_STATUS_APPENDIX = """

## How To Call Skills

`AGENT.md` only handles reading, routing, and status judgment. When a production workflow needs to run, enter the relevant Skill's `SKILL.md`:

- InnerAtlas / Wenxin: read `evolution/organ-systems/wenxin/SKILL.md`.
- PSP: read `evolution/organ-systems/psp/SKILL.md`.
- IPO Reverse: read `evolution/organ-systems/ipo-reverse/SKILL.md`.
- Taste Generator: read `evolution/organ-systems/taste-generator/SKILL.md` to generate a design selector, summarize owner choices, update `DESIGN_TASTE.xml` first, then generate `DESIGN.md`.
- Owner-grown capabilities: read `capabilities/<capability-id>/SKILL.md`; candidate Skills are not installable Skills until promoted.

## Status And Alignment

Judge avatar alignment across five layers:

1. Structure gate: from the openLifeOS factory, run `python scripts/doctor_avatar_repo.py <this-lifeos-repo> --json`; read `required_completion`, `overall_completion`, `life_stage`, `required_failed`, and `next_actions`.
2. Content maturity: read `content_maturity` and `skill_content_maturity` in doctor JSON, especially InnerAtlas, PSP, skill_recommendations, avatar_description, and Design.
3. Owner alignment: read `evolution/alignment/current.yml`, `docs/lifeos-content-review.md`, and artifact markers such as `pending-owner-response`, `interaction_needed`, or `owner_confirmation_required`.
4. Evidence maturity: read `docs/evidence-sufficiency.md` and `identity/psp/<person-id>/current/EVIDENCE_MATURITY.xml`.
5. Runtime activity: read `runtime/sessions/`, `runtime/runtime-skills/`, `runtime/runtime-lessons/`, `evolution/ipo/`, and `capabilities/`.

When reporting status, include structure completion, content maturity, whether owner alignment is pending, evidence maturity, the current lifecycle stage, and the next smallest action.
"""


def configured_language(root: Path) -> str:
    matrix = root / "matrix.yml"
    if not matrix.exists():
        return "zh-CN"
    for raw in matrix.read_text(encoding="utf-8").splitlines():
        if raw.startswith("language:"):
            return raw.split(":", 1)[1].strip().strip('"').strip("'")
    return "zh-CN"


def convert_root_agent_text(text: str, rewrites: dict[str, str], language: str) -> tuple[str, bool]:
    updated, changed = strip_skill_frontmatter(text)
    for old, new in rewrites.items():
        if old in updated:
            updated = updated.replace(old, new)
            changed = True
    if "本文件不是可安装 Codex Skill" not in updated and "This file is not an installable Codex Skill" not in updated:
        lines = updated.splitlines()
        if lines and lines[0].startswith("# "):
            insert_at = 1
            lines.insert(
                insert_at,
                "\n本文件不是可安装 Codex Skill；它告诉 agent 如何阅读 avatar、调用真正的 Skill、判断状态和 owner alignment。"
                if language != "en-US"
                else "\nThis file is not an installable Codex Skill; it tells an agent how to read the avatar, call real Skills, and judge status and owner alignment.",
            )
            updated = "\n".join(lines).rstrip() + "\n"
            changed = True
    if "doctor_avatar_repo.py" not in updated or "skill_content_maturity" not in updated or "EVIDENCE_MATURITY.xml" not in updated:
        updated = updated.rstrip() + (EN_AGENT_STATUS_APPENDIX if language == "en-US" else ZH_AGENT_STATUS_APPENDIX)
        if not updated.endswith("\n"):
            updated += "\n"
        changed = True
    return updated, changed


def migrate_root_agent_entrypoint(root: Path) -> dict[str, object]:
    root = root.expanduser().resolve()
    _, rewrites_map = load_revision(REVISION_0004_PATH, "lifeos_schema_0004")
    language = configured_language(root)
    moves: list[dict[str, str]] = []
    rewrites: list[str] = []
    archived: list[dict[str, str]] = []

    root_skill = root / "SKILL.md"
    root_agent = root / "AGENT.md"
    if root_skill.exists() and not root_agent.exists():
        shutil.move(str(root_skill), str(root_agent))
        moves.append({"from": "SKILL.md", "to": "AGENT.md"})
    elif root_skill.exists() and root_agent.exists():
        archive = root / "legacy" / "root-entrypoints" / "SKILL.0004_root_agent_entrypoint.md"
        archive.parent.mkdir(parents=True, exist_ok=True)
        if not archive.exists():
            shutil.move(str(root_skill), str(archive))
            archived.append({"from": "SKILL.md", "to": str(archive.relative_to(root))})
        else:
            root_skill.unlink()
            archived.append({"from": "SKILL.md", "to": "removed; archive already exists"})

    if root_agent.exists():
        text = root_agent.read_text(encoding="utf-8")
        updated, changed = convert_root_agent_text(text, rewrites_map, language)
        if changed:
            root_agent.write_text(updated, encoding="utf-8")
            rewrites.append("AGENT.md")

    for path in iter_text_candidates(root):
        if path == root_agent:
            continue
        if rewrite_text_file(path, rewrites_map):
            rewrites.append(str(path.relative_to(root)))

    status_updated = update_status(root, REVISION_0004)
    report = {
        "schema_version": "v2",
        "revision": REVISION_0004,
        "down_revision": REVISION_0003,
        "moves": moves,
        "archived": archived,
        "rewrites": sorted(set(rewrites)),
        "status_updated": status_updated,
    }
    write_migration_report(root, REVISION_0004, report)
    return report


def migrate_v1_to_v2(root: Path) -> dict[str, object]:
    root = root.expanduser().resolve()
    moves_map, rewrites_map = load_revision(REVISION_0002_PATH, "lifeos_schema_0002")
    moves: list[dict[str, str]] = []
    rewrites: list[str] = []
    for source_rel, target_rel in moves_map.items():
        source = root / source_rel
        target = root / target_rel
        if source.exists() or source.is_symlink():
            merge_move(source, target)
            moves.append({"from": source_rel, "to": target_rel})

    for path in iter_text_candidates(root):
        if rewrite_text_file(path, rewrites_map):
            rewrites.append(str(path.relative_to(root)))

    status_updated = update_status(root, REVISION_0002)
    report = {
        "schema_version": "v2",
        "revision": REVISION_0002,
        "moves": moves,
        "rewrites": rewrites,
        "status_updated": status_updated,
    }
    write_migration_report(root, REVISION_0002, report)
    return report


def remove_empty_dirs(root: Path, rels: tuple[str, ...]) -> list[str]:
    removed: list[str] = []
    for rel in rels:
        path = root / rel
        if path.exists() and path.is_dir():
            try:
                path.rmdir()
                removed.append(rel)
            except OSError:
                pass
    return removed


REFINED_SKELETON_READMES = {
    "metabolism/processing/README.md": "# Metabolism Processing\n\nExtraction jobs, normalization state, risk flags, and evidence packets waiting for owner review.\n",
    "metabolism/extracted/README.md": "# Metabolism Extracted\n\nOwner-approved derived evidence packets ready for LifeOS routing.\n",
    "runtime/runtime-profile/README.md": "# Runtime Profile\n\nRuntime context, recent sessions, temporary limits, and adapter state.\n",
    "evolution/alignment/README.md": "# Alignment\n\nOwner alignment, corrections, disagreement reviews, and promotion confirmations.\n",
    "evolution/mutations/README.md": "# Mutations\n\nProposed LifeOS changes that require evidence, review, owner alignment, and version records.\n",
}


def ensure_v3_skeleton(root: Path) -> list[str]:
    module = load_revision_module(REVISION_0005_PATH, "lifeos_schema_0005")
    created: list[str] = []
    for rel, text in module.V3_SKELETON_FILES.items():
        path = root / rel
        if path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        created.append(rel)
    return created


def ensure_v3_artifact_sections(root: Path) -> bool:
    module = load_revision_module(REVISION_0005_PATH, "lifeos_schema_0005_artifacts")
    path = root / "artifacts" / "current.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(
            "schema: openlifeos.artifacts-current.v1\n"
            "artifacts:\n"
            f"{module.V3_ARTIFACT_SECTIONS}",
            encoding="utf-8",
        )
        return True
    text = path.read_text(encoding="utf-8")
    additions: list[str] = []
    for marker, section in (
        ("  sources:", _extract_artifact_section(module.V3_ARTIFACT_SECTIONS, "sources")),
        ("  taste:", _extract_artifact_section(module.V3_ARTIFACT_SECTIONS, "taste")),
        ("  meta_skills:", _extract_artifact_section(module.V3_ARTIFACT_SECTIONS, "meta_skills")),
        ("  publication:", _extract_artifact_section(module.V3_ARTIFACT_SECTIONS, "publication")),
    ):
        if marker not in text:
            additions.append(section)
    if not additions:
        return False
    if "artifacts:" not in text:
        text = text.rstrip() + "\nartifacts:\n"
    updated = text.rstrip() + "\n" + "".join(additions)
    path.write_text(updated, encoding="utf-8")
    return True


def _extract_artifact_section(sections: str, key: str) -> str:
    lines = sections.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line == f"  {key}:":
            start = index
            break
    if start is None:
        return ""
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("  ") and not lines[index].startswith("    "):
            end = index
            break
    return "\n".join(lines[start:end]) + "\n"


def ensure_refined_skeleton(root: Path) -> list[str]:
    created: list[str] = []
    for rel, text in REFINED_SKELETON_READMES.items():
        path = root / rel
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            created.append(rel)
    return created


def migrate_v2_refine_living_fs(root: Path) -> dict[str, object]:
    root = root.expanduser().resolve()
    moves_map, rewrites_map = load_revision(REVISION_0003_PATH, "lifeos_schema_0003")
    moves: list[dict[str, str]] = []
    rewrites: list[str] = []
    for source_rel, target_rel in moves_map.items():
        source = root / source_rel
        target = root / target_rel
        if source.exists() or source.is_symlink():
            merge_move(source, target)
            moves.append({"from": source_rel, "to": target_rel})

    removed_empty = remove_empty_dirs(root, ("skills/self-evolution", "skills/content", "skills", "memory", "cognition", "intake", "roles"))
    created_skeleton = ensure_refined_skeleton(root)

    for path in iter_text_candidates(root):
        if rewrite_text_file(path, rewrites_map):
            rewrites.append(str(path.relative_to(root)))

    status_updated = update_status(root, REVISION_0003)
    report = {
        "schema_version": "v2",
        "revision": REVISION_0003,
        "moves": moves,
        "removed_empty_dirs": removed_empty,
        "created_skeleton": created_skeleton,
        "rewrites": rewrites,
        "status_updated": status_updated,
    }
    write_migration_report(root, REVISION_0003, report)
    return report


def migrate_v3_governed_artifact_repo(root: Path) -> dict[str, object]:
    root = root.expanduser().resolve()
    _, rewrites_map = load_revision(REVISION_0005_PATH, "lifeos_schema_0005")
    created_skeleton = ensure_v3_skeleton(root)
    artifact_registry_updated = ensure_v3_artifact_sections(root)
    rewrites: list[str] = []
    for path in iter_text_candidates(root):
        if rewrite_text_file(path, rewrites_map):
            rewrites.append(str(path.relative_to(root)))
    status_updated = update_status(root, REVISION_0005, schema_version="v3")
    report = {
        "schema_version": "v3",
        "revision": REVISION_0005,
        "down_revision": REVISION_0004,
        "created_skeleton": created_skeleton,
        "artifact_registry_updated": artifact_registry_updated,
        "rewrites": rewrites,
        "status_updated": status_updated,
    }
    write_migration_report(root, REVISION_0005, report)
    return report


MigrationFn = Callable[[Path], dict[str, object]]


MIGRATION_FUNCTIONS: dict[str, MigrationFn] = {
    REVISION_0002: migrate_v1_to_v2,
    REVISION_0003: migrate_v2_refine_living_fs,
    REVISION_0004: migrate_root_agent_entrypoint,
    REVISION_0005: migrate_v3_governed_artifact_repo,
}


def resolve_target_revision(alias: str) -> str:
    revision = REVISION_ALIASES.get(alias, alias)
    if revision not in REVISION_ORDER:
        raise ValueError(f"Unknown migration target: {alias}")
    return revision


def migrate_to_revision(root: Path, target_revision: str) -> dict[str, object]:
    root = root.expanduser().resolve()
    target_revision = resolve_target_revision(target_revision)
    current_revision = infer_current_revision(root)
    current_index = REVISION_ORDER.index(current_revision)
    target_index = REVISION_ORDER.index(target_revision)
    if current_index > target_index:
        raise ValueError(f"Cannot downgrade from {current_revision} to {target_revision}")

    applied: list[dict[str, object]] = []
    for revision in REVISION_ORDER[current_index + 1 : target_index + 1]:
        fn = MIGRATION_FUNCTIONS[revision]
        applied.append(fn(root))

    report = {
        "schema_version": "v3" if target_revision == REVISION_0005 else "v2",
        "from_revision": current_revision,
        "to_revision": target_revision,
        "applied_revisions": [item["revision"] for item in applied],
        "up_to_date": not applied,
        "reports": applied,
    }
    write_migration_report(root, f"upgrade_to_{target_revision}", report)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", help="LifeOS repo path")
    parser.add_argument(
        "--to",
        choices=sorted(REVISION_ALIASES),
        default="latest",
        help="Migration target alias. Use latest/head for the newest schema revision.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = migrate_to_revision(Path(args.target), args.to)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
