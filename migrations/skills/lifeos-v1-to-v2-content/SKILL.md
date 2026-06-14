---
name: lifeos-v1-to-v2-content-migration
description: Migrate historical LifeOS v1/v1.5 content into LifeOS v2 typed artifacts when the transformation requires semantic judgment rather than file moves.
---

# LifeOS v1 to v2 Content Migration Skill

Use this after `scripts/migrate_lifeos_schema.py` has completed deterministic
file moves.

## Input Schema

```yaml
schema: openlifeos.migration-content-input.v1
source_lifeos: path
target_schema: openlifeos.schema.v2
source_artifacts:
  - path: string
    artifact_type: wenxin | psp | design | runtime_lesson | capability | work | unknown
    current_schema: string
    visibility: public | private | local-only | unknown
requested_outputs:
  - output_type: capability_card | role_card | runtime_lesson | ipo_review | work_index | design_profile
```

## Output Schema

```yaml
schema: openlifeos.migration-content-output.v1
target_schema: openlifeos.schema.v2
outputs:
  - path: string
    output_type: capability_card | role_card | runtime_lesson | ipo_review | work_index | design_profile
    evidence_sources:
      - path: string
        used_for: string
    confidence: low | medium | high
    review_required: true
legacy_leftovers:
  - path: string
    reason: string
```

## Procedure

1. Read `schemas/lifeos.schema.v2.yml` and the migration report in `legacy/migration-reports/`.
2. Classify each historical artifact by what question it answers:
   - identity: who is represented?
   - runtime lesson: what happened in a session?
   - capability: what can this LifeOS reliably do?
   - work: what was created?
   - role: under which social identity does this behavior apply?
3. Produce only typed v2 artifacts listed in the requested outputs.
4. If evidence is insufficient or private, leave the material under `legacy/`
   and emit a `legacy_leftovers` entry instead of guessing.
5. Every output must include evidence sources and `review_required: true`.

## Boundaries

- Do not invent identity, private facts, capabilities, or role claims.
- Do not copy raw private transcripts into v2 public layers.
- Do not promote runtime lessons directly into capabilities without IPO Reverse
  and owner alignment.
