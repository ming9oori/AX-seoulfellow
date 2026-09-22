#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np


METHODS = (
    "B0_VANILLA_DENSE_RAG",
    "P1_QPA_CROSS_ENCODER_MMR",
    "P1U_ATTENTION_SEEKER_ASPECT_CROSS_ENCODER_MMR",
    "P1A_QPA_ASPECT_CROSS_ENCODER_MMR",
)
LABELS = {
    METHODS[0]: "Dense RAG",
    METHODS[1]: "PCF-first / Aspect X",
    METHODS[2]: "PCF-first / local Aspect",
    METHODS[3]: "PCF-first / LLM Aspect",
}
METRICS = (
    "evidence_hit_at_1",
    "evidence_hit_at_5",
    "evidence_recall_at_5",
    "complete_evidence_set_at_5",
    "evidence_mrr",
    "taskframe_recall_at_3",
    "pcf_recall_at_3",
)
COMPARISONS = (
    (METHODS[2], METHODS[1]),
    (METHODS[3], METHODS[1]),
    (METHODS[2], METHODS[3]),
    (METHODS[2], METHODS[0]),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze the controlled local-vs-LLM Aspect extractor run"
    )
    parser.add_argument("--metrics-jsonl", type=Path, required=True)
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


def summarize(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["method"])].append(row)
    output = []
    for method in METHODS:
        item: dict[str, Any] = {
            "method": method,
            "question_rows": len(grouped[method]),
        }
        for metric in METRICS:
            values = [
                float(row[metric])
                for row in grouped[method]
                if row.get(metric) is not None
            ]
            item[metric] = float(np.mean(values)) if values else None
            item[f"{metric}_n"] = len(values)
        output.append(item)
    return output


def paired_bootstrap(
    rows: Sequence[Mapping[str, Any]], *, iterations: int, seed: int
) -> list[dict[str, Any]]:
    by_method_metric: dict[tuple[str, str], dict[str, float]] = defaultdict(dict)
    for row in rows:
        for metric in METRICS:
            if row.get(metric) is not None:
                by_method_metric[(str(row["method"]), metric)][str(row["qid"])] = float(
                    row[metric]
                )
    rng = np.random.default_rng(seed)
    output = []
    for comparison_index, (left, right) in enumerate(COMPARISONS):
        for metric_index, metric in enumerate(METRICS):
            left_values = by_method_metric[(left, metric)]
            right_values = by_method_metric[(right, metric)]
            qids = sorted(set(left_values) & set(right_values))
            if not qids:
                continue
            deltas = np.asarray(
                [left_values[qid] - right_values[qid] for qid in qids],
                dtype=np.float64,
            )
            local_rng = np.random.default_rng(
                rng.integers(0, 2**32 - 1)
                + 100 * comparison_index
                + metric_index
            )
            indices = local_rng.integers(0, len(deltas), size=(iterations, len(deltas)))
            sampled = deltas[indices].mean(axis=1)
            output.append(
                {
                    "left": left,
                    "right": right,
                    "comparison": f"{left} - {right}",
                    "metric": metric,
                    "n": len(qids),
                    "observed_difference": float(deltas.mean()),
                    "ci95": [
                        float(np.quantile(sampled, 0.025)),
                        float(np.quantile(sampled, 0.975)),
                    ],
                    "probability_difference_gt_0": float(np.mean(sampled > 0.0)),
                }
            )
    return output


def percent(value: float | None) -> str:
    return "-" if value is None else f"{100 * value:.2f}"


def main() -> None:
    args = parse_args()
    if args.bootstrap_iterations < 1:
        raise ValueError("bootstrap-iterations must be positive")
    rows = read_jsonl(args.metrics_jsonl)
    unknown = sorted({str(row["method"]) for row in rows} - set(METHODS))
    missing = sorted(set(METHODS) - {str(row["method"]) for row in rows})
    if unknown or missing:
        raise ValueError(f"Method mismatch; unknown={unknown}, missing={missing}")
    summary = summarize(rows)
    paired = paired_bootstrap(
        rows,
        iterations=args.bootstrap_iterations,
        seed=args.seed,
    )
    result = {
        "status": "development_source_control_comparison",
        "warning": (
            "The 150 source-derived questions have been inspected repeatedly and are "
            "not an untouched confirmatory holdout."
        ),
        "protocol": {
            "methods": list(METHODS),
            "bootstrap_iterations": args.bootstrap_iterations,
            "bootstrap_unit": "qid",
            "seed": args.seed,
            "common_question_only_applicability_gate": True,
            "identical_downstream_retrieval": True,
        },
        "summary": summary,
        "paired_bootstrap": paired,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# Controlled Aspect extractor comparison",
        "",
        "> Development/source-control comparison; not an untouched confirmatory holdout.",
        "",
        "| Method | Hit@1 | Hit@5 | Recall@5 | Complete@5 | MRR | TF@3 | PCF@3 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for item in summary:
        lines.append(
            f"| {LABELS[item['method']]} | "
            f"{percent(item['evidence_hit_at_1'])} | "
            f"{percent(item['evidence_hit_at_5'])} | "
            f"{percent(item['evidence_recall_at_5'])} | "
            f"{percent(item['complete_evidence_set_at_5'])} | "
            f"{percent(item['evidence_mrr'])} | "
            f"{percent(item['taskframe_recall_at_3'])} | "
            f"{percent(item['pcf_recall_at_3'])} |"
        )
    lines.extend(
        [
            "",
            "## Paired differences",
            "",
            "| Comparison | Metric | n | Delta (%p) | 95% CI (%p) | P(delta>0) |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for item in paired:
        lines.append(
            f"| {LABELS[item['left']]} - {LABELS[item['right']]} | "
            f"{item['metric']} | {item['n']} | "
            f"{100 * item['observed_difference']:+.2f} | "
            f"[{100 * item['ci95'][0]:+.2f}, {100 * item['ci95'][1]:+.2f}] | "
            f"{item['probability_difference_gt_0']:.4f} |"
        )
    args.output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")


if __name__ == "__main__":
    main()
