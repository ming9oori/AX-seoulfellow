#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a claim-safe feasibility report for the 500+ gold-item target."""

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_OUTPUTS_DIR = Path("outputs")
MIN_REQUIRED_CHUNKS = 100
MIN_REQUIRED_GOLD_ITEMS = 500


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path, rows, fieldnames):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def as_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def round4(value):
    return round(float(value), 4)


def fmt(value):
    if isinstance(value, float):
        return f"{value:.4f}"
    if value is True:
        return "yes"
    if value is False:
        return "no"
    if value is None:
        return ""
    return str(value)


def md_table(headers, rows):
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(fmt(cell) for cell in row) + " |")
    return "\n".join(lines)


def batch_rows(assignment_summary):
    rows = []
    cumulative_chunks = 0
    cumulative_candidate_edges = 0
    cumulative_active_review_items = 0
    cumulative_high_impact_chunks = 0

    for idx, batch in enumerate(assignment_summary.get("batches") or [], start=1):
        chunk_count = as_int(batch.get("chunk_count"))
        candidate_edges = as_int(batch.get("candidate_edges_total"))
        active_items = as_int(batch.get("active_review_items_total"))
        high_impact = as_int(batch.get("high_impact_chunks"))
        cumulative_chunks += chunk_count
        cumulative_candidate_edges += candidate_edges
        cumulative_active_review_items += active_items
        cumulative_high_impact_chunks += high_impact
        rows.append({
            "batch_order": idx,
            "batch_id": batch.get("batch_id"),
            "chunk_count": chunk_count,
            "candidate_edges": candidate_edges,
            "active_review_items": active_items,
            "high_impact_chunks": high_impact,
            "cumulative_chunks": cumulative_chunks,
            "cumulative_candidate_edges": cumulative_candidate_edges,
            "cumulative_active_review_items": cumulative_active_review_items,
            "cumulative_high_impact_chunks": cumulative_high_impact_chunks,
            "candidate_edges_per_chunk": round4(candidate_edges / chunk_count) if chunk_count else 0.0,
            "cumulative_candidate_edges_per_chunk": (
                round4(cumulative_candidate_edges / cumulative_chunks) if cumulative_chunks else 0.0
            ),
            "meets_500_candidate_proxy": cumulative_candidate_edges >= MIN_REQUIRED_GOLD_ITEMS,
            "meets_100_chunk_requirement": cumulative_chunks >= MIN_REQUIRED_CHUNKS,
            "meets_minimum_chunk_and_candidate_proxy": (
                cumulative_candidate_edges >= MIN_REQUIRED_GOLD_ITEMS
                and cumulative_chunks >= MIN_REQUIRED_CHUNKS
            ),
        })
    return rows


