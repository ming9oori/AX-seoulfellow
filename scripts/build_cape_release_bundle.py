#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build CAPE-KG EACL release bundles with checksums and safety notes."""

import argparse
import csv
import hashlib
import json
import tarfile
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_OUTPUTS_DIR = Path("outputs")
DEFAULT_PLAN_FILE = Path("AX_EACL_submission_review_revised_plan.md")

SCRIPT_FILES = [
    "scripts/audit_cape_plan_requirements.py",
    "scripts/build_cape_annotation_calibration_pack.py",
    "scripts/build_cape_annotation_batch_assignments.py",
    "scripts/build_cape_annotation_batch_review_preview.py",
    "scripts/build_cape_anonymized_submission_prep.py",
    "scripts/build_cape_annotation_expansion_package.py",
    "scripts/build_cape_gold_sampling_coverage_report.py",
    "scripts/build_cape_gold_item_feasibility_report.py",
    "scripts/build_cape_annotation_progress_report.py",
    "scripts/build_cape_annotation_workbench.py",
    "scripts/build_cape_active_review_human_effort.py",
    "scripts/build_cape_ablation_coverage_report.py",
    "scripts/build_cape_alias_canonicalization_report.py",
    "scripts/build_cape_arr_submission_policy_checklist.py",
    "scripts/build_cape_eacl_paper_draft.py",
    "scripts/build_cape_eacl_submission_package_manifest.py",
    "scripts/build_cape_evaluation_protocol_lock.py",
    "scripts/build_cape_experiment_reproduction_card.py",
    "scripts/build_cape_external_resource_license_report.py",
    "scripts/build_cape_human_gate_action_plan.py",
    "scripts/build_cape_human_review_master_checklist.py",
    "scripts/build_cape_human_review_first_batch_card.py",
    "scripts/build_cape_human_review_role_quickstart.py",
    "scripts/build_cape_human_review_status_dashboard.py",
    "scripts/build_cape_human_review_launch_checklist.py",
    "scripts/build_cape_human_review_packet_integrity_report.py",
    "scripts/build_cape_human_review_handoff.py",
    "scripts/build_cape_kg_eacl_experiment.py",
    "scripts/build_cape_mapping_review_progress_report.py",
    "scripts/build_cape_mapping_review_workbench.py",
    "scripts/build_cape_component_evidence_spans.py",
    "scripts/build_cape_predicate_cue_spans.py",
    "scripts/build_cape_annotation_protocol_traceability.py",
    "scripts/build_cape_metric_traceability_audit.py",
    "scripts/build_cape_contribution_claim_traceability.py",
    "scripts/build_cape_related_work_baseline_traceability.py",
    "scripts/build_cape_evidence_graph_projection.py",
    "scripts/build_cape_ncs_pcf_crosswalk.py",
    "scripts/build_cape_claim_language_guardrails.py",
    "scripts/build_cape_claimable_main_table.py",
    "scripts/build_cape_eacl_plan_compliance_matrix.py",
    "scripts/build_cape_annotation_qc_report.py",
    "scripts/build_cape_cq_query_pack.py",
    "scripts/build_cape_neo4j_evidence_query_pack.py",
    "scripts/build_cape_paper_tables.py",
    "scripts/build_cape_paper_table_blueprint.py",
    "scripts/build_cape_paper_section_source_map.py",
    "scripts/build_cape_post_human_scoring_readiness.py",
    "scripts/build_cape_provenance_manifest.py",
    "scripts/build_cape_prov_o_export.py",
    "scripts/build_cape_prompt_node_edge_traceability.py",
    "scripts/build_cape_schema_retrieval_coverage_report.py",
    "scripts/build_cape_public_synthetic_examples.py",
    "scripts/build_cape_public_reproducibility_manifest.py",
    "scripts/build_cape_rq_evidence_matrix.py",
    "scripts/build_cape_reviewer_risk_register.py",
    "scripts/build_cape_reviewer_response_prep.py",
    "scripts/build_cape_responsible_nlp_checklist_prep.py",
    "scripts/build_cape_revised_plan_completion_audit.py",
    "scripts/build_cape_schema_plan_alignment_report.py",
    "scripts/build_cape_submission_timeline_action_board.py",
    "scripts/build_cape_method_module_coverage.py",
    "scripts/build_cape_method_novelty_positioning.py",
    "scripts/build_cape_qwen3_model_scaling_report.py",
    "scripts/build_cape_release_bundle.py",
    "scripts/build_cape_strict_json_diagnostics.py",
    "scripts/build_cape_structural_evaluation.py",
    "scripts/build_cape_structural_gap_worklist.py",
    "scripts/build_cape_structural_review_action_plan.py",
    "scripts/validate_cape_structural_review_returns.py",
    "scripts/build_cape_structural_review_application_plan.py",
    "scripts/build_cape_submission_completion_audit.py",
    "scripts/cape_pre_human_status.py",
    "scripts/build_sac_kg_verifier_pruner_baseline.py",
    "scripts/check_qwen3_32b_awq_readiness.py",
    "scripts/compute_cape_annotation_iaa.py",
    "scripts/compute_cape_statistical_analysis.py",
    "scripts/evaluate_actual_llm_silver.py",
    "scripts/evaluate_cape_active_review_efficiency.py",
    "scripts/evaluate_cape_crosswalk_review.py",
    "scripts/evaluate_cape_human_gold.py",
    "scripts/evaluate_cape_human_gold_span_iou.py",
    "scripts/evaluate_cape_mapping_review.py",
    "scripts/export_cape_kg_rdf_shacl.py",
    "scripts/export_kg_to_neo4j.py",
    "scripts/import_cape_gold_annotation.py",
    "scripts/import_cape_crosswalk_review.py",
    "scripts/import_cape_mapping_review.py",
    "scripts/prepare_cape_adjudication_draft.py",
    "scripts/prepare_cape_crosswalk_review_package.py",
    "scripts/prepare_cape_gold_annotation_package.py",
    "scripts/prepare_cape_mapping_review_package.py",
    "scripts/profile_public_benchmarks.py",
    "scripts/run_ax_epak_on_211.sh",
    "scripts/run_ax_epak_preprocessed.sh",
    "scripts/run_cape_kg_eacl_experiment.sh",
    "scripts/run_cape_llm_condition_baselines.py",
    "scripts/run_cape_annotation_roundtrip_smoke.py",
    "scripts/run_cape_active_review_effort_roundtrip_smoke.py",
    "scripts/run_cape_human_return_apply.sh",
    "scripts/run_cape_strong_return_apply.sh",
    "scripts/run_cape_mapping_roundtrip_smoke.py",
    "scripts/run_cape_crosswalk_roundtrip_smoke.py",
    "scripts/run_cape_post_annotation_refresh.sh",
    "scripts/run_cep_onto_llm_extraction.py",
    "scripts/run_public_benchmark_llm_eval.py",
    "scripts/serve_kg_viewer.sh",
    "scripts/start_neo4j_kg.sh",
    "scripts/sync_cape_annotation_manifest.py",
    "scripts/validate_cape_human_review_returns.py",
    "scripts/validate_cape_pre_human_handoff.py",
    "scripts/validate_cape_strong_review_returns.py",
    "scripts/validate_neo4j_import_csv.py",
    "scripts/validate_cape_experiment_readiness.py",
]

