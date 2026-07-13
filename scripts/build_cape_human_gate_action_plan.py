#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a concrete human-gate action plan for CAPE-KG submission blockers."""

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")


RETURN_FIELDS = [
    "required_for_minimum",
    "task_type",
    "owner",
    "batch_or_group",
    "expected_rows",
    "input_file",
    "reviewed_file",
    "target_file",
    "present",
    "status",
    "next_action",
]

GATE_MATRIX_FIELDS = [
    "gate_id",
    "gate_type",
    "required_for_minimum",
    "claim_status",
    "unlock_condition",
    "current_progress",
    "required_return_files",
    "blocking_return_files_missing",
    "post_return_command",
    "next_action",
]


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


def write_csv(path, rows, fieldnames):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def bool_text(value):
    return "yes" if value else "no"


def build_return_rows(preflight, mapping_summary):
    rows = []
    annotation = preflight.get("annotation_returns") or {}
    for item in annotation.get("files", []):
        rows.append(
            {
                "task_type": "human_gold_annotation",
                "required_for_minimum": "yes",
                "owner": f"annotator_{item.get('annotator')}",
                "batch_or_group": item.get("batch"),
                "expected_rows": item.get("expected_batch_rows"),
                "input_file": item.get("input_file"),
                "reviewed_file": item.get("reviewed_file"),
                "target_file": item.get("target_file"),
                "present": bool_text(item.get("present")),
                "status": item.get("status"),
                "next_action": "Export edited JSONL with the exact reviewed_file name, then run preflight.",
            }
        )
    adjudication = preflight.get("adjudication_return") or {}
    if adjudication:
        rows.append(
            {
                "task_type": "human_gold_adjudication",
                "required_for_minimum": "yes",
                "owner": "adjudicator",
                "batch_or_group": "full_120_adjudication",
                "expected_rows": adjudication.get("expected_rows"),
                "input_file": adjudication.get("input_file"),
                "reviewed_file": adjudication.get("reviewed_file"),
                "target_file": adjudication.get("target_file"),
                "present": bool_text(adjudication.get("present")),
                "status": adjudication.get("status"),
                "next_action": "Resolve adjudication_draft rows, save adjudication_edited.jsonl, then run preflight/import.",
            }
        )
    mapping = preflight.get("mapping_return") or {}
    if mapping:
        mapping_expected_rows = (
            mapping.get("expected_top5_rows")
            or mapping.get("reviewed_rows")
            or mapping.get("target_rows")
            or mapping.get("expected_priority_groups")
        )
        rows.append(
            {
                "task_type": "mapping_expert_review",
                "required_for_minimum": "no",
                "owner": "mapping_expert",
                "batch_or_group": "top20_groups_top5_rows",
                "expected_rows": mapping_expected_rows,
                "input_file": mapping.get("target_file"),
                "reviewed_file": mapping.get("reviewed_file"),
                "target_file": mapping.get("target_file"),
                "present": bool_text(mapping.get("present")),
                "status": mapping.get("status"),
                "next_action": (
                    "Review Top-5 candidates for the 20 priority groups "
                    f"({mapping_expected_rows} rows), export mapping_review_items.reviewed.jsonl, then run preflight/import."
                ),
            }
        )
    crosswalk = preflight.get("crosswalk_return") or {}
    if crosswalk:
        rows.append(
            {
                "task_type": "crosswalk_expert_review",
                "required_for_minimum": "no",
                "owner": "crosswalk_expert",
                "batch_or_group": "ncs_pcf_crosswalk_candidates",
                "expected_rows": crosswalk.get("expected_rows"),
                "input_file": crosswalk.get("target_file"),
                "reviewed_file": crosswalk.get("reviewed_file"),
                "target_file": crosswalk.get("target_file"),
                "present": bool_text(crosswalk.get("present")),
                "status": crosswalk.get("status"),
                "next_action": "Review NCS-PCF crosswalk candidates, export crosswalk_review_items.reviewed.jsonl, then run preflight/import.",
            }
        )
    if not mapping and mapping_summary:
        rows.append(
            {
                "task_type": "mapping_expert_review",
                "required_for_minimum": "no",
                "owner": "mapping_expert",
                "batch_or_group": "top20_groups_top5_rows",
                "expected_rows": 100,
                "input_file": mapping_summary.get("review_file"),
                "reviewed_file": str(Path(mapping_summary.get("review_file", "")).with_suffix(".reviewed.jsonl")),
                "target_file": mapping_summary.get("review_file"),
                "present": "no",
                "status": "missing_reviewed_file",
                "next_action": "Review Top-5 candidates for the 20 priority groups (100 rows), export reviewed JSONL, then run preflight/import.",
            }
        )
    active_review = preflight.get("active_review_effort_return") or {}
    if active_review:
        rows.append(
            {
                "task_type": "active_review_human_effort",
                "required_for_minimum": "no",
                "owner": "active_reviewer",
                "batch_or_group": "pooled_active_uncertainty_random",
                "expected_rows": active_review.get("expected_rows"),
                "input_file": active_review.get("template_file"),
                "reviewed_file": active_review.get("reviewed_file"),
                "target_file": active_review.get("metrics_file"),
                "present": bool_text(active_review.get("present")),
                "status": active_review.get("status"),
                "next_action": "Fill reviewer_id, review_seconds, decision, corrected_error, and high_impact_correction in the active-review effort CSV, then run preflight/refresh.",
            }
        )
    return rows


