#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rebuild AX ZAIJE Layer2 KG with methodology-v2 schema traceability.

This is a replay build: it reuses previously saved OpenAI raw responses and
re-materializes the KG while adding explicit traceability for how the schema,
canonical inventory, and predicates were constructed.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import build_ax_zaije_layer2_kg as base  # noqa: E402
import run_ax_zaije_openai_llm_kg as openai_run  # noqa: E402


RUN_ID = "RUN_2026_07_08_METHOD_V2_REPLAY_001"
DEFAULT_RAW_DIR = Path("experiments/ax_zaije_layer2_kg_openai_20260707/layer2_kg")
DEFAULT_OUTPUT_DIR = Path("experiments/ax_zaije_layer2_kg_openai_methodology_v2_20260708/layer2_kg")


NODE_TYPE_DERIVATION = {
    "DomainOntology": ("schema_root", "Layer2 도메인 KG 전체를 하나의 스키마 인스턴스로 묶기 위한 root node type."),
    "Book": ("source_evidence_graph", "입력 문서 전체를 provenance의 최상위 원천으로 보존하기 위한 node type."),
    "Chapter": ("source_evidence_graph", "원문의 장 구조를 보존하여 KG 근거를 문서 구조와 연결하기 위한 node type."),
    "Section": ("source_evidence_graph", "원문의 절 단위 문맥과 페이지 범위를 보존하기 위한 node type."),
    "SourceChunk": ("source_evidence_graph", "LLM 입력 단위와 검색 단위를 분리 보존하기 위한 node type."),
    "EvidenceSpan": ("source_evidence_graph", "문장/근거 span을 독립 node로 두어 모든 domain node/edge를 근거 문장에 연결하기 위한 node type."),
    "DomainProcess": ("domain_metamodel", "여러 DomainTask를 상위 업무 흐름으로 묶기 위한 node type."),
    "DomainTask": ("task_frame_schema", "입력, 산출물, 수행 역할, 의사결정, 원칙을 갖는 반복 가능한 업무 단위를 표현하기 위한 node type."),
    "Step": ("task_frame_schema", "DomainTask 내부의 세부 절차가 필요한 경우 확장하기 위한 node type."),
    "Artifact": ("task_frame_schema", "업무 수행 중 생성되거나 사용되는 문서, 계획서, 표, 산출물을 표현하기 위한 node type."),
    "InformationObject": ("task_frame_schema", "분석 대상 정보, 요구조건, 고객 니즈, 평가자 정보처럼 문서가 아닌 정보 객체를 표현하기 위한 node type."),
    "DecisionPoint": ("task_frame_schema", "Bid/No-Bid처럼 업무 흐름에서 판단이 필요한 지점을 표현하기 위한 node type."),
    "Role": ("task_frame_schema", "PM, 제안팀, 영업대표 등 업무 수행 주체를 표현하기 위한 node type."),
    "Stakeholder": ("task_frame_schema", "고객, 평가자, 의사결정자 등 업무가 대상으로 삼는 이해관계자를 표현하기 위한 node type."),
    "Principle": ("task_frame_schema", "고객 중심, 프로세스 관리 등 업무 수행 원칙을 표현하기 위한 node type."),
    "StrategyPattern": ("task_frame_schema", "수주전략, 제안전략, 발표전략처럼 재사용 가능한 전략 패턴을 표현하기 위한 node type."),
    "Risk": ("task_frame_schema", "수주/제안 과정에서 관리해야 하는 위험 요인을 표현하기 위한 node type."),
    "Metric": ("task_frame_schema", "수주율 등 성과 지표를 표현하기 위한 node type."),
    "ReviewType": ("task_frame_schema", "전략 리뷰, 초안 리뷰, 최종 리뷰 등 검토 단계를 표현하기 위한 node type."),
    "DecisionOutcome": ("task_frame_schema", "Bid, No-Bid처럼 의사결정 결과를 표현하기 위한 node type."),
    "Condition": ("task_frame_schema", "특정 위험 또는 전략이 발생하는 조건을 표현하기 위한 확장 node type."),
    "AliasTerm": ("skos_alias_management", "한국어/영어/약어/동의어를 canonical node에 연결하기 위한 node type."),
}


