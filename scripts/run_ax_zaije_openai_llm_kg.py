#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run the AX ZAIJE Layer2 KG experiment with OpenAI API LLM extraction.

The earlier MVP kept the LLM interfaces but filled them deterministically.
This script uses the same downstream schema/validation/export code, but calls
OpenAI Chat Completions for Task Frame evidence linking and triple extraction.

API keys are read only from OPENAI_API_KEY. Do not put keys in this file.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import build_ax_zaije_layer2_kg as base  # noqa: E402


DEFAULT_OUTPUT_DIR = Path("experiments/ax_zaije_layer2_kg_openai_20260707/layer2_kg")
DEFAULT_MODEL = "gpt-4o-mini"
RUN_ID = "RUN_2026_07_07_OPENAI_001"

DOMAIN_PREDICATES = [
    pred
    for pred in base.EDGE_SCHEMA
    if pred
    not in {
        "HAS_CHAPTER",
        "HAS_SECTION",
        "HAS_CHUNK",
        "ALIAS_OF",
        "EVIDENCED_BY",
    }
]

MODEL_PRICE_PER_1M = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
    "gpt-5-mini": {"input": 0.25, "output": 2.00},
}


def add_usage(total_usage: Counter[str], usage: dict[str, Any] | None) -> None:
    if not usage:
        return
    for key, value in usage.items():
        if isinstance(value, (int, float)):
            total_usage[key] += value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def compact_text(text: str, limit: int) -> str:
    text = str(text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 120].rstrip() + "\n...[TRUNCATED_FOR_PROMPT]..."


def node_label(node: dict[str, Any]) -> str:
    return (
        node.get("name_ko")
        or node.get("name_en")
        or node.get("statement")
        or node.get("title")
        or node.get("term")
        or node.get("id")
        or ""
    )


def process_inventory() -> list[dict[str, Any]]:
    return [
        {
            "id": process_id,
            "type": "DomainProcess",
            "label": process["name_ko"],
            "aliases": [],
        }
        for process_id, process in base.PROCESSES.items()
    ]


def task_inventory(task_frames: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": frame["id"],
            "type": "DomainTask",
            "label": frame["name_ko"],
            "aliases": frame.get("aliases") or [],
            "definition": frame.get("definition", ""),
        }
        for frame in task_frames
    ]


def entity_inventory_for_text(text: str, limit: int = 48) -> list[dict[str, Any]]:
    scored = []
    for entity_id, entity in base.ENTITIES.items():
        labels = [entity.get("name_ko", ""), entity.get("name_en", ""), entity.get("statement", "")]
        labels.extend(entity.get("aliases") or [])
        labels.extend(entity.get("keywords") or [])
        score = base.text_score(text, [label for label in labels if label])
        scored.append((score, entity_id, entity))
    scored.sort(key=lambda item: (-item[0], item[1]))
    selected = [row for row in scored if row[0] > 0][:limit]
    if len(selected) < min(20, len(scored)):
        selected.extend(scored[: min(20, len(scored)) - len(selected)])
    seen = set()
    rows = []
    for _score, entity_id, entity in selected:
        if entity_id in seen:
            continue
        seen.add(entity_id)
        rows.append(
            {
                "id": entity_id,
                "type": entity["type"],
                "label": entity.get("name_ko") or entity.get("statement"),
                "aliases": entity.get("aliases") or [],
            }
        )
    return rows


def allowed_predicates_payload() -> list[dict[str, Any]]:
    rows = []
    for pred in DOMAIN_PREDICATES:
        domain, range_ = base.EDGE_SCHEMA[pred]
        rows.append({"predicate": pred, "domain": domain or ["Any"], "range": range_ or ["Any"]})
    return rows


