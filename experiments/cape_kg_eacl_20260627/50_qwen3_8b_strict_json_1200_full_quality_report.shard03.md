# Condition-Specific LLM Baseline Report

Generated: 2026-06-28T03:38:05.504864+00:00

- Output directory: `experiments/cape_kg_eacl_20260627`
- Output prefix: `qwen3_8b_strict_json_1200_full`
- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218`
- Quantization: `4bit`
- Strict JSON contract: True
- CUDA_VISIBLE_DEVICES: `3`
- Chunk file: `01_data/evaluation_chunks.jsonl`
- Shard: 4 / 8
- Chunks selected: 15

## Conditions

- B0_plain_llm: raw_rows=15, valid_triples=134, valid_nodes=0, valid_edges=0, valid_mappings=0, parse_or_generation_error_rows=1, partial_json_repaired_rows=1
- B1_predicate_constrained: raw_rows=15, valid_triples=0, valid_nodes=0, valid_edges=120, valid_mappings=0, parse_or_generation_error_rows=3, partial_json_repaired_rows=3
- B2_current_project: raw_rows=15, valid_triples=0, valid_nodes=120, valid_edges=42, valid_mappings=0, parse_or_generation_error_rows=8, partial_json_repaired_rows=8
- B3_edc_style: raw_rows=15, valid_triples=0, valid_nodes=92, valid_edges=35, valid_mappings=0, parse_or_generation_error_rows=8, partial_json_repaired_rows=8
- B4_taxonomy_rag: raw_rows=15, valid_triples=0, valid_nodes=116, valid_edges=36, valid_mappings=19, parse_or_generation_error_rows=10, partial_json_repaired_rows=10
- B5_procedural_prompt: raw_rows=15, valid_triples=0, valid_nodes=196, valid_edges=26, valid_mappings=0, parse_or_generation_error_rows=10, partial_json_repaired_rows=10
- P_cape_kg_actual: raw_rows=15, valid_triples=0, valid_nodes=75, valid_edges=56, valid_mappings=31, parse_or_generation_error_rows=5, partial_json_repaired_rows=5
- P_minus_CQ: raw_rows=15, valid_triples=0, valid_nodes=75, valid_edges=56, valid_mappings=27, parse_or_generation_error_rows=6, partial_json_repaired_rows=6
- P_minus_Evidence: raw_rows=15, valid_triples=0, valid_nodes=74, valid_edges=62, valid_mappings=34, parse_or_generation_error_rows=4, partial_json_repaired_rows=4
- P_minus_Procedural_schema: raw_rows=15, valid_triples=0, valid_nodes=73, valid_edges=47, valid_mappings=26, parse_or_generation_error_rows=6, partial_json_repaired_rows=6
- P_minus_Validator: raw_rows=15, valid_triples=0, valid_nodes=75, valid_edges=57, valid_mappings=28, parse_or_generation_error_rows=6, partial_json_repaired_rows=6
- P_minus_Standard_bridge: raw_rows=15, valid_triples=0, valid_nodes=75, valid_edges=54, valid_mappings=0, parse_or_generation_error_rows=1, partial_json_repaired_rows=1
- P_minus_Schema_retrieval: raw_rows=15, valid_triples=0, valid_nodes=72, valid_edges=55, valid_mappings=26, parse_or_generation_error_rows=5, partial_json_repaired_rows=5

## Files

- Raw outputs: `48_qwen3_8b_strict_json_1200_full_raw.shard03.jsonl`
- Validated outputs: `49_qwen3_8b_strict_json_1200_full_valid.shard03.jsonl`
