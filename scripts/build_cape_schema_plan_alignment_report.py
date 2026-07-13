#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a plan-vs-current-schema alignment report for CAPE-KG."""

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_OUTPUTS_DIR = Path("outputs")
DEFAULT_PLAN_FILE = Path("AX_EACL_submission_review_revised_plan.md")

EXPECTED_NODE_TYPES = [
    "DomainTask",
    "ProcedureStep",
    "DecisionGateway",
    "GuardCondition",
    "Artifact",
    "ArtifactFlow",
    "Role",
    "ReviewCheckpoint",
    "Principle",
    "Risk",
    "EvidenceAnchor",
    "NCSCompetencyUnit",
    "PCFElement",
    "MappingCandidate",
]

EXPECTED_EDGE_TYPES = [
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
    "EVIDENCED_BY",
    "REQUIRES_CAPABILITY",
    "PROCESS_CONTEXT",
    "CANDIDATE_ALIGNS_WITH",
]

KNOWN_PENDING_TERMS = {
    "BRANCHES_TO",
}


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


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


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def rel(path):
    return str(Path(path).as_posix())


def count_by(rows, key):
    return Counter(row.get(key) for row in rows if row.get(key))


def build_rows(exp_dir, outputs_dir):
    release_dir = exp_dir / "06_release"
    eval_dir = exp_dir / "04_evaluation"

    layer2_nodes = read_jsonl(outputs_dir / "07_layer2_graph/layer2_nodes.jsonl")
    layer2_edges = read_jsonl(outputs_dir / "07_layer2_graph/layer2_edges.jsonl")
    ncs_nodes = read_jsonl(outputs_dir / "01_layer1/layer1_ncs_nodes.jsonl")
    pcf_nodes = read_jsonl(outputs_dir / "01_layer1/layer1_pcf_nodes.jsonl")
    ncs_mappings = read_jsonl(outputs_dir / "08_mapping/l2_ncs_mapping_candidates.jsonl")
    pcf_mappings = read_jsonl(outputs_dir / "08_mapping/l2_pcf_mapping_candidates.jsonl")

    evidence_summary = read_json(outputs_dir / "13_evidence_graph/evidence_graph_projection_summary.json", {}) or {}
    neo4j_manifest = read_json(outputs_dir / "11_neo4j_import/manifest.json", {}) or {}
    structural_summary = read_json(eval_dir / "structural_gap_worklist_summary.json", {}) or {}
    crosswalk_summary = read_json(eval_dir / "ncs_pcf_crosswalk_summary.json", {}) or {}

    node_counts = count_by(layer2_nodes, "type")
    edge_counts = count_by(layer2_edges, "predicate")
    ncs_node_counts = count_by(ncs_nodes, "type")
    pcf_node_counts = count_by(pcf_nodes, "type")
    relationship_types = neo4j_manifest.get("relationship_types") or {}

    mapping_candidate_rows = len(ncs_mappings) + len(pcf_mappings)
    outputs = {
        "canonical_layer2_nodes": rel(outputs_dir / "07_layer2_graph/layer2_nodes.jsonl"),
        "canonical_layer2_edges": rel(outputs_dir / "07_layer2_graph/layer2_edges.jsonl"),
        "evidence_projection_summary": rel(outputs_dir / "13_evidence_graph/evidence_graph_projection_summary.json"),
        "neo4j_manifest": rel(outputs_dir / "11_neo4j_import/manifest.json"),
        "ncs_mapping_candidates": rel(outputs_dir / "08_mapping/l2_ncs_mapping_candidates.jsonl"),
        "pcf_mapping_candidates": rel(outputs_dir / "08_mapping/l2_pcf_mapping_candidates.jsonl"),
        "structural_gap_worklist_summary": rel(eval_dir / "structural_gap_worklist_summary.json"),
        "ncs_pcf_crosswalk_summary": rel(eval_dir / "ncs_pcf_crosswalk_summary.json"),
        "alignment_json": rel(release_dir / "schema_plan_alignment.json"),
        "alignment_md": rel(release_dir / "schema_plan_alignment.md"),
    }

    rows = []
    for term in EXPECTED_NODE_TYPES:
        canonical_count = int(node_counts.get(term, 0))
        represented_count = canonical_count
        represented_in = "canonical_layer2_graph" if canonical_count else ""
        status = "canonical_layer2_present" if canonical_count else "missing_unclassified"
        claim_scope = "canonical Layer 2 KG term"
        evidence_files = [outputs["canonical_layer2_nodes"]]
        notes = ""

        if term == "ReviewCheckpoint" and canonical_count == 0:
            represented_count = int(structural_summary.get("review_checkpoint_candidate_count") or 0)
            represented_in = "structural_review_worklist"
            status = "pending_structural_review"
            claim_scope = "known schema gap tracked for human structural review"
            evidence_files = [
                outputs["structural_gap_worklist_summary"],
                rel(exp_dir / "05_review/structural_review_checkpoint_candidates.csv"),
            ]
            notes = "Canonical graph has no ReviewCheckpoint nodes yet; candidates are prepared for structural review."
        elif term == "ReviewCheckpoint":
            notes = "ReviewCheckpoint nodes are materialized in canonical Layer 2 from review/check/approval-signaled procedure steps; final correctness remains human-gold pending."
        elif term == "EvidenceAnchor":
            represented_count = int(evidence_summary.get("evidence_anchor_node_count") or 0)
            represented_in = "evidence_projection"
            status = "projection_present"
            claim_scope = "noncanonical EvidenceAnchor projection; final span correctness remains human-gold pending"
            evidence_files = [outputs["evidence_projection_summary"]]
            notes = "EvidenceAnchor is materialized in outputs/13_evidence_graph and Neo4j export, not in canonical layer2_nodes.jsonl."
        elif term == "NCSCompetencyUnit":
            represented_count = int(ncs_node_counts.get("NCSCompetencyUnit", 0))
            represented_in = "layer1_ncs_graph_and_mapping_targets"
            status = "layer1_standard_present"
            claim_scope = "Layer 1 standard taxonomy node type"
            evidence_files = [
                rel(outputs_dir / "01_layer1/layer1_ncs_nodes.jsonl"),
                outputs["ncs_mapping_candidates"],
            ]
            notes = "NCSCompetencyUnit belongs to Layer 1 and mapping targets, not canonical Layer 2 nodes."
        elif term == "PCFElement":
            represented_count = int(pcf_node_counts.get("PCFElement", 0))
            represented_in = "layer1_pcf_graph_and_mapping_targets"
            status = "layer1_standard_present"
            claim_scope = "Layer 1 standard taxonomy node type"
            evidence_files = [
                rel(outputs_dir / "01_layer1/layer1_pcf_nodes.jsonl"),
                outputs["pcf_mapping_candidates"],
            ]
            notes = "PCFElement belongs to Layer 1 and mapping targets, not canonical Layer 2 nodes."
        elif term == "MappingCandidate":
            represented_count = mapping_candidate_rows
            represented_in = "mapping_candidate_rows"
            status = "represented_as_candidate_rows"
            claim_scope = "candidate-only standard bridge pending expert review"
            evidence_files = [outputs["ncs_mapping_candidates"], outputs["pcf_mapping_candidates"]]
            notes = "Mapping candidates are JSONL review rows and Neo4j relationships, not canonical KG nodes."

        rows.append(
            {
                "term": term,
                "kind": "node_type",
                "plan_section": "7.1 Node types",
                "canonical_layer2_count": canonical_count,
                "represented_count": represented_count,
                "represented_in": represented_in,
                "status": status,
                "claim_scope": claim_scope,
                "evidence_files": evidence_files,
                "notes": notes,
            }
        )

    for term in EXPECTED_EDGE_TYPES:
        canonical_count = int(edge_counts.get(term, 0))
        represented_count = canonical_count
        represented_in = "canonical_layer2_graph" if canonical_count else ""
        status = "canonical_layer2_present" if canonical_count else "missing_unclassified"
        claim_scope = "canonical Layer 2 KG predicate"
        evidence_files = [outputs["canonical_layer2_edges"]]
        notes = ""

        if term == "BRANCHES_TO":
            represented_count = int(structural_summary.get("gateway_branch_gap_count") or 0)
            represented_in = "structural_review_worklist"
            status = "pending_structural_review"
            claim_scope = "known schema gap tracked for human structural review"
            evidence_files = [
                outputs["structural_gap_worklist_summary"],
                rel(exp_dir / "05_review/structural_gateway_branch_gaps.csv"),
            ]
            notes = "Decision gateways are present, but explicit branch outcomes are pending structural review."
        elif term == "HAS_REVIEW_CHECKPOINT" and canonical_count == 0:
            represented_count = int(structural_summary.get("review_checkpoint_candidate_count") or 0)
            represented_in = "structural_review_worklist"
            status = "pending_structural_review"
            claim_scope = "known schema gap tracked for human structural review"
            evidence_files = [
                outputs["structural_gap_worklist_summary"],
                rel(exp_dir / "05_review/structural_review_checkpoint_candidates.csv"),
            ]
            notes = "Review checkpoint links are not in canonical Layer 2 yet; candidates are prepared for review."
        elif term == "HAS_REVIEW_CHECKPOINT":
            notes = "Review-signaled ProcedureStep nodes are linked to projected ReviewCheckpoint nodes in canonical Layer 2."
        elif term == "EVIDENCED_BY":
            represented_count = int(evidence_summary.get("evidenced_by_edge_count") or relationship_types.get("EVIDENCED_BY") or 0)
            represented_in = "evidence_projection_and_neo4j_export"
            status = "projection_present"
            claim_scope = "noncanonical evidence projection; final span correctness remains human-gold pending"
            evidence_files = [outputs["evidence_projection_summary"], outputs["neo4j_manifest"]]
            notes = "EVIDENCED_BY is materialized as projection/Neo4j relationships from node/edge evidence_anchor_ids."
        elif term == "REQUIRES_CAPABILITY":
            represented_count = int(relationship_types.get("REQUIRES_CAPABILITY") or len(ncs_mappings))
            represented_in = "mapping_projection_and_neo4j_export"
            status = "mapping_projection_present"
            claim_scope = "candidate-only NCS mapping pending expert review"
            evidence_files = [outputs["ncs_mapping_candidates"], outputs["neo4j_manifest"]]
            notes = "NCS mapping is candidate-only and must not be presented as expert-confirmed alignment."
        elif term == "PROCESS_CONTEXT":
            represented_count = int(relationship_types.get("PROCESS_CONTEXT") or len(pcf_mappings))
            represented_in = "mapping_projection_and_neo4j_export"
            status = "mapping_projection_present"
            claim_scope = "candidate-only PCF mapping pending expert review"
            evidence_files = [outputs["pcf_mapping_candidates"], outputs["neo4j_manifest"]]
            notes = "PCF mapping is candidate-only and must not be presented as expert-confirmed alignment."
        elif term == "CANDIDATE_ALIGNS_WITH":
            represented_count = mapping_candidate_rows + int(crosswalk_summary.get("candidate_count") or 0)
            represented_in = "mapping_candidate_rows_and_crosswalk_candidates"
            status = "represented_as_candidate_rows"
            claim_scope = "generic plan relation represented by standard-specific mapping rows pending expert review"
            evidence_files = [
                outputs["ncs_mapping_candidates"],
                outputs["pcf_mapping_candidates"],
                outputs["ncs_pcf_crosswalk_summary"],
            ]
            notes = "Current exports use REQUIRES_CAPABILITY/PROCESS_CONTEXT for standard-specific candidate edges."

        rows.append(
            {
                "term": term,
                "kind": "edge_type",
                "plan_section": "7.2 Edge types",
                "canonical_layer2_count": canonical_count,
                "represented_count": represented_count,
                "represented_in": represented_in,
                "status": status,
                "claim_scope": claim_scope,
                "evidence_files": evidence_files,
                "notes": notes,
            }
        )

    return rows, outputs


