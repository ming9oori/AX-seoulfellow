#!/usr/bin/env python3
"""Run Qwen-style LLM predictions on public benchmark adapter subsets."""

import argparse
import json
import os
import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from run_cep_onto_llm_extraction import DEFAULT_MODEL, generate_json, load_model, parse_json_object


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")


def read_jsonl(path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
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


def norm(text):
    text = "" if text is None else str(text).lower()
    text = re.sub(r"[^a-z0-9가-힣]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def f1(tp, pred_total, gold_total):
    precision = tp / pred_total if pred_total else 0.0
    recall = tp / gold_total if gold_total else 0.0
    score = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return round(precision, 4), round(recall, 4), round(score, 4)


def truncate_text(text, max_chars):
    text = str(text or "")
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0]


def build_paged_prompt(row, max_chars):
    text = truncate_text(row.get("text", ""), max_chars)
    user = f"""
Extract a procedural graph from the document.
Return ONLY one valid JSON object. No markdown. No explanation.

JSON shape:
{{
  "nodes": [
    {{"label": "short action/artifact/condition label", "type": "ProcedureStep|Artifact|GuardCondition|Role"}}
  ],
  "edges": [
    {{"source_label": "node label", "predicate": "PRECEDES|USES_INPUT|PRODUCES|ASSOCIATED_WITH", "target_label": "node label", "condition": "optional condition"}}
  ]
}}

Document:
{text}
""".strip()
    return [
        {"role": "system", "content": "You extract procedural graph JSON from text."},
        {"role": "user", "content": user},
    ]


def build_text2kg_prompt(row, max_chars):
    text = truncate_text(row.get("text", ""), max_chars)
    ontology_relations = row.get("ontology_relations", [])[:80]
    ontology_concepts = row.get("ontology_concepts", [])[:80]
    user = f"""
Extract ontology-guided KG triples from the sentence.
Return ONLY one valid JSON object. No markdown. No explanation.
Use only relation labels from the allowed ontology relations.

Allowed concepts:
{json.dumps(ontology_concepts, ensure_ascii=False)}

Allowed relations:
{json.dumps(ontology_relations, ensure_ascii=False)}

JSON shape:
{{
  "triples": [
    {{"sub": "subject text", "rel": "allowed relation label", "obj": "object text"}}
  ]
}}

Sentence:
{text}
""".strip()
    return [
        {"role": "system", "content": "You extract ontology-guided triples as JSON."},
        {"role": "user", "content": user},
    ]


def validate_paged(parsed):
    valid = {"nodes": [], "edges": []}
    errors = Counter()
    if not isinstance(parsed, dict):
        errors["root_not_object"] += 1
        return valid, errors
    for item in parsed.get("nodes", []) if isinstance(parsed.get("nodes", []), list) else []:
        if not isinstance(item, dict):
            errors["node_not_object"] += 1
            continue
        label = str(item.get("label", "")).strip()
        node_type = str(item.get("type", "")).strip()
        if not label:
            errors["missing_node_label"] += 1
            continue
        valid["nodes"].append({"label": label[:160], "type": node_type[:60]})
    allowed_predicates = {"PRECEDES", "USES_INPUT", "PRODUCES", "ASSOCIATED_WITH"}
    for item in parsed.get("edges", []) if isinstance(parsed.get("edges", []), list) else []:
        if not isinstance(item, dict):
            errors["edge_not_object"] += 1
            continue
        source = str(item.get("source_label", "")).strip()
        target = str(item.get("target_label", "")).strip()
        predicate = str(item.get("predicate", "")).strip().upper()
        if predicate not in allowed_predicates:
            errors["unknown_predicate"] += 1
            continue
        if not source or not target:
            errors["missing_edge_endpoint"] += 1
            continue
        valid["edges"].append(
            {
                "source_label": source[:160],
                "predicate": predicate,
                "target_label": target[:160],
                "condition": str(item.get("condition", "")).strip()[:160],
            }
        )
    return valid, errors


def validate_text2kg(parsed, allowed_relations):
    valid = {"triples": []}
    errors = Counter()
    if not isinstance(parsed, dict):
        errors["root_not_object"] += 1
        return valid, errors
    allowed = {norm(r) for r in allowed_relations}
    for item in parsed.get("triples", []) if isinstance(parsed.get("triples", []), list) else []:
        if not isinstance(item, dict):
            errors["triple_not_object"] += 1
            continue
        sub = str(item.get("sub", "")).strip()
        rel = str(item.get("rel", "")).strip()
        obj = str(item.get("obj", "")).strip()
        if not sub or not rel or not obj:
            errors["missing_triple_field"] += 1
            continue
        if allowed and norm(rel) not in allowed:
            errors["unknown_relation"] += 1
            continue
        valid["triples"].append({"sub": sub[:160], "rel": rel[:120], "obj": obj[:160]})
    return valid, errors


def score_paged(row, valid):
    gold_labels = {norm(n.get("label")) for n in row.get("gold_nodes", []) if norm(n.get("label"))}
    pred_labels = {norm(n.get("label")) for n in valid.get("nodes", []) if norm(n.get("label"))}
    node_tp = len(gold_labels & pred_labels)
    node_precision, node_recall, node_f1 = f1(node_tp, len(pred_labels), len(gold_labels))

    gold_predicates = Counter(e.get("predicate", "") for e in row.get("gold_edges", []))
    pred_predicates = Counter(e.get("predicate", "") for e in valid.get("edges", []))
    edge_predicate_tp = sum(min(pred_predicates[p], gold_predicates[p]) for p in set(pred_predicates) | set(gold_predicates))
    edge_precision, edge_recall, edge_f1 = f1(edge_predicate_tp, sum(pred_predicates.values()), sum(gold_predicates.values()))
    return {
        "gold_nodes": len(gold_labels),
        "pred_nodes": len(pred_labels),
        "node_label_precision": node_precision,
        "node_label_recall": node_recall,
        "node_label_f1": node_f1,
        "gold_edges": sum(gold_predicates.values()),
        "pred_edges": sum(pred_predicates.values()),
        "edge_predicate_precision": edge_precision,
        "edge_predicate_recall": edge_recall,
        "edge_predicate_f1": edge_f1,
    }


def score_text2kg(row, valid):
    gold_triples = {(norm(t.get("sub")), norm(t.get("rel")), norm(t.get("obj"))) for t in row.get("gold_triples", [])}
    pred_triples = {(norm(t.get("sub")), norm(t.get("rel")), norm(t.get("obj"))) for t in valid.get("triples", [])}
    triple_tp = len(gold_triples & pred_triples)
    triple_precision, triple_recall, triple_f1 = f1(triple_tp, len(pred_triples), len(gold_triples))
    gold_relations = {norm(t.get("rel")) for t in row.get("gold_triples", [])}
    pred_relations = {norm(t.get("rel")) for t in valid.get("triples", [])}
    relation_tp = len(gold_relations & pred_relations)
    relation_precision, relation_recall, relation_f1 = f1(relation_tp, len(pred_relations), len(gold_relations))
    return {
        "gold_triples": len(gold_triples),
        "pred_triples": len(pred_triples),
        "triple_exact_precision": triple_precision,
        "triple_exact_recall": triple_recall,
        "triple_exact_f1": triple_f1,
        "relation_precision": relation_precision,
        "relation_recall": relation_recall,
        "relation_f1": relation_f1,
    }


def mean(rows, key):
    vals = [r.get("scores", {}).get(key, 0.0) for r in rows]
    return round(sum(vals) / len(vals), 4) if vals else 0.0


def output_paths(out_dir, prefix, shard_index=None):
    suffix = "" if shard_index is None else f".shard{shard_index:02d}"
    return {
        "raw": out_dir / f"{prefix}_raw{suffix}.jsonl",
        "valid": out_dir / f"{prefix}_valid{suffix}.jsonl",
        "results": out_dir / f"{prefix}_results{suffix}.jsonl",
        "summary": out_dir / f"{prefix}_summary{suffix}.json",
        "report": out_dir / f"{prefix}_report{suffix}.md",
    }


def select_jobs(jobs, shard_index, num_shards):
    if num_shards <= 1:
        return jobs
    return [job for idx, job in enumerate(jobs) if idx % num_shards == shard_index]


def build_summary(args, paths, raw_rows, valid_rows, result_rows, errors, shard_index=None, shard_summaries=None):
    paged_result_rows = [r for r in result_rows if r.get("benchmark") == "PAGED"]
    text2kg_result_rows = [r for r in result_rows if r.get("benchmark") == "Text2KGBench"]
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "model": args.model,
        "quantization": args.quantization,
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES", ""),
        "paged_items": len(paged_result_rows),
        "text2kg_items": len(text2kg_result_rows),
        "raw_rows": len(raw_rows),
        "valid_rows": len(valid_rows),
        "result_rows": len(result_rows),
        "errors": dict(errors),
        "paged": {
            "mean_node_label_f1": mean(paged_result_rows, "node_label_f1"),
            "mean_edge_predicate_f1": mean(paged_result_rows, "edge_predicate_f1"),
        },
        "text2kg": {
            "mean_relation_f1": mean(text2kg_result_rows, "relation_f1"),
            "mean_triple_exact_f1": mean(text2kg_result_rows, "triple_exact_f1"),
        },
        "files": {
            "raw": str(paths["raw"]),
            "valid": str(paths["valid"]),
            "results": str(paths["results"]),
            "report": str(paths["report"]),
        },
    }
    if shard_index is not None:
        summary["is_shard"] = True
        summary["shard_index"] = shard_index
        summary["num_shards"] = args.num_shards
    else:
        summary["is_shard"] = False
        if args.num_shards > 1:
            summary["merged_shards"] = args.num_shards
            summary["shard_summaries"] = shard_summaries or []
    return summary


