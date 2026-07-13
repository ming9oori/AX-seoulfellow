#!/usr/bin/env python3
"""Create and statically lock the APRE R3 experiment before any fresh API call."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import r3_apre as apre


PARENT_ID = "zaije_ldr_r2_20260712_blre_v1"
PRIMARY_CANDIDATES = {
    "C02": "gpt-4.1-mini-2025-04-14",
    "C03": "gpt-4o-2024-08-06",
    "C04": "gpt-4.1-2025-04-14",
}
FALSIFIER_CANDIDATES = {
    "C01": "gpt-4o-mini-2024-07-18",
    "C03": "gpt-4o-2024-08-06",
    "C04": "gpt-4.1-2025-04-14",
}


CLAIMHOOD_PROMPT = """You are measuring whether one exact source anchor bears an Atomic Work Claim.
Judge only the single anchor supplied. Read source_text and structural context. Do not rewrite or compare spans.
CLAIM_BEARING means the anchor, possibly with supplied structural context, asserts a work-relevant action, rule, definition, condition, evaluative proposition, or operationally usable fact.
NON_CLAIM means empty/invalid text, a bare title/label with no usable proposition, table decoration, or an anchor contradicted/unrelated to its source.
UNDERDETERMINED means the supplied source/context cannot support a stable decision.
evidence_support is SUPPORTED only when the exact anchor occurs in and is semantically supported by source_text.
Return the supplied anchor_id exactly."""

FACET_PROMPT = """Judge one proposed binary semantic facet for one exact Atomic Work Claim anchor.
Return SUPPORTED only when the source and structural context support the proposed facet, NOT_SUPPORTED when they do not, and UNDERDETERMINED when ambiguous.
Facets are orthogonal and need not be mutually exclusive. Do not rewrite the anchor. Return proposal_id exactly."""

FALSIFIER_PROMPT = """Act only as an independent falsifier. Given source, exact anchor, and one proposed value, decide whether the proposal is SUPPORTED, CONTRADICTED, or UNDERDETERMINED by the source.
Do not generate a replacement label. Treat altered quantities, unrelated anchors, and unsupported normative/general-rule promotion as contradicted. Return proposal_id exactly."""

DIAGNOSTIC_PROMPT = """Audit a deterministic atomic-anchor segmentation on exposed development data only.
Count a missing anchor only if a distinct work-relevant predicate/assertion in source_text has no matching anchor.
Count an over-merged anchor only if one anchor contains two independent predicates that should be separate claims.
An enumeration of entities, properties, or examples is not multiple independent predicates. A bare label cannot be over-merged.
Count broken structural context only when a list or table header is visibly present inside source_text, is required to interpret an anchor, and is absent from that anchor's supplied context links.
Do not count ordinary discourse anaphora, references to another page, external missing passages, a standalone list item with no visible header, or an ambiguous claim as broken structural context.
For a table value, supplied HAS_ROW_HEADER and HAS_COLUMN_HEADER links are sufficient even if the value is numeric.
document_context is valid orientation but is not itself an exact source span.
Return counts and the exact listed IDs. This is a diagnostic, not reference annotation."""


def dump_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def dump_yaml(path: Path, text: str) -> None:
    dump_text(path, text)


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    project = Path(__file__).resolve().parents[1]
    root = project / "experiments" / apre.EXPERIMENT_ID
    parent = project / "experiments" / PARENT_ID
    root.mkdir(parents=True, exist_ok=True)

    source_dev = parent / "data" / "dev_exposed_60.jsonl"
    source_bakeoff = parent / "data" / "model_bakeoff_24.jsonl"
    source_fresh = parent / "data" / "r2_pilot_60.jsonl"
    source_lock = parent / "data" / "r2_pilot_lock.json"
    expected_fresh_hash = "3e499252899e964b7363310e5733961fc3e6aa65aa4d0d382537839173003b17"
    if file_hash(source_fresh) != expected_fresh_hash:
        raise RuntimeError("Parent fresh60 hash mismatch")

    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    for source, target in [
        (source_dev, data_dir / "dev_exposed_60.jsonl"),
        (source_bakeoff, data_dir / "dev_qualification_24.jsonl"),
        (source_fresh, data_dir / "r3_pilot_60_imported_unexposed.jsonl"),
    ]:
        shutil.copyfile(source, target)

    dev = apre.read_jsonl(data_dir / "dev_exposed_60.jsonl")
    qualification = apre.read_jsonl(data_dir / "dev_qualification_24.jsonl")
    fresh = apre.read_jsonl(data_dir / "r3_pilot_60_imported_unexposed.jsonl")
    parent_lock = json.loads(source_lock.read_text(encoding="utf-8"))
    dev_ids = {row["evidence_id"] for row in dev}
    dev_groups = {row["leakage_group_id"] for row in dev}
    fresh_ids = {row["evidence_id"] for row in fresh}
    fresh_groups = {row["leakage_group_id"] for row in fresh}
    if len(fresh) != 60 or dev_ids & fresh_ids or dev_groups & fresh_groups:
        raise RuntimeError("Imported fresh60 leakage or count failure")

    dev_anchors = [apre.build_atomic_anchors(row) for row in dev]
    qualification_ids = {row["evidence_id"] for row in qualification}
    qualification_anchors = [row for row in dev_anchors if row["evidence_id"] in qualification_ids]
    fresh_anchors = [apre.build_atomic_anchors(row) for row in fresh]
    apre.write_jsonl(root / "anchor" / "dev_audit" / "dev_exposed_anchors.jsonl", dev_anchors)
    apre.write_jsonl(root / "anchor" / "dev_audit" / "dev_qualification_anchors.jsonl", qualification_anchors)
    apre.write_jsonl(root / "anchor" / "fresh60" / "anchors_pre_api.jsonl", fresh_anchors)
    dev_validation = apre.validate_anchor_records(dev_anchors)
    fresh_validation = apre.validate_anchor_records(fresh_anchors)
    first = (root / "anchor" / "fresh60" / "anchors_pre_api.jsonl").read_bytes()
    rerun = b"".join((apre.canonical(apre.build_atomic_anchors(row)) + "\n").encode("utf-8") for row in fresh)
    deterministic_identity = first == rerun

    source_hash = file_hash(Path(__file__).with_name("r3_apre.py"))
    try:
        git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=project.parent, text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        git_commit = "UNAVAILABLE"

    prompts = root / "preregistration" / "prompts"
    dump_text(prompts / "claimhood_v1.txt", CLAIMHOOD_PROMPT)
    dump_text(prompts / "facet_v1.txt", FACET_PROMPT)
    dump_text(prompts / "falsifier_v1.txt", FALSIFIER_PROMPT)
    dump_text(prompts / "segmenter_diagnostic_v1.txt", DIAGNOSTIC_PROMPT)

    claim_schema = {
        "type": "object", "additionalProperties": False,
        "required": ["anchor_id", "claimhood", "evidence_support"],
        "properties": {
            "anchor_id": {"type": "string"},
            "claimhood": {"type": "string", "enum": ["CLAIM_BEARING", "NON_CLAIM", "UNDERDETERMINED"]},
            "evidence_support": {"type": "string", "enum": ["SUPPORTED", "CONTRADICTED", "UNDERDETERMINED"]},
        },
    }
    decision_schema = {
        "type": "object", "additionalProperties": False,
        "required": ["proposal_id", "decision"],
        "properties": {
            "proposal_id": {"type": "string"},
            "decision": {"type": "string", "enum": ["SUPPORTED", "NOT_SUPPORTED", "UNDERDETERMINED"]},
        },
    }
    falsifier_schema = {
        "type": "object", "additionalProperties": False,
        "required": ["proposal_id", "decision"],
        "properties": {
            "proposal_id": {"type": "string"},
            "decision": {"type": "string", "enum": ["SUPPORTED", "CONTRADICTED", "UNDERDETERMINED"]},
        },
    }
    anchor_schema = {
        "type": "object", "additionalProperties": False,
        "required": ["anchor_id", "evidence_id", "start_char", "end_char", "text_by_program", "structure_type", "context_span_ids", "context_relations", "generation_rule", "source_hash"],
        "properties": {
            "anchor_id": {"type": "string"}, "evidence_id": {"type": "string"},
            "start_char": {"type": "integer", "minimum": 0}, "end_char": {"type": "integer", "minimum": 1},
            "text_by_program": {"type": "string"}, "structure_type": {"type": "string"},
            "context_span_ids": {"type": "array", "items": {"type": "string"}},
            "context_relations": {"type": "array", "items": {"type": "string"}},
            "generation_rule": {"type": "string"}, "source_hash": {"type": "string"},
        },
    }
    apre.write_json(root / "preregistration" / "anchor_schema_v1.json", anchor_schema)
    apre.write_json(root / "preregistration" / "field_schema_v1.json", decision_schema)
    apre.write_json(root / "preregistration" / "claimhood_schema_v1.json", claim_schema)
    apre.write_json(root / "preregistration" / "falsifier_schema_v1.json", falsifier_schema)

    dump_yaml(root / "preregistration" / "data_import_policy.yaml", f"""experiment_id: {apre.EXPERIMENT_ID}
