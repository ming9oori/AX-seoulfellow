#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check whether Qwen3-32B-AWQ can be used for CAPE-KG runs."""

import argparse
import importlib.util
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

try:
    from huggingface_hub import model_info, snapshot_download
except ImportError as exc:
    raise SystemExit("huggingface_hub is required for this readiness check") from exc


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_REPO_ID = "Qwen/Qwen3-32B-AWQ"
STANDARD_REPO_ID = "Qwen/Qwen3-32B"
PYTHON_ENV = Path("/home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python")


def module_available(name):
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


def patch_autoawq_transformers_compat():
    try:
        import transformers.activations as activations
    except Exception:
        return
    if not hasattr(activations, "PytorchGELUTanh") and hasattr(activations, "GELUTanh"):
        activations.PytorchGELUTanh = activations.GELUTanh


def autoawq_import_status():
    if not (module_available("autoawq") or module_available("awq")):
        return False, "not_installed"
    try:
        patch_autoawq_transformers_compat()
        import awq  # noqa: F401

        return True, ""
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def gib(bytes_value):
    return round(float(bytes_value or 0) / 1024**3, 3)


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def cache_base():
    if os.environ.get("HF_HUB_CACHE"):
        return Path(os.environ["HF_HUB_CACHE"])
    if os.environ.get("HF_HOME"):
        return Path(os.environ["HF_HOME"]) / "hub"
    return Path.home() / ".cache/huggingface/hub"


def repo_cache_dir(repo_id):
    return cache_base() / ("models--" + repo_id.replace("/", "--"))


def cached_snapshots(repo_id):
    snapshots_dir = repo_cache_dir(repo_id) / "snapshots"
    if not snapshots_dir.exists():
        return []
    return sorted(
        [path for path in snapshots_dir.iterdir() if path.is_dir()],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )


def snapshot_summaries(repo_id):
    summaries = []
    for path in cached_snapshots(repo_id):
        safetensors = sorted(path.glob("*.safetensors"))
        total = 0
        for item in safetensors:
            try:
                total += item.stat().st_size
            except OSError:
                pass
        summaries.append({
            "path": str(path),
            "safetensors_count": len(safetensors),
            "safetensors_gib": gib(total),
        })
    return summaries


def complete_snapshots(summaries, metadata):
    expected_count = int(metadata.get("safetensors_count") or 0)
    expected_gib = float(metadata.get("safetensors_gib") or 0.0)
    complete = []
    for row in summaries:
        count_ok = expected_count > 0 and int(row.get("safetensors_count") or 0) >= expected_count
        size_ok = expected_gib > 0 and float(row.get("safetensors_gib") or 0.0) >= expected_gib * 0.98
        if count_ok and size_ok:
            complete.append(row)
    return complete


def count_lines(path):
    path = Path(path)
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def qwen32_awq_core_run_summary(exp_dir):
    exp_dir = Path(exp_dir)
    raw_path = exp_dir / "48_qwen3_32b_awq_core_120_raw.jsonl"
    valid_path = exp_dir / "49_qwen3_32b_awq_core_120_valid.jsonl"
    quality_report = exp_dir / "50_qwen3_32b_awq_core_120_quality_report.md"
    silver_report = exp_dir / "04_evaluation/qwen3_32b_awq_core_silver_evaluation_report.md"
    silver_metrics = exp_dir / "04_evaluation/qwen3_32b_awq_core_silver_metrics.json"
    raw_rows = count_lines(raw_path)
    valid_rows = count_lines(valid_path)
    complete = (
        raw_rows == 480
        and valid_rows == 480
        and quality_report.exists()
        and silver_report.exists()
        and silver_metrics.exists()
    )
    return {
        "raw_file": str(raw_path) if raw_path.exists() else None,
        "valid_file": str(valid_path) if valid_path.exists() else None,
        "quality_report": str(quality_report) if quality_report.exists() else None,
        "silver_report": str(silver_report) if silver_report.exists() else None,
        "silver_metrics": str(silver_metrics) if silver_metrics.exists() else None,
        "raw_rows": raw_rows,
        "valid_rows": valid_rows,
        "expected_rows": 480,
        "complete": complete,
    }


def collect_repo_metadata(repo_id):
    info = model_info(repo_id, files_metadata=True)
    safetensors = [row for row in info.siblings if row.rfilename.endswith(".safetensors")]
    selected = [
        row for row in info.siblings
        if row.rfilename.endswith((".safetensors", ".json", ".model", ".txt", ".py", ".md"))
    ]
    return {
        "repo_id": repo_id,
        "sha": info.sha,
        "file_count": len(info.siblings),
        "safetensors_count": len(safetensors),
        "safetensors_gib": gib(sum((row.size or 0) for row in safetensors)),
        "selected_download_gib": gib(sum((row.size or 0) for row in selected)),
        "largest_files": [
            {"file": row.rfilename, "gib": gib(row.size or 0)}
            for row in sorted(info.siblings, key=lambda item: item.size or 0, reverse=True)[:5]
        ],
        "source": f"https://huggingface.co/{repo_id}",
    }


