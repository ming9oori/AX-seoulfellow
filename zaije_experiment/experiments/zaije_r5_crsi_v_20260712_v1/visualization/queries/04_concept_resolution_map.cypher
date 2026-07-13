:param system_id => 'R5-B1';
MATCH p=(m:Mention)-[:DENOTES]->(c:DomainConcept)
WHERE c.system_id=$system_id OPTIONAL MATCH q=(a:MergeActivity)-[:GENERATED]->(c)
RETURN p,q LIMIT 80;
