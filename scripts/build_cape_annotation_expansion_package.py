#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build optional expanded annotation packages for all available Layer2 chunks."""

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_OUTPUTS_DIR = Path("outputs")
ANNOTATORS = ("A", "B")


def read_jsonl(path):
    path = Path(path)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


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


def refs_by_chunk(exp_dir):
    grouped = defaultdict(list)
    for ref in read_jsonl(exp_dir / "01_data/silver_reference_edges.jsonl"):
        chunk_ids = sorted({span.get("chunk_id") for span in ref.get("evidence_spans", []) if span.get("chunk_id")})
        for chunk_id in chunk_ids:
            grouped[chunk_id].append(ref)
    return grouped


def evidence_anchor_to_sentence_id(anchor_id):
    if not anchor_id:
        return None
    if anchor_id.startswith("EA-"):
        return anchor_id[3:]
    return anchor_id


def span_sentence_id(span):
    return span.get("sentence_id") or evidence_anchor_to_sentence_id(span.get("evidence_anchor_id"))


def edge_sentence_ids(edge):
    ids = set()
    for span in edge.get("evidence_spans") or []:
        sentence_id = span_sentence_id(span)
        if sentence_id:
            ids.add(sentence_id)
    for anchor_id in edge.get("evidence_anchor_ids") or []:
        sentence_id = evidence_anchor_to_sentence_id(anchor_id)
        if sentence_id:
            ids.add(sentence_id)
    return ids


def candidate_summary(edge, allowed_sentence_ids=None):
    allowed = set(allowed_sentence_ids or [])
    spans = edge.get("evidence_spans") or []
    if allowed:
        local_spans = [span for span in spans if span_sentence_id(span) in allowed]
    else:
        local_spans = spans
    first_span = (local_spans or spans or [{}])[0]
    if allowed:
        local_anchor_ids = sorted(
            {
                span.get("evidence_anchor_id")
                for span in local_spans
                if span.get("evidence_anchor_id")
            }
            | {
                anchor_id
                for anchor_id in edge.get("evidence_anchor_ids", [])
                if evidence_anchor_to_sentence_id(anchor_id) in allowed
            }
        )
    else:
        local_anchor_ids = edge.get("evidence_anchor_ids", [])
    primary_evidence = {
        "sentence_id": first_span.get("sentence_id"),
        "page": first_span.get("page"),
        "start_char": first_span.get("start_char"),
        "end_char": first_span.get("end_char"),
        "text": first_span.get("text"),
    }
    return {
        "reference_id": edge.get("reference_id"),
        "source_id": edge.get("source_id"),
        "source_label": edge.get("source_label"),
        "source_type": edge.get("source_type"),
        "predicate": edge.get("predicate"),
        "target_id": edge.get("target_id"),
        "target_label": edge.get("target_label"),
        "target_type": edge.get("target_type"),
        "evidence_anchor_ids": local_anchor_ids or edge.get("evidence_anchor_ids", []),
        "primary_evidence": primary_evidence,
        "component_evidence_spans": component_evidence_spans(edge, primary_evidence),
    }


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
    return None


def component_span_row(edge, component, label, primary_evidence, span, method, exact):
    if span:
        start, end, span_text, method = span
    elif method == "full_sentence_proxy":
        span_text = primary_evidence.get("text") or ""
        start = 0
        end = len(span_text)
    else:
        start = ""
        end = ""
        span_text = ""
    return {
        "component": component,
        "label": label,
        "predicate": edge.get("predicate"),
        "sentence_id": primary_evidence.get("sentence_id"),
        "page": primary_evidence.get("page"),
        "sentence_span_start": start,
        "sentence_span_end": end,
        "text": span_text,
        "span_method": method,
        "span_exact": bool(exact),
        "claim_status": "automatic_candidate_span_suggestion_not_gold",
    }


def component_evidence_spans(edge, primary_evidence):
    text = primary_evidence.get("text") or ""
    source_label = edge.get("source_label") or ""
    target_label = edge.get("target_label") or ""
    source_span = find_label_span(text, source_label)
    target_span = find_label_span(text, target_label)
    return [
        component_span_row(edge, "subject", source_label, primary_evidence, source_span, "label_not_found_in_sentence", bool(source_span)),
        component_span_row(edge, "predicate", edge.get("predicate") or "", primary_evidence, None, "full_sentence_proxy", False),
        component_span_row(edge, "object", target_label, primary_evidence, target_span, "label_not_found_in_sentence", bool(target_span)),
    ]


