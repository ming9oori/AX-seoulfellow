#!/usr/bin/env python3
"""Run frozen B0-B3 systems on confirmatory VALIDATION and evaluate them."""

from __future__ import annotations

import getpass
import hashlib
import json
import os
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import r2_api
import r3_batch_api
import r4_ceoc as r4


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_output(path: Path, manifest: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[str, int]]:
    output = {row["custom_id"]: row for row in r4.read_jsonl(path)}
    decisions = {}
    usage = Counter()
    for meta in manifest:
        item = output[meta["custom_id"]]
        if item.get("error") or item["response"]["status_code"] != 200:
            raise RuntimeError(f"Confirmatory request failed: {meta['custom_id']}")
        body = item["response"]["body"]
        parsed = json.loads(r2_api.extract_text(body))
        if parsed["candidate_id"] != meta["candidate_id"]:
            raise RuntimeError("Confirmatory candidate ID mismatch")
        if parsed["selected_option_id"] not in meta["option_ids"] + ["NONE"]:
            raise RuntimeError("Confirmatory free option generation")
        u = body.get("usage") or {}
        usage["input_tokens"] += int(u.get("input_tokens") or 0)
        usage["output_tokens"] += int(u.get("output_tokens") or 0)
        usage["cached_input_tokens"] += int((u.get("input_tokens_details") or {}).get("cached_tokens") or 0)
        decisions[meta["candidate_id"]] = {**parsed, "response_id": body.get("id")}
    return decisions, dict(usage)


def create_batch(
    *, candidates: list[dict[str, Any]], model: str, prompt: str, schema: dict[str, Any],
    run_dir: Path, phase: str,
) -> tuple[Path, list[dict[str, Any]]]:
    input_path = run_dir / "batch_input.jsonl"
    manifest_path = run_dir / "logical_request_manifest.jsonl"
    requests, manifest = [], []
    for index, item in enumerate(candidates, 1):
        custom_id = f"{phase}_{index:04d}"
        payload = {key: item[key] for key in ["candidate_id", "candidate_type", "source_text", "anchor_text", "operation", "option_ids", "registered_mention_ids", "cue_types"]}
        requests.append({
            "custom_id": custom_id, "method": "POST", "url": "/v1/responses",
            "body": {
                "model": model,
                "input": [
                    {"role": "system", "content": [{"type": "input_text", "text": prompt}]},
                    {"role": "user", "content": [{"type": "input_text", "text": r4.canonical(payload)}]},
                ],
                "text": {"format": {"type": "json_schema", "name": "r4_confirmatory_closed_choice_v1", "strict": True, "schema": schema}},
                "temperature": 0, "max_output_tokens": 350,
            },
        })
        manifest.append({
            "custom_id": custom_id, "candidate_id": item["candidate_id"], "candidate_type": item["candidate_type"],
            "option_ids": item["option_ids"], "anchor_id": item["anchor_id"], "evidence_id": item["evidence_id"],
            "leakage_group_id": item["leakage_group_id"], "selection_score": item["selection_score"],
        })
    r4.write_jsonl(input_path, requests); r4.write_jsonl(manifest_path, manifest)
    return input_path, manifest


