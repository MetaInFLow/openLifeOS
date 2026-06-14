from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from migrate_lifeos_schema import (  # noqa: E402
    infer_current_revision,
    migrate_root_agent_entrypoint,
    migrate_to_revision,
)


class LifeOSRootAgentMigrationTest(unittest.TestCase):
    def write_schema_0003_repo(self, root: Path, explicit_revision: bool = True) -> None:
        for rel in [
            "evolution/organ-systems/wenxin",
            "evolution/organ-systems/psp",
            "evolution/organ-systems/ipo-reverse",
            "identity/memories",
            "identity/cognition/skill-bindings",
            "integrations",
            "legacy",
            "runtime/sessions",
            "capabilities",
            "security",
            "docs",
        ]:
            (root / rel).mkdir(parents=True, exist_ok=True)
        status = "schema: openlifeos.lifecycle-status.v1\nlifeos_schema: v2\n"
        if explicit_revision:
            status += "schema_revision: 0003_lifeos_schema_v2_refine_living_fs\n"
        (root / "LIFEOS_STATUS.yml").write_text(status, encoding="utf-8")
        (root / "SKILL.md").write_text(
            "\n".join(
                [
                    "---",
                    "name: example-lifeos",
                    "description: Example generated root skill.",
                    "---",
                    "",
                    "# Example",
                    "",
                    "这是 Example 的 openLifeOS Skill 入口。",
                    "",
                    "## 信息源顺序",
                    "",
                    "1. **根路由规则**：本文件。",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (root / "matrix.yml").write_text(
            "language: zh-CN\n"
            "root_skill:\n"
            "  id: example-lifeos\n"
            "  path: .\n"
            "  entrypoint: SKILL.md\n",
            encoding="utf-8",
        )
        (root / "integrations" / "hermes.yml").write_text(
            "targets: identity/wenxin, identity/psp, identity/wenxin/skill-recommendations, identity/memories/index, SKILL.md\n",
            encoding="utf-8",
        )
        (root / "README.md").write_text(
            "先读 `SKILL.md` 和 `artifacts/current.yml`。\n",
            encoding="utf-8",
        )

    def test_0004_moves_root_skill_to_agent_and_rewrites_routing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_schema_0003_repo(root)

            report = migrate_root_agent_entrypoint(root)

            self.assertEqual(report["revision"], "0004_root_agent_entrypoint")
            self.assertTrue((root / "AGENT.md").exists())
            self.assertFalse((root / "SKILL.md").exists())
            agent = (root / "AGENT.md").read_text(encoding="utf-8")
            self.assertNotIn("name: example-lifeos", agent)
            self.assertIn("本文件不是可安装 Codex Skill", agent)
            self.assertIn("doctor_avatar_repo.py", agent)
            self.assertIn("skill_content_maturity", agent)
            self.assertIn("EVIDENCE_MATURITY.xml", agent)
            matrix = (root / "matrix.yml").read_text(encoding="utf-8")
            self.assertIn("root_agent:", matrix)
            self.assertIn("entrypoint: AGENT.md", matrix)
            self.assertNotIn("root_skill:", matrix)
            self.assertIn("AGENT.md", (root / "integrations" / "hermes.yml").read_text(encoding="utf-8"))
            self.assertIn("AGENT.md", (root / "README.md").read_text(encoding="utf-8"))
            self.assertIn("schema_revision: 0004_root_agent_entrypoint", (root / "LIFEOS_STATUS.yml").read_text(encoding="utf-8"))
            self.assertTrue((root / "legacy" / "migration-reports" / "0004_root_agent_entrypoint.json").exists())

    def test_latest_upgrade_infers_0003_without_status_revision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_schema_0003_repo(root, explicit_revision=False)

            self.assertEqual(infer_current_revision(root), "0003_lifeos_schema_v2_refine_living_fs")
            report = migrate_to_revision(root, "latest")

            self.assertEqual(report["from_revision"], "0003_lifeos_schema_v2_refine_living_fs")
            self.assertEqual(report["to_revision"], "0005_lifeos_schema_v3_governed_artifact_repo")
            self.assertEqual(
                report["applied_revisions"],
                ["0004_root_agent_entrypoint", "0005_lifeos_schema_v3_governed_artifact_repo"],
            )
            self.assertTrue((root / "AGENT.md").exists())
            self.assertFalse((root / "SKILL.md").exists())
            self.assertTrue((root / "CATALOG.md").exists())
            self.assertTrue((root / "sources" / "CATALOG.md").exists())
            self.assertTrue((root / "taste" / "current.yml").exists())


if __name__ == "__main__":
    unittest.main()
