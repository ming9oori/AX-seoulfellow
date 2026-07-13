#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a claim-safe experiment reproduction card for CAPE-KG."""

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_OUTPUTS_DIR = Path("outputs")
DEFAULT_PLAN_FILE = Path("AX_EACL_submission_review_revised_plan.md")
CLAIM_STATUS = "experiment_reproduction_card_ready_not_human_gold_claim"

CONDITION_ORDER = [
    "B0_plain_llm",
    "B1_predicate_constrained",
    "B2_current_project",
    "B3_edc_style",
    "B4_taxonomy_rag",
    "B5_procedural_prompt",
    "B6_sac_kg_verifier_pruner",
    "P_cape_kg_actual",
    "P_minus_CQ",
    "P_minus_Evidence",
    "P_minus_Procedural_schema",
    "P_minus_Schema_retrieval",
    "P_minus_Standard_bridge",
    "P_minus_Validator",
]

CONDITION_META = {
    "B0_plain_llm": {
        "family": "baseline",
        "output_keys": "triples",
        "prompt_file": "02_schema/prompts/B0_plain_llm_triple_extraction.txt",
        "reproduction_group": "qwen3_8b_initial_baselines",
        "method_role": "Plain LLM triple extraction without ontology schema.",
    },
    "B1_predicate_constrained": {
        "family": "baseline",
        "output_keys": "edges",
        "prompt_file": "02_schema/prompts/B1_predicate_constrained_llm.txt",
        "reproduction_group": "qwen3_8b_initial_baselines",
        "method_role": "Predicate-constrained extraction using CAPE-KG edge labels.",
    },
    "B2_current_project": {
        "family": "baseline",
        "output_keys": "nodes, edges",
        "prompt_file": "02_schema/prompts/B2_current_project_baseline.txt",
        "reproduction_group": "qwen3_8b_b2_b4_baselines",
        "method_role": "Task-frame baseline followed by Layer 2 schema post-processing.",
    },
    "B3_edc_style": {
        "family": "baseline",
        "output_keys": "nodes, edges",
        "prompt_file": "02_schema/prompts/B3_edc_style_baseline.txt",
        "reproduction_group": "qwen3_8b_edc_schema_ablation",
        "method_role": "Extract-define-canonicalize style open-schema baseline.",
    },
    "B4_taxonomy_rag": {
        "family": "baseline",
        "output_keys": "nodes, edges, mappings",
        "prompt_file": "02_schema/prompts/B4_taxonomy_rag_baseline.txt",
        "reproduction_group": "qwen3_8b_b2_b4_baselines",
        "method_role": "Taxonomy-RAG baseline with NCS/PCF snippets.",
    },
    "B5_procedural_prompt": {
        "family": "baseline",
        "output_keys": "nodes, edges",
        "prompt_file": "02_schema/prompts/B5_procedural_prompt_baseline.txt",
        "reproduction_group": "qwen3_8b_initial_baselines",
        "method_role": "Procedural prompt focused on action, gateway, condition, and artifact flow.",
    },
    "B6_sac_kg_verifier_pruner": {
        "family": "baseline",
        "output_keys": "nodes, edges, mappings",
        "prompt_file": "02_schema/prompts/B6_sac_kg_verifier_pruner_baseline.txt",
        "reproduction_group": "sac_kg_verifier_pruner",
        "method_role": "SAC-KG-style deterministic verifier/pruner approximation.",
    },
    "P_cape_kg_actual": {
        "family": "proposed",
        "output_keys": "nodes, edges, mappings",
        "prompt_file": "02_schema/prompts/P_cape_kg.txt",
        "reproduction_group": "qwen3_8b_cape_ablation",
        "method_role": "CAPE-KG proposed condition with CQ anchoring, grounding, validation, and bridge.",
    },
    "P_minus_CQ": {
        "family": "ablation",
        "output_keys": "nodes, edges, mappings",
        "prompt_file": "",
        "reproduction_group": "qwen3_8b_cape_ablation",
        "method_role": "Ablation removing competency-question anchoring.",
    },
    "P_minus_Evidence": {
        "family": "ablation",
        "output_keys": "nodes, edges, mappings",
        "prompt_file": "",
        "reproduction_group": "qwen3_8b_cape_ablation",
        "method_role": "Ablation weakening evidence-anchor requirements.",
    },
    "P_minus_Procedural_schema": {
        "family": "ablation",
        "output_keys": "nodes, edges, mappings",
        "prompt_file": "",
        "reproduction_group": "qwen3_8b_cape_ablation",
        "method_role": "Ablation replacing procedural schema with flatter schema.",
    },
    "P_minus_Schema_retrieval": {
        "family": "ablation",
        "output_keys": "nodes, edges, mappings",
        "prompt_file": "02_schema/prompts/P_minus_Schema_retrieval.txt",
        "reproduction_group": "qwen3_8b_edc_schema_ablation",
        "method_role": "Ablation removing chunk-specific schema/taxonomy retrieval.",
    },
    "P_minus_Standard_bridge": {
        "family": "ablation",
        "output_keys": "nodes, edges",
        "prompt_file": "",
        "reproduction_group": "qwen3_8b_cape_ablation",
        "method_role": "Ablation removing NCS/PCF standard bridge outputs.",
    },
    "P_minus_Validator": {
        "family": "ablation",
        "output_keys": "nodes, edges, mappings",
        "prompt_file": "",
        "reproduction_group": "qwen3_8b_cape_ablation",
        "method_role": "Ablation removing post-hoc validator rejection.",
    },
}

