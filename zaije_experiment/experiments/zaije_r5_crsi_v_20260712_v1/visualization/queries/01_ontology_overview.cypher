:param system_id => 'R5-B1';
MATCH p=(a:R5Entity)-[r]->(b:R5Entity)
WHERE a.system_id=$system_id AND r.type IN ['HAS_DEFINITION','HAS_ALIAS','PRECEDES','HAS_CONDITION','HAS_QUANTITY_CONSTRAINT','HAS_FIELD']
RETURN p LIMIT 80;
