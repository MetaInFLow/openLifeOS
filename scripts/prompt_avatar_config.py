#!/usr/bin/env python3
"""Prompt for openLifeOS setup values and write a flat replicateme.yml."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from replicateme_yaml import write_flat_yaml


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "avatar"


def ask(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    return value or default


def ask_bool(label: str, default: bool = False) -> bool:
    default_text = "Y/n" if default else "y/N"
    value = input(f"{label} [{default_text}]: ").strip().lower()
    if not value:
        return default
    return value in {"y", "yes", "true", "1"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="replicateme.yml", help="YAML config path to write")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    print("Stage 1/6: Target Gate - decide whose LifeOS this is and whether the identity is named or anonymous.")
    identity_mode = ask("Identity mode: named or anonymous", "named")
    display_name = ask("Display name / public label", "Target Owner" if identity_mode != "anonymous" else "Anonymous")
    owner_name = ask("Owner name stored in this local config", display_name if identity_mode != "anonymous" else "Anonymous Owner")
    psp_display_name = ask("PSP display name / pseudonym", display_name if identity_mode != "anonymous" else "Pseudonym")
    default_repo = f"{slugify(display_name).title().replace('-', '')}.LifeOS"
    repo_name = ask("LifeOS repo name (custom allowed)", default_repo)
    person_id = ask("Person ID / PSP slug", slugify(psp_display_name))
    print("Stage 2/6: Boundary Gate - configure language, visibility, and external boundaries. No personal evidence is needed yet.")
    language = ask("Language: zh-CN or en-US", "zh-CN")
    process_log_language = ask("Process log language: zh-CN or en-US", language)
    visibility = ask("Avatar repo visibility: local-only, private, public", "local-only")
    github_owner = ask("GitHub owner/org", "MetaInFlow")

    configure_github = ask_bool("Configure GitHub/gh tooling", True)
    create_avatar_repo = ask_bool("Create avatar GitHub repo with gh later", False)
    create_memory_repo = ask_bool("Create private memory wiki GitHub repo with gh later", False)
    memory_repo_name = ask("Memory wiki repo name", f"{repo_name.removesuffix('.Skill')}.wiki")
    memory_repo_visibility = ask("Memory wiki repo visibility", "private")
    wiki_authoritative_source = ask("Wiki authoritative source: github, server-rsync, local-only", "github")
    wiki_rsync_enabled = wiki_authoritative_source == "server-rsync" or ask_bool("Configure rsync server mirror", False)
    wiki_rsync_target = ask("Rsync target label/path (no secrets)", "") if wiki_rsync_enabled else ""

    domains = ask(
        "Recommended skill domains, comma-separated",
        "professional-core, communication, decision-making",
    )

    config = {
        "repo_path": f"output/meta/{repo_name}",
        "repo_name": repo_name,
        "identity_mode": identity_mode,
        "owner_name": owner_name,
        "display_name": display_name,
        "psp_display_name": psp_display_name,
        "person_id": person_id,
        "language": language,
        "process_log_language": process_log_language,
        "visibility": visibility,
        "public_summary": "TODO: owner-approved public summary",
        "public_material_policy": "private-by-default",
        "raw_material_policy": "never-commit",
        "github_owner": github_owner,
        "github_configure": configure_github,
        "github_account_type": "unknown",
        "github_auth_method": "gh-oauth" if configure_github else "skip",
        "github_permissions": "metadata:read, contents:write",
        "github_require_gh": configure_github,
        "github_auth_required": configure_github and (create_avatar_repo or create_memory_repo),
        "github_create_avatar_repo": create_avatar_repo,
        "github_create_memory_repo": create_memory_repo,
        "github_token_policy": "do-not-store; use gh auth or environment variables",
        "memory_repo_name": memory_repo_name,
        "memory_repo_visibility": memory_repo_visibility,
        "memory_repo_path": f"identity/memories/{person_id}-wiki",
        "memory_source_policy": "github-private-wiki",
        "memory_access_policy": "private-by-default",
        "memory_public_mirror": "index-only",
        "memory_collaboration_policy": "private-pr-or-owner-approved-extract",
        "memory_raw_material_policy": "never-copy-raw-private-bodies",
        "memory_allowed_public_exports": "approved-facts, redacted-summaries, abstracted-patterns",
        "wiki_authoritative_source": wiki_authoritative_source,
        "wiki_sync_modes": "github, rsync" if wiki_rsync_enabled else "github",
        "wiki_rsync_enabled": wiki_rsync_enabled,
        "wiki_rsync_target": wiki_rsync_target,
        "feishu_configure": False,
        "feishu_tenant_name": "",
        "feishu_app_id": "",
        "feishu_app_type": "none",
        "feishu_auth_method": "skip",
        "feishu_permissions": "",
        "feishu_source_usage": "",
        "feishu_token_policy": "not-configured",
        "hermes_configure": True,
        "hermes_update_cadence": "on-new-evidence",
        "hermes_source_usage": "github-events, wiki-diff, manual-approved-material",
        "hermes_targets": "identity/wenxin, identity/psp, identity/wenxin/skill-recommendations, identity/memories/index, AGENT.md, github-pr",
        "hermes_token_policy": "env-only-or-platform-secret",
        "wenxin_goals": "self-understanding, public-positioning, field-map, gap-analysis, future-paths, skill-candidates",
        "recommended_skill_domains": domains,
        "skill_recommendations_source": "identity/wenxin/",
    }

    output = Path(args.output).expanduser().resolve()
    write_flat_yaml(output, config)
    print(f"Wrote {output}")
    print(f"Next: python scripts/apply_avatar_config.py {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
