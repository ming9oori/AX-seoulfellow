MATCH (n) WHERE n.system_id='SIMPLE-E2E' AND n.type IN ['WorkUnit','Actor','Organization','Artifact','InformationObject']
RETURN n.type AS type,n.confidence AS confidence,count(*) AS count ORDER BY type,confidence;
