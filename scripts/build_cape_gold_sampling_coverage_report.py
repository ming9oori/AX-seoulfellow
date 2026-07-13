#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a claim-safe gold-subset sampling and coverage report."""

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_OUTPUTS_DIR = Path("outputs")


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


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


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path, rows, fieldnames):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def as_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def as_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def fmt(value):
    if value is None:
        return "pending"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def md_table(headers, rows):
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(fmt(cell) for cell in row) + " |")
    return "\n".join(lines)


def row_chunk_id(row):
    return str(row.get("chunk_id") or "").strip()


def source_chunk_id(row):
    return str(row.get("source_chunk_id") or row.get("chunk_id") or "").strip()


def sentence_count(row):
    sentence_ids = row.get("sentence_ids") or row.get("split_sentence_ids") or []
    if isinstance(sentence_ids, list):
        return len(sentence_ids)
    return 0


def load_active_review(exp_dir):
    rows = read_jsonl(exp_dir / "05_review/actual_llm_active_review_queue_P_cape_kg_actual.jsonl")
    by_chunk = defaultdict(lambda: {"active_review_items": 0, "high_impact_items": 0, "review_error_items": 0})
    for row in rows:
        chunk_id = row.get("chunk_id")
        if not chunk_id:
            continue
        item = by_chunk[chunk_id]
        item["active_review_items"] += 1
        if row.get("high_impact_error_label"):
            item["high_impact_items"] += 1
        if row.get("review_error_label"):
            item["review_error_items"] += 1
    return dict(by_chunk)


def package_rows(exp_dir, package_name, fallback_path=None):
    if fallback_path:
        rows = read_jsonl(fallback_path)
        if rows:
            return rows, fallback_path
    path = exp_dir / "01_data/gold_annotation" / package_name / "annotator_A.jsonl"
    rows = read_jsonl(path)
    return rows, path


def summarize_rows(label, rows, active_by_chunk):
    chapter_counts = Counter()
    section_counts = Counter()
    source_chunks = set()
    pages = []
    candidate_edges_total = 0
    chunks_with_candidates = 0
    dense_candidate_chunks = 0
    zero_candidate_chunks = 0
    sentence_total = 0
    active_chunks = 0
    high_impact_chunks = 0
    review_error_chunks = 0

    for row in rows:
        chunk_id = row_chunk_id(row)
        src_id = source_chunk_id(row)
        if src_id:
            source_chunks.add(src_id)
        chapter_counts[str(row.get("chapter_id") or "missing")] += 1
        section_counts[str(row.get("section_id") or "missing")] += 1
        for key in ("page_start", "page_end"):
            page = as_int(row.get(key), None)
            if page is not None:
                pages.append(page)
        candidates = as_int(row.get("silver_candidate_edge_count"))
        candidate_edges_total += candidates
        if candidates > 0:
            chunks_with_candidates += 1
        if candidates >= 40:
            dense_candidate_chunks += 1
        if candidates == 0:
            zero_candidate_chunks += 1
        sentence_total += sentence_count(row)
        active = active_by_chunk.get(src_id) or active_by_chunk.get(chunk_id) or {}
        if as_int(active.get("active_review_items")):
            active_chunks += 1
        if as_int(active.get("high_impact_items")):
            high_impact_chunks += 1
        if as_int(active.get("review_error_items")):
            review_error_chunks += 1

    count = len(rows)
    return {
        "label": label,
        "chunk_count": count,
        "unique_source_chunk_count": len(source_chunks),
        "chapter_count": len(chapter_counts),
        "section_count": len(section_counts),
        "page_min": min(pages) if pages else None,
        "page_max": max(pages) if pages else None,
        "sentence_total": sentence_total,
        "candidate_edges_total": candidate_edges_total,
        "candidate_edges_per_chunk_avg": round(candidate_edges_total / count, 4) if count else 0.0,
        "chunks_with_candidates": chunks_with_candidates,
        "dense_candidate_chunks_ge40": dense_candidate_chunks,
        "zero_candidate_chunks": zero_candidate_chunks,
        "active_review_chunks": active_chunks,
        "high_impact_chunks": high_impact_chunks,
        "review_error_chunks": review_error_chunks,
        "chapter_distribution": dict(sorted(chapter_counts.items())),
        "section_distribution": dict(sorted(section_counts.items())),
    }


