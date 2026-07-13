#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a claim-safe diagnostic report for alias/canonicalization coverage."""

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_OUTPUTS_DIR = Path("outputs")
CLAIM_STATUS = "alias_canonicalization_diagnostic_ready_pending_human_gold_node_matching"


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path):
    path = Path(path)
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path, rows, fieldnames):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def rel(path):
    return str(Path(path).as_posix())


def normalize_alias(value):
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def as_list(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def md_value(value):
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return f"{value:.6f}"
    if isinstance(value, list):
        return ", ".join(f"`{item}`" for item in value)
    if value is None:
        return ""
    return str(value).replace("|", "\\|")


def md_table(headers, rows):
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(md_value(row.get(header, "")) for header in headers) + " |")
    return "\n".join(lines)


def parse_graph_quality_alias_collisions(path):
    path = Path(path)
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"Alias collisions:\s*([0-9]+)", text)
    return int(match.group(1)) if match else None


def label_for_node(node):
    return node.get("label") or node.get("label_ko") or node.get("label_en") or node.get("node_id") or ""


def build_node_alias_summary(nodes):
    label_groups = defaultdict(list)
    nodes_with_aliases = 0
    raw_alias_total = 0
    unique_alias_total = 0
    duplicate_alias_within_node_total = 0
    node_rows = []
    for node in nodes:
        node_id = node.get("node_id") or ""
        label = label_for_node(node)
        node_type = node.get("type") or ""
        label_norm = normalize_alias(label)
        if label_norm:
            label_groups[label_norm].append(node_id)
        aliases = [alias for alias in as_list(node.get("aliases")) if str(alias or "").strip()]
        alias_norms = [normalize_alias(alias) for alias in aliases if normalize_alias(alias)]
        unique_alias_norms = sorted(set(alias_norms))
        if aliases:
            nodes_with_aliases += 1
        raw_alias_total += len(aliases)
        unique_alias_total += len(unique_alias_norms)
        duplicate_alias_within_node_total += len(alias_norms) - len(unique_alias_norms)
        if aliases:
            node_rows.append(
                {
                    "node_id": node_id,
                    "node_type": node_type,
                    "label": label,
                    "raw_alias_count": len(aliases),
                    "unique_normalized_alias_count": len(unique_alias_norms),
                    "duplicate_alias_within_node_count": len(alias_norms) - len(unique_alias_norms),
                }
            )

    duplicate_label_groups = {
        label: sorted(set(ids))
        for label, ids in label_groups.items()
        if len(set(ids)) > 1
    }
    return {
        "layer2_node_count": len(nodes),
        "nodes_with_aliases": nodes_with_aliases,
        "nodes_without_aliases": len(nodes) - nodes_with_aliases,
        "node_alias_coverage_rate": round(nodes_with_aliases / len(nodes), 6) if nodes else 0.0,
        "raw_node_alias_total": raw_alias_total,
        "unique_node_alias_total": unique_alias_total,
        "duplicate_alias_within_node_total": duplicate_alias_within_node_total,
        "duplicate_label_group_count": len(duplicate_label_groups),
        "duplicate_label_groups_sample": [
            {"normalized_label": label, "node_ids": ids}
            for label, ids in sorted(duplicate_label_groups.items())[:20]
        ],
        "nodes_with_aliases_sample": sorted(node_rows, key=lambda row: (-row["raw_alias_count"], row["node_id"]))[:20],
    }


