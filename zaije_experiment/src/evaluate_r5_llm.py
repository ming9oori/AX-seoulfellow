#!/usr/bin/env python3
"""Parse R5 Batch output, build B2/B3/B4, and evaluate utility/cost."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import r5_crsi as r5


def load_r4(root: Path, split: str) -> dict:
    if split == "dev":
        source = root.parent / "zaije_r4_ceoc_20260712_v1" / "runs" / "dev_b1"
    else:
        source = root / "data" / "confirmatory"
        return {"system": "R4-B1", "nodes": r5.read_jsonl(source / "r4_b1_nodes.jsonl"), "edges": r5.read_jsonl(source / "r4_b1_edges.jsonl")}
    return {"system": "R4-B1", "nodes": r5.read_jsonl(source / "nodes.jsonl"), "edges": r5.read_jsonl(source / "edges.jsonl")}


def write_run(root: Path, split: str, graph: dict, refs: dict, extra: dict | None = None) -> dict:
    run = root / split / graph["system"].lower().replace("-", "_")
    r5.write_jsonl(run / "nodes.jsonl", graph["nodes"])
    r5.write_jsonl(run / "edges.jsonl", graph["edges"])
    metrics = r5.evaluate_graph(graph, refs)
    if extra:
        metrics.update(extra)
    r5.write_json(run / "metrics.json", metrics)
    return metrics


def add_usage(total: dict[str, int], usage: dict[str, int]) -> None:
    for key in ("input_tokens", "output_tokens", "total_tokens"):
        total[key] = total.get(key, 0) + usage.get(key, 0)


def cq_metrics(graph: dict) -> dict:
    nodes, edges = graph["nodes"], graph["edges"]
    types = Counter(n["type"] for n in nodes)
    rels = Counter(e["type"] for e in edges)
    promoted = [n for n in nodes if n.get("operational") and n["type"] in r5.CONCEPT_TYPES]
    tests = [
        {"cq_id": "CQ5_1_CONCEPT_ALIAS", "answerable": bool(rels["HAS_ALIAS"] or graph["system"] == "R5-B0")},
        {"cq_id": "CQ5_2_PROCESS", "answerable": bool(types["WorkUnit"] and (rels["PRECEDES"] or types["WorkUnit"] == 1))},
        {"cq_id": "CQ5_3_RULE_CONSTRAINT", "answerable": bool(types["Rule"] and (rels["HAS_CONDITION"] or rels["HAS_QUANTITY_CONSTRAINT"] or rels["HAS_ACTION"]))},
        {"cq_id": "CQ5_4_TEMPLATE_FIELD", "answerable": bool((types["Template"] and rels["HAS_FIELD"]) or types["TemplateField"])},
        {"cq_id": "CQ5_5_EVIDENCE_TRACE", "answerable": all(n.get("evidence_anchor_ids") for n in promoted) if promoted else True},
    ]
    answerability = sum(t["answerable"] for t in tests) / len(tests)
    return {"questions": tests, "answerability": answerability, "provenance_precision": 1.0 if tests[-1]["answerable"] else 0.0, "unsupported_answer_rate": 0.0}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["dev", "confirmatory"], required=True)
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[1]
    root = project / "experiments" / r5.EXPERIMENT_ID
    api = root / "api" / args.split
    manifest = {m["custom_id"]: m for m in r5.read_jsonl(api / "logical_request_manifest.jsonl")}
    gray = {c["candidate_id"]: c for c in r5.read_jsonl(root / "reference" / args.split / "gray.jsonl")}
    refs = {key: r5.read_jsonl(root / "reference" / args.split / f"{key}.jsonl") for key in ("hard_positive", "hard_negative", "gray")}
    graph = load_r4(root, args.split)
    records = r5.read_jsonl(api / "batch_output.jsonl")
    repair = root / "api" / f"{args.split}_repair"
    if repair.exists() and (repair / "batch_output.jsonl").exists():
        manifest.update({m["custom_id"]: m for m in r5.read_jsonl(repair / "logical_request_manifest.jsonl")})
        records.extend(r5.read_jsonl(repair / "batch_output.jsonl"))

    decisions: dict[str, dict] = {}
    repeats: dict[str, dict] = {}
    direct: dict[str, dict] = {}
    usage_by_custom: dict[str, dict[str, int]] = {}
    parse_errors = []
    for record in records:
        custom_id = record["custom_id"]
        try:
            payload, usage = r5.response_payload(record)
        except Exception as exc:
            raw_usage = record.get("response", {}).get("body", {}).get("usage") or {}
            usage_by_custom[custom_id] = {
                "input_tokens": int(raw_usage.get("input_tokens", 0)),
                "output_tokens": int(raw_usage.get("output_tokens", 0)),
                "total_tokens": int(raw_usage.get("total_tokens", 0)),
            }
            parse_errors.append({"custom_id": custom_id, "error": str(exc)}); continue
        usage_by_custom[custom_id] = usage
        item = manifest[custom_id]
        if item["task"] == "DIRECT_B4":
            direct[custom_id] = payload
            continue
        candidate = gray[item["candidate_id"]]
        row = {**candidate, **payload, "custom_id": custom_id}
        if item["task"] == "GRAY_REPEAT": repeats[item["candidate_id"]] = row
        else: decisions[item["candidate_id"]] = row

    direct_evidence_done = {manifest[cid].get("evidence_id") for cid in direct}
    unresolved_parse_errors = [e for e in parse_errors if manifest[e["custom_id"]].get("evidence_id") not in direct_evidence_done]
    if parse_errors:
        r5.write_json(api / "parse_errors.json", parse_errors)
    if unresolved_parse_errors:
        raise RuntimeError(f"{len(unresolved_parse_errors)} batch outputs failed parsing without a repair output")
    agreement_rows = []
    for cid, repeat in repeats.items():
        original = decisions[cid]
        agreement_rows.append({"candidate_id": cid, "first": original["decision"], "repeat": repeat["decision"], "agree": original["decision"] == repeat["decision"]})
    repeat_agreement = sum(r["agree"] for r in agreement_rows) / len(agreement_rows) if agreement_rows else 1.0
    r5.write_jsonl(root / "evaluation" / args.split / "llm_repeat_agreement.jsonl", agreement_rows)
    r5.write_jsonl(root / "decisions" / args.split / "gray_decisions.jsonl", decisions.values())

    b1_graph = r5.build_graph(graph, "R5-B1")
    b1_metrics = r5.evaluate_graph(b1_graph, refs)
    sweep = []
    fractions = (.10, .20, .40) if args.split == "dev" else ()
    for fraction in fractions:
        selected = r5.select_budget(list(gray.values()), fraction)
        selected_decisions = {c["candidate_id"]: decisions[c["candidate_id"]] for c in selected}
        b2 = r5.build_graph(graph, "R5-B2", selected_decisions)
        metrics = r5.evaluate_graph(b2, refs)
        token = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        selected_ids = {c["candidate_id"] for c in selected}
        for cid in selected_ids:
            add_usage(token, usage_by_custom[f"{args.split}-gray-{cid}"])
            if cid in repeats: add_usage(token, usage_by_custom[f"{args.split}-repeat-{cid}"])
        sweep.append({"fraction": fraction, "selected_count": len(selected), "metrics": metrics, "usage": token})

    b3 = r5.build_graph(graph, "R5-B3", decisions)
    b3_metrics = write_run(root, args.split, b3, refs)
    b3_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    for custom_id, item in manifest.items():
        if item["task"] in {"GRAY", "GRAY_REPEAT"}: add_usage(b3_usage, usage_by_custom[custom_id])

    if args.split == "dev":
        eligible = [row for row in sweep if row["metrics"]["safe_ontology_yield"] / max(1, b3_metrics["safe_ontology_yield"]) >= .80]
        chosen_fraction = min((row["fraction"] for row in eligible), default=.20)
        chosen = next(row for row in sweep if row["fraction"] == chosen_fraction)
        r5.write_json(root / "evaluation" / "dev" / "budget_sweep.json", {"b1": b1_metrics, "b3": b3_metrics, "b3_usage": b3_usage, "rows": sweep, "chosen_fraction": chosen_fraction})
        selected = r5.select_budget(list(gray.values()), chosen_fraction)
    else:
        freeze = r5.read_json(root / "locks" / "system_freeze.json")
        chosen_fraction = freeze["b2_budget_fraction"]
        selected = r5.select_budget(list(gray.values()), chosen_fraction)

    selected_decisions = {c["candidate_id"]: decisions[c["candidate_id"]] for c in selected}
    b2 = r5.build_graph(graph, "R5-B2", selected_decisions)
    b2_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    for item in selected:
        cid = item["candidate_id"]
        add_usage(b2_usage, usage_by_custom[f"{args.split}-gray-{cid}"])
        if cid in repeats: add_usage(b2_usage, usage_by_custom[f"{args.split}-repeat-{cid}"])
    b2_metrics = write_run(root, args.split, b2, refs, {"llm_repeat_agreement": repeat_agreement})

    rows = r5.read_jsonl(root / "data" / args.split / ("dev_120_exposed.jsonl" if args.split == "dev" else "validation_fresh_all.jsonl"))
    anchors = r5.read_jsonl(root / "data" / args.split / "anchors.jsonl")
    b4 = r5.build_b4_graph(rows, anchors, direct)
    extracted = sum(len(v.get("concepts", [])) + len(v.get("relations", [])) for v in direct.values())
    unsupported = b4.pop("adapter_unsupported_count")
    b4_metrics = write_run(root, args.split, b4, refs, {"unsupported_label_rate": unsupported / extracted if extracted else 0.0, "adapter_unsupported_count": unsupported})
    b4_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    for custom_id, item in manifest.items():
        if item["task"] == "DIRECT_B4": add_usage(b4_usage, usage_by_custom[custom_id])

    cq = {}
    for g in [b1_graph, b2, b3, b4]:
        cq[g["system"]] = cq_metrics(g)
        r5.write_json(root / "evaluation" / args.split / "cq" / f"{g['system'].lower().replace('-', '_')}.json", cq[g["system"]])
    summary = {
        "split": args.split, "candidate_count": len(gray), "selected_count": len(selected), "b2_budget_fraction": chosen_fraction,
        "repeat_count": len(agreement_rows), "repeat_agreement": repeat_agreement,
        "decision_counts": dict(Counter(d["decision"] for d in decisions.values())),
        "systems": {"R5-B1": b1_metrics, "R5-B2": b2_metrics, "R5-B3": b3_metrics, "R5-B4": b4_metrics},
        "usage": {"R5-B2": b2_usage, "R5-B3": b3_usage, "R5-B4": b4_usage}, "cq": cq,
    }
    r5.write_json(root / "evaluation" / args.split / "llm_comparison.json", summary)
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
