#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from kg_rag.common import normalize_text
from kg_rag.retrieval import GraphIndex
from run_experiment import build_backend, resolve_config


BASE_METHOD = "P1_QPA_CROSS_ENCODER_MMR"
ASPECT_METHOD = "P1U_ATTENTION_SEEKER_ASPECT_CROSS_ENCODER_MMR"
METRICS = (
    "evidence_hit_at_1",
    "evidence_hit_at_5",
    "evidence_recall_at_5",
    "complete_evidence_set_at_5",
    "evidence_mrr",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Replay diagnostic candidate scores to tune Aspect reranking"
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--bootstrap-iterations", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20260921)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


@dataclass(frozen=True)
class ReplayConfig:
    aspect_weight: float
    mmr_lambda: float
    base_quota: int
    merge_mode: str
    replacement_margin: float

    @property
    def name(self) -> str:
        return (
            f"aw={self.aspect_weight:.2f}|mmr={self.mmr_lambda:.2f}|"
            f"quota={self.base_quota}|merge={self.merge_mode}|"
            f"margin={self.replacement_margin:.3f}"
        )


def candidate_scores(
    diagnostics: Sequence[Mapping[str, Any]],
    *,
    aspect_weight: float,
    rrf_k: float = 60.0,
) -> dict[str, float]:
    output: dict[str, float] = {}
    for item in diagnostics:
        evidence_id = str(item["evidence_id"])
        score = 1.0 / (rrf_k + int(item["p0_rank"]))
        score += 2.0 / (rrf_k + int(item["cross_encoder_rank"]))
        aspect_rank = item.get("aspect_cross_encoder_rank")
        if aspect_rank is not None:
            score += aspect_weight / (rrf_k + int(aspect_rank))
        output[evidence_id] = score
    return output


def replay_selection(
    diagnostics: Sequence[Mapping[str, Any]],
    *,
    scores: Mapping[str, float],
    text_matrix: np.ndarray,
    positions: Mapping[str, int],
    evidence_top_k: int,
    mmr_lambda: float,
    base_quota: int,
) -> list[str]:
    by_id = {str(item["evidence_id"]): item for item in diagnostics}
    values = list(scores.values())
    minimum = min(values) if values else 0.0
    maximum = max(values) if values else 0.0
    denominator = maximum - minimum
    relevance = {
        evidence_id: (
            (score - minimum) / denominator if denominator > 0 else 1.0
        )
        for evidence_id, score in scores.items()
    }
    base_ranked = sorted(
        (
            (evidence_id, int(item["base_path_rank"]))
            for evidence_id, item in by_id.items()
            if item.get("base_path_rank") is not None
        ),
        key=lambda value: (value[1], value[0]),
    )
    selected = [evidence_id for evidence_id, _ in base_ranked[:base_quota]]
    candidate_ids = sorted(by_id)
    while len(selected) < evidence_top_k and len(selected) < len(candidate_ids):
        best_id = ""
        best_key: tuple[float, float, float, str] | None = None
        for evidence_id in candidate_ids:
            if evidence_id in selected:
                continue
            redundancy = 0.0
            candidate_vector = text_matrix[positions[evidence_id]]
            candidate_section = normalize_text(by_id[evidence_id].get("section_path"))
            for selected_id in selected:
                similarity = max(
                    0.0,
                    float(candidate_vector @ text_matrix[positions[selected_id]]),
                )
                redundancy = max(redundancy, similarity)
                selected_section = normalize_text(
                    by_id[selected_id].get("section_path")
                )
                if candidate_section and candidate_section == selected_section:
                    redundancy = 1.0
            mmr_score = mmr_lambda * relevance[evidence_id] - (
                1.0 - mmr_lambda
            ) * redundancy
            key = (
                mmr_score,
                relevance[evidence_id],
                float(by_id[evidence_id]["cross_encoder_score"]),
                evidence_id,
            )
            if best_key is None or key > best_key:
                best_key = key
                best_id = evidence_id
        if not best_id:
            break
        selected.append(best_id)
    return sorted(selected, key=lambda evidence_id: (-scores[evidence_id], evidence_id))


def merge_with_base(
    aspect_ids: Sequence[str],
    base_ids: Sequence[str],
    scores: Mapping[str, float],
    *,
    mode: str,
    replacement_margin: float,
    evidence_top_k: int,
) -> list[str]:
    aspect = list(aspect_ids[:evidence_top_k])
    base = list(base_ids[:evidence_top_k])
    if mode == "raw":
        return aspect
    if mode == "pin_top1":
        if not base:
            return aspect
        output = [base[0], *(item for item in aspect if item != base[0])]
        for item in base:
            if len(output) >= evidence_top_k:
                break
            if item not in output:
                output.append(item)
        return output[:evidence_top_k]
    if mode not in {"conservative_1", "conservative_2"}:
        raise ValueError(f"Unknown merge mode: {mode}")
    replacements = int(mode.rsplit("_", 1)[-1])
    output = list(base)
    novel = [item for item in aspect if item not in output]
    for candidate in novel:
        if replacements <= 0 or not output:
            break
        replaceable = output[1:] if len(output) > 1 else []
        if not replaceable:
            break
        weakest = min(
            replaceable,
            key=lambda evidence_id: (scores.get(evidence_id, -1.0), evidence_id),
        )
        if scores.get(candidate, -1.0) < scores.get(weakest, -1.0) + replacement_margin:
            continue
        output[output.index(weakest)] = candidate
        replacements -= 1
    if output:
        pinned = output[0]
        rest = sorted(
            output[1:],
            key=lambda evidence_id: (-scores.get(evidence_id, -1.0), evidence_id),
        )
        output = [pinned, *rest]
    return output[:evidence_top_k]


def evidence_metrics(selected: Sequence[str], gold: Sequence[str]) -> dict[str, float]:
    gold_set = set(gold)
    retrieved = list(selected)
    overlap = gold_set & set(retrieved)
    reciprocal_rank = 0.0
    for rank, evidence_id in enumerate(retrieved, 1):
        if evidence_id in gold_set:
            reciprocal_rank = 1.0 / rank
            break
    return {
        "evidence_hit_at_1": float(bool(retrieved and retrieved[0] in gold_set)),
        "evidence_hit_at_5": float(bool(overlap)),
        "evidence_recall_at_5": len(overlap) / len(gold_set),
        "complete_evidence_set_at_5": float(gold_set.issubset(set(retrieved))),
        "evidence_mrr": reciprocal_rank,
    }


def paired_summary(
    deltas: Mapping[str, Sequence[float]],
    *,
    iterations: int,
    seed: int,
) -> dict[str, Any]:
    output: dict[str, Any] = {}
    rng = np.random.default_rng(seed)
    for index, metric in enumerate(METRICS):
        values = np.asarray(deltas[metric], dtype=np.float64)
        local_rng = np.random.default_rng(rng.integers(0, 2**32 - 1) + index)
        indices = local_rng.integers(0, len(values), size=(iterations, len(values)))
        sampled = values[indices].mean(axis=1)
        output[metric] = {
            "n": len(values),
            "difference": float(values.mean()),
            "ci95": [
                float(np.quantile(sampled, 0.025)),
                float(np.quantile(sampled, 0.975)),
            ],
            "probability_gt_0": float(np.mean(sampled > 0.0)),
        }
    return output


def main() -> None:
    args = parse_args()
    if args.bootstrap_iterations < 1:
        raise ValueError("bootstrap-iterations must be positive")
    retrieval = read_jsonl(args.run_dir / "02_retrieval.jsonl")
    gold_rows = read_jsonl(args.run_dir / "03_aligned_gold.jsonl")
    gold = {
        str(row["qid"]): list(row.get("gold_evidence_ids", []))
        for row in gold_rows
        if row.get("gold_evidence_ids")
    }
    rows = {(str(row["qid"]), str(row["method"])): row for row in retrieval}
    config = resolve_config(args.config)
    snapshot = json.loads(
        (args.run_dir / "00_graph_snapshot.json").read_text(encoding="utf-8")
    )
    backend = build_backend(config)
    graph = GraphIndex(
        snapshot,
        backend,
        embedding_batch_size=int(config["retrieval"]["embedding_batch_size"]),
    )
    evidence_index = graph.indices["evidence"]
    positions = {value: index for index, value in enumerate(evidence_index.ids)}
    text_matrix = evidence_index.matrices["text"]
    evidence_top_k = int(config["retrieval"]["evidence_top_k"])

    grid = [
        ReplayConfig(weight, mmr, quota, merge, margin)
        for weight in (0.25, 0.50, 0.75, 1.00, 1.50, 2.00)
        for mmr in (0.85, 0.90, 0.95, 1.00)
        for quota in (1, 2)
        for merge in ("raw", "pin_top1", "conservative_1", "conservative_2")
        for margin in ((0.0, 0.0005) if merge.startswith("conservative") else (0.0,))
    ]
    results: list[dict[str, Any]] = []
    exact_replay_checked = False
    for option in grid:
        deltas = {metric: [] for metric in METRICS}
        method_values = {metric: [] for metric in METRICS}
        changed = 0
        for qid, gold_ids in gold.items():
            base_row = rows[(qid, BASE_METHOD)]
            aspect_row = rows[(qid, ASPECT_METHOD)]
            base_ids = [item["evidence_id"] for item in base_row.get("evidence", [])]
            diagnostics = aspect_row.get("telemetry", {}).get("late_fusion", {}).get(
                "candidate_diagnostics", []
            )
            if not diagnostics or not any(
                item.get("aspect_cross_encoder_rank") is not None
                for item in diagnostics
            ):
                selected = base_ids
            else:
                scores = candidate_scores(
                    diagnostics,
                    aspect_weight=option.aspect_weight,
                )
                replayed = replay_selection(
                    diagnostics,
                    scores=scores,
                    text_matrix=text_matrix,
                    positions=positions,
                    evidence_top_k=evidence_top_k,
                    mmr_lambda=option.mmr_lambda,
                    base_quota=option.base_quota,
                )
                selected = merge_with_base(
                    replayed,
                    base_ids,
                    scores,
                    mode=option.merge_mode,
                    replacement_margin=option.replacement_margin,
                    evidence_top_k=evidence_top_k,
                )
                if (
                    not exact_replay_checked
                    and option.aspect_weight == 0.75
                    and option.mmr_lambda == 0.90
                    and option.base_quota == 2
                    and option.merge_mode == "raw"
                ):
                    actual = [
                        item["evidence_id"]
                        for item in aspect_row.get("evidence", [])
                    ]
                    if selected != actual:
                        raise AssertionError(
                            f"Replay mismatch for {qid}: {selected} != {actual}"
                        )
            changed += selected != base_ids
            baseline = evidence_metrics(base_ids, gold_ids)
            proposed = evidence_metrics(selected, gold_ids)
            for metric in METRICS:
                method_values[metric].append(proposed[metric])
                deltas[metric].append(proposed[metric] - baseline[metric])
        if (
            option.aspect_weight == 0.75
            and option.mmr_lambda == 0.90
            and option.base_quota == 2
            and option.merge_mode == "raw"
        ):
            exact_replay_checked = True
        means = {metric: float(np.mean(values)) for metric, values in method_values.items()}
        mean_delta = {metric: float(np.mean(values)) for metric, values in deltas.items()}
        objective = (
            1.5 * mean_delta["evidence_recall_at_5"]
            + mean_delta["evidence_hit_at_5"]
            + mean_delta["complete_evidence_set_at_5"]
            + mean_delta["evidence_mrr"]
            + 2.0 * min(0.0, mean_delta["evidence_hit_at_1"])
        )
        results.append(
            {
                "config": option.__dict__,
                "name": option.name,
                "changed_qids": changed,
                "means": means,
                "deltas_vs_p1": mean_delta,
                "objective": objective,
            }
        )
    if not exact_replay_checked:
        raise AssertionError("The current online configuration was not replay-validated")
    results.sort(
        key=lambda item: (
            item["objective"],
            item["deltas_vs_p1"]["evidence_recall_at_5"],
            item["deltas_vs_p1"]["evidence_mrr"],
        ),
        reverse=True,
    )
    finalists = results[:20]
    for index, item in enumerate(finalists):
        option = ReplayConfig(**item["config"])
        deltas = {metric: [] for metric in METRICS}
        for qid, gold_ids in gold.items():
            base_row = rows[(qid, BASE_METHOD)]
            aspect_row = rows[(qid, ASPECT_METHOD)]
            base_ids = [value["evidence_id"] for value in base_row.get("evidence", [])]
            diagnostics = aspect_row.get("telemetry", {}).get("late_fusion", {}).get(
                "candidate_diagnostics", []
            )
            if diagnostics and any(
                value.get("aspect_cross_encoder_rank") is not None
                for value in diagnostics
            ):
                scores = candidate_scores(diagnostics, aspect_weight=option.aspect_weight)
                selected = replay_selection(
                    diagnostics,
                    scores=scores,
                    text_matrix=text_matrix,
                    positions=positions,
                    evidence_top_k=evidence_top_k,
                    mmr_lambda=option.mmr_lambda,
                    base_quota=option.base_quota,
                )
                selected = merge_with_base(
                    selected,
                    base_ids,
                    scores,
                    mode=option.merge_mode,
                    replacement_margin=option.replacement_margin,
                    evidence_top_k=evidence_top_k,
                )
            else:
                selected = base_ids
            baseline = evidence_metrics(base_ids, gold_ids)
            proposed = evidence_metrics(selected, gold_ids)
            for metric in METRICS:
                deltas[metric].append(proposed[metric] - baseline[metric])
        item["paired_bootstrap"] = paired_summary(
            deltas,
            iterations=args.bootstrap_iterations,
            seed=args.seed + index,
        )

    output = {
        "status": "exploratory_development_only",
        "warning": (
            "The 210 questions are reused development data. Select one configuration, "
            "freeze it, and evaluate once on a newly generated untouched holdout."
        ),
        "grid_size": len(grid),
        "exact_replay_validated": exact_replay_checked,
        "objective": (
            "1.5*Recall@5 delta + Hit@5 delta + Complete@5 delta + MRR delta "
            "+ 2*negative Hit@1 delta"
        ),
        "top_results": finalists,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Aspect rerank replay tuning",
        "",
        "> Exploratory development-only sweep. These are not holdout results.",
        "",
        "| Rank | Config | Hit@1 Δ | Hit@5 Δ | Recall@5 Δ | Complete@5 Δ | MRR Δ |",
        "|---:|---|---:|---:|---:|---:|---:|",
    ]
    for rank, item in enumerate(finalists, 1):
        delta = item["deltas_vs_p1"]
        lines.append(
            f"| {rank} | `{item['name']}` | "
            f"{100*delta['evidence_hit_at_1']:+.2f} | "
            f"{100*delta['evidence_hit_at_5']:+.2f} | "
            f"{100*delta['evidence_recall_at_5']:+.2f} | "
            f"{100*delta['complete_evidence_set_at_5']:+.2f} | "
            f"{100*delta['evidence_mrr']:+.2f} |"
        )
    args.output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")


if __name__ == "__main__":
    main()
