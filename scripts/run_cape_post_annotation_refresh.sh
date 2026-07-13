#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON_BIN="${PYTHON_BIN:-python3}"
LLM_PYTHON="${LLM_PYTHON:-$PYTHON_BIN}"
EXP_DIR="${EXP_DIR:-experiments/cape_kg_eacl_20260627}"
PLAN_FILE="${PLAN_FILE:-AX_EACL_submission_review_revised_plan.md}"
OUTPUTS_DIR="${OUTPUTS_DIR:-outputs}"
STAMP="${STAMP:-$(date -u +%Y%m%dT%H%M%SZ)}"
APPLY_IMPORTS="${APPLY_IMPORTS:-0}"
STARTED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

GOLD_DIR="$EXP_DIR/01_data/gold_annotation/full_120"
PILOT_DIR="$EXP_DIR/01_data/gold_annotation/pilot_30"
BATCH_DIR="$EXP_DIR/05_review/human_gold_batches"
MAPPING_DIR="$EXP_DIR/01_data/mapping_review"
CROSSWALK_DIR="$EXP_DIR/01_data/crosswalk_review"
shopt -s nullglob

run_import_if_present() {
  local target_file="$1"
  local reviewed_file="$2"
  local report_file="$3"
  local extra_args=("${@:4}")
  if [[ ! -f "$reviewed_file" ]]; then
    echo "Skipping import; reviewed file not found: $reviewed_file"
    return 0
  fi
  local apply_args=()
  if [[ "$APPLY_IMPORTS" == "1" ]]; then
    apply_args+=(--apply)
  fi
  "$PYTHON_BIN" scripts/import_cape_gold_annotation.py \
    --experiment-dir "$EXP_DIR" \
    --target-file "$target_file" \
    --reviewed-file "$reviewed_file" \
    --report-file "$report_file" \
    "${extra_args[@]}" \
    "${apply_args[@]}"
}

run_mapping_import_if_present() {
  local reviewed_file="$1"
  local report_file="$2"
  if [[ ! -f "$reviewed_file" ]]; then
    echo "Skipping mapping import; reviewed file not found: $reviewed_file"
    return 0
  fi
  local apply_args=()
  if [[ "$APPLY_IMPORTS" == "1" ]]; then
    apply_args+=(--apply)
  fi
  "$PYTHON_BIN" scripts/import_cape_mapping_review.py \
    --experiment-dir "$EXP_DIR" \
    --target-file "$MAPPING_DIR/mapping_review_items.jsonl" \
    --reviewed-file "$reviewed_file" \
    --report-file "$report_file" \
    --allow-partial \
    "${apply_args[@]}"
}

run_crosswalk_import_if_present() {
  local reviewed_file="$1"
  local report_file="$2"
  if [[ ! -f "$reviewed_file" ]]; then
    echo "Skipping crosswalk import; reviewed file not found: $reviewed_file"
    return 0
  fi
  local apply_args=()
  if [[ "$APPLY_IMPORTS" == "1" ]]; then
    apply_args+=(--apply)
  fi
  "$PYTHON_BIN" scripts/import_cape_crosswalk_review.py \
    --experiment-dir "$EXP_DIR" \
    --target-file "$CROSSWALK_DIR/crosswalk_review_items.jsonl" \
    --reviewed-file "$reviewed_file" \
    --report-file "$report_file" \
    --allow-partial \
	    "${apply_args[@]}"
}

