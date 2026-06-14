#!/usr/bin/env python3
"""Validate the structure and public-safety basics of a LifeOS avatar repo."""

from __future__ import annotations

import argparse
import re
import xml.etree.ElementTree as ET
from pathlib import Path


BASE_REQUIRED_PATHS = [
    "LIFEOS_STATUS.yml",
    "DELIVERY.md",
    "LIFEOS-CATALOG.html",
    "replicateme.yml",
    "README.md",
    "AGENT.md",
    "DESIGN.md",
    "matrix.yml",
    "artifacts/README.md",
    "artifacts/current.yml",
    "identity/README.md",
    "identity/current.yml",
    "identity/avatar-description/current.yml",
    "identity/avatar-description/versions.yml",
    "identity/avatar-description/changelog.md",
    "identity/public-profile/profile.yml",
    "identity/inneratlas/ARTIFACTS.xml",
    "identity/inneratlas/current/INNERATLAS_REPORT.xml",
    "identity/wenxin/versions.yml",
    "identity/wenxin/changelog.md",
    "metabolism/inbox/README.md",
    "metabolism/processing/README.md",
    "metabolism/extracted/README.md",
    "runtime/README.md",
    "runtime/sessions/README.md",
    "runtime/runtime-skills/README.md",
    "runtime/runtime-lessons/README.md",
    "runtime/runtime-profile/README.md",
    "runtime/memory/working-lessons/README.md",
    "evolution/README.md",
    "evolution/ipo/README.md",
    "evolution/alignment/README.md",
    "evolution/mutations/README.md",
    "capabilities/README.md",
    "identities/README.md",
    "work/README.md",
    "integrations/README.md",
    "integrations/github.yml",
    "integrations/feishu.yml",
    "integrations/hermes.yml",
    "integrations/data-sources.yml",
    "identity/wenxin/skill-summaries/README.md",
    "integrations/skill-sources/default-skills/README.md",
    "integrations/skill-sources/default-skills/self-evolution.md",
    "integrations/skill-sources/default-skills/skill-updates.yml",
    "docs/skill-system/runtime-skill-candidates.md",
    "identity/wenxin/skill-recommendations.yml",
    "security/README.md",
    "security/permissions.yml",
    "docs/README.md",
    "docs/evidence-sufficiency.md",
    "docs/self-evolution-output-standards.md",
]

V3_REQUIRED_PATHS = [
    "CATALOG.md",
    "sources/CATALOG.md",
    "sources/authority.yml",
    "sources/raw/README.md",
    "sources/processed/README.md",
    "sources/indexes/README.md",
    "sources/packets/README.md",
    "taste/README.md",
    "taste/current.yml",
    "taste/text/README.md",
    "taste/image/README.md",
    "taste/interface/README.md",
    "taste/brand/README.md",
    "taste/references/README.md",
    "meta-skills/README.md",
    "meta-skills/current.yml",
    "meta-skills/skills/README.md",
    "meta-skills/candidates/README.md",
    "publication/README.md",
    "publication/current.yml",
    "publication/profile/README.md",
    "publication/bio/README.md",
    "publication/positioning/README.md",
    "publication/website/README.md",
    "publication/media-kit/README.md",
    "publication/talks/README.md",
    "publication/articles/README.md",
    "publication/public-claims.yml",
    "governance/README.md",
    "governance/schemas/README.md",
    "governance/policies/README.md",
    "governance/decisions/README.md",
]

BASE_REQUIRED_PATH_OPTIONS = [
    ("agents/openai.yaml", "integrations/agents/openai.yaml"),
    ("design/README.md", "identity/design/README.md"),
    ("design/versions.yml", "identity/design/versions.yml"),
    ("design/changelog.md", "identity/design/changelog.md"),
    ("scripts/update_default_skills.py", "legacy/scripts/update_default_skills.py"),
    ("cognition/README.md", "identity/cognition/README.md"),
    ("cognition/object-taxonomy.yml", "identity/cognition/object-taxonomy.yml"),
    ("cognition/data-contracts.yml", "identity/cognition/data-contracts.yml"),
    ("cognition/skill-bindings/README.md", "identity/cognition/skill-bindings/README.md"),
    ("cognition/skill-bindings/data-sources.yml", "identity/cognition/skill-bindings/data-sources.yml"),
    ("skills/README.md", "legacy/skills-v1/README.md"),
    ("skills/self-evolution/wenxin/SKILL.md", "evolution/organ-systems/wenxin/SKILL.md"),
    ("skills/self-evolution/psp/SKILL.md", "evolution/organ-systems/psp/SKILL.md"),
    ("skills/self-evolution/ipo-reverse/SKILL.md", "evolution/organ-systems/ipo-reverse/SKILL.md"),
    ("memory/README.md", "identity/memories/README.md"),
    ("memory/START-HERE.md", "identity/memories/START-HERE.md"),
    ("memory/wiki-repo.yml", "identity/memories/wiki-repo.yml"),
    ("memory/working-lessons/README.md", "runtime/memory/working-lessons/README.md"),
    ("memory/long-term/README.md", "identity/memories/long-term/README.md"),
    ("memory/distilled-knowledge/README.md", "capabilities/memory/distilled-knowledge/README.md"),
    ("intake/README.md", "metabolism/inbox/README.md"),
    ("roles/README.md", "identities/README.md"),
]

