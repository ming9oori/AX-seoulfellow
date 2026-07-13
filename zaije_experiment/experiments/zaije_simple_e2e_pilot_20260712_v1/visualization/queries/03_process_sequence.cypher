MATCH p=(a:WorkUnit)-[:PRECEDES]->(b:WorkUnit)
WHERE a.system_id='SIMPLE-E2E' RETURN p LIMIT 100;
