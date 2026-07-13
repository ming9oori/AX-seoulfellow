#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prepare and evaluate human-effort data for CAPE active review."""

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_CONDITION = "P_cape_kg_actual"
DEFAULT_ARM_BUDGET = 100
ALLOWED_HUMAN_DECISIONS = {"correct", "incorrect", "partial", "unsupported", "invalid", "unsure"}
CORRECTION_DECISIONS = {"incorrect", "partial", "unsupported", "invalid"}

TEMPLATE_FIELDS = [
    "review_item_id",
    "condition",
    "chunk_id",
    "subject",
    "predicate",
    "object",
    "evidence_anchor_ids",
    "confidence",
    "active_priority",
    "uncertainty_priority",
    "active_rank",
    "uncertainty_rank",
    "random_rank",
    "included_in_active",
    "included_in_uncertainty",
    "included_in_random",
    "silver_review_error_label",
    "silver_high_impact_error_label",
    "silver_error_reasons",
    "reviewer_id",
    "review_seconds",
    "decision",
    "corrected_error",
    "high_impact_correction",
    "evidence_issue",
    "schema_issue",
    "notes",
]

METRIC_FIELDS = [
    "arm",
    "budget",
    "assigned",
    "reviewed",
    "review_seconds",
    "review_hours",
    "corrected_errors",
    "high_impact_corrections",
    "corrections_per_hour",
    "high_impact_corrections_per_hour",
    "precision_corrected",
    "claim_status",
]

BRIEFING_FIELDS = [
    "review_order",
    "review_item_id",
    "chunk_id",
    "subject",
    "predicate",
    "object",
    "evidence_anchor_ids",
    "membership_bucket",
    "review_focus",
    "active_rank",
    "uncertainty_rank",
    "random_rank",
    "active_priority",
    "uncertainty_priority",
    "confidence",
    "silver_review_error_label",
    "silver_high_impact_error_label",
    "silver_error_reasons",
    "required_human_fields",
    "timing_instruction",
    "claim_status",
]


def read_csv(path):
    path = Path(path)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fieldnames):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def to_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def to_bool(value):
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "corrected", "high"}


def stable_score(value, salt="cape-active-review"):
    digest = hashlib.sha1(f"{salt}|{value}".encode("utf-8")).hexdigest()
    return int(digest[:12], 16)


def rank_rows(rows, key, reverse=True):
    ranked = sorted(rows, key=lambda row: (to_float(row.get(key)), row.get("review_item_id", "")), reverse=reverse)
    return {row.get("review_item_id"): index for index, row in enumerate(ranked, start=1)}


def random_ranks(rows):
    ranked = sorted(rows, key=lambda row: stable_score(row.get("review_item_id")))
    return {row.get("review_item_id"): index for index, row in enumerate(ranked, start=1)}


def build_template(queue_rows, condition, arm_budget):
    filtered = [row for row in queue_rows if row.get("condition") == condition]
    active_rank = rank_rows(filtered, "active_priority", reverse=True)
    uncertainty_rank = rank_rows(filtered, "uncertainty_priority", reverse=True)
    random_rank = random_ranks(filtered)
    selected_ids = {
        item_id
        for ranks in (active_rank, uncertainty_rank, random_rank)
        for item_id, rank in ranks.items()
        if rank <= arm_budget
    }
    by_id = {row.get("review_item_id"): row for row in filtered}
    rows = []
    for item_id in sorted(selected_ids, key=lambda rid: min(active_rank.get(rid, 10**9), uncertainty_rank.get(rid, 10**9), random_rank.get(rid, 10**9))):
        row = by_id[item_id]
        rows.append(
            {
                "review_item_id": item_id,
                "condition": row.get("condition"),
                "chunk_id": row.get("chunk_id"),
                "subject": row.get("subject"),
                "predicate": row.get("predicate"),
                "object": row.get("object"),
                "evidence_anchor_ids": row.get("evidence_anchor_ids"),
                "confidence": row.get("confidence"),
                "active_priority": row.get("active_priority"),
                "uncertainty_priority": row.get("uncertainty_priority"),
                "active_rank": active_rank.get(item_id, ""),
                "uncertainty_rank": uncertainty_rank.get(item_id, ""),
                "random_rank": random_rank.get(item_id, ""),
                "included_in_active": str(active_rank.get(item_id, 10**9) <= arm_budget).lower(),
                "included_in_uncertainty": str(uncertainty_rank.get(item_id, 10**9) <= arm_budget).lower(),
                "included_in_random": str(random_rank.get(item_id, 10**9) <= arm_budget).lower(),
                "silver_review_error_label": row.get("review_error_label"),
                "silver_high_impact_error_label": row.get("high_impact_error_label"),
                "silver_error_reasons": row.get("error_reasons"),
            }
        )
    return rows


