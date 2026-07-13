#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build contribution-claim traceability artifacts for CAPE-KG."""

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_OUTPUTS_DIR = Path("outputs")
DEFAULT_PLAN_FILE = Path("AX_EACL_submission_review_revised_plan.md")
CLAIM_STATUS = "contribution_claim_traceability_ready_pending_human_gold_and_expert_returns"


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


def contribution_row(
    contribution_id,
    title,
    plan_sentence_en,
    plan_sentence_ko,
    linked_rqs,
    linked_metrics,
    linked_modules,
    reviewer_questions,
    evidence_files,
    setup_claimable_now,
    final_performance_claim_ready,
    current_claim_boundary,
    safe_pre_human_wording_ko,
    safe_pre_human_wording_en,
    forbidden_pre_human_claim,
    remaining_gates,
):
    missing = [row["path"] for row in evidence_files if not row["exists"] or row["bytes"] == 0]
    return {
        "contribution_id": contribution_id,
        "title": title,
        "plan_sentence_en": plan_sentence_en,
        "plan_sentence_ko": plan_sentence_ko,
        "linked_rqs": linked_rqs,
        "linked_metrics": linked_metrics,
        "linked_modules": linked_modules,
        "reviewer_questions": reviewer_questions,
        "evidence_files": evidence_files,
        "missing_evidence_files": missing,
        "setup_claimable_now": bool(setup_claimable_now),
        "final_performance_claim_ready": bool(final_performance_claim_ready),
        "current_claim_boundary": current_claim_boundary,
        "safe_pre_human_wording_ko": safe_pre_human_wording_ko,
        "safe_pre_human_wording_en": safe_pre_human_wording_en,
        "forbidden_pre_human_claim": forbidden_pre_human_claim,
        "remaining_gates": remaining_gates,
    }


