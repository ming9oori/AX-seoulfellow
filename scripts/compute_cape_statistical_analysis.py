#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compute silver/proxy statistical diagnostics for CAPE-KG outputs.

The report is intentionally conservative: it uses the current silver reference
only and does not make final paper claims before human-gold adjudication.
"""

import argparse
import csv
import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from evaluate_actual_llm_silver import (
    DEFAULT_VALID_FILES,
    collect_reference_instances,
    counter_prf,
    evidence_ids_from_item,
    evidence_ids_from_ref,
    norm_label,
    norm_predicate,
    pred_edge_key,
    read_jsonl,
    ref_edge_key,
    ref_node_keys,
)


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
PROPOSED_CONDITION = "P_cape_kg_actual"
COMPARISON_CONDITIONS = [
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
]
METRICS = ["edge_exact_f1", "predicate_f1", "node_label_f1", "evidence_f1"]


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path, rows, fieldnames=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def round6(value):
    return round(float(value), 6)


def collect_ref_counters(ref_by_chunk, chunk_id):
    ref_edges = Counter()
    ref_predicates = Counter()
    ref_nodes = Counter()
    ref_evidence = Counter()
    for ref in ref_by_chunk.get(chunk_id, []):
        ref_edges[ref_edge_key(chunk_id, ref)] += 1
        ref_predicates[(chunk_id, norm_predicate(ref.get("predicate")))] += 1
        for node_key in ref_node_keys(chunk_id, ref):
            ref_nodes[node_key] += 1
        for evidence_id in evidence_ids_from_ref(ref, chunk_id):
            ref_evidence[(chunk_id, evidence_id)] += 1
    return {
        "edges": ref_edges,
        "predicates": ref_predicates,
        "nodes": ref_nodes,
        "evidence": ref_evidence,
    }


def empty_pred_counters():
    return {
        "edges": Counter(),
        "predicates": Counter(),
        "nodes": Counter(),
        "evidence": Counter(),
    }


def collect_prediction_counters(valid_files):
    by_condition_chunk = defaultdict(lambda: defaultdict(empty_pred_counters))
    rows_by_condition = Counter()
    for valid_path in valid_files:
        for row in read_jsonl(valid_path):
            condition = row.get("condition") or "unknown"
            chunk_id = row.get("chunk_id")
            if not chunk_id:
                continue
            rows_by_condition[condition] += 1
            pred = by_condition_chunk[condition][chunk_id]
            for node in row.get("nodes", []):
                label = norm_label(node.get("label"))
                if label:
                    pred["nodes"][(chunk_id, label)] += 1
                for evidence_id in evidence_ids_from_item(node):
                    pred["evidence"][(chunk_id, evidence_id)] += 1
            for edge in row.get("edges", []):
                predicate = norm_predicate(edge.get("predicate"))
                key = pred_edge_key(chunk_id, edge)
                if key[1] and key[2] and key[3]:
                    pred["edges"][key] += 1
                if predicate:
                    pred["predicates"][(chunk_id, predicate)] += 1
                for evidence_id in evidence_ids_from_item(edge):
                    pred["evidence"][(chunk_id, evidence_id)] += 1
            for triple in row.get("triples", []):
                subject = norm_label(triple.get("subject"))
                obj = norm_label(triple.get("object"))
                predicate = norm_predicate(triple.get("predicate"))
                if subject:
                    pred["nodes"][(chunk_id, subject)] += 1
                if obj:
                    pred["nodes"][(chunk_id, obj)] += 1
                if subject and predicate and obj:
                    pred["edges"][(chunk_id, subject, predicate, obj)] += 1
                if predicate:
                    pred["predicates"][(chunk_id, predicate)] += 1
                for evidence_id in evidence_ids_from_item(triple):
                    pred["evidence"][(chunk_id, evidence_id)] += 1
    return by_condition_chunk, rows_by_condition


def score_chunk(pred, ref):
    edge = counter_prf(pred["edges"], ref["edges"])
    predicate = counter_prf(pred["predicates"], ref["predicates"])
    node = counter_prf(pred["nodes"], ref["nodes"])
    evidence = counter_prf(pred["evidence"], ref["evidence"])
    return {
        "edge_exact_f1": edge["f1"],
        "predicate_f1": predicate["f1"],
        "node_label_f1": node["f1"],
        "evidence_f1": evidence["f1"],
        "edge_exact_tp": edge["tp"],
        "predicate_tp": predicate["tp"],
        "node_label_tp": node["tp"],
        "evidence_tp": evidence["tp"],
        "ref_edges": sum(ref["edges"].values()),
        "pred_edges": sum(pred["edges"].values()),
    }


def build_chunk_scores(exp_dir, valid_files):
    eval_chunks = [row["chunk_id"] for row in read_jsonl(exp_dir / "01_data/evaluation_chunks.jsonl")]
    ref_by_chunk = collect_reference_instances(exp_dir)
    pred_by_condition_chunk, rows_by_condition = collect_prediction_counters(valid_files)
    conditions = sorted(pred_by_condition_chunk)
    rows = []
    by_condition = defaultdict(dict)
    for condition in conditions:
        for chunk_id in eval_chunks:
            ref = collect_ref_counters(ref_by_chunk, chunk_id)
            pred = pred_by_condition_chunk[condition].get(chunk_id, empty_pred_counters())
            scores = score_chunk(pred, ref)
            row = {
                "condition": condition,
                "chunk_id": chunk_id,
                **scores,
                "claim_status": "silver_proxy_not_human_gold",
            }
            rows.append(row)
            by_condition[condition][chunk_id] = row
    return eval_chunks, conditions, rows_by_condition, rows, by_condition


def percentile(values, pct):
    if not values:
        return 0.0
    ordered = sorted(values)
    pos = (len(ordered) - 1) * pct
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return ordered[int(pos)]
    return ordered[lo] * (hi - pos) + ordered[hi] * (pos - lo)


def bootstrap_delta_ci(deltas, iterations, seed):
    if not deltas:
        return {"mean_delta": 0.0, "ci_low": 0.0, "ci_high": 0.0, "p_approx": 1.0}
    rng = random.Random(seed)
    n = len(deltas)
    means = []
    for _ in range(iterations):
        sample = [deltas[rng.randrange(n)] for _i in range(n)]
        means.append(sum(sample) / n)
    mean_delta = sum(deltas) / n
    le_zero = sum(1 for value in means if value <= 0.0) / len(means)
    ge_zero = sum(1 for value in means if value >= 0.0) / len(means)
    return {
        "mean_delta": round6(mean_delta),
        "ci_low": round6(percentile(means, 0.025)),
        "ci_high": round6(percentile(means, 0.975)),
        "p_approx": round6(min(1.0, 2 * min(le_zero, ge_zero))),
    }


def binomial_two_sided_p(discordant_a, discordant_b):
    n = discordant_a + discordant_b
    if n == 0:
        return 1.0
    k = min(discordant_a, discordant_b)
    prob = sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n)
    return min(1.0, 2 * prob)


def compare_conditions(eval_chunks, by_condition, baseline, proposed, iterations, seed):
    rows = []
    mcnemar_rows = []
    for metric in METRICS:
        proposed_scores = [by_condition[proposed][chunk_id][metric] for chunk_id in eval_chunks]
        baseline_scores = [by_condition[baseline][chunk_id][metric] for chunk_id in eval_chunks]
        deltas = [p - b for p, b in zip(proposed_scores, baseline_scores)]
        seed_key = f"{baseline}|{proposed}|{metric}".encode("utf-8")
        seed_offset = int(hashlib.sha1(seed_key).hexdigest()[:8], 16)
        ci = bootstrap_delta_ci(deltas, iterations, seed + seed_offset)
        proposed_mean = sum(proposed_scores) / len(proposed_scores) if proposed_scores else 0.0
        baseline_mean = sum(baseline_scores) / len(baseline_scores) if baseline_scores else 0.0
        rows.append(
            {
                "proposed_condition": proposed,
                "baseline_condition": baseline,
                "metric": metric,
                "proposed_macro_mean": round6(proposed_mean),
                "baseline_macro_mean": round6(baseline_mean),
                "mean_delta": ci["mean_delta"],
                "bootstrap_ci_low": ci["ci_low"],
                "bootstrap_ci_high": ci["ci_high"],
                "bootstrap_p_approx": ci["p_approx"],
                "chunks": len(eval_chunks),
                "iterations": iterations,
                "claim_status": "silver_proxy_not_human_gold",
            }
        )

        proposed_success = [score > 0 for score in proposed_scores]
        baseline_success = [score > 0 for score in baseline_scores]
        proposed_only = sum(1 for p, b in zip(proposed_success, baseline_success) if p and not b)
        baseline_only = sum(1 for p, b in zip(proposed_success, baseline_success) if b and not p)
        both_success = sum(1 for p, b in zip(proposed_success, baseline_success) if p and b)
        neither = sum(1 for p, b in zip(proposed_success, baseline_success) if not p and not b)
        mcnemar_rows.append(
            {
                "proposed_condition": proposed,
                "baseline_condition": baseline,
                "metric": metric,
                "proposed_only_success_chunks": proposed_only,
                "baseline_only_success_chunks": baseline_only,
                "both_success_chunks": both_success,
                "neither_success_chunks": neither,
                "exact_mcnemar_p": round6(binomial_two_sided_p(proposed_only, baseline_only)),
                "claim_status": "silver_proxy_not_human_gold",
            }
        )
    return rows, mcnemar_rows


def build_report(payload):
    lines = [
        "# CAPE-KG Statistical Diagnostics",
        "",
        f"Generated: {payload['generated_at_utc']}",
        "",
        "This report uses the current silver reference only. It is not final paper evidence until the same analysis is run against adjudicated human-gold labels.",
        "",
        f"- Proposed condition: `{payload['proposed_condition']}`",
        f"- Chunks: {payload['chunk_count']}",
        f"- Bootstrap iterations: {payload['bootstrap_iterations']}",
        "",
        "## Paired Bootstrap Delta",
        "",
        "| baseline | metric | proposed mean | baseline mean | delta | 95% CI | p approx |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    focus_metrics = {"predicate_f1", "node_label_f1", "evidence_f1"}
    for row in payload["bootstrap_rows"]:
        if row["metric"] not in focus_metrics:
            continue
        lines.append(
            f"| {row['baseline_condition']} | {row['metric']} | "
            f"{row['proposed_macro_mean']} | {row['baseline_macro_mean']} | "
            f"{row['mean_delta']} | [{row['bootstrap_ci_low']}, {row['bootstrap_ci_high']}] | "
            f"{row['bootstrap_p_approx']} |"
        )
    lines += [
        "",
        "## Chunk-Level Success McNemar Diagnostic",
        "",
        "| baseline | metric | proposed-only | baseline-only | both | neither | exact p |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in payload["mcnemar_rows"]:
        if row["metric"] not in focus_metrics:
            continue
        lines.append(
            f"| {row['baseline_condition']} | {row['metric']} | "
            f"{row['proposed_only_success_chunks']} | {row['baseline_only_success_chunks']} | "
            f"{row['both_success_chunks']} | {row['neither_success_chunks']} | "
            f"{row['exact_mcnemar_p']} |"
        )
    lines += [
        "",
        "## Files",
        "",
        f"- JSON: `{payload['json_file']}`",
        f"- Bootstrap CSV: `{payload['bootstrap_csv']}`",
        f"- McNemar CSV: `{payload['mcnemar_csv']}`",
        f"- Per-chunk CSV: `{payload['chunk_scores_csv']}`",
        "",
    ]
    return "\n".join(lines)


def run(args):
    exp_dir = Path(args.experiment_dir)
    output_dir = exp_dir / "04_evaluation"
    valid_files = [exp_dir / name for name in DEFAULT_VALID_FILES]
    if args.valid_file:
        valid_files = [Path(path) for path in args.valid_file]
    valid_files = [path for path in valid_files if path.exists()]
    eval_chunks, conditions, rows_by_condition, chunk_rows, by_condition = build_chunk_scores(exp_dir, valid_files)
    proposed = args.proposed_condition
    comparisons = [condition for condition in COMPARISON_CONDITIONS if condition in conditions and condition != proposed]
    if proposed not in conditions:
        raise SystemExit(f"Missing proposed condition: {proposed}")

    bootstrap_rows = []
    mcnemar_rows = []
    for baseline in comparisons:
        boot, mcn = compare_conditions(eval_chunks, by_condition, baseline, proposed, args.bootstrap_iterations, args.seed)
        bootstrap_rows.extend(boot)
        mcnemar_rows.extend(mcn)

    json_path = output_dir / "statistical_analysis_metrics.json"
    bootstrap_csv = output_dir / "statistical_analysis_bootstrap.csv"
    mcnemar_csv = output_dir / "statistical_analysis_mcnemar.csv"
    chunk_scores_csv = output_dir / "statistical_analysis_chunk_scores.csv"
    report_path = output_dir / "statistical_analysis_report.md"
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "source_valid_files": [str(path) for path in valid_files],
        "proposed_condition": proposed,
        "comparison_conditions": comparisons,
        "chunk_count": len(eval_chunks),
        "conditions": conditions,
        "rows_by_condition": dict(rows_by_condition),
        "bootstrap_iterations": args.bootstrap_iterations,
        "seed": args.seed,
        "claim_status": "silver_proxy_not_human_gold",
        "json_file": str(json_path),
        "bootstrap_csv": str(bootstrap_csv),
        "mcnemar_csv": str(mcnemar_csv),
        "chunk_scores_csv": str(chunk_scores_csv),
        "report_file": str(report_path),
        "bootstrap_rows": bootstrap_rows,
        "mcnemar_rows": mcnemar_rows,
    }
    write_json(json_path, payload)
    write_csv(bootstrap_csv, bootstrap_rows)
    write_csv(mcnemar_csv, mcnemar_rows)
    write_csv(chunk_scores_csv, chunk_rows)
    write_text(report_path, build_report(payload))
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--valid-file", action="append", help="Optional valid JSONL file. Repeat to evaluate multiple files.")
    parser.add_argument("--proposed-condition", default=PROPOSED_CONDITION)
    parser.add_argument("--bootstrap-iterations", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=1729)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
