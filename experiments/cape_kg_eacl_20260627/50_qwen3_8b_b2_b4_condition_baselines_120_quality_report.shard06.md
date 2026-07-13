# Condition-Specific LLM Baseline Report

Generated: 2026-06-27T17:29:14.329307+00:00

- Output directory: `experiments/cape_kg_eacl_20260627`
- Output prefix: `qwen3_8b_b2_b4_condition_baselines_120`
- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218`
- Quantization: `4bit`
- CUDA_VISIBLE_DEVICES: `6`
- Chunk file: `01_data/evaluation_chunks.jsonl`
- Shard: 7 / 8
- Chunks selected: 15

## Conditions

- B2_current_project: raw_rows=15, valid_triples=0, valid_nodes=11, valid_edges=7, valid_mappings=0, parse_or_generation_error_rows=12
- B4_taxonomy_rag: raw_rows=15, valid_triples=0, valid_nodes=5, valid_edges=3, valid_mappings=3, parse_or_generation_error_rows=13

## Files

- Raw outputs: `48_qwen3_8b_b2_b4_condition_baselines_120_raw.shard06.jsonl`
- Validated outputs: `49_qwen3_8b_b2_b4_condition_baselines_120_valid.shard06.jsonl`
