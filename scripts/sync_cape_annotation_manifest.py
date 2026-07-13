#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Synchronize CAPE-KG annotation manifest metadata with current JSONL files.

This does not alter annotator or adjudication labels. It only refreshes package
metadata and tracking-sheet candidate counts so the manifest describes the files
that annotators actually edit.
"""

import argparse
import csv
import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
PACKAGES = ("pilot_30", "full_120")
ANNOTATORS = ("A", "B")


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_jsonl(path):
    path = Path(path)
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


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


def candidate_count(row):
    candidates = row.get("silver_candidate_edges")
    if isinstance(candidates, list):
        return len(candidates)
    return int(row.get("silver_candidate_edge_count") or 0)


def status(row, field, default=""):
    return str(row.get(field) or default).strip()


def package_summary(exp_dir, package_name):
    package_dir = Path(exp_dir) / "01_data/gold_annotation" / package_name
    annotator_rows = {}
    for annotator in ANNOTATORS:
        rows = read_jsonl(package_dir / f"annotator_{annotator}.jsonl")
        annotator_rows[annotator] = {row.get("chunk_id"): row for row in rows if row.get("chunk_id")}
    adjudication_rows = {
        row.get("chunk_id"): row
        for row in read_jsonl(package_dir / "adjudication.jsonl")
        if row.get("chunk_id")
    }
    chunk_ids = sorted(set().union(*[set(rows) for rows in annotator_rows.values()], set(adjudication_rows)))
    tracking = []
    counts = []
    chapter_counter = Counter()
    issues = []
    for chunk_id in chunk_ids:
        row_a = annotator_rows.get("A", {}).get(chunk_id, {})
        row_b = annotator_rows.get("B", {}).get(chunk_id, {})
        adj = adjudication_rows.get(chunk_id, {})
        template = row_a or row_b or adj
        count_a = candidate_count(row_a) if row_a else None
        count_b = candidate_count(row_b) if row_b else None
        if count_a is not None and count_b is not None and count_a != count_b:
            issues.append({
                "level": "warning",
                "code": "annotator_candidate_count_mismatch",
                "chunk_id": chunk_id,
                "annotator_A_count": count_a,
                "annotator_B_count": count_b,
            })
        current_count = count_a if count_a is not None else count_b if count_b is not None else 0
        counts.append(current_count)
        chapter_counter[template.get("chapter_id") or "unknown"] += 1
        tracking.append({
            "package": package_name,
            "chunk_id": chunk_id,
            "chapter_id": template.get("chapter_id"),
            "section_id": template.get("section_id"),
            "page_start": template.get("page_start"),
            "page_end": template.get("page_end"),
            "silver_candidate_edge_count": current_count,
            "annotator_A_status": status(row_a, "annotation_status", "missing"),
            "annotator_B_status": status(row_b, "annotation_status", "missing"),
            "adjudication_status": status(adj, "adjudication_status", "missing"),
            "priority": "pilot" if package_name == "pilot_30" else "full",
            "comment": "",
        })
    return {
        "package": package_name,
        "package_dir": str(package_dir),
        "chunk_count": len(chunk_ids),
        "candidate_edges_total": sum(counts),
        "candidate_edges_min": min(counts) if counts else 0,
        "candidate_edges_max": max(counts) if counts else 0,
        "chapter_distribution": dict(chapter_counter),
        "tracking_rows": tracking,
        "issues": issues,
    }


def build_report(payload):
    lines = [
        "# CAPE-KG Annotation Manifest Sync Report",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Experiment: `{payload['experiment_dir']}`",
        f"Apply mode: `{payload['apply_mode']}`",
        "",
        "This report covers metadata synchronization only. Annotator and adjudication JSONL labels are not modified.",
        "",
        "| package | chunks | before candidates | after candidates | status |",
        "|---|---:|---:|---:|---|",
    ]
    for row in payload["packages"]:
        lines.append(
            f"| {row['package']} | {row['chunk_count']} | {row['before_candidate_edges_total']} | "
            f"{row['after_candidate_edges_total']} | {row['status']} |"
        )
    if payload.get("issues"):
        lines += ["", "## Issues", ""]
        for issue in payload["issues"]:
            lines.append(f"- {issue['package']}: {issue['code']} {issue.get('chunk_id', '')}")
    return "\n".join(lines) + "\n"


def run(args):
    exp_dir = Path(args.experiment_dir)
    root = exp_dir / "01_data/gold_annotation"
    manifest_path = root / "annotation_package_manifest.json"
    manifest = read_json(manifest_path, {}) or {}
    manifest.setdefault("packages", {})
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    package_reports = []
    all_tracking = []
    issues = []
    for package_name in PACKAGES:
        summary = package_summary(exp_dir, package_name)
        package_meta = manifest["packages"].setdefault(package_name, {})
        before_total = int(package_meta.get("candidate_edges_total") or 0)
        package_reports.append({
            "package": package_name,
            "chunk_count": summary["chunk_count"],
            "before_candidate_edges_total": before_total,
            "after_candidate_edges_total": summary["candidate_edges_total"],
            "status": "updated" if before_total != summary["candidate_edges_total"] else "unchanged",
        })
        for issue in summary["issues"]:
            issue = dict(issue)
            issue["package"] = package_name
            issues.append(issue)
        if args.apply:
            package_meta["chunk_count"] = summary["chunk_count"]
            package_meta["candidate_edges_total"] = summary["candidate_edges_total"]
            package_meta["candidate_edges_min"] = summary["candidate_edges_min"]
            package_meta["candidate_edges_max"] = summary["candidate_edges_max"]
            package_meta["chapter_distribution"] = summary["chapter_distribution"]
            package_meta["metadata_source"] = "current_annotator_jsonl"
            package_meta["metadata_synced_at_utc"] = datetime.now(timezone.utc).isoformat()
            tracking_path = root / package_name / "tracking_sheet.csv"
            write_csv(
                tracking_path,
                summary["tracking_rows"],
                [
                    "package",
                    "chunk_id",
                    "chapter_id",
                    "section_id",
                    "page_start",
                    "page_end",
                    "silver_candidate_edge_count",
                    "annotator_A_status",
                    "annotator_B_status",
                    "adjudication_status",
                    "priority",
                    "comment",
                ],
            )
        all_tracking.extend(summary["tracking_rows"])

    if args.apply:
        manifest["metadata_synced_at_utc"] = datetime.now(timezone.utc).isoformat()
        manifest["metadata_source"] = "current_annotator_jsonl"
        manifest["sync_report"] = str(root / "annotation_manifest_sync_report.md")
        backup_path = manifest_path.with_suffix(manifest_path.suffix + f".bak.{timestamp}")
        shutil.copy2(manifest_path, backup_path)
        manifest["previous_manifest_backup"] = str(backup_path)
        write_json(manifest_path, manifest)
        write_csv(
            root / "gold_annotation_master_tracking_sheet.csv",
            all_tracking,
            [
                "package",
                "chunk_id",
                "chapter_id",
                "section_id",
                "page_start",
                "page_end",
                "silver_candidate_edge_count",
                "annotator_A_status",
                "annotator_B_status",
                "adjudication_status",
                "priority",
                "comment",
            ],
        )

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "apply_mode": bool(args.apply),
        "manifest": str(manifest_path),
        "packages": package_reports,
        "issues": issues,
    }
    report_path = root / "annotation_manifest_sync_report.md"
    json_path = root / "annotation_manifest_sync_report.json"
    write_json(json_path, payload)
    write_text(report_path, build_report(payload))
    print(json.dumps({
        "sync_json": str(json_path),
        "sync_report": str(report_path),
        "apply_mode": bool(args.apply),
        "packages": package_reports,
        "issue_count": len(issues),
    }, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
