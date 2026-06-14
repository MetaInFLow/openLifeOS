#!/usr/bin/env python3
"""Report completion progress for an openLifeOS repo."""

from __future__ import annotations

import argparse
from datetime import date, datetime
import json
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from replicateme_yaml import as_bool, as_list, read_flat_yaml


ROOT = Path(__file__).resolve().parents[1]
VALIDATE_SCRIPT = ROOT / "scripts" / "validate_avatar_repo.py"


@dataclass(frozen=True)
class Check:
    label: str
    fn: Callable[["RepoContext"], tuple[bool, str]]


@dataclass(frozen=True)
class Phase:
    id: str
    name: str
    required: bool
    expected_outputs: tuple[str, ...]
    checks: tuple[Check, ...]


@dataclass
class CheckResult:
    label: str
    passed: bool
    detail: str


@dataclass
class PhaseResult:
    id: str
    name: str
    required: bool
    expected_outputs: tuple[str, ...]
    checks: list[CheckResult]

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)


class RepoContext:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.config = read_flat_yaml(root / "replicateme.yml")

    def path(self, rel: str) -> Path:
        return self.root / rel

    def exists(self, rel: str) -> bool:
        path = self.path(rel)
        return path.exists() and path.suffix != ".tmpl"

    def template_exists(self, rel: str) -> bool:
        return self.path(rel + ".tmpl").exists()

    def read(self, rel: str) -> str:
        path = self.path(rel)
        if not path.exists():
            return ""
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return ""

    def files(self, rel: str) -> list[Path]:
        base = self.path(rel)
        if not base.exists():
            return []
        return [
            path
            for path in base.rglob("*")
            if path.is_file() and ".git" not in path.parts and path.suffix != ".tmpl"
        ]


@dataclass(frozen=True)
class LifeStage:
    stage_id: int
    stage_name: str
    age_days: int | None
    age_label: str
    stage_reason: str
    data_flow: tuple[str, ...]


def ok(message: str) -> tuple[bool, str]:
    return True, message


def fail(message: str) -> tuple[bool, str]:
    return False, message


def parse_status_date(text: str, field: str) -> date | None:
    match = re.search(rf"^{re.escape(field)}:\s*['\"]?([^'\"\n]+)['\"]?\s*$", text, re.MULTILINE)
    if not match:
        return None
    raw = match.group(1).strip()
    if not raw:
        return None
    normalized = raw.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized).date()
    except ValueError:
        try:
            return date.fromisoformat(raw[:10])
        except ValueError:
            return None


def age_label(age_days: int | None) -> str:
    if age_days is None:
        return "unknown"
    if age_days < 30:
        return f"{age_days} 天"
    months = max(1, round(age_days / 30))
    return f"约 {months} 个月"


def meaningful_files(ctx: RepoContext, rel: str) -> list[Path]:
    ignored_names = {"README.md", "index.md", ".gitkeep"}
    return [
        path
        for path in ctx.files(rel)
        if path.name not in ignored_names and not path.name.endswith(".tmpl")
    ]


def artifact_registry_section_text(ctx: RepoContext, artifact_key: str) -> str:
    text = ctx.read("artifacts/current.yml")
    if not text:
        return ""
    match = re.search(rf"^\s{{2}}{re.escape(artifact_key)}:\s*$([\s\S]*?)(?=^\s{{2}}\S|\Z)", text, re.MULTILINE)
    return match.group(1) if match else ""


def artifact_registry_field(ctx: RepoContext, artifact_key: str, field: str) -> str:
    section = artifact_registry_section_text(ctx, artifact_key)
    if not section:
        return ""
    match = re.search(rf"^\s{{4}}{re.escape(field)}:\s*(.+)$", section, re.MULTILINE)
    return match.group(1).strip().strip("'\"") if match else ""


def evidence_backed_artifact(ctx: RepoContext, artifact_key: str, fallback_exists: bool) -> bool:
    maturity = evidence_maturity(ctx)
    if maturity == "scaffold":
        return False

    status = artifact_registry_field(ctx, artifact_key, "status").lower()
    sufficiency = artifact_registry_field(ctx, artifact_key, "evidence_sufficiency").lower()
    if status or sufficiency:
        if status in {"scaffold", "template", "placeholder", "intake-only"}:
            return False
        if sufficiency in {"partial", "sufficient", "reviewed"}:
            return fallback_exists

    return fallback_exists


def lifecycle_age(ctx: RepoContext) -> tuple[int | None, str]:
    status = ctx.read("LIFEOS_STATUS.yml")
    created = parse_status_date(status, "created_at") or parse_status_date(status, "birth_date")
    observed = parse_status_date(status, "updated_at") or date.today()
    if not created:
        return None, "unknown"
    days = max(0, (observed - created).days)
    return days, age_label(days)


def diagnose_life_stage(root: Path) -> LifeStage:
    ctx = RepoContext(root)
    age_days, label = lifecycle_age(ctx)
    has_intake = (ctx.exists("metabolism/inbox") and bool(meaningful_files(ctx, "metabolism/inbox"))) or (
        ctx.exists("intake") and bool(meaningful_files(ctx, "intake"))
    )
    has_wenxin_artifact = (
        ctx.exists("identity/inneratlas/current/INNERATLAS_REPORT.xml")
        or ctx.exists("identity/wenxin/WENXIN_REPORT.md")
        or ctx.exists("identity/wenxin/WENXIN_REPORT.html")
        or bool(meaningful_files(ctx, "identity/wenxin/reports"))
    )
    has_psp_artifact = bool(meaningful_files(ctx, "identity/psp"))
    has_wenxin = evidence_backed_artifact(ctx, "wenxin", has_wenxin_artifact)
    has_psp = evidence_backed_artifact(ctx, "psp", has_psp_artifact)
    has_sessions = bool(meaningful_files(ctx, "runtime/sessions"))
    has_runtime_skills = bool(meaningful_files(ctx, "runtime/runtime-skills"))
    has_runtime_lessons = bool(meaningful_files(ctx, "runtime/runtime-lessons"))
    has_ipo = bool(meaningful_files(ctx, "evolution/ipo"))
    has_capabilities = bool(meaningful_files(ctx, "capabilities"))

    stages: tuple[tuple[int, str, bool, str], ...] = (
        (8, "Meta Skill Formation", has_capabilities, "capabilities contains promoted durable capability artifacts"),
        (7, "IPO Running", has_ipo, "evolution/ipo contains IPO review artifacts"),
        (6, "Runtime Lesson", has_runtime_lessons, "runtime/runtime-lessons contains local lesson artifacts"),
        (5, "Runtime Skill", has_runtime_skills, "runtime/runtime-skills contains local runtime skill artifacts"),
        (4, "Cloud Runtime", has_sessions, "runtime/sessions contains session artifacts"),
        (3, "PSP Complete", has_psp, "identity/psp contains PSP/person-model artifacts"),
        (2, "Wenxin Complete", has_wenxin, "identity/wenxin contains Wenxin self-discovery artifacts"),
        (1, "Evidence Intake", has_intake, "intake contains unprocessed source material"),
    )
    for stage_id, stage_name, matched, reason in stages:
        if matched:
            return LifeStage(
                stage_id,
                stage_name,
                age_days,
                label,
                reason,
                (
                    "metabolism/inbox",
                    "runtime/sessions",
                    "runtime/runtime-skills",
                    "runtime/runtime-lessons",
                    "evolution/ipo",
                    "capabilities",
                ),
            )
    return LifeStage(
        0,
        "Kernel Scaffold",
        age_days,
        label,
        "only scaffold/body structure is detectable; no digested identity or runtime activity artifacts found",
        (
            "metabolism/inbox",
            "runtime/sessions",
            "runtime/runtime-skills",
            "runtime/runtime-lessons",
            "evolution/ipo",
            "capabilities",
        ),
    )


def unique_hits(markers: tuple[str, ...], text: str) -> list[str]:
    hits: list[str] = []
    for marker in markers:
        if marker in text and marker not in hits:
            hits.append(marker)
    return hits


def file_exists(rel: str) -> Callable[[RepoContext], tuple[bool, str]]:
    def check(ctx: RepoContext) -> tuple[bool, str]:
        if not ctx.exists(rel) and ctx.template_exists(rel):
            return fail(f"template-only: {rel}.tmpl exists but {rel} is missing")
        return ok(rel) if ctx.exists(rel) else fail(f"missing {rel}")

    return check


def contains(rel: str, patterns: tuple[str, ...]) -> Callable[[RepoContext], tuple[bool, str]]:
    def check(ctx: RepoContext) -> tuple[bool, str]:
        if not ctx.exists(rel) and ctx.template_exists(rel):
            return fail(f"template-only: {rel}.tmpl exists but {rel} is missing")
        text = ctx.read(rel)
        missing = [pattern for pattern in patterns if pattern not in text]
        if missing:
            return fail(f"{rel} missing: {', '.join(missing)}")
        return ok(rel)

    return check


def no_pending_markers(rel: str) -> Callable[[RepoContext], tuple[bool, str]]:
    def check(ctx: RepoContext) -> tuple[bool, str]:
        if not ctx.exists(rel) and ctx.template_exists(rel):
            return fail(f"template-only: {rel}.tmpl exists but {rel} is missing")
        text = ctx.read(rel)
        if not text:
            return fail(f"missing or unreadable {rel}")
        markers = ("TODO", "todo", "scaffold", "example:")
        hits = unique_hits(markers, text)
        if hits:
            return fail(f"{rel} still has pending markers: {', '.join(hits)}")
        return ok(rel)

    return check


def matrix_field(name: str, allowed: tuple[str, ...] | None = None) -> Callable[[RepoContext], tuple[bool, str]]:
    def check(ctx: RepoContext) -> tuple[bool, str]:
        matrix = ctx.read("matrix.yml")
        match = re.search(rf"^{re.escape(name)}:\s*['\"]?([^'\"\n]+)['\"]?\s*$", matrix, re.MULTILINE)
        if not match:
            return fail(f"matrix.yml missing {name}")
        value = match.group(1).strip()
        if not value or value == "TODO":
            return fail(f"matrix.yml has empty {name}")
        if allowed and value not in allowed:
            return fail(f"matrix.yml {name}={value}; expected one of {', '.join(allowed)}")
        return ok(f"{name}: {value}")

    return check


def configured_language(ctx: RepoContext) -> str:
    matrix = ctx.read("matrix.yml")
    match = re.search(r"^language:\s*['\"]?([^'\"\n]+)['\"]?\s*$", matrix, re.MULTILINE)
    return match.group(1).strip() if match else "zh-CN"


def child_text(element: ET.Element | None, name: str) -> str:
    if element is None:
        return ""
    child = element.find(name)
    if child is None or child.text is None:
        return ""
    return child.text.strip()


def psp_xml_language_valid(ctx: RepoContext, path: Path) -> tuple[bool, str]:
    expected = configured_language(ctx)
    supported = {"zh-CN", "en-US"}
    rel = path.relative_to(ctx.root)
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return fail(f"{rel} is not valid XML: {exc}")
    root_language = (root.get("language") or "").strip()
    contract_language = child_text(root.find("language_contract"), "output_language")
    metadata_language = child_text(root.find("metadata"), "output_language")
    if root_language not in supported:
        return fail(f"{rel} missing supported root language")
    if contract_language not in supported:
        return fail(f"{rel} missing supported language_contract/output_language")
    if metadata_language not in supported:
        return fail(f"{rel} missing supported metadata/output_language")
    if root_language != contract_language or contract_language != metadata_language:
        return fail(f"{rel} language mismatch: root={root_language}, contract={contract_language}, metadata={metadata_language}")
    if root_language != expected:
        return fail(f"{rel} language {root_language} does not match matrix.yml language {expected}")
    return ok(f"{rel} language={root_language}")


def required_paths(paths: tuple[str, ...]) -> Callable[[RepoContext], tuple[bool, str]]:
    def check(ctx: RepoContext) -> tuple[bool, str]:
        missing = [rel for rel in paths if not ctx.exists(rel)]
        template_only = [rel for rel in missing if ctx.template_exists(rel)]
        if missing:
            if template_only:
                return fail(
                    "template-only: "
                    + ", ".join(rel + ".tmpl" for rel in template_only)
                    + "; missing real files: "
                    + ", ".join(missing)
                )
            return fail("missing: " + ", ".join(missing))
        return ok(f"{len(paths)} required paths present")

    return check


def required_path_options(options: tuple[tuple[str, ...], ...]) -> Callable[[RepoContext], tuple[bool, str]]:
    def check(ctx: RepoContext) -> tuple[bool, str]:
        missing = [rels for rels in options if not any(ctx.exists(rel) for rel in rels)]
        if missing:
            return fail("missing options: " + "; ".join(" or ".join(rels) for rels in missing))
        return ok(f"{len(options)} required path options present")

    return check


def first_existing(ctx: RepoContext, paths: tuple[str, ...]) -> str:
    for rel in paths:
        if ctx.exists(rel):
            return rel
    return paths[0]


def psp_scaffold_exists(ctx: RepoContext) -> tuple[bool, str]:
    current_files = sorted((ctx.path("identity") / "psp").glob("*/current/PSP_REPORT.xml"))
    version_files = sorted((ctx.path("identity") / "psp").glob("*/versions/PSP_REPORT.*.xml"))
    evidence_files = sorted((ctx.path("identity") / "psp").glob("*/current/EVIDENCE_MATURITY.xml"))
    if not current_files and list((ctx.path("identity") / "psp").glob("*/current/PSP_REPORT.xml.tmpl")):
        return fail("template-only: identity/psp/<person-id>/current/PSP_REPORT.xml.tmpl exists but PSP artifact is missing")
    if not current_files:
        return fail("missing identity/psp/<person-id>/current/PSP_REPORT.xml")
    if not version_files:
        return fail("missing identity/psp/<person-id>/versions/PSP_REPORT.<timestamp>.xml")
    passed, detail = psp_xml_language_valid(ctx, current_files[0])
    if not passed:
        return fail(detail)
    if evidence_files:
        passed, detail = psp_xml_language_valid(ctx, evidence_files[0])
        if not passed:
            return fail(detail)
    return ok(str(current_files[0].relative_to(ctx.root)))


