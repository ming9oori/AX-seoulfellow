#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build reviewer-question response preparation artifacts for CAPE-KG."""

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from cape_pre_human_status import effective_prehuman_summary


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_PLAN_FILE = Path("AX_EACL_submission_review_revised_plan.md")
READY_STATUS = "reviewer_response_prep_ready_not_submission_complete"


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


def evidence_files(paths):
    files = [file_state(path) for path in paths]
    missing = [row["path"] for row in files if not row["exists"] or row["bytes"] == 0]
    return files, missing


def response(
    response_id,
    reviewer_question,
    concern_class,
    status,
    short_answer_ko,
    short_answer_en,
    evidence_paths,
    safe_claim_boundary,
    must_not_claim,
    remaining_gate,
    paper_sections,
):
    files, missing = evidence_files(evidence_paths)
    return {
        "response_id": response_id,
        "reviewer_question": reviewer_question,
        "concern_class": concern_class,
        "status": status,
        "paper_sections": paper_sections,
        "short_answer_ko": short_answer_ko,
        "short_answer_en": short_answer_en,
        "safe_claim_boundary": safe_claim_boundary,
        "must_not_claim": must_not_claim,
        "remaining_gate": remaining_gate,
        "evidence_files": files,
        "missing_evidence_files": missing,
    }


