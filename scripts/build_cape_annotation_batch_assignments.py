#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build partial human-gold annotation assignment batches from the priority queue."""

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_PACKAGE = "full_120"
ANNOTATORS = ("A", "B")

OVERVIEW_FIELDNAMES = [
    "batch_id",
    "package",
    "rank_start",
    "rank_end",
    "chunk_count",
    "candidate_edges_total",
    "active_review_items_total",
    "high_impact_chunks",
    "chunk_ids",
    "annotator_A_file",
    "annotator_B_file",
    "tracking_sheet",
    "readme",
]

TRACKING_FIELDNAMES = [
    "batch_id",
    "rank",
    "chunk_id",
    "chapter_id",
    "section_id",
    "page_start",
    "page_end",
    "priority_score",
    "priority_reason",
    "silver_candidate_edge_count",
    "active_review_items",
    "review_error_items",
    "high_impact_items",
    "workflow_status",
    "annotator_A_status",
    "annotator_B_status",
    "adjudication_status",
]


def read_jsonl(path):
    rows = []
    path = Path(path)
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path, rows, fieldnames):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def as_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def chunk_key(row):
    return str(row.get("chunk_id") or "").strip()


def select_priority_rows(exp_dir, package, max_chunks):
    queue_path = exp_dir / "05_review/human_gold_annotation_priority_queue.jsonl"
    rows = read_jsonl(queue_path)
    selected = [
        row for row in rows
        if row.get("package") == package and row.get("workflow_status") != "adjudicated" and chunk_key(row)
    ]
    selected.sort(key=lambda row: as_int(row.get("rank"), 999999))
    return selected[:max_chunks], queue_path


def load_annotator_rows(exp_dir, package, annotator):
    path = exp_dir / "01_data/gold_annotation" / package / f"annotator_{annotator}.jsonl"
    rows = read_jsonl(path)
    return path, {chunk_key(row): row for row in rows if chunk_key(row)}


def import_command(exp_dir, target_file, reviewed_file, apply=False):
    cmd = (
        f"python3 scripts/import_cape_gold_annotation.py --experiment-dir {exp_dir} "
        f"--target-file {target_file} --reviewed-file {reviewed_file} --allow-partial"
    )
    if apply:
        cmd += " --apply"
    return cmd


def preferred_wrapper_commands(exp_dir):
    return {
        "preflight": (
            "python3 "
            f"scripts/validate_cape_human_review_returns.py --experiment-dir {exp_dir}"
        ),
        "dry_run": (
            "PYTHON_BIN=python3 "
            "LLM_PYTHON=python3 "
            "APPLY_IMPORTS=0 bash scripts/run_cape_human_return_apply.sh"
        ),
        "apply": (
            "PYTHON_BIN=python3 "
            "LLM_PYTHON=python3 "
            "APPLY_IMPORTS=1 bash scripts/run_cape_human_return_apply.sh"
        ),
        "claim_status": "preferred_operational_path",
    }


def build_readme(batch, exp_dir):
    lines = [
        f"# {batch['batch_id']} Human-Gold Annotation Batch",
        "",
        "This directory contains partial annotation inputs for independent annotators A and B.",
        "The files are not gold labels until reviewers edit them, import them, compute IAA, and adjudicate the final file.",
        "",
        "## Files",
        "",
        f"- Annotator A input: `{batch['annotator_files']['A']}`",
        f"- Annotator B input: `{batch['annotator_files']['B']}`",
        f"- Tracking sheet: `{batch['tracking_sheet']}`",
        "",
        "## Workflow",
        "",
        "1. Open the static workbench:",
        f"   `{exp_dir / '01_data/gold_annotation/annotation_workbench.html'}`",
        "2. Load the annotator input JSONL for A or B.",
        "3. Review each chunk using only the chunk text as authority.",
        "4. Export the edited JSONL into this batch directory using the reviewed filename shown below.",
        "5. Run the return preflight first after reviewed files are exported.",
        "6. Use the human-return wrapper for dry-run/apply once the required return files are ready.",
        "7. Use individual import commands only for debugging a specific batch file.",
        "",
        "## Required Reviewed Filenames",
        "",
    ]
    for annotator in ANNOTATORS:
        lines += [
            f"### Annotator {annotator}",
            "",
            f"Save reviewed JSONL as: `{batch['reviewed_files'][annotator]}`",
            "",
        ]
    lines += [
        "## Recommended Return Preflight and Wrapper",
        "",
        "Validate returned files without importing:",
        "",
        "```bash",
        "python3 scripts/validate_cape_human_review_returns.py --experiment-dir experiments/cape_kg_eacl_20260627",
        "```",
        "",
        "Dry-run the complete post-return refresh:",
        "",
        "```bash",
        "PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=0 bash scripts/run_cape_human_return_apply.sh",
        "```",
        "",
        "Apply returned files only after preflight passes and the reviewed files are present:",
        "",
        "```bash",
        "PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=1 bash scripts/run_cape_human_return_apply.sh",
        "```",
        "",
        "## Low-Level Debug Import Commands",
        "",
        "The following commands validate a single reviewed batch file. Prefer the wrapper above for operational imports.",
        "",
    ]
    for annotator in ANNOTATORS:
        lines += [
            f"### Annotator {annotator}",
            "",
            "Single-file dry run:",
            "",
            "```bash",
            batch["import_commands"][annotator]["dry_run"],
            "```",
            "",
            "Single-file apply for debugging only:",
            "",
            "```bash",
            batch["import_commands"][annotator]["apply"],
            "```",
            "",
        ]
    lines += [
        "After both annotators are imported for enough chunks, recompute IAA and prepare adjudication drafts.",
        "",
    ]
    return "\n".join(lines)


