#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run a non-claimable CAPE-KG NCS-PCF crosswalk review smoke test."""

import argparse
import csv
import json
import sys
from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from evaluate_cape_crosswalk_review import FIELDNAMES, evaluate_rows  # noqa: E402
from import_cape_crosswalk_review import merge_rows, validate_rows  # noqa: E402


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_OUT_DIR = DEFAULT_EXP_DIR / "06_release/crosswalk_roundtrip_smoke"


def read_jsonl(path):
    rows = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in FIELDNAMES})


def as_int(value, default=999):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def select_source_groups(rows, source_group_count):
    groups = defaultdict(list)
    for row in rows:
        groups[str(row.get("source_id") or "")].append(row)

    selected = []
    selected_source_ids = []
    for source_id in sorted(groups):
        group = sorted(groups[source_id], key=lambda row: as_int(row.get("crosswalk_rank")))
        ranks = {as_int(row.get("crosswalk_rank")) for row in group}
        if not set(range(1, 11)).issubset(ranks):
            continue
        selected_source_ids.append(source_id)
        selected.extend([row for row in group if as_int(row.get("crosswalk_rank")) <= 10])
        if len(selected_source_ids) >= source_group_count:
            break
    return selected, selected_source_ids


def reviewed_row(row):
    out = deepcopy(row)
    rank = as_int(out.get("crosswalk_rank"))
    if rank == 1:
        out["expert_decision"] = "accepted"
        out["utility_grade"] = "3"
        out["explanation_quality_score"] = "5"
    else:
        out["expert_decision"] = "rejected"
        out["utility_grade"] = "0"
        out["explanation_quality_score"] = "3"
    out["review_status"] = "completed"
    out["reviewer_id"] = "crosswalk_roundtrip_smoke"
    out["comment"] = "Roundtrip smoke test row; not expert gold and not paper evidence."
    return out


def render_report(payload):
    lines = [
        "# CAPE-KG NCS-PCF Crosswalk Roundtrip Smoke Test",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Overall status: `{payload['overall_status']}`",
        f"Claim status: `{payload['claim_status']}`",
        "",
        "This is an engineering smoke test only. It uses copied crosswalk rows to verify import and evaluation mechanics; it is not expert review and must not be used as paper evidence.",
        "",
        "## Summary",
        "",
        f"- Source groups: {payload['selected_source_group_count']}",
        f"- Reviewed rows: {payload['reviewed_rows']}",
        f"- Import errors: {payload['import_error_count']}",
        f"- Import warnings: {payload['import_warning_count']}",
        f"- Metric rows: {payload['metric_rows']}",
        "",
        "## Metrics",
        "",
        "| candidates | source tasks | completed | pending | complete groups | Hit@1 | Hit@3 | Hit@5 | P@10 | MRR | nDCG@10 | utility | explanation quality | status |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in payload["metrics"]:
        lines.append(
            f"| {row['candidate_rows']} | {row['source_task_count']} | {row['completed_rows']} | "
            f"{row['pending_rows']} | {row['complete_source_groups']} | {row['hit_at_1']} | "
            f"{row['hit_at_3']} | {row['hit_at_5']} | {row['precision_at_10']} | "
            f"{row['mrr']} | {row['ndcg_at_10']} | {row['utility_grade_mean']} | "
            f"{row['explanation_quality_score_mean']} | {row['claim_status']} |"
        )
    lines += ["", "## Files", ""]
    for key, value in payload["files"].items():
        lines.append(f"- {key}: `{value}`")
    if payload["issues"]:
        lines += ["", "## Issues", ""]
        for item in payload["issues"]:
            lines.append(f"- [{item['level']}] {item['code']}: {item['message']}")
    lines.append("")
    return "\n".join(lines)


def run(args):
    exp_dir = Path(args.experiment_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    source_file = exp_dir / "01_data/crosswalk_review/crosswalk_review_items.jsonl"
    source_rows = read_jsonl(source_file)
    target_rows, source_ids = select_source_groups(source_rows, args.source_group_count)
    reviewed_rows = [reviewed_row(row) for row in target_rows]
    issues = []

    if len(source_ids) != args.source_group_count:
        issues.append(
            {
                "level": "error",
                "code": "insufficient_complete_source_groups",
                "message": f"Expected {args.source_group_count} complete source groups, got {len(source_ids)}.",
            }
        )

    errors, warnings = validate_rows(target_rows, reviewed_rows, allow_partial=False)
    merged_rows, import_summary = merge_rows(target_rows, reviewed_rows, allow_partial=False) if not errors else ([], {})
    for message in errors:
        issues.append({"level": "error", "code": "import_validation_error", "message": message})
    for message in warnings:
        issues.append({"level": "warning", "code": "import_validation_warning", "message": message})

    metrics = [evaluate_rows(merged_rows)] if merged_rows else []
    if not metrics:
        issues.append({"level": "error", "code": "no_metrics", "message": "No crosswalk smoke metrics were produced."})

    files = {
        "target": str(out_dir / "crosswalk_target.jsonl"),
        "reviewed": str(out_dir / "crosswalk_reviewed.jsonl"),
        "merged": str(out_dir / "crosswalk_merged.jsonl"),
        "import_report": str(out_dir / "crosswalk_import_report.json"),
        "metrics_csv": str(out_dir / "crosswalk_metrics_smoke.csv"),
        "metrics_json": str(out_dir / "crosswalk_metrics_smoke.json"),
        "summary": str(out_dir / "crosswalk_roundtrip_smoke_summary.json"),
        "report": str(out_dir / "crosswalk_roundtrip_smoke_report.md"),
    }
    import_report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "dry_run",
        "source_file": str(source_file),
        "target_rows": len(target_rows),
        "reviewed_rows": len(reviewed_rows),
        "selected_source_ids": source_ids,
        "errors": errors,
        "warnings": warnings,
        "summary": import_summary,
        "status": "validated_dry_run" if not errors else "failed_validation",
    }
    write_jsonl(files["target"], target_rows)
    write_jsonl(files["reviewed"], reviewed_rows)
    write_jsonl(files["merged"], merged_rows)
    write_json(files["import_report"], import_report)
    write_csv(files["metrics_csv"], metrics)
    write_json(files["metrics_json"], {"claim_status": "crosswalk_roundtrip_smoke_not_paper_evidence", "metrics": metrics})

    blocking_issues = [item for item in issues if item["level"] == "error"]
    overall_status = "FAIL" if blocking_issues else "PASS"
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "output_dir": str(out_dir),
        "overall_status": overall_status,
        "claim_status": "crosswalk_roundtrip_smoke_not_paper_evidence",
        "source_group_count": args.source_group_count,
        "selected_source_group_count": len(source_ids),
        "selected_source_ids": source_ids,
        "reviewed_rows": len(reviewed_rows),
        "import_error_count": len(errors),
        "import_warning_count": len(warnings),
        "metric_rows": len(metrics),
        "metrics": metrics,
        "issues": issues,
        "files": files,
    }
    write_json(files["summary"], payload)
    write_text(files["report"], render_report(payload))
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if overall_status != "PASS":
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--source-group-count", type=int, default=2)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
