#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Evaluate component-level evidence span exact/IoU against human gold.

This evaluator is intentionally conservative. It only produces paper-claimable
span metrics for completed/adjudicated chunks. Before human adjudication, it
writes pending artifacts so the post-human pipeline is ready and auditable.
"""

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
COMPLETED_ADJUDICATION_STATUSES = {
    "adjudicated",
    "completed",
    "complete",
    "final",
    "accepted",
    "no_disagreement_adjudicated",
}
REJECTED_EDGE_DECISIONS = {"reject", "rejected", "unsupported", "remove", "removed"}
COMPONENTS = ("subject", "predicate", "object")

COMPONENT_FIELDNAMES = [
    "chunk_id",
    "edge_key",
    "component",
    "gold_sentence_id",
    "candidate_sentence_id",
    "gold_start",
    "gold_end",
    "candidate_start",
    "candidate_end",
    "iou",
    "exact_match",
    "gold_text",
    "candidate_text",
]


def read_jsonl(path):
    rows = []
    path = Path(path)
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            row["_line_no"] = line_no
            rows.append(row)
    return rows


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


def rel(path):
    return str(Path(path).as_posix())


def norm_label(value):
    value = str(value or "").strip().lower()
    value = re.sub(r"\s+", "", value)
    value = re.sub(r"[`'\"“”‘’()\[\]{}<>:;,.!?/\\|_-]+", "", value)
    return value


def norm_text(value):
    return " ".join(str(value or "").strip().split()).lower()


def norm_predicate(value):
    return str(value or "").strip().upper()


def norm_evidence_id(value):
    value = str(value or "").strip()
    if value.startswith("EA-"):
        value = value[3:]
    return value


def status_value(row):
    return norm_text(row.get("adjudication_status") or row.get("annotation_status"))


def is_completed_adjudication(row):
    return status_value(row) in COMPLETED_ADJUDICATION_STATUSES


def edge_decision(edge):
    return norm_text(edge.get("decision") or edge.get("adjudication_decision") or edge.get("status"))


def is_rejected_edge(edge):
    return edge_decision(edge) in REJECTED_EDGE_DECISIONS


def edge_label(edge, side):
    if side == "source":
        return edge.get("source_label") or edge.get("subject") or edge.get("source") or edge.get("source_id")
    return edge.get("target_label") or edge.get("object") or edge.get("target") or edge.get("target_id")


def edge_key(chunk_id, edge):
    return (
        chunk_id,
        norm_label(edge_label(edge, "source")),
        norm_predicate(edge.get("predicate") or edge.get("edge_type")),
        norm_label(edge_label(edge, "target")),
    )


def edge_key_text(key):
    return "::".join(str(part) for part in key)


def int_or_none(value):
    if value in ("", None):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def span_anchor(span):
    return norm_evidence_id(span.get("evidence_anchor_id") or span.get("sentence_id"))


def span_start_end(span):
    start = int_or_none(span.get("sentence_span_start"))
    end = int_or_none(span.get("sentence_span_end"))
    if start is None or end is None:
        start = int_or_none(span.get("start_char"))
        end = int_or_none(span.get("end_char"))
    return start, end


def usable_span(span):
    start, end = span_start_end(span)
    anchor = span_anchor(span)
    return anchor, start, end


def valid_range(start, end):
    return start is not None and end is not None and end >= start


def span_iou(gold_span, candidate_span):
    gold_anchor, gold_start, gold_end = usable_span(gold_span)
    cand_anchor, cand_start, cand_end = usable_span(candidate_span)
    if not gold_anchor or not cand_anchor or gold_anchor != cand_anchor:
        return 0.0
    if not valid_range(gold_start, gold_end) or not valid_range(cand_start, cand_end):
        return 0.0
    intersection = max(0, min(gold_end, cand_end) - max(gold_start, cand_start))
    union = max(gold_end, cand_end) - min(gold_start, cand_start)
    if union <= 0:
        return 0.0
    return intersection / union


def span_exact(gold_span, candidate_span):
    gold_anchor, gold_start, gold_end = usable_span(gold_span)
    cand_anchor, cand_start, cand_end = usable_span(candidate_span)
    return (
        bool(gold_anchor)
        and gold_anchor == cand_anchor
        and valid_range(gold_start, gold_end)
        and gold_start == cand_start
        and gold_end == cand_end
    )


def component_spans(edge):
    spans = defaultdict(list)
    for span in edge.get("component_evidence_spans") or []:
        component = str(span.get("component") or "").strip().lower()
        if component in COMPONENTS:
            spans[component].append(span)
    return spans


def best_component_match(gold_span, candidate_spans):
    if not candidate_spans:
        return None, 0.0, False
    best = None
    best_iou = -1.0
    best_exact = False
    for candidate in candidate_spans:
        iou = span_iou(gold_span, candidate)
        exact = span_exact(gold_span, candidate)
        if exact or iou > best_iou:
            best = candidate
            best_iou = iou
            best_exact = exact
        if exact:
            break
    return best, max(0.0, best_iou), bool(best_exact)


def edge_match_score(gold_edge, candidate_edge):
    gold_spans = component_spans(gold_edge)
    candidate_spans = component_spans(candidate_edge)
    scores = []
    for component in COMPONENTS:
        for gold_span in gold_spans.get(component) or []:
            _, iou, exact = best_component_match(gold_span, candidate_spans.get(component) or [])
            scores.append(1.0 if exact else iou)
    if not scores:
        return 0.0
    return sum(scores) / len(scores)


def load_candidates(candidate_file):
    candidates_by_chunk_key = defaultdict(list)
    candidate_rows = read_jsonl(candidate_file)
    candidate_edge_count = 0
    candidate_component_span_count = 0
    for row in candidate_rows:
        chunk_id = row.get("chunk_id")
        for edge in row.get("silver_candidate_edges") or row.get("candidate_edges") or row.get("gold_edges") or []:
            key = edge_key(chunk_id, edge)
            if not all(key):
                continue
            candidate_edge_count += 1
            candidate_component_span_count += sum(len(v) for v in component_spans(edge).values())
            candidates_by_chunk_key[key].append(edge)
    return candidates_by_chunk_key, {
        "candidate_rows": len(candidate_rows),
        "candidate_edge_count": candidate_edge_count,
        "candidate_component_span_count": candidate_component_span_count,
    }


def completed_gold_edges(adjudication_rows):
    status_counts = Counter()
    completed_chunks = 0
    gold_edges = []
    gold_component_span_count = 0
    for row in adjudication_rows:
        status_counts[status_value(row) or "missing"] += 1
        if not is_completed_adjudication(row):
            continue
        completed_chunks += 1
        chunk_id = row.get("chunk_id")
        for edge in row.get("adjudicated_gold_edges") or row.get("gold_edges") or []:
            if is_rejected_edge(edge):
                continue
            key = edge_key(chunk_id, edge)
            if not all(key):
                continue
            spans = component_spans(edge)
            gold_component_span_count += sum(len(v) for v in spans.values())
            gold_edges.append((key, edge))
    return gold_edges, {
        "completed_adjudicated_chunks": completed_chunks,
        "status_counts": dict(sorted(status_counts.items())),
        "gold_edge_count": len(gold_edges),
        "gold_component_span_count": gold_component_span_count,
    }


def evaluate(adjudication_file, candidate_file):
    adjudication_rows = read_jsonl(adjudication_file)
    candidate_by_key, candidate_summary = load_candidates(candidate_file)
    gold_edges, gold_summary = completed_gold_edges(adjudication_rows)
    used_candidate_ids = set()
    component_rows = []
    matched_edge_count = 0

    for key, gold_edge in gold_edges:
        candidates = candidate_by_key.get(key) or []
        best_candidate = None
        best_score = -1.0
        best_index = -1
        for index, candidate in enumerate(candidates):
            candidate_identity = (key, index)
            if candidate_identity in used_candidate_ids:
                continue
            score = edge_match_score(gold_edge, candidate)
            if score > best_score:
                best_candidate = candidate
                best_score = score
                best_index = index
        if best_candidate is None:
            continue
        used_candidate_ids.add((key, best_index))
        matched_edge_count += 1
        candidate_spans = component_spans(best_candidate)
        for component, spans in component_spans(gold_edge).items():
            for gold_span in spans:
                candidate_span, iou, exact = best_component_match(gold_span, candidate_spans.get(component) or [])
                gold_anchor, gold_start, gold_end = usable_span(gold_span)
                cand_anchor, cand_start, cand_end = usable_span(candidate_span or {})
                component_rows.append(
                    {
                        "chunk_id": key[0],
                        "edge_key": edge_key_text(key),
                        "component": component,
                        "gold_sentence_id": gold_anchor,
                        "candidate_sentence_id": cand_anchor,
                        "gold_start": "" if gold_start is None else gold_start,
                        "gold_end": "" if gold_end is None else gold_end,
                        "candidate_start": "" if cand_start is None else cand_start,
                        "candidate_end": "" if cand_end is None else cand_end,
                        "iou": round(iou, 6),
                        "exact_match": bool(exact),
                        "gold_text": gold_span.get("text") or "",
                        "candidate_text": (candidate_span or {}).get("text") or "",
                    }
                )

    component_count = len(component_rows)
    exact_count = sum(1 for row in component_rows if row["exact_match"])
    mean_iou = sum(float(row["iou"]) for row in component_rows) / component_count if component_count else None
    span_exact_rate = exact_count / component_count if component_count else None
    component_counts = Counter(row["component"] for row in component_rows)
    component_iou = {}
    component_exact = {}
    for component in COMPONENTS:
        rows = [row for row in component_rows if row["component"] == component]
        if not rows:
            component_iou[component] = None
            component_exact[component] = None
            continue
        component_iou[component] = round(sum(float(row["iou"]) for row in rows) / len(rows), 6)
        component_exact[component] = round(sum(1 for row in rows if row["exact_match"]) / len(rows), 6)

    if gold_summary["completed_adjudicated_chunks"] == 0:
        claim_status = "pending_human_adjudication"
    elif gold_summary["gold_component_span_count"] == 0:
        claim_status = "pending_human_component_spans"
    else:
        claim_status = "human_gold_span_iou_scored"

    summary = {
        "adjudication_file": rel(adjudication_file),
        "candidate_file": rel(candidate_file),
        **candidate_summary,
        **gold_summary,
        "matched_edge_count": matched_edge_count,
        "matched_component_span_count": component_count,
        "component_counts": dict(sorted(component_counts.items())),
        "span_exact_match_rate": None if span_exact_rate is None else round(span_exact_rate, 6),
        "mean_span_iou": None if mean_iou is None else round(mean_iou, 6),
        "component_exact_match_rate": component_exact,
        "component_mean_iou": component_iou,
        "claim_status": claim_status,
    }
    return summary, component_rows


def render_report(payload):
    summary = payload["summary"]
    lines = [
        "# CAPE-KG Human-Gold Component Span IoU",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Claim status: `{summary['claim_status']}`",
        "",
        "This report evaluates automatic component-level evidence span suggestions against adjudicated human gold.",
        "It is paper-claimable only after completed adjudication rows contain component evidence spans.",
        "",
        "## Summary",
        "",
        "| Item | Value |",
        "|---|---:|",
        f"| Candidate rows | {summary['candidate_rows']} |",
        f"| Candidate edges | {summary['candidate_edge_count']} |",
        f"| Candidate component spans | {summary['candidate_component_span_count']} |",
        f"| Completed adjudicated chunks | {summary['completed_adjudicated_chunks']} |",
        f"| Gold edges | {summary['gold_edge_count']} |",
        f"| Gold component spans | {summary['gold_component_span_count']} |",
        f"| Matched edges | {summary['matched_edge_count']} |",
        f"| Matched component spans | {summary['matched_component_span_count']} |",
        f"| Span exact match rate | {summary['span_exact_match_rate']} |",
        f"| Mean span IoU | {summary['mean_span_iou']} |",
        "",
        "## Component Metrics",
        "",
        "| component | count | exact rate | mean IoU |",
        "|---|---:|---:|---:|",
    ]
    for component in COMPONENTS:
        lines.append(
            f"| {component} | {summary['component_counts'].get(component, 0)} | "
            f"{summary['component_exact_match_rate'].get(component)} | {summary['component_mean_iou'].get(component)} |"
        )
    lines += [
        "",
        "## Status Counts",
        "",
    ]
    for key, value in summary["status_counts"].items():
        lines.append(f"- {key}: {value}")
    if not payload["component_rows"]:
        lines += [
            "",
            "## Interpretation",
            "",
            "- No component span metric rows were produced yet.",
            "- This is expected before human adjudication or before gold component spans are returned.",
            "",
        ]
    lines += [
        "",
        "## Output Files",
        "",
        f"- Metrics JSON: `{payload['outputs']['json']}`",
        f"- Component rows CSV: `{payload['outputs']['csv']}`",
        f"- Report MD: `{payload['outputs']['md']}`",
        "",
    ]
    return "\n".join(lines)


def run(args):
    exp_dir = Path(args.experiment_dir)
    output_dir = exp_dir / "04_evaluation"
    adjudication_file = Path(args.adjudication_file) if args.adjudication_file else exp_dir / "01_data/gold_annotation/full_120/adjudication.jsonl"
    candidate_file = Path(args.candidate_file) if args.candidate_file else exp_dir / "01_data/gold_annotation_template.jsonl"
    summary, component_rows = evaluate(adjudication_file, candidate_file)
    outputs = {
        "json": rel(output_dir / "human_gold_span_iou_metrics.json"),
        "csv": rel(output_dir / "human_gold_span_iou_components.csv"),
        "md": rel(output_dir / "human_gold_span_iou_report.md"),
    }
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": rel(exp_dir),
        "summary": summary,
        "component_rows": component_rows[:1000],
        "component_row_count": len(component_rows),
        "outputs": outputs,
    }
    write_json(outputs["json"], payload)
    write_csv(outputs["csv"], component_rows, COMPONENT_FIELDNAMES)
    write_text(outputs["md"], render_report(payload))
    print(json.dumps({"summary": summary, "outputs": outputs}, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--adjudication-file", default="")
    parser.add_argument("--candidate-file", default="")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
