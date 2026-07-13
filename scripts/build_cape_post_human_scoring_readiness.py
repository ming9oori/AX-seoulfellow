#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a metric-level post-human scoring readiness map for CAPE-KG."""

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from cape_pre_human_status import effective_prehuman_claim_status, effective_prehuman_summary


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_PLAN_FILE = Path("AX_EACL_submission_review_revised_plan.md")
DEFAULT_PINNED_PYTHON = Path("/home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python")
READY_STATUS = "post_human_scoring_readiness_ready_pending_human_returns"


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
    return str(Path(path).as_posix())


def file_state(path):
    path = Path(path)
    return {
        "path": rel(path),
        "exists": path.exists() and path.is_file(),
        "bytes": path.stat().st_size if path.exists() and path.is_file() else 0,
    }


def status_from_returns(rows, task_types):
    relevant = [row for row in rows if row.get("task_type") in set(task_types)]
    present = sum(1 for row in relevant if row.get("present") == "yes")
    expected = len(relevant)
    required_minimum = sum(1 for row in relevant if row.get("required_for_minimum") == "yes")
    required_present = sum(
        1 for row in relevant if row.get("required_for_minimum") == "yes" and row.get("present") == "yes"
    )
    if expected == 0:
        status = "no_return_file_registered"
    elif present == expected:
        status = "ready_to_score_after_refresh"
    elif present > 0:
        status = "partial_returns_present"
    else:
        status = "pending_human_returns"
    return {
        "status": status,
        "expected_return_files": expected,
        "present_return_files": present,
        "minimum_expected_return_files": required_minimum,
        "minimum_present_return_files": required_present,
        "reviewed_files": [row.get("reviewed_file") for row in relevant],
    }


def row_for_metric(
    metric_id,
    metric_name,
    paper_claim,
    task_types,
    required_gate_ids,
    scoring_outputs,
    scoring_commands,
    current_evidence,
    return_rows,
    notes,
):
    state = status_from_returns(return_rows, task_types)
    claimable_now = state["status"] == "ready_to_score_after_refresh"
    return {
        "metric_id": metric_id,
        "metric_name": metric_name,
        "paper_claim": paper_claim,
        "claimable_now": claimable_now,
        "claim_status": "claimable_after_refresh" if claimable_now else state["status"],
        "required_human_or_expert_inputs": task_types,
        "required_gate_ids": required_gate_ids,
        "expected_return_files": state["expected_return_files"],
        "present_return_files": state["present_return_files"],
        "minimum_expected_return_files": state["minimum_expected_return_files"],
        "minimum_present_return_files": state["minimum_present_return_files"],
        "reviewed_files": state["reviewed_files"],
        "scoring_outputs": [file_state(path) for path in scoring_outputs],
        "scoring_commands": scoring_commands,
        "current_evidence": [file_state(path) for path in current_evidence],
        "notes": notes,
    }


def summarize_return_rows(rows):
    by_task = Counter(row.get("task_type") for row in rows)
    present_by_task = Counter(row.get("task_type") for row in rows if row.get("present") == "yes")
    minimum_rows = [row for row in rows if row.get("required_for_minimum") == "yes"]
    return {
        "tracked_return_files": len(rows),
        "present_return_files": sum(1 for row in rows if row.get("present") == "yes"),
        "minimum_return_files": len(minimum_rows),
        "minimum_present_return_files": sum(1 for row in minimum_rows if row.get("present") == "yes"),
        "task_type_counts": dict(sorted(by_task.items())),
        "task_type_present_counts": dict(sorted(present_by_task.items())),
    }


