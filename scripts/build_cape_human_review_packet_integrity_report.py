#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build an integrity report for the CAPE-KG human-review packet."""

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")

ANNOTATION_REQUIRED_FIELDS = {
    "annotation_status",
    "annotator_id",
    "chunk_id",
    "chunk_text",
    "gold_edges",
    "gold_nodes",
    "instructions",
    "silver_candidate_edges",
}
MAPPING_REQUIRED_FIELDS = {
    "claim_status",
    "expert_decision",
    "mapping_id",
    "rank",
    "review_status",
    "source_id",
    "standard",
    "target_id",
}
CROSSWALK_REQUIRED_FIELDS = {
    "claim_status",
    "crosswalk_id",
    "crosswalk_rank",
    "expert_decision",
    "review_status",
    "source_id",
    "ncs_target_id",
    "pcf_target_id",
}
ACTIVE_EFFORT_REQUIRED_COLUMNS = {
    "review_item_id",
    "condition",
    "chunk_id",
    "subject",
    "predicate",
    "object",
    "reviewer_id",
    "review_seconds",
    "decision",
    "corrected_error",
    "high_impact_correction",
    "evidence_issue",
    "schema_issue",
    "notes",
}


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path):
    rows = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            row["_line_no"] = line_no
            rows.append(row)
    return rows