def write_summary_report(paths, summary):
    write_json(paths["summary"], summary)
    report = f"""# Public Benchmark LLM Evaluation Report

Generated: {summary['generated_at_utc']}

- Model: `{summary['model']}`
- Quantization: `{summary['quantization']}`
- CUDA_VISIBLE_DEVICES: `{summary['cuda_visible_devices']}`
- PAGED items: {summary['paged_items']}
- Text2KGBench items: {summary['text2kg_items']}
- Raw rows: {summary.get('raw_rows', '')}
- Valid rows: {summary.get('valid_rows', '')}
- Result rows: {summary.get('result_rows', '')}

## PAGED

- Mean node-label F1: {summary['paged']['mean_node_label_f1']}
- Mean edge-predicate F1: {summary['paged']['mean_edge_predicate_f1']}

## Text2KGBench

- Mean relation F1: {summary['text2kg']['mean_relation_f1']}
- Mean triple exact F1: {summary['text2kg']['mean_triple_exact_f1']}

## Errors

{json.dumps(summary['errors'], ensure_ascii=False, indent=2, sort_keys=True)}

## Files

- Raw outputs: `{paths['raw'].name}`
- Validated outputs: `{paths['valid'].name}`
- Item scores: `{paths['results'].name}`
- Summary: `{paths['summary'].name}`
"""
    write_text(paths["report"], report)


