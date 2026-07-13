CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (n:Entity) REQUIRE n.id IS UNIQUE;
CREATE INDEX source_excel_row IF NOT EXISTS FOR (n:SourceBlock) ON (n.excel_row);
CREATE INDEX source_page IF NOT EXISTS FOR (n:SourceBlock) ON (n.page);
CREATE INDEX claim_status IF NOT EXISTS FOR (n:Claim) ON (n.status);
CREATE INDEX claim_predicate IF NOT EXISTS FOR (n:Claim) ON (n.predicate);
CREATE INDEX concept_name IF NOT EXISTS FOR (n:Concept) ON (n.canonical_name);
