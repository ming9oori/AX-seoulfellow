# Condition-Specific LLM Baseline Report

Generated: 2026-06-28T03:50:44.141627+00:00

## Combined Shards

- Output directory: `experiments/cape_kg_eacl_20260627`
- Output prefix: `qwen3_8b_strict_json_1200_full`
- Shards requested: 8
- Raw rows: 1560
- Valid rows: 1560

## Conditions

- B0_plain_llm: raw_rows=120, valid_triples=1037, valid_nodes=0, valid_edges=0, valid_mappings=0, parse_or_generation_error_rows=16, partial_json_repaired_rows=16
- B1_predicate_constrained: raw_rows=120, valid_triples=0, valid_nodes=0, valid_edges=805, valid_mappings=0, parse_or_generation_error_rows=17, partial_json_repaired_rows=17
- B2_current_project: raw_rows=120, valid_triples=0, valid_nodes=867, valid_edges=334, valid_mappings=0, parse_or_generation_error_rows=63, partial_json_repaired_rows=63
- B3_edc_style: raw_rows=120, valid_triples=0, valid_nodes=769, valid_edges=263, valid_mappings=0, parse_or_generation_error_rows=59, partial_json_repaired_rows=59
- B4_taxonomy_rag: raw_rows=120, valid_triples=0, valid_nodes=719, valid_edges=323, valid_mappings=126, parse_or_generation_error_rows=76, partial_json_repaired_rows=76
- B5_procedural_prompt: raw_rows=120, valid_triples=0, valid_nodes=1307, valid_edges=302, valid_mappings=0, parse_or_generation_error_rows=76, partial_json_repaired_rows=76
- P_cape_kg_actual: raw_rows=120, valid_triples=0, valid_nodes=576, valid_edges=373, valid_mappings=227, parse_or_generation_error_rows=43, partial_json_repaired_rows=43
- P_minus_CQ: raw_rows=120, valid_triples=0, valid_nodes=586, valid_edges=391, valid_mappings=233, parse_or_generation_error_rows=48, partial_json_repaired_rows=48
- P_minus_Evidence: raw_rows=120, valid_triples=0, valid_nodes=574, valid_edges=383, valid_mappings=227, parse_or_generation_error_rows=39, partial_json_repaired_rows=39
- P_minus_Procedural_schema: raw_rows=120, valid_triples=0, valid_nodes=558, valid_edges=353, valid_mappings=212, parse_or_generation_error_rows=42, partial_json_repaired_rows=42
- P_minus_Schema_retrieval: raw_rows=120, valid_triples=0, valid_nodes=568, valid_edges=417, valid_mappings=216, parse_or_generation_error_rows=31, partial_json_repaired_rows=31
- P_minus_Standard_bridge: raw_rows=120, valid_triples=0, valid_nodes=577, valid_edges=405, valid_mappings=0, parse_or_generation_error_rows=16, partial_json_repaired_rows=16
- P_minus_Validator: raw_rows=120, valid_triples=0, valid_nodes=570, valid_edges=375, valid_mappings=229, parse_or_generation_error_rows=43, partial_json_repaired_rows=43

## Files

- Raw outputs: `48_qwen3_8b_strict_json_1200_full_raw.jsonl`
- Validated outputs: `49_qwen3_8b_strict_json_1200_full_valid.jsonl`

## Shard Reports

# Condition-Specific LLM Baseline Report

Generated: 2026-06-28T03:31:01.407904+00:00

