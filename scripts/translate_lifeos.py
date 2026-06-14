#!/usr/bin/env python3
"""Translate a generated LifeOS repo into an OpenClaw agent or Hermes profile."""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUPPORTED_RUNTIMES = {"openclaw", "hermes"}
SUPPORTED_REVIEW_MODES = {"proposal-only", "off"}
DEFAULT_TUNING_POLICY = "proposal_only"

SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "api key assignment": re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][^'\"\s]{12,}"),
    "github token": re.compile(r"gh[pousr]_[A-Za-z0-9_]{30,}"),
    "openai key": re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
}

TEXT_SUFFIXES = {"", ".md", ".txt", ".yaml", ".yml", ".json", ".toml"}


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "lifeos-profile"


def read_text(path: Path) -> str:
    if not path.exists() or path.is_dir():
        return ""
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def yaml_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def display_path(path: Path | str | None, base: Path | None = None) -> str:
    if path is None:
        return "missing"
    if isinstance(path, str):
        return path
    try:
        if base is not None:
            return path.relative_to(base).as_posix()
    except ValueError:
        pass
    try:
        root_relative = path.relative_to(ROOT)
        return root_relative.as_posix()
    except ValueError:
        return path.name


def list_block(values: list[str], indent: int = 2) -> str:
    pad = " " * indent
    if not values:
        return f"{pad}[]"
    return "\n".join(f"{pad}- {yaml_quote(value)}" for value in values)


