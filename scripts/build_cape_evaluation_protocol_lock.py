#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Freeze CAPE-KG evaluation protocol details before human returns."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_OUTPUTS_DIR = Path("outputs")
DEFAULT_PLAN_FILE = Path("AX_EACL_submission_review_revised_plan.md")
PROTOCOL_VERSION = "cape-eacl-evaluation-protocol-v1"

PROTOCOL_PUBLIC_FILES = [
    ("revised_plan", DEFAULT_PLAN_FILE),
    ("cape_schema", "experiments/cape_kg_eacl_20260627/02_schema/cape_schema.json"),
    ("prompt_contract", "experiments/cape_kg_eacl_20260627/02_schema/prompts/strict_json_contract.txt"),
    ("baseline_prompt_b0", "experiments/cape_kg_eacl_20260627/02_schema/prompts/B0_plain_llm_triple_extraction.txt"),
    ("baseline_prompt_b1", "experiments/cape_kg_eacl_20260627/02_schema/prompts/B1_predicate_constrained_llm.txt"),
    ("baseline_prompt_b2", "experiments/cape_kg_eacl_20260627/02_schema/prompts/B2_current_project_baseline.txt"),
    ("baseline_prompt_b3", "experiments/cape_kg_eacl_20260627/02_schema/prompts/B3_edc_style_baseline.txt"),
    ("baseline_prompt_b4", "experiments/cape_kg_eacl_20260627/02_schema/prompts/B4_taxonomy_rag_baseline.txt"),
    ("baseline_prompt_b5", "experiments/cape_kg_eacl_20260627/02_schema/prompts/B5_procedural_prompt_baseline.txt"),
    ("baseline_prompt_b6", "experiments/cape_kg_eacl_20260627/02_schema/prompts/B6_sac_kg_verifier_pruner_baseline.txt"),
    ("proposed_prompt", "experiments/cape_kg_eacl_20260627/02_schema/prompts/P_cape_kg.txt"),
    ("ablation_prompt_minus_schema_retrieval", "experiments/cape_kg_eacl_20260627/02_schema/prompts/P_minus_Schema_retrieval.txt"),
    ("human_gold_evaluator", "scripts/evaluate_cape_human_gold.py"),
    ("span_iou_evaluator", "scripts/evaluate_cape_human_gold_span_iou.py"),
    ("mapping_review_evaluator", "scripts/evaluate_cape_mapping_review.py"),
    ("crosswalk_review_evaluator", "scripts/evaluate_cape_crosswalk_review.py"),
    ("active_effort_evaluator", "scripts/build_cape_active_review_human_effort.py"),
    ("ablation_coverage_builder", "scripts/build_cape_ablation_coverage_report.py"),
    ("alias_canonicalization_builder", "scripts/build_cape_alias_canonicalization_report.py"),
    ("annotation_calibration_builder", "scripts/build_cape_annotation_calibration_pack.py"),
    ("statistical_analysis", "scripts/compute_cape_statistical_analysis.py"),
    ("return_preflight", "scripts/validate_cape_human_review_returns.py"),
    ("human_return_wrapper", "scripts/run_cape_human_return_apply.sh"),
    ("post_annotation_refresh_wrapper", "scripts/run_cape_post_annotation_refresh.sh"),
    ("pre_human_handoff_validator", "scripts/validate_cape_pre_human_handoff.py"),
    ("release_bundle_builder", "scripts/build_cape_release_bundle.py"),
    ("provenance_manifest_builder", "scripts/build_cape_provenance_manifest.py"),
    ("schema_retrieval_coverage_builder", "scripts/build_cape_schema_retrieval_coverage_report.py"),
    ("arr_submission_policy_checklist_builder", "scripts/build_cape_arr_submission_policy_checklist.py"),
    ("anonymized_submission_prep_builder", "scripts/build_cape_anonymized_submission_prep.py"),
    ("responsible_nlp_checklist_prep_builder", "scripts/build_cape_responsible_nlp_checklist_prep.py"),
    ("experiment_reproduction_card_builder", "scripts/build_cape_experiment_reproduction_card.py"),
    ("evidence_graph_projection_builder", "scripts/build_cape_evidence_graph_projection.py"),
    ("neo4j_evidence_query_pack_builder", "scripts/build_cape_neo4j_evidence_query_pack.py"),
    ("paper_table_blueprint_builder", "scripts/build_cape_paper_table_blueprint.py"),
    ("method_novelty_positioning_builder", "scripts/build_cape_method_novelty_positioning.py"),
    ("qwen3_model_scaling_report_builder", "scripts/build_cape_qwen3_model_scaling_report.py"),
    ("metric_traceability_audit_builder", "scripts/build_cape_metric_traceability_audit.py"),
    ("contribution_claim_traceability_builder", "scripts/build_cape_contribution_claim_traceability.py"),
    ("related_work_baseline_traceability_builder", "scripts/build_cape_related_work_baseline_traceability.py"),
    ("annotation_protocol_traceability_builder", "scripts/build_cape_annotation_protocol_traceability.py"),
    ("claim_language_guardrails_builder", "scripts/build_cape_claim_language_guardrails.py"),
    ("reviewer_response_prep_builder", "scripts/build_cape_reviewer_response_prep.py"),
    ("submission_timeline_action_board_builder", "scripts/build_cape_submission_timeline_action_board.py"),
    ("revised_plan_completion_audit_builder", "scripts/build_cape_revised_plan_completion_audit.py"),
    ("pre_human_status_helper", "scripts/cape_pre_human_status.py"),
]