def merge_shards(args):
    exp_dir = Path(args.experiment_dir)
    out_dir = exp_dir / "08_public_benchmarks"
    paths = output_paths(out_dir, args.output_prefix)
    raw_rows = []
    valid_rows = []
    result_rows = []
    errors = Counter()
    shard_summaries = []
    for shard_index in range(args.num_shards):
        shard_paths = output_paths(out_dir, args.output_prefix, shard_index)
        raw_rows.extend(read_jsonl(shard_paths["raw"]) if shard_paths["raw"].exists() else [])
        valid_rows.extend(read_jsonl(shard_paths["valid"]) if shard_paths["valid"].exists() else [])
        result_rows.extend(read_jsonl(shard_paths["results"]) if shard_paths["results"].exists() else [])
        if shard_paths["summary"].exists():
            summary = json.loads(shard_paths["summary"].read_text(encoding="utf-8"))
            shard_summaries.append(str(shard_paths["summary"]))
            errors.update(summary.get("errors") or {})
    write_jsonl(paths["raw"], raw_rows)
    write_jsonl(paths["valid"], valid_rows)
    write_jsonl(paths["results"], result_rows)
    summary = build_summary(args, paths, raw_rows, valid_rows, result_rows, errors, shard_summaries=shard_summaries)
    write_summary_report(paths, summary)
    print(json.dumps({"event": "merged", **summary}, ensure_ascii=False, indent=2))


