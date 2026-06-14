from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from migrate_lifeos_schema import HEAD_REVISION, infer_current_revision, migrate_to_revision  # noqa: E402


V3_GOVERNED_PATHS = [
    "CATALOG.md",
    "sources/CATALOG.md",
    "sources/authority.yml",
    "sources/raw/README.md",
    "sources/processed/README.md",
    "sources/indexes/README.md",
    "sources/packets/README.md",
    "taste/README.md",
    "taste/current.yml",
    "taste/text/README.md",
    "taste/image/README.md",
    "taste/interface/README.md",
    "taste/brand/README.md",
    "taste/references/README.md",
    "meta-skills/README.md",
    "meta-skills/current.yml",
    "meta-skills/skills/README.md",
    "meta-skills/candidates/README.md",
    "publication/README.md",
    "publication/current.yml",
    "publication/profile/README.md",
    "publication/bio/README.md",
    "publication/positioning/README.md",
    "publication/website/README.md",
    "publication/media-kit/README.md",
    "publication/talks/README.md",
    "publication/articles/README.md",
    "publication/public-claims.yml",
    "governance/README.md",
    "governance/schemas/README.md",
    "governance/policies/README.md",
    "governance/decisions/README.md",
]


class LifeOSSchemaV3GovernedRepoTest(unittest.TestCase):
    def test_fresh_init_renders_v3_governed_layers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "Example.LifeOS"
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "init_avatar_repo.py"),
                    str(target),
                    "--owner-name",
                    "Example Owner",
                    "--display-name",
                    "Example Owner",
                    "--person-id",
                    "example-owner",
                    "--skip-self-evolution-skill-install",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            for rel in V3_GOVERNED_PATHS:
                self.assertTrue((target / rel).exists(), rel)
            status = (target / "LIFEOS_STATUS.yml").read_text(encoding="utf-8")
            self.assertIn("lifeos_schema: v3", status)
            self.assertIn("schema_revision: 0005_lifeos_schema_v3_governed_artifact_repo", status)
            artifacts = (target / "artifacts/current.yml").read_text(encoding="utf-8")
            self.assertIn("sources:", artifacts)
            self.assertIn("taste:", artifacts)
            self.assertIn("meta_skills:", artifacts)
            self.assertIn("publication:", artifacts)
            readme = (target / "README.md").read_text(encoding="utf-8")
            self.assertIn("## 用户先看这里", readme)
            self.assertIn("## 结构怎么读", readme)
            catalog = (target / "CATALOG.md").read_text(encoding="utf-8")
            self.assertIn("Start here.", catalog)
            self.assertIn("## User-Facing Maps", catalog)

    def test_latest_migration_adds_v3_governed_layers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "legacy").mkdir()
            (root / "matrix.yml").write_text("language: zh-CN\nroot_agent:\n  entrypoint: AGENT.md\n", encoding="utf-8")
            (root / "AGENT.md").write_text("# Agent\n", encoding="utf-8")
            (root / "LIFEOS_STATUS.yml").write_text(
                "schema: openlifeos.lifecycle-status.v1\n"
                "lifeos_schema: v2\n"
                "schema_revision: 0004_root_agent_entrypoint\n",
                encoding="utf-8",
            )

            report = migrate_to_revision(root, "latest")

            self.assertEqual(HEAD_REVISION, "0005_lifeos_schema_v3_governed_artifact_repo")
            self.assertEqual(report["to_revision"], "0005_lifeos_schema_v3_governed_artifact_repo")
            self.assertEqual(report["applied_revisions"], ["0005_lifeos_schema_v3_governed_artifact_repo"])
            self.assertEqual(infer_current_revision(root), "0005_lifeos_schema_v3_governed_artifact_repo")
            for rel in V3_GOVERNED_PATHS:
                self.assertTrue((root / rel).exists(), rel)
            self.assertIn("lifeos_schema: v3", (root / "LIFEOS_STATUS.yml").read_text(encoding="utf-8"))
            self.assertIn("Start here.", (root / "CATALOG.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
