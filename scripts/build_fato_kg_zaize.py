#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a first-pass FATO-KG experiment from 자이제_1.xlsx.

This builder intentionally avoids pandas/openpyxl so the experiment can run in
the current minimal environment. It reads the XLSX XML directly, then creates a
transparent rule-based first pass aligned with layer2_fato_kg_methodology_eacl.md.

The generated KG is not human gold. It is a reproducible FATO-KG bootstrap:
evidence units, section chunks, seed task frames, frame-anchored triples,
validated graph files, mapping candidates, and human review artifacts.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import statistics
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape


DEFAULT_XLSX = Path("자이제_1.xlsx")
DEFAULT_METHODOLOGY = Path("layer2_fato_kg_methodology_eacl.md")
DEFAULT_OUTPUT_DIR = Path("experiments/fato_kg_zaize_20260703")
DEFAULT_LAYER1_DIR = Path("outputs/01_layer1")
RUN_DATE = "2026-07-03"

NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL_NS = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}


TASK_SEEDS = [
    {
        "frame_id": "L2_TASK_BID_CONTEXT_UNDERSTANDING",
        "canonical_task_name": "입찰·제안 환경 이해",
        "aliases": ["Bid and proposal context understanding", "입찰 환경 이해", "제안 환경 이해"],
        "task_type": "OpportunityAssessmentTask",
        "sections": ["1.1", "1.1.1", "1.1.2", "1.1.3", "1.1.4"],
        "keywords": ["입찰", "제안", "제안 역량", "경쟁력", "고객 니즈", "요구조건"],
        "cross_domain_pattern": "OpportunityContextUnderstanding",
    },
    {
        "frame_id": "L2_TASK_PROPOSAL_PROCESS_MANAGEMENT",
        "canonical_task_name": "제안 프로세스 관리",
        "aliases": ["Proposal process management", "제안 프로세스"],
        "task_type": "ProcessManagementTask",
        "sections": ["1.3", "1.3.1"],
        "keywords": ["제안 프로세스", "프로세스", "관리", "일정", "단계"],
        "cross_domain_pattern": "ProcessManagement",
    },
    {
        "frame_id": "L2_TASK_CAPTURE_PLANNING",
        "canonical_task_name": "수주영업",
        "aliases": ["Capture Planning", "Capture Plan", "비즈니스 개발"],
        "task_type": "InformationGatheringTask",
        "sections": ["1.3.2", "2.1"],
        "keywords": ["수주영업", "Capture Plan", "비즈니스 개발", "영업", "사전영업"],
        "cross_domain_pattern": "BusinessDevelopment",
    },
    {
        "frame_id": "L2_TASK_CAPTURE_INFORMATION_MANAGEMENT",
        "canonical_task_name": "영업 정보 관리",
        "aliases": ["Capture information management", "고객 정보 관리", "Account Plan"],
        "task_type": "InformationGatheringTask",
        "sections": ["2.1.3", "2.2.1"],
        "keywords": ["영업 정보", "고객 정보", "정보 관리", "Account Plan", "Capture Plan"],
        "cross_domain_pattern": "InformationManagement",
    },
    {
        "frame_id": "L2_TASK_CUSTOMER_NEEDS_ANALYSIS",
        "canonical_task_name": "고객 니즈 분석",
        "aliases": ["Customer needs analysis", "고객 요구조건 분석", "고객 이슈 분석"],
        "task_type": "RequirementAnalysisTask",
        "sections": ["1.1.1", "2.4.4", "3.1.3"],
        "keywords": ["고객 니즈", "고객의 니즈", "요구조건", "고객 이슈", "Needs"],
        "cross_domain_pattern": "RequirementAnalysis",
    },
    {
        "frame_id": "L2_TASK_UNSTATED_REQUIREMENT_DISCOVERY",
        "canonical_task_name": "비공식 요구조건 발굴",
        "aliases": ["Unstated requirement discovery", "숨은 요구조건 발굴"],
        "task_type": "RequirementAnalysisTask",
        "sections": ["1.1.1"],
        "keywords": ["비공식", "요구조건", "숨은", "빙산", "Unstated Requirement"],
        "cross_domain_pattern": "ImplicitRequirementDiscovery",
    },
    {
        "frame_id": "L2_TASK_VALUE_PROPOSITION",
        "canonical_task_name": "가치제안 개발",
        "aliases": ["Value proposition development", "고객 가치 제안"],
        "task_type": "StrategyDevelopmentTask",
        "sections": ["2.2.2"],
        "keywords": ["가치제안", "Value Proposition", "고객 가치", "효용", "가치"],
        "cross_domain_pattern": "ValuePropositionDevelopment",
    },
    {
        "frame_id": "L2_TASK_EVALUATOR_ANALYSIS",
        "canonical_task_name": "평가자 분석",
        "aliases": ["Evaluator analysis", "평가위원 분석"],
        "task_type": "StakeholderAnalysisTask",
        "sections": ["2.3.1", "2.3.2", "2.3.3", "2.3.4"],
        "keywords": ["평가자", "평가위원", "의사결정자", "영향자", "기술전문가", "사용자", "행정가"],
        "cross_domain_pattern": "StakeholderAnalysis",
    },
    {
        "frame_id": "L2_TASK_PURCHASE_STAGE_DIAGNOSIS",
        "canonical_task_name": "고객 구매단계 진단",
        "aliases": ["Purchase stage diagnosis", "구매단계 진단"],
        "task_type": "StakeholderAnalysisTask",
        "sections": ["2.4.1"],
        "keywords": ["구매단계", "구매 단계", "고객 단계", "의사결정 단계"],
        "cross_domain_pattern": "StakeholderStageDiagnosis",
    },
    {
        "frame_id": "L2_TASK_TRUST_BUILDING",
        "canonical_task_name": "신뢰도 관리",
        "aliases": ["Trust building", "신뢰 구축"],
        "task_type": "CommunicationTask",
        "sections": ["2.4.2"],
        "keywords": ["신뢰", "신뢰도", "관계", "관계구축", "투명성"],
        "cross_domain_pattern": "TrustBuilding",
    },
    {
        "frame_id": "L2_TASK_PERSUASIVE_COMMUNICATION",
        "canonical_task_name": "설득 커뮤니케이션 설계",
        "aliases": ["Persuasive communication design", "커뮤니케이션 설계"],
        "task_type": "CommunicationTask",
        "sections": ["2.4.3", "2.4.4", "2.4.5"],
        "keywords": ["커뮤니케이션", "설득", "소통", "메시지", "관점"],
        "cross_domain_pattern": "PersuasiveCommunication",
    },
    {
        "frame_id": "L2_TASK_PROPOSAL_STRATEGY_MANAGEMENT",
        "canonical_task_name": "제안전략 관리",
        "aliases": ["Proposal strategy management", "제안전략", "Proposal Strategy"],
        "task_type": "StrategyDevelopmentTask",
        "sections": ["3.1"],
        "keywords": ["제안전략", "전략", "Proposal Strategy", "전략 개발"],
        "cross_domain_pattern": "StrategyManagement",
    },
    {
        "frame_id": "L2_TASK_CUSTOMER_ISSUE_ANALYSIS",
        "canonical_task_name": "고객 이슈 분석",
        "aliases": ["Customer issue analysis", "핵심이슈 분석", "Hot buttons"],
        "task_type": "RequirementAnalysisTask",
        "sections": ["3.1.3"],
        "keywords": ["고객 이슈", "핵심이슈", "Hot buttons", "이슈"],
        "cross_domain_pattern": "IssueAnalysis",
    },
    {
        "frame_id": "L2_TASK_COMPETITOR_ANALYSIS",
        "canonical_task_name": "경쟁사 분석",
        "aliases": ["Competitor analysis", "경쟁자 분석"],
        "task_type": "StrategyDevelopmentTask",
        "sections": ["3.1.4"],
        "keywords": ["경쟁사", "경쟁자", "경쟁사 분석", "경쟁자의 강점", "경쟁자의 약점"],
        "cross_domain_pattern": "CompetitiveAnalysis",
    },
    {
        "frame_id": "L2_TASK_DIFFERENTIATOR_IDENTIFICATION",
        "canonical_task_name": "차별화 요소 규명",
        "aliases": ["Differentiator identification", "핵심 차별화요소 규명"],
        "task_type": "StrategyDevelopmentTask",
        "sections": ["3.1.4"],
        "keywords": ["차별화", "차별화 요소", "핵심 차별화요소", "Discriminator", "차별성"],
        "cross_domain_pattern": "DifferentiatorIdentification",
    },
    {
        "frame_id": "L2_TASK_STRATEGY_STATEMENT_WRITING",
        "canonical_task_name": "전략기술서 작성",
        "aliases": ["Strategy statement writing", "전략 기술서"],
        "task_type": "ArtifactAuthoringTask",
        "sections": ["3.2.2"],
        "keywords": ["전략기술서", "전략 기술서", "Theme Statement", "작성"],
        "cross_domain_pattern": "StrategyArtifactAuthoring",
    },
    {
        "frame_id": "L2_TASK_TACTIC_DEVELOPMENT",
        "canonical_task_name": "전술개발",
        "aliases": ["Tactic development", "전술 개발"],
        "task_type": "StrategyDevelopmentTask",
        "sections": ["3.2.3", "3.2.4"],
        "keywords": ["전술", "전술개발", "전술 개발", "tactic"],
        "cross_domain_pattern": "TacticDevelopment",
    },
    {
        "frame_id": "L2_TASK_SOLUTION_OPTIMIZATION",
        "canonical_task_name": "솔루션 최적화",
        "aliases": ["Solution optimization", "솔루션 개발"],
        "task_type": "StrategyDevelopmentTask",
        "sections": ["3.2.4"],
        "keywords": ["솔루션", "최적화", "Solution", "대안"],
        "cross_domain_pattern": "SolutionOptimization",
    },
    {
        "frame_id": "L2_TASK_COMMUNICATION_METHOD_DEVELOPMENT",
        "canonical_task_name": "커뮤니케이션 방법 개발",
        "aliases": ["Communication method development", "메시지 전달 방법 개발"],
        "task_type": "CommunicationTask",
        "sections": ["3.2.4"],
        "keywords": ["커뮤니케이션 방법", "전달", "메시지", "표현", "소통"],
        "cross_domain_pattern": "CommunicationMethodDevelopment",
    },
    {
        "frame_id": "L2_TASK_STRATEGY_VALIDATION",
        "canonical_task_name": "전략 효과성 검증",
        "aliases": ["Strategy validation", "전략 검증"],
        "task_type": "ReviewTask",
        "sections": ["3.2.3", "3.2.5"],
        "keywords": ["효과성", "검증", "리뷰", "테스트", "타당성"],
        "cross_domain_pattern": "StrategyValidation",
    },
    {
        "frame_id": "L2_TASK_POSITION_STRATEGY_SELECTION",
        "canonical_task_name": "1등·2등 전략 선택",
        "aliases": ["Position strategy selection", "1등 전략", "2등 전략"],
        "task_type": "DecisionTask",
        "sections": ["3.3.1"],
        "keywords": ["1등 전략", "2등 전략", "선택", "전략 선택"],
        "cross_domain_pattern": "PositionStrategySelection",
    },
    {
        "frame_id": "L2_TASK_DIRECT_INDIRECT_STRATEGY_SELECTION",
        "canonical_task_name": "정공법·역공법 선택",
        "aliases": ["Direct/indirect strategy selection", "정공법", "역공법"],
        "task_type": "DecisionTask",
        "sections": ["3.3.2"],
        "keywords": ["정공법", "역공법", "공략", "우회"],
        "cross_domain_pattern": "DirectIndirectStrategySelection",
    },
    {
        "frame_id": "L2_TASK_RISK_MANAGEMENT",
        "canonical_task_name": "리스크 관리",
        "aliases": ["Risk management", "제안 리스크 관리"],
        "task_type": "RiskAssessmentTask",
        "sections": ["3.3.3"],
        "keywords": ["리스크", "위험", "실패", "약점", "위협", "Risk"],
        "cross_domain_pattern": "RiskManagement",
    },
    {
        "frame_id": "L2_TASK_PROPOSAL_PLANNING",
        "canonical_task_name": "제안서 기획",
        "aliases": ["Proposal planning", "제안 기획"],
        "task_type": "ArtifactAuthoringTask",
        "sections": ["1.3.3"],
        "keywords": ["제안서 기획", "Proposal Planning", "기획", "목차", "스토리보드"],
        "cross_domain_pattern": "ArtifactPlanning",
    },
    {
        "frame_id": "L2_TASK_PROPOSAL_WRITING_MILESTONE",
        "canonical_task_name": "제안서 작성 단계 관리",
        "aliases": ["Proposal writing milestone management", "제안서 작성"],
        "task_type": "ArtifactAuthoringTask",
        "sections": ["1.3.4"],
        "keywords": ["제안서 작성", "작성 단계", "작성자", "마감", "초안"],
        "cross_domain_pattern": "ArtifactAuthoringMilestone",
    },
    {
        "frame_id": "L2_TASK_PRESENTATION_PREPARATION",
        "canonical_task_name": "프레젠테이션 준비",
        "aliases": ["Presentation preparation", "PT 준비"],
        "task_type": "CommunicationTask",
        "sections": ["1.3.5"],
        "keywords": ["프레젠테이션", "PT", "발표", "질의응답", "슬라이드"],
        "cross_domain_pattern": "PresentationPreparation",
    },
]


