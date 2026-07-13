# Condition-Specific LLM Baseline Report

Generated: 2026-06-27T17:02:28.819356+00:00

- Output directory: `experiments/cape_kg_eacl_20260627`
- Output prefix: `qwen3_8b_condition_baselines_120`
- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218`
- Quantization: `4bit`
- CUDA_VISIBLE_DEVICES: `3`
- Chunk file: `01_data/evaluation_chunks.jsonl`
- Shard: 4 / 8
- Chunks selected: 15

## Conditions

- B0_plain_llm: raw_rows=15, valid_triples=35, valid_nodes=0, valid_edges=0, parse_or_generation_error_rows=8
- B1_predicate_constrained: raw_rows=15, valid_triples=0, valid_nodes=0, valid_edges=29, parse_or_generation_error_rows=8
- B5_procedural_prompt: raw_rows=15, valid_triples=0, valid_nodes=7, valid_edges=5, parse_or_generation_error_rows=13

## Files

- Raw outputs: `48_qwen3_8b_condition_baselines_120_raw.shard03.jsonl`
- Validated outputs: `49_qwen3_8b_condition_baselines_120_valid.shard03.jsonl`
