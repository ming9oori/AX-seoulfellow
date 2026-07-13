MATCH p=(w:WorkUnit)-[r]->(x)
WHERE w.system_id='SIMPLE-E2E' AND type(r) IN ['HAS_INPUT','PRODUCES_OUTPUT']
RETURN p LIMIT 120;
