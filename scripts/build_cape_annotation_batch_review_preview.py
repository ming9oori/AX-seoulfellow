#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build candidate/span preview tables for CAPE-KG human annotation batches."""

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")

SUMMARY_FIELDS = [
    "batch_id",
    "rank_start",
    "rank_end",
    "chunk_count",
    "candidate_edges_total",
    "candidate_edges_per_chunk_avg",
    "exact_component_ratio",
    "full_sentence_proxy_components",
    "label_not_found_components",
    "chunks_needing_span_attention",
    "zero_candidate_chunks",
    "dense_candidate_chunks",
    "high_impact_chunks",
    "preview_csv",
    "preview_md",
]

PREVIEW_FIELDS = [
    "rank",
    "chunk_id",
    "page_start",
    "page_end",
    "priority_score",
    "priority_reason",
    "candidate_edges",
    "top_predicates",
    "unique_evidence_anchors",
    "component_spans",
    "exact_components",
    "exact_component_ratio",
    "full_sentence_proxy_components",
    "label_not_found_components",
    "active_review_items",
    "high_impact_items",
    "review_focus",
]


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


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


def read_csv(path):
    path = Path(path)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
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
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def as_int(value, default=0):
    try:
        if value in ("", None):
            return default
        return int(float(value))
    except Exception:
        return default


def as_float(value, default=0.0):
    try:
        if value in ("", None):
            return default
        return float(value)
    except Exception:
        return default


def ratio(numerator, denominator):
    denominator = as_int(denominator)
    if denominator <= 0:
        return 0.0
    return as_int(numerator) / denominator


def fmt_ratio(value):
    return f"{float(value):.4f}"


def short_counter(counter, limit=4):
    return "; ".join(f"{key}:{value}" for key, value in counter.most_common(limit))


def chunk_preview(row, tracking):
    candidates = row.get("silver_candidate_edges") or []
    predicate_counts = Counter()
    evidence_ids = set()
    component_count = 0
    exact_components = 0
    full_sentence_proxy = 0
    label_not_found = 0
    for edge in candidates:
        predicate_counts[str(edge.get("predicate") or "")] += 1
        for evidence_id in edge.get("evidence_anchor_ids") or []:
            evidence_ids.add(str(evidence_id))
        for component in edge.get("component_evidence_spans") or []:
            component_count += 1
            if component.get("span_exact"):
                exact_components += 1
            method = str(component.get("span_method") or "")
            if method == "full_sentence_proxy":
                full_sentence_proxy += 1
            if method == "label_not_found_in_sentence" or not component.get("text"):
                label_not_found += 1

    candidate_edges = max(len(candidates), as_int(row.get("silver_candidate_edge_count")))
    exact_ratio = ratio(exact_components, component_count)
    high_impact = as_int(tracking.get("high_impact_items"))
    active_items = as_int(tracking.get("active_review_items"))
    focus = []
    if candidate_edges == 0:
        focus.append("missing-edge scan")
    if candidate_edges >= 40:
        focus.append("dense candidate pruning")
    if exact_ratio < 0.50 and candidate_edges > 0:
        focus.append("evidence span repair")
    if high_impact > 0:
        focus.append("high-impact review")
    if not focus:
        focus.append("standard candidate review")

    return {
        "rank": tracking.get("rank", ""),
        "chunk_id": row.get("chunk_id", ""),
        "page_start": row.get("page_start", ""),
        "page_end": row.get("page_end", ""),
        "priority_score": tracking.get("priority_score", ""),
        "priority_reason": tracking.get("priority_reason", ""),
        "candidate_edges": candidate_edges,
        "top_predicates": short_counter(predicate_counts),
        "unique_evidence_anchors": len(evidence_ids),
        "component_spans": component_count,
        "exact_components": exact_components,
        "exact_component_ratio": fmt_ratio(exact_ratio),
        "full_sentence_proxy_components": full_sentence_proxy,
        "label_not_found_components": label_not_found,
        "active_review_items": active_items,
        "high_impact_items": high_impact,
        "review_focus": "; ".join(focus),
    }


