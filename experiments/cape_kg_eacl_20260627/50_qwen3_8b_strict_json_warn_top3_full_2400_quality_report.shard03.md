# Condition-Specific LLM Baseline Report

Generated: 2026-06-28T10:57:08.816270+00:00

- Output directory: `experiments/cape_kg_eacl_20260627`
- Output prefix: `qwen3_8b_strict_json_warn_top3_full_2400`
- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218`
- Quantization: `4bit`
- Strict JSON contract: True
- CUDA_VISIBLE_DEVICES: `3`
- Chunk file: `01_data/evaluation_chunks.jsonl`
- Shard: 4 / 8
- Chunks selected: 15

## Conditions

- B2_current_project: raw_rows=15, valid_triples=0, valid_nodes=128, valid_edges=86, valid_mappings=0, parse_or_generation_error_rows=3, partial_json_repaired_rows=3
- B4_taxonomy_rag: raw_rows=15, valid_triples=0, valid_nodes=131, valid_edges=75, valid_mappings=43, parse_or_generation_error_rows=5, partial_json_repaired_rows=5
- B5_procedural_prompt: raw_rows=15, valid_triples=0, valid_nodes=268, valid_edges=96, valid_mappings=0, parse_or_generation_error_rows=7, partial_json_repaired_rows=7

## Files

- Raw outputs: `48_qwen3_8b_strict_json_warn_top3_full_2400_raw.shard03.jsonl`
- Validated outputs: `49_qwen3_8b_strict_json_warn_top3_full_2400_valid.shard03.jsonl`