def read_csv_rows(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


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
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def rel(path):
    return str(Path(path).as_posix())


def file_state(path):
    path = Path(path)
    return {
        "path": rel(path),
        "exists": path.exists(),
        "bytes": path.stat().st_size if path.exists() else 0,
    }


def add_issue(issues, component, severity, code, detail, path=None, expected=None, actual=None):
    issues.append(
        {
            "component": component,
            "severity": severity,
            "code": code,
            "detail": detail,
            "path": rel(path) if path else "",
            "expected": "" if expected is None else expected,
            "actual": "" if actual is None else actual,
        }
    )


def count_candidates(row):
    if "silver_candidate_edge_count" in row:
        try:
            return int(row.get("silver_candidate_edge_count") or 0)
        except (TypeError, ValueError):
            return 0
    candidates = row.get("silver_candidate_edges")
    return len(candidates) if isinstance(candidates, list) else 0


def status_counts(rows, key):
    return dict(Counter(str(row.get(key, "")) for row in rows))


def validate_minimum_annotation_batches(exp_dir, issues):
    release_dir = exp_dir / "06_release"
    assignment_path = release_dir / "annotation_batch_assignment_summary.json"
    assignment = read_json(assignment_path, {}) or {}
    batches = assignment.get("batches") or []
    component = "minimum_annotation_batches"
    batch_rows = []
    annotator_totals = {
        "A": {"rows": 0, "unique_chunks": set(), "candidate_edges_total": 0, "status_counts": Counter()},
        "B": {"rows": 0, "unique_chunks": set(), "candidate_edges_total": 0, "status_counts": Counter()},
    }
    input_files = []
    reviewed_files = []
    missing_inputs = 0
    present_reviewed_files = 0
    field_issue_count = 0
    chunk_pair_mismatch_count = 0

    if not assignment_path.exists():
        add_issue(issues, component, "ERROR", "missing_assignment_summary", "Missing annotation batch assignment summary.", assignment_path)

    for batch in batches:
        batch_id = batch.get("batch_id")
        expected_chunk_ids = list(batch.get("chunk_ids") or [])
        batch_result = {
            "batch_id": batch_id,
            "expected_chunks": len(expected_chunk_ids),
            "candidate_edges_expected": batch.get("candidate_edges_total"),
            "A_rows": 0,
            "B_rows": 0,
            "A_candidate_edges": 0,
            "B_candidate_edges": 0,
            "A_reviewed_present": False,
            "B_reviewed_present": False,
            "chunk_ids_match": False,
        }
        chunks_by_annotator = {}
        for annotator in ("A", "B"):
            input_path = Path((batch.get("annotator_files") or {}).get(annotator, ""))
            reviewed_path = Path((batch.get("reviewed_files") or {}).get(annotator, ""))
            if str(input_path):
                input_files.append(rel(input_path))
            if str(reviewed_path):
                reviewed_files.append(rel(reviewed_path))
                if reviewed_path.exists():
                    present_reviewed_files += 1
                    batch_result[f"{annotator}_reviewed_present"] = True
            if not input_path.exists():
                missing_inputs += 1
                add_issue(issues, component, "ERROR", "missing_annotation_input", "Missing annotator input JSONL.", input_path)
                continue

            rows = read_jsonl(input_path)
            chunks = [row.get("chunk_id") for row in rows]
            chunks_by_annotator[annotator] = chunks
            candidates = sum(count_candidates(row) for row in rows)
            annotator_totals[annotator]["rows"] += len(rows)
            annotator_totals[annotator]["unique_chunks"].update(chunks)
            annotator_totals[annotator]["candidate_edges_total"] += candidates
            annotator_totals[annotator]["status_counts"].update(row.get("annotation_status", "") for row in rows)
            batch_result[f"{annotator}_rows"] = len(rows)
            batch_result[f"{annotator}_candidate_edges"] = candidates

            if len(rows) != len(expected_chunk_ids):
                add_issue(
                    issues,
                    component,
                    "ERROR",
                    "annotation_batch_row_count_mismatch",
                    f"{annotator} row count does not match batch chunk count.",
                    input_path,
                    expected=len(expected_chunk_ids),
                    actual=len(rows),
                )
            if set(chunks) != set(expected_chunk_ids):
                add_issue(
                    issues,
                    component,
                    "ERROR",
                    "annotation_batch_chunk_set_mismatch",
                    f"{annotator} chunk IDs do not match assignment summary.",
                    input_path,
                    expected=len(expected_chunk_ids),
                    actual=len(set(chunks)),
                )
            if candidates != batch.get("candidate_edges_total"):
                add_issue(
                    issues,
                    component,
                    "ERROR",
                    "annotation_candidate_edge_count_mismatch",
                    f"{annotator} candidate edge total does not match assignment summary.",
                    input_path,
                    expected=batch.get("candidate_edges_total"),
                    actual=candidates,
                )

            missing_field_rows = []
            wrong_annotator_rows = []
            wrong_status_rows = []
            for row in rows:
                missing = sorted(ANNOTATION_REQUIRED_FIELDS - set(row))
                if missing:
                    missing_field_rows.append({"line": row.get("_line_no"), "missing": ",".join(missing)})
                if row.get("annotator_id") != annotator:
                    wrong_annotator_rows.append(row.get("_line_no"))
                if row.get("annotation_status") != "pending_human_annotation":
                    wrong_status_rows.append(row.get("_line_no"))
                if row.get("silver_candidate_edge_count") is not None:
                    listed = row.get("silver_candidate_edges")
                    listed_count = len(listed) if isinstance(listed, list) else 0
                    if listed_count != count_candidates(row):
                        field_issue_count += 1
                        add_issue(
                            issues,
                            component,
                            "ERROR",
                            "annotation_candidate_edge_field_mismatch",
                            "silver_candidate_edge_count does not match silver_candidate_edges length.",
                            input_path,
                            expected=count_candidates(row),
                            actual=listed_count,
                        )
                        break
            if missing_field_rows:
                field_issue_count += len(missing_field_rows)
                add_issue(
                    issues,
                    component,
                    "ERROR",
                    "annotation_required_fields_missing",
                    f"{len(missing_field_rows)} rows are missing required fields; first rows={missing_field_rows[:3]}",
                    input_path,
                )
            if wrong_annotator_rows:
                field_issue_count += len(wrong_annotator_rows)
                add_issue(
                    issues,
                    component,
                    "ERROR",
                    "annotation_annotator_id_mismatch",
                    f"{len(wrong_annotator_rows)} rows have the wrong annotator_id.",
                    input_path,
                    expected=annotator,
                    actual=wrong_annotator_rows[:5],
                )
            if wrong_status_rows:
                add_issue(
                    issues,
                    component,
                    "ERROR",
                    "annotation_status_not_pending",
                    f"{len(wrong_status_rows)} rows are not pending_human_annotation.",
                    input_path,
                    expected="pending_human_annotation",
                    actual=wrong_status_rows[:5],
                )

        if set(chunks_by_annotator.get("A") or []) == set(chunks_by_annotator.get("B") or []) == set(expected_chunk_ids):
            batch_result["chunk_ids_match"] = True
        else:
            chunk_pair_mismatch_count += 1
        batch_rows.append(batch_result)

    assigned_unique_chunks = len(annotator_totals["A"]["unique_chunks"] | annotator_totals["B"]["unique_chunks"])
    candidate_total_a = annotator_totals["A"]["candidate_edges_total"]
    candidate_total_b = annotator_totals["B"]["candidate_edges_total"]
    if candidate_total_a != candidate_total_b:
        add_issue(
            issues,
            component,
            "ERROR",
            "annotator_candidate_totals_diverge",
            "A/B candidate totals differ.",
            expected=candidate_total_a,
            actual=candidate_total_b,
        )

    return {
        "assignment_summary": file_state(assignment_path),
        "batch_count": len(batches),
        "expected_batch_count": assignment.get("batch_count"),
        "annotation_input_files": len(input_files),
        "missing_required_input_files": missing_inputs,
        "reviewed_files_expected": len(reviewed_files),
        "reviewed_files_present": present_reviewed_files,
        "assigned_unique_chunks": assigned_unique_chunks,
        "assigned_chunks_expected": assignment.get("assigned_chunks"),
        "candidate_edges_total": candidate_total_a,
        "candidate_edges_total_B": candidate_total_b,
        "candidate_edges_expected": assignment.get("candidate_edges_total"),
        "chunk_pair_mismatch_count": chunk_pair_mismatch_count,
        "field_issue_count": field_issue_count,
        "rows_by_annotator": {k: v["rows"] for k, v in annotator_totals.items()},
        "unique_chunks_by_annotator": {k: len(v["unique_chunks"]) for k, v in annotator_totals.items()},
        "status_counts_by_annotator": {k: dict(v["status_counts"]) for k, v in annotator_totals.items()},
        "batches": batch_rows,
        "claim_status": "input_batches_ready_pending_human_annotation",
    }


def validate_mapping_review(exp_dir, issues):
    component = "mapping_expert_review"
    path = exp_dir / "01_data/mapping_review/mapping_review_items.jsonl"
    manifest_path = exp_dir / "01_data/mapping_review/mapping_review_manifest.json"
    workbench_path = exp_dir / "01_data/mapping_review/mapping_review_workbench.html"
    sheet_path = exp_dir / "01_data/mapping_review/mapping_review_sheet.csv"
    rows = []
    if path.exists():
        rows = read_jsonl(path)
    else:
        add_issue(issues, component, "ERROR", "missing_mapping_items", "Missing mapping review JSONL.", path)

    mapping_ids = [row.get("mapping_id") for row in rows]
    standards = Counter(row.get("standard") for row in rows)
    groups = defaultdict(list)
    ranks_by_group = defaultdict(list)
    required_field_issues = 0
    for row in rows:
        groups[(row.get("source_id"), row.get("standard"))].append(row)
        try:
            ranks_by_group[(row.get("source_id"), row.get("standard"))].append(int(row.get("rank")))
        except (TypeError, ValueError):
            pass
        missing = sorted(MAPPING_REQUIRED_FIELDS - set(row))
        if missing:
            required_field_issues += 1

    if required_field_issues:
        add_issue(issues, component, "ERROR", "mapping_required_fields_missing", f"{required_field_issues} rows are missing required fields.", path)
    duplicate_ids = len(mapping_ids) - len(set(mapping_ids))
    if duplicate_ids:
        add_issue(issues, component, "ERROR", "mapping_duplicate_ids", "Duplicate mapping IDs found.", path, expected=0, actual=duplicate_ids)
    bad_group_sizes = {f"{source_id}:{standard}": len(items) for (source_id, standard), items in groups.items() if len(items) != 5}
    if bad_group_sizes:
        add_issue(issues, component, "ERROR", "mapping_group_size_mismatch", "Each source-standard group should have five top-k rows.", path, expected=5, actual=list(bad_group_sizes.items())[:5])
    bad_ranks = {
        f"{source_id}:{standard}": sorted(ranks)
        for (source_id, standard), ranks in ranks_by_group.items()
        if sorted(ranks) != [1, 2, 3, 4, 5]
    }
    if bad_ranks:
        add_issue(issues, component, "ERROR", "mapping_rank_sequence_mismatch", "Mapping ranks should be 1..5 per group.", path, expected=[1, 2, 3, 4, 5], actual=list(bad_ranks.items())[:5])

    statuses = status_counts(rows, "review_status")
    pending_rows = statuses.get("pending_expert_review", 0)
    completed_rows = len(rows) - pending_rows
    if completed_rows:
        add_issue(issues, component, "WARN", "mapping_rows_already_reviewed", "Some mapping rows are no longer pending expert review.", path, expected=0, actual=completed_rows)

    return {
        "items_file": file_state(path),
        "manifest_file": file_state(manifest_path),
        "workbench_file": file_state(workbench_path),
        "sheet_file": file_state(sheet_path),
        "candidate_rows": len(rows),
        "unique_mapping_ids": len(set(mapping_ids)),
        "duplicate_mapping_ids": duplicate_ids,
        "standard_counts": dict(standards),
        "source_standard_groups": len(groups),
        "group_size_min": min((len(v) for v in groups.values()), default=0),
        "group_size_max": max((len(v) for v in groups.values()), default=0),
        "pending_rows": pending_rows,
        "completed_rows": completed_rows,
        "review_status_counts": statuses,
        "claim_status": "mapping_packet_ready_pending_expert_review",
    }


def validate_crosswalk_review(exp_dir, issues):
    component = "crosswalk_expert_review"
    path = exp_dir / "01_data/crosswalk_review/crosswalk_review_items.jsonl"
    manifest_path = exp_dir / "01_data/crosswalk_review/crosswalk_review_manifest.json"
    protocol_path = exp_dir / "01_data/crosswalk_review/crosswalk_review_protocol.md"
    sheet_path = exp_dir / "01_data/crosswalk_review/crosswalk_review_sheet.csv"
    rows = []
    if path.exists():
        rows = read_jsonl(path)
    else:
        add_issue(issues, component, "ERROR", "missing_crosswalk_items", "Missing crosswalk review JSONL.", path)

    crosswalk_ids = [row.get("crosswalk_id") for row in rows]
    groups = defaultdict(list)
    ranks_by_group = defaultdict(list)
    required_field_issues = 0
    for row in rows:
        groups[row.get("source_id")].append(row)
        try:
            ranks_by_group[row.get("source_id")].append(int(row.get("crosswalk_rank")))
        except (TypeError, ValueError):
            pass
        missing = sorted(CROSSWALK_REQUIRED_FIELDS - set(row))
        if missing:
            required_field_issues += 1

    if required_field_issues:
        add_issue(issues, component, "ERROR", "crosswalk_required_fields_missing", f"{required_field_issues} rows are missing required fields.", path)
    duplicate_ids = len(crosswalk_ids) - len(set(crosswalk_ids))
    if duplicate_ids:
        add_issue(issues, component, "ERROR", "crosswalk_duplicate_ids", "Duplicate crosswalk IDs found.", path, expected=0, actual=duplicate_ids)
    bad_group_sizes = {source_id: len(items) for source_id, items in groups.items() if len(items) != 10}
    if bad_group_sizes:
        add_issue(issues, component, "ERROR", "crosswalk_group_size_mismatch", "Each source task should have ten crosswalk rows.", path, expected=10, actual=list(bad_group_sizes.items())[:5])
    expected_ranks = list(range(1, 11))
    bad_ranks = {source_id: sorted(ranks) for source_id, ranks in ranks_by_group.items() if sorted(ranks) != expected_ranks}
    if bad_ranks:
        add_issue(issues, component, "ERROR", "crosswalk_rank_sequence_mismatch", "Crosswalk ranks should be 1..10 per source task.", path, expected=expected_ranks, actual=list(bad_ranks.items())[:5])

    statuses = status_counts(rows, "review_status")
    pending_rows = statuses.get("pending_expert_review", 0)
    completed_rows = len(rows) - pending_rows
    if completed_rows:
        add_issue(issues, component, "WARN", "crosswalk_rows_already_reviewed", "Some crosswalk rows are no longer pending expert review.", path, expected=0, actual=completed_rows)

    return {
        "items_file": file_state(path),
        "manifest_file": file_state(manifest_path),
        "protocol_file": file_state(protocol_path),
        "sheet_file": file_state(sheet_path),
        "candidate_rows": len(rows),
        "unique_crosswalk_ids": len(set(crosswalk_ids)),
        "duplicate_crosswalk_ids": duplicate_ids,
        "source_tasks": len(groups),
        "group_size_min": min((len(v) for v in groups.values()), default=0),
        "group_size_max": max((len(v) for v in groups.values()), default=0),
        "pending_rows": pending_rows,
        "completed_rows": completed_rows,
        "review_status_counts": statuses,
        "claim_status": "crosswalk_packet_ready_pending_expert_review",
    }


def validate_active_review_effort(exp_dir, issues):
    component = "active_review_effort"
    path = exp_dir / "05_review/active_review_human_effort_template.csv"
    briefing_path = exp_dir / "05_review/active_review_human_effort_briefing.csv"
    briefing_json_path = exp_dir / "06_release/active_review_human_effort_briefing.json"
    briefing = read_json(briefing_json_path, {}) or {}
    expected_reviewed_path = Path(briefing.get("expected_reviewed_csv") or exp_dir / "05_review/active_review_human_effort.reviewed.csv")
    rows = []
    columns = set()
    if path.exists():
        rows = read_csv_rows(path)
        columns = set(rows[0].keys()) if rows else set()
    else:
        add_issue(issues, component, "ERROR", "missing_active_effort_template", "Missing active-review effort template.", path)

    missing_columns = sorted(ACTIVE_EFFORT_REQUIRED_COLUMNS - columns)
    if missing_columns:
        add_issue(issues, component, "ERROR", "active_effort_required_columns_missing", "Missing required active effort columns.", path, expected=sorted(ACTIVE_EFFORT_REQUIRED_COLUMNS), actual=missing_columns)
    review_item_ids = [row.get("review_item_id") for row in rows]
    duplicate_ids = len(review_item_ids) - len(set(review_item_ids))
    if duplicate_ids:
        add_issue(issues, component, "ERROR", "active_effort_duplicate_ids", "Duplicate active-review effort IDs found.", path, expected=0, actual=duplicate_ids)
    human_filled_rows = sum(1 for row in rows if row.get("reviewer_id") or row.get("decision") or row.get("review_seconds"))
    if human_filled_rows:
        add_issue(issues, component, "WARN", "active_effort_rows_already_filled", "Some active effort rows already contain human response fields.", path, expected=0, actual=human_filled_rows)

    return {
        "template_file": file_state(path),
        "briefing_csv": file_state(briefing_path),
        "briefing_json": file_state(briefing_json_path),
        "expected_reviewed_csv": file_state(expected_reviewed_path),
        "template_rows": len(rows),
        "briefing_rows": briefing.get("briefing_rows"),
        "unique_review_item_ids": len(set(review_item_ids)),
        "duplicate_review_item_ids": duplicate_ids,
        "human_response_rows_present": human_filled_rows,
        "claim_status": "active_effort_packet_ready_pending_human_review",
    }


def validate_strong_resegmented_review(exp_dir, issues):
    component = "optional_strong_review"
    preview_path = exp_dir / "06_release/strong_resegmented_review_preview_summary.json"
    preflight_path = exp_dir / "06_release/strong_review_return_preflight.json"
    preview = read_json(preview_path, {}) or {}
    preflight = read_json(preflight_path, {}) or {}
    package_dir = Path(preview.get("package_dir") or exp_dir / "01_data/gold_annotation/strong_resegmented_342_max18")
    files = {
        "annotator_A": package_dir / "annotator_A.jsonl",
        "annotator_B": package_dir / "annotator_B.jsonl",
        "adjudication": package_dir / "adjudication.jsonl",
        "adjudication_draft": package_dir / "adjudication_draft.jsonl",
        "tracking_sheet": package_dir / "tracking_sheet.csv",
        "preview_csv": package_dir / "strong_review_preview.csv",
        "preview_md": package_dir / "strong_review_preview.md",
    }
    for key, path in files.items():
        if not path.exists():
            add_issue(issues, component, "ERROR", f"missing_strong_{key}", f"Missing strong review {key} file.", path)

    rows_a = read_jsonl(files["annotator_A"]) if files["annotator_A"].exists() else []
    rows_b = read_jsonl(files["annotator_B"]) if files["annotator_B"].exists() else []
    adjudication_rows = read_jsonl(files["adjudication"]) if files["adjudication"].exists() else []
    source_chunks = {row.get("source_chunk_id") for row in rows_a if row.get("source_chunk_id")}
    candidate_edges = sum(count_candidates(row) for row in rows_a)
    if len(rows_a) != len(rows_b):
        add_issue(issues, component, "ERROR", "strong_ab_row_count_mismatch", "Strong A/B annotator row counts differ.", expected=len(rows_a), actual=len(rows_b))
    if {row.get("chunk_id") for row in rows_a} != {row.get("chunk_id") for row in rows_b}:
        add_issue(issues, component, "ERROR", "strong_ab_chunk_set_mismatch", "Strong A/B chunk IDs differ.")
    if len(rows_a) != preview.get("review_unit_count"):
        add_issue(issues, component, "ERROR", "strong_review_unit_count_mismatch", "Strong review units do not match preview summary.", files["annotator_A"], expected=preview.get("review_unit_count"), actual=len(rows_a))
    if candidate_edges != preview.get("candidate_edges_total"):
        add_issue(issues, component, "ERROR", "strong_candidate_edge_count_mismatch", "Strong candidate edge total does not match preview summary.", files["annotator_A"], expected=preview.get("candidate_edges_total"), actual=candidate_edges)
    if len(source_chunks) != preview.get("source_chunk_count"):
        add_issue(issues, component, "ERROR", "strong_source_chunk_count_mismatch", "Strong source chunk count does not match preview summary.", files["annotator_A"], expected=preview.get("source_chunk_count"), actual=len(source_chunks))

    return {
        "package_id": preview.get("package_id"),
        "package_dir": rel(package_dir),
        "preview_summary": file_state(preview_path),
        "return_preflight": file_state(preflight_path),
        "input_files": {key: file_state(path) for key, path in files.items()},
        "review_unit_count": len(rows_a),
        "review_unit_count_B": len(rows_b),
        "adjudication_rows": len(adjudication_rows),
        "source_chunk_count": len(source_chunks),
        "candidate_edges_total": candidate_edges,
        "expected_review_unit_count": preview.get("review_unit_count"),
        "expected_source_chunk_count": preview.get("source_chunk_count"),
        "expected_candidate_edges_total": preview.get("candidate_edges_total"),
        "return_status": preflight.get("overall_status"),
        "claim_status": "optional_strong_packet_ready_pending_human_review",
    }


def validate_return_manifest(exp_dir, issues):
    component = "return_file_manifest"
    path = exp_dir / "05_review/human_review_master_return_files.csv"
    rows = []
    if path.exists():
        rows = read_csv_rows(path)
    else:
        add_issue(issues, component, "ERROR", "missing_master_return_manifest", "Missing master return-file manifest.", path)

    required_rows = [row for row in rows if row.get("requiredness") == "required"]
    minimum_rows = [row for row in rows if row.get("required_for_minimum") == "yes"]
    optional_strong_rows = [row for row in rows if row.get("requiredness") == "optional_strong"]
    optional_structural_rows = [row for row in rows if row.get("requiredness") == "optional_structural"]
    input_missing = []
    reviewed_present = []
    present_field_yes = []
    for row in rows:
        input_file = Path(row.get("input_file") or "")
        reviewed_file = Path(row.get("reviewed_file") or "")
        if str(input_file) and not input_file.exists():
            input_missing.append(rel(input_file))
        if str(reviewed_file) and reviewed_file.exists():
            reviewed_present.append(rel(reviewed_file))
        if row.get("present") == "yes":
            present_field_yes.append(row.get("reviewed_file"))
    if input_missing:
        add_issue(issues, component, "ERROR", "return_manifest_input_missing", "Input files listed in the return manifest are missing.", path, expected=0, actual=input_missing[:10])
    if len(reviewed_present) != len(present_field_yes):
        add_issue(issues, component, "ERROR", "return_manifest_present_field_mismatch", "Return manifest present field does not match filesystem.", path, expected=len(reviewed_present), actual=len(present_field_yes))

    return {
        "manifest_file": file_state(path),
        "rows": len(rows),
        "required_return_files": len(required_rows),
        "minimum_paper_gate_return_files": len(minimum_rows),
        "optional_strong_return_files": len(optional_strong_rows),
        "optional_structural_return_files": len(optional_structural_rows),
        "input_files_missing": len(input_missing),
        "reviewed_files_present": len(reviewed_present),
        "present_field_yes": len(present_field_yes),
        "status_counts": dict(Counter(row.get("status") for row in rows)),
        "claim_status": "return_manifest_ready_pending_human_returns",
    }


def validate_handoff_bundles(exp_dir, issues):
    component = "handoff_bundles"
    handoff_dir = exp_dir / "06_release/human_review_handoff"
    manifest_path = handoff_dir / "human_review_handoff_manifest.json"
    checksum_path = handoff_dir / "human_review_handoff_checksums.sha256"
    report_path = handoff_dir / "human_review_handoff_report.md"
    manifest = read_json(manifest_path, {}) or {}
    bundles = manifest.get("bundles") or {}
    missing_bundles = []
    bundle_rows = []
    for bundle_name, bundle in sorted(bundles.items()):
        path = Path(bundle.get("path") or "")
        exists = path.exists()
        size = path.stat().st_size if exists else 0
        if not exists:
            missing_bundles.append(bundle_name)
            add_issue(issues, component, "ERROR", "missing_handoff_bundle", "Missing handoff bundle.", path, actual=bundle_name)
        elif bundle.get("bytes") is not None and int(bundle.get("bytes")) != size:
            add_issue(issues, component, "ERROR", "handoff_bundle_size_mismatch", "Handoff bundle size differs from manifest.", path, expected=bundle.get("bytes"), actual=size)
        bundle_rows.append(
            {
                "bundle": bundle_name,
                "path": rel(path),
                "exists": exists,
                "bytes": size,
                "file_count": bundle.get("file_count"),
            }
        )

    if manifest.get("claim_status") != "handoff_ready_pending_human_review":
        add_issue(
            issues,
            component,
            "ERROR",
            "handoff_claim_status_mismatch",
            "Unexpected handoff manifest claim status.",
            manifest_path,
            expected="handoff_ready_pending_human_review",
            actual=manifest.get("claim_status"),
        )

    return {
        "manifest_file": file_state(manifest_path),
        "report_file": file_state(report_path),
        "checksums_file": file_state(checksum_path),
        "bundle_count": len(bundles),
        "missing_bundle_count": len(missing_bundles),
        "assigned_chunks": manifest.get("assigned_chunks"),
        "candidate_edges_total": manifest.get("candidate_edges_total"),
        "claim_status": manifest.get("claim_status"),
        "bundles": bundle_rows,
    }


def md_table(headers, rows):
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(header, "")) for header in headers) + " |")
    return "\n".join(lines)