CURRENT_CONTEXT_FILES = [
    ("claim_gate_report", "experiments/cape_kg_eacl_20260627/06_release/claim_gate_report.json"),
    ("arr_submission_policy_checklist", "experiments/cape_kg_eacl_20260627/06_release/arr_submission_policy_checklist.json"),
    ("anonymized_submission_prep", "experiments/cape_kg_eacl_20260627/06_release/anonymized_submission_prep.json"),
    ("responsible_nlp_checklist_prep", "experiments/cape_kg_eacl_20260627/06_release/responsible_nlp_checklist_prep.json"),
    ("experiment_reproduction_card", "experiments/cape_kg_eacl_20260627/06_release/experiment_reproduction_card.json"),
    ("paper_tables", "experiments/cape_kg_eacl_20260627/06_release/paper_tables.md"),
    ("paper_table_blueprint", "experiments/cape_kg_eacl_20260627/06_release/paper_table_blueprint.json"),
    ("claimable_main_table", "experiments/cape_kg_eacl_20260627/06_release/claimable_main_table.json"),
    ("ablation_coverage_report", "experiments/cape_kg_eacl_20260627/06_release/ablation_coverage_report.json"),
    ("alias_canonicalization_report", "experiments/cape_kg_eacl_20260627/06_release/alias_canonicalization_report.json"),
    ("claim_language_guardrails", "experiments/cape_kg_eacl_20260627/06_release/claim_language_guardrails.json"),
    ("reviewer_response_prep", "experiments/cape_kg_eacl_20260627/06_release/reviewer_response_prep.json"),
    ("submission_timeline_action_board", "experiments/cape_kg_eacl_20260627/06_release/submission_timeline_action_board.json"),
    ("revised_plan_completion_audit", "experiments/cape_kg_eacl_20260627/06_release/revised_plan_completion_audit.json"),
    ("revised_plan_completion_audit_public_safe", "experiments/cape_kg_eacl_20260627/06_release/revised_plan_completion_audit_public_safe.json"),
    ("method_module_coverage", "experiments/cape_kg_eacl_20260627/06_release/method_module_coverage.json"),
    ("schema_retrieval_coverage_report", "experiments/cape_kg_eacl_20260627/06_release/schema_retrieval_coverage_report.json"),
    ("method_novelty_positioning", "experiments/cape_kg_eacl_20260627/06_release/method_novelty_positioning.json"),
    ("qwen3_model_scaling_report", "experiments/cape_kg_eacl_20260627/06_release/qwen3_model_scaling_report.json"),
    ("metric_traceability_audit", "experiments/cape_kg_eacl_20260627/06_release/metric_traceability_audit.json"),
    ("contribution_claim_traceability", "experiments/cape_kg_eacl_20260627/06_release/contribution_claim_traceability.json"),
    ("related_work_baseline_traceability", "experiments/cape_kg_eacl_20260627/06_release/related_work_baseline_traceability.json"),
    ("annotation_protocol_traceability", "experiments/cape_kg_eacl_20260627/06_release/annotation_protocol_traceability.json"),
    ("rq_evidence_matrix", "experiments/cape_kg_eacl_20260627/06_release/rq_evidence_matrix.json"),
    ("evidence_graph_projection", "outputs/13_evidence_graph/evidence_graph_projection_summary.json"),
    ("neo4j_evidence_query_pack", "experiments/cape_kg_eacl_20260627/06_release/neo4j_evidence_query_pack.json"),
]

