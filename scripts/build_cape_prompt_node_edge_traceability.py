#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build prompt/output and final KG node/edge traceability artifacts."""

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_OUTPUTS_DIR = Path("outputs")
DEFAULT_VALID_FILE = "49_qwen3_8b_strict_json_1200_full_valid.jsonl"
DEFAULT_VALID_FILES = [
    DEFAULT_VALID_FILE,
    "49_sac_kg_verifier_pruner_baseline_valid.jsonl",
]

CONDITION_METADATA = {
    "B0_plain_llm": {
        "family": "baseline",
        "prompt_file": "B0_plain_llm_triple_extraction.txt",
        "prompt_intent": "Schema 없이 subject-predicate-object triple을 직접 추출한다.",
        "output_keys": ["triples"],
    },
    "B1_predicate_constrained": {
        "family": "baseline",
        "prompt_file": "B1_predicate_constrained_llm.txt",
        "prompt_intent": "CAPE-KG 허용 predicate만 사용해 edge 후보를 추출한다.",
        "output_keys": ["edges"],
    },
    "B2_current_project": {
        "family": "baseline",
        "prompt_file": "B2_current_project_baseline.txt",
        "prompt_intent": "Task frame을 먼저 추론한 뒤 Layer 2 schema의 node/edge로 후처리한다.",
        "output_keys": ["nodes", "edges"],
    },
    "B3_edc_style": {
        "family": "baseline",
        "prompt_file": "B3_edc_style_baseline.txt",
        "prompt_intent": "Open-schema item을 추출, 정의, canonicalize한 뒤 CAPE-compatible node/edge로 변환한다.",
        "output_keys": ["nodes", "edges"],
    },
    "B4_taxonomy_rag": {
        "family": "baseline",
        "prompt_file": "B4_taxonomy_rag_baseline.txt",
        "prompt_intent": "NCS/PCF/task taxonomy snippet을 retrieval context로 제공하고 KG 후보와 mapping 후보를 추출한다.",
        "output_keys": ["nodes", "edges", "mappings"],
    },
    "B5_procedural_prompt": {
        "family": "baseline",
        "prompt_file": "B5_procedural_prompt_baseline.txt",
        "prompt_intent": "Action, actor, gateway, guard condition, artifact flow, dependency를 절차형으로 추출한다.",
        "output_keys": ["nodes", "edges"],
    },
    "B6_sac_kg_verifier_pruner": {
        "family": "baseline",
        "prompt_file": "B6_sac_kg_verifier_pruner_baseline.txt",
        "prompt_intent": "기존 generator 후보에 schema/evidence verifier와 pruning을 적용하는 SAC-KG-style approximation이다.",
        "output_keys": ["nodes", "edges"],
    },
    "P_cape_kg_actual": {
        "family": "proposed",
        "prompt_file": "P_cape_kg.txt",
        "prompt_intent": "CQ anchoring, evidence grounding, procedural schema, validator, NCS/PCF bridge를 결합한다.",
        "output_keys": ["nodes", "edges", "mappings"],
    },
    "P_minus_CQ": {
        "family": "ablation",
        "prompt_file": "",
        "prompt_intent": "제안 방법론에서 competency-question anchoring을 제거한다.",
        "output_keys": ["nodes", "edges", "mappings"],
    },
    "P_minus_Evidence": {
        "family": "ablation",
        "prompt_file": "",
        "prompt_intent": "제안 방법론에서 evidence anchor 요구를 약화한다.",
        "output_keys": ["nodes", "edges", "mappings"],
    },
    "P_minus_Procedural_schema": {
        "family": "ablation",
        "prompt_file": "",
        "prompt_intent": "절차형 schema 대신 flat non-procedural schema를 사용한다.",
        "output_keys": ["nodes", "edges", "mappings"],
    },
    "P_minus_Validator": {
        "family": "ablation",
        "prompt_file": "",
        "prompt_intent": "Post-hoc validator rejection 없이 모델의 schema 선택을 더 허용한다.",
        "output_keys": ["nodes", "edges", "mappings"],
    },
    "P_minus_Standard_bridge": {
        "family": "ablation",
        "prompt_file": "",
        "prompt_intent": "NCS/PCF taxonomy bridge 출력을 제거한다.",
        "output_keys": ["nodes", "edges"],
    },
    "P_minus_Schema_retrieval": {
        "family": "ablation",
        "prompt_file": "P_minus_Schema_retrieval.txt",
        "prompt_intent": "Chunk-specific CQ/schema/taxonomy retrieval을 제거하고 full schema 목록만 사용한다.",
        "output_keys": ["nodes", "edges", "mappings"],
    },
}

