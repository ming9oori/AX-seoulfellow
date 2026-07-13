:param system_id => 'R5-B1';
MATCH (m:Mention)-[:DENOTES]->(c:DomainConcept)
WHERE c.system_id=$system_id WITH c,count(m) AS surface_count WHERE surface_count>1
RETURN c.uid,c.label,surface_count ORDER BY surface_count DESC LIMIT 30;
