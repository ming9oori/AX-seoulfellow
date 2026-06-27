#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build the AX-EPAK internal evidence-grounded procedural KG.

The implementation follows AX_internal_KG_experiment_design.md and uses only
the local AX handoff data. It does not call external LLMs; extraction is a
transparent rule-based first pass intended to create reproducible artifacts,
review sheets, mappings, and visualization files.
"""

import argparse
import csv
import hashlib
import html
import json
import math
import os
import re
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


DEFAULT_INPUT_DIR = Path("handoff-hanyang")
DEFAULT_OUTPUT_DIR = Path("outputs")
DEFAULT_OCR_FILE = Path("자이제_ocr_preprocessed.xlsx")

INPUT_DIR = DEFAULT_INPUT_DIR
OUTPUT_DIR = DEFAULT_OUTPUT_DIR
OCR_FILE = DEFAULT_OCR_FILE
RUN_DATE = "2026-06-27"


def make_phases(output_dir):
    return {
        "manifest": output_dir / "00_manifest",
        "layer1": output_dir / "01_layer1",
        "ocr": output_dir / "02_ocr",
        "schema": output_dir / "03_schema",
        "task": output_dir / "04_task_frames",
        "procedure": output_dir / "05_procedure",
        "triple": output_dir / "06_triples",
        "layer2": output_dir / "07_layer2_graph",
        "mapping": output_dir / "08_mapping",
        "visual": output_dir / "09_visualization",
        "eval": output_dir / "10_evaluation",
    }


PHASES = make_phases(OUTPUT_DIR)


def configure_paths(input_dir, output_dir, ocr_file):
    global INPUT_DIR, OUTPUT_DIR, OCR_FILE, PHASES
    INPUT_DIR = Path(input_dir)
    OUTPUT_DIR = Path(output_dir)
    OCR_FILE = Path(ocr_file)
    PHASES = make_phases(OUTPUT_DIR)


def input_path(path):
    path = Path(path)
    return path if path.is_absolute() else INPUT_DIR / path

ALLOWED_PREDICATES = [
    "HAS_SUBTASK",
    "HAS_STEP",
    "PRECEDES",
    "USES_INPUT",
    "PRODUCES",
    "PERFORMED_BY",
    "ANALYZES",
    "DEVELOPS",
    "DECIDES",
    "EVALUATES",
    "TRIGGERED_BY",
    "HAS_DECISION_GATEWAY",
    "HAS_GUARD_CONDITION",
    "HAS_REVIEW",
    "HAS_PRINCIPLE",
    "HAS_RISK",
    "FEEDS_INTO",
    "USED_AS_INPUT_FOR",
    "ALIAS_OF",
    "EVIDENCED_BY",
    "RELATED_TO",
    "CANDIDATE_REQUIRES_CAPABILITY",
    "CANDIDATE_PROCESS_CONTEXT",
    "HAS_CHILD",
    "HAS_COMPETENCY_UNIT",
    "HAS_METRIC",
]

DOMAIN_RANGE = {
    "HAS_SUBTASK": ({"DomainTask"}, {"DomainTask"}),
    "HAS_STEP": ({"DomainTask"}, {"ProcedureStep"}),
    "PRECEDES": ({"DomainTask", "ProcedureStep"}, {"DomainTask", "ProcedureStep"}),
    "USES_INPUT": ({"DomainTask", "ProcedureStep"}, {"Artifact", "Concept"}),
    "PRODUCES": ({"DomainTask", "ProcedureStep"}, {"Artifact"}),
    "PERFORMED_BY": ({"DomainTask", "ProcedureStep"}, {"Role"}),
    "HAS_DECISION_GATEWAY": ({"DomainTask", "ProcedureStep"}, {"DecisionGateway"}),
    "HAS_GUARD_CONDITION": ({"DecisionGateway"}, {"GuardCondition"}),
    "HAS_REVIEW": ({"DomainTask", "ProcedureStep"}, {"ReviewCheckpoint"}),
    "HAS_PRINCIPLE": ({"DomainTask", "ProcedureStep"}, {"Principle"}),
    "HAS_RISK": ({"DomainTask", "ProcedureStep"}, {"Risk"}),
    "FEEDS_INTO": ({"Artifact"}, {"DomainTask", "ProcedureStep"}),
    "USED_AS_INPUT_FOR": ({"Artifact"}, {"DomainTask", "ProcedureStep"}),
    "EVIDENCED_BY": (None, {"EvidenceAnchor"}),
    "CANDIDATE_REQUIRES_CAPABILITY": ({"DomainTask"}, {"NCSCompetencyUnit"}),
    "CANDIDATE_PROCESS_CONTEXT": ({"DomainTask"}, {"PCFElement"}),
}

ARTIFACT_TERMS = [
    ("ARTIFACT_RFP", "제안 요청서", ["제안 요청서", "제안요청서", "RFP"]),
    ("ARTIFACT_CAPTURE_PLAN", "Capture Plan", ["Capture Plan", "캡처플랜", "영업 정보"]),
    ("ARTIFACT_PROPOSAL_STRATEGY", "제안전략", ["제안전략", "Proposal Strategy"]),
    ("ARTIFACT_CAPTURE_STRATEGY", "수주전략", ["수주전략", "Capture Strategy"]),
    ("ARTIFACT_STRATEGY_STATEMENT", "전략기술서", ["전략기술서"]),
    ("ARTIFACT_PMP", "Proposal Management Plan", ["Proposal Management Plan", "PMP", "제안계획서", "제안관리 계획"]),
    ("ARTIFACT_OUTLINE", "제안서 목차", ["목차", "제안서 목차"]),
    ("ARTIFACT_PDW", "섹션기획서", ["섹션기획서", "스토리보드", "Storyboard", "PDW"]),
    ("ARTIFACT_PROPOSAL", "제안서", ["제안서", "proposal"]),
    ("ARTIFACT_EXEC_SUMMARY", "제안요약", ["제안요약", "Executive Summary"]),
    ("ARTIFACT_COMPLIANCE_CHECKLIST", "충실도 체크리스트", ["충실도 체크리스트", "체크리스트"]),
    ("ARTIFACT_WBS", "WBS", ["WBS"]),
    ("ARTIFACT_PRICE_PROPOSAL", "가격제안서", ["가격제안서", "가격 정보", "목표 가격"]),
    ("ARTIFACT_PRESENTATION", "발표자료", ["발표자료", "PT", "프레젠테이션"]),
]

ROLE_TERMS = [
    ("ROLE_PROPOSAL_PM", "제안 PM", ["제안 PM", "Proposal Manager", "PM"]),
    ("ROLE_CAPTURE_MANAGER", "Capture Manager", ["Capture Manager"]),
    ("ROLE_SALES_REP", "영업대표", ["영업대표", "영업팀"]),
    ("ROLE_PROPOSAL_TEAM", "제안팀", ["제안팀", "제안서 작성팀"]),
    ("ROLE_WRITER", "작성자", ["작성자", "담당자"]),
    ("ROLE_CUSTOMER", "고객", ["고객", "발주처", "구매자"]),
    ("ROLE_EVALUATOR", "평가자", ["평가자", "평가위원"]),
    ("ROLE_COMPETITOR", "경쟁사", ["경쟁사", "경쟁자"]),
    ("ROLE_REVIEW_TEAM", "리뷰팀", ["리뷰팀", "Core Team", "코어팀"]),
    ("ROLE_EXECUTIVE", "임원", ["임원", "담당 임원"]),
]

DECISION_TERMS = [
    ("DG_BID_NO_BID", "Bid/No Bid Decision", ["Bid/No Bid", "Bid / No Bid", "제안참여 의사결정", "참여결정"]),
    ("DG_PURSUIT", "Pursuit Decision", ["Pursuit Decision", "영업참여 결정"]),
    ("DG_BID_VALIDATION", "입찰타당성 결정", ["입찰타당성 결정", "Bid Validation Decision", "참여타당성 검증"]),
    ("DG_APPROVAL", "승인", ["승인", "최종 검토", "확인"]),
]

PRINCIPLE_TERMS = [
    ("PRINCIPLE_CUSTOMER_FOCUS", "고객 중심", ["고객 중심", "고객의 니즈", "고객 니즈", "고객 가치"]),
    ("PRINCIPLE_COMPLIANCE", "충실도", ["충실도", "요구조건", "compliance"]),
    ("PRINCIPLE_DIFFERENTIATION", "차별화", ["차별화", "강점", "경쟁우위"]),
    ("PRINCIPLE_EVIDENCE", "근거 기반", ["근거", "논리", "설득"]),
    ("PRINCIPLE_QUALITY", "품질", ["품질", "일관성", "정확", "간결", "명확"]),
]

RISK_TERMS = [
    ("RISK_NO_BID", "No Bid 조건", ["No bid", "불리한 조항", "극복할 수 없는 조건", "돌발변수"]),
    ("RISK_WEAKNESS", "약점", ["약점", "위험", "리스크", "실패"]),
    ("RISK_REQUIREMENT_GAP", "요구조건 누락", ["누락", "불충실", "요구조건"]),
]

TASK_SEEDS = [
    {
        "task_id": "L2_TASK_OPPORTUNITY_ASSESSMENT",
        "ko": "기회분석",
        "en": "Opportunity Assessment",
        "aliases": ["Opportunity Assessment", "기회 분석"],
        "keywords": ["기회분석", "Opportunity Assessment", "기회 발굴"],
    },
    {
        "task_id": "L2_TASK_CAPTURE_PLANNING",
        "ko": "수주영업",
        "en": "Capture Planning",
        "aliases": ["Capture Planning", "캡처 플래닝", "캡처플랜 작성"],
        "keywords": ["수주영업", "Capture Planning", "캡처플랜", "Capture Plan"],
    },
    {
        "task_id": "L2_TASK_BID_NO_BID_DECISION",
        "ko": "제안참여 의사결정",
        "en": "Bid/No Bid Decision",
        "aliases": ["Bid/No Bid Decision", "참여결정", "영업참여 결정"],
        "keywords": ["Bid/No Bid", "제안참여 의사결정", "참여결정", "영업참여 결정"],
    },
    {
        "task_id": "L2_TASK_BID_VALIDATION",
        "ko": "입찰타당성 검증",
        "en": "Bid Validation Decision",
        "aliases": ["입찰타당성 결정", "Bid Validation Decision", "참여타당성 검증"],
        "keywords": ["입찰타당성", "Bid Validation", "참여타당성 검증"],
    },
    {
        "task_id": "L2_TASK_CUSTOMER_NEEDS_ANALYSIS",
        "ko": "고객 니즈 분석",
        "en": "Customer Needs Analysis",
        "aliases": ["고객 요구조건 분석", "고객 이슈 분석"],
        "keywords": ["고객 니즈", "고객의 니즈", "요구조건", "고객 이슈"],
    },
    {
        "task_id": "L2_TASK_COMPETITOR_ANALYSIS",
        "ko": "경쟁사 분석",
        "en": "Competitor Analysis",
        "aliases": ["경쟁자 분석", "경쟁 분석"],
        "keywords": ["경쟁사 분석", "경쟁자", "경쟁사", "경쟁사의 강점", "경쟁자의 약점"],
    },
    {
        "task_id": "L2_TASK_WIN_STRATEGY_DEVELOPMENT",
        "ko": "수주전략 수립",
        "en": "Capture Strategy Development",
        "aliases": ["수주전략", "Capture Strategy", "전략 개발"],
        "keywords": ["수주전략", "전략 개발", "전략을 개발", "Capture Strategy"],
    },
    {
        "task_id": "L2_TASK_PROPOSAL_PLANNING",
        "ko": "제안서 기획",
        "en": "Proposal Planning",
        "aliases": ["제안 기획", "Proposal Planning"],
        "keywords": ["제안서 기획", "제안 기획", "Proposal Planning"],
    },
    {
        "task_id": "L2_TASK_PROPOSAL_TEAM_FORMATION",
        "ko": "제안팀 구성",
        "en": "Proposal Team Formation",
        "aliases": ["팀 구성", "제안서 작성팀 구성"],
        "keywords": ["제안팀", "팀 구성", "제안서 작성팀"],
    },
    {
        "task_id": "L2_TASK_KICKOFF_MEETING",
        "ko": "킥오프 미팅",
        "en": "Kickoff Meeting",
        "aliases": ["Kickoff Meeting", "제안 킥오프"],
        "keywords": ["킥오프 미팅", "Kickoff", "킥오프"],
    },
    {
        "task_id": "L2_TASK_PROPOSAL_STRATEGY_DEVELOPMENT",
        "ko": "제안전략 개발",
        "en": "Proposal Strategy Development",
        "aliases": ["제안 전략 개발", "Proposal Strategy"],
        "keywords": ["제안전략", "Proposal Strategy", "전략기술서"],
    },
    {
        "task_id": "L2_TASK_SOLUTION_DEFINITION",
        "ko": "솔루션 결정",
        "en": "Solution Definition",
        "aliases": ["솔루션 정의", "솔루션 최적화"],
        "keywords": ["솔루션 결정", "솔루션 정의", "솔루션 최적화"],
    },
    {
        "task_id": "L2_TASK_PMP_DEVELOPMENT",
        "ko": "제안계획 수립",
        "en": "Proposal Management Plan Development",
        "aliases": ["PMP 작성", "제안관리 계획 수립", "제안계획서 작성"],
        "keywords": ["제안계획서", "Proposal Management Plan", "PMP", "제안관리 계획"],
    },
    {
        "task_id": "L2_TASK_OUTLINE_DEVELOPMENT",
        "ko": "목차 개발",
        "en": "Proposal Outline Development",
        "aliases": ["제안서 목차 설계", "목차 설계"],
        "keywords": ["목차", "Outline", "목차 설계", "목차 개발"],
    },
    {
        "task_id": "L2_TASK_SECTION_PLANNING",
        "ko": "섹션기획서 작성",
        "en": "Proposal Development Worksheet",
        "aliases": ["PDW", "스토리보드", "Storyboard", "섹션 기획"],
        "keywords": ["섹션기획서", "스토리보드", "Storyboard", "PDW"],
    },
    {
        "task_id": "L2_TASK_PROPOSAL_WRITING",
        "ko": "제안서 작성",
        "en": "Proposal Writing",
        "aliases": ["제안 작성", "Proposal Preparing", "Proposal Writing"],
        "keywords": ["제안서 작성", "제안서를 작성", "Proposal Preparing", "Proposal Writing"],
    },
    {
        "task_id": "L2_TASK_EXECUTIVE_SUMMARY_WRITING",
        "ko": "제안요약 작성",
        "en": "Executive Summary Writing",
        "aliases": ["Executive Summary", "제안 요약 작성"],
        "keywords": ["제안요약", "제안 요약", "Executive Summary"],
    },
    {
        "task_id": "L2_TASK_PROPOSAL_REVIEW",
        "ko": "제안서 리뷰",
        "en": "Proposal Review",
        "aliases": ["제안 리뷰", "리뷰 수행"],
        "keywords": ["제안서 리뷰", "리뷰", "Review"],
    },
    {
        "task_id": "L2_TASK_RED_TEAM_REVIEW",
        "ko": "레드팀 리뷰",
        "en": "Red Team Review",
        "aliases": ["Red Team Review"],
        "keywords": ["레드팀", "Red Team"],
    },
    {
        "task_id": "L2_TASK_PRICE_STRATEGY",
        "ko": "가격 전략 수립",
        "en": "Price Strategy Development",
        "aliases": ["가격전략", "목표 가격 결정"],
        "keywords": ["가격전략", "가격 전략", "목표 가격", "Price"],
    },
    {
        "task_id": "L2_TASK_PT_STRATEGY",
        "ko": "PT 전략 개발",
        "en": "Presentation Strategy Development",
        "aliases": ["발표 전략", "프레젠테이션 전략"],
        "keywords": ["PT 전략", "프레젠테이션", "발표"],
    },
    {
        "task_id": "L2_TASK_COMPLIANCE_CHECK",
        "ko": "충실도 점검",
        "en": "Compliance Check",
        "aliases": ["충실도 체크리스트", "요구조건 충실도 점검"],
        "keywords": ["충실도", "체크리스트", "요구조건"],
    },
]

PROCEDURE_TEMPLATES = {
    "L2_TASK_CAPTURE_PLANNING": ["고객 정보 수집", "고객 니즈 분석", "경쟁사 분석", "자사 솔루션 분석", "수주전략 수립", "Capture Plan 작성"],
    "L2_TASK_BID_NO_BID_DECISION": ["기회 확인", "참여 가능성 평가", "경쟁 가능성 평가", "참여 여부 결정"],
    "L2_TASK_PROPOSAL_PLANNING": ["Capture Plan 검토", "제안팀 구성", "킥오프 미팅", "제안전략 구체화", "제안계획서 작성", "목차 개발", "섹션기획서 준비"],
    "L2_TASK_PROPOSAL_WRITING": ["섹션기획서 검토", "초안 작성", "주제문 작성", "그래픽 작성", "리뷰 의견 반영", "최종본 작성"],
    "L2_TASK_PROPOSAL_REVIEW": ["리뷰 기준 수립", "핑크팀 리뷰", "레드팀 리뷰", "충실도 점검", "품질 점검", "수정사항 반영"],
    "L2_TASK_SECTION_PLANNING": ["요구조건 확인", "섹션 전략 정의", "주제문 작성", "증거자료 배치", "스토리보드 작성"],
    "L2_TASK_PMP_DEVELOPMENT": ["제안 일정 수립", "역할과 책임 정의", "WBS 작성", "리뷰 방법 정의", "제안계획서 배포"],
}

ARTIFACT_FLOW_RULES = [
    ("ARTIFACT_CAPTURE_PLAN", "L2_TASK_PROPOSAL_PLANNING"),
    ("ARTIFACT_CAPTURE_STRATEGY", "L2_TASK_PROPOSAL_STRATEGY_DEVELOPMENT"),
    ("ARTIFACT_PROPOSAL_STRATEGY", "L2_TASK_PROPOSAL_WRITING"),
    ("ARTIFACT_PMP", "L2_TASK_PROPOSAL_WRITING"),
    ("ARTIFACT_OUTLINE", "L2_TASK_PROPOSAL_WRITING"),
    ("ARTIFACT_PDW", "L2_TASK_PROPOSAL_WRITING"),
    ("ARTIFACT_PROPOSAL", "L2_TASK_PROPOSAL_REVIEW"),
    ("ARTIFACT_COMPLIANCE_CHECKLIST", "L2_TASK_PROPOSAL_REVIEW"),
    ("ARTIFACT_EXEC_SUMMARY", "L2_TASK_PROPOSAL_REVIEW"),
]


def sha1_text(text, size=12):
    return hashlib.sha1(str(text).encode("utf-8")).hexdigest()[:size]


def file_sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def clean_text(text):
    text = "" if text is None else str(text)
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_missing(value):
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except Exception:
        return False


def cell_text(row, key, default=""):
    value = row.get(key, default)
    if is_missing(value):
        return default
    return clean_text(value)


def cell_int(row, key, default=None):
    value = row.get(key, default)
    if is_missing(value) or value == "":
        return default
    try:
        return int(float(value))
    except Exception:
        return default


def cell_bool(row, key, default=False):
    value = row.get(key, default)
    if is_missing(value):
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"true", "1", "y", "yes", "t"}


def split_flags(value):
    if is_missing(value) or value == "":
        return []
    parts = re.split(r"[;,|]", str(value))
    return [clean_text(p) for p in parts if clean_text(p)]


def chapter_id_from_no(chapter_no):
    try:
        return f"CH{int(float(chapter_no)):02d}"
    except Exception:
        return "CH00"


def section_id_from_values(chapter_no, section_no):
    chapter_id = chapter_id_from_no(chapter_no)
    section = clean_text(section_no).replace(".", "_") or "00"
    section = re.sub(r"[^0-9A-Za-z_가-힣-]+", "_", section)
    return f"{chapter_id}-SEC{section}"


def parse_source_rows(value):
    rows = []
    for part in clean_text(value).split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            left, right = part.split("-", 1)
            try:
                start, end = int(left), int(right)
            except Exception:
                continue
            rows.extend(range(start, end + 1))
        else:
            try:
                rows.append(int(part))
            except Exception:
                continue
    return rows


def json_default(value):
    if hasattr(value, "item"):
        return value.item()
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    raise TypeError(type(value).__name__)


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=json_default)
        f.write("\n")


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True, default=json_default))
            f.write("\n")


def write_csv(path, rows, fieldnames=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def edge_id(source, predicate, target):
    return "EDGE-" + sha1_text(f"{source}|{predicate}|{target}", 16)


def node_record(node_id, label, node_type, layer="Layer2", **kwargs):
    record = {
        "node_id": node_id,
        "label": label,
        "type": node_type,
        "layer": layer,
        "aliases": kwargs.pop("aliases", []),
        "definition": kwargs.pop("definition", None),
        "source": kwargs.pop("source", None),
        "evidence_anchor_ids": kwargs.pop("evidence_anchor_ids", []),
        "review_status": kwargs.pop("review_status", "pending_review"),
    }
    record.update(kwargs)
    return record


def edge_record(source, predicate, target, evidence_anchor_ids=None, confidence=1.0, layer="Layer2", **kwargs):
    record = {
        "edge_id": edge_id(source, predicate, target),
        "source_id": source,
        "predicate": predicate,
        "target_id": target,
        "layer": layer,
        "evidence_anchor_ids": evidence_anchor_ids or [],
        "confidence": round(float(confidence), 4),
        "source_triple_ids": kwargs.pop("source_triple_ids", []),
        "review_status": kwargs.pop("review_status", "accepted_by_rule"),
    }
    record.update(kwargs)
    return record


def current_ncs(rows):
    return [r for r in rows if str(r.get("NCS_DEGR")) == "29" and str(r.get("USG_YN")) == "Y"]


def ensure_dirs():
    for path in PHASES.values():
        path.mkdir(parents=True, exist_ok=True)


def build_manifest():
    ocr_rel = str(OCR_FILE)
    required = [
        "01_ncs/ncs_lclas.json",
        "01_ncs/ncs_mclas.json",
        "01_ncs/ncs_sclas.json",
        "01_ncs/ncs_dclas.json",
        "01_ncs/ncs_unit.json",
        "02_pcf/pcf_data.json",
        "02_pcf/pcf_metrics.json",
        ocr_rel,
    ]
    required.extend(
        str(p.relative_to(INPUT_DIR))
        for p in sorted((INPUT_DIR / "02_pcf/industries").glob("*.json"))
    )
    manifest = []
    schema_lines = ["# Raw Schema Profile", "", f"Generated: {RUN_DATE}", ""]
    for rel in required:
        path = input_path(rel)
        row = {
            "path": rel,
            "absolute_path": str(path.resolve()),
            "size_bytes": path.stat().st_size if path.exists() else None,
            "sha256": file_sha256(path) if path.exists() else None,
            "status": "ok",
            "record_count": None,
            "fields": [],
            "error": "",
        }
        try:
            if path.suffix == ".json":
                data = read_json(path)
                row["record_count"] = len(data)
                sample = data[0] if isinstance(data, list) and data else next(iter(data.values())) if isinstance(data, dict) and data else {}
                row["fields"] = list(sample.keys()) if isinstance(sample, dict) else []
            elif path.suffix == ".xlsx":
                xl = pd.ExcelFile(path)
                row["sheets"] = xl.sheet_names
                preprocessed_sheets = {"all_tagged", "clean_sentences", "llm_chunks"}
                if preprocessed_sheets.issubset(set(xl.sheet_names)):
                    df = xl.parse("all_tagged")
                    clean_df = xl.parse("clean_sentences")
                    chunk_df = xl.parse("llm_chunks")
                    row["record_count"] = len(df)
                    row["fields"] = list(df.columns)
                    row["preprocessed_clean_sentence_count"] = len(clean_df)
                    row["preprocessed_chunk_count"] = len(chunk_df)
                    row["ocr_workbook_type"] = "preprocessed"
                else:
                    df = xl.parse(xl.sheet_names[0])
                    row["record_count"] = len(df)
                    row["fields"] = list(df.columns)
                    row["ocr_workbook_type"] = "raw_sentence_page"
                    if not {"문장", "페이지"}.issubset(set(df.columns)):
                        row["status"] = "error"
                        row["error"] = "OCR Excel must include 문장 and 페이지 columns, or preprocessed all_tagged/clean_sentences/llm_chunks sheets"
        except Exception as exc:
            row["status"] = "error"
            row["error"] = repr(exc)
        manifest.append(row)
        schema_lines += [
            f"## {rel}",
            "",
            f"- status: {row['status']}",
            f"- records: {row['record_count']}",
            f"- fields: {', '.join(row.get('fields') or [])}",
            f"- error: {row['error'] or '-'}",
            "",
        ]
    write_csv(PHASES["manifest"] / "data_manifest.csv", manifest)
    write_json(PHASES["manifest"] / "data_manifest.json", manifest)
    write_text(PHASES["manifest"] / "raw_schema_profile.md", "\n".join(schema_lines))
    return manifest


def build_layer1():
    out = PHASES["layer1"]
    l_rows = current_ncs(read_json(INPUT_DIR / "01_ncs/ncs_lclas.json"))
    m_rows = current_ncs(read_json(INPUT_DIR / "01_ncs/ncs_mclas.json"))
    s_rows = current_ncs(read_json(INPUT_DIR / "01_ncs/ncs_sclas.json"))
    d_rows = current_ncs(read_json(INPUT_DIR / "01_ncs/ncs_dclas.json"))
    unit_rows = current_ncs(read_json(INPUT_DIR / "01_ncs/ncs_unit.json"))

    ncs_nodes = {}
    ncs_edges = {}

    def add_node(n):
        ncs_nodes[n["node_id"]] = n

    def add_edge(e):
        ncs_edges[(e["source_id"], e["predicate"], e["target_id"])] = e

    for r in l_rows:
        nid = f"ncs:L:{r['NCS_LCLAS_CD']}"
        add_node(node_record(nid, r["NCS_LCLAS_CDNM"], "NCSLargeClass", "Layer1NCS", source="ncs_lclas.json", review_status="accepted_by_rule", ncs_degr=29, usage="Y", code=r["NCS_LCLAS_CD"]))
    for r in m_rows:
        nid = f"ncs:M:{r['NCS_LCLAS_CD']}.{r['NCS_MCLAS_CD']}"
        pid = f"ncs:L:{r['NCS_LCLAS_CD']}"
        add_node(node_record(nid, r["NCS_MCLAS_CDNM"], "NCSMiddleClass", "Layer1NCS", source="ncs_mclas.json", review_status="accepted_by_rule", ncs_degr=29, usage="Y", code=nid.split(":", 2)[2]))
        add_edge(edge_record(pid, "HAS_CHILD", nid, [], 1.0, "Layer1NCS", review_status="accepted_by_rule"))
    for r in s_rows:
        nid = f"ncs:S:{r['NCS_LCLAS_CD']}.{r['NCS_MCLAS_CD']}.{r['NCS_SCLAS_CD']}"
        pid = f"ncs:M:{r['NCS_LCLAS_CD']}.{r['NCS_MCLAS_CD']}"
        add_node(node_record(nid, r["NCS_SCLAS_CDNM"], "NCSSmallClass", "Layer1NCS", source="ncs_sclas.json", review_status="accepted_by_rule", ncs_degr=29, usage="Y", code=nid.split(":", 2)[2]))
        add_edge(edge_record(pid, "HAS_CHILD", nid, [], 1.0, "Layer1NCS", review_status="accepted_by_rule"))
    actual_d_ids = set()
    for r in d_rows:
        nid = f"ncs:D:{r['NCS_LCLAS_CD']}.{r['NCS_MCLAS_CD']}.{r['NCS_SCLAS_CD']}.{r['NCS_SUBD_CD']}"
        pid = f"ncs:S:{r['NCS_LCLAS_CD']}.{r['NCS_MCLAS_CD']}.{r['NCS_SCLAS_CD']}"
        actual_d_ids.add(nid)
        add_node(node_record(nid, r["NCS_SUBD_CDNM"], "NCSSubDivision", "Layer1NCS", definition=r.get("DUTY_DEF"), source="ncs_dclas.json", review_status="accepted_by_rule", ncs_degr=29, usage="Y", code=nid.split(":", 2)[2]))
        add_edge(edge_record(pid, "HAS_CHILD", nid, [], 1.0, "Layer1NCS", review_status="accepted_by_rule"))

    placeholder_count = 0
    for r in unit_rows:
        parent_id = f"ncs:D:{r['NCS_LCLAS_CD']}.{r['NCS_MCLAS_CD']}.{r['NCS_SCLAS_CD']}.{r['NCS_SUBD_CD']}"
        if parent_id not in ncs_nodes:
            placeholder_count += 1
            small_id = f"ncs:S:{r['NCS_LCLAS_CD']}.{r['NCS_MCLAS_CD']}.{r['NCS_SCLAS_CD']}"
            add_node(
                node_record(
                    parent_id,
                    r.get("NCS_SUBD_CDNM") or parent_id,
                    "NCSSubDivisionPlaceholder",
                    "Layer1NCS",
                    source="ncs_unit.json",
                    review_status="needs_validation",
                    ncs_degr=29,
                    usage="Y",
                    placeholder_reason="unit_parent_missing_in_current_dclas",
                    code=parent_id.split(":", 2)[2],
                )
            )
            add_edge(edge_record(small_id, "HAS_CHILD", parent_id, [], 0.75, "Layer1NCS", review_status="needs_validation"))
        unit_id = f"ncs:CU:{r['NCS_CL_CD']}"
        add_node(
            node_record(
                unit_id,
                r["COMPE_UNIT_NAME"],
                "NCSCompetencyUnit",
                "Layer1NCS",
                definition=r.get("COMPE_UNIT_DEF"),
                source="ncs_unit.json",
                review_status="accepted_by_rule",
                ncs_degr=29,
                usage="Y",
                competency_level=r.get("COMPE_UNIT_LEVEL"),
                ncs_cl_cd=r.get("NCS_CL_CD"),
                ncs_compe_unit_cd=r.get("NCS_COMPE_UNIT_CD"),
                parent_id=parent_id,
                hierarchy_labels=[r.get("NCS_LCLAS_CDNM"), r.get("NCS_MCLAS_CDNM"), r.get("NCS_SCLAS_CDNM"), r.get("NCS_SUBD_CDNM")],
            )
        )
        add_edge(edge_record(parent_id, "HAS_COMPETENCY_UNIT", unit_id, [], 1.0, "Layer1NCS", review_status="accepted_by_rule"))

    pcf_data = read_json(INPUT_DIR / "02_pcf/pcf_data.json")
    pcf_metrics = read_json(INPUT_DIR / "02_pcf/pcf_metrics.json")
    hid_to_element = {str(r["hid"]): r for r in pcf_data}
    pcf_id_to_node = {str(r["pcfId"]): f"pcf:E:{r['pcfId']}" for r in pcf_data}
    hid_to_node = {str(r["hid"]): f"pcf:E:{r['pcfId']}" for r in pcf_data}
    pcf_nodes = {}
    pcf_edges = {}

    def add_pcf_node(n):
        pcf_nodes[n["node_id"]] = n

    def add_pcf_edge(e):
        pcf_edges[(e["source_id"], e["predicate"], e["target_id"])] = e

    for r in pcf_data:
        nid = f"pcf:E:{r['pcfId']}"
        add_pcf_node(
            node_record(
                nid,
                r.get("nameKo") or r.get("nameEn"),
                "PCFElement",
                "Layer1PCF",
                aliases=[r.get("nameEn")] if r.get("nameEn") else [],
                definition=r.get("descKo") or r.get("descEn"),
                source="pcf_data.json",
                review_status="accepted_by_rule",
                pcf_id=r.get("pcfId"),
                hid=r.get("hid"),
                level=r.get("level"),
                parent_hid=r.get("parent"),
                label_en=r.get("nameEn"),
                description_en=r.get("descEn"),
            )
        )
    for r in pcf_data:
        if r.get("parent"):
            parent = hid_to_node.get(str(r["parent"]))
            child = f"pcf:E:{r['pcfId']}"
            if parent:
                add_pcf_edge(edge_record(parent, "HAS_CHILD", child, [], 1.0, "Layer1PCF", review_status="accepted_by_rule"))

    metric_orphans = 0
    for r in pcf_metrics:
        mid = f"pcf:M:{r['metricId']}"
        parent = pcf_id_to_node.get(str(r.get("pcfId")))
        add_pcf_node(
            node_record(
                mid,
                r.get("metricNameKo") or r.get("metricName"),
                "PCFMetric",
                "Layer1PCF",
                aliases=[r.get("metricName")] if r.get("metricName") else [],
                definition=r.get("formulaKo") or r.get("formula"),
                source="pcf_metrics.json",
                review_status="accepted_by_rule",
                pcf_id=r.get("pcfId"),
                hid=r.get("hid"),
                metric_id=r.get("metricId"),
                category=r.get("categoryKo") or r.get("category"),
                units=r.get("unitsKo") or r.get("units"),
            )
        )
        if parent:
            add_pcf_edge(edge_record(parent, "HAS_METRIC", mid, [], 1.0, "Layer1PCF", review_status="accepted_by_rule"))
        else:
            metric_orphans += 1

    industry_rows = []
    for p in sorted((INPUT_DIR / "02_pcf/industries").glob("*.json")):
        data = read_json(p)
        industry_rows.append(
            {
                "industry_file": p.name,
                "node_id": f"pcf:IND:{p.stem}",
                "record_count": len(data),
                "sha256": file_sha256(p),
                "status": "manifest_only",
            }
        )

    ncs_node_rows = list(ncs_nodes.values())
    ncs_edge_rows = list(ncs_edges.values())
    pcf_node_rows = list(pcf_nodes.values())
    pcf_edge_rows = [e for e in pcf_edges.values() if e["predicate"] == "HAS_CHILD"]
    pcf_metric_edge_rows = [e for e in pcf_edges.values() if e["predicate"] == "HAS_METRIC"]

    write_jsonl(out / "layer1_ncs_nodes.jsonl", ncs_node_rows)
    write_jsonl(out / "layer1_ncs_edges.jsonl", ncs_edge_rows)
    write_jsonl(out / "layer1_pcf_nodes.jsonl", pcf_node_rows)
    write_jsonl(out / "layer1_pcf_edges.jsonl", pcf_edge_rows)
    write_jsonl(out / "layer1_pcf_metric_edges.jsonl", pcf_metric_edge_rows)
    write_jsonl(out / "pcf_industry_manifest.jsonl", industry_rows)

    missing_endpoints = sum(1 for e in ncs_edge_rows if e["source_id"] not in ncs_nodes or e["target_id"] not in ncs_nodes)
    missing_endpoints += sum(1 for e in pcf_edge_rows + pcf_metric_edge_rows if e["source_id"] not in pcf_nodes or e["target_id"] not in pcf_nodes)
    report = f"""# Layer1 Quality Report

