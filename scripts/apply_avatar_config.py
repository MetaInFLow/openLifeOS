#!/usr/bin/env python3
"""Apply an openLifeOS YAML config: scaffold repo, check tooling, and wire setup files."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from replicateme_yaml import as_bool, as_list, read_flat_yaml, write_flat_yaml


ROOT = Path(__file__).resolve().parents[1]
INIT_SCRIPT = ROOT / "scripts" / "init_avatar_repo.py"


def run(cmd: list[str], cwd: Path | None = None, execute: bool = True) -> int:
    if not execute:
        print("[plan] " + " ".join(cmd))
        return 0
    print("[run] " + " ".join(cmd), flush=True)
    return subprocess.run(cmd, cwd=cwd, check=False).returncode


def process_log_language(config: dict[str, object]) -> str:
    return str(config.get("process_log_language") or config.get("language") or "zh-CN")


def say(config: dict[str, object], zh: str, en: str) -> None:
    print(zh if process_log_language(config) == "zh-CN" else en)


def require(value: object, key: str) -> str:
    text = "" if value is None else str(value).strip()
    if not text:
        raise SystemExit(f"Missing required config key: {key}")
    return text


def ensure_gh(config: dict[str, object], install_tools: bool) -> None:
    if not as_bool(config, "github_require_gh", False):
        return

    if shutil.which("git") is None:
        raise SystemExit("Missing git. Install git before applying this config.")

    if shutil.which("gh") is None:
        if install_tools or as_bool(config, "github_install_gh", False):
            if shutil.which("brew") is None:
                raise SystemExit("gh is missing and Homebrew is unavailable. Install GitHub CLI manually.")
            code = run(["brew", "install", "gh"])
            if code != 0:
                raise SystemExit("brew install gh failed")
        else:
            raise SystemExit("gh is missing. Re-run with --install-tools or install GitHub CLI manually.")

    if as_bool(config, "github_auth_required", False):
        result = subprocess.run(["gh", "auth", "status"], text=True, capture_output=True, check=False)
        if result.returncode != 0:
            raise SystemExit("gh is installed but not authenticated. Run: gh auth login")


def scaffold_repo(config_path: Path, config: dict[str, object], force: bool, refresh_self_evolution_skills: bool) -> Path:
    raw_repo_path = Path(require(config.get("repo_path"), "repo_path")).expanduser()
    repo_path = raw_repo_path if raw_repo_path.is_absolute() else config_path.parent / raw_repo_path
    repo_path = repo_path.resolve()
    owner_name = require(config.get("owner_name"), "owner_name")
    display_name = str(config.get("display_name") or owner_name)
    identity_mode = str(config.get("identity_mode") or "named")
    psp_display_name = str(config.get("psp_display_name") or display_name)
    person_id = require(config.get("person_id"), "person_id")
    github_owner = str(config.get("github_owner") or "MetaInFlow")
    visibility = str(config.get("visibility") or "local-only")
    language = str(config.get("language") or "zh-CN")
    log_language = process_log_language(config)

    cmd = [
        sys.executable,
        str(INIT_SCRIPT),
        str(repo_path),
        "--owner-name",
        owner_name,
        "--display-name",
        display_name,
        "--identity-mode",
        identity_mode,
        "--psp-display-name",
        psp_display_name,
        "--person-id",
        person_id,
        "--github-owner",
        github_owner,
        "--visibility",
        visibility,
        "--language",
        language,
        "--process-log-language",
        log_language,
    ]
    if force:
        cmd.append("--force")
    if refresh_self_evolution_skills or as_bool(config, "refresh_self_evolution_skills", False):
        cmd.append("--refresh-self-evolution-skill-install")
    code = run(cmd)
    if code != 0:
        raise SystemExit(code)

    target_config = dict(config)
    target_config["repo_path"] = str(repo_path)
    write_flat_yaml(repo_path / "replicateme.yml", target_config)
    say(config, f"已写入 {repo_path / 'replicateme.yml'}", f"Wrote {repo_path / 'replicateme.yml'}")
    return repo_path


def yaml_quote(value: object) -> str:
    text = "" if value is None else str(value)
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def default_public_summary(config: dict[str, object]) -> str:
    display_name = str(config.get("display_name") or config.get("owner_name") or "This LifeOS")
    language = str(config.get("language") or "zh-CN")
    if language == "zh-CN":
        return f"{display_name} 的 openLifeOS 已完成初始化；个人定位、履历、技能、审美、经历和长期记忆等待 owner-approved evidence 后再生成。"
    return f"{display_name}'s openLifeOS has been initialized; positioning, biography, skills, aesthetics, experiences, and long-term memory require owner-approved evidence before generation."


def write_public_profile(repo_path: Path, config: dict[str, object]) -> None:
    identity_mode = str(config.get("identity_mode") or "named")
    psp_display_name = str(config.get("psp_display_name") or config.get("display_name") or config.get("owner_name") or "")
    public_summary = str(config.get("public_summary") or "").strip()
    if not public_summary or public_summary.startswith("TODO"):
        public_summary = default_public_summary(config)
    text = "\n".join(
        [
            f"identity_mode: {yaml_quote(identity_mode)}",
            f"owner_name: {yaml_quote(config.get('owner_name') or '')}",
            f"display_name: {yaml_quote(config.get('display_name') or config.get('owner_name') or '')}",
            f"psp_display_name: {yaml_quote(psp_display_name)}",
            f"person_id: {yaml_quote(config.get('person_id') or '')}",
            f"language: {yaml_quote(config.get('language') or 'zh-CN')}",
            f"process_log_language: {yaml_quote(process_log_language(config))}",
            f"visibility: {yaml_quote(config.get('visibility') or 'local-only')}",
            f"public_summary: {yaml_quote(public_summary)}",
            "public_roles: []",
            "public_links:",
            "  website: \"\"",
            "  github: \"\"",
            "  linkedin: \"\"",
            "  x: \"\"",
            "contact_policy: \"TODO: describe public contact preference or leave blank.\"",
            "do_not_claim: []",
            "source_notes:",
            "  - \"Only add facts that are public or explicitly approved by the owner.\"",
            "  - \"For anonymous identities, use psp_display_name as the PSP name and do not infer a real-world identity.\"",
            "",
        ]
    )
    path = repo_path / "identity" / "public-profile" / "profile.yml"
    path.write_text(text, encoding="utf-8")
    say(config, f"已写入 {path}", f"Wrote {path}")


def write_memory_config(repo_path: Path, config: dict[str, object]) -> None:
    github_owner = str(config.get("github_owner") or "")
    memory_repo_name = str(config.get("memory_repo_name") or "")
    memory_repo_visibility = str(config.get("memory_repo_visibility") or "private")
    memory_repo_path = str(config.get("memory_repo_path") or "identity/memories/wiki")
    create_memory_repo = as_bool(config, "github_create_memory_repo", False)
    authoritative_source = str(config.get("wiki_authoritative_source") or "github")
    sync_modes = as_list(config, "wiki_sync_modes") or ["github"]
    memory_access_policy = str(config.get("memory_access_policy") or "private-by-default")
    public_mirror = str(config.get("memory_public_mirror") or "index-only")
    allowed_public_exports = as_list(config, "memory_allowed_public_exports") or [
        "approved-facts",
        "redacted-summaries",
        "abstracted-patterns",
    ]
    private_collaboration = str(config.get("memory_collaboration_policy") or "private-pr-or-owner-approved-extract")
    memory_raw_material_policy = str(config.get("memory_raw_material_policy") or "never-copy-raw-private-bodies")
    rsync_enabled = as_bool(config, "wiki_rsync_enabled", False)
    rsync_target = str(config.get("wiki_rsync_target") or "")
    language = str(config.get("language") or "zh-CN")
    rule = (
        "链接或摘要长期 wiki；public 层只保留 index/approved-derived 内容，不复制私密正文。如果 authoritative_source 是 server-rsync，则服务器是唯一真源，GitHub 只作为协同或公开镜像。"
        if language == "zh-CN"
        else "Link or summarize the wiki; the public layer keeps only index/approved-derived content and never copies private bodies. If authoritative_source is server-rsync, the server is the single source of truth and GitHub is only a collaboration or publishing mirror."
    )

    text = "\n".join(
        [
            f"github_owner: {github_owner}",
            f"repository: {memory_repo_name}",
            f"visibility: {memory_repo_visibility}",
            f"local_path: {memory_repo_path}",
            f"create_with_gh: {'true' if create_memory_repo else 'false'}",
            f"authoritative_source: {authoritative_source}",
            f"sync_modes: {', '.join(sync_modes)}",
            f"source_policy: {memory_access_policy}",
            f"public_mirror: {public_mirror}",
            f"allowed_public_exports: {', '.join(allowed_public_exports)}",
            f"private_collaboration: {private_collaboration}",
            f"raw_material_policy: {memory_raw_material_policy}",
            f"rsync_enabled: {'true' if rsync_enabled else 'false'}",
            f"rsync_target: {rsync_target}",
            "status: configured",
            f"rule: {rule}",
            "",
        ]
    )
    path = repo_path / "identity" / "memories" / "wiki-repo.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    say(config, f"已写入 {path}", f"Wrote {path}")


def write_integration_configs(repo_path: Path, config: dict[str, object]) -> None:
    integrations = repo_path / "integrations"
    integrations.mkdir(parents=True, exist_ok=True)

    github_text = "\n".join(
        [
            f"enabled: {'true' if as_bool(config, 'github_configure', False) else 'false'}",
            f"owner: {config.get('github_owner') or ''}",
            f"account_type: {config.get('github_account_type') or 'unknown'}",
            f"auth_method: {config.get('github_auth_method') or 'skip'}",
            f"permissions: {', '.join(as_list(config, 'github_permissions'))}",
            f"token_policy: {config.get('github_token_policy') or 'do-not-store'}",
            f"create_avatar_repo: {'true' if as_bool(config, 'github_create_avatar_repo', False) else 'false'}",
            f"create_memory_repo: {'true' if as_bool(config, 'github_create_memory_repo', False) else 'false'}",
            "status: configured",
            "",
        ]
    )
    github_path = integrations / "github.yml"
    github_path.write_text(github_text, encoding="utf-8")
    say(config, f"已写入 {github_path}", f"Wrote {github_path}")

    feishu_enabled = as_bool(config, "feishu_configure", False)
    feishu_text = "\n".join(
        [
            f"enabled: {'true' if feishu_enabled else 'false'}",
            f"tenant_name: {config.get('feishu_tenant_name') or ''}",
            f"app_id: {config.get('feishu_app_id') or ''}",
            f"app_type: {config.get('feishu_app_type') or 'none'}",
            f"auth_method: {config.get('feishu_auth_method') or 'skip'}",
            f"permissions: {', '.join(as_list(config, 'feishu_permissions'))}",
            f"source_usage: {', '.join(as_list(config, 'feishu_source_usage'))}",
            f"token_policy: {config.get('feishu_token_policy') or 'not-configured'}",
            f"raw_material_policy: {config.get('raw_material_policy') or 'never-commit'}",
            f"status: {'configured' if feishu_enabled else 'disabled'}",
            "",
        ]
    )
    feishu_path = integrations / "feishu.yml"
    feishu_path.write_text(feishu_text, encoding="utf-8")
    say(config, f"已写入 {feishu_path}", f"Wrote {feishu_path}")

    hermes_enabled = as_bool(config, "hermes_configure", False)
    language = str(config.get("language") or "zh-CN")
    hermes_rule = (
        "Hermes 只处理授权材料和安全摘要；不要把 token、私密正文或未脱敏原始材料写入 repo。"
        if language == "zh-CN"
        else "Hermes only processes approved materials and safe summaries; do not write tokens, private bodies, or unredacted raw material into the repo."
    )
    hermes_text = "\n".join(
        [
            f"enabled: {'true' if hermes_enabled else 'false'}",
            f"update_cadence: {config.get('hermes_update_cadence') or 'manual'}",
            f"source_usage: {', '.join(as_list(config, 'hermes_source_usage'))}",
            f"targets: {', '.join(as_list(config, 'hermes_targets'))}",
            "github_collaboration: pull-request-or-commit",
            f"token_policy: {config.get('hermes_token_policy') or 'not-configured'}",
            f"status: {'configured' if hermes_enabled else 'disabled'}",
            f"rule: {hermes_rule}",
            "",
        ]
    )
    hermes_path = integrations / "hermes.yml"
    hermes_path.write_text(hermes_text, encoding="utf-8")
    say(config, f"已写入 {hermes_path}", f"Wrote {hermes_path}")


def write_permissions_summary(repo_path: Path, config: dict[str, object]) -> None:
    language = str(config.get("language") or "zh-CN")
    rule = (
        "不提交 token、app_secret、cookie、refresh token、私钥或原始私密资料。"
        if language == "zh-CN"
        else "Do not commit tokens, app secrets, cookies, refresh tokens, private keys, or raw private material."
    )
    allowed_public_exports = as_list(config, "memory_allowed_public_exports") or [
        "approved-facts",
        "redacted-summaries",
        "abstracted-patterns",
    ]
    text = "\n".join(
        [
            f"public_material_policy: {config.get('public_material_policy') or 'private-by-default'}",
            f"raw_material_policy: {config.get('raw_material_policy') or 'never-commit'}",
            "secret_storage: environment-or-password-manager-only",
            "memory:",
            f"  source_policy: {config.get('memory_access_policy') or 'private-by-default'}",
            f"  public_mirror: {config.get('memory_public_mirror') or 'index-only'}",
            f"  collaboration_policy: {config.get('memory_collaboration_policy') or 'private-pr-or-owner-approved-extract'}",
            f"  allowed_public_exports: {', '.join(allowed_public_exports)}",
            f"  raw_material_policy: {config.get('memory_raw_material_policy') or 'never-copy-raw-private-bodies'}",
            "github:",
            "  config: integrations/github.yml",
            f"  permissions: {', '.join(as_list(config, 'github_permissions'))}",
            f"  token_policy: {config.get('github_token_policy') or 'do-not-store'}",
            "feishu:",
            "  config: integrations/feishu.yml",
            f"  permissions: {', '.join(as_list(config, 'feishu_permissions'))}",
            f"  token_policy: {config.get('feishu_token_policy') or 'not-configured'}",
            "hermes:",
            "  config: integrations/hermes.yml",
            f"  source_usage: {', '.join(as_list(config, 'hermes_source_usage'))}",
            f"  targets: {', '.join(as_list(config, 'hermes_targets'))}",
            f"  token_policy: {config.get('hermes_token_policy') or 'not-configured'}",
            f"rule: {rule}",
            "",
        ]
    )
    path = repo_path / "security" / "permissions.yml"
    path.write_text(text, encoding="utf-8")
    say(config, f"已写入 {path}", f"Wrote {path}")


def skill_recommendation(domain: str, source: str, language: str) -> dict[str, str]:
    normalized = domain.strip().lower().replace(" ", "-")
    if language == "zh-CN":
        defaults = {
            "engineering": ("engineer-skill", "蒸馏工程判断、架构习惯、review 规则、debug 方法和交付 playbook。"),
            "professional-core": ("professional-core-skill", "把这个人的核心职业操作系统蒸馏成可复用工作流。"),
            "communication": ("communication-skill", "蒸馏对外表达、写作、会议和 stakeholder 沟通模式。"),
            "decision-making": ("decision-making-skill", "蒸馏决策原则、取舍模式和风险门禁。"),
            "founder": ("founder-skill", "蒸馏创始人/公司构建能力、融资叙事、GTM 判断和运营节奏。"),
            "sales": ("sales-skill", "蒸馏销售发现、客户筛选、方案、跟进和异议处理模式。"),
            "product": ("product-skill", "蒸馏产品策略、需求塑形、路线图和验证判断。"),
        }
        fallback = f"把这个人的 {domain} 能力蒸馏成可复用 Skill。"
    else:
        defaults = {
            "engineering": ("engineer-skill", "Distill engineering judgment, architecture habits, review rules, and delivery playbooks."),
            "professional-core": ("professional-core-skill", "Distill the subject's core professional operating system into reusable workflows."),
            "communication": ("communication-skill", "Distill external communication, writing, meeting, and stakeholder patterns."),
            "decision-making": ("decision-making-skill", "Distill decision principles, tradeoff patterns, and risk gates."),
            "founder": ("founder-skill", "Distill founder/company-building skills, fundraising narrative, GTM judgment, and operating cadence."),
            "sales": ("sales-skill", "Distill sales discovery, qualification, proposal, follow-up, and objection-handling patterns."),
            "product": ("product-skill", "Distill product strategy, requirement shaping, roadmap, and validation judgment."),
        }
        fallback = f"Distill the subject's {domain} ability into a reusable Skill."
    skill_id, why = defaults.get(
        normalized,
        (f"{normalized}-skill", fallback),
    )
    return {
        "machine_name": skill_id,
        "alias": "null",
        "user_named": "false",
        "skill_type": "distilled-meta-skill",
        "domain": domain,
        "source": source,
        "eligibility_type": "repeated_workflow",
        "evidence_strength": "missing",
        "implemented": "false",
        "summarized": "false",
        "summary_artifact": "null",
        "implementation_artifact": "null",
        "usage_scenario": why,
        "promotion_gate": "IPO Reverse + owner alignment",
        "evidence_needed": "2-5 key projects; judgment principles and tradeoffs; reusable workflow, inputs, outputs, and acceptance criteria",
    }


def write_skill_recommendations(repo_path: Path, config: dict[str, object]) -> None:
    source = str(config.get("skill_recommendations_source") or "identity/wenxin/")
    domains = as_list(config, "recommended_skill_domains") or ["professional-core", "communication", "decision-making"]
    language = str(config.get("language") or "zh-CN")
    recommendations = [skill_recommendation(domain, source, language) for domain in domains]
    rule = (
        "推荐 Skill 必须满足两类 evidence gate 之一：highly possible 全球前 5% / 高分位能力，或高频重复行为且可抽象出稳定输入、流程、输出和验收标准。系统工具、自我进化工具、泛泛领域兴趣和一次性项目不得直接算推荐 Skill。"
        if language == "zh-CN"
        else "A recommended Skill must satisfy one of two evidence gates: highly possible top-5-percent/high-percentile capability, or repeated work with extractable stable inputs, process, outputs, and acceptance criteria. System tools, self-evolution tools, generic interests, and one-off projects must not become recommended Skills by default."
    )
    lines = [
        "schema: openlifeos.wenxin-skill-recommendations.v1",
        f"language: {language}",
        f"generated_from: {source}",
        "status: intake-ready",
        f"rule: {rule}",
        "eligibility_gate:",
        "  allowed_types:",
        "    - top_5_percent_capability_hypothesis",
        "    - repeated_workflow",
        "  disallow:",
        "    - self_evolution_tool_installed",
        "    - generic_domain_interest",
        "    - one_off_project_without_reusable_workflow",
        "    - unsupported_capability_guess",
        "recommendations:",
    ]
    for item in recommendations:
        lines.extend(
            [
                f"  - machine_name: {item['machine_name']}",
                f"    alias: {item['alias']}",
                f"    user_named: {item['user_named']}",
                f"    skill_type: {item['skill_type']}",
                f"    eligibility_type: {item['eligibility_type']}",
                f"    evidence_strength: {item['evidence_strength']}",
                f"    implemented: {item['implemented']}",
                f"    summarized: {item['summarized']}",
                f"    summary_artifact: {item['summary_artifact']}",
                f"    implementation_artifact: {item['implementation_artifact']}",
                "    usage_scenarios:",
                f"      - {item['usage_scenario']}",
                "    evidence_sources: []",
                "    evidence_needed:",
                f"      - {item['evidence_needed']}",
                f"    promotion_gate: {item['promotion_gate']}",
            ]
        )
    lines.append("watchlist: []")
    path = repo_path / "identity" / "wenxin" / "skill-recommendations.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    say(config, f"已写入 {path}", f"Wrote {path}")


def create_remote_repos(repo_path: Path, config: dict[str, object], execute: bool) -> None:
    owner = str(config.get("github_owner") or "")
    repo_name = str(config.get("repo_name") or repo_path.name)
    visibility = str(config.get("visibility") or "local-only")
    if as_bool(config, "github_create_avatar_repo", False) and visibility in {"private", "public"}:
        privacy_flag = "--public" if visibility == "public" else "--private"
        run(["gh", "repo", "create", f"{owner}/{repo_name}", privacy_flag, "--source", str(repo_path), "--remote", "origin"], execute=execute)

    if as_bool(config, "github_create_memory_repo", False):
        memory_repo = str(config.get("memory_repo_name") or f"{repo_name}.wiki")
        memory_visibility = str(config.get("memory_repo_visibility") or "private")
        privacy_flag = "--public" if memory_visibility == "public" else "--private"
        run(["gh", "repo", "create", f"{owner}/{memory_repo}", privacy_flag, "--clone=false"], execute=execute)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", help="Path to replicateme.yml")
    parser.add_argument("--force", action="store_true", help="Overwrite generated avatar files")
    parser.add_argument("--refresh-self-evolution-skills", action="store_true", help="Refresh existing vendored self-evolution skills from latest GitHub release/archive")
    parser.add_argument("--install-tools", action="store_true", help="Install missing gh via Homebrew when possible")
    parser.add_argument("--create-remotes", action="store_true", help="Actually create configured GitHub repos with gh")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).expanduser().resolve()
    config = read_flat_yaml(config_path)
    if not config:
        raise SystemExit(f"Empty or missing config: {config_path}")

    ensure_gh(config, args.install_tools)
    say(config, "当前阶段：Kernel Scaffold / 根据配置生成确定性 LifeOS 骨架。", "Stage: Kernel Scaffold - generating deterministic LifeOS structure from config.")
    repo_path = scaffold_repo(config_path, config, args.force, args.refresh_self_evolution_skills)
    say(config, "当前阶段：Boundary Wiring / 写入 profile、memory、integration 和 permission 边界。", "Stage: Boundary Wiring - writing profile, memory, integration, and permission boundaries.")
    write_public_profile(repo_path, config)
    write_memory_config(repo_path, config)
    write_integration_configs(repo_path, config)
    write_permissions_summary(repo_path, config)
    write_skill_recommendations(repo_path, config)
    create_remote_repos(repo_path, config, args.create_remotes)

    if process_log_language(config) == "zh-CN":
        print("下一步：")
        print(f"- python {ROOT / 'scripts' / 'doctor_avatar_repo.py'} {repo_path}")
        print("- 当前阶段将进入 Evidence Intake：先向 owner 说明材料用途，再确认哪些 evidence 被授权用于问心、PSP 或 Skill 结论。")
    else:
        print("Next:")
        print(f"- python {ROOT / 'scripts' / 'doctor_avatar_repo.py'} {repo_path}")
        print("- Stage: Evidence Intake - ask the owner which evidence is approved before generating Wenxin, PSP, or Skill conclusions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