build_neo4j_exports() {
  "$PYTHON_BIN" scripts/export_kg_to_neo4j.py \
    --outputs-dir "$OUTPUTS_DIR" \
    --out-dir "$OUTPUTS_DIR/11_neo4j_import"
  "$PYTHON_BIN" scripts/export_kg_to_neo4j.py \
    --outputs-dir "$OUTPUTS_DIR" \
    --out-dir "$OUTPUTS_DIR/11_neo4j_import_flat" \
    --flat-relationships \
    --csv-base-url "http://localhost:8765/$OUTPUTS_DIR/11_neo4j_import_flat" \
    --http-cypher-name "neo4j_import_http_8765.cypher"
  "$PYTHON_BIN" scripts/export_kg_to_neo4j.py \
    --outputs-dir "$OUTPUTS_DIR" \
    --out-dir "$OUTPUTS_DIR/11_neo4j_import_flat" \
    --flat-relationships \
    --csv-base-url "http://127.0.0.1:8765/$OUTPUTS_DIR/11_neo4j_import_flat" \
    --http-cypher-name "neo4j_import_http_127001_8765.cypher"
  "$PYTHON_BIN" scripts/validate_neo4j_import_csv.py \
    --import-dir "$OUTPUTS_DIR/11_neo4j_import" \
    --output-json "$OUTPUTS_DIR/11_neo4j_import/neo4j_csv_validation_report.json" \
    --output-report "$OUTPUTS_DIR/11_neo4j_import/neo4j_csv_validation_report.md" \
    --fail-on-error
  "$PYTHON_BIN" scripts/validate_neo4j_import_csv.py \
    --import-dir "$OUTPUTS_DIR/11_neo4j_import_flat" \
    --output-json "$OUTPUTS_DIR/11_neo4j_import_flat/neo4j_csv_validation_report.json" \
    --output-report "$OUTPUTS_DIR/11_neo4j_import_flat/neo4j_csv_validation_report.md" \
    --fail-on-error
  "$PYTHON_BIN" scripts/build_cape_neo4j_evidence_query_pack.py \
    --experiment-dir "$EXP_DIR" \
    --outputs-dir "$OUTPUTS_DIR"
}

echo "Post-annotation refresh started."
echo "EXP_DIR=$EXP_DIR"
echo "APPLY_IMPORTS=$APPLY_IMPORTS"

"$PYTHON_BIN" -m py_compile \
  scripts/import_cape_gold_annotation.py \
  scripts/compute_cape_annotation_iaa.py \
  scripts/prepare_cape_adjudication_draft.py \
  scripts/build_cape_annotation_batch_review_preview.py \
  scripts/build_cape_annotation_return_field_guide.py \
  scripts/build_cape_human_return_error_playbook.py \
  scripts/build_cape_gold_sampling_coverage_report.py \
  scripts/build_cape_gold_item_feasibility_report.py \
  scripts/evaluate_cape_human_gold.py \
  scripts/evaluate_cape_human_gold_span_iou.py \
  scripts/build_cape_annotation_progress_report.py \
  scripts/build_cape_annotation_qc_report.py \
  scripts/build_cape_annotation_expansion_package.py \
  scripts/evaluate_cape_active_review_efficiency.py \
  scripts/build_cape_active_review_human_effort.py \
  scripts/run_cape_active_review_effort_roundtrip_smoke.py \
  scripts/build_cape_human_review_handoff.py \
  scripts/build_cape_human_gate_action_plan.py \
  scripts/build_cape_human_review_master_checklist.py \
  scripts/build_cape_human_review_first_batch_card.py \
  scripts/build_cape_human_review_role_quickstart.py \
  scripts/build_cape_human_review_status_dashboard.py \
  scripts/build_cape_human_review_launch_checklist.py \
  scripts/import_cape_mapping_review.py \
  scripts/import_cape_crosswalk_review.py \
  scripts/prepare_cape_crosswalk_review_package.py \
  scripts/evaluate_cape_crosswalk_review.py \
  scripts/validate_cape_human_review_returns.py \
  scripts/validate_cape_strong_review_returns.py \
  scripts/audit_cape_plan_requirements.py \
  scripts/validate_cape_experiment_readiness.py \
  scripts/build_cape_claimable_main_table.py \
  scripts/build_cape_cq_query_pack.py \
  scripts/build_cape_neo4j_evidence_query_pack.py \
  scripts/build_cape_ablation_coverage_report.py \
  scripts/build_cape_alias_canonicalization_report.py \
  scripts/build_cape_paper_tables.py \
  scripts/build_cape_paper_table_blueprint.py \
  scripts/build_cape_arr_submission_policy_checklist.py \
  scripts/build_cape_anonymized_submission_prep.py \
  scripts/build_cape_responsible_nlp_checklist_prep.py \
  scripts/build_cape_experiment_reproduction_card.py \
  scripts/build_cape_paper_section_source_map.py \
  scripts/build_cape_post_human_scoring_readiness.py \
  scripts/build_cape_claim_language_guardrails.py \
  scripts/build_cape_reviewer_response_prep.py \
  scripts/build_cape_submission_timeline_action_board.py \
  scripts/build_cape_eacl_submission_package_manifest.py \
  scripts/build_cape_eacl_plan_compliance_matrix.py \
  scripts/build_cape_revised_plan_completion_audit.py \
  scripts/build_cape_revised_plan_section_status.py \
  scripts/build_cape_evaluation_protocol_lock.py \
  scripts/build_cape_public_synthetic_examples.py \
  scripts/build_cape_public_reproducibility_manifest.py \
  scripts/build_cape_provenance_manifest.py \
  scripts/build_cape_prov_o_export.py \
  scripts/build_cape_component_evidence_spans.py \
  scripts/build_cape_predicate_cue_spans.py \
  scripts/build_cape_annotation_protocol_traceability.py \
  scripts/build_cape_metric_traceability_audit.py \
  scripts/build_cape_contribution_claim_traceability.py \
  scripts/build_cape_related_work_baseline_traceability.py \
  scripts/build_cape_evidence_graph_projection.py \
  scripts/build_cape_edge_component_span_traceability.py \
  scripts/build_cape_prompt_node_edge_traceability.py \
  scripts/build_cape_schema_retrieval_coverage_report.py \
  scripts/build_cape_alias_canonicalization_report.py \
  scripts/build_cape_rq_evidence_matrix.py \
  scripts/build_cape_reviewer_risk_register.py \
  scripts/build_cape_schema_plan_alignment_report.py \
  scripts/build_cape_ncs_pcf_crosswalk.py \
  scripts/build_cape_structural_evaluation.py \
  scripts/export_cape_kg_rdf_shacl.py \
  scripts/build_cape_structural_gap_worklist.py \
  scripts/build_cape_structural_review_action_plan.py \
  scripts/validate_cape_structural_review_returns.py \
  scripts/build_cape_structural_review_application_plan.py \
  scripts/build_cape_method_module_coverage.py \
  scripts/build_cape_method_novelty_positioning.py \
  scripts/build_cape_qwen3_model_scaling_report.py \
  scripts/build_cape_submission_completion_audit.py \
  scripts/build_cape_revised_plan_completion_audit.py \
  scripts/build_cape_revised_plan_section_status.py \
  scripts/build_cape_annotation_protocol_traceability.py \
  scripts/build_cape_metric_traceability_audit.py \
  scripts/build_cape_contribution_claim_traceability.py \
  scripts/build_cape_related_work_baseline_traceability.py \
  scripts/build_cape_eacl_paper_draft.py \
  scripts/build_cape_kg_eacl_experiment.py \
  scripts/run_cape_annotation_roundtrip_smoke.py \
  scripts/run_cape_mapping_roundtrip_smoke.py \
  scripts/run_cape_crosswalk_roundtrip_smoke.py \
  scripts/build_cape_release_bundle.py \
  scripts/validate_cape_pre_human_handoff.py

