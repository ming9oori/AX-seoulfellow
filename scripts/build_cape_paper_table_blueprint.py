#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a claim-safe paper table blueprint for CAPE-KG."""

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from cape_pre_human_status import effective_prehuman_summary


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_PLAN_FILE = Path("AX_EACL_submission_review_revised_plan.md")
READY_STATUS = "paper_table_blueprint_ready_not_submission_complete"


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
    return Path(path).as_posix()


def file_state(path):
    path = Path(path)
    present = path.exists() and path.is_file()
    return {
        "path": rel(path),
        "exists": present,
        "bytes": path.stat().st_size if present else 0,
    }


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


def table_spec(
    table_id,
    paper_location,
    title,
    rq,
    current_status,
    current_use,
    target_metrics,
    evidence_paths,
    promotion_gate,
    final_claim_allowed,
    caption_stub,
):
    evidence = [file_state(path) for path in evidence_paths]
    missing = [row["path"] for row in evidence if not row["exists"] or row["bytes"] == 0]
    return {
        "table_id": table_id,
        "paper_location": paper_location,
        "title": title,
        "rq": rq,
        "current_status": current_status,
        "current_use": current_use,
        "target_metrics": target_metrics,
        "evidence_files": evidence,
        "missing_evidence_files": missing,
        "promotion_gate": promotion_gate,
        "final_claim_allowed": final_claim_allowed,
        "caption_stub": caption_stub,
    }


def build_tables(exp_dir, plan_file):
    exp_dir = Path(exp_dir)
    release = exp_dir / "06_release"
    evaluation = exp_dir / "04_evaluation"
    public_bench = exp_dir / "08_public_benchmarks"
    outputs = Path("outputs")
    return [
        table_spec(
            "T01_dataset_annotation_status",
            "main: Dataset and Annotation",
            "Dataset, annotation, and review-gate status",
            "Dataset",
            "setup_claimable_human_gold_pending",
            "main_table_setup_only",
            ["evaluation chunks", "priority gold subset", "adjudicated chunks", "gold items", "return files"],
            [
                release / "paper_tables.md",
                release / "gold_sampling_coverage_report.md",
                release / "human_review_status_dashboard_ko.md",
                evaluation / "human_gold_validation_summary.json",
            ],
            "human-gold annotation and adjudication",
            False,
            "Dataset and annotation status for the Korean bid/proposal procedural KG extraction benchmark.",
        ),
        table_spec(
            "T02_main_extraction_human_gold",
            "main: Main Results",
            "Human-gold extraction performance",
            "RQ1",
            "pending_human_gold",
            "placeholder_only",
            ["Node F1", "Edge F1", "Evidence EM", "Evidence IoU", "Unsupported Edge Rate"],
            [
                release / "post_human_scoring_readiness.md",
                evaluation / "human_gold_metrics.json",
                evaluation / "human_gold_span_iou_metrics.json",
                release / "claim_gate_report.md",
            ],
            "gold.completed_chunks, gold.item_count, gold.iaa, llm.proposed_human_gold_score",
            False,
            "Main extraction results against adjudicated human-gold nodes, edges, and evidence spans.",
        ),
        table_spec(
            "T03_cq_schema_ablation",
            "main: Ablation Studies",
            "CAPE-KG module ablations",
            "RQ2",
            "diagnostic_only_until_human_gold",
            "diagnostic_or_appendix_until_gold",
            ["P - CQ", "P - Schema retrieval", "P - Procedural schema", "P - Validator", "Ontology conformance", "CQ answerability"],
            [
                release / "paper_tables.md",
                evaluation / "actual_llm_silver_metrics.json",
                evaluation / "cq_answerability_by_condition.csv",
                evaluation / "structural_evaluation_metrics.json",
                release / "rq_evidence_matrix.md",
            ],
            "human-gold scoring for ablation conditions",
            False,
            "Ablation results for CQ anchoring, schema retrieval, procedural schema constraints, and validators.",
        ),
        table_spec(
            "T04_structural_cq_diagnostics",
            "main or appendix: Structural Analysis",
            "Ontology, procedural consistency, and CQ answerability diagnostics",
            "RQ2",
            "structural_diagnostic_ready",
            "main_structural_diagnostic_with_claim_safety",
            ["Ontology conformance", "Procedural consistency", "Cycle count", "Gateway branch gaps", "CQ answerability"],
            [
                evaluation / "structural_evaluation_report.md",
                evaluation / "ontology_conformance_metrics.json",
                evaluation / "procedural_consistency_metrics.json",
                evaluation / "cq_answerability_structural_metrics.json",
                release / "cq_query_pack.md",
            ],
            "human confirmation for semantic correctness claims",
            False,
            "Automatic structural diagnostics for the constructed Layer 2 procedural KG.",
        ),
        table_spec(
            "T05_public_benchmark_adapter",
            "appendix or auxiliary main: Public Benchmark",
            "Public benchmark adapter diagnostics",
            "External validity",
            "auxiliary_claimable_not_main_private_result",
            "auxiliary_or_appendix",
            ["PAGED node/edge F1", "Text2KG relation/triple F1", "run size"],
            [
                public_bench / "public_benchmark_crosscheck_report.md",
                public_bench / "public_benchmark_crosscheck_summary.json",
                release / "public_reproducibility_manifest.md",
            ],
            "none before human return; keep auxiliary scope",
            True,
            "Auxiliary public-benchmark adapter diagnostics; not a substitute for target-corpus human-gold results.",
        ),
        table_spec(
            "T06_mapping_downstream",
            "main or appendix: Downstream Mapping",
            "Layer2-to-NCS/PCF mapping utility",
            "RQ3",
            "pending_expert_review",
            "candidate_generation_only",
            ["P@1", "P@5", "MRR", "nDCG@10", "expert accept rate", "explanation quality"],
            [
                evaluation / "mapping_downstream_report.md",
                release / "mapping_review_progress_report.md",
                evaluation / "mapping_expert_metrics.json",
                release / "rq_evidence_matrix.md",
            ],
            "mapping.expert_review",
            False,
            "Expert-reviewed downstream standard-taxonomy alignment performance.",
        ),
        table_spec(
            "T07_crosswalk_downstream",
            "appendix or downstream analysis",
            "Layer2-bridged NCS-PCF crosswalk utility",
            "RQ3",
            "pending_expert_review",
            "candidate_generation_only",
            ["accept rate", "Hit@K", "P@10", "MRR", "nDCG@10", "utility", "explanation quality"],
            [
                evaluation / "ncs_pcf_crosswalk_report.md",
                evaluation / "ncs_pcf_crosswalk_summary.json",
                evaluation / "crosswalk_expert_metrics.json",
            ],
            "crosswalk.expert_review",
            False,
            "Expert-reviewed utility of Layer2-bridged NCS-PCF crosswalk candidates.",
        ),
        table_spec(
            "T08_active_review_efficiency",
            "appendix or analysis: Human-in-the-loop",
            "Active-review efficiency",
            "RQ4",
            "pending_human_effort",
            "pool_design_only",
            ["review seconds", "corrections", "high-impact corrections", "precision@k", "lift vs random"],
            [
                release / "active_review_human_effort_plan.md",
                evaluation / "active_review_human_effort_metrics.json",
                evaluation / "active_review_ablation_metrics.json",
                evaluation / "active_review_pool_overlap_summary.json",
            ],
            "active-review human effort return and adjudicated outcomes",
            False,
            "Human-effort efficiency of active-review prioritization compared with control queues.",
        ),
        table_spec(
            "T09_reproducibility_release",
            "main: Reproducibility / appendix",
            "Reproducibility and release artifacts",
            "Reproducibility",
            "claimable_setup_rights_review_required",
            "main_setup_or_appendix",
            ["schema", "prompts", "code", "public-safe bundle", "PROV-O", "RDF/SHACL", "synthetic examples"],
            [
                release / "public_reproducibility_manifest.md",
                release / "release_bundle_safety_report.md",
                release / "provenance_manifest.md",
                release / "provenance_prov_o_report.md",
                outputs / "12_rdf/cape_kg_shacl_validation_report.md",
                release / "public_synthetic_examples/README.md",
            ],
            "rights review before source-text release",
            True,
            "Release and reproducibility artifacts supporting a public-safe replication path.",
        ),
    ]


