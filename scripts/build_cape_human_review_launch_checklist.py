#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a day-1 launch checklist for CAPE-KG human review."""

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")

TASK_FIELDS = [
    "priority",
    "phase",
    "actor",
    "task_type",
    "batch_or_group",
    "open_file",
    "save_as",
    "expected_rows",
    "command",
    "unlocks",
    "claim_note",
]

MINIMUM_TASK_TYPES = {"human_gold_annotation", "human_gold_adjudication"}


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


def write_csv(path, rows, fieldnames):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def rel(path):
    return str(Path(path).as_posix())


def present(value):
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"yes", "true", "1", "present"}


def count_present(rows):
    return sum(1 for row in rows if present(row.get("present")))


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
        "selected_chunks": int(policy.get("selected_chunk_count") or 0),
        "minimum_gate_target_chunks": int(policy.get("minimum_gate_target_chunks") or 100),
        "batch_count": int(policy.get("batch_count") or 0),
        "batch_size": int(policy.get("batch_size") or 0),
        "priority_formula": policy.get("priority_formula"),
        "candidate_edges": int(coverage.get("priority_100_candidate_edges") or 0),
        "full_120_candidate_edges": int(coverage.get("full_120_candidate_edges") or 0),
        "candidate_edge_coverage": float(coverage.get("priority_100_candidate_edge_coverage_of_full120") or 0.0),
        "active_review_coverage": float(coverage.get("priority_100_active_review_chunk_coverage_of_full120") or 0.0),
        "high_impact_coverage": float(coverage.get("priority_100_high_impact_chunk_coverage_of_full120") or 0.0),
        "not_gold_until": policy.get("not_gold_until"),
    }


def normalize_return_rows(rows):
    normalized = []
    for row in rows:
        clean = {str(k).lstrip("\ufeff"): v for k, v in row.items()}
        normalized.append(clean)
    return normalized


