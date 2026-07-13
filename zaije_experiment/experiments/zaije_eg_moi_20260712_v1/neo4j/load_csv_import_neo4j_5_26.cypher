/*
EG-MOI Neo4j 5.26+ UI importer

Run each statement separately in Neo4j Query.

Neo4j Desktop:
1. Copy nodes.csv and edges.csv into the instance import directory.
2. Keep the database running.
3. Use file:///nodes.csv and file:///edges.csv as written below.

Neo4j Aura:
- file:/// URLs cannot read files from your computer.
- Replace both file URLs with HTTPS URLs reachable by Aura, or use Data Importer.

The import keeps evidence_anchor_ids and props_json as JSON strings so that it
does not require APOC.
*/

// 1. Neo4j 5.26 or later is required for dynamic labels and relationship types.
CALL dbms.components()
YIELD versions
RETURN versions[0] AS neo4j_version;

// 2. Optional cleanup: uncomment only when replacing the existing EG-MOI graph.
// MATCH (n:EGEntity {system_id: 'EG-MOI-V1'})
// DETACH DELETE n;

// 3. Create the UID uniqueness constraint before MERGE.
CREATE CONSTRAINT egentity_uid_unique IF NOT EXISTS
FOR (n:EGEntity)
REQUIRE n.uid IS UNIQUE;

// 4. Check that Neo4j can read the node CSV. Expected: 11053.
LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
RETURN count(row) AS node_csv_rows;

// 5. Import nodes and dynamically apply labels such as SchemaClass or Assertion.
LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
WITH row
WHERE row['uid:ID'] IS NOT NULL
MERGE (n:EGEntity {uid: row['uid:ID']})
SET n:$(split(row[':LABEL'], ';'))
SET n.id = row.id,
    n.system_id = row.system_id,
    n.type = row.type,
    n.label = row.label,
    n.status = CASE
        WHEN row.status IS NULL OR trim(row.status) = '' THEN null
        ELSE row.status
    END,
    n.evidence_anchor_ids = row.evidence_anchor_ids,
    n.props_json = row.props_json
RETURN count(*) AS processed_node_rows;

// 6. Verify nodes. Expected: 11053 EG-MOI nodes.
MATCH (n:EGEntity {system_id: 'EG-MOI-V1'})
RETURN count(n) AS nodes;

MATCH (n:EGEntity {system_id: 'EG-MOI-V1'})
UNWIND labels(n) AS label
RETURN label, count(*) AS count
ORDER BY count DESC, label;

// 7. Check relationship endpoints before importing. Expected: 0 missing rows.
LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row
OPTIONAL MATCH (source:EGEntity {uid: row[':START_ID']})
OPTIONAL MATCH (target:EGEntity {uid: row[':END_ID']})
WITH source, target
WHERE source IS NULL OR target IS NULL
RETURN count(*) AS missing_endpoint_rows;

// 8. Import relationships using each CSV row's dynamic :TYPE value.
LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row
MATCH (source:EGEntity {uid: row[':START_ID']})
MATCH (target:EGEntity {uid: row[':END_ID']})
MERGE (source)-[r:$(row[':TYPE']) {uid: row.uid}]->(target)
SET r.system_id = row.system_id,
    r.type = row.type,
    r.status = CASE
        WHEN row.status IS NULL OR trim(row.status) = '' THEN null
        ELSE row.status
    END,
    r.evidence_anchor_ids = row.evidence_anchor_ids,
    r.props_json = row.props_json
RETURN count(*) AS processed_relationship_rows;

// 9. Verify relationships. Expected: 19502 EG-MOI relationships.
MATCH (:EGEntity {system_id: 'EG-MOI-V1'})-[r]->(:EGEntity {system_id: 'EG-MOI-V1'})
WHERE r.system_id = 'EG-MOI-V1'
RETURN count(r) AS relationships;

MATCH (:EGEntity {system_id: 'EG-MOI-V1'})-[r]->(:EGEntity {system_id: 'EG-MOI-V1'})
WHERE r.system_id = 'EG-MOI-V1'
RETURN type(r) AS relationship_type, count(*) AS count
ORDER BY count DESC, relationship_type;

// 10. Final structural checks. Expected: 8, 16, 8, 201, 445.
MATCH (:SchemaClass)-[r:SUBCLASS_OF]->(:MetaClass)
RETURN count(r) AS induced_schema;

MATCH (:ConceptCluster)-[r]->(:ConceptCluster)
WHERE type(r) IN ['HAS_INPUT', 'PRODUCES_OUTPUT']
RETURN count(r) AS input_and_output;

MATCH (:ConceptCluster)-[r:PERFORMED_BY]->(:ConceptCluster)
RETURN count(r) AS performer;

MATCH (:ConceptCluster)-[r:PRECEDES]->(:ConceptCluster)
RETURN count(r) AS sequence;

MATCH (:Assertion)-[r:DERIVED_FROM]->(:EvidenceUnit)
RETURN count(r) AS assertion_evidence;
