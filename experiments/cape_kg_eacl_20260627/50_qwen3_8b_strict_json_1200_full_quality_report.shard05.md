# Condition-Specific LLM Baseline Report

Generated: 2026-06-28T03:50:40.561746+00:00

- Output directory: `experiments/cape_kg_eacl_20260627`
- Output prefix: `qwen3_8b_strict_json_1200_full`
- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218`
- Quantization: `4bit`
- Strict JSON contract: True
- CUDA_VISIBLE_DEVICES: `5`
- Chunk file: `01_data/evaluation_chunks.jsonl`
- Shard: 6 / 8
- Chunks selected: 15

## Conditions

- B0_plain_llm: raw_rows=15, valid_triples=179, valid_nodes=0, valid_edges=0, valid_mappings=0, parse_or_generation_error_rows=5, partial_json_repaired_rows=5
- B1_predicate_constrained: raw_rows=15, valid_triples=0, valid_nodes=0, valid_edges=124, valid_mappings=0, parse_or_generation_error_rows=5, partial_json_repaired_rows=5
- B2_current_project: raw_rows=15, valid_triples=0, valid_nodes=128, valid_edges=30, valid_mappings=0, parse_or_generation_error_rows=11, partial_json_repaired_rows=11
- B3_edc_style: raw_rows=15, valid_triples=0, valid_nodes=101, valid_edges=24, valid_mappings=0, parse_or_generation_error_rows=8, partial_json_repaired_rows=8
- B4_taxonomy_rag: raw_rows=15, valid_triples=0, valid_nodes=78, valid_edges=30, valid_mappings=6, parse_or_generation_error_rows=11, partial_json_repaired_rows=11
- B5_procedural_prompt: raw_rows=15, valid_triples=0, valid_nodes=153, valid_edges=24, valid_mappings=0, parse_or_generation_error_rows=10, partial_json_repaired_rows=10
- P_cape_kg_actual: raw_rows=15, valid_triples=0, valid_nodes=66, valid_edges=40, valid_mappings=21, parse_or_generation_error_rows=7, partial_json_repaired_rows=7
- P_minus_CQ: raw_rows=15, valid_triples=0, valid_nodes=70, valid_edges=41, valid_mappings=24, parse_or_generation_error_rows=8, partial_json_repaired_rows=8
- P_minus_Evidence: raw_rows=15, valid_triples=0, valid_nodes=68, valid_edges=33, valid_mappings=19, parse_or_generation_error_rows=8, partial_json_repaired_rows=8
- P_minus_Procedural_schema: raw_rows=15, valid_triples=0, valid_nodes=67, valid_edges=36, valid_mappings=19, parse_or_generation_error_rows=8, partial_json_repaired_rows=8
- P_minus_Validator: raw_rows=15, valid_triples=0, valid_nodes=64, valid_edges=35, valid_mappings=22, parse_or_generation_error_rows=7, partial_json_repaired_rows=7
- P_minus_Standard_bridge: raw_rows=15, valid_triples=0, valid_nodes=73, valid_edges=47, valid_mappings=0, parse_or_generation_error_rows=4, partial_json_repaired_rows=4
- P_minus_Schema_retrieval: raw_rows=15, valid_triples=0, valid_nodes=70, valid_edges=48, valid_mappings=20, parse_or_generation_error_rows=7, partial_json_repaired_rows=7

## Files

- Raw outputs: `48_qwen3_8b_strict_json_1200_full_raw.shard05.jsonl`
- Validated outputs: `49_qwen3_8b_strict_json_1200_full_valid.shard05.jsonl`
