#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build provenance manifest for CAPE-KG experiment artifacts."""

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_OUTPUTS_DIR = Path("outputs")

LLM_RUN_FIELDS = [
    "logical_run",
    "raw_file",
    "valid_file",
    "quality_report",
    "raw_rows",
    "valid_rows",
    "conditions",
    "models",
    "parse_error_rows",
    "repaired_rows",
    "first_generated_at_utc",
    "last_generated_at_utc",
    "raw_sha256",
    "valid_sha256",
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


def file_state(path, role="", required=False, with_hash=True):
    path = Path(path)
    exists = path.exists() and path.is_file()
    row = {
        "path": rel(path),
        "role": role,
        "required": bool(required),
        "exists": exists,
        "bytes": path.stat().st_size if exists else 0,
        "sha256": sha256_file(path) if exists and with_hash else "",
    }
    if exists and path.suffix in {".jsonl", ".csv"}:
        row["records"] = count_records(path)
    return row


def count_records(path):
    path = Path(path)
    if not path.exists():
        return 0
    if path.suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            return max(0, sum(1 for _ in f) - 1)
    with path.open("r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def iter_jsonl(path):
    path = Path(path)
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                yield {"_json_error": True}


def logical_key(path):
    name = Path(path).name
    name = re.sub(r"\.shard\d+\.jsonl$", ".jsonl", name)
    stem = Path(name).stem
    stem = re.sub(r"^\d+_", "", stem)
    for suffix in [
        "_raw",
        "_valid",
        "_quality_report",
        "_silver_metrics",
        "_silver_evaluation_report",
        "_evaluation_report",
    ]:
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
    return stem


def collect_llm_file_groups(exp_dir):
    exp_dir = Path(exp_dir)
    groups = defaultdict(lambda: {"raw": [], "valid": [], "quality": []})
    for path in sorted(exp_dir.glob("*.jsonl")):
        if ".shard" in path.name:
            continue
        name = path.name
        if name.endswith("_raw.jsonl") or name == "45_llm_tool_extractions_raw.jsonl":
            groups[logical_key(path)]["raw"].append(path)
        elif name.endswith("_valid.jsonl") or name == "46_llm_tool_extractions_valid.jsonl":
            groups[logical_key(path)]["valid"].append(path)
    for path in sorted(exp_dir.glob("*quality_report.md")):
        if ".shard" in path.name:
            continue
        groups[logical_key(path)]["quality"].append(path)
    return groups


def summarize_raw(path):
    rows = 0
    parse_errors = 0
    repaired = 0
    conditions = Counter()
    models = Counter()
    timestamps = []
    for row in iter_jsonl(path):
        rows += 1
        condition = row.get("condition")
        model = row.get("model")
        if condition:
            conditions[str(condition)] += 1
        if model:
            models[str(model)] += 1
        if row.get("parse_error"):
            parse_errors += 1
        if row.get("partial_json_repaired"):
            repaired += 1
        if row.get("generated_at_utc"):
            timestamps.append(str(row["generated_at_utc"]))
    return {
        "rows": rows,
        "parse_error_rows": parse_errors,
        "repaired_rows": repaired,
        "conditions": dict(sorted(conditions.items())),
        "models": dict(sorted(models.items())),
        "first_generated_at_utc": min(timestamps) if timestamps else "",
        "last_generated_at_utc": max(timestamps) if timestamps else "",
    }


def summarize_valid(path):
    rows = 0
    conditions = Counter()
    for row in iter_jsonl(path):
        rows += 1
        condition = row.get("condition")
        if condition:
            conditions[str(condition)] += 1
    return {"rows": rows, "conditions": dict(sorted(conditions.items()))}


def collect_llm_runs(exp_dir):
    runs = []
    for key, files in sorted(collect_llm_file_groups(exp_dir).items()):
        raw_path = files["raw"][0] if files["raw"] else None
        valid_path = files["valid"][0] if files["valid"] else None
        quality_path = files["quality"][0] if files["quality"] else None
        if not raw_path and not valid_path:
            continue
        raw_summary = summarize_raw(raw_path) if raw_path else {}
        valid_summary = summarize_valid(valid_path) if valid_path else {}
        condition_counts = Counter()
        condition_counts.update(raw_summary.get("conditions", {}))
        condition_counts.update(valid_summary.get("conditions", {}))
        runs.append(
            {
                "logical_run": key,
                "raw_file": rel(raw_path) if raw_path else "",
                "valid_file": rel(valid_path) if valid_path else "",
                "quality_report": rel(quality_path) if quality_path else "",
                "raw_rows": raw_summary.get("rows", 0),
                "valid_rows": valid_summary.get("rows", 0),
                "conditions": json.dumps(dict(sorted(condition_counts.items())), ensure_ascii=False),
                "models": json.dumps(raw_summary.get("models", {}), ensure_ascii=False),
                "parse_error_rows": raw_summary.get("parse_error_rows", 0),
                "repaired_rows": raw_summary.get("repaired_rows", 0),
                "first_generated_at_utc": raw_summary.get("first_generated_at_utc", ""),
                "last_generated_at_utc": raw_summary.get("last_generated_at_utc", ""),
                "raw_sha256": sha256_file(raw_path) if raw_path else "",
                "valid_sha256": sha256_file(valid_path) if valid_path else "",
            }
        )
    return runs


def collect_prompt_and_schema_files(exp_dir, outputs_dir):
    files = []
    for path in sorted((Path(exp_dir) / "02_schema/prompts").glob("*.txt")):
        files.append(file_state(path, "prompt", required=True))
    for path in [
        Path(exp_dir) / "02_schema/cape_schema.json",
        Path(exp_dir) / "02_schema/cape_shapes.shacl.ttl",
        Path(outputs_dir) / "03_schema/layer2_schema.json",
        Path(outputs_dir) / "03_schema/domain_range_constraints.json",
        Path(outputs_dir) / "03_schema/allowed_predicates.json",
        Path(outputs_dir) / "03_schema/competency_questions.json",
    ]:
        files.append(file_state(path, "schema_or_cq", required=True))
    return files


def collect_source_files(exp_dir, outputs_dir):
    return [
        file_state(Path(outputs_dir) / "00_manifest/data_manifest.json", "data_manifest", required=True),
        file_state(Path(outputs_dir) / "02_ocr/document_structure_reviewed.json", "ocr_structure", required=True),
        file_state(Path(outputs_dir) / "02_ocr/ocr_sentences_clean.jsonl", "evidence_sentence_anchors", required=True),
        file_state(Path(outputs_dir) / "02_ocr/layer2_chunks.jsonl", "layer2_chunks", required=True),
        file_state(Path(outputs_dir) / "01_layer1/layer1_ncs_nodes.jsonl", "layer1_ncs_nodes", required=True),
        file_state(Path(outputs_dir) / "01_layer1/layer1_pcf_nodes.jsonl", "layer1_pcf_nodes", required=True),
        file_state(Path(exp_dir) / "01_data/evaluation_chunks.jsonl", "evaluation_chunks", required=True),
        file_state(Path(exp_dir) / "08_public_benchmarks/public_benchmark_manifest.json", "public_benchmark_manifest", required=False),
    ]


def collect_evaluation_files(exp_dir, outputs_dir):
    exp_dir = Path(exp_dir)
    outputs_dir = Path(outputs_dir)
    paths = [
        exp_dir / "04_evaluation/actual_llm_silver_metrics.json",
        exp_dir / "04_evaluation/qwen3_14b_core_silver_metrics.json",
        exp_dir / "04_evaluation/qwen3_32b_awq_core_silver_metrics.json",
        exp_dir / "06_release/qwen3_model_scaling_report.json",
        exp_dir / "06_release/qwen3_model_scaling_report.md",
        exp_dir / "04_evaluation/structural_evaluation_metrics.json",
        exp_dir / "04_evaluation/evidence_span_granularity_metrics.json",
        outputs_dir / "13_evidence_graph/evidence_graph_projection_summary.json",
        outputs_dir / "13_evidence_graph/evidence_graph_projection_report.md",
        outputs_dir / "13_evidence_graph/evidence_anchor_nodes.jsonl",
        outputs_dir / "13_evidence_graph/evidenced_by_edges.jsonl",
        outputs_dir / "11_neo4j_import/manifest.json",
        outputs_dir / "11_neo4j_import/neo4j_csv_validation_report.json",
        outputs_dir / "11_neo4j_import_flat/manifest.json",
        outputs_dir / "11_neo4j_import_flat/neo4j_csv_validation_report.json",
        outputs_dir / "11_neo4j_import_flat/neo4j_evidence_queries.cypher",
        exp_dir / "06_release/neo4j_evidence_query_pack.json",
        exp_dir / "06_release/neo4j_evidence_query_pack.md",
        exp_dir / "04_evaluation/active_review_efficiency_metrics.json",
        exp_dir / "04_evaluation/active_review_ablation_metrics.json",
        exp_dir / "04_evaluation/active_review_human_effort_metrics.json",
        exp_dir / "04_evaluation/active_review_pool_overlap_summary.json",
        exp_dir / "04_evaluation/active_review_pool_overlap_report.md",
        exp_dir / "06_release/active_review_human_effort_briefing.json",
        exp_dir / "06_release/active_review_human_effort_briefing.md",
        exp_dir / "05_review/active_review_human_effort_briefing.csv",
        exp_dir / "08_public_benchmarks/public_benchmark_manifest.json",
        exp_dir / "08_public_benchmarks/public_benchmark_adapter_report.md",
        exp_dir / "08_public_benchmarks/public_benchmark_crosscheck_summary.json",
        exp_dir / "08_public_benchmarks/public_benchmark_crosscheck_report.md",
        exp_dir / "04_evaluation/ncs_pcf_crosswalk_summary.json",
        exp_dir / "04_evaluation/mapping_downstream_results.csv",
        exp_dir / "04_evaluation/mapping_downstream_arm_diagnostics.csv",
        exp_dir / "04_evaluation/mapping_downstream_arm_rerank_details.csv",
        exp_dir / "04_evaluation/mapping_downstream_arm_rerank_summary.json",
        exp_dir / "04_evaluation/mapping_downstream_report.md",
        exp_dir / "04_evaluation/mapping_expert_metrics.json",
        exp_dir / "06_release/mapping_review_group_briefing.json",
        exp_dir / "06_release/mapping_review_group_briefing.md",
        exp_dir / "05_review/mapping_review_group_briefing_top20.csv",
        exp_dir / "04_evaluation/cq_query_sample_answers.csv",
        exp_dir / "04_evaluation/human_gold_metrics.json",
        exp_dir / "04_evaluation/human_gold_span_iou_metrics.json",
        exp_dir / "04_evaluation/human_gold_span_iou_components.csv",
        exp_dir / "04_evaluation/human_gold_span_iou_report.md",
        exp_dir / "06_release/claim_gate_report.json",
        exp_dir / "06_release/arr_submission_policy_checklist.json",
        exp_dir / "06_release/arr_submission_policy_checklist.md",
        exp_dir / "06_release/anonymized_submission_prep.json",
        exp_dir / "06_release/anonymized_submission_prep.md",
        exp_dir / "06_release/anonymized_submission_risk_scan.csv",
        exp_dir / "06_release/responsible_nlp_checklist_prep.json",
        exp_dir / "06_release/responsible_nlp_checklist_prep.md",
        exp_dir / "06_release/responsible_nlp_checklist_items.csv",
        exp_dir / "06_release/experiment_reproduction_card.json",
        exp_dir / "06_release/experiment_reproduction_card.md",
        exp_dir / "06_release/experiment_reproduction_conditions.csv",
        exp_dir / "06_release/claim_language_guardrails.json",
        exp_dir / "06_release/claim_language_guardrails.md",
        exp_dir / "06_release/reviewer_response_prep.json",
        exp_dir / "06_release/reviewer_response_prep.md",
        exp_dir / "06_release/submission_timeline_action_board.json",
        exp_dir / "06_release/submission_timeline_action_board.md",
        exp_dir / "06_release/claimable_main_table.json",
        exp_dir / "06_release/submission_readiness_audit.json",
        exp_dir / "06_release/submission_readiness_audit.md",
        exp_dir / "06_release/eacl_plan_compliance_matrix.json",
        exp_dir / "06_release/eacl_plan_compliance_matrix.md",
        exp_dir / "06_release/paper_readiness_checklist.json",
        exp_dir / "06_release/paper_readiness_checklist.md",
        exp_dir / "06_release/rq_evidence_matrix.json",
        exp_dir / "06_release/rq_evidence_matrix.md",
        exp_dir / "06_release/reviewer_risk_register.json",
        exp_dir / "06_release/reviewer_risk_register.csv",
        exp_dir / "06_release/reviewer_risk_register.md",
        exp_dir / "06_release/method_novelty_positioning.json",
        exp_dir / "06_release/method_novelty_positioning.md",
        exp_dir / "06_release/cq_query_pack.json",
        exp_dir / "06_release/cq_query_pack.md",
        exp_dir / "06_release/paper_tables.md",
        exp_dir / "06_release/paper_table_blueprint.json",
        exp_dir / "06_release/paper_table_blueprint.md",
        exp_dir / "06_release/paper_section_source_map.json",
        exp_dir / "06_release/paper_section_source_map.md",
        exp_dir / "06_release/eacl_submission_package_manifest.json",
        exp_dir / "06_release/eacl_submission_package_manifest.md",
        exp_dir / "06_release/post_human_scoring_readiness.json",
        exp_dir / "06_release/post_human_scoring_readiness.md",
        exp_dir / "06_release/submission_completion_audit_ko.json",
        exp_dir / "06_release/submission_completion_audit_ko.md",
        exp_dir / "06_release/pre_human_handoff_validation.json",
        exp_dir / "06_release/prompt_node_edge_traceability.json",
        exp_dir / "06_release/prompt_node_edge_traceability.md",
        exp_dir / "06_release/public_reproducibility_manifest.json",
        exp_dir / "06_release/public_reproducibility_manifest.md",
        exp_dir / "06_release/public_reproducibility_manifest.csv",
        exp_dir / "07_reports/README_current_reports_ko.md",
        exp_dir / "07_reports/professor_report_core_essentials_prompt_cq_node_edge_separate_20260629_ko.md",
        exp_dir / "07_reports/professor_report_core_essentials_separate_from_slides_20260629_ko.md",
        exp_dir / "07_reports/professor_report_core_summary_separate_from_slides_sync4_20260629_ko.md",
        exp_dir / "07_reports/professor_report_core_summary_separate_from_slides_latest_20260629_ko.md",
        exp_dir / "07_reports/professor_report_key_summary_separate_from_slides_20260629_ko.md",
        exp_dir / "07_reports/professor_report_core_contents_separate_20260629_ko.md",
        exp_dir / "07_reports/professor_report_key_content_only_prompt_cq_node_edge_20260629_ko.md",
        exp_dir / "07_reports/professor_report_core_summary_current_20260629_ko.md",
        exp_dir / "07_reports/professor_report_slide_contents_current_20260628_ko.md",
        exp_dir / "07_reports/professor_report_core_essentials_prompt_cq_node_edge_20260628_ko.md",
        exp_dir / "07_reports/professor_report_core_separate_summary_prompt_cq_node_edge_20260628_ko.md",
        exp_dir / "07_reports/professor_report_core_brief_prompt_cq_node_edge_20260628_ko.md",
        exp_dir / "07_reports/professor_report_core_briefing_prompt_cq_node_edge_current_20260628_ko.md",
        exp_dir / "07_reports/professor_report_core_summary_current_20260628_ko.md",
        exp_dir / "07_reports/eacl_paper_draft.md",
    ]
    return [file_state(path, "evaluation_or_gate", required=True) for path in paths]


def collect_human_review_files(exp_dir):
    exp_dir = Path(exp_dir)
    handoff_dir = exp_dir / "06_release/human_review_handoff"
    annotation_expansion = read_json(exp_dir / "01_data/gold_annotation/annotation_expansion_manifest.json", {}) or {}
    package_name = annotation_expansion.get("strong_resegmented_package") or "strong_resegmented_342_max18"
    strong_package_dir = exp_dir / "01_data/gold_annotation" / package_name
    paths = [
        exp_dir / "01_data/gold_annotation/annotation_package_manifest.json",
        exp_dir / "01_data/gold_annotation/annotation_manifest_sync_report.json",
        exp_dir / "01_data/gold_annotation/annotation_expansion_manifest.json",
        exp_dir / "01_data/gold_annotation/annotation_expansion_report.md",
        exp_dir / "06_release/annotation_batch_review_preview_summary.json",
        exp_dir / "06_release/annotation_batch_review_preview_summary.md",
        exp_dir / "05_review/annotation_batch_review_preview_summary.csv",
        exp_dir / "06_release/gold_sampling_coverage_report.json",
        exp_dir / "06_release/gold_sampling_coverage_report.md",
        exp_dir / "05_review/gold_sampling_coverage_by_chapter.csv",
        exp_dir / "05_review/gold_sampling_priority100_selected_chunks.csv",
        exp_dir / "06_release/strong_resegmented_review_preview_summary.json",
        exp_dir / "06_release/strong_resegmented_review_preview_summary.md",
        exp_dir / "05_review/strong_resegmented_review_preview_summary.csv",
        exp_dir / f"01_data/gold_annotation/{package_name}/strong_review_preview.csv",
        exp_dir / f"01_data/gold_annotation/{package_name}/strong_review_preview.md",
        exp_dir / "06_release/human_review_return_preflight.json",
        exp_dir / "06_release/strong_review_return_preflight.json",
        exp_dir / "06_release/strong_review_return_preflight.md",
        exp_dir / "06_release/strong_return_apply_last_run.json",
        exp_dir / "06_release/strong_return_apply_last_run.md",
        exp_dir / "06_release/strong_return_apply_refusal_last_run.json",
        exp_dir / "06_release/strong_return_apply_refusal_last_run.md",
        exp_dir / "06_release/human_return_apply_last_run.json",
        exp_dir / "06_release/human_return_apply_last_run.md",
        exp_dir / "06_release/human_return_apply_refusal_last_run.json",
        exp_dir / "06_release/human_return_apply_refusal_last_run.md",
        exp_dir / "06_release/post_annotation_refresh_last_run.json",
        exp_dir / "06_release/human_gate_action_plan.json",
        exp_dir / "06_release/human_gate_action_plan.md",
        exp_dir / "06_release/human_review_master_checklist_ko.json",
        exp_dir / "06_release/human_review_master_checklist_ko.md",
        exp_dir / "05_review/human_review_first_batch_execution_card.json",
        exp_dir / "05_review/human_review_first_batch_execution_card_ko.md",
        exp_dir / "05_review/human_review_role_quickstart_cards.json",
        exp_dir / "05_review/human_review_role_quickstart_cards_ko.md",
        exp_dir / "05_review/human_review_role_quickstart_cards.csv",
        exp_dir / "06_release/human_review_status_dashboard_ko.json",
        exp_dir / "06_release/human_review_status_dashboard_ko.md",
        exp_dir / "06_release/human_review_launch_checklist_ko.json",
        exp_dir / "06_release/human_review_launch_checklist_ko.md",
        exp_dir / "06_release/human_review_packet_integrity.json",
        exp_dir / "06_release/human_review_packet_integrity.md",
        exp_dir / "06_release/active_review_human_effort_briefing.json",
        exp_dir / "06_release/active_review_human_effort_briefing.md",
        exp_dir / "05_review/human_gate_required_returns.csv",
        exp_dir / "05_review/human_review_gate_dependency_matrix.csv",
        exp_dir / "05_review/human_review_master_return_files.csv",
        exp_dir / "05_review/human_review_packet_integrity_issues.csv",
        exp_dir / "05_review/human_review_status_next_actions.csv",
        exp_dir / "05_review/human_review_minimum_gate_launch_tasks.csv",
        exp_dir / "05_review/active_review_human_effort_briefing.csv",
        exp_dir / "01_data/mapping_review/mapping_review_manifest.json",
        exp_dir / "06_release/mapping_review_group_briefing.json",
        exp_dir / "06_release/mapping_review_group_briefing.md",
        exp_dir / "05_review/mapping_review_group_briefing_top20.csv",
        handoff_dir / "human_review_handoff_manifest.json",
        handoff_dir / "human_review_handoff_report.md",
        handoff_dir / "human_review_handoff_checksums.sha256",
        handoff_dir / "README_strong_resegmented_review_ko.md",
        handoff_dir / "strong_resegmented_review_manifest.json",
        strong_package_dir / "annotator_A.jsonl",
        strong_package_dir / "annotator_B.jsonl",
        strong_package_dir / "adjudication.jsonl",
        strong_package_dir / "adjudication_draft.jsonl",
        strong_package_dir / "tracking_sheet.csv",
    ]
    rows = [file_state(path, "human_review_handoff", required=True) for path in paths]

    handoff_manifest = read_json(handoff_dir / "human_review_handoff_manifest.json", {}) or {}
    for bundle_name, bundle in sorted((handoff_manifest.get("bundles") or {}).items()):
        bundle_path = bundle.get("path")
        if bundle_path:
            rows.append(file_state(Path(bundle_path), f"human_review_bundle:{bundle_name}", required=True))
    return rows


def collect_release_files(exp_dir):
    exp_dir = Path(exp_dir)
    paths = [
        exp_dir / "06_release/reproducibility_manifest.json",
        exp_dir / "06_release/public_reproducibility_manifest.json",
        exp_dir / "06_release/public_reproducibility_manifest.md",
        exp_dir / "06_release/public_reproducibility_manifest.csv",
        exp_dir / "06_release/anonymized_submission_prep.json",
        exp_dir / "06_release/anonymized_submission_prep.md",
        exp_dir / "06_release/anonymized_submission_risk_scan.csv",
        exp_dir / "06_release/responsible_nlp_checklist_prep.json",
        exp_dir / "06_release/responsible_nlp_checklist_prep.md",
        exp_dir / "06_release/responsible_nlp_checklist_items.csv",
        exp_dir / "06_release/experiment_reproduction_card.json",
        exp_dir / "06_release/experiment_reproduction_card.md",
        exp_dir / "06_release/experiment_reproduction_conditions.csv",
        exp_dir / "06_release/data_release_ethics_statement.md",
        exp_dir / "06_release/external_resource_license_report.json",
        exp_dir / "06_release/external_resource_license_report.csv",
        exp_dir / "06_release/external_resource_license_report.md",
        exp_dir / "06_release/evaluation_protocol_lock.json",
        exp_dir / "06_release/evaluation_protocol_lock.md",
        exp_dir / "06_release/latest_release_bundle_index.json",
        exp_dir / "06_release/latest_release_bundle_index.md",
        exp_dir / "06_release/annotation_batch_review_preview_summary.json",
        exp_dir / "06_release/annotation_batch_review_preview_summary.md",
        exp_dir / "06_release/gold_sampling_coverage_report.json",
        exp_dir / "06_release/gold_sampling_coverage_report.md",
        exp_dir / "06_release/strong_resegmented_review_preview_summary.json",
        exp_dir / "06_release/strong_resegmented_review_preview_summary.md",
        exp_dir / "06_release/human_review_status_dashboard_ko.json",
        exp_dir / "06_release/human_review_status_dashboard_ko.md",
        exp_dir / "06_release/human_review_launch_checklist_ko.json",
        exp_dir / "06_release/human_review_launch_checklist_ko.md",
        exp_dir / "06_release/release_bundle_safety_report.md",
        exp_dir / "06_release/public_external_release_review_queue.csv",
        exp_dir / "06_release/public_external_release_review_queue.md",
        exp_dir / "06_release/public_synthetic_examples/README.md",
        exp_dir / "06_release/public_synthetic_examples/synthetic_evaluation_summary.json",
    ]
    return [file_state(path, "release_or_reproducibility", required=True) for path in paths]


def missing_required(groups):
    missing = []
    for group_name, rows in groups.items():
        for row in rows:
            if row.get("required") and not row.get("exists"):
                missing.append({"group": group_name, "path": row.get("path"), "role": row.get("role")})
    return missing


def build_payload(exp_dir, outputs_dir):
    exp_dir = Path(exp_dir)
    outputs_dir = Path(outputs_dir)
    llm_runs = collect_llm_runs(exp_dir)
    groups = {
        "source_files": collect_source_files(exp_dir, outputs_dir),
        "prompt_and_schema_files": collect_prompt_and_schema_files(exp_dir, outputs_dir),
        "evaluation_files": collect_evaluation_files(exp_dir, outputs_dir),
        "human_review_files": collect_human_review_files(exp_dir),
        "release_files": collect_release_files(exp_dir),
    }
    missing = missing_required(groups)
    llm_runs_with_raw = sum(1 for row in llm_runs if row.get("raw_file"))
    llm_runs_with_valid = sum(1 for row in llm_runs if row.get("valid_file"))
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "outputs_dir": str(outputs_dir),
        "claim_status": "provenance_manifest_ready_not_human_gold_evidence" if not missing else "provenance_manifest_incomplete",
        "summary": {
            "source_file_count": len(groups["source_files"]),
            "prompt_and_schema_file_count": len(groups["prompt_and_schema_files"]),
            "evaluation_file_count": len(groups["evaluation_files"]),
            "human_review_file_count": len(groups["human_review_files"]),
            "release_file_count": len(groups["release_files"]),
            "llm_run_count": len(llm_runs),
            "llm_runs_with_raw": llm_runs_with_raw,
            "llm_runs_with_valid": llm_runs_with_valid,
            "missing_required_count": len(missing),
        },
        "missing_required": missing,
        **groups,
        "llm_runs": llm_runs,
        "outputs": {
            "manifest_json": str(exp_dir / "06_release/provenance_manifest.json"),
            "manifest_md": str(exp_dir / "06_release/provenance_manifest.md"),
            "llm_run_index_csv": str(exp_dir / "04_evaluation/provenance_llm_run_index.csv"),
        },
    }


def render_report(payload):
    summary = payload["summary"]
    lines = [
        "# CAPE-KG Provenance Manifest",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Claim status: `{payload['claim_status']}`",
        "",
        "This manifest records file-level provenance for source artifacts, prompts, schemas, LLM runs, evaluation outputs, human-review handoffs, and release bundles. It is reproducibility evidence, not human-gold performance evidence.",
        "",
        "## Summary",
        "",
        "| Item | Value |",
        "|---|---:|",
    ]
    for key, value in summary.items():
        lines.append(f"| {key} | {value} |")
    if payload["missing_required"]:
        lines += ["", "## Missing Required Files", ""]
        for row in payload["missing_required"]:
            lines.append(f"- {row['group']}: `{row['path']}` ({row['role']})")
    lines += [
        "",
        "## LLM Run Index",
        "",
        "| logical_run | raw_rows | valid_rows | parse_errors | repaired | raw_file | valid_file |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    for row in payload["llm_runs"]:
        lines.append(
            f"| {row['logical_run']} | {row['raw_rows']} | {row['valid_rows']} | {row['parse_error_rows']} | "
            f"{row['repaired_rows']} | `{row['raw_file']}` | `{row['valid_file']}` |"
        )
    lines += ["", "## File Groups", ""]
    for group_name in [
        "source_files",
        "prompt_and_schema_files",
        "evaluation_files",
        "human_review_files",
        "release_files",
    ]:
        lines += [
            f"### {group_name}",
            "",
            "| role | exists | records | bytes | sha256 | path |",
            "|---|---:|---:|---:|---|---|",
        ]
        for row in payload[group_name]:
            lines.append(
                f"| {row['role']} | {row['exists']} | {row.get('records', '')} | {row['bytes']} | "
                f"`{row['sha256']}` | `{row['path']}` |"
            )
        lines.append("")
    lines += [
        "## Interpretation",
        "",
        "- Use `provenance_llm_run_index.csv` to trace LLM raw outputs, validated outputs, quality reports, models, conditions, and parse-repair counts.",
        "- Use this manifest with release checksums to reproduce the exact pre-human experiment package.",
        "- Human-gold labels, IAA, adjudication, expert mapping decisions, and active-review effort remain external human-return evidence until reviewed files are imported.",
        "",
    ]
    return "\n".join(lines)


def run(args):
    payload = build_payload(args.experiment_dir, args.outputs_dir)
    outputs = payload["outputs"]
    write_json(outputs["manifest_json"], payload)
    write_text(outputs["manifest_md"], render_report(payload))
    write_csv(outputs["llm_run_index_csv"], payload["llm_runs"], LLM_RUN_FIELDS)
    print(json.dumps({
        "manifest_json": outputs["manifest_json"],
        "manifest_md": outputs["manifest_md"],
        "llm_run_index_csv": outputs["llm_run_index_csv"],
        "claim_status": payload["claim_status"],
        "missing_required_count": payload["summary"]["missing_required_count"],
        "llm_run_count": payload["summary"]["llm_run_count"],
    }, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--outputs-dir", default=str(DEFAULT_OUTPUTS_DIR))
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