def render_batch_preview(batch_id, summary_row, preview_rows):
    lines = [
        f"# {batch_id} Review Preview",
        "",
        "이 문서는 사람 검수자가 batch를 열기 전에 candidate edge 밀도와 evidence span 품질을 빠르게 확인하기 위한 보조 자료입니다.",
        "자동 후보를 gold로 확정하지 않으며, 최종 판단은 annotator/adjudicator가 원문 chunk text만 근거로 수행해야 합니다.",
        "",
        "## Batch Summary",
        "",
        f"- chunks: {summary_row['chunk_count']}",
        f"- candidate edges: {summary_row['candidate_edges_total']}",
        f"- avg candidate edges per chunk: {summary_row['candidate_edges_per_chunk_avg']}",
        f"- exact component ratio: {summary_row['exact_component_ratio']}",
        f"- chunks needing span attention: {summary_row['chunks_needing_span_attention']}",
        f"- dense candidate chunks: {summary_row['dense_candidate_chunks']}",
        f"- zero candidate chunks: {summary_row['zero_candidate_chunks']}",
        f"- high-impact chunks: {summary_row['high_impact_chunks']}",
        "",
        "## Chunk Preview",
        "",
        "| rank | chunk_id | pages | candidates | exact ratio | top predicates | review focus |",
        "| --- | --- | --- | ---: | ---: | --- | --- |",
    ]
    for row in preview_rows:
        lines.append(
            "| {rank} | `{chunk_id}` | {page_start}-{page_end} | {candidate_edges} | {exact_component_ratio} | {top_predicates} | {review_focus} |".format(
                **row
            )
        )
    lines += [
        "",
        "## 해석",
        "",
        "- `dense candidate pruning`: 후보가 많아 accept/reject 판단 시간이 많이 걸릴 수 있습니다.",
        "- `evidence span repair`: 자동 component span이 exact하지 않으므로 accepted edge에는 사람이 evidence를 더 엄격히 확인해야 합니다.",
        "- `missing-edge scan`: 자동 후보가 거의 없으므로 원문에서 직접 지지되는 빠진 edge가 있는지 확인해야 합니다.",
        "- `high-impact review`: evidence, schema, risk, gateway, central task-flow에 영향을 줄 수 있어 우선 검토합니다.",
        "",
    ]
    return "\n".join(lines)


