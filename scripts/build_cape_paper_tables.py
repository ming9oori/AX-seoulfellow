#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build paper-oriented Markdown/LaTeX tables from CAPE-KG experiment outputs."""

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
FOCUS_CONDITIONS = [
    "B0_plain_llm",
    "B1_predicate_constrained",
    "B2_current_project",
    "B3_edc_style",
    "B4_taxonomy_rag",
    "B5_procedural_prompt",
    "B6_sac_kg_verifier_pruner",
    "P_cape_kg_actual",
    "P_minus_CQ",
    "P_minus_Evidence",
    "P_minus_Procedural_schema",
    "P_minus_Schema_retrieval",
    "P_minus_Standard_bridge",
    "P_minus_Validator",
]


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def fmt(value):
    if value is None:
        return "pending"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def read_csv(path):
    path = Path(path)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def markdown_table(headers, rows):
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(fmt(cell) for cell in row) + " |")
    return "\n".join(lines)


def latex_escape(value):
    text = fmt(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text


def latex_table(caption, label, headers, rows):
    align = "l" * len(headers)
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\small",
        r"\begin{tabular}{" + align + "}",
        r"\toprule",
        " & ".join(latex_escape(h) for h in headers) + r" \\",
        r"\midrule",
    ]
    for row in rows:
        lines.append(" & ".join(latex_escape(cell) for cell in row) + r" \\")
    lines += [
        r"\bottomrule",
        r"\end{tabular}",
        rf"\caption{{{latex_escape(caption)}}}",
        rf"\label{{{latex_escape(label)}}}",
        r"\end{table}",
        "",
    ]
    return "\n".join(lines)


def dataset_rows(exp_dir):
    run_summary = read_json(exp_dir / "run_summary.json", {}) or {}
    human = read_json(exp_dir / "04_evaluation/human_gold_validation_summary.json", {}) or {}
    mapping = read_json(exp_dir / "01_data/mapping_review/mapping_review_manifest.json", {}) or {}
    expansion = read_json(exp_dir / "01_data/gold_annotation/annotation_expansion_manifest.json", {}) or {}
    return [
        ["Evaluation chunks", run_summary.get("evaluation_chunks", "missing"), "selected Korean bid/proposal chunks"],
        ["Optional all-available annotation chunks", expansion.get("all_available_chunk_count", "missing"), expansion.get("claim_status", "missing")],
        ["Optional remaining annotation chunks", expansion.get("remaining_optional_chunk_count", "missing"), "not part of the 11-file minimum paper gate"],
        [
            "Optional strong resegmented review units",
            expansion.get("strong_resegmented_chunk_count", "missing"),
            f"max {expansion.get('strong_resegmented_max_sentences', 'missing')} source sentences/unit; {expansion.get('strong_resegmented_claim_status', 'missing')}",
        ],
        ["Silver nodes", run_summary.get("silver_reference_nodes", "missing"), "current KG-derived reference"],
        ["Silver edges", run_summary.get("silver_reference_edges", "missing"), "current KG-derived reference"],
        ["Silver evidence anchors", run_summary.get("silver_reference_evidence", "missing"), "current KG-derived reference"],
        ["Adjudicated human-gold chunks", human.get("completed_adjudicated_chunks", 0), human.get("claim_status", "missing")],
        ["Human-gold items", human.get("gold_item_count_for_readiness", 0), "nodes + edges + evidence"],
        ["Mapping review rows", mapping.get("candidate_rows", 0), mapping.get("claim_status", "missing")],
    ]


def gold_sampling_rows(exp_dir):
    payload = read_json(exp_dir / "06_release/gold_sampling_coverage_report.json", {}) or {}
    if not payload:
        return [["missing", "missing", "missing", "missing", "missing", "missing", "missing"]]
    policy = payload.get("selection_policy") or {}
    coverage = payload.get("coverage_summary") or {}
    return [
        [
            payload.get("claim_status"),
            policy.get("selected_chunk_count"),
            coverage.get("priority_100_candidate_edges"),
            coverage.get("full_120_candidate_edges"),
            coverage.get("priority_100_candidate_edge_coverage_of_full120"),
            coverage.get("priority_100_active_review_chunk_coverage_of_full120"),
            coverage.get("priority_100_high_impact_chunk_coverage_of_full120"),
        ]
    ]


