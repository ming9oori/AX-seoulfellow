#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit CAPE-KG EACL plan requirements against current experiment artifacts."""

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_PLAN = Path("AX_EACL_submission_review_revised_plan.md")
FULL_EVAL_ROWS = 120
REQUIRED_ERROR_ANALYSIS_SECTIONS = [
    "## Claim Scope",
    "## Actual LLM Silver/Proxy Diagnostics",
    "## Proxy Scaffold Error Summary",
    "## Error Taxonomy",
    "## Human-Gold Follow-Up",
]


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path):
    path = Path(path)
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def file_evidence(path):
    path = Path(path)
    if path.exists() and path.stat().st_size > 0:
        return {"path": str(path), "exists": True, "bytes": path.stat().st_size}
    return {"path": str(path), "exists": False, "bytes": 0}


def error_analysis_status(exp_dir):
    md_path = Path(exp_dir) / "07_reports/error_analysis.md"
    json_path = Path(exp_dir) / "07_reports/error_analysis.json"
    evidence = {
        "markdown": file_evidence(md_path),
        "json": file_evidence(json_path),
        "required_sections": REQUIRED_ERROR_ANALYSIS_SECTIONS,
        "missing_sections": REQUIRED_ERROR_ANALYSIS_SECTIONS[:],
        "taxonomy_family_count": 0,
        "ready_for_minimum_accept": False,
    }
    if not md_path.exists() or not json_path.exists():
        return False, evidence
    text = md_path.read_text(encoding="utf-8")
    missing_sections = [section for section in REQUIRED_ERROR_ANALYSIS_SECTIONS if section not in text]
    evidence["missing_sections"] = missing_sections
    payload = read_json(json_path, {}) or {}
    summary = payload.get("summary") or {}
    taxonomy = payload.get("error_taxonomy") or []
    evidence["taxonomy_family_count"] = len(taxonomy)
    evidence["ready_for_minimum_accept"] = bool(summary.get("ready_for_minimum_accept"))
    evidence["claim_scope"] = summary.get("claim_scope")
    ok = (
        md_path.stat().st_size >= 3000
        and json_path.stat().st_size >= 1000
        and not missing_sections
        and len(taxonomy) >= 6
        and bool(summary.get("ready_for_minimum_accept"))
    )
    return ok, evidence


def count_jsonl(path):
    return len(read_jsonl(path))


def condition_max_rows(exp_dir):
    max_counts = defaultdict(int)
    parse_counts = defaultdict(int)
    for raw_path in sorted(exp_dir.glob("48_*_raw.jsonl")):
        per_run = Counter()
        per_run_parse = Counter()
        for row in read_jsonl(raw_path):
            condition = row.get("condition") or "unknown"
            per_run[condition] += 1
            if row.get("parse_error") or row.get("error"):
                per_run_parse[condition] += 1
        for condition, rows in per_run.items():
            if rows > max_counts[condition]:
                max_counts[condition] = rows
                parse_counts[condition] = per_run_parse[condition]
    return dict(max_counts), dict(parse_counts)


def iaa_status(exp_dir):
    summaries = []
    for path in sorted((exp_dir / "01_data/gold_annotation").glob("iaa*/iaa_summary.json")):
        payload = read_json(path, {}) or {}
        payload["path"] = str(path)
        summaries.append(payload)
    max_completed = max([int(row.get("completed_pair_chunks") or 0) for row in summaries] or [0])
    computed_100 = any(row.get("status") == "computed" and int(row.get("completed_pair_chunks") or 0) >= 100 for row in summaries)
    return summaries, max_completed, computed_100


def public_eval_counts(exp_dir):
    public_dir = exp_dir / "08_public_benchmarks"
    crosscheck_path = public_dir / "public_benchmark_crosscheck_summary.json"
    crosscheck = read_json(crosscheck_path, {}) or {}
    crosscheck_summary = crosscheck.get("summary") or {}
    if crosscheck_summary:
        max_single_paged = int(crosscheck_summary.get("max_single_run_paged_items") or 0)
        max_single_text2kg = int(crosscheck_summary.get("max_single_run_text2kg_items") or 0)
        runs = crosscheck.get("runs") or []
        return runs, max_single_paged, max_single_text2kg, max_single_paged, max_single_text2kg

    summaries = []
    for path in sorted(public_dir.glob("*_summary.json")):
        payload = read_json(path, {}) or {}
        if payload.get("is_shard"):
            continue
        if "paged_items" in payload or "text2kg_items" in payload:
            payload["_path"] = str(path)
            summaries.append(payload)
    paged = sum(int(row.get("paged_items") or 0) for row in summaries)
    text2kg = sum(int(row.get("text2kg_items") or 0) for row in summaries)
    max_single_paged = max([int(row.get("paged_items") or 0) for row in summaries] or [0])
    max_single_text2kg = max([int(row.get("text2kg_items") or 0) for row in summaries] or [0])
    return summaries, paged, text2kg, max_single_paged, max_single_text2kg


