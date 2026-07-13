MATCH p=(m:Mention)-[:DERIVED_FROM]->(a:Anchor)<-[:HAS_ANCHOR]-(e:EvidenceBundle)
WHERE m.system_id='SIMPLE-E2E' RETURN p LIMIT 100;