def reviewed_decision(row):
    decision = str(row.get("decision") or "").strip().lower()
    return decision in CORRECTION_DECISIONS or to_bool(row.get("corrected_error"))


def is_reviewed(row):
    decision = str(row.get("decision") or "").strip().lower()
    reviewer_id = str(row.get("reviewer_id") or "").strip()
    return decision in ALLOWED_HUMAN_DECISIONS and bool(reviewer_id) and to_float(row.get("review_seconds")) > 0


def evaluate_reviewed(rows, arm_budget):
    metrics = []
    for arm, rank_key, include_key in [
        ("active_priority", "active_rank", "included_in_active"),
        ("uncertainty_only", "uncertainty_rank", "included_in_uncertainty"),
        ("random_control", "random_rank", "included_in_random"),
    ]:
        arm_rows = [
            row
            for row in rows
            if to_bool(row.get(include_key)) and int(to_float(row.get(rank_key), 10**9)) <= arm_budget
        ]
        reviewed = [row for row in arm_rows if is_reviewed(row)]
        seconds = sum(to_float(row.get("review_seconds")) for row in reviewed)
        corrected = sum(1 for row in reviewed if reviewed_decision(row))
        high_impact = sum(1 for row in reviewed if to_bool(row.get("high_impact_correction")))
        hours = seconds / 3600.0 if seconds > 0 else 0.0
        claim_status = "human_effort_evaluated" if reviewed and seconds > 0 else "pending_human_effort_timing"
        metrics.append(
            {
                "arm": arm,
                "budget": arm_budget,
                "assigned": len(arm_rows),
                "reviewed": len(reviewed),
                "review_seconds": round(seconds, 3),
                "review_hours": round(hours, 6),
                "corrected_errors": corrected,
                "high_impact_corrections": high_impact,
                "corrections_per_hour": round(corrected / hours, 6) if hours else None,
                "high_impact_corrections_per_hour": round(high_impact / hours, 6) if hours else None,
                "precision_corrected": round(corrected / len(reviewed), 6) if reviewed else None,
                "claim_status": claim_status,
            }
        )
    return metrics


