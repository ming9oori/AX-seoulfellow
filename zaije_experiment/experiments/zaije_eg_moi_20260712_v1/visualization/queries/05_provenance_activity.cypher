MATCH p=(x:Assertion)-[:WAS_GENERATED_BY]->(a:ExtractionActivity) RETURN p LIMIT 100;