def evaluate_cq(graph: dict[str, Any], cq_rows: list[dict[str, Any]]) -> dict[str, Any]:
    nodes = {item["id"]: item for item in graph["nodes"]}
    edges = graph["edges"]
    derived = defaultdict(list)
    for edge in edges:
        if edge["type"] == "DERIVED_FROM":
            derived[edge["source"]].append(edge["target"])
    type_map = {
        "EXPLICIT_DEFINITION": {"ExplicitDefinition"},
        "TEMPLATE_FIELD": {"TemplateField"},
        "QUANTITY_CONSTRAINT": {"QuantityConstraint"},
        "EXPLICIT_RULE": {"ExplicitDeonticRule"},
    }
    answers = []
    for cq in cq_rows:
        answer_rows = []
        if cq["type"] == "EXPLICIT_SEQUENCE":
            for edge in edges:
                if edge["type"] != "REL_PRECEDES":
                    continue
                evidence = sorted(set(derived[edge["source"]] + derived[edge["target"]]))
                answer_rows.append({"answer_node_ids": [edge["source"], edge["target"]], "graph_path": [edge["source"], edge["id"], edge["target"]], "evidence_anchor_ids": evidence})
        else:
            allowed = type_map.get(cq["type"], set())
            for node in nodes.values():
                if node["type"] not in allowed:
                    continue
                evidence = derived[node["id"]]
                answer_rows.append({"answer_node_ids": [node["id"]], "graph_path": [node["id"], *evidence[:1]], "evidence_anchor_ids": evidence})
        for answer in answer_rows:
            answer["exact_source_text"] = [nodes[item]["exact_text"] for item in answer["evidence_anchor_ids"] if item in nodes and nodes[item]["type"] == "Anchor"]
        answers.append({"cq_id": cq["cq_id"], "type": cq["type"], "answers": answer_rows[:100], "abstained": not bool(answer_rows)})
    answerability = sum(not item["abstained"] for item in answers) / len(answers)
    all_answers = [answer for item in answers for answer in item["answers"]]
    provenance_ok = [bool(answer["evidence_anchor_ids"]) and len(answer["exact_source_text"]) == len(answer["evidence_anchor_ids"]) for answer in all_answers]
    return {
        "answers": answers, "cq_evidence_answerability": answerability,
        "answer_provenance_precision": statistics.mean(provenance_ok) if provenance_ok else 1.0,
        "unsupported_answer_rate": 1 - statistics.mean(provenance_ok) if provenance_ok else 0.0,
    }


def ontology_yield(graph: dict[str, Any]) -> dict[str, int]:
    counts = Counter(node["type"] for node in graph["nodes"])
    return {
        "accepted_concepts": counts["Concept"], "accepted_aliases": counts["Alias"],
        "accepted_assertions": sum(counts[item] for item in ["ExplicitDefinition", "QuantityConstraint", "ExplicitCondition", "ExplicitException", "ExplicitProcessStep", "TemplateField"]),
        "accepted_rules": counts["ExplicitDeonticRule"], "accepted_llm_candidates": counts["SupportedCandidate"],
        "policy_compliant_graph_yield": sum(counts[item] for item in ["Concept", "Alias", "ExplicitDefinition", "QuantityConstraint", "ExplicitCondition", "ExplicitException", "ExplicitProcessStep", "TemplateField", "ExplicitDeonticRule", "ExampleInstance", "SupportedCandidate"]),
    }


def bootstrap(candidates: list[dict[str, Any]], b2_ids: set[str], b2: dict[str, dict[str, Any]], b3: dict[str, dict[str, Any]], iterations: int = 5000) -> dict[str, Any]:
    groups = defaultdict(list)
    for item in candidates:
        groups[item["leakage_group_id"]].append(item)
    group_ids = sorted(groups)
    rng = random.Random(20260712)
    differences = []
    for _ in range(iterations):
        sampled = [rng.choice(group_ids) for _ in group_ids]
        b2_count = b3_count = 0
        for group_id in sampled:
            for item in groups[group_id]:
                candidate_id = item["candidate_id"]
                b2_count += int(candidate_id in b2_ids and b2.get(candidate_id, {}).get("decision") == "SUPPORTED")
                b3_count += int(b3.get(candidate_id, {}).get("decision") == "SUPPORTED")
        differences.append(b2_count - b3_count)
    differences.sort()
    return {
        "cluster": "leakage_group_id", "groups": len(group_ids), "iterations": iterations,
        "b2_minus_b3_accepted_mean": statistics.mean(differences),
        "ci95": [differences[int(iterations * 0.025)], differences[min(iterations - 1, int(iterations * 0.975))]],
    }


