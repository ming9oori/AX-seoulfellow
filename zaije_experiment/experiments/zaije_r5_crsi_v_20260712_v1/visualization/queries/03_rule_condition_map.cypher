:param system_id => 'R5-B1';
MATCH p=(r:Rule)-[rel]->(x)
WHERE r.system_id=$system_id AND type(rel) IN ['HAS_CONDITION','HAS_EXCEPTION','HAS_QUANTITY_CONSTRAINT','HAS_ACTION','DERIVED_FROM']
RETURN p LIMIT 80;
