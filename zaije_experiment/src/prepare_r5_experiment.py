#!/usr/bin/env python3
"""Audit inputs and freeze the R5-CRSI-V preregistration."""

from __future__ import annotations

import json
import shutil
import sys
from collections import Counter
from pathlib import Path

import r2_blre
import r3_apre
import r4_ceoc
import r5_crsi as r5


R4_ID = "zaije_r4_ceoc_20260712_v1"


def text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def main() -> int:
    project = Path(__file__).resolve().parents[1]
    workspace = project.parent
    root = project / "experiments" / r5.EXPERIMENT_ID
    r4root = project / "experiments" / R4_ID
    source = workspace / "handoff-hanyang" / "수주제안" / "자이제_1.xlsx"
    legacy = workspace / "legacy" / "자이제_1.xlsx"
    root.mkdir(parents=True, exist_ok=True)

    _, requested_rows = r2_blre.read_xlsx_raw(source)
    _, legacy_rows = r2_blre.read_xlsx_raw(legacy)
    requested_logical = [(r["excel_row"], r["text_for_llm_human"]) for r in requested_rows]
    legacy_logical = [(r["excel_row"], r["text_for_llm_human"]) for r in legacy_rows]
    logical_equal = requested_logical == legacy_logical
    if not logical_equal:
        raise RuntimeError("The user-specified workbook is not logically identical to the R4 source")

    corpus = r5.read_jsonl(project / "data" / "canonical" / "corpus.jsonl")
    raw_by_row = {r["excel_row"]: r["text_for_llm_human"] for r in requested_rows}
    source_sha = r5.file_sha(source)
    enriched = [{**row, "raw_text": raw_by_row[row["excel_row"]], "source_binary_sha256": source_sha,
                 "source_file": str(source.relative_to(workspace))} for row in corpus]

    r4_status = r5.read_json(r4root / "reference" / "status.json")
    if r4_status["overall_status"] != "DETERMINISTIC_CORE_ONLY_PASS" or r4_status["canonical_graph_system"] != "R4-B1":
        raise RuntimeError("R4 canonical input is not in the required state")
    old_dev = r5.read_json(r4root / "locks" / "exposure_registry.json")
    old_confirm = r5.read_json(r4root / "locks" / "confirmatory_membership_lock.json")
    exposed_ids = set(old_dev["evidence_ids"]) | set(old_confirm["evidence_ids"])
    exposed_groups = set(old_dev["leakage_group_ids"]) | set(old_confirm["leakage_group_ids"])
    fresh = [r for r in enriched if r["split"] == "VALIDATION" and r["evidence_id"] not in exposed_ids and r["leakage_group_id"] not in exposed_groups]
    fresh.sort(key=lambda r: r["excel_row"])
    if not fresh:
        raise RuntimeError("No fresh VALIDATION group remains")

    confirm_path = root / "data" / "confirmatory" / "validation_fresh_all.jsonl"
    r5.write_jsonl(confirm_path, fresh)
    fresh_anchors = [r3_apre.build_atomic_anchors(r) for r in fresh]
    r5.write_jsonl(root / "data" / "confirmatory" / "anchors.jsonl", fresh_anchors)

    # DEV is the already exposed R4 development set. Track P uses the locked R4 canonical graph.
    dev = r5.read_jsonl(r4root / "data" / "dev_exposed" / "dev_120.jsonl")
    dev = [{**row, "source_binary_sha256": source_sha, "source_file": str(source.relative_to(workspace))} for row in dev]
    r5.write_jsonl(root / "data" / "dev" / "dev_120_exposed.jsonl", dev)
    shutil.copy2(r4root / "data" / "dev_exposed" / "anchors.jsonl", root / "data" / "dev" / "anchors.jsonl")

    input_files = [
        r4root / "runs" / "b1_deterministic" / "nodes.jsonl",
        r4root / "runs" / "b1_deterministic" / "edges.jsonl",
        r4root / "graphs" / "rdf" / "ceoc_core.ttl",
        source,
    ]
    r5.write_json(root / "locks" / "input_audit.json", {
        "experiment_id": r5.EXPERIMENT_ID,
        "requested_source": str(source), "requested_source_binary_sha256": source_sha,
        "r4_source": str(legacy), "r4_source_binary_sha256": r5.file_sha(legacy),
        "logical_records": len(requested_rows), "logical_content_equal": logical_equal,
        "logical_content_sha256": r5.sha256_bytes(json.dumps(requested_logical, ensure_ascii=False, separators=(",", ":")).encode()),
        "r4_status": r4_status, "locked_input_hashes": {str(p.relative_to(workspace)): r5.file_sha(p) for p in input_files},
        "test_access": 0,
    })
    r5.write_json(root / "locks" / "exposure_registry.json", {
        "prior_exposed_evidence_count": len(exposed_ids), "prior_exposed_group_count": len(exposed_groups),
        "prior_exposed_evidence_ids": sorted(exposed_ids), "prior_exposed_group_ids": sorted(exposed_groups),
        "sources": {"R1_R3_DEV": old_dev["evidence_count"], "R4_CONFIRMATORY_NOW_EXPOSED": old_confirm["count"]},
        "test_access": 0,
    })
    r5.write_json(root / "locks" / "confirmatory_membership_lock.json", {
        "experiment_id": r5.EXPERIMENT_ID, "source_split": "VALIDATION", "target_count": 80,
        "actual_count": len(fresh), "actual_group_count": len({r['leakage_group_id'] for r in fresh}),
        "membership_sha256": r5.file_sha(confirm_path), "evidence_ids": [r["evidence_id"] for r in fresh],
        "leakage_group_ids": sorted({r["leakage_group_id"] for r in fresh}),
        "prior_evidence_overlap": len({r['evidence_id'] for r in fresh} & exposed_ids),
        "prior_group_overlap": len({r['leakage_group_id'] for r in fresh} & exposed_groups),
        "test_membership_count": 0, "prior_api_exposure": 0, "membership_change_allowed": False,
        "block_types": dict(Counter(r.get("block_type") for r in fresh)),
    })
    r5.write_json(root / "amendments" / "confirmatory_shortfall_pre_api.json", {
        "timing": "PRE_API", "reason": "Only eight Evidence bundles in seven previously unexposed VALIDATION leakage groups remain after R1-R4 exposure exclusion.",
        "target_evidence": 80, "available_evidence": len(fresh), "shortfall": 80 - len(fresh),
        "action": "Include every remaining fresh VALIDATION leakage group; do not substitute INDUCTION or TEST.",
        "claim_limit": "Confirmatory estimates are exploratory-small-n and cannot support precise population performance claims.",
    })

    registry = """relations:
  - HAS_DEFINITION
  - HAS_ALIAS
  - HAS_INPUT
  - PRODUCES_OUTPUT
  - PERFORMED_BY
  - PRECEDES
  - HAS_CONDITION
  - HAS_EXCEPTION
  - HAS_QUANTITY_CONSTRAINT
  - USES_TEMPLATE
  - HAS_FIELD
  - ILLUSTRATES
  - ADDRESSES_ISSUE
  - SUPPORTS_DECISION
  - PART_OF
  - BROADER
new_relation_policy: QUARANTINE_ONLY
"""
    text(root / "preregistration" / "relation_registry.yaml", registry)
    text(root / "preregistration" / "type_compatibility.yaml", """hard_incompatible:
  - [Actor, Artifact]
  - [Actor, InformationObject]
  - [WorkUnit, Metric]
  - [WorkUnit, Artifact]
  - [Template, TemplateField]
  - [ExampleInstance, DomainConcept]
  - [Organization, Actor]
hard_merge_only: true
soft_merge_direct_promotion: false
""")
    text(root / "preregistration" / "protocol.md", """# R5-CRSI-V frozen protocol

R4-B1 is the locked ontology-core input. R5-B0 keeps surface forms separate. R5-B1 performs only explicit-alias, normalized-exact-alias, type-safe relation-registry operations. R5-B2 sends the frozen 20% graph-impact subset of gray candidates to one pointwise closed-choice model. R5-B3 sends every gray candidate. R5-B4 is a direct-LLM baseline with the same Evidence and anchor identifiers. LLM outputs never bypass deterministic evidence, domain/range, hard-negative, taxonomy-cycle, or operational-promotion gates. TEST data and membership are prohibited.

The confirmatory target was 80 Evidence bundles. Only eight bundles in seven unexposed VALIDATION groups remained; all eight were locked before API use under the design's shortfall rule.
""")
    r5.write_json(root / "preregistration" / "system_freeze_draft.json", {
        "model": r5.MODEL, "temperature": 0, "budget_sweep": [0.10, 0.20, 0.40],
        "default_b2_budget_if_no_80pct_yield": 0.20, "repeat_fraction": 0.20,
        "pair_score": {"lexical": 0.30, "graph": 0.25, "definition": 0.20, "role": 0.15, "bilingual": 0.10},
        "merge_policy": "HARD_MERGE_OR_LLM_SAME_THEN_CONSTRAINT_GATE", "test_access": 0,
    })
    r5.write_json(root / "reference" / "status.json", {
        "experiment_id": r5.EXPERIMENT_ID, "phase": "R5_0_COMPLETE", "overall_status": "IN_PROGRESS",
        "confirmatory_actual_n": len(fresh), "confirmatory_target_n": 80, "test_access": 0,
    })
    print(json.dumps({"experiment": str(root), "fresh_validation": len(fresh), "fresh_groups": len({r['leakage_group_id'] for r in fresh}), "logical_source_equal": logical_equal}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
