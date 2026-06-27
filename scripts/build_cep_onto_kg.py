#!/usr/bin/env python3
"""
Build a first-pass CEP-Onto knowledge graph from the local AX-HYU handoff data.

This script intentionally avoids external LLM calls. It implements the
deterministic parts of the experiment plan plus a transparent, rule-based
Layer2 population pass so the user's data can be turned into inspectable KG
artifacts immediately.
"""

import argparse
import csv
import hashlib
import json
import math
import os
import re
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


RUN_DATE = "2026-06-27"
DEFAULT_INPUT = Path("handoff-hanyang")
DEFAULT_OUTPUT = Path("experiments/cep_onto_jaije_20260627")

TASK_ACTIONS = [
    "작성", "분석", "검토", "수립", "결정", "평가", "관리", "기획", "개발", "수행",
    "준비", "파악", "정의", "도출", "협상", "리뷰", "점검", "승인", "제출", "조사",
    "식별", "대응", "개선", "실행", "설계", "구성", "확인", "합의", "공유", "구체화",
    "선정", "입수", "수집", "제시", "검증", "배포", "반영", "비교", "공략",
]

CORE_TASK_ACTIONS = {
    "작성", "분석", "검토", "수립", "결정", "평가", "관리", "기획", "개발", "수행",
    "준비", "파악", "정의", "도출", "협상", "리뷰", "점검", "승인", "제출", "조사",
    "식별", "개선", "실행", "설계", "구성", "확인", "합의", "공유", "구체화",
    "선정", "입수", "수집", "제시", "검증", "배포", "반영", "비교", "공략",
}

DOMAIN_TERMS = [
    "수주", "입찰", "제안", "제안서", "RFP", "RFI", "RFQ", "고객", "경쟁", "영업",
    "전략", "가격", "솔루션", "리뷰", "킥오프", "캡처", "Capture", "Proposal",
    "Bid", "No Bid", "Pursuit", "사업", "계약", "평가", "요구조건", "니즈",
    "주제문", "섹션", "스토리보드", "PMP", "제안계획서", "제안요약", "역할",
    "책임", "일정", "분량", "초안", "요약", "강점", "약점", "기회", "품질",
]

KEYWORDS = {
    "Artifact": [
        "제안서", "제안 요청서", "제안요청서", "RFP", "RFI", "RFQ", "Capture Plan",
        "캡처플랜", "제안계획서", "PMP", "Proposal Management Plan", "전략기술서",
        "섹션기획서", "스토리보드", "Storyboard", "PDW", "제안요약", "Executive Summary",
        "주제문", "체크리스트", "충실도 체크리스트", "목차", "WBS", "가격제안서",
        "견적서", "계약서", "입찰공고", "문서", "계획서", "발표자료", "프로젝트 조직도",
        "고객미팅 플래너", "제안관리 계획", "제안전략", "수주전략", "성공스토리",
    ],
    "Role": [
        "제안 PM", "PM", "Proposal Manager", "Capture Manager", "영업대표", "영업팀",
        "제안팀", "작성자", "리뷰팀", "고객", "평가자", "평가위원", "의사결정자",
        "영향자", "경쟁사", "담당자", "Core Team", "섹션 리더", "PL", "임원",
        "수행 PM", "프로젝트팀", "발주처", "구매자",
    ],
    "DecisionGateway": [
        "Bid/No Bid", "Bid / No Bid", "Bid Decision", "No Bid", "Pursuit Decision",
        "입찰타당성 결정", "참여결정", "참여 결정", "영업참여 결정", "의사결정",
        "최종 의사결정", "승인", "결정", "검증", "타당성", "입찰 참여",
    ],
    "Principle": [
        "고객 중심", "고객의 니즈", "일관성", "차별화", "투명성", "명확", "충실도",
        "근거", "논리", "설득", "강점", "가치", "Benefit", "Benefits", "전문성",
        "정확", "간결", "품질", "표준화", "전략적 초점",
    ],
    "Metric": [
        "일정", "비용", "가격", "예산", "승률", "점수", "평가점수", "리스크", "위험",
        "계약 규모", "기간", "원가", "목표 가격", "고객 점수",
    ],
    "Risk": [
        "리스크", "위험", "불리한", "극복할 수 없는", "약점", "실패", "부담", "오류",
        "누락", "이슈", "문제", "편견", "돌발변수", "위기", "No bid",
    ],
    "ReviewEvent": [
        "리뷰", "핑크팀", "레드팀", "블루팀", "골드팀", "검토회의", "평가회의",
        "킥오프 미팅", "미팅", "회의", "검수", "점검",
    ],
}

PREDICATE_REGISTRY = {
    "HAS_SUBTASK": ("DomainTask", "ProcedureStep"),
    "PRECEDES": ("ProcedureStep", "ProcedureStep"),
    "USES_INPUT": ("DomainTask", "Artifact"),
    "PRODUCES": ("DomainTask", "Artifact"),
    "PERFORMED_BY": ("ProcedureStep", "Role"),
    "RESPONSIBLE_FOR": ("Role", "DomainTask"),
    "HAS_DECISION_GATEWAY": ("DomainTask", "DecisionGateway"),
    "HAS_GUARD_CONDITION": ("*", "GuardCondition"),
    "BRANCHES_TO": ("DecisionGateway", "ProcedureStep"),
    "HAS_REVIEW": ("DomainTask", "ReviewEvent"),
    "HAS_PRINCIPLE": ("DomainTask", "Principle"),
    "HAS_RISK": ("DomainTask", "Risk"),
    "TRANSFORMS_INTO": ("Artifact", "Artifact"),
    "EVIDENCED_BY": ("*", "EvidenceAnchor"),
    "ANCHOR_OF": ("EvidenceAnchor", "*"),
    "ALIAS_OF": ("*", "*"),
    "CANDIDATE_ALIGNS_WITH": ("DomainTask", "StandardAnchor"),
    "REQUIRES_CAPABILITY": ("DomainTask", "StandardAnchor"),
    "PROCESS_CONTEXT": ("DomainTask", "StandardAnchor"),
    "CONFLICTS_WITH": ("*", "*"),
    "BROADER": ("*", "*"),
    "HAS_METRIC": ("StandardAnchor", "StandardAnchor"),
}


def sha1_text(text, size=12):
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:size]


def stable_id(prefix, *parts):
    body = "|".join("" if p is None else str(p) for p in parts)
    return f"{prefix}:{sha1_text(body)}"


def to_builtin(value):
    if isinstance(value, dict):
        return {str(k): to_builtin(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_builtin(v) for v in value]
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


def read_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(to_builtin(data), f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(to_builtin(row), ensure_ascii=False, sort_keys=True))
            f.write("\n")


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write(text)


def write_csv(path, rows, fieldnames=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    if fieldnames is None:
        keys = []
        for row in rows:
            for key in row.keys():
                if key not in keys:
                    keys.append(key)
        fieldnames = keys
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: to_builtin(row.get(k)) for k in fieldnames})


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


def normalize_label(label):
    label = clean_text(label)
    label = label.strip(" \t\r\n-:;,.·•")
    label = re.sub(r"^[0-9]+(?:\.[0-9]+)*\s*", "", label)
    label = re.sub(r"\bChapter\s*[0-9]+\.?\s*", "", label, flags=re.I)
    label = re.sub(r"^(첫째|둘째|셋째|넷째|그리고|또한|즉|따라서|하지만|그러나)\s*(은|는|,)?\s*", "", label)
    label = re.sub(r"^(은|는|이|가|을|를|의|및)\s+", "", label)
    label = re.sub(r"\s+", " ", label)
    label = re.sub(r"(을|를|이|가|은|는|의|에|에서|으로|로|와|과|및)$", "", label)
    label = re.sub(r"(한다|하다|하는|하기|하여|하고|된다|되는|되며)$", "", label)
    label = label.strip(" \t\r\n-:;,.·•")
    return label[:80]


def contains_domain_term(text):
    lowered = text.lower()
    return any(term.lower() in lowered for term in DOMAIN_TERMS)


def source_manifest(input_dir):
    specs = [
        ("01_ncs/ncs_lclas.json", "NCS 대분류", "Layer1 NCS hierarchy"),
        ("01_ncs/ncs_mclas.json", "NCS 중분류", "Layer1 NCS hierarchy"),
        ("01_ncs/ncs_sclas.json", "NCS 소분류", "Layer1 NCS hierarchy"),
        ("01_ncs/ncs_dclas.json", "NCS 세분류", "Layer1 NCS hierarchy"),
        ("01_ncs/ncs_unit.json", "NCS 능력단위", "Layer1 NCS competency units"),
        ("02_pcf/pcf_data.json", "PCF element", "Layer1 PCF process axis"),
        ("02_pcf/pcf_metrics.json", "PCF metrics", "Optional metric nodes"),
        ("06_suju_focus/ncs_suju_units.json", "수주 NCS 선별본", "Standard triangulation focus set"),
        ("06_suju_focus/pcf_3.0_market_and_sell.json", "PCF 3.0 선별본", "Standard triangulation focus set"),
        ("자이제_ocr_sentences.xlsx", "자이제 OCR sentence", "Layer2 source corpus"),
    ]
    rows = []
    for rel, name, role in specs:
        path = input_dir / rel
        records = None
        if path.suffix == ".json":
            data = read_json(path)
            records = len(data)
        elif path.suffix == ".xlsx":
            records = len(pd.read_excel(path))
        rows.append(
            {
                "path": str(path),
                "name": name,
                "role": role,
                "records": records,
                "size_bytes": path.stat().st_size,
                "sha256": file_sha256(path),
            }
        )
    return rows


