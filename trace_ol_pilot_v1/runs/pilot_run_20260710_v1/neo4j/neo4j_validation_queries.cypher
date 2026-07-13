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

// -----------------------------------------------------------------------------
// Mandatory validation queries. Every query should return zero rows unless noted.
// -----------------------------------------------------------------------------

// V1. Accepted claim without evidence.
MATCH (c:Claim)
WHERE c.status = 'ACCEPTED'
  AND NOT EXISTS { MATCH (:Evidence)-[:SUPPORTS]->(c) }
RETURN c.id AS claim_id;

// V2. Accepted assertion without source claim.
MATCH (a:Assertion)
WHERE a.status = 'ACCEPTED'
  AND NOT EXISTS { MATCH (:Claim)-[:PROMOTED_TO]->(a) }
RETURN a.id AS assertion_id;

// V3. Accepted assertion without source evidence path.
MATCH (a:Assertion)
WHERE a.status = 'ACCEPTED'
  AND NOT EXISTS {
    MATCH (:Evidence)-[:SUPPORTS]->(:Claim)-[:PROMOTED_TO]->(a)
  }
RETURN a.id AS assertion_id;

// V4. Discourse claims incorrectly promoted to operational assertions.
MATCH (c:Claim)-[:PROMOTED_TO]->(a:Assertion)
WHERE c.claim_family = 'DISCOURSE'
  AND a.status = 'ACCEPTED'
RETURN c.id AS claim_id, c.claim_type AS claim_type, a.id AS assertion_id;

// V5. NeedsReview claims included in the operational projection.
MATCH (c:Claim)-[:PROMOTED_TO]->(a:Assertion)
WHERE c.status = 'NEEDS_REVIEW'
  AND a.operational = true
RETURN c.id AS claim_id, a.id AS assertion_id;

// V6. MUST_NOT with non-negative polarity.
MATCH (c:Claim)
WHERE c.modality = 'MUST_NOT'
  AND coalesce(c.polarity, 'NONE') <> 'NEGATIVE'
RETURN c.id AS claim_id, c.polarity AS polarity;

// V7. Accepted operational relationship missing lineage properties.
MATCH ()-[r]->()
WHERE coalesce(r.operational, false) = true
  AND (r.claim_id IS NULL OR r.evidence_id IS NULL OR r.assertion_id IS NULL)
RETURN type(r) AS rel_type, r.assertion_id AS assertion_id;

// V8. Orphan concepts. Informational; some lexical-only concepts may be allowed.
MATCH (c:Concept)
WHERE NOT (c)--()
RETURN c.id AS concept_id, c.pref_label AS pref_label;

// V9. Counts by claim status and tier. Expected to return a dashboard table.
MATCH (c:Claim)
RETURN c.status AS status,
       c.reference_tier AS reference_tier,
       count(*) AS claim_count
ORDER BY status, reference_tier;

// V10. Counts by operational relationship type. Expected dashboard table.
MATCH ()-[r]->()
WHERE coalesce(r.operational, false) = true
RETURN type(r) AS relationship_type, count(*) AS relationship_count
ORDER BY relationship_count DESC;

// -----------------------------------------------------------------------------
// Visualization queries
// -----------------------------------------------------------------------------

// Q1. Evidence → Claim → Assertion → entities audit path.
MATCH p=(e:Evidence)-[:SUPPORTS]->(c:Claim)-[:PROMOTED_TO]->(a:Assertion)
OPTIONAL MATCH p2=(a)-[:SUBJECT|OBJECT]->(x)
RETURN p, p2
LIMIT 50;

// Q2. Process and artifact projection.
MATCH p=(t:Task)-[r:PRODUCES]->(a:Artifact)
WHERE coalesce(r.operational, false) = true
RETURN p
LIMIT 100;

// Q3. Event-triggered decisions.
MATCH p=(e:Event)-[r:TRIGGERS]->(d:Decision)
WHERE coalesce(r.operational, false) = true
RETURN p
LIMIT 100;

// Q4. Rules with evidence.
MATCH (ev:Evidence)-[:SUPPORTS]->(c:Claim)-[:PROMOTED_TO]->(r:Rule)
OPTIONAL MATCH p1=(r)-[:HAS_ANTECEDENT]->(cond:Condition)
OPTIONAL MATCH p2=(r)-[:HAS_CONSEQUENT]->(act)
RETURN ev, c, r, p1, p2
LIMIT 50;

// Q5. Claims requiring review.
MATCH (e:Evidence)-[:SUPPORTS]->(c:Claim)
WHERE c.status = 'NEEDS_REVIEW'
RETURN e.id AS evidence_id,
       c.id AS claim_id,
       c.claim_type AS claim_type,
       c.modality AS modality,
       c.uncertainty_code AS uncertainty_code
ORDER BY c.risk DESC, c.confidence ASC
LIMIT 100;