def reviewed_files_for(rows, task_types):
    task_types = set(task_types)
    return [str(row.get("reviewed_file") or "") for row in rows if row.get("task_type") in task_types]


def missing_reviewed_files_for(rows, task_types):
    task_types = set(task_types)
    return [
        str(row.get("reviewed_file") or "")
        for row in rows
        if row.get("task_type") in task_types and str(row.get("present") or "").lower() != "yes"
    ]


def join_paths(paths):
    return "; ".join(path for path in paths if path)


def blocker_status(blockers, gate_id, default="pending_human"):
    return (blockers.get(gate_id) or {}).get("status") or default


def blocker_next_step(blockers, gate_id, default):
    return (blockers.get(gate_id) or {}).get("next_step") or default


def build_gate_dependency_matrix(return_rows, audit, preflight, mapping_summary, commands):
    blockers = {row.get("id"): row for row in audit.get("blocking_items", [])}
    annotation = preflight.get("annotation_returns") or {}
    adjudication = preflight.get("adjudication_return") or {}
    mapping_return = preflight.get("mapping_return") or {}
    active_review = preflight.get("active_review_effort_return") or {}

    annotation_files = reviewed_files_for(return_rows, {"human_gold_annotation"})
    annotation_missing = missing_reviewed_files_for(return_rows, {"human_gold_annotation"})
    adjudication_files = reviewed_files_for(return_rows, {"human_gold_adjudication"})
    adjudication_missing = missing_reviewed_files_for(return_rows, {"human_gold_adjudication"})
    mapping_files = reviewed_files_for(return_rows, {"mapping_expert_review"})
    mapping_missing = missing_reviewed_files_for(return_rows, {"mapping_expert_review"})
    crosswalk_files = reviewed_files_for(return_rows, {"crosswalk_expert_review"})
    crosswalk_missing = missing_reviewed_files_for(return_rows, {"crosswalk_expert_review"})
    active_files = reviewed_files_for(return_rows, {"active_review_human_effort"})
    active_missing = missing_reviewed_files_for(return_rows, {"active_review_human_effort"})

    gold_files = annotation_files + adjudication_files
    gold_missing = annotation_missing + adjudication_missing
    return [
        {
            "gate_id": "min.iaa",
            "gate_type": "minimum_accept",
            "required_for_minimum": "yes",
            "claim_status": blocker_status(blockers, "min.iaa"),
            "unlock_condition": "100 paired chunks with two independent annotator returns and IAA recomputation.",
            "current_progress": (
                f"{annotation.get('present_files', 0)}/{annotation.get('expected_files', 0)} annotation reviewed files present; "
                f"{annotation.get('paired_completed_chunks', 0)}/100 paired completed chunks."
            ),
            "required_return_files": join_paths(annotation_files),
            "blocking_return_files_missing": join_paths(annotation_missing),
            "post_return_command": commands["preflight_returns"] + " && " + commands["apply_wrapper"],
            "next_action": blocker_next_step(blockers, "min.iaa", "Import completed annotator A/B files and recompute IAA."),
        },
        {
            "gate_id": "min.gold_chunks",
            "gate_type": "minimum_accept",
            "required_for_minimum": "yes",
            "claim_status": blocker_status(blockers, "min.gold_chunks"),
            "unlock_condition": "100+ chunks adjudicated after A/B annotation and adjudication import.",
            "current_progress": f"{adjudication.get('completed_adjudicated_chunks', 0)}/100 adjudicated chunks.",
            "required_return_files": join_paths(gold_files),
            "blocking_return_files_missing": join_paths(gold_missing),
            "post_return_command": commands["preflight_returns"] + " && " + commands["apply_wrapper"],
            "next_action": blocker_next_step(
                blockers,
                "min.gold_chunks",
                "Complete two-annotator labeling and adjudication for at least 100 chunks.",
            ),
        },
        {
            "gate_id": "min.gold_items",
            "gate_type": "minimum_accept",
            "required_for_minimum": "yes",
            "claim_status": blocker_status(blockers, "min.gold_items"),
            "unlock_condition": "500+ adjudicated node/edge/evidence items available in human-gold validation.",
            "current_progress": "0/500 adjudicated node/edge/evidence items in current validation summary.",
            "required_return_files": join_paths(gold_files),
            "blocking_return_files_missing": join_paths(gold_missing),
            "post_return_command": commands["preflight_returns"] + " && " + commands["apply_wrapper"],
            "next_action": blocker_next_step(
                blockers,
                "min.gold_items",
                "Adjudicate enough nodes, edges, and evidence anchors to reach 500 gold items.",
            ),
        },
        {
            "gate_id": "min.proposed",
            "gate_type": "minimum_accept",
            "required_for_minimum": "yes",
            "claim_status": blocker_status(blockers, "min.proposed", default="partial"),
            "unlock_condition": "P_cape_kg_actual scored against adjudicated human gold after gold completion.",
            "current_progress": "P_cape_kg_actual generated for 120 rows; human-gold scored conditions=[] until adjudication exists.",
            "required_return_files": join_paths(adjudication_files),
            "blocking_return_files_missing": join_paths(adjudication_missing),
            "post_return_command": commands["apply_imports_and_refresh"],
            "next_action": blocker_next_step(
                blockers,
                "min.proposed",
                "Score P_cape_kg_actual against adjudicated human gold after gold completion.",
            ),
        },
        {
            "gate_id": "mapping.expert_review",
            "gate_type": "optional_strong",
            "required_for_minimum": "no",
            "claim_status": "pending_expert_review",
            "unlock_condition": "Top-5 NCS/PCF mapping groups reviewed by expert and mapping metrics recomputed.",
            "current_progress": (
                f"{mapping_summary.get('complete_source_groups', 0)}/"
                f"{mapping_summary.get('source_task_standard_groups', 0)} source-task-standard groups complete; "
                f"{mapping_return.get('complete_top5_groups', 0)}/"
                f"{mapping_return.get('expected_priority_groups', 0)} priority Top-5 groups complete; "
                f"{mapping_summary.get('pending_rows', 0)} candidate rows pending."
            ),
            "required_return_files": join_paths(mapping_files),
            "blocking_return_files_missing": join_paths(mapping_missing),
            "post_return_command": commands["preflight_returns"] + " && " + commands["apply_wrapper"],
            "next_action": mapping_return.get("next_action")
            or "Review Top-5 candidates for the 20 priority groups (100 rows), then run preflight/import.",
        },
        {
            "gate_id": "crosswalk.expert_review",
            "gate_type": "optional_strong",
            "required_for_minimum": "no",
            "claim_status": "pending_crosswalk_expert_review",
            "unlock_condition": "NCS-PCF crosswalk candidate rows reviewed by expert and crosswalk metrics recomputed.",
            "current_progress": (
                f"{(preflight.get('crosswalk_return') or {}).get('complete_source_groups', 0)}/"
                f"{(preflight.get('crosswalk_return') or {}).get('expected_source_tasks', 0)} source-task groups complete; "
                f"{(preflight.get('crosswalk_return') or {}).get('completed_rows', 0)}/"
                f"{(preflight.get('crosswalk_return') or {}).get('expected_rows', 0)} rows complete."
            ),
            "required_return_files": join_paths(crosswalk_files),
            "blocking_return_files_missing": join_paths(crosswalk_missing),
            "post_return_command": commands["preflight_returns"] + " && " + commands["apply_wrapper"],
            "next_action": "Review crosswalk_review_items.reviewed.jsonl, then run preflight/import.",
        },
        {
            "gate_id": "strong.active_review_effort",
            "gate_type": "strong_or_auxiliary",
            "required_for_minimum": "no",
            "claim_status": "pending_human_effort_timing",
            "unlock_condition": "Active-review effort CSV completed with timing/correction fields and metrics refreshed.",
            "current_progress": (
                f"{active_review.get('reviewed_rows', 0)}/{active_review.get('expected_rows', 0)} reviewed rows; "
                f"{active_review.get('timed_review_rows', 0)} timed rows."
            ),
            "required_return_files": join_paths(active_files),
            "blocking_return_files_missing": join_paths(active_missing),
            "post_return_command": commands["preflight_returns"] + " && " + commands["apply_wrapper"],
            "next_action": "Fill active_review_human_effort.reviewed.csv and rerun preflight/refresh.",
        },
    ]


