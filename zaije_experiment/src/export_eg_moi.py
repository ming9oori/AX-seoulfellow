#!/usr/bin/env python3
"""Export EG-MOI outputs to RDF/SKOS/PROV-O/SHACL, Neo4j CSV, and SVG views."""

from __future__ import annotations

import csv
import hashlib
import html
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import quote

from pyshacl import validate
from rdflib import Graph, Literal, Namespace, RDF, URIRef
from rdflib.namespace import PROV, SH, SKOS, XSD


EXPERIMENT_ID = "zaije_eg_moi_20260712_v1"
SYSTEM_ID = "EG-MOI-V1"
EG = Namespace("https://example.org/eg-moi/")
RES = Namespace("https://example.org/eg-moi/resource/")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.open(encoding="utf-8") if line.strip()]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def uri(uid: str) -> URIRef:
    return URIRef(str(RES) + quote(uid, safe=""))


def predicate(value: str) -> URIRef:
    name = re.sub(r"[^A-Za-z0-9_]", "_", value)
    return EG[name]


def literal(value: Any) -> Literal:
    if isinstance(value, bool):
        return Literal(value, datatype=XSD.boolean)
    if isinstance(value, int):
        return Literal(value, datatype=XSD.integer)
    if isinstance(value, float):
        return Literal(value, datatype=XSD.decimal)
    if isinstance(value, (list, dict)):
        return Literal(json.dumps(value, ensure_ascii=False, sort_keys=True), datatype=RDF.JSON)
    return Literal(str(value))


def canonical_graph(nodes: list[dict], edges: list[dict]) -> Graph:
    graph = Graph()
    for prefix, ns in (("eg", EG), ("res", RES), ("prov", PROV), ("skos", SKOS)):
        graph.bind(prefix, ns)
    for node in nodes:
        subject = uri(node["uid"])
        graph.add((subject, RDF.type, EG[node["type"]]))
        graph.add((subject, EG.uid, Literal(node["uid"])))
        graph.add((subject, EG.systemId, Literal(node["system_id"])))
        label = node.get("preferred_label") or node.get("label") or node.get("exact_text") or node["id"]
        graph.add((subject, EG.label, Literal(str(label))))
        for key, value in node.items():
            if key in {"id", "uid", "system_id", "type", "label", "preferred_label"} or value is None:
                continue
            graph.add((subject, predicate(key), literal(value)))
    for edge in edges:
        source, target = uri(edge["source"]), uri(edge["target"])
        graph.add((source, predicate(edge["type"]), target))
    return graph


def skos_graph(nodes: list[dict]) -> Graph:
    graph = Graph()
    graph.bind("eg", EG); graph.bind("res", RES); graph.bind("skos", SKOS)
    scheme = RES["zaije-eg-moi-concept-scheme"]
    graph.add((scheme, RDF.type, SKOS.ConceptScheme))
    graph.add((scheme, SKOS.prefLabel, Literal("자이제 EG-MOI 귀납 개념 체계", lang="ko")))
    for node in nodes:
        if node["type"] != "ConceptCluster" or node.get("status") != "VALIDATED":
            continue
        subject = uri(node["uid"])
        graph.add((subject, RDF.type, SKOS.Concept))
        graph.add((subject, SKOS.inScheme, scheme))
        graph.add((subject, SKOS.prefLabel, Literal(node.get("preferred_label") or node.get("label"), lang="ko")))
        for alt in node.get("surface_forms") or []:
            if alt != node.get("preferred_label"):
                graph.add((subject, SKOS.altLabel, Literal(alt)))
        graph.add((subject, EG.domainType, Literal(node.get("domain_type", ""))))
        graph.add((subject, EG.metaType, Literal(node.get("meta_type", ""))))
    return graph


def provenance_graph(nodes: list[dict], edges: list[dict]) -> Graph:
    graph = Graph()
    graph.bind("eg", EG); graph.bind("res", RES); graph.bind("prov", PROV)
    for node in nodes:
        subject = uri(node["uid"])
        if node["type"] == "ExtractionActivity":
            graph.add((subject, RDF.type, PROV.Activity))
        elif node["type"] in {"Mention", "SemanticFrame", "ConceptCluster", "RelationCluster", "Assertion", "SchemaClass", "SchemaProperty"}:
            graph.add((subject, RDF.type, PROV.Entity))
        else:
            continue
        graph.add((subject, EG.uid, Literal(node["uid"])))
    for edge in edges:
        if edge["type"] == "DERIVED_FROM":
            graph.add((uri(edge["source"]), PROV.wasDerivedFrom, uri(edge["target"])))
        elif edge["type"] == "WAS_GENERATED_BY":
            graph.add((uri(edge["source"]), PROV.wasGeneratedBy, uri(edge["target"])))
    return graph


