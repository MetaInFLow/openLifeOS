# openLifeOS Folder Declaration v0

Status: as-is governance note
Date: 2026-05-23
Scope: current `openLifeOS` repository only

## Engineering Route

- Route: Inherit / existing repository / folder governance.
- Stage: I, project handover and structure audit.
- Project shape: lightweight Python CLI plus Skill/template factory repository.
- Main lever: documentation governance, not code restructuring.
- Stop condition for this pass: clarify folder ownership without renaming or moving existing paths.

## Task Contract

Goal: make the current folder architecture explicit enough that an agent or maintainer can safely extend the repo.

Inputs:

- `README.md`: public product narrative and current repository shape.
- `SKILL.md`: factory Skill entrypoint and operating protocol.
- `matrix.yml`: machine-readable layer index.
- `scripts/`: deterministic setup, validation, and progress gates.
- `assets/`: Chinese and English generated repo templates.
- `references/`: blueprint and configuration references.

Output:

- Current folder responsibility map.
- Source-of-truth split between this root repo and generated LifeOS repos.
- Dependency flow for initialization and validation.
- Guardrails for future folder changes.

## One Sentence

This repository is the openLifeOS factory and agent-entry workspace: it defines the public narrative, factory Skill protocol, templates, and Python scripts used to create and validate target LifeOS repositories.

It is not itself a generated personal LifeOS instance. Concrete digital avatars are factory outputs under `output/meta/`.
Generated avatar repos use root `AGENT.md` as their agent reading/routing protocol; the factory root still uses `SKILL.md` so Codex can discover openLifeOS itself as a Skill.

## Current Top-Level Tree

```text
openLifeOS/
├── README.md
├── SKILL.md
├── matrix.yml
├── agents/
│   └── openai.yaml
├── assets/
│   ├── avatar-skill-template/
│   └── avatar-skill-template-en/
├── docs/
│   ├── assets/
│   └── governance/
├── output/
│   └── meta/
├── references/
└── scripts/
```

## Folder Contracts

| Path | Contract | Owner truth | Notes |
| --- | --- | --- | --- |
| `README.md` | Human-facing public explanation of openLifeOS. | Product narrative. | Explains the long-term intelligence kernel and current repo shape. |
| `SKILL.md` | Factory Skill entrypoint and operating protocol. | Runtime behavior contract. | Tells Codex/OpenAI-style agents how to initialize and govern generated LifeOS repos. |
| `matrix.yml` | Machine-readable repository and generated-layer index. | Structure index. | Should mirror actual root layers and generated target layers. |
| `agents/openai.yaml` | OpenAI/Codex app metadata. | Agent UI metadata. | Display name, short description, default prompt, implicit invocation policy. |
| `scripts/` | Deterministic command layer. | Executable behavior. | Prompts for config, applies templates, validates generated repos, reports progress. |
| `assets/avatar-skill-template/` | Default Chinese target repo skeleton. | zh-CN generated repo template. | Contains `.tmpl` files copied/rendered by scripts. |
| `assets/avatar-skill-template-en/` | English target repo skeleton. | en-US generated repo template. | Should stay structurally aligned with the Chinese template. |
| `references/` | Detailed specifications used by humans and agents. | Design/reference truth. | Defines blueprint, config order, and `replicateme.yml` schema. |
| `docs/assets/` | Public presentation images. | Human-facing assets. | Currently stores README visual material. |
| `docs/governance/` | Governance notes for this repo. | Maintainer-facing governance. | Folder declarations and future decision support belong here. |
| `output/meta/` | Local factory output for generated LifeOS repos. | Runtime/generated output. | Contents are gitignored by default; keep only `.gitkeep` in this repo. |

## Root Repo vs Generated Repo

The biggest boundary in this project is between the factory repo and generated LifeOS repos.

This root repo owns:

```text
README.md
SKILL.md
matrix.yml
agents/openai.yaml
scripts/
assets/
references/
docs/
```

A generated target repo owns:

```text
output/meta/Target.LifeOS/
├── replicateme.yml
├── README.md
├── AGENT.md
├── agents/openai.yaml
├── matrix.yml
├── cognition/
├── identity/
├── integrations/
├── skills/
├── memory/
├── security/
└── docs/
```

Therefore, `cognition/`, `identity/`, `integrations/`, `skills/`, `memory/`, `security/`, and `replicateme.yml` are expected inside generated target repos under `output/meta/`, not at the factory root.