def evidence_by_chunk(evidence_spans: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by_chunk: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for ev in evidence_spans:
        by_chunk[ev["chunk_id"]].append(ev)
    return by_chunk


def evidence_payload_for_chunk(chunk: dict[str, Any], by_chunk: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = []
    for ev in by_chunk.get(chunk["chunk_id"], []):
        rows.append(
            {
                "evidence_id": ev["id"],
                "page": ev.get("page"),
                "section_no": ev.get("section_no"),
                "text": compact_text(ev.get("text_span", ""), 500),
            }
        )
    return rows


def normalize_base_url(base_url: str | None) -> str:
    url = (base_url or "https://api.openai.com/v1").rstrip("/")
    if not url.endswith("/v1"):
        url += "/v1"
    return url


class OpenAIChatClient:
    def __init__(self, model: str, timeout: int, temperature: float, max_tokens: int, base_url: str | None = None) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not set. Set it in the shell environment before running this script.")
        self.model = model
        self.timeout = timeout
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.endpoint = normalize_base_url(base_url or os.getenv("OPENAI_BASE_URL")) + "/chat/completions"

    def complete_json(self, system_prompt: str, user_prompt: str, retries: int = 4) -> tuple[dict[str, Any], dict[str, Any]]:
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "response_format": {"type": "json_object"},
        }
        last_error = ""
        for attempt in range(retries):
            try:
                return self._post(body)
            except RuntimeError as exc:
                last_error = str(exc)
                retry_body = dict(body)
                if "max_tokens" in last_error and "max_completion_tokens" in last_error:
                    retry_body.pop("max_tokens", None)
                    retry_body["max_completion_tokens"] = self.max_tokens
                if "temperature" in last_error and ("unsupported" in last_error.lower() or "not support" in last_error.lower()):
                    retry_body.pop("temperature", None)
                if retry_body != body:
                    body = retry_body
                    continue
                if attempt == retries - 1:
                    break
                time.sleep(min(2**attempt, 8))
        raise RuntimeError(last_error or "OpenAI request failed")

    def _post(self, body: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            self.endpoint,
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raw_error = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code}: {raw_error}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"URL error: {exc}") from exc
        payload = json.loads(raw)
        content = payload["choices"][0]["message"].get("content") or "{}"
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Model returned non-JSON content: {content[:500]}") from exc
        usage = payload.get("usage") or {}
        return parsed, usage


TASK_FRAME_SYSTEM_PROMPT = """당신은 업무 도메인 온톨로지 설계자입니다.
입력 문서에서 확인되는 내용을 기존 Layer 2 canonical Task catalog에 연결합니다.

규칙:
1. 원문 evidence_id가 있는 내용만 연결합니다.
2. 새 task를 남발하지 말고, 기존 task로 설명 가능한 경우 task_frame_links에 넣습니다.
3. 사례 속 인물, 회사, 프로젝트명은 일반 업무 지식으로 승격하지 않습니다.
4. evidence_ids는 반드시 입력으로 제공된 evidence_id 중에서만 고릅니다.
5. 출력은 JSON object만 반환합니다."""


TRIPLE_SYSTEM_PROMPT = """당신은 근거 기반 지식그래프 삼중항 추출기입니다.
입력 chunk에서 확인되는 업무 지식을 subject-predicate-object 형태로 추출합니다.

규칙:
1. predicate는 allowed_predicates 안에서만 선택합니다.
2. subject_id와 object_id는 candidate_nodes에 제공된 canonical id 중에서만 고릅니다.
3. 모든 triple은 evidence_ids를 가져야 하며, evidence_ids는 입력 evidence 목록의 id만 사용할 수 있습니다.
4. evidence가 chunk 안에 없으면 추출하지 않습니다.
5. 확신이 낮거나 schema에 맞지 않으면 triples가 아니라 review_notes 또는 new_node_candidates에 보냅니다.
6. 예시 인물, 회사, 프로젝트는 일반 업무 지식으로 승격하지 않습니다.
7. 출력은 JSON object만 반환합니다."""


