# Condition-Specific LLM Baseline Report

Generated: 2026-06-27T22:55:33.043398+00:00

- Output directory: `experiments/cape_kg_eacl_20260627`
- Output prefix: `qwen3_14b_core_conditions_120`
- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-14B/snapshots/40c069824f4251a91eefaf281ebe4c544efd3e18`
- Quantization: `4bit`
- CUDA_VISIBLE_DEVICES: `0,1`
- Chunk file: `01_data/evaluation_chunks.jsonl`
- Shard: 1 / 4
- Chunks selected: 30

## Conditions

- B0_plain_llm: raw_rows=30, valid_triples=219, valid_nodes=0, valid_edges=0, valid_mappings=0, parse_or_generation_error_rows=15, partial_json_repaired_rows=15
- B1_predicate_constrained: raw_rows=30, valid_triples=0, valid_nodes=0, valid_edges=146, valid_mappings=0, parse_or_generation_error_rows=19, partial_json_repaired_rows=19
- B2_current_project: raw_rows=30, valid_triples=0, valid_nodes=178, valid_edges=13, valid_mappings=0, parse_or_generation_error_rows=25, partial_json_repaired_rows=25
- P_cape_kg_actual: raw_rows=30, valid_triples=0, valid_nodes=150, valid_edges=92, valid_mappings=2, parse_or_generation_error_rows=27, partial_json_repaired_rows=27

## Files

- Raw outputs: `48_qwen3_14b_core_conditions_120_raw.shard00.jsonl`
- Validated outputs: `49_qwen3_14b_core_conditions_120_valid.shard00.jsonl`
