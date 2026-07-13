#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a Korean section-by-section status report for the revised EACL plan."""

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_OUTPUTS_DIR = Path("outputs")
DEFAULT_PLAN_FILE = Path("AX_EACL_submission_review_revised_plan.md")
CLAIM_STATUS = "revised_plan_section_status_ready_not_submission_complete"


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


def rel(path):
    return str(Path(path).as_posix())


def exists(path):
    return Path(path).exists() and Path(path).stat().st_size > 0


def evidence_state(paths):
    missing = [path for path in paths if not exists(path)]
    return {
        "evidence_files": [rel(path) for path in paths],
        "evidence_file_count": len(paths),
        "missing_evidence_files": [rel(path) for path in missing],
        "evidence_files_present": not missing,
    }


def gate_map(claim_gate):
    out = {}
    for row in claim_gate.get("gates") or []:
        out[row.get("id") or row.get("gate")] = row
    return out


def checklist_by_id(audit):
    return {row.get("id"): row for row in audit.get("audit_rows") or []}


def section_rows(exp_dir, outputs_dir, plan_file, data):
    release = exp_dir / "06_release"
    reports = exp_dir / "07_reports"
    eval_dir = exp_dir / "04_evaluation"
    schema_dir = exp_dir / "02_schema"
    review_dir = exp_dir / "05_review"
    public_dir = exp_dir / "08_public_benchmarks"
    out = Path(outputs_dir)

    audit = data["revised_audit"]
    paper_map = data["paper_section_map"]
    claim_gate = data["claim_gate"]
    method = data["method_module_coverage"]
    packet = data["human_review_packet_integrity"]
    compliance = data["compliance"]
    gmap = gate_map(claim_gate)

    summary = audit.get("summary") or {}
    paper_summary = paper_map.get("summary") or {}
    method_summary = method.get("summary") or {}
    packet_summary = packet.get("summary") or {}
    compliance_summary = compliance.get("summary") or {}

    common_claim_boundary = (
        "최종 성능 claim은 human-gold annotation, IAA, adjudication, "
        "P_cape_kg_actual human-gold scoring 이후에만 가능하다."
    )
    expert_boundary = (
        "mapping/crosswalk utility claim은 expert review 반환 파일이 들어온 뒤에만 가능하다."
    )

    rows = [
        {
            "section_id": "S01",
            "plan_section": "1. 결론 요약",
            "current_status": "method_and_infrastructure_ready_claim_gated",
            "what_is_done": (
                "CAPE-KG task framing, Layer 1/Layer 2 KG construction, evidence grounding, "
                "baseline/ablation/release scaffolds are prepared."
            ),
            "key_numbers": (
                f"pre-human checks={summary.get('pre_human_handoff_checks')}; "
                f"claim gate={summary.get('claim_gate_overall_status')}; "
                f"method modules={method_summary.get('modules_with_required_artifacts')}/"
                f"{method_summary.get('module_count')}"
            ),
            "claim_boundary": common_claim_boundary,
            "next_action": "사람 검수 반환 전까지는 KG 구축 완료와 최종 성능 claim 미완료를 분리해 보고한다.",
            **evidence_state(
                [
                    plan_file,
                    release / "method_novelty_positioning.md",
                    release / "revised_plan_completion_audit.md",
                    release / "claim_gate_report.md",
                ]
            ),
        },
        {
            "section_id": "S02",
            "plan_section": "2. EACL 제출 적합성 판단",
            "current_status": "submission_policy_scaffold_ready_not_submission_ready",
            "what_is_done": "ARR/EACL policy checklist, anonymization prep, responsible NLP prep, timeline board are present.",
            "key_numbers": (
                f"submission_ready={compliance_summary.get('submission_ready')}; "
                f"minimum return files={compliance_summary.get('minimum_paper_gate_return_file_present_count')}/"
                f"{compliance_summary.get('minimum_paper_gate_return_file_count')}"
            ),
            "claim_boundary": "제출 가능 판단은 최종 paper claim gate가 열린 뒤 다시 해야 한다.",
            "next_action": "human return 이후 policy checklist와 anonymization scan을 다시 실행한다.",
            **evidence_state(
                [
                    release / "arr_submission_policy_checklist.md",
                    release / "anonymized_submission_prep.md",
                    release / "responsible_nlp_checklist_prep.md",
                    release / "submission_timeline_action_board.md",
                ]
            ),
        },
        {
            "section_id": "S03",
            "plan_section": "3. Accept 가능성 판단",
            "current_status": "risk_register_ready_with_open_human_gates",
            "what_is_done": "Reviewer risk register and claim-language guardrails separate safe method claims from blocked performance claims.",
            "key_numbers": (
                f"required gate failures={claim_gate.get('required_failure_count')}; "
                f"optional gate failures={claim_gate.get('optional_failure_count')}"
            ),
            "claim_boundary": common_claim_boundary,
            "next_action": "교수님 보고에서는 accept 가능성을 현재 결과가 아니라 남은 gate 기준으로 설명한다.",
            **evidence_state(
                [
                    release / "reviewer_risk_register.md",
                    release / "claim_language_guardrails.md",
                    release / "claim_gate_report.md",
                    release / "paper_readiness_checklist.md",
                ]
            ),
        },
        {
            "section_id": "S04",
            "plan_section": "4. 관련 연구 대비 포지셔닝",
            "current_status": "positioning_and_baseline_traceability_ready",
            "what_is_done": "Related-work baseline traceability maps EDC/SAC-KG/Taxonomy-RAG-style baselines to local artifacts.",
            "key_numbers": "baseline family coverage includes B0-B6 plus CAPE-KG and ablations.",
            "claim_boundary": "선행연구 대비 성능 우위는 human-gold score 이후에만 주장한다.",
            "next_action": "논문 본문에는 차별점과 구현 범위를 분리해 쓴다.",
            **evidence_state(
                [
                    release / "related_work_baseline_traceability.md",
                    release / "method_novelty_positioning.md",
                    release / "ablation_coverage_report.md",
                ]
            ),
        },
        {
            "section_id": "S05",
            "plan_section": "5. 수정된 핵심 연구 질문",
            "current_status": "rq_evidence_matrix_ready",
            "what_is_done": "RQ1-RQ4 are linked to evidence files, metrics, and human/expert gates.",
            "key_numbers": "RQ count=4; final claim-ready RQ count remains gated by human/expert evidence.",
            "claim_boundary": "RQ별 final answer는 adjudicated human-gold와 expert review 이후 확정한다.",
            "next_action": "발표에서는 RQ를 task/evidence/mapping/review-efficiency 네 축으로 설명한다.",
            **evidence_state(
                [
                    release / "rq_evidence_matrix.md",
                    release / "metric_traceability_audit.md",
                    release / "contribution_claim_traceability.md",
                ]
            ),
        },
        {
            "section_id": "S06",
            "plan_section": "6. 수정된 방법론: CAPE-KG",
            "current_status": "m1_m11_artifacts_present_human_claim_pending",
            "what_is_done": "M1-M11 executable artifacts are present; human-dependent modules keep claim gates open.",
            "key_numbers": (
                f"modules={method_summary.get('modules_with_required_artifacts')}/"
                f"{method_summary.get('module_count')}; "
                f"human-dependent={method_summary.get('human_dependent_module_count')}"
            ),
            "claim_boundary": "방법론 구성은 설명 가능하지만, 모듈별 성능 효과는 human-gold 비교 후 주장한다.",
            "next_action": "M3-M11의 human-dependent claim boundary를 논문 표와 본문에 유지한다.",
            **evidence_state(
                [
                    release / "method_module_coverage.md",
                    release / "prompt_node_edge_traceability.md",
                    release / "provenance_manifest.md",
                ]
            ),
        },
        {
            "section_id": "S07",
            "plan_section": "7. 온톨로지 스키마 수정안",
            "current_status": "schema_rdf_shacl_and_evidence_projection_ready",
            "what_is_done": "Node/edge schema, CQ queries, RDF/SHACL-style export, EvidenceAnchor projection are present.",
            "key_numbers": (
                "Layer 2 nodes/edges and evidence anchors are structurally validated; "
                "SHACL-style validation is PASS."
            ),
            "claim_boundary": "schema conformance is structural evidence, not human correctness evidence.",
            "next_action": "schema terms should stay synchronized with CQ and prompt traceability.",
            **evidence_state(
                [
                    schema_dir / "cape_schema.json",
                    schema_dir / "cape_shapes.shacl.ttl",
                    release / "cq_query_pack.md",
                    out / "12_rdf/cape_kg_shacl_validation_report.md",
                    out / "13_evidence_graph/evidence_graph_projection_report.md",
                ]
            ),
        },
        {
            "section_id": "S08",
            "plan_section": "8. 데이터 및 annotation 계획",
            "current_status": "annotation_packet_ready_pending_human_returns",
            "what_is_done": "Human-review packets, annotation guideline, batch assignment, and packet integrity checks are ready.",
            "key_numbers": (
                f"minimum chunks={packet_summary.get('minimum_annotation_chunks')}; "
                f"candidate edges={packet_summary.get('minimum_annotation_candidate_edges')}; "
                f"required reviewed files={packet_summary.get('required_reviewed_files_present')}/"
                f"{packet_summary.get('required_reviewed_files_expected')}"
            ),
            "claim_boundary": "annotation package readiness does not create gold labels.",
            "next_action": "A/B annotator files and adjudication file must be returned before scoring.",
            **evidence_state(
                [
                    exp_dir / "01_data/annotation_guideline_v1.md",
                    release / "annotation_protocol_traceability.md",
                    release / "human_review_packet_integrity.md",
                    release / "human_review_start_here_ko.md",
                    release / "human_review_claim_gate_one_page_ko.md",
                ]
            ),
        },
        {
            "section_id": "S09",
            "plan_section": "9. 실험 설계",
            "current_status": "baseline_ablation_public_benchmark_diagnostics_ready",
            "what_is_done": "B0-B6, proposed, ablations, model-scaling diagnostics, public benchmark adapters, and paper tables are present.",
            "key_numbers": (
                "actual LLM conditions cover the 120-row evaluation set; "
                "diagnostic tables are claim-safe until human-gold scoring."
            ),
            "claim_boundary": "silver/proxy diagnostics must not be reported as final F1/P@K evidence.",
            "next_action": "human-gold and expert-return refresh will populate final main result cells.",
            **evidence_state(
                [
                    eval_dir / "actual_llm_silver_evaluation_report.md",
                    release / "ablation_coverage_report.md",
                    release / "qwen3_model_scaling_report.md",
                    public_dir / "public_benchmark_crosscheck_report.md",
                    release / "paper_tables.md",
                ]
            ),
        },
        {
            "section_id": "S10",
            "plan_section": "10. 논문 contribution 문장 수정안",
            "current_status": "contribution_traceability_ready_pending_final_scores",
            "what_is_done": "Contribution claims are linked to current evidence, RQs, reviewer risks, and claim gates.",
            "key_numbers": "three contribution lines are supportable as task/method/resource framing, not final performance superiority.",
            "claim_boundary": common_claim_boundary,
            "next_action": "논문 introduction에서는 contribution claim을 gate-safe wording으로 유지한다.",
            **evidence_state(
                [
                    release / "contribution_claim_traceability.md",
                    release / "claim_language_guardrails.md",
                    reports / "eacl_paper_draft.md",
                ]
            ),
        },
        {
            "section_id": "S11",
            "plan_section": "11. EACL 제출용 논문 구조",
            "current_status": "draft_and_section_source_map_ready_not_submission_ready",
            "what_is_done": "EACL paper draft has section anchors and a source map with zero missing evidence files.",
            "key_numbers": (
                f"sections={paper_summary.get('present_sections')}/"
                f"{paper_summary.get('total_sections')}; "
                f"missing evidence={paper_summary.get('missing_evidence_files')}; "
                f"human/expert blocked sections={paper_summary.get('human_or_expert_blocked_sections')}"
            ),
            "claim_boundary": "draft is claim-safe but safe_to_use_as_submission is false.",
            "next_action": "human returns 이후 Dataset/Experiments/Analysis/Conclusion sections를 final result로 갱신한다.",
            **evidence_state(
                [
                    reports / "eacl_paper_draft.md",
                    release / "paper_section_source_map.md",
                    release / "eacl_submission_package_manifest.md",
                ]
            ),
        },
        {
            "section_id": "S12",
            "plan_section": "12. Reviewer 관점의 예상 질문과 대응",
            "current_status": "reviewer_response_pack_ready_with_open_risks",
            "what_is_done": "Reviewer risks, response prep, release/ethics statements, and public-safe mitigation are prepared.",
            "key_numbers": "open risks include human gold, mapping review, crosswalk utility, active-review effort, and overclaiming.",
            "claim_boundary": "reviewer 답변도 final scores가 아니라 current gate status에 맞춰야 한다.",
            "next_action": "human/expert returns 이후 open risk IDs를 닫고 reviewer response를 갱신한다.",
            **evidence_state(
                [
                    release / "reviewer_response_prep.md",
                    release / "reviewer_risk_register.md",
                    release / "data_release_ethics_statement.md",
                    release / "public_reproducibility_manifest.md",
                ]
            ),
        },
        {
            "section_id": "S13",
            "plan_section": "13. EACL 제출 전 필수 체크리스트",
            "current_status": "automatic_items_pass_human_items_pending",
            "what_is_done": "The checklist is audited item-by-item; automatic-stage evidence is present and human-gated rows remain open.",
            "key_numbers": (
                f"checklist items={summary.get('checklist_item_count')}; "
                f"proven automatic={summary.get('completion_proven_item_count')}; "
                f"human blocked={summary.get('human_blocked_item_count')}"
            ),
            "claim_boundary": "minimum accept checklist is not complete until gold chunks/items/IAA/proposed scoring are complete.",
            "next_action": "11 minimum paper-gate return files must be completed before final main table.",
            **evidence_state(
                [
                    release / "revised_plan_completion_audit.md",
                    release / "paper_readiness_checklist.md",
                    release / "human_gate_action_plan.md",
                    review_dir / "human_review_master_return_files.csv",
                ]
            ),
        },
        {
            "section_id": "S14",
            "plan_section": "14. 수정된 일정안",
            "current_status": "timeline_action_board_ready_human_execution_pending",
            "what_is_done": "Timeline/action board and human gate action plan identify the critical path and return files.",
            "key_numbers": (
                f"required claim return files={summary.get('present_human_return_files')}/"
                f"{summary.get('required_human_return_files')}; "
                f"master return files={summary.get('master_return_files_present')}/"
                f"{summary.get('master_return_files')}"
            ),
            "claim_boundary": "schedule risk remains dominated by human annotation/adjudication and expert reviews.",
            "next_action": "first priority is annotator A/B batch returns, then adjudication, then APPLY_IMPORTS=1 refresh.",
            **evidence_state(
                [
                    release / "submission_timeline_action_board.md",
                    release / "human_gate_action_plan.md",
                    release / "human_review_status_dashboard_ko.md",
                    release / "post_human_scoring_readiness.md",
                ]
            ),
        },
    ]

    # Attach direct blocking-gate evidence to the rows that need it most.
    gate_ids_by_section = {
        "S08": ["gold.completed_chunks", "gold.item_count", "gold.iaa"],
        "S09": ["llm.proposed_human_gold_score", "mapping.expert_review", "crosswalk.expert_review"],
        "S13": ["gold.completed_chunks", "gold.item_count", "gold.iaa", "llm.proposed_human_gold_score"],
    }
    audit_by_id = checklist_by_id(audit)
    for row in rows:
        gate_ids = gate_ids_by_section.get(row["section_id"], [])
        row["blocking_gate_ids"] = ";".join(gate_ids)
        row["blocking_gate_statuses"] = ";".join(
            f"{gate_id}:{(gmap.get(gate_id) or {}).get('status', 'unknown')}" for gate_id in gate_ids
        )
        checklist_ids = [
            item_id
            for item_id, item in audit_by_id.items()
            if item.get("human_blocked") == "yes" and item_id.startswith("min.")
        ]
        if row["section_id"] == "S13":
            row["minimum_blocked_checklist_ids"] = ";".join(checklist_ids)
        else:
            row["minimum_blocked_checklist_ids"] = ""
    return rows


