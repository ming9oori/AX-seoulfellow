:param system_id => 'R5-B1';
MATCH p=(x:R5Entity)-[:DERIVED_FROM]->(a:Anchor)<-[:HAS_ANCHOR]-(e:EvidenceBundle)<-[:HAS_EVIDENCE]-(s:Section)
WHERE x.system_id=$system_id RETURN p LIMIT 60;
