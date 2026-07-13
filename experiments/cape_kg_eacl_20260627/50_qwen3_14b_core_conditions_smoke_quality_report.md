# Condition-Specific LLM Baseline Report

Generated: 2026-06-27T21:35:28.238711+00:00

- Output directory: `experiments/cape_kg_eacl_20260627`
- Output prefix: `qwen3_14b_core_conditions_smoke`
- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-14B/snapshots/40c069824f4251a91eefaf281ebe4c544efd3e18`
- Quantization: `4bit`
- CUDA_VISIBLE_DEVICES: `0,1`
- Chunk file: `01_data/evaluation_chunks.jsonl`
- Shard: 1 / 1
- Chunks selected: 4

## Conditions

- B0_plain_llm: raw_rows=4, valid_triples=13, valid_nodes=0, valid_edges=0, valid_mappings=0, parse_or_generation_error_rows=0, partial_json_repaired_rows=0
- B1_predicate_constrained: raw_rows=4, valid_triples=0, valid_nodes=0, valid_edges=5, valid_mappings=0, parse_or_generation_error_rows=0, partial_json_repaired_rows=0
- B2_current_project: raw_rows=4, valid_triples=0, valid_nodes=14, valid_edges=6, valid_mappings=0, parse_or_generation_error_rows=2, partial_json_repaired_rows=2
- P_cape_kg_actual: raw_rows=4, valid_triples=0, valid_nodes=20, valid_edges=10, valid_mappings=0, parse_or_generation_error_rows=4, partial_json_repaired_rows=4

## Files

- Raw outputs: `48_qwen3_14b_core_conditions_smoke_raw.jsonl`
- Validated outputs: `49_qwen3_14b_core_conditions_smoke_valid.jsonl`
