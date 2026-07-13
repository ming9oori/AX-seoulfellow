#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate optional structural-review return CSV files for CAPE-KG."""

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")

CHECKPOINT_ALLOWED = {
    "accept_review_checkpoint",
    "keep_current_type",
    "merge_with_existing_review",
    "reject_candidate",
    "needs_discussion",
}
GATEWAY_ALLOWED = {
    "add_branches_to",
    "keep_gateway_without_branch",
    "split_gateway",
    "reject_gateway",
    "needs_discussion",
}

REQUIRED_COMMON_FIELDS = {"gap_type", "recommended_action", "human_decision", "human_notes"}


def read_csv(path):
    path = Path(path)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def rel(path):
    return str(Path(path).as_posix())


def reviewed_path(path):
    path = Path(path)
    return path.with_name(f"{path.stem}.reviewed{path.suffix}")


def fieldnames_for(path):
    path = Path(path)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or [])


def key_for(row, key_field):
    return str(row.get(key_field) or "").strip()


def validate_file(input_file, reviewed_file, key_field, allowed_decisions, task_type):
    input_rows = read_csv(input_file)
    reviewed_rows = read_csv(reviewed_file)
    input_keys = [key_for(row, key_field) for row in input_rows]
    reviewed_keys = [key_for(row, key_field) for row in reviewed_rows]
    errors = []
    warnings = []

    summary = {
        "task_type": task_type,
        "input_file": rel(input_file),
        "reviewed_file": rel(reviewed_file),
        "present": reviewed_file.exists(),
        "status": "missing_reviewed_file",
        "expected_rows": len(input_rows),
        "reviewed_rows": 0,
        "completed_rows": 0,
        "decision_counts": {},
        "error_count": 0,
        "warning_count": 0,
        "errors": [],
        "warnings": [],
    }

    if not input_file.exists():
        errors.append({"code": "missing_input_file", "path": rel(input_file)})
        summary["status"] = "missing_input_file"
        summary["errors"] = errors
        summary["error_count"] = len(errors)
        return summary

    if not reviewed_file.exists():
        return summary

    summary["reviewed_rows"] = len(reviewed_rows)
    input_fieldnames = set(fieldnames_for(input_file))
    reviewed_fieldnames = set(fieldnames_for(reviewed_file))
    missing_fields = sorted((input_fieldnames | REQUIRED_COMMON_FIELDS | {key_field}) - reviewed_fieldnames)
    if missing_fields:
        errors.append({"code": "missing_required_fields", "fields": missing_fields})

    if len(reviewed_rows) != len(input_rows):
        errors.append(
            {
                "code": "row_count_mismatch",
                "expected_rows": len(input_rows),
                "reviewed_rows": len(reviewed_rows),
            }
        )

    duplicate_reviewed = sorted(key for key, count in Counter(reviewed_keys).items() if key and count > 1)
    if duplicate_reviewed:
        errors.append({"code": "duplicate_reviewed_keys", "sample": duplicate_reviewed[:20]})

    missing_keys = sorted(set(input_keys) - set(reviewed_keys))
    extra_keys = sorted(set(reviewed_keys) - set(input_keys))
    if missing_keys:
        errors.append({"code": "missing_input_keys", "sample": missing_keys[:20], "count": len(missing_keys)})
    if extra_keys:
        errors.append({"code": "extra_reviewed_keys", "sample": extra_keys[:20], "count": len(extra_keys)})

    decision_counts = Counter()
    completed = 0
    for row in reviewed_rows:
        row_key = key_for(row, key_field)
        decision = str(row.get("human_decision") or "").strip()
        notes = str(row.get("human_notes") or "").strip()
        if not decision:
            errors.append({"code": "missing_human_decision", key_field: row_key})
            continue
        decision_counts[decision] += 1
        if decision not in allowed_decisions:
            errors.append(
                {
                    "code": "invalid_human_decision",
                    key_field: row_key,
                    "decision": decision,
                    "allowed": sorted(allowed_decisions),
                }
            )
            continue
        completed += 1
        if decision in {"accept_review_checkpoint", "add_branches_to", "split_gateway", "merge_with_existing_review", "needs_discussion"} and not notes:
            warnings.append({"code": "decision_without_notes", key_field: row_key, "decision": decision})

    summary["decision_counts"] = dict(sorted(decision_counts.items()))
    summary["completed_rows"] = completed
    summary["error_count"] = len(errors)
    summary["warning_count"] = len(warnings)
    summary["errors"] = errors[:100]
    summary["warnings"] = warnings[:100]
    if errors:
        summary["status"] = "failed_validation"
    elif completed == len(input_rows):
        summary["status"] = "validated"
    else:
        summary["status"] = "incomplete_review"
    return summary


