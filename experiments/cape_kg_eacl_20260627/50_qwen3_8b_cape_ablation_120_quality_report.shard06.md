# Condition-Specific LLM Baseline Report

Generated: 2026-06-27T18:59:26.030107+00:00

- Output directory: `experiments/cape_kg_eacl_20260627`
- Output prefix: `qwen3_8b_cape_ablation_120`
- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218`
- Quantization: `4bit`
- CUDA_VISIBLE_DEVICES: `6`
- Chunk file: `01_data/evaluation_chunks.jsonl`
- Shard: 7 / 8
- Chunks selected: 15

## Conditions

- P_cape_kg_actual: raw_rows=15, valid_triples=0, valid_nodes=70, valid_edges=23, valid_mappings=1, parse_or_generation_error_rows=14, partial_json_repaired_rows=13
- P_minus_CQ: raw_rows=15, valid_triples=0, valid_nodes=73, valid_edges=8, valid_mappings=2, parse_or_generation_error_rows=14, partial_json_repaired_rows=14
- P_minus_Evidence: raw_rows=15, valid_triples=0, valid_nodes=62, valid_edges=28, valid_mappings=2, parse_or_generation_error_rows=13, partial_json_repaired_rows=12
- P_minus_Procedural_schema: raw_rows=15, valid_triples=0, valid_nodes=67, valid_edges=21, valid_mappings=3, parse_or_generation_error_rows=13, partial_json_repaired_rows=12
- P_minus_Validator: raw_rows=15, valid_triples=0, valid_nodes=65, valid_edges=24, valid_mappings=1, parse_or_generation_error_rows=14, partial_json_repaired_rows=12
- P_minus_Standard_bridge: raw_rows=15, valid_triples=0, valid_nodes=70, valid_edges=27, valid_mappings=0, parse_or_generation_error_rows=7, partial_json_repaired_rows=6

## Files

- Raw outputs: `48_qwen3_8b_cape_ablation_120_raw.shard06.jsonl`
- Validated outputs: `49_qwen3_8b_cape_ablation_120_valid.shard06.jsonl`
