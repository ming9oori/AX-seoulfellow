# LLM Tool-Constrained Extraction Report

Generated: 2026-06-27T15:56:20.448684+00:00

- Output directory: `experiments/cape_kg_eacl_20260627`
- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218`
- Quantization: `4bit`
- CUDA_VISIBLE_DEVICES: `0`
- Chunk file: `01_data/evaluation_chunks.jsonl`
- Shard: 1 / 1
- Selected chunks: 10
- Newly processed chunks: 10
- Raw rows currently present: 10
- Valid task frames in this run: 8
- Valid procedural relations in this run: 18
- Rejected candidates in this run: 0
- Validation/drop counts: {"domain_violation": 5, "parse_error": 2, "range_violation": 1, "root_not_object": 2}

Files:

- Raw model output: `45_llm_tool_extractions_raw.jsonl`
- Validated tool calls: `46_llm_tool_extractions_valid.jsonl`