PREDICATE_DERIVATION = {
    "HAS_CHAPTER": ("source_structure", "Book에서 Chapter로 이어지는 원문 구조 보존 관계."),
    "HAS_SECTION": ("source_structure", "Chapter에서 Section으로 이어지는 원문 구조 보존 관계."),
    "HAS_CHUNK": ("source_structure", "Section에서 LLM/검색 입력 단위인 SourceChunk로 이어지는 관계."),
    "HAS_PROCESS": ("schema_scaffold", "Layer2 ontology root가 상위 DomainProcess를 포함함을 표현하는 scaffold 관계."),
    "HAS_TASK": ("task_catalog", "DomainProcess가 하위 DomainTask를 포함함을 표현하는 업무 catalog 관계."),
    "HAS_SUBTASK": ("task_decomposition", "Task 내부 세부 task 또는 step 분해 관계."),
    "CONTAINS": ("document_information_composition", "Artifact나 InformationObject가 하위 정보 객체를 포함하는 관계."),
    "PART_OF": ("document_information_composition", "정보 객체/산출물이 더 큰 정보 객체/산출물의 일부임을 표현하는 관계."),
    "DISCOVERS": ("task_information_flow", "업무 수행을 통해 숨은 니즈나 정보를 발견하는 관계."),
    "PRECEDES": ("workflow_order", "업무 또는 step의 선후행 순서를 표현하는 관계."),
    "USES_INPUT": ("task_io", "Task가 입력 산출물/정보/전략을 사용하는 관계."),
    "USED_AS_INPUT_FOR": ("task_io", "산출물/정보/전략이 후속 Task의 입력으로 사용되는 역방향 탐색 관계."),
    "PRODUCES": ("task_io", "Task가 산출물/정보/전략을 만들어내는 관계."),
    "PERFORMED_BY": ("responsibility", "Task/Step을 수행하는 Role을 연결하는 관계."),
    "TARGETS_STAKEHOLDER": ("stakeholder_targeting", "Task나 전략이 대상으로 삼는 이해관계자를 연결하는 관계."),
    "ANALYZES": ("analysis_activity", "Task/Step이 정보, 이해관계자, 위험을 분석하는 관계."),
    "DEVELOPS": ("development_activity", "Task/Step이 산출물이나 전략을 개발하는 관계."),
    "REFINES_INTO": ("strategy_refinement", "산출물/전략이 더 구체적인 산출물/전략으로 정교화되는 관계."),
    "DECIDES": ("decision_model", "DecisionPoint나 Role이 특정 DecisionOutcome을 결정하는 관계."),
    "HAS_DECISION_POINT": ("decision_model", "Task/Process에 포함된 의사결정 지점을 연결하는 관계."),
    "EVALUATES": ("review_evaluation", "Task/Role이 산출물, 전략, 지표를 평가하는 관계."),
    "HAS_REVIEW": ("review_evaluation", "Task/Artifact가 필요한 review type을 갖는 관계."),
    "HAS_PRINCIPLE": ("principle_alignment", "Task/StrategyPattern에 적용되는 업무 원칙을 연결하는 관계."),
    "MITIGATES": ("risk_management", "Task/StrategyPattern이 Risk를 완화하는 관계."),
    "INCREASES_RISK": ("risk_management", "Condition이 Risk를 증가시키는 관계."),
    "MAY_RESULT_IN": ("outcome_link", "Task/StrategyPattern이 정보/산출물/지표로 이어질 수 있음을 표현하는 관계."),
    "ALIAS_OF": ("skos_alias_management", "AliasTerm을 canonical node에 연결하는 동의어 관계."),
    "EVIDENCED_BY": ("provenance", "Domain node/edge를 EvidenceSpan에 연결하는 provenance 관계."),
}


PRIORITY_ARTIFACT_IDS = {
    "L2_ARTIFACT_RFP",
    "L2_ARTIFACT_CAPTURE_PLAN",
    "L2_ARTIFACT_PROPOSAL_PLAN",
    "L2_ARTIFACT_PMP",
    "L2_ARTIFACT_PDW",
    "L2_ARTIFACT_BCM",
    "L2_ARTIFACT_STRATEGY_STATEMENT",
}


