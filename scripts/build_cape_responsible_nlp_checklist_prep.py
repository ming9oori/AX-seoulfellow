#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a Responsible NLP checklist preparation artifact for CAPE-KG."""

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_PLAN_FILE = Path("AX_EACL_submission_review_revised_plan.md")
READY_STATUS = "responsible_nlp_checklist_prep_ready_not_final_answers"


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
    return Path(path).as_posix()


def file_state(path):
    path = Path(path)
    exists = path.exists() and path.is_file()
    return {"path": rel(path), "exists": exists, "bytes": path.stat().st_size if exists else 0}


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


def checklist_item(
    item_id,
    checklist_area,
    draft_answer,
    evidence_files,
    paper_section,
    status,
    remaining_action,
    claim_boundary,
):
    evidence = [file_state(path) for path in evidence_files]
    missing = [row["path"] for row in evidence if not row["exists"] or row["bytes"] == 0]
    return {
        "item_id": item_id,
        "checklist_area": checklist_area,
        "draft_answer": draft_answer,
        "evidence_files": evidence,
        "missing_evidence_files": missing,
        "paper_section": paper_section,
        "status": status if not missing else "missing_evidence",
        "remaining_action": remaining_action,
        "claim_boundary": claim_boundary,
    }


def build_items(exp_dir, plan_file):
    exp_dir = Path(exp_dir)
    release = exp_dir / "06_release"
    reports = exp_dir / "07_reports"
    return [
        checklist_item(
            "RNLP01_limitations_and_claim_scope",
            "Limitations and claim scope",
            "The study separates KG construction, setup diagnostics, silver/proxy diagnostics, and final human-gold claims. Final extraction and mapping performance claims are withheld until human-gold annotation, IAA, adjudication, and expert review are complete.",
            [
                plan_file,
                release / "claim_language_guardrails.md",
                release / "claimable_main_table.md",
                release / "claim_gate_report.md",
                reports / "eacl_paper_draft.md",
            ],
            "Limitations; Results; Ethics",
            "draft_ready",
            "Keep all final performance language synchronized after human/expert returns.",
            "Do not present silver/proxy metrics as final main-result evidence.",
        ),
        checklist_item(
            "RNLP02_data_rights_and_release_boundaries",
            "Data rights and release boundaries",
            "The target corpus is treated as restricted source-derived enterprise procedural text. Public release is split from internal reproducibility: the public-safe skeleton contains schema, prompts, scripts, synthetic examples, aggregate diagnostics, provenance, and validation reports, while raw or source-derived text remains withheld unless rights are cleared.",
            [
                release / "data_release_ethics_statement.md",
                release / "public_reproducibility_manifest.md",
                release / "external_resource_license_report.md",
                release / "release_bundle_safety_report.md",
            ],
            "Data; Ethics; Reproducibility",
            "draft_ready",
            "Authors must complete final rights review before any external supplement upload.",
            "Public-safe artifacts mitigate reproducibility limits but do not authorize raw source-text redistribution.",
        ),
        checklist_item(
            "RNLP03_private_or_sensitive_data",
            "Private or sensitive data",
            "The workflow assumes that the domain corpus may contain organization-specific or sensitive business-procedure details. Public artifacts should exclude raw OCR text, private review workbooks, reviewer identifiers, and source-derived examples unless explicitly rights-cleared and anonymized.",
            [
                release / "data_release_ethics_statement.md",
                release / "anonymized_submission_prep.md",
                release / "anonymized_submission_risk_scan.csv",
                release / "public_external_release_excluded_review_queue.md",
            ],
            "Ethics; Data",
            "draft_ready",
            "Inspect the final anonymized paper and supplement immediately before ARR upload.",
            "Internal preparation artifacts may mention private paths; upload artifacts must not.",
        ),
        checklist_item(
            "RNLP04_human_annotation_and_reviewer_privacy",
            "Human annotation and reviewer privacy",
            "Human review packages are prepared for annotators, adjudication, mapping experts, crosswalk experts, and active-review effort tracking. Reviewer identities and timing/correction logs should stay private or aggregated, and IAA should be reported as reliability evidence, not personal evaluation.",
            [
                release / "human_review_launch_checklist_ko.md",
                release / "human_review_master_checklist_ko.md",
                release / "human_review_status_dashboard_ko.md",
                release / "data_release_ethics_statement.md",
            ],
            "Ethics; Evaluation",
            "pending_human_gold",
            "Complete annotation returns, adjudication, and aggregate-only reporting before final claims.",
            "Do not publish reviewer-level private work files or raw timing logs.",
        ),
        checklist_item(
            "RNLP05_llm_use_and_hallucination_risk",
            "LLM use and hallucination risk",
            "LLMs are used for baseline, proposed-condition, ablation, and model-scaling prediction generation. The paper should disclose that LLM outputs may hallucinate unsupported nodes, edges, mappings, or evidence; schema constraints, evidence anchors, strict JSON validation, and claim gates reduce but do not eliminate this risk.",
            [
                release / "prompt_node_edge_traceability.md",
                release / "strict_json_diagnostics.md",
                release / "qwen3_model_scaling_report.md",
                release / "reviewer_risk_register.md",
            ],
            "Methods; Ethics; Limitations",
            "draft_ready",
            "Refresh risk language if the final model set or decoding configuration changes.",
            "Generation coverage and silver diagnostics are not human-gold performance evidence.",
        ),
        checklist_item(
            "RNLP06_reproducibility_without_raw_private_corpus",
            "Reproducibility when raw corpus cannot be released",
            "The release provides schema, prompts, evaluation scripts, RDF/SHACL shapes, provenance records, checksums, public benchmark adapters, and synthetic examples so that the method and metrics remain inspectable even if the private domain corpus cannot be redistributed.",
            [
                release / "public_reproducibility_manifest.md",
                release / "public_synthetic_examples/README.md",
                release / "provenance_manifest.md",
                release / "evaluation_protocol_lock.md",
            ],
            "Reproducibility; Ethics",
            "draft_ready",
            "Keep the public-safe bundle and checksums synchronized after every final-result refresh.",
            "Synthetic examples demonstrate format and tooling; they do not replace target-corpus human-gold evaluation.",
        ),
        checklist_item(
            "RNLP07_public_benchmark_license_and_citation",
            "Public benchmark license and citation",
            "Public benchmark adapters are included as auxiliary checks and should follow original benchmark licenses and citation requirements. Their results support external sanity checking, not the main Korean enterprise-corpus performance claim.",
            [
                release / "external_resource_license_report.md",
                release / "external_resource_license_report.csv",
                release / "public_reproducibility_manifest.md",
                exp_dir / "08_public_benchmarks/public_benchmark_crosscheck_report.md",
            ],
            "Related Work; Experiments; Reproducibility",
            "pending_rights_review",
            "Verify citation and redistribution terms for all external resources before submission.",
            "Auxiliary public-benchmark results must not be framed as target-domain final evidence.",
        ),
        checklist_item(
            "RNLP08_anonymization_and_supplement_safety",
            "Anonymization and supplement safety",
            "The current internal package is not upload-ready. An anonymization prep scan exists, but the final ARR upload requires an ACL-formatted anonymous PDF and a supplement rebuilt from the public-safe skeleton with local usernames, absolute paths, source-derived workbooks, and private review files removed.",
            [
                release / "anonymized_submission_prep.md",
                release / "arr_submission_policy_checklist.md",
                release / "latest_release_bundle_index.md",
                release / "release_bundle_checksums.sha256",
            ],
            "Submission checklist; Supplement",
            "pending_author_confirmation",
            "Prepare final anonymous PDF and upload-safe supplement after human-gold refresh.",
            "Do not upload internal reproducibility bundles or source-derived review handoff materials.",
        ),
        checklist_item(
            "RNLP09_dual_use_or_misuse",
            "Dual-use or misuse",
            "The method structures enterprise procedural knowledge and could reveal operational workflows if raw private text were released. The current mitigation is to keep raw/source-derived materials restricted, publish only public-safe scaffolding, and report aggregated results.",
            [
                release / "data_release_ethics_statement.md",
                release / "reviewer_risk_register.md",
                release / "public_reproducibility_manifest.md",
            ],
            "Ethics; Limitations",
            "draft_ready",
            "Recheck dual-use wording after final release contents are selected.",
            "Utility claims should be scoped to KG construction and evaluation, not operational deployment readiness.",
        ),
        checklist_item(
            "RNLP10_final_author_confirmation",
            "Final author confirmation",
            "Several Responsible NLP checklist answers require author confirmation rather than repository evidence: no dual submission, final anonymization, rights clearance, final page-limit check, and whether any acknowledgments or identifying metadata remain.",
            [
                release / "arr_submission_policy_checklist.md",
                release / "submission_timeline_action_board.md",
                release / "submission_completion_audit_ko.md",
            ],
            "Submission checklist",
            "pending_author_confirmation",
            "Authors must complete final policy, rights, and anonymization confirmations immediately before upload.",
            "This prep artifact is not an official completed checklist and must not be marked submission-ready.",
        ),
    ]


