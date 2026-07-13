#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Preflight returned human-review files before applying CAPE-KG imports."""

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from import_cape_gold_annotation import (
    key_for as annotation_key_for,
    load_chunk_context,
    load_schema,
    merge_rows as merge_annotation_rows,
    read_rows as read_annotation_rows,
    status_of as annotation_status_of,
    validate_import as validate_annotation_import,
)
from import_cape_mapping_review import (
    key_for as mapping_key_for,
    merge_rows as merge_mapping_rows,
    read_review_rows as read_mapping_review_rows,
    validate_rows as validate_mapping_rows,
)
from import_cape_crosswalk_review import (
    merge_rows as merge_crosswalk_rows,
    read_review_rows as read_crosswalk_review_rows,
    validate_rows as validate_crosswalk_rows,
)


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
COMPLETED_ANNOTATION_STATUSES = {"completed", "needs_adjudication"}
COMPLETED_ADJUDICATION_STATUSES = {
    "adjudicated",
    "completed",
    "complete",
    "final",
    "accepted",
    "no_disagreement_adjudicated",
}
COMPLETED_MAPPING_STATUSES = {"completed", "reviewed", "adjudicated", "final"}
ACTIVE_REVIEW_REQUIRED_FIELDS = {
    "review_item_id",
    "condition",
    "chunk_id",
    "included_in_active",
    "included_in_uncertainty",
    "included_in_random",
    "reviewer_id",
    "review_seconds",
    "decision",
    "corrected_error",
    "high_impact_correction",
}
ACTIVE_REVIEW_ALLOWED_DECISIONS = {"", "correct", "incorrect", "partial", "unsupported", "invalid", "unsure"}
ACTIVE_REVIEW_CORRECTION_DECISIONS = {"incorrect", "partial", "unsupported", "invalid"}
ACTIVE_REVIEW_ALLOWED_BOOL = {"", "0", "1", "true", "false", "yes", "no", "y", "n"}


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


def completed_annotation_chunks(rows):
    return {
        annotation_key_for(row)
        for row in rows
        if annotation_status_of(row).strip().lower() in COMPLETED_ANNOTATION_STATUSES
    }


def status_counts(rows, status_fn):
    counts = Counter()
    for row in rows:
        counts[status_fn(row) or "missing"] += 1
    return dict(sorted(counts.items()))


def row_line(row):
    line_no = row.get("_line_no")
    return line_no if line_no else None


def node_or_label_key(row, prefix):
    return str(
        row.get(f"{prefix}_id")
        or row.get(f"{prefix}_label")
        or row.get(prefix)
        or ""
    ).strip()


def candidate_edge_key(edge):
    return (
        node_or_label_key(edge, "source") or node_or_label_key(edge, "subject"),
        str(edge.get("predicate") or edge.get("rel") or "").strip().upper(),
        node_or_label_key(edge, "target") or node_or_label_key(edge, "object"),
    )


def accepted_candidate_refs_and_keys(row):
    refs = set()
    keys = set()
    for edge in row.get("gold_edges") or []:
        if not isinstance(edge, dict):
            continue
        ref = str(edge.get("reference_id") or edge.get("candidate_reference_id") or "").strip()
        if ref:
            refs.add(ref)
        key = candidate_edge_key(edge)
        if all(key):
            keys.add(key)
    return refs, keys


def annotation_candidate_coverage_issues(row):
    status = annotation_status_of(row).strip().lower()
    if status not in COMPLETED_ANNOTATION_STATUSES:
        return []

    chunk_id = annotation_key_for(row)
    line_no = row_line(row)
    issues = []
    candidates = [edge for edge in row.get("silver_candidate_edges") or [] if isinstance(edge, dict)]
    rejected_refs = {str(ref).strip() for ref in (row.get("rejected_candidate_reference_ids") or []) if str(ref).strip()}
    accepted_refs, accepted_keys = accepted_candidate_refs_and_keys(row)
    unresolved = []
    for edge in candidates:
        ref = str(edge.get("reference_id") or "").strip()
        key = candidate_edge_key(edge)
        if ref and (ref in rejected_refs or ref in accepted_refs):
            continue
        if all(key) and key in accepted_keys:
            continue
        unresolved.append(ref or "::".join(value for value in key if value))

    if unresolved:
        issues.append(
            {
                "level": "error",
                "code": "completed_chunk_has_unreviewed_candidate_edges",
                "message": (
                    f"Completed annotation row has {len(unresolved)} silver candidate edges that are neither "
                    "accepted in gold_edges nor listed in rejected_candidate_reference_ids."
                ),
                "chunk_id": chunk_id,
                "line": line_no,
                "unresolved_count": len(unresolved),
                "sample": unresolved[:10],
            }
        )
    if candidates and not (row.get("gold_edges") or rejected_refs):
        issues.append(
            {
                "level": "error",
                "code": "completed_chunk_without_accept_or_reject_actions",
                "message": "Completed annotation row has candidate edges but no accepted gold_edges or rejected candidate refs.",
                "chunk_id": chunk_id,
                "line": line_no,
            }
        )
    if status == "needs_adjudication" and not str(row.get("comments") or "").strip():
        issues.append(
            {
                "level": "error",
                "code": "needs_adjudication_missing_comments",
                "message": "Rows marked needs_adjudication must explain the ambiguity in comments.",
                "chunk_id": chunk_id,
                "line": line_no,
            }
        )
    return issues


