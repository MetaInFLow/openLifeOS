from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from migrate_lifeos_schema import migrate_v2_refine_living_fs  # noqa: E402


class LifeOSSchemaV2RefinementMigrationTest(unittest.TestCase):
    def write_schema_0002_repo(self, root: Path) -> None:
        for rel in [
            "skills/engineering-everything",
            "skills/content/public-narrative-system",
            "skills/self-evolution/wenxin",
            "skills/self-evolution/psp",
            "skills/self-evolution/ipo-reverse",
            "skills/self-evolution/cognitive-alignment",
            "memory/working-lessons",
            "memory/long-term",
            "memory/distilled-knowledge",
            "cognition/skill-bindings",
            "intake",
            "roles",
            "capabilities",
            "evolution",
            "identity",
            "runtime",
            "legacy",
        ]:
            (root / rel).mkdir(parents=True, exist_ok=True)
        (root / "LIFEOS_STATUS.yml").write_text(
            "schema: openlifeos.lifecycle-status.v1\nlifeos_schema: v2\nschema_revision: 0002_lifeos_schema_v2\n",
            encoding="utf-8",
        )
        (root / "skills/engineering-everything/SKILL.md").write_text("# Engineering\n", encoding="utf-8")
        (root / "skills/content/public-narrative-system/SKILL.md").write_text("# Narrative\n", encoding="utf-8")
        for name in ["wenxin", "psp", "ipo-reverse", "cognitive-alignment"]:
            (root / f"skills/self-evolution/{name}/SKILL.md").write_text(f"# {name}\n", encoding="utf-8")
        (root / "skills/README.md").write_text("# skills v1\n", encoding="utf-8")
        (root / "memory/START-HERE.md").write_text("# memory\n", encoding="utf-8")
        (root / "memory/wiki-repo.yml").write_text("repo: memory\n", encoding="utf-8")
        (root / "memory/working-lessons/README.md").write_text("# working\n", encoding="utf-8")
        (root / "memory/long-term/README.md").write_text("# long\n", encoding="utf-8")
        (root / "memory/distilled-knowledge/README.md").write_text("# distilled\n", encoding="utf-8")
        (root / "cognition/object-taxonomy.yml").write_text("taxonomy: true\n", encoding="utf-8")
        (root / "cognition/data-contracts.yml").write_text("contracts: true\n", encoding="utf-8")
        (root / "cognition/skill-bindings/data-sources.yml").write_text("bindings: true\n", encoding="utf-8")
        (root / "intake/README.md").write_text("# intake\n", encoding="utf-8")
        (root / "roles/index.md").write_text("# roles\n", encoding="utf-8")
        (root / "matrix.yml").write_text(
            "path: skills/engineering-everything/SKILL.md\nmemory: memory/START-HERE.md\nrole_path: roles/index.md\n",
            encoding="utf-8",
        )

    def test_refinement_removes_conflicting_top_level_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_schema_0002_repo(root)

            report = migrate_v2_refine_living_fs(root)

            self.assertEqual(report["revision"], "0003_lifeos_schema_v2_refine_living_fs")
            self.assertTrue((root / "capabilities/engineering-everything/SKILL.md").exists())
            self.assertTrue((root / "capabilities/publication/public-narrative-system/SKILL.md").exists())
            self.assertTrue((root / "evolution/organ-systems/wenxin/SKILL.md").exists())
            self.assertTrue((root / "evolution/organ-systems/psp/SKILL.md").exists())
            self.assertTrue((root / "evolution/organ-systems/ipo-reverse/SKILL.md").exists())
            self.assertTrue((root / "evolution/organ-systems/cognitive-alignment/SKILL.md").exists())
            self.assertTrue((root / "identity/memories/START-HERE.md").exists())
            self.assertTrue((root / "identity/memories/long-term/README.md").exists())
            self.assertTrue((root / "runtime/memory/working-lessons/README.md").exists())
            self.assertTrue((root / "capabilities/memory/distilled-knowledge/README.md").exists())
            self.assertTrue((root / "identity/cognition/object-taxonomy.yml").exists())
            self.assertTrue((root / "identity/cognition/skill-bindings/data-sources.yml").exists())
            self.assertTrue((root / "metabolism/inbox/README.md").exists())
            self.assertTrue((root / "metabolism/processing/README.md").exists())
            self.assertTrue((root / "metabolism/extracted/README.md").exists())
            self.assertTrue((root / "runtime/runtime-profile/README.md").exists())
            self.assertTrue((root / "evolution/alignment/README.md").exists())
            self.assertTrue((root / "evolution/mutations/README.md").exists())
            self.assertFalse((root / "identity/soul/README.md").exists())
            self.assertTrue((root / "identities/index.md").exists())
            self.assertTrue((root / "legacy/skills-v1/README.md").exists())
            self.assertFalse((root / "skills").exists())
            self.assertFalse((root / "memory").exists())
            self.assertFalse((root / "cognition").exists())
            self.assertFalse((root / "intake").exists())
            self.assertFalse((root / "roles").exists())
            self.assertIn(
                "capabilities/engineering-everything/SKILL.md",
                (root / "matrix.yml").read_text(encoding="utf-8"),
            )
            self.assertIn("identity/memories/START-HERE.md", (root / "matrix.yml").read_text(encoding="utf-8"))
            self.assertIn("identities/index.md", (root / "matrix.yml").read_text(encoding="utf-8"))
            self.assertIn("schema_revision: 0003_lifeos_schema_v2_refine_living_fs", (root / "LIFEOS_STATUS.yml").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
