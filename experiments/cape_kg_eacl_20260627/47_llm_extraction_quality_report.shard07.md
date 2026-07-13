# LLM Tool-Constrained Extraction Report

Generated: 2026-06-27T16:09:01.345377+00:00

- Output directory: `experiments/cape_kg_eacl_20260627`
- Model: `/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218`
- Quantization: `4bit`
- CUDA_VISIBLE_DEVICES: `7`
- Chunk file: `01_data/evaluation_chunks.jsonl`
- Shard: 8 / 8
- Selected chunks: 15
- Newly processed chunks: 15
- Raw rows currently present: 15
- Valid task frames in this run: 8
- Valid procedural relations in this run: 3
- Rejected candidates in this run: 1
- Validation/drop counts: {"domain_violation": 6, "parse_error": 7, "range_violation": 4, "root_not_object": 7, "unknown_class": 1}

Files:

- Raw model output: `45_llm_tool_extractions_raw.shard07.jsonl`
- Validated tool calls: `46_llm_tool_extractions_valid.shard07.jsonl`
