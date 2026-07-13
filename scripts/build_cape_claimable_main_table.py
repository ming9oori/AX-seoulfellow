#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a conservative claimable main-table view for CAPE-KG."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")


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


def fmt(value):
    if value is None or value == "":
        return "-"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def markdown_table(headers, rows):
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(header, "")) for header in headers) + " |")
    return "\n".join(lines)


def gate_map(claim_gate):
    return {row.get("gate_id"): row for row in claim_gate.get("gates", [])}


def public_summary(exp_dir):
    crosscheck = read_json(exp_dir / "08_public_benchmarks/public_benchmark_crosscheck_summary.json", {}) or {}
    crosscheck_summary = crosscheck.get("summary") or {}
    if crosscheck_summary:
        return {
            "manifest_exists": bool(read_json(exp_dir / "08_public_benchmarks/public_benchmark_manifest.json", {}) or {}),
            "summary_count": int(crosscheck_summary.get("run_count") or 0),
            "paged_items": int(crosscheck_summary.get("max_single_run_paged_items") or 0),
            "text2kg_items": int(crosscheck_summary.get("max_single_run_text2kg_items") or 0),
            "best_paged_edge_f1": float(crosscheck_summary.get("best_paged_edge_f1") or 0.0),
            "best_text2kg_relation_f1": float(crosscheck_summary.get("best_text2kg_relation_f1") or 0.0),
            "strong_cross_run_present": bool(crosscheck_summary.get("strong_cross_run_present")),
            "evidence_file": "08_public_benchmarks/public_benchmark_crosscheck_summary.json",
        }

    manifest = read_json(exp_dir / "08_public_benchmarks/public_benchmark_manifest.json", {}) or {}
    summaries = []
    for path in sorted((exp_dir / "08_public_benchmarks").glob("*_summary.json")):
        payload = read_json(path, {}) or {}
        if "paged_items" in payload or "text2kg_items" in payload:
            summaries.append(payload)
    paged_items = max((int(item.get("paged_items") or 0) for item in summaries), default=0)
    text2kg_items = max((int(item.get("text2kg_items") or 0) for item in summaries), default=0)
    best_text2kg_relation = max(
        ((item.get("text2kg") or {}).get("mean_relation_f1") or 0.0 for item in summaries),
        default=0.0,
    )
    best_paged_edge = max(
        ((item.get("paged") or {}).get("mean_edge_predicate_f1") or 0.0 for item in summaries),
        default=0.0,
    )
    return {
        "manifest_exists": bool(manifest),
        "summary_count": len(summaries),
        "paged_items": paged_items,
        "text2kg_items": text2kg_items,
        "best_paged_edge_f1": best_paged_edge,
        "best_text2kg_relation_f1": best_text2kg_relation,
        "strong_cross_run_present": False,
        "evidence_file": "08_public_benchmarks/*_summary.json",
    }


def first_condition(metrics, condition):
    for row in metrics:
        if row.get("condition") == condition:
            return row
    return None


