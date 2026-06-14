from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from migrate_lifeos_schema import migrate_v1_to_v2  # noqa: E402


class LifeOSSchemaMigrationTest(unittest.TestCase):
    def write_v1_repo(self, root: Path) -> None:
        for rel in [
            "agents",
            "apps/homepage",
            "design",
            "profiles/openclaw",
            "scripts",
            "life",
            "system",
            "identity",
            "work",
            "runtime",
            "integrations",
        ]:
            (root / rel).mkdir(parents=True, exist_ok=True)
        (root / "LIFEOS_STATUS.yml").write_text(
            "schema: openlifeos.lifecycle-status.v1\nrepo: Example.LifeOS\n",
            encoding="utf-8",
        )
        (root / "agents/openai.yaml").write_text("name: example\n", encoding="utf-8")
        (root / "apps/homepage/index.html").write_text("<html></html>\n", encoding="utf-8")
        (root / "design/DESIGN-20260602.md").write_text("# Design\n", encoding="utf-8")
        (root / "profiles/openclaw/profile.yml").write_text("id: example\n", encoding="utf-8")
        (root / "scripts/update_default_skills.py").write_text("# script\n", encoding="utf-8")
        (root / "life/README.md").write_text("# old navigation\n", encoding="utf-8")
        (root / "system/README.md").write_text("# old navigation\n", encoding="utf-8")
        (root / "artifacts").mkdir()
        (root / "artifacts/current.yml").write_text(
            "artifacts:\n"
            "  design:\n"
            "    active_artifact: design/DESIGN-20260602.md\n"
            "    versions_ledger: design/versions.yml\n",
            encoding="utf-8",
        )

    def test_v1_to_v2_moves_classified_dirs_and_legacy_navigation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_v1_repo(root)

            report = migrate_v1_to_v2(root)

            self.assertEqual(report["schema_version"], "v2")
            self.assertTrue((root / "integrations/agents/openai.yaml").exists())
            self.assertTrue((root / "work/apps/homepage/index.html").exists())
            self.assertTrue((root / "identity/design/DESIGN-20260602.md").exists())
            self.assertTrue((root / "runtime/profiles/openclaw/profile.yml").exists())
            self.assertTrue((root / "legacy/scripts/update_default_skills.py").exists())
            self.assertTrue((root / "legacy/navigation-v1/life/README.md").exists())
            self.assertTrue((root / "legacy/navigation-v1/system/README.md").exists())
            self.assertFalse((root / "agents").exists())
            self.assertFalse((root / "apps").exists())
            self.assertFalse((root / "design").exists())
            self.assertIn("lifeos_schema: v2", (root / "LIFEOS_STATUS.yml").read_text(encoding="utf-8"))
            self.assertIn("identity/design/DESIGN-20260602.md", (root / "artifacts/current.yml").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
