#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build component-level evidence span diagnostics for CAPE-KG triples.

The current KG stores sentence evidence anchors for accepted triples. This
script derives subject/object lexical character spans when their labels appear
in the evidence sentence, and records predicate evidence as a sentence-level
proxy. It is a grounding diagnostic, not human-gold span annotation.
"""

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_OUTPUTS_DIR = Path("outputs")

CSV_FIELDS = [
    "triple_id",
    "component",
    "label",
    "predicate",
    "chunk_id",
    "sentence_id",
    "page",
    "span_method",
    "span_exact",
    "sentence_span_start",
    "sentence_span_end",
    "chunk_span_start",
    "chunk_span_end",
    "text",
]


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


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in CSV_FIELDS})


def first_nonempty(values):
    for value in values:
        if value:
            return value
    return ""


def find_label_span(text, label):
    text = str(text or "")
    label = str(label or "").strip()
    if not text or not label:
        return None
    idx = text.find(label)
    if idx >= 0:
        return idx, idx + len(label), text[idx: idx + len(label)], "exact_label_match"
    lowered_idx = text.lower().find(label.lower())
    if lowered_idx >= 0:
        return lowered_idx, lowered_idx + len(label), text[lowered_idx: lowered_idx + len(label)], "case_insensitive_label_match"
    compact_label = "".join(label.split())
    compact_text = "".join(text.split())
    if compact_label and compact_label in compact_text:
        # Compact matching proves presence but not reliable offsets in the original string.
        return None
    return None


def chunk_sentence_offsets(outputs_dir):
    mapping = {}
    for chunk in read_jsonl(outputs_dir / "02_ocr/layer2_chunks.jsonl"):
        chunk_id = chunk.get("chunk_id")
        for offset in chunk.get("sentence_offsets", []):
            sentence_id = offset.get("sentence_id")
            if chunk_id and sentence_id:
                mapping[(chunk_id, sentence_id)] = (
                    offset.get("chunk_char_start"),
                    offset.get("chunk_char_end"),
                )
    return mapping


def anchor_by_id(outputs_dir):
    anchors = {}
    for row in read_jsonl(outputs_dir / "06_triples/evidence_anchors.jsonl"):
        anchor_id = row.get("evidence_anchor_id")
        if anchor_id:
            anchors[anchor_id] = row
    return anchors


def span_row(triple, component, label, sentence_id, anchor, evidence_text, sentence_offsets, span, method, exact):
    chunk_id = (triple.get("evidence") or {}).get("chunk_id")
    sentence_start = ""
    sentence_end = ""
    chunk_start = ""
    chunk_end = ""
    span_text = ""
    if span:
        sentence_start, sentence_end, span_text, method = span
        offset = sentence_offsets.get((chunk_id, sentence_id))
        if offset and offset[0] is not None:
            chunk_start = int(offset[0]) + int(sentence_start)
            chunk_end = int(offset[0]) + int(sentence_end)
    elif method == "full_sentence_proxy":
        sentence_start = 0
        sentence_end = len(evidence_text or "")
        span_text = evidence_text or ""
        offset = sentence_offsets.get((chunk_id, sentence_id))
        if offset and offset[0] is not None:
            chunk_start = int(offset[0])
            chunk_end = int(offset[0]) + len(evidence_text or "")
    return {
        "triple_id": triple.get("triple_id"),
        "component": component,
        "label": label,
        "predicate": triple.get("predicate"),
        "chunk_id": chunk_id,
        "sentence_id": sentence_id,
        "page": anchor.get("page") if anchor else "",
        "span_method": method,
        "span_exact": bool(exact),
        "sentence_span_start": sentence_start,
        "sentence_span_end": sentence_end,
        "chunk_span_start": chunk_start,
        "chunk_span_end": chunk_end,
        "text": span_text,
    }


def component_rows_for_triple(triple, anchors, sentence_offsets):
    evidence = triple.get("evidence") or {}
    evidence_text = evidence.get("evidence_text") or ""
    sentence_id = first_nonempty(evidence.get("sentence_ids") or [])
    subject = triple.get("subject") or {}
    obj = triple.get("object") or {}
    subject_anchor = anchors.get(subject.get("evidence_anchor_id")) or {}
    object_anchor = anchors.get(obj.get("evidence_anchor_id")) or {}
    fallback_anchor = subject_anchor or object_anchor

    subject_label = subject.get("label") or ""
    object_label = obj.get("label") or ""
    subject_span = find_label_span(evidence_text, subject_label)
    object_span = find_label_span(evidence_text, object_label)
    rows = [
        span_row(
            triple,
            "subject",
            subject_label,
            sentence_id,
            subject_anchor or fallback_anchor,
            evidence_text,
            sentence_offsets,
            subject_span,
            "label_not_found_in_sentence",
            bool(subject_span),
        ),
        span_row(
            triple,
            "predicate",
            triple.get("predicate") or "",
            sentence_id,
            fallback_anchor,
            evidence_text,
            sentence_offsets,
            None,
            "full_sentence_proxy",
            False,
        ),
        span_row(
            triple,
            "object",
            object_label,
            sentence_id,
            object_anchor or fallback_anchor,
            evidence_text,
            sentence_offsets,
            object_span,
            "label_not_found_in_sentence",
            bool(object_span),
        ),
    ]
    return rows


def build_payload(exp_dir, outputs_dir):
    triples = read_jsonl(outputs_dir / "06_triples/layer2_triples_schema_valid.jsonl")
    anchors = anchor_by_id(outputs_dir)
    sentence_offsets = chunk_sentence_offsets(outputs_dir)
    enriched = []
    flat_rows = []
    counts = Counter()
    for triple in triples:
        component_rows = component_rows_for_triple(triple, anchors, sentence_offsets)
        flat_rows.extend(component_rows)
        for row in component_rows:
            counts[f"{row['component']}.{row['span_method']}"] += 1
            if row["span_exact"]:
                counts[f"{row['component']}.exact"] += 1
            if row["chunk_span_start"] != "":
                counts[f"{row['component']}.chunk_span"] += 1
        enriched.append({**triple, "component_evidence_spans": component_rows})

    triple_count = len(triples)
    component_count = len(flat_rows)
    exact_components = sum(1 for row in flat_rows if row["span_exact"])
    chunk_spans = sum(1 for row in flat_rows if row["chunk_span_start"] != "")
    subject_exact = counts.get("subject.exact", 0)
    object_exact = counts.get("object.exact", 0)
    predicate_proxy = counts.get("predicate.full_sentence_proxy", 0)
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "outputs_dir": str(outputs_dir),
        "triple_count": triple_count,
        "component_count": component_count,
        "exact_component_span_count": exact_components,
        "exact_component_span_rate": round(exact_components / component_count, 6) if component_count else 0.0,
        "chunk_span_count": chunk_spans,
        "chunk_span_rate": round(chunk_spans / component_count, 6) if component_count else 0.0,
        "subject_exact_span_count": subject_exact,
        "subject_exact_span_rate": round(subject_exact / triple_count, 6) if triple_count else 0.0,
        "object_exact_span_count": object_exact,
        "object_exact_span_rate": round(object_exact / triple_count, 6) if triple_count else 0.0,
        "predicate_full_sentence_proxy_count": predicate_proxy,
        "predicate_full_sentence_proxy_rate": round(predicate_proxy / triple_count, 6) if triple_count else 0.0,
        "method_counts": dict(counts),
        "claim_status": "automatic_component_span_diagnostic_not_human_gold",
        "limitations": [
            "Subject/object spans are lexical exact-match diagnostics.",
            "Predicate spans use full-sentence proxy support rather than predicate-token annotation.",
            "Final evidence exactness claims require adjudicated human-gold spans.",
        ],
    }
    return summary, enriched, flat_rows


def render_report(summary):
    lines = [
        "# CAPE-KG Component Evidence Span Granularity Report",
        "",
        f"Generated: {summary['generated_at_utc']}",
        "",
        "This report audits how far the current evidence grounding goes beyond sentence anchors.",
        "It derives subject/object lexical character spans when labels appear in the evidence sentence and marks predicate support as a full-sentence proxy.",
        "It is not a human-gold span evaluation.",
        "",
        "## Summary",
        "",
        f"- Triples: {summary['triple_count']}",
        f"- Components: {summary['component_count']}",
        f"- Exact component spans: {summary['exact_component_span_count']} ({summary['exact_component_span_rate']})",
        f"- Components with chunk-local spans: {summary['chunk_span_count']} ({summary['chunk_span_rate']})",
        f"- Subject exact spans: {summary['subject_exact_span_count']} ({summary['subject_exact_span_rate']})",
        f"- Object exact spans: {summary['object_exact_span_count']} ({summary['object_exact_span_rate']})",
        f"- Predicate full-sentence proxies: {summary['predicate_full_sentence_proxy_count']} ({summary['predicate_full_sentence_proxy_rate']})",
        f"- Claim status: `{summary['claim_status']}`",
        "",
        "## Method Counts",
        "",
        "| key | count |",
        "|---|---:|",
    ]
    for key, value in sorted(summary["method_counts"].items()):
        lines.append(f"| {key} | {value} |")
    lines += [
        "",
        "## Interpretation",
        "",
        "- Sentence-level evidence coverage is already present in the KG.",
        "- This diagnostic adds component-level lexical spans for subject/object labels where possible.",
        "- Predicate evidence is still sentence-level proxy evidence; human annotation is needed for predicate-token evidence spans.",
        "- Use this file to document evidence-grounding granularity honestly before human-gold span scoring.",
        "",
    ]
    return "\n".join(lines)


def run(args):
    exp_dir = Path(args.experiment_dir)
    outputs_dir = Path(args.outputs_dir)
    summary, enriched, flat_rows = build_payload(exp_dir, outputs_dir)

    jsonl_path = outputs_dir / "06_triples/layer2_triples_component_spans.jsonl"
    csv_path = exp_dir / "04_evaluation/evidence_span_granularity_components.csv"
    metrics_path = exp_dir / "04_evaluation/evidence_span_granularity_metrics.json"
    report_path = exp_dir / "04_evaluation/evidence_span_granularity_report.md"

    summary["output_files"] = {
        "component_spans_jsonl": str(jsonl_path),
        "component_spans_csv": str(csv_path),
        "metrics_json": str(metrics_path),
        "report_md": str(report_path),
    }

    write_jsonl(jsonl_path, enriched)
    write_csv(csv_path, flat_rows)
    write_json(metrics_path, summary)
    write_text(report_path, render_report(summary))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--outputs-dir", default=str(DEFAULT_OUTPUTS_DIR))
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
