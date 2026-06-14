from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from apply_avatar_config import write_memory_config  # noqa: E402


class ApplyAvatarConfigTest(unittest.TestCase):
    def test_write_memory_config_uses_identity_memories_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "identity" / "memories").mkdir(parents=True)

            write_memory_config(
                root,
                {
                    "language": "zh-CN",
                    "github_owner": "MetaInFlow",
                    "memory_repo_name": "Example.wiki",
                    "memory_repo_visibility": "private",
                    "memory_repo_path": "identity/memories/example-wiki",
                    "wiki_authoritative_source": "github",
                    "wiki_sync_modes": "github",
                    "memory_access_policy": "private-by-default",
                    "memory_public_mirror": "index-only",
                },
            )

            memory_config = root / "identity" / "memories" / "wiki-repo.yml"
            self.assertTrue(memory_config.exists())
            self.assertIn("repository: Example.wiki", memory_config.read_text(encoding="utf-8"))
            self.assertFalse((root / "memory").exists())


if __name__ == "__main__":
    unittest.main()
