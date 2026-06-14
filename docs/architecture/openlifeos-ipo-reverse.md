# openLifeOS Factory IPO Reverse

## 0. Standard Output Gate

```yaml
standard_output_gate:
  artifact_type: ipo-reverse
  evidence_sufficiency: sufficient
  evidence_sources:
    - source_id: openlifeos-root-skill
      source_type: repo_file
      authority: primary
      used_for:
        - factory intent
        - base versus evolved lifecycle boundary
    - source_id: init-avatar-repo
      source_type: repo_file
      authority: primary
      used_for:
        - scaffold process
        - bundled self-evolution skill installation
    - source_id: apply-avatar-config
      source_type: repo_file
      authority: primary
      used_for:
        - boundary wiring process
        - public profile and integration config generation
    - source_id: validate-avatar-repo
      source_type: repo_file
      authority: primary
      used_for:
        - current validation contract
    - source_id: doctor-avatar-repo
      source_type: repo_file
      authority: primary
      used_for:
        - progress gate contract
    - source_id: anthonyhf-lifeos
      source_type: generated_sample
      authority: user-approved
      used_for:
        - evolved sample room comparison
    - source_id: fresh-base-init-20260531
      source_type: local_test_run
      authority: primary
      used_for:
        - positive construction proof
        - gate failure evidence
  missing_information: []
  confidence:
    overall: high
    notes: "The base scaffold was generated in a temp directory and compared against validation/progress gates. The remaining uncertainty is product naming, not technical causality."
```

## 1. Finished Output Reference

The output being reverse-engineered is not only the current `AnthonyHF.LifeOS` sample room. The real finished output should be:

1. A **base LifeOS** that `openLifeOS` can construct deterministically from config and approved installation sources.
2. An **evolved LifeOS** that starts from base, then grows through evidence intake, Wenxin, PSP XML, Design, IPO Reverse, skill recommendations, owner-grown meta skills, memory, and runtime projections. `SOUL.md` is paused as a LifeOS source artifact.

AnthonyHF is an evolved sample room. It should inform the factory, but it must not redefine base init by accident.

## 2. Artifact Evidence Map

| Module | Observable Evidence | Inference | Evidence |
|---|---|---|---|
| Factory intent | Root `SKILL.md` says factory lives at repo root and instances generate under `output/meta/<Target.LifeOS>/` | openLifeOS is a generator and governance repo, not one hardcoded avatar | E1 |
| Base generator | `scripts/init_avatar_repo.py` renders templates, initializes git, installs Wenxin/PSP/IPO Reverse/Taste Generator | Base construction already exists and is executable | E1 |
| Boundary wiring | `scripts/apply_avatar_config.py` writes public profile, memory config, integrations, permissions, and skill recommendations | Base is at least two-stage: scaffold then wiring | E1 |
| Base skill set | `SELF_EVOLUTION_SKILL_REPOS` includes Wenxin, PSP, IPO Reverse, and Taste Generator | Engineering Everything and Cognitive Alignment are not base skills | E1 |
| Current validator | `scripts/validate_avatar_repo.py` requires Engineering Everything, Cognitive Alignment, and Anthony-specific skill summaries | Validator currently encodes evolved-Anthony assumptions | E1 |
| Current progress gate | `scripts/doctor_avatar_repo.py` has the same evolved paths in required skeleton checks | Progress output under-reports fresh base completion | E1 |
| Template placement | Templates now generate `identity/cognition/skill-bindings`, `integrations/skill-sources`, `identity/wenxin/skill-summaries`, and `docs/skill-system` | Template placement has been aligned to the refined LifeOS v2 object taxonomy | E1 |
| Anthony placement | Anthony moved bindings to `identity/cognition/skill-bindings`, skill source manifests to `integrations/skill-sources`, recommendations to `identity/wenxin` | Evolved sample room reveals the desired object taxonomy | E1 |
| Fresh base test | Temp init succeeded, installed Wenxin/PSP/IPO Reverse/Taste Generator, but validator failed on evolved-only paths | Construction works; gate contract is wrong for base | E1 |

## 3. Hidden Cognitive Tasks

| Explicit Work | Hidden Cognitive Task | Chosen Method | Rejected Method |
|---|---|---|---|
| "Base LifeOS 能否构建出来" | Separate deterministic scaffold readiness from content maturity | Two-level lifecycle gate: base and evolved | Single 100% completion score |
| "Anthony 样板间是否可生产" | Distinguish sample-room evidence from factory invariant | Treat Anthony as evolved reference implementation | Copy Anthony-specific skills into init |
| "利用 IPO 反推 openLifeOS" | Recover the production process that should lead from config to LifeOS | IPO Reverse plus forward reconstruction | Ad hoc bug list |
| Skill placement cleanup | Enforce object taxonomy across templates, docs, validators, projections | Canonical path map | Keep legacy paths and patch one script |
| Runtime projections | Decide whether OpenClaw/Hermes output belongs to base | Put projections after synthesis/evolved gate | Generate runtime profiles during init |