def configure_run_id() -> None:
    base.RUN_ID = RUN_ID
    openai_run.RUN_ID = RUN_ID


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def load_raw_rows(raw_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    task_rows = openai_run.read_jsonl(raw_dir / "19_openai_task_frame_links.raw.jsonl")
    triple_rows = openai_run.read_jsonl(raw_dir / "20_openai_triples.raw.jsonl")
    if not task_rows:
        raise FileNotFoundError(f"No task frame raw rows found in {raw_dir}")
    if not triple_rows:
        raise FileNotFoundError(f"No triple raw rows found in {raw_dir}")
    return task_rows, triple_rows


def usage_from_raw(task_rows: list[dict[str, Any]], triple_rows: list[dict[str, Any]]) -> dict[str, Any]:
    usage: Counter[str] = Counter()
    for row in task_rows + triple_rows:
        openai_run.add_usage(usage, row.get("usage"))
    return dict(usage)


def reconcile_task_frame_evidence_ids(
    task_rows: list[dict[str, Any]],
    evidence_spans: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Map placeholder/invalid task-link evidence IDs to the chunk evidence IDs.

    The saved OpenAI task-frame rows sometimes used EV_ZAIJE_000000 although the
    actual EvidenceSpan sequence starts at EV_ZAIJE_000001. The raw rows are kept
    unchanged in file 19; file 19b records this deterministic reconciliation.
    """
    valid_ids = {ev["id"] for ev in evidence_spans}
    by_section_chunk: dict[str, list[str]] = {}
    by_section: dict[str, list[str]] = {}
    for ev in evidence_spans:
        by_section_chunk.setdefault(str(ev.get("section_chunk_id") or ""), []).append(ev["id"])
        by_section.setdefault(str(ev.get("section_no") or ""), []).append(ev["id"])

    rows: list[dict[str, Any]] = []
    stats = {
        "task_frame_links": 0,
        "links_with_valid_original_evidence": 0,
        "links_reconciled_to_section_chunk": 0,
        "links_unresolved": 0,
    }
    for row in task_rows:
        updated = json.loads(json.dumps(row, ensure_ascii=False))
        row_reconciled = 0
        parsed = updated.get("parsed") or {}
        updated["replay_run_id"] = RUN_ID
        for link in parsed.get("task_frame_links") or []:
            stats["task_frame_links"] += 1
            original_ids = [str(ev).strip() for ev in link.get("evidence_ids") or [] if str(ev).strip()]
            valid_original = [ev_id for ev_id in original_ids if ev_id in valid_ids]
            if valid_original:
                link["evidence_ids"] = valid_original
                stats["links_with_valid_original_evidence"] += 1
                continue
            replacement = by_section_chunk.get(str(row.get("chunk_id") or ""), [])[:8]
            if not replacement:
                replacement = by_section.get(str(row.get("section_no") or ""), [])[:8]
            if replacement:
                link["evidence_ids"] = replacement
                link["evidence_id_reconciliation"] = {
                    "status": "reconciled_to_section_chunk",
                    "original_evidence_ids": original_ids,
                    "reconciled_evidence_ids": replacement,
                    "reason": "LLM returned placeholder or invalid evidence id for a section-summary task-frame link.",
                }
                row_reconciled += 1
                stats["links_reconciled_to_section_chunk"] += 1
            else:
                link["evidence_id_reconciliation"] = {
                    "status": "unresolved",
                    "original_evidence_ids": original_ids,
                }
                stats["links_unresolved"] += 1
        updated["task_frame_evidence_reconciliation_count"] = row_reconciled
        rows.append(updated)
    return rows, stats


def referenced_by_task_index() -> dict[str, list[str]]:
    refs: dict[str, list[str]] = {}
    for seed in base.TASK_SEEDS:
        task_id = seed["task_id"]
        for field in ["inputs", "outputs", "roles", "stakeholders", "principles", "risks", "decision_points", "reviews"]:
            for entity_id in seed.get(field, []):
                refs.setdefault(entity_id, []).append(task_id)
    return {key: sorted(set(value)) for key, value in refs.items()}


def make_node_type_traceability() -> list[dict[str, Any]]:
    rows = []
    for node_type_name, required in base.NODE_REQUIRED.items():
        category, rationale = NODE_TYPE_DERIVATION.get(node_type_name, ("schema_extension", "Layer2 schema 확장을 위해 정의한 node type."))
        rows.append(
            {
                "node_type": node_type_name,
                "derivation_category": category,
                "required_fields_json": json.dumps(required, ensure_ascii=False),
                "design_rationale": rationale,
                "methodology_anchor": "AX_ZAIJE_Layer2_KG_Methodology.md sections 5, 9, 17",
            }
        )
    return rows


def make_process_traceability(evidence_spans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    sections = {str(ev.get("section_no") or "") for ev in evidence_spans}
    for process_id, process in base.PROCESSES.items():
        matched_sections = [section for section in process.get("sections", []) if any(s == section or s.startswith(f"{section}.") for s in sections)]
        rows.append(
            {
                "canonical_id": process_id,
                "node_type": "DomainProcess",
                "label_ko": process["name_ko"],
                "id_construction_rule": "L2_PROCESS_<UPPERCASE_ENGLISH_PHASE_NAME>",
                "derivation_basis": "source section grouping + Task Catalog 상위 업무 흐름",
                "source_sections_json": json.dumps(process.get("sections", []), ensure_ascii=False),
                "matched_source_sections_json": json.dumps(matched_sections, ensure_ascii=False),
                "definition": process["definition"],
            }
        )
    return rows


def make_task_traceability(task_frames: list[dict[str, Any]]) -> list[dict[str, Any]]:
    frame_by_id = {frame["id"]: frame for frame in task_frames}
    rows = []
    for seed in base.TASK_SEEDS:
        frame = frame_by_id.get(seed["task_id"], {})
        rows.append(
            {
                "canonical_id": seed["task_id"],
                "node_type": "DomainTask",
                "label_ko": seed["task_name_ko"],
                "id_construction_rule": "L2_TASK_<UPPERCASE_ENGLISH_TASK_NAME>",
                "derivation_basis": "section evidence + activity verb + input/output/role frame + CQ relevance",
                "parent_process_id": seed["parent_process_id"],
                "source_sections_json": json.dumps(seed.get("sections", []), ensure_ascii=False),
                "keywords_json": json.dumps(seed.get("keywords", []), ensure_ascii=False),
                "inputs_json": json.dumps(seed.get("inputs", []), ensure_ascii=False),
                "outputs_json": json.dumps(seed.get("outputs", []), ensure_ascii=False),
                "roles_json": json.dumps(seed.get("roles", []), ensure_ascii=False),
                "grounding_evidence_count": len(frame.get("evidence_refs") or []),
                "llm_task_frame_link_count": frame.get("llm_task_frame_link_count", 0),
                "llm_confirmed_evidence_count": len(frame.get("llm_confirmed_evidence_refs") or []),
                "evidence_refs_json": json.dumps((frame.get("evidence_refs") or [])[:10], ensure_ascii=False),
                "definition": seed["definition"],
            }
        )
    return rows


def make_entity_traceability(evidence_spans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    task_refs = referenced_by_task_index()
    rows = []
    for entity_id, entity in base.ENTITIES.items():
        evidence_refs = base.evidence_for_entity(entity_id, evidence_spans, [], limit=8)
        label = entity.get("name_ko") or entity.get("statement") or entity_id
        referenced_by = task_refs.get(entity_id, [])
        if entity_id in PRIORITY_ARTIFACT_IDS:
            basis = "priority artifact candidate in methodology + source evidence keyword match"
        elif referenced_by:
            basis = "referenced by canonical task frame slot"
        else:
            basis = "domain extension concept retained for schema/CQ coverage"
        rows.append(
            {
                "canonical_id": entity_id,
                "node_type": entity["type"],
                "label_ko": label,
                "id_construction_rule": "L2_<TYPE_OR_ROLE>_<UPPERCASE_ENGLISH_CANONICAL_LABEL>",
                "derivation_basis": basis,
                "artifact_or_concept_kind": entity.get("artifact_type") or entity.get("info_type") or entity.get("role_type") or entity.get("stakeholder_type") or entity.get("risk_type") or entity.get("review_stage") or entity.get("outcome_type") or "",
                "aliases_json": json.dumps(entity.get("aliases") or [], ensure_ascii=False),
                "keywords_json": json.dumps(entity.get("keywords") or [], ensure_ascii=False),
                "referenced_by_task_ids_json": json.dumps(referenced_by, ensure_ascii=False),
                "evidence_refs_json": json.dumps(evidence_refs, ensure_ascii=False),
                "evidence_match_rule": "alias/keyword/name string match over EvidenceSpan text; evidence is for grounding and review, not human gold confirmation",
            }
        )
    return rows


def make_predicate_traceability() -> list[dict[str, Any]]:
    domain_predicates = set(openai_run.DOMAIN_PREDICATES)
    rows = []
    for predicate, (domain, range_) in base.EDGE_SCHEMA.items():
        category, rationale = PREDICATE_DERIVATION.get(predicate, ("schema_extension", "Layer2 schema 확장을 위해 정의한 predicate."))
        rows.append(
            {
                "predicate": predicate,
                "derivation_category": category,
                "domain_json": json.dumps(domain or ["Any"], ensure_ascii=False),
                "range_json": json.dumps(range_ or ["Any"], ensure_ascii=False),
                "allowed_for_llm_extraction": predicate in domain_predicates,
                "design_rationale": rationale,
                "predicate_relation_note": "predicate는 edge/relation의 type이며, 실제 relation instance는 subject-predicate-object triple 또는 graph edge이다.",
            }
        )
    return rows


def render_schema_derivation_md(
    node_type_rows: list[dict[str, Any]],
    process_rows: list[dict[str, Any]],
    task_rows: list[dict[str, Any]],
    entity_rows: list[dict[str, Any]],
    predicate_rows: list[dict[str, Any]],
) -> str:
    node_counts = Counter(row["node_type"] for row in entity_rows)
    llm_predicates = sum(1 for row in predicate_rows if row["allowed_for_llm_extraction"])
    lines = [
        "# AX ZAIJE Layer2 KG Methodology v2 Schema Derivation",
        "",
        f"Generated: {base.now_iso()}",
        f"Run ID: `{RUN_ID}`",
        "",
        "## 1. Schema 설계 절차",
        "",
        "이번 v2 방법론에서는 KG 구축을 두 단계로 분리했다.",
        "",
        "| 단계 | 산출물 | 설명 |",
        "| --- | --- | --- |",
        "| A. Schema/Inventory 설계 | node type, canonical node, predicate schema | LLM이 자유롭게 node/predicate를 만들기 전에 사용할 어휘와 relation type을 정의한다. |",
        "| B. Evidence-grounded LLM extraction | task-frame link, triple 후보 | LLM은 원문 evidence에서 schema 안에 들어맞는 relation 후보만 제안한다. |",
        "| C. Validation/Materialization | 최종 nodes/edges | canonical id, allowed predicate, evidence id, domain/range, confidence threshold를 통과한 항목만 그래프에 반영한다. |",
        "",
        "즉 `L2_ARTIFACT_RFP`, `L2_TASK_CAPTURE_PLANNING`, `CONTAINS` 같은 값은 LLM이 즉석에서 만든 값이 아니다. 설계 단계에서 만든 controlled vocabulary이고, LLM은 그 후보 집합 안에서만 subject, predicate, object를 선택했다.",
        "",
        "## 2. ID 생성 규칙",
        "",
        "| 대상 | 규칙 | 예시 |",
        "| --- | --- | --- |",
        "| DomainProcess | `L2_PROCESS_<업무흐름>` | `L2_PROCESS_CAPTURE_PLANNING` |",
        "| DomainTask | `L2_TASK_<업무활동>` | `L2_TASK_CAPTURE_PLANNING` |",
        "| Artifact | `L2_ARTIFACT_<산출물명>` | `L2_ARTIFACT_RFP` |",
        "| InformationObject | `L2_INFO_<정보객체명>` | `L2_INFO_OFFICIAL_REQUIREMENT` |",
        "| Role | `L2_ROLE_<역할명>` | `L2_ROLE_PROPOSAL_TEAM` |",
        "| Predicate | 대문자 동사/관계구 | `USES_INPUT`, `PRODUCES`, `CONTAINS` |",
        "",
        "ID는 사람이 읽을 수 있는 stable canonical id로 설계했다. 동일 개념의 한국어, 영어, 약어는 `AliasTerm`과 `ALIAS_OF`로 연결한다.",
        "",
        "## 3. Node Type 도출",
        "",
        "| category | count |",
        "| --- | ---: |",
    ]
    for category, count in Counter(row["derivation_category"] for row in node_type_rows).most_common():
        lines.append(f"| `{category}` | {count} |")
    lines += [
        "",
        "Node type은 원문 구조를 추적하기 위한 Source Evidence Graph 유형과, 업무 지식을 표현하기 위한 Task Frame 유형으로 나누었다.",
        "",
        "## 4. Canonical Process/Task 도출",
        "",
        f"- Canonical process: {len(process_rows)}개",
        f"- Canonical task: {len(task_rows)}개",
        "",
        "Process는 책의 장/절 흐름을 업무 단계로 묶어 만들었다. Task는 단순 섹션 제목이 아니라, 원문에서 활동, 입력, 산출물, 역할, 의사결정 또는 후속 업무 연결이 확인되는 단위를 후보로 삼았다.",
        "",
        "| task id | label | parent process | grounding evidence | valid LLM links |",
        "| --- | --- | --- | ---: | ---: |",
    ]
    for row in task_rows:
        lines.append(
            f"| `{row['canonical_id']}` | {row['label_ko']} | `{row['parent_process_id']}` | "
            f"{row['grounding_evidence_count']} | {row['llm_task_frame_link_count']} |"
        )
    lines += [
        "",
        "## 5. Canonical Entity 도출",
        "",
        "| node type | count |",
        "| --- | ---: |",
    ]
    for node_type_name, count in node_counts.most_common():
        lines.append(f"| `{node_type_name}` | {count} |")
    lines += [
        "",
        "Entity는 세 가지 기준으로 포함했다.",
        "",
        "1. 설계서에서 우선 인식 대상으로 지정된 Artifact.",
        "2. Task Frame의 input/output/role/stakeholder/principle/risk/review slot에 필요한 개념.",
        "3. Competency Question 경로를 평가하기 위해 필요한 핵심 정보 객체.",
        "",
        "각 entity는 alias, keyword, preferred label을 이용해 EvidenceSpan과 자동 연결했고, 이 근거는 사람 검수 전 grounding 및 review queue 생성을 위한 것이다.",
        "",
        "## 6. Predicate 도출",
        "",
        f"- 전체 predicate: {len(predicate_rows)}개",
        f"- LLM 추출 허용 predicate: {llm_predicates}개",
        "",
        "Predicate는 relation과 거의 같은 개념이지만 정확히는 relation type이다. 예를 들어 `CONTAINS`는 relation type이고, 실제 relation instance는 다음과 같은 edge이다.",
        "",
        "```text",
        "L2_ARTIFACT_RFP -[CONTAINS]-> L2_INFO_OFFICIAL_REQUIREMENT",
        "```",
        "",
        "| predicate | category | domain | range | LLM allowed |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in predicate_rows:
        allowed = "yes" if row["allowed_for_llm_extraction"] else "no"
        lines.append(f"| `{row['predicate']}` | `{row['derivation_category']}` | `{row['domain_json']}` | `{row['range_json']}` | {allowed} |")
    lines += [
        "",
        "## 7. 논문 작성 시 표현",
        "",
        "본 연구에서는 LLM을 schema author로 사용하지 않고, schema-constrained extractor로 사용했다. 먼저 문헌 기반/도메인 기반 설계 절차를 통해 Layer2 node type, canonical inventory, allowed predicate, domain/range constraint를 구성했다. 이후 OpenAI LLM은 각 chunk에서 evidence id와 함께 canonical subject, allowed predicate, canonical object를 선택하도록 제한되었다. 최종 KG 반영은 canonical id validation, predicate validation, domain/range validation, evidence validation, confidence threshold, SPO deduplication을 통과한 경우로 한정했다.",
    ]
    return "\n".join(lines) + "\n"


def write_traceability_outputs(
    output_dir: Path,
    evidence_spans: list[dict[str, Any]],
    task_frames: list[dict[str, Any]],
) -> dict[str, Any]:
    node_type_rows = make_node_type_traceability()
    process_rows = make_process_traceability(evidence_spans)
    task_rows = make_task_traceability(task_frames)
    entity_rows = make_entity_traceability(evidence_spans)
    predicate_rows = make_predicate_traceability()
    inventory_rows = process_rows + task_rows + entity_rows

    base.write_csv(
        output_dir / "25_node_type_traceability.csv",
        node_type_rows,
        ["node_type", "derivation_category", "required_fields_json", "design_rationale", "methodology_anchor"],
    )
    base.write_csv(
        output_dir / "26_canonical_inventory_traceability.csv",
        inventory_rows,
        sorted({key for row in inventory_rows for key in row.keys()}),
    )
    base.write_csv(
        output_dir / "27_predicate_schema_traceability.csv",
        predicate_rows,
        ["predicate", "derivation_category", "domain_json", "range_json", "allowed_for_llm_extraction", "design_rationale", "predicate_relation_note"],
    )
    write_jsonl(output_dir / "25_node_type_traceability.jsonl", node_type_rows)
    write_jsonl(output_dir / "26_canonical_inventory_traceability.jsonl", inventory_rows)
    write_jsonl(output_dir / "27_predicate_schema_traceability.jsonl", predicate_rows)
    schema_md = render_schema_derivation_md(node_type_rows, process_rows, task_rows, entity_rows, predicate_rows)
    base.write_text(output_dir / "28_methodology_schema_derivation.md", schema_md)
    base.write_json(
        output_dir / "28_methodology_schema_derivation.json",
        {
            "generated_at_utc": base.now_iso(),
            "run_id": RUN_ID,
            "schema_construction_claim": "schema-constrained evidence-grounded KG construction with explicit schema derivation traceability",
            "id_convention": {
                "process": "L2_PROCESS_<UPPERCASE_ENGLISH_PHASE_NAME>",
                "task": "L2_TASK_<UPPERCASE_ENGLISH_TASK_NAME>",
                "artifact": "L2_ARTIFACT_<UPPERCASE_ENGLISH_CANONICAL_LABEL>",
                "information_object": "L2_INFO_<UPPERCASE_ENGLISH_CANONICAL_LABEL>",
                "predicate": "UPPERCASE_VERB_OR_RELATION_PHRASE",
            },
            "counts": {
                "node_types": len(node_type_rows),
                "canonical_processes": len(process_rows),
                "canonical_tasks": len(task_rows),
                "canonical_entities": len(entity_rows),
                "predicates": len(predicate_rows),
                "llm_allowed_predicates": sum(1 for row in predicate_rows if row["allowed_for_llm_extraction"]),
            },
            "traceability_files": [
                "25_node_type_traceability.csv",
                "25_node_type_traceability.jsonl",
                "26_canonical_inventory_traceability.csv",
                "26_canonical_inventory_traceability.jsonl",
                "27_predicate_schema_traceability.csv",
                "27_predicate_schema_traceability.jsonl",
                "28_methodology_schema_derivation.md",
            ],
        },
    )
    return {
        "node_type_rows": len(node_type_rows),
        "canonical_inventory_rows": len(inventory_rows),
        "predicate_rows": len(predicate_rows),
    }


def render_methodology_v2_run_report(
    output_dir: Path,
    raw_dir: Path,
    summary: dict[str, Any],
    traceability_counts: dict[str, Any],
) -> str:
    counts = summary["counts"]
    cost = summary["cost_estimate"]
    reconciliation = summary.get("task_frame_evidence_reconciliation", {})
    return f"""# AX ZAIJE Layer2 KG Methodology v2 Replay Run Report

Generated: {base.now_iso()}
Run ID: `{RUN_ID}`

## 실행 방식

| 항목 | 내용 |
| --- | --- |
| 입력 데이터 | `자이제_1.xlsx` |
| 방법론 문서 | `AX_ZAIJE_Layer2_KG_Methodology.md` |
| OpenAI 원시 응답 | `{raw_dir}` |
| v2 산출물 | `{output_dir}` |
| LLM 재호출 | 없음 |
| 재실행 방식 | 기존 OpenAI raw response를 재사용한 replay build |

## 핵심 보강

| 보강 항목 | 산출물 |
| --- | --- |
| Node type 설계 근거 | `25_node_type_traceability.csv/jsonl` |
| Canonical process/task/entity 도출 근거 | `26_canonical_inventory_traceability.csv/jsonl` |
| Predicate 도출 근거와 domain/range | `27_predicate_schema_traceability.csv/jsonl` |
| 논문용 방법론 설명 | `28_methodology_schema_derivation.md` |

## Task Frame Evidence ID Reconciliation

| 항목 | 값 |
| --- | ---: |
| task frame links | {reconciliation.get('task_frame_links', 0)} |
| original valid evidence links | {reconciliation.get('links_with_valid_original_evidence', 0)} |
| reconciled to section chunk evidence | {reconciliation.get('links_reconciled_to_section_chunk', 0)} |
| unresolved links | {reconciliation.get('links_unresolved', 0)} |

원시 OpenAI 응답은 `19_openai_task_frame_links.raw.jsonl`에 그대로 보존했고, evidence id reconciliation 결과는 `19b_openai_task_frame_links.reconciled.jsonl`에 별도로 저장했다.

## 재빌드 결과

| 항목 | 값 |
| --- | ---: |
| valid sentence rows | {counts['valid_sentence_rows']} |
| source chunks | {counts['source_chunks']} |
| evidence spans | {counts['evidence_spans']} |
| task frame LLM rows | {counts['task_frame_llm_rows']} |
| triple LLM rows | {counts['triple_llm_rows']} |
| LLM accepted triples | {counts['llm_triples_accepted']} |
| LLM rejected triples | {counts['llm_triples_rejected']} |
| raw triples | {counts['raw_triples']} |
| validated triples | {counts['validated_triples']} |
| graph nodes | {counts['nodes']} |
| graph edges | {counts['edges']} |
| CQ passed | {counts['cq_passed']}/{counts['cq_total']} |

## Schema Traceability Counts

| 항목 | 값 |
| --- | ---: |
| node type traceability rows | {traceability_counts['node_type_rows']} |
| canonical inventory traceability rows | {traceability_counts['canonical_inventory_rows']} |
| predicate traceability rows | {traceability_counts['predicate_rows']} |

## Token/Cost Reference

| 항목 | 값 |
| --- | ---: |
| prompt tokens | {cost['prompt_tokens']} |
| completion tokens | {cost['completion_tokens']} |
| total tokens | {cost['total_tokens']} |
| estimated USD | {cost.get('estimated_standard_cost_usd')} |

이번 v2 run은 API 비용을 새로 발생시키지 않고, 저장된 OpenAI 응답을 재사용하여 schema derivation traceability를 포함한 최종 KG 산출물을 다시 생성했다.
"""


def build_experiment(args: argparse.Namespace) -> dict[str, Any]:
    configure_run_id()
    input_xlsx = Path(args.input_xlsx)
    methodology = Path(args.methodology)
    raw_dir = Path(args.raw_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    sheet_name, raw_rows = base.read_xlsx_table(input_xlsx)
    normalized_rows = base.normalize_rows(raw_rows, input_xlsx)
    source_chunks, evidence_spans, evidence_by_id = base.make_source_chunks(normalized_rows)
    source_profile_md, source_profile = base.build_source_profile_md(sheet_name, len(raw_rows), normalized_rows, source_chunks, evidence_spans, input_xlsx, methodology)
    seed_raw_task_frames, seed_task_frames = base.build_task_frames(evidence_spans)
    task_raw_rows, triple_raw_rows = load_raw_rows(raw_dir)
    task_reconciled_rows, task_reconciliation_stats = reconcile_task_frame_evidence_ids(task_raw_rows, evidence_spans)

    task_frames = openai_run.apply_task_frame_links(seed_task_frames, task_reconciled_rows, evidence_by_id)
    alias_dictionary = base.build_alias_dictionary(task_frames)
    llm_triples, rejected_llm_triples = openai_run.convert_llm_triples(triple_raw_rows, task_frames, evidence_by_id)
    raw_triples = openai_run.scaffold_triples(task_frames, evidence_by_id) + llm_triples

    nodes, edges = base.build_nodes_and_edges(normalized_rows, source_chunks, evidence_spans, task_frames, raw_triples, evidence_by_id, input_xlsx)
    validated_triples = base.validate_triples(raw_triples, nodes, evidence_by_id)
    cq_results = base.evaluate_cqs(edges)
    quality = base.compute_quality(nodes, edges, validated_triples, cq_results)
    review_rows = base.build_review_queue(nodes, edges, validated_triples, evidence_by_id)
    cost = openai_run.estimate_cost(args.model, usage_from_raw(task_raw_rows, triple_raw_rows))

    base.write_text(output_dir / "00_source_profile.md", source_profile_md)
    base.write_text(output_dir / "01_layer2_core_schema.yaml", base.render_core_schema_yaml())
    base.write_text(output_dir / "02_layer2_domain_extension_zaije.yaml", base.render_domain_extension_yaml())
    base.write_jsonl(output_dir / "03_source_chunks.jsonl", source_chunks)
    base.write_jsonl(output_dir / "04_evidence_spans.jsonl", evidence_spans)
    base.write_jsonl(output_dir / "05_task_frames.raw.jsonl", seed_raw_task_frames)
    base.write_jsonl(output_dir / "06_task_frames.canonical.jsonl", task_frames)
    base.write_json(output_dir / "07_terms_alias_dictionary.json", alias_dictionary)
    base.write_jsonl(output_dir / "08_triples.raw.jsonl", raw_triples)
    base.write_jsonl(output_dir / "09_triples.validated.jsonl", validated_triples)
    base.write_jsonl(output_dir / "10_nodes.jsonl", nodes)
    base.write_jsonl(output_dir / "11_edges.jsonl", edges)

    quality_report = base.render_quality_report(source_profile, nodes, edges, raw_triples, validated_triples, cq_results, quality, output_dir)
    quality_report = quality_report.replace(
        "- LLM 상태: 현재 Python 환경에 `torch/transformers/vllm`이 없어 deterministic MVP extractor로 실행했다.",
        f"- LLM 상태: 기존 OpenAI Chat Completions API `{args.model}` 원시 응답을 재사용해 replay build를 수행했다.",
    )
    quality_report = quality_report.replace(
        "- LLM 교체 지점: `18_extraction_prompts.md`와 `05_task_frames.raw.jsonl`, `08_triples.raw.jsonl` 형식.",
        "- LLM 원본 응답: `19_openai_task_frame_links.raw.jsonl`, `20_openai_triples.raw.jsonl`.",
    )
    base.write_text(output_dir / "12_quality_report.md", quality_report)

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
    base.write_csv(output_dir / "13_review_queue.csv", review_rows, review_fields)
    base.write_minimal_xlsx(output_dir / "13_review_queue.xlsx", {"review_queue": (review_fields, review_rows)})
    base.write_neo4j_export(output_dir, nodes, edges)
    base.write_rdf_export(output_dir, nodes, edges)
    base.write_json(output_dir / "16_competency_questions.json", cq_results)
    base.write_text(output_dir / "17_graph_query_demo.md", base.render_query_demo(nodes, edges, cq_results))

    prompt_args = SimpleNamespace(model=args.model)
    base.write_text(output_dir / "18_extraction_prompts.md", openai_run.render_openai_prompts_md(prompt_args))
    base.write_jsonl(output_dir / "19_openai_task_frame_links.raw.jsonl", task_raw_rows)
    base.write_jsonl(output_dir / "19b_openai_task_frame_links.reconciled.jsonl", task_reconciled_rows)
    base.write_jsonl(output_dir / "20_openai_triples.raw.jsonl", triple_raw_rows)
    base.write_jsonl(output_dir / "21_openai_triples.accepted.jsonl", llm_triples)
    base.write_jsonl(output_dir / "22_openai_triples.rejected.jsonl", rejected_llm_triples)
    base.write_json(output_dir / "23_openai_usage_and_cost.json", cost)

    report_args = SimpleNamespace(model=args.model, dry_run=False)
    extraction_meta = {
        "task_frame_requests": len(task_raw_rows),
        "triple_requests": len(triple_raw_rows),
        "usage": usage_from_raw(task_raw_rows, triple_raw_rows),
        "errors": [],
        "task_raw_path": str(raw_dir / "19_openai_task_frame_links.raw.jsonl"),
        "triple_raw_path": str(raw_dir / "20_openai_triples.raw.jsonl"),
    }
    openai_report = openai_run.render_openai_report(
        output_dir,
        report_args,
        extraction_meta,
        llm_triples,
        rejected_llm_triples,
        validated_triples,
        nodes,
        edges,
        cq_results,
        cost,
    )
    openai_report = openai_report.replace(
        "- 이번 실행은 실제 OpenAI API LLM 추론을 사용했다.",
        "- 이번 v2 replay build는 저장된 실제 OpenAI API LLM 원시 응답을 재사용했다.",
    )
    base.write_text(output_dir / "24_openai_llm_run_report.md", openai_report)
    traceability_counts = write_traceability_outputs(output_dir, evidence_spans, task_frames)

    summary = {
        "generated_at_utc": base.now_iso(),
        "run_id": RUN_ID,
        "input_xlsx": str(input_xlsx),
        "methodology": str(methodology),
        "raw_openai_source_dir": str(raw_dir),
        "output_dir": str(output_dir),
        "llm_runtime_status": "replay_from_saved_openai_raw_responses",
        "model": args.model,
        "claim_status": "schema_derivation_traceable_layer2_llm_bootstrap_not_human_gold",
        "cost_estimate": cost,
        "task_frame_evidence_reconciliation": task_reconciliation_stats,
        "counts": {
            "valid_sentence_rows": len(normalized_rows),
            "source_chunks": len(source_chunks),
            "evidence_spans": len(evidence_spans),
            "task_frame_llm_rows": len(task_raw_rows),
            "triple_llm_rows": len(triple_raw_rows),
            "llm_triples_accepted": len(llm_triples),
            "llm_triples_rejected": len(rejected_llm_triples),
            "raw_triples": len(raw_triples),
            "validated_triples": len(validated_triples),
            "nodes": len(nodes),
            "edges": len(edges),
            "review_queue_rows": len(review_rows),
            "cq_passed": sum(1 for row in cq_results if row["passed"]),
            "cq_total": len(cq_results),
        },
        "quality": quality,
        "schema_traceability_counts": traceability_counts,
        "outputs": [
            "00_source_profile.md",
            "01_layer2_core_schema.yaml",
            "02_layer2_domain_extension_zaije.yaml",
            "03_source_chunks.jsonl",
            "04_evidence_spans.jsonl",
            "06_task_frames.canonical.jsonl",
            "08_triples.raw.jsonl",
            "09_triples.validated.jsonl",
            "10_nodes.jsonl",
            "11_edges.jsonl",
            "12_quality_report.md",
            "14_neo4j_import/nodes.csv",
            "14_neo4j_import/edges.csv",
            "14_neo4j_import/import.cypher",
            "18_extraction_prompts.md",
            "19_openai_task_frame_links.raw.jsonl",
            "19b_openai_task_frame_links.reconciled.jsonl",
            "20_openai_triples.raw.jsonl",
            "21_openai_triples.accepted.jsonl",
            "22_openai_triples.rejected.jsonl",
            "23_openai_usage_and_cost.json",
            "24_openai_llm_run_report.md",
            "25_node_type_traceability.csv",
            "25_node_type_traceability.jsonl",
            "26_canonical_inventory_traceability.csv",
            "26_canonical_inventory_traceability.jsonl",
            "27_predicate_schema_traceability.csv",
            "27_predicate_schema_traceability.jsonl",
            "28_methodology_schema_derivation.json",
            "28_methodology_schema_derivation.md",
            "29_methodology_v2_replay_run_report.md",
        ],
    }
    base.write_json(output_dir / "run_summary.json", summary)
    base.write_text(output_dir / "29_methodology_v2_replay_run_report.md", render_methodology_v2_run_report(output_dir, raw_dir, summary, traceability_counts))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay AX ZAIJE OpenAI KG build with methodology-v2 traceability")
    parser.add_argument("--input-xlsx", default=str(base.DEFAULT_XLSX))
    parser.add_argument("--methodology", default=str(base.DEFAULT_METHODOLOGY))
    parser.add_argument("--raw-dir", default=str(DEFAULT_RAW_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--model", default=openai_run.DEFAULT_MODEL)
    args = parser.parse_args()
    summary = build_experiment(args)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