def expected_annotation_files(exp_dir, batch_count):
    batch_root = exp_dir / "05_review/human_gold_batches"
    target_root = exp_dir / "01_data/gold_annotation/full_120"
    items = []
    for batch_index in range(1, batch_count + 1):
        batch_name = f"full_120_priority_batch_{batch_index:03d}"
        batch_dir = batch_root / batch_name
        for annotator in ("A", "B"):
            input_file = batch_dir / f"annotator_{annotator}_{batch_name}.jsonl"
            reviewed_file = batch_dir / f"annotator_{annotator}_{batch_name}.reviewed.jsonl"
            target_file = target_root / f"annotator_{annotator}.jsonl"
            items.append(
                {
                    "annotator": annotator,
                    "batch": batch_name,
                    "input_file": input_file,
                    "reviewed_file": reviewed_file,
                    "target_file": target_file,
                }
            )
    return items


def validate_annotation_returns(exp_dir, batch_count):
    schema = load_schema(exp_dir)
    chunk_context, chunk_context_issues = load_chunk_context(exp_dir)
    files = []
    errors = []
    warnings = []
    completed_by_annotator = defaultdict(set)
    present_count = 0
    valid_count = 0
    total_reviewed_rows = 0

    for item in expected_annotation_files(exp_dir, batch_count):
        input_file = item["input_file"]
        reviewed_file = item["reviewed_file"]
        target_file = item["target_file"]
        file_summary = {
            "annotator": item["annotator"],
            "batch": item["batch"],
            "input_file": rel(input_file),
            "reviewed_file": rel(reviewed_file),
            "target_file": rel(target_file),
            "present": reviewed_file.exists(),
            "status": "missing_reviewed_file",
            "error_count": 0,
            "warning_count": 0,
            "reviewed_rows": 0,
            "expected_batch_rows": 0,
            "completed_chunks": 0,
        }
        files.append(file_summary)

        if not input_file.exists() or not target_file.exists():
            file_summary["status"] = "missing_input_or_target"
            file_summary["error_count"] += 1
            errors.append(
                {
                    "scope": "annotation",
                    "batch": item["batch"],
                    "annotator": item["annotator"],
                    "error": "missing_input_or_target",
                    "input_file_exists": input_file.exists(),
                    "target_file_exists": target_file.exists(),
                }
            )
            continue
        input_rows = read_annotation_rows(input_file)
        file_summary["expected_batch_rows"] = len(input_rows)

        if not reviewed_file.exists():
            continue

        present_count += 1
        target_rows = read_annotation_rows(target_file)
        reviewed_rows = read_annotation_rows(reviewed_file)
        total_reviewed_rows += len(reviewed_rows)
        file_summary["reviewed_rows"] = len(reviewed_rows)
        file_summary["reviewed_status_counts"] = status_counts(reviewed_rows, annotation_status_of)

        input_keys = {annotation_key_for(row) for row in input_rows if annotation_key_for(row)}
        reviewed_keys = {annotation_key_for(row) for row in reviewed_rows if annotation_key_for(row)}
        file_issues = []
        missing_from_batch = sorted(input_keys - reviewed_keys)
        extra_not_in_batch = sorted(reviewed_keys - input_keys)
        if missing_from_batch:
            file_issues.append(
                {
                    "level": "error",
                    "code": "missing_batch_chunks",
                    "message": f"Reviewed file is missing {len(missing_from_batch)} rows from its assigned batch.",
                    "sample": missing_from_batch[:10],
                }
            )
        if extra_not_in_batch:
            file_issues.append(
                {
                    "level": "error",
                    "code": "extra_chunks_not_in_batch",
                    "message": f"Reviewed file contains {len(extra_not_in_batch)} chunks outside this batch.",
                    "sample": extra_not_in_batch[:10],
                }
            )
        for chunk_issue in chunk_context_issues:
            file_issues.append(
                {
                    "level": chunk_issue.get("level", "error"),
                    "code": chunk_issue.get("code", "chunk_context_issue"),
                    "message": chunk_issue.get("message", ""),
                    "chunk_id": chunk_issue.get("chunk_id"),
                }
            )
        file_issues.extend(validate_annotation_import(target_rows, reviewed_rows, schema, chunk_context, allow_partial=True))
        expected_annotator = str(item["annotator"]).strip()
        for row in reviewed_rows:
            chunk_id = annotation_key_for(row)
            line_no = row_line(row)
            row_status = annotation_status_of(row).strip().lower()
            row_annotator = str(row.get("annotator_id") or "").strip()
            if row_annotator and row_annotator != expected_annotator:
                file_issues.append(
                    {
                        "level": "error",
                        "code": "annotator_id_mismatch",
                        "message": (
                            f"Reviewed row annotator_id `{row_annotator}` does not match assigned annotator "
                            f"`{expected_annotator}`."
                        ),
                        "chunk_id": chunk_id,
                        "line": line_no,
                    }
                )
            if row_status in COMPLETED_ANNOTATION_STATUSES and not row_annotator:
                file_issues.append(
                    {
                        "level": "error",
                        "code": "completed_annotation_missing_annotator_id",
                        "message": "Rows marked completed or needs_adjudication must include annotator_id.",
                        "chunk_id": chunk_id,
                        "line": line_no,
                    }
                )
            file_issues.extend(annotation_candidate_coverage_issues(row))
        file_errors = [issue for issue in file_issues if issue.get("level") == "error"]
        file_warnings = [issue for issue in file_issues if issue.get("level") == "warning"]
        file_summary["error_count"] = len(file_errors)
        file_summary["warning_count"] = len(file_warnings)
        file_summary["errors"] = file_errors[:20]
        file_summary["warnings"] = file_warnings[:20]

        if file_errors:
            file_summary["status"] = "failed_validation"
            errors.extend(
                {
                    "scope": "annotation",
                    "batch": item["batch"],
                    "annotator": item["annotator"],
                    **issue,
                }
                for issue in file_errors[:20]
            )
            warnings.extend(
                {
                    "scope": "annotation",
                    "batch": item["batch"],
                    "annotator": item["annotator"],
                    **issue,
                }
                for issue in file_warnings[:20]
            )
            continue

        _, merge_summary = merge_annotation_rows(target_rows, reviewed_rows, allow_partial=True)
        completed = completed_annotation_chunks(reviewed_rows)
        completed_by_annotator[item["annotator"]].update(completed)
        file_summary["completed_chunks"] = len(completed)
        file_summary["merge_summary"] = merge_summary
        file_summary["status"] = "validated"
        valid_count += 1
        warnings.extend(
            {
                "scope": "annotation",
                "batch": item["batch"],
                "annotator": item["annotator"],
                **issue,
            }
            for issue in file_warnings[:20]
        )

    paired_completed = completed_by_annotator["A"] & completed_by_annotator["B"]
    expected_files = batch_count * 2
    ready_for_minimum_import = (
        not errors
        and present_count == expected_files
        and valid_count == expected_files
        and len(completed_by_annotator["A"]) >= 100
        and len(completed_by_annotator["B"]) >= 100
        and len(paired_completed) >= 100
    )
    return {
        "expected_files": expected_files,
        "present_files": present_count,
        "valid_files": valid_count,
        "missing_files": expected_files - present_count,
        "reviewed_rows": total_reviewed_rows,
        "completed_chunks_by_annotator": {
            "A": len(completed_by_annotator["A"]),
            "B": len(completed_by_annotator["B"]),
        },
        "paired_completed_chunks": len(paired_completed),
        "ready_for_minimum_import": ready_for_minimum_import,
        "files": files,
        "errors": errors[:200],
        "warnings": warnings[:200],
        "error_count": len(errors),
        "warning_count": len(warnings),
    }


