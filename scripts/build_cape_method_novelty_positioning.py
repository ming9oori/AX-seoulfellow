#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build method novelty positioning evidence for the CAPE-KG package."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_OUTPUTS_DIR = Path("outputs")


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


def file_state(path, role, required=True):
    path = Path(path)
    present = path.exists() and path.is_file()
    return {
        "path": rel(path),
        "role": role,
        "required": bool(required),
        "exists": present,
        "bytes": path.stat().st_size if present else 0,
    }


def metric_map(metrics_payload):
    rows = metrics_payload.get("metrics") or []
    return {row.get("condition"): row for row in rows if row.get("condition")}


def condition_output_map(traceability):
    rows = ((traceability.get("llm_condition_outputs") or {}).get("conditions") or [])
    return {row.get("condition"): row for row in rows if row.get("condition")}


def fmt_float(value):
    if value is None or value == "":
        return "n/a"
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return str(value)


def condition_evidence(condition, metrics_by_condition, outputs_by_condition):
    metric = metrics_by_condition.get(condition) or {}
    output = outputs_by_condition.get(condition) or {}
    rows = metric.get("rows", output.get("valid_rows", "n/a"))
    nodes = metric.get("pred_nodes", output.get("nodes", "n/a"))
    edges = metric.get("pred_edges", output.get("edges", "n/a"))
    triples = metric.get("pred_triples", output.get("triples", "n/a"))
    mappings = metric.get("pred_mappings", output.get("mappings", "n/a"))
    predicate_f1 = fmt_float(metric.get("predicate_f1"))
    evidence_f1 = fmt_float(metric.get("evidence_f1"))
    return (
        f"valid rows={rows}; nodes={nodes}; edges={edges}; triples={triples}; "
        f"mappings={mappings}; predicate F1={predicate_f1}; evidence F1={evidence_f1}"
    )