def run(args):
    exp_dir = Path(args.experiment_dir)
    out_dir = exp_dir / "08_public_benchmarks"
    paged_rows = read_jsonl(out_dir / "paged_cape_adapter_subset.jsonl")[: args.max_paged]
    text2kg_rows = read_jsonl(out_dir / "text2kgbench_cape_adapter_subset.jsonl")[: args.max_text2kg]

    all_jobs = [("PAGED", row) for row in paged_rows] + [("Text2KGBench", row) for row in text2kg_rows]
    jobs = select_jobs(all_jobs, args.shard_index, args.num_shards)
    paths = output_paths(out_dir, args.output_prefix, args.shard_index if args.num_shards > 1 else None)

    tokenizer, model = load_model(args.model, args.quantization)
    raw_rows = []
    valid_rows = []
    result_rows = []
    errors = Counter()
    started = time.time()

    for idx, (benchmark, row) in enumerate(jobs, 1):
        item_id = row.get("item_id")
        try:
            if benchmark == "PAGED":
                messages = build_paged_prompt(row, args.max_prompt_chars)
            else:
                messages = build_text2kg_prompt(row, args.max_prompt_chars)
            raw_text = generate_json(tokenizer, model, messages, args.max_new_tokens)
            parsed, parse_error = parse_json_object(raw_text)
            if parse_error:
                errors[f"{benchmark}:parse_error"] += 1
            if benchmark == "PAGED":
                valid, validation_errors = validate_paged(parsed)
                scores = score_paged(row, valid)
            else:
                valid, validation_errors = validate_text2kg(parsed, row.get("ontology_relations", []))
                scores = score_text2kg(row, valid)
            for key, value in validation_errors.items():
                errors[f"{benchmark}:{key}"] += value
        except Exception as exc:
            raw_text = ""
            parsed = None
            parse_error = None
            valid = {"nodes": [], "edges": [], "triples": []}
            scores = {}
            errors[f"{benchmark}:generation_exception"] += 1
            raw_rows.append(
                {
                    "benchmark": benchmark,
                    "item_id": item_id,
                    "error": f"{type(exc).__name__}: {exc}",
                    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                }
            )
            continue

        raw_rows.append(
            {
                "benchmark": benchmark,
                "item_id": item_id,
                "raw_text": raw_text,
                "parsed": parsed,
                "parse_error": parse_error,
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            }
        )
        valid_rows.append({"benchmark": benchmark, "item_id": item_id, "valid": valid})
        result_rows.append({"benchmark": benchmark, "item_id": item_id, "scores": scores})
        if idx % max(1, args.progress_every) == 0:
            print(
                json.dumps(
                    {
                        "event": "progress",
                        "processed": idx,
                        "total": len(jobs),
                        "all_jobs": len(all_jobs),
                        "shard_index": args.shard_index,
                        "num_shards": args.num_shards,
                        "benchmark": benchmark,
                        "elapsed_sec": round(time.time() - started, 1),
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )

    write_jsonl(paths["raw"], raw_rows)
    write_jsonl(paths["valid"], valid_rows)
    write_jsonl(paths["results"], result_rows)
    summary = build_summary(
        args,
        paths,
        raw_rows,
        valid_rows,
        result_rows,
        errors,
        shard_index=args.shard_index if args.num_shards > 1 else None,
    )
    write_summary_report(paths, summary)
    print(json.dumps({"event": "done", **summary}, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--quantization", choices=["native", "4bit", "8bit", "fp16"], default="4bit")
    parser.add_argument("--output-prefix", default="public_qwen3_8b_subset_eval")
    parser.add_argument("--max-paged", type=int, default=10)
    parser.add_argument("--max-text2kg", type=int, default=20)
    parser.add_argument("--max-prompt-chars", type=int, default=2800)
    parser.add_argument("--max-new-tokens", type=int, default=550)
    parser.add_argument("--progress-every", type=int, default=5)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--num-shards", type=int, default=1)
    parser.add_argument("--merge-shards", action="store_true")
    args = parser.parse_args()
    if args.num_shards < 1:
        raise SystemExit("--num-shards must be >= 1")
    if args.shard_index < 0 or args.shard_index >= args.num_shards:
        raise SystemExit("--shard-index must satisfy 0 <= shard-index < num-shards")
    if args.merge_shards:
        merge_shards(args)
    else:
        run(args)


if __name__ == "__main__":
    main()