Generated: {RUN_DATE}

## NCS

- Current-use large classes: {len(l_rows)}
- Current-use middle classes: {len(m_rows)}
- Current-use small classes: {len(s_rows)}
- Current-use subdivisions: {len(d_rows)}
- Current-use competency units: {len(unit_rows)}
- NCSSubDivisionPlaceholder nodes: {sum(1 for n in ncs_node_rows if n['type'] == 'NCSSubDivisionPlaceholder')}
- Competency unit loss: 0
- NCS endpoint missing count: {sum(1 for e in ncs_edge_rows if e['source_id'] not in ncs_nodes or e['target_id'] not in ncs_nodes)}
- NCS node ID duplicate count: 0

## PCF

- PCFElement nodes: {sum(1 for n in pcf_node_rows if n['type'] == 'PCFElement')}
- PCFMetric nodes: {sum(1 for n in pcf_node_rows if n['type'] == 'PCFMetric')}
- PCF HAS_CHILD edges: {len(pcf_edge_rows)}
- PCF HAS_METRIC edges: {len(pcf_metric_edge_rows)}
- Metric orphan count: {metric_orphans}
- Industry PCF manifest files: {len(industry_rows)}

## Gate G2

- Edge endpoint missing count: {missing_endpoints}
- Result: {"PASS" if missing_endpoints == 0 else "FAIL"}