def actual_llm_rows(exp_dir):
    payload = read_json(exp_dir / "04_evaluation/actual_llm_silver_metrics.json", {}) or {}
    by_condition = {row.get("condition"): row for row in payload.get("metrics", [])}
    rows = []
    for condition in FOCUS_CONDITIONS:
        row = by_condition.get(condition)
        if not row:
            continue
        rows.append(
            [
                condition,
                row.get("edge_exact_f1"),
                row.get("predicate_f1"),
                row.get("node_label_f1"),
                row.get("evidence_f1"),
                row.get("parse_or_generation_error_rows"),
                row.get("partial_json_repaired_rows"),
            ]
        )
    return rows


def core_condition_rows_from_file(path, model_label):
    payload = read_json(path, {}) or {}
    by_condition = {row.get("condition"): row for row in payload.get("metrics", [])}
    rows = []
    for condition in ["B0_plain_llm", "B1_predicate_constrained", "B2_current_project", "P_cape_kg_actual"]:
        row = by_condition.get(condition)
        if not row:
            continue
        rows.append(
            [
                model_label,
                condition,
                row.get("rows"),
                row.get("edge_exact_f1"),
                row.get("predicate_f1"),
                row.get("node_label_f1"),
                row.get("evidence_f1"),
                row.get("parse_or_generation_error_rows"),
                row.get("partial_json_repaired_rows"),
            ]
        )
    return rows


def model_scaling_rows(exp_dir):
    rows = []
    rows.extend(core_condition_rows_from_file(exp_dir / "04_evaluation/actual_llm_silver_metrics.json", "Qwen3-8B"))
    rows.extend(core_condition_rows_from_file(exp_dir / "04_evaluation/qwen3_14b_core_silver_metrics.json", "Qwen3-14B"))
    rows.extend(core_condition_rows_from_file(exp_dir / "04_evaluation/qwen3_32b_awq_core_silver_metrics.json", "Qwen3-32B-AWQ"))
    return rows


def human_gold_rows(exp_dir):
    payload = read_json(exp_dir / "04_evaluation/human_gold_metrics.json", {}) or {}
    rows = payload.get("metrics", [])
    if not rows:
        validation = (payload.get("validation") or read_json(exp_dir / "04_evaluation/human_gold_validation_summary.json", {}) or {})
        return [[validation.get("claim_status", "pending_human_adjudication"), validation.get("completed_adjudicated_chunks", 0), validation.get("gold_item_count_for_readiness", 0), "metrics pending"]]
    return [
        [
            row.get("condition"),
            row.get("edge_exact_f1"),
            row.get("node_label_f1"),
            row.get("evidence_exact_match"),
            row.get("ontology_conformance"),
            row.get("procedural_consistency"),
            row.get("cq_answerability"),
        ]
        for row in rows
    ]


def evidence_span_rows(exp_dir):
    payload = read_json(exp_dir / "04_evaluation/evidence_span_granularity_metrics.json", {}) or {}
    if not payload:
        return [["missing", "missing", "missing", "missing", "missing", "missing"]]
    return [
        [
            payload.get("triple_count"),
            payload.get("component_count"),
            payload.get("subject_exact_span_rate"),
            payload.get("object_exact_span_rate"),
            payload.get("predicate_full_sentence_proxy_rate"),
            payload.get("claim_status"),
        ]
    ]


