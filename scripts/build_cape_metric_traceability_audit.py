#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a claim-safe metric traceability audit for the revised EACL plan."""

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_OUTPUTS_DIR = Path("outputs")
DEFAULT_PLAN_FILE = Path("AX_EACL_submission_review_revised_plan.md")
CLAIM_STATUS = "metric_traceability_ready_pending_human_gold_and_expert_returns"

METRIC_BINDINGS = {
    "M01_node_f1": {
        "plan_metric": "Node F1",
        "plan_section": "9.3 Main evaluation metrics",
        "protocol_groups": ["human_gold_core"],
        "protocol_metrics": ["node_label_f1"],
        "evaluator_scripts": ["scripts/evaluate_cape_human_gold.py"],
        "paper_tables": ["T02_main_extraction_human_gold"],
        "diagnostic_outputs": ["experiments/cape_kg_eacl_20260627/04_evaluation/actual_llm_silver_metrics.json"],
    },
    "M02_edge_f1": {
        "plan_metric": "Edge F1",
        "plan_section": "9.3 Main evaluation metrics",
        "protocol_groups": ["human_gold_core"],
        "protocol_metrics": ["edge_exact_f1", "predicate_f1"],
        "evaluator_scripts": ["scripts/evaluate_cape_human_gold.py"],
        "paper_tables": ["T02_main_extraction_human_gold"],
        "diagnostic_outputs": ["experiments/cape_kg_eacl_20260627/04_evaluation/actual_llm_silver_metrics.json"],
    },
    "M03_evidence_exact_iou": {
        "plan_metric": "Evidence Exact Match / Evidence IoU",
        "plan_section": "9.3 Main evaluation metrics",
        "protocol_groups": ["human_gold_core"],
        "protocol_metrics": ["evidence_exact_or_f1", "component_span_exact_match", "component_span_iou"],
        "evaluator_scripts": ["scripts/evaluate_cape_human_gold.py", "scripts/evaluate_cape_human_gold_span_iou.py"],
        "paper_tables": ["T02_main_extraction_human_gold"],
        "diagnostic_outputs": [
            "experiments/cape_kg_eacl_20260627/04_evaluation/evidence_span_granularity_metrics.json",
            "experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_span_iou_metrics.json",
        ],
    },
    "M04_unsupported_edge_rate": {
        "plan_metric": "Unsupported Edge Rate",
        "plan_section": "9.3 Main evaluation metrics",
        "protocol_groups": ["human_gold_core"],
        "protocol_metrics": ["evidence_exact_or_f1"],
        "evaluator_scripts": ["scripts/evaluate_cape_human_gold.py"],
        "paper_tables": ["T02_main_extraction_human_gold"],
        "diagnostic_outputs": ["experiments/cape_kg_eacl_20260627/04_evaluation/evidence_grounding_report.md"],
    },
    "M05_ontology_conformance": {
        "plan_metric": "Ontology Conformance",
        "plan_section": "9.3 Main evaluation metrics",
        "protocol_groups": ["structural"],
        "protocol_metrics": ["ontology_conformance"],
        "evaluator_scripts": ["scripts/build_cape_structural_evaluation.py", "scripts/export_cape_kg_rdf_shacl.py"],
        "paper_tables": ["T03_cq_schema_ablation", "T04_structural_cq_diagnostics"],
        "diagnostic_outputs": [
            "experiments/cape_kg_eacl_20260627/04_evaluation/ontology_conformance_metrics.json",
            "outputs/12_rdf/cape_kg_shacl_validation_summary.json",
        ],
    },
    "M06_procedural_consistency": {
        "plan_metric": "Procedural Consistency",
        "plan_section": "9.3 Main evaluation metrics",
        "protocol_groups": ["structural"],
        "protocol_metrics": ["procedural_consistency"],
        "evaluator_scripts": ["scripts/build_cape_structural_evaluation.py"],
        "paper_tables": ["T04_structural_cq_diagnostics"],
        "diagnostic_outputs": ["experiments/cape_kg_eacl_20260627/04_evaluation/procedural_consistency_metrics.json"],
    },
    "M07_cq_answerability": {
        "plan_metric": "CQ Answerability",
        "plan_section": "9.3 Main evaluation metrics",
        "protocol_groups": ["structural"],
        "protocol_metrics": ["cq_answerability"],
        "evaluator_scripts": ["scripts/build_cape_cq_query_pack.py", "scripts/build_cape_structural_evaluation.py"],
        "paper_tables": ["T03_cq_schema_ablation", "T04_structural_cq_diagnostics"],
        "diagnostic_outputs": [
            "experiments/cape_kg_eacl_20260627/04_evaluation/cq_answerability_structural_metrics.json",
            "experiments/cape_kg_eacl_20260627/06_release/cq_query_pack.json",
        ],
    },
    "M08_mapping_pk_mrr_ndcg": {
        "plan_metric": "NCS/PCF Mapping P@K / MRR / nDCG",
        "plan_section": "9.3 and 9.5 Downstream task",
        "protocol_groups": ["mapping_expert"],
        "protocol_metrics": ["hit_at_1", "hit_at_5", "precision_at_5", "mrr", "ndcg_at_10"],
        "evaluator_scripts": ["scripts/evaluate_cape_mapping_review.py"],
        "paper_tables": ["T06_mapping_downstream"],
        "diagnostic_outputs": [
            "experiments/cape_kg_eacl_20260627/04_evaluation/mapping_expert_metrics.json",
            "experiments/cape_kg_eacl_20260627/04_evaluation/mapping_downstream_arm_rerank_summary.json",
        ],
    },
    "M09_crosswalk_accept_utility": {
        "plan_metric": "NCS-PCF Crosswalk Accept Rate / Utility",
        "plan_section": "9.5 Downstream task",
        "protocol_groups": ["crosswalk_expert"],
        "protocol_metrics": ["expert_accept_rate", "hit_at_1", "hit_at_5", "precision_at_10", "mrr", "ndcg_at_10", "utility_grade_mean"],
        "evaluator_scripts": ["scripts/evaluate_cape_crosswalk_review.py", "scripts/build_cape_ncs_pcf_crosswalk.py"],
        "paper_tables": ["T07_crosswalk_downstream"],
        "diagnostic_outputs": [
            "experiments/cape_kg_eacl_20260627/04_evaluation/crosswalk_expert_metrics.json",
            "experiments/cape_kg_eacl_20260627/04_evaluation/ncs_pcf_crosswalk_summary.json",
        ],
    },
    "M10_active_review_efficiency": {
        "plan_metric": "Active Review Efficiency",
        "plan_section": "9.3 Main evaluation metrics",
        "protocol_groups": ["active_review_effort"],
        "protocol_metrics": ["review_seconds", "corrections_per_hour", "high_impact_corrections_per_hour"],
        "evaluator_scripts": ["scripts/evaluate_cape_active_review_efficiency.py", "scripts/build_cape_active_review_human_effort.py"],
        "paper_tables": ["T08_active_review_efficiency"],
        "diagnostic_outputs": [
            "experiments/cape_kg_eacl_20260627/04_evaluation/active_review_human_effort_metrics.json",
            "experiments/cape_kg_eacl_20260627/04_evaluation/active_review_efficiency_metrics.json",
            "experiments/cape_kg_eacl_20260627/04_evaluation/active_review_ablation_metrics.json",
        ],
    },
}


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


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


