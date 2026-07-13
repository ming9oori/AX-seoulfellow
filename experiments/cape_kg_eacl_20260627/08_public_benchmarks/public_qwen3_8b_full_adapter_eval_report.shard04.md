# Public Benchmark LLM Evaluation Report

Generated: 2026-06-27T23:24:39.069697+00:00

- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218`
- Quantization: `4bit`
- CUDA_VISIBLE_DEVICES: `4`
- PAGED items: 12
- Text2KGBench items: 25
- Raw rows: 37
- Valid rows: 37
- Result rows: 37

## PAGED

- Mean node-label F1: 0.229
- Mean edge-predicate F1: 0.3351

## Text2KGBench

- Mean relation F1: 0.516
- Mean triple exact F1: 0.2027

## Errors

{
  "PAGED:missing_edge_endpoint": 2,
  "PAGED:parse_error": 5,
  "PAGED:root_not_object": 5,
  "Text2KGBench:parse_error": 1,
  "Text2KGBench:root_not_object": 1,
  "Text2KGBench:unknown_relation": 1
}

## Files

- Raw outputs: `public_qwen3_8b_full_adapter_eval_raw.shard04.jsonl`
- Validated outputs: `public_qwen3_8b_full_adapter_eval_valid.shard04.jsonl`
- Item scores: `public_qwen3_8b_full_adapter_eval_results.shard04.jsonl`
- Summary: `public_qwen3_8b_full_adapter_eval_summary.shard04.json`