def design_scaffold_exists(ctx: RepoContext) -> tuple[bool, str]:
    md_files = sorted(ctx.path("design").glob("DESIGN-*.md")) or sorted(ctx.path("identity/design").glob("DESIGN-*.md"))
    xml_files = sorted(ctx.path("identity/design").glob("DESIGN_TASTE-*.xml"))
    if not md_files and (list(ctx.path("design").glob("DESIGN-*.md.tmpl")) or list(ctx.path("identity/design").glob("DESIGN-*.md.tmpl"))):
        return fail("template-only: identity/design/DESIGN-<timestamp>.md.tmpl exists but Design artifact is missing")
    if not ctx.exists("DESIGN.md"):
        return fail("missing DESIGN.md")
    if not ctx.exists("identity/design/current/DESIGN_TASTE.xml"):
        return fail("missing identity/design/current/DESIGN_TASTE.xml")
    if not xml_files:
        return fail("missing identity/design/DESIGN_TASTE-<timestamp>.xml")
    return ok(str(md_files[0].relative_to(ctx.root))) if md_files else fail("missing identity/design/DESIGN-<timestamp>.md")


def artifact_registry_configured(ctx: RepoContext) -> tuple[bool, str]:
    text = ctx.read("artifacts/current.yml")
    if not text:
        return fail("missing artifacts/current.yml")
    required = (
        "avatar_description:",
        "wenxin:",
        "psp:",
        "design:",
        "skill_recommendations:",
        "evidence_maturity:",
        "current_entrypoint:",
        "active_artifact:",
    )
    missing = [item for item in required if item not in text]
    if missing:
        return fail("artifacts/current.yml missing: " + ", ".join(missing))
    return ok("artifacts/current.yml")


def psp_update_log_exists(ctx: RepoContext) -> tuple[bool, str]:
    files = sorted((ctx.path("identity") / "psp").glob("*/update-log-*.md"))
    if not files and list((ctx.path("identity") / "psp").glob("*/update-log-*.md.tmpl")):
        return fail("template-only: identity/psp/<person-id>/update-log-<timestamp>.md.tmpl exists but update-log artifact is missing")
    return ok(str(files[0].relative_to(ctx.root))) if files else fail("missing identity/psp/<person-id>/update-log-<timestamp>.md")


def psp_initialization_exists(ctx: RepoContext) -> tuple[bool, str]:
    files = sorted((ctx.path("identity") / "psp").glob("*/INITIALIZATION.md"))
    if not files and list((ctx.path("identity") / "psp").glob("*/INITIALIZATION.md.tmpl")):
        return fail("template-only: identity/psp/<person-id>/INITIALIZATION.md.tmpl exists but INITIALIZATION.md is missing")
    return ok(str(files[0].relative_to(ctx.root))) if files else fail("missing identity/psp/<person-id>/INITIALIZATION.md")


def standard_artifact_gate(
    ctx: RepoContext,
    path: Path,
    artifact_type: str,
    required_markers: tuple[str, ...],
) -> tuple[bool, str]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return fail(f"{path.relative_to(ctx.root)} is not UTF-8 text")
    rel = path.relative_to(ctx.root)
    if "standard_output_gate" not in text:
        return fail(f"{rel} missing standard_output_gate from docs/self-evolution-output-standards.md")
    if f"artifact_type: {artifact_type}" not in text and f"artifact_type: `{artifact_type}`" not in text:
        return fail(f"{rel} missing artifact_type: {artifact_type}")
    sufficiency_match = re.search(r"evidence_sufficiency:\s*`?(sufficient|insufficient)`?", text)
    if not sufficiency_match:
        return fail(f"{rel} missing evidence_sufficiency: sufficient|insufficient")
    if "evidence_sources" not in text:
        return fail(f"{rel} missing evidence_sources")
    if "missing_information" not in text:
        return fail(f"{rel} missing missing_information")
    if sufficiency_match.group(1) == "insufficient":
        if "suggested_prompt" not in text and "why_needed" not in text:
            return fail(f"{rel} is insufficient but does not provide targeted missing-information prompts")
        return ok(f"{rel} declares insufficient evidence and prompts for missing information")
    missing = []
    for marker in required_markers:
        alternatives = tuple(part.strip() for part in marker.split("|"))
        if not any(alternative in text for alternative in alternatives):
            missing.append(marker)
    if missing:
        return fail(f"{rel} is sufficient but missing standard sections: " + ", ".join(missing))
    return ok(f"{rel} passes {artifact_type} standard output gate")


def psp_generated(ctx: RepoContext) -> tuple[bool, str]:
    psp_path = current_entrypoint_path(ctx, "psp", "")
    if psp_path and ctx.exists(psp_path):
        artifact = ctx.path(psp_path)
    else:
        active_path = active_artifact_path(ctx, "psp")
        if active_path and ctx.exists(active_path):
            artifact = ctx.path(active_path)
        else:
            files = sorted((ctx.path("identity") / "psp").glob("*/versions/PSP_REPORT.*.xml"))
            artifact = files[-1] if files else None
    if artifact is None:
        return fail("missing PSP artifact")
    text = artifact.read_text(encoding="utf-8")
    markers = (
        "TODO",
        "scaffold",
        "intake-only",
        "Generate from approved source material",
        "No stable work preference, decision pattern, communication style",
        "no personal evidence body",
        "has been provided yet",
        "cannot do yet",
    )
    hits = unique_hits(markers, text)
    if hits:
        return fail(f"{artifact.relative_to(ctx.root)} still has pending markers: {', '.join(hits)}")
    if len(text.strip()) < 800:
        return fail(f"{artifact.relative_to(ctx.root)} is too thin for a generated PSP")
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        return fail(f"{artifact.relative_to(ctx.root)} is not valid XML: {exc}")
    required = (
        "language_contract",
        "metadata",
        "evidence_maturity",
        "source_inventory",
        "evidence_boundary",
        "ontology_map",
        "kernel",
        "cognition",
        "decision_model",
        "interaction_model",
        "business_domain_model",
        "language_fingerprint",
        "best_state",
        "delegation_boundary",
        "runtime_instructions",
        "validation_plan",
        "confirmation_checklist",
        "acceptance_criteria",
        "confidence_by_section",
        "missing_information",
        "iteration_log",
    )
    if root.tag != "psp_report" or root.attrib.get("schema") != "psp.report.v1":
        return fail(f"{artifact.relative_to(ctx.root)} must be psp_report schema=psp.report.v1")
    passed, detail = psp_xml_language_valid(ctx, artifact)
    if not passed:
        return fail(detail)
    missing = [name for name in required if root.find(name) is None]
    if missing:
        return fail(f"{artifact.relative_to(ctx.root)} missing PSP XML modules: " + ", ".join(missing))
    return ok(str(artifact.relative_to(ctx.root)))


def setup_config_exists(ctx: RepoContext) -> tuple[bool, str]:
    if not ctx.exists("replicateme.yml"):
        return fail("missing replicateme.yml")
    required = (
        "repo_name",
        "owner_name",
        "person_id",
        "github_owner",
        "github_auth_method",
        "memory_repo_name",
        "wiki_authoritative_source",
        "feishu_configure",
        "hermes_configure",
        "wenxin_goals",
        "raw_material_policy",
    )
    missing = []
    for key in required:
        value = ctx.config.get(key)
        if key not in ctx.config or value is None or value == "" or (isinstance(value, list) and not value):
            missing.append(key)
    if missing:
        return fail("replicateme.yml missing: " + ", ".join(missing))
    return ok("replicateme.yml")


def integration_permissions_configured(ctx: RepoContext) -> tuple[bool, str]:
    missing_files = [
        rel
        for rel in (
            "integrations/github.yml",
            "integrations/feishu.yml",
            "integrations/hermes.yml",
            "integrations/data-sources.yml",
            "security/permissions.yml",
        )
        if not ctx.exists(rel)
    ]
    if missing_files:
        return fail("missing: " + ", ".join(missing_files))

    if as_bool(ctx.config, "github_configure", False):
        github_permissions = as_list(ctx.config, "github_permissions")
        if not ctx.config.get("github_auth_method") or str(ctx.config.get("github_auth_method")) == "skip":
            return fail("GitHub is enabled but github_auth_method is not configured")
        if not github_permissions:
            return fail("GitHub is enabled but github_permissions is empty")

    if as_bool(ctx.config, "feishu_configure", False):
        feishu_permissions = as_list(ctx.config, "feishu_permissions")
        if not ctx.config.get("feishu_auth_method") or str(ctx.config.get("feishu_auth_method")) == "skip":
            return fail("Feishu is enabled but feishu_auth_method is not configured")
        if not feishu_permissions:
            return fail("Feishu is enabled but feishu_permissions is empty")
        token_policy = str(ctx.config.get("feishu_token_policy") or "")
        if token_policy not in {"env-only", "manual-export"}:
            return fail("Feishu token policy must avoid repo storage")

    if as_bool(ctx.config, "hermes_configure", False):
        hermes_sources = as_list(ctx.config, "hermes_source_usage")
        hermes_targets = as_list(ctx.config, "hermes_targets")
        token_policy = str(ctx.config.get("hermes_token_policy") or "")
        if not hermes_sources:
            return fail("Hermes is enabled but hermes_source_usage is empty")
        if not hermes_targets:
            return fail("Hermes is enabled but hermes_targets is empty")
        if token_policy not in {"env-only-or-platform-secret", "env-only", "platform-secret"}:
            return fail("Hermes token policy must avoid repo storage")

    return ok("integration permission configs present")


def github_tooling_ready(ctx: RepoContext) -> tuple[bool, str]:
    if not as_bool(ctx.config, "github_require_gh", False):
        return ok("github_require_gh is false")
    if shutil.which("git") is None:
        return fail("git is missing")
    if shutil.which("gh") is None:
        return fail("gh is missing; run scripts/apply_avatar_config.py <config> --install-tools")
    if as_bool(ctx.config, "github_auth_required", False):
        result = subprocess.run(["gh", "auth", "status"], text=True, capture_output=True, check=False)
        if result.returncode != 0:
            return fail("gh is installed but not authenticated; run gh auth login")
    return ok("git/gh tooling ready")


def profile_complete(ctx: RepoContext) -> tuple[bool, str]:
    text = ctx.read("identity/public-profile/profile.yml")
    if not text:
        return fail("missing identity/public-profile/profile.yml")

    required = ("owner_name", "display_name", "person_id", "public_summary")
    missing = [field for field in required if not re.search(rf"^{field}:\s*.+$", text, re.MULTILINE)]
    if missing:
        return fail("missing fields: " + ", ".join(missing))

    pending_lines = []
    for field in required:
        match = re.search(rf"^{field}:\s*(.+)$", text, re.MULTILINE)
        value = match.group(1).strip().strip("'\"") if match else ""
        if not value or value.startswith("TODO"):
            pending_lines.append(field)
    if pending_lines:
        return fail("pending fields: " + ", ".join(pending_lines))
    return ok("public profile fields filled")


def wenxin_self_discovery_artifact(ctx: RepoContext) -> tuple[bool, str]:
    inneratlas_current = current_entrypoint_path(ctx, "wenxin", "identity/inneratlas/current/INNERATLAS_REPORT.xml")
    if inneratlas_current.endswith(".xml") and ctx.exists(inneratlas_current):
        text = ctx.read(inneratlas_current)
        artifact_name = re.search(r'artifact_name="([^"]+)"', text)
        completion = re.search(r"<completion_percent>(\d+)</completion_percent>", text)
        report_status = re.search(r"<report_status>([^<]+)</report_status>", text)
        if not artifact_name or artifact_name.group(1) != "INNERATLAS_REPORT.xml":
            return fail(f"{inneratlas_current} is not canonical INNERATLAS_REPORT.xml")
        if not completion or completion.group(1) != "100" or not report_status or report_status.group(1) != "complete":
            completion_value = completion.group(1) if completion else "missing"
            status_value = report_status.group(1) if report_status else "missing"
            return fail(
                f"{inneratlas_current} exists but is not complete "
                f"(report_status={status_value}, completion_percent={completion_value})"
            )
        return ok(inneratlas_current)

    files = [
        path
        for path in ctx.files("identity/wenxin")
        if path.name != "README.md" and path.stat().st_size > 0
    ]
    if not files:
        return fail("no generated Wenxin artifact under identity/wenxin/")
    preferred = {"WENXIN_REPORT.md", "public-positioning.md", "skill-recommendations.yml"}
    if not any(path.name in preferred for path in files):
        return fail("identity/wenxin/ has artifacts, but none of WENXIN_REPORT.md, public-positioning.md, or skill-recommendations.yml")
    report = ctx.path("identity/wenxin/WENXIN_REPORT.md")
    if report.exists():
        passed, detail = standard_artifact_gate(
            ctx,
            report,
            "wenxin",
            (
                "standard_output_gate",
                "source_inventory",
                "一句话定位|one-line positioning",
                "三段卖点|three selling points",
                "我是谁|who I am",
                "我现在站在哪|where I stand",
                "领域覆盖图|field coverage map",
                "完成度百分比|completion percentage",
                "Gap 分析|gap analysis",
                "三条未来路径|three future paths",
                "Skill|candidate Skill recommendations",
            ),
        )
        if not passed:
            return fail(detail)
    return ok(", ".join(str(path.relative_to(ctx.root)) for path in files[:3]))