def render_summary(payload):
    lines = [
        "# CAPE-KG Annotation Batch Review Preview Summary",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Experiment: `{payload['experiment_dir']}`",
        "",
        "이 문서는 priority 100 human-gold annotation batch의 candidate edge/span preview를 요약합니다.",
        "gold annotation 결과가 아니라, annotator가 검수 난이도와 evidence span 주의 지점을 먼저 파악하기 위한 handoff 보조 자료입니다.",
        "",
        "## Summary",
        "",
        f"- claim_status: `{payload['claim_status']}`",
        f"- batches: {payload['batch_count']}",
        f"- chunks: {payload['chunk_count']}",
        f"- candidate edges: {payload['candidate_edges_total']}",
        f"- exact component ratio: {payload['exact_component_ratio']}",
        f"- chunks needing span attention: {payload['chunks_needing_span_attention']}",
        f"- dense candidate chunks: {payload['dense_candidate_chunks']}",
        f"- zero candidate chunks: {payload['zero_candidate_chunks']}",
        "",
        "## Batches",
        "",
        "| batch | chunks | candidates | exact ratio | span attention | dense | zero | high-impact | preview |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in payload["batches"]:
        lines.append(
            "| `{batch_id}` | {chunk_count} | {candidate_edges_total} | {exact_component_ratio} | {chunks_needing_span_attention} | {dense_candidate_chunks} | {zero_candidate_chunks} | {high_impact_chunks} | `{preview_md}` |".format(
                **row
            )
        )
    lines += [
        "",
        "## Output Files",
        "",
        f"- JSON: `{payload['outputs']['json']}`",
        f"- Markdown: `{payload['outputs']['markdown']}`",
        f"- CSV: `{payload['outputs']['csv']}`",
        "",
    ]
    return "\n".join(lines)


def render_strong_package_preview(package_id, summary_row, preview_rows):
    lines = [
        f"# {package_id} Strong Review Preview",
        "",
        "이 문서는 optional strong 300+ human review package를 시작하기 전에 review unit별 candidate edge 밀도와 evidence span 품질을 확인하기 위한 보조 자료입니다.",
        "자동 후보를 gold로 확정하지 않으며, 최종 판단은 annotator/adjudicator가 split text와 source sentence evidence만 근거로 수행해야 합니다.",
        "",
        "## Package Summary",
        "",
        f"- review units: {summary_row['chunk_count']}",
        f"- source chunks represented: {summary_row['source_chunk_count']}",
        f"- candidate edges: {summary_row['candidate_edges_total']}",
        f"- avg candidate edges per unit: {summary_row['candidate_edges_per_chunk_avg']}",
        f"- exact component ratio: {summary_row['exact_component_ratio']}",
        f"- units needing span attention: {summary_row['chunks_needing_span_attention']}",
        f"- dense candidate units: {summary_row['dense_candidate_chunks']}",
        f"- zero candidate units: {summary_row['zero_candidate_chunks']}",
        "",
        "## Top Review Attention Units",
        "",
        "| rank | review_unit | source_chunk | pages | candidates | exact ratio | top predicates | review focus |",
        "| ---: | --- | --- | --- | ---: | ---: | --- | --- |",
    ]
    ranked = sorted(
        preview_rows,
        key=lambda row: (
            "evidence span repair" not in row.get("review_focus", ""),
            "dense candidate pruning" not in row.get("review_focus", ""),
            -as_int(row.get("candidate_edges")),
            row.get("chunk_id", ""),
        ),
    )
    for idx, row in enumerate(ranked[:50], start=1):
        lines.append(
            "| {idx} | `{chunk_id}` | `{source_chunk_id}` | {page_start}-{page_end} | {candidate_edges} | {exact_component_ratio} | {top_predicates} | {review_focus} |".format(
                idx=idx,
                **row,
            )
        )
    lines += [
        "",
        "## 해석",
        "",
        "- `dense candidate pruning`: 후보가 많아 accept/reject 판단 시간이 많이 걸릴 수 있습니다.",
        "- `evidence span repair`: 자동 component span이 exact하지 않으므로 accepted edge에는 사람이 evidence를 더 엄격히 확인해야 합니다.",
        "- `missing-edge scan`: 자동 후보가 거의 없으므로 split text에서 직접 지지되는 빠진 edge가 있는지 확인해야 합니다.",
        "- 이 preview는 300+ strong-paper scale scaffold의 검수 난이도 보조 자료이며, completed human-gold evidence가 아닙니다.",
        "",
    ]
    return "\n".join(lines)


def render_strong_summary(payload):
    lines = [
        "# CAPE-KG Strong Resegmented Review Preview Summary",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Experiment: `{payload['experiment_dir']}`",
        "",
        "이 문서는 optional strong 300+ resegmented human-review package의 candidate edge/span preview를 요약합니다.",
        "gold annotation 결과가 아니라, 300+ 검수를 시작할 때 review unit 밀도와 evidence span 주의 지점을 파악하기 위한 handoff 보조 자료입니다.",
        "",
        "## Summary",
        "",
        f"- claim_status: `{payload['claim_status']}`",
        f"- package: `{payload['package_id']}`",
        f"- review units: {payload['review_unit_count']}",
        f"- source chunks represented: {payload['source_chunk_count']}",
        f"- candidate edges: {payload['candidate_edges_total']}",
        f"- exact component ratio: {payload['exact_component_ratio']}",
        f"- units needing span attention: {payload['chunks_needing_span_attention']}",
        f"- dense candidate units: {payload['dense_candidate_chunks']}",
        f"- zero candidate units: {payload['zero_candidate_chunks']}",
        "",
        "## Output Files",
        "",
        f"- JSON: `{payload['outputs']['json']}`",
        f"- Markdown: `{payload['outputs']['markdown']}`",
        f"- CSV: `{payload['outputs']['csv']}`",
        f"- Package preview CSV: `{payload['package_preview_csv']}`",
        f"- Package preview Markdown: `{payload['package_preview_md']}`",
        "",
    ]
    return "\n".join(lines)


def strong_preview_row(row, tracking):
    preview = chunk_preview(row, tracking)
    preview["source_chunk_id"] = row.get("source_chunk_id", row.get("chunk_id", ""))
    preview["split_index"] = row.get("split_index", "")
    preview["split_sentence_count"] = len(row.get("split_sentence_ids") or row.get("sentence_ids") or [])
    preview["split_max_sentences"] = row.get("split_max_sentences", "")
    return preview


def build_strong_preview(exp_dir):
    exp_dir = Path(exp_dir)
    release_dir = exp_dir / "06_release"
    review_dir = exp_dir / "05_review"
    root = exp_dir / "01_data/gold_annotation"
    manifest = read_json(root / "annotation_expansion_manifest.json", {}) or {}
    package_id = manifest.get("strong_resegmented_package") or ""
    if not package_id:
        return None
    package_dir = root / package_id
    input_file = package_dir / "annotator_A.jsonl"
    tracking_rows = read_csv(package_dir / "tracking_sheet.csv")
    tracking_by_chunk = {row.get("chunk_id"): row for row in tracking_rows}
    rows = read_jsonl(input_file)
    if not rows:
        return None

    preview_rows = [strong_preview_row(row, tracking_by_chunk.get(row.get("chunk_id"), {})) for row in rows]
    candidate_edges = sum(as_int(row["candidate_edges"]) for row in preview_rows)
    component_spans = sum(as_int(row["component_spans"]) for row in preview_rows)
    exact_components = sum(as_int(row["exact_components"]) for row in preview_rows)
    full_sentence_proxy = sum(as_int(row["full_sentence_proxy_components"]) for row in preview_rows)
    label_not_found = sum(as_int(row["label_not_found_components"]) for row in preview_rows)
    span_attention = sum(1 for row in preview_rows if as_float(row["exact_component_ratio"]) < 0.50 and as_int(row["candidate_edges"]) > 0)
    dense = sum(1 for row in preview_rows if as_int(row["candidate_edges"]) >= 40)
    zero = sum(1 for row in preview_rows if as_int(row["candidate_edges"]) == 0)
    source_chunk_count = len({row.get("source_chunk_id") for row in preview_rows if row.get("source_chunk_id")})

    package_preview_csv = package_dir / "strong_review_preview.csv"
    package_preview_md = package_dir / "strong_review_preview.md"
    summary_csv = review_dir / "strong_resegmented_review_preview_summary.csv"
    outputs = {
        "json": str(release_dir / "strong_resegmented_review_preview_summary.json"),
        "markdown": str(release_dir / "strong_resegmented_review_preview_summary.md"),
        "csv": str(summary_csv),
    }
    summary_row = {
        "batch_id": package_id,
        "rank_start": 1,
        "rank_end": len(preview_rows),
        "chunk_count": len(preview_rows),
        "source_chunk_count": source_chunk_count,
        "candidate_edges_total": candidate_edges,
        "candidate_edges_per_chunk_avg": fmt_ratio(candidate_edges / len(preview_rows) if preview_rows else 0.0),
        "exact_component_ratio": fmt_ratio(ratio(exact_components, component_spans)),
        "full_sentence_proxy_components": full_sentence_proxy,
        "label_not_found_components": label_not_found,
        "chunks_needing_span_attention": span_attention,
        "zero_candidate_chunks": zero,
        "dense_candidate_chunks": dense,
        "high_impact_chunks": 0,
        "preview_csv": str(package_preview_csv),
        "preview_md": str(package_preview_md),
    }
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "claim_status": "strong_resegmented_review_preview_ready_not_gold_evidence",
        "package_id": package_id,
        "package_dir": str(package_dir),
        "review_unit_count": len(preview_rows),
        "source_chunk_count": source_chunk_count,
        "candidate_edges_total": candidate_edges,
        "exact_component_ratio": fmt_ratio(ratio(exact_components, component_spans)),
        "component_spans_total": component_spans,
        "exact_components_total": exact_components,
        "chunks_needing_span_attention": span_attention,
        "dense_candidate_chunks": dense,
        "zero_candidate_chunks": zero,
        "package_preview_csv": str(package_preview_csv),
        "package_preview_md": str(package_preview_md),
        "summary": summary_row,
        "outputs": outputs,
    }
    strong_fields = PREVIEW_FIELDS + ["source_chunk_id", "split_index", "split_sentence_count", "split_max_sentences"]
    write_csv(package_preview_csv, preview_rows, strong_fields)
    write_text(package_preview_md, render_strong_package_preview(package_id, summary_row, preview_rows))
    write_json(outputs["json"], payload)
    write_text(outputs["markdown"], render_strong_summary(payload))
    write_csv(summary_csv, [summary_row], SUMMARY_FIELDS + ["source_chunk_count"])
    return payload


