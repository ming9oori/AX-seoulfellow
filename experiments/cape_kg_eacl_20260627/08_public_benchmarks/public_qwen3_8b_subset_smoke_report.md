# Public Benchmark LLM Evaluation Report

Generated: 2026-06-27T17:36:32.898943+00:00

- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218`
- Quantization: `4bit`
- CUDA_VISIBLE_DEVICES: `0`
- PAGED items: 3
- Text2KGBench items: 5

## PAGED

- Mean node-label F1: 0.0
- Mean edge-predicate F1: 0.1333

## Text2KGBench

- Mean relation F1: 0.4
- Mean triple exact F1: 0.0

## Errors

{
  "PAGED:parse_error": 2,
  "PAGED:root_not_object": 2,
  "Text2KGBench:unknown_relation": 1
}

## Files

- Raw outputs: `public_qwen3_8b_subset_smoke_raw.jsonl`
- Validated outputs: `public_qwen3_8b_subset_smoke_valid.jsonl`
- Item scores: `public_qwen3_8b_subset_smoke_results.jsonl`
- Summary: `public_qwen3_8b_subset_smoke_summary.json`
