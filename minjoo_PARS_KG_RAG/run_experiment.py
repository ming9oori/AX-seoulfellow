#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import traceback
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from kg_rag.common import load_yaml, normalize_text, read_json, utc_now, write_json, write_jsonl
from kg_rag.evaluation import (
    align_gold_evidence,
    evaluate_answers,
    evaluate_retrieval,
    load_qa_csv,
    write_metric_table,
)
from kg_rag.openai_backend import OpenAIBackend
from kg_rag.reranking import CrossEncoderReranker
from kg_rag.retrieval import (
    P1_RERANK_METHODS,
    QUERY_PROFILE_METHODS,
    GraphIndex,
    QPARetriever,
)
from kg_rag.snapshot import export_snapshot
from kg_rag.unsupervised_aspects import (
    P1B_PROFILE_FREE,
    P1G_PCF_GROUNDED,
    P1G_PROFILE_FREE,
    P1P_PARS,
    P1P_PARS_PROFILE_FREE,
    QUESTION_ONLY_UNSUPERVISED_ASPECT_METHODS,
    UNSUPERVISED_ASPECT_METHODS,
    PCFGroundedAspectExtractor,
    UnsupervisedAspectExtractor,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the PARS-KG-RAG experiment")
    parser.add_argument(
        "--config",
        type=Path,
        default=BASE_DIR / "config" / "experiment.yaml",
    )
    parser.add_argument(
        "--qa-csv",
        type=Path,
        default=None,
        help="Override paths.qa_csv from the selected config",
    )
    parser.add_argument("--run-id", default="")
    parser.add_argument("--limit", type=int, default=0, help="0 means all QA rows")
    parser.add_argument(
        "--include-development",
        action="store_true",
        help="Include configured development qids in metrics (diagnostic runs only)",
    )
    parser.add_argument(
        "--stage",
        choices=("all", "snapshot", "retrieve", "generate", "evaluate"),
        default="all",
    )
    parser.add_argument("--reuse-snapshot", action="store_true")
    return parser.parse_args()


def resolve_config(path: Path) -> dict[str, Any]:
    config = load_yaml(path.resolve())
    root = path.resolve().parent.parent
    for key in ("neo4j_env", "qa_csv", "cache_dir", "runs_dir"):
        config["paths"][key] = str((root / config["paths"][key]).resolve())
    return config


def default_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def heuristic_profile(
    question: str,
    error: str = "",
    *,
    configured: bool = False,
) -> dict[str, Any]:
    text = normalize_text(question)
    facets = ["identity", "evidence"]
    functions = ["fact"]
    answer_shape = "FACT"
    if any(token in text for token in ("정의", "무엇인가", "의미")):
        answer_shape, facets, functions = "DEFINITION", facets + ["definition"], ["definition", "fact"]
    if any(token in text for token in ("어떻게", "방법", "방안")):
        answer_shape, facets, functions = "METHOD", facets + ["action", "procedure"], ["procedure", "recommendation"]
    if any(token in text for token in ("절차", "단계", "순서")):
        answer_shape, facets, functions = "PROCEDURE", facets + ["procedure", "temporal"], ["procedure", "rule"]
    if any(token in text for token in ("왜", "이유", "원인")):
        answer_shape, facets = "REASON", facets + ["cause"]
    if any(token in text for token in ("차이", "비교", "어떻게 다른")):
        answer_shape, facets = "COMPARISON", facets + ["comparison", "qualifier"]
    if any(token in text for token in ("어떤", "무엇들", "항목", "내용은")):
        answer_shape, facets = "LIST", facets + ["object", "triple"]
    requires_qualifiers = any(
        token in text for token in ("전에", "후에", "경우", "조건", "예외", "때", "목적", "비교")
    )
    if requires_qualifiers:
        facets.append("qualifier")
    return {
        "answer_shape": answer_shape,
        "target_facets": list(dict.fromkeys(facets))[:8],
        "knowledge_functions": list(dict.fromkeys(functions))[:6],
        "key_terms": [text[:80]],
        "requires_qualifiers": requires_qualifiers,
        "requires_structured_fact": answer_shape in {"LIST", "METHOD", "COMPARISON", "PROCEDURE"},
        "rationale": (
            "configured deterministic Korean cue-based query profile"
            if configured
            else f"deterministic fallback after profiler failure: {error[:120]}"
        ),
        "fallback": not configured,
        "profile_source": "heuristic" if configured else "fallback",
    }


def dataset_audit(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "created_at": utc_now(),
        "qa_count": len(rows),
        "question_types": dict(Counter(row.get("question_type", "") for row in rows)),
        "difficulty": dict(Counter(row.get("difficulty", "") for row in rows)),
        "review_status": dict(Counter(row.get("review_status", "") for row in rows)),
        "answerable": dict(Counter(row.get("answerable", "") for row in rows)),
        "chapters": dict(Counter(row.get("chapter_title", "") for row in rows)),
        "warning": (
            "References are frozen for this pilot, but review_status is not changed by this runner. "
            "Pending references must be human-reviewed before publication-grade Gold evaluation."
        ),
    }


def build_backend(config: Mapping[str, Any]) -> OpenAIBackend:
    models = config["models"]
    return OpenAIBackend(
        cache_path=Path(config["paths"]["cache_dir"]) / "openai_cache.sqlite",
        embedding_model=models["embedding"],
        embedding_dimensions=int(models.get("embedding_dimensions", 1024)),
        embedding_provider=models.get("embedding_provider", "openai"),
        embedding_revision=models.get("embedding_revision"),
        embedding_device=models.get("embedding_device", "cpu"),
        embedding_dtype=models.get("embedding_dtype", "float32"),
        embedding_max_length=models.get("embedding_max_length"),
        embedding_query_prompt_name=models.get("embedding_query_prompt_name"),
        # Profile-free experiments do not configure or invoke a dedicated
        # Query Profile model.  Legacy profile-aware methods can still set it.
        profiler_model=models.get("query_profiler", models["answer_generator"]),
        generator_model=models["answer_generator"],
        aspect_analyzer_model=models.get("aspect_analyzer"),
        paraphrase_validator_model=models.get("paraphrase_validator"),
        reasoning_effort=models.get("reasoning_effort", "low"),
        max_retries=int(config["generation"]["max_retries"]),
    )


def make_profiles(
    qa_rows: list[Mapping[str, Any]],
    backend: OpenAIBackend,
    output_path: Path,
    concurrency: int,
    *,
    allow_fallback: bool = True,
    mode: str = "llm",
) -> list[dict[str, Any]]:
    if mode not in {"llm", "heuristic"}:
        raise ValueError("profiling.mode must be 'llm' or 'heuristic'")
    print(f"[profile:{mode}] {len(qa_rows)} questions")

    def one(row: Mapping[str, Any]) -> dict[str, Any]:
        if mode == "heuristic":
            return {
                "qid": row["qa_id"],
                "question": row["question"],
                "profile": heuristic_profile(row["question"], configured=True),
                "response_id": "",
                "cached": False,
                "error": "",
            }
        try:
            profile, response_id, cached = backend.profile_question(row["question"])
            return {
                "qid": row["qa_id"],
                "question": row["question"],
                "profile": profile,
                "response_id": response_id,
                "cached": cached,
                "error": "",
            }
        except Exception as exc:
            if not allow_fallback:
                raise RuntimeError(
                    f"Query profiling failed for {row['qa_id']} and fallback is disabled"
                ) from exc
            return {
                "qid": row["qa_id"],
                "question": row["question"],
                "profile": heuristic_profile(row["question"], str(exc)),
                "response_id": "",
                "cached": False,
                "error": f"{type(exc).__name__}: {exc}",
            }

    results: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {executor.submit(one, row): row["qa_id"] for row in qa_rows}
        for completed, future in enumerate(as_completed(futures), start=1):
            value = future.result()
            results[value["qid"]] = value
            if completed % 25 == 0 or completed == len(futures):
                print(f"[profile] {completed}/{len(futures)}")
    ordered = [results[row["qa_id"]] for row in qa_rows]
    write_jsonl(output_path, ordered)
    return ordered


def heuristic_aspects(question: str, error: str = "") -> dict[str, Any]:
    """Conservative emergency fallback; the official config disables it."""
    text = normalize_text(question)
    return {
        "domain_objects": [text[:120]],
        "actions": [text[:120]],
        "constraints": [],
        "desired_information": [text[:120]],
        "search_terms": [text[:120]],
        "rationale": f"deterministic fallback after Aspect analyzer failure: {error[:120]}",
        "fallback": True,
    }


def make_aspect_profiles(
    qa_rows: list[Mapping[str, Any]],
    backend: OpenAIBackend,
    output_path: Path,
    concurrency: int,
    *,
    allow_fallback: bool = False,
) -> list[dict[str, Any]]:
    print(f"[aspect] {len(qa_rows)} questions")

    def one(row: Mapping[str, Any]) -> dict[str, Any]:
        try:
            aspects, response_id, cached = backend.analyze_question_aspects(
                row["question"]
            )
            return {
                "qid": row["qa_id"],
                "question": row["question"],
                "aspects": aspects,
                "response_id": response_id,
                "cached": cached,
                "error": "",
            }
        except Exception as exc:
            if not allow_fallback:
                raise RuntimeError(
                    f"Aspect analysis failed for {row['qa_id']} and fallback is disabled"
                ) from exc
            return {
                "qid": row["qa_id"],
                "question": row["question"],
                "aspects": heuristic_aspects(row["question"], str(exc)),
                "response_id": "",
                "cached": False,
                "error": f"{type(exc).__name__}: {exc}",
            }

    results: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {executor.submit(one, row): row["qa_id"] for row in qa_rows}
        for completed, future in enumerate(as_completed(futures), start=1):
            value = future.result()
            results[value["qid"]] = value
            if completed % 25 == 0 or completed == len(futures):
                print(f"[aspect] {completed}/{len(futures)}")
    ordered = [results[row["qa_id"]] for row in qa_rows]
    write_jsonl(output_path, ordered)
    return ordered


def make_unsupervised_aspect_profiles(
    qa_rows: list[Mapping[str, Any]],
    backend: OpenAIBackend,
    output_path: Path,
    config: Mapping[str, Any],
    methods: Sequence[str],
) -> list[dict[str, Any]]:
    requested = [
        method
        for method in methods
        if method in QUESTION_ONLY_UNSUPERVISED_ASPECT_METHODS
    ]
    print(
        "[unsupervised-aspect] "
        f"{len(qa_rows)} questions x {len(requested)} variants"
    )
    extractor_config = dict(config)
    extractor_config["variants"] = requested
    extractor = UnsupervisedAspectExtractor(backend, extractor_config)
    results = extractor.extract_many(qa_rows)
    write_jsonl(output_path, results)
    return results


def make_pcf_grounded_aspect_profiles(
    qa_rows: list[Mapping[str, Any]],
    backend: OpenAIBackend,
    graph: GraphIndex,
    output_path: Path,
    config: Mapping[str, Any],
) -> list[dict[str, Any]]:
    print(f"[pcf-grounded-aspect] {len(qa_rows)} questions")
    extractor = PCFGroundedAspectExtractor(backend, graph, config)
    results = extractor.extract_many(qa_rows)
    write_jsonl(output_path, results)
    return results


def merge_unsupervised_aspect_profiles(
    qa_rows: Sequence[Mapping[str, Any]],
    *collections: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    by_qid: dict[str, dict[str, Any]] = {
        str(row["qa_id"]): {
            "qid": str(row["qa_id"]),
            "question": normalize_text(row["question"]),
            "variants": {},
        }
        for row in qa_rows
    }
    for collection in collections:
        for row in collection:
            qid = str(row["qid"])
            if qid not in by_qid:
                raise ValueError(f"Unknown qid in Aspect artifact: {qid}")
            variants = row.get("variants", {})
            if not isinstance(variants, Mapping):
                raise ValueError(f"Aspect variants must be a mapping for {qid}")
            overlap = set(by_qid[qid]["variants"]) & set(variants)
            if overlap:
                raise ValueError(
                    f"Duplicate Aspect variants for {qid}: {sorted(overlap)}"
                )
            by_qid[qid]["variants"].update(variants)
    return [by_qid[str(row["qa_id"])] for row in qa_rows]


def run_retrieval(
    qa_rows: list[Mapping[str, Any]],
    profiles: list[Mapping[str, Any]],
    retriever: QPARetriever,
    config: Mapping[str, Any],
    output_path: Path,
    aspect_profiles: list[Mapping[str, Any]] | None = None,
    unsupervised_aspect_profiles: list[Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    profile_by_qid = {row["qid"]: row["profile"] for row in profiles}
    aspect_by_qid = {
        row["qid"]: row["aspects"] for row in (aspect_profiles or [])
    }
    unsupervised_by_qid = {
        row["qid"]: row.get("variants", {})
        for row in (unsupervised_aspect_profiles or [])
    }
    total = len(qa_rows) * len(config["methods"]) * len(config["conditions"])
    print(f"[retrieve] {total} method-condition-question cases")
    results: list[dict[str, Any]] = []
    count = 0
    for row in qa_rows:
        for condition in config["conditions"]:
            for method in config["methods"]:
                question_aspects = None
                if method == "P1A_QPA_ASPECT_CROSS_ENCODER_MMR":
                    question_aspects = aspect_by_qid.get(row["qa_id"])
                elif method in UNSUPERVISED_ASPECT_METHODS:
                    question_aspects = unsupervised_by_qid.get(
                        row["qa_id"], {}
                    ).get(method)
                elif method in {
                    P1G_PROFILE_FREE,
                    P1P_PARS,
                    P1P_PARS_PROFILE_FREE,
                }:
                    # The direct-Aspect and P1-PARS ablations deliberately
                    # share P1-G's question-derived, graph-grounded Aspects.
                    # They change retrieval components, never the extractor.
                    question_aspects = unsupervised_by_qid.get(
                        row["qa_id"], {}
                    ).get(P1G_PCF_GROUNDED)
                results.append(
                    retriever.retrieve(
                        qid=row["qa_id"],
                        question=row["question"],
                        method=method,
                        condition=condition,
                        profile=profile_by_qid.get(row["qa_id"]),
                        aspects=question_aspects,
                    )
                )
                count += 1
                if count % 100 == 0 or count == total:
                    print(f"[retrieve] {count}/{total}")
    write_jsonl(output_path, results)
    return results


def _valid_citations(values: Any, evidence_ids: list[str]) -> list[str]:
    alias_to_id = {
        f"E{index}": evidence_id for index, evidence_id in enumerate(evidence_ids, start=1)
    }
    alias_to_id.update({evidence_id: evidence_id for evidence_id in evidence_ids})
    output: list[str] = []
    for value in values or []:
        normalized = normalize_text(value).strip("[]")
        evidence_id = alias_to_id.get(normalized)
        if evidence_id and evidence_id not in output:
            output.append(evidence_id)
    return output


def _strip_structured_citations(text: str) -> str:
    return normalize_text(
        re.sub(
            r"\[(?:E\d+|EV_[0-9a-fA-F]+)(?:\s*,\s*(?:E\d+|EV_[0-9a-fA-F]+))*\]",
            "",
            text,
        )
    )


def generate_answers(
    retrieval_rows: list[Mapping[str, Any]],
    backend: OpenAIBackend,
    config: Mapping[str, Any],
    output_path: Path,
) -> list[dict[str, Any]]:
    print(f"[generate] {len(retrieval_rows)} cases with online grounding verification")
    max_tokens = int(config["generation"]["max_output_tokens"])

    def one(row: Mapping[str, Any]) -> dict[str, Any]:
        retrieved_provenance = [
            {
                "evidence_id": item.get("evidence_id"),
                "rank": item.get("rank"),
                "source_file": item.get("source_file", ""),
                "page": item.get("page"),
                "section_path": item.get("section_path", ""),
                "retrieval_source": item.get("original_source", item.get("source", "")),
                "provenance": item.get("provenance", {}),
            }
            for item in row.get("evidence", [])
        ]
        base = {
            "qid": row["qid"],
            "question": row["question"],
            "method": row["method"],
            "condition": row["condition"],
            "retrieval_status": row["status"],
            "retrieved_evidence_ids": [item["evidence_id"] for item in row.get("evidence", [])],
            "retrieved_evidence_provenance": retrieved_provenance,
            "created_at": utc_now(),
        }
        if not row.get("evidence"):
            return {
                **base,
                "prediction_answer": "현재 검색된 원문 근거만으로는 질문에 답하기 어렵습니다.",
                "citations": [],
                "citation_provenance": [],
                "status": "NO_CONTEXT",
                "draft": {},
                "verification": {},
                "generation_response_id": "",
                "verification_response_id": "",
                "cached": False,
                "api_failed": False,
                "error": "",
            }
        try:
            draft, generation_id, cached_generation = backend.generate_answer(
                question=row["question"], context=row["context"], max_output_tokens=max_tokens
            )
            verification, verification_id, cached_verification = backend.verify_answer(
                question=row["question"],
                context=row["context"],
                draft=draft,
                max_output_tokens=max_tokens,
            )
            retrieved_ids = [item["evidence_id"] for item in row.get("evidence", [])]
            citations = _valid_citations(
                verification.get("supported_citations"), retrieved_ids
            )
            answer = _strip_structured_citations(
                verification.get("corrected_answer", "")
            )
            limitation = normalize_text(verification.get("limitation"))
            if limitation and limitation not in answer:
                answer = normalize_text(f"{answer} {limitation}")
            supported = bool(verification.get("supported")) and bool(citations)
            status = "ANSWERED" if supported and draft.get("status") == "ANSWERED" else "INSUFFICIENT"
            if not answer:
                answer = "현재 검색된 원문 근거만으로는 질문에 답하기 어렵습니다."
                status = "INSUFFICIENT"
            return {
                **base,
                "prediction_answer": answer,
                "citations": citations,
                "citation_provenance": [
                    value
                    for value in retrieved_provenance
                    if value["evidence_id"] in citations
                ],
                "status": status,
                "draft": draft,
                "verification": verification,
                "generation_response_id": generation_id,
                "verification_response_id": verification_id,
                "cached": cached_generation and cached_verification,
                "api_failed": False,
                "error": "",
            }
        except Exception as exc:
            return {
                **base,
                "prediction_answer": "",
                "citations": [],
                "citation_provenance": [],
                "status": "API_FAILED",
                "draft": {},
                "verification": {},
                "generation_response_id": "",
                "verification_response_id": "",
                "cached": False,
                "api_failed": True,
                "error": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc(limit=4),
            }

    results: list[dict[str, Any]] = []
    concurrency = int(config["generation"]["concurrency"])
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(one, row) for row in retrieval_rows]
        for completed, future in enumerate(as_completed(futures), start=1):
            results.append(future.result())
            if completed % 50 == 0 or completed == len(futures):
                print(f"[generate] {completed}/{len(futures)}")
    results.sort(key=lambda item: (item["qid"], item["condition"], item["method"]))
    write_jsonl(output_path, results)
    api_failures = [row for row in results if row.get("api_failed")]
    if api_failures and bool(config["generation"].get("fail_on_api_error", False)):
        raise RuntimeError(
            f"Answer generation failed for {len(api_failures)}/{len(results)} cases; "
            "partial failures were written, but evaluation is intentionally blocked."
        )
    return results


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def validate_question_artifact(
    qa_rows: list[Mapping[str, Any]],
    artifact_rows: list[Mapping[str, Any]],
    *,
    label: str,
) -> None:
    expected = [
        (str(row["qa_id"]), normalize_text(row["question"])) for row in qa_rows
    ]
    actual = [
        (str(row.get("qid", "")), normalize_text(row.get("question", "")))
        for row in artifact_rows
    ]
    if actual != expected:
        raise ValueError(
            f"Existing {label} does not match the selected QA rows in order, ID, or text"
        )


def write_final_report(
    path: Path,
    *,
    run_id: str,
    snapshot: Mapping[str, Any],
    audit: Mapping[str, Any],
    alignment: Mapping[str, Any],
    retrieval_summary: list[Mapping[str, Any]],
    answer_summary: list[Mapping[str, Any]],
) -> None:
    manifest = snapshot["manifest"]
    evaluated_methods = {row["method"] for row in answer_summary}
    p0_vs_vanilla = {
        "P0_QPA",
        "B0_VANILLA_DENSE_RAG",
    }.issubset(evaluated_methods)
    has_p1a = "P1A_QPA_ASPECT_CROSS_ENCODER_MMR" in evaluated_methods
    has_p1 = "P1_QPA_CROSS_ENCODER_MMR" in evaluated_methods
    has_p1u = bool(set(UNSUPERVISED_ASPECT_METHODS) & evaluated_methods)
    has_profile_free_component_ablation = {
        P1B_PROFILE_FREE,
        P1G_PROFILE_FREE,
        P1P_PARS_PROFILE_FREE,
    }.issubset(evaluated_methods)
    synthetic_count = int(
        audit.get("review_status", {}).get("synthetic_not_human_reviewed", 0)
    )
    source_derived_count = int(audit["qa_count"]) - synthetic_count
    if synthetic_count:
        dataset_warning = (
            f"- QA는 원문 EvidenceSpan 기반 {source_derived_count}문항과 합성 일반화 "
            f"{synthetic_count}문항으로 구성됩니다. 후자는 현업자 독립 작성본이 아니므로 "
            "일반 실무 질문 전체의 성능으로 과장하면 안 됩니다."
        )
    else:
        dataset_warning = (
            "- 현재 QA는 원문 EvidenceSpan을 바탕으로 생성되어 직접 원문 검색에 "
            "유리할 수 있으므로, 일반 실무 질문 전체의 성능으로 과장하면 안 됩니다."
        )
    if has_profile_free_component_ablation:
        report_title = "# P1-PARS Profile-free 최소 구성요소 Ablation 보고서"
    elif has_p1u:
        report_title = "# PCF-first 비지도 질문 Aspect 선별 실험 보고서"
    elif has_p1a:
        report_title = "# PCF-first P1 및 질문 Aspect 확장 실험 보고서"
    elif has_p1:
        report_title = "# PCF-first P1 재정렬 실험 보고서"
    elif p0_vs_vanilla:
        report_title = "# 초기 P0 vs 일반 Dense RAG 실험 보고서"
    else:
        report_title = "# PARS-KG-RAG 실험 보고서"
    lines = [
        report_title,
        "",
        f"- run_id: `{run_id}`",
        f"- 실행 시간(UTC): `{utc_now()}`",
        f"- QA: {audit['qa_count']}개",
        f"- 공식 평가: {answer_summary[0]['n'] if answer_summary else 0}개(개발 문항 제외)",
        f"- Neo4j 스냅샷: PCF {manifest['node_counts']['PCFProcess']}, TaskFrame {manifest['node_counts']['TaskFrame']}, TaskMention {manifest['node_counts']['TaskMention']}, Fact {manifest['node_counts']['Fact']}, EvidenceSpan {manifest['node_counts']['EvidenceSpan']}",
        "",
        "## 해석 전 필수 주의",
        "",
        f"- 제공된 참조 답변의 검수 상태: `{audit['review_status']}`. 현재 점수는 임시 참조답 기반 파일럿이며 최종 Gold 성능으로 과장하면 안 됩니다.",
        f"- QA 원문 항목과 Neo4j EvidenceSpan 정렬률: {100 * alignment['evidence_item_alignment_rate']:.2f}% ({alignment['matched_evidence_item_count']}/{alignment['evidence_item_count']}).",
        "- PCF/TaskFrame Gold는 현재 그래프 경로로 역추론했으므로, 독립적 온톨로지 정답률이 아니라 검색 일관성 지표입니다.",
        dataset_warning,
        "",
        "## 최종 답변 성능",
        "",
        "검색 지표는 파이프라인 진단용 산출물에만 보존하며, 주 성능은 최종 답변 지표로 보고합니다.",
        "",
        "| 방법 | 조건 | BLEU-4 | R-1 | R-2 | R-L | BERTScore | 답변 보류율 |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in answer_summary:
        lines.append(
            f"| {row['method']} | {row['condition']} | {row['bleu4_kiwi']:.2f} | "
            f"{row['rouge1_f1_kiwi']:.2f} | {row['rouge2_f1_kiwi']:.2f} | "
            f"{row['rougeL_f1_kiwi']:.2f} | {row['bertscore_f1_xlmr17']:.2f} | "
            f"{100 * row['insufficient_rate']:.2f}% |"
        )
    lines.extend(
        [
            "",
            "## 방법론 결론 판정 기준",
            "",
        ]
    )
    if p0_vs_vanilla:
        lines.extend(
            [
                "- 주 비교는 `P0_QPA - B0_VANILLA_DENSE_RAG`의 paired bootstrap 차이입니다.",
                "- 95% CI가 0보다 크면 P0 우세, 0보다 작으면 일반 Dense RAG 우세, 0을 포함하면 우열 불명으로 판정합니다.",
                "- 이 비교는 두 완성 파이프라인의 종단 간 비교이며, 그래프만의 순수 인과 효과를 분리한 ablation은 아닙니다.",
            ]
        )
        if has_p1:
            lines.append(
                "- `P1 - P0`는 PCF-first 후보 생성은 그대로 둔 채 Cross-Encoder/RRF/MMR 최종 재정렬의 추가 효과를 봅니다."
            )
        if has_p1a:
            lines.append(
                "- `P1-A - P1`은 같은 최종 재정렬에서 질문 Aspect 분석 신호만 추가한 효과를 봅니다."
            )
        if has_p1u:
            lines.append(
                "- `P1-U - P1/P1-A`는 동일한 PCF-first·Cross-Encoder·RRF·MMR 경로에서 질문-only 비지도 Aspect 신호만 바꾼 탐색 비교입니다."
            )
    else:
        if has_profile_free_component_ablation:
            lines.extend(
                [
                    "- `PF-Direct - PF-Base`는 같은 Profile-free PCF-first 경로에 Direct Aspect만 추가한 효과를 봅니다.",
                    "- `PF-Full - PF-Direct`는 같은 입력·모델·후보 설정에서 PARS만 추가한 효과를 봅니다.",
                    "- 점추정치뿐 아니라 paired bootstrap 95% CI가 0을 제외하는지 함께 판정합니다.",
                ]
            )
        if {"P0_QPA", "B0_EVIDENCE_HYBRID"}.issubset(evaluated_methods):
            lines.append("- P0가 B0보다 최종 답변 지표가 높으면 구조화 속성과 그래프 경로의 추가 가치가 있습니다.")
        if {"P0_QPA", "A1_FIXED_PROPERTIES"}.issubset(evaluated_methods):
            lines.append("- P0가 A1보다 높으면 질문 별 속성 활성화의 가치가 있습니다.")
        if {"P0_QPA", "A2_NO_GAP_ADAPTATION"}.issubset(evaluated_methods):
            lines.append("- P0가 A2보다 높으면 PCF 매핑·그래프 결손을 보완하는 검색의 가치가 있습니다.")
        if {"V2_EVIDENCE_GRAPH_LATE_FUSION", "B0_EVIDENCE_HYBRID"}.issubset(evaluated_methods):
            lines.append("- V2가 B0보다 높으면 원문 후보를 보존한 graph late fusion의 추가 가치가 있습니다.")
        if {"V2_EVIDENCE_GRAPH_LATE_FUSION", "P0_QPA"}.issubset(evaluated_methods):
            lines.append("- V2가 P0보다 높으면 PCF hard routing 대신 evidence-first 후보 결합을 사용하는 설계가 더 적합하다는 뜻입니다.")
    lines.extend(
        [
            "",
            "자세한 답변 bootstrap CI와 문항별 결과는 `metrics/` 산출물을 참조하십시오.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    config = resolve_config(args.config)
    if args.qa_csv is not None:
        config["paths"]["qa_csv"] = str(args.qa_csv.resolve())
    run_id = args.run_id or default_run_id()
    run_dir = Path(config["paths"]["runs_dir"]) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    write_json(run_dir / "resolved_config.json", config)

    qa_rows = load_qa_csv(
        Path(config["paths"]["qa_csv"]),
        require_answers=args.stage in {"all", "evaluate"},
    )
    if args.limit:
        qa_rows = qa_rows[: args.limit]
    audit = dataset_audit(qa_rows)
    write_json(run_dir / "00_dataset_audit.json", audit)

    snapshot_path = run_dir / "00_graph_snapshot.json"
    if snapshot_path.exists() and args.reuse_snapshot:
        snapshot = read_json(snapshot_path)
    else:
        print("[snapshot] reading live Neo4j Aura")
        snapshot = export_snapshot(
            env_path=Path(config["paths"]["neo4j_env"]),
            output_path=snapshot_path,
            transport=config["neo4j"]["transport"],
            connect_timeout=float(config["neo4j"]["connect_timeout_seconds"]),
            query_timeout=float(config["neo4j"]["query_timeout_seconds"]),
            max_retries=int(config["neo4j"]["max_retries"]),
        )
        print(f"[snapshot] {snapshot['manifest']['node_counts']}")
    if args.stage == "snapshot":
        return

    backend = build_backend(config)
    graph: GraphIndex | None = None

    def get_graph() -> GraphIndex:
        nonlocal graph
        if graph is None:
            print("[index] embedding graph property views")
            graph = GraphIndex(
                snapshot,
                backend,
                embedding_batch_size=int(
                    config["retrieval"]["embedding_batch_size"]
                ),
            )
        return graph

    profiles: list[dict[str, Any]] = []
    uses_query_profiles = bool(
        set(QUERY_PROFILE_METHODS) & set(config["methods"])
    )
    if uses_query_profiles:
        profiles_path = run_dir / "01_query_profiles.jsonl"
        if profiles_path.exists() and args.stage in {"retrieve", "generate", "evaluate"}:
            profiles = read_jsonl(profiles_path)
            validate_question_artifact(qa_rows, profiles, label="query profiles")
        else:
            profiles = make_profiles(
                qa_rows,
                backend,
                profiles_path,
                concurrency=int(config["generation"]["concurrency"]),
                allow_fallback=bool(
                    config.get("profiling", {}).get("allow_fallback", True)
                ),
                mode=str(config.get("profiling", {}).get("mode", "llm")),
            )

    aspect_profiles: list[dict[str, Any]] = []
    uses_llm_aspect_analysis = (
        "P1A_QPA_ASPECT_CROSS_ENCODER_MMR" in config["methods"]
    )
    if uses_llm_aspect_analysis:
        aspects_path = run_dir / "01_question_aspects.jsonl"
        if aspects_path.exists() and args.stage in {
            "retrieve",
            "generate",
            "evaluate",
        }:
            aspect_profiles = read_jsonl(aspects_path)
            validate_question_artifact(
                qa_rows,
                aspect_profiles,
                label="LLM Aspect profiles",
            )
        else:
            aspect_profiles = make_aspect_profiles(
                qa_rows,
                backend,
                aspects_path,
                concurrency=int(config["generation"]["concurrency"]),
                allow_fallback=bool(
                    config.get("aspect_analysis", {}).get("allow_fallback", False)
                ),
            )

    question_only_aspect_profiles: list[dict[str, Any]] = []
    uses_question_only_aspects = bool(
        set(QUESTION_ONLY_UNSUPERVISED_ASPECT_METHODS) & set(config["methods"])
    )
    if uses_question_only_aspects:
        unsupervised_path = run_dir / "01_question_only_aspects.jsonl"
        if unsupervised_path.exists() and args.stage in {
            "retrieve",
            "generate",
            "evaluate",
        }:
            question_only_aspect_profiles = read_jsonl(unsupervised_path)
            validate_question_artifact(
                qa_rows,
                question_only_aspect_profiles,
                label="question-only Aspect profiles",
            )
        else:
            question_only_aspect_profiles = make_unsupervised_aspect_profiles(
                qa_rows,
                backend,
                unsupervised_path,
                config.get("unsupervised_aspect", {}),
                config["methods"],
            )

    grounded_aspect_profiles: list[dict[str, Any]] = []
    uses_pcf_grounded_aspects = bool(
        {
            P1G_PCF_GROUNDED,
            P1G_PROFILE_FREE,
            P1P_PARS,
            P1P_PARS_PROFILE_FREE,
        }
        & set(config["methods"])
    )
    if uses_pcf_grounded_aspects:
        grounded_path = run_dir / "01_pcf_grounded_aspects.jsonl"
        if grounded_path.exists() and args.stage in {
            "retrieve",
            "generate",
            "evaluate",
        }:
            grounded_aspect_profiles = read_jsonl(grounded_path)
            validate_question_artifact(
                qa_rows,
                grounded_aspect_profiles,
                label="PCF-grounded Aspect profiles",
            )
        else:
            grounded_aspect_profiles = make_pcf_grounded_aspect_profiles(
                qa_rows,
                backend,
                get_graph(),
                grounded_path,
                config.get("pcf_grounded_aspect", {}),
            )

    unsupervised_aspect_profiles = merge_unsupervised_aspect_profiles(
        qa_rows,
        question_only_aspect_profiles,
        grounded_aspect_profiles,
    )

    retrieval_path = run_dir / "02_retrieval.jsonl"
    if retrieval_path.exists() and args.stage in {"generate", "evaluate"}:
        retrieval_rows = read_jsonl(retrieval_path)
    else:
        cross_encoder = None
        if set(P1_RERANK_METHODS) & set(config["methods"]):
            print("[reranker] loading pinned multilingual cross-encoder")
            cross_encoder = CrossEncoderReranker(
                config["retrieval"]["p0_cross_encoder_rerank"]
            )
        retriever = QPARetriever(
            get_graph(),
            config["retrieval"],
            cross_encoder=cross_encoder,
        )
        retrieval_rows = run_retrieval(
            qa_rows,
            profiles,
            retriever,
            config,
            retrieval_path,
            aspect_profiles=aspect_profiles,
            unsupervised_aspect_profiles=unsupervised_aspect_profiles,
        )
    gold_rows, alignment_report = align_gold_evidence(qa_rows, snapshot)
    write_jsonl(run_dir / "03_aligned_gold.jsonl", gold_rows)
    write_json(run_dir / "03_alignment_report.json", alignment_report)
    dev_qids = set(config["evaluation"].get("development_qids", []))
    official_qids = {
        row["qa_id"]
        for row in qa_rows
        if args.include_development or row["qa_id"] not in dev_qids
    }
    official_retrieval = [row for row in retrieval_rows if row["qid"] in official_qids]
    official_gold = [row for row in gold_rows if row["qid"] in official_qids]
    retrieval_per_question, retrieval_summary = evaluate_retrieval(
        official_retrieval, official_gold
    )
    write_jsonl(run_dir / "03_retrieval_metrics_per_question.jsonl", retrieval_per_question)
    write_json(run_dir / "03_retrieval_metric_summary.json", retrieval_summary)
    if args.stage == "retrieve":
        return

    answers_path = run_dir / "04_answers.jsonl"
    if answers_path.exists() and args.stage == "evaluate":
        answer_rows = read_jsonl(answers_path)
    else:
        answer_rows = generate_answers(retrieval_rows, backend, config, answers_path)
    if args.stage == "generate":
        return

    metrics_dir = run_dir / "metrics"
    metrics_dir.mkdir(exist_ok=True)
    official_qa_rows = [row for row in qa_rows if row["qa_id"] in official_qids]
    answer_summary, _ = evaluate_answers(
        answer_rows=answer_rows,
        qa_rows=official_qa_rows,
        output_dir=metrics_dir,
        config=config,
    )
    write_metric_table(metrics_dir / "answer_metric_table.md", answer_summary)
    write_final_report(
        run_dir / "FINAL_REPORT.md",
        run_id=run_id,
        snapshot=snapshot,
        audit=audit,
        alignment=alignment_report,
        retrieval_summary=retrieval_summary,
        answer_summary=answer_summary,
    )
    print(f"[done] {run_dir}")


if __name__ == "__main__":
    main()
