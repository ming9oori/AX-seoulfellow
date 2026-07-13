# Condition-Specific LLM Baseline Report

Generated: 2026-06-28T08:27:28.922693+00:00

- Output directory: `experiments/cape_kg_eacl_20260627`
- Output prefix: `qwen3_32b_awq_core_120`
- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-32B-AWQ/snapshots/0499c3ac83fdef8810b907a23894ba91e95eddd8`
- Quantization: `native`
- Strict JSON contract: False
- CUDA_VISIBLE_DEVICES: `2,3`
- Chunk file: `01_data/evaluation_chunks.jsonl`
- Shard: 2 / 4
- Chunks selected: 30

## Conditions

- B0_plain_llm: raw_rows=30, valid_triples=232, valid_nodes=0, valid_edges=0, valid_mappings=0, parse_or_generation_error_rows=15, partial_json_repaired_rows=15
- B1_predicate_constrained: raw_rows=30, valid_triples=0, valid_nodes=0, valid_edges=148, valid_mappings=0, parse_or_generation_error_rows=18, partial_json_repaired_rows=18
- B2_current_project: raw_rows=30, valid_triples=0, valid_nodes=178, valid_edges=13, valid_mappings=0, parse_or_generation_error_rows=25, partial_json_repaired_rows=25
- P_cape_kg_actual: raw_rows=30, valid_triples=0, valid_nodes=146, valid_edges=84, valid_mappings=0, parse_or_generation_error_rows=29, partial_json_repaired_rows=29

## Files

- Raw outputs: `48_qwen3_32b_awq_core_120_raw.shard01.jsonl`
- Validated outputs: `49_qwen3_32b_awq_core_120_valid.shard01.jsonl`