def build(args):
    exp_dir = Path(args.experiment_dir)
    review_dir = exp_dir / "05_review"
    release_dir = exp_dir / "06_release"
    batch_root = review_dir / "human_gold_batches"
    assignment = read_json(release_dir / "annotation_batch_assignment_summary.json", {}) or {}
    batches = assignment.get("batches") or []
    summary_rows = []
    all_candidate_edges = 0
    all_component_spans = 0
    all_exact_components = 0
    all_span_attention = 0
    all_dense = 0
    all_zero = 0
    all_high_impact = 0
    all_chunk_count = 0

    for batch in batches:
        batch_id = batch.get("batch_id")
        if not batch_id:
            continue
        batch_dir = batch_root / batch_id
        input_file = batch_dir / f"annotator_A_{batch_id}.jsonl"
        tracking_rows = read_csv(batch_dir / "batch_tracking_sheet.csv")
        tracking_by_chunk = {row.get("chunk_id"): row for row in tracking_rows}
        rows = read_jsonl(input_file)
        preview_rows = []
        for row in rows:
            preview = chunk_preview(row, tracking_by_chunk.get(row.get("chunk_id"), {}))
            preview_rows.append(preview)

        candidate_edges = sum(as_int(row["candidate_edges"]) for row in preview_rows)
        component_spans = sum(as_int(row["component_spans"]) for row in preview_rows)
        exact_components = sum(as_int(row["exact_components"]) for row in preview_rows)
        full_sentence_proxy = sum(as_int(row["full_sentence_proxy_components"]) for row in preview_rows)
        label_not_found = sum(as_int(row["label_not_found_components"]) for row in preview_rows)
        span_attention = sum(1 for row in preview_rows if as_float(row["exact_component_ratio"]) < 0.50 and as_int(row["candidate_edges"]) > 0)
        dense = sum(1 for row in preview_rows if as_int(row["candidate_edges"]) >= 40)
        zero = sum(1 for row in preview_rows if as_int(row["candidate_edges"]) == 0)
        high_impact = sum(1 for row in preview_rows if as_int(row["high_impact_items"]) > 0)

        preview_csv = batch_dir / "batch_review_preview.csv"
        preview_md = batch_dir / "batch_review_preview.md"
        summary_row = {
            "batch_id": batch_id,
            "rank_start": batch.get("rank_start"),
            "rank_end": batch.get("rank_end"),
            "chunk_count": len(preview_rows),
            "candidate_edges_total": candidate_edges,
            "candidate_edges_per_chunk_avg": fmt_ratio(candidate_edges / len(preview_rows) if preview_rows else 0.0),
            "exact_component_ratio": fmt_ratio(ratio(exact_components, component_spans)),
            "full_sentence_proxy_components": full_sentence_proxy,
            "label_not_found_components": label_not_found,
            "chunks_needing_span_attention": span_attention,
            "zero_candidate_chunks": zero,
            "dense_candidate_chunks": dense,
            "high_impact_chunks": high_impact,
            "preview_csv": str(preview_csv),
            "preview_md": str(preview_md),
        }
        write_csv(preview_csv, preview_rows, PREVIEW_FIELDS)
        write_text(preview_md, render_batch_preview(batch_id, summary_row, preview_rows))
        summary_rows.append(summary_row)

        all_candidate_edges += candidate_edges
        all_component_spans += component_spans
        all_exact_components += exact_components
        all_span_attention += span_attention
        all_dense += dense
        all_zero += zero
        all_high_impact += high_impact
        all_chunk_count += len(preview_rows)

    outputs = {
        "json": str(release_dir / "annotation_batch_review_preview_summary.json"),
        "markdown": str(release_dir / "annotation_batch_review_preview_summary.md"),
        "csv": str(review_dir / "annotation_batch_review_preview_summary.csv"),
    }
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "claim_status": "annotation_batch_review_preview_ready_not_gold_evidence",
        "batch_count": len(summary_rows),
        "chunk_count": all_chunk_count,
        "candidate_edges_total": all_candidate_edges,
        "exact_component_ratio": fmt_ratio(ratio(all_exact_components, all_component_spans)),
        "component_spans_total": all_component_spans,
        "exact_components_total": all_exact_components,
        "chunks_needing_span_attention": all_span_attention,
        "dense_candidate_chunks": all_dense,
        "zero_candidate_chunks": all_zero,
        "high_impact_chunks": all_high_impact,
        "batches": summary_rows,
        "outputs": outputs,
    }
    write_json(outputs["json"], payload)
    write_text(outputs["markdown"], render_summary(payload))
    write_csv(outputs["csv"], summary_rows, SUMMARY_FIELDS)
    strong_payload = build_strong_preview(exp_dir)
    if strong_payload:
        outputs["strong_json"] = strong_payload["outputs"]["json"]
        outputs["strong_markdown"] = strong_payload["outputs"]["markdown"]
        outputs["strong_csv"] = strong_payload["outputs"]["csv"]
    print(json.dumps(outputs, ensure_ascii=False, indent=2))


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    return parser.parse_args()


if __name__ == "__main__":
    build(parse_args())