def build_payload(exp_dir, outputs_dir, plan_file):
    exp_dir = Path(exp_dir)
    outputs_dir = Path(outputs_dir)
    plan_file = Path(plan_file)
    release_dir = exp_dir / "06_release"
    eval_dir = exp_dir / "04_evaluation"

    revised_audit = read_json(release_dir / "revised_plan_completion_audit.json", {}) or {}
    claim_gate = read_json(release_dir / "claim_gate_report.json", {}) or {}
    rq_matrix = read_json(release_dir / "rq_evidence_matrix.json", {}) or {}
    metric_audit = read_json(release_dir / "metric_traceability_audit.json", {}) or {}
    reviewer_prep = read_json(release_dir / "reviewer_response_prep.json", {}) or {}

    minimum_blockers = [
        "min.gold_chunks",
        "min.gold_items",
        "min.iaa",
        "min.proposed",
    ]
    expert_blockers = [
        "strong.mapping_downstream",
        "crosswalk.expert_review",
    ]
    effort_blockers = ["strong.active_review"]
    rights_blockers = ["external_rights_review_for_raw_source_text"]

    rows = [
        contribution_row(
            "C1_task_definition_and_evidence_grounding",
            "Evidence-grounded procedural KG construction task",
            "We formulate evidence-grounded procedural KG construction from long enterprise documents as a constrained information extraction task, requiring typed nodes, relations, and character-level evidence anchors.",
            "한국어 장문 업무 문서에서 절차형 KG 구축 문제를 typed node/relation과 evidence grounding이 필요한 constrained information extraction task로 정의한다.",
            ["RQ1", "RQ2"],
            [
                "Node F1",
                "Edge F1",
                "Evidence Exact Match",
                "Evidence IoU",
                "Unsupported Edge Rate",
                "Ontology Conformance",
                "Procedural Consistency",
                "CQ Answerability",
            ],
            ["M1", "M2", "M4", "M5", "M6", "M7", "M8"],
            ["Q01_domain_application", "Q04_why_korean_enterprise_documents", "Q06_subjective_evaluation"],
            [
                file_state(plan_file, "revised plan contribution statement"),
                file_state(release_dir / "rq_evidence_matrix.md", "RQ-to-evidence matrix"),
                file_state(release_dir / "metric_traceability_audit.md", "metric traceability audit"),
                file_state(release_dir / "prompt_node_edge_traceability.md", "prompt/node/edge traceability"),
                file_state(eval_dir / "evidence_span_granularity_report.md", "evidence span diagnostic"),
                file_state(eval_dir / "structural_evaluation_report.md", "structural diagnostic report"),
                file_state(outputs_dir / "07_layer2_graph/layer2_nodes.jsonl", "final Layer 2 node artifacts"),
                file_state(outputs_dir / "07_layer2_graph/layer2_edges.jsonl", "final Layer 2 edge artifacts"),
            ],
            True,
            False,
            "Task formulation, schema, KG artifacts, and automatic diagnostics are claimable; final extraction quality is not.",
            "현재는 장문 한국어 업무 문서를 evidence-grounded procedural IE task로 정의하고, 이를 위한 schema, KG 산출물, 자동 진단 지표를 준비했다고 말할 수 있다.",
            "At the pre-human stage, it is safe to claim the task formulation, schema, KG artifacts, and automatic diagnostics.",
            "CAPE-KG improves final node/edge/evidence F1 over baselines.",
            minimum_blockers,
        ),
        contribution_row(
            "C2_cape_kg_framework",
            "CAPE-KG framework",
            "We propose CAPE-KG, a competency-question anchored extraction framework that combines schema retrieval, constrained generation, evidence-span verification, ontology validation, and procedural consistency checking.",
            "CQ 기반 schema retrieval, constrained generation, evidence-span verification, ontology validation, procedural consistency checking을 결합한 CAPE-KG 프레임워크를 제안한다.",
            ["RQ1", "RQ2", "RQ4"],
            [
                "Ontology Conformance",
                "Procedural Consistency",
                "CQ Answerability",
                "Active Review Efficiency",
                "Ablation: P - CQ",
                "Ablation: P - Evidence",
                "Ablation: P - Validator",
                "Ablation: P - Active review",
            ],
            ["M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9", "M10"],
            ["Q03_existing_ontology_guided_extraction", "Q05_prompt_engineering", "Q06_subjective_evaluation"],
            [
                file_state(release_dir / "method_module_coverage.md", "M1-M11 module coverage"),
                file_state(release_dir / "method_novelty_positioning.md", "method novelty positioning"),
                file_state(release_dir / "schema_retrieval_coverage_report.md", "schema retrieval coverage"),
                file_state(release_dir / "strict_json_diagnostics.md", "strict JSON diagnostics"),
                file_state(release_dir / "evaluation_protocol_lock.md", "locked evaluation protocol"),
                file_state(release_dir / "claim_language_guardrails.md", "claim language guardrails"),
                file_state(eval_dir / "active_review_efficiency_report.md", "active-review diagnostic"),
                file_state(release_dir / "active_review_human_effort_plan.md", "human-effort collection protocol"),
            ],
            True,
            False,
            "Integrated framework implementation and diagnostic coverage are claimable; module-level improvements remain human-gold gated.",
            "현재는 CAPE-KG의 구성 모듈과 검증/진단 체계가 구현되어 있음을 claim할 수 있지만, 각 모듈이 최종 성능을 개선한다는 주장은 human-gold 이후로 보류해야 한다.",
            "It is safe to claim that the integrated framework and diagnostic scaffolds are implemented; final module gains remain gated.",
            "Each CAPE-KG module independently improves final quality.",
            minimum_blockers + effort_blockers,
        ),
        contribution_row(
            "C3_benchmark_and_standard_taxonomy_alignment",
            "Korean bid/proposal benchmark and standard taxonomy alignment",
            "We introduce a Korean bid/proposal work-domain benchmark and evaluate whether the resulting procedural KG improves standard taxonomy alignment to capability and process reference layers.",
            "수주·제안 업무 benchmark를 구축하고, 추출된 절차형 KG가 NCS/PCF 표준 taxonomy alignment를 개선하는지 평가한다.",
            ["RQ3"],
            [
                "NCS/PCF Mapping P@K",
                "P@1",
                "P@5",
                "MRR",
                "nDCG@10",
                "Expert accept rate",
                "Explanation quality score",
            ],
            ["M1", "M5", "M9", "M11"],
            ["Q02_reproducibility_private_data", "Q04_why_korean_enterprise_documents", "Q07_ncs_pcf_nlp_contribution"],
            [
                file_state(release_dir / "gold_sampling_coverage_report.md", "gold sampling coverage report"),
                file_state(release_dir / "public_reproducibility_manifest.md", "public-safe reproducibility manifest"),
                file_state(release_dir / "public_synthetic_examples/README.md", "public-safe synthetic examples"),
                file_state(exp_dir / "08_public_benchmarks/public_benchmark_crosscheck_report.md", "public benchmark cross-check"),
                file_state(outputs_dir / "08_mapping/l2_ncs_mapping_candidates.jsonl", "Layer2-to-NCS mapping candidates"),
                file_state(outputs_dir / "08_mapping/l2_pcf_mapping_candidates.jsonl", "Layer2-to-PCF mapping candidates"),
                file_state(eval_dir / "ncs_pcf_crosswalk_report.md", "NCS-PCF crosswalk candidates"),
                file_state(release_dir / "mapping_review_progress_report.md", "mapping review progress"),
            ],
            True,
            False,
            "Benchmark/release scaffolds and mapping candidates are claimable; benchmark reliability and taxonomy utility require human/expert returns.",
            "현재는 benchmark 구축 및 공개 가능 재현 패키지, NCS/PCF 후보 생성까지 준비되었다고 말할 수 있다. benchmark 신뢰도와 taxonomy alignment 개선 주장은 사람 검수와 expert review 이후에만 가능하다.",
            "It is safe to claim benchmark/release scaffolds and mapping candidates; reliability and alignment utility remain expert/human gated.",
            "The benchmark is fully validated or the KG improves NCS/PCF alignment.",
            minimum_blockers + expert_blockers + rights_blockers,
        ),
    ]

    missing_files = sorted({path for row in rows for path in row["missing_evidence_files"]})
    setup_claimable_count = sum(1 for row in rows if row["setup_claimable_now"])
    final_ready_count = sum(1 for row in rows if row["final_performance_claim_ready"])
    reviewer_question_ids = {
        item.get("response_id")
        for item in reviewer_prep.get("responses", [])
        if item.get("response_id")
    }
    linked_reviewer_question_ids = {qid for row in rows for qid in row["reviewer_questions"]}
    rq_source_rows = rq_matrix.get("research_questions") or rq_matrix.get("rows") or []
    rq_ids = {row.get("rq_id") for row in rq_source_rows if row.get("rq_id")}
    metric_ids = {row.get("metric_id") for row in metric_audit.get("metric_rows", []) if row.get("metric_id")}

    summary = {
        "claim_status": CLAIM_STATUS,
        "contribution_count": len(rows),
        "setup_claimable_count": setup_claimable_count,
        "final_performance_claim_ready_count": final_ready_count,
        "blocked_final_claim_count": len(rows) - final_ready_count,
        "missing_evidence_file_count": len(missing_files),
        "linked_rq_count": len({rq for row in rows for rq in row["linked_rqs"]}),
        "known_rq_count": len(rq_ids),
        "known_metric_count": len(metric_ids),
        "linked_reviewer_question_count": len(linked_reviewer_question_ids),
        "known_reviewer_question_count": len(reviewer_question_ids),
        "plan_completion_proven": revised_audit.get("plan_completion_proven", False),
        "claim_gate_overall_status": claim_gate.get("overall_status"),
    }

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "claim_status": CLAIM_STATUS,
        "plan_file": rel(plan_file),
        "experiment_dir": rel(exp_dir),
        "outputs_dir": rel(outputs_dir),
        "summary": summary,
        "claim_boundary": {
            "safe_to_use_pre_human": True,
            "safe_scope": "Use for contribution framing, paper outline, reviewer-risk planning, and reproducibility description.",
            "not_claimable_until": "Final performance, benchmark reliability, taxonomy-alignment utility, and active-review efficiency remain pending human-gold, IAA, adjudication, mapping/crosswalk expert review, and human-effort returns.",
            "final_performance_claim_ready": False,
        },
        "contribution_rows": rows,
        "missing_evidence_files": missing_files,
        "source_artifacts": {
            "revised_plan": rel(plan_file),
            "revised_plan_completion_audit": rel(release_dir / "revised_plan_completion_audit.json"),
            "claim_gate_report": rel(release_dir / "claim_gate_report.json"),
            "rq_evidence_matrix": rel(release_dir / "rq_evidence_matrix.json"),
            "metric_traceability_audit": rel(release_dir / "metric_traceability_audit.json"),
            "reviewer_response_prep": rel(release_dir / "reviewer_response_prep.json"),
        },
    }
    return payload


