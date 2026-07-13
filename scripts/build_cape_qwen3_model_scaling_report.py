#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a claim-safe Qwen3 model-scaling report for CAPE-KG."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")

MODEL_SOURCES = [
    {
        "model": "Qwen3-8B",
        "role": "main local paper-package diagnostic",
        "metrics": "04_evaluation/actual_llm_silver_metrics.json",
        "report": "04_evaluation/actual_llm_silver_evaluation_report.md",
        "valid_file": "49_qwen3_8b_strict_json_1200_full_valid.jsonl",
    },
    {
        "model": "Qwen3-14B",
        "role": "stronger local core diagnostic",
        "metrics": "04_evaluation/qwen3_14b_core_silver_metrics.json",
        "report": "04_evaluation/qwen3_14b_core_silver_evaluation_report.md",
        "valid_file": "49_qwen3_14b_core_conditions_120_valid.jsonl",
    },
    {
        "model": "Qwen3-32B-AWQ",
        "role": "largest completed local core diagnostic",
        "metrics": "04_evaluation/qwen3_32b_awq_core_silver_metrics.json",
        "report": "04_evaluation/qwen3_32b_awq_core_silver_evaluation_report.md",
        "valid_file": "49_qwen3_32b_awq_core_120_valid.jsonl",
    },
]

CORE_CONDITIONS = ["B0_plain_llm", "B1_predicate_constrained", "B2_current_project", "P_cape_kg_actual"]
DISPLAY_FIELDS = [
    "rows",
    "pred_edges",
    "edge_exact_f1",
    "predicate_f1",
    "node_label_f1",
    "evidence_f1",
    "parse_or_generation_error_rows",
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


def rel(path):
    return str(Path(path).as_posix())


def file_state(path, role, required=True):
    path = Path(path)
    present = path.exists() and path.is_file()
    return {
        "path": rel(path),
        "role": role,
        "required": bool(required),
        "exists": present,
        "bytes": path.stat().st_size if present else 0,
    }


def row_by_condition(metrics_payload):
    rows = metrics_payload.get("metrics") or []
    return {row.get("condition"): row for row in rows if row.get("condition")}


def f4(value):
    if value is None or value == "":
        return ""
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return str(value)


def table_escape(value):
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def build_payload(exp_dir):
    exp_dir = Path(exp_dir)
    release_dir = exp_dir / "06_release"
    source_files = []
    model_rows = []
    condition_rows = []
    missing_required = []

    for source in MODEL_SOURCES:
        metrics_path = exp_dir / source["metrics"]
        report_path = exp_dir / source["report"]
        valid_path = exp_dir / source["valid_file"]
        source_files.extend(
            [
                file_state(metrics_path, f"{source['model']} metrics"),
                file_state(report_path, f"{source['model']} report"),
                file_state(valid_path, f"{source['model']} validated outputs"),
            ]
        )
        metrics = read_json(metrics_path, {}) or {}
        by_condition = row_by_condition(metrics)
        present_conditions = sorted(set(by_condition) & set(CORE_CONDITIONS))
        proposed = by_condition.get("P_cape_kg_actual") or {}
        model_rows.append(
            {
                "model": source["model"],
                "role": source["role"],
                "metrics_path": rel(metrics_path),
                "report_path": rel(report_path),
                "valid_path": rel(valid_path),
                "core_conditions_present": present_conditions,
                "core_condition_count": len(present_conditions),
                "proposed_rows": proposed.get("rows"),
                "proposed_pred_edges": proposed.get("pred_edges"),
                "proposed_edge_exact_f1": proposed.get("edge_exact_f1"),
                "proposed_predicate_f1": proposed.get("predicate_f1"),
                "proposed_node_label_f1": proposed.get("node_label_f1"),
                "proposed_evidence_f1": proposed.get("evidence_f1"),
                "proposed_parse_or_generation_error_rows": proposed.get("parse_or_generation_error_rows"),
                "claim_status": metrics.get("claim_status", "silver_proxy_not_human_gold"),
            }
        )
        for condition in CORE_CONDITIONS:
            row = dict(by_condition.get(condition) or {})
            condition_rows.append(
                {
                    "model": source["model"],
                    "condition": condition,
                    **{field: row.get(field) for field in DISPLAY_FIELDS},
                    "claim_status": row.get("claim_status") or metrics.get("claim_status", "silver_proxy_not_human_gold"),
                }
            )

    readiness_path = release_dir / "qwen3_32b_awq_readiness.json"
    readiness_md_path = release_dir / "qwen3_32b_awq_readiness.md"
    source_files.append(file_state(readiness_path, "Qwen3-32B-AWQ readiness JSON", required=False))
    source_files.append(file_state(readiness_md_path, "Qwen3-32B-AWQ readiness report", required=False))
    readiness = read_json(readiness_path, {}) or {}
    core_run = readiness.get("qwen3_32b_awq_core_run") or {}

    missing_required = [row["path"] for row in source_files if row["required"] and not row["exists"]]
    by_model = {row["model"]: row for row in model_rows}
    q8 = by_model.get("Qwen3-8B") or {}
    q32 = by_model.get("Qwen3-32B-AWQ") or {}
    deltas_vs_8b = {}
    for field in ["proposed_edge_exact_f1", "proposed_predicate_f1", "proposed_node_label_f1", "proposed_evidence_f1"]:
        if q8.get(field) is not None and q32.get(field) is not None:
            deltas_vs_8b[field] = round(float(q32[field]) - float(q8[field]), 6)

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": rel(exp_dir),
        "summary": {
            "claim_status": (
                "qwen3_model_scaling_diagnostic_ready_not_human_gold"
                if not missing_required
                else "qwen3_model_scaling_missing_required_sources"
            ),
            "models": [row["model"] for row in model_rows],
            "model_count": len(model_rows),
            "core_conditions": CORE_CONDITIONS,
            "missing_required_source_count": len(missing_required),
            "missing_required_sources": missing_required,
            "qwen3_32b_awq_core_run_complete": core_run.get("complete"),
            "qwen3_32b_awq_valid_rows": core_run.get("valid_rows"),
            "qwen3_32b_awq_raw_rows": core_run.get("raw_rows"),
            "qwen3_32b_awq_expected_rows": core_run.get("expected_rows"),
            "qwen3_32b_awq_can_load_native": readiness.get("can_transformers_native_awq"),
            "qwen3_32b_awq_can_download_with_headroom": readiness.get("can_download_awq"),
            "qwen3_32b_awq_recommended_next_action": readiness.get("recommended_next_action"),
            "proposed_metric_delta_qwen3_32b_awq_minus_8b": deltas_vs_8b,
        },
        "source_files": source_files,
        "model_rows": model_rows,
        "condition_rows": condition_rows,
        "interpretation": [
            "All model-scaling scores are silver/proxy diagnostics, not human-gold performance evidence.",
            "Qwen3-32B-AWQ is the largest completed local core run and is already available for B0/B1/B2/P over 120 chunks.",
            "The 32B-AWQ run improves proposed-method silver predicate F1 and exact edge F1 over the 8B core diagnostic, but evidence F1 is lower than the 8B proposed diagnostic; do not overclaim monotonic model scaling.",
            "The next paper-level step is not another automatic GPU run; it is adjudicated human-gold scoring of the existing model outputs.",
        ],
    }


