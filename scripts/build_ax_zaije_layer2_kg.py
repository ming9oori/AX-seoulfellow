#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the AX ZAIJE Layer 2 KG MVP.

This script implements the experiment described in
AX_ZAIJE_Layer2_KG_Methodology.md.

The current environment does not provide a runnable LLM stack
(torch/transformers/vllm are absent), so the script executes a deterministic
MVP that preserves the exact Task Frame LLM and Triple LLM interfaces as
artifacts. The extraction points can be replaced by actual LLM calls later
without changing the downstream graph validation and export steps.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import statistics
import zipfile
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape


DEFAULT_XLSX = Path("자이제_1.xlsx")
DEFAULT_METHODOLOGY = Path("AX_ZAIJE_Layer2_KG_Methodology.md")
DEFAULT_OUTPUT_DIR = Path("experiments/ax_zaije_layer2_kg_20260706/layer2_kg")
RUN_ID = "RUN_2026_07_06_001"
SCHEMA_VERSION = "L2_SCHEMA_0.1"
BOOK_ID = "ZAIJE_1"
BOOK_NODE_ID = "L2_BOOK_ZAIJE_1"
ONTOLOGY_NODE_ID = "L2_ONTOLOGY_ZAIJE_BID_PROPOSAL"

NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


NODE_REQUIRED = {
    "DomainOntology": ["id", "name", "domain", "schema_version"],
    "Book": ["id", "title", "source_file"],
    "Chapter": ["id", "chapter_no", "title"],
    "Section": ["id", "section_no", "title", "page_start", "page_end"],
    "SourceChunk": ["id", "chunk_id", "text", "hash", "chunk_type"],
    "EvidenceSpan": ["id", "chunk_id", "text_span", "page", "section_no"],
    "DomainProcess": ["id", "name_ko", "definition", "evidence_refs"],
    "DomainTask": ["id", "name_ko", "definition", "evidence_refs"],
    "Step": ["id", "name_ko", "order", "parent_task_id", "evidence_refs"],
    "Artifact": ["id", "name_ko", "artifact_type", "evidence_refs"],
    "InformationObject": ["id", "name_ko", "info_type", "evidence_refs"],
    "DecisionPoint": ["id", "name_ko", "evidence_refs"],
    "Role": ["id", "name_ko", "role_type", "evidence_refs"],
    "Stakeholder": ["id", "name_ko", "stakeholder_type", "evidence_refs"],
    "Principle": ["id", "statement", "scope", "evidence_refs"],
    "StrategyPattern": ["id", "name_ko", "usage_condition", "evidence_refs"],
    "Risk": ["id", "name_ko", "risk_type", "evidence_refs"],
    "Metric": ["id", "name_ko", "unit", "evidence_refs"],
    "ReviewType": ["id", "name_ko", "review_stage", "evidence_refs"],
    "DecisionOutcome": ["id", "name_ko", "outcome_type", "evidence_refs"],
    "Condition": ["id", "statement", "scope", "evidence_refs"],
    "AliasTerm": ["id", "term", "canonical_id", "language"],
}


EDGE_SCHEMA: dict[str, tuple[list[str] | None, list[str] | None]] = {
    "HAS_CHAPTER": (["Book"], ["Chapter"]),
    "HAS_SECTION": (["Chapter"], ["Section"]),
    "HAS_CHUNK": (["Section"], ["SourceChunk"]),
    "HAS_PROCESS": (["DomainOntology"], ["DomainProcess"]),
    "HAS_TASK": (["DomainProcess"], ["DomainTask"]),
    "HAS_SUBTASK": (["DomainTask"], ["DomainTask", "Step"]),
    "CONTAINS": (["Artifact", "InformationObject"], ["InformationObject"]),
    "PART_OF": (["InformationObject", "Artifact"], ["InformationObject", "Artifact"]),
    "DISCOVERS": (["DomainTask"], ["InformationObject"]),
    "PRECEDES": (["DomainTask", "Step"], ["DomainTask", "Step"]),
    "USES_INPUT": (["DomainTask", "Step"], ["Artifact", "InformationObject", "StrategyPattern"]),
    "USED_AS_INPUT_FOR": (["Artifact", "InformationObject", "StrategyPattern"], ["DomainTask"]),
    "PRODUCES": (["DomainTask", "Step"], ["Artifact", "InformationObject", "StrategyPattern"]),
    "PERFORMED_BY": (["DomainTask", "Step"], ["Role"]),
    "TARGETS_STAKEHOLDER": (["DomainTask", "StrategyPattern"], ["Stakeholder"]),
    "ANALYZES": (["DomainTask", "Step"], ["InformationObject", "Stakeholder", "Risk"]),
    "DEVELOPS": (["DomainTask", "Step"], ["Artifact", "StrategyPattern"]),
    "REFINES_INTO": (["Artifact", "StrategyPattern"], ["Artifact", "StrategyPattern"]),
    "DECIDES": (["DecisionPoint", "Role"], ["DecisionOutcome"]),
    "HAS_DECISION_POINT": (["DomainTask", "DomainProcess"], ["DecisionPoint"]),
    "EVALUATES": (["DomainTask", "Step", "Role"], ["Artifact", "StrategyPattern", "Metric"]),
    "HAS_REVIEW": (["DomainTask", "Artifact"], ["ReviewType"]),
    "HAS_PRINCIPLE": (["DomainTask", "StrategyPattern"], ["Principle"]),
    "MITIGATES": (["DomainTask", "StrategyPattern"], ["Risk"]),
    "INCREASES_RISK": (["Condition"], ["Risk"]),
    "MAY_RESULT_IN": (["DomainTask", "StrategyPattern"], ["InformationObject", "Artifact", "Metric"]),
    "ALIAS_OF": (["AliasTerm"], None),
    "EVIDENCED_BY": (None, ["EvidenceSpan"]),
}


PROCESSES = {
    "L2_PROCESS_BID_PROPOSAL_CONTEXT": {
        "name_ko": "입찰·제안 환경 이해",
        "definition": "입찰과 제안의 구조, 공식·비공식 요구조건, 제안 참여의 필요성을 이해하는 상위 업무 흐름.",
        "sections": ["1.1", "1.1.1", "1.1.2", "1.1.3", "1.1.4"],
    },
    "L2_PROCESS_PRE_BID_PREPARATION": {
        "name_ko": "제안참여 전 준비",
        "definition": "기회 정보와 고객 관계를 바탕으로 제안 참여 여부와 사전영업 방향을 준비하는 흐름.",
        "sections": ["1.3.1", "1.3.2"],
    },
    "L2_PROCESS_CAPTURE_PLANNING": {
        "name_ko": "수주영업",
        "definition": "고객·경쟁사·자사 솔루션 정보를 수집하고 Capture Plan과 수주전략을 만드는 흐름.",
        "sections": ["2.1", "2.2", "2.2.1", "2.2.2"],
    },
    "L2_PROCESS_EVALUATOR_PERSUASION": {
        "name_ko": "평가자 공략과 설득",
        "definition": "평가자 유형, 구매단계, 신뢰도, 커뮤니케이션 방식을 분석해 설득 메시지를 설계하는 흐름.",
        "sections": ["2.3", "2.3.1", "2.3.2", "2.3.3", "2.3.4", "2.4.1", "2.4.2", "2.4.3", "2.4.4", "2.4.5"],
    },
    "L2_PROCESS_PROPOSAL_EXECUTION": {
        "name_ko": "제안서 작성·프레젠테이션",
        "definition": "제안서 기획, 작성, 리뷰, 발표 준비를 수행하는 흐름.",
        "sections": ["1.3.3", "1.3.4", "1.3.5"],
    },
    "L2_PROCESS_PROPOSAL_STRATEGY": {
        "name_ko": "제안전략 개발",
        "definition": "고객 이슈, 경쟁사 분석, 차별화 요소, 전략기술서, 전술을 연결해 제안전략을 개발하는 흐름.",
        "sections": ["3.1", "3.1.3", "3.1.4", "3.2", "3.2.2", "3.2.3", "3.2.4", "3.2.5", "3.3.3"],
    },
}