run_import_if_present \
  "$GOLD_DIR/annotator_A.jsonl" \
  "$GOLD_DIR/annotator_A_edited.jsonl" \
  "$GOLD_DIR/annotator_A_import_report.json"

run_import_if_present \
  "$GOLD_DIR/annotator_B.jsonl" \
  "$GOLD_DIR/annotator_B_edited.jsonl" \
  "$GOLD_DIR/annotator_B_import_report.json"

run_import_if_present \
  "$GOLD_DIR/adjudication.jsonl" \
  "$GOLD_DIR/adjudication_edited.jsonl" \
  "$GOLD_DIR/adjudication_import_report.json"

for reviewed_file in "$BATCH_DIR"/full_120_priority_batch_*/annotator_A_full_120_priority_batch_*.reviewed.jsonl; do
  run_import_if_present \
    "$GOLD_DIR/annotator_A.jsonl" \
    "$reviewed_file" \
    "${reviewed_file%.reviewed.jsonl}.import_report.json" \
    --allow-partial
done

for reviewed_file in "$BATCH_DIR"/full_120_priority_batch_*/annotator_B_full_120_priority_batch_*.reviewed.jsonl; do
  run_import_if_present \
    "$GOLD_DIR/annotator_B.jsonl" \
    "$reviewed_file" \
    "${reviewed_file%.reviewed.jsonl}.import_report.json" \
    --allow-partial
done

for reviewed_file in "$MAPPING_DIR"/mapping_review*.reviewed.jsonl; do
  run_mapping_import_if_present \
    "$reviewed_file" \
    "${reviewed_file%.reviewed.jsonl}.import_report.json"
done

