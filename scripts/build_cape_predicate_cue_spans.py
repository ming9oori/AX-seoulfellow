#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build automatic predicate cue span diagnostics for CAPE-KG triples.

The canonical component span diagnostic keeps predicate evidence as a
sentence-level proxy. This script adds a separate lexical cue diagnostic for
predicate support when predicate-like surface cues are found in the evidence
sentence. It does not change the canonical KG and does not claim human-gold
predicate-span correctness.
"""

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_OUTPUTS_DIR = Path("outputs")
CLAIM_STATUS = "automatic_predicate_cue_span_diagnostic_not_human_gold"

CSV_FIELDS = [
    "triple_id",
    "predicate",
    "subject_id",
    "object_id",
    "sentence_id",
    "evidence_anchor_id",
    "chunk_id",
    "page",
    "cue_method",
    "cue_pattern",
    "cue_span_start",
    "cue_span_end",
    "chunk_span_start",
    "chunk_span_end",
    "cue_text_included",
    "cue_text_char_count",
    "cue_text_sha256",
    "review_status",
]

PREDICATE_CUE_PATTERNS = {
    "USES_INPUT": [
        "활용",
        "사용",
        "기반",
        "바탕",
        "참조",
        "입력",
        "정보수집",
        "정보 수집",
        "수집",
        "분석",
    ],
    "PRODUCES": [
        "작성",
        "제출",
        "도출",
        "생성",
        "개발",
        "수립",
        "산출",
        "정의",
        "결정",
    ],
    "PERFORMED_BY": [
        "수행",
        "담당",
        "책임",
        "참여",
        "검토",
        "관리",
        "주관",
    ],
    "HAS_STEP": [
        "단계",
        "절차",
        "프로세스",
        "과정",
        "활동",
        "먼저",
        "다음",
        "이후",
    ],
    "PRECEDES": [
        "먼저",
        "다음",
        "이후",
        "후",
        "끝나고",
        "전에",
        "선행",
        "이어",
    ],
    "HAS_PRINCIPLE": [
        "원칙",
        "준수",
        "유의",
        "고려",
        "지켜",
        "해야 한다",
    ],
    "HAS_DECISION_GATEWAY": [
        "결정",
        "판단",
        "여부",
        "승인",
        "검토",
        "게이트",
    ],
    "HAS_REVIEW_CHECKPOINT": [
        "리뷰",
        "검토",
        "점검",
        "확인",
        "승인",
        "review",
    ],
    "HAS_RISK": [
        "위험",
        "리스크",
        "문제",
        "실패",
        "부족",
        "불확실",
        "risk",
    ],
    "HAS_GUARD_CONDITION": [
        "조건",
        "기준",
        "요건",
        "판단",
        "검토",
        "평가",
    ],
    "FEEDS_INTO": [
        "연계",
        "이어",
        "반영",
        "활용",
        "전달",
        "입력",
        "사용",
    ],
    "USED_AS_INPUT_FOR": [
        "활용",
        "사용",
        "입력",
        "반영",
        "연계",
        "바탕",
        "기반",
    ],
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


def write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in CSV_FIELDS})


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def rel(path):
    return str(Path(path).as_posix())


def text_sha256(value):
    if value in (None, ""):
        return ""
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def first_nonempty(values):
    for value in values or []:
        if value:
            return value
    return ""


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


def anchors_by_sentence(outputs_dir):
    mapping = {}
    for row in read_jsonl(outputs_dir / "06_triples/evidence_anchors.jsonl"):
        sentence_id = row.get("sentence_id")
        if sentence_id:
            mapping[sentence_id] = row
    return mapping


def find_predicate_cue(text, predicate):
    text = str(text or "")
    patterns = PREDICATE_CUE_PATTERNS.get(predicate) or []
    best = None
    for pattern in patterns:
        idx = text.find(pattern)
        if idx < 0 and pattern.isascii():
            idx = text.lower().find(pattern.lower())
        if idx < 0:
            continue
        candidate = (idx, idx + len(pattern), pattern)
        if best is None or candidate[0] < best[0] or (candidate[0] == best[0] and len(pattern) > len(best[2])):
            best = candidate
    return best


def row_for_triple(triple, anchors, sentence_offsets):
    evidence = triple.get("evidence") or {}
    text = evidence.get("evidence_text") or ""
    chunk_id = evidence.get("chunk_id") or ""
    sentence_id = first_nonempty(evidence.get("sentence_ids") or [])
    predicate = triple.get("predicate") or ""
    anchor = anchors.get(sentence_id) or {}
    cue = find_predicate_cue(text, predicate)
    cue_span_start = ""
    cue_span_end = ""
    chunk_span_start = ""
    chunk_span_end = ""
    cue_pattern = ""
    cue_text = ""
    cue_method = "predicate_cue_not_found"
    if cue:
        cue_span_start, cue_span_end, cue_pattern = cue
        cue_text = text[cue_span_start:cue_span_end]
        cue_method = "predicate_cue_lexical_match"
        offset = sentence_offsets.get((chunk_id, sentence_id))
        if offset and offset[0] is not None:
            chunk_span_start = int(offset[0]) + int(cue_span_start)
            chunk_span_end = int(offset[0]) + int(cue_span_end)
    subject = triple.get("subject") or {}
    obj = triple.get("object") or {}
    return {
        "triple_id": triple.get("triple_id"),
        "predicate": predicate,
        "subject_id": subject.get("canonical_id"),
        "object_id": obj.get("canonical_id"),
        "sentence_id": sentence_id,
        "evidence_anchor_id": anchor.get("evidence_anchor_id") or (f"EA-{sentence_id}" if sentence_id else ""),
        "chunk_id": chunk_id,
        "page": anchor.get("page", ""),
        "cue_method": cue_method,
        "cue_pattern": cue_pattern,
        "cue_span_start": cue_span_start,
        "cue_span_end": cue_span_end,
        "chunk_span_start": chunk_span_start,
        "chunk_span_end": chunk_span_end,
        "cue_text_included": False,
        "cue_text_char_count": len(cue_text),
        "cue_text_sha256": text_sha256(cue_text),
        "review_status": "automatic_predicate_cue_diagnostic_source_text_omitted",
    }


def build_payload(exp_dir, outputs_dir):
    exp_dir = Path(exp_dir)
    outputs_dir = Path(outputs_dir)
    triples = read_jsonl(outputs_dir / "06_triples/layer2_triples_schema_valid.jsonl")
    anchors = anchors_by_sentence(outputs_dir)
    sentence_offsets = chunk_sentence_offsets(outputs_dir)
    rows = [row_for_triple(triple, anchors, sentence_offsets) for triple in triples]

    predicate_counts = Counter(row["predicate"] for row in rows)
    predicate_match_counts = Counter(row["predicate"] for row in rows if row["cue_method"] == "predicate_cue_lexical_match")
    method_counts = Counter(row["cue_method"] for row in rows)
    chunk_span_count = sum(1 for row in rows if row["chunk_span_start"] != "")
    by_predicate = {}
    for predicate in sorted(predicate_counts):
        total = predicate_counts[predicate]
        matched = predicate_match_counts.get(predicate, 0)
        by_predicate[predicate] = {
            "triple_count": total,
            "predicate_cue_span_count": matched,
            "predicate_cue_span_rate": round(matched / total, 6) if total else 0.0,
            "cue_patterns": PREDICATE_CUE_PATTERNS.get(predicate, []),
        }

    matched_count = method_counts.get("predicate_cue_lexical_match", 0)
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": rel(exp_dir),
        "outputs_dir": rel(outputs_dir),
        "claim_status": CLAIM_STATUS,
        "source_text_included": False,
        "triple_count": len(triples),
        "predicate_cue_span_count": matched_count,
        "predicate_cue_missing_count": method_counts.get("predicate_cue_not_found", 0),
        "predicate_cue_span_rate": round(matched_count / len(rows), 6) if rows else 0.0,
        "chunk_span_count": chunk_span_count,
        "chunk_span_rate": round(chunk_span_count / len(rows), 6) if rows else 0.0,
        "method_counts": dict(sorted(method_counts.items())),
        "by_predicate": by_predicate,
        "limitations": [
            "Predicate cue spans are lexical heuristics, not human-gold predicate-token annotations.",
            "No source sentence text is included; cue text is represented only by hash and length.",
            "Cue absence does not mean the edge is unsupported; it means no configured surface cue was found.",
            "Final predicate-span correctness requires adjudicated human-gold span scoring.",
        ],
    }
    return rows, summary


def render_report(summary):
    lines = [
        "# CAPE-KG Predicate Cue Span Diagnostic",
        "",
        f"Generated: {summary['generated_at_utc']}",
        f"Claim status: `{summary['claim_status']}`",
        "",
        "This report adds an automatic lexical predicate-cue diagnostic on top of the existing sentence-level predicate evidence proxy.",
        "It is not a human-gold predicate-span evaluation. Source text is omitted from JSONL/CSV rows.",
        "",
        "## Summary",
        "",
        "| Item | Value |",
        "|---|---:|",
        f"| Triples | {summary['triple_count']} |",
        f"| Predicate cue spans found | {summary['predicate_cue_span_count']} |",
        f"| Predicate cue spans missing | {summary['predicate_cue_missing_count']} |",
        f"| Predicate cue span rate | {summary['predicate_cue_span_rate']} |",
        f"| Chunk-local cue spans | {summary['chunk_span_count']} |",
        f"| Chunk-local cue span rate | {summary['chunk_span_rate']} |",
        "",
        "## Method Counts",
        "",
        "| Method | Count |",
        "|---|---:|",
    ]
    for key, value in sorted(summary["method_counts"].items()):
        lines.append(f"| `{key}` | {value} |")
    lines += [
        "",
        "## Predicate Coverage",
        "",
        "| Predicate | Triples | Cue spans | Rate |",
        "|---|---:|---:|---:|",
    ]
    for predicate, row in sorted(summary["by_predicate"].items()):
        lines.append(
            f"| `{predicate}` | {row['triple_count']} | {row['predicate_cue_span_count']} | {row['predicate_cue_span_rate']} |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "- Existing component span diagnostics still treat predicate evidence as full-sentence proxy evidence.",
        "- This file adds a separate lexical cue diagnostic for predicates when configured surface cues are present.",
        "- Cue span presence is useful for review prioritization and later human-gold predicate span comparison.",
        "- Cue span absence must not be interpreted as unsupported evidence.",
        "",
    ]
    return "\n".join(lines)


def run(args):
    exp_dir = Path(args.experiment_dir)
    outputs_dir = Path(args.outputs_dir)
    rows, summary = build_payload(exp_dir, outputs_dir)
    jsonl_path = outputs_dir / "06_triples/layer2_predicate_cue_spans.jsonl"
    csv_path = exp_dir / "04_evaluation/predicate_cue_span_rows.csv"
    metrics_path = exp_dir / "04_evaluation/predicate_cue_span_metrics.json"
    report_path = exp_dir / "04_evaluation/predicate_cue_span_report.md"
    summary["output_files"] = {
        "predicate_cue_spans_jsonl": rel(jsonl_path),
        "predicate_cue_spans_csv": rel(csv_path),
        "metrics_json": rel(metrics_path),
        "report_md": rel(report_path),
    }
    write_jsonl(jsonl_path, rows)
    write_csv(csv_path, rows)
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
