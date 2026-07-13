#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compute two-annotator agreement for CAPE-KG gold annotation JSONL files."""

import argparse
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


COMPLETED_STATUSES = {"completed", "needs_adjudication", "adjudicated"}


def read_jsonl(path):
    rows = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def norm(value):
    return " ".join(str(value or "").strip().split()).lower()


def edge_key(edge):
    return (
        norm(edge.get("source_id") or edge.get("source_label")),
        norm(edge.get("predicate") or edge.get("edge_type")),
        norm(edge.get("target_id") or edge.get("target_label")),
    )


def node_key(node):
    return (norm(node.get("type")), norm(node.get("node_id") or node.get("label")))


def evidence_ids(edge):
    ids = set(edge.get("evidence_anchor_ids") or [])
    for span in edge.get("evidence_spans") or []:
        if span.get("evidence_anchor_id"):
            ids.add(span["evidence_anchor_id"])
        elif span.get("sentence_id"):
            ids.add(span["sentence_id"])
    return {norm(v) for v in ids if v}


def row_completed(row):
    return row.get("annotation_status") in COMPLETED_STATUSES


def f1(set_a, set_b):
    if not set_a and not set_b:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0, "intersection": 0, "a_count": 0, "b_count": 0}
    inter = len(set_a & set_b)
    precision = inter / len(set_a) if set_a else 0.0
    recall = inter / len(set_b) if set_b else 0.0
    score = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1": round(score, 6),
        "intersection": inter,
        "a_count": len(set_a),
        "b_count": len(set_b),
    }


def cohen_kappa(pairs):
    if not pairs:
        return None
    n = len(pairs)
    agree = sum(1 for a, b in pairs if a == b)
    p0 = agree / n
    a_counts = Counter(a for a, _ in pairs)
    b_counts = Counter(b for _, b in pairs)
    pe = sum((a_counts[label] / n) * (b_counts[label] / n) for label in set(a_counts) | set(b_counts))
    if math.isclose(1.0, pe):
        return 1.0 if math.isclose(1.0, p0) else 0.0
    return round((p0 - pe) / (1 - pe), 6)


def candidate_key(candidate):
    return (
        norm(candidate.get("source_id") or candidate.get("source_label")),
        norm(candidate.get("predicate")),
        norm(candidate.get("target_id") or candidate.get("target_label")),
    )


def accepted_candidate_pairs(row_a, row_b, edges_a, edges_b):
    candidate_keys = set()
    for row in (row_a, row_b):
        for candidate in row.get("silver_candidate_edges") or []:
            key = candidate_key(candidate)
            if all(key):
                candidate_keys.add(key)
    return [(key in edges_a, key in edges_b) for key in sorted(candidate_keys)]


def evidence_agreement(row_a, row_b):
    edges_a = {edge_key(edge): evidence_ids(edge) for edge in row_a.get("gold_edges") or []}
    edges_b = {edge_key(edge): evidence_ids(edge) for edge in row_b.get("gold_edges") or []}
    matched = sorted(set(edges_a) & set(edges_b))
    if not matched:
        return {"matched_edges": 0, "mean_evidence_jaccard": None}
    scores = []
    for key in matched:
        a_ids = edges_a[key]
        b_ids = edges_b[key]
        if not a_ids and not b_ids:
            scores.append(1.0)
        elif not a_ids or not b_ids:
            scores.append(0.0)
        else:
            scores.append(len(a_ids & b_ids) / len(a_ids | b_ids))
    return {"matched_edges": len(matched), "mean_evidence_jaccard": round(sum(scores) / len(scores), 6)}