PRIVATE_LOCK_INPUTS = [
    ("evaluation_chunk_selection_120", "experiments/cape_kg_eacl_20260627/01_data/evaluation_chunks.jsonl"),
    ("gold_candidate_template_120", "experiments/cape_kg_eacl_20260627/01_data/gold_annotation_template.jsonl"),
    ("minimum_gold_package_a", "experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/annotator_A.jsonl"),
    ("minimum_gold_package_b", "experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/annotator_B.jsonl"),
    ("minimum_gold_resolution_template", "experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/adjudication.jsonl"),
    ("mapping_review_candidate_pool", "experiments/cape_kg_eacl_20260627/01_data/mapping_review/mapping_review_items.jsonl"),
    ("crosswalk_review_candidate_pool", "experiments/cape_kg_eacl_20260627/01_data/crosswalk_review/crosswalk_review_items.jsonl"),
]


def sha256_file(path):
    path = Path(path)
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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


def rel(path):
    return str(Path(path).as_posix())


def file_state(path, role):
    path = Path(path)
    exists = path.exists() and path.is_file()
    return {
        "role": role,
        "path": rel(path),
        "exists": exists,
        "bytes": path.stat().st_size if exists else 0,
        "sha256": sha256_file(path) if exists else "",
    }


def private_file_state(source_id, path):
    path = Path(path)
    exists = path.exists() and path.is_file()
    return {
        "source_id": source_id,
        "exists": exists,
        "bytes": path.stat().st_size if exists else 0,
        "sha256": sha256_file(path) if exists else "",
    }


def canonical_hash(payload):
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def collect_condition_sets(exp_dir):
    metrics = read_json(Path(exp_dir) / "04_evaluation/actual_llm_silver_metrics.json", {}) or {}
    rows = metrics.get("metrics") or []
    conditions = sorted({row.get("condition") for row in rows if row.get("condition")})
    qwen14 = read_json(Path(exp_dir) / "04_evaluation/qwen3_14b_core_silver_metrics.json", {}) or {}
    qwen32 = read_json(Path(exp_dir) / "04_evaluation/qwen3_32b_awq_core_silver_metrics.json", {}) or {}
    return {
        "main_condition_set": conditions,
        "model_scaling_conditions": {
            "qwen3_14b": sorted({row.get("condition") for row in (qwen14.get("metrics") or []) if row.get("condition")}),
            "qwen3_32b_awq": sorted({row.get("condition") for row in (qwen32.get("metrics") or []) if row.get("condition")}),
        },
    }


