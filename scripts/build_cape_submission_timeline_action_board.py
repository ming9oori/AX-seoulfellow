#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a dated submission timeline and action board for the CAPE-KG EACL plan."""

import argparse
import csv
import json
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

from cape_pre_human_status import effective_prehuman_summary


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_PLAN_FILE = Path("AX_EACL_submission_review_revised_plan.md")
READY_STATUS = "submission_timeline_action_board_ready_not_submission_complete"
ARR_TARGET_DATE = date(2026, 8, 3)


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


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def rel(path):
    return Path(path).as_posix()


def file_state(path):
    path = Path(path)
    present = path.exists() and path.is_file()
    return {
        "path": rel(path),
        "exists": present,
        "bytes": path.stat().st_size if present else 0,
    }


def md_table(headers, rows):
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        values = []
        for header in headers:
            value = row.get(header, "")
            if isinstance(value, list):
                value = "<br>".join(str(v) for v in value)
            values.append(str(value).replace("|", "\\|").replace("\n", "<br>"))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def phase(phase_id, start, end, plan_tasks, current_status, evidence, blocking_gates, action_now, as_of):
    start_date = date.fromisoformat(start)
    end_date = date.fromisoformat(end)
    return {
        "phase_id": phase_id,
        "start_date": start,
        "end_date": end,
        "days_until_start": (start_date - as_of).days,
        "days_until_end": (end_date - as_of).days,
        "plan_tasks": plan_tasks,
        "current_status": current_status,
        "evidence": [file_state(path) for path in evidence],
        "missing_evidence_files": [
            rel(path)
            for path in evidence
            if not Path(path).exists() or not Path(path).is_file() or Path(path).stat().st_size == 0
        ],
        "blocking_gates": blocking_gates,
        "action_now": action_now,
    }


def action(action_id, workstream, due_date, priority, status, owner, required_for, evidence, next_action, as_of):
    due = date.fromisoformat(due_date)
    return {
        "action_id": action_id,
        "workstream": workstream,
        "due_date": due_date,
        "days_until_due": (due - as_of).days,
        "priority": priority,
        "status": status,
        "owner": owner,
        "required_for": required_for,
        "evidence": [file_state(path) for path in evidence],
        "missing_evidence_files": [
            rel(path)
            for path in evidence
            if not Path(path).exists() or not Path(path).is_file() or Path(path).stat().st_size == 0
        ],
        "next_action": next_action,
    }


