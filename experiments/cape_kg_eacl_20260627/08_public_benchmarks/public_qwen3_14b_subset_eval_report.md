# Public Benchmark LLM Evaluation Report

Generated: 2026-06-27T23:14:52.432795+00:00

- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-14B/snapshots/40c069824f4251a91eefaf281ebe4c544efd3e18`
- Quantization: `4bit`
- CUDA_VISIBLE_DEVICES: `0,1`
- PAGED items: 10
- Text2KGBench items: 20

## PAGED

- Mean node-label F1: 0.1733
- Mean edge-predicate F1: 0.1446

## Text2KGBench

- Mean relation F1: 0.2817
- Mean triple exact F1: 0.02

## Errors

{
  "PAGED:parse_error": 6,
  "PAGED:root_not_object": 6,
  "PAGED:unknown_predicate": 1,
  "Text2KGBench:unknown_relation": 1
}

## Files

- Raw outputs: `public_qwen3_14b_subset_eval_raw.jsonl`
- Validated outputs: `public_qwen3_14b_subset_eval_valid.jsonl`
- Item scores: `public_qwen3_14b_subset_eval_results.jsonl`
- Summary: `public_qwen3_14b_subset_eval_summary.json`
