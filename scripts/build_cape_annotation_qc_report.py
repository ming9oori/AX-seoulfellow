#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build annotation QC and gate worklists for CAPE-KG human-gold packages."""

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
COMPLETED_ANNOTATION_STATUSES = {"completed", "needs_adjudication", "adjudicated"}
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


def read_jsonl_with_issues(path):
    path = Path(path)
    rows = []
    issues = []
    if not path.exists():
        issues.append(issue("error", "missing_file", path, "", f"Required file does not exist: {path}"))
        return rows, issues
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            raw = line.strip()
            if not raw:
                continue
            try:
                rows.append(json.loads(raw))
            except json.JSONDecodeError as exc:
                issues.append(issue("error", "json_decode_error", path, "", f"Line {line_no}: {exc}"))
    return rows, issues


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
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def norm(value):
    return str(value or "").strip().lower()


def issue(severity, code, path, chunk_id, message):
    return {
        "severity": severity,
        "code": code,
        "file": str(path) if path else "",
        "chunk_id": chunk_id or "",
        "message": message,
    }


def is_annotation_complete(row):
    return norm(row.get("annotation_status")) in COMPLETED_ANNOTATION_STATUSES


def is_adjudication_complete(row):
    return norm(row.get("adjudication_status")) in COMPLETED_ADJUDICATION_STATUSES


def rows_by_chunk(rows, path, issues):
    output = {}
    counts = Counter()
    for row in rows:
        chunk_id = row.get("chunk_id")
        if not chunk_id:
            issues.append(issue("error", "missing_chunk_id", path, "", "Row has no chunk_id."))
            continue
        counts[chunk_id] += 1
        if chunk_id not in output:
            output[chunk_id] = row
    for chunk_id, count in counts.items():
        if count > 1:
            issues.append(issue("error", "duplicate_chunk_row", path, chunk_id, f"Chunk appears {count} times."))
    return output


def count_gold_items(adjudication_rows):
    nodes = 0
    edges = 0
    evidence = set()
    for row in adjudication_rows:
        if not is_adjudication_complete(row):
            continue
        gold_nodes = row.get("adjudicated_gold_nodes") or []
        gold_edges = row.get("adjudicated_gold_edges") or []
        if isinstance(gold_nodes, list):
            nodes += len([item for item in gold_nodes if isinstance(item, dict)])
            for item in gold_nodes:
                if isinstance(item, dict):
                    for ev in item.get("evidence_anchor_ids") or item.get("evidence_ids") or []:
                        evidence.add(str(ev))
        if isinstance(gold_edges, list):
            edges += len([item for item in gold_edges if isinstance(item, dict)])
            for item in gold_edges:
                if isinstance(item, dict):
                    for ev in item.get("evidence_anchor_ids") or item.get("evidence_ids") or []:
                        evidence.add(str(ev))
    return {
        "adjudicated_gold_nodes": nodes,
        "adjudicated_gold_edges": edges,
        "adjudicated_gold_evidence_links": len(evidence),
        "gold_item_count_for_readiness": nodes + edges + len(evidence),
    }


def load_batch_chunk_map(exp_dir, package):
    summary = read_json(Path(exp_dir) / "06_release/annotation_batch_assignment_summary.json", {}) or {}
    chunk_to_batch = {}
    for batch in summary.get("batches", []):
        if batch.get("package") != package:
            continue
        for chunk_id in batch.get("chunk_ids", []):
            chunk_to_batch[chunk_id] = batch.get("batch_id")
    return chunk_to_batch, summary