FINAL_NODE_GENERATION = {
    "DomainTask": "TASK_SEEDS의 label/alias/keyword로 OCR sentence evidence를 검색해 생성",
    "ProcedureStep": "task별 procedure template 또는 입력/산출물 기반 step 추론으로 생성",
    "ReviewCheckpoint": "검토/리뷰/점검/승인/확인 신호가 있는 ProcedureStep에서 별도 checkpoint node로 투영",
    "Artifact": "task evidence 안의 입력물/산출물 용어 매칭으로 생성",
    "Role": "수행자/책임 주체 용어 매칭으로 생성",
    "DecisionGateway": "의사결정 관련 용어 매칭으로 생성",
    "GuardCondition": "의사결정 evidence에서 조건/가능성/경쟁/자원 등 조건 표현을 정규식으로 추출",
    "Principle": "원칙/품질 기준 용어 매칭으로 생성",
    "Risk": "위험/불리함/실패 가능성 용어 매칭으로 생성",
    "ArtifactFlow": "특정 산출물이 다음 task 입력으로 쓰이는 규칙에서 생성",
}

FINAL_EDGE_GENERATION = {
    "PRODUCES": "task/step의 outputs slot을 Artifact node로 연결",
    "USES_INPUT": "task/step의 inputs slot을 Artifact 또는 Concept node로 연결",
    "PERFORMED_BY": "task/step의 roles slot을 Role node로 연결",
    "HAS_STEP": "DomainTask를 해당 ProcedureStep 목록에 연결",
    "HAS_REVIEW_CHECKPOINT": "검토/리뷰/점검/승인/확인 신호가 있는 ProcedureStep을 ReviewCheckpoint node로 연결",
    "PRECEDES": "같은 task 안에서 step order 기준으로 순서 연결",
    "HAS_PRINCIPLE": "task/step의 principles slot을 Principle node로 연결",
    "HAS_DECISION_GATEWAY": "task/step에서 발견된 의사결정 node를 연결",
    "HAS_RISK": "task/step의 risks slot을 Risk node로 연결",
    "HAS_GUARD_CONDITION": "DecisionGateway에서 추출된 조건 node를 연결",
    "FEEDS_INTO": "Artifact가 다음 task로 흘러가는 규칙을 연결",
    "USED_AS_INPUT_FOR": "Artifact가 다음 task 입력으로 사용되는 규칙을 연결",
}

RUNTIME_PROMPT_CONSTRAINTS = [
    "Return ONLY one valid JSON object; no markdown and no explanation.",
    "Each item must use evidence_anchor_ids from the current chunk sentence_ids.",
    "Do not use outside knowledge.",
    "Keep Korean labels when the source text is Korean.",
    "Schema-constrained conditions receive allowed node types and allowed edge predicates.",
    "CAPE conditions impose hard limits of at most 5 nodes, 5 edges, and 3 mappings per chunk.",
    "Strict JSON runs prepend a JSON-only contract and /no_think instruction for Qwen-style chat models.",
]


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path):
    rows = []
    path = Path(path)
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def rel(path):
    return str(Path(path).as_posix())


def file_state(path):
    path = Path(path)
    return {
        "path": rel(path),
        "exists": path.exists(),
        "bytes": path.stat().st_size if path.exists() else 0,
    }


def prompt_inventory(exp_dir):
    prompt_dir = Path(exp_dir) / "02_schema/prompts"
    rows = []
    for condition, meta in CONDITION_METADATA.items():
        prompt_file = meta.get("prompt_file") or ""
        prompt_path = prompt_dir / prompt_file if prompt_file else None
        prompt_text = ""
        if prompt_path and prompt_path.exists():
            prompt_text = prompt_path.read_text(encoding="utf-8").strip()
        rows.append(
            {
                "condition": condition,
                "family": meta["family"],
                "prompt_file": rel(prompt_path) if prompt_path else "",
                "prompt_file_exists": bool(prompt_path and prompt_path.exists()),
                "prompt_text": prompt_text,
                "prompt_intent": meta["prompt_intent"],
                "expected_output_keys": meta["output_keys"],
            }
        )
    return rows


def resolve_valid_paths(exp_dir, valid_files):
    paths = []
    for valid_file in valid_files:
        path = Path(valid_file)
        if not path.is_absolute():
            path = Path(exp_dir) / path
        paths.append(path)
    return paths