def completed_mapping_groups(rows):
    def row_completed(row):
        status = str(row.get("review_status") or "").strip().lower()
        decision = str(row.get("expert_decision") or "").strip().lower()
        grade = str(row.get("relevance_grade") or "").strip()
        explanation_quality = str(row.get("explanation_quality_score") or "").strip()
        reviewer_id = str(row.get("reviewer_id") or "").strip()
        return (
            status in COMPLETED_MAPPING_STATUSES
            and decision in {"accepted", "rejected", "unsure"}
            and grade in {"0", "1", "2", "3"}
            and explanation_quality in {"1", "2", "3", "4", "5"}
            and bool(reviewer_id)
        )

    by_group = defaultdict(list)
    for row in rows:
        standard = str(row.get("standard") or "").strip()
        source_id = str(row.get("source_id") or "").strip()
        rank = int(row.get("rank") or 0)
        if standard and source_id and 1 <= rank <= 5:
            by_group[(standard, source_id)].append(row)
    complete_groups = []
    for (standard, source_id), group_rows in by_group.items():
        ranks = {int(row.get("rank") or 0) for row in group_rows}
        if not set(range(1, 6)).issubset(ranks):
            continue
        if all(row_completed(row) for row in group_rows):
            complete_groups.append({"standard": standard, "source_id": source_id})
    return complete_groups


def read_csv_rows(path):
    path = Path(path)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def to_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def validate_mapping_return(exp_dir):
    target_file = exp_dir / "01_data/mapping_review/mapping_review_items.jsonl"
    reviewed_file = exp_dir / "01_data/mapping_review/mapping_review_items.reviewed.jsonl"
    next_groups_file = exp_dir / "05_review/mapping_review_next_20_groups.csv"
    priority_group_rows = read_csv_rows(next_groups_file)
    expected_top5_rows = sum(to_int(row.get("top5_rows")) for row in priority_group_rows)
    summary = {
        "target_file": rel(target_file),
        "reviewed_file": rel(reviewed_file),
        "next_groups_file": rel(next_groups_file),
        "present": reviewed_file.exists(),
        "status": "missing_reviewed_file",
        "expected_priority_groups": len(priority_group_rows),
        "expected_top5_rows": expected_top5_rows,
        "target_rows": 0,
        "reviewed_rows": 0,
        "completed_rows": 0,
        "complete_top5_groups": 0,
        "ready_for_expert_metric_import": False,
        "errors": [],
        "warnings": [],
        "error_count": 0,
        "warning_count": 0,
    }
    if not target_file.exists():
        summary["status"] = "missing_target"
        summary["errors"] = [{"error": "missing_target", "path": rel(target_file)}]
        summary["error_count"] = 1
        return summary
    original_rows = read_mapping_review_rows(target_file)
    summary["target_rows"] = len(original_rows)
    if not reviewed_file.exists():
        return summary

    reviewed_rows = read_mapping_review_rows(reviewed_file)
    errors, warnings = validate_mapping_rows(original_rows, reviewed_rows, allow_partial=True)
    summary["reviewed_rows"] = len(reviewed_rows)
    summary["errors"] = [{"message": item} for item in errors[:200]]
    summary["warnings"] = [{"message": item} for item in warnings[:200]]
    summary["error_count"] = len(errors)
    summary["warning_count"] = len(warnings)
    if errors:
        summary["status"] = "failed_validation"
        return summary

    merged_rows, merge_summary = merge_mapping_rows(original_rows, reviewed_rows, allow_partial=True)
    groups = completed_mapping_groups(merged_rows)
    summary["merge_summary"] = merge_summary
    summary["completed_rows"] = merge_summary.get("completed_rows", 0)
    summary["complete_top5_groups"] = len(groups)
    summary["status"] = "validated"
    summary["ready_for_expert_metric_import"] = len(groups) > 0
    return summary