def build_payload(exp_dir, outputs_dir, plan_file):
    exp_dir = Path(exp_dir)
    outputs_dir = Path(outputs_dir)
    release_dir = exp_dir / "06_release"
    public_files = [file_state(path, role) for role, path in PROTOCOL_PUBLIC_FILES]
    current_context_files = [file_state(path, role) for role, path in CURRENT_CONTEXT_FILES]
    private_inputs = [private_file_state(source_id, path) for source_id, path in PRIVATE_LOCK_INPUTS]
    private_input_ids = [source_id for source_id, _path in PRIVATE_LOCK_INPUTS]
    claim_gate = read_json(release_dir / "claim_gate_report.json", {}) or {}
    pre_human = read_json(release_dir / "pre_human_handoff_validation.json", {}) or {}
    readiness = read_json(release_dir / "submission_readiness_audit.json", {}) or {}

    metric_definitions = {
        "human_gold_core": [
            {"metric": "node_label_f1", "unit": "condition", "source": "human-gold scored outputs"},
            {"metric": "edge_exact_f1", "unit": "condition", "source": "human-gold scored outputs"},
            {"metric": "predicate_f1", "unit": "condition", "source": "human-gold scored outputs"},
            {"metric": "evidence_exact_or_f1", "unit": "condition", "source": "human-gold evidence anchors"},
            {"metric": "component_span_exact_match", "unit": "subject/predicate/object component", "source": "adjudicated spans"},
            {"metric": "component_span_iou", "unit": "subject/predicate/object component", "source": "adjudicated spans"},
        ],
        "structural": [
            {"metric": "ontology_conformance", "unit": "KG", "source": "domain/range/schema validation"},
            {"metric": "procedural_consistency", "unit": "KG", "source": "cycle, gateway, artifact-flow checks"},
            {"metric": "cq_answerability", "unit": "competency question", "source": "graph-query answerability"},
        ],
        "mapping_expert": [
            {"metric": "expert_accept_rate", "unit": "standard"},
            {"metric": "hit_at_1", "unit": "standard"},
            {"metric": "hit_at_3", "unit": "standard"},
            {"metric": "hit_at_5", "unit": "standard"},
            {"metric": "precision_at_5", "unit": "standard"},
            {"metric": "mrr", "unit": "standard"},
            {"metric": "ndcg_at_10", "unit": "standard"},
            {"metric": "explanation_quality_score_mean", "unit": "standard"},
        ],
        "crosswalk_expert": [
            {"metric": "expert_accept_rate", "unit": "NCS-PCF source-task group"},
            {"metric": "hit_at_1", "unit": "NCS-PCF source-task group"},
            {"metric": "hit_at_3", "unit": "NCS-PCF source-task group"},
            {"metric": "hit_at_5", "unit": "NCS-PCF source-task group"},
            {"metric": "precision_at_10", "unit": "NCS-PCF source-task group"},
            {"metric": "mrr", "unit": "NCS-PCF source-task group"},
            {"metric": "ndcg_at_10", "unit": "NCS-PCF source-task group"},
            {"metric": "utility_grade_mean", "unit": "candidate row"},
            {"metric": "explanation_quality_score_mean", "unit": "candidate row"},
        ],
        "active_review_effort": [
            {"metric": "review_seconds", "unit": "review row"},
            {"metric": "corrections_per_hour", "unit": "review arm"},
            {"metric": "high_impact_corrections_per_hour", "unit": "review arm"},
        ],
    }

    evaluation_commands = {
        "preflight_human_returns": "python3 scripts/validate_cape_human_review_returns.py --experiment-dir experiments/cape_kg_eacl_20260627",
        "apply_human_returns": "PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=1 bash scripts/run_cape_human_return_apply.sh",
        "dry_refresh": "PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=0 bash scripts/run_cape_post_annotation_refresh.sh",
        "final_handoff_validation": "python3 scripts/validate_cape_pre_human_handoff.py --experiment-dir experiments/cape_kg_eacl_20260627 --outputs-dir outputs",
        "release_checksum": "sha256sum -c experiments/cape_kg_eacl_20260627/06_release/release_bundle_checksums.sha256",
    }

    claim_gate_policy = {
        "required_gate_ids": [row.get("gate_id") for row in claim_gate.get("gates", []) if row.get("required")],
        "blocked_until_human_returns": [
            "human_gold_chunks",
            "human_gold_items",
            "two annotator agreement",
            "human_gold_scoring_for_proposed_method",
            "mapping_expert_review_for_downstream_claims",
            "crosswalk_expert_review_for_bridge_utility_claims",
            "active_review_effort_timing_for_efficiency_claims",
        ],
        "no_substitution_policy": "Silver/proxy diagnostics, smoke tests, and model-generated labels cannot substitute for adjudicated human-gold or expert-review evidence.",
    }
    current_context = {
        "current_claim_gate_status": claim_gate.get("overall_status"),
        "current_readiness_status": readiness.get("claim_status"),
        "current_pre_human_status": pre_human.get("overall_status"),
        "current_context_files": current_context_files,
    }

    stable = {
        "protocol_version": PROTOCOL_VERSION,
        "metric_definitions": metric_definitions,
        "condition_sets": collect_condition_sets(exp_dir),
        "claim_gate_policy": claim_gate_policy,
        "locked_public_files": public_files,
        "locked_private_input_ids": private_input_ids,
        "evaluation_commands": evaluation_commands,
    }
    stable["protocol_content_sha256"] = canonical_hash(stable)
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "outputs_dir": str(outputs_dir),
        "plan_file": str(plan_file),
        "claim_status": "evaluation_protocol_locked_pending_human_returns",
        **stable,
        "current_context": current_context,
        "locked_private_inputs": private_inputs,
        "outputs": {
            "json": str(release_dir / "evaluation_protocol_lock.json"),
            "markdown": str(release_dir / "evaluation_protocol_lock.md"),
        },
    }
    return payload


