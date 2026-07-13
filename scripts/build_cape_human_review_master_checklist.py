#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a Korean master checklist for CAPE-KG human review execution."""

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from cape_pre_human_status import effective_prehuman_summary


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")

MASTER_RETURN_FIELDS = [
    "requiredness",
    "required_for_minimum",
    "task_type",
    "owner",
    "batch_or_group",
    "expected_rows",
    "input_file",
    "reviewed_file",
    "present",
    "status",
    "why_it_matters",
    "next_action",
]

MINIMUM_RETURN_TASK_TYPES = {"human_gold_annotation", "human_gold_adjudication"}


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


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


def present_text(value):
    if isinstance(value, bool):
        return "yes" if value else "no"
    if value is None:
        return "no"
    text = str(value).strip().lower()
    if text in {"yes", "true", "1", "present"}:
        return "yes"
    return "no"


def count_present(rows):
    return sum(1 for row in rows if present_text(row.get("present")) == "yes")


def file_state(path):
    path = Path(path)
    return {"path": str(path), "exists": path.exists(), "bytes": path.stat().st_size if path.exists() else 0}


def required_reason(task_type):
    if task_type == "human_gold_annotation":
        return "100 chunk two-annotator gold와 IAA 계산에 필요"
    if task_type == "human_gold_adjudication":
        return "최종 adjudicated human-gold와 proposed human-gold scoring에 필요"
    if task_type == "mapping_expert_review":
        return "NCS/PCF mapping P@K, MRR, nDCG, accept-rate claim에 필요"
    if task_type == "crosswalk_expert_review":
        return "NCS-PCF crosswalk accept-rate, utility, ranking claim에 필요"
    if task_type == "active_review_human_effort":
        return "active review efficiency와 사람 검수 비용 claim에 필요"
    return "계획서의 human gate 증거에 필요"


def optional_reason(task_type):
    if task_type == "structural_review_checkpoint_candidates":
        return "ReviewCheckpoint 후보 45개를 구조적으로 정제하기 위한 선택 검수"
    if task_type == "structural_gateway_branch_gaps":
        return "DecisionGateway branch gap 4개를 검토하기 위한 선택 검수"
    return "구조 진단 후속 정제를 위한 선택 검수"


def normalize_required_rows(rows):
    normalized = []
    for row in rows:
        task_type = row.get("task_type", "")
        required_for_minimum = "yes" if task_type in MINIMUM_RETURN_TASK_TYPES else "no"
        normalized.append(
            {
                "requiredness": "required",
                "required_for_minimum": required_for_minimum,
                "task_type": task_type,
                "owner": row.get("owner", ""),
                "batch_or_group": row.get("batch_or_group", ""),
                "expected_rows": row.get("expected_rows", ""),
                "input_file": row.get("input_file", ""),
                "reviewed_file": row.get("reviewed_file", ""),
                "present": present_text(row.get("present")),
                "status": row.get("status", ""),
                "why_it_matters": required_reason(task_type),
                "next_action": row.get("next_action", ""),
            }
        )
    return normalized


def normalize_optional_rows(rows):
    normalized = []
    for row in rows:
        task_type = row.get("task_type", "")
        normalized.append(
            {
                "requiredness": "optional_structural",
                "required_for_minimum": "no",
                "task_type": task_type,
                "owner": row.get("owner", "structural_reviewer"),
                "batch_or_group": row.get("batch_or_group", "structural_gap_worklist"),
                "expected_rows": row.get("expected_rows", ""),
                "input_file": row.get("input_file", ""),
                "reviewed_file": row.get("reviewed_file", ""),
                "present": present_text(row.get("present")),
                "status": row.get("status", ""),
                "why_it_matters": optional_reason(task_type),
                "next_action": row.get("next_action", ""),
            }
        )
    return normalized


