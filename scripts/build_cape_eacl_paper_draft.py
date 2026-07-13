#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a claim-safe EACL paper draft from current CAPE-KG artifacts."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from cape_pre_human_status import effective_prehuman_summary


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
TITLE = "CAPE-KG: Competency-Question Anchored Procedural Evidence Grounding for Domain Knowledge Graph Construction"
FOCUS_CONDITIONS = [
    "B0_plain_llm",
    "B1_predicate_constrained",
    "B2_current_project",
    "B3_edc_style",
    "B4_taxonomy_rag",
    "B5_procedural_prompt",
    "B6_sac_kg_verifier_pruner",
    "P_cape_kg_actual",
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


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def fmt(value):
    if value is None:
        return "pending"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def md_table(headers, rows):
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(fmt(cell) for cell in row) + " |")
    return "\n".join(lines)


def condition_rows(exp_dir):
    payload = read_json(exp_dir / "04_evaluation/actual_llm_silver_metrics.json", {}) or {}
    by_condition = {row.get("condition"): row for row in payload.get("metrics", [])}
    rows = []
    for condition in FOCUS_CONDITIONS:
        row = by_condition.get(condition)
        if not row:
            continue
        rows.append([
            condition,
            row.get("rows"),
            row.get("edge_exact_f1"),
            row.get("predicate_f1"),
            row.get("node_label_f1"),
            row.get("evidence_f1"),
            row.get("parse_or_generation_error_rows"),
        ])
    return rows


def public_rows(exp_dir):
    rows = []
    public_dir = exp_dir / "08_public_benchmarks"
    for path in sorted(public_dir.glob("*_summary.json")):
        payload = read_json(path, {}) or {}
        if payload.get("is_shard"):
            continue
        if "paged_items" not in payload and "text2kg_items" not in payload:
            continue
        rows.append([
            path.name,
            payload.get("paged_items", 0),
            (payload.get("paged") or {}).get("mean_node_label_f1"),
            (payload.get("paged") or {}).get("mean_edge_predicate_f1"),
            payload.get("text2kg_items", 0),
            (payload.get("text2kg") or {}).get("mean_relation_f1"),
            (payload.get("text2kg") or {}).get("mean_triple_exact_f1"),
        ])
    return rows


def evidence_span_rows(exp_dir):
    payload = read_json(exp_dir / "04_evaluation/evidence_span_granularity_metrics.json", {}) or {}
    if not payload:
        return [["missing", "missing", "missing", "missing", "missing", "missing"]]
    return [[
        payload.get("triple_count"),
        payload.get("component_count"),
        payload.get("subject_exact_span_rate"),
        payload.get("object_exact_span_rate"),
        payload.get("predicate_full_sentence_proxy_rate"),
        payload.get("claim_status"),
    ]]


def structural_rows(exp_dir):
    payload = read_json(exp_dir / "04_evaluation/structural_evaluation_metrics.json", {}) or {}
    if not payload:
        return [["missing", "missing", "missing", "missing", "missing", "missing", "missing"]]
    ontology = payload.get("ontology_conformance") or {}
    procedural = payload.get("procedural_consistency") or {}
    cq = payload.get("cq_answerability") or {}
    return [[
        payload.get("claim_status"),
        ontology.get("ontology_conformance_rate"),
        ontology.get("domain_range_violation_count"),
        ontology.get("evidence_missing_edge_count"),
        procedural.get("procedural_consistency_rate"),
        procedural.get("precedence_cycle_count"),
        cq.get("cq_answerability_rate"),
    ]]


def structural_gap_rows(exp_dir):
    payload = read_json(exp_dir / "04_evaluation/structural_gap_worklist_summary.json", {}) or {}
    if not payload:
        return [["missing", "missing", "missing", "missing", "missing"]]
    return [[
        payload.get("claim_status"),
        payload.get("review_checkpoint_candidate_count"),
        payload.get("gateway_branch_gap_count"),
        payload.get("structural_cq_answerability_rate"),
        payload.get("human_gate_effect"),
    ]]


