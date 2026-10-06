from __future__ import annotations

import csv
import importlib.metadata
import json
import math
import platform
import statistics
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
from kiwipiepy import Kiwi
from rouge_score.rouge_scorer import RougeScorer
from sacrebleu.metrics import BLEU

from .common import (
    normalize_match_text,
    normalize_text,
    parse_jsonish,
    utc_now,
    write_json,
    write_jsonl,
)
from .unsupervised_aspects import (
    P1B_PROFILE_FREE,
    P1G_PCF_GROUNDED,
    P1G_PROFILE_FREE,
    P1P_PARS,
    P1P_PARS_PROFILE_FREE,
    P1U_ATTENTION_SEEKER,
    P1U_EMBEDRANK,
    P1U_EMBEDRANK_MMR,
    P1U_TFIDF,
)


EVIDENCE_ONLY_METHODS = {"B0_VANILLA_DENSE_RAG", "B0_EVIDENCE_HYBRID"}

ANSWER_COMPARISON_PAIRS = (
    ("P0_QPA", "B0_VANILLA_DENSE_RAG"),
    ("P0_QPA", "B0_EVIDENCE_HYBRID"),
    ("P0_QPA", "A1_FIXED_PROPERTIES"),
    ("P0_QPA", "A2_NO_GAP_ADAPTATION"),
    ("V2_EVIDENCE_GRAPH_LATE_FUSION", "B0_EVIDENCE_HYBRID"),
    ("V2_EVIDENCE_GRAPH_LATE_FUSION", "P0_QPA"),
    ("P1_QPA_CROSS_ENCODER_MMR", "P0_QPA"),
    ("P1_QPA_CROSS_ENCODER_MMR", "B0_VANILLA_DENSE_RAG"),
    ("P1A_QPA_ASPECT_CROSS_ENCODER_MMR", "P1_QPA_CROSS_ENCODER_MMR"),
    ("P1A_QPA_ASPECT_CROSS_ENCODER_MMR", "P0_QPA"),
    ("P1A_QPA_ASPECT_CROSS_ENCODER_MMR", "B0_VANILLA_DENSE_RAG"),
    (P1U_TFIDF, "P1_QPA_CROSS_ENCODER_MMR"),
    (P1U_TFIDF, "P1A_QPA_ASPECT_CROSS_ENCODER_MMR"),
    (P1U_EMBEDRANK, "P1_QPA_CROSS_ENCODER_MMR"),
    (P1U_EMBEDRANK, "P1A_QPA_ASPECT_CROSS_ENCODER_MMR"),
    (P1U_EMBEDRANK_MMR, "P1_QPA_CROSS_ENCODER_MMR"),
    (P1U_EMBEDRANK_MMR, "P1A_QPA_ASPECT_CROSS_ENCODER_MMR"),
    (P1U_ATTENTION_SEEKER, "P1_QPA_CROSS_ENCODER_MMR"),
    (P1U_ATTENTION_SEEKER, "B0_VANILLA_DENSE_RAG"),
    (P1G_PCF_GROUNDED, "B0_VANILLA_DENSE_RAG"),
    (P1G_PCF_GROUNDED, "P1_QPA_CROSS_ENCODER_MMR"),
    (P1G_PCF_GROUNDED, "P1A_QPA_ASPECT_CROSS_ENCODER_MMR"),
    (P1P_PARS, "B0_VANILLA_DENSE_RAG"),
    (P1P_PARS, "P1_QPA_CROSS_ENCODER_MMR"),
    (P1P_PARS, "P1A_QPA_ASPECT_CROSS_ENCODER_MMR"),
    (P1P_PARS, P1G_PCF_GROUNDED),
    (P1P_PARS_PROFILE_FREE, "B0_VANILLA_DENSE_RAG"),
    (P1P_PARS_PROFILE_FREE, P1B_PROFILE_FREE),
    (P1P_PARS_PROFILE_FREE, P1G_PROFILE_FREE),
    (P1P_PARS_PROFILE_FREE, P1P_PARS),
    (P1P_PARS_PROFILE_FREE, P1G_PCF_GROUNDED),
    (P1G_PROFILE_FREE, P1B_PROFILE_FREE),
)


