#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build human annotation progress and priority reports for CAPE-KG."""

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


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


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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


def norm_status(value):
    return str(value or "").strip().lower()


def is_annotation_complete(row):
    return norm_status(row.get("annotation_status")) in COMPLETED_ANNOTATION_STATUSES


def is_adjudication_complete(row):
    return norm_status(row.get("adjudication_status")) in COMPLETED_ADJUDICATION_STATUSES


def load_active_review_by_chunk(exp_dir):
    path = Path(exp_dir) / "05_review/actual_llm_active_review_queue_P_cape_kg_actual.jsonl"
    by_chunk = defaultdict(lambda: {
        "active_review_items": 0,
        "high_impact_items": 0,
        "review_error_items": 0,
        "max_active_priority": 0.0,
        "max_uncertainty_priority": 0.0,
        "error_reasons": Counter(),
    })
    for row in read_jsonl(path):
        chunk_id = row.get("chunk_id")
        if not chunk_id:
            continue
        item = by_chunk[chunk_id]
        item["active_review_items"] += 1
        if row.get("high_impact_error_label"):
            item["high_impact_items"] += 1
        if row.get("review_error_label"):
            item["review_error_items"] += 1
        try:
            item["max_active_priority"] = max(item["max_active_priority"], float(row.get("active_priority") or 0.0))
            item["max_uncertainty_priority"] = max(item["max_uncertainty_priority"], float(row.get("uncertainty_priority") or 0.0))
        except (TypeError, ValueError):
            pass
        for reason in str(row.get("error_reasons") or "").split(","):
            reason = reason.strip()
            if reason:
                item["error_reasons"][reason] += 1
    output = {}
    for chunk_id, item in by_chunk.items():
        output[chunk_id] = {
            "active_review_items": item["active_review_items"],
            "high_impact_items": item["high_impact_items"],
            "review_error_items": item["review_error_items"],
            "max_active_priority": round(item["max_active_priority"], 6),
            "max_uncertainty_priority": round(item["max_uncertainty_priority"], 6),
            "top_error_reasons": ",".join(reason for reason, _ in item["error_reasons"].most_common(3)),
        }
    return output


def rows_by_chunk(rows):
    return {row.get("chunk_id"): row for row in rows if row.get("chunk_id")}


