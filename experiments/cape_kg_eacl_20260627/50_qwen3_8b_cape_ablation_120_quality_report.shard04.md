# Condition-Specific LLM Baseline Report

Generated: 2026-06-27T18:57:01.208196+00:00

- Output directory: `experiments/cape_kg_eacl_20260627`
- Output prefix: `qwen3_8b_cape_ablation_120`
- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218`
- Quantization: `4bit`
- CUDA_VISIBLE_DEVICES: `4`
- Chunk file: `01_data/evaluation_chunks.jsonl`
- Shard: 5 / 8
- Chunks selected: 15

## Conditions

- P_cape_kg_actual: raw_rows=15, valid_triples=0, valid_nodes=58, valid_edges=16, valid_mappings=2, parse_or_generation_error_rows=13, partial_json_repaired_rows=11
- P_minus_CQ: raw_rows=15, valid_triples=0, valid_nodes=50, valid_edges=12, valid_mappings=4, parse_or_generation_error_rows=13, partial_json_repaired_rows=9
- P_minus_Evidence: raw_rows=15, valid_triples=0, valid_nodes=44, valid_edges=16, valid_mappings=5, parse_or_generation_error_rows=12, partial_json_repaired_rows=8
- P_minus_Procedural_schema: raw_rows=15, valid_triples=0, valid_nodes=48, valid_edges=15, valid_mappings=3, parse_or_generation_error_rows=12, partial_json_repaired_rows=8
- P_minus_Validator: raw_rows=15, valid_triples=0, valid_nodes=62, valid_edges=22, valid_mappings=2, parse_or_generation_error_rows=13, partial_json_repaired_rows=11
- P_minus_Standard_bridge: raw_rows=15, valid_triples=0, valid_nodes=55, valid_edges=23, valid_mappings=0, parse_or_generation_error_rows=9, partial_json_repaired_rows=5

## Files

- Raw outputs: `48_qwen3_8b_cape_ablation_120_raw.shard04.jsonl`
- Validated outputs: `49_qwen3_8b_cape_ablation_120_valid.shard04.jsonl`
