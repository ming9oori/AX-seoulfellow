#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build role-specific quickstart cards for CAPE-KG human review."""

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")


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


def bundle_path(handoff_manifest, key):
    bundle = (handoff_manifest.get("bundles") or {}).get(key) or {}
    if bundle.get("path"):
        return bundle["path"]
    default_names = {
        "annotator_A": "cape_human_gold_annotator_A_priority100.tar.gz",
        "annotator_B": "cape_human_gold_annotator_B_priority100.tar.gz",
        "coordinator": "cape_human_gold_coordinator_priority100.tar.gz",
        "adjudicator": "cape_human_gold_adjudicator_full120.tar.gz",
        "mapping_expert": "cape_mapping_expert_review_top20_groups.tar.gz",
        "crosswalk_expert": "cape_crosswalk_expert_review_ncs_pcf.tar.gz",
        "active_review_effort": "cape_active_review_human_effort.tar.gz",
        "structural_reviewer": "cape_structural_review_optional.tar.gz",
        "strong_resegmented_review": "cape_human_gold_strong_resegmented_342.tar.gz",
    }
    name = default_names.get(key)
    if not name:
        return ""
    exp_dir = Path(handoff_manifest.get("experiment_dir") or DEFAULT_EXP_DIR)
    return str(exp_dir / "06_release/human_review_handoff" / name)


def rows_for_owner(return_rows, owner):
    return [row for row in return_rows if row.get("owner") == owner]


def first_path(rows, key):
    for row in rows:
        value = row.get(key)
        if value:
            return value
    return ""


def build_annotation_card(exp_dir, owner, bundle_key, return_rows, handoff_manifest):
    rows = rows_for_owner(return_rows, owner)
    first_batch = [row for row in rows if row.get("batch_or_group") == "full_120_priority_batch_001"]
    return {
        "role": owner,
        "bundle": bundle_path(handoff_manifest, bundle_key),
        "goal": "priority 100 chunks 중 배정된 5개 batch를 독립 검수",
        "start_here": str(exp_dir / "05_review/human_review_first_batch_execution_card_ko.md"),
        "open_files": [
            str(exp_dir / "01_data/gold_annotation/annotation_workbench.html"),
            str(exp_dir / "01_data/annotation_guideline_v1.md"),
            str(exp_dir / "06_release/annotation_calibration_pack_ko.md"),
            first_path(first_batch or rows, "input_file"),
        ],
        "save_files": [row.get("reviewed_file", "") for row in rows],
        "first_required_return": first_path(first_batch or rows, "reviewed_file"),
        "claim_note": "A/B가 같은 100 chunks를 모두 완료하고 IAA/adjudication이 끝나기 전까지 human-gold claim 금지",
        "return_rows": rows,
    }


