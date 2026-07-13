#!/usr/bin/env python3
"""Create and lock the one allowed fresh INDUCTION re-pilot sample."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path


def load_phase0(path: Path):
    spec = importlib.util.spec_from_file_location("zaije_phase0", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    experiment = Path(__file__).resolve().parents[1]
    phase0 = load_phase0(experiment / "src" / "prepare_phase0.py")
    corpus = phase0.read_jsonl(experiment / "data" / "canonical" / "corpus.jsonl") if hasattr(phase0, "read_jsonl") else [json.loads(line) for line in (experiment / "data" / "canonical" / "corpus.jsonl").read_text(encoding="utf-8").splitlines() if line]
    assignment = {row["evidence_id"]: row["split"] for row in corpus}
    pilot_lock = json.loads((experiment / "annotation" / "pilot" / "pilot_lock.json").read_text(encoding="utf-8"))
    excluded = set(pilot_lock["evidence_ids"])
    candidates = [row for row in corpus if row["split"] == "INDUCTION" and row["evidence_id"] not in excluded]
    selected = phase0.select_diverse(candidates, 20, "ldr-fresh-repilot-v2")
    if set(row["evidence_id"] for row in selected) & excluded:
        raise RuntimeError("Re-pilot overlaps original PILOT")
    bundles = [phase0.context_bundle(row, corpus, assignment) for row in selected]
    out = experiment / "annotation" / "llm_reference" / "repilot_v2"
    out.mkdir(parents=True, exist_ok=True)
    bundle_path = out / "repilot_bundles.jsonl"
    phase0.write_jsonl(bundle_path, bundles)
    lock = {
        "version": "v2",
        "seed": phase0.SEED,
        "count": 20,
        "source_split": "INDUCTION",
        "original_pilot_overlap": 0,
        "test_membership": False,
        "evidence_ids": [row["evidence_id"] for row in selected],
        "bundle_sha256": hashlib.sha256(bundle_path.read_bytes()).hexdigest(),
        "policy": "One allowed fresh re-pilot after v1 Gate 1L failure; no further prompt revision.",
    }
    phase0.write_json(out / "repilot_lock.json", lock)
    print(json.dumps({"count": 20, "overlap": 0, "bundle_sha256": lock["bundle_sha256"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
