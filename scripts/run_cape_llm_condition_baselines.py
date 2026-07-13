#!/usr/bin/env python3
"""Run condition-specific LLM baseline prompts for the CAPE-KG EACL package."""

import argparse
import json
import os
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

try:
    from run_cep_onto_llm_extraction import (
        DEFAULT_MODEL,
        chunk_sentence_lines,
        clean_text,
        generate_json,
        load_model,
        parse_json_object,
        safe_slug,
    )
except ModuleNotFoundError as exc:
    if exc.name not in {"torch", "transformers"}:
        raise
    DEFAULT_MODEL = (
        "/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-8B/"
        "snapshots/b968826d9c46dd6066d109eabc6255188de91218"
    )

    def clean_text(text):
        import re

        text = "" if text is None else str(text)
        text = text.replace("\u00a0", " ")
        return re.sub(r"\s+", " ", text).strip()

    def safe_slug(value):
        import re

        value = clean_text(value)
        value = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")
        return value or "unknown_model"

    def chunk_sentence_lines(chunk):
        text = chunk.get("text", "")
        offsets = chunk.get("sentence_offsets", [])
        lines = []
        if offsets:
            for item in offsets:
                sent_id = item.get("sentence_id")
                start = item.get("chunk_char_start")
                end = item.get("chunk_char_end")
                if sent_id and isinstance(start, int) and isinstance(end, int):
                    sentence_text = clean_text(text[start:end])
                    if sentence_text:
                        lines.append(f"{sent_id}: {sentence_text}")
            if lines:
                return "\n".join(lines)
        sentence_ids = chunk.get("sentence_ids", [])
        if sentence_ids and clean_text(text):
            return f"{sentence_ids[0]}: {clean_text(text)}"
        return ""

    def parse_json_object(text):
        import re

        text = str(text or "").strip()
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
        try:
            return json.loads(text), None
        except json.JSONDecodeError:
            pass
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            candidate = text[start:end + 1]
            try:
                return json.loads(candidate), None
            except json.JSONDecodeError as parse_exc:
                return None, f"{type(parse_exc).__name__}: {parse_exc}"
        return None, "No JSON object found"

    def load_model(*_args, **_kwargs):
        raise RuntimeError("LLM generation requires torch/transformers. Use the project LLM virtualenv.")

    def generate_json(*_args, **_kwargs):
        raise RuntimeError("LLM generation requires torch/transformers. Use the project LLM virtualenv.")


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")

ALLOWED_NODE_TYPES = {
    "DomainTask",
    "ProcedureStep",
    "DecisionGateway",
    "GuardCondition",
    "Artifact",
    "ArtifactFlow",
    "Role",
    "ReviewCheckpoint",
    "Principle",
    "Risk",
}

ALLOWED_EDGE_TYPES = {
    "HAS_STEP",
    "PRECEDES",
    "BRANCHES_TO",
    "HAS_GUARD_CONDITION",
    "USES_INPUT",
    "PRODUCES",
    "FEEDS_INTO",
    "PERFORMED_BY",
    "HAS_DECISION_GATEWAY",
    "HAS_REVIEW_CHECKPOINT",
    "HAS_PRINCIPLE",
    "HAS_RISK",
    "USED_AS_INPUT_FOR",
}

CONDITIONS = {
    "B0_plain_llm": {
        "description": "Plain subject-predicate-object extraction without an ontology schema.",
        "keys": ["triples"],
    },
    "B1_predicate_constrained": {
        "description": "Predicate-constrained extraction using only CAPE-KG edge labels.",
        "keys": ["edges"],
    },
    "B2_current_project": {
        "description": "Current project style: task-frame extraction followed by schema post-processing.",
        "keys": ["nodes", "edges"],
    },
    "B3_edc_style": {
        "description": "EDC-style baseline: extract, define, and canonicalize open-schema KG items before CAPE-compatible scoring.",
        "keys": ["nodes", "edges"],
    },
    "B4_taxonomy_rag": {
        "description": "Taxonomy-RAG style extraction with NCS/PCF snippets in the prompt.",
        "keys": ["nodes", "edges", "mappings"],
    },
    "B5_procedural_prompt": {
        "description": "Procedural prompt extracting actions, actors, gateways, conditions, artifacts, and flows.",
        "keys": ["nodes", "edges"],
    },
    "P_cape_kg_actual": {
        "description": "CAPE-KG proposed prompt with CQ anchoring, evidence grounding, procedural schema, validation, and taxonomy bridge.",
        "keys": ["nodes", "edges", "mappings"],
    },
    "P_minus_CQ": {
        "description": "CAPE-KG ablation without competency-question anchoring.",
        "keys": ["nodes", "edges", "mappings"],
    },
    "P_minus_Evidence": {
        "description": "CAPE-KG ablation without required evidence anchors.",
        "keys": ["nodes", "edges", "mappings"],
    },
    "P_minus_Procedural_schema": {
        "description": "CAPE-KG ablation using a flat non-procedural schema.",
        "keys": ["nodes", "edges", "mappings"],
    },
    "P_minus_Validator": {
        "description": "CAPE-KG ablation retaining raw model schema choices without post-hoc validator rejection.",
        "keys": ["nodes", "edges", "mappings"],
    },
    "P_minus_Standard_bridge": {
        "description": "CAPE-KG ablation without NCS/PCF taxonomy bridge outputs.",
        "keys": ["nodes", "edges"],
    },
    "P_minus_Schema_retrieval": {
        "description": "CAPE-KG ablation without chunk-specific CQ/schema retrieval; uses the full schema list without taxonomy snippets.",
        "keys": ["nodes", "edges", "mappings"],
    },
}

