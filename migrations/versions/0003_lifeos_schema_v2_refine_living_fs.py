"""Refine LifeOS schema v2 into a living filesystem.

Revision ID: 0003_lifeos_schema_v2_refine_living_fs
Revises: 0002_lifeos_schema_v2
"""

REVISION = "0003_lifeos_schema_v2_refine_living_fs"
DOWN_REVISION = "0002_lifeos_schema_v2"

STRUCTURAL_MOVES = {
    "skills/engineering-everything": "capabilities/engineering-everything",
    "skills/content/public-narrative-system": "capabilities/publication/public-narrative-system",
    "skills/publication": "capabilities/publication",
    "skills/self-evolution/wenxin": "evolution/organ-systems/wenxin",
    "skills/self-evolution/psp": "evolution/organ-systems/psp",
    "skills/self-evolution/ipo-reverse": "evolution/organ-systems/ipo-reverse",
    "skills/self-evolution/cognitive-alignment": "evolution/organ-systems/cognitive-alignment",
    "skills/README.md": "legacy/skills-v1/README.md",
    "skills/SKILLS-CATALOG.html": "legacy/skills-v1/SKILLS-CATALOG.html",
    "memory/START-HERE.md": "identity/memories/START-HERE.md",
    "memory/README.md": "identity/memories/README.md",
    "memory/wiki-repo.yml": "identity/memories/wiki-repo.yml",
    "memory/af-wiki": "identity/memories/af-wiki",
    "memory/long-term": "identity/memories/long-term",
    "memory/working-lessons": "runtime/memory/working-lessons",
    "memory/distilled-knowledge": "capabilities/memory/distilled-knowledge",
    "cognition": "identity/cognition",
    "intake": "metabolism/inbox",
    "roles": "identities",
}

TEXT_REWRITES = {
    "skills/engineering-everything": "capabilities/engineering-everything",
    "skills/content/public-narrative-system": "capabilities/publication/public-narrative-system",
    "skills/self-evolution/wenxin": "evolution/organ-systems/wenxin",
    "skills/self-evolution/psp": "evolution/organ-systems/psp",
    "skills/self-evolution/ipo-reverse": "evolution/organ-systems/ipo-reverse",
    "skills/self-evolution/cognitive-alignment": "evolution/organ-systems/cognitive-alignment",
    "skills/README.md": "legacy/skills-v1/README.md",
    "memory/START-HERE.md": "identity/memories/START-HERE.md",
    "memory/wiki-repo.yml": "identity/memories/wiki-repo.yml",
    "memory/working-lessons/": "runtime/memory/working-lessons/",
    "memory/long-term/": "identity/memories/long-term/",
    "memory/distilled-knowledge/": "capabilities/memory/distilled-knowledge/",
    "cognition/skill-bindings/": "identity/cognition/skill-bindings/",
    "cognition/object-taxonomy.yml": "identity/cognition/object-taxonomy.yml",
    "cognition/data-contracts.yml": "identity/cognition/data-contracts.yml",
    "intake/": "metabolism/inbox/",
    "roles/": "identities/",
}
