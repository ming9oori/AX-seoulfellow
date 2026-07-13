#!/usr/bin/env python3
"""Execute the five representative Cypher queries and render their live results."""

from __future__ import annotations

import base64
import hashlib
import html
import json
import math
import os
from collections import Counter
from pathlib import Path
from typing import Any

from neo4j import GraphDatabase


EXPERIMENT_ID = "zaije_eg_moi_20260712_v1"

QUERY_SPECS = [
    {
        "key": "01_schema",
        "title": "1. Induced Schema",
        "relation": "SUBCLASS_OF",
        "total_query": "MATCH (:SchemaClass)-[r:SUBCLASS_OF]->(:MetaClass) RETURN count(r) AS count",
        "graph_query": """
MATCH (a:SchemaClass)-[r:SUBCLASS_OF]->(b:MetaClass)
RETURN a.uid AS source_uid,a.type AS source_type,a.label AS source_label,a.props_json AS source_props,
       type(r) AS relation,b.uid AS target_uid,b.type AS target_type,b.label AS target_label,b.props_json AS target_props
LIMIT 50
""",
    },
    {
        "key": "02_input_output",
        "title": "2. Work Input and Output",
        "relation": "HAS_INPUT / PRODUCES_OUTPUT",
        "total_query": """
MATCH (:ConceptCluster)-[r]->(:ConceptCluster)
WHERE type(r) IN ['HAS_INPUT','PRODUCES_OUTPUT']
RETURN count(r) AS count
""",
        "graph_query": """
MATCH (a:ConceptCluster)-[r]->(b:ConceptCluster)
WHERE type(r) IN ['HAS_INPUT','PRODUCES_OUTPUT']
RETURN a.uid AS source_uid,a.type AS source_type,a.label AS source_label,a.props_json AS source_props,
       type(r) AS relation,b.uid AS target_uid,b.type AS target_type,b.label AS target_label,b.props_json AS target_props
LIMIT 50
""",
    },
    {
        "key": "03_performer",
        "title": "3. Work Performer",
        "relation": "PERFORMED_BY",
        "total_query": "MATCH (:ConceptCluster)-[r:PERFORMED_BY]->(:ConceptCluster) RETURN count(r) AS count",
        "graph_query": """
MATCH (a:ConceptCluster)-[r:PERFORMED_BY]->(b:ConceptCluster)
RETURN a.uid AS source_uid,a.type AS source_type,a.label AS source_label,a.props_json AS source_props,
       type(r) AS relation,b.uid AS target_uid,b.type AS target_type,b.label AS target_label,b.props_json AS target_props
LIMIT 30
""",
    },
    {
        "key": "04_sequence",
        "title": "4. Work Sequence",
        "relation": "PRECEDES",
        "total_query": "MATCH (:ConceptCluster)-[r:PRECEDES]->(:ConceptCluster) RETURN count(r) AS count",
        "graph_query": """
MATCH (a:ConceptCluster)-[r:PRECEDES]->(b:ConceptCluster)
RETURN a.uid AS source_uid,a.type AS source_type,a.label AS source_label,a.props_json AS source_props,
       type(r) AS relation,b.uid AS target_uid,b.type AS target_type,b.label AS target_label,b.props_json AS target_props
LIMIT 50
""",
    },
    {
        "key": "05_evidence",
        "title": "5. Assertion Evidence Trace",
        "relation": "DERIVED_FROM",
        "total_query": "MATCH (:Assertion)-[r:DERIVED_FROM]->(:EvidenceUnit) RETURN count(r) AS count",
        "graph_query": """
MATCH (a:Assertion)-[r:DERIVED_FROM]->(b:EvidenceUnit)
RETURN a.uid AS source_uid,a.type AS source_type,a.label AS source_label,a.props_json AS source_props,
       type(r) AS relation,b.uid AS target_uid,b.type AS target_type,b.label AS target_label,b.props_json AS target_props
LIMIT 50
""",
    },
]

