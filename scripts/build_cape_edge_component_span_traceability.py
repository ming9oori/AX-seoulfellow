#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build edge-to-component evidence span traceability for CAPE-KG.

This joins final Layer 2 KG edges with their source triples and the
component-level span diagnostic. It intentionally omits source text and keeps
only hashes, offsets, and metadata, so the artifact can support traceability
without becoming a source-text release.
"""

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_OUTPUTS_DIR = Path("outputs")

CLAIM_STATUS = "edge_component_span_traceability_ready_not_human_gold_span_claim"

CSV_FIELDS = [
    "edge_component_span_link_id",
    "edge_id",
    "source_id",
    "predicate",
    "target_id",
    "triple_id",
    "component",
    "component_label",
    "component_predicate",
    "evidence_anchor_id",
    "sentence_id",
    "chunk_id",
    "page",
    "span_method",
    "span_exact",
    "sentence_span_start",
    "sentence_span_end",
    "chunk_span_start",
    "chunk_span_end",
    "text_included",
    "text_char_count",
    "text_sha256",
    "review_status",
]


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


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in CSV_FIELDS})


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def rel(path):
    return str(Path(path).as_posix())


def as_list(value):
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def text_sha256(value):
    if value in (None, ""):
        return ""
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def short_hash(value, length=20):
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:length]


def link_id(edge_id, triple_id, component, sentence_id, index):
    return "ECSL-" + short_hash(f"{edge_id}|{triple_id}|{component}|{sentence_id}|{index}", 24)


def anchor_lookup(outputs_dir):
    by_sentence = {}
    by_id = {}
    for row in read_jsonl(outputs_dir / "06_triples/evidence_anchors.jsonl"):
        anchor_id = row.get("evidence_anchor_id")
        sentence_id = row.get("sentence_id")
        if anchor_id:
            by_id[anchor_id] = row
        if sentence_id and anchor_id:
            by_sentence[sentence_id] = row
    return by_sentence, by_id


def component_span_rows(outputs_dir):
    rows = read_jsonl(outputs_dir / "06_triples/layer2_triples_component_spans.jsonl")
    by_triple = {}
    for row in rows:
        triple_id = row.get("triple_id")
        if triple_id:
            by_triple[triple_id] = row
    return rows, by_triple


def build_traceability(exp_dir, outputs_dir):
    exp_dir = Path(exp_dir)
    outputs_dir = Path(outputs_dir)
    out_dir = outputs_dir / "13_evidence_graph"
    release_dir = exp_dir / "06_release"

    edges = read_jsonl(outputs_dir / "07_layer2_graph/layer2_edges.jsonl")
    triples, triple_by_id = component_span_rows(outputs_dir)
    anchor_by_sentence, anchor_by_id = anchor_lookup(outputs_dir)

    rows = []
    missing_edge_source_triples = []
    missing_component_span_triples = []
    component_counts = Counter()
    span_method_counts = Counter()
    span_exact_counts = Counter()
    edge_with_links = set()
    linked_triple_ids = set()

    for edge in edges:
        edge_id = edge.get("edge_id")
        source_triple_ids = as_list(edge.get("source_triple_ids"))
        if not source_triple_ids:
            missing_edge_source_triples.append(edge_id)
            continue
        for triple_id in source_triple_ids:
            triple = triple_by_id.get(triple_id)
            if not triple:
                missing_component_span_triples.append({"edge_id": edge_id, "triple_id": triple_id})
                continue
            linked_triple_ids.add(triple_id)
            component_spans = as_list(triple.get("component_evidence_spans"))
            if not component_spans:
                missing_component_span_triples.append({"edge_id": edge_id, "triple_id": triple_id})
                continue
            for idx, span in enumerate(component_spans, start=1):
                component = span.get("component") or ""
                sentence_id = span.get("sentence_id") or ""
                anchor = anchor_by_sentence.get(sentence_id) or {}
                evidence_anchor_id = anchor.get("evidence_anchor_id")
                if not evidence_anchor_id and sentence_id:
                    evidence_anchor_id = f"EA-{sentence_id}"
                source_text = span.get("text") or ""
                row = {
                    "edge_component_span_link_id": link_id(edge_id, triple_id, component, sentence_id, idx),
                    "edge_id": edge_id,
                    "source_id": edge.get("source_id"),
                    "predicate": edge.get("predicate"),
                    "target_id": edge.get("target_id"),
                    "triple_id": triple_id,
                    "component": component,
                    "component_label": span.get("label") or "",
                    "component_predicate": span.get("predicate") or "",
                    "evidence_anchor_id": evidence_anchor_id or "",
                    "sentence_id": sentence_id,
                    "chunk_id": span.get("chunk_id") or anchor.get("chunk_id") or "",
                    "page": span.get("page") if span.get("page") not in (None, "") else anchor.get("page", ""),
                    "span_method": span.get("span_method") or "",
                    "span_exact": bool(span.get("span_exact")),
                    "sentence_span_start": span.get("sentence_span_start", ""),
                    "sentence_span_end": span.get("sentence_span_end", ""),
                    "chunk_span_start": span.get("chunk_span_start", ""),
                    "chunk_span_end": span.get("chunk_span_end", ""),
                    "text_included": False,
                    "text_char_count": len(str(source_text)),
                    "text_sha256": text_sha256(source_text),
                    "review_status": "derived_from_component_span_diagnostic_source_text_omitted",
                }
                rows.append(row)
                edge_with_links.add(edge_id)
                component_counts[component] += 1
                span_method_counts[f"{component}.{row['span_method']}"] += 1
                if row["span_exact"]:
                    span_exact_counts[component] += 1

    final_edge_count = len(edges)
    edge_component_link_count = len(rows)
    exact_component_span_count = sum(span_exact_counts.values())
    chunk_span_count = sum(1 for row in rows if row.get("chunk_span_start") not in (None, ""))
    output_paths = {
        "edge_component_span_links_jsonl": out_dir / "edge_component_span_links.jsonl",
        "edge_component_span_links_csv": out_dir / "edge_component_span_links.csv",
        "traceability_json": release_dir / "edge_component_span_traceability.json",
        "traceability_md": release_dir / "edge_component_span_traceability.md",
    }
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": rel(exp_dir),
        "outputs_dir": rel(outputs_dir),
        "claim_status": CLAIM_STATUS,
        "source_text_included": False,
        "final_layer2_edge_count": final_edge_count,
        "component_span_triple_count": len(triples),
        "edges_with_source_triple_ids": final_edge_count - len(missing_edge_source_triples),
        "edges_with_component_span_links": len(edge_with_links),
        "edge_component_span_link_count": edge_component_link_count,
        "linked_source_triple_count": len(linked_triple_ids),
        "component_count_by_role": dict(sorted(component_counts.items())),
        "span_method_counts": dict(sorted(span_method_counts.items())),
        "exact_component_span_count": exact_component_span_count,
        "exact_component_span_rate": round(exact_component_span_count / edge_component_link_count, 6) if edge_component_link_count else 0.0,
        "chunk_span_count": chunk_span_count,
        "chunk_span_rate": round(chunk_span_count / edge_component_link_count, 6) if edge_component_link_count else 0.0,
        "subject_exact_span_count": span_exact_counts.get("subject", 0),
        "object_exact_span_count": span_exact_counts.get("object", 0),
        "predicate_full_sentence_proxy_count": span_method_counts.get("predicate.full_sentence_proxy", 0),
        "missing_edge_source_triple_count": len(missing_edge_source_triples),
        "missing_component_span_triple_count": len(missing_component_span_triples),
        "missing_edge_source_triples": missing_edge_source_triples[:100],
        "missing_component_span_triples": missing_component_span_triples[:100],
        "evidence_anchor_catalog_count": len(anchor_by_id),
        "outputs": {key: rel(path) for key, path in output_paths.items()},
        "limitations": [
            "Rows join final Layer 2 edges to source triples and automatic component span diagnostics.",
            "Subject/object spans are lexical diagnostics when labels are found in the evidence sentence.",
            "Predicate evidence remains a full-sentence proxy rather than token-level predicate annotation.",
            "No source text is included; text hashes and offsets are provided for traceability.",
            "Final span-quality claims still require adjudicated human-gold span scoring.",
        ],
    }
    return rows, summary, output_paths


def render_report(summary):
    lines = [
        "# CAPE-KG Edge Component Span Traceability",
        "",
        f"Generated: {summary['generated_at_utc']}",
        f"Claim status: `{summary['claim_status']}`",
        "",
        "This artifact links final Layer 2 KG edges to source triples and automatic subject/predicate/object evidence-span diagnostics.",
        "It is a traceability artifact, not a human-gold span-quality result.",
        "Source text is omitted; rows contain offsets, hashes, and metadata only.",
        "",
        "## Summary",
        "",
        "| Item | Value |",
        "|---|---:|",
        f"| Final Layer 2 edges | {summary['final_layer2_edge_count']} |",
        f"| Edges with source triple IDs | {summary['edges_with_source_triple_ids']} |",
        f"| Edges with component span links | {summary['edges_with_component_span_links']} |",
        f"| Edge-component span links | {summary['edge_component_span_link_count']} |",
        f"| Linked source triples | {summary['linked_source_triple_count']} |",
        f"| Exact component spans | {summary['exact_component_span_count']} |",
        f"| Exact component span rate | {summary['exact_component_span_rate']} |",
        f"| Chunk-local spans | {summary['chunk_span_count']} |",
        f"| Chunk-local span rate | {summary['chunk_span_rate']} |",
        f"| Predicate full-sentence proxies | {summary['predicate_full_sentence_proxy_count']} |",
        f"| Missing edge source triples | {summary['missing_edge_source_triple_count']} |",
        f"| Missing component span triples | {summary['missing_component_span_triple_count']} |",
        "",
        "## Component Roles",
        "",
        "| Component | Links |",
        "|---|---:|",
    ]
    for key, value in sorted(summary["component_count_by_role"].items()):
        lines.append(f"| `{key}` | {value} |")
    lines += [
        "",
        "## Span Methods",
        "",
        "| Method | Links |",
        "|---|---:|",
    ]
    for key, value in sorted(summary["span_method_counts"].items()):
        lines.append(f"| `{key}` | {value} |")
    lines += [
        "",
        "## Interpretation",
        "",
        "- Final KG edges can now be traced to source triples and automatic component-level evidence spans.",
        "- The file is useful for reviewer explanation and later human span adjudication.",
        "- Predicate rows remain sentence-level proxy support until human-gold predicate spans are returned.",
        "- Source text is intentionally omitted from JSONL/CSV rows.",
        "",
    ]
    return "\n".join(lines)


def run(args):
    exp_dir = Path(args.experiment_dir)
    outputs_dir = Path(args.outputs_dir)
    rows, summary, output_paths = build_traceability(exp_dir, outputs_dir)
    write_jsonl(output_paths["edge_component_span_links_jsonl"], rows)
    write_csv(output_paths["edge_component_span_links_csv"], rows)
    write_json(output_paths["traceability_json"], summary)
    write_text(output_paths["traceability_md"], render_report(summary))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--outputs-dir", default=str(DEFAULT_OUTPUTS_DIR))
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
