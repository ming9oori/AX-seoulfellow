# Public Benchmark LLM Evaluation Report

Generated: 2026-06-27T23:24:15.480329+00:00

- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218`
- Quantization: `4bit`
- CUDA_VISIBLE_DEVICES: `6`
- PAGED items: 12
- Text2KGBench items: 25
- Raw rows: 37
- Valid rows: 37
- Result rows: 37

## PAGED

- Mean node-label F1: 0.2593
- Mean edge-predicate F1: 0.5073

## Text2KGBench

- Mean relation F1: 0.6229
- Mean triple exact F1: 0.1741

## Errors

{
  "PAGED:missing_edge_endpoint": 12,
  "PAGED:parse_error": 2,
  "PAGED:root_not_object": 2,
  "Text2KGBench:unknown_relation": 2
}

## Files

- Raw outputs: `public_qwen3_8b_full_adapter_eval_raw.shard06.jsonl`
- Validated outputs: `public_qwen3_8b_full_adapter_eval_valid.shard06.jsonl`
- Item scores: `public_qwen3_8b_full_adapter_eval_results.shard06.jsonl`
- Summary: `public_qwen3_8b_full_adapter_eval_summary.shard06.json`
