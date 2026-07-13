#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Evaluate actual LLM condition outputs against the silver CAPE-KG reference.

This is a silver/proxy evaluator. It does not replace human gold scoring.
"""

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")

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

DEFAULT_VALID_FILES = [
    "49_qwen3_8b_condition_baselines_120_valid.jsonl",
    "49_qwen3_8b_b2_b4_condition_baselines_120_valid.jsonl",
    "49_qwen3_8b_edc_schema_ablation_valid.jsonl",
    "49_qwen3_8b_cape_ablation_120_valid.jsonl",
    "49_sac_kg_verifier_pruner_baseline_valid.jsonl",
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


def write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0])
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


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


def prf(tp, fp, fn):
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1": round(f1, 6),
    }


def counter_prf(pred_counter, ref_counter):
    tp = sum((pred_counter & ref_counter).values())
    pred_total = sum(pred_counter.values())
    ref_total = sum(ref_counter.values())
    scores = prf(tp, pred_total - tp, ref_total - tp)
    scores.update({"tp": tp, "fp": pred_total - tp, "fn": ref_total - tp})
    return scores


def collect_reference_instances(exp_dir):
    eval_chunks = {row["chunk_id"] for row in read_jsonl(exp_dir / "01_data/evaluation_chunks.jsonl")}
    ref_by_chunk = defaultdict(dict)
    for ref in read_jsonl(exp_dir / "01_data/silver_reference_edges.jsonl"):
        reference_id = ref.get("reference_id")
        for span in ref.get("evidence_spans", []):
            chunk_id = span.get("chunk_id")
            if not chunk_id or chunk_id not in eval_chunks:
                continue
            key = reference_id or f"{ref.get('source_id')}|{ref.get('predicate')}|{ref.get('target_id')}"
            ref_by_chunk[chunk_id][key] = ref
    return {chunk_id: list(rows.values()) for chunk_id, rows in ref_by_chunk.items()}


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


def ref_node_keys(chunk_id, ref):
    keys = []
    if ref.get("source_label"):
        keys.append((chunk_id, norm_label(ref.get("source_label"))))
    if ref.get("target_label"):
        keys.append((chunk_id, norm_label(ref.get("target_label"))))
    return keys


def evidence_ids_from_ref(ref, chunk_id):
    ids = set()
    for span in ref.get("evidence_spans", []):
        if span.get("chunk_id") != chunk_id:
            continue
        if span.get("sentence_id"):
            ids.add(norm_evidence_id(span["sentence_id"]))
        elif span.get("evidence_anchor_id"):
            ids.add(norm_evidence_id(span["evidence_anchor_id"]))
    for evidence_id in ref.get("evidence_anchor_ids", []):
        ids.add(norm_evidence_id(evidence_id))
    return ids


def evidence_ids_from_item(item):
    return {norm_evidence_id(v) for v in item.get("evidence_anchor_ids", []) if v}


def load_raw_error_counts(valid_path):
    raw_name = valid_path.name.replace("49_", "48_").replace("_valid.jsonl", "_raw.jsonl")
    raw_path = valid_path.with_name(raw_name)
    counts = defaultdict(Counter)
    for row in read_jsonl(raw_path):
        condition = row.get("condition", "unknown")
        counts[condition]["raw_rows"] += 1
        if row.get("parse_error") or row.get("error"):
            counts[condition]["parse_or_generation_error_rows"] += 1
        if row.get("partial_json_repaired"):
            counts[condition]["partial_json_repaired_rows"] += 1
    return counts


def evaluate_file(exp_dir, valid_path, ref_by_chunk):
    raw_counts = load_raw_error_counts(valid_path)
    by_condition = defaultdict(lambda: {
        "source_file": valid_path.name,
        "rows": 0,
        "chunks": set(),
        "pred_edges": Counter(),
        "pred_predicates": Counter(),
        "pred_nodes": Counter(),
        "pred_evidence": Counter(),
        "pred_triples": 0,
        "pred_mappings": 0,
        "edge_items": 0,
        "edge_items_with_evidence": 0,
        "schema_valid_edges": 0,
        "mapping_items_with_evidence": 0,
    })

    for row in read_jsonl(valid_path):
        condition = row.get("condition", "unknown")
        chunk_id = row.get("chunk_id")
        agg = by_condition[condition]
        agg["rows"] += 1
        if chunk_id:
            agg["chunks"].add(chunk_id)
        for node in row.get("nodes", []):
            label = norm_label(node.get("label"))
            if label:
                agg["pred_nodes"][(chunk_id, label)] += 1
            for evidence_id in evidence_ids_from_item(node):
                agg["pred_evidence"][(chunk_id, evidence_id)] += 1
        for edge in row.get("edges", []):
            predicate = norm_predicate(edge.get("predicate"))
            agg["edge_items"] += 1
            if evidence_ids_from_item(edge):
                agg["edge_items_with_evidence"] += 1
            if predicate in ALLOWED_EDGE_TYPES:
                agg["schema_valid_edges"] += 1
            key = pred_edge_key(chunk_id, edge)
            if key[1] and key[2] and key[3]:
                agg["pred_edges"][key] += 1
            if predicate:
                agg["pred_predicates"][(chunk_id, predicate)] += 1
            for evidence_id in evidence_ids_from_item(edge):
                agg["pred_evidence"][(chunk_id, evidence_id)] += 1
        for triple in row.get("triples", []):
            agg["pred_triples"] += 1
            label_subject = norm_label(triple.get("subject"))
            label_object = norm_label(triple.get("object"))
            if label_subject:
                agg["pred_nodes"][(chunk_id, label_subject)] += 1
            if label_object:
                agg["pred_nodes"][(chunk_id, label_object)] += 1
            for evidence_id in evidence_ids_from_item(triple):
                agg["pred_evidence"][(chunk_id, evidence_id)] += 1
        for mapping in row.get("mappings", []):
            agg["pred_mappings"] += 1
            if evidence_ids_from_item(mapping):
                agg["mapping_items_with_evidence"] += 1
            for evidence_id in evidence_ids_from_item(mapping):
                agg["pred_evidence"][(chunk_id, evidence_id)] += 1

    results = []
    for condition, agg in sorted(by_condition.items()):
        ref_edges = Counter()
        ref_predicates = Counter()
        ref_nodes = Counter()
        ref_evidence = Counter()
        for chunk_id in agg["chunks"]:
            for ref in ref_by_chunk.get(chunk_id, []):
                ref_edges[ref_edge_key(chunk_id, ref)] += 1
                ref_predicates[(chunk_id, norm_predicate(ref.get("predicate")))] += 1
                for node_key in ref_node_keys(chunk_id, ref):
                    ref_nodes[node_key] += 1
                for evidence_id in evidence_ids_from_ref(ref, chunk_id):
                    ref_evidence[(chunk_id, evidence_id)] += 1

        edge_scores = counter_prf(agg["pred_edges"], ref_edges)
        predicate_scores = counter_prf(agg["pred_predicates"], ref_predicates)
        node_scores = counter_prf(agg["pred_nodes"], ref_nodes)
        evidence_scores = counter_prf(agg["pred_evidence"], ref_evidence)
        raw = raw_counts.get(condition, Counter())
        edge_evidence_rate = agg["edge_items_with_evidence"] / agg["edge_items"] if agg["edge_items"] else 0.0
        schema_edge_rate = agg["schema_valid_edges"] / agg["edge_items"] if agg["edge_items"] else 0.0
        mapping_evidence_rate = agg["mapping_items_with_evidence"] / agg["pred_mappings"] if agg["pred_mappings"] else 0.0
        results.append({
            "source_file": agg["source_file"],
            "condition": condition,
            "rows": agg["rows"],
            "chunks": len(agg["chunks"]),
            "raw_rows": raw.get("raw_rows", agg["rows"]),
            "parse_or_generation_error_rows": raw.get("parse_or_generation_error_rows", 0),
            "partial_json_repaired_rows": raw.get("partial_json_repaired_rows", 0),
            "pred_edges": sum(agg["pred_edges"].values()),
            "pred_nodes": sum(agg["pred_nodes"].values()),
            "pred_triples": agg["pred_triples"],
            "pred_mappings": agg["pred_mappings"],
            "ref_edge_instances": sum(ref_edges.values()),
            "edge_exact_precision": edge_scores["precision"],
            "edge_exact_recall": edge_scores["recall"],
            "edge_exact_f1": edge_scores["f1"],
            "edge_exact_tp": edge_scores["tp"],
            "predicate_precision": predicate_scores["precision"],
            "predicate_recall": predicate_scores["recall"],
            "predicate_f1": predicate_scores["f1"],
            "node_label_precision": node_scores["precision"],
            "node_label_recall": node_scores["recall"],
            "node_label_f1": node_scores["f1"],
            "evidence_precision": evidence_scores["precision"],
            "evidence_recall": evidence_scores["recall"],
            "evidence_f1": evidence_scores["f1"],
            "edge_evidence_attachment_rate": round(edge_evidence_rate, 6),
            "schema_edge_rate": round(schema_edge_rate, 6),
            "mapping_evidence_attachment_rate": round(mapping_evidence_rate, 6),
            "claim_status": "silver_proxy_not_human_gold",
        })
    return results


def build_report(rows, output_dir, output_stem):
    lines = [
        "# Actual LLM Silver Evaluation",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "This report scores actual LLM generations against the silver reference derived from the current KG.",
        "It is useful for debugging and relative sanity checks, but it is not a substitute for human-gold evaluation.",
        "",
        "## Summary",
        "",
        "| source file | condition | rows | edges | exact F1 | predicate F1 | node F1 | evidence F1 | repair rows | parse/error rows |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in sorted(rows, key=lambda r: (r["source_file"], r["condition"])):
        lines.append(
            f"| {row['source_file']} | {row['condition']} | {row['rows']} | {row['pred_edges']} | "
            f"{row['edge_exact_f1']} | {row['predicate_f1']} | {row['node_label_f1']} | "
            f"{row['evidence_f1']} | {row['partial_json_repaired_rows']} | "
            f"{row['parse_or_generation_error_rows']} |"
        )
    lines += [
        "",
        "## Interpretation Notes",
        "",
        "- `edge_exact_f1` requires exact normalized subject label, predicate, and object label match within the same chunk.",
        "- `predicate_f1` ignores subject/object labels and measures whether the same CAPE predicate types appear in each chunk.",
        "- `node_label_f1` compares predicted node/triple labels with reference source/target labels within each chunk.",
        "- `evidence_f1` compares sentence/evidence IDs used by the model with reference evidence IDs in the same chunk.",
        "- High `partial_json_repaired_rows` means the raw generation was truncated or malformed but complete arrays were salvaged for audit.",
        "",
        f"- CSV: `{output_dir / f'{output_stem}_metrics.csv'}`",
        f"- JSON: `{output_dir / f'{output_stem}_metrics.json'}`",
        "",
    ]
    return "\n".join(lines)


def run(args):
    exp_dir = Path(args.experiment_dir)
    output_dir = exp_dir / "04_evaluation"
    output_stem = args.output_stem
    ref_by_chunk = collect_reference_instances(exp_dir)
    valid_files = [exp_dir / name for name in DEFAULT_VALID_FILES]
    if args.valid_file:
        valid_files = [Path(path) for path in args.valid_file]

    all_rows = []
    for valid_path in valid_files:
        if not valid_path.exists():
            continue
        all_rows.extend(evaluate_file(exp_dir, valid_path, ref_by_chunk))

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "source_valid_files": [str(path) for path in valid_files if path.exists()],
        "reference": "silver_reference_edges_by_chunk",
        "claim_status": "silver_proxy_not_human_gold",
        "metrics": all_rows,
    }
    write_csv(output_dir / f"{output_stem}_metrics.csv", all_rows)
    write_json(output_dir / f"{output_stem}_metrics.json", payload)
    write_text(output_dir / f"{output_stem}_evaluation_report.md", build_report(all_rows, output_dir, output_stem))
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--valid-file", action="append", help="Optional valid JSONL file. Repeat to evaluate multiple files.")
    parser.add_argument("--output-stem", default="actual_llm_silver")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