def build_overlap_summary(rows):
    arm_specs = [
        ("active_priority", "included_in_active"),
        ("uncertainty_only", "included_in_uncertainty"),
        ("random_control", "included_in_random"),
    ]
    arm_sets = {
        arm: {row.get("review_item_id") for row in rows if to_bool(row.get(include_key))}
        for arm, include_key in arm_specs
    }
    all_ids = set().union(*arm_sets.values()) if arm_sets else set()
    total_assignments = sum(len(ids) for ids in arm_sets.values())
    pairwise = []
    for idx, (left, _) in enumerate(arm_specs):
        for right, _ in arm_specs[idx + 1 :]:
            pairwise.append(
                {
                    "left_arm": left,
                    "right_arm": right,
                    "overlap_rows": len(arm_sets[left] & arm_sets[right]),
                    "jaccard": round(len(arm_sets[left] & arm_sets[right]) / max(1, len(arm_sets[left] | arm_sets[right])), 6),
                }
            )
    buckets = {
        "active_only": 0,
        "uncertainty_only": 0,
        "random_only": 0,
        "active_and_uncertainty_only": 0,
        "active_and_random_only": 0,
        "uncertainty_and_random_only": 0,
        "all_three": 0,
    }
    high_impact_by_bucket = {key: 0 for key in buckets}
    error_by_bucket = {key: 0 for key in buckets}
    by_id = {row.get("review_item_id"): row for row in rows}
    for item_id in all_ids:
        membership = {arm for arm, ids in arm_sets.items() if item_id in ids}
        if membership == {"active_priority"}:
            bucket = "active_only"
        elif membership == {"uncertainty_only"}:
            bucket = "uncertainty_only"
        elif membership == {"random_control"}:
            bucket = "random_only"
        elif membership == {"active_priority", "uncertainty_only"}:
            bucket = "active_and_uncertainty_only"
        elif membership == {"active_priority", "random_control"}:
            bucket = "active_and_random_only"
        elif membership == {"uncertainty_only", "random_control"}:
            bucket = "uncertainty_and_random_only"
        else:
            bucket = "all_three"
        buckets[bucket] += 1
        row = by_id.get(item_id, {})
        if to_bool(row.get("silver_high_impact_error_label")):
            high_impact_by_bucket[bucket] += 1
        if to_bool(row.get("silver_review_error_label")):
            error_by_bucket[bucket] += 1
    return {
        "claim_status": "pool_design_diagnostic_not_human_effort_claim",
        "unique_review_rows": len(all_ids),
        "total_arm_assignments_before_pooling": total_assignments,
        "duplicate_assignments_removed_by_pooling": total_assignments - len(all_ids),
        "pooling_reduction_rate": round((total_assignments - len(all_ids)) / max(1, total_assignments), 6),
        "arm_counts": {arm: len(ids) for arm, ids in arm_sets.items()},
        "pairwise_overlap": pairwise,
        "membership_buckets": [
            {
                "bucket": bucket,
                "rows": count,
                "silver_error_rows": error_by_bucket[bucket],
                "silver_high_impact_error_rows": high_impact_by_bucket[bucket],
            }
            for bucket, count in buckets.items()
        ],
    }


def build_overlap_report(payload):
    summary = payload["overlap_summary"]
    lines = [
        "# CAPE-KG Active Review Pool Overlap Diagnostic",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Claim status: `{summary['claim_status']}`",
        "",
        "This report explains how the active-priority, uncertainty-only, and random-control review arms are pooled into one human-effort sheet.",
        "It is a design diagnostic only; human-review efficiency claims still require reviewer timing and adjudicated labels.",
        "",
        "## Pooling Summary",
        "",
        f"- Total arm assignments before pooling: {summary['total_arm_assignments_before_pooling']}",
        f"- Unique review rows after pooling: {summary['unique_review_rows']}",
        f"- Duplicate assignments removed: {summary['duplicate_assignments_removed_by_pooling']}",
        f"- Pooling reduction rate: {summary['pooling_reduction_rate']}",
        "",
        "## Arm Counts",
        "",
        "| arm | rows |",
        "|---|---:|",
    ]
    for arm, count in summary["arm_counts"].items():
        lines.append(f"| {arm} | {count} |")
    lines += [
        "",
        "## Pairwise Overlap",
        "",
        "| left arm | right arm | overlap rows | Jaccard |",
        "|---|---|---:|---:|",
    ]
    for row in summary["pairwise_overlap"]:
        lines.append(f"| {row['left_arm']} | {row['right_arm']} | {row['overlap_rows']} | {row['jaccard']} |")
    lines += [
        "",
        "## Membership Buckets",
        "",
        "| bucket | rows | silver error rows | silver high-impact rows |",
        "|---|---:|---:|---:|",
    ]
    for row in summary["membership_buckets"]:
        lines.append(
            f"| {row['bucket']} | {row['rows']} | {row['silver_error_rows']} | {row['silver_high_impact_error_rows']} |"
        )
    lines += [
        "",
        "## Claim Scope",
        "",
        "- The overlap counts describe assignment design, not model quality.",
        "- `silver_error_rows` and `silver_high_impact_error_rows` are proxy labels used only to prioritize review.",
        "- Final active-review efficiency requires the returned `active_review_human_effort.reviewed.csv` and adjudicated human-gold outcomes.",
        "",
    ]
    return "\n".join(lines)