def predicate_cue_span_rows(exp_dir):
    payload = read_json(exp_dir / "04_evaluation/predicate_cue_span_metrics.json", {}) or {}
    if not payload:
        return [["missing", "missing", "missing", "missing", "missing", "missing", "missing"]]
    return [
        [
            payload.get("triple_count"),
            payload.get("predicate_cue_span_count"),
            payload.get("predicate_cue_missing_count"),
            payload.get("predicate_cue_span_rate"),
            payload.get("chunk_span_count"),
            payload.get("source_text_included"),
            payload.get("claim_status"),
        ]
    ]


def structural_rows(exp_dir):
    payload = read_json(exp_dir / "04_evaluation/structural_evaluation_metrics.json", {}) or {}
    if not payload:
        return [["missing", "missing", "missing", "missing", "missing", "missing", "missing"]]
    ontology = payload.get("ontology_conformance") or {}
    procedural = payload.get("procedural_consistency") or {}
    cq = payload.get("cq_answerability") or {}
    return [
        [
            payload.get("claim_status", "kg_structural_diagnostic_not_human_gold"),
            ontology.get("ontology_conformance_rate"),
            ontology.get("domain_range_violation_count"),
            ontology.get("evidence_missing_edge_count"),
            procedural.get("procedural_consistency_rate"),
            procedural.get("precedence_cycle_count"),
            cq.get("cq_answerability_rate"),
        ]
    ]


def structural_gap_rows(exp_dir):
    payload = read_json(exp_dir / "04_evaluation/structural_gap_worklist_summary.json", {}) or {}
    if not payload:
        return [["missing", "missing", "missing", "missing", "missing"]]
    return [
        [
            payload.get("claim_status"),
            payload.get("review_checkpoint_candidate_count"),
            payload.get("gateway_branch_gap_count"),
            payload.get("structural_cq_answerability_rate"),
            payload.get("human_gate_effect"),
        ]
    ]


def public_rows(exp_dir):
    rows = []
    for path in sorted((exp_dir / "08_public_benchmarks").glob("*_summary.json")):
        payload = read_json(path, {}) or {}
        if "paged_items" not in payload and "text2kg_items" not in payload:
            continue
        rows.append(
            [
                path.name,
                payload.get("paged_items", 0),
                (payload.get("paged") or {}).get("mean_node_label_f1"),
                (payload.get("paged") or {}).get("mean_edge_predicate_f1"),
                payload.get("text2kg_items", 0),
                (payload.get("text2kg") or {}).get("mean_relation_f1"),
                (payload.get("text2kg") or {}).get("mean_triple_exact_f1"),
            ]
        )
    return rows


def public_crosscheck_rows(exp_dir):
    payload = read_json(exp_dir / "08_public_benchmarks/public_benchmark_crosscheck_summary.json", {}) or {}
    summary = payload.get("summary") or {}
    if not summary:
        return [["missing", "missing", "missing", "missing", "missing", "missing", "missing"]]
    return [
        [
            summary.get("run_count"),
            summary.get("strong_cross_run_present"),
            summary.get("max_single_run_paged_items"),
            summary.get("max_single_run_text2kg_items"),
            summary.get("best_paged_edge_f1"),
            summary.get("best_text2kg_relation_f1"),
            summary.get("claim_status"),
        ]
    ]


def mapping_rows(exp_dir):
    payload = read_json(exp_dir / "04_evaluation/mapping_expert_metrics.json", {}) or {}
    return [
        [
            row.get("standard"),
            row.get("completed_rows"),
            row.get("pending_rows"),
            row.get("complete_source_groups"),
            row.get("hit_at_5"),
            row.get("precision_at_5"),
            row.get("mrr"),
            row.get("ndcg_at_10"),
            row.get("explanation_quality_score_mean"),
            row.get("claim_status"),
        ]
        for row in payload.get("metrics", [])
    ]


def crosswalk_rows(exp_dir):
    payload = read_json(exp_dir / "04_evaluation/ncs_pcf_crosswalk_summary.json", {}) or {}
    if not payload:
        return [["missing", "missing", "missing", "missing", "missing"]]
    return [
        [
            payload.get("shared_source_tasks"),
            payload.get("all_pair_count"),
            payload.get("candidate_count"),
            payload.get("top_k_per_standard"),
            payload.get("claim_status"),
        ]
    ]


