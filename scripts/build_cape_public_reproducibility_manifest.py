#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a public-safe reproducibility manifest for CAPE-KG."""

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_OUTPUTS_DIR = Path("outputs")

TEXT_RISK_PATTERNS = (
    "source corpus text",
    "private review package",
    "private source document",
)


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


def file_row(category, description, path, release_status="public_safe", reviewer_value="reproducibility"):
    path = Path(path)
    return {
        "category": category,
        "description": description,
        "path": rel(path),
        "exists": "yes" if path.exists() else "no",
        "bytes": path.stat().st_size if path.exists() else 0,
        "release_status": release_status,
        "reviewer_value": reviewer_value,
    }


def glob_rows(category, description_prefix, pattern, release_status="public_safe", reviewer_value="reproducibility"):
    rows = []
    for path in sorted(Path().glob(pattern)):
        rows.append(file_row(category, f"{description_prefix}: {path.name}", path, release_status, reviewer_value))
    return rows


def build_rows(exp_dir, outputs_dir):
    exp_dir = Path(exp_dir)
    outputs_dir = Path(outputs_dir)
    release_dir = exp_dir / "06_release"
    public_dir = exp_dir / "08_public_benchmarks"
    rows = []

    rows.extend(
        [
            file_row("schema_and_cq", "CAPE node/edge schema", exp_dir / "02_schema/cape_schema.json"),
            file_row("schema_and_cq", "SHACL-style shapes", exp_dir / "02_schema/cape_shapes.shacl.ttl"),
            file_row("schema_and_cq", "Competency questions", exp_dir / "02_schema/competency_questions.json"),
        ]
    )
    rows.extend(glob_rows("prompts", "LLM condition prompt", rel(exp_dir / "02_schema/prompts/*.txt")))
    rows.extend(
        [
            file_row("runtime_code", "LLM condition runner", "scripts/run_cape_llm_condition_baselines.py"),
            file_row("runtime_code", "KG experiment builder", "scripts/build_cape_kg_eacl_experiment.py"),
            file_row("runtime_code", "RDF and SHACL-style exporter", "scripts/export_cape_kg_rdf_shacl.py"),
            file_row("runtime_code", "CQ query pack builder", "scripts/build_cape_cq_query_pack.py"),
            file_row("runtime_code", "Neo4j evidence query pack builder", "scripts/build_cape_neo4j_evidence_query_pack.py", "internal_only", "Neo4j evidence inspection helper"),
            file_row("runtime_code", "Prompt-node-edge traceability builder", "scripts/build_cape_prompt_node_edge_traceability.py"),
            file_row("runtime_code", "Experiment reproduction card builder", "scripts/build_cape_experiment_reproduction_card.py"),
            file_row("runtime_code", "Evidence graph projection builder", "scripts/build_cape_evidence_graph_projection.py"),
            file_row("runtime_code", "Predicate cue span diagnostic builder", "scripts/build_cape_predicate_cue_spans.py"),
            file_row("runtime_code", "Method novelty positioning builder", "scripts/build_cape_method_novelty_positioning.py"),
            file_row("runtime_code", "Qwen3 model-scaling report builder", "scripts/build_cape_qwen3_model_scaling_report.py"),
            file_row("runtime_code", "Gold sampling coverage report builder", "scripts/build_cape_gold_sampling_coverage_report.py"),
            file_row("runtime_code", "Public synthetic example builder", "scripts/build_cape_public_synthetic_examples.py"),
            file_row("runtime_code", "Anonymized submission prep builder", "scripts/build_cape_anonymized_submission_prep.py"),
            file_row("runtime_code", "Responsible NLP checklist prep builder", "scripts/build_cape_responsible_nlp_checklist_prep.py"),
            file_row("runtime_code", "Release bundle builder", "scripts/build_cape_release_bundle.py"),
            file_row("runtime_code", "Pre-human release validator", "scripts/validate_cape_pre_human_handoff.py"),
            file_row("runtime_code", "Pre-human status helper", "scripts/cape_pre_human_status.py"),
            file_row("runtime_code", "Revised plan completion audit builder", "scripts/build_cape_revised_plan_completion_audit.py"),
            file_row(
                "runtime_code",
                "Annotation protocol traceability builder",
                "scripts/build_cape_annotation_protocol_traceability.py",
                "internal_only",
                "human annotation protocol traceability; internal review path references",
            ),
            file_row("runtime_code", "Metric traceability audit builder", "scripts/build_cape_metric_traceability_audit.py"),
            file_row("runtime_code", "Contribution claim traceability builder", "scripts/build_cape_contribution_claim_traceability.py"),
            file_row("runtime_code", "Related-work baseline traceability builder", "scripts/build_cape_related_work_baseline_traceability.py"),
            file_row(
                "runtime_code",
                "Human-review packet integrity builder",
                "scripts/build_cape_human_review_packet_integrity_report.py",
                "internal_only",
                "human-review packet integrity; internal path references",
            ),
        ]
    )
    rows.extend(
        [
            file_row("evaluation_protocol", "Locked evaluation protocol", release_dir / "evaluation_protocol_lock.md"),
            file_row("evaluation_protocol", "Locked evaluation protocol JSON", release_dir / "evaluation_protocol_lock.json"),
            file_row("evaluation_protocol", "Claim-safe paper tables", release_dir / "paper_tables.md", "live_release_status"),
            file_row("evaluation_protocol", "Claim-safe paper tables LaTeX", release_dir / "paper_tables.tex", "live_release_status"),
            file_row("evaluation_protocol", "Claimability table", release_dir / "claimable_main_table.md", "live_release_status"),
            file_row("evaluation_protocol", "Experiment reproduction card", release_dir / "experiment_reproduction_card.md", "live_release_status"),
            file_row("evaluation_protocol", "Experiment reproduction card JSON", release_dir / "experiment_reproduction_card.json", "live_release_status"),
            file_row("evaluation_protocol", "Experiment reproduction condition CSV", release_dir / "experiment_reproduction_conditions.csv", "live_release_status"),
            file_row("evaluation_protocol", "RQ evidence matrix", release_dir / "rq_evidence_matrix.md", "live_release_status"),
            file_row("evaluation_protocol", "Public-safe revised plan completion audit", release_dir / "revised_plan_completion_audit_public_safe.md"),
            file_row("evaluation_protocol", "Public-safe revised plan completion audit JSON", release_dir / "revised_plan_completion_audit_public_safe.json"),
            file_row("evaluation_protocol", "Public-safe revised plan completion audit CSV", release_dir / "revised_plan_completion_audit_public_safe_items.csv"),
            file_row("evaluation_protocol", "Metric traceability audit", release_dir / "metric_traceability_audit.md"),
            file_row("evaluation_protocol", "Metric traceability audit JSON", release_dir / "metric_traceability_audit.json"),
            file_row("evaluation_protocol", "Metric traceability audit CSV", release_dir / "metric_traceability_audit.csv"),
            file_row("evaluation_protocol", "Contribution claim traceability", release_dir / "contribution_claim_traceability.md"),
            file_row("evaluation_protocol", "Contribution claim traceability JSON", release_dir / "contribution_claim_traceability.json"),
            file_row("evaluation_protocol", "Contribution claim traceability CSV", release_dir / "contribution_claim_traceability.csv"),
            file_row("evaluation_protocol", "Related-work baseline traceability", release_dir / "related_work_baseline_traceability.md"),
            file_row("evaluation_protocol", "Related-work baseline traceability JSON", release_dir / "related_work_baseline_traceability.json"),
            file_row("evaluation_protocol", "Related-work baseline traceability CSV", release_dir / "related_work_baseline_traceability.csv"),
            file_row(
                "evaluation_protocol",
                "Annotation protocol traceability",
                release_dir / "annotation_protocol_traceability.md",
                "internal_only",
                "human annotation protocol traceability; internal review path references",
            ),
            file_row(
                "evaluation_protocol",
                "Annotation protocol traceability JSON",
                release_dir / "annotation_protocol_traceability.json",
                "internal_only",
                "human annotation protocol traceability; internal review path references",
            ),
            file_row(
                "evaluation_protocol",
                "Annotation protocol traceability CSV",
                release_dir / "annotation_protocol_traceability.csv",
                "internal_only",
                "human annotation protocol traceability; internal review path references",
            ),
            file_row("evaluation_protocol", "Method novelty positioning", release_dir / "method_novelty_positioning.md", "live_release_status"),
            file_row("evaluation_protocol", "Method novelty positioning JSON", release_dir / "method_novelty_positioning.json", "live_release_status"),
            file_row("evaluation_protocol", "Qwen3 model-scaling report", release_dir / "qwen3_model_scaling_report.md", "live_release_status"),
            file_row("evaluation_protocol", "Qwen3 model-scaling report JSON", release_dir / "qwen3_model_scaling_report.json", "live_release_status"),
            file_row("evaluation_protocol", "CQ query pack", release_dir / "cq_query_pack.md"),
            file_row("traceability", "Prompt to node/edge traceability", release_dir / "prompt_node_edge_traceability.md"),
            file_row("traceability", "Prompt to node/edge traceability JSON", release_dir / "prompt_node_edge_traceability.json"),
            file_row("traceability", "Evidence graph projection report", outputs_dir / "13_evidence_graph/evidence_graph_projection_report.md", "internal_only", "source-grounded graph projection; source text omitted"),
            file_row("traceability", "Evidence graph projection summary", outputs_dir / "13_evidence_graph/evidence_graph_projection_summary.json", "internal_only", "source-grounded graph projection; source text omitted"),
            file_row("traceability", "Predicate cue span diagnostic report", exp_dir / "04_evaluation/predicate_cue_span_report.md", "internal_only", "automatic predicate cue diagnostic; source text omitted"),
            file_row("traceability", "Predicate cue span diagnostic metrics", exp_dir / "04_evaluation/predicate_cue_span_metrics.json", "internal_only", "automatic predicate cue diagnostic; source text omitted"),
            file_row("traceability", "Predicate cue span diagnostic rows", exp_dir / "04_evaluation/predicate_cue_span_rows.csv", "internal_only", "automatic predicate cue diagnostic; source text omitted"),
            file_row("traceability", "Predicate cue span JSONL", outputs_dir / "06_triples/layer2_predicate_cue_spans.jsonl", "internal_only", "automatic predicate cue diagnostic; source text omitted"),
            file_row("traceability", "Neo4j evidence query pack", release_dir / "neo4j_evidence_query_pack.md", "internal_only", "Neo4j Browser queries for EvidenceAnchor/EVIDENCED_BY inspection"),
            file_row("traceability", "Neo4j evidence query pack JSON", release_dir / "neo4j_evidence_query_pack.json", "internal_only", "Neo4j Browser queries for EvidenceAnchor/EVIDENCED_BY inspection"),
        ]
    )
    rows.extend(
        [
            file_row("synthetic_public_examples", "Synthetic example README", release_dir / "public_synthetic_examples/README.md"),
            file_row("synthetic_public_examples", "Synthetic chunks", release_dir / "public_synthetic_examples/synthetic_chunks.jsonl"),
            file_row("synthetic_public_examples", "Synthetic gold labels", release_dir / "public_synthetic_examples/synthetic_gold.jsonl"),
            file_row("synthetic_public_examples", "Synthetic predictions", release_dir / "public_synthetic_examples/synthetic_predictions.jsonl"),
            file_row("synthetic_public_examples", "Synthetic evaluation summary", release_dir / "public_synthetic_examples/synthetic_evaluation_summary.json"),
        ]
    )
    rows.extend(
        [
            file_row("public_benchmarks", "Public benchmark manifest", public_dir / "public_benchmark_manifest.json"),
            file_row("public_benchmarks", "Public benchmark adapter report", public_dir / "public_benchmark_adapter_report.md"),
            file_row("public_benchmarks", "Public benchmark cross-check report", public_dir / "public_benchmark_crosscheck_report.md"),
            file_row("public_benchmarks", "Public benchmark cross-check summary", public_dir / "public_benchmark_crosscheck_summary.json"),
            file_row("public_benchmarks", "Qwen3 8B subset report", public_dir / "public_qwen3_8b_subset_eval_report.md"),
            file_row("public_benchmarks", "Qwen3 8B subset summary", public_dir / "public_qwen3_8b_subset_eval_summary.json"),
            file_row("public_benchmarks", "Qwen3 14B subset report", public_dir / "public_qwen3_14b_subset_eval_report.md"),
            file_row("public_benchmarks", "Qwen3 14B subset summary", public_dir / "public_qwen3_14b_subset_eval_summary.json"),
        ]
    )
    rows.extend(
        [
            file_row("release_safety", "Data release and ethics statement", release_dir / "data_release_ethics_statement.md"),
            file_row("release_safety", "External resource license report", release_dir / "external_resource_license_report.md"),
            file_row("release_safety", "External resource license report JSON", release_dir / "external_resource_license_report.json"),
            file_row("release_safety", "Release bundle safety report", release_dir / "release_bundle_safety_report.md", "live_release_status"),
            file_row("release_safety", "Latest release bundle index", release_dir / "latest_release_bundle_index.md", "live_release_status"),
        ]
    )
    rows.extend(
        [
            file_row("internal_only", "Full graph visualization and source-grounded graph files", outputs_dir / "09_visualization/kg_viewer.html", "internal_only", "demo; inspect before public release"),
            file_row("internal_only", "Full graph RDF export", outputs_dir / "12_rdf/cape_kg_layer2.ttl", "internal_only", "derived graph; inspect before public release"),
            file_row("internal_only", "Neo4j source-grounded import package", outputs_dir / "11_neo4j_import_flat/README.md", "internal_only", "derived graph; includes EvidenceAnchor projection without source text"),
            file_row("internal_only", "Neo4j source-grounded import validation", outputs_dir / "11_neo4j_import_flat/neo4j_csv_validation_report.md", "internal_only", "parser and evidence-projection validation"),
            file_row("internal_only", "Neo4j source-grounded evidence Cypher queries", outputs_dir / "11_neo4j_import_flat/neo4j_evidence_queries.cypher", "internal_only", "Neo4j Browser query helper; source text omitted"),
            file_row("internal_only", "EvidenceAnchor node projection", outputs_dir / "13_evidence_graph/evidence_anchor_nodes.jsonl", "internal_only", "derived graph; source text omitted"),
            file_row("internal_only", "EVIDENCED_BY edge projection", outputs_dir / "13_evidence_graph/evidenced_by_edges.jsonl", "internal_only", "derived graph; source text omitted"),
            file_row("internal_only", "Gold subset sampling coverage report", release_dir / "gold_sampling_coverage_report.md", "internal_only", "private review selection evidence"),
        ]
    )
    return rows