def build_launch_tasks(required_rows, exp_dir):
    annotation_rows = [
        row
        for row in required_rows
        if row.get("required_for_minimum") == "yes" and row.get("task_type") == "human_gold_annotation"
    ]
    annotation_rows.sort(key=lambda row: (row.get("batch_or_group", ""), row.get("owner", "")))
    adjudication_rows = [
        row
        for row in required_rows
        if row.get("required_for_minimum") == "yes" and row.get("task_type") == "human_gold_adjudication"
    ]
    optional_rows = [row for row in required_rows if row.get("required_for_minimum") != "yes"]

    py = "python3"
    exp = rel(exp_dir)
    commands = {
        "verify_handoff_checksums": f"sha256sum -c {exp}/06_release/human_review_handoff/human_review_handoff_checksums.sha256",
        "validate_returns": f"{py} scripts/validate_cape_human_review_returns.py --experiment-dir {exp}",
        "dry_apply": f"PYTHON_BIN={py} LLM_PYTHON={py} APPLY_IMPORTS=0 bash scripts/run_cape_human_return_apply.sh",
        "apply_returns": f"PYTHON_BIN={py} LLM_PYTHON={py} APPLY_IMPORTS=1 bash scripts/run_cape_human_return_apply.sh",
        "validate_pre_human": f"{py} scripts/validate_cape_pre_human_handoff.py --experiment-dir {exp} --outputs-dir outputs",
        "release_checksums": f"sha256sum -c {exp}/06_release/release_bundle_checksums.sha256",
    }

    tasks = [
        {
            "priority": "1",
            "phase": "0_package_integrity",
            "actor": "coordinator",
            "task_type": "checksum",
            "batch_or_group": "human_review_handoff",
            "open_file": f"{exp}/06_release/human_review_handoff/human_review_handoff_checksums.sha256",
            "save_as": "",
            "expected_rows": "",
            "command": commands["verify_handoff_checksums"],
            "unlocks": "review package distribution",
            "claim_note": "checksum은 검수 evidence가 아니라 handoff integrity evidence입니다.",
        }
    ]

    priority = 2
    for row in annotation_rows:
        tasks.append(
            {
                "priority": str(priority),
                "phase": "1_independent_annotation",
                "actor": row.get("owner", ""),
                "task_type": row.get("task_type", ""),
                "batch_or_group": row.get("batch_or_group", ""),
                "open_file": row.get("input_file", ""),
                "save_as": row.get("reviewed_file", ""),
                "expected_rows": row.get("expected_rows", ""),
                "command": "",
                "unlocks": "A/B paired chunks for IAA and adjudication",
                "claim_note": "두 annotator가 같은 batch를 모두 완료해야 IAA/adjudication으로 진행됩니다.",
            }
        )
        priority += 1

    tasks.extend(
        [
            {
                "priority": str(priority),
                "phase": "2_preflight",
                "actor": "coordinator",
                "task_type": "return_preflight",
                "batch_or_group": "minimum_100_annotation_returns",
                "open_file": f"{exp}/05_review/human_gate_required_returns.csv",
                "save_as": f"{exp}/06_release/human_review_return_preflight.md",
                "expected_rows": "10 annotation reviewed files before A/B import",
                "command": commands["validate_returns"],
                "unlocks": "safe dry-run/import decision",
                "claim_note": "preflight가 error 없이 통과하기 전에는 import하지 않습니다.",
            },
            {
                "priority": str(priority + 1),
                "phase": "3_dry_run",
                "actor": "coordinator",
                "task_type": "dry_run_refresh",
                "batch_or_group": "returned_human_files",
                "open_file": "",
                "save_as": f"{exp}/06_release/human_return_apply_last_run.md",
                "expected_rows": "",
                "command": commands["dry_apply"],
                "unlocks": "apply readiness check",
                "claim_note": "dry-run은 안전 점검이며 human-gold claim을 만들지 않습니다.",
            },
            {
                "priority": str(priority + 2),
                "phase": "4_apply_annotation_returns",
                "actor": "coordinator",
                "task_type": "apply_returns",
                "batch_or_group": "minimum_100_annotation_returns",
                "open_file": "",
                "save_as": f"{exp}/01_data/gold_annotation/full_120/annotator_A.jsonl; {exp}/01_data/gold_annotation/full_120/annotator_B.jsonl",
                "expected_rows": "100 rows per annotator after all 5 batches",
                "command": commands["apply_returns"],
                "unlocks": "IAA computation and adjudication draft refresh",
                "claim_note": "annotation import 후에도 adjudication 전까지 final human-gold score는 없습니다.",
            },
        ]
    )
    priority += 3

    for row in adjudication_rows:
        tasks.append(
            {
                "priority": str(priority),
                "phase": "5_adjudication",
                "actor": row.get("owner", "adjudicator"),
                "task_type": row.get("task_type", ""),
                "batch_or_group": row.get("batch_or_group", ""),
                "open_file": row.get("input_file", ""),
                "save_as": row.get("reviewed_file", ""),
                "expected_rows": row.get("expected_rows", ""),
                "command": "",
                "unlocks": "adjudicated human-gold metrics and P_cape_kg_actual scoring",
                "claim_note": "adjudication_edited.jsonl까지 들어와야 최소 제출 claim gate를 열 수 있습니다.",
            }
        )
        priority += 1

    tasks.extend(
        [
            {
                "priority": str(priority),
                "phase": "6_apply_adjudication",
                "actor": "coordinator",
                "task_type": "apply_adjudication",
                "batch_or_group": "full_120_adjudication",
                "open_file": f"{exp}/01_data/gold_annotation/full_120/adjudication_edited.jsonl",
                "save_as": f"{exp}/04_evaluation/human_gold_metrics.json",
                "expected_rows": "120 adjudication rows",
                "command": commands["apply_returns"],
                "unlocks": "human-gold scoring and claim gate update",
                "claim_note": "이 단계 이후에만 human-gold 기반 main table을 갱신할 수 있습니다.",
            },
            {
                "priority": str(priority + 1),
                "phase": "7_final_validation",
                "actor": "coordinator",
                "task_type": "final_validation",
                "batch_or_group": "release_and_claim_gate",
                "open_file": f"{exp}/06_release/claim_gate_report.md",
                "save_as": f"{exp}/06_release/pre_human_handoff_validation.md",
                "expected_rows": "",
                "command": commands["validate_pre_human"],
                "unlocks": "submission readiness audit evidence",
                "claim_note": "claim gate가 PASS가 되기 전까지 성능 우위 주장은 금지합니다.",
            },
            {
                "priority": str(priority + 2),
                "phase": "7_final_validation",
                "actor": "coordinator",
                "task_type": "checksum",
                "batch_or_group": "release_bundle",
                "open_file": f"{exp}/06_release/release_bundle_checksums.sha256",
                "save_as": "",
                "expected_rows": "",
                "command": commands["release_checksums"],
                "unlocks": "reproducibility bundle integrity evidence",
                "claim_note": "bundle integrity와 paper claim readiness는 별개입니다.",
            },
        ]
    )

    optional_tasks = []
    for row in optional_rows:
        optional_tasks.append(
            {
                "actor": row.get("owner", ""),
                "task_type": row.get("task_type", ""),
                "batch_or_group": row.get("batch_or_group", ""),
                "open_file": row.get("input_file", ""),
                "save_as": row.get("reviewed_file", ""),
                "expected_rows": row.get("expected_rows", ""),
                "claim_note": "optional/strong claim용이며 minimum human-gold gate를 대체하지 않습니다.",
            }
        )

    return tasks, optional_tasks, commands