def build_payload(exp_dir):
    exp_dir = Path(exp_dir)
    release_dir = exp_dir / "06_release"
    review_dir = exp_dir / "05_review"
    handoff_dir = release_dir / "human_review_handoff"

    audit = read_json(release_dir / "submission_readiness_audit.json", {}) or {}
    claim_gate = read_json(release_dir / "claim_gate_report.json", {}) or {}
    annotation_progress = read_json(release_dir / "annotation_progress_summary.json", {}) or {}
    preflight = read_json(release_dir / "human_review_return_preflight.json", {}) or {}
    handoff = read_json(handoff_dir / "human_review_handoff_manifest.json", {}) or {}
    optional_strong = handoff.get("optional_strong_review") or {}
    mapping_summary = read_json(release_dir / "mapping_review_progress_summary.json", {}) or {}
    batch_rows = read_csv(review_dir / "human_gold_batches/full_120_batch_assignment_overview.csv")
    next_100 = read_csv(review_dir / "human_gold_next_100_worklist.csv")
    mapping_groups = read_csv(review_dir / "mapping_review_next_20_groups.csv")
    mapping_rows = read_csv(review_dir / "mapping_review_next_60_rows.csv")

    return_rows = build_return_rows(preflight, mapping_summary)
    minimum_return_rows = [row for row in return_rows if row.get("required_for_minimum") == "yes"]
    optional_strong_return_rows = [row for row in return_rows if row.get("required_for_minimum") != "yes"]
    annotation_returns = preflight.get("annotation_returns") or {}
    adjudication_return = preflight.get("adjudication_return") or {}
    mapping_return = preflight.get("mapping_return") or {}
    crosswalk_return = preflight.get("crosswalk_return") or {}
    active_review_return = preflight.get("active_review_effort_return") or {}
    audit_summary = audit.get("summary") or {}
    full_120 = annotation_progress.get("full_120_summary") or {}

    commands = {
        "verify_handoff_checksums": "sha256sum -c experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/human_review_handoff_checksums.sha256",
        "preflight_returns": "python3 scripts/validate_cape_human_review_returns.py --experiment-dir experiments/cape_kg_eacl_20260627",
        "dry_run_wrapper": "PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=0 bash scripts/run_cape_human_return_apply.sh",
        "apply_wrapper": "PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=1 bash scripts/run_cape_human_return_apply.sh",
        "dry_run_refresh": "APPLY_IMPORTS=0 bash scripts/run_cape_post_annotation_refresh.sh",
        "apply_imports_and_refresh": "APPLY_IMPORTS=1 bash scripts/run_cape_post_annotation_refresh.sh",
        "final_handoff_validation": "python3 scripts/validate_cape_pre_human_handoff.py --experiment-dir experiments/cape_kg_eacl_20260627 --outputs-dir outputs",
        "verify_release_checksums": "sha256sum -c experiments/cape_kg_eacl_20260627/06_release/release_bundle_checksums.sha256",
    }

    gate_dependency_matrix = build_gate_dependency_matrix(return_rows, audit, preflight, mapping_summary, commands)

    blockers = [
        {
            "id": row.get("id"),
            "requirement": row.get("requirement"),
            "status": row.get("status"),
            "next_step": row.get("next_step"),
        }
        for row in audit.get("blocking_items", [])
    ]

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "claim_status": "human_gate_action_plan_ready_pending_returns",
        "readiness": {
            "submission_claim_status": audit.get("claim_status"),
            "claim_gate_overall_status": claim_gate.get("overall_status"),
            "minimum_accept_blocking_items": audit_summary.get("minimum_accept_blocking_items"),
            "blocking_items": blockers,
            "overall_return_status": preflight.get("overall_status"),
        },
        "minimum_thresholds": {
            "adjudicated_chunks_required": 100,
            "gold_items_required": 500,
            "paired_iaa_chunks_required": 100,
            "proposed_condition_required_for_scoring": "P_cape_kg_actual",
            "mapping_review_minimum": "Top-5 candidates for priority source-task groups; expert P@K/MRR claims require completed groups.",
        },
        "current_progress": {
            "minimum_paper_gate_return_files": len(minimum_return_rows),
            "minimum_paper_gate_return_files_present": sum(1 for row in minimum_return_rows if row.get("present") == "yes"),
            "optional_strong_return_files": len(optional_strong_return_rows),
            "optional_strong_return_files_present": sum(1 for row in optional_strong_return_rows if row.get("present") == "yes"),
            "tracked_human_return_files": len(return_rows),
            "tracked_human_return_files_present": sum(1 for row in return_rows if row.get("present") == "yes"),
            "human_gold_full_120_chunks": full_120.get("chunk_count"),
            "annotator_A_completed_chunks": full_120.get("annotator_A_completed_chunks"),
            "annotator_B_completed_chunks": full_120.get("annotator_B_completed_chunks"),
            "paired_completed_chunks": full_120.get("paired_completed_chunks"),
            "adjudicated_chunks": full_120.get("adjudicated_chunks"),
            "candidate_edges_total": full_120.get("candidate_edges_total"),
            "active_review_chunks": full_120.get("active_review_chunks"),
            "high_impact_chunks": full_120.get("high_impact_chunks"),
            "annotation_expected_reviewed_files": annotation_returns.get("expected_files"),
            "annotation_present_reviewed_files": annotation_returns.get("present_files"),
            "annotation_valid_reviewed_files": annotation_returns.get("valid_files"),
            "adjudication_reviewed_file_present": adjudication_return.get("present"),
            "adjudication_completed_chunks": adjudication_return.get("completed_adjudicated_chunks"),
            "mapping_completed_rows": mapping_summary.get("completed_rows"),
            "mapping_pending_rows": mapping_summary.get("pending_rows"),
            "mapping_complete_source_groups": mapping_summary.get("complete_source_groups"),
            "crosswalk_expected_rows": crosswalk_return.get("expected_rows"),
            "crosswalk_completed_rows": crosswalk_return.get("completed_rows"),
            "crosswalk_complete_source_groups": crosswalk_return.get("complete_source_groups"),
            "crosswalk_reviewed_file_present": crosswalk_return.get("present"),
            "active_review_effort_expected_rows": active_review_return.get("expected_rows"),
            "active_review_effort_reviewed_rows": active_review_return.get("reviewed_rows"),
            "active_review_effort_timed_rows": active_review_return.get("timed_review_rows"),
            "active_review_effort_present": active_review_return.get("present"),
            "optional_strong_package": optional_strong.get("package"),
            "optional_strong_review_units": optional_strong.get("rows"),
            "optional_strong_source_chunks": optional_strong.get("source_chunk_count"),
            "optional_strong_candidate_edges": optional_strong.get("candidate_edges_total"),
            "optional_strong_status": optional_strong.get("claim_status"),
        },
        "handoff": {
            "manifest": str(handoff_dir / "human_review_handoff_manifest.json"),
            "report": str(handoff_dir / "human_review_handoff_report.md"),
            "checksums": str(handoff_dir / "human_review_handoff_checksums.sha256"),
            "annotator_A_bundle": (handoff.get("bundles") or {}).get("annotator_A", {}).get("path"),
            "annotator_B_bundle": (handoff.get("bundles") or {}).get("annotator_B", {}).get("path"),
            "coordinator_bundle": (handoff.get("bundles") or {}).get("coordinator", {}).get("path"),
            "adjudicator_bundle": (handoff.get("bundles") or {}).get("adjudicator", {}).get("path"),
            "mapping_expert_bundle": (handoff.get("bundles") or {}).get("mapping_expert", {}).get("path"),
            "crosswalk_expert_bundle": (handoff.get("bundles") or {}).get("crosswalk_expert", {}).get("path"),
            "active_review_effort_bundle": (handoff.get("bundles") or {}).get("active_review_effort", {}).get("path"),
            "strong_resegmented_bundle": (handoff.get("bundles") or {}).get("strong_resegmented_review", {}).get("path"),
        },
        "required_return_files": return_rows,
        "gate_dependency_matrix": gate_dependency_matrix,
        "annotation_batches": batch_rows,
        "top_annotation_worklist_preview": next_100[:20],
        "mapping_priority_groups": mapping_groups[:20],
        "mapping_priority_rows": mapping_rows[:60],
        "commands": commands,
        "output_files": {
            "plan_json": str(release_dir / "human_gate_action_plan.json"),
            "plan_md": str(release_dir / "human_gate_action_plan.md"),
            "required_returns_csv": str(review_dir / "human_gate_required_returns.csv"),
            "gate_dependency_matrix_csv": str(review_dir / "human_review_gate_dependency_matrix.csv"),
        },
    }
    return payload