## 4. Methodology Selection

| Task | Candidate Methods | Selected | Reason |
|---|---|---|---|
| Validate base constructability | Snapshot diff, schema validation, fresh init test | Fresh init plus gate comparison | Directly proves what factory can construct |
| Define lifecycle | Maturity model, release stages, feature flags | Base/evolved gates | Matches current distinction between scaffold and Anthony sample |
| Fix path drift | Migration script, docs-only note, canonical taxonomy | Canonical taxonomy plus mechanical template/gate alignment | Prevents future divergence |
| Prevent overfitting | Exclusion list, product doctrine, validator modes | Validator modes | Lets Anthony-specific artifacts remain valid without becoming universal |

## 5. Middle-Layer Artifacts Recovered

| Artifact | Recovered Content | Downstream Consumer |
|---|---|---|
| Canonical path map | Defines where identity, cognition, integrations, self-evolution skills, instance skills, and projections live | Templates, validators, translator |
| Base gate checklist | Required files for init + apply + installed self-evolution skills | `validate_avatar_repo.py`, `doctor_avatar_repo.py` |
| Evolved gate checklist | Evidence-backed Wenxin/PSP XML/Design, skill summaries, owner-grown meta skills, projections | `doctor_avatar_repo.py --mode evolved` |
| Promotion rule | Engineering Everything and Cognitive Alignment are allowed evolved meta skills, not base requirements | Skill recommendation and validation logic |
| Forward reconstruction test | Fresh init should pass base validation after apply | CI or local regression test |

## 6. Final IPO

### Input

Required inputs for base construction:

- Target repo path.
- `owner_name`, `display_name`, `identity_mode`, `psp_display_name`, `person_id`.
- `github_owner`, `visibility`, `language`, `process_log_language`.
- Template directory for the selected language.
- GitHub archive access for Wenxin, PSP, IPO Reverse, and Taste Generator, unless skipped.

Required inputs for evolved construction:

- A base LifeOS repo.
- Owner-approved evidence.
- Evidence sufficiency policy.
- Completed outputs to reverse through IPO.
- Owner alignment decisions for skill promotion.
- Runtime target selection, such as Hermes or OpenClaw.

### Process

#### Stage 1: Target and Boundary Config

- Input: target identity, visibility, language, repo path.
- Operation: normalize stable identifiers and write config.
- Output: `replicateme.yml`, target repo path, security defaults.
- Success: no secrets requested or stored.
- Failure signal: identity fields are inferred from private context without owner input.

#### Stage 2: Kernel Scaffold

- Input: config and template directory.
- Operation: render root files, identity scaffolds, PSP XML/Design/Wenxin versioned placeholders, identity/runtime/capability memory layers, integrations, docs, security, evolution organ systems, and capabilities layer.
- Output: base repository tree.
- Success: no unresolved template tokens outside vendored skill templates.
- Failure signal: generated tree contains stale paths or missing current registries.

#### Stage 3: Base Self-Evolution Skill Install

- Input: Wenxin, PSP, IPO Reverse, and Taste Generator GitHub archives.
- Operation: vendor each repo into `evolution/organ-systems/<skill-id>/` with `.openlifeos-skill-source.yml`.
- Output: three concrete `SKILL.md` entrypoints.
- Success: `evolution/organ-systems/{wenxin,psp,ipo-reverse,taste-generator}/SKILL.md` exist.
- Failure signal: init silently leaves only bridge docs where real skills are required.

#### Stage 4: Boundary Wiring

- Input: config.
- Operation: write public profile, memory wiki config, GitHub/Feishu/Hermes integration configs, permissions, and intake-ready skill recommendations.
- Output: base configured LifeOS.
- Success: `public-profile`, `identity/memories/wiki-repo.yml`, `integrations/*.yml`, `security/permissions.yml`, `identity/wenxin/skill-recommendations.yml` exist.
- Failure signal: `apply_avatar_config.py --force` duplicates initial timestamp artifacts without clear version semantics.

#### Stage 5: Base Gate

