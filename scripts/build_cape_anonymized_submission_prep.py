#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build an anonymized-submission preparation report for CAPE-KG."""

import argparse
import csv
import json
import re
import tarfile
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_PLAN_FILE = Path("AX_EACL_submission_review_revised_plan.md")
READY_STATUS = "anonymized_submission_prep_ready_not_upload_ready"

TEXT_SUFFIXES = {".csv", ".json", ".jsonl", ".md", ".py", ".sh", ".ttl", ".txt", ".yaml", ".yml"}
TEXT_SCAN_MAX_BYTES = 2 * 1024 * 1024

RISK_PATTERNS = [
    ("absolute_home_path", re.compile(r"/home/[^\s`\"']+|/Users/[^\s`\"']+")),
    ("local_user_or_lab_name", re.compile(r"\b(minjoo|idsl)\b", re.IGNORECASE)),
    ("workspace_name", re.compile(r"AX_서울펠로우|AX_서울펠로우")),
    ("internal_experiment_path", re.compile(r"experiments/cape_kg_eacl_20260627")),
    ("source_or_review_private_path", re.compile(r"\b(01_data|05_review|human_review_handoff|gold_annotation_template|evaluation_chunks|annotator_|adjudication)\b")),
    ("internal_bundle_reference", re.compile(r"internal_repro|internal_bundle|source-derived", re.IGNORECASE)),
]

FORBIDDEN_PUBLIC_TAR_PATTERNS = (
    "01_data/",
    "05_review/",
    "human_review_handoff/",
    "gold_annotation_template.jsonl",
    "evaluation_chunks.jsonl",
    "annotator_A.jsonl",
    "annotator_B.jsonl",
    "adjudication.jsonl",
    "adjudication_draft.jsonl",
    "internal_repro",
)


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


def scan_text_file(path, scope, max_hits=200):
    path = Path(path)
    hits = []
    if not path.exists() or not path.is_file() or path.suffix not in TEXT_SUFFIXES:
        return hits
    if path.stat().st_size > TEXT_SCAN_MAX_BYTES:
        return hits
    text = path.read_text(encoding="utf-8", errors="replace")
    for line_no, line in enumerate(text.splitlines(), start=1):
        for pattern_id, regex in RISK_PATTERNS:
            if regex.search(line):
                hits.append(
                    {
                        "scope": scope,
                        "path": rel(path),
                        "line": line_no,
                        "risk_type": pattern_id,
                        "severity": "manual_rewrite_required" if scope == "paper_draft" else "review_before_upload",
                        "snippet": line.strip()[:240],
                    }
                )
                if len(hits) >= max_hits:
                    return hits
    return hits


def scan_tar_names(path):
    path = Path(path)
    if not path.exists() or not path.is_file():
        return [], {"exists": False, "file_count": 0, "path": rel(path)}
    forbidden = []
    try:
        with tarfile.open(path, "r:gz") as tar:
            names = tar.getnames()
    except Exception as exc:
        return [{"scope": "public_safe_tar", "path": rel(path), "risk_type": "tar_open_error", "severity": "blocking", "snippet": str(exc)}], {
            "exists": True,
            "file_count": 0,
            "path": rel(path),
            "open_error": str(exc),
        }
    for name in names:
        normalized = name.replace("\\", "/")
        for pattern in FORBIDDEN_PUBLIC_TAR_PATTERNS:
            if pattern in normalized:
                forbidden.append(
                    {
                        "scope": "public_safe_tar",
                        "path": normalized,
                        "line": "",
                        "risk_type": "forbidden_tar_member",
                        "severity": "blocking",
                        "snippet": pattern,
                    }
                )
                break
    return forbidden, {"exists": True, "file_count": len(names), "path": rel(path)}