def task_frame_user_prompt(chunk: dict[str, Any], task_frames: list[dict[str, Any]], evidence_rows: list[dict[str, Any]], max_chars: int) -> str:
    payload = {
        "document_metadata": {
            "book_id": base.BOOK_ID,
            "chapter_no": chunk.get("chapter_no"),
            "chapter_title": chunk.get("chapter_title"),
            "section_no": chunk.get("section_no"),
            "section_title": chunk.get("section_title"),
            "chunk_id": chunk.get("chunk_id"),
        },
        "section_text": compact_text(chunk.get("text", ""), max_chars),
        "canonical_task_catalog": task_inventory(task_frames),
        "evidence_candidates": evidence_rows,
        "output_schema": {
            "chunk_id": "string",
            "task_frame_links": [
                {
                    "task_id": "canonical task id",
                    "evidence_ids": ["EV_ZAIJE_000000"],
                    "observed_inputs": ["canonical node id or literal term"],
                    "observed_outputs": ["canonical node id or literal term"],
                    "observed_roles": ["canonical node id or literal term"],
                    "observed_decision_points": ["canonical node id or literal term"],
                    "confidence": 0.0,
                    "rationale": "short Korean reason",
                }
            ],
            "candidate_new_task_frames": [],
            "candidate_terms": [],
            "review_notes": [],
        },
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def triple_user_prompt(
    chunk: dict[str, Any],
    task_frames: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    max_chars: int,
) -> str:
    text = chunk.get("text", "")
    candidate_nodes = process_inventory() + task_inventory(task_frames) + entity_inventory_for_text(text)
    payload = {
        "chunk": {
            "chunk_id": chunk.get("chunk_id"),
            "chapter_no": chunk.get("chapter_no"),
            "chapter_title": chunk.get("chapter_title"),
            "section_no": chunk.get("section_no"),
            "section_title": chunk.get("section_title"),
            "page_start": chunk.get("page_start"),
            "page_end": chunk.get("page_end"),
            "text": compact_text(text, max_chars),
        },
        "candidate_nodes": candidate_nodes,
        "allowed_predicates": allowed_predicates_payload(),
        "evidence_candidates": evidence_rows,
        "relation_scope_options": ["definition", "process_step", "principle", "empirical_claim", "example_case", "author_opinion"],
        "output_schema": {
            "chunk_id": "string",
            "triples": [
                {
                    "subject_id": "canonical node id",
                    "predicate": "allowed predicate",
                    "object_id": "canonical node id",
                    "frame_task_id": "canonical task id or empty string",
                    "evidence_ids": ["EV_ZAIJE_000000"],
                    "evidence_span": "verbatim supporting span",
                    "confidence": 0.0,
                    "relation_scope": "process_step",
                    "rationale": "short Korean reason",
                }
            ],
            "new_node_candidates": [],
            "review_notes": [],
        },
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def run_openai_extractions(
    output_dir: Path,
    client: OpenAIChatClient | None,
    source_chunks: list[dict[str, Any]],
    evidence_spans: list[dict[str, Any]],
    task_frames: list[dict[str, Any]],
    args: argparse.Namespace,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    by_chunk = evidence_by_chunk(evidence_spans)
    task_raw_path = output_dir / "19_openai_task_frame_links.raw.jsonl"
    triple_raw_path = output_dir / "20_openai_triples.raw.jsonl"

    existing_task = {row.get("chunk_id") for row in read_jsonl(task_raw_path)} if args.resume else set()
    existing_triple = {row.get("chunk_id") for row in read_jsonl(triple_raw_path)} if args.resume else set()
    if not args.resume:
        task_raw_path.unlink(missing_ok=True)
        triple_raw_path.unlink(missing_ok=True)

    section_chunks = [chunk for chunk in source_chunks if chunk.get("chunk_type") == "section_summary_chunk"]
    paragraph_chunks = [chunk for chunk in source_chunks if chunk.get("chunk_type") == "paragraph_chunk"]
    if args.max_task_chunks:
        section_chunks = section_chunks[: args.max_task_chunks]
    if args.max_triple_chunks:
        paragraph_chunks = paragraph_chunks[: args.max_triple_chunks]

    total_usage = Counter()
    errors: list[dict[str, Any]] = []

    for idx, chunk in enumerate(section_chunks, start=1):
        chunk_id = chunk["chunk_id"]
        if chunk_id in existing_task:
            continue
        if args.dry_run:
            parsed = {"chunk_id": chunk_id, "task_frame_links": [], "candidate_new_task_frames": [], "candidate_terms": [], "review_notes": ["dry_run"]}
            usage = {}
        else:
            if client is None:
                raise RuntimeError("OpenAI client is required unless --dry-run is set.")
            parsed, usage = client.complete_json(
                TASK_FRAME_SYSTEM_PROMPT,
                task_frame_user_prompt(chunk, task_frames, evidence_payload_for_chunk(chunk, by_chunk), args.max_task_chars),
            )
        row = {
            "chunk_id": chunk_id,
            "chunk_type": chunk.get("chunk_type"),
            "section_no": chunk.get("section_no"),
            "model": args.model,
            "run_id": RUN_ID,
            "prompt_kind": "task_frame_linking",
            "parsed": parsed,
            "usage": usage,
        }
        append_jsonl(task_raw_path, row)
        add_usage(total_usage, usage)
        if args.sleep:
            time.sleep(args.sleep)
        if idx % 10 == 0:
            print(f"[task-frame] {idx}/{len(section_chunks)} complete", flush=True)

    for idx, chunk in enumerate(paragraph_chunks, start=1):
        chunk_id = chunk["chunk_id"]
        if chunk_id in existing_triple:
            continue
        evidence_rows = evidence_payload_for_chunk(chunk, by_chunk)
        if args.dry_run:
            parsed = {"chunk_id": chunk_id, "triples": [], "new_node_candidates": [], "review_notes": ["dry_run"]}
            usage = {}
        else:
            if client is None:
                raise RuntimeError("OpenAI client is required unless --dry-run is set.")
            try:
                parsed, usage = client.complete_json(
                    TRIPLE_SYSTEM_PROMPT,
                    triple_user_prompt(chunk, task_frames, evidence_rows, args.max_triple_chars),
                )
            except Exception as exc:  # keep long jobs resumable
                errors.append({"chunk_id": chunk_id, "error": str(exc)[:1000]})
                parsed = {"chunk_id": chunk_id, "triples": [], "new_node_candidates": [], "review_notes": [f"request_failed: {type(exc).__name__}"]}
                usage = {}
        row = {
            "chunk_id": chunk_id,
            "chunk_type": chunk.get("chunk_type"),
            "section_no": chunk.get("section_no"),
            "model": args.model,
            "run_id": RUN_ID,
            "prompt_kind": "triple_extraction",
            "parsed": parsed,
            "usage": usage,
        }
        append_jsonl(triple_raw_path, row)
        add_usage(total_usage, usage)
        if args.sleep:
            time.sleep(args.sleep)
        if idx % 10 == 0:
            print(f"[triple] {idx}/{len(paragraph_chunks)} complete", flush=True)

    task_rows = read_jsonl(task_raw_path)
    triple_rows = read_jsonl(triple_raw_path)
    meta = {
        "task_frame_requests": len(task_rows),
        "triple_requests": len(triple_rows),
        "usage": dict(total_usage),
        "errors": errors,
        "task_raw_path": str(task_raw_path),
        "triple_raw_path": str(triple_raw_path),
    }
    return task_rows, triple_rows, meta


def canonical_nodes_for_validation(task_frames: list[dict[str, Any]]) -> set[str]:
    ids = {base.ONTOLOGY_NODE_ID}
    ids.update(base.PROCESSES)
    ids.update(frame["id"] for frame in task_frames)
    ids.update(base.ENTITIES)
    return ids


def evidence_id_from_span(evidence_span: str, candidate_ids: list[str], evidence_by_id: dict[str, dict[str, Any]]) -> list[str]:
    text = (evidence_span or "").strip()
    if not text:
        return []
    normalized = re.sub(r"\s+", " ", text)
    for ev_id in candidate_ids:
        ev_text = re.sub(r"\s+", " ", evidence_by_id.get(ev_id, {}).get("text_span", ""))
        if normalized and (normalized in ev_text or ev_text in normalized):
            return [ev_id]
    return []


def apply_task_frame_links(task_frames: list[dict[str, Any]], task_rows: list[dict[str, Any]], evidence_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    frame_by_id = {frame["id"]: dict(frame) for frame in task_frames}
    llm_refs: dict[str, list[str]] = defaultdict(list)
    link_counts: Counter[str] = Counter()
    for row in task_rows:
        parsed = row.get("parsed") or {}
        for link in parsed.get("task_frame_links") or []:
            task_id = str(link.get("task_id") or "").strip()
            if task_id not in frame_by_id:
                continue
            evidence_ids = [ev for ev in link.get("evidence_ids") or [] if ev in evidence_by_id]
            if not evidence_ids:
                continue
            llm_refs[task_id].extend(evidence_ids)
            link_counts[task_id] += 1
    frames = []
    for frame in task_frames:
        updated = dict(frame)
        refs = list(dict.fromkeys(llm_refs.get(frame["id"], [])))
        updated["llm_confirmed_evidence_refs"] = refs
        updated["llm_task_frame_link_count"] = int(link_counts.get(frame["id"], 0))
        updated["evidence_refs"] = refs[:20] if refs else frame.get("evidence_refs", [])
        updated["evidence_spans"] = updated["evidence_refs"]
        updated["evidence_sections"] = sorted({str(evidence_by_id[ev]["section_no"]) for ev in updated["evidence_refs"] if ev in evidence_by_id})
        updated["extraction_run_id"] = RUN_ID
        updated["extraction_method"] = "openai_llm_task_frame_linking_with_seed_catalog"
        updated["review_status"] = "llm_confirmed_needs_human_review" if refs else "seed_fallback_needs_human_review"
        updated["confidence"] = 0.92 if refs else min(float(frame.get("confidence") or 0.7), 0.75)
        frames.append(updated)
    return frames


def scaffold_triples(task_frames: list[dict[str, Any]], evidence_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    triples = []
    seq = 1

    def add(source: str, predicate: str, target: str, refs: list[str], confidence: float = 0.95) -> None:
        nonlocal seq
        triples.append(
            base.make_triple(
                f"L2_TRI_SCAF_{seq:06d}",
                source,
                predicate,
                target,
                None,
                refs,
                evidence_by_id,
                confidence=confidence,
                relation_scope="schema_scaffold",
                extraction_method="schema_scaffold_not_llm",
            )
        )
        triples[-1]["extraction_run_id"] = RUN_ID
        seq += 1

    for process_id in base.PROCESSES:
        refs = []
        for frame in task_frames:
            if frame.get("parent_process_id") == process_id:
                refs.extend((frame.get("evidence_refs") or [])[:2])
        add(base.ONTOLOGY_NODE_ID, "HAS_PROCESS", process_id, refs[:4], 0.95)
    for frame in task_frames:
        add(frame["parent_process_id"], "HAS_TASK", frame["id"], (frame.get("evidence_refs") or [])[:4], 0.95)
    return triples


def convert_llm_triples(
    triple_rows: list[dict[str, Any]],
    task_frames: list[dict[str, Any]],
    evidence_by_id: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    allowed_node_ids = canonical_nodes_for_validation(task_frames)
    task_ids = {frame["id"] for frame in task_frames}
    triples: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen = set()
    seq = 1
    for row in triple_rows:
        parsed = row.get("parsed") or {}
        chunk_id = row.get("chunk_id", "")
        chunk_evidence_ids = [ev_id for ev_id, ev in evidence_by_id.items() if ev.get("chunk_id") == chunk_id]
        for item in parsed.get("triples") or []:
            subject_id = str(item.get("subject_id") or "").strip()
            predicate = str(item.get("predicate") or "").strip()
            object_id = str(item.get("object_id") or "").strip()
            frame_task_id = str(item.get("frame_task_id") or "").strip() or None
            evidence_refs = [str(ev).strip() for ev in item.get("evidence_ids") or [] if str(ev).strip() in evidence_by_id]
            if not evidence_refs:
                evidence_refs = evidence_id_from_span(str(item.get("evidence_span") or ""), chunk_evidence_ids, evidence_by_id)
            issues = []
            if subject_id not in allowed_node_ids:
                issues.append("subject_not_in_candidate_nodes")
            if object_id not in allowed_node_ids:
                issues.append("object_not_in_candidate_nodes")
            if predicate not in DOMAIN_PREDICATES:
                issues.append("predicate_not_allowed")
            if frame_task_id and frame_task_id not in task_ids:
                issues.append("frame_task_id_not_canonical")
            if not evidence_refs:
                issues.append("missing_valid_evidence_ids")
            key = (subject_id, predicate, object_id)
            if key in seen:
                issues.append("duplicate_spo")
            if issues:
                rejected.append({"chunk_id": chunk_id, "item": item, "issues": issues})
                continue
            seen.add(key)
            confidence = item.get("confidence", 0.72)
            try:
                confidence = float(confidence)
            except (TypeError, ValueError):
                confidence = 0.72
            relation_scope = str(item.get("relation_scope") or "process_step").strip()
            if relation_scope not in {"definition", "process_step", "principle", "empirical_claim", "example_case", "author_opinion"}:
                relation_scope = "process_step"
            triple = base.make_triple(
                f"L2_TRI_OPENAI_{seq:06d}",
                subject_id,
                predicate,
                object_id,
                frame_task_id,
                evidence_refs,
                evidence_by_id,
                confidence=max(0.0, min(1.0, confidence)),
                relation_scope=relation_scope,
                extraction_method=f"openai_chat_completions:{row.get('model')}",
            )
            triple["extraction_run_id"] = RUN_ID
            triple["llm_rationale"] = item.get("rationale", "")
            triple["source_chunk_id"] = chunk_id
            triples.append(triple)
            seq += 1
    return triples, rejected


def estimate_cost(model: str, usage: dict[str, Any]) -> dict[str, Any]:
    prices = MODEL_PRICE_PER_1M.get(model)
    prompt_tokens = int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
    completion_tokens = int(usage.get("completion_tokens") or usage.get("output_tokens") or 0)
    total_tokens = int(usage.get("total_tokens") or prompt_tokens + completion_tokens)
    payload = {
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "pricing_note": "Estimated from published per-1M token standard prices; actual bill can differ by service tier, caching, or account settings.",
    }
    if prices:
        payload["estimated_standard_cost_usd"] = round((prompt_tokens * prices["input"] + completion_tokens * prices["output"]) / 1_000_000, 6)
        payload["input_usd_per_1m"] = prices["input"]
        payload["output_usd_per_1m"] = prices["output"]
    else:
        payload["estimated_standard_cost_usd"] = None
    return payload


def render_openai_report(
    output_dir: Path,
    args: argparse.Namespace,
    extraction_meta: dict[str, Any],
    llm_triples: list[dict[str, Any]],
    rejected_llm_triples: list[dict[str, Any]],
    validated_triples: list[dict[str, Any]],
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    cq_results: list[dict[str, Any]],
    cost: dict[str, Any],
) -> str:
    pred_counts = Counter(triple["predicate"] for triple in llm_triples)
    execution_line = (
        "- 이번 실행은 드라이런이며 OpenAI API를 호출하지 않았다."
        if args.dry_run
        else "- 이번 실행은 실제 OpenAI API LLM 추론을 사용했다."
    )
    lines = [
        "# AX ZAIJE Layer2 KG OpenAI LLM Run Report",
        "",
        f"Generated: {base.now_iso()}",
        f"Run ID: `{RUN_ID}`",
        f"Model: `{args.model}`",
        f"Output dir: `{output_dir}`",
        "",
        "## 실행 요약",
        "",
        "| item | value |",
        "| --- | ---: |",
        f"| Task Frame LLM calls | {extraction_meta['task_frame_requests']} |",
        f"| Triple LLM calls | {extraction_meta['triple_requests']} |",
        f"| LLM accepted triples | {len(llm_triples)} |",
        f"| LLM rejected triples | {len(rejected_llm_triples)} |",
        f"| validated triples total | {len(validated_triples)} |",
        f"| graph nodes | {len(nodes)} |",
        f"| graph edges | {len(edges)} |",
        f"| CQ passed | {sum(1 for row in cq_results if row['passed'])}/{len(cq_results)} |",
        f"| estimated token cost USD | {cost.get('estimated_standard_cost_usd')} |",
        "",
        "## 비용 산정",
        "",
        "| field | value |",
        "| --- | ---: |",
        f"| prompt tokens | {cost['prompt_tokens']} |",
        f"| completion tokens | {cost['completion_tokens']} |",
        f"| total tokens | {cost['total_tokens']} |",
        f"| input USD / 1M | {cost.get('input_usd_per_1m', '')} |",
        f"| output USD / 1M | {cost.get('output_usd_per_1m', '')} |",
        "",
        f"- {cost['pricing_note']}",
        "",
        "## LLM Predicate Distribution",
        "",
        "| predicate | LLM triples |",
        "| --- | ---: |",
    ]
    for predicate, count in pred_counts.most_common():
        lines.append(f"| `{predicate}` | {count} |")
    lines += [
        "",
        "## 출력 파일",
        "",
        "- `19_openai_task_frame_links.raw.jsonl`: Task Frame linking 원본 LLM 응답",
        "- `20_openai_triples.raw.jsonl`: Triple extraction 원본 LLM 응답",
        "- `21_openai_triples.accepted.jsonl`: schema 후보 ID/evidence 조건을 통과한 LLM triple",
        "- `22_openai_triples.rejected.jsonl`: 자동 변환 단계에서 제외된 LLM triple",
        "- `08_triples.raw.jsonl`: schema scaffold + accepted LLM triples",
        "- `09_triples.validated.jsonl`: KG validator 통과 triple",
        "",
        "## 해석 경계",
        "",
        execution_line,
        "- 단, ontology/process/task catalog 자체는 설계서의 canonical seed를 기준으로 유지했다.",
        "- 최소 graph connectivity를 위해 `HAS_PROCESS`, `HAS_TASK` schema scaffold를 포함했고, 그 외 LLM이 제안한 relation 후보는 동일 validator로 자동 검증했다.",
        "- 사람 검수 전이므로 의미적 정답 gold KG로 주장하면 안 된다.",
    ]
    if extraction_meta.get("errors"):
        lines += ["", "## Request Errors", "", "| chunk_id | error |", "| --- | --- |"]
        for row in extraction_meta["errors"][:30]:
            err = str(row["error"]).replace("|", "\\|").replace("\n", " ")
            lines.append(f"| `{row['chunk_id']}` | {err} |")
    return "\n".join(lines) + "\n"


def render_openai_prompts_md(args: argparse.Namespace) -> str:
    return f"""# OpenAI LLM Extraction Prompts

Model: `{args.model}`

이 파일은 이번 OpenAI API 실행에서 사용한 실제 system prompt와 user prompt 구조를 보존한다.
실제 chunk별 user prompt는 원문 길이 때문에 `19_openai_task_frame_links.raw.jsonl`, `20_openai_triples.raw.jsonl`에는 저장하지 않고,
아래 템플릿과 각 chunk/evidence/candidate node JSON으로 재현한다.

## Task Frame System Prompt

```text
{TASK_FRAME_SYSTEM_PROMPT}
```

## Task Frame User Payload Fields

```json
{{
  "document_metadata": {{"book_id": "ZAIJE_1", "chapter_no": "...", "section_no": "...", "chunk_id": "..."}},
  "section_text": "section summary chunk text",
  "canonical_task_catalog": ["15 canonical task ids with labels/aliases/definitions"],
  "evidence_candidates": ["evidence_id/page/section/text rows from the chunk"],
  "output_schema": {{"task_frame_links": [], "candidate_new_task_frames": [], "candidate_terms": [], "review_notes": []}}
}}
```

## Triple System Prompt

```text
{TRIPLE_SYSTEM_PROMPT}
```

## Triple User Payload Fields

```json
{{
  "chunk": {{"chunk_id": "...", "section_no": "...", "text": "paragraph chunk text"}},
  "candidate_nodes": ["processes + canonical tasks + text-relevant canonical entities"],
  "allowed_predicates": ["predicate/domain/range from Layer2 schema"],
  "evidence_candidates": ["evidence_id/page/section/text rows from the chunk"],
  "relation_scope_options": ["definition", "process_step", "principle", "empirical_claim", "example_case", "author_opinion"],
  "output_schema": {{"triples": [], "new_node_candidates": [], "review_notes": []}}
}}
```
"""


def build_experiment(args: argparse.Namespace) -> dict[str, Any]:
    input_xlsx = Path(args.input_xlsx)
    methodology = Path(args.methodology)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    sheet_name, raw_rows = base.read_xlsx_table(input_xlsx)
    normalized_rows = base.normalize_rows(raw_rows, input_xlsx)
    source_chunks, evidence_spans, evidence_by_id = base.make_source_chunks(normalized_rows)
    source_profile_md, source_profile = base.build_source_profile_md(sheet_name, len(raw_rows), normalized_rows, source_chunks, evidence_spans, input_xlsx, methodology)
    seed_raw_task_frames, seed_task_frames = base.build_task_frames(evidence_spans)
    alias_dictionary_seed = base.build_alias_dictionary(seed_task_frames)

    client = None if args.dry_run else OpenAIChatClient(args.model, args.timeout, args.temperature, args.max_output_tokens, args.base_url)
    task_rows, triple_rows, extraction_meta = run_openai_extractions(output_dir, client, source_chunks, evidence_spans, seed_task_frames, args)
    task_frames = apply_task_frame_links(seed_task_frames, task_rows, evidence_by_id)
    alias_dictionary = base.build_alias_dictionary(task_frames)
    llm_triples, rejected_llm_triples = convert_llm_triples(triple_rows, task_frames, evidence_by_id)
    raw_triples = scaffold_triples(task_frames, evidence_by_id) + llm_triples

    nodes, edges = base.build_nodes_and_edges(normalized_rows, source_chunks, evidence_spans, task_frames, raw_triples, evidence_by_id, input_xlsx)
    validated_triples = base.validate_triples(raw_triples, nodes, evidence_by_id)
    cq_results = base.evaluate_cqs(edges)
    quality = base.compute_quality(nodes, edges, validated_triples, cq_results)
    review_rows = base.build_review_queue(nodes, edges, validated_triples, evidence_by_id)
    cost = estimate_cost(args.model, extraction_meta.get("usage", {}))

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
    llm_status_line = (
        "- LLM 상태: 드라이런으로 OpenAI API 호출 없이 파이프라인만 점검했다."
        if args.dry_run
        else f"- LLM 상태: OpenAI Chat Completions API로 `{args.model}` 실제 추론을 실행했다."
    )
    quality_report = quality_report.replace(
        "- LLM 상태: 현재 Python 환경에 `torch/transformers/vllm`이 없어 deterministic MVP extractor로 실행했다.",
        llm_status_line,
    )
    quality_report = quality_report.replace(
        "- LLM 교체 지점: `18_extraction_prompts.md`와 `05_task_frames.raw.jsonl`, `08_triples.raw.jsonl` 형식.",
        "- LLM 원본 응답: `19_openai_task_frame_links.raw.jsonl`, `20_openai_triples.raw.jsonl`.",
    )
    quality_report = quality_report.replace(f"Run ID: `{base.RUN_ID}`", f"Run ID: `{RUN_ID}`")
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
    base.write_text(output_dir / "18_extraction_prompts.md", render_openai_prompts_md(args))
    base.write_jsonl(output_dir / "21_openai_triples.accepted.jsonl", llm_triples)
    base.write_jsonl(output_dir / "22_openai_triples.rejected.jsonl", rejected_llm_triples)
    base.write_json(output_dir / "23_openai_usage_and_cost.json", cost)
    base.write_text(
        output_dir / "24_openai_llm_run_report.md",
        render_openai_report(output_dir, args, extraction_meta, llm_triples, rejected_llm_triples, validated_triples, nodes, edges, cq_results, cost),
    )

    summary = {
        "generated_at_utc": base.now_iso(),
        "run_id": RUN_ID,
        "input_xlsx": str(input_xlsx),
        "methodology": str(methodology),
        "output_dir": str(output_dir),
        "llm_runtime_status": "dry_run_no_api_call" if args.dry_run else "executed_openai_api",
        "model": args.model,
        "claim_status": "dry_run_pipeline_check_not_llm_result" if args.dry_run else "layer2_llm_bootstrap_ready_not_human_gold",
        "extraction_meta": extraction_meta,
        "cost_estimate": cost,
        "counts": {
            "valid_sentence_rows": len(normalized_rows),
            "source_chunks": len(source_chunks),
            "evidence_spans": len(evidence_spans),
            "task_frame_llm_rows": len(task_rows),
            "triple_llm_rows": len(triple_rows),
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
        "outputs": [
            "19_openai_task_frame_links.raw.jsonl",
            "20_openai_triples.raw.jsonl",
            "21_openai_triples.accepted.jsonl",
            "22_openai_triples.rejected.jsonl",
            "23_openai_usage_and_cost.json",
            "24_openai_llm_run_report.md",
            "08_triples.raw.jsonl",
            "09_triples.validated.jsonl",
            "10_nodes.jsonl",
            "11_edges.jsonl",
            "12_quality_report.md",
            "14_neo4j_import/nodes.csv",
            "14_neo4j_import/edges.csv",
            "14_neo4j_import/import.cypher",
        ],
        "seed_alias_dictionary_generated": bool(alias_dictionary_seed),
    }
    base.write_json(output_dir / "run_summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build AX ZAIJE Layer2 KG with OpenAI LLM extraction")
    parser.add_argument("--input-xlsx", default=str(base.DEFAULT_XLSX))
    parser.add_argument("--methodology", default=str(base.DEFAULT_METHODOLOGY))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--base-url", default="")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-output-tokens", type=int, default=1800)
    parser.add_argument("--max-task-chunks", type=int, default=0, help="0 means all section summary chunks")
    parser.add_argument("--max-triple-chunks", type=int, default=0, help="0 means all paragraph chunks")
    parser.add_argument("--max-task-chars", type=int, default=5000)
    parser.add_argument("--max-triple-chars", type=int, default=1800)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--sleep", type=float, default=0.05)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    summary = build_experiment(args)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