for reviewed_file in "$CROSSWALK_DIR"/crosswalk_review*.reviewed.jsonl; do
  run_crosswalk_import_if_present \
    "$reviewed_file" \
    "${reviewed_file%.reviewed.jsonl}.import_report.json"
done

if [[ -f "$PILOT_DIR/annotator_A.jsonl" && -f "$PILOT_DIR/annotator_B.jsonl" ]]; then
  "$PYTHON_BIN" scripts/compute_cape_annotation_iaa.py \
    --annotator-a "$PILOT_DIR/annotator_A.jsonl" \
    --annotator-b "$PILOT_DIR/annotator_B.jsonl" \
    --output-dir "$EXP_DIR/01_data/gold_annotation/iaa_pilot_30"
fi

"$PYTHON_BIN" scripts/compute_cape_annotation_iaa.py \
  --annotator-a "$GOLD_DIR/annotator_A.jsonl" \
  --annotator-b "$GOLD_DIR/annotator_B.jsonl" \
  --output-dir "$EXP_DIR/01_data/gold_annotation/iaa_full_120"

"$PYTHON_BIN" scripts/prepare_cape_adjudication_draft.py \
  --experiment-dir "$EXP_DIR" \
  --package full_120

if [[ -d "$PILOT_DIR" ]]; then
  "$PYTHON_BIN" scripts/prepare_cape_adjudication_draft.py \
    --experiment-dir "$EXP_DIR" \
    --package pilot_30
fi

"$PYTHON_BIN" scripts/evaluate_cape_human_gold.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/evaluate_cape_human_gold_span_iou.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_annotation_progress_report.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_annotation_qc_report.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_annotation_expansion_package.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_annotation_batch_review_preview.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_gold_sampling_coverage_report.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_gold_item_feasibility_report.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/validate_cape_human_review_returns.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/validate_cape_strong_review_returns.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/evaluate_cape_active_review_efficiency.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_active_review_human_effort.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/run_cape_active_review_effort_roundtrip_smoke.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_gate_action_plan.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_annotation_return_field_guide.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_return_error_playbook.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_review_master_checklist.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_review_first_batch_card.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_review_role_quickstart.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_review_status_dashboard.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_review_launch_checklist.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_review_handoff.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/run_cape_annotation_roundtrip_smoke.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/evaluate_cape_mapping_review.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_mapping_review_progress_report.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/run_cape_mapping_roundtrip_smoke.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_component_evidence_spans.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_predicate_cue_spans.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_evidence_graph_projection.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_edge_component_span_traceability.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_ncs_pcf_crosswalk.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/prepare_cape_crosswalk_review_package.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/evaluate_cape_crosswalk_review.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/run_cape_crosswalk_roundtrip_smoke.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_structural_evaluation.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/export_cape_kg_rdf_shacl.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_structural_gap_worklist.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_structural_review_action_plan.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/validate_cape_structural_review_returns.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_structural_review_application_plan.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_annotation_calibration_pack.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_review_master_checklist.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_review_first_batch_card.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_review_role_quickstart.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_review_status_dashboard.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_review_launch_checklist.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_review_handoff.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_gate_action_plan.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_review_master_checklist.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_review_first_batch_card.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_review_role_quickstart.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_review_status_dashboard.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_review_launch_checklist.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_review_handoff.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_public_synthetic_examples.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_prompt_node_edge_traceability.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_schema_retrieval_coverage_report.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_alias_canonicalization_report.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_schema_plan_alignment_report.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_rq_evidence_matrix.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_gold_sampling_coverage_report.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_gold_item_feasibility_report.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_experiment_reproduction_card.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_provenance_manifest.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_prov_o_export.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_method_module_coverage.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_method_novelty_positioning.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_kg_eacl_experiment.py --kg-dir "$OUTPUTS_DIR" --experiment-dir "$EXP_DIR" --sample-size 120
"$PYTHON_BIN" scripts/build_cape_component_evidence_spans.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_predicate_cue_spans.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_evidence_graph_projection.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_edge_component_span_traceability.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_ncs_pcf_crosswalk.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/prepare_cape_crosswalk_review_package.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/evaluate_cape_crosswalk_review.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/run_cape_crosswalk_roundtrip_smoke.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/audit_cape_plan_requirements.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/validate_cape_experiment_readiness.py --experiment-dir "$EXP_DIR" --no-fail

if [[ -x "$LLM_PYTHON" ]]; then
  "$LLM_PYTHON" scripts/check_qwen3_32b_awq_readiness.py --experiment-dir "$EXP_DIR" || true
