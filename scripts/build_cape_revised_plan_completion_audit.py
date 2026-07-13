#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a detailed completion audit for the revised CAPE-KG EACL plan."""

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from cape_pre_human_status import effective_prehuman_summary


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_OUTPUTS_DIR = Path("outputs")
DEFAULT_PLAN_FILE = Path("AX_EACL_submission_review_revised_plan.md")
CLAIM_STATUS = "revised_plan_not_complete_human_evidence_pending"
PUBLIC_SAFE_CLAIM_STATUS = "public_safe_revised_plan_completion_audit_ready_not_submission_complete"


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


def write_csv(path, rows, fieldnames):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def rel(path):
    return str(Path(path).as_posix())


def truthy(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"yes", "true", "1", "present"}
    return bool(value)


def split_evidence_paths(value):
    paths = []
    for item in str(value or "").split(","):
        item = item.strip()
        if item:
            paths.append(item)
    return paths


def evidence_state(paths):
    if not paths:
        return {
            "evidence_file_count": 0,
            "evidence_files_present": False,
            "missing_evidence_files": [],
        }
    missing = [path for path in paths if not Path(path).exists()]
    return {
        "evidence_file_count": len(paths),
        "evidence_files_present": not missing,
        "missing_evidence_files": missing,
    }


def proof_state(row):
    status = str(row.get("status") or "").lower()
    claimable = truthy(row.get("claimable"))
    if status == "pass" and claimable:
        return "proven_for_current_automatic_stage"
    if status == "pass" and not claimable:
        return "artifact_ready_not_claimable"
    if status == "partial":
        return "scaffold_ready_human_evidence_pending"
    if status == "pending_human":
        return "human_required_not_complete"
    return "inspect"


def build_audit_rows(compliance):
    rows = []
    for row in compliance.get("checklist_rows") or []:
        evidence_paths = split_evidence_paths(row.get("evidence"))
        evidence = evidence_state(evidence_paths)
        state = proof_state(row)
        completion_proven = state == "proven_for_current_automatic_stage"
        rows.append(
            {
                "scope": row.get("scope"),
                "id": row.get("id"),
                "requirement": row.get("requirement"),
                "status": row.get("status"),
                "claimable": "yes" if truthy(row.get("claimable")) else "no",
                "automation_state": row.get("automation_state"),
                "proof_state": state,
                "completion_proven": "yes" if completion_proven else "no",
                "human_blocked": "yes" if state in {"human_required_not_complete", "scaffold_ready_human_evidence_pending"} else "no",
                "evidence_file_count": evidence["evidence_file_count"],
                "evidence_files_present": "yes" if evidence["evidence_files_present"] else "no",
                "missing_evidence_files": ";".join(evidence["missing_evidence_files"]),
                "evidence": row.get("evidence"),
                "next_step": row.get("next_step"),
            }
        )
    return rows


def method_rows(compliance):
    rows = []
    for row in compliance.get("method_module_rows") or []:
        missing = int(row.get("missing_required") or 0)
        human_dependent = truthy(row.get("human_dependent"))
        rows.append(
            {
                "module": row.get("module"),
                "name": row.get("name"),
                "status": row.get("status"),
                "required_artifacts": row.get("required_artifacts"),
                "missing_required": missing,
                "human_dependent": "yes" if human_dependent else "no",
                "proof_state": "artifact_present_human_claim_pending" if human_dependent else "artifact_present",
                "remaining_for_claim": row.get("remaining_for_claim"),
            }
        )
    return rows


def first_missing_return_rows(rows, limit=8):
    out = []
    for row in rows:
        if truthy(row.get("present")):
            continue
        out.append(
            {
                "required_for_minimum": "yes" if truthy(row.get("required_for_minimum")) else "no",
                "task_type": row.get("task_type"),
                "owner": row.get("owner"),
                "batch_or_group": row.get("batch_or_group"),
                "expected_rows": row.get("expected_rows"),
                "reviewed_file": row.get("reviewed_file"),
                "status": row.get("status"),
                "next_action": row.get("next_action") or row.get("next_step"),
            }
        )
        if len(out) >= limit:
            break
    return out


