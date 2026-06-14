# Translation Review Proposal

Translation ID: `<translation_id>`
Target runtime: `<openclaw|hermes>`
Target profile: `<profile path>`

This file is a proposal surface for SKILL.md-guided semantic tuning. It must not be applied automatically.

## Tuning Policy

- Mode: `proposal_only`.
- The deterministic script output is the baseline.
- A Skill or agent may propose edits to runtime projection files, but must not overwrite canonical LifeOS files.
- Manual confirmation or an explicit apply command is required before proposed changes are applied.

## Immutable Fields

- `profile.manifest.yml` source paths, rules, validation results, and timestamps.
- `coverage-report.yml` coverage status and generated audit categories.
- Secret scan and private body scan results.
- Canonical LifeOS identity, memory, skill, security, and integration files.

## Suggested Review Item

### `<target file>`

- Status: `<present|missing>`
- Source evidence: `<LifeOS source path or manifest entry>`
- Suggested change: `<human-readable proposed tuning>`
- Reason: `<why this improves runtime fit>`
- Risk: `<what can go wrong if applied>`
- Coverage impact: `<none|supported|partial|unsupported backlog update>`

## Proposal Patch

No patch has been applied. Add human-reviewed diff notes here if runtime files need tuning.
