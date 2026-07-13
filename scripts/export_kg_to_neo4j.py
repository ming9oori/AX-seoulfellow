#!/usr/bin/env python3
"""Export the built AX/CAPE KG artifacts to Neo4j LOAD CSV files."""

import argparse
import base64
import csv
import json
import re
from collections import defaultdict
from pathlib import Path


DEFAULT_OUTPUTS_DIR = Path("outputs")
DEFAULT_OUT_DIR = Path("outputs/11_neo4j_import")


NODE_FILES = [
    "01_layer1/layer1_ncs_nodes.jsonl",
    "01_layer1/layer1_pcf_nodes.jsonl",
    "07_layer2_graph/layer2_nodes.jsonl",
]

EDGE_FILES = [
    "01_layer1/layer1_ncs_edges.jsonl",
    "01_layer1/layer1_pcf_edges.jsonl",
    "01_layer1/layer1_pcf_metric_edges.jsonl",
    "07_layer2_graph/layer2_edges.jsonl",
]

MAPPING_FILES = [
    "08_mapping/l2_ncs_mapping_candidates.jsonl",
    "08_mapping/l2_pcf_mapping_candidates.jsonl",
]

EVIDENCE_NODE_FILE = "13_evidence_graph/evidence_anchor_nodes.jsonl"
EVIDENCE_EDGE_FILE = "13_evidence_graph/evidenced_by_edges.jsonl"


NODE_FIELDS = [
    "node_id",
    "label",
    "type",
    "layer",
    "definition",
    "label_ko",
    "label_en",
    "code",
    "hid",
    "parent_hid",
    "source",
    "review_status",
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
    "aliases_json",
    "evidence_anchor_ids_json",
    "raw_json",
]