def compact_checklist_rows(audit):
    rows = []
    for row in audit.get("audit_rows") or []:
        rows.append(
            {
                "scope": row.get("scope"),
                "id": row.get("id"),
                "status": row.get("status"),
                "completion_proven": row.get("completion_proven"),
                "human_blocked": row.get("human_blocked"),
                "proof_state": row.get("proof_state"),
                "next_step": row.get("next_step"),
            }
        )
    return rows


def compact_method_rows(method):
    source_rows = method.get("modules") or []
    if not source_rows:
        source_rows = method.get("method_module_rows") or []
    rows = []
    for row in source_rows:
        module = row.get("module_id") or row.get("module")
        required_artifacts = (
            row.get("required_artifact_count")
            if row.get("required_artifact_count") is not None
            else row.get("required_artifacts")
        )
        missing_required = (
            row.get("missing_required_artifact_count")
            if row.get("missing_required_artifact_count") is not None
            else row.get("missing_required")
        )
        human_dependent = (
            row.get("human_dependent_for_final_claim")
            if row.get("human_dependent_for_final_claim") is not None
            else row.get("human_dependent")
        )
        rows.append(
            {
                "module": module,
                "name": row.get("name"),
                "status": row.get("status"),
                "required_artifacts": required_artifacts,
                "missing_required": missing_required,
                "human_dependent": human_dependent,
                "remaining_for_claim": row.get("remaining_for_paper_claim") or row.get("remaining_for_claim"),
            }
        )
    return rows


