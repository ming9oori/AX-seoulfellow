#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run a non-claimable CAPE-KG mapping review pipeline smoke test."""

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

from evaluate_cape_mapping_review import FIELDNAMES, evaluate_standard  # noqa: E402
from import_cape_mapping_review import merge_rows, validate_rows  # noqa: E402


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_OUT_DIR = DEFAULT_EXP_DIR / "06_release/mapping_roundtrip_smoke"


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


def group_key(row):
    return (str(row.get("standard") or ""), str(row.get("source_id") or ""))


def select_top5_groups(rows, groups_per_standard):
    groups = defaultdict(list)
    for row in rows:
        if int(row.get("rank") or 999) <= 5:
            groups[group_key(row)].append(row)

    selected = []
    by_standard = defaultdict(list)
    for key, group in sorted(groups.items()):
        if len(group) < 5:
            continue
        standard, _ = key
        if len(by_standard[standard]) >= groups_per_standard:
            continue
        group = sorted(group, key=lambda row: int(row.get("rank") or 999))[:5]
        by_standard[standard].append(group)
        selected.extend(group)
    return selected, by_standard


def reviewed_row(row):
    out = deepcopy(row)
    rank = int(out.get("rank") or 999)
    if rank == 1:
        out["expert_decision"] = "accepted"
        out["relevance_grade"] = "3"
        out["explanation_quality_score"] = "5"
    else:
        out["expert_decision"] = "rejected"
        out["relevance_grade"] = "0"
        out["explanation_quality_score"] = "3"
    out["review_status"] = "completed"
    out["reviewer_id"] = "roundtrip_smoke"
    out["comment"] = "Roundtrip smoke test row; not expert gold and not paper evidence."
    return out


def render_report(payload):
    lines = [
        "# CAPE-KG Mapping Roundtrip Smoke Test",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Overall status: `{payload['overall_status']}`",
        f"Claim status: `{payload['claim_status']}`",
        "",
        "This is an engineering smoke test only. It uses copied mapping rows to verify import and evaluation mechanics; it is not expert review and must not be used as paper evidence.",
        "",
        "## Summary",
        "",
        f"- Reviewed rows: {payload['reviewed_rows']}",
        f"- Import errors: {payload['import_error_count']}",
        f"- Import warnings: {payload['import_warning_count']}",
        f"- Metric rows: {payload['metric_rows']}",
        "",
        "## Metrics",
        "",
        "| standard | completed rows | pending rows | complete groups | Hit@1 | Hit@5 | P@5 | MRR | nDCG@10 | explanation quality | status |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in payload["metrics"]:
        lines.append(
            f"| {row['standard']} | {row['completed_rows']} | {row['pending_rows']} | "
            f"{row['complete_source_groups']} | {row['hit_at_1']} | {row['hit_at_5']} | "
            f"{row['precision_at_5']} | {row['mrr']} | {row['ndcg_at_10']} | "
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
    source_file = exp_dir / "01_data/mapping_review/mapping_review_items.jsonl"
    source_rows = read_jsonl(source_file)
    target_rows, selected_groups = select_top5_groups(source_rows, args.groups_per_standard)
    reviewed_rows = [reviewed_row(row) for row in target_rows]
    issues = []

    expected_standards = {"NCS", "PCF"}
    selected_standards = set(selected_groups)
    if selected_standards != expected_standards:
        issues.append(
            {
                "level": "error",
                "code": "missing_standard_group",
                "message": f"Expected groups for {sorted(expected_standards)}, got {sorted(selected_standards)}.",
            }
        )

    errors, warnings = validate_rows(target_rows, reviewed_rows, allow_partial=False)
    merged_rows, import_summary = merge_rows(target_rows, reviewed_rows, allow_partial=False) if not errors else ([], {})
    for message in errors:
        issues.append({"level": "error", "code": "import_validation_error", "message": message})
    for message in warnings:
        issues.append({"level": "warning", "code": "import_validation_warning", "message": message})

    by_standard = defaultdict(list)
    for row in merged_rows:
        by_standard[row.get("standard") or "unknown"].append(row)
    metrics = [evaluate_standard(standard, rows) for standard, rows in sorted(by_standard.items())]
    if not metrics:
        issues.append({"level": "error", "code": "no_metrics", "message": "No mapping smoke metrics were produced."})

    files = {
        "target": str(out_dir / "mapping_target.jsonl"),
        "reviewed": str(out_dir / "mapping_reviewed.jsonl"),
        "merged": str(out_dir / "mapping_merged.jsonl"),
        "import_report": str(out_dir / "mapping_import_report.json"),
        "metrics_csv": str(out_dir / "mapping_metrics_smoke.csv"),
        "metrics_json": str(out_dir / "mapping_metrics_smoke.json"),
        "summary": str(out_dir / "mapping_roundtrip_smoke_summary.json"),
        "report": str(out_dir / "mapping_roundtrip_smoke_report.md"),
    }
    import_report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "dry_run",
        "source_file": str(source_file),
        "target_rows": len(target_rows),
        "reviewed_rows": len(reviewed_rows),
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
    write_json(files["metrics_json"], {"claim_status": "mapping_roundtrip_smoke_not_paper_evidence", "metrics": metrics})

    blocking_issues = [item for item in issues if item["level"] == "error"]
    overall_status = "FAIL" if blocking_issues else "PASS"
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "output_dir": str(out_dir),
        "overall_status": overall_status,
        "claim_status": "mapping_roundtrip_smoke_not_paper_evidence",
        "groups_per_standard": args.groups_per_standard,
        "selected_group_count": sum(len(groups) for groups in selected_groups.values()),
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
    parser.add_argument("--groups-per-standard", type=int, default=1)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