REPRODUCTION_COMMANDS = [
    {
        "group": "qwen3_8b_initial_baselines",
        "conditions": "B0_plain_llm,B1_predicate_constrained,B5_procedural_prompt",
        "command": (
            "LLM_PYTHON=python3 CUDA_VISIBLE_DEVICES=0 python3 "
            "scripts/run_cape_llm_condition_baselines.py "
            "--output-dir experiments/cape_kg_eacl_20260627 "
            "--chunk-file 01_data/evaluation_chunks.jsonl "
            "--conditions B0_plain_llm,B1_predicate_constrained,B5_procedural_prompt "
            "--kg-dir outputs --output-prefix qwen3_8b_condition_baselines_120 "
            "--max-chunks 120 --strict-json-contract --resume"
        ),
        "expected_valid_file": "experiments/cape_kg_eacl_20260627/49_qwen3_8b_condition_baselines_120_valid.jsonl",
    },
    {
        "group": "qwen3_8b_b2_b4_baselines",
        "conditions": "B2_current_project,B4_taxonomy_rag",
        "command": (
            "LLM_PYTHON=python3 CUDA_VISIBLE_DEVICES=0 python3 "
            "scripts/run_cape_llm_condition_baselines.py "
            "--output-dir experiments/cape_kg_eacl_20260627 "
            "--chunk-file 01_data/evaluation_chunks.jsonl "
            "--conditions B2_current_project,B4_taxonomy_rag "
            "--kg-dir outputs --output-prefix qwen3_8b_b2_b4_condition_baselines "
            "--max-chunks 120 --strict-json-contract --resume"
        ),
        "expected_valid_file": "experiments/cape_kg_eacl_20260627/49_qwen3_8b_b2_b4_condition_baselines_120_valid.jsonl",
    },
    {
        "group": "qwen3_8b_edc_schema_ablation",
        "conditions": "B3_edc_style,P_minus_Schema_retrieval",
        "command": (
            "LLM_PYTHON=python3 CUDA_VISIBLE_DEVICES=0 python3 "
            "scripts/run_cape_llm_condition_baselines.py "
            "--output-dir experiments/cape_kg_eacl_20260627 "
            "--chunk-file 01_data/evaluation_chunks.jsonl "
            "--conditions B3_edc_style,P_minus_Schema_retrieval "
            "--kg-dir outputs --output-prefix qwen3_8b_edc_schema_ablation "
            "--max-chunks 120 --strict-json-contract --resume"
        ),
        "expected_valid_file": "experiments/cape_kg_eacl_20260627/49_qwen3_8b_edc_schema_ablation_valid.jsonl",
    },
    {
        "group": "qwen3_8b_cape_ablation",
        "conditions": "P_cape_kg_actual,P_minus_CQ,P_minus_Evidence,P_minus_Procedural_schema,P_minus_Standard_bridge,P_minus_Validator",
        "command": (
            "LLM_PYTHON=python3 CUDA_VISIBLE_DEVICES=0 python3 "
            "scripts/run_cape_llm_condition_baselines.py "
            "--output-dir experiments/cape_kg_eacl_20260627 "
            "--chunk-file 01_data/evaluation_chunks.jsonl "
            "--conditions P_cape_kg_actual,P_minus_CQ,P_minus_Evidence,P_minus_Procedural_schema,P_minus_Standard_bridge,P_minus_Validator "
            "--kg-dir outputs --output-prefix qwen3_8b_cape_ablation "
            "--max-chunks 120 --strict-json-contract --resume"
        ),
        "expected_valid_file": "experiments/cape_kg_eacl_20260627/49_qwen3_8b_cape_ablation_120_valid.jsonl",
    },
    {
        "group": "sac_kg_verifier_pruner",
        "conditions": "B6_sac_kg_verifier_pruner",
        "command": (
            "python3 scripts/build_sac_kg_verifier_pruner_baseline.py "
            "--experiment-dir experiments/cape_kg_eacl_20260627 --outputs-dir outputs"
        ),
        "expected_valid_file": "experiments/cape_kg_eacl_20260627/49_sac_kg_verifier_pruner_baseline_valid.jsonl",
    },
    {
        "group": "silver_scoring",
        "conditions": "all conditions",
        "command": "python3 scripts/evaluate_actual_llm_silver.py --experiment-dir experiments/cape_kg_eacl_20260627",
        "expected_valid_file": "experiments/cape_kg_eacl_20260627/04_evaluation/actual_llm_silver_metrics.json",
    },
    {
        "group": "human_gold_refresh_after_returns",
        "conditions": "all conditions after human returns",
        "command": "PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=1 bash scripts/run_cape_post_annotation_refresh.sh",
        "expected_valid_file": "experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_metrics.json",
    },
]


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path, rows, fieldnames):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def rel(path):
    return str(Path(path).as_posix())


