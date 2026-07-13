#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a Korean completion audit for the revised CAPE-KG EACL plan."""

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from cape_pre_human_status import effective_prehuman_summary


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_PLAN_FILE = Path("AX_EACL_submission_review_revised_plan.md")
DEFAULT_OUTPUTS_DIR = Path("outputs")


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


def fmt(value):
    if value is True:
        return "yes"
    if value is False:
        return "no"
    if value is None:
        return "-"
    return str(value)


def md_table(headers, rows):
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(header, "")) for header in headers) + " |")
    return "\n".join(lines)


def file_state(path):
    path = Path(path)
    return {"path": str(path), "exists": path.exists(), "bytes": path.stat().st_size if path.exists() else 0}


def truthy(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"yes", "true", "1", "present"}
    return bool(value)


def master_return_counts(master_rows):
    optional_rows = [row for row in master_rows if not truthy(row.get("required_for_minimum", True))]
    optional_structural = [row for row in optional_rows if row.get("requiredness") == "optional_structural"]
    optional_claim = [row for row in optional_rows if row.get("requiredness") != "optional_structural"]
    required_claim = [row for row in master_rows if row.get("requiredness", "required") == "required"]
    return {
        "master_optional_claim_return_files": len(optional_claim),
        "master_optional_claim_return_files_present": sum(1 for row in optional_claim if truthy(row.get("present"))),
        "optional_structural_return_files": len(optional_structural),
        "optional_structural_return_files_present": sum(1 for row in optional_structural if truthy(row.get("present"))),
        "master_required_claim_return_files": len(required_claim),
        "master_required_claim_return_files_present": sum(1 for row in required_claim if truthy(row.get("present"))),
        "master_return_files": len(master_rows),
        "master_return_files_present": sum(1 for row in master_rows if truthy(row.get("present"))),
    }


def item_rows(items):
    rows = []
    for item in items:
        rows.append(
            {
                "id": item.get("id"),
                "category": item.get("category"),
                "status": item.get("status"),
                "claimable": "yes" if item.get("claimable") else "no",
                "requirement": item.get("requirement"),
                "next_step": item.get("next_step"),
            }
        )
    return rows


def gate_rows(gates):
    rows = []
    for gate in gates:
        rows.append(
            {
                "gate": gate.get("gate_id") or gate.get("id") or gate.get("gate"),
                "status": gate.get("status"),
                "requirement": gate.get("requirement"),
                "evidence": gate.get("evidence"),
            }
        )
    return rows


def render_paper_readiness_checklist(readiness, generated_at, plan_file, exp_dir):
    def normalize_rows(checklist):
        rows = []
        passed = 0
        failed = 0
        for raw_item in checklist:
            if len(raw_item) < 3:
                continue
            requirement, status, evidence = raw_item[0], bool(raw_item[1]), raw_item[2]
            if status:
                passed += 1
            else:
                failed += 1
            rows.append(
                {
                    "requirement": requirement,
                    "status": "PASS" if status else "PENDING",
                    "evidence": evidence,
                }
            )
        return rows, passed, failed

    minimum_rows, minimum_passed, minimum_failed = normalize_rows(readiness.get("minimum_accept_checklist") or [])
    strong_rows, strong_passed, strong_failed = normalize_rows(readiness.get("strong_accept_checklist") or [])
    total_rows = minimum_rows + strong_rows
    passed = minimum_passed + strong_passed
    failed = minimum_failed + strong_failed

    lines = [
        "# CAPE-KG Paper Readiness Checklist",
        "",
        f"Generated: {generated_at}",
        f"Plan: `{plan_file}`",
        f"Experiment: `{exp_dir}`",
        "",
        "이 문서는 `paper_readiness_checklist.json`을 사람이 검토하기 쉬운 Markdown 표로 렌더링한 것입니다.",
        "PASS는 자동 산출물이 존재하거나 실행이 끝났다는 뜻이며, PENDING은 human-gold 또는 human review 완료 전에는 논문 claim으로 사용할 수 없다는 뜻입니다.",
        "",
        "## Summary",
        "",
        f"- Items: {len(total_rows)}",
        f"- PASS: {passed}",
        f"- PENDING: {failed}",
        f"- Minimum-accept items: {len(minimum_rows)} / pending {minimum_failed}",
        f"- Strong-accept items: {len(strong_rows)} / pending {strong_failed}",
        "",
        "## Minimum-Accept Checklist",
        "",
        md_table(["requirement", "status", "evidence"], minimum_rows),
        "",
        "## Strong-Accept Checklist",
        "",
        md_table(["requirement", "status", "evidence"], strong_rows) if strong_rows else "No strong-accept checklist was found.",
        "",
        "## Interpretation",
        "",
        "- `B0/B1/B2 baseline`, `ablation`, `error analysis`, `public benchmark`, `release plan`, `limitations`는 자동 산출물 기준으로 준비되었습니다.",
        "- `gold annotation`, `gold item count`, `IAA`, `CAPE-KG proposed human-gold evaluation`은 사람 검수와 adjudication 이후에만 완료로 바뀝니다.",
        "- strong-accept 항목의 `1,500+ gold edge/evidence item`, mapping downstream, active-review efficiency 역시 사람 검수 전에는 논문 claim으로 사용할 수 없습니다.",
        "- 이 체크리스트는 제출 가능성 감사용이며, silver/proxy diagnostic을 human-gold 성능으로 대체하지 않습니다.",
        "",
    ]
    return "\n".join(lines)