def active_review_ablation_rows(exp_dir):
    payload = read_json(exp_dir / "04_evaluation/active_review_ablation_metrics.json", {}) or {}
    rows = []
    for row in payload.get("rows", []):
        if row.get("target_label") != "high_impact_error":
            continue
        if row.get("budget") not in {25, 55, 100}:
            continue
        rows.append([
            row.get("condition"),
            row.get("strategy"),
            row.get("budget"),
            row.get("errors_found"),
            row.get("error_precision_at_k"),
            row.get("lift_vs_random_expected"),
            row.get("claim_status"),
        ])
    return rows


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
        return [["missing", "missing", "missing", "missing", "missing", "missing", "missing"]]
    return [[
        metrics.get("candidate_rows"),
        metrics.get("source_task_count"),
        metrics.get("completed_rows"),
        metrics.get("pending_rows"),
        metrics.get("hit_at_5"),
        metrics.get("utility_grade_mean"),
        metrics.get("claim_status"),
    ]]


def readiness_rows(audit):
    rows = []
    for item in audit.get("items", []):
        rows.append([
            item.get("id"),
            item.get("category"),
            item.get("status"),
            "yes" if item.get("claimable") else "no",
            item.get("requirement"),
        ])
    return rows


def blocking_rows(audit):
    return [
        [item.get("id"), item.get("requirement"), item.get("next_step")]
        for item in audit.get("blocking_items", [])
    ]


def truthy_present(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"yes", "true", "1", "present"}
    return bool(value)


def return_file_counts(required_returns):
    minimum = [row for row in required_returns if truthy_present(row.get("required_for_minimum", True))]
    optional = [row for row in required_returns if not truthy_present(row.get("required_for_minimum", True))]
    return {
        "minimum_paper_gate_return_files": len(minimum),
        "minimum_paper_gate_return_files_present": sum(1 for row in minimum if truthy_present(row.get("present"))),
        "optional_strong_return_files": len(optional),
        "optional_strong_return_files_present": sum(1 for row in optional if truthy_present(row.get("present"))),
        "tracked_human_return_files": len(required_returns),
        "tracked_human_return_files_present": sum(1 for row in required_returns if truthy_present(row.get("present"))),
    }


def return_type_rows(action_plan):
    counts = {}
    present = {}
    for row in action_plan.get("required_return_files", []):
        task_type = row.get("task_type", "unknown")
        counts[task_type] = counts.get(task_type, 0) + 1
        present[task_type] = present.get(task_type, 0) + (1 if truthy_present(row.get("present")) else 0)
    labels = {
        "human_gold_annotation": "Human-gold annotation",
        "human_gold_adjudication": "Human-gold adjudication",
        "mapping_expert_review": "Mapping expert review",
        "crosswalk_expert_review": "NCS-PCF crosswalk expert review",
        "active_review_human_effort": "Active-review human effort",
    }
    purposes = {
        "human_gold_annotation": "two-annotator labels for priority chunks",
        "human_gold_adjudication": "final adjudicated gold labels",
        "mapping_expert_review": "expert-confirmed NCS/PCF mapping labels",
        "crosswalk_expert_review": "expert-confirmed NCS-PCF crosswalk utility labels",
        "active_review_human_effort": "review timing and correction-effort evidence",
    }
    rows = []
    for task_type in [
        "human_gold_annotation",
        "human_gold_adjudication",
        "mapping_expert_review",
        "crosswalk_expert_review",
        "active_review_human_effort",
    ]:
        if task_type not in counts:
            continue
        rows.append([
            labels.get(task_type, task_type),
            counts[task_type],
            present.get(task_type, 0),
            purposes.get(task_type, ""),
        ])
    if rows:
        rows.append([
            "Total",
            sum(counts.values()),
            sum(present.values()),
            "all human-return files required before final claims",
        ])
    return rows


