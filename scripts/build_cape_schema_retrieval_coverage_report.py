#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a claim-safe coverage report for CQ-linked schema retrieval."""

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_OUTPUTS_DIR = Path("outputs")
FOCUS_CONDITIONS = [
    "P_cape_kg_actual",
    "P_minus_Schema_retrieval",
    "B4_taxonomy_rag",
]
EXPECTED_CQ_COUNT = 12
EXPECTED_SCHEMA_RETRIEVAL_STATUS = "schema_retrieval_coverage_ready_silver_diagnostic_not_human_gold"


CONDITION_POLICY = {
    "P_cape_kg_actual": {
        "condition_role": "proposed",
        "uses_cq_anchor": True,
        "uses_chunk_specific_schema_retrieval": True,
        "uses_taxonomy_snippets": True,
        "uses_full_schema_list": True,
        "keeps_evidence_grounding": True,
        "keeps_validator": True,
        "keeps_mapping_output_shape": True,
        "interpretation": "Full CAPE-KG condition: CQ anchoring plus chunk-specific schema/taxonomy context.",
    },
    "P_minus_Schema_retrieval": {
        "condition_role": "ablation",
        "uses_cq_anchor": True,
        "uses_chunk_specific_schema_retrieval": False,
        "uses_taxonomy_snippets": False,
        "uses_full_schema_list": True,
        "keeps_evidence_grounding": True,
        "keeps_validator": True,
        "keeps_mapping_output_shape": True,
        "interpretation": "Ablation that keeps the output contract but removes chunk-specific schema/taxonomy retrieval.",
    },
    "B4_taxonomy_rag": {
        "condition_role": "baseline",
        "uses_cq_anchor": False,
        "uses_chunk_specific_schema_retrieval": True,
        "uses_taxonomy_snippets": True,
        "uses_full_schema_list": False,
        "keeps_evidence_grounding": True,
        "keeps_validator": False,
        "keeps_mapping_output_shape": True,
        "interpretation": "Taxonomy/RAG baseline without the full CQ-anchored CAPE control stack.",
    },
}


CQ_FALLBACK_SUPPORT = {
    "CQ10": "evidence_anchored_items",
    "CQ11": "ncs_mapping_items",
    "CQ12": "pcf_mapping_items",
}


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path):
    path = Path(path)
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


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


def round6(value):
    return round(float(value), 6)


def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return default


def md_value(value):
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
        lines.append("| " + " | ".join(md_value(row.get(header, "")) for header in headers) + " |")
    return "\n".join(lines)


def prompt_rows(traceability):
    inventory = traceability.get("prompt_inventory") or []
    by_condition = {row.get("condition"): row for row in inventory}
    rows = []
    for condition in FOCUS_CONDITIONS:
        policy = dict(CONDITION_POLICY[condition])
        prompt = by_condition.get(condition) or {}
        rows.append(
            {
                "condition": condition,
                "condition_role": policy["condition_role"],
                "uses_cq_anchor": policy["uses_cq_anchor"],
                "uses_chunk_specific_schema_retrieval": policy["uses_chunk_specific_schema_retrieval"],
                "uses_taxonomy_snippets": policy["uses_taxonomy_snippets"],
                "uses_full_schema_list": policy["uses_full_schema_list"],
                "keeps_evidence_grounding": policy["keeps_evidence_grounding"],
                "keeps_validator": policy["keeps_validator"],
                "keeps_mapping_output_shape": policy["keeps_mapping_output_shape"],
                "expected_output_keys": prompt.get("expected_output_keys") or [],
                "prompt_file": prompt.get("prompt_file") or "",
                "prompt_text": prompt.get("prompt_text") or "",
                "interpretation": policy["interpretation"],
            }
        )
    return rows


def output_rows(traceability):
    condition_rows = ((traceability.get("llm_condition_outputs") or {}).get("conditions") or [])
    by_condition = {row.get("condition"): row for row in condition_rows}
    rows = []
    for condition in FOCUS_CONDITIONS:
        row = by_condition.get(condition) or {}
        rows.append(
            {
                "condition": condition,
                "valid_rows": safe_int(row.get("valid_rows")),
                "triples": safe_int(row.get("triples")),
                "nodes": safe_int(row.get("nodes")),
                "edges": safe_int(row.get("edges")),
                "mappings": safe_int(row.get("mappings")),
                "source_files": row.get("source_files") or [],
            }
        )
    return rows