def load_priority_queue(exp_dir):
    rows = read_jsonl(exp_dir / "05_review/human_gold_annotation_priority_queue.jsonl")
    rows.sort(key=lambda row: as_int(row.get("rank"), 999999))
    return rows


def load_assigned_chunk_ids(exp_dir):
    summary = read_json(exp_dir / "06_release/annotation_batch_assignment_summary.json", {}) or {}
    ids = []
    for batch in summary.get("batches", []):
        ids.extend(batch.get("chunk_ids") or [])
    return set(ids), summary


def select_rows_by_ids(rows, ids):
    id_set = set(ids)
    return [row for row in rows if row_chunk_id(row) in id_set or source_chunk_id(row) in id_set]


def chapter_coverage_rows(stats_by_label):
    labels = list(stats_by_label)
    chapters = sorted({chapter for stats in stats_by_label.values() for chapter in stats["chapter_distribution"]})
    rows = []
    for chapter in chapters:
        row = {"chapter_id": chapter}
        for label in labels:
            row[f"{label}_chunks"] = stats_by_label[label]["chapter_distribution"].get(chapter, 0)
        rows.append(row)
    return rows


def selected_chunk_rows(priority_rows, assigned_ids):
    rows = []
    for row in priority_rows:
        chunk_id = row_chunk_id(row)
        if chunk_id not in assigned_ids:
            continue
        rows.append({
            "rank": as_int(row.get("rank")),
            "chunk_id": chunk_id,
            "chapter_id": row.get("chapter_id"),
            "section_id": row.get("section_id"),
            "page_start": row.get("page_start"),
            "page_end": row.get("page_end"),
            "priority_score": row.get("priority_score"),
            "priority_reason": row.get("priority_reason"),
            "silver_candidate_edge_count": row.get("silver_candidate_edge_count"),
            "active_review_items": row.get("active_review_items"),
            "high_impact_items": row.get("high_impact_items"),
            "top_error_reasons": row.get("top_error_reasons"),
        })
    rows.sort(key=lambda row: row["rank"])
    return rows