PUBLIC_SAFE_EXP_DIRS = [
    "00_plan",
    "02_schema",
    "04_evaluation",
    "06_release",
    "07_reports",
]

PUBLIC_SAFE_PUBLIC_BENCHMARK_SUFFIXES = (
    "_summary.json",
    "_report.md",
    "_metrics.json",
    "_results.jsonl",
    "_valid.jsonl",
    "_manifest.json",
)

TEXT_RISK_PATTERNS = [
    "01_data/",
    "05_review/human_gold_batches/",
    "gold_annotation_template.jsonl",
    "evaluation_chunks.jsonl",
    "annotation_workbench.html",
    "annotator_",
    "adjudication.jsonl",
    "adjudication_draft.jsonl",
]
TEXT_SCAN_SUFFIXES = {
    ".csv",
    ".html",
    ".json",
    ".jsonl",
    ".md",
    ".sh",
    ".ttl",
    ".txt",
    ".yaml",
    ".yml",
}
TEXT_SCAN_MAX_BYTES = 5 * 1024 * 1024

PUBLIC_SAFE_EXCLUDE_PATH_PATTERNS = [
    "06_release/annotation_roundtrip_smoke/",
    "06_release/active_review_effort_roundtrip_smoke/",
    "06_release/mapping_roundtrip_smoke/",
    "06_release/crosswalk_roundtrip_smoke/",
    "06_release/human_review_handoff/",
    "06_release/human_review_packet_integrity",
    "scripts/build_cape_human_review_packet_integrity_report.py",
    "06_release/gold_sampling_coverage_report",
    "06_release/gold_item_feasibility_report",
    "06_release/public_external_release_review_queue.csv",
    "06_release/public_external_release_review_queue.md",
    "06_release/public_external_release_excluded_review_queue.csv",
    "06_release/public_external_release_excluded_review_queue.md",
]


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


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def should_skip(path):
    path = Path(path)
    parts = set(path.parts)
    if "__pycache__" in parts:
        return True
    if "06_release" in parts and "bundles" in parts:
        return True
    if path.suffix in {".pyc", ".pyo"}:
        return True
    if path.name.endswith((".tar.gz", ".tgz", ".zip")):
        return True
    if path.name in {"release_bundle_manifest.json", "release_bundle_checksums.sha256"}:
        return True
    if path.name == "release_bundle_safety_report.md":
        return True
    if path.name in {
        "latest_release_bundle_index.json",
        "latest_release_bundle_index.md",
        "anonymized_submission_prep.json",
        "anonymized_submission_prep.md",
        "anonymized_submission_risk_scan.csv",
        "eacl_submission_package_manifest.json",
        "eacl_submission_package_manifest.md",
        "post_annotation_refresh_last_run.json",
        "post_annotation_refresh_last_run.md",
    }:
        return True
    if path.name in {"pre_human_handoff_validation.json", "pre_human_handoff_validation.md"}:
        return True
    if path.name in {"human_review_status_dashboard_ko.json", "human_review_status_dashboard_ko.md"}:
        return True
    return False


