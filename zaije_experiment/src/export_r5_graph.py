#!/usr/bin/env python3
"""Export the selected R5 graph to RDF, Neo4j CSV, queries, and SVG views."""

from __future__ import annotations

import csv
import html
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import quote

from rdflib import Graph, Literal, Namespace, RDF, URIRef
from rdflib.namespace import XSD
from pyshacl import validate

import r5_crsi as r5


ZA = Namespace("https://example.org/zaije/")
RES = Namespace("https://example.org/zaije/resource/")


def uri(uid: str) -> URIRef:
    return URIRef(str(RES) + quote(uid, safe=""))


def export_rdf(root: Path, nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, Any]:
    graph = Graph()
    graph.bind("zaije", ZA); graph.bind("res", RES)
    for node in nodes:
        subject = uri(node["uid"])
        graph.add((subject, RDF.type, ZA[node["type"]]))
        graph.add((subject, ZA.uid, Literal(node["uid"])))
        graph.add((subject, ZA.systemId, Literal(node["system_id"])))
        graph.add((subject, ZA.label, Literal(str(node.get("preferred_label") or node.get("label") or node.get("exact_text") or node["id"]))))
        if node.get("operational"):
            graph.add((subject, ZA.operational, Literal(True, datatype=XSD.boolean)))
        for anchor in node.get("evidence_anchor_ids") or []:
            graph.add((subject, ZA.evidenceAnchorId, Literal(anchor)))
    for edge in edges:
        assertion = uri(edge["uid"])
        direct = ZA[edge["type"]]
        graph.add((uri(edge["source"]), direct, uri(edge["target"])))
        graph.add((assertion, RDF.type, ZA.CanonicalRelationAssertion if edge["type"] in r5.RELATION_REGISTRY else ZA.RelationAssertion))
        graph.add((assertion, ZA.uid, Literal(edge["uid"])))
        graph.add((assertion, ZA.relationType, Literal(edge["type"])))
        graph.add((assertion, ZA.source, uri(edge["source"])))
        graph.add((assertion, ZA.target, uri(edge["target"])))
        for anchor in edge.get("evidence_anchor_ids") or []:
            graph.add((assertion, ZA.evidenceAnchorId, Literal(anchor)))
    rdf_dir = root / "graphs" / "rdf"
    rdf_dir.mkdir(parents=True, exist_ok=True)
    path = rdf_dir / "r5_canonical.ttl"
    graph.serialize(path, format="turtle")
    parsed = Graph(); parsed.parse(path, format="turtle")
    shapes_text = """@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix zaije: <https://example.org/zaije/> .

zaije:CanonicalRelationShape a sh:NodeShape ;
  sh:targetClass zaije:CanonicalRelationAssertion ;
  sh:property [ sh:path zaije:source ; sh:minCount 1 ; sh:maxCount 1 ] ;
  sh:property [ sh:path zaije:target ; sh:minCount 1 ; sh:maxCount 1 ] ;
  sh:property [ sh:path zaije:relationType ; sh:minCount 1 ; sh:maxCount 1 ] ;
  sh:property [ sh:path zaije:evidenceAnchorId ; sh:minCount 1 ] .
"""
    shapes_path = root / "graphs" / "shacl" / "shapes.ttl"
    shapes_path.parent.mkdir(parents=True, exist_ok=True)
    shapes_path.write_text(shapes_text, encoding="utf-8")
    shapes_graph = Graph(); shapes_graph.parse(shapes_path, format="turtle")
    conforms, report_graph, report_text = validate(parsed, shacl_graph=shapes_graph, inference="none", abort_on_first=False)
    report_graph.serialize(root / "graphs" / "shacl" / "report.ttl", format="turtle")
    (root / "graphs" / "shacl" / "report.txt").write_text(report_text, encoding="utf-8")
    metrics = {"rdf_parse_pass": True, "rdf_triple_count": len(parsed), "shacl_conforms": bool(conforms), "critical_shacl_violation": 0 if conforms else 1}
    r5.write_json(root / "graphs" / "shacl" / "metrics.json", metrics)
    return metrics