V2_ALLOWED_TOP_LEVEL_DIRS = {
    "artifacts",
    "capabilities",
    "docs",
    "evolution",
    "identity",
    "identities",
    "integrations",
    "legacy",
    "metabolism",
    "runtime",
    "security",
    "work",
}

V3_ALLOWED_TOP_LEVEL_DIRS = V2_ALLOWED_TOP_LEVEL_DIRS | {
    "sources",
    "taste",
    "meta-skills",
    "publication",
    "governance",
}

V2_DISALLOWED_TOP_LEVEL_DIRS = {
    "agents",
    "apps",
    "profiles",
    "scripts",
    "design",
    "life",
    "system",
    "skills",
    "memory",
    "cognition",
    "intake",
    "roles",
}

EVOLVED_REQUIRED_PATHS = [
    "capabilities/engineering-everything/SKILL.md",
    "evolution/organ-systems/cognitive-alignment/SKILL.md",
    "identity/wenxin/skill-summaries/engineering-everything.md",
]

SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "api key assignment": re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][^'\"\s]{12,}"),
    "github token": re.compile(r"gh[pousr]_[A-Za-z0-9_]{30,}"),
    "openai key": re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
}

TEXT_SUFFIXES = {
    "",
    ".md",
    ".txt",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".csv",
    ".xml",
}

AVATAR_DESCRIPTION_REQUIRED_MARKERS = [
    "schema: openlifeos.avatar-description.v1",
    "display_name:",
    "one_line:",
    "current_role:",
    "evidence_level:",
    "maturity_notice:",
    "operating_mode:",
    "strengths:",
    "boundaries:",
    "source_refs:",
    "claim_evidence:",
    "derived_from:",
]

AVATAR_DESCRIPTION_CLAIM_EVIDENCE_KEYS = [
    "one_line",
    "current_role",
    "operating_mode",
    "strengths",
    "boundaries",
]

ARTIFACT_REGISTRY_REQUIRED_ARTIFACTS = [
    "avatar_description",
    "wenxin",
    "psp",
    "design",
    "skill_recommendations",
    "evidence_maturity",
]

V3_ARTIFACT_REGISTRY_REQUIRED_ARTIFACTS = [
    "sources",
    "taste",
    "meta_skills",
    "publication",
]

ARTIFACT_REGISTRY_REQUIRED_FIELDS = [
    "semantic_role",
    "current_entrypoint",
    "status",
    "evidence_sufficiency",
]

ARTIFACT_REGISTRY_ANSWER_REQUIRED = set(ARTIFACT_REGISTRY_REQUIRED_ARTIFACTS)

AVATAR_DESCRIPTION_CLAIM_APPROVAL_MARKERS = [
    "avatar_description_claim_approval:",
    "schema: openlifeos.avatar-description-synthesis.v1",
    "current_entrypoint: identity/avatar-description/current.yml",
    "approved_manifest_shape:",
    "approval:",
    "approved_claims:",
    "allowed_fields:",
    "required_fields_per_claim:",
    "evidence_rules:",
    "failure_rules:",
]

AVATAR_DESCRIPTION_CLAIM_APPROVAL_REQUIRED_TERMS = [
    "reviewer",
    "approved_at",
    "approval_ref",
    "one_line",
    "current_role",
    "operating_mode",
    "strengths",
    "boundaries",
    "value",
    "evidence",
    "missing approval metadata fails synthesis",
    "missing or disallowed evidence refs fail synthesis",
]


