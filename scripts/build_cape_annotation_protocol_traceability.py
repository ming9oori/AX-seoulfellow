#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build annotation-protocol traceability artifacts for CAPE-KG."""

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_OUTPUTS_DIR = Path("outputs")
DEFAULT_PLAN_FILE = Path("AX_EACL_submission_review_revised_plan.md")
CLAIM_STATUS = "annotation_protocol_traceability_ready_pending_human_returns"


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_rows(path):
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


def file_state(path, role):
    path = Path(path)
    exists = path.exists() and path.is_file()
    return {
        "role": role,
        "path": rel(path),
        "exists": exists,
        "bytes": path.stat().st_size if exists else 0,
    }


def md_table(headers, rows):
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        values = []
        for header in headers:
            value = row.get(header, "")
            if isinstance(value, list):
                value = "<br>".join(str(v) for v in value)
            values.append(str(value).replace("|", "\\|").replace("\n", "<br>"))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def int_value(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def present_count(rows):
    return sum(1 for row in rows if str(row.get("present", "")).lower() == "yes")


def split_semicolon_count(value):
    if not value:
        return 0
    return len([item.strip() for item in str(value).split(";") if item.strip()])


def build_plan_target_rows():
    return [
        {
            "target_id": "T01_task_or_procedure_step",
            "plan_requirement": "Task 또는 ProcedureStep 표시",
            "protocol_coverage": "Guideline node type table and gold_node_fields cover DomainTask and ProcedureStep.",
            "evidence_artifacts": "annotation_guideline_v1.md; annotation_schema.json",
            "current_status": "covered_by_protocol_pending_human_annotation",
        },
        {
            "target_id": "T02_artifact",
            "plan_requirement": "Artifact 표시",
            "protocol_coverage": "Guideline node type table and gold_node_fields cover Artifact.",
            "evidence_artifacts": "annotation_guideline_v1.md; annotation_schema.json",
            "current_status": "covered_by_protocol_pending_human_annotation",
        },
        {
            "target_id": "T03_role",
            "plan_requirement": "Role 표시",
            "protocol_coverage": "Guideline node type table and gold_node_fields cover Role.",
            "evidence_artifacts": "annotation_guideline_v1.md; annotation_schema.json",
            "current_status": "covered_by_protocol_pending_human_annotation",
        },
        {
            "target_id": "T04_decision_gateway",
            "plan_requirement": "DecisionGateway 표시",
            "protocol_coverage": "Guideline node type table and gold_node_fields cover DecisionGateway.",
            "evidence_artifacts": "annotation_guideline_v1.md; annotation_schema.json",
            "current_status": "covered_by_protocol_pending_human_annotation",
        },
        {
            "target_id": "T05_guard_condition",
            "plan_requirement": "GuardCondition 표시",
            "protocol_coverage": "Guideline node type table and gold_node_fields cover GuardCondition.",
            "evidence_artifacts": "annotation_guideline_v1.md; annotation_schema.json",
            "current_status": "covered_by_protocol_pending_human_annotation",
        },
        {
            "target_id": "T06_review_checkpoint",
            "plan_requirement": "ReviewCheckpoint 표시",
            "protocol_coverage": "Guideline node type table covers ReviewCheckpoint; current KG projects review/check/approval-signaled ProcedureStep nodes as ReviewCheckpoint.",
            "evidence_artifacts": "annotation_guideline_v1.md; cq_query_pack.md; prompt_node_edge_traceability.md; structural_evaluation_metrics.json",
            "current_status": "covered_by_protocol_and_current_kg_projection_pending_human_annotation",
        },
        {
            "target_id": "T07_principle_or_risk",
            "plan_requirement": "Principle/Risk 표시",
            "protocol_coverage": "Guideline node type table and predicate table cover Principle and Risk.",
            "evidence_artifacts": "annotation_guideline_v1.md; annotation_schema.json",
            "current_status": "covered_by_protocol_pending_human_annotation",
        },
        {
            "target_id": "T08_edge_type",
            "plan_requirement": "Edge type 표시",
            "protocol_coverage": "Guideline predicate table and gold_edge_fields require predicate, source, target, and decision.",
            "evidence_artifacts": "annotation_guideline_v1.md; annotation_schema.json",
            "current_status": "covered_by_protocol_pending_human_annotation",
        },
        {
            "target_id": "T09_evidence_span",
            "plan_requirement": "Evidence span 표시",
            "protocol_coverage": "Guideline evidence section and gold_edge_fields require evidence_anchor_ids and evidence_spans.",
            "evidence_artifacts": "annotation_guideline_v1.md; annotation_schema.json; human_gold_span_iou_report.md",
            "current_status": "covered_by_protocol_pending_human_annotation",
        },
        {
            "target_id": "T10_page_and_chunk_id",
            "plan_requirement": "page/chunk ID 표시",
            "protocol_coverage": "Batch/template records retain chunk_id and page metadata; annotators must not modify package identity.",
            "evidence_artifacts": "annotation_guideline_v1.md; annotation_batch_assignment_summary.json; human_review_master_return_files.csv",
            "current_status": "covered_by_protocol_pending_human_annotation",
        },
    ]


def build_workflow_rows(summary):
    return [
        {
            "workflow_id": "W01_schema_and_guideline",
            "stage": "Annotation schema and guideline",
            "evidence": "annotation_schema.json; annotation_guideline_v1.md",
            "current_status": "ready",
            "gate_effect": "Defines allowed node/edge/evidence fields before human annotation.",
        },
        {
            "workflow_id": "W02_batch_assignment",
            "stage": "Priority-100 two-annotator batch assignment",
            "evidence": "annotation_batch_assignment_summary.json",
            "current_status": f"{summary['assigned_chunks']}/{summary['minimum_chunk_target']} minimum chunks assigned",
            "gate_effect": "Prepares the minimum 100-chunk paper gate inputs.",
        },
        {
            "workflow_id": "W03_independent_annotation",
            "stage": "Independent annotator A/B returns",
            "evidence": "human_gate_required_returns.csv",
            "current_status": f"{summary['minimum_required_return_file_present_count']}/{summary['minimum_required_return_file_count']} minimum return files present",
            "gate_effect": "Unlocks IAA, adjudication, and human-gold scoring only after returns exist.",
        },
        {
            "workflow_id": "W04_iaa",
            "stage": "Inter-annotator agreement",
            "evidence": "iaa_full_120/iaa_summary.json",
            "current_status": f"{summary['completed_pair_chunks']}/{summary['minimum_chunk_target']} paired chunks completed",
            "gate_effect": "Blocks edge F1/type agreement/span IoU reporting until paired annotation exists.",
        },
        {
            "workflow_id": "W05_adjudication",
            "stage": "Adjudication",
            "evidence": "full_120/adjudication_draft_summary.json",
            "current_status": f"{summary['adjudicated_chunks']}/{summary['minimum_chunk_target']} adjudicated chunks",
            "gate_effect": "Blocks final gold labels and paper main table until adjudication is complete.",
        },
        {
            "workflow_id": "W06_human_gold_validation",
            "stage": "Human-gold validation",
            "evidence": "human_gold_validation_summary.json",
            "current_status": f"{summary['gold_item_count']}/{summary['minimum_gold_item_target']} adjudicated items",
            "gate_effect": "Requires 100+ chunks, 500+ items, and zero validation errors for minimum claim readiness.",
        },
        {
            "workflow_id": "W07_proposed_human_gold_scoring",
            "stage": "P_cape_kg_actual human-gold scoring",
            "evidence": "human_gold_metrics.json",
            "current_status": summary["human_gold_metric_status"],
            "gate_effect": "Final proposed-method F1 remains unavailable before adjudicated gold.",
        },
        {
            "workflow_id": "W08_mapping_expert_review",
            "stage": "NCS/PCF mapping expert review",
            "evidence": "human_gate_required_returns.csv; mapping_expert_metrics.json",
            "current_status": f"{summary['mapping_review_return_present_count']}/{summary['mapping_review_return_file_count']} expert return files present",
            "gate_effect": "Blocks mapping P@K/MRR/nDCG and accept-rate claims.",
        },
        {
            "workflow_id": "W09_crosswalk_expert_review",
            "stage": "NCS-PCF crosswalk expert review",
            "evidence": "human_gate_required_returns.csv; crosswalk_expert_metrics.json",
            "current_status": f"{summary['crosswalk_review_return_present_count']}/{summary['crosswalk_review_return_file_count']} expert return files present",
            "gate_effect": "Blocks crosswalk utility and ranking claims.",
        },
        {
            "workflow_id": "W10_active_review_effort",
            "stage": "Active-review human-effort evidence",
            "evidence": "human_gate_required_returns.csv; active_review_human_effort_report.md",
            "current_status": f"{summary['active_effort_return_present_count']}/{summary['active_effort_return_file_count']} effort return files present",
            "gate_effect": "Blocks active-review efficiency and human-effort reduction claims.",
        },
    ]


def build_payload(exp_dir, outputs_dir, plan_file):
    exp_dir = Path(exp_dir)
    outputs_dir = Path(outputs_dir)
    plan_file = Path(plan_file)
    data_dir = exp_dir / "01_data"
    gold_dir = data_dir / "gold_annotation"
    eval_dir = exp_dir / "04_evaluation"
    review_dir = exp_dir / "05_review"
    release_dir = exp_dir / "06_release"

    schema = read_json(gold_dir / "annotation_schema.json", {}) or {}
    batch = read_json(release_dir / "annotation_batch_assignment_summary.json", {}) or {}
    packet = read_json(release_dir / "human_review_packet_integrity.json", {}) or {}
    packet_summary = packet.get("summary") or {}
    iaa = read_json(gold_dir / "iaa_full_120/iaa_summary.json", {}) or {}
    adjudication = read_json(gold_dir / "full_120/adjudication_draft_summary.json", {}) or {}
    validation = read_json(eval_dir / "human_gold_validation_summary.json", {}) or {}
    metrics = read_json(eval_dir / "human_gold_metrics.json", {}) or {}
    gate_rows = read_csv_rows(review_dir / "human_review_gate_dependency_matrix.csv")
    return_rows = read_csv_rows(review_dir / "human_gate_required_returns.csv")

    required_rows = [row for row in return_rows if row.get("requiredness", "required") == "required"]
    minimum_rows = [row for row in return_rows if row.get("required_for_minimum") == "yes"]
    mapping_rows = [row for row in return_rows if row.get("task_type") == "mapping_expert_review"]
    crosswalk_rows = [row for row in return_rows if row.get("task_type") == "crosswalk_expert_review"]
    effort_rows = [row for row in return_rows if row.get("task_type") == "active_review_human_effort"]
    task_type_counts = Counter(row.get("task_type", "unknown") for row in return_rows)
    task_type_present = Counter(row.get("task_type", "unknown") for row in return_rows if row.get("present") == "yes")

    summary = {
        "claim_status": CLAIM_STATUS,
        "plan_target_count": 10,
        "covered_plan_target_count": 10,
        "minimum_chunk_target": 100,
        "minimum_gold_item_target": 500,
        "strong_chunk_target_min": 300,
        "strong_chunk_target_max": 500,
        "strong_gold_item_target_min": 1500,
        "strong_gold_item_target_max": 3000,
        "batch_count": int_value(batch.get("batch_count")),
        "batch_size": int_value(batch.get("batch_size")),
        "assigned_chunks": int_value(batch.get("assigned_chunks")),
        "candidate_edges_total": int_value(batch.get("candidate_edges_total")),
        "active_review_items_total": int_value(batch.get("active_review_items_total")),
        "high_impact_chunks": int_value(batch.get("high_impact_chunks")),
        "annotator_count": 2,
        "adjudicator_required": True,
        "minimum_annotation_input_files": int_value(packet_summary.get("minimum_annotation_input_files")),
        "minimum_annotation_chunks": int_value(packet_summary.get("minimum_annotation_chunks")),
        "minimum_annotation_candidate_edges": int_value(packet_summary.get("minimum_annotation_candidate_edges")),
        "required_return_file_count": len(required_rows),
        "required_return_file_present_count": present_count(required_rows),
        "minimum_required_return_file_count": len(minimum_rows),
        "minimum_required_return_file_present_count": present_count(minimum_rows),
        "completed_pair_chunks": int_value(iaa.get("completed_pair_chunks")),
        "pending_pair_chunks": int_value(iaa.get("pending_pair_chunks")),
        "adjudicated_chunks": int_value(validation.get("completed_adjudicated_chunks")),
        "pending_or_incomplete_chunks": int_value(validation.get("pending_or_incomplete_chunks")),
        "gold_item_count": int_value(validation.get("gold_item_count_for_readiness")),
        "validation_error_count": int_value(validation.get("validation_error_count")),
        "human_gold_metric_status": metrics.get("claim_status", "unknown"),
        "packet_integrity_error_count": int_value(packet_summary.get("integrity_error_count")),
        "packet_integrity_warning_count": int_value(packet_summary.get("integrity_warning_count")),
        "handoff_bundle_count": int_value(packet_summary.get("handoff_bundle_count")),
        "missing_handoff_bundle_count": int_value(packet_summary.get("missing_handoff_bundle_count")),
        "mapping_review_return_file_count": len(mapping_rows),
        "mapping_review_return_present_count": present_count(mapping_rows),
        "crosswalk_review_return_file_count": len(crosswalk_rows),
        "crosswalk_review_return_present_count": present_count(crosswalk_rows),
        "active_effort_return_file_count": len(effort_rows),
        "active_effort_return_present_count": present_count(effort_rows),
        "iaa_status": iaa.get("status"),
        "adjudication_claim_status": adjudication.get("claim_status"),
        "human_gold_claim_status": validation.get("claim_status"),
    }

    plan_target_rows = build_plan_target_rows()
    workflow_rows = build_workflow_rows(summary)
    return_file_summary = [
        {
            "task_type": task_type,
            "rows": task_type_counts[task_type],
            "present": task_type_present[task_type],
            "missing": task_type_counts[task_type] - task_type_present[task_type],
        }
        for task_type in sorted(task_type_counts)
    ]
    gate_summary_rows = [
        {
            "gate_id": row.get("gate_id", ""),
            "gate_type": row.get("gate_type", ""),
            "required_for_minimum": row.get("required_for_minimum", ""),
            "claim_status": row.get("claim_status", ""),
            "current_progress": row.get("current_progress", ""),
            "blocking_return_file_count": split_semicolon_count(row.get("blocking_return_files_missing")),
        }
        for row in gate_rows
    ]

    source_artifacts = {
        "revised_plan": file_state(plan_file, "revised EACL plan"),
        "annotation_guideline": file_state(data_dir / "annotation_guideline_v1.md", "human-gold annotation guideline"),
        "annotation_schema": file_state(gold_dir / "annotation_schema.json", "human-gold schema"),
        "batch_assignment": file_state(release_dir / "annotation_batch_assignment_summary.json", "priority-100 batch assignment summary"),
        "human_review_packet_integrity": file_state(release_dir / "human_review_packet_integrity.json", "handoff bundle integrity summary"),
        "iaa_summary": file_state(gold_dir / "iaa_full_120/iaa_summary.json", "IAA summary"),
        "adjudication_draft_summary": file_state(gold_dir / "full_120/adjudication_draft_summary.json", "adjudication draft summary"),
        "human_gold_validation_summary": file_state(eval_dir / "human_gold_validation_summary.json", "human-gold validation summary"),
        "human_gold_metrics": file_state(eval_dir / "human_gold_metrics.json", "human-gold metric output"),
        "required_returns": file_state(review_dir / "human_gate_required_returns.csv", "required human-return manifest"),
        "gate_dependency_matrix": file_state(review_dir / "human_review_gate_dependency_matrix.csv", "claim gate dependency matrix"),
        "claim_gate_report": file_state(release_dir / "claim_gate_report.json", "claim gate report"),
        "outputs_dir": file_state(outputs_dir / "07_layer2_graph/layer2_edges.jsonl", "final Layer 2 edge output"),
    }

    missing_sources = sorted(row["path"] for row in source_artifacts.values() if not row["exists"] or row["bytes"] == 0)
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "claim_status": CLAIM_STATUS,
        "plan_file": rel(plan_file),
        "experiment_dir": rel(exp_dir),
        "outputs_dir": rel(outputs_dir),
        "summary": summary,
        "annotation_schema_summary": {
            "annotation_file_type": schema.get("annotation_file_type"),
            "required_chunk_fields": schema.get("required_chunk_fields", []),
            "gold_node_fields": schema.get("gold_node_fields", []),
            "gold_edge_fields": schema.get("gold_edge_fields", []),
            "completed_status_values": schema.get("completed_status_values", []),
            "paper_claim_requires": schema.get("paper_claim_requires", []),
        },
        "plan_target_rows": plan_target_rows,
        "workflow_rows": workflow_rows,
        "return_file_summary": return_file_summary,
        "gate_summary_rows": gate_summary_rows,
        "claim_boundary": {
            "safe_scope": "Use as an internal traceability map from revised-plan annotation requirements to prepared annotation protocol, batches, IAA/adjudication placeholders, and claim gates.",
            "not_claimable": "This artifact does not satisfy human-gold annotation, IAA, adjudication, final extraction F1, mapping expert review, crosswalk utility, or active-review efficiency claims.",
            "human_or_expert_gated": True,
            "current_gate_status": "pending_human_annotations",
        },
        "source_artifacts": source_artifacts,
        "missing_source_artifacts": missing_sources,
        "outputs": {
            "json": rel(release_dir / "annotation_protocol_traceability.json"),
            "markdown": rel(release_dir / "annotation_protocol_traceability.md"),
            "csv": rel(release_dir / "annotation_protocol_traceability.csv"),
        },
    }
    return payload