def render_report(payload):
    summary = payload["summary"]
    components = payload["components"]
    component_rows = [
        {
            "component": "Minimum annotation batches",
            "status": "READY/PENDING",
            "rows": components["minimum_annotation_batches"]["annotation_input_files"],
            "key_count": f"{components['minimum_annotation_batches']['assigned_unique_chunks']} chunks / {components['minimum_annotation_batches']['candidate_edges_total']} candidate edges",
            "human_state": f"{components['minimum_annotation_batches']['reviewed_files_present']} reviewed files present",
        },
        {
            "component": "Mapping expert review",
            "status": "READY/PENDING",
            "rows": components["mapping_expert_review"]["candidate_rows"],
            "key_count": f"{components['mapping_expert_review']['source_standard_groups']} source-standard groups",
            "human_state": f"{components['mapping_expert_review']['completed_rows']} completed rows",
        },
        {
            "component": "NCS-PCF crosswalk review",
            "status": "READY/PENDING",
            "rows": components["crosswalk_expert_review"]["candidate_rows"],
            "key_count": f"{components['crosswalk_expert_review']['source_tasks']} source tasks",
            "human_state": f"{components['crosswalk_expert_review']['completed_rows']} completed rows",
        },
        {
            "component": "Active-review effort",
            "status": "READY/PENDING",
            "rows": components["active_review_effort"]["template_rows"],
            "key_count": f"{components['active_review_effort']['unique_review_item_ids']} review items",
            "human_state": f"{components['active_review_effort']['human_response_rows_present']} human-filled rows",
        },
        {
            "component": "Optional strong package",
            "status": "READY/PENDING",
            "rows": components["optional_strong_review"]["review_unit_count"],
            "key_count": f"{components['optional_strong_review']['source_chunk_count']} source chunks / {components['optional_strong_review']['candidate_edges_total']} candidate edges",
            "human_state": components["optional_strong_review"]["return_status"],
        },
        {
            "component": "Return-file manifest",
            "status": "READY/PENDING",
            "rows": components["return_file_manifest"]["rows"],
            "key_count": f"{components['return_file_manifest']['required_return_files']} required / {components['return_file_manifest']['minimum_paper_gate_return_files']} minimum",
            "human_state": f"{components['return_file_manifest']['reviewed_files_present']} returned files",
        },
        {
            "component": "Handoff bundles",
            "status": "READY",
            "rows": components["handoff_bundles"]["bundle_count"],
            "key_count": f"{components['handoff_bundles']['assigned_chunks']} chunks / {components['handoff_bundles']['candidate_edges_total']} candidate edges",
            "human_state": components["handoff_bundles"]["claim_status"],
        },
    ]
    issue_rows = payload.get("issues") or []
    if issue_rows:
        issue_table = md_table(
            ["severity", "component", "code", "detail", "path"],
            [
                {
                    "severity": issue["severity"],
                    "component": issue["component"],
                    "code": issue["code"],
                    "detail": issue["detail"],
                    "path": issue["path"],
                }
                for issue in issue_rows
            ],
        )
    else:
        issue_table = "No blocking integrity issues were found."

    lines = [
        "# CAPE-KG Human Review Packet Integrity Report",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Experiment: `{payload['experiment_dir']}`",
        f"Overall status: `{payload['overall_status']}`",
        f"Claim status: `{payload['claim_status']}`",
        "",
        "이 보고서는 human-gold/IAA/전문가 검수 결과를 대체하지 않습니다.",
        "목적은 사람이 검수하기 전에 배포된 입력 파일, return-file manifest, handoff bundle이 구조적으로 빠짐없이 준비되었는지 확인하는 것입니다.",
        "",
        "## Summary",
        "",
        f"- Integrity errors: {summary['integrity_error_count']}",
        f"- Integrity warnings: {summary['integrity_warning_count']}",
        f"- Minimum annotation chunks assigned: {summary['minimum_annotation_chunks']}",
        f"- Minimum annotation candidate edges: {summary['minimum_annotation_candidate_edges']}",
        f"- Mapping review rows: {summary['mapping_review_rows']}",
        f"- Crosswalk review rows: {summary['crosswalk_review_rows']}",
        f"- Active-review effort rows: {summary['active_review_effort_rows']}",
        f"- Optional strong review units: {summary['optional_strong_review_units']}",
        f"- Required human return files currently present: {summary['required_reviewed_files_present']} / {summary['required_reviewed_files_expected']}",
        "",
        "## Component Readiness",
        "",
        md_table(["component", "status", "rows", "key_count", "human_state"], component_rows),
        "",
        "## Interpretation",
        "",
        "- `READY/PENDING`은 입력 패킷은 준비되었지만 사람의 reviewed/adjudicated 파일이 아직 없다는 뜻입니다.",
        "- 현재 단계에서 없는 reviewed 파일은 오류가 아닙니다. 오류는 입력 파일 누락, ID 불일치, 행 수 불일치, manifest 불일치입니다.",
        "- 논문 claim으로 사용할 수 있는 human-gold 성능, IAA, expert mapping metric은 사람이 return 파일을 작성하고 import/preflight를 통과한 뒤에만 생성됩니다.",
        "",
        "## Issues",
        "",
        issue_table,
        "",
        "## Output Files",
        "",
        f"- JSON: `{payload['outputs']['json']}`",
        f"- Markdown: `{payload['outputs']['markdown']}`",
        f"- Issue CSV: `{payload['outputs']['issue_csv']}`",
        "",
    ]
    return "\n".join(lines)