def completed_crosswalk_groups(rows):
    def row_completed(row):
        status = str(row.get("review_status") or "").strip().lower()
        decision = str(row.get("expert_decision") or "").strip().lower()
        grade = str(row.get("utility_grade") or "").strip()
        explanation_quality = str(row.get("explanation_quality_score") or "").strip()
        reviewer_id = str(row.get("reviewer_id") or "").strip()
        return (
            status in COMPLETED_MAPPING_STATUSES
            and decision in {"accepted", "rejected", "unsure"}
            and grade in {"0", "1", "2", "3"}
            and explanation_quality in {"1", "2", "3", "4", "5"}
            and bool(reviewer_id)
        )

    by_source = defaultdict(list)
    for row in rows:
        source_id = str(row.get("source_id") or "").strip()
        rank = int(row.get("crosswalk_rank") or 0)
        if source_id and rank > 0:
            by_source[source_id].append(row)
    complete_groups = []
    for source_id, group_rows in by_source.items():
        ranks = {int(row.get("crosswalk_rank") or 0) for row in group_rows}
        expected = set(range(1, max(ranks) + 1)) if ranks else set()
        if expected and expected.issubset(ranks) and all(row_completed(row) for row in group_rows):
            complete_groups.append({"source_id": source_id})
    return complete_groups


def validate_crosswalk_return(exp_dir):
    target_file = exp_dir / "01_data/crosswalk_review/crosswalk_review_items.jsonl"
    reviewed_file = exp_dir / "01_data/crosswalk_review/crosswalk_review_items.reviewed.jsonl"
    manifest_file = exp_dir / "01_data/crosswalk_review/crosswalk_review_manifest.json"
    manifest = {}
    if manifest_file.exists():
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    summary = {
        "target_file": rel(target_file),
        "reviewed_file": rel(reviewed_file),
        "manifest_file": rel(manifest_file),
        "present": reviewed_file.exists(),
        "status": "missing_reviewed_file",
        "expected_rows": int(manifest.get("candidate_rows") or 0),
        "expected_source_tasks": int(manifest.get("source_task_count") or 0),
        "reviewed_rows": 0,
        "completed_rows": 0,
        "complete_source_groups": 0,
        "ready_for_crosswalk_metric_import": False,
        "errors": [],
        "warnings": [],
        "error_count": 0,
        "warning_count": 0,
    }
    if not target_file.exists():
        summary["status"] = "missing_target"
        summary["errors"] = [{"error": "missing_target", "path": rel(target_file)}]
        summary["error_count"] = 1
        return summary
    if not reviewed_file.exists():
        return summary

    original_rows = read_crosswalk_review_rows(target_file)
    reviewed_rows = read_crosswalk_review_rows(reviewed_file)
    errors, warnings = validate_crosswalk_rows(original_rows, reviewed_rows, allow_partial=True)
    summary["reviewed_rows"] = len(reviewed_rows)
    summary["errors"] = [{"message": item} for item in errors[:200]]
    summary["warnings"] = [{"message": item} for item in warnings[:200]]
    summary["error_count"] = len(errors)
    summary["warning_count"] = len(warnings)
    if errors:
        summary["status"] = "failed_validation"
        return summary

    merged_rows, merge_summary = merge_crosswalk_rows(original_rows, reviewed_rows, allow_partial=True)
    groups = completed_crosswalk_groups(merged_rows)
    summary["merge_summary"] = merge_summary
    summary["completed_rows"] = merge_summary.get("completed_rows", 0)
    summary["complete_source_groups"] = len(groups)
    summary["status"] = "validated"
    summary["ready_for_crosswalk_metric_import"] = len(groups) > 0
    return summary


def completed_adjudication_chunks(rows):
    return {
        annotation_key_for(row)
        for row in rows
        if annotation_status_of(row).strip().lower() in COMPLETED_ADJUDICATION_STATUSES
    }


