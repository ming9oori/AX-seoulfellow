# Condition-Specific LLM Baseline Report

Generated: 2026-06-27T20:14:30.687905+00:00

- Output directory: `experiments/cape_kg_eacl_20260627`
- Output prefix: `qwen3_8b_edc_schema_ablation_smoke`
- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218`
- Quantization: `4bit`
- CUDA_VISIBLE_DEVICES: `0`
- Chunk file: `01_data/evaluation_chunks.jsonl`
- Shard: 1 / 1
- Chunks selected: 2

## Conditions

- B3_edc_style: raw_rows=2, valid_triples=0, valid_nodes=3, valid_edges=4, valid_mappings=0, parse_or_generation_error_rows=0, partial_json_repaired_rows=0
- P_minus_Schema_retrieval: raw_rows=2, valid_triples=0, valid_nodes=10, valid_edges=5, valid_mappings=0, parse_or_generation_error_rows=2, partial_json_repaired_rows=2

## Files

- Raw outputs: `48_qwen3_8b_edc_schema_ablation_smoke_raw.jsonl`
- Validated outputs: `49_qwen3_8b_edc_schema_ablation_smoke_valid.jsonl`
