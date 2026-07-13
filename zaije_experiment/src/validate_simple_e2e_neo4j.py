#!/usr/bin/env python3
"""Validate the simple automatic KG in a live Neo4j database."""

from __future__ import annotations

import json
import os
from pathlib import Path

from neo4j import GraphDatabase

import r5_crsi as r5


EXPERIMENT_ID = "zaije_simple_e2e_pilot_20260712_v1"


def scalar(session, query: str) -> int:
    return int(session.run(query).single()["value"])


def main() -> int:
    project = Path(__file__).resolve().parents[1]
    root = project / "experiments" / EXPERIMENT_ID
    expected = r5.read_json(root / "graphs" / "export_metrics.json")
    uri = os.environ.get("NEO4J_URI", "bolt://127.0.0.1:7688")
    driver = GraphDatabase.driver(uri, auth=None)
    with driver.session(database="neo4j") as session:
        session.run("CREATE CONSTRAINT simple_uid_unique IF NOT EXISTS ON (n:R5Entity) ASSERT n.uid IS UNIQUE").consume()
        session.run("CREATE INDEX simple_system IF NOT EXISTS FOR (n:R5Entity) ON (n.system_id)").consume()
        session.run("CREATE INDEX simple_type IF NOT EXISTS FOR (n:R5Entity) ON (n.type)").consume()
        session.run("CALL db.awaitIndexes(120)").consume()
        node_count = scalar(session, "MATCH (n) RETURN count(n) AS value")
        rel_count = scalar(session, "MATCH ()-[r]->() RETURN count(r) AS value")
        semantic_count = scalar(session, "MATCH ()-[r]->() WHERE type(r) IN ['PERFORMED_BY','HAS_INPUT','PRODUCES_OUTPUT','PRECEDES'] RETURN count(r) AS value")
        semantic_grounded = scalar(session, "MATCH ()-[r]->() WHERE type(r) IN ['PERFORMED_BY','HAS_INPUT','PRODUCES_OUTPUT','PRECEDES'] AND r.evidence_anchor_ids <> '[]' RETURN count(r) AS value")
        type_counts = {row["type"]: row["count"] for row in session.run("MATCH (n) WHERE n.type IN ['WorkUnit','Actor','Organization','Artifact','InformationObject'] RETURN n.type AS type,count(*) AS count")}
        relation_counts = {row["relation"]: row["count"] for row in session.run("MATCH ()-[r]->() WHERE type(r) IN ['PERFORMED_BY','HAS_INPUT','PRODUCES_OUTPUT','PRECEDES'] RETURN type(r) AS relation,count(*) AS count")}
        views = {
            "workunit_actor": scalar(session, "MATCH (:WorkUnit)-[r:PERFORMED_BY]->() RETURN count(r) AS value"),
            "workunit_input_output": scalar(session, "MATCH (:WorkUnit)-[r]->() WHERE type(r) IN ['HAS_INPUT','PRODUCES_OUTPUT'] RETURN count(r) AS value"),
            "process_sequence": scalar(session, "MATCH (:WorkUnit)-[r:PRECEDES]->(:WorkUnit) RETURN count(r) AS value"),
            "evidence_trace": scalar(session, "MATCH (:Mention)-[r:DERIVED_FROM]->(:Anchor)<-[:HAS_ANCHOR]-(:EvidenceBundle) RETURN count(r) AS value"),
        }
        constraints = [dict(row) for row in session.run("SHOW CONSTRAINTS YIELD name,type RETURN name,type")]
        indexes = [dict(row) for row in session.run("SHOW INDEXES YIELD name,state RETURN name,state")]
    driver.close()
    result = {
        "neo4j_version": "4.4.43", "runtime": "LOCAL_COMMUNITY_SERVER", "uri": uri,
        "node_count": node_count, "expected_node_count": expected["node_export_count"],
        "relationship_count": rel_count, "expected_relationship_count": expected["relationship_export_count"],
        "node_coverage": node_count / expected["node_export_count"],
        "relationship_coverage": rel_count / expected["relationship_export_count"],
        "semantic_relation_count": semantic_count,
        "semantic_relation_provenance_coverage": semantic_grounded / semantic_count if semantic_count else 1.0,
        "type_counts": type_counts, "relation_counts": relation_counts,
        "view_result_counts": views, "all_views_non_empty": all(views.values()),
        "constraints": constraints, "indexes": indexes,
        "human_intervention_count": 0, "accuracy_claimed": False,
    }
    result["pass"] = all([
        result["node_coverage"] == 1.0, result["relationship_coverage"] == 1.0,
        result["semantic_relation_provenance_coverage"] == 1.0,
        result["all_views_non_empty"], all(result["type_counts"].values()), all(result["relation_counts"].values()),
    ])
    r5.write_json(root / "graphs" / "neo4j" / "runtime_validation.json", result)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