def crosswalk_expert_rows(exp_dir):
    payload = read_json(exp_dir / "04_evaluation/crosswalk_expert_metrics.json", {}) or {}
    metrics = payload.get("metrics") or {}
    if not metrics:
        return [["missing", "missing", "missing", "missing", "missing", "missing", "missing", "missing", "missing"]]
    return [
        [
            metrics.get("candidate_rows"),
            metrics.get("source_task_count"),
            metrics.get("completed_rows"),
            metrics.get("pending_rows"),
            metrics.get("hit_at_5"),
            metrics.get("precision_at_10"),
            metrics.get("mrr"),
            metrics.get("utility_grade_mean"),
            metrics.get("claim_status"),
        ]
    ]


def active_review_rows(exp_dir):
    payload = read_json(exp_dir / "04_evaluation/active_review_efficiency_metrics.json", {}) or {}
    wanted_budgets = {10, 25, 55, 100}
    rows = []
    for row in payload.get("metrics", []):
        if row.get("target_label") != "high_impact_error":
            continue
        if row.get("strategy") not in {"active_priority", "uncertainty_only"}:
            continue
        if row.get("budget") not in wanted_budgets:
            continue
        rows.append(
            [
                payload.get("condition", row.get("condition")),
                row.get("strategy"),
                row.get("budget"),
                row.get("errors_found"),
                row.get("error_precision_at_k"),
                row.get("error_recall_at_k"),
                row.get("lift_vs_random_expected"),
                payload.get("claim_status", "silver_proxy_diagnostic"),
            ]
        )
    return rows


def active_review_ablation_rows(exp_dir):
    payload = read_json(exp_dir / "04_evaluation/active_review_ablation_metrics.json", {}) or {}
    wanted_budgets = {25, 55, 100}
    rows = []
    for row in payload.get("rows", []):
        if row.get("target_label") != "high_impact_error":
            continue
        if row.get("budget") not in wanted_budgets:
            continue
        rows.append(
            [
                row.get("condition"),
                row.get("strategy"),
                row.get("budget"),
                row.get("errors_found"),
                row.get("error_precision_at_k"),
                row.get("error_recall_at_k"),
                row.get("lift_vs_random_expected"),
                row.get("claim_status"),
            ]
        )
    return rows


def active_review_human_effort_rows(exp_dir):
    payload = read_json(exp_dir / "04_evaluation/active_review_human_effort_metrics.json", {}) or {}
    rows = []
    for row in payload.get("metrics", []):
        rows.append(
            [
                row.get("arm"),
                row.get("budget"),
                row.get("assigned"),
                row.get("reviewed"),
                row.get("review_seconds"),
                row.get("corrected_errors"),
                row.get("high_impact_corrections"),
                row.get("claim_status"),
            ]
        )
    if not rows and payload:
        rows.append(
            [
                payload.get("condition", "P_cape_kg_actual"),
                payload.get("arm_budget", "missing"),
                payload.get("pooled_rows", "missing"),
                0,
                0,
                0,
                0,
                payload.get("claim_status", "ready_for_human_effort_collection"),
            ]
        )
    return rows


def active_review_pool_overlap_rows(exp_dir):
    payload = read_json(exp_dir / "04_evaluation/active_review_pool_overlap_summary.json", {}) or {}
    if not payload:
        return [["missing", "missing", "missing", "missing", "missing", "missing", "missing", "missing"]]
    arm_counts = payload.get("arm_counts") or {}
    return [
        [
            payload.get("total_arm_assignments_before_pooling"),
            payload.get("unique_review_rows"),
            payload.get("duplicate_assignments_removed_by_pooling"),
            payload.get("pooling_reduction_rate"),
            arm_counts.get("active_priority"),
            arm_counts.get("uncertainty_only"),
            arm_counts.get("random_control"),
            payload.get("claim_status"),
        ]
    ]


