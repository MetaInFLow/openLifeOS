#!/usr/bin/env python3
"""Create an openLifeOS repo from bundled templates."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request
import json
from pathlib import Path

from migrate_lifeos_schema import ensure_v3_artifact_sections, ensure_v3_skeleton


ROOT = Path(__file__).resolve().parents[1]
INTAKE_SCRIPT = ROOT / "scripts" / "start_avatar_intake.py"
TEMPLATE_DIRS = {
    "zh-CN": ROOT / "assets" / "avatar-skill-template",
    "en-US": ROOT / "assets" / "avatar-skill-template-en",
}

SELF_EVOLUTION_SKILL_REPOS = {
    "wenxin": {
        "skill_id": "inneratlas",
        "repo": "MetaInFLow/innerAtlas-skill",
        "path": "evolution/organ-systems/wenxin",
    },
    "psp": {
        "repo": "MetaInFLow/psp-skill",
        "path": "evolution/organ-systems/psp",
    },
    "ipo-reverse": {
        "repo": "MetaInFLow/ipo-reverse-skill",
        "path": "evolution/organ-systems/ipo-reverse",
    },
    "taste-generator": {
        "repo": "MetaInFLow/taste-generator-skill",
        "path": "evolution/organ-systems/taste-generator",
    },
}


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "avatar"


def render_text(text: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def render_path(path: Path, values: dict[str, str]) -> Path:
    rendered = str(path)
    for key, value in values.items():
        rendered = rendered.replace("__" + key + "__", value)
    if rendered.endswith(".tmpl"):
        rendered = rendered[:-5]
    return Path(rendered)


def copy_template(template_dir: Path, target: Path, values: dict[str, str], force: bool) -> list[Path]:
    created: list[Path] = []
    for source in sorted(template_dir.rglob("*")):
        if source.is_dir():
            continue
        if "__pycache__" in source.parts or source.suffix in {".pyc", ".pyo"}:
            continue

        rel = source.relative_to(template_dir)
        dest = target / render_path(rel, values)
        if dest.exists() and not force:
            raise SystemExit(f"Refusing to overwrite existing file: {dest}")

        dest.parent.mkdir(parents=True, exist_ok=True)
        text = source.read_text(encoding="utf-8")
        dest.write_text(render_text(text, values), encoding="utf-8")
        created.append(dest)
    return created


def github_json(url: str) -> dict[str, object] | None:
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "openLifeOS"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None


def github_archive_url(repo: str) -> tuple[str, str, str]:
    latest = github_json(f"https://api.github.com/repos/{repo}/releases/latest")
    if latest and isinstance(latest.get("tarball_url"), str):
        tag = str(latest.get("tag_name") or "latest")
        return str(latest["tarball_url"]), "release", tag

    repo_meta = github_json(f"https://api.github.com/repos/{repo}")
    branch = "main"
    if repo_meta and isinstance(repo_meta.get("default_branch"), str):
        branch = str(repo_meta["default_branch"])
    return f"https://api.github.com/repos/{repo}/tarball/{branch}", "branch", branch


def download_github_archive(repo: str, archive: Path) -> tuple[str, str]:
    if shutil.which("gh"):
        release = subprocess.run(
            ["gh", "release", "view", "-R", repo, "--json", "tagName", "--jq", ".tagName"],
            text=True,
            capture_output=True,
            check=False,
        )
        tag = release.stdout.strip()
        if release.returncode == 0 and tag:
            result = subprocess.run(
                ["gh", "release", "download", tag, "-R", repo, "--archive=tar.gz", "--output", str(archive)],
                text=True,
                capture_output=True,
                check=False,
            )
            if result.returncode == 0:
                return "release", tag

        branch = subprocess.run(
            ["gh", "repo", "view", repo, "--json", "defaultBranchRef", "--jq", ".defaultBranchRef.name"],
            text=True,
            capture_output=True,
            check=False,
        )
        branch_name = branch.stdout.strip() if branch.returncode == 0 else "main"
        result = subprocess.run(
            ["gh", "api", f"repos/{repo}/tarball/{branch_name}", "--output", str(archive)],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode == 0:
            return "branch", branch_name

    archive_url, source_type, source_ref = github_archive_url(repo)
    urllib.request.urlretrieve(archive_url, archive)
    return source_type, source_ref


def copy_archive_payload(archive: Path, dest: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="openlifeos-skill-extract-") as tmp:
        extract_root = Path(tmp)
        with tarfile.open(archive, "r:gz") as tar:
            try:
                tar.extractall(extract_root, filter="data")
            except TypeError:
                tar.extractall(extract_root)
        roots = [path for path in extract_root.iterdir() if path.is_dir()]
        if len(roots) != 1:
            raise RuntimeError("Unexpected GitHub archive layout")
        source_root = roots[0]
        if dest.exists():
            shutil.rmtree(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source_root, dest, ignore=shutil.ignore_patterns(".git", ".github"))


def install_self_evolution_skills(target: Path, skip: bool = False, refresh: bool = False) -> list[str]:
    """Install complete self-evolution skills from GitHub release archives.

    The LifeOS instance vendors a normal directory copy under evolution/organ-systems.
    It deliberately does not use git submodules, so runtime profiles and users see
    one ordinary skill tree with a source manifest.
    """
    installed: list[str] = []
    if skip:
        return installed

    for skill_id, spec in SELF_EVOLUTION_SKILL_REPOS.items():
        rel = spec["path"]
        repo = spec["repo"]
        manifest_skill_id = spec.get("skill_id", skill_id)
        dest = target / rel
        if not refresh and (dest / "SKILL.md").exists() and (dest / ".openlifeos-skill-source.yml").exists():
            installed.append(rel)
            continue

        with tempfile.TemporaryDirectory(prefix=f"openlifeos-{skill_id}-") as tmp:
            backup = Path(tmp) / "backup"
            had_existing = dest.exists()
            if had_existing:
                shutil.move(str(dest), str(backup))
            try:
                archive = Path(tmp) / f"{skill_id}.tar.gz"
                source_type, source_ref = download_github_archive(repo, archive)
                copy_archive_payload(archive, dest)
                manifest = "\n".join(
                    [
                        "schema: openlifeos.skill-source.v1",
                        f"skill_id: {manifest_skill_id}",
                        f"github_repo: {repo}",
                        f"source_type: {source_type}",
                        f"source_ref: {source_ref}",
                        f"installed_at: {dt.datetime.now().astimezone().replace(microsecond=0).isoformat()}",
                        "install_mode: github-archive-vendor",
                        "submodule: false",
                        "",
                    ]
                )
                (dest / ".openlifeos-skill-source.yml").write_text(manifest, encoding="utf-8")
            except Exception as exc:
                if dest.exists():
                    shutil.rmtree(dest)
                if had_existing:
                    shutil.move(str(backup), str(dest))
                print(f"Warning: could not install {skill_id} skill from {repo}: {exc}")
                continue
            installed.append(rel)
    return installed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", help="Target repo directory to create")
    parser.add_argument("--owner-name", required=True, help="Person, team, or organization represented by the avatar")
    parser.add_argument("--display-name", help="Human-facing display name; defaults to owner name")
    parser.add_argument(
        "--identity-mode",
        default="named",
        choices=["named", "anonymous"],
        help="Whether the LifeOS uses a named identity or an anonymous/pseudonymous identity",
    )
    parser.add_argument("--psp-display-name", help="Name used in PSP/person-model files; useful as a pseudonym for anonymous identities")
    parser.add_argument("--person-id", help="Stable slug for identity/psp/<person-id>")
    parser.add_argument("--github-owner", default="MetaInFlow", help="GitHub user or org for future remote URL")
    parser.add_argument("--visibility", default="local-only", choices=["local-only", "private", "public"])
    parser.add_argument(
        "--language",
        default="zh-CN",
        choices=sorted(TEMPLATE_DIRS),
        help="Template language for generated Skill files; defaults to Chinese",
    )
    parser.add_argument(
        "--process-log-language",
        choices=sorted(TEMPLATE_DIRS),
        help="Language for process logs; defaults to --language",
    )
    parser.add_argument(
        "--skip-self-evolution-skill-install",
        action="store_true",
        help="Skip best-effort GitHub release/archive install for complete self-evolution skills",
    )
    parser.add_argument(
        "--refresh-self-evolution-skill-install",
        action="store_true",
        help="Refresh existing vendored self-evolution skills from latest GitHub release/archive instead of keeping the manifest-pinned copy",
    )
    parser.add_argument(
        "--lifecycle",
        default="delivery",
        choices=["development", "delivery"],
        help="LifeOS lifecycle mode. development allows submodule/working-source meta skills; delivery uses release/archive snapshots.",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    target = Path(args.target).expanduser().resolve()
    repo_name = target.name
    created_at = dt.datetime.now().astimezone().replace(microsecond=0)
    lifeos_age_label = "0 天" if args.language == "zh-CN" else "0 days"
    process_log_language = args.process_log_language or args.language
    display_name = args.display_name or args.owner_name
    psp_display_name = args.psp_display_name or display_name
    person_id = args.person_id or slugify(psp_display_name)
    skill_id = slugify(repo_name.removesuffix(".Skill").removesuffix(".skill"))
    memory_repo_name = f"{repo_name.removesuffix('.Skill').removesuffix('.skill')}.wiki"
    upload_version = f"{slugify(repo_name)}-upload-{created_at.strftime('%Y%m%d-%H%M%S')}"
    delivery_version = f"{slugify(repo_name)}-delivery-{created_at.strftime('%Y%m%d-%H%M%S')}"
    current_lifeos_version = upload_version if args.lifecycle == "development" else delivery_version
    if args.language == "zh-CN":
        initial_public_summary = (
            f"{display_name} 的 openLifeOS 已完成 local-only 初始化；个人定位、履历、技能、审美、经历和长期记忆等待 owner-approved evidence 后再生成。"
        )
    else:
        initial_public_summary = (
            f"{display_name}'s openLifeOS has been initialized; positioning, biography, skills, aesthetics, experiences, and long-term memory require owner-approved evidence before generation."
        )

    values = {
        "TODAY": dt.date.today().isoformat(),
        "CREATED_AT": created_at.isoformat(),
        "LIFEOS_AGE_LABEL": lifeos_age_label,
        "ARTIFACT_TIMESTAMP": created_at.strftime("%Y%m%d-%H%M%S"),
        "REPO_NAME": repo_name,
        "SKILL_ID": skill_id,
        "DISPLAY_NAME": display_name,
        "PSP_DISPLAY_NAME": psp_display_name,
        "OWNER_NAME": args.owner_name,
        "IDENTITY_MODE": args.identity_mode,
        "INITIAL_PUBLIC_SUMMARY": initial_public_summary,
        "PERSON_ID": person_id,
        "GITHUB_OWNER": args.github_owner,
        "VISIBILITY": args.visibility,
        "LANGUAGE": args.language,
        "PROCESS_LOG_LANGUAGE": process_log_language,
        "LIFEOS_LIFECYCLE": args.lifecycle,
        "UPLOAD_VERSION": upload_version,
        "DELIVERY_VERSION": delivery_version,
        "CURRENT_LIFEOS_VERSION": current_lifeos_version,
        "MEMORY_REPO_NAME": memory_repo_name,
        "MEMORY_REPO_PATH": f"identity/memories/{person_id}-wiki",
        "RECOMMENDED_SKILL_DOMAINS": "professional-core, communication, decision-making",
        "DEFAULT_SKILLS_REPO": "MetaInFlow/openLifeOS",
        "DEFAULT_SKILLS_REF": "latest",
        "WENXIN_SKILL_REPO": "MetaInFLow/innerAtlas-skill",
        "PSP_SKILL_REPO": "MetaInFLow/psp-skill",
        "IPO_REVERSE_SKILL_REPO": "MetaInFLow/ipo-reverse-skill",
        "TASTE_GENERATOR_SKILL_REPO": "MetaInFLow/taste-generator-skill",
    }

    template_dir = TEMPLATE_DIRS[args.language]
    if not template_dir.exists():
        raise SystemExit(f"Missing template directory: {template_dir}")

    target.mkdir(parents=True, exist_ok=True)
    created = copy_template(template_dir, target, values, args.force)
    v3_created = ensure_v3_skeleton(target)
    if ensure_v3_artifact_sections(target):
        v3_created.append("artifacts/current.yml")
    created.extend(target / rel for rel in v3_created)

    git_dir = target / ".git"
    if not git_dir.exists() and shutil.which("git"):
        subprocess.run(["git", "init"], cwd=target, check=True)

    installed_skills = install_self_evolution_skills(
        target,
        skip=args.skip_self_evolution_skill_install,
        refresh=args.refresh_self_evolution_skill_install,
    )

    if process_log_language == "zh-CN":
        print(f"已创建 {repo_name}: {target}")
        print("当前阶段：Kernel Scaffold / 内核骨架生成")
        print(f"身份模式：{args.identity_mode}")
        print(f"PSP 显示名：{psp_display_name}")
        print(f"内容语言：{args.language}")
        print(f"过程日志语言：{process_log_language}")
        print(f"LifeOS 状态：{args.lifecycle}（见 LIFEOS_STATUS.yml）")
        print(f"已渲染文件数：{len(created)}")
        if installed_skills:
            print("已安装完整 self-evolution skills：" + ", ".join(installed_skills))
        print("下一阶段：Evidence Intake / 证据摄入。启动提示如下：")
        sys.stdout.flush()
        if INTAKE_SCRIPT.exists():
            subprocess.run([sys.executable, str(INTAKE_SCRIPT), str(target), "--language", process_log_language], check=False)
        else:
            print(f"运行：python scripts/start_avatar_intake.py {target}")
    else:
        print(f"Created {repo_name} at {target}")
        print("Stage: Kernel Scaffold")
        print(f"Identity mode: {args.identity_mode}")
        print(f"PSP display name: {psp_display_name}")
        print(f"Content language: {args.language}")
        print(f"Process log language: {process_log_language}")
        print(f"LifeOS lifecycle: {args.lifecycle} (see LIFEOS_STATUS.yml)")
        print(f"Rendered {len(created)} files")
        if installed_skills:
            print("Installed complete self-evolution skills: " + ", ".join(installed_skills))
        print("Next stage: Evidence Intake. Kickoff prompt:")
        sys.stdout.flush()
        if INTAKE_SCRIPT.exists():
            subprocess.run([sys.executable, str(INTAKE_SCRIPT), str(target), "--language", process_log_language], check=False)
        else:
            print(f"Run: python scripts/start_avatar_intake.py {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
