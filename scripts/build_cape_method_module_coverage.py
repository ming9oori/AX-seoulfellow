#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build CAPE-KG M1-M11 method module coverage evidence."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_OUTPUTS_DIR = Path("outputs")


def read_jsonl_count(path):
    path = Path(path)
    if not path.exists():
        return 0
    count = 0
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                count += 1
    return count


def read_csv_count(path):
    path = Path(path)
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8-sig") as f:
        return max(0, sum(1 for _ in f) - 1)


def artifact(path, kind="file", required=True):
    path = Path(path)
    exists = path.exists() and path.stat().st_size > 0
    row = {
        "path": str(path),
        "kind": kind,
        "required": bool(required),
        "exists": exists,
        "bytes": path.stat().st_size if path.exists() else 0,
    }
    if exists and path.suffix == ".jsonl":
        row["records"] = read_jsonl_count(path)
    elif exists and path.suffix == ".csv":
        row["records"] = read_csv_count(path)
    return row


def module(module_id, name, purpose, artifacts, scripts, remaining, human_dependent=False):
    required = [row for row in artifacts if row["required"]]
    missing = [row for row in required if not row["exists"]]
    optional_missing = [row for row in artifacts if not row["required"] and not row["exists"]]
    if missing:
        status = "missing_required_artifact"
    elif human_dependent:
        status = "implemented_artifacts_present_human_claim_pending"
    else:
        status = "implemented_artifacts_present"
    return {
        "module_id": module_id,
        "name": name,
        "purpose": purpose,
        "status": status,
        "human_dependent_for_final_claim": bool(human_dependent),
        "required_artifact_count": len(required),
        "missing_required_artifact_count": len(missing),
        "optional_missing_artifact_count": len(optional_missing),
        "artifacts": artifacts,
        "scripts": [artifact(path, kind="script", required=True) for path in scripts],
        "remaining_for_paper_claim": remaining,
    }