- Output directory: `experiments/cape_kg_eacl_20260627`
- Output prefix: `qwen3_8b_strict_json_1200_full`
- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218`
- Quantization: `4bit`
- Strict JSON contract: True
- CUDA_VISIBLE_DEVICES: `0`
- Chunk file: `01_data/evaluation_chunks.jsonl`
- Shard: 1 / 8
- Chunks selected: 15

## Conditions

- B0_plain_llm: raw_rows=15, valid_triples=96, valid_nodes=0, valid_edges=0, valid_mappings=0, parse_or_generation_error_rows=1, partial_json_repaired_rows=1
- B1_predicate_constrained: raw_rows=15, valid_triples=0, valid_nodes=0, valid_edges=93, valid_mappings=0, parse_or_generation_error_rows=2, partial_json_repaired_rows=2
- B2_current_project: raw_rows=15, valid_triples=0, valid_nodes=106, valid_edges=50, valid_mappings=0, parse_or_generation_error_rows=7, partial_json_repaired_rows=7
- B3_edc_style: raw_rows=15, valid_triples=0, valid_nodes=91, valid_edges=42, valid_mappings=0, parse_or_generation_error_rows=6, partial_json_repaired_rows=6
- B4_taxonomy_rag: raw_rows=15, valid_triples=0, valid_nodes=88, valid_edges=56, valid_mappings=20, parse_or_generation_error_rows=9, partial_json_repaired_rows=9
- B5_procedural_prompt: raw_rows=15, valid_triples=0, valid_nodes=166, valid_edges=43, valid_mappings=0, parse_or_generation_error_rows=8, partial_json_repaired_rows=8
- P_cape_kg_actual: raw_rows=15, valid_triples=0, valid_nodes=76, valid_edges=52, valid_mappings=31, parse_or_generation_error_rows=5, partial_json_repaired_rows=5
- P_minus_CQ: raw_rows=15, valid_triples=0, valid_nodes=76, valid_edges=58, valid_mappings=38, parse_or_generation_error_rows=4, partial_json_repaired_rows=4
- P_minus_Evidence: raw_rows=15, valid_triples=0, valid_nodes=74, valid_edges=50, valid_mappings=31, parse_or_generation_error_rows=3, partial_json_repaired_rows=3
- P_minus_Procedural_schema: raw_rows=15, valid_triples=0, valid_nodes=69, valid_edges=51, valid_mappings=35, parse_or_generation_error_rows=2, partial_json_repaired_rows=2
- P_minus_Validator: raw_rows=15, valid_triples=0, valid_nodes=74, valid_edges=50, valid_mappings=28, parse_or_generation_error_rows=5, partial_json_repaired_rows=5
- P_minus_Standard_bridge: raw_rows=15, valid_triples=0, valid_nodes=74, valid_edges=57, valid_mappings=0, parse_or_generation_error_rows=1, partial_json_repaired_rows=1
- P_minus_Schema_retrieval: raw_rows=15, valid_triples=0, valid_nodes=74, valid_edges=60, valid_mappings=32, parse_or_generation_error_rows=1, partial_json_repaired_rows=1

## Files

- Raw outputs: `48_qwen3_8b_strict_json_1200_full_raw.shard00.jsonl`
- Validated outputs: `49_qwen3_8b_strict_json_1200_full_valid.shard00.jsonl`


# Condition-Specific LLM Baseline Report

Generated: 2026-06-28T03:40:07.010725+00:00

- Output directory: `experiments/cape_kg_eacl_20260627`
- Output prefix: `qwen3_8b_strict_json_1200_full`
- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218`
- Quantization: `4bit`
- Strict JSON contract: True
- CUDA_VISIBLE_DEVICES: `1`
- Chunk file: `01_data/evaluation_chunks.jsonl`
- Shard: 2 / 8
- Chunks selected: 15

## Conditions

