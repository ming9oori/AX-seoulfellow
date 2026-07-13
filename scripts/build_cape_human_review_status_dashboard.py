#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a compact Korean status dashboard for CAPE-KG human review gates."""

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
MINIMUM_RETURN_TASK_TYPES = {"human_gold_annotation", "human_gold_adjudication"}

NEXT_ACTION_FIELDS = [
    "priority",
    "actor",
    "objective",
    "open_file",
    "save_as",
    "command",
    "unlocks",
    "claim_note",
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


def as_int(value, default=0):
    try:
        if value in ("", None):
            return default
        return int(float(value))
    except Exception:
        return default


def present(value):
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"yes", "true", "1", "present"}


def present_text(value):
    return "yes" if present(value) else "no"


def pct(done, total):
    done = as_int(done)
    total = as_int(total)
    if total <= 0:
        return "n/a"
    return f"{done / total:.1%}"


def rel(path):
    return str(Path(path).as_posix())


def file_state(path):
    path = Path(path)
    return {
        "path": rel(path),
        "exists": path.exists(),
        "bytes": path.stat().st_size if path.exists() else 0,
    }


def first_batch_rows(return_rows):
    return [
        row
        for row in return_rows
        if row.get("task_type") == "human_gold_annotation"
        and row.get("batch_or_group") == "full_120_priority_batch_001"
    ]


def get_return_row(return_rows, task_type):
    for row in return_rows:
        if row.get("task_type") == task_type:
            return row
    return {}


def count_rows(rows, predicate):
    return sum(1 for row in rows if predicate(row))


def gold_sampling_summary(exp_dir):
    exp_dir = Path(exp_dir)
    report_path = exp_dir / "06_release/gold_sampling_coverage_report.json"
    data = read_json(report_path, {}) or {}
    policy = data.get("selection_policy") or {}
    coverage = data.get("coverage_summary") or {}
    return {
        "claim_status": data.get("claim_status"),
        "report_json": rel(report_path),
        "report_markdown": rel(exp_dir / "06_release/gold_sampling_coverage_report.md"),
        "selected_chunks": as_int(policy.get("selected_chunk_count")),
        "minimum_gate_target_chunks": as_int(policy.get("minimum_gate_target_chunks"), 100),
        "batch_count": as_int(policy.get("batch_count")),
        "batch_size": as_int(policy.get("batch_size")),
        "candidate_edges": as_int(coverage.get("priority_100_candidate_edges")),
        "full_120_candidate_edges": as_int(coverage.get("full_120_candidate_edges")),
        "candidate_edge_coverage": float(coverage.get("priority_100_candidate_edge_coverage_of_full120") or 0.0),
        "active_review_coverage": float(coverage.get("priority_100_active_review_chunk_coverage_of_full120") or 0.0),
        "high_impact_coverage": float(coverage.get("priority_100_high_impact_chunk_coverage_of_full120") or 0.0),
        "not_gold_until": policy.get("not_gold_until"),
    }


def latest_bundle(latest_index, release_manifest, bundle_key):
    current = latest_index.get("current") or {}
    legacy = latest_index.get("current_bundles") or {}
    manifest_key = "internal_bundle" if bundle_key == "internal" else "public_safe_bundle"
    legacy_key = "internal" if bundle_key == "internal" else "public_safe"
    return (
        current.get(manifest_key)
        or legacy.get(legacy_key)
        or release_manifest.get(manifest_key)
        or {}
    )