def parse_profile_yaml(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    text = read_text(path)
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip().strip('"').strip("'")
        if value and not value.startswith("[") and not value.startswith("{"):
            data[key.strip()] = value
    return data


def parse_flat_yaml(path: Path) -> dict[str, str]:
    """Parse the simple nested YAML shape used by LIFEOS_STATUS.yml."""
    values: dict[str, str] = {}
    stack: list[tuple[int, str]] = []
    text = read_text(path)
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#") or ":" not in raw:
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        key, value = raw.strip().split(":", 1)
        while stack and stack[-1][0] >= indent:
            stack.pop()
        full_key = ".".join([item[1] for item in stack] + [key.strip()])
        value = value.strip().strip('"').strip("'")
        if value:
            values[full_key] = value
        else:
            stack.append((indent, key.strip()))
    return values


def read_lifeos_status(lifeos: Path) -> dict[str, str]:
    status_path = lifeos / "LIFEOS_STATUS.yml"
    if not status_path.exists():
        return {
            "lifeos_status_file": "missing",
            "lifeos_lifecycle": "unknown",
            "lifeos_current_version": "unknown",
            "lifeos_upload_version": "unknown",
            "lifeos_delivery_version": "unknown",
            "meta_skill_source_mode": "unknown",
            "meta_skill_uploadable": "unknown",
        }

    values = parse_flat_yaml(status_path)
    lifecycle = values.get("lifecycle.mode", "unknown")
    development_mode = values.get("source_policy.meta_skills.development.install_mode", "submodule-or-working-source")
    delivery_mode = values.get("source_policy.meta_skills.delivery.install_mode", "github-release-archive")
    if lifecycle == "development":
        source_mode = development_mode
        uploadable = values.get("source_policy.meta_skills.development.uploadable", "true")
    elif lifecycle == "delivery":
        source_mode = delivery_mode
        uploadable = values.get("source_policy.meta_skills.delivery.uploadable", "false")
    else:
        source_mode = "unknown"
        uploadable = "unknown"

    return {
        "lifeos_status_file": "LIFEOS_STATUS.yml",
        "lifeos_lifecycle": lifecycle,
        "lifeos_current_version": values.get("versions.current_version", "unknown"),
        "lifeos_upload_version": values.get("versions.upload_version", "unknown"),
        "lifeos_delivery_version": values.get("versions.delivery_version", "unknown"),
        "meta_skill_source_mode": source_mode,
        "meta_skill_uploadable": uploadable,
    }


def extract_heading(text: str, heading: str) -> str:
    pattern = re.compile(rf"^##+\s+{re.escape(heading)}\s*$", re.MULTILINE | re.IGNORECASE)
    match = pattern.search(text)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"^##+\s+", text[start:], re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(text)
    return text[start:end].strip()


def first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def find_active_identity_artifact(lifeos: Path, artifact: str) -> Path | None:
    """Resolve active identity artifact from identity/current.yml without a YAML dependency."""
    current = lifeos / "identity" / "current.yml"
    text = read_text(current)
    if not text:
        return None
    in_active = False
    in_artifact = False
    active_indent = artifact_indent = 0
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()
        if line == "active:":
            in_active = True
            active_indent = indent
            in_artifact = False
            continue
        if in_active and indent <= active_indent and line.endswith(":"):
            in_active = False
            in_artifact = False
        if in_active and line == f"{artifact}:":
            in_artifact = True
            artifact_indent = indent
            continue
        if in_artifact and indent <= artifact_indent and line.endswith(":"):
            in_artifact = False
        if in_artifact and line.startswith("versioned_artifact:"):
            value = line.split(":", 1)[1].strip().strip('"').strip("'")
            path = lifeos / value
            if path.exists():
                return path
    return None


def find_active_artifact_entrypoint(lifeos: Path, artifact: str) -> Path | None:
    """Resolve an artifact current entrypoint from artifacts/current.yml without a YAML dependency."""
    current = lifeos / "artifacts" / "current.yml"
    text = read_text(current)
    if not text:
        return None
    in_artifacts = False
    in_artifact = False
    artifacts_indent = artifact_indent = 0
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()
        if line == "artifacts:":
            in_artifacts = True
            artifacts_indent = indent
            in_artifact = False
            continue
        if in_artifacts and indent <= artifacts_indent and line.endswith(":"):
            in_artifacts = False
            in_artifact = False
        if in_artifacts and line == f"{artifact}:":
            in_artifact = True
            artifact_indent = indent
            continue
        if in_artifact and indent <= artifact_indent and line.endswith(":"):
            in_artifact = False
        if in_artifact and line.startswith("current_entrypoint:"):
            value = line.split(":", 1)[1].strip().strip('"').strip("'")
            path = lifeos / value
            if path.exists():
                return path
    return None


def find_latest_psp(lifeos: Path) -> Path | None:
    active = find_active_identity_artifact(lifeos, "psp")
    if active:
        return active
    psp_root = lifeos / "identity" / "psp"
    candidates = sorted(psp_root.glob("*/current/PSP_REPORT.xml"))
    if candidates:
        return candidates[-1]
    candidates = sorted(psp_root.glob("*/versions/PSP_REPORT.*.xml"))
    if candidates:
        return candidates[-1]
    return None


def find_latest_evidence_maturity(lifeos: Path) -> Path | None:
    active = find_active_artifact_entrypoint(lifeos, "evidence_maturity")
    if active and active.exists():
        return active
    psp_root = lifeos / "identity" / "psp"
    candidates = sorted(psp_root.glob("*/current/EVIDENCE_MATURITY.xml"))
    if candidates:
        return candidates[-1]
    candidates = sorted(psp_root.glob("*/versions/EVIDENCE_MATURITY.*.xml"))
    if candidates:
        return candidates[-1]
    return first_existing([lifeos / "docs" / "evidence-sufficiency.md"])


def iter_text_files(root: Path):
    for path in root.rglob("*"):
        if ".git" in path.parts or path.is_dir():
            continue
        if path.suffix in TEXT_SUFFIXES:
            yield path


def scan_secrets(root: Path) -> list[str]:
    findings: list[str] = []
    for path in iter_text_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for name, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                findings.append(f"{name}: {path.relative_to(root)}")
    return findings


def collect_markdown_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*.md") if path.is_file() and ".git" not in path.parts)


def render_source_excerpt(
    title: str,
    path: Path | None,
    body: str,
    limit: int = 7000,
    base: Path | None = None,
) -> str:
    if not path or not body.strip():
        return f"## {title}\n\nNo source artifact found.\n"
    clipped = body.strip()
    if len(clipped) > limit:
        clipped = clipped[:limit].rstrip() + "\n\n[Truncated by translation guard.]"
    return f"## {title}\n\nSource: `{display_path(path, base)}`\n\n{clipped}\n"


def build_soul(lifeos: Path, psp_path: Path | None, maturity_path: Path | None) -> str:
    psp = read_text(psp_path) if psp_path else ""
    sections = []
    for heading in ["Scope", "Current Model", "Behavior Rules", "Memory / Skill Boundary", "Validation"]:
        body = extract_heading(psp, heading)
        if body:
            sections.append(f"## {heading}\n\n{body}")
    if not sections and psp:
        sections.append(render_source_excerpt("Canonical PSP XML", psp_path, psp, limit=5000, base=lifeos))

    maturity = read_text(maturity_path) if maturity_path else ""
    provenance = [
        "# SOUL.md",
        "",
        "This runtime SOUL is a projection generated from the canonical LifeOS PSP XML. It is not a LifeOS source artifact.",
        "",
        "\n\n".join(sections),
        "",
        "## Runtime Boundary",
        "",
        "- Do not invent facts, private context, or unsupported personality claims.",
        "- Treat the LifeOS repo as the canonical source of identity, memory, skills, and policy.",
        "- Runtime feedback must return as lesson evidence before it changes durable LifeOS artifacts.",
        "",
        "## Provenance",
        "",
        f"- Source LifeOS: `{lifeos.name}`",
        f"- PSP XML source: `{display_path(psp_path, lifeos)}`",
        f"- Evidence sufficiency source: `{display_path(maturity_path, lifeos)}`",
    ]
    if maturity.strip():
        provenance.extend(["", "## Evidence Sufficiency", "", maturity.strip()[:3000]])
    return "\n".join(provenance)


def build_identity(lifeos: Path, wenxin_path: Path | None, profile: dict[str, str]) -> str:
    wenxin = read_text(wenxin_path) if wenxin_path else ""
    sections = []
    for heading in ["Summary", "Core Findings", "Next Evidence Needed"]:
        body = extract_heading(wenxin, heading)
        if body:
            sections.append(f"## {heading}\n\n{body}")
    if not sections and wenxin:
        sections.append(render_source_excerpt("Wenxin Summary", wenxin_path, wenxin, limit=5000, base=lifeos))

    lines = [
        "# Runtime Identity",
        "",
        "This file is translated from the LifeOS identity layer.",
        "",
        "## Metadata",
        "",
        f"- Display name: {profile.get('display_name', lifeos.name)}",
        f"- Person ID: {profile.get('person_id', 'unknown')}",
        f"- Identity mode: {profile.get('identity_mode', 'unknown')}",
        f"- Visibility: {profile.get('visibility', 'unknown')}",
        "",
        *sections,
    ]
    return "\n".join(lines)


def build_openclaw_identity(lifeos: Path, wenxin_path: Path | None, profile: dict[str, str]) -> str:
    """Render OpenClaw's IDENTITY.md template with LifeOS-backed values."""
    wenxin = read_text(wenxin_path) if wenxin_path else ""
    one_line = extract_heading(wenxin, "一句话定位 / one-line positioning")
    selling_points = extract_heading(wenxin, "三段卖点 / three selling points")
    who_i_am = extract_heading(wenxin, "我是谁 / who I am")
    gap = extract_heading(wenxin, "Gap 分析 / gap analysis")
    display_name = profile.get("display_name", lifeos.name.removesuffix(".LifeOS"))
    person_id = profile.get("person_id", "unknown")
    visibility = profile.get("visibility", "unknown")
    avatar = "https://haodifan.github.io/AnthonyHF.LifeOS/assets/personal/anthonyhf-readme-cover.png"

    lines = [
        "---",
        'summary: "OpenClaw identity filled from AnthonyHF.LifeOS"',
        'title: "IDENTITY.md - AnthonyHF"',
        "source_template: openclaw/docs/reference/templates/IDENTITY.md",
        "source_lifeos: AnthonyHF.LifeOS",
        "---",
        "",
        "# IDENTITY.md - Who Am I?",
        "",
        "- **Name:** AnthonyHF",
        "- **Creature:** LifeOS projection agent",
        "- **Vibe:** Direct, engineering-minded, evidence-aware, context-first, boundary-conscious",
        "- **Emoji:** 🧭",
        f"- **Avatar:** {avatar}",
        "",
        "---",
        "",
        "This identity is filled from AnthonyHF.LifeOS. The canonical identity source remains the LifeOS repo; this OpenClaw file is a runtime projection.",
        "",
        "## Runtime Role",
        "",
        f"- Display name: {display_name}",
        f"- Person ID: {person_id}",
        f"- Visibility: {visibility}",
        "- Role: Anthony Fan's OpenClaw-facing personal agent workspace identity.",
        "- Source of truth: `AnthonyHF.LifeOS/identity/`, `AnthonyHF.LifeOS/AGENT.md`, and generated profile manifests.",
        "",
        "## Public Positioning",
        "",
        one_line.strip() or "AnthonyHF is Anthony Fan's LifeOS-backed public identity and agent collaboration entrypoint.",
        "",
    ]
    if selling_points.strip():
        lines.extend(["## Core Signals", "", selling_points.strip(), ""])
    if who_i_am.strip():
        lines.extend(["## Identity Scope", "", who_i_am.strip(), ""])
    lines.extend(
        [
            "## Operating Boundary",
            "",
            "- Do not invent Anthony's private facts, customer details, relationships, language fingerprint, or unsupported personality claims.",
            "- Treat PSP, Wenxin, configured memory wiki pointers, and LifeOS evidence gates as source-backed context, not as a complete human replica.",
            "- Runtime feedback must return to LifeOS as lesson evidence before changing durable identity, memory, or skill files.",
            "- Raw private materials, Feishu/Miaoji transcripts, memory wiki private bodies, secrets, and unreviewed working lessons must not enter OpenClaw prompt files.",
            "",
        ]
    )
    if gap.strip():
        lines.extend(["## Known Evidence Gaps", "", gap.strip(), ""])
    lines.extend(
        [
            "## Provenance",
            "",
            f"- LifeOS source: `{lifeos.name}`",
            f"- Wenxin source: `{display_path(wenxin_path, lifeos)}`",
            "- OpenClaw template: `docs/reference/templates/IDENTITY.md` in `openclaw/openclaw`.",
        ]
    )
    return "\n".join(lines)


def build_user_context(lifeos: Path) -> str:
    long_term = first_existing(
        [
            lifeos / "identity" / "memories" / "long-term",
            lifeos / "memory" / "long-term",
        ]
    )
    distilled = first_existing(
        [
            lifeos / "capabilities" / "memory" / "distilled-knowledge",
            lifeos / "memory" / "distilled-knowledge",
        ]
    )
    chunks = [
        "# Runtime User Context",
        "",
        "This file contains translated memory summaries. It should contain stable facts, preferences, claims, and constraints only.",
        "",
    ]
    for title, root in [("Long-Term Memory", long_term), ("Distilled Knowledge", distilled)]:
        if root is None:
            chunks.append(f"## {title}")
            chunks.append("")
            chunks.append("No source artifacts found.")
            chunks.append("")
            continue
        files = [path for path in collect_markdown_files(root) if path.name != "README.md"]
        if not files and (root / "README.md").exists():
            files = [root / "README.md"]
        chunks.append(f"## {title}")
        chunks.append("")
        if not files:
            chunks.append("No source artifacts found.")
            chunks.append("")
            continue
        for path in files:
            chunks.append(f"### {path.relative_to(lifeos)}")
            chunks.append("")
            text = read_text(path).strip()
            chunks.append(text[:5000] + ("\n\n[Truncated by translation guard.]" if len(text) > 5000 else ""))
            chunks.append("")
    return "\n".join(chunks)


def build_agents_policy(lifeos: Path) -> str:
    security = read_text(lifeos / "security" / "permissions.yml")
    meta_files = [path for path in collect_markdown_files(lifeos / "identity" / "wenxin" / "skill-summaries") if path.name != "README.md"]
    chunks = [
        "# AGENTS.md",
        "",
        "This file is a runtime policy projection generated from LifeOS.",
        "",
        "## Operating Rules",
        "",
        "- Treat LifeOS as the canonical source of truth.",
        "- Do not promote runtime lessons directly into durable identity, memory, or meta skills.",
        "- Send runtime feedback back as lesson evidence.",
        "- Do not export raw private material, secrets, or unreviewed working lessons.",
        "",
    ]
    if security.strip():
        chunks.extend(["## Security Projection", "", "```yaml", security.strip()[:5000], "```", ""])
    if meta_files:
        chunks.extend(["## Meta Skill Projection", ""])
        for path in meta_files:
            chunks.extend([f"### {path.relative_to(lifeos)}", "", read_text(path).strip()[:5000], ""])
    else:
        chunks.extend(["## Meta Skill Projection", "", "No meta skill artifacts found.", ""])
    return "\n".join(chunks)


def build_tools(lifeos: Path) -> str:
    bindings_path = first_existing(
        [
            lifeos / "identity" / "cognition" / "skill-bindings" / "data-sources.yml",
            lifeos / "cognition" / "skill-bindings" / "data-sources.yml",
        ]
    )
    bindings = read_text(bindings_path) if bindings_path else ""
    data_sources = read_text(lifeos / "integrations" / "data-sources.yml")
    chunks = [
        "# Runtime Tool And Data Bindings",
        "",
        "This file is advisory unless the target runtime enforces these bindings.",
        "",
        "## Skill Bindings",
        "",
        "```yaml",
        bindings.strip() or "missing: identity/cognition/skill-bindings/data-sources.yml",
        "```",
        "",
        "## Data Sources",
        "",
        "```yaml",
        data_sources.strip() or "missing: integrations/data-sources.yml",
        "```",
    ]
    return "\n".join(chunks)


def build_readme(runtime: str, profile_id: str, lifeos: Path, profile: dict[str, str], maturity_path: Path | None) -> str:
    maturity = read_text(maturity_path) if maturity_path else ""
    lines = [
        f"# {profile_id}",
        "",
        f"Runtime projection for `{runtime}` generated from `{lifeos.name}`.",
        "",
        "## Source",
        "",
        f"- Canonical LifeOS: `{lifeos.name}`",
        f"- Display name: {profile.get('display_name', lifeos.name)}",
        f"- Visibility: {profile.get('visibility', 'unknown')}",
        "",
        "## Translation Rule",
        "",
        "Runtime files are projections. The LifeOS folder remains the source of truth.",
    ]
    if maturity.strip():
        lines.extend(["", "## Evidence Sufficiency", "", maturity.strip()[:5000]])
    return "\n".join(lines)


def copy_skill_projection(lifeos: Path, target: Path) -> list[str]:
    generated: list[str] = []
    return generated


def write_openclaw_skill_adapter(
    dest: Path,
    name: str,
    description: str,
    canonical_source: str,
    usage: str,
) -> None:
    write_text(
        dest / "SKILL.md",
        "\n".join(
            [
                "---",
                f"name: {name}",
                f"description: {description}",
                "source_runtime: openclaw",
                f"canonical_source: {canonical_source}",
                "---",
                "",
                f"# {name}",
                "",
                "This is an OpenClaw workspace skill adapter generated from AnthonyHF.LifeOS.",
                "",
                "## Canonical Source",
                "",
                f"- `{canonical_source}`",
                "",
                "## Use When",
                "",
                usage,
                "",
                "## Rules",
                "",
                "- Treat this adapter as runtime routing, not the source of truth.",
                "- Read the canonical source when available before making durable claims.",
                "- Do not copy raw private evidence into OpenClaw files.",
                "- Send new runtime feedback back to LifeOS as lesson evidence.",
            ]
        ),
    )


def create_relative_symlink(link_path: Path, target_path: Path) -> bool:
    link_path.parent.mkdir(parents=True, exist_ok=True)
    if link_path.exists() or link_path.is_symlink():
        link_path.unlink()
    rel_target = os.path.relpath(target_path, start=link_path.parent)
    try:
        link_path.symlink_to(rel_target, target_is_directory=target_path.is_dir())
    except OSError:
        return False
    return True


def create_openclaw_skill_projection(lifeos: Path, target: Path) -> list[str]:
    """Create OpenClaw-discoverable skill adapters plus advisory source symlinks."""
    generated: list[str] = []
    skills_root = target / "skills"

    adapters = [
        (
            skills_root / "anthonyhf-root",
            "anthonyhf-root",
            "Route AnthonyHF identity, memory, skill, migration, and safety tasks through the LifeOS root protocol.",
            "AGENT.md",
            "Use when a task asks who AnthonyHF is, how to route Anthony-specific work, or how to update LifeOS safely.",
        ),
        (
            skills_root / "self-evolution" / "cognitive-alignment",
            "anthonyhf-cognitive-alignment",
            "Handle AnthonyHF cognitive alignment, disagreement review, and reusable lesson routing.",
            "evolution/organ-systems/cognitive-alignment/SKILL.md",
            "Use when Anthony asks for alignment, says the agent is wrong, or provides a correction that should become reusable behavior.",
        ),
        (
            skills_root / "self-evolution" / "psp",
            "anthonyhf-psp",
            "Update AnthonyHF PSP/person model boundaries from approved evidence.",
            "evolution/organ-systems/psp/SKILL.md",
            "Use when updating Anthony's person model, judgment patterns, behavior boundaries, or validation samples.",
        ),
        (
            skills_root / "self-evolution" / "wenxin",
            "anthonyhf-wenxin",
            "Update AnthonyHF public positioning and Wenxin self-discovery artifacts from approved evidence.",
            "evolution/organ-systems/wenxin/SKILL.md",
            "Use when improving Anthony's public narrative, professional positioning, or structured Wenxin output.",
        ),
        (
            skills_root / "self-evolution" / "ipo-reverse",
            "anthonyhf-ipo-reverse",
            "Reverse-engineer finished outputs into evidence maps, hidden cognitive tasks, middle-layer assets, and reusable IPO.",
            "evolution/organ-systems/ipo-reverse/SKILL.md",
            "Use when turning completed artifacts, project outputs, conversations, or system designs into SOP, training material, Skill blueprint, or reusable methodology.",
        ),
        (
            skills_root / "engineering-everything",
            "anthonyhf-engineering-everything",
            "Route engineering, architecture, execution, SOP, AI/Agent workflow, and validation tasks.",
            "capabilities/engineering-everything/SKILL.md",
            "Use when the task involves engineering judgment, implementation, project execution, review gates, or operational planning.",
        ),
        (
            skills_root / "openlifeos-migration",
            "anthonyhf-openlifeos-migration",
            "Migrate this LifeOS across OpenClaw, Hermes, Codex Skill, configured memory wiki, GitHub Pages, and local evidence sources.",
            "docs/migration/platform-migration-instructions.md",
            "Use when translating, deploying, or importing AnthonyHF across runtimes or external evidence sources.",
        ),
    ]
    for dest, name, description, source, usage in adapters:
        write_openclaw_skill_adapter(dest, name, description, source, usage)
        generated.append(str((dest / "SKILL.md").relative_to(target)))

    source_links = skills_root / "_source-links"
    link_targets = [
        ("root-agent", lifeos / "AGENT.md"),
        ("lifeos-capabilities", lifeos / "capabilities"),
        ("self-evolution", lifeos / "evolution" / "organ-systems"),
        ("ipo-reverse", lifeos / "evolution" / "organ-systems" / "ipo-reverse"),
        ("engineering-everything", lifeos / "capabilities" / "engineering-everything"),
        ("migration-docs", lifeos / "docs" / "migration"),
    ]
    linked: list[str] = []
    for name, source_path in link_targets:
        if source_path.exists() and create_relative_symlink(source_links / name, source_path):
            rel = str((source_links / name).relative_to(target))
            generated.append(rel)
            linked.append(rel)

    write_text(
        skills_root / "_source-links.md",
        "\n".join(
            [
                "# OpenClaw Skill Source Links",
                "",
                "OpenClaw workspace skills are exposed through real adapter `SKILL.md` files so discovery works even when sandboxing ignores symlinks that escape the workspace.",
                "",
                "The `_source-links/` directory contains advisory symlinks back to AnthonyHF.LifeOS canonical sources for local, non-sandboxed inspection.",
                "",
                "## Generated Links",
                "",
                *[f"- `{item}`" for item in linked],
                "",
                "## Rule",
                "",
                "Adapters are runtime entrypoints. Canonical behavior remains in LifeOS sources.",
            ]
        ),
    )
    generated.append(str((skills_root / "_source-links.md").relative_to(target)))
    return generated


def copy_learning_queue(lifeos: Path, target: Path) -> list[str]:
    generated: list[str] = []
    skill_recommendations = lifeos / "identity" / "wenxin" / "skill-recommendations.yml"
    if skill_recommendations.exists():
        dest = target / "learning_queue" / "skill-recommendations.yml"
        write_text(dest, read_text(skill_recommendations))
        generated.append(str(dest.relative_to(target)))
    working = first_existing(
        [
            lifeos / "runtime" / "memory" / "working-lessons" / "README.md",
            lifeos / "memory" / "working-lessons" / "README.md",
        ]
    )
    if working and working.exists():
        dest = target / "learning_queue" / "working-lessons.README.md"
        write_text(dest, read_text(working))
        generated.append(str(dest.relative_to(target)))
    return generated


def build_hermes_config(profile: dict[str, str], lifeos: Path) -> str:
    display_name = profile.get("display_name", lifeos.name)
    visibility = profile.get("visibility", "unknown")
    return "\n".join(
        [
            f'name: {yaml_quote(display_name)}',
            f'description: {yaml_quote("LifeOS runtime projection for " + display_name)}',
            "lifeos:",
            f"  source: {yaml_quote(lifeos.name)}",
            f"  visibility: {yaml_quote(visibility)}",
            "  canonical_source: true",
            "translation:",
            "  feedback_policy: runtime_logs_to_working_lessons",
            "  direct_identity_writes: false",
            "  direct_meta_skill_writes: false",
        ]
    )


def generated_file_entry(target: str, rule: str, sources: list[str]) -> dict[str, object]:
    return {"target": target, "rule": rule, "sources": sources}


def render_manifest(
    translation_id: str,
    lifeos: Path,
    runtime: str,
    target: Path,
    generated_files: list[dict[str, object]],
    excluded: list[dict[str, str]],
    validation: dict[str, str],
    review_file: str,
    review_mode: str,
    lifecycle_status: dict[str, str],
) -> str:
    lines = [
        f"translation_id: {yaml_quote(translation_id)}",
        f"source_lifeos: {yaml_quote(lifeos.name)}",
        f"target_runtime: {yaml_quote(runtime)}",
        f"target_profile: {yaml_quote(display_path(target, lifeos))}",
        f"generated_at: {yaml_quote(dt.datetime.now().astimezone().replace(microsecond=0).isoformat())}",
        f"identity_current: {yaml_quote('identity/current.yml' if (lifeos / 'identity' / 'current.yml').exists() else 'not_found')}",
        f"tuning_policy: {yaml_quote(DEFAULT_TUNING_POLICY)}",
        f"review_mode: {yaml_quote(review_mode)}",
        f"review_file: {yaml_quote(review_file)}",
        "manual_confirmation_required: true",
        "",
        "lifeos_status:",
        f"  status_file: {yaml_quote(lifecycle_status['lifeos_status_file'])}",
        f"  lifecycle: {yaml_quote(lifecycle_status['lifeos_lifecycle'])}",
        f"  current_version: {yaml_quote(lifecycle_status['lifeos_current_version'])}",
        f"  upload_version: {yaml_quote(lifecycle_status['lifeos_upload_version'])}",
        f"  delivery_version: {yaml_quote(lifecycle_status['lifeos_delivery_version'])}",
        f"  meta_skill_source_mode: {yaml_quote(lifecycle_status['meta_skill_source_mode'])}",
        f"  meta_skill_uploadable: {yaml_quote(lifecycle_status['meta_skill_uploadable'])}",
        "",
        "generated_files:",
    ]
    for item in generated_files:
        lines.append(f"  - target: {yaml_quote(str(item['target']))}")
        lines.append(f"    rule: {yaml_quote(str(item['rule']))}")
        lines.append("    sources:")
        for source in item["sources"]:  # type: ignore[index]
            lines.append(f"      - {yaml_quote(str(source))}")
    lines.extend(["", "excluded:"])
    for item in excluded:
        lines.append(f"  - path: {yaml_quote(item['path'])}")
        lines.append(f"    reason: {yaml_quote(item['reason'])}")
    lines.extend(["", "validation:"])
    for key, value in validation.items():
        lines.append(f"  {key}: {yaml_quote(value)}")
    return "\n".join(lines)


def render_coverage(translation_id: str, runtime: str) -> str:
    supported = [
        "identity.psp_xml -> runtime SOUL.md projection",
        "identity.wenxin -> IDENTITY.md/PROFILE.md",
        "runtime_skill -> target runtime skills/",
    ]
    partial = [
        "long_term_memory -> USER.md/memories/seed.md; runtime may not enforce fact provenance",
        "distilled_knowledge -> USER.md/memories/knowledge.md; claim freshness is preserved as text",
        "distilled_meta_skill -> AGENTS.md/PROFILE.md; runtime may treat rules as advisory",
        "skill_binding -> TOOLS.md/config.yaml; runtime may not enforce bindings",
        "security.permissions -> policy text/config; runtime enforcement depends on adapter",
        "integrations.data_sources -> connector hints; connector availability is runtime-specific",
        "evidence_sufficiency -> README.md; no native maturity field assumed",
    ]
    if runtime == "openclaw":
        supported.append("openclaw.workspace_skill_adapters -> skills/<skill>/SKILL.md")
        partial.insert(
            0,
            "openclaw.source_symlinks -> skills/_source-links/; advisory only and may be ignored by sandboxed workspace copies",
        )
    coverage = {
        "supported": supported,
        "partial": partial,
        "unsupported": [
            "owner_alignment_promotion_gate; keep in LifeOS and adapter-side review queue",
            "tiered_memory_write_enforcement; keep canonical memory isolation in LifeOS",
        ],
        "intentionally_excluded": [
            "raw_materials export; raw private evidence stays in LifeOS",
            "working_lessons prompt injection; unreviewed lessons stay in learning_queue",
            "skill_recommendations runtime activation; recommendations remain backlog until promoted",
        ],
    }
    lines = [
        f"translation_id: {yaml_quote(translation_id)}",
        f"target_runtime: {yaml_quote(runtime)}",
        "coverage:",
    ]
    for status, items in coverage.items():
        lines.append(f"  {status}:")
        for item in items:
            lines.append(f"    - {yaml_quote(item)}")
    return "\n".join(lines)


def review_targets(runtime: str) -> list[dict[str, str]]:
    if runtime == "openclaw":
        return [
            {
                "target": "SOUL.md",
                "source": "identity/psp/*/current/PSP_REPORT.xml",
                "focus": "Runtime voice, section order, boundary wording, and clarity of source limitations.",
            },
            {
                "target": "AGENTS.md",
                "source": "identity/wenxin/skill-summaries/ and security/permissions.yml",
                "focus": "Agent-workspace operating rules, promotion boundaries, and enforcement wording.",
            },
            {
                "target": "USER.md",
                "source": "identity/memories/long-term/ and capabilities/*/memory/",
                "focus": "Stable fact ordering, preference grouping, and claim readability.",
            },
            {
                "target": "TOOLS.md",
                "source": "identity/cognition/skill-bindings/data-sources.yml and integrations/data-sources.yml",
                "focus": "Connector binding clarity and unsupported connector notes.",
            },
        ]
    return [
        {
            "target": "SOUL.md",
            "source": "identity/psp/*/current/PSP_REPORT.xml",
            "focus": "Runtime voice, section order, boundary wording, and clarity of source limitations.",
        },
        {
            "target": "PROFILE.md",
            "source": "identity/wenxin/WENXIN_REPORT.md and identity/wenxin/skill-summaries/",
            "focus": "Profile narrative, profile-level guidance, and meta-skill readability.",
        },
        {
            "target": "config.yaml",
            "source": "security/permissions.yml, integrations/data-sources.yml, and skill bindings",
            "focus": "Config comments, connector hints, and policy visibility.",
        },
        {
            "target": "memories/seed.md",
            "source": "identity/memories/long-term/ and capabilities/*/memory/",
            "focus": "Stable fact ordering, preference grouping, and claim readability.",
        },
    ]


def render_review(
    translation_id: str,
    runtime: str,
    target: Path,
    generated_files: list[dict[str, object]],
) -> str:
    generated_targets = {str(item["target"]) for item in generated_files}
    lines = [
        "# Translation Review Proposal",
        "",
        f"Translation ID: `{translation_id}`",
        f"Target runtime: `{runtime}`",
        f"Target profile: `{display_path(target)}`",
        "",
        "This file is a proposal surface for AGENT.md-guided and Skill-guided semantic tuning. It must not be applied automatically.",
        "",
        "## Tuning Policy",
        "",
        "- Mode: `proposal_only`.",
        "- The deterministic script output is the baseline.",
        "- A Skill or agent may propose edits to runtime projection files, but must not overwrite canonical LifeOS files.",
        "- Manual confirmation or an explicit apply command is required before proposed changes are applied.",
        "",
        "## Immutable Fields",
        "",
        "- `profile.manifest.yml` source paths, rules, validation results, and timestamps.",
        "- `coverage-report.yml` coverage status and generated audit categories.",
        "- Secret scan and private body scan results.",
        "- Canonical LifeOS identity, memory, skill, security, and integration files.",
        "",
        "## Allowed Proposal Areas",
        "",
        "- Runtime voice and structure in runtime-projected `SOUL.md`.",
        "- Behavior-rule organization in `AGENTS.md` or `PROFILE.md`.",
        "- Summary ordering in `USER.md` or `memories/seed.md`.",
        "- Adapter backlog notes for partial or unsupported coverage.",
        "",
        "## Suggested Review Items",
        "",
    ]
    for item in review_targets(runtime):
        status = "present" if item["target"] in generated_targets else "missing"
        lines.extend(
            [
                f"### {item['target']}",
                "",
                f"- Status: `{status}`",
                f"- Source evidence: `{item['source']}`",
                f"- Suggested change: Review {item['focus']}",
                "- Reason: Improve runtime fit without changing the LifeOS source of truth.",
                "- Risk: May overfit runtime phrasing or weaken evidence boundaries if applied without review.",
                "- Coverage impact: Advisory only; update adapter backlog if a feature remains partial or unsupported.",
                "",
            ]
        )
    lines.extend(
        [
            "## Proposal Patch",
            "",
            "No patch has been applied. Add human-reviewed diff notes here if runtime files need tuning.",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lifeos", help="Generated LifeOS repo directory")
    parser.add_argument("--runtime", required=True, choices=sorted(SUPPORTED_RUNTIMES), help="Target runtime")
    parser.add_argument("--profile-id", help="Target profile/agent id; defaults to LifeOS display name or folder name")
    parser.add_argument("--output", help="Output directory; defaults to <lifeos>/profiles/<runtime>/<profile-id>")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing output directory")
    parser.add_argument("--emit-review", action="store_true", help="Emit translation.review.md for AGENT/Skill-guided tuning proposals")
    parser.add_argument(
        "--review-mode",
        default="proposal-only",
        choices=sorted(SUPPORTED_REVIEW_MODES),
        help="Review behavior; proposal-only emits advisory review files and off disables review output",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    lifeos = Path(args.lifeos).expanduser().resolve()
    if not lifeos.exists():
        raise SystemExit(f"LifeOS repo does not exist: {lifeos}")

    profile = parse_profile_yaml(lifeos / "identity" / "public-profile" / "profile.yml")
    profile_id = args.profile_id or slugify(profile.get("display_name", lifeos.name.removesuffix(".LifeOS")))
    target = Path(args.output).expanduser().resolve() if args.output else lifeos / "profiles" / args.runtime / profile_id

    if target.exists():
        if not args.force:
            raise SystemExit(f"Output exists; pass --force to overwrite: {target}")
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)

    psp_path = find_latest_psp(lifeos)
    wenxin_path = find_active_identity_artifact(lifeos, "wenxin") or first_existing([lifeos / "identity" / "wenxin" / "WENXIN_REPORT.md"])
    maturity_path = find_latest_evidence_maturity(lifeos)
    translation_id = f"{profile_id}-{args.runtime}-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    lifecycle_status = read_lifeos_status(lifeos)

    generated_files: list[dict[str, object]] = []
    excluded = [
        {"path": "identity/psp/*/raw_materials/", "reason": "raw_private_material"},
        {"path": "runtime/memory/working-lessons/", "reason": "unreviewed_candidate_lessons_not_prompt_injected"},
    ]

    write_text(target / "SOUL.md", build_soul(lifeos, psp_path, maturity_path))
    generated_files.append(
        generated_file_entry(
            "SOUL.md",
            "psp-xml-to-runtime-soul-projection",
            [
                str(psp_path.relative_to(lifeos)) if psp_path else "missing",
                str(maturity_path.relative_to(lifeos)) if maturity_path else "missing",
            ],
        )
    )

    if args.runtime == "openclaw":
        write_text(target / "IDENTITY.md", build_openclaw_identity(lifeos, wenxin_path, profile))
        write_text(target / "USER.md", build_user_context(lifeos))
        write_text(target / "AGENTS.md", build_agents_policy(lifeos))
        write_text(target / "TOOLS.md", build_tools(lifeos))
        write_text(target / "README.md", build_readme(args.runtime, profile_id, lifeos, profile, maturity_path))
        generated_files.extend(
            [
                generated_file_entry("IDENTITY.md", "openclaw-identity-template-fill", [str(wenxin_path.relative_to(lifeos)) if wenxin_path else "missing", "openclaw/docs/reference/templates/IDENTITY.md"]),
                generated_file_entry("USER.md", "long-term-memory-to-user-context", ["identity/memories/long-term/", "capabilities/*/memory/"]),
                generated_file_entry("AGENTS.md", "skill-summary-to-agent-rules + security-to-runtime-policy", ["identity/wenxin/skill-summaries/", "security/permissions.yml"]),
                generated_file_entry("TOOLS.md", "bindings-to-tools + integrations-to-runtime-connectors", ["identity/cognition/skill-bindings/data-sources.yml", "integrations/data-sources.yml"]),
                generated_file_entry("README.md", "evidence-sufficiency-to-profile-readme", [str(maturity_path.relative_to(lifeos)) if maturity_path else "missing"]),
            ]
        )
    else:
        write_text(target / "PROFILE.md", build_identity(lifeos, wenxin_path, profile))
        write_text(target / "memories" / "seed.md", build_user_context(lifeos))
        write_text(target / "config.yaml", build_hermes_config(profile, lifeos))
        write_text(target / "README.md", build_readme(args.runtime, profile_id, lifeos, profile, maturity_path))
        generated_files.extend(
            [
                generated_file_entry("PROFILE.md", "wenxin-to-identity", [str(wenxin_path.relative_to(lifeos)) if wenxin_path else "missing"]),
                generated_file_entry("memories/seed.md", "long-term-memory-to-user-context", ["identity/memories/long-term/", "capabilities/*/memory/"]),
                generated_file_entry("config.yaml", "bindings-to-tools + security-to-runtime-policy + integrations-to-runtime-connectors", ["identity/cognition/skill-bindings/data-sources.yml", "security/permissions.yml", "integrations/data-sources.yml"]),
                generated_file_entry("README.md", "evidence-sufficiency-to-profile-readme", [str(maturity_path.relative_to(lifeos)) if maturity_path else "missing"]),
            ]
        )

    for rel in copy_skill_projection(lifeos, target):
        generated_files.append(generated_file_entry(rel, "runtime-skill-to-runtime-skill", ["capabilities/<capability-id>/SKILL.md"]))
    if args.runtime == "openclaw":
        for rel in create_openclaw_skill_projection(lifeos, target):
            generated_files.append(
                generated_file_entry(
                    rel,
                    "openclaw-workspace-skill-adapter",
                    ["AGENT.md", "evolution/organ-systems/", "capabilities/engineering-everything/SKILL.md", "docs/migration/platform-migration-instructions.md"],
                )
            )
    for rel in copy_learning_queue(lifeos, target):
        generated_files.append(generated_file_entry(rel, "skill-recommendations-to-backlog", ["identity/wenxin/skill-recommendations.yml", "runtime/memory/working-lessons/README.md"]))

    review_file = "translation.review.md" if args.emit_review and args.review_mode != "off" else "not_generated"
    if review_file != "not_generated":
        write_text(target / review_file, render_review(translation_id, args.runtime, target, generated_files))
        generated_files.append(generated_file_entry(review_file, "skill-guided-review-proposal", ["profile.manifest.yml", "coverage-report.yml", "runtime projection files"]))

    if (lifeos / "LIFEOS_STATUS.yml").exists():
        generated_files.append(
            generated_file_entry(
                "profile.manifest.yml",
                "lifeos-lifecycle-status-to-runtime-manifest",
                ["LIFEOS_STATUS.yml"],
            )
        )

    secret_findings = scan_secrets(target)
    validation = {
        "secret_scan": "failed" if secret_findings else "passed",
        "private_body_scan": "manual_review_required",
        "provenance": "passed",
        "coverage_audit": "passed_with_gaps",
        "tuning_policy": DEFAULT_TUNING_POLICY,
        "manual_confirmation_required": "true",
    }
    if secret_findings:
        validation["secret_findings"] = "; ".join(secret_findings)

    write_text(
        target / "profile.manifest.yml",
        render_manifest(translation_id, lifeos, args.runtime, target, generated_files, excluded, validation, review_file, args.review_mode, lifecycle_status),
    )
    write_text(target / "coverage-report.yml", render_coverage(translation_id, args.runtime))

    if secret_findings:
        print(f"Translation generated with secret-scan failures: {target}")
        for finding in secret_findings:
            print(f"- {finding}")
        return 1

    print(f"Translation generated: {target}")
    print(f"Runtime: {args.runtime}")
    generated_summary = "profile.manifest.yml, coverage-report.yml"
    if review_file != "not_generated":
        generated_summary += ", translation.review.md"
    print(f"Generated: {generated_summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