SCHEMA_COLORS = {
    "ProposalWorkUnit": "#9CC9F2",
    "ProposalRole": "#A8D5A2",
    "ProposalOrganization": "#63C7B2",
    "ProposalArtifact": "#C3A6E8",
    "CustomerRequirement": "#F5D267",
    "ProposalContext": "#F4AD82",
    "EvaluationMeasure": "#ECA0BD",
    "ProposalDomainConcept": "#B9C2CC",
    "WorkUnit": "#6EA8E5",
    "Agent": "#58BFA3",
    "Resource": "#9D7CCC",
    "Context": "#E8935B",
    "Measure": "#D96C8C",
    "DomainConcept": "#8996A3",
    "Assertion": "#F39C5A",
    "EvidenceUnit": "#D7DCE2",
    "SchemaClass": "#B69DDB",
    "MetaClass": "#C9D0D8",
}

RELATION_COLORS = {
    "SUBCLASS_OF": "#7451A6",
    "HAS_INPUT": "#B8860B",
    "PRODUCES_OUTPUT": "#7B4FA1",
    "PERFORMED_BY": "#16866D",
    "PRECEDES": "#3578B8",
    "DERIVED_FROM": "#6B7280",
}


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def props(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return {}


def display_label(label: str | None, node_type: str, props_json: str | None) -> str:
    data = props(props_json)
    if node_type == "EvidenceUnit" and data.get("exact_text"):
        return str(data["exact_text"])
    return str(label or data.get("exact_text") or node_type)


def schema_key(node_type: str, label: str | None, props_json: str | None) -> str:
    data = props(props_json)
    if node_type == "ConceptCluster":
        return str(data.get("domain_type") or data.get("meta_type") or node_type)
    if node_type == "SchemaClass":
        return str(label or data.get("meta_type") or node_type)
    if node_type == "MetaClass":
        return str(label or node_type)
    return node_type


def clean_label(value: str, limit: int) -> str:
    value = " ".join(value.replace("\n", " ").split())
    return value[:limit] + ("..." if len(value) > limit else "")


def grouped_positions(
    nodes: dict[str, dict[str, str]],
    width: int,
    height: int,
) -> tuple[dict[str, tuple[float, float]], dict[str, tuple[float, float, float]]]:
    groups: dict[str, list[str]] = {}
    for uid, node in nodes.items():
        groups.setdefault(node["schema"], []).append(uid)
    keys = sorted(groups)
    center_x, center_y = width / 2, height / 2 + 55
    centers: dict[str, tuple[float, float]] = {}
    if len(keys) == 1:
        centers[keys[0]] = (center_x, center_y)
    elif len(keys) == 2:
        centers[keys[0]] = (width * 0.29, center_y)
        centers[keys[1]] = (width * 0.71, center_y)
    else:
        for index, key in enumerate(keys):
            angle = 2 * math.pi * index / len(keys) - math.pi / 2
            centers[key] = (
                center_x + width * 0.34 * math.cos(angle),
                center_y + height * 0.28 * math.sin(angle),
            )
    result: dict[str, tuple[float, float]] = {}
    bounds: dict[str, tuple[float, float, float]] = {}
    for key in keys:
        members = sorted(groups[key])
        cx, cy = centers[key]
        if len(members) == 1:
            result[members[0]] = (cx, cy)
            bounds[key] = (cx, cy, 58)
            continue
        cursor = 0
        ring = 0
        maximum_radius = 0.0
        while cursor < len(members):
            capacity = 10 + ring * 8
            ring_members = members[cursor : cursor + capacity]
            radius = 72 + ring * 62
            maximum_radius = radius
            for offset, uid in enumerate(ring_members):
                angle = 2 * math.pi * offset / len(ring_members) + ring * 0.22
                result[uid] = (cx + radius * math.cos(angle), cy + radius * math.sin(angle))
            cursor += len(ring_members)
            ring += 1
        bounds[key] = (cx, cy, maximum_radius + 52)
    return result, bounds


def build_svg(
    title: str,
    total_count: int,
    rows: list[dict[str, Any]],
    returned_count: int | None = None,
) -> str:
    nodes: dict[str, dict[str, str]] = {}
    edges = []
    for row in rows:
        source_type = str(row["source_type"])
        target_type = str(row["target_type"])
        source_uid = str(row["source_uid"])
        target_uid = str(row["target_uid"])
        nodes[source_uid] = {
            "type": source_type,
            "label": display_label(row["source_label"], source_type, row["source_props"]),
            "schema": schema_key(source_type, row["source_label"], row["source_props"]),
        }
        nodes[target_uid] = {
            "type": target_type,
            "label": display_label(row["target_label"], target_type, row["target_props"]),
            "schema": schema_key(target_type, row["target_label"], row["target_props"]),
        }
        edges.append({
            "source": source_uid,
            "target": target_uid,
            "relation": str(row["relation"]),
        })
    width = 1900 if len(nodes) > 40 else 1500
    height = 1250 if len(nodes) > 40 else 900
    returned = returned_count if returned_count is not None else len(rows)
    legend_keys = sorted({node["schema"] for node in nodes.values()})
    coords, group_bounds = grouped_positions(nodes, width, height)
    marker_defs = []
    for relation in sorted({str(row["relation"]) for row in rows}):
        marker_id = "arrow_" + hashlib.sha1(relation.encode()).hexdigest()[:8]
        color = RELATION_COLORS.get(relation, "#6B7280")
        marker_defs.append(
            f'<marker id="{marker_id}" markerWidth="9" markerHeight="9" refX="8" refY="3.5" orient="auto">'
            f'<path d="M0,0 L0,7 L9,3.5 z" fill="{color}"/></marker>'
        )
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#FAFBFC"/>',
        f'<defs>{"".join(marker_defs)}</defs>',
        f'<text x="40" y="48" font-family="sans-serif" font-size="30" font-weight="700" fill="#102A43">{html.escape(title)}</text>',
        f'<text x="40" y="80" font-family="sans-serif" font-size="16" fill="#52606D">Live Neo4j result | total {total_count} | query returned {returned} paths | displayed {len(rows)}</text>',
        '<text x="40" y="108" font-family="sans-serif" font-size="14" fill="#52606D">Node color = induced schema · Arrow color = relationship type</text>',
    ]
    legend_x, legend_y = 40, 140
    for key in legend_keys:
        color = SCHEMA_COLORS.get(key, "#E5E7EB")
        item_width = max(150, min(265, 50 + len(key) * 9))
        if legend_x + item_width > width - 40:
            legend_x = 40
            legend_y += 30
        parts.append(f'<rect x="{legend_x}" y="{legend_y-15}" width="20" height="20" rx="4" fill="{color}" stroke="#607080"/>')
        parts.append(f'<text x="{legend_x+28}" y="{legend_y}" font-family="sans-serif" font-size="14" fill="#334E68">{html.escape(key)}</text>')
        legend_x += item_width
    for key, (cx, cy, radius) in group_bounds.items():
        color = SCHEMA_COLORS.get(key, "#E5E7EB")
        parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius:.1f}" fill="{color}" fill-opacity="0.09" stroke="{color}" stroke-width="2" stroke-dasharray="8 7"/>')
        parts.append(f'<text x="{cx:.1f}" y="{cy-radius+24:.1f}" text-anchor="middle" font-family="sans-serif" font-size="16" font-weight="700" fill="#334E68">{html.escape(key)}</text>')
    node_radius = 37 if len(nodes) <= 24 else 27 if len(nodes) <= 60 else 21
    for edge in edges:
        relation = edge["relation"]
        relation_color = RELATION_COLORS.get(relation, "#6B7280")
        marker_id = "arrow_" + hashlib.sha1(relation.encode()).hexdigest()[:8]
        x1, y1 = coords[edge["source"]]
        x2, y2 = coords[edge["target"]]
        dx, dy = x2 - x1, y2 - y1
        distance = math.hypot(dx, dy) or 1.0
        start_x = x1 + dx / distance * (node_radius + 2)
        start_y = y1 + dy / distance * (node_radius + 2)
        end_x = x2 - dx / distance * (node_radius + 8)
        end_y = y2 - dy / distance * (node_radius + 8)
        parts.append(f'<line x1="{start_x:.1f}" y1="{start_y:.1f}" x2="{end_x:.1f}" y2="{end_y:.1f}" stroke="{relation_color}" stroke-width="2.1" stroke-opacity="0.72" marker-end="url(#{marker_id})"/>')
        if len(edges) <= 20:
            parts.append(f'<text x="{(start_x+end_x)/2:.1f}" y="{(start_y+end_y)/2-5:.1f}" text-anchor="middle" font-family="sans-serif" font-size="10" font-weight="700" fill="{relation_color}">{html.escape(relation)}</text>')
    font_size = 9 if len(nodes) <= 24 else 7 if len(nodes) <= 60 else 6
    label_limit = 18 if len(nodes) <= 24 else 12
    for uid in sorted(nodes):
        node = nodes[uid]
        x, y = coords[uid]
        color = SCHEMA_COLORS.get(node["schema"], "#E5E7EB")
        label = clean_label(node["label"], label_limit)
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{node_radius}" fill="{color}" stroke="#425466" stroke-width="1.7"/>')
        parts.append(f'<text x="{x:.1f}" y="{y+3:.1f}" text-anchor="middle" font-family="sans-serif" font-size="{font_size}" font-weight="700" fill="#102A43">{html.escape(label)}</text>')
        if len(nodes) <= 30:
            parts.append(f'<text x="{x:.1f}" y="{y+node_radius+14:.1f}" text-anchor="middle" font-family="sans-serif" font-size="8" fill="#52606D">{html.escape(node["schema"])}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def render_svg(path: Path, title: str, total_count: int, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_svg(title, total_count, rows), encoding="utf-8")


def render_collage(path: Path, items: list[dict[str, Any]]) -> None:
    width, height = 3000, 1920
    panels = [
        (30, 40, 960, 570),
        (1020, 40, 960, 570),
        (2010, 40, 960, 570),
        (520, 650, 960, 570),
        (1510, 650, 960, 570),
    ]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#F5F7FA"/>',
        '<text x="70" y="1320" font-family="sans-serif" font-size="54" font-weight="700" fill="#102A43">Five representative Cypher results executed in Neo4j</text>',
    ]
    for item, (x, y, panel_width, panel_height) in zip(items, panels):
        encoded = base64.b64encode(item["svg_text"].encode("utf-8")).decode("ascii")
        parts.append(f'<rect x="{x}" y="{y}" width="{panel_width}" height="{panel_height}" rx="10" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="3"/>')
        parts.append(f'<image x="{x+5}" y="{y+5}" width="{panel_width-10}" height="{panel_height-10}" preserveAspectRatio="xMidYMid meet" href="data:image/svg+xml;base64,{encoded}"/>')
    summary_y = 1390
    for index, item in enumerate(items):
        parts.append(
            f'<text x="90" y="{summary_y + index*82}" font-family="sans-serif" font-size="34" fill="#334E68">'
            f'{index+1}. {html.escape(item["title"])}: total {item["total_count"]}, returned {item["returned_path_count"]}</text>'
        )
    parts.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts), encoding="utf-8")