def load_qa_csv(path: Path, *, require_answers: bool = True) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"QA CSV is empty: {path}")
    qids = [row.get("qa_id", "") for row in rows]
    if any(not qid for qid in qids):
        raise ValueError("A QA row has an empty qa_id")
    duplicates = [qid for qid, count in Counter(qids).items() if count > 1]
    if duplicates:
        raise ValueError(f"Duplicate qa_id values: {duplicates[:10]}")
    if require_answers and any(not normalize_text(row.get("answer")) for row in rows):
        raise ValueError("A QA row has an empty reference answer")
    return rows


def _json_list(value: Any) -> list[str]:
    parsed = parse_jsonish(value, [])
    if isinstance(parsed, str):
        parsed = [parsed]
    if not isinstance(parsed, list):
        return []
    return list(dict.fromkeys(normalize_text(item) for item in parsed if normalize_text(item)))


def _optional_bool(value: Any) -> bool | None:
    text = normalize_text(value).lower()
    if text == "true":
        return True
    if text == "false":
        return False
    return None


def _pages(row: Mapping[str, Any]) -> set[str]:
    values = parse_jsonish(row.get("page"), [])
    if not isinstance(values, list):
        values = [row.get("page_start"), row.get("page_end")]
    return {normalize_text(value) for value in values if normalize_text(value)}


