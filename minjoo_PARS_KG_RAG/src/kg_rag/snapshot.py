from __future__ import annotations

import os
import random
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse

from dotenv import load_dotenv
from neo4j import GraphDatabase
import requests

from .common import normalize_text, utc_now, write_json


PCF_QUERY = """
MATCH (p:PCFProcess)
RETURN properties(p) AS properties
ORDER BY p.id
"""

PCF_EDGE_QUERY = """
MATCH (child:PCFProcess)-[r:CHILD_OF]->(parent:PCFProcess)
RETURN child.id AS child_id, parent.id AS parent_id, properties(r) AS properties
ORDER BY child.id, parent.id
"""

TASKFRAME_QUERY = """
MATCH (tf:TaskFrame)
OPTIONAL MATCH (tf)-[:HAS_ALIAS]->(alias:TaskFrameAlias)
RETURN properties(tf) AS properties,
       collect(DISTINCT properties(alias)) AS aliases
ORDER BY properties.id
"""

MAPPING_QUERY = """
MATCH (tf:TaskFrame)-[r]->(pcf:PCFProcess)
WHERE type(r) IN ['MAPS_TO_PCF', 'ALSO_MAPS_TO_PCF', 'HAS_PCF_CONTEXT']
RETURN tf.id AS taskframe_id,
       pcf.id AS pcf_id,
       type(r) AS relationship_type,
       properties(r) AS properties
ORDER BY tf.id, relationship_type, pcf.id
"""

TASKMENTION_QUERY = """
MATCH (tm:TaskMention)-[:MEMBER_OF]->(tf:TaskFrame)
OPTIONAL MATCH (tm)-[:SUPPORTED_BY]->(e:EvidenceSpan)
RETURN properties(tm) AS properties,
       tf.id AS taskframe_id,
       collect(DISTINCT e.id) AS evidence_ids
ORDER BY properties.id
"""

FACT_QUERY = """
MATCH (f:Fact)
OPTIONAL MATCH (tf:TaskFrame)-[fr]->(f)
WHERE type(fr) IN ['HAS_CORE_FACT', 'HAS_SUPPORTING_FACT', 'HAS_CONTEXT_FACT']
WITH f, collect(DISTINCT {
    taskframe_id: tf.id,
    relationship_type: type(fr),
    properties: properties(fr)
}) AS frame_links
OPTIONAL MATCH (f)-[tr:RELATED_TO_TASK_MENTION]->(tm:TaskMention)
WITH f, frame_links, collect(DISTINCT {
    taskmention_id: tm.id,
    properties: properties(tr)
}) AS taskmention_links
OPTIONAL MATCH (f)-[:SUPPORTED_BY]->(e:EvidenceSpan)
RETURN properties(f) AS properties,
       frame_links,
       taskmention_links,
       collect(DISTINCT e.id) AS evidence_ids
ORDER BY properties.id
"""

EVIDENCE_QUERY = """
MATCH (e:EvidenceSpan)
OPTIONAL MATCH (section:Section)-[:HAS_EVIDENCE]->(e)
RETURN properties(e) AS properties,
       collect(DISTINCT properties(section)) AS sections
ORDER BY properties.id
"""

TASKFRAME_RELATION_QUERY = """
MATCH (source:TaskFrame)-[r]->(target:TaskFrame)
WHERE type(r) IN ['PRECEDES', 'SUPPORTS', 'RELATED_TASK', 'SUBTASK_OF']
RETURN source.id AS source_id,
       target.id AS target_id,
       type(r) AS relationship_type,
       properties(r) AS properties
ORDER BY source.id, relationship_type, target.id
"""


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Required environment variable is missing: {name}")
    return value


def _rows(session: Any, query: str) -> list[dict[str, Any]]:
    return [dict(record) for record in session.run(query)]