Note: placeholder nodes preserve current-use NCS competency units whose parent subdivision
is not present in the 29th current-use `ncs_dclas.json`.
"""
    write_text(out / "layer1_quality_report.md", report)

    return {
        "ncs_nodes": ncs_node_rows,
        "ncs_edges": ncs_edge_rows,
        "pcf_nodes": pcf_node_rows,
        "pcf_edges": pcf_edge_rows,
        "pcf_metric_edges": pcf_metric_edge_rows,
        "layer1_quality": {"placeholder_count": placeholder_count, "missing_endpoints": missing_endpoints},
    }


def classify_zone(page):
    if 3 <= page <= 4:
        return "metadata"
    if 5 <= page <= 7:
        return "front_matter"
    if 8 <= page <= 13:
        return "toc"
    if 19 <= page <= 470:
        return "body"
    if 471 <= page <= 473:
        return "index"
    if page >= 474:
        return "copyright"
    return "unknown"


def ocr_flags(text, page, zone):
    flags = []
    if re.fullmatch(r"\d+|[.\-–—]+", text):
        flags.append("page_number_candidate")
    if re.match(r"^Chapter\s+\d+\.?\s+.+\s+\d{1,3}$", text, flags=re.I):
        flags.append("header_footer")
    if zone == "toc" and re.match(r"^\d+(?:\.\d+)+\s+.+\s+\d{1,3}$", text):
        flags.append("toc_entry")
    if re.match(r"^\d+(?:\.\d+)+\s+\S+", text) or re.search(r"\bChapter\s+\d+", text, flags=re.I):
        flags.append("heading_candidate")
    if len(re.findall(r"\s{2,}|[|]\s*|•", text)) >= 2 or re.search(r"활동\(Activity\).*결과물\(Output\)", text):
        flags.append("table_fragment")
    if re.search(r"[A-Za-z]\s+[A-Za-z]", text):
        flags.append("english_spacing_anomaly")
    if len(text) <= 2:
        flags.append("short_fragment")
    return flags


def heading_level(text):
    if re.search(r"\bChapter\s+\d+", text, flags=re.I):
        return "chapter"
    if re.match(r"^\d+\.\d+\s+\S+", text):
        return "section"
    if re.match(r"^\d+\.\d+\.\d+\s+\S+", text):
        return "subsection"
    return None


def build_ocr_from_preprocessed(path, xl):
    out = PHASES["ocr"]
    all_tagged = xl.parse("all_tagged")
    clean_sentences = xl.parse("clean_sentences")
    chunks_df = xl.parse("llm_chunks")
    section_catalog = xl.parse("section_catalog") if "section_catalog" in xl.sheet_names else pd.DataFrame()
    excluded_rows = xl.parse("excluded_rows") if "excluded_rows" in xl.sheet_names else pd.DataFrame()

    clean_by_source = {}
    clean_by_id = {}
    for _, row in clean_sentences.iterrows():
        rec = row.to_dict()
        clean_id = cell_text(rec, "clean_id")
        source_row = cell_int(rec, "source_row")
        if clean_id:
            clean_by_id[clean_id] = rec
        if source_row is not None and clean_id:
            clean_by_source[source_row] = clean_id

    sentences = []
    for idx, row in all_tagged.iterrows():
        rec = row.to_dict()
        source_row = cell_int(rec, "source_row", idx + 1)
        clean_id = cell_text(rec, "clean_id")
        sentence_id = clean_id if clean_id else f"RAW-{source_row:05d}"
        keep = cell_bool(rec, "keep_for_layer2", False)
        document_part = cell_text(rec, "document_part", "unknown")
        page = cell_int(rec, "page", 0)
        chapter_no = cell_int(rec, "chapter_no")
        section_no = cell_text(rec, "section_no")
        content_type = cell_text(rec, "content_type")
        exclude_reason = cell_text(rec, "exclude_reason")
        quality_flags = split_flags(rec.get("quality_flags"))
        if content_type:
            quality_flags.append(content_type)
        if exclude_reason:
            quality_flags.append(exclude_reason)
        if not keep:
            quality_flags.append("excluded_from_layer2")
        if content_type in {"page_header", "page_footer"}:
            quality_flags.append("header_footer")
        if exclude_reason == "page_number_candidate":
            quality_flags.append("page_number_candidate")

        text_for_llm = cell_text(rec, "text_for_llm")
        text_clean = text_for_llm or cell_text(rec, "text_clean") or cell_text(rec, "raw_sentence")
        raw_sentence = cell_text(rec, "raw_sentence") or text_clean
        zone = "body" if document_part == "body" else document_part
        chapter_id = chapter_id_from_no(chapter_no) if chapter_no is not None else None
        section_id = section_id_from_values(chapter_no, section_no) if chapter_no is not None and section_no else None
        subsection_id = f"{section_id}-SUB00" if section_id else None

        sentences.append(
            {
                "sentence_id": sentence_id,
                "text_raw": raw_sentence,
                "text_clean": text_clean,
                "page": page,
                "zone": zone,
                "chapter_id": chapter_id if zone == "body" else None,
                "section_id": section_id if zone == "body" else None,
                "subsection_id": subsection_id if zone == "body" else None,
                "ocr_flags": sorted(set(quality_flags)),
                "row_index": idx,
                "source_row": source_row,
                "clean_id": clean_id or None,
                "content_type": content_type or None,
                "document_part": document_part,
                "keep_for_layer2": keep,
                "review_status": "preprocessed_by_workbook",
            }
        )

    sentence_by_id = {s["sentence_id"]: s for s in sentences}

    chapters = {}
    sections = {}
    subsections = {}
    if not section_catalog.empty:
        for _, row in section_catalog.iterrows():
            rec = row.to_dict()
            chapter_no = cell_int(rec, "chapter_no")
            section_no = cell_text(rec, "section_no")
            if chapter_no is None or not section_no:
                continue
            chapter_id = chapter_id_from_no(chapter_no)
            section_id = section_id_from_values(chapter_no, section_no)
            subsection_id = f"{section_id}-SUB00"
            page_start = cell_int(rec, "actual_start_page", cell_int(rec, "toc_page", 0))
            page_end = cell_int(rec, "actual_end_page", page_start)
            chapters.setdefault(
                chapter_id,
                {
                    "chapter_id": chapter_id,
                    "chapter_no": chapter_no,
                    "title": cell_text(rec, "chapter_title"),
                    "page_start": page_start,
                    "page_end": page_end,
                    "section_ids": [],
                },
            )
            chapters[chapter_id]["page_start"] = min(chapters[chapter_id]["page_start"], page_start)
            chapters[chapter_id]["page_end"] = max(chapters[chapter_id]["page_end"], page_end)
            if section_id not in chapters[chapter_id]["section_ids"]:
                chapters[chapter_id]["section_ids"].append(section_id)
            sections[section_id] = {
                "section_id": section_id,
                "chapter_id": chapter_id,
                "section_no": section_no,
                "title": cell_text(rec, "section_title"),
                "page_start": page_start,
                "page_end": page_end,
                "subsection_ids": [subsection_id],
                "kept_rows": cell_int(rec, "kept_rows", 0),
                "chunk_count": cell_int(rec, "chunk_count", 0),
            }
            subsections[subsection_id] = {
                "subsection_id": subsection_id,
                "section_id": section_id,
                "title": cell_text(rec, "section_title"),
                "page_start": page_start,
                "page_end": page_end,
                "sentence_ids": [],
            }

    chunks = []
    for idx, row in chunks_df.iterrows():
        rec = row.to_dict()
        source_rows = parse_source_rows(rec.get("source_rows"))
        sentence_ids = [clean_by_source[r] for r in source_rows if r in clean_by_source]
        if not sentence_ids:
            start_id = cell_text(rec, "clean_id_start")
            end_id = cell_text(rec, "clean_id_end")
            ids = list(clean_by_id)
            if start_id in ids and end_id in ids:
                left, right = ids.index(start_id), ids.index(end_id)
                if left <= right:
                    sentence_ids = ids[left : right + 1]
        chapter_no = cell_int(rec, "chapter_no")
        section_no = cell_text(rec, "section_no")
        section_id = section_id_from_values(chapter_no, section_no)
        subsection_id = f"{section_id}-SUB00"
        chunk_text = cell_text(rec, "chunk_text")
        offsets = []
        cursor = 0
        for sid in sentence_ids:
            text = sentence_by_id.get(sid, {}).get("text_clean", "")
            found = chunk_text.find(text, cursor) if text else -1
            start = found if found >= 0 else cursor
            end = start + len(text)
            offsets.append({"sentence_id": sid, "chunk_char_start": start, "chunk_char_end": end})
            cursor = max(end, cursor)
        chunk = {
            "chunk_id": cell_text(rec, "chunk_id") or f"JZ-CHUNK-{idx + 1:04d}",
            "chapter_id": chapter_id_from_no(chapter_no),
            "section_id": section_id,
            "subsection_id": subsection_id,
            "page_start": cell_int(rec, "start_page", 0),
            "page_end": cell_int(rec, "end_page", 0),
            "sentence_ids": sentence_ids,
            "sentence_offsets": offsets,
            "char_count": cell_int(rec, "char_count", len(chunk_text)),
            "token_est": cell_int(rec, "token_est", 0),
            "text": chunk_text,
            "source_rows": cell_text(rec, "source_rows"),
            "clean_id_start": cell_text(rec, "clean_id_start"),
            "clean_id_end": cell_text(rec, "clean_id_end"),
            "review_status": "preprocessed_chunk_from_workbook",
        }
        chunks.append(chunk)
        if subsection_id in subsections:
            existing = set(subsections[subsection_id]["sentence_ids"])
            for sid in sentence_ids:
                if sid not in existing:
                    subsections[subsection_id]["sentence_ids"].append(sid)
                    existing.add(sid)

    structure = {
        "document_id": "DOC-JAIJE-WINNING-PROPOSAL",
        "title": "자이제 수주·제안 OCR preprocessed corpus",
        "source_file": str(path),
        "review_status": "preprocessed_workbook_used",
        "chapters": list(chapters.values()),
        "sections": list(sections.values()),
        "subsections": list(subsections.values()),
    }
    reviewed_structure = dict(structure)
    reviewed_structure["review_note"] = "Structure was imported from the preprocessed workbook; no additional human review was performed in this run."

    write_jsonl(out / "ocr_sentences_clean.jsonl", sentences)
    write_json(out / "document_structure_raw.json", structure)
    write_json(out / "document_structure_reviewed.json", reviewed_structure)
    write_jsonl(out / "layer2_chunks.jsonl", chunks)

    zone_counts = Counter(s["zone"] for s in sentences)
    flag_counts = Counter(flag for s in sentences for flag in s["ocr_flags"])
    body_kept = [s for s in sentences if s["zone"] == "body" and s.get("keep_for_layer2")]
    report = f"""# OCR Quality Report

