# LifeOS Runtime Translation Layer

Status: draft implemented, v2 tuning proposal layer
Date: 2026-05-30
Scope: openLifeOS factory and generated LifeOS repos

## Problem

openLifeOS generates a canonical digital-person folder:

```text
output/meta/<Person.LifeOS>/
├── identity/
├── metabolism/
├── runtime/
├── evolution/
├── capabilities/
├── identities/
├── security/
├── integrations/
└── docs/
```

OpenClaw and Hermes consume different runtime concepts:

| Framework | Runtime concept | Typical target files |
| --- | --- | --- |
| OpenClaw | Agent workspace | `SOUL.md`, `AGENTS.md`, `USER.md`, `TOOLS.md`, `skills/` |
| Hermes | Profile | `SOUL.md`, `config.yaml`, `PROFILE.md`, `memories/`, `skills/` |

The LifeOS folder should remain the canonical source of truth. Runtime profiles are generated projections.

v2 adds a second layer: AGENT.md-guided and Skill-guided semantic tuning proposals. The script still produces deterministic baseline runtime files, while the agent/Skill layer may only emit review proposals.

## Goals

1. Translate LifeOS artifacts into OpenClaw and Hermes runtime files.
2. Preserve source-to-target traceability through `profile.manifest.yml`.
3. Audit whether LifeOS features are fully supported, partially mapped, unsupported, or intentionally excluded through `coverage-report.yml`.

## Non-Goals

- Do not make OpenClaw or Hermes the source of truth for LifeOS identity, memory, or meta skills.
- Do not export raw private evidence, secrets, or unreviewed working lessons into runtime prompts.
- Do not require OpenClaw or Hermes to natively support every LifeOS mechanism.

## Architecture

```text
LifeOS Folder
  -> source scan
  -> cognition object classification
  -> privacy/security guards
  -> runtime profile projection
  -> optional SKILL-guided review proposal
  -> OpenClaw agent or Hermes profile
  -> manifest + coverage audit
```

The first implementation is file-based and dependency-free:

- Translation rules live in `translations/rules/`.
- Runtime adapter expectations live in `translations/adapters/`.
- Schemas and contracts live in `translations/schemas/`.
- SKILL-guided tuning policy lives in `translations/tuning/`.
- The executable translator is `scripts/translate_lifeos.py`.

## v2 Tuning Layer

The runtime translation path is:

```text
LifeOS canonical folder
-> deterministic script projection
-> optional SKILL-guided review proposal
-> manually confirmed runtime profile changes
```

The default tuning policy is `proposal_only`:

- The script output is the baseline.
- `translation.review.md` is advisory and must not be applied automatically.
- A Skill or agent can propose wording, ordering, and adapter backlog improvements.
- Manual confirmation or an explicit apply command is required before changing generated runtime files.
- Runtime feedback still returns to LifeOS as lesson evidence, then passes through IPO Reverse and owner alignment before changing canonical artifacts.

Immutable script-generated fields:

- `profile.manifest.yml` source paths, rules, validation results, and timestamps.
- `coverage-report.yml` coverage statuses.
- Secret scan and private body scan results.
- Canonical LifeOS identity, memory, skill, security, and integration files.

Allowed review proposal areas:

- `SOUL.md`: target runtime projection voice, section order, boundary wording, confidence note wording. Source remains PSP XML, not a LifeOS `SOUL.md` artifact.
- `AGENTS.md` / `PROFILE.md`: behavior-rule organization and runtime guidance wording.
- `USER.md` / `memories/seed.md`: stable fact ordering and summary readability.
- `TOOLS.md` / `config.yaml`: connector hints and policy note wording.
- Coverage backlog notes for partial or unsupported adapter features.

## Translation Matrix

| LifeOS source | Object type | OpenClaw target | Hermes target | Expected coverage |
| --- | --- | --- | --- | --- |
| `identity/psp/<person>/current/PSP_REPORT.xml` | `identity.psp_xml` | `SOUL.md` runtime projection | `SOUL.md` runtime projection | supported |
| `identity/wenxin/WENXIN_REPORT.md` | `identity.wenxin` | `IDENTITY.md` | `PROFILE.md` | supported |
| `identity/memories/long-term/` | `long_term_memory` | `USER.md` | `memories/seed.md` | partial |
| `capabilities/*/memory/` | `distilled_knowledge` | `USER.md` | `memories/seed.md` | partial |
| `runtime/memory/working-lessons/` | `working_lesson` | `learning_queue/` | `learning_queue/` | intentionally excluded from prompt |
| `runtime/runtime-skills/` | `runtime_skill` | `skills/` | `skills/` | supported |
| `capabilities/` | `distilled_meta_skill` | `AGENTS.md` | `PROFILE.md` | partial |
| `identity/cognition/skill-bindings/data-sources.yml` | `skill_binding` | `TOOLS.md` | `config.yaml` | partial |
| `security/permissions.yml` | `policy` | `AGENTS.md` | `config.yaml` | partial |
| `integrations/data-sources.yml` | `data_source` | `TOOLS.md` | `config.yaml` | partial |
| `docs/evidence-sufficiency.md` | `maturity` | `README.md` | `README.md` | partial |
| `identity/wenxin/skill-recommendations.yml` | `skill_roadmap` | `learning_queue/` | `learning_queue/` | intentionally excluded from runtime activation |

## Generated Artifacts

For OpenClaw:

```text
profiles/openclaw/<agent-id>/
├── SOUL.md
├── AGENTS.md
├── IDENTITY.md
├── USER.md
├── TOOLS.md
├── README.md
├── skills/
├── learning_queue/
├── profile.manifest.yml
├── coverage-report.yml
└── translation.review.md  # optional, proposal-only
```

For Hermes:

```text
profiles/hermes/<profile-id>/
├── SOUL.md
├── PROFILE.md
├── config.yaml
├── README.md
├── memories/
├── skills/
├── learning_queue/
├── profile.manifest.yml
├── coverage-report.yml
└── translation.review.md  # optional, proposal-only
```

## Coverage Audit

The coverage report answers whether anything in LifeOS was lost in translation:

- `supported`: direct or equivalent runtime landing zone exists.
- `partial`: useful projection exists, but enforcement or object structure is weaker.
- `unsupported`: no runtime landing zone exists.
- `intentionally_excluded`: should not affect runtime behavior.

Unsupported coverage does not block profile generation. Privacy violations and missing required runtime outputs should block generation.

## Manifest Additions

`profile.manifest.yml` records tuning state:

```yaml
tuning_policy: "proposal_only"
review_mode: "proposal-only"
review_file: "translation.review.md"
manual_confirmation_required: true
```

If review output is disabled, `review_file` is `not_generated`.

## Command

```bash
python3 scripts/translate_lifeos.py output/meta/ZhangYiming.LifeOS --runtime openclaw --profile-id zhang-yiming --force --emit-review
python3 scripts/translate_lifeos.py output/meta/ZhangYiming.LifeOS --runtime hermes --profile-id zhang-yiming --force --emit-review
```

By default, generated profiles are written inside the LifeOS repo:

```text
<LifeOS>/profiles/<runtime>/<profile-id>/
```

## Feedback Rule

Runtime profiles must not directly mutate canonical LifeOS artifacts. Feedback returns as evidence:

```text
runtime run log
-> working lesson
-> IPO Reverse
-> owner alignment
-> LifeOS update
-> next translation
```
