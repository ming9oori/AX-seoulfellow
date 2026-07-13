:param system_id => 'R5-B1';
MATCH p=(a:WorkUnit)-[r:PRECEDES]->(b:WorkUnit)
WHERE a.system_id=$system_id RETURN p LIMIT 60;
