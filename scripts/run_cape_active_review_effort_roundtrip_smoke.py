#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Non-claimable active-review effort CSV roundtrip smoke test."""

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from build_cape_active_review_human_effort import (
    METRIC_FIELDS,
    TEMPLATE_FIELDS,
    evaluate_reviewed,
    to_bool,
    write_csv,
    write_json,
    write_text,
)
from validate_cape_human_review_returns import validate_active_review_effort_return


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
CLAIM_STATUS = "active_review_effort_roundtrip_smoke_not_paper_evidence"


def read_csv(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def rank_value(row, key):
    try:
        value = int(float(row.get(key) or 10**9))
    except Exception:
        value = 10**9
    return value if value > 0 else 10**9


def select_smoke_rows(template_rows, per_arm=10, minimum=30):
    selected = {}
    arm_specs = [
        ("included_in_active", "active_rank"),
        ("included_in_uncertainty", "uncertainty_rank"),
        ("included_in_random", "random_rank"),
    ]
    for include_key, rank_key in arm_specs:
        ranked = sorted(
            [row for row in template_rows if to_bool(row.get(include_key))],
            key=lambda row: (rank_value(row, rank_key), row.get("review_item_id", "")),
        )
        for row in ranked[:per_arm]:
            selected[row.get("review_item_id")] = row

    if len(selected) < minimum:
        ranked_all = sorted(
            template_rows,
            key=lambda row: (
                min(rank_value(row, "active_rank"), rank_value(row, "uncertainty_rank"), rank_value(row, "random_rank")),
                row.get("review_item_id", ""),
            ),
        )
        for row in ranked_all:
            selected[row.get("review_item_id")] = row
            if len(selected) >= minimum:
                break

    return sorted(
        selected.values(),
        key=lambda row: (
            min(rank_value(row, "active_rank"), rank_value(row, "uncertainty_rank"), rank_value(row, "random_rank")),
            row.get("review_item_id", ""),
        ),
    )


def build_reviewed_rows(template_rows):
    rows = []
    for index, source in enumerate(template_rows, start=1):
        row = dict(source)
        if index % 5 == 0:
            decision = "incorrect"
            corrected = "true"
            high_impact = "true" if index % 10 == 0 else "false"
            evidence_issue = "true" if high_impact == "true" else "false"
            schema_issue = "true" if index % 15 == 0 else "false"
            notes = "roundtrip smoke correction"
        elif index % 7 == 0:
            decision = "partial"
            corrected = "true"
            high_impact = "false"
            evidence_issue = "false"
            schema_issue = "true"
            notes = "roundtrip smoke partial correction"
        else:
            decision = "correct"
            corrected = "false"
            high_impact = "false"
            evidence_issue = "false"
            schema_issue = "false"
            notes = "roundtrip smoke accepted"

        row.update(
            {
                "reviewer_id": "active_effort_roundtrip_smoke",
                "review_seconds": str(24 + (index % 11)),
                "decision": decision,
                "corrected_error": corrected,
                "high_impact_correction": high_impact,
                "evidence_issue": evidence_issue,
                "schema_issue": schema_issue,
                "notes": notes,
            }
        )
        rows.append(row)
    return rows


def render_report(summary):
    metrics = summary.get("metrics", [])
    lines = [
        "# CAPE-KG Active-Review Effort Roundtrip Smoke",
        "",
        f"Generated: {summary['generated_at_utc']}",
        f"Overall status: `{summary['overall_status']}`",
        f"Claim status: `{summary['claim_status']}`",
        "",
        "This is a synthetic engineering smoke test for the active-review human-effort CSV path.",
        "It is not paper evidence and must not be used as human-effort or model-quality evidence.",
        "",
        "## Summary",
        "",
        f"- selected rows: {summary['selected_rows']}",
        f"- reviewed rows: {summary['reviewed_rows']}",
        f"- validation status: `{summary['validation_status']}`",
        f"- validation errors: {summary['validation_error_count']}",
        f"- validation warnings: {summary['validation_warning_count']}",
        f"- ready for metric import: {summary['ready_for_effort_metric_import']}",
        "",
        "## Metrics",
        "",
        "| arm | assigned | reviewed | seconds | corrected | high-impact | status |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in metrics:
        lines.append(
            f"| {row.get('arm')} | {row.get('assigned')} | {row.get('reviewed')} | "
            f"{row.get('review_seconds')} | {row.get('corrected_errors')} | "
            f"{row.get('high_impact_corrections')} | {row.get('claim_status')} |"
        )
    lines += [
        "",
        "## Claim Scope",
        "",
        "- The reviewed CSV is synthetic and scoped only to roundtrip validation.",
        "- The real `active_review_human_effort.reviewed.csv` is still required before any human-effort claim.",
        "",
    ]
    return "\n".join(lines)


def run(args):
    exp_dir = Path(args.experiment_dir)
    review_dir = exp_dir / "05_review"
    release_dir = exp_dir / "06_release"
    smoke_dir = release_dir / "active_review_effort_roundtrip_smoke"
    fake_exp = smoke_dir / "validator_fixture_exp"
    fake_release = fake_exp / "06_release"
    fake_release.mkdir(parents=True, exist_ok=True)

    template_path = review_dir / "active_review_human_effort_template.csv"
    if not template_path.exists():
        raise FileNotFoundError(f"Missing active-review effort template: {template_path}")

    template_rows = read_csv(template_path)
    selected_rows = select_smoke_rows(template_rows, per_arm=args.per_arm, minimum=args.minimum_rows)
    if len(selected_rows) < args.minimum_rows:
        raise RuntimeError(f"Not enough active-review effort rows for smoke: {len(selected_rows)}")

    reviewed_rows = build_reviewed_rows(selected_rows)
    smoke_template = smoke_dir / "active_review_human_effort_template_smoke.csv"
    smoke_reviewed = smoke_dir / "active_review_human_effort.reviewed.smoke.csv"
    metrics_csv = smoke_dir / "active_review_effort_metrics_smoke.csv"
    metrics_json = smoke_dir / "active_review_effort_metrics_smoke.json"
    validation_json = smoke_dir / "active_review_effort_validation_smoke.json"
    summary_json = smoke_dir / "active_review_effort_roundtrip_smoke_summary.json"
    report_md = smoke_dir / "active_review_effort_roundtrip_smoke_report.md"
    fake_plan = fake_release / "active_review_human_effort_plan.json"

    write_csv(smoke_template, selected_rows, TEMPLATE_FIELDS)
    write_csv(smoke_reviewed, reviewed_rows, TEMPLATE_FIELDS)
    write_json(
        fake_plan,
        {
            "template_csv": str(smoke_template),
            "expected_reviewed_csv": str(smoke_reviewed),
            "metrics_json": str(metrics_json),
        },
    )

    validation = validate_active_review_effort_return(fake_exp)
    metrics = evaluate_reviewed(reviewed_rows, args.arm_budget)
    write_json(validation_json, validation)
    write_csv(metrics_csv, metrics, METRIC_FIELDS)
    write_json(
        metrics_json,
        {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "claim_status": CLAIM_STATUS,
            "metrics": metrics,
        },
    )

    issues = []
    if validation.get("status") != "validated":
        issues.append({"error": "validation_status_not_validated", "actual": validation.get("status")})
    if validation.get("error_count") != 0:
        issues.append({"error": "validation_errors_present", "actual": validation.get("error_count")})
    if validation.get("ready_for_effort_metric_import") is not True:
        issues.append({"error": "not_ready_for_effort_metric_import", "actual": validation.get("ready_for_effort_metric_import")})
    if len(metrics) != 3:
        issues.append({"error": "metric_rows_unexpected", "actual": len(metrics)})
    for row in metrics:
        if row.get("claim_status") != "human_effort_evaluated":
            issues.append({"error": "metric_claim_status_unexpected", "arm": row.get("arm"), "actual": row.get("claim_status")})
        if int(row.get("reviewed") or 0) <= 0:
            issues.append({"error": "metric_reviewed_rows_zero", "arm": row.get("arm")})

    overall_status = "PASS" if not issues else "FAIL"
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "overall_status": overall_status,
        "claim_status": CLAIM_STATUS,
        "experiment_dir": str(exp_dir),
        "smoke_dir": str(smoke_dir),
        "source_template": str(template_path),
        "template_smoke_csv": str(smoke_template),
        "reviewed_smoke_csv": str(smoke_reviewed),
        "validation_json": str(validation_json),
        "metrics_csv": str(metrics_csv),
        "metrics_json": str(metrics_json),
        "selected_rows": len(selected_rows),
        "reviewed_rows": len(reviewed_rows),
        "validation_status": validation.get("status"),
        "validation_error_count": validation.get("error_count"),
        "validation_warning_count": validation.get("warning_count"),
        "ready_for_effort_metric_import": validation.get("ready_for_effort_metric_import"),
        "completed_review_rows": validation.get("completed_review_rows"),
        "timed_review_rows": validation.get("timed_review_rows"),
        "metric_rows": len(metrics),
        "metrics": metrics,
        "issues": issues,
    }
    write_json(summary_json, summary)
    write_text(report_md, render_report(summary))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if issues:
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--per-arm", type=int, default=10)
    parser.add_argument("--minimum-rows", type=int, default=30)
    parser.add_argument("--arm-budget", type=int, default=100)
    run(parser.parse_args())


if __name__ == "__main__":
    main()