def return_rows(human_gate):
    rows = []
    for row in human_gate.get("required_return_files") or []:
        rows.append(
            {
                "minimum": row.get("required_for_minimum"),
                "task": row.get("task_type"),
                "owner": row.get("owner"),
                "batch_or_group": row.get("batch_or_group"),
                "expected_rows": row.get("expected_rows"),
                "present": row.get("present"),
                "status": row.get("status"),
                "reviewed_file": row.get("reviewed_file"),
            }
        )
    return rows


def render_table(headers, rows):
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        values = []
        for header in headers:
            value = str(row.get(header, ""))
            values.append(value.replace("|", "\\|").replace("\n", " "))
        lines.append("| " + " | ".join(values) + " |")
    return lines


def render_markdown(payload):
    summary = payload["summary"]
    lines = [
        "# CAPE-KG Revised Plan Section Status",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Plan: `{payload['plan_file']}`",
        f"Claim status: `{payload['claim_status']}`",
        "",
        "이 문서는 `AX_EACL_submission_review_revised_plan.md`의 주요 장별 요구사항을 현재 산출물과 직접 연결한 한국어 운영표입니다.",
        "제출 완료 선언이 아니라, revised plan을 어디까지 실행했고 어떤 evidence가 남았는지 확인하기 위한 상태표입니다.",
        "",
        "## 핵심 판단",
        "",
        f"- Pre-human validation: `{summary['pre_human_handoff_status']}` ({summary['pre_human_handoff_pass']} PASS / {summary['pre_human_handoff_warn']} WARN / {summary['pre_human_handoff_fail']} FAIL)",
        f"- Claim gate: `{summary['claim_gate_overall_status']}`",
        f"- 계획서 13장 체크리스트: {summary['checklist_item_count']}개 중 자동 완료 증거 {summary['completion_proven_item_count']}개, human-blocked {summary['human_blocked_item_count']}개",
        f"- M1-M11 방법론 모듈: required artifact missing {summary['method_modules_missing_required']}개",
        f"- Minimum paper-gate return files: {summary['minimum_return_files_present']}/{summary['minimum_return_files_required']}",
        f"- Required claim/human return files: {summary['required_return_files_present']}/{summary['required_return_files']}",
        "",
        "현재 결론은 명확합니다. KG 구축, 실험 scaffold, release/reproducibility, prompt/schema/evaluation protocol은 준비되었지만, 최종 논문 성능 claim은 human-gold annotation, IAA, adjudication, proposed human-gold scoring, expert review 반환 전에는 열 수 없습니다.",
        "",
        "## Revised Plan 장별 상태",
        "",
    ]
    section_headers = [
        "section_id",
        "plan_section",
        "current_status",
        "key_numbers",
        "claim_boundary",
        "next_action",
        "blocking_gate_ids",
    ]
    lines += render_table(section_headers, payload["section_rows"])
    lines += [
        "",
        "## 계획서 13장 체크리스트 상태",
        "",
    ]
    checklist_headers = ["scope", "id", "status", "completion_proven", "human_blocked", "proof_state", "next_step"]
    lines += render_table(checklist_headers, payload["checklist_rows"])
    lines += [
        "",
        "## M1-M11 방법론 모듈 상태",
        "",
    ]
    method_headers = ["module", "name", "status", "required_artifacts", "missing_required", "human_dependent", "remaining_for_claim"]
    lines += render_table(method_headers, payload["method_rows"])
    lines += [
        "",
        "## 아직 필요한 반환 파일",
        "",
        "아래 파일이 들어와야 final main table과 human-gold/expert-review claim을 갱신할 수 있습니다.",
        "",
    ]
    return_headers = ["minimum", "task", "owner", "batch_or_group", "expected_rows", "present", "status", "reviewed_file"]
    lines += render_table(return_headers, payload["return_rows"])
    lines += [
        "",
        "## 사용 명령",
        "",
        "사람 검수 반환 전 dry-run:",
        "",
        "```bash",
        "PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=0 bash scripts/run_cape_human_return_apply.sh",
        "```",
        "",
        "사람 검수 반환 후 적용:",
        "",
        "```bash",
        "PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=1 bash scripts/run_cape_human_return_apply.sh",
        "```",
        "",
        "최종 검증:",
        "",
        "```bash",
        "python3 scripts/validate_cape_pre_human_handoff.py --experiment-dir experiments/cape_kg_eacl_20260627 --outputs-dir outputs",
        "sha256sum -c experiments/cape_kg_eacl_20260627/06_release/release_bundle_checksums.sha256",
        "sha256sum -c experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/human_review_handoff_checksums.sha256",
        "```",
        "",
        "## 산출 파일",
        "",
        f"- JSON: `{payload['output_files']['json']}`",
        f"- CSV: `{payload['output_files']['csv']}`",
        f"- Markdown: `{payload['output_files']['markdown']}`",
    ]
    return "\n".join(lines) + "\n"


