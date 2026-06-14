# Configuration Order

Use this sequence when guiding a user through a new digital-avatar Skill repo. The current `openLifeOS` repo acts as a factory: setup starts from a TUI-generated YAML config, then applies that config to create concrete avatar repos under `output/meta/<Target.LifeOS>/`, check tooling, and wire the first artifacts. The architecture is a loop: Wenxin helps the user understand themselves, Skill distillation turns strong capabilities into reusable Skills, PSP models the deeper person, Hermes feeds new evidence back into the repo, and wiki sync keeps long-term memory authoritative.

## Lifecycle vs Initialization

The current generated-repo schema is LifeOS schema v2, defined in `schemas/lifeos.schema.v2.yml`.

Schema migration is versioned:

- deterministic moves/path rewrites: `scripts/migrate_lifeos_schema.py` and `migrations/versions/*.py`;
- semantic content transformation into new artifact formats: `migrations/skills/*/SKILL.md`, with explicit input schema, output schema, evidence sources, and review requirements.

Use `python scripts/migrate_lifeos_schema.py <LifeOS> --to latest` for normal upgrades. The script infers the current `schema_revision`, applies missing revisions in order, and writes `legacy/migration-reports/*.json`.

初始化 gates 和数字生命 lifecycle 必须分开。

初始化 gates 回答“目标、边界、骨架、权限、入口、标准和 review surface 是否齐”；Stage 0-8 回答“这个 LifeOS 是否已经开始真实 intake、session、lesson、IPO evolution 和 capability 成长”。

Canonical lifecycle data flow:

```text
metabolism/inbox
-> runtime/sessions
-> runtime/runtime-skills
-> runtime/runtime-lessons
-> evolution/ipo
-> capabilities
```

| Lifecycle stage | 数字生命状态 | 判断重点 |
| --- | --- | --- |
| Stage 0 Kernel Newborn | 刚初始化，只有身体结构。 | lifecycle 目录骨架存在，但没有消化后的 identity/runtime/capability 证据。 |
| Stage 1 Evidence Intake | 原材料进入系统，还没有 Wenxin/PSP 结论。 | `metabolism/inbox/` source manifest 和材料用途。 |
| Stage 2 Wenxin Complete | 第一轮自我认知形成。 | `identity/wenxin/` reports、conclusions、versions。 |
| Stage 3 PSP Complete | 更深的人物模型形成。 | `identity/psp/` fingerprints、reasoning/decision/communication patterns、PSP artifact。 |
| Stage 4 Cloud Runtime | 开始有真实运行活动。 | `runtime/sessions/` run log、任务反馈、outputs、observations。 |
| Stage 5 Runtime Skill | session 中长出局部可复用能力。 | `runtime/runtime-skills/` concrete workflow candidates。 |
| Stage 6 Runtime Lesson | session 产生局部经验。 | `runtime/runtime-lessons/` lesson-event、failure pattern、owner feedback。 |
| Stage 7 IPO Running | 完成产物进入 IPO Reverse。 | `evolution/ipo/` reverse reports、promotion evidence、owner alignment。 |
| Stage 8 Meta Skill Formation | 多个 runtime skill 融合为稳定能力。 | `capabilities/` capability map、promoted skill binding、installable Skill references。 |

`scripts/doctor_avatar_repo.py` 应同时报告 scaffold/progress completion 和 lifecycle stage/age。`100%` progress 只代表结构/协议门禁通过，不代表内容成熟、人格成熟、能力成熟或 Stage 8。

## Phase Outputs

`scripts/doctor_avatar_repo.py` uses these expected outputs as its completion model.