fi

"$PYTHON_BIN" scripts/build_cape_strict_json_diagnostics.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_qwen3_model_scaling_report.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_claimable_main_table.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_cq_query_pack.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_ablation_coverage_report.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_paper_tables.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_paper_table_blueprint.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_arr_submission_policy_checklist.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_anonymized_submission_prep.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_responsible_nlp_checklist_prep.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_experiment_reproduction_card.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_eacl_paper_draft.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_paper_section_source_map.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_post_human_scoring_readiness.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_claim_language_guardrails.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_reviewer_response_prep.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_submission_timeline_action_board.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_eacl_submission_package_manifest.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_eacl_plan_compliance_matrix.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_prompt_node_edge_traceability.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_schema_retrieval_coverage_report.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_alias_canonicalization_report.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_schema_plan_alignment_report.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_submission_completion_audit.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_revised_plan_completion_audit.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_revised_plan_section_status.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_rq_evidence_matrix.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_cq_query_pack.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_ablation_coverage_report.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_reviewer_risk_register.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_kg_eacl_experiment.py --kg-dir "$OUTPUTS_DIR" --experiment-dir "$EXP_DIR" --sample-size 120
"$PYTHON_BIN" scripts/build_cape_component_evidence_spans.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_predicate_cue_spans.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_evidence_graph_projection.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_edge_component_span_traceability.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_ncs_pcf_crosswalk.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/prepare_cape_crosswalk_review_package.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/evaluate_cape_crosswalk_review.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/run_cape_crosswalk_roundtrip_smoke.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_structural_evaluation.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/export_cape_kg_rdf_shacl.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_structural_gap_worklist.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_structural_review_action_plan.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/validate_cape_structural_review_returns.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_structural_review_application_plan.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_review_master_checklist.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_review_role_quickstart.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_review_status_dashboard.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_review_launch_checklist.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_review_handoff.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_gate_action_plan.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_review_master_checklist.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_review_first_batch_card.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_review_role_quickstart.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_review_status_dashboard.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_review_launch_checklist.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_review_handoff.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_prov_o_export.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/export_cape_kg_rdf_shacl.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_evidence_graph_projection.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_edge_component_span_traceability.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_method_module_coverage.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_method_novelty_positioning.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_qwen3_model_scaling_report.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_rq_evidence_matrix.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_cq_query_pack.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_ablation_coverage_report.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_alias_canonicalization_report.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_gold_sampling_coverage_report.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_gold_item_feasibility_report.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_method_novelty_positioning.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_qwen3_model_scaling_report.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_reviewer_risk_register.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_evidence_graph_projection.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_edge_component_span_traceability.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
build_neo4j_exports
"$PYTHON_BIN" scripts/build_cape_public_reproducibility_manifest.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_anonymized_submission_prep.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_responsible_nlp_checklist_prep.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_experiment_reproduction_card.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_provenance_manifest.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_eacl_plan_compliance_matrix.py \
  --experiment-dir "$EXP_DIR" \
  --plan-file "$PLAN_FILE"

"$PYTHON_BIN" scripts/build_cape_paper_section_source_map.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_post_human_scoring_readiness.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_claim_language_guardrails.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_reviewer_response_prep.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_submission_timeline_action_board.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_anonymized_submission_prep.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_responsible_nlp_checklist_prep.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_experiment_reproduction_card.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_eacl_submission_package_manifest.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_submission_completion_audit.py \
  --experiment-dir "$EXP_DIR" \
  --plan-file "$PLAN_FILE" \
  --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_revised_plan_completion_audit.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_revised_plan_section_status.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR" --plan-file "$PLAN_FILE"

"$PYTHON_BIN" scripts/build_cape_rq_evidence_matrix.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_cq_query_pack.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_gold_sampling_coverage_report.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_gold_item_feasibility_report.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_method_novelty_positioning.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_reviewer_risk_register.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_evidence_graph_projection.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_edge_component_span_traceability.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
build_neo4j_exports
"$PYTHON_BIN" scripts/build_cape_public_reproducibility_manifest.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_provenance_manifest.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_prov_o_export.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_evaluation_protocol_lock.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_release_bundle.py \
  --experiment-dir "$EXP_DIR" \
  --outputs-dir "$OUTPUTS_DIR" \
  --plan-file "$PLAN_FILE" \
  --stamp "$STAMP"