def statistical_rows(exp_dir):
    payload = read_json(exp_dir / "04_evaluation/statistical_analysis_metrics.json", {}) or {}
    focus_baselines = {"B0_plain_llm", "B2_current_project", "B3_edc_style", "B4_taxonomy_rag", "B5_procedural_prompt"}
    focus_metrics = {"predicate_f1", "node_label_f1", "evidence_f1"}
    rows = []
    for row in payload.get("bootstrap_rows", []):
        if row.get("baseline_condition") not in focus_baselines:
            continue
        if row.get("metric") not in focus_metrics:
            continue
        rows.append(
            [
                row.get("baseline_condition"),
                row.get("metric"),
                row.get("proposed_macro_mean"),
                row.get("baseline_macro_mean"),
                row.get("mean_delta"),
                f"[{row.get('bootstrap_ci_low')}, {row.get('bootstrap_ci_high')}]",
                row.get("bootstrap_p_approx"),
                row.get("claim_status"),
            ]
        )
    return rows


def gate_rows(exp_dir):
    payload = read_json(exp_dir / "06_release/claim_gate_report.json", {}) or {}
    return [
        [row.get("gate_id"), row.get("status"), row.get("required"), row.get("evidence")]
        for row in payload.get("gates", [])
    ]


def run(args):
    exp_dir = Path(args.experiment_dir)
    generated = datetime.now(timezone.utc).isoformat()

    sections = []
    latex_sections = []

    table_specs = [
        (
            "Dataset and Annotation Status",
            "tab:cape-data-status",
            ["Item", "Value", "Note"],
            dataset_rows(exp_dir),
        ),
        (
            "Gold Subset Sampling Coverage",
            "tab:cape-gold-sampling",
            ["Status", "Selected", "Selected edges", "Full-120 edges", "Candidate coverage", "Active coverage", "High-impact coverage"],
            gold_sampling_rows(exp_dir),
        ),
        (
            "Actual LLM Silver Diagnostics",
            "tab:cape-actual-silver",
            ["Condition", "Edge F1", "Predicate F1", "Node F1", "Evidence F1", "Parse errors", "Repairs"],
            actual_llm_rows(exp_dir),
        ),
        (
            "Model Scaling Core Silver Diagnostics",
            "tab:cape-model-scaling",
            ["Model", "Condition", "Rows", "Edge F1", "Predicate F1", "Node F1", "Evidence F1", "Parse errors", "Repairs"],
            model_scaling_rows(exp_dir),
        ),
        (
            "Human-Gold Metrics",
            "tab:cape-human-gold",
            ["Condition/status", "Edge/chunks", "Node/items", "Evidence EM", "Ontology", "Procedural", "CQ"],
            human_gold_rows(exp_dir),
        ),
        (
            "Evidence Span Granularity Diagnostic",
            "tab:cape-evidence-span-granularity",
            ["Triples", "Components", "Subject exact", "Object exact", "Predicate proxy", "Status"],
            evidence_span_rows(exp_dir),
        ),
        (
            "Predicate Cue Span Diagnostic",
            "tab:cape-predicate-cue-span",
            ["Triples", "Cue spans", "Missing cues", "Cue rate", "Chunk spans", "Source text included", "Status"],
            predicate_cue_span_rows(exp_dir),
        ),
        (
            "KG Structural Diagnostics",
            "tab:cape-structural-diagnostics",
            ["Status", "Ontology", "Domain/range errors", "Evidence missing", "Procedural", "Cycles", "CQ answerability"],
            structural_rows(exp_dir),
        ),
        (
            "Structural Gap Worklist",
            "tab:cape-structural-gap-worklist",
            ["Status", "Review checkpoint candidates", "Gateway branch gaps", "Structural CQ", "Human gate effect"],
            structural_gap_rows(exp_dir),
        ),
        (
            "Public Subset Diagnostics",
            "tab:cape-public-subset",
            ["Run", "PAGED n", "PAGED node F1", "PAGED edge F1", "Text2KG n", "Relation F1", "Triple F1"],
            public_rows(exp_dir),
        ),
        (
            "Public Benchmark Cross-Check",
            "tab:cape-public-crosscheck",
            ["Runs", "Strong run", "Max PAGED n", "Max Text2KG n", "Best PAGED edge F1", "Best Text2KG relation F1", "Status"],
            public_crosscheck_rows(exp_dir),
        ),
        (
            "Mapping Expert Review",
            "tab:cape-mapping-review",
            ["Standard", "Completed", "Pending", "Groups", "Hit@5", "P@5", "MRR", "nDCG@10", "Explanation", "Status"],
            mapping_rows(exp_dir),
        ),
        (
            "Layer2-bridged NCS-PCF Crosswalk Candidates",
            "tab:cape-ncs-pcf-crosswalk",
            ["Shared Layer2 tasks", "All pairs", "Candidate rows", "Top-K per standard", "Status"],
            crosswalk_rows(exp_dir),
        ),
        (
            "Crosswalk Expert Review",
            "tab:cape-crosswalk-review",
            ["Candidates", "Source tasks", "Completed", "Pending", "Hit@5", "P@10", "MRR", "Utility", "Status"],
            crosswalk_expert_rows(exp_dir),
        ),
        (
            "Active Review Prioritization Diagnostic",
            "tab:cape-active-review",
            ["Condition", "Strategy", "Budget", "Errors", "Precision@k", "Recall@k", "Lift", "Status"],
            active_review_rows(exp_dir),
        ),
        (
            "P minus Active Review Ablation Diagnostic",
            "tab:cape-active-review-ablation",
            ["Condition", "Strategy", "Budget", "Errors", "Precision@k", "Recall@k", "Lift", "Status"],
            active_review_ablation_rows(exp_dir),
        ),
        (
            "Active Review Human-Effort Handoff",
            "tab:cape-active-review-effort",
            ["Arm", "Budget", "Assigned", "Reviewed", "Seconds", "Corrections", "High-impact", "Status"],
            active_review_human_effort_rows(exp_dir),
        ),
        (
            "Active Review Pool Design",
            "tab:cape-active-review-pool",
            ["Arm assignments", "Unique rows", "Duplicate removed", "Reduction", "Active rows", "Uncertainty rows", "Random rows", "Status"],
            active_review_pool_overlap_rows(exp_dir),
        ),
        (
            "Paired Bootstrap Silver Diagnostics",
            "tab:cape-bootstrap",
            ["Baseline", "Metric", "P mean", "Base mean", "Delta", "95% CI", "p approx", "Status"],
            statistical_rows(exp_dir),
        ),
        (
            "Claim Gate",
            "tab:cape-claim-gate",
            ["Gate", "Status", "Required", "Evidence"],
            gate_rows(exp_dir),
        ),
    ]

    for title, label, headers, rows in table_specs:
        if not rows:
            rows = [["missing", "missing", "missing"][: len(headers)]]
        sections.append(f"## {title}\n\n" + markdown_table(headers, rows))
        latex_sections.append(latex_table(title, label, headers, rows))

    md = "\n\n".join(
        [
            "# CAPE-KG Paper Tables",
            "",
            f"Generated: {generated}",
            "",
            "Tables marked by pending human gold or expert review are diagnostic only and should not be used as final paper claims.",
            "",
            *sections,
            "",
        ]
    )
    tex = "\n".join(
        [
            "% Auto-generated CAPE-KG paper tables.",
            f"% Generated: {generated}",
            "% Requires booktabs.",
            "",
            *latex_sections,
        ]
    )

    output_dir = exp_dir / "06_release"
    write_text(output_dir / "paper_tables.md", md)
    write_text(output_dir / "paper_tables.tex", tex)
    print(json.dumps({"paper_tables_md": str(output_dir / "paper_tables.md"), "paper_tables_tex": str(output_dir / "paper_tables.tex")}, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
