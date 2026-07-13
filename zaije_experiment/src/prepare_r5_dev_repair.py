#!/usr/bin/env python3
"""Prepare the pre-freeze DEV repair for two truncated B4 responses."""

from __future__ import annotations

import json
from pathlib import Path

import r5_crsi as r5


def main() -> int:
    project = Path(__file__).resolve().parents[1]
    root = project / "experiments" / r5.EXPERIMENT_ID
    source = root / "api" / "dev"
    target = root / "api" / "dev_repair"
    affected = {"dev-direct-row-1046", "dev-direct-row-280"}
    requests = []
    manifest = []
    source_manifest = {m["custom_id"]: m for m in r5.read_jsonl(source / "logical_request_manifest.jsonl")}
    for request in r5.read_jsonl(source / "batch_input.jsonl"):
        if request["custom_id"] not in affected:
            continue
        old = request["custom_id"]
        request["custom_id"] = old + "-repair"
        request["body"]["max_output_tokens"] = 1800
        requests.append(request)
        manifest.append({**source_manifest[old], "custom_id": request["custom_id"], "repair_of": old})
    if len(requests) != 2:
        raise RuntimeError("Expected exactly two repair requests")
    r5.write_jsonl(target / "batch_input.jsonl", requests)
    r5.write_jsonl(target / "logical_request_manifest.jsonl", manifest)
    r5.write_json(target / "pre_freeze_amendment.json", {
        "timing": "DEV_PRE_SYSTEM_FREEZE", "reason": "Two direct-baseline responses reached max_output_tokens=800 and produced incomplete JSON.",
        "affected_custom_ids": sorted(affected), "change": "max_output_tokens 800 -> 1800 for affected requests only",
        "prompt_changed": False, "schema_changed": False, "candidate_system_changed": False,
        "batch_input_sha256": r5.file_sha(target / "batch_input.jsonl"), "key_stored": False,
    })
    print(json.dumps(r5.read_json(target / "pre_freeze_amendment.json"), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
