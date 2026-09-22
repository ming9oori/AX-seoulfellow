#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


QA_V2_DIR = Path(__file__).resolve().parent
if str(QA_V2_DIR) not in sys.path:
    sys.path.insert(0, str(QA_V2_DIR))

from paraphrase_pipeline import normalize_text, read_csv, read_jsonl, write_json  # noqa: E402


METRICS = (
    "evidence_hit_at_1",
    "evidence_hit_at_5",
    "evidence_recall_at_5",
    "complete_evidence_set_at_5",
    "evidence_mrr",
    "taskframe_recall_at_3",
    "fact_recall_at_12",
    "pcf_recall_at_3",
)
METHOD_COMPARISONS = (
    ("V2_EVIDENCE_GRAPH_LATE_FUSION", "B0_EVIDENCE_HYBRID"),
    ("V2_EVIDENCE_GRAPH_LATE_FUSION", "P0_QPA"),
    ("P0_QPA", "B0_EVIDENCE_HYBRID"),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize B0/P0/V2 retrieval on the paraphrase challenge"
    )
    parser.add_argument("--qa-csv", type=Path, required=True)
    parser.add_argument("--metrics-jsonl", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--bootstrap-iterations", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20260920)
    return parser.parse_args()


def _mean(values: Sequence[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _quantile(sorted_values: Sequence[float], probability: float) -> float:
    if not sorted_values:
        raise ValueError("Cannot compute a quantile of an empty sequence")
    position = (len(sorted_values) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return sorted_values[lower]
    weight = position - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def _bootstrap_ci(
    values: Sequence[float], *, iterations: int, seed: int
) -> tuple[float | None, float | None]:
    if not values:
        return None, None
    if len(values) == 1:
        return values[0], values[0]
    rng = random.Random(seed)
    count = len(values)
    samples = sorted(
        sum(values[rng.randrange(count)] for _ in range(count)) / count
        for _ in range(iterations)
    )
    return _quantile(samples, 0.025), _quantile(samples, 0.975)


def _subseed(seed: int, *parts: Any) -> int:
    payload = "|".join([str(seed), *(str(part) for part in parts)])
    return int(hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16], 16)


def _scopes(row: Mapping[str, Any]) -> Iterable[tuple[str, str]]:
    yield "all", "all"
    yield "variant_type", row["variant_type"]
    if row["variant_type"] != "original_control":
        yield "paraphrase_lexical_band", row["lexical_overlap_band"]


def _enrich_rows(
    qa_rows: Sequence[Mapping[str, Any]], metric_rows: Sequence[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    metadata = {normalize_text(row.get("qa_id")): row for row in qa_rows}
    if len(metadata) != len(qa_rows):
        raise ValueError("QA CSV has duplicate or empty qa_id values")
    unknown = sorted(
        {
            normalize_text(row.get("qid"))
            for row in metric_rows
            if normalize_text(row.get("qid")) not in metadata
        }
    )
    if unknown:
        raise ValueError(f"Metric rows reference unknown qids: {unknown[:10]}")
    enriched: list[dict[str, Any]] = []
    for row in metric_rows:
        qa = metadata[normalize_text(row.get("qid"))]
        enriched.append(
            {
                **row,
                "parent_qa_id": normalize_text(qa.get("parent_qa_id")),
                "variant_type": normalize_text(qa.get("variant_type")),
                "lexical_overlap_band": normalize_text(qa.get("lexical_overlap_band")),
                "lexical_overlap_score": float(qa.get("lexical_overlap_score", 0.0)),
            }
        )
    return enriched


def _aggregate(enriched: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in enriched:
        for scope, value in _scopes(row):
            groups[(row["method"], row["condition"], scope, value)].append(row)
    output: list[dict[str, Any]] = []
    for (method, condition, scope, value), rows in sorted(groups.items()):
        item: dict[str, Any] = {
            "method": method,
            "condition": condition,
            "scope": scope,
            "scope_value": value,
            "question_count": len(rows),
        }
        for metric in METRICS:
            values = [float(row[metric]) for row in rows if row.get(metric) is not None]
            item[metric] = _mean(values)
            item[f"{metric}_n"] = len(values)
        output.append(item)
    return output


def _pairwise_method_deltas(
    enriched: Sequence[Mapping[str, Any]], *, iterations: int, seed: int
) -> list[dict[str, Any]]:
    by_key = {
        (row["qid"], row["condition"], row["method"]): row for row in enriched
    }
    metadata_by_qid = {row["qid"]: row for row in enriched}
    conditions = sorted({row["condition"] for row in enriched})
    qids = sorted({row["qid"] for row in enriched})
    output: list[dict[str, Any]] = []
    for left, right in METHOD_COMPARISONS:
        for condition in conditions:
            for metric in METRICS:
                scoped: dict[tuple[str, str], list[float]] = defaultdict(list)
                for qid in qids:
                    left_row = by_key.get((qid, condition, left))
                    right_row = by_key.get((qid, condition, right))
                    if not left_row or not right_row:
                        continue
                    if left_row.get(metric) is None or right_row.get(metric) is None:
                        continue
                    delta = float(left_row[metric]) - float(right_row[metric])
                    for scope in _scopes(metadata_by_qid[qid]):
                        scoped[scope].append(delta)
                for (scope, scope_value), deltas in sorted(scoped.items()):
                    low, high = _bootstrap_ci(
                        deltas,
                        iterations=iterations,
                        seed=_subseed(seed, left, right, condition, metric, scope, scope_value),
                    )
                    output.append(
                        {
                            "left_method": left,
                            "right_method": right,
                            "condition": condition,
                            "metric": metric,
                            "scope": scope,
                            "scope_value": scope_value,
                            "n_pairs": len(deltas),
                            "mean_delta_left_minus_right": _mean(deltas),
                            "bootstrap_ci_95": [low, high],
                            "left_wins": sum(delta > 1e-12 for delta in deltas),
                            "ties": sum(abs(delta) <= 1e-12 for delta in deltas),
                            "left_losses": sum(delta < -1e-12 for delta in deltas),
                        }
                    )
    return output


def _paraphrase_degradation(
    enriched: Sequence[Mapping[str, Any]], *, iterations: int, seed: int
) -> list[dict[str, Any]]:
    by_key = {
        (row["qid"], row["condition"], row["method"]): row for row in enriched
    }
    grouped: dict[tuple[str, str, str, str, str], list[float]] = defaultdict(list)
    for row in enriched:
        if row["variant_type"] == "original_control":
            continue
        original = by_key.get((row["parent_qa_id"], row["condition"], row["method"]))
        if original is None:
            continue
        for metric in METRICS:
            if row.get(metric) is None or original.get(metric) is None:
                continue
            delta = float(row[metric]) - float(original[metric])
            grouped[(row["method"], row["condition"], metric, "variant_type", row["variant_type"])].append(delta)
            grouped[(row["method"], row["condition"], metric, "lexical_overlap_band", row["lexical_overlap_band"])].append(delta)
    output: list[dict[str, Any]] = []
    for (method, condition, metric, scope, scope_value), deltas in sorted(grouped.items()):
        low, high = _bootstrap_ci(
            deltas,
            iterations=iterations,
            seed=_subseed(seed, "degradation", method, condition, metric, scope, scope_value),
        )
        output.append(
            {
                "method": method,
                "condition": condition,
                "metric": metric,
                "scope": scope,
                "scope_value": scope_value,
                "n_pairs": len(deltas),
                "mean_delta_paraphrase_minus_original": _mean(deltas),
                "bootstrap_ci_95": [low, high],
                "improved": sum(delta > 1e-12 for delta in deltas),
                "unchanged": sum(abs(delta) <= 1e-12 for delta in deltas),
                "degraded": sum(delta < -1e-12 for delta in deltas),
            }
        )
    return output


def summarize(
    qa_rows: Sequence[Mapping[str, Any]],
    metric_rows: Sequence[Mapping[str, Any]],
    *,
    bootstrap_iterations: int = 10000,
    seed: int = 20260920,
) -> dict[str, Any]:
    if bootstrap_iterations < 1:
        raise ValueError("bootstrap_iterations must be positive")
    enriched = _enrich_rows(qa_rows, metric_rows)
    return {
        "created_at": utc_now(),
        "benchmark_status": "synthetic_development_only",
        "qa_count": len({row["qid"] for row in enriched}),
        "metric_row_count": len(enriched),
        "bootstrap_iterations": bootstrap_iterations,
        "seed": seed,
        "aggregates": _aggregate(enriched),
        "paired_method_deltas": _pairwise_method_deltas(
            enriched, iterations=bootstrap_iterations, seed=seed
        ),
        "paired_paraphrase_degradation": _paraphrase_degradation(
            enriched, iterations=bootstrap_iterations, seed=seed
        ),
        "interpretation_guardrail": (
            "Use this report to diagnose lexical robustness. It cannot establish real-user "
            "performance because all paraphrases descend from the source-derived control set."
        ),
    }


def _percent(value: Any) -> str:
    return "—" if value is None else f"{100 * float(value):.2f}"


def write_markdown(path: Path, report: Mapping[str, Any]) -> None:
    lines = [
        "# 패러프레이즈 검색 강건성 진단",
        "",
        "> 개발용 합성 진단셋 결과이며 실제 실무자 질문에 대한 일반 성능으로 해석하지 않는다.",
        "",
        "## 전체 검색 성능",
        "",
        "| 방법 | 조건 | n | Hit@1 | Hit@5 | Recall@5 | Complete@5 | MRR |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    overall = [
        row for row in report["aggregates"] if row["scope"] == "all"
    ]
    for row in overall:
        lines.append(
            f"| {row['method']} | {row['condition']} | {row['question_count']} | "
            f"{_percent(row['evidence_hit_at_1'])} | {_percent(row['evidence_hit_at_5'])} | "
            f"{_percent(row['evidence_recall_at_5'])} | "
            f"{_percent(row['complete_evidence_set_at_5'])} | {_percent(row['evidence_mrr'])} |"
        )
    lines.extend(
        [
            "",
            "## 패러프레이즈 어휘 중첩 구간별 Recall@5",
            "",
            "| 방법 | 조건 | 중첩 구간 | n | Recall@5 | Complete@5 | MRR |",
            "|---|---|---|---:|---:|---:|---:|",
        ]
    )
    bands = [
        row
        for row in report["aggregates"]
        if row["scope"] == "paraphrase_lexical_band"
    ]
    for row in bands:
        lines.append(
            f"| {row['method']} | {row['condition']} | {row['scope_value']} | "
            f"{row['question_count']} | {_percent(row['evidence_recall_at_5'])} | "
            f"{_percent(row['complete_evidence_set_at_5'])} | {_percent(row['evidence_mrr'])} |"
        )
    lines.extend(
        [
            "",
            "## V2 − B0 패러프레이즈 구간별 Recall@5",
            "",
            "| 조건 | 중첩 구간 | n | 평균 차이(%p) | 95% bootstrap CI(%p) | 승/무/패 |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    deltas = [
        row
        for row in report["paired_method_deltas"]
        if row["left_method"] == "V2_EVIDENCE_GRAPH_LATE_FUSION"
        and row["right_method"] == "B0_EVIDENCE_HYBRID"
        and row["metric"] == "evidence_recall_at_5"
        and row["scope"] == "paraphrase_lexical_band"
    ]
    for row in deltas:
        low, high = row["bootstrap_ci_95"]
        lines.append(
            f"| {row['condition']} | {row['scope_value']} | {row['n_pairs']} | "
            f"{100 * row['mean_delta_left_minus_right']:.2f} | "
            f"[{100 * low:.2f}, {100 * high:.2f}] | "
            f"{row['left_wins']}/{row['ties']}/{row['left_losses']} |"
        )
    lines.extend(
        [
            "",
            "## 해석 제한",
            "",
            "- 원질문과 Gold Evidence를 고정했으므로 표현 변화에 대한 검색 강건성만 진단한다.",
            "- V2 가중치 조정에는 사용할 수 있지만 최종 test 또는 실제 사용자 성능 근거로 쓰지 않는다.",
            "- 최종 주장은 독립적으로 수집한 Operational Set과 KG Challenge Set에서만 한다.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    report = summarize(
        read_csv(args.qa_csv),
        read_jsonl(args.metrics_jsonl),
        bootstrap_iterations=args.bootstrap_iterations,
        seed=args.seed,
    )
    write_json(args.output_json, report)
    write_markdown(args.output_md, report)
    print(f"OK: {args.output_json}")
    print(f"OK: {args.output_md}")


if __name__ == "__main__":
    main()