def build_payload(exp_dir, outputs_dir):
    exp_dir = Path(exp_dir)
    outputs_dir = Path(outputs_dir)
    modules = [
        module(
            "M1",
            "Document structure recovery",
            "Recover OCR rows, clean sentences, chunks, and evaluation subset.",
            [
                artifact(outputs_dir / "02_ocr/document_structure_reviewed.json"),
                artifact(outputs_dir / "02_ocr/ocr_sentences_clean.jsonl"),
                artifact(outputs_dir / "02_ocr/layer2_chunks.jsonl"),
                artifact(exp_dir / "01_data/evaluation_chunks.jsonl"),
                artifact(outputs_dir / "02_ocr/ocr_quality_report.md"),
            ],
            ["scripts/build_ax_epak_internal_kg.py", "scripts/build_cape_kg_eacl_experiment.py"],
            "No additional automatic step required; source-text release still requires rights review.",
        ),
        module(
            "M2",
            "CQ generation and selection",
            "Represent competency questions and use them in evaluation/reporting.",
            [
                artifact(outputs_dir / "03_schema/competency_questions.json"),
                artifact(exp_dir / "02_schema/competency_questions.json"),
                artifact(outputs_dir / "10_evaluation/cq_answerability_report.md"),
                artifact(exp_dir / "04_evaluation/cq_answerability_by_condition.csv"),
                artifact(exp_dir / "04_evaluation/cq_query_sample_answers.csv"),
                artifact(exp_dir / "06_release/cq_query_pack.json"),
                artifact(exp_dir / "06_release/cq_query_pack.md"),
            ],
            ["scripts/build_cape_kg_eacl_experiment.py", "scripts/build_cape_cq_query_pack.py"],
            "Human-gold CQ answerability must be recomputed after adjudication.",
        ),
        module(
            "M3",
            "CQ-linked schema retrieval",
            "Provide chunk-specific schema/taxonomy context and ablate schema retrieval.",
            [
                artifact(exp_dir / "02_schema/cape_schema.json"),
                artifact(exp_dir / "02_schema/prompts/P_cape_kg.txt"),
                artifact(exp_dir / "02_schema/prompts/P_minus_Schema_retrieval.txt"),
                artifact(exp_dir / "06_release/schema_retrieval_coverage_report.json"),
                artifact(exp_dir / "06_release/schema_retrieval_coverage_report.md"),
                artifact(exp_dir / "04_evaluation/schema_retrieval_cq_support_by_condition.csv"),
                artifact(exp_dir / "49_qwen3_8b_cape_ablation_120_valid.jsonl"),
                artifact(exp_dir / "50_qwen3_8b_cape_ablation_120_quality_report.md"),
            ],
            [
                "scripts/run_cape_llm_condition_baselines.py",
                "scripts/build_cape_schema_retrieval_coverage_report.py",
                "scripts/build_cape_kg_eacl_experiment.py",
            ],
            "Final claim requires human-gold comparison of P vs. schema-retrieval ablation.",
            human_dependent=True,
        ),
        module(
            "M4",
            "Procedural frame extraction",
            "Extract task frames and procedural structures before graph assembly.",
            [
                artifact(outputs_dir / "04_task_frames/canonical_task_catalog.json"),
                artifact(outputs_dir / "04_task_frames/task_frame_candidates_raw.jsonl"),
                artifact(outputs_dir / "05_procedure/procedure_structures_clean.jsonl"),
                artifact(outputs_dir / "05_procedure/procedure_edges.jsonl"),
                artifact(outputs_dir / "04_task_frames/task_frame_quality_report.md"),
                artifact(outputs_dir / "05_procedure/procedure_quality_report.md"),
            ],
            ["scripts/build_ax_epak_internal_kg.py", "scripts/run_cep_onto_llm_extraction.py"],
            "Human review should verify task/step correctness before final claims.",
            human_dependent=True,
        ),
        module(
            "M5",
            "Evidence-span constrained triple extraction",
            "Build schema-valid triples with evidence anchors.",
            [
                artifact(outputs_dir / "06_triples/layer2_triples_schema_valid.jsonl"),
                artifact(outputs_dir / "06_triples/layer2_triples_component_spans.jsonl"),
                artifact(outputs_dir / "06_triples/layer2_predicate_cue_spans.jsonl"),
                artifact(outputs_dir / "06_triples/evidence_anchors.jsonl"),
                artifact(outputs_dir / "13_evidence_graph/evidence_graph_projection_summary.json"),
                artifact(outputs_dir / "13_evidence_graph/evidence_anchor_nodes.jsonl"),
                artifact(outputs_dir / "13_evidence_graph/evidenced_by_edges.jsonl"),
                artifact(outputs_dir / "13_evidence_graph/edge_component_span_links.jsonl"),
                artifact(outputs_dir / "13_evidence_graph/edge_component_span_links.csv"),
                artifact(exp_dir / "04_evaluation/evidence_span_granularity_metrics.json"),
                artifact(exp_dir / "04_evaluation/evidence_span_granularity_report.md"),
                artifact(exp_dir / "04_evaluation/predicate_cue_span_metrics.json"),
                artifact(exp_dir / "04_evaluation/predicate_cue_span_report.md"),
                artifact(exp_dir / "04_evaluation/predicate_cue_span_rows.csv"),
                artifact(exp_dir / "06_release/edge_component_span_traceability.json"),
                artifact(exp_dir / "06_release/edge_component_span_traceability.md"),
                artifact(exp_dir / "04_evaluation/human_gold_span_iou_metrics.json"),
                artifact(exp_dir / "04_evaluation/human_gold_span_iou_components.csv"),
                artifact(exp_dir / "04_evaluation/human_gold_span_iou_report.md"),
                artifact(exp_dir / "06_release/provenance_manifest.json"),
                artifact(exp_dir / "06_release/provenance_manifest.md"),
                artifact(exp_dir / "06_release/provenance_prov_o.ttl"),
                artifact(exp_dir / "06_release/provenance_prov_o_summary.json"),
                artifact(exp_dir / "06_release/provenance_prov_o_report.md"),
                artifact(exp_dir / "04_evaluation/provenance_llm_run_index.csv"),
                artifact(outputs_dir / "06_triples/triple_quality_report.md"),
                artifact(exp_dir / "01_data/silver_reference_edges.jsonl"),
                artifact(exp_dir / "03_predictions/P_cape_kg_silver.jsonl"),
            ],
            [
                "scripts/build_ax_epak_internal_kg.py",
                "scripts/build_cape_component_evidence_spans.py",
                "scripts/build_cape_predicate_cue_spans.py",
                "scripts/build_cape_evidence_graph_projection.py",
                "scripts/build_cape_edge_component_span_traceability.py",
                "scripts/evaluate_cape_human_gold_span_iou.py",
                "scripts/build_cape_provenance_manifest.py",
                "scripts/build_cape_prov_o_export.py",
                "scripts/run_cape_llm_condition_baselines.py",
            ],
            "Component-level span diagnostics are present; character/span exactness must still be validated against adjudicated human gold.",
            human_dependent=True,
        ),
        module(
            "M6",
            "Span verifier",
            "Evaluate evidence support and span grounding quality.",
            [
                artifact(exp_dir / "04_evaluation/actual_llm_silver_metrics.json"),
                artifact(exp_dir / "04_evaluation/actual_llm_silver_evaluation_report.md"),
                artifact(exp_dir / "04_evaluation/evidence_span_granularity_metrics.json"),
                artifact(exp_dir / "04_evaluation/evidence_span_granularity_report.md"),
                artifact(exp_dir / "04_evaluation/predicate_cue_span_metrics.json"),
                artifact(exp_dir / "04_evaluation/predicate_cue_span_report.md"),
                artifact(exp_dir / "04_evaluation/predicate_cue_span_rows.csv"),
                artifact(exp_dir / "06_release/edge_component_span_traceability.json"),
                artifact(exp_dir / "06_release/edge_component_span_traceability.md"),
                artifact(outputs_dir / "13_evidence_graph/edge_component_span_links.jsonl"),
                artifact(outputs_dir / "06_triples/layer2_predicate_cue_spans.jsonl"),
                artifact(exp_dir / "04_evaluation/qwen3_32b_awq_core_silver_metrics.json"),
                artifact(exp_dir / "04_evaluation/human_gold_metrics.json"),
                artifact(exp_dir / "04_evaluation/human_gold_span_iou_metrics.json"),
                artifact(exp_dir / "04_evaluation/human_gold_span_iou_report.md"),
            ],
            [
                "scripts/build_cape_component_evidence_spans.py",
                "scripts/build_cape_predicate_cue_spans.py",
                "scripts/build_cape_edge_component_span_traceability.py",
                "scripts/evaluate_actual_llm_silver.py",
                "scripts/evaluate_cape_human_gold.py",
                "scripts/evaluate_cape_human_gold_span_iou.py",
            ],
            "Current verifier evidence is silver/proxy; human-gold evidence metrics are pending.",
            human_dependent=True,
        ),
        module(
            "M7",
            "Ontology/SHACL validator",
            "Check schema, domain/range, predicate, and conformance constraints.",
            [
                artifact(exp_dir / "02_schema/cape_shapes.shacl.ttl"),
                artifact(exp_dir / "02_schema/cape_schema.json"),
                artifact(exp_dir / "04_evaluation/structural_evaluation_metrics.json"),
                artifact(exp_dir / "04_evaluation/ontology_conformance_metrics.json"),
                artifact(exp_dir / "04_evaluation/ontology_conformance_report.md"),
                artifact(outputs_dir / "12_rdf/cape_kg_layer2.ttl"),
                artifact(outputs_dir / "12_rdf/cape_kg_runtime_shapes.shacl.ttl"),
                artifact(outputs_dir / "12_rdf/cape_kg_shacl_validation_summary.json"),
                artifact(outputs_dir / "12_rdf/cape_kg_shacl_validation_report.md"),
                artifact(outputs_dir / "07_layer2_graph/layer2_graph_quality_report.md"),
            ],
            [
                "scripts/build_cape_structural_evaluation.py",
                "scripts/export_cape_kg_rdf_shacl.py",
                "scripts/build_cape_kg_eacl_experiment.py",
                "scripts/validate_cape_experiment_readiness.py",
            ],
            "No additional automatic step required; final conformance table should use human-gold predictions.",
        ),
        module(
            "M8",
            "Procedural consistency validator",
            "Check procedural edges, precedence, gateway, and artifact-flow consistency.",
            [
                artifact(exp_dir / "04_evaluation/structural_evaluation_metrics.json"),
                artifact(exp_dir / "04_evaluation/procedural_consistency_metrics.json"),
                artifact(exp_dir / "04_evaluation/procedural_consistency_report.md"),
                artifact(exp_dir / "04_evaluation/cq_answerability_structural_metrics.json"),
                artifact(exp_dir / "04_evaluation/cq_answerability_structural.csv"),
                artifact(exp_dir / "04_evaluation/structural_gap_worklist_summary.json"),
                artifact(exp_dir / "04_evaluation/structural_gap_worklist_report.md"),
                artifact(exp_dir / "05_review/structural_review_checkpoint_candidates.csv"),
                artifact(exp_dir / "05_review/structural_gateway_branch_gaps.csv"),
                artifact(exp_dir / "05_review/structural_review_optional_returns.csv"),
                artifact(exp_dir / "06_release/structural_review_action_plan.md"),
                artifact(exp_dir / "06_release/structural_review_action_plan.json"),
                artifact(exp_dir / "06_release/structural_review_return_preflight.md"),
                artifact(exp_dir / "06_release/structural_review_return_preflight.json"),
                artifact(exp_dir / "06_release/structural_review_application_plan.md"),
                artifact(exp_dir / "06_release/structural_review_application_plan.json"),
                artifact(exp_dir / "05_review/structural_review_application_actions.csv"),
                artifact(outputs_dir / "05_procedure/procedure_quality_report.md"),
                artifact(outputs_dir / "07_layer2_graph/layer2_edges.jsonl"),
            ],
            [
                "scripts/build_cape_structural_evaluation.py",
                "scripts/build_cape_structural_gap_worklist.py",
                "scripts/build_cape_structural_review_action_plan.py",
                "scripts/validate_cape_structural_review_returns.py",
                "scripts/build_cape_structural_review_application_plan.py",
                "scripts/build_cape_kg_eacl_experiment.py",
                "scripts/evaluate_cape_human_gold.py",
            ],
            "Human-gold procedural consistency should be recomputed after adjudication.",
            human_dependent=True,
        ),
        module(
            "M9",
            "Alias/canonicalization module",
            "Maintain canonical task labels, aliases, and comparable node labels.",
            [
                artifact(outputs_dir / "04_task_frames/canonical_task_catalog.json"),
                artifact(outputs_dir / "07_layer2_graph/layer2_alias_dictionary.json"),
                artifact(exp_dir / "06_release/alias_canonicalization_report.json"),
                artifact(exp_dir / "06_release/alias_canonicalization_report.md"),
                artifact(exp_dir / "04_evaluation/alias_canonicalization_collision_groups.csv"),
                artifact(exp_dir / "02_schema/prompts/B3_edc_style_baseline.txt"),
                artifact(exp_dir / "49_qwen3_8b_edc_schema_ablation_valid.jsonl"),
            ],
            [
                "scripts/build_ax_epak_internal_kg.py",
                "scripts/build_cape_alias_canonicalization_report.py",
                "scripts/run_cape_llm_condition_baselines.py",
            ],
            "Final node canonicalization quality requires human-gold node matching.",
            human_dependent=True,
        ),
        module(
            "M10",
            "Active review queue",
            "Prioritize likely high-impact errors and human annotation work.",
            [
                artifact(exp_dir / "05_review/active_review_queue.jsonl"),
                artifact(exp_dir / "05_review/human_gold_annotation_priority_queue.csv"),
                artifact(exp_dir / "01_data/gold_annotation/annotation_expansion_manifest.json"),
                artifact(exp_dir / "01_data/gold_annotation/annotation_expansion_report.md"),
                artifact(exp_dir / "05_review/actual_llm_active_review_queue_P_cape_kg_actual.jsonl"),
                artifact(exp_dir / "04_evaluation/active_review_efficiency_metrics.json"),
                artifact(exp_dir / "04_evaluation/active_review_efficiency_report.md"),
                artifact(exp_dir / "04_evaluation/active_review_ablation_metrics.json"),
                artifact(exp_dir / "04_evaluation/active_review_ablation_report.md"),
                artifact(exp_dir / "05_review/active_review_human_effort_template.csv"),
                artifact(exp_dir / "06_release/active_review_human_effort_plan.md"),
                artifact(exp_dir / "04_evaluation/active_review_pool_overlap_summary.json"),
                artifact(exp_dir / "04_evaluation/active_review_pool_overlap_report.md"),
                artifact(exp_dir / "06_release/human_review_master_checklist_ko.md"),
                artifact(exp_dir / "06_release/human_review_master_checklist_ko.json"),
                artifact(exp_dir / "05_review/human_review_master_return_files.csv"),
                artifact(exp_dir / "04_evaluation/active_review_human_effort_metrics.json"),
                artifact(exp_dir / "04_evaluation/active_review_human_effort_report.md"),
            ],
            [
                "scripts/evaluate_cape_active_review_efficiency.py",
                "scripts/build_cape_active_review_human_effort.py",
                "scripts/build_cape_human_review_master_checklist.py",
                "scripts/build_cape_annotation_progress_report.py",
            ],
            "Active-review ablation is represented with silver/proxy diagnostics; final efficiency claim requires human adjudication outcomes and reviewer effort/timing.",
            human_dependent=True,
        ),
        module(
            "M11",
            "NCS/PCF mapping evaluator",
            "Generate and evaluate standard taxonomy mapping candidates.",
            [
                artifact(outputs_dir / "08_mapping/l2_ncs_mapping_candidates.jsonl"),
                artifact(outputs_dir / "08_mapping/l2_pcf_mapping_candidates.jsonl"),
                artifact(outputs_dir / "08_mapping/l2_ncs_pcf_crosswalk_candidates.jsonl"),
                artifact(exp_dir / "04_evaluation/ncs_pcf_crosswalk_summary.json"),
                artifact(exp_dir / "04_evaluation/ncs_pcf_crosswalk_report.md"),
                artifact(exp_dir / "04_evaluation/mapping_downstream_results.csv"),
                artifact(exp_dir / "04_evaluation/mapping_downstream_arm_diagnostics.csv"),
                artifact(exp_dir / "04_evaluation/mapping_downstream_arm_rerank_details.csv"),
                artifact(exp_dir / "04_evaluation/mapping_downstream_arm_rerank_summary.json"),
                artifact(exp_dir / "04_evaluation/mapping_downstream_report.md"),
                artifact(exp_dir / "01_data/mapping_review/mapping_review_items.jsonl"),
                artifact(exp_dir / "04_evaluation/mapping_expert_metrics.json"),
                artifact(exp_dir / "06_release/mapping_review_progress_summary.json"),
            ],
            [
                "scripts/build_cape_ncs_pcf_crosswalk.py",
                "scripts/evaluate_cape_mapping_review.py",
                "scripts/build_cape_mapping_review_progress_report.py",
            ],
            "P@K/MRR/nDCG@10, explanation-quality, crosswalk accept-rate, and utility claims require completed expert review.",
            human_dependent=True,
        ),
    ]

    missing_modules = [row["module_id"] for row in modules if row["missing_required_artifact_count"]]
    human_modules = [row["module_id"] for row in modules if row["human_dependent_for_final_claim"]]
    missing_required = sum(row["missing_required_artifact_count"] for row in modules)
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "outputs_dir": str(outputs_dir),
        "summary": {
            "module_count": len(modules),
            "modules_with_required_artifacts": len(modules) - len(missing_modules),
            "missing_required_artifact_count": missing_required,
            "missing_modules": missing_modules,
            "human_dependent_module_count": len(human_modules),
            "human_dependent_modules": human_modules,
            "claim_status": "all_m1_m11_artifacts_present_human_claims_pending"
            if not missing_modules
            else "method_artifacts_incomplete",
        },
        "modules": modules,
    }
    return payload


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_report(payload):
    summary = payload["summary"]
    lines = [
        "# CAPE-KG Method Module Coverage",
        "",
        f"Generated: {payload['generated_at_utc']}",
        "",
        "This file maps the revised EACL plan's M1-M11 modules to current executable artifacts. It distinguishes implementation evidence from paper-claim evidence.",
        "",
        "## Summary",
        "",
        f"- Modules: {summary['module_count']}",
        f"- Modules with required artifacts: {summary['modules_with_required_artifacts']}",
        f"- Missing required artifacts: {summary['missing_required_artifact_count']}",
        f"- Human-dependent modules for final claims: {summary['human_dependent_module_count']}",
        f"- Claim status: `{summary['claim_status']}`",
        "",
        "## Module Table",
        "",
        "| module | status | human-dependent claim | required artifacts | missing | remaining for paper claim |",
        "|---|---|---:|---:|---:|---|",
    ]
    for row in payload["modules"]:
        lines.append(
            f"| {row['module_id']} {row['name']} | {row['status']} | "
            f"{'yes' if row['human_dependent_for_final_claim'] else 'no'} | "
            f"{row['required_artifact_count']} | {row['missing_required_artifact_count']} | "
            f"{row['remaining_for_paper_claim']} |"
        )
    lines += ["", "## Artifact Evidence", ""]
    for row in payload["modules"]:
        lines += [f"### {row['module_id']}. {row['name']}", ""]
        for art in row["artifacts"]:
            marker = "OK" if art["exists"] else "MISSING"
            required = "required" if art["required"] else "optional"
            count = f", records={art['records']}" if "records" in art else ""
            lines.append(f"- {marker} ({required}) `{art['path']}` bytes={art['bytes']}{count}")
        lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--outputs-dir", default=str(DEFAULT_OUTPUTS_DIR))
    args = parser.parse_args()

    payload = build_payload(Path(args.experiment_dir), Path(args.outputs_dir))
    release_dir = Path(args.experiment_dir) / "06_release"
    json_path = release_dir / "method_module_coverage.json"
    md_path = release_dir / "method_module_coverage.md"
    write_json(json_path, payload)
    write_text(md_path, build_report(payload))
    print(json.dumps({
        "coverage_json": str(json_path),
        "coverage_report": str(md_path),
        "claim_status": payload["summary"]["claim_status"],
        "missing_modules": payload["summary"]["missing_modules"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
