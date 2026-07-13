#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build an RQ-to-evidence matrix for the CAPE-KG EACL experiment."""

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


def count_jsonl(path):
    path = Path(path)
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def file_evidence(path, role, required=True):
    path = Path(path)
    exists = path.exists() and path.is_file()
    return {
        "path": rel(path),
        "role": role,
        "required": bool(required),
        "exists": exists,
        "bytes": path.stat().st_size if exists else 0,
    }


def find_metric(metrics, condition):
    for row in metrics.get("metrics", []) if isinstance(metrics, dict) else []:
        if row.get("condition") == condition:
            return row
    return {}


def count_experiment_cqs(traceability, exp_dir):
    cqs = (traceability.get("competency_questions") or {}).get("experiment_cqs") if isinstance(traceability, dict) else None
    if isinstance(cqs, list):
        return len(cqs)
    source_cqs = read_json(Path(exp_dir) / "02_schema/competency_questions.json", []) or []
    return len(source_cqs) if isinstance(source_cqs, list) else 0


def readiness_by_id(readiness):
    return {row.get("id"): row for row in (readiness or {}).get("items", [])}


def compact_files(files):
    return [item for item in files if item.get("required") or item.get("exists")]


def build_matrix(exp_dir, outputs_dir):
    exp_dir = Path(exp_dir)
    outputs_dir = Path(outputs_dir)
    release_dir = exp_dir / "06_release"
    eval_dir = exp_dir / "04_evaluation"

    actual_metrics = read_json(eval_dir / "actual_llm_silver_metrics.json", {}) or {}
    structural = read_json(eval_dir / "structural_evaluation_metrics.json", {}) or {}
    span = read_json(eval_dir / "evidence_span_granularity_metrics.json", {}) or {}
    mapping = read_json(eval_dir / "mapping_expert_metrics.json", {}) or {}
    crosswalk_review = read_json(eval_dir / "crosswalk_expert_metrics.json", {}) or {}
    active = read_json(eval_dir / "active_review_efficiency_metrics.json", {}) or {}
    effort = read_json(eval_dir / "active_review_human_effort_metrics.json", {}) or {}
    effort_briefing = read_json(release_dir / "active_review_human_effort_briefing.json", {}) or {}
    human_gold = read_json(eval_dir / "human_gold_metrics.json", {}) or {}
    readiness = read_json(release_dir / "submission_readiness_audit.json", {}) or {}
    checklist = read_json(release_dir / "paper_readiness_checklist.json", {}) or {}
    traceability = read_json(release_dir / "prompt_node_edge_traceability.json", {}) or {}

    readiness_items = readiness_by_id(readiness)
    proposed = find_metric(actual_metrics, "P_cape_kg_actual")
    ontology = structural.get("ontology_conformance") or {}
    procedural = structural.get("procedural_consistency") or {}
    cq = structural.get("cq_answerability") or {}
    human_validation = human_gold.get("validation") or {}

    ncs_mapping = outputs_dir / "08_mapping/l2_ncs_mapping_candidates.jsonl"
    pcf_mapping = outputs_dir / "08_mapping/l2_pcf_mapping_candidates.jsonl"
    ncs_count = count_jsonl(ncs_mapping)
    pcf_count = count_jsonl(pcf_mapping)

    mapping_metrics = mapping.get("metrics") or []
    mapping_pending_rows = sum(int(row.get("pending_rows") or 0) for row in mapping_metrics if isinstance(row, dict))
    mapping_completed_rows = sum(int(row.get("completed_rows") or 0) for row in mapping_metrics if isinstance(row, dict))
    crosswalk_review_metrics = crosswalk_review.get("metrics") or {}

    common_human_blockers = [
        readiness_items.get("min.gold_chunks", {}).get("next_step", "Complete 100+ adjudicated human-gold chunks."),
        readiness_items.get("min.gold_items", {}).get("next_step", "Complete 500+ adjudicated gold node/edge/evidence items."),
        readiness_items.get("min.iaa", {}).get("next_step", "Compute IAA from two annotators."),
        readiness_items.get("min.proposed", {}).get("next_step", "Score proposed method against adjudicated human gold."),
    ]
    common_human_blockers = [item for item in common_human_blockers if item]

    rows = [
        {
            "rq_id": "RQ1",
            "title": "Evidence-grounded procedural KG extraction",
            "question": "한국어 장문 업무 문서에서 Task, ProcedureStep, DecisionGateway, GuardCondition, ArtifactFlow를 추출할 때 evidence-span grounding을 강제하면 unsupported triple과 hallucination을 줄일 수 있는가?",
            "plan_metrics": [
                "Node F1",
                "Edge F1",
                "Evidence Exact Match",
                "Evidence IoU",
                "Unsupported Edge Rate",
            ],
            "current_status": "automatic_diagnostic_ready_human_gold_pending",
            "claim_ready": False,
            "claim_scope": "Final extraction quality claims require adjudicated human-gold nodes, edges, and evidence spans.",
            "current_values": {
                "final_layer2_nodes": ontology.get("node_count"),
                "final_layer2_edges": ontology.get("edge_count"),
                "evidence_missing_edge_count": ontology.get("evidence_missing_edge_count"),
                "dangling_edge_count": ontology.get("dangling_edge_count"),
                "component_span_claim_status": span.get("claim_status"),
                "component_count": span.get("component_count"),
                "exact_component_span_rate": span.get("exact_component_span_rate"),
                "predicate_full_sentence_proxy_rate": span.get("predicate_full_sentence_proxy_rate"),
                "proposed_silver_edge_f1": proposed.get("edge_exact_f1"),
                "proposed_silver_evidence_f1": proposed.get("evidence_f1"),
                "human_gold_completed_chunks": human_validation.get("completed_adjudicated_chunks"),
                "human_gold_items": human_validation.get("gold_item_count_for_readiness"),
            },
            "evidence_files": compact_files(
                [
                    file_evidence(eval_dir / "actual_llm_silver_metrics.json", "silver/proxy extraction diagnostics"),
                    file_evidence(eval_dir / "actual_llm_silver_evaluation_report.md", "silver/proxy extraction report"),
                    file_evidence(eval_dir / "evidence_span_granularity_metrics.json", "component span diagnostic"),
                    file_evidence(eval_dir / "evidence_span_granularity_report.md", "component span report"),
                    file_evidence(outputs_dir / "06_triples/layer2_triples_component_spans.jsonl", "component span handoff"),
                    file_evidence(eval_dir / "human_gold_metrics.json", "human-gold scoring placeholder"),
                    file_evidence(eval_dir / "human_gold_validation_summary.json", "human-gold completion state"),
                ]
            ),
            "remaining_for_final_claim": common_human_blockers,
        },
        {
            "rq_id": "RQ2",
            "title": "CQ-anchored schema control",
            "question": "Competency Question을 schema selection, LLM extraction, validation, evaluation의 anchor로 사용할 때 ontology conformance와 CQ answerability가 향상되는가?",
            "plan_metrics": [
                "Ontology Conformance",
                "Procedural Consistency",
                "CQ Answerability",
                "Ablation: P - CQ",
                "Ablation: P - Schema retrieval",
                "Ablation: P - Validator",
            ],
            "current_status": "structural_diagnostic_ready_human_gold_pending",
            "claim_ready": False,
            "claim_scope": "Structural conformance can be reported as an automatic diagnostic; final quality improvements require human-gold scoring.",
            "current_values": {
                "cq_count": count_experiment_cqs(traceability, exp_dir),
                "ontology_conformance_rate": ontology.get("ontology_conformance_rate"),
                "domain_range_violation_count": ontology.get("domain_range_violation_count"),
                "procedural_consistency_rate": procedural.get("procedural_consistency_rate"),
                "procedural_consistency_issue_count": procedural.get("procedural_consistency_issue_count"),
                "cq_answerability_rate": cq.get("cq_answerability_rate"),
                "ablation_conditions_available": [
                    "P_minus_CQ",
                    "P_minus_Procedural_schema",
                    "P_minus_Schema_retrieval",
                    "P_minus_Validator",
                ],
            },
            "evidence_files": compact_files(
                [
                    file_evidence(exp_dir / "02_schema/competency_questions.json", "experiment CQ inventory"),
                    file_evidence(outputs_dir / "03_schema/competency_questions.json", "internal build CQ inventory"),
                    file_evidence(eval_dir / "structural_evaluation_metrics.json", "combined structural metrics"),
                    file_evidence(eval_dir / "ontology_conformance_metrics.json", "ontology conformance metrics"),
                    file_evidence(eval_dir / "procedural_consistency_metrics.json", "procedural consistency metrics"),
                    file_evidence(eval_dir / "cq_answerability_structural_metrics.json", "CQ answerability metrics"),
                    file_evidence(eval_dir / "cq_answerability_by_condition.csv", "CQ answerability by LLM condition"),
                    file_evidence(release_dir / "prompt_node_edge_traceability.json", "prompt/CQ/node-edge traceability"),
                ]
            ),
            "remaining_for_final_claim": common_human_blockers,
        },
        {
            "rq_id": "RQ3",
            "title": "Standard taxonomy bridge",
            "question": "Layer2 procedural KG가 NCS/PCF 표준 taxonomy mapping의 downstream 성능을 향상시키는가?",
            "plan_metrics": [
                "NCS/PCF Mapping P@K",
                "P@1",
                "P@5",
                "MRR",
                "nDCG@10",
                "Expert accept rate",
                "Explanation quality score",
            ],
            "current_status": "candidate_pipeline_ready_expert_review_pending",
            "claim_ready": False,
            "claim_scope": "Candidate generation and rerank diagnostics are ready; downstream mapping performance claims require expert review.",
            "current_values": {
                "ncs_mapping_candidates": ncs_count,
                "pcf_mapping_candidates": pcf_count,
                "mapping_completed_rows": mapping_completed_rows,
                "mapping_pending_rows": mapping_pending_rows,
                "mapping_claim_status": mapping.get("claim_status"),
                "crosswalk_candidate_rows": crosswalk_review_metrics.get("candidate_rows"),
                "crosswalk_source_task_count": crosswalk_review_metrics.get("source_task_count"),
                "crosswalk_completed_rows": crosswalk_review_metrics.get("completed_rows"),
                "crosswalk_pending_rows": crosswalk_review_metrics.get("pending_rows"),
                "crosswalk_claim_status": crosswalk_review.get("claim_status"),
            },
            "evidence_files": compact_files(
                [
                    file_evidence(ncs_mapping, "Layer2-to-NCS mapping candidates"),
                    file_evidence(pcf_mapping, "Layer2-to-PCF mapping candidates"),
                    file_evidence(eval_dir / "mapping_downstream_results.csv", "mapping downstream arm diagnostics"),
                    file_evidence(eval_dir / "mapping_downstream_arm_rerank_summary.json", "mapping rerank summary"),
                    file_evidence(eval_dir / "ncs_pcf_crosswalk_summary.json", "Layer2-bridged crosswalk candidates"),
                    file_evidence(eval_dir / "mapping_expert_metrics.json", "expert-review metric placeholder"),
                    file_evidence(eval_dir / "crosswalk_expert_metrics.json", "NCS-PCF crosswalk expert-review metric placeholder"),
                    file_evidence(exp_dir / "01_data/crosswalk_review/crosswalk_review_manifest.json", "NCS-PCF crosswalk expert-review manifest"),
                    file_evidence(release_dir / "mapping_review_progress_summary.json", "expert review progress"),
                ]
            ),
            "remaining_for_final_claim": [
                readiness_items.get("strong.mapping_downstream", {}).get(
                    "next_step",
                    "Complete expert review for mapping candidates and recompute P@K/MRR/nDCG@10.",
                ),
                "Complete NCS-PCF crosswalk expert review and recompute accept-rate, Hit@K, P@10, MRR, nDCG@10, utility, and explanation-quality metrics.",
            ],
        },
        {
            "rq_id": "RQ4",
            "title": "Human review efficiency",
            "question": "Evidence verifier와 active review queue가 전문가 검수 비용을 줄이면서 KG 품질을 높이는가?",
            "plan_metrics": [
                "Active Review Efficiency",
                "Corrected high-impact errors per hour",
                "Precision@K",
                "Recall@K",
                "Lift vs random review",
                "Ablation: P - Active review",
            ],
            "current_status": "review_queue_ready_human_effort_pending",
            "claim_ready": False,
            "claim_scope": "Silver/proxy prioritization and human-effort templates are ready; review-cost claims require completed human timing/correction returns.",
            "current_values": {
                "active_review_claim_status": active.get("claim_status"),
                "candidate_count": active.get("candidate_count"),
                "silver_proxy_high_impact_error_count": active.get("high_impact_error_count"),
                "human_effort_claim_status": effort.get("claim_status"),
                "human_effort_reviewed_file_present": effort.get("reviewed_file_present"),
                "human_effort_pooled_rows": effort.get("pooled_rows"),
                "human_effort_arm_counts": effort.get("arm_counts"),
                "human_effort_briefing_claim_status": effort_briefing.get("claim_status"),
                "human_effort_briefing_rows": effort_briefing.get("briefing_rows"),
            },
            "evidence_files": compact_files(
                [
                    file_evidence(eval_dir / "active_review_efficiency_metrics.json", "silver/proxy active review diagnostic"),
                    file_evidence(eval_dir / "active_review_efficiency_report.md", "silver/proxy active review report"),
                    file_evidence(eval_dir / "active_review_ablation_metrics.json", "active-review ablation diagnostic"),
                    file_evidence(eval_dir / "active_review_human_effort_metrics.json", "human-effort collection state"),
                    file_evidence(eval_dir / "active_review_human_effort_report.md", "human-effort report"),
                    file_evidence(release_dir / "active_review_human_effort_briefing.json", "human-effort briefing summary"),
                    file_evidence(release_dir / "active_review_human_effort_briefing.md", "human-effort briefing"),
                    file_evidence(exp_dir / "05_review/actual_llm_active_review_queue_P_cape_kg_actual.csv", "active review queue"),
                    file_evidence(exp_dir / "05_review/active_review_human_effort_template.csv", "human-effort return template"),
                    file_evidence(exp_dir / "05_review/active_review_human_effort_briefing.csv", "human-effort review navigation CSV"),
                    file_evidence(release_dir / "active_review_human_effort_plan.md", "human-effort protocol"),
                ]
            ),
            "remaining_for_final_claim": [
                readiness_items.get("strong.active_review", {}).get(
                    "next_step",
                    "Collect reviewed active-review human-effort CSV and validate efficiency against human adjudication outcomes.",
                )
            ],
        },
    ]

    missing_required_files = []
    for row in rows:
        for item in row["evidence_files"]:
            if item["required"] and not item["exists"]:
                missing_required_files.append({"rq_id": row["rq_id"], "path": item["path"], "role": item["role"]})

    summary = {
        "rq_count": len(rows),
        "claim_ready_count": sum(1 for row in rows if row["claim_ready"]),
        "automatic_or_candidate_ready_count": sum(1 for row in rows if row["current_status"]),
        "human_or_expert_pending_count": sum(1 for row in rows if not row["claim_ready"]),
        "missing_required_evidence_files": len(missing_required_files),
        "readiness_claim_status": readiness.get("claim_status"),
        "paper_readiness_minimum_items": len(checklist.get("minimum_accept_checklist") or []),
        "paper_readiness_strong_items": len(checklist.get("strong_accept_checklist") or []),
    }

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_plan": "AX_EACL_submission_review_revised_plan.md",
        "experiment_dir": rel(exp_dir),
        "outputs_dir": rel(outputs_dir),
        "claim_scope": "pre_human_gold_rq_evidence_matrix",
        "summary": summary,
        "research_questions": rows,
        "missing_required_evidence_files": missing_required_files,
    }