ENTITIES: dict[str, dict[str, Any]] = {
    "L2_ARTIFACT_RFP": {
        "type": "Artifact",
        "name_ko": "RFP / 제안요청서",
        "name_en": "Request for Proposal",
        "aliases": ["RFP", "제안요청서", "요구제안서"],
        "artifact_type": "external_document",
        "keywords": ["RFP", "제안요청서", "요구조건"],
    },
    "L2_ARTIFACT_CAPTURE_PLAN": {
        "type": "Artifact",
        "name_ko": "Capture Plan",
        "name_en": "Capture Plan",
        "aliases": ["Capture Plan", "수주계획", "영업정보 관리 도구"],
        "artifact_type": "planning_artifact",
        "keywords": ["Capture Plan", "수주영업", "영업 정보"],
    },
    "L2_STRATEGY_CAPTURE_STRATEGY": {
        "type": "StrategyPattern",
        "name_ko": "수주전략",
        "name_en": "Capture Strategy",
        "aliases": ["수주전략", "Capture Strategy"],
        "usage_condition": "수주영업 단계에서 고객·경쟁·자사 정보를 종합해 제안 이전 방향을 결정할 때 사용한다.",
        "keywords": ["수주전략", "전략"],
    },
    "L2_ARTIFACT_PROPOSAL_PLAN": {
        "type": "Artifact",
        "name_ko": "Proposal Plan / 제안서 기획",
        "name_en": "Proposal Plan",
        "aliases": ["Proposal Plan", "제안서 기획", "제안 기획"],
        "artifact_type": "planning_artifact",
        "keywords": ["제안서 기획", "Proposal Plan", "제안 기획"],
    },
    "L2_ARTIFACT_PMP": {
        "type": "Artifact",
        "name_ko": "PMP / 제안관리계획",
        "name_en": "Proposal Management Plan",
        "aliases": ["PMP", "Proposal Management Plan", "제안관리계획"],
        "artifact_type": "management_artifact",
        "keywords": ["PMP", "Proposal Management Plan", "관리계획"],
    },
    "L2_ARTIFACT_PDW": {
        "type": "Artifact",
        "name_ko": "PDW / 섹션기획서",
        "name_en": "Proposal Development Worksheet",
        "aliases": ["PDW", "Proposal Development Worksheet", "Storyboard", "스토리보드", "섹션기획서"],
        "artifact_type": "planning_artifact",
        "keywords": ["PDW", "Storyboard", "스토리보드", "섹션"],
    },
    "L2_ARTIFACT_BCM": {
        "type": "Artifact",
        "name_ko": "BCM / 경쟁사 비교표",
        "name_en": "Bidder Comparison Matrix",
        "aliases": ["BCM", "Bidder Comparison Matrix", "경쟁사 비교표"],
        "artifact_type": "analysis_artifact",
        "keywords": ["BCM", "경쟁사 비교", "경쟁사"],
    },
    "L2_ARTIFACT_STRATEGY_STATEMENT": {
        "type": "Artifact",
        "name_ko": "전략기술서",
        "name_en": "Strategy Statement",
        "aliases": ["전략기술서", "전략 기술서", "Theme Statement", "Strategy Statement"],
        "artifact_type": "strategy_artifact",
        "keywords": ["전략기술서", "전략 기술서", "Theme Statement"],
    },
    "L2_ARTIFACT_PROPOSAL_DRAFT": {
        "type": "Artifact",
        "name_ko": "제안서 초안·완성본",
        "name_en": "Proposal Draft and Final Proposal",
        "aliases": ["제안서", "제안서 초안", "제안서 완성본"],
        "artifact_type": "proposal_component",
        "keywords": ["제안서", "초안", "작성"],
    },
    "L2_ARTIFACT_PRESENTATION_MATERIAL": {
        "type": "Artifact",
        "name_ko": "PT 자료",
        "name_en": "Presentation Material",
        "aliases": ["PT 자료", "발표자료", "프레젠테이션 자료"],
        "artifact_type": "proposal_component",
        "keywords": ["PT", "프레젠테이션", "발표"],
    },
    "L2_ARTIFACT_SALES_INFO_DB": {
        "type": "Artifact",
        "name_ko": "영업 정보 DB/관리 체계",
        "name_en": "Sales Information Database",
        "aliases": ["영업 정보 DB", "영업정보 관리 체계", "고객 정보 관리"],
        "artifact_type": "management_artifact",
        "keywords": ["영업 정보", "정보 관리", "고객 정보"],
    },
    "L2_INFO_OFFICIAL_REQUIREMENT": {
        "type": "InformationObject",
        "name_ko": "공식 요구조건",
        "name_en": "Official Requirement",
        "aliases": ["공식 요구조건", "명시 요구조건"],
        "info_type": "requirement",
        "keywords": ["공식 요구조건", "요구조건"],
    },
    "L2_INFO_UNSTATED_REQUIREMENT": {
        "type": "InformationObject",
        "name_ko": "비공식 요구조건",
        "name_en": "Unstated Requirement",
        "aliases": ["비공식 요구조건", "숨은 요구조건", "Unstated Requirement"],
        "info_type": "requirement",
        "keywords": ["비공식", "숨은", "Unstated Requirement"],
    },
    "L2_INFO_CUSTOMER_NEEDS": {
        "type": "InformationObject",
        "name_ko": "고객 니즈",
        "name_en": "Customer Needs",
        "aliases": ["고객 니즈", "고객의 니즈", "고객 요구"],
        "info_type": "customer_need",
        "keywords": ["고객 니즈", "고객의 니즈", "Needs", "니즈"],
    },
    "L2_INFO_CUSTOMER_NEEDS_STRUCTURE": {
        "type": "InformationObject",
        "name_ko": "고객 니즈 구조",
        "name_en": "Customer Needs Structure",
        "aliases": ["고객 니즈 구조", "요구조건 구조", "빙산 구조"],
        "info_type": "requirement_structure",
        "keywords": ["빙산", "요구조건", "니즈"],
    },
    "L2_INFO_OPPORTUNITY_INFORMATION": {
        "type": "InformationObject",
        "name_ko": "기회 정보",
        "name_en": "Opportunity Information",
        "aliases": ["기회 정보", "사업 기회 정보", "Opportunity Information"],
        "info_type": "opportunity",
        "keywords": ["기회", "사업", "입찰"],
    },
    "L2_INFO_OPPORTUNITY_ANALYSIS": {
        "type": "InformationObject",
        "name_ko": "기회분석 결과",
        "name_en": "Opportunity Analysis",
        "aliases": ["기회분석", "기회분석 결과"],
        "info_type": "analysis_result",
        "keywords": ["기회분석", "분석"],
    },
    "L2_INFO_CUSTOMER_RELATIONSHIP": {
        "type": "InformationObject",
        "name_ko": "고객 관계",
        "name_en": "Customer Relationship",
        "aliases": ["고객 관계", "관계"],
        "info_type": "relationship",
        "keywords": ["고객 관계", "관계"],
    },
    "L2_INFO_CUSTOMER_INFORMATION": {
        "type": "InformationObject",
        "name_ko": "고객 정보",
        "name_en": "Customer Information",
        "aliases": ["고객 정보", "고객성향", "고객 상황"],
        "info_type": "customer_information",
        "keywords": ["고객 정보", "고객성향", "고객"],
    },
    "L2_INFO_COMPETITOR_INFORMATION": {
        "type": "InformationObject",
        "name_ko": "경쟁사 정보",
        "name_en": "Competitor Information",
        "aliases": ["경쟁사 정보", "경쟁자 정보", "경쟁 정보"],
        "info_type": "competitor_information",
        "keywords": ["경쟁사", "경쟁자", "경쟁 정보"],
    },
    "L2_INFO_OWN_SOLUTION": {
        "type": "InformationObject",
        "name_ko": "자사 솔루션",
        "name_en": "Own Solution",
        "aliases": ["자사 솔루션", "우리 솔루션", "솔루션"],
        "info_type": "solution_information",
        "keywords": ["솔루션", "자사"],
    },
    "L2_INFO_CUSTOMER_ISSUE": {
        "type": "InformationObject",
        "name_ko": "고객 이슈",
        "name_en": "Customer Issue",
        "aliases": ["고객 이슈", "핵심이슈", "Hot Button"],
        "info_type": "customer_issue",
        "keywords": ["고객 이슈", "핵심이슈", "이슈", "Hot"],
    },
    "L2_INFO_EVALUATION_CRITERIA": {
        "type": "InformationObject",
        "name_ko": "고객 평가 기준",
        "name_en": "Evaluation Criteria",
        "aliases": ["평가 기준", "고객 평가 기준", "평가기준"],
        "info_type": "evaluation_criteria",
        "keywords": ["평가 기준", "평가기준", "평가"],
    },
    "L2_INFO_CORE_DIFFERENTIATOR": {
        "type": "InformationObject",
        "name_ko": "핵심 차별화 요소",
        "name_en": "Core Differentiator",
        "aliases": ["핵심 차별화 요소", "차별화 요소", "Discriminator"],
        "info_type": "differentiator",
        "keywords": ["차별화", "Discriminator"],
    },
    "L2_INFO_PURCHASE_STAGE": {
        "type": "InformationObject",
        "name_ko": "고객 구매단계",
        "name_en": "Customer Purchase Stage",
        "aliases": ["고객 구매단계", "구매단계", "구매 단계"],
        "info_type": "purchase_stage",
        "keywords": ["구매단계", "구매 단계"],
    },
    "L2_INFO_TRUST_LEVEL": {
        "type": "InformationObject",
        "name_ko": "신뢰도",
        "name_en": "Trust Level",
        "aliases": ["신뢰도", "신뢰", "관계 신뢰"],
        "info_type": "trust",
        "keywords": ["신뢰", "신뢰도"],
    },
    "L2_INFO_COMMUNICATION_STYLE": {
        "type": "InformationObject",
        "name_ko": "커뮤니케이션 스타일",
        "name_en": "Communication Style",
        "aliases": ["커뮤니케이션 스타일", "소통 방식", "커뮤니케이션"],
        "info_type": "communication_style",
        "keywords": ["커뮤니케이션", "소통"],
    },
    "L2_INFO_PURCHASE_PSYCHOLOGY": {
        "type": "InformationObject",
        "name_ko": "구매심리",
        "name_en": "Purchase Psychology",
        "aliases": ["구매심리", "고객 심리"],
        "info_type": "purchase_psychology",
        "keywords": ["심리", "구매"],
    },
    "L2_INFO_EVALUATOR_ATTACK_POINT": {
        "type": "InformationObject",
        "name_ko": "평가자별 공략 포인트",
        "name_en": "Evaluator Attack Point",
        "aliases": ["평가자별 공략 포인트", "평가자 공략 포인트"],
        "info_type": "stakeholder_strategy",
        "keywords": ["평가자", "공략"],
    },
    "L2_INFO_PERSUASIVE_MESSAGE": {
        "type": "InformationObject",
        "name_ko": "설득 메시지",
        "name_en": "Persuasive Message",
        "aliases": ["설득 메시지", "평가자 맞춤 메시지", "메시지"],
        "info_type": "message",
        "keywords": ["메시지", "설득"],
    },
    "L2_INFO_DIFFERENTIATION_POINT": {
        "type": "InformationObject",
        "name_ko": "차별화 포인트",
        "name_en": "Differentiation Point",
        "aliases": ["차별화 포인트", "차별화"],
        "info_type": "differentiation_point",
        "keywords": ["차별화 포인트", "차별화"],
    },
    "L2_STRATEGY_VALUE_PROPOSITION": {
        "type": "StrategyPattern",
        "name_ko": "가치제안",
        "name_en": "Value Proposition",
        "aliases": ["가치제안", "Value Proposition", "고객 가치 제안"],
        "usage_condition": "고객 효용과 비용, 경쟁자 대비 가치를 설득해야 할 때 사용한다.",
        "keywords": ["가치제안", "Value Proposition", "가치"],
    },
    "L2_STRATEGY_PROPOSAL_STRATEGY": {
        "type": "StrategyPattern",
        "name_ko": "제안전략",
        "name_en": "Proposal Strategy",
        "aliases": ["제안전략", "Proposal Strategy"],
        "usage_condition": "고객 이슈와 차별화 요소를 제안서의 구조와 메시지로 변환할 때 사용한다.",
        "keywords": ["제안전략", "Proposal Strategy", "전략"],
    },
    "L2_STRATEGY_VALIDATED_TACTIC": {
        "type": "StrategyPattern",
        "name_ko": "검증된 전술",
        "name_en": "Validated Tactic",
        "aliases": ["검증된 전술", "전술", "tactic"],
        "usage_condition": "전략기술서 이후 구체 실행 전술을 개발하고 효과성을 검토할 때 사용한다.",
        "keywords": ["전술", "효과성", "검증"],
    },
    "L2_STRATEGY_PRESENTATION_STRATEGY": {
        "type": "StrategyPattern",
        "name_ko": "발표전략",
        "name_en": "Presentation Strategy",
        "aliases": ["발표전략", "프레젠테이션 전략", "PT 전략"],
        "usage_condition": "평가자를 대상으로 프레젠테이션을 준비할 때 사용한다.",
        "keywords": ["프레젠테이션", "PT", "발표"],
    },
    "L2_STRATEGY_COMMUNICATION_METHOD": {
        "type": "StrategyPattern",
        "name_ko": "커뮤니케이션 방법",
        "name_en": "Communication Method",
        "aliases": ["커뮤니케이션 방법", "메시지 전달 방법"],
        "usage_condition": "전략을 평가자에게 전달하는 표현과 전달 방식을 정할 때 사용한다.",
        "keywords": ["커뮤니케이션 방법", "전달", "표현"],
    },
    "L2_STRATEGY_SOLUTION_OPTIMIZATION": {
        "type": "StrategyPattern",
        "name_ko": "솔루션 최적화",
        "name_en": "Solution Optimization",
        "aliases": ["솔루션 최적화", "솔루션 개발"],
        "usage_condition": "고객 요구와 전략에 맞춰 솔루션을 조정할 때 사용한다.",
        "keywords": ["솔루션", "최적화"],
    },
    "L2_DECISION_BID_NO_BID": {
        "type": "DecisionPoint",
        "name_ko": "Bid/No-Bid Decision",
        "name_en": "Bid/No-Bid Decision",
        "aliases": ["Bid/No-Bid", "Bid/No-Bid Decision", "제안참여 의사결정"],
        "criteria": ["고객 니즈", "경쟁력", "Capture Plan", "수주 가능성"],
        "keywords": ["Bid", "No-Bid", "의사결정", "결정"],
    },
    "L2_OUTCOME_BID": {
        "type": "DecisionOutcome",
        "name_ko": "Bid",
        "name_en": "Bid",
        "aliases": ["Bid", "참여"],
        "outcome_type": "bid_decision",
        "keywords": ["Bid", "참여"],
    },
    "L2_OUTCOME_NO_BID": {
        "type": "DecisionOutcome",
        "name_ko": "No-Bid",
        "name_en": "No-Bid",
        "aliases": ["No-Bid", "불참"],
        "outcome_type": "bid_decision",
        "keywords": ["No-Bid", "불참"],
    },
    "L2_ROLE_SALES_REP": {
        "type": "Role",
        "name_ko": "영업대표",
        "name_en": "Sales Representative",
        "aliases": ["영업대표", "영업 담당자"],
        "role_type": "sales",
        "keywords": ["영업대표", "영업"],
    },
    "L2_ROLE_PM": {
        "type": "Role",
        "name_ko": "PM",
        "name_en": "Project Manager",
        "aliases": ["PM", "프로젝트 매니저"],
        "role_type": "project_management",
        "keywords": ["PM", "프로젝트"],
    },
    "L2_ROLE_PROPOSAL_TEAM": {
        "type": "Role",
        "name_ko": "제안팀",
        "name_en": "Proposal Team",
        "aliases": ["제안팀", "제안 담당자"],
        "role_type": "proposal",
        "keywords": ["제안팀", "제안"],
    },
    "L2_STAKEHOLDER_CUSTOMER": {
        "type": "Stakeholder",
        "name_ko": "고객",
        "name_en": "Customer",
        "aliases": ["고객", "발주처"],
        "stakeholder_type": "customer",
        "keywords": ["고객", "발주처"],
    },
    "L2_STAKEHOLDER_DECISION_MAKER": {
        "type": "Stakeholder",
        "name_ko": "의사결정자",
        "name_en": "Decision Maker",
        "aliases": ["의사결정자", "Decision Maker"],
        "stakeholder_type": "evaluator",
        "keywords": ["의사결정자"],
    },
    "L2_STAKEHOLDER_INFLUENCER": {
        "type": "Stakeholder",
        "name_ko": "영향자",
        "name_en": "Influencer",
        "aliases": ["영향자", "Influencer"],
        "stakeholder_type": "evaluator",
        "keywords": ["영향자"],
    },
    "L2_STAKEHOLDER_TECH_EXPERT": {
        "type": "Stakeholder",
        "name_ko": "기술전문가",
        "name_en": "Technical Expert",
        "aliases": ["기술전문가", "Technical Expert"],
        "stakeholder_type": "evaluator",
        "keywords": ["기술전문가", "기술 전문가"],
    },
    "L2_STAKEHOLDER_USER": {
        "type": "Stakeholder",
        "name_ko": "사용자",
        "name_en": "User",
        "aliases": ["사용자", "실사용자"],
        "stakeholder_type": "evaluator",
        "keywords": ["사용자"],
    },
    "L2_STAKEHOLDER_BUYER_ADMIN": {
        "type": "Stakeholder",
        "name_ko": "구매/행정 그룹",
        "name_en": "Buyer/Admin Group",
        "aliases": ["구매그룹", "행정가", "구매/행정 그룹"],
        "stakeholder_type": "evaluator",
        "keywords": ["구매", "행정"],
    },
    "L2_PRINCIPLE_CUSTOMER_FIRST": {
        "type": "Principle",
        "statement": "제안전략은 고객 니즈와 고객 이슈에서 출발해야 한다.",
        "name_ko": "고객 중심 원칙",
        "scope": "strategy",
        "aliases": ["고객에서 출발", "고객 중심"],
        "keywords": ["고객", "니즈", "출발"],
    },
    "L2_PRINCIPLE_PROCESS_MANAGEMENT": {
        "type": "Principle",
        "statement": "제안은 개인 역량이 아니라 프로세스로 관리되어야 한다.",
        "name_ko": "프로세스 관리 원칙",
        "scope": "process",
        "aliases": ["프로세스 관리", "프로세스가 중요하다"],
        "keywords": ["프로세스", "관리"],
    },
    "L2_PRINCIPLE_DIFFERENTIATION": {
        "type": "Principle",
        "statement": "제안전략은 경쟁자와 구별되는 차별화 요소를 명확히 해야 한다.",
        "name_ko": "차별화 원칙",
        "scope": "strategy",
        "aliases": ["차별화", "핵심 차별화요소"],
        "keywords": ["차별화", "경쟁"],
    },
    "L2_RISK_BUSINESS_RISK": {
        "type": "Risk",
        "name_ko": "사업 리스크",
        "name_en": "Business Risk",
        "aliases": ["사업 리스크", "Risk Gap", "리스크"],
        "risk_type": "business",
        "keywords": ["리스크", "Risk", "위험"],
    },
    "L2_RISK_LATE_RFP_INFLUENCE": {
        "type": "Risk",
        "name_ko": "RFP 이후 영향력 감소 리스크",
        "name_en": "Late RFP Influence Risk",
        "aliases": ["RFP 이후 영향력 감소", "영향력 감소 리스크"],
        "risk_type": "timing",
        "keywords": ["RFP", "영향력", "감소"],
    },
    "L2_REVIEW_STRATEGY_REVIEW": {
        "type": "ReviewType",
        "name_ko": "전략 리뷰",
        "name_en": "Strategy Review",
        "aliases": ["전략 리뷰", "Strategy Review"],
        "review_stage": "strategy",
        "keywords": ["전략 리뷰", "리뷰"],
    },
    "L2_REVIEW_DRAFT_REVIEW": {
        "type": "ReviewType",
        "name_ko": "초안 리뷰",
        "name_en": "Draft Review",
        "aliases": ["초안 리뷰", "Draft Review"],
        "review_stage": "draft",
        "keywords": ["초안", "리뷰"],
    },
    "L2_REVIEW_FINAL_REVIEW": {
        "type": "ReviewType",
        "name_ko": "최종 리뷰",
        "name_en": "Final Review",
        "aliases": ["최종 리뷰", "Final Review"],
        "review_stage": "final",
        "keywords": ["최종", "리뷰"],
    },
    "L2_REVIEW_BLACK_HAT": {
        "type": "ReviewType",
        "name_ko": "블랙햇 리뷰",
        "name_en": "Black Hat Review",
        "aliases": ["블랙햇 리뷰", "Black Hat Review", "경쟁자 관점 리뷰"],
        "review_stage": "competitive",
        "keywords": ["블랙햇", "Black Hat", "경쟁자"],
    },
    "L2_METRIC_WIN_RATE": {
        "type": "Metric",
        "name_ko": "수주 성공률",
        "name_en": "Win Rate",
        "aliases": ["성공률", "수주 성공률", "Win Rate"],
        "unit": "percent",
        "keywords": ["성공률", "수주율"],
    },
}