def shape_graph() -> Graph:
    graph = Graph()
    graph.bind("eg", EG); graph.bind("sh", SH)

    def property_shape(shape: URIRef, path: URIRef, minimum: int = 1, value: Any | None = None) -> None:
        prop = URIRef(str(shape) + "Property" + hashlib.sha1(str(path).encode()).hexdigest()[:8])
        graph.add((shape, SH.property, prop))
        graph.add((prop, SH.path, path))
        graph.add((prop, SH.minCount, Literal(minimum)))
        if value is not None:
            graph.add((prop, SH.hasValue, literal(value)))

    evidence_shape = EG.EvidenceUnitShape
    graph.add((evidence_shape, RDF.type, SH.NodeShape)); graph.add((evidence_shape, SH.targetClass, EG.EvidenceUnit))
    property_shape(evidence_shape, EG.exact_text)

    mention_shape = EG.MentionShape
    graph.add((mention_shape, RDF.type, SH.NodeShape)); graph.add((mention_shape, SH.targetClass, EG.Mention))
    property_shape(mention_shape, EG.DERIVED_FROM); property_shape(mention_shape, EG.DENOTES)

    assertion_shape = EG.AssertionShape
    graph.add((assertion_shape, RDF.type, SH.NodeShape)); graph.add((assertion_shape, SH.targetClass, EG.Assertion))
    property_shape(assertion_shape, EG.DERIVED_FROM); property_shape(assertion_shape, EG.WAS_GENERATED_BY)
    property_shape(assertion_shape, EG.status, value="VALIDATED")

    cluster_shape = EG.ValidatedClusterShape
    graph.add((cluster_shape, RDF.type, SH.NodeShape)); graph.add((cluster_shape, SH.targetClass, EG.ConceptCluster))
    property_shape(cluster_shape, EG.status); property_shape(cluster_shape, EG.evidence_anchor_ids)
    return graph


def export_rdf(root: Path, nodes: list[dict], edges: list[dict]) -> dict[str, Any]:
    out = root / "rdf"
    out.mkdir(parents=True, exist_ok=True)
    canonical = canonical_graph(nodes, edges)
    skos = skos_graph(nodes)
    prov = provenance_graph(nodes, edges)
    shapes = shape_graph()
    canonical.serialize(out / "canonical.ttl", format="turtle")
    skos.serialize(out / "concepts.skos.ttl", format="turtle")
    prov.serialize(out / "provenance.prov.ttl", format="turtle")
    shapes.serialize(out / "shapes.ttl", format="turtle")

    conforms, report_graph, report_text = validate(
        data_graph=canonical, shacl_graph=shapes, inference="rdfs", abort_on_first=False,
        allow_infos=True, allow_warnings=True, meta_shacl=True, advanced=True,
    )
    report_graph.serialize(out / "validation_report.ttl", format="turtle")
    (out / "validation_report.txt").write_text(report_text, encoding="utf-8")

    # Parse every serialized product again so the pass is about files on disk.
    parse_counts = {}
    for filename in ("canonical.ttl", "concepts.skos.ttl", "provenance.prov.ttl", "shapes.ttl", "validation_report.ttl"):
        parsed = Graph().parse(out / filename, format="turtle")
        parse_counts[filename] = len(parsed)
    metrics = {
        "canonical_triple_count": len(canonical),
        "skos_triple_count": len(skos),
        "prov_o_triple_count": len(prov),
        "shape_triple_count": len(shapes),
        "shacl_conforms": bool(conforms),
        "serialized_parse_counts": parse_counts,
        "all_rdf_files_parse": all(parse_counts.values()),
    }
    write_json(out / "rdf_validation_metrics.json", metrics)
    return metrics