def file_state(path, role):
    path = Path(path)
    exists = path.exists() and path.is_file()
    return {
        "role": role,
        "path": rel(path),
        "exists": exists,
        "bytes": path.stat().st_size if exists else 0,
    }


def prompt_text(exp_dir, prompt_rel):
    if not prompt_rel:
        return ""
    path = Path(exp_dir) / prompt_rel
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def metric_map(exp_dir):
    payload = read_json(Path(exp_dir) / "04_evaluation/actual_llm_silver_metrics.json", {}) or {}
    return {row.get("condition"): row for row in payload.get("metrics", []) if row.get("condition")}


def command_rows(exp_dir):
    rows = []
    for row in REPRODUCTION_COMMANDS:
        path = Path(row["expected_valid_file"])
        rows.append(
            {
                **row,
                "exists": path.exists() and path.is_file(),
                "bytes": path.stat().st_size if path.exists() and path.is_file() else 0,
                "paper_claim_scope": "reproduction or diagnostic only; not final human-gold performance",
            }
        )
    protocol = read_json(Path(exp_dir) / "06_release/evaluation_protocol_lock.json", {}) or {}
    for step, command in sorted((protocol.get("evaluation_commands") or {}).items()):
        rows.append(
            {
                "group": f"protocol_{step}",
                "conditions": "post-human or release protocol",
                "command": command,
                "expected_valid_file": "",
                "exists": True,
                "bytes": "",
                "paper_claim_scope": "locked protocol command",
            }
        )
    return rows


def condition_rows(exp_dir):
    metrics = metric_map(exp_dir)
    rows = []
    for condition in CONDITION_ORDER:
        meta = CONDITION_META[condition]
        metric = metrics.get(condition, {})
        source_file = metric.get("source_file") or ""
        source_path = Path(exp_dir) / source_file if source_file else Path("")
        rows.append(
            {
                "condition": condition,
                "family": meta["family"],
                "method_role": meta["method_role"],
                "output_keys": meta["output_keys"],
                "prompt_file": rel(Path(exp_dir) / meta["prompt_file"]) if meta["prompt_file"] else "runtime condition only",
                "prompt_text": prompt_text(exp_dir, meta["prompt_file"]),
                "reproduction_group": meta["reproduction_group"],
                "source_valid_file": rel(source_path) if source_file else "",
                "source_valid_file_exists": source_path.exists() and source_path.is_file() if source_file else False,
                "rows": metric.get("rows", 0),
                "chunks": metric.get("chunks", 0),
                "pred_nodes": metric.get("pred_nodes", 0),
                "pred_edges": metric.get("pred_edges", 0),
                "pred_triples": metric.get("pred_triples", 0),
                "pred_mappings": metric.get("pred_mappings", 0),
                "edge_exact_f1": metric.get("edge_exact_f1", ""),
                "predicate_f1": metric.get("predicate_f1", ""),
                "node_label_f1": metric.get("node_label_f1", ""),
                "evidence_f1": metric.get("evidence_f1", ""),
                "metric_claim_status": metric.get("claim_status", ""),
                "paper_claim_scope": "diagnostic/silver only until adjudicated human-gold scoring",
            }
        )
    return rows


