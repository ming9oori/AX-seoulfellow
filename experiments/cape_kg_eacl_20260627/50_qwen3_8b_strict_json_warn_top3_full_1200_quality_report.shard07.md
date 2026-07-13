# Condition-Specific LLM Baseline Report

Generated: 2026-06-28T04:48:24.489402+00:00

- Output directory: `experiments/cape_kg_eacl_20260627`
- Output prefix: `qwen3_8b_strict_json_warn_top3_full_1200`
- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218`
- Quantization: `4bit`
- Strict JSON contract: True
- CUDA_VISIBLE_DEVICES: `7`
- Chunk file: `01_data/evaluation_chunks.jsonl`
- Shard: 8 / 8
- Chunks selected: 15

## Conditions

- B2_current_project: raw_rows=15, valid_triples=0, valid_nodes=99, valid_edges=41, valid_mappings=0, parse_or_generation_error_rows=8, partial_json_repaired_rows=8
- B4_taxonomy_rag: raw_rows=15, valid_triples=0, valid_nodes=109, valid_edges=54, valid_mappings=14, parse_or_generation_error_rows=11, partial_json_repaired_rows=11
- B5_procedural_prompt: raw_rows=15, valid_triples=0, valid_nodes=174, valid_edges=47, valid_mappings=0, parse_or_generation_error_rows=11, partial_json_repaired_rows=11

## Files

- Raw outputs: `48_qwen3_8b_strict_json_warn_top3_full_1200_raw.shard07.jsonl`
- Validated outputs: `49_qwen3_8b_strict_json_warn_top3_full_1200_valid.shard07.jsonl`
