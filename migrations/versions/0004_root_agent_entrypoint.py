"""Switch generated LifeOS repos from root SKILL.md to AGENT.md.

Revision ID: 0004_root_agent_entrypoint
Revises: 0003_lifeos_schema_v2_refine_living_fs
"""

REVISION = "0004_root_agent_entrypoint"
DOWN_REVISION = "0003_lifeos_schema_v2_refine_living_fs"

STRUCTURAL_MOVES = {}

TEXT_REWRITES = {
    "root_skill:": "root_agent:",
    "entrypoint: SKILL.md": "entrypoint: AGENT.md",
    "identity/memories/index, SKILL.md": "identity/memories/index, AGENT.md",
    "identity/memories/index, `SKILL.md`": "identity/memories/index, `AGENT.md`",
    "targets: identity/wenxin, identity/psp, identity/wenxin/skill-recommendations, identity/memories/index, SKILL.md": "targets: identity/wenxin, identity/psp, identity/wenxin/skill-recommendations, identity/memories/index, AGENT.md",
    "先读 `SKILL.md` 和 `artifacts/current.yml`": "先读 `AGENT.md` 和 `artifacts/current.yml`",
    "Read `SKILL.md` and `artifacts/current.yml`": "Read `AGENT.md` and `artifacts/current.yml`",
    "root `SKILL.md`": "root `AGENT.md`",
    "root SKILL.md": "root AGENT.md",
    "Root SKILL.md": "Root AGENT.md",
    "根 `SKILL.md`": "根 `AGENT.md`",
    "根 SKILL": "根 AGENT.md",
    "本 `SKILL.md`": "本 `AGENT.md`",
    "this `SKILL.md`": "this `AGENT.md`",
    "根路由规则": "根 agent 读取和路由规则",
    "openLifeOS Skill 入口": "openLifeOS avatar agent 入口",
    "This is the Skill entrypoint": "This is the agent entrypoint",
    "SKILL 引导": "`AGENT.md` 引导",
    "SKILL-guided": "AGENT/Skill-guided",
    "generated root `SKILL.md`": "generated root `AGENT.md`",
    "generated root SKILL.md": "generated root AGENT.md",
}