def build_payload(exp_dir, outputs_dir):
    exp_dir = Path(exp_dir)
    outputs_dir = Path(outputs_dir)
    active_by_chunk = load_active_review(exp_dir)
    expansion = read_json(exp_dir / "01_data/gold_annotation/annotation_expansion_manifest.json", {}) or {}
    assigned_ids, assignment_summary = load_assigned_chunk_ids(exp_dir)
    priority_rows = load_priority_queue(exp_dir)

    source_rows = read_jsonl(outputs_dir / "02_ocr/layer2_chunks.jsonl")
    full120_rows, full120_path = package_rows(exp_dir, "full_120")
    all214_rows, all214_path = package_rows(exp_dir, "all_available_214")
    strong_package = expansion.get("strong_resegmented_package") or "strong_resegmented_342_max18"
    strong_rows, strong_path = package_rows(exp_dir, strong_package)

    selected100_rows = select_rows_by_ids(full120_rows, assigned_ids)
    remaining20_rows = [row for row in full120_rows if row_chunk_id(row) not in assigned_ids]

    stats = {
        "source_layer2_chunks": summarize_rows("source_layer2_chunks", source_rows, active_by_chunk),
        "full_120_gold_package": summarize_rows("full_120_gold_package", full120_rows, active_by_chunk),
        "priority_100_assigned": summarize_rows("priority_100_assigned", selected100_rows, active_by_chunk),
        "remaining_20_in_full_120": summarize_rows("remaining_20_in_full_120", remaining20_rows, active_by_chunk),
        "all_available_214_optional": summarize_rows("all_available_214_optional", all214_rows, active_by_chunk),
        f"{strong_package}_optional_strong": summarize_rows(f"{strong_package}_optional_strong", strong_rows, active_by_chunk),
    }
    full = stats["full_120_gold_package"]
    selected = stats["priority_100_assigned"]
    candidate_coverage = (
        round(selected["candidate_edges_total"] / full["candidate_edges_total"], 6)
        if full["candidate_edges_total"] else 0.0
    )
    active_coverage = (
        round(selected["active_review_chunks"] / full["active_review_chunks"], 6)
        if full["active_review_chunks"] else 0.0
    )
    high_impact_coverage = (
        round(selected["high_impact_chunks"] / full["high_impact_chunks"], 6)
        if full["high_impact_chunks"] else 0.0
    )
    selected_chunks = selected_chunk_rows(priority_rows, assigned_ids)
    chapter_rows = chapter_coverage_rows(stats)
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "outputs_dir": str(outputs_dir),
        "claim_status": "gold_sampling_coverage_ready_pending_human_review",
        "selection_policy": {
            "minimum_gate_target_chunks": 100,
            "candidate_pool": str(full120_path),
            "priority_queue": str(exp_dir / "05_review/human_gold_annotation_priority_queue.jsonl"),
            "assignment_summary": str(exp_dir / "06_release/annotation_batch_assignment_summary.json"),
            "priority_formula": "0.4*candidate_edge_density + 0.4*active_review_priority + 0.2*high_impact_error_presence",
            "selected_chunk_count": len(selected100_rows),
            "batch_count": assignment_summary.get("batch_count"),
            "batch_size": assignment_summary.get("batch_size"),
            "not_gold_until": "two annotators complete the selected chunks, IAA is computed, and adjudication is imported",
        },
        "input_files": {
            "source_layer2_chunks": str(outputs_dir / "02_ocr/layer2_chunks.jsonl"),
            "full_120_gold_package": str(full120_path),
            "all_available_214_optional": str(all214_path),
            "optional_strong_package": str(strong_path),
        },
        "coverage_summary": {
            "priority_100_candidate_edge_coverage_of_full120": candidate_coverage,
            "priority_100_active_review_chunk_coverage_of_full120": active_coverage,
            "priority_100_high_impact_chunk_coverage_of_full120": high_impact_coverage,
            "full_120_candidate_edges": full["candidate_edges_total"],
            "priority_100_candidate_edges": selected["candidate_edges_total"],
            "all_available_214_candidate_edges": stats["all_available_214_optional"]["candidate_edges_total"],
            "optional_strong_candidate_edges": stats[f"{strong_package}_optional_strong"]["candidate_edges_total"],
            "strong_300_chunk_gap_after_resegmentation": expansion.get("strong_300_chunk_gap_after_resegmentation"),
        },
        "packages": list(stats.values()),
        "chapter_coverage_rows": chapter_rows,
        "selected_chunks": selected_chunks,
        "outputs": {
            "json": str(exp_dir / "06_release/gold_sampling_coverage_report.json"),
            "markdown": str(exp_dir / "06_release/gold_sampling_coverage_report.md"),
            "chapter_csv": str(exp_dir / "05_review/gold_sampling_coverage_by_chapter.csv"),
            "selected_chunks_csv": str(exp_dir / "05_review/gold_sampling_priority100_selected_chunks.csv"),
        },
    }