def base_row(chunk, candidates, allowed_sentence_ids=None):
    return {
        "chunk_id": chunk["chunk_id"],
        "source_chunk_id": chunk.get("source_chunk_id", chunk["chunk_id"]),
        "page_start": chunk.get("page_start"),
        "page_end": chunk.get("page_end"),
        "chapter_id": chunk.get("chapter_id"),
        "section_id": chunk.get("section_id"),
        "subsection_id": chunk.get("subsection_id"),
        "sentence_ids": chunk.get("sentence_ids", []),
        "chunk_text": chunk.get("text"),
        "annotation_status": "pending_human_annotation",
        "silver_candidate_edge_count": len(candidates),
        "silver_candidate_edges": [candidate_summary(edge, allowed_sentence_ids) for edge in candidates[:50]],
        "gold_nodes": [],
        "gold_edges": [],
        "annotator_id": "",
        "adjudication_notes": "",
        "expansion_note": "optional_strong_paper_scale_scaffold_not_required_for_current_claim_gate",
    }


def annotator_row(row, annotator):
    out = dict(row)
    out["annotator_id"] = annotator
    out["instructions"] = {
        "use_schema_only": True,
        "copy_candidate_edges_when_correct": True,
        "add_missing_edges_when_directly_supported": True,
        "remove_or_mark_rejected_when_unsupported": True,
        "evidence_required": True,
        "text_only_chunks_may_have_zero_silver_candidates": True,
    }
    out["rejected_candidate_reference_ids"] = []
    out["missing_but_supported_notes"] = []
    out["time_minutes"] = ""
    out["comments"] = ""
    return out


def adjudication_row(row):
    return {
        "chunk_id": row["chunk_id"],
        "chapter_id": row.get("chapter_id"),
        "section_id": row.get("section_id"),
        "page_start": row.get("page_start"),
        "page_end": row.get("page_end"),
        "chunk_text": row.get("chunk_text"),
        "annotator_a_status": "pending_human_annotation",
        "annotator_b_status": "pending_human_annotation",
        "disagreement_items": [],
        "adjudicated_gold_nodes": [],
        "adjudicated_gold_edges": [],
        "adjudicator_id": "",
        "adjudication_status": "pending_two_annotator_input",
        "adjudication_notes": "",
        "expansion_note": row.get("expansion_note"),
    }


def tracking_rows(package_name, rows):
    output = []
    for row in rows:
        output.append(
            {
                "package": package_name,
                "chunk_id": row["chunk_id"],
                "source_chunk_id": row.get("source_chunk_id", row["chunk_id"]),
                "split_index": row.get("split_index", ""),
                "split_sentence_count": len(row.get("split_sentence_ids") or row.get("sentence_ids") or []),
                "split_max_sentences": row.get("split_max_sentences", ""),
                "chapter_id": row.get("chapter_id"),
                "section_id": row.get("section_id"),
                "page_start": row.get("page_start"),
                "page_end": row.get("page_end"),
                "silver_candidate_edge_count": row.get("silver_candidate_edge_count", 0),
                "annotator_A_status": "pending_human_annotation",
                "annotator_B_status": "pending_human_annotation",
                "adjudication_status": "pending_two_annotator_input",
                "priority": "optional_expansion",
                "comment": "optional strong-paper annotation expansion",
            }
        )
    return output


