#!/usr/bin/env python3
"""Deterministic data and candidate utilities for the BLRE experiment."""

from __future__ import annotations

import hashlib
import json
import re
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


SEED = 20260712
NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
R2_STRATA = [
    ("TABLE_TEMPLATE", 6),
    ("LIST_MULTILINE", 8),
    ("QUESTION_CAPTION_DISCOURSE", 4),
    ("NORMATIVE_DEONTIC", 8),
    ("CONDITIONAL_EXCEPTION", 8),
    ("DEFINITION_CAUSAL_EVALUATIVE", 8),
    ("NEGATION_QUANTITY_HIGH_RISK", 4),
    ("SIMPLE_GENERAL_PROSE", 14),
]


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


def column_index(reference: str) -> int:
    match = re.match(r"([A-Z]+)", reference)
    if not match:
        return 0
    value = 0
    for char in match.group(1):
        value = value * 26 + ord(char) - 64
    return value - 1


def read_xlsx_raw(path: Path) -> tuple[str, list[dict[str, Any]]]:
    with zipfile.ZipFile(path) as archive:
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        sheet_node = workbook.find(".//a:sheet", NS)
        sheet = sheet_node.attrib.get("name", "Sheet1") if sheet_node is not None else "Sheet1"
        strings: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in root.findall("a:si", NS):
                strings.append("".join(node.text or "" for node in item.findall(".//a:t", NS)))
        root = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        raw_rows: list[tuple[int, list[str]]] = []
        for row_node in root.findall(".//a:sheetData/a:row", NS):
            row_number = int(float(row_node.attrib.get("r", len(raw_rows) + 1)))
            cells: dict[int, str] = {}
            for cell in row_node.findall("a:c", NS):
                index = column_index(cell.attrib.get("r", "A"))
                value_node = cell.find("a:v", NS)
                if cell.attrib.get("t") == "s" and value_node is not None:
                    value = strings[int(value_node.text or "0")]
                elif cell.attrib.get("t") == "inlineStr":
                    value = "".join(node.text or "" for node in cell.findall(".//a:t", NS))
                else:
                    value = value_node.text or "" if value_node is not None else ""
                cells[index] = value
            if cells:
                raw_rows.append((row_number, [cells.get(i, "") for i in range(max(cells) + 1)]))
    header = [value.strip() for value in raw_rows[0][1]]
    records = []
    for excel_row, values in raw_rows[1:]:
        row = {header[i]: values[i] if i < len(values) else "" for i in range(len(header))}
        if not str(row.get("text_for_llm_human") or "").strip():
            continue
        row["excel_row"] = excel_row
        records.append(row)
    return sheet, records


def trim_span(text: str, start: int, end: int) -> tuple[int, int]:
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return start, end


def line_spans(text: str) -> list[tuple[int, int]]:
    spans = []
    offset = 0
    for line in text.splitlines(keepends=True):
        content_end = offset + len(line.rstrip("\r\n"))
        start, end = trim_span(text, offset, content_end)
        if start < end:
            spans.append((start, end))
        offset += len(line)
    if offset < len(text):
        start, end = trim_span(text, offset, len(text))
        if start < end:
            spans.append((start, end))
    return spans


def sentence_spans(text: str) -> list[tuple[int, int]]:
    boundaries = [0]
    for match in re.finditer(r"(?:[.!?。！？]+[\"'”’)]*\s+|\n+)", text):
        boundaries.append(match.end())
    boundaries.append(len(text))
    spans = []
    for left, right in zip(boundaries, boundaries[1:]):
        start, end = trim_span(text, left, right)
        if start < end:
            spans.append((start, end))
    return spans


def clause_spans(text: str, sentence: tuple[int, int]) -> list[tuple[int, int]]:
    start, end = sentence
    boundaries = [start]
    fragment = text[start:end]
    for match in re.finditer(r"(?:[,;:] ?\s*|\s+(?:그러나|하지만|따라서|또한|그리고)\s+)", fragment):
        boundaries.append(start + match.end())
    boundaries.append(end)
    result = []
    for left, right in zip(boundaries, boundaries[1:]):
        a, b = trim_span(text, left, right)
        if b - a >= 3:
            result.append((a, b))
    return result or [sentence]


def structure_type(row: dict[str, Any]) -> str:
    text = row["raw_text"]
    if len(re.findall(r"(?m)^\s*\|.*\|\s*$", text)) >= 2:
        return "TABLE"
    if len(re.findall(r"(?m)^\s*(?:[-*•]|\d+[.)])\s+", text)) >= 1:
        return "LIST"
    if "?" in text or "？" in text:
        return "QUESTION"
    if re.search(r"(?:그림|도표|Figure)\s*\d", text, re.I):
        return "CAPTION"
    if "\n" in text:
        return "MULTILINE"
    return "PROSE"


