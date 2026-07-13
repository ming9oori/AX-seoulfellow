# Condition-Specific LLM Baseline Report

Generated: 2026-06-27T17:13:15.929855+00:00

- Output directory: `experiments/cape_kg_eacl_20260627`
- Output prefix: `qwen3_8b_b2_b4_condition_smoke`
- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218`
- Quantization: `4bit`
- CUDA_VISIBLE_DEVICES: `0`
- Chunk file: `01_data/evaluation_chunks.jsonl`
- Shard: 1 / 1
- Chunks selected: 5

## Conditions

- B2_current_project: raw_rows=5, valid_triples=0, valid_nodes=9, valid_edges=6, valid_mappings=0, parse_or_generation_error_rows=2
- B4_taxonomy_rag: raw_rows=5, valid_triples=0, valid_nodes=6, valid_edges=4, valid_mappings=5, parse_or_generation_error_rows=2

## Files

- Raw outputs: `48_qwen3_8b_b2_b4_condition_smoke_raw.jsonl`
- Validated outputs: `49_qwen3_8b_b2_b4_condition_smoke_valid.jsonl`