def command_sets(exp_dir):
    exp_dir = Path(exp_dir)
    exp_arg = rel(exp_dir)
    pinned = rel(DEFAULT_PINNED_PYTHON)
    return {
        "portable": {
            "validate_returns": f"python3 scripts/validate_cape_human_review_returns.py --experiment-dir {exp_arg}",
            "dry_run_apply_returns": (
                "PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=0 "
                "bash scripts/run_cape_human_return_apply.sh"
            ),
            "apply_returns_and_refresh": (
                "PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=1 "
                "bash scripts/run_cape_human_return_apply.sh"
            ),
            "validate_pre_human_or_post_refresh": (
                f"python3 scripts/validate_cape_pre_human_handoff.py --experiment-dir {exp_arg} --outputs-dir outputs"
            ),
        },
        "pinned": {
            "validate_returns": f"{pinned} scripts/validate_cape_human_review_returns.py --experiment-dir {exp_arg}",
            "dry_run_apply_returns": (
                f"PYTHON_BIN={pinned} LLM_PYTHON={pinned} APPLY_IMPORTS=0 "
                "bash scripts/run_cape_human_return_apply.sh"
            ),
            "apply_returns_and_refresh": (
                f"PYTHON_BIN={pinned} LLM_PYTHON={pinned} APPLY_IMPORTS=1 "
                "bash scripts/run_cape_human_return_apply.sh"
            ),
            "validate_pre_human_or_post_refresh": (
                f"{pinned} scripts/validate_cape_pre_human_handoff.py --experiment-dir {exp_arg} --outputs-dir outputs"
            ),
        },
    }


