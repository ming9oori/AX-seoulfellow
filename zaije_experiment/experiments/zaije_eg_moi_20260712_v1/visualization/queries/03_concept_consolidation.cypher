MATCH p=(m:Mention)-[:DENOTES]->(c:ConceptCluster) WHERE c.status='VALIDATED' RETURN p LIMIT 100;
