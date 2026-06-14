# Cognitive Architecture Benchmark: Hermes and OpenClaw

Status: adopted as generated-repo scaffold guidance
Date: 2026-05-25
Scope: openLifeOS factory and generated LifeOS repos

## Decision

openLifeOS adopts a typed cognition boundary inspired by Hermes and OpenClaw patterns:

- Memory stores declarative, durable facts and claims.
- Skills store reusable procedures and validation gates.
- Identity and policy are separate from memory.
- Integration data sources declare authority, visibility, and allowed exports before evidence can move.
- Mixed source material must be split before durable promotion.

This is now reflected in generated repo scaffolds through `identity/cognition/`, `runtime/memory/working-lessons/`, `identity/memories/long-term/`, `capabilities/*/memory/`, `runtime/runtime-skills/`, `identity/wenxin/skill-summaries/`, and `identity/cognition/skill-bindings/`.

## What We Borrow

| Source pattern | openLifeOS adoption |
| --- | --- |
| Hermes-style strict memory/skill split | `identity/cognition/object-taxonomy.yml` and Skill binding rules |
| File-first inspectability | Markdown/YAML scaffold files in generated repos |
| Skill progressive disclosure | `runtime/runtime-skills/`, `identity/wenxin/skill-summaries/`, and `identity/cognition/skill-bindings/` |
| OpenClaw-style working memory and dreaming layers | `runtime/memory/working-lessons/` as session-context and promotion layer |
| Claim/evidence knowledge layer | `capabilities/*/memory/` for capability-local compiled claims |
| Workspace bootstrap files | generated root `AGENT.md`, `matrix.yml`, `identity/`, `metabolism/`, `runtime/`, `evolution/`, `capabilities/`, `identities/`, `security/`, `integrations/` |

## What We Do Not Claim Yet

The factory does not yet implement a runtime SQLite registry, vector index, automatic dream loop, or conflict engine. Those are target architecture directions. The current hardening step is structural: generated outputs now contain the files and contracts needed to add those systems without mixing memory, skill, identity, and policy.

## Implementation Contract

Any generated LifeOS repo must include:

- machine-readable cognition taxonomy and data contracts;
- explicit data-source integration policy;
- separate memory write targets for working lessons, long-term memory, and distilled knowledge;
- separate skill targets for runtime skills, meta skills, and data bindings;
- validation checks that fail when these scaffold files are absent.

Future SQLite/vector/dream-loop implementation should treat these files as the human-readable materialized surface, not as a reason to collapse object classes.