def r2_stratum(row: dict[str, Any]) -> str:
    text, structure = row["raw_text"], row["structure_type"]
    if structure == "TABLE":
        return "TABLE_TEMPLATE"
    if structure in {"LIST", "MULTILINE"}:
        return "LIST_MULTILINE"
    if structure in {"QUESTION", "CAPTION"} or re.search(r"(?:예를\s*들|사례|오해|반박|인용)", text):
        return "QUESTION_CAPTION_DISCOURSE"
    if re.search(r"(?:하지\s*말아야|금지|해야\s*한다|하여야|반드시|필수|권장|바람직|필요하다)", text):
        return "NORMATIVE_DEONTIC"
    if re.search(r"(?:경우|만약|(?:이|라)면|때에는|단,|예외|이전|이후)", text):
        return "CONDITIONAL_EXCEPTION"
    if re.search(r"(?:이란|정의|의미한다|이유|때문|원인|비교|평가|조사\s*결과)", text):
        return "DEFINITION_CAUSAL_EVALUATIVE"
    if re.search(r"(?:않|못|없|부정|\d+(?:\.\d+)?\s*(?:%|명|점|배|~|\u223c))", text):
        return "NEGATION_QUANTITY_HIGH_RISK"
    return "SIMPLE_GENERAL_PROSE"


def build_candidate_lattice(row: dict[str, Any]) -> dict[str, Any]:
    text, structure = row["raw_text"], row["structure_type"]
    candidates: dict[tuple[int, int], dict[str, Any]] = {}

    def add(start: int, end: int, level: str, rule: str, members: list[str] | None = None, parent: str | None = None) -> None:
        start, end = trim_span(text, start, end)
        if start >= end or end > len(text):
            return
        key = (start, end)
        if key not in candidates:
            candidates[key] = {"start_char": start, "end_char": end, "candidate_level": level, "generation_rule": rule, "member_segment_ids": members or [], "parent_candidate_id": parent}

    lines = line_spans(text)
    if structure == "TABLE":
        for start, end in lines:
            if text[start:end].lstrip().startswith("|"):
                add(start, end, "TABLE_ROW", "markdown_table_row_v1")
    elif structure in {"LIST", "MULTILINE"}:
        for index, (start, end) in enumerate(lines, 1):
            add(start, end, "LINE_OR_ITEM", "line_item_v1", [f"L{index:02d}"])
        if len(lines) > 1:
            header = lines[0]
            for index, item in enumerate(lines[1:], 2):
                if item[1] - header[0] <= 240:
                    add(header[0], item[1], "HEADER_PLUS_ITEM", "header_item_merge_v1", ["L01", f"L{index:02d}"])
    else:
        sentences = sentence_spans(text)
        segment_ids: dict[tuple[int, int], str] = {}
        for sentence_index, sentence in enumerate(sentences, 1):
            add(*sentence, "SENTENCE", "sentence_split_v1", [f"S{sentence_index:02d}"])
            clauses = clause_spans(text, sentence)
            for clause_index, clause in enumerate(clauses, 1):
                segment_ids[clause] = f"S{sentence_index:02d}C{clause_index:02d}"
                add(*clause, "CLAUSE", "clause_split_v1", [segment_ids[clause]])
            for width in (2, 3):
                for index in range(len(clauses) - width + 1):
                    merged = (clauses[index][0], clauses[index + width - 1][1])
                    if merged[1] - merged[0] <= 240:
                        add(*merged, f"CLAUSE_MERGE_{width}", f"adjacent_clause_merge_{width}_v1", [segment_ids[item] for item in clauses[index:index + width]])
    if len(text) <= 240:
        add(0, len(text), "FULL_EVIDENCE", "full_evidence_v1")
    ordered = sorted(candidates.values(), key=lambda item: (item["start_char"], item["end_char"], item["candidate_level"]))
    result = []
    for index, item in enumerate(ordered, 1):
        candidate_id = f"{row['evidence_id']}_C{index:02d}"
        result.append({"evidence_id": row["evidence_id"], "candidate_id": candidate_id, **item, "text_by_program": text[item["start_char"]:item["end_char"]], "structure_type": structure})
    return {"evidence_id": row["evidence_id"], "raw_text": text, "structure_type": structure, "candidates": result}


