#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Evaluate expert-reviewed CAPE-KG NCS/PCF mapping candidates."""

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
COMPLETED_STATUSES = {"completed", "reviewed", "adjudicated", "final"}
POSITIVE_DECISIONS = {"accepted", "accept", "yes", "y", "true"}
NEGATIVE_DECISIONS = {"rejected", "reject", "no", "n", "false"}
UNSURE_DECISIONS = {"unsure"}

FIELDNAMES = [
    "standard",
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
    "precision_at_5",
    "mrr",
    "ndcg_at_10",
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


def write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in FIELDNAMES})


def norm(value):
    return str(value or "").strip().lower()


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
    status_or_decision = norm(row.get("review_status")) in COMPLETED_STATUSES or bool(normalized_decision(row))
    grade = str(row.get("relevance_grade") or "").strip()
    reviewer_id = str(row.get("reviewer_id") or "").strip()
    return status_or_decision and bool(normalized_decision(row)) and grade in {"0", "1", "2", "3"} and bool(reviewer_id)


def is_positive(row):
    decision = normalized_decision(row)
    if decision == "accepted":
        return True
    grade = str(row.get("relevance_grade") or "").strip()
    return grade in {"2", "3"}


def is_negative(row):
    decision = normalized_decision(row)
    if decision == "rejected":
        return True
    grade = str(row.get("relevance_grade") or "").strip()
    return grade in {"0", "1"}


def relevance_value(row):
    grade = str(row.get("relevance_grade") or "").strip()
    if grade in {"0", "1", "2", "3"}:
        return int(grade)
    decision = normalized_decision(row)
    if decision == "accepted":
        return 2
    if decision == "unsure":
        return 1
    return 0


def ndcg_at_k(group, k=10):
    ranked = sorted(group, key=lambda row: int(row.get("rank") or 999))[:k]
    gains = [relevance_value(row) for row in ranked]
    ideal = sorted(gains, reverse=True)

    def dcg(values):
        return sum(((2**rel) - 1) / math.log2(idx + 2) for idx, rel in enumerate(values))

    ideal_dcg = dcg(ideal)
    if ideal_dcg == 0:
        return 0.0
    return dcg(gains) / ideal_dcg


def explanation_quality_values(rows):
    values = []
    for row in rows:
        raw = str(row.get("explanation_quality_score") or "").strip()
        if raw in {"1", "2", "3", "4", "5"}:
            values.append(int(raw))
    return values


def safe_round(value):
    if value == "pending_expert_review":
        return value
    return round(value, 6)


def evaluate_standard(standard, rows):
    source_groups = defaultdict(list)
    for row in rows:
        source_groups[row.get("source_id")].append(row)
    for group in source_groups.values():
        group.sort(key=lambda row: int(row.get("rank") or 999))

    completed_rows = [row for row in rows if is_completed(row)]
    pending_rows = len(rows) - len(completed_rows)
    complete_groups = []
    for source_id, group in source_groups.items():
        top5 = [row for row in group if int(row.get("rank") or 999) <= 5]
        if top5 and all(is_completed(row) for row in top5):
            complete_groups.append((source_id, top5))

    if not complete_groups:
        return {
            "standard": standard,
            "candidate_rows": len(rows),
            "source_task_count": len(source_groups),
            "completed_rows": len(completed_rows),
            "pending_rows": pending_rows,
            "complete_source_groups": 0,
            "sources_with_positive": 0,
            "expert_accept_rate": "pending_expert_review",
            "hit_at_1": "pending_expert_review",
            "hit_at_3": "pending_expert_review",
            "hit_at_5": "pending_expert_review",
            "precision_at_5": "pending_expert_review",
            "mrr": "pending_expert_review",
            "ndcg_at_10": "pending_expert_review",
            "explanation_quality_score_mean": "pending_expert_review",
            "explanation_quality_score_count": 0,
            "claim_status": "pending_expert_review",
        }

    positive_rows = [row for row in completed_rows if is_positive(row)]
    hit_1 = 0
    hit_3 = 0
    hit_5 = 0
    precision_5_sum = 0.0
    reciprocal_sum = 0.0
    ndcg_sum = 0.0
    sources_with_positive = 0
    for _, group in complete_groups:
        positives = [row for row in group if is_positive(row)]
        if positives:
            sources_with_positive += 1
            best_rank = min(int(row.get("rank") or 999) for row in positives)
            if best_rank <= 1:
                hit_1 += 1
            if best_rank <= 3:
                hit_3 += 1
            if best_rank <= 5:
                hit_5 += 1
            reciprocal_sum += 1 / best_rank
        precision_5_sum += len(positives) / 5
        ndcg_sum += ndcg_at_k(group, k=10)

    denom = len(complete_groups)
    explanation_values = explanation_quality_values([row for _, group in complete_groups for row in group])
    return {
        "standard": standard,
        "candidate_rows": len(rows),
        "source_task_count": len(source_groups),
        "completed_rows": len(completed_rows),
        "pending_rows": pending_rows,
        "complete_source_groups": denom,
        "sources_with_positive": sources_with_positive,
        "expert_accept_rate": safe_round(len(positive_rows) / len(completed_rows)) if completed_rows else "pending_expert_review",
        "hit_at_1": safe_round(hit_1 / denom),
        "hit_at_3": safe_round(hit_3 / denom),
        "hit_at_5": safe_round(hit_5 / denom),
        "precision_at_5": safe_round(precision_5_sum / denom),
        "mrr": safe_round(reciprocal_sum / denom),
        "ndcg_at_10": safe_round(ndcg_sum / denom),
        "explanation_quality_score_mean": safe_round(sum(explanation_values) / len(explanation_values))
        if explanation_values
        else "pending_explanation_quality_score",
        "explanation_quality_score_count": len(explanation_values),
        "claim_status": "expert_review_evaluated" if pending_rows == 0 else "partial_expert_review",
    }