def is_external_skill_template(path: Path, root: Path) -> bool:
    try:
        rel = path.relative_to(root)
    except ValueError:
        return False
    return (
        len(rel.parts) >= 3
        and (
            (rel.parts[0] == "skills" and rel.parts[1] == "self-evolution")
            or (rel.parts[0] == "evolution" and rel.parts[1] == "organ-systems")
        )
    )


def iter_text_files(root: Path):
    for path in root.rglob("*"):
        if ".git" in path.parts or path.is_dir() or path.is_symlink():
            continue
        if path.suffix in TEXT_SUFFIXES:
            yield path


def artifact_registry_section(text: str, artifact_key: str) -> str:
    match = re.search(rf"^\s{{2}}{re.escape(artifact_key)}:\s*$([\s\S]*?)(?=^\s{{2}}\S|\Z)", text, re.MULTILINE)
    return match.group(1) if match else ""


def artifact_registry_has_field(section: str, field: str) -> bool:
    return bool(re.search(rf"^\s{{4}}{re.escape(field)}:\s*(.+)$", section, re.MULTILINE))


def validate_artifact_registry_roles(root: Path, failures: list[str]) -> None:
    artifacts_current = root / "artifacts" / "current.yml"
    if not artifacts_current.exists():
        failures.append("Missing required path: artifacts/current.yml")
        return

    artifacts_text = artifacts_current.read_text(encoding="utf-8")
    required_artifacts = list(ARTIFACT_REGISTRY_REQUIRED_ARTIFACTS)
    if lifeos_schema_version(root) == "v3":
        required_artifacts.extend(V3_ARTIFACT_REGISTRY_REQUIRED_ARTIFACTS)

    for artifact_key in required_artifacts:
        section = artifact_registry_section(artifacts_text, artifact_key)
        if not section:
            failures.append(f"artifacts/current.yml missing {artifact_key}")
            continue
        for field in ARTIFACT_REGISTRY_REQUIRED_FIELDS:
            if not artifact_registry_has_field(section, field):
                failures.append(f"artifacts/current.yml {artifact_key} missing {field}")
        if artifact_key in ARTIFACT_REGISTRY_ANSWER_REQUIRED and not artifact_registry_has_field(section, "answers"):
            failures.append(f"artifacts/current.yml {artifact_key} missing answers")
        if artifact_key == "avatar_description" and not re.search(
            r"^\s{4}semantic_role:\s*product_facing_current_avatar_description\s*$",
            section,
            re.MULTILINE,
        ):
            failures.append("artifacts/current.yml avatar_description semantic_role must be product_facing_current_avatar_description")


def validate_avatar_description(root: Path, failures: list[str]) -> None:
    avatar_description = root / "identity" / "avatar-description" / "current.yml"
    artifacts_current = root / "artifacts" / "current.yml"

    if not avatar_description.exists():
        failures.append("Missing required path: identity/avatar-description/current.yml")
        return
    if not artifacts_current.exists():
        failures.append("Missing required path: artifacts/current.yml")
        return

    description_text = avatar_description.read_text(encoding="utf-8")
    artifacts_text = artifacts_current.read_text(encoding="utf-8")

    for marker in AVATAR_DESCRIPTION_REQUIRED_MARKERS:
        if marker not in description_text:
            failures.append(f"identity/avatar-description/current.yml missing {marker.rstrip(':')}")

    for key in AVATAR_DESCRIPTION_CLAIM_EVIDENCE_KEYS:
        if not re.search(rf"^\s{{2}}{re.escape(key)}:\s*$", description_text, re.MULTILINE):
            failures.append(f"identity/avatar-description/current.yml missing claim_evidence.{key}")

    if "avatar_description:" not in artifacts_text:
        failures.append("artifacts/current.yml missing avatar_description")
    if "current_entrypoint: identity/avatar-description/current.yml" not in artifacts_text:
        failures.append("artifacts/current.yml avatar_description must point to identity/avatar-description/current.yml")


def validate_avatar_description_claim_approval_contract(root: Path, failures: list[str]) -> None:
    data_contracts = root / "identity" / "cognition" / "data-contracts.yml"
    if not data_contracts.exists():
        data_contracts = root / "cognition" / "data-contracts.yml"
    if not data_contracts.exists():
        failures.append("Missing required path: identity/cognition/data-contracts.yml")
        return

    text = data_contracts.read_text(encoding="utf-8")
    for marker in AVATAR_DESCRIPTION_CLAIM_APPROVAL_MARKERS:
        if marker not in text:
            failures.append(f"{data_contracts.relative_to(root)} missing avatar description claim approval marker: {marker.rstrip(':')}")
    for term in AVATAR_DESCRIPTION_CLAIM_APPROVAL_REQUIRED_TERMS:
        if term not in text:
            failures.append(f"{data_contracts.relative_to(root)} missing avatar description claim approval term: {term}")