def export_neo4j(root: Path, nodes: list[dict], edges: list[dict]) -> dict[str, Any]:
    out = root / "neo4j"
    out.mkdir(parents=True, exist_ok=True)
    with (out / "nodes.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["uid:ID", "id", "system_id", "type", "label", "status", "evidence_anchor_ids", "props_json", ":LABEL"])
        for node in nodes:
            excluded = {"uid", "id", "system_id", "type", "label", "preferred_label", "status", "evidence_anchor_ids"}
            props = {key: value for key, value in node.items() if key not in excluded}
            label = str(node.get("preferred_label") or node.get("label") or node.get("exact_text") or node["id"])
            writer.writerow([
                node["uid"], node["id"], node["system_id"], node["type"], label[:2000], node.get("status", ""),
                json.dumps(node.get("evidence_anchor_ids") or [], ensure_ascii=False),
                json.dumps(props, ensure_ascii=False, sort_keys=True), f"EGEntity;{node['type']}",
            ])
    with (out / "edges.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow([":START_ID", ":END_ID", "uid", "system_id", "type", "status", "evidence_anchor_ids", "props_json", ":TYPE"])
        for edge in edges:
            excluded = {"uid", "id", "source", "target", "system_id", "type", "status", "evidence_anchor_ids"}
            props = {key: value for key, value in edge.items() if key not in excluded}
            writer.writerow([
                edge["source"], edge["target"], edge["uid"], edge["system_id"], edge["type"], edge.get("status", ""),
                json.dumps(edge.get("evidence_anchor_ids") or [], ensure_ascii=False),
                json.dumps(props, ensure_ascii=False, sort_keys=True), edge["type"],
            ])
    return {"neo4j_node_export_count": len(nodes), "neo4j_relationship_export_count": len(edges)}


QUERIES = {
    "01_schema_overview": "MATCH p=(c:SchemaClass)-[:SUBCLASS_OF]->(m:MetaClass) RETURN p LIMIT 80;",
    "02_operational_assertions": "MATCH p=(a:ConceptCluster)-[r]->(b:ConceptCluster) WHERE type(r) IN ['PERFORMED_BY','HAS_INPUT','PRODUCES_OUTPUT','HAS_CONDITION','HAS_MEASURE','PRECEDES'] RETURN p LIMIT 100;",
    "03_concept_consolidation": "MATCH p=(m:Mention)-[:DENOTES]->(c:ConceptCluster) WHERE c.status='VALIDATED' RETURN p LIMIT 100;",
    "04_evidence_trace": "MATCH p=(x:Assertion)-[:DERIVED_FROM]->(a:EvidenceUnit)<-[:HAS_ANCHOR]-(e:EvidenceUnit) RETURN p LIMIT 100;",
    "05_provenance_activity": "MATCH p=(x:Assertion)-[:WAS_GENERATED_BY]->(a:ExtractionActivity) RETURN p LIMIT 100;",
    "06_unresolved_clusters": "MATCH (c:ConceptCluster {status:'UNRESOLVED'}) RETURN c LIMIT 100;",
}


COLORS = {
    "ConceptCluster": "#8FD3C7", "Mention": "#D8F0EB", "SemanticFrame": "#9CC4E4",
    "Assertion": "#F4B183", "SchemaClass": "#C6B5E8", "MetaClass": "#DDD4F2",
    "EvidenceUnit": "#D5D7DA", "ExtractionActivity": "#F7D774",
}


def render_svg(path: Path, title: str, selected_nodes: list[dict], selected_edges: list[dict]) -> None:
    nodes = {node["uid"]: node for node in selected_nodes}
    selected_edges = [edge for edge in selected_edges if edge["source"] in nodes and edge["target"] in nodes]
    width, height = 1400, 850
    ordered = sorted(nodes)
    positions = {}
    count = max(1, len(ordered))
    for index, uid_value in enumerate(ordered):
        ring = index % 3
        angle = 2 * math.pi * index / count
        radius = 210 + ring * 85
        positions[uid_value] = (width / 2 + radius * math.cos(angle), height / 2 + radius * 0.72 * math.sin(angle))
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#FAFBFC"/>',
        f'<text x="40" y="50" font-family="sans-serif" font-size="26" font-weight="700" fill="#102A43">{html.escape(title)}</text>',
        f'<text x="40" y="78" font-family="sans-serif" font-size="13" fill="#52606D">EG-MOI | nodes {len(nodes)} | relationships {len(selected_edges)}</text>',
    ]
    for edge in selected_edges:
        x1, y1 = positions[edge["source"]]; x2, y2 = positions[edge["target"]]
        parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#9AA5B1" stroke-width="1.5"/>')
        parts.append(f'<text x="{(x1+x2)/2:.1f}" y="{(y1+y2)/2:.1f}" font-family="sans-serif" font-size="8" fill="#52606D">{html.escape(edge["type"])}</text>')
    for uid_value in ordered:
        node = nodes[uid_value]; x, y = positions[uid_value]
        label = str(node.get("preferred_label") or node.get("label") or node.get("exact_text") or node["id"]).replace("\n", " ")
        label = label[:20] + ("..." if len(label) > 20 else "")
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="31" fill="{COLORS.get(node["type"], "#E5E7EB")}" stroke="#486581" stroke-width="1.5"/>')
        parts.append(f'<text x="{x:.1f}" y="{y+4:.1f}" text-anchor="middle" font-family="sans-serif" font-size="8" fill="#102A43">{html.escape(label)}</text>')
        parts.append(f'<text x="{x:.1f}" y="{y+44:.1f}" text-anchor="middle" font-family="sans-serif" font-size="8" fill="#52606D">{html.escape(node["type"])}</text>')
    parts.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts), encoding="utf-8")