def build_report(summary):
    lines = [
        "# CAPE-KG Human Annotation Batch Assignments",
        "",
        f"Generated: {summary['generated_at_utc']}",
        "",
        "These batches are workflow artifacts for human annotation. They do not satisfy the gold-label gate until edited, imported, and adjudicated.",
        "",
        f"- Package: `{summary['package']}`",
        f"- Batch size: {summary['batch_size']}",
        f"- Batches: {summary['batch_count']}",
        f"- Assigned chunks: {summary['assigned_chunks']}",
        f"- Candidate edges in assigned chunks: {summary['candidate_edges_total']}",
        f"- Output directory: `{summary['output_dir']}`",
        "",
        "## Batches",
        "",
        "| batch | chunks | rank range | candidate edges | high-impact chunks | files |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for batch in summary["batches"]:
        files = f"[README]({batch['readme']}) / [tracking]({batch['tracking_sheet']})"
        lines.append(
            f"| {batch['batch_id']} | {batch['chunk_count']} | {batch['rank_start']}-{batch['rank_end']} | "
            f"{batch['candidate_edges_total']} | {batch['high_impact_chunks']} | {files} |"
        )
    lines += [
        "",
        "## Preferred Wrapper Commands",
        "",
        "Use these commands for normal operation after reviewed files are returned:",
        "",
        "```bash",
        summary["preferred_wrapper_commands"]["preflight"],
        "```",
        "",
        "```bash",
        summary["preferred_wrapper_commands"]["dry_run"],
        "```",
        "",
        "```bash",
        summary["preferred_wrapper_commands"]["apply"],
        "```",
        "",
        "## Generated Files",
        "",
        f"- Summary JSON: `{summary['summary_json']}`",
        f"- Overview CSV: `{summary['overview_csv']}`",
        f"- Report: `{summary['report_md']}`",
        "",
    ]
    return "\n".join(lines)


def run(args):
    exp_dir = Path(args.experiment_dir)
    package = args.package
    selected, queue_path = select_priority_rows(exp_dir, package, args.batch_size * args.max_batches)
    annotator_paths = {}
    annotator_by_chunk = {}
    for annotator in ANNOTATORS:
        path, by_chunk = load_annotator_rows(exp_dir, package, annotator)
        annotator_paths[annotator] = path
        annotator_by_chunk[annotator] = by_chunk

    output_dir = exp_dir / "05_review/human_gold_batches"
    release_dir = exp_dir / "06_release"
    batches = []
    overview_rows = []
    missing = []

    for batch_index in range(0, len(selected), args.batch_size):
        batch_rows = selected[batch_index:batch_index + args.batch_size]
        if not batch_rows:
            continue
        batch_number = (batch_index // args.batch_size) + 1
        batch_id = f"{package}_priority_batch_{batch_number:03d}"
        batch_dir = output_dir / batch_id
        chunk_ids = [chunk_key(row) for row in batch_rows]
        rank_values = [as_int(row.get("rank")) for row in batch_rows]
        tracking_rows = []
        for row in batch_rows:
            tracking = {name: row.get(name, "") for name in TRACKING_FIELDNAMES}
            tracking["batch_id"] = batch_id
            tracking_rows.append(tracking)

        annotator_files = {}
        reviewed_files = {}
        import_commands = {}
        for annotator in ANNOTATORS:
            annotator_batch_rows = []
            for chunk_id in chunk_ids:
                source_row = annotator_by_chunk[annotator].get(chunk_id)
                if source_row is None:
                    missing.append({"batch_id": batch_id, "annotator": annotator, "chunk_id": chunk_id})
                    continue
                annotator_batch_rows.append(source_row)
            input_path = batch_dir / f"annotator_{annotator}_{batch_id}.jsonl"
            reviewed_path = batch_dir / f"annotator_{annotator}_{batch_id}.reviewed.jsonl"
            write_jsonl(input_path, annotator_batch_rows)
            annotator_files[annotator] = str(input_path)
            reviewed_files[annotator] = str(reviewed_path)
            import_commands[annotator] = {
                "dry_run": import_command(exp_dir, annotator_paths[annotator], reviewed_path, apply=False),
                "apply": import_command(exp_dir, annotator_paths[annotator], reviewed_path, apply=True),
            }

        tracking_path = batch_dir / "batch_tracking_sheet.csv"
        readme_path = batch_dir / "README.md"
        write_csv(tracking_path, tracking_rows, TRACKING_FIELDNAMES)

        batch_payload = {
            "batch_id": batch_id,
            "package": package,
            "rank_start": min(rank_values) if rank_values else 0,
            "rank_end": max(rank_values) if rank_values else 0,
            "chunk_count": len(chunk_ids),
            "chunk_ids": chunk_ids,
            "candidate_edges_total": sum(as_int(row.get("silver_candidate_edge_count")) for row in batch_rows),
            "active_review_items_total": sum(as_int(row.get("active_review_items")) for row in batch_rows),
            "high_impact_chunks": sum(1 for row in batch_rows if as_int(row.get("high_impact_items")) > 0),
            "annotator_files": annotator_files,
            "reviewed_files": reviewed_files,
            "tracking_sheet": str(tracking_path),
            "readme": str(readme_path),
            "preferred_wrapper_commands": preferred_wrapper_commands(exp_dir),
            "import_commands": import_commands,
            "import_commands_claim_status": "low_level_debug_only_prefer_wrapper",
        }
        write_text(readme_path, build_readme(batch_payload, exp_dir))
        write_json(batch_dir / "batch_manifest.json", batch_payload)
        batches.append(batch_payload)
        overview_rows.append({
            "batch_id": batch_id,
            "package": package,
            "rank_start": batch_payload["rank_start"],
            "rank_end": batch_payload["rank_end"],
            "chunk_count": batch_payload["chunk_count"],
            "candidate_edges_total": batch_payload["candidate_edges_total"],
            "active_review_items_total": batch_payload["active_review_items_total"],
            "high_impact_chunks": batch_payload["high_impact_chunks"],
            "chunk_ids": ",".join(chunk_ids),
            "annotator_A_file": annotator_files.get("A", ""),
            "annotator_B_file": annotator_files.get("B", ""),
            "tracking_sheet": str(tracking_path),
            "readme": str(readme_path),
        })

    overview_csv = output_dir / f"{package}_batch_assignment_overview.csv"
    summary_json = release_dir / "annotation_batch_assignment_summary.json"
    report_md = release_dir / "annotation_batch_assignment_report.md"
    write_csv(overview_csv, overview_rows, OVERVIEW_FIELDNAMES)
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "package": package,
        "priority_queue": str(queue_path),
        "batch_size": args.batch_size,
        "batch_count": len(batches),
        "assigned_chunks": sum(batch["chunk_count"] for batch in batches),
        "candidate_edges_total": sum(batch["candidate_edges_total"] for batch in batches),
        "active_review_items_total": sum(batch["active_review_items_total"] for batch in batches),
        "high_impact_chunks": sum(batch["high_impact_chunks"] for batch in batches),
        "output_dir": str(output_dir),
        "overview_csv": str(overview_csv),
        "summary_json": str(summary_json),
        "report_md": str(report_md),
        "preferred_wrapper_commands": preferred_wrapper_commands(exp_dir),
        "batches": batches,
        "missing_source_rows": missing,
        "claim_status": "assignment_batches_ready_pending_human_annotation",
        "note": "Workflow artifact only; does not satisfy human-gold or IAA gates.",
    }
    write_json(summary_json, summary)
    write_text(report_md, build_report(summary))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--package", default=DEFAULT_PACKAGE)
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--max-batches", type=int, default=5)
    args = parser.parse_args()
    if args.batch_size <= 0:
        raise SystemExit("--batch-size must be positive")
    if args.max_batches <= 0:
        raise SystemExit("--max-batches must be positive")
    run(args)


if __name__ == "__main__":
    main()