def validate_adjudication_return(exp_dir):
    package_dir = exp_dir / "01_data/gold_annotation/full_120"
    input_file = package_dir / "adjudication_draft.jsonl"
    target_file = package_dir / "adjudication.jsonl"
    reviewed_file = package_dir / "adjudication_edited.jsonl"
    summary = {
        "input_file": rel(input_file),
        "target_file": rel(target_file),
        "reviewed_file": rel(reviewed_file),
        "present": reviewed_file.exists(),
        "status": "missing_reviewed_file",
        "expected_rows": 0,
        "reviewed_rows": 0,
        "completed_adjudicated_chunks": 0,
        "ready_for_minimum_adjudication_import": False,
        "errors": [],
        "warnings": [],
        "error_count": 0,
        "warning_count": 0,
    }
    if not input_file.exists() or not target_file.exists():
        summary["status"] = "missing_input_or_target"
        summary["errors"] = [
            {
                "error": "missing_input_or_target",
                "input_file_exists": input_file.exists(),
                "target_file_exists": target_file.exists(),
            }
        ]
        summary["error_count"] = 1
        return summary
    input_rows = read_annotation_rows(input_file)
    target_rows = read_annotation_rows(target_file)
    summary["expected_rows"] = len(input_rows)
    if not reviewed_file.exists():
        return summary

    reviewed_rows = read_annotation_rows(reviewed_file)
    summary["reviewed_rows"] = len(reviewed_rows)
    input_keys = {annotation_key_for(row) for row in input_rows if annotation_key_for(row)}
    reviewed_keys = {annotation_key_for(row) for row in reviewed_rows if annotation_key_for(row)}
    missing_from_draft = sorted(input_keys - reviewed_keys)
    extra_not_in_draft = sorted(reviewed_keys - input_keys)
    file_issues = []
    if missing_from_draft:
        file_issues.append(
            {
                "level": "warning",
                "code": "missing_draft_chunks",
                "message": f"Reviewed adjudication file is missing {len(missing_from_draft)} draft rows.",
                "sample": missing_from_draft[:10],
            }
        )
    if extra_not_in_draft:
        file_issues.append(
            {
                "level": "error",
                "code": "extra_chunks_not_in_draft",
                "message": f"Reviewed adjudication file contains {len(extra_not_in_draft)} chunks outside the draft.",
                "sample": extra_not_in_draft[:10],
            }
        )
    schema = load_schema(exp_dir)
    chunk_context, chunk_context_issues = load_chunk_context(exp_dir)
    for chunk_issue in chunk_context_issues:
        file_issues.append(
            {
                "level": chunk_issue.get("level", "error"),
                "code": chunk_issue.get("code", "chunk_context_issue"),
                "message": chunk_issue.get("message", ""),
                "chunk_id": chunk_issue.get("chunk_id"),
            }
        )
    file_issues.extend(validate_annotation_import(target_rows, reviewed_rows, schema, chunk_context, allow_partial=True))
    for row in reviewed_rows:
        row_status = annotation_status_of(row).strip().lower()
        if row_status in COMPLETED_ADJUDICATION_STATUSES and not str(row.get("adjudicator_id") or "").strip():
            file_issues.append(
                {
                    "level": "error",
                    "code": "completed_adjudication_missing_adjudicator_id",
                    "message": "Completed adjudication rows must include adjudicator_id.",
                    "chunk_id": annotation_key_for(row),
                    "line": row_line(row),
                }
            )
    errors = [issue for issue in file_issues if issue.get("level") == "error"]
    warnings = [issue for issue in file_issues if issue.get("level") == "warning"]
    completed = completed_adjudication_chunks(reviewed_rows)
    summary["completed_adjudicated_chunks"] = len(completed)
    summary["errors"] = errors[:200]
    summary["warnings"] = warnings[:200]
    summary["error_count"] = len(errors)
    summary["warning_count"] = len(warnings)
    if errors:
        summary["status"] = "failed_validation"
        return summary
    summary["status"] = "validated"
    summary["ready_for_minimum_adjudication_import"] = len(completed) >= 100
    return summary


def to_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def norm_bool_text(value):
    return str(value or "").strip().lower()


def to_bool(value):
    return norm_bool_text(value) in {"1", "true", "yes", "y"}


def active_review_row_reviewed(row):
    return bool(str(row.get("decision") or "").strip() or str(row.get("corrected_error") or "").strip())


