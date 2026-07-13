#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Preflight optional strong 300+ CAPE-KG human-review returns."""

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from import_cape_gold_annotation import (
    key_for,
    load_chunk_context,
    load_schema,
    read_rows,
    status_of,
    validate_import,
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


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


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


def status_counts(rows):
    counts = Counter()
    for row in rows:
        counts[status_of(row) or "missing"] += 1
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
    status = status_of(row).strip().lower()
    if status not in COMPLETED_ANNOTATION_STATUSES:
        return []

    chunk_id = key_for(row)
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


def completed_keys(rows, completed_statuses):
    return {
        key_for(row)
        for row in rows
        if key_for(row) and status_of(row).strip().lower() in completed_statuses
    }


def compare_keys(expected_rows, reviewed_rows, scope):
    expected_keys = {key_for(row) for row in expected_rows if key_for(row)}
    reviewed_keys = {key_for(row) for row in reviewed_rows if key_for(row)}
    issues = []
    missing = sorted(expected_keys - reviewed_keys)
    extra = sorted(reviewed_keys - expected_keys)
    if missing:
        issues.append(
            {
                "level": "warning",
                "code": f"{scope}_missing_expected_rows",
                "message": f"Reviewed file is missing {len(missing)} expected rows.",
                "sample": missing[:10],
            }
        )
    if extra:
        issues.append(
            {
                "level": "error",
                "code": f"{scope}_extra_rows",
                "message": f"Reviewed file contains {len(extra)} rows outside the expected package.",
                "sample": extra[:10],
            }
        )
    return issues


def validate_annotation_file(package_dir, annotator, schema, chunk_context):
    input_file = package_dir / f"annotator_{annotator}.jsonl"
    reviewed_file = package_dir / f"annotator_{annotator}_edited.jsonl"
    summary = {
        "annotator": annotator,
        "input_file": rel(input_file),
        "reviewed_file": rel(reviewed_file),
        "present": reviewed_file.exists(),
        "status": "missing_reviewed_file",
        "expected_rows": 0,
        "reviewed_rows": 0,
        "completed_chunks": 0,
        "status_counts": {},
        "ready_for_strong_iaa": False,
        "errors": [],
        "warnings": [],
        "error_count": 0,
        "warning_count": 0,
    }
    if not input_file.exists():
        summary["status"] = "missing_input_file"
        summary["errors"] = [{"level": "error", "code": "missing_input_file", "path": rel(input_file)}]
        summary["error_count"] = 1
        return summary

    input_rows = read_rows(input_file)
    summary["expected_rows"] = len(input_rows)
    if not reviewed_file.exists():
        return summary

    reviewed_rows = read_rows(reviewed_file)
    summary["reviewed_rows"] = len(reviewed_rows)
    summary["status_counts"] = status_counts(reviewed_rows)

    issues = []
    issues.extend(compare_keys(input_rows, reviewed_rows, f"annotator_{annotator}"))
    issues.extend(validate_import(input_rows, reviewed_rows, schema, chunk_context, allow_partial=True))
    expected_annotator = str(annotator).strip()
    for row in reviewed_rows:
        row_status = status_of(row).strip().lower()
        row_annotator = str(row.get("annotator_id") or "").strip()
        if row_annotator and row_annotator != expected_annotator:
            issues.append(
                {
                    "level": "error",
                    "code": "annotator_id_mismatch",
                    "message": (
                        f"Reviewed row annotator_id `{row_annotator}` does not match assigned annotator "
                        f"`{expected_annotator}`."
                    ),
                    "chunk_id": key_for(row),
                    "line": row_line(row),
                }
            )
        if row_status in COMPLETED_ANNOTATION_STATUSES and not row_annotator:
            issues.append(
                {
                    "level": "error",
                    "code": "completed_annotation_missing_annotator_id",
                    "message": "Rows marked completed or needs_adjudication must include annotator_id.",
                    "chunk_id": key_for(row),
                    "line": row_line(row),
                }
            )
        issues.extend(annotation_candidate_coverage_issues(row))
    errors = [item for item in issues if item.get("level") == "error"]
    warnings = [item for item in issues if item.get("level") == "warning"]
    completed = completed_keys(reviewed_rows, COMPLETED_ANNOTATION_STATUSES)
    summary["completed_chunks"] = len(completed)
    summary["errors"] = errors[:200]
    summary["warnings"] = warnings[:200]
    summary["error_count"] = len(errors)
    summary["warning_count"] = len(warnings)
    if errors:
        summary["status"] = "failed_validation"
        return summary
    summary["status"] = "validated"
    summary["ready_for_strong_iaa"] = len(completed) >= 300
    return summary


def validate_adjudication_file(package_dir, schema, chunk_context):
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
        "status_counts": {},
        "ready_for_strong_adjudication_import": False,
        "errors": [],
        "warnings": [],
        "error_count": 0,
        "warning_count": 0,
    }
    if not input_file.exists() or not target_file.exists():
        summary["status"] = "missing_input_or_target"
        summary["errors"] = [
            {
                "level": "error",
                "code": "missing_input_or_target",
                "input_file_exists": input_file.exists(),
                "target_file_exists": target_file.exists(),
            }
        ]
        summary["error_count"] = 1
        return summary

    input_rows = read_rows(input_file)
    target_rows = read_rows(target_file)
    summary["expected_rows"] = len(input_rows)
    if not reviewed_file.exists():
        return summary

    reviewed_rows = read_rows(reviewed_file)
    summary["reviewed_rows"] = len(reviewed_rows)
    summary["status_counts"] = status_counts(reviewed_rows)

    issues = []
    issues.extend(compare_keys(input_rows, reviewed_rows, "adjudication"))
    issues.extend(validate_import(target_rows, reviewed_rows, schema, chunk_context, allow_partial=True))
    for row in reviewed_rows:
        row_status = status_of(row).strip().lower()
        if row_status in COMPLETED_ADJUDICATION_STATUSES and not str(row.get("adjudicator_id") or "").strip():
            issues.append(
                {
                    "level": "error",
                    "code": "completed_adjudication_missing_adjudicator_id",
                    "message": "Completed adjudication rows must include adjudicator_id.",
                    "chunk_id": key_for(row),
                    "line": row_line(row),
                }
            )
    errors = [item for item in issues if item.get("level") == "error"]
    warnings = [item for item in issues if item.get("level") == "warning"]
    completed = completed_keys(reviewed_rows, COMPLETED_ADJUDICATION_STATUSES)
    summary["completed_adjudicated_chunks"] = len(completed)
    summary["errors"] = errors[:200]
    summary["warnings"] = warnings[:200]
    summary["error_count"] = len(errors)
    summary["warning_count"] = len(warnings)
    if errors:
        summary["status"] = "failed_validation"
        return summary
    summary["status"] = "validated"
    summary["ready_for_strong_adjudication_import"] = len(completed) >= 300
    return summary


