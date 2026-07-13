# Condition-Specific LLM Baseline Report

Generated: 2026-06-28T04:48:03.237015+00:00

- Output directory: `experiments/cape_kg_eacl_20260627`
- Output prefix: `qwen3_8b_strict_json_warn_top3_full_1200`
- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218`
- Quantization: `4bit`
- Strict JSON contract: True
- CUDA_VISIBLE_DEVICES: `1`
- Chunk file: `01_data/evaluation_chunks.jsonl`
- Shard: 2 / 8
- Chunks selected: 15

## Conditions

- B2_current_project: raw_rows=15, valid_triples=0, valid_nodes=103, valid_edges=43, valid_mappings=0, parse_or_generation_error_rows=8, partial_json_repaired_rows=8
- B4_taxonomy_rag: raw_rows=15, valid_triples=0, valid_nodes=93, valid_edges=39, valid_mappings=15, parse_or_generation_error_rows=9, partial_json_repaired_rows=9
- B5_procedural_prompt: raw_rows=15, valid_triples=0, valid_nodes=132, valid_edges=36, valid_mappings=0, parse_or_generation_error_rows=11, partial_json_repaired_rows=11

## Files

- Raw outputs: `48_qwen3_8b_strict_json_warn_top3_full_1200_raw.shard01.jsonl`
- Validated outputs: `49_qwen3_8b_strict_json_warn_top3_full_1200_valid.shard01.jsonl`