def build_payload(exp_dir, outputs_dir):
    exp_dir = Path(exp_dir)
    outputs_dir = Path(outputs_dir)
    release_dir = exp_dir / "06_release"
    review_dir = exp_dir / "05_review"

    assignment_path = release_dir / "annotation_batch_assignment_summary.json"
    coverage_path = release_dir / "gold_sampling_coverage_report.json"
    human_gold_path = exp_dir / "04_evaluation/human_gold_validation_summary.json"

    assignment = read_json(assignment_path, {}) or {}
    coverage = read_json(coverage_path, {}) or {}
    human_gold = read_json(human_gold_path, {}) or {}

    rows = batch_rows(assignment)
    assigned_chunks = as_int(assignment.get("assigned_chunks"))
    priority_candidate_edges = as_int(
        (coverage.get("coverage_summary") or {}).get("priority_100_candidate_edges"),
        as_int(assignment.get("candidate_edges_total")),
    )
    full_120_candidate_edges = as_int((coverage.get("coverage_summary") or {}).get("full_120_candidate_edges"))
    active_review_items = as_int(assignment.get("active_review_items_total"))
    high_impact_chunks = as_int(assignment.get("high_impact_chunks"))
    completed_chunks = as_int(human_gold.get("completed_adjudicated_chunks"))
    current_gold_items = as_int(human_gold.get("gold_item_count_for_readiness"))

    candidate_pool_sufficient = (
        assigned_chunks >= MIN_REQUIRED_CHUNKS
        and priority_candidate_edges >= MIN_REQUIRED_GOLD_ITEMS
    )
    human_gold_gate_satisfied = (
        completed_chunks >= MIN_REQUIRED_CHUNKS
        and current_gold_items >= MIN_REQUIRED_GOLD_ITEMS
    )
    first_proxy_batch = next(
        (row["batch_id"] for row in rows if row["meets_500_candidate_proxy"]),
        None,
    )
    minimum_ready_batch = next(
        (row["batch_id"] for row in rows if row["meets_minimum_chunk_and_candidate_proxy"]),
        None,
    )

    outputs = {
        "json": str(release_dir / "gold_item_feasibility_report.json"),
        "markdown": str(release_dir / "gold_item_feasibility_report.md"),
        "batch_csv": str(review_dir / "gold_item_feasibility_by_batch.csv"),
    }
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "outputs_dir": str(outputs_dir),
        "claim_status": "gold_item_feasibility_ready_pending_human_adjudication",
        "target": {
            "minimum_required_chunks": MIN_REQUIRED_CHUNKS,
            "minimum_required_gold_items": MIN_REQUIRED_GOLD_ITEMS,
            "required_gold_items_per_chunk_avg": round4(MIN_REQUIRED_GOLD_ITEMS / MIN_REQUIRED_CHUNKS),
        },
        "current_human_gold_status": {
            "completed_adjudicated_chunks": completed_chunks,
            "gold_item_count_for_readiness": current_gold_items,
            "claim_status": human_gold.get("claim_status"),
            "human_gold_gate_satisfied": human_gold_gate_satisfied,
        },
        "candidate_pool_summary": {
            "assigned_chunks": assigned_chunks,
            "candidate_edges_total": priority_candidate_edges,
            "full_120_candidate_edges": full_120_candidate_edges,
            "active_review_items_total": active_review_items,
            "high_impact_chunks": high_impact_chunks,
            "candidate_edges_per_required_gold_item": (
                round4(priority_candidate_edges / MIN_REQUIRED_GOLD_ITEMS)
                if MIN_REQUIRED_GOLD_ITEMS else 0.0
            ),
            "candidate_edges_per_assigned_chunk_avg": (
                round4(priority_candidate_edges / assigned_chunks)
                if assigned_chunks else 0.0
            ),
            "candidate_pool_sufficient_for_minimum_item_target": candidate_pool_sufficient,
            "first_batch_meeting_500_candidate_proxy": first_proxy_batch,
            "minimum_batch_meeting_100_chunks_and_500_candidate_proxy": minimum_ready_batch,
        },
        "batch_rows": rows,
        "claim_boundary": {
            "candidate_edges_are_not_gold_items": True,
            "not_claimable_until": (
                "two annotators complete the selected chunks, IAA is computed, "
                "adjudication is imported, and gold_item_count_for_readiness >= 500"
            ),
            "safe_interpretation": (
                "The priority-100 package has enough candidate-edge workload to support "
                "the 500-item target if human adjudication accepts enough node/edge/evidence "
                "items; the current adjudicated gold count remains zero."
            ),
        },
        "input_files": {
            "annotation_batch_assignment_summary": str(assignment_path),
            "gold_sampling_coverage_report": str(coverage_path),
            "human_gold_validation_summary": str(human_gold_path),
        },
        "outputs": outputs,
    }