def summarize_condition_outputs(valid_files):
    rows = []
    by_condition = defaultdict(lambda: {"valid_rows": 0, "triples": 0, "nodes": 0, "edges": 0, "mappings": 0})
    source_files_by_condition = defaultdict(set)
    for valid_file in valid_files:
        file_rows = read_jsonl(valid_file)
        rows.extend(file_rows)
        for row in file_rows:
            condition = row.get("condition") or "UNKNOWN"
            source_files_by_condition[condition].add(rel(valid_file))
            by_condition[condition]["valid_rows"] += 1
            for key in ["triples", "nodes", "edges", "mappings"]:
                value = row.get(key)
                if isinstance(value, list):
                    by_condition[condition][key] += len(value)
    summaries = []
    for condition in sorted(by_condition):
        meta = CONDITION_METADATA.get(condition, {})
        summary = {
            "condition": condition,
            "family": meta.get("family", "unknown"),
            "expected_output_keys": meta.get("output_keys", []),
            "source_files": sorted(source_files_by_condition[condition]),
            **by_condition[condition],
        }
        summaries.append(summary)
    return {
        "valid_file": rel(valid_files[0]) if valid_files else "",
        "valid_files": [rel(path) for path in valid_files],
        "valid_file_state": file_state(valid_files[0]) if valid_files else {},
        "valid_file_states": [file_state(path) for path in valid_files],
        "total_rows": len(rows),
        "conditions": summaries,
    }


def summarize_final_kg(outputs_dir):
    outputs_dir = Path(outputs_dir)
    nodes = read_jsonl(outputs_dir / "07_layer2_graph/layer2_nodes.jsonl")
    edges = read_jsonl(outputs_dir / "07_layer2_graph/layer2_edges.jsonl")
    triples = read_jsonl(outputs_dir / "06_triples/layer2_triples_schema_valid.jsonl")
    procedures = read_jsonl(outputs_dir / "05_procedure/procedure_structures_clean.jsonl")
    tasks = read_json(outputs_dir / "04_task_frames/canonical_task_catalog.json", {}) or {}

    node_type_counts = Counter(row.get("type") for row in nodes)
    edge_predicate_counts = Counter(row.get("predicate") for row in edges)
    node_ids = {row.get("node_id") for row in nodes}
    dangling_edges = [
        row
        for row in edges
        if row.get("source_id") not in node_ids or row.get("target_id") not in node_ids
    ]
    task_rows = tasks.get("tasks") or []

    return {
        "source_files": {
            "canonical_task_catalog": rel(outputs_dir / "04_task_frames/canonical_task_catalog.json"),
            "procedure_structures_clean": rel(outputs_dir / "05_procedure/procedure_structures_clean.jsonl"),
            "layer2_triples_schema_valid": rel(outputs_dir / "06_triples/layer2_triples_schema_valid.jsonl"),
            "layer2_nodes": rel(outputs_dir / "07_layer2_graph/layer2_nodes.jsonl"),
            "layer2_edges": rel(outputs_dir / "07_layer2_graph/layer2_edges.jsonl"),
        },
        "counts": {
            "canonical_tasks": len(task_rows),
            "procedure_structures": len(procedures),
            "procedure_steps_total": sum(len(row.get("steps") or []) for row in procedures),
            "schema_valid_triples": len(triples),
            "final_nodes": len(nodes),
            "final_edges": len(edges),
            "nodes_with_evidence": sum(1 for row in nodes if row.get("evidence_anchor_ids")),
            "edges_with_evidence": sum(1 for row in edges if row.get("evidence_anchor_ids")),
            "edges_with_source_triple_ids": sum(1 for row in edges if row.get("source_triple_ids")),
            "dangling_edges": len(dangling_edges),
        },
        "node_type_counts": dict(node_type_counts.most_common()),
        "edge_predicate_counts": dict(edge_predicate_counts.most_common()),
        "node_generation_rules": FINAL_NODE_GENERATION,
        "edge_generation_rules": FINAL_EDGE_GENERATION,
    }


def collect_competency_questions(exp_dir, outputs_dir):
    exp_dir = Path(exp_dir)
    outputs_dir = Path(outputs_dir)
    experiment_cqs = read_json(exp_dir / "02_schema/competency_questions.json", []) or []
    build_cqs = read_json(outputs_dir / "03_schema/competency_questions.json", []) or []
    return {
        "generation_method": [
            "CQ는 LLM이 자동 생성한 것이 아니라 연구자가 정의한 KG 요구사항입니다.",
            "수주/제안 업무 절차를 task, step, input, output, role, decision, guard, artifact flow, evidence, NCS/PCF mapping 질문으로 분해했습니다.",
            "각 CQ를 target predicate 또는 required KG element에 연결해 schema, LLM prompt, validation, CQ answerability evaluation에 재사용했습니다.",
        ],
        "source_files": {
            "experiment_cq_file": rel(exp_dir / "02_schema/competency_questions.json"),
            "build_cq_file": rel(outputs_dir / "03_schema/competency_questions.json"),
            "build_schema_code": "scripts/build_ax_epak_internal_kg.py",
            "experiment_schema_code": "scripts/build_cape_kg_eacl_experiment.py",
            "runtime_prompt_code": "scripts/run_cape_llm_condition_baselines.py",
        },
        "experiment_cqs": experiment_cqs,
        "build_cqs": build_cqs,
    }


