# Condition-Specific LLM Baseline Report

Generated: 2026-06-28T01:13:12.949515+00:00

- Output directory: `experiments/cape_kg_eacl_20260627`
- Output prefix: `qwen3_8b_strict_json_nothink_1200_smoke`
- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218`
- Quantization: `4bit`
- Strict JSON contract: True
- CUDA_VISIBLE_DEVICES: `0`
- Chunk file: `01_data/evaluation_chunks.jsonl`
- Shard: 1 / 1
- Chunks selected: 2

## Conditions

- P_minus_CQ: raw_rows=2, valid_triples=0, valid_nodes=10, valid_edges=8, valid_mappings=6, parse_or_generation_error_rows=0, partial_json_repaired_rows=0
- P_cape_kg_actual: raw_rows=2, valid_triples=0, valid_nodes=10, valid_edges=8, valid_mappings=6, parse_or_generation_error_rows=0, partial_json_repaired_rows=0
- P_minus_Validator: raw_rows=2, valid_triples=0, valid_nodes=10, valid_edges=8, valid_mappings=4, parse_or_generation_error_rows=0, partial_json_repaired_rows=0
- P_minus_Schema_retrieval: raw_rows=2, valid_triples=0, valid_nodes=10, valid_edges=7, valid_mappings=4, parse_or_generation_error_rows=0, partial_json_repaired_rows=0

## Files

- Raw outputs: `48_qwen3_8b_strict_json_nothink_1200_smoke_raw.jsonl`
- Validated outputs: `49_qwen3_8b_strict_json_nothink_1200_smoke_valid.jsonl`
