# LLM Tool-Constrained Extraction Report

Generated: 2026-06-27T16:09:08.724690+00:00

- Output directory: `experiments/cape_kg_eacl_20260627`
- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218`
- Quantization: `4bit`
- CUDA_VISIBLE_DEVICES: `6`
- Chunk file: `01_data/evaluation_chunks.jsonl`
- Shard: 7 / 8
- Selected chunks: 15
- Newly processed chunks: 15
- Raw rows currently present: 15
- Valid task frames in this run: 7
- Valid procedural relations in this run: 9
- Rejected candidates in this run: 0
- Validation/drop counts: {"domain_violation": 5, "parse_error": 8, "range_violation": 3, "root_not_object": 8}

Files:

- Raw model output: `45_llm_tool_extractions_raw.shard06.jsonl`
- Validated tool calls: `46_llm_tool_extractions_valid.shard06.jsonl`
