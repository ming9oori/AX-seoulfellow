# Condition-Specific LLM Baseline Report

Generated: 2026-06-28T03:58:39.686738+00:00

- Output directory: `experiments/cape_kg_eacl_20260627`
- Output prefix: `qwen3_8b_strict_json_warn_top3_smoke_1200`
- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218`
- Quantization: `4bit`
- Strict JSON contract: True
- CUDA_VISIBLE_DEVICES: `0`
- Chunk file: `01_data/evaluation_chunks.jsonl`
- Shard: 1 / 1
- Chunks selected: 4

## Conditions

- B2_current_project: raw_rows=4, valid_triples=0, valid_nodes=14, valid_edges=11, valid_mappings=0, parse_or_generation_error_rows=0, partial_json_repaired_rows=0
- B4_taxonomy_rag: raw_rows=4, valid_triples=0, valid_nodes=14, valid_edges=10, valid_mappings=8, parse_or_generation_error_rows=0, partial_json_repaired_rows=0
- B5_procedural_prompt: raw_rows=4, valid_triples=0, valid_nodes=20, valid_edges=16, valid_mappings=0, parse_or_generation_error_rows=0, partial_json_repaired_rows=0

## Files

- Raw outputs: `48_qwen3_8b_strict_json_warn_top3_smoke_1200_raw.jsonl`
- Validated outputs: `49_qwen3_8b_strict_json_warn_top3_smoke_1200_valid.jsonl`