"$PYTHON_BIN" scripts/build_cape_anonymized_submission_prep.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_eacl_submission_package_manifest.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_human_review_status_dashboard.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_evaluation_protocol_lock.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR" --plan-file "$PLAN_FILE"

"$PYTHON_BIN" scripts/validate_cape_pre_human_handoff.py \
  --experiment-dir "$EXP_DIR" \
  --outputs-dir "$OUTPUTS_DIR"

# The validation step writes the authoritative pre-human status. Re-render
# downstream summaries that display that status, then rebuild the release
# bundle so the final tarballs carry the same state users see on disk.
"$PYTHON_BIN" scripts/build_cape_submission_completion_audit.py \
  --experiment-dir "$EXP_DIR" \
  --plan-file "$PLAN_FILE" \
  --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_eacl_plan_compliance_matrix.py \
  --experiment-dir "$EXP_DIR" \
  --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_revised_plan_completion_audit.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_revised_plan_section_status.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_annotation_protocol_traceability.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_metric_traceability_audit.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_contribution_claim_traceability.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_related_work_baseline_traceability.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_eacl_paper_draft.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_paper_section_source_map.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_post_human_scoring_readiness.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_claim_language_guardrails.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_reviewer_response_prep.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_submission_timeline_action_board.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_experiment_reproduction_card.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_eacl_submission_package_manifest.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_annotation_calibration_pack.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_review_master_checklist.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_review_first_batch_card.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_review_role_quickstart.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_review_status_dashboard.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_review_launch_checklist.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_review_handoff.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_gold_sampling_coverage_report.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_gold_item_feasibility_report.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_method_novelty_positioning.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_qwen3_model_scaling_report.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_reviewer_risk_register.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_evidence_graph_projection.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_edge_component_span_traceability.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
build_neo4j_exports
"$PYTHON_BIN" scripts/build_cape_public_reproducibility_manifest.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_anonymized_submission_prep.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_responsible_nlp_checklist_prep.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_experiment_reproduction_card.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_evaluation_protocol_lock.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_release_bundle.py \
  --experiment-dir "$EXP_DIR" \
  --outputs-dir "$OUTPUTS_DIR" \
  --plan-file "$PLAN_FILE" \
  --stamp "$STAMP"
"$PYTHON_BIN" scripts/build_cape_anonymized_submission_prep.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_eacl_submission_package_manifest.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_human_review_status_dashboard.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_evaluation_protocol_lock.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/validate_cape_pre_human_handoff.py \
  --experiment-dir "$EXP_DIR" \
  --outputs-dir "$OUTPUTS_DIR"

# The final validation above may update the authoritative PASS/WARN status.
# Re-render status-bearing summaries once more so a subsequent validator run
# sees the same state that is displayed to users and packaged in release files.
"$PYTHON_BIN" scripts/build_cape_submission_completion_audit.py \
  --experiment-dir "$EXP_DIR" \
  --plan-file "$PLAN_FILE" \
  --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_eacl_plan_compliance_matrix.py \
  --experiment-dir "$EXP_DIR" \
  --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_revised_plan_completion_audit.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_revised_plan_section_status.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_annotation_protocol_traceability.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_metric_traceability_audit.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_contribution_claim_traceability.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_related_work_baseline_traceability.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_eacl_paper_draft.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_paper_section_source_map.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_post_human_scoring_readiness.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_claim_language_guardrails.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_reviewer_response_prep.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_submission_timeline_action_board.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_anonymized_submission_prep.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_responsible_nlp_checklist_prep.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_experiment_reproduction_card.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_eacl_submission_package_manifest.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_human_review_master_checklist.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_review_first_batch_card.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_review_role_quickstart.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_review_status_dashboard.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_review_launch_checklist.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_human_review_handoff.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_gold_sampling_coverage_report.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_gold_item_feasibility_report.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_method_novelty_positioning.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_qwen3_model_scaling_report.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_reviewer_risk_register.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_evidence_graph_projection.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_edge_component_span_traceability.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
build_neo4j_exports
"$PYTHON_BIN" scripts/build_cape_public_reproducibility_manifest.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_anonymized_submission_prep.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_responsible_nlp_checklist_prep.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_experiment_reproduction_card.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_provenance_manifest.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_prov_o_export.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR"
"$PYTHON_BIN" scripts/build_cape_evaluation_protocol_lock.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_release_bundle.py \
  --experiment-dir "$EXP_DIR" \
  --outputs-dir "$OUTPUTS_DIR" \
  --plan-file "$PLAN_FILE" \
  --stamp "$STAMP"