def render_report(payload):
    summary = payload["summary"]
    lines = [
        "# CAPE-KG Qwen3 Model Scaling Report",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Experiment: `{payload['experiment_dir']}`",
        "",
        "This report consolidates the completed Qwen3-8B, Qwen3-14B, and Qwen3-32B-AWQ core diagnostics.",
        "It is explicitly claim-safe: these are silver/proxy diagnostics and must not be presented as final human-gold performance.",
        "",
        "## Summary",
        "",
        f"- Claim status: `{summary['claim_status']}`",
        f"- Models: {', '.join(summary['models'])}",
        f"- Core conditions: {', '.join(summary['core_conditions'])}",
        f"- Qwen3-32B-AWQ core run complete: `{summary.get('qwen3_32b_awq_core_run_complete')}`",
        f"- Qwen3-32B-AWQ raw/valid rows: {summary.get('qwen3_32b_awq_raw_rows')} / {summary.get('qwen3_32b_awq_valid_rows')}",
        f"- Recommended next action: {summary.get('qwen3_32b_awq_recommended_next_action')}",
        "",
        "## Proposed-Method Model Scaling",
        "",
        "| model | role | rows | pred edges | exact F1 | predicate F1 | node F1 | evidence F1 | parse/error rows | claim status |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in payload["model_rows"]:
        lines.append(
            "| {model} | {role} | {rows} | {edges} | {exact} | {predicate} | {node} | {evidence} | {parse} | `{claim}` |".format(
                model=table_escape(row["model"]),
                role=table_escape(row["role"]),
                rows=row.get("proposed_rows", ""),
                edges=row.get("proposed_pred_edges", ""),
                exact=f4(row.get("proposed_edge_exact_f1")),
                predicate=f4(row.get("proposed_predicate_f1")),
                node=f4(row.get("proposed_node_label_f1")),
                evidence=f4(row.get("proposed_evidence_f1")),
                parse=row.get("proposed_parse_or_generation_error_rows", ""),
                claim=table_escape(row.get("claim_status", "")),
            )
        )

    lines += [
        "",
        "## Core Condition Matrix",
        "",
        "| model | condition | rows | pred edges | exact F1 | predicate F1 | node F1 | evidence F1 | parse/error rows |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["condition_rows"]:
        lines.append(
            "| {model} | `{condition}` | {rows} | {edges} | {exact} | {predicate} | {node} | {evidence} | {parse} |".format(
                model=table_escape(row["model"]),
                condition=table_escape(row["condition"]),
                rows=row.get("rows", ""),
                edges=row.get("pred_edges", ""),
                exact=f4(row.get("edge_exact_f1")),
                predicate=f4(row.get("predicate_f1")),
                node=f4(row.get("node_label_f1")),
                evidence=f4(row.get("evidence_f1")),
                parse=row.get("parse_or_generation_error_rows", ""),
            )
        )

    lines += ["", "## Interpretation", ""]
    for item in payload["interpretation"]:
        lines.append(f"- {item}")

    lines += [
        "",
        "## Source Files",
        "",
        "| role | path | exists | bytes |",
        "| --- | --- | ---: | ---: |",
    ]
    for row in payload["source_files"]:
        lines.append(f"| {table_escape(row['role'])} | `{row['path']}` | {row['exists']} | {row['bytes']} |")
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    args = parser.parse_args()

    payload = build_payload(Path(args.experiment_dir))
    release_dir = Path(args.experiment_dir) / "06_release"
    json_path = release_dir / "qwen3_model_scaling_report.json"
    md_path = release_dir / "qwen3_model_scaling_report.md"
    write_json(json_path, payload)
    write_text(md_path, render_report(payload))
    print(
        json.dumps(
            {
                "json": str(json_path),
                "markdown": str(md_path),
                "claim_status": payload["summary"]["claim_status"],
                "missing_required_sources": payload["summary"]["missing_required_sources"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
