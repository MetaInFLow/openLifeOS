#!/usr/bin/env python3
"""Evaluate whether the Avatar Description is a usable product-facing read model.

This is a deterministic quality baseline. It does not judge whether the
personality claims are true; it checks whether the current description is
structured, short enough for UI/runtime consumption, evidence-linked, and honest
about maturity.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

from synthesize_avatar_description import CLAIM_FIELDS, parse_avatar_description


REQUIRED_FILES = [
    "identity/avatar-description/current.yml",
    "artifacts/current.yml",
    "identity/cognition/data-contracts.yml",
    "docs/evidence-sufficiency.md",
]

PRIVATE_REF_PREFIXES = ("private:", "secret:")
PRIMARY_TEXT_FIELDS = ["one_line", "current_role", "maturity_notice"]
PRIMARY_LIST_FIELDS = ["operating_mode", "strengths", "boundaries"]
MAX_SCALAR_LENGTH = {
    "one_line": 180,
    "current_role": 260,
    "maturity_notice": 420,
}
MIN_LIST_ITEMS = {
    "operating_mode": 2,
    "strengths": 2,
    "boundaries": 2,
}
MAX_LIST_ITEM_LENGTH = 220


@dataclass
class EvalIssue:
    severity: str
    code: str
    message: str


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _as_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _as_str(value: object) -> str:
    return str(value) if value is not None else ""


def _has_absolute_path(text: str) -> bool:
    return bool(re.search(r"(^|\s)(/Users/|/home/|/var/|[A-Za-z]:\\)", text))


def _has_markdown_blob_marker(text: str) -> bool:
    return bool(re.search(r"(^|\n)#{1,6}\s+", text)) or "```" in text


def _path_is_allowed(root: Path, ref: str) -> bool:
    if ref.startswith("approval:"):
        return True
    if ref.startswith("active.") or ref.startswith("source_id:") or ref.startswith("owner-approved-summary:"):
        return True
    if ref.startswith(PRIVATE_REF_PREFIXES):
        return False
    return (root / ref).exists()


def _artifact_registry_has_product_role(text: str) -> bool:
    return (
        "avatar_description:" in text
        and "semantic_role: product_facing_current_avatar_description" in text
        and "current_entrypoint: identity/avatar-description/current.yml" in text
        and "answers:" in text
    )


def _data_contract_has_claim_approval(text: str) -> bool:
    required_terms = [
        "avatar_description_claim_approval:",
        "schema: openlifeos.avatar-description-synthesis.v1",
        "approved_manifest_shape:",
        "allowed_fields:",
        "required_fields_per_claim:",
        "evidence_rules:",
        "failure_rules:",
        "reviewer",
        "approved_at",
        "approval_ref",
    ]
    return all(term in text for term in required_terms)


def _evidence_maturity(text: str) -> str:
    match = re.search(r"Current maturity:\s*`([^`]+)`", text)
    if match:
        return match.group(1)
    match = re.search(r"Maturity Level:\s*`([^`]+)`", text)
    return match.group(1) if match else "unknown"


def evaluate_avatar_description(root: Path) -> dict[str, object]:
    issues: list[EvalIssue] = []
    root = root.expanduser().resolve()

    for rel in REQUIRED_FILES:
        if not (root / rel).exists():
            issues.append(EvalIssue("fail", "missing_required_file", f"Missing required file: {rel}"))

    description_text = _read(root / "identity/avatar-description/current.yml")
    artifacts_text = _read(root / "artifacts/current.yml")
    contracts_text = _read(root / "identity/cognition/data-contracts.yml")
    maturity_text = _read(root / "docs/evidence-sufficiency.md")
    data = parse_avatar_description(description_text)

    if _as_str(data.get("schema")) != "openlifeos.avatar-description.v1":
        issues.append(EvalIssue("fail", "invalid_schema", "Avatar description schema must be openlifeos.avatar-description.v1"))

    for field in ["display_name", *PRIMARY_TEXT_FIELDS, *PRIMARY_LIST_FIELDS, "source_refs", "derived_from", "claim_evidence"]:
        if field not in data:
            issues.append(EvalIssue("fail", "missing_field", f"Avatar description missing {field}"))

    for field in PRIMARY_TEXT_FIELDS:
        text = _as_str(data.get(field)).strip()
        if not text:
            issues.append(EvalIssue("fail", "empty_primary_field", f"{field} must not be empty"))
        if len(text) > MAX_SCALAR_LENGTH[field]:
            issues.append(EvalIssue("warn", "long_primary_field", f"{field} is {len(text)} chars; target <= {MAX_SCALAR_LENGTH[field]}"))
        if _has_absolute_path(text) or _has_markdown_blob_marker(text):
            issues.append(EvalIssue("fail", "primary_field_not_product_facing", f"{field} contains path or markdown blob markers"))

    for field in PRIMARY_LIST_FIELDS:
        values = _as_list(data.get(field))
        if len(values) < MIN_LIST_ITEMS[field]:
            issues.append(EvalIssue("fail", "too_few_list_items", f"{field} should have at least {MIN_LIST_ITEMS[field]} items"))
        for item in values:
            if len(item) > MAX_LIST_ITEM_LENGTH:
                issues.append(EvalIssue("warn", "long_list_item", f"{field} item is {len(item)} chars; target <= {MAX_LIST_ITEM_LENGTH}"))
            if _has_absolute_path(item) or _has_markdown_blob_marker(item):
                issues.append(EvalIssue("fail", "list_item_not_product_facing", f"{field} contains path or markdown blob markers"))

    maturity_notice = _as_str(data.get("maturity_notice")).lower()
    if "single markdown" not in maturity_notice and "single md" not in maturity_notice:
        issues.append(EvalIssue("fail", "maturity_notice_missing_multi_artifact_boundary", "maturity_notice must say this is not a single markdown source"))
    if "partial" not in maturity_notice and "evidence" not in maturity_notice:
        issues.append(EvalIssue("fail", "maturity_notice_missing_evidence_boundary", "maturity_notice must disclose evidence maturity/boundary"))

    evidence_level = _as_str(data.get("evidence_level"))
    maturity = _evidence_maturity(maturity_text)
    if evidence_level not in {"insufficient", "partial", "sufficient"}:
        issues.append(EvalIssue("fail", "invalid_evidence_level", "evidence_level must be insufficient, partial, or sufficient"))
    if maturity == "evidence-limited-v0" and evidence_level == "sufficient":
        issues.append(EvalIssue("fail", "overstated_evidence_level", "evidence_level cannot be sufficient while evidence maturity is evidence-limited-v0"))

    claim_evidence = data.get("claim_evidence", {})
    if not isinstance(claim_evidence, dict):
        issues.append(EvalIssue("fail", "invalid_claim_evidence", "claim_evidence must be a mapping"))
        claim_evidence = {}
    for field in CLAIM_FIELDS:
        refs = _as_list(claim_evidence.get(field))
        if not refs:
            issues.append(EvalIssue("fail", "missing_claim_evidence", f"claim_evidence.{field} must contain at least one ref"))
        for ref in refs:
            if not _path_is_allowed(root, ref):
                issues.append(EvalIssue("fail", "bad_claim_evidence_ref", f"claim_evidence.{field} has missing/disallowed ref: {ref}"))

    for field_name in ["source_refs", "derived_from"]:
        refs = _as_list(data.get(field_name))
        if not refs:
            issues.append(EvalIssue("fail", "missing_refs", f"{field_name} must contain at least one ref"))
        for ref in refs:
            if not _path_is_allowed(root, ref):
                issues.append(EvalIssue("fail", "bad_ref", f"{field_name} has missing/disallowed ref: {ref}"))

    if not _artifact_registry_has_product_role(artifacts_text):
        issues.append(EvalIssue("fail", "artifact_registry_missing_product_role", "artifacts/current.yml must declare avatar_description as product_facing_current_avatar_description with answers/current_entrypoint"))
    if not _data_contract_has_claim_approval(contracts_text):
        issues.append(EvalIssue("fail", "data_contract_missing_claim_approval", "identity/cognition/data-contracts.yml must declare avatar_description_claim_approval"))

    fail_count = sum(1 for issue in issues if issue.severity == "fail")
    warn_count = sum(1 for issue in issues if issue.severity == "warn")
    status = "pass" if fail_count == 0 else "fail"
    return {
        "status": status,
        "summary": {
            "failures": fail_count,
            "warnings": warn_count,
            "evidenceLevel": evidence_level,
            "maturityLevel": maturity,
            "claimFields": CLAIM_FIELDS,
        },
        "issues": [issue.__dict__ for issue in issues],
    }


def write_markdown_report(path: Path, result: dict[str, object]) -> None:
    summary = result["summary"]
    assert isinstance(summary, dict)
    issues = result["issues"]
    assert isinstance(issues, list)
    lines = [
        "# Avatar Description Eval",
        "",
        f"- Status: `{result['status']}`",
        f"- Failures: `{summary['failures']}`",
        f"- Warnings: `{summary['warnings']}`",
        f"- Evidence level: `{summary['evidenceLevel']}`",
        f"- Maturity level: `{summary['maturityLevel']}`",
        "",
        "## What This Checks",
        "",
        "- The current Avatar Description is structured and product-facing.",
        "- Primary fields do not expose raw paths, markdown blobs, or private refs.",
        "- Every visible claim has field-level evidence.",
        "- Source refs and derived refs exist or use approved pseudo refs.",
        "- Artifact registry and data-contract rules make the artifact role and claim update gate explicit.",
        "",
        "## Issues",
        "",
    ]
    if not issues:
        lines.append("- None.")
    else:
        for issue in issues:
            assert isinstance(issue, dict)
            lines.append(f"- `{issue['severity']}` `{issue['code']}`: {issue['message']}")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", help="Avatar LifeOS repo directory")
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    parser.add_argument("--write-report", help="Write markdown report relative to the target repo or as an absolute path")
    args = parser.parse_args()

    root = Path(args.target).expanduser().resolve()
    result = evaluate_avatar_description(root)
    if args.write_report:
        report_path = Path(args.write_report)
        if not report_path.is_absolute():
            report_path = root / report_path
        write_markdown_report(report_path, result)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Avatar description eval: {result['status']}")
        summary = result["summary"]
        assert isinstance(summary, dict)
        print(f"Failures: {summary['failures']}; warnings: {summary['warnings']}")
        for issue in result["issues"]:
            assert isinstance(issue, dict)
            print(f"- {issue['severity']} {issue['code']}: {issue['message']}")

    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
