# LLM Tool-Constrained Extraction Report

Generated: 2026-06-27T16:25:44.903318+00:00

- Output directory: `experiments/cape_kg_eacl_20260627`
- Model: `/home/minjoo/.cache/huggingface/hub/models--meta-llama--Llama-2-13b-chat-hf/snapshots/a2cb7a712bb6e5e736ca7f8cd98167f81a0b5bd8`
- Source label: `llama2_13b_chat_tool_constrained_extraction`
- Quantization: `4bit`
- Output prefix: `llama2_13b_chat_tool_extractions`
- CUDA_VISIBLE_DEVICES: `0`
- Chunk file: `01_data/evaluation_chunks.jsonl`
- Shard: 1 / 1
- Selected chunks: 10
- Newly processed chunks: 10
- Raw rows currently present: 10
- Valid task frames in this run: 8
- Valid procedural relations in this run: 2
- Rejected candidates in this run: 8
- Validation/drop counts: {"domain_violation": 3, "parse_error": 2, "root_not_object": 2, "unknown_predicate": 3}

Files:

- Raw model output: `45_llama2_13b_chat_tool_extractions_raw.jsonl`
- Validated tool calls: `46_llama2_13b_chat_tool_extractions_valid.jsonl`