def build_responses(exp_dir, plan_file):
    exp_dir = Path(exp_dir)
    release = exp_dir / "06_release"
    reports = exp_dir / "07_reports"
    evaluation = exp_dir / "04_evaluation"
    public_bench = exp_dir / "08_public_benchmarks"
    schema = exp_dir / "02_schema"
    outputs = Path("outputs")

    return [
        response(
            "Q01_domain_application",
            "단순 domain application 아닌가?",
            "task_framing",
            "mitigated_setup_final_performance_pending",
            "논문은 수주·제안 KG 구축 사례가 아니라, 장문 한국어 업무 문서에서 evidence-grounded procedural KG를 추출하는 constrained IE task로 정의한다. 현재 RQ1-RQ4, M1-M11, CQ/query pack, paper section source map이 이 framing을 뒷받침한다.",
            "The paper should be framed as constrained evidence-grounded procedural KG extraction from long Korean enterprise documents, not as a one-off bid/proposal KG case. RQ1-RQ4, M1-M11, the CQ/query pack, and the section source map currently support that framing.",
            [
                plan_file,
                release / "rq_evidence_matrix.md",
                release / "method_module_coverage.md",
                release / "cq_query_pack.md",
                release / "paper_section_source_map.md",
            ],
            "Task definition, method modules, and structural diagnostics are safe to discuss now.",
            "Do not claim final target-corpus superiority until human-gold scoring is complete.",
            "human-gold annotation, IAA, adjudication, and proposed-method scoring",
            ["Introduction", "Task Definition", "Method"],
        ),
        response(
            "Q02_reproducibility_private_data",
            "데이터가 공개되지 않으면 재현성이 낮지 않은가?",
            "reproducibility",
            "mitigated_public_safe_release_rights_review_required",
            "raw OCR/source text는 권리 검토 전 공개하지 않는다. 대신 schema, prompts, evaluation scripts, provenance, public-safe synthetic examples, public benchmark adapters, release bundle manifest를 공개 가능한 재현성 package로 제시한다.",
            "Raw OCR/source text should not be released before rights clearance. Reproducibility is mitigated through schemas, prompts, evaluation scripts, provenance, public-safe synthetic examples, public benchmark adapters, and release-bundle manifests.",
            [
                release / "public_reproducibility_manifest.md",
                release / "public_synthetic_examples/README.md",
                release / "external_resource_license_report.md",
                release / "data_release_ethics_statement.md",
                release / "provenance_manifest.md",
                release / "release_bundle_safety_report.md",
            ],
            "Public-safe reproducibility scaffolding is claimable as setup evidence.",
            "Do not state that private source text can be redistributed or that rights review is complete.",
            "external rights review before public source-text release",
            ["Dataset and Annotation", "Release and Reproducibility", "Ethics"],
        ),
        response(
            "Q03_existing_ontology_guided_extraction",
            "ontology-guided extraction은 이미 많지 않은가?",
            "novelty",
            "partially_mitigated_final_gain_pending",
            "차별점은 ontology guidance 자체가 아니라 CQ-anchored schema retrieval, procedural node/edge schema, component evidence spans, validators, active-review queue, NCS/PCF standard bridge를 하나의 평가 가능한 pipeline으로 묶는 데 있다.",
            "The novelty claim should not be generic ontology guidance. It should focus on combining CQ-anchored schema retrieval, procedural node/edge schemas, component evidence spans, validators, active-review queues, and NCS/PCF standard bridging in an evaluable pipeline.",
            [
                release / "method_novelty_positioning.md",
                release / "method_module_coverage.md",
                release / "prompt_node_edge_traceability.md",
                evaluation / "evidence_span_granularity_report.md",
                evaluation / "structural_evaluation_report.md",
                release / "reviewer_risk_register.md",
            ],
            "Method composition and artifact coverage are safe to claim.",
            "Do not claim that each module independently improves final quality until ablations are scored against human gold.",
            "human-gold ablation scoring",
            ["Related Work", "Method", "Ablation"],
        ),
        response(
            "Q04_why_korean_enterprise_documents",
            "왜 Korean enterprise document인가?",
            "dataset_motivation",
            "claimable_setup_human_quality_pending",
            "이 데이터는 OCR noise, 장문 절차, 한국어/영어 alias 혼합, task-artifact-role-flow가 얽힌 업무 문서라는 IE challenge를 제공한다. 현재 5,009 sentence OCR evidence index와 120 evaluation chunks, 100 priority review chunks가 준비되어 있다.",
            "The corpus is motivated as an IE challenge with OCR noise, long procedural context, mixed Korean/English aliases, and intertwined task-artifact-role-flow structures. The current setup includes 5,009 OCR evidence sentences, 120 evaluation chunks, and 100 priority review chunks.",
            [
                outputs / "06_triples/evidence_anchors.jsonl",
                exp_dir / "01_data/evaluation_chunks.jsonl",
                release / "gold_sampling_coverage_report.md",
                release / "annotation_qc_report.md",
                release / "human_review_packet_integrity.md",
            ],
            "Dataset challenge and sampling setup are safe to describe.",
            "Do not claim benchmark quality or annotation reliability until annotation and IAA are complete.",
            "two-annotator labels, adjudication, and IAA",
            ["Dataset and Annotation", "Analysis"],
        ),
        response(
            "Q05_prompt_engineering",
            "LLM prompt engineering 아닌가?",
            "method_rigor",
            "mitigated_with_constraints_and_diagnostics",
            "CAPE-KG는 prompt만이 아니라 strict JSON contract, schema retrieval, constrained predicate set, component evidence spans, ontology/SHACL validation, procedural diagnostics, provenance lock으로 통제된다.",
            "CAPE-KG is controlled by more than prompts: strict JSON contracts, schema retrieval, constrained predicates, component evidence spans, ontology/SHACL validation, procedural diagnostics, and provenance locks constrain the pipeline.",
            [
                schema / "prompts/strict_json_contract.txt",
                release / "strict_json_diagnostics.md",
                release / "evaluation_protocol_lock.md",
                outputs / "12_rdf/cape_kg_shacl_validation_report.md",
                release / "provenance_manifest.md",
                release / "prompt_node_edge_traceability.md",
            ],
            "Engineering controls, validators, and provenance are safe setup claims.",
            "Do not equate strict JSON or SHACL pass rates with final semantic correctness.",
            "human-gold semantic correctness evaluation",
            ["Method", "Experiments", "Reproducibility"],
        ),
        response(
            "Q06_subjective_evaluation",
            "평가가 subjective하지 않은가?",
            "evaluation_rigor",
            "scaffold_ready_human_metrics_pending",
            "평가는 node/edge F1, evidence EM/IoU, unsupported edge rate, ontology conformance, procedural consistency, CQ answerability, mapping P@K/MRR/nDCG로 정량화되도록 준비되어 있다. 현재 final human-gold 값은 pending이다.",
            "The evaluation is designed around quantitative metrics: node/edge F1, evidence EM/IoU, unsupported edge rate, ontology conformance, procedural consistency, CQ answerability, and mapping P@K/MRR/nDCG. Final human-gold values remain pending.",
            [
                release / "paper_tables.md",
                release / "post_human_scoring_readiness.md",
                evaluation / "human_gold_metrics.json",
                evaluation / "human_gold_span_iou_report.md",
                evaluation / "structural_evaluation_report.md",
                release / "claim_gate_report.md",
            ],
            "Metric definitions and scorer readiness are safe to describe.",
            "Do not report silver/proxy diagnostics as main human-gold performance.",
            "completed human-gold labels and scorer refresh",
            ["Experiments", "Main Results", "Analysis"],
        ),
        response(
            "Q07_ncs_pcf_nlp_contribution",
            "NCS/PCF mapping이 NLP contribution인가?",
            "downstream_scope",
            "candidate_pipeline_ready_expert_review_pending",
            "NCS/PCF는 핵심 NLP contribution이 아니라 downstream standard-taxonomy alignment task로 제한한다. core contribution은 evidence-grounded procedural IE이고, NCS/PCF mapping은 KG가 표준 taxonomy alignment에 유용한지 검증하는 후속 평가다.",
            "NCS/PCF mapping should be scoped as a downstream standard-taxonomy alignment task, not the core NLP contribution. The core contribution is evidence-grounded procedural IE; mapping evaluates whether the resulting KG helps standard-taxonomy alignment.",
            [
                evaluation / "mapping_downstream_report.md",
                release / "mapping_review_progress_report.md",
                evaluation / "ncs_pcf_crosswalk_report.md",
                evaluation / "mapping_expert_metrics.json",
                evaluation / "crosswalk_expert_metrics.json",
                release / "rq_evidence_matrix.md",
            ],
            "Candidate generation and downstream task framing are safe to discuss.",
            "Do not claim P@K, MRR, nDCG, accept-rate, or utility until expert review is complete.",
            "mapping and crosswalk expert review",
            ["Downstream Evaluation", "Analysis"],
        ),
    ]


