#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Evaluate CAPE-KG active-review prioritization with silver/proxy labels.

This does not replace human review timing. It asks whether the automatically
ranked review queue surfaces silver-disagreement/error candidates earlier than
a random queue for actual LLM outputs.
"""

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_VALID_FILE = "49_qwen3_8b_cape_ablation_120_valid.jsonl"
DEFAULT_CONDITION = "P_cape_kg_actual"

ALLOWED_EDGE_TYPES = {
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
    "USED_AS_INPUT_FOR",
}

RISK_TERMS = {
    "risk",
    "위험",
    "리스크",
    "No Bid",
    "노비드",
    "불리",
    "약점",
    "누락",
    "실패",
    "guard",
    "condition",
    "조건",
}

QUEUE_FIELDS = [
    "review_item_id",
    "condition",
    "chunk_id",
    "subject",
    "predicate",
    "object",
    "confidence",
    "active_priority",
    "uncertainty_priority",
    "extraction_uncertainty",
    "evidence_anchor_risk",
    "schema_risk",
    "graph_centrality",
    "conflict_score",
    "silver_exact_match",
    "silver_predicate_match",
    "review_error_label",
    "high_impact_error_label",
    "error_reasons",
    "evidence_anchor_ids",
]

METRIC_FIELDS = [
    "condition",
    "target_label",
    "strategy",
    "budget",
    "reviewed",
    "errors_found",
    "error_precision_at_k",
    "error_recall_at_k",
    "random_expected_errors",
    "lift_vs_random_expected",
]

ABLATION_FIELDS = [
    "condition",
    "target_label",
    "strategy",
    "budget",
    "reviewed",
    "errors_found",
    "error_precision_at_k",
    "error_recall_at_k",
    "random_expected_errors",
    "lift_vs_random_expected",
    "claim_status",
]


def read_jsonl(path):
    rows = []
    path = Path(path)
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


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


def norm_label(value):
    value = str(value or "").strip().lower()
    value = re.sub(r"\s+", "", value)
    value = re.sub(r"[`'\"“”‘’()\[\]{}<>:;,.!?/\\|_-]+", "", value)
    return value


def norm_predicate(value):
    return str(value or "").strip().upper()


def norm_evidence_id(value):
    value = str(value or "").strip()
    if value.startswith("EA-"):
        value = value[3:]
    return value


def safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def stable_id(*parts):
    import hashlib

    text = "|".join(str(part or "") for part in parts)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def ref_edge_key(chunk_id, ref):
    return (
        chunk_id,
        norm_label(ref.get("source_label")),
        norm_predicate(ref.get("predicate")),
        norm_label(ref.get("target_label")),
    )


def pred_edge_key(chunk_id, edge):
    return (
        chunk_id,
        norm_label(edge.get("subject")),
        norm_predicate(edge.get("predicate")),
        norm_label(edge.get("object")),
    )


def load_reference(exp_dir):
    eval_chunks = {row["chunk_id"] for row in read_jsonl(exp_dir / "01_data/evaluation_chunks.jsonl")}
    exact = Counter()
    predicates_by_chunk = defaultdict(set)
    evidence_by_chunk = defaultdict(set)
    for ref in read_jsonl(exp_dir / "01_data/silver_reference_edges.jsonl"):
        chunk_ids = set()
        for span in ref.get("evidence_spans", []):
            chunk_id = span.get("chunk_id")
            if chunk_id in eval_chunks:
                chunk_ids.add(chunk_id)
                if span.get("sentence_id"):
                    evidence_by_chunk[chunk_id].add(norm_evidence_id(span["sentence_id"]))
                if span.get("evidence_anchor_id"):
                    evidence_by_chunk[chunk_id].add(norm_evidence_id(span["evidence_anchor_id"]))
        for chunk_id in chunk_ids:
            exact[ref_edge_key(chunk_id, ref)] += 1
            predicates_by_chunk[chunk_id].add(norm_predicate(ref.get("predicate")))
    return exact, predicates_by_chunk, evidence_by_chunk


def evidence_ids(edge):
    return [norm_evidence_id(value) for value in edge.get("evidence_anchor_ids", []) if norm_evidence_id(value)]


def has_risk_text(*values):
    text = " ".join(str(value or "") for value in values)
    return any(term.lower() in text.lower() for term in RISK_TERMS)


def build_queue(exp_dir, valid_file, condition):
    ref_exact, ref_predicates_by_chunk, ref_evidence_by_chunk = load_reference(exp_dir)
    valid_rows = read_jsonl(valid_file)
    candidates = []
    degree = Counter()

    for row in valid_rows:
        if row.get("condition") != condition:
            continue
        chunk_id = row.get("chunk_id")
        for edge_index, edge in enumerate(row.get("edges", []), start=1):
            subject = str(edge.get("subject") or "").strip()
            obj = str(edge.get("object") or "").strip()
            predicate = norm_predicate(edge.get("predicate"))
            if not subject and not obj and not predicate:
                continue
            candidate = {
                "condition": condition,
                "chunk_id": chunk_id,
                "edge_index": edge_index,
                "subject": subject,
                "predicate": predicate,
                "object": obj,
                "subject_type": edge.get("subject_type") or "",
                "object_type": edge.get("object_type") or "",
                "confidence": round(max(0.0, min(1.0, safe_float(edge.get("confidence"), 0.0))), 3),
                "evidence_anchor_ids": evidence_ids(edge),
            }
            candidates.append(candidate)
            degree[norm_label(subject)] += 1
            degree[norm_label(obj)] += 1

    max_degree = max(degree.values()) if degree else 1
    queue = []
    for idx, item in enumerate(candidates, start=1):
        key = pred_edge_key(item["chunk_id"], item)
        exact_match = ref_exact.get(key, 0) > 0
        predicate_match = item["predicate"] in ref_predicates_by_chunk.get(item["chunk_id"], set())
        evidence = item["evidence_anchor_ids"]
        evidence_in_chunk = bool(set(evidence) & ref_evidence_by_chunk.get(item["chunk_id"], set())) if evidence else False
        schema_valid = item["predicate"] in ALLOWED_EDGE_TYPES and bool(item["subject"]) and bool(item["object"])

        reasons = []
        if not exact_match:
            reasons.append("silver_edge_mismatch")
        if not evidence:
            reasons.append("missing_evidence")
        elif not evidence_in_chunk:
            reasons.append("evidence_not_in_silver_chunk")
        if not schema_valid:
            reasons.append("schema_or_endpoint_issue")
        review_error = bool(reasons)

        uncertainty = round(1.0 - item["confidence"], 4)
        evidence_risk = 0.0 if evidence else 1.0
        schema_risk = 0.0 if schema_valid else 1.0
        centrality = round(max(degree[norm_label(item["subject"])], degree[norm_label(item["object"])]) / max_degree, 4)
        conflict = 1.0 if item["predicate"] in {"HAS_RISK", "HAS_DECISION_GATEWAY", "HAS_GUARD_CONDITION"} or has_risk_text(item["subject"], item["object"]) else 0.0
        high_impact_error = (
            "missing_evidence" in reasons
            or "evidence_not_in_silver_chunk" in reasons
            or "schema_or_endpoint_issue" in reasons
            or (conflict > 0 and not exact_match)
        )
        active_priority = round(
            0.35 * uncertainty
            + 0.25 * evidence_risk
            + 0.20 * centrality
            + 0.10 * schema_risk
            + 0.10 * conflict,
            6,
        )

        queue.append(
            {
                "review_item_id": "ARQ-ACT-" + stable_id(condition, item["chunk_id"], idx, item["subject"], item["predicate"], item["object"]),
                "condition": condition,
                "chunk_id": item["chunk_id"],
                "subject": item["subject"],
                "predicate": item["predicate"],
                "object": item["object"],
                "confidence": item["confidence"],
                "active_priority": active_priority,
                "uncertainty_priority": uncertainty,
                "extraction_uncertainty": uncertainty,
                "evidence_anchor_risk": evidence_risk,
                "schema_risk": schema_risk,
                "graph_centrality": centrality,
                "conflict_score": conflict,
                "silver_exact_match": exact_match,
                "silver_predicate_match": predicate_match,
                "review_error_label": review_error,
                "high_impact_error_label": high_impact_error,
                "error_reasons": ",".join(reasons),
                "evidence_anchor_ids": ",".join(evidence),
            }
        )

    return queue


def budget_values(total):
    values = [10, 25, 50, 100]
    values += [max(1, round(total * frac)) for frac in [0.05, 0.10, 0.20, 0.50]]
    return sorted({value for value in values if 0 < value <= total})


def evaluate_strategy(condition, target_label, label_key, strategy, rows, total_errors, total_items):
    metrics = []
    for budget in budget_values(total_items):
        selected = rows[:budget]
        errors_found = sum(1 for row in selected if row[label_key])
        expected_random = budget * total_errors / total_items if total_items else 0.0
        lift = errors_found / expected_random if expected_random else 0.0
        metrics.append(
            {
                "condition": condition,
                "target_label": target_label,
                "strategy": strategy,
                "budget": budget,
                "reviewed": len(selected),
                "errors_found": errors_found,
                "error_precision_at_k": round(errors_found / len(selected), 6) if selected else 0.0,
                "error_recall_at_k": round(errors_found / total_errors, 6) if total_errors else 0.0,
                "random_expected_errors": round(expected_random, 6),
                "lift_vs_random_expected": round(lift, 6),
            }
        )
    return metrics


def build_ablation_metrics(condition, metrics, target_totals):
    wanted_budgets = {10, 25, 55, 100}
    rows = []
    random_seen = set()
    for row in metrics:
        budget = int(row.get("budget") or 0)
        if budget not in wanted_budgets:
            continue
        target_label = row.get("target_label")
        if row.get("strategy") == "active_priority":
            rows.append(
                {
                    **row,
                    "condition": f"{condition}_with_active_review",
                    "claim_status": "silver_proxy_ablation_not_human_efficiency",
                }
            )
            random_key = (target_label, budget)
            if random_key not in random_seen:
                random_seen.add(random_key)
                target_total = target_totals.get(target_label, 0)
                expected = float(row.get("random_expected_errors") or 0.0)
                rows.append(
                    {
                        "condition": "P_minus_Active_review_random_expected",
                        "target_label": target_label,
                        "strategy": "random_expected",
                        "budget": budget,
                        "reviewed": budget,
                        "errors_found": round(expected, 6),
                        "error_precision_at_k": round(expected / budget, 6) if budget else 0.0,
                        "error_recall_at_k": round(expected / target_total, 6) if target_total else 0.0,
                        "random_expected_errors": round(expected, 6),
                        "lift_vs_random_expected": 1.0 if expected else 0.0,
                        "claim_status": "silver_proxy_ablation_not_human_efficiency",
                    }
                )
        elif row.get("strategy") == "uncertainty_only":
            rows.append(
                {
                    **row,
                    "condition": "P_minus_Active_review_uncertainty_only",
                    "claim_status": "silver_proxy_ablation_not_human_efficiency",
                }
            )
    rows.sort(key=lambda item: (str(item.get("target_label")), int(item.get("budget") or 0), str(item.get("condition"))))
    return rows


def build_ablation_report(payload):
    lines = [
        "# CAPE-KG Active Review Ablation Diagnostic",
        "",
        f"Generated: {payload['generated_at_utc']}",
        "",
        "This report makes the revised plan's `P - Active review` ablation explicit.",
        "It is a silver/proxy diagnostic only; final active-review efficiency requires human effort timing and adjudicated labels.",
        "",
        "## Summary",
        "",
        f"- Base condition: `{payload['base_condition']}`",
        f"- Compared conditions: `{payload['conditions']}`",
        f"- Row count: {payload['row_count']}",
        f"- Claim status: `{payload['claim_status']}`",
        "",
        "## Ablation Rows",
        "",
        "| target | condition | strategy | budget | errors found | precision@k | recall@k | lift |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row.get('target_label')} | {row.get('condition')} | {row.get('strategy')} | "
            f"{row.get('budget')} | {row.get('errors_found')} | {row.get('error_precision_at_k')} | "
            f"{row.get('error_recall_at_k')} | {row.get('lift_vs_random_expected')} |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "- `P_cape_kg_actual_with_active_review` uses the CAPE active-priority queue.",
        "- `P_minus_Active_review_random_expected` removes active review and uses the random expected baseline.",
        "- `P_minus_Active_review_uncertainty_only` keeps uncertainty ranking but removes the multi-signal active-priority queue.",
        "- Do not report these values as final human-review efficiency until human timing/correction files are returned.",
        "",
    ]
    return "\n".join(lines)


def build_report(payload):
    lines = [
        "# CAPE-KG Active Review Efficiency Diagnostic",
        "",
        f"Generated: {payload['generated_at_utc']}",
        "",
        "This is a silver/proxy diagnostic. It does not claim human review efficiency until human reviewer timing and adjudicated labels are available.",
        "",
        f"- Condition: `{payload['condition']}`",
        f"- Valid file: `{payload['valid_file']}`",
        f"- Review candidates: {payload['candidate_count']}",
        f"- Silver/proxy error candidates: {payload['error_count']}",
        f"- Error rate: {payload['error_rate']}",
        "",
        "## Budget Curves",
        "",
        "| target | strategy | budget | errors found | precision@k | recall@k | random expected | lift |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["metrics"]:
        lines.append(
            f"| {row['target_label']} | {row['strategy']} | {row['budget']} | {row['errors_found']} | "
            f"{row['error_precision_at_k']} | {row['error_recall_at_k']} | "
            f"{row['random_expected_errors']} | {row['lift_vs_random_expected']} |"
        )
    lines += [
        "",
        "## Files",
        "",
        f"- Queue JSONL: `{payload['queue_jsonl']}`",
        f"- Queue CSV: `{payload['queue_csv']}`",
        f"- Metrics JSON: `{payload['metrics_json']}`",
        f"- Metrics CSV: `{payload['metrics_csv']}`",
        f"- Active-review ablation report: `{payload['active_review_ablation_report']}`",
        "",
    ]
    return "\n".join(lines)


def run(args):
    exp_dir = Path(args.experiment_dir)
    valid_file = Path(args.valid_file) if args.valid_file else exp_dir / DEFAULT_VALID_FILE
    output_dir = exp_dir / "04_evaluation"
    review_dir = exp_dir / "05_review"
    condition = args.condition

    queue = build_queue(exp_dir, valid_file, condition)
    queue = sorted(queue, key=lambda row: row["active_priority"], reverse=True)
    total_items = len(queue)
    total_errors = sum(1 for row in queue if row["review_error_label"])
    total_high_impact_errors = sum(1 for row in queue if row["high_impact_error_label"])

    active_rows = sorted(queue, key=lambda row: row["active_priority"], reverse=True)
    uncertainty_rows = sorted(queue, key=lambda row: row["uncertainty_priority"], reverse=True)
    metrics = []
    metrics.extend(evaluate_strategy(condition, "all_silver_error", "review_error_label", "active_priority", active_rows, total_errors, total_items))
    metrics.extend(evaluate_strategy(condition, "all_silver_error", "review_error_label", "uncertainty_only", uncertainty_rows, total_errors, total_items))
    metrics.extend(evaluate_strategy(condition, "high_impact_error", "high_impact_error_label", "active_priority", active_rows, total_high_impact_errors, total_items))
    metrics.extend(evaluate_strategy(condition, "high_impact_error", "high_impact_error_label", "uncertainty_only", uncertainty_rows, total_high_impact_errors, total_items))

    queue_jsonl = review_dir / f"actual_llm_active_review_queue_{condition}.jsonl"
    queue_csv = review_dir / f"actual_llm_active_review_queue_{condition}.csv"
    metrics_json = output_dir / "active_review_efficiency_metrics.json"
    metrics_csv = output_dir / "active_review_efficiency_metrics.csv"
    report_path = output_dir / "active_review_efficiency_report.md"
    ablation_json = output_dir / "active_review_ablation_metrics.json"
    ablation_csv = output_dir / "active_review_ablation_metrics.csv"
    ablation_report = output_dir / "active_review_ablation_report.md"
    ablation_rows = build_ablation_metrics(
        condition,
        metrics,
        {
            "all_silver_error": total_errors,
            "high_impact_error": total_high_impact_errors,
        },
    )
    ablation_payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "base_condition": condition,
        "conditions": sorted({row.get("condition") for row in ablation_rows}),
        "row_count": len(ablation_rows),
        "claim_status": "silver_proxy_ablation_not_human_efficiency",
        "source_metrics_json": str(metrics_json),
        "rows": ablation_rows,
    }

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "condition": condition,
        "valid_file": str(valid_file),
        "candidate_count": total_items,
        "error_count": total_errors,
        "error_rate": round(total_errors / total_items, 6) if total_items else 0.0,
        "high_impact_error_count": total_high_impact_errors,
        "high_impact_error_rate": round(total_high_impact_errors / total_items, 6) if total_items else 0.0,
        "claim_status": "silver_proxy_not_human_review_efficiency",
        "queue_jsonl": str(queue_jsonl),
        "queue_csv": str(queue_csv),
        "metrics_json": str(metrics_json),
        "metrics_csv": str(metrics_csv),
        "report_file": str(report_path),
        "active_review_ablation_json": str(ablation_json),
        "active_review_ablation_csv": str(ablation_csv),
        "active_review_ablation_report": str(ablation_report),
        "metrics": metrics,
    }

    write_jsonl(queue_jsonl, queue)
    write_csv(queue_csv, queue, QUEUE_FIELDS)
    write_json(metrics_json, payload)
    write_csv(metrics_csv, metrics, METRIC_FIELDS)
    write_json(ablation_json, ablation_payload)
    write_csv(ablation_csv, ablation_rows, ABLATION_FIELDS)
    write_text(ablation_report, build_ablation_report(ablation_payload))
    write_text(report_path, build_report(payload))
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--valid-file", default="")
    parser.add_argument("--condition", default=DEFAULT_CONDITION)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