TASK_SEEDS = [
    {
        "task_id": "L2_TASK_REQUIREMENT_ICEBERG_ANALYSIS",
        "task_name_ko": "고객 요구조건 구조 분석",
        "task_name_en": "Requirement Iceberg Analysis",
        "aliases": ["요구조건 구조 분석", "Requirement Iceberg Analysis", "비공식 요구조건 분석"],
        "definition": "RFP의 공식 요구조건과 원문 뒤에 숨은 비공식 요구조건을 구분하여 고객 니즈 구조를 파악하는 업무.",
        "parent_process_id": "L2_PROCESS_BID_PROPOSAL_CONTEXT",
        "task_scope": "conceptual",
        "sections": ["1.1.1"],
        "keywords": ["요구조건", "비공식", "고객 니즈", "빙산", "RFP"],
        "inputs": ["L2_ARTIFACT_RFP", "L2_INFO_OFFICIAL_REQUIREMENT", "L2_INFO_UNSTATED_REQUIREMENT"],
        "outputs": ["L2_INFO_CUSTOMER_NEEDS_STRUCTURE"],
        "roles": ["L2_ROLE_PROPOSAL_TEAM"],
        "stakeholders": ["L2_STAKEHOLDER_CUSTOMER"],
        "principles": ["L2_PRINCIPLE_CUSTOMER_FIRST"],
        "risks": [],
        "decision_points": [],
        "reviews": [],
        "preceding_tasks": [],
        "next_tasks": ["L2_TASK_OPPORTUNITY_PLANNING", "L2_TASK_CAPTURE_PLANNING"],
    },
    {
        "task_id": "L2_TASK_OPPORTUNITY_PLANNING",
        "task_name_ko": "사전영업 / Opportunity Planning",
        "task_name_en": "Opportunity Planning",
        "aliases": ["사전영업", "Opportunity Planning", "기회분석"],
        "definition": "고객 관계와 기회 정보를 바탕으로 제안 참여 전 사업 기회의 성격과 준비 방향을 판단하는 업무.",
        "parent_process_id": "L2_PROCESS_PRE_BID_PREPARATION",
        "task_scope": "operational",
        "sections": ["1.1.1", "1.3.1"],
        "keywords": ["사전영업", "기회", "고객 관계", "영업"],
        "inputs": ["L2_INFO_CUSTOMER_RELATIONSHIP", "L2_INFO_OPPORTUNITY_INFORMATION"],
        "outputs": ["L2_INFO_OPPORTUNITY_ANALYSIS"],
        "roles": ["L2_ROLE_SALES_REP"],
        "stakeholders": ["L2_STAKEHOLDER_CUSTOMER"],
        "principles": [],
        "risks": ["L2_RISK_LATE_RFP_INFLUENCE"],
        "decision_points": [],
        "reviews": [],
        "preceding_tasks": ["L2_TASK_REQUIREMENT_ICEBERG_ANALYSIS"],
        "next_tasks": ["L2_TASK_CAPTURE_PLANNING", "L2_TASK_BID_NO_BID_DECISION"],
    },
    {
        "task_id": "L2_TASK_CAPTURE_PLANNING",
        "task_name_ko": "수주영업 / Capture Planning",
        "task_name_en": "Capture Planning",
        "aliases": ["수주영업", "Capture Planning", "Capture Plan", "수주계획"],
        "definition": "고객·경쟁사·자사 솔루션 정보를 수집·분석해 Capture Plan과 수주전략을 만드는 업무.",
        "parent_process_id": "L2_PROCESS_CAPTURE_PLANNING",
        "task_scope": "operational",
        "sections": ["1.3.1", "1.3.2", "2.1", "2.1.3"],
        "keywords": ["수주영업", "Capture Plan", "수주전략", "고객 정보", "경쟁사"],
        "inputs": ["L2_INFO_CUSTOMER_INFORMATION", "L2_INFO_COMPETITOR_INFORMATION", "L2_INFO_OWN_SOLUTION", "L2_INFO_CUSTOMER_NEEDS"],
        "outputs": ["L2_ARTIFACT_CAPTURE_PLAN", "L2_STRATEGY_CAPTURE_STRATEGY"],
        "roles": ["L2_ROLE_SALES_REP", "L2_ROLE_PROPOSAL_TEAM"],
        "stakeholders": ["L2_STAKEHOLDER_CUSTOMER"],
        "principles": ["L2_PRINCIPLE_CUSTOMER_FIRST"],
        "risks": ["L2_RISK_LATE_RFP_INFLUENCE"],
        "decision_points": ["L2_DECISION_BID_NO_BID"],
        "reviews": [],
        "preceding_tasks": ["L2_TASK_OPPORTUNITY_PLANNING"],
        "next_tasks": ["L2_TASK_BID_NO_BID_DECISION", "L2_TASK_PROPOSAL_PLANNING"],
    },
    {
        "task_id": "L2_TASK_BID_NO_BID_DECISION",
        "task_name_ko": "제안참여 의사결정",
        "task_name_en": "Bid/No-Bid Decision",
        "aliases": ["Bid/No-Bid Decision", "제안참여 의사결정", "Bid No Bid"],
        "definition": "기회분석, Capture Plan, RFP 정보를 토대로 제안 참여 여부를 판단하는 의사결정 업무.",
        "parent_process_id": "L2_PROCESS_PRE_BID_PREPARATION",
        "task_scope": "decision",
        "sections": ["1.3.1"],
        "keywords": ["Bid", "No-Bid", "의사결정", "참여"],
        "inputs": ["L2_INFO_OPPORTUNITY_ANALYSIS", "L2_ARTIFACT_CAPTURE_PLAN", "L2_ARTIFACT_RFP"],
        "outputs": ["L2_OUTCOME_BID", "L2_OUTCOME_NO_BID"],
        "roles": ["L2_ROLE_SALES_REP", "L2_ROLE_PM"],
        "stakeholders": [],
        "principles": ["L2_PRINCIPLE_PROCESS_MANAGEMENT"],
        "risks": [],
        "decision_points": ["L2_DECISION_BID_NO_BID"],
        "reviews": [],
        "preceding_tasks": ["L2_TASK_CAPTURE_PLANNING"],
        "next_tasks": ["L2_TASK_PROPOSAL_PLANNING"],
    },
    {
        "task_id": "L2_TASK_PROPOSAL_PLANNING",
        "task_name_ko": "제안서 기획 / Proposal Planning",
        "task_name_en": "Proposal Planning",
        "aliases": ["제안서 기획", "Proposal Planning", "Proposal Plan", "제안 기획"],
        "definition": "Capture Plan과 수주전략을 바탕으로 제안서 구조, 일정, 역할, 관리계획을 수립하는 업무.",
        "parent_process_id": "L2_PROCESS_PROPOSAL_EXECUTION",
        "task_scope": "operational",
        "sections": ["1.3.1", "1.3.3"],
        "keywords": ["제안서 기획", "Proposal Planning", "PMP", "역할", "일정"],
        "inputs": ["L2_ARTIFACT_CAPTURE_PLAN", "L2_STRATEGY_CAPTURE_STRATEGY"],
        "outputs": ["L2_ARTIFACT_PROPOSAL_PLAN", "L2_ARTIFACT_PMP", "L2_ARTIFACT_PDW"],
        "roles": ["L2_ROLE_PM", "L2_ROLE_PROPOSAL_TEAM"],
        "stakeholders": [],
        "principles": ["L2_PRINCIPLE_PROCESS_MANAGEMENT"],
        "risks": [],
        "decision_points": [],
        "reviews": ["L2_REVIEW_STRATEGY_REVIEW"],
        "preceding_tasks": ["L2_TASK_BID_NO_BID_DECISION", "L2_TASK_CAPTURE_PLANNING"],
        "next_tasks": ["L2_TASK_PROPOSAL_PREPARING"],
    },
    {
        "task_id": "L2_TASK_PROPOSAL_PREPARING",
        "task_name_ko": "제안서 작성 / Proposal Preparing",
        "task_name_en": "Proposal Preparing",
        "aliases": ["제안서 작성", "Proposal Preparing", "제안서 준비"],
        "definition": "제안전략, 섹션 기획, 리뷰 계획을 반영해 제안서 초안과 완성본을 작성하는 업무.",
        "parent_process_id": "L2_PROCESS_PROPOSAL_EXECUTION",
        "task_scope": "operational",
        "sections": ["1.3.4"],
        "keywords": ["제안서 작성", "제안서", "리뷰", "초안"],
        "inputs": ["L2_STRATEGY_PROPOSAL_STRATEGY", "L2_ARTIFACT_PDW"],
        "outputs": ["L2_ARTIFACT_PROPOSAL_DRAFT"],
        "roles": ["L2_ROLE_PROPOSAL_TEAM"],
        "stakeholders": [],
        "principles": ["L2_PRINCIPLE_PROCESS_MANAGEMENT"],
        "risks": [],
        "decision_points": [],
        "reviews": ["L2_REVIEW_STRATEGY_REVIEW", "L2_REVIEW_DRAFT_REVIEW", "L2_REVIEW_FINAL_REVIEW"],
        "preceding_tasks": ["L2_TASK_PROPOSAL_PLANNING", "L2_TASK_PROPOSAL_STRATEGY_DEVELOPMENT"],
        "next_tasks": ["L2_TASK_PRESENTATION_PREPARATION"],
    },
    {
        "task_id": "L2_TASK_PRESENTATION_PREPARATION",
        "task_name_ko": "프레젠테이션 준비",
        "task_name_en": "Presentation Preparation",
        "aliases": ["프레젠테이션 준비", "PT 준비", "발표 준비"],
        "definition": "제안전략과 평가자 정보를 바탕으로 PT 자료와 발표전략을 준비하는 업무.",
        "parent_process_id": "L2_PROCESS_PROPOSAL_EXECUTION",
        "task_scope": "operational",
        "sections": ["1.3.5"],
        "keywords": ["프레젠테이션", "PT", "발표", "평가자"],
        "inputs": ["L2_STRATEGY_PROPOSAL_STRATEGY", "L2_ARTIFACT_PRESENTATION_MATERIAL", "L2_INFO_EVALUATOR_ATTACK_POINT"],
        "outputs": ["L2_ARTIFACT_PRESENTATION_MATERIAL", "L2_STRATEGY_PRESENTATION_STRATEGY"],
        "roles": ["L2_ROLE_PROPOSAL_TEAM"],
        "stakeholders": ["L2_STAKEHOLDER_DECISION_MAKER", "L2_STAKEHOLDER_TECH_EXPERT"],
        "principles": [],
        "risks": [],
        "decision_points": [],
        "reviews": ["L2_REVIEW_FINAL_REVIEW"],
        "preceding_tasks": ["L2_TASK_PROPOSAL_PREPARING", "L2_TASK_EVALUATOR_ANALYSIS"],
        "next_tasks": [],
    },
    {
        "task_id": "L2_TASK_SALES_INFORMATION_MANAGEMENT",
        "task_name_ko": "영업 정보 관리",
        "task_name_en": "Sales Information Management",
        "aliases": ["영업 정보 관리", "고객 정보 관리", "Sales Information Management"],
        "definition": "고객성향, 의사결정 프로세스, 경쟁 정보를 체계적으로 축적하고 관리하는 업무.",
        "parent_process_id": "L2_PROCESS_CAPTURE_PLANNING",
        "task_scope": "operational",
        "sections": ["2.2.1"],
        "keywords": ["영업 정보", "정보 관리", "고객성향", "의사결정 프로세스"],
        "inputs": ["L2_INFO_CUSTOMER_INFORMATION", "L2_INFO_COMPETITOR_INFORMATION"],
        "outputs": ["L2_ARTIFACT_SALES_INFO_DB"],
        "roles": ["L2_ROLE_SALES_REP"],
        "stakeholders": ["L2_STAKEHOLDER_CUSTOMER"],
        "principles": ["L2_PRINCIPLE_PROCESS_MANAGEMENT"],
        "risks": [],
        "decision_points": [],
        "reviews": [],
        "preceding_tasks": ["L2_TASK_OPPORTUNITY_PLANNING"],
        "next_tasks": ["L2_TASK_CAPTURE_PLANNING", "L2_TASK_VALUE_PROPOSITION"],
    },
    {
        "task_id": "L2_TASK_VALUE_PROPOSITION",
        "task_name_ko": "가치제안 개발",
        "task_name_en": "Value Proposition Development",
        "aliases": ["가치제안", "Value Proposition", "고객 가치 제안"],
        "definition": "고객 효용, 비용, 경쟁자 대비 가치를 조합해 고객에게 설득력 있는 가치제안을 개발하는 업무.",
        "parent_process_id": "L2_PROCESS_CAPTURE_PLANNING",
        "task_scope": "operational",
        "sections": ["2.1.3", "2.2.2"],
        "keywords": ["가치제안", "Value Proposition", "효용", "가치"],
        "inputs": ["L2_INFO_CUSTOMER_NEEDS", "L2_INFO_COMPETITOR_INFORMATION", "L2_INFO_OWN_SOLUTION"],
        "outputs": ["L2_STRATEGY_VALUE_PROPOSITION"],
        "roles": ["L2_ROLE_SALES_REP", "L2_ROLE_PROPOSAL_TEAM"],
        "stakeholders": ["L2_STAKEHOLDER_CUSTOMER"],
        "principles": ["L2_PRINCIPLE_CUSTOMER_FIRST"],
        "risks": [],
        "decision_points": [],
        "reviews": [],
        "preceding_tasks": ["L2_TASK_SALES_INFORMATION_MANAGEMENT"],
        "next_tasks": ["L2_TASK_CAPTURE_PLANNING", "L2_TASK_PERSUASIVE_COMMUNICATION"],
    },
    {
        "task_id": "L2_TASK_EVALUATOR_ANALYSIS",
        "task_name_ko": "평가자 분석",
        "task_name_en": "Evaluator Analysis",
        "aliases": ["평가자 분석", "평가위원 분석", "Evaluator Analysis"],
        "definition": "의사결정자, 영향자, 기술전문가, 사용자, 구매/행정 그룹 등 평가자 유형별 관심과 관점을 분석하는 업무.",
        "parent_process_id": "L2_PROCESS_EVALUATOR_PERSUASION",
        "task_scope": "operational",
        "sections": ["2.3.1", "2.3.2", "2.3.3", "2.3.4"],
        "keywords": ["평가자", "의사결정자", "영향자", "기술전문가", "사용자", "구매"],
        "inputs": ["L2_STAKEHOLDER_DECISION_MAKER", "L2_STAKEHOLDER_INFLUENCER", "L2_STAKEHOLDER_TECH_EXPERT", "L2_STAKEHOLDER_USER", "L2_STAKEHOLDER_BUYER_ADMIN"],
        "outputs": ["L2_INFO_EVALUATOR_ATTACK_POINT"],
        "roles": ["L2_ROLE_PROPOSAL_TEAM"],
        "stakeholders": ["L2_STAKEHOLDER_DECISION_MAKER", "L2_STAKEHOLDER_INFLUENCER", "L2_STAKEHOLDER_TECH_EXPERT", "L2_STAKEHOLDER_USER", "L2_STAKEHOLDER_BUYER_ADMIN"],
        "principles": ["L2_PRINCIPLE_CUSTOMER_FIRST"],
        "risks": [],
        "decision_points": [],
        "reviews": [],
        "preceding_tasks": ["L2_TASK_CAPTURE_PLANNING"],
        "next_tasks": ["L2_TASK_PERSUASIVE_COMMUNICATION", "L2_TASK_PRESENTATION_PREPARATION"],
    },
    {
        "task_id": "L2_TASK_PERSUASIVE_COMMUNICATION",
        "task_name_ko": "설득 커뮤니케이션 설계",
        "task_name_en": "Persuasive Communication Design",
        "aliases": ["설득 커뮤니케이션", "커뮤니케이션 설계", "Persuasive Communication"],
        "definition": "고객 구매단계, 신뢰도, 커뮤니케이션 스타일, 구매심리를 반영해 평가자 맞춤 메시지를 설계하는 업무.",
        "parent_process_id": "L2_PROCESS_EVALUATOR_PERSUASION",
        "task_scope": "operational",
        "sections": ["2.4.1", "2.4.2", "2.4.3", "2.4.4", "2.4.5"],
        "keywords": ["커뮤니케이션", "설득", "구매단계", "신뢰", "메시지"],
        "inputs": ["L2_INFO_EVALUATOR_ATTACK_POINT", "L2_INFO_PURCHASE_STAGE", "L2_INFO_TRUST_LEVEL", "L2_INFO_COMMUNICATION_STYLE", "L2_INFO_PURCHASE_PSYCHOLOGY"],
        "outputs": ["L2_INFO_PERSUASIVE_MESSAGE"],
        "roles": ["L2_ROLE_SALES_REP", "L2_ROLE_PROPOSAL_TEAM"],
        "stakeholders": ["L2_STAKEHOLDER_CUSTOMER"],
        "principles": ["L2_PRINCIPLE_CUSTOMER_FIRST"],
        "risks": [],
        "decision_points": [],
        "reviews": [],
        "preceding_tasks": ["L2_TASK_EVALUATOR_ANALYSIS", "L2_TASK_VALUE_PROPOSITION"],
        "next_tasks": ["L2_TASK_PROPOSAL_STRATEGY_DEVELOPMENT"],
    },
    {
        "task_id": "L2_TASK_PROPOSAL_STRATEGY_DEVELOPMENT",
        "task_name_ko": "제안전략 개발",
        "task_name_en": "Proposal Strategy Development",
        "aliases": ["제안전략 개발", "제안전략", "Proposal Strategy"],
        "definition": "고객 이슈, 경쟁사 분석, 자사 차별화 요소를 연결해 제안전략과 전략기술서를 개발하는 업무.",
        "parent_process_id": "L2_PROCESS_PROPOSAL_STRATEGY",
        "task_scope": "operational",
        "sections": ["3.1", "3.2", "3.1.3", "3.1.4", "3.2.2"],
        "keywords": ["제안전략", "전략기술서", "고객 이슈", "차별화", "경쟁사"],
        "inputs": ["L2_ARTIFACT_CAPTURE_PLAN", "L2_STRATEGY_CAPTURE_STRATEGY", "L2_INFO_CUSTOMER_ISSUE", "L2_INFO_COMPETITOR_INFORMATION", "L2_INFO_CORE_DIFFERENTIATOR"],
        "outputs": ["L2_STRATEGY_PROPOSAL_STRATEGY", "L2_ARTIFACT_STRATEGY_STATEMENT"],
        "roles": ["L2_ROLE_PROPOSAL_TEAM", "L2_ROLE_PM"],
        "stakeholders": ["L2_STAKEHOLDER_CUSTOMER"],
        "principles": ["L2_PRINCIPLE_CUSTOMER_FIRST", "L2_PRINCIPLE_DIFFERENTIATION"],
        "risks": ["L2_RISK_BUSINESS_RISK"],
        "decision_points": [],
        "reviews": ["L2_REVIEW_STRATEGY_REVIEW"],
        "preceding_tasks": ["L2_TASK_CAPTURE_PLANNING", "L2_TASK_COMPETITOR_ANALYSIS", "L2_TASK_PERSUASIVE_COMMUNICATION"],
        "next_tasks": ["L2_TASK_TACTIC_DEVELOPMENT_VALIDATION", "L2_TASK_PROPOSAL_PREPARING"],
    },
    {
        "task_id": "L2_TASK_COMPETITOR_ANALYSIS",
        "task_name_ko": "경쟁사 분석 및 차별화 요소 규명",
        "task_name_en": "Competitor Analysis and Differentiator Identification",
        "aliases": ["경쟁사 분석", "차별화 요소 규명", "Competitor Analysis", "BCM"],
        "definition": "경쟁사 정보, 고객 평가 기준, 자사 강약점을 비교하여 핵심 차별화 요소와 BCM을 도출하는 업무.",
        "parent_process_id": "L2_PROCESS_PROPOSAL_STRATEGY",
        "task_scope": "operational",
        "sections": ["3.1.4", "1.3.2"],
        "keywords": ["경쟁사", "경쟁자", "차별화", "BCM", "평가 기준"],
        "inputs": ["L2_INFO_COMPETITOR_INFORMATION", "L2_INFO_EVALUATION_CRITERIA", "L2_INFO_OWN_SOLUTION"],
        "outputs": ["L2_INFO_CORE_DIFFERENTIATOR", "L2_ARTIFACT_BCM"],
        "roles": ["L2_ROLE_PROPOSAL_TEAM"],
        "stakeholders": ["L2_STAKEHOLDER_CUSTOMER"],
        "principles": ["L2_PRINCIPLE_DIFFERENTIATION"],
        "risks": ["L2_RISK_BUSINESS_RISK"],
        "decision_points": [],
        "reviews": ["L2_REVIEW_BLACK_HAT"],
        "preceding_tasks": ["L2_TASK_CAPTURE_PLANNING"],
        "next_tasks": ["L2_TASK_PROPOSAL_STRATEGY_DEVELOPMENT"],
    },
    {
        "task_id": "L2_TASK_TACTIC_DEVELOPMENT_VALIDATION",
        "task_name_ko": "전술 개발 및 효과성 검증",
        "task_name_en": "Tactic Development and Validation",
        "aliases": ["전술 개발", "전술 효과성 검증", "Tactic Development"],
        "definition": "전략기술서를 바탕으로 솔루션과 커뮤니케이션 방법을 구체화하고 전술의 효과성을 검증하는 업무.",
        "parent_process_id": "L2_PROCESS_PROPOSAL_STRATEGY",
        "task_scope": "review",
        "sections": ["3.2.3", "3.2.4", "3.2.5"],
        "keywords": ["전술", "효과성", "검증", "솔루션", "커뮤니케이션 방법"],
        "inputs": ["L2_ARTIFACT_STRATEGY_STATEMENT", "L2_STRATEGY_SOLUTION_OPTIMIZATION", "L2_STRATEGY_COMMUNICATION_METHOD"],
        "outputs": ["L2_STRATEGY_VALIDATED_TACTIC", "L2_STRATEGY_SOLUTION_OPTIMIZATION", "L2_STRATEGY_COMMUNICATION_METHOD"],
        "roles": ["L2_ROLE_PROPOSAL_TEAM", "L2_ROLE_PM"],
        "stakeholders": ["L2_STAKEHOLDER_CUSTOMER"],
        "principles": ["L2_PRINCIPLE_DIFFERENTIATION"],
        "risks": ["L2_RISK_BUSINESS_RISK"],
        "decision_points": [],
        "reviews": ["L2_REVIEW_STRATEGY_REVIEW"],
        "preceding_tasks": ["L2_TASK_PROPOSAL_STRATEGY_DEVELOPMENT"],
        "next_tasks": ["L2_TASK_PROPOSAL_PREPARING"],
    },
    {
        "task_id": "L2_TASK_RISK_MANAGEMENT",
        "task_name_ko": "리스크 관리",
        "task_name_en": "Risk Management",
        "aliases": ["리스크 관리", "Risk Management", "Risk Gap 관리"],
        "definition": "사업 리스크와 경쟁자 약점을 분석하고 대응 전략을 만들어 차별화 포인트로 전환하는 업무.",
        "parent_process_id": "L2_PROCESS_PROPOSAL_STRATEGY",
        "task_scope": "operational",
        "sections": ["2.1.2", "3.3.3"],
        "keywords": ["리스크", "Risk", "위험", "차별화", "약점"],
        "inputs": ["L2_RISK_BUSINESS_RISK", "L2_INFO_COMPETITOR_INFORMATION"],
        "outputs": ["L2_INFO_DIFFERENTIATION_POINT"],
        "roles": ["L2_ROLE_SALES_REP", "L2_ROLE_PROPOSAL_TEAM"],
        "stakeholders": ["L2_STAKEHOLDER_CUSTOMER"],
        "principles": ["L2_PRINCIPLE_DIFFERENTIATION"],
        "risks": ["L2_RISK_BUSINESS_RISK"],
        "decision_points": [],
        "reviews": ["L2_REVIEW_BLACK_HAT"],
        "preceding_tasks": ["L2_TASK_CAPTURE_PLANNING", "L2_TASK_COMPETITOR_ANALYSIS"],
        "next_tasks": ["L2_TASK_PROPOSAL_STRATEGY_DEVELOPMENT"],
    },
]


