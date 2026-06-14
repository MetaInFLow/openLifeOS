# LifeOS Lifecycle Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a lifecycle architecture model where sessions are the source of digital-life growth, then adapt the AnthonyHF sample and doctor output to that model.

**Architecture:** Keep the existing initialization gates as scaffold/protocol readiness, and add a separate lifecycle diagnosis that reports which Stage 0-8 state a LifeOS currently occupies. Generated repos get durable first-class layers for intake, runtime, evolution, capabilities, roles, and work while existing memory/skills/cognition paths remain compatibility and governance surfaces.

**Tech Stack:** Markdown architecture docs, avatar template files, Python doctor script, Python unittest.

---

### Task 1: Doctor Lifecycle Diagnosis

**Files:**
- Modify: `scripts/doctor_avatar_repo.py`
- Create: `tests/test_doctor_avatar_repo.py`

- [ ] Write a failing test asserting `to_json(run_doctor(root))` contains `life_stage.stage_id`, `life_stage.stage_name`, `life_stage.age_days`, `life_stage.age_label`, and `life_stage.stage_reason`.
- [ ] Run `python -m unittest tests.test_doctor_avatar_repo -v` and confirm it fails because `life_stage` is missing.
- [ ] Add lifecycle diagnosis helpers that infer the stage from lifecycle directories and current artifacts.
- [ ] Set the AnthonyHF sample start date to `2026-04-02` by default through `LIFEOS_STATUS.yml`, producing a fake age of about two months on `2026-06-02`.
- [ ] Re-run `python -m unittest tests.test_doctor_avatar_repo -v` and confirm it passes.

### Task 2: Lifecycle Architecture Documents

**Files:**
- Create: `docs/architecture/lifeos-lifecycle.md`
- Modify: `references/avatar-repo-blueprint.md`
- Modify: `references/configuration-order.md`
- Modify: `SKILL.md`
- Modify: `README.md`

- [ ] Document Stage 0-8 as the digital-life lifecycle, separate from initialization gates.
- [ ] Define canonical data flow: `intake -> runtime/sessions -> runtime-skills/runtime-lessons -> evolution/ipo -> capabilities`.
- [ ] Update the generated repo contract to include `identity`, `evolution`, `capabilities`, `roles`, `work`, `runtime`, and `intake`.
- [ ] State that doctor reports both scaffold progress and lifecycle stage.

### Task 3: Template And AnthonyHF Structure

**Files:**
- Create lifecycle README templates under `assets/avatar-skill-template/` and `assets/avatar-skill-template-en/`.
- Modify: `assets/avatar-skill-template/matrix.yml.tmpl`
- Modify: `assets/avatar-skill-template-en/matrix.yml.tmpl`
- Add matching README files under `output/meta/AnthonyHF.LifeOS/`.

- [ ] Add README templates for `intake`, `runtime`, `runtime/sessions`, `runtime/runtime-skills`, `runtime/runtime-lessons`, `evolution`, `evolution/ipo`, `capabilities`, `roles`, and `work`.
- [ ] Add the new lifecycle layers to both Chinese and English matrix templates.
- [ ] Add the same directories to AnthonyHF with public-safe README/index files.

### Task 4: Verification

**Files:**
- Modify only files required by Tasks 1-3.

- [ ] Run `python -m unittest tests.test_doctor_avatar_repo -v`.
- [ ] Run `python scripts/doctor_avatar_repo.py output/meta/AnthonyHF.LifeOS --json`.
- [ ] Run `python scripts/openlifeos_progress.py output/meta/AnthonyHF.LifeOS --json`.
- [ ] Inspect `git status --short` and confirm changes match this plan.