- B0_plain_llm: raw_rows=15, valid_triples=132, valid_nodes=0, valid_edges=0, valid_mappings=0, parse_or_generation_error_rows=2, partial_json_repaired_rows=2
- B1_predicate_constrained: raw_rows=15, valid_triples=0, valid_nodes=0, valid_edges=99, valid_mappings=0, parse_or_generation_error_rows=3, partial_json_repaired_rows=3
- B2_current_project: raw_rows=15, valid_triples=0, valid_nodes=103, valid_edges=43, valid_mappings=0, parse_or_generation_error_rows=8, partial_json_repaired_rows=8
- B3_edc_style: raw_rows=15, valid_triples=0, valid_nodes=105, valid_edges=33, valid_mappings=0, parse_or_generation_error_rows=7, partial_json_repaired_rows=7
- B4_taxonomy_rag: raw_rows=15, valid_triples=0, valid_nodes=93, valid_edges=39, valid_mappings=15, parse_or_generation_error_rows=9, partial_json_repaired_rows=9
- B5_procedural_prompt: raw_rows=15, valid_triples=0, valid_nodes=132, valid_edges=36, valid_mappings=0, parse_or_generation_error_rows=11, partial_json_repaired_rows=11
- P_cape_kg_actual: raw_rows=15, valid_triples=0, valid_nodes=70, valid_edges=41, valid_mappings=31, parse_or_generation_error_rows=5, partial_json_repaired_rows=5
- P_minus_CQ: raw_rows=15, valid_triples=0, valid_nodes=73, valid_edges=49, valid_mappings=33, parse_or_generation_error_rows=5, partial_json_repaired_rows=5
- P_minus_Evidence: raw_rows=15, valid_triples=0, valid_nodes=70, valid_edges=45, valid_mappings=31, parse_or_generation_error_rows=4, partial_json_repaired_rows=4
- P_minus_Procedural_schema: raw_rows=15, valid_triples=0, valid_nodes=72, valid_edges=40, valid_mappings=30, parse_or_generation_error_rows=5, partial_json_repaired_rows=5
- P_minus_Validator: raw_rows=15, valid_triples=0, valid_nodes=70, valid_edges=40, valid_mappings=30, parse_or_generation_error_rows=5, partial_json_repaired_rows=5
- P_minus_Standard_bridge: raw_rows=15, valid_triples=0, valid_nodes=73, valid_edges=51, valid_mappings=0, parse_or_generation_error_rows=2, partial_json_repaired_rows=2
- P_minus_Schema_retrieval: raw_rows=15, valid_triples=0, valid_nodes=74, valid_edges=51, valid_mappings=23, parse_or_generation_error_rows=6, partial_json_repaired_rows=6

## Files

- Raw outputs: `48_qwen3_8b_strict_json_1200_full_raw.shard01.jsonl`
- Validated outputs: `49_qwen3_8b_strict_json_1200_full_valid.shard01.jsonl`


# Condition-Specific LLM Baseline Report

Generated: 2026-06-28T03:30:44.144091+00:00

- Output directory: `experiments/cape_kg_eacl_20260627`
- Output prefix: `qwen3_8b_strict_json_1200_full`
- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218`
- Quantization: `4bit`
- Strict JSON contract: True
- CUDA_VISIBLE_DEVICES: `2`
- Chunk file: `01_data/evaluation_chunks.jsonl`
- Shard: 3 / 8
- Chunks selected: 15

## Conditions

- B0_plain_llm: raw_rows=15, valid_triples=126, valid_nodes=0, valid_edges=0, valid_mappings=0, parse_or_generation_error_rows=2, partial_json_repaired_rows=2
- B1_predicate_constrained: raw_rows=15, valid_triples=0, valid_nodes=0, valid_edges=90, valid_mappings=0, parse_or_generation_error_rows=2, partial_json_repaired_rows=2
- B2_current_project: raw_rows=15, valid_triples=0, valid_nodes=104, valid_edges=50, valid_mappings=0, parse_or_generation_error_rows=5, partial_json_repaired_rows=5
- B3_edc_style: raw_rows=15, valid_triples=0, valid_nodes=100, valid_edges=30, valid_mappings=0, parse_or_generation_error_rows=7, partial_json_repaired_rows=7
- B4_taxonomy_rag: raw_rows=15, valid_triples=0, valid_nodes=80, valid_edges=42, valid_mappings=17, parse_or_generation_error_rows=9, partial_json_repaired_rows=9
- B5_procedural_prompt: raw_rows=15, valid_triples=0, valid_nodes=157, valid_edges=46, valid_mappings=0, parse_or_generation_error_rows=7, partial_json_repaired_rows=7
- P_cape_kg_actual: raw_rows=15, valid_triples=0, valid_nodes=74, valid_edges=55, valid_mappings=34, parse_or_generation_error_rows=4, partial_json_repaired_rows=4
- P_minus_CQ: raw_rows=15, valid_triples=0, valid_nodes=72, valid_edges=54, valid_mappings=29, parse_or_generation_error_rows=6, partial_json_repaired_rows=6
- P_minus_Evidence: raw_rows=15, valid_triples=0, valid_nodes=71, valid_edges=54, valid_mappings=34, parse_or_generation_error_rows=4, partial_json_repaired_rows=4
- P_minus_Procedural_schema: raw_rows=15, valid_triples=0, valid_nodes=70, valid_edges=56, valid_mappings=28, parse_or_generation_error_rows=3, partial_json_repaired_rows=3
- P_minus_Validator: raw_rows=15, valid_triples=0, valid_nodes=73, valid_edges=57, valid_mappings=31, parse_or_generation_error_rows=5, partial_json_repaired_rows=5
- P_minus_Standard_bridge: raw_rows=15, valid_triples=0, valid_nodes=71, valid_edges=56, valid_mappings=0, parse_or_generation_error_rows=0, partial_json_repaired_rows=0
- P_minus_Schema_retrieval: raw_rows=15, valid_triples=0, valid_nodes=66, valid_edges=54, valid_mappings=32, parse_or_generation_error_rows=2, partial_json_repaired_rows=2

## Files

- Raw outputs: `48_qwen3_8b_strict_json_1200_full_raw.shard02.jsonl`
- Validated outputs: `49_qwen3_8b_strict_json_1200_full_valid.shard02.jsonl`


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


# Condition-Specific LLM Baseline Report

Generated: 2026-06-28T03:30:01.304509+00:00

- Output directory: `experiments/cape_kg_eacl_20260627`
- Output prefix: `qwen3_8b_strict_json_1200_full`
- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218`
- Quantization: `4bit`
- Strict JSON contract: True
- CUDA_VISIBLE_DEVICES: `4`
- Chunk file: `01_data/evaluation_chunks.jsonl`
- Shard: 5 / 8
- Chunks selected: 15