def current_use(rows):
    return [
        r
        for r in rows
        if str(r.get("NCS_DEGR")) == "29" and str(r.get("USG_YN", "")).upper() == "Y"
    ]


def ncs_class_node(row, level):
    if level == "L":
        code = row["NCS_LCLAS_CD"]
        label = row["NCS_LCLAS_CDNM"]
        node_id = f"ncs:L:{code}"
        parent_id = None
        class_name = "NCSLargeClass"
    elif level == "M":
        code = f"{row['NCS_LCLAS_CD']}-{row['NCS_MCLAS_CD']}"
        label = row["NCS_MCLAS_CDNM"]
        node_id = f"ncs:M:{code}"
        parent_id = f"ncs:L:{row['NCS_LCLAS_CD']}"
        class_name = "NCSMiddleClass"
    elif level == "S":
        code = f"{row['NCS_LCLAS_CD']}-{row['NCS_MCLAS_CD']}-{row['NCS_SCLAS_CD']}"
        label = row["NCS_SCLAS_CDNM"]
        node_id = f"ncs:S:{code}"
        parent_id = f"ncs:M:{row['NCS_LCLAS_CD']}-{row['NCS_MCLAS_CD']}"
        class_name = "NCSSmallClass"
    else:
        code = f"{row['NCS_LCLAS_CD']}-{row['NCS_MCLAS_CD']}-{row['NCS_SCLAS_CD']}-{row['NCS_SUBD_CD']}"
        label = row["NCS_SUBD_CDNM"]
        node_id = f"ncs:D:{code}"
        parent_id = f"ncs:S:{row['NCS_LCLAS_CD']}-{row['NCS_MCLAS_CD']}-{row['NCS_SCLAS_CD']}"
        class_name = "NCSSubDivision"
    return {
        "id": node_id,
        "class": class_name,
        "label_ko": label,
        "code": code,
        "parent_id": parent_id,
        "ncs_degr": row.get("NCS_DEGR"),
        "source_file": f"01_ncs/ncs_{level.lower() if level != 'D' else 'd'}clas.json",
        "raw": row,
    }


def build_ncs(input_dir, out_dir):
    l_rows = current_use(read_json(input_dir / "01_ncs/ncs_lclas.json"))
    m_rows = current_use(read_json(input_dir / "01_ncs/ncs_mclas.json"))
    s_rows = current_use(read_json(input_dir / "01_ncs/ncs_sclas.json"))
    d_rows = current_use(read_json(input_dir / "01_ncs/ncs_dclas.json"))
    unit_rows = current_use(read_json(input_dir / "01_ncs/ncs_unit.json"))

    class_nodes = []
    for level, rows in [("L", l_rows), ("M", m_rows), ("S", s_rows), ("D", d_rows)]:
        for row in rows:
            class_nodes.append(ncs_class_node(row, level))

    unit_nodes = []
    for row in unit_rows:
        subd = f"{row['NCS_LCLAS_CD']}-{row['NCS_MCLAS_CD']}-{row['NCS_SCLAS_CD']}-{row['NCS_SUBD_CD']}"
        unit_nodes.append(
            {
                "id": f"ncs:CU:{row['NCS_CL_CD']}",
                "class": "NCSCompetencyUnit",
                "label_ko": row.get("COMPE_UNIT_NAME"),
                "definition_ko": row.get("COMPE_UNIT_DEF"),
                "competency_level": row.get("COMPE_UNIT_LEVEL"),
                "ncs_cl_cd": row.get("NCS_CL_CD"),
                "ncs_compe_unit_cd": row.get("NCS_COMPE_UNIT_CD"),
                "parent_id": f"ncs:D:{subd}",
                "source_file": "01_ncs/ncs_unit.json",
                "raw": row,
            }
        )

    ids = {n["id"] for n in class_nodes + unit_nodes}
    edges = []
    for node in class_nodes + unit_nodes:
        parent = node.get("parent_id")
        if parent:
            edges.append(
                {
                    "subject": node["id"],
                    "predicate": "BROADER",
                    "object": parent,
                    "confidence": 1.0,
                    "source": "deterministic_ncs_hierarchy",
                }
            )

    quality = {
        "ncs_current_use_counts": {
            "large": len(l_rows),
            "middle": len(m_rows),
            "small": len(s_rows),
            "subdivision": len(d_rows),
            "competency_unit": len(unit_rows),
        },
        "missing_required_code_rows": sum(
            1
            for row in l_rows + m_rows + s_rows + d_rows + unit_rows
            if not all(v is not None and str(v) != "" for k, v in row.items() if k.endswith("_CD"))
        ),
        "orphan_node_count": sum(1 for e in edges if e["object"] not in ids),
        "duplicate_label_count": sum(v - 1 for v in Counter(n.get("label_ko") for n in class_nodes + unit_nodes).values() if v > 1),
        "competency_definition_missing_count": sum(1 for n in unit_nodes if not n.get("definition_ko")),
    }

    write_jsonl(out_dir / "01_clean_ncs_classes.jsonl", class_nodes)
    write_jsonl(out_dir / "02_clean_ncs_competency_units.jsonl", unit_nodes)
    write_jsonl(out_dir / "18_layer1_ncs_nodes.jsonl", class_nodes + unit_nodes)
    write_jsonl(out_dir / "19_layer1_ncs_edges.jsonl", edges)
    return class_nodes, unit_nodes, edges, quality


def build_pcf(input_dir, out_dir):
    elements = read_json(input_dir / "02_pcf/pcf_data.json")
    metrics = read_json(input_dir / "02_pcf/pcf_metrics.json")
    hid_to_id = {str(e["hid"]): f"pcf:EL:{e['hid']}" for e in elements}
    pcf_id_to_hid = {str(e["pcfId"]): str(e["hid"]) for e in elements}

    nodes = []
    edges = []
    for e in elements:
        node_id = f"pcf:EL:{e['hid']}"
        parent_id = hid_to_id.get(str(e.get("parent"))) if e.get("parent") else None
        nodes.append(
            {
                "id": node_id,
                "class": "PCFElement",
                "label_ko": e.get("nameKo"),
                "label_en": e.get("nameEn"),
                "definition_ko": e.get("descKo"),
                "definition_en": e.get("descEn"),
                "hid": e.get("hid"),
                "pcf_id": e.get("pcfId"),
                "level": e.get("level"),
                "parent_id": parent_id,
                "has_metrics": e.get("hasMetrics"),
                "source_file": "02_pcf/pcf_data.json",
                "raw": e,
            }
        )
        if parent_id:
            edges.append(
                {
                    "subject": node_id,
                    "predicate": "BROADER",
                    "object": parent_id,
                    "confidence": 1.0,
                    "source": "deterministic_pcf_hierarchy",
                }
            )

    metric_nodes = []
    metric_edges = []
    for m in metrics:
        hid = str(m.get("hid") or pcf_id_to_hid.get(str(m.get("pcfId"))))
        parent = hid_to_id.get(hid)
        metric_id = f"pcf:MET:{m.get('metricId')}"
        metric_nodes.append(
            {
                "id": metric_id,
                "class": "PCFMetric",
                "label_ko": m.get("metricNameKo"),
                "label_en": m.get("metricName"),
                "formula_ko": m.get("formulaKo"),
                "formula_en": m.get("formula"),
                "unit_ko": m.get("unitsKo"),
                "unit_en": m.get("units"),
                "category_ko": m.get("categoryKo"),
                "category_en": m.get("category"),
                "hid": hid,
                "pcf_id": m.get("pcfId"),
                "source_file": "02_pcf/pcf_metrics.json",
                "raw": m,
            }
        )
        if parent:
            metric_edges.append(
                {
                    "subject": parent,
                    "predicate": "HAS_METRIC",
                    "object": metric_id,
                    "confidence": 1.0,
                    "source": "deterministic_pcf_metric_link",
                }
            )

    quality = {
        "pcf_element_count": len(nodes),
        "pcf_metric_count": len(metric_nodes),
        "pcf_level_distribution": dict(Counter(n["level"] for n in nodes)),
        "pcf_orphan_parent_count": sum(1 for n in nodes if n.get("parent_id") and n["parent_id"] not in hid_to_id.values()),
        "pcf_duplicate_hid_count": sum(v - 1 for v in Counter(n["hid"] for n in nodes).values() if v > 1),
        "pcf_metric_orphan_count": sum(1 for e in metric_edges if e["subject"] not in hid_to_id.values()),
    }

    write_jsonl(out_dir / "03_clean_pcf_elements.jsonl", nodes)
    write_jsonl(out_dir / "04_clean_pcf_metrics.jsonl", metric_nodes)
    write_jsonl(out_dir / "20_layer1_pcf_nodes.jsonl", nodes)
    write_jsonl(out_dir / "21_layer1_pcf_edges.jsonl", edges)
    write_jsonl(out_dir / "22_layer1_pcf_metric_edges.jsonl", metric_edges)
    return nodes, metric_nodes, edges, metric_edges, quality


def detect_heading(text):
    stripped = clean_text(text)
    if not stripped:
        return False, None
    if re.search(r"\bChapter\s*\d+", stripped, flags=re.I):
        return True, "chapter"
    if stripped in {"프롤로그", "에필로그", "목차", "색인"}:
        return True, "chapter"
    if re.match(r"^\d+(?:\.\d+)+\s+\S+", stripped):
        return True, "section"
    if len(stripped) <= 28 and any(term in stripped for term in ["제안", "입찰", "수주", "리뷰", "전략", "기획"]):
        if not re.search(r"(다|요|까|함|함\.|한다|이다)[.?!]?$", stripped):
            return True, "title"
    return False, None


