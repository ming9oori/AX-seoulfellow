# Condition-Specific LLM Baseline Report

Generated: 2026-06-27T16:40:13.465251+00:00

- Output directory: `experiments/cape_kg_eacl_20260627`
- Output prefix: `qwen3_8b_condition_baselines`
- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218`
- Quantization: `4bit`
- CUDA_VISIBLE_DEVICES: `1`
- Chunk file: `01_data/evaluation_chunks.jsonl`
- Chunks selected: 10

## Conditions

- B0_plain_llm: raw_rows=10, valid_triples=24, valid_nodes=0, valid_edges=0, parse_or_generation_error_rows=1
- B1_predicate_constrained: raw_rows=10, valid_triples=0, valid_nodes=0, valid_edges=20, parse_or_generation_error_rows=2
- B5_procedural_prompt: raw_rows=10, valid_triples=0, valid_nodes=20, valid_edges=14, parse_or_generation_error_rows=5

## Files

- Raw outputs: `48_qwen3_8b_condition_baselines_raw.jsonl`
- Validated outputs: `49_qwen3_8b_condition_baselines_valid.jsonl`
