#!/usr/bin/env python3
"""
Run the LLM-backed CEP-Onto extraction pass on top of the deterministic scaffold.

This script consumes the artifacts produced by scripts/build_cep_onto_kg.py and
adds a resumable tool-constrained extraction pass. It intentionally keeps the
LLM output separate from the deterministic graph so that draft rule results,
raw model generations, and validated tool calls can be audited independently.
"""

import argparse
import json
import math
import os
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig


DEFAULT_MODEL = (
    "/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-8B/"
    "snapshots/b968826d9c46dd6066d109eabc6255188de91218"
)

ALLOWED_CLASSES = {
    "DomainTask",
    "ProcedureStep",
    "DecisionGateway",
    "GuardCondition",
    "Artifact",
    "Role",
    "Principle",
    "ReviewEvent",
    "Risk",
}

ALLOWED_PREDICATES = {
    "HAS_SUBTASK",
    "PRECEDES",
    "USES_INPUT",
    "PRODUCES",
    "PERFORMED_BY",
    "RESPONSIBLE_FOR",
    "HAS_DECISION_GATEWAY",
    "HAS_GUARD_CONDITION",
    "BRANCHES_TO",
    "HAS_REVIEW",
    "HAS_PRINCIPLE",
    "HAS_RISK",
    "TRANSFORMS_INTO",
}

PREDICATE_DOMAIN_RANGE = {
    "HAS_SUBTASK": ("DomainTask", "ProcedureStep"),
    "PRECEDES": ("ProcedureStep", "ProcedureStep"),
    "USES_INPUT": ("DomainTask", "Artifact"),
    "PRODUCES": ("DomainTask", "Artifact"),
    "PERFORMED_BY": ("ProcedureStep", "Role"),
    "RESPONSIBLE_FOR": ("Role", "DomainTask"),
    "HAS_DECISION_GATEWAY": ("DomainTask", "DecisionGateway"),
    "HAS_GUARD_CONDITION": ("*", "GuardCondition"),
    "BRANCHES_TO": ("DecisionGateway", "ProcedureStep"),
    "HAS_REVIEW": ("DomainTask", "ReviewEvent"),
    "HAS_PRINCIPLE": ("DomainTask", "Principle"),
    "HAS_RISK": ("DomainTask", "Risk"),
    "TRANSFORMS_INTO": ("Artifact", "Artifact"),
}


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


def clean_text(text):
    text = "" if text is None else str(text)
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clamp_confidence(value):
    try:
        value = float(value)
    except Exception:
        return 0.0
    if math.isnan(value) or math.isinf(value):
        return 0.0
    return round(max(0.0, min(1.0, value)), 3)


def load_model(model_path, quantization):
    tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        local_files_only=True,
        trust_remote_code=True,
    )
    kwargs = {
        "local_files_only": True,
        "trust_remote_code": True,
        "device_map": "auto",
    }
    if quantization == "4bit":
        kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
        )
    elif quantization == "8bit":
        kwargs["quantization_config"] = BitsAndBytesConfig(load_in_8bit=True)
    else:
        kwargs["torch_dtype"] = torch.float16
    model = AutoModelForCausalLM.from_pretrained(model_path, **kwargs)
    model.eval()
    return tokenizer, model


def chunk_sentence_lines(chunk):
    lines = []
    for sent_id, text in zip(chunk.get("sentence_ids", []), chunk.get("text", "").splitlines()):
        text = clean_text(text)
        if text:
            lines.append(f"{sent_id}: {text}")
    return "\n".join(lines)


