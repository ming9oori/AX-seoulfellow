#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate and safely import CAPE-KG human annotation/adjudication exports."""

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from evaluate_cape_human_gold import (
    COMPLETED_ADJUDICATION_STATUSES,
    is_completed_adjudication,
    load_chunk_context,
    load_schema,
    validate_edge,
    validate_node,
)


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")

IMMUTABLE_FIELDS = ["chunk_id", "chunk_text", "chapter_id", "section_id", "page_start", "page_end", "package"]
ANNOTATION_STATUSES = {"pending_human_annotation", "in_progress", "completed", "needs_adjudication"}
ADJUDICATION_STATUSES = set(COMPLETED_ADJUDICATION_STATUSES) | {
    "pending_two_annotator_input",
    "needs_adjudication",
    "in_progress",
}
ANNOTATION_EDITABLE_FIELDS = [
    "annotation_status",
    "annotator_id",
    "gold_nodes",
    "gold_edges",
    "rejected_candidate_reference_ids",
    "missing_but_supported_notes",
    "comments",
    "time_minutes",
]
ADJUDICATION_EDITABLE_FIELDS = [
    "adjudication_status",
    "adjudicator_id",
    "adjudicated_gold_nodes",
    "adjudicated_gold_edges",
    "adjudication_notes",
]


def read_rows(path):
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
    for line_no, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
        row["_line_no"] = line_no
        rows.append(row)
    return rows


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            clean = {key: value for key, value in row.items() if key != "_line_no"}
            f.write(json.dumps(clean, ensure_ascii=False, sort_keys=True) + "\n")


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def row_mode(row):
    return "adjudication" if "adjudication_status" in row or "adjudicated_gold_edges" in row else "annotation"


def status_of(row):
    if row_mode(row) == "adjudication":
        return str(row.get("adjudication_status") or "").strip()
    return str(row.get("annotation_status") or "").strip()


def key_for(row):
    return str(row.get("chunk_id") or "").strip()


def duplicate_keys(rows):
    counts = Counter(key_for(row) for row in rows)
    return [key for key, count in counts.items() if key and count > 1]


def issue(level, code, message, chunk_id=None, line=None):
    row = {"level": level, "code": code, "message": message}
    if chunk_id:
        row["chunk_id"] = chunk_id
    if line:
        row["line"] = line
    return row


def validate_annotation_row(row, schema, chunk_context, issues):
    chunk_id = key_for(row)
    line_no = row.get("_line_no")
    status = status_of(row)
    if status not in ANNOTATION_STATUSES:
        issues.append(issue("error", "invalid_annotation_status", f"Invalid annotation_status `{status}`.", chunk_id, line_no))

    nodes = row.get("gold_nodes") or []
    edges = row.get("gold_edges") or []
    if not isinstance(nodes, list):
        issues.append(issue("error", "gold_nodes_not_list", "gold_nodes must be a list.", chunk_id, line_no))
        nodes = []
    if not isinstance(edges, list):
        issues.append(issue("error", "gold_edges_not_list", "gold_edges must be a list.", chunk_id, line_no))
        edges = []
    for index, node in enumerate(nodes, start=1):
        validate_node(row, node, schema, issues, index, chunk_context)
    for index, edge in enumerate(edges, start=1):
        validate_edge(row, edge, schema, chunk_context, issues, index)

    rejected = row.get("rejected_candidate_reference_ids") or []
    if not isinstance(rejected, list):
        issues.append(issue("error", "rejected_refs_not_list", "rejected_candidate_reference_ids must be a list.", chunk_id, line_no))
    else:
        candidate_refs = {item.get("reference_id") for item in row.get("silver_candidate_edges") or [] if item.get("reference_id")}
        for ref in rejected:
            if candidate_refs and ref not in candidate_refs:
                issues.append(issue("warning", "unknown_rejected_candidate_ref", f"Rejected reference `{ref}` is not a candidate edge.", chunk_id, line_no))


def validate_adjudication_row(row, schema, chunk_context, issues):
    chunk_id = key_for(row)
    line_no = row.get("_line_no")
    status = status_of(row)
    if status not in ADJUDICATION_STATUSES:
        issues.append(issue("error", "invalid_adjudication_status", f"Invalid adjudication_status `{status}`.", chunk_id, line_no))

    nodes = row.get("adjudicated_gold_nodes") or []
    edges = row.get("adjudicated_gold_edges") or []
    if not isinstance(nodes, list):
        issues.append(issue("error", "adjudicated_gold_nodes_not_list", "adjudicated_gold_nodes must be a list.", chunk_id, line_no))
        nodes = []
    if not isinstance(edges, list):
        issues.append(issue("error", "adjudicated_gold_edges_not_list", "adjudicated_gold_edges must be a list.", chunk_id, line_no))
        edges = []
    if is_completed_adjudication(row) and not nodes and not edges:
        issues.append(issue("warning", "completed_adjudication_without_gold_items", "Completed adjudication has no gold nodes or edges.", chunk_id, line_no))
    for index, node in enumerate(nodes, start=1):
        validate_node(row, node, schema, issues, index, chunk_context)
    for index, edge in enumerate(edges, start=1):
        validate_edge(row, edge, schema, chunk_context, issues, index)


