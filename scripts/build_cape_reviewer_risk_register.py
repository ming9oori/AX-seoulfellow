#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a reviewer-facing risk register for the CAPE-KG EACL package."""

import argparse
import csv
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


def exists(path):
    path = Path(path)
    return path.exists()


def file_evidence(path, role, required=True):
    path = Path(path)
    present = path.exists() and path.is_file()
    return {
        "path": rel(path),
        "role": role,
        "required": bool(required),
        "exists": present,
        "bytes": path.stat().st_size if present else 0,
    }


def gate_by_id(claim_gate):
    return {row.get("gate_id"): row for row in (claim_gate or {}).get("gates", [])}


def readiness_by_id(readiness):
    return {row.get("id"): row for row in (readiness or {}).get("items", [])}


def first_row(rows, key, value):
    for row in rows or []:
        if row.get(key) == value:
            return row
    return {}


def metric_value(rows, result_name, field="Current value"):
    row = first_row(rows, "Result", result_name)
    return row.get(field, "")


def count_present(files):
    return sum(1 for item in files if item.get("exists"))


def build_register(exp_dir, outputs_dir):
    exp_dir = Path(exp_dir)
    outputs_dir = Path(outputs_dir)
    release_dir = exp_dir / "06_release"
    eval_dir = exp_dir / "04_evaluation"

    claim_gate = read_json(release_dir / "claim_gate_report.json", {}) or {}
    readiness = read_json(release_dir / "submission_readiness_audit.json", {}) or {}
    compliance = read_json(release_dir / "eacl_plan_compliance_matrix.json", {}) or {}
    rq_matrix = read_json(release_dir / "rq_evidence_matrix.json", {}) or {}
    claimable = read_json(release_dir / "claimable_main_table.json", {}) or {}
    license_report = read_json(release_dir / "external_resource_license_report.json", {}) or {}
    release_manifest = read_json(release_dir / "release_bundle_manifest.json", {}) or {}
    public_repro = read_json(release_dir / "public_reproducibility_manifest.json", {}) or {}
    method_coverage = read_json(release_dir / "method_module_coverage.json", {}) or {}
    public_cross = read_json(exp_dir / "08_public_benchmarks/public_benchmark_crosscheck_summary.json", {}) or {}
    human_gold = read_json(eval_dir / "human_gold_validation_summary.json", {}) or {}
    mapping_progress = read_json(release_dir / "mapping_review_progress_summary.json", {}) or {}
    crosswalk_expert = read_json(eval_dir / "crosswalk_expert_metrics.json", {}) or {}
    crosswalk_metrics = crosswalk_expert.get("metrics") or {}
    active_effort = read_json(eval_dir / "active_review_human_effort_metrics.json", {}) or {}
    active_briefing = read_json(release_dir / "active_review_human_effort_briefing.json", {}) or {}
    structural_gap = read_json(eval_dir / "structural_gap_worklist_summary.json", {}) or {}
    strict_json = read_json(release_dir / "strict_json_diagnostics.json", {}) or {}
    prehuman = read_json(release_dir / "pre_human_handoff_validation.json", {}) or {}

    gates = gate_by_id(claim_gate)
    readiness_items = readiness_by_id(readiness)
    claimable_rows = claimable.get("rows") or []
    compliance_summary = compliance.get("summary") or {}
    rq_summary = rq_matrix.get("summary") or {}
    method_summary = method_coverage.get("summary") or {}
    public_summary = public_cross.get("summary") or {}
    release_summary = release_manifest.get("summary") or release_manifest

    common_gold_action = "; ".join(
        item
        for item in [
            readiness_items.get("min.gold_chunks", {}).get("next_step"),
            readiness_items.get("min.gold_items", {}).get("next_step"),
            readiness_items.get("min.iaa", {}).get("next_step"),
            readiness_items.get("min.proposed", {}).get("next_step"),
        ]
        if item
    )

    rows = [
        {
            "risk_id": "R01_task_framing",
            "reviewer_concern": "The work may look like a Korean domain KG construction case rather than a generalizable NLP task.",
            "severity": "high",
            "current_status": "mitigated_as_pre_human_setup",
            "claim_safety": "claimable_setup_not_final_performance",
            "current_evidence": "CAPE-KG is framed as evidence-grounded procedural KG extraction with RQ1-RQ4 and M1-M11 artifacts.",
            "remaining_action": "Use this framing consistently in the paper; final empirical claims still require human-gold scoring.",
            "evidence_files": [
                file_evidence(release_dir / "rq_evidence_matrix.md", "RQ-to-evidence mapping"),
                file_evidence(release_dir / "method_module_coverage.md", "M1-M11 method coverage"),
                file_evidence(exp_dir / "07_reports/eacl_paper_draft.md", "paper draft with conservative claim scope"),
            ],
        },
        {
            "risk_id": "R02_human_gold_missing",
            "reviewer_concern": "Main extraction quality cannot be trusted without adjudicated human-gold labels and IAA.",
            "severity": "critical",
            "current_status": "open_human_required",
            "claim_safety": "not_claimable",
            "current_evidence": (
                f"{human_gold.get('completed_adjudicated_chunks', 0)}/100 adjudicated chunks, "
                f"{human_gold.get('gold_item_count_for_readiness', 0)}/500 gold items, "
                f"required claim-gate failures={claim_gate.get('required_failure_count', 'unknown')}."
            ),
            "remaining_action": common_gold_action or "Complete human annotation, adjudication, IAA, and proposed-method human-gold scoring.",
            "evidence_files": [
                file_evidence(eval_dir / "human_gold_validation_summary.json", "human-gold completion state"),
                file_evidence(eval_dir / "human_gold_metrics.json", "human-gold metric placeholder"),
                file_evidence(release_dir / "human_gate_action_plan.md", "human gate action plan"),
            ],
        },
        {
            "risk_id": "R03_silver_proxy_overclaim",
            "reviewer_concern": "Silver/proxy diagnostics may be mistaken for final paper performance.",
            "severity": "high",
            "current_status": "mitigated_with_claim_gate",
            "claim_safety": "diagnostic_only_until_gold",
            "current_evidence": (
                f"Claimable table status={claimable.get('overall_claim_status')}; "
                f"pre-human validation={prehuman.get('overall_status')}; "
                "see pre_human_handoff_validation.md for the current check count."
            ),
            "remaining_action": "Keep all silver/proxy tables labeled as diagnostics until adjudicated human-gold metrics are recomputed.",
            "evidence_files": [
                file_evidence(release_dir / "claimable_main_table.md", "claimable vs diagnostic result table"),
                file_evidence(release_dir / "pre_human_handoff_validation.md", "pre-human validation"),
                file_evidence(exp_dir / "07_reports/error_analysis.md", "pre-human error analysis with claim scope"),
            ],
        },
        {
            "risk_id": "R04_method_novelty",
            "reviewer_concern": "The method may appear too close to existing ontology-guided or LLM-KG extraction pipelines.",
            "severity": "high",
            "current_status": "partially_mitigated",
            "claim_safety": "method_artifacts_claimable_final_gain_pending",
            "current_evidence": (
                f"M1-M11 coverage missing artifacts={method_summary.get('missing_required_artifact_count')}; "
                "B3/B4/B6-family baselines, six ablations, and novelty-positioning evidence are present."
            ),
            "remaining_action": "After human-gold scoring, report whether CQ retrieval, evidence grounding, validators, and standard bridge improve metrics.",
            "evidence_files": [
                file_evidence(release_dir / "method_module_coverage.json", "method module artifact coverage"),
                file_evidence(release_dir / "method_novelty_positioning.md", "method novelty positioning matrix"),
                file_evidence(exp_dir / "04_evaluation/actual_llm_silver_metrics.json", "actual LLM silver diagnostics"),
                file_evidence(exp_dir / "50_sac_kg_verifier_pruner_baseline_quality_report.md", "SAC-KG-style baseline diagnostics"),
            ],
        },
        {
            "risk_id": "R05_public_reproducibility",
            "reviewer_concern": "The private Korean source corpus may not be redistributable, weakening reproducibility.",
            "severity": "high",
            "current_status": "mitigated_with_public_safe_release_plan",
            "claim_safety": "claimable_setup_rights_review_still_required",
            "current_evidence": (
                f"External resources={license_report.get('resource_count')}; "
                f"public benchmarks={license_report.get('public_benchmark_count')}; "
                f"rights-review-required resources={license_report.get('rights_review_required_count')}; "
                f"public-safe reproducibility rows={(public_repro.get('summary') or {}).get('public_safe_rows')}."
            ),
            "remaining_action": "Do not release raw OCR/source-derived text unless rights are cleared; use public-safe skeleton, synthetic examples, prompts, schemas, and public benchmark adapters.",
            "evidence_files": [
                file_evidence(release_dir / "data_release_ethics_statement.md", "data release and ethics statement"),
                file_evidence(release_dir / "external_resource_license_report.md", "external resource/license report"),
                file_evidence(release_dir / "public_reproducibility_manifest.md", "public-safe reproducibility manifest"),
                file_evidence(release_dir / "public_reproducibility_manifest.json", "public-safe reproducibility manifest JSON"),
                file_evidence(release_dir / "public_synthetic_examples/README.md", "public-safe synthetic examples"),
            ],
        },
        {
            "risk_id": "R06_public_benchmark_generalization",
            "reviewer_concern": "External generalization evidence may be too thin if only internal Korean documents are evaluated.",
            "severity": "medium",
            "current_status": "mitigated_as_auxiliary_evidence",
            "claim_safety": "auxiliary_claimable_not_main_result",
            "current_evidence": (
                f"PAGED items={public_summary.get('max_single_run_paged_items')}; "
                f"Text2KG items={public_summary.get('max_single_run_text2kg_items')}; "
                f"strong_cross_run={public_summary.get('strong_cross_run_present')}."
            ),
            "remaining_action": "Present public benchmark results as auxiliary robustness evidence, not as a substitute for target-corpus human-gold results.",
            "evidence_files": [
                file_evidence(exp_dir / "08_public_benchmarks/public_benchmark_crosscheck_summary.json", "public benchmark cross-check summary"),
                file_evidence(exp_dir / "08_public_benchmarks/public_benchmark_crosscheck_report.md", "public benchmark report"),
                file_evidence(exp_dir / "08_public_benchmarks/public_benchmark_manifest.json", "public benchmark manifest"),
            ],
        },
        {
            "risk_id": "R07_mapping_downstream_labels",
            "reviewer_concern": "NCS/PCF downstream mapping utility is not claimable without expert-reviewed relevance labels.",
            "severity": "high",
            "current_status": "open_expert_required",
            "claim_safety": "not_claimable_until_expert_review",
            "current_evidence": (
                f"complete source groups={mapping_progress.get('complete_source_groups', 0)}, "
                f"pending rows={mapping_progress.get('pending_rows', 0)}, "
                f"pending groups={mapping_progress.get('pending_source_groups', 0)}."
            ),
            "remaining_action": "Complete Top-5 mapping expert review and recompute P@K, MRR, nDCG@10, accept rate, and explanation quality.",
            "evidence_files": [
                file_evidence(release_dir / "mapping_review_progress_report.md", "mapping review progress report"),
                file_evidence(exp_dir / "04_evaluation/mapping_expert_metrics.json", "mapping expert metric placeholder"),
                file_evidence(exp_dir / "05_review/mapping_review_next_20_groups.csv", "priority mapping groups"),
            ],
        },
        {
            "risk_id": "R08_crosswalk_downstream_utility",
            "reviewer_concern": "Layer2-bridged NCS-PCF crosswalk utility is not claimable without expert-reviewed pair labels.",
            "severity": "medium",
            "current_status": "open_expert_required",
            "claim_safety": "not_claimable_until_crosswalk_expert_review",
            "current_evidence": (
                f"candidate rows={crosswalk_metrics.get('candidate_rows', 0)}, "
                f"source tasks={crosswalk_metrics.get('source_task_count', 0)}, "
                f"completed rows={crosswalk_metrics.get('completed_rows', 0)}, "
                f"pending rows={crosswalk_metrics.get('pending_rows', 0)}."
            ),
            "remaining_action": "Complete NCS-PCF crosswalk expert review and recompute accept rate, Hit@K, P@10, MRR, nDCG@10, utility, and explanation quality.",
            "evidence_files": [
                file_evidence(exp_dir / "04_evaluation/crosswalk_expert_metrics.json", "crosswalk expert metric placeholder"),
                file_evidence(exp_dir / "01_data/crosswalk_review/crosswalk_review_manifest.json", "crosswalk review manifest"),
                file_evidence(exp_dir / "01_data/crosswalk_review/crosswalk_review_sheet.csv", "crosswalk review sheet"),
            ],
        },
        {
            "risk_id": "R09_active_review_effort",
            "reviewer_concern": "Active-review efficiency claims need human timing and correction outcomes.",
            "severity": "medium",
            "current_status": "open_human_required",
            "claim_safety": "not_claimable_until_effort_return",
            "current_evidence": (
                f"human effort status={active_effort.get('claim_status')}; "
                f"reviewed file present={active_effort.get('reviewed_file_present')}; "
                f"pooled rows={active_effort.get('pooled_rows')}; "
                f"briefing rows={active_briefing.get('briefing_rows')}; "
                f"briefing status={active_briefing.get('claim_status')}."
            ),
            "remaining_action": "Collect active_review_human_effort.reviewed.csv and refresh efficiency metrics against adjudicated outcomes.",
            "evidence_files": [
                file_evidence(eval_dir / "active_review_human_effort_report.md", "active-review human effort report"),
                file_evidence(release_dir / "active_review_human_effort_briefing.md", "active-review effort briefing"),
                file_evidence(exp_dir / "05_review/active_review_human_effort_briefing.csv", "active-review effort briefing CSV"),
                file_evidence(release_dir / "active_review_human_effort_briefing.json", "active-review effort briefing summary"),
                file_evidence(exp_dir / "05_review/active_review_human_effort_template.csv", "human effort template"),
                file_evidence(release_dir / "active_review_human_effort_plan.md", "human effort protocol"),
            ],
        },
        {
            "risk_id": "R10_structural_validity",
            "reviewer_concern": "Procedural KG claims require evidence that schema, gateway, and artifact-flow constraints are valid.",
            "severity": "medium",
            "current_status": "mitigated_with_structural_diagnostics",
            "claim_safety": "diagnostic_only_until_human_gold",
            "current_evidence": (
                f"review checkpoint candidates={structural_gap.get('review_checkpoint_candidate_count')}; "
                f"gateway branch gaps={structural_gap.get('gateway_branch_gap_count')}; "
                f"RDF/SHACL export exists={exists(outputs_dir / '12_rdf/cape_kg_layer2.ttl')}."
            ),
            "remaining_action": "Use structural review returns only after human confirmation; recompute structural metrics after final KG changes.",
            "evidence_files": [
                file_evidence(eval_dir / "structural_evaluation_report.md", "structural evaluation report"),
                file_evidence(eval_dir / "structural_gap_worklist_report.md", "structural gap worklist"),
                file_evidence(outputs_dir / "12_rdf/cape_kg_shacl_validation_report.md", "RDF/SHACL validation report"),
            ],
        },
        {
            "risk_id": "R11_llm_reproducibility",
            "reviewer_concern": "LLM outputs may be brittle because of JSON parsing, prompt drift, or model-run provenance gaps.",
            "severity": "medium",
            "current_status": "mitigated_with_strict_json_and_provenance",
            "claim_safety": "claimable_setup_not_quality_result",
            "current_evidence": (
                f"strict JSON gate={gates.get('llm.strict_json_rate', {}).get('status')}; "
                f"revalidated recovery gate={gates.get('llm.revalidated_output_recovery', {}).get('status')}; "
                f"warning conditions={strict_json.get('warning_condition_count', 0)}."
            ),
            "remaining_action": "Keep prompts, model identifiers, raw/valid outputs, and provenance hashes synchronized after any new LLM run.",
            "evidence_files": [
                file_evidence(release_dir / "strict_json_diagnostics.md", "strict JSON diagnostics"),
                file_evidence(release_dir / "provenance_manifest.md", "provenance manifest"),
                file_evidence(eval_dir / "provenance_llm_run_index.csv", "LLM run index"),
            ],
        },
        {
            "risk_id": "R12_release_bundle_safety",
            "reviewer_concern": "Release bundles may accidentally include source text, stale nested bundles, or unsafe review files.",
            "severity": "medium",
            "current_status": "mitigated_with_bundle_scan",
            "claim_safety": "claimable_setup",
            "current_evidence": (
                f"release file count={release_summary.get('internal_file_count', 'unknown')}; "
                f"public-safe file count={release_summary.get('public_safe_file_count', 'unknown')}; "
                f"public-safe risk issues={release_summary.get('public_safe_risk_issue_count', 0)}."
            ),
            "remaining_action": "Regenerate release bundle and checksums after any source artifact change.",
            "evidence_files": [
                file_evidence(release_dir / "release_bundle_manifest.json", "release bundle manifest"),
                file_evidence(release_dir / "release_bundle_safety_report.md", "release bundle safety report"),
                file_evidence(release_dir / "release_bundle_checksums.sha256", "release checksum file"),
                file_evidence(release_dir / "public_reproducibility_manifest.md", "public reproducibility manifest included in public-safe skeleton"),
            ],
        },
        {
            "risk_id": "R13_submission_status_overclaim",
            "reviewer_concern": "The project may be presented as EACL-ready even though required human gates are still open.",
            "severity": "critical",
            "current_status": "open_human_required",
            "claim_safety": "not_submission_ready",
            "current_evidence": (
                f"claim gate={claim_gate.get('overall_status')}; "
                f"minimum blockers={compliance_summary.get('minimum_human_blocker_count')}; "
                f"strong/optional blockers={compliance_summary.get('strong_or_optional_human_blocker_count')}; "
                f"RQ final claim ready count={rq_summary.get('claim_ready_count')}."
            ),
            "remaining_action": "Do not mark the submission complete until all minimum human-gold gates and proposed-method human-gold scoring pass.",
            "evidence_files": [
                file_evidence(release_dir / "submission_completion_audit_ko.md", "completion audit"),
                file_evidence(release_dir / "eacl_plan_compliance_matrix.md", "plan compliance matrix"),
                file_evidence(release_dir / "claim_gate_report.md", "claim gate report"),
            ],
        },
    ]

    for row in rows:
        files = row.get("evidence_files") or []
        row["evidence_file_count"] = len(files)
        row["present_evidence_file_count"] = count_present(files)
        row["missing_required_evidence_files"] = [
            item["path"] for item in files if item.get("required") and not item.get("exists")
        ]
        row["paper_claim_allowed_now"] = row["claim_safety"] in {
            "claimable_setup",
            "claimable_setup_not_quality_result",
            "claimable_setup_rights_review_still_required",
            "auxiliary_claimable_not_main_result",
        }

    issue_rows = [
        row
        for row in rows
        if row["missing_required_evidence_files"]
        or (row["severity"] == "critical" and not row["current_status"].startswith("open_"))
    ]
    open_rows = [row for row in rows if row["current_status"].startswith("open_")]
    mitigated_rows = [row for row in rows if row["current_status"].startswith("mitigated")]
    partial_rows = [row for row in rows if row["current_status"].startswith("partially")]

    summary = {
        "risk_count": len(rows),
        "critical_count": sum(1 for row in rows if row["severity"] == "critical"),
        "high_count": sum(1 for row in rows if row["severity"] == "high"),
        "medium_count": sum(1 for row in rows if row["severity"] == "medium"),
        "open_count": len(open_rows),
        "mitigated_count": len(mitigated_rows),
        "partial_count": len(partial_rows),
        "missing_required_evidence_file_count": sum(len(row["missing_required_evidence_files"]) for row in rows),
        "paper_claim_allowed_now_count": sum(1 for row in rows if row["paper_claim_allowed_now"]),
        "claim_status": (
            "reviewer_risk_register_ready_with_open_human_gates"
            if open_rows and not issue_rows
            else "reviewer_risk_register_has_evidence_issues"
        ),
        "open_risk_ids": [row["risk_id"] for row in open_rows],
    }

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": rel(exp_dir),
        "outputs_dir": rel(outputs_dir),
        "summary": summary,
        "source_status": {
            "claim_gate_overall_status": claim_gate.get("overall_status"),
            "claim_gate_required_failures": claim_gate.get("required_failure_count"),
            "claim_gate_optional_failures": claim_gate.get("optional_failure_count"),
            "readiness_claim_status": readiness.get("claim_status"),
            "compliance_completion_status": compliance_summary.get("completion_status"),
            "pre_human_validation_source_json": rel(release_dir / "pre_human_handoff_validation.json"),
            "pre_human_validation_source_md": rel(release_dir / "pre_human_handoff_validation.md"),
        },
        "risks": rows,
    }