def build_payload(exp_dir):
    exp_dir = Path(exp_dir)
    release_dir = exp_dir / "06_release"
    review_dir = exp_dir / "05_review"
    handoff_dir = release_dir / "human_review_handoff"

    return_rows = read_csv(review_dir / "human_review_master_return_files.csv")
    optional_structural_rows = read_csv(review_dir / "structural_review_optional_returns.csv")
    handoff_manifest = read_json(handoff_dir / "human_review_handoff_manifest.json", {}) or {}
    dashboard = read_json(release_dir / "human_review_status_dashboard_ko.json", {}) or {}
    prehuman = read_json(release_dir / "pre_human_handoff_validation.json", {}) or {}
    first_batch = read_json(review_dir / "human_review_first_batch_execution_card.json", {}) or {}
    strong_manifest = read_json(handoff_dir / "strong_resegmented_review_manifest.json", {}) or {}

    summary = dashboard.get("summary") or {}
    commands = {
        "verify_handoff_checksums": "sha256sum -c experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/human_review_handoff_checksums.sha256",
        "validate_required_returns": "python3 scripts/validate_cape_human_review_returns.py --experiment-dir experiments/cape_kg_eacl_20260627",
        "validate_strong_returns": "python3 scripts/validate_cape_strong_review_returns.py --experiment-dir experiments/cape_kg_eacl_20260627",
        "dry_run_human_return_apply": "PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=0 bash scripts/run_cape_human_return_apply.sh",
        "apply_human_returns": "PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=1 bash scripts/run_cape_human_return_apply.sh",
        "validate_pre_human_handoff": "python3 scripts/validate_cape_pre_human_handoff.py --experiment-dir experiments/cape_kg_eacl_20260627 --outputs-dir outputs",
    }

    cards = [
        build_annotation_card(exp_dir, "annotator_A", "annotator_A", return_rows, handoff_manifest),
        build_annotation_card(exp_dir, "annotator_B", "annotator_B", return_rows, handoff_manifest),
    ]

    adjudication_rows = [row for row in return_rows if row.get("task_type") == "human_gold_adjudication"]
    mapping_rows = [row for row in return_rows if row.get("task_type") == "mapping_expert_review"]
    crosswalk_rows = [row for row in return_rows if row.get("task_type") == "crosswalk_expert_review"]
    active_rows = [row for row in return_rows if row.get("task_type") == "active_review_human_effort"]

    cards.extend(
        [
            {
                "role": "coordinator",
                "bundle": bundle_path(handoff_manifest, "coordinator"),
                "goal": "반환 파일 무결성 확인, preflight, dry-run/apply orchestration",
                "start_here": str(release_dir / "human_review_start_here_ko.md"),
                "open_files": [
                    str(handoff_dir / "human_review_handoff_checksums.sha256"),
                    str(release_dir / "human_review_status_dashboard_ko.md"),
                    str(review_dir / "human_review_master_return_files.csv"),
                    str(review_dir / "human_review_role_quickstart_cards_ko.md"),
                ],
                "save_files": [
                    str(release_dir / "human_review_return_preflight.md"),
                    str(release_dir / "human_return_apply_last_run.md"),
                    str(release_dir / "pre_human_handoff_validation.md"),
                ],
                "first_required_return": first_path(rows_for_owner(return_rows, "annotator_A"), "reviewed_file"),
                "claim_note": "checksum/preflight 통과는 claim evidence가 아니라 import safety evidence",
                "return_rows": [],
            },
            {
                "role": "adjudicator",
                "bundle": bundle_path(handoff_manifest, "adjudicator"),
                "goal": "A/B disagreement를 adjudication하여 final human-gold 생성",
                "start_here": str(exp_dir / "01_data/gold_annotation/adjudication_protocol.md"),
                "open_files": [first_path(adjudication_rows, "input_file"), str(exp_dir / "01_data/gold_annotation/adjudication_protocol.md")],
                "save_files": [first_path(adjudication_rows, "reviewed_file")],
                "first_required_return": first_path(adjudication_rows, "reviewed_file"),
                "claim_note": "adjudication_edited.jsonl import 전에는 proposed human-gold scoring claim 금지",
                "return_rows": adjudication_rows,
            },
            {
                "role": "mapping_expert",
                "bundle": bundle_path(handoff_manifest, "mapping_expert"),
                "goal": "NCS/PCF mapping top20 priority groups의 top-5 후보 검수",
                "start_here": str(exp_dir / "01_data/mapping_review/mapping_review_protocol.md"),
                "open_files": [first_path(mapping_rows, "input_file"), str(exp_dir / "05_review/mapping_review_next_20_groups.csv")],
                "save_files": [first_path(mapping_rows, "reviewed_file")],
                "first_required_return": first_path(mapping_rows, "reviewed_file"),
                "claim_note": "expert-reviewed file import 전에는 mapping P@K/MRR/nDCG claim 금지",
                "return_rows": mapping_rows,
            },
            {
                "role": "crosswalk_expert",
                "bundle": bundle_path(handoff_manifest, "crosswalk_expert"),
                "goal": "NCS-PCF crosswalk 후보 220 rows의 utility/ranking 검수",
                "start_here": str(exp_dir / "01_data/crosswalk_review/crosswalk_review_protocol.md"),
                "open_files": [first_path(crosswalk_rows, "input_file"), str(exp_dir / "01_data/crosswalk_review/crosswalk_review_sheet.csv")],
                "save_files": [first_path(crosswalk_rows, "reviewed_file")],
                "first_required_return": first_path(crosswalk_rows, "reviewed_file"),
                "claim_note": "expert-reviewed file import 전에는 crosswalk accept-rate/utility claim 금지",
                "return_rows": crosswalk_rows,
            },
            {
                "role": "active_reviewer",
                "bundle": bundle_path(handoff_manifest, "active_review_effort"),
                "goal": "active/random review effort와 timing 기록",
                "start_here": str(release_dir / "active_review_human_effort_briefing.md"),
                "open_files": [first_path(active_rows, "input_file"), str(review_dir / "actual_llm_active_review_queue_P_cape_kg_actual.csv")],
                "save_files": [first_path(active_rows, "reviewed_file")],
                "first_required_return": first_path(active_rows, "reviewed_file"),
                "claim_note": "review_seconds/corrected_error 없는 상태에서는 active-review efficiency claim 금지",
                "return_rows": active_rows,
            },
            {
                "role": "structural_reviewer",
                "bundle": bundle_path(handoff_manifest, "structural_reviewer"),
                "goal": "optional structural gap/checkpoint 후보 검수",
                "start_here": str(release_dir / "structural_review_action_plan.md"),
                "open_files": [row.get("input_file", "") for row in optional_structural_rows],
                "save_files": [row.get("reviewed_file", "") for row in optional_structural_rows],
                "first_required_return": first_path(optional_structural_rows, "reviewed_file"),
                "claim_note": "선택 구조 검수이며 minimum paper gate의 대체 evidence가 아님",
                "return_rows": optional_structural_rows,
            },
            {
                "role": "strong_resegmented_review",
                "bundle": bundle_path(handoff_manifest, "strong_resegmented_review"),
                "goal": "optional 342 resegmented review units의 strong setting 검수",
                "start_here": str(handoff_dir / "README_strong_resegmented_review_ko.md"),
                "open_files": [
                    strong_manifest.get("annotator_A_file", ""),
                    strong_manifest.get("annotator_B_file", ""),
                    strong_manifest.get("tracking_sheet", ""),
                ],
                "save_files": list((strong_manifest.get("expected_reviewed_files") or {}).values()),
                "first_required_return": (strong_manifest.get("expected_reviewed_files") or {}).get("annotator_A", ""),
                "claim_note": "strong 300+ claim은 optional이며 A/B/adjudication 완료 후에만 가능",
                "return_rows": [],
            },
        ]
    )

    outputs = {
        "markdown": str(review_dir / "human_review_role_quickstart_cards_ko.md"),
        "json": str(review_dir / "human_review_role_quickstart_cards.json"),
        "csv": str(review_dir / "human_review_role_quickstart_cards.csv"),
    }

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "claim_status": "role_quickstart_ready_pending_human_returns",
        "summary": {
            "pre_human_handoff_status": prehuman.get("overall_status"),
            "pre_human_handoff_checks": prehuman.get("check_count"),
            "minimum_return_files": summary.get("minimum_return_files_total"),
            "minimum_return_files_present": summary.get("minimum_return_files_present"),
            "required_return_files": summary.get("required_return_files_total"),
            "required_return_files_present": summary.get("required_return_files_present"),
            "optional_structural_return_files": summary.get("optional_structural_return_files_total"),
            "optional_structural_return_files_present": summary.get("optional_structural_return_files_present"),
            "master_return_files": summary.get("master_return_files_total"),
            "master_return_files_present": summary.get("master_return_files_present"),
            "first_batch_id": first_batch.get("batch_id"),
            "role_count": len(cards),
        },
        "commands": commands,
        "cards": cards,
        "source_files": {
            "handoff_manifest": file_state(handoff_dir / "human_review_handoff_manifest.json"),
            "master_return_files": file_state(review_dir / "human_review_master_return_files.csv"),
            "dashboard": file_state(release_dir / "human_review_status_dashboard_ko.json"),
            "first_batch_card": file_state(review_dir / "human_review_first_batch_execution_card.json"),
            "structural_optional_returns": file_state(review_dir / "structural_review_optional_returns.csv"),
        },
        "outputs": outputs,
    }