def membership_bucket(row):
    active = to_bool(row.get("included_in_active"))
    uncertainty = to_bool(row.get("included_in_uncertainty"))
    random = to_bool(row.get("included_in_random"))
    if active and uncertainty and random:
        return "all_three"
    if active and uncertainty:
        return "active_and_uncertainty_only"
    if active and random:
        return "active_and_random_only"
    if uncertainty and random:
        return "uncertainty_and_random_only"
    if active:
        return "active_only"
    if uncertainty:
        return "uncertainty_only"
    if random:
        return "random_only"
    return "unassigned"


def review_focus(row):
    focus = []
    if to_bool(row.get("silver_high_impact_error_label")):
        focus.append("high-impact correction check")
    if to_bool(row.get("silver_review_error_label")):
        focus.append("candidate correctness check")
    reasons = str(row.get("silver_error_reasons") or "")
    if "evidence_not_in_silver_chunk" in reasons:
        focus.append("evidence grounding check")
    if "schema" in reasons:
        focus.append("schema issue check")
    if to_float(row.get("confidence")) < 0.4:
        focus.append("low-confidence check")
    if membership_bucket(row) == "random_only":
        focus.append("random-control baseline timing")
    return "; ".join(focus or ["standard review"])


def rank_value(row, key):
    value = to_float(row.get(key), 10**9)
    return value if value > 0 else 10**9


def build_effort_briefing_rows(template_rows):
    sorted_rows = sorted(
        template_rows,
        key=lambda row: (
            not to_bool(row.get("silver_high_impact_error_label")),
            not to_bool(row.get("silver_review_error_label")),
            min(rank_value(row, "active_rank"), rank_value(row, "uncertainty_rank"), rank_value(row, "random_rank")),
            -to_float(row.get("active_priority")),
            -to_float(row.get("uncertainty_priority")),
            row.get("review_item_id", ""),
        ),
    )
    rows = []
    for index, row in enumerate(sorted_rows, start=1):
        rows.append(
            {
                "review_order": index,
                "review_item_id": row.get("review_item_id"),
                "chunk_id": row.get("chunk_id"),
                "subject": row.get("subject"),
                "predicate": row.get("predicate"),
                "object": row.get("object"),
                "evidence_anchor_ids": row.get("evidence_anchor_ids"),
                "membership_bucket": membership_bucket(row),
                "review_focus": review_focus(row),
                "active_rank": row.get("active_rank"),
                "uncertainty_rank": row.get("uncertainty_rank"),
                "random_rank": row.get("random_rank"),
                "active_priority": row.get("active_priority"),
                "uncertainty_priority": row.get("uncertainty_priority"),
                "confidence": row.get("confidence"),
                "silver_review_error_label": row.get("silver_review_error_label"),
                "silver_high_impact_error_label": row.get("silver_high_impact_error_label"),
                "silver_error_reasons": row.get("silver_error_reasons"),
                "required_human_fields": "reviewer_id; review_seconds; decision; corrected_error; high_impact_correction",
                "timing_instruction": "Start timer before reading the row; stop after decision/comment is finalized.",
                "claim_status": "review_navigation_only_pending_human_effort",
            }
        )
    return rows


