MATCH p=(w:WorkUnit)-[:PERFORMED_BY]->(a)
WHERE w.system_id='SIMPLE-E2E' AND (a:Actor OR a:Organization)
RETURN p LIMIT 100;