def metric_rows(exp_dir):
    metrics_payload = read_json(Path(exp_dir) / "04_evaluation/actual_llm_silver_metrics.json", {}) or {}
    rows = []
    for row in metrics_payload.get("metrics") or []:
        condition = row.get("condition")
        if condition not in FOCUS_CONDITIONS:
            continue
        rows.append(
            {
                "condition": condition,
                "source_file": row.get("source_file"),
                "rows": safe_int(row.get("rows")),
                "raw_rows": safe_int(row.get("raw_rows")),
                "parse_or_generation_error_rows": safe_int(row.get("parse_or_generation_error_rows")),
                "pred_nodes": safe_int(row.get("pred_nodes")),
                "pred_edges": safe_int(row.get("pred_edges")),
                "pred_mappings": safe_int(row.get("pred_mappings")),
                "edge_exact_f1": safe_float(row.get("edge_exact_f1")),
                "predicate_f1": safe_float(row.get("predicate_f1")),
                "node_label_f1": safe_float(row.get("node_label_f1")),
                "evidence_f1": safe_float(row.get("evidence_f1")),
                "schema_edge_rate": safe_float(row.get("schema_edge_rate")),
                "mapping_evidence_attachment_rate": safe_float(row.get("mapping_evidence_attachment_rate")),
                "claim_status": row.get("claim_status"),
            }
        )
    return rows


def valid_output_files(traceability):
    summary = traceability.get("llm_condition_outputs") or {}
    values = summary.get("valid_files") or [summary.get("valid_file")]
    return [Path(value) for value in values if value]


def collect_valid_rows(traceability):
    rows_by_condition = defaultdict(list)
    for path in valid_output_files(traceability):
        for row in read_jsonl(path):
            condition = row.get("condition")
            if condition in FOCUS_CONDITIONS:
                copied = dict(row)
                copied["_source_file"] = rel(path)
                rows_by_condition[condition].append(copied)
    return rows_by_condition


def has_evidence(item):
    return bool(item.get("evidence_anchor_ids") or item.get("evidence_sentence_ids") or item.get("evidence"))


def mapping_standard(item):
    return str(item.get("standard") or item.get("target_standard") or "").upper()


def support_count_for_cq(condition_rows, cq):
    cq_id = cq.get("cq_id")
    predicates = set(cq.get("target_predicates") or [])
    count = 0
    chunk_ids = set()
    evidence_items = 0
    for row in condition_rows:
        chunk_id = row.get("chunk_id")
        nodes = row.get("nodes") if isinstance(row.get("nodes"), list) else []
        edges = row.get("edges") if isinstance(row.get("edges"), list) else []
        mappings = row.get("mappings") if isinstance(row.get("mappings"), list) else []
        if cq_id == "CQ10":
            local = sum(1 for item in nodes + edges + mappings if has_evidence(item))
        elif cq_id == "CQ11":
            local = sum(1 for item in mappings if mapping_standard(item) == "NCS")
            local += sum(1 for item in edges if item.get("predicate") in predicates)
        elif cq_id == "CQ12":
            local = sum(1 for item in mappings if mapping_standard(item) == "PCF")
            local += sum(1 for item in edges if item.get("predicate") in predicates)
        else:
            local = sum(1 for item in edges if item.get("predicate") in predicates)
        if local:
            count += local
            chunk_ids.add(chunk_id)
        evidence_items += sum(1 for item in nodes + edges + mappings if has_evidence(item))
    return {
        "support_count": count,
        "supporting_chunks": len(chunk_ids),
        "support_proxy": CQ_FALLBACK_SUPPORT.get(cq_id, "edge_predicate_match"),
        "evidence_anchored_items_in_condition": evidence_items,
    }


def build_cq_support_rows(cqs, rows_by_condition):
    rows = []
    for condition in FOCUS_CONDITIONS:
        condition_rows = rows_by_condition.get(condition) or []
        for cq in cqs:
            support = support_count_for_cq(condition_rows, cq)
            rows.append(
                {
                    "condition": condition,
                    "cq_id": cq.get("cq_id"),
                    "question": cq.get("question"),
                    "target_predicates": ",".join(cq.get("target_predicates") or []),
                    "support_count": support["support_count"],
                    "supporting_chunks": support["supporting_chunks"],
                    "support_proxy": support["support_proxy"],
                    "evidence_anchored_items_in_condition": support["evidence_anchored_items_in_condition"],
                    "claim_status": "cq_support_proxy_not_human_gold_answerability",
                }
            )
    return rows