def build_payload(exp_dir, plan_file):
    exp_dir = Path(exp_dir)
    release = exp_dir / "06_release"
    tables = build_tables(exp_dir, plan_file)
    missing = [path for row in tables for path in row["missing_evidence_files"]]
    status_counts = Counter(row["current_status"] for row in tables)
    use_counts = Counter(row["current_use"] for row in tables)
    validation = read_json(release / "pre_human_handoff_validation.json", {}) or {}
    effective_validation = effective_prehuman_summary(validation)
    claim_gate = read_json(release / "claim_gate_report.json", {}) or {}
    readiness = read_json(release / "post_human_scoring_readiness.json", {}) or {}

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "plan_file": rel(plan_file),
        "experiment_dir": rel(exp_dir),
        "overall_status": "PASS" if not missing else "FAIL",
        "claim_status": READY_STATUS if not missing else "paper_table_blueprint_incomplete",
        "safe_to_use_as_submission": False,
        "submission_ready": False,
        "summary": {
            "table_count": len(tables),
            "final_claim_allowed_now_count": sum(1 for row in tables if row["final_claim_allowed"]),
            "pending_human_or_expert_table_count": sum(
                1
                for row in tables
                if row["current_status"] in {"pending_human_gold", "pending_expert_review", "pending_human_effort"}
            ),
            "diagnostic_or_setup_table_count": sum(
                1
                for row in tables
                if row["current_status"] not in {"pending_human_gold", "pending_expert_review", "pending_human_effort"}
            ),
            "missing_evidence_files": len(missing),
            "status_counts": dict(sorted(status_counts.items())),
            "current_use_counts": dict(sorted(use_counts.items())),
            "pre_human_validation_status": effective_validation.get("overall_status"),
            "pre_human_validation_checks": effective_validation.get("check_count"),
            "claim_gate_overall_status": claim_gate.get("overall_status"),
            "claim_gate_required_failures": claim_gate.get("required_failure_count"),
            "claim_gate_optional_failures": claim_gate.get("optional_failure_count"),
            "post_human_scoring_claim_status": readiness.get("claim_status"),
        },
        "tables": tables,
        "missing_evidence_files": missing,
    }