RELATION_SCHEMA = {
    "HAS_TASK": (["Process"], ["Task"]),
    "HAS_SUBTASK": (["Task"], ["Task"]),
    "HAS_STEP": (["Task"], ["Step"]),
    "PRECEDES": (["Task", "Step"], ["Task", "Step"]),
    "TRIGGERED_BY": (["Task"], ["Condition", "Event"]),
    "USES_INPUT": (["Task", "Step"], ["Artifact", "InputArtifact", "InformationItem", "Concept"]),
    "PRODUCES": (["Task", "Step"], ["Artifact", "OutputArtifact", "StrategyArtifact", "Checklist", "Report", "StrategyElement"]),
    "PERFORMED_BY": (["Task", "Step"], ["Role"]),
    "ACCOUNTABLE_TO": (["Task", "Step"], ["Role", "Stakeholder"]),
    "ANALYZES": (["Task", "Step"], ["Concept", "Artifact", "InformationItem", "Stakeholder", "EvaluationCriterion", "StrategyElement"]),
    "DEVELOPS": (["Task", "Step"], ["Artifact", "StrategyArtifact", "StrategyElement", "Concept"]),
    "EVALUATES": (["Task", "Step"], ["EvaluationCriterion", "Artifact", "Concept"]),
    "DECIDES": (["Task", "Gate"], ["DecisionPoint"]),
    "HAS_DECISION_POINT": (["Task"], ["DecisionPoint"]),
    "HAS_CONDITION": (["Task", "Rule"], ["Condition"]),
    "HAS_CONSTRAINT": (["Task", "Artifact"], ["Constraint"]),
    "HAS_RISK": (["Task", "Artifact"], ["Risk"]),
    "MITIGATES": (["Task", "Control"], ["Risk"]),
    "HAS_PRINCIPLE": (["Task"], ["Principle"]),
    "MAY_RESULT_IN": (["Risk", "Condition", "Task"], ["Risk", "Outcome", "Concept"]),
    "EVIDENCED_BY": (None, ["EvidenceSpan"]),
    "MENTIONED_IN": (None, ["EvidenceSpan"]),
    "MAPS_TO": (["Task"], ["StandardNode", "NCSCompetencyUnit", "PCFElement"]),
    "REQUIRES_CAPABILITY": (["Task"], ["NCSCompetencyUnit", "StandardNode"]),
    "PROCESS_CONTEXT": (["Task"], ["PCFElement", "StandardNode"]),
}


ENTITY_LEXICON = [
    ("Artifact", "제안 요청서", ["제안 요청서", "제안요청서", "RFP"]),
    ("Artifact", "Capture Plan", ["Capture Plan", "캡처플랜", "영업 정보"]),
    ("StrategyArtifact", "수주전략", ["수주전략", "Capture Strategy", "Win Strategy"]),
    ("StrategyArtifact", "제안전략", ["제안전략", "Proposal Strategy"]),
    ("StrategyArtifact", "전략기술서", ["전략기술서", "전략 기술서"]),
    ("Artifact", "제안관리계획서", ["Proposal Management Plan", "PMP", "제안계획서", "제안관리계획"]),
    ("Artifact", "제안서 목차", ["목차", "제안서 목차"]),
    ("Artifact", "섹션기획서", ["섹션기획서", "PDW", "스토리보드", "Storyboard"]),
    ("Artifact", "제안서", ["제안서"]),
    ("Artifact", "제안요약", ["제안요약", "Executive Summary"]),
    ("Checklist", "충실도 체크리스트", ["충실도 체크리스트", "체크리스트"]),
    ("Artifact", "프레젠테이션 자료", ["프레젠테이션", "PT", "발표자료", "슬라이드"]),
    ("InformationItem", "고객 니즈", ["고객 니즈", "고객의 니즈", "Needs"]),
    ("InformationItem", "공식 요구조건", ["공식적인 요구조건", "공식 요구조건", "요구조건"]),
    ("InformationItem", "비공식 요구조건", ["비공식적인 요구조건", "비공식 요구조건", "Unstated Requirement"]),
    ("InformationItem", "고객 정보", ["고객 정보", "Account Plan"]),
    ("InformationItem", "경쟁사 정보", ["경쟁사 정보", "경쟁자의", "경쟁사"]),
    ("EvaluationCriterion", "평가 기준", ["평가 기준", "평가항목", "Evaluation Factor", "점수"]),
    ("StrategyElement", "차별화 요소", ["차별화 요소", "핵심 차별화요소", "Discriminator", "차별성"]),
    ("StrategyElement", "고객 가치", ["고객 가치", "가치제안", "Value Proposition", "효용"]),
    ("Stakeholder", "고객", ["고객", "발주처", "구매자"]),
    ("Stakeholder", "평가자", ["평가자", "평가위원"]),
    ("Stakeholder", "의사결정자", ["의사결정자", "Decision maker"]),
    ("Stakeholder", "영향자", ["영향자", "Influencer"]),
    ("Stakeholder", "기술전문가", ["기술전문가", "전문가"]),
    ("Role", "영업대표", ["영업대표", "영업팀"]),
    ("Role", "제안 PM", ["제안 PM", "Proposal Manager", "PM"]),
    ("Role", "제안팀", ["제안팀", "작성팀"]),
    ("Role", "작성자", ["작성자", "Writer"]),
    ("Role", "리뷰팀", ["리뷰팀", "Core Team", "Red Team", "Blue Team", "Pink Team"]),
    ("DecisionPoint", "Bid/No Bid Decision", ["Bid/No Bid", "제안참여 의사결정", "참여결정"]),
    ("DecisionPoint", "입찰타당성 결정", ["입찰타당성", "Bid Validation"]),
    ("DecisionPoint", "1등·2등 전략 선택", ["1등 전략", "2등 전략"]),
    ("DecisionPoint", "정공법·역공법 선택", ["정공법", "역공법"]),
    ("Risk", "경쟁사 우위", ["경쟁사의 강점", "경쟁자", "경쟁우위"]),
    ("Risk", "요구조건 누락", ["누락", "불충실", "요구조건"]),
    ("Risk", "가격 불리", ["가격", "비싸", "불리"]),
    ("Risk", "제안 실패", ["실패", "위험", "리스크", "Risk"]),
    ("Principle", "고객 중심", ["고객 중심", "고객 관점", "고객의 관점"]),
    ("Principle", "충실도", ["충실도", "Compliance"]),
    ("Principle", "차별화", ["차별화", "강점", "차별성"]),
    ("Principle", "근거 기반 설득", ["근거", "논리", "설득"]),
    ("Principle", "간결하고 명확한 표현", ["간결", "명확", "표현"]),
    ("Condition", "RFP 수신", ["RFP", "제안 요청서", "요청서"]),
    ("Condition", "제출기한", ["제출기한", "마감", "일정"]),
    ("Constraint", "평가 기준", ["평가 기준", "평가항목"]),
    ("Constraint", "제출 요구조건", ["제출", "요구조건"]),
    ("Concept", "고객 이슈", ["고객 이슈", "핵심이슈", "Hot buttons"]),
    ("Concept", "솔루션", ["솔루션", "Solution"]),
    ("Concept", "메시지", ["메시지", "주제문", "Theme Statement"]),
]


