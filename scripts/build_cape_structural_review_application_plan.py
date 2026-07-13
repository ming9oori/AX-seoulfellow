#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a dry-run application plan for optional structural review returns."""

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")

ACTION_FIELDS = [
    "task_type",
    "key",
    "label",
    "human_decision",
    "proposed_action",
    "application_status",
    "manual_update_required",
    "parent_task_id",
    "target_ids",
    "current_type",
    "recommended_action",
    "evidence_anchor_count",
    "human_notes",
]

CHECKPOINT_DECISION_MAP = {
    "accept_review_checkpoint": ("propose_add_or_retype_review_checkpoint", "manual_update_required"),
    "merge_with_existing_review": ("propose_merge_with_existing_review_checkpoint", "manual_update_required"),
    "keep_current_type": ("no_kg_change_keep_current_type", "no_change"),
    "reject_candidate": ("no_kg_change_reject_candidate", "no_change"),
    "needs_discussion": ("discuss_before_kg_change", "discussion_required"),
}

GATEWAY_DECISION_MAP = {
    "add_branches_to": ("propose_add_branches_to_decision_gateway", "manual_update_required"),
    "split_gateway": ("propose_split_decision_gateway", "manual_update_required"),
    "keep_gateway_without_branch": ("no_kg_change_keep_gateway_without_branch", "no_change"),
    "reject_gateway": ("no_kg_change_reject_gateway", "no_change"),
    "needs_discussion": ("discuss_before_kg_change", "discussion_required"),
}


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


def reviewed_path(path):
    path = Path(path)
    return path.with_name(f"{path.stem}.reviewed{path.suffix}")


def rel(path):
    return str(Path(path).as_posix())


def split_targets(value):
    return ",".join(part.strip() for part in str(value or "").split(",") if part.strip())


def as_bool_text(value):
    return "yes" if value else "no"


def checkpoint_action(row):
    decision = str(row.get("human_decision") or "").strip()
    proposed_action, status = CHECKPOINT_DECISION_MAP.get(decision, ("invalid_or_unmapped_decision", "blocked"))
    return {
        "task_type": "structural_review_checkpoint_candidates",
        "key": str(row.get("node_id") or "").strip(),
        "label": str(row.get("label") or "").strip(),
        "human_decision": decision,
        "proposed_action": proposed_action,
        "application_status": status,
        "manual_update_required": as_bool_text(status == "manual_update_required"),
        "parent_task_id": str(row.get("parent_task_id") or "").strip(),
        "target_ids": "",
        "current_type": str(row.get("current_type") or "").strip(),
        "recommended_action": str(row.get("recommended_action") or "").strip(),
        "evidence_anchor_count": str(row.get("evidence_anchor_count") or "").strip(),
        "human_notes": str(row.get("human_notes") or "").strip(),
    }


def gateway_action(row):
    decision = str(row.get("human_decision") or "").strip()
    proposed_action, status = GATEWAY_DECISION_MAP.get(decision, ("invalid_or_unmapped_decision", "blocked"))
    return {
        "task_type": "structural_gateway_branch_gaps",
        "key": str(row.get("gateway_id") or "").strip(),
        "label": str(row.get("gateway_label") or "").strip(),
        "human_decision": decision,
        "proposed_action": proposed_action,
        "application_status": status,
        "manual_update_required": as_bool_text(status == "manual_update_required"),
        "parent_task_id": "",
        "target_ids": split_targets(row.get("candidate_branch_target_ids")),
        "current_type": "DecisionGateway",
        "recommended_action": str(row.get("recommended_action") or "").strip(),
        "evidence_anchor_count": str(row.get("evidence_anchor_count") or "").strip(),
        "human_notes": str(row.get("human_notes") or "").strip(),
    }


def build_actions(review_dir):
    checkpoint_input = review_dir / "structural_review_checkpoint_candidates.csv"
    gateway_input = review_dir / "structural_gateway_branch_gaps.csv"
    checkpoint_reviewed = reviewed_path(checkpoint_input)
    gateway_reviewed = reviewed_path(gateway_input)

    rows = []
    source_files = []
    for task_type, path, builder in [
        ("structural_review_checkpoint_candidates", checkpoint_reviewed, checkpoint_action),
        ("structural_gateway_branch_gaps", gateway_reviewed, gateway_action),
    ]:
        present = path.exists() and path.stat().st_size > 0
        reviewed_rows = read_csv(path) if present else []
        source_files.append({"task_type": task_type, "reviewed_file": rel(path), "present": present, "rows": len(reviewed_rows)})
        rows.extend(builder(row) for row in reviewed_rows)
    return rows, source_files


def status_from_preflight(preflight, action_rows):
    if not preflight:
        return "blocked_missing_structural_review_preflight"
    if int(preflight.get("error_count") or 0) > 0 or preflight.get("overall_status") == "FAIL":
        return "blocked_by_validation_errors"
    if preflight.get("present_files") == 0:
        return "pending_optional_returns"
    if not action_rows:
        return "pending_optional_returns"
    if any(row.get("application_status") == "blocked" for row in action_rows):
        return "blocked_by_unmapped_decisions"
    return "dry_run_plan_ready"