def build_alias_dictionary_summary(alias_dict, nodes_by_id):
    collision_rows = []
    duplicate_reference_rows = []
    missing_reference_rows = []
    raw_reference_count = 0
    unique_reference_count = 0
    duplicate_reference_count = 0
    for alias, values in sorted((alias_dict or {}).items()):
        target_ids = [str(value) for value in as_list(values) if str(value or "").strip()]
        unique_target_ids = sorted(set(target_ids))
        raw_reference_count += len(target_ids)
        unique_reference_count += len(unique_target_ids)
        duplicate_count = len(target_ids) - len(unique_target_ids)
        duplicate_reference_count += duplicate_count
        missing_ids = [node_id for node_id in unique_target_ids if node_id not in nodes_by_id]
        if missing_ids:
            missing_reference_rows.append(
                {
                    "alias": alias,
                    "missing_node_ids": ",".join(missing_ids),
                    "missing_reference_count": len(missing_ids),
                }
            )
        if duplicate_count:
            duplicate_reference_rows.append(
                {
                    "alias": alias,
                    "raw_reference_count": len(target_ids),
                    "unique_reference_count": len(unique_target_ids),
                    "duplicate_reference_count": duplicate_count,
                    "node_ids": ",".join(unique_target_ids),
                }
            )
        if len(unique_target_ids) <= 1 and not duplicate_count:
            continue
        target_nodes = [nodes_by_id.get(node_id, {"node_id": node_id}) for node_id in unique_target_ids]
        node_types = sorted({node.get("type") or "" for node in target_nodes})
        labels = [label_for_node(node) for node in target_nodes]
        if len(unique_target_ids) <= 1:
            collision_kind = "duplicate_reference_only"
        elif len(set(node_types)) > 1:
            collision_kind = "cross_type_collision"
        else:
            collision_kind = "same_type_collision"
        collision_rows.append(
            {
                "alias": alias,
                "normalized_alias": normalize_alias(alias),
                "collision_kind": collision_kind,
                "target_count": len(unique_target_ids),
                "raw_reference_count": len(target_ids),
                "duplicate_reference_count": duplicate_count,
                "node_ids": ",".join(unique_target_ids),
                "node_types": ",".join(node_types),
                "labels": " || ".join(labels),
                "review_status": "pending_human_node_matching_review",
                "claim_status": CLAIM_STATUS,
            }
        )

    collision_kind_counts = Counter(row["collision_kind"] for row in collision_rows)
    ambiguous_collision_count = sum(
        1
        for row in collision_rows
        if row["collision_kind"] in {"cross_type_collision", "same_type_collision"}
    )
    return {
        "alias_entry_count": len(alias_dict or {}),
        "raw_alias_reference_count": raw_reference_count,
        "unique_alias_reference_count": unique_reference_count,
        "duplicate_alias_reference_count": duplicate_reference_count,
        "collision_alias_count": len(collision_rows),
        "ambiguous_collision_alias_count": ambiguous_collision_count,
        "duplicate_reference_only_group_count": collision_kind_counts.get("duplicate_reference_only", 0),
        "collision_kind_counts": dict(sorted(collision_kind_counts.items())),
        "missing_node_reference_count": sum(row["missing_reference_count"] for row in missing_reference_rows),
        "collision_rows": collision_rows,
        "duplicate_reference_rows": duplicate_reference_rows[:50],
        "missing_reference_rows": missing_reference_rows[:50],
    }


def build_canonical_task_summary(catalog, nodes_by_id):
    tasks = catalog.get("tasks") or catalog.get("canonical_tasks") or []
    task_ids = [task.get("task_id") or task.get("node_id") for task in tasks]
    task_ids = [task_id for task_id in task_ids if task_id]
    missing_task_ids = sorted(task_id for task_id in task_ids if task_id not in nodes_by_id)
    tasks_with_aliases = 0
    raw_task_alias_total = 0
    unique_task_alias_total = 0
    duplicate_alias_total = 0
    type_counts = Counter()
    for task in tasks:
        task_id = task.get("task_id") or task.get("node_id") or ""
        node = nodes_by_id.get(task_id) or {}
        type_counts[node.get("type") or "unknown"] += 1
        aliases = [alias for alias in as_list(task.get("aliases")) if str(alias or "").strip()]
        alias_norms = [normalize_alias(alias) for alias in aliases if normalize_alias(alias)]
        unique_alias_norms = sorted(set(alias_norms))
        if aliases:
            tasks_with_aliases += 1
        raw_task_alias_total += len(aliases)
        unique_task_alias_total += len(unique_alias_norms)
        duplicate_alias_total += len(alias_norms) - len(unique_alias_norms)
    return {
        "catalog_review_status": catalog.get("review_status"),
        "canonical_task_count": len(tasks),
        "canonical_tasks_with_aliases": tasks_with_aliases,
        "canonical_task_alias_coverage_rate": round(tasks_with_aliases / len(tasks), 6) if tasks else 0.0,
        "raw_canonical_task_alias_total": raw_task_alias_total,
        "unique_canonical_task_alias_total": unique_task_alias_total,
        "duplicate_canonical_task_alias_total": duplicate_alias_total,
        "canonical_task_ids_missing_from_layer2_nodes": missing_task_ids,
        "canonical_task_type_counts": dict(sorted(type_counts.items())),
    }


