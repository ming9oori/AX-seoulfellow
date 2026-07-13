#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate and safely import CAPE-KG mapping expert-review exports."""

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")

KEY_FIELDS = ["standard", "mapping_id", "source_id", "target_id", "rank"]
EDITABLE_FIELDS = [
    "expert_decision",
    "relevance_grade",
    "explanation_quality_score",
    "review_status",
    "reviewer_id",
    "comment",
]
POSITIVE_DECISIONS = {"accepted"}
NEGATIVE_DECISIONS = {"rejected"}
ALLOWED_DECISIONS = {"", "accepted", "rejected", "unsure"}
ALLOWED_GRADES = {"", "0", "1", "2", "3"}
ALLOWED_EXPLANATION_QUALITY = {"", "1", "2", "3", "4", "5"}
ALLOWED_STATUSES = {"pending_expert_review", "completed", "reviewed", "adjudicated", "final"}
COMPLETED_STATUSES = {"completed", "reviewed", "adjudicated", "final"}


def read_review_rows(path):
    path = Path(path)
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    if text[0] in "[{":
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = None
        if isinstance(data, dict):
            if isinstance(data.get("items"), list):
                return data["items"]
            if isinstance(data.get("rows"), list):
                return data["rows"]
            raise ValueError(f"{path} JSON object must contain an 'items' or 'rows' list")
        if isinstance(data, list):
            return data
        if data is not None:
            raise ValueError(f"{path} must be JSONL, a JSON array, or an object with items/rows")
    rows = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{lineno}: invalid JSON: {exc}") from exc
    return rows


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def key_for(row):
    return tuple(str(row.get(field, "")).strip() for field in KEY_FIELDS)


def display_key(key):
    return "|".join(key)


def norm_decision(value):
    value = str(value or "").strip().lower()
    aliases = {
        "accept": "accepted",
        "yes": "accepted",
        "y": "accepted",
        "true": "accepted",
        "reject": "rejected",
        "no": "rejected",
        "n": "rejected",
        "false": "rejected",
    }
    return aliases.get(value, value)


def normalize_row(row):
    normalized = dict(row)
    normalized["expert_decision"] = norm_decision(normalized.get("expert_decision"))
    normalized["relevance_grade"] = str(normalized.get("relevance_grade") or "").strip()
    normalized["explanation_quality_score"] = str(normalized.get("explanation_quality_score") or "").strip()
    normalized["review_status"] = str(normalized.get("review_status") or "").strip().lower()
    if not normalized["review_status"]:
        normalized["review_status"] = "pending_expert_review"
    normalized["reviewer_id"] = str(normalized.get("reviewer_id") or "").strip()
    normalized["comment"] = str(normalized.get("comment") or "").strip()

    decision = normalized["expert_decision"]
    grade = normalized["relevance_grade"]
    explanation_quality = normalized["explanation_quality_score"]
    if decision or grade or explanation_quality:
        normalized["review_status"] = "completed"
    elif normalized["review_status"] == "completed":
        normalized["review_status"] = "pending_expert_review"

    normalized["claim_status"] = (
        "expert_reviewed_pending_evaluation"
        if normalized["review_status"] in {"completed", "reviewed", "adjudicated", "final"}
        else "not_gold_until_expert_reviewed"
    )
    return normalized


def duplicate_keys(rows):
    counts = Counter(key_for(row) for row in rows)
    return [key for key, count in counts.items() if count > 1]


def is_review_substantive(decision, grade, explanation_quality):
    return bool(decision or grade or explanation_quality)


def validate_rows(original_rows, reviewed_rows, allow_partial):
    errors = []
    warnings = []
    original_by_key = {key_for(row): row for row in original_rows}
    reviewed_by_key = {}

    for key in duplicate_keys(original_rows):
        errors.append(f"original file has duplicate key: {display_key(key)}")
    for key in duplicate_keys(reviewed_rows):
        errors.append(f"reviewed file has duplicate key: {display_key(key)}")

    for idx, row in enumerate(reviewed_rows, start=1):
        key = key_for(row)
        if key not in original_by_key:
            errors.append(f"reviewed row {idx} has no matching original key: {display_key(key)}")
            continue
        reviewed_by_key[key] = row

        original = original_by_key[key]
        for field in KEY_FIELDS + ["source_label", "target_label", "target_type", "mapping_type"]:
            if field in row and str(row.get(field, "")).strip() != str(original.get(field, "")).strip():
                errors.append(
                    f"reviewed row {display_key(key)} changed immutable field {field!r}: "
                    f"{original.get(field)!r} -> {row.get(field)!r}"
                )

        decision = norm_decision(row.get("expert_decision"))
        grade = str(row.get("relevance_grade") or "").strip()
        explanation_quality = str(row.get("explanation_quality_score") or "").strip()
        status = str(row.get("review_status") or "").strip().lower() or "pending_expert_review"

        if decision not in ALLOWED_DECISIONS:
            errors.append(f"{display_key(key)} has invalid expert_decision={row.get('expert_decision')!r}")
        if grade not in ALLOWED_GRADES:
            errors.append(f"{display_key(key)} has invalid relevance_grade={row.get('relevance_grade')!r}")
        if explanation_quality not in ALLOWED_EXPLANATION_QUALITY:
            errors.append(
                f"{display_key(key)} has invalid explanation_quality_score={row.get('explanation_quality_score')!r}"
            )
        if status not in ALLOWED_STATUSES:
            errors.append(f"{display_key(key)} has invalid review_status={row.get('review_status')!r}")
        completed_like = status in COMPLETED_STATUSES or is_review_substantive(decision, grade, explanation_quality)
        if completed_like:
            if not decision:
                errors.append(f"{display_key(key)} is completed/reviewed but has empty expert_decision")
            if not grade:
                errors.append(f"{display_key(key)} is completed/reviewed but has empty relevance_grade")
            if not explanation_quality:
                errors.append(
                    f"{display_key(key)} is completed/reviewed but has empty explanation_quality_score"
                )
            if not str(row.get("reviewer_id") or "").strip():
                errors.append(f"{display_key(key)} is completed/reviewed but has empty reviewer_id")
        if status in COMPLETED_STATUSES and not is_review_substantive(decision, grade, explanation_quality):
            errors.append(f"{display_key(key)} is marked reviewed but has no decision, grade, or explanation score")
        if decision == "unsure" and grade in {"2", "3"}:
            errors.append(f"{display_key(key)} has unsure decision with positive grade {grade}")
        if decision == "unsure" and not str(row.get("comment") or "").strip():
            errors.append(f"{display_key(key)} has unsure decision but empty comment")
        if decision in POSITIVE_DECISIONS and grade in {"0", "1"}:
            errors.append(f"{display_key(key)} has accepted decision with low grade {grade}")
        if decision in POSITIVE_DECISIONS and not str(row.get("comment") or "").strip():
            errors.append(f"{display_key(key)} has accepted decision but empty comment")
        if decision in NEGATIVE_DECISIONS and grade in {"2", "3"}:
            errors.append(f"{display_key(key)} has rejected decision with positive grade {grade}")
        if completed_like and not str(row.get("comment") or "").strip():
            warnings.append(f"{display_key(key)} is completed/reviewed without a comment")

    if not allow_partial:
        missing = sorted(set(original_by_key) - set(reviewed_by_key))
        if missing:
            sample = ", ".join(display_key(key) for key in missing[:5])
            errors.append(f"reviewed file is missing {len(missing)} original rows; sample: {sample}")

    return errors, warnings