def skill_recommendations_generated(ctx: RepoContext) -> tuple[bool, str]:
    text = ctx.read("identity/wenxin/skill-recommendations.yml")
    if not text:
        return fail("missing identity/wenxin/skill-recommendations.yml")
    markers = (
        "TODO",
        "todo",
        "scaffold",
        "intake-ready",
        "status: draft",
        "generated_from: replicateme.yml",
        "evidence-needed",
        "待验证",
        "才能升级为具体 Skill",
    )
    hits = unique_hits(markers, text)
    has_recommendation = bool(re.search(r"^\s*-\s+machine_name:\s*\S+", text, re.MULTILINE))
    if hits:
        return fail("skill-recommendations.yml is still an intake scaffold: " + ", ".join(hits))
    if not has_recommendation:
        return fail("skill-recommendations.yml has no recommendations")
    if "language:" not in text:
        return fail("skill-recommendations.yml should declare language")
    if "machine_name:" not in text:
        return fail("skill-recommendations.yml should define machine_name for each recommendation")
    if "alias:" not in text:
        return fail("skill-recommendations.yml should define alias for user-given names or null")
    if "implemented:" not in text:
        return fail("skill-recommendations.yml should define implemented for each recommendation")
    if "summarized:" not in text:
        return fail("skill-recommendations.yml should define summarized for each recommendation")
    if "usage_scenarios:" not in text:
        return fail("skill-recommendations.yml should define usage_scenarios for each recommendation")
    if "evidence_needed" not in text:
        return fail("skill-recommendations.yml should define evidence_needed for each recommendation")
    if "skill_type:" not in text:
        return fail("skill-recommendations.yml should label each recommendation with skill_type")
    if "promotion_gate:" not in text:
        return fail("skill-recommendations.yml should define promotion_gate for skill upgrades")
    if "eligibility_type:" not in text:
        return fail("skill-recommendations.yml should label each recommendation with eligibility_type")
    if "top_5_percent_capability_hypothesis" not in text and "repeated_workflow" not in text:
        return fail("skill-recommendations.yml should define the high-percentile or repeated-workflow evidence gate")
    return ok("skill recommendations exist")


def memory_configured(ctx: RepoContext) -> tuple[bool, str]:
    path = first_existing(ctx, ("identity/memories/START-HERE.md", "memory/START-HERE.md"))
    text = ctx.read(path)
    if not text:
        return fail("missing identity/memories/START-HERE.md")
    markers = (
        "TODO",
        "example:",
        "first stage has no personal evidence body",
        "future owner-approved evidence",
        "owner-approved-material",
    )
    hits = unique_hits(markers, text)
    if hits:
        return fail(f"{path} is still an intake scaffold: " + ", ".join(hits))
    bullets = [line for line in text.splitlines() if line.strip().startswith("- ")]
    if not bullets:
        return fail(f"{path} has no area entrypoints")
    return ok("memory entrypoints configured")


def memory_wiki_configured(ctx: RepoContext) -> tuple[bool, str]:
    path = first_existing(ctx, ("identity/memories/wiki-repo.yml", "memory/wiki-repo.yml"))
    text = ctx.read(path)
    if not text:
        return fail("missing identity/memories/wiki-repo.yml")
    required = (
        "github_owner:",
        "repository:",
        "visibility:",
        "local_path:",
        "authoritative_source:",
        "sync_modes:",
        "source_policy:",
        "public_mirror:",
        "allowed_public_exports:",
        "private_collaboration:",
        "raw_material_policy:",
    )
    missing = [item for item in required if item not in text]
    if missing:
        return fail(f"{path} missing: " + ", ".join(missing))
    if "status: scaffold" in text:
        return fail(f"{path} still has status: scaffold")
    if "status: intake-ready" in text:
        return fail(f"{path} is intake-ready but has no synchronized memory source yet")
    if "rsync_enabled: true" in text and re.search(r"^rsync_target:\s*(\"\"|')?\s*$", text, re.MULTILINE):
        return fail(f"{path} enables rsync but rsync_target is empty")
    return ok("memory wiki repo configured")


def hermes_configured(ctx: RepoContext) -> tuple[bool, str]:
    text = ctx.read("integrations/hermes.yml")
    if not text:
        return fail("missing integrations/hermes.yml")
    required = ("enabled:", "update_cadence:", "source_usage:", "targets:", "token_policy:")
    missing = [item for item in required if item not in text]
    if missing:
        return fail("integrations/hermes.yml missing: " + ", ".join(missing))
    if "status: scaffold" in text:
        return fail("integrations/hermes.yml still has status: scaffold")
    if "status: intake-ready" in text:
        return fail("integrations/hermes.yml is intake-ready but no self-evolution sync has run yet")
    if "status: configured" in text and not ctx.exists("integrations/hermes-sync-log.md"):
        return fail("integrations/hermes.yml is configured, but no Hermes self-evolution sync log exists yet")
    if "enabled: true" in text:
        if re.search(r"^source_usage:\s*$", text, re.MULTILINE):
            return fail("Hermes enabled but source_usage is empty")
        if re.search(r"^targets:\s*$", text, re.MULTILINE):
            return fail("Hermes enabled but targets is empty")
    return ok("Hermes sync configured")


def skills_configured(ctx: RepoContext) -> tuple[bool, str]:
    skill_files = [
        path
        for path in ctx.files("skills")
        if path.name == "SKILL.md"
    ]
    matrix = ctx.read("matrix.yml")
    matrix_has_legacy_skill_entries = bool(re.search(r"^\s*skills:\s*$\n\s+-\s+id:", matrix, re.MULTILINE))
    matrix_has_taxonomy_slots = "skill_package_rule:" in matrix and "skill_recommendations:" in matrix
    if skill_files:
        return ok(", ".join(str(path.relative_to(ctx.root)) for path in skill_files[:3]))
    if matrix_has_legacy_skill_entries or matrix_has_taxonomy_slots:
        return ok("matrix.yml skill taxonomy slots exist")
    return fail("no concrete skill SKILL.md or matrix.yml skill taxonomy slots")


def cognition_taxonomy_configured(ctx: RepoContext) -> tuple[bool, str]:
    required = (
        first_existing(ctx, ("identity/cognition/README.md", "cognition/README.md")),
        first_existing(ctx, ("identity/cognition/object-taxonomy.yml", "cognition/object-taxonomy.yml")),
        first_existing(ctx, ("identity/cognition/data-contracts.yml", "cognition/data-contracts.yml")),
        "integrations/data-sources.yml",
        first_existing(ctx, ("runtime/memory/working-lessons/README.md", "memory/working-lessons/README.md")),
        first_existing(ctx, ("identity/memories/long-term/README.md", "memory/long-term/README.md")),
        first_existing(ctx, ("capabilities/memory/distilled-knowledge/README.md", "memory/distilled-knowledge/README.md")),
        "identity/wenxin/skill-recommendations.yml",
        "identity/wenxin/skill-summaries/README.md",
        first_existing(ctx, ("identity/cognition/skill-bindings/README.md", "cognition/skill-bindings/README.md")),
        first_existing(ctx, ("identity/cognition/skill-bindings/data-sources.yml", "cognition/skill-bindings/data-sources.yml")),
    )
    missing = [rel for rel in required if not ctx.exists(rel)]
    if missing:
        return fail("missing cognition scaffold: " + ", ".join(missing))

    taxonomy_path = first_existing(ctx, ("identity/cognition/object-taxonomy.yml", "cognition/object-taxonomy.yml"))
    taxonomy = ctx.read(taxonomy_path)
    required_markers = (
        "ephemeral_memory:",
        "working_lesson:",
        "long_term_memory:",
        "distilled_knowledge:",
        "runtime_skill:",
        "distilled_meta_skill:",
        "data_source:",
        "skill_binding:",
        "split_policy:",
    )
    missing_markers = [marker for marker in required_markers if marker not in taxonomy]
    if missing_markers:
        return fail(f"{taxonomy_path} missing: " + ", ".join(missing_markers))

    bindings_path = first_existing(ctx, ("identity/cognition/skill-bindings/data-sources.yml", "cognition/skill-bindings/data-sources.yml"))
    bindings = ctx.read(bindings_path)
    if "split_rule:" not in bindings or "registry: integrations/data-sources.yml" not in bindings:
        return fail(f"{bindings_path} missing split_rule or integration registry")

    contracts_path = first_existing(ctx, ("identity/cognition/data-contracts.yml", "cognition/data-contracts.yml"))
    contracts = ctx.read(contracts_path)
    if "write_order:" not in contracts or "classify object type" not in contracts:
        return fail(f"{contracts_path} missing write_order classification contract")

    return ok("cognition taxonomy, data contracts, memory layers, and skill bindings exist")


def security_boundary_configured(ctx: RepoContext) -> tuple[bool, str]:
    text = ctx.read("security/README.md")
    if not text:
        return fail("missing security/README.md")
    groups = {
        "secret material": ("API", "Token", "key", "password", "密码", "密钥"),
        "private material": ("private", "私密", "私有", "不可公开"),
        "source boundary": ("不要提交", "Never commit", "不得写入", "do not"),
    }
    missing = []
    for label, keywords in groups.items():
        if not any(keyword in text for keyword in keywords):
            missing.append(label)
    if missing:
        return fail("security/README.md missing boundary groups: " + ", ".join(missing))
    return ok("security boundary covers secrets and private material")


def docs_configured(ctx: RepoContext) -> tuple[bool, str]:
    readme = ctx.read("README.md")
    assets = [path for path in ctx.files("docs") if "assets" in path.parts]
    pending = any(marker in readme for marker in ("scaffold", "TODO"))
    if assets:
        return ok(", ".join(str(path.relative_to(ctx.root)) for path in assets[:3]))
    if readme and not pending:
        return ok("README.md no longer looks like scaffold copy")
    return fail("no public docs asset and README.md still looks scaffolded")


MATURITY_LEVELS = ("scaffold", "evidence-limited-v0", "public-v0", "research-grade", "avatar-grade")


def evidence_maturity(ctx: RepoContext) -> str:
    xml_path = current_entrypoint_path(ctx, "evidence_maturity", "")
    candidates = []
    if xml_path:
        candidates.append(ctx.path(xml_path))
    candidates.extend(sorted((ctx.path("identity") / "psp").glob("*/current/EVIDENCE_MATURITY.xml")))
    candidates.extend(sorted((ctx.path("identity") / "psp").glob("*/versions/EVIDENCE_MATURITY.*.xml")))
    for path in candidates:
        if path.exists() and path.suffix == ".xml":
            try:
                root = ET.parse(path).getroot()
            except (ET.ParseError, OSError):
                continue
            maturity = root.find("maturity")
            if maturity is not None and maturity.attrib.get("level"):
                return maturity.attrib["level"].strip().lower()
            level = root.findtext("level")
            if level:
                return level.strip().lower()

    text = ctx.read("docs/evidence-sufficiency.md")
    if not text:
        return "missing"
    patterns = (
        r"^Maturity Level:\s*`?([a-z0-9-]+)`?\s*$",
        r"^Current maturity:\s*`?([a-z0-9-]+)`?\s*$",
    )
    for pattern in patterns:
        match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
        if match:
            return match.group(1).strip().lower()
    return "unknown"


def evidence_sufficiency_report_configured(ctx: RepoContext) -> tuple[bool, str]:
    maturity = evidence_maturity(ctx)
    if maturity not in MATURITY_LEVELS:
        return fail(
            "evidence maturity missing valid maturity level; expected one of "
            + ", ".join(MATURITY_LEVELS)
        )
    xml_path = current_entrypoint_path(ctx, "evidence_maturity", "")
    if xml_path and ctx.exists(xml_path) and xml_path.endswith(".xml"):
        return ok(f"maturity={maturity}; source={xml_path}")

    text = ctx.read("docs/evidence-sufficiency.md")
    if not text:
        return fail("missing evidence maturity XML and docs/evidence-sufficiency.md fallback")
    required_markers = (
        "structure readiness",
        "content maturity",
        "Evidence sources",
        "Unavailable",
        "Incomplete",
        "instance-local",
    )
    missing = [marker for marker in required_markers if marker not in text]
    if missing:
        return fail("docs/evidence-sufficiency.md missing disclosure markers: " + ", ".join(missing))
    return ok(f"maturity={maturity}")


def self_evolution_output_standards_configured(ctx: RepoContext) -> tuple[bool, str]:
    text = ctx.read("docs/self-evolution-output-standards.md")
    if not text:
        return fail("missing docs/self-evolution-output-standards.md")
    required = (
        "Wenxin Standard Output",
        "PSP XML Standard Output",
        "SOUL is paused",
        "Design Standard Output",
        "Taste Generator",
        "IPO Reverse Standard Output",
        "standard_output_gate",
        "evidence_sufficiency",
        "claim_evidence",
        "missing_information",
        "suggested_prompt",
    )
    missing = [marker for marker in required if marker not in text]
    if missing:
        return fail("docs/self-evolution-output-standards.md missing: " + ", ".join(missing))
    return ok("Wenxin, PSP, Design, Taste Generator, and IPO Reverse output standards configured; SOUL paused")


def avatar_description_claim_evidence_configured(ctx: RepoContext) -> tuple[bool, str]:
    text = ctx.read("identity/avatar-description/current.yml")
    if not text:
        return fail("missing identity/avatar-description/current.yml")
    required = (
        "schema: openlifeos.avatar-description.v1",
        "claim_evidence:",
        "one_line:",
        "current_role:",
        "operating_mode:",
        "strengths:",
        "boundaries:",
    )
    missing = [marker for marker in required if marker not in text]
    if missing:
        return fail("identity/avatar-description/current.yml missing claim evidence markers: " + ", ".join(missing))
    return ok("avatar-description field-level claim evidence configured")