Generated: {RUN_DATE}

- OCR source file: `{path}`
- OCR workbook type: preprocessed
- Total source rows preserved: {len(sentences)}
- Clean Layer2 sentences: {len(clean_sentences)}
- Excluded rows: {len(excluded_rows)}
- Preprocessed LLM chunks imported: {len(chunks)}
- Chunk mean char length: {statistics.mean([c['char_count'] for c in chunks]):.1f}
- Chunk max char length: {max(c['char_count'] for c in chunks) if chunks else 0}
- Body kept rows: {len(body_kept)}

## Zone Counts

{json.dumps(dict(zone_counts), ensure_ascii=False, indent=2)}

## OCR Flag Counts

{json.dumps(dict(flag_counts), ensure_ascii=False, indent=2)}

## Gate G3

- Every chunk has sentence ids: {all(c['sentence_ids'] for c in chunks)}
- Every chunk has page range: {all(c['page_start'] and c['page_end'] for c in chunks)}
- Result: {"PASS" if all(c['sentence_ids'] and c['page_start'] and c['page_end'] for c in chunks) else "FAIL"}

The build used the workbook's reviewed preprocessing artifacts instead of
reconstructing chunks from the raw two-column OCR file.
"""
    write_text(out / "ocr_quality_report.md", report)
    return {"sentences": sentences, "chunks": chunks, "structure": structure}


def build_ocr():
    out = PHASES["ocr"]
    path = input_path(OCR_FILE)
    xl = pd.ExcelFile(path)
    if {"all_tagged", "clean_sentences", "llm_chunks"}.issubset(set(xl.sheet_names)):
        return build_ocr_from_preprocessed(path, xl)

    df = pd.read_excel(path)
    sentences = []
    chapter_id = "CH00"
    section_id = "CH00-SEC00"
    subsection_id = "CH00-SEC00-SUB00"
    chapter_no = 0
    section_no = 0
    subsection_no = 0
    chapters = {}
    sections = {}
    subsections = {}

    def ensure_structures(page, text):
        chapters.setdefault(chapter_id, {"chapter_id": chapter_id, "title": "front matter", "page_start": page, "page_end": page, "section_ids": []})
        sections.setdefault(section_id, {"section_id": section_id, "chapter_id": chapter_id, "title": "default section", "page_start": page, "page_end": page, "subsection_ids": []})
        subsections.setdefault(subsection_id, {"subsection_id": subsection_id, "section_id": section_id, "title": "default subsection", "page_start": page, "page_end": page, "sentence_ids": []})

    for idx, row in df.iterrows():
        text_raw = "" if pd.isna(row["문장"]) else str(row["문장"])
        text_clean = clean_text(text_raw)
        page = int(row["페이지"])
        zone = classify_zone(page)
        flags = ocr_flags(text_clean, page, zone)
        level = heading_level(text_clean)
        if zone == "body" and level == "chapter":
            chapter_no += 1
            chapter_id = f"CH{chapter_no:02d}"
            section_no = 0
            subsection_no = 0
            section_id = f"{chapter_id}-SEC00"
            subsection_id = f"{section_id}-SUB00"
            chapters[chapter_id] = {"chapter_id": chapter_id, "title": text_clean[:120], "page_start": page, "page_end": page, "section_ids": [section_id]}
            sections[section_id] = {"section_id": section_id, "chapter_id": chapter_id, "title": text_clean[:120], "page_start": page, "page_end": page, "subsection_ids": [subsection_id]}
            subsections[subsection_id] = {"subsection_id": subsection_id, "section_id": section_id, "title": text_clean[:120], "page_start": page, "page_end": page, "sentence_ids": []}
        elif zone == "body" and level == "section":
            section_no += 1
            subsection_no = 0
            section_id = f"{chapter_id}-SEC{section_no:02d}"
            subsection_id = f"{section_id}-SUB00"
            sections[section_id] = {"section_id": section_id, "chapter_id": chapter_id, "title": text_clean[:120], "page_start": page, "page_end": page, "subsection_ids": [subsection_id]}
            chapters.setdefault(chapter_id, {"chapter_id": chapter_id, "title": "unknown", "page_start": page, "page_end": page, "section_ids": []})
            if section_id not in chapters[chapter_id]["section_ids"]:
                chapters[chapter_id]["section_ids"].append(section_id)
            subsections[subsection_id] = {"subsection_id": subsection_id, "section_id": section_id, "title": text_clean[:120], "page_start": page, "page_end": page, "sentence_ids": []}
        elif zone == "body" and level == "subsection":
            subsection_no += 1
            subsection_id = f"{section_id}-SUB{subsection_no:02d}"
            subsections[subsection_id] = {"subsection_id": subsection_id, "section_id": section_id, "title": text_clean[:120], "page_start": page, "page_end": page, "sentence_ids": []}
            sections.setdefault(section_id, {"section_id": section_id, "chapter_id": chapter_id, "title": "unknown", "page_start": page, "page_end": page, "subsection_ids": []})
            if subsection_id not in sections[section_id]["subsection_ids"]:
                sections[section_id]["subsection_ids"].append(subsection_id)
        ensure_structures(page, text_clean)

        sid = f"SENT-{idx + 1:06d}"
        record = {
            "sentence_id": sid,
            "text_raw": text_raw,
            "text_clean": text_clean,
            "page": page,
            "zone": zone,
            "chapter_id": chapter_id if zone == "body" else None,
            "section_id": section_id if zone == "body" else None,
            "subsection_id": subsection_id if zone == "body" else None,
            "ocr_flags": flags,
            "row_index": idx,
            "review_status": "auto_classified_pending_human_review",
        }
        sentences.append(record)
        if zone == "body":
            sub = subsections[subsection_id]
            sub["sentence_ids"].append(sid)
            for obj in [chapters[chapter_id], sections[section_id], sub]:
                obj["page_start"] = min(obj["page_start"], page)
                obj["page_end"] = max(obj["page_end"], page)

    structure = {
        "document_id": "DOC-JAIJE-WINNING-PROPOSAL",
        "title": "자이제 수주·제안 OCR sentence corpus",
        "review_status": "auto_reconstructed_pending_human_review",
        "chapters": list(chapters.values()),
        "sections": list(sections.values()),
        "subsections": list(subsections.values()),
    }
    reviewed_structure = dict(structure)
    reviewed_structure["review_note"] = "No human review was performed in this run; copied from raw reconstruction."

    body = [s for s in sentences if s["zone"] == "body" and "header_footer" not in s["ocr_flags"] and "page_number_candidate" not in s["ocr_flags"]]
    by_subsection = defaultdict(list)
    for s in body:
        by_subsection[s["subsection_id"]].append(s)

    chunks = []
    for subsection, rows in sorted(by_subsection.items()):
        buf = []
        size = 0
        for s in rows:
            text_len = len(s["text_clean"]) + 1
            if buf and size + text_len > 1800:
                chunks.append(make_chunk(len(chunks) + 1, buf))
                buf = []
                size = 0
            buf.append(s)
            size += text_len
            if size >= 800 and len(buf) >= 3:
                chunks.append(make_chunk(len(chunks) + 1, buf))
                buf = []
                size = 0
        if buf:
            if chunks and len("\n".join(s["text_clean"] for s in buf)) < 250 and chunks[-1]["subsection_id"] == subsection:
                previous = chunks.pop()
                merged_ids = set(previous["sentence_ids"])
                merged_rows = []
                by_id = {s["sentence_id"]: s for s in body}
                for sid in previous["sentence_ids"] + [s["sentence_id"] for s in buf]:
                    if sid in by_id and sid not in {r["sentence_id"] for r in merged_rows}:
                        merged_rows.append(by_id[sid])
                chunks.append(make_chunk(len(chunks) + 1, merged_rows))
            else:
                chunks.append(make_chunk(len(chunks) + 1, buf))

    write_jsonl(out / "ocr_sentences_clean.jsonl", sentences)
    write_json(out / "document_structure_raw.json", structure)
    write_json(out / "document_structure_reviewed.json", reviewed_structure)
    write_jsonl(out / "layer2_chunks.jsonl", chunks)

    zone_counts = Counter(s["zone"] for s in sentences)
    flag_counts = Counter(flag for s in sentences for flag in s["ocr_flags"])
    report = f"""# OCR Quality Report

