#!/usr/bin/env python3
"""Run deterministic R5-B0/B1 and freeze DEV candidate inventories."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import r4_ceoc
import r5_crsi as r5


R4_ID = "zaije_r4_ceoc_20260712_v1"


def load_r4_graph(path: Path) -> dict:
    return {"system": "R4-B1", "nodes": r5.read_jsonl(path / "nodes.jsonl"), "edges": r5.read_jsonl(path / "edges.jsonl")}


def write_run(root: Path, split: str, graph: dict, refs: dict) -> dict:
    run = root / split / graph["system"].lower().replace("-", "_")
    r5.write_jsonl(run / "nodes.jsonl", graph["nodes"])
    r5.write_jsonl(run / "edges.jsonl", graph["edges"])
    metrics = r5.evaluate_graph(graph, refs)
    r5.write_json(run / "metrics.json", metrics)
    return metrics


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["dev", "confirmatory"], default="dev")
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[1]
    root = project / "experiments" / r5.EXPERIMENT_ID
    r4root = project / "experiments" / R4_ID

    if args.split == "dev":
        source = r4root / "runs" / "dev_b1"
        r4graph = load_r4_graph(source)
    else:
        rows = r5.read_jsonl(root / "data" / "confirmatory" / "validation_fresh_all.jsonl")
        anchors = r5.read_jsonl(root / "data" / "confirmatory" / "anchors.jsonl")
        r4graph = r4_ceoc.build_graph(rows, anchors, "R4-B1")
        for node in r4graph["nodes"]:
            if node["type"] == "Document":
                node["source_binary_sha256"] = rows[0]["source_binary_sha256"]
                node["source_file"] = rows[0]["source_file"]
        r5.write_jsonl(root / "data" / "confirmatory" / "r4_b1_nodes.jsonl", r4graph["nodes"])
        r5.write_jsonl(root / "data" / "confirmatory" / "r4_b1_edges.jsonl", r4graph["edges"])

    refs = r5.make_candidates(r4graph)
    ref_dir = root / "reference" / args.split
    for key, rows in refs.items():
        r5.write_jsonl(ref_dir / f"{key}.jsonl", rows)
    r5.write_json(ref_dir / "candidate_counts.json", {k: len(v) for k, v in refs.items()})

    b0 = r5.build_graph(r4graph, "R5-B0")
    b1 = r5.build_graph(r4graph, "R5-B1")
    b0m = write_run(root, args.split, b0, refs)
    b1m = write_run(root, args.split, b1, refs)

    # A second run must be byte-identical before the deterministic cluster gate passes.
    b1_repeat = r5.build_graph(r4graph, "R5-B1")
    stability = r5.sha256_bytes(json.dumps(b1, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()) == r5.sha256_bytes(json.dumps(b1_repeat, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode())
    r5.write_json(root / "evaluation" / args.split / "deterministic_gates.json", {
        "H5_A": {
            "explicit_alias_recall": b1m["explicit_alias_recall"], "explicit_alias_recall_pass": b1m["explicit_alias_recall"] >= .90,
            "hard_negative_merge_violation": b1m["hard_negative_merge_violation"], "hard_negative_pass": b1m["hard_negative_merge_violation"] == 0,
            "merge_provenance_completeness": b1m["merge_provenance_completeness"], "provenance_pass": b1m["merge_provenance_completeness"] == 1,
            "critical_shacl_violation": b1m["critical_shacl_violation"], "shacl_pass": b1m["critical_shacl_violation"] == 0,
            "cluster_rerun_stability": float(stability), "stability_pass": stability,
        },
        "H5_B": {
            "relation_evidence_coverage": b1m["relation_evidence_coverage"], "evidence_pass": b1m["relation_evidence_coverage"] == 1,
            "critical_domain_range_violation": b1m["critical_domain_range_violation"], "domain_range_pass": b1m["critical_domain_range_violation"] == 0,
            "orphan_promoted_relation": b1m["orphan_promoted_relation"], "orphan_pass": b1m["orphan_promoted_relation"] == 0,
            "taxonomy_cycle": b1m["taxonomy_cycle"], "taxonomy_pass": b1m["taxonomy_cycle"] == 0,
            "partonomy_taxonomy_conflation": b1m["partonomy_taxonomy_conflation"], "conflation_pass": b1m["partonomy_taxonomy_conflation"] == 0,
        },
        "b0": b0m, "b1": b1m,
    })
    if args.split == "dev":
        for fraction in (.10, .20, .40):
            selected = r5.select_budget(refs["gray"], fraction)
            r5.write_jsonl(root / "candidates" / "dev" / f"selected_{int(fraction*100):02d}pct.jsonl", selected)
        r5.write_json(root / "candidates" / "dev" / "budget_manifest.json", {
            "gray_count": len(refs["gray"]), "fractions": {str(f): len(r5.select_budget(refs["gray"], f)) for f in (.10, .20, .40)},
            "selection_function": "impact_desc_relation_quota_v1", "frozen_before_api": True,
        })
    print(json.dumps({"split": args.split, "candidate_counts": {k: len(v) for k, v in refs.items()}, "b0": b0m, "b1": b1m}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
