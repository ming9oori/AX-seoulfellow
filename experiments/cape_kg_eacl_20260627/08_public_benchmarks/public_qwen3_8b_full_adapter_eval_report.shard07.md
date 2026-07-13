# Public Benchmark LLM Evaluation Report

Generated: 2026-06-27T23:24:17.914343+00:00

- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218`
- Quantization: `4bit`
- CUDA_VISIBLE_DEVICES: `7`
- PAGED items: 12
- Text2KGBench items: 25
- Raw rows: 37
- Valid rows: 37
- Result rows: 37

## PAGED

- Mean node-label F1: 0.3763
- Mean edge-predicate F1: 0.4161

## Text2KGBench

- Mean relation F1: 0.592
- Mean triple exact F1: 0.2095

## Errors

{
  "PAGED:parse_error": 4,
  "PAGED:root_not_object": 4
}

## Files

- Raw outputs: `public_qwen3_8b_full_adapter_eval_raw.shard07.jsonl`
- Validated outputs: `public_qwen3_8b_full_adapter_eval_valid.shard07.jsonl`
- Item scores: `public_qwen3_8b_full_adapter_eval_results.shard07.jsonl`
- Summary: `public_qwen3_8b_full_adapter_eval_summary.shard07.json`