def build_payload(exp_dir, plan_file):
    exp_dir = Path(exp_dir)
    release_dir = exp_dir / "06_release"
    eval_dir = exp_dir / "04_evaluation"
    review_dir = exp_dir / "05_review"
    return_csv = review_dir / "human_gate_required_returns.csv"
    return_rows = read_csv(return_csv)
    readiness = read_json(release_dir / "submission_readiness_audit.json", {}) or {}
    claim_gate = read_json(release_dir / "claim_gate_report.json", {}) or {}
    prehuman = read_json(release_dir / "pre_human_handoff_validation.json", {}) or {}
    effective_prehuman = effective_prehuman_summary(prehuman)
    commands = command_sets(exp_dir)
    validate_command = commands["portable"]["validate_returns"]
    dry_run_command = commands["portable"]["dry_run_apply_returns"]
    refresh_command = commands["portable"]["apply_returns_and_refresh"]
    prehuman_command = commands["portable"]["validate_pre_human_or_post_refresh"]

    gold_outputs = [
        eval_dir / "human_gold_metrics.json",
        eval_dir / "human_gold_metrics.csv",
        eval_dir / "human_gold_evaluation_report.md",
        eval_dir / "human_gold_validation_summary.json",
        release_dir / "paper_tables.md",
        release_dir / "claimable_main_table.md",
    ]
    span_outputs = [
        eval_dir / "human_gold_span_iou_metrics.json",
        eval_dir / "human_gold_span_iou_components.csv",
        eval_dir / "human_gold_span_iou_report.md",
        release_dir / "paper_tables.md",
    ]
    structural_outputs = [
        eval_dir / "structural_evaluation_metrics.json",
        eval_dir / "structural_evaluation_report.md",
        release_dir / "cq_query_pack.md",
        release_dir / "paper_tables.md",
    ]
    mapping_outputs = [
        eval_dir / "mapping_expert_metrics.json",
        eval_dir / "mapping_expert_evaluation_report.md",
        release_dir / "mapping_review_progress_report.md",
        release_dir / "paper_tables.md",
    ]
    crosswalk_outputs = [
        eval_dir / "crosswalk_expert_metrics.json",
        eval_dir / "crosswalk_expert_evaluation_report.md",
        eval_dir / "ncs_pcf_crosswalk_summary.json",
        eval_dir / "ncs_pcf_crosswalk_report.md",
        release_dir / "paper_tables.md",
    ]
    effort_outputs = [
        eval_dir / "active_review_human_effort_metrics.json",
        eval_dir / "active_review_human_effort_report.md",
        eval_dir / "active_review_efficiency_metrics.json",
        eval_dir / "active_review_efficiency_report.md",
        release_dir / "paper_tables.md",
    ]

    metrics = [
        row_for_metric(
            "M01_node_f1",
            "Node F1",
            "Predicted node type/label quality against adjudicated human gold.",
            ["human_gold_annotation", "human_gold_adjudication"],
            ["gold.completed_chunks", "gold.item_count", "gold.iaa", "llm.proposed_human_gold_score"],
            gold_outputs,
            [validate_command, dry_run_command, refresh_command, prehuman_command],
            [eval_dir / "human_gold_metrics.json", eval_dir / "human_gold_validation_summary.json"],
            return_rows,
            "Claimable only after 100+ chunks, 500+ items, IAA, and adjudication are available.",
        ),
        row_for_metric(
            "M02_edge_f1",
            "Edge F1",
            "Predicted typed source-target edges against adjudicated human gold.",
            ["human_gold_annotation", "human_gold_adjudication"],
            ["gold.completed_chunks", "gold.item_count", "gold.iaa", "llm.proposed_human_gold_score"],
            gold_outputs,
            [validate_command, dry_run_command, refresh_command, prehuman_command],
            [eval_dir / "human_gold_metrics.json", eval_dir / "human_gold_validation_summary.json"],
            return_rows,
            "This is the main extraction result and remains non-claimable while adjudication is absent.",
        ),
        row_for_metric(
            "M03_evidence_exact_iou",
            "Evidence Exact Match / IoU",
            "Character/span grounding quality for predicted evidence anchors.",
            ["human_gold_annotation", "human_gold_adjudication"],
            ["gold.completed_chunks", "gold.item_count", "gold.iaa", "llm.proposed_human_gold_score"],
            span_outputs,
            [validate_command, dry_run_command, refresh_command, prehuman_command],
            [eval_dir / "human_gold_span_iou_metrics.json", eval_dir / "evidence_span_granularity_metrics.json"],
            return_rows,
            "Current span-granularity diagnostics are silver/proxy; adjudicated spans are required for paper claims.",
        ),
        row_for_metric(
            "M04_unsupported_edge_rate",
            "Unsupported Edge Rate",
            "Rate of predicted edges rejected as unsupported by adjudicated evidence.",
            ["human_gold_annotation", "human_gold_adjudication"],
            ["gold.completed_chunks", "gold.item_count", "gold.iaa", "llm.proposed_human_gold_score"],
            gold_outputs,
            [validate_command, dry_run_command, refresh_command, prehuman_command],
            [eval_dir / "human_gold_metrics.json", eval_dir / "evidence_grounding_report.md"],
            return_rows,
            "Unsupported-edge claims require adjudicator decisions, not only automatic evidence-anchor presence.",
        ),
        row_for_metric(
            "M05_ontology_conformance",
            "Ontology Conformance",
            "Domain/range/schema conformance after scoring against human-gold chunks.",
            ["human_gold_annotation", "human_gold_adjudication"],
            ["gold.completed_chunks", "gold.item_count", "llm.proposed_human_gold_score"],
            structural_outputs,
            [validate_command, dry_run_command, refresh_command, prehuman_command],
            [eval_dir / "structural_evaluation_metrics.json", eval_dir / "ontology_conformance_metrics.json"],
            return_rows,
            "Current full-KG structural conformance is claimable as a diagnostic; human-gold condition comparison is pending.",
        ),
        row_for_metric(
            "M06_procedural_consistency",
            "Procedural Consistency",
            "Cycle/gateway/artifact-flow consistency for predicted procedural KG.",
            ["human_gold_annotation", "human_gold_adjudication"],
            ["gold.completed_chunks", "gold.item_count", "llm.proposed_human_gold_score"],
            structural_outputs,
            [validate_command, dry_run_command, refresh_command, prehuman_command],
            [eval_dir / "structural_evaluation_metrics.json", eval_dir / "procedural_consistency_metrics.json"],
            return_rows,
            "Can be reported now only as a structural diagnostic; final condition comparison needs human-gold scoring.",
        ),
        row_for_metric(
            "M07_cq_answerability",
            "CQ Answerability",
            "Whether graph queries can answer the planned competency questions.",
            ["human_gold_annotation", "human_gold_adjudication"],
            ["gold.completed_chunks", "gold.item_count", "llm.proposed_human_gold_score"],
            structural_outputs,
            [validate_command, dry_run_command, refresh_command, prehuman_command],
            [release_dir / "cq_query_pack.json", eval_dir / "cq_answerability_structural_metrics.json"],
            return_rows,
            "CQ8 now has structural KG support through projected ReviewCheckpoint links; correctness of answers still requires human-gold review.",
        ),
        row_for_metric(
            "M08_mapping_pk_mrr_ndcg",
            "NCS/PCF Mapping P@K / MRR / nDCG",
            "Expert-confirmed downstream alignment quality for Layer2-to-NCS/PCF candidates.",
            ["mapping_expert_review"],
            ["mapping.expert_review"],
            mapping_outputs,
            [validate_command, dry_run_command, refresh_command, prehuman_command],
            [eval_dir / "mapping_expert_metrics.json", release_dir / "mapping_review_progress_summary.json"],
            return_rows,
            "Optional/strong claim. It does not satisfy minimum human-gold extraction gates.",
        ),
        row_for_metric(
            "M09_crosswalk_accept_utility",
            "NCS-PCF Crosswalk Accept Rate / Utility",
            "Expert-confirmed utility of Layer2-bridged NCS-PCF crosswalk candidates.",
            ["crosswalk_expert_review"],
            ["crosswalk.expert_review"],
            crosswalk_outputs,
            [validate_command, dry_run_command, refresh_command, prehuman_command],
            [eval_dir / "crosswalk_expert_metrics.json", eval_dir / "ncs_pcf_crosswalk_summary.json"],
            return_rows,
            "Optional/strong claim for standard-taxonomy bridge utility.",
        ),
        row_for_metric(
            "M10_active_review_efficiency",
            "Active Review Efficiency",
            "Corrected high-impact errors per reviewer effort/time.",
            ["active_review_human_effort"],
            ["strong.active_review"],
            effort_outputs,
            [validate_command, dry_run_command, refresh_command, prehuman_command],
            [eval_dir / "active_review_human_effort_metrics.json", eval_dir / "active_review_efficiency_metrics.json"],
            return_rows,
            "Requires reviewed effort/timing CSV and should be interpreted with adjudication outcomes.",
        ),
    ]

    summary = {
        "metric_count": len(metrics),
        "claimable_metric_count": sum(1 for row in metrics if row["claimable_now"]),
        "pending_metric_count": sum(1 for row in metrics if not row["claimable_now"]),
        "return_summary": summarize_return_rows(return_rows),
        "readiness_claim_status": readiness.get("claim_status"),
        "claim_gate_overall_status": claim_gate.get("overall_status"),
        "pre_human_validation_status": effective_prehuman.get("overall_status"),
        "pre_human_validation_counts": effective_prehuman.get("status_counts"),
        "pre_human_validation_check_count": effective_prehuman.get("check_count"),
        "pre_human_validation_claim_status": effective_prehuman_claim_status(prehuman),
    }

    missing_outputs = []
    for metric in metrics:
        for state in metric["scoring_outputs"] + metric["current_evidence"]:
            if not state["exists"]:
                missing_outputs.append(state["path"])
    missing_outputs = sorted(set(missing_outputs))

    overall_status = "PASS" if not missing_outputs and return_rows else "FAIL"
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": rel(exp_dir),
        "plan_file": rel(plan_file),
        "overall_status": overall_status,
        "claim_status": READY_STATUS if overall_status == "PASS" else "post_human_scoring_readiness_incomplete",
        "safe_to_use_as_submission": False,
        "submission_ready": False,
        "summary": summary,
        "missing_outputs_or_evidence": missing_outputs,
        "command_environment": {
            "primary_command_style": "portable_python3",
            "pinned_python": rel(DEFAULT_PINNED_PYTHON),
            "pinned_python_exists": DEFAULT_PINNED_PYTHON.exists(),
        },
        "global_commands": commands["portable"],
        "portable_commands": commands["portable"],
        "pinned_commands": commands["pinned"],
        "metrics": metrics,
        "claim_policy": [
            "This artifact is a scoring readiness map, not human-gold evidence.",
            "Metrics with pending_human_returns must not be used as final paper performance claims.",
            "Run dry-run validation before APPLY_IMPORTS=1 whenever reviewed return files are added.",
            "Regenerate paper tables, claim gate, provenance, and release bundles after applying returns.",
        ],
    }