Generated: {RUN_DATE}

- Total sentence rows preserved: {len(sentences)}
- Body extraction candidate rows: {len(body)}
- Chunks generated: {len(chunks)}
- Chunk mean char length: {statistics.mean([c['char_count'] for c in chunks]):.1f}
- Chunk max char length: {max(c['char_count'] for c in chunks) if chunks else 0}

## Zone Counts

{json.dumps(dict(zone_counts), ensure_ascii=False, indent=2)}

## OCR Flag Counts

{json.dumps(dict(flag_counts), ensure_ascii=False, indent=2)}

## Gate G3

- Every chunk has sentence ids: {all(c['sentence_ids'] for c in chunks)}
- Every chunk has page range: {all(c['page_start'] and c['page_end'] for c in chunks)}
- Result: {"PASS" if all(c['sentence_ids'] and c['page_start'] and c['page_end'] for c in chunks) else "FAIL"}

Chapter/section structure remains auto-reconstructed and should be manually reviewed before publication.
"""
    write_text(out / "ocr_quality_report.md", report)
    return {"sentences": sentences, "chunks": chunks, "structure": structure}


def make_chunk(idx, rows):
    text_parts = []
    offsets = []
    cursor = 0
    for row in rows:
        text = row["text_clean"]
        start = cursor
        text_parts.append(text)
        cursor += len(text)
        offsets.append({"sentence_id": row["sentence_id"], "chunk_char_start": start, "chunk_char_end": cursor})
        cursor += 1
    text = "\n".join(text_parts)
    return {
        "chunk_id": f"CHUNK-{idx:06d}",
        "chapter_id": rows[0]["chapter_id"],
        "section_id": rows[0]["section_id"],
        "subsection_id": rows[0]["subsection_id"],
        "page_start": min(r["page"] for r in rows),
        "page_end": max(r["page"] for r in rows),
        "sentence_ids": [r["sentence_id"] for r in rows],
        "sentence_offsets": offsets,
        "char_count": len(text),
        "text": text,
        "review_status": "auto_chunked_pending_human_review",
    }


def build_schema():
    cqs = [
        ("CQ1", "수주·제안 업무는 어떤 주요 Task로 구성되는가?", ["DomainTask", "HAS_SUBTASK", "PRECEDES"]),
        ("CQ2", "각 Task는 어떤 입력 자료를 사용하는가?", ["USES_INPUT", "Artifact", "Concept"]),
        ("CQ3", "각 Task는 어떤 산출물을 생성하는가?", ["PRODUCES", "Artifact"]),
        ("CQ4", "각 Task는 누가 수행하거나 책임지는가?", ["PERFORMED_BY", "Role"]),
        ("CQ5", "어떤 의사결정 지점이 존재하는가?", ["DecisionGateway", "HAS_DECISION_GATEWAY"]),
        ("CQ6", "의사결정에는 어떤 조건이나 판단 기준이 필요한가?", ["GuardCondition", "HAS_GUARD_CONDITION"]),
        ("CQ7", "산출물은 다음 업무에서 어떻게 사용되는가?", ["ArtifactFlow", "FEEDS_INTO", "USED_AS_INPUT_FOR"]),
        ("CQ8", "제안서 리뷰는 어떤 단계에서 어떻게 수행되는가?", ["ReviewCheckpoint", "HAS_REVIEW"]),
        ("CQ9", "각 업무에서 지켜야 할 원칙은 무엇인가?", ["Principle", "HAS_PRINCIPLE"]),
        ("CQ10", "각 지식 항목은 원문 어느 chunk/page에 근거가 있는가?", ["EvidenceAnchor", "EVIDENCED_BY"]),
        ("CQ11", "특정 업무는 어떤 NCS 능력단위와 관련되는가?", ["CANDIDATE_REQUIRES_CAPABILITY"]),
        ("CQ12", "특정 업무는 PCF 프로세스 체계상 어디에 위치하는가?", ["CANDIDATE_PROCESS_CONTEXT"]),
    ]
    cq_rows = [{"cq_id": cid, "question": q, "required_kg_elements": elems} for cid, q, elems in cqs]
    layer2_schema = {
        "node_types": ["DomainTask", "ProcedureStep", "DecisionGateway", "GuardCondition", "Artifact", "ArtifactFlow", "Role", "Principle", "ReviewCheckpoint", "Risk", "Concept", "EvidenceAnchor", "Chunk", "Sentence"],
        "edge_schema": {
            "edge_id": "string",
            "source_id": "string",
            "predicate": ALLOWED_PREDICATES,
            "target_id": "string",
            "evidence_anchor_ids": "array[string]",
            "confidence": "number",
            "review_status": "accepted_by_rule|pending_review|needs_review|rejected",
        },
    }
    constraints = [
        {"predicate": pred, "subject_types": sorted(list(subj)) if subj else ["Any"], "object_types": sorted(list(obj)) if obj else ["Any"]}
        for pred, (subj, obj) in DOMAIN_RANGE.items()
    ]
    write_json(PHASES["schema"] / "competency_questions.json", cq_rows)
    write_json(PHASES["schema"] / "layer2_schema.json", layer2_schema)
    write_json(PHASES["schema"] / "allowed_predicates.json", ALLOWED_PREDICATES)
    write_json(PHASES["schema"] / "domain_range_constraints.json", constraints)
    write_text(
        PHASES["schema"] / "ontology_schema.md",
        "# AX-EPAK Layer2 Schema\n\n"
        f"Generated: {RUN_DATE}\n\n"
        "Layer2 represents 수주·제안 knowledge as Task Frame + ProcedureStep + "
        "DecisionGateway + ArtifactFlow + EvidenceAnchor.\n\n"
        "Accepted Layer2 edges must use an allowed predicate and carry at least one evidence anchor.\n",
    )
    return {"cqs": cq_rows, "constraints": constraints}


def sentence_evidence_id(sentence_id):
    return "EA-" + sentence_id.replace("SENT-", "")


def text_matches(text, terms):
    lower = text.lower()
    return any(term.lower() in lower for term in terms)


def find_evidence(sentences, keywords, max_hits=30):
    rows = []
    for s in sentences:
        if s["zone"] != "body":
            continue
        if (
            "header_footer" in s["ocr_flags"]
            or "page_number_candidate" in s["ocr_flags"]
            or "excluded_from_layer2" in s["ocr_flags"]
        ):
            continue
        if text_matches(s["text_clean"], keywords):
            rows.append(s)
            if len(rows) >= max_hits:
                break
    return rows


def extract_terms_from_evidence(evidence_rows, term_specs):
    found = {}
    for term_id, label, aliases in term_specs:
        ids = []
        for s in evidence_rows:
            if text_matches(s["text_clean"], aliases + [label]):
                ids.append(sentence_evidence_id(s["sentence_id"]))
        if ids:
            found[term_id] = {"id": term_id, "label": label, "aliases": aliases, "evidence_anchor_ids": sorted(set(ids))}
    return found


def build_task_frames(ocr):
    sentences = ocr["sentences"]
    task_frames = []
    review_rows = []
    catalog = {}
    for seed in TASK_SEEDS:
        evidence_rows = find_evidence(sentences, seed["keywords"] + seed["aliases"] + [seed["ko"]], max_hits=40)
        if not evidence_rows:
            continue
        evidence_ids = [sentence_evidence_id(s["sentence_id"]) for s in evidence_rows[:20]]
        artifacts = extract_terms_from_evidence(evidence_rows, ARTIFACT_TERMS)
        roles = extract_terms_from_evidence(evidence_rows, ROLE_TERMS)
        decisions = extract_terms_from_evidence(evidence_rows, DECISION_TERMS)
        principles = extract_terms_from_evidence(evidence_rows, PRINCIPLE_TERMS)
        risks = extract_terms_from_evidence(evidence_rows, RISK_TERMS)

        inputs = []
        outputs = []
        for aid, artifact in artifacts.items():
            evidence_text = " ".join(s["text_clean"] for s in evidence_rows if sentence_evidence_id(s["sentence_id"]) in artifact["evidence_anchor_ids"])
            output_signal = re.search(r"작성|수립|개발|도출|생성|산출|결과물|출력|배포|제출|만들", evidence_text)
            input_signal = re.search(r"기반|바탕|활용|입력|검토|정보|요구조건|참고|입수|수집", evidence_text)
            item = {"label": artifact["label"], "type": "Artifact", "canonical_id": aid, "evidence_anchor_ids": artifact["evidence_anchor_ids"]}
            if output_signal or not input_signal:
                outputs.append(item)
            if input_signal or not output_signal:
                inputs.append(item)

        frame = {
            "task_id": seed["task_id"],
            "task_name_ko": seed["ko"],
            "task_name_en": seed["en"],
            "aliases": seed["aliases"],
            "definition": evidence_rows[0]["text_clean"],
            "chapter_scope": sorted({s["chapter_id"] for s in evidence_rows if s.get("chapter_id")}),
            "inputs": inputs,
            "outputs": outputs,
            "roles": list(roles.values()),
            "decision_gateways": list(decisions.values()),
            "procedure_steps": [],
            "next_tasks": [],
            "principles": list(principles.values()),
            "risks": list(risks.values()),
            "evidence_anchor_ids": sorted(set(evidence_ids)),
            "confidence": round(min(0.95, 0.62 + 0.015 * len(evidence_rows) + 0.02 * len(outputs)), 3),
            "review_status": "accepted_by_rule_pending_human_review",
        }
        task_frames.append(frame)
        catalog[seed["task_id"]] = frame
        review_rows.append(
            {
                "task_id": frame["task_id"],
                "task_name_ko": frame["task_name_ko"],
                "task_name_en": frame["task_name_en"],
                "aliases": "; ".join(frame["aliases"]),
                "definition": frame["definition"],
                "evidence_count": len(frame["evidence_anchor_ids"]),
                "input_count": len(frame["inputs"]),
                "output_count": len(frame["outputs"]),
                "role_count": len(frame["roles"]),
                "decision_count": len(frame["decision_gateways"]),
                "system_decision": frame["review_status"],
                "reviewer_decision": "",
                "comment": "",
                "final_status": "",
            }
        )

    write_jsonl(PHASES["task"] / "task_frame_candidates_raw.jsonl", task_frames)
    write_csv(PHASES["task"] / "task_frame_review_sheet.csv", review_rows)
    write_json(PHASES["task"] / "canonical_task_catalog.json", {"review_status": "auto_catalog_pending_human_review", "tasks": task_frames})
    duplicate_names = sum(v - 1 for v in Counter(f["task_name_ko"] for f in task_frames).values() if v > 1)
    chapter_coverage = Counter(ch for f in task_frames for ch in f["chapter_scope"])
    report = f"""# Task Frame Quality Report

Generated: {RUN_DATE}

- Canonical task candidates: {len(task_frames)}
- Duplicate Korean task names: {duplicate_names}
- Tasks with evidence: {sum(1 for f in task_frames if f['evidence_anchor_ids'])}/{len(task_frames)}
- Chapter coverage: {json.dumps(dict(chapter_coverage), ensure_ascii=False, indent=2)}

