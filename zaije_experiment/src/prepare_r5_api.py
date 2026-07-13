#!/usr/bin/env python3
"""Create auditable Batch API inputs for R5 DEV or confirmatory phases."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import r5_crsi as r5


def load_r4(root: Path, split: str) -> dict:
    if split == "dev":
        source = root.parent / "zaije_r4_ceoc_20260712_v1" / "runs" / "dev_b1"
    else:
        source = root / "data" / "confirmatory"
        return {"system": "R4-B1", "nodes": r5.read_jsonl(source / "r4_b1_nodes.jsonl"), "edges": r5.read_jsonl(source / "r4_b1_edges.jsonl")}
    return {"system": "R4-B1", "nodes": r5.read_jsonl(source / "nodes.jsonl"), "edges": r5.read_jsonl(source / "edges.jsonl")}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["dev", "confirmatory"], required=True)
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[1]
    root = project / "experiments" / r5.EXPERIMENT_ID
    graph = load_r4(root, args.split)
    gray = r5.read_jsonl(root / "reference" / args.split / "gray.jsonl")
    rows = r5.read_jsonl(root / "data" / args.split / ("dev_120_exposed.jsonl" if args.split == "dev" else "validation_fresh_all.jsonl"))
    anchors = r5.read_jsonl(root / "data" / args.split / "anchors.jsonl")
    anchor_by_evidence = {a["evidence_id"]: a for a in anchors}

    requests = []
    manifest = []
    # B3 calls every gray candidate; repeat the highest-impact 20% under a distinct request ID.
    for item in gray:
        custom_id = f"{args.split}-gray-{item['candidate_id']}"
        requests.append(r5.make_pointwise_request(custom_id, item, graph))
        manifest.append({"custom_id": custom_id, "task": "GRAY", "candidate_id": item["candidate_id"], "repeat_of": None})
    repeat_count = math.ceil(len(gray) * .20) if gray else 0
    for item in sorted(gray, key=lambda x: (-x["impact_score"], x["candidate_id"]))[:repeat_count]:
        custom_id = f"{args.split}-repeat-{item['candidate_id']}"
        requests.append(r5.make_pointwise_request(custom_id, item, graph))
        manifest.append({"custom_id": custom_id, "task": "GRAY_REPEAT", "candidate_id": item["candidate_id"], "repeat_of": f"{args.split}-gray-{item['candidate_id']}"})

    # Direct-LLM baseline receives exactly the same Evidence and anchor context.
    for row in rows:
        custom_id = f"{args.split}-direct-row-{row['excel_row']}"
        requests.append(r5.make_direct_request(custom_id, row, anchor_by_evidence[row["evidence_id"]]))
        manifest.append({"custom_id": custom_id, "task": "DIRECT_B4", "evidence_id": row["evidence_id"], "repeat_of": None})

    run = root / "api" / args.split
    r5.write_jsonl(run / "batch_input.jsonl", requests)
    r5.write_jsonl(run / "logical_request_manifest.jsonl", manifest)
    r5.write_json(run / "input_lock.json", {
        "split": args.split, "model": r5.MODEL, "request_count": len(requests),
        "gray_count": len(gray), "repeat_count": repeat_count, "direct_evidence_count": len(rows),
        "batch_input_sha256": r5.file_sha(run / "batch_input.jsonl"), "manifest_sha256": r5.file_sha(run / "logical_request_manifest.jsonl"),
        "key_stored": False, "test_access": 0,
    })
    print(json.dumps(r5.read_json(run / "input_lock.json"), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