def render_markdown(payload):
    summary = payload["summary"]
    rows = [
        {
            "table_id": row["table_id"],
            "paper_location": row["paper_location"],
            "rq": row["rq"],
            "current_status": row["current_status"],
            "current_use": row["current_use"],
            "promotion_gate": row["promotion_gate"],
        }
        for row in payload["tables"]
    ]
    lines = [
        "# CAPE-KG Paper Table Blueprint",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Plan: `{payload['plan_file']}`",
        f"Experiment: `{payload['experiment_dir']}`",
        "",
        "이 문서는 revised EACL plan의 RQ/metric을 논문 표 배치로 고정한 blueprint입니다.",
        "현재 `paper_tables.md`의 값을 대체하지 않으며, 어떤 표를 main result로 둘 수 있고 어떤 표는 diagnostic/appendix/pending으로 둬야 하는지 구분합니다.",
        "",
        "## Summary",
        "",
        md_table(
            ["Item", "Value"],
            [
                {"Item": "Overall status", "Value": payload["overall_status"]},
                {"Item": "Claim status", "Value": payload["claim_status"]},
                {"Item": "Safe to use as submission", "Value": payload["safe_to_use_as_submission"]},
                {"Item": "Submission ready", "Value": payload["submission_ready"]},
                {"Item": "Table count", "Value": summary["table_count"]},
                {"Item": "Final-claim allowed now", "Value": summary["final_claim_allowed_now_count"]},
                {"Item": "Pending human/expert tables", "Value": summary["pending_human_or_expert_table_count"]},
                {"Item": "Missing evidence files", "Value": summary["missing_evidence_files"]},
                {"Item": "Claim gate", "Value": summary["claim_gate_overall_status"]},
                {"Item": "Pre-human validation", "Value": summary["pre_human_validation_status"]},
                {"Item": "Pre-human checks", "Value": summary["pre_human_validation_checks"]},
            ],
        ),
        "",
        "## Table Blueprint",
        "",
        md_table(["table_id", "paper_location", "rq", "current_status", "current_use", "promotion_gate"], rows),
        "",
        "## Detailed Table Specs",
        "",
    ]
    for row in payload["tables"]:
        lines.extend(
            [
                f"### {row['table_id']}. {row['title']}",
                "",
                f"- Paper location: {row['paper_location']}",
                f"- RQ: `{row['rq']}`",
                f"- Current status: `{row['current_status']}`",
                f"- Current use: `{row['current_use']}`",
                f"- Promotion gate: {row['promotion_gate']}",
                f"- Final claim allowed now: `{row['final_claim_allowed']}`",
                f"- Caption stub: {row['caption_stub']}",
                f"- Target metrics: {', '.join(row['target_metrics'])}",
                "",
                md_table(
                    ["path", "exists", "bytes"],
                    [
                        {"path": evidence["path"], "exists": evidence["exists"], "bytes": evidence["bytes"]}
                        for evidence in row["evidence_files"]
                    ],
                ),
                "",
            ]
        )
    lines.extend(
        [
            "## Claim Policy",
            "",
            "- `placeholder_only`, `candidate_generation_only`, `pool_design_only`, and `diagnostic_or_appendix_until_gold` rows must not be promoted to final main results before their promotion gates pass.",
            "- Public benchmark and reproducibility tables can be used only with their auxiliary/setup scope.",
            "- Main extraction and ablation superiority claims require adjudicated human-gold scoring.",
            "- Mapping/crosswalk tables require expert-reviewed labels.",
            "- This artifact intentionally keeps `safe_to_use_as_submission=false` and `submission_ready=false`.",
            "",
        ]
    )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", type=Path, default=DEFAULT_EXP_DIR)
    parser.add_argument("--plan-file", type=Path, default=DEFAULT_PLAN_FILE)
    args = parser.parse_args()

    payload = build_payload(args.experiment_dir, args.plan_file)
    release = args.experiment_dir / "06_release"
    json_path = release / "paper_table_blueprint.json"
    md_path = release / "paper_table_blueprint.md"
    write_json(json_path, payload)
    write_text(md_path, render_markdown(payload))
    print(
        json.dumps(
            {
                "json": rel(json_path),
                "markdown": rel(md_path),
                "overall_status": payload["overall_status"],
                "claim_status": payload["claim_status"],
                "table_count": payload["summary"]["table_count"],
                "missing_evidence_files": payload["summary"]["missing_evidence_files"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