def build_report(rows, output_dir):
    lines = [
        "# CAPE-KG Mapping Expert Review Evaluation",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "Rows are claimable only for source task groups whose Top-5 candidates have completed expert decisions.",
        "",
        "| standard | completed rows | pending rows | complete groups | Hit@1 | Hit@3 | Hit@5 | P@5 | MRR | nDCG@10 | explanation quality | status |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['standard']} | {row['completed_rows']} | {row['pending_rows']} | "
            f"{row['complete_source_groups']} | {row['hit_at_1']} | {row['hit_at_3']} | "
            f"{row['hit_at_5']} | {row['precision_at_5']} | {row['mrr']} | "
            f"{row['ndcg_at_10']} | {row['explanation_quality_score_mean']} | {row['claim_status']} |"
        )
    lines += [
        "",
        f"- CSV: `{output_dir / 'mapping_expert_metrics.csv'}`",
        f"- JSON: `{output_dir / 'mapping_expert_metrics.json'}`",
        "",
    ]
    return "\n".join(lines)


def run(args):
    exp_dir = Path(args.experiment_dir)
    review_file = Path(args.review_file) if args.review_file else exp_dir / "01_data/mapping_review/mapping_review_items.jsonl"
    output_dir = exp_dir / "04_evaluation"
    rows = read_jsonl(review_file)
    by_standard = defaultdict(list)
    for row in rows:
        by_standard[row.get("standard") or "unknown"].append(row)
    metrics = [evaluate_standard(standard, standard_rows) for standard, standard_rows in sorted(by_standard.items())]
    if not metrics:
        metrics = [
            {
                "standard": "NCS/PCF",
                "candidate_rows": 0,
                "source_task_count": 0,
                "completed_rows": 0,
                "pending_rows": 0,
                "complete_source_groups": 0,
                "sources_with_positive": 0,
                "expert_accept_rate": "pending_expert_review",
                "hit_at_1": "pending_expert_review",
                "hit_at_3": "pending_expert_review",
                "hit_at_5": "pending_expert_review",
                "precision_at_5": "pending_expert_review",
                "mrr": "pending_expert_review",
                "ndcg_at_10": "pending_expert_review",
                "explanation_quality_score_mean": "pending_expert_review",
                "explanation_quality_score_count": 0,
                "claim_status": "missing_review_file",
            }
        ]
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "review_file": str(review_file),
        "metrics": metrics,
        "claim_status": "expert_review_evaluated"
        if metrics and all(row["claim_status"] == "expert_review_evaluated" for row in metrics)
        else "pending_or_partial_expert_review",
    }
    write_csv(output_dir / "mapping_expert_metrics.csv", metrics)
    write_json(output_dir / "mapping_expert_metrics.json", payload)
    write_text(output_dir / "mapping_expert_evaluation_report.md", build_report(metrics, output_dir))
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--review-file", default="")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