def public_evidence_category(row):
    status = str(row.get("status") or "").lower()
    scope = str(row.get("scope") or "")
    if status == "pass":
        return "public_or_release_artifact_available"
    if scope == "minimum_accept":
        return "human_gold_return_required"
    if scope == "strong_accept":
        return "strong_or_expert_return_required"
    return "internal_completion_evidence"


def public_next_step(row):
    proof = row.get("proof_state")
    row_id = row.get("id")
    if proof == "proven_for_current_automatic_stage":
        return "No additional automatic step is required before human returns."
    if row_id in {"min.gold_chunks", "min.gold_items"}:
        return "Complete two-reviewer gold labeling and adjudicated resolution for the minimum evaluation set."
    if row_id == "min.iaa":
        return "Compute agreement after both reviewer streams are complete."
    if row_id == "min.proposed":
        return "Score the proposed condition against adjudicated human-gold labels."
    if row_id in {"strong.gold_chunks", "strong.gold_items"}:
        return "Complete the optional larger human-gold review set before making strong-scale claims."
    if row_id == "strong.mapping_downstream":
        return "Complete expert review before making ranking or utility claims."
    if row_id == "strong.active_review":
        return "Collect reviewer effort and correction outcomes before claiming review-efficiency gains."
    return "Inspect current plan evidence and update after human returns."


def build_public_safe_payload(payload):
    public_rows = []
    for row in payload["audit_rows"]:
        public_rows.append(
            {
                "scope": row.get("scope"),
                "id": row.get("id"),
                "requirement": row.get("requirement"),
                "status": row.get("status"),
                "claimable": row.get("claimable"),
                "proof_state": row.get("proof_state"),
                "completion_proven": row.get("completion_proven"),
                "human_blocked": row.get("human_blocked"),
                "evidence_category": public_evidence_category(row),
                "public_next_step": public_next_step(row),
            }
        )
    return {
        "generated_at_utc": payload["generated_at_utc"],
        "claim_status": PUBLIC_SAFE_CLAIM_STATUS,
        "source_claim_status": payload["claim_status"],
        "plan_file": payload["plan_file"],
        "public_safety": {
            "source_text_included": False,
            "private_review_paths_included": False,
            "reviewed_file_names_included": False,
            "contains_only_counts_statuses_and_generic_next_steps": True,
        },
        "completion_decision": payload["completion_decision"],
        "summary": {
            "checklist_item_count": payload["summary"]["checklist_item_count"],
            "completion_proven_item_count": payload["summary"]["completion_proven_item_count"],
            "human_blocked_item_count": payload["summary"]["human_blocked_item_count"],
            "minimum_human_blocker_count": payload["summary"]["minimum_human_blocker_count"],
            "strong_or_optional_human_blocker_count": payload["summary"]["strong_or_optional_human_blocker_count"],
            "claim_gate_overall_status": payload["summary"]["claim_gate_overall_status"],
            "claim_gate_required_failure_count": payload["summary"]["claim_gate_required_failure_count"],
            "claim_gate_optional_failure_count": payload["summary"]["claim_gate_optional_failure_count"],
            "pre_human_handoff_status": payload["summary"]["pre_human_handoff_status"],
            "pre_human_handoff_checks": payload["summary"]["pre_human_handoff_checks"],
            "required_human_return_files": payload["summary"]["required_human_return_files"],
            "present_human_return_files": payload["summary"]["present_human_return_files"],
            "master_return_files": payload["summary"]["master_return_files"],
            "master_return_files_present": payload["summary"]["master_return_files_present"],
            "method_module_count": payload["summary"]["method_module_count"],
            "method_modules_missing_required": payload["summary"]["method_modules_missing_required"],
            "claim_status": PUBLIC_SAFE_CLAIM_STATUS,
        },
        "human_blocker_ids": payload["actual_human_blockers"],
        "public_audit_rows": public_rows,
        "source_artifact_roles": sorted(payload["source_artifacts"]),
    }


