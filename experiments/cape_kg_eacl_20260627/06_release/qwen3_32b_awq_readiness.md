# Qwen3-32B-AWQ Readiness Check

Generated: 2026-06-29T15:31:56.571803+00:00
Status: **core_run_complete**

## Environment

- Disk free: 24.529 GiB at `/home`
- GPU count visible to torch: None
- CUDA available: None
- Transformers: 4.36.1
- AWQ quantizer in Transformers: False
- autoawq/awq installed: False
- autoawq/awq importable: False
- autoawq import error: not_installed
- vLLM installed: False
- SGLang installed: False

## Model Size

- `Qwen/Qwen3-32B-AWQ` safetensors: 17.998 GiB; selected download: 18.013 GiB
- `Qwen/Qwen3-32B` safetensors: 61.024 GiB; selected download: 61.039 GiB
- AWQ complete cached snapshots: 1
- AWQ partial/config-only cached snapshots: 0
- Standard complete cached snapshots: 0

## Decision

- Can download AWQ with requested headroom: False
- Can load AWQ with Transformers native quantization now: False
- Recommended next action: Qwen3-32B-AWQ core 120-chunk run is complete; use human-gold scoring before paper claims.

## Completed CAPE Run

- Core run complete: True
- Raw rows: 480 / 480
- Valid rows: 480 / 480
- Quality report: `experiments/cape_kg_eacl_20260627/50_qwen3_32b_awq_core_120_quality_report.md`
- Silver report: `experiments/cape_kg_eacl_20260627/04_evaluation/qwen3_32b_awq_core_silver_evaluation_report.md`
- Silver metrics: `experiments/cape_kg_eacl_20260627/04_evaluation/qwen3_32b_awq_core_silver_metrics.json`

## Commands

Check only:

```bash
python3 scripts/check_qwen3_32b_awq_readiness.py --experiment-dir experiments/cape_kg_eacl_20260627
```

Download only after runner dependencies are installed/validated:

```bash
python3 scripts/check_qwen3_32b_awq_readiness.py --experiment-dir experiments/cape_kg_eacl_20260627 --download
```

The CAPE LLM scripts now accept `--quantization native` for pre-quantized models such as AWQ snapshots.

Primary sources:

- https://huggingface.co/Qwen/Qwen3-32B-AWQ
- https://huggingface.co/Qwen/Qwen3-32B
