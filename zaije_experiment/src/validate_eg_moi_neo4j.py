#!/usr/bin/env python3
"""Validate a live Neo4j import of the EG-MOI graph."""

from __future__ import annotations

import json
import os
from pathlib import Path

from neo4j import GraphDatabase


EXPERIMENT_ID = "zaije_eg_moi_20260712_v1"
SYSTEM_ID = "EG-MOI-V1"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def scalar(session, query: str) -> int:
    return int(session.run(query).single()["value"])


def main() -> int:
    project = Path(__file__).resolve().parents[1]
    root = project / "experiments" / EXPERIMENT_ID
    expected = read_json(root / "evaluation" / "export_metrics.json")
    uri = os.environ.get("NEO4J_URI", "bolt://127.0.0.1:7689")
    driver = GraphDatabase.driver(uri, auth=None)
    with driver.session(database="neo4j") as session:
        session.run("CREATE CONSTRAINT eg_uid_unique IF NOT EXISTS ON (n:EGEntity) ASSERT n.uid IS UNIQUE").consume()
        session.run("CREATE INDEX eg_system IF NOT EXISTS FOR (n:EGEntity) ON (n.system_id)").consume()
        session.run("CREATE INDEX eg_type IF NOT EXISTS FOR (n:EGEntity) ON (n.type)").consume()
        session.run("CREATE INDEX eg_status IF NOT EXISTS FOR (n:EGEntity) ON (n.status)").consume()
        session.run("CALL db.awaitIndexes(120)").consume()
        node_count = scalar(session, "MATCH (n) RETURN count(n) AS value")
        rel_count = scalar(session, "MATCH ()-[r]->() RETURN count(r) AS value")
        assertion_count = scalar(session, "MATCH (n:Assertion {status:'VALIDATED'}) RETURN count(n) AS value")
        assertion_grounded = scalar(session, "MATCH (n:Assertion {status:'VALIDATED'}) WHERE n.evidence_anchor_ids <> '[]' RETURN count(n) AS value")
        assertion_generated = scalar(session, "MATCH (:Assertion {status:'VALIDATED'})-[r:WAS_GENERATED_BY]->(:ExtractionActivity) RETURN count(DISTINCT r) AS value")
        invalid_endpoint = scalar(session, "MATCH ()-[r]->() WHERE startNode(r) IS NULL OR endNode(r) IS NULL RETURN count(r) AS value")
        views = {
            "schema": scalar(session, "MATCH (:SchemaClass)-[r:SUBCLASS_OF]->(:MetaClass) RETURN count(r) AS value"),
            "operational": scalar(session, "MATCH (:ConceptCluster)-[r]->(:ConceptCluster) WHERE type(r) IN ['PERFORMED_BY','HAS_INPUT','PRODUCES_OUTPUT','HAS_CONDITION','HAS_MEASURE','PRECEDES'] RETURN count(r) AS value"),
            "consolidation": scalar(session, "MATCH (:Mention)-[r:DENOTES]->(:ConceptCluster) RETURN count(r) AS value"),
            "evidence_trace": scalar(session, "MATCH (:Assertion)-[r:DERIVED_FROM]->(:EvidenceUnit) RETURN count(r) AS value"),
            "provenance": scalar(session, "MATCH (:Assertion)-[r:WAS_GENERATED_BY]->(:ExtractionActivity) RETURN count(r) AS value"),
            "unresolved": scalar(session, "MATCH (n:ConceptCluster {status:'UNRESOLVED'}) RETURN count(n) AS value"),
        }
        node_type_counts = {row["type"]: row["count"] for row in session.run("MATCH (n) RETURN n.type AS type,count(*) AS count ORDER BY type")}
        relation_counts = {row["type"]: row["count"] for row in session.run("MATCH ()-[r]->() RETURN type(r) AS type,count(*) AS count ORDER BY type")}
        constraints = [dict(row) for row in session.run("SHOW CONSTRAINTS YIELD name,type RETURN name,type")]
        indexes = [dict(row) for row in session.run("SHOW INDEXES YIELD name,state RETURN name,state")]
        version = session.run("CALL dbms.components() YIELD versions RETURN versions[0] AS version").single()["version"]
    driver.close()
    result = {
        "runtime": "LOCAL_NEO4J_COMMUNITY",
        "neo4j_version": version,
        "uri": uri,
        "node_count": node_count,
        "expected_node_count": expected["neo4j_node_export_count"],
        "relationship_count": rel_count,
        "expected_relationship_count": expected["neo4j_relationship_export_count"],
        "node_coverage": node_count / expected["neo4j_node_export_count"],
        "relationship_coverage": rel_count / expected["neo4j_relationship_export_count"],
        "validated_assertion_count": assertion_count,
        "assertion_evidence_coverage": assertion_grounded / assertion_count if assertion_count else 1.0,
        "assertion_activity_coverage": assertion_generated / assertion_count if assertion_count else 1.0,
        "invalid_endpoint_count": invalid_endpoint,
        "view_result_counts": views,
        "all_required_views_nonempty": all(views.values()),
        "node_type_counts": node_type_counts,
        "relationship_type_counts": relation_counts,
        "constraints": constraints,
        "indexes": indexes,
        "system_id": SYSTEM_ID,
    }
    result["pass"] = all([
        result["node_coverage"] == 1.0,
        result["relationship_coverage"] == 1.0,
        result["assertion_evidence_coverage"] == 1.0,
        result["assertion_activity_coverage"] == 1.0,
        result["invalid_endpoint_count"] == 0,
        result["all_required_views_nonempty"],
    ])
    write_json(root / "neo4j" / "runtime_validation.json", result)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