def render_md(payload):
    lines = [
        "# CAPE-KG RQ-to-Evidence Matrix",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Plan: `{payload['source_plan']}`",
        f"Experiment: `{payload['experiment_dir']}`",
        "",
        "이 문서는 revised EACL plan의 RQ1-RQ4가 현재 어떤 산출물과 평가 증거로 연결되는지 정리한 release artifact입니다.",
        "자동 진단과 최종 논문 claim을 분리하기 위해, 각 RQ마다 현재 상태와 남은 human/expert 검수 단계를 같이 적었습니다.",
        "",
        "## Summary",
        "",
    ]
    summary = payload["summary"]
    for key in [
        "rq_count",
        "claim_ready_count",
        "automatic_or_candidate_ready_count",
        "human_or_expert_pending_count",
        "missing_required_evidence_files",
        "readiness_claim_status",
    ]:
        lines.append(f"- {key}: {summary.get(key)}")

    lines.extend(
        [
            "",
            "## RQ Matrix",
            "",
            "| RQ | 연구질문 | 현재 상태 | 최종 claim 가능 여부 | 핵심 증거 | 남은 단계 |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in payload["research_questions"]:
        files = ", ".join(f"`{item['path']}`" for item in row["evidence_files"][:4])
        if len(row["evidence_files"]) > 4:
            files += f", +{len(row['evidence_files']) - 4} more"
        remaining = "<br>".join(row["remaining_for_final_claim"])
        lines.append(
            "| {rq_id} | {question} | `{status}` | {claim_ready} | {files} | {remaining} |".format(
                rq_id=row["rq_id"],
                question=row["question"],
                status=row["current_status"],
                claim_ready="yes" if row["claim_ready"] else "no",
                files=files,
                remaining=remaining,
            )
        )

    for row in payload["research_questions"]:
        lines.extend(
            [
                "",
                f"## {row['rq_id']}. {row['title']}",
                "",
                f"- Question: {row['question']}",
                f"- Current status: `{row['current_status']}`",
                f"- Claim ready: {'yes' if row['claim_ready'] else 'no'}",
                f"- Claim scope: {row['claim_scope']}",
                "",
                "### Plan Metrics",
                "",
            ]
        )
        for metric in row["plan_metrics"]:
            lines.append(f"- {metric}")
        lines.extend(["", "### Current Values", ""])
        for key, value in row["current_values"].items():
            lines.append(f"- {key}: `{value}`")
        lines.extend(["", "### Evidence Files", "", "| role | path | exists |", "| --- | --- | --- |"])
        for item in row["evidence_files"]:
            lines.append(f"| {item['role']} | `{item['path']}` | {item['exists']} |")
        lines.extend(["", "### Remaining For Final Claim", ""])
        for item in row["remaining_for_final_claim"]:
            lines.append(f"- {item}")

    if payload["missing_required_evidence_files"]:
        lines.extend(["", "## Missing Required Evidence Files", ""])
        for item in payload["missing_required_evidence_files"]:
            lines.append(f"- {item['rq_id']}: `{item['path']}` ({item['role']})")
    else:
        lines.extend(["", "## Missing Required Evidence Files", "", "- None"])

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- RQ1/RQ2는 자동 구조 진단과 silver/proxy LLM 진단이 준비된 상태입니다.",
            "- RQ3는 NCS/PCF mapping 후보와 downstream scaffold가 준비되었지만 expert review 전입니다.",
            "- RQ4는 active review queue와 human-effort template이 준비되었지만 실제 human timing/correction 결과 전입니다.",
            "- 네 RQ 모두 최종 성능 claim은 human-gold, IAA, adjudication 또는 expert review 이후에만 가능합니다.",
        ]
    )
    return "\n".join(lines) + "\n"


def run(args):
    payload = build_matrix(args.experiment_dir, args.outputs_dir)
    release_dir = Path(args.experiment_dir) / "06_release"
    json_path = release_dir / "rq_evidence_matrix.json"
    md_path = release_dir / "rq_evidence_matrix.md"
    write_json(json_path, payload)
    write_text(md_path, render_md(payload))
    print(json.dumps({"json": rel(json_path), "md": rel(md_path), "summary": payload["summary"]}, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--outputs-dir", default=str(DEFAULT_OUTPUTS_DIR))
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