def build_report(payload):
    readiness = payload["readiness"]
    progress = payload["current_progress"]
    thresholds = payload["minimum_thresholds"]
    handoff = payload["handoff"]
    commands = payload["commands"]

    lines = [
        "# CAPE-KG Human Gate Action Plan",
        "",
        f"Generated: {payload['generated_at_utc']}",
        "",
        "This is an operational action plan for the remaining human-gold and expert-review gates. It does not create gold labels or paper-claimable evidence by itself.",
        "",
        "## Current Gate Status",
        "",
        f"- Submission readiness: `{readiness.get('submission_claim_status')}`",
        f"- Claim gate overall status: `{readiness.get('claim_gate_overall_status')}`",
        f"- Return preflight status: `{readiness.get('overall_return_status')}`",
        f"- Minimum-accept blocking items: {readiness.get('minimum_accept_blocking_items')}",
        f"- Minimum paper-gate return files: {progress.get('minimum_paper_gate_return_files_present')}/{progress.get('minimum_paper_gate_return_files')}",
        f"- Optional/strong claim return files: {progress.get('optional_strong_return_files_present')}/{progress.get('optional_strong_return_files')}",
        f"- Required claim/human return files: {progress.get('tracked_human_return_files_present')}/{progress.get('tracked_human_return_files')}",
        "- Optional structural review files are tracked in the 16-file master checklist, but they do not block the minimum paper gate.",
        "",
        "## Blocking Items",
        "",
    ]
    for row in readiness.get("blocking_items", []):
        lines.append(f"- `{row.get('id')}`: {row.get('requirement')} -> {row.get('next_step')}")
    lines += [
        "",
        "## Gate Dependency Matrix",
        "",
        "| gate | type | minimum | claim status | current progress | missing return files | next action |",
        "|---|---|---:|---|---|---|---|",
    ]
    for row in payload["gate_dependency_matrix"]:
        lines.append(
            f"| `{row['gate_id']}` | {row['gate_type']} | {row['required_for_minimum']} | "
            f"{row['claim_status']} | {row['current_progress']} | `{row['blocking_return_files_missing']}` | "
            f"{row['next_action']} |"
        )
    lines += [
        "",
        "## Minimum Thresholds",
        "",
        f"- Adjudicated chunks: {thresholds['adjudicated_chunks_required']}",
        f"- Gold node/edge/evidence items: {thresholds['gold_items_required']}",
        f"- Paired IAA chunks: {thresholds['paired_iaa_chunks_required']}",
        f"- Proposed condition to score: `{thresholds['proposed_condition_required_for_scoring']}`",
        f"- Mapping review: {thresholds['mapping_review_minimum']}",
        "",
        "## Current Progress",
        "",
        f"- Full annotation package chunks: {progress.get('human_gold_full_120_chunks')}",
        f"- Annotator A completed chunks: {progress.get('annotator_A_completed_chunks')}",
        f"- Annotator B completed chunks: {progress.get('annotator_B_completed_chunks')}",
        f"- Paired completed chunks: {progress.get('paired_completed_chunks')}",
        f"- Adjudicated chunks: {progress.get('adjudicated_chunks')}",
        f"- Annotation reviewed files present: {progress.get('annotation_present_reviewed_files')}/{progress.get('annotation_expected_reviewed_files')}",
        f"- Adjudication reviewed file present: `{progress.get('adjudication_reviewed_file_present')}`",
        f"- Adjudication completed chunks in reviewed return: {progress.get('adjudication_completed_chunks')}",
        f"- Mapping review completed rows: {progress.get('mapping_completed_rows')}",
        f"- Mapping review pending rows: {progress.get('mapping_pending_rows')}",
        f"- Mapping complete source groups: {progress.get('mapping_complete_source_groups')}",
        f"- Crosswalk review completed/expected rows: {progress.get('crosswalk_completed_rows')}/{progress.get('crosswalk_expected_rows')}",
        f"- Crosswalk complete source groups: {progress.get('crosswalk_complete_source_groups')}",
        f"- Crosswalk reviewed file present: `{progress.get('crosswalk_reviewed_file_present')}`",
        f"- Active-review effort reviewed file present: `{progress.get('active_review_effort_present')}`",
        f"- Active-review effort expected/reviewed/timed rows: {progress.get('active_review_effort_expected_rows')}/"
        f"{progress.get('active_review_effort_reviewed_rows')}/{progress.get('active_review_effort_timed_rows')}",
        f"- Optional strong package: `{progress.get('optional_strong_package')}`",
        f"- Optional strong review units/source chunks: {progress.get('optional_strong_review_units')}/{progress.get('optional_strong_source_chunks')}",
        f"- Optional strong candidate edges: {progress.get('optional_strong_candidate_edges')}",
        f"- Optional strong status: `{progress.get('optional_strong_status')}`",
        "",
        "## Handoff Files",
        "",
        f"- Annotator A bundle: `{handoff.get('annotator_A_bundle')}`",
        f"- Annotator B bundle: `{handoff.get('annotator_B_bundle')}`",
        f"- Coordinator bundle: `{handoff.get('coordinator_bundle')}`",
        f"- Adjudicator bundle: `{handoff.get('adjudicator_bundle')}`",
        f"- Mapping expert bundle: `{handoff.get('mapping_expert_bundle')}`",
        f"- Crosswalk expert bundle: `{handoff.get('crosswalk_expert_bundle')}`",
        f"- Active-review effort bundle: `{handoff.get('active_review_effort_bundle')}`",
        f"- Optional strong 300+ bundle: `{handoff.get('strong_resegmented_bundle')}`",
        f"- Handoff report: `{handoff.get('report')}`",
        f"- Checksums: `{handoff.get('checksums')}`",
        "",
        "## Tracked Return Files",
        "",
        "| minimum | task | owner | batch/group | expected rows | present | status | reviewed file |",
        "|---:|---|---|---|---:|---:|---|---|",
    ]
    for row in payload["required_return_files"]:
        lines.append(
            f"| {row.get('required_for_minimum')} | {row['task_type']} | {row['owner']} | {row['batch_or_group']} | "
            f"{row.get('expected_rows', '')} | {row['present']} | {row['status']} | `{row['reviewed_file']}` |"
        )
    lines += [
        "",
        "## Annotation Batch Order",
        "",
        "| batch | rank | chunks | candidate edges | high-impact chunks | A file | B file |",
        "|---|---|---:|---:|---:|---|---|",
    ]
    for row in payload["annotation_batches"]:
        lines.append(
            f"| {row.get('batch_id')} | {row.get('rank_start')}-{row.get('rank_end')} | "
            f"{row.get('chunk_count')} | {row.get('candidate_edges_total')} | {row.get('high_impact_chunks')} | "
            f"`{row.get('annotator_A_file')}` | `{row.get('annotator_B_file')}` |"
        )
    lines += [
        "",
        "## Mapping Review Priority",
        "",
        "| priority | standard | source task | pending top5 | top score | score gap |",
        "|---:|---|---|---:|---:|---:|",
    ]
    for row in payload["mapping_priority_groups"][:20]:
        lines.append(
            f"| {row.get('priority_score')} | {row.get('standard')} | {row.get('source_label')} | "
            f"{row.get('pending_top5_rows')} | {row.get('top_score')} | {row.get('score_gap')} |"
        )
    lines += [
        "",
        "## Commands",
        "",
        "Verify handoff bundle checksums:",
        "",
        "```bash",
        commands["verify_handoff_checksums"],
        "```",
        "",
        "Check returned review files before applying imports:",
        "",
        "```bash",
        commands["preflight_returns"],
        "```",
        "",
        "Recommended dry-run wrapper before applying returned files:",
        "",
        "```bash",
        commands["dry_run_wrapper"],
        "```",
        "",
        "Recommended apply wrapper after preflight passes:",
        "",
        "```bash",
        commands["apply_wrapper"],
        "```",
        "",
        "Low-level dry refresh without applying returned files:",
        "",
        "```bash",
        commands["dry_run_refresh"],
        "```",
        "",
        "Low-level apply refresh after preflight passes:",
        "",
        "```bash",
        commands["apply_imports_and_refresh"],
        "```",
        "",
        "Verify final handoff and release checksums:",
        "",
        "```bash",
        commands["final_handoff_validation"],
        commands["verify_release_checksums"],
        "```",
        "",
        "## Output Files",
        "",
        f"- JSON: `{payload['output_files']['plan_json']}`",
        f"- Markdown: `{payload['output_files']['plan_md']}`",
        f"- Required returns CSV: `{payload['output_files']['required_returns_csv']}`",
        f"- Gate dependency matrix CSV: `{payload['output_files']['gate_dependency_matrix_csv']}`",
        "",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    args = parser.parse_args()

    exp_dir = Path(args.experiment_dir)
    payload = build_payload(exp_dir)
    json_path = exp_dir / "06_release/human_gate_action_plan.json"
    md_path = exp_dir / "06_release/human_gate_action_plan.md"
    csv_path = exp_dir / "05_review/human_gate_required_returns.csv"
    gate_csv_path = exp_dir / "05_review/human_review_gate_dependency_matrix.csv"
    write_json(json_path, payload)
    write_text(md_path, build_report(payload))
    write_csv(csv_path, payload["required_return_files"], RETURN_FIELDS)
    write_csv(gate_csv_path, payload["gate_dependency_matrix"], GATE_MATRIX_FIELDS)
    minimum_return_rows = [row for row in payload["required_return_files"] if row.get("required_for_minimum") == "yes"]
    optional_strong_return_rows = [row for row in payload["required_return_files"] if row.get("required_for_minimum") != "yes"]
    print(json.dumps({
        "plan_json": str(json_path),
        "plan_md": str(md_path),
        "required_returns_csv": str(csv_path),
        "gate_dependency_matrix_csv": str(gate_csv_path),
        "claim_status": payload["claim_status"],
        "minimum_return_file_count": len(minimum_return_rows),
        "optional_strong_return_file_count": len(optional_strong_return_rows),
        "tracked_return_file_count": len(payload["required_return_files"]),
        "return_file_count": len(payload["required_return_files"]),
        "gate_dependency_rows": len(payload["gate_dependency_matrix"]),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
