#!/usr/bin/env python3
"""Serialize the deterministic core to RDF, validate SHACL, and test Neo4j projection."""

from __future__ import annotations

import csv
import json
import os
import re
import statistics
import urllib.parse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from neo4j import GraphDatabase
from pyshacl import validate as shacl_validate
from rdflib import Graph, Literal, Namespace, RDF, SKOS, URIRef
from rdflib.namespace import XSD

import r4_ceoc as r4


CEOC = Namespace("https://example.org/ceoc/")
PROV = Namespace("http://www.w3.org/ns/prov#")


def uri(identifier: str) -> URIRef:
    return URIRef(str(CEOC) + urllib.parse.quote(identifier, safe=""))


def predicate(name: str) -> URIRef:
    return URIRef(str(CEOC) + urllib.parse.quote(name, safe=""))


def literal(value: Any) -> Literal:
    if isinstance(value, bool): return Literal(value, datatype=XSD.boolean)
    if isinstance(value, int): return Literal(value, datatype=XSD.integer)
    if isinstance(value, float): return Literal(value, datatype=XSD.decimal)
    return Literal(str(value))


def rdf_graph(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> Graph:
    graph = Graph()
    graph.bind("ceoc", CEOC); graph.bind("prov", PROV); graph.bind("skos", SKOS)
    for node in nodes:
        subject = uri(node["id"])
        graph.add((subject, RDF.type, CEOC[node["type"]]))
        graph.add((subject, CEOC.canonicalNodeId, Literal(node["id"])))
        if node["type"] == "Concept" and node.get("preferred_label"):
            graph.add((subject, SKOS.prefLabel, Literal(node["preferred_label"], lang="ko")))
        for key, value in node.items():
            if key in {"id", "type"} or value is None:
                continue
            values = value if isinstance(value, list) else [value]
            for item in values:
                graph.add((subject, predicate(key), literal(item)))
    for edge in edges:
        if edge["type"] == "DERIVED_FROM":
            relation = PROV.wasDerivedFrom
        elif edge["type"] == "HAS_DEONTIC_CUE":
            relation = CEOC.hasDeonticCue
        else:
            relation = predicate(edge["type"])
        graph.add((uri(edge["source"]), relation, uri(edge["target"])))
        edge_uri = uri(edge["id"])
        graph.add((edge_uri, RDF.type, CEOC.GraphEdge))
        graph.add((edge_uri, CEOC.canonicalEdgeId, Literal(edge["id"])))
        graph.add((edge_uri, CEOC.edgeSource, uri(edge["source"])))
        graph.add((edge_uri, CEOC.edgeTarget, uri(edge["target"])))
        graph.add((edge_uri, CEOC.edgePredicate, Literal(edge["type"])))
    return graph


def property_value(value: Any) -> Any:
    if value is None: return None
    if isinstance(value, (str, int, float, bool)): return value
    if isinstance(value, list): return [item for item in value if isinstance(item, (str, int, float, bool))]
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def node_rows(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for node in nodes:
        props = {key: property_value(value) for key, value in node.items() if key not in {"id", "type"} and value is not None}
        props.update({"id": node["id"], "type": node["type"], "canonicalNodeId": node["id"]})
        rows.append({"id": node["id"], "label": node["type"], "properties": props})
    return rows


def edge_rows(edges: list[dict[str, Any]], nodes: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    run_id = f"RUN_R4_B1_{r4.EXPERIMENT_ID}"
    for edge in edges:
        evidence = list(edge.get("evidence_anchor_ids") or [])
        if edge["type"] == "DERIVED_FROM" and nodes.get(edge["target"], {}).get("type") == "Anchor":
            evidence.append(edge["target"])
        props = {key: property_value(value) for key, value in edge.items() if key not in {"id", "type", "source", "target"} and value is not None}
        props.update({
            "id": edge["id"], "canonicalEdgeId": edge["id"],
            "canonicalRdfPredicate": edge["type"], "extractionRunId": run_id,
            "evidenceAnchorIds": sorted(set(evidence)),
        })
        rows.append({"id": edge["id"], "type": edge["type"], "source": edge["source"], "target": edge["target"], "properties": props})
    return rows


def write_projection_files(root: Path, nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> None:
    neo_dir = root / "graphs" / "neo4j"
    r4.write_jsonl(neo_dir / "nodes.jsonl", nodes)
    r4.write_jsonl(neo_dir / "edges.jsonl", edges)
    with (neo_dir / "nodes.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "label", "properties_json"]); writer.writeheader()
        for item in nodes: writer.writerow({"id": item["id"], "label": item["label"], "properties_json": json.dumps(item["properties"], ensure_ascii=False, sort_keys=True)})
    with (neo_dir / "edges.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "type", "source", "target", "properties_json"]); writer.writeheader()
        for item in edges: writer.writerow({"id": item["id"], "type": item["type"], "source": item["source"], "target": item["target"], "properties_json": json.dumps(item["properties"], ensure_ascii=False, sort_keys=True)})


def import_neo4j(uri_value: str, nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, Any]:
    driver = GraphDatabase.driver(uri_value, auth=None)
    with driver.session(database="neo4j") as session:
        session.run("MATCH (n) DETACH DELETE n").consume()
        by_label = defaultdict(list)
        for item in nodes: by_label[item["label"]].append(item)
        for label, items in by_label.items():
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", label): raise RuntimeError(label)
            for start in range(0, len(items), 500):
                session.run(f"UNWIND $rows AS row CREATE (n:R4Node:`{label}`) SET n = row.properties", rows=items[start:start+500]).consume()
        by_type = defaultdict(list)
        for item in edges: by_type[item["type"]].append(item)
        for rel_type, items in by_type.items():
            if not re.fullmatch(r"[A-Z][A-Z0-9_]*", rel_type): raise RuntimeError(rel_type)
            for start in range(0, len(items), 500):
                session.run(f"UNWIND $rows AS row MATCH (s:R4Node {{id: row.source}}), (t:R4Node {{id: row.target}}) CREATE (s)-[r:`{rel_type}`]->(t) SET r = row.properties", rows=items[start:start+500]).consume()
        node_count = session.run("MATCH (n:R4Node) RETURN count(n) AS n").single()["n"]
        edge_count = session.run("MATCH ()-[r]->() RETURN count(r) AS n").single()["n"]
        rule_count = session.run("MATCH (r:ExplicitDeonticRule) RETURN count(r) AS n").single()["n"]
        rule_paths = session.run("MATCH p=(r:ExplicitDeonticRule)-[:DERIVED_FROM]->(a:Anchor) RETURN count(p) AS n").single()["n"]
        bad_examples = session.run("MATCH (e:ExampleInstance) WHERE e.promotion_status = 'PROMOTED_RULEBOX' RETURN count(e) AS n").single()["n"]
        sample = [record.data() for record in session.run("MATCH (r:ExplicitDeonticRule)-[:DERIVED_FROM]->(a:Anchor) RETURN r.id AS ruleId, a.id AS anchorId, a.exact_text AS exactText LIMIT 10")]
        edge_provenance = session.run("MATCH ()-[r]->() RETURN count(r) AS total, count(r.canonicalEdgeId) AS covered, count(r.canonicalRdfPredicate) AS rdfCovered").single()
    driver.close()
    return {
        "node_count": node_count, "edge_count": edge_count, "explicit_rule_count": rule_count,
        "explicit_rule_evidence_paths": rule_paths, "example_rulebox_count": bad_examples,
        "sample_evidence_paths": sample,
        "edge_provenance_total": edge_provenance["total"], "edge_provenance_covered": edge_provenance["covered"],
        "edge_rdf_reference_covered": edge_provenance["rdfCovered"],
    }


def main() -> int:
    project = Path(__file__).resolve().parents[1]
    root = project / "experiments" / r4.EXPERIMENT_ID
    gate4 = json.loads((root / "reports" / "gate_r4_4.json").read_text(encoding="utf-8"))
    if gate4["status"] != "PASS": raise RuntimeError("R4-4 must pass")
    source_nodes = r4.read_jsonl(root / "runs" / "b1_deterministic" / "nodes.jsonl")
    source_edges = r4.read_jsonl(root / "runs" / "b1_deterministic" / "edges.jsonl")
    source_graph = {"system": "R4-B1", "nodes": source_nodes, "edges": source_edges}
    confirm_rows = r4.read_jsonl(root / "data" / "confirmatory" / "validation_80.jsonl")
    source_validation = r4.validate_graph(source_graph, confirm_rows)
    if source_validation["critical_shacl_violation_count"]:
        raise RuntimeError("Source B1 graph has critical violations")

    graph = rdf_graph(source_nodes, source_edges)
    rdf_dir = root / "graphs" / "rdf"
    rdf_dir.mkdir(parents=True, exist_ok=True)
    turtle_path = rdf_dir / "ceoc_core.ttl"
    graph.serialize(destination=turtle_path, format="turtle")
    parsed = Graph(); parsed.parse(turtle_path, format="turtle")
    shapes = Graph(); shapes.parse(root / "schema" / "shapes.ttl", format="turtle")
    conforms, report_graph, report_text = shacl_validate(parsed, shacl_graph=shapes, inference="rdfs", abort_on_first=False, allow_infos=True, allow_warnings=True)
    shacl_dir = root / "graphs" / "shacl_reports"; shacl_dir.mkdir(parents=True, exist_ok=True)
    report_graph.serialize(destination=shacl_dir / "report.ttl", format="turtle")
    (shacl_dir / "report.txt").write_text(report_text, encoding="utf-8")

    rdf_node_coverage = sum((uri(node["id"]), RDF.type, CEOC[node["type"]]) in parsed for node in source_nodes) / len(source_nodes)
    rdf_edge_coverage = 0
    for edge in source_edges:
        if edge["type"] == "DERIVED_FROM":
            relation = PROV.wasDerivedFrom
        elif edge["type"] == "HAS_DEONTIC_CUE":
            relation = CEOC.hasDeonticCue
        else:
            relation = predicate(edge["type"])
        rdf_edge_coverage += int((uri(edge["source"]), relation, uri(edge["target"])) in parsed)
    rdf_edge_coverage /= len(source_edges)

    nodes = node_rows(source_nodes)
    by_node = {item["id"]: item for item in source_nodes}
    edges = edge_rows(source_edges, by_node)
    write_projection_files(root, nodes, edges)
    neo4j_uri = os.environ.get("R4_NEO4J_URI", "bolt://127.0.0.1:7688")
    runtime = import_neo4j(neo4j_uri, nodes, edges)
    node_projection = runtime["node_count"] / len(nodes)
    edge_projection = runtime["edge_count"] / len(edges)
    provenance_projection = runtime["edge_provenance_covered"] / runtime["edge_provenance_total"] if runtime["edge_provenance_total"] else 1.0
    rdf_reference_projection = runtime["edge_rdf_reference_covered"] / runtime["edge_provenance_total"] if runtime["edge_provenance_total"] else 1.0
    sample_query_success = runtime["explicit_rule_count"] == runtime["explicit_rule_evidence_paths"] and runtime["explicit_rule_count"] > 0 and runtime["example_rulebox_count"] == 0
    passed = bool(conforms) and source_validation["critical_shacl_violation_count"] == 0 and rdf_node_coverage == 1.0 and rdf_edge_coverage == 1.0 and node_projection == 1.0 and edge_projection == 1.0 and provenance_projection == 1.0 and rdf_reference_projection == 1.0 and sample_query_success
    environment = {
        "rdflib_version": __import__("rdflib").__version__, "pyshacl_version": __import__("pyshacl").__version__,
        "neo4j_server": "4.4.43 Community", "neo4j_uri": neo4j_uri,
    }
    result = {
        "status": "PASS" if passed else "CONSERVATIVE_CORE_REVISE",
        "canonical_system": "R4-B1", "rdf_triple_count": len(parsed), "rdf_serialization_success": 1.0,
        "pyshacl_conforms": bool(conforms), "custom_critical_shacl_violations": source_validation["critical_shacl_violation_count"],
        "rdf_node_coverage": rdf_node_coverage, "rdf_edge_coverage": rdf_edge_coverage,
        "neo4j_node_projection_coverage": node_projection, "neo4j_edge_projection_coverage": edge_projection,
        "neo4j_provenance_property_coverage": provenance_projection,
        "neo4j_rdf_reference_coverage": rdf_reference_projection,
        "sample_evidence_path_query_success": sample_query_success,
        "runtime": runtime, "environment": environment, "test_access": 0,
    }
    r4.write_json(root / "reports" / "gate_r4_5.json", result)
    r4.write_json(root / "graphs" / "neo4j" / "runtime_validation.json", runtime)
    lines = [
        "# R4 RDF and Neo4j Projection Report", "", f"- Gate R4-5: **{result['status']}**",
        f"- Canonical graph: `R4-B1`", f"- RDF triples: `{len(parsed)}`",
        f"- Neo4j nodes/edges: `{runtime['node_count']}` / `{runtime['edge_count']}`", "- TEST access: `0`", "",
        "| Metric | Value | Gate |", "|---|---:|---:|",
        f"| RDF serialization | 1.0000 | 1.00 |", f"| pySHACL conforms | {int(bool(conforms)):.4f} | 1.00 |",
        f"| RDF node coverage | {rdf_node_coverage:.4f} | 1.00 |", f"| RDF edge coverage | {rdf_edge_coverage:.4f} | 1.00 |",
        f"| Neo4j node coverage | {node_projection:.4f} | 1.00 |", f"| Neo4j edge coverage | {edge_projection:.4f} | 1.00 |",
        f"| Neo4j provenance coverage | {provenance_projection:.4f} | 1.00 |",
        f"| Evidence-path runtime query | {int(sample_query_success):.4f} | 1.00 |",
        f"| Example in RuleBox query count | {runtime['example_rulebox_count']} | 0 |",
    ]
    (root / "reports" / "rdf_neo4j_projection_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if passed else 4


if __name__ == "__main__":
    raise SystemExit(main())