def build_payload(exp_dir, plan_file):
    exp_dir = Path(exp_dir)
    release = exp_dir / "06_release"
    plan_file = Path(plan_file)
    arr = read_json(release / "arr_submission_policy_checklist.json", {}) or {}
    claim_gate = read_json(release / "claim_gate_report.json", {}) or {}
    public_manifest = read_json(release / "public_reproducibility_manifest.json", {}) or {}
    anonymized = read_json(release / "anonymized_submission_prep.json", {}) or {}
    items = build_items(exp_dir, plan_file)
    missing_evidence = sorted({path for item in items for path in item["missing_evidence_files"]})
    status_counts = Counter(item["status"] for item in items)
    pending_author = sum(1 for item in items if item["status"] == "pending_author_confirmation")
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "plan_file": rel(plan_file),
        "experiment_dir": rel(exp_dir),
        "overall_status": "PASS" if not missing_evidence else "FAIL",
        "claim_status": READY_STATUS if not missing_evidence else "responsible_nlp_checklist_prep_incomplete",
        "safe_to_use_as_submission": False,
        "submission_ready": False,
        "final_answers_ready": False,
        "summary": {
            "item_count": len(items),
            "draft_answer_count": sum(1 for item in items if item["draft_answer"]),
            "pending_author_confirmation_count": pending_author,
            "missing_evidence_files": len(missing_evidence),
            "status_counts": dict(sorted(status_counts.items())),
            "arr_policy_claim_status": arr.get("claim_status"),
            "arr_responsible_nlp_status": next(
                (
                    item.get("status")
                    for item in arr.get("items", [])
                    if item.get("item_id") == "ARR08_responsible_nlp_checklist"
                ),
                None,
            ),
            "claim_gate_overall_status": claim_gate.get("overall_status"),
            "public_reproducibility_claim_status": public_manifest.get("claim_status"),
            "anonymized_submission_prep_claim_status": anonymized.get("claim_status"),
            "anonymized_upload_ready": anonymized.get("upload_ready"),
        },
        "items": items,
        "missing_evidence_files": missing_evidence,
        "remaining_author_actions": [
            "Fill the official ARR Responsible NLP checklist in the submission system using these draft answers as support.",
            "Confirm final data-rights and redistribution boundaries after selecting the final supplement.",
            "Render and inspect the final anonymous ACL PDF and upload-safe supplement.",
            "Complete human-gold, IAA, adjudication, mapping/crosswalk expert review, and active-review effort returns before final performance claims.",
            "Confirm no dual submission and remove identifying metadata immediately before upload.",
        ],
        "claim_boundaries": [
            "This artifact prepares checklist answers; it is not the official submitted checklist.",
            "safe_to_use_as_submission=false and submission_ready=false are intentional.",
            "No final quality, mapping, or review-efficiency claims are unlocked by this artifact.",
            "Human-gold and expert-review blockers remain active.",
        ],
        "outputs": {
            "json": rel(release / "responsible_nlp_checklist_prep.json"),
            "markdown": rel(release / "responsible_nlp_checklist_prep.md"),
            "csv": rel(release / "responsible_nlp_checklist_items.csv"),
        },
    }
    return payload