def build_payload(exp_dir):
    exp_dir = Path(exp_dir)
    release_dir = exp_dir / "06_release"
    review_dir = exp_dir / "05_review"
    handoff_dir = release_dir / "human_review_handoff"

    action_plan = read_json(release_dir / "human_gate_action_plan.json", {}) or {}
    structural_plan = read_json(release_dir / "structural_review_action_plan.json", {}) or {}
    human_preflight = read_json(release_dir / "human_review_return_preflight.json", {}) or {}
    structural_preflight = read_json(release_dir / "structural_review_return_preflight.json", {}) or {}
    claim_gate = read_json(release_dir / "claim_gate_report.json", {}) or {}
    pre_human = read_json(release_dir / "pre_human_handoff_validation.json", {}) or {}
    effective_pre_human = effective_prehuman_summary(pre_human)
    completion = read_json(release_dir / "submission_completion_audit_ko.json", {}) or {}
    compliance = read_json(release_dir / "eacl_plan_compliance_matrix.json", {}) or {}
    coverage = read_json(release_dir / "method_module_coverage.json", {}) or {}
    handoff = read_json(handoff_dir / "human_review_handoff_manifest.json", {}) or {}
    optional_strong = handoff.get("optional_strong_review") or {}

    required_rows = normalize_required_rows(action_plan.get("required_return_files") or [])
    optional_rows = normalize_optional_rows(structural_plan.get("optional_return_files") or [])
    all_rows = required_rows + optional_rows

    required_count = len(required_rows)
    optional_count = len(optional_rows)
    required_present = count_present(required_rows)
    optional_present = count_present(optional_rows)
    minimum_rows = [row for row in required_rows if row.get("required_for_minimum") == "yes"]
    optional_strong_rows = [row for row in required_rows if row.get("required_for_minimum") != "yes"]
    minimum_present = count_present(minimum_rows)
    optional_strong_present = count_present(optional_strong_rows)

    commands = {
        "verify_handoff_checksums": "sha256sum -c experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/human_review_handoff_checksums.sha256",
        "validate_required_returns": "python3 scripts/validate_cape_human_review_returns.py --experiment-dir experiments/cape_kg_eacl_20260627",
        "validate_optional_structural_returns": "python3 scripts/validate_cape_structural_review_returns.py --experiment-dir experiments/cape_kg_eacl_20260627",
        "dry_wrapper": "PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=0 bash scripts/run_cape_human_return_apply.sh",
        "apply_wrapper": "PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=1 bash scripts/run_cape_human_return_apply.sh",
        "dry_refresh": "PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=0 bash scripts/run_cape_post_annotation_refresh.sh",
        "apply_refresh": "PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=1 bash scripts/run_cape_post_annotation_refresh.sh",
        "validate_pre_human_handoff": "python3 scripts/validate_cape_pre_human_handoff.py --experiment-dir experiments/cape_kg_eacl_20260627 --outputs-dir outputs",
        "verify_release_checksums": "sha256sum -c experiments/cape_kg_eacl_20260627/06_release/release_bundle_checksums.sha256",
    }

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "claim_status": "human_review_master_checklist_ready_pending_human_returns",
        "summary": {
            "claim_gate_overall_status": claim_gate.get("overall_status"),
            "claim_gate_required_failure_count": claim_gate.get("required_failure_count"),
            "claim_gate_optional_failure_count": claim_gate.get("optional_failure_count"),
            "pre_human_handoff_validation": effective_pre_human.get("overall_status"),
            "human_return_preflight": human_preflight.get("overall_status"),
            "structural_return_preflight": structural_preflight.get("overall_status"),
            "completion_status": completion.get("overall_completion_status"),
            "goal_complete": (completion.get("completion_decision") or {}).get("goal_complete"),
            "compliance_claim_status": (compliance.get("summary") or {}).get("claim_status") or compliance.get("claim_status"),
            "method_claim_status": (coverage.get("summary") or {}).get("claim_status"),
            "required_return_files": required_count,
            "required_return_files_present": required_present,
            "required_return_files_missing": required_count - required_present,
            "minimum_paper_gate_return_files": len(minimum_rows),
            "minimum_paper_gate_return_files_present": minimum_present,
            "minimum_paper_gate_return_files_missing": len(minimum_rows) - minimum_present,
            "optional_strong_return_files": len(optional_strong_rows),
            "optional_strong_return_files_present": optional_strong_present,
            "optional_strong_return_files_missing": len(optional_strong_rows) - optional_strong_present,
            "optional_structural_return_files": optional_count,
            "optional_structural_return_files_present": optional_present,
            "optional_structural_return_files_missing": optional_count - optional_present,
            "master_return_files": len(all_rows),
            "master_return_files_present": required_present + optional_present,
            "master_return_files_missing": len(all_rows) - required_present - optional_present,
            "optional_strong_handoff_available": bool(optional_strong.get("available")),
            "optional_strong_package": optional_strong.get("package"),
            "optional_strong_review_units": optional_strong.get("rows"),
            "optional_strong_source_chunks": optional_strong.get("source_chunk_count"),
            "optional_strong_candidate_edges": optional_strong.get("candidate_edges_total"),
        },
        "blocking_claim_gates": [
            {
                "gate_id": gate.get("gate_id"),
                "status": gate.get("status"),
                "requirement": gate.get("requirement") or gate.get("description"),
                "required": gate.get("required"),
                "evidence": gate.get("evidence"),
            }
            for gate in claim_gate.get("gates", [])
            if gate.get("status") == "FAIL"
        ],
        "handoff_bundles": (handoff.get("bundles") or {}),
        "optional_strong_review": optional_strong,
        "required_return_files": required_rows,
        "optional_structural_return_files": optional_rows,
        "all_return_files": all_rows,
        "execution_order": [
            "1. Handoff bundle checksum을 먼저 확인한다.",
            "2. Annotator A/B가 priority 100 chunk를 독립적으로 검수한다.",
            "3. 10개 annotation reviewed JSONL을 정확한 파일명으로 저장한다.",
            "4. required return preflight를 실행해 JSONL 형식, row 수, 완료 상태를 확인한다.",
            "5. A/B import 후 IAA를 계산하고 adjudication draft를 생성한다.",
            "6. Adjudicator가 adjudication_edited.jsonl을 완성한다.",
            "7. APPLY_IMPORTS=1 refresh를 실행해 human-gold metrics와 P_cape_kg_actual scoring을 갱신한다.",
            "8. Mapping expert가 top20 group review를 완료하면 mapping metrics를 갱신한다.",
            "9. Active-review effort CSV를 채우면 active review efficiency claim을 갱신한다.",
            "10. 선택 사항으로 structural review 2개 CSV를 검수하되, 명시적 import/update 전에는 KG를 바꾸지 않는다.",
            "11. 선택 사항으로 strong 300+ resegmented package를 검수할 수 있다. 단, minimum gate의 annotation/adjudication 반환 파일을 대체하지 않는다.",
            "12. Claim gate, pre-human validation, release checksum을 다시 확인한다.",
        ],
        "commands": commands,
        "evidence_files": {
            "human_gate_action_plan": file_state(release_dir / "human_gate_action_plan.md"),
            "human_review_return_preflight": file_state(release_dir / "human_review_return_preflight.md"),
            "structural_review_action_plan": file_state(release_dir / "structural_review_action_plan.md"),
            "structural_review_return_preflight": file_state(release_dir / "structural_review_return_preflight.md"),
            "claim_gate_report": file_state(release_dir / "claim_gate_report.md"),
            "completion_audit": file_state(release_dir / "submission_completion_audit_ko.md"),
            "handoff_manifest": file_state(handoff_dir / "human_review_handoff_manifest.json"),
        },
        "outputs": {
            "markdown": str(release_dir / "human_review_master_checklist_ko.md"),
            "json": str(release_dir / "human_review_master_checklist_ko.json"),
            "csv": str(review_dir / "human_review_master_return_files.csv"),
        },
    }
    return payload