def align_gold_evidence(
    qa_rows: Sequence[Mapping[str, Any]], snapshot: Mapping[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    evidence = {
        row["properties"]["id"]: row["properties"]
        for row in snapshot["evidence_spans"]
    }
    exact: dict[str, list[str]] = defaultdict(list)
    by_page: dict[str, list[str]] = defaultdict(list)
    for evidence_id, properties in evidence.items():
        exact[normalize_match_text(properties.get("name"))].append(evidence_id)
        by_page[normalize_text(properties.get("page"))].append(evidence_id)

    facts_by_evidence: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for fact_row in snapshot["facts"]:
        for evidence_id in fact_row.get("evidence_ids", []):
            facts_by_evidence[evidence_id].append(fact_row)
    mentions_by_evidence: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for mention_row in snapshot["taskmentions"]:
        for evidence_id in mention_row.get("evidence_ids", []):
            mentions_by_evidence[evidence_id].append(mention_row)
    mappings_by_frame: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for mapping in snapshot["pcf_mappings"]:
        mappings_by_frame[mapping["taskframe_id"]].append(mapping)

    aligned: list[dict[str, Any]] = []
    total_items = 0
    matched_items = 0
    fuzzy_items = 0
    explicit_gold_items = 0
    qa_with_explicit_gold = 0
    for row in qa_rows:
        explicit_evidence = _json_list(row.get("gold_evidence_span_ids"))
        unknown_evidence = sorted(set(explicit_evidence) - set(evidence))
        if unknown_evidence:
            raise ValueError(
                f"Unknown explicit Gold EvidenceSpan IDs for {row['qa_id']}: {unknown_evidence}"
            )
        matches: list[dict[str, Any]] = []
        if explicit_evidence:
            gold_evidence_ids = explicit_evidence
            matches = [
                {"evidence_id": evidence_id, "mode": "explicit_gold", "score": 1.0}
                for evidence_id in explicit_evidence
            ]
            explicit_gold_items += len(explicit_evidence)
            qa_with_explicit_gold += 1
        else:
            raw_items = parse_jsonish(row.get("evidence_text"), [])
            if isinstance(raw_items, str):
                raw_items = [raw_items]
            pages = _pages(row)
            for raw_text in raw_items:
                text = normalize_text(raw_text)
                if not text:
                    continue
                total_items += 1
                key = normalize_match_text(text)
                candidates = exact.get(key, [])
                if candidates:
                    page_candidates = [
                        item
                        for item in candidates
                        if normalize_text(evidence[item].get("page")) in pages
                    ]
                    evidence_id = (page_candidates or candidates)[0]
                    matches.append({"evidence_id": evidence_id, "mode": "exact", "score": 1.0})
                    matched_items += 1
                    continue
                pool = [item for page in pages for item in by_page.get(page, [])]
                if not pool:
                    pool = list(evidence)
                best_id = ""
                best_score = 0.0
                for evidence_id in pool:
                    score = SequenceMatcher(
                        None, key, normalize_match_text(evidence[evidence_id].get("name"))
                    ).ratio()
                    if score > best_score:
                        best_id, best_score = evidence_id, score
                if best_id and best_score >= 0.92:
                    matches.append({"evidence_id": best_id, "mode": "fuzzy", "score": best_score})
                    matched_items += 1
                    fuzzy_items += 1
                else:
                    matches.append({"evidence_id": "", "mode": "unmatched", "score": best_score})
            gold_evidence_ids = sorted(
                {item["evidence_id"] for item in matches if item["evidence_id"]}
            )

        inferred_taskframes: set[str] = set()
        for evidence_id in gold_evidence_ids:
            for fact_row in facts_by_evidence.get(evidence_id, []):
                inferred_taskframes.update(
                    link["taskframe_id"]
                    for link in fact_row.get("frame_links", [])
                    if link.get("taskframe_id")
                )
            inferred_taskframes.update(
                mention_row["taskframe_id"]
                for mention_row in mentions_by_evidence.get(evidence_id, [])
                if mention_row.get("taskframe_id")
            )
        explicit_taskframes = _json_list(row.get("gold_taskframe_ids"))
        gold_taskframes = set(explicit_taskframes) if explicit_taskframes else inferred_taskframes
        inferred_pcfs = {
            mapping["pcf_id"]
            for frame_id in gold_taskframes
            for mapping in mappings_by_frame.get(frame_id, [])
            if mapping["relationship_type"] == "MAPS_TO_PCF"
        }
        explicit_pcfs = _json_list(row.get("gold_pcf_ids"))
        gold_pcfs = sorted(set(explicit_pcfs) if explicit_pcfs else inferred_pcfs)
        gold_facts = _json_list(row.get("gold_fact_ids"))
        gold_relations = _json_list(row.get("gold_relation_types"))
        gold_path = parse_jsonish(row.get("gold_path"), [])
        try:
            min_hops = int(row["min_hops"]) if normalize_text(row.get("min_hops")) else None
        except (TypeError, ValueError):
            raise ValueError(f"Invalid min_hops for {row['qa_id']}: {row.get('min_hops')!r}")
        aligned.append(
            {
                "qid": row["qa_id"],
                "evidence_matches": matches,
                "gold_evidence_ids": gold_evidence_ids,
                "gold_taskframe_ids": sorted(gold_taskframes),
                "gold_pcf_ids": gold_pcfs,
                "gold_fact_ids": gold_facts,
                "gold_relation_types": gold_relations,
                "gold_path": gold_path,
                "min_hops": min_hops,
                "expected_behavior": normalize_text(row.get("expected_behavior")),
                "source_answerable": _optional_bool(row.get("source_answerable")),
                "ontology_answerable": _optional_bool(row.get("ontology_answerable")),
                "graph_structure_required": _optional_bool(
                    row.get("graph_structure_required")
                ),
            }
        )
    report = {
        "qa_count": len(qa_rows),
        "evidence_item_count": total_items,
        "matched_evidence_item_count": matched_items,
        "fuzzy_match_count": fuzzy_items,
        "explicit_gold_evidence_count": explicit_gold_items,
        "qa_with_explicit_gold_evidence": qa_with_explicit_gold,
        "evidence_item_alignment_rate": matched_items / total_items if total_items else 0.0,
        "qa_with_any_aligned_evidence": sum(
            bool(item["gold_evidence_ids"]) for item in aligned
        ),
        "qa_with_inferred_taskframe": sum(
            bool(item["gold_taskframe_ids"]) for item in aligned
        ),
        "qa_with_inferred_pcf": sum(bool(item["gold_pcf_ids"]) for item in aligned),
        "caveat": (
            "TaskFrame/PCF gold labels are inferred through the evaluated graph and measure "
            "internal retrieval consistency, not independently reviewed ontology correctness."
        ),
    }
    return aligned, report


def evaluate_retrieval(
    retrieval_rows: Sequence[Mapping[str, Any]],
    gold_rows: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    gold_by_qid = {row["qid"]: row for row in gold_rows}
    per_question: list[dict[str, Any]] = []
    for row in retrieval_rows:
        gold = gold_by_qid[row["qid"]]
        predicted_evidence = [item["evidence_id"] for item in row.get("evidence", [])]
        predicted_frames = [item["id"] for item in row.get("taskframe_candidates", [])]
        predicted_pcfs = [item["id"] for item in row.get("pcf_candidates", [])]
        predicted_facts = [item["id"] for item in row.get("fact_candidates", [])]
        gold_evidence = set(gold["gold_evidence_ids"])
        gold_frames = set(gold["gold_taskframe_ids"])
        gold_pcfs = set(gold["gold_pcf_ids"])
        gold_facts = set(gold.get("gold_fact_ids", []))
        graph_required = gold.get("graph_structure_required") is True
        ranks = [
            index + 1
            for index, evidence_id in enumerate(predicted_evidence)
            if evidence_id in gold_evidence
        ]
        chain_components: list[bool] = []
        if graph_required:
            if gold_evidence:
                chain_components.append(gold_evidence.issubset(set(predicted_evidence[:5])))
            if gold_frames:
                chain_components.append(gold_frames.issubset(set(predicted_frames[:3])))
            if gold_facts:
                chain_components.append(gold_facts.issubset(set(predicted_facts[:12])))
            if gold_pcfs:
                chain_components.append(gold_pcfs.issubset(set(predicted_pcfs[:3])))
        per_question.append(
            {
                "qid": row["qid"],
                "method": row["method"],
                "condition": row["condition"],
                "gold_evidence_count": len(gold_evidence),
                "evidence_hit_at_1": (
                    float(bool(predicted_evidence and predicted_evidence[0] in gold_evidence))
                    if gold_evidence
                    else None
                ),
                "evidence_hit_at_5": float(bool(ranks)) if gold_evidence else None,
                "evidence_recall_at_5": (
                    len(gold_evidence & set(predicted_evidence[:5])) / len(gold_evidence)
                    if gold_evidence
                    else None
                ),
                "complete_evidence_set_at_5": (
                    float(gold_evidence.issubset(set(predicted_evidence[:5])))
                    if gold_evidence
                    else None
                ),
                "evidence_mrr": (1.0 / min(ranks)) if ranks else (0.0 if gold_evidence else None),
                "taskframe_recall_at_3": (
                    len(gold_frames & set(predicted_frames[:3])) / len(gold_frames)
                    if gold_frames and row["method"] not in EVIDENCE_ONLY_METHODS
                    else None
                ),
                "fact_recall_at_12": (
                    len(gold_facts & set(predicted_facts[:12])) / len(gold_facts)
                    if gold_facts
                    else None
                ),
                "complete_gold_node_chain": (
                    float(all(chain_components)) if chain_components else None
                ),
                "pcf_recall_at_3": (
                    len(gold_pcfs & set(predicted_pcfs[:3])) / len(gold_pcfs)
                    if gold_pcfs and row["method"] not in EVIDENCE_ONLY_METHODS
                    else None
                ),
                "status": row.get("status"),
            }
        )

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in per_question:
        grouped[(row["method"], row["condition"])].append(row)
    metric_names = (
        "evidence_hit_at_1",
        "evidence_hit_at_5",
        "evidence_recall_at_5",
        "complete_evidence_set_at_5",
        "evidence_mrr",
        "taskframe_recall_at_3",
        "fact_recall_at_12",
        "pcf_recall_at_3",
        "complete_gold_node_chain",
    )
    summary: list[dict[str, Any]] = []
    for (method, condition), rows in sorted(grouped.items()):
        output: dict[str, Any] = {
            "method": method,
            "condition": condition,
            "n": len(rows),
            "no_context_rate": sum(row["status"] == "NO_CONTEXT" for row in rows) / len(rows),
        }
        for metric in metric_names:
            values = [float(row[metric]) for row in rows if row[metric] is not None]
            output[metric] = statistics.fmean(values) if values else None
            output[f"{metric}_n"] = len(values)
        summary.append(output)
    return per_question, summary


class KiwiTokenizer:
    def __init__(self, kiwi: Kiwi):
        self.kiwi = kiwi

    def tokenize(self, text: str) -> list[str]:
        return [token.form for token in self.kiwi.tokenize(text) if token.form]


def _percentile(values: Sequence[float], value: float) -> float:
    return float(np.quantile(np.asarray(values, dtype=np.float64), value))


def evaluate_answers(
    *,
    answer_rows: Sequence[Mapping[str, Any]],
    qa_rows: Sequence[Mapping[str, Any]],
    output_dir: Path,
    config: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    reference_by_qid = {row["qa_id"]: normalize_text(row["answer"]) for row in qa_rows}
    group_by_qid = {
        row["qa_id"]: normalize_text(row.get("section_no")) or row["qa_id"]
        for row in qa_rows
    }
    expected_qids = set(reference_by_qid)
    grouped_answers: dict[tuple[str, str], dict[str, Mapping[str, Any]]] = defaultdict(dict)
    for row in answer_rows:
        key = (row["method"], row["condition"])
        if row["qid"] in grouped_answers[key]:
            raise ValueError(f"Duplicate answer output for {key}/{row['qid']}")
        grouped_answers[key][row["qid"]] = row

    kiwi = Kiwi()
    tokenizer = KiwiTokenizer(kiwi)
    rouge = RougeScorer(
        ["rouge1", "rouge2", "rougeL"],
        use_stemmer=False,
        tokenizer=tokenizer,
    )
    bleu = BLEU(
        max_ngram_order=4,
        tokenize="none",
        lowercase=False,
        smooth_method="exp",
        effective_order=False,
    )

    per_question: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    ordered_keys = sorted(grouped_answers)
    for method, condition in ordered_keys:
        rows = grouped_answers[(method, condition)]
        missing = sorted(expected_qids - set(rows))
        for qid in missing:
            failures.append(
                {"qid": qid, "method": method, "condition": condition, "reason": "missing_prediction"}
            )
        for qid in sorted(expected_qids):
            source = rows.get(qid, {})
            reference = reference_by_qid[qid]
            prediction = normalize_text(source.get("prediction_answer", ""))
            score = rouge.score(reference, prediction) if prediction else None
            per_question.append(
                {
                    "qid": qid,
                    "group_id": group_by_qid[qid],
                    "method": method,
                    "condition": condition,
                    "reference_answer": reference,
                    "prediction_answer": prediction,
                    "reference_tokens": " ".join(tokenizer.tokenize(reference)),
                    "prediction_tokens": " ".join(tokenizer.tokenize(prediction)),
                    "rouge1_f1": score["rouge1"].fmeasure if score else 0.0,
                    "rouge2_f1": score["rouge2"].fmeasure if score else 0.0,
                    "rougeL_f1": score["rougeL"].fmeasure if score else 0.0,
                    "bertscore_f1": 0.0,
                    "status": source.get("status", "MISSING"),
                    "api_failed": bool(source.get("api_failed", not bool(source))),
                }
            )

    bert_config = config["evaluation"]
    model_id = bert_config["bertscore_model"]
    model_revision = ""
    local_model_path = model_id
    try:
        from huggingface_hub import model_info, snapshot_download
        from transformers import AutoTokenizer
        from bert_score import BERTScorer

        info = model_info(model_id)
        model_revision = info.sha
        local_model_path = snapshot_download(
            repo_id=model_id,
            revision=model_revision,
            allow_patterns=[
                "config.json",
                "model.safetensors",
                "sentencepiece.bpe.model",
                "tokenizer.json",
                "tokenizer_config.json",
            ],
        )
        hf_tokenizer = AutoTokenizer.from_pretrained(local_model_path, use_fast=False)
        overflow: list[dict[str, Any]] = []
        model_limit = min(int(hf_tokenizer.model_max_length), 100_000)
        for row in per_question:
            for field in ("reference_answer", "prediction_answer"):
                if not row[field]:
                    continue
                length = len(hf_tokenizer(row[field], add_special_tokens=True)["input_ids"])
                if length > model_limit:
                    overflow.append({"qid": row["qid"], "field": field, "tokens": length})
        if overflow:
            write_jsonl(output_dir / "answer_evaluation_failures.jsonl", failures + overflow)
            raise RuntimeError(f"BERTScore token length overflow: {overflow[:5]}")

        scorer = BERTScorer(
            model_type=local_model_path,
            num_layers=int(bert_config["bertscore_layers"]),
            batch_size=int(bert_config["bertscore_batch_size"]),
            nthreads=4,
            all_layers=False,
            idf=False,
            device=str(bert_config["bertscore_device"]),
            lang="ko",
            rescale_with_baseline=False,
            use_fast_tokenizer=False,
        )
        nonempty_indices = [
            index for index, row in enumerate(per_question) if row["prediction_answer"]
        ]
        candidates = [per_question[index]["prediction_answer"] for index in nonempty_indices]
        references = [per_question[index]["reference_answer"] for index in nonempty_indices]
        if candidates:
            _, _, f1 = scorer.score(candidates, references, batch_size=int(bert_config["bertscore_batch_size"]))
            for index, value in zip(nonempty_indices, f1.cpu().tolist()):
                per_question[index]["bertscore_f1"] = float(value)
    except Exception as exc:
        failures.append({"stage": "bertscore", "reason": f"{type(exc).__name__}: {exc}"})
        write_jsonl(output_dir / "answer_evaluation_failures.jsonl", failures)
        raise

    by_key: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in per_question:
        by_key[(row["method"], row["condition"])].append(row)

    summary: list[dict[str, Any]] = []
    for (method, condition), rows in sorted(by_key.items()):
        rows.sort(key=lambda item: item["qid"])
        result = bleu.corpus_score(
            [row["prediction_tokens"] for row in rows],
            [[row["reference_tokens"] for row in rows]],
        )
        summary.append(
            {
                "method": method,
                "condition": condition,
                "n": len(rows),
                "bleu4_kiwi": float(result.score),
                "rouge1_f1_kiwi": 100.0 * statistics.fmean(row["rouge1_f1"] for row in rows),
                "rouge2_f1_kiwi": 100.0 * statistics.fmean(row["rouge2_f1"] for row in rows),
                "rougeL_f1_kiwi": 100.0 * statistics.fmean(row["rougeL_f1"] for row in rows),
                "bertscore_f1_xlmr17": 100.0 * statistics.fmean(row["bertscore_f1"] for row in rows),
                "failure_rate": statistics.fmean(float(row["api_failed"]) for row in rows),
                "insufficient_rate": statistics.fmean(
                    float(row["status"] in {"INSUFFICIENT", "NO_CONTEXT"}) for row in rows
                ),
                "bleu_signature": str(bleu.get_signature()),
            }
        )

    bootstrap_iterations = int(config["evaluation"]["bootstrap_iterations"])
    rng = np.random.default_rng(int(config["random_seed"]))
    qids_by_group: dict[str, list[str]] = defaultdict(list)
    for qid, group in group_by_qid.items():
        qids_by_group[group].append(qid)
    groups = sorted(qids_by_group)
    row_lookup = {
        (row["method"], row["condition"], row["qid"]): row for row in per_question
    }
    # SacreBLEU corpus BLEU is recomputed for every bootstrap sample by summing
    # sentence-level sufficient statistics. This is mathematically identical to
    # re-tokenizing and calling corpus_score, but avoids 80,000 repeated parses.
    bleu_stats_lookup: dict[tuple[str, str, str], np.ndarray] = {}
    for row in per_question:
        stats = bleu._extract_corpus_statistics(
            [row["prediction_tokens"]], [[row["reference_tokens"]]]
        )[0]
        bleu_stats_lookup[(row["method"], row["condition"], row["qid"])] = np.asarray(
            stats, dtype=np.int64
        )
    distributions: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    metric_fields = {
        "rouge1_f1_kiwi": "rouge1_f1",
        "rouge2_f1_kiwi": "rouge2_f1",
        "rougeL_f1_kiwi": "rougeL_f1",
        "bertscore_f1_xlmr17": "bertscore_f1",
    }
    for _ in range(bootstrap_iterations):
        sampled_groups = rng.choice(groups, size=len(groups), replace=True)
        sampled_qids = [qid for group in sampled_groups for qid in qids_by_group[group]]
        for method, condition in by_key:
            sampled = [row_lookup[(method, condition, qid)] for qid in sampled_qids]
            aggregated_stats = np.sum(
                [bleu_stats_lookup[(method, condition, qid)] for qid in sampled_qids],
                axis=0,
            )
            bleu_value = bleu._compute_score_from_stats(
                aggregated_stats.astype(int).tolist()
            ).score
            distributions[(method, condition, "bleu4_kiwi")].append(float(bleu_value))
            for metric_name, field in metric_fields.items():
                value = 100.0 * statistics.fmean(row[field] for row in sampled)
                distributions[(method, condition, metric_name)].append(float(value))

    for row in summary:
        method, condition = row["method"], row["condition"]
        row["bootstrap_ci95"] = {}
        for metric in ("bleu4_kiwi", *metric_fields):
            values = distributions[(method, condition, metric)]
            row["bootstrap_ci95"][metric] = [
                _percentile(values, 0.025),
                _percentile(values, 0.975),
            ]

    comparisons: list[dict[str, Any]] = []
    for condition in sorted({key[1] for key in by_key}):
        available = {method for method, item_condition in by_key if item_condition == condition}
        for proposed_method, baseline in ANSWER_COMPARISON_PAIRS:
            if proposed_method not in available or baseline not in available:
                continue
            for metric in ("bleu4_kiwi", *metric_fields):
                proposed = distributions[(proposed_method, condition, metric)]
                other = distributions[(baseline, condition, metric)]
                differences = [left - right for left, right in zip(proposed, other)]
                comparisons.append(
                    {
                        "condition": condition,
                        "comparison": f"{proposed_method} - {baseline}",
                        "metric": metric,
                        "mean_bootstrap_difference": statistics.fmean(differences),
                        "ci95": [_percentile(differences, 0.025), _percentile(differences, 0.975)],
                        "probability_difference_gt_0": sum(value > 0 for value in differences)
                        / len(differences),
                    }
                )

    manifest = {
        "created_at": utc_now(),
        "python": platform.python_version(),
        "packages": {
            name: importlib.metadata.version(name)
            for name in (
                "kiwipiepy",
                "sacrebleu",
                "rouge-score",
                "bert-score",
                "transformers",
                "torch",
            )
        },
        "kiwi": {"version": importlib.metadata.version("kiwipiepy"), "user_dictionary": None},
        "bertscore": {
            "model": model_id,
            "resolved_revision": model_revision,
            "local_snapshot": str(local_model_path),
            "num_layers": int(bert_config["bertscore_layers"]),
            "device": bert_config["bertscore_device"],
            "idf": False,
            "rescale_with_baseline": False,
        },
        "bootstrap": {
            "iterations": bootstrap_iterations,
            "unit": "section_no",
            "group_count": len(groups),
            "seed": int(config["random_seed"]),
        },
        "reference_review_status_counts": dict(Counter(row.get("review_status", "") for row in qa_rows)),
        "protocol_deviation": (
            "All supplied references are used as frozen provisional references, but their "
            "CSV review_status is pending; human review is still required before a final Gold claim."
        ),
    }
    write_jsonl(output_dir / "answer_metric_per_question.jsonl", per_question)
    write_json(output_dir / "answer_metric_summary.json", {"groups": summary, "comparisons": comparisons})
    write_json(output_dir / "answer_metric_manifest.json", manifest)
    write_jsonl(output_dir / "answer_evaluation_failures.jsonl", failures)
    return summary, {"manifest": manifest, "comparisons": comparisons, "failures": failures}


def write_metric_table(path: Path, answer_summary: Sequence[Mapping[str, Any]]) -> None:
    labels = {
        "B0_VANILLA_DENSE_RAG": "B0 일반 Dense RAG",
        "B0_EVIDENCE_HYBRID": "B0 원문 Hybrid RAG",
        "P0_QPA": "P0 QPA 전체",
        "A1_FIXED_PROPERTIES": "A1 고정 속성 가중치",
        "A2_NO_GAP_ADAPTATION": "A2 결손 대응 제거",
        "V2_EVIDENCE_GRAPH_LATE_FUSION": "V2 Evidence-first Graph Late Fusion",
        "P1_QPA_CROSS_ENCODER_MMR": "P1 P0 + Cross-Encoder/MMR",
        "P1A_QPA_ASPECT_CROSS_ENCODER_MMR": "P1-A P1 + 질문 Aspect 분석",
        P1B_PROFILE_FREE: "PCF Path (Aspect/Subgraph 제거)",
        P1G_PCF_GROUNDED: "P1-G PCF-Grounded Aspect Routing",
        P1G_PROFILE_FREE: "PCF+Aspect (Subgraph 제거)",
        P1P_PARS: "P1-PARS + Query Profile (legacy)",
        P1P_PARS_PROFILE_FREE: "PARS-KG-RAG (final)",
        P1U_TFIDF: "P1-U TF-IDF 질문 Aspect",
        P1U_EMBEDRANK: "P1-U EmbedRank 질문 Aspect",
        P1U_EMBEDRANK_MMR: "P1-U EmbedRank+MMR 질문 Aspect",
        P1U_ATTENTION_SEEKER: "P1-U Attention-Seeker 질문 Aspect",
    }
    method_order = {method: index for index, method in enumerate(labels)}
    by_condition: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in answer_summary:
        by_condition[row["condition"]].append(row)
    lines = ["# Answer metric table", ""]
    for condition, rows in sorted(by_condition.items()):
        lines.extend(
            [
                f"## {condition}",
                "",
                "| 방법 | BLEU-4 (Kiwi) ↑ | ROUGE-1 F1 ↑ | ROUGE-2 F1 ↑ | ROUGE-L F1 ↑ | BERTScore F1 ↑ | 실패율 |",
                "|---|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for row in sorted(
            rows,
            key=lambda item: (method_order.get(item["method"], len(method_order)), item["method"]),
        ):
            lines.append(
                f"| {labels.get(row['method'], row['method'])} | {row['bleu4_kiwi']:.2f} | "
                f"{row['rouge1_f1_kiwi']:.2f} | {row['rouge2_f1_kiwi']:.2f} | "
                f"{row['rougeL_f1_kiwi']:.2f} | {row['bertscore_f1_xlmr17']:.2f} | "
                f"{100 * row['failure_rate']:.2f}% |"
            )
        lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