def file_state(path):
    path = Path(path)
    return {"path": rel(path), "exists": path.exists(), "bytes": path.stat().st_size if path.exists() else 0}


def as_paths(rows):
    paths = []
    for row in rows or []:
        if isinstance(row, dict) and row.get("path"):
            paths.append(row["path"])
    return paths


def table_lookup(blueprint):
    return {row.get("table_id"): row for row in blueprint.get("tables") or []}


def protocol_lookup(protocol):
    out = {}
    for group, rows in (protocol.get("metric_definitions") or {}).items():
        out[group] = {row.get("metric") for row in rows}
    return out


def build_metric_rows(exp_dir, outputs_dir):
    exp_dir = Path(exp_dir)
    outputs_dir = Path(outputs_dir)
    release_dir = exp_dir / "06_release"
    post_human = read_json(release_dir / "post_human_scoring_readiness.json", {}) or {}
    protocol = read_json(release_dir / "evaluation_protocol_lock.json", {}) or {}
    blueprint = read_json(release_dir / "paper_table_blueprint.json", {}) or {}
    claim_gate = read_json(release_dir / "claim_gate_report.json", {}) or {}
    compliance = read_json(release_dir / "eacl_plan_compliance_matrix.json", {}) or {}
    metrics = {row.get("metric_id"): row for row in post_human.get("metrics") or []}
    protocol_groups = protocol_lookup(protocol)
    tables = table_lookup(blueprint)
    gate_ids = {row.get("gate_id") for row in claim_gate.get("gates") or []}
    gate_ids.update(row.get("id") for row in compliance.get("checklist_rows") or [] if row.get("id"))
    rows = []
    for metric_id, binding in METRIC_BINDINGS.items():
        metric = metrics.get(metric_id) or {}
        scoring_outputs = as_paths(metric.get("scoring_outputs"))
        output_files = sorted(set(scoring_outputs + binding["diagnostic_outputs"]))
        output_states = [file_state(path) for path in output_files]
        evaluator_states = [file_state(path) for path in binding["evaluator_scripts"]]
        table_ids = binding["paper_tables"]
        table_present = [table_id for table_id in table_ids if table_id in tables]
        protocol_missing = []
        for group, names in zip(binding["protocol_groups"], [binding["protocol_metrics"] for _ in binding["protocol_groups"]]):
            available = protocol_groups.get(group, set())
            for name in names:
                if name not in available:
                    protocol_missing.append(f"{group}:{name}")
        required_gates = metric.get("required_gate_ids") or []
        unknown_gates = sorted(set(required_gates) - gate_ids)
        missing_outputs = [row["path"] for row in output_states if not row["exists"]]
        missing_scripts = [row["path"] for row in evaluator_states if not row["exists"]]
        issues = []
        if not metric:
            issues.append("missing_post_human_metric_row")
        if metric.get("claimable_now") is not False:
            issues.append("metric_should_not_be_claimable_pre_human")
        if metric.get("claim_status") != "pending_human_returns":
            issues.append("unexpected_metric_claim_status")
        if protocol_missing:
            issues.append("protocol_metric_missing")
        if unknown_gates:
            issues.append("unknown_required_gate")
        if missing_outputs:
            issues.append("missing_output_file")
        if missing_scripts:
            issues.append("missing_evaluator_script")
        if set(table_present) != set(table_ids):
            issues.append("paper_table_binding_missing")
        rows.append(
            {
                "metric_id": metric_id,
                "metric_name": metric.get("metric_name") or binding["plan_metric"],
                "plan_metric": binding["plan_metric"],
                "plan_section": binding["plan_section"],
                "claim_status": metric.get("claim_status") or "missing",
                "claimable_now": bool(metric.get("claimable_now")),
                "required_gate_ids": required_gates,
                "expected_return_files": metric.get("expected_return_files"),
                "present_return_files": metric.get("present_return_files"),
                "protocol_groups": binding["protocol_groups"],
                "protocol_metrics": binding["protocol_metrics"],
                "paper_tables": table_ids,
                "evaluator_scripts": binding["evaluator_scripts"],
                "output_files": output_files,
                "evaluator_scripts_present": not missing_scripts,
                "output_files_present": not missing_outputs,
                "paper_tables_present": set(table_present) == set(table_ids),
                "protocol_metrics_present": not protocol_missing,
                "required_gates_known": not unknown_gates,
                "issue_count": len(issues),
                "issues": issues,
            }
        )
    return rows


