#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build claim-language guardrails for CAPE-KG reporting and paper drafting."""

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from cape_pre_human_status import effective_prehuman_summary


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_PLAN_FILE = Path("AX_EACL_submission_review_revised_plan.md")
DEFAULT_OUTPUTS_DIR = Path("outputs")
READY_STATUS = "claim_language_guardrails_ready_not_submission_complete"


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path):
    path = Path(path)
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


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
                value = "<br>".join(str(v) for v in value)
            values.append(str(value).replace("|", "\\|").replace("\n", "<br>"))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def claim(
    claim_id,
    area,
    current_status,
    paper_sections,
    evidence_files,
    allowed_now_ko,
    allowed_now_en,
    forbidden_now_ko,
    forbidden_now_en,
    required_before_stronger_claim,
    safe_phrasing_ko,
    safe_phrasing_en,
    unsafe_phrasing_examples,
    next_gate,
):
    evidence = [file_state(path) for path in evidence_files]
    missing = [row["path"] for row in evidence if not row["exists"] or row["bytes"] == 0]
    return {
        "claim_id": claim_id,
        "area": area,
        "current_status": current_status,
        "paper_sections": paper_sections,
        "evidence_files": evidence,
        "missing_evidence_files": missing,
        "allowed_now_ko": allowed_now_ko,
        "allowed_now_en": allowed_now_en,
        "forbidden_now_ko": forbidden_now_ko,
        "forbidden_now_en": forbidden_now_en,
        "required_before_stronger_claim": required_before_stronger_claim,
        "safe_phrasing_ko": safe_phrasing_ko,
        "safe_phrasing_en": safe_phrasing_en,
        "unsafe_phrasing_examples": unsafe_phrasing_examples,
        "next_gate": next_gate,
    }


