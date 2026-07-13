#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run bounded OpenAI adjudication over the TRACE-OL selective queue.

The API key is read only from OPENAI_API_KEY. It is never written to an
artifact, included in an exception, or passed as a command-line argument.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any


BASE_SCRIPT = Path(__file__).with_name("run_trace_ol_jaije_experiment.py")
DEFAULT_OUTPUT = Path("experiments/trace_ol_jaije_neo4j_20260710/openai_selective")
RESPONSES_URL = "https://api.openai.com/v1/responses"
INPUT_USD_PER_MILLION = 0.15
CACHED_INPUT_USD_PER_MILLION = 0.075
OUTPUT_USD_PER_MILLION = 0.60

SYSTEM_PROMPT = """역할: 당신은 온톨로지 작성자가 아니라 주어진 후보 주장의 근거 판정자다.

절대 규칙:
1. Evidence packet에 없는 사실, 개념, 역할, 단계, 관계를 추가하지 않는다.
2. 제공된 span ID와 entity ID만 사용한다.
3. 질문, 예시, 반례, 저자가 비판한 표현을 일반 사실로 승인하지 않는다.
4. 의무·금지·권고·가능성과 부정 범위를 구분한다.
5. 근거가 충분하지 않으면 abstain한다. 추측으로 빈칸을 채우지 않는다.
6. 허용 predicate 중 맞는 것이 없으면 UNMAPPED 또는 reject를 선택한다.
7. 설명문 없이 정의된 JSON 스키마만 반환한다.

판정 기준:
- accept: 후보가 제공된 근거에 직접 지지된다.
- revise: 근거 범위 안에서 필드 교정이 필요하다.
- reject: 후보가 근거와 어긋나거나 주장으로 볼 수 없다.
- abstain: 문맥 또는 근거가 부족해 결정할 수 없다.
"""

ERROR_CODES = [
    "none",
    "not_asserted",
    "question",
    "example_only",
    "subject_wrong",
    "predicate_wrong",
    "object_wrong",
    "modality_wrong",
    "polarity_wrong",
    "scope_missing",
    "insufficient_evidence",
    "type_violation",
]

RELATION_DOMAIN_RANGE = {
    "HAS_STAGE": ({"Process"}, {"Stage"}),
    "HAS_TASK": ({"Process", "Stage"}, {"Task"}),
    "PRECEDES": ({"Stage", "Task"}, {"Stage", "Task", "Decision"}),
    "REQUIRES_INPUT": ({"Task", "Activity"}, {"Artifact", "InformationObject"}),
    "PRODUCES": ({"Task", "Activity"}, {"Artifact", "InformationObject"}),
    "USES": ({"Task", "Activity"}, {"Artifact", "InformationObject"}),
    "PERFORMED_BY": ({"Task", "Activity"}, {"Role"}),
    "GOVERNED_BY": ({"Task", "Activity"}, {"Rule", "Criterion", "Principle"}),
    "HAS_PRECONDITION": ({"Task", "Stage", "Decision"}, {"Condition"}),
    "HAS_CRITERION": ({"Artifact", "Decision", "Task"}, {"Criterion"}),
    "HAS_OUTCOME": ({"Stage", "Task", "Decision"}, {"Decision", "DecisionOutcome"}),
    "SUPPORTS_GOAL": ({"Artifact", "InformationObject", "Task"}, {"Goal"}),
    "SUPPORTS_DECISION": ({"Artifact", "InformationObject", "Task"}, {"Decision"}),
    "MEASURED_BY": ({"Competitor", "Task", "Artifact"}, {"Criterion", "Metric"}),
    "MITIGATES": ({"Mitigation", "Task"}, {"Risk"}),
}


def load_base() -> Any:
    spec = importlib.util.spec_from_file_location("traceol_base", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def response_schema(predicates: list[str]) -> dict[str, Any]:
    nullable_string = {"anyOf": [{"type": "string"}, {"type": "null"}]}
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "candidate_id": {"type": "string"},
            "decision": {"type": "string", "enum": ["accept", "reject", "revise", "abstain"]},
            "predicate": {"type": "string", "enum": predicates},
            "subject_id": {"type": "string"},
            "object_id": nullable_string,
            "object_literal": nullable_string,
            "polarity": {"type": "string", "enum": ["positive", "negative"]},
            "modality": {
                "type": "string",
                "enum": ["asserted", "required", "prohibited", "recommended", "permitted", "possible", "hypothetical"],
            },
            "evidence_span_ids": {"type": "array", "items": {"type": "string"}, "minItems": 1},
            "condition_span_ids": {"type": "array", "items": {"type": "string"}},
            "error_codes": {"type": "array", "items": {"type": "string", "enum": ERROR_CODES}},
            "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
            "reusable_pattern": nullable_string,
        },
        "required": [
            "candidate_id",
            "decision",
            "predicate",
            "subject_id",
            "object_id",
            "object_literal",
            "polarity",
            "modality",
            "evidence_span_ids",
            "condition_span_ids",
            "error_codes",
            "confidence",
            "reusable_pattern",
        ],
    }