def render_markdown(payload):
    target = payload["target"]
    current = payload["current_human_gold_status"]
    pool = payload["candidate_pool_summary"]
    boundary = payload["claim_boundary"]
    batch_md_rows = [
        [
            row["batch_order"],
            row["batch_id"],
            row["chunk_count"],
            row["candidate_edges"],
            row["cumulative_chunks"],
            row["cumulative_candidate_edges"],
            row["candidate_edges_per_chunk"],
            row["cumulative_candidate_edges_per_chunk"],
            row["meets_500_candidate_proxy"],
            row["meets_100_chunk_requirement"],
            row["meets_minimum_chunk_and_candidate_proxy"],
        ]
        for row in payload["batch_rows"]
    ]

    lines = [
        "# CAPE-KG Gold Item Feasibility Report",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Claim status: `{payload['claim_status']}`",
        "",
        "이 문서는 500개 이상 human-gold item 요건이 이미 충족되었다고 주장하지 않습니다. 현재 priority-100 검수 패키지의 candidate edge 풀이 최소 gold item 목표를 감당할 수 있는지 계산하는 pre-human feasibility artifact입니다.",
        "",
        "## Target and Current Human-Gold Status",
        "",
        md_table(
            ["Item", "Value"],
            [
                ["Minimum required chunks", target["minimum_required_chunks"]],
                ["Minimum required gold items", target["minimum_required_gold_items"]],
                ["Required gold items per chunk avg", target["required_gold_items_per_chunk_avg"]],
                ["Current completed adjudicated chunks", current["completed_adjudicated_chunks"]],
                ["Current gold item count for readiness", current["gold_item_count_for_readiness"]],
                ["Current human-gold claim status", f"`{current.get('claim_status')}`"],
                ["Human-gold gate satisfied", current["human_gold_gate_satisfied"]],
            ],
        ),
        "",
        "## Candidate Pool Feasibility",
        "",
        md_table(
            ["Item", "Value"],
            [
                ["Assigned priority chunks", pool["assigned_chunks"]],
                ["Priority-100 candidate edges", pool["candidate_edges_total"]],
                ["Full-120 candidate edges", pool["full_120_candidate_edges"]],
                ["Active-review items total", pool["active_review_items_total"]],
                ["High-impact chunks", pool["high_impact_chunks"]],
                ["Candidate edges per required gold item", pool["candidate_edges_per_required_gold_item"]],
                ["Candidate edges per assigned chunk avg", pool["candidate_edges_per_assigned_chunk_avg"]],
                ["Candidate pool sufficient for 500-item target", pool["candidate_pool_sufficient_for_minimum_item_target"]],
                ["First batch meeting 500-candidate proxy", pool["first_batch_meeting_500_candidate_proxy"]],
                ["Batch meeting both 100 chunks and 500-candidate proxy", pool["minimum_batch_meeting_100_chunks_and_500_candidate_proxy"]],
            ],
        ),
        "",
        "## Batch-Level Cumulative Feasibility",
        "",
        md_table(
            [
                "Order",
                "Batch",
                "Chunks",
                "Candidate edges",
                "Cum. chunks",
                "Cum. candidates",
                "Edges/chunk",
                "Cum. edges/chunk",
                "500 proxy",
                "100 chunks",
                "Both",
            ],
            batch_md_rows,
        ),
        "",
        "## Claim Boundary",
        "",
        f"- Candidate edges are not gold items: `{boundary['candidate_edges_are_not_gold_items']}`",
        f"- Not claimable until: `{boundary['not_claimable_until']}`",
        f"- Safe interpretation: {boundary['safe_interpretation']}",
        "",
        "## Input and Output Files",
        "",
        f"- Assignment summary: `{payload['input_files']['annotation_batch_assignment_summary']}`",
        f"- Gold sampling coverage: `{payload['input_files']['gold_sampling_coverage_report']}`",
        f"- Human-gold validation summary: `{payload['input_files']['human_gold_validation_summary']}`",
        f"- JSON: `{payload['outputs']['json']}`",
        f"- Batch CSV: `{payload['outputs']['batch_csv']}`",
        "",
    ]
    return "\n".join(lines)


def run(args):
    payload = build_payload(args.experiment_dir, args.outputs_dir)
    write_json(payload["outputs"]["json"], payload)
    write_text(payload["outputs"]["markdown"], render_markdown(payload))
    write_csv(
        payload["outputs"]["batch_csv"],
        payload["batch_rows"],
        [
            "batch_order",
            "batch_id",
            "chunk_count",
            "candidate_edges",
            "active_review_items",
            "high_impact_chunks",
            "cumulative_chunks",
            "cumulative_candidate_edges",
            "cumulative_active_review_items",
            "cumulative_high_impact_chunks",
            "candidate_edges_per_chunk",
            "cumulative_candidate_edges_per_chunk",
            "meets_500_candidate_proxy",
            "meets_100_chunk_requirement",
            "meets_minimum_chunk_and_candidate_proxy",
        ],
    )
    print(json.dumps(payload["outputs"], ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--outputs-dir", default=str(DEFAULT_OUTPUTS_DIR))
    run(parser.parse_args())


if __name__ == "__main__":
    main()