## Conditions

- B0_plain_llm: raw_rows=15, valid_triples=109, valid_nodes=0, valid_edges=0, valid_mappings=0, parse_or_generation_error_rows=1, partial_json_repaired_rows=1
- B1_predicate_constrained: raw_rows=15, valid_triples=0, valid_nodes=0, valid_edges=84, valid_mappings=0, parse_or_generation_error_rows=0, partial_json_repaired_rows=0
- B2_current_project: raw_rows=15, valid_triples=0, valid_nodes=91, valid_edges=41, valid_mappings=0, parse_or_generation_error_rows=8, partial_json_repaired_rows=8
- B3_edc_style: raw_rows=15, valid_triples=0, valid_nodes=90, valid_edges=36, valid_mappings=0, parse_or_generation_error_rows=8, partial_json_repaired_rows=8
- B4_taxonomy_rag: raw_rows=15, valid_triples=0, valid_nodes=74, valid_edges=26, valid_mappings=17, parse_or_generation_error_rows=8, partial_json_repaired_rows=8
- B5_procedural_prompt: raw_rows=15, valid_triples=0, valid_nodes=145, valid_edges=48, valid_mappings=0, parse_or_generation_error_rows=10, partial_json_repaired_rows=10
- P_cape_kg_actual: raw_rows=15, valid_triples=0, valid_nodes=67, valid_edges=34, valid_mappings=18, parse_or_generation_error_rows=7, partial_json_repaired_rows=7
- P_minus_CQ: raw_rows=15, valid_triples=0, valid_nodes=72, valid_edges=39, valid_mappings=23, parse_or_generation_error_rows=7, partial_json_repaired_rows=7
- P_minus_Evidence: raw_rows=15, valid_triples=0, valid_nodes=70, valid_edges=39, valid_mappings=23, parse_or_generation_error_rows=5, partial_json_repaired_rows=5
- P_minus_Procedural_schema: raw_rows=15, valid_triples=0, valid_nodes=63, valid_edges=31, valid_mappings=19, parse_or_generation_error_rows=5, partial_json_repaired_rows=5
- P_minus_Validator: raw_rows=15, valid_triples=0, valid_nodes=70, valid_edges=39, valid_mappings=26, parse_or_generation_error_rows=5, partial_json_repaired_rows=5
- P_minus_Standard_bridge: raw_rows=15, valid_triples=0, valid_nodes=68, valid_edges=42, valid_mappings=0, parse_or_generation_error_rows=4, partial_json_repaired_rows=4
- P_minus_Schema_retrieval: raw_rows=15, valid_triples=0, valid_nodes=66, valid_edges=47, valid_mappings=24, parse_or_generation_error_rows=4, partial_json_repaired_rows=4

