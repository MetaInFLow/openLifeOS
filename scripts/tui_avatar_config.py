#!/usr/bin/env python3
"""TUI-style wizard for openLifeOS personal setup and permission fields."""

from __future__ import annotations

import argparse
import os
import re
import textwrap
from pathlib import Path

from replicateme_yaml import write_flat_yaml


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "avatar"


def clear_screen() -> None:
    if os.environ.get("TERM"):
        print("\033[2J\033[H", end="")


class Wizard:
    def __init__(self, no_clear: bool = False) -> None:
        self.no_clear = no_clear

    def section(self, index: int, total: int, title: str, body: str = "") -> None:
        if not self.no_clear:
            clear_screen()
        print(f"openLifeOS Setup Wizard  [{index}/{total}]")
        print("=" * 72)
        print(title)
        print("-" * 72)
        if body:
            print(textwrap.fill(body, width=72))
            print()

    def ask(self, label: str, default: str = "") -> str:
        suffix = f" [{default}]" if default else ""
        value = input(f"{label}{suffix}: ").strip()
        return value or default

    def ask_bool(self, label: str, default: bool = False) -> bool:
        default_text = "Y/n" if default else "y/N"
        value = input(f"{label} [{default_text}]: ").strip().lower()
        if not value:
            return default
        return value in {"y", "yes", "true", "1"}

    def choose(self, label: str, options: list[str], default: str) -> str:
        default_index = options.index(default) + 1 if default in options else 1
        print(label)
        for idx, option in enumerate(options, 1):
            marker = "*" if idx == default_index else " "
            print(f"  {idx}. {option} {marker}")
        while True:
            raw = input(f"Choose [default {default_index}]: ").strip()
            if not raw:
                return options[default_index - 1]
            if raw.isdigit() and 1 <= int(raw) <= len(options):
                return options[int(raw) - 1]
            if raw in options:
                return raw
            print("Invalid choice.")

    def multi(self, label: str, options: list[str], defaults: list[str]) -> list[str]:
        default_indexes = [str(options.index(item) + 1) for item in defaults if item in options]
        default_text = ",".join(default_indexes)
        print(label)
        for idx, option in enumerate(options, 1):
            marker = "*" if option in defaults else " "
            print(f"  {idx}. {option} {marker}")
        print("Use comma-separated numbers, 'all', or 'none'.")
        while True:
            raw = input(f"Choose [default {default_text or 'none'}]: ").strip().lower()
            if not raw:
                return defaults
            if raw == "all":
                return options
            if raw == "none":
                return []
            selected: list[str] = []
            ok = True
            for part in raw.split(","):
                part = part.strip()
                if not part.isdigit() or not (1 <= int(part) <= len(options)):
                    ok = False
                    break
                selected.append(options[int(part) - 1])
            if ok:
                return selected
            print("Invalid selection.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="replicateme.yml", help="YAML config path to write")
    parser.add_argument("--no-clear", action="store_true", help="Do not clear the terminal between sections")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    wizard = Wizard(no_clear=args.no_clear)
    total = 8

    wizard.section(
        1,
        total,
        "Target Gate / 目标确认",
        "当前阶段：确认要为谁初始化 LifeOS，以及是否使用匿名身份。这一阶段不需要个人材料，只决定 repo、显示名、PSP 化名和路径安全的 person_id。",
    )
    identity_mode = wizard.choose("Identity mode / 身份模式", ["named", "anonymous"], "named")
    display_name = wizard.ask("Display name / public label", "Target Owner" if identity_mode == "named" else "Anonymous")
    owner_name = wizard.ask("Owner name stored in this local config", display_name if identity_mode == "named" else "Anonymous Owner")
    psp_display_name = wizard.ask("PSP display name / pseudonym", display_name if identity_mode == "named" else "Pseudonym")
    default_repo = f"{slugify(display_name).title().replace('-', '')}.LifeOS"
    repo_name = wizard.ask("LifeOS repo name (custom allowed)", default_repo)
    person_id = wizard.ask("Person ID / PSP slug", slugify(psp_display_name))
    repo_path = wizard.ask("Local repo path", f"output/meta/{repo_name}")
    language = wizard.choose("Skill language", ["zh-CN", "en-US"], "zh-CN")
    process_log_language = wizard.choose("Process log language / 过程日志语言", ["zh-CN", "en-US"], language)
    visibility = wizard.choose("Avatar repo visibility", ["local-only", "private", "public"], "local-only")

    wizard.section(
        2,
        total,
        "Boundary Gate / 公开边界",
        "当前阶段：确认 visibility、公开材料策略和禁入内容。仍然不需要个人材料；这里只记录未来材料怎么进入系统。",
    )
    public_summary = wizard.ask("Approved one-line public summary", "TODO: owner-approved public summary")
    public_material_policy = wizard.choose(
        "Public material policy",
        ["public-only", "approved-extracts", "private-by-default"],
        "private-by-default",
    )
    raw_material_policy = wizard.choose(
        "Raw private material policy",
        ["never-commit", "local-only", "private-repo-only"],
        "never-commit",
    )

    wizard.section(
        3,
        total,
        "GitHub permissions / GitHub 权限",
        "推荐使用 GitHub CLI 登录。不要把 GitHub token 写进 YAML 或 repo。",
    )
    github_configure = wizard.ask_bool("Configure GitHub integration", True)
    github_owner = wizard.ask("GitHub user/org", "MetaInFlow") if github_configure else ""
    github_account_type = wizard.choose(
        "GitHub account type",
        ["user", "org", "unknown"],
        "org",
    ) if github_configure else "unknown"
    github_auth_method = wizard.choose(
        "GitHub auth method",
        ["gh-oauth", "fine-grained-token-env", "manual", "skip"],
        "gh-oauth",
    ) if github_configure else "skip"
    github_permissions = wizard.multi(
        "GitHub permissions/scopes needed",
        ["metadata:read", "contents:read", "contents:write", "issues:write", "pull_requests:write", "actions:read", "workflows:write"],
        ["metadata:read", "contents:write"],
    ) if github_configure else []
    create_avatar_repo = wizard.ask_bool("Create avatar GitHub repo later with gh", False) if github_configure else False
    create_memory_repo = wizard.ask_bool("Create memory wiki GitHub repo later with gh", False) if github_configure else False

    wizard.section(
        4,
        total,
        "Memory wiki repo / 长期记忆仓库",
        "openLifeOS 会引导用户在 GitHub 上创建自己的长期 wiki repo，只在 avatar repo 中保存入口和边界。",
    )
    memory_repo_name = wizard.ask("Memory wiki repo name", f"{repo_name.removesuffix('.Skill')}.wiki")
    memory_repo_visibility = wizard.choose("Memory wiki repo visibility", ["private", "public"], "private")
    memory_repo_path = wizard.ask("Memory local/submodule path", f"identity/memories/{person_id}-wiki")
    memory_source_policy = wizard.choose(
        "Memory source policy",
        ["github-private-wiki", "external-private-wiki", "server-rsync", "manual-approved-extracts"],
        "github-private-wiki",
    )
    memory_access_policy = "private-by-default"
    memory_public_mirror = wizard.choose(
        "Memory public mirror",
        ["index-only", "approved-derived", "none"],
        "index-only",
    )
    memory_collaboration_policy = wizard.choose(
        "Memory collaboration policy",
        ["private-pr-or-owner-approved-extract", "private-pr-only", "owner-approved-extract-only"],
        "private-pr-or-owner-approved-extract",
    )
    memory_raw_material_policy = "never-copy-raw-private-bodies"
    memory_allowed_public_exports = ["approved-facts", "redacted-summaries", "abstracted-patterns"]
    wiki_authoritative_source = wizard.choose(
        "Authoritative wiki source",
        ["github", "server-rsync", "local-only"],
        "github",
    )
    wiki_rsync_enabled = wiki_authoritative_source == "server-rsync" or wizard.ask_bool("Configure rsync server mirror", False)
    wiki_sync_defaults = ["github", "rsync"] if wiki_rsync_enabled else ["github"]
    wiki_sync_modes = wizard.multi(
        "Wiki sync modes",
        ["github", "rsync", "manual-export"],
        wiki_sync_defaults,
    )
    wiki_rsync_target = wizard.ask("Rsync target label/path (no secrets)", "") if wiki_rsync_enabled else ""

    wizard.section(
        5,
        total,
        "Feishu permissions / 飞书权限",
        "这里只记录 app 类型、权限需求和 token 存储策略。不要输入 app_secret、tenant token 或 user token。",
    )
    feishu_configure = wizard.ask_bool("Configure Feishu/Lark integration", False)
    feishu_tenant_name = wizard.ask("Feishu tenant/workspace name", "") if feishu_configure else ""
    feishu_app_id = wizard.ask("Feishu app_id (non-secret, optional)", "") if feishu_configure else ""
    feishu_app_type = wizard.choose(
        "Feishu app type",
        ["self-built-app", "user-oauth-app", "manual-export", "unknown"],
        "manual-export",
    ) if feishu_configure else "none"
    feishu_auth_method = wizard.choose(
        "Feishu auth method",
        ["env-only", "manual-export", "oauth", "skip"],
        "env-only",
    ) if feishu_configure else "skip"
    feishu_permissions = wizard.multi(
        "Feishu permissions needed",
        ["docs:read", "drive:read", "wiki:read", "meetings:read", "contacts:read"],
        ["docs:read", "wiki:read"],
    ) if feishu_configure else []
    feishu_source_usage = wizard.multi(
        "Allowed Feishu source usage",
        ["wenxin-self-discovery", "public-positioning", "psp-distillation", "memory-index", "raw-archive"],
        ["wenxin-self-discovery", "public-positioning", "psp-distillation", "memory-index"],
    ) if feishu_configure else []
    feishu_token_policy = "env-only" if feishu_configure else "not-configured"

    wizard.section(
        6,
        total,
        "Wenxin self-discovery / 问心自我发现",
        "当前阶段：只配置下一轮 Evidence Intake 的目标。Wenxin 会在用户明确授权材料后回答“我是谁、站在哪、差多少、往哪走”，不是初始化时凭空生成。",
    )
    wenxin_goals = wizard.multi(
        "Wenxin goals",
        ["self-understanding", "public-positioning", "field-map", "gap-analysis", "future-paths", "skill-candidates"],
        ["self-understanding", "public-positioning", "field-map", "gap-analysis", "future-paths", "skill-candidates"],
    )

    wizard.section(
        7,
        total,
        "Hermes and Skill recommendations / Hermes 与问心候选 Skill 建议",
        "Hermes 用授权新证据持续更新 Wenxin、PSP、Skill recommendations、memory index 和根路由。domain 会生成第一版 skill-recommendations.yml，Wenxin 生成后还要重新校准。",
    )
    hermes_configure = wizard.ask_bool("Configure Hermes self-evolution sync", True)
    hermes_update_cadence = wizard.choose(
        "Hermes update cadence",
        ["on-new-evidence", "daily", "weekly", "manual"],
        "on-new-evidence",
    ) if hermes_configure else "manual"
    hermes_source_usage = wizard.multi(
        "Hermes source usage",
        ["github-events", "feishu-export", "wiki-diff", "manual-approved-material"],
        ["github-events", "wiki-diff", "manual-approved-material"],
    ) if hermes_configure else []
    hermes_targets = wizard.multi(
        "Hermes update targets",
        ["identity/wenxin", "identity/psp", "identity/wenxin/skill-recommendations", "identity/memories/index", "AGENT.md", "github-pr"],
        ["identity/wenxin", "identity/psp", "identity/wenxin/skill-recommendations", "identity/memories/index", "AGENT.md", "github-pr"],
    ) if hermes_configure else []
    domains = wizard.multi(
        "Recommended personal Skill domains",
        ["engineering", "professional-core", "communication", "decision-making", "founder", "sales", "product", "operations", "research"],
        ["professional-core", "communication", "decision-making"],
    )

    wizard.section(8, total, "Review / 生成 YAML", "确认后写入配置文件。")
    config = {
        "repo_path": repo_path,
        "repo_name": repo_name,
        "identity_mode": identity_mode,
        "owner_name": owner_name,
        "display_name": display_name,
        "psp_display_name": psp_display_name,
        "person_id": person_id,
        "language": language,
        "process_log_language": process_log_language,
        "visibility": visibility,
        "public_summary": public_summary,
        "public_material_policy": public_material_policy,
        "raw_material_policy": raw_material_policy,
        "github_configure": github_configure,
        "github_owner": github_owner,
        "github_account_type": github_account_type,
        "github_auth_method": github_auth_method,
        "github_permissions": github_permissions,
        "github_require_gh": github_configure and (github_auth_method == "gh-oauth" or create_avatar_repo or create_memory_repo),
        "github_auth_required": github_configure and github_auth_method == "gh-oauth" and (create_avatar_repo or create_memory_repo),
        "github_create_avatar_repo": create_avatar_repo,
        "github_create_memory_repo": create_memory_repo,
        "github_token_policy": "do-not-store; use gh auth or environment variables",
        "memory_repo_name": memory_repo_name,
        "memory_repo_visibility": memory_repo_visibility,
        "memory_repo_path": memory_repo_path,
        "memory_source_policy": memory_source_policy,
        "memory_access_policy": memory_access_policy,
        "memory_public_mirror": memory_public_mirror,
        "memory_collaboration_policy": memory_collaboration_policy,
        "memory_raw_material_policy": memory_raw_material_policy,
        "memory_allowed_public_exports": memory_allowed_public_exports,
        "wiki_authoritative_source": wiki_authoritative_source,
        "wiki_sync_modes": wiki_sync_modes,
        "wiki_rsync_enabled": wiki_rsync_enabled,
        "wiki_rsync_target": wiki_rsync_target,
        "feishu_configure": feishu_configure,
        "feishu_tenant_name": feishu_tenant_name,
        "feishu_app_id": feishu_app_id,
        "feishu_app_type": feishu_app_type,
        "feishu_auth_method": feishu_auth_method,
        "feishu_permissions": feishu_permissions,
        "feishu_source_usage": feishu_source_usage,
        "feishu_token_policy": feishu_token_policy,
        "hermes_configure": hermes_configure,
        "hermes_update_cadence": hermes_update_cadence,
        "hermes_source_usage": hermes_source_usage,
        "hermes_targets": hermes_targets,
        "hermes_token_policy": "env-only-or-platform-secret" if hermes_configure else "not-configured",
        "wenxin_goals": wenxin_goals,
        "recommended_skill_domains": domains,
        "skill_recommendations_source": "identity/wenxin/",
    }

    print("Will write:")
    for key in ("repo_name", "identity_mode", "display_name", "psp_display_name", "person_id", "language", "process_log_language", "visibility", "github_auth_method", "memory_repo_name", "wiki_authoritative_source", "hermes_configure", "feishu_configure", "recommended_skill_domains"):
        print(f"  {key}: {config[key]}")
    if not wizard.ask_bool("Write replicateme.yml", True):
        print("Aborted.")
        return 1

    output = Path(args.output).expanduser().resolve()
    write_flat_yaml(output, config)
    print(f"Wrote {output}")
    print(f"Next: python scripts/apply_avatar_config.py {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