def overall_status(annotation_a, annotation_b, adjudication):
    if annotation_a["error_count"] or annotation_b["error_count"] or adjudication["error_count"]:
        return "failed_validation"
    if (
        annotation_a["ready_for_strong_iaa"]
        and annotation_b["ready_for_strong_iaa"]
        and adjudication["ready_for_strong_adjudication_import"]
    ):
        return "strong_annotation_and_adjudication_returns_ready"
    if annotation_a["ready_for_strong_iaa"] and annotation_b["ready_for_strong_iaa"]:
        return "strong_annotation_returns_ready_adjudication_pending"
    if annotation_a["present"] or annotation_b["present"] or adjudication["present"]:
        return "partial_strong_returns_validated"
    return "pending_strong_human_returns"


def render_report(payload):
    summary = payload["summary"]
    a = payload["annotation_returns"]["A"]
    b = payload["annotation_returns"]["B"]
    adjudication = payload["adjudication_return"]
    policy = payload.get("validation_policy") or {}
    lines = [
        "# CAPE-KG Optional Strong 300+ Return Preflight",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Overall status: `{payload['overall_status']}`",
        f"Package: `{payload['package']}`",
        "",
        "This preflight checks optional strong-paper-scale reviewed files before any manual import. It does not change the 11-file minimum paper gate and is not paper-claimable human-gold evidence until reviewed files are actually imported, IAA is recomputed, and adjudication/scoring are completed.",
        "",
        "## Validation Policy",
        "",
        f"- Annotator file identity check: `{policy.get('annotator_file_identity_check')}`",
        f"- Completed candidate coverage check: `{policy.get('completed_candidate_coverage_check')}`",
        f"- Needs-adjudication comments required: `{policy.get('needs_adjudication_comments_required')}`",
        f"- Completed adjudication adjudicator id required: `{policy.get('completed_adjudication_adjudicator_id_required')}`",
        "",
        "## Summary",
        "",
        "| Item | Value |",
        "|---|---:|",
        f"| Expected review units | {summary['expected_review_units']} |",
        f"| Annotator A present | {a['present']} |",
        f"| Annotator B present | {b['present']} |",
        f"| A completed chunks | {a['completed_chunks']} |",
        f"| B completed chunks | {b['completed_chunks']} |",
        f"| Paired completed chunks | {summary['paired_completed_chunks']} |",
        f"| Adjudication present | {adjudication['present']} |",
        f"| Completed adjudicated chunks | {adjudication['completed_adjudicated_chunks']} |",
        f"| Ready for strong IAA | {summary['ready_for_strong_iaa']} |",
        f"| Ready for strong adjudication import | {adjudication['ready_for_strong_adjudication_import']} |",
        f"| Error count | {summary['error_count']} |",
        f"| Warning count | {summary['warning_count']} |",
        "",
        "## Expected Reviewed Files",
        "",
        f"- Annotator A: `{a['reviewed_file']}`",
        f"- Annotator B: `{b['reviewed_file']}`",
        f"- Adjudication: `{adjudication['reviewed_file']}`",
        "",
        "## Next Commands After Returns Arrive",
        "",
        "```bash",
        "python3 scripts/validate_cape_strong_review_returns.py \\",
        "  --experiment-dir experiments/cape_kg_eacl_20260627",
        "",
        "python3 scripts/compute_cape_annotation_iaa.py \\",
        f"  --annotator-a {payload['package_dir']}/annotator_A_edited.jsonl \\",
        f"  --annotator-b {payload['package_dir']}/annotator_B_edited.jsonl \\",
        f"  --output-dir {payload['package_dir']}/iaa_strong_resegmented",
        "```",
        "",
    ]
    errors = a["errors"] + b["errors"] + adjudication["errors"]
    warnings = a["warnings"] + b["warnings"] + adjudication["warnings"]
    if errors:
        lines += ["## Errors", ""]
        for item in errors[:50]:
            lines.append(f"- `{item}`")
        lines.append("")
    if warnings:
        lines += ["## Warnings", ""]
        for item in warnings[:50]:
            lines.append(f"- `{item}`")
        lines.append("")
    return "\n".join(lines)


