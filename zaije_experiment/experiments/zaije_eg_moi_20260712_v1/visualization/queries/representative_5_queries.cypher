// 1. Induced ontology schema: 8 SUBCLASS_OF relationships
MATCH p=(:SchemaClass)-[:SUBCLASS_OF]->(:MetaClass)
RETURN p LIMIT 50;

// 2. Work inputs and outputs: 13 HAS_INPUT + 3 PRODUCES_OUTPUT
MATCH p=(:ConceptCluster)-[r]->(:ConceptCluster)
WHERE type(r) IN ['HAS_INPUT', 'PRODUCES_OUTPUT']
RETURN p LIMIT 50;

// 3. Work performers: 8 PERFORMED_BY relationships
MATCH p=(:ConceptCluster)-[:PERFORMED_BY]->(:ConceptCluster)
RETURN p LIMIT 30;

// 4. Work sequence: 201 PRECEDES relationships
MATCH p=(:ConceptCluster)-[:PRECEDES]->(:ConceptCluster)
RETURN p LIMIT 50;

// 5. Assertion-to-source trace: 445 DERIVED_FROM relationships
MATCH p=(:Assertion)-[:DERIVED_FROM]->(:EvidenceUnit)
RETURN p LIMIT 50;
