#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a section-to-source map for the CAPE-KG EACL paper draft."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_PLAN_FILE = Path("AX_EACL_submission_review_revised_plan.md")

READY_CLAIM_STATUS = "paper_section_source_map_ready_not_submission_complete"


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
            values.append(str(value).replace("|", "\\|"))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def section_specs(exp_dir):
    release = exp_dir / "06_release"
    evaluation = exp_dir / "04_evaluation"
    reports = exp_dir / "07_reports"
    public_bench = exp_dir / "08_public_benchmarks"
    return [
        {
            "section_id": "S01",
            "planned_section": "Abstract / contribution framing",
            "draft_anchor": "## Abstract Draft",
            "evidence_files": [
                release / "method_novelty_positioning.md",
                release / "rq_evidence_matrix.md",
                release / "claimable_main_table.md",
            ],
            "claim_status": "claimable_setup_not_final_performance",
            "paper_use_now": "yes_with_claim_safety",
            "blocking_gate_ids": ["gold.completed_chunks", "gold.item_count", "gold.iaa", "llm.proposed_human_gold_score"],
            "notes": "Use for framing and planned contribution only; final performance language must wait for human-gold scoring.",
        },
        {
            "section_id": "S02",
            "planned_section": "Introduction",
            "draft_anchor": "## Introduction",
            "evidence_files": [
                release / "method_novelty_positioning.md",
                release / "rq_evidence_matrix.md",
                release / "claim_gate_report.md",
            ],
            "claim_status": "claimable_setup_not_final_performance",
            "paper_use_now": "yes_with_claim_safety",
            "blocking_gate_ids": ["gold.completed_chunks", "gold.item_count", "gold.iaa", "llm.proposed_human_gold_score"],
            "notes": "Problem framing and gap statements are usable; quantitative superiority claims remain blocked.",
        },
        {
            "section_id": "S03",
            "planned_section": "Related Work",
            "draft_anchor": "## Related Work",
            "evidence_files": [
                release / "method_novelty_positioning.md",
                release / "reviewer_risk_register.md",
            ],
            "claim_status": "claimable_positioning",
            "paper_use_now": "yes",
            "blocking_gate_ids": [],
            "notes": "Positioning is supported by novelty/risk artifacts; citation polishing remains a writing task.",
        },
        {
            "section_id": "S04",
            "planned_section": "Task Definition",
            "draft_anchor": "## Task Definition",
            "evidence_files": [
                exp_dir / "02_schema/cape_schema.json",
                release / "cq_query_pack.md",
                release / "prompt_node_edge_traceability.md",
            ],
            "claim_status": "claimable_setup",
            "paper_use_now": "yes",
            "blocking_gate_ids": [],
            "notes": "CQ, schema, evidence grounding, and standard-bridge task definitions are documented.",
        },
        {
            "section_id": "S05",
            "planned_section": "Dataset and Annotation",
            "draft_anchor": "## Dataset and Annotation",
            "evidence_files": [
                release / "annotation_qc_report.md",
                release / "gold_sampling_coverage_report.md",
                release / "human_review_master_checklist_ko.md",
                release / "human_review_packet_integrity.md",
            ],
            "claim_status": "pending_human_gold",
            "paper_use_now": "setup_only",
            "blocking_gate_ids": ["gold.completed_chunks", "gold.item_count", "gold.iaa"],
            "notes": "Sampling and review packet readiness are documented, but adjudicated labels and IAA are not complete.",
        },
        {
            "section_id": "S06",
            "planned_section": "Method: CAPE-KG",
            "draft_anchor": "## Method: CAPE-KG",
            "evidence_files": [
                release / "method_module_coverage.md",
                release / "prompt_node_edge_traceability.md",
                release / "provenance_manifest.md",
            ],
            "claim_status": "claimable_method_artifacts",
            "paper_use_now": "yes",
            "blocking_gate_ids": [],
            "notes": "M1-M11 implementation artifacts are present; final performance claims remain separate.",
        },
        {
            "section_id": "S07",
            "planned_section": "Experiments: baselines and ablations",
            "draft_anchor": "### Baselines and Ablations",
            "evidence_files": [
                evaluation / "actual_llm_silver_evaluation_report.md",
                release / "qwen3_model_scaling_report.md",
                release / "paper_tables.md",
                release / "claim_gate_report.md",
            ],
            "claim_status": "diagnostic_only_until_human_gold",
            "paper_use_now": "diagnostic_only",
            "blocking_gate_ids": ["llm.proposed_human_gold_score"],
            "notes": "Generation coverage and silver/proxy diagnostics are ready; final main table requires human-gold scoring.",
        },
        {
            "section_id": "S08",
            "planned_section": "Experiments: evidence span granularity",
            "draft_anchor": "### Evidence Span Granularity",
            "evidence_files": [
                evaluation / "evidence_span_granularity_report.md",
                evaluation / "human_gold_span_iou_report.md",
                release / "paper_tables.md",
            ],
            "claim_status": "diagnostic_only_until_human_gold",
            "paper_use_now": "diagnostic_only",
            "blocking_gate_ids": ["gold.completed_chunks", "gold.item_count"],
            "notes": "Component-span diagnostics exist; exact final span quality needs adjudicated human spans.",
        },
        {
            "section_id": "S09",
            "planned_section": "Experiments: KG structural diagnostics",
            "draft_anchor": "### KG Structural Diagnostics",
            "evidence_files": [
                evaluation / "structural_evaluation_report.md",
                evaluation / "structural_gap_worklist_report.md",
                release / "paper_tables.md",
            ],
            "claim_status": "structural_diagnostic_ready",
            "paper_use_now": "yes_as_structural_diagnostic",
            "blocking_gate_ids": [],
            "notes": "Ontology, evidence, and procedural diagnostics are available; review-checkpoint gap is tracked separately.",
        },
        {
            "section_id": "S10",
            "planned_section": "Experiments: public benchmark adapters",
            "draft_anchor": "### Public Benchmark Adapters",
            "evidence_files": [
                public_bench / "public_benchmark_crosscheck_report.md",
                release / "public_reproducibility_manifest.md",
                release / "paper_tables.md",
            ],
            "claim_status": "auxiliary_claimable_not_main_private_result",
            "paper_use_now": "yes_as_auxiliary",
            "blocking_gate_ids": [],
            "notes": "Public adapter diagnostics support generality discussion, not the main Korean enterprise human-gold result.",
        },
        {
            "section_id": "S11",
            "planned_section": "Downstream NCS/PCF mapping and crosswalk",
            "draft_anchor": "### Layer2-Bridged NCS-PCF Crosswalk Candidates",
            "evidence_files": [
                evaluation / "mapping_downstream_report.md",
                release / "mapping_review_progress_report.md",
                evaluation / "ncs_pcf_crosswalk_report.md",
                release / "paper_tables.md",
            ],
            "claim_status": "pending_expert_review",
            "paper_use_now": "candidate_generation_only",
            "blocking_gate_ids": ["mapping.expert_review", "crosswalk.expert_review"],
            "notes": "Candidate generation is complete; Hit@K, MRR, nDCG, utility, and accept-rate claims require expert review.",
        },
        {
            "section_id": "S12",
            "planned_section": "Analysis",
            "draft_anchor": "## Analysis",
            "evidence_files": [
                reports / "error_analysis.md",
                evaluation / "evidence_span_granularity_report.md",
                evaluation / "structural_evaluation_report.md",
                release / "reviewer_risk_register.md",
            ],
            "claim_status": "diagnostic_only_until_human_gold",
            "paper_use_now": "diagnostic_only",
            "blocking_gate_ids": ["gold.completed_chunks", "gold.item_count"],
            "notes": "Silver/proxy error taxonomy is available; final error frequencies should be refreshed after human-gold scoring.",
        },
        {
            "section_id": "S13",
            "planned_section": "Release and reproducibility",
            "draft_anchor": "## Source Artifacts",
            "evidence_files": [
                release / "release_bundle_manifest.json",
                release / "release_bundle_safety_report.md",
                release / "provenance_manifest.md",
                release / "public_reproducibility_manifest.md",
                release / "data_release_ethics_statement.md",
            ],
            "claim_status": "claimable_setup",
            "paper_use_now": "yes",
            "blocking_gate_ids": [],
            "notes": "Internal and public-safe reproducibility bundles are tracked; public release remains filtered for source-text safety.",
        },
        {
            "section_id": "S14",
            "planned_section": "Conclusion",
            "draft_anchor": "## Conclusion",
            "evidence_files": [
                release / "submission_completion_audit_ko.md",
                release / "claim_gate_report.md",
                release / "claimable_main_table.md",
            ],
            "claim_status": "not_submission_ready",
            "paper_use_now": "claim_safe_summary_only",
            "blocking_gate_ids": ["gold.completed_chunks", "gold.item_count", "gold.iaa", "llm.proposed_human_gold_score"],
            "notes": "Conclusion must remain conservative until required human-return gates are satisfied.",
        },
        {
            "section_id": "S15",
            "planned_section": "Limitations",
            "draft_anchor": "## Limitations",
            "evidence_files": [
                release / "limitations.md",
                release / "reviewer_risk_register.md",
                release / "data_release_ethics_statement.md",
            ],
            "claim_status": "claimable_limitations",
            "paper_use_now": "yes",
            "blocking_gate_ids": [],
            "notes": "Known limitations and claim boundaries are already documented.",
        },
        {
            "section_id": "S16",
            "planned_section": "Ethical Considerations",
            "draft_anchor": "## Ethical Considerations",
            "evidence_files": [
                release / "data_release_ethics_statement.md",
                release / "external_resource_license_report.md",
                release / "public_reproducibility_manifest.md",
            ],
            "claim_status": "claimable_ethics",
            "paper_use_now": "yes",
            "blocking_gate_ids": [],
            "notes": "Copyright, release safety, and derived-artifact constraints are documented.",
        },
    ]