def iter_files(root):
    root = Path(root)
    if not root.exists():
        return
    if root.is_file():
        if not should_skip(root):
            yield root
        return
    for path in sorted(root.rglob("*")):
        if path.is_file() and not should_skip(path):
            yield path


def unique_existing(paths):
    seen = set()
    output = []
    for path in paths:
        path = Path(path)
        if not path.exists() or should_skip(path):
            continue
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        output.append(path)
    return output


def internal_files(exp_dir, outputs_dir, plan_file):
    files = []
    files.append(plan_file)
    files.extend(Path(path) for path in SCRIPT_FILES)
    files.extend(iter_files(exp_dir))
    files.extend(iter_files(outputs_dir))
    return unique_existing(files)


def public_safe_files(exp_dir, plan_file):
    files = [plan_file]
    for path in SCRIPT_FILES:
        path = Path(path)
        name = rel(path)
        if any(pattern in name for pattern in PUBLIC_SAFE_EXCLUDE_PATH_PATTERNS):
            continue
        files.append(path)
    for rel_dir in PUBLIC_SAFE_EXP_DIRS:
        for path in iter_files(exp_dir / rel_dir):
            name = rel(path)
            if any(pattern in name for pattern in PUBLIC_SAFE_EXCLUDE_PATH_PATTERNS):
                continue
            files.append(path)
    public_dir = exp_dir / "08_public_benchmarks"
    if public_dir.exists():
        for path in iter_files(public_dir):
            if path.name.endswith(PUBLIC_SAFE_PUBLIC_BENCHMARK_SUFFIXES):
                files.append(path)
    return unique_existing(files)


def filter_public_external_files(files):
    """Exclude public-safe candidates that still mention internal review paths.

    The internal reproducibility bundle keeps those files. The public-safe
    skeleton is intentionally narrower: if a candidate file's path or text
    references source-data, annotator, adjudication, or human-review batch
    conventions, it is left out and recorded in an internal review queue.
    """
    candidate_files = unique_existing(files)
    path_risks = risky_public_paths(candidate_files)
    text_risks = risky_public_text_references(candidate_files)
    excluded_names = set(path_risks)
    excluded_names.update(row.get("path") for row in text_risks if row.get("path"))
    filtered = [path for path in candidate_files if rel(path) not in excluded_names]
    return filtered, path_risks, text_risks