| Phase | Required | Type | Expected outputs | Completion gate |
| --- | --- | --- | --- | --- |
| Stage Notice | Yes | Agent-driven | User-facing statement of current stage, what is being done, why input is needed, and what is not needed this round | User understands whether the agent is doing target setup, boundary setup, scaffold, evidence intake, synthesis, progress, or output. |
| Target Gate | Yes | User input | `repo_name`, `identity_mode`, `owner_name`, `display_name`, `psp_display_name`, `person_id`, `language` | Target identity is explicit. Anonymous mode uses `psp_display_name` as the PSP pseudonym and does not require a real name. |
| 0. Boundary | Yes | Hardcoded | `security/README.md`; `matrix.yml` `visibility`; banned-material rules for secrets and private content | Security boundary exists and visibility is `local-only`, `private`, or `public`. |
| 1. Language | Yes | Hardcoded | `matrix.yml` `language`; generated root `AGENT.md` in selected template language | Language is `zh-CN` or `en-US`; default is `zh-CN`. |
| 2. Setup config and permissions | Yes | TUI-generated + deterministic | `replicateme.yml`; GitHub owner/auth/scopes; Feishu app/auth/scopes; Hermes update intent; avatar repo config; memory wiki repo config; gh requirement/auth flags | YAML exists and is filled; integration permission configs exist; `git`/`gh` are installed or GitHub setup is explicitly disabled. |
| 3. Skeleton | Yes | Hardcoded | `replicateme.yml`; `LIFEOS-CATALOG.html`; `README.md`; `AGENT.md`; `agents/openai.yaml`; `matrix.yml`; `artifacts/current.yml`; `SOUL.md`; `DESIGN.md`; `design/versions.yml`; layer READMEs; lifecycle layers `identity/`, `metabolism/`, `runtime/`, `evolution/`, `capabilities/`, `identities/`, `work/`; governance layers `integrations/`, `security/`, `docs/`, `artifacts/`; compatibility layer `legacy/`; `identity/cognition/`; `identity/memories/`; `runtime/memory/`; `integrations/github.yml`; `integrations/feishu.yml`; `integrations/hermes.yml`; `security/permissions.yml`; `identity/memories/START-HERE.md`; `identity/memories/wiki-repo.yml`; `identity/wenxin/skill-recommendations.yml`; `identity/psp/<person_id>/PSP.md`; `identity/psp/<person_id>/SOUL-<timestamp>.md`; `identity/psp/<person_id>/update-log.md` | Required files exist. |
| 4. Public profile | Yes | Hardcoded with user input | `identity/public-profile/profile.yml` with `identity_mode`, `owner_name`, `display_name`, `psp_display_name`, `person_id`, `public_summary` | Required profile fields are filled and not TODO. |
| 4.5. Evidence sufficiency | Yes | Generated and updated after every intake/synthesis pass | `docs/evidence-sufficiency.md` | Separates structure readiness from content maturity; records source coverage, failed sources, incomplete areas, maturity level, and final disclosure requirements. |
| 4.6. Self-evolution output standards | Yes | Hardcoded standard + generated artifacts follow it | `docs/self-evolution-output-standards.md`; generated Wenxin/PSP/Soul/Design/IPO artifacts | Wenxin, PSP, Soul, Design, and IPO Reverse artifacts pass only when key fields are filled; if evidence is insufficient, they must declare insufficiency and list targeted missing-information prompts. |
| 5. Wenxin self-discovery | No | Generated and iterative | `identity/wenxin/WENXIN_REPORT.md`; optional `identity/wenxin/public-positioning.md`; optional `identity/wenxin/skill-recommendations.yml` | Wenxin output explains who the person is, where they stand, field coverage, gaps, future paths, and candidate Skills to distill. |
| 6. Skill recommendations | No | Generated | Evidence-backed `identity/wenxin/skill-recommendations.yml` | Wenxin-generated recommendation list labels runtime vs distilled meta skill candidates, records evidence needs, and only recommends a Skill when it satisfies either `top_5_percent_capability_hypothesis` or `repeated_workflow`; meta-skill upgrades still require IPO Reverse + owner alignment. |
| 7. PSP/person model | No | Generated and iterative | `identity/psp/<person_id>/PSP.md`; `SOUL.md`; `identity/psp/<person_id>/update-log.md` | PSP has no TODO/scaffold markers, is substantial enough to guide behavior; Soul extracts evidence-backed operating methods from PSP; future updates are logged. |
| 7.5. Global design | No | Generated and iterative | `DESIGN.md`; `design/DESIGN-<timestamp>.md`; `design/versions.yml`; `design/changelog.md` | Global aesthetics and expression preferences are evidence-backed; project-specific UI needs are not automatically promoted to long-term preference. |
| 8. Memory wiki and sync | No | GitHub/server-backed + mixed | `identity/memories/wiki-repo.yml`; `identity/memories/START-HERE.md`; optional GitHub memory repo; optional rsync server source | Memory follows `memory-isolation-model.md`: identity memories hold long-term self context, runtime memory holds session context, capability memory holds domain experience; raw private bodies are linked or abstracted. |
| 9. Hermes self-evolution sync | No | Integration-generated | `integrations/hermes.yml`; update cadence; allowed source usage; target artifacts | Hermes can route new evidence into Wenxin, PSP, skill recommendations, memory index, and GitHub PR/update flow without storing secrets. |
| 10. Capabilities | No | Mixed | Concrete `capabilities/**` files, `runtime/runtime-skills/**`, `evolution/organ-systems/**`, or `matrix.yml` capability bindings | At least one stable capability or self-evolution organ system is wired; skill recommendations can drive future capability creation. |
| 11. Routing | Yes | Hardcoded update | Root `AGENT.md` references identity, Wenxin, PSP, memory, skills, integrations, Hermes, security paths, and status/alignment checks | AI can choose sources without guessing and can report current alignment state. |
| 12. Final validation | Yes | Deterministic | `validate_avatar_repo.py` result | No unresolved template tokens or common secret patterns. |