def build_payload(exp_dir, outputs_dir, plan_file):
    exp_dir = Path(exp_dir)
    outputs_dir = Path(outputs_dir)
    plan_file = Path(plan_file)
    release_dir = exp_dir / "06_release"
    compliance_path = release_dir / "eacl_plan_compliance_matrix.json"
    claim_gate_path = release_dir / "claim_gate_report.json"
    prehuman_path = release_dir / "pre_human_handoff_validation.json"
    completion_path = release_dir / "submission_completion_audit_ko.json"
    readiness_path = release_dir / "paper_readiness_checklist.json"
    returns_path = exp_dir / "05_review/human_review_master_return_files.csv"

    compliance = read_json(compliance_path, {}) or {}
    claim_gate = read_json(claim_gate_path, {}) or {}
    prehuman = read_json(prehuman_path, {}) or {}
    effective_prehuman = effective_prehuman_summary(prehuman)
    completion = read_json(completion_path, {}) or {}
    readiness = read_json(readiness_path, {}) or {}
    master_returns = read_csv(returns_path)
    audit_rows = build_audit_rows(compliance)
    module_rows = method_rows(compliance)

    proof_counts = Counter(row["proof_state"] for row in audit_rows)
    status_counts = Counter(row["status"] for row in audit_rows)
    completion_proven_count = sum(1 for row in audit_rows if row["completion_proven"] == "yes")
    human_blocked_rows = [row for row in audit_rows if row["human_blocked"] == "yes"]
    minimum_blockers = [row for row in human_blocked_rows if row["scope"] == "minimum_accept"]
    strong_blockers = [row for row in human_blocked_rows if row["scope"] == "strong_accept"]
    missing_evidence_rows = [row for row in audit_rows if row["missing_evidence_files"]]

    expected_minimum_blocker_ids = ["min.gold_chunks", "min.gold_items", "min.iaa", "min.proposed"]
    expected_strong_blocker_ids = [
        "strong.gold_chunks",
        "strong.gold_items",
        "strong.mapping_downstream",
        "strong.active_review",
    ]
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "claim_status": CLAIM_STATUS,
        "experiment_dir": rel(exp_dir),
        "outputs_dir": rel(outputs_dir),
        "plan_file": rel(plan_file),
        "completion_decision": {
            "plan_completion_proven": False,
            "submission_ready": False,
            "reason": "The revised plan's automatic scaffolds are ready, but required human-gold, IAA, adjudication, proposed human-gold scoring, and expert/effort evidence are missing.",
        },
        "summary": {
            "checklist_item_count": len(audit_rows),
            "checklist_status_counts": dict(status_counts),
            "proof_state_counts": dict(proof_counts),
            "completion_proven_item_count": completion_proven_count,
            "human_blocked_item_count": len(human_blocked_rows),
            "minimum_human_blocker_count": len(minimum_blockers),
            "strong_or_optional_human_blocker_count": len(strong_blockers),
            "missing_evidence_row_count": len(missing_evidence_rows),
            "claim_gate_overall_status": claim_gate.get("overall_status"),
            "claim_gate_required_failure_count": claim_gate.get("required_failure_count"),
            "claim_gate_optional_failure_count": claim_gate.get("optional_failure_count"),
            "pre_human_handoff_status": effective_prehuman.get("overall_status"),
            "pre_human_handoff_checks": effective_prehuman.get("check_count"),
            "pre_human_handoff_status_counts": effective_prehuman.get("status_counts"),
            "required_human_return_files": (completion.get("summary") or {}).get("required_human_return_files"),
            "present_human_return_files": (completion.get("summary") or {}).get("present_human_return_files"),
            "master_return_files": (completion.get("summary") or {}).get("master_return_files"),
            "master_return_files_present": (completion.get("summary") or {}).get("master_return_files_present"),
            "method_module_count": len(module_rows),
            "method_modules_missing_required": sum(1 for row in module_rows if int(row.get("missing_required") or 0) > 0),
            "readiness_minimum_items": len(readiness.get("minimum_accept_checklist") or []),
            "readiness_strong_items": len(readiness.get("strong_accept_checklist") or []),
            "claim_status": CLAIM_STATUS,
        },
        "expected_human_blockers": {
            "minimum_accept": expected_minimum_blocker_ids,
            "strong_or_optional": expected_strong_blocker_ids,
        },
        "actual_human_blockers": {
            "minimum_accept": [row["id"] for row in minimum_blockers],
            "strong_or_optional": [row["id"] for row in strong_blockers],
        },
        "audit_rows": audit_rows,
        "method_module_rows": module_rows,
        "missing_evidence_rows": missing_evidence_rows,
        "first_missing_return_files": first_missing_return_rows(master_returns),
        "source_artifacts": {
            "eacl_plan_compliance_matrix": rel(compliance_path),
            "claim_gate_report": rel(claim_gate_path),
            "pre_human_handoff_validation": rel(prehuman_path),
            "submission_completion_audit": rel(completion_path),
            "paper_readiness_checklist": rel(readiness_path),
            "human_review_master_return_files": rel(returns_path),
        },
    }
    return payload