def build_payload(exp_dir):
    exp_dir = Path(exp_dir)
    release_dir = exp_dir / "06_release"
    review_dir = exp_dir / "05_review"
    preflight_path = release_dir / "structural_review_return_preflight.json"
    preflight = read_json(preflight_path, {}) or {}
    action_rows, source_files = build_actions(review_dir)

    status = status_from_preflight(preflight, action_rows)
    decision_counts = Counter(row.get("human_decision") or "" for row in action_rows)
    application_counts = Counter(row.get("application_status") or "" for row in action_rows)
    manual_update_count = sum(1 for row in action_rows if row.get("manual_update_required") == "yes")
    no_change_count = application_counts.get("no_change", 0)
    discussion_count = application_counts.get("discussion_required", 0)
    blocked_count = application_counts.get("blocked", 0)

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "overall_status": status,
        "claim_status": "optional_structural_review_application_dry_run_not_paper_evidence",
        "does_modify_kg": False,
        "preflight": {
            "path": rel(preflight_path),
            "overall_status": preflight.get("overall_status"),
            "present_files": preflight.get("present_files"),
            "valid_files": preflight.get("valid_files"),
            "error_count": preflight.get("error_count"),
            "warning_count": preflight.get("warning_count"),
        },
        "source_files": source_files,
        "summary": {
            "action_rows": len(action_rows),
            "manual_update_required": manual_update_count,
            "no_change": no_change_count,
            "discussion_required": discussion_count,
            "blocked": blocked_count,
            "decision_counts": dict(sorted(decision_counts.items())),
            "application_status_counts": dict(sorted(application_counts.items())),
        },
        "actions": action_rows,
        "outputs": {
            "json": str(release_dir / "structural_review_application_plan.json"),
            "md": str(release_dir / "structural_review_application_plan.md"),
            "actions_csv": str(review_dir / "structural_review_application_actions.csv"),
        },
    }


def render_report(payload):
    summary = payload["summary"]
    lines = [
        "# CAPE-KG Structural Review Application Plan",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Overall status: `{payload['overall_status']}`",
        f"Claim status: `{payload['claim_status']}`",
        "",
        "This is a dry-run application plan for optional structural-review returns. It does not modify the KG.",
        "",
        "## Summary",
        "",
        "| Item | Value |",
        "|---|---:|",
        f"| Reviewed action rows | {summary['action_rows']} |",
        f"| Manual update required | {summary['manual_update_required']} |",
        f"| No-change decisions | {summary['no_change']} |",
        f"| Discussion required | {summary['discussion_required']} |",
        f"| Blocked rows | {summary['blocked']} |",
        "",
        "## Preflight",
        "",
        "| Item | Value |",
        "|---|---:|",
    ]
    for key, value in payload["preflight"].items():
        lines.append(f"| {key} | {value} |")
    lines += [
        "",
        "## Source Files",
        "",
        "| task_type | reviewed_file | present | rows |",
        "|---|---|---:|---:|",
    ]
    for row in payload["source_files"]:
        lines.append(f"| {row['task_type']} | `{row['reviewed_file']}` | {row['present']} | {row['rows']} |")

    if payload["actions"]:
        lines += [
            "",
            "## Proposed Actions",
            "",
            "| task_type | key | decision | proposed_action | status | target_ids |",
            "|---|---|---|---|---|---|",
        ]
        for row in payload["actions"][:100]:
            target_ids = row.get("target_ids") or ""
            lines.append(
                f"| {row['task_type']} | `{row['key']}` | `{row['human_decision']}` | "
                f"`{row['proposed_action']}` | `{row['application_status']}` | `{target_ids}` |"
            )
        if len(payload["actions"]) > 100:
            lines.append(f"| ... | ... | ... | ... | ... | {len(payload['actions']) - 100} more rows in CSV |")
    else:
        lines += [
            "",
            "## Proposed Actions",
            "",
            "No optional structural review returns have been provided yet, so there are no application actions.",
        ]

    lines += [
        "",
        "## Decision Mapping",
        "",
        "| reviewed decision | dry-run effect |",
        "|---|---|",
        "| `accept_review_checkpoint` | propose adding/retyping a ReviewCheckpoint or related checkpoint link |",
        "| `merge_with_existing_review` | propose merging with an existing review checkpoint |",
        "| `keep_current_type` | no KG change |",
        "| `reject_candidate` | no KG change |",
        "| `add_branches_to` | propose adding explicit branch targets only with source evidence |",
        "| `split_gateway` | propose splitting an overloaded gateway |",
        "| `keep_gateway_without_branch` | no KG change |",
        "| `reject_gateway` | no KG change |",
        "| `needs_discussion` | discussion required before any KG change |",
        "",
        "## Next Step",
        "",
        "1. Complete optional structural reviewed CSV files only if structural repair evidence is needed.",
        "2. Run `scripts/validate_cape_structural_review_returns.py`.",
        "3. Run this script to generate the dry-run application plan.",
        "4. Apply KG changes only after explicit review of the proposed actions.",
        "",
    ]
    return "\n".join(lines)


def run(args):
    payload = build_payload(args.experiment_dir)
    outputs = payload["outputs"]
    write_json(outputs["json"], payload)
    write_text(outputs["md"], render_report(payload))
    write_csv(outputs["actions_csv"], payload["actions"], ACTION_FIELDS)
    print(json.dumps({
        "overall_status": payload["overall_status"],
        "action_rows": payload["summary"]["action_rows"],
        "manual_update_required": payload["summary"]["manual_update_required"],
        "outputs": outputs,
    }, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