Run:

```bash
python scripts/tui_avatar_config.py --output replicateme.yml
python scripts/apply_avatar_config.py replicateme.yml
python scripts/doctor_avatar_repo.py <target>
python scripts/doctor_avatar_repo.py <target> --strict
python scripts/doctor_avatar_repo.py <target> --json
```

If the YAML requests GitHub repo creation, first install and authenticate GitHub CLI:

```bash
python scripts/apply_avatar_config.py replicateme.yml --install-tools
gh auth login
python scripts/apply_avatar_config.py replicateme.yml --create-remotes
```

## Minimum User Inputs

Progress reports must not describe a LifeOS as "complete" solely because `doctor_avatar_repo.py` reaches 100%. That status means structure/protocol readiness. Doctor reports must also show lifecycle stage/age and the reason for that stage. Use `docs/evidence-sufficiency.md` to report evidence maturity (`scaffold`, `evidence-limited-v0`, `public-v0`, `research-grade`, or `avatar-grade`), unavailable sources, remaining gaps, and whether any Skill files are instance-local or installable. `doctor_avatar_repo.py` must also return `skill_content_maturity`, computed from each built-in Skill's expected output structure, especially PSP XML. Use `docs/self-evolution-output-standards.md` to decide whether Wenxin/InnerAtlas, PSP XML, Soul, Design, and IPO Reverse artifacts pass: key fields must be filled, otherwise the artifact must declare insufficient evidence and ask for the missing information.

The doctor must not replace Skill-level semantic review. It exposes `skill_review_surface` and `skill_content_maturity` so the LifeOS Skill can locate current entrypoints, see structure-derived content gaps, and then review factual reliability, owner alignment, and next-step strategy. The semantic review must be written to `docs/lifeos-content-review.md` and then used as the next-step recommendation queue.

Ask only for missing inputs that materially affect the repo:

