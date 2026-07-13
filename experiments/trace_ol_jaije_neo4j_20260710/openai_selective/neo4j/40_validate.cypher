// Replace the literal with the run_id from manifest.json when needed.
MATCH (s:SourceBlock) RETURN count(s) AS source_blocks;
MATCH (s:SourceBlock) WITH s.excel_row AS excel_row, count(*) AS c WHERE c <> 1 RETURN excel_row, c;
MATCH (c:Claim {status:'Accepted'}) WHERE NOT (c)-[:SUPPORTED_BY]->() RETURN c.id, c.predicate;
MATCH ()-[r]->() WHERE r.claim_id IS NOT NULL OPTIONAL MATCH (c:Claim {id:r.claim_id, status:'Accepted'}) WITH r,c WHERE c IS NULL RETURN type(r), r.claim_id;
MATCH (s)-[r:PRODUCES]->(o) WHERE NOT s:Task OR NOT (o:Artifact OR o:InformationObject) RETURN s.id, o.id, r.claim_id;
MATCH (s)-[r:MITIGATES]->(o) WHERE NOT (s:Mitigation OR s:Task) OR NOT o:Risk RETURN s.id, o.id, r.claim_id;