def build_payload(exp_dir, plan_file, outputs_dir):
    exp_dir = Path(exp_dir)
    outputs_dir = Path(outputs_dir)
    release_dir = exp_dir / "06_release"
    review_dir = exp_dir / "05_review"
    gold_dir = exp_dir / "01_data/gold_annotation"

    audit = read_json(release_dir / "submission_readiness_audit.json", {}) or {}
    claim_gate = read_json(release_dir / "claim_gate_report.json", {}) or {}
    preflight = read_json(release_dir / "human_review_return_preflight.json", {}) or {}
    validation = read_json(release_dir / "pre_human_handoff_validation.json", {}) or {}
    validation_summary = effective_prehuman_summary(validation)
    coverage = read_json(release_dir / "method_module_coverage.json", {}) or {}
    expansion = read_json(gold_dir / "annotation_expansion_manifest.json", {}) or {}
    gold_sampling = read_json(release_dir / "gold_sampling_coverage_report.json", {}) or {}
    human_gold = read_json(exp_dir / "04_evaluation/human_gold_validation_summary.json", {}) or {}
    mapping_progress = read_json(release_dir / "mapping_review_progress_summary.json", {}) or {}
    master_returns = read_csv(review_dir / "human_review_master_return_files.csv")
    sampling_policy = gold_sampling.get("selection_policy") or {}
    sampling_coverage = gold_sampling.get("coverage_summary") or {}

    annotation_returns = preflight.get("annotation_returns") or {}
    adjudication_return = preflight.get("adjudication_return") or {}
    mapping_return = preflight.get("mapping_return") or {}
    crosswalk_return = preflight.get("crosswalk_return") or {}
    active_return = preflight.get("active_review_effort_return") or {}
    minimum_human_return_files = int(annotation_returns.get("expected_files") or 0) + int(bool(adjudication_return))
    minimum_human_return_files_present = int(annotation_returns.get("present_files") or 0) + int(bool(adjudication_return.get("present")))
    optional_strong_return_files = int(bool(mapping_return)) + int(bool(crosswalk_return)) + int(bool(active_return))
    optional_strong_return_files_present = (
        int(bool(mapping_return.get("present")))
        + int(bool(crosswalk_return.get("present")))
        + int(bool(active_return.get("present")))
    )
    tracked_human_return_files = minimum_human_return_files + optional_strong_return_files
    tracked_human_return_files_present = minimum_human_return_files_present + optional_strong_return_files_present
    master_counts = master_return_counts(master_returns)

    minimum_items = [item for item in audit.get("items", []) if item.get("category") == "minimum_accept"]
    strong_items = [item for item in audit.get("items", []) if item.get("category") == "strong_accept"]
    method_items = [item for item in audit.get("items", []) if item.get("category") == "method_modules"]

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "plan_file": str(plan_file),
        "experiment_dir": str(exp_dir),
        "outputs_dir": str(outputs_dir),
        "overall_completion_status": "not_complete_pending_human_gold_iaa_adjudication_and_expert_review",
        "completion_decision": {
            "goal_complete": False,
            "reason": "계획서의 최소 제출 요건 중 human-gold, IAA, adjudication, proposed human-gold scoring이 아직 완료되지 않았습니다.",
        },
        "summary": {
            "submission_claim_status": audit.get("claim_status"),
            "claim_gate_overall_status": claim_gate.get("overall_status"),
            "claim_gate_required_failure_count": claim_gate.get("required_failure_count"),
            "claim_gate_optional_failure_count": claim_gate.get("optional_failure_count"),
            "pre_human_validation_status": validation_summary.get("overall_status"),
            "pre_human_validation_checks": validation_summary.get("check_count"),
            "pre_human_validation_status_counts": validation_summary.get("status_counts"),
            "method_module_claim_status": (coverage.get("summary") or {}).get("claim_status"),
            "missing_method_artifacts": (coverage.get("summary") or {}).get("missing_required_artifact_count"),
            "minimum_paper_gate_return_files": minimum_human_return_files,
            "minimum_paper_gate_return_files_present": minimum_human_return_files_present,
            "minimum_paper_gate_return_files_missing": minimum_human_return_files - minimum_human_return_files_present,
            "optional_strong_return_files": optional_strong_return_files,
            "optional_strong_return_files_present": optional_strong_return_files_present,
            "optional_strong_return_files_missing": optional_strong_return_files - optional_strong_return_files_present,
            "tracked_human_return_files": tracked_human_return_files,
            "tracked_human_return_files_present": tracked_human_return_files_present,
            "tracked_human_return_files_missing": tracked_human_return_files - tracked_human_return_files_present,
            "required_human_return_files": tracked_human_return_files,
            "present_human_return_files": tracked_human_return_files_present,
            **master_counts,
            "optional_structural_return_files_missing": master_counts["optional_structural_return_files"]
            - master_counts["optional_structural_return_files_present"],
            "master_return_files_missing": master_counts["master_return_files"] - master_counts["master_return_files_present"],
            "adjudicated_chunks": human_gold.get("completed_adjudicated_chunks"),
            "gold_item_count": human_gold.get("gold_item_count_for_readiness"),
            "mapping_completed_rows": mapping_progress.get("completed_rows"),
            "mapping_pending_rows": mapping_progress.get("pending_rows"),
            "optional_all_available_chunks": expansion.get("all_available_chunk_count"),
            "optional_remaining_chunks": expansion.get("remaining_optional_chunk_count"),
            "strong_300_chunk_gap": expansion.get("strong_300_chunk_gap"),
            "strong_resegmented_package": expansion.get("strong_resegmented_package"),
            "strong_resegmented_chunks": expansion.get("strong_resegmented_chunk_count"),
            "strong_resegmented_max_sentences": expansion.get("strong_resegmented_max_sentences"),
            "strong_300_chunk_gap_after_resegmentation": expansion.get("strong_300_chunk_gap_after_resegmentation"),
            "strong_resegmented_claim_status": expansion.get("strong_resegmented_claim_status"),
            "priority_100_selected_chunks": sampling_policy.get("selected_chunk_count"),
            "priority_100_candidate_edge_coverage": sampling_coverage.get("priority_100_candidate_edge_coverage_of_full120"),
            "priority_100_active_review_chunk_coverage": sampling_coverage.get("priority_100_active_review_chunk_coverage_of_full120"),
            "priority_100_high_impact_chunk_coverage": sampling_coverage.get("priority_100_high_impact_chunk_coverage_of_full120"),
            "priority_100_candidate_edges": sampling_coverage.get("priority_100_candidate_edges"),
            "full_120_candidate_edges": sampling_coverage.get("full_120_candidate_edges"),
            "gold_sampling_claim_status": gold_sampling.get("claim_status"),
        },
        "minimum_accept_items": item_rows(minimum_items),
        "strong_accept_items": item_rows(strong_items),
        "method_items": item_rows(method_items),
        "claim_gates": gate_rows(claim_gate.get("gates", [])),
        "blocking_items": item_rows(audit.get("blocking_items", [])),
        "human_return_status": {
            "annotation_expected_files": annotation_returns.get("expected_files"),
            "annotation_present_files": annotation_returns.get("present_files"),
            "annotation_valid_files": annotation_returns.get("valid_files"),
            "adjudication_present": adjudication_return.get("present"),
            "mapping_present": mapping_return.get("present"),
            "mapping_expected_priority_groups": mapping_return.get("expected_priority_groups"),
            "crosswalk_present": crosswalk_return.get("present"),
            "crosswalk_expected_source_tasks": crosswalk_return.get("expected_source_tasks"),
            "crosswalk_expected_rows": crosswalk_return.get("expected_rows"),
            "active_review_effort_present": active_return.get("present"),
            "active_review_effort_expected_rows": active_return.get("expected_rows"),
            "optional_structural_return_files": master_counts["optional_structural_return_files"],
            "optional_structural_return_files_present": master_counts["optional_structural_return_files_present"],
            "master_return_files": master_counts["master_return_files"],
            "master_return_files_present": master_counts["master_return_files_present"],
        },
        "evidence_files": {
            "submission_readiness_audit": file_state(release_dir / "submission_readiness_audit.md"),
            "arr_submission_policy_checklist": file_state(release_dir / "arr_submission_policy_checklist.md"),
            "arr_submission_policy_checklist_json": file_state(release_dir / "arr_submission_policy_checklist.json"),
            "anonymized_submission_prep": file_state(release_dir / "anonymized_submission_prep.md"),
            "anonymized_submission_prep_json": file_state(release_dir / "anonymized_submission_prep.json"),
            "anonymized_submission_risk_scan": file_state(release_dir / "anonymized_submission_risk_scan.csv"),
            "paper_readiness_checklist_json": file_state(release_dir / "paper_readiness_checklist.json"),
            "paper_readiness_checklist_md": file_state(release_dir / "paper_readiness_checklist.md"),
            "claim_gate_report": file_state(release_dir / "claim_gate_report.md"),
            "human_gate_action_plan": file_state(release_dir / "human_gate_action_plan.md"),
            "annotation_batch_review_preview": file_state(release_dir / "annotation_batch_review_preview_summary.md"),
            "annotation_batch_review_preview_json": file_state(release_dir / "annotation_batch_review_preview_summary.json"),
            "gold_sampling_coverage_report": file_state(release_dir / "gold_sampling_coverage_report.md"),
            "gold_sampling_coverage_report_json": file_state(release_dir / "gold_sampling_coverage_report.json"),
            "gold_sampling_coverage_by_chapter": file_state(review_dir / "gold_sampling_coverage_by_chapter.csv"),
            "gold_sampling_priority100_selected_chunks": file_state(review_dir / "gold_sampling_priority100_selected_chunks.csv"),
            "strong_resegmented_review_preview": file_state(release_dir / "strong_resegmented_review_preview_summary.md"),
            "strong_resegmented_review_preview_json": file_state(release_dir / "strong_resegmented_review_preview_summary.json"),
            "human_review_master_checklist": file_state(release_dir / "human_review_master_checklist_ko.md"),
            "human_review_first_batch_execution_card": file_state(review_dir / "human_review_first_batch_execution_card_ko.md"),
            "human_review_first_batch_execution_card_json": file_state(review_dir / "human_review_first_batch_execution_card.json"),
            "human_review_role_quickstart": file_state(review_dir / "human_review_role_quickstart_cards_ko.md"),
            "human_review_role_quickstart_json": file_state(review_dir / "human_review_role_quickstart_cards.json"),
            "human_review_role_quickstart_csv": file_state(review_dir / "human_review_role_quickstart_cards.csv"),
            "human_review_status_dashboard": file_state(release_dir / "human_review_status_dashboard_ko.md"),
            "human_review_status_dashboard_json": file_state(release_dir / "human_review_status_dashboard_ko.json"),
            "human_review_launch_checklist": file_state(release_dir / "human_review_launch_checklist_ko.md"),
            "human_review_launch_checklist_json": file_state(release_dir / "human_review_launch_checklist_ko.json"),
            "human_review_packet_integrity": file_state(release_dir / "human_review_packet_integrity.md"),
            "human_review_packet_integrity_json": file_state(release_dir / "human_review_packet_integrity.json"),
            "human_review_packet_integrity_issues": file_state(review_dir / "human_review_packet_integrity_issues.csv"),
            "human_review_status_next_actions": file_state(review_dir / "human_review_status_next_actions.csv"),
            "human_review_master_return_files": file_state(review_dir / "human_review_master_return_files.csv"),
            "human_review_minimum_gate_launch_tasks": file_state(review_dir / "human_review_minimum_gate_launch_tasks.csv"),
            "active_review_human_effort_briefing": file_state(release_dir / "active_review_human_effort_briefing.md"),
            "active_review_human_effort_briefing_json": file_state(release_dir / "active_review_human_effort_briefing.json"),
            "active_review_human_effort_briefing_csv": file_state(review_dir / "active_review_human_effort_briefing.csv"),
            "mapping_review_group_briefing": file_state(release_dir / "mapping_review_group_briefing.md"),
            "mapping_review_group_briefing_json": file_state(release_dir / "mapping_review_group_briefing.json"),
            "mapping_review_group_briefing_csv": file_state(review_dir / "mapping_review_group_briefing_top20.csv"),
            "human_review_return_preflight": file_state(release_dir / "human_review_return_preflight.md"),
            "strong_review_return_preflight": file_state(release_dir / "strong_review_return_preflight.md"),
            "strong_return_apply_last_run": file_state(release_dir / "strong_return_apply_last_run.md"),
            "strong_return_apply_last_run_json": file_state(release_dir / "strong_return_apply_last_run.json"),
            "strong_return_apply_refusal_last_run": file_state(release_dir / "strong_return_apply_refusal_last_run.md"),
            "strong_return_apply_refusal_last_run_json": file_state(release_dir / "strong_return_apply_refusal_last_run.json"),
            "pre_human_validation": file_state(release_dir / "pre_human_handoff_validation.md"),
            "provenance_manifest": file_state(release_dir / "provenance_manifest.md"),
            "provenance_prov_o": file_state(release_dir / "provenance_prov_o.ttl"),
            "provenance_prov_o_report": file_state(release_dir / "provenance_prov_o_report.md"),
            "provenance_llm_run_index": file_state(exp_dir / "04_evaluation/provenance_llm_run_index.csv"),
            "public_reproducibility_manifest": file_state(release_dir / "public_reproducibility_manifest.md"),
            "public_reproducibility_manifest_json": file_state(release_dir / "public_reproducibility_manifest.json"),
            "public_reproducibility_manifest_csv": file_state(release_dir / "public_reproducibility_manifest.csv"),
            "responsible_nlp_checklist_prep": file_state(release_dir / "responsible_nlp_checklist_prep.md"),
            "responsible_nlp_checklist_prep_json": file_state(release_dir / "responsible_nlp_checklist_prep.json"),
            "responsible_nlp_checklist_items_csv": file_state(release_dir / "responsible_nlp_checklist_items.csv"),
            "experiment_reproduction_card": file_state(release_dir / "experiment_reproduction_card.md"),
            "experiment_reproduction_card_json": file_state(release_dir / "experiment_reproduction_card.json"),
            "experiment_reproduction_conditions_csv": file_state(release_dir / "experiment_reproduction_conditions.csv"),
            "claim_language_guardrails": file_state(release_dir / "claim_language_guardrails.md"),
            "claim_language_guardrails_json": file_state(release_dir / "claim_language_guardrails.json"),
            "reviewer_response_prep": file_state(release_dir / "reviewer_response_prep.md"),
            "reviewer_response_prep_json": file_state(release_dir / "reviewer_response_prep.json"),
            "submission_timeline_action_board": file_state(release_dir / "submission_timeline_action_board.md"),
            "submission_timeline_action_board_json": file_state(release_dir / "submission_timeline_action_board.json"),
            "claimable_main_table": file_state(release_dir / "claimable_main_table.md"),
            "reviewer_risk_register": file_state(release_dir / "reviewer_risk_register.md"),
            "reviewer_risk_register_json": file_state(release_dir / "reviewer_risk_register.json"),
            "method_novelty_positioning": file_state(release_dir / "method_novelty_positioning.md"),
            "method_novelty_positioning_json": file_state(release_dir / "method_novelty_positioning.json"),
            "qwen3_model_scaling_report": file_state(release_dir / "qwen3_model_scaling_report.md"),
            "qwen3_model_scaling_report_json": file_state(release_dir / "qwen3_model_scaling_report.json"),
            "paper_tables": file_state(release_dir / "paper_tables.md"),
            "paper_table_blueprint": file_state(release_dir / "paper_table_blueprint.md"),
            "paper_table_blueprint_json": file_state(release_dir / "paper_table_blueprint.json"),
            "paper_section_source_map": file_state(release_dir / "paper_section_source_map.md"),
            "paper_section_source_map_json": file_state(release_dir / "paper_section_source_map.json"),
            "eacl_submission_package_manifest": file_state(release_dir / "eacl_submission_package_manifest.md"),
            "eacl_submission_package_manifest_json": file_state(release_dir / "eacl_submission_package_manifest.json"),
            "post_human_scoring_readiness": file_state(release_dir / "post_human_scoring_readiness.md"),
            "post_human_scoring_readiness_json": file_state(release_dir / "post_human_scoring_readiness.json"),
            "eacl_paper_draft": file_state(exp_dir / "07_reports/eacl_paper_draft.md"),
            "current_reports_index": file_state(exp_dir / "07_reports/README_current_reports_ko.md"),
            "structural_evaluation": file_state(exp_dir / "04_evaluation/structural_evaluation_report.md"),
            "rdf_shacl_export": file_state(outputs_dir / "12_rdf/cape_kg_layer2.ttl"),
            "rdf_shacl_validation": file_state(outputs_dir / "12_rdf/cape_kg_shacl_validation_report.md"),
            "structural_gap_worklist": file_state(exp_dir / "04_evaluation/structural_gap_worklist_report.md"),
            "structural_review_action_plan": file_state(release_dir / "structural_review_action_plan.md"),
            "structural_review_optional_returns": file_state(review_dir / "structural_review_optional_returns.csv"),
            "structural_review_return_preflight": file_state(release_dir / "structural_review_return_preflight.md"),
            "structural_review_application_plan": file_state(release_dir / "structural_review_application_plan.md"),
            "structural_review_application_actions": file_state(review_dir / "structural_review_application_actions.csv"),
            "professor_presentation": file_state(exp_dir / "07_reports/professor_presentation_revised_current_20260628_ko.md"),
            "professor_slide_contents_current": file_state(exp_dir / "07_reports/professor_report_slide_contents_current_20260628_ko.md"),
            "professor_core_essentials_prompt_cq_node_edge_separate": file_state(
                exp_dir / "07_reports/professor_report_core_essentials_prompt_cq_node_edge_separate_20260629_ko.md"
            ),
            "professor_core_essentials_separate_from_slides": file_state(
                exp_dir / "07_reports/professor_report_core_essentials_separate_from_slides_20260629_ko.md"
            ),
            "professor_core_summary_separate_from_slides_sync4": file_state(
                exp_dir / "07_reports/professor_report_core_summary_separate_from_slides_sync4_20260629_ko.md"
            ),
            "professor_key_summary_separate_from_slides": file_state(
                exp_dir / "07_reports/professor_report_key_summary_separate_from_slides_20260629_ko.md"
            ),
            "professor_core_contents_separate": file_state(
                exp_dir / "07_reports/professor_report_core_contents_separate_20260629_ko.md"
            ),
            "professor_key_content_only_prompt_cq_node_edge": file_state(
                exp_dir / "07_reports/professor_report_key_content_only_prompt_cq_node_edge_20260629_ko.md"
            ),
            "professor_core_methodology_prompt_node_edge_summary": file_state(
                exp_dir / "07_reports/professor_report_core_methodology_prompt_node_edge_summary_20260629_ko.md"
            ),
            "professor_core_summary_current_20260629": file_state(
                exp_dir / "07_reports/professor_report_core_summary_current_20260629_ko.md"
            ),
            "professor_core_summary_current": file_state(exp_dir / "07_reports/professor_report_core_summary_current_20260628_ko.md"),
            "professor_core_briefing_prompt_cq_node_edge_current": file_state(exp_dir / "07_reports/professor_report_core_briefing_prompt_cq_node_edge_current_20260628_ko.md"),
            "prompt_node_edge_traceability": file_state(release_dir / "prompt_node_edge_traceability.md"),
            "prompt_node_edge_traceability_json": file_state(release_dir / "prompt_node_edge_traceability.json"),
            "evidence_graph_projection_report": file_state(outputs_dir / "13_evidence_graph/evidence_graph_projection_report.md"),
            "evidence_graph_projection_summary": file_state(outputs_dir / "13_evidence_graph/evidence_graph_projection_summary.json"),
            "neo4j_evidence_query_pack": file_state(release_dir / "neo4j_evidence_query_pack.md"),
            "neo4j_evidence_query_pack_json": file_state(release_dir / "neo4j_evidence_query_pack.json"),
            "neo4j_evidence_queries_cypher": file_state(outputs_dir / "11_neo4j_import_flat/neo4j_evidence_queries.cypher"),
            "annotation_expansion_report": file_state(gold_dir / "annotation_expansion_report.md"),
            "latest_release_bundle_index": file_state(release_dir / "latest_release_bundle_index.md"),
            "latest_release_bundle_index_json": file_state(release_dir / "latest_release_bundle_index.json"),
            "release_checksums": file_state(release_dir / "release_bundle_checksums.sha256"),
            "handoff_checksums": file_state(release_dir / "human_review_handoff/human_review_handoff_checksums.sha256"),
        },
        "next_commands": {
            "check_handoff_checksums": "sha256sum -c experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/human_review_handoff_checksums.sha256",
            "validate_return_files": "python3 scripts/validate_cape_human_review_returns.py --experiment-dir experiments/cape_kg_eacl_20260627",
            "validate_strong_return_files": "python3 scripts/validate_cape_strong_review_returns.py --experiment-dir experiments/cape_kg_eacl_20260627",
            "dry_run_strong_return_apply_wrapper": "PYTHON_BIN=python3 APPLY_IMPORTS=0 bash scripts/run_cape_strong_return_apply.sh",
            "apply_strong_returns_with_wrapper": "PYTHON_BIN=python3 APPLY_IMPORTS=1 bash scripts/run_cape_strong_return_apply.sh",
            "dry_run_human_return_apply_wrapper": "PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=0 bash scripts/run_cape_human_return_apply.sh",
            "apply_human_returns_with_wrapper": "PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=1 bash scripts/run_cape_human_return_apply.sh",
            "low_level_dry_run_refresh": "PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=0 bash scripts/run_cape_post_annotation_refresh.sh",
            "low_level_apply_refresh": "PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=1 bash scripts/run_cape_post_annotation_refresh.sh",
            "check_release_checksums": "sha256sum -c experiments/cape_kg_eacl_20260627/06_release/release_bundle_checksums.sha256",
        },
    }
    return payload


