# Condition-Specific LLM Baseline Report

Generated: 2026-06-27T20:30:16.813740+00:00

- Output directory: `experiments/cape_kg_eacl_20260627`
- Output prefix: `qwen3_8b_edc_schema_ablation`
- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218`
- Quantization: `4bit`
- CUDA_VISIBLE_DEVICES: `4`
- Chunk file: `01_data/evaluation_chunks.jsonl`
- Shard: 5 / 8
- Chunks selected: 15

## Conditions

- B3_edc_style: raw_rows=15, valid_triples=0, valid_nodes=68, valid_edges=7, valid_mappings=0, parse_or_generation_error_rows=11, partial_json_repaired_rows=11
- P_minus_Schema_retrieval: raw_rows=15, valid_triples=0, valid_nodes=68, valid_edges=33, valid_mappings=4, parse_or_generation_error_rows=13, partial_json_repaired_rows=13

## Files

- Raw outputs: `48_qwen3_8b_edc_schema_ablation_raw.shard04.jsonl`
- Validated outputs: `49_qwen3_8b_edc_schema_ablation_valid.shard04.jsonl`
