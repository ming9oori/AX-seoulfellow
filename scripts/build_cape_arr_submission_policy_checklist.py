#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build an ARR/EACL submission policy checklist for CAPE-KG."""

import argparse
import json
import re
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

from cape_pre_human_status import effective_prehuman_summary


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_PLAN_FILE = Path("AX_EACL_submission_review_revised_plan.md")
READY_STATUS = "arr_submission_policy_checklist_ready_not_submission_complete"
ARR_TARGET_DATE = date(2026, 8, 3)

OFFICIAL_SOURCES = [
    {
        "source_id": "SRC01_eacl_2027_dates",
        "title": "EACL 2027 official site",
        "url": "https://2027.eacl.org/",
        "used_for": "ARR submission deadline and conference date.",
    },
    {
        "source_id": "SRC02_arr_cfp",
        "title": "ACL Rolling Review Call for Papers",
        "url": "https://aclrollingreview.org/cfp",
        "used_for": "ARR submission, anonymized supplementary material, and desk-rejection policy cues.",
    },
    {
        "source_id": "SRC03_arr_author_checklist",
        "title": "ARR author checklist / common submission problems",
        "url": "https://aclrollingreview.org/authorchecklist",
        "used_for": "Page-limit and Limitations-section checks.",
    },
    {
        "source_id": "SRC04_aclpub_formatting",
        "title": "ACLPUB paper formatting guidelines",
        "url": "https://acl-org.github.io/ACLPUB/formatting.html",
        "used_for": "Limitations placement and formatting expectations.",
    },
    {
        "source_id": "SRC05_arr_authors",
        "title": "ARR author guidelines",
        "url": "https://aclrollingreview.org/authors",
        "used_for": "Under-review and anonymous-preprint policy cues.",
    },
    {
        "source_id": "SRC06_responsible_nlp",
        "title": "ARR Responsible NLP Research Checklist",
        "url": "https://aclrollingreview.org/responsibleNLPresearch/",
        "used_for": "Ethics, societal impact, and reproducibility checklist scope.",
    },
]


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


def section_positions(text):
    positions = {}
    for match in re.finditer(r"^##\s+(.+?)\s*$", text, flags=re.MULTILINE):
        positions[match.group(1).strip()] = match.start()
    return positions


def checklist_item(item_id, requirement, status, paper_use_now, evidence_paths, source_ids, blocker, next_action):
    evidence = [file_state(path) for path in evidence_paths]
    missing = [row["path"] for row in evidence if not row["exists"] or row["bytes"] == 0]
    return {
        "item_id": item_id,
        "requirement": requirement,
        "status": status,
        "paper_use_now": paper_use_now,
        "evidence_files": evidence,
        "missing_evidence_files": missing,
        "source_ids": source_ids,
        "blocker": blocker,
        "next_action": next_action,
    }