def build_payload(exp_dir, plan_file):
    exp_dir = Path(exp_dir)
    release = exp_dir / "06_release"
    reports = exp_dir / "07_reports"
    latest = read_json(release / "latest_release_bundle_index.json", {}) or {}
    public_bundle = ((latest.get("current") or {}).get("public_safe_bundle") or {}).get("path")
    public_bundle_path = Path(public_bundle) if public_bundle else Path("__missing_public_bundle__")

    scan_targets = [
        ("paper_draft", reports / "eacl_paper_draft.md"),
        ("public_manifest_md", release / "public_reproducibility_manifest.md"),
        ("public_manifest_json", release / "public_reproducibility_manifest.json"),
        ("public_review_queue", release / "public_external_release_review_queue.md"),
        ("release_safety_report", release / "release_bundle_safety_report.md"),
        ("latest_release_index", release / "latest_release_bundle_index.md"),
        ("arr_policy_checklist", release / "arr_submission_policy_checklist.md"),
    ]
    text_hits = []
    for scope, path in scan_targets:
        text_hits.extend(scan_text_file(path, scope))
    tar_hits, tar_summary = scan_tar_names(public_bundle_path)
    risk_rows = text_hits + tar_hits

    required_inputs = [
        file_state(Path(plan_file)),
        file_state(reports / "eacl_paper_draft.md"),
        file_state(release / "arr_submission_policy_checklist.md"),
        file_state(release / "public_reproducibility_manifest.md"),
        file_state(release / "latest_release_bundle_index.json"),
        file_state(public_bundle_path),
    ]
    missing_inputs = [row["path"] for row in required_inputs if not row["exists"] or row["bytes"] == 0]

    manual_gates = [
        {
            "gate_id": "ANON01_final_acl_pdf",
            "status": "pending_pdf_render",
            "action": "Render the final ACL-formatted PDF after human-gold results are inserted and verify page limits.",
        },
        {
            "gate_id": "ANON02_author_identity",
            "status": "pending_author_action",
            "action": "Remove author names, local usernames, acknowledgments, and self-identifying repository paths from the upload manuscript.",
        },
        {
            "gate_id": "ANON03_public_safe_supplement",
            "status": "public_safe_scaffold_ready_upload_rewrite_pending",
            "action": "Use only the public-safe skeleton bundle, rename the top-level supplement directory, and avoid source-text or internal review files.",
        },
        {
            "gate_id": "ANON04_rights_review",
            "status": "pending_author_rights_confirmation",
            "action": "Confirm that no restricted source text, OCR snippets, or private review work files are included in any external supplement.",
        },
        {
            "gate_id": "ANON05_final_policy_confirmation",
            "status": "pending_author_confirmation",
            "action": "Confirm no dual submission and complete responsible NLP / ethics checklist answers immediately before upload.",
        },
    ]
    blocking_tar_hits = [row for row in tar_hits if row.get("severity") == "blocking"]
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "plan_file": rel(plan_file),
        "experiment_dir": rel(exp_dir),
        "overall_status": "PASS" if not missing_inputs else "FAIL",
        "claim_status": READY_STATUS if not missing_inputs else "anonymized_submission_prep_incomplete",
        "safe_to_use_as_submission": False,
        "submission_ready": False,
        "upload_ready": False,
        "summary": {
            "required_inputs": len(required_inputs),
            "missing_inputs": len(missing_inputs),
            "scan_targets": len(scan_targets),
            "risk_rows": len(risk_rows),
            "paper_draft_risk_rows": sum(1 for row in risk_rows if row.get("scope") == "paper_draft"),
            "public_safe_tar_file_count": tar_summary.get("file_count"),
            "public_safe_tar_blocking_hits": len(blocking_tar_hits),
            "manual_gates": len(manual_gates),
            "release_stamp": latest.get("stamp"),
            "public_safe_bundle": rel(public_bundle_path),
        },
        "required_inputs_state": required_inputs,
        "missing_inputs": missing_inputs,
        "manual_gates": manual_gates,
        "risk_rows": risk_rows,
        "tar_summary": tar_summary,
        "interpretation": [
            "This report prepares anonymization and public-safe supplement review; it is not an upload-ready package.",
            "Internal path references in local reports are expected before final packaging, but must be rewritten or removed from the final ARR upload.",
            "The public-safe tar scan must stay free of source-text, human-review, adjudication, and internal reproducibility paths.",
            "Submission-ready language remains forbidden until human-gold, IAA, adjudication, final PDF, and author policy confirmations are complete.",
        ],
        "outputs": {
            "json": rel(release / "anonymized_submission_prep.json"),
            "markdown": rel(release / "anonymized_submission_prep.md"),
            "risk_csv": rel(release / "anonymized_submission_risk_scan.csv"),
        },
    }
    return payload


