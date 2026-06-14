from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_avatar_repo import (  # noqa: E402
    validate_artifact_registry_roles,
    validate_avatar_description,
    validate_avatar_description_claim_approval_contract,
)
from evaluate_avatar_description import evaluate_avatar_description  # noqa: E402


class AvatarDescriptionValidationTest(unittest.TestCase):
    def test_requires_structured_avatar_description_and_claim_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "artifacts").mkdir()
            (root / "identity" / "avatar-description").mkdir(parents=True)
            (root / "artifacts" / "current.yml").write_text(
                "\n".join(
                    [
                        "schema: openlifeos.artifacts-current.v1",
                        "artifacts:",
                        "  avatar_description:",
                        "    semantic_role: product_facing_current_avatar_description",
                        '    answers: "What is this digital avatar currently like?"',
                        "    current_entrypoint: identity/avatar-description/current.yml",
                        "    status: active",
                        "    evidence_sufficiency: partial",
                    ]
                ),
                encoding="utf-8",
            )
            (root / "identity" / "avatar-description" / "current.yml").write_text(
                "\n".join(
                    [
                        "schema: openlifeos.avatar-description.v1",
                        "display_name: Example Person",
                        'one_line: "Example one line."',
                        'current_role: "Example role."',
                        "evidence_level: partial",
                        'maturity_notice: "Structured summary assembled from multiple artifacts, not a single markdown file."',
                        "operating_mode:",
                        '  - "Uses evidence."',
                        "strengths:",
                        '  - "Builds systems."',
                        "boundaries:",
                        '  - "No private claims."',
                        "source_refs:",
                        "  - identity/wenxin/WENXIN_REPORT.md",
                        "claim_evidence:",
                        "  one_line:",
                        "    - identity/wenxin/WENXIN_REPORT.md",
                        "derived_from:",
                        "  - identity/wenxin/WENXIN-20260602.md",
                    ]
                ),
                encoding="utf-8",
            )

            failures: list[str] = []
            validate_avatar_description(root, failures)

        self.assertIn("identity/avatar-description/current.yml missing claim_evidence.current_role", failures)
        self.assertIn("identity/avatar-description/current.yml missing claim_evidence.operating_mode", failures)
        self.assertIn("identity/avatar-description/current.yml missing claim_evidence.strengths", failures)
        self.assertIn("identity/avatar-description/current.yml missing claim_evidence.boundaries", failures)

    def test_artifacts_current_requires_consumer_facing_roles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "artifacts").mkdir()
            (root / "artifacts" / "current.yml").write_text(
                "\n".join(
                    [
                        "schema: openlifeos.artifacts-current.v1",
                        "artifacts:",
                        "  avatar_description:",
                        "    semantic_role: generic_identity_summary",
                        "    current_entrypoint: identity/avatar-description/current.yml",
                        "    status: active",
                        "  wenxin:",
                        "    semantic_role: identity_self_discovery",
                        '    answers: "Who am I and where should I go?"',
                        "    current_entrypoint: identity/wenxin/WENXIN_REPORT.md",
                        "    status: active",
                        "    evidence_sufficiency: partial",
                        "  psp:",
                        "    semantic_role: person_model_source",
                        '    answers: "What behavior model can be inferred?"',
                        "    current_entrypoint: identity/psp/example/current/PSP_REPORT.xml",
                        "    status: partial",
                        "    evidence_sufficiency: partial",
                        "  design:",
                        "    semantic_role: global_aesthetic_system",
                        '    answers: "What taste system should guide output?"',
                        "    current_entrypoint: DESIGN.md",
                        "    status: active",
                        "    evidence_sufficiency: partial",
                        "  skill_recommendations:",
                        "    semantic_role: wenxin_candidate_skill_recommendations",
                        "    current_entrypoint: identity/wenxin/skill-recommendations.yml",
                        "    status: active",
                        "    evidence_sufficiency: partial",
                        "  evidence_maturity:",
                        "    semantic_role: maturity_and_gap_report",
                        "    current_entrypoint: identity/psp/example/current/EVIDENCE_MATURITY.xml",
                        "    status: active",
                        "    evidence_sufficiency: insufficient",
                    ]
                ),
                encoding="utf-8",
            )

            failures: list[str] = []
            validate_artifact_registry_roles(root, failures)
            validate_avatar_description(root, failures)

        self.assertIn("artifacts/current.yml avatar_description missing answers", failures)
        self.assertIn("artifacts/current.yml avatar_description missing evidence_sufficiency", failures)
        self.assertIn("artifacts/current.yml skill_recommendations missing answers", failures)
        self.assertIn("artifacts/current.yml evidence_maturity missing answers", failures)
        self.assertIn(
            "artifacts/current.yml avatar_description semantic_role must be product_facing_current_avatar_description",
            failures,
        )

    def test_data_contract_requires_avatar_description_claim_approval_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "identity" / "cognition").mkdir(parents=True)
            (root / "identity" / "cognition" / "data-contracts.yml").write_text(
                "\n".join(
                    [
                        "version: 1",
                        "owner: Example Owner",
                        "write_order:",
                        "  - capture pointer or event",
                    ]
                ),
                encoding="utf-8",
            )

            failures: list[str] = []
            validate_avatar_description_claim_approval_contract(root, failures)

        self.assertIn(
            "identity/cognition/data-contracts.yml missing avatar description claim approval marker: avatar_description_claim_approval",
            failures,
        )
        self.assertIn(
            "identity/cognition/data-contracts.yml missing avatar description claim approval term: approved_at",
            failures,
        )
        self.assertIn(
            "identity/cognition/data-contracts.yml missing avatar description claim approval term: missing approval metadata fails synthesis",
            failures,
        )

    def test_init_templates_generate_valid_structured_artifact_registry(self) -> None:
        for language in ["zh-CN", "en-US"]:
            with self.subTest(language=language):
                with tempfile.TemporaryDirectory() as tmp:
                    target = Path(tmp) / f"Example-{language}.LifeOS"
                    init = subprocess.run(
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
                            "--language",
                            language,
                            "--skip-self-evolution-skill-install",
                        ],
                        cwd=ROOT,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual(init.returncode, 0, init.stderr + init.stdout)
                    self.assertTrue((target / "AGENT.md").exists())
                    self.assertFalse((target / "SKILL.md").exists())

                    failures: list[str] = []
                    validate_avatar_description(target, failures)
                    validate_artifact_registry_roles(target, failures)
                    validate_avatar_description_claim_approval_contract(target, failures)
                    self.assertEqual(failures, [])
                    eval_result = evaluate_avatar_description(target)
                    self.assertEqual(eval_result["status"], "pass", eval_result["issues"])
                    for skill_name in ["wenxin", "psp", "ipo-reverse", "taste-generator"]:
                        skill_path = target / "evolution" / "organ-systems" / skill_name / "SKILL.md"
                        skill_path.parent.mkdir(parents=True, exist_ok=True)
                        skill_path.write_text(f"# {skill_name}\n", encoding="utf-8")
                    strict = subprocess.run(
                        [
                            sys.executable,
                            str(ROOT / "scripts" / "validate_avatar_repo.py"),
                            str(target),
                            "--strict-v2",
                        ],
                        cwd=ROOT,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual(strict.returncode, 0, strict.stderr + strict.stdout)
                    for legacy_top_level in ["agents", "design", "scripts", "memory", "skills", "cognition", "intake", "roles"]:
                        self.assertFalse((target / legacy_top_level).exists(), legacy_top_level)

                    artifacts = (target / "artifacts" / "current.yml").read_text(encoding="utf-8")
                    data_contracts = (target / "identity" / "cognition" / "data-contracts.yml").read_text(encoding="utf-8")
                    self.assertIn("skill_recommendations:", artifacts)
                    self.assertIn("evidence_maturity:", artifacts)
                    self.assertIn("Which candidate runtime/meta skills are recommended", artifacts)
                    self.assertIn("How mature is the current LifeOS evidence base", artifacts)
                    self.assertIn("avatar_description_claim_approval:", data_contracts)
                    self.assertIn("openlifeos.avatar-description-synthesis.v1", data_contracts)
                    self.assertIn("approval_ref", data_contracts)
                    self.assertIn("missing approval metadata fails synthesis", data_contracts)

    def test_strict_v2_rejects_legacy_top_level_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "LIFEOS_STATUS.yml").write_text("lifeos_schema: v2\n", encoding="utf-8")
            (root / "agents").mkdir()

            strict = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "validate_avatar_repo.py"),
                    str(root),
                    "--strict-v2",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertNotEqual(strict.returncode, 0)
        self.assertIn("Strict LifeOS schema v2 disallows legacy top-level directory: agents", strict.stdout)


if __name__ == "__main__":
    unittest.main()
