#!/usr/bin/env python3
"""Start the Evidence Intake handoff for a generated openLifeOS avatar.

This is intentionally a kickoff, not synthesis. It explains the next stage,
detects available source-discovery CLIs through the vendored InnerAtlas skill,
and prints the first user-facing questions an agent should ask before reading
any material.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from replicateme_yaml import read_flat_yaml


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", help="Generated openLifeOS avatar repo")
    parser.add_argument(
        "--language",
        choices=["zh-CN", "en-US"],
        help="Output language. Defaults to the repo's configured language.",
    )
    parser.add_argument(
        "--skip-source-scan",
        action="store_true",
        help="Do not run the InnerAtlas local CLI source discovery scan.",
    )
    return parser.parse_args()


def repo_language(root: Path, explicit: str | None) -> str:
    if explicit:
        return explicit
    config = read_flat_yaml(root / "replicateme.yml")
    return str(config.get("language") or "zh-CN")


def repo_value(root: Path, key: str, default: str) -> str:
    config = read_flat_yaml(root / "replicateme.yml")
    return str(config.get(key) or default)


def run_source_scan(root: Path) -> list[dict[str, str]]:
    scanner = root / "evolution" / "organ-systems" / "wenxin" / "scripts" / "inneratlas_source_scan.py"
    if not scanner.exists():
        return []
    result = subprocess.run(
        [sys.executable, str(scanner), "--json"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    candidates = payload.get("candidates", [])
    if not isinstance(candidates, list):
        return []
    return [candidate for candidate in candidates if isinstance(candidate, dict)]


def format_candidates(candidates: list[dict[str, str]], language: str) -> str:
    if not candidates:
        return "- 未扫描到可用资料入口 CLI；先使用用户直接提供的材料。" if language == "zh-CN" else "- No source-discovery CLI detected; use directly provided material first."

    lines = []
    for candidate in candidates:
        name = candidate.get("name", "unknown")
        status = candidate.get("status", "unknown")
        source_type = candidate.get("source_type", "unknown")
        suggested_use = candidate.get("suggested_use", "")
        lines.append(f"- `{name}` [{status}] {source_type}: {suggested_use}")
    return "\n".join(lines)


def zh(root: Path, candidates: list[dict[str, str]]) -> str:
    display_name = repo_value(root, "display_name", root.name)
    person_id = repo_value(root, "person_id", "unknown")
    return f"""当前阶段：Evidence Intake / 证据摄入启动。

我们现在在做什么：
- `Kernel Scaffold` 已完成；现在要开始让 InnerAtlas（问心）和 PSP 有真实材料可用。
- 这一步不会读取私有资料正文，也不会自动扫描你的本地目录、GitHub、Lark/Feishu 或其他账号内容。
- 新建 avatar 的默认取材边界：不要读取本地 openLifeOS factory 的 `output/meta/`、其他 avatar repo、历史 `identity/wenxin/` / `identity/inneratlas/` 报告或旧问心结论。只能使用用户本轮直接提供的材料，或用户明确授权的外部资料入口和范围。
- 先确认模式、授权来源和取材范围，再进入 InnerAtlas；PSP 会在 InnerAtlas 初步身份层和经历证据之后继续。

这阶段会写入或更新：
- `metabolism/inbox/`：授权材料入口或摘要。
- `identity/inneratlas/current/INNERATLAS_REPORT.xml`：InnerAtlas/Wenxin 自我发现源产物。
- `identity/wenxin/`：ledger、公开派生摘要和 Skill recommendations。
- `identity/psp/{person_id}/current/PSP_REPORT.xml` 与 `current/EVIDENCE_MATURITY.xml`：PSP/person model 和证据成熟度源产物。
- `docs/evidence-sufficiency.md`：资料充分性和缺口。

本地资料入口 CLI 发现结果：
{format_candidates(candidates, "zh-CN")}

第一个问题：
你要用哪种 InnerAtlas 模式启动 `{display_name}`？

A. 快速模式
基于你已经提供或明确授权的材料直接推理，猜测部分必须写依据；doctor 不到 100% 时只补问缺失项。

B. 完整模式
先推理，再围绕矛盾点、异常点、重点产出点和确认点继续交互；doctor 到 100% 才算完成。

同时请明确授权范围：允许使用哪些资料入口？例如 `gh` 的哪些 repo、`rg/mdfind` 的哪些目录、Lark/Feishu 的哪些文档；未授权的来源一律不用。如果授权本地目录，默认排除本 openLifeOS 仓库的 `output/meta/` 和所有历史问心/InnerAtlas 报告，除非你明确指定某一份历史产物作为本轮材料。
"""


def en(root: Path, candidates: list[dict[str, str]]) -> str:
    display_name = repo_value(root, "display_name", root.name)
    person_id = repo_value(root, "person_id", "unknown")
    return f"""Current stage: Evidence Intake kickoff.

What we are doing now:
- Kernel Scaffold is complete; InnerAtlas and PSP now need owner-approved evidence.
- This step does not read private bodies, scan local folders, enumerate GitHub/Lark/Feishu, or access account-bound data automatically.
- Default boundary for a new avatar: do not read this openLifeOS factory's `output/meta/`, other avatar repos, historical `identity/wenxin/` / `identity/inneratlas/` reports, or prior Wenxin conclusions. Use only material directly provided in this run, or explicitly approved external source entrances and scopes.
- Confirm the mode, approved sources, and allowed scope first. InnerAtlas starts first; PSP follows after initial identity and experience evidence exists.

This stage will write or update:
- `metabolism/inbox/`: approved material entrypoints or summaries.
- `identity/inneratlas/current/INNERATLAS_REPORT.xml`: InnerAtlas/Wenxin source artifact.
- `identity/wenxin/`: ledgers, public derived summaries, and Skill recommendations.
- `identity/psp/{person_id}/current/PSP_REPORT.xml` and `current/EVIDENCE_MATURITY.xml`: PSP/person model and evidence maturity source artifacts.
- `docs/evidence-sufficiency.md`: evidence maturity and gaps.

Local source-discovery CLI scan:
{format_candidates(candidates, "en-US")}

First question:
Which InnerAtlas mode should start `{display_name}`?

A. Quick mode
Infer from already provided or explicitly approved material; guesses must include evidence. If doctor is below 100%, ask only for missing fields.

B. Complete mode
Infer first, then interact around contradictions, anomalies, key output confirmations, and scenario checks. Completion requires doctor at 100%.

Also define the approved scope: which source entrances may be used, such as specific `gh` repos, `rg/mdfind` directories, or Lark/Feishu docs. Unapproved sources are not used. If local folders are approved, exclude this openLifeOS repo's `output/meta/` and all historical Wenxin/InnerAtlas reports by default unless one specific historical artifact is explicitly provided as current-run material.
"""


def main() -> int:
    args = parse_args()
    target = Path(args.target).expanduser().resolve()
    if not target.exists():
        raise SystemExit(f"Target repo not found: {target}")

    language = repo_language(target, args.language)
    candidates = [] if args.skip_source_scan else run_source_scan(target)
    print(zh(target, candidates) if language == "zh-CN" else en(target, candidates))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
