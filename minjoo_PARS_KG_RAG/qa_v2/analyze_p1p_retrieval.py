#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from kg_rag.evaluation import evaluate_retrieval


METHODS = (
    "B0_VANILLA_DENSE_RAG",
    "P1_QPA_CROSS_ENCODER_MMR",
    "P1A_QPA_ASPECT_CROSS_ENCODER_MMR",
    "P1G_PCF_GROUNDED_ASPECT_CROSS_ENCODER_MMR",
    "P1B_PCF_FIRST_PROFILE_FREE_CROSS_ENCODER_MMR",
    "P1G_PCF_GROUNDED_ASPECT_PROFILE_FREE_MMR",
    "P1P_PCF_ANCHORED_PROPERTY_RELATIONAL_SUBGRAPH_MMR",
    "P1P_PCF_ANCHORED_PROPERTY_RELATIONAL_SUBGRAPH_PROFILE_FREE_MMR",
)
METHOD_LABELS = {
    "B0_VANILLA_DENSE_RAG": "Dense RAG",
    "P1_QPA_CROSS_ENCODER_MMR": "PCF-first / Aspect X",
    "P1A_QPA_ASPECT_CROSS_ENCODER_MMR": "Prompt Aspect",
    "P1G_PCF_GROUNDED_ASPECT_CROSS_ENCODER_MMR": "P1-G",
    "P1B_PCF_FIRST_PROFILE_FREE_CROSS_ENCODER_MMR": "PF-Base (Aspect/PARS X)",
    "P1G_PCF_GROUNDED_ASPECT_PROFILE_FREE_MMR": "PF-Direct Aspect (PARS X)",
    "P1P_PCF_ANCHORED_PROPERTY_RELATIONAL_SUBGRAPH_MMR": "P1-PARS + Query Profile (legacy)",
    "P1P_PCF_ANCHORED_PROPERTY_RELATIONAL_SUBGRAPH_PROFILE_FREE_MMR": "P1-PARS Profile-free (final)",
}
P1P = "P1P_PCF_ANCHORED_PROPERTY_RELATIONAL_SUBGRAPH_PROFILE_FREE_MMR"
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
    *((P1P, method) for method in METHODS if method != P1P),
    (
        "P1G_PCF_GROUNDED_ASPECT_PROFILE_FREE_MMR",
        "P1B_PCF_FIRST_PROFILE_FREE_CROSS_ENCODER_MMR",
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze the P1-PARS Profile-free run")
    parser.add_argument("--qa-csv", type=Path, required=True)
    parser.add_argument("--metrics-jsonl", type=Path)
    parser.add_argument("--retrieval-jsonl", type=Path)
    parser.add_argument("--gold-jsonl", type=Path)
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


def mean(values: Sequence[float]) -> float | None:
    return float(np.mean(np.asarray(values, dtype=np.float64))) if values else None


def summarize(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_method: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        by_method[str(row["method"])].append(row)
    output: list[dict[str, Any]] = []
    for method in METHODS:
        method_rows = by_method.get(method, [])
        if not method_rows:
            continue
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
    if args.retrieval_jsonl or args.gold_jsonl:
        if not args.retrieval_jsonl or not args.gold_jsonl:
            raise ValueError("--retrieval-jsonl and --gold-jsonl must be provided together")
        metric_rows, _ = evaluate_retrieval(
            read_jsonl(args.retrieval_jsonl),
            read_jsonl(args.gold_jsonl),
        )
    elif args.metrics_jsonl:
        metric_rows = read_jsonl(args.metrics_jsonl)
    else:
        raise ValueError(
            "Provide --metrics-jsonl or both --retrieval-jsonl and --gold-jsonl"
        )
    metric_rows = [row for row in metric_rows if row.get("method") in METHODS]
    observed_methods = [
        method
        for method in METHODS
        if any(row.get("method") == method for row in metric_rows)
    ]
    unknown = sorted({row["qid"] for row in metric_rows} - set(qa_by_qid))
    if unknown:
        raise ValueError(f"Metric rows contain unknown qids: {unknown[:10]}")

    source_development_qids = {"JAIJE1-QA-0001", "JAIJE1-QA-0002"}
    predicates: list[tuple[str, Callable[[str], bool]]] = [
        (
            "official_combined_178",
            lambda qid: (
                (qid.startswith("JAIJE1-") and qid not in source_development_qids)
                or qa_by_qid[qid].get("split") == "synthetic_holdout"
            ),
        ),
        (
            "source_control_148",
            lambda qid: qid.startswith("JAIJE1-")
            and qid not in source_development_qids,
        ),
        (
            "synthetic_holdout_30",
            lambda qid: qa_by_qid[qid].get("split") == "synthetic_holdout",
        ),
        (
            "configured_development_32",
            lambda qid: qid in source_development_qids
            or qa_by_qid[qid].get("split") == "synthetic_tuning",
        ),
        ("full_exploratory_210", lambda qid: True),
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
            "methods": observed_methods,
            "bootstrap_iterations": args.bootstrap_iterations,
            "bootstrap_unit": "qid",
            "seed": args.seed,
            "selection_warning": (
                "All partitions have been inspected in prior development; results are "
                "exploratory rather than confirmatory."
            ),
        },
        "groups": groups,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = ["# P1-PARS Profile-free retrieval analysis", ""]
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
        lines.extend(
            ["", "P1-PARS paired bootstrap differences are stored in the JSON artifact.", ""]
        )
    args.output_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")


if __name__ == "__main__":
    main()