def row_to_csv(row):
    return {
        "metric_id": row["metric_id"],
        "metric_name": row["metric_name"],
        "plan_metric": row["plan_metric"],
        "plan_section": row["plan_section"],
        "claim_status": row["claim_status"],
        "claimable_now": "yes" if row["claimable_now"] else "no",
        "required_gate_ids": ",".join(row["required_gate_ids"]),
        "expected_return_files": row["expected_return_files"],
        "present_return_files": row["present_return_files"],
        "protocol_groups": ",".join(row["protocol_groups"]),
        "protocol_metrics": ",".join(row["protocol_metrics"]),
        "paper_tables": ",".join(row["paper_tables"]),
        "evaluator_scripts": ",".join(row["evaluator_scripts"]),
        "output_files": ",".join(row["output_files"]),
        "evaluator_scripts_present": "yes" if row["evaluator_scripts_present"] else "no",
        "output_files_present": "yes" if row["output_files_present"] else "no",
        "paper_tables_present": "yes" if row["paper_tables_present"] else "no",
        "protocol_metrics_present": "yes" if row["protocol_metrics_present"] else "no",
        "required_gates_known": "yes" if row["required_gates_known"] else "no",
        "issue_count": row["issue_count"],
        "issues": ",".join(row["issues"]),
    }