def build_rows(exp_dir):
    claim_gate = read_json(exp_dir / "06_release/claim_gate_report.json", {}) or {}
    gates = gate_map(claim_gate)
    human_validation = read_json(exp_dir / "04_evaluation/human_gold_validation_summary.json", {}) or {}
    human_metrics_payload = read_json(exp_dir / "04_evaluation/human_gold_metrics.json", {}) or {}
    human_metrics = human_metrics_payload.get("metrics") or []
    silver_payload = read_json(exp_dir / "04_evaluation/actual_llm_silver_metrics.json", {}) or {}
    silver_metrics = silver_payload.get("metrics") or []
    qwen_scaling = read_json(exp_dir / "06_release/qwen3_model_scaling_report.json", {}) or {}
    qwen_scaling_summary = qwen_scaling.get("summary") or {}
    qwen_scaling_models = qwen_scaling.get("model_rows") or []
    mapping_payload = read_json(exp_dir / "04_evaluation/mapping_expert_metrics.json", {}) or {}
    mapping_metrics = mapping_payload.get("metrics") or []
    crosswalk_payload = read_json(exp_dir / "04_evaluation/crosswalk_expert_metrics.json", {}) or {}
    crosswalk_metrics = crosswalk_payload.get("metrics") or {}
    crosswalk_summary = read_json(exp_dir / "04_evaluation/ncs_pcf_crosswalk_summary.json", {}) or {}
    active_ablation = read_json(exp_dir / "04_evaluation/active_review_ablation_metrics.json", {}) or {}
    active_pool = read_json(exp_dir / "04_evaluation/active_review_pool_overlap_summary.json", {}) or {}
    active_briefing = read_json(exp_dir / "06_release/active_review_human_effort_briefing.json", {}) or {}
    evidence_spans = read_json(exp_dir / "04_evaluation/evidence_span_granularity_metrics.json", {}) or {}
    predicate_cues = read_json(exp_dir / "04_evaluation/predicate_cue_span_metrics.json", {}) or {}
    structural = read_json(exp_dir / "04_evaluation/structural_evaluation_metrics.json", {}) or {}
    structural_gap = read_json(exp_dir / "04_evaluation/structural_gap_worklist_summary.json", {}) or {}
    annotation_expansion = read_json(exp_dir / "01_data/gold_annotation/annotation_expansion_manifest.json", {}) or {}
    gold_sampling = read_json(exp_dir / "06_release/gold_sampling_coverage_report.json", {}) or {}
    public = public_summary(exp_dir)
    ontology = structural.get("ontology_conformance") or {}
    procedural = structural.get("procedural_consistency") or {}
    cq = structural.get("cq_answerability") or {}
    sampling_policy = gold_sampling.get("selection_policy") or {}
    sampling_coverage = gold_sampling.get("coverage_summary") or {}

    completed_chunks = int(human_validation.get("completed_adjudicated_chunks") or 0)
    gold_items = int(human_validation.get("gold_item_count_for_readiness") or 0)
    validation_errors = int(human_validation.get("validation_error_count") or 0)
    human_ready = completed_chunks >= 100 and gold_items >= 500 and validation_errors == 0 and bool(human_metrics)
    proposed_human = first_condition(human_metrics, "P_cape_kg_actual")
    proposed_silver = first_condition(silver_metrics, "P_cape_kg_actual") or {}
    qwen_scaling_values = []
    for row in qwen_scaling_models:
        qwen_scaling_values.append(
            (
                f"{row.get('model')}: exact={row.get('proposed_edge_exact_f1')}, "
                f"predicate={row.get('proposed_predicate_f1')}, "
                f"evidence={row.get('proposed_evidence_f1')}"
            )
        )

    full_mapping = bool(mapping_metrics) and all(row.get("claim_status") == "expert_review_evaluated" for row in mapping_metrics)
    complete_mapping_groups = sum(int(row.get("complete_source_groups") or 0) for row in mapping_metrics)
    pending_mapping_rows = sum(int(row.get("pending_rows") or 0) for row in mapping_metrics)
    full_crosswalk = bool(crosswalk_metrics) and crosswalk_metrics.get("claim_status") == "crosswalk_expert_review_evaluated"

    rows = [
        {
            "Result": "Core extraction main result",
            "Claimability": "claimable" if human_ready else "pending_human",
            "Primary metric": "Human-gold edge/node/evidence F1",
            "Current value": (
                f"edge={proposed_human.get('edge_exact_f1')}, node={proposed_human.get('node_label_f1')}, evidence={proposed_human.get('evidence_f1')}"
                if human_ready and proposed_human
                else "not claimable yet"
            ),
            "Evidence file": "04_evaluation/human_gold_metrics.json",
            "Blocker / note": (
                "none"
                if human_ready
                else f"{completed_chunks}/100 adjudicated chunks, {gold_items}/500 items, validation_errors={validation_errors}"
            ),
        },
        {
            "Result": "Actual LLM run coverage",
            "Claimability": "claimable_setup",
            "Primary metric": "Full conditions generated",
            "Current value": "B0/B1/B2/P=120 rows; 6 ablations",
            "Evidence file": "06_release/claim_gate_report.json",
            "Blocker / note": "generation coverage only; not final quality without human-gold scoring",
        },
        {
            "Result": "Optional annotation expansion",
            "Claimability": "claimable_setup",
            "Primary metric": "All available current-corpus chunks prepared for optional review",
            "Current value": (
                f"all_available={annotation_expansion.get('all_available_chunk_count', 'missing')}, "
                f"remaining_optional={annotation_expansion.get('remaining_optional_chunk_count', 'missing')}, "
                f"strong_300_gap_without_split={annotation_expansion.get('strong_300_chunk_gap', 'missing')}, "
                f"resegmented={annotation_expansion.get('strong_resegmented_chunk_count', 'missing')}, "
                f"strong_300_gap_after_split={annotation_expansion.get('strong_300_chunk_gap_after_resegmentation', 'missing')}"
            ),
            "Evidence file": "01_data/gold_annotation/annotation_expansion_manifest.json",
            "Blocker / note": "optional package does not change the 11-file minimum paper gate; it is tracked separately for strong/optional claims",
        },
        {
            "Result": "Priority-100 gold subset sampling",
            "Claimability": "claimable_setup",
            "Primary metric": "Coverage of full-120 candidate edges, active-review chunks, and high-impact chunks",
            "Current value": (
                f"selected={sampling_policy.get('selected_chunk_count', 'missing')}, "
                f"candidate_edge_coverage={sampling_coverage.get('priority_100_candidate_edge_coverage_of_full120', 'missing')}, "
                f"active_review_coverage={sampling_coverage.get('priority_100_active_review_chunk_coverage_of_full120', 'missing')}, "
                f"high_impact_coverage={sampling_coverage.get('priority_100_high_impact_chunk_coverage_of_full120', 'missing')}"
            ),
            "Evidence file": "06_release/gold_sampling_coverage_report.json",
            "Blocker / note": gold_sampling.get(
                "claim_status",
                "sampling evidence only; not human-gold until two annotators, IAA, and adjudication are complete",
            ),
        },
        {
            "Result": "CAPE-KG silver diagnostic",
            "Claimability": "diagnostic_only",
            "Primary metric": "Silver edge/predicate/node/evidence F1",
            "Current value": (
                f"edge={proposed_silver.get('edge_exact_f1')}, predicate={proposed_silver.get('predicate_f1')}, "
                f"node={proposed_silver.get('node_label_f1')}, evidence={proposed_silver.get('evidence_f1')}"
            ),
            "Evidence file": "04_evaluation/actual_llm_silver_metrics.json",
            "Blocker / note": silver_payload.get("claim_status", "silver_proxy_not_human_gold"),
        },
        {
            "Result": "Qwen3 model scaling diagnostic",
            "Claimability": "diagnostic_only",
            "Primary metric": "Proposed-method silver exact/predicate/evidence F1 across Qwen3-8B/14B/32B-AWQ",
            "Current value": "; ".join(qwen_scaling_values) if qwen_scaling_values else "missing",
            "Evidence file": "06_release/qwen3_model_scaling_report.json",
            "Blocker / note": (
                f"{qwen_scaling_summary.get('claim_status', 'missing')}; "
                f"32B-AWQ rows={qwen_scaling_summary.get('qwen3_32b_awq_valid_rows', 'missing')}/"
                f"{qwen_scaling_summary.get('qwen3_32b_awq_raw_rows', 'missing')}; "
                "not human-gold performance evidence"
            ),
        },
        {
            "Result": "Evidence span granularity",
            "Claimability": "diagnostic_only",
            "Primary metric": "Subject/object lexical char-span coverage; predicate sentence proxy coverage",
            "Current value": (
                f"subject_exact={evidence_spans.get('subject_exact_span_rate', 'missing')}, "
                f"object_exact={evidence_spans.get('object_exact_span_rate', 'missing')}, "
                f"predicate_proxy={evidence_spans.get('predicate_full_sentence_proxy_rate', 'missing')}"
            ),
            "Evidence file": "04_evaluation/evidence_span_granularity_metrics.json",
            "Blocker / note": "predicate-token and final exactness claims require adjudicated human-gold spans",
        },
        {
            "Result": "Predicate cue span diagnostic",
            "Claimability": "diagnostic_only",
            "Primary metric": "Lexical predicate-cue span coverage",
            "Current value": (
                f"cue_spans={predicate_cues.get('predicate_cue_span_count', 'missing')}/"
                f"{predicate_cues.get('triple_count', 'missing')}, "
                f"rate={predicate_cues.get('predicate_cue_span_rate', 'missing')}, "
                f"source_text_included={predicate_cues.get('source_text_included', 'missing')}"
            ),
            "Evidence file": "04_evaluation/predicate_cue_span_metrics.json; outputs/06_triples/layer2_predicate_cue_spans.jsonl",
            "Blocker / note": "automatic lexical diagnostic only; predicate-token correctness requires adjudicated human-gold spans",
        },
        {
            "Result": "KG structural diagnostics",
            "Claimability": "diagnostic_only",
            "Primary metric": "Ontology conformance, procedural consistency, CQ answerability",
            "Current value": (
                f"ontology={ontology.get('ontology_conformance_rate', 'missing')}, "
                f"procedural={procedural.get('procedural_consistency_rate', 'missing')}, "
                f"cq={cq.get('cq_answerability_rate', 'missing')}"
            ),
            "Evidence file": "04_evaluation/structural_evaluation_metrics.json",
            "Blocker / note": structural.get("claim_status", "human-gold structural scoring required before final paper claims"),
        },
        {
            "Result": "Structural gap worklist",
            "Claimability": "claimable_setup",
            "Primary metric": "Review-checkpoint candidates and gateway branch gaps prepared for review",
            "Current value": (
                f"review_checkpoint_candidates={structural_gap.get('review_checkpoint_candidate_count', 'missing')}, "
                f"gateway_branch_gaps={structural_gap.get('gateway_branch_gap_count', 'missing')}"
            ),
            "Evidence file": "04_evaluation/structural_gap_worklist_summary.json",
            "Blocker / note": structural_gap.get(
                "human_gate_effect",
                "worklist only; KG is not automatically changed without human review",
            ),
        },
        {
            "Result": "Public benchmark adapter",
            "Claimability": "auxiliary_claimable",
            "Primary metric": "PAGED/Text2KG subset metrics",
            "Current value": (
                f"PAGED n={public['paged_items']}, best edge F1={public['best_paged_edge_f1']:.4f}; "
                f"Text2KG n={public['text2kg_items']}, best relation F1={public['best_text2kg_relation_f1']:.4f}; "
                f"strong_cross_run={public['strong_cross_run_present']}"
            ),
            "Evidence file": public["evidence_file"],
            "Blocker / note": "auxiliary generalization evidence, not the Korean enterprise human-gold main result",
        },
        {
            "Result": "NCS/PCF mapping downstream",
            "Claimability": "claimable" if full_mapping else "pending_expert_review",
            "Primary metric": "Hit@5/P@5/MRR/nDCG@10/explanation quality for Layer2-to-NCS and Layer2-to-PCF candidates",
            "Current value": (
                f"complete_groups={complete_mapping_groups}, pending_rows={pending_mapping_rows}"
            ),
            "Evidence file": "04_evaluation/mapping_expert_metrics.json",
            "Blocker / note": "expert review must complete Top-5 NCS/PCF candidate groups before downstream mapping claims",
        },
        {
            "Result": "NCS-PCF crosswalk downstream",
            "Claimability": "claimable" if full_crosswalk else "pending_expert_review",
            "Primary metric": "Expert accept rate, Hit@K, P@10, MRR, nDCG@10, utility, explanation quality for Layer2-bridged crosswalk candidates",
            "Current value": (
                f"candidates={crosswalk_metrics.get('candidate_rows', crosswalk_summary.get('candidate_count', 'missing'))}, "
                f"source_tasks={crosswalk_metrics.get('source_task_count', crosswalk_summary.get('shared_source_tasks', 'missing'))}, "
                f"completed_rows={crosswalk_metrics.get('completed_rows', 'missing')}, "
                f"pending_rows={crosswalk_metrics.get('pending_rows', 'missing')}"
            ),
            "Evidence file": "04_evaluation/crosswalk_expert_metrics.json; 04_evaluation/ncs_pcf_crosswalk_summary.json",
            "Blocker / note": "expert review must validate NCS-PCF crosswalk utility before bridge-support claims",
        },
        {
            "Result": "Active-review pool design",
            "Claimability": "claimable_setup",
            "Primary metric": "Three-arm review pool coverage and duplicate reduction",
            "Current value": (
                f"arm_assignments={active_pool.get('total_arm_assignments_before_pooling', 'missing')}, "
                f"unique_rows={active_pool.get('unique_review_rows', 'missing')}, "
                f"duplicate_removed={active_pool.get('duplicate_assignments_removed_by_pooling', 'missing')}, "
                f"reduction={active_pool.get('pooling_reduction_rate', 'missing')}"
            ),
            "Evidence file": "04_evaluation/active_review_pool_overlap_summary.json",
            "Blocker / note": "pool design only; efficiency claims require human timing/correction evidence",
        },
        {
            "Result": "Active-review human-effort briefing",
            "Claimability": "claimable_setup",
            "Primary metric": "Ordered review-navigation sheet for pooled active/uncertainty/random rows",
            "Current value": (
                f"briefing_rows={active_briefing.get('briefing_rows', 'missing')}, "
                f"pooled_rows={active_briefing.get('pooled_rows', 'missing')}, "
                f"claim_status={active_briefing.get('claim_status', 'missing')}"
            ),
            "Evidence file": "06_release/active_review_human_effort_briefing.json; 05_review/active_review_human_effort_briefing.csv",
            "Blocker / note": "review navigation only; efficiency claims require returned timing/correction evidence",
        },
        {
            "Result": "Active-review ablation",
            "Claimability": "diagnostic_only",
            "Primary metric": "P vs P-minus-active-review silver/proxy review-priority lift",
            "Current value": f"ablation_rows={active_ablation.get('row_count', 'missing')}",
            "Evidence file": "04_evaluation/active_review_ablation_metrics.json",
            "Blocker / note": "human timing/correction evidence and adjudicated labels required before efficiency claims",
        },
        {
            "Result": "Release/reproducibility package",
            "Claimability": "claimable_setup",
            "Primary metric": "Release artifacts and public-safe bundle",
            "Current value": gates.get("release.artifacts", {}).get("status", "missing"),
            "Evidence file": "06_release/release_bundle_manifest.json",
            "Blocker / note": "public-safe bundle excludes source text and internal review handoff files",
        },
        {
            "Result": "Submission claim gate",
            "Claimability": "not_ready",
            "Primary metric": "Conservative gate status",
            "Current value": claim_gate.get("overall_status", "missing"),
            "Evidence file": "06_release/claim_gate_report.json",
            "Blocker / note": f"required_failures={claim_gate.get('required_failure_count')}, warnings={claim_gate.get('warning_count')}",
        },
    ]
    return rows


