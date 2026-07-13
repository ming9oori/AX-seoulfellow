#!/usr/bin/env python3
"""Deterministic anchor, cue, and validation utilities for APRE-LDR R3."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


EXPERIMENT_ID = "zaije_ldr_r3_20260712_apre_v1"


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha(value: Any) -> str:
    payload = value if isinstance(value, bytes) else canonical(value).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.open(encoding="utf-8") if line.strip()]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(canonical(row) + "\n")


def _trim(text: str, start: int, end: int) -> tuple[int, int]:
    while start < end and text[start].isspace():
        start += 1
    while start < end and text[end - 1].isspace():
        end -= 1
    return start, end


def _lines(text: str) -> list[tuple[int, int]]:
    result: list[tuple[int, int]] = []
    cursor = 0
    for line in text.splitlines(keepends=True):
        end = cursor + len(line.rstrip("\r\n"))
        start, end = _trim(text, cursor, end)
        if start < end:
            result.append((start, end))
        cursor += len(line)
    if cursor < len(text):
        start, end = _trim(text, cursor, len(text))
        if start < end:
            result.append((start, end))
    return result


def _sentences(text: str, start: int = 0, end: int | None = None) -> list[tuple[int, int]]:
    end = len(text) if end is None else end
    fragment = text[start:end]
    boundaries = [start]
    # Do not split labels such as "A. 진실" or numbered abbreviations.
    for match in re.finditer(r"(?:(?<![A-Za-z0-9])[.!?。！？]+[\"'”’)]*(?:\s+|$)|\n+)", fragment):
        boundaries.append(start + match.end())
    boundaries.append(end)
    result = []
    for left, right in zip(boundaries, boundaries[1:]):
        left, right = _trim(text, left, right)
        if left < right:
            result.append((left, right))
    return result


def _clause_split(text: str, start: int, end: int) -> list[tuple[int, int]]:
    """Split only at strong separators to avoid destroying Korean predicate units."""
    fragment = text[start:end]
    boundaries = [start]
    pattern = (
        r"(?:[;；]\s*|\s+(?:그러나|하지만|따라서|또한|그리고)\s+|"
        r"(?:하고|하며|이고|이며|였고|했으며|있는가\s*하면),\s+|"
        r",\s*(?=(?:그러나|하지만|반면|통합적|현장의)))"
    )
    for match in re.finditer(pattern, fragment):
        boundaries.append(start + match.end())
    boundaries.append(end)
    parts = []
    for left, right in zip(boundaries, boundaries[1:]):
        left, right = _trim(text, left, right)
        if right - left >= 3:
            parts.append((left, right))
    return parts or [(start, end)]


def _table_cells(text: str, start: int, end: int) -> list[tuple[int, int]]:
    line = text[start:end]
    cells = []
    for match in re.finditer(r"(?<=\|)([^|]*)(?=\|)", line):
        left, right = _trim(text, start + match.start(1), start + match.end(1))
        if left < right:
            cells.append((left, right))
    return cells


def _is_separator_cell(value: str) -> bool:
    return bool(re.fullmatch(r":?-{3,}:?", value.strip()))


def _is_nonsemantic_cell(value: str) -> bool:
    value = value.strip()
    return not value or value in {"-", "#"} or bool(re.fullmatch(r"[\d.,%~∼\-]+", value))


def _cell_atomic_spans(text: str, start: int, end: int) -> list[tuple[int, int]]:
    """Split table-cell line breaks and bullets while preserving exact offsets."""
    fragment = text[start:end]
    boundaries = [0, len(fragment)]
    for match in re.finditer(r"<br\s*/?>", fragment, re.I):
        boundaries.extend([match.start(), match.end()])
    for match in re.finditer(r"(?<!^)(?=[•▪◦]\s*)", fragment):
        boundaries.append(match.start())
    boundaries = sorted(set(boundaries))
    spans = []
    for left, right in zip(boundaries, boundaries[1:]):
        if re.fullmatch(r"<br\s*/?>", fragment[left:right], re.I):
            continue
        a, b = _trim(text, start + left, start + right)
        if a < b:
            spans.extend(_clause_split(text, a, b))
    return spans or [(start, end)]


def _list_atomic_spans(text: str, start: int, end: int) -> list[tuple[int, int]]:
    fragment = text[start:end]
    boundaries = [0]
    # Require visible list spacing so arithmetic such as V-C is never split.
    pattern = r"(?<!^)(?=\s+[\-*•▪◦]\s+(?:\d|[가-힣A-Za-z]))|(?<=[가-힣)])(?=-\s*\d{1,2}\s*[~∼-])"
    for match in re.finditer(pattern, fragment):
        boundaries.append(match.start())
    boundaries.append(len(fragment))
    result = []
    for left, right in zip(boundaries, boundaries[1:]):
        a, b = _trim(text, start + left, start + right)
        if a < b:
            result.append((a, b))
    return result or [(start, end)]


def build_atomic_anchors(row: dict[str, Any]) -> dict[str, Any]:
    text = row["raw_text"]
    evidence_id = row["evidence_id"]
    structure = row.get("structure_type", "PROSE")
    anchors: list[dict[str, Any]] = []
    contexts: list[dict[str, Any]] = []
    context_keys: dict[tuple[int, int, str], str] = {}

    def context(start: int, end: int, kind: str) -> str:
        start, end = _trim(text, start, end)
        key = (start, end, kind)
        if key in context_keys:
            return context_keys[key]
        span_id = f"{evidence_id}_X{len(contexts) + 1:02d}"
        contexts.append({
            "span_id": span_id,
            "evidence_id": evidence_id,
            "start_char": start,
            "end_char": end,
            "text_by_program": text[start:end],
            "context_type": kind,
        })
        context_keys[key] = span_id
        return span_id

    def anchor(start: int, end: int, kind: str, rule: str, links: list[tuple[str, str]] | None = None) -> None:
        start, end = _trim(text, start, end)
        if start >= end:
            return
        if any(item["start_char"] == start and item["end_char"] == end for item in anchors):
            return
        links = links or []
        anchor_id = f"{evidence_id}_A{len(anchors) + 1:02d}"
        anchors.append({
            "anchor_id": anchor_id,
            "evidence_id": evidence_id,
            "start_char": start,
            "end_char": end,
            "text_by_program": text[start:end],
            "structure_type": kind,
            "context_span_ids": [item[0] for item in links],
            "context_relations": [item[1] for item in links],
            "generation_rule": rule,
            "source_hash": row.get("text_sha256") or sha(text),
        })

    lines = _lines(text)
    table_lines = [(a, b) for a, b in lines if text[a:b].lstrip().startswith("|")]
    list_line_re = re.compile(r"^\s*(?:[-*•▪◦‣]|\d+[.)])\s*")

    if len(table_lines) >= 2:
        pre_table = [(a, b) for a, b in lines if b <= table_lines[0][0]]
        caption_ids = [context(a, b, "TABLE_CAPTION") for a, b in pre_table]
        parsed = [_table_cells(text, a, b) for a, b in table_lines]
        header_index = 0
        for index, cells in enumerate(parsed):
            if cells and not all(_is_separator_cell(text[a:b]) for a, b in cells):
                header_index = index
                break
        header_cells = parsed[header_index] if parsed else []
        header_ids = [context(a, b, "TABLE_HEADER_CELL") for a, b in header_cells]
        for row_index, cells in enumerate(parsed[header_index + 1 :], header_index + 2):
            if not cells or all(_is_separator_cell(text[a:b]) for a, b in cells):
                continue
            meaningful = [(idx, a, b) for idx, (a, b) in enumerate(cells) if text[a:b].strip() and not _is_separator_cell(text[a:b])]
            semantic = [(idx, a, b) for idx, a, b in meaningful if not _is_nonsemantic_cell(text[a:b])]
            if not meaningful or not semantic:
                continue
            row_header_idx, row_a, row_b = semantic[0]
            row_header_id = context(row_a, row_b, "TABLE_ROW_HEADER")
            for col_idx, a, b in meaningful:
                value = text[a:b].strip()
                if value == "-" or (col_idx == 0 and re.fullmatch(r"\d+", value)):
                    continue
                is_short_row_label = col_idx == row_header_idx and len(value) < 15 and not re.search(r"(?:한다|된다|이다|있|없|필요|강점|약점|우수|높|낮)", value)
                if is_short_row_label or re.fullmatch(r"총\s*(?:합계|계)", value):
                    continue
                links: list[tuple[str, str]] = []
                links.extend((item, "INHERITS_TABLE_CAPTION") for item in caption_ids)
                if col_idx != row_header_idx:
                    links.append((row_header_id, "HAS_ROW_HEADER"))
                if col_idx < len(header_ids):
                    links.append((header_ids[col_idx], "HAS_COLUMN_HEADER"))
                for atom_a, atom_b in _cell_atomic_spans(text, a, b):
                    anchor(atom_a, atom_b, "TABLE_CELL", "MARKDOWN_TABLE_CELL_ATOM_V2", links)
    elif any(list_line_re.match(text[a:b]) for a, b in lines):
        first_item = next((index for index, (a, b) in enumerate(lines) if list_line_re.match(text[a:b])), 0)
        header_ids = [context(a, b, "LIST_HEADER") for a, b in lines[:first_item]]
        previous_line: tuple[int, int] | None = None
        for a, b in lines[first_item:]:
            if re.fullmatch(r"\s*\d+[.)]?\s*", text[a:b]):
                header_ids.append(context(a, b, "LIST_NUMBER_HEADER"))
                previous_line = (a, b)
                continue
            links = [(item, "INHERITS_LIST_HEADER") for item in header_ids]
            if not list_line_re.match(text[a:b]) and previous_line:
                previous_context = context(previous_line[0], previous_line[1], "PREVIOUS_LIST_ITEM")
                links.append((previous_context, "EXPLAINS_PREVIOUS_ITEM"))
            for atom_a, atom_b in _list_atomic_spans(text, a, b):
                anchor(atom_a, atom_b, "LIST_ITEM", "LIST_ATOM_V2", links)
            previous_line = (a, b)
    else:
        for sentence_start, sentence_end in _sentences(text):
            parts = _clause_split(text, sentence_start, sentence_end)
            prior_context: str | None = None
            for part_index, (a, b) in enumerate(parts):
                links = []
                if part_index and prior_context:
                    links.append((prior_context, "INHERITS_SUBJECT_FROM"))
                anchor(a, b, "PROSE_CLAUSE", "KO_CLAUSE_V3", links)
                if part_index == 0:
                    prior_context = context(a, b, "PRECEDING_CLAUSE")

    if not anchors and text.strip():
        start, end = _trim(text, 0, len(text))
        anchor(start, end, "FALLBACK_SPAN", "NONEMPTY_FALLBACK_V1")

    return {
        "evidence_id": evidence_id,
        "raw_text": text,
        "structure_type": structure,
        "chapter": row.get("chapter_title") or row.get("inferred_chapter_title") or "",
        "section": row.get("section_title") or row.get("inferred_section_title") or "",
        "leakage_group_id": row.get("leakage_group_id"),
        "anchors": anchors,
        "context_spans": contexts,
    }


CUE_PATTERNS = {
    "REQUIREMENT": [r"반드시", r"해야\s*한다", r"하여야", r"필수", r"의무"],
    "RECOMMENDATION": [r"권장", r"바람직", r"필요가\s*있", r"하는\s*것이\s*좋"],
    "PROHIBITION": [r"금지", r"해서는\s*안", r"하지\s*말아야"],
    "PERMISSION": [r"할\s*수\s*있", r"허용"],
    "NEGATION": [r"않", r"못", r"없", r"아니"],
    "CONDITION": [r"경우", r"만약", r"(?:이|라)면", r"때", r"조건하에", r"이전", r"이후"],
    "EXCEPTION": [r"단,?", r"다만", r"예외"],
    "EXAMPLE": [r"예를\s*들", r"예시", r"사례"],
    "TEMPLATE": [r"템플릿", r"양식", r"서식"],
    "DEFINITION": [r"이란", r"정의", r"의미한다"],
    "REPORTED": [r"따르면", r"조사\s*결과", r"말했다", r"주장"],
}


def build_cues(anchor_record: dict[str, Any]) -> list[dict[str, Any]]:
    text = anchor_record["raw_text"]
    cues = []
    seen: set[tuple[int, int, str]] = set()
    for family, patterns in CUE_PATTERNS.items():
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.I):
                key = (match.start(), match.end(), family)
                if key in seen:
                    continue
                seen.add(key)
                cues.append({
                    "evidence_id": anchor_record["evidence_id"],
                    "cue_family": family,
                    "start_char": match.start(),
                    "end_char": match.end(),
                    "text_by_program": text[match.start():match.end()],
                    "generation_rule": f"CUE_{family}_V1",
                })
    cues.sort(key=lambda item: (item["start_char"], item["end_char"], item["cue_family"]))
    for index, item in enumerate(cues, 1):
        item["cue_id"] = f"{anchor_record['evidence_id']}_Q{index:02d}"
    return cues


def validate_anchor_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    anchor_count = context_count = 0
    roundtrip = ids_valid = context_valid = 0
    evidence_valid = 0
    structure_counts: Counter[str] = Counter()
    for record in records:
        ids = {item["anchor_id"] for item in record["anchors"]}
        context_ids = {item["span_id"] for item in record["context_spans"]}
        anchor_count += len(record["anchors"])
        context_count += len(record["context_spans"])
        ids_valid += int(len(ids) == len(record["anchors"]))
        item_ok = True
        for item in record["anchors"]:
            structure_counts[item["structure_type"]] += 1
            exact = record["raw_text"][item["start_char"]:item["end_char"]] == item["text_by_program"]
            roundtrip += int(exact)
            links_ok = all(span_id in context_ids for span_id in item["context_span_ids"])
            context_valid += int(links_ok)
            item_ok = item_ok and exact and links_ok
        for item in record["context_spans"]:
            exact = record["raw_text"][item["start_char"]:item["end_char"]] == item["text_by_program"]
            roundtrip += int(exact)
            item_ok = item_ok and exact
        evidence_valid += int(item_ok and bool(record["anchors"]))
    total_spans = anchor_count + context_count
    return {
        "evidence_count": len(records),
        "anchor_count": anchor_count,
        "context_span_count": context_count,
        "anchor_json_validity": evidence_valid / len(records) if records else 1.0,
        "offset_round_trip_validity": roundtrip / total_spans if total_spans else 1.0,
        "anchor_id_uniqueness": ids_valid / len(records) if records else 1.0,
        "context_span_existence": context_valid / anchor_count if anchor_count else 1.0,
        "structure_counts": dict(structure_counts),
        "records_sha256": sha(records),
    }
