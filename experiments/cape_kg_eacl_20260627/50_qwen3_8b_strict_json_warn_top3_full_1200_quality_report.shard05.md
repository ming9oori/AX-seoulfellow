# Condition-Specific LLM Baseline Report

Generated: 2026-06-28T04:47:38.030904+00:00

- Output directory: `experiments/cape_kg_eacl_20260627`
- Output prefix: `qwen3_8b_strict_json_warn_top3_full_1200`
- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218`
- Quantization: `4bit`
- Strict JSON contract: True
- CUDA_VISIBLE_DEVICES: `5`
- Chunk file: `01_data/evaluation_chunks.jsonl`
- Shard: 6 / 8
- Chunks selected: 15

## Conditions

- B2_current_project: raw_rows=15, valid_triples=0, valid_nodes=128, valid_edges=30, valid_mappings=0, parse_or_generation_error_rows=11, partial_json_repaired_rows=11
- B4_taxonomy_rag: raw_rows=15, valid_triples=0, valid_nodes=78, valid_edges=30, valid_mappings=6, parse_or_generation_error_rows=11, partial_json_repaired_rows=11
- B5_procedural_prompt: raw_rows=15, valid_triples=0, valid_nodes=153, valid_edges=24, valid_mappings=0, parse_or_generation_error_rows=10, partial_json_repaired_rows=10

## Files

- Raw outputs: `48_qwen3_8b_strict_json_warn_top3_full_1200_raw.shard05.jsonl`
- Validated outputs: `49_qwen3_8b_strict_json_warn_top3_full_1200_valid.shard05.jsonl`
