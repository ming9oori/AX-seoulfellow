#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a plan-to-evidence compliance matrix for the CAPE-KG EACL plan."""

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_PLAN_FILE = Path("AX_EACL_submission_review_revised_plan.md")


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path):
    path = Path(path)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def file_evidence(path):
    path = Path(path)
    return {
        "path": str(path),
        "exists": path.exists(),
        "bytes": path.stat().st_size if path.exists() else 0,
    }


def fmt(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value).replace("\n", " ")


def md_table(headers, rows):
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(header, "")) for header in headers) + " |")
    return "\n".join(lines)


def audit_items_by_id(audit):
    return {item.get("id"): item for item in audit.get("items", []) if item.get("id")}


def gate_by_id(claim_gate):
    return {gate.get("gate_id"): gate for gate in claim_gate.get("gates", []) if gate.get("gate_id")}


def first_file_from_evidence(evidence):
    paths = []

    def collect(value):
        if isinstance(value, dict):
            if value.get("path"):
                paths.append(value["path"])
            for nested in value.values():
                collect(nested)
        elif isinstance(value, list):
            for nested in value:
                collect(nested)

    collect(evidence)
    return ", ".join(paths[:3])


def checklist_rows(exp_dir, audit):
    rows = []
    for audit_item in audit.get("items", []):
        status = audit_item.get("status")
        rows.append(
            {
                "scope": audit_item.get("category"),
                "id": audit_item.get("id"),
                "requirement": audit_item.get("requirement"),
                "status": status,
                "claimable": bool(audit_item.get("claimable")),
                "automation_state": automation_state(status),
                "evidence": first_file_from_evidence(audit_item.get("evidence")),
                "next_step": audit_item.get("next_step"),
            }
        )
    return rows


def automation_state(status):
    status = str(status or "").lower()
    if status == "pass":
        return "automatic_artifact_ready"
    if status == "pending_human":
        return "requires_human_review"
    if status == "partial":
        return "automatic_scaffold_ready_human_evidence_pending"
    return "inspect"


def module_rows(method_coverage):
    rows = []
    for module in method_coverage.get("modules", []):
        missing = int(module.get("missing_required_artifact_count") or 0)
        human = bool(module.get("human_dependent_for_final_claim"))
        if missing:
            automation = "missing_required_artifact"
        elif human:
            automation = "automatic_artifact_ready_human_claim_pending"
        else:
            automation = "automatic_artifact_ready"
        rows.append(
            {
                "module": module.get("module_id"),
                "name": module.get("name"),
                "status": module.get("status"),
                "required_artifacts": module.get("required_artifact_count"),
                "missing_required": missing,
                "human_dependent": human,
                "automation_state": automation,
                "remaining_for_claim": module.get("remaining_for_paper_claim"),
            }
        )
    return rows


def claim_gate_rows(claim_gate):
    rows = []
    for gate in claim_gate.get("gates", []):
        rows.append(
            {
                "gate_id": gate.get("gate_id"),
                "status": gate.get("status"),
                "required": bool(gate.get("required")),
                "severity": gate.get("severity"),
                "evidence": gate.get("evidence"),
            }
        )
    return rows


def human_return_rows(exp_dir):
    rows = read_csv(exp_dir / "05_review/human_gate_required_returns.csv")
    if rows:
        return rows
    preflight = read_json(exp_dir / "06_release/human_review_return_preflight.json", {}) or {}
    return preflight.get("required_return_files", [])


def human_master_return_rows(exp_dir):
    return read_csv(exp_dir / "05_review/human_review_master_return_files.csv")


def truthy(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"yes", "true", "1", "present"}
    return bool(value)