def rel(path):
    return str(Path(path).as_posix())


def write_checksum_file(path, files):
    rows = []
    for item in files:
        rows.append((sha256_file(item), rel(item)))
    text = "".join(f"{digest}  {name}\n" for digest, name in rows)
    write_text(path, text)
    return rows


def add_file(tar, path, arcname=None):
    tar.add(path, arcname=arcname or rel(path), recursive=False)


def make_bundle(
    bundle_path,
    files,
    checksum_path,
    metadata_path=None,
    safety_report_path=None,
    metadata_arcname=None,
):
    with tarfile.open(bundle_path, "w:gz") as tar:
        for path in files:
            add_file(tar, path)
        add_file(tar, checksum_path)
        if metadata_path and Path(metadata_path).exists():
            add_file(tar, metadata_path, arcname=metadata_arcname)
        if safety_report_path and Path(safety_report_path).exists():
            add_file(tar, safety_report_path)
    return {
        "path": str(bundle_path),
        "bytes": Path(bundle_path).stat().st_size,
        "sha256": sha256_file(bundle_path),
    }


def risky_public_paths(files):
    risky = []
    for path in files:
        name = rel(path)
        if any(pattern in name for pattern in TEXT_RISK_PATTERNS):
            risky.append(name)
    return risky


def risky_public_text_references(files):
    risky = []
    for path in files:
        path = Path(path)
        if path.suffix.lower() not in TEXT_SCAN_SUFFIXES:
            continue
        if not path.exists() or path.stat().st_size > TEXT_SCAN_MAX_BYTES:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            risky.append({"path": rel(path), "pattern": "unreadable_text_file", "detail": str(exc)})
            continue
        for pattern in TEXT_RISK_PATTERNS:
            count = text.count(pattern)
            if count:
                risky.append({"path": rel(path), "pattern": pattern, "occurrences": count})
    return risky


def render_public_external_release_review_queue(payload):
    path_risks = payload.get("public_safe_risky_paths") or []
    text_risks = payload.get("public_safe_risky_text_references") or []
    lines = [
        "# CAPE-KG Public External Release Review Queue",
        "",
        f"Generated: {payload['generated_at_utc']}",
        "",
        "This queue lists conservative path/name risks found while preparing the public-safe release skeleton. It is an internal release-review aid. A warning here does not prove that source text leaked; it marks files that should be inspected before external publication.",
        "",
        "## Summary",
        "",
        "| Item | Value |",
        "|---|---:|",
        f"| Public-safe candidate files | {payload['public_safe_file_count']} |",
        f"| Risky public-safe paths | {len(path_risks)} |",
        f"| Risky text references | {len(text_risks)} |",
        "",
        "## Recommended Policy",
        "",
        "- Keep the internal reproducibility bundle private unless source-data rights are cleared.",
        "- Treat `01_data/`, annotator/adjudication filenames, and human-review batch paths as internal operational references.",
        "- Before external publication, inspect or redact public-safe files listed below if the target release must not expose internal directory conventions.",
        "- Do not use this review queue as human-gold performance evidence.",
        "",
    ]
    if path_risks:
        lines += ["## Risky Paths", ""]
        lines += [f"- `{path}`" for path in path_risks]
        lines.append("")
    lines += [
        "## Risky Text References",
        "",
        "| path | pattern | occurrences | review_action |",
        "|---|---|---:|---|",
    ]
    if text_risks:
        for row in text_risks:
            lines.append(
                f"| `{row.get('path')}` | `{row.get('pattern')}` | {row.get('occurrences', '')} | inspect_or_redact_before_external_release |"
            )
    else:
        lines.append("|  |  | 0 | inspect_or_redact_before_external_release_not_required |")
    lines.append("")
    return "\n".join(lines)