def build_progress_cards(payload):
    return [
        {
            "id": "required_returns",
            "label": "Minimum paper-gate return files",
            "done": payload["summary"]["minimum_return_files_present"],
            "target": payload["summary"]["minimum_return_files_total"],
            "percent": pct(
                payload["summary"]["minimum_return_files_present"],
                payload["summary"]["minimum_return_files_total"],
            ),
            "status": "pending_human_returns",
            "next": "annotation/adjudication reviewed file 11개를 정확한 filename으로 저장",
        },
        {
            "id": "annotation_reviewed_files",
            "label": "A/B annotation reviewed files",
            "done": payload["summary"]["annotation_reviewed_files_present"],
            "target": payload["summary"]["annotation_reviewed_files_total"],
            "percent": pct(
                payload["summary"]["annotation_reviewed_files_present"],
                payload["summary"]["annotation_reviewed_files_total"],
            ),
            "status": "pending_two_annotator_returns",
            "next": "priority batch 001-005를 annotator A/B가 독립 검수",
        },
        {
            "id": "paired_iaa_chunks",
            "label": "IAA paired chunks",
            "done": payload["summary"]["paired_completed_chunks"],
            "target": 100,
            "percent": pct(payload["summary"]["paired_completed_chunks"], 100),
            "status": "pending_iaa",
            "next": "A/B reviewed JSONL import 후 IAA 재계산",
        },
        {
            "id": "adjudicated_chunks",
            "label": "Adjudicated gold chunks",
            "done": payload["summary"]["adjudicated_chunks"],
            "target": 100,
            "percent": pct(payload["summary"]["adjudicated_chunks"], 100),
            "status": "pending_adjudication",
            "next": "adjudication_edited.jsonl 완료 및 import",
        },
        {
            "id": "gold_items",
            "label": "Gold node/edge/evidence items",
            "done": payload["summary"]["gold_item_count"],
            "target": 500,
            "percent": pct(payload["summary"]["gold_item_count"], 500),
            "status": "pending_human_gold_items",
            "next": "adjudicated node/edge/evidence item 500개 이상 확보",
        },
        {
            "id": "mapping_priority_groups",
            "label": "Mapping expert priority groups",
            "done": payload["summary"]["mapping_complete_priority_groups"],
            "target": payload["summary"]["mapping_expected_priority_groups"],
            "percent": pct(
                payload["summary"]["mapping_complete_priority_groups"],
                payload["summary"]["mapping_expected_priority_groups"],
            ),
            "status": "pending_mapping_expert_review",
            "next": "top20 source-task-standard group의 Top-5 후보 검수",
        },
        {
            "id": "crosswalk_source_groups",
            "label": "NCS-PCF crosswalk source groups",
            "done": payload["summary"]["crosswalk_complete_source_groups"],
            "target": payload["summary"]["crosswalk_expected_source_tasks"],
            "percent": pct(
                payload["summary"]["crosswalk_complete_source_groups"],
                payload["summary"]["crosswalk_expected_source_tasks"],
            ),
            "status": "pending_crosswalk_expert_review",
            "next": "NCS-PCF crosswalk 후보 pair utility 검수",
        },
        {
            "id": "active_review_effort_rows",
            "label": "Active-review effort rows",
            "done": payload["summary"]["active_review_effort_reviewed_rows"],
            "target": payload["summary"]["active_review_effort_expected_rows"],
            "percent": pct(
                payload["summary"]["active_review_effort_reviewed_rows"],
                payload["summary"]["active_review_effort_expected_rows"],
            ),
            "status": "pending_human_effort_timing",
            "next": "review_seconds, decision, corrected_error 열 채우기",
        },
    ]