def package_progress(exp_dir, package_name, active_by_chunk):
    base = Path(exp_dir) / "01_data/gold_annotation" / package_name
    annotator_a = read_jsonl(base / "annotator_A.jsonl")
    annotator_b = read_jsonl(base / "annotator_B.jsonl")
    adjudication = read_jsonl(base / "adjudication.jsonl")
    a_by_chunk = rows_by_chunk(annotator_a)
    b_by_chunk = rows_by_chunk(annotator_b)
    adj_by_chunk = rows_by_chunk(adjudication)
    chunk_ids = sorted(set(a_by_chunk) | set(b_by_chunk) | set(adj_by_chunk))
    max_candidate_edges = max(
        [int((a_by_chunk.get(chunk_id) or b_by_chunk.get(chunk_id) or {}).get("silver_candidate_edge_count") or 0) for chunk_id in chunk_ids] or [1]
    )
    worklist = []
    status_counts = Counter()
    for chunk_id in chunk_ids:
        a = a_by_chunk.get(chunk_id, {})
        b = b_by_chunk.get(chunk_id, {})
        adj = adj_by_chunk.get(chunk_id, {})
        template = a or b or adj
        a_status = norm_status(a.get("annotation_status"))
        b_status = norm_status(b.get("annotation_status"))
        adj_status = norm_status(adj.get("adjudication_status"))
        a_done = is_annotation_complete(a)
        b_done = is_annotation_complete(b)
        adj_done = is_adjudication_complete(adj)
        candidate_edges = int(template.get("silver_candidate_edge_count") or 0)
        active = active_by_chunk.get(chunk_id, {})
        candidate_norm = candidate_edges / max_candidate_edges if max_candidate_edges else 0.0
        active_priority = float(active.get("max_active_priority") or 0.0)
        high_impact = int(active.get("high_impact_items") or 0)
        high_impact_score = min(1.0, high_impact / 3.0)
        priority_score = round((0.4 * candidate_norm) + (0.4 * active_priority) + (0.2 * high_impact_score), 6)
        if adj_done:
            workflow_status = "adjudicated"
        elif a_done and b_done:
            workflow_status = "ready_for_adjudication"
        elif a_done or b_done:
            workflow_status = "one_annotator_complete"
        else:
            workflow_status = "pending_two_annotators"
        status_counts[workflow_status] += 1
        reasons = []
        if active_priority > 0:
            reasons.append("active_review")
        if high_impact:
            reasons.append("high_impact")
        if candidate_edges >= max(10, int(max_candidate_edges * 0.2)):
            reasons.append("dense_candidates")
        if not reasons:
            reasons.append("coverage")
        worklist.append({
            "package": package_name,
            "chunk_id": chunk_id,
            "chapter_id": template.get("chapter_id"),
            "section_id": template.get("section_id"),
            "page_start": template.get("page_start"),
            "page_end": template.get("page_end"),
            "workflow_status": workflow_status,
            "annotator_A_status": a_status,
            "annotator_B_status": b_status,
            "adjudication_status": adj_status,
            "silver_candidate_edge_count": candidate_edges,
            "active_review_items": active.get("active_review_items", 0),
            "review_error_items": active.get("review_error_items", 0),
            "high_impact_items": high_impact,
            "max_active_priority": active.get("max_active_priority", 0.0),
            "max_uncertainty_priority": active.get("max_uncertainty_priority", 0.0),
            "top_error_reasons": active.get("top_error_reasons", ""),
            "priority_score": priority_score,
            "priority_reason": ",".join(reasons),
        })
    worklist.sort(key=lambda row: (row["workflow_status"] == "adjudicated", -row["priority_score"], row["chunk_id"]))
    summary = {
        "package": package_name,
        "chunk_count": len(chunk_ids),
        "annotator_A_completed_chunks": sum(1 for row in annotator_a if is_annotation_complete(row)),
        "annotator_B_completed_chunks": sum(1 for row in annotator_b if is_annotation_complete(row)),
        "paired_completed_chunks": sum(1 for chunk_id in chunk_ids if is_annotation_complete(a_by_chunk.get(chunk_id, {})) and is_annotation_complete(b_by_chunk.get(chunk_id, {}))),
        "adjudicated_chunks": sum(1 for row in adjudication if is_adjudication_complete(row)),
        "workflow_status_counts": dict(status_counts),
        "candidate_edges_total": sum(int((a_by_chunk.get(chunk_id) or b_by_chunk.get(chunk_id) or {}).get("silver_candidate_edge_count") or 0) for chunk_id in chunk_ids),
        "active_review_chunks": sum(1 for row in worklist if row["active_review_items"]),
        "high_impact_chunks": sum(1 for row in worklist if row["high_impact_items"]),
    }
    return summary, worklist


