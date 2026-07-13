#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Export CAPE-KG Layer 2 graph to RDF/Turtle and run SHACL-style checks."""

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_OUTPUTS_DIR = Path("outputs")


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


def rel(path):
    return str(Path(path).as_posix())


def short_hash(value, length=16):
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:length]


def node_uri(node_id):
    return f"cape:node_{short_hash(node_id)}"


def edge_uri(edge_id):
    return f"cape:edge_{short_hash(edge_id)}"


def evidence_uri(anchor_id):
    return f"cape:evidence_{short_hash(anchor_id)}"


def ttl_string(value):
    text = "" if value is None else str(value)
    text = text.replace("\\", "\\\\").replace('"', '\\"')
    text = text.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
    return f'"{text}"'


def ttl_int(value):
    try:
        value = int(value)
    except Exception:
        value = 0
    return f'"{value}"^^xsd:integer'


def ttl_float(value):
    try:
        value = float(value)
    except Exception:
        return ""
    return f'"{value:.6f}"^^xsd:decimal'


def ttl_bool(value):
    return f'"{str(bool(value)).lower()}"^^xsd:boolean'


def pred_uri(predicate):
    return "cape:" + str(predicate).strip().replace("-", "_")


def class_uri(type_name):
    return "cape:" + str(type_name).strip().replace("-", "_")


def emit_block(lines, subject, predicates):
    predicates = [(pred, obj) for pred, obj in predicates if obj not in {None, ""}]
    if not predicates:
        return 0
    lines.append(subject)
    for index, (pred, obj) in enumerate(predicates):
        ending = " ." if index == len(predicates) - 1 else " ;"
        lines.append(f"  {pred} {obj}{ending}")
    lines.append("")
    return len(predicates)


def build_constraints(outputs_dir):
    allowed = set(read_json(outputs_dir / "03_schema/allowed_predicates.json", []) or [])
    constraints = {}
    for row in read_json(outputs_dir / "03_schema/domain_range_constraints.json", []) or []:
        constraints[row.get("predicate")] = {
            "subject_types": set(row.get("subject_types") or []),
            "object_types": set(row.get("object_types") or []),
        }
    schema = read_json(outputs_dir / "03_schema/layer2_schema.json", {}) or {}
    node_types = set(schema.get("node_types") or [])
    return allowed, constraints, node_types


def collect_evidence_metadata(outputs_dir):
    rows = read_jsonl(outputs_dir / "06_triples/evidence_anchors.jsonl")
    return {row.get("evidence_anchor_id"): row for row in rows if row.get("evidence_anchor_id")}


def validate_graph(nodes, edges, evidence, allowed_predicates, constraints, allowed_node_types):
    issues = []
    node_ids = [row.get("node_id") for row in nodes]
    edge_ids = [row.get("edge_id") for row in edges]
    node_by_id = {row.get("node_id"): row for row in nodes if row.get("node_id")}
    duplicate_nodes = [item for item, count in Counter(node_ids).items() if item and count > 1]
    duplicate_edges = [item for item, count in Counter(edge_ids).items() if item and count > 1]

    for node_id in duplicate_nodes:
        issues.append({"severity": "error", "type": "duplicate_node_id", "node_id": node_id})
    for edge_id in duplicate_edges:
        issues.append({"severity": "error", "type": "duplicate_edge_id", "edge_id": edge_id})

    for row in nodes:
        node_id = row.get("node_id")
        node_type = row.get("type")
        if not node_id:
            issues.append({"severity": "error", "type": "missing_node_id", "node": row})
        if node_type not in allowed_node_types:
            issues.append({"severity": "error", "type": "unknown_node_type", "node_id": node_id, "node_type": node_type})

    for row in edges:
        edge_id = row.get("edge_id")
        source_id = row.get("source_id")
        target_id = row.get("target_id")
        predicate = row.get("predicate")
        evidence_ids = row.get("evidence_anchor_ids") or []
        source = node_by_id.get(source_id)
        target = node_by_id.get(target_id)

        if predicate not in allowed_predicates:
            issues.append({"severity": "error", "type": "unknown_predicate", "edge_id": edge_id, "predicate": predicate})
        if source is None:
            issues.append({"severity": "error", "type": "dangling_source", "edge_id": edge_id, "source_id": source_id})
        if target is None:
            issues.append({"severity": "error", "type": "dangling_target", "edge_id": edge_id, "target_id": target_id})
        if not evidence_ids:
            issues.append({"severity": "error", "type": "missing_edge_evidence", "edge_id": edge_id})
        for anchor_id in evidence_ids:
            if anchor_id not in evidence:
                issues.append({"severity": "error", "type": "unknown_evidence_anchor", "edge_id": edge_id, "evidence_anchor_id": anchor_id})
        if predicate in constraints and source is not None and target is not None:
            subject_types = constraints[predicate]["subject_types"]
            object_types = constraints[predicate]["object_types"]
            source_ok = "Any" in subject_types or source.get("type") in subject_types
            target_ok = "Any" in object_types or target.get("type") in object_types
            if not source_ok or not target_ok:
                issues.append(
                    {
                        "severity": "error",
                        "type": "domain_range_violation",
                        "edge_id": edge_id,
                        "predicate": predicate,
                        "source_id": source_id,
                        "source_type": source.get("type"),
                        "allowed_subject_types": sorted(subject_types),
                        "target_id": target_id,
                        "target_type": target.get("type"),
                        "allowed_object_types": sorted(object_types),
                    }
                )

    issue_counts = Counter(row["type"] for row in issues)
    severity_counts = Counter(row["severity"] for row in issues)
    return {
        "issues": issues,
        "issue_counts": dict(sorted(issue_counts.items())),
        "severity_counts": dict(sorted(severity_counts.items())),
        "error_count": severity_counts.get("error", 0),
        "warning_count": severity_counts.get("warning", 0),
    }


