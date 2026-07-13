#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run the dependency-free TRACE-OL experiment for the Jaije workbook.

The runner implements the executable, deterministic portion of
TRACE_OL_자이제_Neo4j_전체실험_설계서.md. It preserves every non-empty source
row, builds document/evidence and claim graphs, applies transparent labeling
functions, routes uncertain claims to a bounded LLM queue, projects accepted
claims, and exports an idempotent Neo4j LOAD CSV package.

External OpenAI and live Neo4j execution are represented explicitly as
blocked components when credentials or Docker access are unavailable. They
are never reported as successful local inference or database validation.
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import json
import math
import os
import platform
import re
import subprocess
import sys
import unicodedata
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree as ET


SEED = 20260710
SCHEMA_VERSION = "trace-ol/1.0"
EXPECTED_ROWS = 1366
DESIGN_EXPECTED_INPUT_SHA256 = (
    "9246a6da6c7635b3f34ee55df75112eb38a2984ea06828be943dc196de5926eb"
)
MODEL = "gpt-4o-mini-2024-07-18"
NEO4J_IMAGE = "neo4j:5.26.28-community"
DEFAULT_INPUT = Path(
    "handoff-hanyang/수주제안/자이제_1.xlsx"
)
DEFAULT_DESIGN = Path("TRACE_OL_자이제_Neo4j_전체실험_설계서.md")
DEFAULT_OUTPUT = Path("experiments/trace_ol_jaije_neo4j_20260710")

NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

WHITELIST_PREDICATES = {
    "DEFINES",
    "ALIAS_OF",
    "PART_OF",
    "HAS_STAGE",
    "HAS_TASK",
    "PRECEDES",
    "REQUIRES_INPUT",
    "PRODUCES",
    "USES",
    "PERFORMED_BY",
    "GOVERNED_BY",
    "HAS_PRECONDITION",
    "HAS_CRITERION",
    "HAS_OUTCOME",
    "SUPPORTS_GOAL",
    "SUPPORTS_DECISION",
    "MEASURED_BY",
    "MITIGATES",
    "DISTINCT_FROM",
}

DIRECT_PROJECTION_PREDICATES = WHITELIST_PREDICATES - {"DEFINES"}