def render_markdown(payload):
    summary = payload["summary"]
    lines = [
        "# CAPE-KG Human Review Launch Checklist",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Experiment: `{payload['experiment_dir']}`",
        "",
        "이 문서는 검수자가 바로 시작하기 위한 실행표입니다. 기존 master checklist보다 더 작게, 최소 제출 gate를 여는 데 필요한 파일명과 명령만 앞에 배치합니다.",
        "",
        "## Current Gate State",
        "",
        "| item | value |",
        "|---|---:|",
        f"| Claim gate | `{summary['claim_gate_overall_status']}` |",
        f"| Required claim-gate failures | {summary['claim_gate_required_failure_count']} |",
        f"| Human return preflight | `{summary['human_return_preflight']}` |",
        f"| Minimum return files present | {summary['minimum_return_files_present']}/{summary['minimum_return_files_total']} |",
        f"| Annotation reviewed files present | {summary['annotation_return_files_present']}/{summary['annotation_return_files_total']} |",
        f"| Adjudication reviewed file present | {summary['adjudication_return_files_present']}/{summary['adjudication_return_files_total']} |",
        f"| Mapping/crosswalk/active optional files present | {summary['optional_return_files_present']}/{summary['optional_return_files_total']} |",
        "",
        "## Priority-100 선정 근거",
        "",
        "| item | value |",
        "|---|---:|",
        f"| Selected chunks | {payload['priority_100_sampling'].get('selected_chunks')}/{payload['priority_100_sampling'].get('minimum_gate_target_chunks')} |",
        f"| Batch count / size | {payload['priority_100_sampling'].get('batch_count')} / {payload['priority_100_sampling'].get('batch_size')} |",
        f"| Candidate edges covered | {payload['priority_100_sampling'].get('candidate_edges')}/{payload['priority_100_sampling'].get('full_120_candidate_edges')} |",
        f"| Candidate-edge coverage | {payload['priority_100_sampling'].get('candidate_edge_coverage'):.6f} |",
        f"| Active-review chunk coverage | {payload['priority_100_sampling'].get('active_review_coverage'):.6f} |",
        f"| High-impact chunk coverage | {payload['priority_100_sampling'].get('high_impact_coverage'):.6f} |",
        f"| Claim status | `{payload['priority_100_sampling'].get('claim_status')}` |",
        f"| Report | `{payload['priority_100_sampling'].get('report_markdown')}` |",
        "",
        "이 표는 100개 chunk 선정이 충분한 coverage를 갖는지 보여주는 운영 근거입니다. 실제 gold claim은 A/B 검수, IAA, adjudication 이후에만 가능합니다.",
        "",
        "## Minimum Gate Launch Tasks",
        "",
        "| # | phase | actor | open | save as | command |",
        "|---:|---|---|---|---|---|",
    ]
    for task in payload["minimum_gate_launch_tasks"]:
        command = f"`{task['command']}`" if task.get("command") else ""
        lines.append(
            f"| {task['priority']} | `{task['phase']}` | {task['actor']} | "
            f"`{task['open_file']}` | `{task['save_as']}` | {command} |"
        )

    lines.extend(
        [
            "",
            "## Required Reviewed Filenames",
            "",
            "| task | owner | batch | expected rows | reviewed filename | present |",
            "|---|---|---|---:|---|---|",
        ]
    )
    for row in payload["minimum_required_return_files"]:
        lines.append(
            f"| {row.get('task_type')} | {row.get('owner')} | {row.get('batch_or_group')} | "
            f"{row.get('expected_rows')} | `{row.get('reviewed_file')}` | {row.get('present')} |"
        )

    lines.extend(
        [
            "",
            "## Optional Strong/Utility Tasks",
            "",
            "| actor | task | open | save as | note |",
            "|---|---|---|---|---|",
        ]
    )
    for row in payload["optional_return_tasks"]:
        lines.append(
            f"| {row.get('actor')} | {row.get('task_type')} | `{row.get('open_file')}` | "
            f"`{row.get('save_as')}` | {row.get('claim_note')} |"
        )

    lines.extend(
        [
            "",
            "## Commands",
            "",
        ]
    )
    for name, command in payload["commands"].items():
        lines.extend([f"### {name}", "", "```bash", command, "```", ""])

    lines.extend(
        [
            "## Claim Safety",
            "",
            "- 이 checklist는 작업 시작을 위한 운영 산출물이며 human-gold evidence가 아닙니다.",
            "- `P_cape_kg_actual`의 최종 성능 claim은 adjudication 완료 후 human-gold scoring이 다시 생성될 때만 가능합니다.",
            "- mapping P@K/MRR/nDCG, NCS-PCF crosswalk utility, active-review efficiency는 각각 expert review와 effort CSV가 돌아온 뒤에만 claim할 수 있습니다.",
            "",
        ]
    )
    return "\n".join(lines)