- Input: configured LifeOS.
- Operation: validate deterministic scaffold only.
- Output: base validation report.
- Success: base gate passes even without Engineering Everything, Cognitive Alignment, skill summaries, evidence-backed PSP, or runtime projections.
- Failure signal: validator asks for Anthony-specific evolved artifacts.

#### Stage 6: Evidence Intake and Synthesis

- Input: owner-approved evidence.
- Operation: update Wenxin, PSP XML, Design, memory index, and skill recommendations according to standard output gates.
- Output: evidence-backed evolved artifacts.
- Success: each artifact records sufficiency, sources, missing information, confidence, versions, and changelog.
- Failure signal: scaffold files are treated as sufficient identity claims.

#### Stage 7: Skill Promotion

- Input: repeated workflow or high-percentile capability evidence.
- Operation: run IPO Reverse and owner alignment; only then promote a candidate into runtime/meta skill.
- Output: instance-local or installable skill with source links and summaries.
- Success: Engineering Everything and Cognitive Alignment can exist in Anthony but are not base requirements.
- Failure signal: recommendation or installed self-evolution tool is mistaken for a user skill.

#### Stage 8: Runtime Projection

- Input: evolved artifacts and target runtime.
- Operation: translate LifeOS into Hermes/OpenClaw profile.
- Output: `profiles/<runtime>/<profile-id>/`.
- Success: profile manifest records source artifacts.
- Failure signal: runtime profile is used as source-of-truth for base structure.

## 7. Forward Reconstruction Check

Starting with only the base inputs:

1. `init_avatar_repo.py` can create the repo and install Wenxin/PSP/IPO Reverse/Taste Generator.
2. `apply_avatar_config.py` can wire profile, memory, integrations, permissions, and recommendations.
3. The generated tree contains root `DESIGN.md`, versioned PSP XML/Wenxin/Design scaffolds, current registries, and memory/security/docs layers. `SOUL.md` is not generated as a LifeOS source artifact.

The reconstruction currently fails at validation, not construction, because the validator/progress gate requires evolved-only artifacts.

## 8. Step Deletion Check

| Removed Step | Effect | Keep? |
|---|---|---|
| Boundary config | Repo can render but cannot safely represent visibility or identity | Keep |
| Kernel scaffold | Nothing meaningful exists | Keep |
| Self-evolution install | Base cannot perform Wenxin/PSP/IPO Reverse/Taste Generator later | Keep |
| Boundary wiring | Base remains unconfigured and integration status stays scaffold | Keep |
| Base gate | Regressions cannot be distinguished from incomplete evidence | Keep |
| Evidence synthesis | Only scaffold exists; no evolved LifeOS | Keep, but non-base |
| Skill promotion | Anthony-grown meta skills cannot be justified | Keep, but non-base |
| Runtime projection | Runtime consumers cannot use evolved output | Keep, but non-base |

## 9. Assumptions And Evidence Ledger

| Assumption | Evidence | Confidence | Impact | Verification |
|---|---|---|---|---|
| Base should include Wenxin, PSP, IPO Reverse, Taste Generator | Root Skill and init script install list | High | Defines base requirements | Fresh init |
| Engineering Everything is evolved-only | User correction plus Anthony history | High | Removes it from base gate | Validator mode update |
| Cognitive Alignment is evolved-only for Anthony unless separately selected | User correction and current init list | High | Removes it from base gate | Validator mode update |
| `identity/cognition/skill-bindings` is preferred over legacy skill-local bindings | Anthony sample and current validator expectations | High | Template migration completed | Fresh init validation |
| `integrations/skill-sources` is preferred over legacy default-skill metadata under top-level `skills/` | Anthony sample and current validator expectations | High | Template migration completed | Fresh init validation |

## 10. Downstream Usage

### Immediate Fix Order

1. Add validator/progress modes: `base` and `evolved`.
2. Make `base` require only deterministic scaffold plus Wenxin/PSP/IPO Reverse/Taste Generator.
3. Keep template placement on the canonical paths used by Anthony: `identity/cognition/skill-bindings`, `integrations/skill-sources`, `identity/wenxin/skill-summaries`, and `docs/skill-system`.
4. Keep root docs and references pointed at `identity/cognition/skill-bindings/data-sources.yml`.
5. Add a regression test: fresh init + apply must pass `validate_avatar_repo.py --mode base`.
6. Keep Engineering Everything and Cognitive Alignment in evolved validation only.
7. Treat runtime projections as evolved outputs generated after synthesis.

### Product Definition

Base LifeOS is the installable kernel.

Evolved LifeOS is the living sample room after evidence, synthesis, owner alignment, and runtime translation.

AnthonyHF should remain the first evolved sample room, not the hidden default template.
