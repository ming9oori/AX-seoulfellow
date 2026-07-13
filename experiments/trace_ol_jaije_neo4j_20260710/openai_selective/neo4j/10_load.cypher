// Mount this directory as Neo4j /import before execution.
LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
MERGE (n:Entity {id: row.id})
SET n.canonical_name = row.canonical_name,
    n.run_id = row.run_id,
    n.status = row.status,
    n.predicate = row.predicate,
    n.claim_type = row.claim_type,
    n.confidence = CASE row.confidence WHEN '' THEN null ELSE toFloat(row.confidence) END,
    n.excel_row = CASE row.excel_row WHEN '' THEN null ELSE toInteger(row.excel_row) END,
    n.page = CASE row.page WHEN '' THEN null ELSE toInteger(row.page) END,
    n.context_status = row.context_status,
    n.raw_json = row.raw_json
FOREACH (_ IN CASE WHEN 'Artifact' IN split(row.labels, ';') THEN [1] ELSE [] END | SET n:Artifact)
FOREACH (_ IN CASE WHEN 'Cell' IN split(row.labels, ';') THEN [1] ELSE [] END | SET n:Cell)
FOREACH (_ IN CASE WHEN 'Chapter' IN split(row.labels, ';') THEN [1] ELSE [] END | SET n:Chapter)
FOREACH (_ IN CASE WHEN 'Claim' IN split(row.labels, ';') THEN [1] ELSE [] END | SET n:Claim)
FOREACH (_ IN CASE WHEN 'Column' IN split(row.labels, ';') THEN [1] ELSE [] END | SET n:Column)
FOREACH (_ IN CASE WHEN 'Competitor' IN split(row.labels, ';') THEN [1] ELSE [] END | SET n:Competitor)
FOREACH (_ IN CASE WHEN 'Concept' IN split(row.labels, ';') THEN [1] ELSE [] END | SET n:Concept)
FOREACH (_ IN CASE WHEN 'Constraint' IN split(row.labels, ';') THEN [1] ELSE [] END | SET n:Constraint)
FOREACH (_ IN CASE WHEN 'Criterion' IN split(row.labels, ';') THEN [1] ELSE [] END | SET n:Criterion)
FOREACH (_ IN CASE WHEN 'Decision' IN split(row.labels, ';') THEN [1] ELSE [] END | SET n:Decision)
FOREACH (_ IN CASE WHEN 'Document' IN split(row.labels, ';') THEN [1] ELSE [] END | SET n:Document)
FOREACH (_ IN CASE WHEN 'Entity' IN split(row.labels, ';') THEN [1] ELSE [] END | SET n:Entity)
FOREACH (_ IN CASE WHEN 'EvidenceSpan' IN split(row.labels, ';') THEN [1] ELSE [] END | SET n:EvidenceSpan)
FOREACH (_ IN CASE WHEN 'Formula' IN split(row.labels, ';') THEN [1] ELSE [] END | SET n:Formula)
FOREACH (_ IN CASE WHEN 'InformationObject' IN split(row.labels, ';') THEN [1] ELSE [] END | SET n:InformationObject)
FOREACH (_ IN CASE WHEN 'LabelingFunction' IN split(row.labels, ';') THEN [1] ELSE [] END | SET n:LabelingFunction)
FOREACH (_ IN CASE WHEN 'LexicalEntry' IN split(row.labels, ';') THEN [1] ELSE [] END | SET n:LexicalEntry)
FOREACH (_ IN CASE WHEN 'Mitigation' IN split(row.labels, ';') THEN [1] ELSE [] END | SET n:Mitigation)
FOREACH (_ IN CASE WHEN 'ModelCall' IN split(row.labels, ';') THEN [1] ELSE [] END | SET n:ModelCall)
FOREACH (_ IN CASE WHEN 'Process' IN split(row.labels, ';') THEN [1] ELSE [] END | SET n:Process)
FOREACH (_ IN CASE WHEN 'Risk' IN split(row.labels, ';') THEN [1] ELSE [] END | SET n:Risk)
FOREACH (_ IN CASE WHEN 'Rule' IN split(row.labels, ';') THEN [1] ELSE [] END | SET n:Rule)
FOREACH (_ IN CASE WHEN 'RuleDecision' IN split(row.labels, ';') THEN [1] ELSE [] END | SET n:RuleDecision)
FOREACH (_ IN CASE WHEN 'Run' IN split(row.labels, ';') THEN [1] ELSE [] END | SET n:Run)
FOREACH (_ IN CASE WHEN 'Section' IN split(row.labels, ';') THEN [1] ELSE [] END | SET n:Section)
FOREACH (_ IN CASE WHEN 'SourceBlock' IN split(row.labels, ';') THEN [1] ELSE [] END | SET n:SourceBlock)
FOREACH (_ IN CASE WHEN 'Stage' IN split(row.labels, ';') THEN [1] ELSE [] END | SET n:Stage)
FOREACH (_ IN CASE WHEN 'Table' IN split(row.labels, ';') THEN [1] ELSE [] END | SET n:Table)
FOREACH (_ IN CASE WHEN 'TableRow' IN split(row.labels, ';') THEN [1] ELSE [] END | SET n:TableRow)
FOREACH (_ IN CASE WHEN 'Task' IN split(row.labels, ';') THEN [1] ELSE [] END | SET n:Task)
FOREACH (_ IN CASE WHEN 'Variable' IN split(row.labels, ';') THEN [1] ELSE [] END | SET n:Variable);

LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.rel_type = 'ADJUDICATED_BY'
MATCH (s:Entity {id: row.source_id})
MATCH (t:Entity {id: row.target_id})
MERGE (s)-[r:ADJUDICATED_BY {id: row.edge_id}]->(t)
SET r.claim_id = CASE row.claim_id WHEN '' THEN null ELSE row.claim_id END,
    r.confidence = CASE row.confidence WHEN '' THEN null ELSE toFloat(row.confidence) END,
    r.numeric_value = CASE row.numeric_value WHEN '' THEN null ELSE toFloat(row.numeric_value) END,
    r.run_id = row.run_id,
    r.status = row.status,
    r.raw_json = row.raw_json;

LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.rel_type = 'DENOTES'
MATCH (s:Entity {id: row.source_id})
MATCH (t:Entity {id: row.target_id})
MERGE (s)-[r:DENOTES {id: row.edge_id}]->(t)
SET r.claim_id = CASE row.claim_id WHEN '' THEN null ELSE row.claim_id END,
    r.confidence = CASE row.confidence WHEN '' THEN null ELSE toFloat(row.confidence) END,
    r.numeric_value = CASE row.numeric_value WHEN '' THEN null ELSE toFloat(row.numeric_value) END,
    r.run_id = row.run_id,
    r.status = row.status,
    r.raw_json = row.raw_json;

LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.rel_type = 'DERIVED_FROM'
MATCH (s:Entity {id: row.source_id})
MATCH (t:Entity {id: row.target_id})
MERGE (s)-[r:DERIVED_FROM {id: row.edge_id}]->(t)
SET r.claim_id = CASE row.claim_id WHEN '' THEN null ELSE row.claim_id END,
    r.confidence = CASE row.confidence WHEN '' THEN null ELSE toFloat(row.confidence) END,
    r.numeric_value = CASE row.numeric_value WHEN '' THEN null ELSE toFloat(row.numeric_value) END,
    r.run_id = row.run_id,
    r.status = row.status,
    r.raw_json = row.raw_json;

LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.rel_type = 'DISTINCT_FROM'
MATCH (s:Entity {id: row.source_id})
MATCH (t:Entity {id: row.target_id})
MERGE (s)-[r:DISTINCT_FROM {id: row.edge_id}]->(t)
SET r.claim_id = CASE row.claim_id WHEN '' THEN null ELSE row.claim_id END,
    r.confidence = CASE row.confidence WHEN '' THEN null ELSE toFloat(row.confidence) END,
    r.numeric_value = CASE row.numeric_value WHEN '' THEN null ELSE toFloat(row.numeric_value) END,
    r.run_id = row.run_id,
    r.status = row.status,
    r.raw_json = row.raw_json;

LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.rel_type = 'GENERATED'
MATCH (s:Entity {id: row.source_id})
MATCH (t:Entity {id: row.target_id})
MERGE (s)-[r:GENERATED {id: row.edge_id}]->(t)
SET r.claim_id = CASE row.claim_id WHEN '' THEN null ELSE row.claim_id END,
    r.confidence = CASE row.confidence WHEN '' THEN null ELSE toFloat(row.confidence) END,
    r.numeric_value = CASE row.numeric_value WHEN '' THEN null ELSE toFloat(row.numeric_value) END,
    r.run_id = row.run_id,
    r.status = row.status,
    r.raw_json = row.raw_json;

LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.rel_type = 'GOVERNED_BY'
MATCH (s:Entity {id: row.source_id})
MATCH (t:Entity {id: row.target_id})
MERGE (s)-[r:GOVERNED_BY {id: row.edge_id}]->(t)
SET r.claim_id = CASE row.claim_id WHEN '' THEN null ELSE row.claim_id END,
    r.confidence = CASE row.confidence WHEN '' THEN null ELSE toFloat(row.confidence) END,
    r.numeric_value = CASE row.numeric_value WHEN '' THEN null ELSE toFloat(row.numeric_value) END,
    r.run_id = row.run_id,
    r.status = row.status,
    r.raw_json = row.raw_json;

LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.rel_type = 'HAS_CELL'
MATCH (s:Entity {id: row.source_id})
MATCH (t:Entity {id: row.target_id})
MERGE (s)-[r:HAS_CELL {id: row.edge_id}]->(t)
SET r.claim_id = CASE row.claim_id WHEN '' THEN null ELSE row.claim_id END,
    r.confidence = CASE row.confidence WHEN '' THEN null ELSE toFloat(row.confidence) END,
    r.numeric_value = CASE row.numeric_value WHEN '' THEN null ELSE toFloat(row.numeric_value) END,
    r.run_id = row.run_id,
    r.status = row.status,
    r.raw_json = row.raw_json;

LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.rel_type = 'HAS_CHAPTER'
MATCH (s:Entity {id: row.source_id})
MATCH (t:Entity {id: row.target_id})
MERGE (s)-[r:HAS_CHAPTER {id: row.edge_id}]->(t)
SET r.claim_id = CASE row.claim_id WHEN '' THEN null ELSE row.claim_id END,
    r.confidence = CASE row.confidence WHEN '' THEN null ELSE toFloat(row.confidence) END,
    r.numeric_value = CASE row.numeric_value WHEN '' THEN null ELSE toFloat(row.numeric_value) END,
    r.run_id = row.run_id,
    r.status = row.status,
    r.raw_json = row.raw_json;

LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.rel_type = 'HAS_COLUMN'
MATCH (s:Entity {id: row.source_id})
MATCH (t:Entity {id: row.target_id})
MERGE (s)-[r:HAS_COLUMN {id: row.edge_id}]->(t)
SET r.claim_id = CASE row.claim_id WHEN '' THEN null ELSE row.claim_id END,
    r.confidence = CASE row.confidence WHEN '' THEN null ELSE toFloat(row.confidence) END,
    r.numeric_value = CASE row.numeric_value WHEN '' THEN null ELSE toFloat(row.numeric_value) END,
    r.run_id = row.run_id,
    r.status = row.status,
    r.raw_json = row.raw_json;

LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.rel_type = 'HAS_CONSTRAINT'
MATCH (s:Entity {id: row.source_id})
MATCH (t:Entity {id: row.target_id})
MERGE (s)-[r:HAS_CONSTRAINT {id: row.edge_id}]->(t)
SET r.claim_id = CASE row.claim_id WHEN '' THEN null ELSE row.claim_id END,
    r.confidence = CASE row.confidence WHEN '' THEN null ELSE toFloat(row.confidence) END,
    r.numeric_value = CASE row.numeric_value WHEN '' THEN null ELSE toFloat(row.numeric_value) END,
    r.run_id = row.run_id,
    r.status = row.status,
    r.raw_json = row.raw_json;

LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.rel_type = 'HAS_CRITERION'
MATCH (s:Entity {id: row.source_id})
MATCH (t:Entity {id: row.target_id})
MERGE (s)-[r:HAS_CRITERION {id: row.edge_id}]->(t)
SET r.claim_id = CASE row.claim_id WHEN '' THEN null ELSE row.claim_id END,
    r.confidence = CASE row.confidence WHEN '' THEN null ELSE toFloat(row.confidence) END,
    r.numeric_value = CASE row.numeric_value WHEN '' THEN null ELSE toFloat(row.numeric_value) END,
    r.run_id = row.run_id,
    r.status = row.status,
    r.raw_json = row.raw_json;

LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.rel_type = 'HAS_OBJECT'
MATCH (s:Entity {id: row.source_id})
MATCH (t:Entity {id: row.target_id})
MERGE (s)-[r:HAS_OBJECT {id: row.edge_id}]->(t)
SET r.claim_id = CASE row.claim_id WHEN '' THEN null ELSE row.claim_id END,
    r.confidence = CASE row.confidence WHEN '' THEN null ELSE toFloat(row.confidence) END,
    r.numeric_value = CASE row.numeric_value WHEN '' THEN null ELSE toFloat(row.numeric_value) END,
    r.run_id = row.run_id,
    r.status = row.status,
    r.raw_json = row.raw_json;

LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.rel_type = 'HAS_OUTCOME'
MATCH (s:Entity {id: row.source_id})
MATCH (t:Entity {id: row.target_id})
MERGE (s)-[r:HAS_OUTCOME {id: row.edge_id}]->(t)
SET r.claim_id = CASE row.claim_id WHEN '' THEN null ELSE row.claim_id END,
    r.confidence = CASE row.confidence WHEN '' THEN null ELSE toFloat(row.confidence) END,
    r.numeric_value = CASE row.numeric_value WHEN '' THEN null ELSE toFloat(row.numeric_value) END,
    r.run_id = row.run_id,
    r.status = row.status,
    r.raw_json = row.raw_json;

LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.rel_type = 'HAS_ROW'
MATCH (s:Entity {id: row.source_id})
MATCH (t:Entity {id: row.target_id})
MERGE (s)-[r:HAS_ROW {id: row.edge_id}]->(t)
SET r.claim_id = CASE row.claim_id WHEN '' THEN null ELSE row.claim_id END,
    r.confidence = CASE row.confidence WHEN '' THEN null ELSE toFloat(row.confidence) END,
    r.numeric_value = CASE row.numeric_value WHEN '' THEN null ELSE toFloat(row.numeric_value) END,
    r.run_id = row.run_id,
    r.status = row.status,
    r.raw_json = row.raw_json;

LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.rel_type = 'HAS_SECTION'
MATCH (s:Entity {id: row.source_id})
MATCH (t:Entity {id: row.target_id})
MERGE (s)-[r:HAS_SECTION {id: row.edge_id}]->(t)
SET r.claim_id = CASE row.claim_id WHEN '' THEN null ELSE row.claim_id END,
    r.confidence = CASE row.confidence WHEN '' THEN null ELSE toFloat(row.confidence) END,
    r.numeric_value = CASE row.numeric_value WHEN '' THEN null ELSE toFloat(row.numeric_value) END,
    r.run_id = row.run_id,
    r.status = row.status,
    r.raw_json = row.raw_json;

LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.rel_type = 'HAS_SOURCE_BLOCK'
MATCH (s:Entity {id: row.source_id})
MATCH (t:Entity {id: row.target_id})
MERGE (s)-[r:HAS_SOURCE_BLOCK {id: row.edge_id}]->(t)
SET r.claim_id = CASE row.claim_id WHEN '' THEN null ELSE row.claim_id END,
    r.confidence = CASE row.confidence WHEN '' THEN null ELSE toFloat(row.confidence) END,
    r.numeric_value = CASE row.numeric_value WHEN '' THEN null ELSE toFloat(row.numeric_value) END,
    r.run_id = row.run_id,
    r.status = row.status,
    r.raw_json = row.raw_json;

LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.rel_type = 'HAS_STAGE'
MATCH (s:Entity {id: row.source_id})
MATCH (t:Entity {id: row.target_id})
MERGE (s)-[r:HAS_STAGE {id: row.edge_id}]->(t)
SET r.claim_id = CASE row.claim_id WHEN '' THEN null ELSE row.claim_id END,
    r.confidence = CASE row.confidence WHEN '' THEN null ELSE toFloat(row.confidence) END,
    r.numeric_value = CASE row.numeric_value WHEN '' THEN null ELSE toFloat(row.numeric_value) END,
    r.run_id = row.run_id,
    r.status = row.status,
    r.raw_json = row.raw_json;

LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.rel_type = 'HAS_SUBJECT'
MATCH (s:Entity {id: row.source_id})
MATCH (t:Entity {id: row.target_id})
MERGE (s)-[r:HAS_SUBJECT {id: row.edge_id}]->(t)
SET r.claim_id = CASE row.claim_id WHEN '' THEN null ELSE row.claim_id END,
    r.confidence = CASE row.confidence WHEN '' THEN null ELSE toFloat(row.confidence) END,
    r.numeric_value = CASE row.numeric_value WHEN '' THEN null ELSE toFloat(row.numeric_value) END,
    r.run_id = row.run_id,
    r.status = row.status,
    r.raw_json = row.raw_json;

LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.rel_type = 'HAS_TASK'
MATCH (s:Entity {id: row.source_id})
MATCH (t:Entity {id: row.target_id})
MERGE (s)-[r:HAS_TASK {id: row.edge_id}]->(t)
SET r.claim_id = CASE row.claim_id WHEN '' THEN null ELSE row.claim_id END,
    r.confidence = CASE row.confidence WHEN '' THEN null ELSE toFloat(row.confidence) END,
    r.numeric_value = CASE row.numeric_value WHEN '' THEN null ELSE toFloat(row.numeric_value) END,
    r.run_id = row.run_id,
    r.status = row.status,
    r.raw_json = row.raw_json;

LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.rel_type = 'HAS_VARIABLE'
MATCH (s:Entity {id: row.source_id})
MATCH (t:Entity {id: row.target_id})
MERGE (s)-[r:HAS_VARIABLE {id: row.edge_id}]->(t)
SET r.claim_id = CASE row.claim_id WHEN '' THEN null ELSE row.claim_id END,
    r.confidence = CASE row.confidence WHEN '' THEN null ELSE toFloat(row.confidence) END,
    r.numeric_value = CASE row.numeric_value WHEN '' THEN null ELSE toFloat(row.numeric_value) END,
    r.run_id = row.run_id,
    r.status = row.status,
    r.raw_json = row.raw_json;

LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.rel_type = 'IN_COLUMN'
MATCH (s:Entity {id: row.source_id})
MATCH (t:Entity {id: row.target_id})
MERGE (s)-[r:IN_COLUMN {id: row.edge_id}]->(t)
SET r.claim_id = CASE row.claim_id WHEN '' THEN null ELSE row.claim_id END,
    r.confidence = CASE row.confidence WHEN '' THEN null ELSE toFloat(row.confidence) END,
    r.numeric_value = CASE row.numeric_value WHEN '' THEN null ELSE toFloat(row.numeric_value) END,
    r.run_id = row.run_id,
    r.status = row.status,
    r.raw_json = row.raw_json;

LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.rel_type = 'MEASURED_BY'
MATCH (s:Entity {id: row.source_id})
MATCH (t:Entity {id: row.target_id})
MERGE (s)-[r:MEASURED_BY {id: row.edge_id}]->(t)
SET r.claim_id = CASE row.claim_id WHEN '' THEN null ELSE row.claim_id END,
    r.confidence = CASE row.confidence WHEN '' THEN null ELSE toFloat(row.confidence) END,
    r.numeric_value = CASE row.numeric_value WHEN '' THEN null ELSE toFloat(row.numeric_value) END,
    r.run_id = row.run_id,
    r.status = row.status,
    r.raw_json = row.raw_json;

LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.rel_type = 'MITIGATES'
MATCH (s:Entity {id: row.source_id})
MATCH (t:Entity {id: row.target_id})
MERGE (s)-[r:MITIGATES {id: row.edge_id}]->(t)
SET r.claim_id = CASE row.claim_id WHEN '' THEN null ELSE row.claim_id END,
    r.confidence = CASE row.confidence WHEN '' THEN null ELSE toFloat(row.confidence) END,
    r.numeric_value = CASE row.numeric_value WHEN '' THEN null ELSE toFloat(row.numeric_value) END,
    r.run_id = row.run_id,
    r.status = row.status,
    r.raw_json = row.raw_json;

LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.rel_type = 'PRECEDES'
MATCH (s:Entity {id: row.source_id})
MATCH (t:Entity {id: row.target_id})
MERGE (s)-[r:PRECEDES {id: row.edge_id}]->(t)
SET r.claim_id = CASE row.claim_id WHEN '' THEN null ELSE row.claim_id END,
    r.confidence = CASE row.confidence WHEN '' THEN null ELSE toFloat(row.confidence) END,
    r.numeric_value = CASE row.numeric_value WHEN '' THEN null ELSE toFloat(row.numeric_value) END,
    r.run_id = row.run_id,
    r.status = row.status,
    r.raw_json = row.raw_json;

LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.rel_type = 'PRODUCES'
MATCH (s:Entity {id: row.source_id})
MATCH (t:Entity {id: row.target_id})
MERGE (s)-[r:PRODUCES {id: row.edge_id}]->(t)
SET r.claim_id = CASE row.claim_id WHEN '' THEN null ELSE row.claim_id END,
    r.confidence = CASE row.confidence WHEN '' THEN null ELSE toFloat(row.confidence) END,
    r.numeric_value = CASE row.numeric_value WHEN '' THEN null ELSE toFloat(row.numeric_value) END,
    r.run_id = row.run_id,
    r.status = row.status,
    r.raw_json = row.raw_json;

LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.rel_type = 'REQUIRES_INPUT'
MATCH (s:Entity {id: row.source_id})
MATCH (t:Entity {id: row.target_id})
MERGE (s)-[r:REQUIRES_INPUT {id: row.edge_id}]->(t)
SET r.claim_id = CASE row.claim_id WHEN '' THEN null ELSE row.claim_id END,
    r.confidence = CASE row.confidence WHEN '' THEN null ELSE toFloat(row.confidence) END,
    r.numeric_value = CASE row.numeric_value WHEN '' THEN null ELSE toFloat(row.numeric_value) END,
    r.run_id = row.run_id,
    r.status = row.status,
    r.raw_json = row.raw_json;

LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.rel_type = 'SUPPORTED_BY'
MATCH (s:Entity {id: row.source_id})
MATCH (t:Entity {id: row.target_id})
MERGE (s)-[r:SUPPORTED_BY {id: row.edge_id}]->(t)
SET r.claim_id = CASE row.claim_id WHEN '' THEN null ELSE row.claim_id END,
    r.confidence = CASE row.confidence WHEN '' THEN null ELSE toFloat(row.confidence) END,
    r.numeric_value = CASE row.numeric_value WHEN '' THEN null ELSE toFloat(row.numeric_value) END,
    r.run_id = row.run_id,
    r.status = row.status,
    r.raw_json = row.raw_json;

LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.rel_type = 'SUPPORTS_DECISION'
MATCH (s:Entity {id: row.source_id})
MATCH (t:Entity {id: row.target_id})
MERGE (s)-[r:SUPPORTS_DECISION {id: row.edge_id}]->(t)
SET r.claim_id = CASE row.claim_id WHEN '' THEN null ELSE row.claim_id END,
    r.confidence = CASE row.confidence WHEN '' THEN null ELSE toFloat(row.confidence) END,
    r.numeric_value = CASE row.numeric_value WHEN '' THEN null ELSE toFloat(row.numeric_value) END,
    r.run_id = row.run_id,
    r.status = row.status,
    r.raw_json = row.raw_json;
