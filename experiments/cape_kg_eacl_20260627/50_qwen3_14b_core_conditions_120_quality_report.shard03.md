# Condition-Specific LLM Baseline Report

Generated: 2026-06-27T22:59:56.300492+00:00

- Output directory: `experiments/cape_kg_eacl_20260627`
- Output prefix: `qwen3_14b_core_conditions_120`
- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-14B/snapshots/40c069824f4251a91eefaf281ebe4c544efd3e18`
- Quantization: `4bit`
- CUDA_VISIBLE_DEVICES: `6,7`
- Chunk file: `01_data/evaluation_chunks.jsonl`
- Shard: 4 / 4
- Chunks selected: 30

## Conditions

- B0_plain_llm: raw_rows=30, valid_triples=233, valid_nodes=0, valid_edges=0, valid_mappings=0, parse_or_generation_error_rows=16, partial_json_repaired_rows=16
- B1_predicate_constrained: raw_rows=30, valid_triples=0, valid_nodes=0, valid_edges=170, valid_mappings=0, parse_or_generation_error_rows=20, partial_json_repaired_rows=20
- B2_current_project: raw_rows=30, valid_triples=0, valid_nodes=181, valid_edges=14, valid_mappings=0, parse_or_generation_error_rows=26, partial_json_repaired_rows=26
- P_cape_kg_actual: raw_rows=30, valid_triples=0, valid_nodes=146, valid_edges=91, valid_mappings=2, parse_or_generation_error_rows=29, partial_json_repaired_rows=29

## Files

- Raw outputs: `48_qwen3_14b_core_conditions_120_raw.shard03.jsonl`
- Validated outputs: `49_qwen3_14b_core_conditions_120_valid.shard03.jsonl`