def summarize_cq_support(cq_support_rows):
    by_condition = defaultdict(list)
    for row in cq_support_rows:
        by_condition[row["condition"]].append(row)
    rows = []
    for condition in FOCUS_CONDITIONS:
        items = by_condition.get(condition) or []
        support_total = sum(safe_int(row.get("support_count")) for row in items)
        supported_cqs = sum(1 for row in items if safe_int(row.get("support_count")) > 0)
        supporting_chunks_total = sum(safe_int(row.get("supporting_chunks")) for row in items)
        rows.append(
            {
                "condition": condition,
                "cq_count": len(items),
                "supported_cq_count": supported_cqs,
                "unsupported_cq_count": len(items) - supported_cqs,
                "support_count_total": support_total,
                "supporting_chunks_total": supporting_chunks_total,
                "claim_status": "cq_support_proxy_not_human_gold_answerability",
            }
        )
    return rows


def delta_rows(left_rows, right_rows, left_condition, right_condition, fields):
    left = {row.get("condition"): row for row in left_rows}.get(left_condition) or {}
    right = {row.get("condition"): row for row in right_rows}.get(right_condition) or {}
    rows = []
    for field in fields:
        left_value = safe_float(left.get(field))
        right_value = safe_float(right.get(field))
        rows.append(
            {
                "metric": field,
                "left_condition": left_condition,
                "left_value": round6(left_value),
                "right_condition": right_condition,
                "right_value": round6(right_value),
                "delta_left_minus_right": round6(left_value - right_value),
            }
        )
    return rows


def schema_summary(schema):
    return {
        "node_type_count": len(schema.get("node_types") or []),
        "edge_type_count": len(schema.get("edge_types") or []),
        "domain_range_count": len(schema.get("domain_range") or {}),
        "evidence_span_required": bool(schema.get("evidence_span_required")),
        "node_types": schema.get("node_types") or [],
        "edge_types": schema.get("edge_types") or [],
    }


def build_payload(exp_dir, outputs_dir):
    exp_dir = Path(exp_dir)
    outputs_dir = Path(outputs_dir)
    release_dir = exp_dir / "06_release"
    evaluation_dir = exp_dir / "04_evaluation"

    traceability_path = release_dir / "prompt_node_edge_traceability.json"
    cqs_path = exp_dir / "02_schema/competency_questions.json"
    schema_path = exp_dir / "02_schema/cape_schema.json"
    silver_metrics_path = evaluation_dir / "actual_llm_silver_metrics.json"
    cq_support_csv = evaluation_dir / "schema_retrieval_cq_support_by_condition.csv"

    traceability = read_json(traceability_path, {}) or {}
    cqs = read_json(cqs_path, []) or []
    schema = read_json(schema_path, {}) or {}

    condition_prompts = prompt_rows(traceability)
    condition_outputs = output_rows(traceability)
    condition_metrics = metric_rows(exp_dir)
    rows_by_condition = collect_valid_rows(traceability)
    cq_support = build_cq_support_rows(cqs, rows_by_condition)
    cq_support_summary = summarize_cq_support(cq_support)

    output_deltas = delta_rows(
        condition_outputs,
        condition_outputs,
        "P_cape_kg_actual",
        "P_minus_Schema_retrieval",
        ["valid_rows", "nodes", "edges", "mappings"],
    )
    silver_metric_deltas = delta_rows(
        condition_metrics,
        condition_metrics,
        "P_cape_kg_actual",
        "P_minus_Schema_retrieval",
        [
            "pred_nodes",
            "pred_edges",
            "pred_mappings",
            "edge_exact_f1",
            "predicate_f1",
            "node_label_f1",
            "evidence_f1",
            "schema_edge_rate",
            "mapping_evidence_attachment_rate",
        ],
    )
    cq_support_deltas = delta_rows(
        cq_support_summary,
        cq_support_summary,
        "P_cape_kg_actual",
        "P_minus_Schema_retrieval",
        ["supported_cq_count", "support_count_total", "supporting_chunks_total"],
    )

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": rel(exp_dir),
        "outputs_dir": rel(outputs_dir),
        "method_module": {
            "module_id": "M3",
            "name": "CQ-linked schema retrieval",
            "purpose": "Verify that the proposed condition uses CQ-linked chunk-specific schema/taxonomy context and that the schema-retrieval ablation removes only that component while preserving the output shape.",
        },
        "claim_status": EXPECTED_SCHEMA_RETRIEVAL_STATUS,
        "claim_boundary": {
            "silver_diagnostic_only": True,
            "not_human_gold_performance_evidence": True,
            "safe_interpretation": "This report checks method coverage, output shape, and silver proxy diagnostics for schema retrieval. It does not claim final precision, recall, F1, or human-gold CQ answerability.",
            "not_claimable_until": "adjudicated human-gold annotations, IAA, and human-gold scoring are imported for the proposed and ablation conditions.",
        },
        "schema_summary": schema_summary(schema),
        "competency_question_summary": {
            "cq_count": len(cqs),
            "source_file": rel(cqs_path),
            "all_cqs_have_target_predicates": all(bool(row.get("target_predicates")) for row in cqs),
        },
        "condition_prompt_policy": condition_prompts,
        "condition_output_summary": condition_outputs,
        "condition_silver_metrics": condition_metrics,
        "cq_support_summary": cq_support_summary,
        "cq_support_rows": cq_support,
        "diagnostic_deltas": {
            "output_quantity_P_minus_schema_retrieval": output_deltas,
            "silver_metrics_P_minus_schema_retrieval": silver_metric_deltas,
            "cq_support_P_minus_schema_retrieval": cq_support_deltas,
            "interpretation": "Positive and negative deltas are diagnostics only; the current silver proxy is not an adjudicated performance table.",
        },
        "input_files": {
            "prompt_node_edge_traceability": rel(traceability_path),
            "competency_questions": rel(cqs_path),
            "cape_schema": rel(schema_path),
            "actual_llm_silver_metrics": rel(silver_metrics_path),
            "valid_output_files": [rel(path) for path in valid_output_files(traceability)],
        },
        "outputs": {
            "json": rel(release_dir / "schema_retrieval_coverage_report.json"),
            "markdown": rel(release_dir / "schema_retrieval_coverage_report.md"),
            "cq_support_csv": rel(cq_support_csv),
        },
    }