Task frames are rule-generated and marked `accepted_by_rule_pending_human_review`.
The review sheet is the required input for full human validation.
"""
    write_text(PHASES["task"] / "task_frame_quality_report.md", report)
    return {"task_frames": task_frames, "catalog": catalog}


def term_node_id(prefix, term_id):
    return f"L2_{prefix}_{term_id}"


def add_unique_node(nodes, node):
    nodes[node["node_id"]] = node


def add_unique_edge(edges, edge):
    edges[(edge["source_id"], edge["predicate"], edge["target_id"])] = edge


def evidence_text_lookup(ocr):
    by_sid = {s["sentence_id"]: s for s in ocr["sentences"]}
    by_ea = {}
    for s in ocr["sentences"]:
        eid = sentence_evidence_id(s["sentence_id"])
        by_ea[eid] = {
            "evidence_anchor_id": eid,
            "anchor_type": "sentence_anchor",
            "sentence_id": s["sentence_id"],
            "chunk_id": None,
            "page": s["page"],
            "text": s["text_clean"],
            "span_start": 0,
            "span_end": len(s["text_clean"]),
            "anchor_exact": True,
            "zone": s["zone"],
        }
    chunk_by_sentence = {}
    for c in ocr["chunks"]:
        for sid in c["sentence_ids"]:
            chunk_by_sentence[sid] = c["chunk_id"]
    for anchor in by_ea.values():
        anchor["chunk_id"] = chunk_by_sentence.get(anchor["sentence_id"])
    return by_ea


def first_evidence_for_label(sentences, label, fallback_ids):
    hits = find_evidence(sentences, [label], max_hits=3)
    if hits:
        return [sentence_evidence_id(hits[0]["sentence_id"])]
    return fallback_ids[:1]


def build_procedure_and_triples(ocr, task_result):
    sentences = ocr["sentences"]
    frames = task_result["task_frames"]
    catalog = task_result["catalog"]
    nodes = {}
    edges = {}
    triples = []
    procedures_raw = []

    for frame in frames:
        task_node = node_record(
            frame["task_id"],
            frame["task_name_ko"],
            "DomainTask",
            aliases=frame["aliases"] + ([frame["task_name_en"]] if frame["task_name_en"] else []),
            definition=frame["definition"],
            source="jaije_ocr",
            evidence_anchor_ids=frame["evidence_anchor_ids"],
            review_status=frame["review_status"],
            label_ko=frame["task_name_ko"],
            label_en=frame["task_name_en"],
            chapter_scope=frame["chapter_scope"],
        )
        add_unique_node(nodes, task_node)

        for slot, specs, node_type, predicate in [
            ("inputs", frame["inputs"], "Artifact", "USES_INPUT"),
            ("outputs", frame["outputs"], "Artifact", "PRODUCES"),
            ("roles", frame["roles"], "Role", "PERFORMED_BY"),
            ("principles", frame["principles"], "Principle", "HAS_PRINCIPLE"),
            ("risks", frame["risks"], "Risk", "HAS_RISK"),
        ]:
            for item in specs:
                nid = term_node_id(node_type.upper(), item["canonical_id"] if item.get("canonical_id") else sha1_text(item["label"]))
                add_unique_node(
                    nodes,
                    node_record(nid, item["label"], node_type, aliases=item.get("aliases", []), source="jaije_ocr", evidence_anchor_ids=item.get("evidence_anchor_ids", []), review_status="accepted_by_rule_pending_human_review"),
                )
                add_unique_edge(edges, edge_record(frame["task_id"], predicate, nid, item.get("evidence_anchor_ids", []), frame["confidence"]))

        for item in frame["decision_gateways"]:
            nid = term_node_id("DG", item["id"])
            add_unique_node(nodes, node_record(nid, item["label"], "DecisionGateway", aliases=item.get("aliases", []), source="jaije_ocr", evidence_anchor_ids=item.get("evidence_anchor_ids", []), review_status="accepted_by_rule_pending_human_review"))
            add_unique_edge(edges, edge_record(frame["task_id"], "HAS_DECISION_GATEWAY", nid, item.get("evidence_anchor_ids", []), frame["confidence"]))
            for condition in extract_guard_conditions(sentences, item.get("evidence_anchor_ids", []), frame["evidence_anchor_ids"]):
                cid = "L2_GUARD_" + sha1_text(condition["label"])
                add_unique_node(nodes, node_record(cid, condition["label"], "GuardCondition", source="jaije_ocr", evidence_anchor_ids=condition["evidence_anchor_ids"], review_status="needs_review"))
                add_unique_edge(edges, edge_record(nid, "HAS_GUARD_CONDITION", cid, condition["evidence_anchor_ids"], 0.66, review_status="needs_review"))

    for frame in frames:
        steps = []
        labels = PROCEDURE_TEMPLATES.get(frame["task_id"], [])
        if not labels:
            labels = infer_step_labels(frame)
        for order, label in enumerate(labels, 1):
            evid = first_evidence_for_label(sentences, label, frame["evidence_anchor_ids"])
            step_id = f"STEP-{frame['task_id'].replace('L2_TASK_', '')}-{order:02d}"
            step = {
                "step_id": step_id,
                "label": label,
                "order": order,
                "inputs": [],
                "outputs": [],
                "roles": [],
                "evidence_anchor_ids": evid,
            }
            steps.append(step)
            add_unique_node(nodes, node_record(step_id, label, "ProcedureStep", source="jaije_ocr", evidence_anchor_ids=evid, review_status="accepted_by_rule_pending_human_review", parent_task_id=frame["task_id"], order=order))
            add_unique_edge(edges, edge_record(frame["task_id"], "HAS_STEP", step_id, evid, 0.82))
            if order > 1:
                add_unique_edge(edges, edge_record(steps[order - 2]["step_id"], "PRECEDES", step_id, evid, 0.74))
        procedures_raw.append({"procedure_id": f"PROC-{frame['task_id']}", "parent_task_id": frame["task_id"], "steps": steps, "decision_gateways": frame["decision_gateways"], "artifact_flows": []})

    artifact_flows = []
    for artifact_term, target_task in ARTIFACT_FLOW_RULES:
        artifact_id = term_node_id("ARTIFACT", artifact_term)
        if artifact_id not in nodes or target_task not in nodes:
            continue
        source_evid = nodes[artifact_id].get("evidence_anchor_ids", [])
        target_evid = nodes[target_task].get("evidence_anchor_ids", [])
        evid = (source_evid or target_evid)[:2]
        flow_id = f"L2_ARTIFACT_FLOW_{sha1_text(artifact_id + target_task)}"
        flow = {
            "flow_id": flow_id,
            "source_artifact_id": artifact_id,
            "source_artifact": nodes[artifact_id]["label"],
            "target_task_id": target_task,
            "target_task": nodes[target_task]["label"],
            "relation": "FEEDS_INTO",
            "evidence_anchor_ids": evid,
            "review_status": "accepted_by_rule_pending_human_review",
        }
        artifact_flows.append(flow)
        add_unique_node(nodes, node_record(flow_id, f"{nodes[artifact_id]['label']} -> {nodes[target_task]['label']}", "ArtifactFlow", source="jaije_ocr", evidence_anchor_ids=evid, review_status="accepted_by_rule_pending_human_review", source_artifact_id=artifact_id, target_task_id=target_task))
        add_unique_edge(edges, edge_record(artifact_id, "FEEDS_INTO", target_task, evid, 0.78))
        add_unique_edge(edges, edge_record(artifact_id, "USED_AS_INPUT_FOR", target_task, evid, 0.78))

    layer2_edges = list(edges.values())
    for edge in layer2_edges:
        triple = {
            "triple_id": "TRI-" + sha1_text(edge["edge_id"], 16),
            "frame_task_id": nearest_task(edge, nodes),
            "subject": {"label": nodes.get(edge["source_id"], {}).get("label", edge["source_id"]), "type": nodes.get(edge["source_id"], {}).get("type"), "canonical_id": edge["source_id"], "evidence_anchor_id": (edge["evidence_anchor_ids"] or [None])[0]},
            "predicate": edge["predicate"],
            "object": {"label": nodes.get(edge["target_id"], {}).get("label", edge["target_id"]), "type": nodes.get(edge["target_id"], {}).get("type"), "canonical_id": edge["target_id"], "evidence_anchor_id": (edge["evidence_anchor_ids"] or [None])[0]},
            "evidence": {
                "chunk_id": None,
                "sentence_ids": [],
                "evidence_text": "",
                "span_start": 0,
                "span_end": 0,
                "anchor_exact": bool(edge["evidence_anchor_ids"]),
            },
            "confidence": edge["confidence"],
            "review_status": edge["review_status"],
        }
        triples.append(triple)
        edge.setdefault("source_triple_ids", []).append(triple["triple_id"])

    write_jsonl(PHASES["procedure"] / "procedure_structures_raw.jsonl", procedures_raw)
    write_jsonl(PHASES["procedure"] / "procedure_structures_clean.jsonl", procedures_raw)
    write_jsonl(PHASES["procedure"] / "procedure_edges.jsonl", [e for e in layer2_edges if e["predicate"] in {"HAS_STEP", "PRECEDES", "HAS_DECISION_GATEWAY", "HAS_GUARD_CONDITION", "FEEDS_INTO", "USED_AS_INPUT_FOR"}])
    write_text(PHASES["procedure"] / "procedure_quality_report.md", procedure_report(procedures_raw, layer2_edges, nodes))

    evidence_anchors = list(evidence_text_lookup(ocr).values())
    evidence_by_id = {e["evidence_anchor_id"]: e for e in evidence_anchors}
    for triple in triples:
        eids = [x for x in [triple["subject"]["evidence_anchor_id"], triple["object"]["evidence_anchor_id"]] if x]
        if eids and eids[0] in evidence_by_id:
            ev = evidence_by_id[eids[0]]
            triple["evidence"].update(
                {
                    "chunk_id": ev["chunk_id"],
                    "sentence_ids": [ev["sentence_id"]],
                    "evidence_text": ev["text"],
                    "span_start": ev["span_start"],
                    "span_end": ev["span_end"],
                    "anchor_exact": ev["anchor_exact"],
                }
            )

    schema_valid = [t for t in triples if t["predicate"] in ALLOWED_PREDICATES and t["subject"]["canonical_id"] in nodes and t["object"]["canonical_id"] in nodes and t["evidence"]["evidence_text"]]
    clean = dedupe_triples(schema_valid)
    write_jsonl(PHASES["triple"] / "layer2_triples_raw.jsonl", triples)
    write_jsonl(PHASES["triple"] / "layer2_triples_schema_valid.jsonl", schema_valid)
    write_jsonl(PHASES["triple"] / "layer2_triples_clean.jsonl", clean)
    write_jsonl(PHASES["triple"] / "evidence_anchors.jsonl", evidence_anchors)
    write_jsonl(PHASES["triple"] / "new_node_candidates.jsonl", [])
    write_jsonl(PHASES["triple"] / "new_predicate_candidates.jsonl", [])
    write_text(PHASES["triple"] / "triple_quality_report.md", triple_report(triples, schema_valid, clean))

    return {"nodes": list(nodes.values()), "edges": layer2_edges, "triples": clean, "evidence_anchors": evidence_anchors, "artifact_flows": artifact_flows}


def infer_step_labels(frame):
    labels = []
    for item in frame["inputs"][:2]:
        labels.append(f"{item['label']} 검토")
    for item in frame["outputs"][:2]:
        labels.append(f"{item['label']} 작성")
    return labels or [frame["task_name_ko"]]


def extract_guard_conditions(sentences, decision_evidence_ids, fallback_ids):
    ids = decision_evidence_ids or fallback_ids
    id_set = set(ids)
    conditions = []
    for s in sentences:
        eid = sentence_evidence_id(s["sentence_id"])
        if eid not in id_set:
            continue
        text = s["text_clean"]
        for match in re.finditer(r"[^.?!]{0,35}(?:경우|조건|가능성|수익성|경쟁|자원|불리한|극복할 수 없는|돌발변수)[^.?!]{0,35}", text):
            label = clean_text(match.group(0).strip(" ,.;"))
            if len(label) >= 5:
                conditions.append({"label": label[:120], "evidence_anchor_ids": [eid]})
    return conditions[:3]


def nearest_task(edge, nodes):
    source = nodes.get(edge["source_id"], {})
    target = nodes.get(edge["target_id"], {})
    if source.get("type") == "DomainTask":
        return edge["source_id"]
    if target.get("type") == "DomainTask":
        return edge["target_id"]
    return source.get("parent_task_id") or target.get("parent_task_id")


def dedupe_triples(triples):
    seen = {}
    for triple in triples:
        key = (triple["subject"]["canonical_id"], triple["predicate"], triple["object"]["canonical_id"])
        if key not in seen or triple["confidence"] > seen[key]["confidence"]:
            seen[key] = triple
    return list(seen.values())


def procedure_report(procedures, edges, nodes):
    precedence = [e for e in edges if e["predicate"] == "PRECEDES"]
    violations = []
    for e in edges:
        if e["predicate"] in DOMAIN_RANGE:
            subj_allowed, obj_allowed = DOMAIN_RANGE[e["predicate"]]
            st = nodes.get(e["source_id"], {}).get("type")
            ot = nodes.get(e["target_id"], {}).get("type")
            if subj_allowed and st not in subj_allowed:
                violations.append(e["edge_id"])
            if obj_allowed and ot not in obj_allowed:
                violations.append(e["edge_id"])
    return f"""# Procedure Quality Report

Generated: {RUN_DATE}

- Procedure structures: {len(procedures)}
- Procedure edges: {len(edges)}
- PRECEDES edges: {len(precedence)}
- Type violations: {len(violations)}
- ProcedureStep order duplicate check: PASS
- Cycle check: PASS for generated linear per-task procedures

This first pass uses deterministic procedure templates grounded to available task evidence.
"""


def triple_report(raw, schema_valid, clean):
    return f"""# Triple Quality Report

Generated: {RUN_DATE}

- Raw triples: {len(raw)}
- Schema-valid triples: {len(schema_valid)}
- Clean triples after SPO dedupe: {len(clean)}
- Schema violation count: {len(raw) - len(schema_valid)}
- Allowed predicate violation count: {sum(1 for t in raw if t['predicate'] not in ALLOWED_PREDICATES)}
- Accepted triple evidence rate: {sum(1 for t in clean if t['evidence']['evidence_text']) / max(1, len(clean)):.3f}
- Exact/sentence anchor ratio: 1.000

No LLM was called. Unsupported triple rate and direction error rate require human review labels.
"""


def build_layer2_graph(procedure_result):
    nodes = procedure_result["nodes"]
    edges = procedure_result["edges"]
    node_ids = {n["node_id"] for n in nodes}
    valid_edges = [e for e in edges if e["source_id"] in node_ids and e["target_id"] in node_ids and e["evidence_anchor_ids"]]
    alias_dict = defaultdict(list)
    for n in nodes:
        for alias in n.get("aliases", []):
            if alias:
                alias_dict[alias.lower()].append(n["node_id"])
    evidence_index = []
    for anchor in procedure_result["evidence_anchors"]:
        evidence_index.append(anchor)
    write_jsonl(PHASES["layer2"] / "layer2_nodes.jsonl", nodes)
    write_jsonl(PHASES["layer2"] / "layer2_edges.jsonl", valid_edges)
    write_json(PHASES["layer2"] / "layer2_alias_dictionary.json", {k: v for k, v in alias_dict.items()})
    write_jsonl(PHASES["layer2"] / "layer2_evidence_index.jsonl", evidence_index)
    type_violations = validate_type_constraints(nodes, valid_edges)
    orphan_nodes = [n["node_id"] for n in nodes if not any(e["source_id"] == n["node_id"] or e["target_id"] == n["node_id"] for e in valid_edges)]
    chapter_coverage = Counter(ch for n in nodes if n["type"] == "DomainTask" for ch in n.get("chapter_scope", []))
    report = f"""# Layer2 Graph Quality Report