def md_table(headers, rows):
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        values = []
        for header in headers:
            values.append(str(row.get(header, "")).replace("|", "\\|").replace("\n", " "))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def render_report(payload):
    summary = payload["summary"]
    risk_preview = payload["risk_rows"][:40]
    lines = [
        "# CAPE-KG Anonymized Submission Prep",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Plan: `{payload['plan_file']}`",
        "",
        "이 문서는 ARR/EACL 업로드 직전 익명화와 public-safe supplement 준비를 위한 점검 산출물입니다. 최종 제출 승인 문서가 아니며, `safe_to_use_as_submission=false`와 `submission_ready=false`를 의도적으로 유지합니다.",
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
                {"Item": "Upload ready", "Value": payload["upload_ready"]},
                {"Item": "Risk rows", "Value": summary["risk_rows"]},
                {"Item": "Paper draft risk rows", "Value": summary["paper_draft_risk_rows"]},
                {"Item": "Public-safe tar file count", "Value": summary["public_safe_tar_file_count"]},
                {"Item": "Public-safe tar blocking hits", "Value": summary["public_safe_tar_blocking_hits"]},
                {"Item": "Manual gates", "Value": summary["manual_gates"]},
                {"Item": "Release stamp", "Value": summary["release_stamp"]},
                {"Item": "Public-safe bundle", "Value": summary["public_safe_bundle"]},
            ],
        ),
        "",
        "## Manual Gates",
        "",
        md_table(["gate_id", "status", "action"], payload["manual_gates"]),
        "",
        "## Required Inputs",
        "",
        md_table(["path", "exists", "bytes"], payload["required_inputs_state"]),
        "",
        "## Risk Scan Preview",
        "",
    ]
    if risk_preview:
        lines.append(md_table(["scope", "path", "line", "risk_type", "severity", "snippet"], risk_preview))
        if len(payload["risk_rows"]) > len(risk_preview):
            lines.append("")
            lines.append(f"- Full risk scan rows: `{payload['outputs']['risk_csv']}`")
    else:
        lines.append("- No conservative risk rows were found in the scanned targets.")
    lines += [
        "",
        "## Upload Policy",
        "",
        "- Final manuscript upload requires a rendered ACL PDF, not this Markdown draft.",
        "- Supplement upload should be built from the public-safe skeleton only; internal reproducibility bundles are not upload candidates.",
        "- Source-text paths, annotation handoff files, annotator/adjudication files, and local usernames must not appear in the uploaded supplement.",
        "- This artifact is allowed to report internal paths because it is an internal preparation report.",
        "",
        "## Interpretation",
        "",
    ]
    for item in payload["interpretation"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def run(args):
    payload = build_payload(args.experiment_dir, args.plan_file)
    release = Path(args.experiment_dir) / "06_release"
    json_path = release / "anonymized_submission_prep.json"
    md_path = release / "anonymized_submission_prep.md"
    csv_path = release / "anonymized_submission_risk_scan.csv"
    write_json(json_path, payload)
    write_text(md_path, render_report(payload))
    write_csv(csv_path, payload["risk_rows"], ["scope", "path", "line", "risk_type", "severity", "snippet"])
    print(json.dumps({
        "json": rel(json_path),
        "markdown": rel(md_path),
        "risk_csv": rel(csv_path),
        "overall_status": payload["overall_status"],
        "claim_status": payload["claim_status"],
        "risk_rows": payload["summary"]["risk_rows"],
        "public_safe_tar_blocking_hits": payload["summary"]["public_safe_tar_blocking_hits"],
        "upload_ready": payload["upload_ready"],
    }, ensure_ascii=False, indent=2))
    if payload["overall_status"] != "PASS":
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--plan-file", default=str(DEFAULT_PLAN_FILE))
    run(parser.parse_args())


if __name__ == "__main__":
    main()