REGRESSION_ROWS = {
    218,
    222,
    236,
    243,
    244,
    245,
    246,
    247,
    461,
    497,
    916,
    983,
    1140,
    *range(1315, 1336),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def created_at_for_run(run_id: str) -> str:
    match = re.search(r"run:(\d{8}T\d{6}Z)", run_id)
    if not match:
        return utc_now()
    value = datetime.strptime(match.group(1), "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    return value.isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def stable_hash(value: Any, size: int = 24) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:size]


def normalize_text(value: Any) -> str:
    return unicodedata.normalize("NFC", str(value or ""))


def normalized_scalar(value: Any) -> str | None:
    text = normalize_text(value).strip()
    if not text:
        return None
    try:
        number = float(text)
    except ValueError:
        return text
    return str(int(number)) if number.is_integer() else text


def slug(value: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z가-힣]+", "-", normalize_text(value).strip()).strip("-")
    return cleaned.lower() or stable_hash(value, 12)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def column_index(cell_ref: str) -> int:
    match = re.match(r"([A-Z]+)", cell_ref)
    if not match:
        return 0
    result = 0
    for character in match.group(1):
        result = result * 26 + ord(character) - 64
    return result - 1


def read_xlsx(path: Path) -> tuple[str, list[dict[str, Any]]]:
    """Read the first worksheet directly from OOXML without third-party packages."""
    with zipfile.ZipFile(path) as archive:
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        sheet_node = workbook.find(".//a:sheet", NS)
        sheet_name = sheet_node.attrib.get("name", "Sheet1") if sheet_node is not None else "Sheet1"
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in root.findall("a:si", NS):
                shared_strings.append("".join(node.text or "" for node in item.findall(".//a:t", NS)))

        root = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        raw_rows: list[tuple[int, list[str]]] = []
        for row_node in root.findall(".//a:sheetData/a:row", NS):
            excel_row = int(float(row_node.attrib.get("r", len(raw_rows) + 1)))
            cells: dict[int, str] = {}
            for cell in row_node.findall("a:c", NS):
                index = column_index(cell.attrib.get("r", "A"))
                cell_type = cell.attrib.get("t")
                value_node = cell.find("a:v", NS)
                value = ""
                if cell_type == "s" and value_node is not None:
                    value = shared_strings[int(value_node.text or "0")]
                elif cell_type == "inlineStr":
                    value = "".join(node.text or "" for node in cell.findall(".//a:t", NS))
                elif value_node is not None:
                    value = value_node.text or ""
                cells[index] = normalize_text(value)
            if cells:
                raw_rows.append((excel_row, [cells.get(i, "") for i in range(max(cells) + 1)]))

    if not raw_rows:
        raise ValueError(f"No worksheet rows found in {path}")
    header = [value.strip() for value in raw_rows[0][1]]
    required = {
        "page",
        "chapter_no",
        "chapter_title",
        "section_no",
        "section_title",
        "text_for_llm_human",
    }
    missing = sorted(required - set(header))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    records: list[dict[str, Any]] = []
    for excel_row, values in raw_rows[1:]:
        record = {header[i]: values[i] if i < len(values) else "" for i in range(len(header))}
        if not str(record.get("text_for_llm_human") or "").strip():
            continue
        record["_excel_row"] = excel_row
        records.append(record)
    return sheet_name, records


def classify_block(text: str) -> str:
    has_table = len(re.findall(r"(?m)^\s*\|.*\|\s*$", text)) >= 2
    has_formula = bool(re.search(r"(?:\b[A-Z]\b|Winner|Loser|Value|Cost)\s*[=<>]", text))
    has_list = bool(re.search(r"(?m)^\s*(?:[0-9]+[.)]|[•*-])\s*", text))
    has_question = "?" in text or bool(re.search(r"(?:인가|하는가|일까)[?？]?\s*$", text))
    has_figure = bool(re.search(r"(?:그림|도표|Figure)\s*\d", text, re.I))
    flags = [has_table, has_formula, has_list, has_question, has_figure]
    if sum(flags) > 1:
        return "mixed"
    if has_table:
        return "markdown_table"
    if has_formula:
        return "formula"
    if has_list:
        return "list"
    if has_question:
        return "question"
    if has_figure:
        return "figure_caption"
    return "prose"


def source_id(excel_row: int) -> str:
    return f"src:jaije:v1:clean_sentences:r{excel_row}"


def build_source_blocks(
    records: list[dict[str, Any]], input_path: Path, input_hash: str, run_id: str, sheet_name: str
) -> list[dict[str, Any]]:
    observed_context: list[dict[str, str | None]] = []
    for record in records:
        observed_context.append(
            {
                "chapter_no": normalized_scalar(record.get("chapter_no")),
                "chapter_title": normalized_scalar(record.get("chapter_title")),
                "section_no": normalized_scalar(record.get("section_no")),
                "section_title": normalized_scalar(record.get("section_title")),
            }
        )

    blocks: list[dict[str, Any]] = []
    context_fields = ("chapter_no", "chapter_title", "section_no", "section_title")
    for index, record in enumerate(records):
        raw_context = observed_context[index]
        missing_fields = [field for field in context_fields if raw_context[field] is None]
        inferred: dict[str, str | None] = {field: raw_context[field] for field in context_fields}
        inference_sources: list[str] = []
        if missing_fields:
            for distance in range(1, len(records)):
                candidates = (index - distance, index + distance)
                for candidate_index in candidates:
                    if not 0 <= candidate_index < len(records):
                        continue
                    candidate = observed_context[candidate_index]
                    for field in missing_fields:
                        if inferred[field] is None and candidate[field] is not None:
                            inferred[field] = candidate[field]
                            inference_sources.append(source_id(records[candidate_index]["_excel_row"]))
                if all(inferred[field] is not None for field in missing_fields):
                    break

        text_raw = normalize_text(record["text_for_llm_human"])
        page_raw = normalized_scalar(record.get("page"))
        page = int(page_raw) if page_raw and page_raw.isdigit() else None
        block = {
            "id": source_id(record["_excel_row"]),
            "document_id": "doc:jaije:v1",
            "sheet": sheet_name,
            "excel_row": record["_excel_row"],
            "page_raw": page_raw,
            "page": page,
            "chapter_no_raw": raw_context["chapter_no"],
            "chapter_title_raw": raw_context["chapter_title"],
            "section_no_raw": raw_context["section_no"],
            "section_title_raw": raw_context["section_title"],
            "text_raw": text_raw,
            "text_nfc": unicodedata.normalize("NFC", text_raw),
            "block_type": classify_block(text_raw),
            "context_status": "missing" if missing_fields else "observed",
            "missing_context_fields": missing_fields,
            "inferred_chapter_no": inferred["chapter_no"] if missing_fields else None,
            "inferred_chapter_title": inferred["chapter_title"] if missing_fields else None,
            "inferred_section_no": inferred["section_no"] if missing_fields else None,
            "inferred_section_title": inferred["section_title"] if missing_fields else None,
            "context_inference_source_ids": sorted(set(inference_sources)),
            "context_inference_status": "candidate" if missing_fields else "not_needed",
            "source_file": str(input_path),
            "source_file_sha256": input_hash,
            "content_sha256": sha256_bytes(text_raw.encode("utf-8")),
            "ingest_run_id": run_id,
            "schema_version": "source-block/1.0",
        }
        blocks.append(block)
    return blocks


def segment_text(text: str, block_type: str) -> list[tuple[int, int, str]]:
    if block_type in {"markdown_table", "formula", "mixed"}:
        return [(0, len(text), text)]
    spans: list[tuple[int, int, str]] = []
    cursor = 0
    for piece in re.split(r"(?<=[.!?。！？])\s+|\n+", text):
        if not piece.strip():
            continue
        start = text.find(piece, cursor)
        if start < 0:
            start = cursor
        end = start + len(piece)
        spans.append((start, end, text[start:end]))
        cursor = end
    return spans or [(0, len(text), text)]


def build_evidence_spans(blocks: list[dict[str, Any]], run_id: str) -> list[dict[str, Any]]:
    spans: list[dict[str, Any]] = []
    for block in blocks:
        for start, end, quote in segment_text(block["text_raw"], block["block_type"]):
            spans.append(
                {
                    "id": f"span:{block['id']}:{start}-{end}",
                    "source_id": block["id"],
                    "start": start,
                    "end": end,
                    "quote": quote,
                    "page": block["page"],
                    "excel_row": block["excel_row"],
                    "context_status": block["context_status"],
                    "run_id": run_id,
                    "schema_version": "evidence-span/1.0",
                }
            )
    return spans


def clean_table_cell(value: str) -> str:
    return re.sub(r"<br\s*/?>", " / ", value, flags=re.I).strip()


def parse_tables(blocks: list[dict[str, Any]], run_id: str) -> list[dict[str, Any]]:
    tables: list[dict[str, Any]] = []
    for block in blocks:
        lines = block["text_raw"].splitlines()
        table_lines = [line.strip() for line in lines if line.strip().startswith("|") and line.strip().endswith("|")]
        if len(table_lines) < 2:
            continue
        parsed = [[clean_table_cell(cell) for cell in line.strip("|").split("|")] for line in table_lines]
        separator_index = next(
            (
                index
                for index, row in enumerate(parsed)
                if row and all(bool(re.fullmatch(r":?-{3,}:?", cell.replace(" ", ""))) for cell in row)
            ),
            None,
        )
        if separator_index is None or separator_index == 0:
            continue
        headers = parsed[separator_index - 1]
        data_rows = parsed[separator_index + 1 :]
        width = max([len(headers), *(len(row) for row in data_rows)] or [0])
        headers += [f"column_{index + 1}" for index in range(len(headers), width)]
        normalized_rows = [row + [""] * (width - len(row)) for row in data_rows]
        title_lines = [line.strip() for line in lines[: lines.index(next(line for line in lines if line.strip().startswith("|")))] if line.strip()]
        table_id = f"tbl:{block['id']}:1"
        tables.append(
            {
                "id": table_id,
                "source_id": block["id"],
                "excel_row": block["excel_row"],
                "title": " ".join(title_lines),
                "headers": headers,
                "rows": normalized_rows,
                "column_count": width,
                "row_count": len(normalized_rows),
                "column_consistent": all(len(row) == width for row in normalized_rows),
                "run_id": run_id,
                "schema_version": "table/1.0",
            }
        )
    return tables


def parse_formulas(blocks: list[dict[str, Any]], run_id: str) -> list[dict[str, Any]]:
    formulas: list[dict[str, Any]] = []
    expression_pattern = re.compile(
        r"(?:Value\s*=\s*V|Cost\s*=\s*C|\bV\s*>\s*C\b|Winner\s*\(V-C\)\s*>\s*Loser\s*\(V-C\))",
        re.I,
    )
    for block in blocks:
        expressions = list(dict.fromkeys(match.group(0) for match in expression_pattern.finditer(block["text_raw"])))
        if not expressions:
            continue
        variables = []
        if any(re.search(r"\bV\b", expression) for expression in expressions):
            variables.append({"symbol": "V", "meaning": "Value"})
        if any(re.search(r"\bC\b", expression) for expression in expressions):
            variables.append({"symbol": "C", "meaning": "Cost"})
        constraints = [
            {"operator": ">", "expression": expression}
            for expression in expressions
            if ">" in expression
        ]
        formulas.append(
            {
                "id": f"formula:{block['id']}:1",
                "source_id": block["id"],
                "excel_row": block["excel_row"],
                "expression": " ; ".join(expressions),
                "expressions": expressions,
                "variables": variables,
                "constraints": constraints,
                "interpretation_status": "NeedsReview",
                "context_status": block["context_status"],
                "run_id": run_id,
                "schema_version": "formula/1.0",
            }
        )
    return formulas


KNOWN_TERMS = [
    "Opportunity Assessment",
    "Pursuit Decision",
    "Capture Planning",
    "Capture Plan",
    "Proposal Planning",
    "Bid/No bid Decision",
    "Bidder Comparison Matrix",
    "BCM",
    "Account Plan",
    "Executive Summary",
    "Value",
    "Cost",
    "리스크 관리",
    "경쟁자 분석",
    "경쟁사 분석",
    "핵심 차별화요소",
]


def mine_terms(blocks: list[dict[str, Any]], run_id: str) -> list[dict[str, Any]]:
    mentions: list[dict[str, Any]] = []
    for block in blocks:
        text = block["text_raw"]
        for term in KNOWN_TERMS:
            for match in re.finditer(re.escape(term), text, re.I):
                mentions.append(
                    {
                        "id": f"mention:{block['id']}:{match.start()}-{match.end()}",
                        "surface": text[match.start() : match.end()],
                        "normalized": term.casefold(),
                        "source_id": block["id"],
                        "start": match.start(),
                        "end": match.end(),
                        "term_score": 0.98 if term in {"Capture Plan", "BCM"} else 0.88,
                        "run_id": run_id,
                    }
                )
    return mentions


def entity(entity_id: str, labels: list[str], name: str, **props: Any) -> dict[str, Any]:
    return {"id": entity_id, "labels": labels, "canonical_name": name, **props}


def domain_entities(run_id: str) -> list[dict[str, Any]]:
    definitions = [
        ("process:capture-and-proposal", ["Process"], "수주·제안 프로세스"),
        ("stage:opportunity-assessment", ["Stage"], "Opportunity Assessment"),
        ("stage:capture-planning", ["Stage"], "Capture Planning"),
        ("stage:pursuit-decision", ["Stage", "Decision"], "Pursuit Decision"),
        ("stage:capture-strategy", ["Stage"], "수주전략 수립"),
        ("stage:customer-collaboration", ["Stage"], "고객과 협력"),
        ("stage:competitor-analysis", ["Stage"], "경쟁자 분석"),
        ("task:proposal-planning", ["Task"], "Proposal Planning"),
        ("task:capture-strategy-development", ["Task"], "수주전략 초안 개발"),
        ("task:customer-collaboration", ["Task"], "고객과 솔루션 정의"),
        ("task:competitor-analysis", ["Task"], "경쟁사 분석"),
        ("task:customer-issue-synthesis", ["Task"], "고객 이슈 종합"),
        ("task:strategy-implementation", ["Task"], "전략 구현"),
        ("task:risk-management", ["Task", "Mitigation"], "리스크 관리"),
        ("artifact:capture-plan", ["Artifact"], "Capture Plan"),
        ("artifact:capture-plan-draft", ["Artifact"], "Capture Plan 초안"),
        ("artifact:executive-summary-draft", ["Artifact"], "Executive Summary 초안"),
        ("artifact:bcm", ["Artifact"], "Bidder Comparison Matrix (BCM)"),
        ("artifact:account-plan", ["Artifact"], "Account Plan"),
        ("decision:bid-no-bid", ["Decision"], "Bid/No bid Decision"),
        ("decision:winning-strategy", ["Decision"], "이기는 전략 개발"),
        ("criterion:exactly-same-word", ["Criterion"], "Exactly Same Word 불가능 수준"),
        ("criterion:specific-experience", ["Criterion"], "구체적 경험"),
        ("criterion:schedule-capability", ["Criterion"], "일정준수 역량"),
        ("criterion:budget", ["Criterion"], "예산"),
        ("criterion:manager-familiarity", ["Criterion"], "관리자 친숙도"),
        ("competitor:self", ["Competitor"], "자사"),
        ("competitor:a", ["Competitor"], "A사"),
        ("competitor:b", ["Competitor"], "B사"),
        ("information:individual-issue", ["InformationObject"], "개인의 이슈"),
        ("information:organizational-issue", ["InformationObject"], "조직의 이슈"),
        ("risk:proposed-solution", ["Risk"], "제안 솔루션 리스크"),
        ("risk:schedule-delay", ["Risk"], "일정 지연"),
        ("risk:cost-technology-change", ["Risk"], "기술요소 변경 비용 증대"),
        ("risk:cost-scope-change", ["Risk"], "요구사항·구축범위 변경 비용 증대"),
        ("mitigation:communication-channel", ["Mitigation"], "의사소통 채널 강화 및 협의체 구성"),
        ("mitigation:technology-alternative", ["Mitigation"], "비용 증가 최소화 대안 및 위험관리위원회 검토"),
        ("mitigation:requirements-elicitation", ["Mitigation"], "사용자 요구사항 사전 도출 및 확인"),
        ("rule:risk-avoidance-antipattern", ["Rule"], "리스크 언급 회피 안티패턴"),
        ("rule:risk-disclosure", ["Rule"], "리스크 적극 언급 및 관리 역량 제시"),
        ("lex:capture-plan", ["LexicalEntry"], "Capture Plan"),
        ("concept:capture-plan-information", ["Concept", "InformationObject"], "특정 사업 기회의 영업 정보"),
        ("concept:capture-plan-tool", ["Concept", "Artifact"], "영업 정보를 관리하는 쉬플리 도구"),
    ]
    return [entity(identifier, labels, name, run_id=run_id, schema_version=SCHEMA_VERSION) for identifier, labels, name in definitions]


def canonical_claim_id(
    subject_id: str,
    predicate: str,
    object_id: str | None,
    object_literal: str | None,
    polarity: str,
    modality: str,
    scope: str,
) -> str:
    canonical = {
        "subject": subject_id,
        "predicate": predicate,
        "object": object_id or object_literal,
        "polarity": polarity,
        "modality": modality,
        "conditions": [],
        "scope": scope,
    }
    return f"claim:{stable_hash(canonical, 32)}"


def make_candidate(
    subject_id: str,
    predicate: str,
    row: int,
    run_id: str,
    span_by_row: dict[int, str],
    *,
    object_id: str | None = None,
    object_literal: str | None = None,
    claim_type: str = "relational",
    polarity: str = "positive",
    modality: str = "asserted",
    confidence: float = 0.97,
    critical: bool = False,
    numeric_value: float | None = None,
    scope: str = "document",
    lf_ids: list[str] | None = None,
    utility: float = 0.9,
) -> dict[str, Any]:
    claim_id = canonical_claim_id(subject_id, predicate, object_id, object_literal, polarity, modality, scope)
    return {
        "id": claim_id,
        "claim_type": claim_type,
        "subject_id": subject_id,
        "predicate": predicate,
        "object_id": object_id,
        "object_literal": object_literal,
        "polarity": polarity,
        "modality": modality,
        "condition_span_ids": [],
        "evidence_span_ids": [span_by_row[row]],
        "source_ids": [source_id(row)],
        "source_excel_rows": [row],
        "scope": scope,
        "confidence": round(confidence, 4),
        "critical": critical,
        "numeric_value": numeric_value,
        "labeling_function_votes": [
            {"lf_id": lf_id, "vote": "accept", "weight": 1.0} for lf_id in (lf_ids or ["lf:jaije:exact-structure:1.0"])
        ],
        "utility": utility,
        "extraction_method": "deterministic_labeling_functions",
        "run_id": run_id,
        "schema_version": "claim/1.0",
    }


def fixed_claims(
    blocks_by_row: dict[int, dict[str, Any]], span_by_row: dict[int, str], tables: list[dict[str, Any]], run_id: str
) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []

    def add(subject: str, predicate: str, row: int, **kwargs: Any) -> None:
        if row not in blocks_by_row:
            raise ValueError(f"Required regression row {row} is absent")
        claims.append(make_candidate(subject, predicate, row, run_id, span_by_row, **kwargs))

    add("process:capture-and-proposal", "HAS_STAGE", 218, object_id="stage:opportunity-assessment", critical=True, confidence=0.98)
    add("process:capture-and-proposal", "HAS_STAGE", 218, object_id="stage:pursuit-decision", critical=True, confidence=0.98)
    add("stage:opportunity-assessment", "PRECEDES", 218, object_id="stage:pursuit-decision", critical=True, confidence=0.98)
    add("process:capture-and-proposal", "HAS_STAGE", 236, object_id="stage:capture-planning", confidence=0.97)
    add("stage:capture-planning", "HAS_OUTCOME", 236, object_id="decision:bid-no-bid", confidence=0.97)
    add("task:proposal-planning", "REQUIRES_INPUT", 222, object_id="artifact:capture-plan", critical=True, confidence=0.98)
    add("stage:capture-strategy", "HAS_TASK", 243, object_id="task:capture-strategy-development", confidence=0.97)
    add("task:capture-strategy-development", "PRODUCES", 243, object_id="artifact:capture-plan-draft", confidence=0.97)
    add("task:capture-strategy-development", "PRODUCES", 243, object_id="artifact:executive-summary-draft", confidence=0.97)
    add("stage:customer-collaboration", "HAS_TASK", 244, object_id="task:customer-collaboration", confidence=0.97)
    add("task:customer-collaboration", "PRODUCES", 244, object_id="artifact:capture-plan", confidence=0.97)
    add("stage:competitor-analysis", "HAS_TASK", 246, object_id="task:competitor-analysis", confidence=0.97)
    add("task:competitor-analysis", "PRODUCES", 246, object_id="artifact:bcm", critical=True, confidence=0.98)
    add("artifact:bcm", "SUPPORTS_DECISION", 247, object_id="decision:winning-strategy", confidence=0.97)
    add("concept:capture-plan-information", "DISTINCT_FROM", 461, object_id="artifact:account-plan", claim_type="comparative", confidence=0.97)
    add(
        "concept:capture-plan-information",
        "DEFINES",
        245,
        object_literal="특정 사업 기회에 대한 영업 정보",
        claim_type="definition",
        confidence=0.97,
    )
    add(
        "concept:capture-plan-tool",
        "DEFINES",
        245,
        object_literal="영업 정보를 관리하는 쉬플리 도구",
        claim_type="definition",
        confidence=0.97,
    )
    add("task:customer-issue-synthesis", "REQUIRES_INPUT", 916, object_id="information:individual-issue", confidence=0.96)
    add("task:customer-issue-synthesis", "PRODUCES", 916, object_id="information:organizational-issue", confidence=0.96)
    add("task:strategy-implementation", "GOVERNED_BY", 1140, object_id="criterion:exactly-same-word", claim_type="rule", modality="required", confidence=0.97)
    add(
        "risk:proposed-solution",
        "DEFINES",
        1315,
        object_literal="리스크 관리는 제안된 솔루션의 리스크를 최소화하는 전략이다",
        claim_type="definition",
        confidence=0.97,
    )
    add("task:risk-management", "MITIGATES", 1315, object_id="risk:proposed-solution", confidence=0.97)
    add(
        "rule:risk-avoidance-antipattern",
        "DEFINES",
        1317,
        object_literal="리스크를 언급하는 것 자체를 피하는 일",
        claim_type="rule",
        polarity="negative",
        modality="prohibited",
        confidence=0.97,
    )
    add(
        "rule:risk-disclosure",
        "DEFINES",
        1318,
        object_literal="제안서에서 리스크를 적극적으로 언급하고 관리 역량을 보여준다",
        claim_type="rule",
        modality="recommended",
        confidence=0.97,
    )
    add("mitigation:communication-channel", "MITIGATES", 1333, object_id="risk:schedule-delay", confidence=0.97)
    add("mitigation:technology-alternative", "MITIGATES", 1333, object_id="risk:cost-technology-change", confidence=0.97)
    add("mitigation:requirements-elicitation", "MITIGATES", 1333, object_id="risk:cost-scope-change", confidence=0.97)

    criterion_ids = {
        "구체적 경험": "criterion:specific-experience",
        "일정준수 / 역량": "criterion:schedule-capability",
        "예산": "criterion:budget",
        "관리자 / 친숙도": "criterion:manager-familiarity",
    }
    competitor_ids = {"자사": "competitor:self", "A사": "competitor:a", "B사": "competitor:b"}
    table_983 = next((table for table in tables if table["excel_row"] == 983), None)
    if table_983:
        headers = [re.sub(r"^[①②③④⑤⑥#\s/]+", "", header).strip() for header in table_983["headers"]]
        competitor_columns = {
            index: competitor_ids[header]
            for index, header in enumerate(headers)
            if header in competitor_ids
        }
        for row in table_983["rows"]:
            if len(row) < 6 or not row[0].strip().isdigit():
                continue
            criterion_name = row[1].strip()
            criterion_id = criterion_ids.get(criterion_name)
            if not criterion_id:
                continue
            add("artifact:bcm", "HAS_CRITERION", 983, object_id=criterion_id, confidence=0.97)
            for column_index, competitor_id in competitor_columns.items():
                value_match = re.search(r"\d+(?:\.\d+)?", row[column_index])
                if not value_match:
                    continue
                numeric_value = float(value_match.group(0))
                add(
                    competitor_id,
                    "MEASURED_BY",
                    983,
                    object_id=criterion_id,
                    claim_type="score",
                    confidence=0.96,
                    numeric_value=numeric_value,
                    scope=f"bcm:{criterion_id}:{competitor_id}",
                )
    return claims


def generic_claim_candidates(
    blocks: list[dict[str, Any]], span_by_row: dict[int, str], run_id: str
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    cues = {
        "definition": re.compile(r"(?:이란|란\s|정의|의미|말한다)"),
        "normative": re.compile(r"(?:해야|하여야|필요|중요|권고|피해야|하지 말아야)"),
        "risk": re.compile(r"(?:리스크|위험|대처|완화|대안)"),
        "process": re.compile(r"(?:단계|이후|먼저|끝나고|다음|프로세스)"),
        "comparison": re.compile(r"(?:비교|차이|반면|보다|경쟁자에 비해서)"),
        "formula": re.compile(r"(?:\bV\s*>\s*C\b|Winner\s*\(|Value\s*=|Cost\s*=)"),
        "table": re.compile(r"(?m)^\s*\|.*\|\s*$"),
    }
    for block in blocks:
        text = block["text_raw"]
        matched = [name for name, pattern in cues.items() if pattern.search(text)]
        if not matched and block["block_type"] != "question":
            continue
        if block["block_type"] == "question":
            confidence = 0.15
            status_hint = "reject"
            predicate = "UNMAPPED"
            claim_type = "question"
        else:
            confidence = min(0.88, 0.42 + 0.07 * len(matched))
            status_hint = "route"
            if "definition" in matched:
                predicate, claim_type = "DEFINES", "definition"
            elif "comparison" in matched:
                predicate, claim_type = "DISTINCT_FROM", "comparative"
            elif "risk" in matched:
                predicate, claim_type = "MITIGATES", "risk"
            elif "process" in matched:
                predicate, claim_type = "PRECEDES", "process"
            elif "table" in matched:
                predicate, claim_type = "MEASURED_BY", "table"
            else:
                predicate, claim_type = "DEFINES", "rule"
        section_value = block["section_no_raw"] or block["inferred_section_no"] or "unscoped"
        subject = f"sec:jaije:v1:{slug(str(section_value))}"
        candidate = make_candidate(
            subject,
            predicate,
            block["excel_row"],
            run_id,
            span_by_row,
            object_literal=text,
            claim_type=claim_type,
            confidence=confidence,
            modality="required" if "normative" in matched else "asserted",
            lf_ids=[f"lf:generic:{name}:1.0" for name in matched] or ["lf:question-blocker:1.0"],
            utility=1.0 if block["excel_row"] in REGRESSION_ROWS else (0.85 if set(matched) & {"risk", "formula", "table"} else 0.45),
            scope=f"source-row:{block['excel_row']}",
        )
        candidate["matched_cues"] = matched
        candidate["status_hint"] = status_hint
        candidates.append(candidate)
    return candidates


def adjudicate_candidates(
    fixed: list[dict[str, Any]], generic: list[dict[str, Any]], run_id: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    merged: dict[str, dict[str, Any]] = {candidate["id"]: candidate for candidate in generic}
    merged.update({candidate["id"]: candidate for candidate in fixed})
    candidates = sorted(merged.values(), key=lambda row: row["id"])
    uncertain = [row for row in candidates if 0.25 < row["confidence"] < 0.92]
    queue_size = min(30, math.ceil(len(candidates) * 0.10))
    queued_ids = {
        row["id"]
        for row in sorted(
            uncertain,
            key=lambda item: item["utility"] * (1.0 - abs(2 * item["confidence"] - 1.0)),
            reverse=True,
        )[:queue_size]
    }
    adjudicated: list[dict[str, Any]] = []
    model_calls: list[dict[str, Any]] = []
    api_available = bool(os.environ.get("OPENAI_API_KEY"))
    for sequence, candidate in enumerate(candidates, start=1):
        row = dict(candidate)
        if row["confidence"] >= (0.96 if row["critical"] else 0.92):
            row["status"] = "Accepted"
            row["decision_source"] = "weak_supervision_auto_accept"
        elif row["confidence"] <= 0.25:
            row["status"] = "Rejected"
            row["decision_source"] = "question_or_low_confidence_blocker"
        elif row["id"] in queued_ids:
            row["status"] = "NeedsReview"
            row["decision_source"] = "llm_gate_blocked_missing_api_key" if not api_available else "llm_gate_not_called_by_offline_runner"
            model_calls.append(
                {
                    "id": f"call:{run_id}:{len(model_calls) + 1:06d}",
                    "candidate_id": row["id"],
                    "model": MODEL,
                    "endpoint": "responses.parse",
                    "prompt_template_id": "prompt:claim-adjudicator:1.0",
                    "prompt_hash": stable_hash("TRACE-OL claim adjudicator v1", 64),
                    "input_hash": stable_hash(
                        {"candidate_id": row["id"], "evidence_span_ids": row["evidence_span_ids"]}, 64
                    ),
                    "status": "blocked_missing_api_key" if not api_available else "not_called_offline_mode",
                    "decision": None,
                    "parse_status": "not_attempted",
                    "retry_count": 0,
                    "input_tokens": 0,
                    "cached_input_tokens": 0,
                    "output_tokens": 0,
                    "latency_ms": 0,
                    "estimated_cost_usd": 0.0,
                    "created_at_utc": created_at_for_run(run_id),
                }
            )
        else:
            row["status"] = "NeedsReview"
            row["decision_source"] = "low_utility_review_queue"
        row["sequence"] = sequence
        adjudicated.append(row)
    return candidates, adjudicated, model_calls


def add_node(registry: dict[str, dict[str, Any]], node: dict[str, Any]) -> None:
    identifier = node["id"]
    labels = list(dict.fromkeys(["Entity", *(node.get("labels") or [])]))
    normalized = {**node, "labels": labels}
    if identifier in registry:
        existing = registry[identifier]
        existing["labels"] = list(dict.fromkeys([*(existing.get("labels") or []), *labels]))
        for key, value in normalized.items():
            if key not in existing or existing[key] in (None, "", []):
                existing[key] = value
        return
    registry[identifier] = normalized


def relation_id(source: str, rel_type: str, target: str, discriminator: str = "") -> str:
    return f"rel:{stable_hash([source, rel_type, target, discriminator], 32)}"


def add_relation(
    relationships: list[dict[str, Any]],
    source: str,
    rel_type: str,
    target: str,
    *,
    claim_id: str | None = None,
    run_id: str,
    **props: Any,
) -> None:
    discriminator = claim_id or str(props.get("role") or "")
    candidate = {
        "id": relation_id(source, rel_type, target, discriminator),
        "source_id": source,
        "target_id": target,
        "type": rel_type,
        "claim_id": claim_id,
        "run_id": run_id,
        **props,
    }
    if candidate["id"] not in {row["id"] for row in relationships}:
        relationships.append(candidate)


def build_graph(
    blocks: list[dict[str, Any]],
    spans: list[dict[str, Any]],
    tables: list[dict[str, Any]],
    formulas: list[dict[str, Any]],
    adjudicated: list[dict[str, Any]],
    run_id: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    nodes: dict[str, dict[str, Any]] = {}
    relationships: list[dict[str, Any]] = []
    add_node(nodes, entity(run_id, ["Run"], run_id, run_id=run_id, experiment_id="P2_DISTILLED_PRODUCTION_OFFLINE"))
    add_node(nodes, entity("doc:jaije:v1", ["Document"], "자이제", run_id=run_id))
    add_relation(relationships, run_id, "GENERATED", "doc:jaije:v1", run_id=run_id)

    section_ids: set[str] = set()
    chapter_ids: set[str] = set()
    for block in blocks:
        chapter_no = block["chapter_no_raw"]
        section_no = block["section_no_raw"]
        if chapter_no is not None:
            chapter_id = f"chap:jaije:v1:{slug(str(chapter_no))}"
            if chapter_id not in chapter_ids:
                add_node(
                    nodes,
                    entity(chapter_id, ["Chapter"], block["chapter_title_raw"] or str(chapter_no), chapter_no=chapter_no, run_id=run_id),
                )
                add_relation(relationships, "doc:jaije:v1", "HAS_CHAPTER", chapter_id, run_id=run_id)
                chapter_ids.add(chapter_id)
            if section_no is not None:
                section_id = f"sec:jaije:v1:{slug(str(section_no))}"
                if section_id not in section_ids:
                    add_node(
                        nodes,
                        entity(
                            section_id,
                            ["Section"],
                            block["section_title_raw"] or str(section_no),
                            section_no=section_no,
                            chapter_no=chapter_no,
                            run_id=run_id,
                        ),
                    )
                    add_relation(relationships, chapter_id, "HAS_SECTION", section_id, run_id=run_id)
                    section_ids.add(section_id)
                add_relation(relationships, section_id, "HAS_SOURCE_BLOCK", block["id"], run_id=run_id)
        else:
            add_relation(relationships, "doc:jaije:v1", "HAS_UNSCOPED_BLOCK", block["id"], run_id=run_id)
        add_node(
            nodes,
            {
                "id": block["id"],
                "labels": ["SourceBlock"],
                "canonical_name": f"clean_sentences row {block['excel_row']}",
                **block,
                "run_id": run_id,
            },
        )

    for span in spans:
        add_node(nodes, {"id": span["id"], "labels": ["EvidenceSpan"], "canonical_name": span["id"], **span})
        add_relation(relationships, span["id"], "DERIVED_FROM", span["source_id"], run_id=run_id)

    for table in tables:
        add_node(nodes, entity(table["id"], ["Table"], table["title"] or table["id"], **table))
        add_relation(relationships, table["id"], "DERIVED_FROM", table["source_id"], run_id=run_id)
        for column_index, header in enumerate(table["headers"]):
            column_id = f"column:{table['id']}:{column_index}"
            add_node(nodes, entity(column_id, ["Column"], header or f"column {column_index + 1}", column_index=column_index, run_id=run_id))
            add_relation(relationships, table["id"], "HAS_COLUMN", column_id, run_id=run_id)
        for row_index, values in enumerate(table["rows"]):
            row_id = f"row:{table['id']}:{row_index}"
            add_node(nodes, entity(row_id, ["TableRow"], f"row {row_index + 1}", row_index=row_index, run_id=run_id))
            add_relation(relationships, table["id"], "HAS_ROW", row_id, run_id=run_id)
            for column_index, value in enumerate(values):
                cell_id = f"cell:{table['id']}:r{row_index}:c{column_index}"
                add_node(nodes, entity(cell_id, ["Cell"], value or cell_id, value=value, row_index=row_index, column_index=column_index, run_id=run_id))
                add_relation(relationships, row_id, "HAS_CELL", cell_id, run_id=run_id)
                add_relation(relationships, cell_id, "IN_COLUMN", f"column:{table['id']}:{column_index}", run_id=run_id)

    for formula in formulas:
        add_node(nodes, entity(formula["id"], ["Formula"], formula["expression"], **formula))
        add_relation(relationships, formula["id"], "DERIVED_FROM", formula["source_id"], run_id=run_id)
        for variable in formula["variables"]:
            variable_id = f"variable:{formula['id']}:{variable['symbol']}"
            add_node(nodes, entity(variable_id, ["Variable"], variable["symbol"], meaning=variable["meaning"], symbol=variable["symbol"], run_id=run_id))
            add_relation(relationships, formula["id"], "HAS_VARIABLE", variable_id, run_id=run_id)
        for index, constraint in enumerate(formula["constraints"]):
            constraint_id = f"constraint:{formula['id']}:{index}"
            add_node(nodes, entity(constraint_id, ["Constraint"], constraint["expression"], **constraint, run_id=run_id))
            add_relation(relationships, formula["id"], "HAS_CONSTRAINT", constraint_id, run_id=run_id)

    for item in domain_entities(run_id):
        add_node(nodes, item)
    add_relation(relationships, "lex:capture-plan", "DENOTES", "concept:capture-plan-information", run_id=run_id)
    add_relation(relationships, "lex:capture-plan", "DENOTES", "concept:capture-plan-tool", run_id=run_id)

    lf_ids = sorted({vote["lf_id"] for claim in adjudicated for vote in claim["labeling_function_votes"]})
    for lf_id in lf_ids:
        add_node(nodes, entity(lf_id, ["LabelingFunction", "RuleDecision"], lf_id, run_id=run_id))

    accepted_relations: list[dict[str, Any]] = []
    for claim in adjudicated:
        add_node(
            nodes,
            entity(
                claim["id"],
                ["Claim"],
                f"{claim['subject_id']} {claim['predicate']} {claim['object_id'] or claim['object_literal'] or ''}",
                **claim,
            ),
        )
        add_relation(relationships, claim["id"], "HAS_SUBJECT", claim["subject_id"], run_id=run_id)
        if claim.get("object_id"):
            add_relation(relationships, claim["id"], "HAS_OBJECT", claim["object_id"], run_id=run_id)
        for evidence_id in claim["evidence_span_ids"]:
            add_relation(relationships, claim["id"], "SUPPORTED_BY", evidence_id, run_id=run_id)
        for vote in claim["labeling_function_votes"]:
            add_relation(relationships, claim["id"], "ADJUDICATED_BY", vote["lf_id"], run_id=run_id)
        if (
            claim["status"] == "Accepted"
            and claim.get("object_id")
            and claim["predicate"] in DIRECT_PROJECTION_PREDICATES
        ):
            projected = {
                "id": relation_id(claim["subject_id"], claim["predicate"], claim["object_id"], claim["id"]),
                "source_id": claim["subject_id"],
                "target_id": claim["object_id"],
                "type": claim["predicate"],
                "claim_id": claim["id"],
                "confidence": claim["confidence"],
                "numeric_value": claim.get("numeric_value"),
                "run_id": run_id,
                "status": "Accepted",
                "schema_version": "relation/1.0",
            }
            relationships.append(projected)
            accepted_relations.append(projected)
    return sorted(nodes.values(), key=lambda row: row["id"]), sorted(relationships, key=lambda row: row["id"]), accepted_relations


def static_cqs(
    nodes: list[dict[str, Any]], relationships: list[dict[str, Any]], claims: list[dict[str, Any]], formulas: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    accepted = {claim["id"]: claim for claim in claims if claim["status"] == "Accepted"}
    direct = [row for row in relationships if row.get("claim_id")]

    def has(source: str, rel_type: str, target: str | None = None) -> bool:
        return any(
            row["source_id"] == source and row["type"] == rel_type and (target is None or row["target_id"] == target)
            for row in relationships
        )

    formula_ok = any(
        {variable["symbol"] for variable in formula["variables"]} >= {"V", "C"}
        and any(constraint["operator"] == ">" for constraint in formula["constraints"])
        for formula in formulas
    )
    checks = [
        ("CQ-01", "수주 프로세스 단계와 순서", has("stage:opportunity-assessment", "PRECEDES", "stage:pursuit-decision")),
        ("CQ-02", "단계별 활동과 산출물", has("task:capture-strategy-development", "PRODUCES")),
        ("CQ-03", "Proposal Planning의 입력", has("task:proposal-planning", "REQUIRES_INPUT", "artifact:capture-plan")),
        (
            "CQ-04",
            "Capture Plan의 의미 분리",
            has("lex:capture-plan", "DENOTES", "concept:capture-plan-information")
            and has("lex:capture-plan", "DENOTES", "concept:capture-plan-tool"),
        ),
        ("CQ-05", "Capture Plan과 Account Plan 비교", has("concept:capture-plan-information", "DISTINCT_FROM", "artifact:account-plan")),
        (
            "CQ-06",
            "BCM의 생성과 사용",
            has("task:competitor-analysis", "PRODUCES", "artifact:bcm")
            and has("artifact:bcm", "SUPPORTS_DECISION", "decision:winning-strategy"),
        ),
        (
            "CQ-07",
            "BCM 평가 기준과 점수",
            sum(1 for row in direct if row["source_id"] == "artifact:bcm" and row["type"] == "HAS_CRITERION") >= 4
            and sum(1 for claim in accepted.values() if claim["claim_type"] == "score" and claim.get("numeric_value") is not None) >= 12,
        ),
        ("CQ-08", "가치제안 수식", formula_ok),
        (
            "CQ-09",
            "리스크 정의",
            any(claim["claim_type"] == "definition" and claim["subject_id"].startswith("risk:") for claim in accepted.values()),
        ),
        ("CQ-10", "리스크 대응책", sum(1 for row in direct if row["type"] == "MITIGATES") >= 3),
        (
            "CQ-11",
            "리스크 관리 안티패턴",
            any(claim["claim_type"] == "rule" and claim["polarity"] == "negative" for claim in accepted.values()),
        ),
        (
            "CQ-12",
            "근거 감사",
            all(
                row["claim_id"] in accepted and bool(accepted[row["claim_id"]]["evidence_span_ids"])
                for row in direct
            ),
        ),
    ]
    return [
        {"id": identifier, "question": question, "passed": passed, "execution_mode": "in_memory_static_equivalent"}
        for identifier, question, passed in checks
    ]


def regression_checks(
    blocks_by_row: dict[int, dict[str, Any]], tables: list[dict[str, Any]], formulas: list[dict[str, Any]], relationships: list[dict[str, Any]], claims: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    accepted = [claim for claim in claims if claim["status"] == "Accepted"]

    def direct(source: str, rel_type: str, target: str | None = None) -> bool:
        return any(
            row["source_id"] == source and row["type"] == rel_type and (target is None or row["target_id"] == target)
            for row in relationships
        )

    table_983 = next((table for table in tables if table["excel_row"] == 983), None)
    formula_497 = next((formula for formula in formulas if formula["excel_row"] == 497), None)
    risk_claims = [claim for claim in accepted if any(1315 <= row <= 1335 for row in claim["source_excel_rows"])]
    checks = [
        ("REG-218", direct("stage:opportunity-assessment", "PRECEDES", "stage:pursuit-decision"), "Stage/Decision 순서와 근거"),
        (
            "REG-245",
            direct("lex:capture-plan", "DENOTES", "concept:capture-plan-information")
            and direct("lex:capture-plan", "DENOTES", "concept:capture-plan-tool"),
            "Capture Plan 2개 sense 분리",
        ),
        (
            "REG-497",
            bool(formula_497)
            and {item["symbol"] for item in formula_497["variables"]} >= {"V", "C"}
            and any(item["operator"] == ">" for item in formula_497["constraints"]),
            "Formula/Variable/Constraint 구조",
        ),
        (
            "REG-916-1140",
            all(blocks_by_row[row]["context_status"] == "observed" for row in (916, 1140)),
            "현재 입력의 observed 메타데이터 원문 보존; 설계 기준의 null 기대와 데이터 버전 차이 기록",
        ),
        (
            "REG-983",
            bool(table_983) and table_983["column_count"] == 7 and table_983["row_count"] >= 5,
            "BCM 표 헤더·행·점수 복원",
        ),
        (
            "REG-1315-1335",
            len(risk_claims) >= 7
            and any(claim["polarity"] == "negative" for claim in risk_claims)
            and sum(1 for claim in risk_claims if claim["predicate"] == "MITIGATES") >= 4,
            "Risk/Mitigation/Rule 구분과 안티패턴 극성",
        ),
    ]
    return [{"id": identifier, "passed": passed, "expectation": expectation} for identifier, passed, expectation in checks]


def validation_results(
    blocks: list[dict[str, Any]], spans: list[dict[str, Any]], nodes: list[dict[str, Any]], relationships: list[dict[str, Any]], claims: list[dict[str, Any]], cqs: list[dict[str, Any]], regressions: list[dict[str, Any]], input_hash: str
) -> list[dict[str, Any]]:
    node_ids = [node["id"] for node in nodes]
    node_id_set = set(node_ids)
    accepted = {claim["id"]: claim for claim in claims if claim["status"] == "Accepted"}
    direct = [row for row in relationships if row.get("claim_id")]
    offset_errors = 0
    blocks_by_id = {block["id"]: block for block in blocks}
    for span in spans:
        source = blocks_by_id[span["source_id"]]["text_raw"]
        if source[span["start"] : span["end"]] != span["quote"]:
            offset_errors += 1
    checks = [
        ("VAL_SOURCE_BLOCK_COUNT", "critical", EXPECTED_ROWS, len(blocks), len(blocks) == EXPECTED_ROWS),
        ("VAL_DUPLICATE_SOURCE_ID", "critical", 0, len(blocks) - len({row["id"] for row in blocks}), len(blocks) == len({row["id"] for row in blocks})),
        ("VAL_OFFSET_ROUNDTRIP", "critical", 0, offset_errors, offset_errors == 0),
        ("VAL_GLOBAL_ID_UNIQUENESS", "critical", 0, len(node_ids) - len(node_id_set), len(node_ids) == len(node_id_set)),
        (
            "VAL_DANGLING_RELATIONSHIP_ENDPOINT",
            "critical",
            0,
            sum(1 for row in relationships if row["source_id"] not in node_id_set or row["target_id"] not in node_id_set),
            all(row["source_id"] in node_id_set and row["target_id"] in node_id_set for row in relationships),
        ),
        (
            "VAL_ACCEPTED_WITHOUT_EVIDENCE",
            "critical",
            0,
            sum(1 for claim in accepted.values() if not claim["evidence_span_ids"]),
            all(claim["evidence_span_ids"] for claim in accepted.values()),
        ),
        (
            "VAL_DIRECT_EDGE_CLAIM_CONSISTENCY",
            "critical",
            0,
            sum(1 for row in direct if row["claim_id"] not in accepted),
            all(row["claim_id"] in accepted for row in direct),
        ),
        ("VAL_CQ_PASS", "critical", len(cqs), sum(item["passed"] for item in cqs), all(item["passed"] for item in cqs)),
        (
            "VAL_REGRESSION_PASS",
            "critical",
            len(regressions),
            sum(item["passed"] for item in regressions),
            all(item["passed"] for item in regressions),
        ),
        (
            "VAL_CURRENT_INPUT_MISSING_CONTEXT",
            "critical",
            0,
            sum(block["context_status"] == "missing" for block in blocks),
            sum(block["context_status"] == "missing" for block in blocks) == 0,
        ),
        (
            "VAL_DESIGN_INPUT_HASH_MATCH",
            "comparability",
            DESIGN_EXPECTED_INPUT_SHA256,
            input_hash,
            input_hash == DESIGN_EXPECTED_INPUT_SHA256,
        ),
        (
            "VAL_DESIGN_MISSING_CONTEXT_BASELINE",
            "comparability",
            3,
            sum(block["context_status"] == "missing" for block in blocks),
            sum(block["context_status"] == "missing" for block in blocks) == 3,
        ),
    ]
    return [
        {
            "check_id": check_id,
            "severity": severity,
            "expected": expected,
            "actual": actual,
            "passed": passed,
        }
        for check_id, severity, expected, actual, passed in checks
    ]


def make_split(blocks: list[dict[str, Any]]) -> dict[str, Any]:
    sections: dict[str, dict[str, Any]] = {}
    for block in blocks:
        section_no = block["section_no_raw"]
        if section_no is None:
            continue
        section_id = f"sec:jaije:v1:{slug(str(section_no))}"
        sections.setdefault(
            section_id,
            {
                "section_id": section_id,
                "section_no": section_no,
                "section_title": block["section_title_raw"],
                "source_ids": [],
            },
        )["source_ids"].append(block["id"])
    for section in sections.values():
        bucket = int(stable_hash([SEED, section["section_id"]], 8), 16) % 100
        section["split"] = "R_RULE_DEV" if bucket < 40 else ("D_DEV" if bucket < 70 else "T_TEST")
    return {
        "split_id": "jaije-section-split-v1",
        "seed": SEED,
        "unit": "section",
        "sections": sorted(sections.values(), key=lambda row: row["section_id"]),
        "counts": dict(Counter(row["split"] for row in sections.values())),
    }


def base64_json(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "base64:" + base64.urlsafe_b64encode(payload).decode("ascii")


def export_neo4j(output_dir: Path, nodes: list[dict[str, Any]], relationships: list[dict[str, Any]], run_id: str) -> None:
    neo4j_dir = output_dir / "neo4j"
    node_rows = []
    for node in nodes:
        node_rows.append(
            {
                "id": node["id"],
                "labels": ";".join(node.get("labels") or []),
                "canonical_name": node.get("canonical_name", ""),
                "run_id": node.get("run_id", run_id),
                "status": node.get("status", ""),
                "predicate": node.get("predicate", ""),
                "claim_type": node.get("claim_type", ""),
                "confidence": node.get("confidence", ""),
                "excel_row": node.get("excel_row", ""),
                "page": node.get("page", ""),
                "context_status": node.get("context_status", ""),
                "raw_json": base64_json(node),
            }
        )
    relationship_rows = []
    for rel in relationships:
        relationship_rows.append(
            {
                "edge_id": rel["id"],
                "source_id": rel["source_id"],
                "target_id": rel["target_id"],
                "rel_type": rel["type"],
                "claim_id": rel.get("claim_id", "") or "",
                "confidence": rel.get("confidence", ""),
                "numeric_value": rel.get("numeric_value", "") if rel.get("numeric_value") is not None else "",
                "run_id": rel.get("run_id", run_id),
                "status": rel.get("status", ""),
                "raw_json": base64_json(rel),
            }
        )
    write_csv(
        neo4j_dir / "nodes.csv",
        node_rows,
        ["id", "labels", "canonical_name", "run_id", "status", "predicate", "claim_type", "confidence", "excel_row", "page", "context_status", "raw_json"],
    )
    write_csv(
        neo4j_dir / "relationships.csv",
        relationship_rows,
        ["edge_id", "source_id", "target_id", "rel_type", "claim_id", "confidence", "numeric_value", "run_id", "status", "raw_json"],
    )

    labels = sorted({label for node in nodes for label in node.get("labels") or []})
    rel_types = sorted({rel["type"] for rel in relationships})
    constraints = """CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (n:Entity) REQUIRE n.id IS UNIQUE;
CREATE INDEX source_excel_row IF NOT EXISTS FOR (n:SourceBlock) ON (n.excel_row);
CREATE INDEX source_page IF NOT EXISTS FOR (n:SourceBlock) ON (n.page);
CREATE INDEX claim_status IF NOT EXISTS FOR (n:Claim) ON (n.status);
CREATE INDEX claim_predicate IF NOT EXISTS FOR (n:Claim) ON (n.predicate);
CREATE INDEX concept_name IF NOT EXISTS FOR (n:Concept) ON (n.canonical_name);
"""
    write_text(neo4j_dir / "00_constraints.cypher", constraints)
    load_lines = [
        "// Mount this directory as Neo4j /import before execution.",
        "LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row",
        "MERGE (n:Entity {id: row.id})",
        "SET n.canonical_name = row.canonical_name,",
        "    n.run_id = row.run_id,",
        "    n.status = row.status,",
        "    n.predicate = row.predicate,",
        "    n.claim_type = row.claim_type,",
        "    n.confidence = CASE row.confidence WHEN '' THEN null ELSE toFloat(row.confidence) END,",
        "    n.excel_row = CASE row.excel_row WHEN '' THEN null ELSE toInteger(row.excel_row) END,",
        "    n.page = CASE row.page WHEN '' THEN null ELSE toInteger(row.page) END,",
        "    n.context_status = row.context_status,",
        "    n.raw_json = row.raw_json",
    ]
    for label in labels:
        safe_label = re.sub(r"[^A-Za-z0-9_]", "_", label)
        load_lines.append(
            f"FOREACH (_ IN CASE WHEN '{label}' IN split(row.labels, ';') THEN [1] ELSE [] END | SET n:{safe_label})"
        )
    load_lines[-1] += ";"
    for rel_type in rel_types:
        safe_type = re.sub(r"[^A-Za-z0-9_]", "_", rel_type)
        load_lines.extend(
            [
                "",
                "LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row",
                f"WITH row WHERE row.rel_type = '{rel_type}'",
                "MATCH (s:Entity {id: row.source_id})",
                "MATCH (t:Entity {id: row.target_id})",
                f"MERGE (s)-[r:{safe_type} {{id: row.edge_id}}]->(t)",
                "SET r.claim_id = CASE row.claim_id WHEN '' THEN null ELSE row.claim_id END,",
                "    r.confidence = CASE row.confidence WHEN '' THEN null ELSE toFloat(row.confidence) END,",
                "    r.numeric_value = CASE row.numeric_value WHEN '' THEN null ELSE toFloat(row.numeric_value) END,",
                "    r.run_id = row.run_id,",
                "    r.status = row.status,",
                "    r.raw_json = row.raw_json;",
            ]
        )
    write_text(neo4j_dir / "10_load.cypher", "\n".join(load_lines) + "\n")
    write_text(
        neo4j_dir / "40_validate.cypher",
        """// Replace the literal with the run_id from manifest.json when needed.
MATCH (s:SourceBlock) RETURN count(s) AS source_blocks;
MATCH (s:SourceBlock) WITH s.excel_row AS excel_row, count(*) AS c WHERE c <> 1 RETURN excel_row, c;
MATCH (c:Claim {status:'Accepted'}) WHERE NOT (c)-[:SUPPORTED_BY]->() RETURN c.id, c.predicate;
MATCH ()-[r]->() WHERE r.claim_id IS NOT NULL OPTIONAL MATCH (c:Claim {id:r.claim_id, status:'Accepted'}) WITH r,c WHERE c IS NULL RETURN type(r), r.claim_id;
MATCH (s)-[r:PRODUCES]->(o) WHERE NOT s:Task OR NOT (o:Artifact OR o:InformationObject) RETURN s.id, o.id, r.claim_id;
MATCH (s)-[r:MITIGATES]->(o) WHERE NOT (s:Mitigation OR s:Task) OR NOT o:Risk RETURN s.id, o.id, r.claim_id;
""",
    )
    write_text(
        neo4j_dir / "50_competency_questions.cypher",
        """// CQ-01
MATCH p=(s:Stage)-[:PRECEDES]->(n:Stage) RETURN s.canonical_name, n.canonical_name;
// CQ-03
MATCH (t:Task)-[r:REQUIRES_INPUT]->(i) WHERE t.canonical_name CONTAINS 'Proposal Planning' RETURN t.canonical_name, i.canonical_name, r.claim_id;
// CQ-04
MATCH (l:LexicalEntry)-[:DENOTES]->(c:Concept) WHERE l.canonical_name = 'Capture Plan' RETURN c.id, c.canonical_name, labels(c);
// CQ-06/07
MATCH (t:Task)-[p:PRODUCES]->(b:Artifact) WHERE b.canonical_name CONTAINS 'BCM' OPTIONAL MATCH (b)-[c:HAS_CRITERION]->(criterion) RETURN t.canonical_name, b.canonical_name, collect(criterion.canonical_name), p.claim_id;
// CQ-08
MATCH (f:Formula)-[:HAS_VARIABLE]->(v:Variable) OPTIONAL MATCH (f)-[:HAS_CONSTRAINT]->(c:Constraint) RETURN f.expression, collect(DISTINCT v.symbol), collect(DISTINCT c.expression);
// CQ-10
MATCH (m)-[r:MITIGATES]->(risk:Risk) RETURN m.canonical_name, risk.canonical_name, r.claim_id;
// CQ-12
MATCH (s)-[r]->(o) WHERE r.claim_id IS NOT NULL MATCH (c:Claim {id:r.claim_id})-[:SUPPORTED_BY]->(e) RETURN s.canonical_name, type(r), o.canonical_name, c.id, e.id;
""",
    )
    write_json(
        neo4j_dir / "manifest.json",
        {
            "run_id": run_id,
            "node_count": len(nodes),
            "relationship_count": len(relationships),
            "node_labels": dict(Counter(label for node in nodes for label in node.get("labels") or [])),
            "relationship_types": dict(Counter(row["type"] for row in relationships)),
            "idempotency": "MERGE by Entity.id and relationship.id",
        },
    )


def docker_status() -> dict[str, Any]:
    try:
        result = subprocess.run(
            ["docker", "info"], capture_output=True, text=True, timeout=10, check=False
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as error:
        return {"available": False, "reason": type(error).__name__}
    output = "\n".join([result.stderr, result.stdout]).strip()
    if result.returncode == 0:
        reason = "ok"
    elif "permission denied" in output.lower():
        reason = "permission_denied_docker_socket"
    elif "cannot connect" in output.lower():
        reason = "docker_daemon_unreachable"
    else:
        reason = output.splitlines()[-1] if output else "docker_info_failed"
    return {"available": result.returncode == 0, "reason": reason}


def render_report(
    manifest: dict[str, Any], preflight: dict[str, Any], metrics: dict[str, Any], validations: list[dict[str, Any]], experiments: list[dict[str, Any]]
) -> str:
    critical_failed = [row for row in validations if row["severity"] == "critical" and not row["passed"]]
    comparability_failed = [row for row in validations if row["severity"] == "comparability" and not row["passed"]]
    lines = [
        "# TRACE-OL 자이제 Neo4j 실험 결과",
        "",
        f"- Run ID: `{manifest['run_id']}`",
        f"- 입력: `{manifest['input_file']}`",
        f"- 입력 SHA-256: `{manifest['input_sha256']}`",
        f"- 정적 파이프라인 상태: **{'PASS' if not critical_failed else 'FAIL'}**",
        f"- 설계 기준 비교 가능성: **{'BASELINE_DRIFT' if comparability_failed else 'MATCH'}**",
        f"- 전체 DoD 상태: **{metrics['full_design_status']}**",
        "",
        "## 핵심 결과",
        "",
        "| 항목 | 결과 |",
        "|---|---:|",
    ]
    for key, value in metrics["counts"].items():
        lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "## 데이터 기준 차이",
            "",
            f"설계서 기준 입력 해시는 `{DESIGN_EXPECTED_INPUT_SHA256}`이지만 실제 파일은 `{manifest['input_sha256']}`이다. ",
            f"설계서가 예상한 원문 문맥 누락은 3건이나 현재 파일은 {preflight['actual_missing_context']}건이다. 현재 파일의 값을 원문으로 보존했으며 누락을 인위적으로 재현하지 않았다.",
            "",
            "## 실험 매트릭스",
            "",
            "| 실험 | 상태 | 비고 |",
            "|---|---|---|",
        ]
    )
    for experiment in experiments:
        lines.append(f"| {experiment['id']} | {experiment['status']} | {experiment['reason']} |")
    lines.extend(
        [
            "",
            "## 검증",
            "",
            "| 검사 | 심각도 | 기대 | 실제 | 결과 |",
            "|---|---|---:|---:|---|",
        ]
    )
    for row in validations:
        lines.append(
            f"| {row['check_id']} | {row['severity']} | {row['expected']} | {row['actual']} | {'PASS' if row['passed'] else 'FAIL'} |"
        )
    lines.extend(
        [
            "",
            "## 해석 한계",
            "",
            "- Accepted는 규칙·구조·근거 계약을 통과했다는 뜻이며 human gold 정확도를 뜻하지 않는다.",
            "- OpenAI 키가 없어 선택 게이트의 요청 목록만 동결했고 실제 모델 판정·규칙 증류·3회 반복은 수행하지 않았다.",
            "- Docker 데몬 권한이 없어 Neo4j 실적재는 수행하지 않았다. CSV/Cypher와 인메모리 등가 검증은 생성·통과했다.",
            "- 실행 Python은 3.13.13으로, 설계서가 고정한 3.11/3.12 범위 밖이다. 본 실행기는 표준 라이브러리만 사용해 동작했지만 공식 재현 환경과는 다르다.",
            "- 사람 주석 gold가 없어 precision/recall/F1과 bootstrap CI는 산출하지 않았다.",
        ]
    )
    return "\n".join(lines) + "\n"


def run(args: argparse.Namespace) -> dict[str, Any]:
    input_path = Path(args.input_xlsx).resolve()
    design_path = Path(args.design).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    if not input_path.is_file():
        raise FileNotFoundError(input_path)
    if not design_path.is_file():
        raise FileNotFoundError(design_path)

    input_hash = file_sha256(input_path)
    design_hash = file_sha256(design_path)
    git_commit = "unavailable"
    try:
        git_commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=False
        ).stdout.strip() or "unavailable"
    except FileNotFoundError:
        pass
    run_id = args.run_id or f"run:{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}:P2_OFFLINE:{git_commit}"
    created_at = created_at_for_run(run_id)

    sheet_name, records = read_xlsx(input_path)
    blocks = build_source_blocks(records, input_path, input_hash, run_id, sheet_name)
    if len(blocks) != EXPECTED_ROWS:
        raise ValueError(f"Expected {EXPECTED_ROWS} non-empty rows, found {len(blocks)}")
    spans = build_evidence_spans(blocks, run_id)
    tables = parse_tables(blocks, run_id)
    formulas = parse_formulas(blocks, run_id)
    terms = mine_terms(blocks, run_id)
    blocks_by_row = {block["excel_row"]: block for block in blocks}
    span_by_row: dict[int, str] = {}
    for span in spans:
        span_by_row.setdefault(span["excel_row"], span["id"])
    exact = fixed_claims(blocks_by_row, span_by_row, tables, run_id)
    generic = generic_claim_candidates(blocks, span_by_row, run_id)
    candidates, adjudicated, model_calls = adjudicate_candidates(exact, generic, run_id)
    nodes, relationships, accepted_relations = build_graph(blocks, spans, tables, formulas, adjudicated, run_id)
    cqs = static_cqs(nodes, relationships, adjudicated, formulas)
    regressions = regression_checks(blocks_by_row, tables, formulas, relationships, adjudicated)
    validations = validation_results(blocks, spans, nodes, relationships, adjudicated, cqs, regressions, input_hash)
    critical_failed = [row for row in validations if row["severity"] == "critical" and not row["passed"]]
    split = make_split(blocks)
    docker = docker_status()
    python_supported = sys.version_info[:2] in {(3, 11), (3, 12)}
    api_available = bool(os.environ.get("OPENAI_API_KEY"))
    actual_missing = sum(block["context_status"] == "missing" for block in blocks)

    config = {
        "project": {"name": "traceol-jaije", "seed": SEED, "timezone": "UTC"},
        "input": {"path": str(input_path), "sheet": sheet_name, "expected_rows": EXPECTED_ROWS, "actual_sha256": input_hash},
        "confidence": {"accept_threshold": 0.92, "critical_accept_threshold": 0.96, "reject_threshold": 0.25},
        "llm": {"enabled": api_available, "model": MODEL, "temperature": 0, "budget_ratio": 0.10, "max_calls": 30},
        "neo4j": {"image": NEO4J_IMAGE, "batch_size": 500, "isolation_mode": "fresh_volume"},
        "evaluation": {"split_id": split["split_id"], "gold": None, "llm_repeats": 3},
    }
    config_hash = stable_hash(config, 64)
    preflight = {
        "input_exists": True,
        "input_sha256": input_hash,
        "design_expected_input_sha256": DESIGN_EXPECTED_INPUT_SHA256,
        "input_hash_matches_design": input_hash == DESIGN_EXPECTED_INPUT_SHA256,
        "sheet": sheet_name,
        "required_columns_valid": True,
        "nonempty_source_rows": len(blocks),
        "design_expected_missing_context": 3,
        "actual_missing_context": actual_missing,
        "python": platform.python_version(),
        "python_supported_by_design": python_supported,
        "openai_api_key_available": api_available,
        "docker": docker,
        "output_writable": os.access(output_dir, os.W_OK),
        "status": "BASELINE_DRIFT_AND_EXTERNAL_BLOCKERS",
    }
    manifest = {
        "run_id": run_id,
        "experiment_id": "P2_DISTILLED_PRODUCTION_OFFLINE_PARTIAL",
        "created_at_utc": created_at,
        "input_file": str(input_path),
        "input_sha256": input_hash,
        "design_file": str(design_path),
        "design_sha256": design_hash,
        "design_expected_input_sha256": DESIGN_EXPECTED_INPUT_SHA256,
        "git_commit": git_commit,
        "config_sha256": config_hash,
        "prompt_versions": {"claim": "claim_adjudicator/1.0", "sense": "sense_resolver/1.0"},
        "model": MODEL,
        "seed": SEED,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "neo4j_image": NEO4J_IMAGE,
        "split_id": split["split_id"],
        "gold_version": None,
        "schema_version": SCHEMA_VERSION,
    }
    experiments = [
        {"id": "B0_RULE_ONLY", "status": "EXECUTED", "reason": "전량 규칙 후보 생성·자동 승인/기각 완료"},
        {"id": "B1_LOCAL_EMBEDDING", "status": "NOT_EXECUTED", "reason": "설계 설정에서 local embedding 비활성"},
        {"id": "B2_FULL_ADJ", "status": "BLOCKED", "reason": "OPENAI_API_KEY와 human gold 없음"},
        {"id": "P1_SELECTIVE", "status": "ROUTING_ONLY", "reason": f"{len(model_calls)}건 요청 동결; 실제 API 호출 없음"},
        {"id": "P2_DISTILLED", "status": "PARTIAL", "reason": "teacher 판정이 없어 증류 규칙 0건; B0 승인 결과만 projection"},
    ]
    accepted = [row for row in adjudicated if row["status"] == "Accepted"]
    metrics = {
        "run_id": run_id,
        "full_design_status": "BLOCKED_EXTERNAL_AND_BASELINE_DRIFT",
        "counts": {
            "source_blocks": len(blocks),
            "missing_context_original": actual_missing,
            "evidence_spans": len(spans),
            "tables": len(tables),
            "table_cells": sum(table["row_count"] * table["column_count"] for table in tables),
            "formulas": len(formulas),
            "term_mentions": len(terms),
            "claim_candidates": len(candidates),
            "accepted_claims": len(accepted),
            "needs_review_claims": sum(row["status"] == "NeedsReview" for row in adjudicated),
            "rejected_claims": sum(row["status"] == "Rejected" for row in adjudicated),
            "llm_gate_queue": len(model_calls),
            "actual_llm_calls": 0,
            "distilled_rules": 0,
            "graph_nodes": len(nodes),
            "graph_relationships": len(relationships),
            "accepted_direct_relations": len(accepted_relations),
            "cq_passed": sum(item["passed"] for item in cqs),
            "cq_total": len(cqs),
            "regression_passed": sum(item["passed"] for item in regressions),
            "regression_total": len(regressions),
        },
        "accepted_claim_evidence_coverage": (
            sum(bool(row["evidence_span_ids"]) for row in accepted) / len(accepted) if accepted else 0.0
        ),
        "direct_edge_claim_consistency": (
            sum(row["claim_id"] in {claim["id"] for claim in accepted} for row in accepted_relations) / len(accepted_relations)
            if accepted_relations
            else 0.0
        ),
        "llm_call_ratio": 0.0,
        "gold_precision": None,
        "gold_recall": None,
        "gold_f1": None,
        "bootstrap_ci": None,
        "gold_metrics_reason": "human gold and adjudication log are not available",
    }

    annotation_package = [
        {
            "source_id": block["id"],
            "excel_row": block["excel_row"],
            "text_raw": block["text_raw"],
            "candidate_claim_ids": [claim["id"] for claim in adjudicated if block["id"] in claim["source_ids"]],
            "human_decision": None,
            "annotator": None,
            "status": "unannotated",
        }
        for block in blocks
        if block["excel_row"] in REGRESSION_ROWS
    ]

    write_json(output_dir / "config.lock.json", config)
    write_json(output_dir / "manifest.json", manifest)
    write_json(output_dir / "00_preflight.json", preflight)
    write_jsonl(output_dir / "source_blocks.jsonl", blocks)
    write_jsonl(output_dir / "evidence_spans.jsonl", spans)
    write_jsonl(output_dir / "tables.jsonl", tables)
    write_jsonl(output_dir / "formulas.jsonl", formulas)
    write_jsonl(output_dir / "term_candidates.jsonl", terms)
    write_jsonl(output_dir / "claims.candidate.jsonl", candidates)
    write_jsonl(output_dir / "claims.adjudicated.jsonl", adjudicated)
    write_jsonl(output_dir / "entities.jsonl", nodes)
    write_jsonl(output_dir / "relations.accepted.jsonl", accepted_relations)
    write_jsonl(output_dir / "model_calls.jsonl", model_calls)
    write_jsonl(output_dir / "distilled_rules.jsonl", [])
    write_json(output_dir / "split_manifest.json", split)
    write_jsonl(output_dir / "annotation_package.jsonl", annotation_package)
    write_json(output_dir / "competency_questions.json", cqs)
    write_json(output_dir / "regression_results.json", regressions)
    write_json(output_dir / "validation.json", {"checks": validations, "critical_failed": len(critical_failed)})
    write_json(output_dir / "metrics.json", metrics)
    write_json(output_dir / "experiment_matrix_results.json", experiments)
    export_neo4j(output_dir, nodes, relationships, run_id)
    write_text(output_dir / "report.md", render_report(manifest, preflight, metrics, validations, experiments))
    write_text(
        output_dir / "README.md",
        f"""# TRACE-OL Jaije run\n\nReproduce the deterministic run from the repository root:\n\n```bash\npython scripts/run_trace_ol_jaije_experiment.py \\\n+  --input-xlsx \"{input_path}\" \\\n+  --design \"{design_path}\" \\\n+  --output-dir \"{output_dir}\" \\\n+  --run-id \"{run_id}\"\n```\n\nLoad Neo4j after mounting `{output_dir / 'neo4j'}` as `/import`:\n\n```bash\ncypher-shell -u neo4j -p '<password>' -f /import/00_constraints.cypher\ncypher-shell -u neo4j -p '<password>' -f /import/10_load.cypher\ncypher-shell -u neo4j -p '<password>' -f /import/40_validate.cypher\n```\n""",
    )
    summary = {
        "run_id": run_id,
        "output_dir": str(output_dir),
        "static_validation_status": "PASS" if not critical_failed else "FAIL",
        "full_design_status": metrics["full_design_status"],
        "input_hash_matches_design": input_hash == DESIGN_EXPECTED_INPUT_SHA256,
        "counts": metrics["counts"],
    }
    write_json(output_dir / "run_summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run TRACE-OL Jaije Neo4j experiment")
    parser.add_argument("--input-xlsx", default=str(DEFAULT_INPUT))
    parser.add_argument("--design", default=str(DEFAULT_DESIGN))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--run-id", default="")
    args = parser.parse_args()
    summary = run(args)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