def mapping_status(exp_dir):
    metrics = read_json(exp_dir / "04_evaluation/mapping_expert_metrics.json", {}) or {}
    rows = metrics.get("metrics") or []
    pending = sum(int(row.get("pending_rows") or 0) for row in rows if isinstance(row.get("pending_rows"), int))
    complete_groups = sum(int(row.get("complete_source_groups") or 0) for row in rows)
    fully_reviewed = bool(rows) and all(row.get("claim_status") == "expert_review_evaluated" for row in rows)
    return rows, pending, complete_groups, fully_reviewed


def item(item_id, category, requirement, status, claimable, evidence, next_step):
    return {
        "id": item_id,
        "category": category,
        "requirement": requirement,
        "status": status,
        "claimable": bool(claimable),
        "evidence": evidence,
        "next_step": next_step,
    }


def done_or(ok, done, pending):
    return done if ok else pending


def audit(exp_dir, plan_file):
    exp_dir = Path(exp_dir)
    workspace = exp_dir.parent.parent if exp_dir.parent.name == "experiments" else Path(".")
    max_rows, parse_rows = condition_max_rows(exp_dir)
    eval_chunks = count_jsonl(exp_dir / "01_data/evaluation_chunks.jsonl")
    human_summary = read_json(exp_dir / "04_evaluation/human_gold_validation_summary.json", {}) or {}
    completed_chunks = int(human_summary.get("completed_adjudicated_chunks") or 0)
    gold_items = int(human_summary.get("gold_item_count_for_readiness") or 0)
    validation_errors = int(human_summary.get("validation_error_count") or 0)
    iaa_summaries, iaa_completed, iaa_ready = iaa_status(exp_dir)
    public_summaries, paged_items, text2kg_items, max_single_paged, max_single_text2kg = public_eval_counts(exp_dir)
    mapping_rows, pending_mapping, mapping_groups, mapping_ready = mapping_status(exp_dir)
    human_metrics = read_json(exp_dir / "04_evaluation/human_gold_metrics.json", {}) or {}
    human_scored = {row.get("condition") for row in human_metrics.get("metrics", []) if row.get("claim_status") == "human_gold_scored"}
    synthetic_summary_path = exp_dir / "06_release/public_synthetic_examples/synthetic_evaluation_summary.json"
    synthetic_summary = read_json(synthetic_summary_path, {}) or {}
    synthetic_ready = (
        synthetic_summary_path.exists()
        and int(synthetic_summary.get("synthetic_chunk_count") or 0) >= 2
        and int(synthetic_summary.get("validation_error_count") or 0) == 0
        and synthetic_summary.get("source_text_policy") == "synthetic_only_no_source_corpus_text"
    )
    method_coverage_path = exp_dir / "06_release/method_module_coverage.json"
    method_coverage_report = exp_dir / "06_release/method_module_coverage.md"
    method_coverage = read_json(method_coverage_path, {}) or {}
    method_summary = method_coverage.get("summary") or {}
    method_missing_count = int(method_summary.get("missing_required_artifact_count") or 0)
    method_module_count = int(method_summary.get("module_count") or 0)
    method_present_count = int(method_summary.get("modules_with_required_artifacts") or 0)
    method_all_artifacts_present = method_module_count >= 11 and method_missing_count == 0
    error_analysis_ready, error_analysis_evidence = error_analysis_status(exp_dir)
    annotation_expansion = read_json(exp_dir / "01_data/gold_annotation/annotation_expansion_manifest.json", {}) or {}
    strong_resegmented_count = int(annotation_expansion.get("strong_resegmented_chunk_count") or 0)
    strong_resegmented_package = annotation_expansion.get("strong_resegmented_package") or "strong_resegmented_package"
    gold_sampling = read_json(exp_dir / "06_release/gold_sampling_coverage_report.json", {}) or {}
    sampling_policy = gold_sampling.get("selection_policy") or {}
    sampling_coverage = gold_sampling.get("coverage_summary") or {}
    priority_100_selected = int(sampling_policy.get("selected_chunk_count") or 0)
    priority_100_candidate_edges = int(sampling_coverage.get("priority_100_candidate_edges") or 0)
    full_120_candidate_edges = int(sampling_coverage.get("full_120_candidate_edges") or 0)
    priority_100_candidate_coverage = float(
        sampling_coverage.get("priority_100_candidate_edge_coverage_of_full120") or 0.0
    )
    priority_100_active_coverage = float(
        sampling_coverage.get("priority_100_active_review_chunk_coverage_of_full120") or 0.0
    )
    priority_100_high_impact_coverage = float(
        sampling_coverage.get("priority_100_high_impact_chunk_coverage_of_full120") or 0.0
    )
    gold_sampling_ready = (
        priority_100_selected >= 100
        and full_120_candidate_edges > 0
        and priority_100_candidate_coverage >= 0.90
        and priority_100_active_coverage >= 0.90
        and priority_100_high_impact_coverage >= 0.90
    )
    gold_sampling_note = (
        "No additional automatic step required; priority-100 sampling covers "
        f"{priority_100_candidate_edges}/{full_120_candidate_edges} full-120 candidate edges "
        f"({priority_100_candidate_coverage:.4f}), active-review coverage={priority_100_active_coverage:.4f}, "
        f"high-impact coverage={priority_100_high_impact_coverage:.4f}. Human annotation/adjudication still required."
        if gold_sampling_ready
        else "Regenerate gold_sampling_coverage_report and verify the priority-100 selected subset before launching human review."
    )
    if strong_resegmented_count >= 300:
        strong_gold_next_step = (
            f"Use `{strong_resegmented_package}` for optional 300+ two-annotator review and adjudication; "
            "do not claim 300+ adjudicated chunks until reviewed returns are imported."
        )
    else:
        strong_gold_next_step = (
            "Review the optional all-available chunk expansion package, or add/split source data to reach "
            "the 300-500 chunk strong target."
        )

    baseline_ready = all(max_rows.get(cond, 0) >= FULL_EVAL_ROWS for cond in ["B0_plain_llm", "B1_predicate_constrained", "B2_current_project"])
    proposed_ready = max_rows.get("P_cape_kg_actual", 0) >= FULL_EVAL_ROWS
    ablations = sorted([cond for cond, rows in max_rows.items() if cond.startswith("P_minus_") and rows >= FULL_EVAL_ROWS])
    full_public_subset = paged_items > 0 or text2kg_items > 0
    strong_public_cross = max_single_paged >= 100 and max_single_text2kg >= 200
    sac_style_ready = max_rows.get("B6_sac_kg_verifier_pruner", 0) >= FULL_EVAL_ROWS and (
        exp_dir / "50_sac_kg_verifier_pruner_baseline_quality_report.md"
    ).exists()

    release_files = [
        exp_dir / "02_schema/cape_schema.json",
        exp_dir / "02_schema/competency_questions.json",
        exp_dir / "02_schema/prompts/P_cape_kg.txt",
        exp_dir / "04_evaluation/actual_llm_silver_metrics.json",
        exp_dir / "04_evaluation/evidence_span_granularity_metrics.json",
        exp_dir / "04_evaluation/evidence_span_granularity_report.md",
        exp_dir / "04_evaluation/statistical_analysis_metrics.json",
        exp_dir / "07_reports/error_analysis.md",
        exp_dir / "07_reports/error_analysis.json",
        exp_dir / "01_data/gold_annotation/annotation_manifest_sync_report.json",
        exp_dir / "01_data/gold_annotation/annotation_manifest_sync_report.md",
        exp_dir / "01_data/gold_annotation/annotation_expansion_manifest.json",
        exp_dir / "01_data/gold_annotation/annotation_expansion_report.md",
        exp_dir / "05_review/human_gold_annotation_priority_queue.csv",
        exp_dir / "05_review/human_gold_next_100_worklist.csv",
        exp_dir / "05_review/human_gold_batches/full_120_batch_assignment_overview.csv",
        exp_dir / "06_release/gold_sampling_coverage_report.json",
        exp_dir / "06_release/gold_sampling_coverage_report.md",
        exp_dir / "05_review/gold_sampling_priority100_selected_chunks.csv",
        exp_dir / "05_review/gold_sampling_coverage_by_chapter.csv",
        exp_dir / "05_review/active_review_human_effort_template.csv",
        exp_dir / "06_release/active_review_human_effort_plan.json",
        exp_dir / "06_release/active_review_human_effort_plan.md",
        exp_dir / "04_evaluation/active_review_human_effort_metrics.json",
        exp_dir / "04_evaluation/active_review_human_effort_report.md",
        exp_dir / "04_evaluation/active_review_pool_overlap_summary.json",
        exp_dir / "04_evaluation/active_review_pool_overlap_report.md",
        exp_dir / "04_evaluation/active_review_ablation_metrics.json",
        exp_dir / "04_evaluation/active_review_ablation_report.md",
        exp_dir / "08_public_benchmarks/public_benchmark_crosscheck_summary.json",
        exp_dir / "08_public_benchmarks/public_benchmark_crosscheck_report.md",
        exp_dir / "05_review/mapping_review_priority_queue.csv",
        exp_dir / "05_review/mapping_review_next_20_groups.csv",
        exp_dir / "05_review/mapping_review_next_60_rows.csv",
        exp_dir / "06_release/annotation_progress_summary.json",
        exp_dir / "06_release/annotation_progress_report.md",
        exp_dir / "06_release/annotation_batch_assignment_summary.json",
        exp_dir / "06_release/annotation_batch_assignment_report.md",
        exp_dir / "06_release/annotation_qc_summary.json",
        exp_dir / "06_release/annotation_qc_report.md",
        exp_dir / "05_review/annotation_qc_issues.csv",
        exp_dir / "05_review/annotation_completion_gate_worklist.csv",
        exp_dir / "06_release/human_gate_action_plan.json",
        exp_dir / "06_release/human_gate_action_plan.md",
        exp_dir / "05_review/human_gate_required_returns.csv",
        exp_dir / "06_release/mapping_review_progress_summary.json",
        exp_dir / "06_release/mapping_review_progress_report.md",
        exp_dir / "06_release/reproducibility_manifest.json",
        exp_dir / "06_release/limitations.md",
        exp_dir / "06_release/public_synthetic_examples/README.md",
        exp_dir / "06_release/public_synthetic_examples/synthetic_chunks.jsonl",
        exp_dir / "06_release/public_synthetic_examples/synthetic_gold.jsonl",
        exp_dir / "06_release/public_synthetic_examples/synthetic_predictions.jsonl",
        exp_dir / "06_release/public_synthetic_examples/synthetic_evaluation_summary.json",
        exp_dir / "06_release/model_selection_and_scaling_plan.md",
        exp_dir / "06_release/qwen3_32b_awq_readiness.json",
        exp_dir / "06_release/qwen3_32b_awq_readiness.md",
        exp_dir / "06_release/strict_json_diagnostics.json",
        exp_dir / "06_release/strict_json_diagnostics.md",
        exp_dir / "05_review/strict_json_reprompt_priority.csv",
        exp_dir / "05_review/strict_json_gate_selected_error_rows.csv",
        exp_dir / "02_schema/prompts/strict_json_contract.txt",
        exp_dir / "06_release/method_module_coverage.json",
        exp_dir / "06_release/method_module_coverage.md",
        exp_dir / "06_release/release_bundle_manifest.json",
        exp_dir / "06_release/release_bundle_checksums.sha256",
        exp_dir / "06_release/release_bundle_safety_report.md",
    ]
    release_missing = [str(path) for path in release_files if not path.exists() or path.stat().st_size == 0]

    items = [
        item(
            "min.gold_chunks",
            "minimum_accept",
            "100+ adjudicated gold chunks",
            "pass" if completed_chunks >= 100 and validation_errors == 0 else "pending_human",
            completed_chunks >= 100 and validation_errors == 0,
            [file_evidence(exp_dir / "04_evaluation/human_gold_validation_summary.json"), {"completed_chunks": completed_chunks, "validation_errors": validation_errors}],
            "Complete two-annotator labeling and adjudication for at least 100 chunks.",
        ),
        item(
            "min.gold_items",
            "minimum_accept",
            "500+ adjudicated gold node/edge/evidence items",
            "pass" if gold_items >= 500 and validation_errors == 0 else "pending_human",
            gold_items >= 500 and validation_errors == 0,
            [file_evidence(exp_dir / "04_evaluation/human_gold_validation_summary.json"), {"gold_items": gold_items}],
            "Adjudicate enough nodes, edges, and evidence anchors to reach 500 gold items.",
        ),
        item(
            "min.iaa",
            "minimum_accept",
            "2+ annotators and agreement for 100+ chunks",
            "pass" if iaa_ready else "pending_human",
            iaa_ready,
            [
                file_evidence(exp_dir / "04_evaluation/human_gold_validation_summary.json"),
                *[file_evidence(row.get("path", "")) for row in iaa_summaries],
                {"iaa_summary_count": len(iaa_summaries), "max_completed_pair_chunks": iaa_completed},
            ],
            "Import completed annotator A/B files and recompute IAA.",
        ),
        item(
            "min.gold_sampling_ready",
            "minimum_accept",
            "Priority-100 gold subset sampling ready",
            "pass" if gold_sampling_ready else "fail",
            gold_sampling_ready,
            [
                file_evidence(exp_dir / "06_release/gold_sampling_coverage_report.json"),
                file_evidence(exp_dir / "06_release/gold_sampling_coverage_report.md"),
                file_evidence(exp_dir / "05_review/gold_sampling_priority100_selected_chunks.csv"),
                file_evidence(exp_dir / "05_review/gold_sampling_coverage_by_chapter.csv"),
                {
                    "selected_chunks": priority_100_selected,
                    "priority_100_candidate_edges": priority_100_candidate_edges,
                    "full_120_candidate_edges": full_120_candidate_edges,
                    "candidate_edge_coverage": priority_100_candidate_coverage,
                    "active_review_chunk_coverage": priority_100_active_coverage,
                    "high_impact_chunk_coverage": priority_100_high_impact_coverage,
                    "claim_status": gold_sampling.get("claim_status"),
                },
            ],
            gold_sampling_note,
        ),
        item(
            "min.baselines",
            "minimum_accept",
            "B0/B1/B2 actual LLM baselines completed",
            "pass" if baseline_ready else "fail",
            baseline_ready,
            [
                file_evidence(exp_dir / "04_evaluation/actual_llm_silver_metrics.json"),
                file_evidence(exp_dir / "49_qwen3_8b_strict_json_1200_full_valid.jsonl"),
                {"condition_max_rows": {k: max_rows.get(k, 0) for k in ["B0_plain_llm", "B1_predicate_constrained", "B2_current_project"]}},
            ],
            done_or(
                baseline_ready,
                "No additional automatic step required; keep baseline artifacts synchronized.",
                "Rerun missing baseline shards until each condition reaches 120 rows.",
            ),
        ),
        item(
            "min.proposed",
            "minimum_accept",
            "CAPE-KG proposed result completed and scored",
            "pass" if "P_cape_kg_actual" in human_scored else "partial" if proposed_ready else "fail",
            "P_cape_kg_actual" in human_scored,
            [
                file_evidence(exp_dir / "04_evaluation/human_gold_metrics.json"),
                file_evidence(exp_dir / "04_evaluation/human_gold_metrics.csv"),
                file_evidence(exp_dir / "04_evaluation/human_gold_validation_summary.json"),
                file_evidence(exp_dir / "49_qwen3_8b_strict_json_1200_full_valid.jsonl"),
                {
                    "P_cape_kg_actual_rows": max_rows.get("P_cape_kg_actual", 0),
                    "human_gold_scored_conditions": sorted(human_scored),
                },
            ],
            "Score P_cape_kg_actual against adjudicated human gold after gold completion.",
        ),
        item(
            "min.ablations",
            "minimum_accept",
            "3+ actual ablations completed",
            "pass" if len(ablations) >= 3 else "fail",
            len(ablations) >= 3,
            [
                file_evidence(exp_dir / "04_evaluation/actual_llm_silver_metrics.json"),
                file_evidence(exp_dir / "49_qwen3_8b_cape_ablation_120_valid.jsonl"),
                {"full_ablation_conditions": ablations},
            ],
            done_or(
                len(ablations) >= 3,
                "No additional automatic step required; ablation coverage satisfies the minimum gate.",
                "Run additional ablation conditions if fewer than three full conditions exist.",
            ),
        ),
        item(
            "min.error_analysis",
            "minimum_accept",
            "Structured error analysis table and taxonomy",
            "pass" if error_analysis_ready else "fail",
            error_analysis_ready,
            [error_analysis_evidence],
            done_or(
                error_analysis_ready,
                "No additional automatic step required; update only if new diagnostics change.",
                "Generate or update structured error_analysis.md/json with claim scope, diagnostics, taxonomy, and human-gold follow-up.",
            ),
        ),
        item(
            "min.public_subset",
            "minimum_accept",
            "Public benchmark or public subset experiment",
            "pass" if full_public_subset else "fail",
            full_public_subset,
            [
                file_evidence(exp_dir / "08_public_benchmarks/public_benchmark_crosscheck_summary.json"),
                {"paged_items": paged_items, "text2kg_items": text2kg_items, "summary_count": len(public_summaries)},
            ],
            done_or(
                full_public_subset,
                "No additional automatic step required; public subset evidence is present.",
                "Run model evaluation on PAGED/Text2KGBench subsets.",
            ),
        ),
        item(
            "min.release_plan",
            "minimum_accept",
            "Code, prompt, schema, and reproducibility release package",
            "pass" if not release_missing else "fail",
            not release_missing,
            [file_evidence(path) for path in release_files],
            done_or(
                not release_missing,
                "No additional automatic step required; regenerate only after source artifacts change.",
                "Regenerate missing release package artifacts.",
            ),
        ),
        item(
            "min.limitations",
            "minimum_accept",
            "Limitations section",
            "pass" if (exp_dir / "06_release/limitations.md").exists() else "fail",
            (exp_dir / "06_release/limitations.md").exists(),
            [file_evidence(exp_dir / "06_release/limitations.md")],
            done_or(
                (exp_dir / "06_release/limitations.md").exists(),
                "No additional automatic step required; keep limitations synchronized with future human results.",
                "Create limitations.md with current human-gold and model limits.",
            ),
        ),
        item(
            "min.public_synthetic_examples",
            "minimum_accept",
            "Public-safe synthetic examples for reproducibility mitigation",
            "pass" if synthetic_ready else "fail",
            synthetic_ready,
            [
                file_evidence(exp_dir / "06_release/public_synthetic_examples/README.md"),
                file_evidence(synthetic_summary_path),
                {
                    "synthetic_chunk_count": synthetic_summary.get("synthetic_chunk_count"),
                    "validation_error_count": synthetic_summary.get("validation_error_count"),
                    "source_text_policy": synthetic_summary.get("source_text_policy"),
                },
            ],
            done_or(
                synthetic_ready,
                "No additional automatic step required; synthetic public-safe examples are ready.",
                "Generate public-safe synthetic examples that demonstrate JSONL formats without source-corpus text.",
            ),
        ),
        item(
            "strong.gold_chunks",
            "strong_accept",
            "300-500 adjudicated gold chunks",
            "pending_human",
            False,
            [
                {"completed_chunks": completed_chunks, "target_min": 300},
                {
                    "all_available_chunks": annotation_expansion.get("all_available_chunk_count"),
                    "strong_resegmented_package": strong_resegmented_package,
                    "strong_resegmented_chunks": annotation_expansion.get("strong_resegmented_chunk_count"),
                    "strong_300_chunk_gap_after_resegmentation": annotation_expansion.get("strong_300_chunk_gap_after_resegmentation"),
                    "strong_resegmented_claim_status": annotation_expansion.get("strong_resegmented_claim_status"),
                },
                file_evidence(exp_dir / "01_data/gold_annotation/annotation_expansion_manifest.json"),
                file_evidence(exp_dir / "01_data/gold_annotation/annotation_expansion_report.md"),
            ],
            strong_gold_next_step,
        ),
        item(
            "strong.gold_items",
            "strong_accept",
            "1,500+ adjudicated gold edge/evidence items",
            "pass" if gold_items >= 1500 and validation_errors == 0 else "pending_human",
            gold_items >= 1500 and validation_errors == 0,
            [
                file_evidence(exp_dir / "04_evaluation/human_gold_validation_summary.json"),
                {
                    "gold_items": gold_items,
                    "target_min": 1500,
                    "validation_errors": validation_errors,
                    "strong_resegmented_package": strong_resegmented_package,
                    "strong_resegmented_chunks": annotation_expansion.get("strong_resegmented_chunk_count"),
                },
                file_evidence(exp_dir / "01_data/gold_annotation/annotation_expansion_manifest.json"),
            ],
            "Complete optional 300+ two-annotator review and adjudication until at least 1,500 gold edge/evidence items are available.",
        ),
        item(
            "strong.public_cross",
            "strong_accept",
            "PAGED/Text2KGBench cross experiment",
            "pass" if strong_public_cross else ("partial" if full_public_subset else "fail"),
            strong_public_cross,
            [
                file_evidence(exp_dir / "08_public_benchmarks/public_benchmark_crosscheck_summary.json"),
                {
                "paged_items_total": paged_items,
                "text2kg_items_total": text2kg_items,
                "max_single_run_paged_items": max_single_paged,
                "max_single_run_text2kg_items": max_single_text2kg,
                },
            ],
            done_or(
                strong_public_cross,
                "No additional automatic step required; cross-check includes PAGED >= 100 and Text2KG >= 200 in a single run.",
                "Run at least one merged public adapter evaluation with PAGED >= 100 and Text2KG >= 200.",
            ),
        ),
        item(
            "strong.edc_taxonomy_baselines",
            "strong_accept",
            "EDC/SAC-KG/Taxonomy-RAG family baselines or reproductions",
            "pass" if sac_style_ready else ("partial" if max_rows.get("B3_edc_style", 0) >= FULL_EVAL_ROWS and max_rows.get("B4_taxonomy_rag", 0) >= FULL_EVAL_ROWS else "fail"),
            sac_style_ready,
            [
                file_evidence(exp_dir / "50_qwen3_8b_edc_schema_ablation_quality_report.md"),
                file_evidence(exp_dir / "50_sac_kg_verifier_pruner_baseline_quality_report.md"),
                {
                    "B3_edc_style_rows": max_rows.get("B3_edc_style", 0),
                    "B4_taxonomy_rag_rows": max_rows.get("B4_taxonomy_rag", 0),
                    "B6_sac_kg_verifier_pruner_rows": max_rows.get("B6_sac_kg_verifier_pruner", 0),
                    "B6_report_exists": (exp_dir / "50_sac_kg_verifier_pruner_baseline_quality_report.md").exists(),
                    "note": "B6 is a deterministic SAC-KG-style verifier/pruner approximation, not a full SAC-KG reproduction.",
                },
            ],
            done_or(
                sac_style_ready,
                "No additional automatic step required; B3/B4/B6 family baseline artifacts are present.",
                "Run B3/B4 plus a SAC-KG-style verifier/pruner approximation, or clearly document why full SAC-KG reproduction is out of scope.",
            ),
        ),
        item(
            "strong.mapping_downstream",
            "strong_accept",
            "NCS/PCF mapping downstream evaluation",
            "pass" if mapping_ready else "partial",
            mapping_ready,
            [
                {"complete_source_groups": mapping_groups, "pending_rows": pending_mapping, "metrics_rows": len(mapping_rows)},
                file_evidence(exp_dir / "06_release/mapping_review_progress_report.md"),
                file_evidence(exp_dir / "05_review/mapping_review_priority_queue.csv"),
                file_evidence(exp_dir / "04_evaluation/ncs_pcf_crosswalk_summary.json"),
                file_evidence(exp_dir / "04_evaluation/ncs_pcf_crosswalk_report.md"),
                file_evidence(workspace / "outputs/08_mapping/l2_ncs_pcf_crosswalk_candidates.jsonl"),
            ],
            "Complete expert review for mapping candidates and crosswalk candidates before making P@K/MRR/nDCG@10, explanation-quality, accept-rate, or utility claims.",
        ),
        item(
            "strong.active_review",
            "strong_accept",
            "Active review efficiency evaluation",
            "partial"
            if (
                (exp_dir / "04_evaluation/active_review_efficiency_metrics.json").exists()
                and (exp_dir / "06_release/active_review_human_effort_plan.json").exists()
            )
            else "fail",
            False,
            [
                file_evidence(exp_dir / "04_evaluation/active_review_efficiency_metrics.json"),
                file_evidence(exp_dir / "04_evaluation/active_review_efficiency_report.md"),
                file_evidence(exp_dir / "04_evaluation/active_review_ablation_metrics.json"),
                file_evidence(exp_dir / "04_evaluation/active_review_ablation_report.md"),
                file_evidence(exp_dir / "04_evaluation/active_review_pool_overlap_summary.json"),
                file_evidence(exp_dir / "04_evaluation/active_review_pool_overlap_report.md"),
                file_evidence(exp_dir / "05_review/active_review_human_effort_template.csv"),
                file_evidence(exp_dir / "06_release/active_review_human_effort_plan.json"),
                file_evidence(exp_dir / "04_evaluation/active_review_human_effort_metrics.json"),
            ],
            "Collect reviewed active-review human-effort CSV and validate efficiency against human adjudication outcomes.",
        ),
        item(
            "strong.visualization",
            "strong_accept",
            "Visualization/demo provided",
            "pass" if (workspace / "outputs/09_visualization/kg_viewer.html").exists() else "fail",
            (workspace / "outputs/09_visualization/kg_viewer.html").exists(),
            [file_evidence(workspace / "outputs/09_visualization/kg_viewer.html")],
            done_or(
                (workspace / "outputs/09_visualization/kg_viewer.html").exists(),
                "No additional automatic step required; keep the viewer synchronized with future graph updates.",
                "Generate or repair the KG visualization viewer.",
            ),
        ),
        item(
            "method.m1_m11",
            "method_modules",
            "CAPE-KG M1-M11 modules represented by executable artifacts",
            "partial" if method_all_artifacts_present else "fail",
            method_all_artifacts_present,
            [
                file_evidence(method_coverage_path),
                file_evidence(method_coverage_report),
                {
                    "module_count": method_module_count,
                    "modules_with_required_artifacts": method_present_count,
                    "missing_required_artifact_count": method_missing_count,
                    "human_dependent_modules": method_summary.get("human_dependent_modules"),
                    "coverage_claim_status": method_summary.get("claim_status"),
                },
                file_evidence(exp_dir / "02_schema/competency_questions.json"),
                file_evidence(exp_dir / "02_schema/prompts/P_cape_kg.txt"),
                file_evidence(exp_dir / "04_evaluation/evidence_span_granularity_report.md"),
                file_evidence(exp_dir / "04_evaluation/structural_evaluation_metrics.json"),
                file_evidence(exp_dir / "04_evaluation/structural_evaluation_report.md"),
                file_evidence(exp_dir / "04_evaluation/ontology_conformance_metrics.json"),
                file_evidence(exp_dir / "04_evaluation/ontology_conformance_report.md"),
                file_evidence(exp_dir / "04_evaluation/procedural_consistency_metrics.json"),
                file_evidence(exp_dir / "04_evaluation/procedural_consistency_report.md"),
                file_evidence(exp_dir / "04_evaluation/cq_answerability_structural_metrics.json"),
                file_evidence(exp_dir / "04_evaluation/structural_gap_worklist_summary.json"),
                file_evidence(exp_dir / "04_evaluation/structural_gap_worklist_report.md"),
                file_evidence(exp_dir / "05_review/structural_review_checkpoint_candidates.csv"),
                file_evidence(exp_dir / "05_review/structural_gateway_branch_gaps.csv"),
                file_evidence(exp_dir / "05_review/structural_review_optional_returns.csv"),
                file_evidence(exp_dir / "06_release/structural_review_action_plan.md"),
                file_evidence(exp_dir / "06_release/structural_review_return_preflight.md"),
                file_evidence(exp_dir / "05_review/actual_llm_active_review_queue_P_cape_kg_actual.jsonl"),
                file_evidence(exp_dir / "05_review/active_review_human_effort_template.csv"),
                file_evidence(exp_dir / "06_release/active_review_human_effort_plan.md"),
                file_evidence(exp_dir / "06_release/annotation_batch_assignment_report.md"),
                file_evidence(exp_dir / "04_evaluation/mapping_downstream_report.md"),
                file_evidence(exp_dir / "04_evaluation/ncs_pcf_crosswalk_report.md"),
                file_evidence(exp_dir / "06_release/mapping_review_progress_report.md"),
                file_evidence(exp_dir / "05_review/mapping_review_next_20_groups.csv"),
            ],
            "All executable module artifacts are present; human-review and human-gold scoring evidence remains required for final paper claims."
            if method_all_artifacts_present
            else "Run build_cape_method_module_coverage.py and regenerate missing module artifacts.",
        ),
    ]

    status_counts = Counter(row["status"] for row in items)
    claimable_count = sum(1 for row in items if row["claimable"])
    blocking = [
        row for row in items
        if row["category"] == "minimum_accept" and row["status"] != "pass" and not row["claimable"]
    ]
    strong_human_blocking = [
        row for row in items
        if row["category"] == "strong_accept" and row["status"] in {"pending_human", "partial"} and not row["claimable"]
    ]
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_plan": str(plan_file),
        "experiment_dir": str(exp_dir),
        "summary": {
            "items": len(items),
            "status_counts": dict(status_counts),
            "claimable_items": claimable_count,
            "minimum_accept_blocking_items": len(blocking),
            "strong_accept_human_blocking_items": len(strong_human_blocking),
            "evaluation_chunks": eval_chunks,
            "condition_max_rows": max_rows,
            "condition_parse_or_generation_error_rows_at_max_run": parse_rows,
        },
        "items": items,
        "blocking_items": blocking,
        "strong_human_blocking_items": strong_human_blocking,
        "claim_status": "pending_human_gold_iaa_and_human_gold_scoring" if blocking else "minimum_accept_requirements_satisfied",
    }
    return payload