def write_visualization(root: Path, nodes: list[dict], edges: list[dict]) -> dict[str, Any]:
    qdir = root / "visualization" / "queries"
    qdir.mkdir(parents=True, exist_ok=True)
    for name, query in QUERIES.items():
        (qdir / f"{name}.cypher").write_text(query + "\n", encoding="utf-8")
    (root / "visualization" / "style.grass").write_text(
        "node { diameter: 44px; caption: '{label}'; font-size: 10px; color: #D9E2EC; border-color: #486581; }\n"
        "node.ConceptCluster { color: #8FD3C7; }\nnode.Assertion { color: #F4B183; }\n"
        "node.SchemaClass { color: #C6B5E8; }\nnode.EvidenceUnit { color: #D5D7DA; }\n"
        "relationship { caption: '<type>'; color: #7B8794; }\n", encoding="utf-8",
    )
    specs = {
        "01_schema.svg": ("Induced Schema", {"SUBCLASS_OF", "INSTANCE_OF"}, 45),
        "02_operations.svg": ("Operational Assertions", {"PERFORMED_BY", "HAS_INPUT", "PRODUCES_OUTPUT", "HAS_CONDITION", "HAS_MEASURE", "PRECEDES"}, 60),
        "03_consolidation.svg": ("Mention to Concept Consolidation", {"DENOTES"}, 60),
        "04_evidence_trace.svg": ("Assertion Evidence Trace", {"DERIVED_FROM"}, 60),
        "05_provenance.svg": ("Extraction Provenance", {"WAS_GENERATED_BY"}, 60),
    }
    by_uid = {node["uid"]: node for node in nodes}
    manifest = []
    for filename, (title, relations, limit) in specs.items():
        chosen_edges = [edge for edge in edges if edge["type"] in relations][:limit]
        uids = {uid_value for edge in chosen_edges for uid_value in (edge["source"], edge["target"])}
        chosen_nodes = [by_uid[uid_value] for uid_value in sorted(uids) if uid_value in by_uid]
        path = root / "visualization" / "screenshots" / filename
        render_svg(path, title, chosen_nodes, chosen_edges)
        manifest.append({"file": filename, "node_count": len(chosen_nodes), "relationship_count": len(chosen_edges), "non_empty": bool(chosen_nodes and chosen_edges), "sha256": file_sha(path)})
    write_json(root / "visualization" / "manifest.json", manifest)
    metrics = read_json(root / "evaluation" / "structural_metrics.json")
    mdir = root / "visualization" / "metrics"
    mdir.mkdir(parents=True, exist_ok=True)
    for filename, values in (
        ("node_type_counts.csv", metrics["node_type_counts"]),
        ("relationship_type_counts.csv", metrics["relationship_type_counts"]),
    ):
        with (mdir / filename).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle); writer.writerow(["name", "count"]); writer.writerows(sorted(values.items()))
    return {"visualization_count": len(manifest), "non_empty_visualization_count": sum(item["non_empty"] for item in manifest)}


def main() -> int:
    project = Path(__file__).resolve().parents[1]
    root = project / "experiments" / EXPERIMENT_ID
    nodes = read_jsonl(root / "graph" / "nodes.jsonl")
    edges = read_jsonl(root / "graph" / "edges.jsonl")
    rdf = export_rdf(root, nodes, edges)
    neo4j = export_neo4j(root, nodes, edges)
    views = write_visualization(root, nodes, edges)
    metrics = {**rdf, **neo4j, **views}
    metrics["pass"] = bool(rdf["shacl_conforms"] and rdf["all_rdf_files_parse"] and views["visualization_count"] == views["non_empty_visualization_count"])
    write_json(root / "evaluation" / "export_metrics.json", metrics)
    print(json.dumps(metrics, ensure_ascii=False))
    return 0 if metrics["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