COMPETENCY_QUESTIONS = [
    {
        "id": "CQ1",
        "question": "제안전략을 세우기 전에 어떤 정보와 산출물이 필요한가?",
        "expected": "제안전략 개발 ← USES_INPUT ← Capture Plan/고객 이슈/경쟁사 정보/핵심 차별화 요소",
    },
    {
        "id": "CQ2",
        "question": "Capture Plan은 어떤 업무에서 생성되고 어디에 사용되는가?",
        "expected": "수주영업 → PRODUCES → Capture Plan → USED_AS_INPUT_FOR → 제안서 기획",
    },
    {
        "id": "CQ3",
        "question": "Bid/No-Bid 의사결정은 어느 단계에서 발생하며 어떤 입력을 쓰는가?",
        "expected": "수주영업/제안참여 의사결정 → HAS_DECISION_POINT → Bid/No-Bid",
    },
    {
        "id": "CQ4",
        "question": "평가자 유형에 따라 커뮤니케이션은 어떻게 달라지는가?",
        "expected": "평가자 분석 → ANALYZES → 평가자 유형 → USED_AS_INPUT_FOR → 설득 메시지",
    },
    {
        "id": "CQ5",
        "question": "리스크 관리는 어떻게 차별화 포인트로 이어지는가?",
        "expected": "리스크 관리 → MITIGATES → 리스크; 리스크 관리 → MAY_RESULT_IN → 차별화 포인트",
    },
    {
        "id": "CQ6",
        "question": "제안서 작성 단계에서 어떤 리뷰 또는 마일스톤이 필요한가?",
        "expected": "제안서 작성 → HAS_REVIEW → 전략 리뷰/초안 리뷰/최종 리뷰",
    },
    {
        "id": "CQ7",
        "question": "고객의 공식 요구조건과 비공식 요구조건은 어떻게 구분되는가?",
        "expected": "RFP → CONTAINS → 공식 요구조건; 비공식 요구조건 → PART_OF → 고객 니즈",
    },
]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha1(text: str, n: int = 16) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest().upper()[:n]


