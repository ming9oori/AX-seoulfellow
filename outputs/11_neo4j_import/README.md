# Neo4j Import Package

Generated: 2026-06-29T18:56:37Z

## Counts

- Nodes: 11028
- Relationships: 14455
- Relationship types: 18
- Missing relationship endpoints: 0
- EvidenceAnchor nodes: 451
- KGEdgeAssertion nodes: 947
- EVIDENCED_BY relationships: 3915

## Files

- `nodes.csv`
- `relationships/*.csv`
- `neo4j_import.cypher`
- `manifest.json`

JSON carrier columns such as `raw_json`, `aliases_json`,
`evidence_anchor_ids_json`, and `source_triple_ids_json` are stored as
`base64:<payload>` strings. This avoids Neo4j Desktop CSV parser failures on
JSON escape sequences while preserving the original payload losslessly.

## Import

Copy this directory into Neo4j's import directory, or copy `nodes.csv` and the `relationships/` folder there. Then run:

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

MATCH (t:Layer2 {type: 'DomainTask'})-[r]->(m:Layer1NCS)
RETURN t.label, type(r), m.label, r.rank, r.score
ORDER BY t.label, r.rank
LIMIT 30;

MATCH p = (:Layer2 {node_id: 'L2_TASK_OPPORTUNITY_ASSESSMENT'})-[*1..2]->()
RETURN p
LIMIT 25;

MATCH p = (:Layer2)-[:EVIDENCED_BY]->(:EvidenceAnchor)
RETURN p
LIMIT 25;

MATCH p = (:KGEdgeAssertion)-[:EVIDENCED_BY]->(:EvidenceAnchor)
RETURN p
LIMIT 25;
```
