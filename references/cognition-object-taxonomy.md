# Cognition Object Taxonomy

openLifeOS generated repos must keep declarative memory, procedural skill, identity, policy, and integration data as separate object classes.

The core rule:

> Memory answers what is true. Skill answers how to do something. If a source contains both, split it before writing durable objects.

## Object Classes

| Object | Answers | Default path in generated repo | Allowed contents | Forbidden contents |
| --- | --- | --- | --- | --- |
| `ephemeral_memory` | What matters only in this run? | external session log or `runtime/memory/working-lessons/` intake pointer | active task state, temporary observations, run context | stable facts, reusable procedures |
| `working_lesson` | What candidate lesson may become durable? | `runtime/memory/working-lessons/` | dated lesson, evidence pointer, confidence, scope, review status | polished SOP, private raw transcript |
| `long_term_memory` | What stable fact or preference is true? | `identity/memories/long-term/` or private memory wiki | facts, preferences, decisions, stable constraints, provenance | steps, workflows, scripts |
| `distilled_knowledge` | What claim has been compiled from multiple sources? | `capabilities/*/memory/` or memory wiki | claims, evidence ids, freshness, contradictions | single raw note, task procedure |
| `runtime_skill` | How should a repeatable task be executed? | `docs/skill-system/runtime-skill-candidates.md` or external skill repo | when-to-use, procedure, dependencies, validation, pitfalls | user/project facts, private preferences |
| `distilled_meta_skill` | What reusable judgment should guide future agents? | `identity/wenxin/skill-summaries/` or external meta skill repo | routing rules, decision gates, review standards, abstracted examples | raw task logs, private evidence bodies |
| `policy_persona` | What behavior and boundaries govern the agent? | `identity/`, `security/`, root `AGENT.md` | tone, standing orders, approval rules, risk boundaries | project facts, task workflows |
| `identity_layer` | Who is represented? | `identity/` | self/user/org identity, aliases, public profile, PSP pointers | operational SOP, long memory miscellany |
| `data_source` | Where does evidence come from and what can be copied? | `integrations/data-sources.yml` | connector, authority, visibility, token policy, allowed exports | secrets, copied private source bodies |
| `skill_binding` | Which facts/configs a skill may read without embedding them? | `identity/cognition/skill-bindings/data-sources.yml` | fact dependencies, connector dependencies, visibility constraints | permanent facts inside `SKILL.md` |

## Split Rule

When a captured item contains both facts and procedure:

1. Extract declarative facts into `working_lesson` or `long_term_memory`.
2. Extract repeatable steps into a `runtime_skill` proposal.
3. Create a binding or edge from the skill to the facts it requires.
4. Keep raw evidence in the authorized source; write only pointers or approved summaries to the repo.

## Generated Repo Contract

Every generated LifeOS repo should contain these scaffold files:

- `identity/cognition/object-taxonomy.yml`: machine-readable object classes and write routes.
- `identity/cognition/data-contracts.yml`: connector and authority rules for evidence movement.
- `runtime/memory/working-lessons/README.md`: dated candidate lessons.
- `identity/memories/long-term/README.md`: stable declarative memory.
- `capabilities/*/memory/README.md`: capability-local claim/evidence/contradiction layer.
- `docs/skill-system/runtime-skill-candidates.mdREADME.md`: executable skills.
- `identity/wenxin/skill-summaries/README.md`: distilled meta skills.
- `identity/cognition/skill-bindings/data-sources.yml`: skill-to-data bindings without embedding facts in skills.

This taxonomy extends `memory-isolation-model.md` and `skill-taxonomy-and-promotion.md`; those files remain the privacy and promotion gates.