def write_csv_rows(path, payload):
    fields = [
        "contribution_id",
        "title",
        "setup_claimable_now",
        "final_performance_claim_ready",
        "linked_rqs",
        "linked_metrics",
        "linked_modules",
        "reviewer_questions",
        "missing_evidence_file_count",
        "remaining_gates",
        "current_claim_boundary",
        "forbidden_pre_human_claim",
    ]
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in payload["contribution_rows"]:
            writer.writerow(
                {
                    "contribution_id": row["contribution_id"],
                    "title": row["title"],
                    "setup_claimable_now": row["setup_claimable_now"],
                    "final_performance_claim_ready": row["final_performance_claim_ready"],
                    "linked_rqs": ";".join(row["linked_rqs"]),
                    "linked_metrics": ";".join(row["linked_metrics"]),
                    "linked_modules": ";".join(row["linked_modules"]),
                    "reviewer_questions": ";".join(row["reviewer_questions"]),
                    "missing_evidence_file_count": len(row["missing_evidence_files"]),
                    "remaining_gates": ";".join(row["remaining_gates"]),
                    "current_claim_boundary": row["current_claim_boundary"],
                    "forbidden_pre_human_claim": row["forbidden_pre_human_claim"],
                }
            )


def render_md(payload):
    lines = [
        "# CAPE-KG Contribution Claim Traceability",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Plan: `{payload['plan_file']}`",
        f"Experiment: `{payload['experiment_dir']}`",
        "",
        "This artifact maps the three revised-plan contribution statements to current evidence, reviewer concerns, metrics, and claim gates.",
        "It is claim-safe: it separates setup/method claims that are currently supported from final performance claims that remain gated by human or expert evidence.",
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
            f"- Safe to use pre-human: `{payload['claim_boundary']['safe_to_use_pre_human']}`",
            f"- Safe scope: {payload['claim_boundary']['safe_scope']}",
            f"- Final performance claims remain pending: {payload['claim_boundary']['not_claimable_until']}",
            "",
            "## Contribution Rows",
            "",
        ]
    )
    table_rows = []
    for row in payload["contribution_rows"]:
        table_rows.append(
            {
                "id": row["contribution_id"],
                "title": row["title"],
                "setup claimable now": row["setup_claimable_now"],
                "final performance ready": row["final_performance_claim_ready"],
                "linked RQs": row["linked_rqs"],
                "remaining gates": row["remaining_gates"],
            }
        )
    lines.append(md_table(["id", "title", "setup claimable now", "final performance ready", "linked RQs", "remaining gates"], table_rows))
    for row in payload["contribution_rows"]:
        lines.extend(
            [
                "",
                f"## {row['contribution_id']}. {row['title']}",
                "",
                f"- Plan sentence EN: {row['plan_sentence_en']}",
                f"- Plan sentence KO: {row['plan_sentence_ko']}",
                f"- Current claim boundary: {row['current_claim_boundary']}",
                f"- Forbidden pre-human claim: {row['forbidden_pre_human_claim']}",
                "",
                "### Safe Pre-Human Wording",
                "",
                f"- KO: {row['safe_pre_human_wording_ko']}",
                f"- EN: {row['safe_pre_human_wording_en']}",
                "",
                "### Links",
                "",
                f"- RQs: `{', '.join(row['linked_rqs'])}`",
                f"- Modules: `{', '.join(row['linked_modules'])}`",
                f"- Reviewer questions: `{', '.join(row['reviewer_questions'])}`",
                f"- Metrics: `{', '.join(row['linked_metrics'])}`",
                "",
                "### Evidence Files",
                "",
                md_table(["role", "path", "exists", "bytes"], row["evidence_files"]),
                "",
                "### Remaining Gates",
                "",
            ]
        )
        lines.extend(f"- `{gate}`" for gate in row["remaining_gates"])
    lines.extend(
        [
            "",
            "## Source Artifacts",
            "",
        ]
    )
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
    json_path = release_dir / "contribution_claim_traceability.json"
    md_path = release_dir / "contribution_claim_traceability.md"
    csv_path = release_dir / "contribution_claim_traceability.csv"
    write_json(json_path, payload)
    write_text(md_path, render_md(payload))
    write_csv_rows(csv_path, payload)
    print(json.dumps({"json": rel(json_path), "markdown": rel(md_path), "csv": rel(csv_path), "claim_status": CLAIM_STATUS}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