def handoff_bundle_rows(exp_dir):
    manifest = read_json(exp_dir / "06_release/human_review_handoff/human_review_handoff_manifest.json", {}) or {}
    bundles = manifest.get("bundles") or {}
    labels = {
        "annotator_A": "Annotator A",
        "annotator_B": "Annotator B",
        "coordinator": "Coordinator",
        "adjudicator": "Adjudicator",
        "mapping_expert": "Mapping expert",
        "crosswalk_expert": "NCS-PCF crosswalk expert",
        "active_review_effort": "Active-review effort",
        "structural_reviewer": "Structural reviewer",
        "strong_resegmented_review": "Optional strong 300+ review",
    }
    rows = []
    for key in [
        "annotator_A",
        "annotator_B",
        "coordinator",
        "adjudicator",
        "mapping_expert",
        "crosswalk_expert",
        "active_review_effort",
        "structural_reviewer",
        "strong_resegmented_review",
    ]:
        bundle = bundles.get(key)
        if not bundle:
            continue
        rows.append([
            labels.get(key, key),
            Path(bundle.get("path", "")).name,
            bundle.get("file_count"),
            bundle.get("sha256"),
        ])
    return rows


def build_markdown(exp_dir):
    now = datetime.now(timezone.utc).isoformat()
    audit = read_json(exp_dir / "06_release/submission_readiness_audit.json", {}) or {}
    gate = read_json(exp_dir / "06_release/claim_gate_report.json", {}) or {}
    run_summary = read_json(exp_dir / "run_summary.json", {}) or {}
    action_plan = read_json(exp_dir / "06_release/human_gate_action_plan.json", {}) or {}
    master_checklist = read_json(exp_dir / "06_release/human_review_master_checklist_ko.json", {}) or {}
    return_preflight = read_json(exp_dir / "06_release/human_review_return_preflight.json", {}) or {}
    pre_human = read_json(exp_dir / "06_release/pre_human_handoff_validation.json", {}) or {}
    effective_pre_human = effective_prehuman_summary(pre_human)
    provenance = read_json(exp_dir / "06_release/provenance_manifest.json", {}) or {}
    annotation_expansion = read_json(exp_dir / "01_data/gold_annotation/annotation_expansion_manifest.json", {}) or {}
    public = public_rows(exp_dir)
    conditions = condition_rows(exp_dir)
    crosswalk = crosswalk_rows(exp_dir)
    crosswalk_expert = crosswalk_expert_rows(exp_dir)
    active_ablation = active_review_ablation_rows(exp_dir)
    evidence_spans = evidence_span_rows(exp_dir)
    structural = structural_rows(exp_dir)
    structural_gap = structural_gap_rows(exp_dir)
    status = audit.get("claim_status", "unknown")
    summary = audit.get("summary", {})
    required_failures = gate.get("required_failure_count", "unknown")
    current_progress = action_plan.get("current_progress") or {}
    required_returns = action_plan.get("required_return_files") or []
    return_counts = return_file_counts(required_returns)
    master_summary = master_checklist.get("summary") or {}
    return_rows = return_type_rows(action_plan)
    bundle_rows = handoff_bundle_rows(exp_dir)

    lines = [
        f"# {TITLE}",
        "",
        f"Generated: {now}",
        "",
        "**Status:** internal claim-safe draft, not a submission-ready manuscript.",
        "",
        (
            "This draft intentionally separates completed engineering/evaluation artifacts from final paper claims. "
            "The current package is not EACL-ready because adjudicated human-gold labels, IAA, human-gold scoring, "
            "mapping expert review, NCS-PCF crosswalk expert review, and active-review effort evidence are still pending."
        ),
        "",
        "## Claim Safety Summary",
        "",
        f"- Current claim status: `{status}`",
        f"- Required claim-gate failures: `{required_failures}`",
        f"- Submission audit status counts: `{summary.get('status_counts', {})}`",
        f"- Evaluation chunks: `{run_summary.get('evaluation_chunks', 'missing')}`",
        f"- Silver reference edges: `{run_summary.get('silver_reference_edges', 'missing')}`",
        f"- Human return preflight: `{return_preflight.get('overall_status', 'missing')}`",
        f"- Pre-human handoff validation: `{effective_pre_human.get('overall_status', 'missing')}`",
        f"- Provenance manifest: `{provenance.get('claim_status', 'missing')}`",
        f"- Minimum paper-gate human-return files: `{return_counts['minimum_paper_gate_return_files_present']}/{return_counts['minimum_paper_gate_return_files']}`",
        f"- Optional/strong claim human-return files: `{return_counts['optional_strong_return_files_present']}/{return_counts['optional_strong_return_files']}`",
        f"- Required claim/human-return files: `{return_counts['tracked_human_return_files_present']}/{return_counts['tracked_human_return_files']}`",
        (
            f"- Optional structural review files: "
            f"`{master_summary.get('optional_structural_return_files_present', 0)}/{master_summary.get('optional_structural_return_files', 0)}`"
        ),
        (
            f"- All master return files: "
            f"`{master_summary.get('required_return_files_present', 0) + master_summary.get('optional_structural_return_files_present', 0)}/"
            f"{master_summary.get('required_return_files', return_counts['tracked_human_return_files']) + master_summary.get('optional_structural_return_files', 0)}`"
        ),
        "",
        "### Blocking Items",
        "",
        md_table(["ID", "Requirement", "Next step"], blocking_rows(audit)),
        "",
        "## Abstract Draft",
        "",
        (
            "We study evidence-grounded procedural knowledge graph construction for long, noisy Korean bid and proposal documents. "
            "The proposed CAPE-KG framework anchors extraction to competency questions, retrieves task-specific schema context, "
            "constrains generated nodes and edges to evidence spans, and routes uncertain outputs into active human review. "
            "The current experiment package implements the task definition, schema, prompts, actual LLM baselines, ablations, "
            "public benchmark adapters, provenance manifests, reviewer workbenches, adjudication handoff, mapping expert review handoff, and active-review effort collection. "
            "The package also includes a separate NCS-PCF crosswalk expert-review handoff for Layer2 bridge utility. "
            "Preliminary silver-reference diagnostics suggest that schema, "
            "evidence, and validator components materially change extraction behavior, but final effectiveness claims are deferred "
            "until adjudicated human-gold labels and inter-annotator agreement are complete."
        ),
        "",
        "## Introduction",
        "",
        (
            "Domain knowledge graph construction from enterprise procedure documents requires more than extracting generic triples. "
            "A useful graph must preserve procedural order, decision conditions, artifacts, responsible roles, evidence provenance, "
            "and downstream links to standard taxonomies. CAPE-KG frames this as an information extraction and resource/evaluation problem."
        ),
        "",
        "Current claimable contributions:",
        "",
        "- A competency-question anchored task definition for evidence-grounded procedural KG construction.",
        "- A CAPE schema covering tasks, procedure steps, gateways, guard conditions, artifacts, roles, principles, risks, and evidence anchors.",
        "- Executable actual LLM baselines and ablations over 120 evaluation chunks.",
        "- Layer 2 KG RDF/Turtle export and SHACL-style validation artifacts for ontology, predicate, domain/range, dangling-edge, and evidence-anchor checks.",
        "- File-level provenance manifest and PROV-O Turtle export covering source files, prompts, schemas, LLM raw/valid outputs, evaluation artifacts, handoff files, and release artifacts.",
        "- Public benchmark adapters and model diagnostics for PAGED and Text2KGBench subsets.",
        "- Structured pre-human error analysis with claim scope, taxonomy, actual LLM diagnostics, and human-gold follow-up.",
        "- Human annotation, adjudication, IAA, mapping review, crosswalk review, active-review, and optional structural-review workbenches with an 11-file minimum paper gate, 3 optional/strong claim returns, and 2 optional structural returns in the 16-file master manifest.",
        "",
        "Claims that must remain pending:",
        "",
        "- Superiority over baselines on human-gold edge, node, evidence, ontology, procedural, or CQ metrics.",
        "- Expert-confirmed NCS/PCF mapping P@K, MRR, nDCG@10, accept-rate, and explanation-quality claims.",
        "- Expert-confirmed NCS-PCF crosswalk accept-rate and utility claims.",
        "- Human review efficiency claims based on adjudicated outcomes.",
        "",
        "## Related Work",
        "",
        "- LLM-based KG construction: EDC and SAC-KG motivate structured extraction, canonicalization, verifier, and pruner components.",
        "- Ontology-guided information extraction: Text2KGBench provides ontology-conformance and hallucination-oriented evaluation context.",
        "- Procedural graph extraction: PAGED motivates process element and flow extraction for procedural text.",
        "- Evidence grounding: CAPE-KG treats source evidence anchors as first-class evaluation objects.",
        "",
        "## Task Definition",
        "",
        "Input: a document chunk with sentence/evidence IDs and optional schema/taxonomy context.",
        "",
        "Output:",
        "",
        "- nodes with type, label, confidence, and evidence anchors;",
        "- edges with subject/object labels, predicate, type hints, confidence, and evidence anchors;",
        "- optional NCS/PCF mapping candidates;",
        "- optional Layer2-bridged NCS-PCF crosswalk candidates;",
        "- validation metadata for ontology, procedural, and evidence constraints.",
        "",
        "Core metrics planned for the final paper are edge exact F1, predicate F1, node label F1, evidence F1 or exact match, ontology conformance, procedural consistency, CQ answerability, and mapping P@K/MRR/nDCG@10 plus explanation quality after expert review.",
        "",
        "## Dataset and Annotation",
        "",
        md_table([
            "Item",
            "Current value",
            "Status",
        ], [
            ["Evaluation chunks", run_summary.get("evaluation_chunks", "missing"), "available"],
            ["Silver reference nodes", run_summary.get("silver_reference_nodes", "missing"), "diagnostic only"],
            ["Silver reference edges", run_summary.get("silver_reference_edges", "missing"), "diagnostic only"],
            ["Adjudicated human-gold chunks", current_progress.get("adjudicated_chunks", 0), "pending"],
            ["Human-gold items", 0, "pending"],
            ["Annotation reviewed files", f"{current_progress.get('annotation_present_reviewed_files', 0)}/{current_progress.get('annotation_expected_reviewed_files', 0)}", "pending return"],
            ["Adjudication reviewed file", "present" if current_progress.get("adjudication_reviewed_file_present") else "missing", "pending return"],
            ["Mapping review rows", current_progress.get("mapping_pending_rows", 220), "pending expert review"],
            ["Active-review effort rows", current_progress.get("active_review_effort_expected_rows", 0), "pending reviewer timing"],
            ["Optional all-available annotation chunks", annotation_expansion.get("all_available_chunk_count", "missing"), annotation_expansion.get("claim_status", "missing")],
            ["Optional remaining annotation chunks", annotation_expansion.get("remaining_optional_chunk_count", "missing"), "optional expansion, not current gate"],
            [
                "Optional strong resegmented review units",
                annotation_expansion.get("strong_resegmented_chunk_count", "missing"),
                f"max {annotation_expansion.get('strong_resegmented_max_sentences', 'missing')} source sentences/unit; {annotation_expansion.get('strong_resegmented_claim_status', 'missing')}",
            ],
        ]),
        "",
        "The annotation package and workbench are ready, but the paper must not claim human-gold results until two annotators and adjudication are complete.",
        "",
        "### Human Review Return Manifest",
        "",
        md_table(["Return type", "Required files", "Present files", "Purpose"], return_rows),
        "",
        (
            "The return preflight currently has no validation errors, but all paper-claimable human evidence remains pending until "
            "the 11 minimum files and 3 optional/strong claim files are returned and imported. The 2 optional structural-review "
            "files are tracked in the master manifest as procedural-structure follow-up and do not change the minimum paper gate."
        ),
        "",
        "### Handoff Bundles",
        "",
        md_table(["Bundle", "File", "Files inside", "SHA256"], bundle_rows),
        "",
        "## Method: CAPE-KG",
        "",
        "CAPE-KG consists of the following modules:",
        "",
        "1. CQ-linked schema retrieval.",
        "2. Procedural frame extraction.",
        "3. Evidence-span constrained generation.",
        "4. Ontology and procedural validation.",
        "5. NCS/PCF mapping candidate generation.",
        "6. Layer2-bridged NCS-PCF crosswalk candidate generation.",
        "7. Active review prioritization.",
        "",
        "The current experiment also includes B6, a deterministic SAC-KG-style verifier/pruner approximation. It uses existing generator candidates and applies schema/evidence/domain-range checks. This should be described as an approximation, not a full SAC-KG reproduction.",
        "",
        "## Experiments",
        "",
        "### Baselines and Ablations",
        "",
        md_table(["Condition", "Rows", "Edge F1", "Predicate F1", "Node F1", "Evidence F1", "Parse/error rows"], conditions),
        "",
        "These are silver-reference diagnostics only. Final tables must be regenerated after human-gold annotation and scoring.",
        "",
        "### Evidence Span Granularity",
        "",
        md_table(["Triples", "Components", "Subject exact", "Object exact", "Predicate proxy", "Status"], evidence_spans),
        "",
        "This diagnostic separates sentence-level evidence support from component-level lexical spans. Predicate evidence remains a sentence-level proxy until human-gold span annotation is available.",
        "",
        "### KG Structural Diagnostics",
        "",
        md_table(["Status", "Ontology", "Domain/range errors", "Evidence missing", "Procedural", "Cycles", "CQ answerability"], structural),
        "",
        "This diagnostic checks ontology/domain-range conformance, procedural constraints, and structural CQ answerability on the built KG. It is not a human-gold performance result.",
        "",
        "### Structural Gap Worklist",
        "",
        md_table(["Status", "Review checkpoint candidates", "Gateway branch gaps", "Structural CQ", "Human gate effect"], structural_gap),
        "",
        "This worklist turns structural diagnostics into reviewable follow-up items. It does not automatically modify the KG and does not change the 11-file minimum paper gate.",
        "",
        "### Public Benchmark Adapters",
        "",
        md_table(["Run", "PAGED n", "PAGED node F1", "PAGED edge F1", "Text2KG n", "Relation F1", "Triple F1"], public),
        "",
        "The public benchmark adapter results are useful external diagnostics, not official leaderboard claims.",
        "",
        "### Layer2-Bridged NCS-PCF Crosswalk Candidates",
        "",
        md_table(["Shared Layer2 tasks", "All pairs", "Candidate rows", "Top-K per standard", "Status"], crosswalk),
        "",
        "These are bridge-supported candidate pairs only. Expert review is required before reporting crosswalk precision, accept-rate, or downstream utility.",
        "",
        "### NCS-PCF Crosswalk Expert Review Status",
        "",
        md_table(["Candidates", "Source tasks", "Completed", "Pending", "Hit@5", "Utility", "Status"], crosswalk_expert),
        "",
        "This status table separates candidate generation from expert-confirmed crosswalk utility claims.",
        "",
        "### P minus Active Review Ablation",
        "",
        md_table(["Condition", "Strategy", "Budget", "Errors", "Precision@k", "Lift", "Status"], active_ablation),
        "",
        "This is a silver/proxy scaffold for the active-review ablation in the revised plan. It must be rerun against adjudicated human labels and reviewer effort files before any efficiency claim.",
        "",
        "## Analysis",
        "",
        "- Structured error analysis artifact: `07_reports/error_analysis.md` and `07_reports/error_analysis.json`.",
        "- Error types: unsupported edges, invalid evidence, ontology violations, procedural flow errors, mapping misses, strict JSON recovery issues, and silver/reference mismatch.",
        "- Evidence failure cases: missing anchors, overly broad anchors, and hallucinated support.",
        "- Procedural consistency cases: missing gateways, invalid guard conditions, and artifact-flow direction errors.",
        "- Active review: compare active priority, uncertainty-only, and random review after adjudicated outcomes exist.",
        "",
        "## Required Work Before Submission",
        "",
        md_table(["ID", "Category", "Status", "Claimable", "Requirement"], readiness_rows(audit)),
        "",
        "## Source Artifacts",
        "",
        "- `06_release/submission_readiness_audit.md`",
        "- `06_release/claim_gate_report.md`",
        "- `06_release/paper_tables.md` and `paper_tables.tex`",
        "- `04_evaluation/actual_llm_silver_evaluation_report.md`",
        "- `06_release/provenance_manifest.md`, `06_release/provenance_prov_o.ttl`, and `04_evaluation/provenance_llm_run_index.csv`",
        "- `04_evaluation/structural_evaluation_report.md`",
        "- `outputs/12_rdf/cape_kg_layer2.ttl` and `outputs/12_rdf/cape_kg_shacl_validation_report.md`",
        "- `04_evaluation/structural_gap_worklist_report.md`",
        "- `06_release/human_gate_action_plan.md` and `05_review/human_gate_required_returns.csv`",
        "- `06_release/human_review_return_preflight.md`",
        "- `06_release/human_review_handoff/human_review_handoff_report.md`",
        "- `07_reports/error_analysis.md` and `07_reports/error_analysis.json`",
        "- `07_reports/final_eacl_experiment_report.md`",
        "",
        "## Conclusion",
        "",
        (
            "The current CAPE-KG package is ready for pre-human handoff and internal paper drafting: "
            "the schema, prompts, actual LLM runs, ablations, structural diagnostics, public benchmark adapters, "
            "provenance records, reviewer workbenches, and release manifests are available. "
            "The final paper conclusion must be rewritten after adjudicated human-gold labels, IAA, expert mapping review, "
            "crosswalk review, and active-review effort evidence are returned."
        ),
        "",
        "## Limitations",
        "",
        "- Human-gold annotation, adjudication, and IAA are not complete.",
        "- Silver diagnostics are useful for debugging but cannot support final paper claims.",
        "- Mapping downstream metrics require expert-reviewed NCS/PCF candidate groups.",
        "- Active-review efficiency requires returned reviewer timing/correction files and adjudicated outcomes.",
        "- Raw copyrighted text may not be releasable; release must emphasize schema, prompts, code, derived annotations, and public adapters.",
        "- The SAC-KG-style B6 baseline is an approximation, not a faithful full reproduction.",
        "- Qwen3-32B-AWQ core B0/B1/B2/P diagnostic runs are complete, but all model-scaling scores remain silver/proxy until human-gold scoring.",
        "- Standard Qwen3-32B weights are not currently cached; the current disk state is not suitable for a standard-weight 32B run without freeing additional space.",
        "",
        "## Ethical Considerations",
        "",
        (
            "The release package should avoid exposing copyrighted or sensitive raw source text unless rights are cleared. "
            "The reproducibility path should prioritize schema, prompts, evaluation code, public benchmark adapters, derived annotations, and visualization artifacts."
        ),
        "",
        "## References",
        "",
        "1. EACL 2027 Call for Papers. https://2027.eacl.org/calls/papers/",
        "2. ACL Rolling Review CFP. https://aclrollingreview.org/cfp",
        "3. Chen et al. 2024. SAC-KG: Exploiting Large Language Models as Skilled Automatic Constructors for Domain Knowledge Graph. https://aclanthology.org/2024.acl-long.238/",
        "4. Zhang and Soh. 2024. Extract, Define, Canonicalize: An LLM-based Framework for Knowledge Graph Construction. https://aclanthology.org/2024.emnlp-main.548/",
        "5. Pan et al. 2025. Taxonomy-Driven Knowledge Graph Construction for Domain-Specific Scientific Applications. https://aclanthology.org/2025.findings-acl.223/",
        "6. Mihindukulasooriya et al. 2023. Text2KGBench: A Benchmark for Ontology-Driven Knowledge Graph Generation from Text. https://ar5iv.labs.arxiv.org/html/2308.02357",
        "7. Zhou et al. 2026. TextMineX: Data, Evaluation Framework and Ontology-guided LLM Pipeline for Humanitarian Mine Action. https://aclanthology.org/2026.findings-eacl.130.pdf",
        "8. Du et al. 2024. PAGED: A Benchmark for Procedural Graphs Extraction from Documents. https://aclanthology.org/2024.acl-long.583/",
        "9. Ying et al. 2026. Multi-Agent Procedural Graph Extraction with Structural Feedback. https://aclanthology.org/2026.findings-eacl.158.pdf",
        "10. W3C SHACL. https://www.w3.org/TR/shacl/",
        "11. W3C PROV-O. https://www.w3.org/TR/prov-o/",
    ]
    return "\n".join(lines) + "\n"