def return_file_counts(rows):
    minimum = [row for row in rows if truthy(row.get("required_for_minimum", True))]
    optional = [row for row in rows if not truthy(row.get("required_for_minimum", True))]
    return {
        "minimum_paper_gate_return_file_count": len(minimum),
        "minimum_paper_gate_return_file_present_count": sum(1 for row in minimum if truthy(row.get("present"))),
        "optional_strong_return_file_count": len(optional),
        "optional_strong_return_file_present_count": sum(1 for row in optional if truthy(row.get("present"))),
        "tracked_human_return_file_count": len(rows),
        "tracked_human_return_file_present_count": sum(1 for row in rows if truthy(row.get("present"))),
    }


def master_return_file_counts(rows):
    minimum = [row for row in rows if truthy(row.get("required_for_minimum", True))]
    optional = [row for row in rows if not truthy(row.get("required_for_minimum", True))]
    optional_structural = [row for row in optional if row.get("requiredness") == "optional_structural"]
    optional_claim = [row for row in optional if row.get("requiredness") != "optional_structural"]
    required_claim = [row for row in rows if row.get("requiredness", "required") == "required"]
    return {
        "master_minimum_return_file_count": len(minimum),
        "master_minimum_return_file_present_count": sum(1 for row in minimum if truthy(row.get("present"))),
        "master_optional_claim_return_file_count": len(optional_claim),
        "master_optional_claim_return_file_present_count": sum(1 for row in optional_claim if truthy(row.get("present"))),
        "master_optional_structural_return_file_count": len(optional_structural),
        "master_optional_structural_return_file_present_count": sum(1 for row in optional_structural if truthy(row.get("present"))),
        "master_required_claim_return_file_count": len(required_claim),
        "master_required_claim_return_file_present_count": sum(1 for row in required_claim if truthy(row.get("present"))),
        "master_return_file_count": len(rows),
        "master_return_file_present_count": sum(1 for row in rows if truthy(row.get("present"))),
    }


