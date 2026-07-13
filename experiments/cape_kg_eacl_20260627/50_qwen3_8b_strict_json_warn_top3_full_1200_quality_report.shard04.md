# Condition-Specific LLM Baseline Report

Generated: 2026-06-28T04:43:26.539618+00:00

- Output directory: `experiments/cape_kg_eacl_20260627`
- Output prefix: `qwen3_8b_strict_json_warn_top3_full_1200`
- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218`
- Quantization: `4bit`
- Strict JSON contract: True
- CUDA_VISIBLE_DEVICES: `4`
- Chunk file: `01_data/evaluation_chunks.jsonl`
- Shard: 5 / 8
- Chunks selected: 15

## Conditions

- B2_current_project: raw_rows=15, valid_triples=0, valid_nodes=91, valid_edges=41, valid_mappings=0, parse_or_generation_error_rows=8, partial_json_repaired_rows=8
- B4_taxonomy_rag: raw_rows=15, valid_triples=0, valid_nodes=74, valid_edges=26, valid_mappings=17, parse_or_generation_error_rows=8, partial_json_repaired_rows=8
- B5_procedural_prompt: raw_rows=15, valid_triples=0, valid_nodes=145, valid_edges=48, valid_mappings=0, parse_or_generation_error_rows=10, partial_json_repaired_rows=10

## Files

- Raw outputs: `48_qwen3_8b_strict_json_warn_top3_full_1200_raw.shard04.jsonl`
- Validated outputs: `49_qwen3_8b_strict_json_warn_top3_full_1200_valid.shard04.jsonl`
