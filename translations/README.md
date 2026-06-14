# LifeOS Runtime Translation Layer

openLifeOS stores the canonical digital-person repo. Runtime frameworks consume projections of that repo.

This layer defines how a generated LifeOS folder is translated into runtime profiles:

- OpenClaw: agent workspace projection.
- Hermes: profile projection.

The translation layer has three jobs:

1. Translate LifeOS artifacts into runtime files.
2. Preserve traceability through a manifest.
3. Audit feature coverage so unsupported or lossy mappings are visible.
4. Optionally emit a SKILL-guided review proposal for semantic tuning.

## Source And Target

```text
output/meta/<Person.LifeOS>/
  identity/
  memory/
  skills/
  cognition/
  security/
  integrations/
  docs/
        ↓
translations/rules/*
        ↓
profiles/<runtime>/<profile-id>/
```

The LifeOS folder remains the source of truth. Runtime profiles are projections and should not directly update identity, PSP, long-term memory, or meta skills.

Runtime feedback flows back as evidence:

```text
runtime logs
-> working lesson
-> IPO Reverse
-> owner alignment
-> LifeOS update
-> next translation
```

## Required Outputs

Each translation run must produce:

- runtime files such as `SOUL.md`, `AGENTS.md`, `USER.md`, `config.yaml`, `memories/seed.md`, or `skills/`;
- `profile.manifest.yml`, recording sources, rules, exclusions, and validation;
- `coverage-report.yml`, recording supported, partial, unsupported, and intentionally excluded LifeOS features.

When `--emit-review` is used, the run also produces:

- `translation.review.md`, a proposal-only review surface for SKILL.md-guided tuning.

`translation.review.md` must not be applied automatically. It can suggest runtime wording, ordering, and adapter backlog improvements, but it cannot change canonical LifeOS files, manifest provenance, coverage status, or scan results.

## Coverage Status

| Status | Meaning |
| --- | --- |
| `supported` | The runtime has a direct or equivalent landing zone. |
| `partial` | The translation preserves useful semantics but loses enforcement or structure. |
| `unsupported` | The runtime has no native landing zone. |
| `intentionally_excluded` | The object should not affect runtime behavior, usually for privacy or maturity reasons. |

## Commands

```bash
python3 scripts/translate_lifeos.py output/meta/Target.LifeOS --runtime openclaw --profile-id target --force --emit-review
python3 scripts/translate_lifeos.py output/meta/Target.LifeOS --runtime hermes --profile-id target --force --emit-review
```