## Files

- Raw outputs: `48_qwen3_8b_strict_json_1200_full_raw.shard04.jsonl`
- Validated outputs: `49_qwen3_8b_strict_json_1200_full_valid.shard04.jsonl`


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


# Condition-Specific LLM Baseline Report

Generated: 2026-06-28T03:38:12.613340+00:00

- Output directory: `experiments/cape_kg_eacl_20260627`
- Output prefix: `qwen3_8b_strict_json_1200_full`
- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218`
- Quantization: `4bit`
- Strict JSON contract: True
- CUDA_VISIBLE_DEVICES: `7`
- Chunk file: `01_data/evaluation_chunks.jsonl`
- Shard: 8 / 8
- Chunks selected: 15

## Conditions

- B0_plain_llm: raw_rows=15, valid_triples=138, valid_nodes=0, valid_edges=0, valid_mappings=0, parse_or_generation_error_rows=2, partial_json_repaired_rows=2
- B1_predicate_constrained: raw_rows=15, valid_triples=0, valid_nodes=0, valid_edges=99, valid_mappings=0, parse_or_generation_error_rows=0, partial_json_repaired_rows=0
- B2_current_project: raw_rows=15, valid_triples=0, valid_nodes=99, valid_edges=41, valid_mappings=0, parse_or_generation_error_rows=8, partial_json_repaired_rows=8
- B3_edc_style: raw_rows=15, valid_triples=0, valid_nodes=96, valid_edges=33, valid_mappings=0, parse_or_generation_error_rows=8, partial_json_repaired_rows=8
- B4_taxonomy_rag: raw_rows=15, valid_triples=0, valid_nodes=109, valid_edges=54, valid_mappings=14, parse_or_generation_error_rows=11, partial_json_repaired_rows=11
- B5_procedural_prompt: raw_rows=15, valid_triples=0, valid_nodes=174, valid_edges=47, valid_mappings=0, parse_or_generation_error_rows=11, partial_json_repaired_rows=11
- P_cape_kg_actual: raw_rows=15, valid_triples=0, valid_nodes=73, valid_edges=45, valid_mappings=29, parse_or_generation_error_rows=6, partial_json_repaired_rows=6
- P_minus_CQ: raw_rows=15, valid_triples=0, valid_nodes=73, valid_edges=45, valid_mappings=27, parse_or_generation_error_rows=7, partial_json_repaired_rows=7
- P_minus_Evidence: raw_rows=15, valid_triples=0, valid_nodes=73, valid_edges=47, valid_mappings=27, parse_or_generation_error_rows=6, partial_json_repaired_rows=6
- P_minus_Procedural_schema: raw_rows=15, valid_triples=0, valid_nodes=72, valid_edges=44, valid_mappings=24, parse_or_generation_error_rows=8, partial_json_repaired_rows=8
- P_minus_Validator: raw_rows=15, valid_triples=0, valid_nodes=71, valid_edges=45, valid_mappings=32, parse_or_generation_error_rows=5, partial_json_repaired_rows=5
- P_minus_Standard_bridge: raw_rows=15, valid_triples=0, valid_nodes=73, valid_edges=53, valid_mappings=0, parse_or_generation_error_rows=1, partial_json_repaired_rows=1
- P_minus_Schema_retrieval: raw_rows=15, valid_triples=0, valid_nodes=73, valid_edges=51, valid_mappings=27, parse_or_generation_error_rows=3, partial_json_repaired_rows=3

## Files

- Raw outputs: `48_qwen3_8b_strict_json_1200_full_raw.shard07.jsonl`
- Validated outputs: `49_qwen3_8b_strict_json_1200_full_valid.shard07.jsonl`
