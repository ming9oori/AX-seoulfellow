#!/usr/bin/env python3
"""Audit the exact Neo4j snapshot used by an experiment.

The snapshot intentionally flattens a few graph patterns.  This program restores
those captured edges for counting purposes, while explicitly distinguishing
properties read from Neo4j from fields derived during snapshot export.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


VERSION = "neo4j-snapshot-audit-v1"
DERIVED_PROPERTIES = {"PCFProcess": {"computed_path", "computed_path_text"}}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit node, relationship, property, and connectivity coverage"
    )
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    return parser.parse_args()


def is_present(value: Any) -> bool:
    return value is not None and value != "" and value != [] and value != {}


def value_type(value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        if not value:
            return "list<empty>"
        return "list<" + ",".join(sorted({value_type(item) for item in value})) + ">"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def normalized_text(value: Any) -> str:
    return " ".join(unicodedata.normalize("NFKC", str(value or "")).lower().split())


def unique_properties(rows: Iterable[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    unique: dict[str, dict[str, Any]] = {}
    anonymous = 0
    raw_count = 0
    for row in rows:
        raw_count += 1
        properties = dict(row)
        identifier = str(properties.get("id") or "")
        if identifier:
            unique[identifier] = properties
        else:
            anonymous += 1
            unique[f"__anonymous_{anonymous}"] = properties
    return list(unique.values()), raw_count


def property_schema(
    label: str, rows: Sequence[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    keys = sorted({key for row in rows for key in row})
    output = []
    for key in keys:
        values = [row.get(key) for row in rows if is_present(row.get(key))]
        output.append(
            {
                "property": key,
                "origin": (
                    "snapshot_derived"
                    if key in DERIVED_PROPERTIES.get(label, set())
                    else "neo4j"
                ),
                "present": len(values),
                "total": len(rows),
                "coverage": len(values) / len(rows) if rows else None,
                "types": sorted({value_type(value) for value in values}),
            }
        )
    return output


def distribution(values: Sequence[int]) -> dict[str, float | int | None]:
    if not values:
        return {key: None for key in ("min", "median", "mean", "p95", "max")}
    ordered = sorted(values)
    p95_index = max(0, math.ceil(0.95 * len(ordered)) - 1)
    return {
        "min": min(ordered),
        "median": float(statistics.median(ordered)),
        "mean": float(statistics.fmean(ordered)),
        "p95": ordered[p95_index],
        "max": max(ordered),
    }


def count_values(rows: Sequence[Mapping[str, Any]], property_name: str) -> dict[str, int]:
    return dict(
        Counter(
            normalized_text(row.get(property_name)) or "missing" for row in rows
        ).most_common()
    )


def edge(
    relationship_type: str,
    source_label: str,
    source_id: Any,
    target_label: str,
    target_id: Any,
    properties: Mapping[str, Any] | None = None,
    *,
    properties_captured: bool,
) -> dict[str, Any]:
    return {
        "relationship_type": relationship_type,
        "source_label": source_label,
        "source_id": str(source_id or ""),
        "target_label": target_label,
        "target_id": str(target_id or ""),
        "properties": dict(properties or {}),
        "properties_captured": properties_captured,
    }


def captured_edges(snapshot: Mapping[str, Any]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in snapshot["pcf_child_of"]:
        output.append(
            edge(
                "CHILD_OF",
                "PCFProcess",
                row.get("child_id"),
                "PCFProcess",
                row.get("parent_id"),
                row.get("properties"),
                properties_captured=True,
            )
        )
    for row in snapshot["taskframes"]:
        taskframe_id = row["properties"].get("id")
        for alias in row.get("aliases", []):
            output.append(
                edge(
                    "HAS_ALIAS",
                    "TaskFrame",
                    taskframe_id,
                    "TaskFrameAlias",
                    alias.get("id"),
                    properties_captured=False,
                )
            )
    for row in snapshot["pcf_mappings"]:
        output.append(
            edge(
                str(row.get("relationship_type")),
                "TaskFrame",
                row.get("taskframe_id"),
                "PCFProcess",
                row.get("pcf_id"),
                row.get("properties"),
                properties_captured=True,
            )
        )
    for row in snapshot["taskmentions"]:
        mention_id = row["properties"].get("id")
        output.append(
            edge(
                "MEMBER_OF",
                "TaskMention",
                mention_id,
                "TaskFrame",
                row.get("taskframe_id"),
                properties_captured=False,
            )
        )
        for evidence_id in row.get("evidence_ids", []):
            output.append(
                edge(
                    "SUPPORTED_BY(TaskMention)",
                    "TaskMention",
                    mention_id,
                    "EvidenceSpan",
                    evidence_id,
                    properties_captured=False,
                )
            )
    for row in snapshot["facts"]:
        fact_id = row["properties"].get("id")
        for link in row.get("frame_links", []):
            output.append(
                edge(
                    str(link.get("relationship_type")),
                    "TaskFrame",
                    link.get("taskframe_id"),
                    "Fact",
                    fact_id,
                    link.get("properties"),
                    properties_captured=True,
                )
            )
        for link in row.get("taskmention_links", []):
            output.append(
                edge(
                    "RELATED_TO_TASK_MENTION",
                    "Fact",
                    fact_id,
                    "TaskMention",
                    link.get("taskmention_id"),
                    link.get("properties"),
                    properties_captured=True,
                )
            )
        for evidence_id in row.get("evidence_ids", []):
            output.append(
                edge(
                    "SUPPORTED_BY(Fact)",
                    "Fact",
                    fact_id,
                    "EvidenceSpan",
                    evidence_id,
                    properties_captured=False,
                )
            )
    for row in snapshot["evidence_spans"]:
        evidence_id = row["properties"].get("id")
        for section in row.get("sections", []):
            output.append(
                edge(
                    "HAS_EVIDENCE",
                    "Section",
                    section.get("id"),
                    "EvidenceSpan",
                    evidence_id,
                    properties_captured=False,
                )
            )
    for row in snapshot["taskframe_relations"]:
        output.append(
            edge(
                str(row.get("relationship_type")),
                "TaskFrame",
                row.get("source_id"),
                "TaskFrame",
                row.get("target_id"),
                row.get("properties"),
                properties_captured=True,
            )
        )
    return output


def relationship_summary(edges: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, bool], list[Mapping[str, Any]]] = defaultdict(list)
    for item in edges:
        key = (
            str(item["relationship_type"]),
            str(item["source_label"]),
            str(item["target_label"]),
            bool(item["properties_captured"]),
        )
        grouped[key].append(item)
    output = []
    for (relationship_type, source, target, properties_captured), rows in sorted(
        grouped.items()
    ):
        property_rows = [row["properties"] for row in rows]
        output.append(
            {
                "relationship_type": relationship_type,
                "source_label": source,
                "target_label": target,
                "count": len(rows),
                "relationship_properties_captured": properties_captured,
                "property_schema": (
                    property_schema(f"REL:{relationship_type}", property_rows)
                    if properties_captured
                    else []
                ),
            }
        )
    return output


def missing_reference_counts(
    edges: Sequence[Mapping[str, Any]], ids_by_label: Mapping[str, set[str]]
) -> dict[str, int]:
    missing_source = 0
    missing_target = 0
    blank_endpoint = 0
    for item in edges:
        source_id = str(item["source_id"])
        target_id = str(item["target_id"])
        if not source_id or not target_id:
            blank_endpoint += 1
        if source_id not in ids_by_label.get(str(item["source_label"]), set()):
            missing_source += 1
        if target_id not in ids_by_label.get(str(item["target_label"]), set()):
            missing_target += 1
    return {
        "blank_endpoint_edges": blank_endpoint,
        "missing_source_references": missing_source,
        "missing_target_references": missing_target,
    }


def markdown_report(audit: Mapping[str, Any]) -> str:
    lines = [
        "# Neo4j graph snapshot audit",
        "",
        f"- Audit version: `{audit['audit_version']}`",
        f"- Snapshot schema: `{audit['snapshot']['schema_version']}`",
        f"- Snapshot time (UTC): `{audit['snapshot']['created_at']}`",
        f"- Neo4j database: `{audit['snapshot']['database']}`",
        f"- Snapshot SHA-256: `{audit['snapshot']['sha256']}`",
        "",
        "> Counts describe the frozen experiment snapshot, not a live query at report-reading time. "
        "TaskFrameAlias and Section are captured as nested nodes. `computed_path` fields are "
        "derived by the exporter and are not original Neo4j properties.",
        "",
        "## Nodes",
        "",
        "| Label | Unique nodes | Captured rows/associations | Duplicate captured rows |",
        "|---|---:|---:|---:|",
    ]
    for item in audit["nodes"]:
        lines.append(
            f"| {item['label']} | {item['unique_count']} | {item['captured_count']} | "
            f"{item['captured_count'] - item['unique_count']} |"
        )
    lines.extend(
        [
            "",
            "## Relationships",
            "",
            "| Type | Direction | Count | Relationship properties in snapshot |",
            "|---|---|---:|---|",
        ]
    )
    for item in audit["relationships"]:
        captured = "yes" if item["relationship_properties_captured"] else "no"
        lines.append(
            f"| {item['relationship_type']} | {item['source_label']} → "
            f"{item['target_label']} | {item['count']} | {captured} |"
        )
    integrity = audit["integrity"]
    coverage = audit["coverage"]
    lines.extend(
        [
            "",
            "## Connectivity and integrity",
            "",
            f"- Blank edge endpoints: **{integrity['blank_endpoint_edges']}**",
            f"- Missing source references: **{integrity['missing_source_references']}**",
            f"- Missing target references: **{integrity['missing_target_references']}**",
            f"- PCF roots / detected ancestry cycles: **{coverage['pcf_root_count']} / "
            f"{coverage['pcf_cycle_count']}**",
            f"- TaskFrames mapped to PCF: **{coverage['mapped_taskframes']} / "
            f"{coverage['taskframe_count']}**",
            f"- PCF nodes directly mapped from TaskFrame: **{coverage['directly_mapped_pcf']} / "
            f"{coverage['pcf_count']}**",
            f"- Evidence referenced by a TaskMention: **{coverage['evidence_referenced_by_mention']} / "
            f"{coverage['evidence_count']}**",
            f"- Evidence referenced by a Fact: **{coverage['evidence_referenced_by_fact']} / "
            f"{coverage['evidence_count']}**",
            f"- Evidence referenced by either: **{coverage['evidence_referenced_by_either']} / "
            f"{coverage['evidence_count']}**",
            f"- Evidence not referenced by TaskMention or Fact: "
            f"**{coverage['evidence_unreferenced_by_mention_or_fact']}**",
            f"- TaskMentions without EvidenceSpan: **{coverage['taskmentions_without_evidence']}**",
            f"- Facts without EvidenceSpan: **{coverage['facts_without_evidence']}**",
            f"- Duplicate normalized EvidenceSpan text groups / extra nodes: "
            f"**{coverage['duplicate_evidence_text_groups']} / "
            f"{coverage['duplicate_evidence_extra_nodes']}**",
            "",
            "## Degree distributions",
            "",
            "| Measure | Min | Median | Mean | P95 | Max |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for name, values in audit["degree_distributions"].items():
        lines.append(
            f"| {name} | {values['min']} | {values['median']} | "
            f"{values['mean']:.2f} | {values['p95']} | {values['max']} |"
        )
    lines.extend(["", "## Node property coverage", ""])
    for item in audit["nodes"]:
        lines.extend(
            [
                f"### {item['label']}",
                "",
                "| Property | Origin | Present | Coverage | Types |",
                "|---|---|---:|---:|---|",
            ]
        )
        for prop in item["property_schema"]:
            coverage_value = (
                "-" if prop["coverage"] is None else f"{100 * prop['coverage']:.2f}%"
            )
            lines.append(
                f"| `{prop['property']}` | {prop['origin']} | {prop['present']} / "
                f"{prop['total']} | {coverage_value} | {', '.join(prop['types'])} |"
            )
        lines.append("")
    lines.extend(["## Captured relationship property coverage", ""])
    for item in audit["relationships"]:
        if not item["relationship_properties_captured"]:
            continue
        lines.extend(
            [
                f"### {item['relationship_type']} ({item['source_label']} → "
                f"{item['target_label']})",
                "",
                "| Property | Present | Coverage | Types |",
                "|---|---:|---:|---|",
            ]
        )
        for prop in item["property_schema"]:
            coverage_value = (
                "-" if prop["coverage"] is None else f"{100 * prop['coverage']:.2f}%"
            )
            lines.append(
                f"| `{prop['property']}` | {prop['present']} / {prop['total']} | "
                f"{coverage_value} | {', '.join(prop['types'])} |"
            )
        lines.append("")
    lines.extend(
        [
            "## Important snapshot limits",
            "",
            "- The export queries cover the graph patterns used by this experiment; they are not a "
            "generic dump of every possible Neo4j label or relationship.",
            "- Relationship properties for `HAS_ALIAS`, `MEMBER_OF`, both `SUPPORTED_BY` views, "
            "and `HAS_EVIDENCE` were not selected by the snapshot queries, so their schemas cannot "
            "be inferred from this artifact.",
            "- Re-run the live snapshot export before claiming these counts describe a later graph state.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    raw = args.snapshot.read_bytes()
    snapshot = json.loads(raw)
    required = {
        "pcf_processes",
        "pcf_child_of",
        "taskframes",
        "pcf_mappings",
        "taskmentions",
        "facts",
        "evidence_spans",
        "taskframe_relations",
    }
    missing = sorted(required - snapshot.keys())
    if missing:
        raise ValueError(f"Snapshot is missing required keys: {missing}")

    raw_nodes = {
        "PCFProcess": [row["properties"] for row in snapshot["pcf_processes"]],
        "TaskFrame": [row["properties"] for row in snapshot["taskframes"]],
        "TaskFrameAlias": [
            alias for row in snapshot["taskframes"] for alias in row.get("aliases", [])
        ],
        "TaskMention": [row["properties"] for row in snapshot["taskmentions"]],
        "Fact": [row["properties"] for row in snapshot["facts"]],
        "EvidenceSpan": [row["properties"] for row in snapshot["evidence_spans"]],
        "Section": [
            section
            for row in snapshot["evidence_spans"]
            for section in row.get("sections", [])
        ],
    }
    nodes: list[dict[str, Any]] = []
    properties_by_label: dict[str, list[dict[str, Any]]] = {}
    ids_by_label: dict[str, set[str]] = {}
    for label, raw_rows in raw_nodes.items():
        unique_rows, captured_count = unique_properties(raw_rows)
        properties_by_label[label] = unique_rows
        ids_by_label[label] = {
            str(row.get("id")) for row in unique_rows if row.get("id")
        }
        nodes.append(
            {
                "label": label,
                "unique_count": len(unique_rows),
                "captured_count": captured_count,
                "property_schema": property_schema(label, unique_rows),
            }
        )

    edges = captured_edges(snapshot)
    relationships = relationship_summary(edges)
    integrity = missing_reference_counts(edges, ids_by_label)

    pcf_ids = ids_by_label["PCFProcess"]
    parent_by_child = {
        str(row["child_id"]): str(row["parent_id"])
        for row in snapshot["pcf_child_of"]
    }
    cycle_nodes: set[str] = set()
    for start in pcf_ids:
        current = start
        path: set[str] = set()
        while current in parent_by_child:
            if current in path:
                cycle_nodes.add(current)
                break
            path.add(current)
            current = parent_by_child[current]

    mention_evidence = {
        str(evidence_id)
        for row in snapshot["taskmentions"]
        for evidence_id in row.get("evidence_ids", [])
    }
    fact_evidence = {
        str(evidence_id)
        for row in snapshot["facts"]
        for evidence_id in row.get("evidence_ids", [])
    }
    evidence_ids = ids_by_label["EvidenceSpan"]
    mapped_taskframes = {
        str(row["taskframe_id"]) for row in snapshot["pcf_mappings"]
    }
    mapped_pcf = {str(row["pcf_id"]) for row in snapshot["pcf_mappings"]}
    evidence_text_counts = Counter(
        normalized_text(row.get("name") or row.get("displayName"))
        for row in properties_by_label["EvidenceSpan"]
    )
    duplicate_groups = [count for text, count in evidence_text_counts.items() if text and count > 1]

    mention_by_tf = Counter(
        str(row.get("taskframe_id")) for row in snapshot["taskmentions"]
    )
    fact_by_tf = Counter(
        str(link.get("taskframe_id"))
        for row in snapshot["facts"]
        for link in row.get("frame_links", [])
    )
    aliases_by_tf = {
        str(row["properties"].get("id")): len(row.get("aliases", []))
        for row in snapshot["taskframes"]
    }
    pcf_mappings_by_tf = Counter(
        str(row.get("taskframe_id")) for row in snapshot["pcf_mappings"]
    )
    taskframe_ids = sorted(ids_by_label["TaskFrame"])
    degree_distributions = {
        "TaskMentions per TaskFrame": distribution(
            [mention_by_tf[value] for value in taskframe_ids]
        ),
        "Fact links per TaskFrame": distribution(
            [fact_by_tf[value] for value in taskframe_ids]
        ),
        "Aliases per TaskFrame": distribution(
            [aliases_by_tf.get(value, 0) for value in taskframe_ids]
        ),
        "PCF mappings per TaskFrame": distribution(
            [pcf_mappings_by_tf[value] for value in taskframe_ids]
        ),
        "Evidence per TaskMention": distribution(
            [len(row.get("evidence_ids", [])) for row in snapshot["taskmentions"]]
        ),
        "Evidence per Fact": distribution(
            [len(row.get("evidence_ids", [])) for row in snapshot["facts"]]
        ),
    }
    coverage = {
        "pcf_count": len(pcf_ids),
        "pcf_root_count": len(pcf_ids - set(parent_by_child)),
        "pcf_cycle_count": len(cycle_nodes),
        "taskframe_count": len(taskframe_ids),
        "mapped_taskframes": len(mapped_taskframes),
        "directly_mapped_pcf": len(mapped_pcf),
        "evidence_count": len(evidence_ids),
        "evidence_referenced_by_mention": len(evidence_ids & mention_evidence),
        "evidence_referenced_by_fact": len(evidence_ids & fact_evidence),
        "evidence_referenced_by_either": len(
            evidence_ids & (mention_evidence | fact_evidence)
        ),
        "evidence_unreferenced_by_mention_or_fact": len(
            evidence_ids - mention_evidence - fact_evidence
        ),
        "taskmentions_without_evidence": sum(
            not row.get("evidence_ids") for row in snapshot["taskmentions"]
        ),
        "facts_without_evidence": sum(
            not row.get("evidence_ids") for row in snapshot["facts"]
        ),
        "duplicate_evidence_text_groups": len(duplicate_groups),
        "duplicate_evidence_extra_nodes": sum(count - 1 for count in duplicate_groups),
        "document_count": len(
            {
                normalized_text(row.get("document_id"))
                for row in properties_by_label["EvidenceSpan"]
                if row.get("document_id")
            }
        ),
        "section_count": len(ids_by_label["Section"]),
        "page_count": len(
            {
                normalized_text(row.get("page"))
                for row in properties_by_label["EvidenceSpan"]
                if row.get("page")
            }
        ),
    }
    audit = {
        "audit_version": VERSION,
        "snapshot": {
            "path": str(args.snapshot),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "schema_version": snapshot.get("schema_version"),
            "created_at": snapshot.get("created_at"),
            "database": snapshot.get("database"),
            "transport": snapshot.get("transport"),
        },
        "nodes": nodes,
        "relationships": relationships,
        "integrity": integrity,
        "coverage": coverage,
        "degree_distributions": degree_distributions,
        "categorical_distributions": {
            "pcf_level": count_values(properties_by_label["PCFProcess"], "level"),
            "taskmention_quality_status": count_values(
                properties_by_label["TaskMention"], "quality_status"
            ),
            "fact_quality_status": count_values(
                properties_by_label["Fact"], "quality_status"
            ),
            "fact_knowledge_function": count_values(
                properties_by_label["Fact"], "knowledge_function"
            ),
            "alias_type": count_values(
                properties_by_label["TaskFrameAlias"], "alias_type"
            ),
        },
        "manifest_from_exporter": snapshot.get("manifest", {}),
        "limitations": [
            "Counts describe the frozen snapshot, not a live query at report-reading time.",
            "The exporter selects experiment-relevant graph patterns, not every possible label.",
            "Some relationship properties were not projected by the snapshot queries.",
            "PCF computed_path and computed_path_text are exporter-derived fields.",
        ],
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    args.output_md.write_text(markdown_report(audit), encoding="utf-8")
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")


if __name__ == "__main__":
    main()