def validate_active_review_effort_return(exp_dir):
    plan_path = exp_dir / "06_release/active_review_human_effort_plan.json"
    plan = {}
    if plan_path.exists():
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    template_file = Path(plan.get("template_csv") or exp_dir / "05_review/active_review_human_effort_template.csv")
    reviewed_file = Path(plan.get("expected_reviewed_csv") or exp_dir / "05_review/active_review_human_effort.reviewed.csv")
    metrics_file = Path(plan.get("metrics_json") or exp_dir / "04_evaluation/active_review_human_effort_metrics.json")
    template_rows = read_csv_rows(template_file)
    summary = {
        "plan_file": rel(plan_path),
        "template_file": rel(template_file),
        "reviewed_file": rel(reviewed_file),
        "metrics_file": rel(metrics_file),
        "present": reviewed_file.exists(),
        "status": "missing_reviewed_file",
        "expected_rows": len(template_rows),
        "reviewed_rows": 0,
        "completed_review_rows": 0,
        "timed_review_rows": 0,
        "total_review_seconds": 0.0,
        "ready_for_effort_metric_import": False,
        "errors": [],
        "warnings": [],
        "error_count": 0,
        "warning_count": 0,
    }
    if not template_file.exists():
        summary["status"] = "missing_template"
        summary["errors"] = [{"error": "missing_template", "path": rel(template_file)}]
        summary["error_count"] = 1
        return summary
    if not reviewed_file.exists():
        return summary

    reviewed_rows = read_csv_rows(reviewed_file)
    summary["reviewed_rows"] = len(reviewed_rows)
    fieldnames = set(reviewed_rows[0].keys()) if reviewed_rows else set()
    missing_fields = sorted(ACTIVE_REVIEW_REQUIRED_FIELDS - fieldnames)
    if missing_fields:
        summary["errors"].append({"error": "missing_required_fields", "fields": missing_fields})

    template_ids = {row.get("review_item_id") for row in template_rows if row.get("review_item_id")}
    reviewed_ids = [row.get("review_item_id") for row in reviewed_rows if row.get("review_item_id")]
    duplicate_ids = sorted({item_id for item_id in reviewed_ids if reviewed_ids.count(item_id) > 1})
    extra_ids = sorted(set(reviewed_ids) - template_ids)
    missing_ids = sorted(template_ids - set(reviewed_ids))
    if duplicate_ids:
        summary["errors"].append({"error": "duplicate_review_item_ids", "sample": duplicate_ids[:10]})
    if extra_ids:
        summary["errors"].append({"error": "extra_review_item_ids", "sample": extra_ids[:10]})
    if missing_ids:
        summary["warnings"].append({"warning": "missing_template_rows", "count": len(missing_ids), "sample": missing_ids[:10]})

    decision_counts = Counter()
    reviewer_counts = Counter()
    correction_counts = Counter()
    high_impact_counts = Counter()
    for idx, row in enumerate(reviewed_rows, start=1):
        row_id = row.get("review_item_id") or f"row_{idx}"
        decision = str(row.get("decision") or "").strip().lower()
        reviewer_id = str(row.get("reviewer_id") or "").strip()
        review_seconds_raw = str(row.get("review_seconds") or "").strip()
        corrected_error = norm_bool_text(row.get("corrected_error"))
        high_impact = norm_bool_text(row.get("high_impact_correction"))
        evidence_issue = norm_bool_text(row.get("evidence_issue"))
        schema_issue = norm_bool_text(row.get("schema_issue"))
        notes = str(row.get("notes") or "").strip()
        row_has_review = active_review_row_reviewed(row) or bool(reviewer_id or review_seconds_raw or high_impact)

        decision_counts[decision or "blank"] += 1
        reviewer_counts[reviewer_id or "blank"] += 1
        correction_counts[corrected_error or "blank"] += 1
        high_impact_counts[high_impact or "blank"] += 1

        for field, value in [
            ("corrected_error", corrected_error),
            ("high_impact_correction", high_impact),
            ("evidence_issue", evidence_issue),
            ("schema_issue", schema_issue),
            ("included_in_active", norm_bool_text(row.get("included_in_active"))),
            ("included_in_uncertainty", norm_bool_text(row.get("included_in_uncertainty"))),
            ("included_in_random", norm_bool_text(row.get("included_in_random"))),
        ]:
            if value not in ACTIVE_REVIEW_ALLOWED_BOOL:
                summary["errors"].append({"error": "invalid_boolean_value", "row": row_id, "field": field, "value": value})

        if decision not in ACTIVE_REVIEW_ALLOWED_DECISIONS:
            summary["errors"].append({"error": "invalid_decision", "row": row_id, "value": decision})

        if review_seconds_raw:
            if to_float(review_seconds_raw, -1.0) < 0:
                summary["errors"].append({"error": "negative_review_seconds", "row": row_id, "value": review_seconds_raw})

        if row_has_review:
            if not reviewer_id:
                summary["errors"].append({"error": "reviewed_row_missing_reviewer_id", "row": row_id})
            if not decision:
                summary["errors"].append({"error": "reviewed_row_missing_decision", "row": row_id})
            if not review_seconds_raw or to_float(review_seconds_raw) <= 0:
                summary["errors"].append({"error": "reviewed_row_missing_positive_review_seconds", "row": row_id})
            if corrected_error == "":
                summary["errors"].append({"error": "reviewed_row_missing_corrected_error", "row": row_id})
            if high_impact == "":
                summary["errors"].append({"error": "reviewed_row_missing_high_impact_correction", "row": row_id})

        if decision in ACTIVE_REVIEW_CORRECTION_DECISIONS and corrected_error not in {"1", "true", "yes", "y"}:
            summary["errors"].append(
                {"error": "correction_decision_without_corrected_error", "row": row_id, "decision": decision}
            )
        if decision == "correct" and to_bool(corrected_error):
            summary["errors"].append({"error": "correct_decision_with_corrected_error", "row": row_id})
        if to_bool(high_impact) and not to_bool(corrected_error):
            summary["errors"].append({"error": "high_impact_without_corrected_error", "row": row_id})
        if to_bool(high_impact) and not (to_bool(evidence_issue) or to_bool(schema_issue) or notes):
            summary["warnings"].append({"warning": "high_impact_without_issue_flag_or_notes", "row": row_id})

    completed_rows = [row for row in reviewed_rows if active_review_row_reviewed(row)]
    timed_rows = [row for row in completed_rows if to_float(row.get("review_seconds")) > 0]
    summary["completed_review_rows"] = len(completed_rows)
    summary["timed_review_rows"] = len(timed_rows)
    summary["total_review_seconds"] = round(sum(to_float(row.get("review_seconds")) for row in timed_rows), 3)
    summary["decision_counts"] = dict(sorted(decision_counts.items()))
    summary["reviewer_counts"] = dict(sorted(reviewer_counts.items()))
    summary["correction_counts"] = dict(sorted(correction_counts.items()))
    summary["high_impact_counts"] = dict(sorted(high_impact_counts.items()))
    if reviewed_rows and not completed_rows:
        summary["warnings"].append({"warning": "reviewed_file_has_no_completed_decisions"})
    if completed_rows and not timed_rows:
        summary["warnings"].append({"warning": "completed_decisions_have_no_positive_review_seconds"})

    summary["error_count"] = len(summary["errors"])
    summary["warning_count"] = len(summary["warnings"])
    if summary["errors"]:
        summary["status"] = "failed_validation"
        return summary
    summary["status"] = "validated"
    summary["ready_for_effort_metric_import"] = (
        len(template_rows) > 0
        and len(completed_rows) == len(template_rows)
        and len(timed_rows) == len(completed_rows)
        and not missing_ids
    )
    if reviewed_rows and not summary["ready_for_effort_metric_import"]:
        summary["warnings"].append(
            {
                "warning": "active_review_effort_not_complete_for_claim",
                "expected_rows": len(template_rows),
                "completed_review_rows": len(completed_rows),
                "timed_review_rows": len(timed_rows),
            }
        )
        summary["warning_count"] = len(summary["warnings"])
    return summary