def ocr_risk(text):
    risk = 0.0
    if len(text) < 2:
        risk += 0.35
    if re.search(r"[A-Za-z]\s+[A-Za-z]", text):
        risk += 0.12
    if re.search(r"[�□■◆◇●○]", text):
        risk += 0.25
    if re.fullmatch(r"[\W\d_]+", text):
        risk += 0.35
    if len(text) > 180 and not re.search(r"[.!?다]($|\s)", text):
        risk += 0.12
    if re.search(r"(Chapter|그림|표)\s*\d+.*\d+$", text):
        risk += 0.05
    if re.search(r"[가-힣][A-Za-z]|[A-Za-z][가-힣]", text):
        risk += 0.04
    return round(min(1.0, risk), 3)


def build_ocr(input_dir, out_dir):
    df = pd.read_excel(input_dir / "자이제_ocr_sentences.xlsx")
    rows = []
    sections = {}
    chapters = {}
    page_counter = defaultdict(int)
    chapter_no = 0
    section_no = 0
    chapter_id = "CH00"
    section_id = "CH00-SEC000"
    chapters[chapter_id] = {
        "chapter_id": chapter_id,
        "title": "front matter",
        "page_start": None,
        "page_end": None,
        "section_ids": [],
    }
    sections[section_id] = {
        "section_id": section_id,
        "chapter_id": chapter_id,
        "title": "front matter",
        "page_start": None,
        "page_end": None,
        "sentence_ids": [],
    }

    for idx, row in df.iterrows():
        text = clean_text(row.get("문장"))
        if not text:
            continue
        page = int(row.get("페이지"))
        page_counter[page] += 1
        page_seq = page_counter[page]
        sent_id = f"SENT-P{page:03d}-{page_seq:04d}"
        page_only = bool(re.fullmatch(r"\d+|[.\-–—]+", text))
        heading, heading_type = detect_heading(text)
        is_header_footer = bool(re.match(r"^Chapter\s+\d+\.?\s+.+\s+\d{1,3}$", text, flags=re.I))
        is_toc_like = bool(
            page < 21
            and re.match(r"^\d+(?:\.\d+)+\s+.+\s+\d{1,3}$", text)
        )

        if heading and heading_type == "chapter":
            chapter_no += 1
            chapter_id = f"CH{chapter_no:02d}"
            chapters[chapter_id] = {
                "chapter_id": chapter_id,
                "title": text[:120],
                "page_start": page,
                "page_end": page,
                "section_ids": [],
            }
            section_no = 0
            section_id = f"{chapter_id}-SEC{section_no:03d}"
            sections[section_id] = {
                "section_id": section_id,
                "chapter_id": chapter_id,
                "title": text[:120],
                "page_start": page,
                "page_end": page,
                "sentence_ids": [],
            }
            chapters[chapter_id]["section_ids"].append(section_id)
        elif heading:
            section_no += 1
            section_id = f"{chapter_id}-SEC{section_no:03d}"
            sections[section_id] = {
                "section_id": section_id,
                "chapter_id": chapter_id,
                "title": text[:120],
                "page_start": page,
                "page_end": page,
                "sentence_ids": [],
            }
            chapters[chapter_id]["section_ids"].append(section_id)

        is_index = bool(re.search(r"색인|찾아보기|Index", text, flags=re.I))
        is_body = bool(text and not page_only and text != "." and not is_header_footer and not is_toc_like)
        record = {
            "sentence_id": sent_id,
            "global_index": len(rows),
            "page": page,
            "page_sequence": page_seq,
            "text": text,
            "char_start": 0,
            "char_end": len(text),
            "chapter_id": chapter_id,
            "section_id": section_id,
            "is_body": is_body,
            "is_heading": heading,
            "heading_type": heading_type,
            "is_index": is_index,
            "is_page_number_only": page_only,
            "is_header_footer": is_header_footer,
            "is_toc_like": is_toc_like,
            "ocr_risk": ocr_risk(text),
        }
        rows.append(record)

        sec = sections[section_id]
        sec["sentence_ids"].append(sent_id)
        sec["page_start"] = page if sec["page_start"] is None else min(sec["page_start"], page)
        sec["page_end"] = page if sec["page_end"] is None else max(sec["page_end"], page)
        chap = chapters[chapter_id]
        chap["page_start"] = page if chap["page_start"] is None else min(chap["page_start"], page)
        chap["page_end"] = page if chap["page_end"] is None else max(chap["page_end"], page)

    evidence = [
        {
            "anchor_id": r["sentence_id"],
            "anchor_type": "SentenceAnchor",
            "sentence_id": r["sentence_id"],
            "page": r["page"],
            "text": r["text"],
            "char_start": 0,
            "char_end": len(r["text"]),
            "section_id": r["section_id"],
            "is_body": r["is_body"],
            "is_index": r["is_index"],
            "ocr_risk": r["ocr_risk"],
        }
        for r in rows
    ]

    document_structure = {
        "document_id": "DOC-JAIJE-WINNING-PROPOSAL",
        "title": "SHIPLEY WINNING PROPOSAL / 자이제 OCR sentence corpus",
        "source_file": "자이제_ocr_sentences.xlsx",
        "page_count": len({r["page"] for r in rows}),
        "sentence_count": len(rows),
        "chapters": list(chapters.values()),
        "sections": list(sections.values()),
    }

    write_jsonl(out_dir / "05_ocr_clean_sentences.jsonl", rows)
    write_json(out_dir / "06_document_structure.json", document_structure)
    write_jsonl(out_dir / "07_evidence_anchors.jsonl", evidence)
    return rows, evidence, document_structure


def make_chunk(chunk_id, chunk_type, rows):
    text = "\n".join(r["text"] for r in rows)
    return {
        "chunk_id": chunk_id,
        "chunk_type": chunk_type,
        "sentence_ids": [r["sentence_id"] for r in rows],
        "section_ids": sorted({r["section_id"] for r in rows}),
        "page_start": min(r["page"] for r in rows),
        "page_end": max(r["page"] for r in rows),
        "char_count": len(text),
        "sentence_count": len(rows),
        "text": text,
    }


def build_chunks(sentences, out_dir):
    body = [r for r in sentences if r["is_body"] and not r["is_index"]]
    chunks_c1 = []
    window = 6
    stride = 4
    for start in range(0, len(body), stride):
        rows = body[start : start + window]
        if len(rows) < 2:
            continue
        chunks_c1.append(make_chunk(f"CHUNK-C1-{len(chunks_c1)+1:05d}", "sentence_window", rows))

    by_section = defaultdict(list)
    for r in body:
        by_section[r["section_id"]].append(r)

    chunks_c2 = []
    for section_id, rows in sorted(by_section.items(), key=lambda kv: min(r["global_index"] for r in kv[1])):
        if not rows:
            continue
        chunks_c2.append(make_chunk(f"CHUNK-C2-{len(chunks_c2)+1:05d}", "section_based", rows))

    chunks_c3 = []
    max_chars = 2400
    for section_id, rows in sorted(by_section.items(), key=lambda kv: min(r["global_index"] for r in kv[1])):
        buf = []
        size = 0
        for r in rows:
            next_size = size + len(r["text"]) + 1
            if buf and next_size > max_chars:
                chunks_c3.append(make_chunk(f"CHUNK-C3-{len(chunks_c3)+1:05d}", "hybrid_semantic", buf))
                buf = buf[-1:] if len(buf) > 1 else []
                size = sum(len(x["text"]) + 1 for x in buf)
            buf.append(r)
            size += len(r["text"]) + 1
        if buf:
            chunks_c3.append(make_chunk(f"CHUNK-C3-{len(chunks_c3)+1:05d}", "hybrid_semantic", buf))

    write_jsonl(out_dir / "08_chunks_sentence_window.jsonl", chunks_c1)
    write_jsonl(out_dir / "09_chunks_section_based.jsonl", chunks_c2)
    write_jsonl(out_dir / "10_chunks_hybrid_semantic.jsonl", chunks_c3)
    return chunks_c1, chunks_c2, chunks_c3


def add_anchor(anchors, anchor_type, label, sentence, start, end, confidence, method):
    label = normalize_label(label)
    if not label or len(label) < 2:
        return
    anchor_id = stable_id("ANCH", anchor_type, sentence["sentence_id"], start, end, label)
    anchors.append(
        {
            "anchor_id": anchor_id,
            "anchor_type": anchor_type,
            "label": label,
            "surface": sentence["text"][start:end] if 0 <= start < end <= len(sentence["text"]) else label,
            "sentence_id": sentence["sentence_id"],
            "page": sentence["page"],
            "section_id": sentence["section_id"],
            "char_start": int(max(0, start)),
            "char_end": int(max(start, end)),
            "confidence": round(float(max(0.0, min(1.0, confidence))), 3),
            "ocr_risk": sentence["ocr_risk"],
            "method": method,
        }
    )


def extract_task_label(text, start, end, action):
    before = text[max(0, start - 38) : start]
    before = re.split(r"[.?!;:•\n]|(?:\s-\s)", before)[-1]
    before = re.sub(r"\([^)]*$", "", before)
    before = re.sub(r".*(?:그리고|또한|첫째|둘째|셋째|단계\s*\d+|활동\(Activity\)|결과물\(Output\))", "", before)
    before = normalize_label(before)
    if len(before) > 24:
        tokens = before.split()
        before = " ".join(tokens[-4:]) if len(tokens) > 1 else before[-24:]
    label = normalize_label(f"{before} {action}" if before else action)
    label = re.sub(r"(정보|내용|자료)$", r"\1", label)
    return label