def md_table(headers, rows):
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(header, "")) for header in headers) + " |")
    return "\n".join(lines)


def render_markdown(payload):
    summary = payload["summary"]
    rows = []
    for metric in payload["metrics"]:
        rows.append(
            {
                "metric": metric["metric_name"],
                "claim_status": metric["claim_status"],
                "returns": f"{metric['present_return_files']}/{metric['expected_return_files']}",
                "gate_ids": ", ".join(metric["required_gate_ids"]),
                "main_outputs": "<br>".join(state["path"] for state in metric["scoring_outputs"][:3]),
            }
        )

    command_rows = [
        {"step": name, "command": command}
        for name, command in payload["global_commands"].items()
    ]
    pinned_command_rows = [
        {"step": name, "command": command}
        for name, command in payload["pinned_commands"].items()
    ]

    lines = [
        "# CAPE-KG Post-Human Scoring Readiness",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Claim status: `{payload['claim_status']}`",
        f"Overall status: `{payload['overall_status']}`",
        f"Safe to use as submission: `{payload['safe_to_use_as_submission']}`",
        f"Submission ready: `{payload['submission_ready']}`",
        "",
        "이 파일은 사람 검수 결과가 돌아온 뒤 어떤 지표를 어떤 명령으로 갱신해야 하는지 고정한 readiness map입니다. "
        "현재 human-gold evidence 자체가 아니며, 최종 논문 성능 claim을 대체하지 않습니다.",
        "",
        "## Summary",
        "",
        md_table(
            ["item", "value"],
            [
                {"item": "metric_count", "value": summary["metric_count"]},
                {"item": "claimable_metric_count", "value": summary["claimable_metric_count"]},
                {"item": "pending_metric_count", "value": summary["pending_metric_count"]},
                {"item": "tracked_return_files", "value": summary["return_summary"]["tracked_return_files"]},
                {"item": "present_return_files", "value": summary["return_summary"]["present_return_files"]},
                {"item": "minimum_return_files", "value": summary["return_summary"]["minimum_return_files"]},
                {"item": "minimum_present_return_files", "value": summary["return_summary"]["minimum_present_return_files"]},
                {"item": "readiness_claim_status", "value": summary.get("readiness_claim_status")},
                {"item": "claim_gate_overall_status", "value": summary.get("claim_gate_overall_status")},
                {"item": "pre_human_validation_status", "value": summary.get("pre_human_validation_status")},
                {"item": "pre_human_validation_counts", "value": summary.get("pre_human_validation_counts")},
                {"item": "pre_human_validation_check_count", "value": summary.get("pre_human_validation_check_count")},
                {"item": "pre_human_validation_claim_status", "value": summary.get("pre_human_validation_claim_status")},
                {"item": "primary_command_style", "value": payload["command_environment"]["primary_command_style"]},
                {"item": "pinned_python_exists", "value": payload["command_environment"]["pinned_python_exists"]},
            ],
        ),
        "",
        "## Metric Readiness",
        "",
        md_table(["metric", "claim_status", "returns", "gate_ids", "main_outputs"], rows),
        "",
        "## Refresh Commands",
        "",
        "아래 명령은 현재 repository checkout에서 바로 실행하기 위한 portable `python3` 기준 명령입니다.",
        "",
        md_table(["step", "command"], command_rows),
        "",
        "## Pinned Environment Commands",
        "",
        f"아래 명령은 현재 서버에서 확인된 pinned Python 경로 `{payload['command_environment']['pinned_python']}`를 사용하는 참고 명령입니다.",
        "",
        md_table(["step", "command"], pinned_command_rows),
        "",
        "## Claim Policy",
        "",
    ]
    lines.extend(f"- {item}" for item in payload["claim_policy"])
    lines.extend(
        [
            "",
            "## Missing Outputs Or Evidence",
            "",
        ]
    )
    if payload["missing_outputs_or_evidence"]:
        lines.extend(f"- `{path}`" for path in payload["missing_outputs_or_evidence"])
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", type=Path, default=DEFAULT_EXP_DIR)
    parser.add_argument("--plan-file", type=Path, default=DEFAULT_PLAN_FILE)
    args = parser.parse_args()

    payload = build_payload(args.experiment_dir, args.plan_file)
    release_dir = args.experiment_dir / "06_release"
    json_path = release_dir / "post_human_scoring_readiness.json"
    md_path = release_dir / "post_human_scoring_readiness.md"
    write_json(json_path, payload)
    write_text(md_path, render_markdown(payload))
    print(
        json.dumps(
            {
                "json": rel(json_path),
                "markdown": rel(md_path),
                "overall_status": payload["overall_status"],
                "claim_status": payload["claim_status"],
                "metric_count": payload["summary"]["metric_count"],
                "pending_metric_count": payload["summary"]["pending_metric_count"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