def category_summary(rows):
    summary = {}
    for row in rows:
        cat = row["category"]
        item = summary.setdefault(cat, {"total": 0, "present": 0, "public_safe": 0, "internal_only": 0})
        item["total"] += 1
        if row["exists"] == "yes":
            item["present"] += 1
        if row["release_status"] == "public_safe":
            item["public_safe"] += 1
        if row["release_status"] == "internal_only":
            item["internal_only"] += 1
    return summary


def scan_generated_text(rows):
    text = json.dumps(rows, ensure_ascii=False)
    return [pattern for pattern in TEXT_RISK_PATTERNS if pattern in text]


def md_table(headers, rows):
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(h, "")).replace("|", "\\|") for h in headers) + " |")
    return "\n".join(lines)


def render_markdown(payload):
    lines = [
        "# CAPE-KG Public Reproducibility Manifest",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Experiment: `{payload['experiment_dir']}`",
        "",
        "This manifest maps the reproducibility material promised in the EACL plan to public-safe artifacts. It is not a performance-result claim.",
        "",
        "## Claim Status",
        "",
        f"- Claim status: `{payload['claim_status']}`",
        f"- Public-safe rows: {payload['summary']['public_safe_rows']}",
        f"- Internal-only rows: {payload['summary']['internal_only_rows']}",
        f"- Missing rows: {payload['summary']['missing_rows']}",
        f"- Text-risk hits in manifest payload: {len(payload['text_risk_hits'])}",
        "",
        "## Requirement Coverage",
        "",
        md_table(["requirement", "status", "evidence"], payload["requirement_coverage"]),
        "",
        "## Category Summary",
        "",
        md_table(["category", "total", "present", "public_safe", "internal_only"], [{"category": k, **v} for k, v in sorted(payload["category_summary"].items())]),
        "",
        "## Artifact Rows",
        "",
        md_table(["category", "description", "path", "exists", "release_status", "reviewer_value"], payload["artifact_rows"]),
        "",
        "## Notes",
        "",
        "- The source corpus itself is not part of the public-safe skeleton.",
        "- Synthetic examples are only format and release-safety artifacts.",
        "- Public benchmark rows are auxiliary generalization evidence, not the main private-domain human-gold result.",
        "- Final submission-level claims still require human-gold and expert-review returns.",
        "",
    ]
    return "\n".join(lines)