def extract_anchor_candidates(sentences, out_dir):
    anchors = []
    action_pattern = re.compile("|".join(re.escape(a) for a in sorted(TASK_ACTIONS, key=len, reverse=True)))
    for sentence in sentences:
        if not sentence["is_body"] or sentence["is_index"]:
            continue
        text = sentence["text"]
        for match in action_pattern.finditer(text):
            action = match.group(0)
            label = extract_task_label(text, match.start(), match.end(), action)
            if task_label_is_valid(label) and action in CORE_TASK_ACTIONS:
                conf = 0.62 + (0.18 if contains_domain_term(label) else 0.08 if contains_domain_term(text) else 0.0)
                conf -= sentence["ocr_risk"] * 0.15
                add_anchor(anchors, "TaskActionAnchor", label, sentence, match.start(), match.end(), conf, "action_keyword_window")

        for entity_type, words in KEYWORDS.items():
            anchor_type = f"{entity_type}Anchor"
            for word in sorted(words, key=len, reverse=True):
                flags = re.I if re.search(r"[A-Za-z]", word) else 0
                for match in re.finditer(re.escape(word), text, flags=flags):
                    conf = 0.74 - sentence["ocr_risk"] * 0.10
                    add_anchor(anchors, anchor_type, match.group(0), sentence, match.start(), match.end(), conf, "keyword")

        for pattern in [
            r"[^.?!]{0,35}(?:경우|때|조건|전제|기준|하면|한다면)[^.?!]{0,35}",
            r"[^.?!]{0,35}(?:불리한 조항|극복할 수 없는 조건|예상치 못한 돌발변수)[^.?!]{0,35}",
        ]:
            for match in re.finditer(pattern, text):
                surface = match.group(0).strip(" ,.")
                if len(surface) >= 6:
                    add_anchor(anchors, "ConditionAnchor", surface, sentence, match.start(), match.end(), 0.66, "condition_pattern")

    seen = {}
    for a in anchors:
        key = (a["anchor_type"], a["sentence_id"], a["char_start"], a["char_end"], a["label"].lower())
        if key not in seen or a["confidence"] > seen[key]["confidence"]:
            seen[key] = a
    anchors = list(seen.values())
    write_jsonl(out_dir / "24_anchor_candidates.jsonl", anchors)
    return anchors


def task_label_is_valid(label):
    if not label or len(label) < 3 or len(label) > 70:
        return False
    if re.search(r"^(Chapter|그림|표|내용 첨부|대략적인 틀)", label, flags=re.I):
        return False
    if re.search(r"(이 책|책을 산|오해\s*\d|모든 것|비즈니스는|사회적 환경|경향성)", label):
        return False
    if re.match(r"^(은|는|이|가|을|를|의)\s*", label):
        return False
    if label in set(TASK_ACTIONS):
        return False
    return contains_domain_term(label) and any(a in label for a in CORE_TASK_ACTIONS)


def build_layer2(sentences, evidence, anchors, out_dir):
    sentence_by_id = {s["sentence_id"]: s for s in sentences}
    evidence_by_id = {e["anchor_id"]: e for e in evidence}
    anchors_by_sentence = defaultdict(list)
    for a in anchors:
        anchors_by_sentence[a["sentence_id"]].append(a)

    node_index = {}
    nodes = []
    task_occurrences = []
    task_frames_raw = {}
    task_frames_verified = {}

    def get_node(class_name, label, evidence_ids, confidence=0.7, extra=None):
        label = normalize_label(label)
        node_id = stable_id(f"L2:{class_name}", label.lower())
        if node_id not in node_index:
            node = {
                "id": node_id,
                "class": class_name,
                "label": label,
                "aliases": [],
                "evidence_anchor_ids": [],
                "confidence": round(confidence, 3),
                "source": "jaije_ocr_rule_extraction",
            }
            if extra:
                node.update(extra)
            node_index[node_id] = node
            nodes.append(node)
        node = node_index[node_id]
        for eid in evidence_ids:
            if eid and eid not in node["evidence_anchor_ids"]:
                node["evidence_anchor_ids"].append(eid)
        node["confidence"] = round(max(node["confidence"], confidence), 3)
        return node_id

    def add_edge(edge_map, subject, predicate, obj, evidence_ids, confidence, modality="should", source="rule"):
        if not subject or not obj:
            return
        evidence_ids = [eid for eid in evidence_ids if eid]
        key = (subject, predicate, obj, tuple(sorted(evidence_ids)))
        if key not in edge_map:
            edge_map[key] = {
                "edge_id": stable_id("EDGE", subject, predicate, obj, ",".join(sorted(evidence_ids))),
                "subject": subject,
                "predicate": predicate,
                "object": obj,
                "evidence_anchor_ids": evidence_ids,
                "confidence": round(float(confidence), 3),
                "modality": modality,
                "source": source,
            }
        else:
            edge_map[key]["confidence"] = round(max(edge_map[key]["confidence"], confidence), 3)

    edge_map = {}

    for sentence in sentences:
        if not sentence["is_body"] or sentence["is_index"]:
            continue
        sid = sentence["sentence_id"]
        sent_anchors = anchors_by_sentence.get(sid, [])
        task_anchors = [a for a in sent_anchors if a["anchor_type"] == "TaskActionAnchor" and task_label_is_valid(a["label"])]
        if not task_anchors:
            continue
        artifacts = [a for a in sent_anchors if a["anchor_type"] == "ArtifactAnchor"]
        roles = [a for a in sent_anchors if a["anchor_type"] == "RoleAnchor"]
        decisions = [a for a in sent_anchors if a["anchor_type"] == "DecisionGatewayAnchor"]
        conditions = [a for a in sent_anchors if a["anchor_type"] == "ConditionAnchor"]
        principles = [a for a in sent_anchors if a["anchor_type"] == "PrincipleAnchor"]
        risks = [a for a in sent_anchors if a["anchor_type"] == "RiskAnchor"]
        reviews = [a for a in sent_anchors if a["anchor_type"] == "ReviewEventAnchor"]

        for ta in task_anchors:
            task_conf = max(0.45, min(0.95, ta["confidence"]))
            task_id = get_node("DomainTask", ta["label"], [sid], task_conf)
            step_id = stable_id("L2:ProcedureStep", sid, ta["label"], ta["char_start"])
            if step_id not in node_index:
                node = {
                    "id": step_id,
                    "class": "ProcedureStep",
                    "label": ta["label"],
                    "task_id": task_id,
                    "sequence_index": sentence["global_index"],
                    "page": sentence["page"],
                    "section_id": sentence["section_id"],
                    "evidence_anchor_ids": [sid],
                    "confidence": round(task_conf, 3),
                    "source": "jaije_ocr_rule_extraction",
                }
                node_index[step_id] = node
                nodes.append(node)
            task_occurrences.append(
                {
                    "task_id": task_id,
                    "step_id": step_id,
                    "label": ta["label"],
                    "sentence_id": sid,
                    "section_id": sentence["section_id"],
                    "global_index": sentence["global_index"],
                    "char_start": ta["char_start"],
                    "confidence": task_conf,
                }
            )
            add_edge(edge_map, task_id, "HAS_SUBTASK", step_id, [sid], task_conf)
            add_edge(edge_map, task_id, "EVIDENCED_BY", sid, [sid], 1.0, "must")
            add_edge(edge_map, step_id, "EVIDENCED_BY", sid, [sid], 1.0, "must")

            frame = task_frames_raw.setdefault(
                task_id,
                {
                    "task_id": task_id,
                    "task_name": ta["label"],
                    "definition": sentence["text"],
                    "evidence_anchor_ids": [],
                    "inputs": [],
                    "outputs": [],
                    "roles": [],
                    "decision_points": [],
                    "principles": [],
                    "risks": [],
                    "confidence": task_conf,
                    "status": "raw",
                },
            )
            if sid not in frame["evidence_anchor_ids"]:
                frame["evidence_anchor_ids"].append(sid)
            frame["confidence"] = round(max(frame["confidence"], task_conf), 3)

            for a in artifacts:
                art_id = get_node("Artifact", a["label"], [sid], a["confidence"])
                txt = sentence["text"]
                output_signal = bool(re.search(r"(작성|수립|개발|도출|준비|생성|만들|구성|정의|배포|제출)", txt))
                input_signal = bool(re.search(r"(기반|바탕|활용|참고|입수|수집|검토|요구조건|정보|분석|토대)", txt))
                if output_signal:
                    add_edge(edge_map, task_id, "PRODUCES", art_id, [sid], min(0.86, a["confidence"] + 0.06))
                    if a["label"] not in frame["outputs"]:
                        frame["outputs"].append(a["label"])
                if input_signal or not output_signal:
                    add_edge(edge_map, task_id, "USES_INPUT", art_id, [sid], min(0.78, a["confidence"]))
                    if a["label"] not in frame["inputs"]:
                        frame["inputs"].append(a["label"])

            for a in roles:
                role_id = get_node("Role", a["label"], [sid], a["confidence"])
                add_edge(edge_map, step_id, "PERFORMED_BY", role_id, [sid], a["confidence"])
                add_edge(edge_map, role_id, "RESPONSIBLE_FOR", task_id, [sid], max(0.45, a["confidence"] - 0.08), "may")
                if a["label"] not in frame["roles"]:
                    frame["roles"].append(a["label"])

            for a in decisions:
                dec_id = get_node("DecisionGateway", a["label"], [sid], a["confidence"])
                add_edge(edge_map, task_id, "HAS_DECISION_GATEWAY", dec_id, [sid], a["confidence"])
                if a["label"] not in frame["decision_points"]:
                    frame["decision_points"].append(a["label"])
                for c in conditions:
                    cond_id = get_node("GuardCondition", c["label"], [sid], c["confidence"])
                    add_edge(edge_map, dec_id, "HAS_GUARD_CONDITION", cond_id, [sid], c["confidence"])

            for a in conditions:
                cond_id = get_node("GuardCondition", a["label"], [sid], a["confidence"])
                add_edge(edge_map, task_id, "HAS_GUARD_CONDITION", cond_id, [sid], a["confidence"])

            for a in principles:
                princ_id = get_node("Principle", a["label"], [sid], a["confidence"])
                add_edge(edge_map, task_id, "HAS_PRINCIPLE", princ_id, [sid], a["confidence"])
                if a["label"] not in frame["principles"]:
                    frame["principles"].append(a["label"])

            for a in risks:
                risk_id = get_node("Risk", a["label"], [sid], a["confidence"])
                add_edge(edge_map, task_id, "HAS_RISK", risk_id, [sid], a["confidence"])
                if a["label"] not in frame["risks"]:
                    frame["risks"].append(a["label"])

            for a in reviews:
                review_id = get_node("ReviewEvent", a["label"], [sid], a["confidence"])
                add_edge(edge_map, task_id, "HAS_REVIEW", review_id, [sid], a["confidence"])

    by_section = defaultdict(list)
    for occ in task_occurrences:
        by_section[occ["section_id"]].append(occ)
    for section_id, occs in by_section.items():
        occs = sorted(occs, key=lambda o: (o["global_index"], o["char_start"]))
        for prev, nxt in zip(occs, occs[1:]):
            if prev["step_id"] == nxt["step_id"] or prev["task_id"] == nxt["task_id"]:
                continue
            gap = nxt["global_index"] - prev["global_index"]
            if gap <= 8:
                conf = 0.52 if gap > 2 else 0.64
                add_edge(edge_map, prev["step_id"], "PRECEDES", nxt["step_id"], [prev["sentence_id"], nxt["sentence_id"]], conf, "may")

    # Artifact flow candidates: artifact produced by one task and used by another.
    produces_by_artifact = defaultdict(list)
    uses_by_artifact = defaultdict(list)
    for e in edge_map.values():
        if e["predicate"] == "PRODUCES":
            produces_by_artifact[e["object"]].append(e)
        elif e["predicate"] == "USES_INPUT":
            uses_by_artifact[e["object"]].append(e)
    for artifact_id, prod_edges in produces_by_artifact.items():
        for pe in prod_edges[:10]:
            for ue in uses_by_artifact.get(artifact_id, [])[:10]:
                if pe["subject"] != ue["subject"]:
                    # Keep the plan predicate set: the flow is represented by task->artifact and task uses artifact.
                    pass

    for task_id, frame in task_frames_raw.items():
        completeness = sum(1 for slot in ["inputs", "outputs", "roles", "decision_points", "principles"] if frame[slot])
        verified_conf = min(0.98, frame["confidence"] + completeness * 0.025)
        verified = dict(frame)
        verified["confidence"] = round(verified_conf, 3)
        verified["status"] = "verified_rule_grounded" if frame["evidence_anchor_ids"] else "unsupported_candidate"
        if frame["evidence_anchor_ids"]:
            task_frames_verified[task_id] = verified

    edges = list(edge_map.values())
    evidence_index = []
    for e in evidence:
        evidence_index.append(
            {
                "evidence_anchor_id": e["anchor_id"],
                "sentence_id": e["sentence_id"],
                "page": e["page"],
                "section_id": e["section_id"],
                "text": e["text"],
                "ocr_risk": e["ocr_risk"],
                "node_count": sum(1 for n in nodes if e["anchor_id"] in n.get("evidence_anchor_ids", [])),
                "edge_count": sum(1 for edge in edges if e["anchor_id"] in edge.get("evidence_anchor_ids", [])),
            }
        )

    aliases = defaultdict(set)
    for n in nodes:
        key = normalize_label(n["label"]).lower()
        aliases[key].add(n["label"])
    alias_dict = {k: sorted(v) for k, v in aliases.items() if len(v) > 1}

    unsupported = []
    for frame in task_frames_raw.values():
        if not frame.get("evidence_anchor_ids"):
            unsupported.append(frame)

    write_jsonl(out_dir / "25_task_frames_raw.jsonl", task_frames_raw.values())
    write_jsonl(out_dir / "26_task_frames_verified.jsonl", task_frames_verified.values())
    write_jsonl(out_dir / "27_procedural_relations_raw.jsonl", edges)
    verified_edges = [e for e in edges if e.get("evidence_anchor_ids") and e["confidence"] >= 0.45]
    write_jsonl(out_dir / "28_procedural_relations_verified.jsonl", verified_edges)
    write_jsonl(out_dir / "29_layer2_nodes.jsonl", nodes)
    write_jsonl(out_dir / "30_layer2_edges.jsonl", verified_edges)
    write_jsonl(out_dir / "31_layer2_evidence_index.jsonl", evidence_index)
    write_json(out_dir / "32_alias_dictionary.json", alias_dict)
    write_jsonl(out_dir / "34_unsupported_candidates.jsonl", unsupported)
    return nodes, verified_edges, task_frames_verified, evidence_index