def environment_summary(path_for_disk):
    usage = shutil.disk_usage(path_for_disk)
    autoawq_importable, autoawq_import_error = autoawq_import_status()
    modules = {
        "torch": module_available("torch"),
        "transformers": module_available("transformers"),
        "accelerate": module_available("accelerate"),
        "bitsandbytes": module_available("bitsandbytes"),
        "autoawq": module_available("autoawq") or module_available("awq"),
        "autoawq_importable": autoawq_importable,
        "vllm": module_available("vllm"),
        "sglang": module_available("sglang"),
        "transformers_awq_quantizer": module_available("transformers.quantizers.quantizer_awq"),
    }
    torch_payload = {}
    if modules["torch"]:
        try:
            import torch

            torch_payload = {
                "version": getattr(torch, "__version__", ""),
                "cuda": getattr(torch.version, "cuda", ""),
                "cuda_available": bool(torch.cuda.is_available()),
                "device_count": int(torch.cuda.device_count()),
            }
        except Exception as exc:
            torch_payload = {"error": repr(exc)}
    transformers_payload = {}
    if modules["transformers"]:
        try:
            import transformers

            transformers_payload = {"version": getattr(transformers, "__version__", "")}
        except Exception as exc:
            transformers_payload = {"error": repr(exc)}
    return {
        "disk_path": str(path_for_disk),
        "disk_total_gib": gib(usage.total),
        "disk_used_gib": gib(usage.used),
        "disk_free_gib": gib(usage.free),
        "python_env": str(PYTHON_ENV),
        "modules": modules,
        "autoawq_import_error": autoawq_import_error,
        "torch": torch_payload,
        "transformers": transformers_payload,
    }


def build_report(payload):
    env = payload["environment"]
    awq = payload["awq_model"]
    standard = payload["standard_model"]
    lines = [
        "# Qwen3-32B-AWQ Readiness Check",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Status: **{payload['status']}**",
        "",
        "## Environment",
        "",
        f"- Disk free: {env['disk_free_gib']} GiB at `{env['disk_path']}`",
        f"- GPU count visible to torch: {env.get('torch', {}).get('device_count')}",
        f"- CUDA available: {env.get('torch', {}).get('cuda_available')}",
        f"- Transformers: {env.get('transformers', {}).get('version')}",
        f"- AWQ quantizer in Transformers: {env['modules'].get('transformers_awq_quantizer')}",
        f"- autoawq/awq installed: {env['modules'].get('autoawq')}",
        f"- autoawq/awq importable: {env['modules'].get('autoawq_importable')}",
        f"- autoawq import error: {env.get('autoawq_import_error') or 'none'}",
        f"- vLLM installed: {env['modules'].get('vllm')}",
        f"- SGLang installed: {env['modules'].get('sglang')}",
        "",
        "## Model Size",
        "",
        f"- `{awq['repo_id']}` safetensors: {awq['safetensors_gib']} GiB; selected download: {awq['selected_download_gib']} GiB",
        f"- `{standard['repo_id']}` safetensors: {standard['safetensors_gib']} GiB; selected download: {standard['selected_download_gib']} GiB",
        f"- AWQ complete cached snapshots: {len(payload['complete_cached_awq_snapshots'])}",
        f"- AWQ partial/config-only cached snapshots: {len(payload['partial_cached_awq_snapshots'])}",
        f"- Standard complete cached snapshots: {len(payload['complete_cached_standard_snapshots'])}",
        "",
        "## Decision",
        "",
        f"- Can download AWQ with requested headroom: {payload['can_download_awq']}",
        f"- Can load AWQ with Transformers native quantization now: {payload['can_transformers_native_awq']}",
        f"- Recommended next action: {payload['recommended_next_action']}",
        "",
    ]
    core_run = payload.get("qwen3_32b_awq_core_run") or {}
    if core_run.get("raw_file") or core_run.get("valid_file"):
        lines.extend([
            "## Completed CAPE Run",
            "",
            f"- Core run complete: {core_run.get('complete')}",
            f"- Raw rows: {core_run.get('raw_rows')} / {core_run.get('expected_rows')}",
            f"- Valid rows: {core_run.get('valid_rows')} / {core_run.get('expected_rows')}",
            f"- Quality report: `{core_run.get('quality_report')}`",
            f"- Silver report: `{core_run.get('silver_report')}`",
            f"- Silver metrics: `{core_run.get('silver_metrics')}`",
            "",
        ])
    lines.extend([
        "## Commands",
        "",
        "Check only:",
        "",
        "```bash",
        "python3 scripts/check_qwen3_32b_awq_readiness.py --experiment-dir experiments/cape_kg_eacl_20260627",
        "```",
        "",
        "Download only after runner dependencies are installed/validated:",
        "",
        "```bash",
        "python3 scripts/check_qwen3_32b_awq_readiness.py --experiment-dir experiments/cape_kg_eacl_20260627 --download",
        "```",
        "",
        "The CAPE LLM scripts now accept `--quantization native` for pre-quantized models such as AWQ snapshots.",
        "",
        "Primary sources:",
        "",
        f"- {awq['source']}",
        f"- {standard['source']}",
        "",
    ])
    return "\n".join(lines)