def table_escape(value):
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        value = ", ".join(str(item) for item in value)
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def build_payload(exp_dir, outputs_dir):
    exp_dir = Path(exp_dir)
    outputs_dir = Path(outputs_dir)
    release_dir = exp_dir / "06_release"
    eval_dir = exp_dir / "04_evaluation"

    traceability = read_json(release_dir / "prompt_node_edge_traceability.json", {}) or {}
    method_coverage = read_json(release_dir / "method_module_coverage.json", {}) or {}
    cq_pack = read_json(release_dir / "cq_query_pack.json", {}) or {}
    silver_metrics = read_json(eval_dir / "actual_llm_silver_metrics.json", {}) or {}
    structural = read_json(eval_dir / "structural_evaluation_metrics.json", {}) or {}
    spans = read_json(eval_dir / "evidence_span_granularity_metrics.json", {}) or {}

    metrics_by_condition = metric_map(silver_metrics)
    outputs_by_condition = condition_output_map(traceability)
    final_counts = ((traceability.get("final_kg") or {}).get("counts") or {})
    method_summary = method_coverage.get("summary") or {}
    cq_summary = cq_pack.get("summary") or {}
    structural_conformance = structural.get("ontology_conformance") or {}
    procedural = structural.get("procedural_consistency") or {}

    prior_work_positioning = [
        {
            "family": "Plain LLM triple extraction / Text2KG-style extraction",
            "representative_condition": "B0_plain_llm",
            "what_it_covers": "Open subject-predicate-object extraction from each chunk.",
            "what_cape_adds": "Typed task/procedure nodes, allowed predicates, evidence anchors, CQ-linked schema, and validators.",
            "current_evidence": condition_evidence("B0_plain_llm", metrics_by_condition, outputs_by_condition),
            "claim_boundary": "Current values are silver/proxy diagnostics; final quality gains need adjudicated human-gold scoring.",
        },
        {
            "family": "Predicate-constrained LLM KG extraction",
            "representative_condition": "B1_predicate_constrained",
            "what_it_covers": "Relation extraction with an allowed predicate list.",
            "what_cape_adds": "Node typing, procedural task frames, evidence span tracking, CQ answerability, and standard-taxonomy mapping.",
            "current_evidence": condition_evidence("B1_predicate_constrained", metrics_by_condition, outputs_by_condition),
            "claim_boundary": "Predicate control alone is diagnostic, not a final proposed-method claim.",
        },
        {
            "family": "Current project baseline / task-frame post-processing",
            "representative_condition": "B2_current_project",
            "what_it_covers": "Task-frame extraction followed by Layer 2 schema post-processing.",
            "what_cape_adds": "Full CAPE pipeline adds CQ retrieval, evidence grounding, validators, ablations, and NCS/PCF bridge.",
            "current_evidence": condition_evidence("B2_current_project", metrics_by_condition, outputs_by_condition),
            "claim_boundary": "Useful as an internal baseline; final comparison requires human-gold metrics.",
        },
        {
            "family": "EDC-style open-schema extraction and canonicalization",
            "representative_condition": "B3_edc_style",
            "what_it_covers": "Extract, define, and canonicalize open-schema items before schema-compatible scoring.",
            "what_cape_adds": "Procedural KG schema, CQ-linked query needs, evidence span checks, and release-time claim gates.",
            "current_evidence": condition_evidence("B3_edc_style", metrics_by_condition, outputs_by_condition),
            "claim_boundary": "Baseline approximation is available; do not claim superiority until human-gold scoring.",
        },
        {
            "family": "Taxonomy-RAG / ontology-guided KG extraction",
            "representative_condition": "B4_taxonomy_rag",
            "what_it_covers": "Retrieval of taxonomy snippets before extracting schema-constrained nodes, edges, and mappings.",
            "what_cape_adds": "CAPE treats NCS/PCF as downstream bridge evidence, connects it to procedural KG nodes, and tracks expert-review readiness.",
            "current_evidence": condition_evidence("B4_taxonomy_rag", metrics_by_condition, outputs_by_condition),
            "claim_boundary": "Mapping utility requires expert labels before paper claims.",
        },
        {
            "family": "Procedural prompt / workflow extraction",
            "representative_condition": "B5_procedural_prompt",
            "what_it_covers": "Action, actor, gateway, guard condition, artifact flow, and dependency extraction.",
            "what_cape_adds": "CQ anchoring, schema validation, evidence anchoring, structural diagnostics, and KG query package.",
            "current_evidence": condition_evidence("B5_procedural_prompt", metrics_by_condition, outputs_by_condition),
            "claim_boundary": "Procedural structure is built and diagnosable; correctness still needs human adjudication.",
        },
        {
            "family": "SAC-KG-style verifier/pruner",
            "representative_condition": "B6_sac_kg_verifier_pruner",
            "what_it_covers": "Generate candidate nodes/edges, then verify and prune using schema/evidence constraints.",
            "what_cape_adds": "End-to-end CQ/procedural/mapping/release-gate pipeline rather than verifier/pruner alone.",
            "current_evidence": condition_evidence("B6_sac_kg_verifier_pruner", metrics_by_condition, outputs_by_condition),
            "claim_boundary": "This is a deterministic approximation baseline, not a full reproduction of an external system.",
        },
        {
            "family": "CAPE-KG proposed method",
            "representative_condition": "P_cape_kg_actual",
            "what_it_covers": "CQ-linked schema retrieval, procedural extraction, evidence grounding, validation, and standard bridge.",
            "what_cape_adds": "This is the proposed integrated method rather than a single extraction component.",
            "current_evidence": condition_evidence("P_cape_kg_actual", metrics_by_condition, outputs_by_condition),
            "claim_boundary": "Implemented and traceable now; final performance claim remains pending human-gold scoring.",
        },
    ]

    module_to_novelty_map = [
        {
            "innovation_axis": "Competency-question anchored extraction",
            "modules": ["M2", "M3"],
            "implements": "CQs define what the KG must answer, then guide schema/predicate retrieval and CQ query-pack evaluation.",
            "ablation_or_diagnostic": "P_minus_CQ and P_minus_Schema_retrieval isolate CQ anchoring and schema-retrieval effects.",
            "evidence_files": [
                rel(release_dir / "cq_query_pack.md"),
                rel(release_dir / "prompt_node_edge_traceability.md"),
                rel(outputs_dir / "03_schema/competency_questions.json"),
            ],
            "current_status": f"{cq_summary.get('answerable_cq_count', 'n/a')}/{cq_summary.get('cq_count', 'n/a')} CQs answerable by current KG query diagnostics.",
        },
        {
            "innovation_axis": "Evidence-grounded procedural KG construction",
            "modules": ["M4", "M5", "M6"],
            "implements": "Task/procedure frames are converted into typed nodes and edges with evidence anchors and component-span diagnostics.",
            "ablation_or_diagnostic": "P_minus_Evidence tests evidence grounding; evidence span granularity metrics diagnose span quality.",
            "evidence_files": [
                rel(release_dir / "prompt_node_edge_traceability.md"),
                rel(eval_dir / "evidence_span_granularity_report.md"),
                rel(outputs_dir / "06_triples/layer2_triples_component_spans.jsonl"),
            ],
            "current_status": (
                f"final nodes={final_counts.get('final_nodes', 'n/a')}; "
                f"final edges={final_counts.get('final_edges', 'n/a')}; "
                f"component span exact rate={fmt_float(spans.get('exact_component_span_rate'))}"
            ),
        },
        {
            "innovation_axis": "Ontology and procedural consistency validation",
            "modules": ["M7", "M8"],
            "implements": "Domain/range, predicate, dangling-edge, precedence, gateway, and artifact-flow checks are explicit release artifacts.",
            "ablation_or_diagnostic": "P_minus_Validator and structural evaluation isolate validator/constraint contributions.",
            "evidence_files": [
                rel(eval_dir / "structural_evaluation_report.md"),
                rel(outputs_dir / "12_rdf/cape_kg_shacl_validation_report.md"),
                rel(release_dir / "structural_review_action_plan.md"),
            ],
            "current_status": (
                f"dangling edges={structural_conformance.get('dangling_edge_count', 'n/a')}; "
                f"precedence cycles={procedural.get('precedence_cycle_count', 'n/a')}"
            ),
        },
        {
            "innovation_axis": "Standard taxonomy bridge",
            "modules": ["M11"],
            "implements": "Layer 2 procedural tasks are connected to NCS/PCF candidate mappings and NCS-PCF crosswalk candidates.",
            "ablation_or_diagnostic": "P_minus_Standard_bridge removes the standard bridge output for ablation.",
            "evidence_files": [
                rel(outputs_dir / "08_mapping/l2_ncs_mapping_candidates.jsonl"),
                rel(outputs_dir / "08_mapping/l2_pcf_mapping_candidates.jsonl"),
                rel(eval_dir / "ncs_pcf_crosswalk_report.md"),
            ],
            "current_status": "Candidate mappings exist; downstream utility and accept-rate claims require expert review.",
        },
        {
            "innovation_axis": "Active review and claim-safety gates",
            "modules": ["M10"],
            "implements": "Risky chunks and likely high-impact errors are queued for human review, while release gates prevent overclaiming.",
            "ablation_or_diagnostic": "Active-review ablation metrics and human-effort template separate automatic prioritization from human-time claims.",
            "evidence_files": [
                rel(eval_dir / "active_review_efficiency_report.md"),
                rel(release_dir / "claimable_main_table.md"),
                rel(release_dir / "pre_human_handoff_validation.md"),
            ],
            "current_status": "Automatic queue is ready; effort/time claims require returned human effort sheet.",
        },
    ]

    claimable_now = [
        {
            "claim": "The CAPE-KG pipeline has implemented artifacts for M1-M11.",
            "evidence": (
                f"modules={method_summary.get('module_count', 'n/a')}; "
                f"missing required artifacts={method_summary.get('missing_required_artifact_count', 'n/a')}"
            ),
            "safe_scope": "Implementation and reproducibility setup claim.",
        },
        {
            "claim": "The current corpus has a built Layer 2 procedural KG.",
            "evidence": (
                f"nodes={final_counts.get('final_nodes', 'n/a')}; "
                f"edges={final_counts.get('final_edges', 'n/a')}; "
                f"edges with evidence={final_counts.get('edges_with_evidence', 'n/a')}"
            ),
            "safe_scope": "Built KG artifact claim, not human-validated extraction-quality claim.",
        },
        {
            "claim": "Baseline/proposed/ablation conditions are traceable.",
            "evidence": (
                f"condition metrics={len(metrics_by_condition)}; "
                f"prompt inventory={len(traceability.get('prompt_inventory') or [])}"
            ),
            "safe_scope": "Experimental setup and silver/proxy diagnostic claim.",
        },
        {
            "claim": "CQs are connected to concrete graph queries.",
            "evidence": (
                f"CQs={cq_summary.get('cq_count', 'n/a')}; "
                f"answerable={cq_summary.get('answerable_cq_count', 'n/a')}; "
                f"rate={fmt_float(cq_summary.get('cq_answerability_rate'))}"
            ),
            "safe_scope": "CQ query-package readiness, not final answer correctness.",
        },
    ]

    not_claimable_yet = [
        {
            "claim": "CAPE-KG improves extraction quality over all baselines.",
            "required_next_evidence": "Adjudicated human-gold labels, IAA, and human-gold metrics for proposed and baseline conditions.",
        },
        {
            "claim": "NCS/PCF mapping candidates are useful for downstream expert work.",
            "required_next_evidence": "Expert-reviewed mapping/crosswalk labels and recomputed P@K, MRR, nDCG, accept rate, and utility scores.",
        },
        {
            "claim": "Active review reduces human effort in practice.",
            "required_next_evidence": "Returned human effort sheet with time/correction outcomes and refreshed active-effort metrics.",
        },
        {
            "claim": "The package is submission complete.",
            "required_next_evidence": "All minimum human-gold gates and proposed-method human-gold scoring must pass the claim gate.",
        },
    ]

    source_files = [
        file_state(release_dir / "method_module_coverage.json", "M1-M11 module coverage"),
        file_state(release_dir / "method_module_coverage.md", "M1-M11 module coverage report"),
        file_state(release_dir / "prompt_node_edge_traceability.json", "prompt/output traceability"),
        file_state(release_dir / "prompt_node_edge_traceability.md", "prompt/output traceability report"),
        file_state(release_dir / "cq_query_pack.json", "CQ query pack"),
        file_state(eval_dir / "actual_llm_silver_metrics.json", "silver/proxy baseline diagnostics"),
        file_state(eval_dir / "structural_evaluation_metrics.json", "structural diagnostics"),
        file_state(eval_dir / "evidence_span_granularity_metrics.json", "evidence span diagnostics"),
    ]

    missing_required_sources = [row["path"] for row in source_files if row["required"] and not row["exists"]]
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": rel(exp_dir),
        "outputs_dir": rel(outputs_dir),
        "summary": {
            "claim_status": (
                "method_novelty_positioning_ready_final_gain_pending_human_gold"
                if not missing_required_sources
                else "method_novelty_positioning_missing_sources"
            ),
            "source_file_count": len(source_files),
            "missing_required_source_count": len(missing_required_sources),
            "missing_required_sources": missing_required_sources,
            "method_modules": method_summary.get("module_count"),
            "missing_required_method_artifacts": method_summary.get("missing_required_artifact_count"),
            "llm_condition_metric_count": len(metrics_by_condition),
            "cq_count": cq_summary.get("cq_count"),
            "answerable_cq_count": cq_summary.get("answerable_cq_count"),
            "final_nodes": final_counts.get("final_nodes"),
            "final_edges": final_counts.get("final_edges"),
        },
        "source_files": source_files,
        "prior_work_positioning": prior_work_positioning,
        "module_to_novelty_map": module_to_novelty_map,
        "claimable_now": claimable_now,
        "not_claimable_yet": not_claimable_yet,
    }
    return payload