SUBTASK_LINKS = {
    "L2_TASK_PROPOSAL_STRATEGY_MANAGEMENT": [
        "L2_TASK_CUSTOMER_ISSUE_ANALYSIS",
        "L2_TASK_COMPETITOR_ANALYSIS",
        "L2_TASK_DIFFERENTIATOR_IDENTIFICATION",
        "L2_TASK_STRATEGY_STATEMENT_WRITING",
    ],
    "L2_TASK_CAPTURE_PLANNING": [
        "L2_TASK_CAPTURE_INFORMATION_MANAGEMENT",
        "L2_TASK_CUSTOMER_NEEDS_ANALYSIS",
        "L2_TASK_BID_CONTEXT_UNDERSTANDING",
    ],
    "L2_TASK_PROPOSAL_PROCESS_MANAGEMENT": [
        "L2_TASK_CAPTURE_PLANNING",
        "L2_TASK_PROPOSAL_PLANNING",
        "L2_TASK_PROPOSAL_WRITING_MILESTONE",
        "L2_TASK_PRESENTATION_PREPARATION",
    ],
    "L2_TASK_TACTIC_DEVELOPMENT": [
        "L2_TASK_SOLUTION_OPTIMIZATION",
        "L2_TASK_COMMUNICATION_METHOD_DEVELOPMENT",
        "L2_TASK_STRATEGY_VALIDATION",
    ],
}

PRECEDENCE_CHAIN = [
    "L2_TASK_BID_CONTEXT_UNDERSTANDING",
    "L2_TASK_CAPTURE_PLANNING",
    "L2_TASK_CAPTURE_INFORMATION_MANAGEMENT",
    "L2_TASK_CUSTOMER_NEEDS_ANALYSIS",
    "L2_TASK_EVALUATOR_ANALYSIS",
    "L2_TASK_PROPOSAL_STRATEGY_MANAGEMENT",
    "L2_TASK_COMPETITOR_ANALYSIS",
    "L2_TASK_DIFFERENTIATOR_IDENTIFICATION",
    "L2_TASK_STRATEGY_STATEMENT_WRITING",
    "L2_TASK_PROPOSAL_PLANNING",
    "L2_TASK_PROPOSAL_WRITING_MILESTONE",
    "L2_TASK_PRESENTATION_PREPARATION",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def sha1_short(text: str, n: int = 12) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:n].upper()


def stable_node_id(node_type: str, label: str) -> str:
    prefix = re.sub(r"[^A-Za-z0-9]+", "_", node_type.upper()).strip("_")
    return f"L2_{prefix}_{sha1_short(label, 10)}"