def ipo_reverse_artifacts_follow_standard(ctx: RepoContext) -> tuple[bool, str]:
    files = [
        *ctx.files("identity/ipo-reverse"),
        *[
            path
            for path in [*ctx.files("runtime/memory/working-lessons"), *ctx.files("memory/working-lessons")]
            if path.name.endswith("-ipo.md") or "ipo" in path.name.lower()
        ],
    ]
    markdown_files = [path for path in files if path.suffix == ".md" and path.name != "README.md"]
    if not markdown_files:
        return ok("no IPO Reverse artifact generated yet")
    failures = []
    for path in markdown_files:
        passed, detail = standard_artifact_gate(
            ctx,
            path,
            "ipo-reverse",
            (
                "standard_output_gate",
                "finished_output_reference",
                "artifact_evidence_map",
                "hidden_cognitive_tasks",
                "methodology_selection",
                "middle_layer_artifacts",
                "process_chain",
                "final_IPO",
                "forward_reconstruction_check",
                "counterfactual_or_step_deletion_check",
                "assumptions_and_evidence_ledger",
                "downstream_usage",
            ),
        )
        if not passed:
            failures.append(detail)
    if failures:
        return fail("; ".join(failures))
    return ok(", ".join(str(path.relative_to(ctx.root)) for path in markdown_files[:3]))


def artifact_registry_field(ctx: RepoContext, artifact_key: str, field: str) -> str:
    text = ctx.read("artifacts/current.yml")
    if not text:
        return ""
    section = re.search(rf"^\s{{2}}{re.escape(artifact_key)}:\s*$([\s\S]*?)(?=^\s{{2}}\S|\Z)", text, re.MULTILINE)
    if not section:
        return ""
    match = re.search(rf"^\s{{4}}{re.escape(field)}:\s*['\"]?([^'\"\n]+)['\"]?\s*$", section.group(1), re.MULTILINE)
    return match.group(1).strip() if match else ""


def active_artifact_path(ctx: RepoContext, artifact_key: str) -> str:
    return artifact_registry_field(ctx, artifact_key, "active_artifact")


def current_entrypoint_path(ctx: RepoContext, artifact_key: str, fallback: str) -> str:
    return artifact_registry_field(ctx, artifact_key, "current_entrypoint") or fallback


CONTENT_MATURITY_ORDER = ("scaffold", "evidence-limited-v0", "public-v0", "research-grade", "avatar-grade")

CONTENT_CONFIDENCE_SCORE = {
    "high": 100,
    "medium-high": 82,
    "medium_high": 82,
    "medium": 64,
    "low-medium": 44,
    "low_medium": 44,
    "low": 28,
    "insufficient": 8,
}

CONTENT_STATUS_SCORE = {
    "avatar-grade": 100,
    "research-grade": 90,
    "confirmed": 88,
    "public-v0": 72,
    "configured": 64,
    "append-only": 60,
    "inferred": 68,
    "hypothesis": 42,
    "evidence-limited-v0": 45,
    "not_started": 18,
    "not-started": 18,
    "unassessed": 12,
    "empty": 8,
    "scaffold": 6,
}


def maturity_level_from_score(score: int) -> str:
    if score >= 88:
        return "avatar-grade"
    if score >= 74:
        return "research-grade"
    if score >= 50:
        return "public-v0"
    if score >= 22:
        return "evidence-limited-v0"
    return "scaffold"


def cap_maturity_level(level: str, cap: str) -> str:
    if level not in CONTENT_MATURITY_ORDER:
        level = "scaffold"
    if cap not in CONTENT_MATURITY_ORDER:
        return level
    return CONTENT_MATURITY_ORDER[min(CONTENT_MATURITY_ORDER.index(level), CONTENT_MATURITY_ORDER.index(cap))]


def xml_all_text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return " ".join(" ".join(element.itertext()).split())


def xml_has_substantive_evidence(element: ET.Element | None) -> bool:
    if element is None:
        return False
    evidence_attr = element.get("evidence")
    if evidence_attr and evidence_attr.strip().lower() not in {"none", "n/a", "na", "unknown"}:
        return True
    for descendant in element.iter():
        if descendant.tag == "evidence" and descendant.text and descendant.text.strip().lower() not in {"none", "n/a", "unknown"}:
            return True
    return False


def xml_has_missing_evidence(element: ET.Element | None) -> bool:
    if element is None:
        return False
    return any(descendant.tag == "missing_evidence" and (descendant.text or "").strip() for descendant in element.iter())


def xml_confidence_scores(element: ET.Element | None) -> list[int]:
    if element is None:
        return []
    scores: list[int] = []
    for descendant in element.iter():
        raw = descendant.attrib.get("confidence")
        if raw:
            scores.append(CONTENT_CONFIDENCE_SCORE.get(raw.strip().lower(), 45))
    return scores


def parse_xml_path(path: Path) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return None


PSP_CONTENT_MODULES = (
    "language_contract",
    "metadata",
    "evidence_maturity",
    "source_inventory",
    "evidence_boundary",
    "ontology_map",
    "kernel",
    "cognition",
    "decision_model",
    "interaction_model",
    "business_domain_model",
    "language_fingerprint",
    "best_state",
    "delegation_boundary",
    "runtime_instructions",
    "validation_plan",
    "confirmation_checklist",
    "acceptance_criteria",
    "confidence_by_section",
    "missing_information",
    "iteration_log",
)

PSP_CONTENT_CORE_MODULES = {
    "evidence_maturity",
    "source_inventory",
    "evidence_boundary",
    "ontology_map",
    "kernel",
    "cognition",
    "decision_model",
    "interaction_model",
    "business_domain_model",
    "language_fingerprint",
    "best_state",
    "delegation_boundary",
    "runtime_instructions",
    "validation_plan",
    "confirmation_checklist",
    "acceptance_criteria",
}

PSP_CONTENT_WEIGHTS = {
    "language_contract": 2,
    "metadata": 2,
    "evidence_maturity": 6,
    "source_inventory": 5,
    "evidence_boundary": 5,
    "ontology_map": 8,
    "kernel": 9,
    "cognition": 8,
    "decision_model": 10,
    "interaction_model": 7,
    "business_domain_model": 6,
    "language_fingerprint": 7,
    "best_state": 6,
    "delegation_boundary": 6,
    "runtime_instructions": 7,
    "validation_plan": 7,
    "confirmation_checklist": 5,
    "acceptance_criteria": 5,
    "confidence_by_section": 4,
    "missing_information": 4,
    "iteration_log": 3,
}

PSP_NESTED_REQUIREMENTS = {
    "kernel": ("ultimate_value_order", "boundaries", "drivers", "identity_self_definition"),
    "ontology_map": ("dimensions",),
    "cognition": ("world_assumptions", "attribution_patterns", "attention_filter", "analogy_domains"),
    "decision_model": (
        "decision_style",
        "information_threshold",
        "risk_policy",
        "conflict_resolution",
        "judgment_patterns",
        "pre_answer_checks",
        "forced_downgrade_rules",
    ),
    "interaction_model": ("communication_style", "relationship_posture", "disagreement_style", "questioning_style"),
    "business_domain_model": (
        "business_logic",
        "customer_logic",
        "talent_logic",
        "organization_logic",
        "data_and_metrics",
        "execution_loops",
    ),
    "delegation_boundary": ("cannot_represent", "can_represent", "private_information_policy", "external_translation_policy"),
    "runtime_instructions": ("must_follow", "must_not_do", "uncertainty_policy"),
    "validation_plan": ("blind_evaluation", "judgment_holdout", "consistency_scan"),
    "confirmation_checklist": ("items",),
}


def current_psp_artifact(ctx: RepoContext) -> Path | None:
    psp_path = current_entrypoint_path(ctx, "psp", "")
    if psp_path and ctx.exists(psp_path):
        return ctx.path(psp_path)
    active_path = active_artifact_path(ctx, "psp")
    if active_path and ctx.exists(active_path):
        return ctx.path(active_path)
    files = sorted((ctx.path("identity") / "psp").glob("*/current/PSP_REPORT.xml"))
    if files:
        return files[0]
    versions = sorted((ctx.path("identity") / "psp").glob("*/versions/PSP_REPORT.*.xml"))
    return versions[-1] if versions else None