def md_table(headers, rows):
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        values = []
        for header in headers:
            value = row.get(header, "")
            if isinstance(value, list):
                value = ", ".join(f"`{item}`" for item in value)
            elif isinstance(value, bool):
                value = "yes" if value else "no"
            values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def render_report(payload):
    kg = payload["final_kg"]
    counts = kg["counts"]
    prompt_rows = []
    for row in payload["prompt_inventory"]:
        prompt_rows.append(
            {
                "condition": row["condition"],
                "family": row["family"],
                "prompt_file": f"`{row['prompt_file']}`" if row["prompt_file"] else "runtime condition only",
                "output": row["expected_output_keys"],
                "intent": row["prompt_intent"],
            }
        )

    output_rows = []
    for row in payload["llm_condition_outputs"]["conditions"]:
        output_rows.append(
            {
                "condition": row["condition"],
                "valid_rows": row["valid_rows"],
                "triples": row["triples"],
                "nodes": row["nodes"],
                "edges": row["edges"],
                "mappings": row["mappings"],
            }
        )

    node_rows = []
    for node_type, count in kg["node_type_counts"].items():
        node_rows.append(
            {
                "node_type": node_type,
                "count": count,
                "generation_rule": kg["node_generation_rules"].get(node_type, ""),
            }
        )

    edge_rows = []
    for predicate, count in kg["edge_predicate_counts"].items():
        edge_rows.append(
            {
                "predicate": predicate,
                "count": count,
                "generation_rule": kg["edge_generation_rules"].get(predicate, ""),
            }
        )

    lines = [
        "# CAPE-KG Prompt, Node, and Edge Traceability",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Experiment: `{payload['experiment_dir']}`",
        f"Outputs: `{payload['outputs_dir']}`",
        "",
        "## 핵심 해석",
        "",
        "- 최종 Layer 2 KG는 LLM 출력물을 그대로 저장한 결과가 아니라, OCR evidence anchor, task seed, 용어 사전, 절차 템플릿, schema validator로 조립한 rule/schema/evidence 기반 graph입니다.",
        "- LLM 산출물은 baseline/proposed/ablation 조건별 prediction이며, 최종 성능 claim은 human-gold annotation 이후에만 가능합니다.",
        "- 이 문서는 어떤 프롬프트/조건이 어떤 JSON key를 산출했고, 최종 node/edge가 어떤 규칙으로 생성되었는지를 추적하기 위한 release artifact입니다.",
        "",
        "## Runtime Prompt 공통 제약",
        "",
    ]
    lines += [f"- {item}" for item in payload["runtime_prompt_constraints"]]
    lines += [
        "",
        "## 프롬프트/조건별 산출물 매핑",
        "",
        md_table(["condition", "family", "prompt_file", "output", "intent"], prompt_rows),
        "",
        "## 실제 프롬프트 파일 원문",
        "",
        "아래 원문은 `experiments/cape_kg_eacl_20260627/02_schema/prompts/`에 저장된 프롬프트 파일 내용입니다. 실제 LLM 호출 때는 이 조건별 원문에 runtime template, chunk sentence, sentence id, allowed schema, JSON shape가 결합됩니다.",
        "",
        md_table(
            ["condition", "prompt_file", "prompt_text"],
            [
                {
                    "condition": row["condition"],
                    "prompt_file": f"`{row['prompt_file']}`" if row["prompt_file"] else "runtime condition only",
                    "prompt_text": f"`{row['prompt_text']}`" if row["prompt_text"] else "",
                }
                for row in payload["prompt_inventory"]
            ],
        ),
        "",
        "## Competency Question 생성 방식과 예시",
        "",
    ]
    lines += [f"- {item}" for item in payload["competency_questions"]["generation_method"]]
    cq_rows = []
    for row in payload["competency_questions"]["experiment_cqs"]:
        cq_rows.append(
            {
                "cq_id": row.get("cq_id"),
                "question": row.get("question"),
                "target_predicates": row.get("target_predicates") or row.get("required_kg_elements") or [],
            }
        )
    lines += [
        "",
        "CQ source files:",
        "",
        f"- Experiment CQ: `{payload['competency_questions']['source_files']['experiment_cq_file']}`",
        f"- Internal build CQ: `{payload['competency_questions']['source_files']['build_cq_file']}`",
        f"- CQ/schema generation code: `{payload['competency_questions']['source_files']['build_schema_code']}`, `{payload['competency_questions']['source_files']['experiment_schema_code']}`",
        "",
        md_table(["cq_id", "question", "target_predicates"], cq_rows),
        "",
        "## LLM Validated Output 수량",
        "",
        "Source valid files:",
        "",
        "\n".join(f"- `{path}`" for path in payload["llm_condition_outputs"].get("valid_files") or [payload["llm_condition_outputs"].get("valid_file")]),
        "",
        md_table(["condition", "valid_rows", "triples", "nodes", "edges", "mappings"], output_rows),
        "",
        "## 최종 KG Node 생성 방식",
        "",
        f"- Final nodes: {counts['final_nodes']}",
        f"- Nodes with evidence: {counts['nodes_with_evidence']} / {counts['final_nodes']}",
        "",
        md_table(["node_type", "count", "generation_rule"], node_rows),
        "",
        "## 최종 KG Edge 생성 방식",
        "",
        f"- Final edges: {counts['final_edges']}",
        f"- Edges with evidence: {counts['edges_with_evidence']} / {counts['final_edges']}",
        f"- Edges with `source_triple_ids`: {counts['edges_with_source_triple_ids']} / {counts['final_edges']}",
        f"- Dangling edges: {counts['dangling_edges']}",
        "",
        md_table(["predicate", "count", "generation_rule"], edge_rows),
        "",
        "## 중간 산출물 연결",
        "",
        "| 단계 | 파일 | 현재 수량 |",
        "|---|---|---:|",
        f"| Task frame | `{kg['source_files']['canonical_task_catalog']}` | {counts['canonical_tasks']} |",
        f"| Procedure structure | `{kg['source_files']['procedure_structures_clean']}` | {counts['procedure_structures']} procedures / {counts['procedure_steps_total']} steps |",
        f"| Schema-valid triple | `{kg['source_files']['layer2_triples_schema_valid']}` | {counts['schema_valid_triples']} |",
        f"| Final nodes | `{kg['source_files']['layer2_nodes']}` | {counts['final_nodes']} |",
        f"| Final edges | `{kg['source_files']['layer2_edges']}` | {counts['final_edges']} |",
        "",
        "## 주의",
        "",
        "- 이 산출물은 재현성과 설명 가능성을 위한 traceability 문서입니다.",
        "- LLM output quantity는 성능 우수성을 뜻하지 않습니다.",
        "- Precision/recall/F1 main table은 adjudicated human-gold가 들어온 뒤 다시 계산해야 합니다.",
        "",
    ]
    return "\n".join(lines)


