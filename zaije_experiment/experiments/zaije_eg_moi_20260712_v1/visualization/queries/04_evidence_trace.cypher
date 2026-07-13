MATCH p=(x:Assertion)-[:DERIVED_FROM]->(a:EvidenceUnit)<-[:HAS_ANCHOR]-(e:EvidenceUnit) RETURN p LIMIT 100;