def export_csv(root: Path, nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> None:
    out = root / "graphs" / "neo4j"
    out.mkdir(parents=True, exist_ok=True)
    with (out / "nodes.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["uid:ID", "id", "system_id", "type", "label", "evidence_anchor_ids", "props_json", ":LABEL"])
        for node in nodes:
            props = {k: v for k, v in node.items() if k not in {"uid", "id", "system_id", "type", "label", "preferred_label", "evidence_anchor_ids"}}
            writer.writerow([node["uid"], node["id"], node["system_id"], node["type"], str(node.get("preferred_label") or node.get("label") or node.get("exact_text") or node["id"])[:1000], json.dumps(node.get("evidence_anchor_ids") or [], ensure_ascii=False), json.dumps(props, ensure_ascii=False, sort_keys=True), f"R5Entity;{node['type']}"])
    with (out / "edges.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow([":START_ID", ":END_ID", "uid", "system_id", "type", "evidence_anchor_ids", "props_json", ":TYPE"])
        for edge in edges:
            props = {k: v for k, v in edge.items() if k not in {"uid", "id", "source", "target", "system_id", "type", "evidence_anchor_ids"}}
            writer.writerow([edge["source"], edge["target"], edge["uid"], edge["system_id"], edge["type"], json.dumps(edge.get("evidence_anchor_ids") or [], ensure_ascii=False), json.dumps(props, ensure_ascii=False, sort_keys=True), edge["type"]])
    r5.write_jsonl(out / "nodes.jsonl", nodes)
    r5.write_jsonl(out / "edges.jsonl", edges)


QUERIES = {
    "01_ontology_overview": """MATCH p=(a:R5Entity)-[r]->(b:R5Entity)
WHERE a.system_id=$system_id AND r.type IN ['HAS_DEFINITION','HAS_ALIAS','PRECEDES','HAS_CONDITION','HAS_QUANTITY_CONSTRAINT','HAS_FIELD']
RETURN p LIMIT 80;""",
    "02_work_process_map": """MATCH p=(a:WorkUnit)-[r:PRECEDES]->(b:WorkUnit)
WHERE a.system_id=$system_id RETURN p LIMIT 60;""",
    "03_rule_condition_map": """MATCH p=(r:Rule)-[rel]->(x)
WHERE r.system_id=$system_id AND type(rel) IN ['HAS_CONDITION','HAS_EXCEPTION','HAS_QUANTITY_CONSTRAINT','HAS_ACTION','DERIVED_FROM']
RETURN p LIMIT 80;""",
    "04_concept_resolution_map": """MATCH p=(m:Mention)-[:DENOTES]->(c:DomainConcept)
WHERE c.system_id=$system_id OPTIONAL MATCH q=(a:MergeActivity)-[:GENERATED]->(c)
RETURN p,q LIMIT 80;""",
    "05_template_field_map": """MATCH p=(t:Template)-[:HAS_FIELD]->(f:TemplateField)
WHERE t.system_id=$system_id RETURN p LIMIT 80;""",
    "06_evidence_trace": """MATCH p=(x:R5Entity)-[:DERIVED_FROM]->(a:Anchor)<-[:HAS_ANCHOR]-(e:EvidenceBundle)<-[:HAS_EVIDENCE]-(s:Section)
WHERE x.system_id=$system_id RETURN p LIMIT 60;""",
    "07_baseline_comparison": """MATCH (m:Mention)-[:DENOTES]->(c:DomainConcept)
WHERE c.system_id=$system_id WITH c,count(m) AS surface_count WHERE surface_count>1
RETURN c.uid,c.label,surface_count ORDER BY surface_count DESC LIMIT 30;""",
    "08_orphan_provenance_check": """MATCH (n:R5Entity) WHERE n.system_id=$system_id AND n.type IN ['DomainConcept','Rule','Condition','Metric','Template','TemplateField','WorkUnit']
AND coalesce(n.evidence_anchor_ids,'[]')='[]' RETURN count(n) AS orphan_count;""",
}


def write_queries(root: Path) -> None:
    qdir = root / "visualization" / "queries"
    for name, query in QUERIES.items():
        text = ":param system_id => 'R5-B1';\n" + query + "\n"
        (qdir / f"{name}.cypher").parent.mkdir(parents=True, exist_ok=True)
        (qdir / f"{name}.cypher").write_text(text, encoding="utf-8")
    grass = """node { diameter: 44px; color: #D9E2EC; border-color: #486581; border-width: 2px; text-color-internal: #102A43; caption: '{label}'; font-size: 10px; }
node.DomainConcept { color: #8FD3C7; border-color: #147D64; }
node.WorkUnit { color: #9CC4E4; border-color: #2563A6; }
node.Rule { color: #F4B183; border-color: #B45309; }
node.Condition { color: #F7D774; border-color: #9A6700; }
node.Metric { color: #E7A6B6; border-color: #9F3151; }
node.Template, node.TemplateField { color: #C6B5E8; border-color: #6B4FA1; }
node.Anchor, node.EvidenceBundle { color: #D5D7DA; border-color: #5F6368; }
relationship { color: #7B8794; shaft-width: 2px; caption: '<type>'; font-size: 8px; }
"""
    (root / "visualization" / "style.grass").write_text(grass, encoding="utf-8")


COLORS = {"DomainConcept": "#8FD3C7", "Mention": "#D8F0EB", "WorkUnit": "#9CC4E4", "Rule": "#F4B183", "Condition": "#F7D774", "Metric": "#E7A6B6", "Template": "#C6B5E8", "TemplateField": "#DDD4F2", "Anchor": "#D5D7DA", "EvidenceBundle": "#ECEEF0", "MergeActivity": "#B6D7A8"}


def render_svg(path: Path, title: str, selected_nodes: list[dict[str, Any]], selected_edges: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    nodes = {n["uid"]: n for n in selected_nodes}
    selected_edges = [e for e in selected_edges if e["source"] in nodes and e["target"] in nodes]
    width, height = 1400, 850
    count = max(1, len(nodes))
    positions = {}
    ordered = sorted(nodes)
    for i, uid in enumerate(ordered):
        ring = i % 3
        angle = 2 * math.pi * i / count
        radius = 210 + ring * 85
        positions[uid] = (width / 2 + radius * math.cos(angle), height / 2 + radius * .72 * math.sin(angle))
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="#FAFBFC"/>', f'<text x="40" y="50" font-family="sans-serif" font-size="26" font-weight="700" fill="#102A43">{html.escape(title)}</text>',
             f'<text x="40" y="78" font-family="sans-serif" font-size="13" fill="#52606D">R5-B1 | nodes {len(nodes)} | relationships {len(selected_edges)}</text>']
    for edge in selected_edges:
        x1, y1 = positions[edge["source"]]; x2, y2 = positions[edge["target"]]
        parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#9AA5B1" stroke-width="1.5"/>')
        mx, my = (x1+x2)/2, (y1+y2)/2
        parts.append(f'<text x="{mx:.1f}" y="{my:.1f}" font-family="sans-serif" font-size="8" fill="#52606D">{html.escape(edge["type"])}</text>')
    for uid in ordered:
        node = nodes[uid]; x, y = positions[uid]
        label = str(node.get("preferred_label") or node.get("label") or node.get("exact_text") or node["id"]).replace("\n", " ")
        label = label[:22] + ("..." if len(label) > 22 else "")
        color = COLORS.get(node["type"], "#D9E2EC")
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="31" fill="{color}" stroke="#486581" stroke-width="1.5"/>')
        parts.append(f'<text x="{x:.1f}" y="{y+4:.1f}" text-anchor="middle" font-family="sans-serif" font-size="8" fill="#102A43">{html.escape(label)}</text>')
        parts.append(f'<text x="{x:.1f}" y="{y+44:.1f}" text-anchor="middle" font-family="sans-serif" font-size="8" fill="#52606D">{html.escape(node["type"])}</text>')
    parts.append('</svg>')
    path.write_text("\n".join(parts), encoding="utf-8")


def connected_view(nodes: list[dict[str, Any]], edges: list[dict[str, Any]], edge_types: set[str], limit: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    chosen_edges = [e for e in edges if e["type"] in edge_types][:limit]
    uids = {u for e in chosen_edges for u in (e["source"], e["target"])}
    by_uid = {n["uid"]: n for n in nodes}
    return [by_uid[u] for u in sorted(uids) if u in by_uid], chosen_edges


def write_views(root: Path, nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, Any]:
    out = root / "visualization" / "screenshots"
    specs = {
        "01_ontology_overview.svg": ("Ontology Overview", {"HAS_DEFINITION", "HAS_ALIAS", "PRECEDES", "HAS_CONDITION", "HAS_FIELD"}, 35),
        "02_work_process_map.svg": ("Work Process Map", {"PRECEDES"}, 35),
        "03_rule_condition_map.svg": ("Rule, Condition and Quantity", {"HAS_CONDITION", "HAS_EXCEPTION", "HAS_QUANTITY_CONSTRAINT", "HAS_ACTION"}, 35),
        "04_concept_resolution_map.svg": ("Concept Resolution", {"DENOTES", "GENERATED", "USED"}, 45),
        "05_template_field_map.svg": ("Template and Field", {"HAS_FIELD"}, 30),
        "06_evidence_trace.svg": ("Evidence Trace", {"DERIVED_FROM", "HAS_ANCHOR", "HAS_EVIDENCE"}, 45),
        "07a_baseline_fragmented.svg": ("B0 Surface Fragmentation", {"REL_ALIAS_OF"}, 35),
        "07b_proposed_canonical.svg": ("B1 Canonical Concepts", {"HAS_ALIAS", "DENOTES"}, 35),
    }
    manifest = []
    for filename, (title, rels, limit) in specs.items():
        ns, es = connected_view(nodes, edges, rels, limit)
        render_svg(out / filename, title, ns, es)
        manifest.append({"file": filename, "node_count": len(ns), "relationship_count": len(es), "non_empty": bool(ns and es), "sha256": r5.file_sha(out / filename)})
    r5.write_json(root / "visualization" / "manifest.json", manifest)
    return {"views": manifest, "required_six_non_empty": sum(x["non_empty"] for x in manifest[:6])}


def write_metrics_csv(root: Path) -> None:
    out = root / "visualization" / "metrics"
    out.mkdir(parents=True, exist_ok=True)
    confirm = r5.read_json(root / "evaluation" / "confirmatory" / "llm_comparison.json")
    dev = r5.read_json(root / "evaluation" / "dev" / "llm_comparison.json")
    full = r5.read_json(root / "full_non_test" / "r5_b1" / "metrics.json")
    with (out / "system_metrics.csv").open("w", encoding="utf-8", newline="") as h:
        w=csv.writer(h); w.writerow(["split","system","nodes","relationships","safe_yield","critical_violations","provenance","unsupported_label_rate"])
        for split, data in (("DEV",dev),("CONFIRMATORY",confirm)):
            for system,m in data["systems"].items(): w.writerow([split,system,m["node_count"],m["relationship_count"],m["safe_ontology_yield"],m["critical_shacl_violation"],m["promoted_provenance_completeness"],m["unsupported_label_rate"]])
        w.writerow(["FULL_DEMO","R5-B1",full["node_count"],full["relationship_count"],full["safe_ontology_yield"],full["critical_shacl_violation"],full["promoted_provenance_completeness"],full["unsupported_label_rate"]])
    for name, rows in {
        "concept_metrics.csv": [["metric","value"],["canonical_concepts",full["canonical_concept_count"]],["surface_mentions",full["surface_mention_count"]],["fragmentation_reduction",full["fragmentation_reduction"]],["explicit_alias_recall",full["explicit_alias_recall"]]],
        "relation_metrics.csv": [["metric","value"],["relationship_count",full["relationship_count"]],["relation_evidence_coverage",full["relation_evidence_coverage"]],["domain_range_violation",full["critical_domain_range_violation"]],["taxonomy_cycle",full["taxonomy_cycle"]]],
        "cq_metrics.csv": [["split","system","answerability","provenance_precision"]]+[[split,system,v["answerability"],v["provenance_precision"]] for split,d in (("DEV",dev),("CONFIRMATORY",confirm)) for system,v in d["cq"].items()],
        "cost_metrics.csv": [["split","system","input_tokens","output_tokens","total_tokens"]]+[[split,system,u["input_tokens"],u["output_tokens"],u["total_tokens"]] for split,d in (("DEV",dev),("CONFIRMATORY",confirm)) for system,u in d["usage"].items()],
    }.items():
        with (out/name).open("w",encoding="utf-8",newline="") as h: csv.writer(h).writerows(rows)


def main() -> int:
    project = Path(__file__).resolve().parents[1]
    root = project / "experiments" / r5.EXPERIMENT_ID
    source = root / "full_non_test" / "r5_b1"
    nodes, edges = r5.read_jsonl(source / "nodes.jsonl"), r5.read_jsonl(source / "edges.jsonl")
    rdf_metrics = export_rdf(root, nodes, edges)
    export_csv(root, nodes, edges)
    write_queries(root)
    view_metrics = write_views(root, nodes, edges)
    write_metrics_csv(root)
    summary = {**rdf_metrics, **view_metrics, "neo4j_node_export_count": len(nodes), "neo4j_relationship_export_count": len(edges)}
    r5.write_json(root / "graphs" / "export_metrics.json", summary)
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