def normalize_float_int(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        number = float(text)
        if number.is_integer():
            return str(int(number))
    except Exception:
        pass
    return text


def normalize_section(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    parts = []
    for part in text.split("."):
        if not part:
            continue
        try:
            number = float(part)
            if number.is_integer():
                parts.append(str(int(number)))
            else:
                parts.append(part)
        except Exception:
            parts.append(part)
    return ".".join(parts) if parts else text


def section_slug(section_no: str) -> str:
    return re.sub(r"[^A-Za-z0-9가-힣]+", "_", section_no or "UNASSIGNED").strip("_") or "UNASSIGNED"


def col_index(cell_ref: str) -> int:
    match = re.match(r"([A-Z]+)", cell_ref)
    if not match:
        return 0
    idx = 0
    for ch in match.group(1):
        idx = idx * 26 + ord(ch) - 64
    return idx - 1


def read_xlsx_table(path: Path) -> tuple[str, list[dict[str, Any]]]:
    with zipfile.ZipFile(path) as zf:
        workbook = ET.fromstring(zf.read("xl/workbook.xml"))
        sheet = workbook.find(".//a:sheet", NS)
        sheet_name = sheet.attrib.get("name", "Sheet1") if sheet is not None else "Sheet1"
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in zf.namelist():
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for item in root.findall("a:si", NS):
                shared_strings.append("".join(t.text or "" for t in item.findall(".//a:t", NS)))

        worksheet_name = "xl/worksheets/sheet1.xml"
        root = ET.fromstring(zf.read(worksheet_name))
        raw_rows: list[tuple[int, list[str]]] = []
        for row in root.findall(".//a:sheetData/a:row", NS):
            row_index = int(float(row.attrib.get("r", len(raw_rows) + 1)))
            cells: dict[int, str] = {}
            for cell in row.findall("a:c", NS):
                idx = col_index(cell.attrib.get("r", "A"))
                cell_type = cell.attrib.get("t")
                val_node = cell.find("a:v", NS)
                value = ""
                if cell_type == "s" and val_node is not None:
                    value = shared_strings[int(val_node.text or "0")]
                elif cell_type == "inlineStr":
                    value = "".join(t.text or "" for t in cell.findall(".//a:t", NS))
                elif val_node is not None:
                    value = val_node.text or ""
                cells[idx] = value
            if cells:
                raw_rows.append((row_index, [cells.get(i, "") for i in range(max(cells) + 1)]))
    if not raw_rows:
        raise ValueError(f"No rows found in {path}")
    header = [str(value).strip() for value in raw_rows[0][1]]
    rows: list[dict[str, Any]] = []
    for excel_row, values in raw_rows[1:]:
        record = {header[i]: values[i] if i < len(values) else "" for i in range(len(header))}
        record["_excel_row"] = excel_row
        rows.append(record)
    return sheet_name, rows


def classify_modality(text: str) -> str:
    stripped = text.strip()
    if re.search(r"표\s*\d|평가\s*시트|점수[:：]|총계", stripped):
        return "table"
    if re.search(r"그림\s*\d|도표|Figure", stripped, re.I):
        return "figure_caption"
    if re.match(r"^[①②③④⑤⑥⑦⑧⑨0-9]+[.)]", stripped) or "•" in stripped:
        return "list"
    if "예시" in stripped or "사례" in stripped:
        return "example"
    if "정의" in stripped or "이란" in stripped or "의미한다" in stripped:
        return "definition"
    return "prose"


def classify_modality_for_triple(text: str) -> str:
    if "하지 말" in text or "안 된다" in text or "주의" in text:
        return "warning"
    if "예시" in text or "사례" in text:
        return "example"
    if "해야" in text or "하라" in text or "중요" in text or "필요" in text:
        return "normative"
    if "이란" in text or "의미" in text:
        return "definition"
    if "대부분" in text or "일반" in text or "흔히" in text:
        return "heuristic"
    return "descriptive"


def classify_scope(text: str, task_id: str) -> str:
    if "예시" in text or "사례" in text:
        return "example_only"
    if task_id in {
        "L2_TASK_CUSTOMER_NEEDS_ANALYSIS",
        "L2_TASK_COMPETITOR_ANALYSIS",
        "L2_TASK_RISK_MANAGEMENT",
        "L2_TASK_PROPOSAL_STRATEGY_MANAGEMENT",
    }:
        return "task_specific"
    if "NCS" in text or "PCF" in text or "표준" in text:
        return "mapping_hint"
    if "해야" in text or "중요" in text or "하라" in text:
        return "domain_principle"
    return "source_claim"


def text_contains(text: str, keywords: list[str]) -> bool:
    low = text.lower()
    return any(keyword.lower() in low for keyword in keywords if keyword)


def count_keyword_hits(text: str, keywords: list[str]) -> int:
    low = text.lower()
    return sum(low.count(keyword.lower()) for keyword in keywords if keyword)


def infer_process(task: dict[str, Any]) -> str:
    sections = task.get("sections") or []
    if any(str(s).startswith("1.") for s in sections):
        return "PROCESS_PROPOSAL_OVERVIEW"
    if any(str(s).startswith("2.") for s in sections):
        return "PROCESS_CAPTURE_SALES"
    if any(str(s).startswith("3.") for s in sections):
        return "PROCESS_PROPOSAL_STRATEGY"
    return "PROCESS_BID_PROPOSAL"


def default_definition(task: dict[str, Any]) -> str:
    name = task["canonical_task_name"]
    task_type = task["task_type"]
    return f"{name}은(는) 수주·제안 도메인에서 {task_type} 패턴으로 수행되는 업무 단위이며, 관련 입력·산출물·역할·리스크·원칙을 evidence에 근거해 관리한다."


def make_evidence_units(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    section_counters: Counter[str] = Counter()
    for idx, row in enumerate(rows, start=1):
        text = str(row.get("text_for_llm_human") or "").strip()
        if not text:
            continue
        page = normalize_float_int(row.get("page"))
        chapter_no = normalize_float_int(row.get("chapter_no"))
        section_no = normalize_section(row.get("section_no"))
        section_key = f"{chapter_no}|{section_no}|{row.get('section_title') or ''}"
        section_counters[section_key] += 1
        page_part = f"P{int(page):03d}" if page.isdigit() else "PUNK"
        section_part = section_slug(section_no)
        evidence_id = f"EV_ZAIZE_{page_part}_S{section_part}_{section_counters[section_key]:04d}"
        missing_meta = not chapter_no or not section_no or not row.get("section_title")
        evidence.append(
            {
                "evidence_id": evidence_id,
                "source_document_id": "DOC_ZAIZE_001",
                "source_file": str(DEFAULT_XLSX),
                "source_sheet": "clean_sentences",
                "source_excel_row": row.get("_excel_row"),
                "page": int(page) if page.isdigit() else None,
                "chapter_no": int(chapter_no) if chapter_no.isdigit() else None,
                "chapter_title": str(row.get("chapter_title") or "").strip(),
                "section_no": section_no,
                "section_title": str(row.get("section_title") or "").strip(),
                "text": text,
                "char_start": None,
                "char_end": None,
                "evidence_modality": classify_modality(text),
                "needs_context_imputation": missing_meta,
                "source_type": "ocr_clean_sentence",
                "review_status": "source_evidence_unreviewed",
            }
        )
    profile = build_source_profile(rows, evidence)
    return evidence, profile


def build_source_profile(rows: list[dict[str, Any]], evidence: list[dict[str, Any]]) -> dict[str, Any]:
    valid = evidence
    chapter_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    section_groups: dict[tuple[Any, str, str], list[dict[str, Any]]] = defaultdict(list)
    for ev in valid:
        chapter_groups[str(ev.get("chapter_no") or "")].append(ev)
        section_groups[(ev.get("chapter_no"), ev.get("section_no") or "", ev.get("section_title") or "")].append(ev)
    chapter_rows = []
    for chapter, rows_for_chapter in sorted(chapter_groups.items(), key=lambda item: (999 if not item[0] else int(item[0]), item[0])):
        pages = [row["page"] for row in rows_for_chapter if row.get("page") is not None]
        section_count = len({(row.get("section_no"), row.get("section_title")) for row in rows_for_chapter})
        title = next((row.get("chapter_title") for row in rows_for_chapter if row.get("chapter_title")), "")
        chapter_rows.append(
            {
                "chapter_no": chapter,
                "chapter_title": title,
                "sentence_rows": len(rows_for_chapter),
                "section_count": section_count,
                "page_min": min(pages) if pages else None,
                "page_max": max(pages) if pages else None,
            }
        )
    pages = [row["page"] for row in valid if row.get("page") is not None]
    missing = [row for row in valid if row.get("needs_context_imputation")]
    return {
        "generated_at_utc": now_iso(),
        "source_file": str(DEFAULT_XLSX),
        "methodology_file": str(DEFAULT_METHODOLOGY),
        "sheet": "clean_sentences",
        "physical_rows": len(rows),
        "valid_sentence_rows": len(valid),
        "chapter_count": len([key for key in chapter_groups if key]),
        "section_count_including_missing": len(section_groups),
        "section_count_with_metadata": len([key for key in section_groups if key[0] and key[1] and key[2]]),
        "page_min": min(pages) if pages else None,
        "page_max": max(pages) if pages else None,
        "missing_structure_metadata_sentences": len(missing),
        "chapter_profile": chapter_rows,
        "evidence_modality_counts": dict(Counter(row["evidence_modality"] for row in valid)),
        "claim_status": "source_profile_ready_not_human_gold",
    }


def make_chunks(evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, str, str], list[dict[str, Any]]] = defaultdict(list)
    for ev in evidence:
        key = (ev.get("chapter_no"), ev.get("section_no") or "", ev.get("section_title") or "")
        groups[key].append(ev)
    chunks = []
    for idx, (key, evs) in enumerate(groups.items(), start=1):
        chapter_no, section_no, section_title = key
        pages = [ev["page"] for ev in evs if ev.get("page") is not None]
        chunk_id = f"CH_ZAIZE_{section_slug(section_no)}_{idx:03d}"
        chunks.append(
            {
                "chunk_id": chunk_id,
                "source_document_id": "DOC_ZAIZE_001",
                "chapter_no": chapter_no,
                "chapter_title": next((ev.get("chapter_title") for ev in evs if ev.get("chapter_title")), ""),
                "section_no": section_no,
                "section_title": section_title,
                "page_min": min(pages) if pages else None,
                "page_max": max(pages) if pages else None,
                "evidence_ids": [ev["evidence_id"] for ev in evs],
                "evidence_count": len(evs),
                "chunk_text": "\n".join(ev["text"] for ev in evs),
                "chunk_type": "section_chunk" if section_no else "needs_context_imputation_chunk",
                "char_len": sum(len(ev["text"]) for ev in evs),
                "review_status": "chunk_unreviewed",
            }
        )
    return chunks


def task_chunk_score(task: dict[str, Any], chunk: dict[str, Any]) -> float:
    score = 0.0
    section_no = str(chunk.get("section_no") or "")
    sections = task.get("sections") or []
    if section_no in sections:
        score += 6.0
    elif any(section_no.startswith(f"{section}.") or section.startswith(f"{section_no}.") for section in sections if section_no):
        score += 3.0
    score += min(5, count_keyword_hits(chunk.get("chunk_text", ""), task.get("keywords") or []))
    return score


def build_task_catalog(chunks: list[dict[str, Any]], evidence_by_id: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, list[str]]]:
    candidates = []
    catalog = []
    alias_dict: dict[str, list[str]] = {}
    for seed in TASK_SEEDS:
        scored_chunks = [(task_chunk_score(seed, chunk), chunk) for chunk in chunks]
        matched = [chunk for score, chunk in scored_chunks if score > 0]
        matched = sorted(matched, key=lambda chunk: (chunk.get("chapter_no") or 999, chunk.get("section_no") or "", chunk.get("chunk_id")))[:8]
        evidence_sections = []
        evidence_ids = []
        for chunk in matched:
            evidence_sections.append(
                {
                    "chapter": chunk.get("chapter_no"),
                    "section_no": chunk.get("section_no"),
                    "section_title": chunk.get("section_title"),
                    "chunk_id": chunk.get("chunk_id"),
                    "page_min": chunk.get("page_min"),
                    "page_max": chunk.get("page_max"),
                }
            )
            evidence_ids.extend(chunk.get("evidence_ids", [])[:2])
        evidence_ids = list(dict.fromkeys(evidence_ids))[:10]
        confidence = round(min(0.95, 0.58 + 0.03 * len(matched) + 0.01 * len(evidence_ids)), 3)
        frame = {
            "frame_id": seed["frame_id"],
            "domain": "bid_proposal",
            "canonical_task_name": seed["canonical_task_name"],
            "aliases": seed["aliases"],
            "task_type": seed["task_type"],
            "definition": default_definition(seed),
            "parent_process": infer_process(seed),
            "preconditions": infer_preconditions(seed),
            "inputs": infer_slot_entities(seed, "input"),
            "outputs": infer_slot_entities(seed, "output"),
            "roles": infer_slot_entities(seed, "role"),
            "subtasks": [task_id_to_name(tid) for tid in SUBTASK_LINKS.get(seed["frame_id"], [])],
            "next_tasks": next_tasks_for(seed["frame_id"]),
            "decision_points": infer_slot_entities(seed, "decision"),
            "risks": infer_slot_entities(seed, "risk"),
            "principles": infer_slot_entities(seed, "principle"),
            "success_criteria": infer_success_criteria(seed),
            "evidence_sections": evidence_sections,
            "evidence_ids": evidence_ids,
            "cross_domain_pattern": seed["cross_domain_pattern"],
            "confidence": confidence,
            "source": "seed_catalog_rule_based_from_layer2_fato_methodology",
            "review_status": "needs_human_review",
        }
        candidates.append(
            {
                **frame,
                "candidate_status": "accepted_seed_candidate",
                "candidate_reason": "Listed in layer2_fato_kg_methodology_eacl.md seed task catalog and supported by matched evidence sections.",
            }
        )
        catalog.append(frame)
        alias_dict[seed["canonical_task_name"]] = seed["aliases"]
    return candidates, catalog, alias_dict


def task_id_to_name(task_id: str) -> str:
    for task in TASK_SEEDS:
        if task["frame_id"] == task_id:
            return task["canonical_task_name"]
    return task_id


def next_tasks_for(task_id: str) -> list[str]:
    out = []
    for i, current in enumerate(PRECEDENCE_CHAIN[:-1]):
        if current == task_id:
            out.append(task_id_to_name(PRECEDENCE_CHAIN[i + 1]))
    return out


def infer_preconditions(task: dict[str, Any]) -> list[str]:
    name = task["canonical_task_name"]
    if "전략" in name:
        return ["고객 니즈 또는 요구조건 정보가 존재함", "경쟁사 또는 평가 기준 정보가 존재함"]
    if "제안서" in name:
        return ["제안전략 또는 요구조건 정보가 존재함"]
    if "평가자" in name or "고객" in name:
        return ["고객 또는 평가자 관련 정보가 수집됨"]
    if "리스크" in name:
        return ["사업 기회와 경쟁 상황이 식별됨"]
    return ["관련 문서 evidence가 존재함"]


def infer_slot_entities(task: dict[str, Any], slot: str) -> list[dict[str, str]]:
    name = task["canonical_task_name"]
    task_id = task["frame_id"]
    slots = {
        "input": [],
        "output": [],
        "role": [],
        "decision": [],
        "risk": [],
        "principle": [],
    }
    if "고객" in name or "요구" in name or "이슈" in name:
        slots["input"].extend([{"name": "고객 정보", "type": "InformationItem"}, {"name": "제안 요청서", "type": "Artifact"}])
        slots["output"].append({"name": "고객 니즈", "type": "InformationItem"})
        slots["principle"].append({"name": "고객 중심", "type": "Principle"})
    if "경쟁" in name or "차별화" in name:
        slots["input"].append({"name": "경쟁사 정보", "type": "InformationItem"})
        slots["output"].append({"name": "차별화 요소", "type": "StrategyElement"})
        slots["risk"].append({"name": "경쟁사 우위", "type": "Risk"})
    if "전략" in name or task["task_type"] == "StrategyDevelopmentTask":
        slots["input"].extend([{"name": "고객 니즈", "type": "InformationItem"}, {"name": "평가 기준", "type": "EvaluationCriterion"}])
        slots["output"].append({"name": "제안전략", "type": "StrategyArtifact"})
        slots["role"].extend([{"name": "영업대표", "type": "Role"}, {"name": "제안 PM", "type": "Role"}])
    if "제안서" in name:
        slots["input"].extend([{"name": "제안전략", "type": "StrategyArtifact"}, {"name": "제안 요청서", "type": "Artifact"}])
        slots["output"].append({"name": "제안서", "type": "Artifact"})
        slots["role"].extend([{"name": "제안 PM", "type": "Role"}, {"name": "작성자", "type": "Role"}])
    if "프레젠테이션" in name:
        slots["input"].append({"name": "제안서", "type": "Artifact"})
        slots["output"].append({"name": "프레젠테이션 자료", "type": "Artifact"})
        slots["role"].append({"name": "발표자", "type": "Role"})
    if "리스크" in name:
        slots["input"].append({"name": "경쟁사 정보", "type": "InformationItem"})
        slots["output"].append({"name": "리스크 완화 방안", "type": "StrategyElement"})
        slots["risk"].append({"name": "제안 실패", "type": "Risk"})
    if task_id in {"L2_TASK_POSITION_STRATEGY_SELECTION", "L2_TASK_DIRECT_INDIRECT_STRATEGY_SELECTION"}:
        slots["decision"].append({"name": name, "type": "DecisionPoint"})
    if task_id in {"L2_TASK_BID_CONTEXT_UNDERSTANDING", "L2_TASK_CAPTURE_PLANNING"}:
        slots["decision"].append({"name": "Bid/No Bid Decision", "type": "DecisionPoint"})
    if not slots["role"]:
        slots["role"].append({"name": "제안팀", "type": "Role"})
    return slots.get(slot, [])


def infer_success_criteria(task: dict[str, Any]) -> list[str]:
    name = task["canonical_task_name"]
    criteria = ["관련 evidence에 근거한 입력·산출물·원칙이 명확히 연결됨"]
    if "전략" in name:
        criteria.append("고객 니즈와 차별화 요소가 전략 산출물에 반영됨")
    if "제안서" in name:
        criteria.append("요구조건 충족과 고객 관점 메시지가 산출물에 반영됨")
    if "리스크" in name:
        criteria.append("식별된 리스크와 완화 방안이 함께 제시됨")
    return criteria


def best_tasks_for_evidence(ev: dict[str, Any], catalog: list[dict[str, Any]], max_tasks: int = 2) -> list[tuple[float, dict[str, Any]]]:
    fake_chunk = {
        "section_no": ev.get("section_no"),
        "chunk_text": ev.get("text", ""),
        "chapter_no": ev.get("chapter_no"),
    }
    seed_by_id = {task["frame_id"]: task for task in TASK_SEEDS}
    scored = []
    for frame in catalog:
        seed = seed_by_id.get(frame["frame_id"], frame)
        score = task_chunk_score(seed, fake_chunk)
        if score > 0:
            scored.append((score, frame))
    scored.sort(key=lambda item: (-item[0], item[1]["frame_id"]))
    return scored[:max_tasks]


def choose_predicate(node_type: str, text: str, task: dict[str, Any]) -> str:
    produce_cues = ["작성", "수립", "개발", "도출", "만들", "생성", "산출", "제시", "규명"]
    input_cues = ["활용", "사용", "기반", "분석", "검토", "파악", "수집", "포함"]
    if node_type in {"Artifact", "StrategyArtifact", "Checklist", "Report", "StrategyElement"}:
        if any(cue in text for cue in produce_cues):
            return "PRODUCES"
        if any(cue in text for cue in input_cues):
            return "USES_INPUT"
        if task["task_type"] in {"ArtifactAuthoringTask", "StrategyDevelopmentTask"}:
            return "PRODUCES"
        return "USES_INPUT"
    if node_type == "InformationItem":
        return "ANALYZES" if "분석" in task["canonical_task_name"] or "분석" in text else "USES_INPUT"
    if node_type == "Stakeholder":
        return "ANALYZES" if task["task_type"] in {"StakeholderAnalysisTask", "RequirementAnalysisTask"} else "ACCOUNTABLE_TO"
    if node_type == "Role":
        return "PERFORMED_BY"
    if node_type == "DecisionPoint":
        return "HAS_DECISION_POINT"
    if node_type == "Risk":
        if any(cue in text for cue in ["완화", "극복", "최소화", "관리", "활용"]):
            return "MITIGATES"
        return "HAS_RISK"
    if node_type == "Principle":
        return "HAS_PRINCIPLE"
    if node_type == "Condition":
        return "TRIGGERED_BY"
    if node_type == "Constraint":
        return "HAS_CONSTRAINT"
    if node_type == "EvaluationCriterion":
        return "EVALUATES"
    return "ANALYZES"


def validation_status(triple: dict[str, Any], node_types: dict[str, str], evidence_by_id: dict[str, dict[str, Any]]) -> tuple[str, list[str]]:
    issues = []
    predicate = triple.get("predicate")
    if predicate not in RELATION_SCHEMA:
        issues.append("predicate_not_allowed")
    evidence_ids = triple.get("evidence_ids") or []
    if not evidence_ids:
        issues.append("missing_evidence")
    quote = triple.get("evidence_quote") or ""
    for ev_id in evidence_ids:
        text = (evidence_by_id.get(ev_id) or {}).get("text", "")
        if quote and quote not in text:
            issues.append("evidence_quote_not_substring")
            break
    subject_type = triple.get("subject_type")
    object_type = triple.get("object_type")
    domain_range = RELATION_SCHEMA.get(predicate)
    if domain_range:
        allowed_subjects, allowed_objects = domain_range
        if allowed_subjects is not None and subject_type not in allowed_subjects:
            issues.append(f"domain_violation:{subject_type}->{predicate}")
        if object_type not in allowed_objects:
            issues.append(f"range_violation:{predicate}->{object_type}")
    confidence = float(triple.get("confidence") or 0.0)
    if issues:
        return "rejected_" + issues[0], issues
    if confidence < 0.80:
        return "needs_review_low_confidence", ["confidence_below_auto_accept"]
    if triple.get("scope") == "example_only":
        return "needs_review_example_scope", ["example_scope_not_promoted"]
    return "verified", []


def build_triples(
    evidence: list[dict[str, Any]],
    catalog: list[dict[str, Any]],
    evidence_by_id: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    raw: list[dict[str, Any]] = []
    edge_seq = 0
    for ev in evidence:
        text = ev["text"]
        best_tasks = best_tasks_for_evidence(ev, catalog, max_tasks=2)
        if not best_tasks:
            continue
        matched_entities = []
        low_text = text.lower()
        for node_type, label, keywords in ENTITY_LEXICON:
            hit_keywords = [kw for kw in keywords if kw.lower() in low_text]
            if hit_keywords:
                matched_entities.append((node_type, label, hit_keywords[0]))
        if not matched_entities:
            continue
        matched_entities = matched_entities[:3]
        for score, task in best_tasks:
            for node_type, label, hit in matched_entities:
                predicate = choose_predicate(node_type, text, task)
                edge_seq += 1
                confidence = min(0.96, 0.68 + 0.03 * score + (0.08 if hit in text else 0.0))
                quote = text if len(text) <= 280 else text[:280]
                raw.append(
                    {
                        "triple_id": f"FATO_TRI_{edge_seq:06d}",
                        "chunk_id": None,
                        "subject": task["canonical_task_name"],
                        "subject_id": task["frame_id"],
                        "subject_type": "Task",
                        "predicate": predicate,
                        "object": label,
                        "object_id": stable_node_id(node_type, label),
                        "object_type": node_type,
                        "frame_task_id": task["frame_id"],
                        "evidence_ids": [ev["evidence_id"]],
                        "evidence_quote": quote,
                        "modality": classify_modality_for_triple(text),
                        "scope": classify_scope(text, task["frame_id"]),
                        "polarity": "negative" if "아니" in text or "안 된다" in text or "하지 말" in text else "positive",
                        "confidence": round(confidence, 3),
                        "matched_keyword": hit,
                        "extraction_model": "rule_based_fato_bootstrap_v0.1",
                        "source_text_sha1": sha1_short(text, 16),
                    }
                )
    node_types = {task["frame_id"]: "Task" for task in catalog}
    for node_type, label, _keywords in ENTITY_LEXICON:
        node_types[stable_node_id(node_type, label)] = node_type
    validated = []
    for triple in raw:
        status, issues = validation_status(triple, node_types, evidence_by_id)
        if status.startswith("rejected_"):
            continue
        validated.append({**triple, "validation_status": status, "validation_issues": issues, "review_status": "needs_review" if status != "verified" else "auto_verified"})
    return raw, validated


def add_node(nodes: dict[str, dict[str, Any]], node: dict[str, Any]) -> None:
    node_id = node["node_id"]
    if node_id in nodes:
        existing = nodes[node_id]
        for key in ["evidence_ids", "aliases"]:
            values = list(dict.fromkeys((existing.get(key) or []) + (node.get(key) or [])))
            existing[key] = values
        if len(str(node.get("definition") or "")) > len(str(existing.get("definition") or "")):
            existing["definition"] = node.get("definition")
        return
    nodes[node_id] = node


def build_layer2_graph(
    evidence: list[dict[str, Any]],
    chunks: list[dict[str, Any]],
    catalog: list[dict[str, Any]],
    validated_triples: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []
    process_nodes = {
        "PROCESS_BID_PROPOSAL": ("Process", "수주·제안 업무 프로세스"),
        "PROCESS_PROPOSAL_OVERVIEW": ("Process", "입찰·제안 개요 프로세스"),
        "PROCESS_CAPTURE_SALES": ("Process", "수주영업·고객 이해 프로세스"),
        "PROCESS_PROPOSAL_STRATEGY": ("Process", "제안전략·리스크 관리 프로세스"),
    }
    for node_id, (node_type, label) in process_nodes.items():
        add_node(
            nodes,
            {
                "node_id": node_id,
                "node_type": node_type,
                "name": label,
                "canonical_name": label,
                "domain": "bid_proposal",
                "source": "fato_core_process_seed",
                "review_status": "accepted_seed",
            },
        )
    for ev in evidence:
        add_node(
            nodes,
            {
                "node_id": ev["evidence_id"],
                "node_type": "EvidenceSpan",
                "name": ev["evidence_id"],
                "canonical_name": ev["evidence_id"],
                "domain": "bid_proposal",
                "page": ev.get("page"),
                "section_no": ev.get("section_no"),
                "section_title": ev.get("section_title"),
                "text": ev.get("text"),
                "source": "source_evidence_unit",
                "review_status": ev.get("review_status"),
            },
        )
    for frame in catalog:
        add_node(
            nodes,
            {
                "node_id": frame["frame_id"],
                "node_type": "Task",
                "name": frame["canonical_task_name"],
                "canonical_name": frame["canonical_task_name"],
                "aliases": frame["aliases"],
                "domain": "bid_proposal",
                "task_type": frame["task_type"],
                "definition": frame["definition"],
                "evidence_ids": frame.get("evidence_ids", []),
                "cross_domain_pattern": frame.get("cross_domain_pattern"),
                "confidence": frame.get("confidence"),
                "source": frame.get("source"),
                "review_status": frame.get("review_status"),
            },
        )
        edges.append(make_edge(frame["parent_process"], "HAS_TASK", frame["frame_id"], frame["frame_id"], frame.get("evidence_ids", [])[:1], "Task frame is included in parent process.", 0.95, "verified", "seed_process_membership"))
        for ev_id in frame.get("evidence_ids", [])[:5]:
            edges.append(make_edge(frame["frame_id"], "EVIDENCED_BY", ev_id, frame["frame_id"], [ev_id], "Task frame evidence section.", 0.9, "verified", "task_frame_evidence"))
    for parent, children in SUBTASK_LINKS.items():
        for child in children:
            edges.append(make_edge(parent, "HAS_SUBTASK", child, parent, [], "Seed catalog subtask relation.", 0.86, "needs_review_seed_relation", "seed_subtask"))
    for left, right in zip(PRECEDENCE_CHAIN, PRECEDENCE_CHAIN[1:]):
        edges.append(make_edge(left, "PRECEDES", right, left, [], "Seed process order relation.", 0.78, "needs_review_seed_relation", "seed_precedence"))
    entity_label_by_id: dict[str, tuple[str, str]] = {}
    for node_type, label, _keywords in ENTITY_LEXICON:
        entity_label_by_id[stable_node_id(node_type, label)] = (node_type, label)
    for triple in validated_triples:
        obj_type, label = entity_label_by_id.get(triple["object_id"], (triple["object_type"], triple["object"]))
        add_node(
            nodes,
            {
                "node_id": triple["object_id"],
                "node_type": obj_type,
                "name": label,
                "canonical_name": label,
                "domain": "bid_proposal",
                "evidence_ids": triple.get("evidence_ids", []),
                "source": "frame_anchored_rule_extraction",
                "review_status": "needs_review",
            },
        )
        edges.append(
            make_edge(
                triple["subject_id"],
                triple["predicate"],
                triple["object_id"],
                triple["frame_task_id"],
                triple["evidence_ids"],
                triple["evidence_quote"],
                triple["confidence"],
                triple["validation_status"],
                "frame_anchored_rule_extraction",
                extra={
                    "triple_id": triple["triple_id"],
                    "modality": triple["modality"],
                    "scope": triple["scope"],
                    "polarity": triple["polarity"],
                    "review_status": triple["review_status"],
                },
            )
        )
        for ev_id in triple.get("evidence_ids", []):
            edges.append(make_edge(triple["object_id"], "EVIDENCED_BY", ev_id, triple["frame_task_id"], [ev_id], "Object mention evidence.", 0.9, "verified", "object_evidence"))
    # Merge duplicate semantic edges while preserving evidence.
    merged: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for edge in edges:
        key = (edge["source_id"], edge["predicate"], edge["target_id"], edge.get("frame_task_id") or "")
        if key not in merged:
            merged[key] = edge
            continue
        current = merged[key]
        current["evidence_ids"] = list(dict.fromkeys((current.get("evidence_ids") or []) + (edge.get("evidence_ids") or [])))
        current["confidence"] = round(max(float(current.get("confidence") or 0), float(edge.get("confidence") or 0)), 3)
        current["evidence_count"] = len(current["evidence_ids"])
    final_edges = []
    for i, edge in enumerate(merged.values(), start=1):
        edge["edge_id"] = f"FATO_EDGE_{i:06d}"
        edge["evidence_count"] = len(edge.get("evidence_ids") or [])
        final_edges.append(edge)
    return list(nodes.values()), final_edges


def make_edge(
    source_id: str,
    predicate: str,
    target_id: str,
    frame_task_id: str | None,
    evidence_ids: list[str],
    evidence_quote: str,
    confidence: float,
    validation_status: str,
    source: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "edge_id": "",
        "source_id": source_id,
        "predicate": predicate,
        "target_id": target_id,
        "frame_task_id": frame_task_id,
        "evidence_ids": evidence_ids,
        "evidence_quote": evidence_quote,
        "confidence": round(float(confidence), 3),
        "validation_status": validation_status,
        "source": source,
        "created_at": RUN_DATE,
    }
    if extra:
        payload.update(extra)
    return payload


def tokenize(text: str) -> set[str]:
    tokens = re.findall(r"[A-Za-z0-9가-힣]{2,}", str(text).lower())
    stop = {"그리고", "또는", "대한", "있는", "한다", "위한", "관리", "개발", "분석", "process", "management"}
    return {tok for tok in tokens if tok not in stop}


def load_layer1_nodes(layer1_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    def read(path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        rows = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        return rows

    ncs = read(layer1_dir / "layer1_ncs_nodes.jsonl")
    pcf = read(layer1_dir / "layer1_pcf_nodes.jsonl")
    return ncs, pcf


def mapping_score(task: dict[str, Any], target: dict[str, Any]) -> tuple[float, dict[str, float]]:
    task_text = " ".join(
        [
            task.get("canonical_task_name", ""),
            task.get("definition", ""),
            " ".join(task.get("aliases") or []),
            " ".join(item.get("name", "") for item in task.get("inputs") or []),
            " ".join(item.get("name", "") for item in task.get("outputs") or []),
        ]
    )
    target_text = " ".join(
        str(target.get(key) or "")
        for key in ["label", "label_ko", "label_en", "definition", "description_en", "code", "hid"]
    )
    t_tokens = tokenize(task_text)
    g_tokens = tokenize(target_text)
    overlap = len(t_tokens & g_tokens) / max(1, len(t_tokens | g_tokens))
    label_sim = SequenceMatcher(None, task.get("canonical_task_name", ""), str(target.get("label") or "")).ratio()
    alias_sim = max([SequenceMatcher(None, alias, str(target.get("label") or "")).ratio() for alias in task.get("aliases", [])] or [0])
    definition_sim = SequenceMatcher(None, task.get("definition", "")[:240], str(target.get("definition") or "")[:240]).ratio()
    hierarchy_support = 0.12 if any(tok in g_tokens for tok in ["전략", "제안", "고객", "영업", "risk", "proposal", "customer"]) else 0.0
    raw = 0.35 * label_sim + 0.20 * alias_sim + 0.20 * overlap + 0.15 * definition_sim + 0.10 * hierarchy_support
    return round(raw, 6), {
        "task_name_similarity": round(label_sim, 6),
        "alias_similarity": round(alias_sim, 6),
        "token_overlap": round(overlap, 6),
        "definition_similarity": round(definition_sim, 6),
        "graph_neighbor_support": round(hierarchy_support, 6),
    }


def build_mapping_candidates(catalog: list[dict[str, Any]], layer1_dir: Path) -> list[dict[str, Any]]:
    ncs_nodes, pcf_nodes = load_layer1_nodes(layer1_dir)
    candidates = []
    seq = 0
    for task in catalog:
        for scheme, targets, mapping_type in [
            ("NCS", ncs_nodes, "REQUIRES_CAPABILITY"),
            ("PCF", pcf_nodes, "PROCESS_CONTEXT"),
        ]:
            scored = []
            for target in targets:
                score, components = mapping_score(task, target)
                scored.append((score, components, target))
            scored.sort(key=lambda item: item[0], reverse=True)
            for rank, (score, components, target) in enumerate(scored[:5], start=1):
                seq += 1
                candidates.append(
                    {
                        "mapping_id": f"FATO_MAP_{seq:06d}",
                        "source_layer": "Layer2",
                        "source_id": task["frame_id"],
                        "source_name": task["canonical_task_name"],
                        "target_layer": "Layer1",
                        "target_scheme": scheme,
                        "target_id": target.get("node_id"),
                        "target_name": target.get("label") or target.get("label_ko"),
                        "mapping_type": mapping_type,
                        "rank": rank,
                        "score": score,
                        "score_components": components,
                        "evidence": {
                            "layer2_evidence_ids": task.get("evidence_ids", [])[:3],
                            "layer1_text_fields": ["label", "definition", "label_en", "description_en"],
                        },
                        "reason": f"Layer2 task '{task['canonical_task_name']}' and {scheme} node '{target.get('label')}' share lexical/definition evidence under a loose FATO-KG mapping policy; node merge is not performed.",
                        "review_status": "needs_review",
                    }
                )
    return candidates


def build_review_rows(validated: list[dict[str, Any]], mappings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for triple in sorted(validated, key=lambda row: (row.get("validation_status") == "verified", -float(row.get("confidence") or 0)))[:500]:
        rows.append(
            {
                "item_id": triple["triple_id"],
                "item_type": "frame_anchored_triple",
                "source_text": triple["evidence_quote"],
                "extracted_subject": triple["subject"],
                "predicate": triple["predicate"],
                "object": triple["object"],
                "frame_task_id": triple["frame_task_id"],
                "evidence_quote": triple["evidence_quote"],
                "confidence": triple["confidence"],
                "validation_status": triple["validation_status"],
                "review_decision": "",
                "reviewer_comment": "",
                "canonical_fix": "",
            }
        )
    for row in mappings:
        if row["rank"] <= 3:
            rows.append(
                {
                    "item_id": row["mapping_id"],
                    "item_type": "mapping_candidate",
                    "source_text": row["reason"],
                    "extracted_subject": row["source_name"],
                    "predicate": row["mapping_type"],
                    "object": row["target_name"],
                    "frame_task_id": row["source_id"],
                    "evidence_quote": "; ".join(row["evidence"].get("layer2_evidence_ids") or []),
                    "confidence": row["score"],
                    "validation_status": "needs_expert_review",
                    "review_decision": "",
                    "reviewer_comment": "",
                    "canonical_fix": "",
                }
            )
    return rows


def write_minimal_xlsx(path: Path, sheets: dict[str, tuple[list[str], list[dict[str, Any]]]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    def sheet_xml(headers: list[str], rows: list[dict[str, Any]]) -> str:
        lines = [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
            "<sheetData>",
        ]
        all_rows = [dict(zip(headers, headers))]
        all_rows.extend(rows)
        for r_idx, row in enumerate(all_rows, start=1):
            lines.append(f'<row r="{r_idx}">')
            for c_idx, header in enumerate(headers, start=1):
                col = ""
                n = c_idx
                while n:
                    n, rem = divmod(n - 1, 26)
                    col = chr(65 + rem) + col
                value = escape(str(row.get(header, "") if r_idx > 1 else header))
                lines.append(f'<c r="{col}{r_idx}" t="inlineStr"><is><t>{value}</t></is></c>')
            lines.append("</row>")
        lines += ["</sheetData>", "</worksheet>"]
        return "\n".join(lines)

    content_types = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
    ]
    for idx in range(1, len(sheets) + 1):
        content_types.append(f'<Override PartName="/xl/worksheets/sheet{idx}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>')
    content_types.append("</Types>")
    workbook_sheets = []
    workbook_rels = []
    for idx, name in enumerate(sheets, start=1):
        workbook_sheets.append(f'<sheet name="{escape(name)}" sheetId="{idx}" r:id="rId{idx}"/>')
        workbook_rels.append(f'<Relationship Id="rId{idx}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{idx}.xml"/>')
    workbook_xml = "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">',
            "<sheets>",
            *workbook_sheets,
            "</sheets>",
            "</workbook>",
        ]
    )
    rels_xml = "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>',
            "</Relationships>",
        ]
    )
    workbook_rels_xml = "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
            *workbook_rels,
            "</Relationships>",
        ]
    )
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", "\n".join(content_types))
        zf.writestr("_rels/.rels", rels_xml)
        zf.writestr("xl/workbook.xml", workbook_xml)
        zf.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml)
        for idx, (_name, (headers, rows)) in enumerate(sheets.items(), start=1):
            zf.writestr(f"xl/worksheets/sheet{idx}.xml", sheet_xml(headers, rows))


