#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prepare an adjudication draft from two CAPE-KG annotation files.

The output is a draft, not a substitute for human adjudication. Chunks with
perfect A/B agreement can be marked as no-disagreement adjudicated; chunks with
any node, edge, or evidence disagreement are left for an adjudicator.
"""

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
COMPLETED_STATUSES = {"completed", "needs_adjudication", "adjudicated"}


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


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


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


def norm_evidence_id(value):
    value = str(value or "").strip()
    if value.startswith("EA-"):
        value = value[3:]
    return value


def row_completed(row):
    return row.get("annotation_status") in COMPLETED_STATUSES


def node_key(node):
    return (
        norm(node.get("type")),
        norm(node.get("node_id") or node.get("label")),
    )


def edge_key(edge):
    return (
        norm(edge.get("source_id") or edge.get("source_label") or edge.get("subject")),
        norm(edge.get("predicate") or edge.get("edge_type")),
        norm(edge.get("target_id") or edge.get("target_label") or edge.get("object")),
    )


def evidence_ids(item):
    ids = set()
    for value in item.get("evidence_anchor_ids") or []:
        normalized = norm_evidence_id(value)
        if normalized:
            ids.add(normalized)
    for span in item.get("evidence_spans") or []:
        normalized = norm_evidence_id(span.get("evidence_anchor_id") or span.get("sentence_id"))
        if normalized:
            ids.add(normalized)
    return ids


def keyed_items(items, key_fn):
    by_key = {}
    duplicates = Counter()
    for item in items or []:
        key = key_fn(item)
        if not all(key):
            continue
        if key in by_key:
            duplicates[key] += 1
            continue
        by_key[key] = item
    return by_key, duplicates


def base_adjudication_row(row_a, row_b, template_row, package_name):
    source = template_row or row_a or row_b or {}
    return {
        "package": source.get("package") or package_name,
        "chunk_id": source.get("chunk_id"),
        "chapter_id": source.get("chapter_id"),
        "section_id": source.get("section_id"),
        "page_start": source.get("page_start"),
        "page_end": source.get("page_end"),
        "chunk_text": source.get("chunk_text"),
        "annotator_a_status": (row_a or {}).get("annotation_status", "missing"),
        "annotator_b_status": (row_b or {}).get("annotation_status", "missing"),
        "disagreement_items": [],
        "adjudicated_gold_nodes": [],
        "adjudicated_gold_edges": [],
        "adjudicator_id": "",
        "adjudication_status": "pending_two_annotator_input",
        "adjudication_notes": "",
        "draft_generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def disagreement(kind, issue, key, item_a=None, item_b=None, extra=None):
    row = {
        "kind": kind,
        "issue": issue,
        "key": list(key),
        "annotator_a_item": item_a,
        "annotator_b_item": item_b,
    }
    if extra:
        row.update(extra)
    return row


def merge_completed_pair(row_a, row_b, template_row, package_name):
    out = base_adjudication_row(row_a, row_b, template_row, package_name)
    nodes_a, dup_nodes_a = keyed_items(row_a.get("gold_nodes", []), node_key)
    nodes_b, dup_nodes_b = keyed_items(row_b.get("gold_nodes", []), node_key)
    edges_a, dup_edges_a = keyed_items(row_a.get("gold_edges", []), edge_key)
    edges_b, dup_edges_b = keyed_items(row_b.get("gold_edges", []), edge_key)

    for key, item in sorted(nodes_a.items()):
        if key in nodes_b:
            out["adjudicated_gold_nodes"].append(item)
        else:
            out["disagreement_items"].append(disagreement("node", "only_annotator_a", key, item_a=item))
    for key, item in sorted(nodes_b.items()):
        if key not in nodes_a:
            out["disagreement_items"].append(disagreement("node", "only_annotator_b", key, item_b=item))

    for key, item in sorted(edges_a.items()):
        if key not in edges_b:
            out["disagreement_items"].append(disagreement("edge", "only_annotator_a", key, item_a=item))
            continue
        other = edges_b[key]
        evidence_a = evidence_ids(item)
        evidence_b = evidence_ids(other)
        if evidence_a == evidence_b:
            out["adjudicated_gold_edges"].append(item)
        else:
            out["disagreement_items"].append(
                disagreement(
                    "edge",
                    "evidence_mismatch",
                    key,
                    item_a=item,
                    item_b=other,
                    extra={
                        "annotator_a_evidence_ids": sorted(evidence_a),
                        "annotator_b_evidence_ids": sorted(evidence_b),
                    },
                )
            )
    for key, item in sorted(edges_b.items()):
        if key not in edges_a:
            out["disagreement_items"].append(disagreement("edge", "only_annotator_b", key, item_b=item))

    for key, count in dup_nodes_a.items():
        out["disagreement_items"].append(disagreement("node", "duplicate_annotator_a", key, extra={"duplicate_count": count + 1}))
    for key, count in dup_nodes_b.items():
        out["disagreement_items"].append(disagreement("node", "duplicate_annotator_b", key, extra={"duplicate_count": count + 1}))
    for key, count in dup_edges_a.items():
        out["disagreement_items"].append(disagreement("edge", "duplicate_annotator_a", key, extra={"duplicate_count": count + 1}))
    for key, count in dup_edges_b.items():
        out["disagreement_items"].append(disagreement("edge", "duplicate_annotator_b", key, extra={"duplicate_count": count + 1}))

    if out["disagreement_items"]:
        out["adjudication_status"] = "needs_adjudication"
        out["adjudication_notes"] = "Draft contains A/B disagreements; adjudicator must resolve before scoring."
    else:
        out["adjudication_status"] = "no_disagreement_adjudicated"
        out["adjudication_notes"] = "Auto-filled from exact A/B agreement; review before final paper scoring."
    out["disagreement_count"] = len(out["disagreement_items"])
    return out


def build_draft(annotator_a, annotator_b, template_file, package_name):
    rows_a = {row["chunk_id"]: row for row in read_jsonl(annotator_a)}
    rows_b = {row["chunk_id"]: row for row in read_jsonl(annotator_b)}
    template_rows = read_jsonl(template_file)
    template_by_chunk = {row["chunk_id"]: row for row in template_rows}
    chunk_ids = [row["chunk_id"] for row in template_rows] or sorted(set(rows_a) | set(rows_b))

    output_rows = []
    status_counts = Counter()
    disagreement_counts = Counter()
    completed_pair_chunks = 0
    auto_adjudicated_chunks = 0
    needs_adjudication_chunks = 0
    pending_pair_chunks = 0
    agreed_nodes = 0
    agreed_edges = 0

    for chunk_id in chunk_ids:
        row_a = rows_a.get(chunk_id)
        row_b = rows_b.get(chunk_id)
        template_row = template_by_chunk.get(chunk_id)
        if row_a and row_b and row_completed(row_a) and row_completed(row_b):
            completed_pair_chunks += 1
            out = merge_completed_pair(row_a, row_b, template_row, package_name)
            if out["adjudication_status"] == "no_disagreement_adjudicated":
                auto_adjudicated_chunks += 1
            else:
                needs_adjudication_chunks += 1
            for item in out["disagreement_items"]:
                disagreement_counts[f"{item['kind']}:{item['issue']}"] += 1
            agreed_nodes += len(out["adjudicated_gold_nodes"])
            agreed_edges += len(out["adjudicated_gold_edges"])
        else:
            pending_pair_chunks += 1
            out = base_adjudication_row(row_a, row_b, template_row, package_name)
        status_counts[out["adjudication_status"]] += 1
        output_rows.append(out)

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "annotator_a": str(annotator_a),
        "annotator_b": str(annotator_b),
        "template_file": str(template_file),
        "package": package_name,
        "total_chunks": len(output_rows),
        "completed_pair_chunks": completed_pair_chunks,
        "pending_pair_chunks": pending_pair_chunks,
        "auto_adjudicated_chunks": auto_adjudicated_chunks,
        "needs_adjudication_chunks": needs_adjudication_chunks,
        "agreed_gold_nodes_in_draft": agreed_nodes,
        "agreed_gold_edges_in_draft": agreed_edges,
        "status_counts": dict(sorted(status_counts.items())),
        "disagreement_counts": dict(sorted(disagreement_counts.items())),
        "claim_status": "draft_not_final_human_gold",
    }
    return output_rows, summary


def report_text(summary):
    output_file = summary.get("output_file", "experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/adjudication_draft.jsonl")
    lines = [
        "# CAPE-KG Adjudication Draft Report",
        "",
        f"Generated: {summary['generated_at_utc']}",
        "",
        "This draft is generated from two annotator files. It is not final gold until an adjudicator reviews it.",
        "",
        "## Summary",
        "",
        f"- Package: {summary['package']}",
        f"- Total chunks: {summary['total_chunks']}",
        f"- Completed A/B pair chunks: {summary['completed_pair_chunks']}",
        f"- Pending A/B pair chunks: {summary['pending_pair_chunks']}",
        f"- Auto-adjudicated no-disagreement chunks: {summary['auto_adjudicated_chunks']}",
        f"- Chunks needing adjudication: {summary['needs_adjudication_chunks']}",
        f"- Agreed gold nodes in draft: {summary['agreed_gold_nodes_in_draft']}",
        f"- Agreed gold edges in draft: {summary['agreed_gold_edges_in_draft']}",
        "",
        "## Status Counts",
        "",
    ]
    for key, value in summary["status_counts"].items():
        lines.append(f"- {key}: {value}")
    if summary["disagreement_counts"]:
        lines += ["", "## Disagreement Counts", ""]
        for key, value in summary["disagreement_counts"].items():
            lines.append(f"- {key}: {value}")
    lines += [
        "",
        "## Next Command",
        "",
        "After adjudicator review, validate and score with:",
        "",
        "```bash",
        f"python3 scripts/evaluate_cape_human_gold.py --experiment-dir experiments/cape_kg_eacl_20260627 --adjudication-file {output_file}",
        "```",
        "",
    ]
    return "\n".join(lines)


def run(args):
    exp_dir = Path(args.experiment_dir)
    package_dir = exp_dir / "01_data/gold_annotation" / args.package
    annotator_a = Path(args.annotator_a) if args.annotator_a else package_dir / "annotator_A.jsonl"
    annotator_b = Path(args.annotator_b) if args.annotator_b else package_dir / "annotator_B.jsonl"
    template_file = Path(args.template_file) if args.template_file else package_dir / "adjudication.jsonl"
    output_file = Path(args.output_file) if args.output_file else package_dir / "adjudication_draft.jsonl"
    summary_file = output_file.with_name("adjudication_draft_summary.json")
    report_file = output_file.with_name("adjudication_draft_report.md")

    rows, summary = build_draft(annotator_a, annotator_b, template_file, args.package)
    summary["output_file"] = str(output_file)
    summary["summary_file"] = str(summary_file)
    summary["report_file"] = str(report_file)
    write_jsonl(output_file, rows)
    write_json(summary_file, summary)
    write_text(report_file, report_text(summary))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--package", default="full_120")
    parser.add_argument("--annotator-a", default="")
    parser.add_argument("--annotator-b", default="")
    parser.add_argument("--template-file", default="")
    parser.add_argument("--output-file", default="")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