def compile_standard_docs(ncs_units, pcf_nodes):
    ncs_docs = []
    for n in ncs_units:
        ncs_docs.append(
            {
                "id": n["id"],
                "class": "StandardAnchor",
                "standard": "NCS",
                "label": n.get("label_ko") or "",
                "text": clean_text((n.get("label_ko") or "") + " " + (n.get("definition_ko") or "")),
            }
        )
    pcf_docs = []
    for n in pcf_nodes:
        pcf_docs.append(
            {
                "id": n["id"],
                "class": "StandardAnchor",
                "standard": "PCF",
                "label": n.get("label_ko") or n.get("label_en") or "",
                "text": clean_text(" ".join([n.get("label_ko") or "", n.get("label_en") or "", n.get("definition_ko") or "", n.get("definition_en") or ""])),
            }
        )
    return ncs_docs, pcf_docs


def top_tfidf_matches(queries, docs, top_k=3):
    if not queries or not docs:
        return [[] for _ in queries]
    corpus = [d["text"] for d in docs]
    vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), min_df=1, max_features=60000)
    doc_matrix = vectorizer.fit_transform(corpus)
    query_matrix = vectorizer.transform(queries)
    sim = cosine_similarity(query_matrix, doc_matrix)
    all_matches = []
    for row in sim:
        ranked = sorted(enumerate(row), key=lambda x: x[1], reverse=True)[:top_k]
        all_matches.append([(docs[i], float(score)) for i, score in ranked])
    return all_matches


def add_standard_mapping(nodes, edges, task_frames, ncs_units, pcf_nodes, out_dir):
    task_nodes = [n for n in nodes if n["class"] == "DomainTask"]
    task_texts = []
    for n in task_nodes:
        frame = task_frames.get(n["id"], {})
        task_texts.append(clean_text(n["label"] + " " + frame.get("definition", "")))

    ncs_docs, pcf_docs = compile_standard_docs(ncs_units, pcf_nodes)
    ncs_matches = top_tfidf_matches(task_texts, ncs_docs, top_k=3)
    pcf_matches = top_tfidf_matches(task_texts, pcf_docs, top_k=3)

    existing = {(e["subject"], e["predicate"], e["object"]) for e in edges}
    standard_nodes = {}
    mapping_disagreement = {}
    for idx, task in enumerate(task_nodes):
        task_evidence = task.get("evidence_anchor_ids", [])[:3]
        ncs_top = ncs_matches[idx] if idx < len(ncs_matches) else []
        pcf_top = pcf_matches[idx] if idx < len(pcf_matches) else []
        top_scores = []
        for standard, score in ncs_top:
            top_scores.append(score)
            standard_nodes[standard["id"]] = standard
            if score >= 0.055:
                pred = "REQUIRES_CAPABILITY" if score >= 0.12 and standard == ncs_top[0][0] else "CANDIDATE_ALIGNS_WITH"
                key = (task["id"], pred, standard["id"])
                if key not in existing:
                    edges.append(
                        {
                            "edge_id": stable_id("EDGE", task["id"], pred, standard["id"]),
                            "subject": task["id"],
                            "predicate": pred,
                            "object": standard["id"],
                            "evidence_anchor_ids": task_evidence,
                            "confidence": round(min(0.95, score), 3),
                            "modality": "may",
                            "source": "tfidf_standard_triangulation",
                            "mapping_score": round(score, 6),
                        }
                    )
                    existing.add(key)
        for standard, score in pcf_top:
            top_scores.append(score)
            standard_nodes[standard["id"]] = standard
            if score >= 0.055:
                pred = "PROCESS_CONTEXT" if score >= 0.12 and standard == pcf_top[0][0] else "CANDIDATE_ALIGNS_WITH"
                key = (task["id"], pred, standard["id"])
                if key not in existing:
                    edges.append(
                        {
                            "edge_id": stable_id("EDGE", task["id"], pred, standard["id"]),
                            "subject": task["id"],
                            "predicate": pred,
                            "object": standard["id"],
                            "evidence_anchor_ids": task_evidence,
                            "confidence": round(min(0.95, score), 3),
                            "modality": "may",
                            "source": "tfidf_standard_triangulation",
                            "mapping_score": round(score, 6),
                        }
                    )
                    existing.add(key)
        best_ncs = ncs_top[0][1] if ncs_top else 0.0
        best_pcf = pcf_top[0][1] if pcf_top else 0.0
        mapping_disagreement[task["id"]] = round(1.0 - min(1.0, (best_ncs + best_pcf) / 0.35), 3)

    for sid, snode in standard_nodes.items():
        nodes.append(
            {
                "id": sid,
                "class": "StandardAnchor",
                "label": snode["label"],
                "standard": snode["standard"],
                "evidence_anchor_ids": [],
                "confidence": 1.0,
                "source": "layer1_standard_reference",
            }
        )

    write_jsonl(out_dir / "29_layer2_nodes.jsonl", nodes)
    write_jsonl(out_dir / "30_layer2_edges.jsonl", edges)
    return nodes, edges, mapping_disagreement