def render_report(payload):
    summary = payload["summary"]
    evidence = payload["evidence_files"]
    commands = payload["next_commands"]
    lines = [
        "# CAPE-KG EACL 제출 완료 감사표",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Plan: `{payload['plan_file']}`",
        f"Experiment: `{payload['experiment_dir']}`",
        "",
        "## 결론",
        "",
        "**현재 목표는 아직 완료가 아닙니다.** 자동 KG 구축, LLM 실행, baseline/ablation, release bundle, pre-human validation은 준비되었지만, 계획서의 최소 제출 요건 중 human-gold annotation, IAA, adjudication, proposed human-gold scoring이 남아 있습니다.",
        "",
        "| 항목 | 현재 값 |",
        "|---|---:|",
        f"| Submission claim status | `{summary.get('submission_claim_status')}` |",
        f"| Claim gate | `{summary.get('claim_gate_overall_status')}` |",
        f"| Required claim-gate failures | {summary.get('claim_gate_required_failure_count')} |",
        f"| Optional claim-gate failures | {summary.get('claim_gate_optional_failure_count')} |",
        f"| Pre-human validation | `{summary.get('pre_human_validation_status')}` |",
        f"| Pre-human checks | {summary.get('pre_human_validation_checks')} |",
        f"| Method missing artifacts | {summary.get('missing_method_artifacts')} |",
        f"| Minimum paper-gate return files | {summary.get('minimum_paper_gate_return_files_present')}/{summary.get('minimum_paper_gate_return_files')} |",
        f"| Optional/strong claim return files | {summary.get('optional_strong_return_files_present')}/{summary.get('optional_strong_return_files')} |",
        f"| Required claim/human return files | {summary.get('tracked_human_return_files_present')}/{summary.get('tracked_human_return_files')} |",
        f"| Optional structural review files | {summary.get('optional_structural_return_files_present')}/{summary.get('optional_structural_return_files')} |",
        f"| All master return files | {summary.get('master_return_files_present')}/{summary.get('master_return_files')} |",
        f"| Adjudicated chunks | {summary.get('adjudicated_chunks')} |",
        f"| Gold item count | {summary.get('gold_item_count')} |",
        f"| Mapping pending rows | {summary.get('mapping_pending_rows')} |",
        f"| Optional all-available chunks | {summary.get('optional_all_available_chunks')} |",
        f"| Optional remaining chunks | {summary.get('optional_remaining_chunks')} |",
        f"| Strong 300-chunk gap without resegmentation | {summary.get('strong_300_chunk_gap')} |",
        f"| Strong resegmented package | `{summary.get('strong_resegmented_package')}` |",
        f"| Strong resegmented chunks | {summary.get('strong_resegmented_chunks')} |",
        f"| Strong resegmented max sentences | {summary.get('strong_resegmented_max_sentences')} |",
        f"| Strong 300-chunk gap after resegmentation | {summary.get('strong_300_chunk_gap_after_resegmentation')} |",
        f"| Strong resegmented claim status | `{summary.get('strong_resegmented_claim_status')}` |",
        f"| Priority-100 selected chunks | {summary.get('priority_100_selected_chunks')} |",
        f"| Priority-100 candidate-edge coverage | {summary.get('priority_100_candidate_edge_coverage')} |",
        f"| Priority-100 active-review chunk coverage | {summary.get('priority_100_active_review_chunk_coverage')} |",
        f"| Priority-100 high-impact chunk coverage | {summary.get('priority_100_high_impact_chunk_coverage')} |",
        f"| Priority-100 candidate edges | {summary.get('priority_100_candidate_edges')}/{summary.get('full_120_candidate_edges')} |",
        f"| Gold sampling claim status | `{summary.get('gold_sampling_claim_status')}` |",
        "",
        "## Minimum-Accept 요구사항 상태",
        "",
        md_table(["id", "status", "claimable", "requirement", "next_step"], payload["minimum_accept_items"]),
        "",
        "## Strong-Accept 요구사항 상태",
        "",
        md_table(["id", "status", "claimable", "requirement", "next_step"], payload["strong_accept_items"]),
        "",
        "## 현재 Blocking Items",
        "",
        md_table(["id", "status", "claimable", "requirement", "next_step"], payload["blocking_items"]),
        "",
        "## Human Return 상태",
        "",
        "| 항목 | 값 |",
        "|---|---:|",
    ]
    for key, value in payload["human_return_status"].items():
        lines.append(f"| {key} | {fmt(value)} |")
    lines += [
        "",
        "## Optional Annotation Expansion 해석",
        "",
        "- 현재 minimum paper-gate는 기존 priority 100 chunk의 annotation/adjudication 반환 11개 파일 기준입니다.",
        "- mapping expert review, NCS-PCF crosswalk expert review, active-review effort 3개 파일은 optional/strong claim용이며, minimum 11개와 합쳐 required claim/human return 14개로 추적합니다.",
        "- structural review 2개 파일은 절차 구조 보강용 선택 검수이며, master manifest 전체에서는 16개 반환 파일로 함께 추적합니다.",
        "- `all_available_214`는 current corpus 전체를 검수하기 위한 선택 패키지입니다.",
        "- `remaining_94_text_only`는 기존 120개에 포함되지 않은 나머지 chunk입니다.",
        "- `priority_100`은 full-120 안에서 candidate edge, active-review, high-impact 항목을 우선 덮도록 선정한 최소 검수 subset입니다.",
        "- priority-100 sampling coverage는 subset 선정 근거일 뿐이며, gold result claim은 아닙니다.",
        f"- `{summary.get('strong_resegmented_package')}`는 같은 원본 corpus를 최대 {summary.get('strong_resegmented_max_sentences')}개 source sentence 단위로 재분할한 300+ 검수 후보 패키지입니다.",
        "- 이 재분할 패키지도 사람 검수 전 준비물입니다. 300+ adjudicated chunk claim은 두 annotator 검수와 adjudication이 완료된 뒤에만 가능합니다.",
        "",
        "## 증거 파일",
        "",
        "| 산출물 | 존재 | bytes | 경로 |",
        "|---|---:|---:|---|",
    ]
    for name, state in evidence.items():
        lines.append(f"| {name} | {fmt(state.get('exists'))} | {state.get('bytes')} | `{state.get('path')}` |")
    lines += [
        "",
        "## 다음 명령",
        "",
    ]
    for name, command in commands.items():
        lines += [f"### {name}", "", "```bash", command, "```", ""]
    lines += [
        "## 사용 시 주의",
        "",
        "- 이 문서는 완료 선언이 아니라 완료 여부 감사표입니다.",
        "- silver/proxy diagnostic은 human-gold 성능 증거로 취급하지 않습니다.",
        "- claim gate FAIL은 현재 expected state입니다. 실패 원인은 실험 오류가 아니라 human-gold 미완료입니다.",
        "",
    ]
    return "\n".join(lines)


def run(args):
    payload = build_payload(args.experiment_dir, args.plan_file, args.outputs_dir)
    release_dir = Path(args.experiment_dir) / "06_release"
    checklist_json_path = release_dir / "paper_readiness_checklist.json"
    checklist_md_path = release_dir / "paper_readiness_checklist.md"
    json_path = release_dir / "submission_completion_audit_ko.json"
    md_path = release_dir / "submission_completion_audit_ko.md"

    readiness = read_json(checklist_json_path, {}) or {}
    write_text(
        checklist_md_path,
        render_paper_readiness_checklist(
            readiness,
            payload["generated_at_utc"],
            args.plan_file,
            args.experiment_dir,
        ),
    )
    payload["evidence_files"]["paper_readiness_checklist_md"] = file_state(checklist_md_path)

    write_json(json_path, payload)
    write_text(md_path, render_report(payload))
    print(
        json.dumps(
            {
                "json": str(json_path),
                "markdown": str(md_path),
                "paper_readiness_checklist": str(checklist_md_path),
                "overall_completion_status": payload["overall_completion_status"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--plan-file", default=str(DEFAULT_PLAN_FILE))
    parser.add_argument("--outputs-dir", default=str(DEFAULT_OUTPUTS_DIR))
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