def render_schema_md() -> str:
    lines = [
        "# FATO-KG Layer2 Graph Schema",
        "",
        f"Generated: {now_iso()}",
        "",
        "This schema follows `layer2_fato_kg_methodology_eacl.md` and is a bootstrap schema, not a human-gold ontology.",
        "",
        "## Node Types",
        "",
        "| node_type | role |",
        "| --- | --- |",
    ]
    for node_type in [
        "Process",
        "Task",
        "Step",
        "Artifact",
        "InformationItem",
        "StrategyArtifact",
        "StrategyElement",
        "Role",
        "Stakeholder",
        "DecisionPoint",
        "Risk",
        "Principle",
        "Condition",
        "Constraint",
        "EvaluationCriterion",
        "EvidenceSpan",
    ]:
        lines.append(f"| `{node_type}` | FATO Layer2 node class |")
    lines += ["", "## Relations", "", "| predicate | domain | range |", "| --- | --- | --- |"]
    for pred, domain_range in RELATION_SCHEMA.items():
        domain, range_ = domain_range if domain_range else (None, [])
        lines.append(f"| `{pred}` | `{', '.join(domain) if domain else 'Any'}` | `{', '.join(range_)}` |")
    lines += [
        "",
        "## Claim Boundary",
        "",
        "- Every edge must keep `frame_task_id`, `evidence_ids`, `confidence`, and `validation_status`.",
        "- `verified` means rule-level evidence/schema checks passed, not human semantic correctness.",
        "- Mapping edges are candidates only and must not merge Layer2 and Layer1 nodes.",
    ]
    return "\n".join(lines) + "\n"