def build_prompt(chunk, max_chars):
    sentence_block = chunk_sentence_lines(chunk)
    if len(sentence_block) > max_chars:
        sentence_block = sentence_block[:max_chars].rsplit("\n", 1)[0]

    schema = {
        "create_task_frame": {
            "task_name": "string",
            "definition": "string grounded in the text",
            "inputs": ["Artifact labels"],
            "outputs": ["Artifact labels"],
            "roles": ["Role labels"],
            "decision_points": ["DecisionGateway labels"],
            "principles": ["Principle labels"],
            "risks": ["Risk labels"],
            "evidence_anchor_ids": ["one or more sentence ids from this chunk"],
            "confidence": "0.0-1.0",
        },
        "add_procedural_relation": {
            "subject_label": "string",
            "subject_type": sorted(ALLOWED_CLASSES),
            "predicate": sorted(ALLOWED_PREDICATES),
            "object_label": "string",
            "object_type": sorted(ALLOWED_CLASSES),
            "modality": ["must", "should", "may", "example"],
            "evidence_anchor_ids": ["one or more sentence ids from this chunk"],
            "confidence": "0.0-1.0",
        },
        "reject_candidate": {
            "candidate_text": "string",
            "reason": "unsupported|too_vague|ocr_error|out_of_scope",
            "evidence_anchor_ids": ["sentence ids if available"],
        },
    }

    user = f"""
You are performing CEP-Onto extraction for bid/proposal work.

Return ONLY one valid JSON object. No markdown. No explanation.

Use only these tool-call keys:
- create_task_frame
- add_procedural_relation
- reject_candidate

Rules:
1. Every task, relation, and slot must be supported by at least one sentence id from the chunk.
2. Do not invent information that is not directly supported by the chunk.
3. Use Korean labels as they appear in the text when possible.
4. Use only allowed predicates and classes from the schema.
5. Prefer procedural knowledge: tasks, steps, decisions, guard conditions, artifacts, roles, risks, and principles.
6. If a claim is uncertain but text-supported, set modality to "may" and lower confidence.
7. If no grounded task or relation exists, return empty arrays.

Output JSON shape:
{json.dumps(schema, ensure_ascii=False, indent=2)}

Chunk metadata:
chunk_id: {chunk.get("chunk_id")}
pages: {chunk.get("page_start")}..{chunk.get("page_end")}
sentence_ids: {json.dumps(chunk.get("sentence_ids", []), ensure_ascii=False)}

Chunk sentences:
{sentence_block}
""".strip()

    return [
        {
            "role": "system",
            "content": "You extract evidence-grounded ontology tool calls. Return only valid JSON.",
        },
        {"role": "user", "content": user},
    ]


def generate_json(tokenizer, model, messages, max_new_tokens):
    try:
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
    except TypeError:
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

    inputs = tokenizer(prompt, return_tensors="pt")
    inputs = {k: v.to(model.device) for k, v in inputs.items()}
    with torch.inference_mode():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=None,
            top_p=None,
            top_k=None,
            pad_token_id=tokenizer.eos_token_id,
        )
    generated = outputs[0][inputs["input_ids"].shape[-1] :]
    return tokenizer.decode(generated, skip_special_tokens=True).strip()


