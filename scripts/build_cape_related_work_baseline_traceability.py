#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build related-work-to-baseline traceability artifacts for CAPE-KG."""

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_OUTPUTS_DIR = Path("outputs")
DEFAULT_PLAN_FILE = Path("AX_EACL_submission_review_revised_plan.md")
CLAIM_STATUS = "related_work_baseline_traceability_ready_not_official_reproduction"


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
    }


def condition_metric(metrics_payload, condition):
    for row in metrics_payload.get("metrics") or []:
        if row.get("condition") == condition:
            return row
    return {}


def fmt_metric(row):
    if not row:
        return "missing"
    return (
        f"rows={row.get('rows', 'n/a')}; "
        f"nodes={row.get('pred_nodes', 'n/a')}; "
        f"edges={row.get('pred_edges', 'n/a')}; "
        f"mappings={row.get('pred_mappings', 'n/a')}; "
        f"predicate_f1={float(row.get('predicate_f1') or 0):.4f}; "
        f"evidence_f1={float(row.get('evidence_f1') or 0):.4f}"
    )


def md_table(headers, rows):
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        values = []
        for header in headers:
            value = row.get(header, "")
            if isinstance(value, list):
                value = "<br>".join(str(v) for v in value)
            values.append(str(value).replace("|", "\\|").replace("\n", "<br>"))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def row(
    reference_id,
    reference_name,
    source_url,
    plan_role,
    local_coverage_type,
    local_conditions,
    evidence_files,
    safe_use,
    not_claimable,
    related_sections,
    metric_summary="",
):
    missing = [item["path"] for item in evidence_files if not item["exists"] or item["bytes"] == 0]
    return {
        "reference_id": reference_id,
        "reference_name": reference_name,
        "source_url": source_url,
        "plan_role": plan_role,
        "local_coverage_type": local_coverage_type,
        "local_conditions": local_conditions,
        "metric_summary": metric_summary,
        "evidence_files": evidence_files,
        "missing_evidence_files": missing,
        "safe_use": safe_use,
        "not_claimable": not_claimable,
        "related_sections": related_sections,
    }