"$PYTHON_BIN" scripts/build_cape_anonymized_submission_prep.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_eacl_submission_package_manifest.py --experiment-dir "$EXP_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/build_cape_human_review_status_dashboard.py --experiment-dir "$EXP_DIR"
"$PYTHON_BIN" scripts/build_cape_evaluation_protocol_lock.py --experiment-dir "$EXP_DIR" --outputs-dir "$OUTPUTS_DIR" --plan-file "$PLAN_FILE"
"$PYTHON_BIN" scripts/validate_cape_pre_human_handoff.py \
  --experiment-dir "$EXP_DIR" \
  --outputs-dir "$OUTPUTS_DIR"

RELEASE_CHECKSUMS="$EXP_DIR/06_release/release_bundle_checksums.sha256"
HANDOFF_CHECKSUMS="$EXP_DIR/06_release/human_review_handoff/human_review_handoff_checksums.sha256"
release_checksum_status="not_checked"
handoff_checksum_status="not_checked"
if [[ -f "$RELEASE_CHECKSUMS" ]]; then
  sha256sum -c "$RELEASE_CHECKSUMS"
  release_checksum_status="OK"
fi
if [[ -f "$HANDOFF_CHECKSUMS" ]]; then
  sha256sum -c "$HANDOFF_CHECKSUMS"
  handoff_checksum_status="OK"
fi

ENDED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
REFRESH_SUMMARY_JSON="$EXP_DIR/06_release/post_annotation_refresh_last_run.json"
REFRESH_SUMMARY_MD="$EXP_DIR/06_release/post_annotation_refresh_last_run.md"

"$PYTHON_BIN" - "$REFRESH_SUMMARY_JSON" "$REFRESH_SUMMARY_MD" "$EXP_DIR" "$OUTPUTS_DIR" "$PLAN_FILE" "$STAMP" "$APPLY_IMPORTS" "$STARTED_AT" "$ENDED_AT" "$release_checksum_status" "$handoff_checksum_status" <<'PY'
import json
import sys
from pathlib import Path

json_path = Path(sys.argv[1])
md_path = Path(sys.argv[2])
exp_dir = Path(sys.argv[3])
outputs_dir = Path(sys.argv[4])
plan_file = sys.argv[5]
stamp = sys.argv[6]
apply_imports = sys.argv[7]
started_at = sys.argv[8]
ended_at = sys.argv[9]
release_checksum_status = sys.argv[10]
handoff_checksum_status = sys.argv[11]

def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))

claim_gate = read_json(exp_dir / "06_release/claim_gate_report.json", {}) or {}
pre_human = read_json(exp_dir / "06_release/pre_human_handoff_validation.json", {}) or {}
return_preflight = read_json(exp_dir / "06_release/human_review_return_preflight.json", {}) or {}
completion = read_json(exp_dir / "06_release/submission_completion_audit_ko.json", {}) or {}
release_manifest = read_json(exp_dir / "06_release/release_bundle_manifest.json", {}) or {}
human_summary = read_json(exp_dir / "04_evaluation/human_gold_validation_summary.json", {}) or {}
mapping_progress = read_json(exp_dir / "06_release/mapping_review_progress_summary.json", {}) or {}
crosswalk_metrics = read_json(exp_dir / "04_evaluation/crosswalk_expert_metrics.json", {}) or {}
crosswalk_summary = (crosswalk_metrics.get("metrics") or {}) if isinstance(crosswalk_metrics, dict) else {}