def render_report(payload):
    summary = payload["summary"]
    lines = [
        "# CAPE-KG Schema Plan Alignment",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Claim status: `{payload['claim_status']}`",
        "",
        "This report aligns the schema terms in `AX_EACL_submission_review_revised_plan.md` sections 7.1 and 7.2 with the current artifacts. It deliberately separates canonical Layer 2 graph terms from projection, mapping-candidate, and human-review worklist terms.",
        "",
        "## Summary",
        "",
        "| Item | Value |",
        "|---|---:|",
        f"| Plan node types | {summary['plan_node_type_count']} |",
        f"| Plan edge types | {summary['plan_edge_type_count']} |",
        f"| Canonical Layer 2 present terms | {summary['canonical_layer2_present_count']} |",
        f"| Projection or mapping represented terms | {summary['projection_or_mapping_represented_count']} |",
        f"| Pending structural review terms | {summary['pending_structural_review_count']} |",
        f"| Missing unclassified terms | {summary['missing_unclassified_count']} |",
        "",
        "## Interpretation",
        "",
        "- `canonical_layer2_present`: present directly in `layer2_nodes.jsonl` or `layer2_edges.jsonl`.",
        "- `projection_present`: materialized in evidence projection, RDF/SHACL, or Neo4j export rather than canonical Layer 2 JSONL.",
        "- `mapping_projection_present` / `represented_as_candidate_rows`: standard-bridge candidates exist but remain pending expert review.",
        "- `pending_structural_review`: known noncanonical gap prepared as a human structural review worklist.",
        "- `missing_unclassified`: unexpected gap; validator should fail if this is nonzero.",
        "",
        "## Alignment Rows",
        "",
        "| kind | term | canonical_count | represented_count | status | represented_in | claim_scope |",
        "|---|---|---:|---:|---|---|---|",
    ]
    for row in payload["rows"]:
        lines.append(
            "| {kind} | `{term}` | {canonical_layer2_count} | {represented_count} | `{status}` | {represented_in} | {claim_scope} |".format(
                **row
            )
        )
    lines += [
        "",
        "## Known Structural Review Terms",
        "",
        "| term | evidence | note |",
        "|---|---|---|",
    ]
    pending_rows = [row for row in payload["rows"] if row["status"] == "pending_structural_review"]
    if pending_rows:
        for row in pending_rows:
            evidence = ", ".join(f"`{path}`" for path in row.get("evidence_files", []))
            lines.append(f"| `{row['term']}` | {evidence} | {row.get('notes', '')} |")
    else:
        lines.append("|  |  | No pending structural terms. |")
    lines += [
        "",
        "## Claim Safety",
        "",
        "- This report does not change the canonical KG.",
        "- It prevents overclaiming that every plan schema term is already present as a canonical Layer 2 node or edge.",
        "- Mapping and crosswalk rows remain candidate-only until expert review returns are imported.",
        "- Review checkpoint terms are canonical when present, but their correctness remains pending human-gold review.",
        "- Branch terms remain structural-review worklist items until human review confirms source-supported branch outcomes.",
        "",
    ]
    return "\n".join(lines)


