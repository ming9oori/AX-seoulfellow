#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np


METHODS = (
    "B0_VANILLA_DENSE_RAG",
    "P1_QPA_CROSS_ENCODER_MMR",
    "P1U_ATTENTION_SEEKER_ASPECT_CROSS_ENCODER_MMR",
)
METHOD_LABELS = {
    "B0_VANILLA_DENSE_RAG": "Dense RAG",
    "P1_QPA_CROSS_ENCODER_MMR": "PCF-first / Aspect X",
    "P1U_ATTENTION_SEEKER_ASPECT_CROSS_ENCODER_MMR": (
        "PCF-first / Attention-Seeker Aspect O"
    ),
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
    (
        "P1U_ATTENTION_SEEKER_ASPECT_CROSS_ENCODER_MMR",
        "P1_QPA_CROSS_ENCODER_MMR",
    ),
    (
        "P1U_ATTENTION_SEEKER_ASPECT_CROSS_ENCODER_MMR",
        "B0_VANILLA_DENSE_RAG",
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze the frozen three-way retrieval run")
    parser.add_argument("--qa-csv", type=Path, required=True)
    parser.add_argument("--metrics-jsonl", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--bootstrap-iterations", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20260920)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def mean(values: Sequence[float]) -> float | None:
    return float(np.mean(np.asarray(values, dtype=np.float64))) if values else None


def summarize(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_method: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        by_method[str(row["method"])].append(row)
    output: list[dict[str, Any]] = []
    for method in METHODS:
        method_rows = by_method.get(method, [])
        item: dict[str, Any] = {"method": method, "n": len(method_rows)}
        for metric in METRICS:
            values = [
                float(row[metric])
                for row in method_rows
                if row.get(metric) is not None
            ]
            item[metric] = mean(values)
            item[f"{metric}_n"] = len(values)
        output.append(item)
    return output


def paired_bootstrap(
    rows: Sequence[Mapping[str, Any]],
    *,
    iterations: int,
    seed: int,
) -> list[dict[str, Any]]:
    values: dict[tuple[str, str], dict[str, float]] = defaultdict(dict)
    for row in rows:
        qid = str(row["qid"])
        method = str(row["method"])
        for metric in METRICS:
            if row.get(metric) is not None:
                values[(method, metric)][qid] = float(row[metric])
    output: list[dict[str, Any]] = []
    rng = np.random.default_rng(seed)
    for left, right in COMPARISONS:
        for metric in METRICS:
            left_values = values[(left, metric)]
            right_values = values[(right, metric)]
            qids = sorted(set(left_values) & set(right_values))
            if not qids:
                continue
            deltas = np.asarray(
                [left_values[qid] - right_values[qid] for qid in qids],
                dtype=np.float64,
            )
            indices = rng.integers(0, len(deltas), size=(iterations, len(deltas)))
            sampled = deltas[indices].mean(axis=1)
            output.append(
                {
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


def format_value(value: Any) -> str:
    return "-" if value is None else f"{100.0 * float(value):.2f}"


def main() -> None:
    args = parse_args()
    if args.bootstrap_iterations < 1:
        raise ValueError("bootstrap-iterations must be positive")
    with args.qa_csv.open(encoding="utf-8-sig", newline="") as handle:
        qa_rows = list(csv.DictReader(handle))
    qa_by_qid = {row["qa_id"]: row for row in qa_rows}
    metric_rows = read_jsonl(args.metrics_jsonl)
    unknown = sorted({row["qid"] for row in metric_rows} - set(qa_by_qid))
    if unknown:
        raise ValueError(f"Metric rows contain unknown qids: {unknown[:10]}")

    source_development_qids = {"JAIJE1-QA-0001", "JAIJE1-QA-0002"}
    predicates: list[tuple[str, Callable[[str], bool]]] = [
        (
            "official_combined",
            lambda qid: (
                (qid.startswith("JAIJE1-") and qid not in source_development_qids)
                or qa_by_qid[qid].get("split") == "synthetic_holdout"
            ),
        ),
        (
            "source_control",
            lambda qid: qid.startswith("JAIJE1-")
            and qid not in source_development_qids,
        ),
        (
            "synthetic_holdout",
            lambda qid: qa_by_qid[qid].get("split") == "synthetic_holdout",
        ),
        ("full_development_210", lambda qid: True),
    ]
    holdout_strata = sorted(
        {
            row.get("query_stratum", "")
            for row in qa_rows
            if row.get("split") == "synthetic_holdout"
        }
        - {""}
    )
    predicates.extend(
        (
            f"synthetic_holdout/{stratum}",
            lambda qid, stratum=stratum: (
                qa_by_qid[qid].get("split") == "synthetic_holdout"
                and qa_by_qid[qid].get("query_stratum") == stratum
            ),
        )
        for stratum in holdout_strata
    )

    groups: list[dict[str, Any]] = []
    for group_index, (name, predicate) in enumerate(predicates):
        rows = [row for row in metric_rows if predicate(str(row["qid"]))]
        groups.append(
            {
                "group": name,
                "qid_count": len({str(row["qid"]) for row in rows}),
                "summary": summarize(rows),
                "paired_bootstrap": paired_bootstrap(
                    rows,
                    iterations=args.bootstrap_iterations,
                    seed=args.seed + group_index,
                ),
            }
        )

    result = {
        "protocol": {
            "methods": list(METHODS),
            "bootstrap_iterations": args.bootstrap_iterations,
            "bootstrap_unit": "qid",
            "seed": args.seed,
            "tuning_partition_excluded": True,
            "synthetic_holdout_definition": "even-numbered QAGEN ids, frozen before tuning results were inspected",
        },
        "groups": groups,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = ["# Three-way retrieval analysis", ""]
    for group in groups:
        lines.extend(
            [
                f"## {group['group']} (n={group['qid_count']})",
                "",
                "| Method | Hit@1 | Hit@5 | Recall@5 | Complete@5 | MRR | TF@3 | PCF@3 |",
                "|---|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for item in group["summary"]:
            lines.append(
                f"| {METHOD_LABELS[item['method']]} | "
                f"{format_value(item['evidence_hit_at_1'])} | "
                f"{format_value(item['evidence_hit_at_5'])} | "
                f"{format_value(item['evidence_recall_at_5'])} | "
                f"{format_value(item['complete_evidence_set_at_5'])} | "
                f"{format_value(item['evidence_mrr'])} | "
                f"{format_value(item['taskframe_recall_at_3'])} | "
                f"{format_value(item['pcf_recall_at_3'])} |"
            )
        lines.extend(["", "Paired bootstrap differences are stored in the JSON artifact.", ""])
    args.output_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")


if __name__ == "__main__":
    main()