def generate_cqs(task_frames, nodes, edges, out_dir):
    node_by_id = {n["id"]: n for n in nodes}
    edge_by_subject = defaultdict(list)
    for e in edges:
        edge_by_subject[e["subject"]].append(e)

    tasks = []
    for frame in task_frames.values():
        tasks.append(
            {
                "task_id": frame["task_id"],
                "label": frame["task_name"],
                "evidence_count": len(frame.get("evidence_anchor_ids", [])),
                "slot_count": sum(1 for k in ["inputs", "outputs", "roles", "decision_points", "principles", "risks"] if frame.get(k)),
                "confidence": frame.get("confidence", 0.0),
            }
        )
    tasks = sorted(tasks, key=lambda t: (t["slot_count"], t["evidence_count"], t["confidence"]), reverse=True)[:30]

    templates = [
        ("Task decomposition", "{label}은 어떤 하위 절차 단계로 구성되는가?", ["HAS_SUBTASK"]),
        ("Input-output", "{label}의 입력 자료와 산출물은 무엇인가?", ["USES_INPUT", "PRODUCES"]),
        ("Role responsibility", "{label}은 어떤 역할이 수행하거나 책임지는가?", ["PERFORMED_BY", "RESPONSIBLE_FOR"]),
        ("Decision/gateway", "{label}에는 어떤 의사결정 지점이나 조건이 연결되는가?", ["HAS_DECISION_GATEWAY", "HAS_GUARD_CONDITION"]),
        ("Principle", "{label} 수행 시 지켜야 할 원칙이나 품질 기준은 무엇인가?", ["HAS_PRINCIPLE"]),
        ("Standard alignment", "{label}은 어떤 NCS 능력단위 또는 PCF process와 관련되는가?", ["REQUIRES_CAPABILITY", "PROCESS_CONTEXT", "CANDIDATE_ALIGNS_WITH"]),
    ]
    cqs = []
    for task in tasks:
        for cq_type, template, predicates in templates:
            cq_id = f"CQ-{len(cqs)+1:03d}"
            cqs.append(
                {
                    "cq_id": cq_id,
                    "cq_type": cq_type,
                    "question": template.format(label=task["label"]),
                    "seed_node_id": task["task_id"],
                    "seed_label": task["label"],
                    "target_predicates": predicates,
                    "generated_by": "rule_template_from_verified_task_frame",
                    "status": "candidate",
                }
            )
            if len(cqs) >= 120:
                break
        if len(cqs) >= 120:
            break

    core = cqs[:60]
    for cq in core:
        cq["status"] = "core_candidate_pending_expert_approval"

    sparql_templates = []
    for cq in cqs:
        values = " ".join(f"cepo:{p}" for p in cq["target_predicates"])
        sparql_templates.append(
            {
                "cq_id": cq["cq_id"],
                "seed_node_id": cq["seed_node_id"],
                "query_type": "local_graph_pattern",
                "template": f"SELECT ?object WHERE {{ <{cq['seed_node_id']}> ?predicate ?object . VALUES ?predicate {{ {values} }} }}",
                "target_predicates": cq["target_predicates"],
            }
        )

    answer_rows = []
    for cq in core:
        direct = [e for e in edge_by_subject.get(cq["seed_node_id"], []) if e["predicate"] in cq["target_predicates"]]
        if not direct and "PERFORMED_BY" in cq["target_predicates"]:
            # Role responsibility can be answered through task -> step -> role.
            subtasks = [e["object"] for e in edge_by_subject.get(cq["seed_node_id"], []) if e["predicate"] == "HAS_SUBTASK"]
            for step in subtasks:
                direct.extend([e for e in edge_by_subject.get(step, []) if e["predicate"] == "PERFORMED_BY"])
        answer_rows.append(
            {
                "cq_id": cq["cq_id"],
                "cq_type": cq["cq_type"],
                "question": cq["question"],
                "answerable": bool(direct),
                "supporting_edge_count": len(direct),
                "supporting_objects": [node_by_id.get(e["object"], {}).get("label", e["object"]) for e in direct[:10]],
                "evidence_anchor_ids": sorted({eid for e in direct for eid in e.get("evidence_anchor_ids", [])}),
            }
        )

    write_jsonl(out_dir / "11_cq_candidates_raw.jsonl", cqs)
    write_jsonl(out_dir / "12_cq_core_reviewed.jsonl", core)
    write_jsonl(out_dir / "13_cq_to_sparql_templates.jsonl", sparql_templates)
    return cqs, core, answer_rows


def write_schema_artifacts(out_dir):
    tbox = """@prefix cepo: <https://example.org/cep-onto#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .

cepo:DomainTask a owl:Class .
cepo:ProcedureStep a owl:Class .
cepo:DecisionGateway a owl:Class .
cepo:GuardCondition a owl:Class .
cepo:Artifact a owl:Class .
cepo:Role a owl:Class .
cepo:Principle a owl:Class .
cepo:ReviewEvent a owl:Class .
cepo:Risk a owl:Class .
cepo:EvidenceAnchor a owl:Class .
cepo:StandardAnchor a owl:Class .
cepo:ExtractionActivity a owl:Class .

cepo:HAS_SUBTASK a owl:ObjectProperty ; rdfs:domain cepo:DomainTask ; rdfs:range cepo:ProcedureStep .
cepo:PRECEDES a owl:ObjectProperty ; rdfs:domain cepo:ProcedureStep ; rdfs:range cepo:ProcedureStep .
cepo:USES_INPUT a owl:ObjectProperty ; rdfs:domain cepo:DomainTask ; rdfs:range cepo:Artifact .
cepo:PRODUCES a owl:ObjectProperty ; rdfs:domain cepo:DomainTask ; rdfs:range cepo:Artifact .
cepo:PERFORMED_BY a owl:ObjectProperty ; rdfs:domain cepo:ProcedureStep ; rdfs:range cepo:Role .
cepo:RESPONSIBLE_FOR a owl:ObjectProperty ; rdfs:domain cepo:Role ; rdfs:range cepo:DomainTask .
cepo:HAS_DECISION_GATEWAY a owl:ObjectProperty ; rdfs:domain cepo:DomainTask ; rdfs:range cepo:DecisionGateway .
cepo:HAS_GUARD_CONDITION a owl:ObjectProperty ; rdfs:range cepo:GuardCondition .
cepo:HAS_REVIEW a owl:ObjectProperty ; rdfs:domain cepo:DomainTask ; rdfs:range cepo:ReviewEvent .
cepo:HAS_PRINCIPLE a owl:ObjectProperty ; rdfs:domain cepo:DomainTask ; rdfs:range cepo:Principle .
cepo:HAS_RISK a owl:ObjectProperty ; rdfs:domain cepo:DomainTask ; rdfs:range cepo:Risk .
cepo:EVIDENCED_BY a owl:ObjectProperty ; rdfs:range cepo:EvidenceAnchor .
cepo:CANDIDATE_ALIGNS_WITH a owl:ObjectProperty ; rdfs:domain cepo:DomainTask ; rdfs:range cepo:StandardAnchor .
cepo:REQUIRES_CAPABILITY a owl:ObjectProperty ; rdfs:domain cepo:DomainTask ; rdfs:range cepo:StandardAnchor .
cepo:PROCESS_CONTEXT a owl:ObjectProperty ; rdfs:domain cepo:DomainTask ; rdfs:range cepo:StandardAnchor .
"""
    shapes = """@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix cepo: <https://example.org/cep-onto#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

cepo:DomainTaskShape a sh:NodeShape ;
  sh:targetClass cepo:DomainTask ;
  sh:property [ sh:path cepo:EVIDENCED_BY ; sh:minCount 1 ] .

cepo:ProcedureStepShape a sh:NodeShape ;
  sh:targetClass cepo:ProcedureStep ;
  sh:property [ sh:path cepo:EVIDENCED_BY ; sh:minCount 1 ] .

cepo:ProceduralRelationShape a sh:NodeShape ;
  sh:message "Every CEP-Onto generated relation must carry at least one evidence anchor in the JSONL edge payload." .
"""
    tool_schemas = {
        "create_task_frame": {
            "type": "object",
            "required": ["task_name", "evidence_anchor_ids", "confidence"],
            "properties": {
                "task_name": {"type": "string"},
                "definition": {"type": "string"},
                "inputs": {"type": "array", "items": {"type": "string"}},
                "outputs": {"type": "array", "items": {"type": "string"}},
                "roles": {"type": "array", "items": {"type": "string"}},
                "decision_points": {"type": "array", "items": {"type": "string"}},
                "principles": {"type": "array", "items": {"type": "string"}},
                "evidence_anchor_ids": {"type": "array", "minItems": 1, "items": {"type": "string"}},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            },
        },
        "add_procedural_relation": {
            "type": "object",
            "required": ["subject_id", "predicate", "object_id", "evidence_anchor_ids", "confidence"],
            "properties": {
                "subject_id": {"type": "string"},
                "predicate": {"enum": sorted(PREDICATE_REGISTRY.keys())},
                "object_id": {"type": "string"},
                "modality": {"enum": ["must", "should", "may", "example"]},
                "condition_id": {"type": ["string", "null"]},
                "evidence_anchor_ids": {"type": "array", "minItems": 1, "items": {"type": "string"}},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            },
        },
        "attach_evidence_anchor": {
            "type": "object",
            "required": ["target_id", "evidence_anchor_id", "claim_part"],
            "properties": {
                "target_id": {"type": "string"},
                "evidence_anchor_id": {"type": "string"},
                "claim_part": {"enum": ["subject", "predicate", "object", "slot", "whole_claim"]},
            },
        },
        "reject_candidate": {
            "type": "object",
            "required": ["candidate_id", "reason"],
            "properties": {"candidate_id": {"type": "string"}, "reason": {"type": "string"}},
        },
        "propose_new_schema_term": {
            "type": "object",
            "required": ["term", "term_type", "evidence_anchor_ids"],
            "properties": {
                "term": {"type": "string"},
                "term_type": {"enum": ["class", "predicate", "slot", "constraint"]},
                "evidence_anchor_ids": {"type": "array", "minItems": 1, "items": {"type": "string"}},
            },
        },
    }
    registry = [
        {"predicate": p, "domain": d, "range": r}
        for p, (d, r) in sorted(PREDICATE_REGISTRY.items())
    ]
    write_text(out_dir / "14_ontology_tbox.ttl", tbox)
    write_text(out_dir / "15_ontology_shapes.shacl.ttl", shapes)
    write_json(out_dir / "16_tool_schemas.json", tool_schemas)
    write_json(out_dir / "17_predicate_registry.json", registry)