def render_markdown(payload):
    prompt_rows_md = [
        {
            "condition": row["condition"],
            "role": row["condition_role"],
            "CQ": row["uses_cq_anchor"],
            "chunk_schema": row["uses_chunk_specific_schema_retrieval"],
            "taxonomy": row["uses_taxonomy_snippets"],
            "full_schema": row["uses_full_schema_list"],
            "validator": row["keeps_validator"],
            "output": row["expected_output_keys"],
            "prompt_file": f"`{row['prompt_file']}`" if row["prompt_file"] else "",
        }
        for row in payload["condition_prompt_policy"]
    ]
    output_rows_md = [
        {
            "condition": row["condition"],
            "valid_rows": row["valid_rows"],
            "nodes": row["nodes"],
            "edges": row["edges"],
            "mappings": row["mappings"],
        }
        for row in payload["condition_output_summary"]
    ]
    metric_rows_md = [
        {
            "condition": row["condition"],
            "source_file": row["source_file"],
            "pred_nodes": row["pred_nodes"],
            "pred_edges": row["pred_edges"],
            "pred_mappings": row["pred_mappings"],
            "edge_exact_f1": row["edge_exact_f1"],
            "predicate_f1": row["predicate_f1"],
            "node_label_f1": row["node_label_f1"],
            "evidence_f1": row["evidence_f1"],
        }
        for row in payload["condition_silver_metrics"]
    ]
    cq_summary_md = [
        {
            "condition": row["condition"],
            "cq_count": row["cq_count"],
            "supported_cq_count": row["supported_cq_count"],
            "unsupported_cq_count": row["unsupported_cq_count"],
            "support_count_total": row["support_count_total"],
            "supporting_chunks_total": row["supporting_chunks_total"],
        }
        for row in payload["cq_support_summary"]
    ]
    delta_md = payload["diagnostic_deltas"]["silver_metrics_P_minus_schema_retrieval"]
    schema = payload["schema_summary"]
    cq = payload["competency_question_summary"]
    boundary = payload["claim_boundary"]

    lines = [
        "# CAPE-KG CQ-Linked Schema Retrieval Coverage",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Claim status: `{payload['claim_status']}`",
        "",
        "## Purpose",
        "",
        "이 문서는 revised plan의 M3 `CQ-linked schema retrieval`가 실험 산출물 안에서 어떻게 구현/제거/비교되었는지를 독립적으로 점검하는 release artifact입니다.",
        "",
        "## Claim Boundary",
        "",
        f"- Silver diagnostic only: {boundary['silver_diagnostic_only']}",
        f"- Not human-gold performance evidence: {boundary['not_human_gold_performance_evidence']}",
        f"- Safe interpretation: {boundary['safe_interpretation']}",
        f"- Not claimable until: {boundary['not_claimable_until']}",
        "",
        "## Schema and CQ Inventory",
        "",
        md_table(
            ["item", "value"],
            [
                {"item": "CQ count", "value": cq["cq_count"]},
                {"item": "All CQs have target predicates", "value": cq["all_cqs_have_target_predicates"]},
                {"item": "Node types", "value": schema["node_type_count"]},
                {"item": "Edge types", "value": schema["edge_type_count"]},
                {"item": "Domain-range rules", "value": schema["domain_range_count"]},
                {"item": "Evidence span required", "value": schema["evidence_span_required"]},
            ],
        ),
        "",
        "## Condition Policy",
        "",
        md_table(["condition", "role", "CQ", "chunk_schema", "taxonomy", "full_schema", "validator", "output", "prompt_file"], prompt_rows_md),
        "",
        "## LLM Output Quantity From Traceability Files",
        "",
        md_table(["condition", "valid_rows", "nodes", "edges", "mappings"], output_rows_md),
        "",
        "## CQ Support Proxy",
        "",
        "CQ support는 LLM valid JSONL의 edge predicate, mapping standard, evidence anchor 존재 여부를 기준으로 계산한 proxy입니다. 이는 human-gold answerability가 아닙니다.",
        "",
        md_table(["condition", "cq_count", "supported_cq_count", "unsupported_cq_count", "support_count_total", "supporting_chunks_total"], cq_summary_md),
        "",
        f"Detailed CQ support CSV: `{payload['outputs']['cq_support_csv']}`",
        "",
        "## Silver Metric Diagnostic",
        "",
        "아래 silver metric은 자동 reference와의 proxy 비교입니다. 최종 main table 수치가 아니며, adjudicated human-gold scoring 이후 재계산해야 합니다.",
        "",
        md_table(["condition", "source_file", "pred_nodes", "pred_edges", "pred_mappings", "edge_exact_f1", "predicate_f1", "node_label_f1", "evidence_f1"], metric_rows_md),
        "",
        "## P vs P_minus_Schema_retrieval Diagnostic Delta",
        "",
        md_table(["metric", "left_condition", "left_value", "right_condition", "right_value", "delta_left_minus_right"], delta_md),
        "",
        "## Input Files",
        "",
    ]
    lines += [f"- {key}: `{value}`" for key, value in payload["input_files"].items() if key != "valid_output_files"]
    lines += [f"- valid_output_file: `{path}`" for path in payload["input_files"]["valid_output_files"]]
    lines += [
        "",
        "## Output Files",
        "",
        f"- JSON: `{payload['outputs']['json']}`",
        f"- Markdown: `{payload['outputs']['markdown']}`",
        f"- CQ support CSV: `{payload['outputs']['cq_support_csv']}`",
        "",
    ]
    return "\n".join(lines)


def run(args):
    payload = build_payload(args.experiment_dir, args.outputs_dir)
    release_dir = Path(args.experiment_dir) / "06_release"
    evaluation_dir = Path(args.experiment_dir) / "04_evaluation"
    json_path = release_dir / "schema_retrieval_coverage_report.json"
    md_path = release_dir / "schema_retrieval_coverage_report.md"
    csv_path = evaluation_dir / "schema_retrieval_cq_support_by_condition.csv"

    write_json(json_path, payload)
    write_text(md_path, render_markdown(payload))
    write_csv(
        csv_path,
        payload["cq_support_rows"],
        [
            "condition",
            "cq_id",
            "question",
            "target_predicates",
            "support_count",
            "supporting_chunks",
            "support_proxy",
            "evidence_anchored_items_in_condition",
            "claim_status",
        ],
    )
    print(
        json.dumps(
            {
                "json": rel(json_path),
                "markdown": rel(md_path),
                "cq_support_csv": rel(csv_path),
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