def render_report(payload):
    summary = payload["summary"]
    rows = [
        {
            "item_id": item["item_id"],
            "checklist_area": item["checklist_area"],
            "status": item["status"],
            "paper_section": item["paper_section"],
            "remaining_action": item["remaining_action"],
            "claim_boundary": item["claim_boundary"],
        }
        for item in payload["items"]
    ]
    evidence_rows = []
    seen = set()
    for item in payload["items"]:
        for evidence in item["evidence_files"]:
            key = evidence["path"]
            if key in seen:
                continue
            seen.add(key)
            evidence_rows.append(evidence)
    lines = [
        "# CAPE-KG Responsible NLP Checklist Prep",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Plan: `{payload['plan_file']}`",
        "",
        "This artifact prepares draft answers and evidence mapping for the ARR/EACL Responsible NLP checklist. It is not the official completed checklist and intentionally keeps `safe_to_use_as_submission=false`, `submission_ready=false`, and `final_answers_ready=false`.",
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
                {"Item": "Final answers ready", "Value": payload["final_answers_ready"]},
                {"Item": "Checklist prep items", "Value": summary["item_count"]},
                {"Item": "Draft answer count", "Value": summary["draft_answer_count"]},
                {"Item": "Pending author confirmations", "Value": summary["pending_author_confirmation_count"]},
                {"Item": "Missing evidence files", "Value": summary["missing_evidence_files"]},
                {"Item": "ARR policy checklist", "Value": summary["arr_policy_claim_status"]},
                {"Item": "ARR08 status", "Value": summary["arr_responsible_nlp_status"]},
                {"Item": "Claim gate", "Value": summary["claim_gate_overall_status"]},
                {"Item": "Public reproducibility", "Value": summary["public_reproducibility_claim_status"]},
                {"Item": "Anonymized prep", "Value": summary["anonymized_submission_prep_claim_status"]},
                {"Item": "Anonymized upload ready", "Value": summary["anonymized_upload_ready"]},
            ],
        ),
        "",
        "## Checklist Draft Items",
        "",
        md_table(["item_id", "checklist_area", "status", "paper_section", "remaining_action", "claim_boundary"], rows),
        "",
        "## Draft Answers",
        "",
    ]
    for item in payload["items"]:
        lines += [
            f"### {item['item_id']}. {item['checklist_area']}",
            "",
            item["draft_answer"],
            "",
            f"- Status: `{item['status']}`",
            f"- Paper section: `{item['paper_section']}`",
            f"- Remaining action: {item['remaining_action']}",
            f"- Claim boundary: {item['claim_boundary']}",
            "",
        ]
    lines += [
        "## Remaining Author Actions",
        "",
    ]
    for action in payload["remaining_author_actions"]:
        lines.append(f"- {action}")
    lines += [
        "",
        "## Claim Boundaries",
        "",
    ]
    for boundary in payload["claim_boundaries"]:
        lines.append(f"- {boundary}")
    lines += [
        "",
        "## Evidence Files",
        "",
        md_table(["path", "exists", "bytes"], evidence_rows),
        "",
        "## Missing Evidence",
        "",
    ]
    if payload["missing_evidence_files"]:
        for path in payload["missing_evidence_files"]:
            lines.append(f"- `{path}`")
    else:
        lines.append("- No missing evidence files.")
    return "\n".join(lines) + "\n"