def render_eval_report(
    profile: dict[str, Any],
    chunks: list[dict[str, Any]],
    catalog: list[dict[str, Any]],
    raw: list[dict[str, Any]],
    validated: list[dict[str, Any]],
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    mappings: list[dict[str, Any]],
    review_rows: list[dict[str, Any]],
    output_dir: Path,
) -> str:
    validation_counts = Counter(row["validation_status"] for row in validated)
    edge_pred_counts = Counter(edge["predicate"] for edge in edges)
    node_type_counts = Counter(node["node_type"] for node in nodes)
    mapping_scheme_counts = Counter(row["target_scheme"] for row in mappings)
    task_edge_counts = Counter(edge.get("frame_task_id") for edge in edges if edge.get("frame_task_id"))
    chapter_rows = profile.get("chapter_profile", [])
    lines = [
        "# FATO-KG 자이제_1.xlsx 실험 리포트",
        "",
        f"Generated: {now_iso()}",
        f"Experiment dir: `{output_dir}`",
        "Input: `자이제_1.xlsx`",
        "Methodology: `layer2_fato_kg_methodology_eacl.md`",
        "",
        "이 리포트는 `자이제_1.xlsx`를 FATO-KG 방법론에 맞춰 처리한 1차 bootstrap 결과를 요약한다. "
        "현재 결과는 자동 구축 결과이며, 사람 검수를 완료한 gold ontology/KG가 아니다.",
        "",
        "## 1. 실행 요약",
        "",
        "| 항목 | 값 |",
        "| --- | ---: |",
        f"| 유효 evidence sentences | {profile['valid_sentence_rows']} |",
        f"| 장 수 | {profile['chapter_count']} |",
        f"| section chunks | {len(chunks)} |",
        f"| seed task frames | {len(catalog)} |",
        f"| raw frame-anchored triples | {len(raw)} |",
        f"| validated triples | {len(validated)} |",
        f"| Layer2 nodes | {len(nodes)} |",
        f"| Layer2 edges | {len(edges)} |",
        f"| Layer1 mapping candidates | {len(mappings)} |",
        f"| human review sheet rows | {len(review_rows)} |",
        "",
        "## 2. 입력 데이터 프로파일",
        "",
        "| 항목 | 값 |",
        "| --- | ---: |",
        f"| sheet | clean_sentences |",
        f"| 유효 문장 행 | {profile['valid_sentence_rows']} |",
        f"| 장 수 | {profile['chapter_count']} |",
        f"| section chunk 수 | {len(chunks)} |",
        f"| 구조 메타데이터 누락 문장 | {profile['missing_structure_metadata_sentences']} |",
        "",
        "| chapter | sentence rows |",
        "| --- | ---: |",
    ]
    for row in chapter_rows:
        chapter = row.get("chapter_no") or "missing_metadata"
        title = row.get("chapter_title") or ""
        label = f"{chapter} {title}".strip()
        lines.append(f"| {label} | {row.get('sentence_rows', 0)} |")
    lines += [
        "",
        "## 3. 적용한 처리 절차",
        "",
        "1. `xlsx` 내부 XML을 직접 읽어 `page`, `chapter_no`, `section_no`, `section_title`, `text_for_llm_human` 컬럼을 추출했다.",
        "2. 각 문장 행을 evidence unit으로 만들고, 원문 보존용 `evidence_id`, page, chapter, section, SHA1 fingerprint를 부여했다.",
        "3. 장·절 구조를 기준으로 52개 section chunk를 구성했다. 구조 정보가 빠진 문장은 별도 `missing_structure` chunk로 분리했다.",
        "4. 방법론 문서의 Layer2 FATO task frame 방향에 맞춰 26개 seed task frame을 만들었다.",
        "5. task별 section hint와 키워드 매칭으로 관련 evidence를 연결하고, task frame candidate와 catalog를 산출했다.",
        "6. evidence 문장에서 입력물, 산출물, 역할, 이해관계자, 원칙, 리스크, 의사결정점, 평가 기준 단서를 찾아 frame-anchored triple을 생성했다.",
        "7. triple마다 allowed predicate, domain/range, evidence quote substring, confidence 기준을 적용해 자동 검증했다.",
        "8. 검증된 triple을 Layer2 graph node/edge로 materialize하고, 모든 edge에 `frame_task_id`, `evidence_ids`, `confidence`, `validation_status`를 남겼다.",
        "9. 기존 `outputs/01_layer1`의 NCS/PCF 노드와 lexical similarity 기반 top-k mapping candidate를 만들었다. 이 단계는 후보 생성이며 node merge가 아니다.",
        "10. 자동 검증에서 검수 우선순위가 높은 triple 500개와 Layer1 매핑 후보 top-3를 사람 검수용 sheet로 내보냈다.",
        "",
        "## 4. 검증 상태",
        "",
        "| validation_status | count |",
        "| --- | ---: |",
    ]
    for status, count in validation_counts.most_common():
        lines.append(f"| `{status}` | {count} |")
    lines += [
        "",
        "## 5. Node Type 분포",
        "",
        "| node_type | nodes |",
        "| --- | ---: |",
    ]
    for node_type, count in node_type_counts.most_common():
        lines.append(f"| `{node_type}` | {count} |")
    lines += [
        "",
        "## 6. Predicate 분포",
        "",
        "| predicate | edges |",
        "| --- | ---: |",
    ]
    for pred, count in edge_pred_counts.most_common():
        lines.append(f"| `{pred}` | {count} |")
    lines += [
        "",
        "## 7. 가장 많은 evidence를 가진 Task Frame",
        "",
        "| frame_task_id | task name | evidence/edge count |",
        "| --- | --- | ---: |",
    ]
    frame_names = {frame["frame_id"]: frame["canonical_task_name"] for frame in catalog}
    for task_id, count in task_edge_counts.most_common(15):
        lines.append(f"| `{task_id}` | {frame_names.get(task_id, '')} | {count} |")
    lines += [
        "",
        "## 8. Layer1 Mapping 후보",
        "",
        "| target scheme | candidates |",
        "| --- | ---: |",
    ]
    for scheme, count in mapping_scheme_counts.most_common():
        lines.append(f"| `{scheme}` | {count} |")
    lines += [
        "",
        "mapping score는 task name similarity, alias similarity, token overlap, definition similarity, graph-neighbor support를 합산한 heuristic score이다. "
        "이 값은 사람 검수 우선순위용이며 정답 매핑을 의미하지 않는다.",
        "",
        "## 9. 산출물",
        "",
        "| file | meaning |",
        "| --- | --- |",
        "| `00_source_profile.json` | 입력 엑셀의 장/절/문장 수와 누락 메타데이터 요약 |",
        "| `01_evidence_units.jsonl` | 원문 문장 단위 evidence unit |",
        "| `02_chunks.jsonl` | 장·절 기준 section chunk |",
        "| `03_task_frame_candidates.jsonl` | evidence 기반 task frame 후보 |",
        "| `04_task_frame_catalog.jsonl` | 26개 FATO task frame catalog |",
        "| `05_alias_dictionary.json` | task frame alias 사전 |",
        "| `06_relation_schema.json` | 허용 predicate와 domain/range 제약 |",
        "| `07_frame_anchored_triples_raw.jsonl` | 자동 추출 raw triple |",
        "| `08_frame_anchored_triples_validated.jsonl` | schema/evidence 검증 후 triple |",
        "| `09_layer2_nodes.jsonl` | Layer2 graph node |",
        "| `10_layer2_edges.jsonl` | Layer2 graph edge |",
        "| `11_layer2_graph_schema.md` | Layer2 graph schema 설명 |",
        "| `12_l2_l1_mapping_candidates.jsonl` | NCS/PCF 매핑 후보 |",
        "| `13_human_review_sheet.xlsx` | 사람 검수용 triple/mapping sheet |",
        "| `13_human_review_sheet.csv` | 같은 내용을 CSV로 내보낸 파일 |",
        "| `14_benchmark_gold_frames.jsonl` | human annotation starter template |",
        "| `15_benchmark_gold_triples.jsonl` | human annotation starter template |",
        "| `layer2_neo4j_import.cypher` | Neo4j import 보조 스크립트 초안 |",
        "| `agent_query_templates.md` | agent query pattern 초안 |",
        "| `graph_api_spec.yaml` | graph API spec 초안 |",
        "",
        "## 10. 재실행 명령",
        "",
        "```bash",
        "cd /home/minjoo/AX_서울펠로우",
        "python3 scripts/build_fato_kg_zaize.py \\",
        "  --input-xlsx 자이제_1.xlsx \\",
        "  --methodology layer2_fato_kg_methodology_eacl.md \\",
        "  --output-dir experiments/fato_kg_zaize_20260703 \\",
        "  --layer1-dir outputs/01_layer1",
        "```",
        "",
        "## 11. Claim Boundary",
        "",
        "- 이 결과는 FATO-KG 방법론의 deterministic bootstrap 실험이다.",
        "- 이번 실행은 외부 LLM/GPU를 사용하지 않았다. 현재 서버의 GPU는 이후 LLM 기반 extraction/verification을 붙일 때 사용할 수 있다.",
        "- `verified`는 evidence quote substring, allowed predicate, domain/range 같은 자동 검증을 통과했다는 뜻이다.",
        "- human-gold 성능, task attribution accuracy, evidence faithfulness F1은 아직 주장할 수 없다.",
        "- `14_benchmark_gold_frames.jsonl`, `15_benchmark_gold_triples.jsonl`은 human annotation starter template이며 gold 완료 파일이 아니다.",
    ]
    return "\n".join(lines) + "\n"