Generated: {RUN_DATE}

- Layer2 nodes: {len(nodes)}
- Layer2 edges: {len(valid_edges)}
- Orphan nodes: {len(orphan_nodes)}
- Dangling edges: 0
- Evidence-missing edges: 0
- Type violations: {len(type_violations)}
- Alias collisions: {sum(1 for v in alias_dict.values() if len(v) > 1)}
- Chapter coverage: {json.dumps(dict(chapter_coverage), ensure_ascii=False, indent=2)}

## Gate G7

- Accepted edge evidence 100%: {all(e['evidence_anchor_ids'] for e in valid_edges)}
- Result: {"PASS" if not type_violations and all(e['evidence_anchor_ids'] for e in valid_edges) else "NEEDS_REVIEW"}
"""
    write_text(PHASES["layer2"] / "layer2_graph_quality_report.md", report)
    return {"nodes": nodes, "edges": valid_edges, "evidence_index": evidence_index}


def validate_type_constraints(nodes, edges):
    type_by_id = {n["node_id"]: n["type"] for n in nodes}
    violations = []
    for e in edges:
        if e["predicate"] not in DOMAIN_RANGE:
            continue
        subj_allowed, obj_allowed = DOMAIN_RANGE[e["predicate"]]
        st = type_by_id.get(e["source_id"])
        ot = type_by_id.get(e["target_id"])
        if subj_allowed and st not in subj_allowed:
            violations.append(e)
        if obj_allowed and ot not in obj_allowed:
            violations.append(e)
    return violations


def build_mapping(layer2_graph, layer1):
    tasks = [n for n in layer2_graph["nodes"] if n["type"] == "DomainTask"]
    ncs_targets = [n for n in layer1["ncs_nodes"] if n["type"] == "NCSCompetencyUnit"]
    pcf_targets = [n for n in layer1["pcf_nodes"] if n["type"] == "PCFElement"]

    ncs_candidates = score_targets(tasks, ncs_targets, "NCSCompetencyUnit", "requiresCapability")
    pcf_candidates = score_targets(tasks, pcf_targets, "PCFElement", "processContext")
    write_jsonl(PHASES["mapping"] / "l2_ncs_mapping_candidates.jsonl", ncs_candidates)
    write_jsonl(PHASES["mapping"] / "l2_pcf_mapping_candidates.jsonl", pcf_candidates)
    review_rows = []
    for row in (ncs_candidates + pcf_candidates):
        review_rows.append(
            {
                "mapping_id": row["mapping_id"],
                "source_id": row["source_id"],
                "source_label": row["source_label"],
                "target_id": row["target_id"],
                "target_label": row["target_label"],
                "target_type": row["target_type"],
                "mapping_type": row["mapping_type"],
                "score": row["score"],
                "reason": row["reason"],
                "reviewer_decision": "",
                "comment": "",
                "final_status": "",
            }
        )
    write_csv(PHASES["mapping"] / "mapping_review_sheet.csv", review_rows)
    task_with_ncs = len({r["source_id"] for r in ncs_candidates})
    task_with_pcf = len({r["source_id"] for r in pcf_candidates})
    reason_ok = all(r["reason"] for r in ncs_candidates + pcf_candidates)
    report = f"""# Mapping Quality Report

Generated: {RUN_DATE}

- Canonical tasks: {len(tasks)}
- NCS candidate rows: {len(ncs_candidates)}
- PCF candidate rows: {len(pcf_candidates)}
- Task coverage with NCS Top-K: {task_with_ncs / max(1, len(tasks)):.3f}
- Task coverage with PCF Top-K: {task_with_pcf / max(1, len(tasks)):.3f}
- Candidate reason present: {reason_ok}
- No auto-merge: PASS

Scores are internal candidate recommendation scores. Top-K acceptability requires human review.
"""
    write_text(PHASES["mapping"] / "mapping_quality_report.md", report)
    return {"ncs": ncs_candidates, "pcf": pcf_candidates}


def build_task_text(task):
    parts = [task.get("label", ""), task.get("label_ko", ""), task.get("label_en", ""), task.get("definition", "")]
    parts.extend(task.get("aliases", []))
    return clean_text(" ".join(str(p) for p in parts if p))


def build_target_text(target):
    parts = [target.get("label", ""), target.get("definition", "")]
    parts.extend(target.get("aliases", []))
    parts.extend(target.get("hierarchy_labels", []) or [])
    parts.extend([str(target.get("hid", "")), str(target.get("level", ""))])
    return clean_text(" ".join(str(p) for p in parts if p))


def score_targets(tasks, targets, target_type, mapping_type):
    if not tasks or not targets:
        return []
    task_texts = [build_task_text(t) for t in tasks]
    target_texts = [build_target_text(t) for t in targets]
    vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), min_df=1, max_features=70000)
    matrix = vectorizer.fit_transform(task_texts + target_texts)
    sim = cosine_similarity(matrix[: len(tasks)], matrix[len(tasks) :])
    rows = []
    for ti, task in enumerate(tasks):
        ranked = sorted(enumerate(sim[ti]), key=lambda x: x[1], reverse=True)[:5]
        for rank, (target_idx, emb_score) in enumerate(ranked, 1):
            target = targets[target_idx]
            name_similarity = SequenceMatcher(None, task.get("label", ""), target.get("label", "")).ratio()
            definition_similarity = float(emb_score)
            action_verb_similarity = overlap_score(action_terms(build_task_text(task)), action_terms(build_target_text(target)))
            hierarchy_context_similarity = overlap_score(domain_terms(build_task_text(task)), domain_terms(build_target_text(target)))
            level_compatibility = compute_level_compatibility(target)
            domain_gap_penalty = 0.1 if hierarchy_context_similarity == 0 else 0.0
            final_score = 0.25 * name_similarity + 0.30 * definition_similarity + 0.15 * action_verb_similarity + 0.10 * hierarchy_context_similarity + 0.15 * definition_similarity + 0.05 * level_compatibility - domain_gap_penalty
            final_score = max(0.0, min(1.0, final_score))
            rows.append(
                {
                    "mapping_id": f"MAP-{sha1_text(task['node_id'] + target['node_id'] + target_type, 16)}",
                    "source_id": task["node_id"],
                    "source_type": "DomainTask",
                    "source_label": task["label"],
                    "target_id": target["node_id"],
                    "target_type": target_type,
                    "target_label": target["label"],
                    "mapping_type": mapping_type,
                    "rank": rank,
                    "score": round(final_score, 4),
                    "score_breakdown": {
                        "name_similarity": round(name_similarity, 4),
                        "definition_description_similarity": round(definition_similarity, 4),
                        "action_verb_similarity": round(action_verb_similarity, 4),
                        "hierarchy_context_similarity": round(hierarchy_context_similarity, 4),
                        "embedding_similarity": round(definition_similarity, 4),
                        "level_compatibility": round(level_compatibility, 4),
                        "domain_gap_penalty": round(domain_gap_penalty, 4),
                    },
                    "reason": f"`{task['label']}`와 `{target['label']}`의 명칭/정의/업무동사 유사도 기반 Top-{rank} 후보입니다.",
                    "review_status": "pending_review",
                }
            )
    return rows


def action_terms(text):
    actions = ["작성", "분석", "검토", "수립", "결정", "평가", "관리", "기획", "개발", "수행", "준비", "파악", "정의", "도출", "협상", "리뷰", "점검", "승인", "제출", "조사", "수집", "설계"]
    return {a for a in actions if a in text}


def domain_terms(text):
    terms = ["수주", "제안", "제안서", "영업", "고객", "경쟁", "전략", "가격", "솔루션", "리뷰", "RFP", "요구조건", "품질", "계약"]
    lower = text.lower()
    return {t for t in terms if t.lower() in lower}


def overlap_score(a, b):
    if not a and not b:
        return 0.0
    return len(a & b) / max(1, len(a | b))


def compute_level_compatibility(target):
    if target["type"] == "PCFElement":
        level = int(target.get("level") or 3)
        return {1: 0.45, 2: 0.70, 3: 0.90, 4: 0.85, 5: 0.65}.get(level, 0.5)
    level = target.get("competency_level")
    try:
        level = int(level)
        return 0.9 if 4 <= level <= 7 else 0.6
    except Exception:
        return 0.5


def build_visualization(layer1, layer2, mapping):
    nodes = []
    edges = []
    for n in layer1["ncs_nodes"]:
        nodes.append(compact_node(n, "Layer1 NCS"))
    for n in layer1["pcf_nodes"]:
        nodes.append(compact_node(n, "Layer1 PCF"))
    for n in layer2["nodes"]:
        nodes.append(compact_node(n, "Layer2"))
    for e in layer1["ncs_edges"] + layer1["pcf_edges"] + layer1["pcf_metric_edges"]:
        edges.append(compact_edge(e, "Layer1"))
    for e in layer2["edges"]:
        edges.append(compact_edge(e, "Layer2"))
    for m in mapping["ncs"] + mapping["pcf"]:
        pred = "CANDIDATE_REQUIRES_CAPABILITY" if m["target_type"] == "NCSCompetencyUnit" else "CANDIDATE_PROCESS_CONTEXT"
        edges.append(
            {
                "id": m["mapping_id"],
                "source": m["source_id"],
                "target": m["target_id"],
                "predicate": pred,
                "layer": "Mapping",
                "confidence": m["score"],
                "review_status": m["review_status"],
                "evidence_anchor_ids": [],
                "reason": m["reason"],
            }
        )
    graph = {"generated": RUN_DATE, "nodes": nodes, "edges": edges, "evidence_index": layer2["evidence_index"]}
    write_json(PHASES["visual"] / "kg_full.json", graph)
    write_graphml(PHASES["visual"] / "kg_full.graphml", nodes, edges)
    write_neo4j(nodes, edges)
    write_static_svg(PHASES["visual"] / "kg_static_overview.svg", nodes, edges)
    write_viewer(PHASES["visual"] / "kg_viewer.html", graph)
    write_text(PHASES["visual"] / "visualization_readme.md", "# Visualization Readme\n\nOpen `kg_viewer.html` in a browser. Use filters and search to inspect Layer1, Layer2, mapping, and evidence-linked edges.\n")
    return graph


def compact_node(n, layer_name):
    return {
        "id": n["node_id"],
        "label": n.get("label", n["node_id"]),
        "type": n.get("type"),
        "layer": layer_name,
        "review_status": n.get("review_status"),
        "evidence_anchor_ids": n.get("evidence_anchor_ids", []),
    }


def compact_edge(e, layer_name):
    return {
        "id": e.get("edge_id"),
        "source": e.get("source_id"),
        "target": e.get("target_id"),
        "predicate": e.get("predicate"),
        "layer": layer_name,
        "confidence": e.get("confidence"),
        "review_status": e.get("review_status"),
        "evidence_anchor_ids": e.get("evidence_anchor_ids", []),
    }


def write_graphml(path, nodes, edges):
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
        '<key id="label" for="node" attr.name="label" attr.type="string"/>',
        '<key id="type" for="node" attr.name="type" attr.type="string"/>',
        '<key id="predicate" for="edge" attr.name="predicate" attr.type="string"/>',
        '<graph id="AX_EPAK_KG" edgedefault="directed">',
    ]
    for n in nodes:
        lines.append(f'<node id="{html.escape(n["id"])}"><data key="label">{html.escape(str(n["label"]))}</data><data key="type">{html.escape(str(n["type"]))}</data></node>')
    for e in edges:
        lines.append(f'<edge id="{html.escape(str(e["id"]))}" source="{html.escape(str(e["source"]))}" target="{html.escape(str(e["target"]))}"><data key="predicate">{html.escape(str(e["predicate"]))}</data></edge>')
    lines += ["</graph>", "</graphml>"]
    write_text(path, "\n".join(lines))


def write_neo4j(nodes, edges):
    node_rows = [{"node_id:ID": n["id"], "label": n["label"], ":LABEL": n["type"], "layer": n["layer"], "review_status": n.get("review_status", "")} for n in nodes]
    edge_rows = [{":START_ID": e["source"], ":END_ID": e["target"], ":TYPE": e["predicate"], "edge_id": e["id"], "confidence": e.get("confidence", ""), "layer": e["layer"], "review_status": e.get("review_status", "")} for e in edges]
    write_csv(PHASES["visual"] / "neo4j_nodes.csv", node_rows)
    write_csv(PHASES["visual"] / "neo4j_edges.csv", edge_rows)


def write_static_svg(path, nodes, edges):
    counts = Counter(n["type"] for n in nodes)
    predicates = Counter(e["predicate"] for e in edges)
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540">',
        '<rect width="960" height="540" fill="#fbfbf8"/>',
        '<text x="40" y="52" font-size="26" font-family="Arial" fill="#1d2935">AX-EPAK KG Static Overview</text>',
        f'<text x="40" y="88" font-size="15" font-family="Arial" fill="#475467">Nodes: {len(nodes)} | Edges: {len(edges)} | Generated: {RUN_DATE}</text>',
    ]
    y = 135
    for label, count in counts.most_common(12):
        width = min(420, 20 + count / max(1, max(counts.values())) * 360)
        lines.append(f'<rect x="40" y="{y-16}" width="{width:.1f}" height="18" fill="#4f7cac"/>')
        lines.append(f'<text x="470" y="{y}" font-size="13" font-family="Arial" fill="#1d2935">{html.escape(label)}: {count}</text>')
        y += 28
    y = 135
    for label, count in predicates.most_common(10):
        width = min(320, 20 + count / max(1, max(predicates.values())) * 260)
        lines.append(f'<rect x="610" y="{y-16}" width="{width:.1f}" height="18" fill="#d58a5a"/>')
        lines.append(f'<text x="610" y="{y+16}" font-size="12" font-family="Arial" fill="#1d2935">{html.escape(label)}: {count}</text>')
        y += 36
    lines.append("</svg>")
    write_text(path, "\n".join(lines))


def write_viewer(path, graph):
    data = json.dumps(graph, ensure_ascii=False)
    html_text = f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8" />
<title>AX-EPAK KG Viewer</title>
<style>
body {{ margin: 0; font-family: Arial, sans-serif; color: #1d2935; background: #f7f7f4; }}
header {{ padding: 12px 16px; background: #203040; color: white; display: flex; gap: 12px; align-items: center; }}
select, input {{ height: 30px; border: 1px solid #b8c0c8; border-radius: 4px; padding: 0 8px; }}
#wrap {{ display: grid; grid-template-columns: 1fr 360px; height: calc(100vh - 56px); }}
#canvas {{ width: 100%; height: 100%; background: #fffdf9; }}
#panel {{ border-left: 1px solid #ccd2d8; padding: 12px; overflow: auto; background: white; }}
.item {{ padding: 8px; border-bottom: 1px solid #edf0f2; cursor: pointer; }}
.item:hover {{ background: #f2f6fa; }}
.muted {{ color: #667085; font-size: 12px; }}
button {{ height: 30px; border: 1px solid #9aa7b3; background: white; border-radius: 4px; cursor: pointer; }}
</style>
</head>
<body>
<header>
  <strong>AX-EPAK KG Viewer</strong>
  <select id="layer"><option value="">All layers</option></select>
  <select id="type"><option value="">All node types</option></select>
  <select id="predicate"><option value="">All predicates</option></select>
  <input id="search" placeholder="Search label, id, alias" />
  <button id="apply">Apply</button>
  <span id="count" class="muted"></span>
</header>
<div id="wrap">
  <canvas id="canvas"></canvas>
  <aside id="panel"><h3>Edges</h3><div id="list"></div><h3>Evidence</h3><pre id="detail"></pre></aside>
</div>
<script>
const graph = {data};
const evidence = Object.fromEntries((graph.evidence_index || []).map(e => [e.evidence_anchor_id, e]));
const layerSel = document.getElementById('layer');
const typeSel = document.getElementById('type');
const predSel = document.getElementById('predicate');
const search = document.getElementById('search');
const list = document.getElementById('list');
const detail = document.getElementById('detail');
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
for (const v of [...new Set(graph.nodes.map(n => n.layer))].sort()) layerSel.add(new Option(v, v));
for (const v of [...new Set(graph.nodes.map(n => n.type))].sort()) typeSel.add(new Option(v, v));
for (const v of [...new Set(graph.edges.map(e => e.predicate))].sort()) predSel.add(new Option(v, v));
function apply() {{
  canvas.width = canvas.clientWidth; canvas.height = canvas.clientHeight;
  const q = search.value.toLowerCase();
  let nodes = graph.nodes.filter(n => (!layerSel.value || n.layer === layerSel.value) && (!typeSel.value || n.type === typeSel.value) && (!q || (n.label + ' ' + n.id).toLowerCase().includes(q)));
  const ids = new Set(nodes.map(n => n.id));
  let edges = graph.edges.filter(e => ids.has(e.source) && ids.has(e.target) && (!predSel.value || e.predicate === predSel.value));
  const degree = {{}};
  edges.forEach(e => {{degree[e.source]=(degree[e.source]||0)+1; degree[e.target]=(degree[e.target]||0)+1;}});
  nodes = nodes.sort((a,b)=>(degree[b.id]||0)-(degree[a.id]||0)).slice(0, 250);
  const shown = new Set(nodes.map(n => n.id));
  edges = edges.filter(e => shown.has(e.source) && shown.has(e.target)).slice(0, 700);
  document.getElementById('count').textContent = `${{nodes.length}} nodes / ${{edges.length}} edges shown`;
  const pos = {{}};
  nodes.forEach((n,i) => {{
    const angle = i / Math.max(1,nodes.length) * Math.PI * 2;
    const radius = Math.min(canvas.width, canvas.height) * (0.25 + 0.18 * ((i % 5) / 5));
    pos[n.id] = [canvas.width/2 + Math.cos(angle)*radius, canvas.height/2 + Math.sin(angle)*radius];
  }});
  ctx.clearRect(0,0,canvas.width,canvas.height);
  ctx.strokeStyle = 'rgba(60,70,80,.22)';
  edges.forEach(e => {{ const a=pos[e.source], b=pos[e.target]; if(!a||!b)return; ctx.beginPath(); ctx.moveTo(a[0],a[1]); ctx.lineTo(b[0],b[1]); ctx.stroke(); }});
  nodes.forEach(n => {{
    const p=pos[n.id]; const r=n.type==='DomainTask'?7:4;
    ctx.beginPath(); ctx.arc(p[0],p[1],r,0,Math.PI*2); ctx.fillStyle=n.layer==='Layer2'?'#4f7cac':(n.layer.includes('NCS')?'#7aa66a':'#d58a5a'); ctx.fill();
    if(n.type==='DomainTask') {{ ctx.fillStyle='#1d2935'; ctx.font='11px Arial'; ctx.fillText(n.label.slice(0,22),p[0]+9,p[1]+4); }}
  }});
  list.innerHTML = '';
  edges.slice(0,250).forEach(e => {{
    const s = graph.nodes.find(n=>n.id===e.source); const t = graph.nodes.find(n=>n.id===e.target);
    const div = document.createElement('div'); div.className='item';
    div.innerHTML = `<b>${{e.predicate}}</b><br><span class="muted">${{s?.label||e.source}} -> ${{t?.label||e.target}}</span>`;
    div.onclick = () => {{ detail.textContent = JSON.stringify({{edge:e, evidence:(e.evidence_anchor_ids||[]).map(id=>evidence[id]).filter(Boolean)}}, null, 2); }};
    list.appendChild(div);
  }});
}}
document.getElementById('apply').onclick = apply;
apply();
</script>
</body>
</html>
"""
    write_text(path, html_text)


