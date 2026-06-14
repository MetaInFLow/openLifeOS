from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from evaluate_avatar_description import evaluate_avatar_description  # noqa: E402
from tests.test_synthesize_avatar_description import AvatarDescriptionSynthesisTest  # noqa: E402


class AvatarDescriptionEvalTest(unittest.TestCase):
    def write_eval_ready_repo(self, root: Path) -> None:
        AvatarDescriptionSynthesisTest().write_minimal_repo(root)
        (root / "identity" / "cognition").mkdir(parents=True, exist_ok=True)
        (root / "identity" / "cognition" / "data-contracts.yml").write_text(
            "\n".join(
                [
                    "version: 1",
                    "avatar_description_claim_approval:",
                    "  schema: openlifeos.avatar-description-synthesis.v1",
                    "  current_entrypoint: identity/avatar-description/current.yml",
                    "  approved_manifest_shape:",
                    "    approval:",
                    "      required_fields:",
                    "        - reviewer",
                    "        - approved_at",
                    "        - approval_ref",
                    "    approved_claims:",
                    "      allowed_fields:",
                    "        - one_line",
                    "        - current_role",
                    "        - operating_mode",
                    "        - strengths",
                    "        - boundaries",
                    "      required_fields_per_claim:",
                    "        - value",
                    "        - evidence",
                    "  evidence_rules:",
                    "    - evidence refs must be repo-relative paths that exist in this LifeOS repo",
                    "  failure_rules:",
                    "    - missing approval metadata fails synthesis",
                    "    - missing or disallowed evidence refs fail synthesis",
                ]
            ),
            encoding="utf-8",
        )
        (root / "docs" / "evidence-sufficiency.md").write_text(
            "# Evidence Sufficiency Report\n\nCurrent maturity: `evidence-limited-v0`\n",
            encoding="utf-8",
        )
        (root / "artifacts" / "current.yml").write_text(
            "\n".join(
                [
                    "schema: openlifeos.artifacts-current.v1",
                    "artifacts:",
                    "  avatar_description:",
                    "    semantic_role: product_facing_current_avatar_description",
                    '    answers: "What is this digital avatar currently like?"',
                    "    current_entrypoint: identity/avatar-description/current.yml",
                    "    active_artifact: identity/avatar-description/current.yml",
                    "    status: active",
                    "    evidence_sufficiency: partial",
                    "  wenxin:",
                    "    current_entrypoint: identity/wenxin/WENXIN_REPORT.md",
                    "    active_artifact: identity/wenxin/WENXIN-20260602.md",
                    "  psp:",
                    "    current_entrypoint: identity/psp/example-person/current/PSP_REPORT.xml",
                    "    active_artifact: identity/psp/example-person/versions/PSP_REPORT.20260602.xml",
                    "  evidence_maturity:",
                    "    current_entrypoint: identity/psp/example-person/current/EVIDENCE_MATURITY.xml",
                ]
            ),
            encoding="utf-8",
        )
        for rel in [
            "identity/wenxin/WENXIN-20260602.md",
        ]:
            (root / rel).write_text(f"# {rel}\n", encoding="utf-8")
        (root / "identity" / "avatar-description" / "current.yml").write_text(
            "\n".join(
                [
                    "schema: openlifeos.avatar-description.v1",
                    "display_name: Example Person",
                    'one_line: "Example product-facing summary."',
                    'current_role: "Example current role for a product surface."',
                    "evidence_level: partial",
                    'maturity_notice: "This is not a single markdown source; evidence remains partial."',
                    "operating_mode:",
                    '  - "Keeps source-of-truth boundaries clear."',
                    '  - "Uses approved evidence before changing claims."',
                    "strengths:",
                    '  - "Builds reliable systems."',
                    '  - "Explains tradeoffs clearly."',
                    "boundaries:",
                    '  - "Does not infer private facts."',
                    '  - "Does not overstate evidence maturity."',
                    "source_refs:",
                    "  - identity/wenxin/WENXIN_REPORT.md",
                    "  - identity/psp/example-person/current/PSP_REPORT.xml",
                    "  - identity/psp/example-person/current/EVIDENCE_MATURITY.xml",
                    "claim_evidence:",
                    "  one_line:",
                    "    - identity/wenxin/WENXIN_REPORT.md",
                    "  current_role:",
                    "    - identity/psp/example-person/current/PSP_REPORT.xml",
                    "  operating_mode:",
                    "    - identity/psp/example-person/current/PSP_REPORT.xml",
                    "  strengths:",
                    "    - identity/wenxin/WENXIN_REPORT.md",
                    "  boundaries:",
                    "    - identity/psp/example-person/current/EVIDENCE_MATURITY.xml",
                    "derived_from:",
                    "  - identity/wenxin/WENXIN-20260602.md",
                    "  - identity/psp/example-person/versions/PSP_REPORT.20260602.xml",
                    "  - identity/psp/example-person/current/EVIDENCE_MATURITY.xml",
                ]
            ),
            encoding="utf-8",
        )

    def test_eval_passes_for_current_anthonyhf_sample(self) -> None:
        result = evaluate_avatar_description(ROOT / "output/meta/AnthonyHF.LifeOS")

        self.assertEqual(result["status"], "pass", result["issues"])

    def test_eval_rejects_non_product_facing_and_overstated_description(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_eval_ready_repo(root)
            path = root / "identity" / "avatar-description" / "current.yml"
            text = path.read_text(encoding="utf-8")
            text = text.replace('one_line: "Example product-facing summary."', 'one_line: "/Users/example/raw/private.md"')
            text = text.replace("evidence_level: partial", "evidence_level: sufficient")
            text = text.replace("  strengths:\n    - identity/wenxin/WENXIN_REPORT.md\n", "  strengths:\n")
            path.write_text(text, encoding="utf-8")

            result = evaluate_avatar_description(root)

        self.assertEqual(result["status"], "fail")
        codes = {issue["code"] for issue in result["issues"]}
        self.assertIn("primary_field_not_product_facing", codes)
        self.assertIn("missing_claim_evidence", codes)
        self.assertIn("overstated_evidence_level", codes)

    def test_cli_writes_markdown_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_eval_ready_repo(root)
            report = "docs/avatar-description-eval.md"

            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "evaluate_avatar_description.py"),
                    str(root),
                    "--write-report",
                    report,
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            report_text = (root / report).read_text(encoding="utf-8")
            self.assertIn("# Avatar Description Eval", report_text)
            self.assertIn("Status: `pass`", report_text)


if __name__ == "__main__":
    unittest.main()