def compute(annotator_a, annotator_b):
    rows_a = {row["chunk_id"]: row for row in read_jsonl(annotator_a)}
    rows_b = {row["chunk_id"]: row for row in read_jsonl(annotator_b)}
    shared_ids = sorted(set(rows_a) & set(rows_b))
    completed_ids = [chunk_id for chunk_id in shared_ids if row_completed(rows_a[chunk_id]) and row_completed(rows_b[chunk_id])]

    pending = len(shared_ids) - len(completed_ids)
    if not completed_ids:
        return {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "annotator_a": str(annotator_a),
            "annotator_b": str(annotator_b),
            "shared_chunks": len(shared_ids),
            "completed_pair_chunks": 0,
            "pending_pair_chunks": pending,
            "status": "pending_human_annotations",
            "metrics": None,
            "disagreement_chunks": [],
        }

    all_edges_a = set()
    all_edges_b = set()
    all_nodes_a = set()
    all_nodes_b = set()
    candidate_pairs = []
    evidence_scores = []
    disagreement_chunks = []

    for chunk_id in completed_ids:
        row_a = rows_a[chunk_id]
        row_b = rows_b[chunk_id]
        edges_a = {edge_key(edge) for edge in row_a.get("gold_edges") or []}
        edges_b = {edge_key(edge) for edge in row_b.get("gold_edges") or []}
        nodes_a = {node_key(node) for node in row_a.get("gold_nodes") or []}
        nodes_b = {node_key(node) for node in row_b.get("gold_nodes") or []}
        all_edges_a |= {(chunk_id,) + key for key in edges_a}
        all_edges_b |= {(chunk_id,) + key for key in edges_b}
        all_nodes_a |= {(chunk_id,) + key for key in nodes_a}
        all_nodes_b |= {(chunk_id,) + key for key in nodes_b}
        candidate_pairs.extend(accepted_candidate_pairs(row_a, row_b, edges_a, edges_b))
        ev = evidence_agreement(row_a, row_b)
        if ev["mean_evidence_jaccard"] is not None:
            evidence_scores.append(ev["mean_evidence_jaccard"])
        if edges_a != edges_b or nodes_a != nodes_b:
            disagreement_chunks.append(
                {
                    "chunk_id": chunk_id,
                    "edge_only_a": [list(key) for key in sorted(edges_a - edges_b)],
                    "edge_only_b": [list(key) for key in sorted(edges_b - edges_a)],
                    "node_only_a": [list(key) for key in sorted(nodes_a - nodes_b)],
                    "node_only_b": [list(key) for key in sorted(nodes_b - nodes_a)],
                }
            )

    metrics = {
        "edge_exact": f1(all_edges_a, all_edges_b),
        "node_exact": f1(all_nodes_a, all_nodes_b),
        "candidate_acceptance_kappa": cohen_kappa(candidate_pairs),
        "candidate_decisions": len(candidate_pairs),
        "mean_evidence_jaccard_on_matched_edges": round(sum(evidence_scores) / len(evidence_scores), 6)
        if evidence_scores
        else None,
    }
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "annotator_a": str(annotator_a),
        "annotator_b": str(annotator_b),
        "shared_chunks": len(shared_ids),
        "completed_pair_chunks": len(completed_ids),
        "pending_pair_chunks": pending,
        "status": "computed",
        "metrics": metrics,
        "disagreement_chunks": disagreement_chunks,
    }


def report_text(summary):
    lines = [
        "# CAPE-KG Annotation IAA Report",
        "",
        f"Generated: {summary['generated_at_utc']}",
        "",
        "## Inputs",
        "",
        f"- Annotator A: `{summary['annotator_a']}`",
        f"- Annotator B: `{summary['annotator_b']}`",
        f"- Shared chunks: {summary['shared_chunks']}",
        f"- Completed paired chunks: {summary['completed_pair_chunks']}",
        f"- Pending paired chunks: {summary['pending_pair_chunks']}",
        "",
    ]
    if summary["metrics"] is None:
        lines.extend(
            [
                "## Status",
                "",
                "No paired completed human annotations were found. Agreement is pending.",
                "",
            ]
        )
    else:
        metrics = summary["metrics"]
        lines.extend(
            [
                "## Metrics",
                "",
                f"- Edge exact F1: {metrics['edge_exact']['f1']}",
                f"- Node exact F1: {metrics['node_exact']['f1']}",
                f"- Candidate acceptance Cohen kappa: {metrics['candidate_acceptance_kappa']}",
                f"- Candidate decisions: {metrics['candidate_decisions']}",
                f"- Matched-edge evidence Jaccard: {metrics['mean_evidence_jaccard_on_matched_edges']}",
                f"- Disagreement chunks: {len(summary['disagreement_chunks'])}",
                "",
            ]
        )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotator-a", required=True)
    parser.add_argument("--annotator-b", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    summary = compute(Path(args.annotator_a), Path(args.annotator_b))
    write_json(output_dir / "iaa_summary.json", summary)
    write_text(output_dir / "iaa_report.md", report_text(summary))
    write_json(output_dir / "disagreement_chunks.json", summary.get("disagreement_chunks", []))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