def build_rdf(nodes, edges, evidence, output_paths):
    used_evidence = set()
    for row in nodes:
        used_evidence.update(row.get("evidence_anchor_ids") or [])
    for row in edges:
        used_evidence.update(row.get("evidence_anchor_ids") or [])

    lines = [
        "@prefix cape: <https://example.org/cape-kg#> .",
        "@prefix prov: <http://www.w3.org/ns/prov#> .",
        "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .",
        "",
    ]
    statement_count = 0

    for type_name in sorted({row.get("type") for row in nodes if row.get("type")}):
        statement_count += emit_block(
            lines,
            class_uri(type_name),
            [
                ("a", "rdfs:Class"),
                ("rdfs:label", ttl_string(type_name)),
            ],
        )

    for predicate in sorted({row.get("predicate") for row in edges if row.get("predicate")}):
        statement_count += emit_block(
            lines,
            pred_uri(predicate),
            [
                ("a", "rdf:Property"),
                ("rdfs:label", ttl_string(predicate)),
            ],
        )

    for anchor_id in sorted(used_evidence):
        meta = evidence.get(anchor_id) or {}
        predicates = [
            ("a", "cape:EvidenceAnchor"),
            ("cape:evidenceAnchorId", ttl_string(anchor_id)),
            ("cape:sentenceId", ttl_string(meta.get("sentence_id", ""))),
            ("cape:page", ttl_int(meta.get("page", 0))),
            ("cape:spanStart", ttl_int(meta.get("span_start", 0))),
            ("cape:spanEnd", ttl_int(meta.get("span_end", 0))),
            ("cape:anchorExact", ttl_bool(meta.get("anchor_exact", False))),
            ("cape:zone", ttl_string(meta.get("zone", ""))),
        ]
        if meta.get("chunk_id"):
            predicates.append(("cape:chunkId", ttl_string(meta.get("chunk_id"))))
        statement_count += emit_block(lines, evidence_uri(anchor_id), predicates)

    for row in nodes:
        uri = node_uri(row.get("node_id"))
        predicates = [
            ("a", class_uri(row.get("type"))),
            ("a", "cape:KGNode"),
            ("rdfs:label", ttl_string(row.get("label", ""))),
            ("cape:nodeId", ttl_string(row.get("node_id", ""))),
            ("cape:nodeType", ttl_string(row.get("type", ""))),
            ("cape:layer", ttl_string(row.get("layer", ""))),
            ("cape:reviewStatus", ttl_string(row.get("review_status", ""))),
            ("cape:source", ttl_string(row.get("source", ""))),
        ]
        if row.get("label_ko"):
            predicates.append(("cape:labelKo", ttl_string(row.get("label_ko"))))
        if row.get("label_en"):
            predicates.append(("cape:labelEn", ttl_string(row.get("label_en"))))
        if row.get("order") is not None:
            predicates.append(("cape:procedureOrder", ttl_int(row.get("order"))))
        if row.get("parent_task_id"):
            predicates.append(("cape:parentTaskId", ttl_string(row.get("parent_task_id"))))
        for alias in row.get("aliases") or []:
            predicates.append(("cape:alias", ttl_string(alias)))
        for anchor_id in row.get("evidence_anchor_ids") or []:
            predicates.append(("prov:wasDerivedFrom", evidence_uri(anchor_id)))
        statement_count += emit_block(lines, uri, predicates)

    node_ids = {row.get("node_id") for row in nodes}
    for row in edges:
        if row.get("source_id") in node_ids and row.get("target_id") in node_ids:
            lines.append(f"{node_uri(row.get('source_id'))} {pred_uri(row.get('predicate'))} {node_uri(row.get('target_id'))} .")
            lines.append("")
            statement_count += 1
        predicates = [
            ("a", "cape:KGEdge"),
            ("cape:edgeId", ttl_string(row.get("edge_id", ""))),
            ("cape:predicate", ttl_string(row.get("predicate", ""))),
            ("cape:sourceNode", node_uri(row.get("source_id")) if row.get("source_id") in node_ids else ttl_string(row.get("source_id", ""))),
            ("cape:targetNode", node_uri(row.get("target_id")) if row.get("target_id") in node_ids else ttl_string(row.get("target_id", ""))),
            ("cape:layer", ttl_string(row.get("layer", ""))),
            ("cape:reviewStatus", ttl_string(row.get("review_status", ""))),
            ("cape:confidence", ttl_float(row.get("confidence"))),
        ]
        for triple_id in row.get("source_triple_ids") or []:
            predicates.append(("cape:sourceTripleId", ttl_string(triple_id)))
        for anchor_id in row.get("evidence_anchor_ids") or []:
            predicates.append(("prov:wasDerivedFrom", evidence_uri(anchor_id)))
        statement_count += emit_block(lines, edge_uri(row.get("edge_id")), predicates)

    return "\n".join(lines), {
        "rdf_statement_count": statement_count,
        "used_evidence_anchor_count": len(used_evidence),
        "output_ttl": output_paths["rdf_ttl"],
    }


