:param system_id => 'R5-B1';
MATCH (n:R5Entity) WHERE n.system_id=$system_id AND n.type IN ['DomainConcept','Rule','Condition','Metric','Template','TemplateField','WorkUnit']
AND coalesce(n.evidence_anchor_ids,'[]')='[]' RETURN count(n) AS orphan_count;