def build_payload(exp_dir, plan_file):
    exp_dir = Path(exp_dir)
    release = exp_dir / "06_release"
    review = exp_dir / "05_review"
    evaluation = exp_dir / "04_evaluation"
    outputs = Path("outputs")

    generated = datetime.now(timezone.utc)
    as_of = generated.date()

    compliance = read_json(release / "eacl_plan_compliance_matrix.json", {}) or {}
    compliance_summary = compliance.get("summary") or {}
    validation = read_json(release / "pre_human_handoff_validation.json", {}) or {}
    effective_validation = effective_prehuman_summary(validation)
    claim_gate = read_json(release / "claim_gate_report.json", {}) or {}
    completion = read_json(release / "submission_completion_audit_ko.json", {}) or {}
    scorer = read_json(release / "post_human_scoring_readiness.json", {}) or {}
    returns = read_csv(review / "human_review_master_return_files.csv")
    next_actions = read_csv(review / "human_review_status_next_actions.csv")

    minimum_returns = [row for row in returns if row.get("required_for_minimum") == "yes"]
    optional_returns = [row for row in returns if row.get("required_for_minimum") != "yes"]
    optional_claim_returns = [row for row in optional_returns if row.get("requiredness") != "optional_structural"]
    optional_structural_returns = [row for row in optional_returns if row.get("requiredness") == "optional_structural"]
    present_minimum = sum(1 for row in minimum_returns if row.get("present") == "yes")
    present_optional = sum(1 for row in optional_returns if row.get("present") == "yes")
    present_optional_claim = sum(1 for row in optional_claim_returns if row.get("present") == "yes")
    present_optional_structural = sum(1 for row in optional_structural_returns if row.get("present") == "yes")

    phases = [
        phase(
            "A01_foundation_week",
            "2026-06-27",
            "2026-07-03",
            [
                "논문 title, task definition, related work 확정",
                "annotation guideline v1 작성",
                "30 chunk pilot annotation",
            ],
            "automatic_foundation_ready_pilot_human_pending",
            [
                plan_file,
                exp_dir / "01_data/annotation_guideline_v1.md",
                release / "method_novelty_positioning.md",
                release / "rq_evidence_matrix.md",
                release / "human_review_launch_checklist_ko.md",
            ],
            ["gold.completed_chunks", "gold.iaa"],
            "Pilot/foundation 문서는 준비됨. 실제 pilot 또는 priority batch annotation 반환이 필요함.",
            as_of,
        ),
        phase(
            "A02_minimum_gold_and_core_runs",
            "2026-07-04",
            "2026-07-12",
            [
                "100~150 chunk gold annotation",
                "B0/B1/B2 baseline 구현",
                "CAPE-KG minimal implementation",
            ],
            "automatic_llm_runs_ready_minimum_gold_pending",
            [
                release / "claim_gate_report.md",
                release / "paper_tables.md",
                evaluation / "actual_llm_silver_metrics.json",
                review / "human_review_master_return_files.csv",
            ],
            ["gold.completed_chunks", "gold.item_count", "gold.iaa"],
            "Baseline/proposed generation은 준비됨. 11개 minimum human-return file이 critical path.",
            as_of,
        ),
        phase(
            "A03_main_scoring_and_metrics",
            "2026-07-13",
            "2026-07-20",
            [
                "main experiments",
                "evidence span evaluation",
                "ontology conformance evaluation",
                "procedural consistency evaluation",
            ],
            "scorers_ready_human_gold_refresh_pending",
            [
                release / "post_human_scoring_readiness.md",
                evaluation / "human_gold_metrics.json",
                evaluation / "human_gold_span_iou_report.md",
                evaluation / "structural_evaluation_report.md",
                outputs / "12_rdf/cape_kg_shacl_validation_report.md",
            ],
            ["llm.proposed_human_gold_score"],
            "Human-gold import 후 scoring wrapper와 post-annotation refresh를 실행해야 main metric이 채워짐.",
            as_of,
        ),
        phase(
            "A04_ablation_analysis_writing",
            "2026-07-21",
            "2026-07-27",
            [
                "ablation",
                "error analysis",
                "paper writing",
            ],
            "diagnostic_tables_ready_final_claim_refresh_pending",
            [
                release / "paper_tables.md",
                exp_dir / "07_reports/error_analysis.md",
                exp_dir / "07_reports/eacl_paper_draft.md",
                release / "claim_language_guardrails.md",
                release / "reviewer_response_prep.md",
            ],
            ["gold.completed_chunks", "llm.proposed_human_gold_score"],
            "현재 paper draft와 diagnostic tables는 준비됨. human-gold 결과가 들어오면 final result language로 갱신해야 함.",
            as_of,
        ),
        phase(
            "A05_internal_review_and_submission_package",
            "2026-07-28",
            "2026-08-02",
            [
                "internal review",
                "reproducibility package",
                "final submission",
            ],
            "release_package_ready_not_submission_complete",
            [
                release / "eacl_submission_package_manifest.md",
                release / "latest_release_bundle_index.md",
                release / "release_bundle_checksums.sha256",
                release / "pre_human_handoff_validation.md",
            ],
            ["gold.completed_chunks", "gold.item_count", "gold.iaa", "llm.proposed_human_gold_score"],
            "Release bundle은 준비되어 있으나 submission-ready gate는 human-gold 완료 전까지 false.",
            as_of,
        ),
        phase(
            "A06_arr_submission_target",
            "2026-08-03",
            "2026-08-03",
            ["ARR submission"],
            "not_submission_ready_until_minimum_gates_pass",
            [
                release / "submission_completion_audit_ko.md",
                release / "eacl_plan_compliance_matrix.md",
                release / "claim_gate_report.md",
            ],
            ["gold.completed_chunks", "gold.item_count", "gold.iaa", "llm.proposed_human_gold_score"],
            "최소 human-gold gates와 proposed human-gold scoring이 PASS가 되기 전에는 제출 완료로 표시하지 않음.",
            as_of,
        ),
    ]

    actions = [
        action(
            "CP01_minimum_annotation_returns",
            "human_gold_annotation",
            "2026-07-12",
            "critical",
            "pending_human",
            "annotator_A_and_B",
            "minimum_accept",
            [review / "human_review_master_return_files.csv", release / "human_review_launch_checklist_ko.md"],
            "10개 priority batch A/B reviewed JSONL을 exact filename으로 반환한다.",
            as_of,
        ),
        action(
            "CP02_adjudication_return",
            "human_gold_adjudication",
            "2026-07-13",
            "critical",
            "pending_human",
            "adjudicator",
            "minimum_accept",
            [exp_dir / "01_data/gold_annotation/full_120/adjudication_draft.jsonl", release / "human_gate_action_plan.md"],
            "A/B annotation 반환 후 adjudication_edited.jsonl을 작성하고 import한다.",
            as_of,
        ),
        action(
            "CP03_iaa_and_human_gold_scoring",
            "human_gold_metrics",
            "2026-07-20",
            "critical",
            "pending_human_returns",
            "pipeline_after_returns",
            "minimum_accept",
            [release / "post_human_scoring_readiness.md", evaluation / "human_gold_metrics.json", evaluation / "human_gold_span_iou_metrics.json"],
            "검수 반환 import 후 IAA, node/edge/evidence/span metrics, P_cape_kg_actual scoring을 재계산한다.",
            as_of,
        ),
        action(
            "CP04_claim_safe_main_tables",
            "paper_tables",
            "2026-07-27",
            "critical",
            "automatic_scaffold_ready_human_values_pending",
            "paper_author",
            "minimum_accept",
            [release / "paper_tables.md", release / "claimable_main_table.md", release / "claim_language_guardrails.md"],
            "Human-gold metric이 채워진 뒤 silver/proxy diagnostic language를 final result language와 분리해 업데이트한다.",
            as_of,
        ),
        action(
            "CP05_release_and_validation_freeze",
            "submission_package",
            "2026-08-02",
            "critical",
            "release_ready_not_submission_complete",
            "pipeline",
            "minimum_accept",
            [release / "eacl_submission_package_manifest.md", release / "latest_release_bundle_index.md", release / "pre_human_handoff_validation.md"],
            "최종 결과 반영 후 release bundle, checksum, protocol lock, pre-human/final validation을 다시 실행한다.",
            as_of,
        ),
        action(
            "OP01_mapping_expert_review",
            "mapping_downstream",
            "2026-07-27",
            "strong_optional",
            "pending_expert_review",
            "mapping_expert",
            "strong_accept",
            [release / "mapping_review_progress_report.md", evaluation / "mapping_expert_metrics.json"],
            "Top-K NCS/PCF 후보를 expert review하고 P@K/MRR/nDCG/explanation quality를 재계산한다.",
            as_of,
        ),
        action(
            "OP02_crosswalk_expert_review",
            "ncs_pcf_crosswalk",
            "2026-07-27",
            "strong_optional",
            "pending_expert_review",
            "crosswalk_expert",
            "strong_accept",
            [exp_dir / "01_data/crosswalk_review/crosswalk_review_manifest.json", evaluation / "crosswalk_expert_metrics.json"],
            "Layer2-bridged NCS-PCF crosswalk 후보를 expert review하고 utility metrics를 재계산한다.",
            as_of,
        ),
        action(
            "OP03_active_review_effort",
            "active_review_efficiency",
            "2026-07-27",
            "strong_optional",
            "pending_human_effort",
            "active_review_effort_reviewer",
            "strong_accept",
            [release / "active_review_human_effort_plan.md", evaluation / "active_review_human_effort_metrics.json"],
            "active/uncertainty/random control effort sheet를 채워 review-efficiency claim을 검증한다.",
            as_of,
        ),
        action(
            "OP04_structural_checkpoint_review",
            "structural_review_checkpoint_candidates",
            "2026-07-27",
            "strong_optional",
            "pending_structural_reviewer",
            "structural_reviewer",
            "strong_accept",
            [
                release / "structural_review_action_plan.md",
                release / "structural_review_return_preflight.md",
                review / "structural_review_checkpoint_candidates.csv",
            ],
            "ReviewCheckpoint 후보를 구조 검수자가 확인하고 structural review returns를 반영한다.",
            as_of,
        ),
        action(
            "OP05_structural_gateway_branch_review",
            "structural_gateway_branch_gaps",
            "2026-07-27",
            "strong_optional",
            "pending_structural_reviewer",
            "structural_reviewer",
            "strong_accept",
            [
                release / "structural_review_action_plan.md",
                release / "structural_review_return_preflight.md",
                review / "structural_gateway_branch_gaps.csv",
            ],
            "Gateway branch gap 후보를 확인해 procedural consistency 보강 여부를 결정한다.",
            as_of,
        ),
    ]

    missing_evidence = [
        path
        for item in phases + actions
        for path in item.get("missing_evidence_files", [])
    ]
    action_status_counts = Counter(row["status"] for row in actions)
    phase_status_counts = Counter(row["current_status"] for row in phases)

    payload = {
        "generated_at_utc": generated.isoformat(),
        "as_of_date": as_of.isoformat(),
        "plan_file": rel(plan_file),
        "experiment_dir": rel(exp_dir),
        "overall_status": "PASS" if not missing_evidence else "FAIL",
        "claim_status": READY_STATUS if not missing_evidence else "submission_timeline_action_board_incomplete",
        "safe_to_use_as_submission": False,
        "submission_ready": False,
        "summary": {
            "arr_target_date": ARR_TARGET_DATE.isoformat(),
            "days_to_arr_target": (ARR_TARGET_DATE - as_of).days,
            "phase_count": len(phases),
            "action_count": len(actions),
            "critical_action_count": sum(1 for row in actions if row["priority"] == "critical"),
            "strong_optional_action_count": sum(1 for row in actions if row["priority"] == "strong_optional"),
            "minimum_human_return_files": len(minimum_returns),
            "minimum_human_return_files_present": present_minimum,
            "optional_human_return_files": len(optional_returns),
            "optional_human_return_files_present": present_optional,
            "optional_claim_return_files": len(optional_claim_returns),
            "optional_claim_return_files_present": present_optional_claim,
            "optional_structural_return_files": len(optional_structural_returns),
            "optional_structural_return_files_present": present_optional_structural,
            "tracked_human_return_files": len(returns),
            "tracked_human_return_files_present": present_minimum + present_optional,
            "human_blocker_count": compliance_summary.get("human_blocker_count"),
            "claim_gate_overall_status": claim_gate.get("overall_status"),
            "claim_gate_required_failures": claim_gate.get("required_failure_count"),
            "claim_gate_optional_failures": claim_gate.get("optional_failure_count"),
            "pre_human_validation_status": effective_validation.get("overall_status"),
            "pre_human_validation_checks": effective_validation.get("check_count"),
            "completion_status": completion.get("overall_completion_status"),
            "post_human_scoring_claim_status": scorer.get("claim_status"),
            "next_action_rows": len(next_actions),
            "missing_evidence_files": len(missing_evidence),
            "phase_status_counts": dict(sorted(phase_status_counts.items())),
            "action_status_counts": dict(sorted(action_status_counts.items())),
        },
        "strategy_a_aggressive_schedule": phases,
        "critical_path_actions": actions,
        "missing_evidence_files": missing_evidence,
    }
    return payload


