#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build public-safe synthetic examples for the CAPE-KG EACL package."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def example_rows():
    chunks = [
        {
            "chunk_id": "SYN-CHUNK-001",
            "chunk_text": (
                "The proposal manager reviews the customer request, records key needs, "
                "and asks the capture lead to prepare a capture plan."
            ),
            "chapter_id": "SYN-CH",
            "section_id": "SYN-SEC-01",
            "page_start": 1,
            "page_end": 1,
            "source_kind": "synthetic_public_example",
        },
        {
            "chunk_id": "SYN-CHUNK-002",
            "chunk_text": (
                "After the draft outline is approved, section writers prepare response sections. "
                "A review checkpoint checks evidence, compliance, and risk items."
            ),
            "chapter_id": "SYN-CH",
            "section_id": "SYN-SEC-02",
            "page_start": 2,
            "page_end": 2,
            "source_kind": "synthetic_public_example",
        },
    ]
    nodes = [
        {"node_id": "SYN-TASK-CAPTURE", "type": "DomainTask", "label": "Capture planning"},
        {"node_id": "SYN-STEP-REVIEW-REQUEST", "type": "ProcedureStep", "label": "Review customer request"},
        {"node_id": "SYN-ARTIFACT-CAPTURE-PLAN", "type": "Artifact", "label": "Capture plan"},
        {"node_id": "SYN-ROLE-PROPOSAL-MANAGER", "type": "Role", "label": "Proposal manager"},
        {"node_id": "SYN-TASK-PROPOSAL-DRAFT", "type": "DomainTask", "label": "Proposal draft preparation"},
        {"node_id": "SYN-STEP-WRITE-SECTIONS", "type": "ProcedureStep", "label": "Write response sections"},
        {"node_id": "SYN-CHECKPOINT-EVIDENCE", "type": "ReviewCheckpoint", "label": "Evidence and compliance review"},
        {"node_id": "SYN-RISK-UNSUPPORTED-CLAIM", "type": "Risk", "label": "Unsupported claim risk"},
    ]
    evidence = [
        {
            "evidence_id": "SYN-EA-001",
            "chunk_id": "SYN-CHUNK-001",
            "sentence_id": "SYN-SENT-001",
            "start_char": 0,
            "end_char": len(chunks[0]["chunk_text"]),
            "text": chunks[0]["chunk_text"],
        },
        {
            "evidence_id": "SYN-EA-002",
            "chunk_id": "SYN-CHUNK-002",
            "sentence_id": "SYN-SENT-002",
            "start_char": 0,
            "end_char": len(chunks[1]["chunk_text"]),
            "text": chunks[1]["chunk_text"],
        },
    ]
    edges = [
        {
            "edge_id": "SYN-EDGE-001",
            "source_id": "SYN-TASK-CAPTURE",
            "target_id": "SYN-STEP-REVIEW-REQUEST",
            "predicate": "HAS_STEP",
            "evidence_anchor_ids": ["SYN-EA-001"],
        },
        {
            "edge_id": "SYN-EDGE-002",
            "source_id": "SYN-STEP-REVIEW-REQUEST",
            "target_id": "SYN-ARTIFACT-CAPTURE-PLAN",
            "predicate": "PRODUCES",
            "evidence_anchor_ids": ["SYN-EA-001"],
        },
        {
            "edge_id": "SYN-EDGE-003",
            "source_id": "SYN-STEP-REVIEW-REQUEST",
            "target_id": "SYN-ROLE-PROPOSAL-MANAGER",
            "predicate": "PERFORMED_BY",
            "evidence_anchor_ids": ["SYN-EA-001"],
        },
        {
            "edge_id": "SYN-EDGE-004",
            "source_id": "SYN-TASK-PROPOSAL-DRAFT",
            "target_id": "SYN-STEP-WRITE-SECTIONS",
            "predicate": "HAS_STEP",
            "evidence_anchor_ids": ["SYN-EA-002"],
        },
        {
            "edge_id": "SYN-EDGE-005",
            "source_id": "SYN-STEP-WRITE-SECTIONS",
            "target_id": "SYN-CHECKPOINT-EVIDENCE",
            "predicate": "PRECEDES",
            "evidence_anchor_ids": ["SYN-EA-002"],
        },
        {
            "edge_id": "SYN-EDGE-006",
            "source_id": "SYN-STEP-WRITE-SECTIONS",
            "target_id": "SYN-RISK-UNSUPPORTED-CLAIM",
            "predicate": "HAS_RISK",
            "evidence_anchor_ids": ["SYN-EA-002"],
        },
    ]
    annotation_rows = [
        {
            "annotation_status": "completed",
            "reviewer_id": "synthetic_reference",
            "chunk_id": chunk["chunk_id"],
            "chunk_text": chunk["chunk_text"],
            "chapter_id": chunk["chapter_id"],
            "section_id": chunk["section_id"],
            "page_start": chunk["page_start"],
            "page_end": chunk["page_end"],
            "package": "public_synthetic_examples",
            "gold_nodes": [node for node in nodes if node["node_id"] in {
                "SYN-TASK-CAPTURE",
                "SYN-STEP-REVIEW-REQUEST",
                "SYN-ARTIFACT-CAPTURE-PLAN",
                "SYN-ROLE-PROPOSAL-MANAGER",
            }] if chunk["chunk_id"] == "SYN-CHUNK-001" else [node for node in nodes if node["node_id"] in {
                "SYN-TASK-PROPOSAL-DRAFT",
                "SYN-STEP-WRITE-SECTIONS",
                "SYN-CHECKPOINT-EVIDENCE",
                "SYN-RISK-UNSUPPORTED-CLAIM",
            }],
            "gold_edges": [edge for edge in edges if edge["evidence_anchor_ids"][0] == ("SYN-EA-001" if chunk["chunk_id"] == "SYN-CHUNK-001" else "SYN-EA-002")],
            "evidence_anchors": [ev for ev in evidence if ev["chunk_id"] == chunk["chunk_id"]],
            "comments": "Synthetic public example only; not source-corpus data.",
        }
        for chunk in chunks
    ]
    prediction_rows = [
        {
            "condition": "P_cape_kg_synthetic_example",
            "chunk_id": chunk["chunk_id"],
            "nodes": row["gold_nodes"],
            "edges": row["gold_edges"],
            "evidence_anchors": row["evidence_anchors"],
            "claim_status": "synthetic_example_not_paper_result",
        }
        for chunk, row in zip(chunks, annotation_rows)
    ]
    return chunks, annotation_rows, prediction_rows, nodes, edges, evidence