The generated `cognition/` layer is the object-boundary contract for each target LifeOS repo. It keeps memory, skill, identity, policy, and data-source routing separate before evidence is written into durable files.

Do not add those generated-instance folders to this root unless the project explicitly decides to make this repository both factory and self-hosted LifeOS instance.

## Initialization Flow

```text
User intent
  -> scripts/tui_avatar_config.py or scripts/prompt_avatar_config.py
  -> replicateme.yml
  -> scripts/apply_avatar_config.py
  -> scripts/init_avatar_repo.py
  -> assets/avatar-skill-template*/ rendered files
  -> output/meta/Target.LifeOS/
  -> scripts/validate_avatar_repo.py
  -> scripts/doctor_avatar_repo.py
  -> scripts/openlifeos_progress.py
```

`references/configuration-order.md` defines the expected phase model for this flow. `doctor_avatar_repo.py` is a validator for generated target repos, not a health check for the generator root.

## Current Script Map

| Script | Role |
| --- | --- |
| `scripts/tui_avatar_config.py` | Interactive setup wizard for user-facing configuration. |
| `scripts/prompt_avatar_config.py` | Prompt-based config writer for `replicateme.yml`. |
| `scripts/apply_avatar_config.py` | Applies config, scaffolds target repo, optionally checks GitHub tooling/remotes. |
| `scripts/init_avatar_repo.py` | Copies and renders a target repo from bundled templates. |
| `scripts/validate_avatar_repo.py` | Checks generated repo required paths, unresolved template tokens, and common secret patterns. |
| `scripts/doctor_avatar_repo.py` | Reports generated repo completion by phase. |
| `scripts/openlifeos_progress.py` | Agent-facing wrapper around doctor checks. |
| `scripts/synthesize_avatar_description.py` | Conservatively refreshes the structured current Avatar description refs/evidence from active artifacts without rewriting claim text unless approved. |
| `scripts/replicateme_yaml.py` | Minimal flat YAML reader/writer helper. |

## Governance Rules

1. Keep `SKILL.md`, `README.md`, `matrix.yml`, and `references/` consistent when changing semantics.
2. Keep Chinese and English templates structurally aligned unless divergence is intentional and documented.
3. Treat `scripts/` behavior as the executable truth; references must not promise outputs the scripts cannot create.
4. Treat `references/configuration-order.md` as the phase model for generated target repos.
5. Do not commit secrets, raw private material, private wiki bodies, customer data, or unapproved identity material; memory isolation rules live in `references/memory-isolation-model.md`, and Skill promotion rules live in `references/skill-taxonomy-and-promotion.md`.
6. Keep concrete generated avatars under `output/meta/`; do not promote generated instance files into the factory root.
7. Preserve compatibility names such as `replicateme.yml` and `scripts/*avatar*` until a deliberate migration decision is recorded.
8. New generated repo layers should first be added to templates, then reflected in `matrix.yml`, references, and validators.
9. New architectural decisions should be recorded under `docs/governance/` or promoted later to `docs/decisions/` if ADR lifecycle is adopted.

## Observed Gaps

These are not blockers, but they matter for maintainability:

- There is no `pyproject.toml`, `requirements.txt`, or `Makefile`; scripts currently rely only on the Python standard library.
- There is no formal test suite; the current lightweight verification is `python3 -m py_compile scripts/*.py`.
- `doctor_avatar_repo.py .` fails on the root repo by design, because root is the generator and not a generated target repo.
- `output/meta/` is now the local factory output convention; generated contents are intentionally ignored.
- `docs/` previously only held public assets; governance documentation now starts here.
- Historical names still use `avatar` and `replicateme`; README and `SKILL.md` already document them as compatibility interfaces.

## Recommended Next Structure Work

| Priority | Action | Target | Validation |
| --- | --- | --- | --- |
| P0 | Keep this folder declaration current when top-level folders change. | `docs/governance/folder-declaration-v0.md` | `git diff --check` |
| P0 | Keep generated avatar instances inside factory output. | `output/meta/<Target.LifeOS>/` | generated contents stay gitignored |
| P1 | Add a tiny developer command surface. | `Makefile` or `pyproject.toml` scripts | `python3 -m py_compile scripts/*.py` |
| P1 | Add generated-repo fixtures for validator/doctor tests. | `tests/fixtures/` or `fixtures/` | run validator against passing and failing fixtures |
| P2 | Decide whether compatibility names should remain forever or migrate. | future ADR/governance note | scripts, README, templates updated together |
| P2 | Add a docs index if governance docs grow. | `docs/README.md` | links resolve |