def build_claims(exp_dir, plan_file, outputs_dir):
    exp_dir = Path(exp_dir)
    plan_file = Path(plan_file)
    outputs_dir = Path(outputs_dir)
    release = exp_dir / "06_release"
    reports = exp_dir / "07_reports"
    evaluation = exp_dir / "04_evaluation"
    public_bench = exp_dir / "08_public_benchmarks"
    outputs = Path("outputs")
    layer2_node_count = len(read_jsonl(outputs_dir / "07_layer2_graph/layer2_nodes.jsonl"))
    layer2_edge_count = len(read_jsonl(outputs_dir / "07_layer2_graph/layer2_edges.jsonl"))

    return [
        claim(
            "C01_task_and_method_framing",
            "Task framing and CAPE-KG contribution",
            "claimable_setup_or_diagnostic",
            ["Introduction", "Task Definition", "Method"],
            [
                plan_file,
                release / "method_novelty_positioning.md",
                release / "rq_evidence_matrix.md",
                release / "prompt_node_edge_traceability.md",
            ],
            "CAPE-KG를 한국어 장문 업무 문서의 evidence-grounded procedural KG construction task로 정의했고, CQ/schema/evidence/validator/standard bridge를 결합한 pre-human 방법론 산출물을 구축했다고 말할 수 있다.",
            "We can describe CAPE-KG as a pre-human, evidence-grounded procedural KG construction framework combining CQs, schema control, evidence grounding, validation, and standard-taxonomy bridging.",
            "EACL 제출이 완료되었거나, 최종 성능 우수성이 입증되었다고 말하면 안 된다.",
            "Do not say the EACL submission is complete or that final superiority has been proven.",
            [
                "Adjudicated human-gold extraction metrics",
                "IAA and adjudication evidence",
                "Final paper tables refreshed after human returns",
            ],
            "본 연구는 CAPE-KG task framing과 pre-human 실험 인프라를 완성했으며, 최종 성능 claim은 human-gold 이후 확정한다.",
            "We present the CAPE-KG framing and pre-human experimental infrastructure; final performance claims remain gated by human-gold evaluation.",
            [
                "CAPE-KG is ready for EACL submission.",
                "CAPE-KG outperforms all baselines on the target corpus.",
            ],
            "minimum human-gold gates",
        ),
        claim(
            "C02_kg_construction_counts",
            "KG construction counts and structural integrity",
            "claimable_setup_or_diagnostic",
            ["Dataset", "KG Construction", "Analysis"],
            [
                Path("outputs/10_evaluation/final_build_report.md"),
                Path("outputs/07_layer2_graph/layer2_graph_quality_report.md"),
                Path("outputs/12_rdf/cape_kg_shacl_validation_report.md"),
                Path("outputs/09_visualization/kg_viewer.html"),
            ],
            f"Layer 1 NCS/PCF와 Layer 2 업무 KG가 구축되었고, 현재 Layer 2는 {layer2_node_count} nodes, {layer2_edge_count} edges이며 accepted edge evidence 누락과 dangling edge가 없다고 말할 수 있다.",
            f"We can report constructed KG counts and structural checks: Layer 2 currently has {layer2_node_count} nodes and {layer2_edge_count} edges with no missing accepted-edge evidence or dangling edges.",
            "이 count를 human-gold 정답 대비 정확도 또는 추출 성능으로 해석하면 안 된다.",
            "Do not interpret construction counts as human-gold accuracy or extraction quality.",
            [
                "Human verification of node/edge correctness",
                "Error analysis refreshed after adjudication",
            ],
            f"Layer 2 KG construction is complete as an automatic build artifact: {layer2_node_count} nodes and {layer2_edge_count} evidence-linked edges.",
            f"The Layer 2 KG is complete as an automatic build artifact: {layer2_node_count} nodes and {layer2_edge_count} evidence-linked edges.",
            [
                "The constructed KG is correct with high precision.",
                "The KG has been fully validated by humans.",
            ],
            "human correctness validation",
        ),
        claim(
            "C03_main_extraction_performance",
            "Main extraction performance",
            "pending_human_gold",
            ["Experiments", "Main Results", "Conclusion"],
            [
                evaluation / "human_gold_metrics.json",
                evaluation / "human_gold_validation_summary.json",
                release / "claimable_main_table.md",
                release / "post_human_scoring_readiness.md",
                release / "claim_gate_report.md",
            ],
            "현재는 main extraction result가 pending human-gold라고만 말할 수 있다.",
            "At present, main extraction performance must be described as pending human-gold evaluation.",
            "silver/proxy F1을 final main table 또는 논문 성능 우수성으로 제시하면 안 된다.",
            "Do not present silver/proxy F1 as the final main-result table or as superiority evidence.",
            [
                "100+ adjudicated chunks",
                "500+ gold node/edge/evidence items",
                "2+ annotator IAA",
                "P_cape_kg_actual scored against adjudicated human gold",
            ],
            "Main extraction performance is not yet claimable; the scoring pipeline is ready and waiting for adjudicated human-gold returns.",
            "Main extraction performance is not yet claimable; the scoring pipeline is ready pending adjudicated human-gold returns.",
            [
                "CAPE-KG achieves the best extraction F1.",
                "The main table proves the proposed method is superior.",
            ],
            "human-gold annotation, IAA, adjudication, and scoring",
        ),
        claim(
            "C04_evidence_faithfulness",
            "Evidence grounding and faithfulness",
            "pending_human_gold",
            ["Method", "Faithfulness Evaluation", "Error Analysis"],
            [
                evaluation / "evidence_grounding_report.md",
                evaluation / "evidence_span_granularity_report.md",
                evaluation / "human_gold_span_iou_report.md",
                release / "post_human_scoring_readiness.md",
            ],
            "자동 구축 edge의 evidence attachment와 component span diagnostic은 보고할 수 있지만, human-gold faithfulness claim은 보류해야 한다.",
            "We can report automatic evidence attachment and component-span diagnostics, while holding human-gold faithfulness claims.",
            "evidence span 정확도 또는 unsupported edge 감소를 human-gold로 입증했다고 말하면 안 된다.",
            "Do not say evidence-span correctness or unsupported-edge reduction is proven against human gold.",
            [
                "Adjudicated component span returns",
                "Human-gold exact/IoU evidence metrics",
                "Unsupported-edge adjudication",
            ],
            "Evidence diagnostics are available, but faithfulness claims remain diagnostic until adjudicated span evidence is imported.",
            "Evidence diagnostics are available, but faithfulness claims remain diagnostic until adjudicated span evidence is imported.",
            [
                "CAPE-KG eliminates hallucination.",
                "Evidence spans are human-validated.",
            ],
            "adjudicated span and unsupported-edge evaluation",
        ),
        claim(
            "C05_baseline_ablation_superiority",
            "Baseline, ablation, and model-scaling superiority",
            "pending_human_gold",
            ["Experiments", "Ablation", "Model Scaling"],
            [
                evaluation / "actual_llm_silver_metrics.json",
                release / "qwen3_model_scaling_report.md",
                release / "paper_tables.md",
                release / "evaluation_protocol_lock.md",
            ],
            "B0-B6, P_cape_kg_actual, P_minus_* 조건과 Qwen3 scaling을 실행했고, 현재 수치는 silver/proxy diagnostic이라고 말할 수 있다.",
            "We can report that B0-B6, P_cape_kg_actual, P_minus_* ablations, and Qwen3 scaling diagnostics were run.",
            "P_cape_kg_actual이 baseline보다 최종적으로 우수하다고 말하면 안 된다.",
            "Do not claim final superiority of P_cape_kg_actual over baselines yet.",
            [
                "Same frozen metric definitions applied to adjudicated human gold",
                "Final statistical tests after human-gold scoring",
            ],
            "Baseline, ablation, and scaling runs are complete as silver/proxy diagnostics; final comparative claims require human-gold scoring.",
            "Baseline, ablation, and scaling runs are complete as silver/proxy diagnostics; final comparative claims require human-gold scoring.",
            [
                "Qwen3-32B-AWQ proves monotonic model scaling.",
                "The ablation proves CQ improves final F1.",
            ],
            "human-gold comparative scoring",
        ),
        claim(
            "C06_structural_diagnostics",
            "Structural conformance, procedural consistency, and CQ answerability",
            "claimable_setup_or_diagnostic",
            ["Evaluation", "Analysis"],
            [
                evaluation / "structural_evaluation_report.md",
                release / "cq_query_pack.md",
                evaluation / "structural_gap_worklist_report.md",
                Path("outputs/12_rdf/cape_kg_shacl_validation_report.md"),
            ],
            "ontology conformance, procedural consistency, CQ answerability 같은 자동 구조 진단은 보고할 수 있다.",
            "We can report automatic structural diagnostics such as ontology conformance, procedural consistency, and CQ answerability.",
            "구조적으로 answerable하다는 사실을 답변의 human-gold correctness로 해석하면 안 된다.",
            "Do not treat structural answerability as human-gold answer correctness.",
            [
                "Human-gold correctness check for extracted items",
                "Human review of structural gap worklist",
            ],
            "Structural diagnostics indicate schema and query coverage, not final semantic correctness.",
            "Structural diagnostics indicate schema and query coverage, not final semantic correctness.",
            [
                "All competency questions are correctly answered.",
                "The KG is semantically complete.",
            ],
            "human semantic correctness review",
        ),
        claim(
            "C07_public_benchmark_adapter",
            "Public benchmark adapter diagnostics",
            "claimable_setup_or_diagnostic",
            ["Experiments", "Generalization Check", "Reproducibility"],
            [
                public_bench / "public_benchmark_crosscheck_summary.json",
                public_bench / "public_benchmark_crosscheck_report.md",
                release / "public_reproducibility_manifest.md",
            ],
            "PAGED/Text2KG adapter 기반 public cross-check를 auxiliary diagnostic으로 실행했다고 말할 수 있다.",
            "We can report the PAGED/Text2KG adapter runs as auxiliary diagnostics.",
            "public benchmark 결과를 private Korean enterprise corpus의 main result로 대체하면 안 된다.",
            "Do not replace the private Korean enterprise main result with public-adapter diagnostics.",
            [
                "Final private-corpus human-gold scoring",
                "Explicit benchmark scope and adapter limitations",
            ],
            "Public benchmark runs are auxiliary adapter diagnostics, not official leaderboard or private-corpus main evidence.",
            "Public benchmark runs are auxiliary adapter diagnostics, not official leaderboard or private-corpus main evidence.",
            [
                "The public benchmark proves generalization of the private-corpus method.",
                "These are official benchmark leaderboard results.",
            ],
            "scope-limited auxiliary reporting",
        ),
        claim(
            "C08_mapping_crosswalk",
            "NCS/PCF mapping and NCS-PCF crosswalk",
            "pending_expert_review",
            ["Downstream Evaluation", "Standard Taxonomy Bridge"],
            [
                evaluation / "mapping_downstream_report.md",
                evaluation / "mapping_expert_metrics.json",
                evaluation / "ncs_pcf_crosswalk_report.md",
                evaluation / "crosswalk_expert_metrics.json",
                release / "mapping_review_progress_report.md",
            ],
            "NCS/PCF Top-K mapping 후보와 Layer2-bridged NCS-PCF crosswalk 후보를 생성했다고 말할 수 있다.",
            "We can report that NCS/PCF Top-K mapping candidates and Layer2-bridged NCS-PCF crosswalk candidates were generated.",
            "expert review 없이 P@K, MRR, nDCG@10, utility, accept-rate를 주장하면 안 된다.",
            "Do not claim P@K, MRR, nDCG@10, utility, or accept-rate without expert review.",
            [
                "Mapping expert review returns",
                "Crosswalk expert review returns",
                "Refreshed downstream metrics",
            ],
            "The standard bridge is candidate-generation evidence only until mapping and crosswalk expert review is complete.",
            "The standard bridge is candidate-generation evidence only until mapping and crosswalk expert review is complete.",
            [
                "CAPE-KG improves NCS/PCF mapping accuracy.",
                "The crosswalk utility is expert-validated.",
            ],
            "mapping and crosswalk expert review",
        ),
        claim(
            "C09_active_review_efficiency",
            "Active-review efficiency",
            "pending_human_effort",
            ["Human-in-the-loop Evaluation", "Active Review"],
            [
                release / "active_review_human_effort_plan.md",
                release / "active_review_human_effort_briefing.md",
                evaluation / "active_review_human_effort_report.md",
                evaluation / "active_review_efficiency_report.md",
            ],
            "active/uncertainty/random review queue와 human-effort 입력 양식이 준비되었다고 말할 수 있다.",
            "We can report that active/uncertainty/random review queues and human-effort templates are ready.",
            "사람 검수 시간이 절감되었거나 active review가 더 효율적이었다고 말하면 안 된다.",
            "Do not claim reduced review time or active-review efficiency yet.",
            [
                "Returned active-review human-effort CSV",
                "Timing/correction evidence",
                "Efficiency metrics refreshed after returns",
            ],
            "Active-review artifacts support review navigation only; efficiency claims require returned timing and correction evidence.",
            "Active-review artifacts support review navigation only; efficiency claims require returned timing and correction evidence.",
            [
                "Active review reduces annotation cost.",
                "The queue is proven more efficient than random review.",
            ],
            "active-review effort return file",
        ),
        claim(
            "C10_reproducibility_release",
            "Reproducibility, data release, and ethics",
            "rights_review_required",
            ["Limitations", "Ethics", "Reproducibility", "Artifact Appendix"],
            [
                release / "release_bundle_manifest.json",
                release / "latest_release_bundle_index.md",
                release / "data_release_ethics_statement.md",
                release / "external_resource_license_report.md",
                release / "public_reproducibility_manifest.md",
                release / "public_synthetic_examples/README.md",
            ],
            "code, prompt, schema, synthetic public-safe examples, public-safe bundle 경계를 설명할 수 있다.",
            "We can describe code, prompts, schema, synthetic public-safe examples, and public-safe bundle boundaries.",
            "원문 corpus 또는 내부 검수 파일을 공개할 수 있다고 말하면 안 된다.",
            "Do not claim raw source corpus or internal review files can be released publicly.",
            [
                "Rights review for any source-text release",
                "Final public artifact audit after paper claims are fixed",
            ],
            "Reproducibility is supported through public-safe artifacts; source-text release remains rights-gated.",
            "Reproducibility is supported through public-safe artifacts; source-text release remains rights-gated.",
            [
                "All data will be publicly released.",
                "The public bundle contains the full private corpus.",
            ],
            "rights review and public-safe audit",
        ),
    ]