def validate(schema, nodes, edges, evidence):
    node_types = set(schema.get("node_types") or [])
    edge_types = set(schema.get("edge_types") or [])
    domain_range = schema.get("domain_range") or {}
    by_node = {node["node_id"]: node for node in nodes}
    evidence_ids = {row["evidence_id"] for row in evidence}
    issues = []
    for node in nodes:
        if node.get("type") not in node_types:
            issues.append({"level": "error", "code": "invalid_node_type", "node_id": node.get("node_id"), "type": node.get("type")})
    for edge in edges:
        predicate = edge.get("predicate")
        if predicate not in edge_types:
            issues.append({"level": "error", "code": "invalid_edge_type", "edge_id": edge.get("edge_id"), "predicate": predicate})
            continue
        source = by_node.get(edge.get("source_id"))
        target = by_node.get(edge.get("target_id"))
        if not source or not target:
            issues.append({"level": "error", "code": "unknown_edge_endpoint", "edge_id": edge.get("edge_id")})
            continue
        rule = domain_range.get(predicate) or {}
        allowed_sources = set(rule.get("subject_types") or [])
        allowed_targets = set(rule.get("object_types") or [])
        if allowed_sources and "Any" not in allowed_sources and source.get("type") not in allowed_sources:
            issues.append({"level": "error", "code": "source_type_violation", "edge_id": edge.get("edge_id")})
        if allowed_targets and "Any" not in allowed_targets and target.get("type") not in allowed_targets:
            issues.append({"level": "error", "code": "target_type_violation", "edge_id": edge.get("edge_id")})
        for evidence_id in edge.get("evidence_anchor_ids") or []:
            if evidence_id not in evidence_ids:
                issues.append({"level": "error", "code": "unknown_evidence_anchor", "edge_id": edge.get("edge_id"), "evidence_id": evidence_id})
    return issues


def build_readme(payload):
    return "\n".join([
        "# Public Synthetic CAPE-KG Examples",
        "",
        "These files are synthetic examples for public reproducibility checks.",
        "They are not copied, paraphrased, or derived from the private/source corpus.",
        "",
        "## Files",
        "",
        "- `synthetic_chunks.jsonl`: toy public-safe input chunks.",
        "- `synthetic_gold.jsonl`: toy gold annotation rows using the CAPE node, edge, and evidence-anchor shape.",
        "- `synthetic_predictions.jsonl`: toy prediction rows in the CAPE output shape.",
        "- `synthetic_evaluation_summary.json`: schema validation and count summary.",
        "",
        "## Intended Use",
        "",
        "Use this package to inspect the expected JSONL structure, evidence anchors, and schema-conformant procedural edges without exposing copyrighted source text.",
        "It is a format and release-safety artifact only; it is not a paper result and must not be mixed with human-gold evaluation.",
        "",
        "## Summary",
        "",
        f"- Synthetic chunks: {payload['synthetic_chunk_count']}",
        f"- Synthetic nodes: {payload['synthetic_node_count']}",
        f"- Synthetic edges: {payload['synthetic_edge_count']}",
        f"- Validation errors: {payload['validation_error_count']}",
        f"- Claim status: `{payload['claim_status']}`",
        "",
    ])


def run(args):
    exp_dir = Path(args.experiment_dir)
    out_dir = exp_dir / "06_release/public_synthetic_examples"
    schema = read_json(exp_dir / "02_schema/cape_schema.json")
    chunks, annotation_rows, prediction_rows, nodes, edges, evidence = example_rows()
    issues = validate(schema, nodes, edges, evidence)
    errors = [row for row in issues if row.get("level") == "error"]
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "output_dir": str(out_dir),
        "synthetic_chunk_count": len(chunks),
        "synthetic_node_count": len(nodes),
        "synthetic_edge_count": len(edges),
        "synthetic_evidence_anchor_count": len(evidence),
        "validation_error_count": len(errors),
        "validation_issue_count": len(issues),
        "validation_issues": issues,
        "source_text_policy": "synthetic_only_no_source_corpus_text",
        "claim_status": "public_format_example_not_paper_result",
        "files": {
            "readme": str(out_dir / "README.md"),
            "chunks": str(out_dir / "synthetic_chunks.jsonl"),
            "gold": str(out_dir / "synthetic_gold.jsonl"),
            "predictions": str(out_dir / "synthetic_predictions.jsonl"),
            "summary": str(out_dir / "synthetic_evaluation_summary.json"),
        },
    }
    write_jsonl(out_dir / "synthetic_chunks.jsonl", chunks)
    write_jsonl(out_dir / "synthetic_gold.jsonl", annotation_rows)
    write_jsonl(out_dir / "synthetic_predictions.jsonl", prediction_rows)
    write_json(out_dir / "synthetic_evaluation_summary.json", payload)
    write_text(out_dir / "README.md", build_readme(payload))
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    if errors:
        raise SystemExit(2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