def validate_import(original_rows, reviewed_rows, schema, chunk_context, allow_partial):
    issues = []
    original_by_key = {key_for(row): row for row in original_rows if key_for(row)}
    reviewed_by_key = {}
    original_mode = row_mode(original_rows[0]) if original_rows else "annotation"

    for key in duplicate_keys(original_rows):
        issues.append(issue("error", "duplicate_original_chunk", f"Original file has duplicate chunk `{key}`.", key))
    for key in duplicate_keys(reviewed_rows):
        issues.append(issue("error", "duplicate_reviewed_chunk", f"Reviewed file has duplicate chunk `{key}`.", key))

    for row in reviewed_rows:
        chunk_id = key_for(row)
        line_no = row.get("_line_no")
        if not chunk_id:
            issues.append(issue("error", "missing_chunk_id", "Reviewed row has no chunk_id.", line=line_no))
            continue
        if chunk_id not in original_by_key:
            issues.append(issue("error", "unknown_chunk_id", "Reviewed chunk is not present in the target file.", chunk_id, line_no))
            continue
        if row_mode(row) != original_mode:
            issues.append(issue("error", "mode_mismatch", f"Reviewed row mode `{row_mode(row)}` does not match target mode `{original_mode}`.", chunk_id, line_no))
        reviewed_by_key[chunk_id] = row
        original = original_by_key[chunk_id]
        for field in IMMUTABLE_FIELDS:
            if field in row and str(row.get(field, "")).strip() != str(original.get(field, "")).strip():
                issues.append(
                    issue(
                        "error",
                        "immutable_field_changed",
                        f"Immutable field `{field}` changed: {original.get(field)!r} -> {row.get(field)!r}.",
                        chunk_id,
                        line_no,
                    )
                )
        if row_mode(row) == "adjudication":
            validate_adjudication_row(row, schema, chunk_context, issues)
        else:
            validate_annotation_row(row, schema, chunk_context, issues)

    if not allow_partial:
        missing = sorted(set(original_by_key) - set(reviewed_by_key))
        if missing:
            sample = ", ".join(missing[:5])
            issues.append(issue("error", "missing_reviewed_chunks", f"Reviewed file is missing {len(missing)} chunks; sample: {sample}"))

    return issues


def merge_rows(original_rows, reviewed_rows, allow_partial):
    reviewed_by_key = {key_for(row): row for row in reviewed_rows if key_for(row)}
    mode = row_mode(original_rows[0]) if original_rows else "annotation"
    editable = ADJUDICATION_EDITABLE_FIELDS if mode == "adjudication" else ANNOTATION_EDITABLE_FIELDS
    merged = []
    changed_rows = 0
    status_counts = Counter()
    node_count = 0
    edge_count = 0

    for original in original_rows:
        chunk_id = key_for(original)
        row = {key: value for key, value in original.items() if key != "_line_no"}
        reviewed = reviewed_by_key.get(chunk_id)
        if reviewed is not None:
            before = {field: row.get(field) for field in editable}
            for field in editable:
                if field in reviewed:
                    row[field] = reviewed.get(field)
            after = {field: row.get(field) for field in editable}
            if before != after:
                changed_rows += 1
        elif not allow_partial:
            raise AssertionError("missing rows should have been rejected before merge")

        status_counts[status_of(row) or "missing"] += 1
        nodes = row.get("adjudicated_gold_nodes") if mode == "adjudication" else row.get("gold_nodes")
        edges = row.get("adjudicated_gold_edges") if mode == "adjudication" else row.get("gold_edges")
        node_count += len(nodes or [])
        edge_count += len(edges or [])
        merged.append(row)

    return merged, {
        "mode": mode,
        "changed_rows": changed_rows,
        "status_counts": dict(sorted(status_counts.items())),
        "gold_node_rows": node_count,
        "gold_edge_rows": edge_count,
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
    target_file = Path(args.target_file)
    reviewed_file = Path(args.reviewed_file)
    report_file = Path(args.report_file) if args.report_file else target_file.with_suffix(".import_report.json")

    original_rows = read_rows(target_file)
    reviewed_rows = read_rows(reviewed_file)
    schema = load_schema(exp_dir)
    chunk_context, chunk_issues = load_chunk_context(exp_dir)
    issues = [
        issue(item.get("level", "error"), item.get("code", "chunk_context_issue"), item.get("message", ""), item.get("chunk_id"), item.get("line"))
        for item in chunk_issues
    ]
    issues.extend(validate_import(original_rows, reviewed_rows, schema, chunk_context, args.allow_partial))

    errors = [item for item in issues if item["level"] == "error"]
    warnings = [item for item in issues if item["level"] == "warning"]
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
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors[:200],
        "warnings": warnings[:200],
        "issue_count_truncated": max(0, len(issues) - 400),
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
    parser.add_argument("--target-file", required=True)
    parser.add_argument("--reviewed-file", required=True)
    parser.add_argument("--report-file", default="")
    parser.add_argument("--backup-dir", default="")
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