CAPE_CONDITIONS = {
    "P_cape_kg_actual",
    "P_minus_CQ",
    "P_minus_Evidence",
    "P_minus_Procedural_schema",
    "P_minus_Validator",
    "P_minus_Standard_bridge",
    "P_minus_Schema_retrieval",
}

SCHEMA_EDGE_CONDITIONS = {
    "B1_predicate_constrained",
    "B2_current_project",
    "B3_edc_style",
    "B4_taxonomy_rag",
    "B5_procedural_prompt",
    *CAPE_CONDITIONS,
}

MAPPING_CONDITIONS = {
    "B4_taxonomy_rag",
    "P_cape_kg_actual",
    "P_minus_CQ",
    "P_minus_Evidence",
    "P_minus_Procedural_schema",
    "P_minus_Validator",
    "P_minus_Schema_retrieval",
}

STRICT_JSON_CONTRACT = """
Strict JSON contract:
- Return exactly one JSON object and nothing else.
- The first non-whitespace character must be `{` and the last non-whitespace character must be `}`.
- Do not include markdown, code fences, comments, XML tags, `<think>` blocks, prose, or explanations.
- For Qwen/Qwen-style chat models, obey `/no_think`; do not emit hidden or visible reasoning.
- Output the JSON object immediately without a preamble.
- Use compact JSON without indentation or extra whitespace to reduce truncation risk.
- Use double-quoted JSON strings only.
- Use empty arrays for absent `nodes`, `edges`, `triples`, or `mappings` fields required by the requested shape.
""".strip()

NON_PROCEDURAL_NODE_TYPES = {
    "DomainTask",
    "Artifact",
    "Role",
    "Principle",
    "Risk",
}

NON_PROCEDURAL_EDGE_TYPES = {
    "USES_INPUT",
    "PRODUCES",
    "PERFORMED_BY",
    "HAS_PRINCIPLE",
    "HAS_RISK",
}

COMPETENCY_QUESTIONS = [
    "CQ1: Identify major bid/proposal tasks and procedural steps.",
    "CQ2: Identify input artifacts used by each task.",
    "CQ3: Identify output artifacts produced by each task.",
    "CQ4: Identify roles responsible for each task.",
    "CQ5: Identify decision gateways.",
    "CQ6: Identify guard conditions for decisions or branches.",
    "CQ7: Identify artifact flows between tasks.",
    "CQ8: Identify review checkpoints.",
    "CQ9: Identify principles and risks.",
    "CQ10: Attach every accepted item to evidence in the chunk.",
    "CQ11: Link task labels to NCS capability candidates when supported.",
    "CQ12: Link task labels to PCF process candidates when supported.",
]