def build_payload(exp_dir, outputs_dir, plan_file):
    exp_dir = Path(exp_dir)
    outputs_dir = Path(outputs_dir)
    plan_file = Path(plan_file)
    release_dir = exp_dir / "06_release"
    eval_dir = exp_dir / "04_evaluation"
    public_dir = exp_dir / "08_public_benchmarks"
    schema_dir = exp_dir / "02_schema"

    metrics = read_json(eval_dir / "actual_llm_silver_metrics.json", {}) or {}
    public_summary = read_json(public_dir / "public_benchmark_crosscheck_summary.json", {}) or {}
    public_stats = public_summary.get("summary") or {}

    b3 = condition_metric(metrics, "B3_edc_style")
    b4 = condition_metric(metrics, "B4_taxonomy_rag")
    b5 = condition_metric(metrics, "B5_procedural_prompt")
    b6 = condition_metric(metrics, "B6_sac_kg_verifier_pruner")

    rows = [
        row(
            "RW01_sac_kg",
            "SAC-KG: generator / verifier / pruner style domain KG construction",
            "https://aclanthology.org/2024.acl-long.238/",
            "Motivates verifier/pruner-style KG construction baseline.",
            "deterministic_approximation_baseline",
            ["B6_sac_kg_verifier_pruner"],
            [
                file_state(schema_dir / "prompts/B6_sac_kg_verifier_pruner_baseline.txt", "B6 prompt"),
                file_state(eval_dir / "actual_llm_silver_metrics.json", "B6 silver/proxy metric row"),
                file_state(release_dir / "method_novelty_positioning.md", "novelty-positioning caveat"),
            ],
            "Use as an approximate verifier/pruner baseline family in setup and ablation discussion.",
            "Do not claim a full SAC-KG reproduction or direct leaderboard comparison.",
            ["Related Work", "Experiments: Baselines", "Limitations"],
            fmt_metric(b6),
        ),
        row(
            "RW02_edc",
            "Extract, Define, Canonicalize (EDC)",
            "https://aclanthology.org/2024.emnlp-main.548/",
            "Motivates open-schema extraction and canonicalization comparison.",
            "style_baseline",
            ["B3_edc_style"],
            [
                file_state(schema_dir / "prompts/B3_edc_style_baseline.txt", "B3 prompt"),
                file_state(eval_dir / "actual_llm_silver_metrics.json", "B3 silver/proxy metric row"),
                file_state(release_dir / "alias_canonicalization_report.md", "canonicalization diagnostic"),
            ],
            "Use as an EDC-style baseline family for open-schema/canonicalization contrast.",
            "Do not claim an exact implementation of the original EDC system.",
            ["Related Work", "Experiments: Baselines", "Analysis"],
            fmt_metric(b3),
        ),
        row(
            "RW03_taxonomy_driven_kg",
            "Taxonomy-driven KG construction / Taxonomy-RAG",
            "https://aclanthology.org/2025.findings-acl.223/",
            "Motivates taxonomy-retrieval baseline and standard-taxonomy bridge framing.",
            "style_baseline_and_downstream_bridge",
            ["B4_taxonomy_rag", "P_minus_Standard_bridge"],
            [
                file_state(schema_dir / "prompts/B4_taxonomy_rag_baseline.txt", "B4 prompt"),
                file_state(eval_dir / "actual_llm_silver_metrics.json", "B4 silver/proxy metric row"),
                file_state(outputs_dir / "08_mapping/l2_ncs_mapping_candidates.jsonl", "Layer2-to-NCS candidates"),
                file_state(outputs_dir / "08_mapping/l2_pcf_mapping_candidates.jsonl", "Layer2-to-PCF candidates"),
                file_state(eval_dir / "mapping_downstream_report.md", "mapping downstream diagnostic"),
            ],
            "Use as taxonomy-retrieval and downstream bridge context.",
            "Do not claim mapping utility before expert labels are returned.",
            ["Related Work", "Method: Standard bridge", "Downstream Evaluation"],
            fmt_metric(b4),
        ),
        row(
            "RW04_text2kgbench",
            "Text2KGBench ontology-driven KG generation benchmark",
            "https://ar5iv.labs.arxiv.org/html/2308.02357",
            "Motivates ontology-conformance and hallucination-oriented public sanity checks.",
            "public_adapter_diagnostic",
            ["public_qwen3_8b_full_adapter_eval"],
            [
                file_state(public_dir / "text2kgbench_cape_adapter_subset.jsonl", "Text2KGBench CAPE adapter subset"),
                file_state(public_dir / "text2kgbench_profile.json", "Text2KGBench local profile"),
                file_state(public_dir / "public_benchmark_crosscheck_summary.json", "public cross-check summary"),
                file_state(public_dir / "public_benchmark_crosscheck_report.md", "public cross-check report"),
            ],
            (
                "Use as auxiliary public benchmark evidence: "
                f"max Text2KG n={public_stats.get('max_single_run_text2kg_items')}; "
                f"best relation F1={public_stats.get('best_text2kg_relation_f1')}."
            ),
            "Do not treat adapter diagnostics as official Text2KGBench leaderboard results or target-corpus final evidence.",
            ["Related Work", "Experiments: Public benchmark adapters", "Limitations"],
        ),
        row(
            "RW05_textminex",
            "TextMineX ontology-guided LLM pipeline",
            "https://aclanthology.org/2026.findings-eacl.130.pdf",
            "Motivates ontology conformance and source-text faithfulness positioning.",
            "conceptual_positioning_with_local_validators",
            ["M5_evidence_grounding", "M7_ontology_validation"],
            [
                file_state(eval_dir / "evidence_span_granularity_report.md", "evidence-span diagnostic"),
                file_state(eval_dir / "structural_evaluation_report.md", "ontology/procedural structural diagnostic"),
                file_state(outputs_dir / "12_rdf/cape_kg_shacl_validation_report.md", "SHACL-style validation report"),
                file_state(release_dir / "metric_traceability_audit.md", "metric-to-output traceability"),
            ],
            "Use as related-work motivation for faithfulness and ontology-guided extraction.",
            "Do not claim TextMineX reproduction or direct comparison.",
            ["Related Work", "Method: Validation", "Faithfulness Evaluation"],
        ),
        row(
            "RW06_paged",
            "PAGED procedural graph extraction benchmark",
            "https://aclanthology.org/2024.acl-long.583/",
            "Motivates procedural graph extraction and public procedural sanity checks.",
            "public_adapter_and_procedural_prompt_baseline",
            ["B5_procedural_prompt", "public_qwen3_8b_full_adapter_eval"],
            [
                file_state(schema_dir / "prompts/B5_procedural_prompt_baseline.txt", "B5 prompt"),
                file_state(eval_dir / "actual_llm_silver_metrics.json", "B5 silver/proxy metric row"),
                file_state(public_dir / "paged_cape_adapter_subset.jsonl", "PAGED CAPE adapter subset"),
                file_state(public_dir / "paged_profile.json", "PAGED local profile"),
                file_state(public_dir / "public_benchmark_crosscheck_summary.json", "public cross-check summary"),
            ],
            (
                "Use as procedural graph extraction context: "
                f"max PAGED n={public_stats.get('max_single_run_paged_items')}; "
                f"best edge F1={public_stats.get('best_paged_edge_f1')}."
            ),
            "Do not treat adapter diagnostics as official PAGED leaderboard results or target-corpus final evidence.",
            ["Related Work", "Experiments: Public benchmark adapters", "Analysis"],
            fmt_metric(b5),
        ),
        row(
            "RW07_multi_agent_procedural_feedback",
            "Multi-agent procedural graph extraction with structural feedback",
            "https://aclanthology.org/2026.findings-eacl.158.pdf",
            "Motivates procedural feedback, structural constraints, and review queues.",
            "conceptual_positioning_with_structural_feedback_artifacts",
            ["M8_procedural_consistency_validator", "M10_active_review_queue"],
            [
                file_state(eval_dir / "procedural_consistency_report.md", "procedural consistency report"),
                file_state(release_dir / "structural_review_action_plan.md", "structural-review action plan"),
                file_state(eval_dir / "active_review_efficiency_report.md", "active-review diagnostic"),
                file_state(release_dir / "active_review_human_effort_plan.md", "human-effort protocol"),
            ],
            "Use as motivation for structural feedback and active review scaffolding.",
            "Do not claim a multi-agent reproduction or human-effort gains before returned timing/correction data.",
            ["Related Work", "Method: Active review", "Analysis"],
        ),
        row(
            "RW08_shacl",
            "W3C SHACL",
            "https://www.w3.org/TR/shacl/",
            "Provides standards context for shape/domain-range validation.",
            "standard_validation_artifact",
            ["M7_ontology_shacl_validator"],
            [
                file_state(schema_dir / "cape_shapes.shacl.ttl", "schema SHACL-style shapes"),
                file_state(outputs_dir / "12_rdf/cape_kg_runtime_shapes.shacl.ttl", "runtime shapes"),
                file_state(outputs_dir / "12_rdf/cape_kg_shacl_validation_summary.json", "validation summary"),
                file_state(outputs_dir / "12_rdf/cape_kg_shacl_validation_report.md", "validation report"),
            ],
            "Use to document validation design and reproducibility.",
            "Do not equate SHACL pass rates with final semantic correctness.",
            ["Method: Validation", "Reproducibility", "Limitations"],
        ),
        row(
            "RW09_prov_o",
            "W3C PROV-O",
            "https://www.w3.org/TR/prov-o/",
            "Provides standards context for provenance of prompts, runs, chunks, and outputs.",
            "standard_provenance_artifact",
            ["provenance_manifest", "provenance_prov_o_export"],
            [
                file_state(release_dir / "provenance_manifest.md", "provenance manifest"),
                file_state(release_dir / "provenance_manifest.json", "provenance manifest JSON"),
                file_state(release_dir / "provenance_prov_o.ttl", "PROV-O TTL export"),
                file_state(release_dir / "provenance_prov_o_report.md", "PROV-O export report"),
            ],
            "Use to document reproducibility and run provenance.",
            "Do not claim that provenance alone resolves private-corpus release rights.",
            ["Reproducibility", "Ethics", "Limitations"],
        ),
    ]

    missing = sorted({item for r in rows for item in r["missing_evidence_files"]})
    direct_conditions = sorted({c for r in rows for c in r["local_conditions"] if c.startswith("B") or c.startswith("P_")})
    public_adapter_rows = [r for r in rows if r["local_coverage_type"].startswith("public_adapter")]
    standard_rows = [r for r in rows if r["local_coverage_type"].startswith("standard_")]
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "claim_status": CLAIM_STATUS,
        "plan_file": rel(plan_file),
        "experiment_dir": rel(exp_dir),
        "outputs_dir": rel(outputs_dir),
        "summary": {
            "claim_status": CLAIM_STATUS,
            "reference_count": len(rows),
            "missing_evidence_file_count": len(missing),
            "direct_llm_condition_count": len(direct_conditions),
            "public_adapter_reference_count": len(public_adapter_rows),
            "standard_reference_count": len(standard_rows),
            "official_reproduction_claim_count": 0,
            "public_benchmark_claim_status": public_stats.get("claim_status"),
            "strong_public_cross_run_present": bool(public_stats.get("strong_cross_run_present")),
            "max_single_run_paged_items": int(public_stats.get("max_single_run_paged_items") or 0),
            "max_single_run_text2kg_items": int(public_stats.get("max_single_run_text2kg_items") or 0),
        },
        "claim_boundary": {
            "safe_scope": "Use for Related Work, baseline motivation, public-adapter scope, validation standards, and reproducibility framing.",
            "not_claimable": "This artifact does not prove official reproductions, benchmark leaderboard standing, target-corpus final performance, or human/expert-reviewed utility.",
            "human_or_expert_gated": True,
        },
        "related_work_rows": rows,
        "missing_evidence_files": missing,
        "source_artifacts": {
            "revised_plan": rel(plan_file),
            "method_novelty_positioning": rel(release_dir / "method_novelty_positioning.json"),
            "public_benchmark_crosscheck": rel(public_dir / "public_benchmark_crosscheck_summary.json"),
            "actual_llm_silver_metrics": rel(eval_dir / "actual_llm_silver_metrics.json"),
            "external_resource_license_report": rel(release_dir / "external_resource_license_report.json"),
        },
    }
    return payload