def lifeos_schema_version(root: Path) -> str:
    status = root / "LIFEOS_STATUS.yml"
    if not status.exists():
        return "v1"
    text = status.read_text(encoding="utf-8")
    match = re.search(r"^lifeos_schema:\s*['\"]?([^'\"\n]+)['\"]?\s*$", text, re.MULTILINE)
    return match.group(1).strip() if match else "v1"


def validate_required_path_options(root: Path, failures: list[str]) -> None:
    for options in BASE_REQUIRED_PATH_OPTIONS:
        if not any((root / rel).exists() for rel in options):
            failures.append("Missing required path option: " + " or ".join(options))


def taste_generator_configured(root: Path) -> bool:
    for rel in ("matrix.yml", "integrations/skill-sources/default-skills/skill-updates.yml"):
        path = root / rel
        if path.exists() and "taste-generator" in path.read_text(encoding="utf-8"):
            return True
    return False


def validate_taste_generator_route(root: Path, failures: list[str]) -> None:
    if not taste_generator_configured(root):
        return
    if not (root / "evolution/organ-systems/taste-generator/SKILL.md").exists():
        failures.append(
            "Missing required taste-generator Skill: evolution/organ-systems/taste-generator/SKILL.md"
        )


def validate_v2_top_level(root: Path, failures: list[str], strict_v2: bool = False) -> None:
    schema_version = lifeos_schema_version(root)
    if not strict_v2 and schema_version not in {"v2", "v3"}:
        return
    allowed = V3_ALLOWED_TOP_LEVEL_DIRS if schema_version == "v3" else V2_ALLOWED_TOP_LEVEL_DIRS
    for path in root.iterdir():
        if not path.is_dir() or path.name == ".git":
            continue
        if path.name not in allowed:
            failures.append(f"LifeOS schema {schema_version} disallows top-level directory: {path.name}")
        if strict_v2 and path.name in V2_DISALLOWED_TOP_LEVEL_DIRS:
            failures.append(f"Strict LifeOS schema {schema_version} disallows legacy top-level directory: {path.name}")


def configured_language(root: Path) -> str:
    matrix = root / "matrix.yml"
    if not matrix.exists():
        return "zh-CN"
    match = re.search(r"^language:\s*['\"]?([^'\"\n]+)['\"]?\s*$", matrix.read_text(encoding="utf-8"), re.MULTILINE)
    return match.group(1).strip() if match else "zh-CN"


def xml_child_text(element: ET.Element | None, name: str) -> str:
    if element is None:
        return ""
    child = element.find(name)
    if child is None or child.text is None:
        return ""
    return child.text.strip()