def markdown_report(payload):
    lines = [
        "# CAPE-KG Submission Readiness Audit",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Source plan: `{payload['source_plan']}`",
        f"Experiment: `{payload['experiment_dir']}`",
        "",
        f"Claim status: **{payload['claim_status']}**",
        "",
        "This audit maps the revised EACL plan to current files. It does not treat silver/proxy diagnostics as human-gold evidence.",
        "",
        "## Summary",
        "",
        f"- Total audited items: {payload['summary']['items']}",
        f"- Claimable items: {payload['summary']['claimable_items']}",
        f"- Minimum-accept blocking items: {payload['summary']['minimum_accept_blocking_items']}",
        f"- Strong-accept human-blocking items: {payload['summary']['strong_accept_human_blocking_items']}",
        f"- Status counts: `{payload['summary']['status_counts']}`",
        "",
        "## Requirement Table",
        "",
        "| id | category | status | claimable | requirement | next step |",
        "|---|---|---:|---:|---|---|",
    ]
    for row in payload["items"]:
        lines.append(
            f"| {row['id']} | {row['category']} | {row['status']} | "
            f"{'yes' if row['claimable'] else 'no'} | {row['requirement']} | {row['next_step']} |"
        )
    lines += ["", "## Blocking Minimum-Accept Items", ""]
    if payload["blocking_items"]:
        for row in payload["blocking_items"]:
            lines.append(f"- {row['id']}: {row['requirement']} -> {row['next_step']}")
    else:
        lines.append("- None.")
    lines += ["", "## Strong-Accept Human-Dependent Items", ""]
    if payload["strong_human_blocking_items"]:
        for row in payload["strong_human_blocking_items"]:
            lines.append(f"- {row['id']}: {row['requirement']} -> {row['next_step']}")
    else:
        lines.append("- None.")
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--plan-file", default=str(DEFAULT_PLAN))
    args = parser.parse_args()

    exp_dir = Path(args.experiment_dir)
    payload = audit(exp_dir, Path(args.plan_file))
    output_dir = exp_dir / "06_release"
    write_json(output_dir / "submission_readiness_audit.json", payload)
    write_text(output_dir / "submission_readiness_audit.md", markdown_report(payload))
    print(json.dumps({
        "audit_json": str(output_dir / "submission_readiness_audit.json"),
        "audit_report": str(output_dir / "submission_readiness_audit.md"),
        "claim_status": payload["claim_status"],
        "status_counts": payload["summary"]["status_counts"],
        "blocking_items": [row["id"] for row in payload["blocking_items"]],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
