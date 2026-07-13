# Public Benchmark LLM Evaluation Report

Generated: 2026-06-27T17:40:46.074606+00:00

- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218`
- Quantization: `4bit`
- CUDA_VISIBLE_DEVICES: `1`
- PAGED items: 10
- Text2KGBench items: 20

## PAGED

- Mean node-label F1: 0.1608
- Mean edge-predicate F1: 0.1794

## Text2KGBench

- Mean relation F1: 0.45
- Mean triple exact F1: 0.05

## Errors

{
  "PAGED:parse_error": 6,
  "PAGED:root_not_object": 6,
  "Text2KGBench:unknown_relation": 2
}

## Files

- Raw outputs: `public_qwen3_8b_subset_eval_raw.jsonl`
- Validated outputs: `public_qwen3_8b_subset_eval_valid.jsonl`
- Item scores: `public_qwen3_8b_subset_eval_results.jsonl`
- Summary: `public_qwen3_8b_subset_eval_summary.json`