def render_md(payload):
    summary = payload["summary"]
    lines = [
        "# CAPE-KG Annotation Protocol Traceability",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Claim status: `{payload['claim_status']}`",
        f"Plan: `{payload['plan_file']}`",
        "",
        "This artifact maps the revised plan's annotation requirements to the prepared human-gold protocol, batch assignments, IAA/adjudication placeholders, validation summaries, and human-return gates.",
        "It is a workflow traceability artifact, not human-gold performance evidence.",
        "",
        "## Summary",
        "",
    ]
    for key in [
        "plan_target_count",
        "covered_plan_target_count",
        "minimum_chunk_target",
        "minimum_gold_item_target",
        "batch_count",
        "assigned_chunks",
        "candidate_edges_total",
        "minimum_required_return_file_count",
        "minimum_required_return_file_present_count",
        "completed_pair_chunks",
        "pending_pair_chunks",
        "adjudicated_chunks",
        "gold_item_count",
        "packet_integrity_error_count",
        "handoff_bundle_count",
        "missing_handoff_bundle_count",
        "iaa_status",
        "adjudication_claim_status",
        "human_gold_claim_status",
    ]:
        lines.append(f"- {key}: `{summary.get(key)}`")
    lines.extend(
        [
            "",
            "## Plan Annotation Targets",
            "",
            md_table(
                ["target_id", "plan_requirement", "protocol_coverage", "evidence_artifacts", "current_status"],
                payload["plan_target_rows"],
            ),
            "",
            "## Human-Gold Workflow Traceability",
            "",
            md_table(["workflow_id", "stage", "evidence", "current_status", "gate_effect"], payload["workflow_rows"]),
            "",
            "## Return File Summary",
            "",
            md_table(["task_type", "rows", "present", "missing"], payload["return_file_summary"]),
            "",
            "## Human-Gold Gate Boundary",
            "",
            f"- Safe scope: {payload['claim_boundary']['safe_scope']}",
            f"- Not claimable: {payload['claim_boundary']['not_claimable']}",
            f"- Human/expert gated: `{payload['claim_boundary']['human_or_expert_gated']}`",
            f"- Current gate status: `{payload['claim_boundary']['current_gate_status']}`",
            "",
            "## Gate Dependency Snapshot",
            "",
            md_table(
                ["gate_id", "gate_type", "required_for_minimum", "claim_status", "current_progress", "blocking_return_file_count"],
                payload["gate_summary_rows"],
            ),
            "",
            "## Source Artifacts",
            "",
            md_table(["role", "path", "exists", "bytes"], list(payload["source_artifacts"].values())),
            "",
            "## Interpretation",
            "",
            "- The plan target coverage is complete at the protocol/workflow level: all ten annotation target categories are represented in guideline/schema/gate artifacts.",
            "- The paper minimum is not yet satisfied because human annotator returns, IAA, adjudication, and human-gold scoring are still pending.",
            "- Mapping, crosswalk, and active-review efficiency claims remain expert/human-return gated.",
            "",
        ]
    )
    return "\n".join(lines)


def write_csv_rows(path, payload):
    fields = [
        "target_id",
        "plan_requirement",
        "protocol_coverage",
        "evidence_artifacts",
        "current_status",
    ]
    write_csv(path, payload["plan_target_rows"], fields)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", type=Path, default=DEFAULT_EXP_DIR)
    parser.add_argument("--outputs-dir", type=Path, default=DEFAULT_OUTPUTS_DIR)
    parser.add_argument("--plan-file", type=Path, default=DEFAULT_PLAN_FILE)
    args = parser.parse_args()

    payload = build_payload(args.experiment_dir, args.outputs_dir, args.plan_file)
    release_dir = args.experiment_dir / "06_release"
    json_path = release_dir / "annotation_protocol_traceability.json"
    md_path = release_dir / "annotation_protocol_traceability.md"
    csv_path = release_dir / "annotation_protocol_traceability.csv"
    write_json(json_path, payload)
    write_text(md_path, render_md(payload))
    write_csv_rows(csv_path, payload)
    print(json.dumps({"claim_status": payload["claim_status"], "outputs": payload["outputs"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