def validate_psp_language_contract(root: Path, failures: list[str]) -> None:
    expected = configured_language(root)
    supported = {"zh-CN", "en-US"}
    for path in sorted((root / "identity" / "psp").glob("*/current/PSP_REPORT.xml")) + sorted((root / "identity" / "psp").glob("*/current/EVIDENCE_MATURITY.xml")):
        try:
            xml_root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            failures.append(f"{path.relative_to(root)} is not valid XML: {exc}")
            continue
        root_language = (xml_root.get("language") or "").strip()
        contract_language = xml_child_text(xml_root.find("language_contract"), "output_language")
        metadata_language = xml_child_text(xml_root.find("metadata"), "output_language")
        if root_language not in supported:
            failures.append(f"{path.relative_to(root)} missing supported root language")
        if contract_language not in supported:
            failures.append(f"{path.relative_to(root)} missing supported language_contract/output_language")
        if metadata_language not in supported:
            failures.append(f"{path.relative_to(root)} missing supported metadata/output_language")
        if root_language and contract_language and root_language != contract_language:
            failures.append(f"{path.relative_to(root)} language mismatch: root={root_language}, contract={contract_language}")
        if contract_language and metadata_language and contract_language != metadata_language:
            failures.append(f"{path.relative_to(root)} language mismatch: contract={contract_language}, metadata={metadata_language}")
        if root_language and expected and root_language != expected:
            failures.append(f"{path.relative_to(root)} language {root_language} does not match matrix.yml language {expected}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", help="Avatar repo directory")
    parser.add_argument(
        "--mode",
        choices=["base", "evolved"],
        default="base",
        help="base validates deterministic init output; evolved also requires owner-grown sample-room artifacts",
    )
    parser.add_argument(
        "--strict-v2",
        action="store_true",
        help="fail if v1/v1.5 legacy top-level directories exist; intended for fresh v2 baseline validation",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.target).expanduser().resolve()
    failures: list[str] = []
    warnings: list[str] = []

    if not root.exists():
        raise SystemExit(f"Target does not exist: {root}")

    schema_version = lifeos_schema_version(root)
    required_paths = list(BASE_REQUIRED_PATHS)
    if schema_version == "v3":
        required_paths.extend(V3_REQUIRED_PATHS)
    if args.mode == "evolved":
        required_paths.extend(EVOLVED_REQUIRED_PATHS)

    for rel in required_paths:
        if not (root / rel).exists():
            failures.append(f"Missing required path: {rel}")
    validate_required_path_options(root, failures)
    validate_taste_generator_route(root, failures)
    validate_v2_top_level(root, failures, strict_v2=args.strict_v2)

    validate_avatar_description(root, failures)
    validate_artifact_registry_roles(root, failures)
    validate_avatar_description_claim_approval_contract(root, failures)

    if not list((root / "identity" / "psp").glob("*/versions/PSP_REPORT.*.xml")):
        failures.append("Missing required PSP scaffold: identity/psp/<person-id>/versions/PSP_REPORT.<timestamp>.xml")

    if not list((root / "identity" / "psp").glob("*/versions/EVIDENCE_MATURITY.*.xml")):
        failures.append("Missing required PSP evidence maturity scaffold: identity/psp/<person-id>/versions/EVIDENCE_MATURITY.<timestamp>.xml")

    if not list((root / "design").glob("DESIGN-*.md")) and not list((root / "identity" / "design").glob("DESIGN-*.md")):
        failures.append("Missing required Design scaffold: design/DESIGN-<timestamp>.md or identity/design/DESIGN-<timestamp>.md")

    if not list((root / "identity" / "psp").glob("*/current/PSP_REPORT.xml")):
        failures.append("Missing required PSP current entrypoint: identity/psp/<person-id>/current/PSP_REPORT.xml")

    if not list((root / "identity" / "psp").glob("*/current/EVIDENCE_MATURITY.xml")):
        failures.append("Missing required evidence maturity current entrypoint: identity/psp/<person-id>/current/EVIDENCE_MATURITY.xml")

    validate_psp_language_contract(root, failures)

    if not list((root / "identity" / "inneratlas" / "versions").glob("INNERATLAS_REPORT.*.xml")):
        failures.append("Missing required InnerAtlas versioned artifact: identity/inneratlas/versions/INNERATLAS_REPORT.<timestamp>.xml")

    if not list((root / "identity" / "psp").glob("*/current.yml")):
        failures.append("Missing PSP active registry: identity/psp/<person-id>/current.yml")

    if not list((root / "identity" / "psp").glob("*/versions.yml")):
        failures.append("Missing PSP versions ledger: identity/psp/<person-id>/versions.yml")

    if not list((root / "identity" / "psp").glob("*/changelog.md")):
        failures.append("Missing PSP changelog: identity/psp/<person-id>/changelog.md")

    if not list((root / "identity" / "psp").glob("*/update-log-*.md")):
        failures.append("Missing required PSP update log: identity/psp/<person-id>/update-log-<timestamp>.md")

    if not list((root / "identity" / "psp").glob("*/INITIALIZATION.md")):
        failures.append("Missing PSP initialization adapter: identity/psp/<person-id>/INITIALIZATION.md")

    for path in iter_text_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            warnings.append(f"Skipped non-UTF8 text-like file: {path.relative_to(root)}")
            continue

        if not is_external_skill_template(path, root) and ("{{" in text or "}}" in text):
            failures.append(f"Unresolved template token in {path.relative_to(root)}")

        for name, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                failures.append(f"Possible {name} in {path.relative_to(root)}")

    if failures:
        print("Validation failed:")
        for item in failures:
            print(f"- {item}")
    else:
        print("Validation passed.")

    if warnings:
        print("Warnings:")
        for item in warnings:
            print(f"- {item}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
