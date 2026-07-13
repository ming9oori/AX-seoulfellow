#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a JSONL/CSV evidence graph projection for CAPE-KG.

The canonical Layer 2 graph stores evidence as `evidence_anchor_ids` on nodes
and edges. This script materializes those anchors as first-class
`EvidenceAnchor` rows and `EVIDENCED_BY` links for tools that expect explicit
graph objects. It intentionally omits full source sentence text.
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


def read_jsonl(path):
    path = Path(path)
    rows = []
    if not path.exists():
        return rows
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
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            f.write("\n")


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


def as_list(value):
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def short_hash(value, length=16):
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:length]


def text_sha256(value):
    if value in (None, ""):
        return ""
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def evidence_edge_id(source_kind, source_id, target_id):
    return "EVEDGE-" + short_hash(f"{source_kind}|{source_id}|EVIDENCED_BY|{target_id}", 20)


def build_projection(exp_dir, outputs_dir):
    exp_dir = Path(exp_dir)
    outputs_dir = Path(outputs_dir)
    out_dir = outputs_dir / "13_evidence_graph"
    nodes = read_jsonl(outputs_dir / "07_layer2_graph/layer2_nodes.jsonl")
    edges = read_jsonl(outputs_dir / "07_layer2_graph/layer2_edges.jsonl")
    anchors = read_jsonl(outputs_dir / "06_triples/evidence_anchors.jsonl")
    anchor_by_id = {row.get("evidence_anchor_id"): row for row in anchors if row.get("evidence_anchor_id")}

    used_anchor_ids = set()
    for row in nodes:
        used_anchor_ids.update(as_list(row.get("evidence_anchor_ids")))
    for row in edges:
        used_anchor_ids.update(as_list(row.get("evidence_anchor_ids")))
    used_anchor_ids = {anchor_id for anchor_id in used_anchor_ids if anchor_id}

    evidence_nodes = []
    unknown_anchor_ids = []
    for anchor_id in sorted(used_anchor_ids):
        meta = anchor_by_id.get(anchor_id) or {}
        if not meta:
            unknown_anchor_ids.append(anchor_id)
        source_text = meta.get("text") or ""
        sentence_id = meta.get("sentence_id") or anchor_id.replace("EA-", "", 1)
        evidence_nodes.append(
            {
                "node_id": anchor_id,
                "type": "EvidenceAnchor",
                "layer": "EvidenceProjection",
                "label": sentence_id,
                "evidence_anchor_id": anchor_id,
                "sentence_id": sentence_id,
                "chunk_id": meta.get("chunk_id"),
                "page": meta.get("page"),
                "zone": meta.get("zone"),
                "span_start": meta.get("span_start"),
                "span_end": meta.get("span_end"),
                "anchor_exact": meta.get("anchor_exact"),
                "text_included": False,
                "text_char_count": len(source_text),
                "text_sha256": text_sha256(source_text),
                "source": "evidence_anchor_catalog",
                "review_status": "source_text_omitted_projection",
            }
        )

    evidenced_by_edges = []
    for row in nodes:
        source_id = row.get("node_id")
        for anchor_id in as_list(row.get("evidence_anchor_ids")):
            if not anchor_id:
                continue
            evidenced_by_edges.append(
                {
                    "evidence_edge_id": evidence_edge_id("KGNode", source_id, anchor_id),
                    "source_kind": "KGNode",
                    "source_id": source_id,
                    "source_label": row.get("label"),
                    "source_type": row.get("type"),
                    "predicate": "EVIDENCED_BY",
                    "target_id": anchor_id,
                    "target_type": "EvidenceAnchor",
                    "layer": "EvidenceProjection",
                    "confidence": 1.0,
                    "review_status": "projection_from_node_evidence_anchor_ids",
                    "source_kg_edge_source_id": "",
                    "source_kg_edge_target_id": "",
                    "source_kg_edge_predicate": "",
                }
            )

    for row in edges:
        source_id = row.get("edge_id")
        label = f"{row.get('source_id')} {row.get('predicate')} {row.get('target_id')}"
        for anchor_id in as_list(row.get("evidence_anchor_ids")):
            if not anchor_id:
                continue
            evidenced_by_edges.append(
                {
                    "evidence_edge_id": evidence_edge_id("KGEdge", source_id, anchor_id),
                    "source_kind": "KGEdge",
                    "source_id": source_id,
                    "source_label": label,
                    "source_type": "KGEdge",
                    "predicate": "EVIDENCED_BY",
                    "target_id": anchor_id,
                    "target_type": "EvidenceAnchor",
                    "layer": "EvidenceProjection",
                    "confidence": row.get("confidence"),
                    "review_status": "projection_from_edge_evidence_anchor_ids",
                    "source_kg_edge_source_id": row.get("source_id"),
                    "source_kg_edge_target_id": row.get("target_id"),
                    "source_kg_edge_predicate": row.get("predicate"),
                }
            )

    source_kind_counts = Counter(row["source_kind"] for row in evidenced_by_edges)
    anchor_zone_counts = Counter(str(row.get("zone") or "") for row in evidence_nodes)
    output_paths = {
        "evidence_anchor_nodes_jsonl": out_dir / "evidence_anchor_nodes.jsonl",
        "evidence_anchor_nodes_csv": out_dir / "evidence_anchor_nodes.csv",
        "evidenced_by_edges_jsonl": out_dir / "evidenced_by_edges.jsonl",
        "evidenced_by_edges_csv": out_dir / "evidenced_by_edges.csv",
        "summary_json": out_dir / "evidence_graph_projection_summary.json",
        "report_md": out_dir / "evidence_graph_projection_report.md",
    }
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": rel(exp_dir),
        "outputs_dir": rel(outputs_dir),
        "claim_status": "evidence_graph_projection_ready_not_human_gold_span_claim",
        "source_text_included": False,
        "layer2_node_count": len(nodes),
        "layer2_edge_count": len(edges),
        "evidence_anchor_catalog_count": len(anchor_by_id),
        "used_evidence_anchor_count": len(used_anchor_ids),
        "evidence_anchor_node_count": len(evidence_nodes),
        "evidenced_by_edge_count": len(evidenced_by_edges),
        "kg_node_evidenced_by_edge_count": source_kind_counts.get("KGNode", 0),
        "kg_edge_evidenced_by_edge_count": source_kind_counts.get("KGEdge", 0),
        "unknown_used_evidence_anchor_count": len(unknown_anchor_ids),
        "unknown_used_evidence_anchor_ids": unknown_anchor_ids[:100],
        "anchor_zone_counts": dict(sorted(anchor_zone_counts.items())),
        "outputs": {key: rel(path) for key, path in output_paths.items()},
        "interpretation": [
            "This projection materializes EvidenceAnchor and EVIDENCED_BY for JSONL/CSV graph tools.",
            "It does not replace the canonical Layer 2 node/edge files.",
            "Full source sentence text is intentionally omitted; use the internal evidence catalog when allowed.",
            "Final evidence-span correctness still requires adjudicated human-gold span scoring.",
        ],
    }

    return evidence_nodes, evidenced_by_edges, summary, output_paths