def csv_rows(cards):
    rows = []
    for card in cards:
        rows.append(
            {
                "role": card.get("role"),
                "bundle": card.get("bundle"),
                "start_here": card.get("start_here"),
                "first_open_file": (card.get("open_files") or [""])[0],
                "first_required_return": card.get("first_required_return"),
                "claim_note": card.get("claim_note"),
            }
        )
    return rows


def render_report(payload):
    summary = payload["summary"]
    lines = [
        "# CAPE-KG 역할별 사람 검수 Quickstart",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Experiment: `{payload['experiment_dir']}`",
        "",
        "이 문서는 역할별로 지금 열 파일, 저장 파일, 반환 후 명령을 빠르게 확인하기 위한 내부 실행 카드입니다. 자세한 기준은 각 protocol/checklist를 따릅니다.",
        "",
        "## 상태 요약",
        "",
        f"- Pre-human handoff: `{summary.get('pre_human_handoff_status')}`",
        f"- Pre-human checks: {summary.get('pre_human_handoff_checks')}",
        f"- Minimum return files: {summary.get('minimum_return_files_present')}/{summary.get('minimum_return_files')}",
        f"- Required claim/human return files: {summary.get('required_return_files_present')}/{summary.get('required_return_files')}",
        f"- Optional structural review files: {summary.get('optional_structural_return_files_present')}/{summary.get('optional_structural_return_files')}",
        f"- All master return files: {summary.get('master_return_files_present')}/{summary.get('master_return_files')}",
        f"- First batch: `{summary.get('first_batch_id')}`",
        f"- Roles: {summary.get('role_count')}",
        "",
        "## 역할별 카드",
        "",
    ]
    for card in payload["cards"]:
        lines += [
            f"### {card['role']}",
            "",
            f"- Bundle: `{card.get('bundle')}`",
            f"- Goal: {card.get('goal')}",
            f"- Start here: `{card.get('start_here')}`",
            f"- First required return: `{card.get('first_required_return')}`",
            f"- Claim note: {card.get('claim_note')}",
            "",
            "Open files:",
        ]
        for item in card.get("open_files") or []:
            if item:
                lines.append(f"- `{item}`")
        lines += ["", "Save/return files:"]
        for item in card.get("save_files") or []:
            if item:
                lines.append(f"- `{item}`")
        lines.append("")
        rows = card.get("return_rows") or []
        if rows:
            lines += [
                "Return rows:",
                "",
                md_table(["owner", "task_type", "batch_or_group", "expected_rows", "input_file", "reviewed_file", "present", "status"], rows),
                "",
            ]
    lines += ["## 공통 명령", ""]
    for name, command in payload["commands"].items():
        lines += [f"### {name}", "", "```bash", command, "```", ""]
    lines += [
        "## Source Files",
        "",
        md_table(["path", "exists", "bytes"], list(payload["source_files"].values())),
        "",
        "## Output Files",
        "",
        f"- Markdown: `{payload['outputs']['markdown']}`",
        f"- JSON: `{payload['outputs']['json']}`",
        f"- CSV: `{payload['outputs']['csv']}`",
        "",
    ]
    return "\n".join(lines)


def run(args):
    payload = build_payload(args.experiment_dir)
    write_json(payload["outputs"]["json"], payload)
    write_text(payload["outputs"]["markdown"], render_report(payload))
    write_csv(
        payload["outputs"]["csv"],
        csv_rows(payload["cards"]),
        ["role", "bundle", "start_here", "first_open_file", "first_required_return", "claim_note"],
    )
    print(json.dumps(payload["outputs"], ensure_ascii=False, indent=2))


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