def build_payload(exp_dir, plan_file):
    exp_dir = Path(exp_dir)
    release = exp_dir / "06_release"
    responses = build_responses(exp_dir, plan_file)
    missing = [path for row in responses for path in row["missing_evidence_files"]]
    status_counts = Counter(row["status"] for row in responses)
    concern_counts = Counter(row["concern_class"] for row in responses)
    claim_gate = read_json(release / "claim_gate_report.json", {}) or {}
    validation = read_json(release / "pre_human_handoff_validation.json", {}) or {}
    effective_validation = effective_prehuman_summary(validation)
    risk_register = read_json(release / "reviewer_risk_register.json", {}) or {}

    summary = {
        "response_count": len(responses),
        "missing_evidence_files": len(missing),
        "status_counts": dict(sorted(status_counts.items())),
        "concern_counts": dict(sorted(concern_counts.items())),
        "claim_gate_overall_status": claim_gate.get("overall_status"),
        "claim_gate_required_failures": claim_gate.get("required_failure_count"),
        "claim_gate_optional_failures": claim_gate.get("optional_failure_count"),
        "pre_human_validation_status": effective_validation.get("overall_status"),
        "pre_human_validation_checks": effective_validation.get("check_count"),
        "reviewer_risk_register_status": risk_register.get("claim_status"),
        "safe_to_use_as_submission": False,
        "submission_ready": False,
    }

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "plan_file": rel(plan_file),
        "experiment_dir": rel(exp_dir),
        "overall_status": "PASS" if not missing else "FAIL",
        "claim_status": READY_STATUS if not missing else "reviewer_response_prep_incomplete",
        "safe_to_use_as_submission": False,
        "submission_ready": False,
        "summary": summary,
        "responses": responses,
        "missing_evidence_files": missing,
    }


def render_markdown(payload):
    summary = payload["summary"]
    rows = []
    for row in payload["responses"]:
        rows.append(
            {
                "id": row["response_id"],
                "reviewer_question": row["reviewer_question"],
                "status": row["status"],
                "safe_claim_boundary": row["safe_claim_boundary"],
                "remaining_gate": row["remaining_gate"],
            }
        )

    lines = [
        "# CAPE-KG Reviewer Response Prep",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Plan: `{payload['plan_file']}`",
        f"Experiment: `{payload['experiment_dir']}`",
        "",
        "이 문서는 revised EACL plan 12장의 예상 reviewer 질문을 현재 evidence, 안전한 답변 문구, 금지 claim, 남은 gate로 연결한 준비 문서입니다.",
        "최종 rebuttal 문서가 아니라 pre-human 상태에서 논문 초안과 발표 문구가 reviewer 우려에 어떻게 대응해야 하는지 고정하는 guardrail입니다.",
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
                {"Item": "Reviewer questions", "Value": summary["response_count"]},
                {"Item": "Missing evidence files", "Value": summary["missing_evidence_files"]},
                {"Item": "Claim gate", "Value": summary["claim_gate_overall_status"]},
                {"Item": "Pre-human validation", "Value": summary["pre_human_validation_status"]},
                {"Item": "Pre-human checks", "Value": summary.get("pre_human_validation_checks")},
            ],
        ),
        "",
        "## Response Table",
        "",
        md_table(["id", "reviewer_question", "status", "safe_claim_boundary", "remaining_gate"], rows),
        "",
        "## Detailed Responses",
        "",
    ]
    for row in payload["responses"]:
        lines.extend(
            [
                f"### {row['response_id']}. {row['reviewer_question']}",
                "",
                f"- Concern class: `{row['concern_class']}`",
                f"- Status: `{row['status']}`",
                f"- Paper sections: {', '.join(row['paper_sections'])}",
                f"- Remaining gate: {row['remaining_gate']}",
                "",
                "**Short answer, Korean**",
                "",
                row["short_answer_ko"],
                "",
                "**Short answer, English**",
                "",
                row["short_answer_en"],
                "",
                "**Safe claim boundary**",
                "",
                row["safe_claim_boundary"],
                "",
                "**Must not claim yet**",
                "",
                row["must_not_claim"],
                "",
                "**Evidence files**",
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
            "- `mitigated_*` and `*_ready_*` statuses mean paper sections can describe setup, design, diagnostics, or candidate generation.",
            "- Human-gold extraction quality, IAA, adjudicated correctness, mapping utility, and active-review efficiency remain unclaimable until the relevant returns are imported and scoring is refreshed.",
            "- Silver/proxy diagnostics may support debugging and reviewer-risk planning, but must not be reported as final main results.",
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
    json_path = release / "reviewer_response_prep.json"
    md_path = release / "reviewer_response_prep.md"
    write_json(json_path, payload)
    write_text(md_path, render_markdown(payload))
    print(
        json.dumps(
            {
                "json": rel(json_path),
                "markdown": rel(md_path),
                "overall_status": payload["overall_status"],
                "claim_status": payload["claim_status"],
                "response_count": payload["summary"]["response_count"],
                "missing_evidence_files": payload["summary"]["missing_evidence_files"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