def render_report(summary):
    lines = [
        "# CAPE-KG Evidence Graph Projection",
        "",
        f"Generated: {summary['generated_at_utc']}",
        f"Claim status: `{summary['claim_status']}`",
        "",
        "This artifact materializes evidence anchors as graph objects for JSONL/CSV workflows. It is structural/reproducibility evidence, not a human-gold span-quality claim.",
        "",
        "## Summary",
        "",
        "| Item | Value |",
        "|---|---:|",
    ]
    for key in [
        "source_text_included",
        "layer2_node_count",
        "layer2_edge_count",
        "evidence_anchor_catalog_count",
        "used_evidence_anchor_count",
        "evidence_anchor_node_count",
        "evidenced_by_edge_count",
        "kg_node_evidenced_by_edge_count",
        "kg_edge_evidenced_by_edge_count",
        "unknown_used_evidence_anchor_count",
    ]:
        lines.append(f"| {key} | {summary[key]} |")
    lines += [
        "",
        "## Outputs",
        "",
        "| Artifact | Path |",
        "|---|---|",
    ]
    for key, path in summary["outputs"].items():
        lines.append(f"| {key} | `{path}` |")
    lines += [
        "",
        "## Interpretation",
        "",
    ]
    for item in summary["interpretation"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def run(args):
    evidence_nodes, evidenced_by_edges, summary, output_paths = build_projection(args.experiment_dir, args.outputs_dir)
    node_fields = [
        "node_id",
        "type",
        "layer",
        "label",
        "evidence_anchor_id",
        "sentence_id",
        "chunk_id",
        "page",
        "zone",
        "span_start",
        "span_end",
        "anchor_exact",
        "text_included",
        "text_char_count",
        "text_sha256",
        "source",
        "review_status",
    ]
    edge_fields = [
        "evidence_edge_id",
        "source_kind",
        "source_id",
        "source_label",
        "source_type",
        "predicate",
        "target_id",
        "target_type",
        "layer",
        "confidence",
        "review_status",
        "source_kg_edge_source_id",
        "source_kg_edge_target_id",
        "source_kg_edge_predicate",
    ]
    write_jsonl(output_paths["evidence_anchor_nodes_jsonl"], evidence_nodes)
    write_csv(output_paths["evidence_anchor_nodes_csv"], evidence_nodes, node_fields)
    write_jsonl(output_paths["evidenced_by_edges_jsonl"], evidenced_by_edges)
    write_csv(output_paths["evidenced_by_edges_csv"], evidenced_by_edges, edge_fields)
    write_json(output_paths["summary_json"], summary)
    write_text(output_paths["report_md"], render_report(summary))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--outputs-dir", default=str(DEFAULT_OUTPUTS_DIR))
    run(parser.parse_args())


if __name__ == "__main__":
    main()