def build_payload(exp_dir):
    exp_dir = Path(exp_dir)
    expansion = read_json(exp_dir / "01_data/gold_annotation/annotation_expansion_manifest.json", {}) or {}
    package = expansion.get("strong_resegmented_package") or "strong_resegmented_342_max18"
    package_dir = exp_dir / "01_data/gold_annotation" / package
    schema = load_schema(exp_dir)
    chunk_context, chunk_context_issues = load_chunk_context(exp_dir)

    annotation_a = validate_annotation_file(package_dir, "A", schema, chunk_context)
    annotation_b = validate_annotation_file(package_dir, "B", schema, chunk_context)
    adjudication = validate_adjudication_file(package_dir, schema, chunk_context)
    completed_a = set()
    completed_b = set()
    for annotator, target in (("A", completed_a), ("B", completed_b)):
        reviewed_file = package_dir / f"annotator_{annotator}_edited.jsonl"
        if reviewed_file.exists():
            target.update(completed_keys(read_rows(reviewed_file), COMPLETED_ANNOTATION_STATUSES))
    status = overall_status(annotation_a, annotation_b, adjudication)
    error_count = annotation_a["error_count"] + annotation_b["error_count"] + adjudication["error_count"]
    warning_count = annotation_a["warning_count"] + annotation_b["warning_count"] + adjudication["warning_count"]
    if chunk_context_issues:
        warning_count += len(chunk_context_issues)
    summary = {
        "expected_review_units": int(expansion.get("strong_resegmented_chunk_count") or annotation_a.get("expected_rows") or 0),
        "paired_completed_chunks": len(completed_a & completed_b),
        "ready_for_strong_iaa": annotation_a["ready_for_strong_iaa"] and annotation_b["ready_for_strong_iaa"] and len(completed_a & completed_b) >= 300,
        "ready_for_strong_claim_after_import": status == "strong_annotation_and_adjudication_returns_ready",
        "error_count": error_count,
        "warning_count": warning_count,
    }
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": rel(exp_dir),
        "package": package,
        "package_dir": rel(package_dir),
        "overall_status": status,
        "claim_status": "strong_return_preflight_not_paper_evidence",
        "validation_policy": {
            "annotator_file_identity_check": True,
            "completed_candidate_coverage_check": True,
            "needs_adjudication_comments_required": True,
            "completed_adjudication_adjudicator_id_required": True,
        },
        "summary": summary,
        "chunk_context_issue_count": len(chunk_context_issues),
        "chunk_context_issues": chunk_context_issues[:50],
        "annotation_returns": {"A": annotation_a, "B": annotation_b},
        "adjudication_return": adjudication,
        "outputs": {
            "json": rel(exp_dir / "06_release/strong_review_return_preflight.json"),
            "markdown": rel(exp_dir / "06_release/strong_review_return_preflight.md"),
        },
    }


def run(args):
    payload = build_payload(args.experiment_dir)
    outputs = payload["outputs"]
    write_json(outputs["json"], payload)
    write_text(outputs["markdown"], render_report(payload))
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if payload["overall_status"] == "failed_validation":
        raise SystemExit(2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
