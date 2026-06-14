from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from synthesize_avatar_description import synthesize_avatar_description  # noqa: E402


class AvatarDescriptionSynthesisTest(unittest.TestCase):
    def write_minimal_repo(self, root: Path) -> None:
        for rel in [
            "identity/avatar-description",
            "identity/wenxin",
            "identity/psp/example-person/current",
            "identity/psp/example-person/versions",
            "docs",
        ]:
            (root / rel).mkdir(parents=True, exist_ok=True)
        for rel in [
            "identity/wenxin/WENXIN_REPORT.md",
            "identity/psp/example-person/current/PSP_REPORT.xml",
            "identity/psp/example-person/versions/PSP_REPORT.20260602.xml",
        ]:
            (root / rel).write_text(f"# {rel}\n", encoding="utf-8")
        (root / "identity/psp/example-person/current/EVIDENCE_MATURITY.xml").write_text(
            '<evidence_maturity schema="psp.evidence-maturity.v1"><maturity level="evidence-limited-v0"/></evidence_maturity>\n',
            encoding="utf-8",
        )
        (root / "artifacts").mkdir()
        (root / "artifacts" / "current.yml").write_text(
            "\n".join(
                [
                    "schema: openlifeos.artifacts-current.v1",
                    "artifacts:",
                    "  avatar_description:",
                    "    current_entrypoint: identity/avatar-description/current.yml",
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
        (root / "identity" / "avatar-description" / "current.yml").write_text(
            "\n".join(
                [
                    "schema: openlifeos.avatar-description.v1",
                    "display_name: Example Person",
                    'one_line: "Keep this exact current summary."',
                    'current_role: "Keep this exact role."',
                    "evidence_level: insufficient",
                    'maturity_notice: "Old maturity notice."',
                    "operating_mode:",
                    '  - "Keep this operating mode."',
                    "strengths:",
                    '  - "Keep this strength."',
                    "boundaries:",
                    '  - "Keep this boundary."',
                    "source_refs:",
                    "  - old/source.md",
                    "claim_evidence:",
                    "  one_line:",
                    "    - old/source.md",
                    "  current_role:",
                    "    - old/source.md",
                    "  operating_mode:",
                    "    - old/source.md",
                    "  strengths:",
                    "    - old/source.md",
                    "  boundaries:",
                    "    - old/source.md",
                    "derived_from:",
                    "  - old/source.md",
                    'updated_at: "2026-01-01T00:00:00+00:00"',
                ]
            ),
            encoding="utf-8",
        )

    def test_synthesis_refreshes_refs_without_rewriting_claim_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_minimal_repo(root)

            result = synthesize_avatar_description(
                root,
                timestamp="2026-06-02T12:00:00+08:00",
            )

            text = (root / "identity" / "avatar-description" / "current.yml").read_text(encoding="utf-8")

        self.assertEqual(result.changed_fields, [])
        self.assertIn('one_line: "Keep this exact current summary."', text)
        self.assertIn('current_role: "Keep this exact role."', text)
        self.assertIn("identity/wenxin/WENXIN_REPORT.md", text)
        self.assertIn("identity/psp/example-person/current/PSP_REPORT.xml", text)
        self.assertIn("identity/psp/example-person/current/EVIDENCE_MATURITY.xml", text)
        self.assertNotIn("SOUL.md", text)
        self.assertNotIn("old/source.md", text)
        self.assertIn('updated_at: "2026-06-02T12:00:00+08:00"', text)

    def test_approved_manifest_can_update_explicit_claim_with_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_minimal_repo(root)
            manifest = root / "approved-avatar-claims.yml"
            manifest.write_text(
                "\n".join(
                    [
                        "schema: openlifeos.avatar-description-synthesis.v1",
                        "approval:",
                        '  reviewer: "owner@example.test"',
                        '  approved_at: "2026-06-02T12:30:00+08:00"',
                        '  approval_ref: "review://avatar-description/one-line"',
                        "approved_claims:",
                        "  one_line:",
                        '    value: "Approved replacement summary."',
                        "    evidence:",
                        "      - identity/wenxin/WENXIN_REPORT.md",
                    ]
                ),
                encoding="utf-8",
            )

            result = synthesize_avatar_description(
                root,
                approved_claims_path=manifest,
                timestamp="2026-06-02T12:30:00+08:00",
            )

            text = (root / "identity" / "avatar-description" / "current.yml").read_text(encoding="utf-8")

        self.assertEqual(result.changed_fields, ["one_line"])
        self.assertIn('one_line: "Approved replacement summary."', text)
        self.assertIn('current_role: "Keep this exact role."', text)
        self.assertIn("  one_line:\n    - approval:review://avatar-description/one-line\n    - identity/wenxin/WENXIN_REPORT.md", text)

    def test_approved_manifest_requires_reviewer_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_minimal_repo(root)
            manifest = root / "approved-avatar-claims.yml"
            manifest.write_text(
                "\n".join(
                    [
                        "schema: openlifeos.avatar-description-synthesis.v1",
                        "approved_claims:",
                        "  one_line:",
                        '    value: "Unreviewed replacement summary."',
                        "    evidence:",
                        "      - identity/wenxin/WENXIN_REPORT.md",
                    ]
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "approval.reviewer"):
                synthesize_avatar_description(
                    root,
                    approved_claims_path=manifest,
                    timestamp="2026-06-02T12:30:00+08:00",
                )

            text = (root / "identity" / "avatar-description" / "current.yml").read_text(encoding="utf-8")

        self.assertIn('one_line: "Keep this exact current summary."', text)

    def test_approved_manifest_rejects_missing_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_minimal_repo(root)
            manifest = root / "approved-avatar-claims.yml"
            manifest.write_text(
                "\n".join(
                    [
                        "schema: openlifeos.avatar-description-synthesis.v1",
                        "approval:",
                        '  reviewer: "owner@example.test"',
                        '  approved_at: "2026-06-02T12:30:00+08:00"',
                        '  approval_ref: "review://avatar-description/one-line"',
                        "approved_claims:",
                        "  one_line:",
                        '    value: "Missing evidence replacement summary."',
                        "    evidence:",
                        "      - private/raw-transcript.md",
                    ]
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "missing or disallowed evidence"):
                synthesize_avatar_description(
                    root,
                    approved_claims_path=manifest,
                    timestamp="2026-06-02T12:30:00+08:00",
                )

            text = (root / "identity" / "avatar-description" / "current.yml").read_text(encoding="utf-8")

        self.assertIn('one_line: "Keep this exact current summary."', text)


if __name__ == "__main__":
    unittest.main()
