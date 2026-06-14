"""LifeOS schema v3 governed artifact repository skeleton."""

from __future__ import annotations


STRUCTURAL_MOVES: dict[str, str] = {}

TEXT_REWRITES: dict[str, str] = {
    "schemas/lifeos.schema.v2.yml": "schemas/lifeos.schema.v3.yml",
    "LifeOS schema v2": "LifeOS schema v3",
    "lifeos.schema.v2": "lifeos.schema.v3",
}

V3_SKELETON_FILES: dict[str, str] = {
    "CATALOG.md": """# LifeOS Catalog

Start here. 先看这里。This file explains how to read this governed LifeOS repository without understanding every directory first.

## Read Order｜阅读顺序

1. `LIFEOS_STATUS.yml` - schema revision、lifecycle mode、delivery/development 状态。
2. `artifacts/current.yml` - 当前 active artifacts 和 current entrypoints。
3. `identity/avatar-description/current.yml` - 给用户、UI 和 runtime handbook 读取的当前分身摘要。
4. `sources/CATALOG.md` 和 `sources/authority.yml` - source authority、visibility、材料边界。
5. `identity/`、`taste/`、`runtime/`、`publication/`、`meta-skills/`、`capabilities/` - 治理后的语义产物和成长证据。

## User-Facing Maps｜用户视角地图

| 用户问题 / Question | Path | Meaning |
| --- | --- | --- |
| 当前状态是什么？ | `LIFEOS_STATUS.yml`, `docs/evidence-sufficiency.md` | 结构状态、lifecycle mode、证据成熟度和已知缺口。 |
| 当前数字分身是什么样？ | `identity/avatar-description/current.yml` | 从 active InnerAtlas、PSP、taste artifacts 派生的 product-facing summary。 |
| 哪些证据可以用？ | `sources/authority.yml`, `sources/packets/` | Source authority 和 organ input packets。 |
| 身份/person model 结论在哪里？ | `identity/inneratlas/`, `identity/psp/` | InnerAtlas 负责自我发现；PSP 负责 person model。 |
| 审美和表达偏好在哪里？ | `taste/current.yml`, `DESIGN.md` | v3 taste 入口和兼容投影。 |
| LifeOS 是否真的活着？ | `runtime/sessions/` | 真实 sessions、task outputs、失败、反馈和 lessons。 |
| 哪些内容可以公开？ | `publication/current.yml`, `publication/public-claims.yml`, `security/` | 公开投影和 public claim evidence。 |
| 哪些能力已经稳定？ | `meta-skills/`, `capabilities/` | 经过 review 和 owner alignment 的稳定 skills/capabilities。 |

## Boundary｜边界

Raw materials and tags do not directly write identity, PSP, taste, meta-skill, or publication artifacts. 原始材料和标签不能直接写人格、PSP、taste、Meta Skill 或公开表达结论。它们先生成 `sources/packets/` 下的 evidence packets；`evolution/organ-systems/` 中的 organ systems 负责语义生成，并在激活产物时同步更新 registries。
""",
    "sources/CATALOG.md": """# Sources Catalog

`sources/` is the truth-source and material routing layer. 它回答：有哪些材料、谁授权、材料在哪里、哪些 organ systems 可以使用。

| Area | Purpose / 用途 | Boundary / 边界 |
| --- | --- | --- |
| `raw/` | 授权原始材料暂存；raw 留在外部系统时可以为空。 | 默认 local-only；没有 owner 明确授权不要存私密正文。 |
| `processed/` | 可重建的 transcript、processed Markdown 和 normalized document view。 | 只是 evidence view，不是最终 LifeOS 结论。 |
| `indexes/` | source IDs、hash、外部路径、权限和 tag database snapshot。 | 只放 metadata 和 pointer。 |
| `packets/` | 给 InnerAtlas、PSP、Taste Generator、IPO Reverse 的 organ input packets。 | 这是材料处理和语义生成的边界。 |

This layer records evidence and routing. It does not generate identity conclusions, PSP claims, taste models, meta skills, or public claims. `identity/`、`taste/`、`meta-skills/`、`publication/` 的结论只能由对应 organ / review flow 生成。
""",
    "sources/authority.yml": """schema: openlifeos.source-authority.v1
authority_rule: raw and processed materials are evidence sources, not semantic conclusions
default_visibility: local-only
raw_material_policy:
  store_raw_in_repo: false
  allowed_when: explicit owner approval and local-only visibility
organ_packet_policy:
  inneratlas: sources/packets/inneratlas/
  psp: sources/packets/psp/
  taste_generator: sources/packets/taste-generator/
  ipo_reverse: sources/packets/ipo-reverse/
""",
    "sources/raw/README.md": "# Raw Sources\n\nAuthorized raw material staging. Default is local-only and can remain empty when raw material stays in external systems.\n",
    "sources/processed/README.md": "# Processed Sources\n\nProcessed Markdown, transcript, and normalized document outputs. These files are rebuildable evidence views, not final LifeOS conclusions.\n",
    "sources/indexes/README.md": "# Source Indexes\n\nSource IDs, content hashes, external pointers, visibility, tag database snapshots, and authority metadata.\n",
    "sources/packets/README.md": "# Organ Input Packets\n\nEvidence packets prepared for InnerAtlas, PSP, Taste Generator, and IPO Reverse. Organ systems own semantic generation after this boundary.\n",
    "taste/README.md": "# Taste\n\nGoverned taste system covering text, image, interface, and brand expression. `DESIGN.md` and `identity/design/current/DESIGN_TASTE.xml` remain compatibility projections.\n",
    "taste/current.yml": """schema: openlifeos.taste-current.v1
status: scaffold
current_entrypoints:
  text: taste/text/README.md
  image: taste/image/README.md
  interface: taste/interface/README.md
  brand: taste/brand/README.md
compatibility:
  design_markdown: DESIGN.md
  design_taste_xml: identity/design/current/DESIGN_TASTE.xml
""",
    "taste/text/README.md": "# Text Taste\n\nWriting taste, tone, rhythm, vocabulary, structure, and expression preferences.\n",
    "taste/image/README.md": "# Image Taste\n\nImage taste, composition, visual references, photography or illustration preferences, color, texture, and anti-preferences.\n",
    "taste/interface/README.md": "# Interface Taste\n\nInterface taste, information density, navigation, interaction, component, motion, and usability preferences.\n",
    "taste/brand/README.md": "# Brand Taste\n\nPersonal or organizational brand expression variables and public-facing style constraints.\n",
    "taste/references/README.md": "# Taste References\n\nLike, maybe, avoid, and anti-preference evidence indexes used by Taste Generator.\n",
    "meta-skills/README.md": "# Meta Skills\n\nGoverned owner-grown Meta Skills. Stable skills live in `skills/`; unpromoted candidates live in `candidates/`.\n",
    "meta-skills/current.yml": """schema: openlifeos.meta-skills-current.v1
status: scaffold
stable_skills: []
candidates: []
promotion_gate: IPO Reverse evidence plus owner alignment
""",
    "meta-skills/skills/README.md": "# Stable Meta Skills\n\nStable reusable judgment, routing, methodology, and review-gate skills after promotion.\n",
    "meta-skills/candidates/README.md": "# Meta Skill Candidates\n\nCandidate Meta Skills before IPO Reverse, evidence binding, and owner alignment.\n",
    "publication/README.md": "# Publication\n\nPublic-facing projections generated from governed identity, PSP, taste, meta-skill, and source evidence.\n",
    "publication/current.yml": """schema: openlifeos.publication-current.v1
status: scaffold
entrypoints:
  profile: publication/profile/
  bio: publication/bio/
  positioning: publication/positioning/
  website: publication/website/
  media_kit: publication/media-kit/
  public_claims: publication/public-claims.yml
""",
    "publication/profile/README.md": "# Publication Profile\n\nApproved public profile projections.\n",
    "publication/bio/README.md": "# Publication Bio\n\nApproved short, medium, and long biography projections.\n",
    "publication/positioning/README.md": "# Publication Positioning\n\nApproved public positioning, audience, and offer narratives.\n",
    "publication/website/README.md": "# Publication Website\n\nWebsite copy, structure, and public presentation artifacts.\n",
    "publication/media-kit/README.md": "# Media Kit\n\nPublic media kit, headshots, logos, bios, and speaking material pointers.\n",
    "publication/talks/README.md": "# Talks\n\nPublic talks, outlines, abstracts, and approved speaker material.\n",
    "publication/articles/README.md": "# Articles\n\nPublic articles, drafts, and publication indexes.\n",
    "publication/public-claims.yml": """schema: openlifeos.public-claims.v1
claims: []
rule: every public claim must point to approved evidence or a governed organ artifact
""",
    "governance/README.md": "# Governance\n\nInstance-level schemas, policies, decisions, and changelog pointers for this LifeOS.\n",
    "governance/schemas/README.md": "# Governance Schemas\n\nInstance-level schema snapshots or overrides. Factory schemas remain in the openLifeOS root repo.\n",
    "governance/policies/README.md": "# Governance Policies\n\nInstance-level publication, memory, source, promotion, and review policies.\n",
    "governance/decisions/README.md": "# Governance Decisions\n\nArchitecture and governance decisions for this LifeOS instance.\n",
}

