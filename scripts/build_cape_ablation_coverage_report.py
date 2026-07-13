#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a claim-safe coverage report for CAPE-KG ablation experiments."""

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_OUTPUTS_DIR = Path("outputs")
CLAIM_STATUS = "ablation_coverage_ready_silver_diagnostic_not_human_gold"

BASELINE_CONDITIONS = [
    "B0_plain_llm",
    "B1_predicate_constrained",
    "B2_current_project",
    "B3_edc_style",
    "B4_taxonomy_rag",
    "B5_procedural_prompt",
    "B6_sac_kg_verifier_pruner",
]

LLM_ABLATIONS = [
    {
        "condition": "P_minus_CQ",
        "component_removed": "Competency-question anchoring",
        "plan_expected_effect": "CQ answerability and schema-control signals should weaken.",
        "output_shape_expected": ["nodes", "edges", "mappings"],
    },
    {
        "condition": "P_minus_Evidence",
        "component_removed": "Evidence grounding requirement",
        "plan_expected_effect": "Unsupported or weakly grounded outputs should increase.",
        "output_shape_expected": ["nodes", "edges", "mappings"],
    },
    {
        "condition": "P_minus_Procedural_schema",
        "component_removed": "Procedural schema constraints",
        "plan_expected_effect": "Gateway, condition, artifact-flow, and procedural-consistency signals should weaken.",
        "output_shape_expected": ["nodes", "edges", "mappings"],
    },
    {
        "condition": "P_minus_Schema_retrieval",
        "component_removed": "Chunk-specific CQ/schema/taxonomy retrieval",
        "plan_expected_effect": "Schema-control and context-selection effects are isolated.",
        "output_shape_expected": ["nodes", "edges", "mappings"],
    },
    {
        "condition": "P_minus_Standard_bridge",
        "component_removed": "NCS/PCF standard bridge output",
        "plan_expected_effect": "Mapping output should be removed while node/edge extraction remains.",
        "output_shape_expected": ["nodes", "edges"],
    },
    {
        "condition": "P_minus_Validator",
        "component_removed": "Validator rejection/pruning",
        "plan_expected_effect": "Schema-conformance errors and noisy candidates should be less filtered.",
        "output_shape_expected": ["nodes", "edges", "mappings"],
    },
]


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


def as_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return default


def as_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def fmt(value):
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return f"{value:.6f}"
    if isinstance(value, list):
        return ", ".join(f"`{item}`" for item in value)
    if value is None:
        return ""
    return str(value)


def md_table(headers, rows):
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(header, "")) for header in headers) + " |")
    return "\n".join(lines)


def condition_output_lookup(traceability):
    rows = ((traceability.get("llm_condition_outputs") or {}).get("conditions") or [])
    return {row.get("condition"): row for row in rows}


def prompt_lookup(traceability):
    rows = traceability.get("prompt_inventory") or []
    return {row.get("condition"): row for row in rows}


def metric_lookup(metrics_payload):
    rows = metrics_payload.get("metrics") or []
    return {row.get("condition"): row for row in rows}


def build_llm_ablation_rows(traceability, metrics_payload, statistical_payload):
    output_by_condition = condition_output_lookup(traceability)
    prompt_by_condition = prompt_lookup(traceability)
    metric_by_condition = metric_lookup(metrics_payload)
    comparison_conditions = set(statistical_payload.get("comparison_conditions") or [])
    rows = []
    for spec in LLM_ABLATIONS:
        condition = spec["condition"]
        output = output_by_condition.get(condition) or {}
        prompt = prompt_by_condition.get(condition) or {}
        metrics = metric_by_condition.get(condition) or {}
        output_keys = prompt.get("expected_output_keys") or []
        rows.append(
            {
                "ablation_family": "llm_component_ablation",
                "condition": condition,
                "component_removed": spec["component_removed"],
                "plan_expected_effect": spec["plan_expected_effect"],
                "output_shape_expected": ",".join(spec["output_shape_expected"]),
                "output_shape_actual": ",".join(output_keys),
                "valid_rows_traceability": as_int(output.get("valid_rows")),
                "traceability_nodes": as_int(output.get("nodes")),
                "traceability_edges": as_int(output.get("edges")),
                "traceability_mappings": as_int(output.get("mappings")),
                "metric_rows": as_int(metrics.get("rows")),
                "pred_nodes": as_int(metrics.get("pred_nodes")),
                "pred_edges": as_int(metrics.get("pred_edges")),
                "pred_mappings": as_int(metrics.get("pred_mappings")),
                "edge_exact_f1": round(as_float(metrics.get("edge_exact_f1")), 6),
                "predicate_f1": round(as_float(metrics.get("predicate_f1")), 6),
                "node_label_f1": round(as_float(metrics.get("node_label_f1")), 6),
                "evidence_f1": round(as_float(metrics.get("evidence_f1")), 6),
                "schema_edge_rate": round(as_float(metrics.get("schema_edge_rate")), 6),
                "mapping_evidence_attachment_rate": round(as_float(metrics.get("mapping_evidence_attachment_rate")), 6),
                "statistical_comparison_present": condition in comparison_conditions,
                "source_file": metrics.get("source_file") or ",".join(output.get("source_files") or []),
                "claim_status": metrics.get("claim_status") or "missing_metric_row",
            }
        )
    return rows


