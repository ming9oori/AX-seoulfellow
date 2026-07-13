:param system_id => 'R5-B1';
MATCH p=(t:Template)-[:HAS_FIELD]->(f:TemplateField)
WHERE t.system_id=$system_id RETURN p LIMIT 80;