def rows_for_csv(items):
    rows = []
    for item in items:
        rows.append(
            {
                "item_id": item["item_id"],
                "checklist_area": item["checklist_area"],
                "status": item["status"],
                "paper_section": item["paper_section"],
                "draft_answer": item["draft_answer"],
                "remaining_action": item["remaining_action"],
                "claim_boundary": item["claim_boundary"],
                "evidence_files": "; ".join(evidence["path"] for evidence in item["evidence_files"]),
                "missing_evidence_files": "; ".join(item["missing_evidence_files"]),
            }
        )
    return rows


def run(args):
    payload = build_payload(args.experiment_dir, args.plan_file)
    release = Path(args.experiment_dir) / "06_release"
    json_path = release / "responsible_nlp_checklist_prep.json"
    md_path = release / "responsible_nlp_checklist_prep.md"
    csv_path = release / "responsible_nlp_checklist_items.csv"
    write_json(json_path, payload)
    write_text(md_path, render_report(payload))
    write_csv(
        csv_path,
        rows_for_csv(payload["items"]),
        [
            "item_id",
            "checklist_area",
            "status",
            "paper_section",
            "draft_answer",
            "remaining_action",
            "claim_boundary",
            "evidence_files",
            "missing_evidence_files",
        ],
    )
    print(
        json.dumps(
            {
                "json": rel(json_path),
                "markdown": rel(md_path),
                "csv": rel(csv_path),
                "overall_status": payload["overall_status"],
                "claim_status": payload["claim_status"],
                "item_count": payload["summary"]["item_count"],
                "missing_evidence_files": payload["summary"]["missing_evidence_files"],
                "final_answers_ready": payload["final_answers_ready"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if payload["overall_status"] != "PASS":
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--plan-file", default=str(DEFAULT_PLAN_FILE))
    run(parser.parse_args())


if __name__ == "__main__":
    main()