def csv_rows(payload):
    rows = []
    for row in payload["risks"]:
        rows.append(
            {
                "risk_id": row["risk_id"],
                "severity": row["severity"],
                "current_status": row["current_status"],
                "claim_safety": row["claim_safety"],
                "paper_claim_allowed_now": row["paper_claim_allowed_now"],
                "reviewer_concern": row["reviewer_concern"],
                "current_evidence": row["current_evidence"],
                "remaining_action": row["remaining_action"],
                "present_evidence_file_count": row["present_evidence_file_count"],
                "missing_required_evidence_files": "; ".join(row["missing_required_evidence_files"]),
            }
        )
    return rows


def render_markdown(payload):
    summary = payload["summary"]
    lines = [
        "# CAPE-KG Reviewer Risk Register",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Experiment: `{payload['experiment_dir']}`",
        "",
        "이 문서는 EACL/ARR 리뷰어가 제기할 가능성이 큰 우려를 현재 산출물, claim 가능 범위, 남은 human/expert gate와 연결한 제출 준비용 risk register입니다.",
        "최종 성능 claim은 human-gold annotation, IAA, adjudication, expert review가 끝난 뒤에만 가능합니다.",
        "",
        "## Summary",
        "",
        f"- Claim status: `{summary['claim_status']}`",
        f"- Risks: {summary['risk_count']} total; critical={summary['critical_count']}, high={summary['high_count']}, medium={summary['medium_count']}",
        f"- Open risks: {summary['open_count']} ({', '.join(summary['open_risk_ids'])})",
        f"- Mitigated/partial risks: {summary['mitigated_count']} mitigated, {summary['partial_count']} partial",
        f"- Missing required evidence files: {summary['missing_required_evidence_file_count']}",
        f"- Paper-claim-allowed setup/auxiliary items now: {summary['paper_claim_allowed_now_count']}",
        "",
        "## Source Status",
        "",
        "| item | value |",
        "| --- | --- |",
    ]
    for key, value in payload["source_status"].items():
        lines.append(f"| {key} | `{value}` |")

    lines += [
        "",
        "## Risk Table",
        "",
        "| id | severity | status | claim safety | reviewer concern | current evidence | remaining action |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["risks"]:
        concern = row["reviewer_concern"].replace("|", "\\|")
        evidence = row["current_evidence"].replace("|", "\\|")
        action = row["remaining_action"].replace("|", "\\|")
        lines.append(
            f"| {row['risk_id']} | {row['severity']} | `{row['current_status']}` | `{row['claim_safety']}` | "
            f"{concern} | {evidence} | {action} |"
        )

    lines += ["", "## Evidence Files", ""]
    for row in payload["risks"]:
        lines += [
            f"### {row['risk_id']}. {row['reviewer_concern']}",
            "",
            f"- Status: `{row['current_status']}`",
            f"- Claim safety: `{row['claim_safety']}`",
            f"- Evidence coverage: {row['present_evidence_file_count']}/{row['evidence_file_count']}",
        ]
        if row["missing_required_evidence_files"]:
            lines.append(f"- Missing required evidence: `{'; '.join(row['missing_required_evidence_files'])}`")
        lines += ["", "| role | path | exists | bytes |", "| --- | --- | ---: | ---: |"]
        for item in row["evidence_files"]:
            lines.append(f"| {item['role']} | `{item['path']}` | {item['exists']} | {item['bytes']} |")
        lines.append("")

    lines += [
        "## Interpretation",
        "",
        "- `open_human_required` and `open_expert_required` are expected blockers, not script failures.",
        "- `diagnostic_only_until_gold` means the value can guide debugging or slides, but not final performance claims.",
        "- `claimable_setup` means the artifact supports reproducibility or experimental setup, not method quality.",
    ]
    return "\n".join(lines) + "\n"


def run(args):
    exp_dir = Path(args.experiment_dir)
    outputs_dir = Path(args.outputs_dir)
    release_dir = exp_dir / "06_release"
    payload = build_register(exp_dir, outputs_dir)

    json_path = release_dir / "reviewer_risk_register.json"
    csv_path = release_dir / "reviewer_risk_register.csv"
    md_path = release_dir / "reviewer_risk_register.md"
    write_json(json_path, payload)
    write_csv(
        csv_path,
        csv_rows(payload),
        [
            "risk_id",
            "severity",
            "current_status",
            "claim_safety",
            "paper_claim_allowed_now",
            "reviewer_concern",
            "current_evidence",
            "remaining_action",
            "present_evidence_file_count",
            "missing_required_evidence_files",
        ],
    )
    write_text(md_path, render_markdown(payload))
    print(
        json.dumps(
            {
                "claim_status": payload["summary"]["claim_status"],
                "risk_count": payload["summary"]["risk_count"],
                "open_count": payload["summary"]["open_count"],
                "missing_required_evidence_file_count": payload["summary"]["missing_required_evidence_file_count"],
                "json": rel(json_path),
                "csv": rel(csv_path),
                "markdown": rel(md_path),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--outputs-dir", default=str(DEFAULT_OUTPUTS_DIR))
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