def build_payload(exp_dir, outputs_dir):
    exp_dir = Path(exp_dir)
    release_dir = exp_dir / "06_release"
    rows = build_rows(exp_dir, outputs_dir)
    missing = [row for row in rows if row["exists"] != "yes"]
    public_safe_rows = [row for row in rows if row["release_status"] == "public_safe"]
    internal_rows = [row for row in rows if row["release_status"] == "internal_only"]
    requirement_coverage = [
        {
            "requirement": "schema",
            "status": "covered" if any(row["category"] == "schema_and_cq" and row["exists"] == "yes" for row in rows) else "missing",
            "evidence": "CAPE schema, SHACL-style shapes, competency questions",
        },
        {
            "requirement": "prompts",
            "status": "covered" if sum(1 for row in rows if row["category"] == "prompts" and row["exists"] == "yes") >= 8 else "missing",
            "evidence": "condition prompts plus strict JSON contract",
        },
        {
            "requirement": "code",
            "status": "covered" if sum(1 for row in rows if row["category"] == "runtime_code" and row["exists"] == "yes") >= 8 else "missing",
            "evidence": "runners, builders, exporters, release validator",
        },
        {
            "requirement": "evaluation protocol",
            "status": "covered" if any(row["description"] == "Locked evaluation protocol" and row["exists"] == "yes" for row in rows) else "missing",
            "evidence": "locked metrics, condition sets, claim policy",
        },
        {
            "requirement": "derived public examples",
            "status": "covered" if sum(1 for row in rows if row["category"] == "synthetic_public_examples" and row["exists"] == "yes") >= 5 else "missing",
            "evidence": "synthetic chunks, gold, predictions, summary",
        },
        {
            "requirement": "public benchmark cross-check",
            "status": "covered" if sum(1 for row in rows if row["category"] == "public_benchmarks" and row["exists"] == "yes") >= 6 else "missing",
            "evidence": "adapter, cross-check, Qwen3 public benchmark summaries",
        },
        {
            "requirement": "release safety",
            "status": "covered" if sum(1 for row in rows if row["category"] == "release_safety" and row["exists"] == "yes") >= 4 else "missing",
            "evidence": "ethics, license, safety, latest bundle index",
        },
    ]
    text_risk_hits = scan_generated_text(rows)
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": rel(exp_dir),
        "outputs_dir": rel(outputs_dir),
        "claim_status": "public_reproducibility_manifest_ready_not_submission_complete",
        "summary": {
            "artifact_rows": len(rows),
            "public_safe_rows": len(public_safe_rows),
            "internal_only_rows": len(internal_rows),
            "missing_rows": len(missing),
            "covered_requirements": sum(1 for row in requirement_coverage if row["status"] == "covered"),
            "total_requirements": len(requirement_coverage),
        },
        "requirement_coverage": requirement_coverage,
        "category_summary": category_summary(rows),
        "artifact_rows": rows,
        "text_risk_hits": text_risk_hits,
        "outputs": {
            "markdown": rel(release_dir / "public_reproducibility_manifest.md"),
            "json": rel(release_dir / "public_reproducibility_manifest.json"),
            "csv": rel(release_dir / "public_reproducibility_manifest.csv"),
        },
    }


def run(args):
    payload = build_payload(args.experiment_dir, args.outputs_dir)
    outputs = payload["outputs"]
    write_json(outputs["json"], payload)
    write_csv(
        outputs["csv"],
        payload["artifact_rows"],
        ["category", "description", "path", "exists", "bytes", "release_status", "reviewer_value"],
    )
    write_text(outputs["markdown"], render_markdown(payload))
    print(json.dumps(outputs, ensure_ascii=False, indent=2))


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--outputs-dir", default=str(DEFAULT_OUTPUTS_DIR))
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
