# Public Benchmark LLM Evaluation Report

Generated: 2026-06-27T23:24:38.286202+00:00

- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218`
- Quantization: `4bit`
- CUDA_VISIBLE_DEVICES: `3`
- PAGED items: 13
- Text2KGBench items: 25
- Raw rows: 38
- Valid rows: 38
- Result rows: 38

## PAGED

- Mean node-label F1: 0.2517
- Mean edge-predicate F1: 0.2553

## Text2KGBench

- Mean relation F1: 0.5413
- Mean triple exact F1: 0.136

## Errors

{
  "PAGED:parse_error": 7,
  "PAGED:root_not_object": 7
}

## Files

- Raw outputs: `public_qwen3_8b_full_adapter_eval_raw.shard03.jsonl`
- Validated outputs: `public_qwen3_8b_full_adapter_eval_valid.shard03.jsonl`
- Item scores: `public_qwen3_8b_full_adapter_eval_results.shard03.jsonl`
- Summary: `public_qwen3_8b_full_adapter_eval_summary.shard03.json`