def read_jsonl(path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def append_jsonl(path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
        f.write("\n")


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            f.write("\n")


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write(text)


def load_taxonomy_context(kg_dir, limit):
    rows = []
    for standard, rel_path in [
        ("NCS", "08_mapping/l2_ncs_mapping_candidates.jsonl"),
        ("PCF", "08_mapping/l2_pcf_mapping_candidates.jsonl"),
    ]:
        path = Path(kg_dir) / rel_path
        if not path.exists():
            continue
        for row in read_jsonl(path):
            if int(row.get("rank", 999)) > 3:
                continue
            rows.append(
                {
                    "standard": standard,
                    "source_label": row.get("source_label", ""),
                    "target_label": row.get("target_label", ""),
                    "target_type": row.get("target_type", ""),
                    "score": row.get("score", 0),
                }
            )
    rows = sorted(rows, key=lambda r: (r["standard"], r["source_label"], -float(r.get("score") or 0)))
    lines = []
    seen = set()
    for row in rows:
        key = (row["standard"], row["source_label"], row["target_label"])
        if key in seen:
            continue
        seen.add(key)
        lines.append(
            f"- {row['standard']}: task={row['source_label']} -> {row['target_label']} "
            f"({row['target_type']}, score={row['score']})"
        )
        if len(lines) >= limit:
            break
    return "\n".join(lines)


def output_paths(exp_dir, prefix, shard_index=None):
    prefix = safe_slug(prefix)
    suffix = "" if shard_index is None else f".shard{shard_index:02d}"
    return {
        "raw": exp_dir / f"48_{prefix}_raw{suffix}.jsonl",
        "valid": exp_dir / f"49_{prefix}_valid{suffix}.jsonl",
        "report": exp_dir / f"50_{prefix}_quality_report{suffix}.md",
    }


def completed_keys(path):
    done = set()
    if not path.exists():
        return done
    for row in read_jsonl(path):
        if row.get("condition") and row.get("chunk_id"):
            done.add((row["condition"], row["chunk_id"]))
    return done


def select_chunks(chunks, max_chunks, shard_index, num_shards):
    selected = []
    for idx, chunk in enumerate(chunks):
        if num_shards > 1 and idx % num_shards != shard_index:
            continue
        selected.append(chunk)
    if max_chunks is not None:
        selected = selected[:max_chunks]
    return selected


def as_list(value):
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def find_json_array(text, key):
    key_token = f'"{key}"'
    key_pos = text.find(key_token)
    if key_pos < 0:
        return None
    start = text.find("[", key_pos + len(key_token))
    if start < 0:
        return None
    depth = 0
    in_string = False
    escape = False
    for idx in range(start, len(text)):
        char = text[idx]
        if escape:
            escape = False
            continue
        if char == "\\":
            escape = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                return text[start:idx + 1]
    return None


def find_json_array_start(text, key):
    key_token = f'"{key}"'
    key_pos = text.find(key_token)
    if key_pos < 0:
        return -1
    return text.find("[", key_pos + len(key_token))


def parse_complete_objects_from_array_prefix(text, key):
    """Return complete top-level JSON objects from a possibly truncated array.

    This is deliberately conservative: incomplete trailing objects are dropped,
    nested objects inside a top-level object are handled through brace depth,
    and parse failures for individual recovered spans are ignored.
    """
    start = find_json_array_start(text or "", key)
    if start < 0:
        return None
    objects = []
    in_string = False
    escape = False
    object_depth = 0
    object_start = None
    for idx in range(start + 1, len(text)):
        char = text[idx]
        if escape:
            escape = False
            continue
        if char == "\\":
            escape = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            if object_depth == 0:
                object_start = idx
            object_depth += 1
        elif char == "}":
            if object_depth <= 0:
                continue
            object_depth -= 1
            if object_depth == 0 and object_start is not None:
                candidate = text[object_start:idx + 1]
                try:
                    parsed = json.loads(candidate)
                except Exception:
                    object_start = None
                    continue
                if isinstance(parsed, dict):
                    objects.append(parsed)
                object_start = None
        elif char == "]" and object_depth == 0:
            break
    return objects if objects else None


def repair_partial_json_object(text):
    repaired = {}
    for key in ["nodes", "edges", "triples", "mappings"]:
        array_text = find_json_array(text or "", key)
        value = None
        if array_text:
            try:
                value = json.loads(array_text)
            except Exception:
                value = None
        if value is None:
            value = parse_complete_objects_from_array_prefix(text or "", key)
        if isinstance(value, list):
            repaired[key] = value
    return repaired if repaired else None


def valid_evidence_ids(ids, allowed):
    out = []
    for value in as_list(ids):
        value = clean_text(value)
        if value in allowed and value not in out:
            out.append(value)
    return out


def build_condition_prompt(condition, chunk, max_chars, taxonomy_context="", strict_json_contract=False):
    sentence_block = chunk_sentence_lines(chunk)
    if len(sentence_block) > max_chars:
        sentence_block = sentence_block[:max_chars].rsplit("\n", 1)[0]

    common = f"""
Return ONLY one valid JSON object. No markdown. No explanation.
Every extracted item must include at least one evidence_anchor_ids value from the chunk.
Do not use outside knowledge. Keep Korean labels when the source text is Korean.

Chunk metadata:
chunk_id: {chunk.get("chunk_id")}
pages: {chunk.get("page_start")}..{chunk.get("page_end")}
sentence_ids: {json.dumps(chunk.get("sentence_ids", []), ensure_ascii=False)}

Chunk sentences:
{sentence_block}
""".strip()

    if condition == "B0_plain_llm":
        instruction = """
You are the B0 baseline: plain LLM triple extraction.
Extract only directly supported subject-predicate-object triples.
Use any short predicate label that appears appropriate from the text.

JSON shape:
{
  "triples": [
    {
      "subject": "string",
      "predicate": "string",
      "object": "string",
      "evidence_anchor_ids": ["sentence ids"],
      "confidence": 0.0
    }
  ]
}
""".strip()
    elif condition == "B1_predicate_constrained":
        instruction = f"""
You are the B1 baseline: predicate-constrained LLM extraction.
Use only these predicates:
{json.dumps(sorted(ALLOWED_EDGE_TYPES), ensure_ascii=False)}

Extract edges as directly supported triples. Include node types if inferable.

JSON shape:
{{
  "edges": [
    {{
      "subject": "string",
      "subject_type": "DomainTask|ProcedureStep|DecisionGateway|GuardCondition|Artifact|ArtifactFlow|Role|ReviewCheckpoint|Principle|Risk",
      "predicate": "one allowed predicate",
      "object": "string",
      "object_type": "DomainTask|ProcedureStep|DecisionGateway|GuardCondition|Artifact|ArtifactFlow|Role|ReviewCheckpoint|Principle|Risk",
      "evidence_anchor_ids": ["sentence ids"],
      "confidence": 0.0
    }}
  ]
}}
""".strip()
    elif condition == "B2_current_project":
        instruction = f"""
You are the B2 baseline: current project extraction style.
First infer task frames from the chunk, then post-process them into CAPE-KG nodes and edges.
Prefer DomainTask, ProcedureStep, Artifact, Role, DecisionGateway, GuardCondition, ReviewCheckpoint, Principle, and Risk.
Use only these node types:
{json.dumps(sorted(ALLOWED_NODE_TYPES), ensure_ascii=False)}
Use only these edge predicates:
{json.dumps(sorted(ALLOWED_EDGE_TYPES), ensure_ascii=False)}

JSON shape:
{{
  "nodes": [
    {{
      "label": "string",
      "type": "one allowed node type",
      "definition": "short text-grounded description",
      "evidence_anchor_ids": ["sentence ids"],
      "confidence": 0.0
    }}
  ],
  "edges": [
    {{
      "subject": "string",
      "subject_type": "one allowed node type",
      "predicate": "one allowed edge predicate",
      "object": "string",
      "object_type": "one allowed node type",
      "evidence_anchor_ids": ["sentence ids"],
      "confidence": 0.0
    }}
  ]
}}
""".strip()
    elif condition == "B3_edc_style":
        instruction = f"""
You are the B3 baseline: EDC-style extraction.
Follow three steps internally:
1. Extract text-supported entity/relation mentions from the chunk.
2. Define each extracted concept using only the chunk text.
3. Canonicalize the extracted items into reusable labels and CAPE-compatible node/edge fields.

Do not use competency questions, taxonomy snippets, or procedural validators.
For scoring compatibility, choose the closest type/predicate from these compact inventories.

Node types:
{json.dumps(sorted(ALLOWED_NODE_TYPES), ensure_ascii=False)}

Edge predicates:
{json.dumps(sorted(ALLOWED_EDGE_TYPES), ensure_ascii=False)}

JSON shape:
{{
  "nodes": [
    {{
      "label": "canonical label",
      "type": "closest node type",
      "definition": "short definition grounded in this chunk",
      "mention": "surface text from chunk",
      "evidence_anchor_ids": ["sentence ids"],
      "confidence": 0.0
    }}
  ],
  "edges": [
    {{
      "subject": "canonical subject label",
      "subject_type": "closest node type",
      "predicate": "closest edge predicate",
      "object": "canonical object label",
      "object_type": "closest node type",
      "definition": "short relation definition grounded in this chunk",
      "evidence_anchor_ids": ["sentence ids"],
      "confidence": 0.0
    }}
  ]
}}
""".strip()
    elif condition == "B4_taxonomy_rag":
        instruction = f"""
You are the B4 baseline: taxonomy-RAG extraction.
Use the NCS/PCF/task taxonomy hints only as retrieval context. Extract only what is directly supported by the chunk.
Do not force a taxonomy mapping when the chunk does not support it.

Taxonomy snippets:
{taxonomy_context or "- No taxonomy snippets available."}

Use only these node types:
{json.dumps(sorted(ALLOWED_NODE_TYPES), ensure_ascii=False)}
Use only these edge predicates:
{json.dumps(sorted(ALLOWED_EDGE_TYPES), ensure_ascii=False)}

JSON shape:
{{
  "nodes": [
    {{
      "label": "string",
      "type": "one allowed node type",
      "evidence_anchor_ids": ["sentence ids"],
      "confidence": 0.0
    }}
  ],
  "edges": [
    {{
      "subject": "string",
      "subject_type": "one allowed node type",
      "predicate": "one allowed edge predicate",
      "object": "string",
      "object_type": "one allowed node type",
      "evidence_anchor_ids": ["sentence ids"],
      "confidence": 0.0
    }}
  ],
  "mappings": [
    {{
      "source_task": "text-supported task label",
      "standard": "NCS|PCF",
      "target_label": "taxonomy label from snippets",
      "evidence_anchor_ids": ["sentence ids"],
      "confidence": 0.0
    }}
  ]
}}
""".strip()
    elif condition == "B5_procedural_prompt":
        instruction = f"""
You are the B5 baseline: procedural prompt extraction.
Extract actions, actors/roles, decision gateways, guard conditions, artifacts, risks, principles, and procedural flows.
Use only these node types:
{json.dumps(sorted(ALLOWED_NODE_TYPES), ensure_ascii=False)}
Use only these edge predicates:
{json.dumps(sorted(ALLOWED_EDGE_TYPES), ensure_ascii=False)}

JSON shape:
{{
  "nodes": [
    {{
      "label": "string",
      "type": "one allowed node type",
      "evidence_anchor_ids": ["sentence ids"],
      "confidence": 0.0
    }}
  ],
  "edges": [
    {{
      "subject": "string",
      "subject_type": "one allowed node type",
      "predicate": "one allowed edge predicate",
      "object": "string",
      "object_type": "one allowed node type",
      "evidence_anchor_ids": ["sentence ids"],
      "confidence": 0.0
    }}
  ]
}}
""".strip()
    elif condition in CAPE_CONDITIONS:
        use_cq = condition != "P_minus_CQ"
        require_evidence = condition != "P_minus_Evidence"
        use_procedural = condition != "P_minus_Procedural_schema"
        use_validator = condition != "P_minus_Validator"
        use_standard_bridge = condition != "P_minus_Standard_bridge"
        use_schema_retrieval = condition != "P_minus_Schema_retrieval"

        node_types = sorted(ALLOWED_NODE_TYPES if use_procedural else NON_PROCEDURAL_NODE_TYPES)
        edge_types = sorted(ALLOWED_EDGE_TYPES if use_procedural else NON_PROCEDURAL_EDGE_TYPES)
        evidence_rule = (
            "Every node, edge, and mapping must include evidence_anchor_ids from the chunk."
            if require_evidence
            else "Evidence anchors are optional in this ablation. Include them only if convenient."
        )
        validator_rule = (
            "Use only the listed node types and edge predicates. Invalid schema terms will be rejected."
            if use_validator
            else "You may propose schema terms freely in this ablation; keep them short and text-grounded."
        )
        cq_block = "\n".join(f"- {cq}" for cq in COMPETENCY_QUESTIONS) if use_cq else "- CQ anchoring disabled for this ablation."
        if not use_standard_bridge:
            taxonomy_block = "- NCS/PCF bridge disabled for this ablation."
        elif not use_schema_retrieval:
            taxonomy_block = "- Chunk-specific schema/taxonomy retrieval disabled for this ablation. Use only the full schema lists below and the chunk text."
        else:
            taxonomy_block = taxonomy_context
        mappings_shape = """
  ],
  "mappings": [
    {
      "source_task": "text-supported task label",
      "standard": "NCS|PCF",
      "target_label": "taxonomy label from snippets",
      "evidence_anchor_ids": ["sentence ids"],
      "confidence": 0.0
    }
  ]
""".rstrip() if use_standard_bridge else "\n  ]"

        instruction = f"""
You are running the {condition} CAPE-KG condition.
Extract a domain procedural knowledge graph from the chunk.

Competency questions:
{cq_block}

Taxonomy snippets:
{taxonomy_block or "- No taxonomy snippets available."}

Rules:
- {evidence_rule}
- {validator_rule}
- Do not use outside knowledge.
- Keep Korean labels when the source text is Korean.
- Prefer concise, reusable labels.
- Hard limit: return at most 5 nodes, at most 5 edges, and at most 3 mappings.
- If the chunk does not support a field, return an empty array for that field.

Allowed node types for this condition:
{json.dumps(node_types, ensure_ascii=False)}

Allowed edge predicates for this condition:
{json.dumps(edge_types, ensure_ascii=False)}

JSON shape:
{{
  "nodes": [
    {{
      "label": "string",
      "type": "node type",
      "evidence_anchor_ids": ["sentence ids"],
      "confidence": 0.0
    }}
  ],
  "edges": [
    {{
      "subject": "string",
      "subject_type": "node type",
      "predicate": "edge predicate",
      "object": "string",
      "object_type": "node type",
      "evidence_anchor_ids": ["sentence ids"],
      "confidence": 0.0
    }}
{mappings_shape}
}}
""".strip()
    else:
        raise ValueError(f"Unsupported condition: {condition}")

    system_content = "You are an evidence-grounded information extraction baseline."
    user_content = instruction + "\n\n" + common
    if strict_json_contract:
        system_content = "You are a JSON-only evidence-grounded information extraction function.\n" + STRICT_JSON_CONTRACT
        user_content = "/no_think\n" + user_content + "\n\n/no_think\nReturn exactly one compact JSON object now."

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]


def validate_confidence(value):
    try:
        value = float(value)
    except Exception:
        return 0.0
    return round(max(0.0, min(1.0, value)), 3)


def allowed_node_types_for(condition):
    if condition == "P_minus_Procedural_schema":
        return NON_PROCEDURAL_NODE_TYPES
    return ALLOWED_NODE_TYPES


def allowed_edge_types_for(condition):
    if condition == "P_minus_Procedural_schema":
        return NON_PROCEDURAL_EDGE_TYPES
    return ALLOWED_EDGE_TYPES


def evidence_required_for(condition):
    return condition not in {"P_minus_Evidence", "P_minus_Validator"}


def validator_enabled_for(condition):
    return condition != "P_minus_Validator"


def validate_condition(condition, parsed, chunk):
    allowed_ids = set(chunk.get("sentence_ids", []))
    allowed_node_types = allowed_node_types_for(condition)
    allowed_edge_types = allowed_edge_types_for(condition)
    evidence_required = evidence_required_for(condition)
    validator_enabled = validator_enabled_for(condition)
    errors = Counter()
    valid = {
        "condition": condition,
        "chunk_id": chunk.get("chunk_id"),
        "nodes": [],
        "edges": [],
        "triples": [],
        "mappings": [],
    }
    if not isinstance(parsed, dict):
        errors["root_not_object"] += 1
        return valid, errors

    if condition == "B0_plain_llm":
        for item in as_list(parsed.get("triples")):
            if not isinstance(item, dict):
                errors["triple_not_object"] += 1
                continue
            evidence = valid_evidence_ids(item.get("evidence_anchor_ids"), allowed_ids)
            subject = clean_text(item.get("subject"))
            predicate = clean_text(item.get("predicate"))
            obj = clean_text(item.get("object"))
            if not subject or not predicate or not obj:
                errors["missing_triple_field"] += 1
                continue
            if not evidence:
                errors["missing_or_invalid_evidence"] += 1
                continue
            valid["triples"].append(
                {
                    "subject": subject[:160],
                    "predicate": predicate[:120],
                    "object": obj[:160],
                    "evidence_anchor_ids": evidence,
                    "confidence": validate_confidence(item.get("confidence")),
                }
            )

    if condition in SCHEMA_EDGE_CONDITIONS:
        for item in as_list(parsed.get("nodes")):
            if not isinstance(item, dict):
                errors["node_not_object"] += 1
                continue
            label = clean_text(item.get("label"))
            node_type = clean_text(item.get("type"))
            evidence = valid_evidence_ids(item.get("evidence_anchor_ids"), allowed_ids)
            if validator_enabled and node_type not in allowed_node_types:
                errors["unknown_node_type"] += 1
                continue
            if not label or (evidence_required and not evidence):
                errors["missing_node_label_or_evidence"] += 1
                continue
            if not node_type:
                node_type = "UnknownType" if not validator_enabled else ""
            valid["nodes"].append(
                {
                    "label": label[:160],
                    "type": node_type,
                    "evidence_anchor_ids": evidence,
                    "confidence": validate_confidence(item.get("confidence")),
                }
            )

        for item in as_list(parsed.get("edges")):
            if not isinstance(item, dict):
                errors["edge_not_object"] += 1
                continue
            subject = clean_text(item.get("subject"))
            obj = clean_text(item.get("object"))
            predicate = clean_text(item.get("predicate")).upper()
            subject_type = clean_text(item.get("subject_type"))
            object_type = clean_text(item.get("object_type"))
            evidence = valid_evidence_ids(item.get("evidence_anchor_ids"), allowed_ids)
            if validator_enabled and predicate not in allowed_edge_types:
                errors["unknown_predicate"] += 1
                continue
            if validator_enabled and subject_type and subject_type not in allowed_node_types:
                errors["unknown_subject_type"] += 1
                continue
            if validator_enabled and object_type and object_type not in allowed_node_types:
                errors["unknown_object_type"] += 1
                continue
            if not subject or not obj or (evidence_required and not evidence):
                errors["missing_edge_field_or_evidence"] += 1
                continue
            if not predicate:
                predicate = "UNKNOWN_PREDICATE" if not validator_enabled else ""
            valid["edges"].append(
                {
                    "subject": subject[:160],
                    "subject_type": subject_type,
                    "predicate": predicate,
                    "object": obj[:160],
                    "object_type": object_type,
                    "evidence_anchor_ids": evidence,
                    "confidence": validate_confidence(item.get("confidence")),
                }
            )

    if condition in MAPPING_CONDITIONS:
        for item in as_list(parsed.get("mappings")):
            if not isinstance(item, dict):
                errors["mapping_not_object"] += 1
                continue
            source_task = clean_text(item.get("source_task"))
            standard = clean_text(item.get("standard")).upper()
            target_label = clean_text(item.get("target_label"))
            evidence = valid_evidence_ids(item.get("evidence_anchor_ids"), allowed_ids)
            if validator_enabled and standard not in {"NCS", "PCF"}:
                errors["unknown_standard"] += 1
                continue
            if not source_task or not target_label or (evidence_required and not evidence):
                errors["missing_mapping_field_or_evidence"] += 1
                continue
            if not standard:
                standard = "UNKNOWN_STANDARD" if not validator_enabled else ""
            valid["mappings"].append(
                {
                    "source_task": source_task[:160],
                    "standard": standard,
                    "target_label": target_label[:160],
                    "evidence_anchor_ids": evidence,
                    "confidence": validate_confidence(item.get("confidence")),
                }
            )

    return valid, errors


def run(args):
    exp_dir = Path(args.output_dir)
    paths = output_paths(exp_dir, args.output_prefix, args.shard_index if args.num_shards > 1 else None)
    chunks = select_chunks(read_jsonl(exp_dir / args.chunk_file), args.max_chunks, args.shard_index, args.num_shards)
    taxonomy_context = load_taxonomy_context(args.kg_dir, args.taxonomy_context_items)
    conditions = [c.strip() for c in args.conditions.split(",") if c.strip()]
    for condition in conditions:
        if condition not in CONDITIONS:
            raise SystemExit(f"Unsupported condition: {condition}")
    done = completed_keys(paths["raw"]) if args.resume else set()

    print(
        json.dumps(
            {
                "event": "start",
                "output_dir": str(exp_dir),
                "chunk_file": args.chunk_file,
                "conditions": conditions,
                "chunks_selected": len(chunks),
                "already_done": len(done),
                "model": args.model,
                "output_prefix": safe_slug(args.output_prefix),
                "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES", ""),
                "shard_index": args.shard_index,
                "num_shards": args.num_shards,
            },
            ensure_ascii=False,
        ),
        flush=True,
    )

    tokenizer, model = load_model(args.model, args.quantization)
    started = time.time()
    processed = 0
    stats = defaultdict(Counter)

    for condition in conditions:
        for chunk in chunks:
            key = (condition, chunk["chunk_id"])
            if key in done:
                continue
            messages = build_condition_prompt(
                condition,
                chunk,
                args.max_prompt_chars,
                taxonomy_context,
                strict_json_contract=args.strict_json_contract,
            )
            raw_text = ""
            parsed = None
            parse_error = None
            error = None
            partial_json_repaired = False
            try:
                raw_text = generate_json(tokenizer, model, messages, args.max_new_tokens)
                parsed, parse_error = parse_json_object(raw_text)
                if parse_error:
                    stats[condition]["parse_error"] += 1
                    repaired = repair_partial_json_object(raw_text)
                    if repaired:
                        parsed = repaired
                        partial_json_repaired = True
                        stats[condition]["partial_json_repair"] += 1
                valid, validation_errors = validate_condition(condition, parsed, chunk)
                stats[condition].update(validation_errors)
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
                stats[condition]["generation_exception"] += 1
                valid = {"condition": condition, "chunk_id": chunk["chunk_id"], "nodes": [], "edges": [], "triples": [], "mappings": []}

            raw_row = {
                "condition": condition,
                "chunk_id": chunk["chunk_id"],
                "page_start": chunk.get("page_start"),
                "page_end": chunk.get("page_end"),
                "sentence_ids": chunk.get("sentence_ids", []),
                "raw_text": raw_text,
                "parsed": parsed,
                "parse_error": parse_error,
                "partial_json_repaired": partial_json_repaired,
                "strict_json_contract": bool(args.strict_json_contract),
                "error": error,
                "model": args.model,
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            }
            append_jsonl(paths["raw"], raw_row)
            append_jsonl(paths["valid"], valid)

            stats[condition]["raw_rows"] += 1
            stats[condition]["valid_nodes"] += len(valid.get("nodes", []))
            stats[condition]["valid_edges"] += len(valid.get("edges", []))
            stats[condition]["valid_triples"] += len(valid.get("triples", []))
            stats[condition]["valid_mappings"] += len(valid.get("mappings", []))
            if parse_error or error:
                stats[condition]["raw_rows_with_parse_or_generation_errors"] += 1
            processed += 1
            if processed % max(1, args.progress_every) == 0:
                print(
                    json.dumps(
                        {
                            "event": "progress",
                            "processed_generations": processed,
                            "condition": condition,
                            "chunk_id": chunk["chunk_id"],
                            "elapsed_sec": round(time.time() - started, 1),
                        },
                        ensure_ascii=False,
                    ),
                    flush=True,
                )

    raw_rows = read_jsonl(paths["raw"]) if paths["raw"].exists() else []
    valid_rows = read_jsonl(paths["valid"]) if paths["valid"].exists() else []
    aggregate = defaultdict(Counter)
    for row in raw_rows:
        condition = row.get("condition", "unknown")
        aggregate[condition]["raw_rows"] += 1
        if row.get("parse_error") or row.get("error"):
            aggregate[condition]["raw_rows_with_parse_or_generation_errors"] += 1
        if row.get("partial_json_repaired"):
            aggregate[condition]["partial_json_repaired_rows"] += 1
    for row in valid_rows:
        condition = row.get("condition", "unknown")
        aggregate[condition]["valid_nodes"] += len(row.get("nodes", []))
        aggregate[condition]["valid_edges"] += len(row.get("edges", []))
        aggregate[condition]["valid_triples"] += len(row.get("triples", []))
        aggregate[condition]["valid_mappings"] += len(row.get("mappings", []))

    report = [
        "# Condition-Specific LLM Baseline Report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        f"- Output directory: `{exp_dir}`",
        f"- Output prefix: `{safe_slug(args.output_prefix)}`",
        f"- Model: `{args.model}`",
        f"- Quantization: `{args.quantization}`",
        f"- Strict JSON contract: {bool(args.strict_json_contract)}",
        f"- CUDA_VISIBLE_DEVICES: `{os.environ.get('CUDA_VISIBLE_DEVICES', '')}`",
        f"- Chunk file: `{args.chunk_file}`",
        f"- Shard: {args.shard_index + 1} / {args.num_shards}",
        f"- Chunks selected: {len(chunks)}",
        "",
        "## Conditions",
        "",
    ]
    for condition in conditions:
        counts = aggregate[condition]
        report.append(
            f"- {condition}: raw_rows={counts['raw_rows']}, "
            f"valid_triples={counts['valid_triples']}, "
            f"valid_nodes={counts['valid_nodes']}, "
            f"valid_edges={counts['valid_edges']}, "
            f"valid_mappings={counts['valid_mappings']}, "
            f"parse_or_generation_error_rows={counts['raw_rows_with_parse_or_generation_errors']}, "
            f"partial_json_repaired_rows={counts['partial_json_repaired_rows']}"
        )
    report += [
        "",
        "## Files",
        "",
        f"- Raw outputs: `{paths['raw'].name}`",
        f"- Validated outputs: `{paths['valid'].name}`",
        "",
    ]
    write_text(paths["report"], "\n".join(report))
    print(
        json.dumps(
            {
                "event": "done",
                "processed_generations": processed,
                "raw_file": str(paths["raw"]),
                "valid_file": str(paths["valid"]),
                "report_file": str(paths["report"]),
                "conditions": {k: dict(v) for k, v in aggregate.items()},
            },
            ensure_ascii=False,
        ),
        flush=True,
    )