def build_payload(exp_dir, plan_file):
    exp_dir = Path(exp_dir)
    plan_file = Path(plan_file)
    release = exp_dir / "06_release"
    draft_path = exp_dir / "07_reports/eacl_paper_draft.md"
    status_path = release / "eacl_paper_draft_status.json"
    claim_path = release / "claim_gate_report.json"
    completion_path = release / "submission_completion_audit_ko.json"

    draft_text = draft_path.read_text(encoding="utf-8") if draft_path.exists() else ""
    status = read_json(status_path, {}) or {}
    claim_gate = read_json(claim_path, {}) or {}
    completion = read_json(completion_path, {}) or {}
    plan_text = plan_file.read_text(encoding="utf-8") if plan_file.exists() else ""

    sections = []
    missing_evidence = []
    missing_anchors = []
    for spec in section_specs(exp_dir):
        evidence = [file_state(path) for path in spec["evidence_files"]]
        missing = [row["path"] for row in evidence if not row["exists"] or row["bytes"] == 0]
        present_in_draft = spec["draft_anchor"] in draft_text
        if missing:
            missing_evidence.extend(missing)
        if not present_in_draft:
            missing_anchors.append(spec["draft_anchor"])
        sections.append(
            {
                "section_id": spec["section_id"],
                "planned_section": spec["planned_section"],
                "draft_anchor": spec["draft_anchor"],
                "present_in_draft": present_in_draft,
                "primary_evidence_files": evidence,
                "missing_evidence_files": missing,
                "claim_status": spec["claim_status"],
                "paper_use_now": spec["paper_use_now"],
                "blocking_gate_ids": spec["blocking_gate_ids"],
                "notes": spec["notes"],
            }
        )

    status_counts = {}
    for row in sections:
        status_counts[row["claim_status"]] = status_counts.get(row["claim_status"], 0) + 1

    blocking_gate_ids = sorted({gate for row in sections for gate in row["blocking_gate_ids"]})
    claim_gate_rows = claim_gate.get("gates") or []
    blocking_gate_status = [
        {
            "gate_id": row.get("gate_id"),
            "status": row.get("status"),
            "required": row.get("required"),
            "evidence": row.get("evidence"),
        }
        for row in claim_gate_rows
        if row.get("gate_id") in blocking_gate_ids
    ]

    overall_status = "PASS" if not missing_evidence and not missing_anchors else "FAIL"
    claim_status = READY_CLAIM_STATUS if overall_status == "PASS" else "paper_section_source_map_incomplete"
    summary = {
        "total_sections": len(sections),
        "present_sections": sum(1 for row in sections if row["present_in_draft"]),
        "missing_sections": len(missing_anchors),
        "evidence_file_references": sum(len(row["primary_evidence_files"]) for row in sections),
        "missing_evidence_files": len(missing_evidence),
        "claim_status_counts": status_counts,
        "human_or_expert_blocked_sections": sum(
            1
            for row in sections
            if row["claim_status"] in {"pending_human_gold", "pending_expert_review", "not_submission_ready"}
            or "until_human_gold" in row["claim_status"]
        ),
        "safe_to_use_as_submission": False,
        "submission_ready": False,
        "draft_claim_status": status.get("claim_status"),
        "draft_safe_to_use_as_submission": status.get("safe_to_use_as_submission"),
        "claim_gate_overall_status": claim_gate.get("overall_status"),
        "claim_gate_required_failure_count": claim_gate.get("required_failure_count"),
        "claim_gate_optional_failure_count": claim_gate.get("optional_failure_count"),
        "completion_status": completion.get("overall_completion_status"),
    }

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "plan_file": rel(plan_file),
        "experiment_dir": rel(exp_dir),
        "paper_draft": rel(draft_path),
        "plan_long_paper_section_present": "Long paper 구조" in plan_text,
        "overall_status": overall_status,
        "claim_status": claim_status,
        "safe_to_use_as_submission": False,
        "submission_ready": False,
        "summary": summary,
        "missing_draft_anchors": missing_anchors,
        "missing_evidence_files": missing_evidence,
        "blocking_gate_status": blocking_gate_status,
        "sections": sections,
        "interpretation": [
            "This source map verifies paper-section evidence coverage, not final submission readiness.",
            "Sections with silver/proxy diagnostics must not be rewritten as human-gold performance claims.",
            "Human-gold annotation, IAA, adjudication, proposed-method scoring, and expert review remain blocking gates.",
        ],
    }


