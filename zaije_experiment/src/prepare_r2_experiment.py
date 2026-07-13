#!/usr/bin/env python3
"""Lock R2 DEV, bake-off, fresh pilot, and deterministic candidate lattices."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import r2_blre as blre


EXPERIMENT_ID = "zaije_ldr_r2_20260712_blre_v1"


def main() -> int:
    experiment_root = Path(__file__).resolve().parents[1]
    workspace = experiment_root.parent
    run_root = experiment_root / "experiments" / EXPERIMENT_ID
    source = workspace / "legacy" / "자이제_1.xlsx"
    if hashlib.sha256(source.read_bytes()).hexdigest() != "9246a6da6c7635b3f34ee55df75112eb38a2984ea06828be943dc196de5926eb":
        raise RuntimeError("Input hash mismatch")
    sheet, raw_records = blre.read_xlsx_raw(source)
    if sheet != "clean_sentences" or len(raw_records) != 1366:
        raise RuntimeError(f"Unexpected input {sheet}/{len(raw_records)}")
    corpus = blre.read_jsonl(experiment_root / "data" / "canonical" / "corpus.jsonl")
    corpus_by_row = {row["excel_row"]: row for row in corpus}
    enriched = []
    for raw in raw_records:
        base = corpus_by_row[raw["excel_row"]]
        row = {**base, "raw_text": raw["text_for_llm_human"]}
        row["structure_type"] = blre.structure_type(row)
        row["r2_stratum"] = blre.r2_stratum(row)
        enriched.append(row)
    by_id = {row["evidence_id"]: row for row in enriched}

    prior_pilot = json.loads((experiment_root / "annotation" / "pilot" / "pilot_lock.json").read_text(encoding="utf-8"))["evidence_ids"]
    prior_repilot = json.loads((experiment_root / "annotation" / "llm_reference" / "repilot_v2" / "repilot_lock.json").read_text(encoding="utf-8"))["evidence_ids"]
    exposed_ids = set(prior_pilot) | set(prior_repilot)
    if len(exposed_ids) != 60:
        raise RuntimeError(f"Expected 60 exposed IDs, got {len(exposed_ids)}")
    exposed = [by_id[evidence_id] for evidence_id in sorted(exposed_ids)]

    gold_rows = list(csv.DictReader((experiment_root / "annotation" / "locks" / "gold_sampling_manifest.csv").open(encoding="utf-8")))
    locked_ids = {row["evidence_id"] for row in gold_rows}
    retired_induction_ids = {row["evidence_id"] for row in gold_rows if row["gold_role"] == "INDUCTION_GOLD"}
    excluded_ids = exposed_ids
    excluded_groups = {by_id[evidence_id]["leakage_group_id"] for evidence_id in excluded_ids}
    fresh_candidates = [row for row in enriched if row["split"] == "INDUCTION" and row["evidence_id"] not in excluded_ids and row["leakage_group_id"] not in excluded_groups]
    amended_quotas = [
        ("TABLE_TEMPLATE", 1), ("LIST_MULTILINE", 8), ("QUESTION_CAPTION_DISCOURSE", 4),
        ("NORMATIVE_DEONTIC", 5), ("CONDITIONAL_EXCEPTION", 10),
        ("DEFINITION_CAUSAL_EVALUATIVE", 14), ("NEGATION_QUANTITY_HIGH_RISK", 4),
        ("SIMPLE_GENERAL_PROSE", 14),
    ]
    fresh = blre.stratified_sample(fresh_candidates, amended_quotas, "r2-confirmatory-pilot-amended")
    fresh_ids = {row["evidence_id"] for row in fresh}
    fresh_groups = {row["leakage_group_id"] for row in fresh}
    if fresh_ids & excluded_ids or fresh_groups & excluded_groups:
        raise RuntimeError("Fresh pilot leakage")

    bakeoff_quotas = [
        ("TABLE_TEMPLATE", 4), ("LIST_MULTILINE", 4), ("QUESTION_CAPTION_DISCOURSE", 4),
        ("NORMATIVE_DEONTIC", 4), ("CONDITIONAL_EXCEPTION", 2),
        ("DEFINITION_CAUSAL_EVALUATIVE", 2), ("SIMPLE_GENERAL_PROSE", 4),
    ]
    bakeoff = blre.stratified_sample(exposed, bakeoff_quotas, "r2-model-bakeoff")

    data_dir = run_root / "data"
    blre.write_jsonl(data_dir / "dev_exposed_60.jsonl", exposed)
    blre.write_jsonl(data_dir / "model_bakeoff_24.jsonl", bakeoff)
    blre.write_jsonl(data_dir / "r2_pilot_60.jsonl", fresh)
    fresh_path = data_dir / "r2_pilot_60.jsonl"
    lock = {
        "experiment_id": EXPERIMENT_ID,
        "seed": blre.SEED,
        "count": len(fresh),
        "membership_sha256": hashlib.sha256(fresh_path.read_bytes()).hexdigest(),
        "evidence_ids": [row["evidence_id"] for row in fresh],
        "leakage_group_ids": sorted(fresh_groups),
        "exposed_60_evidence_overlap": len(fresh_ids & exposed_ids),
        "exposed_60_leakage_group_overlap": len(fresh_groups & excluded_groups),
        "retired_induction_membership_evidence_overlap": len(fresh_ids & retired_induction_ids),
        "test_reference_access": 0,
    }
    blre.write_json(data_dir / "r2_pilot_lock.json", lock)
    blre.write_json(data_dir / "inherited_gate0_manifest.json", {"gate0": "PASS", "split_manifest_sha256": (experiment_root / "data" / "manifests" / "split_manifest.sha256").read_text().split()[0], "counts": dict(Counter(row["split"] for row in enriched))})

    for name, rows in [("dev_exposed", exposed), ("model_bakeoff", bakeoff), ("r2_pilot", fresh)]:
        lattices = [blre.build_candidate_lattice(row) for row in rows]
        blre.write_jsonl(run_root / "candidates" / "lattice" / f"{name}.jsonl", lattices)
        blre.write_json(run_root / "candidates" / "validation" / f"{name}.json", blre.lattice_validation(lattices))

    audit = {
        "experiment_id": EXPERIMENT_ID,
        "raw_text_difference_from_phase0_view": sum(row["raw_text"] != row["text"] for row in enriched),
        "structure_counts": dict(Counter(row["structure_type"] for row in enriched)),
        "strata_counts": dict(Counter(row["r2_stratum"] for row in enriched)),
        "fresh_strata": dict(Counter(row["r2_stratum"] for row in fresh)),
        "bakeoff_strata": dict(Counter(row["r2_stratum"] for row in bakeoff)),
        "fresh_candidate_pool": len(fresh_candidates),
    }
    blre.write_json(run_root / "manifests" / "data_audit.json", audit)
    locked_paths = [data_dir / "dev_exposed_60.jsonl", data_dir / "model_bakeoff_24.jsonl", data_dir / "r2_pilot_60.jsonl", data_dir / "r2_pilot_lock.json", run_root / "preregistration" / "preregister.yaml", run_root / "preregistration" / "model_bakeoff_policy.yaml", run_root / "preregistration" / "gate_thresholds.yaml", run_root / "preregistration" / "sampling_amendment_pre_api.md"]
    blre.write_json(run_root / "manifests" / "pre_api_lock_hashes.json", {str(path.relative_to(run_root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in locked_paths})
    print(json.dumps({"experiment_id": EXPERIMENT_ID, "dev_exposed": len(exposed), "bakeoff": len(bakeoff), "fresh_pilot": len(fresh), "fresh_pool": len(fresh_candidates), "fresh_strata": audit["fresh_strata"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