def build_payload(exp_dir, plan_file):
    release_dir = exp_dir / "06_release"
    audit = read_json(release_dir / "submission_readiness_audit.json", {}) or {}
    claim_gate = read_json(release_dir / "claim_gate_report.json", {}) or {}
    method_coverage = read_json(release_dir / "method_module_coverage.json", {}) or {}
    strict = read_json(release_dir / "strict_json_diagnostics.json", {}) or {}
    pre_human = read_json(release_dir / "pre_human_handoff_validation.json", {}) or {}
    completion = read_json(release_dir / "submission_completion_audit_ko.json", {}) or {}
    provenance = read_json(release_dir / "provenance_manifest.json", {}) or {}
    prov_o = read_json(release_dir / "provenance_prov_o_summary.json", {}) or {}
    rdf_shacl = read_json(Path(audit.get("outputs_dir", "outputs")) / "12_rdf/cape_kg_shacl_validation_summary.json", {}) or {}
    returns = human_return_rows(exp_dir)
    master_returns = human_master_return_rows(exp_dir)
    return_counts = return_file_counts(returns)
    master_return_counts = master_return_file_counts(master_returns) if master_returns else {}

    checklist = checklist_rows(exp_dir, audit)
    modules = module_rows(method_coverage)
    gates = claim_gate_rows(claim_gate)
    status_counts = Counter(row["status"] for row in checklist)
    module_state_counts = Counter(row["automation_state"] for row in modules)
    gate_status_counts = Counter(row["status"] for row in gates)

    human_blockers = [
        row
        for row in checklist
        if row["status"] in {"pending_human", "partial"} and not row.get("claimable")
    ]
    minimum_human_blockers = [row for row in human_blockers if row.get("scope") == "minimum_accept"]
    strong_human_blockers = [row for row in human_blockers if row.get("scope") == "strong_accept"]
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "plan_file": str(plan_file),
        "plan_file_evidence": file_evidence(plan_file),
        "summary": {
            "claim_status": audit.get("claim_status"),
            "claim_gate_overall_status": claim_gate.get("overall_status"),
            "claim_gate_required_failures": claim_gate.get("required_failure_count"),
            "claim_gate_optional_failures": claim_gate.get("optional_failure_count"),
            "claim_gate_warnings": claim_gate.get("warning_count"),
            "pre_human_handoff_status": pre_human.get("overall_status"),
            "pre_human_handoff_checks": pre_human.get("check_count"),
            "pre_human_handoff_status_counts": pre_human.get("status_counts"),
            "strict_json_gate_status": strict.get("strict_json_gate_status"),
            "strict_json_warning_conditions": strict.get("conditions_over_strict_json_warning_threshold"),
            "provenance_claim_status": provenance.get("claim_status"),
            "prov_o_claim_status": prov_o.get("claim_status"),
            "rdf_shacl_claim_status": rdf_shacl.get("claim_status"),
            "rdf_shacl_overall_status": rdf_shacl.get("overall_status"),
            "minimum_and_strong_status_counts": dict(status_counts),
            "method_module_state_counts": dict(module_state_counts),
            "claim_gate_status_counts": dict(gate_status_counts),
            **return_counts,
            **master_return_counts,
            "required_human_return_file_count": len(returns),
            "minimum_human_blocker_count": len(minimum_human_blockers),
            "strong_or_optional_human_blocker_count": len(strong_human_blockers),
            "human_blocker_count": len(human_blockers),
            "completion_status": completion.get("overall_completion_status"),
            "submission_ready": False,
        },
        "checklist_rows": checklist,
        "method_module_rows": modules,
        "claim_gate_rows": gates,
        "human_blockers": human_blockers,
        "minimum_human_blockers": minimum_human_blockers,
        "strong_or_optional_human_blockers": strong_human_blockers,
        "required_human_returns": returns,
        "master_human_returns": master_returns,
        "source_artifacts": {
            "submission_readiness_audit": str(release_dir / "submission_readiness_audit.json"),
            "claim_gate_report": str(release_dir / "claim_gate_report.json"),
            "method_module_coverage": str(release_dir / "method_module_coverage.json"),
            "requirements_matrix": str(exp_dir / "00_plan/requirements_matrix.json"),
            "submission_completion_audit": str(release_dir / "submission_completion_audit_ko.json"),
            "paper_readiness_checklist": str(release_dir / "paper_readiness_checklist.json"),
            "human_gate_required_returns": str(exp_dir / "05_review/human_gate_required_returns.csv"),
            "human_review_master_return_files": str(exp_dir / "05_review/human_review_master_return_files.csv"),
            "pre_human_handoff_validation": str(release_dir / "pre_human_handoff_validation.json"),
            "provenance_manifest": str(release_dir / "provenance_manifest.json"),
            "provenance_prov_o_summary": str(release_dir / "provenance_prov_o_summary.json"),
            "rdf_shacl_validation": "outputs/12_rdf/cape_kg_shacl_validation_summary.json",
            "release_bundle_checksums": str(release_dir / "release_bundle_checksums.sha256"),
        },
    }
    return payload