def overall_status(annotation, adjudication, mapping, crosswalk, active_review):
    if (
        annotation["error_count"]
        or adjudication["error_count"]
        or mapping["error_count"]
        or crosswalk["error_count"]
        or active_review["error_count"]
    ):
        return "failed_validation"
    if (
        annotation["ready_for_minimum_import"]
        and adjudication["ready_for_minimum_adjudication_import"]
        and mapping["ready_for_expert_metric_import"]
        and crosswalk["ready_for_crosswalk_metric_import"]
        and active_review["ready_for_effort_metric_import"]
    ):
        return "all_human_returns_ready"
    if annotation["ready_for_minimum_import"] and adjudication["ready_for_minimum_adjudication_import"]:
        return "annotation_and_adjudication_returns_ready_optional_pending"
    if annotation["ready_for_minimum_import"] and adjudication["present"]:
        return "annotation_returns_ready_adjudication_validated_or_pending"
    if annotation["ready_for_minimum_import"] and mapping["ready_for_expert_metric_import"]:
        return "annotation_and_mapping_returns_ready_active_pending"
    if annotation["ready_for_minimum_import"]:
        return "annotation_returns_ready_adjudication_pending"
    if annotation["present_files"] or adjudication["present"] or mapping["present"] or crosswalk["present"] or active_review["present"]:
        return "partial_returns_validated"
    return "pending_human_returns"


def return_scope_summary(annotation, adjudication, mapping, crosswalk, active_review):
    present = int(annotation.get("present_files") or 0)
    present += 1 if adjudication.get("present") else 0
    present += 1 if mapping.get("present") else 0
    present += 1 if crosswalk.get("present") else 0
    present += 1 if active_review.get("present") else 0
    minimum_ready = bool(
        annotation.get("ready_for_minimum_import")
        and adjudication.get("ready_for_minimum_adjudication_import")
    )
    mapping_ready = bool(mapping.get("ready_for_expert_metric_import"))
    crosswalk_ready = bool(crosswalk.get("ready_for_crosswalk_metric_import"))
    active_ready = bool(active_review.get("ready_for_effort_metric_import"))
    if not present:
        apply_scope = "no_return_files"
    elif minimum_ready and mapping_ready and crosswalk_ready and active_ready:
        apply_scope = "all_minimum_and_optional_returns_ready"
    elif minimum_ready:
        apply_scope = "minimum_annotation_adjudication_ready_optional_pending"
    else:
        apply_scope = "partial_valid_returns_only"
    return {
        "present_human_return_files": present,
        "apply_scope": apply_scope,
        "minimum_paper_gate_ready_after_preflight": minimum_ready,
        "optional_mapping_ready_after_preflight": mapping_ready,
        "optional_crosswalk_ready_after_preflight": crosswalk_ready,
        "optional_active_effort_ready_after_preflight": active_ready,
    }