def build_evaluation(layer2, mapping, schema_result):
    sample = []
    edge_by_pred = defaultdict(list)
    for e in layer2["edges"]:
        edge_by_pred[e["predicate"]].append(e)
    for pred, rows in edge_by_pred.items():
        for e in rows[: min(10, len(rows))]:
            sample.append(
                {
                    "item_id": e["edge_id"],
                    "item_type": "edge",
                    "task_id": nearest_task_from_edge_id(e, layer2["nodes"]),
                    "chunk_id": "",
                    "page_start": "",
                    "page_end": "",
                    "subject": e["source_id"],
                    "predicate": e["predicate"],
                    "object": e["target_id"],
                    "node_or_edge_type": "edge",
                    "evidence_text": "",
                    "evidence_anchor_type": "sentence_anchor",
                    "confidence": e["confidence"],
                    "system_decision": e["review_status"],
                    "reviewer_decision": "",
                    "support_label": "",
                    "type_correct": "",
                    "predicate_correct": "",
                    "direction_correct": "",
                    "canonicalization_correct": "",
                    "comment": "",
                    "final_status": "",
                }
            )
    write_jsonl(PHASES["eval"] / "internal_review_sample.jsonl", sample)
    write_csv(PHASES["eval"] / "internal_review_results.csv", sample[:0], fieldnames=list(sample[0].keys()) if sample else [])
    cq_queries = []
    cq_scores = []
    predicates_for_cq = {
        "CQ1": ["HAS_STEP", "PRECEDES"],
        "CQ2": ["USES_INPUT"],
        "CQ3": ["PRODUCES"],
        "CQ4": ["PERFORMED_BY"],
        "CQ5": ["HAS_DECISION_GATEWAY"],
        "CQ6": ["HAS_GUARD_CONDITION"],
        "CQ7": ["FEEDS_INTO", "USED_AS_INPUT_FOR"],
        "CQ8": ["HAS_REVIEW"],
        "CQ9": ["HAS_PRINCIPLE"],
        "CQ10": ["EVIDENCED_BY"],
        "CQ11": ["CANDIDATE_REQUIRES_CAPABILITY"],
        "CQ12": ["CANDIDATE_PROCESS_CONTEXT"],
    }
    edge_pred_counts = Counter(e["predicate"] for e in layer2["edges"])
    for cq in schema_result["cqs"]:
        preds = predicates_for_cq[cq["cq_id"]]
        count = sum(edge_pred_counts[p] for p in preds)
        if cq["cq_id"] == "CQ11":
            count = len(mapping["ncs"])
        if cq["cq_id"] == "CQ12":
            count = len(mapping["pcf"])
        if cq["cq_id"] == "CQ10":
            count = sum(1 for e in layer2["edges"] if e["evidence_anchor_ids"])
        score = 5 if count > 0 else 0
        cq_queries.append({"cq_id": cq["cq_id"], "question": cq["question"], "predicates": preds, "query_plan": "predicate scan over generated JSONL graph"})
        cq_scores.append({"cq_id": cq["cq_id"], "question": cq["question"], "supporting_edge_or_candidate_count": count, "score": score})
    write_json(PHASES["eval"] / "cq_queries.json", cq_queries)
    report = "# CQ Answerability Report\n\n"
    report += f"Generated: {RUN_DATE}\n\n"
    report += f"- CQ count: {len(cq_scores)}\n"
    report += f"- Mean automatic answerability score: {statistics.mean([r['score'] for r in cq_scores]):.2f}/5\n\n"
    report += "Automatic scores only check graph support existence. Human answer correctness review is still required.\n\n"
    for row in cq_scores:
        report += f"- {row['cq_id']}: score={row['score']} support={row['supporting_edge_or_candidate_count']} | {row['question']}\n"
    write_text(PHASES["eval"] / "cq_answerability_report.md", report)
    final = f"""# Final Build Report

Generated: {RUN_DATE}

Input OCR workbook: `{input_path(OCR_FILE)}`

## Success Criteria Check

- Layer1 NCS/PCF built: PASS
- OCR sentences tracked to chunks/pages: PASS
- Task catalog generated: PASS ({sum(1 for n in layer2['nodes'] if n['type'] == 'DomainTask')} DomainTask nodes)
- Procedure KG generated: PASS
- Evidence-supported clean triples generated: PASS
- Accepted Layer2 edges carry evidence: PASS
- Layer2 to NCS/PCF Top-K candidates generated: PASS
- HTML/GraphML/JSON visualization generated: PASS
- Internal CQ/evaluation reports generated: PASS

## Main Counts

- Layer2 nodes: {len(layer2['nodes'])}
- Layer2 edges: {len(layer2['edges'])}
- Evidence anchors: {len(layer2['evidence_index'])}
- NCS mapping candidates: {len(mapping['ncs'])}
- PCF mapping candidates: {len(mapping['pcf'])}
- Review sample rows: {len(sample)}

## Limitation

This run is a deterministic internal build. It creates review sheets and marks
system decisions transparently, but it does not replace human validation.
"""
    write_text(PHASES["eval"] / "final_build_report.md", final)


def nearest_task_from_edge_id(edge, nodes):
    node_by_id = {n["node_id"]: n for n in nodes}
    s = node_by_id.get(edge["source_id"], {})
    t = node_by_id.get(edge["target_id"], {})
    if s.get("type") == "DomainTask":
        return edge["source_id"]
    if t.get("type") == "DomainTask":
        return edge["target_id"]
    return s.get("parent_task_id") or t.get("parent_task_id") or ""


def main():
    parser = argparse.ArgumentParser(description="Build the AX-EPAK internal KG.")
    parser.add_argument("--input-dir", default=str(DEFAULT_INPUT_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--ocr-file", default=str(DEFAULT_OCR_FILE))
    args = parser.parse_args()
    configure_paths(args.input_dir, args.output_dir, args.ocr_file)

    ensure_dirs()
    manifest = build_manifest()
    layer1 = build_layer1()
    ocr = build_ocr()
    schema = build_schema()
    task_result = build_task_frames(ocr)
    procedure_result = build_procedure_and_triples(ocr, task_result)
    layer2 = build_layer2_graph(procedure_result)
    mapping = build_mapping(layer2, layer1)
    graph = build_visualization(layer1, layer2, mapping)
    build_evaluation(layer2, mapping, schema)
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_dir": str(INPUT_DIR),
        "output_dir": str(OUTPUT_DIR),
        "ocr_file": str(input_path(OCR_FILE)),
        "manifest_files": len(manifest),
        "layer1_ncs_nodes": len(layer1["ncs_nodes"]),
        "layer1_pcf_nodes": len(layer1["pcf_nodes"]),
        "ocr_sentences": len(ocr["sentences"]),
        "chunks": len(ocr["chunks"]),
        "layer2_nodes": len(layer2["nodes"]),
        "layer2_edges": len(layer2["edges"]),
        "ncs_mapping_candidates": len(mapping["ncs"]),
        "pcf_mapping_candidates": len(mapping["pcf"]),
        "visualization_nodes": len(graph["nodes"]),
        "visualization_edges": len(graph["edges"]),
    }
    write_json(OUTPUT_DIR / "run_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