def render_report(payload):
    headers = ["Result", "Claimability", "Primary metric", "Current value", "Evidence file", "Blocker / note"]
    lines = [
        "# CAPE-KG Claimable Main Table",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Overall claim status: `{payload['overall_claim_status']}`",
        "",
        "This table is intentionally conservative. Silver/proxy diagnostics are separated from claimable human-gold results.",
        "",
        markdown_table(headers, payload["rows"]),
        "",
        "## Interpretation",
        "",
        "- `claimable`: can be used as a paper claim with the listed evidence.",
        "- `claimable_setup`: supports reproducibility or experiment coverage, but is not a quality result.",
        "- `auxiliary_claimable`: can support an auxiliary/public-benchmark claim, not the main Korean enterprise result.",
        "- `diagnostic_only`: useful for debugging or motivation only.",
        "- `pending_human` / `pending_expert_review`: blocked on human review before paper claims.",
        "",
    ]
    return "\n".join(lines)


def run(args):
    exp_dir = Path(args.experiment_dir)
    rows = build_rows(exp_dir)
    blocking = [row for row in rows if row["Claimability"] in {"pending_human", "pending_expert_review", "not_ready"}]
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "overall_claim_status": "ready" if not blocking else "pending_human_gold_and_or_expert_review",
        "blocking_result_count": len(blocking),
        "rows": rows,
    }
    release_dir = exp_dir / "06_release"
    write_json(release_dir / "claimable_main_table.json", payload)
    write_text(release_dir / "claimable_main_table.md", render_report(payload))
    print(json.dumps({
        "claimable_main_table_json": str(release_dir / "claimable_main_table.json"),
        "claimable_main_table_md": str(release_dir / "claimable_main_table.md"),
        "overall_claim_status": payload["overall_claim_status"],
        "blocking_result_count": payload["blocking_result_count"],
    }, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