def run(args):
    exp_dir = Path(args.experiment_dir)
    release_dir = exp_dir / "06_release"
    env = environment_summary(Path(args.disk_path))
    awq = collect_repo_metadata(args.repo_id)
    standard = collect_repo_metadata(STANDARD_REPO_ID)
    cached_awq = snapshot_summaries(args.repo_id)
    cached_standard = snapshot_summaries(STANDARD_REPO_ID)
    complete_cached_awq = complete_snapshots(cached_awq, awq)
    complete_cached_standard = complete_snapshots(cached_standard, standard)
    partial_cached_awq = [row for row in cached_awq if row not in complete_cached_awq]
    partial_cached_standard = [row for row in cached_standard if row not in complete_cached_standard]
    can_download_awq = env["disk_free_gib"] >= (awq["selected_download_gib"] + args.min_headroom_gib)
    modules = env["modules"]
    can_transformers_native_awq = bool(
        modules.get("transformers")
        and modules.get("accelerate")
        and modules.get("transformers_awq_quantizer")
        and modules.get("autoawq_importable")
        and env.get("torch", {}).get("cuda_available")
    )
    can_vllm = bool(modules.get("vllm"))
    can_sglang = bool(modules.get("sglang"))

    if complete_cached_awq and (can_transformers_native_awq or can_vllm or can_sglang):
        status = "ready"
        recommended = "Run Qwen3-32B-AWQ smoke with --quantization native."
    elif can_download_awq and (can_transformers_native_awq or can_vllm or can_sglang):
        status = "ready_after_download"
        recommended = "Download Qwen3-32B-AWQ, then run a smoke condition."
    elif can_download_awq:
        status = "download_possible_runner_missing"
        recommended = "Install or validate autoawq, vLLM, or SGLang before downloading/running AWQ."
    else:
        status = "insufficient_disk_for_awq"
        recommended = "Free disk space before downloading Qwen3-32B-AWQ."

    core_run = qwen32_awq_core_run_summary(exp_dir)
    if core_run["complete"]:
        status = "core_run_complete"
        recommended = "Qwen3-32B-AWQ core 120-chunk run is complete; use human-gold scoring before paper claims."

    download_path = None
    download_error = None
    if args.download:
        if not can_download_awq and not complete_cached_awq:
            download_error = "insufficient_disk_headroom"
        else:
            try:
                download_path = snapshot_download(
                    repo_id=args.repo_id,
                    allow_patterns=["*.safetensors", "*.json", "*.model", "*.txt", "*.py", "*.md"],
                    local_files_only=False,
                )
                cached_awq = snapshot_summaries(args.repo_id)
                complete_cached_awq = complete_snapshots(cached_awq, awq)
                partial_cached_awq = [row for row in cached_awq if row not in complete_cached_awq]
            except Exception as exc:
                download_error = repr(exc)

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "repo_id": args.repo_id,
        "environment": env,
        "awq_model": awq,
        "standard_model": standard,
        "cached_awq_snapshots": cached_awq,
        "complete_cached_awq_snapshots": complete_cached_awq,
        "partial_cached_awq_snapshots": partial_cached_awq,
        "cached_standard_snapshots": cached_standard,
        "complete_cached_standard_snapshots": complete_cached_standard,
        "partial_cached_standard_snapshots": partial_cached_standard,
        "min_headroom_gib": args.min_headroom_gib,
        "can_download_awq": can_download_awq,
        "can_transformers_native_awq": can_transformers_native_awq,
        "can_vllm_awq": can_vllm,
        "can_sglang_awq": can_sglang,
        "download_requested": bool(args.download),
        "download_path": download_path,
        "download_error": download_error,
        "qwen3_32b_awq_core_run": core_run,
        "status": status,
        "recommended_next_action": recommended,
        "claim_status": "model_readiness_only_not_a_paper_result",
    }
    json_path = release_dir / "qwen3_32b_awq_readiness.json"
    md_path = release_dir / "qwen3_32b_awq_readiness.md"
    write_json(json_path, payload)
    write_text(md_path, build_report(payload))
    print(json.dumps({"json": str(json_path), "report": str(md_path), "status": status, "recommended_next_action": recommended}, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--repo-id", default=DEFAULT_REPO_ID)
    parser.add_argument("--disk-path", default="/home")
    parser.add_argument("--min-headroom-gib", type=float, default=10.0)
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