def md_value(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value).replace("|", "\\|").replace("\n", " ")


def md_table(headers, rows):
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(md_value(row.get(header, "")) for header in headers) + " |")
    return "\n".join(lines)


def build_report(payload):
    summary = payload["summary"]
    lines = [
        "# CAPE-KG Revised Plan Completion Audit",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Plan file: `{payload['plan_file']}`",
        "",
        "This audit is a completion-proof artifact for the revised EACL plan. It does not mark the project complete; it records which plan requirements are proven by current artifacts and which remain blocked by human evidence.",
        "",
        "## Completion Decision",
        "",
        f"- Claim status: `{payload['claim_status']}`",
        f"- Plan completion proven: `{payload['completion_decision']['plan_completion_proven']}`",
        f"- Submission ready: `{payload['completion_decision']['submission_ready']}`",
        f"- Reason: {payload['completion_decision']['reason']}",
        "",
        "## Summary",
        "",
        md_table(
            ["metric", "value"],
            [
                {"metric": "checklist_item_count", "value": summary["checklist_item_count"]},
                {"metric": "completion_proven_item_count", "value": summary["completion_proven_item_count"]},
                {"metric": "human_blocked_item_count", "value": summary["human_blocked_item_count"]},
                {"metric": "minimum_human_blocker_count", "value": summary["minimum_human_blocker_count"]},
                {"metric": "strong_or_optional_human_blocker_count", "value": summary["strong_or_optional_human_blocker_count"]},
                {"metric": "missing_evidence_row_count", "value": summary["missing_evidence_row_count"]},
                {"metric": "claim_gate_overall_status", "value": summary["claim_gate_overall_status"]},
                {"metric": "pre_human_handoff_status", "value": summary["pre_human_handoff_status"]},
                {"metric": "pre_human_handoff_checks", "value": summary["pre_human_handoff_checks"]},
                {"metric": "required_human_return_files", "value": summary["required_human_return_files"]},
                {"metric": "present_human_return_files", "value": summary["present_human_return_files"]},
                {"metric": "method_modules_missing_required", "value": summary["method_modules_missing_required"]},
            ],
        ),
        "",
        "## Expected Human Blockers",
        "",
        md_table(
            ["blocker_group", "ids"],
            [
                {"blocker_group": "minimum_accept", "ids": ", ".join(payload["actual_human_blockers"]["minimum_accept"])},
                {"blocker_group": "strong_or_optional", "ids": ", ".join(payload["actual_human_blockers"]["strong_or_optional"])},
            ],
        ),
        "",
        "## Plan Checklist Audit",
        "",
        md_table(
            [
                "scope",
                "id",
                "status",
                "claimable",
                "proof_state",
                "completion_proven",
                "human_blocked",
                "evidence_files_present",
                "next_step",
            ],
            payload["audit_rows"],
        ),
        "",
        "## Method Module Audit",
        "",
        md_table(
            ["module", "name", "status", "required_artifacts", "missing_required", "human_dependent", "proof_state"],
            payload["method_module_rows"],
        ),
        "",
        "## First Missing Return Files",
        "",
        md_table(
            ["required_for_minimum", "task_type", "owner", "batch_or_group", "expected_rows", "reviewed_file", "status"],
            payload["first_missing_return_files"],
        ),
        "",
        "## Source Artifacts",
        "",
    ]
    for label, path in payload["source_artifacts"].items():
        lines.append(f"- `{label}`: `{path}`")
    return "\n".join(lines) + "\n"