parent_experiment_id: {PARENT_ID}
fresh_pilot_source: imported_unexposed_r2_lock
fresh_pilot_count: 60
membership_sha256: {expected_fresh_hash}
membership_change_allowed: false
prior_api_exposure: 0
test_access_allowed: false
""")
    dump_yaml(root / "preregistration" / "primary_model_policy.yaml", """required_configurations: 1
qualification_sample: DEV_EXPOSED_24
qualification_repeats: 2
fresh_repeats: 3
one_item_per_request: true
candidate_order_exposure: false
candidates:
  C02: gpt-4.1-mini-2025-04-14
  C03: gpt-4o-2024-08-06
  C04: gpt-4.1-2025-04-14
""")
    dump_yaml(root / "preregistration" / "falsifier_model_policy.yaml", """required_configurations: 1
must_differ_from_primary_snapshot: true
comparison_mode: pointwise
candidates:
  C01: gpt-4o-mini-2024-07-18
  C03: gpt-4o-2024-08-06
  C04: gpt-4.1-2025-04-14
""")
    dump_yaml(root / "preregistration" / "pointwise_api_policy.yaml", """one_item_per_request: true
cache_replay: false
fresh_transport: batch_api
dev_transport: synchronous_responses_api
same_id_repilot: false
retry_reasons: [transport_failure, rate_limit, truncated, refusal, incomplete]
fresh_request_cap: 3000
fresh_input_token_cap: 10000000
fresh_output_token_cap: 1000000
""")
    dump_yaml(root / "preregistration" / "gate_thresholds_r3.yaml", """r3_1:
  anchor_json_validity: 1.00
  offset_round_trip_validity: 1.00
  anchor_id_uniqueness: 1.00
  context_span_existence: 1.00
  deterministic_rerun_identity: 1.00
  dev_missing_anchor_max: 0.05
  dev_over_merged_anchor_max: 0.05
  dev_broken_structural_context_max: 0.02
