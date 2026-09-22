#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import traceback
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import yaml


QA_V2_DIR = Path(__file__).resolve().parent
PROJECT_DIR = QA_V2_DIR.parent
WORKSPACE_DIR = PROJECT_DIR.parent
SRC_DIR = PROJECT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(QA_V2_DIR) not in sys.path:
    sys.path.insert(0, str(QA_V2_DIR))

from paraphrase_pipeline import (  # noqa: E402
    LexicalOverlapScorer,
    VARIANT_TYPES,
    build_challenge_rows,
    build_parent_records,
    load_gold_overrides,
    read_csv,
    read_jsonl,
    sha256_file,
    validate_challenge_rows,
    validate_generated_record,
    write_csv,
    write_json,
    write_jsonl,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def default_output_dir() -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return QA_V2_DIR / "generated" / f"paraphrase_v1_{stamp}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a synthetic paraphrase stress test with frozen Gold Evidence"
    )
    parser.add_argument(
        "--source-csv",
        type=Path,
        default=WORKSPACE_DIR / "AX" / "qa_dataset" / "outputs" / "full_terra_v1" / "qa_dataset.csv",
    )
    parser.add_argument(
        "--aligned-gold",
        type=Path,
        default=PROJECT_DIR / "runs" / "full_20260919" / "03_aligned_gold.jsonl",
    )
    parser.add_argument(
        "--snapshot",
        type=Path,
        default=PROJECT_DIR / "runs" / "full_20260919" / "00_graph_snapshot.json",
    )
    parser.add_argument(
        "--gold-overrides",
        type=Path,
        default=QA_V2_DIR / "paraphrase_gold_overrides.json",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_DIR / "config" / "experiment.yaml",
    )
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--limit", type=int, default=0, help="0 means all 148 official parents")
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--max-rewrite-attempts", type=int, default=2)
    parser.add_argument("--generator-model", default="")
    parser.add_argument("--validator-model", default="")
    return parser.parse_args()


def _load_config(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"YAML root must be an object: {path}")
    return value


def _snapshot_evidence_ids(path: Path) -> set[str]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return {
        str(row.get("properties", {}).get("id", ""))
        for row in value.get("evidence_spans", [])
        if row.get("properties", {}).get("id")
    }


