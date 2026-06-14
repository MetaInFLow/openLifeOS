"""LifeOS schema v2 structural migration.

Revision ID: 0002_lifeos_schema_v2
Revises: 0001_openlifeos_base
"""

REVISION = "0002_lifeos_schema_v2"
DOWN_REVISION = "0001_openlifeos_base"

STRUCTURAL_MOVES = {
    "agents": "integrations/agents",
    "apps": "work/apps",
    "profiles": "runtime/profiles",
    "scripts": "legacy/scripts",
    "design": "identity/design",
    "life": "legacy/navigation-v1/life",
    "system": "legacy/navigation-v1/system",
}

TEXT_REWRITES = {
    "design/": "identity/design/",
    "profiles/": "runtime/profiles/",
    "apps/": "work/apps/",
    "agents/": "integrations/agents/",
}
