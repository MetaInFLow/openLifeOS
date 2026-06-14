# Memory Isolation Model

openLifeOS memory must be useful for collaboration without turning the public repo into a private data store.

The rule is simple: public memory is a derived surface, private memory is the collaboration surface, and raw sensitive material stays in the authoritative private source.

Memory is declarative. It may store facts, preferences, decisions, constraints, claims, evidence pointers, freshness, and contradiction status. It must not store reusable procedures or task workflows. When an intake note contains both factual memory and a repeatable procedure, split it before promotion: the factual part stays in memory and the procedural part becomes a Skill proposal or Skill update.

## Storage Tiers

| Tier | Visibility | Purpose | Allowed contents | Collaboration mode |
| --- | --- | --- | --- | --- |
| Public surface | `public` | Open-source interface, public README/docs, public-safe indexes | Confirmed public facts, owner-approved summaries, redacted links, abstracted non-reversible conclusions | Public PR or issue |
| Private collaboration | `private` | Shared memory/wiki repo for trusted collaborators and agents | Working context, area indexes, private-but-shareable summaries, source pointers, review notes | Private PR or owner-approved branch |
| Local/server authority | `local-only` | Authoritative raw context source | Private wiki bodies, Feishu/Lark exports, raw transcripts, customer docs, personal records | Owner-approved extracts only |
| Banned material | `banned` | Not memory | Secrets, tokens, passwords, cookies, private keys, credential dumps | Never store |

## Metadata Contract

Every memory source or area should be classifiable by these fields:

- `object_type`: `skill-run`, `lesson-event`, `source-artifact`, `thought-fragment`, `area-index`, `distilled-pattern`, or `skill-upgrade-candidate`.
- `visibility`: `public`, `private`, `local-only`, or `banned`.
- `authority`: `public-repo`, `memory-wiki`, `server-rsync`, `local-vault`, or an external app label.
- `source_state`: `raw`, `redacted`, `abstracted`, or `approved-public`.
- `collaboration_mode`: `public-pr`, `private-pr`, `owner-approved-extract`, or `none`.
- `public_mirror`: `none`, `index-only`, or `approved-derived`.
- `lifecycle_state`: `captured`, `triaged`, `linked`, `promoted`, or `archived`.

## Movement Rules

1. Downward access is allowed by permission: an agent may read a private source only when that source is configured and authorized.
2. Upward copying is not allowed: private or local-only bodies must not be copied into a more public tier.
3. Upward derivation is allowed only after redaction or abstraction: a public surface can contain approved facts, redacted summaries, and non-reversible conclusions.
4. The authoritative source wins factual conflicts. If `authoritative_source` is `server-rsync`, server state beats GitHub mirrors. If it is `github`, the private memory wiki beats stale public artifacts.
5. Public repos may point to private sources, but the pointer must describe the boundary and must not expose source text.
6. Hermes and other sync agents should operate on approved materials or safe summaries, then write PRs or reviewed patches instead of silently publishing private memory.

## Object Type Routing

| Object type | Example | Authoritative storage | Collaboration storage | Public surface |
| --- | --- | --- | --- | --- |
| `lesson-event` | Daily lessons produced by a task using a specific runtime or meta Skill | Private memory wiki or local/server log keyed by `skill_id`, `skill_type`, `task_id`, and date | Private PR into `runtime/memory/working-lessons/` or the relevant runtime Skill lesson queue | Only promoted, redacted lessons or stable patterns after IPO Reverse and owner alignment |
| `skill-run` | A runtime skill execution, such as Hermes GitHub `SnapAF-skills` work | Runtime skill repo logs, private memory, or task system | Run summary and issue/PR links in private memory | Public only if task output is public-safe |
| `distilled-pattern` | A repeated lesson that changes how a capability should behave | Capability repo or `capabilities/<capability-id>/memory/` patterns | PR against the capability repo with evidence pointers | Public if the pattern contains no private source facts |
| `skill-upgrade-candidate` | Proposed upgrade from runtime evidence to distilled meta skill behavior | IPO Reverse output plus alignment notes | Private review queue targeting the meta skill repo | Public only after owner alignment and redaction |
| `source-artifact` | Large PDFs, books, reports, slide decks, exported docs | Content-addressed object store, local vault, private Drive, private wiki, or server path | Metadata card plus extraction notes in private memory; raw file stays outside the public repo | Bibliographic metadata, hash, approved abstract, or redacted citation only |
| `thought-fragment` | Daily thinking, quick notes, voice memo summaries, unprocessed ideas | Private inbox, local vault, Feishu/Lark export, or server wiki | Append-only intake queue, then triage into area indexes or lessons | Nothing by default; may become approved summary or pattern after synthesis |
| `area-index` | Work/project/knowledge/life entrypoint | `identity/memories/START-HERE.md` plus private wiki area index | Private wiki updates or owner-reviewed extracts | Public-safe area names, access boundaries, and no source bodies |
| `long-term-memory` | Stable declarative facts, preferences, decisions, and durable constraints | `identity/memories/long-term/` or private memory wiki | Private PR or owner-approved extracted summaries | Approved facts, redacted summaries, or abstracted conclusions only |
| `distilled-knowledge` | Compiled claims with evidence, freshness, and contradiction tracking | `capabilities/*/memory/` or memory wiki claim pages | Private wiki updates or owner-reviewed claim edits | Public-safe claims with evidence pointers only |

Daily lessons should not be written directly into a public Skill as raw chronology. Treat them as evidence events first. Runtime-skill lessons may fix that runtime skill directly. Upgrades into distilled meta skill behavior require IPO Reverse plus owner alignment, with a pointer back to the private evidence when needed.

Large artifacts should not be copied into Git unless the repo is private and intentionally uses a large-file strategy. The default is a pointer card with `artifact_id`, `uri_or_path`, `sha256`, `visibility`, `authority`, `extraction_state`, `summary_visibility`, and `allowed_use`.

Thought fragments are not stable facts. Store them as intake with minimal metadata, then periodically triage them into lessons, project context, area indexes, PSP evidence, or discard/archive.

Generated LifeOS repos should include `runtime/memory/working-lessons/`, `identity/memories/long-term/`, and `capabilities/*/memory/` as separate write targets. Do not collapse them into a single `MEMORY.md`-style file unless emitting a compatibility view.

## Default Generated Repo Rule

Generated LifeOS repos should default to:

- `memory_repo_visibility: private`.
- `memory_public_mirror: index-only`.
- `memory_collaboration_policy: private-pr-or-owner-approved-extract`.
- `memory_raw_material_policy: never-copy-raw-private-bodies`.
- `memory_allowed_public_exports: approved-facts, redacted-summaries, abstracted-patterns`.