def package_qc(exp_dir, package):
    package_dir = Path(exp_dir) / "01_data/gold_annotation" / package
    paths = {
        "annotator_A": package_dir / "annotator_A.jsonl",
        "annotator_B": package_dir / "annotator_B.jsonl",
        "adjudication": package_dir / "adjudication.jsonl",
    }
    issues = []
    a_rows, a_issues = read_jsonl_with_issues(paths["annotator_A"])
    b_rows, b_issues = read_jsonl_with_issues(paths["annotator_B"])
    adj_rows, adj_issues = read_jsonl_with_issues(paths["adjudication"])
    issues.extend(a_issues)
    issues.extend(b_issues)
    issues.extend(adj_issues)

    a_by_chunk = rows_by_chunk(a_rows, paths["annotator_A"], issues)
    b_by_chunk = rows_by_chunk(b_rows, paths["annotator_B"], issues)
    adj_by_chunk = rows_by_chunk(adj_rows, paths["adjudication"], issues)
    chunk_ids = sorted(set(a_by_chunk) | set(b_by_chunk) | set(adj_by_chunk))
    chunk_to_batch, batch_summary = load_batch_chunk_map(exp_dir, package)

    missing_a = sorted(set(chunk_ids) - set(a_by_chunk))
    missing_b = sorted(set(chunk_ids) - set(b_by_chunk))
    missing_adj = sorted(set(chunk_ids) - set(adj_by_chunk))
    for chunk_id in missing_a:
        issues.append(issue("error", "missing_annotator_a_row", paths["annotator_A"], chunk_id, "Chunk is absent from annotator_A.jsonl."))
    for chunk_id in missing_b:
        issues.append(issue("error", "missing_annotator_b_row", paths["annotator_B"], chunk_id, "Chunk is absent from annotator_B.jsonl."))
    for chunk_id in missing_adj:
        issues.append(issue("error", "missing_adjudication_row", paths["adjudication"], chunk_id, "Chunk is absent from adjudication.jsonl."))

    worklist = []
    workflow_counts = Counter()
    for chunk_id in chunk_ids:
        a = a_by_chunk.get(chunk_id, {})
        b = b_by_chunk.get(chunk_id, {})
        adj = adj_by_chunk.get(chunk_id, {})
        a_done = is_annotation_complete(a)
        b_done = is_annotation_complete(b)
        adj_done = is_adjudication_complete(adj)
        if adj_done:
            workflow = "adjudicated"
            next_action = "none"
        elif a_done and b_done:
            workflow = "ready_for_adjudication"
            next_action = "adjudicate"
        elif a_done:
            workflow = "awaiting_annotator_B"
            next_action = "complete annotator B"
        elif b_done:
            workflow = "awaiting_annotator_A"
            next_action = "complete annotator A"
        else:
            workflow = "pending_two_annotators"
            next_action = "complete annotator A and B"
        workflow_counts[workflow] += 1
        template = a or b or adj
        worklist.append(
            {
                "package": package,
                "chunk_id": chunk_id,
                "batch_id": chunk_to_batch.get(chunk_id, ""),
                "workflow_status": workflow,
                "next_action": next_action,
                "annotator_A_status": a.get("annotation_status", ""),
                "annotator_B_status": b.get("annotation_status", ""),
                "adjudication_status": adj.get("adjudication_status", ""),
                "candidate_edges": template.get("silver_candidate_edge_count", ""),
                "page_start": template.get("page_start", ""),
                "page_end": template.get("page_end", ""),
            }
        )

    assigned_chunks = set(chunk_to_batch)
    unassigned_chunks = sorted(set(chunk_ids) - assigned_chunks)
    assigned_missing_from_package = sorted(assigned_chunks - set(chunk_ids))
    for chunk_id in unassigned_chunks:
        if chunk_to_batch:
            issues.append(issue("info", "chunk_not_in_priority_batch", package_dir, chunk_id, "Chunk is in package but not assigned to a priority batch."))
    for chunk_id in assigned_missing_from_package:
        issues.append(issue("error", "batch_chunk_missing_from_package", package_dir, chunk_id, "Priority batch chunk is absent from package files."))

    gold_counts = count_gold_items(adj_rows)
    completed_a = sum(1 for row in a_rows if is_annotation_complete(row))
    completed_b = sum(1 for row in b_rows if is_annotation_complete(row))
    paired_completed = sum(1 for chunk_id in chunk_ids if is_annotation_complete(a_by_chunk.get(chunk_id, {})) and is_annotation_complete(b_by_chunk.get(chunk_id, {})))
    adjudicated = sum(1 for row in adj_rows if is_adjudication_complete(row))
    error_count = sum(1 for row in issues if row["severity"] == "error")
    warning_count = sum(1 for row in issues if row["severity"] == "warning")
    minimum_gate_pass = (
        package == "full_120"
        and adjudicated >= 100
        and gold_counts["gold_item_count_for_readiness"] >= 500
        and error_count == 0
    )

    return {
        "package": package,
        "package_dir": str(package_dir),
        "files": {name: str(path) for name, path in paths.items()},
        "chunk_count": len(chunk_ids),
        "annotator_A_rows": len(a_rows),
        "annotator_B_rows": len(b_rows),
        "adjudication_rows": len(adj_rows),
        "annotator_A_completed_chunks": completed_a,
        "annotator_B_completed_chunks": completed_b,
        "paired_completed_chunks": paired_completed,
        "ready_for_adjudication_chunks": workflow_counts.get("ready_for_adjudication", 0),
        "adjudicated_chunks": adjudicated,
        "workflow_status_counts": dict(sorted(workflow_counts.items())),
        "batch_assigned_chunks": len(assigned_chunks),
        "batch_assignment_summary_file": str(Path(exp_dir) / "06_release/annotation_batch_assignment_summary.json") if batch_summary else None,
        "batch_chunks_missing_from_package": len(assigned_missing_from_package),
        "package_chunks_not_in_priority_batch": len(unassigned_chunks),
        "gold_counts": gold_counts,
        "issue_count": len(issues),
        "error_count": error_count,
        "warning_count": warning_count,
        "minimum_gate_pass": minimum_gate_pass,
        "issues": issues,
        "worklist": sorted(
            worklist,
            key=lambda row: (
                row["workflow_status"] == "adjudicated",
                row["workflow_status"] == "ready_for_adjudication",
                row.get("batch_id") or "zzzz",
                row["chunk_id"],
            ),
        ),
    }