def validate_graph(nodes, edges, evidence_ids):
    node_classes = {n["id"]: n["class"] for n in nodes}
    known_nodes = set(node_classes)
    known_nodes |= set(evidence_ids)
    unknown_predicate = [e for e in edges if e["predicate"] not in PREDICATE_REGISTRY]
    missing_evidence = [
        e
        for e in edges
        if e["predicate"] not in {"BROADER", "HAS_METRIC"} and not e.get("evidence_anchor_ids")
    ]
    missing_node_ref = [e for e in edges if e["subject"] not in known_nodes or e["object"] not in known_nodes]
    domain_range = []
    for e in edges:
        if e["predicate"] not in PREDICATE_REGISTRY:
            continue
        domain, range_ = PREDICATE_REGISTRY[e["predicate"]]
        subj_cls = node_classes.get(e["subject"], "EvidenceAnchor" if e["subject"] in evidence_ids else None)
        obj_cls = node_classes.get(e["object"], "EvidenceAnchor" if e["object"] in evidence_ids else None)
        if domain != "*" and subj_cls and subj_cls != domain:
            domain_range.append(e)
        if range_ != "*" and obj_cls and obj_cls != range_:
            domain_range.append(e)
    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "unknown_predicate_count": len(unknown_predicate),
        "missing_evidence_edge_count": len(missing_evidence),
        "missing_node_reference_count": len(missing_node_ref),
        "domain_range_violation_count": len(domain_range),
        "shacl_like_violation_rate": round(
            (len(unknown_predicate) + len(missing_evidence) + len(missing_node_ref) + len(domain_range))
            / max(1, len(edges)),
            6,
        ),
    }


def build_review_queue(nodes, edges, evidence_by_id, mapping_disagreement, out_dir):
    degree = Counter()
    for e in edges:
        degree[e["subject"]] += 1
        degree[e["object"]] += 1
    max_degree = max(degree.values()) if degree else 1
    queue = []
    for e in edges:
        evidences = [evidence_by_id.get(eid) for eid in e.get("evidence_anchor_ids", [])]
        risks = [ev.get("ocr_risk", 0.0) for ev in evidences if ev]
        evidence_anchor_risk = max(risks) if risks else 0.4
        graph_centrality = max(degree[e["subject"]], degree[e["object"]]) / max_degree
        uncertainty = 1.0 - e.get("confidence", 0.0)
        mapping = mapping_disagreement.get(e["subject"], 0.0)
        conflict = 0.0
        text = " ".join(ev.get("text", "") for ev in evidences if ev)
        if re.search(r"No bid|불리한|극복할 수 없는|돌발변수|실패|위험", text, flags=re.I):
            conflict = 0.8
        priority = 0.30 * uncertainty + 0.20 * evidence_anchor_risk + 0.20 * graph_centrality + 0.15 * mapping + 0.15 * conflict
        queue.append(
            {
                "review_item_id": stable_id("REV", e["edge_id"]),
                "target_type": "edge",
                "target_id": e["edge_id"],
                "subject": e["subject"],
                "predicate": e["predicate"],
                "object": e["object"],
                "confidence": e.get("confidence"),
                "extraction_uncertainty": round(uncertainty, 3),
                "evidence_anchor_risk": round(evidence_anchor_risk, 3),
                "graph_centrality": round(graph_centrality, 3),
                "mapping_disagreement": round(mapping, 3),
                "conflict_score": round(conflict, 3),
                "review_priority": round(priority, 6),
                "evidence_anchor_ids": e.get("evidence_anchor_ids", []),
            }
        )
    queue = sorted(queue, key=lambda r: r["review_priority"], reverse=True)
    write_jsonl(out_dir / "33_conflict_review_queue.jsonl", queue)
    return queue


def write_gold_annotation_template(chunks, out_dir):
    # Stratified seed: first chunk per chapter/section spread, marked pending rather than fake gold.
    selected = []
    seen_sections = set()
    for chunk in chunks:
        section = chunk["section_ids"][0] if chunk["section_ids"] else "UNKNOWN"
        if section not in seen_sections:
            selected.append(chunk)
            seen_sections.add(section)
        if len(selected) >= max(1, int(len(chunks) * 0.05)):
            break
    rows = []
    for chunk in selected:
        rows.append(
            {
                "chunk_id": chunk["chunk_id"],
                "annotation_status": "pending_human_annotation",
                "sentence_ids": chunk["sentence_ids"],
                "page_start": chunk["page_start"],
                "page_end": chunk["page_end"],
                "gold_entities": [],
                "gold_relations": [],
                "evidence_spans": [],
                "annotator_notes": "",
            }
        )
    write_jsonl(out_dir / "35_gold_annotations.jsonl", rows)
    return rows


