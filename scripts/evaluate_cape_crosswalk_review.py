#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Evaluate expert-reviewed CAPE-KG NCS-PCF crosswalk candidates."""

import argparse
import csv
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
COMPLETED_STATUSES = {"completed", "reviewed", "adjudicated", "final"}
POSITIVE_DECISIONS = {"accepted", "accept", "yes", "y", "true"}
NEGATIVE_DECISIONS = {"rejected", "reject", "no", "n", "false"}
UNSURE_DECISIONS = {"unsure"}

FIELDNAMES = [
    "candidate_rows",
    "source_task_count",
    "completed_rows",
    "pending_rows",
    "complete_source_groups",
    "sources_with_positive",
    "expert_accept_rate",
    "hit_at_1",
    "hit_at_3",
    "hit_at_5",
    "precision_at_10",
    "mrr",
    "ndcg_at_10",
    "utility_grade_mean",
    "explanation_quality_score_mean",
    "explanation_quality_score_count",
    "claim_status",
]


def read_jsonl(path):
    rows = []
    path = Path(path)
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path, rows, fieldnames):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def norm(value):
    return str(value or "").strip().lower()


def as_int(value, default=999):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def normalized_decision(row):
    decision = norm(row.get("expert_decision"))
    if decision in POSITIVE_DECISIONS:
        return "accepted"
    if decision in NEGATIVE_DECISIONS:
        return "rejected"
    if decision in UNSURE_DECISIONS:
        return "unsure"
    return ""


def is_completed(row):
    decision = normalized_decision(row)
    grade = str(row.get("utility_grade") or "").strip()
    explanation_quality = str(row.get("explanation_quality_score") or "").strip()
    reviewer_id = str(row.get("reviewer_id") or "").strip()
    status_or_decision = norm(row.get("review_status")) in COMPLETED_STATUSES or bool(decision)
    return (
        status_or_decision
        and decision in {"accepted", "rejected", "unsure"}
        and grade in {"0", "1", "2", "3"}
        and explanation_quality in {"1", "2", "3", "4", "5"}
        and bool(reviewer_id)
    )


def is_positive(row):
    if normalized_decision(row) == "accepted":
        return True
    return str(row.get("utility_grade") or "").strip() in {"2", "3"}


def relevance_value(row):
    grade = str(row.get("utility_grade") or "").strip()
    if grade in {"0", "1", "2", "3"}:
        return int(grade)
    if normalized_decision(row) == "accepted":
        return 2
    if normalized_decision(row) == "unsure":
        return 1
    return 0


def values(rows, field, allowed):
    out = []
    for row in rows:
        raw = str(row.get(field) or "").strip()
        if raw in allowed:
            out.append(int(raw))
    return out


def ndcg_at_k(group, k=10):
    ranked = sorted(group, key=lambda row: as_int(row.get("crosswalk_rank")))[:k]
    gains = [relevance_value(row) for row in ranked]
    ideal = sorted(gains, reverse=True)

    def dcg(items):
        return sum(((2**rel) - 1) / math.log2(idx + 2) for idx, rel in enumerate(items))

    ideal_dcg = dcg(ideal)
    if ideal_dcg == 0:
        return 0.0
    return dcg(gains) / ideal_dcg


def safe_round(value):
    if isinstance(value, str):
        return value
    return round(value, 6)