def render_report(payload):
    summary = payload["summary"]
    lines = [
        "# CAPE-KG Method Novelty Positioning",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Experiment: `{payload['experiment_dir']}`",
        f"Outputs: `{payload['outputs_dir']}`",
        "",
        "This artifact explains what the proposed CAPE-KG pipeline adds beyond common LLM-KG, ontology-guided, taxonomy-RAG, procedural-prompt, and verifier/pruner baselines.",
        "It is a claim-safe positioning artifact: it supports method framing and reproducibility, but it does not replace human-gold evaluation.",
        "",
        "## Summary",
        "",
        f"- Claim status: `{summary['claim_status']}`",
        f"- Method modules tracked: {summary.get('method_modules')}",
        f"- Missing required method artifacts: {summary.get('missing_required_method_artifacts')}",
        f"- LLM condition metric rows: {summary.get('llm_condition_metric_count')}",
        f"- CQs: {summary.get('answerable_cq_count')}/{summary.get('cq_count')} answerable by current graph-query diagnostics",
        f"- Current Layer 2 KG: {summary.get('final_nodes')} nodes, {summary.get('final_edges')} edges",
        "",
        "## Prior-Work Positioning Matrix",
        "",
        "| prior-work family | representative condition | what it covers | what CAPE-KG adds | current evidence | claim boundary |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["prior_work_positioning"]:
        lines.append(
            "| {family} | `{condition}` | {covers} | {adds} | {evidence} | {boundary} |".format(
                family=table_escape(row["family"]),
                condition=table_escape(row["representative_condition"]),
                covers=table_escape(row["what_it_covers"]),
                adds=table_escape(row["what_cape_adds"]),
                evidence=table_escape(row["current_evidence"]),
                boundary=table_escape(row["claim_boundary"]),
            )
        )

    lines += [
        "",
        "## Module-to-Novelty Map",
        "",
        "| innovation axis | modules | implementation | ablation/diagnostic | current status |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in payload["module_to_novelty_map"]:
        lines.append(
            "| {axis} | `{modules}` | {implements} | {diag} | {status} |".format(
                axis=table_escape(row["innovation_axis"]),
                modules=table_escape(", ".join(row["modules"])),
                implements=table_escape(row["implements"]),
                diag=table_escape(row["ablation_or_diagnostic"]),
                status=table_escape(row["current_status"]),
            )
        )
    lines += ["", "### Evidence Files by Innovation Axis", ""]
    for row in payload["module_to_novelty_map"]:
        lines.append(f"#### {row['innovation_axis']}")
        for path in row["evidence_files"]:
            lines.append(f"- `{path}`")
        lines.append("")

    lines += [
        "## What Can Be Claimed Now",
        "",
        "| claim | evidence | safe scope |",
        "| --- | --- | --- |",
    ]
    for row in payload["claimable_now"]:
        lines.append(
            f"| {table_escape(row['claim'])} | {table_escape(row['evidence'])} | {table_escape(row['safe_scope'])} |"
        )

    lines += [
        "",
        "## What Cannot Be Claimed Yet",
        "",
        "| claim to defer | required next evidence |",
        "| --- | --- |",
    ]
    for row in payload["not_claimable_yet"]:
        lines.append(
            f"| {table_escape(row['claim'])} | {table_escape(row['required_next_evidence'])} |"
        )

    lines += [
        "",
        "## Source Files",
        "",
        "| role | path | exists | bytes |",
        "| --- | --- | ---: | ---: |",
    ]
    for row in payload["source_files"]:
        lines.append(
            f"| {table_escape(row['role'])} | `{row['path']}` | {row['exists']} | {row['bytes']} |"
        )
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--outputs-dir", default=str(DEFAULT_OUTPUTS_DIR))
    args = parser.parse_args()

    payload = build_payload(Path(args.experiment_dir), Path(args.outputs_dir))
    release_dir = Path(args.experiment_dir) / "06_release"
    json_path = release_dir / "method_novelty_positioning.json"
    md_path = release_dir / "method_novelty_positioning.md"
    write_json(json_path, payload)
    write_text(md_path, render_report(payload))
    print(
        json.dumps(
            {
                "novelty_json": str(json_path),
                "novelty_report": str(md_path),
                "claim_status": payload["summary"]["claim_status"],
                "missing_required_sources": payload["summary"]["missing_required_sources"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