def build_public_safe_report(payload):
    summary = payload["summary"]
    lines = [
        "# CAPE-KG Public-Safe Revised Plan Completion Audit",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Plan file: `{payload['plan_file']}`",
        "",
        "This public-safe audit exposes completion status, counts, and generic next steps without source text, private review paths, or reviewed file names.",
        "",
        "## Public Safety",
        "",
        f"- Claim status: `{payload['claim_status']}`",
        f"- Source text included: `{payload['public_safety']['source_text_included']}`",
        f"- Private review paths included: `{payload['public_safety']['private_review_paths_included']}`",
        f"- Reviewed file names included: `{payload['public_safety']['reviewed_file_names_included']}`",
        "",
        "## Completion Decision",
        "",
        f"- Plan completion proven: `{payload['completion_decision']['plan_completion_proven']}`",
        f"- Submission ready: `{payload['completion_decision']['submission_ready']}`",
        f"- Reason: {payload['completion_decision']['reason']}",
        "",
        "## Summary",
        "",
        md_table(
            ["metric", "value"],
            [
                {"metric": "checklist_item_count", "value": summary["checklist_item_count"]},
                {"metric": "completion_proven_item_count", "value": summary["completion_proven_item_count"]},
                {"metric": "human_blocked_item_count", "value": summary["human_blocked_item_count"]},
                {"metric": "minimum_human_blocker_count", "value": summary["minimum_human_blocker_count"]},
                {"metric": "strong_or_optional_human_blocker_count", "value": summary["strong_or_optional_human_blocker_count"]},
                {"metric": "claim_gate_overall_status", "value": summary["claim_gate_overall_status"]},
                {"metric": "pre_human_handoff_status", "value": summary["pre_human_handoff_status"]},
                {"metric": "pre_human_handoff_checks", "value": summary["pre_human_handoff_checks"]},
                {"metric": "required_human_return_files", "value": summary["required_human_return_files"]},
                {"metric": "present_human_return_files", "value": summary["present_human_return_files"]},
                {"metric": "method_modules_missing_required", "value": summary["method_modules_missing_required"]},
            ],
        ),
        "",
        "## Public Audit Rows",
        "",
        md_table(
            [
                "scope",
                "id",
                "status",
                "claimable",
                "proof_state",
                "completion_proven",
                "human_blocked",
                "evidence_category",
                "public_next_step",
            ],
            payload["public_audit_rows"],
        ),
        "",
        "## Source Artifact Roles",
        "",
    ]
    for role in payload["source_artifact_roles"]:
        lines.append(f"- `{role}`")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--outputs-dir", default=str(DEFAULT_OUTPUTS_DIR))
    parser.add_argument("--plan-file", default=str(DEFAULT_PLAN_FILE))
    args = parser.parse_args()

    exp_dir = Path(args.experiment_dir)
    release_dir = exp_dir / "06_release"
    payload = build_payload(exp_dir, Path(args.outputs_dir), Path(args.plan_file))
    json_path = release_dir / "revised_plan_completion_audit.json"
    md_path = release_dir / "revised_plan_completion_audit.md"
    csv_path = release_dir / "revised_plan_completion_audit_items.csv"
    public_json_path = release_dir / "revised_plan_completion_audit_public_safe.json"
    public_md_path = release_dir / "revised_plan_completion_audit_public_safe.md"
    public_csv_path = release_dir / "revised_plan_completion_audit_public_safe_items.csv"
    public_payload = build_public_safe_payload(payload)
    write_json(json_path, payload)
    write_text(md_path, build_report(payload))
    write_csv(
        csv_path,
        payload["audit_rows"],
        [
            "scope",
            "id",
            "requirement",
            "status",
            "claimable",
            "automation_state",
            "proof_state",
            "completion_proven",
            "human_blocked",
            "evidence_file_count",
            "evidence_files_present",
            "missing_evidence_files",
            "evidence",
            "next_step",
        ],
    )
    write_json(public_json_path, public_payload)
    write_text(public_md_path, build_public_safe_report(public_payload))
    write_csv(
        public_csv_path,
        public_payload["public_audit_rows"],
        [
            "scope",
            "id",
            "requirement",
            "status",
            "claimable",
            "proof_state",
            "completion_proven",
            "human_blocked",
            "evidence_category",
            "public_next_step",
        ],
    )
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print(f"Wrote {csv_path}")
    print(f"Wrote {public_json_path}")
    print(f"Wrote {public_md_path}")
    print(f"Wrote {public_csv_path}")


if __name__ == "__main__":
    main()