r3_2_primary:
  schema_validity: 1.00
  anchor_id_validity: 1.00
  claimhood_repeat_agreement_min: 0.92
  positive_anchor_set_f1_min: 0.90
  critical_binary_facet_repeat_agreement_min: 0.90
  deterministic_control_balanced_accuracy_min: 0.95
  api_failure_rate_max: 0.01
r3_2_falsifier:
  supported_recall_min: 0.90
  contradicted_recall_min: 0.90
  balanced_accuracy_min: 0.92
  repeat_agreement_min: 0.90
r3_3:
  exact_agreement_min: 0.90
  positive_pairwise_f1_median_min: 0.90
  usable_coverage_min: 0.90
  unstable_rate_max: 0.10
""")
    dump_yaml(root / "preregistration" / "downstream_overlap_policy.yaml", """reference_model_overlap_primary_analysis: false
report_sets: [NO_REFERENCE_MODEL_OVERLAP, SELF_OVERLAP_SENSITIVITY, HARD_ONLY, HARD_PLUS_SOFT]
e0_e5_allowed_only_after: PROVISIONAL_REFERENCE_PASS
""")
    dump_text(root / "preregistration" / "r3_amendment_from_r2.md", """# R3 amendment from R2

R2 was stopped before fresh API exposure because only one of five configurations qualified for a required three-model panel. R3 registers a new hypothesis: one pinned primary model measured pointwise three times, deterministic rules, an independent pinned falsifier, and negative controls can form a provisional engineering reference. Listwise candidate comparison, majority-as-truth, single mutually exclusive semantic mode, and same-ID re-pilot are prohibited.
""")

    import_lock = {
        "experiment_id": apre.EXPERIMENT_ID,
        "imported_from_experiment_id": PARENT_ID,
        "source_lock_sha256": file_hash(source_lock),
        "source_membership_sha256": parent_lock["membership_sha256"],
        "imported_file_sha256": file_hash(data_dir / "r3_pilot_60_imported_unexposed.jsonl"),
        "evidence_count": len(fresh),
        "prior_api_exposure": 0,
        "dev_evidence_overlap": len(dev_ids & fresh_ids),
        "dev_leakage_group_overlap": len(dev_groups & fresh_groups),
        "membership_change_allowed": False,
        "test_access": 0,
    }
    apre.write_json(root / "locks" / "imported_fresh60_lock.json", import_lock)
    apre.write_json(root / "anchor" / "dev_audit" / "static_validation.json", dev_validation)
    apre.write_json(root / "anchor" / "fresh60" / "static_validation_pre_api.json", fresh_validation)
    gate_r30 = {
        "status": "PASS",
        "imported_fresh60_hash_match": file_hash(data_dir / "r3_pilot_60_imported_unexposed.jsonl") == expected_fresh_hash,
        "prior_api_exposure": 0,
        "dev_evidence_overlap": 0,
        "dev_leakage_group_overlap": 0,
        "test_access": 0,
        "membership_count": len(fresh),
    }
    apre.write_json(root / "reports" / "gate_r3_0.json", gate_r30)
    gate_r31_static = {
        "status": "PENDING_DEV_DIAGNOSTIC",
        "static_metrics": dev_validation,
        "fresh_pre_api_static_metrics": fresh_validation,
        "deterministic_rerun_identity": deterministic_identity,
        "segmenter_git_commit": git_commit,
        "segmenter_source_sha256": source_hash,
    }
    apre.write_json(root / "reports" / "gate_r3_1.json", gate_r31_static)

    lock_paths = [
        data_dir / "r3_pilot_60_imported_unexposed.jsonl",
        root / "locks" / "imported_fresh60_lock.json",
        root / "preregistration" / "data_import_policy.yaml",
        root / "preregistration" / "primary_model_policy.yaml",
        root / "preregistration" / "falsifier_model_policy.yaml",
        root / "preregistration" / "pointwise_api_policy.yaml",
        root / "preregistration" / "gate_thresholds_r3.yaml",
        root / "preregistration" / "downstream_overlap_policy.yaml",
    ]
    apre.write_json(root / "manifests" / "phase_a_lock_hashes.json", {
        str(path.relative_to(root)): file_hash(path) for path in lock_paths
    })
    apre.write_json(root / "manifests" / "pre_api_state.json", {
        "experiment_id": apre.EXPERIMENT_ID,
        "fresh_api_exposure": 0,
        "test_access": 0,
        "dev_anchor_count": dev_validation["anchor_count"],
        "qualification_anchor_count": sum(len(row["anchors"]) for row in qualification_anchors),
        "fresh_anchor_count": fresh_validation["anchor_count"],
        "segmenter_source_sha256": source_hash,
    })
    print(json.dumps({
        "experiment_id": apre.EXPERIMENT_ID,
        "gate_r3_0": "PASS",
        "gate_r3_1": "PENDING_DEV_DIAGNOSTIC",
        "dev_anchors": dev_validation["anchor_count"],
        "qualification_anchors": sum(len(row["anchors"]) for row in qualification_anchors),
        "fresh_anchors": fresh_validation["anchor_count"],
        "fresh_api_exposure": 0,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