class QueryAPIClient:
    """Minimal read-only Aura Query API client used when Bolt 7687 is unavailable."""

    def __init__(
        self,
        *,
        uri: str,
        username: str,
        password: str,
        database: str,
        connect_timeout: float,
        query_timeout: float,
        max_retries: int,
    ) -> None:
        parsed = urlparse(uri)
        if not parsed.hostname:
            raise ValueError(f"Invalid Neo4j URI: {uri!r}")
        self.url = (
            f"https://{parsed.hostname}/db/{quote(database, safe='')}/query/v2"
        )
        self.timeout = (connect_timeout, query_timeout)
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.auth = (username, password)
        self.session.headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "qpa-kg-rag-snapshot/1.0",
            }
        )

    def query(self, statement: str) -> list[dict[str, Any]]:
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.post(
                    self.url,
                    json={"statement": statement, "parameters": {}, "accessMode": "Read"},
                    timeout=self.timeout,
                )
                payload = response.json()
                errors = payload.get("errors") or []
                if errors:
                    first = errors[0]
                    raise RuntimeError(
                        f"{first.get('code', 'Neo4jError')}: {first.get('message', '')}"
                    )
                response.raise_for_status()
                data = payload.get("data") or {}
                fields = data.get("fields") or []
                values = data.get("values") or []
                return [dict(zip(fields, row, strict=True)) for row in values]
            except Exception as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
                time.sleep(min(30.0, 2**attempt + random.random()))
        assert last_error is not None
        raise last_error

    def close(self) -> None:
        self.session.close()


def _clean_links(rows: list[dict[str, Any]], key: str) -> None:
    for row in rows:
        row[key] = [
            item
            for item in row.get(key, [])
            if isinstance(item, dict)
            and any(value is not None for value in item.values())
        ]


def _add_pcf_paths(snapshot: dict[str, Any]) -> None:
    pcf_by_id = {
        row["properties"]["id"]: row["properties"]
        for row in snapshot["pcf_processes"]
    }
    parent_by_child: dict[str, str] = {}
    for edge in snapshot["pcf_child_of"]:
        parent_by_child[edge["child_id"]] = edge["parent_id"]

    for pcf_id, properties in pcf_by_id.items():
        path: list[dict[str, Any]] = []
        current = pcf_id
        seen: set[str] = set()
        while current and current not in seen and current in pcf_by_id:
            seen.add(current)
            node = pcf_by_id[current]
            path.append(
                {
                    "id": current,
                    "level": node.get("level"),
                    "code": node.get("code") or node.get("pcfid"),
                    "name": node.get("name"),
                }
            )
            current = parent_by_child.get(current, "")
        path.reverse()
        properties["computed_path"] = path
        properties["computed_path_text"] = " > ".join(
            normalize_text(item.get("name")) for item in path if item.get("name")
        )