def build_payload(exp_dir):
    exp_dir = Path(exp_dir)
    release_dir = exp_dir / "06_release"
    review_dir = exp_dir / "05_review"
    required_returns_path = review_dir / "human_gate_required_returns.csv"

    required_rows = normalize_return_rows(read_csv(required_returns_path))
    minimum_rows = [
        row
        for row in required_rows
        if row.get("required_for_minimum") == "yes" and row.get("task_type") in MINIMUM_TASK_TYPES
    ]
    annotation_rows = [row for row in minimum_rows if row.get("task_type") == "human_gold_annotation"]
    adjudication_rows = [row for row in minimum_rows if row.get("task_type") == "human_gold_adjudication"]
    optional_rows = [row for row in required_rows if row.get("required_for_minimum") != "yes"]

    tasks, optional_tasks, commands = build_launch_tasks(required_rows, exp_dir)
    claim_gate = read_json(release_dir / "claim_gate_report.json", {}) or {}
    preflight = read_json(release_dir / "human_review_return_preflight.json", {}) or {}

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": rel(exp_dir),
        "claim_status": "human_review_launch_checklist_ready_pending_human_returns",
        "priority_100_sampling": gold_sampling_summary(exp_dir),
        "summary": {
            "claim_gate_overall_status": claim_gate.get("overall_status"),
            "claim_gate_required_failure_count": claim_gate.get("required_failure_count"),
            "claim_gate_optional_failure_count": claim_gate.get("optional_failure_count"),
            "human_return_preflight": preflight.get("overall_status"),
            "minimum_return_files_total": len(minimum_rows),
            "minimum_return_files_present": count_present(minimum_rows),
            "annotation_return_files_total": len(annotation_rows),
            "annotation_return_files_present": count_present(annotation_rows),
            "adjudication_return_files_total": len(adjudication_rows),
            "adjudication_return_files_present": count_present(adjudication_rows),
            "optional_return_files_total": len(optional_rows),
            "optional_return_files_present": count_present(optional_rows),
        },
        "minimum_required_return_files": minimum_rows,
        "minimum_gate_launch_tasks": tasks,
        "optional_return_tasks": optional_tasks,
        "commands": commands,
        "outputs": {
            "json": rel(release_dir / "human_review_launch_checklist_ko.json"),
            "markdown": rel(release_dir / "human_review_launch_checklist_ko.md"),
            "csv": rel(review_dir / "human_review_minimum_gate_launch_tasks.csv"),
        },
    }
    return payload


def run(args):
    exp_dir = Path(args.experiment_dir)
    release_dir = exp_dir / "06_release"
    review_dir = exp_dir / "05_review"
    payload = build_payload(exp_dir)
    write_json(release_dir / "human_review_launch_checklist_ko.json", payload)
    write_text(release_dir / "human_review_launch_checklist_ko.md", render_markdown(payload))
    write_csv(review_dir / "human_review_minimum_gate_launch_tasks.csv", payload["minimum_gate_launch_tasks"], TASK_FIELDS)
    print(
        json.dumps(
            {
                "json": payload["outputs"]["json"],
                "markdown": payload["outputs"]["markdown"],
                "csv": payload["outputs"]["csv"],
                "claim_status": payload["claim_status"],
                "minimum_return_files_present": payload["summary"]["minimum_return_files_present"],
                "minimum_return_files_total": payload["summary"]["minimum_return_files_total"],
                "launch_task_rows": len(payload["minimum_gate_launch_tasks"]),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