def md_table(headers, rows):
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        values = []
        for header in headers:
            value = row.get(header, "")
            if isinstance(value, bool):
                value = str(value)
            values.append(str(value).replace("|", "\\|").replace("\n", " "))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def build_payload(exp_dir, outputs_dir, plan_file):
    exp_dir = Path(exp_dir)
    outputs_dir = Path(outputs_dir)
    release = exp_dir / "06_release"
    conditions = condition_rows(exp_dir)
    commands = command_rows(exp_dir)
    source_files = [
        file_state(plan_file, "revised_plan"),
        file_state(exp_dir / "01_data/evaluation_chunks.jsonl", "evaluation_chunks_private"),
        file_state(exp_dir / "04_evaluation/actual_llm_silver_metrics.json", "silver_metrics"),
        file_state(exp_dir / "06_release/evaluation_protocol_lock.json", "evaluation_protocol_lock"),
        file_state(exp_dir / "06_release/prompt_node_edge_traceability.json", "prompt_node_edge_traceability"),
        file_state(exp_dir / "06_release/qwen3_model_scaling_report.json", "qwen3_model_scaling"),
        file_state(exp_dir / "08_public_benchmarks/public_benchmark_crosscheck_summary.json", "public_benchmark_crosscheck"),
        file_state(outputs_dir / "07_layer2_graph/layer2_nodes.jsonl", "final_layer2_nodes"),
        file_state(outputs_dir / "07_layer2_graph/layer2_edges.jsonl", "final_layer2_edges"),
    ]
    source_files.extend(file_state(Path(row["expected_valid_file"]), f"reproduction_output:{row['group']}") for row in commands if row["expected_valid_file"])
    missing_source_files = [row["path"] for row in source_files if not row["exists"]]
    missing_condition_outputs = [row["condition"] for row in conditions if not row["source_valid_file_exists"]]
    rows_120 = sum(1 for row in conditions if int(row.get("rows") or 0) == 120)
    summary = {
        "claim_status": CLAIM_STATUS,
        "safe_to_use_as_submission": False,
        "submission_ready": False,
        "final_performance_claim_ready": False,
        "condition_count": len(conditions),
        "baseline_condition_count": sum(1 for row in conditions if row["family"] == "baseline"),
        "proposed_condition_count": sum(1 for row in conditions if row["family"] == "proposed"),
        "ablation_condition_count": sum(1 for row in conditions if row["family"] == "ablation"),
        "conditions_with_120_rows": rows_120,
        "command_group_count": len(commands),
        "missing_source_file_count": len(missing_source_files),
        "missing_condition_output_count": len(missing_condition_outputs),
    }
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": rel(exp_dir),
        "outputs_dir": rel(outputs_dir),
        "plan_file": rel(plan_file),
        "claim_status": CLAIM_STATUS,
        "summary": summary,
        "conditions": conditions,
        "reproduction_commands": commands,
        "source_files": source_files,
        "missing_source_files": missing_source_files,
        "missing_condition_outputs": missing_condition_outputs,
        "claim_gate_policy": [
            "The condition matrix documents executed or reproducible diagnostic runs, not final paper performance.",
            "Silver/proxy F1 values are allowed only for debugging and setup discussion.",
            "Main result tables require adjudicated human-gold labels, IAA, adjudication, and post-human scoring.",
            "Downstream mapping utility requires expert-reviewed NCS/PCF and crosswalk returns.",
        ],
        "outputs": {
            "json": rel(release / "experiment_reproduction_card.json"),
            "markdown": rel(release / "experiment_reproduction_card.md"),
            "csv": rel(release / "experiment_reproduction_conditions.csv"),
        },
    }