def build_mentions(evidence_id: str, raw_text: str, claim_unit_id: str, start: int, end: int) -> list[dict[str, Any]]:
    fragment = raw_text[start:end]
    spans: set[tuple[int, int, str]] = set()
    patterns = [
        (r"\d+(?:[.,]\d+)?(?:\s*[~∼-]\s*\d+(?:[.,]\d+)?)?\s*(?:%|명|점|배|개|원|년|개월)?", "NUMBER_OR_RANGE"),
        (r"[A-Za-z][A-Za-z0-9/_-]*(?:\s+[A-Za-z][A-Za-z0-9/_-]*){0,2}", "TERM"),
        (r"[가-힣]{2,}(?:\s+[가-힣]{2,}){0,2}", "KOREAN_PHRASE"),
    ]
    for pattern, kind in patterns:
        for match in re.finditer(pattern, fragment):
            a, b = start + match.start(), start + match.end()
            if b - a <= 60:
                spans.add((a, b, kind))
    for match in re.finditer(r"(?:경우|만약|(?:이|라)면|때|이전|이후|예외)", fragment):
        spans.add((start + match.start(), start + match.end(), "CONDITION_CUE"))
    ordered = sorted(spans, key=lambda item: (item[0], item[1], item[2]))
    return [{"evidence_id": evidence_id, "claim_unit_id": claim_unit_id, "mention_id": f"{claim_unit_id}_M{index:02d}", "start_char": a, "end_char": b, "text_by_program": raw_text[a:b], "mention_kind": kind} for index, (a, b, kind) in enumerate(ordered, 1)]


def percentile(values: list[int], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    low, high = int(position), min(len(ordered) - 1, int(position) + 1)
    fraction = position - low
    return ordered[low] * (1 - fraction) + ordered[high] * fraction


def lattice_validation(lattices: list[dict[str, Any]]) -> dict[str, Any]:
    total = roundtrip = unique_ids = unique_offsets = structure_ok = 0
    counts = []
    for lattice in lattices:
        candidates = lattice["candidates"]
        counts.append(len(candidates))
        total += len(candidates)
        roundtrip += sum(lattice["raw_text"][item["start_char"]:item["end_char"]] == item["text_by_program"] for item in candidates)
        unique_ids += int(len({item["candidate_id"] for item in candidates}) == len(candidates))
        unique_offsets += int(len({(item["start_char"], item["end_char"]) for item in candidates}) == len(candidates))
        if lattice["structure_type"] == "TABLE":
            rows = [span for span in line_spans(lattice["raw_text"]) if lattice["raw_text"][span[0]:span[1]].lstrip().startswith("|")]
            preserved = all(any(item["start_char"] == a and item["end_char"] == b for item in candidates) for a, b in rows)
        elif lattice["structure_type"] in {"LIST", "MULTILINE"}:
            rows = line_spans(lattice["raw_text"])
            preserved = all(any(item["start_char"] == a and item["end_char"] == b for item in candidates) for a, b in rows)
        else:
            preserved = bool(candidates)
        structure_ok += int(preserved)
    return {
        "candidate_count": total,
        "evidence_count": len(lattices),
        "offset_round_trip": roundtrip / total if total else 1.0,
        "candidate_id_uniqueness": unique_ids / len(lattices) if lattices else 1.0,
        "offset_uniqueness": unique_offsets / len(lattices) if lattices else 1.0,
        "structure_preservation": structure_ok / len(lattices) if lattices else 1.0,
        "candidate_count_min": min(counts) if counts else 0,
        "candidate_count_median": percentile(counts, 0.5),
        "candidate_count_p95": percentile(counts, 0.95),
        "candidate_count_max": max(counts) if counts else 0,
    }


def deterministic_sample(rows: list[dict[str, Any]], count: int, salt: str) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: sha([SEED, salt, row["evidence_id"]]))[:count]


def stratified_sample(rows: list[dict[str, Any]], quotas: list[tuple[str, int]], salt: str) -> list[dict[str, Any]]:
    by_stratum: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_stratum[row["r2_stratum"]].append(row)
    selected = []
    used = set()
    for stratum, count in quotas:
        candidates = [row for row in deterministic_sample(by_stratum[stratum], len(by_stratum[stratum]), f"{salt}:{stratum}") if row["evidence_id"] not in used]
        if len(candidates) < count:
            raise RuntimeError(f"Insufficient {stratum}: need {count}, have {len(candidates)}")
        for row in candidates[:count]:
            selected.append(row); used.add(row["evidence_id"])
    return sorted(selected, key=lambda row: row["excel_row"])