def render_report(payload):
    summary = payload["summary"]
    lines = [
        "# CAPE-KG Paper Section Source Map",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Plan: `{payload['plan_file']}`",
        f"Draft: `{payload['paper_draft']}`",
        "",
        "이 문서는 EACL 논문 초안의 각 섹션이 어떤 현재 산출물로 뒷받침되는지 매핑한 release artifact입니다. 최종 제출 가능 선언이 아니라, 섹션별 근거와 claim boundary를 확인하기 위한 감사표입니다.",
        "",
        "## Summary",
        "",
        md_table(
            ["Item", "Value"],
            [
                {"Item": "Overall status", "Value": payload["overall_status"]},
                {"Item": "Claim status", "Value": payload["claim_status"]},
                {"Item": "Safe to use as submission", "Value": summary["safe_to_use_as_submission"]},
                {"Item": "Submission ready", "Value": summary["submission_ready"]},
                {"Item": "Total sections", "Value": summary["total_sections"]},
                {"Item": "Present sections", "Value": summary["present_sections"]},
                {"Item": "Missing section anchors", "Value": summary["missing_sections"]},
                {"Item": "Evidence file references", "Value": summary["evidence_file_references"]},
                {"Item": "Missing evidence files", "Value": summary["missing_evidence_files"]},
                {"Item": "Human/expert blocked sections", "Value": summary["human_or_expert_blocked_sections"]},
                {"Item": "Claim gate", "Value": summary["claim_gate_overall_status"]},
                {"Item": "Required claim-gate failures", "Value": summary["claim_gate_required_failure_count"]},
                {"Item": "Optional claim-gate failures", "Value": summary["claim_gate_optional_failure_count"]},
            ],
        ),
        "",
        "## Section Map",
        "",
        md_table(
            ["section_id", "planned_section", "draft_anchor", "present", "claim_status", "paper_use_now", "evidence_files", "blocking_gate_ids"],
            [
                {
                    "section_id": row["section_id"],
                    "planned_section": row["planned_section"],
                    "draft_anchor": row["draft_anchor"],
                    "present": row["present_in_draft"],
                    "claim_status": row["claim_status"],
                    "paper_use_now": row["paper_use_now"],
                    "evidence_files": [evidence["path"] for evidence in row["primary_evidence_files"]],
                    "blocking_gate_ids": row["blocking_gate_ids"],
                }
                for row in payload["sections"]
            ],
        ),
        "",
        "## Blocking Gate Alignment",
        "",
    ]
    if payload["blocking_gate_status"]:
        lines.append(md_table(["gate_id", "status", "required", "evidence"], payload["blocking_gate_status"]))
    else:
        lines.append("No blocking gates are attached to the section map.")
    lines += [
        "",
        "## Missing Evidence",
        "",
    ]
    if payload["missing_draft_anchors"] or payload["missing_evidence_files"]:
        for anchor in payload["missing_draft_anchors"]:
            lines.append(f"- Missing draft anchor: `{anchor}`")
        for path in payload["missing_evidence_files"]:
            lines.append(f"- Missing evidence file: `{path}`")
    else:
        lines.append("- No missing draft anchors or evidence files.")
    lines += [
        "",
        "## Use Guidance",
        "",
        "- `claimable_setup`, `claimable_method_artifacts`, and related setup statuses can support method, resource, and reproducibility descriptions.",
        "- `diagnostic_only_until_human_gold` must remain diagnostic until adjudicated labels are imported and scoring is refreshed.",
        "- `pending_expert_review` sections can describe candidate generation but must not report mapping utility metrics as final.",
        "- `safe_to_use_as_submission` is intentionally false because the paper still needs human-gold and expert-review returns.",
    ]
    return "\n".join(lines) + "\n"


def run(args):
    payload = build_payload(args.experiment_dir, args.plan_file)
    release = Path(args.experiment_dir) / "06_release"
    json_path = release / "paper_section_source_map.json"
    md_path = release / "paper_section_source_map.md"
    write_json(json_path, payload)
    write_text(md_path, render_report(payload))
    print(
        json.dumps(
            {
                "json": rel(json_path),
                "markdown": rel(md_path),
                "overall_status": payload["overall_status"],
                "claim_status": payload["claim_status"],
                "missing_evidence_files": len(payload["missing_evidence_files"]),
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
