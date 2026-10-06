"""Frozen legacy answer metric algorithm with pinned revision and PARS-Cover pairs.
Copied without changing tokenization, BLEU smoothing, ROUGE or BERTScore scoring.
The caller encodes document+section (or document+qid fallback) in section_no.
Original evaluation.py is untouched; only model revision, pairs, true point delta,
and the bootstrap unit label differ from the legacy function.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence
import importlib.metadata
import platform
import statistics
import numpy as np
from kiwipiepy import Kiwi
from rouge_score.rouge_scorer import RougeScorer
from sacrebleu.metrics import BLEU
from .common import normalize_text, utc_now, write_json, write_jsonl
from .evaluation import KiwiTokenizer, _percentile
ANSWER_COMPARISON_PAIRS = (
    ("PARS_COVER", "LEGACY_PARS"),
    ("PARS_COVER", "PARS_COVER_NO_SET"),
    ("PARS_COVER", "PARS_COVER_TEXT_ONLY"),
)

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

        info = model_info(model_id, revision=bert_config["bertscore_revision"])
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
                        "point_difference": next(r[metric] for r in summary if r["method"] == proposed_method and r["condition"] == condition) - next(r[metric] for r in summary if r["method"] == baseline and r["condition"] == condition),
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
            "unit": "document_section_encoded_in_section_no",
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