def write_package(root, package_name, rows):
    package_dir = root / package_name
    package_dir.mkdir(parents=True, exist_ok=True)
    for annotator in ANNOTATORS:
        write_jsonl(package_dir / f"annotator_{annotator}.jsonl", [annotator_row(row, annotator) for row in rows])
    write_jsonl(package_dir / "adjudication.jsonl", [adjudication_row(row) for row in rows])
    tracking = tracking_rows(package_name, rows)
    write_csv(
        package_dir / "tracking_sheet.csv",
        tracking,
        [
            "package",
            "chunk_id",
            "source_chunk_id",
            "split_index",
            "split_sentence_count",
            "split_max_sentences",
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
    candidate_counts = [int(row.get("silver_candidate_edge_count") or 0) for row in rows]
    return {
        "package_dir": str(package_dir),
        "chunk_count": len(rows),
        "annotator_files": {annotator: str(package_dir / f"annotator_{annotator}.jsonl") for annotator in ANNOTATORS},
        "adjudication_file": str(package_dir / "adjudication.jsonl"),
        "tracking_sheet": str(package_dir / "tracking_sheet.csv"),
        "candidate_edges_total": sum(candidate_counts),
        "candidate_edges_min": min(candidate_counts) if candidate_counts else 0,
        "candidate_edges_max": max(candidate_counts) if candidate_counts else 0,
        "chunks_with_silver_candidates": sum(1 for value in candidate_counts if value > 0),
        "chapter_distribution": dict(Counter(row.get("chapter_id") or "unknown" for row in rows)),
    }


def sentence_lookup(outputs_dir):
    lookup = {}
    for row in read_jsonl(Path(outputs_dir) / "02_ocr/ocr_sentences_clean.jsonl"):
        sentence_id = row.get("sentence_id")
        if sentence_id:
            lookup[sentence_id] = row
    return lookup


def split_text(sentence_rows, fallback_text):
    parts = [row.get("text_clean") or row.get("text_raw") for row in sentence_rows]
    text = " ".join(part.strip() for part in parts if part and part.strip())
    return text or fallback_text or ""


def split_pages(sentence_rows, fallback_start, fallback_end):
    pages = [row.get("page") for row in sentence_rows if isinstance(row.get("page"), int)]
    if not pages:
        return fallback_start, fallback_end
    return min(pages), max(pages)


def split_source_rows(sentence_rows):
    rows = [row.get("source_row") for row in sentence_rows if row.get("source_row") is not None]
    if not rows:
        return ""
    return f"{min(rows)}-{max(rows)}" if min(rows) != max(rows) else str(rows[0])


def build_resegmented_rows(chunks, refs, sentences, max_sentences):
    rows = []
    if max_sentences < 1:
        raise ValueError("--strong-max-sentences must be >= 1")
    for chunk in chunks:
        sentence_ids = list(chunk.get("sentence_ids") or [])
        if not sentence_ids:
            rows.append(base_row(chunk, refs.get(chunk["chunk_id"], [])))
            continue
        split_count = (len(sentence_ids) + max_sentences - 1) // max_sentences
        source_edges = refs.get(chunk["chunk_id"], [])
        for start in range(0, len(sentence_ids), max_sentences):
            segment_ids = sentence_ids[start : start + max_sentences]
            split_index = (start // max_sentences) + 1
            sentence_rows = [sentences[sid] for sid in segment_ids if sid in sentences]
            page_start, page_end = split_pages(sentence_rows, chunk.get("page_start"), chunk.get("page_end"))
            text = split_text(sentence_rows, chunk.get("text"))
            local_edges = [
                edge
                for edge in source_edges
                if not edge_sentence_ids(edge) or edge_sentence_ids(edge).intersection(segment_ids)
            ]
            split_chunk = {
                **chunk,
                "chunk_id": f"{chunk['chunk_id']}-SPLIT-{split_index:03d}",
                "source_chunk_id": chunk["chunk_id"],
                "clean_id_start": segment_ids[0],
                "clean_id_end": segment_ids[-1],
                "page_start": page_start,
                "page_end": page_end,
                "sentence_ids": segment_ids,
                "sentence_offsets": [],
                "source_rows": split_source_rows(sentence_rows) or chunk.get("source_rows"),
                "text": text,
                "char_count": len(text),
                "token_est": max(1, round(len(text.split()) * 1.35)) if text else 0,
            }
            row = base_row(split_chunk, local_edges, allowed_sentence_ids=segment_ids)
            row.update(
                {
                    "source_chunk_id": chunk["chunk_id"],
                    "split_index": split_index,
                    "split_count_for_source_chunk": split_count,
                    "split_sentence_ids": segment_ids,
                    "split_max_sentences": max_sentences,
                    "source_chunk_sentence_count": len(sentence_ids),
                    "expansion_note": "optional_strong_paper_resegmented_scaffold_not_required_for_current_claim_gate",
                }
            )
            rows.append(row)
    return rows


def render_report(summary):
    strong_package_name = summary.get("strong_resegmented_package")
    strong_package = (summary.get("packages") or {}).get(strong_package_name, {})
    lines = [
        "# CAPE-KG Optional Annotation Expansion Package",
        "",
        f"Generated: {summary['generated_at_utc']}",
        "",
        "This package is an optional strong-paper scale scaffold. It does not change the 11-file minimum paper gate and is tracked separately for optional/strong claims.",
        "The original current source has 214 Layer2 chunks. A sentence-preserving resegmentation scaffold is provided for a 300+ chunk human-review target.",
        "",
        "## Summary",
        "",
        f"- All available Layer2 chunks: {summary['all_available_chunk_count']}",
        f"- Current required full package chunks: {summary['current_full_package_chunk_count']}",
        f"- Remaining optional chunks: {summary['remaining_optional_chunk_count']}",
        f"- Maximum current-corpus adjudicated chunks if fully reviewed: {summary['max_current_corpus_chunk_count']}",
        f"- Strong 300 chunk target gap without resegmentation: {summary['strong_300_chunk_gap']}",
        f"- Strong resegmented package: `{strong_package_name}`",
        f"- Strong resegmented max sentences per unit: {summary['strong_resegmented_max_sentences']}",
        f"- Strong resegmented review units: {summary['strong_resegmented_chunk_count']}",
        f"- Strong 300 chunk target gap after resegmentation: {summary['strong_300_chunk_gap_after_resegmentation']}",
        f"- Claim status: `{summary['claim_status']}`",
        "",
        "## Packages",
        "",
        "| package | chunks | chunks with silver candidates | candidate edges | path |",
        "|---|---:|---:|---:|---|",
    ]
    for name, pkg in summary["packages"].items():
        lines.append(
            f"| {name} | {pkg['chunk_count']} | {pkg['chunks_with_silver_candidates']} | "
            f"{pkg['candidate_edges_total']} | `{pkg['package_dir']}` |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "- `all_available_214` is useful if the project wants to review every current chunk.",
        "- `remaining_94_text_only` contains chunks not included in the current 120-chunk evaluation package.",
        f"- `{strong_package_name}` splits the same source chunks into at most {summary['strong_resegmented_max_sentences']} source sentences per review unit, yielding {summary['strong_resegmented_chunk_count']} pending human-review units.",
        f"- The resegmented package keeps `source_chunk_id` and `split_sentence_ids`, so every review unit remains traceable to the original Layer2 chunk and source sentences.",
        "- Many remaining chunks have zero silver candidates; annotators can still add directly supported nodes/edges from text.",
        "- This is optional expansion evidence, not completed human gold. It must not be reported as adjudicated 300+ chunks until two-annotator review and adjudication are returned.",
        "",
        "## Strong resegmented package detail",
        "",
        f"- Package path: `{strong_package.get('package_dir')}`",
        f"- Review units: {strong_package.get('chunk_count')}",
        f"- Units with silver candidates: {strong_package.get('chunks_with_silver_candidates')}",
        f"- Candidate edges total: {strong_package.get('candidate_edges_total')}",
        f"- Claim status: `{summary['strong_resegmented_claim_status']}`",
        "",
    ]
    return "\n".join(lines)


def run(args):
    exp_dir = Path(args.experiment_dir)
    outputs_dir = Path(args.outputs_dir)
    root = exp_dir / "01_data/gold_annotation"
    chunks = read_jsonl(outputs_dir / "02_ocr/layer2_chunks.jsonl")
    current_full = read_jsonl(root / "full_120/annotator_A.jsonl")
    current_ids = {row.get("chunk_id") for row in current_full if row.get("chunk_id")}
    refs = refs_by_chunk(exp_dir)
    sentences = sentence_lookup(outputs_dir)
    all_rows = [base_row(chunk, refs.get(chunk["chunk_id"], [])) for chunk in chunks]
    remaining_rows = [row for row in all_rows if row["chunk_id"] not in current_ids]
    strong_resegmented_rows = build_resegmented_rows(chunks, refs, sentences, args.strong_max_sentences)
    strong_package_name = f"strong_resegmented_{len(strong_resegmented_rows)}_max{args.strong_max_sentences}"

    packages = {
        "all_available_214": write_package(root, "all_available_214", all_rows),
        "remaining_94_text_only": write_package(root, "remaining_94_text_only", remaining_rows),
        strong_package_name: write_package(root, strong_package_name, strong_resegmented_rows),
    }
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "outputs_dir": str(outputs_dir),
        "source_layer2_chunks": str(outputs_dir / "02_ocr/layer2_chunks.jsonl"),
        "current_full_package": str(root / "full_120"),
        "all_available_chunk_count": len(all_rows),
        "current_full_package_chunk_count": len(current_ids),
        "remaining_optional_chunk_count": len(remaining_rows),
        "max_current_corpus_chunk_count": len(all_rows),
        "strong_300_chunk_gap": max(0, 300 - len(all_rows)),
        "strong_resegmented_package": strong_package_name,
        "strong_resegmented_max_sentences": args.strong_max_sentences,
        "strong_resegmented_chunk_count": len(strong_resegmented_rows),
        "strong_300_chunk_gap_after_resegmentation": max(0, 300 - len(strong_resegmented_rows)),
        "strong_resegmented_claim_status": (
            "ready_pending_human_review"
            if len(strong_resegmented_rows) >= 300
            else "below_300_pending_source_expansion_or_smaller_split"
        ),
        "packages": packages,
        "claim_status": "optional_expansion_ready_pending_human_review",
        "human_gate_effect": "does_not_change_minimum_11_file_paper_gate",
    }
    summary_path = root / "annotation_expansion_manifest.json"
    report_path = root / "annotation_expansion_report.md"
    write_json(summary_path, summary)
    write_text(report_path, render_report(summary))
    print(json.dumps({**summary, "report": str(report_path), "manifest": str(summary_path)}, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--outputs-dir", default=str(DEFAULT_OUTPUTS_DIR))
    parser.add_argument("--strong-max-sentences", type=int, default=18)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