def revalidate_raw(args):
    exp_dir = Path(args.output_dir)
    paths = output_paths(exp_dir, args.output_prefix, args.shard_index if args.num_shards > 1 else None)
    if not paths["raw"].exists():
        raise SystemExit(f"Missing raw file: {paths['raw']}")
    chunks = {row["chunk_id"]: row for row in read_jsonl(exp_dir / args.chunk_file)}
    raw_rows = read_jsonl(paths["raw"])
    new_raw_rows = []
    valid_rows = []
    aggregate = defaultdict(Counter)
    for row in raw_rows:
        condition = row.get("condition", "unknown")
        chunk_id = row.get("chunk_id")
        chunk = chunks.get(chunk_id, {"chunk_id": chunk_id, "sentence_ids": row.get("sentence_ids", [])})
        raw_text = row.get("raw_text") or ""
        parsed, parse_error = parse_json_object(raw_text)
        partial_json_repaired = False
        if parse_error:
            repaired = repair_partial_json_object(raw_text)
            if repaired is not None:
                parsed = repaired
                partial_json_repaired = True
                aggregate[condition]["partial_json_repaired_rows"] += 1
        valid, validation_errors = validate_condition(condition, parsed, chunk)
        aggregate[condition].update(validation_errors)
        aggregate[condition]["raw_rows"] += 1
        aggregate[condition]["valid_triples"] += len(valid.get("triples", []))
        aggregate[condition]["valid_nodes"] += len(valid.get("nodes", []))
        aggregate[condition]["valid_edges"] += len(valid.get("edges", []))
        aggregate[condition]["valid_mappings"] += len(valid.get("mappings", []))
        if parse_error or row.get("error"):
            aggregate[condition]["raw_rows_with_parse_or_generation_errors"] += 1
        if (parse_error or row.get("error")) and not partial_json_repaired:
            aggregate[condition]["unrepaired_parse_or_generation_error_rows"] += 1
        new_row = dict(row)
        new_row["parsed"] = parsed
        new_row["parse_error"] = parse_error
        new_row["partial_json_repaired"] = partial_json_repaired
        new_row["revalidated_at_utc"] = datetime.now(timezone.utc).isoformat()
        new_raw_rows.append(new_row)
        valid_rows.append(valid)

    write_jsonl(paths["raw"], sorted(new_raw_rows, key=lambda r: (r.get("condition", ""), r.get("chunk_id", ""))))
    write_jsonl(paths["valid"], sorted(valid_rows, key=lambda r: (r.get("condition", ""), r.get("chunk_id", ""))))

    report = [
        "# Condition-Specific LLM Baseline Report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Revalidated Existing Raw Outputs",
        "",
        f"- Output directory: `{exp_dir}`",
        f"- Output prefix: `{safe_slug(args.output_prefix)}`",
        f"- Raw rows: {len(raw_rows)}",
        f"- Raw file: `{paths['raw'].name}`",
        f"- Validated outputs: `{paths['valid'].name}`",
        "",
        "## Conditions",
        "",
    ]
    for condition, counts in sorted(aggregate.items()):
        report.append(
            f"- {condition}: raw_rows={counts['raw_rows']}, "
            f"valid_triples={counts['valid_triples']}, "
            f"valid_nodes={counts['valid_nodes']}, "
            f"valid_edges={counts['valid_edges']}, "
            f"valid_mappings={counts['valid_mappings']}, "
            f"parse_or_generation_error_rows={counts['raw_rows_with_parse_or_generation_errors']}, "
            f"unrepaired_parse_or_generation_error_rows={counts['unrepaired_parse_or_generation_error_rows']}, "
            f"partial_json_repaired_rows={counts['partial_json_repaired_rows']}"
        )
    write_text(paths["report"], "\n".join(report) + "\n")
    print(
        json.dumps(
            {
                "event": "revalidated",
                "raw_rows": len(raw_rows),
                "raw_file": str(paths["raw"]),
                "valid_file": str(paths["valid"]),
                "report_file": str(paths["report"]),
                "conditions": {k: dict(v) for k, v in aggregate.items()},
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def merge_shards(args):
    exp_dir = Path(args.output_dir)
    combined_paths = output_paths(exp_dir, args.output_prefix)
    raw_rows = []
    valid_rows = []
    shard_reports = []
    for shard_index in range(args.num_shards):
        paths = output_paths(exp_dir, args.output_prefix, shard_index)
        if paths["raw"].exists():
            raw_rows.extend(read_jsonl(paths["raw"]))
        if paths["valid"].exists():
            valid_rows.extend(read_jsonl(paths["valid"]))
        if paths["report"].exists():
            shard_reports.append(paths["report"].read_text(encoding="utf-8"))

    raw_rows = sorted(raw_rows, key=lambda r: (r.get("condition", ""), r.get("chunk_id", "")))
    valid_rows = sorted(valid_rows, key=lambda r: (r.get("condition", ""), r.get("chunk_id", "")))
    write_jsonl(combined_paths["raw"], raw_rows)
    write_jsonl(combined_paths["valid"], valid_rows)

    aggregate = defaultdict(Counter)
    for row in raw_rows:
        condition = row.get("condition", "unknown")
        aggregate[condition]["raw_rows"] += 1
        if row.get("parse_error") or row.get("error"):
            aggregate[condition]["raw_rows_with_parse_or_generation_errors"] += 1
        if row.get("partial_json_repaired"):
            aggregate[condition]["partial_json_repaired_rows"] += 1
    for row in valid_rows:
        condition = row.get("condition", "unknown")
        aggregate[condition]["valid_triples"] += len(row.get("triples", []))
        aggregate[condition]["valid_nodes"] += len(row.get("nodes", []))
        aggregate[condition]["valid_edges"] += len(row.get("edges", []))
        aggregate[condition]["valid_mappings"] += len(row.get("mappings", []))

    report = [
        "# Condition-Specific LLM Baseline Report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Combined Shards",
        "",
        f"- Output directory: `{exp_dir}`",
        f"- Output prefix: `{safe_slug(args.output_prefix)}`",
        f"- Shards requested: {args.num_shards}",
        f"- Raw rows: {len(raw_rows)}",
        f"- Valid rows: {len(valid_rows)}",
        "",
        "## Conditions",
        "",
    ]
    for condition, counts in sorted(aggregate.items()):
        report.append(
            f"- {condition}: raw_rows={counts['raw_rows']}, "
            f"valid_triples={counts['valid_triples']}, "
            f"valid_nodes={counts['valid_nodes']}, "
            f"valid_edges={counts['valid_edges']}, "
            f"valid_mappings={counts['valid_mappings']}, "
            f"parse_or_generation_error_rows={counts['raw_rows_with_parse_or_generation_errors']}, "
            f"partial_json_repaired_rows={counts['partial_json_repaired_rows']}"
        )
    report += [
        "",
        "## Files",
        "",
        f"- Raw outputs: `{combined_paths['raw'].name}`",
        f"- Validated outputs: `{combined_paths['valid'].name}`",
        "",
        "## Shard Reports",
        "",
        "\n\n".join(shard_reports),
    ]
    write_text(combined_paths["report"], "\n".join(report))
    print(
        json.dumps(
            {
                "event": "merged",
                "raw_rows": len(raw_rows),
                "valid_rows": len(valid_rows),
                "report_file": str(combined_paths["report"]),
                "conditions": {k: dict(v) for k, v in aggregate.items()},
            },
            ensure_ascii=False,
        )
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--chunk-file", default="01_data/evaluation_chunks.jsonl")
    parser.add_argument("--conditions", default="B0_plain_llm,B1_predicate_constrained,B5_procedural_prompt")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--quantization", choices=["native", "4bit", "8bit", "fp16"], default="4bit")
    parser.add_argument("--kg-dir", default="outputs")
    parser.add_argument("--taxonomy-context-items", type=int, default=40)
    parser.add_argument("--output-prefix", default="qwen3_8b_condition_baselines")
    parser.add_argument("--max-chunks", type=int, default=None)
    parser.add_argument("--max-prompt-chars", type=int, default=3600)
    parser.add_argument("--max-new-tokens", type=int, default=700)
    parser.add_argument("--progress-every", type=int, default=5)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--num-shards", type=int, default=1)
    parser.add_argument("--merge-shards", action="store_true")
    parser.add_argument("--revalidate-raw", action="store_true")
    parser.add_argument("--strict-json-contract", action="store_true")
    args = parser.parse_args()
    if args.num_shards < 1:
        raise SystemExit("--num-shards must be >= 1")
    if not 0 <= args.shard_index < args.num_shards:
        raise SystemExit("--shard-index must satisfy 0 <= shard_index < num_shards")
    if args.revalidate_raw:
        revalidate_raw(args)
    elif args.merge_shards:
        merge_shards(args)
    else:
        run(args)


if __name__ == "__main__":
    main()