def build_baseline_rows(traceability, metrics_payload):
    output_by_condition = condition_output_lookup(traceability)
    metric_by_condition = metric_lookup(metrics_payload)
    rows = []
    for condition in BASELINE_CONDITIONS:
        output = output_by_condition.get(condition) or {}
        metrics = metric_by_condition.get(condition) or {}
        rows.append(
            {
                "condition": condition,
                "valid_rows_traceability": as_int(output.get("valid_rows")),
                "metric_rows": as_int(metrics.get("rows")),
                "pred_nodes": as_int(metrics.get("pred_nodes")),
                "pred_edges": as_int(metrics.get("pred_edges")),
                "pred_mappings": as_int(metrics.get("pred_mappings")),
                "edge_exact_f1": round(as_float(metrics.get("edge_exact_f1")), 6),
                "predicate_f1": round(as_float(metrics.get("predicate_f1")), 6),
                "node_label_f1": round(as_float(metrics.get("node_label_f1")), 6),
                "evidence_f1": round(as_float(metrics.get("evidence_f1")), 6),
                "claim_status": metrics.get("claim_status") or "missing_metric_row",
            }
        )
    return rows


def build_active_review_rows(active_payload):
    rows = []
    for row in active_payload.get("rows") or []:
        condition = row.get("condition") or ""
        if not condition.startswith("P_minus_Active_review") and condition != "P_cape_kg_actual_with_active_review":
            continue
        rows.append(
            {
                "ablation_family": "active_review_effort_diagnostic",
                "condition": condition,
                "component_removed": "Active review prioritization" if condition.startswith("P_minus_Active_review") else "none",
                "strategy": row.get("strategy"),
                "target_label": row.get("target_label"),
                "budget": as_int(row.get("budget")),
                "reviewed": as_int(row.get("reviewed")),
                "errors_found": round(as_float(row.get("errors_found")), 6),
                "error_precision_at_k": round(as_float(row.get("error_precision_at_k")), 6),
                "error_recall_at_k": round(as_float(row.get("error_recall_at_k")), 6),
                "lift_vs_random_expected": round(as_float(row.get("lift_vs_random_expected")), 6),
                "claim_status": row.get("claim_status"),
            }
        )
    return rows


def summarize_active_review(rows):
    conditions = sorted({row["condition"] for row in rows})
    minus_conditions = sorted(condition for condition in conditions if condition.startswith("P_minus_Active_review"))
    budgets = sorted({row["budget"] for row in rows})
    return {
        "active_review_ablation_condition_count": len(minus_conditions),
        "active_review_ablation_conditions": minus_conditions,
        "active_review_diagnostic_row_count": len(rows),
        "active_review_budgets": budgets,
        "active_review_claim_statuses": sorted({row.get("claim_status") for row in rows if row.get("claim_status")}),
    }