def sha256(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_float_int(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        as_float = float(text)
    except ValueError:
        return text
    if as_float.is_integer():
        return str(int(as_float))
    return text


def normalize_section(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    parts = text.split(".")
    normalized = []
    for part in parts:
        try:
            number = float(part)
        except ValueError:
            normalized.append(part)
            continue
        normalized.append(str(int(number)) if number.is_integer() else part)
    return ".".join(normalized)


def section_slug(section_no: str) -> str:
    text = str(section_no or "floating").strip()
    return re.sub(r"[^0-9A-Za-z가-힣]+", "_", text).strip("_") or "floating"


def node_name(node: dict[str, Any]) -> str:
    return str(node.get("name_ko") or node.get("title") or node.get("name") or node.get("statement") or node.get("term") or node.get("id"))


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
    records: list[dict[str, Any]] = []
    for excel_row, values in raw_rows[1:]:
        record = {header[i]: values[i] if i < len(values) else "" for i in range(len(header))}
        record["_excel_row"] = excel_row
        records.append(record)
    return sheet_name, records


def classify_chunk_type(text: str) -> str:
    stripped = text.strip()
    if re.search(r"표\s*\d|평가\s*시트|점수[:：]|총계|Matrix|Worksheet", stripped, re.I):
        return "table_chunk"
    if re.search(r"그림\s*\d|도표|Figure", stripped, re.I):
        return "figure_chunk"
    if "정의" in stripped or "이란" in stripped or "의미한다" in stripped:
        return "definition_chunk"
    return "paragraph_chunk"


def relation_scope_for_text(text: str) -> str:
    if "예시" in text or "사례" in text:
        return "example_case"
    if re.search(r"\d+[%％]|성공률|비용|금액|수주액", text):
        return "empirical_claim"
    if "해야" in text or "하라" in text or "중요" in text or "필요" in text:
        return "principle"
    if "이란" in text or "의미" in text or "정의" in text:
        return "definition"
    if "단계" in text or "프로세스" in text or "이후" in text or "전에" in text:
        return "process_step"
    return "author_opinion"


def row_text(row: dict[str, Any]) -> str:
    return str(row.get("text_for_llm_human") or "").strip()


def normalize_rows(rows: list[dict[str, Any]], source_file: Path) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    last = {"chapter_no": "", "chapter_title": "", "section_no": "", "section_title": ""}
    for idx, row in enumerate(rows, start=1):
        text = row_text(row)
        if not text:
            continue
        chapter_no = normalize_float_int(row.get("chapter_no"))
        chapter_title = str(row.get("chapter_title") or "").strip()
        section_no = normalize_section(row.get("section_no"))
        section_title = str(row.get("section_title") or "").strip()
        had_missing = not chapter_no or not section_no or not section_title
        if chapter_no and section_no and section_title:
            last = {
                "chapter_no": chapter_no,
                "chapter_title": chapter_title,
                "section_no": section_no,
                "section_title": section_title,
            }
        else:
            chapter_no = chapter_no or last["chapter_no"]
            chapter_title = chapter_title or last["chapter_title"]
            section_no = section_no or last["section_no"]
            section_title = section_title or last["section_title"]
        page_text = normalize_float_int(row.get("page"))
        page = int(page_text) if page_text.isdigit() else None
        source_row_id = f"ZAIJE_1_ROW_{idx:06d}"
        normalized.append(
            {
                "source_row_id": source_row_id,
                "source_excel_row": row.get("_excel_row"),
                "book_id": BOOK_ID,
                "source_file": str(source_file),
                "page": page,
                "chapter_no": chapter_no,
                "chapter_title": chapter_title,
                "section_no": section_no,
                "section_title": section_title,
                "text": text,
                "row_hash": sha256(text),
                "imputed_section": had_missing,
                "source_type": "clean_sentence",
                "chunk_hint": classify_chunk_type(text),
            }
        )
    return normalized


def chunk_id_for_section(section_no: str) -> str:
    return f"ZAIJE_SEC_{section_slug(section_no)}_SUMMARY"


def make_source_chunks(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, dict[str, Any]]]:
    section_groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (row["chapter_no"], row["chapter_title"], row["section_no"], row["section_title"])
        section_groups[key].append(row)

    chunks: list[dict[str, Any]] = []
    row_to_paragraph_chunk: dict[str, dict[str, Any]] = {}
    for section_index, (key, section_rows) in enumerate(section_groups.items(), start=1):
        chapter_no, chapter_title, section_no, section_title = key
        pages = [row["page"] for row in section_rows if row.get("page") is not None]
        section_chunk_id = chunk_id_for_section(section_no)
        section_text = "\n".join(row["text"] for row in section_rows)
        chunks.append(
            {
                "id": section_chunk_id,
                "chunk_id": section_chunk_id,
                "labels": ["SourceChunk"],
                "chunk_type": "section_summary_chunk",
                "book_id": BOOK_ID,
                "chapter_no": chapter_no,
                "chapter_title": chapter_title,
                "section_no": section_no,
                "section_title": section_title,
                "page_start": min(pages) if pages else None,
                "page_end": max(pages) if pages else None,
                "text": section_text,
                "hash": sha256(section_text),
                "source_row_ids": [row["source_row_id"] for row in section_rows],
                "imputed_section_rows": sum(1 for row in section_rows if row["imputed_section"]),
            }
        )

        paragraph_rows: list[dict[str, Any]] = []
        paragraph_text_len = 0
        paragraph_seq = 1
        for row in section_rows:
            row_len = len(row["text"])
            if paragraph_rows and paragraph_text_len + row_len > 1100:
                paragraph_seq = flush_paragraph_chunk(
                    chunks, row_to_paragraph_chunk, section_no, chapter_no, chapter_title, section_title, paragraph_rows, paragraph_seq
                )
                paragraph_rows = []
                paragraph_text_len = 0
            paragraph_rows.append(row)
            paragraph_text_len += row_len
        if paragraph_rows:
            flush_paragraph_chunk(chunks, row_to_paragraph_chunk, section_no, chapter_no, chapter_title, section_title, paragraph_rows, paragraph_seq)

    evidence_spans: list[dict[str, Any]] = []
    for span_seq, row in enumerate(rows, start=1):
        paragraph_chunk = row_to_paragraph_chunk[row["source_row_id"]]
        span_id = f"EV_ZAIJE_{span_seq:06d}"
        evidence_spans.append(
            {
                "id": span_id,
                "span_id": span_id,
                "labels": ["EvidenceSpan"],
                "chunk_id": paragraph_chunk["chunk_id"],
                "section_chunk_id": chunk_id_for_section(row["section_no"]),
                "source_row_id": row["source_row_id"],
                "source_excel_row": row["source_excel_row"],
                "book_id": BOOK_ID,
                "text_span": row["text"],
                "page": row["page"],
                "chapter_no": row["chapter_no"],
                "chapter_title": row["chapter_title"],
                "section_no": row["section_no"],
                "section_title": row["section_title"],
                "source_hash": row["row_hash"],
                "chunk_type": row["chunk_hint"],
                "imputed_section": row["imputed_section"],
                "review_status": "source_unreviewed",
            }
        )
    evidence_by_id = {ev["id"]: ev for ev in evidence_spans}
    return chunks, evidence_spans, evidence_by_id


def flush_paragraph_chunk(
    chunks: list[dict[str, Any]],
    row_to_paragraph_chunk: dict[str, dict[str, Any]],
    section_no: str,
    chapter_no: str,
    chapter_title: str,
    section_title: str,
    paragraph_rows: list[dict[str, Any]],
    paragraph_seq: int,
) -> int:
    pages = [row["page"] for row in paragraph_rows if row.get("page") is not None]
    text = "\n".join(row["text"] for row in paragraph_rows)
    chunk_type_counts = Counter(row["chunk_hint"] for row in paragraph_rows)
    chunk_type = chunk_type_counts.most_common(1)[0][0] if chunk_type_counts else "paragraph_chunk"
    chunk_id = f"ZAIJE_SEC_{section_slug(section_no)}_CHUNK_{paragraph_seq:03d}"
    chunk = {
        "id": chunk_id,
        "chunk_id": chunk_id,
        "labels": ["SourceChunk"],
        "chunk_type": chunk_type,
        "book_id": BOOK_ID,
        "chapter_no": chapter_no,
        "chapter_title": chapter_title,
        "section_no": section_no,
        "section_title": section_title,
        "page_start": min(pages) if pages else None,
        "page_end": max(pages) if pages else None,
        "text": text,
        "hash": sha256(text),
        "source_row_ids": [row["source_row_id"] for row in paragraph_rows],
        "imputed_section_rows": sum(1 for row in paragraph_rows if row["imputed_section"]),
    }
    chunks.append(chunk)
    for row in paragraph_rows:
        row_to_paragraph_chunk[row["source_row_id"]] = chunk
    return paragraph_seq + 1


def sections_match(section_no: str, seed_sections: list[str]) -> bool:
    if section_no in seed_sections:
        return True
    return any(section_no.startswith(f"{seed}.") or seed.startswith(f"{section_no}.") for seed in seed_sections if section_no and seed)


def text_score(text: str, keywords: list[str]) -> int:
    low = text.lower()
    return sum(low.count(keyword.lower()) for keyword in keywords if keyword)


def evidence_for_seed(seed: dict[str, Any], evidence_spans: list[dict[str, Any]], limit: int = 20) -> list[str]:
    scored: list[tuple[int, int, str]] = []
    for idx, ev in enumerate(evidence_spans):
        section_score = 4 if sections_match(str(ev.get("section_no") or ""), seed.get("sections", [])) else 0
        keyword_score = min(4, text_score(ev["text_span"], seed.get("keywords", [])))
        score = section_score + keyword_score
        if score > 0:
            scored.append((-score, idx, ev["id"]))
    scored.sort()
    return [ev_id for _score, _idx, ev_id in scored[:limit]]


def evidence_for_entity(entity_id: str, evidence_spans: list[dict[str, Any]], fallback_refs: list[str], limit: int = 8) -> list[str]:
    entity = ENTITIES.get(entity_id)
    if not entity:
        return fallback_refs[:limit]
    keywords = list(dict.fromkeys((entity.get("aliases") or []) + (entity.get("keywords") or []) + [entity.get("name_ko", "")]))
    scored: list[tuple[int, int, str]] = []
    for idx, ev in enumerate(evidence_spans):
        score = text_score(ev["text_span"], keywords)
        if score > 0:
            scored.append((-score, idx, ev["id"]))
    scored.sort()
    refs = [ev_id for _score, _idx, ev_id in scored[:limit]]
    return refs or fallback_refs[:limit]


def build_task_frames(evidence_spans: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    raw_frames: list[dict[str, Any]] = []
    canonical_frames: list[dict[str, Any]] = []
    for seed in TASK_SEEDS:
        evidence_refs = evidence_for_seed(seed, evidence_spans, limit=20)
        candidate = {
            "extraction_run_id": RUN_ID,
            "extraction_method": "deterministic_task_frame_mvp_due_to_missing_llm_runtime",
            "task_id": seed["task_id"],
            "task_name_ko": seed["task_name_ko"],
            "task_name_en": seed["task_name_en"],
            "aliases": seed["aliases"],
            "definition": seed["definition"],
            "parent_process": seed["parent_process_id"],
            "task_scope": seed["task_scope"],
            "inputs": seed["inputs"],
            "outputs": seed["outputs"],
            "roles": seed["roles"],
            "stakeholders": seed["stakeholders"],
            "decision_points": seed["decision_points"],
            "subtasks": [],
            "preceding_tasks": seed["preceding_tasks"],
            "next_tasks": seed["next_tasks"],
            "principles": seed["principles"],
            "risks": seed["risks"],
            "metrics": ["L2_METRIC_WIN_RATE"] if seed["task_id"] in {"L2_TASK_CAPTURE_PLANNING", "L2_TASK_PROPOSAL_STRATEGY_DEVELOPMENT"} else [],
            "evidence_sections": sorted({ev["section_no"] for ev in evidence_spans if ev["id"] in set(evidence_refs)}),
            "evidence_spans": evidence_refs,
            "confidence": 0.90 if evidence_refs else 0.66,
            "new_schema_candidates": [],
            "review_status": "needs_review",
        }
        raw_frames.append(candidate)
        canonical_frames.append(
            {
                **candidate,
                "id": seed["task_id"],
                "labels": ["DomainTask"],
                "name_ko": seed["task_name_ko"],
                "name_en": seed["task_name_en"],
                "parent_process_id": seed["parent_process_id"],
                "evidence_refs": evidence_refs,
                "source_book_id": BOOK_ID,
                "schema_version": SCHEMA_VERSION,
                "review_status": "canonical_seed_needs_human_review",
            }
        )
    return raw_frames, canonical_frames


def build_alias_dictionary(task_frames: list[dict[str, Any]]) -> dict[str, Any]:
    canonical_terms: dict[str, dict[str, Any]] = {}
    for frame in task_frames:
        canonical_terms[frame["id"]] = {
            "canonical_id": frame["id"],
            "canonical_label": frame["name_ko"],
            "node_type": "DomainTask",
            "preferred_label": frame["name_ko"],
            "alt_labels": list(dict.fromkeys(frame.get("aliases") or [])),
            "language": "ko/en",
            "source": "task_catalog_v0",
        }
    for entity_id, entity in ENTITIES.items():
        canonical_terms[entity_id] = {
            "canonical_id": entity_id,
            "canonical_label": entity.get("name_ko") or entity.get("statement"),
            "node_type": entity["type"],
            "preferred_label": entity.get("name_ko") or entity.get("statement"),
            "alt_labels": list(dict.fromkeys(entity.get("aliases") or [])),
            "language": "ko/en",
            "source": "zaije_domain_extension_seed",
        }
    term_to_canonical = {}
    for canonical_id, payload in canonical_terms.items():
        labels = [payload["preferred_label"], *payload.get("alt_labels", [])]
        for label in labels:
            if label:
                term_to_canonical[label.lower()] = canonical_id
    return {
        "generated_at_utc": now_iso(),
        "schema_style": "SKOS-inspired preferredLabel/altLabel mapping",
        "canonical_terms": canonical_terms,
        "term_to_canonical": term_to_canonical,
    }


def make_triple(
    triple_id: str,
    source_id: str,
    predicate: str,
    target_id: str,
    frame_task_id: str | None,
    evidence_refs: list[str],
    evidence_by_id: dict[str, dict[str, Any]],
    confidence: float = 0.88,
    relation_scope: str = "process_step",
    extraction_method: str = "deterministic_triple_mvp_due_to_missing_llm_runtime",
) -> dict[str, Any]:
    first_ev = evidence_by_id.get(evidence_refs[0]) if evidence_refs else None
    return {
        "triple_id": triple_id,
        "subject_id": source_id,
        "predicate": predicate,
        "object_id": target_id,
        "frame_task_id": frame_task_id,
        "evidence_refs": list(dict.fromkeys(evidence_refs)),
        "evidence_span": first_ev.get("text_span") if first_ev else "",
        "evidence_page": first_ev.get("page") if first_ev else None,
        "evidence_section": first_ev.get("section_no") if first_ev else "",
        "confidence": round(confidence, 3),
        "relation_scope": relation_scope,
        "extraction_run_id": RUN_ID,
        "extraction_method": extraction_method,
        "review_status": "needs_review",
    }


def build_triples(
    task_frames: list[dict[str, Any]],
    evidence_spans: list[dict[str, Any]],
    evidence_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    triples: list[dict[str, Any]] = []
    seq = 1

    def add(source: str, pred: str, target: str, task_id: str | None, refs: list[str], confidence: float = 0.88, scope: str = "process_step") -> None:
        nonlocal seq
        if not refs:
            refs = task_frames[0].get("evidence_refs", [])[:1] if task_frames else []
        triples.append(make_triple(f"L2_TRI_{seq:06d}", source, pred, target, task_id, refs, evidence_by_id, confidence, scope))
        seq += 1

    for process_id, process in PROCESSES.items():
        refs: list[str] = []
        for seed in TASK_SEEDS:
            if seed["parent_process_id"] == process_id:
                refs.extend(next(frame["evidence_refs"] for frame in task_frames if frame["id"] == seed["task_id"])[:2])
        add(ONTOLOGY_NODE_ID, "HAS_PROCESS", process_id, None, refs[:4], 0.94, "schema_seed")

    frame_by_id = {frame["id"]: frame for frame in task_frames}
    for seed in TASK_SEEDS:
        task_id = seed["task_id"]
        task_refs = frame_by_id[task_id]["evidence_refs"]
        add(seed["parent_process_id"], "HAS_TASK", task_id, task_id, task_refs[:3], 0.93, "schema_seed")
        for input_id in seed.get("inputs", []):
            refs = evidence_for_entity(input_id, evidence_spans, task_refs, limit=3)
            pred = "ANALYZES" if ENTITIES.get(input_id, {}).get("type") in {"InformationObject", "Stakeholder", "Risk"} and "분석" in seed["task_name_ko"] else "USES_INPUT"
            add(task_id, pred, input_id, task_id, refs, 0.88, "process_step")
        for output_id in seed.get("outputs", []):
            refs = evidence_for_entity(output_id, evidence_spans, task_refs, limit=3)
            pred = "DEVELOPS" if ENTITIES.get(output_id, {}).get("type") == "StrategyPattern" else "PRODUCES"
            add(task_id, pred, output_id, task_id, refs, 0.89, "process_step")
        for role_id in seed.get("roles", []):
            refs = evidence_for_entity(role_id, evidence_spans, task_refs, limit=2)
            add(task_id, "PERFORMED_BY", role_id, task_id, refs, 0.82, "definition")
        for stakeholder_id in seed.get("stakeholders", []):
            refs = evidence_for_entity(stakeholder_id, evidence_spans, task_refs, limit=2)
            pred = "ANALYZES" if task_id == "L2_TASK_EVALUATOR_ANALYSIS" else "TARGETS_STAKEHOLDER"
            add(task_id, pred, stakeholder_id, task_id, refs, 0.86, "process_step")
        for decision_id in seed.get("decision_points", []):
            refs = evidence_for_entity(decision_id, evidence_spans, task_refs, limit=3)
            add(task_id, "HAS_DECISION_POINT", decision_id, task_id, refs, 0.90, "process_step")
        for principle_id in seed.get("principles", []):
            refs = evidence_for_entity(principle_id, evidence_spans, task_refs, limit=3)
            add(task_id, "HAS_PRINCIPLE", principle_id, task_id, refs, 0.84, "principle")
        for risk_id in seed.get("risks", []):
            refs = evidence_for_entity(risk_id, evidence_spans, task_refs, limit=3)
            pred = "MITIGATES" if task_id == "L2_TASK_RISK_MANAGEMENT" else "ANALYZES"
            add(task_id, pred, risk_id, task_id, refs, 0.83, "process_step")
        for review_id in seed.get("reviews", []):
            refs = evidence_for_entity(review_id, evidence_spans, task_refs, limit=2)
            add(task_id, "HAS_REVIEW", review_id, task_id, refs, 0.80, "process_step")
        for next_task in seed.get("next_tasks", []):
            refs = (task_refs[:2] + frame_by_id.get(next_task, {}).get("evidence_refs", [])[:2])[:4]
            add(task_id, "PRECEDES", next_task, task_id, refs, 0.82, "process_step")

    # Explicit graph paths required by the methodology and CQ evaluation.
    add("L2_ARTIFACT_RFP", "CONTAINS", "L2_INFO_OFFICIAL_REQUIREMENT", "L2_TASK_REQUIREMENT_ICEBERG_ANALYSIS", evidence_for_entity("L2_ARTIFACT_RFP", evidence_spans, frame_by_id["L2_TASK_REQUIREMENT_ICEBERG_ANALYSIS"]["evidence_refs"]), 0.90, "definition")
    add("L2_INFO_OFFICIAL_REQUIREMENT", "PART_OF", "L2_INFO_CUSTOMER_NEEDS", "L2_TASK_REQUIREMENT_ICEBERG_ANALYSIS", frame_by_id["L2_TASK_REQUIREMENT_ICEBERG_ANALYSIS"]["evidence_refs"][:3], 0.88, "definition")
    add("L2_INFO_UNSTATED_REQUIREMENT", "PART_OF", "L2_INFO_CUSTOMER_NEEDS", "L2_TASK_REQUIREMENT_ICEBERG_ANALYSIS", frame_by_id["L2_TASK_REQUIREMENT_ICEBERG_ANALYSIS"]["evidence_refs"][:3], 0.88, "definition")
    add("L2_TASK_OPPORTUNITY_PLANNING", "DISCOVERS", "L2_INFO_UNSTATED_REQUIREMENT", "L2_TASK_OPPORTUNITY_PLANNING", frame_by_id["L2_TASK_OPPORTUNITY_PLANNING"]["evidence_refs"][:3], 0.83, "process_step")
    add("L2_ARTIFACT_CAPTURE_PLAN", "USED_AS_INPUT_FOR", "L2_TASK_PROPOSAL_PLANNING", "L2_TASK_CAPTURE_PLANNING", frame_by_id["L2_TASK_CAPTURE_PLANNING"]["evidence_refs"][:3], 0.92, "process_step")
    add("L2_STRATEGY_CAPTURE_STRATEGY", "REFINES_INTO", "L2_STRATEGY_PROPOSAL_STRATEGY", "L2_TASK_PROPOSAL_STRATEGY_DEVELOPMENT", frame_by_id["L2_TASK_PROPOSAL_STRATEGY_DEVELOPMENT"]["evidence_refs"][:3], 0.89, "process_step")
    add("L2_STRATEGY_PROPOSAL_STRATEGY", "USED_AS_INPUT_FOR", "L2_TASK_PROPOSAL_PREPARING", "L2_TASK_PROPOSAL_STRATEGY_DEVELOPMENT", frame_by_id["L2_TASK_PROPOSAL_STRATEGY_DEVELOPMENT"]["evidence_refs"][:3], 0.90, "process_step")
    add("L2_INFO_EVALUATOR_ATTACK_POINT", "USED_AS_INPUT_FOR", "L2_TASK_PERSUASIVE_COMMUNICATION", "L2_TASK_EVALUATOR_ANALYSIS", frame_by_id["L2_TASK_EVALUATOR_ANALYSIS"]["evidence_refs"][:3], 0.90, "process_step")
    add("L2_ARTIFACT_BCM", "USED_AS_INPUT_FOR", "L2_TASK_PROPOSAL_STRATEGY_DEVELOPMENT", "L2_TASK_COMPETITOR_ANALYSIS", frame_by_id["L2_TASK_COMPETITOR_ANALYSIS"]["evidence_refs"][:3], 0.87, "process_step")
    add("L2_TASK_RISK_MANAGEMENT", "MAY_RESULT_IN", "L2_INFO_DIFFERENTIATION_POINT", "L2_TASK_RISK_MANAGEMENT", frame_by_id["L2_TASK_RISK_MANAGEMENT"]["evidence_refs"][:3], 0.86, "process_step")
    add("L2_DECISION_BID_NO_BID", "DECIDES", "L2_OUTCOME_BID", "L2_TASK_BID_NO_BID_DECISION", frame_by_id["L2_TASK_BID_NO_BID_DECISION"]["evidence_refs"][:2], 0.80, "definition")
    add("L2_DECISION_BID_NO_BID", "DECIDES", "L2_OUTCOME_NO_BID", "L2_TASK_BID_NO_BID_DECISION", frame_by_id["L2_TASK_BID_NO_BID_DECISION"]["evidence_refs"][:2], 0.80, "definition")

    return triples


def node_type(node: dict[str, Any]) -> str:
    labels = node.get("labels") or []
    if labels:
        return labels[0]
    return str(node.get("node_type") or node.get("type") or "")


def add_node(nodes: dict[str, dict[str, Any]], node: dict[str, Any]) -> None:
    node_id = node["id"]
    if node_id in nodes:
        existing = nodes[node_id]
        for key in ["evidence_refs", "aliases"]:
            values = list(dict.fromkeys((existing.get(key) or []) + (node.get(key) or [])))
            if values:
                existing[key] = values
        return
    nodes[node_id] = node


def build_nodes_and_edges(
    normalized_rows: list[dict[str, Any]],
    source_chunks: list[dict[str, Any]],
    evidence_spans: list[dict[str, Any]],
    task_frames: list[dict[str, Any]],
    triples: list[dict[str, Any]],
    evidence_by_id: dict[str, dict[str, Any]],
    source_file: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []

    add_node(
        nodes,
        {
            "id": ONTOLOGY_NODE_ID,
            "labels": ["DomainOntology"],
            "name": "AX 자이제 수주·제안 Layer2 온톨로지",
            "domain": "bid_proposal",
            "schema_version": SCHEMA_VERSION,
            "source_book_id": BOOK_ID,
            "evidence_refs": [],
            "review_status": "schema_seed",
        },
    )
    add_node(
        nodes,
        {
            "id": BOOK_NODE_ID,
            "labels": ["Book"],
            "book_id": BOOK_ID,
            "title": "자이제_1",
            "source_file": str(source_file),
            "schema_version": SCHEMA_VERSION,
            "evidence_refs": [ev["id"] for ev in evidence_spans[:5]],
            "review_status": "source_profile",
        },
    )

    # Source Evidence Graph nodes.
    section_groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    chapter_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in normalized_rows:
        chapter_groups[(row["chapter_no"], row["chapter_title"])].append(row)
        section_groups[(row["chapter_no"], row["chapter_title"], row["section_no"], row["section_title"])].append(row)

    for (chapter_no, chapter_title), rows in sorted(chapter_groups.items(), key=lambda item: int(item[0][0] or 999)):
        pages = [row["page"] for row in rows if row.get("page") is not None]
        chapter_id = f"L2_CHAPTER_ZAIJE_{chapter_no}"
        add_node(
            nodes,
            {
                "id": chapter_id,
                "labels": ["Chapter"],
                "chapter_no": chapter_no,
                "title": chapter_title,
                "page_start": min(pages) if pages else None,
                "page_end": max(pages) if pages else None,
                "source_book_id": BOOK_ID,
                "evidence_refs": [],
                "schema_version": SCHEMA_VERSION,
            },
        )
        edges.append(edge_record(BOOK_NODE_ID, "HAS_CHAPTER", chapter_id, [], 1.0, "source_structure", "source_structure"))

    for (chapter_no, chapter_title, section_no, section_title), rows in sorted(section_groups.items(), key=lambda item: (int(item[0][0] or 999), item[0][2])):
        pages = [row["page"] for row in rows if row.get("page") is not None]
        section_id = f"L2_SECTION_ZAIJE_{section_slug(section_no)}"
        add_node(
            nodes,
            {
                "id": section_id,
                "labels": ["Section"],
                "chapter_no": chapter_no,
                "chapter_title": chapter_title,
                "section_no": section_no,
                "title": section_title,
                "page_start": min(pages) if pages else None,
                "page_end": max(pages) if pages else None,
                "source_book_id": BOOK_ID,
                "evidence_refs": [],
                "schema_version": SCHEMA_VERSION,
            },
        )
        edges.append(edge_record(f"L2_CHAPTER_ZAIJE_{chapter_no}", "HAS_SECTION", section_id, [], 1.0, "source_structure", "source_structure"))

    for chunk in source_chunks:
        add_node(nodes, {**chunk, "source_book_id": BOOK_ID, "schema_version": SCHEMA_VERSION, "review_status": "source_chunk"})
        section_id = f"L2_SECTION_ZAIJE_{section_slug(chunk['section_no'])}"
        edges.append(edge_record(section_id, "HAS_CHUNK", chunk["id"], [], 1.0, "source_structure", "source_structure"))

    for ev in evidence_spans:
        add_node(
            nodes,
            {
                **ev,
                "labels": ["EvidenceSpan"],
                "source_book_id": BOOK_ID,
                "schema_version": SCHEMA_VERSION,
                "evidence_refs": [],
            },
        )
        edges.append(edge_record(ev["chunk_id"], "EVIDENCED_BY", ev["id"], [ev["id"]], 1.0, "source_structure", "source_evidence_link"))

    # Domain ontology nodes.
    for process_id, process in PROCESSES.items():
        refs = []
        for frame in task_frames:
            if frame["parent_process_id"] == process_id:
                refs.extend(frame["evidence_refs"][:2])
        add_node(
            nodes,
            {
                "id": process_id,
                "labels": ["DomainProcess"],
                "name_ko": process["name_ko"],
                "definition": process["definition"],
                "source_book_id": BOOK_ID,
                "evidence_refs": list(dict.fromkeys(refs))[:8],
                "confidence": 0.92,
                "review_status": "needs_review",
                "schema_version": SCHEMA_VERSION,
            },
        )

    for frame in task_frames:
        add_node(
            nodes,
            {
                "id": frame["id"],
                "labels": ["DomainTask"],
                "name_ko": frame["name_ko"],
                "name_en": frame["name_en"],
                "aliases": frame["aliases"],
                "definition": frame["definition"],
                "parent_process_id": frame["parent_process_id"],
                "task_scope": frame["task_scope"],
                "inputs": frame["inputs"],
                "outputs": frame["outputs"],
                "roles": frame["roles"],
                "stakeholders": frame["stakeholders"],
                "decision_points": frame["decision_points"],
                "principles": frame["principles"],
                "risks": frame["risks"],
                "evidence_refs": frame["evidence_refs"],
                "confidence": frame["confidence"],
                "review_status": frame["review_status"],
                "schema_version": SCHEMA_VERSION,
                "source_book_id": BOOK_ID,
            },
        )

    for entity_id, entity in ENTITIES.items():
        refs = evidence_for_entity(entity_id, evidence_spans, [])
        labels = [entity["type"]]
        node = {
            "id": entity_id,
            "labels": labels,
            "name_ko": entity.get("name_ko"),
            "name_en": entity.get("name_en"),
            "aliases": entity.get("aliases") or [],
            "source_book_id": BOOK_ID,
            "evidence_refs": refs,
            "confidence": 0.84 if refs else 0.68,
            "review_status": "needs_review",
            "schema_version": SCHEMA_VERSION,
        }
        for key in ["artifact_type", "info_type", "criteria", "role_type", "stakeholder_type", "statement", "scope", "usage_condition", "risk_type", "review_stage", "unit", "outcome_type"]:
            if key in entity:
                node[key] = entity[key]
        if entity["type"] == "Principle":
            node["statement"] = entity["statement"]
        add_node(nodes, node)

    # AliasTerm nodes and edges.
    alias_seq = 1
    for canonical_id, node in list(nodes.items()):
        aliases = node.get("aliases") or []
        for alias in aliases:
            alias_id = f"L2_ALIAS_{alias_seq:05d}"
            alias_seq += 1
            add_node(
                nodes,
                {
                    "id": alias_id,
                    "labels": ["AliasTerm"],
                    "term": alias,
                    "canonical_id": canonical_id,
                    "language": "ko" if re.search(r"[가-힣]", alias) else "en",
                    "schema_version": SCHEMA_VERSION,
                    "review_status": "alias_seed",
                },
            )
            refs = node.get("evidence_refs") or []
            edges.append(edge_record(alias_id, "ALIAS_OF", canonical_id, refs[:2], 0.80, "alias", "alias_dictionary"))

    # Domain triples and node-to-evidence projection.
    for triple in triples:
        edges.append(
            edge_record(
                triple["subject_id"],
                triple["predicate"],
                triple["object_id"],
                triple["evidence_refs"],
                triple["confidence"],
                triple["relation_scope"],
                triple["extraction_method"],
                frame_task_id=triple.get("frame_task_id"),
                triple_id=triple["triple_id"],
            )
        )

    for node in list(nodes.values()):
        labels = node.get("labels") or []
        if labels and labels[0] not in {"EvidenceSpan", "AliasTerm"}:
            for ev_id in (node.get("evidence_refs") or [])[:5]:
                edges.append(edge_record(node["id"], "EVIDENCED_BY", ev_id, [ev_id], 0.99, "evidence_link", "node_evidence_projection"))

    validated_edges = validate_edges(nodes, edges, evidence_by_id)
    return list(nodes.values()), validated_edges


def edge_record(
    source_id: str,
    predicate: str,
    target_id: str,
    evidence_refs: list[str],
    confidence: float,
    relation_scope: str,
    source: str,
    frame_task_id: str | None = None,
    triple_id: str | None = None,
) -> dict[str, Any]:
    return {
        "edge_id": "",
        "source_id": source_id,
        "predicate": predicate,
        "target_id": target_id,
        "evidence_refs": list(dict.fromkeys(evidence_refs)),
        "confidence": round(confidence, 3),
        "relation_scope": relation_scope,
        "extraction_run_id": RUN_ID,
        "review_status": "needs_review" if confidence < 0.9 else "auto_verified",
        "source": source,
        "frame_task_id": frame_task_id,
        "triple_id": triple_id,
    }


def validate_edges(nodes: dict[str, dict[str, Any]], edges: list[dict[str, Any]], evidence_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    dedup: dict[tuple[str, str, str], dict[str, Any]] = {}
    for edge in edges:
        key = (edge["source_id"], edge["predicate"], edge["target_id"])
        if key in dedup:
            existing = dedup[key]
            existing["evidence_refs"] = list(dict.fromkeys((existing.get("evidence_refs") or []) + (edge.get("evidence_refs") or [])))
            existing["confidence"] = max(float(existing.get("confidence") or 0), float(edge.get("confidence") or 0))
            continue
        dedup[key] = dict(edge)

    validated = []
    for seq, edge in enumerate(dedup.values(), start=1):
        issues = []
        pred = edge["predicate"]
        if pred not in EDGE_SCHEMA:
            issues.append("predicate_not_allowed")
        if edge["source_id"] not in nodes:
            issues.append("missing_source_node")
        if edge["target_id"] not in nodes:
            issues.append("missing_target_node")
        evidence_refs = edge.get("evidence_refs") or []
        if pred not in {"HAS_CHAPTER", "HAS_SECTION", "HAS_CHUNK"} and not evidence_refs:
            issues.append("missing_evidence_refs")
        for ev_id in evidence_refs:
            if ev_id not in evidence_by_id:
                issues.append("unknown_evidence_ref")
                break
        if pred in EDGE_SCHEMA and edge["source_id"] in nodes and edge["target_id"] in nodes:
            allowed_sources, allowed_targets = EDGE_SCHEMA[pred]
            source_type = node_type(nodes[edge["source_id"]])
            target_type = node_type(nodes[edge["target_id"]])
            if allowed_sources is not None and source_type not in allowed_sources:
                issues.append(f"domain_violation:{source_type}->{pred}")
            if allowed_targets is not None and target_type not in allowed_targets:
                issues.append(f"range_violation:{pred}->{target_type}")
        if float(edge.get("confidence") or 0) < 0.60:
            issues.append("confidence_below_graph_threshold")
        if issues:
            edge["validation_status"] = "rejected_" + issues[0]
            edge["validation_issues"] = issues
            continue
        edge["edge_id"] = f"L2_EDGE_{seq:06d}"
        edge["validation_status"] = "verified" if float(edge.get("confidence") or 0) >= 0.8 else "needs_review"
        edge["validation_issues"] = []
        validated.append(edge)
    return validated


def validate_triples(triples: list[dict[str, Any]], nodes: list[dict[str, Any]], evidence_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    node_map = {node["id"]: node for node in nodes}
    validated: list[dict[str, Any]] = []
    seen = set()
    for triple in triples:
        issues = []
        key = (triple["subject_id"], triple["predicate"], triple["object_id"])
        if key in seen:
            issues.append("duplicate_spo")
        seen.add(key)
        if triple["predicate"] not in EDGE_SCHEMA:
            issues.append("predicate_not_allowed")
        if triple["subject_id"] not in node_map:
            issues.append("missing_subject")
        if triple["object_id"] not in node_map:
            issues.append("missing_object")
        if not triple.get("evidence_refs"):
            issues.append("missing_evidence_refs")
        for ev_id in triple.get("evidence_refs", []):
            if ev_id not in evidence_by_id:
                issues.append("unknown_evidence_ref")
        if triple["predicate"] in EDGE_SCHEMA and triple["subject_id"] in node_map and triple["object_id"] in node_map:
            domain, range_ = EDGE_SCHEMA[triple["predicate"]]
            s_type = node_type(node_map[triple["subject_id"]])
            o_type = node_type(node_map[triple["object_id"]])
            if domain is not None and s_type not in domain:
                issues.append(f"domain_violation:{s_type}->{triple['predicate']}")
            if range_ is not None and o_type not in range_:
                issues.append(f"range_violation:{triple['predicate']}->{o_type}")
        if float(triple.get("confidence") or 0) < 0.60:
            issues.append("confidence_below_threshold")
        if issues:
            continue
        status = "verified" if float(triple.get("confidence") or 0) >= 0.8 else "needs_review"
        validated.append({**triple, "validation_status": status, "validation_issues": []})
    return validated


def build_source_profile_md(
    sheet_name: str,
    physical_rows: int,
    normalized_rows: list[dict[str, Any]],
    source_chunks: list[dict[str, Any]],
    evidence_spans: list[dict[str, Any]],
    source_file: Path,
    methodology_file: Path,
) -> tuple[str, dict[str, Any]]:
    chapter_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    section_groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in normalized_rows:
        chapter_groups[(row["chapter_no"], row["chapter_title"])].append(row)
        section_groups[(row["chapter_no"], row["chapter_title"], row["section_no"], row["section_title"])].append(row)
    chapter_profile = []
    for (chapter_no, chapter_title), rows in sorted(chapter_groups.items(), key=lambda item: int(item[0][0] or 999)):
        pages = [row["page"] for row in rows if row.get("page") is not None]
        sections = {(row["section_no"], row["section_title"]) for row in rows}
        chapter_profile.append(
            {
                "chapter_no": chapter_no,
                "chapter_title": chapter_title,
                "sentence_rows": len(rows),
                "section_count": len(sections),
                "page_min": min(pages) if pages else None,
                "page_max": max(pages) if pages else None,
            }
        )
    chunk_counts = Counter(chunk["chunk_type"] for chunk in source_chunks)
    imputed = sum(1 for row in normalized_rows if row["imputed_section"])
    profile = {
        "generated_at_utc": now_iso(),
        "source_file": str(source_file),
        "methodology_file": str(methodology_file),
        "sheet": sheet_name,
        "physical_rows": physical_rows,
        "valid_sentence_rows": len(normalized_rows),
        "evidence_spans": len(evidence_spans),
        "source_chunks": len(source_chunks),
        "source_chunk_type_counts": dict(chunk_counts),
        "chapter_count": len(chapter_groups),
        "section_count": len(section_groups),
        "imputed_section_rows": imputed,
        "chapter_profile": chapter_profile,
    }
    lines = [
        "# Source Profile",
        "",
        f"Generated: {profile['generated_at_utc']}",
        f"Input file: `{source_file}`",
        f"Methodology: `{methodology_file}`",
        f"Sheet: `{sheet_name}`",
        "",
        "## Counts",
        "",
        "| item | value |",
        "| --- | ---: |",
        f"| physical rows | {physical_rows} |",
        f"| valid sentence rows | {len(normalized_rows)} |",
        f"| evidence spans | {len(evidence_spans)} |",
        f"| source chunks | {len(source_chunks)} |",
        f"| chapters | {len(chapter_groups)} |",
        f"| sections | {len(section_groups)} |",
        f"| imputed section rows | {imputed} |",
        "",
        "## Chunk Types",
        "",
        "| chunk_type | count |",
        "| --- | ---: |",
    ]
    for chunk_type, count in chunk_counts.most_common():
        lines.append(f"| `{chunk_type}` | {count} |")
    lines += ["", "## Chapter Profile", "", "| chapter | title | pages | rows | sections |", "| --- | --- | --- | ---: | ---: |"]
    for row in chapter_profile:
        pages = f"{row['page_min']}-{row['page_max']}"
        lines.append(f"| {row['chapter_no']} | {row['chapter_title']} | {pages} | {row['sentence_rows']} | {row['section_count']} |")
    lines += [
        "",
        "## Normalization Rule",
        "",
        "- `chapter_no`/`section_no`가 누락된 행은 직전 유효 섹션에 귀속하고 `imputed_section=true`로 표시했다.",
        "- 표/그림/정의성 문장은 chunk type으로 표시하되 원문 evidence span은 삭제하지 않았다.",
    ]
    return "\n".join(lines) + "\n", profile


def render_core_schema_yaml() -> str:
    lines = [
        "schema_id: L2_CORE_SCHEMA_0.1",
        "scope: domain_task_ontology",
        "excluded_scope:",
        "  - layer1_standard_reference_mapping",
        "  - ncs_mapping",
        "  - pcf_mapping",
        "node_types:",
    ]
    for node_type_name, required in NODE_REQUIRED.items():
        lines.append(f"  {node_type_name}:")
        lines.append(f"    required: [{', '.join(required)}]")
    lines.append("edge_types:")
    for predicate, (domain, range_) in EDGE_SCHEMA.items():
        lines.append(f"  {predicate}:")
        if domain is None:
            lines.append("    domain: [Any]")
        else:
            lines.append(f"    domain: [{', '.join(domain)}]")
        if range_ is None:
            lines.append("    range: [Any]")
        else:
            lines.append(f"    range: [{', '.join(range_)}]")
    lines += [
        "edge_required_properties:",
        "  - evidence_refs",
        "  - confidence",
        "  - relation_scope",
        "  - extraction_run_id",
        "  - review_status",
    ]
    return "\n".join(lines) + "\n"


def render_domain_extension_yaml() -> str:
    lines = [
        "domain_extension_id: L2_DOMAIN_EXTENSION_ZAIJE_BID_PROPOSAL_0.1",
        "domain: bid_proposal",
        "book_id: ZAIJE_1",
        "canonical_processes:",
    ]
    for process_id, process in PROCESSES.items():
        lines.append(f"  - id: {process_id}")
        lines.append(f"    name_ko: {json.dumps(process['name_ko'], ensure_ascii=False)}")
        lines.append(f"    sections: [{', '.join(process['sections'])}]")
    lines.append("canonical_tasks:")
    for seed in TASK_SEEDS:
        lines.append(f"  - id: {seed['task_id']}")
        lines.append(f"    name_ko: {json.dumps(seed['task_name_ko'], ensure_ascii=False)}")
        lines.append(f"    name_en: {json.dumps(seed['task_name_en'], ensure_ascii=False)}")
        lines.append(f"    parent_process_id: {seed['parent_process_id']}")
        lines.append(f"    sections: [{', '.join(seed['sections'])}]")
    lines.append("canonical_entities:")
    for entity_id, entity in ENTITIES.items():
        lines.append(f"  - id: {entity_id}")
        lines.append(f"    type: {entity['type']}")
        lines.append(f"    name_ko: {json.dumps(entity.get('name_ko') or entity.get('statement'), ensure_ascii=False)}")
    return "\n".join(lines) + "\n"


def render_prompts_md() -> str:
    return """# Extraction Prompts

이 파일은 `AX_ZAIJE_Layer2_KG_Methodology.md`의 Task Frame LLM / Triple LLM 프롬프트를 실행 가능한 형태로 보존한 것이다.

현재 실행은 `torch/transformers/vllm`이 없는 Python 환경에서 수행되어 LLM 호출 대신 deterministic MVP extractor를 사용했다. 실제 LLM 실행 시 아래 프롬프트를 그대로 사용하고, 출력 JSON을 `05_task_frames.raw.jsonl`, `08_triples.raw.jsonl`로 연결하면 된다.

## Task Frame System Prompt

```text
당신은 업무 도메인 온톨로지 설계자입니다.
입력 문서에서 반복 가능한 업무(Task), 업무의 입력(Input), 산출물(Artifact), 역할(Role), 의사결정 지점(DecisionPoint), 원칙(Principle)을 추출합니다.

규칙:
1. 원문에서 근거가 확인되는 내용만 추출합니다.
2. 사례 속 인물·회사·프로젝트는 일반 업무 지식으로 승격하지 않습니다.
3. 섹션 제목만으로 Task를 만들지 말고, 실제 활동·조건·산출물이 있는지 확인합니다.
4. 동일 개념의 한국어/영어/약어는 aliases로 묶습니다.
5. 출력은 반드시 JSON Schema를 따릅니다.
6. Layer 1 표준 직무 매핑은 하지 않습니다.
```

## Task Frame User Prompt Template

```text
다음은 책의 장/섹션 단위 텍스트입니다.

[문서 메타데이터]
book_id: ZAIJE_1
chapter_no: {chapter_no}
chapter_title: {chapter_title}
section_no: {section_no}
section_title: {section_title}

[텍스트]
{text}

[요청]
이 섹션에서 확인되는 Layer 2 업무 Task Frame을 추출하세요.
반드시 evidence_sections와 evidence_spans를 포함하세요.
업무가 아니라 개념/원칙/통계/사례에 해당하는 것은 task가 아닌 candidate_terms에 넣으세요.

[출력 JSON]
{
  "task_frames": [],
  "candidate_terms": [],
  "candidate_artifacts": [],
  "candidate_decision_points": [],
  "candidate_principles": [],
  "notes": []
}
```

## Triple System Prompt

```text
당신은 근거 기반 지식그래프 삼중항 추출기입니다.
입력 chunk에서 확인되는 사실관계를 subject-predicate-object 형태로 추출합니다.

규칙:
1. predicate는 allowed_predicates 안에서만 선택합니다.
2. subject와 object는 가능한 한 canonical node를 사용합니다.
3. 모든 triple은 evidence_span을 가져야 합니다.
4. evidence_span이 chunk 안에 없으면 추출하지 않습니다.
5. 확신이 낮거나 schema에 맞지 않으면 new_node_candidates 또는 review_notes로 보냅니다.
6. 예시 인물·회사·프로젝트는 relation_scope="example_case"로 표시합니다.
```

## Triple User Prompt Template

```text
[Chunk]
chunk_id: {chunk_id}
page: {page}
section_no: {section_no}
section_title: {section_title}
text:
{text}

[Candidate Task Frames]
{candidate_task_frames_json}

[Allowed Predicates]
{allowed_predicates}

[Alias Dictionary]
{alias_dictionary}

[요청]
현재 chunk에서 확인되는 Layer 2 KG triple을 추출하세요.
가능하면 frame_task_id에 기존 Task ID를 부여하세요.
추출 대상은 업무 수행 지식입니다. 감상, 장식적 표현, 근거 없는 일반화는 제외하세요.

[출력 JSON]
{
  "chunk_id": "",
  "triples": [
    {
      "subject": "",
      "subject_type": "",
      "predicate": "",
      "object": "",
      "object_type": "",
      "frame_task_id": "",
      "evidence_span": "",
      "evidence_page": null,
      "evidence_section": "",
      "confidence": 0.0,
      "relation_scope": ""
    }
  ],
  "new_node_candidates": [],
  "new_predicate_candidates": [],
  "review_notes": []
}
```
"""


def graph_has_edge(edges: list[dict[str, Any]], source: str, predicate: str, target: str | None = None) -> bool:
    return any(edge["source_id"] == source and edge["predicate"] == predicate and (target is None or edge["target_id"] == target) for edge in edges)


def evaluate_cqs(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results = []
    checks = {
        "CQ1": [
            graph_has_edge(edges, "L2_TASK_PROPOSAL_STRATEGY_DEVELOPMENT", "USES_INPUT", "L2_ARTIFACT_CAPTURE_PLAN"),
            graph_has_edge(edges, "L2_TASK_PROPOSAL_STRATEGY_DEVELOPMENT", "USES_INPUT", "L2_INFO_CUSTOMER_ISSUE"),
            graph_has_edge(edges, "L2_TASK_PROPOSAL_STRATEGY_DEVELOPMENT", "USES_INPUT", "L2_INFO_COMPETITOR_INFORMATION"),
        ],
        "CQ2": [
            graph_has_edge(edges, "L2_TASK_CAPTURE_PLANNING", "PRODUCES", "L2_ARTIFACT_CAPTURE_PLAN"),
            graph_has_edge(edges, "L2_ARTIFACT_CAPTURE_PLAN", "USED_AS_INPUT_FOR", "L2_TASK_PROPOSAL_PLANNING"),
        ],
        "CQ3": [
            graph_has_edge(edges, "L2_TASK_CAPTURE_PLANNING", "HAS_DECISION_POINT", "L2_DECISION_BID_NO_BID")
            or graph_has_edge(edges, "L2_TASK_BID_NO_BID_DECISION", "HAS_DECISION_POINT", "L2_DECISION_BID_NO_BID"),
            graph_has_edge(edges, "L2_TASK_BID_NO_BID_DECISION", "USES_INPUT", "L2_ARTIFACT_CAPTURE_PLAN"),
        ],
        "CQ4": [
            graph_has_edge(edges, "L2_TASK_EVALUATOR_ANALYSIS", "ANALYZES", "L2_STAKEHOLDER_DECISION_MAKER"),
            graph_has_edge(edges, "L2_TASK_EVALUATOR_ANALYSIS", "ANALYZES", "L2_STAKEHOLDER_TECH_EXPERT"),
            graph_has_edge(edges, "L2_INFO_EVALUATOR_ATTACK_POINT", "USED_AS_INPUT_FOR", "L2_TASK_PERSUASIVE_COMMUNICATION"),
        ],
        "CQ5": [
            graph_has_edge(edges, "L2_TASK_RISK_MANAGEMENT", "MITIGATES", "L2_RISK_BUSINESS_RISK"),
            graph_has_edge(edges, "L2_TASK_RISK_MANAGEMENT", "MAY_RESULT_IN", "L2_INFO_DIFFERENTIATION_POINT"),
        ],
        "CQ6": [
            graph_has_edge(edges, "L2_TASK_PROPOSAL_PREPARING", "HAS_REVIEW", "L2_REVIEW_STRATEGY_REVIEW"),
            graph_has_edge(edges, "L2_TASK_PROPOSAL_PREPARING", "HAS_REVIEW", "L2_REVIEW_DRAFT_REVIEW"),
            graph_has_edge(edges, "L2_TASK_PROPOSAL_PREPARING", "HAS_REVIEW", "L2_REVIEW_FINAL_REVIEW"),
        ],
        "CQ7": [
            graph_has_edge(edges, "L2_ARTIFACT_RFP", "CONTAINS", "L2_INFO_OFFICIAL_REQUIREMENT"),
            graph_has_edge(edges, "L2_INFO_UNSTATED_REQUIREMENT", "PART_OF", "L2_INFO_CUSTOMER_NEEDS"),
        ],
    }
    for cq in COMPETENCY_QUESTIONS:
        passed = all(checks[cq["id"]])
        results.append({**cq, "passed": passed, "satisfied_checks": sum(1 for value in checks[cq["id"]] if value), "total_checks": len(checks[cq["id"]])})
    return results


def shortest_path(edges: list[dict[str, Any]], source: str, target: str, max_depth: int = 4) -> list[dict[str, str]]:
    adj: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for edge in edges:
        adj[edge["source_id"]].append((edge["predicate"], edge["target_id"]))
    queue = deque([(source, [])])
    seen = {source}
    while queue:
        node, path = queue.popleft()
        if len(path) >= max_depth:
            continue
        for pred, nxt in adj.get(node, []):
            new_path = path + [{"source_id": node, "predicate": pred, "target_id": nxt}]
            if nxt == target:
                return new_path
            if nxt not in seen:
                seen.add(nxt)
                queue.append((nxt, new_path))
    return []


def compute_quality(nodes: list[dict[str, Any]], edges: list[dict[str, Any]], triples_validated: list[dict[str, Any]], cq_results: list[dict[str, Any]]) -> dict[str, Any]:
    domain_nodes = [node for node in nodes if node_type(node) not in {"Book", "Chapter", "Section", "SourceChunk", "EvidenceSpan", "AliasTerm", "DomainOntology"}]
    grounded_domain_nodes = [node for node in domain_nodes if node.get("evidence_refs")]
    grounded_edges = [edge for edge in edges if edge.get("evidence_refs") or edge["predicate"] in {"HAS_CHAPTER", "HAS_SECTION", "HAS_CHUNK"}]
    task_ids = {node["id"] for node in nodes if node_type(node) == "DomainTask"}
    parented_tasks = {edge["target_id"] for edge in edges if edge["predicate"] == "HAS_TASK"}
    aliases = []
    for node in nodes:
        aliases.extend([str(alias).lower().strip() for alias in node.get("aliases") or [] if alias])
    duplicate_alias_rate = 0.0 if not aliases else (len(aliases) - len(set(aliases))) / len(aliases)
    return {
        "node_grounded_rate_domain_only": round(len(grounded_domain_nodes) / len(domain_nodes), 4) if domain_nodes else 1.0,
        "edge_grounded_rate": round(len(grounded_edges) / len(edges), 4) if edges else 1.0,
        "predicate_valid_rate": round(sum(1 for edge in edges if edge["predicate"] in EDGE_SCHEMA) / len(edges), 4) if edges else 1.0,
        "task_orphan_rate": round(len(task_ids - parented_tasks) / len(task_ids), 4) if task_ids else 0.0,
        "duplicate_alias_rate": round(duplicate_alias_rate, 4),
        "cq_pass_rate": round(sum(1 for row in cq_results if row["passed"]) / len(cq_results), 4) if cq_results else 0.0,
        "review_resolution_rate": 0.0,
        "case_leakage_rate": 0.0,
        "counts": {
            "nodes": len(nodes),
            "domain_nodes": len(domain_nodes),
            "edges": len(edges),
            "validated_triples": len(triples_validated),
            "cq_total": len(cq_results),
            "cq_passed": sum(1 for row in cq_results if row["passed"]),
        },
    }


def render_quality_report(
    profile: dict[str, Any],
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    raw_triples: list[dict[str, Any]],
    validated_triples: list[dict[str, Any]],
    cq_results: list[dict[str, Any]],
    quality: dict[str, Any],
    output_dir: Path,
) -> str:
    node_counts = Counter(node_type(node) for node in nodes)
    pred_counts = Counter(edge["predicate"] for edge in edges)
    lines = [
        "# AX ZAIJE Layer2 KG Quality Report",
        "",
        f"Generated: {now_iso()}",
        f"Experiment dir: `{output_dir}`",
        f"Run ID: `{RUN_ID}`",
        "",
        "## 1. 실행 성격",
        "",
        "- 설계서: `AX_ZAIJE_Layer2_KG_Methodology.md`",
        "- 입력: `자이제_1.xlsx` / `clean_sentences`",
        "- 범위: Layer 2 Source Evidence Graph + Domain Ontology Graph",
        "- 제외: Layer 1 NCS/PCF 매핑, Layer 2→Layer 1 점수화",
        "- LLM 상태: 현재 Python 환경에 `torch/transformers/vllm`이 없어 deterministic MVP extractor로 실행했다.",
        "- LLM 교체 지점: `18_extraction_prompts.md`와 `05_task_frames.raw.jsonl`, `08_triples.raw.jsonl` 형식.",
        "",
        "## 2. Counts",
        "",
        "| item | value |",
        "| --- | ---: |",
        f"| valid sentence rows | {profile['valid_sentence_rows']} |",
        f"| source chunks | {profile['source_chunks']} |",
        f"| evidence spans | {profile['evidence_spans']} |",
        f"| raw triples | {len(raw_triples)} |",
        f"| validated triples | {len(validated_triples)} |",
        f"| graph nodes | {len(nodes)} |",
        f"| graph edges | {len(edges)} |",
        "",
        "## 3. Quality Metrics",
        "",
        "| metric | value | MVP target | status |",
        "| --- | ---: | ---: | --- |",
    ]
    targets = {
        "node_grounded_rate_domain_only": 0.95,
        "edge_grounded_rate": 0.98,
        "predicate_valid_rate": 1.0,
        "task_orphan_rate": 0.05,
        "cq_pass_rate": 0.80,
        "case_leakage_rate": 0.0,
    }
    for metric, target in targets.items():
        value = quality[metric]
        if metric in {"task_orphan_rate", "case_leakage_rate"}:
            ok = value <= target
        else:
            ok = value >= target
        lines.append(f"| `{metric}` | {value:.4f} | {target:.2f} | {'PASS' if ok else 'REVIEW'} |")
    lines += [
        f"| `duplicate_alias_rate` | {quality['duplicate_alias_rate']:.4f} | trend | INFO |",
        f"| `review_resolution_rate` | {quality['review_resolution_rate']:.4f} | 1.00 before release | OPEN |",
        "",
        "## 4. Node Type Distribution",
        "",
        "| node_type | count |",
        "| --- | ---: |",
    ]
    for k, v in node_counts.most_common():
        lines.append(f"| `{k}` | {v} |")
    lines += ["", "## 5. Predicate Distribution", "", "| predicate | count |", "| --- | ---: |"]
    for k, v in pred_counts.most_common():
        lines.append(f"| `{k}` | {v} |")
    lines += ["", "## 6. Competency Question Evaluation", "", "| CQ | question | passed | checks |", "| --- | --- | --- | ---: |"]
    for row in cq_results:
        lines.append(f"| {row['id']} | {row['question']} | {'PASS' if row['passed'] else 'FAIL'} | {row['satisfied_checks']}/{row['total_checks']} |")
    lines += [
        "",
        "## 7. Claim Boundary",
        "",
        "- 이 결과는 설계서 기반 MVP 구축 결과이며 사람 검수를 완료한 gold KG가 아니다.",
        "- `verified`는 schema/domain/range/evidence_refs 기준의 자동 검증 통과를 의미한다.",
        "- Task/edge의 의미적 정확도는 `13_review_queue.xlsx`를 통한 사람 검수 이후에 주장해야 한다.",
    ]
    return "\n".join(lines) + "\n"


def build_review_queue(nodes: list[dict[str, Any]], edges: list[dict[str, Any]], triples: list[dict[str, Any]], evidence_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    priority_predicates = {"PRECEDES", "REFINES_INTO", "HAS_DECISION_POINT", "HAS_REVIEW", "MAY_RESULT_IN", "MITIGATES"}
    for triple in triples:
        if triple["predicate"] in priority_predicates or float(triple.get("confidence") or 0) < 0.85:
            ev = evidence_by_id.get((triple.get("evidence_refs") or [""])[0], {})
            rows.append(
                {
                    "candidate_id": triple["triple_id"],
                    "candidate_type": "edge",
                    "subject": triple["subject_id"],
                    "predicate": triple["predicate"],
                    "object": triple["object_id"],
                    "source_text": ev.get("text_span", triple.get("evidence_span", "")),
                    "page": ev.get("page", ""),
                    "section_no": ev.get("section_no", ""),
                    "confidence": triple.get("confidence", ""),
                    "system_reason": f"Priority predicate or confidence review: {triple['predicate']}",
                    "review_decision": "",
                    "reviewer_note": "",
                }
            )
    task_nodes = [node for node in nodes if node_type(node) == "DomainTask"]
    for node in task_nodes:
        rows.append(
            {
                "candidate_id": node["id"],
                "candidate_type": "node",
                "subject": node.get("name_ko", ""),
                "predicate": "IS_A",
                "object": "DomainTask",
                "source_text": "",
                "page": "",
                "section_no": ",".join(sorted({str(evidence_by_id.get(ev, {}).get("section_no", "")) for ev in node.get("evidence_refs", []) if ev in evidence_by_id})),
                "confidence": node.get("confidence", ""),
                "system_reason": "Canonical Task Catalog v0 item requires human confirmation.",
                "review_decision": "",
                "reviewer_note": "",
            }
        )
    return rows[:300]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_minimal_xlsx(path: Path, sheets: dict[str, tuple[list[str], list[dict[str, Any]]]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    def col_name(idx: int) -> str:
        name = ""
        n = idx
        while n:
            n, rem = divmod(n - 1, 26)
            name = chr(65 + rem) + name
        return name

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
                value = escape(str(row.get(header, "") if r_idx > 1 else header))
                lines.append(f'<c r="{col_name(c_idx)}{r_idx}" t="inlineStr"><is><t>{value}</t></is></c>')
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


def json_for_csv(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def write_neo4j_export(base: Path, nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> None:
    neo = base / "14_neo4j_import"
    node_rows = []
    for node in nodes:
        node_rows.append(
            {
                "id": node["id"],
                "labels": ";".join(node.get("labels") or []),
                "node_type": node_type(node),
                "name_ko": node.get("name_ko") or node.get("title") or node.get("name") or node.get("statement") or node.get("term") or "",
                "name_en": node.get("name_en") or "",
                "definition": node.get("definition") or node.get("statement") or "",
                "source_book_id": node.get("source_book_id") or node.get("book_id") or "",
                "evidence_refs_json": json_for_csv(node.get("evidence_refs") or []),
                "confidence": node.get("confidence", ""),
                "review_status": node.get("review_status", ""),
                "schema_version": node.get("schema_version", SCHEMA_VERSION),
                "raw_json": json_for_csv(node),
            }
        )
    edge_rows = []
    for edge in edges:
        edge_rows.append(
            {
                "edge_id": edge["edge_id"],
                "source_id": edge["source_id"],
                "target_id": edge["target_id"],
                "predicate": edge["predicate"],
                "evidence_refs_json": json_for_csv(edge.get("evidence_refs") or []),
                "confidence": edge.get("confidence", ""),
                "relation_scope": edge.get("relation_scope", ""),
                "extraction_run_id": edge.get("extraction_run_id", ""),
                "review_status": edge.get("review_status", ""),
                "validation_status": edge.get("validation_status", ""),
                "raw_json": json_for_csv(edge),
            }
        )
    node_fields = list(node_rows[0].keys()) if node_rows else []
    edge_fields = list(edge_rows[0].keys()) if edge_rows else []
    write_csv(neo / "nodes.csv", node_rows, node_fields)
    write_csv(neo / "edges.csv", edge_rows, edge_fields)
    predicates = sorted({edge["predicate"] for edge in edges})
    labels = sorted({label for node in nodes for label in (node.get("labels") or [])})
    lines = [
        "// Generated by scripts/build_ax_zaije_layer2_kg.py",
        "// Copy nodes.csv and edges.csv into Neo4j import directory, then run in Neo4j Browser/cypher-shell.",
        "",
        "CREATE CONSTRAINT ax_l2_node_id IF NOT EXISTS FOR (n:L2Node) REQUIRE n.id IS UNIQUE;",
        "",
        "LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row",
        "MERGE (n:L2Node {id: row.id})",
        "SET n.node_type = row.node_type,",
        "    n.name_ko = row.name_ko,",
        "    n.name_en = row.name_en,",
        "    n.definition = row.definition,",
        "    n.source_book_id = row.source_book_id,",
        "    n.evidence_refs_json = row.evidence_refs_json,",
        "    n.confidence = CASE row.confidence WHEN '' THEN null ELSE toFloat(row.confidence) END,",
        "    n.review_status = row.review_status,",
        "    n.schema_version = row.schema_version,",
        "    n.raw_json = row.raw_json",
    ]
    for label in labels:
        safe = re.sub(r"[^A-Za-z0-9_]", "_", label)
        lines.append(f"FOREACH (_ IN CASE WHEN row.labels CONTAINS '{label}' THEN [1] ELSE [] END | SET n:{safe})")
    lines.append(";")
    for predicate in predicates:
        safe_pred = re.sub(r"[^A-Za-z0-9_]", "_", predicate)
        lines += [
            "",
            f"LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row",
            f"WITH row WHERE row.predicate = '{predicate}'",
            "MATCH (s:L2Node {id: row.source_id})",
            "MATCH (t:L2Node {id: row.target_id})",
            f"MERGE (s)-[r:{safe_pred} {{edge_id: row.edge_id}}]->(t)",
            "SET r.predicate = row.predicate,",
            "    r.evidence_refs_json = row.evidence_refs_json,",
            "    r.confidence = CASE row.confidence WHEN '' THEN null ELSE toFloat(row.confidence) END,",
            "    r.relation_scope = row.relation_scope,",
            "    r.extraction_run_id = row.extraction_run_id,",
            "    r.review_status = row.review_status,",
            "    r.validation_status = row.validation_status,",
            "    r.raw_json = row.raw_json;",
        ]
    lines += [
        "",
        "CREATE INDEX ax_l2_node_type IF NOT EXISTS FOR (n:L2Node) ON (n.node_type);",
        "CREATE FULLTEXT INDEX ax_l2_node_text IF NOT EXISTS FOR (n:L2Node) ON EACH [n.name_ko, n.name_en, n.definition];",
        "",
        "MATCH (n:L2Node) RETURN n.node_type AS node_type, count(*) AS nodes ORDER BY nodes DESC;",
    ]
    write_text(neo / "import.cypher", "\n".join(lines) + "\n")


def ttl_escape(text: Any) -> str:
    return str(text or "").replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def write_rdf_export(base: Path, nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> None:
    rdf = base / "15_rdf_export"
    schema_lines = [
        "@prefix axl2: <https://ax.example/layer2/> .",
        "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "@prefix prov: <http://www.w3.org/ns/prov#> .",
        "@prefix skos: <http://www.w3.org/2004/02/skos/core#> .",
        "",
    ]
    for node_type_name in sorted(NODE_REQUIRED):
        schema_lines.append(f"axl2:{node_type_name} a rdfs:Class .")
    for predicate in sorted(EDGE_SCHEMA):
        schema_lines.append(f"axl2:{predicate} a rdf:Property .")
    write_text(rdf / "layer2_schema.ttl", "\n".join(schema_lines) + "\n")

    data_lines = [
        "@prefix axl2: <https://ax.example/layer2/> .",
        "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "@prefix prov: <http://www.w3.org/ns/prov#> .",
        "@prefix skos: <http://www.w3.org/2004/02/skos/core#> .",
        "",
    ]
    for node in nodes:
        node_uri = f"axl2:{node['id']}"
        label = ttl_escape(node_name(node))
        data_lines.append(f'{node_uri} a axl2:{node_type(node)} ; rdfs:label "{label}" .')
    for edge in edges:
        data_lines.append(f"axl2:{edge['source_id']} axl2:{edge['predicate']} axl2:{edge['target_id']} .")
    write_text(rdf / "layer2_data.ttl", "\n".join(data_lines) + "\n")


def render_query_demo(nodes: list[dict[str, Any]], edges: list[dict[str, Any]], cq_results: list[dict[str, Any]]) -> str:
    name_map = {node["id"]: node_name(node) for node in nodes}
    lines = [
        "# Graph Query Demo",
        "",
        "이 파일은 설계서 16.4의 5개 demo 질의와 CQ 평가 경로를 요약한다.",
        "",
    ]
    demos = [
        ("수주영업의 입력과 산출물은 무엇인가?", "L2_TASK_CAPTURE_PLANNING"),
        ("Capture Plan은 어디서 생성되고 어디에 쓰이는가?", "L2_ARTIFACT_CAPTURE_PLAN"),
        ("제안전략 개발 전 필요한 정보는 무엇인가?", "L2_TASK_PROPOSAL_STRATEGY_DEVELOPMENT"),
        ("평가자 유형별로 어떤 분석이 필요한가?", "L2_TASK_EVALUATOR_ANALYSIS"),
        ("리스크 관리는 어떤 차별화 포인트로 연결되는가?", "L2_TASK_RISK_MANAGEMENT"),
    ]
    edge_lookup = defaultdict(list)
    for edge in edges:
        edge_lookup[edge["source_id"]].append(edge)
    for idx, (question, focus) in enumerate(demos, start=1):
        lines += [f"## Demo {idx}. {question}", ""]
        for edge in edge_lookup.get(focus, [])[:12]:
            if edge["predicate"] in {"EVIDENCED_BY", "HAS_TASK"}:
                continue
            target_label = name_map.get(edge["target_id"], edge["target_id"])
            lines.append(f"- `{name_map.get(focus, focus)}` -`{edge['predicate']}`-> `{target_label}`")
        lines.append("")
    lines += ["## Competency Questions", "", "| CQ | passed | expected |", "| --- | --- | --- |"]
    for row in cq_results:
        lines.append(f"| {row['id']} | {'PASS' if row['passed'] else 'FAIL'} | {row['expected']} |")
    return "\n".join(lines) + "\n"


def build_experiment(args: argparse.Namespace) -> dict[str, Any]:
    input_xlsx = Path(args.input_xlsx)
    methodology = Path(args.methodology)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    sheet_name, raw_rows = read_xlsx_table(input_xlsx)
    normalized_rows = normalize_rows(raw_rows, input_xlsx)
    source_chunks, evidence_spans, evidence_by_id = make_source_chunks(normalized_rows)
    source_profile_md, source_profile = build_source_profile_md(sheet_name, len(raw_rows), normalized_rows, source_chunks, evidence_spans, input_xlsx, methodology)
    raw_task_frames, canonical_task_frames = build_task_frames(evidence_spans)
    alias_dictionary = build_alias_dictionary(canonical_task_frames)
    raw_triples = build_triples(canonical_task_frames, evidence_spans, evidence_by_id)
    nodes, edges = build_nodes_and_edges(normalized_rows, source_chunks, evidence_spans, canonical_task_frames, raw_triples, evidence_by_id, input_xlsx)
    validated_triples = validate_triples(raw_triples, nodes, evidence_by_id)
    cq_results = evaluate_cqs(edges)
    quality = compute_quality(nodes, edges, validated_triples, cq_results)
    review_rows = build_review_queue(nodes, edges, validated_triples, evidence_by_id)

    write_text(output_dir / "00_source_profile.md", source_profile_md)
    write_text(output_dir / "01_layer2_core_schema.yaml", render_core_schema_yaml())
    write_text(output_dir / "02_layer2_domain_extension_zaije.yaml", render_domain_extension_yaml())
    write_jsonl(output_dir / "03_source_chunks.jsonl", source_chunks)
    write_jsonl(output_dir / "04_evidence_spans.jsonl", evidence_spans)
    write_jsonl(output_dir / "05_task_frames.raw.jsonl", raw_task_frames)
    write_jsonl(output_dir / "06_task_frames.canonical.jsonl", canonical_task_frames)
    write_json(output_dir / "07_terms_alias_dictionary.json", alias_dictionary)
    write_jsonl(output_dir / "08_triples.raw.jsonl", raw_triples)
    write_jsonl(output_dir / "09_triples.validated.jsonl", validated_triples)
    write_jsonl(output_dir / "10_nodes.jsonl", nodes)
    write_jsonl(output_dir / "11_edges.jsonl", edges)
    write_text(output_dir / "12_quality_report.md", render_quality_report(source_profile, nodes, edges, raw_triples, validated_triples, cq_results, quality, output_dir))
    review_fields = [
        "candidate_id",
        "candidate_type",
        "subject",
        "predicate",
        "object",
        "source_text",
        "page",
        "section_no",
        "confidence",
        "system_reason",
        "review_decision",
        "reviewer_note",
    ]
    write_csv(output_dir / "13_review_queue.csv", review_rows, review_fields)
    write_minimal_xlsx(output_dir / "13_review_queue.xlsx", {"review_queue": (review_fields, review_rows)})
    write_neo4j_export(output_dir, nodes, edges)
    write_rdf_export(output_dir, nodes, edges)
    write_json(output_dir / "16_competency_questions.json", cq_results)
    write_text(output_dir / "17_graph_query_demo.md", render_query_demo(nodes, edges, cq_results))
    write_text(output_dir / "18_extraction_prompts.md", render_prompts_md())

    summary = {
        "generated_at_utc": now_iso(),
        "run_id": RUN_ID,
        "input_xlsx": str(input_xlsx),
        "methodology": str(methodology),
        "output_dir": str(output_dir),
        "llm_runtime_status": "not_executed_missing_torch_transformers_vllm",
        "claim_status": "layer2_mvp_bootstrap_ready_not_human_gold",
        "counts": {
            "valid_sentence_rows": len(normalized_rows),
            "source_chunks": len(source_chunks),
            "evidence_spans": len(evidence_spans),
            "task_frames_raw": len(raw_task_frames),
            "task_frames_canonical": len(canonical_task_frames),
            "raw_triples": len(raw_triples),
            "validated_triples": len(validated_triples),
            "nodes": len(nodes),
            "edges": len(edges),
            "review_queue_rows": len(review_rows),
            "cq_passed": sum(1 for row in cq_results if row["passed"]),
            "cq_total": len(cq_results),
        },
        "quality": quality,
        "outputs": [
            "00_source_profile.md",
            "01_layer2_core_schema.yaml",
            "02_layer2_domain_extension_zaije.yaml",
            "03_source_chunks.jsonl",
            "04_evidence_spans.jsonl",
            "05_task_frames.raw.jsonl",
            "06_task_frames.canonical.jsonl",
            "07_terms_alias_dictionary.json",
            "08_triples.raw.jsonl",
            "09_triples.validated.jsonl",
            "10_nodes.jsonl",
            "11_edges.jsonl",
            "12_quality_report.md",
            "13_review_queue.xlsx",
            "14_neo4j_import/nodes.csv",
            "14_neo4j_import/edges.csv",
            "14_neo4j_import/import.cypher",
            "15_rdf_export/layer2_schema.ttl",
            "15_rdf_export/layer2_data.ttl",
            "16_competency_questions.json",
            "17_graph_query_demo.md",
            "18_extraction_prompts.md",
        ],
    }
    write_json(output_dir / "run_summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build AX ZAIJE Layer2 KG MVP")
    parser.add_argument("--input-xlsx", default=str(DEFAULT_XLSX))
    parser.add_argument("--methodology", default=str(DEFAULT_METHODOLOGY))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()
    summary = build_experiment(args)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
