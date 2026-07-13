#!/usr/bin/env python3
"""Validate the imported R5 graph against a running Neo4j instance."""

from __future__ import annotations

import json
from pathlib import Path

from neo4j import GraphDatabase

import r5_crsi as r5


def scalar(session, query: str, key: str = "value") -> int | float:
    return session.run(query).single()[key]


def main() -> int:
    project = Path(__file__).resolve().parents[1]
    root = project / "experiments" / r5.EXPERIMENT_ID
    expected = r5.read_json(root / "graphs" / "export_metrics.json")
    driver = GraphDatabase.driver("bolt://127.0.0.1:7688", auth=None)
    with driver.session(database="neo4j") as session:
        session.run("CREATE CONSTRAINT r5_uid_unique IF NOT EXISTS ON (n:R5Entity) ASSERT n.uid IS UNIQUE").consume()
        session.run("CREATE INDEX r5_system_id IF NOT EXISTS FOR (n:R5Entity) ON (n.system_id)").consume()
        session.run("CREATE INDEX r5_type IF NOT EXISTS FOR (n:R5Entity) ON (n.type)").consume()
        session.run("CALL db.awaitIndexes(120)").consume()
        node_count = scalar(session, "MATCH (n) RETURN count(n) AS value")
        rel_count = scalar(session, "MATCH ()-[r]->() RETURN count(r) AS value")
        registry = sorted(r5.RELATION_REGISTRY)
        registry_literal = json.dumps(registry)
        registry_count = scalar(session, f"MATCH ()-[r]->() WHERE r.type IN {registry_literal} RETURN count(r) AS value")
        registry_grounded = scalar(session, f"MATCH ()-[r]->() WHERE r.type IN {registry_literal} AND r.evidence_anchor_ids <> '[]' RETURN count(r) AS value")
        views = {
            "01_ontology_overview": scalar(session, "MATCH (a)-[r]->(b) WHERE a.system_id='R5-B1' AND r.type IN ['HAS_DEFINITION','HAS_ALIAS','PRECEDES','HAS_CONDITION','HAS_QUANTITY_CONSTRAINT','HAS_FIELD'] RETURN count(r) AS value"),
            "02_work_process_map": scalar(session, "MATCH (:WorkUnit)-[r:PRECEDES]->(:WorkUnit) RETURN count(r) AS value"),
            "03_rule_condition_map": scalar(session, "MATCH (:Rule)-[r]->() WHERE type(r) IN ['HAS_CONDITION','HAS_EXCEPTION','HAS_QUANTITY_CONSTRAINT','HAS_ACTION','DERIVED_FROM'] RETURN count(r) AS value"),
            "04_concept_resolution_map": scalar(session, "MATCH (:Mention)-[r:DENOTES]->(:DomainConcept) RETURN count(r) AS value"),
            "05_template_field_map": scalar(session, "MATCH (:Template)-[r:HAS_FIELD]->(:TemplateField) RETURN count(r) AS value"),
            "06_evidence_trace": scalar(session, "MATCH (:R5Entity)-[r:DERIVED_FROM]->(:Anchor)<-[:HAS_ANCHOR]-(:EvidenceBundle)<-[:HAS_EVIDENCE]-(:Section) RETURN count(r) AS value"),
        }
        rule_total = scalar(session, "MATCH (r:Rule) RETURN count(r) AS value")
        rule_traced = scalar(session, "MATCH (r:Rule)-[:DERIVED_FROM]->(:Anchor) RETURN count(DISTINCT r) AS value")
        concept_total = scalar(session, "MATCH (c:DomainConcept) RETURN count(c) AS value")
        concept_mentioned = scalar(session, "MATCH (:Mention)-[:DENOTES]->(c:DomainConcept) RETURN count(DISTINCT c) AS value")
        constraints = [dict(row) for row in session.run("SHOW CONSTRAINTS YIELD name,type RETURN name,type")]
        indexes = [dict(row) for row in session.run("SHOW INDEXES YIELD name,state RETURN name,state")]
    driver.close()
    result = {
        "neo4j_version": "4.4.43", "runtime": "LOCAL_COMMUNITY_SERVER", "database": "neo4j",
        "node_count": node_count, "expected_node_count": expected["neo4j_node_export_count"],
        "relationship_count": rel_count, "expected_relationship_count": expected["neo4j_relationship_export_count"],
        "node_coverage": node_count / expected["neo4j_node_export_count"],
        "relationship_coverage": rel_count / expected["neo4j_relationship_export_count"],
        "registry_relation_count": registry_count,
        "provenance_property_coverage": registry_grounded / registry_count if registry_count else 1.0,
        "view_result_counts": views, "required_six_non_empty": sum(value > 0 for value in views.values()),
        "rule_total": rule_total, "rule_traced": rule_traced, "rule_anchor_path_coverage": rule_traced / rule_total if rule_total else 1.0,
        "concept_total": concept_total, "concept_mentioned": concept_mentioned, "concept_mention_path_coverage": concept_mentioned / concept_total if concept_total else 1.0,
        "constraints": constraints, "indexes": indexes,
    }
    result["H5_F_pass"] = all([
        result["node_coverage"] == 1.0, result["relationship_coverage"] == 1.0,
        result["provenance_property_coverage"] == 1.0, result["required_six_non_empty"] == 6,
        result["rule_anchor_path_coverage"] == 1.0, result["concept_mention_path_coverage"] == 1.0,
    ])
    r5.write_json(root / "graphs" / "neo4j" / "runtime_validation.json", result)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["H5_F_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