def build_edc_summary(path):
    rows = read_jsonl(path)
    condition_counts = Counter()
    node_counts = Counter()
    edge_counts = Counter()
    mapping_counts = Counter()
    triple_counts = Counter()
    for row in rows:
        condition = row.get("condition") or "unknown"
        condition_counts[condition] += 1
        node_counts[condition] += len(as_list(row.get("nodes")))
        edge_counts[condition] += len(as_list(row.get("edges")))
        mapping_counts[condition] += len(as_list(row.get("mappings")))
        triple_counts[condition] += len(as_list(row.get("triples")))
    return {
        "source_file": rel(path),
        "row_count": len(rows),
        "conditions": sorted(condition_counts),
        "condition_rows": [
            {
                "condition": condition,
                "rows": condition_counts[condition],
                "nodes": node_counts[condition],
                "edges": edge_counts[condition],
                "mappings": mapping_counts[condition],
                "triples": triple_counts[condition],
            }
            for condition in sorted(condition_counts)
        ],
    }


def build_payload(exp_dir, outputs_dir):
    exp_dir = Path(exp_dir)
    outputs_dir = Path(outputs_dir)
    nodes_path = outputs_dir / "07_layer2_graph/layer2_nodes.jsonl"
    edges_path = outputs_dir / "07_layer2_graph/layer2_edges.jsonl"
    alias_path = outputs_dir / "07_layer2_graph/layer2_alias_dictionary.json"
    quality_path = outputs_dir / "07_layer2_graph/layer2_graph_quality_report.md"
    catalog_path = outputs_dir / "04_task_frames/canonical_task_catalog.json"
    edc_path = exp_dir / "49_qwen3_8b_edc_schema_ablation_valid.jsonl"

    nodes = read_jsonl(nodes_path)
    edges = read_jsonl(edges_path)
    alias_dict = read_json(alias_path, {}) or {}
    catalog = read_json(catalog_path, {}) or {}
    nodes_by_id = {node.get("node_id"): node for node in nodes if node.get("node_id")}

    alias_summary = build_alias_dictionary_summary(alias_dict, nodes_by_id)
    node_summary = build_node_alias_summary(nodes)
    task_summary = build_canonical_task_summary(catalog, nodes_by_id)
    edc_summary = build_edc_summary(edc_path)
    graph_quality_collision_count = parse_graph_quality_alias_collisions(quality_path)

    collision_csv_path = exp_dir / "04_evaluation/alias_canonicalization_collision_groups.csv"
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "claim_status": CLAIM_STATUS,
        "experiment_dir": rel(exp_dir),
        "outputs_dir": rel(outputs_dir),
        "method_module": {
            "module_id": "M9",
            "name": "Alias/canonicalization module",
            "purpose": "Maintain canonical task labels, aliases, and comparable node labels.",
        },
        "claim_boundary": {
            "diagnostic_only": True,
            "human_gold_node_matching_required": True,
            "collision_review_required": True,
            "safe_interpretation": "This report documents automatic alias/canonicalization coverage and collision queues.",
            "not_claimable_until": "Final node canonicalization quality, precision, recall, and merge/split correctness require human-gold node matching and adjudicated review.",
        },
        "input_files": {
            "layer2_nodes": rel(nodes_path),
            "layer2_edges": rel(edges_path),
            "alias_dictionary": rel(alias_path),
            "layer2_graph_quality_report": rel(quality_path),
            "canonical_task_catalog": rel(catalog_path),
            "b3_edc_schema_ablation_valid": rel(edc_path),
        },
        "output_files": {
            "collision_groups_csv": rel(collision_csv_path),
            "json": rel(exp_dir / "06_release/alias_canonicalization_report.json"),
            "markdown": rel(exp_dir / "06_release/alias_canonicalization_report.md"),
        },
        "summary": {
            "layer2_node_count": len(nodes),
            "layer2_edge_count": len(edges),
            "canonical_task_count": task_summary["canonical_task_count"],
            "alias_entry_count": alias_summary["alias_entry_count"],
            "collision_alias_count": alias_summary["collision_alias_count"],
            "ambiguous_collision_alias_count": alias_summary["ambiguous_collision_alias_count"],
            "duplicate_reference_only_group_count": alias_summary["duplicate_reference_only_group_count"],
            "graph_quality_alias_collision_count": graph_quality_collision_count,
            "duplicate_alias_reference_count": alias_summary["duplicate_alias_reference_count"],
            "nodes_with_aliases": node_summary["nodes_with_aliases"],
            "node_alias_coverage_rate": node_summary["node_alias_coverage_rate"],
            "human_gold_node_matching_required": True,
            "claim_status": CLAIM_STATUS,
        },
        "node_alias_summary": node_summary,
        "alias_dictionary_summary": {
            key: value
            for key, value in alias_summary.items()
            if key not in {"collision_rows", "duplicate_reference_rows", "missing_reference_rows"}
        },
        "canonical_task_summary": task_summary,
        "b3_edc_style_baseline_summary": edc_summary,
        "collision_groups": alias_summary["collision_rows"],
        "duplicate_reference_sample": alias_summary["duplicate_reference_rows"],
        "missing_reference_sample": alias_summary["missing_reference_rows"],
    }
    return payload