def build_status(exp_dir, draft_path):
    audit = read_json(exp_dir / "06_release/submission_readiness_audit.json", {}) or {}
    gate = read_json(exp_dir / "06_release/claim_gate_report.json", {}) or {}
    action_plan = read_json(exp_dir / "06_release/human_gate_action_plan.json", {}) or {}
    master_checklist = read_json(exp_dir / "06_release/human_review_master_checklist_ko.json", {}) or {}
    required_returns = action_plan.get("required_return_files", [])
    return_counts = return_file_counts(required_returns)
    master_summary = master_checklist.get("summary") or {}
    blocking = [item.get("id") for item in audit.get("blocking_items", [])]
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "draft_file": str(draft_path),
        "claim_status": audit.get("claim_status"),
        "submission_ready": False,
        "required_failure_count": gate.get("required_failure_count"),
        "blocking_items": blocking,
        **return_counts,
        "required_human_return_files": return_counts["tracked_human_return_files"],
        "optional_structural_return_files": master_summary.get("optional_structural_return_files", 0),
        "optional_structural_return_files_present": master_summary.get("optional_structural_return_files_present", 0),
        "master_return_files": master_summary.get("required_return_files", return_counts["tracked_human_return_files"])
        + master_summary.get("optional_structural_return_files", 0),
        "master_return_files_present": master_summary.get("required_return_files_present", return_counts["tracked_human_return_files_present"])
        + master_summary.get("optional_structural_return_files_present", 0),
        "return_preflight_status": (read_json(exp_dir / "06_release/human_review_return_preflight.json", {}) or {}).get("overall_status"),
        "pre_human_handoff_status": effective_prehuman_summary(
            read_json(exp_dir / "06_release/pre_human_handoff_validation.json", {}) or {}
        ).get("overall_status"),
        "safe_to_use_as_submission": False,
        "reason": "Human-gold annotation, adjudication, IAA, proposed-method human-gold scoring, mapping expert review, NCS-PCF crosswalk expert review, and active-review effort evidence are still pending.",
    }


def run(args):
    exp_dir = Path(args.experiment_dir)
    draft_path = exp_dir / "07_reports/eacl_paper_draft.md"
    status_path = exp_dir / "06_release/eacl_paper_draft_status.json"
    write_text(draft_path, build_markdown(exp_dir))
    write_json(status_path, build_status(exp_dir, draft_path))
    print(json.dumps({"draft": str(draft_path), "status": str(status_path)}, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