def render_report(payload):
    lines = [
        "# CAPE-KG Evaluation Protocol Lock",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Claim status: `{payload['claim_status']}`",
        f"Protocol version: `{payload['protocol_version']}`",
        f"Protocol content SHA256: `{payload['protocol_content_sha256']}`",
        "",
        "This file freezes the evaluation protocol before human returns are imported. It is reproducibility evidence, not a final performance claim.",
        "",
        "## Claim Gate Policy",
        "",
        f"- No-substitution policy: {payload['claim_gate_policy']['no_substitution_policy']}",
        f"- Required gate IDs: `{', '.join(payload['claim_gate_policy']['required_gate_ids'])}`",
        "",
        "## Current Context Snapshot",
        "",
        "These values document the current pre-human state and are intentionally outside the protocol content hash. The pre-human validation value is the previous on-disk validator result at lock-generation time, not an input to the current validation pass.",
        "",
        f"- Current claim gate: `{payload['current_context']['current_claim_gate_status']}`",
        f"- Current readiness: `{payload['current_context']['current_readiness_status']}`",
        f"- Current pre-human validation: `{payload['current_context']['current_pre_human_status']}`",
        "",
        "## Human-Dependent Blockers",
        "",
    ]
    for item in payload["claim_gate_policy"]["blocked_until_human_returns"]:
        lines.append(f"- `{item}`")

    lines += [
        "",
        "## Frozen Condition Sets",
        "",
        "| set | conditions |",
        "|---|---|",
        f"| main | `{', '.join(payload['condition_sets']['main_condition_set'])}` |",
        f"| qwen3_14b | `{', '.join(payload['condition_sets']['model_scaling_conditions']['qwen3_14b'])}` |",
        f"| qwen3_32b_awq | `{', '.join(payload['condition_sets']['model_scaling_conditions']['qwen3_32b_awq'])}` |",
        "",
        "## Metric Definitions",
        "",
    ]
    for group, rows in payload["metric_definitions"].items():
        lines += [
            f"### {group}",
            "",
            "| metric | unit | source |",
            "|---|---|---|",
        ]
        for row in rows:
            lines.append(f"| `{row['metric']}` | {row.get('unit', '')} | {row.get('source', '')} |")
        lines.append("")

    lines += [
        "## Locked Public Files",
        "",
        "These files define the protocol, prompts, evaluators, wrappers, and validators included in the protocol hash.",
        "",
        "| role | exists | bytes | sha256 | path |",
        "|---|---:|---:|---|---|",
    ]
    for row in payload["locked_public_files"]:
        lines.append(f"| {row['role']} | {row['exists']} | {row['bytes']} | `{row['sha256']}` | `{row['path']}` |")

    lines += [
        "",
        "## Current Context Files",
        "",
        "These files summarize the current run state. They are hash-checked for freshness but excluded from the protocol content hash.",
        "",
        "| role | exists | bytes | sha256 | path |",
        "|---|---:|---:|---|---|",
    ]
    for row in payload["current_context"]["current_context_files"]:
        lines.append(f"| {row['role']} | {row['exists']} | {row['bytes']} | `{row['sha256']}` | `{row['path']}` |")

    lines += [
        "",
        "## Locked Private Inputs",
        "",
        "Private inputs are represented by source IDs and hashes only so this protocol lock can remain public-safe. Their source IDs are in the protocol hash; their current hashes are tracked separately for handoff freshness.",
        "",
        "| source_id | exists | bytes | sha256 |",
        "|---|---:|---:|---|",
    ]
    for row in payload["locked_private_inputs"]:
        lines.append(f"| `{row['source_id']}` | {row['exists']} | {row['bytes']} | `{row['sha256']}` |")

    lines += [
        "",
        "## Evaluation Commands",
        "",
        "| step | command |",
        "|---|---|",
    ]
    for step, command in payload["evaluation_commands"].items():
        lines.append(f"| `{step}` | `{command}` |")

    lines += [
        "",
        "## Interpretation",
        "",
        "- Human returns may update metric values, but metric definitions, condition sets, and claim-gate policy should remain stable unless this lock is intentionally regenerated.",
        "- The protocol content hash changes whenever locked protocol files, metric definitions, condition sets, private input IDs, or commands change.",
        "- Current context files may change after regeneration without redefining the protocol itself.",
        "- Final paper claims still require adjudicated human-gold and expert-review evidence.",
        "",
    ]
    return "\n".join(lines)


def run(args):
    payload = build_payload(args.experiment_dir, args.outputs_dir, args.plan_file)
    outputs = payload["outputs"]
    write_json(outputs["json"], payload)
    write_text(outputs["markdown"], render_report(payload))
    print(json.dumps({
        "json": outputs["json"],
        "markdown": outputs["markdown"],
        "claim_status": payload["claim_status"],
        "protocol_content_sha256": payload["protocol_content_sha256"],
        "locked_public_files": len(payload["locked_public_files"]),
        "current_context_files": len(payload["current_context"]["current_context_files"]),
        "locked_private_inputs": len(payload["locked_private_inputs"]),
    }, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--outputs-dir", default=str(DEFAULT_OUTPUTS_DIR))
    parser.add_argument("--plan-file", default=str(DEFAULT_PLAN_FILE))
    run(parser.parse_args())


if __name__ == "__main__":
    main()
