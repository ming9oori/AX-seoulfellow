# Condition-Specific LLM Baseline Report

Generated: 2026-06-28T10:47:44.573256+00:00

- Output directory: `experiments/cape_kg_eacl_20260627`
- Output prefix: `qwen3_8b_strict_json_warn_top3_full_2400`
- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218`
- Quantization: `4bit`
- Strict JSON contract: True
- CUDA_VISIBLE_DEVICES: `0`
- Chunk file: `01_data/evaluation_chunks.jsonl`
- Shard: 1 / 8
- Chunks selected: 15

## Conditions

- B2_current_project: raw_rows=15, valid_triples=0, valid_nodes=109, valid_edges=81, valid_mappings=0, parse_or_generation_error_rows=0, partial_json_repaired_rows=0
- B4_taxonomy_rag: raw_rows=15, valid_triples=0, valid_nodes=89, valid_edges=76, valid_mappings=59, parse_or_generation_error_rows=2, partial_json_repaired_rows=2
- B5_procedural_prompt: raw_rows=15, valid_triples=0, valid_nodes=198, valid_edges=90, valid_mappings=0, parse_or_generation_error_rows=3, partial_json_repaired_rows=3

## Files

- Raw outputs: `48_qwen3_8b_strict_json_warn_top3_full_2400_raw.shard00.jsonl`
- Validated outputs: `49_qwen3_8b_strict_json_warn_top3_full_2400_valid.shard00.jsonl`