def build_payload(exp_dir):
    exp_dir = Path(exp_dir)
    release_dir = exp_dir / "06_release"
    review_dir = exp_dir / "05_review"
    gold_dir = exp_dir / "01_data/gold_annotation"
    mapping_dir = exp_dir / "01_data/mapping_review"
    crosswalk_dir = exp_dir / "01_data/crosswalk_review"

    claim_gate = read_json(release_dir / "claim_gate_report.json", {}) or {}
    preflight = read_json(release_dir / "human_review_return_preflight.json", {}) or {}
    master_checklist = read_json(release_dir / "human_review_master_checklist_ko.json", {}) or {}
    action_plan = read_json(release_dir / "human_gate_action_plan.json", {}) or {}
    human_gold = read_json(exp_dir / "04_evaluation/human_gold_validation_summary.json", {}) or {}
    mapping_progress = read_json(release_dir / "mapping_review_progress_summary.json", {}) or {}
    active_effort = read_json(exp_dir / "04_evaluation/active_review_human_effort_metrics.json", {}) or {}
    completion = read_json(release_dir / "submission_completion_audit_ko.json", {}) or {}
    pre_human = read_json(release_dir / "pre_human_handoff_validation.json", {}) or {}
    expansion = read_json(gold_dir / "annotation_expansion_manifest.json", {}) or {}
    latest_index = read_json(release_dir / "latest_release_bundle_index.json", {}) or {}
    release_manifest = read_json(release_dir / "release_bundle_manifest.json", {}) or {}
    latest_internal = latest_bundle(latest_index, release_manifest, "internal")
    latest_public_safe = latest_bundle(latest_index, release_manifest, "public_safe")
    sampling = gold_sampling_summary(exp_dir)

    return_rows = read_csv(review_dir / "human_review_master_return_files.csv")
    required_rows = [row for row in return_rows if row.get("requiredness") == "required"]
    minimum_rows = [
        row
        for row in required_rows
        if row.get("required_for_minimum") == "yes"
        or (not row.get("required_for_minimum") and row.get("task_type") in MINIMUM_RETURN_TASK_TYPES)
    ]
    optional_strong_rows = [row for row in required_rows if row not in minimum_rows]
    optional_rows = [row for row in return_rows if row.get("requiredness") != "required"]
    annotation_rows = [row for row in required_rows if row.get("task_type") == "human_gold_annotation"]
    present_required = count_rows(required_rows, lambda row: present(row.get("present")))
    present_minimum = count_rows(minimum_rows, lambda row: present(row.get("present")))
    present_optional_strong = count_rows(optional_strong_rows, lambda row: present(row.get("present")))
    present_optional_structural = count_rows(optional_rows, lambda row: present(row.get("present")))
    present_annotation = count_rows(annotation_rows, lambda row: present(row.get("present")))

    annotation_preflight = preflight.get("annotation_returns") or {}
    adjudication_preflight = preflight.get("adjudication_return") or {}
    mapping_preflight = preflight.get("mapping_return") or {}
    crosswalk_preflight = preflight.get("crosswalk_return") or {}
    active_preflight = preflight.get("active_review_effort_return") or {}
    thresholds = action_plan.get("minimum_thresholds") or {}

    batch_rows = read_csv(review_dir / "human_gold_batches/full_120_batch_assignment_overview.csv")
    mapping_priority_rows = read_csv(review_dir / "mapping_review_next_20_groups.csv")
    first_rows = first_batch_rows(required_rows)
    mapping_row = get_return_row(required_rows, "mapping_expert_review")
    crosswalk_row = get_return_row(required_rows, "crosswalk_expert_review")
    active_row = get_return_row(required_rows, "active_review_human_effort")
    adjudication_row = get_return_row(required_rows, "human_gold_adjudication")

    commands = {
        "verify_handoff_checksums": "sha256sum -c experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/human_review_handoff_checksums.sha256",
        "validate_required_returns": "python3 scripts/validate_cape_human_review_returns.py --experiment-dir experiments/cape_kg_eacl_20260627",
        "dry_run_human_return_apply": "PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=0 bash scripts/run_cape_human_return_apply.sh",
        "apply_human_returns": "PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=1 bash scripts/run_cape_human_return_apply.sh",
        "validate_pre_human_handoff": "python3 scripts/validate_cape_pre_human_handoff.py --experiment-dir experiments/cape_kg_eacl_20260627 --outputs-dir outputs",
        "verify_release_checksums": "sha256sum -c experiments/cape_kg_eacl_20260627/06_release/release_bundle_checksums.sha256",
    }

    summary = {
        "claim_gate_overall_status": claim_gate.get("overall_status"),
        "claim_gate_required_failure_count": claim_gate.get("required_failure_count"),
        "claim_gate_optional_failure_count": claim_gate.get("optional_failure_count"),
        "pre_human_validation_source_json": rel(release_dir / "pre_human_handoff_validation.json"),
        "pre_human_validation_source_md": rel(release_dir / "pre_human_handoff_validation.md"),
        "completion_status": completion.get("overall_completion_status"),
        "latest_release_stamp": latest_index.get("stamp") or release_manifest.get("stamp"),
        "latest_internal_bundle": latest_internal.get("path"),
        "latest_internal_bundle_sha256": latest_internal.get("sha256"),
        "latest_public_safe_bundle": latest_public_safe.get("path"),
        "latest_public_safe_bundle_sha256": latest_public_safe.get("sha256"),
        "required_return_files_total": len(required_rows),
        "required_return_files_present": present_required,
        "required_return_files_missing": len(required_rows) - present_required,
        "minimum_return_files_total": len(minimum_rows),
        "minimum_return_files_present": present_minimum,
        "minimum_return_files_missing": len(minimum_rows) - present_minimum,
        "optional_strong_return_files_total": len(optional_strong_rows),
        "optional_strong_return_files_present": present_optional_strong,
        "optional_strong_return_files_missing": len(optional_strong_rows) - present_optional_strong,
        "optional_return_files_total": len(optional_rows),
        "optional_return_files_present": present_optional_structural,
        "optional_structural_return_files_total": len(optional_rows),
        "optional_structural_return_files_present": present_optional_structural,
        "optional_structural_return_files_missing": len(optional_rows) - present_optional_structural,
        "master_return_files_total": len(return_rows),
        "master_return_files_present": present_required + present_optional_structural,
        "master_return_files_missing": len(return_rows) - present_required - present_optional_structural,
        "annotation_reviewed_files_total": len(annotation_rows),
        "annotation_reviewed_files_present": present_annotation,
        "annotation_reviewed_rows": annotation_preflight.get("reviewed_rows", 0),
        "paired_completed_chunks": annotation_preflight.get("paired_completed_chunks", 0),
        "adjudicated_chunks": human_gold.get("completed_adjudicated_chunks", 0),
        "gold_item_count": human_gold.get("gold_item_count_for_readiness", 0),
        "adjudication_reviewed_file_present": bool(adjudication_preflight.get("present")),
        "mapping_expected_priority_groups": mapping_preflight.get("expected_priority_groups")
        or thresholds.get("mapping_review_minimum")
        or 20,
        "mapping_complete_priority_groups": mapping_preflight.get("complete_top5_groups", 0),
        "mapping_candidate_rows": mapping_progress.get("candidate_rows", 0),
        "mapping_pending_rows": mapping_progress.get("pending_rows", 0),
        "mapping_pending_source_groups": mapping_progress.get("pending_source_groups", 0),
        "crosswalk_expected_rows": crosswalk_preflight.get("expected_rows", 0),
        "crosswalk_completed_rows": crosswalk_preflight.get("completed_rows", 0),
        "crosswalk_expected_source_tasks": crosswalk_preflight.get("expected_source_tasks", 0),
        "crosswalk_complete_source_groups": crosswalk_preflight.get("complete_source_groups", 0),
        "crosswalk_reviewed_file_present": bool(crosswalk_preflight.get("present")),
        "active_review_effort_expected_rows": active_preflight.get("expected_rows")
        or active_effort.get("pooled_rows")
        or 0,
        "active_review_effort_reviewed_rows": active_preflight.get("completed_review_rows", 0),
        "active_review_effort_reviewed_file_present": bool(active_preflight.get("present")),
        "optional_strong_package": expansion.get("strong_resegmented_package"),
        "optional_strong_review_units": expansion.get("strong_resegmented_chunk_count"),
        "optional_strong_claim_status": expansion.get("strong_resegmented_claim_status"),
    }

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "claim_status": "human_review_status_dashboard_ready_pending_returns",
        "priority_100_sampling": sampling,
        "summary": summary,
        "progress_cards": [],
        "next_action_rows": [],
        "first_annotation_batch": batch_rows[0] if batch_rows else {},
        "first_annotation_return_files": first_rows,
        "mapping_priority_preview": mapping_priority_rows[:5],
        "required_return_files": required_rows,
        "optional_return_files": optional_rows,
        "commands": commands,
        "do_not_claim": [
            "CAPE-KG가 baseline보다 human-gold 기준으로 우수하다는 최종 성능 claim",
            "NCS/PCF mapping P@K, MRR, nDCG, expert accept-rate claim",
            "NCS-PCF crosswalk accept-rate, utility, ranking claim",
            "active-review efficiency가 사람 검수 비용을 줄였다는 최종 claim",
            "strong_resegmented_342_max18이 342개 adjudicated gold chunk로 완료되었다는 claim",
        ],
        "source_files": {
            "claim_gate_report": file_state(release_dir / "claim_gate_report.json"),
            "human_review_return_preflight": file_state(release_dir / "human_review_return_preflight.json"),
            "human_review_master_checklist": file_state(release_dir / "human_review_master_checklist_ko.json"),
            "human_gate_action_plan": file_state(release_dir / "human_gate_action_plan.json"),
            "human_review_first_batch_execution_card": file_state(
                review_dir / "human_review_first_batch_execution_card_ko.md"
            ),
            "human_review_first_batch_execution_card_json": file_state(
                review_dir / "human_review_first_batch_execution_card.json"
            ),
            "human_review_role_quickstart": file_state(
                review_dir / "human_review_role_quickstart_cards_ko.md"
            ),
            "human_review_role_quickstart_json": file_state(
                review_dir / "human_review_role_quickstart_cards.json"
            ),
            "human_review_role_quickstart_csv": file_state(
                review_dir / "human_review_role_quickstart_cards.csv"
            ),
            "human_review_master_return_files": file_state(review_dir / "human_review_master_return_files.csv"),
            "gold_sampling_coverage_report": file_state(release_dir / "gold_sampling_coverage_report.json"),
            "gold_sampling_selected_chunks": file_state(review_dir / "gold_sampling_priority100_selected_chunks.csv"),
            "batch_assignment_overview": file_state(review_dir / "human_gold_batches/full_120_batch_assignment_overview.csv"),
            "mapping_priority_groups": file_state(review_dir / "mapping_review_next_20_groups.csv"),
            "mapping_review_items": file_state(mapping_dir / "mapping_review_items.jsonl"),
            "crosswalk_review_items": file_state(crosswalk_dir / "crosswalk_review_items.jsonl"),
            "crosswalk_review_protocol": file_state(crosswalk_dir / "crosswalk_review_protocol.md"),
            "active_review_effort_template": file_state(review_dir / "active_review_human_effort_template.csv"),
            "latest_release_bundle_index": file_state(release_dir / "latest_release_bundle_index.json"),
            "release_bundle_manifest": file_state(release_dir / "release_bundle_manifest.json"),
        },
        "outputs": {
            "markdown": str(release_dir / "human_review_status_dashboard_ko.md"),
            "json": str(release_dir / "human_review_status_dashboard_ko.json"),
            "next_actions_csv": str(review_dir / "human_review_status_next_actions.csv"),
            "first_batch_card_markdown": str(review_dir / "human_review_first_batch_execution_card_ko.md"),
            "first_batch_card_json": str(review_dir / "human_review_first_batch_execution_card.json"),
            "role_quickstart_markdown": str(review_dir / "human_review_role_quickstart_cards_ko.md"),
            "role_quickstart_json": str(review_dir / "human_review_role_quickstart_cards.json"),
            "role_quickstart_csv": str(review_dir / "human_review_role_quickstart_cards.csv"),
        },
    }
    payload["progress_cards"] = build_progress_cards(payload)

    next_actions = [
        {
            "priority": 1,
            "actor": "coordinator",
            "objective": "handoff bundle이 손상되지 않았는지 확인",
            "open_file": str(release_dir / "human_review_handoff/human_review_handoff_checksums.sha256"),
            "save_as": "",
            "command": commands["verify_handoff_checksums"],
            "unlocks": "review package distribution",
            "claim_note": "checksum 통과는 gold evidence가 아니라 handoff integrity evidence입니다.",
        }
    ]
    for row in first_rows:
        next_actions.append(
            {
                "priority": len(next_actions) + 1,
                "actor": row.get("owner"),
                "objective": "priority batch 001 독립 annotation",
                "open_file": row.get("input_file"),
                "save_as": row.get("reviewed_file"),
                "command": "",
                "unlocks": "first 20 paired chunks for IAA after both annotators return",
                "claim_note": "A/B 둘 다 완료되어야 IAA와 adjudication으로 진행됩니다.",
            }
        )
    next_actions.extend(
        [
            {
                "priority": len(next_actions) + 1,
                "actor": "coordinator",
                "objective": "반환 파일 preflight",
                "open_file": str(review_dir / "human_review_master_return_files.csv"),
                "save_as": str(release_dir / "human_review_return_preflight.md"),
                "command": commands["validate_required_returns"],
                "unlocks": "safe dry-run/import decision",
                "claim_note": "preflight가 PASS/partial이 아니면 import하지 않습니다.",
            },
            {
                "priority": len(next_actions) + 2,
                "actor": "coordinator",
                "objective": "사람 반환 파일 dry-run 반영",
                "open_file": "",
                "save_as": str(release_dir / "human_return_apply_last_run.md"),
                "command": commands["dry_run_human_return_apply"],
                "unlocks": "apply readiness check",
                "claim_note": "dry-run은 산출물 적용 전 안전 점검입니다.",
            },
            {
                "priority": len(next_actions) + 3,
                "actor": "adjudicator",
                "objective": "A/B disagreement adjudication",
                "open_file": adjudication_row.get("input_file"),
                "save_as": adjudication_row.get("reviewed_file"),
                "command": "",
                "unlocks": "100+ adjudicated chunks, 500+ gold items, proposed human-gold scoring",
                "claim_note": "adjudication import 전까지 final gold claim은 보류합니다.",
            },
            {
                "priority": len(next_actions) + 4,
                "actor": "mapping_expert",
                "objective": "NCS/PCF top20 priority group expert review",
                "open_file": mapping_row.get("input_file"),
                "save_as": mapping_row.get("reviewed_file"),
                "command": "",
                "unlocks": "mapping P@K/MRR/nDCG/expert accept-rate claim",
                "claim_note": "전문가 검수 전 mapping 성능은 후보 생성 결과로만 표현합니다.",
            },
            {
                "priority": len(next_actions) + 5,
                "actor": "crosswalk_expert",
                "objective": "NCS-PCF crosswalk 후보 utility 검수",
                "open_file": crosswalk_row.get("input_file"),
                "save_as": crosswalk_row.get("reviewed_file"),
                "command": "",
                "unlocks": "NCS-PCF crosswalk accept-rate/utility/ranking claim",
                "claim_note": "전문가 검수 전 crosswalk 결과는 bridge-supported candidate로만 표현합니다.",
            },
            {
                "priority": len(next_actions) + 6,
                "actor": "active_reviewer",
                "objective": "active-review effort/timing 기록",
                "open_file": active_row.get("input_file"),
                "save_as": active_row.get("reviewed_file"),
                "command": "",
                "unlocks": "active review efficiency claim",
                "claim_note": "review_seconds와 corrected_error가 없으면 efficiency claim을 하지 않습니다.",
            },
        ]
    )
    payload["next_action_rows"] = next_actions
    return payload


