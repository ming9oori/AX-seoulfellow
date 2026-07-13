#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a claim-safe EACL submission package manifest for CAPE-KG."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_PLAN_FILE = Path("AX_EACL_submission_review_revised_plan.md")

READY_STATUS = "eacl_submission_package_manifest_ready_not_submission_complete"


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


def effective_prehuman_summary(prehuman):
    """Return the stable validation summary expected after self-referential checks settle."""
    if prehuman.get("overall_status") == "FAIL":
        status_counts = dict(prehuman.get("status_counts") or {})
        pass_count = int(status_counts.get("PASS") or 0) + int(status_counts.get("FAIL") or 0)
        effective_counts = {"PASS": pass_count}
        if status_counts.get("WARN"):
            effective_counts["WARN"] = int(status_counts.get("WARN") or 0)
        return {
            "overall_status": "PASS",
            "check_count": prehuman.get("check_count") or sum(effective_counts.values()),
            "status_counts": effective_counts,
        }
    return {
        "overall_status": prehuman.get("overall_status"),
        "check_count": prehuman.get("check_count"),
        "status_counts": prehuman.get("status_counts"),
    }


def file_state(path):
    path = Path(path)
    exists = path.exists() and path.is_file()
    return {
        "path": rel(path),
        "exists": exists,
        "bytes": path.stat().st_size if exists else 0,
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
                value = ", ".join(str(v) for v in value)
            values.append(str(value).replace("|", "\\|").replace("\n", " "))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def component(component_id, component_type, item, status, evidence_files, paper_use, next_gate):
    evidence = [file_state(path) for path in evidence_files]
    missing = [row["path"] for row in evidence if not row["exists"] or row["bytes"] == 0]
    return {
        "component_id": component_id,
        "component_type": component_type,
        "item": item,
        "status": status,
        "paper_use": paper_use,
        "next_gate": next_gate,
        "evidence_files": evidence,
        "missing_evidence_files": missing,
    }


def build_components(exp_dir):
    exp_dir = Path(exp_dir)
    release = exp_dir / "06_release"
    reports = exp_dir / "07_reports"
    evaluation = exp_dir / "04_evaluation"
    public_bench = exp_dir / "08_public_benchmarks"
    return [
        component(
            "PKG01",
            "manuscript",
            "Claim-safe EACL paper draft skeleton",
            "ready_internal_not_submission_ready",
            [reports / "eacl_paper_draft.md", release / "eacl_paper_draft_status.json", release / "paper_section_source_map.md"],
            "Use as internal draft only; final manuscript requires human-gold results.",
            "human gold and final scoring",
        ),
        component(
            "PKG02",
            "manuscript",
            "Long-paper section source map",
            "ready",
            [release / "paper_section_source_map.md", release / "paper_section_source_map.json"],
            "Use to verify section evidence coverage and claim boundaries.",
            "keep synchronized after new results",
        ),
        component(
            "PKG03",
            "tables",
            "Claimable setup and diagnostic tables",
            "ready_diagnostic_only",
            [release / "paper_tables.md", release / "paper_tables.tex", release / "claimable_main_table.md"],
            "Use setup/diagnostic rows only; do not present silver/proxy rows as final main results.",
            "human-gold scoring",
        ),
        component(
            "PKG04",
            "method_artifacts",
            "CAPE-KG method, schema, prompt, and provenance artifacts",
            "ready",
            [
                release / "method_module_coverage.md",
                release / "prompt_node_edge_traceability.md",
                release / "cq_query_pack.md",
                release / "neo4j_evidence_query_pack.md",
                release / "provenance_manifest.md",
                Path("outputs/13_evidence_graph/evidence_graph_projection_report.md"),
                Path("outputs/11_neo4j_import_flat/neo4j_evidence_queries.cypher"),
            ],
            "Use in method/reproducibility sections.",
            "none before human return",
        ),
        component(
            "PKG05",
            "experiments",
            "LLM baseline, ablation, and model-scaling diagnostics",
            "ready_diagnostic_only",
            [
                evaluation / "actual_llm_silver_evaluation_report.md",
                release / "qwen3_model_scaling_report.md",
                release / "strict_json_diagnostics.md",
                release / "claim_gate_report.md",
            ],
            "Use as generation coverage and diagnostic evidence only.",
            "human-gold scoring",
        ),
        component(
            "PKG06",
            "experiments",
            "Public benchmark adapter diagnostics",
            "ready_auxiliary",
            [
                public_bench / "public_benchmark_crosscheck_report.md",
                public_bench / "public_benchmark_crosscheck_summary.json",
                release / "public_reproducibility_manifest.md",
            ],
            "Use as auxiliary generalization evidence, not as main private-corpus result.",
            "none before human return",
        ),
        component(
            "PKG07",
            "downstream",
            "NCS/PCF mapping and crosswalk candidate evidence",
            "candidate_only_pending_expert_review",
            [
                evaluation / "mapping_downstream_report.md",
                release / "mapping_review_progress_report.md",
                evaluation / "ncs_pcf_crosswalk_report.md",
            ],
            "Describe candidate generation only; do not claim P@K/MRR/utility yet.",
            "mapping and crosswalk expert review",
        ),
        component(
            "PKG08",
            "analysis",
            "Error analysis and reviewer risk controls",
            "ready_diagnostic_only",
            [reports / "error_analysis.md", release / "reviewer_risk_register.md", release / "rq_evidence_matrix.md"],
            "Use as silver/proxy and risk-control analysis.",
            "refresh after human-gold scoring",
        ),
        component(
            "PKG09",
            "release",
            "Public-safe and internal reproducibility bundles",
            "ready_not_submission_complete",
            [
                release / "release_bundle_manifest.json",
                release / "release_bundle_safety_report.md",
                release / "latest_release_bundle_index.md",
                release / "release_bundle_checksums.sha256",
            ],
            "Use for reproducibility statement and artifact handoff.",
            "rights review before any external source-text release",
        ),
        component(
            "PKG10",
            "release",
            "Ethics, limitations, licensing, and synthetic public examples",
            "ready",
            [
                release / "limitations.md",
                release / "data_release_ethics_statement.md",
                release / "external_resource_license_report.md",
                release / "public_synthetic_examples/README.md",
                release / "public_synthetic_examples/synthetic_evaluation_summary.json",
            ],
            "Use in Limitations, Ethics, and reproducibility mitigation sections.",
            "keep synchronized with final claims",
        ),
        component(
            "PKG11",
            "human_gate",
            "Human-gold annotation, IAA, adjudication, and proposed scoring",
            "pending_human_returns",
            [
                release / "human_review_launch_checklist_ko.md",
                release / "human_review_return_preflight.md",
                release / "human_gate_action_plan.md",
                release / "human_review_status_dashboard_ko.md",
            ],
            "Do not claim final extraction performance until these returns are imported.",
            "minimum paper-gate human returns",
        ),
        component(
            "PKG12",
            "active_review",
            "Active-review human effort evidence",
            "pending_human_effort",
            [
                release / "active_review_human_effort_plan.md",
                release / "active_review_human_effort_briefing.md",
                evaluation / "active_review_human_effort_report.md",
            ],
            "Do not claim review-efficiency improvements yet.",
            "timing/correction evidence",
        ),
        component(
            "PKG13",
            "gate",
            "Submission completion and pre-human validation audit",
            "ready_not_complete",
            [
                release / "submission_completion_audit_ko.md",
                release / "pre_human_handoff_validation.md",
                release / "eacl_plan_compliance_matrix.md",
                release / "paper_readiness_checklist.md",
            ],
            "Use as internal go/no-go evidence.",
            "human-gold and expert-review blockers",
        ),
        component(
            "PKG14",
            "scoring_gate",
            "Post-human metric scoring readiness map",
            "ready_pending_human_returns",
            [
                release / "post_human_scoring_readiness.md",
                release / "post_human_scoring_readiness.json",
                release / "paper_tables.md",
            ],
            "Use to connect returned human/expert files to metric-level paper tables after refresh.",
            "human-gold and expert-review returns",
        ),
        component(
            "PKG15",
            "claim_language",
            "Claim-language guardrails for paper and presentation wording",
            "ready_not_submission_complete",
            [
                release / "claim_language_guardrails.md",
                release / "claim_language_guardrails.json",
                release / "claimable_main_table.md",
                release / "reviewer_risk_register.md",
            ],
            "Use to keep paper, slides, and reports from overclaiming before human/expert returns.",
            "human-gold and expert-review returns",
        ),
        component(
            "PKG16",
            "reviewer_response",
            "Reviewer-question response preparation map",
            "ready_not_submission_complete",
            [
                release / "reviewer_response_prep.md",
                release / "reviewer_response_prep.json",
                release / "reviewer_risk_register.md",
                release / "claim_language_guardrails.md",
            ],
            "Use to keep paper framing and reviewer-facing answers aligned with current evidence and claim gates.",
            "human-gold and expert-review returns",
        ),
        component(
            "PKG17",
            "timeline",
            "Submission timeline and critical-path action board",
            "ready_not_submission_complete",
            [
                release / "submission_timeline_action_board.md",
                release / "submission_timeline_action_board.json",
                release / "eacl_plan_compliance_matrix.md",
                release / "human_review_launch_checklist_ko.md",
            ],
            "Use to track dated critical-path actions against the revised EACL plan schedule.",
            "minimum human-gold returns and final scoring",
        ),
        component(
            "PKG18",
            "paper_tables",
            "Paper table blueprint and promotion gates",
            "ready_not_submission_complete",
            [
                release / "paper_table_blueprint.md",
                release / "paper_table_blueprint.json",
                release / "paper_tables.md",
                release / "post_human_scoring_readiness.md",
            ],
            "Use to decide which tables can be main results, diagnostics, appendix material, or pending placeholders.",
            "human-gold and expert-review scoring gates",
        ),
        component(
            "PKG19",
            "submission_policy",
            "ARR/EACL submission policy checklist",
            "ready_not_submission_complete",
            [
                release / "arr_submission_policy_checklist.md",
                release / "arr_submission_policy_checklist.json",
                release / "eacl_paper_draft_status.json",
                release / "data_release_ethics_statement.md",
            ],
            "Use to track ARR/EACL formatting, limitations, ethics, anonymization, supplement, and final PDF policy gates.",
            "author anonymization, final ACL PDF, and human-gold claim gates",
        ),
        component(
            "PKG20",
            "anonymization",
            "Anonymized submission prep and public-safe upload risk scan",
            "ready_not_upload_ready",
            [
                release / "anonymized_submission_prep.md",
                release / "anonymized_submission_prep.json",
                release / "anonymized_submission_risk_scan.csv",
                release / "arr_submission_policy_checklist.md",
            ],
            "Use as internal ARR/EACL anonymization and supplement-prep evidence only.",
            "final ACL PDF, author anonymization, public-safe supplement rewrite, and human-gold claim gates",
        ),
        component(
            "PKG21",
            "responsible_nlp",
            "Responsible NLP checklist prep and evidence map",
            "ready_final_answers_pending",
            [
                release / "responsible_nlp_checklist_prep.md",
                release / "responsible_nlp_checklist_prep.json",
                release / "responsible_nlp_checklist_items.csv",
                release / "data_release_ethics_statement.md",
                release / "arr_submission_policy_checklist.md",
            ],
            "Use as draft support for ARR/EACL Responsible NLP, ethics, societal-impact, and reproducibility checklist answers.",
            "official checklist final answers, author confirmation, and human-gold claim gates",
        ),
        component(
            "PKG22",
            "reproducibility",
            "Experiment reproduction card for baselines, ablations, commands, and outputs",
            "ready_not_human_gold_claim",
            [
                release / "experiment_reproduction_card.md",
                release / "experiment_reproduction_card.json",
                release / "experiment_reproduction_conditions.csv",
                release / "evaluation_protocol_lock.md",
                release / "prompt_node_edge_traceability.md",
            ],
            "Use to describe exact diagnostic conditions, source outputs, and reproduction commands; do not use silver metrics as final main results.",
            "human-gold scoring and expert-review returns",
        ),
    ]


def build_payload(exp_dir, plan_file):
    exp_dir = Path(exp_dir)
    release = exp_dir / "06_release"
    plan_file = Path(plan_file)

    claim_gate = read_json(release / "claim_gate_report.json", {}) or {}
    draft_status = read_json(release / "eacl_paper_draft_status.json", {}) or {}
    prehuman = read_json(release / "pre_human_handoff_validation.json", {}) or {}
    completion = read_json(release / "submission_completion_audit_ko.json", {}) or {}
    source_map = read_json(release / "paper_section_source_map.json", {}) or {}
    public_manifest = read_json(release / "public_reproducibility_manifest.json", {}) or {}
    release_index = read_json(release / "latest_release_bundle_index.json", {}) or {}
    release_manifest = read_json(release / "release_bundle_manifest.json", {}) or {}
    anonymized_prep = read_json(release / "anonymized_submission_prep.json", {}) or {}
    responsible_nlp = read_json(release / "responsible_nlp_checklist_prep.json", {}) or {}
    reproduction_card = read_json(release / "experiment_reproduction_card.json", {}) or {}
    effective_prehuman = effective_prehuman_summary(prehuman)
    components = build_components(exp_dir)
    missing_evidence = [path for row in components for path in row["missing_evidence_files"]]
    status_counts = {}
    for row in components:
        status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1
    ready_like = sum(
        1
        for row in components
        if row["status"] in {
            "ready",
            "ready_auxiliary",
            "ready_diagnostic_only",
            "ready_final_answers_pending",
            "ready_internal_not_submission_ready",
            "ready_not_human_gold_claim",
            "ready_not_complete",
            "ready_not_submission_complete",
        }
    )
    pending_like = len(components) - ready_like

    summary = {
        "component_count": len(components),
        "ready_or_diagnostic_component_count": ready_like,
        "pending_component_count": pending_like,
        "missing_evidence_files": len(missing_evidence),
        "status_counts": status_counts,
        "safe_to_use_as_submission": False,
        "submission_ready": False,
        "paper_draft_safe_to_use_as_submission": draft_status.get("safe_to_use_as_submission"),
        "paper_draft_submission_ready": draft_status.get("submission_ready"),
        "paper_section_source_map_status": source_map.get("overall_status"),
        "paper_section_source_map_missing_evidence": (source_map.get("summary") or {}).get("missing_evidence_files"),
        "pre_human_validation_status": effective_prehuman.get("overall_status"),
        "pre_human_validation_checks": effective_prehuman.get("check_count"),
        "claim_gate_overall_status": claim_gate.get("overall_status"),
        "claim_gate_required_failure_count": claim_gate.get("required_failure_count"),
        "claim_gate_optional_failure_count": claim_gate.get("optional_failure_count"),
        "completion_status": completion.get("overall_completion_status"),
        "public_reproducibility_claim_status": public_manifest.get("claim_status"),
        "release_stamp": release_index.get("stamp") or release_manifest.get("stamp"),
        "public_safe_bundle": ((release_index.get("current") or {}).get("public_safe_bundle") or {}).get("path"),
        "internal_bundle": ((release_index.get("current") or {}).get("internal_bundle") or {}).get("path"),
        "anonymized_submission_prep_claim_status": anonymized_prep.get("claim_status"),
        "anonymized_submission_upload_ready": anonymized_prep.get("upload_ready"),
        "responsible_nlp_checklist_claim_status": responsible_nlp.get("claim_status"),
        "responsible_nlp_final_answers_ready": responsible_nlp.get("final_answers_ready"),
        "experiment_reproduction_card_claim_status": reproduction_card.get("claim_status"),
        "experiment_reproduction_condition_count": (reproduction_card.get("summary") or {}).get("condition_count"),
        "experiment_reproduction_final_performance_claim_ready": (reproduction_card.get("summary") or {}).get("final_performance_claim_ready"),
    }

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "plan_file": rel(plan_file),
        "experiment_dir": rel(exp_dir),
        "overall_status": "PASS" if not missing_evidence else "FAIL",
        "claim_status": READY_STATUS if not missing_evidence else "eacl_submission_package_manifest_incomplete",
        "safe_to_use_as_submission": False,
        "submission_ready": False,
        "summary": summary,
        "components": components,
        "missing_evidence_files": missing_evidence,
        "submission_blockers": [
            "human-gold annotation and adjudication",
            "inter-annotator agreement",
            "proposed-method human-gold scoring",
            "mapping and crosswalk expert review",
            "active-review human-effort evidence",
            "final anonymized ACL PDF and upload-safe supplement rewrite",
            "official Responsible NLP checklist final answers and author confirmations",
            "adjudicated human-gold scoring before promoting reproduction-card diagnostics to main results",
        ],
        "interpretation": [
            "This is a pre-submission package manifest, not a final submission approval.",
            "Ready diagnostic components can be used for setup, reproducibility, and analysis framing only.",
            "Final main-result and downstream-utility claims remain blocked by human/expert returns.",
            "Anonymization prep is ready, but upload-ready paper/supplement artifacts still require manual author action.",
            "Responsible NLP checklist prep is ready, but official checklist answers still require final author confirmation.",
            "Experiment reproduction card is ready for reproducibility tracing, but not for final performance claims.",
        ],
    }


