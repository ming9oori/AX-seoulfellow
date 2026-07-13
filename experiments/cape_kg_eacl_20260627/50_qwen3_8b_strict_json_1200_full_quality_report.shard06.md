# Condition-Specific LLM Baseline Report

Generated: 2026-06-28T03:34:07.194503+00:00

- Output directory: `experiments/cape_kg_eacl_20260627`
- Output prefix: `qwen3_8b_strict_json_1200_full`
- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218`
- Quantization: `4bit`
- Strict JSON contract: True
- CUDA_VISIBLE_DEVICES: `6`
- Chunk file: `01_data/evaluation_chunks.jsonl`
- Shard: 7 / 8
- Chunks selected: 15

## Conditions

- B0_plain_llm: raw_rows=15, valid_triples=123, valid_nodes=0, valid_edges=0, valid_mappings=0, parse_or_generation_error_rows=2, partial_json_repaired_rows=2
- B1_predicate_constrained: raw_rows=15, valid_triples=0, valid_nodes=0, valid_edges=96, valid_mappings=0, parse_or_generation_error_rows=2, partial_json_repaired_rows=2
- B2_current_project: raw_rows=15, valid_triples=0, valid_nodes=116, valid_edges=37, valid_mappings=0, parse_or_generation_error_rows=8, partial_json_repaired_rows=8
- B3_edc_style: raw_rows=15, valid_triples=0, valid_nodes=94, valid_edges=30, valid_mappings=0, parse_or_generation_error_rows=7, partial_json_repaired_rows=7
- B4_taxonomy_rag: raw_rows=15, valid_triples=0, valid_nodes=81, valid_edges=40, valid_mappings=18, parse_or_generation_error_rows=9, partial_json_repaired_rows=9
- B5_procedural_prompt: raw_rows=15, valid_triples=0, valid_nodes=184, valid_edges=32, valid_mappings=0, parse_or_generation_error_rows=9, partial_json_repaired_rows=9
- P_cape_kg_actual: raw_rows=15, valid_triples=0, valid_nodes=75, valid_edges=50, valid_mappings=32, parse_or_generation_error_rows=4, partial_json_repaired_rows=4
- P_minus_CQ: raw_rows=15, valid_triples=0, valid_nodes=75, valid_edges=49, valid_mappings=32, parse_or_generation_error_rows=5, partial_json_repaired_rows=5
- P_minus_Evidence: raw_rows=15, valid_triples=0, valid_nodes=74, valid_edges=53, valid_mappings=28, parse_or_generation_error_rows=5, partial_json_repaired_rows=5
- P_minus_Procedural_schema: raw_rows=15, valid_triples=0, valid_nodes=72, valid_edges=48, valid_mappings=31, parse_or_generation_error_rows=5, partial_json_repaired_rows=5
- P_minus_Validator: raw_rows=15, valid_triples=0, valid_nodes=73, valid_edges=52, valid_mappings=32, parse_or_generation_error_rows=5, partial_json_repaired_rows=5
- P_minus_Standard_bridge: raw_rows=15, valid_triples=0, valid_nodes=70, valid_edges=45, valid_mappings=0, parse_or_generation_error_rows=3, partial_json_repaired_rows=3
- P_minus_Schema_retrieval: raw_rows=15, valid_triples=0, valid_nodes=73, valid_edges=51, valid_mappings=32, parse_or_generation_error_rows=3, partial_json_repaired_rows=3

## Files

- Raw outputs: `48_qwen3_8b_strict_json_1200_full_raw.shard06.jsonl`
- Validated outputs: `49_qwen3_8b_strict_json_1200_full_valid.shard06.jsonl`