def render_markdown(payload):
    summary = payload["summary"]
    phase_rows = [
        {
            "phase": row["phase_id"],
            "dates": f"{row['start_date']}~{row['end_date']}",
            "status": row["current_status"],
            "blocking_gates": row["blocking_gates"],
            "action_now": row["action_now"],
        }
        for row in payload["strategy_a_aggressive_schedule"]
    ]
    action_rows = [
        {
            "id": row["action_id"],
            "workstream": row["workstream"],
            "due": row["due_date"],
            "D-day": row["days_until_due"],
            "priority": row["priority"],
            "status": row["status"],
            "owner": row["owner"],
            "next_action": row["next_action"],
        }
        for row in payload["critical_path_actions"]
    ]

    lines = [
        "# CAPE-KG Submission Timeline Action Board",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"As-of date: `{payload['as_of_date']}`",
        f"Plan: `{payload['plan_file']}`",
        "",
        "이 문서는 revised EACL plan 14장의 공격적 EACL/ARR 제출 일정과 현재 gate 상태를 연결한 action board입니다.",
        "제출 완료 선언이 아니라, 남은 minimum/strong gate와 날짜별 critical path를 추적하기 위한 release artifact입니다.",
        "",
        "## Summary",
        "",
        md_table(
            ["Item", "Value"],
            [
                {"Item": "Overall status", "Value": payload["overall_status"]},
                {"Item": "Claim status", "Value": payload["claim_status"]},
                {"Item": "Safe to use as submission", "Value": payload["safe_to_use_as_submission"]},
                {"Item": "Submission ready", "Value": payload["submission_ready"]},
                {"Item": "ARR target date", "Value": summary["arr_target_date"]},
                {"Item": "Days to ARR target", "Value": summary["days_to_arr_target"]},
                {"Item": "Pre-human validation", "Value": summary["pre_human_validation_status"]},
                {"Item": "Pre-human checks", "Value": summary["pre_human_validation_checks"]},
                {"Item": "Claim gate", "Value": summary["claim_gate_overall_status"]},
                {"Item": "Minimum return files", "Value": f"{summary['minimum_human_return_files_present']}/{summary['minimum_human_return_files']}"},
                {"Item": "Optional/strong claim return files", "Value": f"{summary['optional_claim_return_files_present']}/{summary['optional_claim_return_files']}"},
                {"Item": "Optional structural review files", "Value": f"{summary['optional_structural_return_files_present']}/{summary['optional_structural_return_files']}"},
                {"Item": "All master return files", "Value": f"{summary['tracked_human_return_files_present']}/{summary['tracked_human_return_files']}"},
                {"Item": "Human blockers", "Value": summary["human_blocker_count"]},
            ],
        ),
        "",
        "## Strategy A Schedule Status",
        "",
        md_table(["phase", "dates", "status", "blocking_gates", "action_now"], phase_rows),
        "",
        "## Critical Path Actions",
        "",
        md_table(["id", "workstream", "due", "D-day", "priority", "status", "owner", "next_action"], action_rows),
        "",
        "## Interpretation",
        "",
        "- 자동 실험, baseline/ablation scaffolding, paper draft, release bundle은 pre-human 기준으로 준비되었습니다.",
        "- ARR 2026-08-03 목표의 critical path는 2026-07-12까지 minimum annotation returns를 확보하고, 2026-07-20까지 human-gold scoring을 채우는 것입니다.",
        "- Mapping/crosswalk expert review와 active-review human effort는 strong-accept claim을 위한 optional/strong path입니다.",
        "- Optional structural review 2개 파일은 procedural structure 보강용이며, minimum human-gold gate나 strong mapping/active-review claim gate를 대체하지 않습니다.",
        "- `safe_to_use_as_submission=false`와 `submission_ready=false`는 의도된 상태입니다. 최소 human-gold gate가 PASS가 되기 전에는 제출 완료로 표시하지 않습니다.",
        "",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", type=Path, default=DEFAULT_EXP_DIR)
    parser.add_argument("--plan-file", type=Path, default=DEFAULT_PLAN_FILE)
    args = parser.parse_args()

    payload = build_payload(args.experiment_dir, args.plan_file)
    release = args.experiment_dir / "06_release"
    json_path = release / "submission_timeline_action_board.json"
    md_path = release / "submission_timeline_action_board.md"
    write_json(json_path, payload)
    write_text(md_path, render_markdown(payload))
    print(
        json.dumps(
            {
                "json": rel(json_path),
                "markdown": rel(md_path),
                "overall_status": payload["overall_status"],
                "claim_status": payload["claim_status"],
                "days_to_arr_target": payload["summary"]["days_to_arr_target"],
                "critical_action_count": payload["summary"]["critical_action_count"],
                "missing_evidence_files": payload["summary"]["missing_evidence_files"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