def table_row(values):
    return "| " + " | ".join(str(value).replace("|", "\\|") for value in values) + " |"


def render_return_table(rows):
    lines = [
        "| 구분 | minimum | 작업 | 담당 | 묶음 | 예상 rows | 현재 | reviewed 파일 |",
        "|---|---|---|---|---|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            table_row(
                [
                    row.get("requiredness"),
                    row.get("required_for_minimum"),
                    row.get("task_type"),
                    row.get("owner"),
                    row.get("batch_or_group"),
                    row.get("expected_rows"),
                    f"{row.get('present')} / {row.get('status')}",
                    f"`{row.get('reviewed_file')}`",
                ]
            )
        )
    return "\n".join(lines)


def render_report(payload):
    summary = payload["summary"]
    commands = payload["commands"]
    lines = [
        "# CAPE-KG 사람 검수 실행 마스터 체크리스트",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Experiment: `{payload['experiment_dir']}`",
        "",
        "## 1. 현재 결론",
        "",
        "현재 자동 KG 구축, LLM baseline/proposed/ablation, public benchmark adapter, release bundle, pre-human validation은 준비되어 있습니다. 그러나 논문 수준의 최종 성능 claim은 아직 하면 안 됩니다. 이유는 human-gold annotation, IAA, adjudication, proposed-method human-gold scoring이 완료되지 않았기 때문입니다.",
        "",
        "| 항목 | 현재 값 |",
        "|---|---:|",
        f"| Claim gate | `{summary.get('claim_gate_overall_status')}` |",
        f"| Required claim-gate failures | {summary.get('claim_gate_required_failure_count')} |",
        f"| Optional claim-gate failures | {summary.get('claim_gate_optional_failure_count')} |",
        f"| Pre-human handoff validation | `{summary.get('pre_human_handoff_validation')}` |",
        f"| Required return preflight | `{summary.get('human_return_preflight')}` |",
        f"| Optional structural preflight | `{summary.get('structural_return_preflight')}` |",
        f"| Minimum paper-gate human returns | {summary.get('minimum_paper_gate_return_files_present')}/{summary.get('minimum_paper_gate_return_files')} |",
        f"| Optional/strong claim returns | {summary.get('optional_strong_return_files_present')}/{summary.get('optional_strong_return_files')} |",
        f"| Required claim/human return files | {summary.get('required_return_files_present')}/{summary.get('required_return_files')} |",
        f"| Optional structural review files | {summary.get('optional_structural_return_files_present')}/{summary.get('optional_structural_return_files')} |",
        f"| All master return files | {summary.get('master_return_files_present')}/{summary.get('master_return_files')} |",
        f"| Optional strong handoff | `{summary.get('optional_strong_handoff_available')}` |",
        f"| Optional strong package | `{summary.get('optional_strong_package')}` |",
        f"| Optional strong review units | {summary.get('optional_strong_review_units')} |",
        f"| Goal complete | `{summary.get('goal_complete')}` |",
        "",
        "## 2. Claim을 막고 있는 항목",
        "",
        "| gate | 필수 | status | requirement | evidence |",
        "|---|---:|---|---|---|",
    ]
    for gate in payload["blocking_claim_gates"]:
        lines.append(
            table_row(
                [
                    f"`{gate.get('gate_id')}`",
                    "yes" if gate.get("required") else "no",
                    gate.get("status"),
                    gate.get("requirement"),
                    gate.get("evidence"),
                ]
            )
        )
    lines += [
        "",
        "## 3. 실행 순서",
        "",
    ]
    lines.extend(f"- {step}" for step in payload["execution_order"])
    lines += [
        "",
        "## 4. Required claim/human 반환 파일 14개",
        "",
        "아래 14개 파일은 논문 claim과 직접 연결되는 required claim/human 반환 파일입니다. 이 중 `minimum = yes`인 annotation/adjudication 11개 파일이 minimum paper-gate를 여는 필수 반환 파일이고, mapping expert review, NCS-PCF crosswalk expert review, active-review effort 3개는 optional/strong claim을 위한 반환 파일입니다. 선택 structural review 2개까지 포함한 master manifest 전체는 16개입니다. 파일명은 반드시 표의 `reviewed 파일` 경로와 동일해야 합니다.",
        "",
        render_return_table(payload["required_return_files"]),
        "",
        "## 5. 선택 구조 검수 파일 2개",
        "",
        "아래 2개 파일은 구조 진단 후속 정제를 위한 선택 검수입니다. minimum paper-gate의 annotation/adjudication 반환 파일을 대체하지 않으며, reviewed 파일이 돌아오기 전에는 KG를 자동 수정하지 않습니다.",
        "",
        render_return_table(payload["optional_structural_return_files"]),
        "",
        "## 6. 선택 Strong 300+ 검수 Bundle",
        "",
    ]
    strong = payload.get("optional_strong_review") or {}
    bundles = payload.get("handoff_bundles") or {}
    strong_bundle = (bundles.get("strong_resegmented_review") or {}).get("path")
    if strong.get("available"):
        lines += [
            "이 bundle은 강한 accept 가능권의 300~500 chunk human-gold 목표를 위한 선택 검수 자료입니다. minimum paper-gate의 annotation/adjudication 반환 파일을 대체하지 않습니다.",
            "",
            f"- Package: `{strong.get('package')}`",
            f"- Review units: {strong.get('rows')}",
            f"- Source chunks represented: {strong.get('source_chunk_count')}",
            f"- Candidate edges: {strong.get('candidate_edges_total')}",
            f"- Bundle: `{strong_bundle}`",
            f"- Annotator A reviewed file: `{(strong.get('expected_reviewed_files') or {}).get('annotator_A')}`",
            f"- Annotator B reviewed file: `{(strong.get('expected_reviewed_files') or {}).get('annotator_B')}`",
            f"- Adjudication reviewed file: `{(strong.get('expected_reviewed_files') or {}).get('adjudication')}`",
            "",
        ]
    else:
        lines += ["Strong 300+ optional handoff bundle is not available in the current manifest.", ""]
    lines += [
        "## 7. 파일별 의미",
        "",
        "| 구분 | 작업 | 왜 필요한가 | 다음 행동 |",
        "|---|---|---|---|",
    ]
    for row in payload["all_return_files"]:
        lines.append(
            table_row(
                [
                    row.get("requiredness"),
                    row.get("task_type"),
                    row.get("why_it_matters"),
                    row.get("next_action"),
                ]
            )
        )
    lines += [
        "",
        "## 8. 실행 명령",
        "",
        "Handoff bundle checksum 확인:",
        "",
        "```bash",
        commands["verify_handoff_checksums"],
        "```",
        "",
        "필수 사람 반환 파일 preflight:",
        "",
        "```bash",
        commands["validate_required_returns"],
        "```",
        "",
        "선택 구조 검수 반환 파일 preflight:",
        "",
        "```bash",
        commands["validate_optional_structural_returns"],
        "```",
        "",
        "권장 dry-run wrapper:",
        "",
        "```bash",
        commands["dry_wrapper"],
        "```",
        "",
        "권장 apply wrapper:",
        "",
        "```bash",
        commands["apply_wrapper"],
        "```",
        "",
        "저수준 dry refresh:",
        "",
        "```bash",
        commands["dry_refresh"],
        "```",
        "",
        "저수준 apply refresh:",
        "",
        "```bash",
        commands["apply_refresh"],
        "```",
        "",
        "최종 검증:",
        "",
        "```bash",
        commands["validate_pre_human_handoff"],
        commands["verify_release_checksums"],
        "```",
        "",
        "## 9. 발표 및 논문 작성 시 주의 문구",
        "",
        "- 말할 수 있음: KG 구축, LLM 실행, baseline/ablation, 구조 진단, handoff 준비는 완료.",
        "- 말할 수 있음: 현재 claim gate 실패는 실험 실패가 아니라 human-gold 미완료를 막는 보수적 안전장치.",
        "- 아직 말하면 안 됨: CAPE-KG가 최종적으로 baseline보다 우수하다는 human-gold 기반 성능 claim.",
        "- 아직 말하면 안 됨: NCS/PCF mapping P@K, MRR, nDCG, expert accept-rate가 확정되었다는 claim.",
        "- 아직 말하면 안 됨: optional strong 342개 검수 단위가 실제 342개 adjudicated gold chunk로 완료되었다는 claim.",
        "",
        "## 10. 산출물",
        "",
        f"- JSON: `{payload['outputs']['json']}`",
        f"- Markdown: `{payload['outputs']['markdown']}`",
        f"- CSV: `{payload['outputs']['csv']}`",
        "",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    args = parser.parse_args()

    exp_dir = Path(args.experiment_dir)
    payload = build_payload(exp_dir)
    outputs = payload["outputs"]
    write_json(outputs["json"], payload)
    write_text(outputs["markdown"], render_report(payload))
    write_csv(outputs["csv"], payload["all_return_files"], MASTER_RETURN_FIELDS)
    print(
        json.dumps(
            {
                "markdown": outputs["markdown"],
                "json": outputs["json"],
                "csv": outputs["csv"],
                "claim_status": payload["claim_status"],
                "required_return_files": len(payload["required_return_files"]),
                "optional_structural_return_files": len(payload["optional_structural_return_files"]),
                "required_present": payload["summary"]["required_return_files_present"],
                "optional_present": payload["summary"]["optional_structural_return_files_present"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