def build_payload(exp_dir, plan_file, outputs_dir):
    exp_dir = Path(exp_dir)
    release = exp_dir / "06_release"
    claims = build_claims(exp_dir, plan_file, outputs_dir)
    claim_gate = read_json(release / "claim_gate_report.json", {}) or {}
    prehuman = read_json(release / "pre_human_handoff_validation.json", {}) or {}
    effective_prehuman = effective_prehuman_summary(prehuman)
    readiness = read_json(release / "submission_readiness_audit.json", {}) or {}
    status_counts = Counter(row["current_status"] for row in claims)
    missing = sorted({path for row in claims for path in row["missing_evidence_files"]})
    claimable_statuses = {"claimable_setup_or_diagnostic"}
    pending_statuses = {"pending_human_gold", "pending_expert_review", "pending_human_effort"}
    summary = {
        "claim_count": len(claims),
        "status_counts": dict(sorted(status_counts.items())),
        "claimable_now_count": sum(1 for row in claims if row["current_status"] in claimable_statuses),
        "pending_human_or_expert_count": sum(1 for row in claims if row["current_status"] in pending_statuses),
        "rights_review_required_count": sum(1 for row in claims if row["current_status"] == "rights_review_required"),
        "missing_evidence_files": len(missing),
        "safe_to_use_as_submission": False,
        "submission_ready": False,
        "claim_gate_overall_status": claim_gate.get("overall_status"),
        "claim_gate_required_failure_count": claim_gate.get("required_failure_count"),
        "claim_gate_optional_failure_count": claim_gate.get("optional_failure_count"),
        "pre_human_validation_status": effective_prehuman.get("overall_status"),
        "pre_human_validation_checks": effective_prehuman.get("check_count"),
        "readiness_claim_status": readiness.get("claim_status"),
    }
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "plan_file": rel(plan_file),
        "experiment_dir": rel(exp_dir),
        "overall_status": "PASS" if not missing else "FAIL",
        "claim_status": READY_STATUS if not missing else "claim_language_guardrails_incomplete",
        "safe_to_use_as_submission": False,
        "submission_ready": False,
        "summary": summary,
        "claims": claims,
        "missing_evidence_files": missing,
        "claim_policy": [
            "Use claimable_setup_or_diagnostic wording only for setup, construction, structural diagnostics, and reproducibility framing.",
            "Use diagnostic_only or pending wording for any silver/proxy metric.",
            "Do not state final extraction superiority until adjudicated human-gold scoring is complete.",
            "Do not state NCS/PCF mapping utility until expert review returns are imported.",
            "Do not state active-review efficiency until timing/correction evidence is returned.",
            "Do not state public release of source text until rights review is complete.",
        ],
    }