def render_neo4j_cypher(nodes_path: str, edges_path: str) -> str:
    return f"""// FATO-KG Layer2 import helper
// Generated by scripts/build_fato_kg_zaize.py
// Convert JSONL to CSV or use APOC json loading in a local Neo4j environment.

CREATE CONSTRAINT fato_node_id IF NOT EXISTS FOR (n:FATONode) REQUIRE n.node_id IS UNIQUE;

// Source JSONL files:
// nodes: {nodes_path}
// edges: {edges_path}

// Suggested labels:
// (:FATONode:Task), (:FATONode:EvidenceSpan), (:FATONode:Artifact), (:FATONode:Role)
// Relationship types use the `predicate` field in 10_layer2_edges.jsonl.
"""


def render_agent_queries() -> str:
    return """# FATO-KG Agent Query Templates

## 업무 계획

Input: target Task

Traversal:

```text
Task <-PRECEDES- predecessor tasks
Task -USES_INPUT-> required inputs
Task -PRODUCES-> expected outputs
Task -EVIDENCED_BY-> EvidenceSpan
```

## 체크리스트 생성

```text
Task -HAS_PRINCIPLE-> Principle
Task -HAS_CONDITION-> Condition
Task -HAS_CONSTRAINT-> Constraint
Task -HAS_RISK-> Risk
```

## 리스크 경고

```text
Task -HAS_RISK-> Risk
Task -MITIGATES-> Risk
Risk -EVIDENCED_BY-> EvidenceSpan
```

## 표준 매핑 설명

```text
Task -REQUIRES_CAPABILITY/PROCESS_CONTEXT-> MappingCandidate target
Task -EVIDENCED_BY-> EvidenceSpan
```
"""