def extract_output_text(response: dict[str, Any]) -> str:
    for item in response.get("output") or []:
        for content in item.get("content") or []:
            if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                return content["text"]
    raise ValueError("response_has_no_output_text")


def normalized_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def validate_result(result: dict[str, Any], packet: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = {
        "candidate_id",
        "decision",
        "predicate",
        "subject_id",
        "object_id",
        "object_literal",
        "polarity",
        "modality",
        "evidence_span_ids",
        "condition_span_ids",
        "error_codes",
        "confidence",
        "reusable_pattern",
    }
    if set(result) != required:
        errors.append("schema_keys_mismatch")
    candidate = packet["candidate"]
    if result.get("candidate_id") != candidate["id"]:
        errors.append("candidate_id_mismatch")
    if result.get("subject_id") != candidate["subject_id"]:
        errors.append("subject_id_outside_packet")
    if result.get("predicate") not in packet["allowed_predicates"]:
        errors.append("predicate_outside_packet")
    object_id = result.get("object_id")
    allowed_object_ids = [value for value in [candidate.get("object_id")] if value]
    if object_id is not None and object_id not in allowed_object_ids:
        errors.append("object_id_outside_packet")
    evidence_ids = result.get("evidence_span_ids") or []
    allowed_spans = {row["span_id"] for row in packet["evidence"]}
    if not evidence_ids or not set(evidence_ids).issubset(allowed_spans):
        errors.append("evidence_span_outside_packet")
    condition_ids = result.get("condition_span_ids") or []
    if not set(condition_ids).issubset(allowed_spans):
        errors.append("condition_span_outside_packet")
    literal = result.get("object_literal")
    if literal and result.get("decision") in {"accept", "revise"}:
        evidence_text = " ".join(row["quote"] for row in packet["evidence"])
        candidate_literal = packet["candidate"].get("object_literal")
        permitted_candidate_normalization = (
            candidate_literal is not None
            and normalized_space(literal) == normalized_space(candidate_literal)
        )
        if (
            normalized_space(literal) not in normalized_space(evidence_text)
            and not permitted_candidate_normalization
        ):
            errors.append("object_literal_not_grounded")
    if result.get("decision") not in {"accept", "reject", "revise", "abstain"}:
        errors.append("invalid_decision")
    if result.get("decision") in {"accept", "revise"}:
        predicate = result.get("predicate")
        subject_types = set(packet["entity_types"].get(result.get("subject_id"), []))
        object_types = set(packet["entity_types"].get(result.get("object_id"), []))
        if predicate == "UNMAPPED":
            errors.append("accepted_unmapped_predicate")
        elif predicate == "DEFINES":
            if result.get("object_literal") is None:
                errors.append("definition_requires_literal")
            if not subject_types & {"Concept", "Risk", "Rule", "LexicalEntry", "Criterion"}:
                errors.append("definition_subject_type_violation")
        elif predicate in {"DISTINCT_FROM", "ALIAS_OF", "PART_OF"}:
            if result.get("object_id") is None:
                errors.append("binary_relation_requires_object_id")
        elif predicate in RELATION_DOMAIN_RANGE:
            allowed_subject, allowed_object = RELATION_DOMAIN_RANGE[predicate]
            if not subject_types & allowed_subject:
                errors.append("predicate_domain_violation")
            if result.get("object_id") is None or not object_types & allowed_object:
                errors.append("predicate_range_violation")
            if result.get("object_literal") is not None:
                errors.append("relational_claim_must_not_use_literal")
    confidence = result.get("confidence")
    if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        errors.append("invalid_confidence")
    return errors


def make_packet(
    candidate: dict[str, Any],
    blocks_by_id: dict[str, dict[str, Any]],
    spans_by_id: dict[str, dict[str, Any]],
    block_order: list[str],
    predicates: list[str],
    entity_types: dict[str, list[str]],
) -> dict[str, Any]:
    evidence = [
        {
            "span_id": span_id,
            "source_id": spans_by_id[span_id]["source_id"],
            "quote": spans_by_id[span_id]["quote"],
        }
        for span_id in candidate["evidence_span_ids"]
    ]
    source = blocks_by_id[candidate["source_ids"][0]]
    index = block_order.index(source["id"])
    previous = blocks_by_id[block_order[index - 1]]["text_raw"][:240] if index > 0 else ""
    following = blocks_by_id[block_order[index + 1]]["text_raw"][:240] if index + 1 < len(block_order) else ""
    return {
        "task": "claim_adjudication",
        "candidate": {
            "id": candidate["id"],
            "claim_type": candidate["claim_type"],
            "subject_id": candidate["subject_id"],
            "predicate": candidate["predicate"],
            "object_id": candidate.get("object_id"),
            "object_literal": candidate.get("object_literal"),
            "object_literal_normalization_policy": "candidate_literal_is_permitted_normalization",
            "polarity": candidate["polarity"],
            "modality": candidate["modality"],
        },
        "evidence": evidence,
        "context": {
            "chapter": source["chapter_title_raw"] or source["inferred_chapter_title"],
            "section": source["section_title_raw"] or source["inferred_section_title"],
            "context_status": source["context_status"],
            "previous_block_excerpt": previous,
            "next_block_excerpt": following,
        },
        "rule_votes": candidate["labeling_function_votes"],
        "allowed_predicates": predicates,
        "allowed_entity_ids": [value for value in [candidate["subject_id"], candidate.get("object_id")] if value],
        "entity_types": {
            identifier: entity_types.get(identifier, [])
            for identifier in [candidate["subject_id"], candidate.get("object_id")]
            if identifier
        },
    }


def api_request(
    api_key: str,
    model: str,
    packet: dict[str, Any],
    predicates: list[str],
    timeout: int,
    max_output_tokens: int,
) -> tuple[dict[str, Any], int]:
    payload = {
        "model": model,
        "input": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(packet, ensure_ascii=False, sort_keys=True)},
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "traceol_claim_adjudication",
                "strict": True,
                "schema": response_schema(predicates),
            }
        },
        "temperature": 0,
        "max_output_tokens": max_output_tokens,
    }
    request = urllib.request.Request(
        RESPONSES_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8")), response.status


def sanitized_http_error(error: urllib.error.HTTPError) -> str:
    try:
        body = json.loads(error.read().decode("utf-8"))
        message = str((body.get("error") or {}).get("message") or "http_error")
    except Exception:
        message = "http_error"
    return f"HTTP {error.code}: {message[:800]}"


def execute_call(
    *,
    api_key: str,
    model: str,
    candidate: dict[str, Any],
    packet: dict[str, Any],
    repeat: int,
    sequence: int,
    run_id: str,
    predicates: list[str],
    timeout: int,
    max_output_tokens: int,
    max_retries: int,
    base: Any,
) -> dict[str, Any]:
    started = time.monotonic()
    response: dict[str, Any] | None = None
    error_text: str | None = None
    attempts = 0
    for attempt in range(max_retries + 1):
        attempts += 1
        try:
            response, _ = api_request(api_key, model, packet, predicates, timeout, max_output_tokens)
            error_text = None
            break
        except urllib.error.HTTPError as error:
            error_text = sanitized_http_error(error)
            if error.code not in {408, 409, 429, 500, 502, 503, 504} or attempt >= max_retries:
                break
        except (urllib.error.URLError, TimeoutError) as error:
            error_text = f"{type(error).__name__}: {str(error)[:500]}"
            if attempt >= max_retries:
                break
        time.sleep(min(8, 2**attempt))

    latency_ms = int((time.monotonic() - started) * 1000)
    call_id = f"call:{run_id}:r{repeat}:{sequence:06d}"
    ledger: dict[str, Any] = {
        "id": call_id,
        "candidate_id": candidate["id"],
        "repeat": repeat,
        "model": model,
        "endpoint": "responses.create",
        "prompt_template_id": "prompt:claim-adjudicator:1.0",
        "prompt_hash": base.stable_hash(SYSTEM_PROMPT, 64),
        "input_hash": base.stable_hash(packet, 64),
        "response_id": None,
        "response_status": None,
        "decision": None,
        "parse_status": "not_attempted",
        "validation_errors": [],
        "retry_count": attempts - 1,
        "http_attempts": attempts,
        "input_tokens": 0,
        "cached_input_tokens": 0,
        "output_tokens": 0,
        "latency_ms": latency_ms,
        "estimated_cost_usd": 0.0,
        "error": error_text,
        "created_at_utc": base.created_at_for_run(run_id),
        "parsed_result": None,
    }
    if response is None:
        ledger["response_status"] = "error"
        return ledger

    ledger["response_id"] = response.get("id")
    ledger["response_status"] = response.get("status")
    usage = response.get("usage") or {}
    input_details = usage.get("input_tokens_details") or {}
    ledger["input_tokens"] = int(usage.get("input_tokens") or 0)
    ledger["cached_input_tokens"] = int(input_details.get("cached_tokens") or 0)
    ledger["output_tokens"] = int(usage.get("output_tokens") or 0)
    uncached = max(0, ledger["input_tokens"] - ledger["cached_input_tokens"])
    ledger["estimated_cost_usd"] = round(
        (
            uncached * INPUT_USD_PER_MILLION
            + ledger["cached_input_tokens"] * CACHED_INPUT_USD_PER_MILLION
            + ledger["output_tokens"] * OUTPUT_USD_PER_MILLION
        )
        / 1_000_000,
        8,
    )
    try:
        parsed = json.loads(extract_output_text(response))
        validation_errors = validate_result(parsed, packet)
        ledger["parsed_result"] = parsed
        ledger["decision"] = parsed.get("decision")
        ledger["validation_errors"] = validation_errors
        ledger["parse_status"] = "valid" if not validation_errors else "invalid_local_contract"
    except Exception as error:
        ledger["parse_status"] = "parse_error"
        ledger["error"] = f"{type(error).__name__}: {str(error)[:500]}"
    return ledger


def semantic_signature(result: dict[str, Any]) -> tuple[Any, ...]:
    return (
        result.get("predicate"),
        result.get("subject_id"),
        result.get("object_id"),
        result.get("object_literal"),
        result.get("polarity"),
        result.get("modality"),
        tuple(sorted(result.get("evidence_span_ids") or [])),
        tuple(sorted(result.get("condition_span_ids") or [])),
    )


def apply_consensus(
    adjudicated: list[dict[str, Any]], ledgers: list[dict[str, Any]], repeats: int, base: Any
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_candidate: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for ledger in ledgers:
        by_candidate[ledger["candidate_id"]].append(ledger)
    consensus_rows: list[dict[str, Any]] = []
    output: list[dict[str, Any]] = []
    for candidate in adjudicated:
        calls = sorted(by_candidate.get(candidate["id"], []), key=lambda row: row["repeat"])
        if not calls:
            output.append(candidate)
            continue
        valid = [row for row in calls if row["parse_status"] == "valid" and row.get("parsed_result")]
        decisions = [row["parsed_result"]["decision"] for row in valid]
        accept_like = [row for row in valid if row["parsed_result"]["decision"] in {"accept", "revise"}]
        reject_count = sum(decision == "reject" for decision in decisions)
        updated = dict(candidate)
        status = "NeedsReview"
        reason = "llm_repeat_incomplete_or_disagreed"
        promoted_result: dict[str, Any] | None = None
        if len(valid) == repeats and len(accept_like) == repeats:
            signatures = {semantic_signature(row["parsed_result"]) for row in accept_like}
            if len(signatures) == 1:
                promoted_result = accept_like[0]["parsed_result"]
                status = "Accepted"
                reason = "openai_unanimous_accept_or_revise"
            else:
                reason = "openai_unanimous_accept_but_semantic_revision_disagreed"
        elif reject_count > repeats / 2:
            status = "Rejected"
            reason = "openai_majority_reject"
        elif len(valid) == repeats and all(decision == "abstain" for decision in decisions):
            reason = "openai_unanimous_abstain"

        original_id = updated["id"]
        if promoted_result:
            updated["predicate"] = promoted_result["predicate"]
            updated["subject_id"] = promoted_result["subject_id"]
            updated["object_id"] = promoted_result["object_id"]
            updated["object_literal"] = promoted_result["object_literal"]
            updated["polarity"] = promoted_result["polarity"]
            updated["modality"] = promoted_result["modality"]
            updated["evidence_span_ids"] = promoted_result["evidence_span_ids"]
            updated["condition_span_ids"] = promoted_result["condition_span_ids"]
            updated["confidence"] = promoted_result["confidence"]
            updated["candidate_id"] = original_id
            updated["id"] = base.canonical_claim_id(
                updated["subject_id"],
                updated["predicate"],
                updated["object_id"],
                updated["object_literal"],
                updated["polarity"],
                updated["modality"],
                updated["scope"],
            )
        updated["status"] = status
        updated["decision_source"] = reason
        updated["llm_call_ids"] = [row["id"] for row in calls]
        output.append(updated)
        consensus_rows.append(
            {
                "candidate_id": original_id,
                "final_claim_id": updated["id"],
                "valid_repeats": len(valid),
                "expected_repeats": repeats,
                "decisions": decisions,
                "decision_counts": dict(Counter(decisions)),
                "status": status,
                "reason": reason,
            }
        )
    deduplicated: dict[str, dict[str, Any]] = {}
    for row in output:
        if row["id"] not in deduplicated or row["status"] == "Accepted":
            deduplicated[row["id"]] = row
    return sorted(deduplicated.values(), key=lambda row: row["id"]), consensus_rows


def proposed_distilled_rules(
    claims: list[dict[str, Any]], consensus: list[dict[str, Any]], split: dict[str, Any]
) -> list[dict[str, Any]]:
    accepted_ids = {row["final_claim_id"] for row in consensus if row["status"] == "Accepted"}
    section_by_source = {
        source_id: section["section_id"]
        for section in split["sections"]
        for source_id in section["source_ids"]
    }
    groups: dict[tuple[str, tuple[str, ...]], list[dict[str, Any]]] = defaultdict(list)
    for claim in claims:
        if claim["id"] not in accepted_ids:
            continue
        key = (claim["predicate"], tuple(sorted(claim.get("matched_cues") or [])))
        groups[key].append(claim)
    rules = []
    for sequence, ((predicate, cues), rows) in enumerate(sorted(groups.items()), start=1):
        sections = sorted(
            {
                section_by_source[source_id]
                for row in rows
                for source_id in row["source_ids"]
                if source_id in section_by_source
            }
        )
        rules.append(
            {
                "id": f"lf:distilled:openai:{sequence:03d}",
                "predicate": predicate,
                "matched_cues": list(cues),
                "support": len(rows),
                "distinct_section_support": len(sections),
                "source_claim_ids": [row["id"] for row in rows],
                "status": "NeedsRuleValidation",
                "adopted": False,
                "reason": "separate rule-validation precision and counterexamples unavailable",
            }
        )
    return rules


def render_report(summary: dict[str, Any], consensus: list[dict[str, Any]]) -> str:
    counts = summary["counts"]
    agreement = Counter(row["reason"] for row in consensus)
    lines = [
        "# TRACE-OL OpenAI 선택 판정 결과",
        "",
        f"- Run ID: `{summary['run_id']}`",
        f"- Model: `{summary['model']}`",
        f"- 상태: **{summary['status']}**",
        f"- API key 저장: **아니오**",
        f"- 반복 판정 완전 일치율: **{summary['repeat_unanimity_rate']:.2%}**",
        f"- 실패 CQ: **{', '.join(summary['failed_cq_ids']) or '없음'}**",
        "",
        "## 수량",
        "",
        "| 항목 | 값 |",
        "|---|---:|",
    ]
    for key, value in counts.items():
        lines.append(f"| {key} | {value} |")
    lines += ["", "## 반복 합의", "", "| 결과 | 후보 수 |", "|---|---:|"]
    for reason, count in sorted(agreement.items()):
        lines.append(f"| {reason} | {count} |")
    lines += [
        "",
        "## 승격 정책",
        "",
        "- 3회 모두 유효하고 accept/revise이며 의미 필드가 동일한 경우만 Accepted로 승격했다.",
        "- 과반 reject는 Rejected, 나머지는 NeedsReview로 보존했다.",
        "- 증류 규칙은 별도 validation split 정밀도를 측정할 수 없어 후보만 만들고 채택하지 않았다.",
        "- human gold가 없으므로 precision/recall/F1은 여전히 산출하지 않았다.",
    ]
    return "\n".join(lines) + "\n"


def run(args: argparse.Namespace) -> dict[str, Any]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key and not args.reuse_model_calls:
        raise SystemExit("OPENAI_API_KEY is required")
    base = load_base()
    input_path = Path(args.input_xlsx).resolve()
    design_path = Path(args.design).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    run_id = args.run_id

    input_hash = base.file_sha256(input_path)
    sheet_name, records = base.read_xlsx(input_path)
    blocks = base.build_source_blocks(records, input_path, input_hash, run_id, sheet_name)
    spans = base.build_evidence_spans(blocks, run_id)
    tables = base.parse_tables(blocks, run_id)
    formulas = base.parse_formulas(blocks, run_id)
    terms = base.mine_terms(blocks, run_id)
    blocks_by_row = {block["excel_row"]: block for block in blocks}
    blocks_by_id = {block["id"]: block for block in blocks}
    spans_by_id = {span["id"]: span for span in spans}
    span_by_row: dict[int, str] = {}
    for span in spans:
        span_by_row.setdefault(span["excel_row"], span["id"])
    exact = base.fixed_claims(blocks_by_row, span_by_row, tables, run_id)
    generic = base.generic_claim_candidates(blocks, span_by_row, run_id)
    candidates, adjudicated, offline_queue = base.adjudicate_candidates(exact, generic, run_id)
    if args.queue_source == "typed_audit":
        ranked_exact = sorted(
            exact,
            key=lambda row: (
                not row["critical"],
                -row["utility"],
                row["source_excel_rows"][0],
                row["id"],
            ),
        )
        queued_ids = [row["id"] for row in ranked_exact[: args.max_candidates]]
        selected_id_set = set(queued_ids)
        for row in adjudicated:
            if row["id"] in selected_id_set:
                row["status"] = "NeedsReview"
                row["decision_source"] = "utility_aware_typed_audit_gate"
    else:
        queued_ids = [row["candidate_id"] for row in offline_queue][: args.max_candidates]
    candidates_by_id = {row["id"]: row for row in adjudicated}
    selected = [candidates_by_id[candidate_id] for candidate_id in queued_ids]
    predicates = sorted({*base.WHITELIST_PREDICATES, "UNMAPPED"})
    block_order = [block["id"] for block in blocks]
    entity_types = {
        row["id"]: row["labels"]
        for row in base.domain_entities(run_id)
    }
    packets = {
        candidate["id"]: make_packet(
            candidate, blocks_by_id, spans_by_id, block_order, predicates, entity_types
        )
        for candidate in selected
    }

    jobs = []
    sequence = 1
    for repeat in range(1, args.repeats + 1):
        for candidate in selected:
            jobs.append((repeat, sequence, candidate))
            sequence += 1
    ledgers: list[dict[str, Any]] = []
    if args.reuse_model_calls:
        ledger_path = output_dir / "model_calls.jsonl"
        if not ledger_path.is_file():
            raise SystemExit(f"Cannot reuse missing ledger: {ledger_path}")
        ledgers = [json.loads(line) for line in ledger_path.open(encoding="utf-8") if line.strip()]
        expected_candidates = {candidate["id"] for candidate in selected}
        if len(ledgers) != len(jobs) or {row["candidate_id"] for row in ledgers} != expected_candidates:
            raise SystemExit("Existing model call ledger does not match the requested queue/repeats")
    else:
        assert api_key is not None
        with ThreadPoolExecutor(max_workers=args.max_concurrency) as executor:
            futures = [
                executor.submit(
                    execute_call,
                    api_key=api_key,
                    model=args.model,
                    candidate=candidate,
                    packet=packets[candidate["id"]],
                    repeat=repeat,
                    sequence=sequence,
                    run_id=run_id,
                    predicates=predicates,
                    timeout=args.timeout,
                    max_output_tokens=args.max_output_tokens,
                    max_retries=args.max_retries,
                    base=base,
                )
                for repeat, sequence, candidate in jobs
            ]
            for future in as_completed(futures):
                ledgers.append(future.result())
    ledgers.sort(key=lambda row: (row["repeat"], row["id"]))
    for ledger in ledgers:
        parsed_result = ledger.get("parsed_result")
        packet = packets.get(ledger["candidate_id"])
        if parsed_result is None or packet is None:
            continue
        validation_errors = validate_result(parsed_result, packet)
        ledger["validation_errors"] = validation_errors
        ledger["parse_status"] = "valid" if not validation_errors else "invalid_local_contract"

    final_claims, consensus = apply_consensus(adjudicated, ledgers, args.repeats, base)
    split = base.make_split(blocks)
    distilled_candidates = proposed_distilled_rules(final_claims, consensus, split)
    nodes, relationships, accepted_relations = base.build_graph(
        blocks, spans, tables, formulas, final_claims, run_id
    )
    node_registry = {node["id"]: node for node in nodes}
    final_by_candidate = {
        row.get("candidate_id", row["id"]): row["id"] for row in final_claims
    }
    for ledger in ledgers:
        base.add_node(
            node_registry,
            base.entity(
                ledger["id"],
                ["ModelCall"],
                ledger["id"],
                run_id=run_id,
                candidate_id=ledger["candidate_id"],
                model=ledger["model"],
                prompt_hash=ledger["prompt_hash"],
                input_hash=ledger["input_hash"],
                decision=ledger["decision"],
                parse_status=ledger["parse_status"],
            ),
        )
        final_claim_id = final_by_candidate.get(ledger["candidate_id"])
        if final_claim_id:
            base.add_relation(
                relationships,
                final_claim_id,
                "ADJUDICATED_BY",
                ledger["id"],
                run_id=run_id,
            )
    nodes = sorted(node_registry.values(), key=lambda row: row["id"])
    relationships = sorted(relationships, key=lambda row: row["id"])
    cqs = base.static_cqs(nodes, relationships, final_claims, formulas)
    regressions = base.regression_checks(blocks_by_row, tables, formulas, relationships, final_claims)
    validations = base.validation_results(
        blocks, spans, nodes, relationships, final_claims, cqs, regressions, input_hash
    )
    critical_failed = [row for row in validations if row["severity"] == "critical" and not row["passed"]]
    valid_calls = [row for row in ledgers if row["parse_status"] == "valid"]
    api_errors = [row for row in ledgers if row["response_status"] == "error"]
    parsed_calls = [row for row in ledgers if row.get("parsed_result") is not None]
    guardrail_rejections = [row for row in ledgers if row["parse_status"] == "invalid_local_contract"]
    total_cost = round(sum(row["estimated_cost_usd"] for row in ledgers), 8)
    if critical_failed or api_errors:
        run_status = "FAILED"
    elif guardrail_rejections:
        run_status = "PASS_WITH_GUARDRAIL_REJECTIONS"
    else:
        run_status = "PASS"
    summary = {
        "run_id": run_id,
        "model": args.model,
        "status": run_status,
        "output_dir": str(output_dir),
        "counts": {
            "queue_source": args.queue_source,
            "selected_candidates": len(selected),
            "repeats": args.repeats,
            "api_calls": len(ledgers),
            "completed_responses": sum(row["response_status"] == "completed" for row in ledgers),
            "schema_parsed_responses": len(parsed_calls),
            "valid_structured_responses": len(valid_calls),
            "local_contract_guardrail_rejections": len(guardrail_rejections),
            "api_errors": len(api_errors),
            "unanimous_promotions": sum(row["status"] == "Accepted" for row in consensus),
            "majority_rejections": sum(row["status"] == "Rejected" for row in consensus),
            "remaining_needs_review": sum(row["status"] == "NeedsReview" for row in consensus),
            "unanimous_candidate_decisions": sum(
                len(set(row["decisions"])) == 1 and len(row["decisions"]) == args.repeats
                for row in consensus
            ),
            "accepted_claims_total": sum(row["status"] == "Accepted" for row in final_claims),
            "distilled_rule_candidates": len(distilled_candidates),
            "adopted_distilled_rules": 0,
            "graph_nodes": len(nodes),
            "graph_relationships": len(relationships),
            "cq_passed": sum(row["passed"] for row in cqs),
            "cq_total": len(cqs),
            "regression_passed": sum(row["passed"] for row in regressions),
            "regression_total": len(regressions),
        },
        "usage": {
            "input_tokens": sum(row["input_tokens"] for row in ledgers),
            "cached_input_tokens": sum(row["cached_input_tokens"] for row in ledgers),
            "output_tokens": sum(row["output_tokens"] for row in ledgers),
            "estimated_cost_usd": total_cost,
            "pricing_snapshot": {
                "input_usd_per_million": INPUT_USD_PER_MILLION,
                "cached_input_usd_per_million": CACHED_INPUT_USD_PER_MILLION,
                "output_usd_per_million": OUTPUT_USD_PER_MILLION,
                "source": "https://developers.openai.com/api/docs/models/gpt-4o-mini",
            },
        },
        "critical_validation_failures": len(critical_failed),
        "failed_cq_ids": [row["id"] for row in cqs if not row["passed"]],
        "repeat_unanimity_rate": round(
            sum(
                len(set(row["decisions"])) == 1 and len(row["decisions"]) == args.repeats
                for row in consensus
            )
            / len(consensus),
            4,
        ) if consensus else 0.0,
        "full_design_status": "BLOCKED_CQ_GOLD_LIVE_NEO4J_AND_BASELINE_DRIFT",
        "api_key_persisted": False,
    }

    consensus_by_id = {row["candidate_id"]: row for row in consensus}
    review_queue = []
    for candidate in selected:
        result = consensus_by_id[candidate["id"]]
        if result["status"] == "Accepted":
            continue
        review_queue.append(
            {
                "candidate_id": candidate["id"],
                "status": result["status"],
                "reason": result["reason"],
                "decisions": result["decisions"],
                "decision_counts": result["decision_counts"],
                "subject_id": candidate["subject_id"],
                "predicate": candidate["predicate"],
                "object_id": candidate.get("object_id"),
                "object_literal": candidate.get("object_literal"),
                "source_ids": candidate["source_ids"],
                "source_excel_rows": candidate["source_excel_rows"],
                "evidence_span_ids": candidate["evidence_span_ids"],
                "human_decision": None,
                "reviewer": None,
                "reviewer_note": None,
            }
        )

    request_ledger = [
        {
            "candidate_id": candidate["id"],
            "evidence_span_ids": candidate["evidence_span_ids"],
            "input_hash": base.stable_hash(packets[candidate["id"]], 64),
            "prompt_hash": base.stable_hash(SYSTEM_PROMPT, 64),
        }
        for candidate in selected
    ]
    base.write_json(output_dir / "manifest.json", {
        "run_id": run_id,
        "created_at_utc": base.created_at_for_run(run_id),
        "input_file": str(input_path),
        "input_sha256": input_hash,
        "design_file": str(design_path),
        "design_sha256": base.file_sha256(design_path),
        "model": args.model,
        "endpoint": "responses.create",
        "prompt_hash": base.stable_hash(SYSTEM_PROMPT, 64),
        "repeats": args.repeats,
        "max_candidates": args.max_candidates,
        "queue_source": args.queue_source,
        "seed": base.SEED,
    })
    base.write_jsonl(output_dir / "source_blocks.jsonl", blocks)
    base.write_jsonl(output_dir / "evidence_spans.jsonl", spans)
    base.write_jsonl(output_dir / "tables.jsonl", tables)
    base.write_jsonl(output_dir / "formulas.jsonl", formulas)
    base.write_jsonl(output_dir / "term_candidates.jsonl", terms)
    base.write_jsonl(output_dir / "claims.candidate.jsonl", candidates)
    base.write_jsonl(output_dir / "claims.adjudicated.jsonl", final_claims)
    base.write_jsonl(output_dir / "llm_requests.jsonl", request_ledger)
    base.write_jsonl(output_dir / "model_calls.jsonl", ledgers)
    base.write_json(output_dir / "llm_consensus.json", consensus)
    base.write_jsonl(output_dir / "human_review_queue.jsonl", review_queue)
    base.write_jsonl(output_dir / "distilled_rules.candidate.jsonl", distilled_candidates)
    base.write_jsonl(output_dir / "distilled_rules.jsonl", [])
    base.write_jsonl(output_dir / "entities.jsonl", nodes)
    base.write_jsonl(output_dir / "relations.accepted.jsonl", accepted_relations)
    base.write_json(output_dir / "split_manifest.json", split)
    base.write_json(output_dir / "competency_questions.json", cqs)
    base.write_json(output_dir / "regression_results.json", regressions)
    base.write_json(output_dir / "validation.json", {"checks": validations, "critical_failed": len(critical_failed)})
    base.write_json(output_dir / "run_summary.json", summary)
    base.write_json(output_dir / "experiment_matrix_results.json", [
        {"id": "B0_RULE_ONLY", "status": "EXECUTED", "reason": "offline baseline completed"},
        {"id": "B2_FULL_ADJ", "status": "NOT_EXECUTED", "reason": "full 609-candidate adjudication was outside the bounded 30-call gate"},
        {"id": "P1_SELECTIVE", "status": "EXECUTED", "reason": f"{len(selected)} typed candidates x {args.repeats} repeats"},
        {"id": "P2_DISTILLED", "status": "BLOCKED", "reason": "distilled rule candidates require separate validation and human gold"},
    ])
    base.write_text(output_dir / "report.md", render_report(summary, consensus))
    base.export_neo4j(output_dir, nodes, relationships, run_id)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run TRACE-OL selective OpenAI adjudication")
    parser.add_argument("--input-xlsx", default=str(load_base().DEFAULT_INPUT))
    parser.add_argument("--design", default=str(load_base().DEFAULT_DESIGN))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--run-id", default="run:20260710T010000Z:P1_OPENAI:a9482ce")
    parser.add_argument("--model", default="gpt-4o-mini-2024-07-18")
    parser.add_argument("--max-candidates", type=int, default=30)
    parser.add_argument("--queue-source", choices=["typed_audit", "uncertain"], default="typed_audit")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--max-concurrency", type=int, default=4)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--max-output-tokens", type=int, default=700)
    parser.add_argument("--reuse-model-calls", action="store_true")
    args = parser.parse_args()
    summary = run(args)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