def build_payload(exp_dir, outputs_dir, plan_file):
    rows, outputs = build_rows(exp_dir, outputs_dir)
    status_counts = Counter(row["status"] for row in rows)
    missing_unclassified = [row["term"] for row in rows if row["status"] == "missing_unclassified"]
    pending_structural = [row["term"] for row in rows if row["status"] == "pending_structural_review"]
    unexpected_pending = sorted(set(pending_structural) - KNOWN_PENDING_TERMS)
    claim_status = (
        "schema_plan_alignment_ready_with_known_structural_gaps"
        if not missing_unclassified and not unexpected_pending
        else "schema_plan_alignment_has_unclassified_gaps"
    )
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": rel(exp_dir),
        "outputs_dir": rel(outputs_dir),
        "plan_file": rel(plan_file),
        "claim_status": claim_status,
        "summary": {
            "plan_node_type_count": len(EXPECTED_NODE_TYPES),
            "plan_edge_type_count": len(EXPECTED_EDGE_TYPES),
            "alignment_row_count": len(rows),
            "canonical_layer2_present_count": status_counts.get("canonical_layer2_present", 0),
            "projection_or_mapping_represented_count": (
                status_counts.get("projection_present", 0)
                + status_counts.get("mapping_projection_present", 0)
                + status_counts.get("represented_as_candidate_rows", 0)
                + status_counts.get("layer1_standard_present", 0)
            ),
            "pending_structural_review_count": status_counts.get("pending_structural_review", 0),
            "missing_unclassified_count": status_counts.get("missing_unclassified", 0),
            "status_counts": dict(sorted(status_counts.items())),
            "known_pending_structural_terms": sorted(KNOWN_PENDING_TERMS),
            "unexpected_pending_structural_terms": unexpected_pending,
            "missing_unclassified_terms": missing_unclassified,
        },
        "rows": rows,
        "source_artifacts": outputs,
    }


def run(args):
    exp_dir = Path(args.experiment_dir)
    outputs_dir = Path(args.outputs_dir)
    plan_file = Path(args.plan_file)
    release_dir = exp_dir / "06_release"
    payload = build_payload(exp_dir, outputs_dir, plan_file)
    json_path = release_dir / "schema_plan_alignment.json"
    md_path = release_dir / "schema_plan_alignment.md"
    write_json(json_path, payload)
    write_text(md_path, render_report(payload))
    print(json.dumps({"json": rel(json_path), "markdown": rel(md_path), "claim_status": payload["claim_status"]}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--outputs-dir", default=str(DEFAULT_OUTPUTS_DIR))
    parser.add_argument("--plan-file", default=str(DEFAULT_PLAN_FILE))
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
