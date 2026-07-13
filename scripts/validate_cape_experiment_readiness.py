#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Conservative readiness gate for the CAPE-KG EACL experiment package.

The gate is intentionally stricter than the scaffold reports: it only marks a
paper claim as ready when the current files contain direct evidence. Pending
human annotation, IAA, adjudication, or expert mapping review remain failures.
"""

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
MIN_CHUNKS = 100
MIN_GOLD_ITEMS = 500
MIN_ABLATIONS = 3
FULL_EVAL_ROWS = 120
BASELINE_CONDITIONS = {"B0_plain_llm", "B1_predicate_constrained", "B2_current_project"}
PROPOSED_CONDITION = "P_cape_kg_actual"
REQUIRED_ERROR_ANALYSIS_SECTIONS = [
    "## Claim Scope",
    "## Actual LLM Silver/Proxy Diagnostics",
    "## Proxy Scaffold Error Summary",
    "## Error Taxonomy",
    "## Human-Gold Follow-Up",
]


def strip_prefix_suffix(value, prefix="", suffix=""):
    value = str(value)
    if prefix and value.startswith(prefix):
        value = value[len(prefix):]
    if suffix and value.endswith(suffix):
        value = value[:-len(suffix)]
    return value


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


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


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def status(ok, severity="fail"):
    if ok:
        return "PASS"
    if severity == "warn":
        return "WARN"
    return "FAIL"


def gate(gate_id, description, ok, evidence, severity="fail", required=True):
    return {
        "gate_id": gate_id,
        "description": description,
        "required": required,
        "severity": severity,
        "status": status(ok, severity),
        "evidence": evidence,
    }


def condition_counts(exp_dir):
    counts = defaultdict(
        lambda: {
            "raw_rows": 0,
            "valid_rows": 0,
            "parse_or_generation_error_rows": 0,
            "partial_json_repaired_rows": 0,
            "unrepaired_parse_or_generation_error_rows": 0,
            "max_raw_rows_single_run": 0,
            "parse_or_generation_error_rows_at_max_run": 0,
            "partial_json_repaired_rows_at_max_run": 0,
            "unrepaired_parse_or_generation_error_rows_at_max_run": 0,
            "selected_max_run_prefix": "",
        }
    )
    for report in sorted(exp_dir.glob("50_*_quality_report.md")):
        prefix = strip_prefix_suffix(report.name, "50_", "_quality_report.md")
        raw_path = exp_dir / f"48_{prefix}_raw.jsonl"
        valid_path = exp_dir / f"49_{prefix}_valid.jsonl"
        raw_rows = []
        if raw_path.exists():
            with raw_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        raw_rows.append(json.loads(line))
        valid_rows = []
        if valid_path.exists():
            with valid_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        valid_rows.append(json.loads(line))
        run_counts = defaultdict(
            lambda: {
                "raw_rows": 0,
                "parse_or_generation_error_rows": 0,
                "partial_json_repaired_rows": 0,
                "unrepaired_parse_or_generation_error_rows": 0,
            }
        )
        for row in raw_rows:
            condition = row.get("condition") or "unknown"
            counts[condition]["raw_rows"] += 1
            run_counts[condition]["raw_rows"] += 1
            if row.get("partial_json_repaired"):
                counts[condition]["partial_json_repaired_rows"] += 1
                run_counts[condition]["partial_json_repaired_rows"] += 1
            if row.get("parse_error") or row.get("error"):
                counts[condition]["parse_or_generation_error_rows"] += 1
                run_counts[condition]["parse_or_generation_error_rows"] += 1
                if not row.get("partial_json_repaired"):
                    counts[condition]["unrepaired_parse_or_generation_error_rows"] += 1
                    run_counts[condition]["unrepaired_parse_or_generation_error_rows"] += 1
        for row in valid_rows:
            counts[row.get("condition") or "unknown"]["valid_rows"] += 1
        for condition, run_count in run_counts.items():
            current = counts[condition]
            better_same_size = (
                run_count["raw_rows"] == current["max_raw_rows_single_run"]
                and run_count["raw_rows"] > 0
                and (
                    run_count["unrepaired_parse_or_generation_error_rows"]
                    < current["unrepaired_parse_or_generation_error_rows_at_max_run"]
                    or (
                        run_count["unrepaired_parse_or_generation_error_rows"]
                        == current["unrepaired_parse_or_generation_error_rows_at_max_run"]
                        and run_count["parse_or_generation_error_rows"]
                        < current["parse_or_generation_error_rows_at_max_run"]
                    )
                )
            )
            if run_count["raw_rows"] > current["max_raw_rows_single_run"] or better_same_size:
                counts[condition]["max_raw_rows_single_run"] = run_count["raw_rows"]
                counts[condition]["parse_or_generation_error_rows_at_max_run"] = run_count["parse_or_generation_error_rows"]
                counts[condition]["partial_json_repaired_rows_at_max_run"] = run_count["partial_json_repaired_rows"]
                counts[condition]["unrepaired_parse_or_generation_error_rows_at_max_run"] = run_count["unrepaired_parse_or_generation_error_rows"]
                counts[condition]["selected_max_run_prefix"] = prefix
    return dict(counts)


def human_gold_gate(exp_dir):
    summary_path = exp_dir / "04_evaluation/human_gold_validation_summary.json"
    summary = read_json(summary_path, {}) or {}
    completed = int(summary.get("completed_adjudicated_chunks") or 0)
    items = int(summary.get("gold_item_count_for_readiness") or 0)
    errors = int(summary.get("validation_error_count") or 0)
    return summary_path, summary, completed, items, errors


def iaa_gate(exp_dir):
    package_dir = exp_dir / "01_data/gold_annotation"
    summaries = []
    for path in sorted(package_dir.glob("iaa*/iaa_summary.json")):
        payload = read_json(path, {}) or {}
        payload["_path"] = str(path)
        summaries.append(payload)
    max_completed = max([int(row.get("completed_pair_chunks") or 0) for row in summaries] or [0])
    computed = any(
        (row.get("status") == "computed") and int(row.get("completed_pair_chunks") or 0) >= MIN_CHUNKS
        for row in summaries
    )
    return summaries, max_completed, computed


def human_gold_metric_conditions(exp_dir):
    metrics = read_json(exp_dir / "04_evaluation/human_gold_metrics.json", {}) or {}
    rows = metrics.get("metrics") or []
    return {row.get("condition") for row in rows if row.get("claim_status") == "human_gold_scored"}


def mapping_gate(exp_dir):
    metrics_path = exp_dir / "04_evaluation/mapping_expert_metrics.json"
    progress_path = exp_dir / "06_release/mapping_review_progress_summary.json"
    metrics = read_json(metrics_path, {}) or {}
    progress = read_json(progress_path, {}) or {}
    rows = metrics.get("metrics") or []
    completed_groups = sum(int(row.get("complete_source_groups") or 0) for row in rows)
    pending_rows = sum(int(row.get("pending_rows") or 0) for row in rows if isinstance(row.get("pending_rows"), int))
    fully_evaluated = bool(rows) and all(row.get("claim_status") == "expert_review_evaluated" for row in rows)
    return metrics_path, progress_path, progress, rows, completed_groups, pending_rows, fully_evaluated


def crosswalk_gate(exp_dir):
    metrics_path = exp_dir / "04_evaluation/crosswalk_expert_metrics.json"
    manifest_path = exp_dir / "01_data/crosswalk_review/crosswalk_review_manifest.json"
    metrics = read_json(metrics_path, {}) or {}
    manifest = read_json(manifest_path, {}) or {}
    summary = metrics.get("metrics") or {}
    completed_rows = int(summary.get("completed_rows") or 0)
    pending_rows = int(summary.get("pending_rows") or 0)
    complete_groups = int(summary.get("complete_source_groups") or 0)
    fully_evaluated = bool(summary) and summary.get("claim_status") == "crosswalk_expert_review_evaluated"
    return metrics_path, manifest_path, manifest, summary, completed_rows, pending_rows, complete_groups, fully_evaluated


def public_subset_gate(exp_dir):
    public_dir = exp_dir / "08_public_benchmarks"
    crosscheck_path = public_dir / "public_benchmark_crosscheck_summary.json"
    crosscheck = read_json(crosscheck_path, {}) or {}
    crosscheck_summary = crosscheck.get("summary") or {}
    if crosscheck_summary:
        return (
            crosscheck.get("runs") or [],
            int(crosscheck_summary.get("max_single_run_paged_items") or 0),
            int(crosscheck_summary.get("max_single_run_text2kg_items") or 0),
        )

    summaries = []
    for path in sorted(public_dir.glob("*_summary.json")):
        payload = read_json(path, {}) or {}
        if payload.get("is_shard"):
            continue
        if "paged_items" in payload or "text2kg_items" in payload:
            payload["_path"] = str(path)
            summaries.append(payload)
    total_paged = sum(int(row.get("paged_items") or 0) for row in summaries)
    total_text2kg = sum(int(row.get("text2kg_items") or 0) for row in summaries)
    return summaries, total_paged, total_text2kg


def existing_file_gate(path):
    path = Path(path)
    return path.exists() and path.stat().st_size > 0


def error_analysis_status(exp_dir):
    md_path = Path(exp_dir) / "07_reports/error_analysis.md"
    json_path = Path(exp_dir) / "07_reports/error_analysis.json"
    evidence = {
        "markdown": {"path": str(md_path), "exists": md_path.exists(), "bytes": md_path.stat().st_size if md_path.exists() else 0},
        "json": {"path": str(json_path), "exists": json_path.exists(), "bytes": json_path.stat().st_size if json_path.exists() else 0},
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


def build_report(payload):
    lines = [
        "# CAPE-KG Claim Gate Report",
        "",
        f"Generated: {payload['generated_at_utc']}",
        "",
        f"Overall status: **{payload['overall_status']}**",
        "",
        "This gate is conservative. Silver/proxy diagnostics and actual LLM runs are not treated as final paper evidence unless they are scored against adjudicated human gold labels.",
        "",
        "| gate | status | requirement | evidence |",
        "|---|---|---|---|",
    ]
    for row in payload["gates"]:
        evidence = str(row["evidence"]).replace("\n", " ")
        lines.append(f"| {row['gate_id']} | {row['status']} | {row['description']} | {evidence} |")
    lines += [
        "",
        "## Blocking Items",
        "",
    ]
    blocking = [row for row in payload["gates"] if row["status"] == "FAIL" and row["required"]]
    if blocking:
        for row in blocking:
            lines.append(f"- {row['gate_id']}: {row['description']} ({row['evidence']})")
    else:
        lines.append("- None")
    warnings = [row for row in payload["gates"] if row["status"] == "WARN"]
    lines += ["", "## Warnings", ""]
    if warnings:
        for row in warnings:
            lines.append(f"- {row['gate_id']}: {row['description']} ({row['evidence']})")
    else:
        lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def run(args):
    exp_dir = Path(args.experiment_dir)
    gates = []

    eval_chunk_count = read_jsonl_count(exp_dir / "01_data/evaluation_chunks.jsonl")
    gates.append(
        gate(
            "data.eval_chunks",
            f"Evaluation subset has at least {MIN_CHUNKS} chunks",
            eval_chunk_count >= MIN_CHUNKS,
            f"{eval_chunk_count} chunks in {exp_dir / '01_data/evaluation_chunks.jsonl'}",
        )
    )

    validation_path, validation, completed_chunks, gold_items, validation_errors = human_gold_gate(exp_dir)
    gates.append(
        gate(
            "gold.completed_chunks",
            f"Adjudicated human-gold chunks >= {MIN_CHUNKS}",
            completed_chunks >= MIN_CHUNKS and validation_errors == 0,
            f"{completed_chunks} completed chunks, validation_errors={validation_errors}, file={validation_path}",
        )
    )
    gates.append(
        gate(
            "gold.item_count",
            f"Human-gold node/edge/evidence items >= {MIN_GOLD_ITEMS}",
            gold_items >= MIN_GOLD_ITEMS and validation_errors == 0,
            f"{gold_items} items, validation_errors={validation_errors}, file={validation_path}",
        )
    )

    iaa_summaries, max_iaa_completed, iaa_ready = iaa_gate(exp_dir)
    gates.append(
        gate(
            "gold.iaa",
            f"Two-annotator agreement computed for >= {MIN_CHUNKS} chunks",
            iaa_ready,
            f"max_completed_pair_chunks={max_iaa_completed}, summaries={len(iaa_summaries)}",
        )
    )

    counts = condition_counts(exp_dir)
    baseline_ready = all(counts.get(cond, {}).get("max_raw_rows_single_run", 0) >= FULL_EVAL_ROWS for cond in BASELINE_CONDITIONS)
    gates.append(
        gate(
            "llm.baselines",
            "Actual full B0/B1/B2 LLM baseline generations exist",
            baseline_ready,
            {cond: counts.get(cond, {}).get("max_raw_rows_single_run", 0) for cond in sorted(BASELINE_CONDITIONS)},
        )
    )

    proposed_generation_ready = counts.get(PROPOSED_CONDITION, {}).get("max_raw_rows_single_run", 0) >= FULL_EVAL_ROWS
    gates.append(
        gate(
            "llm.proposed_generation",
            "Actual full CAPE-KG proposed generation exists",
            proposed_generation_ready,
            {PROPOSED_CONDITION: counts.get(PROPOSED_CONDITION, {}).get("max_raw_rows_single_run", 0)},
        )
    )

    human_metric_conditions = human_gold_metric_conditions(exp_dir)
    gates.append(
        gate(
            "llm.proposed_human_gold_score",
            "CAPE-KG proposed result is scored against adjudicated human gold",
            PROPOSED_CONDITION in human_metric_conditions,
            f"human_gold_scored_conditions={sorted(c for c in human_metric_conditions if c)}",
        )
    )

    ablation_conditions = {
        cond
        for cond, row in counts.items()
        if cond.startswith("P_minus_") and row.get("max_raw_rows_single_run", 0) >= FULL_EVAL_ROWS
    }
    gates.append(
        gate(
            "llm.ablations",
            f"Actual full ablation runs >= {MIN_ABLATIONS}",
            len(ablation_conditions) >= MIN_ABLATIONS,
            f"{len(ablation_conditions)} full ablations: {sorted(ablation_conditions)}",
        )
    )

    strict_parse_warnings = {}
    unrepaired_parse_warnings = {}
    for cond, row in counts.items():
        raw_rows = int(row.get("max_raw_rows_single_run") or 0)
        if raw_rows < FULL_EVAL_ROWS:
            continue
        strict_rate = (int(row.get("parse_or_generation_error_rows_at_max_run") or 0) / raw_rows) if raw_rows else 0.0
        unrepaired_rate = (int(row.get("unrepaired_parse_or_generation_error_rows_at_max_run") or 0) / raw_rows) if raw_rows else 0.0
        if strict_rate > 0.50:
            strict_parse_warnings[cond] = round(strict_rate, 4)
        if unrepaired_rate > 0.05:
            unrepaired_parse_warnings[cond] = round(unrepaired_rate, 4)
    gates.append(
        gate(
            "llm.revalidated_output_recovery",
            "Full actual LLM conditions have unrepaired parse/generation error rate <= 5%",
            not unrepaired_parse_warnings,
            unrepaired_parse_warnings or "all full conditions <= 5% unrepaired after conservative partial-JSON recovery",
            severity="warn",
            required=False,
        )
    )
    gates.append(
        gate(
            "llm.strict_json_rate",
            "Full actual LLM conditions have strict JSON parse/generation error rate <= 50%",
            not strict_parse_warnings,
            strict_parse_warnings or "all full conditions <= 50% strict parse/generation errors",
            severity="warn",
            required=False,
        )
    )

    public_summaries, paged_items, text2kg_items = public_subset_gate(exp_dir)
    gates.append(
        gate(
            "external.public_subset",
            "Public benchmark subset model evaluation exists",
            bool(public_summaries) and (paged_items > 0 or text2kg_items > 0),
            f"PAGED items={paged_items}, Text2KG items={text2kg_items}, summaries={len(public_summaries)}",
        )
    )

    mapping_path, mapping_progress_path, mapping_progress, mapping_rows, complete_groups, pending_mapping_rows, mapping_ready = mapping_gate(exp_dir)
    gates.append(
        gate(
            "mapping.expert_review",
            "NCS/PCF mapping downstream metrics are expert-review claimable",
            mapping_ready,
            (
                f"complete_source_groups={complete_groups}, pending_rows={pending_mapping_rows}, file={mapping_path}, "
                f"progress_file={mapping_progress_path}, progress_pending_groups={mapping_progress.get('pending_source_groups')}"
            ),
            severity="fail",
            required=False,
        )
    )

    (
        crosswalk_path,
        crosswalk_manifest_path,
        crosswalk_manifest,
        crosswalk_summary,
        completed_crosswalk_rows,
        pending_crosswalk_rows,
        complete_crosswalk_groups,
        crosswalk_ready,
    ) = crosswalk_gate(exp_dir)
    gates.append(
        gate(
            "crosswalk.expert_review",
            "Layer2-bridged NCS-PCF crosswalk metrics are expert-review claimable",
            crosswalk_ready,
            (
                f"completed_rows={completed_crosswalk_rows}, pending_rows={pending_crosswalk_rows}, "
                f"complete_source_groups={complete_crosswalk_groups}, file={crosswalk_path}, "
                f"manifest_file={crosswalk_manifest_path}, candidate_rows={crosswalk_manifest.get('candidate_rows')}"
            ),
            severity="fail",
            required=False,
        )
    )

    error_analysis_ready, error_analysis_evidence = error_analysis_status(exp_dir)
    gates.append(
        gate(
            "analysis.error_analysis",
            "Structured error analysis includes claim scope, diagnostics, taxonomy, and human-gold follow-up",
            error_analysis_ready,
            error_analysis_evidence,
        )
    )

    release_files = [
        exp_dir / "02_schema/cape_schema.json",
        exp_dir / "02_schema/competency_questions.json",
        exp_dir / "02_schema/prompts/P_cape_kg.txt",
        exp_dir / "04_evaluation/actual_llm_silver_metrics.json",
        exp_dir / "04_evaluation/active_review_efficiency_metrics.json",
        exp_dir / "04_evaluation/active_review_efficiency_report.md",
        exp_dir / "04_evaluation/active_review_human_effort_metrics.json",
        exp_dir / "04_evaluation/active_review_human_effort_report.md",
        exp_dir / "04_evaluation/active_review_pool_overlap_summary.json",
        exp_dir / "04_evaluation/active_review_pool_overlap_report.md",
        exp_dir / "05_review/active_review_human_effort_template.csv",
        exp_dir / "06_release/active_review_human_effort_plan.json",
        exp_dir / "06_release/active_review_human_effort_plan.md",
        exp_dir / "08_public_benchmarks/public_benchmark_crosscheck_summary.json",
        exp_dir / "08_public_benchmarks/public_benchmark_crosscheck_report.md",
        exp_dir / "04_evaluation/statistical_analysis_metrics.json",
        exp_dir / "04_evaluation/statistical_analysis_report.md",
        exp_dir / "07_reports/error_analysis.md",
        exp_dir / "07_reports/error_analysis.json",
        exp_dir / "01_data/gold_annotation/annotation_manifest_sync_report.json",
        exp_dir / "01_data/gold_annotation/annotation_manifest_sync_report.md",
        exp_dir / "05_review/human_gold_annotation_priority_queue.csv",
        exp_dir / "05_review/human_gold_next_100_worklist.csv",
        exp_dir / "05_review/human_gold_batches/full_120_batch_assignment_overview.csv",
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
        exp_dir / "06_release/mapping_review_progress_summary.json",
        exp_dir / "06_release/mapping_review_progress_report.md",
        exp_dir / "06_release/submission_readiness_audit.json",
        exp_dir / "06_release/submission_readiness_audit.md",
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
        exp_dir / "06_release/release_bundle_manifest.json",
        exp_dir / "06_release/release_bundle_checksums.sha256",
        exp_dir / "06_release/release_bundle_safety_report.md",
    ]
    missing_release = [str(path) for path in release_files if not existing_file_gate(path)]
    gates.append(
        gate(
            "release.artifacts",
            "Schema, prompts, evaluation, error analysis, limitations, and reproducibility artifacts exist",
            not missing_release,
            missing_release or "all required release files exist",
        )
    )

    required_failures = [row for row in gates if row["required"] and row["status"] == "FAIL"]
    warnings = [row for row in gates if row["status"] == "WARN"]
    optional_failures = [row for row in gates if (not row["required"]) and row["status"] == "FAIL"]
    overall_status = "PASS" if not required_failures else "FAIL"
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "overall_status": overall_status,
        "required_failure_count": len(required_failures),
        "optional_failure_count": len(optional_failures),
        "warning_count": len(warnings),
        "gates": gates,
        "condition_counts": counts,
        "human_gold_validation": validation,
        "mapping_expert_metrics": mapping_rows,
        "crosswalk_expert_metrics": crosswalk_summary,
    }

    output_dir = exp_dir / "06_release"
    write_json(output_dir / "claim_gate_report.json", payload)
    write_text(output_dir / "claim_gate_report.md", build_report(payload))
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if overall_status != "PASS" and not args.no_fail:
        return 1
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--no-fail", action="store_true", help="Write reports but exit 0 even when required gates fail.")
    args = parser.parse_args()
    sys.exit(run(args))


if __name__ == "__main__":
    main()