payload = {
    "started_at_utc": started_at,
    "ended_at_utc": ended_at,
    "experiment_dir": str(exp_dir),
    "outputs_dir": str(outputs_dir),
    "plan_file": plan_file,
    "stamp": stamp,
    "apply_imports": apply_imports,
    "claim_status": "post_annotation_refresh_success_pending_human_returns",
    "claim_gate_overall_status": claim_gate.get("overall_status"),
    "claim_gate_required_failures": claim_gate.get("required_failure_count"),
    "claim_gate_optional_failures": claim_gate.get("optional_failure_count"),
    "pre_human_handoff_status": pre_human.get("overall_status"),
    "pre_human_handoff_status_counts": pre_human.get("status_counts"),
    "return_preflight_status": return_preflight.get("overall_status"),
    "present_human_return_files": (completion.get("summary") or {}).get("present_human_return_files"),
    "apply_scope": return_preflight.get("apply_scope"),
    "minimum_paper_gate_ready_after_preflight": return_preflight.get("minimum_paper_gate_ready_after_preflight"),
    "optional_mapping_ready_after_preflight": return_preflight.get("optional_mapping_ready_after_preflight"),
    "optional_crosswalk_ready_after_preflight": return_preflight.get("optional_crosswalk_ready_after_preflight"),
    "optional_active_effort_ready_after_preflight": return_preflight.get("optional_active_effort_ready_after_preflight"),
    "adjudicated_chunks": human_summary.get("completed_adjudicated_chunks"),
    "gold_item_count": human_summary.get("gold_item_count_for_readiness"),
    "mapping_pending_rows": mapping_progress.get("pending_rows"),
    "crosswalk_pending_rows": crosswalk_summary.get("pending_rows"),
    "internal_bundle": release_manifest.get("internal_bundle"),
    "public_safe_bundle": release_manifest.get("public_safe_bundle"),
    "release_checksum_status": release_checksum_status,
    "handoff_checksum_status": handoff_checksum_status,
}

json_path.parent.mkdir(parents=True, exist_ok=True)
json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

lines = [
    "# CAPE-KG Post-Annotation Refresh Last Run",
    "",
    f"Started: `{started_at}`",
    f"Ended: `{ended_at}`",
    f"Experiment: `{exp_dir}`",
    f"APPLY_IMPORTS: `{apply_imports}`",
    f"Stamp: `{stamp}`",
    "",
    "## Status",
    "",
    f"- Claim status: `{payload['claim_status']}`",
    f"- Claim gate: `{payload['claim_gate_overall_status']}`",
    f"- Required claim-gate failures: {payload['claim_gate_required_failures']}",
    f"- Optional claim-gate failures: {payload['claim_gate_optional_failures']}",
    f"- Pre-human handoff validation: `{payload['pre_human_handoff_status']}`; source `{exp_dir / '06_release/pre_human_handoff_validation.md'}`",
    f"- Return preflight: `{payload['return_preflight_status']}`",
    f"- Present human return files: {payload['present_human_return_files']}",
    f"- Apply scope: `{payload['apply_scope']}`",
    f"- Minimum paper gate ready after preflight: {payload['minimum_paper_gate_ready_after_preflight']}",
    f"- Optional mapping ready after preflight: {payload['optional_mapping_ready_after_preflight']}",
    f"- Optional crosswalk ready after preflight: {payload['optional_crosswalk_ready_after_preflight']}",
    f"- Optional active-effort ready after preflight: {payload['optional_active_effort_ready_after_preflight']}",
    f"- Adjudicated chunks: {payload['adjudicated_chunks']}",
    f"- Gold item count: {payload['gold_item_count']}",
    f"- Mapping pending rows: {payload['mapping_pending_rows']}",
    f"- Crosswalk pending rows: {payload['crosswalk_pending_rows']}",
    f"- Release checksum status: `{payload['release_checksum_status']}`",
    f"- Handoff checksum status: `{payload['handoff_checksum_status']}`",
    "",
    "## Release Bundles",
    "",
    f"- Internal: `{(payload['internal_bundle'] or {}).get('path')}`",
    f"- Internal SHA256: `{(payload['internal_bundle'] or {}).get('sha256')}`",
    f"- Public-safe: `{(payload['public_safe_bundle'] or {}).get('path')}`",
    f"- Public-safe SHA256: `{(payload['public_safe_bundle'] or {}).get('sha256')}`",
    "",
    "## Interpretation",
    "",
    "- This run proves the post-annotation refresh pipeline currently completes.",
    "- `APPLY_IMPORTS=0` means no reviewed human-return files were applied.",
    "- Human-gold, IAA, adjudication, proposed human-gold scoring, and expert mapping claims remain pending until reviewed files are returned and imported.",
    "",
]
md_path.write_text("\n".join(lines), encoding="utf-8")
PY

echo "Post-annotation refresh complete."
echo "Final report: $EXP_DIR/07_reports/final_eacl_experiment_report.md"
echo "Claim gate: $EXP_DIR/06_release/claim_gate_report.md"
echo "Refresh summary: $REFRESH_SUMMARY_MD"
