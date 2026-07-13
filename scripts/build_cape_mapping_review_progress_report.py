#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build progress and priority worklists for CAPE-KG mapping expert review."""

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
COMPLETED_STATUSES = {"completed", "reviewed", "adjudicated", "final"}
POSITIVE_DECISIONS = {"accepted", "accept", "yes", "y", "true"}
NEGATIVE_DECISIONS = {"rejected", "reject", "no", "n", "false"}
DECISION_VALUES = POSITIVE_DECISIONS | NEGATIVE_DECISIONS | {"unsure"}

GROUP_FIELDNAMES = [
    "group_key",
    "standard",
    "source_id",
    "source_label",
    "source_type",
    "candidate_rows",
    "top5_rows",
    "completed_top5_rows",
    "pending_top5_rows",
    "completed_rows",
    "pending_rows",
    "group_complete",
    "top_score",
    "second_score",
    "score_gap",
    "completion_gap",
    "score_strength",
    "ambiguity_score",
    "priority_score",
    "priority_reason",
]

ROW_FIELDNAMES = [
    "row_priority",
    "group_priority",
    "group_key",
    "standard",
    "source_id",
    "source_label",
    "mapping_id",
    "mapping_type",
    "rank",
    "score",
    "target_id",
    "target_label",
    "target_type",
    "review_status",
    "expert_decision",
    "relevance_grade",
    "explanation_quality_score",
    "reason",
]