def evaluate_rows(rows):
    source_groups = defaultdict(list)
    for row in rows:
        source_groups[row.get("source_id")].append(row)
    for group in source_groups.values():
        group.sort(key=lambda row: as_int(row.get("crosswalk_rank")))

    completed_rows = [row for row in rows if is_completed(row)]
    complete_groups = []
    for source_id, group in source_groups.items():
        ranks = {as_int(row.get("crosswalk_rank")) for row in group}
        expected = set(range(1, max(ranks) + 1)) if ranks else set()
        if expected and expected.issubset(ranks) and all(is_completed(row) for row in group):
            complete_groups.append((source_id, group))

    if not complete_groups:
        return {
            "candidate_rows": len(rows),
            "source_task_count": len(source_groups),
            "completed_rows": len(completed_rows),
            "pending_rows": len(rows) - len(completed_rows),
            "complete_source_groups": 0,
            "sources_with_positive": 0,
            "expert_accept_rate": "pending_crosswalk_expert_review",
            "hit_at_1": "pending_crosswalk_expert_review",
            "hit_at_3": "pending_crosswalk_expert_review",
            "hit_at_5": "pending_crosswalk_expert_review",
            "precision_at_10": "pending_crosswalk_expert_review",
            "mrr": "pending_crosswalk_expert_review",
            "ndcg_at_10": "pending_crosswalk_expert_review",
            "utility_grade_mean": "pending_crosswalk_expert_review",
            "explanation_quality_score_mean": "pending_crosswalk_expert_review",
            "explanation_quality_score_count": 0,
            "claim_status": "pending_crosswalk_expert_review",
        }

    positive_rows = [row for row in completed_rows if is_positive(row)]
    hit_1 = hit_3 = hit_5 = sources_with_positive = 0
    precision_10_sum = 0.0
    reciprocal_sum = 0.0
    ndcg_sum = 0.0
    for _, group in complete_groups:
        positives = [row for row in group if is_positive(row)]
        if positives:
            sources_with_positive += 1
            best_rank = min(as_int(row.get("crosswalk_rank")) for row in positives)
            if best_rank <= 1:
                hit_1 += 1
            if best_rank <= 3:
                hit_3 += 1
            if best_rank <= 5:
                hit_5 += 1
            reciprocal_sum += 1 / best_rank
        top10 = [row for row in group if as_int(row.get("crosswalk_rank")) <= 10]
        precision_10_sum += len([row for row in top10 if is_positive(row)]) / max(1, len(top10))
        ndcg_sum += ndcg_at_k(group, k=10)

    denom = len(complete_groups)
    evaluable_rows = [row for _, group in complete_groups for row in group]
    utility_values = values(evaluable_rows, "utility_grade", {"0", "1", "2", "3"})
    explanation_values = values(evaluable_rows, "explanation_quality_score", {"1", "2", "3", "4", "5"})
    return {
        "candidate_rows": len(rows),
        "source_task_count": len(source_groups),
        "completed_rows": len(completed_rows),
        "pending_rows": len(rows) - len(completed_rows),
        "complete_source_groups": denom,
        "sources_with_positive": sources_with_positive,
        "expert_accept_rate": safe_round(len(positive_rows) / len(completed_rows)) if completed_rows else "pending_crosswalk_expert_review",
        "hit_at_1": safe_round(hit_1 / denom),
        "hit_at_3": safe_round(hit_3 / denom),
        "hit_at_5": safe_round(hit_5 / denom),
        "precision_at_10": safe_round(precision_10_sum / denom),
        "mrr": safe_round(reciprocal_sum / denom),
        "ndcg_at_10": safe_round(ndcg_sum / denom),
        "utility_grade_mean": safe_round(sum(utility_values) / len(utility_values)) if utility_values else "pending_utility_grade",
        "explanation_quality_score_mean": safe_round(sum(explanation_values) / len(explanation_values))
        if explanation_values
        else "pending_explanation_quality_score",
        "explanation_quality_score_count": len(explanation_values),
        "claim_status": "crosswalk_expert_review_evaluated" if len(completed_rows) == len(rows) else "partial_crosswalk_expert_review",
    }


def build_report(metrics, output_dir):
    lines = [
        "# CAPE-KG NCS-PCF Crosswalk Expert Review Evaluation",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "Rows are claimable only for source-task groups whose crosswalk candidates have completed expert decisions.",
        "",
        "| candidates | completed | pending | complete groups | Hit@1 | Hit@3 | Hit@5 | P@10 | MRR | nDCG@10 | utility | explanation quality | status |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        f"| {metrics['candidate_rows']} | {metrics['completed_rows']} | {metrics['pending_rows']} | "
        f"{metrics['complete_source_groups']} | {metrics['hit_at_1']} | {metrics['hit_at_3']} | "
        f"{metrics['hit_at_5']} | {metrics['precision_at_10']} | {metrics['mrr']} | {metrics['ndcg_at_10']} | "
        f"{metrics['utility_grade_mean']} | {metrics['explanation_quality_score_mean']} | {metrics['claim_status']} |",
        "",
        "## Claim Scope",
        "",
        "- Pre-review rows remain candidate-only and are not gold NCS-PCF crosswalk labels.",
        "- Expert accept-rate, utility, and ranking metrics are only claimable after completed expert review.",
        f"- CSV: `{output_dir / 'crosswalk_expert_metrics.csv'}`",
        f"- JSON: `{output_dir / 'crosswalk_expert_metrics.json'}`",
        "",
    ]
    return "\n".join(lines)


def run(args):
    exp_dir = Path(args.experiment_dir)
    review_file = Path(args.review_file) if args.review_file else exp_dir / "01_data/crosswalk_review/crosswalk_review_items.jsonl"
    output_dir = exp_dir / "04_evaluation"
    rows = read_jsonl(review_file)
    metrics = evaluate_rows(rows)
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "review_file": str(review_file),
        "metrics": metrics,
        "claim_status": metrics.get("claim_status"),
        "report": str(output_dir / "crosswalk_expert_evaluation_report.md"),
    }
    write_json(output_dir / "crosswalk_expert_metrics.json", payload)
    write_csv(output_dir / "crosswalk_expert_metrics.csv", [metrics], FIELDNAMES)
    write_text(output_dir / "crosswalk_expert_evaluation_report.md", build_report(metrics, output_dir))
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--review-file", default="")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