def psp_module_content_score(name: str, module: ET.Element | None) -> dict[str, object]:
    if module is None:
        return {
            "score": 0,
            "status": "missing",
            "confidence": "missing",
            "has_evidence": False,
            "has_missing_evidence": False,
            "required_child_score": 0,
            "gaps": ["module missing"],
        }
    required = PSP_NESTED_REQUIREMENTS.get(name, ())
    present = sum(1 for child_name in required if module.find(child_name) is not None)
    required_score = round(present / len(required) * 100) if required else 100
    status = (module.attrib.get("status") or "").strip().lower()
    confidence = (module.attrib.get("confidence") or "").strip().lower()
    has_evidence = xml_has_substantive_evidence(module)
    has_missing = xml_has_missing_evidence(module)
    text_score = min(100, len(xml_all_text(module)) // 10)
    if status in {"scaffold", "unassessed", "empty", "not_started", "not-started"}:
        text_score = min(text_score, 35)
    confidence_score = CONTENT_CONFIDENCE_SCORE.get(confidence, 34 if confidence else 0)
    status_score = CONTENT_STATUS_SCORE.get(status, 40 if status else 0)
    score = round(
        status_score * 0.22
        + confidence_score * 0.20
        + (100 if has_evidence else 35 if has_missing else 0) * 0.18
        + (100 if has_missing else 55 if has_evidence else 0) * 0.10
        + required_score * 0.12
        + text_score * 0.18
    )
    gaps: list[str] = []
    if required_score < 100:
        gaps.append("missing required child fields")
    if not status or status in {"scaffold", "unassessed", "empty", "not_started", "not-started"}:
        gaps.append(f"status={status or 'missing'}")
    if not confidence or confidence in {"insufficient", "low", "low_medium", "low-medium"}:
        gaps.append(f"confidence={confidence or 'missing'}")
    if name in PSP_CONTENT_CORE_MODULES and not has_evidence:
        gaps.append("missing evidence")
    if name in PSP_CONTENT_CORE_MODULES and not has_missing:
        gaps.append("missing missing_evidence")
    if name in PSP_CONTENT_CORE_MODULES and text_score < 45:
        gaps.append("content too thin")
    return {
        "score": max(0, min(100, score)),
        "status": status or "missing",
        "confidence": confidence or "missing",
        "has_evidence": has_evidence,
        "has_missing_evidence": has_missing,
        "required_child_score": required_score,
        "gaps": gaps,
    }


def psp_content_maturity(ctx: RepoContext) -> dict[str, object]:
    path = current_psp_artifact(ctx)
    if path is None:
        return {
            "level": "missing",
            "score": 0,
            "score_out_of": 100,
            "artifact": "psp",
            "path": None,
            "blocking_gaps": ["missing PSP_REPORT.xml"],
        }
    root = parse_xml_path(path)
    if root is None:
        return {
            "level": "scaffold",
            "score": 0,
            "score_out_of": 100,
            "artifact": "psp",
            "path": str(path.relative_to(ctx.root)),
            "blocking_gaps": ["PSP_REPORT.xml is not valid XML"],
        }
    module_scores = {name: psp_module_content_score(name, root.find(name)) for name in PSP_CONTENT_MODULES}
    total_weight = sum(PSP_CONTENT_WEIGHTS.values())
    score = round(sum(int(module_scores[name]["score"]) * PSP_CONTENT_WEIGHTS[name] for name in PSP_CONTENT_MODULES) / total_weight)
    level = maturity_level_from_score(score)
    evidence_module = root.find("evidence_maturity")
    declared = child_text(evidence_module, "level").lower() if evidence_module is not None else ""
    if declared in CONTENT_MATURITY_ORDER:
        level = cap_maturity_level(level, declared)
    if int(module_scores["validation_plan"]["score"]) < 60:
        level = cap_maturity_level(level, "public-v0")
    if int(module_scores["language_fingerprint"]["score"]) < 60:
        level = cap_maturity_level(level, "public-v0")
    blocking = []
    non_blocking = []
    for name, result in module_scores.items():
        gaps = [str(gap) for gap in result["gaps"]]
        if not gaps:
            continue
        message = f"{name}: " + "; ".join(gaps[:3])
        if name in PSP_CONTENT_CORE_MODULES and int(result["score"]) < 60:
            blocking.append(message)
        else:
            non_blocking.append(message)
    if int(module_scores["validation_plan"]["score"]) < 60:
        blocking.append("validation_plan: blocks research/avatar-grade until holdout or blind validation is started")
    return {
        "level": level,
        "score": score,
        "score_out_of": 100,
        "artifact": "psp",
        "path": str(path.relative_to(ctx.root)),
        "declared_evidence_maturity_level": declared or "unknown",
        "meaning": "PSP content maturity computed from required PSP XML modules; separate from structure completion.",
        "module_scores": module_scores,
        "weak_modules": [
            {"module": name, "score": result["score"], "status": result["status"], "confidence": result["confidence"]}
            for name, result in module_scores.items()
            if int(result["score"]) < 60
        ],
        "blocking_gaps": blocking[:12],
        "non_blocking_gaps": non_blocking[:12],
    }


INNERATLAS_SECTION_WEIGHTS = {
    "metadata": 2,
    "source_discovery": 5,
    "interaction_review": 6,
    "identity_layer": 9,
    "explicit_analysis.mbti": 7,
    "explicit_analysis.big_five": 5,
    "explicit_analysis.capability_levels": 8,
    "explicit_analysis.field_coverage": 6,
    "explicit_analysis.gap_analysis": 8,
    "radar": 7,
    "barriers": 7,
    "milestones": 6,
    "pitch": 6,
    "soft_texture": 6,
    "skill_recommendations": 8,
    "presentation_plan": 3,
    "missing_information": 5,
    "iteration_log": 3,
}

INNERATLAS_REQUIRED = {
    "metadata": (
        ("./metadata/generated_at", 1),
        ("./metadata/last_updated", 1),
        ("./metadata/artifact_root", 1),
        ("./metadata/current_path", 1),
        ("./metadata/version_path", 1),
        ("./metadata/subject_display_name", 1),
        ("./metadata/assessment_mode", 1),
        ("./metadata/workflow_state", 1),
        ("./metadata/report_status", 1),
        ("./metadata/completion_percent", 1),
    ),
    "source_discovery": (
        ("./source_discovery/scanned_at", 1),
        ("./source_discovery/scan_status", 1),
        ("./source_discovery/discovery_policy", 1),
        ("./source_discovery/cli_candidates/cli_candidate", 1),
    ),
    "interaction_review": (
        ("./interaction_review/contradiction", 1),
        ("./interaction_review/anomaly", 1),
        ("./interaction_review/confirmation", 1),
    ),
    "identity_layer": (
        ("./identity_layer/nickname_plain", 1),
        ("./identity_layer/nickname_serious", 1),
        ("./identity_layer/one_line_positioning", 1),
        ("./identity_layer/public_mainline", 1),
        ("./identity_layer/private_mainline", 1),
        ("./identity_layer/why_nickname_fits", 1),
        ("./identity_layer/scarcity_judgment", 1),
        ("./identity_layer/evidence", 1),
    ),
    "explicit_analysis.mbti": (
        ("./explicit_analysis/mbti/method", 1),
        ("./explicit_analysis/mbti/current_judgment", 1),
        ("./explicit_analysis/mbti/dimension", 4),
        ("./explicit_analysis/mbti/change_trajectory", 1),
        ("./explicit_analysis/mbti/evidence", 1),
    ),
    "explicit_analysis.big_five": (("./explicit_analysis/big_five/trait", 5),),
    "explicit_analysis.capability_levels": (("./explicit_analysis/capability_levels/capability", 1),),
    "explicit_analysis.field_coverage": (
        ("./explicit_analysis/field_coverage/strength_zone", 1),
        ("./explicit_analysis/field_coverage/touched_zone", 1),
        ("./explicit_analysis/field_coverage/blank_zone", 1),
    ),
    "explicit_analysis.gap_analysis": (("./explicit_analysis/gap_analysis/advantage_area", 1),),
    "radar": (("./radar/dimension", 5), ("./radar/overall_shape", 1)),
    "barriers": (("./barriers/barrier", 3),),
    "milestones": (("./milestones/milestone", 3),),
    "pitch": (
        ("./pitch/who_they_are", 1),
        ("./pitch/why_they_are_credible", 1),
        ("./pitch/what_value_they_create", 1),
    ),
    "soft_texture": (("./soft_texture/pattern_sentence", 4),),
    "skill_recommendations": (("./skill_recommendations/recommended_skill", 1),),
    "presentation_plan": (("./presentation_plan/section", 13),),
    "missing_information": (("./missing_information/status", 1),),
    "iteration_log": (("./iteration_log/entry", 1),),
}

INNERATLAS_CRITICAL_SECTIONS = {
    "identity_layer",
    "explicit_analysis.mbti",
    "explicit_analysis.capability_levels",
    "explicit_analysis.gap_analysis",
    "radar",
    "barriers",
    "skill_recommendations",
    "missing_information",
}


def current_inneratlas_artifact(ctx: RepoContext) -> Path | None:
    rel = current_entrypoint_path(ctx, "wenxin", "identity/inneratlas/current/INNERATLAS_REPORT.xml")
    if rel and ctx.exists(rel):
        return ctx.path(rel)
    active = active_artifact_path(ctx, "wenxin")
    if active and ctx.exists(active):
        return ctx.path(active)
    current = ctx.path("identity/inneratlas/current/INNERATLAS_REPORT.xml")
    if current.exists():
        return current
    versions = sorted(ctx.path("identity/inneratlas/versions").glob("INNERATLAS_REPORT.*.xml"))
    return versions[-1] if versions else None


def inneratlas_section_element(root: ET.Element, section: str) -> ET.Element | None:
    if section.startswith("explicit_analysis."):
        parent = root.find("./explicit_analysis")
        return parent.find(section.split(".", 1)[1]) if parent is not None else None
    return root.find(f"./{section}")


def xml_elements_valid(elements: list[ET.Element], min_count: int) -> int:
    valid = 0
    for element in elements:
        if xml_all_text(element) or element.attrib:
            valid += 1
    return min(valid, min_count)


def inneratlas_section_score(root: ET.Element, section: str) -> dict[str, object]:
    checks = INNERATLAS_REQUIRED[section]
    passed = 0
    total = 0
    for xpath, min_count in checks:
        total += min_count
        passed += xml_elements_valid(root.findall(xpath), min_count)
    required_completion = round(passed / total * 100) if total else 0
    element = inneratlas_section_element(root, section)
    density_score = min(100, len(xml_all_text(element)) // 12) if element is not None else 0
    evidence_score = 100 if xml_has_substantive_evidence(element) else 35 if section in {"presentation_plan", "iteration_log", "metadata"} else 0
    confidence_values = xml_confidence_scores(element)
    confidence_score = round(sum(confidence_values) / len(confidence_values)) if confidence_values else (
        70 if section in {"metadata", "source_discovery", "presentation_plan", "iteration_log"} else 35
    )
    presentation_score = 100 if element is not None and element.attrib.get("presentation") else 65 if section == "metadata" else 0
    score = round(
        required_completion * 0.42
        + evidence_score * 0.20
        + confidence_score * 0.16
        + density_score * 0.14
        + presentation_score * 0.08
    )
    gaps: list[str] = []
    if element is None:
        gaps.append("section missing")
    if required_completion < 100:
        gaps.append(f"required fields {passed}/{total}")
    if section in INNERATLAS_CRITICAL_SECTIONS and evidence_score < 100:
        gaps.append("missing evidence")
    if section in INNERATLAS_CRITICAL_SECTIONS and confidence_score < 50:
        gaps.append("low or missing confidence")
    if section in INNERATLAS_CRITICAL_SECTIONS and density_score < 35:
        gaps.append("content too thin")
    return {
        "score": max(0, min(100, score)),
        "score_out_of": 100,
        "required_completion": required_completion,
        "has_evidence": evidence_score == 100,
        "confidence_score": confidence_score,
        "gaps": gaps,
    }


def inneratlas_content_maturity(ctx: RepoContext) -> dict[str, object]:
    path = current_inneratlas_artifact(ctx)
    if path is None:
        return {
            "level": "missing",
            "score": 0,
            "score_out_of": 100,
            "artifact": "inneratlas",
            "path": None,
            "blocking_gaps": ["missing INNERATLAS_REPORT.xml"],
        }
    root = parse_xml_path(path)
    if root is None:
        return {
            "level": "scaffold",
            "score": 0,
            "score_out_of": 100,
            "artifact": "inneratlas",
            "path": str(path.relative_to(ctx.root)),
            "blocking_gaps": ["INNERATLAS_REPORT.xml is not valid XML"],
        }
    section_scores = {section: inneratlas_section_score(root, section) for section in INNERATLAS_SECTION_WEIGHTS}
    total_weight = sum(INNERATLAS_SECTION_WEIGHTS.values())
    score = round(
        sum(int(section_scores[section]["score"]) * INNERATLAS_SECTION_WEIGHTS[section] for section in INNERATLAS_SECTION_WEIGHTS)
        / total_weight
    )
    level = maturity_level_from_score(score)
    report_status = child_text(root.find("metadata"), "report_status").lower()
    completion_percent = child_text(root.find("metadata"), "completion_percent")
    missing_status = child_text(root.find("missing_information"), "status").lower()
    unresolved_missing = root.findall("./missing_information/missing")
    required_missing = [item for item in unresolved_missing if item.attrib.get("required_for_100", "").lower() == "true"]
    if report_status != "complete" or completion_percent != "100":
        level = cap_maturity_level(level, "evidence-limited-v0")
    if unresolved_missing:
        level = cap_maturity_level(level, "public-v0")
    if required_missing or missing_status not in {"no_missing_required_fields", "no_missing_required_field"}:
        level = cap_maturity_level(level, "evidence-limited-v0" if required_missing else "public-v0")
    blocking = []
    non_blocking = []
    for section, result in section_scores.items():
        gaps = [str(gap) for gap in result["gaps"]]
        if not gaps:
            continue
        message = f"{section}: " + "; ".join(gaps[:3])
        if section in INNERATLAS_CRITICAL_SECTIONS and int(result["score"]) < 60:
            blocking.append(message)
        else:
            non_blocking.append(message)
    return {
        "level": level,
        "score": score,
        "score_out_of": 100,
        "artifact": "inneratlas",
        "path": str(path.relative_to(ctx.root)),
        "meaning": "InnerAtlas content maturity computed from fixed INNERATLAS_REPORT.xml sections; separate from completion_percent.",
        "section_scores": section_scores,
        "weak_sections": [
            {"section": section, "score": result["score"]}
            for section, result in section_scores.items()
            if int(result["score"]) < 60
        ],
        "blocking_gaps": blocking[:12],
        "non_blocking_gaps": non_blocking[:12],
    }


def text_field_present(text: str, pattern: str) -> bool:
    return bool(re.search(pattern, text, re.MULTILINE))


def simple_text_artifact_maturity(
    ctx: RepoContext,
    artifact: str,
    rel: str,
    required_markers: tuple[str, ...],
    evidence_markers: tuple[str, ...],
    critical_markers: tuple[str, ...] = (),
) -> dict[str, object]:
    text = ctx.read(rel)
    if not text:
        return {
            "level": "missing",
            "score": 0,
            "score_out_of": 100,
            "artifact": artifact,
            "path": rel,
            "blocking_gaps": [f"missing {rel}"],
        }
    required_hits = sum(1 for marker in required_markers if marker in text)
    evidence_hits = sum(1 for marker in evidence_markers if marker in text)
    critical_hits = sum(1 for marker in critical_markers if marker in text)
    required_score = round(required_hits / len(required_markers) * 100) if required_markers else 100
    evidence_score = round(evidence_hits / len(evidence_markers) * 100) if evidence_markers else 60
    critical_score = round(critical_hits / len(critical_markers) * 100) if critical_markers else 100
    density_score = min(100, len(text.strip()) // 20)
    pending_penalty = 25 if unique_hits(("TODO", "scaffold", "待补", "unknown", "intake-only"), text) else 0
    score = max(0, round(required_score * 0.42 + evidence_score * 0.22 + critical_score * 0.18 + density_score * 0.18) - pending_penalty)
    level = maturity_level_from_score(score)
    if pending_penalty:
        level = cap_maturity_level(level, "evidence-limited-v0")
    gaps = []
    missing_required = [marker for marker in required_markers if marker not in text]
    if missing_required:
        gaps.append("missing required markers: " + ", ".join(missing_required[:6]))
    missing_evidence = [marker for marker in evidence_markers if marker not in text]
    if missing_evidence:
        gaps.append("missing evidence markers: " + ", ".join(missing_evidence[:6]))
    if pending_penalty:
        gaps.append("contains pending/scaffold markers")
    return {
        "level": level,
        "score": score,
        "score_out_of": 100,
        "artifact": artifact,
        "path": rel,
        "required_score": required_score,
        "evidence_score": evidence_score,
        "critical_score": critical_score,
        "blocking_gaps": gaps[:8] if score < 60 else [],
        "non_blocking_gaps": gaps[:8] if score >= 60 else [],
    }


def skill_recommendations_content_maturity(ctx: RepoContext) -> dict[str, object]:
    rel = "identity/wenxin/skill-recommendations.yml"
    text = ctx.read(rel)
    if not text:
        return {
            "level": "missing",
            "score": 0,
            "score_out_of": 100,
            "artifact": "skill_recommendations",
            "path": rel,
            "blocking_gaps": [f"missing {rel}"],
        }
    recommendations = len(re.findall(r"^\s*-\s+machine_name:\s*\S+", text, re.MULTILINE))
    implemented = len(re.findall(r"^\s*implemented:\s*true\s*$", text, re.MULTILINE))
    field_markers = (
        "machine_name:",
        "display_name:",
        "alias:",
        "skill_type:",
        "eligibility_type:",
        "evidence_strength:",
        "implemented:",
        "summarized:",
        "evidence_refs:",
        "outputs:",
        "usage_scenarios:",
        "evidence_needed:",
        "promotion_gate:",
    )
    field_score = round(sum(1 for marker in field_markers if marker in text) / len(field_markers) * 100)
    recommendation_score = min(100, recommendations * 22)
    evidence_score = 100 if "evidence_refs:" in text and "evidence_needed:" in text else 35
    implementation_score = min(100, implemented * 30 + recommendations * 8)
    pending_penalty = 25 if unique_hits(("TODO", "scaffold", "待验证", "evidence-needed", "才能升级为具体 Skill"), text) else 0
    score = max(0, round(field_score * 0.36 + recommendation_score * 0.24 + evidence_score * 0.24 + implementation_score * 0.16) - pending_penalty)
    level = maturity_level_from_score(score)
    if recommendations == 0:
        level = "scaffold"
    if pending_penalty:
        level = cap_maturity_level(level, "evidence-limited-v0")
    gaps = []
    if recommendations == 0:
        gaps.append("no recommendations")
    missing = [marker for marker in field_markers if marker not in text]
    if missing:
        gaps.append("missing fields: " + ", ".join(missing[:8]))
    if implemented == 0:
        gaps.append("no implemented or alias-backed skill recommendation")
    if pending_penalty:
        gaps.append("contains pending/scaffold markers")
    return {
        "level": level,
        "score": score,
        "score_out_of": 100,
        "artifact": "skill_recommendations",
        "path": rel,
        "recommendation_count": recommendations,
        "implemented_count": implemented,
        "field_score": field_score,
        "blocking_gaps": gaps[:8] if score < 60 else [],
        "non_blocking_gaps": gaps[:8] if score >= 60 else [],
    }


def avatar_description_content_maturity(ctx: RepoContext) -> dict[str, object]:
    return simple_text_artifact_maturity(
        ctx,
        "avatar_description",
        "identity/avatar-description/current.yml",
        (
            "schema: openlifeos.avatar-description.v1",
            "one_line:",
            "current_role:",
            "operating_mode:",
            "strengths:",
            "boundaries:",
            "claim_evidence:",
        ),
        ("identity/inneratlas/current/INNERATLAS_REPORT.xml", "identity/psp", "DESIGN.md"),
        ("maturity_notice:", "derived_from:", "evidence_status:"),
    )


def design_content_maturity(ctx: RepoContext) -> dict[str, object]:
    result = simple_text_artifact_maturity(
        ctx,
        "design",
        "DESIGN.md",
        ("DESIGN_TASTE.xml", "design_variables", "preference", "avoid", "source"),
        ("evidence", "source", "owner", "confidence", "canonical_source"),
        ("current", "global", "aesthetics", "Motion", "Evidence"),
    )
    xml_rel = "identity/design/current/DESIGN_TASTE.xml"
    xml_path = ctx.path(xml_rel)
    root = parse_xml_path(xml_path)
    if root is None:
        result.setdefault("non_blocking_gaps", []).append(f"missing or invalid canonical XML source: {xml_rel}")
        result["level"] = cap_maturity_level(str(result["level"]), "public-v0")
        result["score"] = min(int(result["score"]), 72)
        return result

    required_modules = (
        "metadata",
        "source_inventory",
        "selection_context",
        "reference_examples",
        "design_variables",
        "theme_atmosphere",
        "color_system",
        "typography_system",
        "spacing_system",
        "layout_system",
        "shape_system",
        "depth_elevation",
        "component_system",
        "navigation_system",
        "motion_interaction",
        "media_imagery",
        "content_evidence",
        "accessibility_system",
        "anti_preferences",
        "responsive_behavior",
        "do_dont_rules",
        "iteration_guide",
        "known_gaps",
        "agent_prompt_guide",
    )
    missing_modules = [module for module in required_modules if root.find(module) is None]
    required_variables = (
        "font_direction",
        "type_scale",
        "color_mode",
        "accent_policy",
        "text_color_policy",
        "surface_density",
        "spacing_rhythm",
        "grid_container",
        "shape_radius",
        "motion_level",
        "media_treatment",
        "navigation_style",
        "accessibility_floor",
        "evidence_style",
    )
    variable_keys = {item.attrib.get("key", "") for item in root.findall("./design_variables/variable")}
    missing_variables = [key for key in required_variables if key not in variable_keys]
    evidence_sufficiency = child_text(root.find("metadata"), "evidence_sufficiency").lower()
    review_status = child_text(root.find("metadata"), "review_status").lower()
    confidence = child_text(root.find("metadata"), "confidence").lower()
    result["canonical_xml_path"] = xml_rel
    result["xml_schema"] = root.attrib.get("schema", "")
    result["xml_evidence_sufficiency"] = evidence_sufficiency
    result["xml_review_status"] = review_status
    result["xml_confidence"] = confidence
    result["xml_missing_modules"] = missing_modules
    result["xml_missing_design_variables"] = missing_variables
    if missing_modules:
        result.setdefault("non_blocking_gaps", []).append("missing XML modules: " + ", ".join(missing_modules[:6]))
        result["level"] = cap_maturity_level(str(result["level"]), "evidence-limited-v0")
        result["score"] = min(int(result["score"]), 55)
    if missing_variables:
        result.setdefault("non_blocking_gaps", []).append("missing design variables: " + ", ".join(missing_variables[:6]))
        result["level"] = cap_maturity_level(str(result["level"]), "evidence-limited-v0")
        result["score"] = min(int(result["score"]), 60)
    if evidence_sufficiency != "sufficient" or "owner-review-needed" in review_status:
        result.setdefault("non_blocking_gaps", []).append(
            f"canonical XML is {evidence_sufficiency or 'unknown'} / {review_status or 'unreviewed'}"
        )
        result["level"] = cap_maturity_level(str(result["level"]), "public-v0")
        result["score"] = min(int(result["score"]), 72)
    return result


def strip_markdown_inline(value: str) -> str:
    return value.strip().strip("`").strip()


def markdown_section(text: str, heading: str) -> str:
    pattern = rf"^##\s+{re.escape(heading)}\s*$([\s\S]*?)(?=^##\s+|\Z)"
    match = re.search(pattern, text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def markdown_bullets(section: str, limit: int = 12) -> list[str]:
    bullets = []
    for line in section.splitlines():
        match = re.match(r"^\s*-\s+(.+?)\s*$", line)
        if match:
            bullets.append(match.group(1).strip())
    return bullets[:limit]


def markdown_numbered_items(section: str, limit: int = 12) -> list[str]:
    items = []
    for line in section.splitlines():
        match = re.match(r"^\s*\d+\.\s+(.+?)\s*$", line)
        if match:
            items.append(match.group(1).strip())
    return items[:limit]


def markdown_table_rows(section: str, headers: tuple[str, ...], limit: int = 20) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or "---" in stripped:
            continue
        cells = [strip_markdown_inline(cell) for cell in stripped.strip("|").split("|")]
        if not cells or cells[0].lower() == headers[0].lower():
            continue
        if len(cells) < len(headers):
            continue
        row: dict[str, object] = {}
        for header, cell in zip(headers, cells):
            if header == "score":
                try:
                    row[header] = int(cell)
                except ValueError:
                    row[header] = cell
            else:
                row[header] = cell
        rows.append(row)
        if len(rows) >= limit:
            break
    return rows


def extract_current_maturity(text: str) -> str:
    patterns = (
        r"^current_maturity:\s*`?([a-z0-9-]+)`?\s*$",
        r"^Current maturity:\s*`?([a-z0-9-]+)`?\s*$",
        r"^Current maturity:\s+`?([a-z0-9-]+)`?",
    )
    for pattern in patterns:
        match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""


def high_assurance_review(ctx: RepoContext) -> dict[str, object]:
    scorecard_rel = "docs/high-assurance-scorecard.md"
    review_rel = "docs/lifeos-content-review.md"
    scorecard = ctx.read(scorecard_rel)
    review = ctx.read(review_rel)
    if not scorecard and not review:
        return {
            "available": False,
            "scorecard_path": scorecard_rel,
            "content_review_path": review_rel,
            "next_recommendations": [],
            "summary": [],
        }

    overall = markdown_table_rows(
        markdown_section(scorecard, "Overall Scores"),
        ("area", "score", "assurance", "meaning"),
    )
    inneratlas = markdown_table_rows(
        markdown_section(scorecard, "InnerAtlas / Wenxin Scores"),
        ("section", "score", "assurance", "strong_evidence", "main_gap"),
    )
    psp = markdown_table_rows(
        markdown_section(scorecard, "PSP Scores"),
        ("module", "score", "assurance", "current_use", "main_gap"),
    )
    skills = markdown_table_rows(
        markdown_section(scorecard, "Candidate Skill Scores"),
        ("candidate", "score", "assurance", "current_status", "promotion_need"),
    )
    review_summary = markdown_bullets(markdown_section(review, "high_assurance_scorecard"), 8)
    content_next = markdown_numbered_items(markdown_section(review, "next_recommendations"), 8)
    scorecard_next = markdown_numbered_items(markdown_section(scorecard, "Next Evidence To Upgrade"), 8)
    high_now = markdown_bullets(markdown_section(scorecard, "High-Assurance Now"), 10)
    not_high = markdown_bullets(markdown_section(scorecard, "Not High-Assurance Yet"), 10)
    maturity = extract_current_maturity(scorecard) or extract_current_maturity(review)
    return {
        "available": True,
        "scorecard_path": scorecard_rel if scorecard else None,
        "content_review_path": review_rel if review else None,
        "current_maturity": maturity or "unknown",
        "interpretation": (
            "High-assurance review is a semantic assurance layer: it explains what the LifeOS may represent, "
            "route, reuse, or cite, and what must remain downgraded despite structural completion."
        ),
        "overall_scores": overall,
        "inneratlas_scores": inneratlas,
        "psp_scores": psp,
        "candidate_skill_scores": skills,
        "summary": review_summary,
        "high_assurance_now": high_now,
        "not_high_assurance_yet": not_high,
        "next_recommendations": scorecard_next or content_next,
    }


def artifact_maturity_interpretation(name: str, result: dict[str, object]) -> str:
    level = str(result.get("level") or "unknown")
    score = result.get("score", 0)
    if name == "inneratlas":
        return f"InnerAtlas identity source is {level} at {score}/100; use it for public-v0 positioning, but review weak sections before treating all claims as high-assurance."
    if name == "psp":
        return f"PSP person model is {level} at {score}/100; suitable for preliminary routing and boundaries, not full behavior fidelity until validation and language evidence improve."
    if name == "skill_recommendations":
        return f"Skill recommendations are {level} at {score}/100; treat implemented aliases as callable, and keep new candidates behind IPO/owner-alignment promotion gates."
    if name == "avatar_description":
        return f"Avatar description is {level} at {score}/100; useful as the product-facing summary, but it must keep evidence and maturity caveats."
    if name == "design":
        return f"Design taste is {level} at {score}/100; use as a direction/starter unless owner-reviewed taste choices and references are present."
    return f"{name} is {level} at {score}/100."


def artifact_next_recommendations(name: str, result: dict[str, object]) -> list[str]:
    recommendations: list[str] = []
    weak_sections = result.get("weak_sections") or []
    weak_modules = result.get("weak_modules") or []
    non_blocking = result.get("non_blocking_gaps") or []
    blocking = result.get("blocking_gaps") or []
    if name == "inneratlas":
        if weak_sections:
            sections = ", ".join(str(item.get("section")) for item in weak_sections[:4] if isinstance(item, dict))
            recommendations.append(f"补齐 InnerAtlas 弱项：{sections}；为每项增加 evidence、confidence、missing/不能判断说明。")
        recommendations.append("下一轮 evidence intake 优先补领域深度、角色边界、结果指标和对外 pitch 的可引用证据。")
    elif name == "psp":
        if weak_modules:
            modules = ", ".join(str(item.get("module")) for item in weak_modules[:4] if isinstance(item, dict))
            recommendations.append(f"补齐 PSP 弱模块：{modules}。")
        recommendations.append("启动 5-10 个 holdout 决策/回答样本，验证 PSP 的 judgment、interaction、language_fingerprint 和 delegation boundary。")
    elif name == "skill_recommendations":
        recommendations.append("把 implemented alias 和新候选分开：已实现的直接路由，新候选必须经过 IPO Reverse、owner alignment 和输入/过程/输出/验收模板。")
    elif name == "avatar_description":
        recommendations.append("继续使用 owner-approved public-safe one_line；任何更强营销表达都走 publication/public-narrative 路由并保留成熟度披露。")
    elif name == "design":
        recommendations.append("完成 Taste Generator owner review 或 iframe selector；补 5 个正向设计参考和 3 个反偏好，再把 DESIGN 从 inferred starter 升级为 owner-approved。")
    if blocking:
        recommendations.append("先处理 blocking gaps：" + "; ".join(str(gap) for gap in blocking[:3]))
    elif non_blocking:
        recommendations.append("处理非阻塞缺口：" + "; ".join(str(gap) for gap in non_blocking[:3]))
    return recommendations[:5]


def skill_content_maturity(ctx: RepoContext) -> dict[str, object]:
    skills = {
        "inneratlas": inneratlas_content_maturity(ctx),
        "psp": psp_content_maturity(ctx),
        "skill_recommendations": skill_recommendations_content_maturity(ctx),
        "avatar_description": avatar_description_content_maturity(ctx),
        "design": design_content_maturity(ctx),
    }
    weights = {
        "inneratlas": 30,
        "psp": 30,
        "skill_recommendations": 16,
        "avatar_description": 14,
        "design": 10,
    }
    for name, result in skills.items():
        result["interpretation"] = artifact_maturity_interpretation(name, result)
        result["next_recommendations"] = artifact_next_recommendations(name, result)
    available = {name: result for name, result in skills.items() if result.get("level") != "missing"}
    if not available:
        score = 0
        level = "missing"
    else:
        total_weight = sum(weights[name] for name in available)
        score = round(sum(int(available[name].get("score", 0)) * weights[name] for name in available) / total_weight)
        level = maturity_level_from_score(score)
        for name, result in available.items():
            if name not in {"inneratlas", "psp"}:
                continue
            result_level = str(result.get("level", "scaffold"))
            if result_level in CONTENT_MATURITY_ORDER:
                level = cap_maturity_level(level, result_level)
    evidence_level = evidence_maturity(ctx)
    if evidence_level in CONTENT_MATURITY_ORDER:
        level = cap_maturity_level(level, evidence_level)
    blocking = []
    for name, result in skills.items():
        for gap in result.get("blocking_gaps", [])[:3]:
            blocking.append(f"{name}: {gap}")
    review = high_assurance_review(ctx)
    next_recommendations = list(review.get("next_recommendations", []))
    if not next_recommendations:
        for name in ("inneratlas", "psp", "design", "skill_recommendations", "avatar_description"):
            for recommendation in skills[name].get("next_recommendations", [])[:1]:
                next_recommendations.append(str(recommendation))
    return {
        "level": level,
        "score": score,
        "score_out_of": 100,
        "score_type": "heuristic_field_and_evidence_coverage",
        "evidence_maturity_level": evidence_level,
        "meaning": "Skill content maturity summarized from each built-in Skill's expected artifact structure; separate from required/openLifeOS progress completion.",
        "interpretation": "Content maturity is a semantic readiness signal. It must be read with high-assurance review, evidence gaps, and next recommendations; it is not equivalent to scaffold completion.",
        "high_assurance_review": review,
        "next_recommendations": next_recommendations[:8],
        "skills": skills,
        "blocking_gaps": blocking[:12],
    }


CORE_REVIEW_ARTIFACTS = (
    ("avatar_description", "identity/avatar-description/current.yml"),
    ("wenxin", "identity/inneratlas/current/INNERATLAS_REPORT.xml"),
    ("psp", "identity/psp/{person_id}/current/PSP_REPORT.xml"),
    ("design", "DESIGN.md"),
    ("skill_recommendations", "identity/wenxin/skill-recommendations.yml"),
    ("evidence_maturity", "identity/psp/{person_id}/current/EVIDENCE_MATURITY.xml"),
)


def skill_review_surface(ctx: RepoContext) -> list[dict[str, object]]:
    person_id = str(ctx.config.get("person_id") or "unknown")
    surface = []
    for artifact_key, fallback in CORE_REVIEW_ARTIFACTS:
        fallback = fallback.format(person_id=person_id)
        current = current_entrypoint_path(ctx, artifact_key, fallback)
        active = active_artifact_path(ctx, artifact_key)
        surface.append(
            {
                "artifact": artifact_key,
                "current_entrypoint": current,
                "current_exists": ctx.exists(current),
                "active_artifact": active,
                "active_exists": ctx.exists(active) if active else None,
            }
        )
    return surface


def skill_content_review_exists(ctx: RepoContext) -> tuple[bool, str]:
    candidates = ("docs/lifeos-content-review.md", "docs/reviews/lifeos-content-review.md")
    existing = [rel for rel in candidates if ctx.exists(rel)]
    if not existing:
        return fail(
            "missing Skill-produced content review; run the LifeOS Skill review workflow and write "
            "docs/lifeos-content-review.md"
        )
    text = ctx.read(existing[0])
    required = (
        "skill_review",
        "reviewed_artifacts",
        "content_completeness",
        "next_recommendations",
    )
    missing = [marker for marker in required if marker not in text]
    if missing:
        return fail(f"{existing[0]} missing Skill review markers: " + ", ".join(missing))
    return ok(existing[0])


def skill_placement_policy_configured(ctx: RepoContext) -> tuple[bool, str]:
    skills = ctx.read(first_existing(ctx, ("capabilities/README.md", "legacy/skills-v1/README.md", "skills/README.md")))
    matrix = ctx.read("matrix.yml")
    missing = []
    skills_has_policy = (
        "SKILL.md" in skills
        and ("capabilities/<capability-id>" in skills or "capabilities/" in skills or "每条分支" in skills)
        and ("identity/wenxin/skill-recommendations.yml" in skills)
    )
    if not skills_has_policy:
        missing.append("capabilities/README.md placement policy")
    if "placement_policy:" not in matrix and "capability_layers:" not in matrix:
        missing.append("matrix.yml skill_layers.placement_policy")
    if missing:
        return fail("missing: " + ", ".join(missing))
    return ok("instance-local vs installable Skill placement policy configured")


def taste_generator_route_configured(ctx: RepoContext) -> tuple[bool, str]:
    matrix = ctx.read("matrix.yml")
    updates = ctx.read("integrations/skill-sources/default-skills/skill-updates.yml")
    configured = "taste-generator" in matrix or "taste-generator" in updates
    skill_exists = ctx.exists("evolution/organ-systems/taste-generator/SKILL.md")
    if configured and not skill_exists:
        return fail("taste-generator configured but missing evolution/organ-systems/taste-generator/SKILL.md")
    if skill_exists:
        return ok("taste-generator design generation Skill installed")
    return ok("taste-generator route not configured for this schema revision")


def validate_passes(ctx: RepoContext) -> tuple[bool, str]:
    if not VALIDATE_SCRIPT.exists():
        return fail(f"missing {VALIDATE_SCRIPT}")
    result = subprocess.run(
        [sys.executable, str(VALIDATE_SCRIPT), str(ctx.root)],
        text=True,
        capture_output=True,
        check=False,
    )
    output = (result.stdout + result.stderr).strip()
    if result.returncode == 0:
        return ok("validate_avatar_repo.py passed")
    return fail(output or "validate_avatar_repo.py failed")


REQUIRED_ROOT_PATHS = (
    "CATALOG.md",
    "replicateme.yml",
    "LIFEOS-CATALOG.html",
    "README.md",
    "AGENT.md",
    "DESIGN.md",
    "matrix.yml",
    "artifacts/README.md",
    "artifacts/current.yml",
    "identity/README.md",
    "identity/avatar-description/README.md",
    "identity/avatar-description/current.yml",
    "identity/avatar-description/versions.yml",
    "identity/avatar-description/changelog.md",
    "identity/public-profile/profile.yml",
    "identity/inneratlas/ARTIFACTS.xml",
    "identity/inneratlas/current/INNERATLAS_REPORT.xml",
    "identity/design/current/DESIGN_TASTE.xml",
    "identity/wenxin/README.md",
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
)

REQUIRED_ROOT_PATH_OPTIONS = (
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
)


PHASES = (
    Phase(
        "0",
        "Boundary",
        True,
        (
            "security/README.md defines banned materials and publication defaults",
            "matrix.yml records visibility",
        ),
        (
            Check("security boundary file exists", file_exists("security/README.md")),
            Check("visibility is configured", matrix_field("visibility", ("local-only", "private", "public"))),
            Check("security boundary mentions secrets and private material", security_boundary_configured),
        ),
    ),
    Phase(
        "1",
        "Language",
        True,
        (
            "matrix.yml language is zh-CN or en-US",
            "generated root AGENT.md uses that language's template",
        ),
        (
            Check("language is configured", matrix_field("language", ("zh-CN", "en-US"))),
            Check("root Agent exists", file_exists("AGENT.md")),
        ),
    ),
    Phase(
        "2",
        "Setup config and permissions",
        True,
        (
            "replicateme.yml records repo, GitHub owner, memory wiki repo, language, and visibility",
            "replicateme.yml records GitHub, Feishu, Hermes, and wiki sync intent without secrets",
            "git/gh dependencies are checked; gh auth is required only when remote creation is requested",
        ),
        (
            Check("setup YAML exists and is filled", setup_config_exists),
            Check("integration permissions are configured", integration_permissions_configured),
            Check("GitHub tooling is ready or explicitly disabled", github_tooling_ready),
        ),
    ),
    Phase(
        "3",
        "Skeleton",
        True,
        (
            "root AGENT.md, matrix.yml, integrations/agents/openai.yaml",
            "CATALOG.md plus sources, taste, meta-skills, publication, and governance governed-repo layers",
            "artifacts/current.yml latest registry plus PSP XML, evidence maturity XML, and DESIGN.md current entrypoints",
            "replicateme.yml plus identity, metabolism, runtime, evolution, capabilities, identities, integrations, security, and docs layer files",
            "identity/cognition/object-taxonomy.yml and identity/cognition/data-contracts.yml",
            "runtime/memory/working-lessons, identity/memories/long-term, capabilities/*/memory, identity/wenxin skill recommendations/summaries, and identity/cognition/skill-bindings",
            "identity/inneratlas/current/INNERATLAS_REPORT.xml fresh draft",
            "identity/psp/<person-id>/current/PSP_REPORT.xml and versions/PSP_REPORT.<timestamp>.xml scaffold",
            "identity/psp/<person-id>/current/EVIDENCE_MATURITY.xml and versions/EVIDENCE_MATURITY.<timestamp>.xml scaffold",
            "identity/psp/<person-id>/update-log-<timestamp>.md update protocol",
            "identity/psp/<person-id>/INITIALIZATION.md framework adapter guide",
            "evolution/organ-systems/{wenxin,psp,ipo-reverse,taste-generator}/ complete self-evolution systems",
        ),
        (
            Check("required skeleton files exist", required_paths(REQUIRED_ROOT_PATHS)),
            Check("required v1/v2 path options exist", required_path_options(REQUIRED_ROOT_PATH_OPTIONS)),
            Check("artifact registry is configured", artifact_registry_configured),
            Check("cognition taxonomy scaffold is configured", cognition_taxonomy_configured),
            Check("PSP scaffold exists", psp_scaffold_exists),
            Check("Design scaffold exists", design_scaffold_exists),
            Check("Taste Generator route is configured", taste_generator_route_configured),
            Check("PSP update log exists", psp_update_log_exists),
            Check("PSP initialization adapter exists", psp_initialization_exists),
        ),
    ),
    Phase(
        "4",
        "Public profile",
        True,
        (
            "identity/public-profile/profile.yml",
            "owner_name, display_name, person_id, public_summary filled with approved facts",
        ),
        (
            Check("public profile is filled", profile_complete),
        ),
    ),
    Phase(
        "4.5",
        "Evidence sufficiency",
        True,
        (
            "identity/psp/<person-id>/current/EVIDENCE_MATURITY.xml records source coverage, failed sources, incomplete areas, maturity level, and final disclosure requirements",
            "progress reports separate structure readiness from content maturity",
        ),
        (
            Check("evidence sufficiency report exists", evidence_sufficiency_report_configured),
        ),
    ),
    Phase(
        "4.6",
        "Self-evolution output standards",
        True,
        (
            "docs/self-evolution-output-standards.md defines pass/fail keys for Wenxin, PSP XML, Design/Taste Generator, and IPO Reverse; SOUL is paused",
            "generated Wenxin/PSP/Design/IPO artifacts either fill required fields or declare insufficiency with targeted prompts",
        ),
        (
            Check("self-evolution output standards exist", self_evolution_output_standards_configured),
            Check("avatar description claim evidence exists", avatar_description_claim_evidence_configured),
            Check("IPO Reverse artifacts follow standard when present", ipo_reverse_artifacts_follow_standard),
        ),
    ),
    Phase(
        "5",
        "Wenxin self-discovery",
        False,
        (
            "identity/inneratlas/current/INNERATLAS_REPORT.xml or equivalent generated artifact",
            "identity/wenxin/public-positioning.md for public-safe external positioning when needed",
            "identity/wenxin/skill-recommendations.yml for Wenxin-generated candidate Skill recommendations",
        ),
        (
            Check("Wenxin self-discovery artifact exists", wenxin_self_discovery_artifact),
        ),
    ),
    Phase(
        "6",
        "Skill recommendations",
        False,
        (
            "identity/wenxin/skill-recommendations.yml recommends evidence-backed runtime or distilled meta Skills to build next",
            "each recommendation labels machine_name, alias, implemented, summarized, usage_scenarios, skill_type, and promotion_gate",
            "each recommendation labels eligibility_type as top_5_percent_capability_hypothesis or repeated_workflow",
            "each recommendation states evidence_needed and promotion_gate",
            "skill recommendations are calibrated from Wenxin outputs and approved evidence",
        ),
        (
            Check("skill recommendations generated", skill_recommendations_generated),
        ),
    ),
    Phase(
        "7",
        "PSP/person model",
        False,
        (
            "identity/psp/<person-id>/current/PSP_REPORT.xml generated from approved material",
            "PSP has no scaffold/TODO markers and is substantial enough to route behavior",
            "identity/psp/<person-id>/update-log-<timestamp>.md tracks ongoing PSP updates",
        ),
        (
            Check("PSP is generated", psp_generated),
            Check("PSP update log exists", psp_update_log_exists),
        ),
    ),
    Phase(
        "8",
        "Memory wiki and sync",
        False,
        (
            "identity/memories/START-HERE.md has real area entrypoints or external wiki routing",
            "identity/memories/wiki-repo.yml points to the user's GitHub wiki repo",
            "identity/memories/wiki-repo.yml records authoritative source, sync modes, public mirror policy, and collaboration mode",
            "private wiki bodies are linked or abstracted, not copied",
        ),
        (
            Check("memory entrypoints configured", memory_configured),
            Check("memory wiki repo configured", memory_wiki_configured),
        ),
    ),
    Phase(
        "9",
        "Hermes self-evolution sync",
        False,
        (
            "integrations/hermes.yml records update cadence, source usage, targets, and token policy",
            "Hermes can update Wenxin, PSP XML, design, skill recommendations, memory index, and root routing from approved evidence",
            "GitHub collaboration path is explicit",
        ),
        (
            Check("Hermes sync configured", hermes_configured),
        ),
    ),
    Phase(
        "10",
        "Capabilities",
        False,
        (
            "capabilities/ contains durable capability entrypoints or matrix.yml lists runtime/evolution/capability bindings",
            "each capability has role, entrypoint, and visibility where known",
        ),
        (
            Check("capability skills configured", skills_configured),
            Check("skill placement policy configured", skill_placement_policy_configured),
        ),
    ),
    Phase(
        "10.5",
        "Skill-guided content review",
        False,
        (
            "doctor exposes key artifact paths as the input surface for Skill review",
            "the LifeOS Skill, not the script, reviews Wenxin, PSP XML, Design, skill recommendations, and evidence maturity",
            "Skill review writes docs/lifeos-content-review.md with content completeness and next recommendations",
        ),
        (
            Check("Skill-produced content review exists", skill_content_review_exists),
        ),
    ),
    Phase(
        "11",
        "Routing",
        True,
        (
            "root AGENT.md routes identity, Wenxin, PSP, memory, skills, integrations, Hermes, and security questions",
            "root AGENT.md routes artifacts/current.yml, PSP XML, evidence maturity XML, and DESIGN.md as latest artifact entrypoints",
            "route references point to existing repo paths",
        ),
        (
            Check(
                "root route paths are referenced",
                contains(
                    "AGENT.md",
                    (
                        "artifacts/current.yml",
                        "CATALOG.md",
                        "sources/CATALOG.md",
                        "sources/authority.yml",
                        "identity/public-profile",
                        "identity/wenxin",
                        "identity/psp",
                        "taste/current.yml",
                        "DESIGN.md",
                        "meta-skills/current.yml",
                        "publication/current.yml",
                        "publication/public-claims.yml",
                        "governance/",
                        "integrations/",
                        "integrations/hermes",
                        "identity/memories/START-HERE",
                        "identity/cognition/object-taxonomy",
                        "identity/cognition/skill-bindings/data-sources",
                        "integrations/data-sources",
                        "capabilities/",
                        "security/README",
                        "doctor_avatar_repo.py",
                        "content_maturity",
                        "skill_content_maturity",
                        "evolution/alignment/current.yml",
                        "EVIDENCE_MATURITY.xml",
                    ),
                ),
            ),
        ),
    ),
    Phase(
        "12",
        "Final validation",
        True,
        (
            "validate_avatar_repo.py passes",
            "no unresolved template tokens or common secret patterns",
        ),
        (
            Check("validation script passes", validate_passes),
        ),
    ),
)


def run_doctor(root: Path) -> list[PhaseResult]:
    ctx = RepoContext(root)
    results: list[PhaseResult] = []
    for phase in PHASES:
        checks: list[CheckResult] = []
        for check in phase.checks:
            passed, detail = check.fn(ctx)
            checks.append(CheckResult(check.label, passed, detail))
        results.append(PhaseResult(phase.id, phase.name, phase.required, phase.expected_outputs, checks))
    if results:
        content = skill_content_maturity(ctx)
        setattr(results[0], "_content_maturity", content)
        setattr(results[0], "_skill_content_maturity", content.get("skills", {}))
        setattr(results[0], "_skill_review_surface", skill_review_surface(ctx))
        setattr(results[0], "_root", root)
    return results


def completion(results: list[PhaseResult], required_only: bool) -> tuple[int, int, int]:
    selected = [phase for phase in results if phase.required or not required_only]
    done = sum(1 for phase in selected if phase.passed)
    total = len(selected)
    percent = round(done * 100 / total) if total else 100
    return done, total, percent


def skill_review_surface_from_results(results: list[PhaseResult]) -> list[dict[str, object]]:
    return getattr(results[0], "_skill_review_surface", []) if results else []


def content_maturity_from_results(results: list[PhaseResult]) -> dict[str, object]:
    value = getattr(results[0], "_content_maturity", None) if results else None
    if isinstance(value, dict):
        return value
    level = value if isinstance(value, str) else "unknown"
    return {
        "level": level,
        "score": None,
        "score_out_of": 100,
        "meaning": "legacy content maturity value",
        "skills": {},
        "blocking_gaps": [],
    }


def phase_next_action(phase: PhaseResult) -> str:
    if phase.name == "Skill-guided content review":
        return "Run the LifeOS Skill content-review workflow and write docs/lifeos-content-review.md"
    return f"Complete Phase {phase.id}: {phase.name}"


def next_actions(results: list[PhaseResult]) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    open_phases = [phase for phase in results if not phase.passed]
    for phase in [phase for phase in open_phases if phase.required][:3]:
        failed = "; ".join(check.detail for check in phase.checks if not check.passed)
        actions.append(
            {
                "source": "phase_gate",
                "artifact": phase.name,
                "status": "open",
                "detail": failed,
                "next_action": f"Complete required Phase {phase.id}: {phase.name}",
            }
        )

    for phase in open_phases[:3]:
        failed = "; ".join(check.detail for check in phase.checks if not check.passed)
        actions.append(
            {
                "source": "phase_gate",
                "artifact": phase.name,
                "status": "open",
                "detail": failed,
                "next_action": phase_next_action(phase),
            }
        )
    if not actions:
        actions.append(
            {
                "source": "doctor",
                "artifact": "Output Gate",
                "status": "ready",
                "detail": "All current doctor phases passed",
                "next_action": "Proceed to owner review, runtime projection review, or the next evidence intake cycle.",
            }
        )
    return actions


def to_json(results: list[PhaseResult]) -> dict[str, object]:
    required_done, required_total, required_percent = completion(results, True)
    overall_done, overall_total, overall_percent = completion(results, False)
    completed = [
        {"id": phase.id, "name": phase.name, "required": phase.required, "status": "done", "emoji": "✅"}
        for phase in results
        if phase.passed
    ]
    open_steps = [
        {
            "id": phase.id,
            "name": phase.name,
            "required": phase.required,
            "status": "in_progress",
            "emoji": "⚙️",
            "failed_checks": [
                {"label": check.label, "detail": check.detail}
                for check in phase.checks
                if not check.passed
            ],
        }
        for phase in results
        if not phase.passed
    ]
    maturity = content_maturity_from_results(results)
    root = getattr(results[0], "_root", None) if results else None
    life_stage = diagnose_life_stage(root) if root else None
    return {
        "required_completion": {
            "done": required_done,
            "total": required_total,
            "percent": required_percent,
            "meaning": "kernel scaffold required gates only; not full personality completion",
        },
        "overall_completion": {
            "done": overall_done,
            "total": overall_total,
            "percent": overall_percent,
            "meaning": "full openLifeOS flow including evidence-backed generated artifacts",
        },
        "completed_steps": completed,
        "open_steps": open_steps,
        "next_stage": open_steps[0]["name"] if open_steps else "Output Gate",
        "next_actions": next_actions(results),
        "content_maturity": {
            key: value
            for key, value in maturity.items()
            if key != "skills"
        },
        "skill_content_maturity": maturity.get("skills", {}),
        "high_assurance_review": maturity.get("high_assurance_review", {}),
        "content_next_recommendations": maturity.get("next_recommendations", []),
        "life_stage": {
            "stage_id": life_stage.stage_id,
            "stage_name": life_stage.stage_name,
            "age_days": life_stage.age_days,
            "age_label": life_stage.age_label,
            "stage_reason": life_stage.stage_reason,
            "data_flow": list(life_stage.data_flow),
            "meaning": "digital-life lifecycle stage; separate from initialization/progress gates",
        }
        if life_stage
        else None,
        "skill_review_surface": skill_review_surface_from_results(results),
        "phases": [
            {
                "id": phase.id,
                "name": phase.name,
                "required": phase.required,
                "passed": phase.passed,
                "expected_outputs": list(phase.expected_outputs),
                "checks": [
                    {
                        "label": check.label,
                        "passed": check.passed,
                        "detail": check.detail,
                    }
                    for check in phase.checks
                ],
            }
            for phase in results
        ],
    }


def report_language(root: Path) -> str:
    config = read_flat_yaml(root / "replicateme.yml")
    return str(config.get("process_log_language") or config.get("language") or "zh-CN")


PHASE_NAME_ZH = {
    "Boundary": "Boundary / 边界",
    "Language": "Language / 语言",
    "Setup config and permissions": "Setup config and permissions / 配置与权限",
    "Skeleton": "Skeleton / 骨架",
    "Public profile": "Public profile / 公开 profile",
    "Evidence sufficiency": "Evidence sufficiency / 证据充分性",
    "Self-evolution output standards": "Self-evolution output standards / 自进化标准产物",
    "Wenxin self-discovery": "Wenxin self-discovery / 问心自我发现",
    "Skill recommendations": "Skill recommendations / 问心候选 Skill 建议",
    "PSP/person model": "PSP/person model / PSP 人物模型",
    "Memory wiki and sync": "Memory wiki and sync / 记忆 wiki 与同步",
    "Hermes self-evolution sync": "Hermes self-evolution sync / Hermes 自进化同步",
    "Skills": "Skills / Skills 配置",
    "Skill-guided content review": "Skill-guided content review / Skill 内容 review",
    "Routing": "Routing / 路由",
    "Final validation": "Final validation / 最终验证",
    "Output Gate": "Output Gate / 输出门禁",
}


def phase_display_name(name: str, zh: bool) -> str:
    return PHASE_NAME_ZH.get(name, name) if zh else name


def phase_status_emoji(phase: PhaseResult) -> str:
    if phase.passed:
        return "✅"
    return "⚙️"


def check_status_emoji(check: CheckResult) -> str:
    return "✅" if check.passed else "⚙️"


def print_report(results: list[PhaseResult], language: str) -> None:
    required_done, required_total, required_percent = completion(results, True)
    overall_done, overall_total, overall_percent = completion(results, False)
    zh = language == "zh-CN"
    maturity = content_maturity_from_results(results)
    root = getattr(results[0], "_root", None) if results else None
    life_stage = diagnose_life_stage(root) if root else None
    print(
        f"内核脚手架必需完成度：{required_done}/{required_total} ({required_percent}%)"
        if zh
        else f"Kernel scaffold required completion: {required_done}/{required_total} ({required_percent}%)"
    )
    print(
        f"全流程完成度：{overall_done}/{overall_total} ({overall_percent}%)"
        if zh
        else f"Full-flow completion: {overall_done}/{overall_total} ({overall_percent}%)"
    )
    print(
        "说明：内核脚手架完成只代表结构、权限、latest registry 和路由可用；问心、PSP XML、design、memory、Hermes 等需要真实授权材料生成后才算完成。SOUL 当前暂停生成。"
        if zh
        else "Note: scaffold completion only means structure, permissions, latest registry, and routing are ready; Wenxin, PSP XML, design, memory, and Hermes require real approved evidence before they count as complete. SOUL generation is currently paused."
    )
    print(
        (
            f"内容成熟度：{maturity.get('level')}（{maturity.get('score')}/{maturity.get('score_out_of')}；"
            f"evidence maturity={maturity.get('evidence_maturity_level', 'unknown')}；不要把结构 100% 等同于 LifeOS 完成）"
        )
        if zh
        else (
            f"Content maturity: {maturity.get('level')} "
            f"({maturity.get('score')}/{maturity.get('score_out_of')}; "
            f"evidence maturity={maturity.get('evidence_maturity_level', 'unknown')}; "
            "do not equate 100% structure with LifeOS completion)"
        )
    )
    print(
        "说明：这里的内容成熟度分数是机器启发式字段/证据覆盖度；高保证评分见下面的语义 review。"
        if zh
        else "Note: this content maturity score is a heuristic field/evidence coverage score; high-assurance semantic scores are listed below."
    )
    blocking_gaps = maturity.get("blocking_gaps", [])
    if blocking_gaps:
        print("内容成熟度缺口：" if zh else "Content maturity gaps:")
        for gap in blocking_gaps[:5]:
            print(f"- {gap}")
    review = maturity.get("high_assurance_review", {})
    if isinstance(review, dict) and review.get("available"):
        print("高保证评价：" if zh else "High-assurance review:")
        current = review.get("current_maturity") or "unknown"
        print(
            f"- 当前语义成熟度：{current}；高保证评价不是人格分数，而是判断哪些内容可稳定代表、路由、复用或对外引用。"
            if zh
            else f"- Current semantic maturity: {current}; high-assurance review explains what can be represented, routed, reused, or cited."
        )
        for item in list(review.get("summary", []))[:4]:
            print(f"- {item}")
    next_recommendations = maturity.get("next_recommendations", [])
    if next_recommendations:
        print("内容成熟度下一步：" if zh else "Content maturity next steps:")
        for recommendation in next_recommendations[:5]:
            print(f"- {recommendation}")
    if life_stage:
        print(
            f"生命阶段：Stage {life_stage.stage_id} / {life_stage.stage_name}，已存在：{life_stage.age_label}（{life_stage.stage_reason}）"
            if zh
            else f"Life stage: Stage {life_stage.stage_id} / {life_stage.stage_name}, age: {life_stage.age_label} ({life_stage.stage_reason})"
        )
    print()
    print("已完成步骤：" if zh else "Completed steps:")
    for phase in results:
        if phase.passed:
            marker = "必需" if phase.required else "可选/生成"
            if not zh:
                marker = "required" if phase.required else "optional/generated"
            print(f"- {phase_status_emoji(phase)} Phase {phase.id}. {phase_display_name(phase.name, zh)} ({marker})")
    open_phases = [phase for phase in results if not phase.passed]
    print()
    print("未完成步骤：" if zh else "Open steps:")
    if open_phases:
        for phase in open_phases:
            marker = "必需" if phase.required else "可选/生成"
            if not zh:
                marker = "required" if phase.required else "optional/generated"
            failed = "; ".join(check.detail for check in phase.checks if not check.passed)
            print(f"- {phase_status_emoji(phase)} Phase {phase.id}. {phase_display_name(phase.name, zh)} ({marker}): {failed}")
    else:
        print("- 无" if zh else "- None")
    print()
    next_stage = open_phases[0].name if open_phases else "Output Gate"
    print(f"下一阶段：{phase_display_name(next_stage, zh)}" if zh else f"Next stage: {next_stage}")
    print()
    print("下一步建议：" if zh else "Recommended next actions:")
    for index, action in enumerate(next_actions(results)[:5], start=1):
        if zh:
            print(f"{index}. {action['next_action']}（{action['artifact']}: {action['detail']}）")
        else:
            print(f"{index}. {action['next_action']} ({action['artifact']}: {action['detail']})")
    print()
    for phase in results:
        status = "已完成" if phase.passed else "未完成"
        required = "必需" if phase.required else "可选/生成"
        if not zh:
            status = "DONE" if phase.passed else "OPEN"
            required = "required" if phase.required else "optional/generated"
        print(f"{phase_status_emoji(phase)} [{status}] Phase {phase.id}. {phase_display_name(phase.name, zh)} ({required})")
        print("  预期产物：" if zh else "  expected outputs:")
        for output in phase.expected_outputs:
            print(f"  - {output}")
        print("  检查：" if zh else "  checks:")
        for check in phase.checks:
            prefix = "通过" if check.passed else "待完成"
            if not zh:
                prefix = "PASS" if check.passed else "PENDING"
            print(f"  - {check_status_emoji(check)} {prefix}: {check.label} ({check.detail})")
        print()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", help="Avatar repo directory")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero unless all required phases are done")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.target).expanduser().resolve()
    if not root.exists():
        raise SystemExit(f"Target does not exist: {root}")

    results = run_doctor(root)
    report = to_json(results)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_report(results, report_language(root))

    required_percent = report["required_completion"]["percent"]  # type: ignore[index]
    return 1 if args.strict and required_percent < 100 else 0


if __name__ == "__main__":
    raise SystemExit(main())