def render_api_spec() -> str:
    return """openapi: 3.0.0
info:
  title: FATO-KG Agent Graph API
  version: 0.1.0
paths:
  /tasks/{task_id}/plan:
    get:
      summary: Return predecessor tasks, inputs, outputs, and evidence for a TaskFrame.
  /tasks/{task_id}/checklist:
    get:
      summary: Return principles, constraints, risks, and evidence-backed checklist items.
  /tasks/{task_id}/mappings:
    get:
      summary: Return Layer1 mapping candidates without merging Layer2 and Layer1 nodes.
"""


def build_experiment(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    sheet_name, rows = read_xlsx_table(Path(args.input_xlsx))
    evidence, profile = make_evidence_units(rows)
    profile["source_file"] = str(args.input_xlsx)
    profile["methodology_file"] = str(args.methodology)
    profile["sheet"] = sheet_name
    chunks = make_chunks(evidence)
    evidence_by_id = {ev["evidence_id"]: ev for ev in evidence}
    candidates, catalog, aliases = build_task_catalog(chunks, evidence_by_id)
    raw, validated = build_triples(evidence, catalog, evidence_by_id)
    nodes, edges = build_layer2_graph(evidence, chunks, catalog, validated)
    mappings = build_mapping_candidates(catalog, Path(args.layer1_dir))
    review_rows = build_review_rows(validated, mappings)

    write_json(output_dir / "00_source_profile.json", profile)
    write_jsonl(output_dir / "01_evidence_units.jsonl", evidence)
    write_jsonl(output_dir / "02_chunks.jsonl", chunks)
    write_jsonl(output_dir / "03_task_frame_candidates.jsonl", candidates)
    write_jsonl(output_dir / "04_task_frame_catalog.jsonl", catalog)
    write_json(output_dir / "05_alias_dictionary.json", aliases)
    write_json(
        output_dir / "06_relation_schema.json",
        {
            "generated_at_utc": now_iso(),
            "claim_status": "fato_relation_schema_ready",
            "relations": [
                {"predicate": pred, "domain": domain if domain is not None else ["Any"], "range": range_}
                for pred, (domain, range_) in RELATION_SCHEMA.items()
            ],
        },
    )
    write_jsonl(output_dir / "07_frame_anchored_triples_raw.jsonl", raw)
    write_jsonl(output_dir / "08_frame_anchored_triples_validated.jsonl", validated)
    write_jsonl(output_dir / "09_layer2_nodes.jsonl", nodes)
    write_jsonl(output_dir / "10_layer2_edges.jsonl", edges)
    write_text(output_dir / "11_layer2_graph_schema.md", render_schema_md())
    write_jsonl(output_dir / "12_l2_l1_mapping_candidates.jsonl", mappings)

    review_fields = [
        "item_id",
        "item_type",
        "source_text",
        "extracted_subject",
        "predicate",
        "object",
        "frame_task_id",
        "evidence_quote",
        "confidence",
        "validation_status",
        "review_decision",
        "reviewer_comment",
        "canonical_fix",
    ]
    write_csv(output_dir / "13_human_review_sheet.csv", review_rows, review_fields)
    write_minimal_xlsx(output_dir / "13_human_review_sheet.xlsx", {"review_items": (review_fields, review_rows)})
    # These are starter templates, not completed gold annotations.
    frame_gold_templates = [
        {**frame, "gold_status": "pending_human_annotation", "annotator_id": "", "adjudication_decision": ""}
        for frame in catalog
    ]
    triple_gold_templates = [
        {
            **triple,
            "gold_status": "pending_human_annotation",
            "annotator_decision": "",
            "adjudication_decision": "",
        }
        for triple in validated[:1200]
    ]
    write_jsonl(output_dir / "14_benchmark_gold_frames.jsonl", frame_gold_templates)
    write_jsonl(output_dir / "15_benchmark_gold_triples.jsonl", triple_gold_templates)
    write_text(
        output_dir / "16_eval_report.md",
        render_eval_report(profile, chunks, catalog, raw, validated, nodes, edges, mappings, review_rows, output_dir),
    )
    write_text(output_dir / "layer2_neo4j_import.cypher", render_neo4j_cypher("09_layer2_nodes.jsonl", "10_layer2_edges.jsonl"))
    write_text(output_dir / "agent_query_templates.md", render_agent_queries())
    write_text(output_dir / "graph_api_spec.yaml", render_api_spec())

    run_summary = {
        "generated_at_utc": now_iso(),
        "input_xlsx": str(args.input_xlsx),
        "methodology": str(args.methodology),
        "output_dir": str(output_dir),
        "claim_status": "fato_kg_bootstrap_ready_not_human_gold",
        "source_profile": {
            "valid_sentence_rows": profile["valid_sentence_rows"],
            "chapter_count": profile["chapter_count"],
            "section_chunks": len(chunks),
            "missing_structure_metadata_sentences": profile["missing_structure_metadata_sentences"],
        },
        "counts": {
            "task_frame_candidates": len(candidates),
            "task_frame_catalog": len(catalog),
            "raw_triples": len(raw),
            "validated_triples": len(validated),
            "layer2_nodes": len(nodes),
            "layer2_edges": len(edges),
            "mapping_candidates": len(mappings),
            "review_rows": len(review_rows),
        },
        "validation_status_counts": dict(Counter(row["validation_status"] for row in validated)),
        "outputs": [
            "00_source_profile.json",
            "01_evidence_units.jsonl",
            "02_chunks.jsonl",
            "03_task_frame_candidates.jsonl",
            "04_task_frame_catalog.jsonl",
            "05_alias_dictionary.json",
            "06_relation_schema.json",
            "07_frame_anchored_triples_raw.jsonl",
            "08_frame_anchored_triples_validated.jsonl",
            "09_layer2_nodes.jsonl",
            "10_layer2_edges.jsonl",
            "11_layer2_graph_schema.md",
            "12_l2_l1_mapping_candidates.jsonl",
            "13_human_review_sheet.xlsx",
            "14_benchmark_gold_frames.jsonl",
            "15_benchmark_gold_triples.jsonl",
            "16_eval_report.md",
        ],
    }
    write_json(output_dir / "run_summary.json", run_summary)
    return run_summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a FATO-KG bootstrap experiment for 자이제_1.xlsx")
    parser.add_argument("--input-xlsx", default=str(DEFAULT_XLSX))
    parser.add_argument("--methodology", default=str(DEFAULT_METHODOLOGY))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--layer1-dir", default=str(DEFAULT_LAYER1_DIR))
    args = parser.parse_args()
    summary = build_experiment(args)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
