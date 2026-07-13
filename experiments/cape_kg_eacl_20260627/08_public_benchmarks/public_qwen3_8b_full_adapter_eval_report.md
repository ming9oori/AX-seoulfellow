# Public Benchmark LLM Evaluation Report

Generated: 2026-06-27T23:25:19.574290+00:00

- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218`
- Quantization: `4bit`
- CUDA_VISIBLE_DEVICES: ``
- PAGED items: 100
- Text2KGBench items: 200
- Raw rows: 300
- Valid rows: 300
- Result rows: 300

## PAGED

- Mean node-label F1: 0.2472
- Mean edge-predicate F1: 0.4233

## Text2KGBench

- Mean relation F1: 0.6015
- Mean triple exact F1: 0.1736

## Errors

{
  "PAGED:missing_edge_endpoint": 21,
  "PAGED:parse_error": 34,
  "PAGED:root_not_object": 34,
  "Text2KGBench:parse_error": 1,
  "Text2KGBench:root_not_object": 1,
  "Text2KGBench:unknown_relation": 9
}

## Files

- Raw outputs: `public_qwen3_8b_full_adapter_eval_raw.jsonl`
- Validated outputs: `public_qwen3_8b_full_adapter_eval_valid.jsonl`
- Item scores: `public_qwen3_8b_full_adapter_eval_results.jsonl`
- Summary: `public_qwen3_8b_full_adapter_eval_summary.json`
