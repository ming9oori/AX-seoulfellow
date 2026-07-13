#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a compact first-batch execution card for CAPE-KG human review."""

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_BATCH_ID = "full_120_priority_batch_001"


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
        "exists": path.exists(),
        "bytes": path.stat().st_size if path.exists() else 0,
    }


def md_table(headers, rows):
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        values = [str(row.get(header, "")).replace("|", "\\|") for header in headers]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def owner_sort_key(row):
    owner = str(row.get("owner") or "")
    if owner.endswith("_A"):
        return (0, owner)
    if owner.endswith("_B"):
        return (1, owner)
    return (2, owner)


def gold_sampling_summary(exp_dir, batch_manifest):
    exp_dir = Path(exp_dir)
    report_path = exp_dir / "06_release/gold_sampling_coverage_report.json"
    data = read_json(report_path, {}) or {}
    policy = data.get("selection_policy") or {}
    coverage = data.get("coverage_summary") or {}
    priority_candidate_edges = int(coverage.get("priority_100_candidate_edges") or 0)
    batch_candidate_edges = int(batch_manifest.get("candidate_edges_total") or 0)
    return {
        "claim_status": data.get("claim_status"),
        "report_json": rel(report_path),
        "report_markdown": rel(exp_dir / "06_release/gold_sampling_coverage_report.md"),
        "selected_chunks": int(policy.get("selected_chunk_count") or 0),
        "minimum_gate_target_chunks": int(policy.get("minimum_gate_target_chunks") or 100),
        "batch_count": int(policy.get("batch_count") or 0),
        "batch_size": int(policy.get("batch_size") or 0),
        "priority_100_candidate_edges": priority_candidate_edges,
        "full_120_candidate_edges": int(coverage.get("full_120_candidate_edges") or 0),
        "batch_candidate_edges": batch_candidate_edges,
        "batch_share_of_priority_candidate_edges": round(batch_candidate_edges / priority_candidate_edges, 6)
        if priority_candidate_edges
        else 0.0,
        "candidate_edge_coverage": float(coverage.get("priority_100_candidate_edge_coverage_of_full120") or 0.0),
        "active_review_coverage": float(coverage.get("priority_100_active_review_chunk_coverage_of_full120") or 0.0),
        "high_impact_coverage": float(coverage.get("priority_100_high_impact_chunk_coverage_of_full120") or 0.0),
        "not_gold_until": policy.get("not_gold_until"),
    }


def build_payload(exp_dir, batch_id):
    exp_dir = Path(exp_dir)
    release_dir = exp_dir / "06_release"
    review_dir = exp_dir / "05_review"
    batch_dir = review_dir / "human_gold_batches" / batch_id
    gold_dir = exp_dir / "01_data/gold_annotation"

    batch_manifest = read_json(batch_dir / "batch_manifest.json", {}) or {}
    preflight = read_json(release_dir / "human_review_return_preflight.json", {}) or {}
    claim_gate = read_json(release_dir / "claim_gate_report.json", {}) or {}
    return_rows = read_csv(review_dir / "human_review_master_return_files.csv")
    first_rows = sorted(
        [
            row
            for row in return_rows
            if row.get("task_type") == "human_gold_annotation"
            and row.get("batch_or_group") == batch_id
        ],
        key=owner_sort_key,
    )

    commands = {
        "verify_handoff_checksums": "sha256sum -c experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/human_review_handoff_checksums.sha256",
        "validate_required_returns": "python3 scripts/validate_cape_human_review_returns.py --experiment-dir experiments/cape_kg_eacl_20260627",
        "dry_run_human_return_apply": "PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=0 bash scripts/run_cape_human_return_apply.sh",
        "apply_human_returns": "PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=1 bash scripts/run_cape_human_return_apply.sh",
    }

    outputs = {
        "markdown": str(review_dir / "human_review_first_batch_execution_card_ko.md"),
        "json": str(review_dir / "human_review_first_batch_execution_card.json"),
    }

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "batch_id": batch_id,
        "claim_status": "first_batch_execution_card_ready_pending_human_returns",
        "current_gate_status": {
            "claim_gate_overall_status": claim_gate.get("overall_status"),
            "claim_gate_required_failure_count": claim_gate.get("required_failure_count"),
            "human_return_preflight_status": preflight.get("overall_status"),
            "minimum_paper_gate_ready_after_preflight": preflight.get("minimum_paper_gate_ready_after_preflight"),
            "apply_scope": preflight.get("apply_scope"),
        },
        "batch_manifest": batch_manifest,
        "priority_100_sampling": gold_sampling_summary(exp_dir, batch_manifest),
        "first_annotation_return_files": first_rows,
        "common_files_to_open": {
            "workbench": file_state(gold_dir / "annotation_workbench.html"),
            "annotation_guideline": file_state(exp_dir / "01_data/annotation_guideline_v1.md"),
            "annotation_schema": file_state(gold_dir / "annotation_schema.json"),
            "adjudication_protocol": file_state(gold_dir / "adjudication_protocol.md"),
            "calibration_pack": file_state(release_dir / "annotation_calibration_pack_ko.md"),
            "batch_readme": file_state(batch_dir / "README.md"),
            "batch_preview_md": file_state(batch_dir / "batch_review_preview.md"),
            "batch_preview_csv": file_state(batch_dir / "batch_review_preview.csv"),
            "batch_tracking_sheet": file_state(batch_dir / "batch_tracking_sheet.csv"),
            "master_return_files": file_state(review_dir / "human_review_master_return_files.csv"),
            "status_dashboard": file_state(release_dir / "human_review_status_dashboard_ko.md"),
            "launch_checklist": file_state(release_dir / "human_review_launch_checklist_ko.md"),
        },
        "commands": commands,
        "guardrails": [
            "Input JSONL은 덮어쓰지 않고 reviewed_file 경로에 새로 저장합니다.",
            "A/B annotator는 서로 결과를 보지 않고 독립적으로 검수합니다.",
            "각 JSONL row는 한 줄에 하나의 JSON object 형식을 유지합니다.",
            "accepted edge에는 evidence anchor 또는 exact span을 남깁니다.",
            "첫 배치 20 chunks만으로 human-gold 최종 성능 claim을 하지 않습니다.",
            "최소 논문 gate는 5개 batch A/B 10개 reviewed 파일과 adjudication reviewed 파일까지 필요합니다.",
        ],
        "outputs": outputs,
    }


