# Anthony Structured LifeOS Artifacts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert AnthonyHF Wenxin and PSP current outputs into structured HTML/XML artifacts, and add scenario-map catalog HTML pages for the Engineering Everything and Public Narrative System meta skills.

**Architecture:** Keep Markdown files as legacy evidence sources, but make HTML the human-facing structured entrypoint and XML the machine-facing structured entrypoint. Add skill catalogs beside the relevant meta skill implementations so each skill can be read as a scenario map without opening every reference file.

**Tech Stack:** Static HTML, XML, existing openLifeOS registry YAML files, existing AnthonyHF.LifeOS artifact directories.

---

### Task 1: Plan and Scope Record

**Files:**
- Create: `docs/superpowers/plans/2026-06-02-anthony-structured-lifeos-artifacts.md`

- [ ] Create this implementation plan so the artifact shape, touched files, and verification gates are explicit.

### Task 2: Wenxin Structured Artifacts

**Files:**
- Create: `output/meta/AnthonyHF.LifeOS/identity/wenxin/WENXIN_REPORT.html`
- Create: `output/meta/AnthonyHF.LifeOS/identity/wenxin/WENXIN_REPORT.xml`

- [ ] Convert the current Wenxin wrapper into a hierarchical human-facing HTML document.
- [ ] Convert the same content into XML with source inventory, positioning, coverage map, gaps, future paths, and skill recommendations.

### Task 3: PSP Structured Artifacts

**Files:**
- Create: `output/meta/AnthonyHF.LifeOS/identity/psp/anthony-fan/PSP.html`
- Create: `output/meta/AnthonyHF.LifeOS/identity/psp/anthony-fan/PSP.xml`

- [ ] Convert the current PSP into a hierarchical human-facing HTML document.
- [ ] Convert the same content into XML covering metadata, material sufficiency, kernel layer, cognition layer, behavior boundaries, and unsupported areas.

### Task 4: Meta Skill Scenario Catalogs

**Files:**
- Create: `output/meta/AnthonyHF.LifeOS/skills/engineering-everything/SKILLS-CATALOG.html`
- Create: `output/meta/AnthonyHF.LifeOS/skills/content/public-narrative-system/SKILLS-CATALOG.html`

- [ ] Add an Engineering Everything catalog organized by lifecycle, architecture, execution, validation, organization, and learning scenarios.
- [ ] Add a Public Narrative System catalog organized by intake, identity, series, product narrative, channel packaging, risk review, and publishing feedback scenarios.

### Task 5: Registry Updates and Verification

**Files:**
- Modify: `output/meta/AnthonyHF.LifeOS/artifacts/current.yml`
- Modify: `output/meta/AnthonyHF.LifeOS/identity/current.yml`
- Modify: `output/meta/AnthonyHF.LifeOS/identity/wenxin/versions.yml`
- Modify: `output/meta/AnthonyHF.LifeOS/identity/wenxin/changelog.md`
- Modify: `output/meta/AnthonyHF.LifeOS/identity/psp/anthony-fan/current.yml`
- Modify: `output/meta/AnthonyHF.LifeOS/identity/psp/anthony-fan/versions.yml`
- Modify: `output/meta/AnthonyHF.LifeOS/identity/psp/anthony-fan/changelog.md`

- [ ] Register HTML as the current structured human entrypoint and XML as the machine entrypoint.
- [ ] Keep Markdown paths under `legacy_markdown_source` so historical evidence remains traceable.
- [ ] Verify HTML/XML files parse or at least pass basic file existence and tag checks.
