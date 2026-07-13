// CQ-01
MATCH p=(s:Stage)-[:PRECEDES]->(n:Stage) RETURN s.canonical_name, n.canonical_name;
// CQ-03
MATCH (t:Task)-[r:REQUIRES_INPUT]->(i) WHERE t.canonical_name CONTAINS 'Proposal Planning' RETURN t.canonical_name, i.canonical_name, r.claim_id;
// CQ-04
MATCH (l:LexicalEntry)-[:DENOTES]->(c:Concept) WHERE l.canonical_name = 'Capture Plan' RETURN c.id, c.canonical_name, labels(c);
// CQ-06/07
MATCH (t:Task)-[p:PRODUCES]->(b:Artifact) WHERE b.canonical_name CONTAINS 'BCM' OPTIONAL MATCH (b)-[c:HAS_CRITERION]->(criterion) RETURN t.canonical_name, b.canonical_name, collect(criterion.canonical_name), p.claim_id;
// CQ-08
MATCH (f:Formula)-[:HAS_VARIABLE]->(v:Variable) OPTIONAL MATCH (f)-[:HAS_CONSTRAINT]->(c:Constraint) RETURN f.expression, collect(DISTINCT v.symbol), collect(DISTINCT c.expression);
// CQ-10
MATCH (m)-[r:MITIGATES]->(risk:Risk) RETURN m.canonical_name, risk.canonical_name, r.claim_id;
// CQ-12
MATCH (s)-[r]->(o) WHERE r.claim_id IS NOT NULL MATCH (c:Claim {id:r.claim_id})-[:SUPPORTED_BY]->(e) RETURN s.canonical_name, type(r), o.canonical_name, c.id, e.id;