def build_items(exp_dir, plan_file):
    exp_dir = Path(exp_dir)
    release = exp_dir / "06_release"
    reports = exp_dir / "07_reports"
    draft_path = reports / "eacl_paper_draft.md"
    draft_text = draft_path.read_text(encoding="utf-8") if draft_path.exists() else ""
    positions = section_positions(draft_text)
    has_limitations = "Limitations" in positions
    has_ethics = "Ethical Considerations" in positions
    has_conclusion = "Conclusion" in positions
    has_references = "References" in positions
    limitations_order_ok = (
        has_conclusion
        and has_limitations
        and has_references
        and positions["Conclusion"] < positions["Limitations"] < positions["References"]
    )
    ethics_order_ok = has_ethics and has_references and positions["Ethical Considerations"] < positions["References"]

    claim_gate = read_json(release / "claim_gate_report.json", {}) or {}
    draft_status = read_json(release / "eacl_paper_draft_status.json", {}) or {}
    validation = read_json(release / "pre_human_handoff_validation.json", {}) or {}
    effective_validation = effective_prehuman_summary(validation)
    return [
        checklist_item(
            "ARR01_deadline_tracking",
            "Track EACL 2027 ARR submission target date and use AoE-style planning.",
            "pass",
            "schedule_reference_only",
            [plan_file, release / "submission_timeline_action_board.md"],
            ["SRC01_eacl_2027_dates"],
            "none",
            "Keep the action board synchronized if official dates change.",
        ),
        checklist_item(
            "ARR02_claim_gate_not_submission_ready",
            "Do not mark the package as submission-ready while required human-gold claim gates fail.",
            "pass_expected_not_ready",
            "internal_go_no_go",
            [release / "claim_gate_report.md", release / "submission_completion_audit_ko.md", release / "pre_human_handoff_validation.md"],
            ["SRC02_arr_cfp"],
            f"claim_gate={claim_gate.get('overall_status')}; required_failures={claim_gate.get('required_failure_count')}",
            "Complete human-gold, IAA, adjudication, and proposed-method human-gold scoring before submission-ready language.",
        ),
        checklist_item(
            "ARR03_limitations_section",
            "Paper draft includes a dedicated Limitations section after Conclusion and before References.",
            "pass" if limitations_order_ok else "fail",
            "draft_section_ready",
            [draft_path, release / "limitations.md"],
            ["SRC03_arr_author_checklist", "SRC04_aclpub_formatting"],
            "none" if limitations_order_ok else "Limitations section missing or misplaced.",
            "Keep Limitations limited to limitations; avoid new results, figures, or analysis in that section.",
        ),
        checklist_item(
            "ARR04_ethics_section",
            "Paper draft includes ethics/data-release discussion before References.",
            "pass" if ethics_order_ok else "fail",
            "draft_section_ready",
            [draft_path, release / "data_release_ethics_statement.md", release / "external_resource_license_report.md"],
            ["SRC06_responsible_nlp"],
            "none" if ethics_order_ok else "Ethical Considerations section missing or misplaced.",
            "Keep data release, private source-text rights, human review, and LLM-use risks synchronized.",
        ),
        checklist_item(
            "ARR05_anonymization",
            "Submission manuscript and supplementary material must be anonymized before ARR upload.",
            "pending_author_action",
            "internal_only_until_anonymized",
            [draft_path, release / "public_reproducibility_manifest.md", release / "release_bundle_safety_report.md"],
            ["SRC02_arr_cfp", "SRC05_arr_authors"],
            "Current draft/release paths are internal and not anonymized for upload.",
            "Prepare an anonymized paper PDF and anonymized supplement bundle from the public-safe release only.",
        ),
        checklist_item(
            "ARR06_page_limit_pdf_check",
            "Long/short paper page limits must be checked on the final ACL-formatted PDF.",
            "pending_pdf_render",
            "not_checkable_from_markdown",
            [draft_path, release / "paper_section_source_map.md", release / "paper_table_blueprint.md"],
            ["SRC03_arr_author_checklist", "SRC04_aclpub_formatting"],
            "Markdown draft cannot prove ACL PDF page count.",
            "Render with the current ACL template and verify long/short page count before upload.",
        ),
        checklist_item(
            "ARR07_supplement_public_safe",
            "Supplementary material should be anonymized and avoid tracking/file-hosting risks.",
            "public_safe_scaffold_ready_anonymization_pending",
            "internal_release_ready_not_upload_ready",
            [release / "latest_release_bundle_index.md", release / "public_reproducibility_manifest.md", release / "public_external_release_review_queue.md"],
            ["SRC02_arr_cfp"],
            "latest_release_bundle_index.md is the authoritative current-bundle pointer; upload-ready anonymization is not yet produced.",
            "Use public-safe skeleton, remove identifying paths/names, and package through an allowed submission mechanism.",
        ),
        checklist_item(
            "ARR08_responsible_nlp_checklist",
            "Responsible NLP, ethics, societal impact, and reproducibility issues should be explicitly covered.",
            "scaffold_ready_final_answers_pending",
            "draft_support_ready",
            [release / "data_release_ethics_statement.md", release / "public_reproducibility_manifest.md", release / "reviewer_risk_register.md"],
            ["SRC06_responsible_nlp"],
            "Final checklist answers must be filled at submission time.",
            "Use the Responsible NLP checklist prep plus data-release, license, public-safe, and reviewer-risk artifacts to fill the official checklist.",
        ),
        checklist_item(
            "ARR09_no_dual_submission",
            "Authors must ensure the paper is not simultaneously submitted elsewhere while under ARR review.",
            "pending_author_confirmation",
            "author_policy_confirmation_required",
            [release / "submission_timeline_action_board.md"],
            ["SRC05_arr_authors"],
            "Requires author confirmation; cannot be proven by repository artifacts.",
            "Confirm submission venue status immediately before ARR upload.",
        ),
        checklist_item(
            "ARR10_final_artifact_sync",
            "Final paper, tables, claims, protocol lock, provenance, and release bundle must be regenerated after any human returns.",
            "pass_pre_human_scaffold",
            "internal_process_ready",
            [
                release / "post_human_scoring_readiness.md",
                release / "paper_table_blueprint.md",
                release / "evaluation_protocol_lock.md",
                release / "provenance_manifest.md",
                release / "eacl_submission_package_manifest.md",
            ],
            ["SRC02_arr_cfp"],
            f"pre_human_validation={validation.get('overall_status')}; paper_submission_ready={draft_status.get('submission_ready')}",
            "After human returns, rerun post-annotation refresh and regenerate the final anonymized submission package.",
        ),
    ]