def render_report(payload):
    annotation = payload["annotation_returns"]
    adjudication = payload["adjudication_return"]
    mapping = payload["mapping_return"]
    crosswalk = payload["crosswalk_return"]
    active_review = payload["active_review_effort_return"]
    policy = payload.get("validation_policy") or {}
    lines = [
        "# CAPE-KG Human Review Return Preflight",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Overall status: `{payload['overall_status']}`",
        "",
        "This preflight checks returned `.reviewed.jsonl` files before applying imports. It does not create paper-claimable human-gold metrics.",
        "",
        "## Validation Policy",
        "",
        f"- Annotator file identity check: `{policy.get('annotator_file_identity_check')}`",
        f"- Completed candidate coverage check: `{policy.get('completed_candidate_coverage_check')}`",
        f"- Needs-adjudication comments required: `{policy.get('needs_adjudication_comments_required')}`",
        f"- Completed adjudication adjudicator id required: `{policy.get('completed_adjudication_adjudicator_id_required')}`",
        f"- Mapping completed rows require explanation quality score: `{policy.get('mapping_completed_rows_require_explanation_quality_score')}`",
        f"- Crosswalk completed rows require utility and explanation scores: `{policy.get('crosswalk_completed_rows_require_utility_and_explanation_scores')}`",
        "",
        "## Return Scope",
        "",
        f"- Present human return files: {payload['present_human_return_files']}",
        f"- Apply scope: `{payload['apply_scope']}`",
        f"- Minimum paper gate ready after preflight: `{payload['minimum_paper_gate_ready_after_preflight']}`",
        f"- Optional mapping ready after preflight: `{payload['optional_mapping_ready_after_preflight']}`",
        f"- Optional crosswalk ready after preflight: `{payload['optional_crosswalk_ready_after_preflight']}`",
        f"- Optional active-effort ready after preflight: `{payload['optional_active_effort_ready_after_preflight']}`",
        "",
        "## Human Annotation Returns",
        "",
        f"- Expected reviewed files: {annotation['expected_files']}",
        f"- Present reviewed files: {annotation['present_files']}",
        f"- Valid reviewed files: {annotation['valid_files']}",
        f"- Completed chunks by annotator: `{annotation['completed_chunks_by_annotator']}`",
        f"- Paired completed chunks: {annotation['paired_completed_chunks']}",
        f"- Ready for minimum import: `{annotation['ready_for_minimum_import']}`",
        f"- Errors / warnings: {annotation['error_count']} / {annotation['warning_count']}",
        "",
        "## Adjudication Return",
        "",
        f"- Reviewed file present: `{adjudication['present']}`",
        f"- Reviewed rows: {adjudication['reviewed_rows']}",
        f"- Completed adjudicated chunks: {adjudication['completed_adjudicated_chunks']}",
        f"- Ready for minimum adjudication import: `{adjudication['ready_for_minimum_adjudication_import']}`",
        f"- Errors / warnings: {adjudication['error_count']} / {adjudication['warning_count']}",
        "",
        "## Mapping Return",
        "",
        f"- Reviewed file present: `{mapping['present']}`",
        f"- Reviewed rows: {mapping['reviewed_rows']}",
        f"- Completed rows after merge: {mapping['completed_rows']}",
        f"- Complete Top-5 groups after merge: {mapping['complete_top5_groups']}",
        f"- Ready for expert metric import: `{mapping['ready_for_expert_metric_import']}`",
        f"- Errors / warnings: {mapping['error_count']} / {mapping['warning_count']}",
        "",
        "## Crosswalk Return",
        "",
        f"- Reviewed file present: `{crosswalk['present']}`",
        f"- Reviewed rows: {crosswalk['reviewed_rows']}",
        f"- Completed rows after merge: {crosswalk['completed_rows']}",
        f"- Complete source groups after merge: {crosswalk['complete_source_groups']}",
        f"- Ready for crosswalk metric import: `{crosswalk['ready_for_crosswalk_metric_import']}`",
        f"- Errors / warnings: {crosswalk['error_count']} / {crosswalk['warning_count']}",
        "",
        "## Active-Review Human-Effort Return",
        "",
        f"- Reviewed CSV present: `{active_review['present']}`",
        f"- Reviewed rows: {active_review['reviewed_rows']}",
        f"- Completed review rows: {active_review['completed_review_rows']}",
        f"- Timed review rows: {active_review['timed_review_rows']}",
        f"- Total review seconds: {active_review['total_review_seconds']}",
        f"- Ready for effort metric import: `{active_review['ready_for_effort_metric_import']}`",
        f"- Errors / warnings: {active_review['error_count']} / {active_review['warning_count']}",
        "",
        "## Apply Command After Ready",
        "",
        "```bash",
        "PYTHON_BIN=python3 \\",
        "LLM_PYTHON=python3 \\",
        "APPLY_IMPORTS=1 \\",
        "bash scripts/run_cape_human_return_apply.sh",
        "```",
        "",
        "Low-level refresh script for debugging only: `scripts/run_cape_post_annotation_refresh.sh`.",
        "",
    ]
    if annotation["errors"] or adjudication["errors"] or mapping["errors"] or crosswalk["errors"] or active_review["errors"]:
        lines += ["## Errors", ""]
        for item in (
            annotation["errors"]
            + adjudication["errors"]
            + mapping["errors"]
            + crosswalk["errors"]
            + active_review["errors"]
        )[:50]:
            lines.append(f"- `{item}`")
        lines.append("")
    return "\n".join(lines)


def run(args):
    exp_dir = Path(args.experiment_dir)
    annotation = validate_annotation_returns(exp_dir, args.batch_count)
    adjudication = validate_adjudication_return(exp_dir)
    mapping = validate_mapping_return(exp_dir)
    crosswalk = validate_crosswalk_return(exp_dir)
    active_review = validate_active_review_effort_return(exp_dir)
    status = overall_status(annotation, adjudication, mapping, crosswalk, active_review)
    scope = return_scope_summary(annotation, adjudication, mapping, crosswalk, active_review)
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": rel(exp_dir),
        "overall_status": status,
        "claim_status": "return_preflight_not_paper_evidence",
        "validation_policy": {
            "annotator_file_identity_check": True,
            "completed_candidate_coverage_check": True,
            "needs_adjudication_comments_required": True,
            "completed_adjudication_adjudicator_id_required": True,
            "mapping_completed_rows_require_explanation_quality_score": True,
            "crosswalk_completed_rows_require_utility_and_explanation_scores": True,
        },
        **scope,
        "annotation_returns": annotation,
        "adjudication_return": adjudication,
        "mapping_return": mapping,
        "crosswalk_return": crosswalk,
        "active_review_effort_return": active_review,
        "report": rel(exp_dir / "06_release/human_review_return_preflight.md"),
    }
    release_dir = exp_dir / "06_release"
    write_json(release_dir / "human_review_return_preflight.json", payload)
    write_text(release_dir / "human_review_return_preflight.md", render_report(payload))
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if status == "failed_validation":
        raise SystemExit(2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--batch-count", type=int, default=5)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