def render_public_external_release_excluded_queue(payload):
    path_risks = payload.get("public_safe_candidate_risky_paths") or []
    text_risks = payload.get("public_safe_candidate_risky_text_references") or []
    excluded_count = payload.get("public_safe_excluded_file_count", 0)
    lines = [
        "# CAPE-KG Public External Release Excluded Queue",
        "",
        f"Generated: {payload['generated_at_utc']}",
        "",
        "This internal queue lists public-safe candidate files that were excluded from the public-safe skeleton because they mention conservative internal source-data, annotator, adjudication, or human-review path/name patterns.",
        "",
        "## Summary",
        "",
        "| Item | Value |",
        "|---|---:|",
        f"| Candidate files before filtering | {payload.get('public_safe_candidate_file_count', 0)} |",
        f"| Files excluded from public-safe skeleton | {excluded_count} |",
        f"| Candidate risky paths | {len(path_risks)} |",
        f"| Candidate risky text references | {len(text_risks)} |",
        "",
        "## Excluded Text References",
        "",
        "| path | pattern | occurrences | public_release_action |",
        "|---|---|---:|---|",
    ]
    if text_risks:
        for row in text_risks:
            lines.append(
                f"| `{row.get('path')}` | `{row.get('pattern')}` | {row.get('occurrences', '')} | excluded_from_public_safe_skeleton |"
            )
    else:
        lines.append("|  |  | 0 | no_action_needed |")
    if path_risks:
        lines += ["", "## Excluded Risky Paths", ""]
        lines += [f"- `{path}`" for path in path_risks]
    lines.append("")
    return "\n".join(lines)


def build_safety_report(payload):
    public = payload["public_safe_bundle"]
    internal = payload["internal_bundle"]
    lines = [
        "# CAPE-KG Release Bundle Safety Report",
        "",
        f"Generated: {payload['generated_at_utc']}",
        "",
        "## Bundles",
        "",
        f"- Internal reproducibility bundle: `{internal['path']}`",
        f"  - SHA256: `{internal['sha256']}`",
        f"  - Files: {payload['internal_file_count']}",
        f"- Public-safe skeleton bundle: `{public['path']}`",
        f"  - SHA256: `{public['sha256']}`",
        f"  - Files: {payload['public_safe_file_count']}",
        "",
        "## Safety Notes",
        "",
        "- The internal bundle may contain source-derived chunk text and annotation work files. Treat it as local/internal unless rights are cleared.",
        "- The public-safe skeleton bundle excludes `01_data`, human-gold batch files, annotation JSONL files, and raw source-text workbench inputs.",
        "- Live post-bundle status files such as `latest_release_bundle_index`, `pre_human_handoff_validation`, `human_review_status_dashboard_ko`, `anonymized_submission_prep`, `eacl_submission_package_manifest`, and `post_annotation_refresh_last_run` are regenerated outside the tarball to avoid self-referential checksum drift.",
        "- Public paper claims still require human gold annotation, IAA, adjudication, and human-gold scoring.",
        "",
        "## Public-Safe Text-Risk Scan",
        "",
    ]
    risky = payload.get("public_safe_risky_paths") or []
    if risky:
        lines.append("The following public-safe files match conservative text-risk patterns and should be inspected before external release:")
        lines += [f"- `{name}`" for name in risky[:200]]
    else:
        lines.append("- No public-safe bundle files matched the conservative text-risk patterns.")
    lines += [
        "",
        "## Public-Safe Text-Content Reference Scan",
        "",
    ]
    risky_text = payload.get("public_safe_risky_text_references") or []
    if risky_text:
        lines.append("The following public-safe text files mention conservative internal path/name patterns. These are metadata references, not necessarily leaked source text, but they should be reviewed before external release:")
        for row in risky_text[:200]:
            lines.append(
                f"- `{row.get('path')}`: pattern `{row.get('pattern')}`, occurrences={row.get('occurrences', '')}"
            )
    else:
        lines.append("- No public-safe text files mentioned conservative internal path/name patterns.")
    excluded_count = payload.get("public_safe_excluded_file_count", 0)
    if excluded_count:
        lines += [
            "",
            "## Public-Safe Candidate Exclusions",
            "",
            f"- Files excluded from the public-safe skeleton by conservative text/path filtering: {excluded_count}",
            f"- Excluded-file review queue: `{payload.get('public_external_release_excluded_review_queue_md')}`",
        ]
    lines += [
        "",
        "## Checksum Files",
        "",
        f"- Internal checksums: `{payload['internal_checksums']}`",
        f"- Public-safe checksums: `{payload['public_safe_checksums']}`",
        "",
    ]
    return "\n".join(lines)