def main() -> int:
    key = os.environ.get("OPENAI_API_KEY") or getpass.getpass("OpenAI API key: ")
    if not key:
        raise RuntimeError("OpenAI API key required")
    project = Path(__file__).resolve().parents[1]
    root = project / "experiments" / r4.EXPERIMENT_ID
    gate3 = read_json(root / "reports" / "gate_r4_3.json")
    freeze = read_json(root / "locks" / "system_freeze.json")
    if gate3["status"] != "PASS" or freeze["confirmatory_api_exposure_at_freeze"] != 0:
        raise RuntimeError("R4-3/freeze precondition failed")
    if r4.file_sha(project / "src" / "r4_ceoc.py") != freeze["candidate_generator_sha256"]:
        raise RuntimeError("Candidate generator changed after freeze")
    confirm_path = root / "data" / "confirmatory" / "validation_80.jsonl"
    if r4.file_sha(confirm_path) != freeze["confirmatory_membership_sha256"]:
        raise RuntimeError("Confirmatory membership changed")
    rows = r4.read_jsonl(confirm_path)
    anchors = r4.read_jsonl(root / "data" / "confirmatory" / "anchors.jsonl")
    membership = read_json(root / "locks" / "confirmatory_membership_lock.json")
    if len(rows) != 80 or membership["test_membership_count"] != 0 or membership["dev_group_overlap"] != 0:
        raise RuntimeError("Confirmatory leakage")

    b0 = r4.build_graph(rows, anchors, "R4-B0")
    b1 = r4.build_graph(rows, anchors, "R4-B1")
    candidates = r4.generate_gray_candidates(rows, anchors)
    b2_candidates = r4.select_gray_candidates(candidates, freeze["selected_b2_budget"])
    if len(candidates) != 146:
        raise RuntimeError(f"Unexpected confirmatory candidate count {len(candidates)}")
    r4.write_jsonl(root / "extraction" / "candidates" / "confirmatory_gray_candidates.jsonl", candidates)
    r4.write_jsonl(root / "extraction" / "candidates" / "confirmatory_b2_selected.jsonl", b2_candidates)

    prompt_path = root / "preregistration" / "prompts" / "closed_choice_v1.txt"
    schema_path = root / "preregistration" / "schemas" / "closed_choice_v1.json"
    if r4.file_sha(prompt_path) != freeze["prompt_sha256"] or r4.file_sha(schema_path) != freeze["schema_sha256"]:
        raise RuntimeError("Frozen prompt/schema changed")
    prompt, task_schema = prompt_path.read_text(encoding="utf-8"), read_json(schema_path)
    b2_dir = root / "runs" / "b2_selective_llm"
    b3_dir = root / "runs" / "b3_exhaustive_llm"
    b2_input, b2_manifest = create_batch(candidates=b2_candidates, model=freeze["model_snapshot"], prompt=prompt, schema=task_schema, run_dir=b2_dir, phase="b2")
    b3_input, b3_manifest = create_batch(candidates=candidates, model=freeze["model_snapshot"], prompt=prompt, schema=task_schema, run_dir=b3_dir, phase="b3")
    execution_lock = {
        "confirmatory_membership_sha256": r4.file_sha(confirm_path),
        "candidate_pool_sha256": r4.file_sha(root / "extraction" / "candidates" / "confirmatory_gray_candidates.jsonl"),
        "b2_selection_sha256": r4.file_sha(root / "extraction" / "candidates" / "confirmatory_b2_selected.jsonl"),
        "b2_batch_input_sha256": r4.file_sha(b2_input), "b3_batch_input_sha256": r4.file_sha(b3_input),
        "b2_requests": len(b2_candidates), "b3_requests": len(candidates), "test_access": 0,
    }
    r4.write_json(root / "locks" / "confirmatory_execution_lock.json", execution_lock)

    r3_batch_api.submit_and_wait(api_key=key, input_path=b2_input, run_dir=b2_dir, metadata={"experiment_id": r4.EXPERIMENT_ID, "phase": "confirmatory_b2"})
    b2_decisions, b2_usage = parse_output(b2_dir / "batch_output.jsonl", b2_manifest)
    r3_batch_api.submit_and_wait(api_key=key, input_path=b3_input, run_dir=b3_dir, metadata={"experiment_id": r4.EXPERIMENT_ID, "phase": "confirmatory_b3"})
    b3_decisions, b3_usage = parse_output(b3_dir / "batch_output.jsonl", b3_manifest)
    r4.write_jsonl(root / "extraction" / "selective_llm" / "confirmatory_b2_outputs.jsonl", [{"candidate_id": key_id, **value} for key_id, value in sorted(b2_decisions.items())])
    r4.write_jsonl(root / "extraction" / "selective_llm" / "confirmatory_b3_outputs.jsonl", [{"candidate_id": key_id, **value} for key_id, value in sorted(b3_decisions.items())])

    b2 = r4.extend_graph_with_llm(b1, b2_candidates, b2_decisions, "R4-B2")
    b3 = r4.extend_graph_with_llm(b1, candidates, b3_decisions, "R4-B3")
    graphs = {"R4-B0": b0, "R4-B1": b1, "R4-B2": b2, "R4-B3": b3}
    metrics, yields, cq_results = {}, {}, {}
    cq_rows = read_json(root / "preregistration" / "cq_split_lock.json")["confirmatory"]
    run_names = {"R4-B0": "b0_structure", "R4-B1": "b1_deterministic", "R4-B2": "b2_selective_llm", "R4-B3": "b3_exhaustive_llm"}
    for system, graph in graphs.items():
        run_dir = root / "runs" / run_names[system]
        r4.write_jsonl(run_dir / "nodes.jsonl", graph["nodes"])
        r4.write_jsonl(run_dir / "edges.jsonl", graph["edges"])
        metrics[system] = r4.validate_graph(graph, rows)
        yields[system] = ontology_yield(graph)
        cq_results[system] = evaluate_cq(graph, cq_rows)
        r4.write_json(run_dir / "metrics.json", metrics[system])
        r4.write_json(root / "evaluation" / "cq" / f"{run_names[system]}.json", cq_results[system])

    b2_tokens = b2_usage.get("input_tokens", 0) + b2_usage.get("output_tokens", 0)
    b3_tokens = b3_usage.get("input_tokens", 0) + b3_usage.get("output_tokens", 0)
    b2_gain = (yields["R4-B2"]["policy_compliant_graph_yield"] - yields["R4-B1"]["policy_compliant_graph_yield"]) / max(1, yields["R4-B1"]["policy_compliant_graph_yield"])
    yield_ratio = yields["R4-B2"]["policy_compliant_graph_yield"] / max(1, yields["R4-B3"]["policy_compliant_graph_yield"])
    token_ratio = b2_tokens / b3_tokens if b3_tokens else 0.0
    safety_pass = all(
        metrics[system]["critical_shacl_violation_count"] == 0
        and metrics[system]["provenance_completeness"] == 1.0
        and metrics[system]["example_to_rule_direct_promotion"] == 0
        for system in ["R4-B1", "R4-B2", "R4-B3"]
    )
    cq_pass = cq_results["R4-B1"]["cq_evidence_answerability"] >= 0.80 and cq_results["R4-B1"]["answer_provenance_precision"] == 1.0 and cq_results["R4-B1"]["unsupported_answer_rate"] == 0
    bootstrap_result = bootstrap(candidates, {item["candidate_id"] for item in b2_candidates}, b2_decisions, b3_decisions)
    r4.write_json(root / "evaluation" / "coverage" / "cluster_bootstrap.json", bootstrap_result)
    cost = {
        "R4-B0": {"requests": 0, "input_tokens": 0, "output_tokens": 0},
        "R4-B1": {"requests": 0, "input_tokens": 0, "output_tokens": 0},
        "R4-B2": {"requests": len(b2_candidates), **b2_usage},
        "R4-B3": {"requests": len(candidates), **b3_usage},
        "b2_token_ratio_to_b3": token_ratio,
    }
    r4.write_json(root / "cost" / "system" / "confirmatory_cost.json", cost)
    hypotheses = {
        "H4_A_conservative_safety": safety_pass,
        "H4_B_accepted_candidate_gain": b2_gain >= 0.15,
        "H4_C_cost_efficiency": token_ratio <= 0.35 and yield_ratio >= 0.85 and metrics["R4-B2"]["critical_shacl_violation_count"] <= metrics["R4-B3"]["critical_shacl_violation_count"],
        "H4_D_structural_usefulness": cq_pass,
        "H4_E_projection": "PENDING_R4_5",
    }
    result = {
        "status": "PASS" if safety_pass and cq_pass else "CONSERVATIVE_CORE_REVISE",
        "systems": {system: {"graph": {"nodes": len(graphs[system]["nodes"]), "edges": len(graphs[system]["edges"])}, "yield": yields[system], "critical_violations": metrics[system]["critical_shacl_violation_count"], "provenance_completeness": metrics[system]["provenance_completeness"], "cq_answerability": cq_results[system]["cq_evidence_answerability"]} for system in graphs},
        "b2_gain_over_b1": b2_gain, "b2_yield_ratio_to_b3": yield_ratio, "b2_token_ratio_to_b3": token_ratio,
        "hypotheses": hypotheses, "bootstrap": bootstrap_result, "cost": cost,
        "confirmatory_evidence_exposed": 80, "test_access": 0,
    }
    r4.write_json(root / "reports" / "gate_r4_4.json", result)
    lines = [
        "# R4 Confirmatory B0-B3 Report", "", f"- Gate R4-4: **{result['status']}**",
        "- Confirmatory VALIDATION Evidence: `80`", "- TEST access: `0`", "",
        "| Metric | B0 | B1 | B2 | B3 |", "|---|---:|---:|---:|---:|",
        f"| Nodes | {len(b0['nodes'])} | {len(b1['nodes'])} | {len(b2['nodes'])} | {len(b3['nodes'])} |",
        f"| Edges | {len(b0['edges'])} | {len(b1['edges'])} | {len(b2['edges'])} | {len(b3['edges'])} |",
        f"| Policy graph yield | {yields['R4-B0']['policy_compliant_graph_yield']} | {yields['R4-B1']['policy_compliant_graph_yield']} | {yields['R4-B2']['policy_compliant_graph_yield']} | {yields['R4-B3']['policy_compliant_graph_yield']} |",
        f"| Critical violations | {metrics['R4-B0']['critical_shacl_violation_count']} | {metrics['R4-B1']['critical_shacl_violation_count']} | {metrics['R4-B2']['critical_shacl_violation_count']} | {metrics['R4-B3']['critical_shacl_violation_count']} |",
        f"| CQ answerability | {cq_results['R4-B0']['cq_evidence_answerability']:.4f} | {cq_results['R4-B1']['cq_evidence_answerability']:.4f} | {cq_results['R4-B2']['cq_evidence_answerability']:.4f} | {cq_results['R4-B3']['cq_evidence_answerability']:.4f} |",
        f"| API requests | 0 | 0 | {len(b2_candidates)} | {len(candidates)} |",
        "", f"- B2 gain over B1: `{b2_gain:.4f}` (Gate >=0.15)",
        f"- B2 yield ratio to B3: `{yield_ratio:.4f}` (Gate >=0.85)",
        f"- B2 token ratio to B3: `{token_ratio:.4f}` (Gate <=0.35)",
    ]
    (root / "reports" / "confirmatory_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 4


if __name__ == "__main__":
    raise SystemExit(main())
