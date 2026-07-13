# Condition-Specific LLM Baseline Report

Generated: 2026-06-28T01:06:45.528095+00:00

- Output directory: `experiments/cape_kg_eacl_20260627`
- Output prefix: `qwen3_8b_strict_json_nothink_smoke`
- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218`
- Quantization: `4bit`
- Strict JSON contract: True
- CUDA_VISIBLE_DEVICES: `0`
- Chunk file: `01_data/evaluation_chunks.jsonl`
- Shard: 1 / 1
- Chunks selected: 4

## Conditions

- P_minus_CQ: raw_rows=4, valid_triples=0, valid_nodes=20, valid_edges=15, valid_mappings=0, parse_or_generation_error_rows=4, partial_json_repaired_rows=4
- P_cape_kg_actual: raw_rows=4, valid_triples=0, valid_nodes=20, valid_edges=15, valid_mappings=1, parse_or_generation_error_rows=4, partial_json_repaired_rows=4
- P_minus_Validator: raw_rows=4, valid_triples=0, valid_nodes=20, valid_edges=15, valid_mappings=1, parse_or_generation_error_rows=4, partial_json_repaired_rows=4
- P_minus_Schema_retrieval: raw_rows=4, valid_triples=0, valid_nodes=20, valid_edges=16, valid_mappings=2, parse_or_generation_error_rows=4, partial_json_repaired_rows=4

## Files

- Raw outputs: `48_qwen3_8b_strict_json_nothink_smoke_raw.jsonl`
- Validated outputs: `49_qwen3_8b_strict_json_nothink_smoke_valid.jsonl`