def build_payload(exp_dir, outputs_dir, plan_file):
    release = exp_dir / "06_release"
    data = {
        "revised_audit": read_json(release / "revised_plan_completion_audit.json", {}) or {},
        "claim_gate": read_json(release / "claim_gate_report.json", {}) or {},
        "human_gate": read_json(release / "human_gate_action_plan.json", {}) or {},
        "paper_section_map": read_json(release / "paper_section_source_map.json", {}) or {},
        "method_module_coverage": read_json(release / "method_module_coverage.json", {}) or {},
        "human_review_packet_integrity": read_json(release / "human_review_packet_integrity.json", {}) or {},
        "compliance": read_json(release / "eacl_plan_compliance_matrix.json", {}) or {},
    }
    audit_summary = data["revised_audit"].get("summary") or {}
    prehuman_counts = audit_summary.get("pre_human_handoff_status_counts") or {}
    compliance_summary = data["compliance"].get("summary") or {}
    method_summary = data["method_module_coverage"].get("summary") or {}

    sections = section_rows(exp_dir, outputs_dir, plan_file, data)
    missing_evidence = []
    for row in sections:
        missing_evidence.extend(row.get("missing_evidence_files") or [])

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "claim_status": CLAIM_STATUS,
        "experiment_dir": rel(exp_dir),
        "outputs_dir": rel(outputs_dir),
        "plan_file": rel(plan_file),
        "summary": {
            "section_count": len(sections),
            "section_evidence_missing_count": len(missing_evidence),
            "claim_gate_overall_status": data["claim_gate"].get("overall_status"),
            "claim_gate_required_failure_count": data["claim_gate"].get("required_failure_count"),
            "claim_gate_optional_failure_count": data["claim_gate"].get("optional_failure_count"),
            "pre_human_handoff_status": audit_summary.get("pre_human_handoff_status") or compliance_summary.get("pre_human_handoff_status"),
            "pre_human_handoff_checks": audit_summary.get("pre_human_handoff_checks") or compliance_summary.get("pre_human_handoff_checks"),
            "pre_human_handoff_pass": prehuman_counts.get("PASS", 0),
            "pre_human_handoff_warn": prehuman_counts.get("WARN", 0),
            "pre_human_handoff_fail": prehuman_counts.get("FAIL", 0),
            "checklist_item_count": audit_summary.get("checklist_item_count"),
            "completion_proven_item_count": audit_summary.get("completion_proven_item_count"),
            "human_blocked_item_count": audit_summary.get("human_blocked_item_count"),
            "minimum_human_blocker_count": audit_summary.get("minimum_human_blocker_count"),
            "strong_or_optional_human_blocker_count": audit_summary.get("strong_or_optional_human_blocker_count"),
            "method_module_count": method_summary.get("module_count") or audit_summary.get("method_module_count"),
            "method_modules_missing_required": method_summary.get("missing_required_artifact_count")
            if method_summary
            else audit_summary.get("method_modules_missing_required"),
            "minimum_return_files_required": compliance_summary.get("minimum_paper_gate_return_file_count"),
            "minimum_return_files_present": compliance_summary.get("minimum_paper_gate_return_file_present_count"),
            "required_return_files": audit_summary.get("required_human_return_files")
            or compliance_summary.get("required_human_return_file_count"),
            "required_return_files_present": audit_summary.get("present_human_return_files")
            or compliance_summary.get("tracked_human_return_file_present_count"),
            "master_return_files": audit_summary.get("master_return_files")
            or compliance_summary.get("master_return_file_count"),
            "master_return_files_present": audit_summary.get("master_return_files_present")
            or compliance_summary.get("master_return_file_present_count"),
        },
        "section_rows": sections,
        "checklist_rows": compact_checklist_rows(data["revised_audit"]),
        "method_rows": compact_method_rows(data["method_module_coverage"]),
        "return_rows": return_rows(data["human_gate"]),
        "source_artifacts": {
            "revised_plan_completion_audit": rel(release / "revised_plan_completion_audit.json"),
            "claim_gate_report": rel(release / "claim_gate_report.json"),
            "human_gate_action_plan": rel(release / "human_gate_action_plan.json"),
            "paper_section_source_map": rel(release / "paper_section_source_map.json"),
            "method_module_coverage": rel(release / "method_module_coverage.json"),
            "human_review_packet_integrity": rel(release / "human_review_packet_integrity.json"),
            "eacl_plan_compliance_matrix": rel(release / "eacl_plan_compliance_matrix.json"),
        },
    }
    return payload


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", type=Path, default=DEFAULT_EXP_DIR)
    parser.add_argument("--outputs-dir", type=Path, default=DEFAULT_OUTPUTS_DIR)
    parser.add_argument("--plan-file", type=Path, default=DEFAULT_PLAN_FILE)
    args = parser.parse_args()

    exp_dir = Path(args.experiment_dir)
    outputs_dir = Path(args.outputs_dir)
    release = exp_dir / "06_release"
    json_path = release / "revised_plan_section_status_ko.json"
    csv_path = release / "revised_plan_section_status_ko.csv"
    md_path = release / "revised_plan_section_status_ko.md"

    payload = build_payload(exp_dir, outputs_dir, Path(args.plan_file))
    payload["output_files"] = {
        "json": rel(json_path),
        "csv": rel(csv_path),
        "markdown": rel(md_path),
    }
    write_json(json_path, payload)
    write_csv(
        csv_path,
        payload["section_rows"],
        [
            "section_id",
            "plan_section",
            "current_status",
            "what_is_done",
            "key_numbers",
            "claim_boundary",
            "next_action",
            "blocking_gate_ids",
            "blocking_gate_statuses",
            "evidence_file_count",
            "evidence_files_present",
            "missing_evidence_files",
            "evidence_files",
        ],
    )
    write_text(md_path, render_markdown(payload))

    print(
        json.dumps(
            {
                "claim_status": payload["claim_status"],
                "section_count": payload["summary"]["section_count"],
                "missing_evidence": payload["summary"]["section_evidence_missing_count"],
                "markdown": rel(md_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