def render_report(payload):
    summary = payload["summary"]
    lines = [
        "# CAPE-KG Claim Language Guardrails",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Plan: `{payload['plan_file']}`",
        f"Experiment: `{payload['experiment_dir']}`",
        "",
        "이 문서는 논문 초안, 발표자료, 교수님 보고에서 사용할 수 있는 표현과 아직 쓰면 안 되는 표현을 claim 단위로 고정한 guardrail입니다. 현재 상태는 pre-human handoff ready이며, 최종 제출 승인이나 최종 성능 claim이 아닙니다.",
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
                {"Item": "Claims", "Value": summary["claim_count"]},
                {"Item": "Claimable setup/diagnostic claims", "Value": summary["claimable_now_count"]},
                {"Item": "Pending human/expert claims", "Value": summary["pending_human_or_expert_count"]},
                {"Item": "Rights-review gated claims", "Value": summary["rights_review_required_count"]},
                {"Item": "Missing evidence files", "Value": summary["missing_evidence_files"]},
                {"Item": "Claim gate", "Value": summary["claim_gate_overall_status"]},
                {"Item": "Pre-human validation", "Value": summary["pre_human_validation_status"]},
                {"Item": "Pre-human checks", "Value": summary["pre_human_validation_checks"]},
            ],
        ),
        "",
        "## Claim Policy",
        "",
    ]
    for rule in payload["claim_policy"]:
        lines.append(f"- {rule}")
    lines += [
        "",
        "## Guardrail Table",
        "",
        md_table(
            [
                "claim_id",
                "area",
                "current_status",
                "safe_phrasing_ko",
                "safe_phrasing_en",
                "next_gate",
            ],
            [
                {
                    "claim_id": row["claim_id"],
                    "area": row["area"],
                    "current_status": row["current_status"],
                    "safe_phrasing_ko": row["safe_phrasing_ko"],
                    "safe_phrasing_en": row["safe_phrasing_en"],
                    "next_gate": row["next_gate"],
                }
                for row in payload["claims"]
            ],
        ),
        "",
        "## Claim Details",
        "",
    ]
    for row in payload["claims"]:
        lines += [
            f"### {row['claim_id']}. {row['area']}",
            "",
            f"- Current status: `{row['current_status']}`",
            f"- Paper sections: {', '.join(row['paper_sections'])}",
            f"- Next gate: {row['next_gate']}",
            "",
            "Allowed now:",
            "",
            f"- KO: {row['allowed_now_ko']}",
            f"- EN: {row['allowed_now_en']}",
            "",
            "Forbidden now:",
            "",
            f"- KO: {row['forbidden_now_ko']}",
            f"- EN: {row['forbidden_now_en']}",
            "",
            "Required before stronger claim:",
        ]
        for item in row["required_before_stronger_claim"]:
            lines.append(f"- {item}")
        lines += [
            "",
            "Unsafe phrasing examples:",
        ]
        for item in row["unsafe_phrasing_examples"]:
            lines.append(f"- {item}")
        lines += [
            "",
            "Evidence files:",
        ]
        for evidence in row["evidence_files"]:
            suffix = "" if evidence["exists"] and evidence["bytes"] > 0 else " (missing_or_empty)"
            lines.append(f"- `{evidence['path']}`{suffix}")
        lines.append("")
    lines += [
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
        "- 이 파일의 safe phrasing은 현재 pre-human 발표/보고/초안에 사용할 수 있는 보수적 표현입니다.",
        "- `pending_human_gold`, `pending_expert_review`, `pending_human_effort` claim은 final main table이나 conclusion에 성능 claim으로 쓰지 않습니다.",
        "- `rights_review_required` claim은 public-safe artifact 범위까지만 설명하고, 원문 corpus 공개 가능성은 별도 권리 검토 전까지 주장하지 않습니다.",
    ]
    return "\n".join(lines) + "\n"


def run(args):
    payload = build_payload(args.experiment_dir, args.plan_file, args.outputs_dir)
    release = Path(args.experiment_dir) / "06_release"
    json_path = release / "claim_language_guardrails.json"
    md_path = release / "claim_language_guardrails.md"
    write_json(json_path, payload)
    write_text(md_path, render_report(payload))
    print(
        json.dumps(
            {
                "json": rel(json_path),
                "markdown": rel(md_path),
                "overall_status": payload["overall_status"],
                "claim_status": payload["claim_status"],
                "claim_count": payload["summary"]["claim_count"],
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
    parser.add_argument("--outputs-dir", default=str(DEFAULT_OUTPUTS_DIR))
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
