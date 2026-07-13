#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build source/license status report for CAPE-KG external resources."""

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_OUTPUTS_DIR = Path("outputs")

FIELDS = [
    "resource_id",
    "resource_type",
    "role_in_study",
    "source_url",
    "paper_url",
    "local_path",
    "local_status",
    "license_name",
    "license_file",
    "license_sha256",
    "git_revision",
    "adapter_subset_file",
    "adapter_subset_items",
    "public_safe_release_action",
    "citation_or_rights_note",
    "claim_status",
]


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256_file(path):
    path = Path(path)
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path):
    return str(Path(path).as_posix())


def local_status(path):
    path = Path(path)
    if path.exists() and path.is_dir():
        return "present_dir"
    if path.exists() and path.is_file():
        return "present_file"
    return "missing"


def license_name_from_file(path):
    path = Path(path)
    if not path.exists():
        return ""
    head = path.read_text(encoding="utf-8", errors="replace")[:4000].lower()
    if "apache license" in head and "version 2.0" in head:
        return "Apache-2.0"
    if "mit license" in head:
        return "MIT"
    return "present_unclassified"


def benchmark_row(exp_dir, benchmark_id, profile):
    local_repo = Path(profile.get("local_repo") or exp_dir / "08_public_benchmarks/repos" / benchmark_id)
    license_file = local_repo / "LICENSE"
    return {
        "resource_id": benchmark_id,
        "resource_type": "public_benchmark",
        "role_in_study": "external procedural/KG sanity check and public reproducibility adapter",
        "source_url": profile.get("source_url", ""),
        "paper_url": profile.get("paper_url", ""),
        "local_path": rel(local_repo),
        "local_status": local_status(local_repo),
        "license_name": license_name_from_file(license_file),
        "license_file": rel(license_file) if license_file.exists() else "",
        "license_sha256": sha256_file(license_file),
        "git_revision": profile.get("git_revision", ""),
        "adapter_subset_file": profile.get("adapter_subset_file", ""),
        "adapter_subset_items": profile.get("adapter_subset_items", ""),
        "public_safe_release_action": "release_adapter_outputs_and_cite_original_license; do_not_relicense_original_benchmark",
        "citation_or_rights_note": "Follow original benchmark license and cite the paper/source URL in any public release.",
        "claim_status": "public_adapter_diagnostic_not_target_corpus_human_gold",
    }


def build_rows(exp_dir, outputs_dir):
    exp_dir = Path(exp_dir)
    outputs_dir = Path(outputs_dir)
    benchmark_dir = exp_dir / "08_public_benchmarks"
    manifest = read_json(benchmark_dir / "public_benchmark_manifest.json", {}) or {}
    benchmarks = manifest.get("benchmarks") or {}
    rows = []
    for benchmark_id in ["PAGED", "Text2KGBench"]:
        profile = benchmarks.get(benchmark_id) or read_json(benchmark_dir / f"{benchmark_id.lower()}_profile.json", {}) or {}
        if profile:
            rows.append(benchmark_row(exp_dir, benchmark_id, profile))

    synthetic_dir = exp_dir / "06_release/public_synthetic_examples"
    rows.append(
        {
            "resource_id": "CAPE_public_synthetic_examples",
            "resource_type": "synthetic_release_artifact",
            "role_in_study": "public-safe format example for schema, evidence anchors, gold rows, and predictions",
            "source_url": "",
            "paper_url": "",
            "local_path": rel(synthetic_dir),
            "local_status": local_status(synthetic_dir),
            "license_name": "project_defined_synthetic_example",
            "license_file": "",
            "license_sha256": "",
            "git_revision": "",
            "adapter_subset_file": rel(synthetic_dir / "synthetic_chunks.jsonl"),
            "adapter_subset_items": 2,
            "public_safe_release_action": "public_safe_include",
            "citation_or_rights_note": "Synthetic only; not copied, paraphrased, or derived from the private/source corpus.",
            "claim_status": "format_example_not_paper_result",
        }
    )
    rows.append(
        {
            "resource_id": "private_bid_proposal_corpus",
            "resource_type": "private_source_corpus",
            "role_in_study": "target Korean bid/proposal procedural KG corpus",
            "source_url": "",
            "paper_url": "",
            "local_path": rel(outputs_dir / "02_ocr/ocr_sentences_clean.jsonl"),
            "local_status": local_status(outputs_dir / "02_ocr/ocr_sentences_clean.jsonl"),
            "license_name": "rights_review_required",
            "license_file": "",
            "license_sha256": "",
            "git_revision": "",
            "adapter_subset_file": "",
            "adapter_subset_items": "",
            "public_safe_release_action": "exclude_raw_text_from_public_safe_bundle",
            "citation_or_rights_note": "Do not externally publish raw OCR/source-derived text unless redistribution rights are explicitly cleared.",
            "claim_status": "internal_only_pending_rights_review",
        }
    )
    rows.append(
        {
            "resource_id": "NCS_standard_layer",
            "resource_type": "standard_taxonomy",
            "role_in_study": "Layer1 competency reference axis and Layer2 mapping target",
            "source_url": "NCS public standard source to be cited in final paper after rights verification",
            "paper_url": "",
            "local_path": rel(outputs_dir / "01_layer1/layer1_ncs_nodes.jsonl"),
            "local_status": local_status(outputs_dir / "01_layer1/layer1_ncs_nodes.jsonl"),
            "license_name": "verify_before_public_redistribution",
            "license_file": "",
            "license_sha256": "",
            "git_revision": "",
            "adapter_subset_file": rel(outputs_dir / "08_mapping/l2_ncs_mapping_candidates.jsonl"),
            "adapter_subset_items": "",
            "public_safe_release_action": "cite_source_and_verify_redistribution_terms",
            "citation_or_rights_note": "Use as a reference layer; verify redistribution terms before including source-derived taxonomy files publicly.",
            "claim_status": "mapping_candidate_ready_expert_review_pending",
        }
    )
    rows.append(
        {
            "resource_id": "PCF_standard_layer",
            "resource_type": "standard_taxonomy",
            "role_in_study": "Layer1 process reference axis and Layer2 mapping target",
            "source_url": "PCF source to be cited in final paper after rights verification",
            "paper_url": "",
            "local_path": rel(outputs_dir / "01_layer1/layer1_pcf_nodes.jsonl"),
            "local_status": local_status(outputs_dir / "01_layer1/layer1_pcf_nodes.jsonl"),
            "license_name": "verify_before_public_redistribution",
            "license_file": "",
            "license_sha256": "",
            "git_revision": "",
            "adapter_subset_file": rel(outputs_dir / "08_mapping/l2_pcf_mapping_candidates.jsonl"),
            "adapter_subset_items": "",
            "public_safe_release_action": "cite_source_and_verify_redistribution_terms",
            "citation_or_rights_note": "Use as a reference layer; verify redistribution terms before including source-derived taxonomy files publicly.",
            "claim_status": "mapping_candidate_ready_expert_review_pending",
        }
    )
    return rows