def build_shapes(allowed_predicates, constraints, allowed_node_types):
    lines = [
        "@prefix sh: <http://www.w3.org/ns/shacl#> .",
        "@prefix cape: <https://example.org/cape-kg#> .",
        "@prefix prov: <http://www.w3.org/ns/prov#> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "",
    ]
    for type_name in sorted(allowed_node_types):
        lines += [
            f"cape:{type_name}Shape a sh:NodeShape ;",
            f"  sh:targetClass cape:{type_name} ;",
            '  sh:property [ sh:path cape:nodeId ; sh:minCount 1 ] ;',
            '  sh:property [ sh:path rdfs:label ; sh:minCount 1 ] .',
            "",
        ]
    lines += [
        "cape:EvidenceGroundedEdgeShape a sh:NodeShape ;",
        "  sh:targetClass cape:KGEdge ;",
        "  sh:property [ sh:path cape:edgeId ; sh:minCount 1 ] ;",
        "  sh:property [ sh:path cape:predicate ; sh:minCount 1 ] ;",
        "  sh:property [ sh:path prov:wasDerivedFrom ; sh:minCount 1 ] .",
        "",
    ]
    for predicate, rule in sorted(constraints.items()):
        lines += [
            f"cape:{predicate}DomainRangeShape a sh:NodeShape ;",
            f"  sh:message {ttl_string(predicate + ' domain/range rule is enforced by the CAPE-KG SHACL-style validator.')} .",
            "",
        ]
    lines += [
        "cape:AllowedPredicateSetShape a sh:NodeShape ;",
        f"  sh:message {ttl_string('Allowed predicates: ' + ', '.join(sorted(allowed_predicates)))} .",
        "",
    ]
    return "\n".join(lines)


def render_report(payload):
    summary = payload["summary"]
    lines = [
        "# CAPE-KG RDF/SHACL-Style Validation Report",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Overall status: `{payload['overall_status']}`",
        f"Claim status: `{payload['claim_status']}`",
        "",
        "This report exports the Layer 2 CAPE-KG graph to Turtle and validates the current JSONL graph against the same predicate, evidence, and domain/range constraints used by the pipeline. It is structural validation evidence, not human-gold performance evidence.",
        "",
        "## Outputs",
        "",
        f"- RDF/Turtle: `{payload['outputs']['rdf_ttl']}`",
        f"- Runtime shapes: `{payload['outputs']['runtime_shapes_ttl']}`",
        f"- Summary JSON: `{payload['outputs']['summary_json']}`",
        f"- Report: `{payload['outputs']['report_md']}`",
        "",
        "## Summary",
        "",
        "| Item | Value |",
        "|---|---:|",
    ]
    for key, value in summary.items():
        lines.append(f"| {key} | {value} |")
    lines += ["", "## Issue Counts", ""]
    if payload["issue_counts"]:
        lines += ["| Issue type | Count |", "|---|---:|"]
        for key, value in payload["issue_counts"].items():
            lines.append(f"| {key} | {value} |")
    else:
        lines.append("- No validation issues.")
    if payload["issues"]:
        lines += ["", "## First Issues", ""]
        for row in payload["issues"][:50]:
            lines.append(f"- `{row.get('type')}`: `{json.dumps(row, ensure_ascii=False)}`")
    lines += [
        "",
        "## Public Release Note",
        "",
        "The RDF export is placed under `outputs/12_rdf` rather than `06_release` because KG labels and definitions are source-derived internal artifacts. The export intentionally omits full evidence sentence text.",
        "",
    ]
    return "\n".join(lines)


