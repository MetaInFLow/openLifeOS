# Refactor Plan: LifeOS v2 Baseline Generator And Doctor

Generated: 2026-06-02

## Background

`AnthonyHF.LifeOS` is now the best current LifeOS v2 baseline. A fresh instance, `output/meta/原始人.LifeOS`, was generated with `scripts/init_avatar_repo.py` and compared against `AnthonyHF.LifeOS`.

After running migrations, `原始人.LifeOS` top-level structure matches v2:

```text
artifacts/
capabilities/
docs/
evolution/
identities/
identity/
integrations/
legacy/
metabolism/
runtime/
security/
work/
```

But two issues were found:

1. The generator still emits old top-level directories before migration:
   - `agents/`
   - `design/`
   - `scripts/`
2. Doctor currently classifies a fresh scaffold as `Stage 3 · PSP Complete` because template PSP/Wenxin files exist, even though no evidence-backed Wenxin or PSP run has happened.

This means the repo can pass compatibility validation while still not being clean as a direct v2 baseline.

## Goal

Make a newly initialized LifeOS instance directly match the current v2 baseline without requiring migration cleanup, and make lifecycle diagnosis distinguish scaffold files from real evidence-backed artifacts.

## Non-Goals

- Do not change `AnthonyHF.LifeOS` as the baseline structure.
- Do not remove compatibility support for migrating older generated repos.
- Do not require every LifeOS to contain Anthony-specific outputs such as homepage app, avatar page view model, runtime profiles, or stable capabilities.
- Do not treat Wenxin/PSP scaffold files as real completed synthesis artifacts.

## Desired Behavior

### Fresh LifeOS

Running:

```bash
python scripts/init_avatar_repo.py output/meta/原始人.LifeOS \
  --owner-name 原始人 \
  --display-name 原始人 \
  --psp-display-name 原始人 \
  --person-id yuan-shi-ren \
  --visibility local-only \
  --language zh-CN \
  --lifecycle delivery
```

should directly produce only allowed v2 top-level directories:

```text
artifacts/
capabilities/
docs/
evolution/
identities/
identity/
integrations/
legacy/
metabolism/
runtime/
security/
work/
```

There should be no fresh top-level:

```text
agents/
design/
scripts/
memory/
skills/
cognition/
profiles/
apps/
roles/
intake/
```

### Doctor

A fresh generated LifeOS should report:

```text
required_completion: 100
overall_completion: incomplete
content_maturity: scaffold
life_stage: Stage 0 or Kernel Scaffold
```

It should not report:

```text
Stage 3 · PSP Complete
```

unless the current PSP/Wenxin artifacts are evidence-backed generated outputs, not initialization placeholders.

## Root Causes

### Generator/template mismatch

Current templates still include old top-level files:

```text
assets/avatar-skill-template/agents/openai.yaml.tmpl
assets/avatar-skill-template/design/*
assets/avatar-skill-template/scripts/update_default_skills.py.tmpl
```

The migration script knows how to move them:

```text
agents -> integrations/agents
design -> identity/design
scripts -> legacy/scripts
```

But the generator should not need this migration for a fresh repo.

### Validator compatibility masks baseline drift

`scripts/validate_avatar_repo.py` allows old-or-new path options:

```python
("agents/openai.yaml", "integrations/agents/openai.yaml")
("design/README.md", "identity/design/README.md")
("scripts/update_default_skills.py", "legacy/scripts/update_default_skills.py")
```

This is correct for migration compatibility, but insufficient for checking whether a freshly generated repo is v2-clean.

### Doctor stage detection is file-existence based

`scripts/doctor_avatar_repo.py` currently treats the existence of `identity/wenxin/WENXIN_REPORT.md` and `identity/psp/*` as enough to infer Wenxin/PSP lifecycle progress.

That is too weak because scaffold files exist at initialization time.

## Refactor Steps

### Step 1: Move template files to v2 locations

Update both Chinese and English templates:

```text
assets/avatar-skill-template/agents/openai.yaml.tmpl
-> assets/avatar-skill-template/integrations/agents/openai.yaml.tmpl

assets/avatar-skill-template/design/*
-> assets/avatar-skill-template/identity/design/*

assets/avatar-skill-template/scripts/update_default_skills.py.tmpl
-> assets/avatar-skill-template/legacy/scripts/update_default_skills.py.tmpl
```

Repeat the same moves for:

```text
assets/avatar-skill-template-en/
```

Expected result: `init_avatar_repo.py` renders v2-clean structure directly.

### Step 2: Update template references

