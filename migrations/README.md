# LifeOS Schema Migrations

This directory is the openLifeOS equivalent of an Alembic migration layer.

- `versions/` contains deterministic structural migrations that can move files,
  rewrite paths, and update machine-readable status fields.
- `skills/` contains Skill-based migrations for transformations where the new
  artifact format requires judgment, synthesis, or content extraction from
  historical files.
- `scripts/migrate_lifeos_schema.py <LifeOS> --to latest` is the normal
  upgrade command. The script infers the current `schema_revision`, applies
  each missing deterministic revision in order, and writes reports under
  `legacy/migration-reports/`.

Rules:

- File moves and path rewrites should be implemented in code.
- New content formats whose content comes from historical artifacts should be
  specified as a Skill with explicit input schema, output schema, and review gate.
- Migrations must preserve legacy material under `legacy/` when the target
  cannot be classified into v2 lifecycle or governance layers.
- Root entrypoint changes are schema migrations. For example,
  `0004_root_agent_entrypoint` moves generated avatar repos from root
  `SKILL.md` to root `AGENT.md` while leaving real Skill packages under
  `evolution/organ-systems/*/SKILL.md` and `capabilities/*/SKILL.md`.
