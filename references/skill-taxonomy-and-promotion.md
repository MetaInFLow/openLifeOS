# Skill Taxonomy and Promotion

openLifeOS must not treat every Skill as the same kind of asset.

There are two primary Skill classes:

| Class | Purpose | Examples | Update source | Success signal |
| --- | --- | --- | --- | --- |
| `runtime-skill` | Execute a concrete workflow with tools, connectors, scripts, prompts, or repo-specific operations | Hermes GitHub `SnapAF-skills`, data collection skills, report generators, task automation skills | Runtime failures, task outputs, logs, user feedback, lesson events | The task completes correctly and repeatably |
| `distilled-meta-skill` | Encode reusable judgment, routing, methodology, review gates, and decision patterns | `engineering-everything`, architecture/review/playbook skills, mature personal operating-system skills | IPO retrospectives, repeated lessons, owner alignment, validated patterns | Future agents make better decisions before execution |

Self-evolution skills such as IPO Reverse, Wenxin, PSP, Hermes sync, and cognitive alignment are bridge skills. They may run as runtime skills, but their job is to turn evidence into updates for identity, memory, skill recommendations, runtime skills, or distilled meta skills.

## Runtime Skill Rule

A runtime skill is allowed to be operational and tool-specific. It may contain:

- Tool calls, scripts, connector instructions, repo-specific flows, evals, and examples.
- Task logs, run summaries, bug reports, and private lesson events.
- Implementation details that change as the runtime changes.

Runtime skills do not become meta skills just because they are useful. They produce evidence.

Runtime skills are procedural. A `SKILL.md` may declare required facts, data sources, connectors, and bindings, but it should not embed user facts, private preferences, project memory, or raw evidence bodies. Put those in the appropriate memory layer or `identity/cognition/skill-bindings/data-sources.yml`, then reference them as bindings.

## Distilled Meta Skill Rule

A distilled meta skill is not a task transcript and not a wrapper around a connector. It should contain:

- Stable task routing judgment.
- Reusable decision principles and tradeoff patterns.
- Review gates, validation gates, and escalation rules.
- Abstracted examples that do not leak private source material.
- A changelog, lessons, patterns, or equivalent evidence trail.

A meta skill should change slowly and only from reviewed evidence.

## Promotion Gate

Runtime evidence can upgrade into a distilled meta skill only after this gate:

1. **Runtime evidence captured**: task output, lesson-event, source pointers, failure/success notes, and affected Skill id are recorded privately.
2. **IPO Reverse**: reconstruct the input, process, output, hidden cognitive tasks, middle-layer artifacts, tradeoffs, and reusable IPO from the finished work.
3. **Alignment review**: compare the inferred rule with owner judgment. Decide whether it is real, recurring, privacy-safe, and worth changing a Skill.
4. **Promotion proposal**: create a candidate lesson or pattern with evidence pointers, privacy classification, blast radius, and target Skill.
5. **Owner or maintainer approval**: merge the update through the right repo path. Public meta skills receive only public-safe abstractions.
6. **Verification**: run skill doctor/evals/checklists where available, then update changelog or recommendations.

If any step fails, keep the material as private evidence or a runtime-skill lesson. Do not promote it into meta behavior.

## Storage Mapping

| Evidence | Store first | Promote to | Rule |
| --- | --- | --- | --- |
| One runtime task lesson | Private memory `lesson-event` | Runtime skill issue/lesson queue | Keep raw chronology private |
| Repeated runtime failure pattern | Private memory + runtime skill PR | Runtime skill fix or eval | Fix execution before changing meta judgment |
| Reusable decision principle | Private lesson + IPO Reverse output | Distilled meta skill `references/lessons.md` or `patterns.md` | Requires alignment review |
| Public-safe generalized method | Meta skill reference | Public meta skill docs | Remove private source facts |
| Tool-specific workflow | Runtime skill repo | Runtime skill docs/evals | Do not encode as broad judgment unless proven general |

## Default Generated Repo Rule

Generated LifeOS repos should distinguish:

- `docs/skill-system/runtime-skill-candidates.md` or external runtime skill repos for execution capabilities.
- `identity/wenxin/skill-summaries/` or documented meta skill references for distilled methodology.
- `identity/cognition/skill-bindings/` for skill-to-data contracts, required facts, connector dependencies, and visibility constraints.
- `evolution/organ-systems/` for complete external self-evolution systems such as Wenxin, PSP, and IPO Reverse.
- `integrations/skill-sources/default-skills/` for openLifeOS-owned bridge/fallback notes only. Do not place duplicate Wenxin, PSP, or IPO Reverse skills there.
- `runtime/runtime-skills/` for session-born temporary abilities.
- `capabilities/` for user-distilled durable capabilities and meta capabilities generated from reviewed evidence.
- `identity/wenxin/skill-recommendations.yml` should label each candidate with `skill_type` and `promotion_gate`.

If a skill proposal includes both procedure and stable facts, split it: keep procedure in the Skill candidate, move facts to memory, and connect them through a binding.