V3_ARTIFACT_SECTIONS = """  sources:
    semantic_role: source_authority_catalog
    answers: "Which raw, processed, indexed, and packetized evidence sources are authoritative, visible, and allowed for organ systems?"
    current_entrypoint: sources/CATALOG.md
    active_artifact: sources/authority.yml
    status: scaffold
    evidence_sufficiency: insufficient
  taste:
    semantic_role: governed_taste_system
    answers: "What text, image, interface, and brand taste model is currently active?"
    current_entrypoint: taste/current.yml
    active_artifact: taste/current.yml
    status: scaffold
    evidence_sufficiency: insufficient
    compatibility_entrypoints:
      - DESIGN.md
      - identity/design/current/DESIGN_TASTE.xml
  meta_skills:
    semantic_role: governed_meta_skill_registry
    answers: "Which owner-grown Meta Skills are stable, which are candidates, and what promotion evidence is required?"
    current_entrypoint: meta-skills/current.yml
    active_artifact: meta-skills/current.yml
    status: scaffold
    evidence_sufficiency: insufficient
  publication:
    semantic_role: public_expression_registry
    answers: "Which public-facing profile, bio, positioning, website, media, talk, article, and claim projections are active?"
    current_entrypoint: publication/current.yml
    active_artifact: publication/current.yml
    status: scaffold
    evidence_sufficiency: insufficient
    public_claims: publication/public-claims.yml
"""