def build_latest_release_index(payload, bundle_dir, release_dir):
    bundle_dir = Path(bundle_dir)
    release_dir = Path(release_dir)
    current_paths = {
        "internal_bundle": payload["internal_bundle"]["path"],
        "public_safe_bundle": payload["public_safe_bundle"]["path"],
        "release_manifest": str(release_dir / "release_bundle_manifest.json"),
        "release_checksums": str(release_dir / "release_bundle_checksums.sha256"),
        "safety_report": payload["safety_report"],
    }
    bundle_files = sorted(bundle_dir.glob("cape_kg_eacl_*"))
    previous_internal = [
        str(path)
        for path in bundle_files
        if path.name.startswith("cape_kg_eacl_internal_repro_")
        and str(path) != payload["internal_bundle"]["path"]
    ]
    previous_public = [
        str(path)
        for path in bundle_files
        if path.name.startswith("cape_kg_eacl_public_safe_skeleton_")
        and str(path) != payload["public_safe_bundle"]["path"]
    ]
    return {
        "generated_at_utc": payload["generated_at_utc"],
        "claim_status": "latest_release_bundle_index_ready_not_submission_complete",
        "experiment_dir": payload["experiment_dir"],
        "outputs_dir": payload["outputs_dir"],
        "plan_file": payload["plan_file"],
        "stamp": payload["stamp"],
        "current": {
            "internal_bundle": payload["internal_bundle"],
            "public_safe_bundle": payload["public_safe_bundle"],
            "release_manifest": current_paths["release_manifest"],
            "release_checksums": current_paths["release_checksums"],
            "safety_report": current_paths["safety_report"],
            "internal_file_count": payload["internal_file_count"],
            "public_safe_file_count": payload["public_safe_file_count"],
            "public_safe_excluded_file_count": payload["public_safe_excluded_file_count"],
        },
        "verification_commands": {
            "release_checksums": f"sha256sum -c {current_paths['release_checksums']}",
            "pre_human_validation": (
                "python3 scripts/validate_cape_pre_human_handoff.py "
                "--experiment-dir experiments/cape_kg_eacl_20260627 --outputs-dir outputs"
            ),
            "handoff_checksums": (
                "sha256sum -c experiments/cape_kg_eacl_20260627/06_release/"
                "human_review_handoff/human_review_handoff_checksums.sha256"
            ),
        },
        "superseded_bundle_counts": {
            "internal_repro": len(previous_internal),
            "public_safe_skeleton": len(previous_public),
        },
        "recent_superseded_internal_repro": previous_internal[-10:],
        "recent_superseded_public_safe_skeleton": previous_public[-10:],
        "public_release_note": (
            "Use the public-safe skeleton bundle for external artifact sharing. "
            "The internal reproducibility bundle may contain source-derived text and review work files."
        ),
        "completion_note": (
            "These bundles are release/reproducibility artifacts only. Submission-level performance claims "
            "remain pending human-gold annotation, IAA, adjudication, proposed human-gold scoring, "
            "mapping expert review, NCS-PCF crosswalk expert review, and active-review effort collection."
        ),
    }


def render_latest_release_index(index):
    current = index["current"]
    internal = current["internal_bundle"]
    public = current["public_safe_bundle"]
    commands = index["verification_commands"]
    lines = [
        "# CAPE-KG Latest Release Bundle Index",
        "",
        f"Generated: {index['generated_at_utc']}",
        f"Claim status: `{index['claim_status']}`",
        f"Stamp: `{index['stamp']}`",
        "",
        "## Current Bundles",
        "",
        "| bundle | path | sha256 | bytes | files |",
        "| --- | --- | --- | ---: | ---: |",
        f"| internal reproducibility | `{internal['path']}` | `{internal['sha256']}` | {internal['bytes']} | {current['internal_file_count']} |",
        f"| public-safe skeleton | `{public['path']}` | `{public['sha256']}` | {public['bytes']} | {current['public_safe_file_count']} |",
        "",
        "## Verification Commands",
        "",
        f"```bash\n{commands['release_checksums']}\n{commands['handoff_checksums']}\n{commands['pre_human_validation']}\n```",
        "",
        "## Superseded Bundle Counts",
        "",
        f"- Internal reproducibility bundles older than current: {index['superseded_bundle_counts']['internal_repro']}",
        f"- Public-safe skeleton bundles older than current: {index['superseded_bundle_counts']['public_safe_skeleton']}",
        "",
        "## Public Release Note",
        "",
        f"- {index['public_release_note']}",
        f"- {index['completion_note']}",
        "",
        "## Related Files",
        "",
        f"- Release manifest: `{current['release_manifest']}`",
        f"- Release checksums: `{current['release_checksums']}`",
        f"- Safety report: `{current['safety_report']}`",
        "",
    ]
    return "\n".join(lines)