def build_payload(exp_dir, outputs_dir):
    rows = build_rows(exp_dir, outputs_dir)
    issues = []
    for row in rows:
        if row["resource_type"] == "public_benchmark":
            if row["local_status"] == "missing":
                issues.append({"resource_id": row["resource_id"], "error": "missing_local_repo"})
            if row["license_name"] != "Apache-2.0":
                issues.append({"resource_id": row["resource_id"], "error": "unexpected_or_missing_license", "license_name": row["license_name"]})
            if not row["source_url"] or not row["paper_url"]:
                issues.append({"resource_id": row["resource_id"], "error": "missing_source_or_paper_url"})
            if int(row["adapter_subset_items"] or 0) <= 0:
                issues.append({"resource_id": row["resource_id"], "error": "missing_adapter_subset"})
        if not row["claim_status"]:
            issues.append({"resource_id": row["resource_id"], "error": "missing_claim_status"})
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "outputs_dir": str(outputs_dir),
        "claim_status": "external_resource_license_report_ready_not_legal_advice",
        "resource_count": len(rows),
        "public_benchmark_count": sum(1 for row in rows if row["resource_type"] == "public_benchmark"),
        "rights_review_required_count": sum(1 for row in rows if "review" in row["license_name"] or "verify" in row["license_name"]),
        "issue_count": len(issues),
        "issues": issues,
        "resources": rows,
        "outputs": {
            "json": str(Path(exp_dir) / "06_release/external_resource_license_report.json"),
            "csv": str(Path(exp_dir) / "06_release/external_resource_license_report.csv"),
            "markdown": str(Path(exp_dir) / "06_release/external_resource_license_report.md"),
        },
    }


def render_report(payload):
    lines = [
        "# CAPE-KG External Resource License and Citation Report",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Claim status: `{payload['claim_status']}`",
        "",
        "This report records source, license, citation, and public-release handling for external/public resources and release-sensitive internal resources. It is a reproducibility and release-safety artifact, not legal advice and not human-gold performance evidence.",
        "",
        "## Summary",
        "",
        "| Item | Value |",
        "|---|---:|",
        f"| Resources | {payload['resource_count']} |",
        f"| Public benchmarks | {payload['public_benchmark_count']} |",
        f"| Rights/redistribution review required | {payload['rights_review_required_count']} |",
        f"| Validation issues | {payload['issue_count']} |",
        "",
        "## Resource Table",
        "",
        "| resource | type | license/status | local status | public-safe release action | citation/rights note |",
        "|---|---|---|---|---|---|",
    ]
    for row in payload["resources"]:
        lines.append(
            f"| `{row['resource_id']}` | {row['resource_type']} | {row['license_name']} | "
            f"{row['local_status']} | {row['public_safe_release_action']} | {row['citation_or_rights_note']} |"
        )
    lines += [
        "",
        "## Public Benchmark Details",
        "",
        "| benchmark | source | paper | git revision | adapter items | license file |",
        "|---|---|---|---|---:|---|",
    ]
    for row in payload["resources"]:
        if row["resource_type"] != "public_benchmark":
            continue
        lines.append(
            f"| {row['resource_id']} | {row['source_url']} | {row['paper_url']} | "
            f"`{row['git_revision']}` | {row['adapter_subset_items']} | `{row['license_file']}` |"
        )
    if payload["issues"]:
        lines += ["", "## Issues", ""]
        for issue in payload["issues"]:
            lines.append(f"- `{issue.get('resource_id')}`: {issue.get('error')}")
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--outputs-dir", default=str(DEFAULT_OUTPUTS_DIR))
    args = parser.parse_args()

    exp_dir = Path(args.experiment_dir)
    outputs_dir = Path(args.outputs_dir)
    payload = build_payload(exp_dir, outputs_dir)
    json_path = exp_dir / "06_release/external_resource_license_report.json"
    csv_path = exp_dir / "06_release/external_resource_license_report.csv"
    md_path = exp_dir / "06_release/external_resource_license_report.md"
    write_json(json_path, payload)
    write_csv(csv_path, payload["resources"])
    write_text(md_path, render_report(payload))
    print(json.dumps({
        "json": str(json_path),
        "csv": str(csv_path),
        "markdown": str(md_path),
        "claim_status": payload["claim_status"],
        "resource_count": payload["resource_count"],
        "issue_count": payload["issue_count"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