def build_payload(exp_dir, outputs_dir, plan_file):
    exp_dir = Path(exp_dir)
    release_dir = exp_dir / "06_release"
    rows = build_metric_rows(exp_dir, outputs_dir)
    issue_rows = [row for row in rows if row["issue_count"]]
    pending_rows = [row for row in rows if row["claim_status"] == "pending_human_returns"]
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "claim_status": CLAIM_STATUS,
        "experiment_dir": rel(exp_dir),
        "outputs_dir": rel(outputs_dir),
        "plan_file": rel(plan_file),
        "summary": {
            "metric_count": len(rows),
            "pending_metric_count": len(pending_rows),
            "claimable_metric_count": sum(1 for row in rows if row["claimable_now"]),
            "metric_issue_count": sum(row["issue_count"] for row in rows),
            "metric_rows_with_issues": len(issue_rows),
            "all_evaluator_scripts_present": all(row["evaluator_scripts_present"] for row in rows),
            "all_output_files_present": all(row["output_files_present"] for row in rows),
            "all_paper_tables_present": all(row["paper_tables_present"] for row in rows),
            "all_protocol_metrics_present": all(row["protocol_metrics_present"] for row in rows),
            "all_required_gates_known": all(row["required_gates_known"] for row in rows),
            "claim_status": CLAIM_STATUS,
        },
        "claim_boundary": {
            "metric_definitions_locked": True,
            "pre_human_claimable_metrics": 0,
            "human_gold_or_expert_returns_required": True,
            "safe_interpretation": "Metric implementations, outputs, protocol definitions, and paper-table bindings are traceable; final metric values remain pending human/expert returns.",
            "not_claimable_until": "Human-gold annotation/adjudication or expert/effort returns are imported and post-human scoring is rerun.",
        },
        "metric_rows": rows,
        "csv_rows": [row_to_csv(row) for row in rows],
        "source_artifacts": {
            "post_human_scoring_readiness": rel(release_dir / "post_human_scoring_readiness.json"),
            "evaluation_protocol_lock": rel(release_dir / "evaluation_protocol_lock.json"),
            "paper_table_blueprint": rel(release_dir / "paper_table_blueprint.json"),
            "claim_gate_report": rel(release_dir / "claim_gate_report.json"),
            "eacl_plan_compliance_matrix": rel(release_dir / "eacl_plan_compliance_matrix.json"),
        },
    }
    return payload


def md_value(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, list):
        return ", ".join(f"`{item}`" for item in value)
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
        "# CAPE-KG Metric Traceability Audit",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Plan file: `{payload['plan_file']}`",
        "",
        "This report maps the revised plan's evaluation metrics to evaluator scripts, output files, protocol definitions, claim gates, and paper tables. It is a traceability audit, not final human-gold performance evidence.",
        "",
        "## Claim Boundary",
        "",
        f"- Claim status: `{payload['claim_status']}`",
        "- Metric definitions and implementation paths are traceable.",
        "- Final values remain pending human-gold, expert-review, or active-review effort returns.",
        "",
        "## Summary",
        "",
        md_table(
            ["metric", "value"],
            [{"metric": key, "value": value} for key, value in summary.items()],
        ),
        "",
        "## Metric Rows",
        "",
        md_table(
            [
                "metric_id",
                "metric_name",
                "claim_status",
                "required_gate_ids",
                "protocol_groups",
                "protocol_metrics",
                "paper_tables",
                "evaluator_scripts_present",
                "output_files_present",
                "issue_count",
            ],
            payload["metric_rows"],
        ),
        "",
        "## Source Artifacts",
        "",
    ]
    for label, path in payload["source_artifacts"].items():
        lines.append(f"- `{label}`: `{path}`")
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
    json_path = release_dir / "metric_traceability_audit.json"
    md_path = release_dir / "metric_traceability_audit.md"
    csv_path = release_dir / "metric_traceability_audit.csv"
    write_json(json_path, payload)
    write_text(md_path, build_report(payload))
    write_csv(
        csv_path,
        payload["csv_rows"],
        [
            "metric_id",
            "metric_name",
            "plan_metric",
            "plan_section",
            "claim_status",
            "claimable_now",
            "required_gate_ids",
            "expected_return_files",
            "present_return_files",
            "protocol_groups",
            "protocol_metrics",
            "paper_tables",
            "evaluator_scripts",
            "output_files",
            "evaluator_scripts_present",
            "output_files_present",
            "paper_tables_present",
            "protocol_metrics_present",
            "required_gates_known",
            "issue_count",
            "issues",
        ],
    )
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print(f"Wrote {csv_path}")


if __name__ == "__main__":
    main()