def render_markdown(payload):
    summary = payload["coverage_summary"]
    policy = payload["selection_policy"]
    package_rows = [
        [
            row["label"],
            row["chunk_count"],
            row["unique_source_chunk_count"],
            row["chapter_count"],
            row["section_count"],
            f"{row['page_min']}-{row['page_max']}",
            row["candidate_edges_total"],
            row["candidate_edges_per_chunk_avg"],
            row["active_review_chunks"],
            row["high_impact_chunks"],
            row["zero_candidate_chunks"],
        ]
        for row in payload["packages"]
    ]
    chapter_headers = ["Chapter"] + [row["label"] for row in payload["packages"]]
    chapter_rows = []
    for row in payload["chapter_coverage_rows"]:
        chapter_rows.append([row["chapter_id"]] + [row.get(f"{label}_chunks", 0) for label in chapter_headers[1:]])
    top_rows = [
        [
            row["rank"],
            row["chunk_id"],
            row["chapter_id"],
            row["section_id"],
            row["silver_candidate_edge_count"],
            row["active_review_items"],
            row["high_impact_items"],
            row["priority_reason"],
        ]
        for row in payload["selected_chunks"][:20]
    ]
    lines = [
        "# CAPE-KG Gold Subset Sampling and Coverage Report",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Claim status: `{payload['claim_status']}`",
        "",
        "이 문서는 human-gold annotation을 대체하지 않습니다. 현재 선택된 검수 subset이 어떤 근거로 구성되었고, corpus/chapter/candidate edge/active-review 관점에서 어떤 범위를 덮는지 설명하는 pre-human sampling evidence입니다.",
        "",
        "## Selection Policy",
        "",
        f"- Minimum paper gate target: `{policy['minimum_gate_target_chunks']}` chunks",
        f"- Selected chunks assigned to A/B batches: `{policy['selected_chunk_count']}`",
        f"- Batch count/size: `{policy.get('batch_count')}` batches x `{policy.get('batch_size')}` chunks",
        f"- Priority formula: `{policy['priority_formula']}`",
        f"- Claim boundary (`not_gold_until`): `{policy['not_gold_until']}`",
        "",
        "## Coverage Summary",
        "",
        f"- Priority-100 candidate-edge coverage within full-120 package: `{summary['priority_100_candidate_edge_coverage_of_full120']}`",
        f"- Priority-100 active-review chunk coverage within full-120 package: `{summary['priority_100_active_review_chunk_coverage_of_full120']}`",
        f"- Priority-100 high-impact chunk coverage within full-120 package: `{summary['priority_100_high_impact_chunk_coverage_of_full120']}`",
        f"- Full-120 candidate edges: `{summary['full_120_candidate_edges']}`",
        f"- Priority-100 candidate edges: `{summary['priority_100_candidate_edges']}`",
        f"- Optional all-available-214 candidate edges: `{summary['all_available_214_candidate_edges']}`",
        f"- Optional strong package candidate edges: `{summary['optional_strong_candidate_edges']}`",
        f"- Strong 300+ chunk gap after resegmentation: `{summary['strong_300_chunk_gap_after_resegmentation']}`",
        "",
        "## Package-Level Coverage",
        "",
        md_table(
            [
                "Package",
                "Chunks",
                "Source chunks",
                "Chapters",
                "Sections",
                "Pages",
                "Candidate edges",
                "Edges/chunk",
                "Active-review chunks",
                "High-impact chunks",
                "Zero-candidate chunks",
            ],
            package_rows,
        ),
        "",
        "## Chapter Coverage",
        "",
        md_table(chapter_headers, chapter_rows),
        "",
        "## Top Selected Priority Chunks",
        "",
        md_table(
            [
                "Rank",
                "Chunk",
                "Chapter",
                "Section",
                "Candidate edges",
                "Active items",
                "High-impact",
                "Reason",
            ],
            top_rows,
        ),
        "",
        "## Output Files",
        "",
        f"- JSON: `{payload['outputs']['json']}`",
        f"- Chapter CSV: `{payload['outputs']['chapter_csv']}`",
        f"- Selected chunks CSV: `{payload['outputs']['selected_chunks_csv']}`",
        "",
    ]
    return "\n".join(lines)


def run(args):
    exp_dir = Path(args.experiment_dir)
    outputs_dir = Path(args.outputs_dir)
    payload = build_payload(exp_dir, outputs_dir)
    write_json(payload["outputs"]["json"], payload)
    write_text(payload["outputs"]["markdown"], render_markdown(payload))
    chapter_fieldnames = ["chapter_id"] + [f"{row['label']}_chunks" for row in payload["packages"]]
    write_csv(payload["outputs"]["chapter_csv"], payload["chapter_coverage_rows"], chapter_fieldnames)
    write_csv(
        payload["outputs"]["selected_chunks_csv"],
        payload["selected_chunks"],
        [
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
            "high_impact_items",
            "top_error_reasons",
        ],
    )
    print(json.dumps(payload["outputs"], ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--outputs-dir", default=str(DEFAULT_OUTPUTS_DIR))
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