Search and update references in both templates:

```text
agents/openai.yaml -> integrations/agents/openai.yaml
design/ -> identity/design/
scripts/update_default_skills.py -> legacy/scripts/update_default_skills.py
```

Do not rewrite references where they intentionally describe migration history or compatibility.

### Step 3: Add strict v2 baseline validation

Add a strict mode to `scripts/validate_avatar_repo.py`:

```bash
python scripts/validate_avatar_repo.py <repo> --strict-v2
```

Strict mode should fail if any disallowed top-level directory exists:

```text
agents/
apps/
profiles/
scripts/
design/
life/
system/
skills/
memory/
cognition/
intake/
roles/
```

Normal mode can keep compatibility options for old repos.

### Step 4: Fix doctor lifecycle stage detection

Doctor should separate:

- scaffold presence
- evidence-backed artifact completion

Suggested rules:

```text
Stage 0 Kernel Scaffold:
  required scaffold exists, but docs/evidence-sufficiency.md says scaffold or artifacts have placeholder/scaffold status.

Stage 1 Evidence Intake:
  metabolism has non-placeholder intake or processing evidence.

Stage 2 Wenxin Complete:
  active Wenxin artifact exists and registry/evidence marks it generated/reviewed, not scaffold.

Stage 3 PSP Complete:
  active PSP artifact exists and registry/evidence marks it generated/reviewed, not scaffold.

Stage 4+ Runtime:
  runtime/sessions has concrete session records beyond README/index placeholders.

Stage 5-6 Runtime Skills/Lessons:
  runtime skill/lesson records exist beyond README/index placeholders.

Stage 7 IPO:
  evolution/ipo contains concrete IPO artifacts beyond README/index placeholders.

Stage 8 Meta Skill Formation:
  capabilities contains promoted durable capability artifacts beyond README/index placeholders.
```

Implementation should prefer machine-readable evidence:

```text
docs/evidence-sufficiency.md
artifacts/current.yml
identity/current.yml
identity/*/versions.yml
identity/avatar-description/current.yml
```

If status is `scaffold`, `placeholder`, `template`, or evidence level is insufficient, do not count it as lifecycle completion.

### Step 5: Update tests

Add or update tests:

```text
tests/test_init_avatar_repo_v2_baseline.py
tests/test_validate_avatar_repo.py
tests/test_doctor_avatar_repo.py
```

Required test cases:

1. Fresh init creates no disallowed top-level dirs.
2. Fresh init passes normal validation.
3. Fresh init passes strict v2 validation.
4. Fresh init doctor reports scaffold / Stage 0, not Stage 3.
5. A repo with real evidence-backed Wenxin/PSP artifacts can still advance to Stage 2/3.
6. Old repos with `agents/`, `design/`, `scripts/` can still be migrated by `scripts/migrate_lifeos_schema.py`.

### Step 6: Recreate `原始人.LifeOS` as acceptance fixture

After refactor:

1. Delete or archive current `output/meta/原始人.LifeOS`.
2. Re-run `init_avatar_repo.py`.
3. Run:

```bash
python scripts/validate_avatar_repo.py output/meta/原始人.LifeOS
python scripts/validate_avatar_repo.py output/meta/原始人.LifeOS --strict-v2
python scripts/doctor_avatar_repo.py output/meta/原始人.LifeOS --json
python scripts/openlifeos_progress.py output/meta/原始人.LifeOS --json
```

Expected:

```text
normal validation: pass
strict v2 validation: pass
doctor required: 100
doctor overall: incomplete
doctor maturity: scaffold
doctor life stage: Stage 0 / Kernel Scaffold
```

## Acceptance Criteria

- Fresh LifeOS generation produces v2-clean top-level structure without migration.
- `agents/`, `design/`, and `scripts/` no longer appear in fresh generated repos.
- Migration still supports old repos.
- Validator has strict mode for v2 baseline enforcement.
- Doctor no longer treats scaffold Wenxin/PSP files as completed lifecycle stages.
- `AnthonyHF.LifeOS` still validates.
- `原始人.LifeOS` validates as a newborn scaffold, not as PSP-complete.

## Risk Notes

- Some tests currently expect file existence to imply higher lifecycle stage; these tests need to be rewritten to include evidence status.
- `current_role` remains part of avatar-description schema for compatibility; do not rename it in this refactor unless a separate schema migration is planned.
- Self-evolution organ-system installation from GitHub can make fresh-init tests slow or network-dependent. Unit tests should use `--skip-self-evolution-skill-install` unless testing install behavior specifically.
