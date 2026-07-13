#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate CAPE-KG artifacts before starting human review."""

import argparse
import csv
import hashlib
import json
import re
import tarfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_OUTPUTS_DIR = Path("outputs")

KNOWN_HUMAN_PENDING_STATUS = "pending_human_gold_iaa_and_human_gold_scoring"
REQUIRED_HANDOFF_BUNDLES = {
    "annotator_A",
    "annotator_B",
    "coordinator",
    "adjudicator",
    "mapping_expert",
    "crosswalk_expert",
    "active_review_effort",
    "structural_reviewer",
}
PUBLIC_SAFE_FORBIDDEN_PATTERNS = (
    "01_data/",
    "05_review/human_gold_batches/",
    "06_release/annotation_roundtrip_smoke/",
    "06_release/active_review_effort_roundtrip_smoke/",
    "06_release/mapping_roundtrip_smoke/",
    "06_release/crosswalk_roundtrip_smoke/",
    "06_release/human_review_handoff/",
    "06_release/human_review_packet_integrity",
    "annotation_workbench.html",
    "build_cape_human_review_packet_integrity_report.py",
    "mapping_review_workbench.html",
    "gold_annotation_template.jsonl",
    "evaluation_chunks.jsonl",
    "annotator_",
    "adjudication.jsonl",
    "adjudication_draft.jsonl",
)
ALLOWED_RETURN_PREFLIGHT_STATUSES = {
    "pending_human_returns",
    "partial_returns_validated",
    "annotation_returns_ready_mapping_pending",
    "annotation_and_mapping_returns_ready",
    "annotation_returns_ready_adjudication_pending",
    "annotation_returns_ready_adjudication_validated_or_pending",
    "annotation_and_adjudication_returns_ready_optional_pending",
    "annotation_and_mapping_returns_ready_active_pending",
    "all_human_returns_ready",
}
ALLOWED_STRONG_RETURN_PREFLIGHT_STATUSES = {
    "pending_strong_human_returns",
    "partial_strong_returns_validated",
    "strong_annotation_returns_ready_adjudication_pending",
    "strong_annotation_and_adjudication_returns_ready",
}
TRACEABILITY_EXPECTED_CONDITIONS = {
    "B0_plain_llm",
    "B1_predicate_constrained",
    "B2_current_project",
    "B3_edc_style",
    "B4_taxonomy_rag",
    "B5_procedural_prompt",
    "B6_sac_kg_verifier_pruner",
    "P_cape_kg_actual",
    "P_minus_CQ",
    "P_minus_Evidence",
    "P_minus_Procedural_schema",
    "P_minus_Schema_retrieval",
    "P_minus_Standard_bridge",
    "P_minus_Validator",
}
TRACEABILITY_RUNTIME_ONLY_CONDITIONS = {
    "P_minus_CQ",
    "P_minus_Evidence",
    "P_minus_Procedural_schema",
    "P_minus_Validator",
    "P_minus_Standard_bridge",
}
EXPECTED_PROTOCOL_PRIVATE_INPUTS = {
    "evaluation_chunk_selection_120": "experiments/cape_kg_eacl_20260627/01_data/evaluation_chunks.jsonl",
    "gold_candidate_template_120": "experiments/cape_kg_eacl_20260627/01_data/gold_annotation_template.jsonl",
    "minimum_gold_package_a": "experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/annotator_A.jsonl",
    "minimum_gold_package_b": "experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/annotator_B.jsonl",
    "minimum_gold_resolution_template": "experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/adjudication.jsonl",
    "mapping_review_candidate_pool": "experiments/cape_kg_eacl_20260627/01_data/mapping_review/mapping_review_items.jsonl",
}
EVALUATION_PROTOCOL_STABLE_KEYS = [
    "protocol_version",
    "metric_definitions",
    "condition_sets",
    "claim_gate_policy",
    "locked_public_files",
    "locked_private_input_ids",
    "evaluation_commands",
]
STALE_REPORT_VALIDATION_PATTERNS = (
    "Pre-human checks: 60",
    "Checks: 60",
    "60 checks",
    "59 PASS",
    "59 / 1 WARN",
    "59 PASS / 1 WARN",
    "59 PASS, 1 WARN",
    "Pre-human checks: 59",
    "Checks: 59",
    "59 checks",
    "58 PASS",
    "58 / 1 WARN",
    "58 PASS / 1 WARN",
    "58 PASS, 1 WARN",
    "Pre-human checks: 58",
    "Checks: 58",
    "58 checks",
    "57 PASS",
    "57 / 1 WARN",
    "57 PASS / 1 WARN",
    "57 PASS, 1 WARN",
    "Pre-human checks: 57",
    "Checks: 57",
    "57 checks",
    "56 PASS",
    "56 / 1 WARN",
    "56 PASS / 1 WARN",
    "56 PASS, 1 WARN",
    "Pre-human checks: 54",
    "Checks: 54",
    "54 checks",
    "54 PASS",
    "54 / 1 WARN",
    "53 PASS / 1 WARN",
    "53 PASS, 1 WARN",
    "Pre-human checks: 53",
    "Checks: 53",
    "53 checks",
    "53 PASS",
    "53 / 1 WARN",
    "52 PASS / 1 WARN",
    "52 PASS, 1 WARN",
    "pre_human_check_count | `53`",
    "{'PASS': 53, 'WARN': 1}",
    '{"PASS": 53, "WARN": 1}',
    "Pre-human checks: 52",
    "Checks: 52",
    "52 checks",
    "52 PASS",
    "52 / 1 WARN",
    "51 PASS / 1 WARN",
    "51 PASS, 1 WARN",
    "Pre-human checks: 51",
    "51 checks",
    "50 PASS",
    "50 / 1 WARN",
    "Pre-human checks: 50",
    "50 checks",
    "49 PASS",
    "49 / 1 WARN",
    "Pre-human checks: 49",
    "49 checks",
    "Pre-human checks: 48",
    "Checks: 48",
    "48 checks",
    "48 PASS",
    "48 / 1 WARN",
    "47 PASS",
    "47 / 1 WARN",
    "47 checks",
    "46 PASS",
    "46 checks",
    "45 PASS",
    "45 checks",
    "44 PASS",
    "44 checks",
    "43 PASS",
    "43 checks",
    "42 PASS",
    "42 checks",
    "41 PASS",
    "41 checks",
    "40 PASS",
    "40 checks",
    "39 PASS",
    "20 PASS / 1 WARN",
    "20 checks:",
    "21 checks:",
    "19 PASS, 1 WARN",
    "PASS, 20 PASS",
    "PASS, 34 checks",
    "39 checks",
    "38 PASS",
    "38 checks",
    "37 PASS",
    "37 checks",
    "36 PASS",
    "36 checks",
    "35 PASS",
    "35 checks",
    "34 PASS",
    "33 PASS",
)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_jsonl(path):
    rows = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            row["_line_no"] = line_no
            rows.append(row)
    return rows


def read_csv_rows(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def as_list(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_hash(payload):
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def rel(path):
    return str(Path(path).as_posix())


def effective_prehuman_summary(prehuman):
    """Return the stable pre-human summary expected after this validator rewrites its own output."""
    if prehuman.get("overall_status") == "FAIL":
        status_counts = dict(prehuman.get("status_counts") or {})
        pass_count = int(status_counts.get("PASS") or 0) + int(status_counts.get("FAIL") or 0)
        effective_counts = {"PASS": pass_count}
        if status_counts.get("WARN"):
            effective_counts["WARN"] = int(status_counts.get("WARN") or 0)
        return {
            "overall_status": "PASS",
            "check_count": prehuman.get("check_count") or sum(effective_counts.values()),
            "status_counts": effective_counts,
        }
    return {
        "overall_status": prehuman.get("overall_status"),
        "check_count": prehuman.get("check_count"),
        "status_counts": prehuman.get("status_counts"),
    }


def add_check(checks, check_id, status, detail, evidence=None):
    checks.append(
        {
            "id": check_id,
            "status": status,
            "detail": detail,
            "evidence": evidence or {},
        }
    )


def truthy_present(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"yes", "true", "1", "present"}
    return bool(value)


def check_required_files(checks, paths, root=None):
    missing = []
    for path in paths:
        path = Path(path)
        if root is not None:
            path = root / path
        if not path.exists():
            missing.append(rel(path))
    if missing:
        add_check(checks, "required_files_present", "FAIL", "Required files are missing.", {"missing": missing})
    else:
        add_check(checks, "required_files_present", "PASS", "All required files are present.", {"count": len(paths)})


def parse_checksum_lines(path):
    rows = []
    for line_no, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            rows.append({"line_no": line_no, "error": "cannot_parse", "raw": line})
            continue
        digest, item_path = parts
        rows.append({"line_no": line_no, "sha256": digest, "path": item_path.strip()})
    return rows


def validate_checksum_file(checks, check_id, path):
    path = Path(path)
    if not path.exists():
        add_check(checks, check_id, "FAIL", "Checksum file is missing.", {"path": rel(path)})
        return

    rows = parse_checksum_lines(path)
    issues = []
    for row in rows:
        if "error" in row:
            issues.append(row)
            continue
        item = Path(row["path"])
        if not item.exists():
            issues.append({"path": row["path"], "error": "missing_file"})
            continue
        actual = sha256_file(item)
        if actual != row["sha256"]:
            issues.append({"path": row["path"], "error": "sha256_mismatch", "expected": row["sha256"], "actual": actual})
    if issues:
        add_check(checks, check_id, "FAIL", "Checksum verification failed.", {"path": rel(path), "issues": issues[:20]})
    else:
        add_check(checks, check_id, "PASS", "Checksum verification passed.", {"path": rel(path), "rows": len(rows)})


def validate_claim_state(checks, exp_dir):
    claim_path = exp_dir / "06_release/claim_gate_report.json"
    readiness_path = exp_dir / "06_release/submission_readiness_audit.json"
    try:
        claim = read_json(claim_path)
        readiness = read_json(readiness_path)
    except Exception as exc:
        add_check(checks, "claim_state_readable", "FAIL", "Claim/readiness JSON cannot be read.", {"error": str(exc)})
        return

    add_check(
        checks,
        "claim_gate_known_human_blockers",
        "WARN",
        "Submission claims are still pending human gold, IAA, adjudication, and human-gold scoring.",
        {
            "claim_gate_overall_status": claim.get("overall_status"),
            "readiness_claim_status": readiness.get("claim_status"),
            "expected_pending_status": KNOWN_HUMAN_PENDING_STATUS,
            "audited_items": len(readiness.get("items", [])),
        },
    )
    if readiness.get("claim_status") != KNOWN_HUMAN_PENDING_STATUS:
        add_check(
            checks,
            "readiness_status_expected",
            "FAIL",
            "Readiness audit does not match the expected pre-human pending status.",
            {"actual": readiness.get("claim_status")},
        )
    else:
        add_check(
            checks,
            "readiness_status_expected",
            "PASS",
            "Readiness audit is in the expected pre-human pending state.",
            {"claim_status": readiness.get("claim_status")},
        )


def validate_claim_gate_blocker_alignment(checks, exp_dir):
    release_dir = exp_dir / "06_release"
    eval_dir = exp_dir / "04_evaluation"
    claim_path = release_dir / "claim_gate_report.json"
    readiness_path = release_dir / "submission_readiness_audit.json"
    compliance_path = release_dir / "eacl_plan_compliance_matrix.json"
    human_gold_path = eval_dir / "human_gold_validation_summary.json"
    human_gold_metrics_path = eval_dir / "human_gold_metrics.json"
    mapping_metrics_path = eval_dir / "mapping_expert_metrics.json"
    mapping_progress_path = release_dir / "mapping_review_progress_summary.json"
    crosswalk_metrics_path = eval_dir / "crosswalk_expert_metrics.json"
    try:
        claim = read_json(claim_path)
        readiness = read_json(readiness_path)
        compliance = read_json(compliance_path)
        human_gold = read_json(human_gold_path)
        human_gold_metrics = read_json(human_gold_metrics_path)
        mapping_metrics = read_json(mapping_metrics_path)
        mapping_progress = read_json(mapping_progress_path)
        crosswalk_metrics = read_json(crosswalk_metrics_path)
    except Exception as exc:
        add_check(
            checks,
            "claim_gate_blocker_alignment",
            "FAIL",
            "Claim gate or blocker evidence cannot be read.",
            {"error": str(exc), "path": rel(claim_path)},
        )
        return

    expected_required_fail_gates = {
        "gold.completed_chunks",
        "gold.item_count",
        "gold.iaa",
        "llm.proposed_human_gold_score",
    }
    expected_optional_fail_gates = {"mapping.expert_review", "crosswalk.expert_review"}
    expected_pass_gates = {
        "data.eval_chunks",
        "llm.baselines",
        "llm.proposed_generation",
        "llm.ablations",
        "llm.revalidated_output_recovery",
        "llm.strict_json_rate",
        "external.public_subset",
        "analysis.error_analysis",
        "release.artifacts",
    }
    expected_minimum_blockers = {"min.gold_chunks", "min.gold_items", "min.iaa", "min.proposed"}
    expected_strong_or_optional_blockers = {
        "strong.gold_chunks",
        "strong.gold_items",
        "strong.mapping_downstream",
        "strong.active_review",
    }

    gates = claim.get("gates") or []
    gate_by_id = {row.get("gate_id"): row for row in gates}
    required_fail_gates = {
        row.get("gate_id")
        for row in gates
        if row.get("status") == "FAIL" and row.get("required") is True
    }
    optional_fail_gates = {
        row.get("gate_id")
        for row in gates
        if row.get("status") == "FAIL" and row.get("required") is not True
    }
    pass_gates = {row.get("gate_id") for row in gates if row.get("status") == "PASS"}
    readiness_blockers = {row.get("id") for row in readiness.get("blocking_items") or []}
    compliance_minimum_blockers = {
        row.get("id")
        for row in compliance.get("minimum_human_blockers") or []
    }
    compliance_strong_blockers = {
        row.get("id")
        for row in compliance.get("strong_or_optional_human_blockers") or []
    }
    issues = []

    if claim.get("overall_status") != "FAIL":
        issues.append({"error": "unexpected_claim_gate_overall_status", "actual": claim.get("overall_status")})
    if claim.get("required_failure_count") != len(expected_required_fail_gates):
        issues.append(
            {
                "error": "unexpected_required_failure_count",
                "expected": len(expected_required_fail_gates),
                "actual": claim.get("required_failure_count"),
            }
        )
    if claim.get("optional_failure_count") != len(expected_optional_fail_gates):
        issues.append(
            {
                "error": "unexpected_optional_failure_count",
                "expected": len(expected_optional_fail_gates),
                "actual": claim.get("optional_failure_count"),
            }
        )
    if claim.get("warning_count") != 0:
        issues.append({"error": "unexpected_warning_count", "actual": claim.get("warning_count")})
    if required_fail_gates != expected_required_fail_gates:
        issues.append(
            {
                "error": "required_fail_gates_mismatch",
                "expected": sorted(expected_required_fail_gates),
                "actual": sorted(required_fail_gates),
            }
        )
    if optional_fail_gates != expected_optional_fail_gates:
        issues.append(
            {
                "error": "optional_fail_gates_mismatch",
                "expected": sorted(expected_optional_fail_gates),
                "actual": sorted(optional_fail_gates),
            }
        )
    missing_pass_gates = sorted(expected_pass_gates - pass_gates)
    if missing_pass_gates:
        issues.append({"error": "expected_pass_gates_not_passing", "gate_ids": missing_pass_gates})
    if readiness_blockers != expected_minimum_blockers:
        issues.append(
            {
                "error": "readiness_blockers_mismatch",
                "expected": sorted(expected_minimum_blockers),
                "actual": sorted(readiness_blockers),
            }
        )
    if compliance_minimum_blockers != expected_minimum_blockers:
        issues.append(
            {
                "error": "compliance_minimum_blockers_mismatch",
                "expected": sorted(expected_minimum_blockers),
                "actual": sorted(compliance_minimum_blockers),
            }
        )
    if compliance_strong_blockers != expected_strong_or_optional_blockers:
        issues.append(
            {
                "error": "compliance_strong_blockers_mismatch",
                "expected": sorted(expected_strong_or_optional_blockers),
                "actual": sorted(compliance_strong_blockers),
            }
        )

    if human_gold.get("claim_status") != "pending_human_adjudication":
        issues.append({"error": "unexpected_human_gold_claim_status", "actual": human_gold.get("claim_status")})
    if human_gold.get("total_rows") != 120 or human_gold.get("unique_chunks") != 120:
        issues.append(
            {
                "error": "unexpected_human_gold_chunk_pool",
                "total_rows": human_gold.get("total_rows"),
                "unique_chunks": human_gold.get("unique_chunks"),
            }
        )
    if human_gold.get("completed_adjudicated_chunks") != 0:
        issues.append({"error": "human_gold_completed_chunks_unexpectedly_nonzero", "actual": human_gold.get("completed_adjudicated_chunks")})
    if human_gold.get("gold_item_count_for_readiness") != 0:
        issues.append({"error": "human_gold_item_count_unexpectedly_nonzero", "actual": human_gold.get("gold_item_count_for_readiness")})
    if human_gold.get("validation_error_count") != 0:
        issues.append({"error": "human_gold_validation_errors", "actual": human_gold.get("validation_error_count")})
    if human_gold_metrics.get("claim_status") != "pending_human_adjudication":
        issues.append({"error": "unexpected_human_gold_metrics_claim_status", "actual": human_gold_metrics.get("claim_status")})
    if human_gold_metrics.get("metrics") not in ([], None):
        issues.append({"error": "human_gold_metrics_should_be_empty_pre_adjudication", "actual_count": len(human_gold_metrics.get("metrics") or [])})

    if mapping_metrics.get("claim_status") != "pending_or_partial_expert_review":
        issues.append({"error": "unexpected_mapping_metrics_claim_status", "actual": mapping_metrics.get("claim_status")})
    mapping_rows = mapping_metrics.get("metrics") or []
    if len(mapping_rows) != 2:
        issues.append({"error": "unexpected_mapping_metric_rows", "actual": len(mapping_rows)})
    for row in mapping_rows:
        if row.get("completed_rows") != 0 or row.get("pending_rows") != 110:
            issues.append(
                {
                    "error": "unexpected_mapping_metric_row_completion",
                    "standard": row.get("standard"),
                    "completed_rows": row.get("completed_rows"),
                    "pending_rows": row.get("pending_rows"),
                }
            )
        for metric_name in ["hit_at_1", "hit_at_3", "hit_at_5", "precision_at_5", "mrr", "ndcg_at_10"]:
            if row.get(metric_name) != "pending_expert_review":
                issues.append(
                    {
                        "error": "mapping_metric_unexpectedly_claimable",
                        "standard": row.get("standard"),
                        "metric": metric_name,
                        "actual": row.get(metric_name),
                    }
                )
    if mapping_progress.get("pending_rows") != 220 or mapping_progress.get("complete_source_groups") != 0:
        issues.append(
            {
                "error": "unexpected_mapping_progress",
                "pending_rows": mapping_progress.get("pending_rows"),
                "complete_source_groups": mapping_progress.get("complete_source_groups"),
            }
        )
    if mapping_progress.get("claim_status") != "pending_or_partial_expert_review":
        issues.append({"error": "unexpected_mapping_progress_claim_status", "actual": mapping_progress.get("claim_status")})

    crosswalk = crosswalk_metrics.get("metrics") or {}
    if crosswalk_metrics.get("claim_status") != "pending_crosswalk_expert_review":
        issues.append({"error": "unexpected_crosswalk_metrics_claim_status", "actual": crosswalk_metrics.get("claim_status")})
    if crosswalk.get("candidate_rows") != 220 or crosswalk.get("source_task_count") != 22:
        issues.append(
            {
                "error": "unexpected_crosswalk_candidate_pool",
                "candidate_rows": crosswalk.get("candidate_rows"),
                "source_task_count": crosswalk.get("source_task_count"),
            }
        )
    if crosswalk.get("completed_rows") != 0 or crosswalk.get("pending_rows") != 220:
        issues.append(
            {
                "error": "unexpected_crosswalk_completion",
                "completed_rows": crosswalk.get("completed_rows"),
                "pending_rows": crosswalk.get("pending_rows"),
            }
        )
    for metric_name in ["expert_accept_rate", "hit_at_1", "hit_at_3", "hit_at_5", "precision_at_10", "mrr", "ndcg_at_10"]:
        if crosswalk.get(metric_name) != "pending_crosswalk_expert_review":
            issues.append(
                {
                    "error": "crosswalk_metric_unexpectedly_claimable",
                    "metric": metric_name,
                    "actual": crosswalk.get(metric_name),
                }
            )

    for gate_id in expected_required_fail_gates | expected_optional_fail_gates | expected_pass_gates:
        if gate_id not in gate_by_id:
            issues.append({"error": "missing_claim_gate", "gate_id": gate_id})

    if issues:
        add_check(
            checks,
            "claim_gate_blocker_alignment",
            "FAIL",
            "Claim gate failures are not aligned with current human/expert blocker evidence.",
            {"path": rel(claim_path), "issues": issues[:80]},
        )
        return

    add_check(
        checks,
        "claim_gate_blocker_alignment",
        "PASS",
        "Claim gate FAIL/PASS states are aligned with readiness blockers, human-gold pending state, and mapping expert pending state.",
        {
            "path": rel(claim_path),
            "required_fail_gates": sorted(expected_required_fail_gates),
            "optional_fail_gates": sorted(expected_optional_fail_gates),
            "minimum_blockers": sorted(expected_minimum_blockers),
            "strong_or_optional_blockers": sorted(expected_strong_or_optional_blockers),
        },
    )


def validate_requirements_matrix(checks, exp_dir):
    matrix_path = exp_dir / "00_plan/requirements_matrix.json"
    matrix_md_path = exp_dir / "00_plan/requirements_matrix.md"
    readiness_path = exp_dir / "06_release/submission_readiness_audit.json"
    try:
        matrix = read_json(matrix_path)
        readiness = read_json(readiness_path)
    except Exception as exc:
        add_check(
            checks,
            "requirements_matrix_traceability",
            "FAIL",
            "Requirements matrix or readiness audit cannot be read.",
            {"error": str(exc)},
        )
        return

    matrix_items = matrix.get("traceability_items") or []
    readiness_items = readiness.get("items") or []
    matrix_ids = [row.get("id") for row in matrix_items]
    readiness_ids = [row.get("id") for row in readiness_items]
    matrix_blocking_ids = [row.get("id") for row in matrix.get("blocking_items") or []]
    readiness_blocking_ids = [row.get("id") for row in readiness.get("blocking_items") or []]
    issues = []
    if matrix.get("status") != readiness.get("claim_status"):
        issues.append(
            {
                "error": "status_mismatch",
                "matrix_status": matrix.get("status"),
                "readiness_claim_status": readiness.get("claim_status"),
            }
        )
    if matrix_ids != readiness_ids:
        issues.append(
            {
                "error": "traceability_item_ids_mismatch",
                "matrix_ids": matrix_ids,
                "readiness_ids": readiness_ids,
            }
        )
    if matrix_blocking_ids != readiness_blocking_ids:
        issues.append(
            {
                "error": "blocking_item_ids_mismatch",
                "matrix_blocking_ids": matrix_blocking_ids,
                "readiness_blocking_ids": readiness_blocking_ids,
            }
        )
    if not matrix_md_path.exists() or "Traceability Table" not in matrix_md_path.read_text(encoding="utf-8"):
        issues.append({"error": "requirements_matrix_markdown_missing_traceability_table", "path": rel(matrix_md_path)})

    if issues:
        add_check(
            checks,
            "requirements_matrix_traceability",
            "FAIL",
            "Requirements matrix is not synchronized with the submission readiness audit.",
            {"path": rel(matrix_path), "issues": issues},
        )
        return
    add_check(
        checks,
        "requirements_matrix_traceability",
        "PASS",
        "Requirements matrix traceability is synchronized with the submission readiness audit.",
        {
            "path": rel(matrix_path),
            "traceability_items": len(matrix_items),
            "blocking_items": matrix_blocking_ids,
            "claim_status": matrix.get("status"),
        },
    )


def validate_eacl_plan_compliance_matrix(checks, exp_dir):
    compliance_path = exp_dir / "06_release/eacl_plan_compliance_matrix.json"
    compliance_md_path = exp_dir / "06_release/eacl_plan_compliance_matrix.md"
    readiness_path = exp_dir / "06_release/submission_readiness_audit.json"
    prehuman_path = exp_dir / "06_release/pre_human_handoff_validation.json"
    try:
        compliance = read_json(compliance_path)
        readiness = read_json(readiness_path)
        prehuman = read_json(prehuman_path)
    except Exception as exc:
        add_check(
            checks,
            "eacl_plan_compliance_matrix",
            "FAIL",
            "EACL plan compliance matrix or readiness audit cannot be read.",
            {"error": str(exc)},
        )
        return

    rows = compliance.get("checklist_rows") or []
    readiness_items = readiness.get("items") or []
    compliance_ids = [row.get("id") for row in rows]
    readiness_ids = [row.get("id") for row in readiness_items]
    compliance_status_by_id = {row.get("id"): row.get("status") for row in rows}
    readiness_status_by_id = {row.get("id"): row.get("status") for row in readiness_items}
    issues = []
    if compliance.get("summary", {}).get("claim_status") != readiness.get("claim_status"):
        issues.append(
            {
                "error": "claim_status_mismatch",
                "compliance_claim_status": compliance.get("summary", {}).get("claim_status"),
                "readiness_claim_status": readiness.get("claim_status"),
            }
        )
    if compliance_ids != readiness_ids:
        issues.append({"error": "checklist_item_ids_mismatch", "compliance_ids": compliance_ids, "readiness_ids": readiness_ids})
    if compliance_status_by_id != readiness_status_by_id:
        issues.append(
            {
                "error": "checklist_status_mismatch",
                "compliance_status_by_id": compliance_status_by_id,
                "readiness_status_by_id": readiness_status_by_id,
            }
        )
    summary = compliance.get("summary") or {}
    previous_prehuman_failed = prehuman.get("overall_status") == "FAIL"
    for field, expected in [
        ("pre_human_handoff_status", prehuman.get("overall_status")),
        ("pre_human_handoff_checks", prehuman.get("check_count")),
        ("pre_human_handoff_status_counts", prehuman.get("status_counts")),
    ]:
        if summary.get(field) != expected:
            if previous_prehuman_failed:
                continue
            issues.append(
                {
                    "error": "pre_human_summary_mismatch",
                    "field": field,
                    "expected": expected,
                    "actual": summary.get(field),
                }
            )
    source_artifacts = compliance.get("source_artifacts") or {}
    for key in [
        "requirements_matrix",
        "submission_completion_audit",
        "paper_readiness_checklist",
        "human_review_master_return_files",
        "pre_human_handoff_validation",
        "provenance_manifest",
        "provenance_prov_o_summary",
        "rdf_shacl_validation",
        "release_bundle_checksums",
    ]:
        path = source_artifacts.get(key)
        if not path:
            issues.append({"error": "missing_source_artifact_entry", "key": key})
        elif not Path(path).exists():
            issues.append({"error": "source_artifact_missing_on_disk", "key": key, "path": path})
    for field, expected in [
        ("minimum_paper_gate_return_file_count", 11),
        ("optional_strong_return_file_count", 3),
        ("tracked_human_return_file_count", 14),
        ("required_human_return_file_count", 14),
        ("master_optional_claim_return_file_count", 3),
        ("master_optional_structural_return_file_count", 2),
        ("master_required_claim_return_file_count", 14),
        ("master_return_file_count", 16),
    ]:
        if summary.get(field) != expected:
            issues.append(
                {
                    "error": "return_file_count_mismatch",
                    "field": field,
                    "expected": expected,
                    "actual": summary.get(field),
                }
            )
    if not compliance_md_path.exists():
        issues.append({"error": "missing_markdown", "path": rel(compliance_md_path)})
    else:
        text = compliance_md_path.read_text(encoding="utf-8")
        for pattern in [
            "## Plan Checklist",
            "## Method Modules M1-M11",
            "RDF/SHACL-style validation",
            "Optional/strong claim return files",
            "Optional structural review files",
            "All master return files",
            "## Master Human Return Files",
        ]:
            if pattern not in text:
                issues.append({"error": "missing_markdown_pattern", "pattern": pattern})

    if issues:
        add_check(
            checks,
            "eacl_plan_compliance_matrix",
            "FAIL",
            "EACL plan compliance matrix is not synchronized with current readiness evidence.",
            {"path": rel(compliance_path), "issues": issues},
        )
        return
    add_check(
        checks,
        "eacl_plan_compliance_matrix",
        "PASS",
        "EACL plan compliance matrix is synchronized with readiness audit item IDs/statuses and current source artifacts.",
        {
            "path": rel(compliance_path),
            "checklist_items": len(rows),
            "human_blocker_count": summary.get("human_blocker_count"),
            "minimum_human_blocker_count": summary.get("minimum_human_blocker_count"),
            "strong_or_optional_human_blocker_count": summary.get("strong_or_optional_human_blocker_count"),
            "pre_human_handoff_status": summary.get("pre_human_handoff_status"),
            "pre_human_handoff_status_counts": summary.get("pre_human_handoff_status_counts"),
        },
    )


def validate_revised_plan_completion_audit(checks, exp_dir):
    release_dir = exp_dir / "06_release"
    json_path = release_dir / "revised_plan_completion_audit.json"
    md_path = release_dir / "revised_plan_completion_audit.md"
    csv_path = release_dir / "revised_plan_completion_audit_items.csv"
    compliance_path = release_dir / "eacl_plan_compliance_matrix.json"
    claim_gate_path = release_dir / "claim_gate_report.json"
    prehuman_path = release_dir / "pre_human_handoff_validation.json"
    expected_status = "revised_plan_not_complete_human_evidence_pending"
    expected_minimum_blockers = {"min.gold_chunks", "min.gold_items", "min.iaa", "min.proposed"}
    expected_strong_blockers = {
        "strong.gold_chunks",
        "strong.gold_items",
        "strong.mapping_downstream",
        "strong.active_review",
    }
    issues = []

    try:
        payload = read_json(json_path)
        csv_rows = read_csv_rows(csv_path)
        compliance = read_json(compliance_path)
        claim_gate = read_json(claim_gate_path)
        prehuman = read_json(prehuman_path)
    except Exception as exc:
        add_check(
            checks,
            "revised_plan_completion_audit",
            "FAIL",
            "Revised plan completion audit artifacts cannot be read.",
            {"json": rel(json_path), "csv": rel(csv_path), "error": str(exc)},
        )
        return

    effective_prehuman = effective_prehuman_summary(prehuman)
    if payload.get("claim_status") != expected_status:
        issues.append({"error": "unexpected_claim_status", "actual": payload.get("claim_status")})
    decision = payload.get("completion_decision") or {}
    if decision.get("plan_completion_proven") is not False:
        issues.append({"error": "plan_completion_should_not_be_proven_pre_human", "actual": decision.get("plan_completion_proven")})
    if decision.get("submission_ready") is not False:
        issues.append({"error": "submission_ready_should_be_false_pre_human", "actual": decision.get("submission_ready")})
    reason = str(decision.get("reason") or "")
    for pattern in ["human-gold", "IAA", "adjudication", "expert"]:
        if pattern not in reason:
            issues.append({"error": "completion_decision_reason_missing_pattern", "pattern": pattern})

    audit_rows = payload.get("audit_rows") or []
    compliance_rows = compliance.get("checklist_rows") or []
    audit_by_id = {row.get("id"): row for row in audit_rows}
    compliance_by_id = {row.get("id"): row for row in compliance_rows}
    if list(audit_by_id) != list(compliance_by_id):
        issues.append({"error": "audit_compliance_ids_mismatch", "audit": list(audit_by_id), "compliance": list(compliance_by_id)})
    for row_id, compliance_row in compliance_by_id.items():
        audit_row = audit_by_id.get(row_id) or {}
        for field in ["scope", "status", "automation_state"]:
            if audit_row.get(field) != compliance_row.get(field):
                issues.append(
                    {
                        "error": "audit_compliance_row_mismatch",
                        "id": row_id,
                        "field": field,
                        "audit": audit_row.get(field),
                        "compliance": compliance_row.get(field),
                    }
                )
        expected_claimable = "yes" if truthy_present(compliance_row.get("claimable")) else "no"
        if audit_row.get("claimable") != expected_claimable:
            issues.append({"error": "claimable_mismatch", "id": row_id, "expected": expected_claimable, "actual": audit_row.get("claimable")})

    summary = payload.get("summary") or {}
    if summary.get("claim_status") != expected_status:
        issues.append({"error": "summary_claim_status_mismatch", "actual": summary.get("claim_status")})
    expected_summary = {
        "checklist_item_count": len(compliance_rows),
        "claim_gate_overall_status": claim_gate.get("overall_status"),
        "claim_gate_required_failure_count": claim_gate.get("required_failure_count"),
        "claim_gate_optional_failure_count": claim_gate.get("optional_failure_count"),
        "pre_human_handoff_status": effective_prehuman.get("overall_status"),
        "pre_human_handoff_checks": effective_prehuman.get("check_count"),
        "pre_human_handoff_status_counts": effective_prehuman.get("status_counts"),
        "required_human_return_files": 14,
        "present_human_return_files": 0,
        "master_return_files": 16,
        "master_return_files_present": 0,
        "method_module_count": 11,
        "method_modules_missing_required": 0,
        "missing_evidence_row_count": 0,
    }
    for field, expected in expected_summary.items():
        if summary.get(field) != expected:
            issues.append({"error": "summary_mismatch", "field": field, "expected": expected, "actual": summary.get(field)})
    if summary.get("claim_gate_overall_status") != "FAIL":
        issues.append({"error": "claim_gate_should_remain_fail_pre_human", "actual": summary.get("claim_gate_overall_status")})
    if summary.get("pre_human_handoff_status") != "PASS":
        issues.append({"error": "pre_human_should_be_pass", "actual": summary.get("pre_human_handoff_status")})
    if int(summary.get("completion_proven_item_count") or 0) <= 0:
        issues.append({"error": "no_completion_proven_items"})
    if int(summary.get("human_blocked_item_count") or 0) < 8:
        issues.append({"error": "too_few_human_blocked_items", "actual": summary.get("human_blocked_item_count")})

    actual_blockers = payload.get("actual_human_blockers") or {}
    if set(actual_blockers.get("minimum_accept") or []) != expected_minimum_blockers:
        issues.append({"error": "minimum_blockers_mismatch", "actual": actual_blockers.get("minimum_accept")})
    if set(actual_blockers.get("strong_or_optional") or []) != expected_strong_blockers:
        issues.append({"error": "strong_blockers_mismatch", "actual": actual_blockers.get("strong_or_optional")})

    proof_states = {row.get("proof_state") for row in audit_rows}
    for state in [
        "proven_for_current_automatic_stage",
        "human_required_not_complete",
        "scaffold_ready_human_evidence_pending",
    ]:
        if state not in proof_states:
            issues.append({"error": "missing_proof_state", "proof_state": state})
    for row in audit_rows:
        status = row.get("status")
        proof = row.get("proof_state")
        if status == "pass" and row.get("claimable") == "yes" and proof != "proven_for_current_automatic_stage":
            issues.append({"error": "pass_claimable_row_not_proven", "id": row.get("id"), "proof_state": proof})
        if status == "pending_human" and proof != "human_required_not_complete":
            issues.append({"error": "pending_human_row_wrong_proof_state", "id": row.get("id"), "proof_state": proof})
        if status == "partial" and proof != "scaffold_ready_human_evidence_pending":
            issues.append({"error": "partial_row_wrong_proof_state", "id": row.get("id"), "proof_state": proof})
        if row.get("missing_evidence_files"):
            issues.append({"error": "row_has_missing_evidence_files", "id": row.get("id"), "missing": row.get("missing_evidence_files")})

    if len(csv_rows) != len(audit_rows):
        issues.append({"error": "csv_row_count_mismatch", "expected": len(audit_rows), "actual": len(csv_rows)})
    for row in csv_rows:
        if row.get("id") not in audit_by_id:
            issues.append({"error": "csv_unknown_row_id", "id": row.get("id")})
            break

    for label, path_value in (payload.get("source_artifacts") or {}).items():
        if not path_value or not Path(path_value).exists():
            issues.append({"error": "source_artifact_missing", "label": label, "path": path_value})

    if not md_path.exists():
        issues.append({"error": "missing_markdown", "path": rel(md_path)})
    else:
        text = md_path.read_text(encoding="utf-8", errors="replace")
        for pattern in [
            "CAPE-KG Revised Plan Completion Audit",
            "Completion Decision",
            "Plan completion proven",
            "Expected Human Blockers",
            "Plan Checklist Audit",
        ]:
            if pattern not in text:
                issues.append({"error": "markdown_missing_pattern", "pattern": pattern})

    if issues:
        add_check(
            checks,
            "revised_plan_completion_audit",
            "FAIL",
            "Revised plan completion audit is missing, stale, or overclaims completion.",
            {"json": rel(json_path), "markdown": rel(md_path), "csv": rel(csv_path), "issues": issues[:80]},
        )
        return

    add_check(
        checks,
        "revised_plan_completion_audit",
        "PASS",
        "Revised plan completion audit proves automatic-stage readiness while keeping human-gated completion unclaimed.",
        {
            "json": rel(json_path),
            "markdown": rel(md_path),
            "csv": rel(csv_path),
            "checklist_items": len(audit_rows),
            "completion_proven_items": summary.get("completion_proven_item_count"),
            "human_blocked_items": summary.get("human_blocked_item_count"),
            "claim_status": payload.get("claim_status"),
        },
    )


def validate_public_revised_plan_completion_audit(checks, exp_dir):
    release_dir = exp_dir / "06_release"
    json_path = release_dir / "revised_plan_completion_audit_public_safe.json"
    md_path = release_dir / "revised_plan_completion_audit_public_safe.md"
    csv_path = release_dir / "revised_plan_completion_audit_public_safe_items.csv"
    internal_path = release_dir / "revised_plan_completion_audit.json"
    expected_status = "public_safe_revised_plan_completion_audit_ready_not_submission_complete"
    forbidden_patterns = [
        "01_data/",
        "05_review/human_gold_batches/",
        "gold_annotation_template.jsonl",
        "evaluation_chunks.jsonl",
        "annotation_workbench.html",
        "annotator_",
        "adjudication.jsonl",
        "adjudication_draft.jsonl",
    ]
    issues = []

    try:
        payload = read_json(json_path)
        internal = read_json(internal_path)
        csv_rows = read_csv_rows(csv_path)
    except Exception as exc:
        add_check(
            checks,
            "public_revised_plan_completion_audit",
            "FAIL",
            "Public-safe revised plan completion audit artifacts cannot be read.",
            {"json": rel(json_path), "csv": rel(csv_path), "error": str(exc)},
        )
        return

    if payload.get("claim_status") != expected_status:
        issues.append({"error": "unexpected_claim_status", "actual": payload.get("claim_status")})
    if payload.get("source_claim_status") != internal.get("claim_status"):
        issues.append({"error": "source_claim_status_mismatch", "expected": internal.get("claim_status"), "actual": payload.get("source_claim_status")})

    safety = payload.get("public_safety") or {}
    expected_safety = {
        "source_text_included": False,
        "private_review_paths_included": False,
        "reviewed_file_names_included": False,
        "contains_only_counts_statuses_and_generic_next_steps": True,
    }
    for field, expected in expected_safety.items():
        if safety.get(field) is not expected:
            issues.append({"error": "public_safety_flag_mismatch", "field": field, "expected": expected, "actual": safety.get(field)})

    decision = payload.get("completion_decision") or {}
    if decision.get("plan_completion_proven") is not False:
        issues.append({"error": "public_audit_overclaims_plan_completion", "actual": decision.get("plan_completion_proven")})
    if decision.get("submission_ready") is not False:
        issues.append({"error": "public_audit_overclaims_submission_ready", "actual": decision.get("submission_ready")})

    summary = payload.get("summary") or {}
    internal_summary = internal.get("summary") or {}
    for field in [
        "checklist_item_count",
        "completion_proven_item_count",
        "human_blocked_item_count",
        "minimum_human_blocker_count",
        "strong_or_optional_human_blocker_count",
        "claim_gate_overall_status",
        "claim_gate_required_failure_count",
        "claim_gate_optional_failure_count",
        "pre_human_handoff_status",
        "pre_human_handoff_checks",
        "required_human_return_files",
        "present_human_return_files",
        "master_return_files",
        "master_return_files_present",
        "method_module_count",
        "method_modules_missing_required",
    ]:
        if summary.get(field) != internal_summary.get(field):
            issues.append({"error": "summary_mismatch_internal", "field": field, "expected": internal_summary.get(field), "actual": summary.get(field)})
    if summary.get("claim_status") != expected_status:
        issues.append({"error": "summary_claim_status_mismatch", "actual": summary.get("claim_status")})

    rows = payload.get("public_audit_rows") or []
    internal_rows = internal.get("audit_rows") or []
    if len(rows) != len(internal_rows):
        issues.append({"error": "public_internal_row_count_mismatch", "expected": len(internal_rows), "actual": len(rows)})
    if len(csv_rows) != len(rows):
        issues.append({"error": "csv_row_count_mismatch", "expected": len(rows), "actual": len(csv_rows)})
    internal_ids = [row.get("id") for row in internal_rows]
    public_ids = [row.get("id") for row in rows]
    if public_ids != internal_ids:
        issues.append({"error": "public_internal_ids_mismatch", "expected": internal_ids, "actual": public_ids})
    for row in rows:
        if row.get("evidence_category") not in {
            "public_or_release_artifact_available",
            "human_gold_return_required",
            "strong_or_expert_return_required",
            "internal_completion_evidence",
        }:
            issues.append({"error": "unknown_evidence_category", "id": row.get("id"), "actual": row.get("evidence_category")})
            break
        if not row.get("public_next_step"):
            issues.append({"error": "missing_public_next_step", "id": row.get("id")})
            break
        if row.get("status") in {"pending_human", "partial"} and row.get("human_blocked") != "yes":
            issues.append({"error": "human_blocked_flag_missing", "id": row.get("id"), "status": row.get("status")})
            break

    source_roles = set(payload.get("source_artifact_roles") or [])
    required_roles = {
        "claim_gate_report",
        "eacl_plan_compliance_matrix",
        "pre_human_handoff_validation",
        "submission_completion_audit",
        "paper_readiness_checklist",
        "human_review_master_return_files",
    }
    missing_roles = sorted(required_roles - source_roles)
    if missing_roles:
        issues.append({"error": "missing_source_artifact_roles", "missing": missing_roles})

    for path in [json_path, md_path, csv_path]:
        if not path.exists():
            issues.append({"error": "missing_public_file", "path": rel(path)})
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        hits = [pattern for pattern in forbidden_patterns if pattern in text]
        if hits:
            issues.append({"error": "public_file_contains_forbidden_pattern", "path": rel(path), "hits": hits})
    if md_path.exists():
        text = md_path.read_text(encoding="utf-8", errors="replace")
        for pattern in [
            "CAPE-KG Public-Safe Revised Plan Completion Audit",
            "Public Safety",
            "Completion Decision",
            "Public Audit Rows",
            "Plan completion proven",
        ]:
            if pattern not in text:
                issues.append({"error": "markdown_missing_pattern", "pattern": pattern})

    if issues:
        add_check(
            checks,
            "public_revised_plan_completion_audit",
            "FAIL",
            "Public-safe revised plan completion audit is missing, stale, unsafe, or overclaims completion.",
            {"json": rel(json_path), "markdown": rel(md_path), "csv": rel(csv_path), "issues": issues[:80]},
        )
        return

    add_check(
        checks,
        "public_revised_plan_completion_audit",
        "PASS",
        "Public-safe revised plan completion audit mirrors completion status without private paths or source text.",
        {
            "json": rel(json_path),
            "markdown": rel(md_path),
            "csv": rel(csv_path),
            "checklist_items": len(rows),
            "claim_status": payload.get("claim_status"),
        },
    )


def validate_revised_plan_section_status(checks, exp_dir):
    release_dir = exp_dir / "06_release"
    json_path = release_dir / "revised_plan_section_status_ko.json"
    md_path = release_dir / "revised_plan_section_status_ko.md"
    csv_path = release_dir / "revised_plan_section_status_ko.csv"
    audit_path = release_dir / "revised_plan_completion_audit.json"
    compliance_path = release_dir / "eacl_plan_compliance_matrix.json"
    issues = []
    try:
        payload = read_json(json_path)
        md_text = md_path.read_text(encoding="utf-8")
        csv_rows = read_csv_rows(csv_path)
        audit = read_json(audit_path)
        compliance = read_json(compliance_path)
    except Exception as exc:
        add_check(
            checks,
            "revised_plan_section_status",
            "FAIL",
            "Revised plan section status files cannot be read.",
            {"json": rel(json_path), "markdown": rel(md_path), "csv": rel(csv_path), "error": str(exc)},
        )
        return

    summary = payload.get("summary") or {}
    audit_summary = audit.get("summary") or {}
    compliance_summary = compliance.get("summary") or {}
    section_rows = payload.get("section_rows") or []
    section_ids = {row.get("section_id") for row in section_rows}
    expected_sections = {f"S{i:02d}" for i in range(1, 15)}

    if payload.get("claim_status") != "revised_plan_section_status_ready_not_submission_complete":
        issues.append({"error": "unexpected_claim_status", "actual": payload.get("claim_status")})
    if summary.get("section_count") != 14 or len(section_rows) != 14 or len(csv_rows) != 14:
        issues.append(
            {
                "error": "unexpected_section_count",
                "summary": summary.get("section_count"),
                "json_rows": len(section_rows),
                "csv_rows": len(csv_rows),
            }
        )
    missing_sections = sorted(expected_sections - section_ids)
    if missing_sections:
        issues.append({"error": "missing_section_ids", "section_ids": missing_sections})
    if summary.get("section_evidence_missing_count") != 0:
        issues.append({"error": "section_evidence_missing", "count": summary.get("section_evidence_missing_count")})

    pairs = [
        ("claim_gate_overall_status", summary.get("claim_gate_overall_status"), audit_summary.get("claim_gate_overall_status")),
        ("pre_human_handoff_status", summary.get("pre_human_handoff_status"), audit_summary.get("pre_human_handoff_status")),
        ("pre_human_handoff_checks", summary.get("pre_human_handoff_checks"), audit_summary.get("pre_human_handoff_checks")),
        ("checklist_item_count", summary.get("checklist_item_count"), audit_summary.get("checklist_item_count")),
        (
            "minimum_return_files_required",
            summary.get("minimum_return_files_required"),
            compliance_summary.get("minimum_paper_gate_return_file_count"),
        ),
        (
            "minimum_return_files_present",
            summary.get("minimum_return_files_present"),
            compliance_summary.get("minimum_paper_gate_return_file_present_count"),
        ),
    ]
    for key, actual, expected in pairs:
        if actual != expected:
            issues.append({"error": "summary_mismatch", "key": key, "actual": actual, "expected": expected})

    required_patterns = [
        "# CAPE-KG Revised Plan Section Status",
        "계획서 13장 체크리스트",
        "M1-M11 방법론 모듈 상태",
        "아직 필요한 반환 파일",
        "APPLY_IMPORTS=0",
        "APPLY_IMPORTS=1",
        "최종 성능 claim은 human-gold annotation",
        "Minimum paper-gate return files",
    ]
    missing_patterns = [pattern for pattern in required_patterns if pattern not in md_text]
    if missing_patterns:
        issues.append({"error": "markdown_missing_required_patterns", "patterns": missing_patterns})

    for section in expected_sections:
        if section not in md_text:
            issues.append({"error": "markdown_missing_section_id", "section_id": section})
            break

    if issues:
        add_check(
            checks,
            "revised_plan_section_status",
            "FAIL",
            "Revised plan section status is missing, stale, or inconsistent with the authoritative audits.",
            {"json": rel(json_path), "markdown": rel(md_path), "csv": rel(csv_path), "issues": issues[:40]},
        )
        return

    add_check(
        checks,
        "revised_plan_section_status",
        "PASS",
        "Korean section-by-section revised-plan status table is synchronized with current gates and audits.",
        {
            "json": rel(json_path),
            "markdown": rel(md_path),
            "csv": rel(csv_path),
            "sections": len(section_rows),
            "claim_gate": summary.get("claim_gate_overall_status"),
            "pre_human_checks": summary.get("pre_human_handoff_checks"),
            "minimum_return_files_present": summary.get("minimum_return_files_present"),
            "minimum_return_files_required": summary.get("minimum_return_files_required"),
        },
    )


def validate_metric_traceability_audit(checks, exp_dir):
    release_dir = exp_dir / "06_release"
    json_path = release_dir / "metric_traceability_audit.json"
    md_path = release_dir / "metric_traceability_audit.md"
    csv_path = release_dir / "metric_traceability_audit.csv"
    post_human_path = release_dir / "post_human_scoring_readiness.json"
    protocol_path = release_dir / "evaluation_protocol_lock.json"
    blueprint_path = release_dir / "paper_table_blueprint.json"
    expected_status = "metric_traceability_ready_pending_human_gold_and_expert_returns"
    expected_metric_ids = {
        "M01_node_f1",
        "M02_edge_f1",
        "M03_evidence_exact_iou",
        "M04_unsupported_edge_rate",
        "M05_ontology_conformance",
        "M06_procedural_consistency",
        "M07_cq_answerability",
        "M08_mapping_pk_mrr_ndcg",
        "M09_crosswalk_accept_utility",
        "M10_active_review_efficiency",
    }
    issues = []

    try:
        payload = read_json(json_path)
        csv_rows = read_csv_rows(csv_path)
        post_human = read_json(post_human_path)
        protocol = read_json(protocol_path)
        blueprint = read_json(blueprint_path)
    except Exception as exc:
        add_check(
            checks,
            "metric_traceability_audit",
            "FAIL",
            "Metric traceability audit artifacts cannot be read.",
            {"json": rel(json_path), "csv": rel(csv_path), "error": str(exc)},
        )
        return

    if payload.get("claim_status") != expected_status:
        issues.append({"error": "unexpected_claim_status", "actual": payload.get("claim_status")})
    summary = payload.get("summary") or {}
    expected_summary = {
        "metric_count": 10,
        "pending_metric_count": 10,
        "claimable_metric_count": 0,
        "metric_issue_count": 0,
        "metric_rows_with_issues": 0,
        "all_evaluator_scripts_present": True,
        "all_output_files_present": True,
        "all_paper_tables_present": True,
        "all_protocol_metrics_present": True,
        "all_required_gates_known": True,
        "claim_status": expected_status,
    }
    for field, expected in expected_summary.items():
        if summary.get(field) != expected:
            issues.append({"error": "summary_mismatch", "field": field, "expected": expected, "actual": summary.get(field)})

    boundary = payload.get("claim_boundary") or {}
    if boundary.get("metric_definitions_locked") is not True:
        issues.append({"error": "metric_definitions_locked_not_true"})
    if boundary.get("pre_human_claimable_metrics") != 0:
        issues.append({"error": "pre_human_claimable_metrics_not_zero", "actual": boundary.get("pre_human_claimable_metrics")})
    if boundary.get("human_gold_or_expert_returns_required") is not True:
        issues.append({"error": "human_gold_or_expert_returns_required_not_true"})
    boundary_text = " ".join(str(boundary.get(key) or "") for key in ["safe_interpretation", "not_claimable_until"])
    for pattern in ["Metric implementations", "human/expert returns", "Human-gold"]:
        if pattern not in boundary_text:
            issues.append({"error": "claim_boundary_missing_pattern", "pattern": pattern})

    rows = payload.get("metric_rows") or []
    row_ids = {row.get("metric_id") for row in rows}
    if row_ids != expected_metric_ids:
        issues.append({"error": "metric_id_set_mismatch", "expected": sorted(expected_metric_ids), "actual": sorted(row_ids)})
    post_metric_ids = {row.get("metric_id") for row in post_human.get("metrics") or []}
    if not expected_metric_ids.issubset(post_metric_ids):
        issues.append({"error": "post_human_metric_ids_missing", "actual": sorted(post_metric_ids)})
    protocol_names_by_group = {
        group: {row.get("metric") for row in group_rows}
        for group, group_rows in (protocol.get("metric_definitions") or {}).items()
    }
    table_ids = {row.get("table_id") for row in blueprint.get("tables") or []}
    for row in rows:
        metric_id = row.get("metric_id")
        if row.get("claim_status") != "pending_human_returns":
            issues.append({"error": "metric_claim_status_not_pending", "metric_id": metric_id, "actual": row.get("claim_status")})
        if row.get("claimable_now") is not False:
            issues.append({"error": "metric_claimable_pre_human", "metric_id": metric_id})
        for flag in [
            "evaluator_scripts_present",
            "output_files_present",
            "paper_tables_present",
            "protocol_metrics_present",
            "required_gates_known",
        ]:
            if row.get(flag) is not True:
                issues.append({"error": "metric_flag_not_true", "metric_id": metric_id, "flag": flag, "actual": row.get(flag)})
        if row.get("issue_count") != 0 or row.get("issues"):
            issues.append({"error": "metric_row_has_issues", "metric_id": metric_id, "issues": row.get("issues")})
        for path in row.get("evaluator_scripts") or []:
            if not Path(path).exists():
                issues.append({"error": "missing_evaluator_script", "metric_id": metric_id, "path": path})
        for path in row.get("output_files") or []:
            if not Path(path).exists():
                issues.append({"error": "missing_output_file", "metric_id": metric_id, "path": path})
        for table_id in row.get("paper_tables") or []:
            if table_id not in table_ids:
                issues.append({"error": "unknown_paper_table", "metric_id": metric_id, "table_id": table_id})
        for group in row.get("protocol_groups") or []:
            if group not in protocol_names_by_group:
                issues.append({"error": "unknown_protocol_group", "metric_id": metric_id, "group": group})
        for metric_name in row.get("protocol_metrics") or []:
            if not any(metric_name in names for names in protocol_names_by_group.values()):
                issues.append({"error": "unknown_protocol_metric", "metric_id": metric_id, "protocol_metric": metric_name})

    if len(csv_rows) != len(rows):
        issues.append({"error": "csv_row_count_mismatch", "expected": len(rows), "actual": len(csv_rows)})
    csv_ids = {row.get("metric_id") for row in csv_rows}
    if csv_ids != expected_metric_ids:
        issues.append({"error": "csv_metric_id_set_mismatch", "actual": sorted(csv_ids)})

    for label, path_value in (payload.get("source_artifacts") or {}).items():
        if not path_value or not Path(path_value).exists():
            issues.append({"error": "source_artifact_missing", "label": label, "path": path_value})

    if not md_path.exists():
        issues.append({"error": "missing_markdown", "path": rel(md_path)})
    else:
        text = md_path.read_text(encoding="utf-8", errors="replace")
        for pattern in [
            "CAPE-KG Metric Traceability Audit",
            "Claim Boundary",
            "Metric Rows",
            "Final values remain pending human-gold",
            "M10_active_review_efficiency",
        ]:
            if pattern not in text:
                issues.append({"error": "markdown_missing_pattern", "pattern": pattern})

    if issues:
        add_check(
            checks,
            "metric_traceability_audit",
            "FAIL",
            "Metric traceability audit is missing, stale, or claim-unsafe.",
            {"json": rel(json_path), "markdown": rel(md_path), "csv": rel(csv_path), "issues": issues[:80]},
        )
        return

    add_check(
        checks,
        "metric_traceability_audit",
        "PASS",
        "Revised-plan metrics are linked to evaluator scripts, outputs, protocol definitions, paper tables, and human/expert gates.",
        {
            "json": rel(json_path),
            "markdown": rel(md_path),
            "csv": rel(csv_path),
            "metric_count": len(rows),
            "claim_status": payload.get("claim_status"),
        },
    )


def validate_contribution_claim_traceability(checks, exp_dir):
    release_dir = exp_dir / "06_release"
    json_path = release_dir / "contribution_claim_traceability.json"
    md_path = release_dir / "contribution_claim_traceability.md"
    csv_path = release_dir / "contribution_claim_traceability.csv"
    expected_status = "contribution_claim_traceability_ready_pending_human_gold_and_expert_returns"
    expected_ids = {
        "C1_task_definition_and_evidence_grounding",
        "C2_cape_kg_framework",
        "C3_benchmark_and_standard_taxonomy_alignment",
    }
    expected_reviewer_questions = {
        "Q01_domain_application",
        "Q02_reproducibility_private_data",
        "Q03_existing_ontology_guided_extraction",
        "Q04_why_korean_enterprise_documents",
        "Q05_prompt_engineering",
        "Q06_subjective_evaluation",
        "Q07_ncs_pcf_nlp_contribution",
    }
    expected_human_gates = {
        "min.gold_chunks",
        "min.gold_items",
        "min.iaa",
        "min.proposed",
    }
    issues = []

    try:
        payload = read_json(json_path)
        csv_rows = read_csv_rows(csv_path)
    except Exception as exc:
        add_check(
            checks,
            "contribution_claim_traceability",
            "FAIL",
            "Contribution claim traceability artifacts cannot be read.",
            {"json": rel(json_path), "csv": rel(csv_path), "error": str(exc)},
        )
        return

    if payload.get("claim_status") != expected_status:
        issues.append({"error": "unexpected_claim_status", "actual": payload.get("claim_status")})
    summary = payload.get("summary") or {}
    expected_summary = {
        "claim_status": expected_status,
        "contribution_count": 3,
        "setup_claimable_count": 3,
        "final_performance_claim_ready_count": 0,
        "blocked_final_claim_count": 3,
        "missing_evidence_file_count": 0,
        "linked_rq_count": 4,
        "known_rq_count": 4,
        "known_metric_count": 10,
        "linked_reviewer_question_count": 7,
        "known_reviewer_question_count": 7,
        "plan_completion_proven": False,
        "claim_gate_overall_status": "FAIL",
    }
    for field, expected in expected_summary.items():
        if summary.get(field) != expected:
            issues.append({"error": "summary_mismatch", "field": field, "expected": expected, "actual": summary.get(field)})

    boundary = payload.get("claim_boundary") or {}
    if boundary.get("safe_to_use_pre_human") is not True:
        issues.append({"error": "safe_to_use_pre_human_not_true"})
    if boundary.get("final_performance_claim_ready") is not False:
        issues.append({"error": "final_performance_claim_boundary_not_false"})
    boundary_text = " ".join(str(boundary.get(key) or "") for key in ["safe_scope", "not_claimable_until"])
    for pattern in ["contribution framing", "human-gold", "mapping/crosswalk expert review", "human-effort"]:
        if pattern not in boundary_text:
            issues.append({"error": "claim_boundary_missing_pattern", "pattern": pattern})

    rows = payload.get("contribution_rows") or []
    row_ids = {row.get("contribution_id") for row in rows}
    if row_ids != expected_ids:
        issues.append({"error": "contribution_id_set_mismatch", "expected": sorted(expected_ids), "actual": sorted(row_ids)})
    if len(csv_rows) != len(rows):
        issues.append({"error": "csv_row_count_mismatch", "expected": len(rows), "actual": len(csv_rows)})
    csv_ids = {row.get("contribution_id") for row in csv_rows}
    if csv_ids != expected_ids:
        issues.append({"error": "csv_id_set_mismatch", "actual": sorted(csv_ids)})

    linked_reviewer_questions = set()
    linked_rqs = set()
    for row in rows:
        contribution_id = row.get("contribution_id")
        if row.get("setup_claimable_now") is not True:
            issues.append({"error": "setup_not_claimable", "contribution_id": contribution_id})
        if row.get("final_performance_claim_ready") is not False:
            issues.append({"error": "final_claim_ready_pre_human", "contribution_id": contribution_id})
        if row.get("missing_evidence_files"):
            issues.append({"error": "row_missing_evidence", "contribution_id": contribution_id, "missing": row.get("missing_evidence_files")})
        for evidence in row.get("evidence_files") or []:
            path = evidence.get("path")
            if not path or not Path(path).exists() or not Path(path).is_file():
                issues.append({"error": "evidence_file_missing_on_disk", "contribution_id": contribution_id, "path": path})
        gates = set(row.get("remaining_gates") or [])
        if not expected_human_gates.issubset(gates):
            issues.append({"error": "missing_minimum_human_gates", "contribution_id": contribution_id, "actual": sorted(gates)})
        if not row.get("current_claim_boundary"):
            issues.append({"error": "missing_claim_boundary", "contribution_id": contribution_id})
        if not row.get("safe_pre_human_wording_ko") or not row.get("safe_pre_human_wording_en"):
            issues.append({"error": "missing_safe_wording", "contribution_id": contribution_id})
        if not row.get("forbidden_pre_human_claim"):
            issues.append({"error": "missing_forbidden_claim", "contribution_id": contribution_id})
        if not row.get("linked_metrics"):
            issues.append({"error": "missing_linked_metrics", "contribution_id": contribution_id})
        if not row.get("linked_modules"):
            issues.append({"error": "missing_linked_modules", "contribution_id": contribution_id})
        linked_reviewer_questions.update(row.get("reviewer_questions") or [])
        linked_rqs.update(row.get("linked_rqs") or [])
    if linked_reviewer_questions != expected_reviewer_questions:
        issues.append({"error": "reviewer_question_coverage_mismatch", "actual": sorted(linked_reviewer_questions)})
    if linked_rqs != {"RQ1", "RQ2", "RQ3", "RQ4"}:
        issues.append({"error": "rq_coverage_mismatch", "actual": sorted(linked_rqs)})

    for label, path_value in (payload.get("source_artifacts") or {}).items():
        if not path_value or not Path(path_value).exists():
            issues.append({"error": "source_artifact_missing", "label": label, "path": path_value})

    if not md_path.exists():
        issues.append({"error": "missing_markdown", "path": rel(md_path)})
    else:
        text = md_path.read_text(encoding="utf-8", errors="replace")
        for pattern in [
            "CAPE-KG Contribution Claim Traceability",
            "Claim Boundary",
            "Contribution Rows",
            "C3_benchmark_and_standard_taxonomy_alignment",
            "Final performance claims remain pending",
        ]:
            if pattern not in text:
                issues.append({"error": "markdown_missing_pattern", "pattern": pattern})

    if issues:
        add_check(
            checks,
            "contribution_claim_traceability",
            "FAIL",
            "Contribution claim traceability is missing, stale, or claim-unsafe.",
            {"json": rel(json_path), "markdown": rel(md_path), "csv": rel(csv_path), "issues": issues[:80]},
        )
        return

    add_check(
        checks,
        "contribution_claim_traceability",
        "PASS",
        "Revised-plan contribution statements are linked to current evidence, metrics, reviewer concerns, and human/expert claim gates.",
        {
            "json": rel(json_path),
            "markdown": rel(md_path),
            "csv": rel(csv_path),
            "contribution_count": len(rows),
            "claim_status": payload.get("claim_status"),
        },
    )


def validate_related_work_baseline_traceability(checks, exp_dir):
    release_dir = exp_dir / "06_release"
    json_path = release_dir / "related_work_baseline_traceability.json"
    md_path = release_dir / "related_work_baseline_traceability.md"
    csv_path = release_dir / "related_work_baseline_traceability.csv"
    expected_status = "related_work_baseline_traceability_ready_not_official_reproduction"
    expected_ids = {
        "RW01_sac_kg",
        "RW02_edc",
        "RW03_taxonomy_driven_kg",
        "RW04_text2kgbench",
        "RW05_textminex",
        "RW06_paged",
        "RW07_multi_agent_procedural_feedback",
        "RW08_shacl",
        "RW09_prov_o",
    }
    expected_conditions = {
        "B3_edc_style",
        "B4_taxonomy_rag",
        "B5_procedural_prompt",
        "B6_sac_kg_verifier_pruner",
        "P_minus_Standard_bridge",
    }
    issues = []

    try:
        payload = read_json(json_path)
        csv_rows = read_csv_rows(csv_path)
    except Exception as exc:
        add_check(
            checks,
            "related_work_baseline_traceability",
            "FAIL",
            "Related-work baseline traceability artifacts cannot be read.",
            {"json": rel(json_path), "csv": rel(csv_path), "error": str(exc)},
        )
        return

    if payload.get("claim_status") != expected_status:
        issues.append({"error": "unexpected_claim_status", "actual": payload.get("claim_status")})
    summary = payload.get("summary") or {}
    expected_summary = {
        "claim_status": expected_status,
        "reference_count": 9,
        "missing_evidence_file_count": 0,
        "direct_llm_condition_count": 5,
        "public_adapter_reference_count": 2,
        "standard_reference_count": 2,
        "official_reproduction_claim_count": 0,
        "public_benchmark_claim_status": "public_adapter_model_runs_diagnostic_not_official_leaderboard",
        "strong_public_cross_run_present": True,
        "max_single_run_paged_items": 100,
        "max_single_run_text2kg_items": 200,
    }
    for field, expected in expected_summary.items():
        if summary.get(field) != expected:
            issues.append({"error": "summary_mismatch", "field": field, "expected": expected, "actual": summary.get(field)})

    boundary = payload.get("claim_boundary") or {}
    if boundary.get("human_or_expert_gated") is not True:
        issues.append({"error": "human_or_expert_gated_not_true"})
    boundary_text = " ".join(str(boundary.get(key) or "") for key in ["safe_scope", "not_claimable"])
    for pattern in ["Related Work", "official reproductions", "leaderboard", "target-corpus final performance"]:
        if pattern not in boundary_text:
            issues.append({"error": "claim_boundary_missing_pattern", "pattern": pattern})

    rows = payload.get("related_work_rows") or []
    row_ids = {row.get("reference_id") for row in rows}
    if row_ids != expected_ids:
        issues.append({"error": "reference_id_set_mismatch", "expected": sorted(expected_ids), "actual": sorted(row_ids)})
    if len(csv_rows) != len(rows):
        issues.append({"error": "csv_row_count_mismatch", "expected": len(rows), "actual": len(csv_rows)})
    csv_ids = {row.get("reference_id") for row in csv_rows}
    if csv_ids != expected_ids:
        issues.append({"error": "csv_id_set_mismatch", "actual": sorted(csv_ids)})

    actual_conditions = {condition for row in rows for condition in row.get("local_conditions") or [] if condition in expected_conditions}
    if actual_conditions != expected_conditions:
        issues.append({"error": "condition_coverage_mismatch", "expected": sorted(expected_conditions), "actual": sorted(actual_conditions)})
    for row in rows:
        reference_id = row.get("reference_id")
        if row.get("missing_evidence_files"):
            issues.append({"error": "row_missing_evidence", "reference_id": reference_id, "missing": row.get("missing_evidence_files")})
        if not row.get("source_url"):
            issues.append({"error": "missing_source_url", "reference_id": reference_id})
        if not row.get("safe_use") or not row.get("not_claimable"):
            issues.append({"error": "missing_claim_boundary_text", "reference_id": reference_id})
        if not row.get("related_sections"):
            issues.append({"error": "missing_related_sections", "reference_id": reference_id})
        for evidence in row.get("evidence_files") or []:
            path = evidence.get("path")
            if not path or not Path(path).exists() or not Path(path).is_file():
                issues.append({"error": "evidence_file_missing_on_disk", "reference_id": reference_id, "path": path})

    for label, path_value in (payload.get("source_artifacts") or {}).items():
        if not path_value or not Path(path_value).exists():
            issues.append({"error": "source_artifact_missing", "label": label, "path": path_value})

    if not md_path.exists():
        issues.append({"error": "missing_markdown", "path": rel(md_path)})
    else:
        text = md_path.read_text(encoding="utf-8", errors="replace")
        for pattern in [
            "CAPE-KG Related Work to Baseline Traceability",
            "not an official reproduction report",
            "RW01_sac_kg",
            "RW04_text2kgbench",
            "RW08_shacl",
            "Claim Boundary",
        ]:
            if pattern not in text:
                issues.append({"error": "markdown_missing_pattern", "pattern": pattern})

    if issues:
        add_check(
            checks,
            "related_work_baseline_traceability",
            "FAIL",
            "Related-work baseline traceability is missing, stale, or claim-unsafe.",
            {"json": rel(json_path), "markdown": rel(md_path), "csv": rel(csv_path), "issues": issues[:80]},
        )
        return

    add_check(
        checks,
        "related_work_baseline_traceability",
        "PASS",
        "Plan related-work references are linked to local baselines, public adapters, validation standards, provenance artifacts, and claim boundaries.",
        {
            "json": rel(json_path),
            "markdown": rel(md_path),
            "csv": rel(csv_path),
            "reference_count": len(rows),
            "claim_status": payload.get("claim_status"),
        },
    )


def validate_annotation_protocol_traceability(checks, exp_dir):
    release_dir = exp_dir / "06_release"
    json_path = release_dir / "annotation_protocol_traceability.json"
    md_path = release_dir / "annotation_protocol_traceability.md"
    csv_path = release_dir / "annotation_protocol_traceability.csv"
    expected_status = "annotation_protocol_traceability_ready_pending_human_returns"
    expected_target_ids = {
        "T01_task_or_procedure_step",
        "T02_artifact",
        "T03_role",
        "T04_decision_gateway",
        "T05_guard_condition",
        "T06_review_checkpoint",
        "T07_principle_or_risk",
        "T08_edge_type",
        "T09_evidence_span",
        "T10_page_and_chunk_id",
    }
    expected_workflow_ids = {
        "W01_schema_and_guideline",
        "W02_batch_assignment",
        "W03_independent_annotation",
        "W04_iaa",
        "W05_adjudication",
        "W06_human_gold_validation",
        "W07_proposed_human_gold_scoring",
        "W08_mapping_expert_review",
        "W09_crosswalk_expert_review",
        "W10_active_review_effort",
    }
    issues = []

    try:
        payload = read_json(json_path)
        csv_rows = read_csv_rows(csv_path)
    except Exception as exc:
        add_check(
            checks,
            "annotation_protocol_traceability",
            "FAIL",
            "Annotation protocol traceability artifacts cannot be read.",
            {"json": rel(json_path), "csv": rel(csv_path), "error": str(exc)},
        )
        return

    if payload.get("claim_status") != expected_status:
        issues.append({"error": "unexpected_claim_status", "actual": payload.get("claim_status")})
    summary = payload.get("summary") or {}
    expected_summary = {
        "claim_status": expected_status,
        "plan_target_count": 10,
        "covered_plan_target_count": 10,
        "minimum_chunk_target": 100,
        "minimum_gold_item_target": 500,
        "batch_count": 5,
        "batch_size": 20,
        "assigned_chunks": 100,
        "candidate_edges_total": 1371,
        "annotator_count": 2,
        "adjudicator_required": True,
        "minimum_annotation_input_files": 10,
        "minimum_annotation_chunks": 100,
        "minimum_required_return_file_count": 11,
        "minimum_required_return_file_present_count": 0,
        "required_return_file_count": 14,
        "required_return_file_present_count": 0,
        "completed_pair_chunks": 0,
        "pending_pair_chunks": 120,
        "adjudicated_chunks": 0,
        "gold_item_count": 0,
        "validation_error_count": 0,
        "packet_integrity_error_count": 0,
        "packet_integrity_warning_count": 0,
        "handoff_bundle_count": 9,
        "missing_handoff_bundle_count": 0,
        "human_gold_metric_status": "pending_human_adjudication",
        "iaa_status": "pending_human_annotations",
        "adjudication_claim_status": "draft_not_final_human_gold",
        "human_gold_claim_status": "pending_human_adjudication",
    }
    for field, expected in expected_summary.items():
        if summary.get(field) != expected:
            issues.append({"error": "summary_mismatch", "field": field, "expected": expected, "actual": summary.get(field)})

    schema_summary = payload.get("annotation_schema_summary") or {}
    for field in ["required_chunk_fields", "gold_node_fields", "gold_edge_fields", "completed_status_values", "paper_claim_requires"]:
        if not schema_summary.get(field):
            issues.append({"error": "schema_summary_missing_field", "field": field})
    for requirement in ["two annotators", "IAA report", "adjudicated gold file"]:
        if requirement not in schema_summary.get("paper_claim_requires", []):
            issues.append({"error": "schema_paper_claim_requirement_missing", "requirement": requirement})

    rows = payload.get("plan_target_rows") or []
    row_ids = {row.get("target_id") for row in rows}
    if row_ids != expected_target_ids:
        issues.append({"error": "plan_target_id_set_mismatch", "expected": sorted(expected_target_ids), "actual": sorted(row_ids)})
    if len(csv_rows) != len(rows) or len(csv_rows) != 10:
        issues.append({"error": "csv_row_count_mismatch", "expected": 10, "actual": len(csv_rows)})
    csv_ids = {row.get("target_id") for row in csv_rows}
    if csv_ids != expected_target_ids:
        issues.append({"error": "csv_target_id_set_mismatch", "actual": sorted(csv_ids)})
    for row in rows:
        if "pending" not in row.get("current_status", ""):
            issues.append({"error": "target_row_should_remain_pending_human_or_review", "target_id": row.get("target_id")})
        if not row.get("protocol_coverage") or not row.get("evidence_artifacts"):
            issues.append({"error": "target_row_missing_coverage_or_evidence", "target_id": row.get("target_id")})

    workflow_rows = payload.get("workflow_rows") or []
    workflow_ids = {row.get("workflow_id") for row in workflow_rows}
    if workflow_ids != expected_workflow_ids:
        issues.append({"error": "workflow_id_set_mismatch", "expected": sorted(expected_workflow_ids), "actual": sorted(workflow_ids)})

    gate_rows = payload.get("gate_summary_rows") or []
    gate_ids = {row.get("gate_id") for row in gate_rows}
    for gate_id in ["min.iaa", "min.gold_chunks", "min.gold_items", "min.proposed"]:
        if gate_id not in gate_ids:
            issues.append({"error": "missing_minimum_gate", "gate_id": gate_id})
    return_summary = {row.get("task_type"): row for row in payload.get("return_file_summary") or []}
    for task_type in ["human_gold_annotation", "human_gold_adjudication", "mapping_expert_review", "crosswalk_expert_review", "active_review_human_effort"]:
        row = return_summary.get(task_type)
        if not row:
            issues.append({"error": "missing_return_file_summary_task_type", "task_type": task_type})
            continue
        if int(row.get("present") or 0) != 0:
            issues.append({"error": "return_file_present_pre_human_should_be_zero", "task_type": task_type, "present": row.get("present")})

    boundary = payload.get("claim_boundary") or {}
    if boundary.get("human_or_expert_gated") is not True:
        issues.append({"error": "human_or_expert_gated_not_true"})
    boundary_text = " ".join(str(boundary.get(key) or "") for key in ["safe_scope", "not_claimable", "current_gate_status"])
    for pattern in ["annotation", "IAA", "adjudication", "mapping expert review", "active-review efficiency", "pending_human_annotations"]:
        if pattern not in boundary_text:
            issues.append({"error": "claim_boundary_missing_pattern", "pattern": pattern})

    for label, state in (payload.get("source_artifacts") or {}).items():
        path_value = state.get("path")
        if not path_value or not Path(path_value).exists():
            issues.append({"error": "source_artifact_missing", "label": label, "path": path_value})
        if not state.get("exists"):
            issues.append({"error": "source_artifact_state_not_exists", "label": label, "path": path_value})
    if payload.get("missing_source_artifacts"):
        issues.append({"error": "missing_source_artifacts", "missing": payload.get("missing_source_artifacts")})

    if not md_path.exists():
        issues.append({"error": "missing_markdown", "path": rel(md_path)})
    else:
        text = md_path.read_text(encoding="utf-8", errors="replace")
        for pattern in [
            "CAPE-KG Annotation Protocol Traceability",
            "Plan Annotation Targets",
            "Human-Gold Gate Boundary",
            "T10_page_and_chunk_id",
            "pending_human_annotations",
            "It is a workflow traceability artifact, not human-gold performance evidence.",
        ]:
            if pattern not in text:
                issues.append({"error": "markdown_missing_pattern", "pattern": pattern})

    if issues:
        add_check(
            checks,
            "annotation_protocol_traceability",
            "FAIL",
            "Annotation protocol traceability is missing, stale, or claim-unsafe.",
            {"json": rel(json_path), "markdown": rel(md_path), "csv": rel(csv_path), "issues": issues[:80]},
        )
        return

    add_check(
        checks,
        "annotation_protocol_traceability",
        "PASS",
        "Plan annotation requirements are linked to protocol, schema, batch, IAA/adjudication, return-file, and gate evidence.",
        {
            "json": rel(json_path),
            "markdown": rel(md_path),
            "csv": rel(csv_path),
            "plan_targets": len(rows),
            "workflow_rows": len(workflow_rows),
            "claim_status": payload.get("claim_status"),
        },
    )


def validate_method_module_coverage(checks, exp_dir):
    release_dir = exp_dir / "06_release"
    coverage_path = release_dir / "method_module_coverage.json"
    coverage_md_path = release_dir / "method_module_coverage.md"
    compliance_path = release_dir / "eacl_plan_compliance_matrix.json"
    try:
        coverage = read_json(coverage_path)
        compliance = read_json(compliance_path)
    except Exception as exc:
        add_check(
            checks,
            "method_module_coverage_claim_safety",
            "FAIL",
            "Method module coverage or compliance matrix cannot be read.",
            {"error": str(exc), "path": rel(coverage_path)},
        )
        return

    expected_modules = [f"M{i}" for i in range(1, 12)]
    expected_human_dependent = {"M3", "M4", "M5", "M6", "M8", "M9", "M10", "M11"}
    expected_non_human = set(expected_modules) - expected_human_dependent
    expected_claim_status = "all_m1_m11_artifacts_present_human_claims_pending"
    human_pending_terms = ("human", "Human", "expert", "adjudication", "gold", "review")

    summary = coverage.get("summary") or {}
    modules = coverage.get("modules") or []
    module_ids = [module.get("module_id") for module in modules]
    modules_by_id = {module.get("module_id"): module for module in modules}
    issues = []

    if summary.get("claim_status") != expected_claim_status:
        issues.append({"error": "unexpected_claim_status", "actual": summary.get("claim_status")})
    if summary.get("module_count") != 11:
        issues.append({"error": "unexpected_module_count", "actual": summary.get("module_count")})
    if summary.get("modules_with_required_artifacts") != 11:
        issues.append(
            {
                "error": "unexpected_modules_with_required_artifacts",
                "actual": summary.get("modules_with_required_artifacts"),
            }
        )
    if summary.get("missing_required_artifact_count") != 0:
        issues.append(
            {
                "error": "missing_required_artifacts_reported",
                "actual": summary.get("missing_required_artifact_count"),
            }
        )
    if summary.get("missing_modules") not in ([], None):
        issues.append({"error": "missing_modules_reported", "actual": summary.get("missing_modules")})
    if set(summary.get("human_dependent_modules") or []) != expected_human_dependent:
        issues.append(
            {
                "error": "human_dependent_modules_mismatch",
                "expected": sorted(expected_human_dependent),
                "actual": summary.get("human_dependent_modules"),
            }
        )
    if summary.get("human_dependent_module_count") != len(expected_human_dependent):
        issues.append(
            {
                "error": "unexpected_human_dependent_module_count",
                "actual": summary.get("human_dependent_module_count"),
            }
        )
    if module_ids != expected_modules:
        issues.append({"error": "module_id_order_mismatch", "expected": expected_modules, "actual": module_ids})

    for module_id in expected_modules:
        module = modules_by_id.get(module_id)
        if not module:
            issues.append({"error": "missing_module", "module_id": module_id})
            continue
        is_human_dependent = module_id in expected_human_dependent
        expected_status = (
            "implemented_artifacts_present_human_claim_pending"
            if is_human_dependent
            else "implemented_artifacts_present"
        )
        if module.get("status") != expected_status:
            issues.append(
                {
                    "error": "unexpected_module_status",
                    "module_id": module_id,
                    "expected": expected_status,
                    "actual": module.get("status"),
                }
            )
        if bool(module.get("human_dependent_for_final_claim")) != is_human_dependent:
            issues.append(
                {
                    "error": "unexpected_human_dependent_flag",
                    "module_id": module_id,
                    "expected": is_human_dependent,
                    "actual": module.get("human_dependent_for_final_claim"),
                }
            )
        if module.get("missing_required_artifact_count") != 0:
            issues.append(
                {
                    "error": "module_missing_required_artifacts",
                    "module_id": module_id,
                    "actual": module.get("missing_required_artifact_count"),
                }
            )
        required_artifacts = [item for item in module.get("artifacts") or [] if item.get("required") is not False]
        if len(required_artifacts) != module.get("required_artifact_count"):
            issues.append(
                {
                    "error": "required_artifact_count_mismatch",
                    "module_id": module_id,
                    "reported": module.get("required_artifact_count"),
                    "actual": len(required_artifacts),
                }
            )
        if not required_artifacts:
            issues.append({"error": "module_has_no_required_artifacts", "module_id": module_id})
        for item in required_artifacts:
            path = item.get("path")
            if not path:
                issues.append({"error": "artifact_missing_path", "module_id": module_id, "item": item})
                continue
            if item.get("exists") is not True or not Path(path).exists():
                issues.append({"error": "artifact_missing_on_disk", "module_id": module_id, "path": path})

        required_scripts = [item for item in module.get("scripts") or [] if item.get("required") is not False]
        if not required_scripts:
            issues.append({"error": "module_has_no_required_scripts", "module_id": module_id})
        for item in required_scripts:
            path = item.get("path")
            if not path:
                issues.append({"error": "script_missing_path", "module_id": module_id, "item": item})
                continue
            if item.get("exists") is not True or not Path(path).exists():
                issues.append({"error": "script_missing_on_disk", "module_id": module_id, "path": path})

        remaining = str(module.get("remaining_for_paper_claim") or "")
        if is_human_dependent and not any(term in remaining for term in human_pending_terms):
            issues.append(
                {
                    "error": "human_dependent_module_missing_human_pending_language",
                    "module_id": module_id,
                    "remaining_for_paper_claim": remaining,
                }
            )
        if module_id in expected_non_human and not remaining:
            issues.append({"error": "non_human_module_missing_remaining_note", "module_id": module_id})

    compliance_rows = compliance.get("method_module_rows") or []
    compliance_ids = [row.get("module") for row in compliance_rows]
    if compliance_ids != expected_modules:
        issues.append({"error": "compliance_method_module_ids_mismatch", "expected": expected_modules, "actual": compliance_ids})
    compliance_by_id = {row.get("module"): row for row in compliance_rows}
    for module_id in expected_modules:
        row = compliance_by_id.get(module_id)
        module = modules_by_id.get(module_id)
        if not row or not module:
            continue
        if row.get("status") != module.get("status"):
            issues.append(
                {
                    "error": "coverage_compliance_status_mismatch",
                    "module_id": module_id,
                    "coverage": module.get("status"),
                    "compliance": row.get("status"),
                }
            )
        if row.get("missing_required") != module.get("missing_required_artifact_count"):
            issues.append(
                {
                    "error": "coverage_compliance_missing_count_mismatch",
                    "module_id": module_id,
                    "coverage": module.get("missing_required_artifact_count"),
                    "compliance": row.get("missing_required"),
                }
            )
    checklist_item = next((row for row in compliance.get("checklist_rows") or [] if row.get("id") == "method.m1_m11"), None)
    if not checklist_item:
        issues.append({"error": "missing_method_m1_m11_checklist_item"})
    else:
        if checklist_item.get("status") != "partial":
            issues.append({"error": "unexpected_method_m1_m11_status", "actual": checklist_item.get("status")})
        next_step = str(checklist_item.get("next_step") or "")
        if not any(term in next_step for term in human_pending_terms):
            issues.append({"error": "method_m1_m11_next_step_missing_human_pending_language", "next_step": next_step})

    if not coverage_md_path.exists():
        issues.append({"error": "missing_markdown", "path": rel(coverage_md_path)})
    else:
        text = coverage_md_path.read_text(encoding="utf-8")
        for pattern in [
            "CAPE-KG Method Module Coverage",
            f"Claim status: `{expected_claim_status}`",
            "M1 Document structure recovery",
            "M11 NCS/PCF mapping evaluator",
            "paper-claim evidence",
        ]:
            if pattern not in text:
                issues.append({"error": "missing_markdown_pattern", "pattern": pattern})

    if issues:
        add_check(
            checks,
            "method_module_coverage_claim_safety",
            "FAIL",
            "Method module coverage does not safely represent M1-M11 executable artifacts and human-dependent final claims.",
            {"path": rel(coverage_path), "issues": issues[:80]},
        )
        return

    add_check(
        checks,
        "method_module_coverage_claim_safety",
        "PASS",
        "CAPE-KG M1-M11 executable artifacts are covered while human-dependent final claims remain pending.",
        {
            "path": rel(coverage_path),
            "modules": len(modules),
            "human_dependent_modules": sorted(expected_human_dependent),
            "claim_status": summary.get("claim_status"),
        },
    )


def validate_paper_readiness_checklist(checks, exp_dir):
    release_dir = exp_dir / "06_release"
    checklist_path = release_dir / "paper_readiness_checklist.json"
    checklist_md_path = release_dir / "paper_readiness_checklist.md"
    readiness_path = release_dir / "submission_readiness_audit.json"
    compliance_path = release_dir / "eacl_plan_compliance_matrix.json"
    try:
        checklist = read_json(checklist_path)
        readiness = read_json(readiness_path)
        compliance = read_json(compliance_path)
    except Exception as exc:
        add_check(
            checks,
            "paper_readiness_checklist",
            "FAIL",
            "Paper readiness checklist or source audit cannot be read.",
            {"error": str(exc), "path": rel(checklist_path)},
        )
        return

    minimum = checklist.get("minimum_accept_checklist") or []
    strong = checklist.get("strong_accept_checklist") or []
    readiness_by_id = {row.get("id"): row for row in readiness.get("items", [])}
    compliance_by_id = {row.get("id"): row for row in compliance.get("checklist_rows", [])}
    issues = []

    if len(minimum) < 10:
        issues.append({"error": "minimum_checklist_too_short", "count": len(minimum)})
    if len(strong) < 7:
        issues.append({"error": "strong_checklist_too_short", "count": len(strong)})

    strong_gold_items = [row for row in strong if len(row) >= 3 and str(row[0]).startswith("1,500+")]
    if not strong_gold_items:
        issues.append({"error": "missing_strong_1500_gold_item_check"})
    else:
        _, status, evidence = strong_gold_items[0]
        if bool(status):
            issues.append({"error": "strong_1500_gold_item_unexpectedly_passed_pre_human", "evidence": evidence})

    expected_readiness = {
        "strong.gold_items": "pending_human",
        "strong.gold_chunks": "pending_human",
        "min.gold_items": "pending_human",
        "min.gold_chunks": "pending_human",
        "min.iaa": "pending_human",
        "min.gold_sampling_ready": "pass",
        "min.proposed": "partial",
    }
    for item_id, expected_status in expected_readiness.items():
        readiness_item = readiness_by_id.get(item_id)
        compliance_item = compliance_by_id.get(item_id)
        if not readiness_item:
            issues.append({"error": "missing_readiness_item", "id": item_id})
            continue
        if readiness_item.get("status") != expected_status:
            issues.append(
                {
                    "error": "unexpected_readiness_status",
                    "id": item_id,
                    "expected": expected_status,
                    "actual": readiness_item.get("status"),
                }
            )
        if item_id.startswith("strong.") and readiness_item.get("claimable"):
            issues.append({"error": "strong_human_item_marked_claimable", "id": item_id})
        if not compliance_item:
            issues.append({"error": "missing_compliance_item", "id": item_id})
        elif compliance_item.get("status") != readiness_item.get("status"):
            issues.append(
                {
                    "error": "compliance_readiness_status_mismatch",
                    "id": item_id,
                    "readiness": readiness_item.get("status"),
                    "compliance": compliance_item.get("status"),
                }
            )

    if not checklist_md_path.exists():
        issues.append({"error": "missing_markdown", "path": rel(checklist_md_path)})
    else:
        text = checklist_md_path.read_text(encoding="utf-8")
        for pattern in [
            "## Minimum-Accept Checklist",
            "## Strong-Accept Checklist",
            "Priority-100 gold subset sampling ready",
            "1,500+ gold edge/evidence item",
            "silver/proxy diagnostic",
        ]:
            if pattern not in text:
                issues.append({"error": "missing_markdown_pattern", "pattern": pattern})

    if issues:
        add_check(
            checks,
            "paper_readiness_checklist",
            "FAIL",
            "Paper readiness checklist is incomplete or not synchronized with strong/minimum human gates.",
            {"path": rel(checklist_path), "issues": issues[:50]},
        )
        return

    add_check(
        checks,
        "paper_readiness_checklist",
        "PASS",
        "Paper readiness checklist separates minimum and strong-accept gates and tracks the 1,500+ gold item requirement.",
        {
            "path": rel(checklist_path),
            "markdown": rel(checklist_md_path),
            "minimum_items": len(minimum),
            "strong_items": len(strong),
            "strong_gold_items_status": strong_gold_items[0][1],
            "readiness_items": len(readiness.get("items", [])),
            "compliance_items": len(compliance.get("checklist_rows", [])),
        },
    )


def validate_rq_evidence_matrix(checks, exp_dir):
    release_dir = exp_dir / "06_release"
    matrix_path = release_dir / "rq_evidence_matrix.json"
    matrix_md_path = release_dir / "rq_evidence_matrix.md"
    try:
        matrix = read_json(matrix_path)
    except Exception as exc:
        add_check(
            checks,
            "rq_evidence_matrix",
            "FAIL",
            "RQ-to-evidence matrix cannot be read.",
            {"error": str(exc), "path": rel(matrix_path)},
        )
        return

    rows = matrix.get("research_questions") or []
    summary = matrix.get("summary") or {}
    expected_ids = ["RQ1", "RQ2", "RQ3", "RQ4"]
    actual_ids = [row.get("rq_id") for row in rows]
    expected_statuses = {
        "RQ1": "automatic_diagnostic_ready_human_gold_pending",
        "RQ2": "structural_diagnostic_ready_human_gold_pending",
        "RQ3": "candidate_pipeline_ready_expert_review_pending",
        "RQ4": "review_queue_ready_human_effort_pending",
    }
    issues = []

    if actual_ids != expected_ids:
        issues.append({"error": "rq_ids_mismatch", "expected": expected_ids, "actual": actual_ids})
    if summary.get("rq_count") != 4:
        issues.append({"error": "unexpected_rq_count", "actual": summary.get("rq_count")})
    if summary.get("claim_ready_count") != 0:
        issues.append({"error": "pre_human_claim_ready_count_not_zero", "actual": summary.get("claim_ready_count")})
    if summary.get("human_or_expert_pending_count") != 4:
        issues.append({"error": "unexpected_pending_rq_count", "actual": summary.get("human_or_expert_pending_count")})
    if summary.get("missing_required_evidence_files") != 0:
        issues.append({"error": "matrix_reports_missing_evidence", "actual": summary.get("missing_required_evidence_files")})

    for row in rows:
        rq_id = row.get("rq_id")
        if row.get("current_status") != expected_statuses.get(rq_id):
            issues.append(
                {
                    "error": "unexpected_rq_status",
                    "rq_id": rq_id,
                    "expected": expected_statuses.get(rq_id),
                    "actual": row.get("current_status"),
                }
            )
        if row.get("claim_ready") is not False:
            issues.append({"error": "rq_marked_claim_ready_pre_human", "rq_id": rq_id, "claim_ready": row.get("claim_ready")})
        if not row.get("remaining_for_final_claim"):
            issues.append({"error": "missing_remaining_for_final_claim", "rq_id": rq_id})
        files = row.get("evidence_files") or []
        if not files:
            issues.append({"error": "missing_evidence_files", "rq_id": rq_id})
        for item in files:
            if item.get("required") and not item.get("exists"):
                issues.append({"error": "required_evidence_missing", "rq_id": rq_id, "path": item.get("path"), "role": item.get("role")})

        current_values = row.get("current_values") or {}
        if rq_id == "RQ2" and current_values.get("cq_count") != 12:
            issues.append({"error": "rq2_cq_count_not_12", "actual": current_values.get("cq_count")})
        if rq_id == "RQ3" and int(current_values.get("mapping_pending_rows") or 0) <= 0:
            issues.append({"error": "rq3_mapping_pending_rows_not_positive", "actual": current_values.get("mapping_pending_rows")})
        if rq_id == "RQ4" and current_values.get("human_effort_reviewed_file_present") is not False:
            issues.append(
                {
                    "error": "rq4_human_effort_unexpectedly_present_pre_human",
                    "actual": current_values.get("human_effort_reviewed_file_present"),
                }
            )

    if matrix.get("missing_required_evidence_files"):
        issues.append({"error": "top_level_missing_required_evidence", "items": matrix.get("missing_required_evidence_files")[:20]})

    if not matrix_md_path.exists():
        issues.append({"error": "missing_markdown", "path": rel(matrix_md_path)})
    else:
        text = matrix_md_path.read_text(encoding="utf-8")
        for pattern in [
            "## RQ Matrix",
            "RQ1",
            "RQ2",
            "RQ3",
            "RQ4",
            "human-gold",
            "expert review",
            "active review",
        ]:
            if pattern not in text:
                issues.append({"error": "missing_markdown_pattern", "pattern": pattern})

    if issues:
        add_check(
            checks,
            "rq_evidence_matrix",
            "FAIL",
            "RQ-to-evidence matrix is incomplete or not synchronized with current pre-human claim state.",
            {"path": rel(matrix_path), "issues": issues[:50]},
        )
        return

    add_check(
        checks,
        "rq_evidence_matrix",
        "PASS",
        "RQ-to-evidence matrix covers RQ1-RQ4, all required evidence files exist, and final claims remain gated by human/expert review.",
        {
            "path": rel(matrix_path),
            "markdown": rel(matrix_md_path),
            "rq_count": len(rows),
            "claim_ready_count": summary.get("claim_ready_count"),
            "human_or_expert_pending_count": summary.get("human_or_expert_pending_count"),
        },
    )


def validate_reviewer_risk_register(checks, exp_dir):
    release_dir = exp_dir / "06_release"
    json_path = release_dir / "reviewer_risk_register.json"
    csv_path = release_dir / "reviewer_risk_register.csv"
    md_path = release_dir / "reviewer_risk_register.md"
    try:
        register = read_json(json_path)
        csv_rows = read_csv_rows(csv_path)
    except Exception as exc:
        add_check(
            checks,
            "reviewer_risk_register",
            "FAIL",
            "Reviewer risk register cannot be read.",
            {"error": str(exc), "path": rel(json_path)},
        )
        return

    summary = register.get("summary") or {}
    source_status = register.get("source_status") or {}
    risks = register.get("risks") or []
    expected_ids = [
        "R01_task_framing",
        "R02_human_gold_missing",
        "R03_silver_proxy_overclaim",
        "R04_method_novelty",
        "R05_public_reproducibility",
        "R06_public_benchmark_generalization",
        "R07_mapping_downstream_labels",
        "R08_crosswalk_downstream_utility",
        "R09_active_review_effort",
        "R10_structural_validity",
        "R11_llm_reproducibility",
        "R12_release_bundle_safety",
        "R13_submission_status_overclaim",
    ]
    expected_open = {
        "R02_human_gold_missing",
        "R07_mapping_downstream_labels",
        "R08_crosswalk_downstream_utility",
        "R09_active_review_effort",
        "R13_submission_status_overclaim",
    }
    risk_ids = [row.get("risk_id") for row in risks]
    open_ids = {
        row.get("risk_id")
        for row in risks
        if str(row.get("current_status") or "").startswith("open_")
    }
    issues = []

    if risk_ids != expected_ids:
        issues.append({"error": "risk_ids_mismatch", "expected": expected_ids, "actual": risk_ids})
    if set(summary.get("open_risk_ids") or []) != expected_open:
        issues.append({"error": "summary_open_risk_ids_mismatch", "expected": sorted(expected_open), "actual": summary.get("open_risk_ids")})
    if open_ids != expected_open:
        issues.append({"error": "open_risk_ids_mismatch", "expected": sorted(expected_open), "actual": sorted(open_ids)})
    if summary.get("risk_count") != 13 or len(risks) != 13:
        issues.append({"error": "unexpected_risk_count", "summary": summary.get("risk_count"), "actual": len(risks)})
    if summary.get("critical_count") != 2:
        issues.append({"error": "unexpected_critical_count", "actual": summary.get("critical_count")})
    if summary.get("high_count") != 5:
        issues.append({"error": "unexpected_high_count", "actual": summary.get("high_count")})
    if summary.get("open_count") != 5:
        issues.append({"error": "unexpected_open_count", "actual": summary.get("open_count")})
    if summary.get("missing_required_evidence_file_count") != 0:
        issues.append(
            {
                "error": "missing_required_evidence_files",
                "actual": summary.get("missing_required_evidence_file_count"),
            }
        )
    if summary.get("claim_status") != "reviewer_risk_register_ready_with_open_human_gates":
        issues.append({"error": "unexpected_claim_status", "actual": summary.get("claim_status")})
    if len(csv_rows) != 13:
        issues.append({"error": "unexpected_csv_row_count", "actual": len(csv_rows)})

    prehuman_path = release_dir / "pre_human_handoff_validation.json"
    prehuman_md_path = release_dir / "pre_human_handoff_validation.md"
    try:
        prehuman = read_json(prehuman_path)
    except Exception as exc:
        prehuman = {}
        issues.append({"error": "cannot_read_pre_human_validation", "path": rel(prehuman_path), "detail": str(exc)})
    if "pre_human_check_count" in source_status:
        issues.append(
            {
                "error": "legacy_stale_prone_pre_human_check_count_field",
                "actual": source_status.get("pre_human_check_count"),
            }
        )
    if "pre_human_validation_status" in source_status:
        issues.append({"error": "legacy_stale_prone_pre_human_validation_status_field"})
    if "pre_human_validation_claim_status" in source_status:
        issues.append({"error": "legacy_stale_prone_pre_human_validation_claim_status_field"})
    if source_status.get("pre_human_validation_source_json") != rel(prehuman_path):
        issues.append(
            {
                "error": "pre_human_validation_source_json_mismatch",
                "actual": source_status.get("pre_human_validation_source_json"),
            }
        )
    if source_status.get("pre_human_validation_source_md") != rel(prehuman_md_path):
        issues.append(
            {
                "error": "pre_human_validation_source_md_mismatch",
                "actual": source_status.get("pre_human_validation_source_md"),
            }
        )

    for row in risks:
        risk_id = row.get("risk_id")
        if not row.get("reviewer_concern"):
            issues.append({"error": "missing_reviewer_concern", "risk_id": risk_id})
        if not row.get("remaining_action"):
            issues.append({"error": "missing_remaining_action", "risk_id": risk_id})
        evidence_files = row.get("evidence_files") or []
        if len(evidence_files) < 2:
            issues.append({"error": "too_few_evidence_files", "risk_id": risk_id, "count": len(evidence_files)})
        if row.get("present_evidence_file_count") != len(evidence_files):
            issues.append(
                {
                    "error": "evidence_file_coverage_not_complete",
                    "risk_id": risk_id,
                    "present": row.get("present_evidence_file_count"),
                    "total": len(evidence_files),
                }
            )
        if row.get("missing_required_evidence_files"):
            issues.append(
                {
                    "error": "risk_reports_missing_required_evidence",
                    "risk_id": risk_id,
                    "missing": row.get("missing_required_evidence_files"),
                }
            )
        for item in evidence_files:
            if item.get("required") and (item.get("exists") is not True or not Path(item.get("path", "")).exists()):
                issues.append({"error": "required_evidence_missing_on_disk", "risk_id": risk_id, "path": item.get("path")})
        if risk_id in expected_open and row.get("paper_claim_allowed_now") is not False:
            issues.append({"error": "open_risk_marked_claimable", "risk_id": risk_id})
        evidence_paths = {item.get("path") for item in evidence_files}
        if risk_id == "R05_public_reproducibility":
            required_public_repro = {
                rel(release_dir / "public_reproducibility_manifest.md"),
                rel(release_dir / "public_reproducibility_manifest.json"),
            }
            missing_public_repro = sorted(required_public_repro - evidence_paths)
            if missing_public_repro:
                issues.append(
                    {
                        "error": "public_reproducibility_risk_missing_manifest_evidence",
                        "missing": missing_public_repro,
                    }
                )
            if "public-safe reproducibility rows=" not in str(row.get("current_evidence") or ""):
                issues.append({"error": "public_reproducibility_risk_missing_row_summary"})
        if risk_id == "R12_release_bundle_safety":
            if rel(release_dir / "public_reproducibility_manifest.md") not in evidence_paths:
                issues.append({"error": "release_bundle_safety_missing_public_repro_manifest_evidence"})

    if not md_path.exists():
        issues.append({"error": "missing_markdown", "path": rel(md_path)})
    else:
        text = md_path.read_text(encoding="utf-8")
        for pattern in [
            "CAPE-KG Reviewer Risk Register",
            "Open risks: 5",
            "R02_human_gold_missing",
            "R07_mapping_downstream_labels",
            "R08_crosswalk_downstream_utility",
            "not_submission_ready",
            "diagnostic_only_until_gold",
        ]:
            if pattern not in text:
                issues.append({"error": "missing_markdown_pattern", "pattern": pattern})
        if "pre_human_check_count" in text:
            issues.append({"error": "legacy_stale_prone_pre_human_check_count_in_markdown"})

    if issues:
        add_check(
            checks,
            "reviewer_risk_register",
            "FAIL",
            "Reviewer risk register is incomplete or not synchronized with current claim blockers.",
            {"path": rel(json_path), "issues": issues[:80]},
        )
        return

    add_check(
        checks,
        "reviewer_risk_register",
        "PASS",
        "Reviewer risk register covers 13 likely reviewer concerns, has complete evidence coverage, and keeps human/expert blockers open.",
        {
            "path": rel(json_path),
            "markdown": rel(md_path),
            "risk_count": len(risks),
            "open_risk_ids": sorted(expected_open),
            "claim_status": summary.get("claim_status"),
        },
    )


def validate_cq_query_pack(checks, exp_dir):
    release_dir = exp_dir / "06_release"
    json_path = release_dir / "cq_query_pack.json"
    md_path = release_dir / "cq_query_pack.md"
    csv_path = exp_dir / "04_evaluation/cq_query_sample_answers.csv"
    try:
        pack = read_json(json_path)
    except Exception as exc:
        add_check(
            checks,
            "cq_query_pack",
            "FAIL",
            "CQ query pack JSON cannot be read.",
            {"error": str(exc), "path": rel(json_path)},
        )
        return

    summary = pack.get("summary") or {}
    queries = pack.get("queries") or []
    expected_ids = [f"CQ{i}" for i in range(1, 13)]
    actual_ids = [row.get("cq_id") for row in queries]
    issues = []

    if summary.get("cq_count") != 12:
        issues.append({"error": "unexpected_cq_count", "actual": summary.get("cq_count")})
    if summary.get("answerable_cq_count") != 12:
        issues.append({"error": "unexpected_answerable_cq_count", "actual": summary.get("answerable_cq_count")})
    try:
        rate = float(summary.get("cq_answerability_rate"))
    except (TypeError, ValueError):
        rate = None
    if rate is None or abs(rate - 1.0) > 0.000001:
        issues.append({"error": "unexpected_cq_answerability_rate", "actual": summary.get("cq_answerability_rate")})
    if summary.get("cq_with_no_support") != []:
        issues.append({"error": "unexpected_cq_with_no_support", "actual": summary.get("cq_with_no_support")})
    if summary.get("claim_status") != "cq_query_pack_ready_not_human_gold_answer_correctness":
        issues.append({"error": "unexpected_claim_status", "actual": summary.get("claim_status")})

    if actual_ids != expected_ids:
        issues.append({"error": "cq_ids_mismatch", "expected": expected_ids, "actual": actual_ids})
    for row in queries:
        cq_id = row.get("cq_id")
        if not row.get("question"):
            issues.append({"error": "missing_question", "cq_id": cq_id})
        if not row.get("cypher") or "MATCH" not in row.get("cypher", ""):
            issues.append({"error": "missing_or_invalid_cypher", "cq_id": cq_id})
        if not row.get("sparql") or "SELECT" not in row.get("sparql", ""):
            issues.append({"error": "missing_or_invalid_sparql", "cq_id": cq_id})
        if cq_id in expected_ids:
            if int(row.get("supporting_item_count") or 0) <= 0:
                issues.append({"error": "cq_should_have_support", "cq_id": cq_id, "actual": row.get("supporting_item_count")})
            if row.get("answerable_by_current_kg") is not True:
                issues.append({"error": "cq_should_be_answerable", "cq_id": cq_id, "actual": row.get("answerable_by_current_kg")})

    if not csv_path.exists():
        issues.append({"error": "missing_sample_answer_csv", "path": rel(csv_path)})
        sample_rows = []
    else:
        try:
            with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
                sample_rows = list(csv.DictReader(f))
        except Exception as exc:
            issues.append({"error": "cannot_read_sample_answer_csv", "path": rel(csv_path), "detail": str(exc)})
            sample_rows = []
        required_fields = {"cq_id", "answer_type", "id", "predicate", "source_label", "target_label"}
        if sample_rows:
            missing_fields = sorted(required_fields - set(sample_rows[0].keys()))
            if missing_fields:
                issues.append({"error": "sample_answer_csv_missing_fields", "missing": missing_fields})
        if len(sample_rows) < 50:
            issues.append({"error": "too_few_sample_answer_rows", "actual": len(sample_rows)})
        if summary.get("sample_answer_rows") != len(sample_rows):
            issues.append(
                {
                    "error": "sample_answer_row_count_mismatch",
                    "summary": summary.get("sample_answer_rows"),
                    "actual": len(sample_rows),
                }
            )

    if not md_path.exists():
        issues.append({"error": "missing_markdown", "path": rel(md_path)})
    else:
        text = md_path.read_text(encoding="utf-8")
        for pattern in [
            "## CQ Query Overview",
            "CQ8",
            "Cypher",
            "SPARQL-style Query",
            "human-gold",
        ]:
            if pattern not in text:
                issues.append({"error": "missing_markdown_pattern", "pattern": pattern})

    if issues:
        add_check(
            checks,
            "cq_query_pack",
            "FAIL",
            "CQ query pack is incomplete or not synchronized with current KG query support.",
            {"path": rel(json_path), "issues": issues[:50]},
        )
        return

    add_check(
        checks,
        "cq_query_pack",
        "PASS",
        "CQ query pack links all 12 competency questions to KG queries and sample answers.",
        {
            "json": rel(json_path),
            "markdown": rel(md_path),
            "sample_answers": rel(csv_path),
            "cq_count": summary.get("cq_count"),
            "answerable_cq_count": summary.get("answerable_cq_count"),
            "cq_with_no_support": summary.get("cq_with_no_support"),
            "sample_answer_rows": len(sample_rows),
            "claim_status": summary.get("claim_status"),
        },
    )


def validate_human_gold_span_iou(checks, exp_dir):
    eval_dir = exp_dir / "04_evaluation"
    json_path = eval_dir / "human_gold_span_iou_metrics.json"
    csv_path = eval_dir / "human_gold_span_iou_components.csv"
    md_path = eval_dir / "human_gold_span_iou_report.md"
    try:
        payload = read_json(json_path)
    except Exception as exc:
        add_check(
            checks,
            "human_gold_span_iou_evaluator",
            "FAIL",
            "Human-gold component span IoU metrics JSON cannot be read.",
            {"error": str(exc), "path": rel(json_path)},
        )
        return

    summary = payload.get("summary") or {}
    issues = []
    allowed_claim_statuses = {
        "pending_human_adjudication",
        "pending_human_component_spans",
        "human_gold_span_iou_scored",
    }
    if summary.get("claim_status") not in allowed_claim_statuses:
        issues.append({"error": "unexpected_claim_status", "actual": summary.get("claim_status")})
    if int(summary.get("candidate_rows") or 0) < 100:
        issues.append({"error": "too_few_candidate_rows", "actual": summary.get("candidate_rows")})
    if int(summary.get("candidate_edge_count") or 0) <= 0:
        issues.append({"error": "candidate_edge_count_not_positive", "actual": summary.get("candidate_edge_count")})
    if int(summary.get("candidate_component_span_count") or 0) <= 0:
        issues.append({"error": "candidate_component_span_count_not_positive", "actual": summary.get("candidate_component_span_count")})
    if int(summary.get("completed_adjudicated_chunks") or 0) == 0:
        if summary.get("claim_status") != "pending_human_adjudication":
            issues.append({"error": "pre_human_span_iou_should_be_pending", "actual": summary.get("claim_status")})
        if summary.get("span_exact_match_rate") is not None or summary.get("mean_span_iou") is not None:
            issues.append(
                {
                    "error": "pre_human_span_metrics_should_be_null",
                    "span_exact_match_rate": summary.get("span_exact_match_rate"),
                    "mean_span_iou": summary.get("mean_span_iou"),
                }
            )
    if set((summary.get("component_exact_match_rate") or {}).keys()) != {"subject", "predicate", "object"}:
        issues.append({"error": "missing_component_exact_keys", "actual": summary.get("component_exact_match_rate")})
    if set((summary.get("component_mean_iou") or {}).keys()) != {"subject", "predicate", "object"}:
        issues.append({"error": "missing_component_iou_keys", "actual": summary.get("component_mean_iou")})

    if not csv_path.exists():
        issues.append({"error": "missing_component_rows_csv", "path": rel(csv_path)})
    else:
        try:
            with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
                fieldnames = list(csv.DictReader(f).fieldnames or [])
        except Exception as exc:
            fieldnames = []
            issues.append({"error": "cannot_read_component_rows_csv", "path": rel(csv_path), "detail": str(exc)})
        required_fields = {"chunk_id", "edge_key", "component", "iou", "exact_match"}
        missing_fields = sorted(required_fields - set(fieldnames))
        if missing_fields:
            issues.append({"error": "component_rows_csv_missing_fields", "missing": missing_fields})

    if not md_path.exists():
        issues.append({"error": "missing_report", "path": rel(md_path)})
    else:
        text = md_path.read_text(encoding="utf-8")
        for pattern in ["Component Span IoU", "Span exact match rate", "Mean span IoU", "paper-claimable"]:
            if pattern not in text:
                issues.append({"error": "missing_report_pattern", "pattern": pattern})

    if issues:
        add_check(
            checks,
            "human_gold_span_iou_evaluator",
            "FAIL",
            "Human-gold component span IoU evaluator artifacts are incomplete or inconsistent.",
            {"path": rel(json_path), "issues": issues[:50]},
        )
        return

    add_check(
        checks,
        "human_gold_span_iou_evaluator",
        "PASS",
        "Human-gold component span exact/IoU evaluator is ready and conservatively pending adjudicated span returns.",
        {
            "json": rel(json_path),
            "csv": rel(csv_path),
            "report": rel(md_path),
            "claim_status": summary.get("claim_status"),
            "candidate_edges": summary.get("candidate_edge_count"),
            "candidate_component_spans": summary.get("candidate_component_span_count"),
            "completed_adjudicated_chunks": summary.get("completed_adjudicated_chunks"),
        },
    )


def validate_evidence_grounding_report_safety(checks, exp_dir):
    report_path = exp_dir / "04_evaluation/evidence_grounding_report.md"
    if not report_path.exists():
        add_check(
            checks,
            "evidence_grounding_report_claim_safety",
            "FAIL",
            "Evidence grounding report is missing.",
            {"path": rel(report_path)},
        )
        return
    text = report_path.read_text(encoding="utf-8", errors="replace")
    issues = []
    required_patterns = [
        "Claim status: `silver_proxy_evidence_grounding_diagnostic_not_human_gold`",
        "not paper-claimable human-gold evidence metrics",
        "human_gold_span_iou_metrics.json",
        "## Summary Table",
        "silver/proxy only",
    ]
    for pattern in required_patterns:
        if pattern not in text:
            issues.append({"error": "missing_claim_safety_pattern", "pattern": pattern})
    stale_patterns = [
        "- B0_plain_llm_proxy: EM=",
        "- B1_predicate_constrained_proxy: EM=",
        "- P_cape_kg_silver: EM=",
    ]
    hits = [pattern for pattern in stale_patterns if pattern in text]
    if hits:
        issues.append({"error": "stale_bullet_only_evidence_report_patterns", "patterns": hits})
    expected_conditions = {
        "B0_plain_llm_proxy",
        "B1_predicate_constrained_proxy",
        "B2_current_project_baseline",
        "P_cape_kg_silver",
        "P_minus_Evidence_proxy",
    }
    missing_conditions = sorted(condition for condition in expected_conditions if condition not in text)
    if missing_conditions:
        issues.append({"error": "missing_expected_condition_rows", "conditions": missing_conditions})

    if issues:
        add_check(
            checks,
            "evidence_grounding_report_claim_safety",
            "FAIL",
            "Evidence grounding report is missing conservative claim-safety context.",
            {"path": rel(report_path), "issues": issues},
        )
        return
    add_check(
        checks,
        "evidence_grounding_report_claim_safety",
        "PASS",
        "Evidence grounding report is explicitly scoped as silver/proxy and not human-gold evidence.",
        {"path": rel(report_path), "expected_conditions_checked": sorted(expected_conditions)},
    )


def validate_evidence_span_granularity_claim_safety(checks, exp_dir, outputs_dir):
    exp_dir = Path(exp_dir)
    outputs_dir = Path(outputs_dir)
    metrics_path = exp_dir / "04_evaluation/evidence_span_granularity_metrics.json"
    report_path = exp_dir / "04_evaluation/evidence_span_granularity_report.md"
    component_csv_path = exp_dir / "04_evaluation/evidence_span_granularity_components.csv"
    component_jsonl_path = outputs_dir / "06_triples/layer2_triples_component_spans.jsonl"
    issues = []

    try:
        metrics = read_json(metrics_path)
    except Exception as exc:
        metrics = {}
        issues.append({"error": "cannot_read_span_granularity_metrics", "path": rel(metrics_path), "detail": str(exc)})

    if metrics:
        triple_count = int(metrics.get("triple_count") or 0)
        component_count = int(metrics.get("component_count") or 0)
        exact_count = int(metrics.get("exact_component_span_count") or 0)
        chunk_count = int(metrics.get("chunk_span_count") or 0)
        predicate_proxy_count = int(metrics.get("predicate_full_sentence_proxy_count") or 0)
        if metrics.get("claim_status") != "automatic_component_span_diagnostic_not_human_gold":
            issues.append({"error": "unexpected_span_granularity_claim_status", "actual": metrics.get("claim_status")})
        if triple_count <= 0:
            issues.append({"error": "span_granularity_triple_count_not_positive", "actual": triple_count})
        if component_count != triple_count * 3:
            issues.append({"error": "component_count_not_three_per_triple", "triple_count": triple_count, "component_count": component_count})
        if not (0 <= exact_count <= component_count):
            issues.append({"error": "exact_component_span_count_out_of_range", "exact": exact_count, "components": component_count})
        if not (0 <= chunk_count <= component_count):
            issues.append({"error": "chunk_span_count_out_of_range", "chunk_spans": chunk_count, "components": component_count})
        if predicate_proxy_count != triple_count:
            issues.append({"error": "predicate_proxy_count_not_one_per_triple", "predicate_proxy_count": predicate_proxy_count, "triple_count": triple_count})
        method_counts = metrics.get("method_counts") or {}
        for key in [
            "subject.exact",
            "object.exact",
            "predicate.full_sentence_proxy",
            "subject.label_not_found_in_sentence",
            "object.label_not_found_in_sentence",
        ]:
            if key not in method_counts:
                issues.append({"error": "missing_span_method_count", "key": key})
        limitations = " ".join(str(item) for item in metrics.get("limitations") or [])
        for pattern in [
            "lexical exact-match diagnostics",
            "full-sentence proxy",
            "adjudicated human-gold spans",
        ]:
            if pattern not in limitations:
                issues.append({"error": "missing_span_granularity_limitation", "pattern": pattern})

    if not component_jsonl_path.exists():
        issues.append({"error": "missing_component_span_jsonl", "path": rel(component_jsonl_path)})
    elif metrics:
        jsonl_rows = sum(1 for _ in component_jsonl_path.open("r", encoding="utf-8"))
        if jsonl_rows != int(metrics.get("triple_count") or 0):
            issues.append({"error": "component_span_jsonl_row_count_mismatch", "rows": jsonl_rows, "triple_count": metrics.get("triple_count")})

    if not component_csv_path.exists():
        issues.append({"error": "missing_component_span_csv", "path": rel(component_csv_path)})
    else:
        try:
            component_rows = read_csv_rows(component_csv_path)
        except Exception as exc:
            component_rows = []
            issues.append({"error": "cannot_read_component_span_csv", "path": rel(component_csv_path), "detail": str(exc)})
        if metrics and len(component_rows) != int(metrics.get("component_count") or 0):
            issues.append({"error": "component_span_csv_row_count_mismatch", "rows": len(component_rows), "component_count": metrics.get("component_count")})

    if not report_path.exists():
        issues.append({"error": "missing_span_granularity_report", "path": rel(report_path)})
    else:
        text = report_path.read_text(encoding="utf-8", errors="replace")
        for pattern in [
            "not a human-gold span evaluation",
            "Claim status: `automatic_component_span_diagnostic_not_human_gold`",
            "Predicate evidence is still sentence-level proxy evidence",
            "human annotation is needed for predicate-token evidence spans",
        ]:
            if pattern not in text:
                issues.append({"error": "missing_span_granularity_report_pattern", "pattern": pattern})

    if issues:
        add_check(
            checks,
            "evidence_span_granularity_claim_safety",
            "FAIL",
            "Evidence span granularity diagnostic is missing, inconsistent, or overclaims human-gold span evidence.",
            {"issues": issues[:50]},
        )
        return

    add_check(
        checks,
        "evidence_span_granularity_claim_safety",
        "PASS",
        "Component span granularity diagnostic is internally consistent and scoped as non-human-gold evidence.",
        {
            "metrics": rel(metrics_path),
            "report": rel(report_path),
            "component_jsonl": rel(component_jsonl_path),
            "component_csv": rel(component_csv_path),
            "triple_count": metrics.get("triple_count"),
            "component_count": metrics.get("component_count"),
            "exact_component_span_rate": metrics.get("exact_component_span_rate"),
            "predicate_full_sentence_proxy_rate": metrics.get("predicate_full_sentence_proxy_rate"),
            "claim_status": metrics.get("claim_status"),
        },
    )


def validate_predicate_cue_span_diagnostic(checks, exp_dir, outputs_dir):
    exp_dir = Path(exp_dir)
    outputs_dir = Path(outputs_dir)
    metrics_path = exp_dir / "04_evaluation/predicate_cue_span_metrics.json"
    report_path = exp_dir / "04_evaluation/predicate_cue_span_report.md"
    cue_jsonl_path = outputs_dir / "06_triples/layer2_predicate_cue_spans.jsonl"
    cue_csv_path = exp_dir / "04_evaluation/predicate_cue_span_rows.csv"
    triples_path = outputs_dir / "06_triples/layer2_triples_schema_valid.jsonl"
    expected_claim_status = "automatic_predicate_cue_span_diagnostic_not_human_gold"
    issues = []

    try:
        metrics = read_json(metrics_path)
    except Exception as exc:
        metrics = {}
        issues.append({"error": "cannot_read_predicate_cue_metrics", "path": rel(metrics_path), "detail": str(exc)})

    try:
        rows = read_jsonl(cue_jsonl_path)
    except Exception as exc:
        rows = []
        issues.append({"error": "cannot_read_predicate_cue_jsonl", "path": rel(cue_jsonl_path), "detail": str(exc)})

    try:
        csv_rows = read_csv_rows(cue_csv_path)
    except Exception as exc:
        csv_rows = []
        issues.append({"error": "cannot_read_predicate_cue_csv", "path": rel(cue_csv_path), "detail": str(exc)})

    try:
        triples = read_jsonl(triples_path)
    except Exception as exc:
        triples = []
        issues.append({"error": "cannot_read_schema_valid_triples", "path": rel(triples_path), "detail": str(exc)})

    if metrics:
        triple_count = int(metrics.get("triple_count") or 0)
        cue_count = int(metrics.get("predicate_cue_span_count") or 0)
        missing_count = int(metrics.get("predicate_cue_missing_count") or 0)
        chunk_span_count = int(metrics.get("chunk_span_count") or 0)
        if metrics.get("claim_status") != expected_claim_status:
            issues.append({"error": "unexpected_predicate_cue_claim_status", "expected": expected_claim_status, "actual": metrics.get("claim_status")})
        if metrics.get("source_text_included") is not False:
            issues.append({"error": "predicate_cue_source_text_included_not_false", "actual": metrics.get("source_text_included")})
        if triple_count <= 0:
            issues.append({"error": "predicate_cue_triple_count_not_positive", "actual": triple_count})
        if triple_count != len(triples):
            issues.append({"error": "predicate_cue_triple_count_mismatch", "metrics": triple_count, "schema_valid_triples": len(triples)})
        if triple_count != len(rows):
            issues.append({"error": "predicate_cue_jsonl_row_count_mismatch", "metrics": triple_count, "jsonl_rows": len(rows)})
        if len(csv_rows) != len(rows):
            issues.append({"error": "predicate_cue_csv_row_count_mismatch", "csv_rows": len(csv_rows), "jsonl_rows": len(rows)})
        if cue_count + missing_count != triple_count:
            issues.append({"error": "predicate_cue_match_missing_sum_mismatch", "cue_count": cue_count, "missing_count": missing_count, "triple_count": triple_count})
        if not (0 <= cue_count <= triple_count):
            issues.append({"error": "predicate_cue_count_out_of_range", "cue_count": cue_count, "triple_count": triple_count})
        if not (0 <= chunk_span_count <= triple_count):
            issues.append({"error": "predicate_cue_chunk_span_count_out_of_range", "chunk_span_count": chunk_span_count, "triple_count": triple_count})

    row_predicate_counts = Counter(row.get("predicate") for row in rows)
    row_match_counts = Counter(
        row.get("predicate")
        for row in rows
        if row.get("cue_method") == "predicate_cue_lexical_match"
    )
    row_method_counts = Counter(row.get("cue_method") for row in rows)
    row_chunk_span_count = sum(1 for row in rows if row.get("chunk_span_start") not in (None, ""))
    if metrics:
        if dict(sorted(row_method_counts.items())) != metrics.get("method_counts"):
            issues.append({"error": "predicate_cue_method_counts_mismatch", "expected": dict(sorted(row_method_counts.items())), "actual": metrics.get("method_counts")})
        if row_chunk_span_count != int(metrics.get("chunk_span_count") or 0):
            issues.append({"error": "predicate_cue_chunk_span_count_mismatch", "expected": row_chunk_span_count, "actual": metrics.get("chunk_span_count")})
        for predicate, total in sorted(row_predicate_counts.items()):
            summary = (metrics.get("by_predicate") or {}).get(predicate)
            if not summary:
                issues.append({"error": "predicate_cue_missing_by_predicate_summary", "predicate": predicate})
                continue
            matched = row_match_counts.get(predicate, 0)
            if summary.get("triple_count") != total:
                issues.append({"error": "predicate_cue_by_predicate_total_mismatch", "predicate": predicate, "expected": total, "actual": summary.get("triple_count")})
            if summary.get("predicate_cue_span_count") != matched:
                issues.append({"error": "predicate_cue_by_predicate_match_mismatch", "predicate": predicate, "expected": matched, "actual": summary.get("predicate_cue_span_count")})

    allowed_methods = {"predicate_cue_lexical_match", "predicate_cue_not_found"}
    forbidden_fields = {"text", "source_text", "evidence_text"}
    triple_ids = [row.get("triple_id") for row in rows if row.get("triple_id")]
    if len(triple_ids) != len(set(triple_ids)):
        issues.append({"error": "predicate_cue_triple_ids_not_unique", "rows": len(triple_ids), "unique": len(set(triple_ids))})
    for row in rows:
        if row.get("cue_method") not in allowed_methods:
            issues.append({"error": "predicate_cue_unknown_method", "line": row.get("_line_no"), "method": row.get("cue_method")})
        if row.get("cue_text_included") is not False:
            issues.append({"error": "predicate_cue_text_included_not_false", "line": row.get("_line_no"), "actual": row.get("cue_text_included")})
        if forbidden_fields.intersection(row):
            issues.append({"error": "predicate_cue_jsonl_contains_source_text_field", "line": row.get("_line_no"), "fields": sorted(forbidden_fields.intersection(row))})
        char_count = int(row.get("cue_text_char_count") or 0)
        has_span = row.get("cue_span_start") not in (None, "") and row.get("cue_span_end") not in (None, "")
        if row.get("cue_method") == "predicate_cue_lexical_match" and not has_span:
            issues.append({"error": "predicate_cue_lexical_match_missing_span", "line": row.get("_line_no"), "triple_id": row.get("triple_id")})
        if row.get("cue_method") == "predicate_cue_not_found" and has_span:
            issues.append({"error": "predicate_cue_not_found_has_span", "line": row.get("_line_no"), "triple_id": row.get("triple_id")})
        if char_count > 0 and not row.get("cue_text_sha256"):
            issues.append({"error": "predicate_cue_nonempty_text_missing_hash", "line": row.get("_line_no"), "triple_id": row.get("triple_id")})

    csv_fieldnames = csv_rows[0].keys() if csv_rows else []
    if forbidden_fields.intersection(csv_fieldnames):
        issues.append({"error": "predicate_cue_csv_contains_source_text_field", "fields": sorted(forbidden_fields.intersection(csv_fieldnames))})

    if report_path.exists():
        report_text = report_path.read_text(encoding="utf-8", errors="replace").lower()
        for pattern in [
            "not a human-gold predicate-span evaluation",
            "source text is omitted",
            "full-sentence proxy",
            "lexical cue diagnostic",
        ]:
            if pattern not in report_text:
                issues.append({"error": "predicate_cue_report_missing_pattern", "pattern": pattern})
    else:
        issues.append({"error": "missing_predicate_cue_report", "path": rel(report_path)})

    if metrics:
        limitations = " ".join(str(item) for item in metrics.get("limitations") or [])
        for pattern in [
            "lexical heuristics",
            "No source sentence text is included",
            "adjudicated human-gold span scoring",
        ]:
            if pattern not in limitations:
                issues.append({"error": "predicate_cue_missing_limitation", "pattern": pattern})

    if issues:
        add_check(
            checks,
            "predicate_cue_span_diagnostic",
            "FAIL",
            "Predicate cue span diagnostic is missing, inconsistent, or overclaims human-gold predicate spans.",
            {"issues": issues[:80]},
        )
        return

    add_check(
        checks,
        "predicate_cue_span_diagnostic",
        "PASS",
        "Automatic predicate cue span diagnostic is internally consistent and source-text safe.",
        {
            "metrics": rel(metrics_path),
            "report": rel(report_path),
            "predicate_cue_spans": rel(cue_jsonl_path),
            "predicate_cue_rows": rel(cue_csv_path),
            "triple_count": metrics.get("triple_count"),
            "predicate_cue_span_count": metrics.get("predicate_cue_span_count"),
            "predicate_cue_span_rate": metrics.get("predicate_cue_span_rate"),
            "source_text_included": False,
            "claim_status": metrics.get("claim_status"),
        },
    )


def validate_edge_component_span_traceability(checks, exp_dir, outputs_dir):
    exp_dir = Path(exp_dir)
    outputs_dir = Path(outputs_dir)
    summary_path = exp_dir / "06_release/edge_component_span_traceability.json"
    report_path = exp_dir / "06_release/edge_component_span_traceability.md"
    links_jsonl_path = outputs_dir / "13_evidence_graph/edge_component_span_links.jsonl"
    links_csv_path = outputs_dir / "13_evidence_graph/edge_component_span_links.csv"
    edges_path = outputs_dir / "07_layer2_graph/layer2_edges.jsonl"
    triples_path = outputs_dir / "06_triples/layer2_triples_component_spans.jsonl"

    try:
        summary = read_json(summary_path)
        report_text = report_path.read_text(encoding="utf-8", errors="replace")
        links = read_jsonl(links_jsonl_path)
        links_csv = read_csv_rows(links_csv_path)
        edges = read_jsonl(edges_path)
        triples = read_jsonl(triples_path)
    except Exception as exc:
        add_check(
            checks,
            "edge_component_span_traceability",
            "FAIL",
            "Edge-to-component span traceability files cannot be read.",
            {"error": str(exc)},
        )
        return

    issues = []
    edge_by_id = {row.get("edge_id"): row for row in edges if row.get("edge_id")}
    triple_by_id = {row.get("triple_id"): row for row in triples if row.get("triple_id")}
    edge_ids_with_source_triples = {
        row.get("edge_id")
        for row in edges
        if row.get("edge_id") and [triple_id for triple_id in as_list(row.get("source_triple_ids")) if triple_id]
    }
    expected_link_count = 0
    expected_edges_with_links = set()
    expected_linked_triples = set()
    missing_source_triples = []
    missing_component_span_triples = []
    for edge in edges:
        edge_id = edge.get("edge_id")
        source_triple_ids = [triple_id for triple_id in as_list(edge.get("source_triple_ids")) if triple_id]
        if not source_triple_ids:
            missing_source_triples.append(edge_id)
            continue
        for triple_id in source_triple_ids:
            triple = triple_by_id.get(triple_id)
            component_spans = as_list((triple or {}).get("component_evidence_spans"))
            if not triple or not component_spans:
                missing_component_span_triples.append({"edge_id": edge_id, "triple_id": triple_id})
                continue
            expected_link_count += len(component_spans)
            expected_edges_with_links.add(edge_id)
            expected_linked_triples.add(triple_id)

    def add_issue(error, **payload):
        if len(issues) < 120:
            row = {"error": error}
            row.update(payload)
            issues.append(row)

    expected_claim_status = "edge_component_span_traceability_ready_not_human_gold_span_claim"
    if summary.get("claim_status") != expected_claim_status:
        add_issue("unexpected_claim_status", expected=expected_claim_status, actual=summary.get("claim_status"))
    if summary.get("source_text_included") is not False:
        add_issue("source_text_included_not_false", actual=summary.get("source_text_included"))
    if len(links) != len(links_csv):
        add_issue("jsonl_csv_row_count_mismatch", jsonl=len(links), csv=len(links_csv))
    if len(links) != expected_link_count:
        add_issue("link_count_mismatch", expected=expected_link_count, actual=len(links))

    expected_counts = {
        "final_layer2_edge_count": len(edges),
        "component_span_triple_count": len(triples),
        "edges_with_source_triple_ids": len(edge_ids_with_source_triples),
        "edges_with_component_span_links": len(expected_edges_with_links),
        "edge_component_span_link_count": expected_link_count,
        "linked_source_triple_count": len(expected_linked_triples),
        "missing_edge_source_triple_count": len(missing_source_triples),
        "missing_component_span_triple_count": len(missing_component_span_triples),
    }
    for key, expected in expected_counts.items():
        if summary.get(key) != expected:
            add_issue("summary_count_mismatch", field=key, expected=expected, actual=summary.get(key))

    link_ids = [row.get("edge_component_span_link_id") for row in links]
    if len(link_ids) != len(set(link_ids)):
        add_issue("link_ids_not_unique", rows=len(link_ids), unique=len(set(link_ids)))

    component_counts = Counter()
    span_method_counts = Counter()
    exact_component_count = 0
    chunk_span_count = 0
    for row in links:
        edge_id = row.get("edge_id")
        triple_id = row.get("triple_id")
        component = row.get("component")
        edge = edge_by_id.get(edge_id) or {}
        if edge_id not in edge_by_id:
            add_issue("link_unknown_edge_id", edge_id=edge_id)
        if triple_id not in triple_by_id:
            add_issue("link_unknown_triple_id", edge_id=edge_id, triple_id=triple_id)
        if component not in {"subject", "predicate", "object"}:
            add_issue("link_unknown_component", link_id=row.get("edge_component_span_link_id"), component=component)
        if edge and row.get("predicate") != edge.get("predicate"):
            add_issue("link_predicate_mismatch", edge_id=edge_id, expected=edge.get("predicate"), actual=row.get("predicate"))
        if row.get("text_included") is not False:
            add_issue("link_text_included_not_false", link_id=row.get("edge_component_span_link_id"), actual=row.get("text_included"))
        if "text" in row or "source_text" in row:
            add_issue("link_contains_source_text_field", link_id=row.get("edge_component_span_link_id"))
        if not row.get("text_sha256") and int(row.get("text_char_count") or 0) > 0:
            add_issue("nonempty_text_missing_hash", link_id=row.get("edge_component_span_link_id"))
        component_counts[component] += 1
        span_method_counts[f"{component}.{row.get('span_method') or ''}"] += 1
        if row.get("span_exact") is True:
            exact_component_count += 1
        if row.get("chunk_span_start") not in (None, ""):
            chunk_span_count += 1

    csv_fieldnames = links_csv[0].keys() if links_csv else []
    forbidden_csv_fields = {"text", "source_text", "evidence_text"}
    if forbidden_csv_fields.intersection(csv_fieldnames):
        add_issue("csv_contains_source_text_field", fields=sorted(forbidden_csv_fields.intersection(csv_fieldnames)))

    if summary.get("component_count_by_role") != dict(sorted(component_counts.items())):
        add_issue("component_count_by_role_mismatch", expected=dict(sorted(component_counts.items())), actual=summary.get("component_count_by_role"))
    if summary.get("span_method_counts") != dict(sorted(span_method_counts.items())):
        add_issue("span_method_counts_mismatch", expected=dict(sorted(span_method_counts.items())), actual=summary.get("span_method_counts"))
    if summary.get("exact_component_span_count") != exact_component_count:
        add_issue("exact_component_span_count_mismatch", expected=exact_component_count, actual=summary.get("exact_component_span_count"))
    if summary.get("chunk_span_count") != chunk_span_count:
        add_issue("chunk_span_count_mismatch", expected=chunk_span_count, actual=summary.get("chunk_span_count"))
    if summary.get("missing_edge_source_triple_count") != 0:
        add_issue("missing_edge_source_triples_present", count=summary.get("missing_edge_source_triple_count"))
    if summary.get("missing_component_span_triple_count") != 0:
        add_issue("missing_component_span_triples_present", count=summary.get("missing_component_span_triple_count"))

    lower_report = report_text.lower()
    for pattern in [
        "not a human-gold span-quality result",
        "source text is omitted",
        "predicate rows remain sentence-level proxy support",
    ]:
        if pattern not in lower_report:
            add_issue("report_missing_pattern", pattern=pattern)

    limitations = " ".join(str(item) for item in summary.get("limitations") or [])
    for pattern in [
        "lexical diagnostics",
        "full-sentence proxy",
        "No source text is included",
        "adjudicated human-gold span scoring",
    ]:
        if pattern not in limitations:
            add_issue("summary_missing_limitation", pattern=pattern)

    if issues:
        add_check(
            checks,
            "edge_component_span_traceability",
            "FAIL",
            "Edge-to-component span traceability is missing, inconsistent, or overclaims span quality.",
            {"issues": issues},
        )
        return

    add_check(
        checks,
        "edge_component_span_traceability",
        "PASS",
        "Final KG edges trace to source triples and automatic component spans without including source text.",
        {
            "final_layer2_edge_count": len(edges),
            "edge_component_span_link_count": len(links),
            "edges_with_component_span_links": len(expected_edges_with_links),
            "linked_source_triple_count": len(expected_linked_triples),
            "source_text_included": False,
            "claim_status": summary.get("claim_status"),
        },
    )


def validate_active_review_diagnostics_safety(checks, exp_dir):
    eval_dir = exp_dir / "04_evaluation"
    review_dir = exp_dir / "05_review"
    release_dir = exp_dir / "06_release"
    efficiency_json = eval_dir / "active_review_efficiency_metrics.json"
    efficiency_report = eval_dir / "active_review_efficiency_report.md"
    ablation_json = eval_dir / "active_review_ablation_metrics.json"
    ablation_report = eval_dir / "active_review_ablation_report.md"
    effort_json = eval_dir / "active_review_human_effort_metrics.json"
    effort_report = eval_dir / "active_review_human_effort_report.md"
    effort_template = review_dir / "active_review_human_effort_template.csv"
    effort_plan = release_dir / "active_review_human_effort_plan.json"
    effort_briefing_json = release_dir / "active_review_human_effort_briefing.json"
    effort_briefing_md = release_dir / "active_review_human_effort_briefing.md"
    effort_briefing_csv = review_dir / "active_review_human_effort_briefing.csv"
    issues = []

    def to_int(value, default=-1):
        try:
            return int(float(value))
        except Exception:
            return default

    try:
        efficiency = read_json(efficiency_json)
    except Exception as exc:
        efficiency = {}
        issues.append({"error": "cannot_read_efficiency_metrics", "path": rel(efficiency_json), "detail": str(exc)})
    if efficiency:
        if efficiency.get("claim_status") != "silver_proxy_not_human_review_efficiency":
            issues.append({"error": "unexpected_efficiency_claim_status", "actual": efficiency.get("claim_status")})
        if int(efficiency.get("candidate_count") or 0) <= 0:
            issues.append({"error": "efficiency_candidate_count_not_positive", "actual": efficiency.get("candidate_count")})
        strategies = {row.get("strategy") for row in as_list(efficiency.get("metrics")) if isinstance(row, dict)}
        if not {"active_priority", "uncertainty_only"}.issubset(strategies):
            issues.append({"error": "missing_efficiency_strategies", "actual": sorted(strategies)})
    if not efficiency_report.exists():
        issues.append({"error": "missing_efficiency_report", "path": rel(efficiency_report)})
    else:
        text = efficiency_report.read_text(encoding="utf-8", errors="replace")
        for pattern in ["silver/proxy diagnostic", "does not claim human review efficiency", "human reviewer timing"]:
            if pattern not in text:
                issues.append({"error": "missing_efficiency_report_pattern", "pattern": pattern})

    try:
        ablation = read_json(ablation_json)
    except Exception as exc:
        ablation = {}
        issues.append({"error": "cannot_read_ablation_metrics", "path": rel(ablation_json), "detail": str(exc)})
    if ablation:
        if ablation.get("claim_status") != "silver_proxy_ablation_not_human_efficiency":
            issues.append({"error": "unexpected_ablation_claim_status", "actual": ablation.get("claim_status")})
        conditions = set(as_list(ablation.get("conditions")))
        expected_conditions = {
            "P_cape_kg_actual_with_active_review",
            "P_minus_Active_review_random_expected",
            "P_minus_Active_review_uncertainty_only",
        }
        if not expected_conditions.issubset(conditions):
            issues.append({"error": "missing_active_review_ablation_conditions", "actual": sorted(conditions)})
        if int(ablation.get("row_count") or 0) <= 0:
            issues.append({"error": "ablation_row_count_not_positive", "actual": ablation.get("row_count")})
    if not ablation_report.exists():
        issues.append({"error": "missing_ablation_report", "path": rel(ablation_report)})
    else:
        text = ablation_report.read_text(encoding="utf-8", errors="replace")
        for pattern in ["P - Active review", "silver/proxy diagnostic only", "Do not report these values as final human-review efficiency"]:
            if pattern not in text:
                issues.append({"error": "missing_ablation_report_pattern", "pattern": pattern})

    try:
        effort = read_json(effort_json)
    except Exception as exc:
        effort = {}
        issues.append({"error": "cannot_read_human_effort_metrics", "path": rel(effort_json), "detail": str(exc)})
    if effort:
        allowed_status = {"ready_for_human_effort_collection", "human_effort_evaluated"}
        if effort.get("claim_status") not in allowed_status:
            issues.append({"error": "unexpected_human_effort_claim_status", "actual": effort.get("claim_status")})
        if not effort.get("reviewed_file_present") and effort.get("claim_status") != "ready_for_human_effort_collection":
            issues.append({"error": "missing_reviewed_file_should_be_collection_ready", "actual": effort.get("claim_status")})
        metrics = [row for row in as_list(effort.get("metrics")) if isinstance(row, dict)]
        arms = {row.get("arm") for row in metrics}
        if not {"active_priority", "uncertainty_only", "random_control"}.issubset(arms):
            issues.append({"error": "missing_human_effort_arms", "actual": sorted(arms)})
        if not effort.get("reviewed_file_present"):
            non_pending = [row for row in metrics if row.get("claim_status") != "pending_human_effort_timing"]
            if non_pending:
                issues.append({"error": "pre_human_effort_rows_should_be_pending", "rows": non_pending[:5]})
    for path, label in [(effort_report, "human_effort_report"), (effort_template, "human_effort_template"), (effort_plan, "human_effort_plan")]:
        if not path.exists():
            issues.append({"error": f"missing_{label}", "path": rel(path)})
    if effort_report.exists():
        text = effort_report.read_text(encoding="utf-8", errors="replace")
        for pattern in ["Claim status: `ready_for_human_effort_collection`", "pending_human_effort_timing", "active_review_human_effort.reviewed.csv"]:
            if pattern not in text:
                issues.append({"error": "missing_human_effort_report_pattern", "pattern": pattern})

    try:
        briefing = read_json(effort_briefing_json)
    except Exception as exc:
        briefing = {}
        issues.append({"error": "cannot_read_human_effort_briefing_json", "path": rel(effort_briefing_json), "detail": str(exc)})
    try:
        briefing_rows = read_csv_rows(effort_briefing_csv)
    except Exception as exc:
        briefing_rows = []
        issues.append({"error": "cannot_read_human_effort_briefing_csv", "path": rel(effort_briefing_csv), "detail": str(exc)})
    if briefing:
        if briefing.get("claim_status") != "review_navigation_only_pending_human_effort":
            issues.append({"error": "human_effort_briefing_claim_status_unexpected", "actual": briefing.get("claim_status")})
        if to_int(briefing.get("pooled_rows")) != 204:
            issues.append({"error": "human_effort_briefing_pooled_rows_unexpected", "actual": briefing.get("pooled_rows")})
        if to_int(briefing.get("briefing_rows")) != 204:
            issues.append({"error": "human_effort_briefing_rows_unexpected", "actual": briefing.get("briefing_rows")})
    if briefing_rows and len(briefing_rows) != 204:
        issues.append({"error": "human_effort_briefing_csv_row_count_unexpected", "actual": len(briefing_rows)})
    if not effort_briefing_md.exists():
        issues.append({"error": "missing_human_effort_briefing_md", "path": rel(effort_briefing_md)})
    else:
        briefing_text = effort_briefing_md.read_text(encoding="utf-8", errors="replace")
        for pattern in [
            "Active Review Human-Effort Briefing",
            "review_navigation_only_pending_human_effort",
            "active_review_human_effort.reviewed.csv",
            "Paper-level active-review claims still require",
        ]:
            if pattern not in briefing_text:
                issues.append({"error": "missing_human_effort_briefing_pattern", "pattern": pattern})

    if issues:
        add_check(
            checks,
            "active_review_diagnostics_claim_safety",
            "FAIL",
            "Active-review diagnostic or human-effort artifacts are missing conservative claim-safety context.",
            {"issues": issues[:50]},
        )
        return
    add_check(
        checks,
        "active_review_diagnostics_claim_safety",
        "PASS",
        "Active-review ablation and human-effort artifacts are explicitly scoped as silver/proxy or pending human timing.",
        {
            "efficiency_metrics": rel(efficiency_json),
            "ablation_metrics": rel(ablation_json),
            "human_effort_metrics": rel(effort_json),
            "human_effort_template": rel(effort_template),
            "human_effort_briefing": rel(effort_briefing_md),
            "human_effort_briefing_rows": len(briefing_rows),
        },
    )


def validate_mapping_downstream_claim_safety(checks, exp_dir, outputs_dir):
    eval_dir = exp_dir / "04_evaluation"
    review_dir = exp_dir / "05_review"
    release_dir = exp_dir / "06_release"
    downstream_report = eval_dir / "mapping_downstream_report.md"
    downstream_results = eval_dir / "mapping_downstream_results.csv"
    arm_diagnostics = eval_dir / "mapping_downstream_arm_diagnostics.csv"
    arm_details = eval_dir / "mapping_downstream_arm_rerank_details.csv"
    arm_summary_path = eval_dir / "mapping_downstream_arm_rerank_summary.json"
    expert_metrics_path = eval_dir / "mapping_expert_metrics.json"
    expert_report = eval_dir / "mapping_expert_evaluation_report.md"
    progress_summary_path = release_dir / "mapping_review_progress_summary.json"
    progress_report = release_dir / "mapping_review_progress_report.md"
    crosswalk_summary_path = eval_dir / "ncs_pcf_crosswalk_summary.json"
    crosswalk_report = eval_dir / "ncs_pcf_crosswalk_report.md"
    crosswalk_review_manifest_path = exp_dir / "01_data/crosswalk_review/crosswalk_review_manifest.json"
    crosswalk_review_items = exp_dir / "01_data/crosswalk_review/crosswalk_review_items.jsonl"
    crosswalk_review_sheet = exp_dir / "01_data/crosswalk_review/crosswalk_review_sheet.csv"
    crosswalk_review_protocol = exp_dir / "01_data/crosswalk_review/crosswalk_review_protocol.md"
    crosswalk_expert_metrics_path = eval_dir / "crosswalk_expert_metrics.json"
    crosswalk_expert_report = eval_dir / "crosswalk_expert_evaluation_report.md"
    crosswalk_candidates = outputs_dir / "08_mapping/l2_ncs_pcf_crosswalk_candidates.jsonl"
    priority_queue = review_dir / "mapping_review_priority_queue.csv"
    next_groups = review_dir / "mapping_review_next_20_groups.csv"
    next_rows = review_dir / "mapping_review_next_60_rows.csv"
    group_briefing_json_path = release_dir / "mapping_review_group_briefing.json"
    group_briefing_md = release_dir / "mapping_review_group_briefing.md"
    group_briefing_csv = review_dir / "mapping_review_group_briefing_top20.csv"

    issues = []
    expected_standards = {"NCS", "PCF"}
    expected_arms = {
        "text_only_task_description",
        "task_frame_only",
        "flat_triples",
        "procedural_kg_with_evidence",
    }

    def to_int(value):
        try:
            return int(value)
        except Exception:
            return None

    if not downstream_report.exists():
        issues.append({"error": "missing_mapping_downstream_report", "path": rel(downstream_report)})
    else:
        text = downstream_report.read_text(encoding="utf-8", errors="replace")
        for pattern in [
            "Expert-confirmed Hit@K/P@5/MRR remain pending",
            "not a paper-claimable mapping result",
            "generated_top5_only",
            "It does not replace expert review",
            "P@K, P@5, MRR, and accept-rate remain pending",
        ]:
            if pattern not in text:
                issues.append({"error": "missing_downstream_report_claim_safety_pattern", "pattern": pattern})

    try:
        result_rows = read_csv_rows(downstream_results)
    except Exception as exc:
        result_rows = []
        issues.append({"error": "cannot_read_mapping_downstream_results", "path": rel(downstream_results), "detail": str(exc)})
    if result_rows:
        standards = {row.get("standard") for row in result_rows}
        if standards != expected_standards:
            issues.append({"error": "downstream_result_standards_mismatch", "actual": sorted(standards)})
        for row in result_rows:
            if row.get("expert_accept_rate") != "pending_human_review":
                issues.append({"error": "downstream_accept_rate_not_pending", "row": row})
            if row.get("p_at_5") != "pending_human_review" or row.get("mrr") != "pending_human_review":
                issues.append({"error": "downstream_metrics_not_pending_human_review", "row": row})
            if to_int(row.get("selected_domain_tasks")) != 22 or to_int(row.get("covered_tasks")) != 22:
                issues.append({"error": "downstream_task_coverage_unexpected", "row": row})
            if to_int(row.get("top5_candidate_rows")) != 110:
                issues.append({"error": "downstream_top5_rows_unexpected", "row": row})

    try:
        diagnostic_rows = read_csv_rows(arm_diagnostics)
    except Exception as exc:
        diagnostic_rows = []
        issues.append({"error": "cannot_read_mapping_arm_diagnostics", "path": rel(arm_diagnostics), "detail": str(exc)})
    if diagnostic_rows:
        diagnostics_standards = {row.get("standard") for row in diagnostic_rows}
        diagnostics_arms = {row.get("representation_arm") for row in diagnostic_rows}
        if diagnostics_standards != expected_standards:
            issues.append({"error": "arm_diagnostic_standards_mismatch", "actual": sorted(diagnostics_standards)})
        if diagnostics_arms != expected_arms:
            issues.append({"error": "arm_diagnostic_arms_mismatch", "actual": sorted(diagnostics_arms)})
        if len(diagnostic_rows) != len(expected_standards) * len(expected_arms):
            issues.append({"error": "arm_diagnostic_row_count_unexpected", "actual": len(diagnostic_rows)})
        for row in diagnostic_rows:
            if row.get("claim_status") != "diagnostic_rerank_only_not_expert_reviewed":
                issues.append({"error": "arm_diagnostic_claim_status_unexpected", "row": row})
            if row.get("candidate_universe") != "generated_top5_only":
                issues.append({"error": "arm_diagnostic_candidate_universe_unexpected", "row": row})
            if row.get("hit_at_5") != "pending_expert_review" or row.get("precision_at_5") != "pending_expert_review" or row.get("mrr") != "pending_expert_review":
                issues.append({"error": "arm_diagnostic_metrics_not_pending", "row": row})
            if to_int(row.get("source_task_groups")) != 22 or to_int(row.get("candidate_rows")) != 110:
                issues.append({"error": "arm_diagnostic_coverage_unexpected", "row": row})

    try:
        detail_rows = read_csv_rows(arm_details)
    except Exception as exc:
        detail_rows = []
        issues.append({"error": "cannot_read_mapping_arm_details", "path": rel(arm_details), "detail": str(exc)})

    try:
        arm_summary = read_json(arm_summary_path)
    except Exception as exc:
        arm_summary = {}
        issues.append({"error": "cannot_read_mapping_arm_summary", "path": rel(arm_summary_path), "detail": str(exc)})
    if arm_summary:
        if arm_summary.get("claim_status") != "diagnostic_rerank_only_not_expert_reviewed":
            issues.append({"error": "arm_summary_claim_status_unexpected", "actual": arm_summary.get("claim_status")})
        if arm_summary.get("candidate_universe") != "generated_top5_only":
            issues.append({"error": "arm_summary_candidate_universe_unexpected", "actual": arm_summary.get("candidate_universe")})
        if set(as_list(arm_summary.get("representation_arms"))) != expected_arms:
            issues.append({"error": "arm_summary_arms_mismatch", "actual": sorted(as_list(arm_summary.get("representation_arms")))})
        if set(as_list(arm_summary.get("standards"))) != expected_standards:
            issues.append({"error": "arm_summary_standards_mismatch", "actual": sorted(as_list(arm_summary.get("standards")))})
        if to_int(arm_summary.get("source_task_groups")) != 44:
            issues.append({"error": "arm_summary_source_task_groups_unexpected", "actual": arm_summary.get("source_task_groups")})
        if detail_rows and to_int(arm_summary.get("detail_rows")) != len(detail_rows):
            issues.append({"error": "arm_summary_detail_rows_mismatch", "summary": arm_summary.get("detail_rows"), "csv_rows": len(detail_rows)})

    try:
        expert_metrics = read_json(expert_metrics_path)
    except Exception as exc:
        expert_metrics = {}
        issues.append({"error": "cannot_read_mapping_expert_metrics", "path": rel(expert_metrics_path), "detail": str(exc)})
    if expert_metrics:
        if expert_metrics.get("claim_status") != "pending_or_partial_expert_review":
            issues.append({"error": "expert_metrics_claim_status_unexpected", "actual": expert_metrics.get("claim_status")})
        metric_rows = [row for row in as_list(expert_metrics.get("metrics")) if isinstance(row, dict)]
        if {row.get("standard") for row in metric_rows} != expected_standards:
            issues.append({"error": "expert_metric_standards_mismatch", "actual": sorted(row.get("standard") for row in metric_rows)})
        pending_fields = [
            "expert_accept_rate",
            "hit_at_1",
            "hit_at_3",
            "hit_at_5",
            "precision_at_5",
            "mrr",
            "ndcg_at_10",
            "explanation_quality_score_mean",
        ]
        for row in metric_rows:
            if row.get("claim_status") != "pending_expert_review":
                issues.append({"error": "expert_metric_row_claim_status_unexpected", "row": row})
            if to_int(row.get("candidate_rows")) != 110 or to_int(row.get("source_task_count")) != 22:
                issues.append({"error": "expert_metric_candidate_coverage_unexpected", "row": row})
            if to_int(row.get("completed_rows")) != 0 or to_int(row.get("complete_source_groups")) != 0:
                issues.append({"error": "expert_metric_should_have_no_completed_rows_pre_human", "row": row})
            if to_int(row.get("pending_rows")) != 110:
                issues.append({"error": "expert_metric_pending_rows_unexpected", "row": row})
            for field in pending_fields:
                if row.get(field) != "pending_expert_review":
                    issues.append({"error": "expert_metric_field_not_pending", "field": field, "row": row})
    if not expert_report.exists():
        issues.append({"error": "missing_mapping_expert_report", "path": rel(expert_report)})
    else:
        text = expert_report.read_text(encoding="utf-8", errors="replace")
        for pattern in ["Rows are claimable only for source task groups", "pending_expert_review"]:
            if pattern not in text:
                issues.append({"error": "missing_expert_report_pattern", "pattern": pattern})

    try:
        progress_summary = read_json(progress_summary_path)
    except Exception as exc:
        progress_summary = {}
        issues.append({"error": "cannot_read_mapping_progress_summary", "path": rel(progress_summary_path), "detail": str(exc)})
    if progress_summary:
        expected_progress = {
            "candidate_rows": 220,
            "source_task_standard_groups": 44,
            "complete_source_groups": 0,
            "pending_source_groups": 44,
            "completed_rows": 0,
            "pending_rows": 220,
        }
        for field, expected in expected_progress.items():
            if to_int(progress_summary.get(field)) != expected:
                issues.append({"error": "mapping_progress_field_unexpected", "field": field, "expected": expected, "actual": progress_summary.get(field)})
        for row in as_list(progress_summary.get("by_standard")):
            if not isinstance(row, dict):
                continue
            if to_int(row.get("candidate_rows")) != 110 or to_int(row.get("pending_rows")) != 110:
                issues.append({"error": "mapping_progress_standard_rows_unexpected", "row": row})
            if to_int(row.get("complete_source_groups")) != 0 or to_int(row.get("pending_source_groups")) != 22:
                issues.append({"error": "mapping_progress_standard_group_status_unexpected", "row": row})
    if not progress_report.exists():
        issues.append({"error": "missing_mapping_progress_report", "path": rel(progress_report)})
    else:
        text = progress_report.read_text(encoding="utf-8", errors="replace")
        for pattern in ["does not turn mapping candidates into gold labels", "evaluable only when every Top-5 candidate"]:
            if pattern not in text:
                issues.append({"error": "missing_progress_report_pattern", "pattern": pattern})

    try:
        group_briefing = read_json(group_briefing_json_path)
    except Exception as exc:
        group_briefing = {}
        issues.append({"error": "cannot_read_mapping_group_briefing_json", "path": rel(group_briefing_json_path), "detail": str(exc)})
    try:
        group_briefing_rows = read_csv_rows(group_briefing_csv)
    except Exception as exc:
        group_briefing_rows = []
        issues.append({"error": "cannot_read_mapping_group_briefing_csv", "path": rel(group_briefing_csv), "detail": str(exc)})
    if group_briefing:
        if group_briefing.get("claim_status") != "candidate_only_pending_expert_review":
            issues.append({"error": "mapping_group_briefing_claim_status_unexpected", "actual": group_briefing.get("claim_status")})
        if to_int(group_briefing.get("group_count")) != 20:
            issues.append({"error": "mapping_group_briefing_group_count_unexpected", "actual": group_briefing.get("group_count")})
        if to_int(group_briefing.get("candidate_rows")) != 100:
            issues.append({"error": "mapping_group_briefing_candidate_rows_unexpected", "actual": group_briefing.get("candidate_rows")})
    if group_briefing_rows and len(group_briefing_rows) != 100:
        issues.append({"error": "mapping_group_briefing_csv_row_count_unexpected", "actual": len(group_briefing_rows)})
    if not group_briefing_md.exists():
        issues.append({"error": "missing_mapping_group_briefing_md", "path": rel(group_briefing_md)})
    else:
        briefing_text = group_briefing_md.read_text(encoding="utf-8", errors="replace")
        for pattern in [
            "Mapping Review Group Briefing",
            "Candidate rows remain non-claimable",
            "Finish all Top-5 rows",
            "candidate_only_pending_expert_review",
        ]:
            if pattern not in briefing_text:
                issues.append({"error": "missing_mapping_group_briefing_pattern", "pattern": pattern})

    try:
        crosswalk_summary = read_json(crosswalk_summary_path)
    except Exception as exc:
        crosswalk_summary = {}
        issues.append({"error": "cannot_read_crosswalk_summary", "path": rel(crosswalk_summary_path), "detail": str(exc)})
    if crosswalk_summary:
        if crosswalk_summary.get("claim_status") != "candidate_only_pending_expert_review":
            issues.append({"error": "crosswalk_claim_status_unexpected", "actual": crosswalk_summary.get("claim_status")})
        if to_int(crosswalk_summary.get("candidate_count")) != 220 or to_int(crosswalk_summary.get("shared_source_tasks")) != 22:
            issues.append({"error": "crosswalk_counts_unexpected", "summary": crosswalk_summary})
    if not crosswalk_report.exists():
        issues.append({"error": "missing_crosswalk_report", "path": rel(crosswalk_report)})
    else:
        text = crosswalk_report.read_text(encoding="utf-8", errors="replace")
        for pattern in ["not expert-confirmed crosswalk labels", "candidate_only_pending_expert_review", "Expert review is still required"]:
            if pattern not in text:
                issues.append({"error": "missing_crosswalk_report_pattern", "pattern": pattern})

    try:
        crosswalk_rows = read_jsonl(crosswalk_candidates)
    except Exception as exc:
        crosswalk_rows = []
        issues.append({"error": "cannot_read_crosswalk_candidates", "path": rel(crosswalk_candidates), "detail": str(exc)})
    if crosswalk_summary and crosswalk_rows and len(crosswalk_rows) != to_int(crosswalk_summary.get("candidate_count")):
        issues.append({"error": "crosswalk_candidate_count_mismatch", "summary": crosswalk_summary.get("candidate_count"), "jsonl_rows": len(crosswalk_rows)})

    try:
        crosswalk_review_manifest = read_json(crosswalk_review_manifest_path)
    except Exception as exc:
        crosswalk_review_manifest = {}
        issues.append({"error": "cannot_read_crosswalk_review_manifest", "path": rel(crosswalk_review_manifest_path), "detail": str(exc)})
    if crosswalk_review_manifest:
        if crosswalk_review_manifest.get("claim_status") != "pending_crosswalk_expert_review":
            issues.append(
                {
                    "error": "crosswalk_review_manifest_claim_status_unexpected",
                    "actual": crosswalk_review_manifest.get("claim_status"),
                }
            )
        if to_int(crosswalk_review_manifest.get("candidate_rows")) != 220:
            issues.append({"error": "crosswalk_review_candidate_rows_unexpected", "actual": crosswalk_review_manifest.get("candidate_rows")})
        if to_int(crosswalk_review_manifest.get("source_task_count")) != 22:
            issues.append({"error": "crosswalk_review_source_tasks_unexpected", "actual": crosswalk_review_manifest.get("source_task_count")})
    try:
        crosswalk_review_rows = read_jsonl(crosswalk_review_items)
    except Exception as exc:
        crosswalk_review_rows = []
        issues.append({"error": "cannot_read_crosswalk_review_items", "path": rel(crosswalk_review_items), "detail": str(exc)})
    if len(crosswalk_review_rows) != 220:
        issues.append({"error": "crosswalk_review_items_row_count_unexpected", "actual": len(crosswalk_review_rows)})
    for path, pattern in [
        (crosswalk_review_sheet, "crosswalk_id"),
        (crosswalk_review_protocol, "CAPE-KG NCS-PCF Crosswalk Expert Review Protocol"),
    ]:
        if not path.exists():
            issues.append({"error": "missing_crosswalk_review_file", "path": rel(path)})
        else:
            text = path.read_text(encoding="utf-8", errors="replace")
            if pattern not in text:
                issues.append({"error": "crosswalk_review_file_missing_pattern", "path": rel(path), "pattern": pattern})
    try:
        crosswalk_expert_metrics = read_json(crosswalk_expert_metrics_path)
    except Exception as exc:
        crosswalk_expert_metrics = {}
        issues.append({"error": "cannot_read_crosswalk_expert_metrics", "path": rel(crosswalk_expert_metrics_path), "detail": str(exc)})
    if crosswalk_expert_metrics:
        if crosswalk_expert_metrics.get("claim_status") != "pending_crosswalk_expert_review":
            issues.append({"error": "crosswalk_expert_metrics_claim_status_unexpected", "actual": crosswalk_expert_metrics.get("claim_status")})
        metrics = crosswalk_expert_metrics.get("metrics") or {}
        expected_pending = [
            "expert_accept_rate",
            "hit_at_1",
            "hit_at_3",
            "hit_at_5",
            "precision_at_10",
            "mrr",
            "ndcg_at_10",
            "utility_grade_mean",
            "explanation_quality_score_mean",
        ]
        if to_int(metrics.get("candidate_rows")) != 220 or to_int(metrics.get("source_task_count")) != 22:
            issues.append({"error": "crosswalk_expert_metrics_coverage_unexpected", "metrics": metrics})
        if to_int(metrics.get("completed_rows")) != 0 or to_int(metrics.get("complete_source_groups")) != 0:
            issues.append({"error": "crosswalk_expert_metrics_should_have_no_completed_rows_pre_human", "metrics": metrics})
        if to_int(metrics.get("pending_rows")) != 220:
            issues.append({"error": "crosswalk_expert_metrics_pending_rows_unexpected", "metrics": metrics})
        for field in expected_pending:
            if metrics.get(field) != "pending_crosswalk_expert_review":
                issues.append({"error": "crosswalk_expert_metric_field_not_pending", "field": field, "metrics": metrics})
    if not crosswalk_expert_report.exists():
        issues.append({"error": "missing_crosswalk_expert_report", "path": rel(crosswalk_expert_report)})
    else:
        text = crosswalk_expert_report.read_text(encoding="utf-8", errors="replace")
        for pattern in ["pending_crosswalk_expert_review", "not gold NCS-PCF crosswalk labels"]:
            if pattern not in text:
                issues.append({"error": "missing_crosswalk_expert_report_pattern", "pattern": pattern})

    for path, expected_rows, label in [
        (priority_queue, 44, "priority_queue"),
        (next_groups, 20, "next_20_groups"),
        (next_rows, 60, "next_60_rows"),
        (group_briefing_csv, 100, "mapping_group_briefing_top20"),
    ]:
        try:
            rows = read_csv_rows(path)
        except Exception as exc:
            issues.append({"error": f"cannot_read_{label}", "path": rel(path), "detail": str(exc)})
            continue
        if len(rows) != expected_rows:
            issues.append({"error": f"{label}_row_count_unexpected", "expected": expected_rows, "actual": len(rows)})

    if issues:
        add_check(
            checks,
            "mapping_downstream_claim_safety",
            "FAIL",
            "Mapping downstream/expert-review artifacts are missing conservative candidate-only claim-safety context.",
            {"issues": issues[:80]},
        )
        return
    add_check(
        checks,
        "mapping_downstream_claim_safety",
        "PASS",
        "Mapping downstream, expert-review, and NCS-PCF crosswalk artifacts are candidate-only or pending expert review.",
        {
            "downstream_report": rel(downstream_report),
            "expert_metrics": rel(expert_metrics_path),
            "progress_summary": rel(progress_summary_path),
            "group_briefing": rel(group_briefing_md),
            "group_briefing_rows": len(group_briefing_rows),
            "crosswalk_summary": rel(crosswalk_summary_path),
            "crosswalk_candidates": rel(crosswalk_candidates),
            "crosswalk_review_manifest": rel(crosswalk_review_manifest_path),
            "crosswalk_expert_metrics": rel(crosswalk_expert_metrics_path),
            "review_queue_groups": 44,
            "pending_candidate_rows": 220,
        },
    )


def validate_llm_diagnostics_public_benchmark_safety(checks, exp_dir):
    eval_dir = exp_dir / "04_evaluation"
    release_dir = exp_dir / "06_release"
    public_dir = exp_dir / "08_public_benchmarks"
    actual_metrics_path = eval_dir / "actual_llm_silver_metrics.json"
    actual_report = eval_dir / "actual_llm_silver_evaluation_report.md"
    scaling_metric_sets = [
        (
            "qwen3_14b_core",
            eval_dir / "qwen3_14b_core_silver_metrics.json",
            eval_dir / "qwen3_14b_core_silver_metrics.csv",
            eval_dir / "qwen3_14b_core_silver_evaluation_report.md",
        ),
        (
            "qwen3_32b_awq_core",
            eval_dir / "qwen3_32b_awq_core_silver_metrics.json",
            eval_dir / "qwen3_32b_awq_core_silver_metrics.csv",
            eval_dir / "qwen3_32b_awq_core_silver_evaluation_report.md",
        ),
    ]
    statistical_json = eval_dir / "statistical_analysis_metrics.json"
    statistical_report = eval_dir / "statistical_analysis_report.md"
    statistical_bootstrap = eval_dir / "statistical_analysis_bootstrap.csv"
    statistical_mcnemar = eval_dir / "statistical_analysis_mcnemar.csv"
    statistical_chunk_scores = eval_dir / "statistical_analysis_chunk_scores.csv"
    public_crosscheck_json = public_dir / "public_benchmark_crosscheck_summary.json"
    public_crosscheck_report = public_dir / "public_benchmark_crosscheck_report.md"
    public_adapter_report = public_dir / "public_benchmark_adapter_report.md"
    qwen32_readiness_json = release_dir / "qwen3_32b_awq_readiness.json"
    qwen32_readiness_report = release_dir / "qwen3_32b_awq_readiness.md"
    qwen_scaling_json = release_dir / "qwen3_model_scaling_report.json"
    qwen_scaling_report = release_dir / "qwen3_model_scaling_report.md"
    strict_json = release_dir / "strict_json_diagnostics.json"
    strict_json_report = release_dir / "strict_json_diagnostics.md"
    issues = []

    expected_actual_conditions = TRACEABILITY_EXPECTED_CONDITIONS
    expected_core_scaling_conditions = {"B0_plain_llm", "B1_predicate_constrained", "B2_current_project", "P_cape_kg_actual"}
    expected_stat_comparisons = {
        "B0_plain_llm",
        "B1_predicate_constrained",
        "B2_current_project",
        "B3_edc_style",
        "B4_taxonomy_rag",
        "B5_procedural_prompt",
        "P_minus_CQ",
        "P_minus_Evidence",
        "P_minus_Procedural_schema",
        "P_minus_Schema_retrieval",
        "P_minus_Standard_bridge",
        "P_minus_Validator",
    }

    def to_int(value):
        try:
            return int(value)
        except Exception:
            return None

    def check_silver_metrics(path, expected_conditions, expected_rows, label):
        try:
            payload = read_json(path)
        except Exception as exc:
            issues.append({"error": f"cannot_read_{label}_metrics", "path": rel(path), "detail": str(exc)})
            return []
        if payload.get("claim_status") != "silver_proxy_not_human_gold":
            issues.append({"error": f"{label}_claim_status_unexpected", "actual": payload.get("claim_status")})
        if payload.get("reference") != "silver_reference_edges_by_chunk":
            issues.append({"error": f"{label}_reference_unexpected", "actual": payload.get("reference")})
        metric_rows = [row for row in as_list(payload.get("metrics")) if isinstance(row, dict)]
        conditions = {row.get("condition") for row in metric_rows}
        missing_conditions = sorted(expected_conditions - conditions)
        if missing_conditions:
            issues.append({"error": f"{label}_missing_conditions", "missing": missing_conditions, "actual": sorted(conditions)})
        for row in metric_rows:
            if row.get("claim_status") != "silver_proxy_not_human_gold":
                issues.append({"error": f"{label}_row_claim_status_unexpected", "row": row})
            if expected_rows is not None and to_int(row.get("rows")) != expected_rows:
                issues.append({"error": f"{label}_row_count_unexpected", "expected": expected_rows, "row": row})
        return metric_rows

    actual_rows = check_silver_metrics(actual_metrics_path, expected_actual_conditions, 120, "actual_llm_silver")
    if len(actual_rows) < len(expected_actual_conditions):
        issues.append({"error": "actual_llm_silver_metric_row_count_too_small", "actual": len(actual_rows)})
    if not actual_report.exists():
        issues.append({"error": "missing_actual_llm_silver_report", "path": rel(actual_report)})
    else:
        text = actual_report.read_text(encoding="utf-8", errors="replace")
        for pattern in ["silver reference", "not a substitute for human-gold evaluation", "partial_json_repaired_rows"]:
            if pattern not in text:
                issues.append({"error": "missing_actual_llm_silver_report_pattern", "pattern": pattern})

    for label, json_path, csv_path, report_path in scaling_metric_sets:
        metric_rows = check_silver_metrics(json_path, expected_core_scaling_conditions, 120, label)
        if len(metric_rows) < len(expected_core_scaling_conditions):
            issues.append({"error": f"{label}_metric_row_count_too_small", "actual": len(metric_rows)})
        if not csv_path.exists():
            issues.append({"error": f"missing_{label}_csv", "path": rel(csv_path)})
        if not report_path.exists():
            issues.append({"error": f"missing_{label}_report", "path": rel(report_path)})
        else:
            text = report_path.read_text(encoding="utf-8", errors="replace")
            for pattern in ["silver reference", "not a substitute for human-gold evaluation"]:
                if pattern not in text:
                    issues.append({"error": f"missing_{label}_report_pattern", "pattern": pattern})

    try:
        statistical = read_json(statistical_json)
    except Exception as exc:
        statistical = {}
        issues.append({"error": "cannot_read_statistical_analysis", "path": rel(statistical_json), "detail": str(exc)})
    statistical_bootstrap_rows = []
    statistical_mcnemar_rows = []
    if statistical:
        if statistical.get("claim_status") != "silver_proxy_not_human_gold":
            issues.append({"error": "statistical_claim_status_unexpected", "actual": statistical.get("claim_status")})
        if statistical.get("proposed_condition") != "P_cape_kg_actual":
            issues.append({"error": "statistical_proposed_condition_unexpected", "actual": statistical.get("proposed_condition")})
        if to_int(statistical.get("chunk_count")) != 120:
            issues.append({"error": "statistical_chunk_count_unexpected", "actual": statistical.get("chunk_count")})
        if to_int(statistical.get("bootstrap_iterations")) < 1000:
            issues.append({"error": "statistical_bootstrap_iterations_too_small", "actual": statistical.get("bootstrap_iterations")})
        comparisons = set(as_list(statistical.get("comparison_conditions")))
        missing_comparisons = sorted(expected_stat_comparisons - comparisons)
        if missing_comparisons:
            issues.append({"error": "statistical_missing_comparison_conditions", "missing": missing_comparisons})
        for key in ["bootstrap_rows", "mcnemar_rows"]:
            rows = [row for row in as_list(statistical.get(key)) if isinstance(row, dict)]
            if not rows:
                issues.append({"error": f"statistical_{key}_empty"})
            bad_rows = [row for row in rows if row.get("claim_status") != "silver_proxy_not_human_gold"]
            if bad_rows:
                issues.append({"error": f"statistical_{key}_claim_status_unexpected", "rows": bad_rows[:5]})
            if key == "bootstrap_rows":
                statistical_bootstrap_rows = rows
            if key == "mcnemar_rows":
                statistical_mcnemar_rows = rows
        bootstrap_metrics = {row.get("metric") for row in statistical_bootstrap_rows if row.get("metric")}
        if bootstrap_metrics and len(statistical_bootstrap_rows) != len(expected_stat_comparisons) * len(bootstrap_metrics):
            issues.append(
                {
                    "error": "statistical_bootstrap_row_count_unexpected",
                    "expected": len(expected_stat_comparisons) * len(bootstrap_metrics),
                    "actual": len(statistical_bootstrap_rows),
                    "metrics": sorted(bootstrap_metrics),
                }
            )
        mcnemar_metrics = {row.get("metric") for row in statistical_mcnemar_rows if row.get("metric")}
        if mcnemar_metrics and len(statistical_mcnemar_rows) != len(expected_stat_comparisons) * len(mcnemar_metrics):
            issues.append(
                {
                    "error": "statistical_mcnemar_row_count_unexpected",
                    "expected": len(expected_stat_comparisons) * len(mcnemar_metrics),
                    "actual": len(statistical_mcnemar_rows),
                    "metrics": sorted(mcnemar_metrics),
                }
            )
        for label, rows in [("bootstrap", statistical_bootstrap_rows), ("mcnemar", statistical_mcnemar_rows)]:
            pairs = {(row.get("baseline_condition"), row.get("metric")) for row in rows}
            missing_pairs = sorted(
                (condition, metric)
                for condition in expected_stat_comparisons
                for metric in ({row.get("metric") for row in rows if row.get("metric")} or set())
                if (condition, metric) not in pairs
            )
            if missing_pairs:
                issues.append({"error": f"statistical_{label}_missing_condition_metric_pairs", "missing": missing_pairs[:20]})
    statistical_csv_rows = {}
    for csv_path, label in [
        (statistical_bootstrap, "statistical_bootstrap"),
        (statistical_mcnemar, "statistical_mcnemar"),
        (statistical_chunk_scores, "statistical_chunk_scores"),
    ]:
        try:
            rows = read_csv_rows(csv_path)
        except Exception as exc:
            rows = []
            issues.append({"error": f"cannot_read_{label}_csv", "path": rel(csv_path), "detail": str(exc)})
        statistical_csv_rows[label] = rows
        bad_rows = [row for row in rows if row.get("claim_status") != "silver_proxy_not_human_gold"]
        if bad_rows:
            issues.append({"error": f"{label}_claim_status_unexpected", "rows": bad_rows[:5]})
    if statistical:
        if len(statistical_csv_rows.get("statistical_bootstrap", [])) != len(statistical_bootstrap_rows):
            issues.append(
                {
                    "error": "statistical_bootstrap_csv_json_row_count_mismatch",
                    "json_rows": len(statistical_bootstrap_rows),
                    "csv_rows": len(statistical_csv_rows.get("statistical_bootstrap", [])),
                }
            )
        if len(statistical_csv_rows.get("statistical_mcnemar", [])) != len(statistical_mcnemar_rows):
            issues.append(
                {
                    "error": "statistical_mcnemar_csv_json_row_count_mismatch",
                    "json_rows": len(statistical_mcnemar_rows),
                    "csv_rows": len(statistical_csv_rows.get("statistical_mcnemar", [])),
                }
            )
        stat_conditions = set(as_list(statistical.get("conditions")))
        chunk_count = to_int(statistical.get("chunk_count"))
        chunk_score_rows = statistical_csv_rows.get("statistical_chunk_scores", [])
        if stat_conditions and chunk_count is not None:
            expected_chunk_score_rows = len(stat_conditions) * chunk_count
            if len(chunk_score_rows) != expected_chunk_score_rows:
                issues.append(
                    {
                        "error": "statistical_chunk_score_row_count_unexpected",
                        "expected": expected_chunk_score_rows,
                        "actual": len(chunk_score_rows),
                        "conditions": sorted(stat_conditions),
                        "chunk_count": chunk_count,
                    }
                )
            chunk_score_conditions = {row.get("condition") for row in chunk_score_rows}
            if chunk_score_conditions != stat_conditions:
                issues.append(
                    {
                        "error": "statistical_chunk_score_condition_set_mismatch",
                        "expected": sorted(stat_conditions),
                        "actual": sorted(chunk_score_conditions),
                    }
                )
            bad_condition_counts = []
            for condition in sorted(stat_conditions):
                count = sum(1 for row in chunk_score_rows if row.get("condition") == condition)
                if count != chunk_count:
                    bad_condition_counts.append({"condition": condition, "expected": chunk_count, "actual": count})
            if bad_condition_counts:
                issues.append({"error": "statistical_chunk_score_condition_counts_unexpected", "rows": bad_condition_counts[:20]})
    if not statistical_report.exists():
        issues.append({"error": "missing_statistical_report", "path": rel(statistical_report)})
    else:
        text = statistical_report.read_text(encoding="utf-8", errors="replace")
        for pattern in ["current silver reference only", "not final paper evidence", "adjudicated human-gold labels"]:
            if pattern not in text:
                issues.append({"error": "missing_statistical_report_pattern", "pattern": pattern})

    try:
        crosscheck = read_json(public_crosscheck_json)
    except Exception as exc:
        crosscheck = {}
        issues.append({"error": "cannot_read_public_benchmark_crosscheck", "path": rel(public_crosscheck_json), "detail": str(exc)})
    if crosscheck:
        summary = crosscheck.get("summary") or {}
        if summary.get("claim_status") != "public_adapter_model_runs_diagnostic_not_official_leaderboard":
            issues.append({"error": "public_crosscheck_claim_status_unexpected", "actual": summary.get("claim_status")})
        if not summary.get("strong_cross_run_present"):
            issues.append({"error": "public_crosscheck_strong_run_missing"})
        if to_int(summary.get("run_count")) < 3:
            issues.append({"error": "public_crosscheck_run_count_too_small", "actual": summary.get("run_count")})
        if to_int(summary.get("max_single_run_paged_items")) < 100 or to_int(summary.get("max_single_run_text2kg_items")) < 200:
            issues.append({"error": "public_crosscheck_item_coverage_too_small", "summary": summary})
        runs = [run for run in as_list(crosscheck.get("runs")) if isinstance(run, dict)]
        run_ids = {run.get("run_id") for run in runs}
        expected_public_runs = {
            "public_qwen3_8b_full_adapter_eval",
            "public_qwen3_8b_subset_eval",
            "public_qwen3_14b_subset_eval",
        }
        missing_runs = sorted(expected_public_runs - run_ids)
        if missing_runs:
            issues.append({"error": "public_crosscheck_missing_runs", "missing": missing_runs, "actual": sorted(run_ids)})
    if not public_crosscheck_report.exists():
        issues.append({"error": "missing_public_crosscheck_report", "path": rel(public_crosscheck_report)})
    else:
        text = public_crosscheck_report.read_text(encoding="utf-8", errors="replace")
        for pattern in [
            "not official benchmark leaderboard claims",
            "external diagnostic coverage only",
            "requires adjudicated human-gold scoring",
        ]:
            if pattern not in text:
                issues.append({"error": "missing_public_crosscheck_report_pattern", "pattern": pattern})
    if not public_adapter_report.exists():
        issues.append({"error": "missing_public_adapter_report", "path": rel(public_adapter_report)})
    else:
        text = public_adapter_report.read_text(encoding="utf-8", errors="replace")
        if "auxiliary diagnostics" not in text:
            issues.append({"error": "missing_public_adapter_auxiliary_scope"})

    try:
        qwen32 = read_json(qwen32_readiness_json)
    except Exception as exc:
        qwen32 = {}
        issues.append({"error": "cannot_read_qwen32_readiness", "path": rel(qwen32_readiness_json), "detail": str(exc)})
    if qwen32:
        core = qwen32.get("qwen3_32b_awq_core_run") or {}
        if qwen32.get("claim_status") != "model_readiness_only_not_a_paper_result":
            issues.append({"error": "qwen32_readiness_claim_status_unexpected", "actual": qwen32.get("claim_status")})
        if qwen32.get("status") != "core_run_complete" or not core.get("complete"):
            issues.append({"error": "qwen32_core_run_not_complete", "status": qwen32.get("status"), "core": core})
        if to_int(core.get("raw_rows")) != 480 or to_int(core.get("valid_rows")) != 480 or to_int(core.get("expected_rows")) != 480:
            issues.append({"error": "qwen32_core_row_counts_unexpected", "core": core})
    if not qwen32_readiness_report.exists():
        issues.append({"error": "missing_qwen32_readiness_report", "path": rel(qwen32_readiness_report)})
    else:
        text = qwen32_readiness_report.read_text(encoding="utf-8", errors="replace")
        if "use human-gold scoring before paper claims" not in text:
            issues.append({"error": "missing_qwen32_human_gold_claim_safety_text"})

    try:
        qwen_scaling = read_json(qwen_scaling_json)
    except Exception as exc:
        qwen_scaling = {}
        issues.append({"error": "cannot_read_qwen_model_scaling_report", "path": rel(qwen_scaling_json), "detail": str(exc)})
    if qwen_scaling:
        summary = qwen_scaling.get("summary") or {}
        model_rows = [row for row in as_list(qwen_scaling.get("model_rows")) if isinstance(row, dict)]
        condition_rows = [row for row in as_list(qwen_scaling.get("condition_rows")) if isinstance(row, dict)]
        models = {row.get("model") for row in model_rows}
        expected_models = {"Qwen3-8B", "Qwen3-14B", "Qwen3-32B-AWQ"}
        if summary.get("claim_status") != "qwen3_model_scaling_diagnostic_ready_not_human_gold":
            issues.append({"error": "qwen_model_scaling_claim_status_unexpected", "actual": summary.get("claim_status")})
        missing_models = sorted(expected_models - models)
        if missing_models:
            issues.append({"error": "qwen_model_scaling_missing_models", "missing": missing_models, "actual": sorted(models)})
        if to_int(summary.get("missing_required_source_count")) != 0:
            issues.append({"error": "qwen_model_scaling_missing_required_sources", "summary": summary})
        if not summary.get("qwen3_32b_awq_core_run_complete"):
            issues.append({"error": "qwen_model_scaling_32b_core_not_complete", "summary": summary})
        if (
            to_int(summary.get("qwen3_32b_awq_raw_rows")) != 480
            or to_int(summary.get("qwen3_32b_awq_valid_rows")) != 480
            or to_int(summary.get("qwen3_32b_awq_expected_rows")) != 480
        ):
            issues.append({"error": "qwen_model_scaling_32b_row_counts_unexpected", "summary": summary})
        for row in model_rows:
            if row.get("claim_status") != "silver_proxy_not_human_gold":
                issues.append({"error": "qwen_model_scaling_row_claim_status_unexpected", "row": row})
            if to_int(row.get("proposed_rows")) != 120:
                issues.append({"error": "qwen_model_scaling_proposed_rows_unexpected", "row": row})
        expected_model_condition_pairs = {(model, condition) for model in expected_models for condition in expected_core_scaling_conditions}
        actual_model_condition_pairs = {(row.get("model"), row.get("condition")) for row in condition_rows}
        missing_pairs = sorted(expected_model_condition_pairs - actual_model_condition_pairs)
        if missing_pairs:
            issues.append({"error": "qwen_model_scaling_missing_model_condition_pairs", "missing": missing_pairs})
    if not qwen_scaling_report.exists():
        issues.append({"error": "missing_qwen_model_scaling_report", "path": rel(qwen_scaling_report)})
    else:
        text = qwen_scaling_report.read_text(encoding="utf-8", errors="replace")
        for pattern in [
            "must not be presented as final human-gold performance",
            "do not overclaim monotonic model scaling",
            "not another automatic GPU run",
        ]:
            if pattern not in text:
                issues.append({"error": "missing_qwen_model_scaling_report_pattern", "pattern": pattern})

    try:
        strict = read_json(strict_json)
    except Exception as exc:
        strict = {}
        issues.append({"error": "cannot_read_strict_json_diagnostics", "path": rel(strict_json), "detail": str(exc)})
    if strict:
        if strict.get("strict_json_gate_status") != "PASS" or strict.get("revalidated_output_recovery_status") != "PASS":
            issues.append({"error": "strict_json_gate_not_pass", "summary": strict})
        if to_int(strict.get("conditions_with_full_runs")) != len(TRACEABILITY_EXPECTED_CONDITIONS):
            issues.append({"error": "strict_json_full_run_condition_count_unexpected", "actual": strict.get("conditions_with_full_runs")})
        if to_int(strict.get("conditions_over_strict_json_warning_threshold")) != 0 or to_int(strict.get("conditions_over_unrepaired_error_threshold")) != 0:
            issues.append({"error": "strict_json_conditions_over_threshold", "summary": strict})
        contract_prompt = Path(strict.get("strict_json_contract_prompt_file") or "")
        if not contract_prompt.exists():
            issues.append({"error": "strict_json_contract_prompt_missing", "path": rel(contract_prompt)})
    if not strict_json_report.exists():
        issues.append({"error": "missing_strict_json_report", "path": rel(strict_json_report)})
    else:
        text = strict_json_report.read_text(encoding="utf-8", errors="replace")
        if "Existing generated outputs and metrics are not modified by this diagnostic" not in text:
            issues.append({"error": "missing_strict_json_non_mutating_scope_text"})

    if issues:
        add_check(
            checks,
            "llm_diagnostics_public_benchmark_claim_safety",
            "FAIL",
            "LLM silver diagnostics, statistical tests, model scaling, or public benchmark artifacts are missing conservative claim-safety context.",
            {"issues": issues[:100]},
        )
        return
    add_check(
        checks,
        "llm_diagnostics_public_benchmark_claim_safety",
        "PASS",
        "LLM diagnostics, statistical tests, model scaling, strict-JSON diagnostics, and public benchmark cross-checks are scoped as silver/proxy or auxiliary diagnostics.",
        {
            "actual_llm_silver_metrics": rel(actual_metrics_path),
            "statistical_analysis": rel(statistical_json),
            "public_benchmark_crosscheck": rel(public_crosscheck_json),
            "qwen3_32b_awq_readiness": rel(qwen32_readiness_json),
            "qwen3_model_scaling_report": rel(qwen_scaling_json),
            "strict_json_diagnostics": rel(strict_json),
            "claim_status": "silver_proxy_or_auxiliary_diagnostic_not_human_gold",
        },
    )


def validate_handoff_manifest(checks, exp_dir):
    manifest_path = exp_dir / "06_release/human_review_handoff/human_review_handoff_manifest.json"
    try:
        manifest = read_json(manifest_path)
    except Exception as exc:
        add_check(checks, "handoff_manifest_readable", "FAIL", "Human review handoff manifest cannot be read.", {"error": str(exc)})
        return

    expected_status = "handoff_ready_pending_human_review"
    if manifest.get("claim_status") != expected_status:
        add_check(
            checks,
            "handoff_claim_status",
            "FAIL",
            "Human review handoff status is not the expected pending state.",
            {"actual": manifest.get("claim_status"), "expected": expected_status},
        )
    else:
        add_check(
            checks,
            "handoff_claim_status",
            "PASS",
            "Human review handoff status is ready for review.",
            {"claim_status": manifest.get("claim_status")},
        )

    assigned_chunks = int(manifest.get("assigned_chunks") or 0)
    batch_count = int(manifest.get("batch_count") or 0)
    if assigned_chunks >= 100 and batch_count >= 5:
        add_check(
            checks,
            "handoff_batch_coverage",
            "PASS",
            "Handoff covers the minimum priority-100 human review set.",
            {"assigned_chunks": assigned_chunks, "batch_count": batch_count},
        )
    else:
        add_check(
            checks,
            "handoff_batch_coverage",
            "FAIL",
            "Handoff does not cover the minimum priority-100 human review set.",
            {"assigned_chunks": assigned_chunks, "batch_count": batch_count},
        )

    annotator_issues = []
    for annotator in ("A", "B"):
        item = (manifest.get("annotators") or {}).get(annotator) or {}
        ok = (
            int(item.get("rows") or 0) >= 100
            and int(item.get("unique_chunks") or 0) >= 100
            and int(item.get("duplicate_chunk_count") or 0) == 0
            and bool(item.get("ready_for_minimum_gate")) is True
        )
        if not ok:
            annotator_issues.append({"annotator": annotator, "manifest": item})
    if annotator_issues:
        add_check(checks, "handoff_annotator_manifests", "FAIL", "Annotator handoff manifests are incomplete.", {"issues": annotator_issues})
    else:
        add_check(checks, "handoff_annotator_manifests", "PASS", "Annotator A/B manifests each cover 100 unique chunks.", {})

    bundles = manifest.get("bundles") or {}
    missing_bundles = sorted(REQUIRED_HANDOFF_BUNDLES - set(bundles))
    bundle_issues = []
    for name, bundle in bundles.items():
        path = Path(bundle.get("path", ""))
        if not path.exists():
            bundle_issues.append({"bundle": name, "error": "missing_file", "path": rel(path)})
            continue
        actual = sha256_file(path)
        if actual != bundle.get("sha256"):
            bundle_issues.append({"bundle": name, "error": "sha256_mismatch", "expected": bundle.get("sha256"), "actual": actual})
        if int(bundle.get("file_count") or 0) <= 0:
            bundle_issues.append({"bundle": name, "error": "empty_or_unreported_file_count"})
    if missing_bundles:
        bundle_issues.append({"error": "missing_bundle_entries", "bundles": missing_bundles})
    if bundle_issues:
        add_check(checks, "handoff_bundle_manifest_hashes", "FAIL", "Handoff bundle manifest entries are inconsistent.", {"issues": bundle_issues})
    else:
        add_check(checks, "handoff_bundle_manifest_hashes", "PASS", "Handoff bundle files match manifest hashes.", {"bundles": sorted(bundles)})


def validate_handoff_bundle_contents(checks, exp_dir):
    manifest_path = exp_dir / "06_release/human_review_handoff/human_review_handoff_manifest.json"
    try:
        manifest = read_json(manifest_path)
    except Exception as exc:
        add_check(checks, "handoff_bundle_contents", "FAIL", "Human review handoff manifest cannot be read for bundle content validation.", {"error": str(exc)})
        return

    required_by_bundle = {
        "annotator_A": [
            "README_annotator_A_ko.md",
            "annotation_workbench.html",
            "annotation_guideline_v1.md",
            "human_review_claim_gate_one_page_ko.md",
            "human_review_master_return_files.csv",
            "human_review_first_batch_execution_card_ko.md",
            "human_review_role_quickstart_cards_ko.md",
            "human_review_role_quickstart_cards.json",
            "human_review_role_quickstart_cards.csv",
            "human_review_launch_checklist_ko.md",
            "human_review_minimum_gate_launch_tasks.csv",
            "build_cape_human_review_first_batch_card.py",
            "build_cape_human_review_role_quickstart.py",
            "build_cape_human_review_launch_checklist.py",
            "annotator_A_priority100_manifest.json",
            "full_120_priority_batch_001/annotator_A_full_120_priority_batch_001.jsonl",
            "full_120_priority_batch_005/annotator_A_full_120_priority_batch_005.jsonl",
            "validate_cape_human_review_returns.py",
            "run_cape_human_return_apply.sh",
        ],
        "annotator_B": [
            "README_annotator_B_ko.md",
            "annotation_workbench.html",
            "annotation_guideline_v1.md",
            "human_review_claim_gate_one_page_ko.md",
            "human_review_master_return_files.csv",
            "human_review_first_batch_execution_card_ko.md",
            "human_review_role_quickstart_cards_ko.md",
            "human_review_role_quickstart_cards.json",
            "human_review_role_quickstart_cards.csv",
            "human_review_launch_checklist_ko.md",
            "human_review_minimum_gate_launch_tasks.csv",
            "build_cape_human_review_first_batch_card.py",
            "build_cape_human_review_role_quickstart.py",
            "build_cape_human_review_launch_checklist.py",
            "annotator_B_priority100_manifest.json",
            "full_120_priority_batch_001/annotator_B_full_120_priority_batch_001.jsonl",
            "full_120_priority_batch_005/annotator_B_full_120_priority_batch_005.jsonl",
            "validate_cape_human_review_returns.py",
            "run_cape_human_return_apply.sh",
        ],
        "coordinator": [
            "README_coordinator_ko.md",
            "annotation_workbench.html",
            "annotation_guideline_v1.md",
            "human_review_claim_gate_one_page_ko.md",
            "human_review_master_return_files.csv",
            "human_review_first_batch_execution_card_ko.md",
            "human_review_role_quickstart_cards_ko.md",
            "human_review_role_quickstart_cards.json",
            "human_review_role_quickstart_cards.csv",
            "human_review_launch_checklist_ko.md",
            "human_review_minimum_gate_launch_tasks.csv",
            "build_cape_human_review_first_batch_card.py",
            "build_cape_human_review_role_quickstart.py",
            "build_cape_human_review_launch_checklist.py",
            "annotator_A_priority100_manifest.json",
            "annotator_B_priority100_manifest.json",
            "full_120_priority_batch_001/annotator_A_full_120_priority_batch_001.jsonl",
            "full_120_priority_batch_001/annotator_B_full_120_priority_batch_001.jsonl",
            "full_120_priority_batch_005/annotator_A_full_120_priority_batch_005.jsonl",
            "full_120_priority_batch_005/annotator_B_full_120_priority_batch_005.jsonl",
            "validate_cape_human_review_returns.py",
            "run_cape_human_return_apply.sh",
        ],
        "adjudicator": [
            "README_adjudicator_ko.md",
            "annotation_guideline_v1.md",
            "adjudication_protocol.md",
            "adjudication_draft.jsonl",
            "adjudication_draft_summary.json",
            "human_review_claim_gate_one_page_ko.md",
            "human_review_master_return_files.csv",
            "human_review_role_quickstart_cards_ko.md",
            "human_review_role_quickstart_cards.json",
            "human_review_role_quickstart_cards.csv",
            "human_review_launch_checklist_ko.md",
            "human_review_minimum_gate_launch_tasks.csv",
            "build_cape_human_review_role_quickstart.py",
            "build_cape_human_review_launch_checklist.py",
            "import_cape_gold_annotation.py",
            "validate_cape_human_review_returns.py",
            "run_cape_human_return_apply.sh",
        ],
        "mapping_expert": [
            "README_mapping_expert_ko.md",
            "mapping_review_workbench.html",
            "mapping_review_protocol.md",
            "mapping_review_items.jsonl",
            "mapping_review_sheet.csv",
            "mapping_review_group_briefing.md",
            "mapping_review_group_briefing_top20.csv",
            "mapping_review_next_20_groups.csv",
            "mapping_review_next_60_rows.csv",
            "human_review_claim_gate_one_page_ko.md",
            "human_review_master_return_files.csv",
            "human_review_role_quickstart_cards_ko.md",
            "human_review_role_quickstart_cards.json",
            "human_review_role_quickstart_cards.csv",
            "human_review_launch_checklist_ko.md",
            "human_review_minimum_gate_launch_tasks.csv",
            "build_cape_human_review_role_quickstart.py",
            "build_cape_human_review_launch_checklist.py",
            "import_cape_mapping_review.py",
            "evaluate_cape_mapping_review.py",
            "run_cape_human_return_apply.sh",
        ],
        "crosswalk_expert": [
            "README_crosswalk_expert_ko.md",
            "crosswalk_review_protocol.md",
            "crosswalk_review_items.jsonl",
            "crosswalk_review_sheet.csv",
            "crosswalk_review_manifest.json",
            "ncs_pcf_crosswalk_report.md",
            "ncs_pcf_crosswalk_candidates.csv",
            "crosswalk_expert_evaluation_report.md",
            "human_review_claim_gate_one_page_ko.md",
            "human_review_master_return_files.csv",
            "human_review_role_quickstart_cards_ko.md",
            "human_review_role_quickstart_cards.json",
            "human_review_role_quickstart_cards.csv",
            "human_review_launch_checklist_ko.md",
            "human_review_minimum_gate_launch_tasks.csv",
            "build_cape_human_review_role_quickstart.py",
            "prepare_cape_crosswalk_review_package.py",
            "import_cape_crosswalk_review.py",
            "evaluate_cape_crosswalk_review.py",
            "run_cape_human_return_apply.sh",
        ],
        "active_review_effort": [
            "README_active_review_effort_ko.md",
            "active_review_human_effort_briefing.md",
            "active_review_human_effort_briefing.csv",
            "active_review_human_effort_template.csv",
            "actual_llm_active_review_queue_P_cape_kg_actual.csv",
            "active_review_efficiency_report.md",
            "active_review_human_effort_report.md",
            "human_review_claim_gate_one_page_ko.md",
            "human_review_master_return_files.csv",
            "human_review_role_quickstart_cards_ko.md",
            "human_review_role_quickstart_cards.json",
            "human_review_role_quickstart_cards.csv",
            "human_review_launch_checklist_ko.md",
            "human_review_minimum_gate_launch_tasks.csv",
            "build_cape_human_review_role_quickstart.py",
            "build_cape_human_review_launch_checklist.py",
            "build_cape_active_review_human_effort.py",
            "validate_cape_human_review_returns.py",
            "run_cape_human_return_apply.sh",
        ],
        "structural_reviewer": [
            "README_structural_reviewer_ko.md",
            "structural_review_action_plan.md",
            "structural_review_return_preflight.md",
            "structural_review_checkpoint_candidates.csv",
            "structural_gateway_branch_gaps.csv",
            "structural_review_optional_returns.csv",
            "human_review_claim_gate_one_page_ko.md",
            "human_review_master_return_files.csv",
            "human_review_role_quickstart_cards_ko.md",
            "human_review_role_quickstart_cards.json",
            "human_review_role_quickstart_cards.csv",
            "human_review_launch_checklist_ko.md",
            "human_review_minimum_gate_launch_tasks.csv",
            "build_cape_human_review_role_quickstart.py",
            "build_cape_human_review_launch_checklist.py",
            "validate_cape_structural_review_returns.py",
            "run_cape_human_return_apply.sh",
        ],
        "strong_resegmented_review": [
            "README_strong_resegmented_review_ko.md",
            "annotation_expansion_manifest.json",
            "strong_resegmented_review_preview_summary.md",
            "strong_resegmented_342_max18/annotator_A.jsonl",
            "strong_resegmented_342_max18/annotator_B.jsonl",
            "strong_resegmented_342_max18/adjudication.jsonl",
            "strong_resegmented_342_max18/tracking_sheet.csv",
            "strong_resegmented_342_max18/strong_review_preview.md",
            "strong_resegmented_review_manifest.json",
            "human_review_claim_gate_one_page_ko.md",
            "human_review_role_quickstart_cards_ko.md",
            "human_review_role_quickstart_cards.json",
            "human_review_role_quickstart_cards.csv",
            "human_review_launch_checklist_ko.md",
            "human_review_minimum_gate_launch_tasks.csv",
            "build_cape_human_review_role_quickstart.py",
            "build_cape_human_review_launch_checklist.py",
            "validate_cape_strong_review_returns.py",
            "run_cape_strong_return_apply.sh",
            "run_cape_human_return_apply.sh",
        ],
    }

    bundles = manifest.get("bundles") or {}
    issues = []
    checked = {}
    for name, required_fragments in required_by_bundle.items():
        bundle = bundles.get(name)
        if not bundle:
            if name in REQUIRED_HANDOFF_BUNDLES:
                issues.append({"bundle": name, "error": "missing_manifest_entry"})
            continue
        path = Path(bundle.get("path", ""))
        if not path.exists():
            issues.append({"bundle": name, "error": "missing_tarball", "path": rel(path)})
            continue
        try:
            with tarfile.open(path, "r:gz") as tf:
                members = tf.getmembers()
                file_names = [member.name for member in members if member.isfile()]
        except Exception as exc:
            issues.append({"bundle": name, "error": "cannot_read_tarball", "path": rel(path), "detail": str(exc)})
            continue

        unsafe_names = []
        for file_name in file_names:
            parts = Path(file_name).parts
            if file_name.startswith("/") or ".." in parts:
                unsafe_names.append(file_name)
        if unsafe_names:
            issues.append({"bundle": name, "error": "unsafe_tar_paths", "paths": unsafe_names[:10]})

        expected_count = int(bundle.get("file_count") or 0)
        if expected_count != len(file_names):
            issues.append({"bundle": name, "error": "file_count_mismatch", "expected": expected_count, "actual": len(file_names)})

        missing_fragments = [
            fragment
            for fragment in required_fragments
            if not any(fragment in file_name for file_name in file_names)
        ]
        if missing_fragments:
            issues.append({"bundle": name, "error": "missing_required_files", "missing": missing_fragments})

        checked[name] = {"file_count": len(file_names), "required_fragments": len(required_fragments)}

    if issues:
        add_check(
            checks,
            "handoff_bundle_contents",
            "FAIL",
            "Human review handoff tarballs are missing required role-specific contents or have unsafe paths.",
            {"issues": issues[:50], "checked": checked},
        )
        return
    add_check(
        checks,
        "handoff_bundle_contents",
        "PASS",
        "Human review handoff tarballs contain the expected role-specific review inputs, guidance, and import/validation scripts.",
        {"checked": checked, "claim_status": "handoff_tarball_contents_ready_pending_human_review"},
    )


def candidate_edges_for_component_span_check(row):
    candidates = row.get("silver_candidate_edges")
    if isinstance(candidates, list):
        return candidates
    return []


def validate_component_span_handoff_coverage(checks, exp_dir):
    exp_dir = Path(exp_dir)
    expected_components = {"subject", "predicate", "object"}
    candidate_paths = [
        exp_dir / "01_data/gold_annotation_template.jsonl",
        exp_dir / "01_data/gold_annotation/full_120/annotator_A.jsonl",
        exp_dir / "01_data/gold_annotation/full_120/annotator_B.jsonl",
        exp_dir / "01_data/gold_annotation/pilot_30/annotator_A.jsonl",
        exp_dir / "01_data/gold_annotation/pilot_30/annotator_B.jsonl",
        exp_dir / "01_data/gold_annotation/strong_resegmented_342_max18/annotator_A.jsonl",
        exp_dir / "01_data/gold_annotation/strong_resegmented_342_max18/annotator_B.jsonl",
    ]
    batch_root = exp_dir / "05_review/human_gold_batches"
    candidate_paths.extend(sorted(batch_root.glob("full_120_priority_batch_*/annotator_*.jsonl")))

    issues = []
    summaries = []
    total_candidates = 0
    total_with_component_spans = 0
    total_exact_components = 0
    total_proxy_components = 0
    checked_files = 0
    for path in candidate_paths:
        if not path.exists():
            issues.append({"path": rel(path), "error": "missing_component_span_candidate_file"})
            continue
        checked_files += 1
        try:
            rows = read_jsonl(path)
        except Exception as exc:
            issues.append({"path": rel(path), "error": "cannot_read_jsonl", "detail": str(exc)})
            continue
        file_candidates = 0
        file_with_component_spans = 0
        file_rows_with_candidates = 0
        file_exact_components = 0
        file_proxy_components = 0
        for row in rows:
            candidates = candidate_edges_for_component_span_check(row)
            if candidates:
                file_rows_with_candidates += 1
            for index, candidate in enumerate(candidates):
                file_candidates += 1
                total_candidates += 1
                spans = candidate.get("component_evidence_spans")
                if not isinstance(spans, list):
                    issues.append(
                        {
                            "path": rel(path),
                            "line_no": row.get("_line_no"),
                            "chunk_id": row.get("chunk_id"),
                            "candidate_index": index,
                            "reference_id": candidate.get("reference_id"),
                            "error": "component_evidence_spans_missing_or_not_list",
                        }
                    )
                    continue
                components = {span.get("component") for span in spans if isinstance(span, dict)}
                missing_components = sorted(expected_components - components)
                if missing_components:
                    issues.append(
                        {
                            "path": rel(path),
                            "line_no": row.get("_line_no"),
                            "chunk_id": row.get("chunk_id"),
                            "candidate_index": index,
                            "reference_id": candidate.get("reference_id"),
                            "error": "component_evidence_spans_missing_components",
                            "missing_components": missing_components,
                        }
                    )
                    continue
                bad_claim_status = [
                    span.get("component")
                    for span in spans
                    if isinstance(span, dict) and span.get("claim_status") != "automatic_candidate_span_suggestion_not_gold"
                ]
                if bad_claim_status:
                    issues.append(
                        {
                            "path": rel(path),
                            "line_no": row.get("_line_no"),
                            "chunk_id": row.get("chunk_id"),
                            "candidate_index": index,
                            "reference_id": candidate.get("reference_id"),
                            "error": "component_span_claim_status_not_conservative",
                            "components": bad_claim_status,
                        }
                    )
                    continue
                file_with_component_spans += 1
                total_with_component_spans += 1
                for span in spans:
                    if not isinstance(span, dict):
                        continue
                    if span.get("span_exact"):
                        file_exact_components += 1
                        total_exact_components += 1
                    if span.get("span_method") == "full_sentence_proxy":
                        file_proxy_components += 1
                        total_proxy_components += 1
        summaries.append(
            {
                "path": rel(path),
                "rows": len(rows),
                "rows_with_candidates": file_rows_with_candidates,
                "candidate_edges": file_candidates,
                "candidate_edges_with_component_spans": file_with_component_spans,
                "exact_components": file_exact_components,
                "full_sentence_proxy_components": file_proxy_components,
            }
        )

    if total_candidates == 0:
        issues.append({"error": "no_candidate_edges_found_for_component_span_validation"})
    if issues:
        add_check(
            checks,
            "component_span_handoff_coverage",
            "FAIL",
            "Component-level evidence span suggestions are missing or inconsistent in human-review packages.",
            {
                "checked_files": checked_files,
                "candidate_edges": total_candidates,
                "candidate_edges_with_component_spans": total_with_component_spans,
                "issues": issues[:50],
                "file_summaries": summaries[:30],
            },
        )
        return
    add_check(
        checks,
        "component_span_handoff_coverage",
        "PASS",
        "Human-review candidate edges include conservative subject/predicate/object component span suggestions.",
        {
            "checked_files": checked_files,
            "candidate_edges": total_candidates,
            "candidate_edges_with_component_spans": total_with_component_spans,
            "exact_components": total_exact_components,
            "full_sentence_proxy_components": total_proxy_components,
            "file_summaries": summaries[:30],
            "claim_status": "automatic_candidate_span_suggestions_not_human_gold",
        },
    )


def validate_prompt_node_edge_traceability(checks, exp_dir, outputs_dir):
    exp_dir = Path(exp_dir)
    outputs_dir = Path(outputs_dir)
    json_path = exp_dir / "06_release/prompt_node_edge_traceability.json"
    md_path = exp_dir / "06_release/prompt_node_edge_traceability.md"
    prompt_dir = exp_dir / "02_schema/prompts"
    issues = []
    try:
        traceability = read_json(json_path)
    except Exception as exc:
        add_check(
            checks,
            "prompt_node_edge_traceability",
            "FAIL",
            "Prompt/CQ/node-edge traceability JSON cannot be read.",
            {"path": rel(json_path), "error": str(exc)},
        )
        return

    if traceability.get("claim_status") != "traceability_ready_not_human_gold_performance_evidence":
        issues.append({"error": "unexpected_claim_status", "claim_status": traceability.get("claim_status")})
    if not md_path.exists():
        issues.append({"error": "missing_markdown_report", "path": rel(md_path)})
    else:
        text = md_path.read_text(encoding="utf-8", errors="replace")
        for pattern in [
            "## Runtime Prompt 공통 제약",
            "## 프롬프트/조건별 산출물 매핑",
            "## Competency Question 생성 방식과 예시",
            "## 최종 KG Node 생성 방식",
            "## 최종 KG Edge 생성 방식",
            "human-gold annotation 이후에만 가능합니다",
        ]:
            if pattern not in text:
                issues.append({"error": "traceability_markdown_missing_pattern", "pattern": pattern})

    constraints = traceability.get("runtime_prompt_constraints") or []
    if len(constraints) < 5:
        issues.append({"error": "too_few_runtime_prompt_constraints", "count": len(constraints)})
    if not any("Return ONLY one valid JSON object" in item for item in constraints):
        issues.append({"error": "missing_json_only_runtime_constraint"})

    prompt_inventory = traceability.get("prompt_inventory") or []
    prompt_by_condition = {row.get("condition"): row for row in prompt_inventory}
    missing_conditions = sorted(TRACEABILITY_EXPECTED_CONDITIONS - set(prompt_by_condition))
    if missing_conditions:
        issues.append({"error": "missing_prompt_inventory_conditions", "conditions": missing_conditions})
    for condition in sorted(TRACEABILITY_EXPECTED_CONDITIONS):
        row = prompt_by_condition.get(condition) or {}
        prompt_file = row.get("prompt_file") or ""
        prompt_text = row.get("prompt_text") or ""
        expected_keys = row.get("expected_output_keys") or []
        if not expected_keys:
            issues.append({"condition": condition, "error": "missing_expected_output_keys"})
        if condition in TRACEABILITY_RUNTIME_ONLY_CONDITIONS:
            if prompt_file or row.get("prompt_file_exists"):
                issues.append({"condition": condition, "error": "runtime_only_condition_has_prompt_file", "prompt_file": prompt_file})
            continue
        if not prompt_file:
            issues.append({"condition": condition, "error": "missing_prompt_file"})
            continue
        prompt_path = Path(prompt_file)
        if not prompt_path.exists():
            issues.append({"condition": condition, "error": "prompt_file_missing_on_disk", "prompt_file": prompt_file})
            continue
        actual_prompt_text = prompt_path.read_text(encoding="utf-8").strip()
        if not prompt_text:
            issues.append({"condition": condition, "error": "prompt_text_missing_in_traceability"})
        elif actual_prompt_text != prompt_text:
            issues.append({"condition": condition, "error": "prompt_text_mismatch", "prompt_file": prompt_file})
        if prompt_dir.as_posix() not in prompt_path.as_posix():
            issues.append({"condition": condition, "error": "prompt_file_outside_prompt_dir", "prompt_file": prompt_file})

    cqs = ((traceability.get("competency_questions") or {}).get("experiment_cqs") or [])
    cq_ids = [row.get("cq_id") for row in cqs]
    if len(cqs) < 12:
        issues.append({"error": "too_few_experiment_cqs", "count": len(cqs)})
    if len(cq_ids) != len(set(cq_ids)):
        issues.append({"error": "duplicate_cq_ids", "cq_ids": cq_ids})
    for row in cqs:
        targets = row.get("target_predicates") or row.get("required_kg_elements") or []
        if not row.get("cq_id") or not row.get("question") or not targets:
            issues.append({"error": "cq_missing_required_fields", "cq_id": row.get("cq_id")})

    output_summary = traceability.get("llm_condition_outputs") or {}
    condition_rows = output_summary.get("conditions") or []
    output_by_condition = {row.get("condition"): row for row in condition_rows}
    missing_output_conditions = sorted(TRACEABILITY_EXPECTED_CONDITIONS - set(output_by_condition))
    if missing_output_conditions:
        issues.append({"error": "missing_llm_output_conditions", "conditions": missing_output_conditions})
    valid_files = output_summary.get("valid_files") or [output_summary.get("valid_file")]
    actual_total = 0
    for valid_file_value in valid_files:
        valid_file = Path(valid_file_value or "")
        if not valid_file.exists():
            issues.append({"error": "valid_output_file_missing", "path": rel(valid_file)})
            continue
        actual_total += len(read_jsonl(valid_file))
    if not issues and int(output_summary.get("total_rows") or 0) != actual_total:
        issues.append({"error": "valid_output_total_rows_mismatch", "traceability": output_summary.get("total_rows"), "actual": actual_total})
    for condition, row in output_by_condition.items():
        if condition in TRACEABILITY_EXPECTED_CONDITIONS and int(row.get("valid_rows") or 0) < 100:
            issues.append({"condition": condition, "error": "condition_valid_rows_below_100", "valid_rows": row.get("valid_rows")})

    kg = traceability.get("final_kg") or {}
    counts = kg.get("counts") or {}
    actual_nodes = read_jsonl(outputs_dir / "07_layer2_graph/layer2_nodes.jsonl")
    actual_edges = read_jsonl(outputs_dir / "07_layer2_graph/layer2_edges.jsonl")
    actual_triples = read_jsonl(outputs_dir / "06_triples/layer2_triples_schema_valid.jsonl")
    actual_node_ids = {row.get("node_id") for row in actual_nodes}
    actual_dangling = [
        row for row in actual_edges
        if row.get("source_id") not in actual_node_ids or row.get("target_id") not in actual_node_ids
    ]
    expected_actual_pairs = {
        "final_nodes": len(actual_nodes),
        "final_edges": len(actual_edges),
        "schema_valid_triples": len(actual_triples),
        "nodes_with_evidence": sum(1 for row in actual_nodes if row.get("evidence_anchor_ids")),
        "edges_with_evidence": sum(1 for row in actual_edges if row.get("evidence_anchor_ids")),
        "edges_with_source_triple_ids": sum(1 for row in actual_edges if row.get("source_triple_ids")),
        "dangling_edges": len(actual_dangling),
    }
    for key, actual in expected_actual_pairs.items():
        if int(counts.get(key) or 0) != actual:
            issues.append({"error": "final_kg_count_mismatch", "field": key, "traceability": counts.get(key), "actual": actual})
    if len(actual_nodes) <= 0 or len(actual_edges) <= 0:
        issues.append({"error": "final_kg_empty_or_missing", "nodes": len(actual_nodes), "edges": len(actual_edges)})
    if actual_dangling:
        issues.append({"error": "final_kg_has_dangling_edges", "dangling_count": len(actual_dangling)})

    if issues:
        add_check(
            checks,
            "prompt_node_edge_traceability",
            "FAIL",
            "Prompt/CQ/node-edge traceability is incomplete or stale.",
            {"path": rel(json_path), "markdown": rel(md_path), "issues": issues[:80]},
        )
        return
    add_check(
        checks,
        "prompt_node_edge_traceability",
        "PASS",
        "Prompt files, CQ definitions, LLM output summaries, and final KG node/edge counts are traceable and synchronized.",
        {
            "json": rel(json_path),
            "markdown": rel(md_path),
            "conditions": len(prompt_by_condition),
            "experiment_cqs": len(cqs),
            "valid_output_rows": output_summary.get("total_rows"),
            "valid_output_files": valid_files,
            "final_nodes": counts.get("final_nodes"),
            "final_edges": counts.get("final_edges"),
            "claim_status": traceability.get("claim_status"),
        },
    )


def validate_schema_retrieval_coverage_report(checks, exp_dir):
    exp_dir = Path(exp_dir)
    release_dir = exp_dir / "06_release"
    evaluation_dir = exp_dir / "04_evaluation"
    json_path = release_dir / "schema_retrieval_coverage_report.json"
    md_path = release_dir / "schema_retrieval_coverage_report.md"
    csv_path = evaluation_dir / "schema_retrieval_cq_support_by_condition.csv"
    expected_conditions = {"P_cape_kg_actual", "P_minus_Schema_retrieval", "B4_taxonomy_rag"}
    expected_status = "schema_retrieval_coverage_ready_silver_diagnostic_not_human_gold"
    issues = []

    try:
        payload = read_json(json_path)
        csv_rows = read_csv_rows(csv_path)
    except Exception as exc:
        add_check(
            checks,
            "schema_retrieval_coverage_report",
            "FAIL",
            "CQ-linked schema retrieval coverage artifacts cannot be read.",
            {"path": rel(json_path), "csv": rel(csv_path), "error": str(exc)},
        )
        return

    if payload.get("claim_status") != expected_status:
        issues.append({"error": "unexpected_claim_status", "actual": payload.get("claim_status")})

    boundary = payload.get("claim_boundary") or {}
    if boundary.get("silver_diagnostic_only") is not True:
        issues.append({"error": "claim_boundary_silver_diagnostic_only_missing"})
    if boundary.get("not_human_gold_performance_evidence") is not True:
        issues.append({"error": "claim_boundary_human_gold_distinction_missing"})
    boundary_text = " ".join(str(boundary.get(key) or "") for key in ["safe_interpretation", "not_claimable_until"])
    for pattern in ["human-gold", "IAA", "adjudicated"]:
        if pattern not in boundary_text:
            issues.append({"error": "claim_boundary_missing_pattern", "pattern": pattern})

    module = payload.get("method_module") or {}
    if module.get("module_id") != "M3":
        issues.append({"error": "method_module_not_m3", "actual": module.get("module_id")})

    schema = payload.get("schema_summary") or {}
    if int(schema.get("node_type_count") or 0) < 10:
        issues.append({"error": "too_few_schema_node_types", "actual": schema.get("node_type_count")})
    if int(schema.get("edge_type_count") or 0) < 10:
        issues.append({"error": "too_few_schema_edge_types", "actual": schema.get("edge_type_count")})
    if schema.get("evidence_span_required") is not True:
        issues.append({"error": "evidence_span_required_not_true"})

    cq = payload.get("competency_question_summary") or {}
    if int(cq.get("cq_count") or 0) != 12:
        issues.append({"error": "cq_count_mismatch", "actual": cq.get("cq_count")})
    if cq.get("all_cqs_have_target_predicates") is not True:
        issues.append({"error": "cq_target_predicates_missing"})

    policy_rows = payload.get("condition_prompt_policy") or []
    policy_by_condition = {row.get("condition"): row for row in policy_rows}
    if set(policy_by_condition) != expected_conditions:
        issues.append({"error": "condition_policy_set_mismatch", "actual": sorted(policy_by_condition)})
    proposed = policy_by_condition.get("P_cape_kg_actual") or {}
    minus_schema = policy_by_condition.get("P_minus_Schema_retrieval") or {}
    taxonomy = policy_by_condition.get("B4_taxonomy_rag") or {}
    if proposed.get("uses_cq_anchor") is not True or proposed.get("uses_chunk_specific_schema_retrieval") is not True:
        issues.append({"error": "proposed_schema_retrieval_policy_mismatch", "row": proposed})
    if minus_schema.get("uses_cq_anchor") is not True or minus_schema.get("uses_chunk_specific_schema_retrieval") is not False:
        issues.append({"error": "minus_schema_retrieval_policy_mismatch", "row": minus_schema})
    if minus_schema.get("uses_taxonomy_snippets") is not False or minus_schema.get("keeps_mapping_output_shape") is not True:
        issues.append({"error": "minus_schema_ablation_boundary_mismatch", "row": minus_schema})
    if taxonomy.get("uses_cq_anchor") is not False or taxonomy.get("uses_taxonomy_snippets") is not True:
        issues.append({"error": "taxonomy_baseline_policy_mismatch", "row": taxonomy})
    for condition, row in policy_by_condition.items():
        output_keys = set(row.get("expected_output_keys") or [])
        if condition in expected_conditions and not {"nodes", "edges", "mappings"}.issubset(output_keys):
            issues.append({"condition": condition, "error": "missing_nodes_edges_mappings_output_shape", "output_keys": sorted(output_keys)})

    output_rows = payload.get("condition_output_summary") or []
    output_by_condition = {row.get("condition"): row for row in output_rows}
    if set(output_by_condition) != expected_conditions:
        issues.append({"error": "condition_output_set_mismatch", "actual": sorted(output_by_condition)})
    for condition in expected_conditions:
        row = output_by_condition.get(condition) or {}
        if int(row.get("valid_rows") or 0) < 100:
            issues.append({"condition": condition, "error": "valid_rows_below_100", "actual": row.get("valid_rows")})
        if int(row.get("nodes") or 0) <= 0 or int(row.get("edges") or 0) <= 0:
            issues.append({"condition": condition, "error": "missing_node_or_edge_outputs", "row": row})

    metrics = payload.get("condition_silver_metrics") or []
    metric_by_condition = {row.get("condition"): row for row in metrics}
    if not {"P_cape_kg_actual", "P_minus_Schema_retrieval"}.issubset(metric_by_condition):
        issues.append({"error": "missing_core_silver_metric_rows", "actual": sorted(metric_by_condition)})
    for condition, row in metric_by_condition.items():
        if row.get("claim_status") != "silver_proxy_not_human_gold":
            issues.append({"condition": condition, "error": "silver_metric_claim_status_mismatch", "actual": row.get("claim_status")})

    cq_summary_rows = payload.get("cq_support_summary") or []
    cq_summary_by_condition = {row.get("condition"): row for row in cq_summary_rows}
    if set(cq_summary_by_condition) != expected_conditions:
        issues.append({"error": "cq_support_summary_set_mismatch", "actual": sorted(cq_summary_by_condition)})
    for condition, row in cq_summary_by_condition.items():
        if int(row.get("cq_count") or 0) != 12:
            issues.append({"condition": condition, "error": "cq_support_count_mismatch", "actual": row.get("cq_count")})
        if row.get("claim_status") != "cq_support_proxy_not_human_gold_answerability":
            issues.append({"condition": condition, "error": "cq_support_claim_status_mismatch", "actual": row.get("claim_status")})

    if len(csv_rows) != len(expected_conditions) * 12:
        issues.append({"error": "cq_support_csv_row_count_mismatch", "actual": len(csv_rows)})
    csv_conditions = {row.get("condition") for row in csv_rows}
    if csv_conditions != expected_conditions:
        issues.append({"error": "cq_support_csv_conditions_mismatch", "actual": sorted(csv_conditions)})
    for row in csv_rows:
        if row.get("claim_status") != "cq_support_proxy_not_human_gold_answerability":
            issues.append({"error": "cq_support_csv_claim_status_mismatch", "row": row})
            break

    deltas = payload.get("diagnostic_deltas") or {}
    for key in [
        "output_quantity_P_minus_schema_retrieval",
        "silver_metrics_P_minus_schema_retrieval",
        "cq_support_P_minus_schema_retrieval",
    ]:
        if not deltas.get(key):
            issues.append({"error": "missing_diagnostic_delta", "key": key})

    if not md_path.exists():
        issues.append({"error": "missing_markdown", "path": rel(md_path)})
    else:
        text = md_path.read_text(encoding="utf-8", errors="replace")
        for pattern in [
            "CAPE-KG CQ-Linked Schema Retrieval Coverage",
            "Silver diagnostic only",
            "Not human-gold performance evidence",
            "P_minus_Schema_retrieval",
            "CQ Support Proxy",
        ]:
            if pattern not in text:
                issues.append({"error": "schema_retrieval_markdown_missing_pattern", "pattern": pattern})

    if issues:
        add_check(
            checks,
            "schema_retrieval_coverage_report",
            "FAIL",
            "CQ-linked schema retrieval coverage report is missing, stale, or claim-unsafe.",
            {"path": rel(json_path), "markdown": rel(md_path), "csv": rel(csv_path), "issues": issues[:80]},
        )
        return

    add_check(
        checks,
        "schema_retrieval_coverage_report",
        "PASS",
        "CQ-linked schema retrieval is represented by proposed, ablation, and taxonomy baseline conditions with claim-safe silver diagnostics.",
        {
            "json": rel(json_path),
            "markdown": rel(md_path),
            "cq_support_csv": rel(csv_path),
            "conditions": sorted(expected_conditions),
            "cq_count": cq.get("cq_count"),
            "schema_node_types": schema.get("node_type_count"),
            "schema_edge_types": schema.get("edge_type_count"),
            "claim_status": payload.get("claim_status"),
        },
    )


def validate_ablation_coverage_report(checks, exp_dir):
    exp_dir = Path(exp_dir)
    release_dir = exp_dir / "06_release"
    evaluation_dir = exp_dir / "04_evaluation"
    json_path = release_dir / "ablation_coverage_report.json"
    md_path = release_dir / "ablation_coverage_report.md"
    csv_path = evaluation_dir / "ablation_coverage_by_condition.csv"
    expected_status = "ablation_coverage_ready_silver_diagnostic_not_human_gold"
    expected_llm_ablations = {
        "P_minus_CQ",
        "P_minus_Evidence",
        "P_minus_Procedural_schema",
        "P_minus_Schema_retrieval",
        "P_minus_Standard_bridge",
        "P_minus_Validator",
    }
    expected_baselines = {
        "B0_plain_llm",
        "B1_predicate_constrained",
        "B2_current_project",
        "B3_edc_style",
        "B4_taxonomy_rag",
        "B5_procedural_prompt",
        "B6_sac_kg_verifier_pruner",
    }
    issues = []

    try:
        payload = read_json(json_path)
        csv_rows = read_csv_rows(csv_path)
    except Exception as exc:
        add_check(
            checks,
            "ablation_coverage_report",
            "FAIL",
            "Ablation coverage artifacts cannot be read.",
            {"path": rel(json_path), "csv": rel(csv_path), "error": str(exc)},
        )
        return

    if payload.get("claim_status") != expected_status:
        issues.append({"error": "unexpected_claim_status", "actual": payload.get("claim_status")})

    boundary = payload.get("claim_boundary") or {}
    if boundary.get("silver_diagnostic_only") is not True:
        issues.append({"error": "claim_boundary_silver_diagnostic_only_missing"})
    if boundary.get("not_human_gold_performance_evidence") is not True:
        issues.append({"error": "claim_boundary_human_gold_distinction_missing"})
    boundary_text = " ".join(str(boundary.get(key) or "") for key in ["safe_interpretation", "not_claimable_until"])
    for pattern in ["silver/proxy", "human-gold", "IAA", "active-review human effort"]:
        if pattern not in boundary_text:
            issues.append({"error": "claim_boundary_missing_pattern", "pattern": pattern})

    reqs = payload.get("plan_requirements") or {}
    if int(reqs.get("minimum_baseline_conditions_required") or 0) < 3:
        issues.append({"error": "minimum_baseline_requirement_not_recorded", "actual": reqs.get("minimum_baseline_conditions_required")})
    if int(reqs.get("minimum_ablation_conditions_required") or 0) < 3:
        issues.append({"error": "minimum_ablation_requirement_not_recorded", "actual": reqs.get("minimum_ablation_conditions_required")})
    if set(reqs.get("planned_llm_ablation_conditions") or []) != expected_llm_ablations:
        issues.append({
            "error": "planned_llm_ablation_conditions_mismatch",
            "actual": sorted(reqs.get("planned_llm_ablation_conditions") or []),
        })
    if reqs.get("planned_active_review_ablation") is not True:
        issues.append({"error": "planned_active_review_ablation_missing"})

    summary = payload.get("summary") or {}
    expected_summary_values = {
        "baseline_condition_count": 7,
        "planned_llm_ablation_count": 6,
        "completed_llm_ablation_count": 6,
    }
    for key, expected in expected_summary_values.items():
        if int(summary.get(key) or 0) != expected:
            issues.append({"error": "summary_count_mismatch", "field": key, "expected": expected, "actual": summary.get(key)})
    if int(summary.get("baseline_ready_condition_count") or 0) < 7:
        issues.append({"error": "baseline_ready_condition_count_too_low", "actual": summary.get("baseline_ready_condition_count")})
    if summary.get("llm_ablation_rows_all_120") is not True:
        issues.append({"error": "llm_ablation_rows_all_120_not_true", "actual": summary.get("llm_ablation_rows_all_120")})
    if int(summary.get("statistical_comparison_ablation_count") or 0) < 6:
        issues.append({"error": "statistical_comparison_ablation_count_too_low", "actual": summary.get("statistical_comparison_ablation_count")})
    if summary.get("active_review_ablation_present") is not True:
        issues.append({"error": "active_review_ablation_present_not_true", "actual": summary.get("active_review_ablation_present")})
    if summary.get("minimum_baseline_requirement_satisfied") is not True:
        issues.append({"error": "minimum_baseline_requirement_not_satisfied"})
    if summary.get("minimum_ablation_requirement_satisfied") is not True:
        issues.append({"error": "minimum_ablation_requirement_not_satisfied"})
    if summary.get("claim_status") != expected_status:
        issues.append({"error": "summary_claim_status_mismatch", "actual": summary.get("claim_status")})

    baseline_rows = payload.get("baseline_rows") or []
    baseline_conditions = {row.get("condition") for row in baseline_rows}
    if baseline_conditions != expected_baselines:
        issues.append({"error": "baseline_condition_set_mismatch", "actual": sorted(baseline_conditions)})
    for row in baseline_rows:
        if int(row.get("valid_rows_traceability") or 0) < 100 or int(row.get("metric_rows") or 0) < 100:
            issues.append({"condition": row.get("condition"), "error": "baseline_rows_below_100", "row": row})
        if row.get("claim_status") != "silver_proxy_not_human_gold":
            issues.append({"condition": row.get("condition"), "error": "baseline_claim_status_mismatch", "actual": row.get("claim_status")})

    llm_rows = payload.get("llm_ablation_rows") or []
    llm_conditions = {row.get("condition") for row in llm_rows}
    if llm_conditions != expected_llm_ablations:
        issues.append({"error": "llm_ablation_condition_set_mismatch", "actual": sorted(llm_conditions)})
    for row in llm_rows:
        condition = row.get("condition")
        if int(row.get("valid_rows_traceability") or 0) < 100 or int(row.get("metric_rows") or 0) < 100:
            issues.append({"condition": condition, "error": "llm_ablation_rows_below_100", "row": row})
        if row.get("claim_status") != "silver_proxy_not_human_gold":
            issues.append({"condition": condition, "error": "llm_ablation_claim_status_mismatch", "actual": row.get("claim_status")})
        if row.get("statistical_comparison_present") is not True:
            issues.append({"condition": condition, "error": "statistical_comparison_missing"})
        expected_output = set(str(row.get("output_shape_expected") or "").split(",")) - {""}
        actual_output = set(str(row.get("output_shape_actual") or "").split(",")) - {""}
        if not expected_output.issubset(actual_output):
            issues.append({
                "condition": condition,
                "error": "output_shape_mismatch",
                "expected": sorted(expected_output),
                "actual": sorted(actual_output),
            })
        if condition == "P_minus_Standard_bridge" and int(row.get("traceability_mappings") or 0) != 0:
            issues.append({"condition": condition, "error": "standard_bridge_ablation_should_have_zero_mappings", "actual": row.get("traceability_mappings")})

    active_summary = payload.get("active_review_ablation_summary") or {}
    if int(active_summary.get("active_review_ablation_condition_count") or 0) < 2:
        issues.append({"error": "active_review_ablation_conditions_too_few", "actual": active_summary.get("active_review_ablation_condition_count")})
    if int(active_summary.get("active_review_diagnostic_row_count") or 0) < 6:
        issues.append({"error": "active_review_diagnostic_rows_too_few", "actual": active_summary.get("active_review_diagnostic_row_count")})
    if set(active_summary.get("active_review_claim_statuses") or []) != {"silver_proxy_ablation_not_human_efficiency"}:
        issues.append({"error": "active_review_claim_statuses_mismatch", "actual": active_summary.get("active_review_claim_statuses")})

    active_rows = payload.get("active_review_ablation_rows") or []
    active_conditions = {row.get("condition") for row in active_rows}
    if not {"P_minus_Active_review_random_expected", "P_minus_Active_review_uncertainty_only"}.issubset(active_conditions):
        issues.append({"error": "active_review_minus_conditions_missing", "actual": sorted(active_conditions)})
    for row in active_rows:
        if row.get("claim_status") != "silver_proxy_ablation_not_human_efficiency":
            issues.append({"condition": row.get("condition"), "error": "active_review_row_claim_status_mismatch", "actual": row.get("claim_status")})
            break

    csv_conditions = {row.get("condition") for row in csv_rows}
    if not expected_llm_ablations.issubset(csv_conditions):
        issues.append({"error": "csv_missing_llm_ablation_conditions", "actual": sorted(csv_conditions)})
    if not {"P_minus_Active_review_random_expected", "P_minus_Active_review_uncertainty_only"}.issubset(csv_conditions):
        issues.append({"error": "csv_missing_active_review_ablation_conditions", "actual": sorted(csv_conditions)})
    if len(csv_rows) < len(llm_rows) + len(active_rows):
        issues.append({"error": "csv_row_count_too_low", "actual": len(csv_rows), "expected_min": len(llm_rows) + len(active_rows)})

    for label, path_value in (payload.get("input_files") or {}).items():
        if path_value and not Path(path_value).exists():
            issues.append({"error": "input_file_missing", "label": label, "path": path_value})

    if not md_path.exists():
        issues.append({"error": "missing_markdown", "path": rel(md_path)})
    else:
        text = md_path.read_text(encoding="utf-8", errors="replace")
        for pattern in [
            "CAPE-KG Ablation Coverage Report",
            "Claim Boundary",
            "LLM Component Ablations",
            "Active-Review Ablation Diagnostic",
            "Not human-gold performance evidence",
        ]:
            if pattern not in text:
                issues.append({"error": "ablation_markdown_missing_pattern", "pattern": pattern})

    if issues:
        add_check(
            checks,
            "ablation_coverage_report",
            "FAIL",
            "Ablation coverage report is missing, stale, or claim-unsafe.",
            {"path": rel(json_path), "markdown": rel(md_path), "csv": rel(csv_path), "issues": issues[:80]},
        )
        return

    add_check(
        checks,
        "ablation_coverage_report",
        "PASS",
        "Planned baseline, LLM ablation, and active-review ablation diagnostics are covered while final performance claims remain human-gold gated.",
        {
            "json": rel(json_path),
            "markdown": rel(md_path),
            "csv": rel(csv_path),
            "baseline_ready": summary.get("baseline_ready_condition_count"),
            "llm_ablations": summary.get("completed_llm_ablation_count"),
            "active_review_rows": summary.get("active_review_diagnostic_row_count"),
            "claim_status": payload.get("claim_status"),
        },
    )


def validate_alias_canonicalization_report(checks, exp_dir, outputs_dir):
    exp_dir = Path(exp_dir)
    outputs_dir = Path(outputs_dir)
    release_dir = exp_dir / "06_release"
    evaluation_dir = exp_dir / "04_evaluation"
    json_path = release_dir / "alias_canonicalization_report.json"
    md_path = release_dir / "alias_canonicalization_report.md"
    csv_path = evaluation_dir / "alias_canonicalization_collision_groups.csv"
    nodes_path = outputs_dir / "07_layer2_graph/layer2_nodes.jsonl"
    edges_path = outputs_dir / "07_layer2_graph/layer2_edges.jsonl"
    alias_path = outputs_dir / "07_layer2_graph/layer2_alias_dictionary.json"
    quality_path = outputs_dir / "07_layer2_graph/layer2_graph_quality_report.md"
    catalog_path = outputs_dir / "04_task_frames/canonical_task_catalog.json"
    expected_status = "alias_canonicalization_diagnostic_ready_pending_human_gold_node_matching"
    issues = []

    try:
        payload = read_json(json_path)
        csv_rows = read_csv_rows(csv_path)
        nodes = read_jsonl(nodes_path)
        edges = read_jsonl(edges_path)
        alias_dict = read_json(alias_path)
        catalog = read_json(catalog_path)
    except Exception as exc:
        add_check(
            checks,
            "alias_canonicalization_report",
            "FAIL",
            "Alias/canonicalization diagnostic artifacts cannot be read.",
            {"path": rel(json_path), "csv": rel(csv_path), "error": str(exc)},
        )
        return

    if payload.get("claim_status") != expected_status:
        issues.append({"error": "unexpected_claim_status", "actual": payload.get("claim_status")})

    boundary = payload.get("claim_boundary") or {}
    if boundary.get("diagnostic_only") is not True:
        issues.append({"error": "claim_boundary_diagnostic_only_missing"})
    if boundary.get("human_gold_node_matching_required") is not True:
        issues.append({"error": "human_gold_node_matching_required_not_true"})
    if boundary.get("collision_review_required") is not True:
        issues.append({"error": "collision_review_required_not_true"})
    boundary_text = " ".join(str(boundary.get(key) or "") for key in ["safe_interpretation", "not_claimable_until"])
    for pattern in ["human-gold", "node matching", "adjudicated"]:
        if pattern not in boundary_text:
            issues.append({"error": "claim_boundary_missing_pattern", "pattern": pattern})

    module = payload.get("method_module") or {}
    if module.get("module_id") != "M9":
        issues.append({"error": "method_module_not_m9", "actual": module.get("module_id")})

    summary = payload.get("summary") or {}
    nodes_with_aliases = sum(1 for node in nodes if as_list(node.get("aliases")))
    raw_reference_count = 0
    unique_reference_count = 0
    duplicate_reference_count = 0
    collision_group_count = 0
    ambiguous_collision_count = 0
    duplicate_only_group_count = 0
    missing_node_refs = []
    node_ids = {node.get("node_id") for node in nodes}
    for alias, values in (alias_dict or {}).items():
        target_ids = [str(value) for value in as_list(values) if str(value or "").strip()]
        unique_ids = sorted(set(target_ids))
        raw_reference_count += len(target_ids)
        unique_reference_count += len(unique_ids)
        duplicate_count = len(target_ids) - len(unique_ids)
        duplicate_reference_count += duplicate_count
        if len(target_ids) > 1:
            collision_group_count += 1
            if len(unique_ids) > 1:
                ambiguous_collision_count += 1
            elif duplicate_count:
                duplicate_only_group_count += 1
        for node_id in unique_ids:
            if node_id not in node_ids:
                missing_node_refs.append({"alias": alias, "node_id": node_id})

    graph_quality_collision_count = None
    if quality_path.exists():
        text = quality_path.read_text(encoding="utf-8", errors="replace")
        match = re.search(r"Alias collisions:\s*([0-9]+)", text)
        if match:
            graph_quality_collision_count = int(match.group(1))

    expected_summary = {
        "layer2_node_count": len(nodes),
        "layer2_edge_count": len(edges),
        "alias_entry_count": len(alias_dict or {}),
        "collision_alias_count": collision_group_count,
        "ambiguous_collision_alias_count": ambiguous_collision_count,
        "duplicate_reference_only_group_count": duplicate_only_group_count,
        "duplicate_alias_reference_count": duplicate_reference_count,
        "nodes_with_aliases": nodes_with_aliases,
    }
    for key, expected in expected_summary.items():
        if summary.get(key) != expected:
            issues.append({"error": "summary_count_mismatch", "field": key, "expected": expected, "actual": summary.get(key)})
    if summary.get("human_gold_node_matching_required") is not True:
        issues.append({"error": "summary_human_gold_node_matching_required_not_true"})
    if graph_quality_collision_count is not None and summary.get("graph_quality_alias_collision_count") != graph_quality_collision_count:
        issues.append(
            {
                "error": "graph_quality_collision_count_mismatch",
                "expected": graph_quality_collision_count,
                "actual": summary.get("graph_quality_alias_collision_count"),
            }
        )
    if graph_quality_collision_count is not None and collision_group_count != graph_quality_collision_count:
        issues.append(
            {
                "error": "recomputed_collision_count_mismatch_graph_quality",
                "recomputed": collision_group_count,
                "graph_quality": graph_quality_collision_count,
            }
        )
    if collision_group_count <= 0:
        issues.append({"error": "collision_queue_empty"})
    if ambiguous_collision_count <= 0:
        issues.append({"error": "ambiguous_collision_count_empty"})
    if missing_node_refs:
        issues.append({"error": "alias_dictionary_references_missing_nodes", "sample": missing_node_refs[:20]})

    alias_summary = payload.get("alias_dictionary_summary") or {}
    expected_alias_summary = {
        "raw_alias_reference_count": raw_reference_count,
        "unique_alias_reference_count": unique_reference_count,
        "missing_node_reference_count": len(missing_node_refs),
    }
    for key, expected in expected_alias_summary.items():
        if alias_summary.get(key) != expected:
            issues.append({"error": "alias_summary_count_mismatch", "field": key, "expected": expected, "actual": alias_summary.get(key)})

    task_summary = payload.get("canonical_task_summary") or {}
    tasks = catalog.get("tasks") or catalog.get("canonical_tasks") or []
    if int(task_summary.get("canonical_task_count") or 0) != len(tasks):
        issues.append({"error": "canonical_task_count_mismatch", "expected": len(tasks), "actual": task_summary.get("canonical_task_count")})
    if int(task_summary.get("canonical_task_count") or 0) < 20:
        issues.append({"error": "too_few_canonical_tasks", "actual": task_summary.get("canonical_task_count")})
    if task_summary.get("catalog_review_status") != catalog.get("review_status"):
        issues.append({"error": "catalog_review_status_mismatch", "actual": task_summary.get("catalog_review_status")})

    b3 = payload.get("b3_edc_style_baseline_summary") or {}
    b3_rows = {row.get("condition"): row for row in b3.get("condition_rows") or []}
    if int(b3.get("row_count") or 0) < 100:
        issues.append({"error": "b3_edc_valid_rows_too_low", "actual": b3.get("row_count")})
    if int((b3_rows.get("B3_edc_style") or {}).get("rows") or 0) < 100:
        issues.append({"error": "b3_edc_style_condition_rows_too_low", "actual": b3_rows.get("B3_edc_style")})

    if len(csv_rows) != collision_group_count:
        issues.append({"error": "collision_csv_row_count_mismatch", "expected": collision_group_count, "actual": len(csv_rows)})
    csv_kinds = {row.get("collision_kind") for row in csv_rows}
    if not {"cross_type_collision", "duplicate_reference_only"}.issubset(csv_kinds):
        issues.append({"error": "collision_csv_kind_set_incomplete", "actual": sorted(csv_kinds)})
    for row in csv_rows:
        if row.get("claim_status") != expected_status:
            issues.append({"error": "collision_csv_claim_status_mismatch", "row": row})
            break
        if row.get("review_status") != "pending_human_node_matching_review":
            issues.append({"error": "collision_csv_review_status_mismatch", "row": row})
            break

    for label, path_value in (payload.get("input_files") or {}).items():
        if path_value and not Path(path_value).exists():
            issues.append({"error": "input_file_missing", "label": label, "path": path_value})

    if not md_path.exists():
        issues.append({"error": "missing_markdown", "path": rel(md_path)})
    else:
        text = md_path.read_text(encoding="utf-8", errors="replace")
        lowered = text.lower()
        for pattern in [
            "alias/canonicalization diagnostic report",
            "claim boundary",
            "collision review queue",
            "pending human-gold node matching",
        ]:
            if pattern not in lowered:
                issues.append({"error": "alias_canonicalization_markdown_missing_pattern", "pattern": pattern})

    if issues:
        add_check(
            checks,
            "alias_canonicalization_report",
            "FAIL",
            "Alias/canonicalization diagnostic report is missing, stale, or claim-unsafe.",
            {"path": rel(json_path), "markdown": rel(md_path), "csv": rel(csv_path), "issues": issues[:80]},
        )
        return

    add_check(
        checks,
        "alias_canonicalization_report",
        "PASS",
        "M9 alias/canonicalization coverage, collision queue, and human-gold node matching boundary are synchronized.",
        {
            "json": rel(json_path),
            "markdown": rel(md_path),
            "csv": rel(csv_path),
            "layer2_nodes": len(nodes),
            "alias_entries": len(alias_dict or {}),
            "collision_groups": collision_group_count,
            "ambiguous_collision_groups": ambiguous_collision_count,
            "claim_status": payload.get("claim_status"),
        },
    )


def validate_schema_plan_alignment(checks, exp_dir, outputs_dir):
    exp_dir = Path(exp_dir)
    outputs_dir = Path(outputs_dir)
    release_dir = exp_dir / "06_release"
    json_path = release_dir / "schema_plan_alignment.json"
    md_path = release_dir / "schema_plan_alignment.md"
    expected_node_terms = {
        "DomainTask",
        "ProcedureStep",
        "DecisionGateway",
        "GuardCondition",
        "Artifact",
        "ArtifactFlow",
        "Role",
        "ReviewCheckpoint",
        "Principle",
        "Risk",
        "EvidenceAnchor",
        "NCSCompetencyUnit",
        "PCFElement",
        "MappingCandidate",
    }
    expected_edge_terms = {
        "HAS_STEP",
        "PRECEDES",
        "BRANCHES_TO",
        "HAS_GUARD_CONDITION",
        "USES_INPUT",
        "PRODUCES",
        "FEEDS_INTO",
        "PERFORMED_BY",
        "HAS_DECISION_GATEWAY",
        "HAS_REVIEW_CHECKPOINT",
        "HAS_PRINCIPLE",
        "HAS_RISK",
        "EVIDENCED_BY",
        "REQUIRES_CAPABILITY",
        "PROCESS_CONTEXT",
        "CANDIDATE_ALIGNS_WITH",
    }
    expected_pending = {"BRANCHES_TO"}
    allowed_statuses = {
        "canonical_layer2_present",
        "projection_present",
        "mapping_projection_present",
        "represented_as_candidate_rows",
        "layer1_standard_present",
        "pending_structural_review",
    }
    issues = []

    try:
        alignment = read_json(json_path)
    except Exception as exc:
        add_check(
            checks,
            "schema_plan_alignment",
            "FAIL",
            "Schema plan alignment JSON cannot be read.",
            {"path": rel(json_path), "error": str(exc)},
        )
        return

    rows = alignment.get("rows") or []
    summary = alignment.get("summary") or {}
    node_terms = {row.get("term") for row in rows if row.get("kind") == "node_type"}
    edge_terms = {row.get("term") for row in rows if row.get("kind") == "edge_type"}
    row_by_term = {row.get("term"): row for row in rows}

    if alignment.get("claim_status") != "schema_plan_alignment_ready_with_known_structural_gaps":
        issues.append({"error": "unexpected_claim_status", "actual": alignment.get("claim_status")})
    if node_terms != expected_node_terms:
        issues.append({"error": "node_term_set_mismatch", "expected": sorted(expected_node_terms), "actual": sorted(node_terms)})
    if edge_terms != expected_edge_terms:
        issues.append({"error": "edge_term_set_mismatch", "expected": sorted(expected_edge_terms), "actual": sorted(edge_terms)})
    if int(summary.get("alignment_row_count") or 0) != len(expected_node_terms) + len(expected_edge_terms):
        issues.append({"error": "alignment_row_count_mismatch", "actual": summary.get("alignment_row_count")})
    if int(summary.get("missing_unclassified_count") or 0) != 0:
        issues.append({"error": "missing_unclassified_terms", "terms": summary.get("missing_unclassified_terms")})
    if set(summary.get("known_pending_structural_terms") or []) != expected_pending:
        issues.append(
            {
                "error": "known_pending_structural_terms_mismatch",
                "expected": sorted(expected_pending),
                "actual": summary.get("known_pending_structural_terms"),
            }
        )
    if summary.get("unexpected_pending_structural_terms") not in ([], None):
        issues.append({"error": "unexpected_pending_structural_terms", "terms": summary.get("unexpected_pending_structural_terms")})

    pending_terms = {row.get("term") for row in rows if row.get("status") == "pending_structural_review"}
    if pending_terms != expected_pending:
        issues.append({"error": "pending_structural_terms_mismatch", "expected": sorted(expected_pending), "actual": sorted(pending_terms)})

    for row in rows:
        term = row.get("term")
        status = row.get("status")
        if status not in allowed_statuses:
            issues.append({"term": term, "error": "unexpected_alignment_status", "status": status})
        if status != "pending_structural_review" and int(row.get("represented_count") or 0) <= 0:
            issues.append({"term": term, "error": "represented_count_not_positive", "status": status, "represented_count": row.get("represented_count")})
        for evidence_path in row.get("evidence_files") or []:
            if evidence_path and not Path(evidence_path).exists():
                issues.append({"term": term, "error": "evidence_file_missing", "path": evidence_path})

    actual_nodes = read_jsonl(outputs_dir / "07_layer2_graph/layer2_nodes.jsonl")
    actual_edges = read_jsonl(outputs_dir / "07_layer2_graph/layer2_edges.jsonl")
    actual_node_counts = Counter(row.get("type") for row in actual_nodes if row.get("type"))
    actual_edge_counts = Counter(row.get("predicate") for row in actual_edges if row.get("predicate"))
    for term, count in actual_node_counts.items():
        row = row_by_term.get(term)
        if row and int(row.get("canonical_layer2_count") or 0) != count:
            issues.append({"term": term, "error": "canonical_node_count_mismatch", "alignment": row.get("canonical_layer2_count"), "actual": count})
    for term, count in actual_edge_counts.items():
        row = row_by_term.get(term)
        if row and int(row.get("canonical_layer2_count") or 0) != count:
            issues.append({"term": term, "error": "canonical_edge_count_mismatch", "alignment": row.get("canonical_layer2_count"), "actual": count})

    expected_status_by_term = {
        "EvidenceAnchor": "projection_present",
        "EVIDENCED_BY": "projection_present",
        "NCSCompetencyUnit": "layer1_standard_present",
        "PCFElement": "layer1_standard_present",
        "MappingCandidate": "represented_as_candidate_rows",
        "REQUIRES_CAPABILITY": "mapping_projection_present",
        "PROCESS_CONTEXT": "mapping_projection_present",
        "CANDIDATE_ALIGNS_WITH": "represented_as_candidate_rows",
    }
    for term, expected_status in expected_status_by_term.items():
        actual_status = (row_by_term.get(term) or {}).get("status")
        if actual_status != expected_status:
            issues.append({"term": term, "error": "special_term_status_mismatch", "expected": expected_status, "actual": actual_status})

    if not md_path.exists():
        issues.append({"error": "missing_markdown_report", "path": rel(md_path)})
    else:
        text = md_path.read_text(encoding="utf-8", errors="replace")
        for pattern in [
            "CAPE-KG Schema Plan Alignment",
            "## Alignment Rows",
            "## Known Structural Review Terms",
            "## Claim Safety",
            "missing_unclassified",
        ]:
            if pattern not in text:
                issues.append({"error": "schema_alignment_markdown_missing_pattern", "pattern": pattern})

    if issues:
        add_check(
            checks,
            "schema_plan_alignment",
            "FAIL",
            "Schema plan alignment is incomplete, stale, or overclaims current canonical coverage.",
            {"path": rel(json_path), "markdown": rel(md_path), "issues": issues[:80]},
        )
        return

    add_check(
        checks,
        "schema_plan_alignment",
        "PASS",
        "Plan schema terms are classified across canonical Layer 2, evidence/mapping projections, and known structural-review gaps.",
        {
            "json": rel(json_path),
            "markdown": rel(md_path),
            "alignment_rows": len(rows),
            "pending_structural_terms": sorted(pending_terms),
            "status_counts": summary.get("status_counts"),
            "claim_status": alignment.get("claim_status"),
        },
    )


def validate_llm_condition_output_integrity(checks, exp_dir):
    exp_dir = Path(exp_dir)
    traceability_path = exp_dir / "06_release/prompt_node_edge_traceability.json"
    eval_chunks_path = exp_dir / "01_data/evaluation_chunks.jsonl"
    schema_path = exp_dir / "02_schema/cape_schema.json"
    try:
        traceability = read_json(traceability_path)
        eval_chunks = read_jsonl(eval_chunks_path)
        schema = read_json(schema_path)
    except Exception as exc:
        add_check(
            checks,
            "llm_condition_output_integrity",
            "FAIL",
            "LLM condition output integrity inputs cannot be read.",
            {"error": str(exc)},
        )
        return

    output_summary = traceability.get("llm_condition_outputs") or {}
    condition_rows = output_summary.get("conditions") or []
    expected_by_condition = {row.get("condition"): row for row in condition_rows}
    expected_conditions = set(TRACEABILITY_EXPECTED_CONDITIONS)
    expected_chunk_ids = {row.get("chunk_id") for row in eval_chunks}
    chunk_sentence_ids = {
        row.get("chunk_id"): set(as_list(row.get("sentence_ids")))
        for row in eval_chunks
    }
    allowed_node_types = set(schema.get("node_types") or [])
    allowed_edge_types = set(schema.get("edge_types") or [])
    valid_files = [value for value in as_list(output_summary.get("valid_files") or output_summary.get("valid_file")) if value]

    issues = []
    condition_chunk_pairs = set()
    condition_chunks = {condition: set() for condition in expected_conditions}
    condition_counts = {
        condition: {"rows": 0, "nodes": 0, "edges": 0, "triples": 0, "mappings": 0}
        for condition in expected_conditions
    }
    total_rows = 0

    def add_issue(error, **payload):
        if len(issues) < 120:
            row = {"error": error}
            row.update(payload)
            issues.append(row)

    def evidence_ids(item):
        return as_list(item.get("evidence_anchor_ids"))

    def validate_evidence(condition, chunk_id, collection, row_no, item_index, item):
        evs = evidence_ids(item)
        if not evs:
            add_issue(
                "missing_evidence_anchor_ids",
                condition=condition,
                chunk_id=chunk_id,
                collection=collection,
                line=row_no,
                item_index=item_index,
            )
            return
        allowed_sentence_ids = chunk_sentence_ids.get(chunk_id) or set()
        for evidence_id in evs:
            sentence_id = evidence_id[3:] if isinstance(evidence_id, str) and evidence_id.startswith("EA-") else evidence_id
            if sentence_id not in allowed_sentence_ids:
                add_issue(
                    "evidence_anchor_not_in_chunk",
                    condition=condition,
                    chunk_id=chunk_id,
                    collection=collection,
                    line=row_no,
                    item_index=item_index,
                    evidence_anchor_id=evidence_id,
                )

    for file_value in valid_files:
        path = Path(file_value)
        if not path.exists():
            add_issue("valid_file_missing", path=rel(path))
            continue
        try:
            rows = read_jsonl(path)
        except Exception as exc:
            add_issue("valid_file_unreadable", path=rel(path), error=str(exc))
            continue
        for row in rows:
            total_rows += 1
            row_no = row.get("_line_no")
            condition = row.get("condition")
            chunk_id = row.get("chunk_id")
            if condition not in expected_conditions:
                add_issue("unexpected_condition", condition=condition, path=rel(path), line=row_no)
                continue
            if chunk_id not in expected_chunk_ids:
                add_issue("unexpected_chunk_id", condition=condition, chunk_id=chunk_id, path=rel(path), line=row_no)
                continue
            pair = (condition, chunk_id)
            if pair in condition_chunk_pairs:
                add_issue("duplicate_condition_chunk_row", condition=condition, chunk_id=chunk_id, path=rel(path), line=row_no)
                continue
            condition_chunk_pairs.add(pair)
            condition_chunks[condition].add(chunk_id)
            condition_counts[condition]["rows"] += 1

            for field in ["nodes", "edges", "triples", "mappings"]:
                if not isinstance(row.get(field), list):
                    add_issue(
                        "output_field_not_list",
                        condition=condition,
                        chunk_id=chunk_id,
                        field=field,
                        path=rel(path),
                        line=row_no,
                    )
                    row[field] = []
                condition_counts[condition][field] += len(row.get(field) or [])

            # P_minus_Validator deliberately weakens schema rejection, so schema-term checks are skipped for it.
            schema_terms_required = condition != "P_minus_Validator"
            for idx, item in enumerate(row.get("nodes") or []):
                if not item.get("label") or not item.get("type"):
                    add_issue("node_missing_label_or_type", condition=condition, chunk_id=chunk_id, line=row_no, item_index=idx)
                if schema_terms_required and item.get("type") not in allowed_node_types:
                    add_issue("node_type_outside_schema", condition=condition, chunk_id=chunk_id, line=row_no, item_index=idx, node_type=item.get("type"))
                validate_evidence(condition, chunk_id, "nodes", row_no, idx, item)

            for idx, item in enumerate(row.get("edges") or []):
                for required_field in ["subject", "predicate", "object"]:
                    if not item.get(required_field):
                        add_issue("edge_missing_required_field", condition=condition, chunk_id=chunk_id, line=row_no, item_index=idx, field=required_field)
                if schema_terms_required and item.get("predicate") not in allowed_edge_types:
                    add_issue("edge_predicate_outside_schema", condition=condition, chunk_id=chunk_id, line=row_no, item_index=idx, predicate=item.get("predicate"))
                for type_field in ["subject_type", "object_type"]:
                    if schema_terms_required and item.get(type_field) and item.get(type_field) not in allowed_node_types:
                        add_issue("edge_endpoint_type_outside_schema", condition=condition, chunk_id=chunk_id, line=row_no, item_index=idx, field=type_field, node_type=item.get(type_field))
                validate_evidence(condition, chunk_id, "edges", row_no, idx, item)

            for idx, item in enumerate(row.get("triples") or []):
                for required_field in ["subject", "predicate", "object"]:
                    if not item.get(required_field):
                        add_issue("triple_missing_required_field", condition=condition, chunk_id=chunk_id, line=row_no, item_index=idx, field=required_field)
                validate_evidence(condition, chunk_id, "triples", row_no, idx, item)

            for idx, item in enumerate(row.get("mappings") or []):
                for required_field in ["source_task", "standard", "target_label"]:
                    if not item.get(required_field):
                        add_issue("mapping_missing_required_field", condition=condition, chunk_id=chunk_id, line=row_no, item_index=idx, field=required_field)
                if item.get("standard") and item.get("standard") not in {"NCS", "PCF"}:
                    add_issue("mapping_unknown_standard", condition=condition, chunk_id=chunk_id, line=row_no, item_index=idx, standard=item.get("standard"))
                validate_evidence(condition, chunk_id, "mappings", row_no, idx, item)

    if set(expected_by_condition) != expected_conditions:
        add_issue(
            "traceability_condition_set_mismatch",
            expected=sorted(expected_conditions),
            actual=sorted(expected_by_condition),
        )
    if int(output_summary.get("total_rows") or 0) != total_rows:
        add_issue("total_row_count_mismatch", traceability=output_summary.get("total_rows"), actual=total_rows)

    for condition in sorted(expected_conditions):
        chunks = condition_chunks.get(condition) or set()
        if chunks != expected_chunk_ids:
            add_issue(
                "condition_chunk_coverage_mismatch",
                condition=condition,
                expected_chunks=len(expected_chunk_ids),
                actual_chunks=len(chunks),
                missing_count=len(expected_chunk_ids - chunks),
                extra_count=len(chunks - expected_chunk_ids),
            )
        expected_row = expected_by_condition.get(condition) or {}
        actual_counts = condition_counts[condition]
        for field in ["valid_rows", "nodes", "edges", "triples", "mappings"]:
            actual_field = "rows" if field == "valid_rows" else field
            if int(expected_row.get(field) or 0) != actual_counts[actual_field]:
                add_issue(
                    "condition_summary_count_mismatch",
                    condition=condition,
                    field=field,
                    traceability=expected_row.get(field),
                    actual=actual_counts[actual_field],
                )
        for expected_key in as_list(expected_row.get("expected_output_keys")):
            if expected_key in {"nodes", "edges", "triples", "mappings"} and actual_counts.get(expected_key, 0) <= 0:
                add_issue(
                    "expected_output_key_has_no_items",
                    condition=condition,
                    expected_output_key=expected_key,
                )

    if issues:
        add_check(
            checks,
            "llm_condition_output_integrity",
            "FAIL",
            "LLM valid outputs do not fully match expected condition/chunk coverage, JSON shape, or evidence anchoring.",
            {"issues": issues},
        )
        return

    add_check(
        checks,
        "llm_condition_output_integrity",
        "PASS",
        "LLM baseline, proposed, and ablation valid outputs cover all expected chunks with valid JSON shape and chunk-local evidence anchors.",
        {
            "conditions": len(expected_conditions),
            "evaluation_chunks": len(expected_chunk_ids),
            "total_rows": total_rows,
            "valid_files": valid_files,
            "per_condition_rows": 120,
            "claim_status": "llm_output_integrity_ready_not_human_gold_performance_evidence",
        },
    )


def validate_review_guidance(checks, exp_dir):
    exp_dir = Path(exp_dir)
    guidance_files = {
        exp_dir / "01_data/annotation_guideline_v1.md": [
            "## 5. Candidate edge 처리 절차",
            "## 9. Quality checklist",
            "## 11. Paper claim 주의사항",
        ],
        exp_dir / "01_data/gold_annotation/adjudication_protocol.md": [
            "## 8. Adjudicator 판정 기준",
            "## 10. Minimum paper gate",
            "## 11. Adjudication checklist",
        ],
        exp_dir / "01_data/mapping_review/mapping_review_protocol.md": [
            "## 4. Accept 기준",
            "## 10. Completion checklist",
            "## 11. Paper claim 주의사항",
        ],
        exp_dir / "06_release/human_review_start_here_ko.md": [
            "상세 annotation guideline",
            "validate_cape_human_review_returns.py",
            "Active Review Human-Effort",
            "Required claim/human",
            "master",
        ],
        exp_dir / "06_release/human_review_claim_gate_one_page_ko.md": [
            "Minimum Paper Gate를 여는 필수 반환 파일",
            "adjudication_edited.jsonl",
            "mapping_review_items.reviewed.jsonl",
            "crosswalk_review_items.reviewed.jsonl",
            "active_review_human_effort.reviewed.csv",
            "APPLY_IMPORTS=1",
            "silver/proxy score",
        ],
        exp_dir / "06_release/human_review_master_checklist_ko.md": [
            "Required claim/human 반환 파일 14개",
            "선택 구조 검수 파일 2개",
            "All master return files",
            "선택 Strong 300+ 검수 Bundle",
            "실행 명령",
        ],
        exp_dir / "06_release/human_review_status_dashboard_ko.md": [
            "CAPE-KG 사람 검수 상태 대시보드",
            "Required claim/human return files",
            "Optional structural review files",
            "All master return files",
            "진행 상태",
            "즉시 열 파일",
            "다음 명령",
            "아직 claim하면 안 되는 것",
        ],
        exp_dir / "06_release/annotation_calibration_pack_ko.md": [
            "CAPE-KG Annotation Calibration Pack",
            "formal priority-100 annotation",
            "정답지가 아니며",
            "논문용 human-gold evidence도 아닙니다",
        ],
        exp_dir / "06_release/annotation_return_field_guide_ko.md": [
            "CAPE-KG Annotation Return Field Guide",
            "Reviewer-Editable Fields",
            "Immutable Fields",
            "rejected_candidate_reference_ids",
            "needs_adjudication",
            "validate_cape_human_review_returns.py",
            "not human-gold",
        ],
        exp_dir / "06_release/human_return_validation_error_playbook_ko.md": [
            "CAPE-KG Human Return Validation Error Playbook",
            "completed_chunk_has_unreviewed_candidate_edges",
            "reviewed_row_missing_positive_review_seconds",
            "invalid_human_decision",
            "validate_cape_human_review_returns.py",
            "validate_cape_structural_review_returns.py",
            "not human-gold",
        ],
        exp_dir / "06_release/human_review_handoff/README_strong_resegmented_review_ko.md": [
            "## Package",
            "## Expected Reviewed Files",
            "## IAA and Adjudication",
            "strong_resegmented_342_max18",
        ],
        exp_dir / "06_release/active_review_human_effort_plan.md": [
            "Expected reviewed CSV",
            "review_seconds",
            "human-effort evidence",
        ],
        exp_dir / "06_release/structural_review_action_plan.md": [
            "Optional Return Files",
            "Input CSV Fields",
            "guard_condition_labels",
            "candidate_branch_target_labels",
            "Decision Policy",
            "Allowed Decisions",
        ],
        exp_dir / "06_release/structural_review_application_plan.md": [
            "dry-run application plan",
            "does not modify the KG",
            "Decision Mapping",
        ],
    }
    issues = []
    for path, patterns in guidance_files.items():
        if not path.exists():
            issues.append({"path": rel(path), "error": "missing_guidance_file"})
            continue
        text = path.read_text(encoding="utf-8")
        missing_patterns = [pattern for pattern in patterns if pattern not in text]
        if missing_patterns:
            issues.append({"path": rel(path), "error": "missing_required_sections", "missing": missing_patterns})

    gateway_branch_worklist_path = exp_dir / "05_review/structural_gateway_branch_gaps.csv"
    if gateway_branch_worklist_path.exists():
        gateway_rows = read_csv_rows(gateway_branch_worklist_path)
        gateway_fields = set(gateway_rows[0].keys()) if gateway_rows else set()
        required_gateway_fields = {
            "gateway_id",
            "gateway_label",
            "guard_condition_ids",
            "guard_condition_labels",
            "incoming_task_ids",
            "incoming_task_labels",
            "candidate_branch_target_ids",
            "candidate_branch_target_labels",
            "human_decision",
            "human_notes",
        }
        missing_gateway_fields = sorted(required_gateway_fields - gateway_fields)
        if not gateway_rows:
            issues.append({"path": rel(gateway_branch_worklist_path), "error": "empty_structural_gateway_branch_worklist"})
        if missing_gateway_fields:
            issues.append(
                {
                    "path": rel(gateway_branch_worklist_path),
                    "error": "structural_gateway_branch_worklist_missing_reviewer_context_fields",
                    "missing": missing_gateway_fields,
                }
            )
        if gateway_rows and not any((row.get("candidate_branch_target_labels") or "").strip() for row in gateway_rows):
            issues.append(
                {
                    "path": rel(gateway_branch_worklist_path),
                    "error": "structural_gateway_branch_worklist_missing_candidate_target_labels",
                }
            )
    else:
        issues.append({"path": rel(gateway_branch_worklist_path), "error": "missing_structural_gateway_branch_worklist"})

    field_guide_json_path = exp_dir / "06_release/annotation_return_field_guide.json"
    field_guide_csv_path = exp_dir / "05_review/annotation_return_field_checklist.csv"
    try:
        field_guide = read_json(field_guide_json_path)
        field_checklist_rows = read_csv_rows(field_guide_csv_path)
    except Exception as exc:
        issues.append(
            {
                "path": rel(field_guide_json_path),
                "error": "annotation_return_field_guide_unreadable",
                "detail": str(exc),
            }
        )
        field_guide = {}
        field_checklist_rows = []
    expected_editable_fields = {
        "annotation_status",
        "gold_nodes",
        "gold_edges",
        "rejected_candidate_reference_ids",
        "comments",
        "time_minutes",
    }
    editable_fields = set(field_guide.get("editable_fields") or [])
    missing_editable_fields = sorted(expected_editable_fields - editable_fields)
    if missing_editable_fields:
        issues.append(
            {
                "path": rel(field_guide_json_path),
                "error": "annotation_return_field_guide_missing_editable_fields",
                "missing": missing_editable_fields,
            }
        )
    if field_guide.get("claim_status") != "annotation_return_field_guide_ready_pending_human_returns":
        issues.append(
            {
                "path": rel(field_guide_json_path),
                "error": "annotation_return_field_guide_claim_status_unexpected",
                "actual": field_guide.get("claim_status"),
            }
        )
    checklist_by_field = {(row.get("scope"), row.get("field")): row for row in field_checklist_rows}
    for scope, field in [
        ("top_level", "annotation_status"),
        ("top_level", "gold_edges"),
        ("top_level", "rejected_candidate_reference_ids"),
        ("gold_edges[]", "predicate"),
        ("gold_edges[]", "evidence_spans"),
    ]:
        if (scope, field) not in checklist_by_field:
            issues.append(
                {
                    "path": rel(field_guide_csv_path),
                    "error": "annotation_return_field_checklist_missing_row",
                    "scope": scope,
                    "field": field,
                }
            )

    error_playbook_json_path = exp_dir / "06_release/human_return_validation_error_playbook.json"
    error_playbook_csv_path = exp_dir / "05_review/human_return_validation_error_codes.csv"
    try:
        error_playbook = read_json(error_playbook_json_path)
        error_code_rows = read_csv_rows(error_playbook_csv_path)
    except Exception as exc:
        issues.append(
            {
                "path": rel(error_playbook_json_path),
                "error": "human_return_validation_error_playbook_unreadable",
                "detail": str(exc),
            }
        )
        error_playbook = {}
        error_code_rows = []
    if error_playbook.get("claim_status") != "human_return_error_playbook_ready_pending_human_returns":
        issues.append(
            {
                "path": rel(error_playbook_json_path),
                "error": "human_return_validation_error_playbook_claim_status_unexpected",
                "actual": error_playbook.get("claim_status"),
            }
        )
    expected_error_codes = {
        "invalid_annotation_status",
        "completed_chunk_has_unreviewed_candidate_edges",
        "needs_adjudication_missing_comments",
        "completed_adjudication_missing_adjudicator_id",
        "invalid expert_decision",
        "reviewed_row_missing_positive_review_seconds",
        "invalid_human_decision",
    }
    actual_error_codes = {row.get("error_code_or_pattern") for row in error_code_rows}
    missing_error_codes = sorted(expected_error_codes - actual_error_codes)
    if missing_error_codes:
        issues.append(
            {
                "path": rel(error_playbook_csv_path),
                "error": "human_return_validation_error_playbook_missing_required_codes",
                "missing": missing_error_codes,
            }
        )
    expected_error_scopes = {
        "annotation",
        "adjudication",
        "mapping",
        "crosswalk",
        "active_review_effort",
        "structural_review",
    }
    actual_error_scopes = {row.get("scope") for row in error_code_rows}
    missing_error_scopes = sorted(expected_error_scopes - actual_error_scopes)
    if missing_error_scopes:
        issues.append(
            {
                "path": rel(error_playbook_csv_path),
                "error": "human_return_validation_error_playbook_missing_scopes",
                "missing": missing_error_scopes,
            }
        )

    annotation_guideline_path = exp_dir / "01_data/annotation_guideline_v1.md"
    adjudication_protocol_path = exp_dir / "01_data/gold_annotation/adjudication_protocol.md"
    mapping_protocol_path = exp_dir / "01_data/mapping_review/mapping_review_protocol.md"

    plan_8_3_annotation_patterns = {
        "node_types": [
            "DomainTask",
            "ProcedureStep",
            "DecisionGateway",
            "GuardCondition",
            "Artifact",
            "ArtifactFlow",
            "Role",
            "ReviewCheckpoint",
            "Principle",
            "Risk",
        ],
        "edge_predicates_and_evidence": [
            "HAS_STEP",
            "PRECEDES",
            "USES_INPUT",
            "PRODUCES",
            "PERFORMED_BY",
            "HAS_DECISION_GATEWAY",
            "HAS_GUARD_CONDITION",
            "HAS_PRINCIPLE",
            "HAS_RISK",
            "FEEDS_INTO",
            "USED_AS_INPUT_FOR",
            "evidence anchor",
            "evidence span",
            "chunk_id",
            "page",
        ],
        "review_workflow": [
            "silver_candidate_edges",
            "gold_edges",
            "rejected_candidate_reference_ids",
            "missing but supported",
            "annotation_status",
            "completed",
            "needs_adjudication",
            "comments",
            "unsupported candidate",
            "Paper claim",
        ],
    }
    if annotation_guideline_path.exists():
        text = annotation_guideline_path.read_text(encoding="utf-8")
        for group, patterns in plan_8_3_annotation_patterns.items():
            missing_patterns = [pattern for pattern in patterns if pattern not in text]
            if missing_patterns:
                issues.append(
                    {
                        "path": rel(annotation_guideline_path),
                        "error": "missing_plan_8_3_annotation_guidance",
                        "group": group,
                        "missing": missing_patterns,
                    }
                )

    adjudication_patterns = [
        "Annotator A",
        "Annotator B",
        "IAA",
        "adjudicated gold",
        "adjudication_draft",
        "Adjudicated chunks",
        "Gold node/edge/evidence items",
        "conservative gold",
        "chunk text",
        "APPLY_IMPORTS=1",
        "claim_gate_report.md",
    ]
    if adjudication_protocol_path.exists():
        text = adjudication_protocol_path.read_text(encoding="utf-8")
        missing_patterns = [pattern for pattern in adjudication_patterns if pattern not in text]
        if missing_patterns:
            issues.append(
                {
                    "path": rel(adjudication_protocol_path),
                    "error": "missing_plan_8_3_adjudication_guidance",
                    "missing": missing_patterns,
                }
            )

    mapping_review_patterns = [
        "Top-5",
        "Hit@1",
        "Hit@3",
        "Hit@5",
        "Precision@5",
        "MRR",
        "expert accept rate",
        "relevance_grade",
        "accepted",
        "rejected",
        "unsure",
        "mapping_review_items.reviewed.jsonl",
        "evaluate_cape_mapping_review.py",
        "downstream mapping 성능 주장",
    ]
    if mapping_protocol_path.exists():
        text = mapping_protocol_path.read_text(encoding="utf-8")
        missing_patterns = [pattern for pattern in mapping_review_patterns if pattern not in text]
        if missing_patterns:
            issues.append(
                {
                    "path": rel(mapping_protocol_path),
                    "error": "missing_plan_8_3_mapping_review_guidance",
                    "missing": missing_patterns,
                    }
                )

    crosswalk_protocol_path = exp_dir / "01_data/crosswalk_review/crosswalk_review_protocol.md"
    crosswalk_review_patterns = [
        "NCS-PCF Crosswalk Expert Review",
        "accepted",
        "rejected",
        "unsure",
        "utility_grade",
        "explanation_quality_score",
        "crosswalk_review_items.reviewed.jsonl",
        "import_cape_crosswalk_review.py",
        "evaluate_cape_crosswalk_review.py",
    ]
    if crosswalk_protocol_path.exists():
        text = crosswalk_protocol_path.read_text(encoding="utf-8")
        missing_patterns = [pattern for pattern in crosswalk_review_patterns if pattern not in text]
        if missing_patterns:
            issues.append(
                {
                    "path": rel(crosswalk_protocol_path),
                    "error": "missing_crosswalk_review_guidance",
                    "missing": missing_patterns,
                }
            )
    else:
        issues.append({"path": rel(crosswalk_protocol_path), "error": "missing_crosswalk_review_protocol"})

    calibration_json_path = exp_dir / "06_release/annotation_calibration_pack.json"
    calibration_md_path = exp_dir / "06_release/annotation_calibration_pack_ko.md"
    calibration_csv_path = exp_dir / "05_review/annotation_calibration_examples.csv"
    try:
        calibration = read_json(calibration_json_path)
        calibration_rows = read_csv_rows(calibration_csv_path)
        if calibration.get("claim_status") != "calibration_only_not_human_gold_evidence":
            issues.append(
                {
                    "path": rel(calibration_json_path),
                    "error": "annotation_calibration_claim_status_unexpected",
                    "actual": calibration.get("claim_status"),
                }
            )
        if calibration.get("formal_priority_overlap_count") != 0:
            issues.append(
                {
                    "path": rel(calibration_json_path),
                    "error": "annotation_calibration_overlaps_formal_priority",
                    "actual": calibration.get("formal_priority_overlap_count"),
                }
            )
        if len(calibration_rows) != calibration.get("example_count"):
            issues.append(
                {
                    "path": rel(calibration_csv_path),
                    "error": "annotation_calibration_csv_json_count_mismatch",
                    "csv_rows": len(calibration_rows),
                    "json_examples": calibration.get("example_count"),
                }
            )
        focus_counts = calibration.get("focus_counts") or {}
        if len(focus_counts) < 4 or int(calibration.get("example_count") or 0) < 8:
            issues.append(
                {
                    "path": rel(calibration_json_path),
                    "error": "annotation_calibration_coverage_too_small",
                    "example_count": calibration.get("example_count"),
                    "focus_counts": focus_counts,
                }
            )
        for row in calibration_rows:
            if not row.get("recommended_check") or not row.get("sample_evidence_excerpt"):
                issues.append(
                    {
                        "path": rel(calibration_csv_path),
                        "error": "annotation_calibration_row_missing_guidance",
                        "calibration_id": row.get("calibration_id"),
                    }
                )
                break
        if calibration_md_path.exists():
            text = calibration_md_path.read_text(encoding="utf-8")
            for pattern in [
                "formal 100개 priority batch와 겹치지 않는 non-priority rows",
                "정답지가 아니며",
                "논문용 human-gold evidence도 아닙니다",
                "minimum paper gate",
            ]:
                if pattern not in text:
                    issues.append(
                        {
                            "path": rel(calibration_md_path),
                            "error": "annotation_calibration_missing_claim_safety_text",
                            "pattern": pattern,
                        }
                    )
        else:
            issues.append({"path": rel(calibration_md_path), "error": "missing_annotation_calibration_markdown"})
    except Exception as exc:
        issues.append(
            {
                "path": rel(calibration_json_path),
                "error": "cannot_read_annotation_calibration_pack",
                "detail": str(exc),
            }
        )

    banned_instruction_phrases = [
        "README의 dry-run import",
        "전체 반환 파일을 한 번에 처리하려면 아래 wrapper",
        "current required human-return gate",
        "13 required human-return",
        "13 required",
        "does not change the 13",
    ]
    wrapper_required_patterns = [
        "APPLY_IMPORTS=0",
        "APPLY_IMPORTS=1",
        "scripts/run_cape_human_return_apply.sh",
    ]
    handoff_dir = exp_dir / "06_release/human_review_handoff"
    wrapper_instruction_files = {
        exp_dir / "06_release/human_review_start_here_ko.md": wrapper_required_patterns
        + ["개별 import 명령의 `--apply`는 특정 파일 디버깅 때만 사용한다"],
        exp_dir / "06_release/human_review_claim_gate_one_page_ko.md": wrapper_required_patterns
        + ["reviewed file이 없으면 `APPLY_IMPORTS=1`은 기본적으로 거부된다"],
        handoff_dir / "README_annotator_A_ko.md": wrapper_required_patterns
        + ["운영 반영은 위 wrapper를 기본 경로로 사용한다"],
        handoff_dir / "README_annotator_B_ko.md": wrapper_required_patterns
        + ["운영 반영은 위 wrapper를 기본 경로로 사용한다"],
        handoff_dir / "README_coordinator_ko.md": wrapper_required_patterns
        + ["아래 batch별 명령은 특정 reviewed file 문제를 디버깅할 때만 사용한다"],
        handoff_dir / "README_adjudicator_ko.md": wrapper_required_patterns,
        handoff_dir / "README_mapping_expert_ko.md": wrapper_required_patterns,
        handoff_dir / "README_crosswalk_expert_ko.md": wrapper_required_patterns,
        handoff_dir / "README_active_review_effort_ko.md": wrapper_required_patterns,
    }
    optional_instruction_files = {
        handoff_dir / "README_strong_resegmented_review_ko.md": [
            "validate_cape_strong_review_returns.py",
            "strong_resegmented_342_max18",
            "optional strong package",
        ],
        handoff_dir / "README_structural_reviewer_ko.md": [
            "reviewed CSV가 돌아오기 전에는 KG를 자동 수정하지 않는다",
            "minimum paper-gate",
        ],
    }
    instruction_safety_files = {
        *wrapper_instruction_files.keys(),
        *optional_instruction_files.keys(),
        exp_dir / "06_release/human_review_handoff/human_review_handoff_report.md",
    }
    for path in sorted(instruction_safety_files, key=lambda item: item.as_posix()):
        if not path.exists():
            issues.append({"path": rel(path), "error": "missing_instruction_safety_file"})
            continue
        text = path.read_text(encoding="utf-8")
        banned_found = [phrase for phrase in banned_instruction_phrases if phrase in text]
        if banned_found:
            issues.append({"path": rel(path), "error": "unsafe_or_stale_handoff_instruction", "phrases": banned_found})

    for path, required_patterns in wrapper_instruction_files.items():
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        missing_patterns = [pattern for pattern in required_patterns if pattern not in text]
        if missing_patterns:
            issues.append({"path": rel(path), "error": "missing_safe_wrapper_instruction", "missing": missing_patterns})

    stale_return_count_files = [
        exp_dir / "06_release/human_review_start_here_ko.md",
        exp_dir / "06_release/human_review_claim_gate_one_page_ko.md",
        exp_dir / "06_release/human_review_master_checklist_ko.md",
        exp_dir / "06_release/human_review_status_dashboard_ko.md",
        exp_dir / "06_release/human_gate_action_plan.md",
        exp_dir / "05_review/human_review_role_quickstart_cards_ko.md",
    ]
    stale_return_count_phrases = [
        "All tracked human-return files",
        "All tracked human return files",
        "전체 추적 반환 파일은 `0/14`",
        "전체 추적 반환 파일 14개",
    ]
    for path in stale_return_count_files:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        stale_found = [phrase for phrase in stale_return_count_phrases if phrase in text]
        if stale_found:
            issues.append(
                {
                    "path": rel(path),
                    "error": "stale_human_return_count_wording",
                    "phrases": stale_found,
                    "expected": "Use 11 minimum + 3 optional/strong claim + 2 optional structural = 16 master wording.",
                }
            )

    pinned_python_patterns = [
        "/home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python",
        "$HOME/tdpo2_aaai2027/.venv_tdpo2/bin/python",
        "tdpo2_aaai2027/.venv_tdpo2/bin/python",
    ]
    human_batch_dir = exp_dir / "05_review/human_gold_batches"
    portable_command_files = [
        exp_dir / "06_release/human_review_start_here_ko.md",
        exp_dir / "06_release/human_review_claim_gate_one_page_ko.md",
        exp_dir / "06_release/human_review_master_checklist_ko.md",
        exp_dir / "06_release/human_review_status_dashboard_ko.md",
        exp_dir / "06_release/human_review_launch_checklist_ko.md",
        exp_dir / "06_release/human_review_return_preflight.md",
        exp_dir / "06_release/human_gate_action_plan.md",
        exp_dir / "06_release/annotation_batch_assignment_report.md",
        exp_dir / "06_release/annotation_batch_assignment_summary.json",
        exp_dir / "05_review/human_review_first_batch_execution_card_ko.md",
        exp_dir / "05_review/human_review_role_quickstart_cards_ko.md",
        *sorted(handoff_dir.glob("README_*_ko.md")),
        *sorted(human_batch_dir.glob("full_120_priority_batch_*/README.md")),
        *sorted(human_batch_dir.glob("full_120_priority_batch_*/batch_manifest.json")),
    ]
    portable_command_files = sorted(set(portable_command_files), key=lambda item: item.as_posix())
    for path in portable_command_files:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        pinned_found = [pattern for pattern in pinned_python_patterns if pattern in text]
        if pinned_found:
            issues.append(
                {
                    "path": rel(path),
                    "error": "pinned_python_path_in_human_review_command",
                    "patterns": pinned_found,
                    "expected": "Use python3/PYTHON_BIN=python3 in human-review operating docs.",
                }
            )

    for path, required_patterns in optional_instruction_files.items():
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        missing_patterns = [pattern for pattern in required_patterns if pattern not in text]
        if missing_patterns:
            issues.append({"path": rel(path), "error": "missing_optional_review_safety_instruction", "missing": missing_patterns})

    manifest = read_json(exp_dir / "06_release/human_review_handoff/human_review_handoff_manifest.json")
    bundles = manifest.get("bundles") or {}
    expected_tar_members = {
        "annotator_A": [
            exp_dir / "01_data/annotation_guideline_v1.md",
            exp_dir / "01_data/gold_annotation/adjudication_protocol.md",
            exp_dir / "06_release/human_review_start_here_ko.md",
            exp_dir / "06_release/human_review_claim_gate_one_page_ko.md",
            exp_dir / "06_release/annotation_calibration_pack_ko.md",
            exp_dir / "06_release/annotation_calibration_pack.json",
            exp_dir / "06_release/annotation_return_field_guide_ko.md",
            exp_dir / "06_release/annotation_return_field_guide.json",
            exp_dir / "05_review/annotation_return_field_checklist.csv",
            exp_dir / "06_release/human_return_validation_error_playbook_ko.md",
            exp_dir / "06_release/human_return_validation_error_playbook.json",
            exp_dir / "05_review/human_return_validation_error_codes.csv",
            exp_dir / "05_review/annotation_calibration_examples.csv",
            exp_dir / "06_release/human_review_master_checklist_ko.md",
            exp_dir / "06_release/human_review_status_dashboard_ko.md",
            exp_dir / "05_review/human_review_status_next_actions.csv",
            exp_dir / "05_review/human_review_master_return_files.csv",
            Path("scripts/build_cape_annotation_return_field_guide.py"),
            Path("scripts/build_cape_human_return_error_playbook.py"),
            Path("scripts/run_cape_human_return_apply.sh"),
        ],
        "annotator_B": [
            exp_dir / "01_data/annotation_guideline_v1.md",
            exp_dir / "01_data/gold_annotation/adjudication_protocol.md",
            exp_dir / "06_release/human_review_start_here_ko.md",
            exp_dir / "06_release/human_review_claim_gate_one_page_ko.md",
            exp_dir / "06_release/annotation_calibration_pack_ko.md",
            exp_dir / "06_release/annotation_calibration_pack.json",
            exp_dir / "06_release/annotation_return_field_guide_ko.md",
            exp_dir / "06_release/annotation_return_field_guide.json",
            exp_dir / "05_review/annotation_return_field_checklist.csv",
            exp_dir / "06_release/human_return_validation_error_playbook_ko.md",
            exp_dir / "06_release/human_return_validation_error_playbook.json",
            exp_dir / "05_review/human_return_validation_error_codes.csv",
            exp_dir / "05_review/annotation_calibration_examples.csv",
            exp_dir / "06_release/human_review_master_checklist_ko.md",
            exp_dir / "06_release/human_review_status_dashboard_ko.md",
            exp_dir / "05_review/human_review_status_next_actions.csv",
            exp_dir / "05_review/human_review_master_return_files.csv",
            Path("scripts/build_cape_annotation_return_field_guide.py"),
            Path("scripts/build_cape_human_return_error_playbook.py"),
            Path("scripts/run_cape_human_return_apply.sh"),
        ],
        "coordinator": [
            exp_dir / "01_data/annotation_guideline_v1.md",
            exp_dir / "01_data/gold_annotation/adjudication_protocol.md",
            exp_dir / "06_release/human_review_start_here_ko.md",
            exp_dir / "06_release/human_review_claim_gate_one_page_ko.md",
            exp_dir / "06_release/annotation_calibration_pack_ko.md",
            exp_dir / "06_release/annotation_calibration_pack.json",
            exp_dir / "06_release/annotation_return_field_guide_ko.md",
            exp_dir / "06_release/annotation_return_field_guide.json",
            exp_dir / "05_review/annotation_return_field_checklist.csv",
            exp_dir / "06_release/human_return_validation_error_playbook_ko.md",
            exp_dir / "06_release/human_return_validation_error_playbook.json",
            exp_dir / "05_review/human_return_validation_error_codes.csv",
            exp_dir / "05_review/annotation_calibration_examples.csv",
            exp_dir / "06_release/human_review_master_checklist_ko.md",
            exp_dir / "06_release/human_review_status_dashboard_ko.md",
            exp_dir / "05_review/human_review_status_next_actions.csv",
            exp_dir / "05_review/human_review_master_return_files.csv",
            Path("scripts/build_cape_annotation_return_field_guide.py"),
            Path("scripts/build_cape_human_return_error_playbook.py"),
            Path("scripts/run_cape_human_return_apply.sh"),
        ],
        "adjudicator": [
            exp_dir / "01_data/gold_annotation/adjudication_protocol.md",
            exp_dir / "01_data/gold_annotation/full_120/adjudication_draft.jsonl",
            exp_dir / "06_release/human_review_start_here_ko.md",
            exp_dir / "06_release/human_review_claim_gate_one_page_ko.md",
            exp_dir / "06_release/annotation_calibration_pack_ko.md",
            exp_dir / "06_release/annotation_calibration_pack.json",
            exp_dir / "06_release/annotation_return_field_guide_ko.md",
            exp_dir / "06_release/annotation_return_field_guide.json",
            exp_dir / "05_review/annotation_return_field_checklist.csv",
            exp_dir / "06_release/human_return_validation_error_playbook_ko.md",
            exp_dir / "06_release/human_return_validation_error_playbook.json",
            exp_dir / "05_review/human_return_validation_error_codes.csv",
            exp_dir / "05_review/annotation_calibration_examples.csv",
            exp_dir / "06_release/human_review_master_checklist_ko.md",
            exp_dir / "06_release/human_review_status_dashboard_ko.md",
            exp_dir / "05_review/human_review_status_next_actions.csv",
            exp_dir / "05_review/human_review_master_return_files.csv",
            Path("scripts/build_cape_annotation_return_field_guide.py"),
            Path("scripts/build_cape_human_return_error_playbook.py"),
            Path("scripts/run_cape_human_return_apply.sh"),
        ],
        "mapping_expert": [
            exp_dir / "01_data/mapping_review/mapping_review_protocol.md",
            exp_dir / "06_release/mapping_review_group_briefing.md",
            exp_dir / "05_review/mapping_review_group_briefing_top20.csv",
            exp_dir / "06_release/human_return_validation_error_playbook_ko.md",
            exp_dir / "06_release/human_return_validation_error_playbook.json",
            exp_dir / "05_review/human_return_validation_error_codes.csv",
            exp_dir / "06_release/human_review_claim_gate_one_page_ko.md",
            exp_dir / "06_release/human_review_master_checklist_ko.md",
            exp_dir / "06_release/human_review_status_dashboard_ko.md",
            exp_dir / "05_review/human_review_status_next_actions.csv",
            exp_dir / "05_review/human_review_master_return_files.csv",
            Path("scripts/build_cape_human_return_error_playbook.py"),
            Path("scripts/run_cape_human_return_apply.sh"),
        ],
        "crosswalk_expert": [
            exp_dir / "01_data/crosswalk_review/crosswalk_review_protocol.md",
            exp_dir / "01_data/crosswalk_review/crosswalk_review_items.jsonl",
            exp_dir / "01_data/crosswalk_review/crosswalk_review_sheet.csv",
            exp_dir / "01_data/crosswalk_review/crosswalk_review_manifest.json",
            exp_dir / "04_evaluation/ncs_pcf_crosswalk_report.md",
            exp_dir / "04_evaluation/ncs_pcf_crosswalk_candidates.csv",
            exp_dir / "04_evaluation/crosswalk_expert_evaluation_report.md",
            exp_dir / "06_release/human_return_validation_error_playbook_ko.md",
            exp_dir / "06_release/human_return_validation_error_playbook.json",
            exp_dir / "05_review/human_return_validation_error_codes.csv",
            exp_dir / "06_release/human_review_claim_gate_one_page_ko.md",
            exp_dir / "06_release/human_review_master_checklist_ko.md",
            exp_dir / "06_release/human_review_status_dashboard_ko.md",
            exp_dir / "05_review/human_review_status_next_actions.csv",
            exp_dir / "05_review/human_review_master_return_files.csv",
            Path("scripts/build_cape_human_return_error_playbook.py"),
            Path("scripts/run_cape_human_return_apply.sh"),
        ],
        "active_review_effort": [
            exp_dir / "06_release/active_review_human_effort_plan.md",
            exp_dir / "06_release/active_review_human_effort_briefing.md",
            exp_dir / "05_review/active_review_human_effort_briefing.csv",
            exp_dir / "05_review/active_review_human_effort_template.csv",
            exp_dir / "06_release/human_return_validation_error_playbook_ko.md",
            exp_dir / "06_release/human_return_validation_error_playbook.json",
            exp_dir / "05_review/human_return_validation_error_codes.csv",
            exp_dir / "06_release/human_review_claim_gate_one_page_ko.md",
            exp_dir / "06_release/human_review_master_checklist_ko.md",
            exp_dir / "06_release/human_review_status_dashboard_ko.md",
            exp_dir / "05_review/human_review_status_next_actions.csv",
            exp_dir / "05_review/human_review_master_return_files.csv",
            Path("scripts/build_cape_human_return_error_playbook.py"),
            Path("scripts/run_cape_human_return_apply.sh"),
        ],
        "structural_reviewer": [
            exp_dir / "06_release/structural_review_action_plan.md",
            exp_dir / "06_release/structural_review_return_preflight.md",
            exp_dir / "06_release/structural_review_application_plan.md",
            exp_dir / "05_review/structural_review_checkpoint_candidates.csv",
            exp_dir / "05_review/structural_gateway_branch_gaps.csv",
            exp_dir / "05_review/structural_review_optional_returns.csv",
            exp_dir / "05_review/structural_review_application_actions.csv",
            exp_dir / "06_release/human_return_validation_error_playbook_ko.md",
            exp_dir / "06_release/human_return_validation_error_playbook.json",
            exp_dir / "05_review/human_return_validation_error_codes.csv",
            exp_dir / "06_release/human_review_claim_gate_one_page_ko.md",
            exp_dir / "06_release/human_review_master_checklist_ko.md",
            exp_dir / "06_release/human_review_status_dashboard_ko.md",
            exp_dir / "05_review/human_review_status_next_actions.csv",
            exp_dir / "05_review/human_review_master_return_files.csv",
            Path("scripts/build_cape_human_return_error_playbook.py"),
            Path("scripts/run_cape_human_return_apply.sh"),
        ],
        "strong_resegmented_review": [
            exp_dir / "01_data/annotation_guideline_v1.md",
            exp_dir / "01_data/gold_annotation/adjudication_protocol.md",
            exp_dir / "01_data/gold_annotation/annotation_schema.json",
            exp_dir / "01_data/gold_annotation/annotation_expansion_manifest.json",
            exp_dir / "01_data/gold_annotation/annotation_expansion_report.md",
            exp_dir / "01_data/gold_annotation/strong_resegmented_342_max18/annotator_A.jsonl",
            exp_dir / "01_data/gold_annotation/strong_resegmented_342_max18/annotator_B.jsonl",
            exp_dir / "01_data/gold_annotation/strong_resegmented_342_max18/adjudication.jsonl",
            exp_dir / "01_data/gold_annotation/strong_resegmented_342_max18/adjudication_draft.jsonl",
            exp_dir / "01_data/gold_annotation/strong_resegmented_342_max18/tracking_sheet.csv",
            exp_dir / "01_data/gold_annotation/strong_resegmented_342_max18/strong_review_preview.csv",
            exp_dir / "01_data/gold_annotation/strong_resegmented_342_max18/strong_review_preview.md",
            exp_dir / "06_release/strong_resegmented_review_preview_summary.json",
            exp_dir / "06_release/strong_resegmented_review_preview_summary.md",
            exp_dir / "06_release/annotation_calibration_pack_ko.md",
            exp_dir / "06_release/annotation_calibration_pack.json",
            exp_dir / "06_release/annotation_return_field_guide_ko.md",
            exp_dir / "06_release/annotation_return_field_guide.json",
            exp_dir / "05_review/annotation_return_field_checklist.csv",
            exp_dir / "06_release/human_return_validation_error_playbook_ko.md",
            exp_dir / "06_release/human_return_validation_error_playbook.json",
            exp_dir / "05_review/human_return_validation_error_codes.csv",
            exp_dir / "05_review/annotation_calibration_examples.csv",
            exp_dir / "05_review/strong_resegmented_review_preview_summary.csv",
            exp_dir / "06_release/human_review_handoff/README_strong_resegmented_review_ko.md",
            exp_dir / "06_release/human_review_handoff/strong_resegmented_review_manifest.json",
            exp_dir / "06_release/human_review_start_here_ko.md",
            exp_dir / "06_release/human_review_claim_gate_one_page_ko.md",
            exp_dir / "06_release/human_review_master_checklist_ko.md",
            exp_dir / "06_release/human_review_status_dashboard_ko.md",
            exp_dir / "05_review/human_review_status_next_actions.csv",
            exp_dir / "05_review/human_review_master_return_files.csv",
            Path("scripts/import_cape_gold_annotation.py"),
            Path("scripts/build_cape_annotation_return_field_guide.py"),
            Path("scripts/build_cape_human_return_error_playbook.py"),
            Path("scripts/validate_cape_strong_review_returns.py"),
            Path("scripts/compute_cape_annotation_iaa.py"),
            Path("scripts/prepare_cape_adjudication_draft.py"),
            Path("scripts/run_cape_strong_return_apply.sh"),
            Path("scripts/run_cape_human_return_apply.sh"),
            Path("scripts/run_cape_post_annotation_refresh.sh"),
        ],
    }
    for bundle_name, expected_paths in expected_tar_members.items():
        bundle = bundles.get(bundle_name) or {}
        path = Path(bundle.get("path", ""))
        if not path.exists():
            issues.append({"bundle": bundle_name, "error": "missing_bundle", "path": rel(path)})
            continue
        try:
            with tarfile.open(path, "r:gz") as tar:
                names = set(tar.getnames())
        except Exception as exc:
            issues.append({"bundle": bundle_name, "error": "cannot_open_bundle", "path": rel(path), "detail": str(exc)})
            continue
        missing = [expected.as_posix() for expected in expected_paths if expected.as_posix() not in names]
        if missing:
            issues.append({"bundle": bundle_name, "error": "missing_guidance_in_bundle", "missing": missing})

    return_guidance_issues = []
    try:
        checked_field_guide = read_json(field_guide_json_path)
        checked_field_checklist_rows = read_csv_rows(field_guide_csv_path)
    except Exception as exc:
        return_guidance_issues.append(
            {
                "path": rel(field_guide_json_path),
                "error": "annotation_return_field_guide_unreadable",
                "detail": str(exc),
            }
        )
        checked_field_guide = {}
        checked_field_checklist_rows = []
    checked_editable_fields = set(checked_field_guide.get("editable_fields") or [])
    checked_missing_editable_fields = sorted(expected_editable_fields - checked_editable_fields)
    if checked_missing_editable_fields:
        return_guidance_issues.append(
            {
                "path": rel(field_guide_json_path),
                "error": "annotation_return_field_guide_missing_editable_fields",
                "missing": checked_missing_editable_fields,
            }
        )
    if checked_field_guide.get("claim_status") != "annotation_return_field_guide_ready_pending_human_returns":
        return_guidance_issues.append(
            {
                "path": rel(field_guide_json_path),
                "error": "annotation_return_field_guide_claim_status_unexpected",
                "actual": checked_field_guide.get("claim_status"),
            }
        )
    checked_field_rows_by_key = {
        (row.get("scope"), row.get("field")): row for row in checked_field_checklist_rows
    }
    required_return_field_rows = [
        ("top_level", "annotation_status"),
        ("top_level", "gold_edges"),
        ("top_level", "rejected_candidate_reference_ids"),
        ("gold_edges[]", "predicate"),
        ("gold_edges[]", "evidence_spans"),
    ]
    for scope, field in required_return_field_rows:
        if (scope, field) not in checked_field_rows_by_key:
            return_guidance_issues.append(
                {
                    "path": rel(field_guide_csv_path),
                    "error": "annotation_return_field_checklist_missing_row",
                    "scope": scope,
                    "field": field,
                }
            )

    try:
        checked_error_playbook = read_json(error_playbook_json_path)
        checked_error_code_rows = read_csv_rows(error_playbook_csv_path)
    except Exception as exc:
        return_guidance_issues.append(
            {
                "path": rel(error_playbook_json_path),
                "error": "human_return_validation_error_playbook_unreadable",
                "detail": str(exc),
            }
        )
        checked_error_playbook = {}
        checked_error_code_rows = []
    if checked_error_playbook.get("claim_status") != "human_return_error_playbook_ready_pending_human_returns":
        return_guidance_issues.append(
            {
                "path": rel(error_playbook_json_path),
                "error": "human_return_validation_error_playbook_claim_status_unexpected",
                "actual": checked_error_playbook.get("claim_status"),
            }
        )
    checked_error_codes = {row.get("error_code_or_pattern") for row in checked_error_code_rows}
    checked_missing_error_codes = sorted(expected_error_codes - checked_error_codes)
    if checked_missing_error_codes:
        return_guidance_issues.append(
            {
                "path": rel(error_playbook_csv_path),
                "error": "human_return_validation_error_playbook_missing_required_codes",
                "missing": checked_missing_error_codes,
            }
        )
    checked_error_scopes = {row.get("scope") for row in checked_error_code_rows}
    checked_missing_error_scopes = sorted(expected_error_scopes - checked_error_scopes)
    if checked_missing_error_scopes:
        return_guidance_issues.append(
            {
                "path": rel(error_playbook_csv_path),
                "error": "human_return_validation_error_playbook_missing_scopes",
                "missing": checked_missing_error_scopes,
            }
        )

    if return_guidance_issues:
        add_check(
            checks,
            "human_return_field_error_guidance",
            "FAIL",
            "Human-return field guide or validation error playbook is incomplete.",
            {"issues": return_guidance_issues},
        )
    else:
        add_check(
            checks,
            "human_return_field_error_guidance",
            "PASS",
            "Human-return field guide and validation error playbook are ready for annotators, adjudicators, experts, and coordinators.",
            {
                "field_guide_json": rel(field_guide_json_path),
                "field_checklist_csv": rel(field_guide_csv_path),
                "editable_fields": sorted(checked_editable_fields),
                "field_checklist_rows": len(checked_field_checklist_rows),
                "error_playbook_json": rel(error_playbook_json_path),
                "error_codes_csv": rel(error_playbook_csv_path),
                "error_code_rows": len(checked_error_code_rows),
                "error_scopes": sorted(checked_error_scopes),
                "claim_statuses": [
                    checked_field_guide.get("claim_status"),
                    checked_error_playbook.get("claim_status"),
                ],
            },
        )

    if issues:
        add_check(
            checks,
            "human_review_guidance_ready",
            "FAIL",
            "Human review guidance files or bundle inclusions are incomplete.",
            {"issues": issues},
        )
        return
    add_check(
        checks,
        "human_review_guidance_ready",
        "PASS",
        "Detailed annotation, adjudication, and mapping review guidance is present and included in handoff bundles.",
        {
            "guidance_files": [rel(path) for path in guidance_files],
            "checked_bundles": sorted(expected_tar_members),
            "instruction_safety_files": [
                rel(path) for path in sorted(instruction_safety_files, key=lambda item: item.as_posix())
            ],
            "wrapper_instruction_files": [
                rel(path) for path in sorted(wrapper_instruction_files, key=lambda item: item.as_posix())
            ],
            "banned_instruction_phrases_checked": len(banned_instruction_phrases),
            "portable_command_files_checked": len(portable_command_files),
            "pinned_python_patterns_checked": len(pinned_python_patterns),
        },
    )


def validate_annotation_batch_review_preview(checks, exp_dir):
    release_dir = exp_dir / "06_release"
    review_dir = exp_dir / "05_review"
    summary_path = release_dir / "annotation_batch_review_preview_summary.json"
    summary_md_path = release_dir / "annotation_batch_review_preview_summary.md"
    summary_csv_path = review_dir / "annotation_batch_review_preview_summary.csv"
    strong_summary_path = release_dir / "strong_resegmented_review_preview_summary.json"
    strong_summary_md_path = release_dir / "strong_resegmented_review_preview_summary.md"
    strong_summary_csv_path = review_dir / "strong_resegmented_review_preview_summary.csv"
    handoff_manifest_path = release_dir / "human_review_handoff/human_review_handoff_manifest.json"
    try:
        summary = read_json(summary_path)
        csv_rows = read_csv_rows(summary_csv_path)
        strong_summary = read_json(strong_summary_path)
        strong_csv_rows = read_csv_rows(strong_summary_csv_path)
        handoff = read_json(handoff_manifest_path)
    except Exception as exc:
        add_check(
            checks,
            "annotation_batch_review_preview",
            "FAIL",
            "Annotation batch review preview artifacts cannot be read.",
            {"error": str(exc), "path": rel(summary_path)},
        )
        return

    issues = []
    if summary.get("claim_status") != "annotation_batch_review_preview_ready_not_gold_evidence":
        issues.append({"error": "unexpected_claim_status", "actual": summary.get("claim_status")})
    if summary.get("batch_count") != 5:
        issues.append({"error": "batch_count_mismatch", "actual": summary.get("batch_count")})
    if summary.get("chunk_count") != 100:
        issues.append({"error": "chunk_count_mismatch", "actual": summary.get("chunk_count")})
    if int(summary.get("candidate_edges_total") or 0) <= 0:
        issues.append({"error": "candidate_edges_total_not_positive", "actual": summary.get("candidate_edges_total")})
    if len(csv_rows) != 5:
        issues.append({"error": "summary_csv_row_count_mismatch", "actual": len(csv_rows)})
    if not summary_md_path.exists():
        issues.append({"error": "missing_summary_markdown", "path": rel(summary_md_path)})
    else:
        text = summary_md_path.read_text(encoding="utf-8")
        for pattern in [
            "Annotation Batch Review Preview Summary",
            "annotation_batch_review_preview_ready_not_gold_evidence",
            "gold annotation 결과가 아니라",
        ]:
            if pattern not in text:
                issues.append({"error": "missing_summary_markdown_pattern", "pattern": pattern})

    if strong_summary.get("claim_status") != "strong_resegmented_review_preview_ready_not_gold_evidence":
        issues.append({"error": "unexpected_strong_claim_status", "actual": strong_summary.get("claim_status")})
    if strong_summary.get("package_id") != "strong_resegmented_342_max18":
        issues.append({"error": "strong_package_id_mismatch", "actual": strong_summary.get("package_id")})
    if strong_summary.get("review_unit_count") != 342:
        issues.append({"error": "strong_review_unit_count_mismatch", "actual": strong_summary.get("review_unit_count")})
    if int(strong_summary.get("candidate_edges_total") or 0) <= 0:
        issues.append({"error": "strong_candidate_edges_total_not_positive", "actual": strong_summary.get("candidate_edges_total")})
    if len(strong_csv_rows) != 1:
        issues.append({"error": "strong_summary_csv_row_count_mismatch", "actual": len(strong_csv_rows)})
    if not strong_summary_md_path.exists():
        issues.append({"error": "missing_strong_summary_markdown", "path": rel(strong_summary_md_path)})
    else:
        strong_text = strong_summary_md_path.read_text(encoding="utf-8")
        for pattern in [
            "Strong Resegmented Review Preview Summary",
            "strong_resegmented_review_preview_ready_not_gold_evidence",
            "gold annotation 결과가 아니라",
        ]:
            if pattern not in strong_text:
                issues.append({"error": "missing_strong_summary_markdown_pattern", "pattern": pattern})
    strong_preview_csv = Path(strong_summary.get("package_preview_csv", ""))
    strong_preview_md = Path(strong_summary.get("package_preview_md", ""))
    if not strong_preview_csv.exists():
        issues.append({"error": "missing_strong_package_preview_csv", "path": rel(strong_preview_csv)})
    else:
        try:
            strong_preview_rows = read_csv_rows(strong_preview_csv)
            if len(strong_preview_rows) != 342:
                issues.append({"error": "strong_package_preview_row_count_mismatch", "actual": len(strong_preview_rows)})
        except Exception as exc:
            issues.append({"error": "cannot_read_strong_package_preview_csv", "detail": str(exc)})
    if not strong_preview_md.exists():
        issues.append({"error": "missing_strong_package_preview_markdown", "path": rel(strong_preview_md)})
    else:
        strong_preview_text = strong_preview_md.read_text(encoding="utf-8")
        for pattern in ["Strong Review Preview", "dense candidate pruning", "evidence span repair", "missing-edge scan"]:
            if pattern not in strong_preview_text:
                issues.append({"error": "missing_strong_package_preview_pattern", "pattern": pattern})

    for batch in summary.get("batches") or []:
        batch_id = batch.get("batch_id")
        preview_csv = Path(batch.get("preview_csv", ""))
        preview_md = Path(batch.get("preview_md", ""))
        if not batch_id:
            issues.append({"error": "missing_batch_id"})
            continue
        if not preview_csv.exists():
            issues.append({"error": "missing_batch_preview_csv", "batch_id": batch_id, "path": rel(preview_csv)})
            continue
        try:
            preview_rows = read_csv_rows(preview_csv)
        except Exception as exc:
            issues.append({"error": "cannot_read_batch_preview_csv", "batch_id": batch_id, "detail": str(exc)})
            continue
        if len(preview_rows) != 20:
            issues.append({"error": "batch_preview_row_count_mismatch", "batch_id": batch_id, "actual": len(preview_rows)})
        if not preview_md.exists():
            issues.append({"error": "missing_batch_preview_markdown", "batch_id": batch_id, "path": rel(preview_md)})
        else:
            md_text = preview_md.read_text(encoding="utf-8")
            for pattern in ["Review Preview", "dense candidate pruning", "evidence span repair", "missing-edge scan"]:
                if pattern not in md_text:
                    issues.append({"error": "missing_batch_preview_pattern", "batch_id": batch_id, "pattern": pattern})

    bundles = handoff.get("bundles") or {}
    for bundle_name in ["annotator_A", "annotator_B", "coordinator"]:
        bundle = bundles.get(bundle_name) or {}
        path = Path(bundle.get("path", ""))
        if not path.exists():
            issues.append({"error": "missing_handoff_bundle_for_preview_check", "bundle": bundle_name, "path": rel(path)})
            continue
        try:
            with tarfile.open(path, "r:gz") as tar:
                names = set(tar.getnames())
        except Exception as exc:
            issues.append({"error": "cannot_read_handoff_bundle_for_preview_check", "bundle": bundle_name, "detail": str(exc)})
            continue
        required_fragments = [
            "annotation_batch_review_preview_summary.md",
            "annotation_batch_review_preview_summary.json",
            "annotation_batch_review_preview_summary.csv",
            "batch_review_preview.md",
            "batch_review_preview.csv",
            "build_cape_annotation_batch_review_preview.py",
        ]
        for fragment in required_fragments:
            if not any(fragment in name for name in names):
                issues.append({"error": "preview_artifact_missing_from_bundle", "bundle": bundle_name, "fragment": fragment})

    strong_bundle = (bundles.get("strong_resegmented_review") or {})
    strong_bundle_path = Path(strong_bundle.get("path", ""))
    if not strong_bundle_path.exists():
        issues.append({"error": "missing_strong_handoff_bundle_for_preview_check", "path": rel(strong_bundle_path)})
    else:
        try:
            with tarfile.open(strong_bundle_path, "r:gz") as tar:
                strong_names = set(tar.getnames())
        except Exception as exc:
            issues.append({"error": "cannot_read_strong_handoff_bundle_for_preview_check", "detail": str(exc)})
            strong_names = set()
        for fragment in [
            "strong_resegmented_review_preview_summary.md",
            "strong_resegmented_review_preview_summary.json",
            "strong_resegmented_review_preview_summary.csv",
            "strong_review_preview.md",
            "strong_review_preview.csv",
            "build_cape_annotation_batch_review_preview.py",
        ]:
            if not any(fragment in name for name in strong_names):
                issues.append({"error": "strong_preview_artifact_missing_from_bundle", "fragment": fragment})

    if issues:
        add_check(
            checks,
            "annotation_batch_review_preview",
            "FAIL",
            "Annotation batch review preview artifacts are missing or inconsistent.",
            {"path": rel(summary_path), "issues": issues[:50]},
        )
        return

    add_check(
        checks,
        "annotation_batch_review_preview",
        "PASS",
        "Annotation candidate/span preview artifacts cover priority-100 chunks and the optional strong 342-unit package, and are included in handoff bundles.",
        {
            "path": rel(summary_path),
            "markdown": rel(summary_md_path),
            "csv": rel(summary_csv_path),
            "strong_path": rel(strong_summary_path),
            "strong_markdown": rel(strong_summary_md_path),
            "strong_csv": rel(strong_summary_csv_path),
            "batch_count": summary.get("batch_count"),
            "chunk_count": summary.get("chunk_count"),
            "candidate_edges_total": summary.get("candidate_edges_total"),
            "exact_component_ratio": summary.get("exact_component_ratio"),
            "chunks_needing_span_attention": summary.get("chunks_needing_span_attention"),
            "strong_review_unit_count": strong_summary.get("review_unit_count"),
            "strong_candidate_edges_total": strong_summary.get("candidate_edges_total"),
            "strong_chunks_needing_span_attention": strong_summary.get("chunks_needing_span_attention"),
        },
    )


def validate_gold_sampling_coverage_report(checks, exp_dir):
    release_dir = exp_dir / "06_release"
    review_dir = exp_dir / "05_review"
    json_path = release_dir / "gold_sampling_coverage_report.json"
    md_path = release_dir / "gold_sampling_coverage_report.md"
    chapter_csv_path = review_dir / "gold_sampling_coverage_by_chapter.csv"
    selected_csv_path = review_dir / "gold_sampling_priority100_selected_chunks.csv"
    try:
        payload = read_json(json_path)
        chapter_rows = read_csv_rows(chapter_csv_path)
        selected_rows = read_csv_rows(selected_csv_path)
    except Exception as exc:
        add_check(
            checks,
            "gold_sampling_coverage_report",
            "FAIL",
            "Gold subset sampling coverage artifacts cannot be read.",
            {"error": str(exc), "path": rel(json_path)},
        )
        return

    issues = []
    expected_status = "gold_sampling_coverage_ready_pending_human_review"
    if payload.get("claim_status") != expected_status:
        issues.append({"error": "unexpected_claim_status", "actual": payload.get("claim_status")})

    policy = payload.get("selection_policy") or {}
    if policy.get("minimum_gate_target_chunks") != 100:
        issues.append({"error": "minimum_gate_target_mismatch", "actual": policy.get("minimum_gate_target_chunks")})
    if policy.get("selected_chunk_count") != 100:
        issues.append({"error": "selected_chunk_count_mismatch", "actual": policy.get("selected_chunk_count")})
    boundary = str(policy.get("not_gold_until") or "")
    for pattern in ["two annotators", "IAA", "adjudication"]:
        if pattern not in boundary:
            issues.append({"error": "claim_boundary_missing_pattern", "pattern": pattern})

    packages = {row.get("label"): row for row in payload.get("packages") or []}
    expected_counts = {
        "source_layer2_chunks": 214,
        "full_120_gold_package": 120,
        "priority_100_assigned": 100,
        "remaining_20_in_full_120": 20,
        "all_available_214_optional": 214,
    }
    for label, expected in expected_counts.items():
        actual = (packages.get(label) or {}).get("chunk_count")
        if actual != expected:
            issues.append({"error": "package_chunk_count_mismatch", "label": label, "expected": expected, "actual": actual})
    strong_packages = [
        row for label, row in packages.items()
        if str(label or "").endswith("_optional_strong")
    ]
    if not strong_packages:
        issues.append({"error": "missing_optional_strong_package"})
    else:
        strong_count = int(strong_packages[0].get("chunk_count") or 0)
        if strong_count < 300:
            issues.append({"error": "optional_strong_package_too_small", "actual": strong_count})

    summary = payload.get("coverage_summary") or {}
    candidate_coverage = float(summary.get("priority_100_candidate_edge_coverage_of_full120") or 0.0)
    active_coverage = float(summary.get("priority_100_active_review_chunk_coverage_of_full120") or 0.0)
    high_impact_coverage = float(summary.get("priority_100_high_impact_chunk_coverage_of_full120") or 0.0)
    if candidate_coverage < 0.90:
        issues.append({"error": "candidate_edge_coverage_too_low", "actual": candidate_coverage})
    if active_coverage < 0.90:
        issues.append({"error": "active_review_coverage_too_low", "actual": active_coverage})
    if high_impact_coverage < 0.90:
        issues.append({"error": "high_impact_coverage_too_low", "actual": high_impact_coverage})
    if int(summary.get("priority_100_candidate_edges") or 0) <= 0:
        issues.append({"error": "priority_candidate_edges_not_positive", "actual": summary.get("priority_100_candidate_edges")})

    if len(selected_rows) != 100:
        issues.append({"error": "selected_csv_row_count_mismatch", "expected": 100, "actual": len(selected_rows)})
    if len(chapter_rows) < 5:
        issues.append({"error": "chapter_csv_too_sparse", "actual": len(chapter_rows)})
    if not md_path.exists():
        issues.append({"error": "missing_markdown", "path": rel(md_path)})
    else:
        text = md_path.read_text(encoding="utf-8")
        for pattern in [
            "Gold Subset Sampling and Coverage Report",
            "Selection Policy",
            "Coverage Summary",
            "not_gold_until",
            "pre-human sampling evidence",
        ]:
            if pattern not in text:
                issues.append({"error": "missing_markdown_pattern", "pattern": pattern})

    if issues:
        add_check(
            checks,
            "gold_sampling_coverage_report",
            "FAIL",
            "Gold subset sampling coverage report is missing or inconsistent.",
            {"path": rel(json_path), "issues": issues[:50]},
        )
        return

    add_check(
        checks,
        "gold_sampling_coverage_report",
        "PASS",
        "Gold subset sampling coverage report explains the priority-100 minimum annotation subset while keeping human-gold claims pending.",
        {
            "json": rel(json_path),
            "markdown": rel(md_path),
            "chapter_csv": rel(chapter_csv_path),
            "selected_chunks_csv": rel(selected_csv_path),
            "candidate_coverage": candidate_coverage,
            "active_review_coverage": active_coverage,
            "high_impact_coverage": high_impact_coverage,
            "selected_chunks": policy.get("selected_chunk_count"),
        },
    )


def validate_gold_item_feasibility_report(checks, exp_dir):
    release_dir = exp_dir / "06_release"
    review_dir = exp_dir / "05_review"
    json_path = release_dir / "gold_item_feasibility_report.json"
    md_path = release_dir / "gold_item_feasibility_report.md"
    csv_path = review_dir / "gold_item_feasibility_by_batch.csv"
    assignment_path = release_dir / "annotation_batch_assignment_summary.json"
    human_gold_path = exp_dir / "04_evaluation/human_gold_validation_summary.json"
    try:
        payload = read_json(json_path)
        rows = read_csv_rows(csv_path)
        assignment = read_json(assignment_path)
        human_gold = read_json(human_gold_path)
    except Exception as exc:
        add_check(
            checks,
            "gold_item_feasibility_report",
            "FAIL",
            "Gold item feasibility artifacts cannot be read.",
            {"error": str(exc), "path": rel(json_path)},
        )
        return

    issues = []
    expected_status = "gold_item_feasibility_ready_pending_human_adjudication"
    if payload.get("claim_status") != expected_status:
        issues.append({"error": "unexpected_claim_status", "actual": payload.get("claim_status")})

    target = payload.get("target") or {}
    if target.get("minimum_required_chunks") != 100:
        issues.append({"error": "minimum_required_chunks_mismatch", "actual": target.get("minimum_required_chunks")})
    if target.get("minimum_required_gold_items") != 500:
        issues.append({"error": "minimum_required_gold_items_mismatch", "actual": target.get("minimum_required_gold_items")})

    current = payload.get("current_human_gold_status") or {}
    if int(current.get("completed_adjudicated_chunks") or 0) != int(human_gold.get("completed_adjudicated_chunks") or 0):
        issues.append({
            "error": "completed_chunks_not_synced",
            "actual": current.get("completed_adjudicated_chunks"),
            "source": human_gold.get("completed_adjudicated_chunks"),
        })
    if int(current.get("gold_item_count_for_readiness") or 0) != int(human_gold.get("gold_item_count_for_readiness") or 0):
        issues.append({
            "error": "gold_item_count_not_synced",
            "actual": current.get("gold_item_count_for_readiness"),
            "source": human_gold.get("gold_item_count_for_readiness"),
        })
    if current.get("human_gold_gate_satisfied") is not False:
        issues.append({"error": "human_gold_gate_should_remain_false_pre_human", "actual": current.get("human_gold_gate_satisfied")})

    pool = payload.get("candidate_pool_summary") or {}
    assigned_chunks = int(pool.get("assigned_chunks") or 0)
    candidate_edges = int(pool.get("candidate_edges_total") or 0)
    if assigned_chunks != int(assignment.get("assigned_chunks") or 0):
        issues.append({"error": "assigned_chunks_not_synced", "actual": assigned_chunks, "source": assignment.get("assigned_chunks")})
    if assigned_chunks < 100:
        issues.append({"error": "assigned_chunks_below_minimum", "actual": assigned_chunks})
    if candidate_edges < 500:
        issues.append({"error": "candidate_edges_below_500_proxy", "actual": candidate_edges})
    if pool.get("candidate_pool_sufficient_for_minimum_item_target") is not True:
        issues.append({
            "error": "candidate_pool_not_marked_sufficient",
            "actual": pool.get("candidate_pool_sufficient_for_minimum_item_target"),
        })
    if not pool.get("first_batch_meeting_500_candidate_proxy"):
        issues.append({"error": "missing_first_batch_meeting_500_proxy"})
    if not pool.get("minimum_batch_meeting_100_chunks_and_500_candidate_proxy"):
        issues.append({"error": "missing_minimum_ready_batch"})

    json_batch_rows = payload.get("batch_rows") or []
    if len(json_batch_rows) != int(assignment.get("batch_count") or 0):
        issues.append({"error": "json_batch_count_mismatch", "actual": len(json_batch_rows), "source": assignment.get("batch_count")})
    if len(rows) != int(assignment.get("batch_count") or 0):
        issues.append({"error": "csv_batch_count_mismatch", "actual": len(rows), "source": assignment.get("batch_count")})
    if json_batch_rows:
        final_row = json_batch_rows[-1]
        if int(final_row.get("cumulative_chunks") or 0) != assigned_chunks:
            issues.append({"error": "final_cumulative_chunks_mismatch", "actual": final_row.get("cumulative_chunks"), "expected": assigned_chunks})
        if int(final_row.get("cumulative_candidate_edges") or 0) != candidate_edges:
            issues.append({"error": "final_cumulative_candidate_edges_mismatch", "actual": final_row.get("cumulative_candidate_edges"), "expected": candidate_edges})
        if final_row.get("meets_minimum_chunk_and_candidate_proxy") is not True:
            issues.append({"error": "final_batch_should_meet_minimum_proxy"})

    boundary = payload.get("claim_boundary") or {}
    if boundary.get("candidate_edges_are_not_gold_items") is not True:
        issues.append({"error": "claim_boundary_candidate_gold_distinction_missing"})
    boundary_text = " ".join(str(boundary.get(key) or "") for key in ["not_claimable_until", "safe_interpretation"])
    for pattern in ["two annotators", "IAA", "adjudication", "gold_item_count_for_readiness >= 500"]:
        if pattern not in boundary_text:
            issues.append({"error": "claim_boundary_missing_pattern", "pattern": pattern})

    if not md_path.exists():
        issues.append({"error": "missing_markdown", "path": rel(md_path)})
    else:
        text = md_path.read_text(encoding="utf-8")
        for pattern in [
            "Gold Item Feasibility Report",
            "pre-human feasibility artifact",
            "Candidate edges are not gold items",
            "Human-gold gate satisfied",
        ]:
            if pattern not in text:
                issues.append({"error": "missing_markdown_pattern", "pattern": pattern})

    if issues:
        add_check(
            checks,
            "gold_item_feasibility_report",
            "FAIL",
            "Gold item feasibility report is missing, stale, or claim-unsafe.",
            {"path": rel(json_path), "issues": issues[:50]},
        )
        return

    add_check(
        checks,
        "gold_item_feasibility_report",
        "PASS",
        "Gold item feasibility report shows the priority-100 candidate pool can cover the 500-item target while keeping human-gold claims pending.",
        {
            "json": rel(json_path),
            "markdown": rel(md_path),
            "batch_csv": rel(csv_path),
            "assigned_chunks": assigned_chunks,
            "candidate_edges": candidate_edges,
            "current_gold_items": current.get("gold_item_count_for_readiness"),
            "claim_status": payload.get("claim_status"),
        },
    )


def validate_neo4j_reports(checks, outputs_dir):
    report_paths = [
        outputs_dir / "11_neo4j_import_flat/neo4j_csv_validation_report.json",
        outputs_dir / "11_neo4j_import/neo4j_csv_validation_report.json",
    ]
    evidence_summary_path = outputs_dir / "13_evidence_graph/evidence_graph_projection_summary.json"
    issues = []
    summaries = []
    try:
        evidence_summary = read_json(evidence_summary_path)
    except Exception as exc:
        evidence_summary = {}
        issues.append({"path": rel(evidence_summary_path), "error": "cannot_read_evidence_projection_summary", "detail": str(exc)})
    for path in report_paths:
        try:
            report = read_json(path)
        except Exception as exc:
            issues.append({"path": rel(path), "error": str(exc)})
            continue
        issue_count = int(report.get("issue_count") or len(report.get("issues") or []))
        manifest = report.get("manifest") or {}
        relationship_types = manifest.get("relationship_types") or {}
        summaries.append(
            {
                "path": rel(path),
                "overall_status": report.get("overall_status"),
                "csv_file_count": report.get("csv_file_count"),
                "total_rows": report.get("total_rows"),
                "issue_count": issue_count,
                "node_count": manifest.get("node_count"),
                "relationship_count": manifest.get("relationship_count"),
                "evidence_anchor_node_count": manifest.get("evidence_anchor_node_count"),
                "kg_edge_assertion_node_count": manifest.get("kg_edge_assertion_node_count"),
                "evidenced_by_relationship_count": relationship_types.get("EVIDENCED_BY"),
            }
        )
        if report.get("overall_status") != "PASS" or issue_count != 0:
            issues.append({"path": rel(path), "summary": summaries[-1]})
        expected_evidence_anchors = evidence_summary.get("evidence_anchor_node_count")
        expected_evidenced_by = evidence_summary.get("evidenced_by_edge_count")
        expected_kg_edge_assertions = evidence_summary.get("layer2_edge_count")
        if expected_evidence_anchors is not None and manifest.get("evidence_anchor_node_count") != expected_evidence_anchors:
            issues.append(
                {
                    "path": rel(path),
                    "error": "neo4j_evidence_anchor_node_count_mismatch",
                    "expected": expected_evidence_anchors,
                    "actual": manifest.get("evidence_anchor_node_count"),
                }
            )
        if expected_evidenced_by is not None and relationship_types.get("EVIDENCED_BY") != expected_evidenced_by:
            issues.append(
                {
                    "path": rel(path),
                    "error": "neo4j_evidenced_by_relationship_count_mismatch",
                    "expected": expected_evidenced_by,
                    "actual": relationship_types.get("EVIDENCED_BY"),
                }
            )
        if expected_kg_edge_assertions is not None and manifest.get("kg_edge_assertion_node_count") != expected_kg_edge_assertions:
            issues.append(
                {
                    "path": rel(path),
                    "error": "neo4j_kg_edge_assertion_node_count_mismatch",
                    "expected": expected_kg_edge_assertions,
                    "actual": manifest.get("kg_edge_assertion_node_count"),
                }
            )
    if issues:
        add_check(checks, "neo4j_csv_validation", "FAIL", "Neo4j CSV validation reports contain issues.", {"issues": issues, "summaries": summaries})
    else:
        add_check(checks, "neo4j_csv_validation", "PASS", "Neo4j CSV validation reports passed and include the EvidenceAnchor/EVIDENCED_BY projection.", {"summaries": summaries})


def validate_neo4j_evidence_query_pack(checks, exp_dir, outputs_dir):
    release_dir = Path(exp_dir) / "06_release"
    json_path = release_dir / "neo4j_evidence_query_pack.json"
    md_path = release_dir / "neo4j_evidence_query_pack.md"
    cypher_path = Path(outputs_dir) / "11_neo4j_import_flat/neo4j_evidence_queries.cypher"
    manifest_path = Path(outputs_dir) / "11_neo4j_import_flat/manifest.json"
    validation_path = Path(outputs_dir) / "11_neo4j_import_flat/neo4j_csv_validation_report.json"
    evidence_summary_path = Path(outputs_dir) / "13_evidence_graph/evidence_graph_projection_summary.json"
    try:
        pack = read_json(json_path)
        manifest = read_json(manifest_path)
        validation = read_json(validation_path)
        evidence_summary = read_json(evidence_summary_path)
        md_text = md_path.read_text(encoding="utf-8")
        cypher_text = cypher_path.read_text(encoding="utf-8")
    except Exception as exc:
        add_check(
            checks,
            "neo4j_evidence_query_pack",
            "FAIL",
            "Neo4j evidence query pack files cannot be read.",
            {"error": str(exc), "path": rel(json_path)},
        )
        return

    issues = []
    summary = pack.get("summary") or {}
    queries = pack.get("queries") or []
    relationship_types = manifest.get("relationship_types") or {}
    expected_summary = {
        "neo4j_node_count": manifest.get("node_count"),
        "neo4j_relationship_count": manifest.get("relationship_count"),
        "neo4j_validation_status": validation.get("overall_status"),
        "evidence_anchor_node_count": manifest.get("evidence_anchor_node_count"),
        "kg_edge_assertion_node_count": manifest.get("kg_edge_assertion_node_count"),
        "evidenced_by_relationship_count": relationship_types.get("EVIDENCED_BY"),
        "layer2_node_count": evidence_summary.get("layer2_node_count"),
        "layer2_edge_count": evidence_summary.get("layer2_edge_count"),
        "source_text_included": evidence_summary.get("source_text_included"),
    }
    for key, expected in expected_summary.items():
        if summary.get(key) != expected:
            issues.append({"error": "summary_mismatch", "field": key, "expected": expected, "actual": summary.get(key)})

    query_ids = [row.get("query_id") for row in queries]
    expected_query_ids = [f"NQ{i:02d}" for i in range(1, 14)]
    if query_ids != expected_query_ids:
        issues.append({"error": "query_id_order_mismatch", "expected": expected_query_ids, "actual": query_ids})
    if pack.get("claim_status") != "neo4j_evidence_query_pack_ready_not_human_gold_evidence":
        issues.append({"error": "unexpected_claim_status", "actual": pack.get("claim_status")})
    if summary.get("query_count") != len(queries) or len(queries) < 12:
        issues.append({"error": "query_count_mismatch", "summary": summary.get("query_count"), "actual": len(queries)})
    if not any("CQ10" in (row.get("source_cq_ids") or []) for row in queries):
        issues.append({"error": "missing_cq10_evidence_query"})

    for pattern in [
        "EvidenceAnchor",
        "KGEdgeAssertion",
        "EVIDENCED_BY",
        "source_text_included",
        "NQ01",
        "NQ13",
    ]:
        if pattern not in cypher_text and pattern not in md_text:
            issues.append({"error": "missing_query_pack_pattern", "pattern": pattern})
    for query_id in expected_query_ids:
        if query_id not in cypher_text:
            issues.append({"error": "query_missing_from_cypher", "query_id": query_id})
    if "Human-gold correctness" not in md_text:
        issues.append({"error": "markdown_missing_claim_boundary_language"})

    if issues:
        add_check(
            checks,
            "neo4j_evidence_query_pack",
            "FAIL",
            "Neo4j evidence query pack is missing, stale, or inconsistent with current Neo4j/evidence manifests.",
            {"path": rel(json_path), "issues": issues[:60]},
        )
        return

    add_check(
        checks,
        "neo4j_evidence_query_pack",
        "PASS",
        "Neo4j evidence query pack is synchronized with the current EvidenceAnchor/EVIDENCED_BY import package.",
        {
            "json": rel(json_path),
            "markdown": rel(md_path),
            "cypher": rel(cypher_path),
            "query_count": len(queries),
            "evidenced_by_relationship_count": summary.get("evidenced_by_relationship_count"),
            "claim_status": pack.get("claim_status"),
        },
    )


def validate_kg_visualization_demo(checks, outputs_dir):
    vis_dir = outputs_dir / "09_visualization"
    graph_json_path = vis_dir / "kg_full.json"
    viewer_path = vis_dir / "kg_viewer.html"
    graphml_path = vis_dir / "kg_full.graphml"
    svg_path = vis_dir / "kg_static_overview.svg"
    readme_path = vis_dir / "visualization_readme.md"
    layer2_nodes_path = outputs_dir / "07_layer2_graph/layer2_nodes.jsonl"
    layer2_edges_path = outputs_dir / "07_layer2_graph/layer2_edges.jsonl"
    evidence_path = outputs_dir / "06_triples/evidence_anchors.jsonl"
    issues = []
    evidence = {}

    for path in [graph_json_path, viewer_path, graphml_path, svg_path, readme_path]:
        if not path.exists():
            issues.append({"error": "missing_visualization_artifact", "path": rel(path)})
        elif path.stat().st_size == 0:
            issues.append({"error": "empty_visualization_artifact", "path": rel(path)})
    if issues:
        add_check(
            checks,
            "kg_visualization_demo",
            "FAIL",
            "KG visualization/demo artifacts are missing.",
            {"issues": issues},
        )
        return

    try:
        graph = read_json(graph_json_path)
    except Exception as exc:
        add_check(
            checks,
            "kg_visualization_demo",
            "FAIL",
            "KG visualization graph JSON cannot be read.",
            {"path": rel(graph_json_path), "error": str(exc)},
        )
        return

    nodes = graph.get("nodes") or []
    edges = graph.get("edges") or []
    evidence_index = graph.get("evidence_index") or []
    layer2_nodes = [row for row in nodes if row.get("layer") == "Layer2"]
    layer2_edges = [row for row in edges if row.get("layer") == "Layer2"]
    mapping_edges = [row for row in edges if row.get("layer") == "Mapping"]
    mapping_predicates = {str(row.get("predicate") or "") for row in mapping_edges}
    node_ids = {row.get("id") for row in nodes}

    try:
        expected_layer2_nodes = len(read_jsonl(layer2_nodes_path))
        expected_layer2_edges = len(read_jsonl(layer2_edges_path))
        expected_evidence = len(read_jsonl(evidence_path))
    except Exception as exc:
        issues.append({"error": "cannot_read_source_graph_counts", "detail": str(exc)})
        expected_layer2_nodes = expected_layer2_edges = expected_evidence = None

    if expected_layer2_nodes is not None and len(layer2_nodes) != expected_layer2_nodes:
        issues.append(
            {
                "error": "layer2_node_count_mismatch",
                "expected": expected_layer2_nodes,
                "actual": len(layer2_nodes),
            }
        )
    if expected_layer2_edges is not None and len(layer2_edges) != expected_layer2_edges:
        issues.append(
            {
                "error": "layer2_edge_count_mismatch",
                "expected": expected_layer2_edges,
                "actual": len(layer2_edges),
            }
        )
    if expected_evidence is not None and len(evidence_index) != expected_evidence:
        issues.append(
            {
                "error": "evidence_index_count_mismatch",
                "expected": expected_evidence,
                "actual": len(evidence_index),
            }
        )

    dangling = [
        {"source": row.get("source"), "target": row.get("target"), "predicate": row.get("predicate")}
        for row in edges
        if row.get("source") not in node_ids or row.get("target") not in node_ids
    ]
    if dangling:
        issues.append({"error": "visualization_graph_has_dangling_edges", "count": len(dangling), "examples": dangling[:10]})
    if not mapping_edges:
        issues.append({"error": "visualization_mapping_edges_missing"})
    legacy_mapping_predicates = {
        "CANDIDATE_REQUIRES_CAPABILITY",
        "CANDIDATE_PROCESS_CONTEXT",
        "REQUIRESCAPABILITY",
        "PROCESSCONTEXT",
    }
    legacy_hits = sorted(mapping_predicates & legacy_mapping_predicates)
    if legacy_hits:
        issues.append({"error": "visualization_mapping_predicates_not_cape_schema", "predicates": legacy_hits})
    expected_mapping_predicates = {"REQUIRES_CAPABILITY", "PROCESS_CONTEXT"}
    missing_mapping_predicates = sorted(expected_mapping_predicates - mapping_predicates)
    if missing_mapping_predicates:
        issues.append(
            {
                "error": "visualization_mapping_predicates_missing",
                "expected": sorted(expected_mapping_predicates),
                "missing": missing_mapping_predicates,
                "actual": sorted(mapping_predicates),
            }
        )

    try:
        viewer_text = viewer_path.read_text(encoding="utf-8", errors="replace")
        for pattern in [
            "AX-EPAK KG Viewer",
            "const graph =",
            "graph.nodes",
            "graph.edges",
            "evidence_index",
            "All predicates",
            "canvas",
        ]:
            if pattern not in viewer_text:
                issues.append({"error": "viewer_missing_pattern", "pattern": pattern})
    except Exception as exc:
        issues.append({"error": "cannot_read_viewer_html", "detail": str(exc)})

    try:
        readme_text = readme_path.read_text(encoding="utf-8", errors="replace")
        for pattern in ["serve_kg_viewer.sh", "kg_viewer.html", "kg_full.json", "kg_full.graphml"]:
            if pattern not in readme_text:
                issues.append({"error": "visualization_readme_missing_pattern", "pattern": pattern})
    except Exception as exc:
        issues.append({"error": "cannot_read_visualization_readme", "detail": str(exc)})

    try:
        graphml_head = graphml_path.read_text(encoding="utf-8", errors="replace")[:20000]
        if "<graphml" not in graphml_head or "<graph" not in graphml_head or "<node" not in graphml_head:
            issues.append({"error": "graphml_missing_expected_markup"})
    except Exception as exc:
        issues.append({"error": "cannot_read_graphml", "detail": str(exc)})

    try:
        svg_head = svg_path.read_text(encoding="utf-8", errors="replace")[:5000]
        if "<svg" not in svg_head:
            issues.append({"error": "svg_missing_svg_markup"})
    except Exception as exc:
        issues.append({"error": "cannot_read_static_svg", "detail": str(exc)})

    evidence = {
        "viewer": rel(viewer_path),
        "graph_json": rel(graph_json_path),
        "graphml": rel(graphml_path),
        "static_svg": rel(svg_path),
        "readme": rel(readme_path),
        "nodes": len(nodes),
        "edges": len(edges),
        "layer2_nodes": len(layer2_nodes),
        "layer2_edges": len(layer2_edges),
        "mapping_edges": len(mapping_edges),
        "mapping_predicates": sorted(mapping_predicates),
        "evidence_index": len(evidence_index),
        "viewer_bytes": viewer_path.stat().st_size,
    }
    if issues:
        add_check(
            checks,
            "kg_visualization_demo",
            "FAIL",
            "KG visualization/demo artifacts are not synchronized with current graph outputs.",
            {**evidence, "issues": issues[:80]},
        )
        return
    add_check(
        checks,
        "kg_visualization_demo",
        "PASS",
        "KG visualization/demo artifacts are present and synchronized with current Layer 2 graph counts.",
        evidence,
    )


def validate_roundtrip_smoke(checks, exp_dir):
    smoke_path = exp_dir / "06_release/annotation_roundtrip_smoke/roundtrip_smoke_summary.json"
    try:
        smoke = read_json(smoke_path)
    except Exception as exc:
        add_check(
            checks,
            "annotation_roundtrip_smoke",
            "FAIL",
            "Annotation roundtrip smoke summary cannot be read.",
            {"path": rel(smoke_path), "error": str(exc)},
        )
        return
    if smoke.get("overall_status") != "PASS":
        add_check(
            checks,
            "annotation_roundtrip_smoke",
            "FAIL",
            "Annotation roundtrip smoke did not pass.",
            {
                "path": rel(smoke_path),
                "overall_status": smoke.get("overall_status"),
                "issues": smoke.get("issues", [])[:20],
            },
        )
        return
    add_check(
        checks,
        "annotation_roundtrip_smoke",
        "PASS",
        "Annotation import, IAA, adjudication, validation, and scoring smoke test passed without using real gold claims.",
        {
            "path": rel(smoke_path),
            "sample_size": smoke.get("sample_size"),
            "metric_rows": smoke.get("metric_rows"),
            "claim_status": smoke.get("claim_status"),
        },
    )


def validate_mapping_roundtrip_smoke(checks, exp_dir):
    smoke_path = exp_dir / "06_release/mapping_roundtrip_smoke/mapping_roundtrip_smoke_summary.json"
    try:
        smoke = read_json(smoke_path)
    except Exception as exc:
        add_check(
            checks,
            "mapping_roundtrip_smoke",
            "FAIL",
            "Mapping roundtrip smoke summary cannot be read.",
            {"path": rel(smoke_path), "error": str(exc)},
        )
        return
    if smoke.get("overall_status") != "PASS":
        add_check(
            checks,
            "mapping_roundtrip_smoke",
            "FAIL",
            "Mapping roundtrip smoke did not pass.",
            {
                "path": rel(smoke_path),
                "overall_status": smoke.get("overall_status"),
                "issues": smoke.get("issues", [])[:20],
            },
        )
        return
    add_check(
        checks,
        "mapping_roundtrip_smoke",
        "PASS",
        "Mapping import and expert-metric smoke test passed without using real expert-review claims.",
        {
            "path": rel(smoke_path),
            "reviewed_rows": smoke.get("reviewed_rows"),
            "metric_rows": smoke.get("metric_rows"),
            "claim_status": smoke.get("claim_status"),
        },
    )


def validate_crosswalk_roundtrip_smoke(checks, exp_dir):
    smoke_path = exp_dir / "06_release/crosswalk_roundtrip_smoke/crosswalk_roundtrip_smoke_summary.json"
    try:
        smoke = read_json(smoke_path)
    except Exception as exc:
        add_check(
            checks,
            "crosswalk_roundtrip_smoke",
            "FAIL",
            "NCS-PCF crosswalk roundtrip smoke summary cannot be read.",
            {"path": rel(smoke_path), "error": str(exc)},
        )
        return
    issues = []
    if smoke.get("overall_status") != "PASS":
        issues.append({"error": "overall_status_not_pass", "actual": smoke.get("overall_status")})
    if smoke.get("claim_status") != "crosswalk_roundtrip_smoke_not_paper_evidence":
        issues.append({"error": "claim_status_mismatch", "actual": smoke.get("claim_status")})
    if int(smoke.get("selected_source_group_count") or 0) < 2:
        issues.append({"error": "selected_source_group_count_too_low", "actual": smoke.get("selected_source_group_count")})
    if int(smoke.get("reviewed_rows") or 0) < 20:
        issues.append({"error": "reviewed_rows_too_low", "actual": smoke.get("reviewed_rows")})
    if int(smoke.get("import_error_count") or 0) != 0:
        issues.append({"error": "import_errors_present", "actual": smoke.get("import_error_count")})
    if int(smoke.get("metric_rows") or 0) != 1:
        issues.append({"error": "metric_rows_unexpected", "actual": smoke.get("metric_rows")})
    metrics = (smoke.get("metrics") or [{}])[0] if smoke.get("metrics") else {}
    if metrics:
        if metrics.get("claim_status") != "crosswalk_expert_review_evaluated":
            issues.append({"error": "smoke_metric_claim_status_unexpected", "actual": metrics.get("claim_status")})
        if int(metrics.get("complete_source_groups") or 0) != int(smoke.get("selected_source_group_count") or 0):
            issues.append(
                {
                    "error": "complete_source_group_count_mismatch",
                    "metric": metrics.get("complete_source_groups"),
                    "summary": smoke.get("selected_source_group_count"),
                }
            )
    else:
        issues.append({"error": "missing_smoke_metrics"})

    if issues:
        add_check(
            checks,
            "crosswalk_roundtrip_smoke",
            "FAIL",
            "NCS-PCF crosswalk roundtrip smoke did not pass expected non-claimable import/evaluation checks.",
            {"path": rel(smoke_path), "issues": issues[:20]},
        )
        return

    add_check(
        checks,
        "crosswalk_roundtrip_smoke",
        "PASS",
        "NCS-PCF crosswalk import and utility/ranking metric smoke test passed without using real expert-review claims.",
        {
            "path": rel(smoke_path),
            "selected_source_groups": smoke.get("selected_source_group_count"),
            "reviewed_rows": smoke.get("reviewed_rows"),
            "metric_rows": smoke.get("metric_rows"),
            "claim_status": smoke.get("claim_status"),
        },
    )


def validate_active_review_effort_roundtrip_smoke(checks, exp_dir):
    smoke_path = exp_dir / "06_release/active_review_effort_roundtrip_smoke/active_review_effort_roundtrip_smoke_summary.json"
    try:
        smoke = read_json(smoke_path)
    except Exception as exc:
        add_check(
            checks,
            "active_review_effort_roundtrip_smoke",
            "FAIL",
            "Active-review effort roundtrip smoke summary cannot be read.",
            {"path": rel(smoke_path), "error": str(exc)},
        )
        return
    issues = []
    if smoke.get("overall_status") != "PASS":
        issues.append({"error": "overall_status_not_pass", "actual": smoke.get("overall_status")})
    if smoke.get("claim_status") != "active_review_effort_roundtrip_smoke_not_paper_evidence":
        issues.append({"error": "claim_status_mismatch", "actual": smoke.get("claim_status")})
    if int(smoke.get("selected_rows") or 0) < 30:
        issues.append({"error": "selected_rows_too_low", "actual": smoke.get("selected_rows")})
    if int(smoke.get("reviewed_rows") or 0) != int(smoke.get("selected_rows") or 0):
        issues.append({"error": "reviewed_selected_row_mismatch", "reviewed": smoke.get("reviewed_rows"), "selected": smoke.get("selected_rows")})
    if smoke.get("validation_status") != "validated":
        issues.append({"error": "validation_status_unexpected", "actual": smoke.get("validation_status")})
    if int(smoke.get("validation_error_count") or 0) != 0:
        issues.append({"error": "validation_errors_present", "actual": smoke.get("validation_error_count")})
    if smoke.get("ready_for_effort_metric_import") is not True:
        issues.append({"error": "not_ready_for_effort_metric_import", "actual": smoke.get("ready_for_effort_metric_import")})
    if int(smoke.get("metric_rows") or 0) != 3:
        issues.append({"error": "metric_rows_unexpected", "actual": smoke.get("metric_rows")})
    metrics = [row for row in as_list(smoke.get("metrics")) if isinstance(row, dict)]
    metric_arms = {row.get("arm") for row in metrics}
    if metric_arms != {"active_priority", "uncertainty_only", "random_control"}:
        issues.append({"error": "metric_arms_unexpected", "actual": sorted(metric_arms)})
    for row in metrics:
        if row.get("claim_status") != "human_effort_evaluated":
            issues.append({"error": "metric_claim_status_unexpected", "arm": row.get("arm"), "actual": row.get("claim_status")})
        if int(row.get("reviewed") or 0) <= 0:
            issues.append({"error": "metric_reviewed_rows_zero", "arm": row.get("arm")})

    if issues:
        add_check(
            checks,
            "active_review_effort_roundtrip_smoke",
            "FAIL",
            "Active-review effort roundtrip smoke did not pass expected non-claimable CSV/evaluation checks.",
            {"path": rel(smoke_path), "issues": issues[:20]},
        )
        return

    add_check(
        checks,
        "active_review_effort_roundtrip_smoke",
        "PASS",
        "Active-review effort CSV validation and human-effort metric smoke test passed without using real human-effort claims.",
        {
            "path": rel(smoke_path),
            "selected_rows": smoke.get("selected_rows"),
            "reviewed_rows": smoke.get("reviewed_rows"),
            "metric_rows": smoke.get("metric_rows"),
            "claim_status": smoke.get("claim_status"),
        },
    )


def validate_claimable_main_table(checks, exp_dir):
    table_path = exp_dir / "06_release/claimable_main_table.json"
    try:
        table = read_json(table_path)
    except Exception as exc:
        add_check(
            checks,
            "claimable_main_table",
            "FAIL",
            "Claimable main table JSON cannot be read.",
            {"path": rel(table_path), "error": str(exc)},
        )
        return
    rows = table.get("rows") or []
    by_result = {row.get("Result"): row for row in rows}
    core = by_result.get("Core extraction main result") or {}
    gate = by_result.get("Submission claim gate") or {}
    sampling = by_result.get("Priority-100 gold subset sampling") or {}
    predicate_cue = by_result.get("Predicate cue span diagnostic") or {}
    if (
        not rows
        or core.get("Claimability") != "pending_human"
        or gate.get("Current value") != "FAIL"
        or sampling.get("Claimability") != "claimable_setup"
        or "candidate_edge_coverage" not in str(sampling.get("Current value") or "")
        or predicate_cue.get("Claimability") != "diagnostic_only"
        or "cue_spans=" not in str(predicate_cue.get("Current value") or "")
        or "predicate_cue_span_metrics.json" not in str(predicate_cue.get("Evidence file") or "")
    ):
        add_check(
            checks,
            "claimable_main_table",
            "FAIL",
            "Claimable main table does not conservatively reflect the current pending-human gate.",
            {
                "path": rel(table_path),
                "overall_claim_status": table.get("overall_claim_status"),
                "core_claimability": core.get("Claimability"),
                "gate_value": gate.get("Current value"),
                "sampling_claimability": sampling.get("Claimability"),
                "sampling_value": sampling.get("Current value"),
                "predicate_cue_claimability": predicate_cue.get("Claimability"),
                "predicate_cue_value": predicate_cue.get("Current value"),
                "predicate_cue_evidence": predicate_cue.get("Evidence file"),
            },
        )
        return
    add_check(
        checks,
        "claimable_main_table",
        "PASS",
        "Claimable main table separates pending human-gold results from diagnostic-only metrics.",
        {
            "path": rel(table_path),
            "overall_claim_status": table.get("overall_claim_status"),
            "blocking_result_count": table.get("blocking_result_count"),
            "sampling_value": sampling.get("Current value"),
            "predicate_cue_value": predicate_cue.get("Current value"),
        },
    )


def validate_claim_language_guardrails(checks, exp_dir):
    json_path = exp_dir / "06_release/claim_language_guardrails.json"
    md_path = exp_dir / "06_release/claim_language_guardrails.md"
    prehuman_path = exp_dir / "06_release/pre_human_handoff_validation.json"
    try:
        payload = read_json(json_path)
        text = md_path.read_text(encoding="utf-8")
        prehuman = read_json(prehuman_path)
    except Exception as exc:
        add_check(
            checks,
            "claim_language_guardrails",
            "FAIL",
            "Claim-language guardrails cannot be read.",
            {"json": rel(json_path), "markdown": rel(md_path), "pre_human_validation": rel(prehuman_path), "error": str(exc)},
        )
        return

    summary = payload.get("summary") or {}
    claims = payload.get("claims") or []
    by_id = {row.get("claim_id"): row for row in claims}
    statuses = {row.get("current_status") for row in claims}
    issues = []
    if payload.get("overall_status") != "PASS":
        issues.append({"error": "overall_status_not_pass", "actual": payload.get("overall_status")})
    if payload.get("claim_status") != "claim_language_guardrails_ready_not_submission_complete":
        issues.append({"error": "claim_status_mismatch", "actual": payload.get("claim_status")})
    if payload.get("safe_to_use_as_submission") is not False:
        issues.append({"error": "safe_to_use_as_submission_should_be_false", "actual": payload.get("safe_to_use_as_submission")})
    if payload.get("submission_ready") is not False:
        issues.append({"error": "submission_ready_should_be_false", "actual": payload.get("submission_ready")})
    if summary.get("claim_count") != 10:
        issues.append({"error": "unexpected_claim_count", "actual": summary.get("claim_count"), "expected": 10})
    if summary.get("missing_evidence_files") != 0 or payload.get("missing_evidence_files"):
        issues.append({"error": "missing_evidence_files", "paths": payload.get("missing_evidence_files")})
    if summary.get("claim_gate_overall_status") != "FAIL":
        issues.append({"error": "claim_gate_should_remain_fail_pre_human", "actual": summary.get("claim_gate_overall_status")})
    if summary.get("pre_human_validation_status") != "PASS":
        issues.append({"error": "pre_human_validation_not_pass", "actual": summary.get("pre_human_validation_status")})
    expected_prehuman = effective_prehuman_summary(prehuman)
    if summary.get("pre_human_validation_status") != expected_prehuman.get("overall_status"):
        issues.append(
            {
                "error": "pre_human_validation_status_stale",
                "actual": summary.get("pre_human_validation_status"),
                "expected": expected_prehuman.get("overall_status"),
            }
        )
    if summary.get("pre_human_validation_checks") != expected_prehuman.get("check_count"):
        issues.append(
            {
                "error": "pre_human_validation_check_count_stale",
                "actual": summary.get("pre_human_validation_checks"),
                "expected": expected_prehuman.get("check_count"),
            }
        )
    expected_check_line = f"| Pre-human checks | {expected_prehuman.get('check_count')} |"
    if expected_check_line not in text:
        issues.append(
            {
                "error": "markdown_pre_human_validation_check_count_stale",
                "expected_line": expected_check_line,
            }
        )
    for required_status in [
        "claimable_setup_or_diagnostic",
        "pending_human_gold",
        "pending_expert_review",
        "pending_human_effort",
        "rights_review_required",
    ]:
        if required_status not in statuses:
            issues.append({"error": "missing_expected_claim_status", "status": required_status})
    expected_status_by_claim = {
        "C01_task_and_method_framing": "claimable_setup_or_diagnostic",
        "C02_kg_construction_counts": "claimable_setup_or_diagnostic",
        "C03_main_extraction_performance": "pending_human_gold",
        "C04_evidence_faithfulness": "pending_human_gold",
        "C05_baseline_ablation_superiority": "pending_human_gold",
        "C06_structural_diagnostics": "claimable_setup_or_diagnostic",
        "C07_public_benchmark_adapter": "claimable_setup_or_diagnostic",
        "C08_mapping_crosswalk": "pending_expert_review",
        "C09_active_review_efficiency": "pending_human_effort",
        "C10_reproducibility_release": "rights_review_required",
    }
    for claim_id, expected_status in expected_status_by_claim.items():
        row = by_id.get(claim_id)
        if not row:
            issues.append({"error": "missing_claim_id", "claim_id": claim_id})
            continue
        if row.get("current_status") != expected_status:
            issues.append(
                {
                    "error": "claim_status_unexpected",
                    "claim_id": claim_id,
                    "actual": row.get("current_status"),
                    "expected": expected_status,
                }
            )
        if not row.get("safe_phrasing_ko") or not row.get("safe_phrasing_en"):
            issues.append({"error": "missing_safe_phrasing", "claim_id": claim_id})
        if not row.get("unsafe_phrasing_examples"):
            issues.append({"error": "missing_unsafe_phrasing_examples", "claim_id": claim_id})
        if row.get("missing_evidence_files"):
            issues.append({"error": "claim_missing_evidence", "claim_id": claim_id, "paths": row.get("missing_evidence_files")})
    required_patterns = [
        "# CAPE-KG Claim Language Guardrails",
        "## Claim Policy",
        "## Guardrail Table",
        "safe_phrasing_ko",
        "Unsafe phrasing examples",
        "claim_language_guardrails_ready_not_submission_complete",
        "pending_human_gold",
        "pending_expert_review",
        "pending_human_effort",
        "rights_review_required",
    ]
    missing_patterns = [pattern for pattern in required_patterns if pattern not in text]
    if missing_patterns:
        issues.append({"error": "markdown_missing_required_patterns", "patterns": missing_patterns})

    if issues:
        add_check(
            checks,
            "claim_language_guardrails",
            "FAIL",
            "Claim-language guardrails are missing claim-safety markers, evidence, or safe/unsafe wording.",
            {"json": rel(json_path), "markdown": rel(md_path), "pre_human_validation": rel(prehuman_path), "issues": issues[:30]},
        )
        return

    add_check(
        checks,
        "claim_language_guardrails",
        "PASS",
        "Claim-language guardrails define safe and unsafe paper/presentation wording for all current claim classes.",
        {
            "json": rel(json_path),
            "markdown": rel(md_path),
            "claims": summary.get("claim_count"),
            "status_counts": summary.get("status_counts"),
            "claim_status": payload.get("claim_status"),
            "safe_to_use_as_submission": payload.get("safe_to_use_as_submission"),
            "pre_human_validation": rel(prehuman_path),
            "pre_human_validation_checks": summary.get("pre_human_validation_checks"),
        },
    )


def validate_reviewer_response_prep(checks, exp_dir):
    json_path = exp_dir / "06_release/reviewer_response_prep.json"
    md_path = exp_dir / "06_release/reviewer_response_prep.md"
    prehuman_path = exp_dir / "06_release/pre_human_handoff_validation.json"
    try:
        payload = read_json(json_path)
        text = md_path.read_text(encoding="utf-8")
        prehuman = read_json(prehuman_path)
    except Exception as exc:
        add_check(
            checks,
            "reviewer_response_prep",
            "FAIL",
            "Reviewer response preparation artifacts cannot be read.",
            {"json": rel(json_path), "markdown": rel(md_path), "pre_human_validation": rel(prehuman_path), "error": str(exc)},
        )
        return

    summary = payload.get("summary") or {}
    responses = payload.get("responses") or []
    by_id = {row.get("response_id"): row for row in responses}
    statuses = {row.get("status") for row in responses}
    issues = []
    if payload.get("overall_status") != "PASS":
        issues.append({"error": "overall_status_not_pass", "actual": payload.get("overall_status")})
    if payload.get("claim_status") != "reviewer_response_prep_ready_not_submission_complete":
        issues.append({"error": "claim_status_mismatch", "actual": payload.get("claim_status")})
    if payload.get("safe_to_use_as_submission") is not False:
        issues.append({"error": "safe_to_use_as_submission_should_be_false", "actual": payload.get("safe_to_use_as_submission")})
    if payload.get("submission_ready") is not False:
        issues.append({"error": "submission_ready_should_be_false", "actual": payload.get("submission_ready")})
    if summary.get("response_count") != 7:
        issues.append({"error": "unexpected_response_count", "actual": summary.get("response_count"), "expected": 7})
    if summary.get("missing_evidence_files") != 0 or payload.get("missing_evidence_files"):
        issues.append({"error": "missing_evidence_files", "paths": payload.get("missing_evidence_files")})
    if summary.get("claim_gate_overall_status") != "FAIL":
        issues.append({"error": "claim_gate_should_remain_fail_pre_human", "actual": summary.get("claim_gate_overall_status")})
    if summary.get("pre_human_validation_status") != "PASS":
        issues.append({"error": "pre_human_validation_not_pass", "actual": summary.get("pre_human_validation_status")})
    expected_prehuman = effective_prehuman_summary(prehuman)
    if summary.get("pre_human_validation_status") != expected_prehuman.get("overall_status"):
        issues.append(
            {
                "error": "pre_human_validation_status_stale",
                "actual": summary.get("pre_human_validation_status"),
                "expected": expected_prehuman.get("overall_status"),
            }
        )
    if summary.get("pre_human_validation_checks") != expected_prehuman.get("check_count"):
        issues.append(
            {
                "error": "pre_human_validation_check_count_stale",
                "actual": summary.get("pre_human_validation_checks"),
                "expected": expected_prehuman.get("check_count"),
            }
        )
    expected_check_line = f"| Pre-human checks | {expected_prehuman.get('check_count')} |"
    if expected_check_line not in text:
        issues.append(
            {
                "error": "markdown_pre_human_validation_check_count_stale",
                "expected_line": expected_check_line,
            }
        )
    for required_status in [
        "mitigated_setup_final_performance_pending",
        "mitigated_public_safe_release_rights_review_required",
        "partially_mitigated_final_gain_pending",
        "claimable_setup_human_quality_pending",
        "mitigated_with_constraints_and_diagnostics",
        "scaffold_ready_human_metrics_pending",
        "candidate_pipeline_ready_expert_review_pending",
    ]:
        if required_status not in statuses:
            issues.append({"error": "missing_expected_response_status", "status": required_status})
    expected_ids = {
        "Q01_domain_application",
        "Q02_reproducibility_private_data",
        "Q03_existing_ontology_guided_extraction",
        "Q04_why_korean_enterprise_documents",
        "Q05_prompt_engineering",
        "Q06_subjective_evaluation",
        "Q07_ncs_pcf_nlp_contribution",
    }
    for response_id in sorted(expected_ids):
        row = by_id.get(response_id)
        if not row:
            issues.append({"error": "missing_response_id", "response_id": response_id})
            continue
        if not row.get("short_answer_ko") or not row.get("short_answer_en"):
            issues.append({"error": "missing_short_answer", "response_id": response_id})
        if not row.get("safe_claim_boundary") or not row.get("must_not_claim") or not row.get("remaining_gate"):
            issues.append({"error": "missing_claim_boundary", "response_id": response_id})
        if row.get("missing_evidence_files"):
            issues.append({"error": "response_missing_evidence", "response_id": response_id, "paths": row.get("missing_evidence_files")})
    required_patterns = [
        "# CAPE-KG Reviewer Response Prep",
        "## Response Table",
        "## Detailed Responses",
        "## Claim Policy",
        "reviewer_response_prep_ready_not_submission_complete",
        "단순 domain application 아닌가?",
        "데이터가 공개되지 않으면 재현성이 낮지 않은가?",
        "ontology-guided extraction은 이미 많지 않은가?",
        "LLM prompt engineering 아닌가?",
        "평가가 subjective하지 않은가?",
        "NCS/PCF mapping이 NLP contribution인가?",
        "safe_to_use_as_submission=false",
        "submission_ready=false",
    ]
    missing_patterns = [pattern for pattern in required_patterns if pattern not in text]
    if missing_patterns:
        issues.append({"error": "markdown_missing_required_patterns", "patterns": missing_patterns})

    if issues:
        add_check(
            checks,
            "reviewer_response_prep",
            "FAIL",
            "Reviewer response prep is missing expected questions, evidence, or claim boundaries.",
            {"json": rel(json_path), "markdown": rel(md_path), "pre_human_validation": rel(prehuman_path), "issues": issues[:30]},
        )
        return

    add_check(
        checks,
        "reviewer_response_prep",
        "PASS",
        "Reviewer response prep maps the revised-plan reviewer questions to evidence, safe answers, and remaining gates.",
        {
            "json": rel(json_path),
            "markdown": rel(md_path),
            "responses": summary.get("response_count"),
            "status_counts": summary.get("status_counts"),
            "claim_status": payload.get("claim_status"),
            "safe_to_use_as_submission": payload.get("safe_to_use_as_submission"),
            "pre_human_validation": rel(prehuman_path),
            "pre_human_validation_checks": summary.get("pre_human_validation_checks"),
        },
    )


def validate_submission_timeline_action_board(checks, exp_dir):
    json_path = exp_dir / "06_release/submission_timeline_action_board.json"
    md_path = exp_dir / "06_release/submission_timeline_action_board.md"
    prehuman_path = exp_dir / "06_release/pre_human_handoff_validation.json"
    try:
        payload = read_json(json_path)
        text = md_path.read_text(encoding="utf-8")
        prehuman = read_json(prehuman_path)
    except Exception as exc:
        add_check(
            checks,
            "submission_timeline_action_board",
            "FAIL",
            "Submission timeline action board cannot be read.",
            {"json": rel(json_path), "markdown": rel(md_path), "pre_human_validation": rel(prehuman_path), "error": str(exc)},
        )
        return

    summary = payload.get("summary") or {}
    phases = payload.get("strategy_a_aggressive_schedule") or []
    actions = payload.get("critical_path_actions") or []
    by_action = {row.get("action_id"): row for row in actions}
    issues = []
    if payload.get("overall_status") != "PASS":
        issues.append({"error": "overall_status_not_pass", "actual": payload.get("overall_status")})
    if payload.get("claim_status") != "submission_timeline_action_board_ready_not_submission_complete":
        issues.append({"error": "claim_status_mismatch", "actual": payload.get("claim_status")})
    if payload.get("safe_to_use_as_submission") is not False:
        issues.append({"error": "safe_to_use_as_submission_should_be_false", "actual": payload.get("safe_to_use_as_submission")})
    if payload.get("submission_ready") is not False:
        issues.append({"error": "submission_ready_should_be_false", "actual": payload.get("submission_ready")})
    if summary.get("arr_target_date") != "2026-08-03":
        issues.append({"error": "arr_target_date_mismatch", "actual": summary.get("arr_target_date")})
    if summary.get("phase_count") != 6:
        issues.append({"error": "unexpected_phase_count", "actual": summary.get("phase_count"), "expected": 6})
    if summary.get("action_count") != 10:
        issues.append({"error": "unexpected_action_count", "actual": summary.get("action_count"), "expected": 10})
    if summary.get("critical_action_count") != 5:
        issues.append({"error": "unexpected_critical_action_count", "actual": summary.get("critical_action_count"), "expected": 5})
    if summary.get("strong_optional_action_count") != 5:
        issues.append({"error": "unexpected_strong_optional_action_count", "actual": summary.get("strong_optional_action_count"), "expected": 5})
    if summary.get("minimum_human_return_files") != 11:
        issues.append({"error": "minimum_return_file_count_mismatch", "actual": summary.get("minimum_human_return_files")})
    if summary.get("optional_claim_return_files") != 3:
        issues.append({"error": "optional_claim_return_file_count_mismatch", "actual": summary.get("optional_claim_return_files"), "expected": 3})
    if summary.get("optional_structural_return_files") != 2:
        issues.append({"error": "optional_structural_return_file_count_mismatch", "actual": summary.get("optional_structural_return_files"), "expected": 2})
    if summary.get("tracked_human_return_files") != 16:
        issues.append({"error": "tracked_return_file_count_mismatch", "actual": summary.get("tracked_human_return_files")})
    if summary.get("claim_gate_overall_status") != "FAIL":
        issues.append({"error": "claim_gate_should_remain_fail_pre_human", "actual": summary.get("claim_gate_overall_status")})
    if summary.get("pre_human_validation_status") != "PASS":
        issues.append({"error": "pre_human_validation_not_pass", "actual": summary.get("pre_human_validation_status")})
    expected_prehuman = effective_prehuman_summary(prehuman)
    if summary.get("pre_human_validation_status") != expected_prehuman.get("overall_status"):
        issues.append(
            {
                "error": "pre_human_validation_status_stale",
                "actual": summary.get("pre_human_validation_status"),
                "expected": expected_prehuman.get("overall_status"),
            }
        )
    if summary.get("pre_human_validation_checks") != expected_prehuman.get("check_count"):
        issues.append(
            {
                "error": "pre_human_validation_check_count_stale",
                "actual": summary.get("pre_human_validation_checks"),
                "expected": expected_prehuman.get("check_count"),
            }
        )
    expected_check_line = f"| Pre-human checks | {expected_prehuman.get('check_count')} |"
    if expected_check_line not in text:
        issues.append(
            {
                "error": "markdown_pre_human_validation_check_count_stale",
                "expected_line": expected_check_line,
            }
        )
    if summary.get("missing_evidence_files") != 0 or payload.get("missing_evidence_files"):
        issues.append({"error": "missing_evidence_files", "paths": payload.get("missing_evidence_files")})

    expected_action_ids = {
        "CP01_minimum_annotation_returns",
        "CP02_adjudication_return",
        "CP03_iaa_and_human_gold_scoring",
        "CP04_claim_safe_main_tables",
        "CP05_release_and_validation_freeze",
        "OP01_mapping_expert_review",
        "OP02_crosswalk_expert_review",
        "OP03_active_review_effort",
        "OP04_structural_checkpoint_review",
        "OP05_structural_gateway_branch_review",
    }
    for action_id in sorted(expected_action_ids):
        row = by_action.get(action_id)
        if not row:
            issues.append({"error": "missing_action_id", "action_id": action_id})
            continue
        if not row.get("due_date") or not row.get("next_action") or not row.get("required_for"):
            issues.append({"error": "action_missing_required_field", "action_id": action_id})
        if row.get("missing_evidence_files"):
            issues.append({"error": "action_missing_evidence", "action_id": action_id, "paths": row.get("missing_evidence_files")})
    required_patterns = [
        "# CAPE-KG Submission Timeline Action Board",
        "## Strategy A Schedule Status",
        "## Critical Path Actions",
        "ARR target date",
        "2026-08-03",
        "Optional/strong claim return files",
        "Optional structural review files",
        "All master return files",
        "CP01_minimum_annotation_returns",
        "CP03_iaa_and_human_gold_scoring",
        "OP01_mapping_expert_review",
        "OP04_structural_checkpoint_review",
        "safe_to_use_as_submission=false",
        "submission_ready=false",
    ]
    missing_patterns = [pattern for pattern in required_patterns if pattern not in text]
    if missing_patterns:
        issues.append({"error": "markdown_missing_required_patterns", "patterns": missing_patterns})

    if issues:
        add_check(
            checks,
            "submission_timeline_action_board",
            "FAIL",
            "Submission timeline action board is missing expected phases, actions, evidence, or claim boundaries.",
            {"json": rel(json_path), "markdown": rel(md_path), "pre_human_validation": rel(prehuman_path), "issues": issues[:30]},
        )
        return

    add_check(
        checks,
        "submission_timeline_action_board",
        "PASS",
        "Submission timeline action board maps the revised-plan schedule to current gates and critical-path actions.",
        {
            "json": rel(json_path),
            "markdown": rel(md_path),
            "arr_target_date": summary.get("arr_target_date"),
            "days_to_arr_target": summary.get("days_to_arr_target"),
            "actions": summary.get("action_count"),
            "claim_status": payload.get("claim_status"),
            "safe_to_use_as_submission": payload.get("safe_to_use_as_submission"),
            "pre_human_validation": rel(prehuman_path),
            "pre_human_validation_checks": summary.get("pre_human_validation_checks"),
        },
    )


def validate_paper_table_blueprint(checks, exp_dir):
    json_path = exp_dir / "06_release/paper_table_blueprint.json"
    md_path = exp_dir / "06_release/paper_table_blueprint.md"
    prehuman_path = exp_dir / "06_release/pre_human_handoff_validation.json"
    try:
        payload = read_json(json_path)
        text = md_path.read_text(encoding="utf-8")
        prehuman = read_json(prehuman_path)
    except Exception as exc:
        add_check(
            checks,
            "paper_table_blueprint",
            "FAIL",
            "Paper table blueprint cannot be read.",
            {"json": rel(json_path), "markdown": rel(md_path), "pre_human_validation": rel(prehuman_path), "error": str(exc)},
        )
        return

    summary = payload.get("summary") or {}
    tables = payload.get("tables") or []
    by_id = {row.get("table_id"): row for row in tables}
    statuses = {row.get("current_status") for row in tables}
    issues = []
    if payload.get("overall_status") != "PASS":
        issues.append({"error": "overall_status_not_pass", "actual": payload.get("overall_status")})
    if payload.get("claim_status") != "paper_table_blueprint_ready_not_submission_complete":
        issues.append({"error": "claim_status_mismatch", "actual": payload.get("claim_status")})
    if payload.get("safe_to_use_as_submission") is not False:
        issues.append({"error": "safe_to_use_as_submission_should_be_false", "actual": payload.get("safe_to_use_as_submission")})
    if payload.get("submission_ready") is not False:
        issues.append({"error": "submission_ready_should_be_false", "actual": payload.get("submission_ready")})
    if summary.get("table_count") != 9:
        issues.append({"error": "unexpected_table_count", "actual": summary.get("table_count"), "expected": 9})
    if summary.get("missing_evidence_files") != 0 or payload.get("missing_evidence_files"):
        issues.append({"error": "missing_evidence_files", "paths": payload.get("missing_evidence_files")})
    if summary.get("claim_gate_overall_status") != "FAIL":
        issues.append({"error": "claim_gate_should_remain_fail_pre_human", "actual": summary.get("claim_gate_overall_status")})
    if summary.get("pre_human_validation_status") != "PASS":
        issues.append({"error": "pre_human_validation_not_pass", "actual": summary.get("pre_human_validation_status")})
    expected_prehuman = effective_prehuman_summary(prehuman)
    if summary.get("pre_human_validation_status") != expected_prehuman.get("overall_status"):
        issues.append(
            {
                "error": "pre_human_validation_status_stale",
                "actual": summary.get("pre_human_validation_status"),
                "expected": expected_prehuman.get("overall_status"),
            }
        )
    if summary.get("pre_human_validation_checks") != expected_prehuman.get("check_count"):
        issues.append(
            {
                "error": "pre_human_validation_check_count_stale",
                "actual": summary.get("pre_human_validation_checks"),
                "expected": expected_prehuman.get("check_count"),
            }
        )
    expected_check_line = f"| Pre-human checks | {expected_prehuman.get('check_count')} |"
    if expected_check_line not in text:
        issues.append(
            {
                "error": "markdown_pre_human_validation_check_count_stale",
                "expected_line": expected_check_line,
            }
        )
    for required_status in [
        "pending_human_gold",
        "diagnostic_only_until_human_gold",
        "structural_diagnostic_ready",
        "auxiliary_claimable_not_main_private_result",
        "pending_expert_review",
        "pending_human_effort",
        "claimable_setup_rights_review_required",
    ]:
        if required_status not in statuses:
            issues.append({"error": "missing_expected_table_status", "status": required_status})
    expected_table_ids = {
        "T01_dataset_annotation_status",
        "T02_main_extraction_human_gold",
        "T03_cq_schema_ablation",
        "T04_structural_cq_diagnostics",
        "T05_public_benchmark_adapter",
        "T06_mapping_downstream",
        "T07_crosswalk_downstream",
        "T08_active_review_efficiency",
        "T09_reproducibility_release",
    }
    for table_id in sorted(expected_table_ids):
        row = by_id.get(table_id)
        if not row:
            issues.append({"error": "missing_table_id", "table_id": table_id})
            continue
        if not row.get("promotion_gate") or not row.get("target_metrics") or not row.get("caption_stub"):
            issues.append({"error": "table_missing_required_field", "table_id": table_id})
        if row.get("missing_evidence_files"):
            issues.append({"error": "table_missing_evidence", "table_id": table_id, "paths": row.get("missing_evidence_files")})
    required_patterns = [
        "# CAPE-KG Paper Table Blueprint",
        "## Table Blueprint",
        "## Detailed Table Specs",
        "## Claim Policy",
        "paper_table_blueprint_ready_not_submission_complete",
        "T02_main_extraction_human_gold",
        "T03_cq_schema_ablation",
        "T06_mapping_downstream",
        "T08_active_review_efficiency",
        "safe_to_use_as_submission=false",
        "submission_ready=false",
    ]
    missing_patterns = [pattern for pattern in required_patterns if pattern not in text]
    if missing_patterns:
        issues.append({"error": "markdown_missing_required_patterns", "patterns": missing_patterns})

    if issues:
        add_check(
            checks,
            "paper_table_blueprint",
            "FAIL",
            "Paper table blueprint is missing expected table specs, promotion gates, evidence, or claim boundaries.",
            {"json": rel(json_path), "markdown": rel(md_path), "pre_human_validation": rel(prehuman_path), "issues": issues[:30]},
        )
        return

    add_check(
        checks,
        "paper_table_blueprint",
        "PASS",
        "Paper table blueprint separates final main tables from diagnostics, appendix material, and pending human/expert gates.",
        {
            "json": rel(json_path),
            "markdown": rel(md_path),
            "tables": summary.get("table_count"),
            "status_counts": summary.get("status_counts"),
            "claim_status": payload.get("claim_status"),
            "safe_to_use_as_submission": payload.get("safe_to_use_as_submission"),
            "pre_human_validation": rel(prehuman_path),
            "pre_human_validation_checks": summary.get("pre_human_validation_checks"),
        },
    )


def validate_arr_submission_policy_checklist(checks, exp_dir):
    json_path = exp_dir / "06_release/arr_submission_policy_checklist.json"
    md_path = exp_dir / "06_release/arr_submission_policy_checklist.md"
    prehuman_path = exp_dir / "06_release/pre_human_handoff_validation.json"
    try:
        payload = read_json(json_path)
        text = md_path.read_text(encoding="utf-8")
        prehuman = read_json(prehuman_path)
        latest_index = read_json(exp_dir / "06_release/latest_release_bundle_index.json")
    except Exception as exc:
        add_check(
            checks,
            "arr_submission_policy_checklist",
            "FAIL",
            "ARR/EACL submission policy checklist cannot be read.",
            {"json": rel(json_path), "markdown": rel(md_path), "pre_human_validation": rel(prehuman_path), "error": str(exc)},
        )
        return

    summary = payload.get("summary") or {}
    items = payload.get("items") or []
    by_id = {row.get("item_id"): row for row in items}
    statuses = {row.get("status") for row in items}
    source_ids = {row.get("source_id") for row in payload.get("official_sources") or []}
    issues = []
    if payload.get("overall_status") != "PASS":
        issues.append({"error": "overall_status_not_pass", "actual": payload.get("overall_status")})
    if payload.get("claim_status") != "arr_submission_policy_checklist_ready_not_submission_complete":
        issues.append({"error": "claim_status_mismatch", "actual": payload.get("claim_status")})
    if payload.get("safe_to_use_as_submission") is not False:
        issues.append({"error": "safe_to_use_as_submission_should_be_false", "actual": payload.get("safe_to_use_as_submission")})
    if payload.get("submission_ready") is not False:
        issues.append({"error": "submission_ready_should_be_false", "actual": payload.get("submission_ready")})
    if summary.get("arr_target_date") != "2026-08-03":
        issues.append({"error": "arr_target_date_mismatch", "actual": summary.get("arr_target_date")})
    if summary.get("item_count") != 10:
        issues.append({"error": "unexpected_item_count", "actual": summary.get("item_count"), "expected": 10})
    if summary.get("official_source_count") != 6:
        issues.append({"error": "unexpected_source_count", "actual": summary.get("official_source_count"), "expected": 6})
    if summary.get("missing_evidence_files") != 0 or payload.get("missing_evidence_files"):
        issues.append({"error": "missing_evidence_files", "paths": payload.get("missing_evidence_files")})
    if summary.get("claim_gate_overall_status") != "FAIL":
        issues.append({"error": "claim_gate_should_remain_fail_pre_human", "actual": summary.get("claim_gate_overall_status")})
    if summary.get("pre_human_validation_status") != "PASS":
        issues.append({"error": "pre_human_validation_not_pass", "actual": summary.get("pre_human_validation_status")})
    expected_prehuman = effective_prehuman_summary(prehuman)
    if summary.get("pre_human_validation_status") != expected_prehuman.get("overall_status"):
        issues.append(
            {
                "error": "pre_human_validation_status_stale",
                "actual": summary.get("pre_human_validation_status"),
                "expected": expected_prehuman.get("overall_status"),
            }
        )
    if summary.get("pre_human_validation_checks") != expected_prehuman.get("check_count"):
        issues.append(
            {
                "error": "pre_human_validation_check_count_stale",
                "actual": summary.get("pre_human_validation_checks"),
                "expected": expected_prehuman.get("check_count"),
            }
        )
    expected_check_line = f"| Pre-human checks | {expected_prehuman.get('check_count')} |"
    if expected_check_line not in text:
        issues.append(
            {
                "error": "markdown_pre_human_validation_check_count_stale",
                "expected_line": expected_check_line,
            }
        )
    latest_stamp = latest_index.get("stamp")
    static_stamp_matches = sorted(set(re.findall(r"latest_release_stamp=([^;\\s|]+)", text)))
    if static_stamp_matches:
        issues.append(
            {
                "error": "static_latest_release_stamp_in_arr_checklist",
                "stamps": static_stamp_matches,
                "latest_stamp": latest_stamp,
                "expected": "Reference latest_release_bundle_index.md instead of embedding a stamp.",
            }
        )
    for required_source in [
        "SRC01_eacl_2027_dates",
        "SRC02_arr_cfp",
        "SRC03_arr_author_checklist",
        "SRC04_aclpub_formatting",
        "SRC05_arr_authors",
        "SRC06_responsible_nlp",
    ]:
        if required_source not in source_ids:
            issues.append({"error": "missing_official_source", "source_id": required_source})
    for required_status in [
        "pass",
        "pass_expected_not_ready",
        "pending_author_action",
        "pending_pdf_render",
        "public_safe_scaffold_ready_anonymization_pending",
        "scaffold_ready_final_answers_pending",
        "pending_author_confirmation",
        "pass_pre_human_scaffold",
    ]:
        if required_status not in statuses:
            issues.append({"error": "missing_expected_policy_status", "status": required_status})
    expected_item_ids = {
        "ARR01_deadline_tracking",
        "ARR02_claim_gate_not_submission_ready",
        "ARR03_limitations_section",
        "ARR04_ethics_section",
        "ARR05_anonymization",
        "ARR06_page_limit_pdf_check",
        "ARR07_supplement_public_safe",
        "ARR08_responsible_nlp_checklist",
        "ARR09_no_dual_submission",
        "ARR10_final_artifact_sync",
    }
    for item_id in sorted(expected_item_ids):
        row = by_id.get(item_id)
        if not row:
            issues.append({"error": "missing_item_id", "item_id": item_id})
            continue
        if not row.get("source_ids") or not row.get("next_action") or not row.get("paper_use_now"):
            issues.append({"error": "item_missing_required_field", "item_id": item_id})
        if row.get("missing_evidence_files"):
            issues.append({"error": "item_missing_evidence", "item_id": item_id, "paths": row.get("missing_evidence_files")})
    required_patterns = [
        "# CAPE-KG ARR/EACL Submission Policy Checklist",
        "## Official Sources",
        "ARR01_deadline_tracking",
        "ARR03_limitations_section",
        "ARR05_anonymization",
        "ARR06_page_limit_pdf_check",
        "ARR09_no_dual_submission",
        "arr_submission_policy_checklist_ready_not_submission_complete",
        "safe_to_use_as_submission=false",
        "submission_ready=false",
        "latest_release_bundle_index.md",
        "2026-08-03",
    ]
    missing_patterns = [pattern for pattern in required_patterns if pattern not in text]
    if missing_patterns:
        issues.append({"error": "markdown_missing_required_patterns", "patterns": missing_patterns})

    if issues:
        add_check(
            checks,
            "arr_submission_policy_checklist",
            "FAIL",
            "ARR/EACL submission policy checklist is missing expected policy items, sources, evidence, or claim boundaries.",
            {"json": rel(json_path), "markdown": rel(md_path), "pre_human_validation": rel(prehuman_path), "issues": issues[:30]},
        )
        return

    add_check(
        checks,
        "arr_submission_policy_checklist",
        "PASS",
        "ARR/EACL submission policy checklist maps official policy items to draft sections, release artifacts, and manual gates.",
        {
            "json": rel(json_path),
            "markdown": rel(md_path),
            "items": summary.get("item_count"),
            "status_counts": summary.get("status_counts"),
            "claim_status": payload.get("claim_status"),
            "safe_to_use_as_submission": payload.get("safe_to_use_as_submission"),
            "pre_human_validation": rel(prehuman_path),
            "pre_human_validation_checks": summary.get("pre_human_validation_checks"),
        },
    )


def validate_anonymized_submission_prep(checks, exp_dir):
    json_path = exp_dir / "06_release/anonymized_submission_prep.json"
    md_path = exp_dir / "06_release/anonymized_submission_prep.md"
    csv_path = exp_dir / "06_release/anonymized_submission_risk_scan.csv"
    try:
        payload = read_json(json_path)
        text = md_path.read_text(encoding="utf-8")
        risk_rows = read_csv_rows(csv_path)
        latest_index = read_json(exp_dir / "06_release/latest_release_bundle_index.json")
    except Exception as exc:
        add_check(
            checks,
            "anonymized_submission_prep",
            "FAIL",
            "Anonymized submission prep artifacts cannot be read.",
            {"json": rel(json_path), "markdown": rel(md_path), "csv": rel(csv_path), "error": str(exc)},
        )
        return

    summary = payload.get("summary") or {}
    latest_current = latest_index.get("current") or {}
    latest_public_bundle = (latest_current.get("public_safe_bundle") or {}).get("path")
    manual_gates = payload.get("manual_gates") or []
    issues = []
    if payload.get("overall_status") != "PASS":
        issues.append({"error": "overall_status_not_pass", "actual": payload.get("overall_status")})
    if payload.get("claim_status") != "anonymized_submission_prep_ready_not_upload_ready":
        issues.append({"error": "claim_status_mismatch", "actual": payload.get("claim_status")})
    if payload.get("safe_to_use_as_submission") is not False:
        issues.append({"error": "safe_to_use_as_submission_should_be_false", "actual": payload.get("safe_to_use_as_submission")})
    if payload.get("submission_ready") is not False:
        issues.append({"error": "submission_ready_should_be_false", "actual": payload.get("submission_ready")})
    if payload.get("upload_ready") is not False:
        issues.append({"error": "upload_ready_should_be_false", "actual": payload.get("upload_ready")})
    if summary.get("missing_inputs") != 0 or payload.get("missing_inputs"):
        issues.append({"error": "missing_inputs", "paths": payload.get("missing_inputs")})
    if summary.get("manual_gates") != 5 or len(manual_gates) != 5:
        issues.append({"error": "manual_gate_count_mismatch", "summary": summary.get("manual_gates"), "actual": len(manual_gates)})
    if summary.get("public_safe_tar_blocking_hits") != 0:
        issues.append(
            {
                "error": "public_safe_tar_blocking_hits",
                "actual": summary.get("public_safe_tar_blocking_hits"),
            }
        )
    if summary.get("release_stamp") != latest_index.get("stamp"):
        issues.append(
            {
                "error": "latest_release_stamp_mismatch",
                "expected": latest_index.get("stamp"),
                "actual": summary.get("release_stamp"),
            }
        )
    if summary.get("public_safe_bundle") != latest_public_bundle:
        issues.append(
            {
                "error": "latest_public_safe_bundle_mismatch",
                "expected": latest_public_bundle,
                "actual": summary.get("public_safe_bundle"),
            }
        )
    if len(risk_rows) != int(summary.get("risk_rows") or 0):
        issues.append({"error": "risk_csv_row_count_mismatch", "csv_rows": len(risk_rows), "summary": summary.get("risk_rows")})
    gate_ids = {row.get("gate_id") for row in manual_gates}
    for gate_id in ["ANON01_final_acl_pdf", "ANON02_author_identity", "ANON03_public_safe_supplement", "ANON04_rights_review", "ANON05_final_policy_confirmation"]:
        if gate_id not in gate_ids:
            issues.append({"error": "missing_manual_gate", "gate_id": gate_id})
    required_patterns = [
        "# CAPE-KG Anonymized Submission Prep",
        "anonymized_submission_prep_ready_not_upload_ready",
        "Safe to use as submission",
        "Submission ready",
        "Upload ready",
        "## Manual Gates",
        "## Risk Scan Preview",
        "public-safe skeleton",
        "Final manuscript upload requires a rendered ACL PDF",
    ]
    missing_patterns = [pattern for pattern in required_patterns if pattern not in text]
    if missing_patterns:
        issues.append({"error": "markdown_missing_required_patterns", "patterns": missing_patterns})

    if issues:
        add_check(
            checks,
            "anonymized_submission_prep",
            "FAIL",
            "Anonymized submission prep is missing claim-safety markers, manual gates, or public-safe tar safety.",
            {"json": rel(json_path), "markdown": rel(md_path), "csv": rel(csv_path), "issues": issues[:30]},
        )
        return

    add_check(
        checks,
        "anonymized_submission_prep",
        "PASS",
        "Anonymized submission prep scans manuscript/supplement risks while keeping upload-ready status false.",
        {
            "json": rel(json_path),
            "markdown": rel(md_path),
            "csv": rel(csv_path),
            "risk_rows": summary.get("risk_rows"),
            "manual_gates": summary.get("manual_gates"),
            "public_safe_tar_file_count": summary.get("public_safe_tar_file_count"),
            "upload_ready": payload.get("upload_ready"),
        },
    )


def validate_responsible_nlp_checklist_prep(checks, exp_dir):
    release_dir = exp_dir / "06_release"
    json_path = release_dir / "responsible_nlp_checklist_prep.json"
    md_path = release_dir / "responsible_nlp_checklist_prep.md"
    csv_path = release_dir / "responsible_nlp_checklist_items.csv"
    try:
        payload = read_json(json_path)
        text = md_path.read_text(encoding="utf-8")
        csv_rows = read_csv_rows(csv_path)
    except Exception as exc:
        add_check(
            checks,
            "responsible_nlp_checklist_prep",
            "FAIL",
            "Responsible NLP checklist prep artifacts cannot be read.",
            {"json": rel(json_path), "markdown": rel(md_path), "csv": rel(csv_path), "error": str(exc)},
        )
        return

    summary = payload.get("summary") or {}
    items = payload.get("items") or []
    statuses = {row.get("status") for row in items}
    ids = {row.get("item_id") for row in items}
    issues = []
    if payload.get("overall_status") != "PASS":
        issues.append({"error": "overall_status_not_pass", "actual": payload.get("overall_status")})
    if payload.get("claim_status") != "responsible_nlp_checklist_prep_ready_not_final_answers":
        issues.append({"error": "claim_status_mismatch", "actual": payload.get("claim_status")})
    if payload.get("safe_to_use_as_submission") is not False:
        issues.append({"error": "safe_to_use_as_submission_should_be_false", "actual": payload.get("safe_to_use_as_submission")})
    if payload.get("submission_ready") is not False:
        issues.append({"error": "submission_ready_should_be_false", "actual": payload.get("submission_ready")})
    if payload.get("final_answers_ready") is not False:
        issues.append({"error": "final_answers_ready_should_be_false", "actual": payload.get("final_answers_ready")})
    if summary.get("item_count") != 10 or len(items) != 10:
        issues.append({"error": "item_count_mismatch", "summary": summary.get("item_count"), "actual": len(items)})
    if summary.get("draft_answer_count") != 10:
        issues.append({"error": "draft_answer_count_mismatch", "actual": summary.get("draft_answer_count")})
    if summary.get("missing_evidence_files") != 0 or payload.get("missing_evidence_files"):
        issues.append({"error": "missing_evidence_files", "paths": payload.get("missing_evidence_files")})
    if len(csv_rows) != len(items):
        issues.append({"error": "csv_row_count_mismatch", "csv_rows": len(csv_rows), "items": len(items)})
    for required_status in ["draft_ready", "pending_author_confirmation", "pending_human_gold", "pending_rights_review"]:
        if required_status not in statuses:
            issues.append({"error": "missing_expected_item_status", "status": required_status})
    for item_id in [
        "RNLP01_limitations_and_claim_scope",
        "RNLP02_data_rights_and_release_boundaries",
        "RNLP03_private_or_sensitive_data",
        "RNLP04_human_annotation_and_reviewer_privacy",
        "RNLP05_llm_use_and_hallucination_risk",
        "RNLP06_reproducibility_without_raw_private_corpus",
        "RNLP07_public_benchmark_license_and_citation",
        "RNLP08_anonymization_and_supplement_safety",
        "RNLP09_dual_use_or_misuse",
        "RNLP10_final_author_confirmation",
    ]:
        if item_id not in ids:
            issues.append({"error": "missing_item_id", "item_id": item_id})
    if summary.get("claim_gate_overall_status") != "FAIL":
        issues.append({"error": "claim_gate_should_remain_fail_pre_human", "actual": summary.get("claim_gate_overall_status")})
    if summary.get("anonymized_upload_ready") is not False:
        issues.append({"error": "anonymized_upload_ready_should_be_false", "actual": summary.get("anonymized_upload_ready")})
    required_patterns = [
        "# CAPE-KG Responsible NLP Checklist Prep",
        "responsible_nlp_checklist_prep_ready_not_final_answers",
        "Safe to use as submission",
        "Submission ready",
        "Final answers ready",
        "## Checklist Draft Items",
        "## Draft Answers",
        "## Remaining Author Actions",
        "## Claim Boundaries",
        "## Evidence Files",
        "RNLP05_llm_use_and_hallucination_risk",
        "RNLP08_anonymization_and_supplement_safety",
        "official completed checklist",
    ]
    missing_patterns = [pattern for pattern in required_patterns if pattern not in text]
    if missing_patterns:
        issues.append({"error": "markdown_missing_required_patterns", "patterns": missing_patterns})

    if issues:
        add_check(
            checks,
            "responsible_nlp_checklist_prep",
            "FAIL",
            "Responsible NLP checklist prep is missing draft answers, evidence, or claim-safety markers.",
            {"json": rel(json_path), "markdown": rel(md_path), "csv": rel(csv_path), "issues": issues[:30]},
        )
        return

    add_check(
        checks,
        "responsible_nlp_checklist_prep",
        "PASS",
        "Responsible NLP checklist prep maps ethics, societal-impact, data, LLM-use, reproducibility, and author-confirmation answers to evidence while keeping final answers pending.",
        {
            "json": rel(json_path),
            "markdown": rel(md_path),
            "csv": rel(csv_path),
            "items": summary.get("item_count"),
            "status_counts": summary.get("status_counts"),
            "final_answers_ready": payload.get("final_answers_ready"),
        },
    )


def validate_experiment_reproduction_card(checks, exp_dir):
    release_dir = exp_dir / "06_release"
    json_path = release_dir / "experiment_reproduction_card.json"
    md_path = release_dir / "experiment_reproduction_card.md"
    csv_path = release_dir / "experiment_reproduction_conditions.csv"
    try:
        payload = read_json(json_path)
        text = md_path.read_text(encoding="utf-8")
        csv_rows = read_csv_rows(csv_path)
    except Exception as exc:
        add_check(
            checks,
            "experiment_reproduction_card",
            "FAIL",
            "Experiment reproduction card artifacts cannot be read.",
            {"json": rel(json_path), "markdown": rel(md_path), "csv": rel(csv_path), "error": str(exc)},
        )
        return

    expected_conditions = [
        "B0_plain_llm",
        "B1_predicate_constrained",
        "B2_current_project",
        "B3_edc_style",
        "B4_taxonomy_rag",
        "B5_procedural_prompt",
        "B6_sac_kg_verifier_pruner",
        "P_cape_kg_actual",
        "P_minus_CQ",
        "P_minus_Evidence",
        "P_minus_Procedural_schema",
        "P_minus_Schema_retrieval",
        "P_minus_Standard_bridge",
        "P_minus_Validator",
    ]
    summary = payload.get("summary") or {}
    conditions = payload.get("conditions") or []
    commands = payload.get("reproduction_commands") or []
    actual_conditions = [row.get("condition") for row in conditions]
    command_groups = {row.get("group") for row in commands}
    issues = []
    if payload.get("claim_status") != "experiment_reproduction_card_ready_not_human_gold_claim":
        issues.append({"error": "claim_status_mismatch", "actual": payload.get("claim_status")})
    if summary.get("safe_to_use_as_submission") is not False:
        issues.append({"error": "safe_to_use_as_submission_should_be_false", "actual": summary.get("safe_to_use_as_submission")})
    if summary.get("submission_ready") is not False:
        issues.append({"error": "submission_ready_should_be_false", "actual": summary.get("submission_ready")})
    if summary.get("final_performance_claim_ready") is not False:
        issues.append({"error": "final_performance_claim_ready_should_be_false", "actual": summary.get("final_performance_claim_ready")})
    if summary.get("condition_count") != 14 or len(conditions) != 14:
        issues.append({"error": "condition_count_mismatch", "summary": summary.get("condition_count"), "actual": len(conditions)})
    if actual_conditions != expected_conditions:
        issues.append({"error": "condition_order_mismatch", "expected": expected_conditions, "actual": actual_conditions})
    if len(csv_rows) != len(conditions):
        issues.append({"error": "csv_row_count_mismatch", "csv_rows": len(csv_rows), "conditions": len(conditions)})
    if summary.get("baseline_condition_count") != 7:
        issues.append({"error": "baseline_condition_count_mismatch", "actual": summary.get("baseline_condition_count")})
    if summary.get("proposed_condition_count") != 1:
        issues.append({"error": "proposed_condition_count_mismatch", "actual": summary.get("proposed_condition_count")})
    if summary.get("ablation_condition_count") != 6:
        issues.append({"error": "ablation_condition_count_mismatch", "actual": summary.get("ablation_condition_count")})
    if summary.get("conditions_with_120_rows") != 14:
        issues.append({"error": "conditions_with_120_rows_mismatch", "actual": summary.get("conditions_with_120_rows")})
    if summary.get("missing_source_file_count") != 0 or payload.get("missing_source_files"):
        issues.append({"error": "missing_source_files", "paths": payload.get("missing_source_files")})
    if summary.get("missing_condition_output_count") != 0 or payload.get("missing_condition_outputs"):
        issues.append({"error": "missing_condition_outputs", "conditions": payload.get("missing_condition_outputs")})
    for required_group in [
        "qwen3_8b_initial_baselines",
        "qwen3_8b_b2_b4_baselines",
        "qwen3_8b_edc_schema_ablation",
        "qwen3_8b_cape_ablation",
        "sac_kg_verifier_pruner",
        "silver_scoring",
        "human_gold_refresh_after_returns",
    ]:
        if required_group not in command_groups:
            issues.append({"error": "missing_reproduction_command_group", "group": required_group})
    for row in conditions:
        if int(row.get("rows") or 0) != 120:
            issues.append({"error": "condition_not_120_rows", "condition": row.get("condition"), "rows": row.get("rows")})
        if row.get("metric_claim_status") != "silver_proxy_not_human_gold":
            issues.append({"error": "condition_claim_status_unexpected", "condition": row.get("condition"), "status": row.get("metric_claim_status")})
    required_patterns = [
        "# CAPE-KG Experiment Reproduction Card",
        "experiment_reproduction_card_ready_not_human_gold_claim",
        "Final performance claim ready",
        "## Condition Matrix",
        "## Reproduction Commands",
        "## Prompt and Output Mapping",
        "## Claim Gate Policy",
        "B6_sac_kg_verifier_pruner",
        "P_minus_Schema_retrieval",
        "human-gold",
    ]
    missing_patterns = [pattern for pattern in required_patterns if pattern not in text]
    if missing_patterns:
        issues.append({"error": "markdown_missing_required_patterns", "patterns": missing_patterns})

    if issues:
        add_check(
            checks,
            "experiment_reproduction_card",
            "FAIL",
            "Experiment reproduction card is missing condition, command, source-file, or claim-safety coverage.",
            {"json": rel(json_path), "markdown": rel(md_path), "csv": rel(csv_path), "issues": issues[:30]},
        )
        return

    add_check(
        checks,
        "experiment_reproduction_card",
        "PASS",
        "Experiment reproduction card maps all baselines, ablations, proposed outputs, commands, and claim gates without promoting silver metrics to final claims.",
        {
            "json": rel(json_path),
            "markdown": rel(md_path),
            "csv": rel(csv_path),
            "conditions": summary.get("condition_count"),
            "command_groups": summary.get("command_group_count"),
            "final_performance_claim_ready": summary.get("final_performance_claim_ready"),
        },
    )


def validate_paper_tables_claim_safety(checks, exp_dir):
    md_path = exp_dir / "06_release/paper_tables.md"
    tex_path = exp_dir / "06_release/paper_tables.tex"
    human_path = exp_dir / "04_evaluation/human_gold_validation_summary.json"
    mapping_path = exp_dir / "04_evaluation/mapping_expert_metrics.json"
    crosswalk_path = exp_dir / "04_evaluation/crosswalk_expert_metrics.json"
    issues = []
    try:
        md_text = md_path.read_text(encoding="utf-8")
    except Exception as exc:
        add_check(
            checks,
            "paper_tables_claim_safety",
            "FAIL",
            "Paper table Markdown cannot be read.",
            {"path": rel(md_path), "error": str(exc)},
        )
        return
    try:
        tex_text = tex_path.read_text(encoding="utf-8")
    except Exception as exc:
        add_check(
            checks,
            "paper_tables_claim_safety",
            "FAIL",
            "Paper table LaTeX cannot be read.",
            {"path": rel(tex_path), "error": str(exc)},
        )
        return

    try:
        human = read_json(human_path)
    except Exception as exc:
        human = {}
        issues.append({"error": "human_gold_validation_unreadable", "path": rel(human_path), "detail": str(exc)})
    try:
        mapping = read_json(mapping_path)
    except Exception as exc:
        mapping = {}
        issues.append({"error": "mapping_expert_metrics_unreadable", "path": rel(mapping_path), "detail": str(exc)})
    try:
        crosswalk = read_json(crosswalk_path)
    except Exception as exc:
        crosswalk = {}
        issues.append({"error": "crosswalk_expert_metrics_unreadable", "path": rel(crosswalk_path), "detail": str(exc)})

    required_md_patterns = [
        "Tables marked by pending human gold or expert review are diagnostic only",
        "## Dataset and Annotation Status",
        "## Gold Subset Sampling Coverage",
        "gold_sampling_coverage_ready_pending_human_review",
        "## Actual LLM Silver Diagnostics",
        "## Model Scaling Core Silver Diagnostics",
        "## Human-Gold Metrics",
        "pending_human_adjudication",
        "metrics pending",
        "## Evidence Span Granularity Diagnostic",
        "automatic_component_span_diagnostic_not_human_gold",
        "## Predicate Cue Span Diagnostic",
        "automatic_predicate_cue_span_diagnostic_not_human_gold",
        "cue",
        "## Mapping Expert Review",
        "pending_expert_review",
        "## Crosswalk Expert Review",
        "pending_crosswalk_expert_review",
        "## Active Review Human-Effort Handoff",
        "pending_human_effort_timing",
        "## Paired Bootstrap Silver Diagnostics",
        "silver_proxy_not_human_gold",
        "## Claim Gate",
        "| gold.completed_chunks | FAIL | True |",
        "| gold.iaa | FAIL | True |",
        "| llm.proposed_human_gold_score | FAIL | True |",
        "candidate_only_pending_expert_review",
        "public_adapter_model_runs_diagnostic_not_official_leaderboard",
    ]
    missing_md = [pattern for pattern in required_md_patterns if pattern not in md_text]
    if missing_md:
        issues.append({"error": "missing_markdown_claim_safety_patterns", "patterns": missing_md})

    required_tex_patterns = [
        r"\label{tab:cape-actual-silver}",
        r"\label{tab:cape-gold-sampling}",
        r"\label{tab:cape-human-gold}",
        r"\label{tab:cape-evidence-span-granularity}",
        r"\label{tab:cape-predicate-cue-span}",
        r"\label{tab:cape-mapping-review}",
        r"\label{tab:cape-crosswalk-review}",
        "pending\\_human\\_adjudication",
        "pending\\_expert\\_review",
        "pending\\_crosswalk\\_expert\\_review",
        "silver\\_proxy\\_not\\_human\\_gold",
        "llm.proposed\\_human\\_gold\\_score",
    ]
    missing_tex = [pattern for pattern in required_tex_patterns if pattern not in tex_text]
    if missing_tex:
        issues.append({"error": "missing_latex_claim_safety_patterns", "patterns": missing_tex})

    completed_chunks = int(human.get("completed_adjudicated_chunks") or 0)
    gold_items = int(human.get("gold_item_count_for_readiness") or 0)
    if completed_chunks != 0 or gold_items != 0:
        issues.append(
            {
                "error": "pre_human_gold_counts_unexpected",
                "completed_adjudicated_chunks": completed_chunks,
                "gold_item_count_for_readiness": gold_items,
            }
        )
    expected_human_row = f"| pending_human_adjudication | {completed_chunks} | {gold_items} | metrics pending |"
    if expected_human_row not in md_text:
        issues.append({"error": "human_gold_pending_row_not_synchronized", "expected_row": expected_human_row})

    mapping_rows = mapping.get("metrics") or []
    if len(mapping_rows) < 2:
        issues.append({"error": "mapping_expert_metric_rows_too_few", "rows": len(mapping_rows)})
    for row in mapping_rows:
        standard = row.get("standard")
        completed = int(row.get("completed_rows") or 0)
        pending = int(row.get("pending_rows") or 0)
        status = row.get("claim_status")
        if completed != 0 or pending <= 0 or status != "pending_expert_review":
            issues.append({"error": "mapping_metric_not_pending_pre_human", "row": row})
        expected_fragment = f"| {standard} | {completed} | {pending} |"
        if expected_fragment not in md_text:
            issues.append({"error": "mapping_table_row_not_synchronized", "expected_fragment": expected_fragment})

    crosswalk_metrics = crosswalk.get("metrics") or {}
    if crosswalk_metrics.get("completed_rows") != 0 or crosswalk_metrics.get("pending_rows") != 220:
        issues.append(
            {
                "error": "crosswalk_metric_not_pending_pre_human",
                "completed_rows": crosswalk_metrics.get("completed_rows"),
                "pending_rows": crosswalk_metrics.get("pending_rows"),
                "claim_status": crosswalk_metrics.get("claim_status"),
            }
        )
    if crosswalk_metrics.get("claim_status") != "pending_crosswalk_expert_review":
        issues.append({"error": "crosswalk_claim_status_unexpected", "actual": crosswalk_metrics.get("claim_status")})
    expected_crosswalk_fragment = (
        f"| {crosswalk_metrics.get('candidate_rows')} | {crosswalk_metrics.get('source_task_count')} | "
        f"{crosswalk_metrics.get('completed_rows')} | {crosswalk_metrics.get('pending_rows')} |"
    )
    if expected_crosswalk_fragment not in md_text:
        issues.append({"error": "crosswalk_table_row_not_synchronized", "expected_fragment": expected_crosswalk_fragment})

    forbidden_final_claim_patterns = [
        "official leaderboard",
        "final human-review efficiency",
        "final paper claims",
        "safe_to_use_as_submission | True",
    ]
    bad_final_claim_patterns = [
        pattern
        for pattern in forbidden_final_claim_patterns
        if pattern in md_text and pattern != "final paper claims"
    ]
    if bad_final_claim_patterns:
        issues.append({"error": "forbidden_final_claim_patterns", "patterns": bad_final_claim_patterns})

    if issues:
        add_check(
            checks,
            "paper_tables_claim_safety",
            "FAIL",
            "Paper tables are missing conservative pre-human claim-safety markers or are not synchronized with pending human/expert gates.",
            {"issues": issues[:50], "markdown": rel(md_path), "latex": rel(tex_path)},
        )
        return
    add_check(
        checks,
        "paper_tables_claim_safety",
        "PASS",
        "Paper tables separate pending human-gold/expert-review results from silver/proxy diagnostics in both Markdown and LaTeX.",
        {
            "markdown": rel(md_path),
            "latex": rel(tex_path),
            "completed_adjudicated_chunks": completed_chunks,
            "gold_item_count_for_readiness": gold_items,
            "mapping_metric_rows": len(mapping_rows),
            "claim_status": "paper_tables_ready_not_submission_claim_evidence",
        },
    )


def validate_data_release_ethics_statement(checks, exp_dir):
    statement_path = exp_dir / "06_release/data_release_ethics_statement.md"
    report_json_path = exp_dir / "06_release/external_resource_license_report.json"
    report_csv_path = exp_dir / "06_release/external_resource_license_report.csv"
    report_md_path = exp_dir / "06_release/external_resource_license_report.md"
    try:
        text = statement_path.read_text(encoding="utf-8")
        report = read_json(report_json_path)
    except Exception as exc:
        add_check(
            checks,
            "data_release_ethics_statement",
            "FAIL",
            "Data release/ethics statement or external resource license report cannot be read.",
            {"statement_path": rel(statement_path), "license_report_path": rel(report_json_path), "error": str(exc)},
        )
        return

    required_patterns = [
        "# CAPE-KG Data Release and Ethics Statement",
        "This document is a release and ethics planning artifact",
        "Current claim status: pending human-gold annotation",
        "Current release status: internal reproducibility package and public-safe skeleton are prepared",
        "Raw source text public release | Restricted pending rights review",
        "Public-safe schema/prompt/script release | Prepared",
        "Synthetic examples | Prepared",
        "Human-gold labels | Pending",
        "IAA and adjudication | Pending",
        "Final paper performance claims | Not yet claimable",
        "External resource license report | Prepared",
        "not substitutes for human-gold evaluation",
        "LLM outputs may hallucinate",
        "Reviewer identities should not be exposed in public artifacts",
        "Do not publish raw domain text unless redistribution rights are explicitly cleared",
    ]
    missing = [pattern for pattern in required_patterns if pattern not in text]
    forbidden_hits = [pattern for pattern in PUBLIC_SAFE_FORBIDDEN_PATTERNS if pattern in text]
    report_issues = []
    if not report_csv_path.exists():
        report_issues.append({"error": "missing_license_report_csv", "path": rel(report_csv_path)})
        csv_rows = []
    else:
        try:
            csv_rows = read_csv_rows(report_csv_path)
        except Exception as exc:
            report_issues.append({"error": "cannot_read_license_report_csv", "path": rel(report_csv_path), "detail": str(exc)})
            csv_rows = []
    if not report_md_path.exists() or report_md_path.stat().st_size == 0:
        report_issues.append({"error": "missing_license_report_markdown", "path": rel(report_md_path)})
    else:
        report_text = report_md_path.read_text(encoding="utf-8", errors="replace")
        for pattern in [
            "# CAPE-KG External Resource License and Citation Report",
            "PAGED",
            "Text2KGBench",
            "Apache-2.0",
            "rights_review_required",
            "not legal advice",
        ]:
            if pattern not in report_text:
                report_issues.append({"error": "license_report_markdown_missing_pattern", "pattern": pattern})
    if report.get("claim_status") != "external_resource_license_report_ready_not_legal_advice":
        report_issues.append({"error": "unexpected_license_report_claim_status", "actual": report.get("claim_status")})
    if int(report.get("issue_count") or 0) != 0:
        report_issues.append({"error": "license_report_has_issues", "issue_count": report.get("issue_count"), "issues": report.get("issues")})
    resources = report.get("resources") or []
    if len(resources) != len(csv_rows):
        report_issues.append({"error": "license_report_json_csv_count_mismatch", "json_rows": len(resources), "csv_rows": len(csv_rows)})
    resources_by_id = {row.get("resource_id"): row for row in resources}
    for resource_id in [
        "PAGED",
        "Text2KGBench",
        "CAPE_public_synthetic_examples",
        "private_bid_proposal_corpus",
        "NCS_standard_layer",
        "PCF_standard_layer",
    ]:
        if resource_id not in resources_by_id:
            report_issues.append({"error": "missing_license_report_resource", "resource_id": resource_id})
    for resource_id in ["PAGED", "Text2KGBench"]:
        row = resources_by_id.get(resource_id) or {}
        if row.get("license_name") != "Apache-2.0":
            report_issues.append({"error": "public_benchmark_license_not_apache_2", "resource_id": resource_id, "actual": row.get("license_name")})
        if not row.get("source_url") or not row.get("paper_url"):
            report_issues.append({"error": "public_benchmark_missing_url", "resource_id": resource_id})
        if not Path(row.get("license_file", "")).exists():
            report_issues.append({"error": "public_benchmark_license_file_missing", "resource_id": resource_id, "path": row.get("license_file")})

    if missing or forbidden_hits or report_issues:
        add_check(
            checks,
            "data_release_ethics_statement",
            "FAIL",
            "Data release and ethics/license release artifacts are missing required claim-safety text, source/license evidence, or public-safe boundaries.",
            {
                "path": rel(statement_path),
                "missing_patterns": missing,
                "forbidden_public_safe_patterns": forbidden_hits,
                "license_report_issues": report_issues,
            },
        )
        return

    add_check(
        checks,
        "data_release_ethics_statement",
        "PASS",
        "Data release and ethics statement plus external resource license report document public-safe release boundaries, benchmark licenses/citations, reproducibility mitigation, human-review privacy, LLM risk, and pending claim status.",
        {
            "path": rel(statement_path),
            "license_report": rel(report_json_path),
            "license_report_csv": rel(report_csv_path),
            "license_report_markdown": rel(report_md_path),
            "claim_status": "data_release_ethics_ready_not_performance_evidence",
            "required_patterns": len(required_patterns),
            "external_resource_count": len(resources),
            "public_benchmark_count": report.get("public_benchmark_count"),
            "rights_review_required_count": report.get("rights_review_required_count"),
        },
    )


def validate_provenance_manifest(checks, exp_dir):
    manifest_path = exp_dir / "06_release/provenance_manifest.json"
    run_index_path = exp_dir / "04_evaluation/provenance_llm_run_index.csv"
    prov_o_ttl_path = exp_dir / "06_release/provenance_prov_o.ttl"
    prov_o_summary_path = exp_dir / "06_release/provenance_prov_o_summary.json"
    prov_o_report_path = exp_dir / "06_release/provenance_prov_o_report.md"
    try:
        manifest = read_json(manifest_path)
    except Exception as exc:
        add_check(
            checks,
            "provenance_manifest",
            "FAIL",
            "Provenance manifest cannot be read.",
            {"path": rel(manifest_path), "error": str(exc)},
        )
        return
    summary = manifest.get("summary") or {}
    issues = []
    if summary.get("missing_required_count") != 0:
        issues.append({"error": "missing_required_provenance_files", "missing": manifest.get("missing_required", [])[:20]})
    if int(summary.get("llm_run_count") or 0) <= 0:
        issues.append({"error": "no_llm_runs_indexed"})
    if int(summary.get("llm_runs_with_valid") or 0) <= 0:
        issues.append({"error": "no_valid_llm_runs_indexed"})
    if not run_index_path.exists() or run_index_path.stat().st_size == 0:
        issues.append({"error": "missing_llm_run_index_csv", "path": rel(run_index_path)})
    if manifest.get("claim_status") != "provenance_manifest_ready_not_human_gold_evidence":
        issues.append({"error": "unexpected_claim_status", "claim_status": manifest.get("claim_status")})
    try:
        prov_o_summary = read_json(prov_o_summary_path)
    except Exception as exc:
        prov_o_summary = {}
        issues.append({"error": "missing_or_unreadable_prov_o_summary", "path": rel(prov_o_summary_path), "detail": str(exc)})
    if not prov_o_ttl_path.exists() or prov_o_ttl_path.stat().st_size == 0:
        issues.append({"error": "missing_prov_o_ttl", "path": rel(prov_o_ttl_path)})
    else:
        ttl_text = prov_o_ttl_path.read_text(encoding="utf-8", errors="replace")
        if "@prefix prov:" not in ttl_text or "cape:LLMExtractionRun" not in ttl_text:
            issues.append({"error": "prov_o_ttl_missing_expected_terms", "path": rel(prov_o_ttl_path)})
    if not prov_o_report_path.exists() or prov_o_report_path.stat().st_size == 0:
        issues.append({"error": "missing_prov_o_report", "path": rel(prov_o_report_path)})
    if prov_o_summary:
        if prov_o_summary.get("claim_status") != "prov_o_export_ready_not_human_gold_evidence":
            issues.append({"error": "unexpected_prov_o_claim_status", "claim_status": prov_o_summary.get("claim_status")})
        for key in ["entity_count", "activity_count", "agent_count", "llm_run_count"]:
            if int(prov_o_summary.get(key) or 0) <= 0:
                issues.append({"error": "prov_o_nonpositive_count", "field": key, "value": prov_o_summary.get(key)})
    if issues:
        add_check(
            checks,
            "provenance_manifest",
            "FAIL",
            "Provenance manifest is incomplete.",
            {"path": rel(manifest_path), "issues": issues},
        )
        return
    add_check(
        checks,
        "provenance_manifest",
        "PASS",
        "Provenance manifest indexes source files, prompts, schemas, LLM runs, evaluation files, human-review handoffs, and release artifacts.",
        {
            "path": rel(manifest_path),
            "run_index": rel(run_index_path),
            "prov_o_ttl": rel(prov_o_ttl_path),
            "prov_o_summary": rel(prov_o_summary_path),
            "prov_o_report": rel(prov_o_report_path),
            "llm_run_count": summary.get("llm_run_count"),
            "llm_runs_with_raw": summary.get("llm_runs_with_raw"),
            "llm_runs_with_valid": summary.get("llm_runs_with_valid"),
            "missing_required_count": summary.get("missing_required_count"),
            "prov_o_entity_count": prov_o_summary.get("entity_count"),
            "prov_o_activity_count": prov_o_summary.get("activity_count"),
            "prov_o_agent_count": prov_o_summary.get("agent_count"),
        },
    )


def validate_layer2_evidence_triple_integrity(checks, exp_dir, outputs_dir):
    nodes_path = outputs_dir / "07_layer2_graph/layer2_nodes.jsonl"
    edges_path = outputs_dir / "07_layer2_graph/layer2_edges.jsonl"
    triples_path = outputs_dir / "06_triples/layer2_triples_schema_valid.jsonl"
    anchors_path = outputs_dir / "06_triples/evidence_anchors.jsonl"
    traceability_path = exp_dir / "06_release/prompt_node_edge_traceability.json"
    rdf_summary_path = outputs_dir / "12_rdf/cape_kg_shacl_validation_summary.json"
    try:
        nodes = read_jsonl(nodes_path)
        edges = read_jsonl(edges_path)
        triples = read_jsonl(triples_path)
        anchors = read_jsonl(anchors_path)
        traceability = read_json(traceability_path)
        rdf_summary = read_json(rdf_summary_path)
    except Exception as exc:
        add_check(
            checks,
            "layer2_evidence_triple_integrity",
            "FAIL",
            "Layer 2 KG, triple, evidence-anchor, or summary files cannot be read.",
            {"error": str(exc)},
        )
        return

    issues = []
    node_ids = [row.get("node_id") for row in nodes]
    edge_ids = [row.get("edge_id") for row in edges]
    triple_ids = [row.get("triple_id") for row in triples]
    anchor_ids = [row.get("evidence_anchor_id") for row in anchors]
    node_id_set = set(node_ids)
    edge_id_set = set(edge_ids)
    triple_by_id = {row.get("triple_id"): row for row in triples}
    anchor_id_set = set(anchor_ids)

    def add_issue(error, **payload):
        if len(issues) < 120:
            row = {"error": error}
            row.update(payload)
            issues.append(row)

    if None in node_id_set or len(node_ids) != len(node_id_set):
        add_issue("node_ids_not_unique_or_missing", rows=len(node_ids), unique=len(node_id_set))
    if None in edge_id_set or len(edge_ids) != len(edge_id_set):
        add_issue("edge_ids_not_unique_or_missing", rows=len(edge_ids), unique=len(edge_id_set))
    if None in set(triple_ids) or len(triple_ids) != len(set(triple_ids)):
        add_issue("triple_ids_not_unique_or_missing", rows=len(triple_ids), unique=len(set(triple_ids)))
    if None in anchor_id_set or len(anchor_ids) != len(anchor_id_set):
        add_issue("evidence_anchor_ids_not_unique_or_missing", rows=len(anchor_ids), unique=len(anchor_id_set))

    trace_counts = (traceability.get("final_kg") or {}).get("counts") or {}
    expected_nodes = trace_counts.get("final_nodes")
    expected_edges = trace_counts.get("final_edges")
    rdf_metrics = (rdf_summary.get("summary") or {})
    if expected_nodes is not None and len(nodes) != expected_nodes:
        add_issue("node_count_mismatch_traceability", expected=expected_nodes, actual=len(nodes))
    if expected_edges is not None and len(edges) != expected_edges:
        add_issue("edge_count_mismatch_traceability", expected=expected_edges, actual=len(edges))
    if int(rdf_metrics.get("node_count") or -1) != len(nodes):
        add_issue("node_count_mismatch_rdf", rdf=rdf_metrics.get("node_count"), actual=len(nodes))
    if int(rdf_metrics.get("edge_count") or -1) != len(edges):
        add_issue("edge_count_mismatch_rdf", rdf=rdf_metrics.get("edge_count"), actual=len(edges))
    if len(triples) != len(edges):
        add_issue("triple_edge_count_mismatch", triples=len(triples), edges=len(edges))

    for node in nodes:
        node_id = node.get("node_id")
        evidence_ids = as_list(node.get("evidence_anchor_ids"))
        if node.get("layer") != "Layer2":
            add_issue("node_not_layer2", node_id=node_id, layer=node.get("layer"))
        if not evidence_ids:
            add_issue("node_missing_evidence_anchor_ids", node_id=node_id)
        for evidence_id in evidence_ids:
            if evidence_id not in anchor_id_set:
                add_issue("node_unknown_evidence_anchor", node_id=node_id, evidence_anchor_id=evidence_id)

    referenced_triples = []
    for edge in edges:
        edge_id = edge.get("edge_id")
        source_id = edge.get("source_id")
        target_id = edge.get("target_id")
        predicate = edge.get("predicate")
        evidence_ids = as_list(edge.get("evidence_anchor_ids"))
        source_triple_ids = as_list(edge.get("source_triple_ids"))
        if source_id not in node_id_set:
            add_issue("edge_unknown_source_node", edge_id=edge_id, source_id=source_id)
        if target_id not in node_id_set:
            add_issue("edge_unknown_target_node", edge_id=edge_id, target_id=target_id)
        if not evidence_ids:
            add_issue("edge_missing_evidence_anchor_ids", edge_id=edge_id)
        for evidence_id in evidence_ids:
            if evidence_id not in anchor_id_set:
                add_issue("edge_unknown_evidence_anchor", edge_id=edge_id, evidence_anchor_id=evidence_id)
        if not source_triple_ids:
            add_issue("edge_missing_source_triple_ids", edge_id=edge_id)
        for triple_id in source_triple_ids:
            referenced_triples.append(triple_id)
            triple = triple_by_id.get(triple_id)
            if not triple:
                add_issue("edge_unknown_source_triple", edge_id=edge_id, triple_id=triple_id)
                continue
            subject = triple.get("subject") or {}
            obj = triple.get("object") or {}
            triple_evidence = triple.get("evidence") or {}
            triple_evidence_ids = set()
            for part in [subject, obj]:
                evidence_id = part.get("evidence_anchor_id")
                if evidence_id:
                    triple_evidence_ids.add(evidence_id)
                    if evidence_id not in anchor_id_set:
                        add_issue("triple_unknown_component_evidence_anchor", triple_id=triple_id, evidence_anchor_id=evidence_id)
            for sentence_id in as_list(triple_evidence.get("sentence_ids")):
                evidence_id = f"EA-{sentence_id}"
                triple_evidence_ids.add(evidence_id)
                if evidence_id not in anchor_id_set:
                    add_issue("triple_unknown_sentence_evidence_anchor", triple_id=triple_id, evidence_anchor_id=evidence_id)
            if subject.get("canonical_id") != source_id:
                add_issue("triple_subject_endpoint_mismatch", edge_id=edge_id, triple_id=triple_id, triple_subject=subject.get("canonical_id"), edge_source=source_id)
            if obj.get("canonical_id") != target_id:
                add_issue("triple_object_endpoint_mismatch", edge_id=edge_id, triple_id=triple_id, triple_object=obj.get("canonical_id"), edge_target=target_id)
            if triple.get("predicate") != predicate:
                add_issue("triple_predicate_mismatch", edge_id=edge_id, triple_id=triple_id, triple_predicate=triple.get("predicate"), edge_predicate=predicate)
            if evidence_ids and triple_evidence_ids and not (set(evidence_ids) & triple_evidence_ids):
                add_issue("edge_triple_evidence_anchor_disjoint", edge_id=edge_id, triple_id=triple_id)

    referenced_triple_set = set(referenced_triples)
    if len(referenced_triples) != len(referenced_triple_set):
        add_issue("source_triple_ids_referenced_more_than_once", references=len(referenced_triples), unique=len(referenced_triple_set))
    unreferenced_triples = sorted(set(triple_ids) - referenced_triple_set)
    if unreferenced_triples:
        add_issue("schema_valid_triples_not_referenced_by_final_edges", count=len(unreferenced_triples), sample=unreferenced_triples[:10])

    if issues:
        add_check(
            checks,
            "layer2_evidence_triple_integrity",
            "FAIL",
            "Layer 2 node/edge evidence anchors or source triples are not internally consistent.",
            {"issues": issues},
        )
        return

    add_check(
        checks,
        "layer2_evidence_triple_integrity",
        "PASS",
        "Final Layer 2 nodes/edges, source triples, and evidence anchors are internally consistent.",
        {
            "nodes": len(nodes),
            "edges": len(edges),
            "schema_valid_triples": len(triples),
            "evidence_anchors": len(anchors),
            "nodes_with_evidence": len(nodes),
            "edges_with_evidence": len(edges),
            "edges_with_source_triples": len(edges),
            "unreferenced_schema_valid_triples": 0,
        },
    )


def validate_evidence_graph_projection(checks, outputs_dir):
    nodes_path = outputs_dir / "07_layer2_graph/layer2_nodes.jsonl"
    edges_path = outputs_dir / "07_layer2_graph/layer2_edges.jsonl"
    anchors_path = outputs_dir / "06_triples/evidence_anchors.jsonl"
    projection_nodes_path = outputs_dir / "13_evidence_graph/evidence_anchor_nodes.jsonl"
    projection_nodes_csv_path = outputs_dir / "13_evidence_graph/evidence_anchor_nodes.csv"
    projection_edges_path = outputs_dir / "13_evidence_graph/evidenced_by_edges.jsonl"
    projection_edges_csv_path = outputs_dir / "13_evidence_graph/evidenced_by_edges.csv"
    summary_path = outputs_dir / "13_evidence_graph/evidence_graph_projection_summary.json"
    report_path = outputs_dir / "13_evidence_graph/evidence_graph_projection_report.md"
    try:
        nodes = read_jsonl(nodes_path)
        edges = read_jsonl(edges_path)
        anchors = read_jsonl(anchors_path)
        projection_nodes = read_jsonl(projection_nodes_path)
        projection_edges = read_jsonl(projection_edges_path)
        projection_nodes_csv = read_csv_rows(projection_nodes_csv_path)
        projection_edges_csv = read_csv_rows(projection_edges_csv_path)
        summary = read_json(summary_path)
        report_text = report_path.read_text(encoding="utf-8")
    except Exception as exc:
        add_check(
            checks,
            "evidence_graph_projection_integrity",
            "FAIL",
            "EvidenceAnchor/EVIDENCED_BY projection files cannot be read.",
            {"error": str(exc)},
        )
        return

    issues = []
    node_ids = {row.get("node_id") for row in nodes}
    kg_edge_ids = {row.get("edge_id") for row in edges}
    anchor_ids = {row.get("evidence_anchor_id") for row in anchors}
    used_anchor_ids = set()
    expected_node_evidence_edges = 0
    expected_kg_edge_evidence_edges = 0
    for row in nodes:
        evidence_ids = [anchor_id for anchor_id in as_list(row.get("evidence_anchor_ids")) if anchor_id]
        used_anchor_ids.update(evidence_ids)
        expected_node_evidence_edges += len(evidence_ids)
    for row in edges:
        evidence_ids = [anchor_id for anchor_id in as_list(row.get("evidence_anchor_ids")) if anchor_id]
        used_anchor_ids.update(evidence_ids)
        expected_kg_edge_evidence_edges += len(evidence_ids)

    projection_node_ids = [row.get("node_id") for row in projection_nodes]
    projection_node_id_set = set(projection_node_ids)
    projection_edge_ids = [row.get("evidence_edge_id") for row in projection_edges]
    projection_edge_id_set = set(projection_edge_ids)
    source_kind_counts = {}
    for row in projection_edges:
        source_kind = row.get("source_kind")
        source_kind_counts[source_kind] = source_kind_counts.get(source_kind, 0) + 1

    def add_issue(error, **payload):
        if len(issues) < 120:
            row = {"error": error}
            row.update(payload)
            issues.append(row)

    expected_claim_status = "evidence_graph_projection_ready_not_human_gold_span_claim"
    if summary.get("claim_status") != expected_claim_status:
        add_issue("unexpected_claim_status", expected=expected_claim_status, actual=summary.get("claim_status"))
    if summary.get("source_text_included") is not False:
        add_issue("source_text_included_not_false", actual=summary.get("source_text_included"))
    report_text_lower = report_text.lower()
    if "source text omitted" not in report_text_lower and "text is intentionally omitted" not in report_text_lower:
        add_issue("report_missing_source_text_omitted_notice")
    if len(projection_node_ids) != len(projection_node_id_set):
        add_issue("projection_node_ids_not_unique", rows=len(projection_node_ids), unique=len(projection_node_id_set))
    if len(projection_edge_ids) != len(projection_edge_id_set):
        add_issue("projection_edge_ids_not_unique", rows=len(projection_edge_ids), unique=len(projection_edge_id_set))

    unknown_used_anchor_ids = sorted(used_anchor_ids - anchor_ids)
    if unknown_used_anchor_ids:
        add_issue("used_anchor_ids_missing_from_catalog", count=len(unknown_used_anchor_ids), sample=unknown_used_anchor_ids[:10])
    missing_projection_nodes = sorted(used_anchor_ids - projection_node_id_set)
    extra_projection_nodes = sorted(projection_node_id_set - used_anchor_ids)
    if missing_projection_nodes:
        add_issue("used_anchor_ids_missing_from_projection", count=len(missing_projection_nodes), sample=missing_projection_nodes[:10])
    if extra_projection_nodes:
        add_issue("projection_has_unused_anchor_nodes", count=len(extra_projection_nodes), sample=extra_projection_nodes[:10])

    expected_counts = {
        "layer2_node_count": len(nodes),
        "layer2_edge_count": len(edges),
        "evidence_anchor_catalog_count": len(anchor_ids),
        "used_evidence_anchor_count": len(used_anchor_ids),
        "evidence_anchor_node_count": len(projection_nodes),
        "evidenced_by_edge_count": len(projection_edges),
        "kg_node_evidenced_by_edge_count": expected_node_evidence_edges,
        "kg_edge_evidenced_by_edge_count": expected_kg_edge_evidence_edges,
        "unknown_used_evidence_anchor_count": len(unknown_used_anchor_ids),
    }
    for key, expected in expected_counts.items():
        if summary.get(key) != expected:
            add_issue("summary_count_mismatch", field=key, expected=expected, actual=summary.get(key))
    if len(projection_nodes_csv) != len(projection_nodes):
        add_issue("projection_node_csv_jsonl_count_mismatch", csv=len(projection_nodes_csv), jsonl=len(projection_nodes))
    if len(projection_edges_csv) != len(projection_edges):
        add_issue("projection_edge_csv_jsonl_count_mismatch", csv=len(projection_edges_csv), jsonl=len(projection_edges))
    if source_kind_counts.get("KGNode", 0) != expected_node_evidence_edges:
        add_issue("kg_node_evidenced_by_count_mismatch", expected=expected_node_evidence_edges, actual=source_kind_counts.get("KGNode", 0))
    if source_kind_counts.get("KGEdge", 0) != expected_kg_edge_evidence_edges:
        add_issue("kg_edge_evidenced_by_count_mismatch", expected=expected_kg_edge_evidence_edges, actual=source_kind_counts.get("KGEdge", 0))

    for row in projection_nodes:
        node_id = row.get("node_id")
        if row.get("type") != "EvidenceAnchor":
            add_issue("projection_node_type_not_evidence_anchor", node_id=node_id, actual=row.get("type"))
        if row.get("layer") != "EvidenceProjection":
            add_issue("projection_node_layer_not_evidence_projection", node_id=node_id, actual=row.get("layer"))
        if row.get("text_included") is not False:
            add_issue("projection_node_text_included_not_false", node_id=node_id, actual=row.get("text_included"))
        if "text" in row or "source_text" in row:
            add_issue("projection_node_contains_source_text_field", node_id=node_id)
        if node_id not in anchor_ids:
            add_issue("projection_node_missing_from_anchor_catalog", node_id=node_id)

    for row in projection_edges:
        source_kind = row.get("source_kind")
        source_id = row.get("source_id")
        target_id = row.get("target_id")
        if row.get("predicate") != "EVIDENCED_BY":
            add_issue("projection_edge_predicate_not_evidenced_by", edge_id=row.get("evidence_edge_id"), actual=row.get("predicate"))
        if row.get("target_type") != "EvidenceAnchor":
            add_issue("projection_edge_target_type_not_evidence_anchor", edge_id=row.get("evidence_edge_id"), actual=row.get("target_type"))
        if target_id not in projection_node_id_set:
            add_issue("projection_edge_unknown_target_anchor", edge_id=row.get("evidence_edge_id"), target_id=target_id)
        if source_kind == "KGNode":
            if source_id not in node_ids:
                add_issue("projection_edge_unknown_source_node", edge_id=row.get("evidence_edge_id"), source_id=source_id)
        elif source_kind == "KGEdge":
            if source_id not in kg_edge_ids:
                add_issue("projection_edge_unknown_source_edge", edge_id=row.get("evidence_edge_id"), source_id=source_id)
        else:
            add_issue("projection_edge_unknown_source_kind", edge_id=row.get("evidence_edge_id"), source_kind=source_kind)

    if issues:
        add_check(
            checks,
            "evidence_graph_projection_integrity",
            "FAIL",
            "EvidenceAnchor/EVIDENCED_BY projection is not internally aligned with Layer 2 evidence anchors.",
            {"issues": issues},
        )
        return

    add_check(
        checks,
        "evidence_graph_projection_integrity",
        "PASS",
        "EvidenceAnchor nodes and EVIDENCED_BY edges match Layer 2 evidence_anchor_ids; source text is omitted.",
        {
            "evidence_anchor_nodes": len(projection_nodes),
            "evidenced_by_edges": len(projection_edges),
            "kg_node_evidenced_by_edges": expected_node_evidence_edges,
            "kg_edge_evidenced_by_edges": expected_kg_edge_evidence_edges,
            "unknown_used_evidence_anchor_count": 0,
            "source_text_included": False,
        },
    )


def validate_rdf_shacl_export(checks, outputs_dir):
    summary_path = outputs_dir / "12_rdf/cape_kg_shacl_validation_summary.json"
    rdf_path = outputs_dir / "12_rdf/cape_kg_layer2.ttl"
    shapes_path = outputs_dir / "12_rdf/cape_kg_runtime_shapes.shacl.ttl"
    report_path = outputs_dir / "12_rdf/cape_kg_shacl_validation_report.md"
    try:
        summary = read_json(summary_path)
    except Exception as exc:
        add_check(
            checks,
            "rdf_shacl_export",
            "FAIL",
            "RDF/SHACL-style validation summary cannot be read.",
            {"path": rel(summary_path), "error": str(exc)},
        )
        return

    issues = []
    for path in [rdf_path, shapes_path, report_path]:
        if not path.exists() or path.stat().st_size == 0:
            issues.append({"error": "missing_or_empty_file", "path": rel(path)})
    if summary.get("overall_status") != "PASS":
        issues.append({"error": "summary_not_pass", "overall_status": summary.get("overall_status")})
    if summary.get("claim_status") != "rdf_shacl_style_validation_pass_not_human_gold":
        issues.append({"error": "unexpected_claim_status", "claim_status": summary.get("claim_status")})
    metrics = summary.get("summary") or {}
    if int(metrics.get("node_count") or 0) <= 0:
        issues.append({"error": "nonpositive_node_count", "actual": metrics.get("node_count")})
    if int(metrics.get("edge_count") or 0) <= 0:
        issues.append({"error": "nonpositive_edge_count", "actual": metrics.get("edge_count")})
    if int(metrics.get("error_count") or 0) != 0:
        issues.append({"error": "rdf_shacl_validation_errors", "actual": metrics.get("error_count")})
    if rdf_path.exists():
        ttl_head = rdf_path.read_text(encoding="utf-8", errors="replace")[:4000]
        if "@prefix cape:" not in ttl_head or "cape:KGEdge" not in rdf_path.read_text(encoding="utf-8", errors="replace"):
            issues.append({"error": "rdf_ttl_missing_expected_terms", "path": rel(rdf_path)})
    if shapes_path.exists():
        shapes_text = shapes_path.read_text(encoding="utf-8", errors="replace")
        if "@prefix sh:" not in shapes_text or "cape:EvidenceGroundedEdgeShape" not in shapes_text:
            issues.append({"error": "runtime_shapes_missing_expected_terms", "path": rel(shapes_path)})

    if issues:
        add_check(
            checks,
            "rdf_shacl_export",
            "FAIL",
            "RDF export or SHACL-style validation artifacts are incomplete.",
            {"issues": issues},
        )
        return
    add_check(
        checks,
        "rdf_shacl_export",
        "PASS",
        "Layer 2 KG RDF export and SHACL-style validation artifacts are present and pass structural checks.",
        {
            "rdf_ttl": rel(rdf_path),
            "runtime_shapes": rel(shapes_path),
            "summary": rel(summary_path),
            "report": rel(report_path),
            "node_count": metrics.get("node_count"),
            "edge_count": metrics.get("edge_count"),
            "rdf_statement_count": metrics.get("rdf_statement_count"),
            "error_count": metrics.get("error_count"),
        },
    )


def validate_human_review_return_preflight(checks, exp_dir):
    preflight_path = exp_dir / "06_release/human_review_return_preflight.json"
    try:
        preflight = read_json(preflight_path)
    except Exception as exc:
        add_check(
            checks,
            "human_review_return_preflight",
            "FAIL",
            "Human review return preflight summary cannot be read.",
            {"path": rel(preflight_path), "error": str(exc)},
        )
        return

    status = preflight.get("overall_status")
    annotation = preflight.get("annotation_returns") or {}
    adjudication = preflight.get("adjudication_return") or {}
    mapping = preflight.get("mapping_return") or {}
    crosswalk = preflight.get("crosswalk_return") or {}
    active_review = preflight.get("active_review_effort_return") or {}
    error_count = (
        int(annotation.get("error_count") or 0)
        + int(adjudication.get("error_count") or 0)
        + int(mapping.get("error_count") or 0)
        + int(crosswalk.get("error_count") or 0)
        + int(active_review.get("error_count") or 0)
    )
    present_return_files = int(annotation.get("present_files") or 0)
    present_return_files += 1 if adjudication.get("present") else 0
    present_return_files += 1 if mapping.get("present") else 0
    present_return_files += 1 if crosswalk.get("present") else 0
    present_return_files += 1 if active_review.get("present") else 0
    minimum_ready = bool(
        annotation.get("ready_for_minimum_import")
        and adjudication.get("ready_for_minimum_adjudication_import")
    )
    mapping_ready = bool(mapping.get("ready_for_expert_metric_import"))
    crosswalk_ready = bool(crosswalk.get("ready_for_crosswalk_metric_import"))
    active_ready = bool(active_review.get("ready_for_effort_metric_import"))
    policy = preflight.get("validation_policy") or {}
    if not present_return_files:
        expected_apply_scope = "no_return_files"
    elif minimum_ready and mapping_ready and crosswalk_ready and active_ready:
        expected_apply_scope = "all_minimum_and_optional_returns_ready"
    elif minimum_ready:
        expected_apply_scope = "minimum_annotation_adjudication_ready_optional_pending"
    else:
        expected_apply_scope = "partial_valid_returns_only"
    scope_issues = []
    if preflight.get("present_human_return_files") != present_return_files:
        scope_issues.append(
            {
                "error": "present_human_return_files_mismatch",
                "expected": present_return_files,
                "actual": preflight.get("present_human_return_files"),
            }
        )
    if preflight.get("apply_scope") != expected_apply_scope:
        scope_issues.append(
            {
                "error": "apply_scope_mismatch",
                "expected": expected_apply_scope,
                "actual": preflight.get("apply_scope"),
            }
        )
    if preflight.get("minimum_paper_gate_ready_after_preflight") is not minimum_ready:
        scope_issues.append(
            {
                "error": "minimum_gate_readiness_mismatch",
                "expected": minimum_ready,
                "actual": preflight.get("minimum_paper_gate_ready_after_preflight"),
            }
        )
    if preflight.get("optional_mapping_ready_after_preflight") is not mapping_ready:
        scope_issues.append(
            {
                "error": "mapping_readiness_mismatch",
                "expected": mapping_ready,
                "actual": preflight.get("optional_mapping_ready_after_preflight"),
            }
        )
    if preflight.get("optional_crosswalk_ready_after_preflight") is not crosswalk_ready:
        scope_issues.append(
            {
                "error": "crosswalk_readiness_mismatch",
                "expected": crosswalk_ready,
                "actual": preflight.get("optional_crosswalk_ready_after_preflight"),
            }
        )
    if preflight.get("optional_active_effort_ready_after_preflight") is not active_ready:
        scope_issues.append(
            {
                "error": "active_effort_readiness_mismatch",
                "expected": active_ready,
                "actual": preflight.get("optional_active_effort_ready_after_preflight"),
            }
        )
    required_policy_flags = [
        "annotator_file_identity_check",
        "completed_candidate_coverage_check",
        "needs_adjudication_comments_required",
        "completed_adjudication_adjudicator_id_required",
        "mapping_completed_rows_require_explanation_quality_score",
        "crosswalk_completed_rows_require_utility_and_explanation_scores",
    ]
    missing_policy_flags = [flag for flag in required_policy_flags if policy.get(flag) is not True]
    if missing_policy_flags:
        scope_issues.append(
            {
                "error": "human_preflight_validation_policy_missing",
                "missing_flags": missing_policy_flags,
            }
        )
    report_path = exp_dir / "06_release/human_review_return_preflight.md"
    report_text = report_path.read_text(encoding="utf-8", errors="replace") if report_path.exists() else ""
    if (
        not report_path.exists()
        or "CAPE-KG Human Review Return Preflight" not in report_text
        or "## Validation Policy" not in report_text
        or "Mapping completed rows require explanation quality score" not in report_text
        or "Crosswalk completed rows require utility and explanation scores" not in report_text
    ):
        scope_issues.append({"error": "missing_or_invalid_human_return_preflight_report", "path": rel(report_path)})
    if status not in ALLOWED_RETURN_PREFLIGHT_STATUSES or error_count or scope_issues:
        add_check(
            checks,
            "human_review_return_preflight",
            "FAIL",
            "Human review return preflight is not in an allowed non-error state.",
            {
                "path": rel(preflight_path),
                "overall_status": status,
                "annotation_error_count": annotation.get("error_count"),
                "adjudication_error_count": adjudication.get("error_count"),
                "mapping_error_count": mapping.get("error_count"),
                "crosswalk_error_count": crosswalk.get("error_count"),
                "active_review_error_count": active_review.get("error_count"),
                "scope_issues": scope_issues,
            },
        )
        return
    add_check(
        checks,
        "human_review_return_preflight",
        "PASS",
        "Human review return preflight is configured and currently has no validation errors.",
        {
            "path": rel(preflight_path),
            "overall_status": status,
            "present_human_return_files": preflight.get("present_human_return_files"),
            "apply_scope": preflight.get("apply_scope"),
            "minimum_paper_gate_ready_after_preflight": preflight.get("minimum_paper_gate_ready_after_preflight"),
            "optional_mapping_ready_after_preflight": preflight.get("optional_mapping_ready_after_preflight"),
            "optional_crosswalk_ready_after_preflight": preflight.get("optional_crosswalk_ready_after_preflight"),
            "optional_active_effort_ready_after_preflight": preflight.get("optional_active_effort_ready_after_preflight"),
            "validation_policy": policy,
            "annotation_present_files": annotation.get("present_files"),
            "annotation_expected_files": annotation.get("expected_files"),
            "paired_completed_chunks": annotation.get("paired_completed_chunks"),
            "adjudication_reviewed_file_present": adjudication.get("present"),
            "mapping_reviewed_rows": mapping.get("reviewed_rows"),
            "crosswalk_reviewed_rows": crosswalk.get("reviewed_rows"),
            "active_review_timed_rows": active_review.get("timed_review_rows"),
        },
    )


def validate_strong_review_return_preflight(checks, exp_dir):
    preflight_path = exp_dir / "06_release/strong_review_return_preflight.json"
    report_path = exp_dir / "06_release/strong_review_return_preflight.md"
    try:
        preflight = read_json(preflight_path)
    except Exception as exc:
        add_check(
            checks,
            "strong_review_return_preflight",
            "FAIL",
            "Optional strong 300+ return preflight summary cannot be read.",
            {"path": rel(preflight_path), "error": str(exc)},
        )
        return

    status = preflight.get("overall_status")
    summary = preflight.get("summary") or {}
    annotation = preflight.get("annotation_returns") or {}
    adjudication = preflight.get("adjudication_return") or {}
    policy = preflight.get("validation_policy") or {}
    error_count = int(summary.get("error_count") or 0)
    issues = []
    if status not in ALLOWED_STRONG_RETURN_PREFLIGHT_STATUSES:
        issues.append({"error": "unexpected_status", "status": status})
    if error_count:
        issues.append({"error": "strong_preflight_errors", "error_count": error_count})
    if int(summary.get("expected_review_units") or 0) < 300:
        issues.append({"error": "expected_review_units_below_300", "expected_review_units": summary.get("expected_review_units")})
    required_policy_flags = [
        "annotator_file_identity_check",
        "completed_candidate_coverage_check",
        "needs_adjudication_comments_required",
        "completed_adjudication_adjudicator_id_required",
    ]
    missing_policy_flags = [flag for flag in required_policy_flags if policy.get(flag) is not True]
    if missing_policy_flags:
        issues.append({"error": "strong_preflight_validation_policy_missing", "missing_flags": missing_policy_flags})
    report_text = report_path.read_text(encoding="utf-8", errors="replace") if report_path.exists() else ""
    if (
        not report_path.exists()
        or "Optional Strong 300+ Return Preflight" not in report_text
        or "## Validation Policy" not in report_text
        or "Completed candidate coverage check" not in report_text
    ):
        issues.append({"error": "missing_or_invalid_markdown_report", "path": rel(report_path)})
    if issues:
        add_check(
            checks,
            "strong_review_return_preflight",
            "FAIL",
            "Optional strong 300+ return preflight is inconsistent.",
            {"path": rel(preflight_path), "issues": issues[:20]},
        )
        return
    add_check(
        checks,
        "strong_review_return_preflight",
        "PASS",
        "Optional strong 300+ return preflight is configured and currently has no validation errors.",
        {
            "path": rel(preflight_path),
            "report": rel(report_path),
            "overall_status": status,
            "expected_review_units": summary.get("expected_review_units"),
            "paired_completed_chunks": summary.get("paired_completed_chunks"),
            "annotator_A_present": (annotation.get("A") or {}).get("present"),
            "annotator_B_present": (annotation.get("B") or {}).get("present"),
            "adjudication_present": adjudication.get("present"),
            "ready_for_strong_iaa": summary.get("ready_for_strong_iaa"),
            "ready_for_strong_claim_after_import": summary.get("ready_for_strong_claim_after_import"),
            "validation_policy": policy,
        },
    )


def validate_human_gate_action_plan(checks, exp_dir):
    release_dir = exp_dir / "06_release"
    review_dir = exp_dir / "05_review"
    plan_path = release_dir / "human_gate_action_plan.json"
    report_path = release_dir / "human_gate_action_plan.md"
    returns_csv_path = review_dir / "human_gate_required_returns.csv"
    gate_matrix_csv_path = review_dir / "human_review_gate_dependency_matrix.csv"
    preflight_path = release_dir / "human_review_return_preflight.json"
    try:
        plan = read_json(plan_path)
        preflight = read_json(preflight_path)
    except Exception as exc:
        add_check(
            checks,
            "human_gate_action_plan",
            "FAIL",
            "Human gate action plan or preflight JSON cannot be read.",
            {"error": str(exc), "plan_path": rel(plan_path), "preflight_path": rel(preflight_path)},
        )
        return

    issues = []
    if plan.get("claim_status") != "human_gate_action_plan_ready_pending_returns":
        issues.append({"error": "unexpected_claim_status", "actual": plan.get("claim_status")})
    if not report_path.exists():
        issues.append({"error": "missing_markdown_report", "path": rel(report_path)})
    if not returns_csv_path.exists():
        issues.append({"error": "missing_required_returns_csv", "path": rel(returns_csv_path)})
    if not gate_matrix_csv_path.exists():
        issues.append({"error": "missing_gate_dependency_matrix_csv", "path": rel(gate_matrix_csv_path)})

    required_returns = plan.get("required_return_files") or []
    minimum_returns = [row for row in required_returns if truthy_present(row.get("required_for_minimum", True))]
    optional_strong_returns = [row for row in required_returns if not truthy_present(row.get("required_for_minimum", True))]
    minimum_return_present = sum(1 for row in minimum_returns if truthy_present(row.get("present")))
    optional_strong_present = sum(1 for row in optional_strong_returns if truthy_present(row.get("present")))
    gate_matrix = plan.get("gate_dependency_matrix") or []
    gate_matrix_csv_rows = []
    if gate_matrix_csv_path.exists():
        try:
            gate_matrix_csv_rows = read_csv_rows(gate_matrix_csv_path)
        except Exception as exc:
            issues.append({"error": "cannot_read_gate_dependency_matrix_csv", "path": rel(gate_matrix_csv_path), "detail": str(exc)})
    annotation_returns = (preflight.get("annotation_returns") or {}).get("files") or []
    adjudication_return = preflight.get("adjudication_return") or {}
    mapping_return = preflight.get("mapping_return") or {}
    crosswalk_return = preflight.get("crosswalk_return") or {}
    active_review_return = preflight.get("active_review_effort_return") or {}
    expected_return_count = (
        len(annotation_returns)
        + (1 if adjudication_return else 0)
        + (1 if mapping_return else 0)
        + (1 if crosswalk_return else 0)
        + (1 if active_review_return else 0)
    )
    if len(required_returns) != expected_return_count:
        issues.append(
            {
                "error": "required_return_count_mismatch",
                "plan_count": len(required_returns),
                "preflight_expected_count": expected_return_count,
            }
        )

    expected_gate_ids = [
        "min.iaa",
        "min.gold_chunks",
        "min.gold_items",
        "min.proposed",
        "mapping.expert_review",
        "crosswalk.expert_review",
        "strong.active_review_effort",
    ]
    minimum_gate_ids = {"min.iaa", "min.gold_chunks", "min.gold_items", "min.proposed"}
    gate_rows_by_id = {row.get("gate_id"): row for row in gate_matrix}
    csv_gate_rows_by_id = {row.get("gate_id"): row for row in gate_matrix_csv_rows}
    if [row.get("gate_id") for row in gate_matrix] != expected_gate_ids:
        issues.append(
            {
                "error": "gate_dependency_ids_mismatch",
                "expected": expected_gate_ids,
                "actual": [row.get("gate_id") for row in gate_matrix],
            }
        )
    if gate_matrix_csv_rows and [row.get("gate_id") for row in gate_matrix_csv_rows] != expected_gate_ids:
        issues.append(
            {
                "error": "gate_dependency_csv_ids_mismatch",
                "expected": expected_gate_ids,
                "actual": [row.get("gate_id") for row in gate_matrix_csv_rows],
            }
        )
    if gate_matrix_csv_rows and len(gate_matrix_csv_rows) != len(gate_matrix):
        issues.append(
            {
                "error": "gate_dependency_json_csv_count_mismatch",
                "json_rows": len(gate_matrix),
                "csv_rows": len(gate_matrix_csv_rows),
            }
        )
    for gate_id in expected_gate_ids:
        row = gate_rows_by_id.get(gate_id)
        csv_row = csv_gate_rows_by_id.get(gate_id)
        if not row:
            issues.append({"error": "missing_gate_dependency_row", "gate_id": gate_id})
            continue
        expected_required = "yes" if gate_id in minimum_gate_ids else "no"
        if row.get("required_for_minimum") != expected_required:
            issues.append(
                {
                    "error": "gate_dependency_required_flag_mismatch",
                    "gate_id": gate_id,
                    "expected": expected_required,
                    "actual": row.get("required_for_minimum"),
                }
            )
        if csv_row and csv_row.get("required_for_minimum") != row.get("required_for_minimum"):
            issues.append(
                {
                    "error": "gate_dependency_csv_json_required_flag_mismatch",
                    "gate_id": gate_id,
                    "json": row.get("required_for_minimum"),
                    "csv": csv_row.get("required_for_minimum"),
                }
            )
        for field in ["unlock_condition", "current_progress", "required_return_files", "post_return_command", "next_action"]:
            if not row.get(field):
                issues.append({"error": "gate_dependency_missing_field_value", "gate_id": gate_id, "field": field})

    gate_missing_fragments = {
        "min.iaa": [
            "annotator_A_full_120_priority_batch_001.reviewed.jsonl",
            "annotator_B_full_120_priority_batch_005.reviewed.jsonl",
        ],
        "min.gold_chunks": ["adjudication_edited.jsonl"],
        "min.gold_items": ["adjudication_edited.jsonl"],
        "min.proposed": ["adjudication_edited.jsonl"],
        "mapping.expert_review": ["mapping_review_items.reviewed.jsonl"],
        "crosswalk.expert_review": ["crosswalk_review_items.reviewed.jsonl"],
        "strong.active_review_effort": ["active_review_human_effort.reviewed.csv"],
    }
    for gate_id, fragments in gate_missing_fragments.items():
        row = gate_rows_by_id.get(gate_id) or {}
        missing_text = row.get("blocking_return_files_missing") or ""
        required_text = row.get("required_return_files") or ""
        combined_text = missing_text + " " + required_text
        for fragment in fragments:
            if fragment not in combined_text:
                issues.append(
                    {
                        "error": "gate_dependency_missing_expected_return_file_reference",
                        "gate_id": gate_id,
                        "fragment": fragment,
                    }
                )

    annotation_plan_rows = [row for row in required_returns if row.get("task_type") == "human_gold_annotation"]
    adjudication_plan_rows = [row for row in required_returns if row.get("task_type") == "human_gold_adjudication"]
    mapping_plan_rows = [row for row in required_returns if row.get("task_type") == "mapping_expert_review"]
    crosswalk_plan_rows = [row for row in required_returns if row.get("task_type") == "crosswalk_expert_review"]
    active_review_plan_rows = [row for row in required_returns if row.get("task_type") == "active_review_human_effort"]
    if len(annotation_plan_rows) != len(annotation_returns):
        issues.append(
            {
                "error": "annotation_return_count_mismatch",
                "plan_count": len(annotation_plan_rows),
                "preflight_count": len(annotation_returns),
            }
        )
    if adjudication_return and len(adjudication_plan_rows) != 1:
        issues.append({"error": "adjudication_return_count_mismatch", "plan_count": len(adjudication_plan_rows)})
    if mapping_return and len(mapping_plan_rows) != 1:
        issues.append({"error": "mapping_return_count_mismatch", "plan_count": len(mapping_plan_rows)})
    if crosswalk_return and len(crosswalk_plan_rows) != 1:
        issues.append({"error": "crosswalk_return_count_mismatch", "plan_count": len(crosswalk_plan_rows)})
    if active_review_return and len(active_review_plan_rows) != 1:
        issues.append({"error": "active_review_return_count_mismatch", "plan_count": len(active_review_plan_rows)})

    by_reviewed = {row.get("reviewed_file"): row for row in required_returns}
    for item in annotation_returns:
        row = by_reviewed.get(item.get("reviewed_file"))
        if not row:
            issues.append({"error": "missing_annotation_reviewed_file_entry", "reviewed_file": item.get("reviewed_file")})
            continue
        if str(row.get("present")).lower() not in {"yes", "no"}:
            issues.append({"error": "invalid_present_value", "reviewed_file": row.get("reviewed_file"), "present": row.get("present")})
        expected_present = "yes" if item.get("present") else "no"
        if row.get("present") != expected_present or row.get("status") != item.get("status"):
            issues.append(
                {
                    "error": "annotation_status_mismatch",
                    "reviewed_file": item.get("reviewed_file"),
                    "plan_present": row.get("present"),
                    "preflight_present": expected_present,
                    "plan_status": row.get("status"),
                    "preflight_status": item.get("status"),
                }
            )
        if not Path(row.get("input_file", "")).exists():
            issues.append({"error": "missing_annotation_input_file", "path": row.get("input_file")})
            if not Path(row.get("target_file", "")).exists():
                issues.append({"error": "missing_annotation_target_file", "path": row.get("target_file")})

    if adjudication_return:
        adjudication_row = by_reviewed.get(adjudication_return.get("reviewed_file"))
        if not adjudication_row:
            issues.append({"error": "missing_adjudication_reviewed_file_entry", "reviewed_file": adjudication_return.get("reviewed_file")})
        else:
            expected_present = "yes" if adjudication_return.get("present") else "no"
            if adjudication_row.get("present") != expected_present or adjudication_row.get("status") != adjudication_return.get("status"):
                issues.append(
                    {
                        "error": "adjudication_status_mismatch",
                        "reviewed_file": adjudication_return.get("reviewed_file"),
                        "plan_present": adjudication_row.get("present"),
                        "preflight_present": expected_present,
                        "plan_status": adjudication_row.get("status"),
                        "preflight_status": adjudication_return.get("status"),
                    }
                )
            if not Path(adjudication_row.get("input_file", "")).exists():
                issues.append({"error": "missing_adjudication_input_file", "path": adjudication_row.get("input_file")})
            if not Path(adjudication_row.get("target_file", "")).exists():
                issues.append({"error": "missing_adjudication_target_file", "path": adjudication_row.get("target_file")})

    if mapping_return:
        mapping_row = by_reviewed.get(mapping_return.get("reviewed_file"))
        if not mapping_row:
            issues.append({"error": "missing_mapping_reviewed_file_entry", "reviewed_file": mapping_return.get("reviewed_file")})
        else:
            expected_present = "yes" if mapping_return.get("present") else "no"
            if mapping_row.get("present") != expected_present or mapping_row.get("status") != mapping_return.get("status"):
                issues.append(
                    {
                        "error": "mapping_status_mismatch",
                        "reviewed_file": mapping_return.get("reviewed_file"),
                        "plan_present": mapping_row.get("present"),
                        "preflight_present": expected_present,
                        "plan_status": mapping_row.get("status"),
                        "preflight_status": mapping_return.get("status"),
                    }
                )
            if not Path(mapping_row.get("input_file", "")).exists():
                issues.append({"error": "missing_mapping_input_file", "path": mapping_row.get("input_file")})
            if not Path(mapping_row.get("target_file", "")).exists():
                issues.append({"error": "missing_mapping_target_file", "path": mapping_row.get("target_file")})

    if active_review_return:
        active_review_row = by_reviewed.get(active_review_return.get("reviewed_file"))
        if not active_review_row:
            issues.append({"error": "missing_active_review_reviewed_file_entry", "reviewed_file": active_review_return.get("reviewed_file")})
        else:
            expected_present = "yes" if active_review_return.get("present") else "no"
            if active_review_row.get("present") != expected_present or active_review_row.get("status") != active_review_return.get("status"):
                issues.append(
                    {
                        "error": "active_review_status_mismatch",
                        "reviewed_file": active_review_return.get("reviewed_file"),
                        "plan_present": active_review_row.get("present"),
                        "preflight_present": expected_present,
                        "plan_status": active_review_row.get("status"),
                        "preflight_status": active_review_return.get("status"),
                    }
                )
            if not Path(active_review_row.get("input_file", "")).exists():
                issues.append({"error": "missing_active_review_input_file", "path": active_review_row.get("input_file")})
            if active_review_row.get("target_file") and not Path(active_review_row.get("target_file", "")).exists():
                issues.append({"error": "missing_active_review_target_file", "path": active_review_row.get("target_file")})

    progress = plan.get("current_progress") or {}
    annotation = preflight.get("annotation_returns") or {}
    if progress.get("annotation_expected_reviewed_files") != annotation.get("expected_files"):
        issues.append(
            {
                "error": "annotation_expected_files_mismatch",
                "plan": progress.get("annotation_expected_reviewed_files"),
                "preflight": annotation.get("expected_files"),
            }
        )
    if progress.get("annotation_present_reviewed_files") != annotation.get("present_files"):
        issues.append(
            {
                "error": "annotation_present_files_mismatch",
                "plan": progress.get("annotation_present_reviewed_files"),
                "preflight": annotation.get("present_files"),
            }
        )
    if adjudication_return and progress.get("adjudication_completed_chunks") != adjudication_return.get("completed_adjudicated_chunks"):
        issues.append(
            {
                "error": "adjudication_completed_chunks_mismatch",
                "plan": progress.get("adjudication_completed_chunks"),
                "preflight": adjudication_return.get("completed_adjudicated_chunks"),
            }
        )
    if active_review_return and progress.get("active_review_effort_timed_rows") != active_review_return.get("timed_review_rows"):
        issues.append(
            {
                "error": "active_review_timed_rows_mismatch",
                "plan": progress.get("active_review_effort_timed_rows"),
                "preflight": active_review_return.get("timed_review_rows"),
            }
        )
    commands = plan.get("commands") or {}
    for key in [
        "preflight_returns",
        "dry_run_wrapper",
        "apply_wrapper",
        "dry_run_refresh",
        "apply_imports_and_refresh",
        "final_handoff_validation",
    ]:
        if key not in commands or not commands[key]:
            issues.append({"error": "missing_action_command", "command_key": key})

    if report_path.exists():
        report_text = report_path.read_text(encoding="utf-8")
        for pattern in ["## Gate Dependency Matrix", "human_review_gate_dependency_matrix.csv", "min.proposed"]:
            if pattern not in report_text:
                issues.append({"error": "missing_action_plan_markdown_pattern", "pattern": pattern})

    if issues:
        add_check(
            checks,
            "human_gate_action_plan",
            "FAIL",
            "Human gate action plan is not synchronized with return preflight and handoff files.",
            {"path": rel(plan_path), "issues": issues[:50]},
        )
        return

    add_check(
        checks,
        "human_gate_action_plan",
        "PASS",
        "Human gate action plan is synchronized with return preflight and split human-return files.",
        {
            "path": rel(plan_path),
            "report": rel(report_path),
            "required_returns_csv": rel(returns_csv_path),
            "gate_dependency_matrix_csv": rel(gate_matrix_csv_path),
            "minimum_paper_gate_return_files": len(minimum_returns),
            "minimum_paper_gate_present_files": minimum_return_present,
            "optional_strong_return_files": len(optional_strong_returns),
            "optional_strong_present_files": optional_strong_present,
            "tracked_human_return_files": len(required_returns),
            "tracked_human_return_files_present": minimum_return_present + optional_strong_present,
            "gate_dependency_rows": len(gate_matrix),
            "annotation_present_files": annotation.get("present_files"),
            "annotation_expected_files": annotation.get("expected_files"),
            "mapping_reviewed_rows": mapping_return.get("reviewed_rows"),
        },
    )


def validate_human_review_status_dashboard(checks, exp_dir):
    release_dir = exp_dir / "06_release"
    review_dir = exp_dir / "05_review"
    dashboard_path = release_dir / "human_review_status_dashboard_ko.json"
    dashboard_md_path = release_dir / "human_review_status_dashboard_ko.md"
    next_actions_path = review_dir / "human_review_status_next_actions.csv"
    master_returns_path = review_dir / "human_review_master_return_files.csv"
    preflight_path = release_dir / "human_review_return_preflight.json"
    try:
        dashboard = read_json(dashboard_path)
        prehuman = read_json(release_dir / "pre_human_handoff_validation.json")
        preflight = read_json(preflight_path)
        latest_index = read_json(release_dir / "latest_release_bundle_index.json")
        release_manifest = read_json(release_dir / "release_bundle_manifest.json")
        gold_sampling = read_json(release_dir / "gold_sampling_coverage_report.json")
        master_rows = read_csv_rows(master_returns_path)
        next_action_rows = read_csv_rows(next_actions_path)
    except Exception as exc:
        add_check(
            checks,
            "human_review_status_dashboard",
            "FAIL",
            "Human review status dashboard cannot be read.",
            {
                "error": str(exc),
                "dashboard": rel(dashboard_path),
                "next_actions_csv": rel(next_actions_path),
            },
        )
        return

    issues = []
    if dashboard.get("claim_status") != "human_review_status_dashboard_ready_pending_returns":
        issues.append({"error": "unexpected_claim_status", "actual": dashboard.get("claim_status")})
    if not dashboard_md_path.exists():
        issues.append({"error": "missing_markdown", "path": rel(dashboard_md_path)})

    required_rows = [row for row in master_rows if row.get("requiredness") == "required"]
    minimum_rows = [row for row in required_rows if truthy_present(row.get("required_for_minimum", True))]
    optional_strong_rows = [row for row in required_rows if not truthy_present(row.get("required_for_minimum", True))]
    optional_structural_rows = [row for row in master_rows if row.get("requiredness") != "required"]
    annotation_rows = [row for row in required_rows if row.get("task_type") == "human_gold_annotation"]
    required_present = sum(1 for row in required_rows if truthy_present(row.get("present")))
    minimum_present = sum(1 for row in minimum_rows if truthy_present(row.get("present")))
    optional_strong_present = sum(1 for row in optional_strong_rows if truthy_present(row.get("present")))
    optional_structural_present = sum(1 for row in optional_structural_rows if truthy_present(row.get("present")))
    annotation_present = sum(1 for row in annotation_rows if truthy_present(row.get("present")))
    summary = dashboard.get("summary") or {}
    if "pre_human_check_count" in summary:
        issues.append({"error": "legacy_stale_prone_pre_human_check_count_field", "actual": summary.get("pre_human_check_count")})
    if "pre_human_status_counts" in summary:
        issues.append({"error": "legacy_stale_prone_pre_human_status_counts_field", "actual": summary.get("pre_human_status_counts")})
    if "pre_human_handoff_validation" in summary:
        issues.append({"error": "legacy_stale_prone_pre_human_validation_status_field"})
    if "pre_human_claim_status" in summary:
        issues.append({"error": "legacy_stale_prone_pre_human_validation_claim_status_field"})
    if summary.get("pre_human_validation_source_json") != rel(release_dir / "pre_human_handoff_validation.json"):
        issues.append({"error": "pre_human_validation_source_json_mismatch", "actual": summary.get("pre_human_validation_source_json")})
    if summary.get("pre_human_validation_source_md") != rel(release_dir / "pre_human_handoff_validation.md"):
        issues.append({"error": "pre_human_validation_source_md_mismatch", "actual": summary.get("pre_human_validation_source_md")})
    latest_current = latest_index.get("current") or {}
    expected_internal = latest_current.get("internal_bundle") or (release_manifest.get("internal_bundle") or {})
    expected_public_safe = latest_current.get("public_safe_bundle") or (release_manifest.get("public_safe_bundle") or {})
    expected_latest_values = {
        "latest_release_stamp": latest_index.get("stamp") or release_manifest.get("stamp"),
        "latest_internal_bundle": expected_internal.get("path"),
        "latest_internal_bundle_sha256": expected_internal.get("sha256"),
        "latest_public_safe_bundle": expected_public_safe.get("path"),
        "latest_public_safe_bundle_sha256": expected_public_safe.get("sha256"),
    }
    for field, expected in expected_latest_values.items():
        actual = summary.get(field)
        if actual != expected:
            issues.append({"error": "latest_release_summary_mismatch", "field": field, "expected": expected, "actual": actual})
    for field in ["latest_internal_bundle", "latest_public_safe_bundle"]:
        bundle_path = Path(summary.get(field) or "")
        if not bundle_path.exists():
            issues.append({"error": "latest_bundle_path_missing", "field": field, "path": rel(bundle_path)})
    annotation = preflight.get("annotation_returns") or {}
    adjudication = preflight.get("adjudication_return") or {}
    mapping = preflight.get("mapping_return") or {}
    crosswalk = preflight.get("crosswalk_return") or {}
    active = preflight.get("active_review_effort_return") or {}

    expected_summary_values = {
        "required_return_files_total": len(required_rows),
        "required_return_files_present": required_present,
        "required_return_files_missing": len(required_rows) - required_present,
        "minimum_return_files_total": len(minimum_rows),
        "minimum_return_files_present": minimum_present,
        "minimum_return_files_missing": len(minimum_rows) - minimum_present,
        "optional_strong_return_files_total": len(optional_strong_rows),
        "optional_strong_return_files_present": optional_strong_present,
        "optional_strong_return_files_missing": len(optional_strong_rows) - optional_strong_present,
        "optional_structural_return_files_total": len(optional_structural_rows),
        "optional_structural_return_files_present": optional_structural_present,
        "optional_structural_return_files_missing": len(optional_structural_rows) - optional_structural_present,
        "master_return_files_total": len(master_rows),
        "master_return_files_present": required_present + optional_structural_present,
        "master_return_files_missing": len(master_rows) - required_present - optional_structural_present,
        "annotation_reviewed_files_total": len(annotation_rows),
        "annotation_reviewed_files_present": annotation_present,
        "paired_completed_chunks": annotation.get("paired_completed_chunks", 0),
        "adjudication_reviewed_file_present": bool(adjudication.get("present")),
        "mapping_expected_priority_groups": mapping.get("expected_priority_groups"),
        "mapping_complete_priority_groups": mapping.get("complete_top5_groups", 0),
        "crosswalk_expected_rows": crosswalk.get("expected_rows"),
        "crosswalk_completed_rows": crosswalk.get("completed_rows", 0),
        "crosswalk_expected_source_tasks": crosswalk.get("expected_source_tasks"),
        "crosswalk_complete_source_groups": crosswalk.get("complete_source_groups", 0),
        "crosswalk_reviewed_file_present": bool(crosswalk.get("present")),
        "active_review_effort_reviewed_file_present": bool(active.get("present")),
    }
    for field, expected in expected_summary_values.items():
        actual = summary.get(field)
        if actual != expected:
            issues.append({"error": "summary_value_mismatch", "field": field, "expected": expected, "actual": actual})

    sampling = dashboard.get("priority_100_sampling") or {}
    sampling_policy = gold_sampling.get("selection_policy") or {}
    sampling_coverage = gold_sampling.get("coverage_summary") or {}
    expected_sampling = {
        "claim_status": gold_sampling.get("claim_status"),
        "selected_chunks": int(sampling_policy.get("selected_chunk_count") or 0),
        "candidate_edges": int(sampling_coverage.get("priority_100_candidate_edges") or 0),
        "full_120_candidate_edges": int(sampling_coverage.get("full_120_candidate_edges") or 0),
        "candidate_edge_coverage": float(sampling_coverage.get("priority_100_candidate_edge_coverage_of_full120") or 0.0),
        "active_review_coverage": float(sampling_coverage.get("priority_100_active_review_chunk_coverage_of_full120") or 0.0),
        "high_impact_coverage": float(sampling_coverage.get("priority_100_high_impact_chunk_coverage_of_full120") or 0.0),
    }
    for field, expected in expected_sampling.items():
        actual = sampling.get(field)
        if isinstance(expected, float):
            if abs(float(actual or 0.0) - expected) > 1e-9:
                issues.append({"error": "priority_sampling_mismatch", "field": field, "expected": expected, "actual": actual})
        elif actual != expected:
            issues.append({"error": "priority_sampling_mismatch", "field": field, "expected": expected, "actual": actual})
    if expected_sampling["selected_chunks"] < 100 or expected_sampling["candidate_edge_coverage"] < 0.90:
        issues.append({"error": "priority_sampling_unexpectedly_weak", "expected_sampling": expected_sampling})

    required_card_ids = {
        "required_returns",
        "annotation_reviewed_files",
        "paired_iaa_chunks",
        "adjudicated_chunks",
        "gold_items",
        "mapping_priority_groups",
        "crosswalk_source_groups",
        "active_review_effort_rows",
    }
    card_ids = {row.get("id") for row in dashboard.get("progress_cards") or []}
    missing_card_ids = sorted(required_card_ids - card_ids)
    if missing_card_ids:
        issues.append({"error": "missing_progress_cards", "missing": missing_card_ids})

    required_actions = {
        "handoff bundle이 손상되지 않았는지 확인",
        "priority batch 001 독립 annotation",
        "반환 파일 preflight",
        "사람 반환 파일 dry-run 반영",
        "A/B disagreement adjudication",
        "NCS/PCF top20 priority group expert review",
        "NCS-PCF crosswalk 후보 utility 검수",
        "active-review effort/timing 기록",
    }
    action_objectives = {row.get("objective") for row in next_action_rows}
    missing_actions = sorted(required_actions - action_objectives)
    if missing_actions:
        issues.append({"error": "missing_next_actions", "missing": missing_actions})
    if len(next_action_rows) < 8:
        issues.append({"error": "too_few_next_action_rows", "actual": len(next_action_rows)})

    first_batch_rows = [r for r in required_rows if r.get("batch_or_group") == "full_120_priority_batch_001"]
    for row in first_batch_rows:
        reviewed_file = row.get("reviewed_file") or ""
        if reviewed_file and reviewed_file not in json.dumps(dashboard, ensure_ascii=False):
            issues.append({"error": "first_batch_reviewed_file_missing_from_dashboard", "reviewed_file": reviewed_file})
    if len(first_batch_rows) != 2:
        issues.append({"error": "first_batch_return_count_unexpected", "actual": len(first_batch_rows)})

    if dashboard_md_path.exists():
        text = dashboard_md_path.read_text(encoding="utf-8")
        for pattern in [
            "CAPE-KG 사람 검수 상태 대시보드",
            "## 진행 상태",
            "## 즉시 열 파일",
            "## 다음 명령",
            "## 아직 claim하면 안 되는 것",
            "## Priority-100 선정 근거",
            "Candidate-edge coverage",
            "Latest internal bundle",
            "Latest public-safe bundle",
        ]:
            if pattern not in text:
                issues.append({"error": "missing_dashboard_markdown_pattern", "pattern": pattern})
        if "Pre-human validation: `FAIL` / checks" in text or "pre_human_check_count" in text:
            issues.append({"error": "legacy_stale_prone_pre_human_count_in_dashboard_markdown"})

    if issues:
        add_check(
            checks,
            "human_review_status_dashboard",
            "FAIL",
            "Human review status dashboard is missing or not synchronized with return preflight.",
            {"path": rel(dashboard_path), "issues": issues[:40]},
        )
        return

    add_check(
        checks,
        "human_review_status_dashboard",
        "PASS",
        "Human review status dashboard is synchronized with return preflight and next-action CSV.",
        {
            "path": rel(dashboard_path),
            "report": rel(dashboard_md_path),
            "next_actions_csv": rel(next_actions_path),
            "minimum_paper_gate_return_files": len(minimum_rows),
            "minimum_paper_gate_present_files": minimum_present,
            "optional_strong_return_files": len(optional_strong_rows),
            "optional_strong_present_files": optional_strong_present,
            "required_claim_human_return_files": len(required_rows),
            "required_claim_human_present_files": required_present,
            "optional_structural_return_files": len(optional_structural_rows),
            "optional_structural_present_files": optional_structural_present,
            "master_return_files": len(master_rows),
            "master_return_files_present": required_present + optional_structural_present,
            "next_action_rows": len(next_action_rows),
            "progress_cards": len(dashboard.get("progress_cards") or []),
        },
    )


def validate_human_review_first_batch_execution_card(checks, exp_dir):
    review_dir = exp_dir / "05_review"
    release_dir = exp_dir / "06_release"
    batch_id = "full_120_priority_batch_001"
    card_json_path = review_dir / "human_review_first_batch_execution_card.json"
    card_md_path = review_dir / "human_review_first_batch_execution_card_ko.md"
    master_returns_path = review_dir / "human_review_master_return_files.csv"
    dashboard_path = release_dir / "human_review_status_dashboard_ko.json"
    batch_manifest_path = review_dir / "human_gold_batches" / batch_id / "batch_manifest.json"

    try:
        card = read_json(card_json_path)
        dashboard = read_json(dashboard_path)
        master_rows = read_csv_rows(master_returns_path)
        batch_manifest = read_json(batch_manifest_path)
        gold_sampling = read_json(release_dir / "gold_sampling_coverage_report.json")
    except Exception as exc:
        add_check(
            checks,
            "human_review_first_batch_execution_card",
            "FAIL",
            "Human review first-batch execution card cannot be read.",
            {
                "error": str(exc),
                "json": rel(card_json_path),
                "markdown": rel(card_md_path),
                "master_returns": rel(master_returns_path),
            },
        )
        return

    issues = []
    if card.get("claim_status") != "first_batch_execution_card_ready_pending_human_returns":
        issues.append({"error": "unexpected_claim_status", "actual": card.get("claim_status")})
    if card.get("batch_id") != batch_id:
        issues.append({"error": "unexpected_batch_id", "expected": batch_id, "actual": card.get("batch_id")})
    outputs = card.get("outputs") or {}
    if outputs.get("markdown") != rel(card_md_path):
        issues.append({"error": "markdown_output_path_mismatch", "expected": rel(card_md_path), "actual": outputs.get("markdown")})
    if outputs.get("json") != rel(card_json_path):
        issues.append({"error": "json_output_path_mismatch", "expected": rel(card_json_path), "actual": outputs.get("json")})
    if not card_md_path.exists():
        issues.append({"error": "missing_markdown", "path": rel(card_md_path)})

    dashboard_outputs = (dashboard.get("outputs") or {})
    if dashboard_outputs.get("first_batch_card_markdown") != rel(card_md_path):
        issues.append(
            {
                "error": "dashboard_first_batch_card_markdown_mismatch",
                "expected": rel(card_md_path),
                "actual": dashboard_outputs.get("first_batch_card_markdown"),
            }
        )
    if dashboard_outputs.get("first_batch_card_json") != rel(card_json_path):
        issues.append(
            {
                "error": "dashboard_first_batch_card_json_mismatch",
                "expected": rel(card_json_path),
                "actual": dashboard_outputs.get("first_batch_card_json"),
            }
        )

    master_first_rows = sorted(
        [
            row
            for row in master_rows
            if row.get("task_type") == "human_gold_annotation"
            and row.get("batch_or_group") == batch_id
        ],
        key=lambda row: row.get("owner") or "",
    )
    card_rows = sorted(card.get("first_annotation_return_files") or [], key=lambda row: row.get("owner") or "")
    if len(card_rows) != 2:
        issues.append({"error": "card_first_batch_return_count_unexpected", "actual": len(card_rows)})
    if len(master_first_rows) != 2:
        issues.append({"error": "master_first_batch_return_count_unexpected", "actual": len(master_first_rows)})

    expected_owners = {"annotator_A", "annotator_B"}
    actual_owners = {row.get("owner") for row in card_rows}
    if actual_owners != expected_owners:
        issues.append({"error": "first_batch_owner_set_mismatch", "expected": sorted(expected_owners), "actual": sorted(actual_owners)})
    for card_row, master_row in zip(card_rows, master_first_rows):
        for field in ["owner", "batch_or_group", "expected_rows", "input_file", "reviewed_file", "present", "status"]:
            if str(card_row.get(field, "")) != str(master_row.get(field, "")):
                issues.append(
                    {
                        "error": "first_batch_row_mismatch",
                        "field": field,
                        "owner": card_row.get("owner") or master_row.get("owner"),
                        "expected": master_row.get(field),
                        "actual": card_row.get(field),
                    }
                )
        if card_row.get("expected_rows") not in {"20", 20}:
            issues.append({"error": "first_batch_expected_rows_not_20", "owner": card_row.get("owner"), "actual": card_row.get("expected_rows")})
        for path_field in ["input_file", "reviewed_file"]:
            value = card_row.get(path_field) or ""
            if value and value not in json.dumps(card, ensure_ascii=False):
                issues.append({"error": "first_batch_path_missing_from_card_payload", "field": path_field, "path": value})

    if batch_manifest.get("batch_id") != batch_id:
        issues.append({"error": "batch_manifest_id_mismatch", "actual": batch_manifest.get("batch_id")})
    if batch_manifest.get("chunk_count") != 20:
        issues.append({"error": "batch_manifest_chunk_count_unexpected", "actual": batch_manifest.get("chunk_count")})
    if int(batch_manifest.get("candidate_edges_total") or 0) <= 0:
        issues.append({"error": "batch_manifest_candidate_edges_missing", "actual": batch_manifest.get("candidate_edges_total")})

    sampling = card.get("priority_100_sampling") or {}
    sampling_policy = gold_sampling.get("selection_policy") or {}
    sampling_coverage = gold_sampling.get("coverage_summary") or {}
    priority_candidate_edges = int(sampling_coverage.get("priority_100_candidate_edges") or 0)
    batch_candidate_edges = int(batch_manifest.get("candidate_edges_total") or 0)
    expected_share = round(batch_candidate_edges / priority_candidate_edges, 6) if priority_candidate_edges else 0.0
    expected_sampling = {
        "claim_status": gold_sampling.get("claim_status"),
        "selected_chunks": int(sampling_policy.get("selected_chunk_count") or 0),
        "priority_100_candidate_edges": priority_candidate_edges,
        "batch_candidate_edges": batch_candidate_edges,
        "batch_share_of_priority_candidate_edges": expected_share,
        "candidate_edge_coverage": float(sampling_coverage.get("priority_100_candidate_edge_coverage_of_full120") or 0.0),
        "active_review_coverage": float(sampling_coverage.get("priority_100_active_review_chunk_coverage_of_full120") or 0.0),
        "high_impact_coverage": float(sampling_coverage.get("priority_100_high_impact_chunk_coverage_of_full120") or 0.0),
    }
    for field, expected in expected_sampling.items():
        actual = sampling.get(field)
        if isinstance(expected, float):
            if abs(float(actual or 0.0) - expected) > 1e-9:
                issues.append({"error": "first_batch_priority_sampling_mismatch", "field": field, "expected": expected, "actual": actual})
        elif actual != expected:
            issues.append({"error": "first_batch_priority_sampling_mismatch", "field": field, "expected": expected, "actual": actual})
    if expected_share <= 0:
        issues.append({"error": "first_batch_priority_share_missing", "expected_share": expected_share})

    common_files = card.get("common_files_to_open") or {}
    required_common = {
        "workbench",
        "annotation_guideline",
        "annotation_schema",
        "adjudication_protocol",
        "calibration_pack",
        "batch_readme",
        "batch_preview_md",
        "batch_tracking_sheet",
        "master_return_files",
        "status_dashboard",
        "launch_checklist",
    }
    missing_common = sorted(required_common - set(common_files))
    if missing_common:
        issues.append({"error": "missing_common_file_entries", "missing": missing_common})
    for name in required_common & set(common_files):
        state = common_files.get(name) or {}
        if not state.get("exists"):
            issues.append({"error": "common_file_missing", "name": name, "path": state.get("path")})

    commands = card.get("commands") or {}
    for name in ["verify_handoff_checksums", "validate_required_returns", "dry_run_human_return_apply", "apply_human_returns"]:
        if not commands.get(name):
            issues.append({"error": "missing_card_command", "command": name})

    guardrail_text = "\n".join(card.get("guardrails") or [])
    for pattern in ["Input JSONL", "A/B annotator", "accepted edge", "최소 논문 gate"]:
        if pattern not in guardrail_text:
            issues.append({"error": "missing_guardrail_pattern", "pattern": pattern})

    if card_md_path.exists():
        md_text = card_md_path.read_text(encoding="utf-8", errors="replace")
        for pattern in [
            "CAPE-KG 첫 배치 검수 실행 카드",
            "Annotator별 입력/저장 파일",
            "반환 후 확인 명령",
            "full_120_priority_batch_001",
            "annotator_A_full_120_priority_batch_001.reviewed.jsonl",
            "annotator_B_full_120_priority_batch_001.reviewed.jsonl",
            "Priority-100 안에서 첫 배치의 의미",
            "First-batch share of priority candidate edges",
        ]:
            if pattern not in md_text:
                issues.append({"error": "missing_card_markdown_pattern", "pattern": pattern})

    if issues:
        add_check(
            checks,
            "human_review_first_batch_execution_card",
            "FAIL",
            "Human review first-batch execution card is missing or not synchronized with return files and dashboard.",
            {"path": rel(card_json_path), "issues": issues[:50]},
        )
        return

    add_check(
        checks,
        "human_review_first_batch_execution_card",
        "PASS",
        "Human review first-batch execution card is synchronized with A/B batch files, dashboard links, guardrails, and safe commands.",
        {
            "json": rel(card_json_path),
            "markdown": rel(card_md_path),
            "batch_id": batch_id,
            "annotation_return_files": len(card_rows),
            "chunk_count": batch_manifest.get("chunk_count"),
            "candidate_edges_total": batch_manifest.get("candidate_edges_total"),
            "commands": len(commands),
        },
    )


def validate_human_review_role_quickstart_cards(checks, exp_dir):
    review_dir = exp_dir / "05_review"
    release_dir = exp_dir / "06_release"
    handoff_dir = release_dir / "human_review_handoff"
    quickstart_json_path = review_dir / "human_review_role_quickstart_cards.json"
    quickstart_md_path = review_dir / "human_review_role_quickstart_cards_ko.md"
    quickstart_csv_path = review_dir / "human_review_role_quickstart_cards.csv"
    dashboard_path = release_dir / "human_review_status_dashboard_ko.json"
    master_returns_path = review_dir / "human_review_master_return_files.csv"
    handoff_manifest_path = handoff_dir / "human_review_handoff_manifest.json"
    first_batch_path = review_dir / "human_review_first_batch_execution_card.json"

    try:
        quickstart = read_json(quickstart_json_path)
        dashboard = read_json(dashboard_path)
        master_rows = read_csv_rows(master_returns_path)
        csv_rows = read_csv_rows(quickstart_csv_path)
        handoff_manifest = read_json(handoff_manifest_path)
        first_batch = read_json(first_batch_path)
    except Exception as exc:
        add_check(
            checks,
            "human_review_role_quickstart_cards",
            "FAIL",
            "Human review role quickstart cards cannot be read.",
            {
                "error": str(exc),
                "json": rel(quickstart_json_path),
                "markdown": rel(quickstart_md_path),
                "csv": rel(quickstart_csv_path),
            },
        )
        return

    issues = []
    expected_roles = {
        "annotator_A",
        "annotator_B",
        "coordinator",
        "adjudicator",
        "mapping_expert",
        "crosswalk_expert",
        "active_reviewer",
        "structural_reviewer",
        "strong_resegmented_review",
    }
    bundle_key_by_role = {
        "annotator_A": "annotator_A",
        "annotator_B": "annotator_B",
        "coordinator": "coordinator",
        "adjudicator": "adjudicator",
        "mapping_expert": "mapping_expert",
        "crosswalk_expert": "crosswalk_expert",
        "active_reviewer": "active_review_effort",
        "structural_reviewer": "structural_reviewer",
        "strong_resegmented_review": "strong_resegmented_review",
    }

    if quickstart.get("claim_status") != "role_quickstart_ready_pending_human_returns":
        issues.append({"error": "unexpected_claim_status", "actual": quickstart.get("claim_status")})

    outputs = quickstart.get("outputs") or {}
    expected_outputs = {
        "markdown": rel(quickstart_md_path),
        "json": rel(quickstart_json_path),
        "csv": rel(quickstart_csv_path),
    }
    for key, expected in expected_outputs.items():
        if outputs.get(key) != expected:
            issues.append({"error": "output_path_mismatch", "field": key, "expected": expected, "actual": outputs.get(key)})
    for path in [quickstart_md_path, quickstart_csv_path]:
        if not path.exists():
            issues.append({"error": "missing_output_file", "path": rel(path)})

    cards = quickstart.get("cards") or []
    role_set = {card.get("role") for card in cards}
    if role_set != expected_roles:
        issues.append({"error": "role_set_mismatch", "expected": sorted(expected_roles), "actual": sorted(role_set)})
    if len(cards) != len(expected_roles):
        issues.append({"error": "role_count_unexpected", "expected": len(expected_roles), "actual": len(cards)})

    summary = quickstart.get("summary") or {}
    dashboard_summary = dashboard.get("summary") or {}
    expected_summary_values = {
        "minimum_return_files": dashboard_summary.get("minimum_return_files_total"),
        "minimum_return_files_present": dashboard_summary.get("minimum_return_files_present"),
        "required_return_files": dashboard_summary.get("required_return_files_total"),
        "required_return_files_present": dashboard_summary.get("required_return_files_present"),
        "first_batch_id": first_batch.get("batch_id"),
        "role_count": len(cards),
    }
    for field, expected in expected_summary_values.items():
        if summary.get(field) != expected:
            issues.append({"error": "summary_value_mismatch", "field": field, "expected": expected, "actual": summary.get(field)})

    dashboard_outputs = dashboard.get("outputs") or {}
    dashboard_expected_outputs = {
        "role_quickstart_markdown": rel(quickstart_md_path),
        "role_quickstart_json": rel(quickstart_json_path),
        "role_quickstart_csv": rel(quickstart_csv_path),
    }
    for field, expected in dashboard_expected_outputs.items():
        if dashboard_outputs.get(field) != expected:
            issues.append(
                {
                    "error": "dashboard_quickstart_output_mismatch",
                    "field": field,
                    "expected": expected,
                    "actual": dashboard_outputs.get(field),
                }
            )

    dashboard_sources = dashboard.get("source_files") or {}
    source_expected = {
        "human_review_role_quickstart": rel(quickstart_md_path),
        "human_review_role_quickstart_json": rel(quickstart_json_path),
        "human_review_role_quickstart_csv": rel(quickstart_csv_path),
    }
    for field, expected in source_expected.items():
        state = dashboard_sources.get(field) or {}
        if state.get("path") != expected or not truthy_present(state.get("exists")):
            issues.append(
                {
                    "error": "dashboard_quickstart_source_mismatch",
                    "field": field,
                    "expected": expected,
                    "actual": state,
                }
            )

    master_reviewed_files = {row.get("reviewed_file") for row in master_rows if row.get("reviewed_file")}
    bundles = handoff_manifest.get("bundles") or {}
    for card in cards:
        role = card.get("role")
        bundle_key = bundle_key_by_role.get(role)
        bundle = bundles.get(bundle_key) or {}
        if bundle.get("path") and card.get("bundle") != bundle.get("path"):
            issues.append({"error": "bundle_path_mismatch", "role": role, "expected": bundle.get("path"), "actual": card.get("bundle")})
        if not card.get("goal"):
            issues.append({"error": "missing_role_goal", "role": role})
        if not card.get("start_here"):
            issues.append({"error": "missing_role_start_here", "role": role})
        if not any(item for item in (card.get("open_files") or [])):
            issues.append({"error": "missing_role_open_files", "role": role})
        if role not in {"coordinator", "strong_resegmented_review"} and not any(item for item in (card.get("save_files") or [])):
            issues.append({"error": "missing_role_save_files", "role": role})
        first_return = card.get("first_required_return") or ""
        if role not in {"coordinator", "structural_reviewer", "strong_resegmented_review"} and first_return not in master_reviewed_files:
            issues.append({"error": "first_required_return_not_in_master", "role": role, "first_required_return": first_return})
        for row in card.get("return_rows") or []:
            reviewed_file = row.get("reviewed_file") or ""
            if reviewed_file and reviewed_file not in master_reviewed_files and role != "structural_reviewer":
                issues.append({"error": "card_return_row_not_in_master", "role": role, "reviewed_file": reviewed_file})

    csv_role_set = {row.get("role") for row in csv_rows}
    if csv_role_set != expected_roles:
        issues.append({"error": "csv_role_set_mismatch", "expected": sorted(expected_roles), "actual": sorted(csv_role_set)})
    if len(csv_rows) != len(cards):
        issues.append({"error": "csv_row_count_mismatch", "expected": len(cards), "actual": len(csv_rows)})

    commands = quickstart.get("commands") or {}
    for name in [
        "verify_handoff_checksums",
        "validate_required_returns",
        "dry_run_human_return_apply",
        "apply_human_returns",
        "validate_pre_human_handoff",
    ]:
        if not commands.get(name):
            issues.append({"error": "missing_quickstart_command", "command": name})

    source_files = quickstart.get("source_files") or {}
    for field in ["handoff_manifest", "master_return_files", "dashboard", "first_batch_card", "structural_optional_returns"]:
        state = source_files.get(field) or {}
        if not truthy_present(state.get("exists")):
            issues.append({"error": "missing_quickstart_source_file", "field": field, "state": state})

    if quickstart_md_path.exists():
        md_text = quickstart_md_path.read_text(encoding="utf-8", errors="replace")
        for pattern in [
            "CAPE-KG 역할별 사람 검수 Quickstart",
            "annotator_A",
            "annotator_B",
            "coordinator",
            "mapping_expert",
            "crosswalk_expert",
            "active_reviewer",
            "strong_resegmented_review",
            "공통 명령",
            "validate_pre_human_handoff",
        ]:
            if pattern not in md_text:
                issues.append({"error": "missing_quickstart_markdown_pattern", "pattern": pattern})
    else:
        issues.append({"error": "missing_quickstart_markdown", "path": rel(quickstart_md_path)})

    if issues:
        add_check(
            checks,
            "human_review_role_quickstart_cards",
            "FAIL",
            "Human review role quickstart cards are missing, stale, or not synchronized with dashboard/handoff files.",
            {"path": rel(quickstart_json_path), "issues": issues[:60]},
        )
        return

    add_check(
        checks,
        "human_review_role_quickstart_cards",
        "PASS",
        "Human review role quickstart cards are synchronized with role bundles, dashboard links, return files, and safe commands.",
        {
            "json": rel(quickstart_json_path),
            "markdown": rel(quickstart_md_path),
            "csv": rel(quickstart_csv_path),
            "roles": len(cards),
            "commands": len(commands),
            "minimum_return_files": summary.get("minimum_return_files"),
            "required_return_files": summary.get("required_return_files"),
        },
    )


def validate_human_review_launch_checklist(checks, exp_dir):
    release_dir = exp_dir / "06_release"
    review_dir = exp_dir / "05_review"
    launch_json_path = release_dir / "human_review_launch_checklist_ko.json"
    launch_md_path = release_dir / "human_review_launch_checklist_ko.md"
    launch_csv_path = review_dir / "human_review_minimum_gate_launch_tasks.csv"
    required_returns_path = review_dir / "human_gate_required_returns.csv"
    preflight_path = release_dir / "human_review_return_preflight.json"
    claim_gate_path = release_dir / "claim_gate_report.json"
    try:
        launch = read_json(launch_json_path)
        launch_rows = read_csv_rows(launch_csv_path)
        return_rows = read_csv_rows(required_returns_path)
        preflight = read_json(preflight_path)
        claim_gate = read_json(claim_gate_path)
        gold_sampling = read_json(release_dir / "gold_sampling_coverage_report.json")
    except Exception as exc:
        add_check(
            checks,
            "human_review_launch_checklist",
            "FAIL",
            "Human review launch checklist cannot be read.",
            {
                "error": str(exc),
                "json": rel(launch_json_path),
                "markdown": rel(launch_md_path),
                "csv": rel(launch_csv_path),
            },
        )
        return

    issues = []
    if launch.get("claim_status") != "human_review_launch_checklist_ready_pending_human_returns":
        issues.append({"error": "unexpected_claim_status", "actual": launch.get("claim_status")})
    if not launch_md_path.exists():
        issues.append({"error": "missing_markdown", "path": rel(launch_md_path)})

    minimum_rows = [
        row
        for row in return_rows
        if truthy_present(row.get("required_for_minimum")) and row.get("task_type") in {"human_gold_annotation", "human_gold_adjudication"}
    ]
    annotation_rows = [row for row in minimum_rows if row.get("task_type") == "human_gold_annotation"]
    adjudication_rows = [row for row in minimum_rows if row.get("task_type") == "human_gold_adjudication"]
    optional_rows = [row for row in return_rows if not truthy_present(row.get("required_for_minimum"))]
    minimum_present = sum(1 for row in minimum_rows if truthy_present(row.get("present")))
    annotation_present = sum(1 for row in annotation_rows if truthy_present(row.get("present")))
    adjudication_present = sum(1 for row in adjudication_rows if truthy_present(row.get("present")))
    optional_present = sum(1 for row in optional_rows if truthy_present(row.get("present")))

    summary = launch.get("summary") or {}
    expected_summary_values = {
        "claim_gate_overall_status": claim_gate.get("overall_status"),
        "claim_gate_required_failure_count": claim_gate.get("required_failure_count"),
        "claim_gate_optional_failure_count": claim_gate.get("optional_failure_count"),
        "human_return_preflight": preflight.get("overall_status"),
        "minimum_return_files_total": len(minimum_rows),
        "minimum_return_files_present": minimum_present,
        "annotation_return_files_total": len(annotation_rows),
        "annotation_return_files_present": annotation_present,
        "adjudication_return_files_total": len(adjudication_rows),
        "adjudication_return_files_present": adjudication_present,
        "optional_return_files_total": len(optional_rows),
        "optional_return_files_present": optional_present,
    }
    for field, expected in expected_summary_values.items():
        actual = summary.get(field)
        if actual != expected:
            issues.append({"error": "summary_value_mismatch", "field": field, "expected": expected, "actual": actual})

    sampling = launch.get("priority_100_sampling") or {}
    sampling_policy = gold_sampling.get("selection_policy") or {}
    sampling_coverage = gold_sampling.get("coverage_summary") or {}
    expected_sampling = {
        "claim_status": gold_sampling.get("claim_status"),
        "selected_chunks": int(sampling_policy.get("selected_chunk_count") or 0),
        "minimum_gate_target_chunks": int(sampling_policy.get("minimum_gate_target_chunks") or 100),
        "candidate_edges": int(sampling_coverage.get("priority_100_candidate_edges") or 0),
        "full_120_candidate_edges": int(sampling_coverage.get("full_120_candidate_edges") or 0),
        "candidate_edge_coverage": float(sampling_coverage.get("priority_100_candidate_edge_coverage_of_full120") or 0.0),
        "active_review_coverage": float(sampling_coverage.get("priority_100_active_review_chunk_coverage_of_full120") or 0.0),
        "high_impact_coverage": float(sampling_coverage.get("priority_100_high_impact_chunk_coverage_of_full120") or 0.0),
    }
    for field, expected in expected_sampling.items():
        actual = sampling.get(field)
        if isinstance(expected, float):
            if abs(float(actual or 0.0) - expected) > 1e-9:
                issues.append({"error": "launch_priority_sampling_mismatch", "field": field, "expected": expected, "actual": actual})
        elif actual != expected:
            issues.append({"error": "launch_priority_sampling_mismatch", "field": field, "expected": expected, "actual": actual})

    launch_tasks = launch.get("minimum_gate_launch_tasks") or []
    if len(launch_rows) != len(launch_tasks):
        issues.append({"error": "csv_json_task_count_mismatch", "csv": len(launch_rows), "json": len(launch_tasks)})
    if len(launch_tasks) < 18:
        issues.append({"error": "too_few_launch_tasks", "actual": len(launch_tasks)})

    required_phases = {
        "0_package_integrity",
        "1_independent_annotation",
        "2_preflight",
        "3_dry_run",
        "4_apply_annotation_returns",
        "5_adjudication",
        "6_apply_adjudication",
        "7_final_validation",
    }
    phases = {row.get("phase") for row in launch_tasks}
    missing_phases = sorted(required_phases - phases)
    if missing_phases:
        issues.append({"error": "missing_launch_phases", "missing": missing_phases})

    annotation_task_rows = [row for row in launch_tasks if row.get("task_type") == "human_gold_annotation"]
    if len(annotation_task_rows) != len(annotation_rows):
        issues.append({"error": "annotation_launch_task_count_mismatch", "expected": len(annotation_rows), "actual": len(annotation_task_rows)})

    payload_text = json.dumps(launch, ensure_ascii=False)
    for row in minimum_rows:
        reviewed_file = row.get("reviewed_file") or ""
        if reviewed_file and reviewed_file not in payload_text:
            issues.append({"error": "minimum_reviewed_file_missing_from_launch_json", "reviewed_file": reviewed_file})

    commands = launch.get("commands") or {}
    for name in ["verify_handoff_checksums", "validate_returns", "dry_apply", "apply_returns", "validate_pre_human", "release_checksums"]:
        if not commands.get(name):
            issues.append({"error": "missing_launch_command", "command": name})

    if launch_md_path.exists():
        text = launch_md_path.read_text(encoding="utf-8")
        for pattern in [
            "CAPE-KG Human Review Launch Checklist",
            "## Current Gate State",
            "## Priority-100 선정 근거",
            "## Minimum Gate Launch Tasks",
            "## Required Reviewed Filenames",
            "## Claim Safety",
            "Candidate-edge coverage",
        ]:
            if pattern not in text:
                issues.append({"error": "missing_launch_markdown_pattern", "pattern": pattern})

    if issues:
        add_check(
            checks,
            "human_review_launch_checklist",
            "FAIL",
            "Human review launch checklist is missing or not synchronized with required return files.",
            {"path": rel(launch_json_path), "issues": issues[:40]},
        )
        return

    add_check(
        checks,
        "human_review_launch_checklist",
        "PASS",
        "Human review launch checklist maps the minimum paper-gate return files to day-1 tasks and safe commands.",
        {
            "path": rel(launch_json_path),
            "report": rel(launch_md_path),
            "launch_tasks_csv": rel(launch_csv_path),
            "minimum_return_files": len(minimum_rows),
            "annotation_return_files": len(annotation_rows),
            "adjudication_return_files": len(adjudication_rows),
            "optional_return_files": len(optional_rows),
            "launch_task_rows": len(launch_tasks),
        },
    )


def validate_human_review_packet_integrity(checks, exp_dir):
    release_dir = exp_dir / "06_release"
    review_dir = exp_dir / "05_review"
    json_path = release_dir / "human_review_packet_integrity.json"
    md_path = release_dir / "human_review_packet_integrity.md"
    issue_csv_path = review_dir / "human_review_packet_integrity_issues.csv"
    evidence = {
        "json": rel(json_path),
        "markdown": rel(md_path),
        "issue_csv": rel(issue_csv_path),
    }
    if not json_path.exists():
        add_check(
            checks,
            "human_review_packet_integrity",
            "FAIL",
            "Human-review packet integrity report JSON is missing.",
            evidence,
        )
        return
    try:
        payload = read_json(json_path)
    except Exception as exc:
        add_check(
            checks,
            "human_review_packet_integrity",
            "FAIL",
            "Human-review packet integrity report JSON cannot be read.",
            {**evidence, "error": str(exc)},
        )
        return

    issues = []
    summary = payload.get("summary") or {}
    components = payload.get("components") or {}
    min_batches = components.get("minimum_annotation_batches") or {}
    mapping = components.get("mapping_expert_review") or {}
    crosswalk = components.get("crosswalk_expert_review") or {}
    active_effort = components.get("active_review_effort") or {}
    strong = components.get("optional_strong_review") or {}
    returns = components.get("return_file_manifest") or {}
    handoff = components.get("handoff_bundles") or {}

    if not md_path.exists():
        issues.append({"error": "missing_markdown", "path": rel(md_path)})
    if not issue_csv_path.exists():
        issues.append({"error": "missing_issue_csv", "path": rel(issue_csv_path)})
    if payload.get("overall_status") != "PASS":
        issues.append({"error": "packet_integrity_not_pass", "actual": payload.get("overall_status")})
    if payload.get("claim_status") != "human_review_packet_integrity_ready_pending_human_returns":
        issues.append({"error": "claim_status_mismatch", "actual": payload.get("claim_status")})
    if summary.get("integrity_error_count") != 0:
        issues.append({"error": "integrity_errors_present", "actual": summary.get("integrity_error_count")})

    expected_values = [
        ("minimum_annotation_input_files", min_batches.get("annotation_input_files"), 10),
        ("minimum_annotation_missing_inputs", min_batches.get("missing_required_input_files"), 0),
        ("minimum_annotation_reviewed_present", min_batches.get("reviewed_files_present"), 0),
        ("minimum_annotation_chunks", min_batches.get("assigned_unique_chunks"), 100),
        ("minimum_annotation_candidate_edges", min_batches.get("candidate_edges_total"), 1371),
        ("minimum_annotation_batch_count", min_batches.get("batch_count"), 5),
        ("minimum_annotation_chunk_pair_mismatch_count", min_batches.get("chunk_pair_mismatch_count"), 0),
        ("mapping_candidate_rows", mapping.get("candidate_rows"), 220),
        ("mapping_unique_ids", mapping.get("unique_mapping_ids"), 220),
        ("mapping_source_standard_groups", mapping.get("source_standard_groups"), 44),
        ("mapping_group_size_min", mapping.get("group_size_min"), 5),
        ("mapping_group_size_max", mapping.get("group_size_max"), 5),
        ("mapping_completed_rows", mapping.get("completed_rows"), 0),
        ("crosswalk_candidate_rows", crosswalk.get("candidate_rows"), 220),
        ("crosswalk_unique_ids", crosswalk.get("unique_crosswalk_ids"), 220),
        ("crosswalk_source_tasks", crosswalk.get("source_tasks"), 22),
        ("crosswalk_group_size_min", crosswalk.get("group_size_min"), 10),
        ("crosswalk_group_size_max", crosswalk.get("group_size_max"), 10),
        ("crosswalk_completed_rows", crosswalk.get("completed_rows"), 0),
        ("active_effort_rows", active_effort.get("template_rows"), 204),
        ("active_effort_unique_ids", active_effort.get("unique_review_item_ids"), 204),
        ("active_effort_human_response_rows", active_effort.get("human_response_rows_present"), 0),
        ("strong_review_units", strong.get("review_unit_count"), 342),
        ("strong_source_chunks", strong.get("source_chunk_count"), 214),
        ("strong_candidate_edges", strong.get("candidate_edges_total"), 2048),
        ("return_manifest_required_files", returns.get("required_return_files"), 14),
        ("return_manifest_minimum_files", returns.get("minimum_paper_gate_return_files"), 11),
        ("return_manifest_input_missing", returns.get("input_files_missing"), 0),
        ("return_manifest_reviewed_present", returns.get("reviewed_files_present"), 0),
        ("handoff_bundle_count", handoff.get("bundle_count"), 9),
        ("handoff_missing_bundle_count", handoff.get("missing_bundle_count"), 0),
    ]
    for name, actual, expected in expected_values:
        if actual != expected:
            issues.append({"error": "count_mismatch", "field": name, "expected": expected, "actual": actual})

    expected_statuses = [
        ("minimum_annotation_claim_status", min_batches.get("claim_status"), "input_batches_ready_pending_human_annotation"),
        ("mapping_claim_status", mapping.get("claim_status"), "mapping_packet_ready_pending_expert_review"),
        ("crosswalk_claim_status", crosswalk.get("claim_status"), "crosswalk_packet_ready_pending_expert_review"),
        ("active_effort_claim_status", active_effort.get("claim_status"), "active_effort_packet_ready_pending_human_review"),
        ("strong_claim_status", strong.get("claim_status"), "optional_strong_packet_ready_pending_human_review"),
        ("return_manifest_claim_status", returns.get("claim_status"), "return_manifest_ready_pending_human_returns"),
        ("handoff_claim_status", handoff.get("claim_status"), "handoff_ready_pending_human_review"),
    ]
    for name, actual, expected in expected_statuses:
        if actual != expected:
            issues.append({"error": "status_mismatch", "field": name, "expected": expected, "actual": actual})

    evidence.update(
        {
            "overall_status": payload.get("overall_status"),
            "claim_status": payload.get("claim_status"),
            "summary": summary,
            "issue_count": len(issues),
        }
    )
    if issues:
        evidence["issues"] = issues[:20]
    add_check(
        checks,
        "human_review_packet_integrity",
        "FAIL" if issues else "PASS",
        "Human-review packet integrity is ready and still correctly marked pending human returns."
        if not issues
        else "Human-review packet integrity report has mismatches.",
        evidence,
    )


def validate_human_return_apply_wrapper_safety(checks, exp_dir):
    release_dir = exp_dir / "06_release"
    script_path = Path("scripts/run_cape_human_return_apply.sh")
    last_json_path = release_dir / "human_return_apply_last_run.json"
    last_md_path = release_dir / "human_return_apply_last_run.md"
    refusal_json_path = release_dir / "human_return_apply_refusal_last_run.json"
    refusal_md_path = release_dir / "human_return_apply_refusal_last_run.md"
    post_refresh_path = release_dir / "post_annotation_refresh_last_run.json"

    def as_int(value):
        try:
            return int(value)
        except Exception:
            return None

    try:
        last_run = read_json(last_json_path)
        refusal = read_json(refusal_json_path)
        post_refresh = read_json(post_refresh_path)
        last_md = last_md_path.read_text(encoding="utf-8")
        refusal_md = refusal_md_path.read_text(encoding="utf-8")
        script_text = script_path.read_text(encoding="utf-8")
    except Exception as exc:
        add_check(
            checks,
            "human_return_apply_wrapper_safety",
            "FAIL",
            "Human-return apply wrapper safety evidence cannot be read.",
            {
                "error": str(exc),
                "last_run": rel(last_json_path),
                "refusal": rel(refusal_json_path),
                "post_refresh": rel(post_refresh_path),
                "script": rel(script_path),
            },
        )
        return

    issues = []
    for pattern in [
        "ALLOW_EMPTY_APPLY",
        "Refusing APPLY_IMPORTS=1",
        "WRAPPER_REFUSAL_JSON",
        "wrapper_status",
        "human_return_apply_refusal_last_run",
        "apply_scope",
        "minimum_paper_gate_ready_after_preflight",
        "Partial validated returns may be applied incrementally",
    ]:
        if pattern not in script_text:
            issues.append({"error": "script_missing_safety_pattern", "pattern": pattern})

    last_run_status = last_run.get("wrapper_status")
    last_run_is_completed = last_run_status == "completed"
    last_run_is_refusal = last_run_status == "refused_empty_apply_no_reviewed_files"
    if not (last_run_is_completed or last_run_is_refusal):
        issues.append({"error": "last_run_unexpected_status", "actual": last_run_status})
    if last_run_is_completed:
        if as_int(last_run.get("exit_code")) != 0:
            issues.append({"error": "last_run_exit_code_not_zero", "actual": last_run.get("exit_code")})
        if str(last_run.get("apply_imports")) != "0":
            issues.append({"error": "last_run_not_dry_run", "actual": last_run.get("apply_imports")})
        if last_run.get("post_refresh_claim_status") != "post_annotation_refresh_success_pending_human_returns":
            issues.append({"error": "unexpected_last_run_post_refresh_status", "actual": last_run.get("post_refresh_claim_status")})
        if last_run.get("pre_human_handoff_status") != "PASS":
            issues.append({"error": "last_run_pre_human_handoff_not_pass", "actual": last_run.get("pre_human_handoff_status")})
        if last_run.get("release_checksum_status") != "OK":
            issues.append({"error": "last_run_release_checksum_not_ok", "actual": last_run.get("release_checksum_status")})
        if last_run.get("handoff_checksum_status") != "OK":
            issues.append({"error": "last_run_handoff_checksum_not_ok", "actual": last_run.get("handoff_checksum_status")})
        if (
            "APPLY_IMPORTS: `0`" not in last_md
            or "Wrapper status: `completed`" not in last_md
            or "Partial validated returns may be applied incrementally" not in last_md
        ):
            issues.append({"error": "last_run_markdown_missing_summary_markers", "path": rel(last_md_path)})
    elif last_run_is_refusal:
        if as_int(last_run.get("exit_code")) != 3:
            issues.append({"error": "last_run_refusal_exit_code_unexpected", "actual": last_run.get("exit_code")})
        if str(last_run.get("apply_imports")) != "1":
            issues.append({"error": "last_run_refusal_not_apply_mode", "actual": last_run.get("apply_imports")})

    if last_run.get("preflight_overall_status") != "pending_human_returns":
        issues.append({"error": "unexpected_last_run_preflight_status", "actual": last_run.get("preflight_overall_status")})
    if as_int(last_run.get("present_human_return_files")) != 0:
        issues.append({"error": "last_run_expected_zero_return_files", "actual": last_run.get("present_human_return_files")})
    if last_run.get("apply_scope") != "no_return_files":
        issues.append({"error": "last_run_apply_scope_unexpected", "actual": last_run.get("apply_scope")})
    if last_run.get("minimum_paper_gate_ready_after_preflight") is not False:
        issues.append(
            {
                "error": "last_run_minimum_gate_readiness_unexpected",
                "actual": last_run.get("minimum_paper_gate_ready_after_preflight"),
            }
        )
    if last_run.get("optional_mapping_ready_after_preflight") is not False:
        issues.append(
            {
                "error": "last_run_mapping_readiness_unexpected",
                "actual": last_run.get("optional_mapping_ready_after_preflight"),
            }
        )
    if last_run.get("optional_crosswalk_ready_after_preflight", False) is not False:
        issues.append(
            {
                "error": "last_run_crosswalk_readiness_unexpected",
                "actual": last_run.get("optional_crosswalk_ready_after_preflight"),
            }
        )
    if last_run.get("optional_active_effort_ready_after_preflight") is not False:
        issues.append(
            {
                "error": "last_run_active_effort_readiness_unexpected",
                "actual": last_run.get("optional_active_effort_ready_after_preflight"),
            }
        )
    if (
        "Apply scope: `no_return_files`" not in last_md
        or "Minimum paper gate ready after preflight: False" not in last_md
    ):
        issues.append({"error": "last_run_markdown_missing_readiness_markers", "path": rel(last_md_path)})

    if refusal.get("wrapper_status") != "refused_empty_apply_no_reviewed_files":
        issues.append({"error": "refusal_status_unexpected", "actual": refusal.get("wrapper_status")})
    if as_int(refusal.get("exit_code")) != 3:
        issues.append({"error": "refusal_exit_code_unexpected", "actual": refusal.get("exit_code")})
    if str(refusal.get("apply_imports")) != "1":
        issues.append({"error": "refusal_not_apply_mode", "actual": refusal.get("apply_imports")})
    if as_int(refusal.get("present_human_return_files")) != 0:
        issues.append({"error": "refusal_expected_zero_return_files", "actual": refusal.get("present_human_return_files")})
    if refusal.get("apply_scope") != "no_return_files":
        issues.append({"error": "refusal_apply_scope_unexpected", "actual": refusal.get("apply_scope")})
    if refusal.get("minimum_paper_gate_ready_after_preflight") is not False:
        issues.append(
            {
                "error": "refusal_minimum_gate_readiness_unexpected",
                "actual": refusal.get("minimum_paper_gate_ready_after_preflight"),
            }
        )
    for pattern in [
        "intentional safety refusal",
        "APPLY_IMPORTS=1",
        "ALLOW_EMPTY_APPLY=1",
        "Apply scope: `no_return_files`",
        "Minimum paper gate ready after preflight: False",
    ]:
        if pattern not in refusal_md:
            issues.append({"error": "refusal_markdown_missing_marker", "pattern": pattern, "path": rel(refusal_md_path)})

    if post_refresh.get("claim_status") != "post_annotation_refresh_success_pending_human_returns":
        issues.append({"error": "post_refresh_claim_status_unexpected", "actual": post_refresh.get("claim_status")})
    if str(post_refresh.get("apply_imports")) != "0":
        issues.append({"error": "post_refresh_not_dry_run", "actual": post_refresh.get("apply_imports")})
    if post_refresh.get("pre_human_handoff_status") != "PASS":
        issues.append({"error": "post_refresh_pre_human_handoff_not_pass", "actual": post_refresh.get("pre_human_handoff_status")})
    if as_int(post_refresh.get("present_human_return_files")) != 0:
        issues.append({"error": "post_refresh_expected_zero_return_files", "actual": post_refresh.get("present_human_return_files")})

    if issues:
        add_check(
            checks,
            "human_return_apply_wrapper_safety",
            "FAIL",
            "Human-return apply wrapper dry-run/refusal safety evidence is incomplete or stale.",
            {"issues": issues[:50]},
        )
        return

    add_check(
        checks,
        "human_return_apply_wrapper_safety",
        "PASS",
        "Human-return apply wrapper records dry-run success and empty-apply refusal evidence.",
        {
            "script": rel(script_path),
            "last_run": rel(last_json_path),
            "refusal": rel(refusal_json_path),
            "post_refresh": rel(post_refresh_path),
            "dry_run_status": last_run.get("wrapper_status"),
            "refusal_status": refusal.get("wrapper_status"),
            "present_human_return_files": last_run.get("present_human_return_files"),
            "apply_scope": last_run.get("apply_scope"),
            "minimum_paper_gate_ready_after_preflight": last_run.get("minimum_paper_gate_ready_after_preflight"),
            "optional_mapping_ready_after_preflight": last_run.get("optional_mapping_ready_after_preflight"),
            "optional_crosswalk_ready_after_preflight": last_run.get("optional_crosswalk_ready_after_preflight"),
            "optional_active_effort_ready_after_preflight": last_run.get("optional_active_effort_ready_after_preflight"),
            "release_checksum_status": last_run.get("release_checksum_status"),
            "handoff_checksum_status": last_run.get("handoff_checksum_status"),
        },
    )


def validate_strong_return_apply_wrapper_safety(checks, exp_dir):
    release_dir = exp_dir / "06_release"
    script_path = Path("scripts/run_cape_strong_return_apply.sh")
    last_json_path = release_dir / "strong_return_apply_last_run.json"
    last_md_path = release_dir / "strong_return_apply_last_run.md"
    refusal_json_path = release_dir / "strong_return_apply_refusal_last_run.json"
    refusal_md_path = release_dir / "strong_return_apply_refusal_last_run.md"
    preflight_path = release_dir / "strong_review_return_preflight.json"

    def as_int(value):
        try:
            return int(value)
        except Exception:
            return None

    try:
        last_run = read_json(last_json_path)
        refusal = read_json(refusal_json_path)
        preflight = read_json(preflight_path)
        last_md = last_md_path.read_text(encoding="utf-8")
        refusal_md = refusal_md_path.read_text(encoding="utf-8")
        script_text = script_path.read_text(encoding="utf-8")
    except Exception as exc:
        add_check(
            checks,
            "strong_return_apply_wrapper_safety",
            "FAIL",
            "Strong-return apply wrapper safety evidence cannot be read.",
            {
                "error": str(exc),
                "last_run": rel(last_json_path),
                "refusal": rel(refusal_json_path),
                "preflight": rel(preflight_path),
                "script": rel(script_path),
            },
        )
        return

    issues = []
    for pattern in [
        "ALLOW_EMPTY_APPLY",
        "Refusing APPLY_IMPORTS=1",
        "validate_cape_strong_review_returns.py",
        "strong_return_apply_refusal_last_run",
        "import_cape_gold_annotation.py",
        "ready_for_strong_claim_after_import",
    ]:
        if pattern not in script_text:
            issues.append({"error": "script_missing_safety_pattern", "pattern": pattern})

    if last_run.get("wrapper_status") != "completed":
        issues.append({"error": "last_run_unexpected_status", "actual": last_run.get("wrapper_status")})
    if as_int(last_run.get("exit_code")) != 0:
        issues.append({"error": "last_run_exit_code_not_zero", "actual": last_run.get("exit_code")})
    if str(last_run.get("apply_imports")) != "0":
        issues.append({"error": "last_run_not_dry_run", "actual": last_run.get("apply_imports")})
    if last_run.get("preflight_overall_status") != "pending_strong_human_returns":
        issues.append({"error": "unexpected_last_run_preflight_status", "actual": last_run.get("preflight_overall_status")})
    if as_int(last_run.get("present_strong_return_files")) != 0:
        issues.append({"error": "last_run_expected_zero_strong_return_files", "actual": last_run.get("present_strong_return_files")})
    if last_run.get("apply_scope") != "no_strong_return_files":
        issues.append({"error": "last_run_apply_scope_unexpected", "actual": last_run.get("apply_scope")})
    if last_run.get("ready_for_strong_iaa") is not False:
        issues.append({"error": "last_run_strong_iaa_readiness_unexpected", "actual": last_run.get("ready_for_strong_iaa")})
    if last_run.get("ready_for_strong_claim_after_import") is not False:
        issues.append({"error": "last_run_strong_claim_readiness_unexpected", "actual": last_run.get("ready_for_strong_claim_after_import")})
    for pattern in [
        "Wrapper status: `completed`",
        "APPLY_IMPORTS: `0`",
        "Apply scope: `no_strong_return_files`",
        "Ready for strong claim after import: False",
    ]:
        if pattern not in last_md:
            issues.append({"error": "last_run_markdown_missing_marker", "pattern": pattern, "path": rel(last_md_path)})

    if refusal.get("wrapper_status") != "refused_empty_apply_no_strong_reviewed_files":
        issues.append({"error": "refusal_status_unexpected", "actual": refusal.get("wrapper_status")})
    if as_int(refusal.get("exit_code")) != 3:
        issues.append({"error": "refusal_exit_code_unexpected", "actual": refusal.get("exit_code")})
    if str(refusal.get("apply_imports")) != "1":
        issues.append({"error": "refusal_not_apply_mode", "actual": refusal.get("apply_imports")})
    if as_int(refusal.get("present_strong_return_files")) != 0:
        issues.append({"error": "refusal_expected_zero_strong_return_files", "actual": refusal.get("present_strong_return_files")})
    if refusal.get("apply_scope") != "no_strong_return_files":
        issues.append({"error": "refusal_apply_scope_unexpected", "actual": refusal.get("apply_scope")})
    if refusal.get("ready_for_strong_claim_after_import") is not False:
        issues.append({"error": "refusal_strong_claim_readiness_unexpected", "actual": refusal.get("ready_for_strong_claim_after_import")})
    for pattern in [
        "intentional safety refusal",
        "APPLY_IMPORTS=1",
        "ALLOW_EMPTY_APPLY=1",
        "Apply scope: `no_strong_return_files`",
        "Ready for strong claim after import: False",
    ]:
        if pattern not in refusal_md:
            issues.append({"error": "refusal_markdown_missing_marker", "pattern": pattern, "path": rel(refusal_md_path)})

    if preflight.get("overall_status") != "pending_strong_human_returns":
        issues.append({"error": "unexpected_preflight_status", "actual": preflight.get("overall_status")})
    summary = preflight.get("summary") or {}
    if as_int(summary.get("expected_review_units")) < 300:
        issues.append({"error": "strong_review_units_below_300", "actual": summary.get("expected_review_units")})
    if summary.get("ready_for_strong_claim_after_import") is not False:
        issues.append({"error": "preflight_strong_claim_readiness_unexpected", "actual": summary.get("ready_for_strong_claim_after_import")})

    if issues:
        add_check(
            checks,
            "strong_return_apply_wrapper_safety",
            "FAIL",
            "Strong-return apply wrapper dry-run/refusal safety evidence is incomplete or stale.",
            {"issues": issues[:50]},
        )
        return

    add_check(
        checks,
        "strong_return_apply_wrapper_safety",
        "PASS",
        "Strong-return apply wrapper records dry-run success and empty-apply refusal evidence.",
        {
            "script": rel(script_path),
            "last_run": rel(last_json_path),
            "refusal": rel(refusal_json_path),
            "preflight": rel(preflight_path),
            "present_strong_return_files": last_run.get("present_strong_return_files"),
            "apply_scope": last_run.get("apply_scope"),
            "expected_review_units": last_run.get("expected_review_units"),
            "ready_for_strong_iaa": last_run.get("ready_for_strong_iaa"),
            "ready_for_strong_claim_after_import": last_run.get("ready_for_strong_claim_after_import"),
        },
    )


def validate_eacl_paper_draft(checks, exp_dir):
    draft_path = exp_dir / "07_reports/eacl_paper_draft.md"
    status_path = exp_dir / "06_release/eacl_paper_draft_status.json"
    plan_path = exp_dir / "06_release/human_gate_action_plan.json"
    master_path = exp_dir / "06_release/human_review_master_checklist_ko.json"
    preflight_path = exp_dir / "06_release/human_review_return_preflight.json"
    claim_path = exp_dir / "06_release/claim_gate_report.json"
    prehuman_path = exp_dir / "06_release/pre_human_handoff_validation.json"
    try:
        status = read_json(status_path)
        plan = read_json(plan_path)
        master = read_json(master_path)
        preflight = read_json(preflight_path)
        claim = read_json(claim_path)
        prehuman = read_json(prehuman_path)
        draft_text = draft_path.read_text(encoding="utf-8")
    except Exception as exc:
        add_check(
            checks,
            "eacl_paper_draft_claim_safety",
            "FAIL",
            "EACL paper draft or supporting JSON cannot be read.",
            {"error": str(exc), "draft_path": rel(draft_path), "status_path": rel(status_path)},
        )
        return

    effective_prehuman = effective_prehuman_summary(prehuman)
    required_returns = plan.get("required_return_files") or []
    required_return_count = len(required_returns)
    present_return_count = sum(1 for row in required_returns if truthy_present(row.get("present")))
    minimum_returns = [row for row in required_returns if truthy_present(row.get("required_for_minimum", True))]
    optional_returns = [row for row in required_returns if not truthy_present(row.get("required_for_minimum", True))]
    minimum_return_count = len(minimum_returns)
    minimum_present_count = sum(1 for row in minimum_returns if truthy_present(row.get("present")))
    optional_return_count = len(optional_returns)
    optional_present_count = sum(1 for row in optional_returns if truthy_present(row.get("present")))
    master_summary = master.get("summary") or {}
    optional_structural_count = int(master_summary.get("optional_structural_return_files") or 0)
    optional_structural_present = int(master_summary.get("optional_structural_return_files_present") or 0)
    master_return_count = int(master_summary.get("required_return_files") or required_return_count) + optional_structural_count
    master_present_count = int(master_summary.get("required_return_files_present") or present_return_count) + optional_structural_present
    issues = []

    if status.get("safe_to_use_as_submission") is not False:
        issues.append({"error": "draft_status_not_claim_safe", "safe_to_use_as_submission": status.get("safe_to_use_as_submission")})
    if status.get("submission_ready") is not False:
        issues.append({"error": "draft_status_submission_ready_should_be_false", "submission_ready": status.get("submission_ready")})
    if status.get("claim_status") != KNOWN_HUMAN_PENDING_STATUS:
        issues.append({"error": "draft_claim_status_mismatch", "actual": status.get("claim_status"), "expected": KNOWN_HUMAN_PENDING_STATUS})
    if status.get("required_failure_count") != claim.get("required_failure_count"):
        issues.append(
            {
                "error": "required_failure_count_mismatch",
                "draft": status.get("required_failure_count"),
                "claim_gate": claim.get("required_failure_count"),
            }
        )
    if status.get("required_human_return_files") != required_return_count:
        issues.append(
            {
                "error": "required_human_return_files_mismatch",
                "draft": status.get("required_human_return_files"),
                "action_plan": required_return_count,
            }
        )
    expected_return_fields = {
        "minimum_paper_gate_return_files": minimum_return_count,
        "minimum_paper_gate_return_files_present": minimum_present_count,
        "optional_strong_return_files": optional_return_count,
        "optional_strong_return_files_present": optional_present_count,
        "tracked_human_return_files": required_return_count,
        "tracked_human_return_files_present": present_return_count,
        "optional_structural_return_files": optional_structural_count,
        "optional_structural_return_files_present": optional_structural_present,
        "master_return_files": master_return_count,
        "master_return_files_present": master_present_count,
    }
    for field, expected in expected_return_fields.items():
        if status.get(field) != expected:
            issues.append({"error": f"{field}_mismatch", "draft": status.get(field), "expected": expected})
    if status.get("return_preflight_status") != preflight.get("overall_status"):
        issues.append(
            {
                "error": "return_preflight_status_mismatch",
                "draft": status.get("return_preflight_status"),
                "preflight": preflight.get("overall_status"),
            }
        )
    if status.get("pre_human_handoff_status") != effective_prehuman.get("overall_status"):
        issues.append(
            {
                "error": "pre_human_handoff_status_mismatch",
                "draft": status.get("pre_human_handoff_status"),
                "pre_human": effective_prehuman.get("overall_status"),
            }
        )

    required_patterns = [
        "**Status:** internal claim-safe draft, not a submission-ready manuscript.",
        "## Introduction",
        "## Related Work",
        "## Task Definition",
        "## Dataset and Annotation",
        "## Method: CAPE-KG",
        "## Experiments",
        "## Analysis",
        "## Conclusion",
        "## Limitations",
        "## Ethical Considerations",
        "## References",
        f"- Pre-human handoff validation: `{effective_prehuman.get('overall_status')}`",
        f"- Minimum paper-gate human-return files: `{minimum_present_count}/{minimum_return_count}`",
        f"- Optional/strong claim human-return files: `{optional_present_count}/{optional_return_count}`",
        f"- Required claim/human-return files: `{present_return_count}/{required_return_count}`",
        f"- Optional structural review files: `{optional_structural_present}/{optional_structural_count}`",
        f"- All master return files: `{master_present_count}/{master_return_count}`",
        "16-file master manifest",
        "### Human Review Return Manifest",
        f"| Total | {required_return_count} | {present_return_count} | all human-return files required before final claims |",
        "### Handoff Bundles",
        "- Human-gold annotation, adjudication, and IAA are not complete.",
        "- Mapping downstream metrics require expert-reviewed NCS/PCF candidate groups.",
        "- Active-review efficiency requires returned reviewer timing/correction files and adjudicated outcomes.",
    ]
    missing_patterns = [pattern for pattern in required_patterns if pattern not in draft_text]
    if missing_patterns:
        issues.append({"error": "draft_missing_claim_safety_text", "missing_patterns": missing_patterns})

    if "safe_to_use_as_submission\": true" in status_path.read_text(encoding="utf-8"):
        issues.append({"error": "status_json_contains_submission_safe_true"})

    if issues:
        add_check(
            checks,
            "eacl_paper_draft_claim_safety",
            "FAIL",
            "EACL paper draft does not match the current conservative claim gate, human-return plan, and standard paper section skeleton.",
            {"path": rel(draft_path), "status_path": rel(status_path), "issues": issues[:50]},
        )
        return

    add_check(
        checks,
        "eacl_paper_draft_claim_safety",
        "PASS",
        "EACL paper draft is synchronized with the conservative claim gate, split human-return plan, and standard paper section skeleton.",
        {
            "path": rel(draft_path),
            "status_path": rel(status_path),
            "minimum_paper_gate_return_files": minimum_return_count,
            "minimum_paper_gate_present_files": minimum_present_count,
            "optional_strong_return_files": optional_return_count,
            "optional_strong_present_files": optional_present_count,
            "tracked_human_return_files": required_return_count,
            "present_human_return_files": present_return_count,
            "optional_structural_return_files": optional_structural_count,
            "optional_structural_present_files": optional_structural_present,
            "master_return_files": master_return_count,
            "master_return_files_present": master_present_count,
            "return_preflight_status": preflight.get("overall_status"),
            "safe_to_use_as_submission": status.get("safe_to_use_as_submission"),
        },
    )


def validate_paper_section_source_map(checks, exp_dir):
    json_path = exp_dir / "06_release/paper_section_source_map.json"
    md_path = exp_dir / "06_release/paper_section_source_map.md"
    try:
        payload = read_json(json_path)
        text = md_path.read_text(encoding="utf-8")
    except Exception as exc:
        add_check(
            checks,
            "paper_section_source_map",
            "FAIL",
            "Paper section source map cannot be read.",
            {"json": rel(json_path), "markdown": rel(md_path), "error": str(exc)},
        )
        return

    summary = payload.get("summary") or {}
    sections = payload.get("sections") or []
    issues = []
    if payload.get("overall_status") != "PASS":
        issues.append({"error": "overall_status_not_pass", "actual": payload.get("overall_status")})
    if payload.get("claim_status") != "paper_section_source_map_ready_not_submission_complete":
        issues.append({"error": "claim_status_mismatch", "actual": payload.get("claim_status")})
    if payload.get("safe_to_use_as_submission") is not False:
        issues.append({"error": "safe_to_use_as_submission_should_be_false", "actual": payload.get("safe_to_use_as_submission")})
    if payload.get("submission_ready") is not False:
        issues.append({"error": "submission_ready_should_be_false", "actual": payload.get("submission_ready")})
    if summary.get("total_sections") != 16:
        issues.append({"error": "unexpected_section_count", "actual": summary.get("total_sections"), "expected": 16})
    if summary.get("present_sections") != summary.get("total_sections"):
        issues.append(
            {
                "error": "draft_section_anchor_missing",
                "present": summary.get("present_sections"),
                "total": summary.get("total_sections"),
                "missing": payload.get("missing_draft_anchors"),
            }
        )
    if summary.get("missing_evidence_files") != 0:
        issues.append({"error": "missing_evidence_files", "paths": payload.get("missing_evidence_files")})
    statuses = {row.get("claim_status") for row in sections}
    for required_status in [
        "pending_human_gold",
        "pending_expert_review",
        "diagnostic_only_until_human_gold",
        "not_submission_ready",
    ]:
        if required_status not in statuses:
            issues.append({"error": "missing_expected_claim_status", "claim_status": required_status})
    required_patterns = [
        "# CAPE-KG Paper Section Source Map",
        "## Section Map",
        "## Blocking Gate Alignment",
        "## Missing Evidence",
        "safe_to_use_as_submission",
        "paper_section_source_map_ready_not_submission_complete",
        "diagnostic_only_until_human_gold",
        "pending_expert_review",
    ]
    missing_patterns = [pattern for pattern in required_patterns if pattern not in text]
    if missing_patterns:
        issues.append({"error": "markdown_missing_required_patterns", "patterns": missing_patterns})

    if issues:
        add_check(
            checks,
            "paper_section_source_map",
            "FAIL",
            "Paper section source map is missing section coverage, claim-safety markers, or evidence files.",
            {"json": rel(json_path), "markdown": rel(md_path), "issues": issues[:30]},
        )
        return

    add_check(
        checks,
        "paper_section_source_map",
        "PASS",
        "Paper section source map covers the planned long-paper sections and preserves human-gold/expert-review claim boundaries.",
        {
            "json": rel(json_path),
            "markdown": rel(md_path),
            "sections": summary.get("total_sections"),
            "evidence_file_references": summary.get("evidence_file_references"),
            "claim_status": payload.get("claim_status"),
            "safe_to_use_as_submission": payload.get("safe_to_use_as_submission"),
        },
    )


def validate_eacl_submission_package_manifest(checks, exp_dir):
    json_path = exp_dir / "06_release/eacl_submission_package_manifest.json"
    md_path = exp_dir / "06_release/eacl_submission_package_manifest.md"
    try:
        payload = read_json(json_path)
        text = md_path.read_text(encoding="utf-8")
        latest_index = read_json(exp_dir / "06_release/latest_release_bundle_index.json")
    except Exception as exc:
        add_check(
            checks,
            "eacl_submission_package_manifest",
            "FAIL",
            "EACL submission package manifest cannot be read.",
            {"json": rel(json_path), "markdown": rel(md_path), "error": str(exc)},
        )
        return

    summary = payload.get("summary") or {}
    latest_current = latest_index.get("current") or {}
    latest_internal_bundle = (latest_current.get("internal_bundle") or {}).get("path")
    latest_public_bundle = (latest_current.get("public_safe_bundle") or {}).get("path")
    components = payload.get("components") or []
    issues = []
    if payload.get("overall_status") != "PASS":
        issues.append({"error": "overall_status_not_pass", "actual": payload.get("overall_status")})
    if payload.get("claim_status") != "eacl_submission_package_manifest_ready_not_submission_complete":
        issues.append({"error": "claim_status_mismatch", "actual": payload.get("claim_status")})
    if payload.get("safe_to_use_as_submission") is not False:
        issues.append({"error": "safe_to_use_as_submission_should_be_false", "actual": payload.get("safe_to_use_as_submission")})
    if payload.get("submission_ready") is not False:
        issues.append({"error": "submission_ready_should_be_false", "actual": payload.get("submission_ready")})
    if summary.get("component_count") != 22:
        issues.append({"error": "unexpected_component_count", "actual": summary.get("component_count"), "expected": 22})
    if summary.get("missing_evidence_files") != 0:
        issues.append({"error": "missing_evidence_files", "paths": payload.get("missing_evidence_files")})
    if summary.get("claim_gate_overall_status") != "FAIL":
        issues.append({"error": "claim_gate_should_remain_fail_pre_human", "actual": summary.get("claim_gate_overall_status")})
    if summary.get("pre_human_validation_status") != "PASS":
        issues.append({"error": "pre_human_validation_not_pass", "actual": summary.get("pre_human_validation_status")})
    if summary.get("release_stamp") != latest_index.get("stamp"):
        issues.append(
            {
                "error": "latest_release_stamp_mismatch",
                "expected": latest_index.get("stamp"),
                "actual": summary.get("release_stamp"),
            }
        )
    if summary.get("internal_bundle") != latest_internal_bundle:
        issues.append(
            {
                "error": "latest_internal_bundle_mismatch",
                "expected": latest_internal_bundle,
                "actual": summary.get("internal_bundle"),
            }
        )
    if summary.get("public_safe_bundle") != latest_public_bundle:
        issues.append(
            {
                "error": "latest_public_safe_bundle_mismatch",
                "expected": latest_public_bundle,
                "actual": summary.get("public_safe_bundle"),
            }
        )
    statuses = {row.get("status") for row in components}
    for required_status in [
        "pending_human_returns",
        "pending_human_effort",
        "candidate_only_pending_expert_review",
        "ready_pending_human_returns",
        "ready_diagnostic_only",
        "ready_not_submission_complete",
        "ready_not_upload_ready",
        "ready_final_answers_pending",
        "ready_not_human_gold_claim",
    ]:
        if required_status not in statuses:
            issues.append({"error": "missing_expected_component_status", "status": required_status})
    if summary.get("anonymized_submission_prep_claim_status") != "anonymized_submission_prep_ready_not_upload_ready":
        issues.append(
            {
                "error": "anonymized_submission_prep_claim_status_mismatch",
                "actual": summary.get("anonymized_submission_prep_claim_status"),
            }
        )
    if summary.get("anonymized_submission_upload_ready") is not False:
        issues.append({"error": "anonymized_upload_ready_should_be_false", "actual": summary.get("anonymized_submission_upload_ready")})
    if summary.get("responsible_nlp_checklist_claim_status") != "responsible_nlp_checklist_prep_ready_not_final_answers":
        issues.append(
            {
                "error": "responsible_nlp_checklist_claim_status_mismatch",
                "actual": summary.get("responsible_nlp_checklist_claim_status"),
            }
        )
    if summary.get("responsible_nlp_final_answers_ready") is not False:
        issues.append({"error": "responsible_nlp_final_answers_should_be_false", "actual": summary.get("responsible_nlp_final_answers_ready")})
    if summary.get("experiment_reproduction_card_claim_status") != "experiment_reproduction_card_ready_not_human_gold_claim":
        issues.append(
            {
                "error": "experiment_reproduction_card_claim_status_mismatch",
                "actual": summary.get("experiment_reproduction_card_claim_status"),
            }
        )
    if summary.get("experiment_reproduction_condition_count") != 14:
        issues.append({"error": "experiment_reproduction_condition_count_mismatch", "actual": summary.get("experiment_reproduction_condition_count")})
    if summary.get("experiment_reproduction_final_performance_claim_ready") is not False:
        issues.append(
            {
                "error": "experiment_reproduction_final_claim_ready_should_be_false",
                "actual": summary.get("experiment_reproduction_final_performance_claim_ready"),
            }
        )
    required_patterns = [
        "# CAPE-KG EACL Submission Package Manifest",
        "Safe to use as submission",
        "Submission ready",
        "## Package Components",
        "## Submission Blockers",
        "eacl_submission_package_manifest_ready_not_submission_complete",
        "pending_human_returns",
        "candidate_only_pending_expert_review",
        "ready_pending_human_returns",
        "ready_diagnostic_only",
        "Claim-language guardrails",
        "Reviewer-question response preparation map",
        "Submission timeline and critical-path action board",
        "Paper table blueprint and promotion gates",
        "ARR/EACL submission policy checklist",
        "Anonymized submission prep and public-safe upload risk scan",
        "Responsible NLP checklist prep and evidence map",
        "Experiment reproduction card for baselines, ablations, commands, and outputs",
    ]
    missing_patterns = [pattern for pattern in required_patterns if pattern not in text]
    if missing_patterns:
        issues.append({"error": "markdown_missing_required_patterns", "patterns": missing_patterns})

    if issues:
        add_check(
            checks,
            "eacl_submission_package_manifest",
            "FAIL",
            "EACL submission package manifest is missing claim-safety markers, blockers, or evidence files.",
            {"json": rel(json_path), "markdown": rel(md_path), "issues": issues[:30]},
        )
        return

    add_check(
        checks,
        "eacl_submission_package_manifest",
        "PASS",
        "EACL submission package manifest separates ready diagnostic/release components from human-gold and expert-review blockers.",
        {
            "json": rel(json_path),
            "markdown": rel(md_path),
            "components": summary.get("component_count"),
            "pending_components": summary.get("pending_component_count"),
            "claim_status": payload.get("claim_status"),
            "safe_to_use_as_submission": payload.get("safe_to_use_as_submission"),
        },
    )


def validate_post_human_scoring_readiness(checks, exp_dir):
    json_path = exp_dir / "06_release/post_human_scoring_readiness.json"
    md_path = exp_dir / "06_release/post_human_scoring_readiness.md"
    prehuman_path = exp_dir / "06_release/pre_human_handoff_validation.json"
    try:
        payload = read_json(json_path)
        text = md_path.read_text(encoding="utf-8")
        prehuman = read_json(prehuman_path)
    except Exception as exc:
        add_check(
            checks,
            "post_human_scoring_readiness",
            "FAIL",
            "Post-human scoring readiness map cannot be read.",
            {"json": rel(json_path), "markdown": rel(md_path), "pre_human_validation": rel(prehuman_path), "error": str(exc)},
        )
        return

    summary = payload.get("summary") or {}
    return_summary = summary.get("return_summary") or {}
    metrics = payload.get("metrics") or []
    issues = []
    if payload.get("overall_status") != "PASS":
        issues.append({"error": "overall_status_not_pass", "actual": payload.get("overall_status")})
    if payload.get("claim_status") != "post_human_scoring_readiness_ready_pending_human_returns":
        issues.append({"error": "claim_status_mismatch", "actual": payload.get("claim_status")})
    if payload.get("safe_to_use_as_submission") is not False:
        issues.append({"error": "safe_to_use_as_submission_should_be_false", "actual": payload.get("safe_to_use_as_submission")})
    if payload.get("submission_ready") is not False:
        issues.append({"error": "submission_ready_should_be_false", "actual": payload.get("submission_ready")})
    if summary.get("metric_count") != 10:
        issues.append({"error": "unexpected_metric_count", "actual": summary.get("metric_count"), "expected": 10})
    effective_prehuman = effective_prehuman_summary(prehuman)
    expected_prehuman_status = effective_prehuman.get("overall_status")
    expected_prehuman_counts = effective_prehuman.get("status_counts")
    expected_prehuman_check_count = effective_prehuman.get("check_count")
    expected_prehuman_claim_status = (
        "pre_human_handoff_ready_not_submission_complete"
        if expected_prehuman_status == "PASS"
        else prehuman.get("claim_status")
    )
    if summary.get("pre_human_validation_status") != expected_prehuman_status:
        issues.append(
            {
                "error": "pre_human_validation_status_stale",
                "actual": summary.get("pre_human_validation_status"),
                "expected": expected_prehuman_status,
            }
        )
    if summary.get("pre_human_validation_counts") != expected_prehuman_counts:
        issues.append(
            {
                "error": "pre_human_validation_counts_stale",
                "actual": summary.get("pre_human_validation_counts"),
                "expected": expected_prehuman_counts,
            }
        )
    if summary.get("pre_human_validation_check_count") != expected_prehuman_check_count:
        issues.append(
            {
                "error": "pre_human_validation_check_count_stale",
                "actual": summary.get("pre_human_validation_check_count"),
                "expected": expected_prehuman_check_count,
            }
        )
    if summary.get("pre_human_validation_claim_status") != expected_prehuman_claim_status:
        issues.append(
            {
                "error": "pre_human_validation_claim_status_stale",
                "actual": summary.get("pre_human_validation_claim_status"),
                "expected": expected_prehuman_claim_status,
            }
        )
    if return_summary.get("tracked_return_files") != 14:
        issues.append({"error": "unexpected_tracked_return_files", "actual": return_summary.get("tracked_return_files"), "expected": 14})
    if int(return_summary.get("present_return_files") or 0) > int(return_summary.get("tracked_return_files") or 0):
        issues.append(
            {
                "error": "present_return_files_exceed_tracked_files",
                "present": return_summary.get("present_return_files"),
                "tracked": return_summary.get("tracked_return_files"),
            }
        )
    if int(return_summary.get("present_return_files") or 0) == 0:
        if summary.get("claimable_metric_count") != 0:
            issues.append({"error": "metrics_should_not_be_claimable_without_returns", "actual": summary.get("claimable_metric_count")})
        if summary.get("pending_metric_count") != summary.get("metric_count"):
            issues.append(
                {
                    "error": "pending_metric_count_mismatch_without_returns",
                    "pending": summary.get("pending_metric_count"),
                    "metric_count": summary.get("metric_count"),
                }
            )
    if payload.get("missing_outputs_or_evidence"):
        issues.append({"error": "missing_outputs_or_evidence", "paths": payload.get("missing_outputs_or_evidence")})
    metric_ids = {row.get("metric_id") for row in metrics}
    for required_metric in [
        "M01_node_f1",
        "M02_edge_f1",
        "M03_evidence_exact_iou",
        "M04_unsupported_edge_rate",
        "M05_ontology_conformance",
        "M06_procedural_consistency",
        "M07_cq_answerability",
        "M08_mapping_pk_mrr_ndcg",
        "M09_crosswalk_accept_utility",
        "M10_active_review_efficiency",
    ]:
        if required_metric not in metric_ids:
            issues.append({"error": "missing_metric_id", "metric_id": required_metric})
    required_patterns = [
        "# CAPE-KG Post-Human Scoring Readiness",
        "post_human_scoring_readiness_ready_pending_human_returns",
        "Node F1",
        "Edge F1",
        "Evidence Exact Match / IoU",
        "NCS/PCF Mapping P@K / MRR / nDCG",
        "Active Review Efficiency",
        "pre_human_validation_check_count",
        "pre_human_validation_claim_status",
        "APPLY_IMPORTS=1 bash scripts/run_cape_human_return_apply.sh",
    ]
    missing_patterns = [pattern for pattern in required_patterns if pattern not in text]
    if missing_patterns:
        issues.append({"error": "markdown_missing_required_patterns", "patterns": missing_patterns})

    if issues:
        add_check(
            checks,
            "post_human_scoring_readiness",
            "FAIL",
            "Post-human scoring readiness map is missing metric coverage, claim-safety markers, or return-file alignment.",
            {"json": rel(json_path), "markdown": rel(md_path), "pre_human_validation": rel(prehuman_path), "issues": issues[:30]},
        )
        return

    add_check(
        checks,
        "post_human_scoring_readiness",
        "PASS",
        "Post-human scoring readiness map links plan metrics to human/expert return files, refresh commands, and output tables.",
        {
            "json": rel(json_path),
            "markdown": rel(md_path),
            "metrics": summary.get("metric_count"),
            "pending_metrics": summary.get("pending_metric_count"),
            "tracked_return_files": return_summary.get("tracked_return_files"),
            "present_return_files": return_summary.get("present_return_files"),
            "claim_status": payload.get("claim_status"),
            "pre_human_validation": rel(prehuman_path),
            "pre_human_validation_check_count": summary.get("pre_human_validation_check_count"),
        },
    )


def validate_current_reports_index(checks, exp_dir):
    index_path = exp_dir / "07_reports/README_current_reports_ko.md"
    issues = []
    try:
        text = index_path.read_text(encoding="utf-8")
    except Exception as exc:
        add_check(
            checks,
            "current_reports_index",
            "FAIL",
            "Current report index cannot be read.",
            {"path": rel(index_path), "error": str(exc)},
        )
        return

    required_patterns = [
        "# 현재 사용할 보고서 인덱스",
        "professor_report_core_essentials_prompt_cq_node_edge_separate_20260629_ko.md",
        "professor_report_core_essentials_separate_from_slides_20260629_ko.md",
        "professor_report_core_summary_separate_from_slides_sync4_20260629_ko.md",
        "professor_report_core_summary_separate_from_slides_latest_20260629_ko.md",
        "professor_report_key_summary_separate_from_slides_20260629_ko.md",
        "professor_report_core_contents_separate_20260629_ko.md",
        "professor_report_key_content_only_prompt_cq_node_edge_20260629_ko.md",
        "professor_report_core_methodology_prompt_node_edge_summary_20260629_ko.md",
        "professor_report_core_summary_current_20260629_ko.md",
        "professor_report_core_briefing_prompt_cq_node_edge_current_20260628_ko.md",
        "professor_report_slide_contents_current_20260628_ko.md",
        "professor_report_core_summary_current_20260628_ko.md",
        "eacl_paper_draft.md",
        "../06_release/eacl_plan_compliance_matrix.md",
        "../06_release/revised_plan_section_status_ko.md",
        "../06_release/submission_completion_audit_ko.md",
        "../06_release/claimable_main_table.md",
        "../06_release/claim_language_guardrails.md",
        "../06_release/reviewer_response_prep.md",
        "../06_release/submission_timeline_action_board.md",
        "../06_release/claim_gate_report.md",
        "../06_release/paper_section_source_map.md",
        "../06_release/paper_table_blueprint.md",
        "../06_release/eacl_submission_package_manifest.md",
        "../06_release/arr_submission_policy_checklist.md",
        "../06_release/anonymized_submission_prep.md",
        "../06_release/responsible_nlp_checklist_prep.md",
        "../06_release/experiment_reproduction_card.md",
        "../06_release/post_human_scoring_readiness.md",
        "../06_release/pre_human_handoff_validation.md",
        "../06_release/latest_release_bundle_index.md",
        "claim gate는 현재 expected `FAIL`",
        "Human-gold annotation",
        "IAA",
        "Adjudication",
        "Mapping expert review",
        "Active-review human effort",
        "run_cape_post_annotation_refresh.sh",
    ]
    missing_patterns = [pattern for pattern in required_patterns if pattern not in text]
    if missing_patterns:
        issues.append({"error": "missing_required_patterns", "patterns": missing_patterns})

    forbidden_patterns = [
        "20260628T233323Z",
        "checks: 52",
        "Checks: 52",
    ]
    stale_hits = [pattern for pattern in forbidden_patterns if pattern in text]
    if stale_hits:
        issues.append({"error": "stale_hardcoded_summary_values", "patterns": stale_hits})

    referenced_files = [
        exp_dir / "07_reports/professor_report_core_essentials_prompt_cq_node_edge_separate_20260629_ko.md",
        exp_dir / "07_reports/professor_report_core_essentials_separate_from_slides_20260629_ko.md",
        exp_dir / "07_reports/professor_report_core_summary_separate_from_slides_sync4_20260629_ko.md",
        exp_dir / "07_reports/professor_report_core_summary_separate_from_slides_latest_20260629_ko.md",
        exp_dir / "07_reports/professor_report_key_summary_separate_from_slides_20260629_ko.md",
        exp_dir / "07_reports/professor_report_core_contents_separate_20260629_ko.md",
        exp_dir / "07_reports/professor_report_key_content_only_prompt_cq_node_edge_20260629_ko.md",
        exp_dir / "07_reports/professor_report_core_methodology_prompt_node_edge_summary_20260629_ko.md",
        exp_dir / "07_reports/professor_report_core_summary_current_20260629_ko.md",
        exp_dir / "07_reports/professor_report_core_briefing_prompt_cq_node_edge_current_20260628_ko.md",
        exp_dir / "07_reports/professor_report_slide_contents_current_20260628_ko.md",
        exp_dir / "07_reports/professor_report_core_summary_current_20260628_ko.md",
        exp_dir / "07_reports/eacl_paper_draft.md",
        exp_dir / "06_release/eacl_plan_compliance_matrix.md",
        exp_dir / "06_release/revised_plan_section_status_ko.md",
        exp_dir / "06_release/submission_completion_audit_ko.md",
        exp_dir / "06_release/claimable_main_table.md",
        exp_dir / "06_release/claim_language_guardrails.md",
        exp_dir / "06_release/reviewer_response_prep.md",
        exp_dir / "06_release/submission_timeline_action_board.md",
        exp_dir / "06_release/claim_gate_report.md",
        exp_dir / "06_release/paper_section_source_map.md",
        exp_dir / "06_release/paper_table_blueprint.md",
        exp_dir / "06_release/eacl_submission_package_manifest.md",
        exp_dir / "06_release/arr_submission_policy_checklist.md",
        exp_dir / "06_release/anonymized_submission_prep.md",
        exp_dir / "06_release/responsible_nlp_checklist_prep.md",
        exp_dir / "06_release/experiment_reproduction_card.md",
        exp_dir / "06_release/post_human_scoring_readiness.md",
        exp_dir / "06_release/pre_human_handoff_validation.md",
        exp_dir / "06_release/latest_release_bundle_index.md",
    ]
    missing_files = [rel(path) for path in referenced_files if not path.exists() or path.stat().st_size == 0]
    if missing_files:
        issues.append({"error": "referenced_files_missing_or_empty", "paths": missing_files})

    if issues:
        add_check(
            checks,
            "current_reports_index",
            "FAIL",
            "Current report index is missing canonical report references or contains stale hardcoded summary values.",
            {"path": rel(index_path), "issues": issues[:20]},
        )
        return

    add_check(
        checks,
        "current_reports_index",
        "PASS",
        "Current report index points users to the canonical professor-report, paper-draft, release-gate, and post-annotation refresh artifacts.",
        {
            "path": rel(index_path),
            "canonical_professor_reports": 11,
            "release_gate_references": 14,
            "referenced_files_checked": len(referenced_files),
        },
    )


def validate_public_reproducibility_manifest(checks, exp_dir):
    release_dir = exp_dir / "06_release"
    json_path = release_dir / "public_reproducibility_manifest.json"
    md_path = release_dir / "public_reproducibility_manifest.md"
    csv_path = release_dir / "public_reproducibility_manifest.csv"
    latest_path = release_dir / "latest_release_bundle_index.json"
    try:
        manifest = read_json(json_path)
        csv_rows = read_csv_rows(csv_path)
        latest = read_json(latest_path)
    except Exception as exc:
        add_check(
            checks,
            "public_reproducibility_manifest",
            "FAIL",
            "Public reproducibility manifest cannot be read.",
            {"error": str(exc), "json": rel(json_path), "markdown": rel(md_path), "csv": rel(csv_path)},
        )
        return

    issues = []
    if manifest.get("claim_status") != "public_reproducibility_manifest_ready_not_submission_complete":
        issues.append({"error": "unexpected_claim_status", "actual": manifest.get("claim_status")})
    outputs = manifest.get("outputs") or {}
    expected_outputs = {"markdown": rel(md_path), "json": rel(json_path), "csv": rel(csv_path)}
    for field, expected in expected_outputs.items():
        if outputs.get(field) != expected:
            issues.append({"error": "output_path_mismatch", "field": field, "expected": expected, "actual": outputs.get(field)})
    if not md_path.exists():
        issues.append({"error": "missing_markdown", "path": rel(md_path)})

    artifact_rows = manifest.get("artifact_rows") or []
    summary = manifest.get("summary") or {}
    if len(csv_rows) != len(artifact_rows):
        issues.append({"error": "csv_row_count_mismatch", "expected": len(artifact_rows), "actual": len(csv_rows)})
    if summary.get("artifact_rows") != len(artifact_rows):
        issues.append({"error": "summary_artifact_row_count_mismatch", "expected": len(artifact_rows), "actual": summary.get("artifact_rows")})
    if summary.get("missing_rows") != 0:
        missing = [row for row in artifact_rows if row.get("exists") != "yes"]
        issues.append({"error": "missing_manifest_artifacts", "missing_rows": summary.get("missing_rows"), "examples": missing[:10]})
    if summary.get("covered_requirements") != summary.get("total_requirements") or summary.get("total_requirements") != 7:
        issues.append({"error": "requirement_coverage_incomplete", "summary": summary})
    if manifest.get("text_risk_hits"):
        issues.append({"error": "manifest_text_risk_hits", "hits": manifest.get("text_risk_hits")})

    required_categories = {
        "schema_and_cq",
        "prompts",
        "runtime_code",
        "evaluation_protocol",
        "traceability",
        "synthetic_public_examples",
        "public_benchmarks",
        "release_safety",
        "internal_only",
    }
    categories = {row.get("category") for row in artifact_rows}
    missing_categories = sorted(required_categories - categories)
    if missing_categories:
        issues.append({"error": "missing_categories", "missing": missing_categories})

    required_paths = {
        "scripts/build_cape_predicate_cue_spans.py",
        rel(exp_dir / "04_evaluation/predicate_cue_span_report.md"),
        rel(exp_dir / "04_evaluation/predicate_cue_span_metrics.json"),
        rel(exp_dir / "04_evaluation/predicate_cue_span_rows.csv"),
        "outputs/06_triples/layer2_predicate_cue_spans.jsonl",
    }
    manifest_paths = {row.get("path") for row in artifact_rows}
    missing_required_paths = sorted(required_paths - manifest_paths)
    if missing_required_paths:
        issues.append({"error": "missing_predicate_cue_manifest_paths", "missing": missing_required_paths})

    coverage = manifest.get("requirement_coverage") or []
    not_covered = [row for row in coverage if row.get("status") != "covered"]
    if not_covered:
        issues.append({"error": "requirements_not_covered", "rows": not_covered})
    coverage_names = {row.get("requirement") for row in coverage}
    expected_requirements = {
        "schema",
        "prompts",
        "code",
        "evaluation protocol",
        "derived public examples",
        "public benchmark cross-check",
        "release safety",
    }
    if coverage_names != expected_requirements:
        issues.append({"error": "requirement_set_mismatch", "expected": sorted(expected_requirements), "actual": sorted(coverage_names)})

    current = latest.get("current") or {}
    public_bundle = current.get("public_safe_bundle") or {}
    public_bundle_path = Path(public_bundle.get("path") or "")
    bundle_names = set()
    if not public_bundle_path.exists():
        issues.append({"error": "public_safe_bundle_missing", "path": rel(public_bundle_path)})
    else:
        try:
            with tarfile.open(public_bundle_path, "r:gz") as tar:
                bundle_names = set(tar.getnames())
        except Exception as exc:
            issues.append({"error": "cannot_open_public_safe_bundle", "path": rel(public_bundle_path), "detail": str(exc)})
    if bundle_names:
        for path in [md_path, json_path, csv_path]:
            if rel(path) not in bundle_names:
                issues.append({"error": "manifest_output_not_in_public_safe_bundle", "path": rel(path)})
        public_safe_paths = [
            row.get("path")
            for row in artifact_rows
            if row.get("release_status") == "public_safe"
        ]
        missing_from_bundle = sorted(path for path in public_safe_paths if path not in bundle_names)
        if missing_from_bundle:
            issues.append({"error": "public_safe_rows_missing_from_bundle", "missing": missing_from_bundle[:30]})

    if md_path.exists():
        text = md_path.read_text(encoding="utf-8", errors="replace")
        for pattern in [
            "CAPE-KG Public Reproducibility Manifest",
            "Requirement Coverage",
            "schema",
            "prompts",
            "public benchmark",
            "Final submission-level claims still require human-gold and expert-review returns.",
        ]:
            if pattern not in text:
                issues.append({"error": "missing_markdown_pattern", "pattern": pattern})
        risky_patterns = [
            "05_review/human_gold_batches/",
            "gold_annotation_template.jsonl",
            "evaluation_chunks.jsonl",
            "annotation_workbench.html",
            "annotator_",
            "adjudication.jsonl",
            "adjudication_draft.jsonl",
        ]
        hits = [pattern for pattern in risky_patterns if pattern in text]
        if hits:
            issues.append({"error": "markdown_mentions_private_review_patterns", "hits": hits})

    if issues:
        add_check(
            checks,
            "public_reproducibility_manifest",
            "FAIL",
            "Public reproducibility manifest is missing, unsafe, or not synchronized with the public-safe bundle.",
            {"path": rel(json_path), "issues": issues[:50]},
        )
        return

    add_check(
        checks,
        "public_reproducibility_manifest",
        "PASS",
        "Public reproducibility manifest maps plan requirements to public-safe artifacts and is included in the public-safe bundle.",
        {
            "json": rel(json_path),
            "markdown": rel(md_path),
            "csv": rel(csv_path),
            "artifact_rows": len(artifact_rows),
            "public_safe_rows": summary.get("public_safe_rows"),
            "internal_only_rows": summary.get("internal_only_rows"),
            "requirements": summary.get("covered_requirements"),
            "public_safe_bundle": rel(public_bundle_path),
        },
    )


def validate_public_synthetic_examples_claim_safety(checks, exp_dir):
    out_dir = exp_dir / "06_release/public_synthetic_examples"
    summary_path = out_dir / "synthetic_evaluation_summary.json"
    readme_path = out_dir / "README.md"
    chunks_path = out_dir / "synthetic_chunks.jsonl"
    gold_path = out_dir / "synthetic_gold.jsonl"
    predictions_path = out_dir / "synthetic_predictions.jsonl"
    try:
        summary = read_json(summary_path)
        chunks = read_jsonl(chunks_path)
        gold_rows = read_jsonl(gold_path)
        prediction_rows = read_jsonl(predictions_path)
    except Exception as exc:
        add_check(
            checks,
            "public_synthetic_examples_claim_safety",
            "FAIL",
            "Public synthetic examples cannot be read.",
            {"error": str(exc), "path": rel(summary_path)},
        )
        return

    issues = []
    expected_files = {
        "readme": readme_path,
        "chunks": chunks_path,
        "gold": gold_path,
        "predictions": predictions_path,
        "summary": summary_path,
    }
    for key, path in expected_files.items():
        if not path.exists():
            issues.append({"error": "missing_synthetic_file", "key": key, "path": rel(path)})
    for key, path_value in (summary.get("files") or {}).items():
        expected_path = expected_files.get(key)
        if expected_path and Path(path_value) != expected_path:
            issues.append(
                {
                    "error": "summary_file_path_mismatch",
                    "key": key,
                    "expected": rel(expected_path),
                    "actual": path_value,
                }
            )

    expected_claim_status = "public_format_example_not_paper_result"
    if summary.get("claim_status") != expected_claim_status:
        issues.append({"error": "unexpected_claim_status", "actual": summary.get("claim_status")})
    if summary.get("source_text_policy") != "synthetic_only_no_source_corpus_text":
        issues.append({"error": "unexpected_source_text_policy", "actual": summary.get("source_text_policy")})
    expected_counts = {
        "synthetic_chunk_count": 2,
        "synthetic_node_count": 8,
        "synthetic_edge_count": 6,
        "synthetic_evidence_anchor_count": 2,
        "validation_error_count": 0,
        "validation_issue_count": 0,
    }
    for key, expected in expected_counts.items():
        if summary.get(key) != expected:
            issues.append({"error": "unexpected_summary_count", "key": key, "expected": expected, "actual": summary.get(key)})
    if len(chunks) != summary.get("synthetic_chunk_count"):
        issues.append({"error": "chunk_count_mismatch", "summary": summary.get("synthetic_chunk_count"), "actual": len(chunks)})
    if len(gold_rows) != summary.get("synthetic_chunk_count"):
        issues.append({"error": "gold_row_count_mismatch", "summary_chunks": summary.get("synthetic_chunk_count"), "actual": len(gold_rows)})
    if len(prediction_rows) != summary.get("synthetic_chunk_count"):
        issues.append(
            {
                "error": "prediction_row_count_mismatch",
                "summary_chunks": summary.get("synthetic_chunk_count"),
                "actual": len(prediction_rows),
            }
        )

    forbidden_patterns = PUBLIC_SAFE_FORBIDDEN_PATTERNS + (
        "AX_",
        "aigpu",
        "minjoo",
        "166.104.",
        "서울펠로우",
        "수주",
        "제안",
    )
    text_paths = [readme_path, chunks_path, gold_path, predictions_path, summary_path]
    text_hits = []
    for path in text_paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in forbidden_patterns:
            if pattern in text:
                text_hits.append({"path": rel(path), "pattern": pattern})
    if text_hits:
        issues.append({"error": "synthetic_files_contain_private_or_internal_pattern", "hits": text_hits[:50]})

    chunk_by_id = {row.get("chunk_id"): row for row in chunks}
    all_nodes = {}
    all_edges = {}
    all_evidence = {}
    for chunk in chunks:
        if chunk.get("source_kind") != "synthetic_public_example":
            issues.append({"error": "chunk_not_marked_synthetic", "chunk_id": chunk.get("chunk_id"), "source_kind": chunk.get("source_kind")})
        if not str(chunk.get("chunk_id") or "").startswith("SYN-"):
            issues.append({"error": "chunk_id_not_synthetic", "chunk_id": chunk.get("chunk_id")})
        if not chunk.get("chunk_text"):
            issues.append({"error": "synthetic_chunk_missing_text", "chunk_id": chunk.get("chunk_id")})

    for row in gold_rows:
        if row.get("annotation_status") != "completed":
            issues.append({"error": "synthetic_gold_not_completed", "chunk_id": row.get("chunk_id"), "status": row.get("annotation_status")})
        if row.get("reviewer_id") != "synthetic_reference":
            issues.append({"error": "synthetic_gold_unexpected_reviewer", "chunk_id": row.get("chunk_id"), "reviewer_id": row.get("reviewer_id")})
        if row.get("package") != "public_synthetic_examples":
            issues.append({"error": "synthetic_gold_unexpected_package", "chunk_id": row.get("chunk_id"), "package": row.get("package")})
        chunk = chunk_by_id.get(row.get("chunk_id"))
        if not chunk:
            issues.append({"error": "synthetic_gold_unknown_chunk", "chunk_id": row.get("chunk_id")})
            continue
        if row.get("chunk_text") != chunk.get("chunk_text"):
            issues.append({"error": "synthetic_gold_chunk_text_mismatch", "chunk_id": row.get("chunk_id")})
        for node in row.get("gold_nodes") or []:
            node_id = node.get("node_id")
            if not str(node_id or "").startswith("SYN-"):
                issues.append({"error": "synthetic_node_id_not_synthetic", "node_id": node_id})
            all_nodes[node_id] = node
        for evidence in row.get("evidence_anchors") or []:
            evidence_id = evidence.get("evidence_id")
            if not str(evidence_id or "").startswith("SYN-"):
                issues.append({"error": "synthetic_evidence_id_not_synthetic", "evidence_id": evidence_id})
            if evidence.get("chunk_id") != row.get("chunk_id"):
                issues.append({"error": "synthetic_evidence_chunk_mismatch", "evidence_id": evidence_id})
            text = chunk.get("chunk_text") or ""
            start = evidence.get("start_char")
            end = evidence.get("end_char")
            if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end > len(text) or start >= end:
                issues.append({"error": "synthetic_evidence_invalid_span", "evidence_id": evidence_id, "start": start, "end": end, "text_len": len(text)})
            elif evidence.get("text") != text[start:end]:
                issues.append({"error": "synthetic_evidence_text_span_mismatch", "evidence_id": evidence_id})
            all_evidence[evidence_id] = evidence
        for edge in row.get("gold_edges") or []:
            edge_id = edge.get("edge_id")
            if not str(edge_id or "").startswith("SYN-"):
                issues.append({"error": "synthetic_edge_id_not_synthetic", "edge_id": edge_id})
            if not edge.get("evidence_anchor_ids"):
                issues.append({"error": "synthetic_edge_missing_evidence_anchor", "edge_id": edge_id})
            all_edges[edge_id] = edge

    if len(all_nodes) != summary.get("synthetic_node_count"):
        issues.append({"error": "synthetic_node_count_mismatch", "summary": summary.get("synthetic_node_count"), "actual": len(all_nodes)})
    if len(all_edges) != summary.get("synthetic_edge_count"):
        issues.append({"error": "synthetic_edge_count_mismatch", "summary": summary.get("synthetic_edge_count"), "actual": len(all_edges)})
    if len(all_evidence) != summary.get("synthetic_evidence_anchor_count"):
        issues.append(
            {
                "error": "synthetic_evidence_count_mismatch",
                "summary": summary.get("synthetic_evidence_anchor_count"),
                "actual": len(all_evidence),
            }
        )
    for edge in all_edges.values():
        if edge.get("source_id") not in all_nodes or edge.get("target_id") not in all_nodes:
            issues.append({"error": "synthetic_edge_unknown_endpoint", "edge_id": edge.get("edge_id")})
        for evidence_id in edge.get("evidence_anchor_ids") or []:
            if evidence_id not in all_evidence:
                issues.append({"error": "synthetic_edge_unknown_evidence", "edge_id": edge.get("edge_id"), "evidence_id": evidence_id})

    expected_predicates = {"HAS_STEP", "PRODUCES", "PERFORMED_BY", "PRECEDES", "HAS_RISK"}
    actual_predicates = {edge.get("predicate") for edge in all_edges.values()}
    if not expected_predicates.issubset(actual_predicates):
        issues.append({"error": "synthetic_predicate_coverage_missing", "expected_subset": sorted(expected_predicates), "actual": sorted(actual_predicates)})

    for row in prediction_rows:
        if row.get("condition") != "P_cape_kg_synthetic_example":
            issues.append({"error": "synthetic_prediction_unexpected_condition", "chunk_id": row.get("chunk_id"), "condition": row.get("condition")})
        if row.get("claim_status") != "synthetic_example_not_paper_result":
            issues.append({"error": "synthetic_prediction_unexpected_claim_status", "chunk_id": row.get("chunk_id"), "claim_status": row.get("claim_status")})
        if row.get("chunk_id") not in chunk_by_id:
            issues.append({"error": "synthetic_prediction_unknown_chunk", "chunk_id": row.get("chunk_id")})

    if not readme_path.exists():
        issues.append({"error": "synthetic_readme_missing", "path": rel(readme_path)})
    else:
        text = readme_path.read_text(encoding="utf-8")
        for pattern in [
            "not copied, paraphrased, or derived from the private/source corpus",
            "format and release-safety artifact only",
            "not a paper result",
            f"Claim status: `{expected_claim_status}`",
        ]:
            if pattern not in text:
                issues.append({"error": "synthetic_readme_missing_pattern", "pattern": pattern})

    if issues:
        add_check(
            checks,
            "public_synthetic_examples_claim_safety",
            "FAIL",
            "Public synthetic examples are missing, unsafe, structurally inconsistent, or claim-unsafe.",
            {"path": rel(summary_path), "issues": issues[:80]},
        )
        return

    add_check(
        checks,
        "public_synthetic_examples_claim_safety",
        "PASS",
        "Public synthetic examples are schema-shaped, source-text safe, and explicitly not paper-result evidence.",
        {
            "path": rel(summary_path),
            "synthetic_chunks": len(chunks),
            "synthetic_nodes": len(all_nodes),
            "synthetic_edges": len(all_edges),
            "claim_status": summary.get("claim_status"),
        },
    )


def validate_release_manifest(checks, exp_dir):
    manifest_path = exp_dir / "06_release/release_bundle_manifest.json"
    try:
        manifest = read_json(manifest_path)
    except Exception as exc:
        add_check(checks, "release_manifest_readable", "FAIL", "Release bundle manifest cannot be read.", {"error": str(exc)})
        return

    risky = manifest.get("public_safe_risky_paths") or []
    if risky:
        add_check(checks, "public_safe_manifest_risk_scan", "FAIL", "Public-safe manifest contains risky paths.", {"public_safe_risky_paths": risky[:50]})
    else:
        add_check(checks, "public_safe_manifest_risk_scan", "PASS", "Public-safe manifest risk scan is empty.", {})

    risky_text = manifest.get("public_safe_risky_text_references") or []
    review_queue_csv = Path(manifest.get("public_external_release_review_queue_csv", ""))
    review_queue_md = Path(manifest.get("public_external_release_review_queue_md", ""))
    review_queue_issues = []
    if not review_queue_csv.exists():
        review_queue_issues.append({"error": "missing_review_queue_csv", "path": rel(review_queue_csv)})
    if not review_queue_md.exists():
        review_queue_issues.append({"error": "missing_review_queue_md", "path": rel(review_queue_md)})
    if review_queue_csv.exists():
        try:
            queue_rows = max(0, sum(1 for _ in review_queue_csv.open("r", encoding="utf-8-sig", newline="")) - 1)
        except Exception as exc:
            queue_rows = 0
            review_queue_issues.append({"error": "cannot_read_review_queue_csv", "path": rel(review_queue_csv), "detail": str(exc)})
        if queue_rows != len(risky_text):
            review_queue_issues.append(
                {
                    "error": "review_queue_row_count_mismatch",
                    "queue_rows": queue_rows,
                    "manifest_text_reference_rows": len(risky_text),
                }
            )
    if review_queue_md.exists():
        text = review_queue_md.read_text(encoding="utf-8", errors="replace")
        for pattern in ["## Summary", "## Risky Text References", "inspect_or_redact_before_external_release"]:
            if pattern not in text:
                review_queue_issues.append({"error": "review_queue_md_missing_pattern", "pattern": pattern})

    if risky_text:
        add_check(
            checks,
            "public_safe_text_reference_scan",
            "WARN",
            "Public-safe text files mention conservative internal path/name patterns; inspect before external release.",
            {
                "public_safe_risky_text_references": risky_text[:50],
                "review_queue_csv": rel(review_queue_csv),
                "review_queue_md": rel(review_queue_md),
                "review_queue_issues": review_queue_issues[:20],
            },
        )
    else:
        add_check(
            checks,
            "public_safe_text_reference_scan",
            "PASS",
            "Public-safe text files do not mention conservative internal path/name patterns.",
            {"review_queue_csv": rel(review_queue_csv), "review_queue_md": rel(review_queue_md), "review_queue_issues": review_queue_issues[:20]},
        )

    if review_queue_issues:
        add_check(
            checks,
            "public_external_release_review_queue",
            "FAIL",
            "Public external release review queue is missing or inconsistent.",
            {"issues": review_queue_issues[:50]},
        )
    else:
        add_check(
            checks,
            "public_external_release_review_queue",
            "PASS",
            "Public external release review queue is synchronized with the public-safe text reference scan.",
            {"csv": rel(review_queue_csv), "markdown": rel(review_queue_md), "risk_rows": len(risky_text)},
        )

    bundle_issues = []
    for key in ("internal_bundle", "public_safe_bundle"):
        bundle = manifest.get(key) or {}
        path = Path(bundle.get("path", ""))
        if not path.exists():
            bundle_issues.append({"bundle": key, "error": "missing_file", "path": rel(path)})
            continue
        actual = sha256_file(path)
        if actual != bundle.get("sha256"):
            bundle_issues.append({"bundle": key, "error": "sha256_mismatch", "expected": bundle.get("sha256"), "actual": actual})
    packet_bundle_policy = {
        "scripts/build_cape_human_review_packet_integrity_report.py",
        "experiments/cape_kg_eacl_20260627/05_review/human_review_packet_integrity_issues.csv",
        "experiments/cape_kg_eacl_20260627/06_release/human_review_packet_integrity.json",
        "experiments/cape_kg_eacl_20260627/06_release/human_review_packet_integrity.md",
    }
    for key in ("internal_bundle", "public_safe_bundle"):
        bundle = manifest.get(key) or {}
        path = Path(bundle.get("path", ""))
        if not path.exists():
            continue
        try:
            with tarfile.open(path, "r:gz") as tar:
                bundle_names = set(tar.getnames())
        except Exception as exc:
            bundle_issues.append({"bundle": key, "error": "cannot_open_bundle_for_packet_policy", "path": rel(path), "detail": str(exc)})
            continue
        if key == "internal_bundle":
            missing_packet_files = sorted(packet_bundle_policy - bundle_names)
            if missing_packet_files:
                bundle_issues.append(
                    {
                        "bundle": key,
                        "error": "missing_human_review_packet_integrity_files",
                        "missing": missing_packet_files,
                    }
                )
        else:
            leaked_packet_files = sorted(packet_bundle_policy & bundle_names)
            if leaked_packet_files:
                bundle_issues.append(
                    {
                        "bundle": key,
                        "error": "public_safe_contains_human_review_packet_integrity_files",
                        "paths": leaked_packet_files,
                    }
                )
    latest_index_path = exp_dir / "06_release/latest_release_bundle_index.json"
    latest_index_md_path = exp_dir / "06_release/latest_release_bundle_index.md"
    try:
        latest_index = read_json(latest_index_path)
    except Exception as exc:
        bundle_issues.append({"bundle": "latest_release_bundle_index", "error": "cannot_read_latest_index", "path": rel(latest_index_path), "detail": str(exc)})
        latest_index = {}
    if latest_index:
        current = latest_index.get("current") or {}
        if latest_index.get("claim_status") != "latest_release_bundle_index_ready_not_submission_complete":
            bundle_issues.append({"bundle": "latest_release_bundle_index", "error": "unexpected_claim_status", "actual": latest_index.get("claim_status")})
        if current.get("internal_bundle", {}).get("path") != (manifest.get("internal_bundle") or {}).get("path"):
            bundle_issues.append({"bundle": "latest_release_bundle_index", "error": "internal_bundle_path_mismatch"})
        if current.get("public_safe_bundle", {}).get("path") != (manifest.get("public_safe_bundle") or {}).get("path"):
            bundle_issues.append({"bundle": "latest_release_bundle_index", "error": "public_safe_bundle_path_mismatch"})
        if current.get("internal_bundle", {}).get("sha256") != (manifest.get("internal_bundle") or {}).get("sha256"):
            bundle_issues.append({"bundle": "latest_release_bundle_index", "error": "internal_bundle_sha256_mismatch"})
        if current.get("public_safe_bundle", {}).get("sha256") != (manifest.get("public_safe_bundle") or {}).get("sha256"):
            bundle_issues.append({"bundle": "latest_release_bundle_index", "error": "public_safe_bundle_sha256_mismatch"})
        commands = latest_index.get("verification_commands") or {}
        for key in ("release_checksums", "pre_human_validation", "handoff_checksums"):
            if not commands.get(key):
                bundle_issues.append({"bundle": "latest_release_bundle_index", "error": "missing_verification_command", "command": key})
    if not latest_index_md_path.exists():
        bundle_issues.append({"bundle": "latest_release_bundle_index", "error": "missing_markdown", "path": rel(latest_index_md_path)})
    else:
        latest_text = latest_index_md_path.read_text(encoding="utf-8", errors="replace")
        for pattern in ["CAPE-KG Latest Release Bundle Index", "Current Bundles", "Verification Commands", "not_submission_complete"]:
            if pattern not in latest_text:
                bundle_issues.append({"bundle": "latest_release_bundle_index", "error": "missing_markdown_pattern", "pattern": pattern})
    if bundle_issues:
        add_check(checks, "release_bundle_manifest_hashes", "FAIL", "Release bundle files do not match manifest hashes.", {"issues": bundle_issues})
    else:
        add_check(checks, "release_bundle_manifest_hashes", "PASS", "Release bundle files match manifest hashes.", {})

    allowed_nested_release_files = {
        manifest.get("internal_checksums"),
        manifest.get("public_safe_checksums"),
        manifest.get("metadata_file"),
    }
    live_post_bundle_files = {
        "06_release/latest_release_bundle_index.json",
        "06_release/latest_release_bundle_index.md",
        "06_release/pre_human_handoff_validation.json",
        "06_release/pre_human_handoff_validation.md",
        "06_release/human_review_status_dashboard_ko.json",
        "06_release/human_review_status_dashboard_ko.md",
        "06_release/anonymized_submission_prep.json",
        "06_release/anonymized_submission_prep.md",
        "06_release/anonymized_submission_risk_scan.csv",
        "06_release/eacl_submission_package_manifest.json",
        "06_release/eacl_submission_package_manifest.md",
        "06_release/post_annotation_refresh_last_run.json",
        "06_release/post_annotation_refresh_last_run.md",
    }
    stale_release_entries = []
    for key in ("internal_bundle", "public_safe_bundle"):
        bundle = manifest.get(key) or {}
        path = Path(bundle.get("path", ""))
        if not path.exists():
            continue
        try:
            with tarfile.open(path, "r:gz") as tar:
                names = tar.getnames()
        except Exception:
            continue
        for name in names:
            if name.endswith("06_release/release_bundle_safety_report.md"):
                stale_release_entries.append({"bundle": key, "path": name, "error": "stale_safety_report_in_bundle"})
            if any(name.endswith(live_name) for live_name in live_post_bundle_files):
                stale_release_entries.append({"bundle": key, "path": name, "error": "live_post_bundle_status_file_in_bundle"})
            if "/06_release/bundles/" in name and name not in allowed_nested_release_files:
                stale_release_entries.append({"bundle": key, "path": name, "error": "stale_nested_release_artifact"})
    if stale_release_entries:
        add_check(
            checks,
            "release_bundle_no_stale_nested_artifacts",
            "FAIL",
            "Release bundles contain stale nested bundle metadata/checksum artifacts.",
            {"issues": stale_release_entries[:100]},
        )
    else:
        add_check(
            checks,
            "release_bundle_no_stale_nested_artifacts",
            "PASS",
            "Release bundles exclude stale nested bundle metadata/checksum artifacts.",
            {},
        )

    public_bundle = manifest.get("public_safe_bundle") or {}
    public_path = Path(public_bundle.get("path", ""))
    if not public_path.exists():
        add_check(checks, "public_safe_tar_content_scan", "FAIL", "Public-safe bundle is missing.", {"path": rel(public_path)})
        return
    try:
        with tarfile.open(public_path, "r:gz") as tar:
            names = tar.getnames()
    except Exception as exc:
        add_check(checks, "public_safe_tar_content_scan", "FAIL", "Public-safe bundle cannot be opened.", {"error": str(exc)})
        return
    forbidden = sorted(name for name in names if any(pattern in name for pattern in PUBLIC_SAFE_FORBIDDEN_PATTERNS))
    if forbidden:
        add_check(checks, "public_safe_tar_content_scan", "FAIL", "Public-safe bundle contains forbidden internal-review paths.", {"paths": forbidden[:100]})
    else:
        add_check(checks, "public_safe_tar_content_scan", "PASS", "Public-safe bundle excludes internal-review and source-text paths.", {"file_count": len(names)})


def validate_report_validation_summary_freshness(checks, exp_dir):
    report_dir = exp_dir / "07_reports"
    release_dir = exp_dir / "06_release"
    prehuman_path = release_dir / "pre_human_handoff_validation.json"
    latest_index_path = release_dir / "latest_release_bundle_index.json"
    candidate_paths = []
    if report_dir.exists():
        candidate_paths.extend(sorted(report_dir.glob("*.md")))
    if release_dir.exists():
        candidate_paths.extend(
            path
            for path in sorted(release_dir.glob("*.md"))
            if path.name != "pre_human_handoff_validation.md"
        )

    issues = []
    try:
        prehuman = read_json(prehuman_path)
    except Exception as exc:
        prehuman = {}
        issues.append({"path": rel(prehuman_path), "error": "cannot_read_pre_human_validation", "detail": str(exc)})

    try:
        latest_index = read_json(latest_index_path)
        latest_stamp = latest_index.get("stamp")
    except Exception as exc:
        latest_index = {}
        latest_stamp = None
        issues.append({"path": rel(latest_index_path), "error": "cannot_read_latest_release_index", "detail": str(exc)})

    audit_json = release_dir / "submission_completion_audit_ko.json"
    master_json = release_dir / "human_review_master_checklist_ko.json"
    action_plan_json = release_dir / "human_gate_action_plan.json"
    master_returns_csv = exp_dir / "05_review/human_review_master_return_files.csv"
    if prehuman:
        effective_prehuman = effective_prehuman_summary(prehuman)
        expected_status = effective_prehuman.get("overall_status")
        expected_checks = effective_prehuman.get("check_count")
        expected_counts = effective_prehuman.get("status_counts")
        try:
            audit = read_json(audit_json)
            audit_summary = audit.get("summary") or {}
            action_plan = read_json(action_plan_json)
            required_rows = action_plan.get("required_return_files") or []
            minimum_rows = [row for row in required_rows if truthy_present(row.get("required_for_minimum"))]
            optional_rows = [row for row in required_rows if not truthy_present(row.get("required_for_minimum"))]
            master_rows = read_csv_rows(master_returns_csv) if master_returns_csv.exists() else []
            master_optional_rows = [row for row in master_rows if not truthy_present(row.get("required_for_minimum"))]
            master_optional_claim_rows = [row for row in master_optional_rows if row.get("requiredness") != "optional_structural"]
            master_optional_structural_rows = [row for row in master_optional_rows if row.get("requiredness") == "optional_structural"]
            master_required_claim_rows = [row for row in master_rows if row.get("requiredness", "required") == "required"]
            expected_return_counts = {
                "minimum_paper_gate_return_files": len(minimum_rows),
                "minimum_paper_gate_return_files_present": sum(1 for row in minimum_rows if truthy_present(row.get("present"))),
                "optional_strong_return_files": len(optional_rows),
                "optional_strong_return_files_present": sum(1 for row in optional_rows if truthy_present(row.get("present"))),
                "tracked_human_return_files": len(required_rows),
                "tracked_human_return_files_present": sum(1 for row in required_rows if truthy_present(row.get("present"))),
                "required_human_return_files": len(required_rows),
                "present_human_return_files": sum(1 for row in required_rows if truthy_present(row.get("present"))),
            }
            if master_rows:
                expected_return_counts.update(
                    {
                        "master_optional_claim_return_files": len(master_optional_claim_rows),
                        "master_optional_claim_return_files_present": sum(
                            1 for row in master_optional_claim_rows if truthy_present(row.get("present"))
                        ),
                        "optional_structural_return_files": len(master_optional_structural_rows),
                        "optional_structural_return_files_present": sum(
                            1 for row in master_optional_structural_rows if truthy_present(row.get("present"))
                        ),
                        "master_required_claim_return_files": len(master_required_claim_rows),
                        "master_required_claim_return_files_present": sum(
                            1 for row in master_required_claim_rows if truthy_present(row.get("present"))
                        ),
                        "master_return_files": len(master_rows),
                        "master_return_files_present": sum(1 for row in master_rows if truthy_present(row.get("present"))),
                    }
                )
            expected_return_counts.update(
                {
                    "minimum_paper_gate_return_files_missing": expected_return_counts["minimum_paper_gate_return_files"]
                    - expected_return_counts["minimum_paper_gate_return_files_present"],
                    "optional_strong_return_files_missing": expected_return_counts["optional_strong_return_files"]
                    - expected_return_counts["optional_strong_return_files_present"],
                    "tracked_human_return_files_missing": expected_return_counts["tracked_human_return_files"]
                    - expected_return_counts["tracked_human_return_files_present"],
                }
            )
            if master_rows:
                expected_return_counts.update(
                    {
                        "optional_structural_return_files_missing": expected_return_counts["optional_structural_return_files"]
                        - expected_return_counts["optional_structural_return_files_present"],
                        "master_return_files_missing": expected_return_counts["master_return_files"]
                        - expected_return_counts["master_return_files_present"],
                    }
                )
            for field, expected in expected_return_counts.items():
                if audit_summary.get(field) != expected:
                    issues.append(
                        {
                            "path": rel(audit_json),
                            "error": "completion_audit_return_count_mismatch",
                            "field": field,
                            "expected": expected,
                            "actual": audit_summary.get(field),
                        }
                    )
            if audit_summary.get("pre_human_validation_status") != expected_status:
                issues.append(
                    {
                        "path": rel(audit_json),
                        "error": "pre_human_validation_status_stale",
                        "expected": expected_status,
                        "actual": audit_summary.get("pre_human_validation_status"),
                    }
                )
            if audit_summary.get("pre_human_validation_checks") != expected_checks:
                issues.append(
                    {
                        "path": rel(audit_json),
                        "error": "pre_human_validation_check_count_stale",
                        "expected": expected_checks,
                        "actual": audit_summary.get("pre_human_validation_checks"),
                    }
                )
            if audit_summary.get("pre_human_validation_status_counts") != expected_counts:
                issues.append(
                    {
                        "path": rel(audit_json),
                        "error": "pre_human_validation_status_counts_stale",
                        "expected": expected_counts,
                        "actual": audit_summary.get("pre_human_validation_status_counts"),
                    }
                )
        except Exception as exc:
            issues.append({"path": rel(audit_json), "error": "cannot_read_completion_audit", "detail": str(exc)})

        try:
            master = read_json(master_json)
            master_summary = master.get("summary") or {}
            if master_summary.get("pre_human_handoff_validation") != expected_status:
                issues.append(
                    {
                        "path": rel(master_json),
                        "error": "master_pre_human_validation_status_stale",
                        "expected": expected_status,
                        "actual": master_summary.get("pre_human_handoff_validation"),
                    }
                )
        except Exception as exc:
            issues.append({"path": rel(master_json), "error": "cannot_read_human_review_master_checklist", "detail": str(exc)})

    current_report_name_tokens = ("current", "digest", "essential", "essentials")

    checked_files = 0
    for path in candidate_paths:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            issues.append({"path": rel(path), "error": "cannot_read_report", "detail": str(exc)})
            continue
        checked_files += 1
        hits = [pattern for pattern in STALE_REPORT_VALIDATION_PATTERNS if pattern in text]
        if hits:
            issues.append({"path": rel(path), "stale_patterns": hits})
        if prehuman:
            effective_prehuman = effective_prehuman_summary(prehuman)
            expected_checks = int(effective_prehuman.get("check_count") or 0)
            expected_passes = int((effective_prehuman.get("status_counts") or {}).get("PASS") or 0)
            stale_table_counts = sorted(
                {
                    int(match.group("count"))
                    for match in re.finditer(r"\|\s*Pre-human checks\s*\|\s*(?P<count>\d+)\s*\|", text)
                    if int(match.group("count")) != expected_checks
                }
            )
            if stale_table_counts:
                issues.append(
                    {
                        "path": rel(path),
                        "error": "stale_pre_human_checks_table_row",
                        "expected": expected_checks,
                        "actual_counts": stale_table_counts,
                    }
                )
            stale_sentence_counts = sorted(
                {
                    (int(match.group("checks")), int(match.group("passes")))
                    for match in re.finditer(
                        r"(?P<checks>\d+)\s+checks\s+중\s+(?P<passes>\d+)\s+PASS\s*/\s*1\s+WARN",
                        text,
                    )
                    if int(match.group("checks")) != expected_checks or int(match.group("passes")) != expected_passes
                }
            )
            if stale_sentence_counts:
                issues.append(
                    {
                        "path": rel(path),
                        "error": "stale_pre_human_checks_sentence",
                        "expected": {"checks": expected_checks, "pass": expected_passes, "warn": 1},
                        "actual_counts": [{"checks": checks, "pass": passes} for checks, passes in stale_sentence_counts],
                    }
                )
        if path.parent == report_dir and any(token in path.name for token in current_report_name_tokens):
            stale_current_report_phrases = [
                "All tracked human-return files",
                "All tracked human return files",
                "Optional/strong tracked return files",
                "24 checks",
                "23 PASS",
                "73 checks",
                "72 PASS",
                "20260629T091930Z",
                "human_docs_master_returns_sync_20260629",
                "081ab390b5a44035ba0ccee2f7438eecc4dfd284f1244dc3aea5d2d9550f0987",
                "3941348caf069e37b74c49275d28d0efeb6d5e849ee7304e166b8cb7d4eed970",
                "dc71bd6812af61241c905b8ddbefab8f5daf1324bb7814a9263709758781f7cf",
                "5e0aba822c9e6e5f03029313596cd4d142f36dae980afd0c2f5798c239d89bfd",
            ]
            stale_current_hits = [phrase for phrase in stale_current_report_phrases if phrase in text]
            if stale_current_hits:
                issues.append(
                    {
                        "path": rel(path),
                        "error": "stale_current_professor_report_summary",
                        "phrases": stale_current_hits,
                    }
                )
        volatile_release_log_files = {
            "latest_release_bundle_index.md",
            "post_annotation_refresh_last_run.md",
        }
        if latest_stamp and path.name not in volatile_release_log_files:
            bundle_stamp_hits = sorted(
                {
                    match.group("stamp")
                    for match in re.finditer(
                        r"cape_kg_eacl_(?:internal_repro|public_safe_skeleton)_(?P<stamp>\d{8}T\d{6}Z)\.tar\.gz",
                        text,
                    )
                    if match.group("stamp") != latest_stamp
                }
            )
            if bundle_stamp_hits:
                issues.append(
                    {
                        "path": rel(path),
                        "error": "stale_release_bundle_reference",
                        "latest_stamp": latest_stamp,
                        "stale_stamps": bundle_stamp_hits,
                    }
                )
        if path == release_dir / "human_review_start_here_ko.md":
            if re.search(r"최신 release stamp는 `\d{8}T\d{6}Z`", text):
                issues.append(
                    {
                        "path": rel(path),
                        "error": "static_latest_release_stamp_in_start_here",
                        "expected": "Reference latest_release_bundle_index.md instead of embedding a stamp.",
                    }
                )
        if prehuman and path == release_dir / "submission_completion_audit_ko.md":
            effective_prehuman = effective_prehuman_summary(prehuman)
            expected_line = f"| Pre-human validation | `{effective_prehuman.get('overall_status')}` |"
            expected_check_line = f"| Pre-human checks | {effective_prehuman.get('check_count')} |"
            if expected_line not in text:
                issues.append(
                    {
                        "path": rel(path),
                        "error": "completion_audit_markdown_pre_human_status_stale",
                        "expected_line": expected_line,
                    }
                )
            if expected_check_line not in text:
                issues.append(
                    {
                        "path": rel(path),
                        "error": "completion_audit_markdown_pre_human_checks_stale",
                        "expected_line": expected_check_line,
                    }
                )
        if prehuman and path == release_dir / "human_review_master_checklist_ko.md":
            effective_prehuman = effective_prehuman_summary(prehuman)
            expected_line = f"| Pre-human handoff validation | `{effective_prehuman.get('overall_status')}` |"
            if expected_line not in text:
                issues.append(
                    {
                        "path": rel(path),
                        "error": "master_checklist_markdown_pre_human_status_stale",
                        "expected_line": expected_line,
                    }
                )

    if issues:
        add_check(
            checks,
            "report_validation_summary_freshness",
            "FAIL",
            "Report or release markdown files contain stale pre-human validation summary counts.",
            {"checked_files": checked_files, "issues": issues[:50]},
        )
        return
    add_check(
        checks,
        "report_validation_summary_freshness",
        "PASS",
        "Report and release markdown files do not contain known stale pre-human validation count patterns.",
        {"checked_files": checked_files, "stale_patterns": list(STALE_REPORT_VALIDATION_PATTERNS)},
    )


def validate_evaluation_protocol_lock(checks, exp_dir):
    release_dir = exp_dir / "06_release"
    json_path = release_dir / "evaluation_protocol_lock.json"
    md_path = release_dir / "evaluation_protocol_lock.md"
    issues = []
    try:
        payload = read_json(json_path)
        md_text = md_path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        add_check(
            checks,
            "evaluation_protocol_lock",
            "FAIL",
            "Evaluation protocol lock is missing or unreadable.",
            {"json": rel(json_path), "markdown": rel(md_path), "error": str(exc)},
        )
        return

    if payload.get("claim_status") != "evaluation_protocol_locked_pending_human_returns":
        issues.append({"error": "unexpected_claim_status", "actual": payload.get("claim_status")})
    if payload.get("protocol_version") != "cape-eacl-evaluation-protocol-v1":
        issues.append({"error": "unexpected_protocol_version", "actual": payload.get("protocol_version")})

    stable = {key: payload.get(key) for key in EVALUATION_PROTOCOL_STABLE_KEYS}
    expected_hash = canonical_hash(stable)
    if payload.get("protocol_content_sha256") != expected_hash:
        issues.append(
            {
                "error": "protocol_content_sha256_mismatch",
                "expected": expected_hash,
                "actual": payload.get("protocol_content_sha256"),
            }
        )

    metric_groups = payload.get("metric_definitions") or {}
    for group in ["human_gold_core", "structural", "mapping_expert", "crosswalk_expert", "active_review_effort"]:
        rows = metric_groups.get(group) or []
        if not rows:
            issues.append({"error": "missing_metric_group", "group": group})
    human_metrics = {row.get("metric") for row in metric_groups.get("human_gold_core") or []}
    for metric in ["node_label_f1", "edge_exact_f1", "predicate_f1", "component_span_iou"]:
        if metric not in human_metrics:
            issues.append({"error": "missing_human_gold_metric", "metric": metric})

    condition_set = set((payload.get("condition_sets") or {}).get("main_condition_set") or [])
    missing_conditions = sorted(TRACEABILITY_EXPECTED_CONDITIONS - condition_set)
    if missing_conditions:
        issues.append({"error": "main_condition_set_missing_expected_conditions", "missing": missing_conditions})

    claim_policy = payload.get("claim_gate_policy") or {}
    if "No-substitution" in claim_policy.get("no_substitution_policy", ""):
        issues.append({"error": "no_substitution_policy_should_be_plain_sentence_not_label"})
    current_context = payload.get("current_context") or {}
    if current_context.get("current_claim_gate_status") != "FAIL":
        issues.append({"error": "claim_gate_status_should_remain_fail_pre_human", "actual": current_context.get("current_claim_gate_status")})

    public_rows = payload.get("locked_public_files") or []
    public_roles = {row.get("role") for row in public_rows}
    for role in [
        "revised_plan",
        "proposed_prompt",
        "human_gold_evaluator",
        "post_annotation_refresh_wrapper",
        "pre_human_handoff_validator",
    ]:
        if role not in public_roles:
            issues.append({"error": "missing_locked_public_role", "role": role})
    for row in public_rows:
        path = Path(row.get("path", ""))
        if not path.exists():
            issues.append({"error": "locked_public_file_missing", "role": row.get("role")})
            continue
        if row.get("sha256") != sha256_file(path):
            issues.append({"error": "locked_public_file_sha_mismatch", "role": row.get("role")})

    context_rows = current_context.get("current_context_files") or []
    context_roles = {row.get("role") for row in context_rows}
    for role in ["claim_gate_report", "method_module_coverage", "rq_evidence_matrix"]:
        if role not in context_roles:
            issues.append({"error": "missing_current_context_role", "role": role})
    for row in context_rows:
        path = Path(row.get("path", ""))
        if not path.exists():
            issues.append({"error": "current_context_file_missing", "role": row.get("role")})
            continue
        if row.get("sha256") != sha256_file(path):
            issues.append({"error": "current_context_file_sha_mismatch", "role": row.get("role")})

    private_rows = payload.get("locked_private_inputs") or []
    private_by_id = {row.get("source_id"): row for row in private_rows}
    private_input_ids = set(payload.get("locked_private_input_ids") or [])
    for source_id, path_text in EXPECTED_PROTOCOL_PRIVATE_INPUTS.items():
        if source_id not in private_input_ids:
            issues.append({"error": "missing_locked_private_input_id", "source_id": source_id})
        row = private_by_id.get(source_id)
        if not row:
            issues.append({"error": "missing_locked_private_input", "source_id": source_id})
            continue
        path = Path(path_text)
        if not path.exists():
            issues.append({"error": "private_input_missing_on_disk", "source_id": source_id})
            continue
        if row.get("sha256") != sha256_file(path):
            issues.append({"error": "private_input_sha_mismatch", "source_id": source_id})

    text_scan = json_path.read_text(encoding="utf-8", errors="replace") + "\n" + md_text
    risky_patterns = [pattern for pattern in PUBLIC_SAFE_FORBIDDEN_PATTERNS if pattern in text_scan]
    if risky_patterns:
        issues.append({"error": "protocol_lock_public_text_mentions_private_path_pattern", "patterns": risky_patterns})

    for pattern in [
        "Protocol content SHA256",
        "Metric Definitions",
        "Locked Private Inputs",
        "Current Context Files",
        "No-substitution policy",
        "Final paper claims still require adjudicated human-gold",
    ]:
        if pattern not in md_text:
            issues.append({"error": "protocol_markdown_missing_pattern", "pattern": pattern})

    commands = payload.get("evaluation_commands") or {}
    for command_id in ["preflight_human_returns", "apply_human_returns", "final_handoff_validation", "release_checksum"]:
        if not commands.get(command_id):
            issues.append({"error": "missing_evaluation_command", "command_id": command_id})

    if issues:
        add_check(
            checks,
            "evaluation_protocol_lock",
            "FAIL",
            "Evaluation protocol lock is missing, stale, unsafe, or incomplete.",
            {"json": rel(json_path), "markdown": rel(md_path), "issues": issues[:80]},
        )
        return

    add_check(
        checks,
        "evaluation_protocol_lock",
        "PASS",
        "Evaluation protocol lock freezes metrics, condition sets, commands, claim policy, and file hashes before human returns.",
        {
            "json": rel(json_path),
            "markdown": rel(md_path),
            "protocol_content_sha256": payload.get("protocol_content_sha256"),
            "locked_public_files": len(public_rows),
            "current_context_files": len(context_rows),
            "locked_private_inputs": len(private_rows),
            "main_conditions": len(condition_set),
        },
    )


def render_report(payload):
    lines = [
        "# CAPE-KG Pre-Human Handoff Validation",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Overall status: `{payload['overall_status']}`",
        f"Claim status: `{payload['claim_status']}`",
        "",
        "## Summary",
        "",
        f"- Checks: {payload['check_count']}",
        f"- PASS: {payload['status_counts'].get('PASS', 0)}",
        f"- WARN: {payload['status_counts'].get('WARN', 0)}",
        f"- FAIL: {payload['status_counts'].get('FAIL', 0)}",
        "",
        "## Checks",
        "",
        "| id | status | detail |",
        "|---|---|---|",
    ]
    for check in payload["checks"]:
        detail = str(check["detail"]).replace("|", "\\|")
        lines.append(f"| `{check['id']}` | `{check['status']}` | {detail} |")
    lines += [
        "",
        "## Interpretation",
        "",
        "- `PASS` means the pre-human handoff infrastructure is ready.",
        "- `WARN` keeps the known paper-claim blocker visible: human gold, IAA, adjudication, and human-gold scoring are not complete.",
        "- Any `FAIL` means the handoff/release artifacts should be fixed before asking annotators to start.",
    ]
    return "\n".join(lines) + "\n"


def run(args):
    exp_dir = Path(args.experiment_dir)
    outputs_dir = Path(args.outputs_dir)
    release_dir = exp_dir / "06_release"
    checks = []

    check_required_files(
        checks,
        [
            release_dir / "claim_gate_report.md",
            release_dir / "claim_gate_report.json",
            release_dir / "arr_submission_policy_checklist.md",
            release_dir / "arr_submission_policy_checklist.json",
            release_dir / "anonymized_submission_prep.md",
            release_dir / "anonymized_submission_prep.json",
            release_dir / "anonymized_submission_risk_scan.csv",
            release_dir / "responsible_nlp_checklist_prep.md",
            release_dir / "responsible_nlp_checklist_prep.json",
            release_dir / "responsible_nlp_checklist_items.csv",
            release_dir / "experiment_reproduction_card.md",
            release_dir / "experiment_reproduction_card.json",
            release_dir / "experiment_reproduction_conditions.csv",
            release_dir / "submission_readiness_audit.md",
            release_dir / "submission_readiness_audit.json",
            release_dir / "human_review_start_here_ko.md",
            release_dir / "human_review_claim_gate_one_page_ko.md",
            release_dir / "release_bundle_manifest.json",
            release_dir / "release_bundle_checksums.sha256",
            release_dir / "latest_release_bundle_index.md",
            release_dir / "latest_release_bundle_index.json",
            release_dir / "claimable_main_table.md",
            release_dir / "claimable_main_table.json",
            release_dir / "claim_language_guardrails.md",
            release_dir / "claim_language_guardrails.json",
            release_dir / "reviewer_response_prep.md",
            release_dir / "reviewer_response_prep.json",
            release_dir / "submission_timeline_action_board.md",
            release_dir / "submission_timeline_action_board.json",
            release_dir / "paper_readiness_checklist.md",
            release_dir / "paper_readiness_checklist.json",
            release_dir / "paper_table_blueprint.md",
            release_dir / "paper_table_blueprint.json",
            release_dir / "method_module_coverage.md",
            release_dir / "method_module_coverage.json",
            release_dir / "method_novelty_positioning.md",
            release_dir / "method_novelty_positioning.json",
            release_dir / "rq_evidence_matrix.md",
            release_dir / "rq_evidence_matrix.json",
            release_dir / "evaluation_protocol_lock.md",
            release_dir / "evaluation_protocol_lock.json",
            release_dir / "reviewer_risk_register.md",
            release_dir / "reviewer_risk_register.json",
            release_dir / "reviewer_risk_register.csv",
            release_dir / "cq_query_pack.md",
            release_dir / "cq_query_pack.json",
            release_dir / "ablation_coverage_report.md",
            release_dir / "ablation_coverage_report.json",
            release_dir / "alias_canonicalization_report.md",
            release_dir / "alias_canonicalization_report.json",
            release_dir / "prompt_node_edge_traceability.md",
            release_dir / "prompt_node_edge_traceability.json",
            release_dir / "schema_retrieval_coverage_report.md",
            release_dir / "schema_retrieval_coverage_report.json",
            release_dir / "schema_plan_alignment.md",
            release_dir / "schema_plan_alignment.json",
            release_dir / "public_reproducibility_manifest.md",
            release_dir / "public_reproducibility_manifest.json",
            release_dir / "public_reproducibility_manifest.csv",
            release_dir / "data_release_ethics_statement.md",
            release_dir / "external_resource_license_report.md",
            release_dir / "external_resource_license_report.json",
            release_dir / "external_resource_license_report.csv",
            release_dir / "human_review_return_preflight.md",
            release_dir / "human_review_return_preflight.json",
            release_dir / "annotation_return_field_guide_ko.md",
            release_dir / "annotation_return_field_guide.json",
            release_dir / "human_return_validation_error_playbook_ko.md",
            release_dir / "human_return_validation_error_playbook.json",
            release_dir / "annotation_batch_review_preview_summary.md",
            release_dir / "annotation_batch_review_preview_summary.json",
            release_dir / "gold_sampling_coverage_report.md",
            release_dir / "gold_sampling_coverage_report.json",
            release_dir / "gold_item_feasibility_report.md",
            release_dir / "gold_item_feasibility_report.json",
            release_dir / "strong_resegmented_review_preview_summary.md",
            release_dir / "strong_resegmented_review_preview_summary.json",
            release_dir / "strong_review_return_preflight.md",
            release_dir / "strong_review_return_preflight.json",
            release_dir / "strong_return_apply_last_run.json",
            release_dir / "strong_return_apply_last_run.md",
            release_dir / "strong_return_apply_refusal_last_run.json",
            release_dir / "strong_return_apply_refusal_last_run.md",
            release_dir / "human_return_apply_last_run.json",
            release_dir / "human_return_apply_last_run.md",
            release_dir / "human_return_apply_refusal_last_run.json",
            release_dir / "human_return_apply_refusal_last_run.md",
            release_dir / "post_annotation_refresh_last_run.json",
            release_dir / "human_gate_action_plan.md",
            release_dir / "human_gate_action_plan.json",
            release_dir / "human_review_master_checklist_ko.md",
            release_dir / "human_review_master_checklist_ko.json",
            exp_dir / "05_review/human_review_first_batch_execution_card_ko.md",
            exp_dir / "05_review/human_review_first_batch_execution_card.json",
            exp_dir / "05_review/human_review_role_quickstart_cards_ko.md",
            exp_dir / "05_review/human_review_role_quickstart_cards.json",
            exp_dir / "05_review/human_review_role_quickstart_cards.csv",
            exp_dir / "05_review/annotation_return_field_checklist.csv",
            exp_dir / "05_review/human_return_validation_error_codes.csv",
            release_dir / "human_review_status_dashboard_ko.md",
            release_dir / "human_review_status_dashboard_ko.json",
            release_dir / "human_review_launch_checklist_ko.md",
            release_dir / "human_review_launch_checklist_ko.json",
            release_dir / "human_review_packet_integrity.md",
            release_dir / "human_review_packet_integrity.json",
            release_dir / "active_review_human_effort_plan.md",
            release_dir / "active_review_human_effort_plan.json",
            release_dir / "active_review_human_effort_briefing.md",
            release_dir / "active_review_human_effort_briefing.json",
            release_dir / "qwen3_32b_awq_readiness.md",
            release_dir / "qwen3_32b_awq_readiness.json",
            release_dir / "strict_json_diagnostics.md",
            release_dir / "strict_json_diagnostics.json",
            release_dir / "qwen3_model_scaling_report.md",
            release_dir / "qwen3_model_scaling_report.json",
            release_dir / "paper_section_source_map.md",
            release_dir / "paper_section_source_map.json",
            release_dir / "eacl_submission_package_manifest.md",
            release_dir / "eacl_submission_package_manifest.json",
            release_dir / "post_human_scoring_readiness.md",
            release_dir / "post_human_scoring_readiness.json",
            release_dir / "metric_traceability_audit.md",
            release_dir / "metric_traceability_audit.json",
            release_dir / "metric_traceability_audit.csv",
            release_dir / "contribution_claim_traceability.md",
            release_dir / "contribution_claim_traceability.json",
            release_dir / "contribution_claim_traceability.csv",
            release_dir / "related_work_baseline_traceability.md",
            release_dir / "related_work_baseline_traceability.json",
            release_dir / "related_work_baseline_traceability.csv",
            release_dir / "annotation_protocol_traceability.md",
            release_dir / "annotation_protocol_traceability.json",
            release_dir / "annotation_protocol_traceability.csv",
            release_dir / "provenance_manifest.md",
            release_dir / "provenance_manifest.json",
            release_dir / "provenance_prov_o.ttl",
            release_dir / "provenance_prov_o_summary.json",
            release_dir / "provenance_prov_o_report.md",
            release_dir / "structural_review_action_plan.md",
            release_dir / "structural_review_action_plan.json",
            release_dir / "structural_review_return_preflight.md",
            release_dir / "structural_review_return_preflight.json",
            release_dir / "structural_review_application_plan.md",
            release_dir / "structural_review_application_plan.json",
            release_dir / "eacl_paper_draft_status.json",
            exp_dir / "07_reports/README_current_reports_ko.md",
            exp_dir / "07_reports/eacl_paper_draft.md",
            exp_dir / "05_review/active_review_human_effort_template.csv",
            exp_dir / "05_review/active_review_human_effort_briefing.csv",
            exp_dir / "05_review/annotation_batch_review_preview_summary.csv",
            exp_dir / "05_review/gold_sampling_coverage_by_chapter.csv",
            exp_dir / "05_review/gold_sampling_priority100_selected_chunks.csv",
            exp_dir / "05_review/gold_item_feasibility_by_batch.csv",
            exp_dir / "05_review/strong_resegmented_review_preview_summary.csv",
            exp_dir / "01_data/gold_annotation/strong_resegmented_342_max18/strong_review_preview.csv",
            exp_dir / "01_data/gold_annotation/strong_resegmented_342_max18/strong_review_preview.md",
            exp_dir / "05_review/human_review_status_next_actions.csv",
            exp_dir / "05_review/human_review_minimum_gate_launch_tasks.csv",
            exp_dir / "05_review/human_review_packet_integrity_issues.csv",
            exp_dir / "04_evaluation/provenance_llm_run_index.csv",
            exp_dir / "04_evaluation/cq_query_sample_answers.csv",
            exp_dir / "05_review/structural_review_application_actions.csv",
            exp_dir / "04_evaluation/active_review_efficiency_metrics.json",
            exp_dir / "04_evaluation/active_review_efficiency_report.md",
            exp_dir / "04_evaluation/active_review_ablation_metrics.json",
            exp_dir / "04_evaluation/active_review_ablation_report.md",
            exp_dir / "04_evaluation/ablation_coverage_by_condition.csv",
            exp_dir / "04_evaluation/active_review_human_effort_metrics.csv",
            exp_dir / "04_evaluation/active_review_human_effort_metrics.json",
            exp_dir / "04_evaluation/active_review_human_effort_report.md",
            exp_dir / "04_evaluation/actual_llm_silver_metrics.csv",
            exp_dir / "04_evaluation/actual_llm_silver_metrics.json",
            exp_dir / "04_evaluation/actual_llm_silver_evaluation_report.md",
            exp_dir / "04_evaluation/schema_retrieval_cq_support_by_condition.csv",
            exp_dir / "04_evaluation/alias_canonicalization_collision_groups.csv",
            exp_dir / "49_qwen3_8b_strict_json_1200_full_valid.jsonl",
            exp_dir / "49_sac_kg_verifier_pruner_baseline_valid.jsonl",
            exp_dir / "04_evaluation/qwen3_14b_core_silver_metrics.csv",
            exp_dir / "04_evaluation/qwen3_14b_core_silver_metrics.json",
            exp_dir / "04_evaluation/qwen3_14b_core_silver_evaluation_report.md",
            exp_dir / "04_evaluation/qwen3_32b_awq_core_silver_metrics.csv",
            exp_dir / "04_evaluation/qwen3_32b_awq_core_silver_metrics.json",
            exp_dir / "04_evaluation/qwen3_32b_awq_core_silver_evaluation_report.md",
            exp_dir / "04_evaluation/statistical_analysis_metrics.json",
            exp_dir / "04_evaluation/statistical_analysis_report.md",
            exp_dir / "04_evaluation/statistical_analysis_bootstrap.csv",
            exp_dir / "04_evaluation/statistical_analysis_mcnemar.csv",
            exp_dir / "04_evaluation/statistical_analysis_chunk_scores.csv",
            exp_dir / "04_evaluation/evidence_span_granularity_metrics.json",
            exp_dir / "04_evaluation/evidence_span_granularity_report.md",
            exp_dir / "04_evaluation/predicate_cue_span_metrics.json",
            exp_dir / "04_evaluation/predicate_cue_span_report.md",
            exp_dir / "04_evaluation/predicate_cue_span_rows.csv",
            release_dir / "edge_component_span_traceability.json",
            release_dir / "edge_component_span_traceability.md",
            outputs_dir / "06_triples/layer2_predicate_cue_spans.jsonl",
            outputs_dir / "13_evidence_graph/evidence_anchor_nodes.jsonl",
            outputs_dir / "13_evidence_graph/evidence_anchor_nodes.csv",
            outputs_dir / "13_evidence_graph/evidenced_by_edges.jsonl",
            outputs_dir / "13_evidence_graph/evidenced_by_edges.csv",
            outputs_dir / "13_evidence_graph/evidence_graph_projection_summary.json",
            outputs_dir / "13_evidence_graph/evidence_graph_projection_report.md",
            outputs_dir / "13_evidence_graph/edge_component_span_links.jsonl",
            outputs_dir / "13_evidence_graph/edge_component_span_links.csv",
            exp_dir / "04_evaluation/evidence_grounding_report.md",
            exp_dir / "04_evaluation/mapping_downstream_report.md",
            exp_dir / "04_evaluation/mapping_downstream_results.csv",
            exp_dir / "04_evaluation/mapping_downstream_arm_diagnostics.csv",
            exp_dir / "04_evaluation/mapping_downstream_arm_rerank_details.csv",
            exp_dir / "04_evaluation/mapping_downstream_arm_rerank_summary.json",
            exp_dir / "04_evaluation/mapping_expert_metrics.csv",
            exp_dir / "04_evaluation/mapping_expert_metrics.json",
            exp_dir / "04_evaluation/mapping_expert_evaluation_report.md",
            exp_dir / "04_evaluation/ncs_pcf_crosswalk_candidates.csv",
            exp_dir / "04_evaluation/ncs_pcf_crosswalk_summary.json",
            exp_dir / "04_evaluation/ncs_pcf_crosswalk_report.md",
            exp_dir / "04_evaluation/human_gold_span_iou_metrics.json",
            exp_dir / "04_evaluation/human_gold_span_iou_components.csv",
            exp_dir / "04_evaluation/human_gold_span_iou_report.md",
            exp_dir / "05_review/mapping_review_priority_queue.csv",
            exp_dir / "05_review/mapping_review_priority_queue.jsonl",
            exp_dir / "05_review/mapping_review_next_20_groups.csv",
            exp_dir / "05_review/mapping_review_next_60_rows.csv",
            exp_dir / "05_review/mapping_review_group_briefing_top20.csv",
            release_dir / "mapping_review_progress_summary.json",
            release_dir / "mapping_review_progress_report.md",
            release_dir / "mapping_review_group_briefing.json",
            release_dir / "mapping_review_group_briefing.md",
            exp_dir / "01_data/annotation_guideline_v1.md",
            exp_dir / "02_schema/competency_questions.json",
            exp_dir / "02_schema/prompts/B0_plain_llm_triple_extraction.txt",
            exp_dir / "02_schema/prompts/B1_predicate_constrained_llm.txt",
            exp_dir / "02_schema/prompts/B2_current_project_baseline.txt",
            exp_dir / "02_schema/prompts/B3_edc_style_baseline.txt",
            exp_dir / "02_schema/prompts/B4_taxonomy_rag_baseline.txt",
            exp_dir / "02_schema/prompts/B5_procedural_prompt_baseline.txt",
            exp_dir / "02_schema/prompts/B6_sac_kg_verifier_pruner_baseline.txt",
            exp_dir / "02_schema/prompts/P_cape_kg.txt",
            exp_dir / "02_schema/prompts/P_minus_Schema_retrieval.txt",
            exp_dir / "01_data/gold_annotation/adjudication_protocol.md",
            exp_dir / "01_data/mapping_review/mapping_review_protocol.md",
            release_dir / "human_review_handoff/human_review_handoff_manifest.json",
            release_dir / "human_review_handoff/human_review_handoff_report.md",
            release_dir / "human_review_handoff/human_review_handoff_checksums.sha256",
            release_dir / "annotation_roundtrip_smoke/roundtrip_smoke_summary.json",
            release_dir / "active_review_effort_roundtrip_smoke/active_review_effort_roundtrip_smoke_summary.json",
            release_dir / "mapping_roundtrip_smoke/mapping_roundtrip_smoke_summary.json",
            release_dir / "crosswalk_roundtrip_smoke/crosswalk_roundtrip_smoke_summary.json",
            exp_dir / "05_review/human_gate_required_returns.csv",
            exp_dir / "05_review/human_review_gate_dependency_matrix.csv",
            exp_dir / "05_review/human_review_master_return_files.csv",
            exp_dir / "00_plan/requirements_matrix.md",
            exp_dir / "00_plan/requirements_matrix.json",
            release_dir / "eacl_plan_compliance_matrix.md",
            release_dir / "eacl_plan_compliance_matrix.json",
            release_dir / "revised_plan_completion_audit.md",
            release_dir / "revised_plan_completion_audit.json",
            release_dir / "revised_plan_completion_audit_items.csv",
            release_dir / "revised_plan_completion_audit_public_safe.md",
            release_dir / "revised_plan_completion_audit_public_safe.json",
            release_dir / "revised_plan_completion_audit_public_safe_items.csv",
            release_dir / "revised_plan_section_status_ko.md",
            release_dir / "revised_plan_section_status_ko.json",
            release_dir / "revised_plan_section_status_ko.csv",
            outputs_dir / "11_neo4j_import_flat/nodes.csv",
            outputs_dir / "11_neo4j_import_flat/neo4j_import_http_8765.cypher",
            outputs_dir / "11_neo4j_import_flat/neo4j_evidence_queries.cypher",
            outputs_dir / "11_neo4j_import_flat/neo4j_csv_validation_report.json",
            outputs_dir / "11_neo4j_import/neo4j_csv_validation_report.json",
            release_dir / "neo4j_evidence_query_pack.json",
            release_dir / "neo4j_evidence_query_pack.md",
            outputs_dir / "09_visualization/kg_viewer.html",
            outputs_dir / "09_visualization/kg_full.json",
            outputs_dir / "09_visualization/kg_full.graphml",
            outputs_dir / "09_visualization/kg_static_overview.svg",
            outputs_dir / "09_visualization/visualization_readme.md",
            outputs_dir / "06_triples/evidence_anchors.jsonl",
            outputs_dir / "06_triples/layer2_triples_schema_valid.jsonl",
            outputs_dir / "12_rdf/cape_kg_layer2.ttl",
            outputs_dir / "12_rdf/cape_kg_runtime_shapes.shacl.ttl",
            outputs_dir / "12_rdf/cape_kg_shacl_validation_summary.json",
            outputs_dir / "12_rdf/cape_kg_shacl_validation_report.md",
            outputs_dir / "06_triples/layer2_triples_component_spans.jsonl",
            outputs_dir / "07_layer2_graph/layer2_nodes.jsonl",
            outputs_dir / "07_layer2_graph/layer2_edges.jsonl",
            outputs_dir / "07_layer2_graph/layer2_evidence_index.jsonl",
            outputs_dir / "03_schema/competency_questions.json",
            outputs_dir / "08_mapping/l2_ncs_pcf_crosswalk_all_pairs.jsonl",
            outputs_dir / "08_mapping/l2_ncs_pcf_crosswalk_candidates.jsonl",
            exp_dir / "08_public_benchmarks/public_benchmark_manifest.json",
            exp_dir / "08_public_benchmarks/public_benchmark_adapter_report.md",
            exp_dir / "08_public_benchmarks/public_benchmark_crosscheck_summary.json",
            exp_dir / "08_public_benchmarks/public_benchmark_crosscheck_report.md",
            exp_dir / "08_public_benchmarks/public_qwen3_8b_full_adapter_eval_summary.json",
            exp_dir / "08_public_benchmarks/public_qwen3_8b_subset_eval_summary.json",
            exp_dir / "08_public_benchmarks/public_qwen3_14b_subset_eval_summary.json",
            release_dir / "public_synthetic_examples/README.md",
            release_dir / "public_synthetic_examples/synthetic_chunks.jsonl",
            release_dir / "public_synthetic_examples/synthetic_gold.jsonl",
            release_dir / "public_synthetic_examples/synthetic_predictions.jsonl",
            release_dir / "public_synthetic_examples/synthetic_evaluation_summary.json",
        ],
    )
    validate_claim_state(checks, exp_dir)
    validate_claim_gate_blocker_alignment(checks, exp_dir)
    validate_requirements_matrix(checks, exp_dir)
    validate_eacl_plan_compliance_matrix(checks, exp_dir)
    validate_revised_plan_completion_audit(checks, exp_dir)
    validate_public_revised_plan_completion_audit(checks, exp_dir)
    validate_revised_plan_section_status(checks, exp_dir)
    validate_metric_traceability_audit(checks, exp_dir)
    validate_contribution_claim_traceability(checks, exp_dir)
    validate_related_work_baseline_traceability(checks, exp_dir)
    validate_annotation_protocol_traceability(checks, exp_dir)
    validate_method_module_coverage(checks, exp_dir)
    validate_paper_readiness_checklist(checks, exp_dir)
    validate_rq_evidence_matrix(checks, exp_dir)
    validate_evaluation_protocol_lock(checks, exp_dir)
    validate_reviewer_risk_register(checks, exp_dir)
    validate_cq_query_pack(checks, exp_dir)
    validate_human_gold_span_iou(checks, exp_dir)
    validate_evidence_grounding_report_safety(checks, exp_dir)
    validate_evidence_span_granularity_claim_safety(checks, exp_dir, outputs_dir)
    validate_predicate_cue_span_diagnostic(checks, exp_dir, outputs_dir)
    validate_edge_component_span_traceability(checks, exp_dir, outputs_dir)
    validate_active_review_diagnostics_safety(checks, exp_dir)
    validate_mapping_downstream_claim_safety(checks, exp_dir, outputs_dir)
    validate_llm_diagnostics_public_benchmark_safety(checks, exp_dir)
    validate_ablation_coverage_report(checks, exp_dir)
    validate_alias_canonicalization_report(checks, exp_dir, outputs_dir)
    validate_handoff_manifest(checks, exp_dir)
    validate_handoff_bundle_contents(checks, exp_dir)
    validate_component_span_handoff_coverage(checks, exp_dir)
    validate_prompt_node_edge_traceability(checks, exp_dir, outputs_dir)
    validate_schema_retrieval_coverage_report(checks, exp_dir)
    validate_schema_plan_alignment(checks, exp_dir, outputs_dir)
    validate_llm_condition_output_integrity(checks, exp_dir)
    validate_review_guidance(checks, exp_dir)
    validate_annotation_batch_review_preview(checks, exp_dir)
    validate_gold_sampling_coverage_report(checks, exp_dir)
    validate_gold_item_feasibility_report(checks, exp_dir)
    validate_checksum_file(checks, "handoff_bundle_checksums", release_dir / "human_review_handoff/human_review_handoff_checksums.sha256")
    validate_roundtrip_smoke(checks, exp_dir)
    validate_active_review_effort_roundtrip_smoke(checks, exp_dir)
    validate_mapping_roundtrip_smoke(checks, exp_dir)
    validate_crosswalk_roundtrip_smoke(checks, exp_dir)
    validate_claimable_main_table(checks, exp_dir)
    validate_claim_language_guardrails(checks, exp_dir)
    validate_reviewer_response_prep(checks, exp_dir)
    validate_submission_timeline_action_board(checks, exp_dir)
    validate_paper_table_blueprint(checks, exp_dir)
    validate_arr_submission_policy_checklist(checks, exp_dir)
    validate_anonymized_submission_prep(checks, exp_dir)
    validate_responsible_nlp_checklist_prep(checks, exp_dir)
    validate_experiment_reproduction_card(checks, exp_dir)
    validate_paper_tables_claim_safety(checks, exp_dir)
    validate_paper_section_source_map(checks, exp_dir)
    validate_post_human_scoring_readiness(checks, exp_dir)
    validate_eacl_submission_package_manifest(checks, exp_dir)
    validate_data_release_ethics_statement(checks, exp_dir)
    validate_provenance_manifest(checks, exp_dir)
    validate_layer2_evidence_triple_integrity(checks, exp_dir, outputs_dir)
    validate_evidence_graph_projection(checks, outputs_dir)
    validate_rdf_shacl_export(checks, outputs_dir)
    validate_human_review_return_preflight(checks, exp_dir)
    validate_strong_review_return_preflight(checks, exp_dir)
    validate_human_gate_action_plan(checks, exp_dir)
    validate_human_review_status_dashboard(checks, exp_dir)
    validate_human_review_first_batch_execution_card(checks, exp_dir)
    validate_human_review_role_quickstart_cards(checks, exp_dir)
    validate_human_review_launch_checklist(checks, exp_dir)
    validate_human_review_packet_integrity(checks, exp_dir)
    validate_human_return_apply_wrapper_safety(checks, exp_dir)
    validate_strong_return_apply_wrapper_safety(checks, exp_dir)
    validate_eacl_paper_draft(checks, exp_dir)
    validate_current_reports_index(checks, exp_dir)
    validate_neo4j_reports(checks, outputs_dir)
    validate_neo4j_evidence_query_pack(checks, exp_dir, outputs_dir)
    validate_kg_visualization_demo(checks, outputs_dir)
    validate_public_reproducibility_manifest(checks, exp_dir)
    validate_public_synthetic_examples_claim_safety(checks, exp_dir)
    validate_release_manifest(checks, exp_dir)
    validate_report_validation_summary_freshness(checks, exp_dir)
    validate_checksum_file(checks, "release_bundle_checksums", release_dir / "release_bundle_checksums.sha256")

    status_counts = {}
    for check in checks:
        status_counts[check["status"]] = status_counts.get(check["status"], 0) + 1
    overall_status = "FAIL" if status_counts.get("FAIL", 0) else "PASS"
    claim_status = (
        "pre_human_handoff_ready_not_submission_complete"
        if overall_status == "PASS"
        else "pre_human_handoff_incomplete"
    )
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": rel(exp_dir),
        "outputs_dir": rel(outputs_dir),
        "overall_status": overall_status,
        "claim_status": claim_status,
        "check_count": len(checks),
        "status_counts": status_counts,
        "checks": checks,
        "report": rel(release_dir / "pre_human_handoff_validation.md"),
    }
    if not args.no_write:
        write_json(release_dir / "pre_human_handoff_validation.json", payload)
        write_text(release_dir / "pre_human_handoff_validation.md", render_report(payload))
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if overall_status != "PASS":
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--outputs-dir", default=str(DEFAULT_OUTPUTS_DIR))
    parser.add_argument("--no-write", action="store_true", help="Validate and print results without updating validation artifacts.")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