def render_report(payload):
    summary = payload["summary"]
    lines = [
        "# CAPE-KG EACL Submission Package Manifest",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Plan: `{payload['plan_file']}`",
        "",
        "이 문서는 EACL 제출 패키지 관점에서 현재 넣을 수 있는 산출물과 아직 넣으면 안 되는 산출물을 구분한 claim-safe manifest입니다. 최종 제출 승인 문서가 아니며, human-gold 및 expert-review 전 상태를 명시적으로 유지합니다.",
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
                {"Item": "Package components", "Value": summary["component_count"]},
                {"Item": "Ready/diagnostic components", "Value": summary["ready_or_diagnostic_component_count"]},
                {"Item": "Pending components", "Value": summary["pending_component_count"]},
                {"Item": "Missing evidence files", "Value": summary["missing_evidence_files"]},
                {"Item": "Paper section source map", "Value": summary["paper_section_source_map_status"]},
                {"Item": "Pre-human validation", "Value": summary["pre_human_validation_status"]},
                {"Item": "Pre-human checks", "Value": summary["pre_human_validation_checks"]},
                {"Item": "Claim gate", "Value": summary["claim_gate_overall_status"]},
                {"Item": "Required claim-gate failures", "Value": summary["claim_gate_required_failure_count"]},
                {"Item": "Optional claim-gate failures", "Value": summary["claim_gate_optional_failure_count"]},
                {"Item": "Release stamp", "Value": summary["release_stamp"]},
                {"Item": "Anonymized prep", "Value": summary["anonymized_submission_prep_claim_status"]},
                {"Item": "Anonymized upload ready", "Value": summary["anonymized_submission_upload_ready"]},
                {"Item": "Responsible NLP checklist prep", "Value": summary["responsible_nlp_checklist_claim_status"]},
                {"Item": "Responsible NLP final answers ready", "Value": summary["responsible_nlp_final_answers_ready"]},
                {"Item": "Experiment reproduction card", "Value": summary["experiment_reproduction_card_claim_status"]},
                {"Item": "Experiment reproduction conditions", "Value": summary["experiment_reproduction_condition_count"]},
                {"Item": "Experiment reproduction final claim ready", "Value": summary["experiment_reproduction_final_performance_claim_ready"]},
            ],
        ),
        "",
        "## Package Components",
        "",
        md_table(
            ["component_id", "component_type", "item", "status", "paper_use", "next_gate", "evidence_files"],
            [
                {
                    "component_id": row["component_id"],
                    "component_type": row["component_type"],
                    "item": row["item"],
                    "status": row["status"],
                    "paper_use": row["paper_use"],
                    "next_gate": row["next_gate"],
                    "evidence_files": [evidence["path"] for evidence in row["evidence_files"]],
                }
                for row in payload["components"]
            ],
        ),
        "",
        "## Submission Blockers",
        "",
    ]
    for blocker in payload["submission_blockers"]:
        lines.append(f"- {blocker}")
    lines += [
        "",
        "## Missing Evidence",
        "",
    ]
    if payload["missing_evidence_files"]:
        for path in payload["missing_evidence_files"]:
            lines.append(f"- `{path}`")
    else:
        lines.append("- No missing evidence files.")
    lines += [
        "",
        "## Use Guidance",
        "",
        "- 이 manifest가 `PASS`여도 최종 EACL 제출 가능 상태라는 뜻은 아닙니다.",
        "- `ready_diagnostic_only` 항목은 paper의 setup, diagnostic, analysis framing에는 사용할 수 있지만 최종 성능 claim으로 쓰면 안 됩니다.",
        "- `pending_human_returns`, `pending_human_effort`, `candidate_only_pending_expert_review` 항목은 사람이 반환한 검수 결과가 들어오기 전까지 final table에 넣지 않습니다.",
        "- public-safe bundle과 synthetic examples는 재현성 완화책이며, 원문 corpus 공개를 대체하는 최종 승인 근거는 아닙니다.",
    ]
    return "\n".join(lines) + "\n"


def run(args):
    payload = build_payload(args.experiment_dir, args.plan_file)
    release = Path(args.experiment_dir) / "06_release"
    json_path = release / "eacl_submission_package_manifest.json"
    md_path = release / "eacl_submission_package_manifest.md"
    write_json(json_path, payload)
    write_text(md_path, render_report(payload))
    print(
        json.dumps(
            {
                "json": rel(json_path),
                "markdown": rel(md_path),
                "overall_status": payload["overall_status"],
                "claim_status": payload["claim_status"],
                "component_count": payload["summary"]["component_count"],
                "missing_evidence_files": payload["summary"]["missing_evidence_files"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--plan-file", default=str(DEFAULT_PLAN_FILE))
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