def build_payload(exp_dir, plan_file):
    exp_dir = Path(exp_dir)
    release = exp_dir / "06_release"
    items = build_items(exp_dir, plan_file)
    missing = [path for row in items for path in row["missing_evidence_files"]]
    status_counts = Counter(row["status"] for row in items)
    validation = read_json(release / "pre_human_handoff_validation.json", {}) or {}
    effective_validation = effective_prehuman_summary(validation)
    claim_gate = read_json(release / "claim_gate_report.json", {}) or {}
    draft_status = read_json(release / "eacl_paper_draft_status.json", {}) or {}
    generated = datetime.now(timezone.utc)
    as_of = generated.date()

    return {
        "generated_at_utc": generated.isoformat(),
        "as_of_date": as_of.isoformat(),
        "plan_file": rel(plan_file),
        "experiment_dir": rel(exp_dir),
        "official_sources": OFFICIAL_SOURCES,
        "overall_status": "PASS" if not missing else "FAIL",
        "claim_status": READY_STATUS if not missing else "arr_submission_policy_checklist_incomplete",
        "safe_to_use_as_submission": False,
        "submission_ready": False,
        "summary": {
            "arr_target_date": ARR_TARGET_DATE.isoformat(),
            "days_to_arr_target": (ARR_TARGET_DATE - as_of).days,
            "item_count": len(items),
            "missing_evidence_files": len(missing),
            "status_counts": dict(sorted(status_counts.items())),
            "pre_human_validation_status": effective_validation.get("overall_status"),
            "pre_human_validation_checks": effective_validation.get("check_count"),
            "claim_gate_overall_status": claim_gate.get("overall_status"),
            "claim_gate_required_failures": claim_gate.get("required_failure_count"),
            "paper_draft_submission_ready": draft_status.get("submission_ready"),
            "paper_draft_safe_to_use_as_submission": draft_status.get("safe_to_use_as_submission"),
            "official_source_count": len(OFFICIAL_SOURCES),
        },
        "items": items,
        "missing_evidence_files": missing,
    }


def render_markdown(payload):
    summary = payload["summary"]
    rows = [
        {
            "id": row["item_id"],
            "requirement": row["requirement"],
            "status": row["status"],
            "paper_use_now": row["paper_use_now"],
            "blocker": row["blocker"],
            "next_action": row["next_action"],
        }
        for row in payload["items"]
    ]
    source_rows = [
        {
            "source_id": row["source_id"],
            "title": row["title"],
            "url": row["url"],
            "used_for": row["used_for"],
        }
        for row in payload["official_sources"]
    ]

    lines = [
        "# CAPE-KG ARR/EACL Submission Policy Checklist",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"As-of date: `{payload['as_of_date']}`",
        f"Plan: `{payload['plan_file']}`",
        "",
        "이 문서는 공식 EACL/ARR/ACLPUB 제출 요구사항을 현재 CAPE-KG paper draft, release bundle, claim gate와 연결한 checklist입니다.",
        "형식·정책 준비 상태를 보는 문서이며, human-gold 성능 gate를 대체하지 않습니다.",
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
                {"Item": "ARR target date", "Value": summary["arr_target_date"]},
                {"Item": "Days to ARR target", "Value": summary["days_to_arr_target"]},
                {"Item": "Checklist items", "Value": summary["item_count"]},
                {"Item": "Missing evidence files", "Value": summary["missing_evidence_files"]},
                {"Item": "Claim gate", "Value": summary["claim_gate_overall_status"]},
                {"Item": "Pre-human validation", "Value": summary["pre_human_validation_status"]},
                {"Item": "Pre-human checks", "Value": summary["pre_human_validation_checks"]},
            ],
        ),
        "",
        "## Checklist",
        "",
        md_table(["id", "requirement", "status", "paper_use_now", "blocker", "next_action"], rows),
        "",
        "## Official Sources",
        "",
        md_table(["source_id", "title", "url", "used_for"], source_rows),
        "",
        "## Detailed Evidence",
        "",
    ]
    for row in payload["items"]:
        lines.extend(
            [
                f"### {row['item_id']}. {row['requirement']}",
                "",
                f"- Status: `{row['status']}`",
                f"- Paper use now: `{row['paper_use_now']}`",
                f"- Source IDs: {', '.join(row['source_ids'])}",
                f"- Blocker: {row['blocker']}",
                f"- Next action: {row['next_action']}",
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
            "- `pass` means the local artifact required for that policy item exists; it does not mean the paper is submission-ready.",
            "- `pending_author_action`, `pending_pdf_render`, and anonymization-related statuses require manual author or final-PDF work.",
            "- `safe_to_use_as_submission=false` and `submission_ready=false` are intentional while human-gold and expert-review gates remain open.",
            "- Re-run this builder after changing official deadlines, paper sections, release bundles, or human-return status.",
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
    json_path = release / "arr_submission_policy_checklist.json"
    md_path = release / "arr_submission_policy_checklist.md"
    write_json(json_path, payload)
    write_text(md_path, render_markdown(payload))
    print(
        json.dumps(
            {
                "json": rel(json_path),
                "markdown": rel(md_path),
                "overall_status": payload["overall_status"],
                "claim_status": payload["claim_status"],
                "item_count": payload["summary"]["item_count"],
                "missing_evidence_files": payload["summary"]["missing_evidence_files"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