def run(args):
    exp_dir = Path(args.experiment_dir)
    outputs_dir = Path(args.outputs_dir)
    plan_file = Path(args.plan_file)
    release_dir = exp_dir / "06_release"
    bundle_dir = release_dir / "bundles"
    bundle_dir.mkdir(parents=True, exist_ok=True)
    stamp = args.stamp or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    public_probe = public_safe_files(exp_dir, plan_file)
    generated_at = datetime.now(timezone.utc).isoformat()
    review_queue_csv_path = release_dir / "public_external_release_review_queue.csv"
    review_queue_md_path = release_dir / "public_external_release_review_queue.md"
    excluded_queue_csv_path = release_dir / "public_external_release_excluded_review_queue.csv"
    excluded_queue_md_path = release_dir / "public_external_release_excluded_review_queue.md"
    public, candidate_risky_paths, candidate_risky_text = filter_public_external_files(public_probe)
    excluded_names = set(candidate_risky_paths)
    excluded_names.update(row.get("path") for row in candidate_risky_text if row.get("path"))
    review_payload = {
        "generated_at_utc": generated_at,
        "experiment_dir": str(exp_dir),
        "outputs_dir": str(outputs_dir),
        "plan_file": str(plan_file),
        "stamp": stamp,
        "internal_file_count": 0,
        "public_safe_candidate_file_count": len(public_probe),
        "public_safe_file_count": len(public),
        "public_safe_excluded_file_count": len(excluded_names),
        "public_safe_candidate_risky_paths": candidate_risky_paths,
        "public_safe_candidate_risky_text_references": candidate_risky_text,
        "public_safe_risky_paths": risky_public_paths(public),
        "public_safe_risky_text_references": risky_public_text_references(public),
    }
    write_csv(
        review_queue_csv_path,
        review_payload["public_safe_risky_text_references"],
        ["path", "pattern", "occurrences", "detail"],
    )
    write_text(review_queue_md_path, render_public_external_release_review_queue(review_payload))
    write_csv(
        excluded_queue_csv_path,
        review_payload["public_safe_candidate_risky_text_references"],
        ["path", "pattern", "occurrences", "detail"],
    )
    write_text(excluded_queue_md_path, render_public_external_release_excluded_queue(review_payload))

    internal = internal_files(exp_dir, outputs_dir, plan_file)
    internal_checksum_path = bundle_dir / f"cape_kg_eacl_internal_{stamp}.sha256"
    public_checksum_path = bundle_dir / f"cape_kg_eacl_public_safe_{stamp}.sha256"
    write_checksum_file(internal_checksum_path, internal)
    write_checksum_file(public_checksum_path, public)

    metadata_path = bundle_dir / f"cape_kg_eacl_release_metadata_{stamp}.json"
    public_metadata_path = bundle_dir / f"cape_kg_eacl_public_release_metadata_{stamp}.json"
    safety_report_path = release_dir / "release_bundle_safety_report.md"
    pre_payload = {
        "generated_at_utc": generated_at,
        "experiment_dir": str(exp_dir),
        "outputs_dir": str(outputs_dir),
        "plan_file": str(plan_file),
        "stamp": stamp,
        "internal_file_count": len(internal),
        "public_safe_file_count": len(public),
        "internal_checksums": str(internal_checksum_path),
        "public_safe_checksums": str(public_checksum_path),
        "public_safe_candidate_file_count": len(public_probe),
        "public_safe_excluded_file_count": len(excluded_names),
        "public_safe_candidate_risky_paths": candidate_risky_paths,
        "public_safe_candidate_risky_text_references": candidate_risky_text,
        "public_safe_risky_paths": risky_public_paths(public),
        "public_safe_risky_text_references": risky_public_text_references(public),
        "public_external_release_review_queue_csv": str(review_queue_csv_path),
        "public_external_release_review_queue_md": str(review_queue_md_path),
        "public_external_release_excluded_review_queue_csv": str(excluded_queue_csv_path),
        "public_external_release_excluded_review_queue_md": str(excluded_queue_md_path),
    }
    write_csv(
        review_queue_csv_path,
        pre_payload["public_safe_risky_text_references"],
        ["path", "pattern", "occurrences", "detail"],
    )
    write_text(review_queue_md_path, render_public_external_release_review_queue(pre_payload))
    write_csv(
        excluded_queue_csv_path,
        pre_payload["public_safe_candidate_risky_text_references"],
        ["path", "pattern", "occurrences", "detail"],
    )
    write_text(excluded_queue_md_path, render_public_external_release_excluded_queue(pre_payload))
    write_json(metadata_path, pre_payload)
    write_json(public_metadata_path, {
        "generated_at_utc": generated_at,
        "stamp": stamp,
        "public_safe_file_count": len(public),
        "public_safe_candidate_file_count": len(public_probe),
        "public_safe_excluded_file_count": len(excluded_names),
        "public_safe_filter_policy": "Excluded candidate files whose paths or text mentioned conservative internal source-data, annotation, adjudication, or human-review naming patterns.",
        "public_safe_risky_path_count": len(pre_payload["public_safe_risky_paths"]),
        "public_safe_risky_text_reference_count": len(pre_payload["public_safe_risky_text_references"]),
        "claim_status": "public_safe_skeleton_filtered_for_external_release_not_submission_complete",
    })

    internal_bundle_path = bundle_dir / f"cape_kg_eacl_internal_repro_{stamp}.tar.gz"
    public_bundle_path = bundle_dir / f"cape_kg_eacl_public_safe_skeleton_{stamp}.tar.gz"
    internal_bundle = make_bundle(
        internal_bundle_path,
        internal,
        internal_checksum_path,
        metadata_path,
        metadata_arcname=f"release_metadata/cape_kg_eacl_release_metadata_{stamp}.json",
    )
    public_bundle = make_bundle(
        public_bundle_path,
        public,
        public_checksum_path,
        public_metadata_path,
        metadata_arcname=f"release_metadata/cape_kg_eacl_public_release_metadata_{stamp}.json",
    )

    payload = {
        **pre_payload,
        "internal_bundle": internal_bundle,
        "public_safe_bundle": public_bundle,
        "metadata_file": str(metadata_path),
        "public_metadata_file": str(public_metadata_path),
        "safety_report": str(safety_report_path),
        "claim_status": "release_bundles_ready_not_submission_complete",
    }
    write_text(safety_report_path, build_safety_report(payload))
    write_json(release_dir / "release_bundle_manifest.json", payload)
    write_text(
        release_dir / "release_bundle_checksums.sha256",
        f"{internal_bundle['sha256']}  {internal_bundle['path']}\n{public_bundle['sha256']}  {public_bundle['path']}\n",
    )
    latest_index = build_latest_release_index(payload, bundle_dir, release_dir)
    write_json(release_dir / "latest_release_bundle_index.json", latest_index)
    write_text(release_dir / "latest_release_bundle_index.md", render_latest_release_index(latest_index))
    print(json.dumps({
        "manifest": str(release_dir / "release_bundle_manifest.json"),
        "checksums": str(release_dir / "release_bundle_checksums.sha256"),
        "safety_report": str(safety_report_path),
        "latest_index": str(release_dir / "latest_release_bundle_index.md"),
        "internal_bundle": internal_bundle,
        "public_safe_bundle": public_bundle,
    }, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--outputs-dir", default=str(DEFAULT_OUTPUTS_DIR))
    parser.add_argument("--plan-file", default=str(DEFAULT_PLAN_FILE))
    parser.add_argument("--stamp", default="")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