def summarize_effort_briefing(rows):
    summary = {}
    for row in rows:
        bucket = row.get("membership_bucket") or "unknown"
        item = summary.setdefault(
            bucket,
            {
                "membership_bucket": bucket,
                "rows": 0,
                "silver_error_rows": 0,
                "silver_high_impact_rows": 0,
                "evidence_focus_rows": 0,
            },
        )
        item["rows"] += 1
        if to_bool(row.get("silver_review_error_label")):
            item["silver_error_rows"] += 1
        if to_bool(row.get("silver_high_impact_error_label")):
            item["silver_high_impact_rows"] += 1
        if "evidence grounding check" in str(row.get("review_focus") or ""):
            item["evidence_focus_rows"] += 1
    return [summary[key] for key in sorted(summary)]


def md_escape(value):
    return str(value or "").replace("|", "/").replace("\n", " ")


def render_effort_briefing_report(payload, briefing_rows, summary_rows):
    lines = [
        "# CAPE-KG Active Review Human-Effort Briefing",
        "",
        f"Generated: {payload['generated_at_utc']}",
        "",
        "This briefing orders the pooled active-review effort sheet before human timing collection.",
        "It is a navigation aid only; it does not create a human-effort efficiency claim until the reviewed CSV is returned with timing and decisions.",
        "",
        "## Summary",
        "",
        f"- claim_status: `{payload['briefing_claim_status']}`",
        f"- condition: `{payload['condition']}`",
        f"- pooled rows: {payload['pooled_rows']}",
        f"- expected reviewed CSV: `{payload['expected_reviewed_csv']}`",
        f"- briefing CSV: `{payload['briefing_csv']}`",
        "",
        "## Required Reviewer Fields",
        "",
        "| field | rule |",
        "|---|---|",
        "| `reviewer_id` | same identifier across all reviewed rows |",
        "| `review_seconds` | positive elapsed seconds for the row |",
        "| `decision` | `correct`, `incorrect`, `partial`, `unsupported`, `invalid`, or `unsure` |",
        "| `corrected_error` | `true` when the reviewer changed or rejected the candidate |",
        "| `high_impact_correction` | `true` for evidence, schema, risk, gateway, or central task-flow corrections |",
        "",
        "## Membership Buckets",
        "",
        "| bucket | rows | silver error | high-impact | evidence focus |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in summary_rows:
        lines.append(
            f"| {row['membership_bucket']} | {row['rows']} | {row['silver_error_rows']} | {row['silver_high_impact_rows']} | {row['evidence_focus_rows']} |"
        )
    lines += [
        "",
        "## First 60 Review Rows",
        "",
        "| order | item | chunk | triple | bucket | focus |",
        "|---:|---|---|---|---|---|",
    ]
    for row in briefing_rows[:60]:
        triple = f"{row.get('subject')} / {row.get('predicate')} / {row.get('object')}"
        lines.append(
            f"| {row['review_order']} | `{row.get('review_item_id')}` | `{row.get('chunk_id')}` | {md_escape(triple)} | {row.get('membership_bucket')} | {md_escape(row.get('review_focus'))} |"
        )
    lines += [
        "",
        "## Claim Scope",
        "",
        "- This briefing uses silver/proxy labels only for review navigation.",
        "- Corrections/hour and high-impact/hour require `active_review_human_effort.reviewed.csv` with timing.",
        "- Paper-level active-review claims still require alignment to adjudicated human-gold outcomes.",
        "",
    ]
    return "\n".join(lines)


def build_report(payload):
    lines = [
        "# CAPE-KG Active Review Human-Effort Plan",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Claim status: `{payload['claim_status']}`",
        "",
        "This artifact prepares the human-effort evidence needed for the active-review efficiency claim. It does not create a claimable efficiency result until reviewers return timing and correction decisions.",
        "",
        "## Files",
        "",
        f"- Template CSV: `{payload['template_csv']}`",
        f"- Expected reviewed CSV: `{payload['expected_reviewed_csv']}`",
        f"- Metrics JSON: `{payload['metrics_json']}`",
        f"- Metrics CSV: `{payload['metrics_csv']}`",
        f"- Evaluation report: `{payload['report_file']}`",
        f"- Pool overlap JSON: `{payload['overlap_json']}`",
        f"- Pool overlap report: `{payload['overlap_report']}`",
        f"- Human-effort briefing: `{payload['briefing_md']}`",
        f"- Human-effort briefing CSV: `{payload['briefing_csv']}`",
        "",
        "## Review Instructions",
        "",
        "- Review each row once in the pooled sheet.",
        "- Fill `reviewer_id`, `review_seconds`, `decision`, `corrected_error`, and `high_impact_correction`.",
        "- Use `decision=correct`, `incorrect`, `partial`, `unsupported`, `invalid`, or `unsure`.",
        "- Mark `corrected_error=true` when the reviewer changed or rejected the candidate.",
        "- Mark `high_impact_correction=true` for evidence, schema, risk, gateway, or central task-flow corrections.",
        "- Save the completed file at the expected reviewed CSV path.",
        "",
        "## Current Assignment",
        "",
        f"- Condition: `{payload['condition']}`",
        f"- Arm budget: {payload['arm_budget']}",
        f"- Pooled rows: {payload['pooled_rows']}",
        f"- Active rows included: {payload['arm_counts'].get('active_priority')}",
        f"- Uncertainty rows included: {payload['arm_counts'].get('uncertainty_only')}",
        f"- Random-control rows included: {payload['arm_counts'].get('random_control')}",
        f"- Duplicate assignments removed by pooling: {payload['overlap_summary']['duplicate_assignments_removed_by_pooling']}",
        f"- Pooling reduction rate: {payload['overlap_summary']['pooling_reduction_rate']}",
        "",
        "## Human-Effort Metrics",
        "",
        "| arm | assigned | reviewed | seconds | corrected | high-impact | corrections/hour | high-impact/hour | status |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in payload.get("metrics", []):
        lines.append(
            f"| {row['arm']} | {row['assigned']} | {row['reviewed']} | {row['review_seconds']} | "
            f"{row['corrected_errors']} | {row['high_impact_corrections']} | "
            f"{row['corrections_per_hour']} | {row['high_impact_corrections_per_hour']} | {row['claim_status']} |"
        )
    lines += [
        "",
        "## Claim Scope",
        "",
        "- `ready_for_human_effort_collection`: template and evaluator are ready, but no reviewed timing file is present.",
        "- `pending_human_effort_timing`: reviewed decisions may be partial or missing review seconds.",
        "- `human_effort_evaluated`: reviewer timing and decisions are present, but paper claims still require adjudicated gold outcome alignment.",
        "",
    ]
    return "\n".join(lines)


def run(args):
    exp_dir = Path(args.experiment_dir)
    condition = args.condition
    arm_budget = args.arm_budget
    review_dir = exp_dir / "05_review"
    release_dir = exp_dir / "06_release"
    eval_dir = exp_dir / "04_evaluation"
    queue_csv = Path(args.queue_csv) if args.queue_csv else review_dir / f"actual_llm_active_review_queue_{condition}.csv"
    template_csv = review_dir / "active_review_human_effort_template.csv"
    reviewed_csv = Path(args.reviewed_csv) if args.reviewed_csv else review_dir / "active_review_human_effort.reviewed.csv"
    metrics_json = eval_dir / "active_review_human_effort_metrics.json"
    metrics_csv = eval_dir / "active_review_human_effort_metrics.csv"
    report_file = eval_dir / "active_review_human_effort_report.md"
    overlap_json = eval_dir / "active_review_pool_overlap_summary.json"
    overlap_report = eval_dir / "active_review_pool_overlap_report.md"
    plan_json = release_dir / "active_review_human_effort_plan.json"
    plan_md = release_dir / "active_review_human_effort_plan.md"
    briefing_json = release_dir / "active_review_human_effort_briefing.json"
    briefing_md = release_dir / "active_review_human_effort_briefing.md"
    briefing_csv = review_dir / "active_review_human_effort_briefing.csv"

    queue_rows = read_csv(queue_csv)
    template_rows = build_template(queue_rows, condition, arm_budget)
    write_csv(template_csv, template_rows, TEMPLATE_FIELDS)

    reviewed_rows = read_csv(reviewed_csv) if reviewed_csv.exists() else template_rows
    metrics = evaluate_reviewed(reviewed_rows, arm_budget)
    has_reviewed_file = reviewed_csv.exists()
    any_human_metric = any(row["claim_status"] == "human_effort_evaluated" for row in metrics)
    claim_status = (
        "human_effort_evaluated_pending_gold_alignment"
        if any_human_metric
        else "pending_human_effort_returns"
        if has_reviewed_file
        else "ready_for_human_effort_collection"
    )
    arm_counts = {
        "active_priority": sum(1 for row in template_rows if to_bool(row.get("included_in_active"))),
        "uncertainty_only": sum(1 for row in template_rows if to_bool(row.get("included_in_uncertainty"))),
        "random_control": sum(1 for row in template_rows if to_bool(row.get("included_in_random"))),
    }
    overlap_summary = build_overlap_summary(template_rows)
    briefing_rows = build_effort_briefing_rows(template_rows)
    briefing_summary = summarize_effort_briefing(briefing_rows)
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "condition": condition,
        "arm_budget": arm_budget,
        "queue_csv": str(queue_csv),
        "template_csv": str(template_csv),
        "expected_reviewed_csv": str(reviewed_csv),
        "reviewed_file_present": has_reviewed_file,
        "pooled_rows": len(template_rows),
        "arm_counts": arm_counts,
        "claim_status": claim_status,
        "metrics_json": str(metrics_json),
        "metrics_csv": str(metrics_csv),
        "report_file": str(report_file),
        "overlap_json": str(overlap_json),
        "overlap_report": str(overlap_report),
        "plan_json": str(plan_json),
        "plan_md": str(plan_md),
        "briefing_json": str(briefing_json),
        "briefing_md": str(briefing_md),
        "briefing_csv": str(briefing_csv),
        "briefing_claim_status": "review_navigation_only_pending_human_effort",
        "briefing_rows": len(briefing_rows),
        "metrics": metrics,
        "overlap_summary": overlap_summary,
        "briefing_summary": briefing_summary,
    }
    write_json(metrics_json, payload)
    write_csv(metrics_csv, metrics, METRIC_FIELDS)
    report = build_report(payload)
    write_text(report_file, report)
    write_json(overlap_json, {"generated_at_utc": payload["generated_at_utc"], **overlap_summary})
    write_text(overlap_report, build_overlap_report(payload))
    write_csv(briefing_csv, briefing_rows, BRIEFING_FIELDS)
    write_json(
        briefing_json,
        {
            "generated_at_utc": payload["generated_at_utc"],
            "experiment_dir": str(exp_dir),
            "condition": condition,
            "claim_status": "review_navigation_only_pending_human_effort",
            "pooled_rows": len(template_rows),
            "briefing_rows": len(briefing_rows),
            "briefing_csv": str(briefing_csv),
            "briefing_md": str(briefing_md),
            "expected_reviewed_csv": str(reviewed_csv),
            "summary_by_membership_bucket": briefing_summary,
        },
    )
    write_text(briefing_md, render_effort_briefing_report(payload, briefing_rows, briefing_summary))
    write_json(plan_json, payload)
    write_text(plan_md, report)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--condition", default=DEFAULT_CONDITION)
    parser.add_argument("--queue-csv", default="")
    parser.add_argument("--reviewed-csv", default="")
    parser.add_argument("--arm-budget", type=int, default=DEFAULT_ARM_BUDGET)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