def build_payload(exp_dir, outputs_dir):
    exp_dir = Path(exp_dir)
    outputs_dir = Path(outputs_dir)
    rdf_dir = outputs_dir / "12_rdf"
    output_paths = {
        "rdf_ttl": rel(rdf_dir / "cape_kg_layer2.ttl"),
        "runtime_shapes_ttl": rel(rdf_dir / "cape_kg_runtime_shapes.shacl.ttl"),
        "summary_json": rel(rdf_dir / "cape_kg_shacl_validation_summary.json"),
        "report_md": rel(rdf_dir / "cape_kg_shacl_validation_report.md"),
    }
    nodes = read_jsonl(outputs_dir / "07_layer2_graph/layer2_nodes.jsonl")
    edges = read_jsonl(outputs_dir / "07_layer2_graph/layer2_edges.jsonl")
    evidence = collect_evidence_metadata(outputs_dir)
    allowed_predicates, constraints, allowed_node_types = build_constraints(outputs_dir)
    validation = validate_graph(nodes, edges, evidence, allowed_predicates, constraints, allowed_node_types)
    rdf_text, rdf_summary = build_rdf(nodes, edges, evidence, output_paths)
    shapes_text = build_shapes(allowed_predicates, constraints, allowed_node_types)

    node_type_counts = Counter(row.get("type") for row in nodes)
    predicate_counts = Counter(row.get("predicate") for row in edges)
    error_count = validation["error_count"]
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "outputs_dir": str(outputs_dir),
        "overall_status": "PASS" if error_count == 0 else "FAIL",
        "claim_status": "rdf_shacl_style_validation_pass_not_human_gold" if error_count == 0 else "rdf_shacl_style_validation_failed",
        "summary": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "node_type_count": len(node_type_counts),
            "predicate_type_count": len(predicate_counts),
            "allowed_predicate_count": len(allowed_predicates),
            "domain_range_rule_count": len(constraints),
            "evidence_anchor_catalog_count": len(evidence),
            "used_evidence_anchor_count": rdf_summary["used_evidence_anchor_count"],
            "rdf_statement_count": rdf_summary["rdf_statement_count"],
            "error_count": error_count,
            "warning_count": validation["warning_count"],
        },
        "node_type_counts": dict(sorted(node_type_counts.items())),
        "predicate_counts": dict(sorted(predicate_counts.items())),
        "issue_counts": validation["issue_counts"],
        "severity_counts": validation["severity_counts"],
        "issues": validation["issues"][:200],
        "issue_count_truncated": max(0, len(validation["issues"]) - 200),
        "outputs": output_paths,
        "_rdf_text": rdf_text,
        "_shapes_text": shapes_text,
    }
    return payload


def run(args):
    payload = build_payload(args.experiment_dir, args.outputs_dir)
    rdf_text = payload.pop("_rdf_text")
    shapes_text = payload.pop("_shapes_text")
    write_text(payload["outputs"]["rdf_ttl"], rdf_text)
    write_text(payload["outputs"]["runtime_shapes_ttl"], shapes_text)
    write_json(payload["outputs"]["summary_json"], payload)
    write_text(payload["outputs"]["report_md"], render_report(payload))
    print(json.dumps({
        "rdf_ttl": payload["outputs"]["rdf_ttl"],
        "runtime_shapes_ttl": payload["outputs"]["runtime_shapes_ttl"],
        "summary_json": payload["outputs"]["summary_json"],
        "report_md": payload["outputs"]["report_md"],
        "overall_status": payload["overall_status"],
        "claim_status": payload["claim_status"],
        "node_count": payload["summary"]["node_count"],
        "edge_count": payload["summary"]["edge_count"],
        "error_count": payload["summary"]["error_count"],
    }, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--outputs-dir", default=str(DEFAULT_OUTPUTS_DIR))
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
