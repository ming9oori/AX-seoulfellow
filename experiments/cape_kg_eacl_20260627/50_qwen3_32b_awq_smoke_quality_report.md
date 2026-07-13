# Condition-Specific LLM Baseline Report

Generated: 2026-06-28T06:02:48.218140+00:00

- Output directory: `experiments/cape_kg_eacl_20260627`
- Output prefix: `qwen3_32b_awq_smoke`
- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-32B-AWQ/snapshots/0499c3ac83fdef8810b907a23894ba91e95eddd8`
- Quantization: `native`
- Strict JSON contract: False
- CUDA_VISIBLE_DEVICES: `0,1`
- Chunk file: `01_data/evaluation_chunks.jsonl`
- Shard: 1 / 1
- Chunks selected: 4

## Conditions

- B0_plain_llm: raw_rows=4, valid_triples=8, valid_nodes=0, valid_edges=0, valid_mappings=0, parse_or_generation_error_rows=0, partial_json_repaired_rows=0
- P_cape_kg_actual: raw_rows=4, valid_triples=0, valid_nodes=20, valid_edges=17, valid_mappings=0, parse_or_generation_error_rows=4, partial_json_repaired_rows=4

## Files

- Raw outputs: `48_qwen3_32b_awq_smoke_raw.jsonl`
- Validated outputs: `49_qwen3_32b_awq_smoke_valid.jsonl`