def _qid_digest(parents: list[Mapping[str, Any]]) -> str:
    text = "\n".join(parent["qid"] for parent in parents)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_preflight(
    *,
    args: argparse.Namespace,
    config: Mapping[str, Any],
    parents: list[Mapping[str, Any]],
    overrides: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    snapshot_ids = _snapshot_evidence_ids(args.snapshot)
    unknown_ids = sorted(
        {
            evidence_id
            for parent in parents
            for evidence_id in parent["gold_evidence_span_ids"]
            if evidence_id not in snapshot_ids
        }
    )
    if unknown_ids:
        raise ValueError(f"Gold Evidence IDs absent from frozen snapshot: {unknown_ids[:20]}")
    scorer = LexicalOverlapScorer()
    overlap_bands = Counter(
        scorer.band(scorer.score(parent["question"], parent["evidence_texts"]))
        for parent in parents
    )
    evidence_counts = Counter(len(parent["gold_evidence_span_ids"]) for parent in parents)
    models = config["models"]
    generator_model = args.generator_model or models["answer_generator"]
    validator_model = (
        args.validator_model
        or models.get("paraphrase_validator")
        or generator_model
    )
    return {
        "created_at": utc_now(),
        "challenge_type": "synthetic_development_only",
        "methodological_status": (
            "Robustness diagnostic derived from source-authored questions; not an "
            "independent practitioner or real-world performance benchmark."
        ),
        "parent_count": len(parents),
        "variants_per_parent": len(VARIANT_TYPES),
        "expected_generated_question_count": len(parents) * len(VARIANT_TYPES),
        "expected_total_row_count_with_controls": len(parents) * (len(VARIANT_TYPES) + 1),
        "excluded_development_qids": list(config["evaluation"].get("development_qids", [])),
        "qid_sha256": _qid_digest(parents),
        "gold_override_qids": sorted(set(overrides) & {parent["qid"] for parent in parents}),
        "gold_evidence_count_distribution": dict(sorted(evidence_counts.items())),
        "original_question_lexical_overlap_bands": dict(sorted(overlap_bands.items())),
        "models": {"generator": generator_model, "validator": validator_model},
        "generation_privacy_contract": {
            "generator_receives": ["original_question", "variant_type_labels", "safe_failure_codes_on_retry"],
            "generator_never_receives": ["reference_answer", "evidence_text", "Gold IDs", "retrieval_results"],
            "validator_receives": ["original_question", "reference_answer", "candidate_questions"],
            "validator_never_receives": ["evidence_text", "Gold IDs", "retrieval_results"],
        },
        "inputs": {
            "source_csv": {"path": str(args.source_csv.resolve()), "sha256": sha256_file(args.source_csv)},
            "aligned_gold": {"path": str(args.aligned_gold.resolve()), "sha256": sha256_file(args.aligned_gold)},
            "snapshot": {"path": str(args.snapshot.resolve()), "sha256": sha256_file(args.snapshot)},
            "gold_overrides": {"path": str(args.gold_overrides.resolve()), "sha256": sha256_file(args.gold_overrides)},
            "config": {"path": str(args.config.resolve()), "sha256": sha256_file(args.config)},
        },
        "readiness": "preflight_passed",
    }


def _failure_codes(errors: list[str]) -> dict[str, list[str]]:
    output: dict[str, list[str]] = {variant_type: [] for variant_type in VARIANT_TYPES}
    global_codes: list[str] = []
    for error in errors:
        if ":" in error:
            variant_type, code = error.split(":", 1)
            if variant_type in output:
                output[variant_type].append(code)
                continue
        global_codes.append(error)
    if global_codes:
        for values in output.values():
            values.extend(global_codes)
    return {key: list(dict.fromkeys(values)) for key, values in output.items() if values}


def _generate_one(
    parent: Mapping[str, Any],
    backend: Any,
    *,
    max_attempts: int,
    generator_model: str,
    validator_model: str,
) -> dict[str, Any]:
    attempts: list[dict[str, Any]] = []
    prior_failure_codes: dict[str, list[str]] | None = None
    final_record: dict[str, Any] = {
        "qid": parent["qid"],
        "variants": [],
        "validations": [],
        "errors": ["not_generated"],
    }
    try:
        for attempt_number in range(1, max_attempts + 1):
            generated, generation_id, generation_cached = backend.generate_paraphrase_variants(
                question=parent["question"],
                prior_failure_codes=prior_failure_codes,
            )
            variants = generated.get("variants", [])
            validated, validation_id, validation_cached = backend.validate_paraphrase_variants(
                question=parent["question"],
                reference_answer=parent["answer"],
                variants=variants,
            )
            record = {
                "qid": parent["qid"],
                "variants": variants,
                "validations": validated.get("validations", []),
                "generation_model": generator_model,
                "generation_response_id": generation_id,
                "generation_cached": generation_cached,
                "validation_model": validator_model,
                "validation_response_id": validation_id,
                "validation_cached": validation_cached,
                "generated_at": utc_now(),
            }
            errors = validate_generated_record(parent, record)
            attempt = {
                "attempt": attempt_number,
                **record,
                "errors": errors,
            }
            attempts.append(attempt)
            final_record = {**record, "errors": errors}
            if not errors:
                break
            prior_failure_codes = _failure_codes(errors)
    except Exception as exc:
        final_record = {
            **final_record,
            "errors": [f"{type(exc).__name__}: {exc}"],
            "traceback": traceback.format_exc(limit=5),
            "generated_at": utc_now(),
        }
    return {**final_record, "attempts": attempts}


def main() -> None:
    args = parse_args()
    args.output_dir = (args.output_dir or default_output_dir()).resolve()
    if args.limit < 0:
        raise ValueError("--limit cannot be negative")
    if args.concurrency < 1:
        raise ValueError("--concurrency must be at least 1")
    if args.max_rewrite_attempts < 1:
        raise ValueError("--max-rewrite-attempts must be at least 1")

    config = _load_config(args.config)
    source_rows = read_csv(args.source_csv)
    aligned_rows = read_jsonl(args.aligned_gold)
    overrides = load_gold_overrides(args.gold_overrides)
    excluded = set(config["evaluation"].get("development_qids", []))
    parents = build_parent_records(
        source_rows,
        aligned_rows,
        excluded_qids=excluded,
        gold_overrides=overrides,
        limit=args.limit,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    preflight = build_preflight(args=args, config=config, parents=parents, overrides=overrides)
    write_json(args.output_dir / "preflight_manifest.json", preflight)
    print(
        f"[preflight] parents={len(parents)}, generated={preflight['expected_generated_question_count']}, "
        f"rows_with_controls={preflight['expected_total_row_count_with_controls']}"
    )
    print(f"[preflight] output={args.output_dir}")
    if args.prepare_only:
        return
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Preflight is complete; set the key in the process "
            "environment and rerun without --prepare-only."
        )

    from kg_rag.openai_backend import OpenAIBackend

    models = config["models"]
    generation = config["generation"]
    generator_model = args.generator_model or models["answer_generator"]
    validator_model = args.validator_model or models.get("paraphrase_validator") or generator_model
    cache_dir = (args.config.resolve().parent.parent / config["paths"]["cache_dir"]).resolve()
    backend = OpenAIBackend(
        cache_path=cache_dir / "openai_cache.sqlite",
        embedding_model=models["embedding"],
        embedding_dimensions=int(models.get("embedding_dimensions", 1024)),
        profiler_model=models["query_profiler"],
        generator_model=generator_model,
        paraphrase_validator_model=validator_model,
        reasoning_effort=models.get("reasoning_effort", "low"),
        max_retries=int(generation.get("max_retries", 5)),
    )

    records: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = {
            executor.submit(
                _generate_one,
                parent,
                backend,
                max_attempts=args.max_rewrite_attempts,
                generator_model=generator_model,
                validator_model=validator_model,
            ): parent["qid"]
            for parent in parents
        }
        for completed, future in enumerate(as_completed(futures), start=1):
            qid = futures[future]
            records[qid] = future.result()
            if completed % 10 == 0 or completed == len(futures):
                print(f"[generate+validate] {completed}/{len(futures)}")

    ordered_records = [records[parent["qid"]] for parent in parents]
    write_jsonl(args.output_dir / "paraphrase_candidates.jsonl", ordered_records)
    rows = build_challenge_rows(parents, records)
    write_csv(args.output_dir / "paraphrase_challenge_all.csv", rows)
    errors, summary = validate_challenge_rows(rows, parents, allow_incomplete=False)
    summary.update(
        {
            "created_at": utc_now(),
            "candidate_parent_failures": sum(bool(record.get("errors")) for record in ordered_records),
            "status": "ready" if not errors else "needs_review_or_regeneration",
        }
    )
    write_json(args.output_dir / "challenge_validation_summary.json", summary)
    if errors:
        write_json(args.output_dir / "challenge_validation_errors.json", errors)
        print(f"[incomplete] {len(errors)} validation errors; ready CSV was not created")
        raise SystemExit(2)
    ready_path = args.output_dir / "paraphrase_challenge_ready.csv"
    write_csv(ready_path, rows)
    print(f"[ready] {ready_path} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
