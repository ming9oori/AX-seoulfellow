// TRACE-OL Neo4j pilot constraints and validation queries
// Current Cypher constraint syntax; adjust database/edition-specific options as needed.

CREATE CONSTRAINT document_id IF NOT EXISTS
FOR (n:Document) REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT section_id IF NOT EXISTS
FOR (n:Section) REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT evidence_id IF NOT EXISTS
FOR (n:Evidence) REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT claim_id IF NOT EXISTS
FOR (n:Claim) REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT concept_id IF NOT EXISTS
FOR (n:Concept) REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT assertion_id IF NOT EXISTS
FOR (n:Assertion) REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT rule_id IF NOT EXISTS
FOR (n:Rule) REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT condition_id IF NOT EXISTS
FOR (n:Condition) REQUIRE n.id IS UNIQUE;