def ttl_literal(value):
    value = clean_text(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{value}"'


def ttl_uri(identifier):
    return f"<urn:ceponto:{sha1_text(identifier, 20)}>"


def write_graph_ttl(nodes, edges, out_dir):
    lines = [
        "@prefix cepo: <https://example.org/cep-onto#> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "",
    ]
    for n in nodes:
        lines.append(f"{ttl_uri(n['id'])} a cepo:{n['class']} ; rdfs:label {ttl_literal(n.get('label') or n.get('label_ko') or n['id'])} .")
    lines.append("")
    for e in edges:
        pred = e["predicate"]
        lines.append(f"{ttl_uri(e['subject'])} cepo:{pred} {ttl_uri(e['object'])} .")
    write_text(out_dir / "44_final_graph.ttl", "\n".join(lines) + "\n")


def write_reports(
    out_dir,
    manifest_rows,
    ncs_quality,
    pcf_quality,
    sentences,
    chunks,
    anchors,
    nodes,
    edges,
    task_frames,
    cq_answer_rows,
    validation,
    review_queue,
):
    write_csv(out_dir / "00_data_manifest.csv", manifest_rows)

    layer1_report = f"""# Layer1 Quality Report

Generated: {RUN_DATE}

## NCS

- Current-use classes: L={ncs_quality['ncs_current_use_counts']['large']}, M={ncs_quality['ncs_current_use_counts']['middle']}, S={ncs_quality['ncs_current_use_counts']['small']}, D={ncs_quality['ncs_current_use_counts']['subdivision']}
- Current-use competency units: {ncs_quality['ncs_current_use_counts']['competency_unit']}
- Orphan nodes after current-use filtering: {ncs_quality['orphan_node_count']}
- Duplicate labels: {ncs_quality['duplicate_label_count']}
- Competency units missing definition: {ncs_quality['competency_definition_missing_count']}

## PCF

- PCF elements: {pcf_quality['pcf_element_count']}
- PCF metrics: {pcf_quality['pcf_metric_count']}
- Level distribution: {pcf_quality['pcf_level_distribution']}
- Orphan parent count: {pcf_quality['pcf_orphan_parent_count']}
- Duplicate hid count: {pcf_quality['pcf_duplicate_hid_count']}
"""
    write_text(out_dir / "23_layer1_quality_report.md", layer1_report)

    answerable = sum(1 for r in cq_answer_rows if r["answerable"])
    cq_report = f"""# CQ Answerability Report

Generated: {RUN_DATE}

- Core CQ candidates evaluated: {len(cq_answer_rows)}
- Locally answerable from generated graph: {answerable}
- CQ answerability: {answerable / max(1, len(cq_answer_rows)):.3f}

This is an automatic graph-pattern check. It is not a human answer-accuracy score.
Core CQ rows are stored in `12_cq_core_reviewed.jsonl`; despite the filename from the experiment plan, this first run marks them as pending expert approval.
"""
    cq_report += "\n## Unanswerable CQ Candidates\n\n"
    for row in [r for r in cq_answer_rows if not r["answerable"]][:20]:
        cq_report += f"- {row['cq_id']} [{row['cq_type']}] {row['question']}\n"
    write_text(out_dir / "39_cq_answerability_report.md", cq_report)

    edge_grounded = sum(1 for e in edges if e.get("evidence_anchor_ids"))
    node_grounded = sum(1 for n in nodes if n.get("evidence_anchor_ids"))
    restoration_success = 0
    evidence_text_by_id = {s["sentence_id"]: s["text"] for s in sentences}
    for e in edges:
        ok = True
        for eid in e.get("evidence_anchor_ids", []):
            if eid not in evidence_text_by_id:
                ok = False
                break
        if ok and e.get("evidence_anchor_ids"):
            restoration_success += 1
    hallucination_report = f"""# Hallucination And Grounding Audit

Generated: {RUN_DATE}

- Nodes: {len(nodes)}
- Edges: {len(edges)}
- Node grounding rate: {node_grounded / max(1, len(nodes)):.3f}
- Edge grounding rate: {edge_grounded / max(1, len(edges)):.3f}
- Evidence restoration success over grounded edges: {restoration_success / max(1, edge_grounded):.3f}
- Unsupported candidate count: 0 for verified Layer2 edges; weak standard mappings retain task evidence but require expert validation.
- SHACL-like violation rate: {validation['shacl_like_violation_rate']:.6f}

The current run is evidence-first and rule-based. It should be treated as a high-recall draft graph, not as a gold ontology.
"""
    write_text(out_dir / "40_hallucination_audit_report.md", hallucination_report)

    review_report = f"""# Human Review Efficiency Report

Generated: {RUN_DATE}

No human review timing was collected in this run. The active review queue has been created for the next experimental pass.

- Review queue items: {len(review_queue)}
- Top-priority review item score: {review_queue[0]['review_priority'] if review_queue else 0}
- Priority formula: 0.30 uncertainty + 0.20 evidence risk + 0.20 centrality + 0.15 mapping disagreement + 0.15 conflict

Use `33_conflict_review_queue.jsonl` for expert review sampling.
"""
    write_text(out_dir / "41_human_review_efficiency_report.md", review_report)

    mapping_edges = [e for e in edges if e["predicate"] in {"CANDIDATE_ALIGNS_WITH", "REQUIRES_CAPABILITY", "PROCESS_CONTEXT"}]
    scores = [e.get("mapping_score", e.get("confidence", 0.0)) for e in mapping_edges]
    mean_mapping_score = f"{statistics.mean(scores):.4f}" if scores else "0.0000"
    median_mapping_score = f"{statistics.median(scores):.4f}" if scores else "0.0000"
    mapping_report = f"""# Mapping Evaluation Report

Generated: {RUN_DATE}

- Weak standard mapping edges: {len(mapping_edges)}
- Mean mapping score: {mean_mapping_score}
- Median mapping score: {median_mapping_score}

Precision@k, MRR, and nDCG require expert relevance labels and are therefore pending.
"""
    write_text(out_dir / "42_mapping_evaluation_report.md", mapping_report)

    node_counts = Counter(n["class"] for n in nodes)
    edge_counts = Counter(e["predicate"] for e in edges)
    final_report = f"""# Final Ontology Build Report

Generated: {RUN_DATE}

## Scope

Built a first-pass CEP-Onto KG using only the local AX-HYU handoff data:
NCS, PCF, PCF metrics, 수주 focus subsets, and `자이제_ocr_sentences.xlsx`.

## OCR And Chunking

- Clean OCR sentences: {len(sentences)}
- Sentence-window chunks: {len(chunks[0])}
- Section-based chunks: {len(chunks[1])}
- Hybrid semantic chunks: {len(chunks[2])}
- Anchor candidates: {len(anchors)}

## Layer2 Graph

- Nodes: {len(nodes)}
- Edges: {len(edges)}
- Verified task frames: {len(task_frames)}

Node class counts:
{json.dumps(dict(node_counts), ensure_ascii=False, indent=2)}

Predicate counts:
{json.dumps(dict(edge_counts), ensure_ascii=False, indent=2)}

## Validation

{json.dumps(validation, ensure_ascii=False, indent=2)}

## Important Limitation

This run does not call an LLM and does not include human adjudicated gold labels.
It is a reproducible draft KG and experiment scaffold aligned with the design document.
The next pass should use `16_tool_schemas.json`, `24_anchor_candidates.jsonl`, and
`33_conflict_review_queue.jsonl` for constrained LLM extraction and expert review.
"""
    write_text(out_dir / "43_final_ontology_build_report.md", final_report)

    config = {
        "run_id": "cep_onto_jaije_20260627_local_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_dir": str(DEFAULT_INPUT),
        "output_dir": str(out_dir),
        "method": "CEP-Onto deterministic Layer1 + rule-based evidence-first Layer2 + TF-IDF standard triangulation",
        "uses_external_llm": False,
        "chunking": {"sentence_window": {"window": 6, "stride": 4}, "hybrid_max_chars": 2400},
        "ncs_filter": {"NCS_DEGR": 29, "USG_YN": "Y"},
    }
    write_text(out_dir / "36_experiment_config.yaml", yaml_dump(config))

    result_rows = [
        {"metric": "clean_ocr_sentences", "value": len(sentences), "condition": "P-local-rule-cep-onto-v1"},
        {"metric": "anchor_candidates", "value": len(anchors), "condition": "P-local-rule-cep-onto-v1"},
        {"metric": "layer2_nodes", "value": len(nodes), "condition": "P-local-rule-cep-onto-v1"},
        {"metric": "layer2_edges", "value": len(edges), "condition": "P-local-rule-cep-onto-v1"},
        {"metric": "verified_task_frames", "value": len(task_frames), "condition": "P-local-rule-cep-onto-v1"},
        {"metric": "cq_answerability_auto", "value": answerable / max(1, len(cq_answer_rows)), "condition": "P-local-rule-cep-onto-v1"},
        {"metric": "shacl_like_violation_rate", "value": validation["shacl_like_violation_rate"], "condition": "P-local-rule-cep-onto-v1"},
    ]
    write_csv(out_dir / "37_experiment_results.csv", result_rows)

    ablation_rows = [
        {"experiment": "chunking", "condition": "C1 sentence-window", "chunk_count": len(chunks[0]), "mean_chars": mean([c["char_count"] for c in chunks[0]])},
        {"experiment": "chunking", "condition": "C2 section-based", "chunk_count": len(chunks[1]), "mean_chars": mean([c["char_count"] for c in chunks[1]])},
        {"experiment": "chunking", "condition": "C3 hybrid-semantic", "chunk_count": len(chunks[2]), "mean_chars": mean([c["char_count"] for c in chunks[2]])},
        {"experiment": "extraction", "condition": "P local rule-based evidence-first", "chunk_count": "", "mean_chars": "", "note": "LLM baselines B0-B4 pending model/API configuration"},
    ]
    write_csv(out_dir / "38_ablation_results.csv", ablation_rows)


def mean(values):
    values = list(values)
    return round(sum(values) / len(values), 3) if values else 0.0


def yaml_dump(obj, indent=0):
    lines = []
    pad = "  " * indent
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                lines.append(f"{pad}{k}:")
                lines.append(yaml_dump(v, indent + 1))
            else:
                lines.append(f"{pad}{k}: {json.dumps(v, ensure_ascii=False)}")
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, (dict, list)):
                lines.append(f"{pad}-")
                lines.append(yaml_dump(item, indent + 1))
            else:
                lines.append(f"{pad}- {json.dumps(item, ensure_ascii=False)}")
    else:
        lines.append(f"{pad}{json.dumps(obj, ensure_ascii=False)}")
    return "\n".join(lines) + ("\n" if indent == 0 else "")


def run(input_dir, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = source_manifest(input_dir)
    ncs_classes, ncs_units, ncs_edges, ncs_quality = build_ncs(input_dir, out_dir)
    pcf_nodes, pcf_metric_nodes, pcf_edges, pcf_metric_edges, pcf_quality = build_pcf(input_dir, out_dir)
    sentences, evidence, document_structure = build_ocr(input_dir, out_dir)
    chunks = build_chunks(sentences, out_dir)
    write_schema_artifacts(out_dir)
    anchors = extract_anchor_candidates(sentences, out_dir)
    nodes, edges, task_frames, evidence_index = build_layer2(sentences, evidence, anchors, out_dir)
    nodes, edges, mapping_disagreement = add_standard_mapping(nodes, edges, task_frames, ncs_units, pcf_nodes, out_dir)
    cqs, core_cqs, cq_answer_rows = generate_cqs(task_frames, nodes, edges, out_dir)

    evidence_by_id = {e["anchor_id"]: e for e in evidence}
    validation = validate_graph(nodes, edges, evidence_by_id.keys())
    review_queue = build_review_queue(nodes, edges, evidence_by_id, mapping_disagreement, out_dir)
    write_gold_annotation_template(chunks[2], out_dir)
    write_graph_ttl(nodes, edges, out_dir)
    write_reports(
        out_dir,
        manifest,
        ncs_quality,
        pcf_quality,
        sentences,
        chunks,
        anchors,
        nodes,
        edges,
        task_frames,
        cq_answer_rows,
        validation,
        review_queue,
    )
    summary = {
        "output_dir": str(out_dir),
        "sentences": len(sentences),
        "anchors": len(anchors),
        "layer2_nodes": len(nodes),
        "layer2_edges": len(edges),
        "task_frames": len(task_frames),
        "core_cqs": len(core_cqs),
        "validation": validation,
    }
    write_json(out_dir / "run_summary.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", default=str(DEFAULT_INPUT))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()
    summary = run(Path(args.input_dir), Path(args.output_dir))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