def render_report(payload):
    lines = [
        "# CAPE-KG Structural Review Return Preflight",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Overall status: `{payload['overall_status']}`",
        f"Claim status: `{payload['claim_status']}`",
        "",
        "This preflight validates optional structural-review return CSV files. Missing optional files are treated as pending, not as submission blockers.",
        "",
        "## Summary",
        "",
        "| Item | Value |",
        "|---|---:|",
        f"| Expected optional files | {payload['expected_files']} |",
        f"| Present optional files | {payload['present_files']} |",
        f"| Valid optional files | {payload['valid_files']} |",
        f"| Total errors | {payload['error_count']} |",
        f"| Total warnings | {payload['warning_count']} |",
        "",
        "## Files",
        "",
        "| task_type | expected | reviewed | completed | status | errors | warnings |",
        "|---|---:|---:|---:|---|---:|---:|",
    ]
    for row in payload["files"]:
        lines.append(
            f"| {row['task_type']} | {row['expected_rows']} | {row['reviewed_rows']} | "
            f"{row['completed_rows']} | {row['status']} | {row['error_count']} | {row['warning_count']} |"
        )
    if payload["errors"]:
        lines += ["", "## Errors", ""]
        for item in payload["errors"][:30]:
            lines.append(f"- `{item.get('task_type')}` {item.get('code')}: {json.dumps(item, ensure_ascii=False)}")
    if payload["warnings"]:
        lines += ["", "## Warnings", ""]
        for item in payload["warnings"][:30]:
            lines.append(f"- `{item.get('task_type')}` {item.get('code')}: {json.dumps(item, ensure_ascii=False)}")
    lines += [
        "",
        "## Interpretation",
        "",
        "- `pending_optional_returns`: no optional reviewed structural CSV has been returned yet.",
        "- `PASS`: reviewed structural CSV files that are present passed validation.",
        "- `FAIL`: at least one reviewed structural CSV is malformed and should not be used.",
        "",
    ]
    return "\n".join(lines)


def run(args):
    exp_dir = Path(args.experiment_dir)
    review_dir = exp_dir / "05_review"
    release_dir = exp_dir / "06_release"
    checkpoint_input = review_dir / "structural_review_checkpoint_candidates.csv"
    gateway_input = review_dir / "structural_gateway_branch_gaps.csv"
    files = [
        validate_file(
            checkpoint_input,
            reviewed_path(checkpoint_input),
            "node_id",
            CHECKPOINT_ALLOWED,
            "structural_review_checkpoint_candidates",
        ),
        validate_file(
            gateway_input,
            reviewed_path(gateway_input),
            "gateway_id",
            GATEWAY_ALLOWED,
            "structural_gateway_branch_gaps",
        ),
    ]
    errors = []
    warnings = []
    for file_summary in files:
        for item in file_summary.get("errors", []):
            errors.append({"task_type": file_summary["task_type"], **item})
        for item in file_summary.get("warnings", []):
            warnings.append({"task_type": file_summary["task_type"], **item})
    present_files = sum(1 for row in files if row.get("present"))
    valid_files = sum(1 for row in files if row.get("status") == "validated")
    if errors:
        overall_status = "FAIL"
    elif present_files == 0:
        overall_status = "pending_optional_returns"
    elif valid_files == present_files:
        overall_status = "PASS"
    else:
        overall_status = "partial_pending"
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "overall_status": overall_status,
        "claim_status": "optional_structural_review_preflight_not_paper_evidence",
        "expected_files": len(files),
        "present_files": present_files,
        "valid_files": valid_files,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "files": files,
        "errors": errors[:200],
        "warnings": warnings[:200],
        "outputs": {
            "json": str(release_dir / "structural_review_return_preflight.json"),
            "md": str(release_dir / "structural_review_return_preflight.md"),
        },
    }
    write_json(release_dir / "structural_review_return_preflight.json", payload)
    write_text(release_dir / "structural_review_return_preflight.md", render_report(payload))
    print(json.dumps({k: payload[k] for k in ["overall_status", "present_files", "valid_files", "error_count", "warning_count"]}, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