def render_markdown(payload):
    summary = payload["summary"]
    lines = [
        "# CAPE-KG Experiment Reproduction Card",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Experiment: `{payload['experiment_dir']}`",
        f"Plan: `{payload['plan_file']}`",
        "",
        "This card connects the revised EACL plan's baselines, ablations, outputs, commands, and claim gates. It is a reproduction map, not a final performance claim.",
        "",
        "## Summary",
        "",
        md_table(
            ["Item", "Value"],
            [
                {"Item": "Claim status", "Value": payload["claim_status"]},
                {"Item": "Safe to use as submission", "Value": summary["safe_to_use_as_submission"]},
                {"Item": "Submission ready", "Value": summary["submission_ready"]},
                {"Item": "Final performance claim ready", "Value": summary["final_performance_claim_ready"]},
                {"Item": "Conditions", "Value": summary["condition_count"]},
                {"Item": "Baselines", "Value": summary["baseline_condition_count"]},
                {"Item": "Proposed", "Value": summary["proposed_condition_count"]},
                {"Item": "Ablations", "Value": summary["ablation_condition_count"]},
                {"Item": "Conditions with 120 rows", "Value": summary["conditions_with_120_rows"]},
                {"Item": "Command groups", "Value": summary["command_group_count"]},
                {"Item": "Missing source files", "Value": summary["missing_source_file_count"]},
                {"Item": "Missing condition outputs", "Value": summary["missing_condition_output_count"]},
            ],
        ),
        "",
        "## Condition Matrix",
        "",
        md_table(
            [
                "condition",
                "family",
                "rows",
                "pred_nodes",
                "pred_edges",
                "pred_triples",
                "pred_mappings",
                "source_valid_file",
                "metric_claim_status",
            ],
            payload["conditions"],
        ),
        "",
        "## Reproduction Commands",
        "",
        md_table(
            ["group", "conditions", "command", "expected_valid_file", "exists", "paper_claim_scope"],
            payload["reproduction_commands"],
        ),
        "",
        "## Prompt and Output Mapping",
        "",
        md_table(
            ["condition", "output_keys", "prompt_file", "reproduction_group", "paper_claim_scope"],
            payload["conditions"],
        ),
        "",
        "## Claim Gate Policy",
        "",
    ]
    for item in payload["claim_gate_policy"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Source Files",
            "",
            md_table(["role", "exists", "bytes", "path"], payload["source_files"]),
            "",
            "## Interpretation",
            "",
            "- Use this file to explain exactly what was run for each baseline, proposed condition, and ablation.",
            "- Use the command groups as reproduction entry points; some commands require the project LLM environment and GPU access.",
            "- Do not use the silver/proxy metric values as final EACL main results.",
            "- After human returns are imported, run the post-annotation refresh wrapper and regenerate this card if condition outputs or claim gates change.",
            "",
        ]
    )
    return "\n".join(lines)


def run(args):
    payload = build_payload(Path(args.experiment_dir), Path(args.outputs_dir), Path(args.plan_file))
    outputs = payload["outputs"]
    write_json(outputs["json"], payload)
    write_csv(
        outputs["csv"],
        payload["conditions"],
        [
            "condition",
            "family",
            "method_role",
            "output_keys",
            "prompt_file",
            "reproduction_group",
            "source_valid_file",
            "source_valid_file_exists",
            "rows",
            "chunks",
            "pred_nodes",
            "pred_edges",
            "pred_triples",
            "pred_mappings",
            "edge_exact_f1",
            "predicate_f1",
            "node_label_f1",
            "evidence_f1",
            "metric_claim_status",
            "paper_claim_scope",
        ],
    )
    write_text(outputs["markdown"], render_markdown(payload))
    print(
        json.dumps(
            {
                "json": outputs["json"],
                "markdown": outputs["markdown"],
                "csv": outputs["csv"],
                "claim_status": payload["claim_status"],
                "condition_count": payload["summary"]["condition_count"],
                "missing_source_file_count": payload["summary"]["missing_source_file_count"],
                "missing_condition_output_count": payload["summary"]["missing_condition_output_count"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--outputs-dir", default=str(DEFAULT_OUTPUTS_DIR))
    parser.add_argument("--plan-file", default=str(DEFAULT_PLAN_FILE))
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
