#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build an optional structural-review action plan for CAPE-KG gap worklists."""

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")

RETURN_FIELDS = [
    "task_type",
    "owner",
    "expected_rows",
    "input_file",
    "reviewed_file",
    "present",
    "status",
    "allowed_decisions",
    "next_action",
]


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path):
    path = Path(path)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def csv_fieldnames(path):
    path = Path(path)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or [])


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path, rows, fieldnames):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def bool_text(value):
    return "yes" if value else "no"


def reviewed_path(path):
    path = Path(path)
    return path.with_name(f"{path.stem}.reviewed{path.suffix}")


def file_present(path):
    path = Path(path)
    return path.exists() and path.stat().st_size > 0


def build_return_rows(exp_dir, summary):
    review_dir = exp_dir / "05_review"
    checkpoint_input = review_dir / "structural_review_checkpoint_candidates.csv"
    gateway_input = review_dir / "structural_gateway_branch_gaps.csv"
    checkpoint_reviewed = reviewed_path(checkpoint_input)
    gateway_reviewed = reviewed_path(gateway_input)
    checkpoint_rows = read_csv(checkpoint_input)
    gateway_rows = read_csv(gateway_input)

    return [
        {
            "task_type": "structural_review_checkpoint_candidates",
            "owner": "structural_reviewer",
            "expected_rows": len(checkpoint_rows),
            "input_file": str(checkpoint_input),
            "reviewed_file": str(checkpoint_reviewed),
            "present": bool_text(file_present(checkpoint_reviewed)),
            "status": "ready_for_optional_review" if not file_present(checkpoint_reviewed) else "reviewed_file_present",
            "allowed_decisions": "accept_review_checkpoint;keep_current_type;merge_with_existing_review;reject_candidate;needs_discussion",
            "next_action": "Fill human_decision and human_notes, then save with the exact reviewed_file name.",
        },
        {
            "task_type": "structural_gateway_branch_gaps",
            "owner": "structural_reviewer",
            "expected_rows": len(gateway_rows),
            "input_file": str(gateway_input),
            "reviewed_file": str(gateway_reviewed),
            "present": bool_text(file_present(gateway_reviewed)),
            "status": "ready_for_optional_review" if not file_present(gateway_reviewed) else "reviewed_file_present",
            "allowed_decisions": "add_branches_to;keep_gateway_without_branch;split_gateway;reject_gateway;needs_discussion",
            "next_action": "Fill human_decision and human_notes; add branch target notes only when source evidence supports the outcome.",
        },
    ]


def render_report(payload):
    rows = payload["optional_return_files"]
    summary = payload["summary"]
    input_fields = payload.get("input_csv_fields") or {}
    lines = [
        "# CAPE-KG Structural Review Action Plan",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Claim status: `{payload['claim_status']}`",
        "",
        "## Purpose",
        "",
        "This plan turns the structural gap worklist into optional human-review return files. It does not change the 11-file minimum paper gate and is tracked separately for optional/strong claims.",
        "",
        "## Summary",
        "",
        "| Item | Value |",
        "|---|---:|",
        f"| Review checkpoint candidates | {summary.get('review_checkpoint_candidate_count')} |",
        f"| Gateway branch gaps | {summary.get('gateway_branch_gap_count')} |",
        f"| Structural CQ answerability | {summary.get('structural_cq_answerability_rate')} |",
        f"| Procedural consistency | {summary.get('procedural_consistency_rate')} |",
        f"| Required human-gate effect | {summary.get('human_gate_effect')} |",
        "",
        "## Optional Return Files",
        "",
        "| task_type | expected_rows | input_file | reviewed_file | status |",
        "|---|---:|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['task_type']} | {row['expected_rows']} | `{row['input_file']}` | "
            f"`{row['reviewed_file']}` | {row['status']} |"
        )
    lines += [
        "",
        "## Input CSV Fields",
        "",
        "- `structural_review_checkpoint_candidates.csv` lists review-signaled task/step rows and their evidence previews.",
        "- `structural_gateway_branch_gaps.csv` includes `guard_condition_labels`, `incoming_task_labels`, and `candidate_branch_target_labels` so reviewers do not need to infer branch targets from IDs alone.",
        "- `human_decision` and `human_notes` are the only fields reviewers must fill unless they need to clarify a branch target in notes.",
        "",
        "| input | fields |",
        "|---|---|",
        f"| structural_review_checkpoint_candidates.csv | `{', '.join(input_fields.get('structural_review_checkpoint_candidates', []))}` |",
        f"| structural_gateway_branch_gaps.csv | `{', '.join(input_fields.get('structural_gateway_branch_gaps', []))}` |",
        "",
        "## Decision Policy",
        "",
        "- Review checkpoint rows should be accepted only when the activity is a true review/checkpoint, not merely a normal task containing review-like wording.",
        "- Gateway branch rows should add `BRANCHES_TO` only when the source evidence supports explicit branch outcomes.",
        "- Ambiguous rows should be marked `needs_discussion` rather than used to modify the KG automatically.",
        "- The current KG must not be changed from this worklist until reviewed files are returned and an import/update step is explicitly run.",
        "",
        "## Allowed Decisions",
        "",
        "| task_type | allowed decisions |",
        "|---|---|",
    ]
    for row in rows:
        lines.append(f"| {row['task_type']} | `{row['allowed_decisions']}` |")
    lines += [
        "",
        "## Next Step",
        "",
        "1. Open the input CSV files listed above.",
        "2. Fill `human_decision` and `human_notes` for each row.",
        "3. Save each file with the exact `.reviewed.csv` filename listed above.",
        "4. Keep these files as optional structural review evidence; they do not replace the 11 minimum paper-gate annotation/adjudication return files.",
        "",
    ]
    return "\n".join(lines)


def run(args):
    exp_dir = Path(args.experiment_dir)
    eval_dir = exp_dir / "04_evaluation"
    release_dir = exp_dir / "06_release"
    review_dir = exp_dir / "05_review"
    summary = read_json(eval_dir / "structural_gap_worklist_summary.json", {}) or {}
    return_rows = build_return_rows(exp_dir, summary)
    input_csv_fields = {
        "structural_review_checkpoint_candidates": csv_fieldnames(review_dir / "structural_review_checkpoint_candidates.csv"),
        "structural_gateway_branch_gaps": csv_fieldnames(review_dir / "structural_gateway_branch_gaps.csv"),
    }
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "claim_status": "optional_structural_review_ready_pending_human_review",
        "summary": summary,
        "optional_return_files": return_rows,
        "input_csv_fields": input_csv_fields,
        "outputs": {
            "plan_json": str(release_dir / "structural_review_action_plan.json"),
            "plan_md": str(release_dir / "structural_review_action_plan.md"),
            "optional_returns_csv": str(review_dir / "structural_review_optional_returns.csv"),
        },
    }
    write_json(release_dir / "structural_review_action_plan.json", payload)
    write_text(release_dir / "structural_review_action_plan.md", render_report(payload))
    write_csv(review_dir / "structural_review_optional_returns.csv", return_rows, RETURN_FIELDS)
    print(json.dumps(payload["outputs"], ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