def build_payload(exp_dir, outputs_dir):
    exp_dir = Path(exp_dir)
    outputs_dir = Path(outputs_dir)
    release_dir = exp_dir / "06_release"
    evaluation_dir = exp_dir / "04_evaluation"

    traceability_path = release_dir / "prompt_node_edge_traceability.json"
    metrics_path = evaluation_dir / "actual_llm_silver_metrics.json"
    statistical_path = evaluation_dir / "statistical_analysis_metrics.json"
    active_path = evaluation_dir / "active_review_ablation_metrics.json"
    schema_retrieval_path = release_dir / "schema_retrieval_coverage_report.json"

    traceability = read_json(traceability_path, {}) or {}
    metrics_payload = read_json(metrics_path, {}) or {}
    statistical_payload = read_json(statistical_path, {}) or {}
    active_payload = read_json(active_path, {}) or {}

    baseline_rows = build_baseline_rows(traceability, metrics_payload)
    llm_ablation_rows = build_llm_ablation_rows(traceability, metrics_payload, statistical_payload)
    active_review_rows = build_active_review_rows(active_payload)
    active_summary = summarize_active_review(active_review_rows)

    completed_llm = [
        row for row in llm_ablation_rows
        if row["valid_rows_traceability"] >= 100
        and row["metric_rows"] >= 100
        and row["claim_status"] == "silver_proxy_not_human_gold"
    ]
    baseline_ready = [
        row for row in baseline_rows
        if row["valid_rows_traceability"] >= 100
        and row["metric_rows"] >= 100
        and row["claim_status"] == "silver_proxy_not_human_gold"
    ]
    active_claim_statuses = set(active_summary["active_review_claim_statuses"])
    active_ready = (
        active_summary["active_review_ablation_condition_count"] >= 2
        and active_summary["active_review_diagnostic_row_count"] >= 6
        and active_claim_statuses == {"silver_proxy_ablation_not_human_efficiency"}
    )

    all_rows = []
    for row in llm_ablation_rows:
        all_rows.append(dict(row))
    for row in active_review_rows:
        all_rows.append(dict(row))

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": rel(exp_dir),
        "outputs_dir": rel(outputs_dir),
        "claim_status": CLAIM_STATUS,
        "claim_boundary": {
            "silver_diagnostic_only": True,
            "not_human_gold_performance_evidence": True,
            "safe_interpretation": (
                "This report proves that planned baseline/ablation conditions were generated and evaluated "
                "with silver/proxy diagnostics. It does not prove final superiority or human-gold performance."
            ),
            "not_claimable_until": (
                "adjudicated human-gold labels, IAA, proposed-vs-ablation human-gold scoring, "
                "and active-review human effort returns are imported."
            ),
        },
        "plan_requirements": {
            "minimum_baseline_conditions_required": 3,
            "minimum_ablation_conditions_required": 3,
            "planned_llm_ablation_conditions": [row["condition"] for row in LLM_ABLATIONS],
            "planned_active_review_ablation": True,
        },
        "summary": {
            "baseline_condition_count": len(baseline_rows),
            "baseline_ready_condition_count": len(baseline_ready),
            "planned_llm_ablation_count": len(LLM_ABLATIONS),
            "completed_llm_ablation_count": len(completed_llm),
            "llm_ablation_rows_all_120": len(completed_llm) == len(LLM_ABLATIONS),
            "statistical_comparison_ablation_count": sum(1 for row in llm_ablation_rows if row["statistical_comparison_present"]),
            "active_review_ablation_present": active_ready,
            "active_review_ablation_condition_count": active_summary["active_review_ablation_condition_count"],
            "active_review_diagnostic_row_count": active_summary["active_review_diagnostic_row_count"],
            "minimum_baseline_requirement_satisfied": len(baseline_ready) >= 3,
            "minimum_ablation_requirement_satisfied": len(completed_llm) >= 3,
            "claim_status": CLAIM_STATUS,
        },
        "baseline_rows": baseline_rows,
        "llm_ablation_rows": llm_ablation_rows,
        "active_review_ablation_summary": active_summary,
        "active_review_ablation_rows": active_review_rows,
        "ablation_rows": all_rows,
        "input_files": {
            "prompt_node_edge_traceability": rel(traceability_path),
            "actual_llm_silver_metrics": rel(metrics_path),
            "statistical_analysis_metrics": rel(statistical_path),
            "active_review_ablation_metrics": rel(active_path),
            "schema_retrieval_coverage_report": rel(schema_retrieval_path),
        },
        "outputs": {
            "json": rel(release_dir / "ablation_coverage_report.json"),
            "markdown": rel(release_dir / "ablation_coverage_report.md"),
            "csv": rel(evaluation_dir / "ablation_coverage_by_condition.csv"),
        },
    }