BRIEFING_FIELDNAMES = [
    "group_rank",
    "group_key",
    "group_priority",
    "review_focus",
    "standard",
    "source_id",
    "source_label",
    "mapping_id",
    "mapping_type",
    "rank",
    "score",
    "score_gap",
    "target_id",
    "target_label",
    "target_type",
    "name_similarity",
    "definition_description_similarity",
    "action_verb_similarity",
    "hierarchy_context_similarity",
    "level_compatibility",
    "domain_gap_penalty",
    "reason",
    "recommended_review_question",
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


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path, fieldnames, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def norm(value):
    return str(value or "").strip().lower()


def as_int(value, default=999):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def as_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def round6(value):
    return round(float(value), 6)


def is_completed(row):
    return norm(row.get("review_status")) in COMPLETED_STATUSES or norm(row.get("expert_decision")) in DECISION_VALUES


def is_positive(row):
    decision = norm(row.get("expert_decision"))
    if decision in POSITIVE_DECISIONS:
        return True
    grade = str(row.get("relevance_grade") or "").strip()
    return grade in {"2", "3"}


def score_group(rows):
    sorted_rows = sorted(rows, key=lambda row: (as_int(row.get("rank")), -as_float(row.get("score"))))
    top5 = [row for row in sorted_rows if as_int(row.get("rank")) <= 5]
    scores = sorted((as_float(row.get("score")) for row in top5), reverse=True)
    top_score = scores[0] if scores else 0.0
    second_score = scores[1] if len(scores) > 1 else 0.0
    score_gap = abs(top_score - second_score) if len(scores) > 1 else 0.0
    completed_top5 = sum(1 for row in top5 if is_completed(row))
    pending_top5 = max(0, len(top5) - completed_top5)
    completed_rows = sum(1 for row in sorted_rows if is_completed(row))
    pending_rows = max(0, len(sorted_rows) - completed_rows)
    completion_gap = pending_top5 / max(1, len(top5))
    score_strength = min(top_score / 0.30, 1.0) if top_score > 0 else 0.0
    ambiguity_score = 1 - min(score_gap / 0.05, 1.0) if len(scores) > 1 else 0.0
    priority_score = 0.55 * completion_gap + 0.25 * score_strength + 0.20 * ambiguity_score
    group_complete = bool(top5) and pending_top5 == 0
    first = sorted_rows[0] if sorted_rows else {}

    reasons = []
    if pending_top5:
        reasons.append(f"{pending_top5} Top-5 rows pending")
    if ambiguity_score >= 0.8:
        reasons.append("close scores")
    if score_strength >= 0.5:
        reasons.append("high-scoring candidates")
    if not reasons:
        reasons.append("Top-5 complete")

    return {
        "group_key": f"{first.get('standard') or 'unknown'}::{first.get('source_id') or 'unknown'}",
        "standard": first.get("standard") or "",
        "source_id": first.get("source_id") or "",
        "source_label": first.get("source_label") or "",
        "source_type": first.get("source_type") or "",
        "candidate_rows": len(sorted_rows),
        "top5_rows": len(top5),
        "completed_top5_rows": completed_top5,
        "pending_top5_rows": pending_top5,
        "completed_rows": completed_rows,
        "pending_rows": pending_rows,
        "group_complete": group_complete,
        "top_score": round6(top_score),
        "second_score": round6(second_score),
        "score_gap": round6(score_gap),
        "completion_gap": round6(completion_gap),
        "score_strength": round6(score_strength),
        "ambiguity_score": round6(ambiguity_score),
        "priority_score": round6(priority_score),
        "priority_reason": "; ".join(reasons),
    }


def build_group_rows(rows):
    groups = defaultdict(list)
    for row in rows:
        key = (row.get("standard") or "unknown", row.get("source_id") or "unknown")
        groups[key].append(row)
    group_rows = [score_group(group_rows) for _, group_rows in sorted(groups.items())]
    group_rows.sort(
        key=lambda row: (
            bool(row.get("group_complete")),
            -as_float(row.get("priority_score")),
            row.get("standard") or "",
            row.get("source_label") or "",
        )
    )
    return group_rows


def build_row_queue(rows, group_rows):
    group_priority = {row["group_key"]: as_float(row.get("priority_score")) for row in group_rows}
    queued = []
    for row in rows:
        group_key = f"{row.get('standard') or 'unknown'}::{row.get('source_id') or 'unknown'}"
        rank = as_int(row.get("rank"))
        top5_bonus = max(0.0, (6 - rank) / 50.0) if rank <= 5 else 0.0
        pending_bonus = 0.25 if not is_completed(row) else 0.0
        row_priority = group_priority.get(group_key, 0.0) + top5_bonus + pending_bonus
        queued.append(
            {
                "row_priority": round6(row_priority),
                "group_priority": round6(group_priority.get(group_key, 0.0)),
                "group_key": group_key,
                "standard": row.get("standard") or "",
                "source_id": row.get("source_id") or "",
                "source_label": row.get("source_label") or "",
                "mapping_id": row.get("mapping_id") or "",
                "mapping_type": row.get("mapping_type") or "",
                "rank": rank if rank != 999 else "",
                "score": row.get("score") if row.get("score") is not None else "",
                "target_id": row.get("target_id") or "",
                "target_label": row.get("target_label") or "",
                "target_type": row.get("target_type") or "",
                "review_status": row.get("review_status") or "",
                "expert_decision": row.get("expert_decision") or "",
                "relevance_grade": row.get("relevance_grade") or "",
                "explanation_quality_score": row.get("explanation_quality_score") or "",
                "reason": row.get("reason") or "",
            }
        )
    queued.sort(
        key=lambda row: (
            norm(row.get("review_status")) in COMPLETED_STATUSES or norm(row.get("expert_decision")) in DECISION_VALUES,
            -as_float(row.get("row_priority")),
            row.get("standard") or "",
            as_int(row.get("rank")),
        )
    )
    return queued


def review_focus_for_group(group_row):
    focus = []
    if as_float(group_row.get("score_gap")) <= 0.01:
        focus.append("close-score disambiguation")
    if as_float(group_row.get("top_score")) >= 0.30:
        focus.append("high-score verification")
    if as_float(group_row.get("top_score")) < 0.15:
        focus.append("low-score skepticism")
    if as_float(group_row.get("pending_top5_rows")) > 0:
        focus.append("complete Top-5 before metric use")
    return "; ".join(focus or ["standard Top-5 review"])


def score_breakdown_value(row, key):
    breakdown = row.get("score_breakdown") or {}
    if not isinstance(breakdown, dict):
        return ""
    value = breakdown.get(key)
    return "" if value is None else value


def recommended_question(row, group_row):
    standard = row.get("standard") or ""
    source = row.get("source_label") or row.get("source_id") or "source task"
    target = row.get("target_label") or row.get("target_id") or "target"
    if standard == "NCS":
        return f"`{source}` 수행에 필요한 직무 능력단위로 `{target}`가 방어 가능한가?"
    if standard == "PCF":
        return f"`{source}` 업무가 PCF process context `{target}`에 자연스럽게 위치하는가?"
    return f"`{source}`와 `{target}`의 업무 목적이 실질적으로 대응되는가?"


def build_group_briefing(rows, group_rows, limit=20):
    rows_by_group = defaultdict(list)
    for row in rows:
        group_key = f"{row.get('standard') or 'unknown'}::{row.get('source_id') or 'unknown'}"
        rows_by_group[group_key].append(row)

    incomplete = [row for row in group_rows if not row.get("group_complete")]
    briefing_rows = []
    for group_rank, group_row in enumerate(incomplete[:limit], start=1):
        group_key = group_row["group_key"]
        top5 = sorted(
            [row for row in rows_by_group.get(group_key, []) if as_int(row.get("rank")) <= 5],
            key=lambda row: (as_int(row.get("rank")), -as_float(row.get("score"))),
        )
        focus = review_focus_for_group(group_row)
        for row in top5:
            briefing_rows.append(
                {
                    "group_rank": group_rank,
                    "group_key": group_key,
                    "group_priority": group_row.get("priority_score"),
                    "review_focus": focus,
                    "standard": row.get("standard") or "",
                    "source_id": row.get("source_id") or "",
                    "source_label": row.get("source_label") or "",
                    "mapping_id": row.get("mapping_id") or "",
                    "mapping_type": row.get("mapping_type") or "",
                    "rank": row.get("rank") if row.get("rank") is not None else "",
                    "score": row.get("score") if row.get("score") is not None else "",
                    "score_gap": group_row.get("score_gap"),
                    "target_id": row.get("target_id") or "",
                    "target_label": row.get("target_label") or "",
                    "target_type": row.get("target_type") or "",
                    "name_similarity": score_breakdown_value(row, "name_similarity"),
                    "definition_description_similarity": score_breakdown_value(row, "definition_description_similarity"),
                    "action_verb_similarity": score_breakdown_value(row, "action_verb_similarity"),
                    "hierarchy_context_similarity": score_breakdown_value(row, "hierarchy_context_similarity"),
                    "level_compatibility": score_breakdown_value(row, "level_compatibility"),
                    "domain_gap_penalty": score_breakdown_value(row, "domain_gap_penalty"),
                    "reason": row.get("reason") or "",
                    "recommended_review_question": recommended_question(row, group_row),
                    "claim_status": "candidate_only_pending_expert_review",
                }
            )
    return briefing_rows


def summarize_by_standard(rows, group_rows):
    by_standard = defaultdict(lambda: {"candidate_rows": 0, "completed_rows": 0, "positive_rows": 0})
    for row in rows:
        standard = row.get("standard") or "unknown"
        by_standard[standard]["candidate_rows"] += 1
        if is_completed(row):
            by_standard[standard]["completed_rows"] += 1
        if is_positive(row):
            by_standard[standard]["positive_rows"] += 1

    for row in group_rows:
        standard = row.get("standard") or "unknown"
        by_standard[standard].setdefault("source_groups", 0)
        by_standard[standard].setdefault("complete_source_groups", 0)
        by_standard[standard].setdefault("pending_source_groups", 0)
        by_standard[standard]["source_groups"] += 1
        if row.get("group_complete"):
            by_standard[standard]["complete_source_groups"] += 1
        else:
            by_standard[standard]["pending_source_groups"] += 1

    summary_rows = []
    for standard, payload in sorted(by_standard.items()):
        candidate_rows = payload.get("candidate_rows", 0)
        completed_rows = payload.get("completed_rows", 0)
        source_groups = payload.get("source_groups", 0)
        complete_source_groups = payload.get("complete_source_groups", 0)
        summary_rows.append(
            {
                "standard": standard,
                "candidate_rows": candidate_rows,
                "completed_rows": completed_rows,
                "pending_rows": candidate_rows - completed_rows,
                "positive_rows": payload.get("positive_rows", 0),
                "source_groups": source_groups,
                "complete_source_groups": complete_source_groups,
                "pending_source_groups": source_groups - complete_source_groups,
            }
        )
    return summary_rows


def md_escape(value):
    return str(value or "").replace("|", "/").replace("\n", " ")


def build_group_briefing_report(briefing_rows, output_paths):
    generated_at = datetime.now(timezone.utc).isoformat()
    groups = defaultdict(list)
    for row in briefing_rows:
        groups[row["group_key"]].append(row)

    lines = [
        "# CAPE-KG Mapping Review Group Briefing",
        "",
        f"Generated: {generated_at}",
        "",
        "This briefing expands the next Top-20 source-task/standard groups into their Top-5 mapping candidates.",
        "It is a reviewer navigation aid only. Candidate rows remain non-claimable until expert decisions are returned and imported.",
        "",
        "## Summary",
        "",
        f"- groups: {len(groups)}",
        f"- candidate rows: {len(briefing_rows)}",
        "- claim_status: `candidate_only_pending_expert_review`",
        "",
        "## Review Rule",
        "",
        "- Finish all Top-5 rows in a source-task/standard group before using that group for Hit@K, P@5, MRR, or accept-rate.",
        "- Treat close-score groups as ambiguity checks; do not accept the top-ranked row only because it ranks first.",
        "- Use `accepted/rejected/unsure`, `relevance_grade`, `explanation_quality_score`, and a short comment in `mapping_review_items.reviewed.jsonl`.",
        "",
    ]

    for group_key, rows in sorted(groups.items(), key=lambda item: (as_int(item[1][0].get("group_rank")), item[0])):
        first = rows[0]
        lines += [
            f"## {first['group_rank']}. {md_escape(first['standard'])} / {md_escape(first['source_label'])}",
            "",
            f"- group_key: `{group_key}`",
            f"- group_priority: {first.get('group_priority')}",
            f"- score_gap: {first.get('score_gap')}",
            f"- review_focus: {md_escape(first.get('review_focus'))}",
            "",
            "| rank | score | target | score signals | review question |",
            "|---:|---:|---|---|---|",
        ]
        for row in sorted(rows, key=lambda item: as_int(item.get("rank"))):
            signals = (
                f"name={row.get('name_similarity')}; "
                f"def={row.get('definition_description_similarity')}; "
                f"verb={row.get('action_verb_similarity')}; "
                f"hier={row.get('hierarchy_context_similarity')}"
            )
            target = f"`{md_escape(row.get('target_id'))}` {md_escape(row.get('target_label'))}"
            lines.append(
                f"| {row.get('rank')} | {row.get('score')} | {target} | {md_escape(signals)} | {md_escape(row.get('recommended_review_question'))} |"
            )
        lines.append("")

    lines += [
        "## Output Files",
        "",
        f"- JSON: `{output_paths['group_briefing_json']}`",
        f"- Markdown: `{output_paths['group_briefing_md']}`",
        f"- CSV: `{output_paths['group_briefing_csv']}`",
        "",
    ]
    return "\n".join(lines)


def build_report(summary, group_rows, output_paths):
    generated_at = datetime.now(timezone.utc).isoformat()
    incomplete_groups = [row for row in group_rows if not row.get("group_complete")]
    lines = [
        "# CAPE-KG Mapping Review Progress Report",
        "",
        f"Generated: {generated_at}",
        "",
        "This is a workflow/progress report for expert mapping review. It does not turn mapping candidates into gold labels by itself.",
        "",
        "A source task group becomes evaluable only when every Top-5 candidate in that standard/source group has a completed expert decision.",
        "",
        "## Summary",
        "",
        "| standard | candidate rows | completed rows | pending rows | source groups | complete groups | pending groups |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary:
        lines.append(
            f"| {row['standard']} | {row['candidate_rows']} | {row['completed_rows']} | {row['pending_rows']} | "
            f"{row['source_groups']} | {row['complete_source_groups']} | {row['pending_source_groups']} |"
        )

    lines += [
        "",
        "## Top Pending Groups",
        "",
        "| priority | standard | source task | pending Top-5 | top score | score gap | reason |",
        "|---:|---|---|---:|---:|---:|---|",
    ]
    for row in incomplete_groups[:25]:
        source_label = str(row.get("source_label") or row.get("source_id") or "").replace("|", "/")
        reason = str(row.get("priority_reason") or "").replace("|", "/")
        lines.append(
            f"| {row['priority_score']} | {row['standard']} | {source_label} | {row['pending_top5_rows']} | "
            f"{row['top_score']} | {row['score_gap']} | {reason} |"
        )

    lines += [
        "",
        "## Generated Files",
        "",
        f"- Progress summary JSON: `{output_paths['summary_json']}`",
        f"- Group priority CSV: `{output_paths['priority_csv']}`",
        f"- Group priority JSONL: `{output_paths['priority_jsonl']}`",
        f"- Next 20 groups CSV: `{output_paths['next_groups_csv']}`",
        f"- Next 60 rows CSV: `{output_paths['next_rows_csv']}`",
        f"- Top-20 group briefing MD: `{output_paths['group_briefing_md']}`",
        f"- Top-20 group briefing CSV: `{output_paths['group_briefing_csv']}`",
        "",
        "Use the next-groups file to finish complete Top-5 groups first; use the next-rows file when assigning row-level review tasks.",
        "",
    ]
    return "\n".join(lines)


def run(args):
    exp_dir = Path(args.experiment_dir)
    review_file = Path(args.review_file) if args.review_file else exp_dir / "01_data/mapping_review/mapping_review_items.jsonl"
    release_dir = exp_dir / "06_release"
    review_out_dir = exp_dir / "05_review"

    rows = read_jsonl(review_file)
    group_rows = build_group_rows(rows)
    row_queue = build_row_queue(rows, group_rows)
    briefing_rows = build_group_briefing(rows, group_rows, limit=20)
    summary_rows = summarize_by_standard(rows, group_rows)
    incomplete_groups = [row for row in group_rows if not row.get("group_complete")]

    output_paths = {
        "report_md": str(release_dir / "mapping_review_progress_report.md"),
        "summary_json": str(release_dir / "mapping_review_progress_summary.json"),
        "priority_csv": str(review_out_dir / "mapping_review_priority_queue.csv"),
        "priority_jsonl": str(review_out_dir / "mapping_review_priority_queue.jsonl"),
        "next_groups_csv": str(review_out_dir / "mapping_review_next_20_groups.csv"),
        "next_rows_csv": str(review_out_dir / "mapping_review_next_60_rows.csv"),
        "group_briefing_json": str(release_dir / "mapping_review_group_briefing.json"),
        "group_briefing_md": str(release_dir / "mapping_review_group_briefing.md"),
        "group_briefing_csv": str(review_out_dir / "mapping_review_group_briefing_top20.csv"),
    }

    summary_payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "review_file": str(review_file),
        "candidate_rows": len(rows),
        "source_task_standard_groups": len(group_rows),
        "complete_source_groups": sum(1 for row in group_rows if row.get("group_complete")),
        "pending_source_groups": len(incomplete_groups),
        "completed_rows": sum(1 for row in rows if is_completed(row)),
        "pending_rows": sum(1 for row in rows if not is_completed(row)),
        "positive_rows": sum(1 for row in rows if is_positive(row)),
        "by_standard": summary_rows,
        "top_pending_groups": incomplete_groups[:25],
        "top20_group_briefing_rows": len(briefing_rows),
        "output_files": output_paths,
        "claim_status": "expert_review_complete" if rows and not incomplete_groups and all(is_completed(row) for row in rows) else "pending_or_partial_expert_review",
        "note": "Workflow/progress artifact only; mapping claims still require completed expert review.",
    }

    write_csv(output_paths["priority_csv"], GROUP_FIELDNAMES, group_rows)
    write_jsonl(output_paths["priority_jsonl"], group_rows)
    write_csv(output_paths["next_groups_csv"], GROUP_FIELDNAMES, incomplete_groups[:20])
    write_csv(output_paths["next_rows_csv"], ROW_FIELDNAMES, [row for row in row_queue if row["row_priority"] > 0][:60])
    write_csv(output_paths["group_briefing_csv"], BRIEFING_FIELDNAMES, briefing_rows)
    write_json(
        output_paths["group_briefing_json"],
        {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "experiment_dir": str(exp_dir),
            "claim_status": "candidate_only_pending_expert_review",
            "source": str(review_file),
            "group_count": len({row["group_key"] for row in briefing_rows}),
            "candidate_rows": len(briefing_rows),
            "briefing_csv": output_paths["group_briefing_csv"],
            "briefing_md": output_paths["group_briefing_md"],
            "rows": briefing_rows,
        },
    )
    write_text(output_paths["group_briefing_md"], build_group_briefing_report(briefing_rows, output_paths))
    write_json(output_paths["summary_json"], summary_payload)
    write_text(output_paths["report_md"], build_report(summary_rows, group_rows, output_paths))

    print(json.dumps(summary_payload, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--review-file", default="")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