def markdown_report(payload):
    lines = [
        "# CAPE-KG Human Annotation Progress",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Experiment: `{payload['experiment_dir']}`",
        "",
        "This report tracks annotation readiness only. Pending rows are not gold labels and are not used for paper claims.",
        "",
        "## Package Summary",
        "",
        "| package | chunks | A done | B done | paired done | adjudicated | active-review chunks | high-impact chunks |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["packages"]:
        lines.append(
            f"| {row['package']} | {row['chunk_count']} | {row['annotator_A_completed_chunks']} | "
            f"{row['annotator_B_completed_chunks']} | {row['paired_completed_chunks']} | "
            f"{row['adjudicated_chunks']} | {row['active_review_chunks']} | {row['high_impact_chunks']} |"
        )
    if payload.get("manifest_consistency"):
        lines += ["", "## Manifest Consistency", ""]
        for row in payload["manifest_consistency"]:
            status = "ok" if row["matches_current_files"] else "mismatch"
            lines.append(
                f"- {row['package']}: {status}; manifest_candidate_edges={row['manifest_candidate_edges_total']}, "
                f"current_candidate_edges={row['current_candidate_edges_total']}"
            )
    full = payload["full_120_summary"]
    lines += [
        "",
        "## Minimum Gold Gate",
        "",
        f"- Required adjudicated chunks: 100",
        f"- Current adjudicated chunks: {full['adjudicated_chunks']}",
        f"- Required paired annotator chunks before adjudication: 100",
        f"- Current paired completed chunks: {full['paired_completed_chunks']}",
        f"- Status: {payload['minimum_gold_gate_status']}",
        "",
        "## Top Annotation Priority Chunks",
        "",
        "| rank | chunk | chapter | score | reason | candidates | active items | high-impact | status |",
        "|---:|---|---|---:|---|---:|---:|---:|---|",
    ]
    for row in payload["top_priority_chunks"][:25]:
        lines.append(
            f"| {row['rank']} | {row['chunk_id']} | {row.get('chapter_id')} | {row['priority_score']} | "
            f"{row['priority_reason']} | {row['silver_candidate_edge_count']} | {row['active_review_items']} | "
            f"{row['high_impact_items']} | {row['workflow_status']} |"
        )
    lines += [
        "",
        "## Files",
        "",
        f"- Summary JSON: `{payload['files']['summary_json']}`",
        f"- Full worklist CSV: `{payload['files']['worklist_csv']}`",
        f"- Full worklist JSONL: `{payload['files']['worklist_jsonl']}`",
        f"- Next 100 CSV: `{payload['files']['next_100_csv']}`",
    ]
    return "\n".join(lines) + "\n"


def run(args):
    exp_dir = Path(args.experiment_dir)
    active_by_chunk = load_active_review_by_chunk(exp_dir)
    manifest_payload = read_json(exp_dir / "01_data/gold_annotation/annotation_package_manifest.json", {}) or {}
    packages = []
    full_worklist = []
    for package_name in ("pilot_30", "full_120"):
        summary, worklist = package_progress(exp_dir, package_name, active_by_chunk)
        packages.append(summary)
        if package_name == "full_120":
            full_worklist = worklist
            full_summary = summary
    manifest_consistency = []
    manifest_packages = (manifest_payload.get("packages") or {}) if isinstance(manifest_payload, dict) else {}
    for summary in packages:
        manifest_candidate_edges = int((manifest_packages.get(summary["package"]) or {}).get("candidate_edges_total") or 0)
        current_candidate_edges = int(summary.get("candidate_edges_total") or 0)
        manifest_consistency.append({
            "package": summary["package"],
            "manifest_candidate_edges_total": manifest_candidate_edges,
            "current_candidate_edges_total": current_candidate_edges,
            "matches_current_files": manifest_candidate_edges == current_candidate_edges,
        })
    ranked = []
    for index, row in enumerate(full_worklist, start=1):
        ranked_row = dict(row)
        ranked_row["rank"] = index
        ranked.append(ranked_row)
    next_100 = [row for row in ranked if row["workflow_status"] != "adjudicated"][:100]
    output_dir = exp_dir / "05_review"
    release_dir = exp_dir / "06_release"
    worklist_csv = output_dir / "human_gold_annotation_priority_queue.csv"
    worklist_jsonl = output_dir / "human_gold_annotation_priority_queue.jsonl"
    next_100_csv = output_dir / "human_gold_next_100_worklist.csv"
    fieldnames = [
        "rank",
        "package",
        "chunk_id",
        "chapter_id",
        "section_id",
        "page_start",
        "page_end",
        "workflow_status",
        "annotator_A_status",
        "annotator_B_status",
        "adjudication_status",
        "priority_score",
        "priority_reason",
        "silver_candidate_edge_count",
        "active_review_items",
        "review_error_items",
        "high_impact_items",
        "max_active_priority",
        "max_uncertainty_priority",
        "top_error_reasons",
    ]
    write_csv(worklist_csv, ranked, fieldnames)
    write_jsonl(worklist_jsonl, ranked)
    write_csv(next_100_csv, next_100, fieldnames)
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "packages": packages,
        "manifest_consistency": manifest_consistency,
        "full_120_summary": full_summary,
        "minimum_gold_gate_status": "pass" if full_summary["adjudicated_chunks"] >= 100 else "pending_human_adjudication",
        "top_priority_chunks": ranked[:50],
        "files": {
            "summary_json": str(release_dir / "annotation_progress_summary.json"),
            "report_md": str(release_dir / "annotation_progress_report.md"),
            "worklist_csv": str(worklist_csv),
            "worklist_jsonl": str(worklist_jsonl),
            "next_100_csv": str(next_100_csv),
        },
    }
    write_json(release_dir / "annotation_progress_summary.json", payload)
    write_text(release_dir / "annotation_progress_report.md", markdown_report(payload))
    print(json.dumps({
        "summary_json": str(release_dir / "annotation_progress_summary.json"),
        "report_md": str(release_dir / "annotation_progress_report.md"),
        "worklist_csv": str(worklist_csv),
        "next_100_csv": str(next_100_csv),
        "minimum_gold_gate_status": payload["minimum_gold_gate_status"],
        "full_120": full_summary,
    }, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
