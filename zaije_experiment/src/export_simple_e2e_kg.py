#!/usr/bin/env python3
"""Export the simple automatic KG to RDF, Neo4j CSV, queries, and SVG views."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import export_r5_graph as exporter
import r5_crsi as r5


EXPERIMENT_ID = "zaije_simple_e2e_pilot_20260712_v1"


def write_queries(root: Path) -> None:
    queries = {
        "01_workunit_actor": """MATCH p=(w:WorkUnit)-[:PERFORMED_BY]->(a)
WHERE w.system_id='SIMPLE-E2E' AND (a:Actor OR a:Organization)
RETURN p LIMIT 100;""",
        "02_workunit_input_output": """MATCH p=(w:WorkUnit)-[r]->(x)
WHERE w.system_id='SIMPLE-E2E' AND type(r) IN ['HAS_INPUT','PRODUCES_OUTPUT']
RETURN p LIMIT 120;""",
        "03_process_sequence": """MATCH p=(a:WorkUnit)-[:PRECEDES]->(b:WorkUnit)
WHERE a.system_id='SIMPLE-E2E' RETURN p LIMIT 100;""",
        "04_evidence_trace": """MATCH p=(m:Mention)-[:DERIVED_FROM]->(a:Anchor)<-[:HAS_ANCHOR]-(e:EvidenceBundle)
WHERE m.system_id='SIMPLE-E2E' RETURN p LIMIT 100;""",
        "05_confidence_summary": """MATCH (n) WHERE n.system_id='SIMPLE-E2E' AND n.type IN ['WorkUnit','Actor','Organization','Artifact','InformationObject']
RETURN n.type AS type,n.confidence AS confidence,count(*) AS count ORDER BY type,confidence;""",
    }
    qdir = root / "visualization" / "queries"
    qdir.mkdir(parents=True, exist_ok=True)
    for name, query in queries.items():
        (qdir / f"{name}.cypher").write_text(query + "\n", encoding="utf-8")
    (root / "visualization" / "style.grass").write_text(
        """node { diameter: 44px; color: #D9E2EC; border-color: #486581; border-width: 2px; caption: '{label}'; font-size: 10px; }
node.WorkUnit { color: #9CC4E4; border-color: #2563A6; }
node.Actor, node.Organization { color: #8FD3C7; border-color: #147D64; }
node.Artifact { color: #C6B5E8; border-color: #6B4FA1; }
node.InformationObject { color: #F7D774; border-color: #9A6700; }
node.Anchor, node.EvidenceBundle { color: #D5D7DA; border-color: #5F6368; }
relationship { color: #7B8794; shaft-width: 2px; caption: '<type>'; font-size: 8px; }
""",
        encoding="utf-8",
    )


def write_views(root: Path, nodes: list[dict], edges: list[dict]) -> dict:
    specs = {
        "01_workunit_actor.svg": ("Automatic WorkUnit and Actor", {"PERFORMED_BY"}, 45),
        "02_workunit_input_output.svg": ("Automatic Input and Output", {"HAS_INPUT", "PRODUCES_OUTPUT"}, 55),
        "03_process_sequence.svg": ("Automatic Process Sequence", {"PRECEDES"}, 45),
        "04_evidence_trace.svg": ("Automatic Evidence Trace", {"DENOTES", "DERIVED_FROM"}, 55),
    }
    out = root / "visualization" / "screenshots"
    manifest = []
    for filename, (title, relations, limit) in specs.items():
        selected_nodes, selected_edges = exporter.connected_view(nodes, edges, relations, limit)
        exporter.render_svg(out / filename, title, selected_nodes, selected_edges)
        manifest.append({
            "file": filename, "node_count": len(selected_nodes), "relationship_count": len(selected_edges),
            "non_empty": bool(selected_nodes and selected_edges), "sha256": r5.file_sha(out / filename),
        })
    r5.write_json(root / "visualization" / "manifest.json", manifest)
    return {"view_count": len(manifest), "non_empty_view_count": sum(x["non_empty"] for x in manifest), "views": manifest}


def main() -> int:
    project = Path(__file__).resolve().parents[1]
    root = project / "experiments" / EXPERIMENT_ID
    source = root / "graphs" / "jsonl"
    nodes = r5.read_jsonl(source / "nodes.jsonl")
    edges = r5.read_jsonl(source / "edges.jsonl")
    rdf = exporter.export_rdf(root, nodes, edges)
    exporter.export_csv(root, nodes, edges)
    write_queries(root)
    views = write_views(root, nodes, edges)
    metrics = r5.read_json(root / "evaluation" / "structural_metrics.json")
    dashboard = root / "visualization" / "metrics"
    dashboard.mkdir(parents=True, exist_ok=True)
    with (dashboard / "type_counts.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle); writer.writerow(["type", "count"])
        writer.writerows(sorted(metrics["required_type_counts"].items()))
    with (dashboard / "relation_counts.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle); writer.writerow(["relation", "count"])
        writer.writerows(sorted(metrics["required_relation_counts"].items()))
    summary = {
        **rdf, **views, "node_export_count": len(nodes), "relationship_export_count": len(edges),
        "human_intervention_count": 0, "llm_call_count": 0, "accuracy_claimed": False,
    }
    r5.write_json(root / "graphs" / "export_metrics.json", summary)
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if rdf["rdf_parse_pass"] and rdf["shacl_conforms"] and views["non_empty_view_count"] == len(views["views"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