def parse_json_object(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    try:
        return json.loads(text), None
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        candidate = text[start : end + 1]
        try:
            return json.loads(candidate), None
        except json.JSONDecodeError as exc:
            return None, f"{type(exc).__name__}: {exc}"
    return None, "No JSON object found"


def as_list(value):
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def valid_evidence_ids(ids, allowed_ids):
    out = []
    for value in as_list(ids):
        value = clean_text(value)
        if value in allowed_ids and value not in out:
            out.append(value)
    return out


def validate_task_frame(item, chunk_id, allowed_ids):
    task_name = clean_text(item.get("task_name"))
    evidence = valid_evidence_ids(item.get("evidence_anchor_ids"), allowed_ids)
    if len(task_name) < 2 or not evidence:
        return None, "missing_task_name_or_evidence"
    return (
        {
            "chunk_id": chunk_id,
            "task_name": task_name[:160],
            "definition": clean_text(item.get("definition"))[:500],
            "inputs": [clean_text(x)[:120] for x in as_list(item.get("inputs")) if clean_text(x)],
            "outputs": [clean_text(x)[:120] for x in as_list(item.get("outputs")) if clean_text(x)],
            "roles": [clean_text(x)[:120] for x in as_list(item.get("roles")) if clean_text(x)],
            "decision_points": [
                clean_text(x)[:120] for x in as_list(item.get("decision_points")) if clean_text(x)
            ],
            "principles": [clean_text(x)[:120] for x in as_list(item.get("principles")) if clean_text(x)],
            "risks": [clean_text(x)[:120] for x in as_list(item.get("risks")) if clean_text(x)],
            "evidence_anchor_ids": evidence,
            "confidence": clamp_confidence(item.get("confidence")),
            "source": "qwen3_8b_tool_constrained_extraction",
        },
        None,
    )


def validate_relation(item, chunk_id, allowed_ids):
    subject_label = clean_text(item.get("subject_label"))
    object_label = clean_text(item.get("object_label"))
    subject_type = clean_text(item.get("subject_type"))
    object_type = clean_text(item.get("object_type"))
    predicate = clean_text(item.get("predicate")).upper()
    evidence = valid_evidence_ids(item.get("evidence_anchor_ids"), allowed_ids)
    modality = clean_text(item.get("modality")) or "may"

    if predicate not in ALLOWED_PREDICATES:
        return None, "unknown_predicate"
    if subject_type not in ALLOWED_CLASSES or object_type not in ALLOWED_CLASSES:
        return None, "unknown_class"
    if len(subject_label) < 2 or len(object_label) < 2 or not evidence:
        return None, "missing_label_or_evidence"
    if modality not in {"must", "should", "may", "example"}:
        modality = "may"

    expected_domain, expected_range = PREDICATE_DOMAIN_RANGE.get(predicate, ("*", "*"))
    if expected_domain != "*" and subject_type != expected_domain:
        return None, "domain_violation"
    if expected_range != "*" and object_type != expected_range:
        return None, "range_violation"

    return (
        {
            "chunk_id": chunk_id,
            "subject_label": subject_label[:160],
            "subject_type": subject_type,
            "predicate": predicate,
            "object_label": object_label[:160],
            "object_type": object_type,
            "modality": modality,
            "evidence_anchor_ids": evidence,
            "confidence": clamp_confidence(item.get("confidence")),
            "source": "qwen3_8b_tool_constrained_extraction",
        },
        None,
    )


def validate_rejection(item, chunk_id, allowed_ids):
    text = clean_text(item.get("candidate_text"))
    reason = clean_text(item.get("reason"))
    if reason not in {"unsupported", "too_vague", "ocr_error", "out_of_scope"}:
        reason = "unsupported"
    evidence = valid_evidence_ids(item.get("evidence_anchor_ids"), allowed_ids)
    if not text:
        return None
    return {
        "chunk_id": chunk_id,
        "candidate_text": text[:300],
        "reason": reason,
        "evidence_anchor_ids": evidence,
        "source": "qwen3_8b_tool_constrained_extraction",
    }


def validate_extraction(parsed, chunk):
    chunk_id = chunk["chunk_id"]
    allowed_ids = set(chunk.get("sentence_ids", []))
    errors = Counter()
    valid = {
        "chunk_id": chunk_id,
        "create_task_frame": [],
        "add_procedural_relation": [],
        "reject_candidate": [],
    }
    if not isinstance(parsed, dict):
        errors["root_not_object"] += 1
        return valid, errors

    for item in as_list(parsed.get("create_task_frame")):
        if not isinstance(item, dict):
            errors["task_not_object"] += 1
            continue
        row, error = validate_task_frame(item, chunk_id, allowed_ids)
        if error:
            errors[error] += 1
        else:
            valid["create_task_frame"].append(row)

    for item in as_list(parsed.get("add_procedural_relation")):
        if not isinstance(item, dict):
            errors["relation_not_object"] += 1
            continue
        row, error = validate_relation(item, chunk_id, allowed_ids)
        if error:
            errors[error] += 1
        else:
            valid["add_procedural_relation"].append(row)

    for item in as_list(parsed.get("reject_candidate")):
        if isinstance(item, dict):
            row = validate_rejection(item, chunk_id, allowed_ids)
            if row:
                valid["reject_candidate"].append(row)

    return valid, errors


def shard_paths(out_dir, shard_index=None):
    suffix = "" if shard_index is None else f".shard{shard_index:02d}"
    return {
        "raw": out_dir / f"45_llm_tool_extractions_raw{suffix}.jsonl",
        "valid": out_dir / f"46_llm_tool_extractions_valid{suffix}.jsonl",
        "report": out_dir / f"47_llm_extraction_quality_report{suffix}.md",
    }


def completed_chunk_ids(path):
    if not path.exists():
        return set()
    done = set()
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                if row.get("chunk_id"):
                    done.add(row["chunk_id"])
            except Exception:
                continue
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


def run(args):
    out_dir = Path(args.output_dir)
    chunks = read_jsonl(out_dir / args.chunk_file)
    chunks = select_chunks(chunks, args.max_chunks, args.shard_index, args.num_shards)
    paths = shard_paths(out_dir, args.shard_index if args.num_shards > 1 else None)
    done = completed_chunk_ids(paths["raw"]) if args.resume else set()

    print(
        json.dumps(
            {
                "event": "start",
                "output_dir": str(out_dir),
                "chunk_file": args.chunk_file,
                "chunks_selected": len(chunks),
                "chunks_already_done": len(done),
                "model": args.model,
                "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES", ""),
                "shard_index": args.shard_index,
                "num_shards": args.num_shards,
            },
            ensure_ascii=False,
        ),
        flush=True,
    )

    tokenizer, model = load_model(args.model, args.quantization)
    error_counts = Counter()
    task_count = 0
    relation_count = 0
    rejection_count = 0
    processed = 0
    started = time.time()

    for chunk in chunks:
        chunk_id = chunk["chunk_id"]
        if chunk_id in done:
            continue
        messages = build_prompt(chunk, args.max_prompt_chars)
        raw_text = ""
        parsed = None
        parse_error = None
        error = None
        try:
            raw_text = generate_json(tokenizer, model, messages, args.max_new_tokens)
            parsed, parse_error = parse_json_object(raw_text)
            if parse_error:
                error_counts["parse_error"] += 1
            valid, validation_errors = validate_extraction(parsed, chunk)
            error_counts.update(validation_errors)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            error_counts["generation_exception"] += 1
            valid = {
                "chunk_id": chunk_id,
                "create_task_frame": [],
                "add_procedural_relation": [],
                "reject_candidate": [],
            }

        raw_row = {
            "chunk_id": chunk_id,
            "page_start": chunk.get("page_start"),
            "page_end": chunk.get("page_end"),
            "sentence_ids": chunk.get("sentence_ids", []),
            "raw_text": raw_text,
            "parsed": parsed,
            "parse_error": parse_error,
            "error": error,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        append_jsonl(paths["raw"], raw_row)
        append_jsonl(paths["valid"], valid)

        task_count += len(valid["create_task_frame"])
        relation_count += len(valid["add_procedural_relation"])
        rejection_count += len(valid["reject_candidate"])
        processed += 1
        if processed % max(1, args.progress_every) == 0:
            print(
                json.dumps(
                    {
                        "event": "progress",
                        "processed": processed,
                        "remaining": len(chunks) - len(done) - processed,
                        "task_frames": task_count,
                        "relations": relation_count,
                        "elapsed_sec": round(time.time() - started, 1),
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )

    total_raw_rows = len(completed_chunk_ids(paths["raw"]))
    report = f"""# LLM Tool-Constrained Extraction Report

Generated: {datetime.now(timezone.utc).isoformat()}

- Output directory: `{out_dir}`
- Model: `{args.model}`
- Quantization: `{args.quantization}`
- CUDA_VISIBLE_DEVICES: `{os.environ.get("CUDA_VISIBLE_DEVICES", "")}`
- Chunk file: `{args.chunk_file}`
- Shard: {args.shard_index + 1} / {args.num_shards}
- Selected chunks: {len(chunks)}
- Newly processed chunks: {processed}
- Raw rows currently present: {total_raw_rows}
- Valid task frames in this run: {task_count}
- Valid procedural relations in this run: {relation_count}
- Rejected candidates in this run: {rejection_count}
- Validation/drop counts: {json.dumps(dict(error_counts), ensure_ascii=False, sort_keys=True)}

Files:

- Raw model output: `{paths["raw"].name}`
- Validated tool calls: `{paths["valid"].name}`
"""
    write_text(paths["report"], report)
    print(
        json.dumps(
            {
                "event": "done",
                "processed": processed,
                "task_frames": task_count,
                "relations": relation_count,
                "rejections": rejection_count,
                "errors": dict(error_counts),
                "raw_file": str(paths["raw"]),
                "valid_file": str(paths["valid"]),
                "report_file": str(paths["report"]),
            },
            ensure_ascii=False,
        ),
        flush=True,
    )


def merge_shards(args):
    out_dir = Path(args.output_dir)
    raw_rows = []
    valid_rows = []
    reports = []
    for shard_idx in range(args.num_shards):
        paths = shard_paths(out_dir, shard_idx)
        if paths["raw"].exists():
            raw_rows.extend(read_jsonl(paths["raw"]))
        if paths["valid"].exists():
            valid_rows.extend(read_jsonl(paths["valid"]))
        if paths["report"].exists():
            reports.append(paths["report"].read_text(encoding="utf-8"))

    raw_rows = sorted(raw_rows, key=lambda r: r.get("chunk_id", ""))
    valid_rows = sorted(valid_rows, key=lambda r: r.get("chunk_id", ""))
    combined_raw = out_dir / "45_llm_tool_extractions_raw.jsonl"
    combined_valid = out_dir / "46_llm_tool_extractions_valid.jsonl"
    write_jsonl(combined_raw, raw_rows)
    write_jsonl(combined_valid, valid_rows)

    task_count = sum(len(r.get("create_task_frame", [])) for r in valid_rows)
    relation_count = sum(len(r.get("add_procedural_relation", [])) for r in valid_rows)
    rejection_count = sum(len(r.get("reject_candidate", [])) for r in valid_rows)
    parse_errors = sum(1 for r in raw_rows if r.get("parse_error") or r.get("error"))
    report = f"""# LLM Tool-Constrained Extraction Report

Generated: {datetime.now(timezone.utc).isoformat()}

## Combined Shards

- Output directory: `{out_dir}`
- Shards requested: {args.num_shards}
- Raw chunk rows: {len(raw_rows)}
- Valid chunk rows: {len(valid_rows)}
- Valid task frames: {task_count}
- Valid procedural relations: {relation_count}
- Rejected candidates: {rejection_count}
- Raw rows with parse/generation errors: {parse_errors}

Files:

- Raw model output: `{combined_raw.name}`
- Validated tool calls: `{combined_valid.name}`

## Shard Reports

"""
    report += "\n\n".join(reports)
    write_text(out_dir / "47_llm_extraction_quality_report.md", report)
    print(
        json.dumps(
            {
                "event": "merged",
                "raw_rows": len(raw_rows),
                "valid_rows": len(valid_rows),
                "task_frames": task_count,
                "relations": relation_count,
                "rejections": rejection_count,
            },
            ensure_ascii=False,
        )
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="experiments/cep_onto_jaije_20260627_gpu_llm")
    parser.add_argument("--chunk-file", default="10_chunks_hybrid_semantic.jsonl")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--quantization", choices=["4bit", "8bit", "fp16"], default="4bit")
    parser.add_argument("--max-chunks", type=int, default=None)
    parser.add_argument("--max-prompt-chars", type=int, default=5200)
    parser.add_argument("--max-new-tokens", type=int, default=1200)
    parser.add_argument("--progress-every", type=int, default=5)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--num-shards", type=int, default=1)
    parser.add_argument("--merge-shards", action="store_true")
    args = parser.parse_args()

    if args.num_shards < 1:
        raise SystemExit("--num-shards must be >= 1")
    if not 0 <= args.shard_index < args.num_shards:
        raise SystemExit("--shard-index must satisfy 0 <= shard_index < num_shards")

    if args.merge_shards:
        merge_shards(args)
    else:
        run(args)


if __name__ == "__main__":
    main()
