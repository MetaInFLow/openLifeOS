from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from doctor_avatar_repo import run_doctor, to_json  # noqa: E402


class DoctorAvatarRepoLifecycleTest(unittest.TestCase):
    def write_minimal_lifeos(self, root: Path) -> None:
        for rel in [
            "identity/wenxin",
            "identity/psp/example-person/current",
            "identity/psp/example-person/versions",
            "identity/public-profile",
            "runtime/sessions/session-001",
            "runtime/runtime-skills",
            "runtime/runtime-lessons",
            "evolution/ipo",
            "capabilities",
            "roles",
            "work",
            "intake",
            "docs",
            "artifacts",
        ]:
            (root / rel).mkdir(parents=True, exist_ok=True)
            (root / rel / "README.md").write_text(f"# {rel}\n", encoding="utf-8")
        (root / "replicateme.yml").write_text(
            "repo_name: Example.LifeOS\nlanguage: zh-CN\nprocess_log_language: zh-CN\n",
            encoding="utf-8",
        )
        (root / "LIFEOS_STATUS.yml").write_text(
            "\n".join(
                [
                    "schema: openlifeos.lifecycle-status.v1",
                    "created_at: \"2026-04-02T00:00:00+08:00\"",
                    "updated_at: \"2026-06-02T00:00:00+08:00\"",
                ]
            ),
            encoding="utf-8",
        )
        (root / "identity/wenxin/WENXIN_REPORT.md").write_text("# Wenxin\n", encoding="utf-8")
        (root / "identity/psp/example-person/current/PSP_REPORT.xml").write_text(
            '<psp_report schema="psp.report.v1"><metadata/><evidence_maturity/><source_inventory/><evidence_boundary/><ontology_map/><kernel/><cognition/><decision_model/><interaction_model/><business_domain_model/><language_fingerprint/><best_state/><delegation_boundary/><runtime_instructions/><validation_plan/><confirmation_checklist/><acceptance_criteria/><confidence_by_section/><missing_information/><iteration_log/></psp_report>\n',
            encoding="utf-8",
        )
        (root / "identity/psp/example-person/versions/PSP_REPORT.20260602.xml").write_text(
            (root / "identity/psp/example-person/current/PSP_REPORT.xml").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        (root / "runtime/sessions/session-001/task.md").write_text("# Task\n", encoding="utf-8")
        (root / "runtime/runtime-lessons/lesson-001.md").write_text("# Lesson\n", encoding="utf-8")
        (root / "docs/evidence-sufficiency.md").write_text(
            "# Evidence Sufficiency\n\nCurrent maturity: `evidence-limited-v0`\n",
            encoding="utf-8",
        )

    def test_json_reports_lifecycle_stage_and_age_from_status_dates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_minimal_lifeos(root)

            payload = to_json(run_doctor(root))

        stage = payload["life_stage"]
        self.assertEqual(stage["stage_id"], 6)
        self.assertEqual(stage["stage_name"], "Runtime Lesson")
        self.assertEqual(stage["age_days"], 61)
        self.assertEqual(stage["age_label"], "约 2 个月")
        self.assertIn("runtime/runtime-lessons", stage["stage_reason"])

    def test_scaffold_psp_and_wenxin_do_not_count_as_completed_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_minimal_lifeos(root)
            (root / "artifacts" / "current.yml").write_text(
                "\n".join(
                    [
                        "schema: openlifeos.artifacts-current.v1",
                        "artifacts:",
                        "  wenxin:",
                        "    status: intake-only",
                        "    evidence_sufficiency: insufficient",
                        "  psp:",
                        "    status: v0.1-intake-only-routing-model",
                        "    evidence_sufficiency: insufficient",
                    ]
                ),
                encoding="utf-8",
            )
            (root / "docs/evidence-sufficiency.md").write_text(
                "# Evidence Sufficiency\n\nCurrent maturity: `scaffold`\n",
                encoding="utf-8",
            )
            for rel in [
                "runtime/sessions/session-001/task.md",
                "runtime/runtime-lessons/lesson-001.md",
            ]:
                (root / rel).unlink()

            payload = to_json(run_doctor(root))

        stage = payload["life_stage"]
        self.assertEqual(stage["stage_id"], 0)
        self.assertEqual(stage["stage_name"], "Kernel Scaffold")

    def test_json_reports_skill_content_maturity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_minimal_lifeos(root)

            payload = to_json(run_doctor(root))

        self.assertIn("content_maturity", payload)
        self.assertIn("skill_content_maturity", payload)
        self.assertIn("level", payload["content_maturity"])
        self.assertIn("psp", payload["skill_content_maturity"])
        self.assertIn("score", payload["skill_content_maturity"]["psp"])
        self.assertIn("blocking_gaps", payload["skill_content_maturity"]["psp"])

    def test_current_anthonyhf_reports_lifecycle_stage(self) -> None:
        payload = to_json(run_doctor(ROOT / "output/meta/AnthonyHF.LifeOS"))

        stage = payload["life_stage"]
        self.assertEqual(stage["stage_id"], 8)
        self.assertEqual(stage["stage_name"], "Meta Skill Formation")
        self.assertEqual(stage["age_days"], 61)
        self.assertEqual(stage["age_label"], "约 2 个月")


if __name__ == "__main__":
    unittest.main()