- Target owner or avatar subject.
- Identity mode: named or anonymous. If anonymous, ask for a PSP pseudonym instead of a real-world identity.
- Repo name.
- Local output path. Default: `output/meta/<repo_name>`.
- Public/private/local-only visibility.
- Language: default Chinese `zh-CN`; English `en-US` only when requested.
- GitHub owner/org, auth method, required permissions/scopes, whether to require `gh`, and whether to create remote repos.
- Feishu/Lark app type, auth method, required permissions/scopes, source usage, and token storage policy.
- Memory wiki repo name and visibility. Default to a private GitHub repo and record it in `identity/memories/wiki-repo.yml`.
- Memory public mirror and collaboration policy. Default to `index-only` plus `private-pr-or-owner-approved-extract`.
- Wiki authoritative source: GitHub, server via rsync, or local-only. If server is selected, record it as the single source of truth.
- Hermes update intent, allowed source usage, update cadence, and token policy.
- Public facts allowed in the repo.
- Wenxin goals: self-understanding, public positioning, field map, gap analysis, future paths, and candidate Skill recommendations.
- Core professional domains that may become recommended personal Skills after Wenxin only when they pass one of two gates: highly possible top-5-percent/high-percentile capability, or repeated work with extractable stable inputs, process, outputs, and acceptance criteria.
- Whether each Skill candidate is a runtime skill, distilled meta skill, or self-evolution bridge; meta upgrades require IPO Reverse plus owner alignment.
- Which generated artifacts should be produced now versus left as TODO.
- Which memory, capability, or organ-system repos should be linked as private submodules.

## Fixed Tasks

Do these directly:

- Create directory layout.
- Create root `AGENT.md`, `matrix.yml`, `agents/openai.yaml`.
- Create or copy `replicateme.yml`.
- Create first-class lifecycle layers: `identity/`, `identity/cognition/`, `identity/memories/`, `metabolism/`, `metabolism/inbox/`, `metabolism/processing/`, `metabolism/extracted/`, `runtime/`, `runtime/sessions/`, `runtime/runtime-skills/`, `runtime/runtime-lessons/`, `runtime/memory/`, `evolution/`, `evolution/ipo/`, `evolution/organ-systems/`, `capabilities/`, `identities/`, and `work/`.
- Keep governance/compatibility layers: `integrations/`, `security/`, `docs/`, `artifacts/`, and `legacy/`.
- Create `security/README.md`.
- Create `security/permissions.yml`.
- Create integration permission stubs: `integrations/github.yml`, `integrations/feishu.yml`.
- Create Hermes sync stub: `integrations/hermes.yml`.
- Create public profile schema with TODO values.
- Create GitHub/memory config stubs: `identity/memories/wiki-repo.yml`.
- Create Skill recommendation stub: `identity/wenxin/skill-recommendations.yml`.
- Create stubs for `artifacts/current.yml`, `SOUL.md`, `DESIGN.md`, `design/`, `identity/wenxin/`, `identity/psp/<person_id>/`, `identity/cognition/`, `identity/memories/`, `runtime/memory/`, `capabilities/`, `evolution/organ-systems/`, and `docs/`.

## Generated Tasks

Only do these when source material is available:

- Generate Wenxin self-discovery report: internal self-understanding, field map, completion/gap analysis, future paths, and public-safe positioning.
- Generate candidate personal Skills from Wenxin, such as an engineer-specific Skill for an engineer avatar.
- Generate recommended personal Skill recommendations from Wenxin and approved evidence; do not promote self-evolution tools, generic interests, one-off projects, or aspirational gaps as personal Skills.
- Generate PSP/person model.
- Generate Soul/operating-method only from evidence-backed PSP claims.
- Generate global design/aesthetics only from owner-approved design or expression evidence.
- Continuously update PSP/person model, Soul, and design from approved new material and record updates in each versions ledger, changelog, and `artifacts/current.yml`.
- Generate memory area index from a private wiki.
- Create or connect the user's own GitHub memory wiki repo and point `identity/memories/wiki-repo.yml` to it.
- Configure rsync to an internal server when needed; if configured as authoritative, treat the server as the only source of truth and GitHub as a collaboration/publishing surface.
- Use Hermes to package new evidence into safe summaries, update Wenxin/PSP/Skill recommendations, and open or prepare GitHub updates.
- Generate public README narrative.
- Generate public architecture/cover visual.

## Handoff Checklist

- `python scripts/validate_avatar_repo.py <target>` passes.
- `python scripts/doctor_avatar_repo.py <target>` shows expected incomplete generated phases or full completion.
- `git status --short` shows only intended files.
- The target repo is initialized with git if requested.
- Remote creation or push is deferred unless the user explicitly chose visibility and destination.