def build_report(payload):
    summary = payload["summary"]
    node_summary = payload["node_alias_summary"]
    alias_summary = payload["alias_dictionary_summary"]
    task_summary = payload["canonical_task_summary"]
    collision_rows = payload["collision_groups"]
    edc_rows = payload["b3_edc_style_baseline_summary"]["condition_rows"]
    lines = [
        "# CAPE-KG Alias/Canonicalization Diagnostic Report",
        "",
        f"Generated: {payload['generated_at_utc']}",
        "",
        "This report documents the current M9 alias/canonicalization artifacts. It is a diagnostic artifact, not human-gold node matching evidence.",
        "",
        "## Claim Boundary",
        "",
        f"- Claim status: `{payload['claim_status']}`",
        "- Diagnostic only: automatic alias coverage and collision queue.",
        "- Pending human-gold node matching: final canonicalization precision, recall, and merge/split correctness are not yet claimable.",
        "- Collision review required: alias collisions are preserved as a review queue, not silently resolved.",
        "",
        "## Summary",
        "",
        md_table(
            ["metric", "value"],
            [
                {"metric": "Layer 2 nodes", "value": summary["layer2_node_count"]},
                {"metric": "Layer 2 edges", "value": summary["layer2_edge_count"]},
                {"metric": "Canonical task catalog entries", "value": summary["canonical_task_count"]},
                {"metric": "Alias dictionary entries", "value": summary["alias_entry_count"]},
                {"metric": "Alias collision groups", "value": summary["collision_alias_count"]},
                {"metric": "Ambiguous multi-node collision groups", "value": summary["ambiguous_collision_alias_count"]},
                {"metric": "Duplicate-reference-only groups", "value": summary["duplicate_reference_only_group_count"]},
                {"metric": "Graph quality collision count", "value": summary["graph_quality_alias_collision_count"]},
                {"metric": "Duplicate alias references", "value": summary["duplicate_alias_reference_count"]},
                {"metric": "Nodes with aliases", "value": summary["nodes_with_aliases"]},
                {"metric": "Node alias coverage rate", "value": summary["node_alias_coverage_rate"]},
            ],
        ),
        "",
        "## Node Alias Coverage",
        "",
        md_table(
            ["metric", "value"],
            [
                {"metric": "nodes_with_aliases", "value": node_summary["nodes_with_aliases"]},
                {"metric": "nodes_without_aliases", "value": node_summary["nodes_without_aliases"]},
                {"metric": "raw_node_alias_total", "value": node_summary["raw_node_alias_total"]},
                {"metric": "unique_node_alias_total", "value": node_summary["unique_node_alias_total"]},
                {"metric": "duplicate_alias_within_node_total", "value": node_summary["duplicate_alias_within_node_total"]},
                {"metric": "duplicate_label_group_count", "value": node_summary["duplicate_label_group_count"]},
            ],
        ),
        "",
        "## Canonical Task Catalog",
        "",
        md_table(
            ["metric", "value"],
            [
                {"metric": "catalog_review_status", "value": task_summary["catalog_review_status"]},
                {"metric": "canonical_task_count", "value": task_summary["canonical_task_count"]},
                {"metric": "canonical_tasks_with_aliases", "value": task_summary["canonical_tasks_with_aliases"]},
                {"metric": "canonical_task_alias_coverage_rate", "value": task_summary["canonical_task_alias_coverage_rate"]},
                {"metric": "raw_canonical_task_alias_total", "value": task_summary["raw_canonical_task_alias_total"]},
                {"metric": "unique_canonical_task_alias_total", "value": task_summary["unique_canonical_task_alias_total"]},
                {"metric": "missing_task_ids_from_layer2_nodes", "value": len(task_summary["canonical_task_ids_missing_from_layer2_nodes"])},
            ],
        ),
        "",
        "## Alias Dictionary Diagnostics",
        "",
        md_table(
            ["metric", "value"],
            [
                {"metric": "alias_entry_count", "value": alias_summary["alias_entry_count"]},
                {"metric": "raw_alias_reference_count", "value": alias_summary["raw_alias_reference_count"]},
                {"metric": "unique_alias_reference_count", "value": alias_summary["unique_alias_reference_count"]},
                {"metric": "duplicate_alias_reference_count", "value": alias_summary["duplicate_alias_reference_count"]},
                {"metric": "collision_alias_count", "value": alias_summary["collision_alias_count"]},
                {"metric": "ambiguous_collision_alias_count", "value": alias_summary["ambiguous_collision_alias_count"]},
                {"metric": "duplicate_reference_only_group_count", "value": alias_summary["duplicate_reference_only_group_count"]},
                {"metric": "missing_node_reference_count", "value": alias_summary["missing_node_reference_count"]},
            ],
        ),
        "",
        "## Collision Review Queue",
        "",
        f"Full CSV: `{payload['output_files']['collision_groups_csv']}`",
        "",
        md_table(
            ["alias", "collision_kind", "target_count", "node_types", "review_status"],
            collision_rows[:20],
        ),
        "",
        "## B3 EDC-Style Baseline Footprint",
        "",
        md_table(["condition", "rows", "nodes", "edges", "mappings", "triples"], edc_rows),
        "",
        "## Inputs",
        "",
    ]
    for label, path in payload["input_files"].items():
        lines.append(f"- `{label}`: `{path}`")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--outputs-dir", default=str(DEFAULT_OUTPUTS_DIR))
    args = parser.parse_args()

    exp_dir = Path(args.experiment_dir)
    payload = build_payload(exp_dir, Path(args.outputs_dir))
    release_dir = exp_dir / "06_release"
    json_path = release_dir / "alias_canonicalization_report.json"
    md_path = release_dir / "alias_canonicalization_report.md"
    csv_path = exp_dir / "04_evaluation/alias_canonicalization_collision_groups.csv"

    write_json(json_path, payload)
    write_text(md_path, build_report(payload))
    write_csv(
        csv_path,
        payload["collision_groups"],
        [
            "alias",
            "normalized_alias",
            "collision_kind",
            "target_count",
            "raw_reference_count",
            "duplicate_reference_count",
            "node_ids",
            "node_types",
            "labels",
            "review_status",
            "claim_status",
        ],
    )
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print(f"Wrote {csv_path}")


if __name__ == "__main__":
    main()