def md_table(headers, rows):
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        values = [str(row.get(header, "")).replace("|", "\\|") for header in headers]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def render_dashboard(payload):
    summary = payload["summary"]
    lines = [
        "# CAPE-KG 사람 검수 상태 대시보드",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Experiment: `{payload['experiment_dir']}`",
        "",
        "이 문서는 긴 체크리스트를 대체하지 않고, 현재 human gate 진행 상태와 다음에 열 파일만 빠르게 보기 위한 상태판입니다.",
        "",
        "## 현재 결론",
        "",
        f"- Claim gate: `{summary.get('claim_gate_overall_status')}`",
        f"- Required claim-gate failures: {summary.get('claim_gate_required_failure_count')}",
        f"- Optional claim-gate failures: {summary.get('claim_gate_optional_failure_count')}",
        f"- Pre-human validation source: `{summary.get('pre_human_validation_source_md')}`",
        f"- Latest release stamp: `{summary.get('latest_release_stamp')}`",
        f"- Latest internal bundle: `{summary.get('latest_internal_bundle')}`",
        f"- Latest internal SHA256: `{summary.get('latest_internal_bundle_sha256')}`",
        f"- Latest public-safe bundle: `{summary.get('latest_public_safe_bundle')}`",
        f"- Latest public-safe SHA256: `{summary.get('latest_public_safe_bundle_sha256')}`",
        f"- Minimum paper-gate return files: {summary.get('minimum_return_files_present')}/{summary.get('minimum_return_files_total')}",
        f"- Optional/strong claim return files: {summary.get('optional_strong_return_files_present')}/{summary.get('optional_strong_return_files_total')}",
        f"- Required claim/human return files: {summary.get('required_return_files_present')}/{summary.get('required_return_files_total')}",
        f"- Optional structural review files: {summary.get('optional_structural_return_files_present')}/{summary.get('optional_structural_return_files_total')}",
        f"- All master return files: {summary.get('master_return_files_present')}/{summary.get('master_return_files_total')}",
        f"- 현재 완료 판단: `{summary.get('completion_status')}`",
        "",
        "## Priority-100 선정 근거",
        "",
        "| item | value |",
        "| --- | ---: |",
        f"| Selected chunks | {payload['priority_100_sampling'].get('selected_chunks')}/{payload['priority_100_sampling'].get('minimum_gate_target_chunks')} |",
        f"| Batch count / size | {payload['priority_100_sampling'].get('batch_count')} / {payload['priority_100_sampling'].get('batch_size')} |",
        f"| Candidate edges covered | {payload['priority_100_sampling'].get('candidate_edges')}/{payload['priority_100_sampling'].get('full_120_candidate_edges')} |",
        f"| Candidate-edge coverage | {payload['priority_100_sampling'].get('candidate_edge_coverage'):.6f} |",
        f"| Active-review chunk coverage | {payload['priority_100_sampling'].get('active_review_coverage'):.6f} |",
        f"| High-impact chunk coverage | {payload['priority_100_sampling'].get('high_impact_coverage'):.6f} |",
        f"| Claim status | `{payload['priority_100_sampling'].get('claim_status')}` |",
        f"| Report | `{payload['priority_100_sampling'].get('report_markdown')}` |",
        "",
        "이 선정 근거는 사람 검수 우선순위와 coverage를 설명하는 운영 근거입니다. human-gold 결과나 성능 claim은 아닙니다.",
        "",
        "## 진행 상태",
        "",
        md_table(["id", "label", "done", "target", "percent", "status", "next"], payload["progress_cards"]),
        "",
        "## 즉시 열 파일",
        "",
        f"- 첫 배치 간편 실행 카드: `{payload['outputs']['first_batch_card_markdown']}`",
        f"- 역할별 quickstart: `{payload['outputs']['role_quickstart_markdown']}`",
        "",
        "가장 먼저 진행할 annotation batch는 `full_120_priority_batch_001`입니다.",
        "",
        md_table(
            ["owner", "batch_or_group", "expected_rows", "input_file", "reviewed_file", "present", "status"],
            payload["first_annotation_return_files"],
        ),
        "",
        "Mapping expert는 아래 우선순위 group부터 검수합니다.",
        "",
        md_table(
            ["priority_score", "standard", "source_label", "pending_top5_rows", "top_score", "score_gap"],
            payload["mapping_priority_preview"],
        ),
        "",
        "## 다음 행동 CSV",
        "",
        f"- CSV: `{payload['outputs']['next_actions_csv']}`",
        "",
        md_table(["priority", "actor", "objective", "open_file", "save_as", "unlocks"], payload["next_action_rows"]),
        "",
        "## 다음 명령",
        "",
    ]
    for name, command in payload["commands"].items():
        lines += [f"### {name}", "", "```bash", command, "```", ""]
    lines += [
        "## 아직 claim하면 안 되는 것",
        "",
    ]
    for item in payload["do_not_claim"]:
        lines.append(f"- {item}")
    lines += [
        "",
        "## Source Files",
        "",
        md_table(["path", "exists", "bytes"], list(payload["source_files"].values())),
        "",
        "## Output Files",
        "",
        f"- JSON: `{payload['outputs']['json']}`",
        f"- Markdown: `{payload['outputs']['markdown']}`",
        f"- Next actions CSV: `{payload['outputs']['next_actions_csv']}`",
        f"- First batch card: `{payload['outputs']['first_batch_card_markdown']}`",
        f"- First batch card JSON: `{payload['outputs']['first_batch_card_json']}`",
        f"- Role quickstart: `{payload['outputs']['role_quickstart_markdown']}`",
        f"- Role quickstart JSON: `{payload['outputs']['role_quickstart_json']}`",
        f"- Role quickstart CSV: `{payload['outputs']['role_quickstart_csv']}`",
        "",
    ]
    return "\n".join(lines)


def run(args):
    exp_dir = Path(args.experiment_dir)
    payload = build_payload(exp_dir)
    write_json(payload["outputs"]["json"], payload)
    write_csv(payload["outputs"]["next_actions_csv"], payload["next_action_rows"], NEXT_ACTION_FIELDS)
    write_text(payload["outputs"]["markdown"], render_dashboard(payload))
    print(json.dumps(payload["outputs"], ensure_ascii=False, indent=2))


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