REL_FIELDS = [
    "rel_id",
    "source_id",
    "target_id",
    "rel_type",
    "predicate",
    "layer",
    "confidence",
    "mapping_type",
    "rank",
    "score",
    "review_status",
    "evidence_anchor_ids_json",
    "source_triple_ids_json",
    "reason",
    "raw_json",
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


def write_csv(path, rows, fieldnames):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def compact_json(value):
    return json.dumps(value if value is not None else None, ensure_ascii=False, separators=(",", ":"))


def neo4j_safe_json(value):
    """Keep JSON payloads out of Neo4j CSV quote parsing edge cases.

    Neo4j Desktop's LOAD CSV parser can reject JSON strings that contain
    backslash-escaped quotes inside a quoted CSV field. Base64 keeps the carrier
    columns lossless while leaving graph-facing scalar fields readable.
    """
    raw = compact_json(value)
    encoded = base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii")
    return "base64:" + encoded


def as_text(value):
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    return compact_json(value)


def rel_type(value):
    value = str(value or "RELATED_TO")
    value = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").upper()
    if not value:
        return "RELATED_TO"
    if value[0].isdigit():
        value = "REL_" + value
    return value


def canonical_mapping_predicate(row):
    mapping_type = str(row.get("mapping_type") or "").strip()
    target_type = str(row.get("target_type") or "").strip()
    normalized = re.sub(r"[^A-Za-z0-9]+", "", mapping_type).lower()
    if normalized in {"requirescapability", "candidaterequirescapability"} or target_type == "NCSCompetencyUnit":
        return "REQUIRES_CAPABILITY"
    if normalized in {"processcontext", "candidateprocesscontext"} or target_type == "PCFElement":
        return "PROCESS_CONTEXT"
    if normalized in {"candidatealignswith", "alignswith"}:
        return "CANDIDATE_ALIGNS_WITH"
    return row.get("predicate") or mapping_type or "CANDIDATE_ALIGNS_WITH"


def node_row(row):
    return {
        "node_id": row.get("node_id", ""),
        "label": row.get("label", ""),
        "type": row.get("type", ""),
        "layer": row.get("layer", ""),
        "definition": row.get("definition", ""),
        "label_ko": row.get("label_ko", ""),
        "label_en": row.get("label_en", ""),
        "code": row.get("code", ""),
        "hid": row.get("hid", ""),
        "parent_hid": row.get("parent_hid", ""),
        "source": row.get("source", ""),
        "review_status": row.get("review_status", ""),
        "evidence_anchor_id": row.get("evidence_anchor_id", ""),
        "sentence_id": row.get("sentence_id", ""),
        "chunk_id": row.get("chunk_id", ""),
        "page": as_text(row.get("page")),
        "zone": row.get("zone", ""),
        "span_start": as_text(row.get("span_start")),
        "span_end": as_text(row.get("span_end")),
        "anchor_exact": as_text(row.get("anchor_exact")),
        "text_included": as_text(row.get("text_included")),
        "text_char_count": as_text(row.get("text_char_count")),
        "text_sha256": row.get("text_sha256", ""),
        "aliases_json": neo4j_safe_json(row.get("aliases", [])),
        "evidence_anchor_ids_json": neo4j_safe_json(row.get("evidence_anchor_ids", [])),
        "raw_json": neo4j_safe_json(row),
    }


def evidence_anchor_node_row(row):
    enriched = dict(row)
    enriched.setdefault("type", "EvidenceAnchor")
    enriched.setdefault("layer", "EvidenceProjection")
    enriched.setdefault("source", "evidence_anchor_catalog")
    return node_row(enriched)


def kg_edge_assertion_node_row(row):
    source_id = row.get("source_id", "")
    return node_row(
        {
            "node_id": source_id,
            "label": row.get("source_label") or source_id,
            "type": "KGEdgeAssertion",
            "layer": "EvidenceProjection",
            "definition": "Reified KG edge assertion used as an EVIDENCED_BY source.",
            "source": "evidence_graph_projection",
            "review_status": row.get("review_status", ""),
            "raw_projection_row": row,
        }
    )


def edge_row(row):
    predicate = row.get("predicate") or row.get("mapping_type") or "RELATED_TO"
    return {
        "rel_id": row.get("edge_id") or row.get("mapping_id") or "",
        "source_id": row.get("source_id", ""),
        "target_id": row.get("target_id", ""),
        "rel_type": rel_type(predicate),
        "predicate": predicate,
        "layer": row.get("layer", ""),
        "confidence": as_text(row.get("confidence")),
        "mapping_type": row.get("mapping_type", ""),
        "rank": as_text(row.get("rank")),
        "score": as_text(row.get("score")),
        "review_status": row.get("review_status", ""),
        "evidence_anchor_ids_json": neo4j_safe_json(row.get("evidence_anchor_ids", [])),
        "source_triple_ids_json": neo4j_safe_json(row.get("source_triple_ids", [])),
        "reason": row.get("reason", ""),
        "raw_json": neo4j_safe_json(row),
    }


def mapping_row(row):
    enriched = dict(row)
    enriched["layer"] = "Layer2ToLayer1Mapping"
    enriched["predicate"] = canonical_mapping_predicate(enriched)
    return edge_row(enriched)


def evidence_edge_row(row):
    enriched = dict(row)
    enriched["edge_id"] = row.get("evidence_edge_id", "")
    enriched["predicate"] = "EVIDENCED_BY"
    enriched["layer"] = row.get("layer") or "EvidenceProjection"
    enriched["mapping_type"] = row.get("source_kind", "")
    enriched["source_triple_ids"] = []
    return edge_row(enriched)


def load_nodes(outputs_dir):
    nodes = {}
    for rel_path in NODE_FILES:
        for row in read_jsonl(outputs_dir / rel_path):
            node_id = row.get("node_id")
            if node_id:
                nodes[node_id] = node_row(row)
    for row in read_jsonl(outputs_dir / EVIDENCE_NODE_FILE):
        node_id = row.get("node_id")
        if node_id:
            nodes[node_id] = evidence_anchor_node_row(row)
    for row in read_jsonl(outputs_dir / EVIDENCE_EDGE_FILE):
        if row.get("source_kind") == "KGEdge" and row.get("source_id"):
            nodes.setdefault(row["source_id"], kg_edge_assertion_node_row(row))
    return nodes


def load_relationships(outputs_dir):
    relationships = []
    for rel_path in EDGE_FILES:
        for row in read_jsonl(outputs_dir / rel_path):
            relationships.append(edge_row(row))
    for rel_path in MAPPING_FILES:
        for row in read_jsonl(outputs_dir / rel_path):
            relationships.append(mapping_row(row))
    for row in read_jsonl(outputs_dir / EVIDENCE_EDGE_FILE):
        relationships.append(evidence_edge_row(row))
    return relationships


def csv_uri(csv_name, csv_base_url=""):
    if csv_base_url:
        return f"{csv_base_url.rstrip('/')}/{csv_name}"
    return f"file:///{csv_name}"


def render_cypher(rel_types, flat_relationships=False, csv_base_url=""):
    lines = [
        "// Generated by scripts/export_kg_to_neo4j.py",
        "// Copy CSV files into Neo4j's import directory for file:/// imports, or serve them over HTTP for URL imports.",
        "",
        "CREATE CONSTRAINT kg_node_id IF NOT EXISTS FOR (n:KGNode) REQUIRE n.node_id IS UNIQUE;",
        "",
        f"LOAD CSV WITH HEADERS FROM '{csv_uri('nodes.csv', csv_base_url)}' AS row",
        "MERGE (n:KGNode {node_id: row.node_id})",
        "SET n.label = row.label,",
        "    n.type = row.type,",
        "    n.layer = row.layer,",
        "    n.definition = row.definition,",
        "    n.label_ko = row.label_ko,",
        "    n.label_en = row.label_en,",
        "    n.code = row.code,",
        "    n.hid = row.hid,",
        "    n.parent_hid = row.parent_hid,",
        "    n.source = row.source,",
        "    n.review_status = row.review_status,",
        "    n.evidence_anchor_id = row.evidence_anchor_id,",
        "    n.sentence_id = row.sentence_id,",
        "    n.chunk_id = row.chunk_id,",
        "    n.page = CASE row.page WHEN '' THEN null ELSE toInteger(row.page) END,",
        "    n.zone = row.zone,",
        "    n.span_start = CASE row.span_start WHEN '' THEN null ELSE toInteger(row.span_start) END,",
        "    n.span_end = CASE row.span_end WHEN '' THEN null ELSE toInteger(row.span_end) END,",
        "    n.anchor_exact = row.anchor_exact,",
        "    n.text_included = row.text_included,",
        "    n.text_char_count = CASE row.text_char_count WHEN '' THEN null ELSE toInteger(row.text_char_count) END,",
        "    n.text_sha256 = row.text_sha256,",
        "    n.aliases_json = row.aliases_json,",
        "    n.evidence_anchor_ids_json = row.evidence_anchor_ids_json,",
        "    n.raw_json = row.raw_json",
        "FOREACH (_ IN CASE WHEN row.layer = 'Layer1NCS' THEN [1] ELSE [] END | SET n:Layer1NCS)",
        "FOREACH (_ IN CASE WHEN row.layer = 'Layer1PCF' THEN [1] ELSE [] END | SET n:Layer1PCF)",
        "FOREACH (_ IN CASE WHEN row.layer = 'Layer2' THEN [1] ELSE [] END | SET n:Layer2)",
        "FOREACH (_ IN CASE WHEN row.layer = 'EvidenceProjection' THEN [1] ELSE [] END | SET n:EvidenceProjection)",
        "FOREACH (_ IN CASE WHEN row.type = 'EvidenceAnchor' THEN [1] ELSE [] END | SET n:EvidenceAnchor)",
        "FOREACH (_ IN CASE WHEN row.type = 'KGEdgeAssertion' THEN [1] ELSE [] END | SET n:KGEdgeAssertion);",
        "",
    ]
    for rel in sorted(rel_types):
        csv_name = f"{rel}.csv" if flat_relationships else f"relationships/{rel}.csv"
        lines.extend(
            [
                f"LOAD CSV WITH HEADERS FROM '{csv_uri(csv_name, csv_base_url)}' AS row",
                "MATCH (s:KGNode {node_id: row.source_id})",
                "MATCH (t:KGNode {node_id: row.target_id})",
                f"MERGE (s)-[r:{rel} {{rel_id: row.rel_id}}]->(t)",
                "SET r.predicate = row.predicate,",
                "    r.layer = row.layer,",
                "    r.confidence = CASE row.confidence WHEN '' THEN null ELSE toFloat(row.confidence) END,",
                "    r.mapping_type = row.mapping_type,",
                "    r.rank = CASE row.rank WHEN '' THEN null ELSE toInteger(row.rank) END,",
                "    r.score = CASE row.score WHEN '' THEN null ELSE toFloat(row.score) END,",
                "    r.review_status = row.review_status,",
                "    r.evidence_anchor_ids_json = row.evidence_anchor_ids_json,",
                "    r.source_triple_ids_json = row.source_triple_ids_json,",
                "    r.reason = row.reason,",
                "    r.raw_json = row.raw_json;",
                "",
            ]
        )
    lines.extend(
        [
            "CREATE INDEX kg_node_layer IF NOT EXISTS FOR (n:KGNode) ON (n.layer);",
            "CREATE INDEX kg_node_type IF NOT EXISTS FOR (n:KGNode) ON (n.type);",
            "CREATE FULLTEXT INDEX kg_node_label_text IF NOT EXISTS FOR (n:KGNode) ON EACH [n.label, n.label_ko, n.label_en, n.definition];",
            "",
            "MATCH (n:KGNode) RETURN n.layer AS layer, n.type AS type, count(*) AS nodes ORDER BY layer, type;",
        ]
    )
    return "\n".join(lines) + "\n"


def render_readme(payload):
    relationship_file_note = "`*.csv` relationship files in this directory" if payload.get("flat_relationships") else "`relationships/*.csv`"
    copy_note = (
        "Copy every CSV in this directory into Neo4j's import directory."
        if payload.get("flat_relationships")
        else "Copy this directory into Neo4j's import directory, or copy `nodes.csv` and the `relationships/` folder there."
    )
    return f"""# Neo4j Import Package

Generated: {payload["generated_at_utc"]}

## Counts

- Nodes: {payload["node_count"]}
- Relationships: {payload["relationship_count"]}
- Relationship types: {len(payload["relationship_types"])}
- Missing relationship endpoints: {payload["missing_endpoint_count"]}
- EvidenceAnchor nodes: {payload.get("evidence_anchor_node_count", 0)}
- KGEdgeAssertion nodes: {payload.get("kg_edge_assertion_node_count", 0)}
- EVIDENCED_BY relationships: {payload["relationship_types"].get("EVIDENCED_BY", 0)}

## Files

- `nodes.csv`
- {relationship_file_note}
- `neo4j_import.cypher`
- `manifest.json`

JSON carrier columns such as `raw_json`, `aliases_json`,
`evidence_anchor_ids_json`, and `source_triple_ids_json` are stored as
`base64:<payload>` strings. This avoids Neo4j Desktop CSV parser failures on
JSON escape sequences while preserving the original payload losslessly.

## Import

{copy_note} Then run:

```bash
cypher-shell -u neo4j -p '<password>' -f neo4j_import.cypher
```

For Neo4j Desktop, open the DB's import folder and place these files there.

If Neo4j blocks `file:///` imports with `dbms.security.allow_csv_import_from_file_urls is false`,
serve this repository over HTTP and use `neo4j_import_http_8765.cypher` instead.

### Neo4j Browser HTTP Import

Use this path when Neo4j Browser reports:

```text
Cannot load from URL 'file:///nodes.csv': configuration property 'dbms.security.allow_csv_import_from_file_urls' is false
```

First, keep the repository HTTP server running:

```bash
bash scripts/serve_kg_viewer.sh
```

Then check CSV visibility in Neo4j Browser:

```cypher
LOAD CSV WITH HEADERS FROM 'http://localhost:8765/outputs/11_neo4j_import_flat/nodes.csv' AS row
RETURN row.node_id, row.label, row.type
LIMIT 5;
```

If the query returns rows, paste and run `neo4j_import_http_8765.cypher` in Neo4j Browser.
If `localhost` does not resolve from the Neo4j database process, try
`neo4j_import_http_127001_8765.cypher`.

## Example Queries

```cypher
MATCH (n:KGNode)
RETURN n.layer, n.type, count(*) AS c
ORDER BY n.layer, n.type;

MATCH (t:Layer2 {{type: 'DomainTask'}})-[r]->(m:Layer1NCS)
RETURN t.label, type(r), m.label, r.rank, r.score
ORDER BY t.label, r.rank
LIMIT 30;

MATCH p = (:Layer2 {{node_id: 'L2_TASK_OPPORTUNITY_ASSESSMENT'}})-[*1..2]->()
RETURN p
LIMIT 25;

MATCH p = (:Layer2)-[:EVIDENCED_BY]->(:EvidenceAnchor)
RETURN p
LIMIT 25;

MATCH p = (:KGEdgeAssertion)-[:EVIDENCED_BY]->(:EvidenceAnchor)
RETURN p
LIMIT 25;
```
"""


def run(args):
    outputs_dir = Path(args.outputs_dir)
    out_dir = Path(args.out_dir)
    rel_dir = out_dir if args.flat_relationships else out_dir / "relationships"
    out_dir.mkdir(parents=True, exist_ok=True)
    rel_dir.mkdir(parents=True, exist_ok=True)

    nodes = load_nodes(outputs_dir)
    relationships = load_relationships(outputs_dir)
    node_ids = set(nodes)
    missing = [r for r in relationships if r["source_id"] not in node_ids or r["target_id"] not in node_ids]
    evidence_anchor_node_count = sum(1 for row in nodes.values() if row.get("type") == "EvidenceAnchor")
    kg_edge_assertion_node_count = sum(1 for row in nodes.values() if row.get("type") == "KGEdgeAssertion")

    by_type = defaultdict(list)
    for row in relationships:
        by_type[row["rel_type"]].append(row)

    write_csv(out_dir / "nodes.csv", sorted(nodes.values(), key=lambda r: r["node_id"]), NODE_FIELDS)
    for rel, rows in sorted(by_type.items()):
        write_csv(rel_dir / f"{rel}.csv", sorted(rows, key=lambda r: (r["source_id"], r["target_id"], r["rel_id"])), REL_FIELDS)

    payload = {
        "generated_at_utc": __import__("datetime").datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "outputs_dir": str(outputs_dir),
        "out_dir": str(out_dir),
        "node_count": len(nodes),
        "relationship_count": len(relationships),
        "relationship_types": dict(sorted((k, len(v)) for k, v in by_type.items())),
        "evidence_anchor_node_count": evidence_anchor_node_count,
        "kg_edge_assertion_node_count": kg_edge_assertion_node_count,
        "flat_relationships": bool(args.flat_relationships),
        "missing_endpoint_count": len(missing),
        "missing_endpoint_sample": missing[:20],
        "source_files": {
            "nodes": NODE_FILES,
            "edges": EDGE_FILES,
            "mappings": MAPPING_FILES,
            "evidence_nodes": EVIDENCE_NODE_FILE,
            "evidence_edges": EVIDENCE_EDGE_FILE,
        },
    }
    (out_dir / "manifest.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "neo4j_import.cypher").write_text(
        render_cypher(by_type.keys(), flat_relationships=args.flat_relationships),
        encoding="utf-8",
    )
    if args.csv_base_url:
        (out_dir / args.http_cypher_name).write_text(
            render_cypher(
                by_type.keys(),
                flat_relationships=args.flat_relationships,
                csv_base_url=args.csv_base_url,
            ),
            encoding="utf-8",
        )
    (out_dir / "README.md").write_text(render_readme(payload), encoding="utf-8")

    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--outputs-dir", default=str(DEFAULT_OUTPUTS_DIR))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument(
        "--flat-relationships",
        action="store_true",
        help="Write relationship CSV files directly into out-dir instead of out-dir/relationships.",
    )
    parser.add_argument(
        "--csv-base-url",
        default="",
        help="Also write an HTTP LOAD CSV Cypher file using this base URL for CSV files.",
    )
    parser.add_argument(
        "--http-cypher-name",
        default="neo4j_import_http_8765.cypher",
        help="Output filename for the optional HTTP LOAD CSV Cypher file.",
    )
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
