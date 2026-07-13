# Public Benchmark LLM Evaluation Report

Generated: 2026-06-27T23:25:04.369453+00:00

- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218`
- Quantization: `4bit`
- CUDA_VISIBLE_DEVICES: `1`
- PAGED items: 13
- Text2KGBench items: 25
- Raw rows: 38
- Valid rows: 38
- Result rows: 38

## PAGED

- Mean node-label F1: 0.154
- Mean edge-predicate F1: 0.465

## Text2KGBench

- Mean relation F1: 0.6573
- Mean triple exact F1: 0.184

## Errors

{
  "PAGED:missing_edge_endpoint": 6,
  "PAGED:parse_error": 4,
  "PAGED:root_not_object": 4,
  "Text2KGBench:unknown_relation": 2
}

## Files

- Raw outputs: `public_qwen3_8b_full_adapter_eval_raw.shard01.jsonl`
- Validated outputs: `public_qwen3_8b_full_adapter_eval_valid.shard01.jsonl`
- Item scores: `public_qwen3_8b_full_adapter_eval_results.shard01.jsonl`
- Summary: `public_qwen3_8b_full_adapter_eval_summary.shard01.json`