def render_report(payload):
    lines = [
        "# CAPE-KG Annotation QC Report",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Experiment: `{payload['experiment_dir']}`",
        "",
        "## Gate Summary",
        "",
        f"- Overall QC status: {payload['overall_qc_status']}",
        f"- Full package minimum gate: {payload['full_120_minimum_gate_status']}",
        f"- Total errors: {payload['total_error_count']}",
        f"- Total warnings: {payload['total_warning_count']}",
        "",
    ]
    for package in payload["packages"]:
        lines += [
            f"## {package['package']}",
            "",
            f"- Chunks: {package['chunk_count']}",
            f"- Annotator A completed: {package['annotator_A_completed_chunks']}",
            f"- Annotator B completed: {package['annotator_B_completed_chunks']}",
            f"- Paired completed chunks: {package['paired_completed_chunks']}",
            f"- Ready for adjudication: {package['ready_for_adjudication_chunks']}",
            f"- Adjudicated chunks: {package['adjudicated_chunks']}",
            f"- Gold item count: {package['gold_counts']['gold_item_count_for_readiness']}",
            f"- Batch-assigned chunks: {package['batch_assigned_chunks']}",
            f"- Errors: {package['error_count']}",
            f"- Warnings: {package['warning_count']}",
            f"- Workflow counts: `{package['workflow_status_counts']}`",
            "",
        ]
    lines += [
        "## Required Next Actions",
        "",
    ]
    full = next((row for row in payload["packages"] if row["package"] == "full_120"), None)
    if full:
        if full["paired_completed_chunks"] < 100:
            lines.append(f"- Complete two annotator files for at least {100 - full['paired_completed_chunks']} more full_120 chunks.")
        if full["adjudicated_chunks"] < 100:
            lines.append(f"- Adjudicate at least {100 - full['adjudicated_chunks']} more full_120 chunks.")
        if full["gold_counts"]["gold_item_count_for_readiness"] < 500:
            lines.append(f"- Add at least {500 - full['gold_counts']['gold_item_count_for_readiness']} more adjudicated gold node/edge/evidence items.")
    if payload["total_error_count"]:
        lines.append("- Resolve QC errors before importing annotations into claimable human-gold metrics.")
    lines += [
        "",
        f"Issue CSV: `{payload['issue_csv']}`",
        f"Gate worklist CSV: `{payload['gate_worklist_csv']}`",
        "",
        "Pending rows are not treated as gold labels. This QC report only verifies annotation workflow readiness and import safety.",
    ]
    return "\n".join(lines) + "\n"


def build(exp_dir, packages):
    exp_dir = Path(exp_dir)
    package_reports = [package_qc(exp_dir, package) for package in packages]
    issues = []
    worklist = []
    for package in package_reports:
        issues.extend({**row, "package": package["package"]} for row in package["issues"])
        worklist.extend(package["worklist"])
    total_errors = sum(package["error_count"] for package in package_reports)
    total_warnings = sum(package["warning_count"] for package in package_reports)
    full = next((row for row in package_reports if row["package"] == "full_120"), None)
    full_gate = "pass" if full and full["minimum_gate_pass"] else "pending_human_annotation"
    overall = "pass" if total_errors == 0 else "action_required"
    if full_gate != "pass":
        overall = "pending_human_annotation"

    issue_csv = exp_dir / "05_review/annotation_qc_issues.csv"
    worklist_csv = exp_dir / "05_review/annotation_completion_gate_worklist.csv"
    summary_json = exp_dir / "06_release/annotation_qc_summary.json"
    report_md = exp_dir / "06_release/annotation_qc_report.md"

    issue_fieldnames = ["package", "severity", "code", "file", "chunk_id", "message"]
    worklist_fieldnames = [
        "package",
        "chunk_id",
        "batch_id",
        "workflow_status",
        "next_action",
        "annotator_A_status",
        "annotator_B_status",
        "adjudication_status",
        "candidate_edges",
        "page_start",
        "page_end",
    ]
    write_csv(issue_csv, issues, issue_fieldnames)
    write_csv(worklist_csv, worklist, worklist_fieldnames)

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "packages": [
            {key: value for key, value in package.items() if key not in {"issues", "worklist"}}
            for package in package_reports
        ],
        "total_error_count": total_errors,
        "total_warning_count": total_warnings,
        "overall_qc_status": overall,
        "full_120_minimum_gate_status": full_gate,
        "issue_csv": str(issue_csv),
        "gate_worklist_csv": str(worklist_csv),
        "summary_json": str(summary_json),
        "report_md": str(report_md),
    }
    write_json(summary_json, payload)
    write_text(report_md, render_report(payload))
    return payload


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--packages", default="pilot_30,full_120")
    args = parser.parse_args()
    packages = [item.strip() for item in args.packages.split(",") if item.strip()]
    payload = build(args.experiment_dir, packages)
    print(
        json.dumps(
            {
                "event": "annotation_qc_written",
                "experiment_dir": payload["experiment_dir"],
                "overall_qc_status": payload["overall_qc_status"],
                "full_120_minimum_gate_status": payload["full_120_minimum_gate_status"],
                "total_error_count": payload["total_error_count"],
                "total_warning_count": payload["total_warning_count"],
                "report_md": payload["report_md"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