def build_payload(exp_dir):
    exp_dir = Path(exp_dir)
    release_dir = exp_dir / "06_release"
    review_dir = exp_dir / "05_review"
    issues = []
    components = {
        "minimum_annotation_batches": validate_minimum_annotation_batches(exp_dir, issues),
        "mapping_expert_review": validate_mapping_review(exp_dir, issues),
        "crosswalk_expert_review": validate_crosswalk_review(exp_dir, issues),
        "active_review_effort": validate_active_review_effort(exp_dir, issues),
        "optional_strong_review": validate_strong_resegmented_review(exp_dir, issues),
        "return_file_manifest": validate_return_manifest(exp_dir, issues),
        "handoff_bundles": validate_handoff_bundles(exp_dir, issues),
    }
    error_count = sum(1 for issue in issues if issue.get("severity") == "ERROR")
    warning_count = sum(1 for issue in issues if issue.get("severity") == "WARN")
    overall_status = "FAIL" if error_count else "PASS"
    output_json = release_dir / "human_review_packet_integrity.json"
    output_md = release_dir / "human_review_packet_integrity.md"
    issue_csv = review_dir / "human_review_packet_integrity_issues.csv"
    summary = {
        "integrity_error_count": error_count,
        "integrity_warning_count": warning_count,
        "minimum_annotation_input_files": components["minimum_annotation_batches"]["annotation_input_files"],
        "minimum_annotation_chunks": components["minimum_annotation_batches"]["assigned_unique_chunks"],
        "minimum_annotation_candidate_edges": components["minimum_annotation_batches"]["candidate_edges_total"],
        "mapping_review_rows": components["mapping_expert_review"]["candidate_rows"],
        "mapping_review_source_standard_groups": components["mapping_expert_review"]["source_standard_groups"],
        "crosswalk_review_rows": components["crosswalk_expert_review"]["candidate_rows"],
        "crosswalk_review_source_tasks": components["crosswalk_expert_review"]["source_tasks"],
        "active_review_effort_rows": components["active_review_effort"]["template_rows"],
        "optional_strong_review_units": components["optional_strong_review"]["review_unit_count"],
        "optional_strong_source_chunks": components["optional_strong_review"]["source_chunk_count"],
        "optional_strong_candidate_edges": components["optional_strong_review"]["candidate_edges_total"],
        "required_reviewed_files_expected": components["return_file_manifest"]["required_return_files"],
        "required_reviewed_files_present": components["return_file_manifest"]["reviewed_files_present"],
        "handoff_bundle_count": components["handoff_bundles"]["bundle_count"],
        "missing_handoff_bundle_count": components["handoff_bundles"]["missing_bundle_count"],
    }
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": rel(exp_dir),
        "overall_status": overall_status,
        "claim_status": "human_review_packet_integrity_ready_pending_human_returns"
        if overall_status == "PASS"
        else "human_review_packet_integrity_failed",
        "summary": summary,
        "components": components,
        "issues": issues,
        "outputs": {
            "json": rel(output_json),
            "markdown": rel(output_md),
            "issue_csv": rel(issue_csv),
        },
    }


def run(args):
    payload = build_payload(args.experiment_dir)
    output_json = Path(payload["outputs"]["json"])
    output_md = Path(payload["outputs"]["markdown"])
    issue_csv = Path(payload["outputs"]["issue_csv"])
    write_json(output_json, payload)
    write_text(output_md, render_report(payload))
    write_csv(
        issue_csv,
        payload["issues"],
        ["component", "severity", "code", "detail", "path", "expected", "actual"],
    )
    print(
        json.dumps(
            {
                "json": payload["outputs"]["json"],
                "markdown": payload["outputs"]["markdown"],
                "issue_csv": payload["outputs"]["issue_csv"],
                "overall_status": payload["overall_status"],
                "claim_status": payload["claim_status"],
                "integrity_error_count": payload["summary"]["integrity_error_count"],
                "integrity_warning_count": payload["summary"]["integrity_warning_count"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if payload["overall_status"] != "PASS":
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