def merge_rows(original_rows, reviewed_rows, allow_partial):
    reviewed_by_key = {key_for(row): normalize_row(row) for row in reviewed_rows}
    merged = []
    changed_rows = 0
    completed_rows = 0
    decision_counts = Counter()
    grade_counts = Counter()
    explanation_quality_counts = Counter()
    by_standard = defaultdict(Counter)

    for original in original_rows:
        key = key_for(original)
        row = dict(original)
        reviewed = reviewed_by_key.get(key)
        if reviewed is not None:
            before = {field: row.get(field, "") for field in EDITABLE_FIELDS}
            for field in EDITABLE_FIELDS:
                row[field] = reviewed.get(field, "")
            row["claim_status"] = reviewed.get("claim_status", row.get("claim_status", ""))
            if before != {field: row.get(field, "") for field in EDITABLE_FIELDS}:
                changed_rows += 1
        elif not allow_partial:
            raise AssertionError("missing rows should have been rejected before merge")

        decision = str(row.get("expert_decision") or "").strip().lower()
        grade = str(row.get("relevance_grade") or "").strip()
        explanation_quality = str(row.get("explanation_quality_score") or "").strip()
        status = str(row.get("review_status") or "").strip().lower()
        if status in {"completed", "reviewed", "adjudicated", "final"} or decision or grade or explanation_quality:
            completed_rows += 1
        decision_counts[decision or "blank"] += 1
        grade_counts[grade or "blank"] += 1
        explanation_quality_counts[explanation_quality or "blank"] += 1
        by_standard[str(row.get("standard") or "unknown")][status or "blank"] += 1
        merged.append(row)

    return merged, {
        "changed_rows": changed_rows,
        "completed_rows": completed_rows,
        "pending_rows": len(merged) - completed_rows,
        "decision_counts": dict(sorted(decision_counts.items())),
        "grade_counts": dict(sorted(grade_counts.items())),
        "explanation_quality_counts": dict(sorted(explanation_quality_counts.items())),
        "status_counts_by_standard": {standard: dict(counter) for standard, counter in sorted(by_standard.items())},
    }


def backup_file(path, backup_dir):
    path = Path(path)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_dir = Path(backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"{path.stem}.{timestamp}{path.suffix}"
    backup_path.write_bytes(path.read_bytes())
    return backup_path


def run(args):
    exp_dir = Path(args.experiment_dir)
    target_file = Path(args.target_file) if args.target_file else exp_dir / "01_data/mapping_review/mapping_review_items.jsonl"
    reviewed_file = Path(args.reviewed_file)
    report_file = Path(args.report_file) if args.report_file else exp_dir / "01_data/mapping_review/mapping_review_import_report.json"

    original_rows = read_review_rows(target_file)
    reviewed_rows = read_review_rows(reviewed_file)
    errors, warnings = validate_rows(original_rows, reviewed_rows, args.allow_partial)
    merged_rows, summary = merge_rows(original_rows, reviewed_rows, args.allow_partial) if not errors else ([], {})

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "apply" if args.apply else "dry_run",
        "experiment_dir": str(exp_dir),
        "target_file": str(target_file),
        "reviewed_file": str(reviewed_file),
        "allow_partial": bool(args.allow_partial),
        "original_rows": len(original_rows),
        "reviewed_rows": len(reviewed_rows),
        "errors": errors,
        "warnings": warnings,
        "summary": summary,
        "status": "failed_validation" if errors else ("applied" if args.apply else "validated_dry_run"),
    }

    if errors:
        write_json(report_file, payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        raise SystemExit(2)

    if args.apply:
        backup_path = backup_file(target_file, args.backup_dir or target_file.parent / "backups")
        write_jsonl(target_file, merged_rows)
        payload["backup_file"] = str(backup_path)

    write_json(report_file, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--reviewed-file", required=True)
    parser.add_argument("--target-file", default="")
    parser.add_argument("--report-file", default="")
    parser.add_argument("--backup-dir", default="")
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