def render_markdown(payload):
    summary = payload["summary"]
    boundary = payload["claim_boundary"]
    llm_rows = [
        {
            "condition": row["condition"],
            "removed": row["component_removed"],
            "valid_rows": row["valid_rows_traceability"],
            "metric_rows": row["metric_rows"],
            "nodes": row["traceability_nodes"],
            "edges": row["traceability_edges"],
            "mappings": row["traceability_mappings"],
            "edge_f1": row["edge_exact_f1"],
            "predicate_f1": row["predicate_f1"],
            "evidence_f1": row["evidence_f1"],
            "stat_test": row["statistical_comparison_present"],
        }
        for row in payload["llm_ablation_rows"]
    ]
    baseline_rows = [
        {
            "condition": row["condition"],
            "valid_rows": row["valid_rows_traceability"],
            "metric_rows": row["metric_rows"],
            "edge_f1": row["edge_exact_f1"],
            "predicate_f1": row["predicate_f1"],
            "node_f1": row["node_label_f1"],
            "evidence_f1": row["evidence_f1"],
        }
        for row in payload["baseline_rows"]
    ]
    active_rows = [
        {
            "condition": row["condition"],
            "strategy": row["strategy"],
            "budget": row["budget"],
            "reviewed": row["reviewed"],
            "errors_found": row["errors_found"],
            "precision": row["error_precision_at_k"],
            "recall": row["error_recall_at_k"],
            "lift": row["lift_vs_random_expected"],
        }
        for row in payload["active_review_ablation_rows"]
    ]
    lines = [
        "# CAPE-KG Ablation Coverage Report",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Claim status: `{payload['claim_status']}`",
        "",
        "## Purpose",
        "",
        "이 문서는 revised plan에서 요구한 baseline/ablation 실험이 현재 산출물에서 어떤 조건과 파일로 구현되었는지 확인하는 release artifact입니다.",
        "",
        "## Claim Boundary",
        "",
        f"- Silver diagnostic only: {boundary['silver_diagnostic_only']}",
        f"- Not human-gold performance evidence: {boundary['not_human_gold_performance_evidence']}",
        f"- Safe interpretation: {boundary['safe_interpretation']}",
        f"- Not claimable until: {boundary['not_claimable_until']}",
        "",
        "## Coverage Summary",
        "",
        md_table(
            ["item", "value"],
            [
                {"item": "Baseline conditions", "value": summary["baseline_condition_count"]},
                {"item": "Baseline ready conditions", "value": summary["baseline_ready_condition_count"]},
                {"item": "Planned LLM ablations", "value": summary["planned_llm_ablation_count"]},
                {"item": "Completed LLM ablations", "value": summary["completed_llm_ablation_count"]},
                {"item": "LLM ablation rows all >=100", "value": summary["llm_ablation_rows_all_120"]},
                {"item": "Statistical comparison ablations", "value": summary["statistical_comparison_ablation_count"]},
                {"item": "Active-review ablation present", "value": summary["active_review_ablation_present"]},
                {"item": "Active-review diagnostic rows", "value": summary["active_review_diagnostic_row_count"]},
                {"item": "Minimum baseline requirement satisfied", "value": summary["minimum_baseline_requirement_satisfied"]},
                {"item": "Minimum ablation requirement satisfied", "value": summary["minimum_ablation_requirement_satisfied"]},
            ],
        ),
        "",
        "## Baseline Coverage",
        "",
        md_table(["condition", "valid_rows", "metric_rows", "edge_f1", "predicate_f1", "node_f1", "evidence_f1"], baseline_rows),
        "",
        "## LLM Component Ablations",
        "",
        md_table(["condition", "removed", "valid_rows", "metric_rows", "nodes", "edges", "mappings", "edge_f1", "predicate_f1", "evidence_f1", "stat_test"], llm_rows),
        "",
        "## Active-Review Ablation Diagnostic",
        "",
        "Active-review rows are review-priority diagnostics only. They do not claim human review efficiency until timing/correction returns are imported.",
        "",
        md_table(["condition", "strategy", "budget", "reviewed", "errors_found", "precision", "recall", "lift"], active_rows),
        "",
        "## Input Files",
        "",
    ]
    lines += [f"- {key}: `{value}`" for key, value in payload["input_files"].items()]
    lines += [
        "",
        "## Output Files",
        "",
        f"- JSON: `{payload['outputs']['json']}`",
        f"- Markdown: `{payload['outputs']['markdown']}`",
        f"- CSV: `{payload['outputs']['csv']}`",
        "",
    ]
    return "\n".join(lines)


def run(args):
    payload = build_payload(args.experiment_dir, args.outputs_dir)
    release_dir = Path(args.experiment_dir) / "06_release"
    evaluation_dir = Path(args.experiment_dir) / "04_evaluation"
    json_path = release_dir / "ablation_coverage_report.json"
    md_path = release_dir / "ablation_coverage_report.md"
    csv_path = evaluation_dir / "ablation_coverage_by_condition.csv"
    write_json(json_path, payload)
    write_text(md_path, render_markdown(payload))
    write_csv(
        csv_path,
        payload["ablation_rows"],
        [
            "ablation_family",
            "condition",
            "component_removed",
            "plan_expected_effect",
            "output_shape_expected",
            "output_shape_actual",
            "valid_rows_traceability",
            "traceability_nodes",
            "traceability_edges",
            "traceability_mappings",
            "metric_rows",
            "pred_nodes",
            "pred_edges",
            "pred_mappings",
            "edge_exact_f1",
            "predicate_f1",
            "node_label_f1",
            "evidence_f1",
            "schema_edge_rate",
            "mapping_evidence_attachment_rate",
            "statistical_comparison_present",
            "source_file",
            "strategy",
            "target_label",
            "budget",
            "reviewed",
            "errors_found",
            "error_precision_at_k",
            "error_recall_at_k",
            "lift_vs_random_expected",
            "claim_status",
        ],
    )
    print(
        json.dumps(
            {
                "json": rel(json_path),
                "markdown": rel(md_path),
                "csv": rel(csv_path),
                "claim_status": payload["claim_status"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--outputs-dir", default=str(DEFAULT_OUTPUTS_DIR))
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