def main() -> int:
    project = Path(__file__).resolve().parents[1]
    root = project / "experiments" / EXPERIMENT_ID
    output = root / "visualization" / "live_query_results"
    uri = os.environ.get("NEO4J_URI", "bolt://127.0.0.1:7689")
    driver = GraphDatabase.driver(uri, auth=None)
    manifest = []
    collage_items = []
    with driver.session(database="neo4j") as session:
        for spec in QUERY_SPECS:
            total_count = int(session.run(spec["total_query"]).single()["count"])
            rows = [dict(row) for row in session.run(spec["graph_query"])]
            path = output / f'{spec["key"]}.svg'
            render_svg(path, spec["title"], total_count, rows)
            item = {
                "key": spec["key"],
                "title": spec["title"],
                "relation": spec["relation"],
                "total_count": total_count,
                "returned_path_count": len(rows),
                "displayed_path_count": len(rows),
                "relationship_counts": dict(Counter(str(row["relation"]) for row in rows)),
                "schema_keys": sorted({
                    schema_key(str(row[f"{side}_type"]), row[f"{side}_label"], row[f"{side}_props"])
                    for row in rows
                    for side in ("source", "target")
                }),
                "file": path.name,
                "sha256": file_sha(path),
                "query_executed_against": uri,
                "neo4j_database": "neo4j",
            }
            manifest.append(item)
            collage_items.append({
                **item,
                "svg_text": build_svg(spec["title"], total_count, rows[:8], returned_count=len(rows)),
            })
    driver.close()
    collage = output / "00_representative_5_live_results.svg"
    render_collage(collage, collage_items)
    result = {
        "query_results": manifest,
        "collage_file": collage.name,
        "collage_sha256": file_sha(collage),
        "all_nonempty": all(item["returned_path_count"] > 0 for item in manifest),
        "expected_totals": [8, 16, 8, 201, 445],
        "actual_totals": [item["total_count"] for item in manifest],
        "pass": [item["total_count"] for item in manifest] == [8, 16, 8, 201, 445],
    }
    (output / "manifest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["pass"] and result["all_nonempty"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