def build_payload(exp_dir, outputs_dir, valid_files):
    exp_dir = Path(exp_dir)
    outputs_dir = Path(outputs_dir)
    valid_paths = resolve_valid_paths(exp_dir, valid_files)
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": rel(exp_dir),
        "outputs_dir": rel(outputs_dir),
        "runtime_prompt_builder": "scripts/run_cape_llm_condition_baselines.py",
        "final_kg_builder": "scripts/build_ax_epak_internal_kg.py",
        "runtime_prompt_constraints": RUNTIME_PROMPT_CONSTRAINTS,
        "prompt_inventory": prompt_inventory(exp_dir),
        "competency_questions": collect_competency_questions(exp_dir, outputs_dir),
        "llm_condition_outputs": summarize_condition_outputs(valid_paths),
        "final_kg": summarize_final_kg(outputs_dir),
        "claim_status": "traceability_ready_not_human_gold_performance_evidence",
    }
    return payload


def run(args):
    valid_files = args.valid_files or list(DEFAULT_VALID_FILES)
    payload = build_payload(args.experiment_dir, args.outputs_dir, valid_files)
    release_dir = Path(args.experiment_dir) / "06_release"
    json_path = release_dir / "prompt_node_edge_traceability.json"
    md_path = release_dir / "prompt_node_edge_traceability.md"
    write_json(json_path, payload)
    write_text(md_path, render_report(payload))
    print(json.dumps({"json": rel(json_path), "markdown": rel(md_path), "claim_status": payload["claim_status"]}, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--outputs-dir", default=str(DEFAULT_OUTPUTS_DIR))
    parser.add_argument("--valid-file", dest="valid_files", action="append", help="Valid JSONL file to summarize. Can be repeated.")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
