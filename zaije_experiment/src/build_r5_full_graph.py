#!/usr/bin/env python3
"""Rebuild the selected deterministic CRSI graph on all non-TEST data."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import r2_blre
import r3_apre
import r4_ceoc
import r5_crsi as r5


def main() -> int:
    project = Path(__file__).resolve().parents[1]
    workspace = project.parent
    root = project / "experiments" / r5.EXPERIMENT_ID
    freeze = r5.read_json(root / "locks" / "system_freeze.json")
    expected = freeze["file_hashes"]["src/r5_crsi.py"]
    if r5.file_sha(project / "src" / "r5_crsi.py") != expected:
        raise RuntimeError("Frozen R5 implementation hash changed")
    source = workspace / "handoff-hanyang" / "수주제안" / "자이제_1.xlsx"
    _, raw_rows = r2_blre.read_xlsx_raw(source)
    raw_by_row = {r["excel_row"]: r["text_for_llm_human"] for r in raw_rows}
    corpus = r5.read_jsonl(project / "data" / "canonical" / "corpus.jsonl")
    rows = [{**row, "raw_text": raw_by_row[row["excel_row"]], "source_binary_sha256": r5.file_sha(source),
             "source_file": str(source.relative_to(workspace))} for row in corpus if row["split"] in {"INDUCTION", "VALIDATION"}]
    if len(rows) != 953 or any(row["split"].startswith("TEST") for row in rows):
        raise RuntimeError("Unexpected full non-TEST membership")
    anchors = [r3_apre.build_atomic_anchors(row) for row in rows]
    r5.write_jsonl(root / "data" / "full_non_test" / "membership.jsonl", rows)
    r5.write_jsonl(root / "data" / "full_non_test" / "anchors.jsonl", anchors)
    r4graph = r4_ceoc.build_graph(rows, anchors, "R4-B1")
    for node in r4graph["nodes"]:
        if node["type"] == "Document":
            node["source_binary_sha256"] = rows[0]["source_binary_sha256"]
            node["source_file"] = rows[0]["source_file"]
    refs = r5.make_candidates(r4graph)
    graph = r5.build_graph(r4graph, "R5-B1")
    graph2 = r5.build_graph(r4graph, "R5-B1")
    stable = r5.sha256_bytes(json.dumps(graph, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()) == r5.sha256_bytes(json.dumps(graph2, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode())
    metrics = r5.evaluate_graph(graph, refs)
    metrics.update({"evidence_count": len(rows), "leakage_group_count": len({r['leakage_group_id'] for r in rows}),
                    "split_counts": dict(Counter(r["split"] for r in rows)), "rerun_stability": float(stable),
                    "test_access": 0, "performance_claim_use": False, "purpose": "FULL_NON_TEST_DEMONSTRATION_GRAPH"})
    out = root / "full_non_test" / "r5_b1"
    r5.write_jsonl(out / "nodes.jsonl", graph["nodes"])
    r5.write_jsonl(out / "edges.jsonl", graph["edges"])
    r5.write_json(out / "metrics.json", metrics)
    for key, records in refs.items():
        r5.write_jsonl(root / "reference" / "full_non_test" / f"{key}.jsonl", records)
    r5.write_json(root / "locks" / "full_non_test_build_lock.json", {
        "selected_system": "R5-B1", "reason": "B2 failed DEV token-efficiency gate and had no confirmatory gray candidates.",
        "membership_count": len(rows), "membership_sha256": r5.file_sha(root / "data" / "full_non_test" / "membership.jsonl"),
        "nodes_sha256": r5.file_sha(out / "nodes.jsonl"), "edges_sha256": r5.file_sha(out / "edges.jsonl"),
        "performance_claim_use": False, "test_access": 0,
    })
    print(json.dumps(metrics, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