def render_report(payload):
    gate = payload["current_gate_status"]
    manifest = payload["batch_manifest"]
    common = payload["common_files_to_open"]
    commands = payload["commands"]
    lines = [
        "# CAPE-KG 첫 배치 검수 실행 카드",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Experiment: `{payload['experiment_dir']}`",
        f"Batch: `{payload['batch_id']}`",
        "",
        "이 문서는 전체 체크리스트가 아니라, human-gold 검수를 실제로 시작할 때 첫 20개 chunk 배치에서 열 파일과 저장 파일을 바로 확인하기 위한 내부 실행 카드입니다.",
        "",
        "## 현재 상태",
        "",
        f"- Claim gate: `{gate.get('claim_gate_overall_status')}`",
        f"- Required claim-gate failures: {gate.get('claim_gate_required_failure_count')}",
        f"- Human-return preflight: `{gate.get('human_return_preflight_status')}`",
        f"- Minimum paper gate ready after preflight: {gate.get('minimum_paper_gate_ready_after_preflight')}",
        f"- Apply scope: `{gate.get('apply_scope')}`",
        "",
        "## 첫 배치 규모",
        "",
        f"- Chunk count: {manifest.get('chunk_count')}",
        f"- Candidate edges: {manifest.get('candidate_edges_total')}",
        f"- Active-review items: {manifest.get('active_review_items_total')}",
        f"- High-impact chunks: {manifest.get('high_impact_chunks')}",
        "",
        "## Priority-100 안에서 첫 배치의 의미",
        "",
        "| item | value |",
        "|---|---:|",
        f"| Priority-100 selected chunks | {payload['priority_100_sampling'].get('selected_chunks')}/{payload['priority_100_sampling'].get('minimum_gate_target_chunks')} |",
        f"| Priority-100 candidate edges | {payload['priority_100_sampling'].get('priority_100_candidate_edges')} |",
        f"| First-batch candidate edges | {payload['priority_100_sampling'].get('batch_candidate_edges')} |",
        f"| First-batch share of priority candidate edges | {payload['priority_100_sampling'].get('batch_share_of_priority_candidate_edges'):.6f} |",
        f"| Full-120 candidate-edge coverage | {payload['priority_100_sampling'].get('candidate_edge_coverage'):.6f} |",
        f"| Active-review coverage | {payload['priority_100_sampling'].get('active_review_coverage'):.6f} |",
        f"| High-impact coverage | {payload['priority_100_sampling'].get('high_impact_coverage'):.6f} |",
        f"| Claim status | `{payload['priority_100_sampling'].get('claim_status')}` |",
        "",
        "첫 배치는 priority-100 중에서도 candidate edge가 가장 많은 구간입니다. 이 수치는 검수 우선순위 설명용이며 human-gold 성능 증거가 아닙니다.",
        "",
        "## Annotator별 입력/저장 파일",
        "",
        md_table(
            ["owner", "batch_or_group", "expected_rows", "input_file", "reviewed_file", "present", "status"],
            payload["first_annotation_return_files"],
        ),
        "",
        "## 공통으로 열 파일",
        "",
        "| 역할 | 존재 | bytes | 경로 |",
        "|---|---:|---:|---|",
    ]
    for name, state in common.items():
        lines.append(f"| {name} | {state.get('exists')} | {state.get('bytes')} | `{state.get('path')}` |")
    lines += [
        "",
        "## 검수 규칙",
        "",
    ]
    for item in payload["guardrails"]:
        lines.append(f"- {item}")
    lines += [
        "",
        "## 반환 후 확인 명령",
        "",
        "반환 파일을 받으면 아래 순서로 확인합니다. `APPLY_IMPORTS=1`은 reviewed 파일들이 실제로 준비된 뒤에만 실행합니다.",
        "",
    ]
    for name, command in commands.items():
        lines += [f"### {name}", "", "```bash", command, "```", ""]
    lines += [
        "## 논문 claim 주의",
        "",
        "- 첫 배치 `full_120_priority_batch_001`은 20 chunks만 다룹니다.",
        "- A/B 둘 다 반환되어도 이 배치 하나만으로는 100 chunk IAA, adjudication, proposed human-gold scoring이 완료되지 않습니다.",
        "- 교수님께 보고할 때는 현재 상태를 `검수 시작 준비 완료, 사람 검수 반환 대기`로 표현해야 합니다.",
        "",
    ]
    return "\n".join(lines)


def run(args):
    payload = build_payload(args.experiment_dir, args.batch_id)
    write_json(payload["outputs"]["json"], payload)
    write_text(payload["outputs"]["markdown"], render_report(payload))
    print(json.dumps(payload["outputs"], ensure_ascii=False, indent=2))


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--batch-id", default=DEFAULT_BATCH_ID)
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
