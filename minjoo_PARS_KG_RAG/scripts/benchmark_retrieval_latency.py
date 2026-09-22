#!/usr/bin/env python3
"""Benchmark warm-cache query-to-Top-5 retrieval latency by method.

The benchmark deliberately excludes one-time graph-index and model-loading time.
For Aspect methods it reports both retrieval-only latency and standalone pipeline
latency, where the amortized P1-G Aspect extraction cost is added once per query.
OpenAI embeddings are read from the experiment cache; this is a method-overhead
benchmark, not an uncached production-service SLA measurement.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import random
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any, Mapping, Sequence


BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"
for path in (BASE_DIR, SRC_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from kg_rag.evaluation import load_qa_csv
from kg_rag.reranking import CrossEncoderReranker
from kg_rag.retrieval import P1_RERANK_METHODS, GraphIndex, QPARetriever
from kg_rag.unsupervised_aspects import (
    P1G_PCF_GROUNDED,
    P1G_PROFILE_FREE,
    P1P_PARS,
    P1P_PARS_PROFILE_FREE,
    PCFGroundedAspectExtractor,
)
from run_experiment import build_backend, resolve_config


ASPECT_RETRIEVAL_METHODS = {
    P1G_PROFILE_FREE,
    P1P_PARS,
    P1P_PARS_PROFILE_FREE,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark per-query retrieval latency for a completed run"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=BASE_DIR
        / "config"
        / "experiment_ablation.yaml",
    )
    parser.add_argument(
        "--source-run",
        type=Path,
        required=True,
        help="Run directory containing 00_graph_snapshot.json",
    )
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--limit", type=int, default=0, help="0 means all selected rows")
    parser.add_argument("--seed", type=int, default=20260922)
    parser.add_argument(
        "--include-development",
        action="store_true",
        help="Benchmark all rows instead of the official main-comparison split",
    )
    return parser.parse_args()


def percentile(values: Sequence[float], probability: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(float(value) for value in values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def summarize(values: Sequence[float]) -> dict[str, float | int]:
    samples = [float(value) for value in values]
    return {
        "n": len(samples),
        "mean_seconds": statistics.fmean(samples) if samples else 0.0,
        "median_seconds": statistics.median(samples) if samples else 0.0,
        "p95_seconds": percentile(samples, 0.95),
        "standard_deviation_seconds": (
            statistics.stdev(samples) if len(samples) > 1 else 0.0
        ),
        "minimum_seconds": min(samples, default=0.0),
        "maximum_seconds": max(samples, default=0.0),
    }


def clear_cross_encoder_cache(reranker: CrossEncoderReranker | None) -> None:
    if reranker is not None:
        reranker._score_cache.clear()  # benchmark isolation across methods


def synchronize_cuda(reranker: CrossEncoderReranker | None) -> None:
    if reranker is None or not reranker.device.startswith("cuda"):
        return
    reranker._torch.cuda.synchronize()


def method_aspects(
    method: str,
    qid: str,
    aspect_by_qid: Mapping[str, Mapping[str, Any]],
) -> Mapping[str, Any] | None:
    if method not in ASPECT_RETRIEVAL_METHODS:
        return None
    return aspect_by_qid.get(qid, {}).get(P1G_PCF_GROUNDED)


def git_revision() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=BASE_DIR,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def main() -> None:
    args = parse_args()
    if args.repeats < 1:
        raise ValueError("--repeats must be at least 1")
    if args.warmup < 0:
        raise ValueError("--warmup cannot be negative")

    config = resolve_config(args.config)
    source_run = args.source_run.resolve()
    output_path = (
        args.output.resolve()
        if args.output
        else source_run / "metrics" / "retrieval_latency_benchmark.json"
    )
    snapshot_path = source_run / "00_graph_snapshot.json"
    if not snapshot_path.exists():
        raise FileNotFoundError(snapshot_path)

    qa_rows = load_qa_csv(Path(config["paths"]["qa_csv"]), require_answers=False)
    development_qids = set(config["evaluation"].get("development_qids", []))
    if not args.include_development:
        qa_rows = [
            row for row in qa_rows if str(row["qa_id"]) not in development_qids
        ]
    if args.limit:
        qa_rows = qa_rows[: args.limit]
    if not qa_rows:
        raise RuntimeError("No QA rows selected for the benchmark")

    with snapshot_path.open(encoding="utf-8") as handle:
        snapshot = json.load(handle)
    # Construct the OpenAI-backed cache reader without allowing a network call.
    # Any cache miss therefore fails immediately instead of changing the timing
    # scope, incurring cost, or writing new embeddings during the benchmark.
    os.environ.setdefault("OPENAI_API_KEY", "cache-only-placeholder")
    backend = build_backend(config)
    backend.client = None

    print("[latency] building graph index; excluded from per-query timing")
    graph_started = perf_counter()
    graph = GraphIndex(
        snapshot,
        backend,
        embedding_batch_size=int(config["retrieval"]["embedding_batch_size"]),
    )
    graph_index_seconds = perf_counter() - graph_started

    print("[latency] extracting P1-G Aspects with warm embedding cache")
    aspect_extractor = PCFGroundedAspectExtractor(
        backend,
        graph,
        config.get("pcf_grounded_aspect", {}),
    )
    aspect_started = perf_counter()
    aspect_rows = aspect_extractor.extract_many(qa_rows)
    aspect_total_seconds = perf_counter() - aspect_started
    aspect_mean_seconds = aspect_total_seconds / len(qa_rows)
    aspect_by_qid = {
        str(row["qid"]): row.get("variants", {}) for row in aspect_rows
    }

    methods = [str(method) for method in config["methods"]]
    cross_encoder: CrossEncoderReranker | None = None
    if set(methods) & set(P1_RERANK_METHODS):
        print("[latency] loading cross-encoder; excluded from per-query timing")
        reranker_started = perf_counter()
        cross_encoder = CrossEncoderReranker(
            config["retrieval"]["p0_cross_encoder_rerank"]
        )
        reranker_load_seconds = perf_counter() - reranker_started
    else:
        reranker_load_seconds = 0.0
    retriever = QPARetriever(
        graph,
        config["retrieval"],
        cross_encoder=cross_encoder,
    )

    warmup_rows = qa_rows[: min(args.warmup, len(qa_rows))]
    if warmup_rows:
        print(f"[latency] warmup {len(warmup_rows)} questions x {len(methods)} methods")
    for row in warmup_rows:
        for method in methods:
            clear_cross_encoder_cache(cross_encoder)
            retriever.retrieve(
                qid=str(row["qa_id"]),
                question=str(row["question"]),
                method=method,
                condition="D0_ORIGINAL",
                profile=None,
                aspects=method_aspects(
                    method,
                    str(row["qa_id"]),
                    aspect_by_qid,
                ),
            )
    clear_cross_encoder_cache(cross_encoder)

    randomizer = random.Random(args.seed)
    timings: dict[str, list[float]] = {method: [] for method in methods}
    per_query: list[dict[str, Any]] = []
    total_cases = len(qa_rows) * len(methods) * args.repeats
    completed = 0
    print(f"[latency] measuring {total_cases} isolated retrieval cases")
    for repeat in range(1, args.repeats + 1):
        ordered_rows = list(qa_rows)
        randomizer.shuffle(ordered_rows)
        for row in ordered_rows:
            ordered_methods = list(methods)
            randomizer.shuffle(ordered_methods)
            for method in ordered_methods:
                clear_cross_encoder_cache(cross_encoder)
                uses_reranker = method in P1_RERANK_METHODS
                if uses_reranker:
                    synchronize_cuda(cross_encoder)
                started = perf_counter()
                result = retriever.retrieve(
                    qid=str(row["qa_id"]),
                    question=str(row["question"]),
                    method=method,
                    condition="D0_ORIGINAL",
                    profile=None,
                    aspects=method_aspects(
                        method,
                        str(row["qa_id"]),
                        aspect_by_qid,
                    ),
                )
                if uses_reranker:
                    synchronize_cuda(cross_encoder)
                elapsed = perf_counter() - started
                timings[method].append(elapsed)
                per_query.append(
                    {
                        "repeat": repeat,
                        "qid": str(row["qa_id"]),
                        "method": method,
                        "retrieval_seconds": elapsed,
                        "evidence_count": len(result.get("evidence", [])),
                        "status": result.get("status", ""),
                    }
                )
                completed += 1
                if completed % 100 == 0 or completed == total_cases:
                    print(f"[latency] {completed}/{total_cases}")

    summaries: dict[str, dict[str, Any]] = {}
    for method in methods:
        retrieval = summarize(timings[method])
        aspect_cost = aspect_mean_seconds if method in ASPECT_RETRIEVAL_METHODS else 0.0
        summaries[method] = {
            **retrieval,
            "aspect_extraction_seconds_per_query": aspect_cost,
            "pipeline_mean_seconds_per_query": (
                float(retrieval["mean_seconds"]) + aspect_cost
            ),
            "pipeline_scope": (
                "P1-G Aspect extraction + retrieval"
                if method in ASPECT_RETRIEVAL_METHODS
                else "retrieval"
            ),
        }

    hardware: dict[str, Any] = {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "cuda_visible_devices": os.getenv("CUDA_VISIBLE_DEVICES", ""),
    }
    if cross_encoder is not None:
        hardware.update(
            {
                "torch": cross_encoder._torch.__version__,
                "cuda_device": cross_encoder.device,
                "gpu": (
                    cross_encoder._torch.cuda.get_device_name()
                    if cross_encoder.device.startswith("cuda")
                    else ""
                ),
            }
        )

    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_revision": git_revision(),
        "source_run": str(source_run),
        "config": str(args.config.resolve()),
        "scope": {
            "split": "all" if args.include_development else "main_comparison",
            "question_count": len(qa_rows),
            "repeats": args.repeats,
            "warmup_question_count": len(warmup_rows),
            "condition": "D0_ORIGINAL",
            "definition": "question-to-Top-5 warm-cache retrieval latency",
            "embedding_cache": "warm SQLite cache",
            "network_access_for_embeddings": "disabled; any cache miss fails",
            "aspect_accounting": (
                "standalone Aspect methods add amortized batch P1-G extraction time"
            ),
            "cross_method_cache_isolation": (
                "cross-encoder score cache cleared before every measured case"
            ),
            "excluded": [
                "one-time graph-index construction",
                "one-time cross-encoder model loading",
                "uncached OpenAI embedding network latency",
                "answer generation and verification API latency",
                "offline metric computation",
            ],
        },
        "one_time_seconds": {
            "graph_index": graph_index_seconds,
            "cross_encoder_load": reranker_load_seconds,
        },
        "aspect_extraction": {
            "total_seconds": aspect_total_seconds,
            "mean_seconds_per_query": aspect_mean_seconds,
        },
        "hardware": hardware,
        "methods": summaries,
        "per_query": per_query,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(f"[latency] wrote {output_path}")
    for method, summary in summaries.items():
        print(
            f"[latency] {method}: retrieval={summary['mean_seconds']:.4f}s, "
            f"pipeline={summary['pipeline_mean_seconds_per_query']:.4f}s/query"
        )


if __name__ == "__main__":
    main()