def write_csv_rows(path, payload):
    fields = [
        "reference_id",
        "reference_name",
        "source_url",
        "plan_role",
        "local_coverage_type",
        "local_conditions",
        "metric_summary",
        "missing_evidence_file_count",
        "safe_use",
        "not_claimable",
        "related_sections",
    ]
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in payload["related_work_rows"]:
            writer.writerow(
                {
                    "reference_id": r["reference_id"],
                    "reference_name": r["reference_name"],
                    "source_url": r["source_url"],
                    "plan_role": r["plan_role"],
                    "local_coverage_type": r["local_coverage_type"],
                    "local_conditions": ";".join(r["local_conditions"]),
                    "metric_summary": r["metric_summary"],
                    "missing_evidence_file_count": len(r["missing_evidence_files"]),
                    "safe_use": r["safe_use"],
                    "not_claimable": r["not_claimable"],
                    "related_sections": ";".join(r["related_sections"]),
                }
            )


def render_md(payload):
    lines = [
        "# CAPE-KG Related Work to Baseline Traceability",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Claim status: `{payload['claim_status']}`",
        f"Plan: `{payload['plan_file']}`",
        "",
        "This artifact maps the revised plan's related-work references to local baselines, public adapters, validators, provenance artifacts, and claim boundaries.",
        "It is not an official reproduction report; it fixes what each reference supports in the paper narrative.",
        "",
        "## Summary",
        "",
    ]
    lines.extend(f"- {key}: `{value}`" for key, value in payload["summary"].items())
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            f"- Safe scope: {payload['claim_boundary']['safe_scope']}",
            f"- Not claimable: {payload['claim_boundary']['not_claimable']}",
            f"- Human/expert gated: `{payload['claim_boundary']['human_or_expert_gated']}`",
            "",
            "## Related Work Matrix",
            "",
        ]
    )
    table_rows = [
        {
            "reference": r["reference_id"],
            "coverage": r["local_coverage_type"],
            "local conditions": r["local_conditions"],
            "missing evidence": len(r["missing_evidence_files"]),
            "safe use": r["safe_use"],
        }
        for r in payload["related_work_rows"]
    ]
    lines.append(md_table(["reference", "coverage", "local conditions", "missing evidence", "safe use"], table_rows))
    for r in payload["related_work_rows"]:
        lines.extend(
            [
                "",
                f"## {r['reference_id']}. {r['reference_name']}",
                "",
                f"- Source URL: {r['source_url']}",
                f"- Plan role: {r['plan_role']}",
                f"- Local coverage type: `{r['local_coverage_type']}`",
                f"- Local conditions/artifacts: `{', '.join(r['local_conditions'])}`",
                f"- Metric summary: {r['metric_summary'] or 'n/a'}",
                f"- Safe use: {r['safe_use']}",
                f"- Not claimable: {r['not_claimable']}",
                f"- Paper sections: `{', '.join(r['related_sections'])}`",
                "",
                "### Evidence Files",
                "",
                md_table(["role", "path", "exists", "bytes"], r["evidence_files"]),
            ]
        )
    lines.extend(["", "## Source Artifacts", ""])
    lines.extend(f"- `{key}`: `{value}`" for key, value in payload["source_artifacts"].items())
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", type=Path, default=DEFAULT_EXP_DIR)
    parser.add_argument("--outputs-dir", type=Path, default=DEFAULT_OUTPUTS_DIR)
    parser.add_argument("--plan-file", type=Path, default=DEFAULT_PLAN_FILE)
    args = parser.parse_args()

    payload = build_payload(args.experiment_dir, args.outputs_dir, args.plan_file)
    release_dir = args.experiment_dir / "06_release"
    json_path = release_dir / "related_work_baseline_traceability.json"
    md_path = release_dir / "related_work_baseline_traceability.md"
    csv_path = release_dir / "related_work_baseline_traceability.csv"
    write_json(json_path, payload)
    write_text(md_path, render_md(payload))
    write_csv_rows(csv_path, payload)
    print(json.dumps({"json": rel(json_path), "markdown": rel(md_path), "csv": rel(csv_path), "claim_status": CLAIM_STATUS}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