def _build_manifest(snapshot: dict[str, Any]) -> dict[str, Any]:
    label_counts = {
        "PCFProcess": len(snapshot["pcf_processes"]),
        "TaskFrame": len(snapshot["taskframes"]),
        "TaskMention": len(snapshot["taskmentions"]),
        "Fact": len(snapshot["facts"]),
        "EvidenceSpan": len(snapshot["evidence_spans"]),
    }
    relationship_counts = Counter()
    relationship_counts["CHILD_OF"] = len(snapshot["pcf_child_of"])
    relationship_counts.update(
        row["relationship_type"] for row in snapshot["pcf_mappings"]
    )
    relationship_counts.update(
        row["relationship_type"] for row in snapshot["taskframe_relations"]
    )
    relationship_counts["MEMBER_OF"] = len(snapshot["taskmentions"])
    relationship_counts["SUPPORTED_BY(TaskMention)"] = sum(
        len(row.get("evidence_ids", [])) for row in snapshot["taskmentions"]
    )
    relationship_counts["SUPPORTED_BY(Fact)"] = sum(
        len(row.get("evidence_ids", [])) for row in snapshot["facts"]
    )
    for fact in snapshot["facts"]:
        relationship_counts.update(
            item["relationship_type"]
            for item in fact.get("frame_links", [])
            if item.get("relationship_type")
        )
        relationship_counts["RELATED_TO_TASK_MENTION"] += len(
            fact.get("taskmention_links", [])
        )

    mapped_pcf_ids = {row["pcf_id"] for row in snapshot["pcf_mappings"]}
    mapped_tf_ids = {row["taskframe_id"] for row in snapshot["pcf_mappings"]}
    return {
        "created_at": snapshot["created_at"],
        "database": snapshot["database"],
        "node_counts": label_counts,
        "relationship_counts": dict(sorted(relationship_counts.items())),
        "directly_mapped_pcf_count": len(mapped_pcf_ids),
        "mapped_taskframe_count": len(mapped_tf_ids),
        "pcf_levels": dict(
            sorted(
                Counter(
                    str(row["properties"].get("level"))
                    for row in snapshot["pcf_processes"]
                ).items()
            )
        ),
        "fact_knowledge_functions": dict(
            Counter(
                normalize_text(row["properties"].get("knowledge_function"))
                or "missing"
                for row in snapshot["facts"]
            ).most_common()
        ),
        "fact_quality_status": dict(
            Counter(
                normalize_text(row["properties"].get("quality_status")) or "missing"
                for row in snapshot["facts"]
            ).most_common()
        ),
    }


def export_snapshot(
    *,
    env_path: Path,
    output_path: Path,
    transport: str = "query_api",
    connect_timeout: float = 15.0,
    query_timeout: float = 120.0,
    max_retries: int = 5,
) -> dict[str, Any]:
    if not env_path.exists():
        raise FileNotFoundError(f"Neo4j env file not found: {env_path}")
    load_dotenv(env_path, override=False)
    uri = _required_env("NEO4J_URI")
    username = _required_env("NEO4J_USERNAME")
    password = _required_env("NEO4J_PASSWORD")
    database = _required_env("NEO4J_DATABASE")

    queries = {
        "pcf_processes": PCF_QUERY,
        "pcf_child_of": PCF_EDGE_QUERY,
        "taskframes": TASKFRAME_QUERY,
        "pcf_mappings": MAPPING_QUERY,
        "taskmentions": TASKMENTION_QUERY,
        "facts": FACT_QUERY,
        "evidence_spans": EVIDENCE_QUERY,
        "taskframe_relations": TASKFRAME_RELATION_QUERY,
    }
    snapshot: dict[str, Any] = {
        "schema_version": "qpa-graph-snapshot-v1",
        "created_at": utc_now(),
        "database": database,
        "transport": transport,
    }
    if transport == "query_api":
        client = QueryAPIClient(
            uri=uri,
            username=username,
            password=password,
            database=database,
            connect_timeout=connect_timeout,
            query_timeout=query_timeout,
            max_retries=max_retries,
        )
        try:
            if client.query("RETURN 1 AS connected") != [{"connected": 1}]:
                raise RuntimeError("Neo4j Query API verification returned an unexpected result")
            for key, query in queries.items():
                try:
                    snapshot[key] = client.query(query)
                except Exception as exc:
                    raise RuntimeError(f"Snapshot query failed at {key}: {exc}") from exc
        finally:
            client.close()
    elif transport == "driver":
        driver = GraphDatabase.driver(
            uri,
            auth=(username, password),
            connection_timeout=connect_timeout,
        )
        try:
            driver.verify_connectivity()
            with driver.session(database=database) as session:
                for key, query in queries.items():
                    snapshot[key] = _rows(session, query)
        finally:
            driver.close()
    else:
        raise ValueError(f"Unsupported Neo4j transport: {transport}")

    _clean_links(snapshot["facts"], "frame_links")
    _clean_links(snapshot["facts"], "taskmention_links")
    _add_pcf_paths(snapshot)
    snapshot["manifest"] = _build_manifest(snapshot)
    write_json(output_path, snapshot)
    return snapshot