def render_report(payload):
    summary = payload["summary"]
    lines = [
        "# CAPE-KG EACL Plan Compliance Matrix",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Plan file: `{payload['plan_file']}`",
        f"Experiment: `{payload['experiment_dir']}`",
        "",
        "## Summary",
        "",
        f"- Claim status: `{summary.get('claim_status')}`",
        f"- Claim gate: `{summary.get('claim_gate_overall_status')}`",
        f"- Required claim-gate failures: {summary.get('claim_gate_required_failures')}",
        f"- Optional claim-gate failures: {summary.get('claim_gate_optional_failures')}",
        f"- Claim-gate warnings: {summary.get('claim_gate_warnings')}",
        f"- Pre-human handoff validation: `{summary.get('pre_human_handoff_status')}`",
        "- Pre-human check counts: see `pre_human_handoff_validation.md` for the current count and status breakdown.",
        f"- Strict JSON gate: `{summary.get('strict_json_gate_status')}`; warning conditions={summary.get('strict_json_warning_conditions')}",
        f"- Provenance manifest: `{summary.get('provenance_claim_status')}`",
        f"- PROV-O export: `{summary.get('prov_o_claim_status')}`",
        f"- RDF/SHACL-style validation: `{summary.get('rdf_shacl_overall_status')}` / `{summary.get('rdf_shacl_claim_status')}`",
        f"- Minimum paper-gate return files: {summary.get('minimum_paper_gate_return_file_present_count')}/{summary.get('minimum_paper_gate_return_file_count')}",
        f"- Optional/strong claim return files: {summary.get('optional_strong_return_file_present_count')}/{summary.get('optional_strong_return_file_count')}",
        f"- Required claim/human return files: {summary.get('tracked_human_return_file_present_count')}/{summary.get('tracked_human_return_file_count')}",
        f"- Optional structural review files: {summary.get('master_optional_structural_return_file_present_count')}/{summary.get('master_optional_structural_return_file_count')}",
        f"- All master return files: {summary.get('master_return_file_present_count')}/{summary.get('master_return_file_count')}",
        f"- Minimum-accept human blockers: {summary.get('minimum_human_blocker_count')}",
        f"- Strong/optional human blockers: {summary.get('strong_or_optional_human_blocker_count')}",
        f"- Completion status: `{summary.get('completion_status')}`",
        "",
        "Interpretation: automatic artifacts are ready for the current pre-human stage, but submission-level performance claims remain blocked by human-gold annotation, IAA, adjudication, proposed-method human-gold scoring, optional mapping expert review, and optional NCS-PCF crosswalk expert review.",
        "",
        "## Plan Checklist",
        "",
        md_table(
            ["scope", "id", "requirement", "status", "claimable", "automation_state", "evidence", "next_step"],
            payload["checklist_rows"],
        ),
        "",
        "## Method Modules M1-M11",
        "",
        md_table(
            [
                "module",
                "name",
                "status",
                "required_artifacts",
                "missing_required",
                "human_dependent",
                "automation_state",
                "remaining_for_claim",
            ],
            payload["method_module_rows"],
        ),
        "",
        "## Claim Gate",
        "",
        md_table(["gate_id", "status", "required", "severity", "evidence"], payload["claim_gate_rows"]),
        "",
        "## Minimum-Accept Human Blocking Work",
        "",
        md_table(["scope", "id", "requirement", "status", "next_step"], payload["minimum_human_blockers"]),
        "",
        "## Strong/Optional Human Blocking Work",
        "",
        md_table(["scope", "id", "requirement", "status", "next_step"], payload["strong_or_optional_human_blockers"]),
        "",
        "## Required Claim/Human Return Files",
        "",
    ]
    if payload["required_human_returns"]:
        headers = list(payload["required_human_returns"][0].keys())
        lines.append(md_table(headers, payload["required_human_returns"]))
    else:
        lines.append("No required return file manifest was found.")
    lines += [
        "",
        "## Master Human Return Files",
        "",
    ]
    if payload["master_human_returns"]:
        headers = list(payload["master_human_returns"][0].keys())
        lines.append(md_table(headers, payload["master_human_returns"]))
    else:
        lines.append("No master return file manifest was found.")
    lines += [
        "",
        "## Source Artifacts",
        "",
    ]
    for name, path in payload["source_artifacts"].items():
        lines.append(f"- {name}: `{path}`")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--plan-file", default=str(DEFAULT_PLAN_FILE))
    args = parser.parse_args()
    exp_dir = Path(args.experiment_dir)
    plan_file = Path(args.plan_file)
    payload = build_payload(exp_dir, plan_file)
    release_dir = exp_dir / "06_release"
    json_path = release_dir / "eacl_plan_compliance_matrix.json"
    md_path = release_dir / "eacl_plan_compliance_matrix.md"
    write_json(json_path, payload)
    write_text(md_path, render_report(payload))
    print(
        json.dumps(
            {
                "matrix_json": str(json_path),
                "matrix_md": str(md_path),
                "claim_status": payload["summary"].get("claim_status"),
                "human_blocker_count": payload["summary"].get("human_blocker_count"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
