# Condition-Specific LLM Baseline Report

Generated: 2026-06-28T10:49:25.462500+00:00

- Output directory: `experiments/cape_kg_eacl_20260627`
- Output prefix: `qwen3_8b_strict_json_warn_top3_full_2400`
- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218`
- Quantization: `4bit`
- Strict JSON contract: True
- CUDA_VISIBLE_DEVICES: `4`
- Chunk file: `01_data/evaluation_chunks.jsonl`
- Shard: 5 / 8
- Chunks selected: 15

## Conditions

- B2_current_project: raw_rows=15, valid_triples=0, valid_nodes=97, valid_edges=67, valid_mappings=0, parse_or_generation_error_rows=2, partial_json_repaired_rows=2
- B4_taxonomy_rag: raw_rows=15, valid_triples=0, valid_nodes=79, valid_edges=54, valid_mappings=27, parse_or_generation_error_rows=6, partial_json_repaired_rows=6
- B5_procedural_prompt: raw_rows=15, valid_triples=0, valid_nodes=154, valid_edges=107, valid_mappings=0, parse_or_generation_error_rows=2, partial_json_repaired_rows=2

## Files

- Raw outputs: `48_qwen3_8b_strict_json_warn_top3_full_2400_raw.shard04.jsonl`
- Validated outputs: `49_qwen3_8b_strict_json_warn_top3_full_2400_valid.shard04.jsonl`
