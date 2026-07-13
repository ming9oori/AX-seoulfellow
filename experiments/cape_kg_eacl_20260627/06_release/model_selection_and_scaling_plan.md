# Model Selection and Scaling Plan

Generated: 2026-06-28

## Current Executed Runs

- Qwen3-8B 4bit: full 120 evaluation chunks completed.
  - Raw rows: `experiments/cape_kg_eacl_20260627/45_llm_tool_extractions_raw.jsonl`
  - Valid rows: `experiments/cape_kg_eacl_20260627/46_llm_tool_extractions_valid.jsonl`
  - Report: `experiments/cape_kg_eacl_20260627/47_llm_extraction_quality_report.md`
- Qwen3-14B 4bit: full 120 evaluation chunks completed for core B0/B1/B2/P conditions.
  - Raw rows: `experiments/cape_kg_eacl_20260627/48_qwen3_14b_core_conditions_120_raw.jsonl`
  - Valid rows: `experiments/cape_kg_eacl_20260627/49_qwen3_14b_core_conditions_120_valid.jsonl`
  - Report: `experiments/cape_kg_eacl_20260627/50_qwen3_14b_core_conditions_120_quality_report.md`
  - Silver proxy evaluation: `experiments/cape_kg_eacl_20260627/04_evaluation/qwen3_14b_core_silver_evaluation_report.md`
- Qwen3-32B-AWQ native quantization: full 120 evaluation chunks completed for core B0/B1/B2/P conditions.
  - Raw rows: `experiments/cape_kg_eacl_20260627/48_qwen3_32b_awq_core_120_raw.jsonl`
  - Valid rows: `experiments/cape_kg_eacl_20260627/49_qwen3_32b_awq_core_120_valid.jsonl`
  - Report: `experiments/cape_kg_eacl_20260627/50_qwen3_32b_awq_core_120_quality_report.md`
  - Silver proxy evaluation: `experiments/cape_kg_eacl_20260627/04_evaluation/qwen3_32b_awq_core_silver_evaluation_report.md`
- Llama-2-13B-chat 4bit: 10 chunk smoke/model-compatibility run completed.
  - Raw rows: `experiments/cape_kg_eacl_20260627/45_llama2_13b_chat_tool_extractions_raw.jsonl`
  - Valid rows: `experiments/cape_kg_eacl_20260627/46_llama2_13b_chat_tool_extractions_valid.jsonl`
  - Report: `experiments/cape_kg_eacl_20260627/47_llama2_13b_chat_tool_extractions_quality_report.md`

## Current Server Capacity Check

- GPUs 0-7 are available: 8 x RTX 3090, 24GB each.
- `/home` free space after caching and running Qwen3-32B-AWQ is about 34GB.
- Hugging Face cache now includes Qwen3-8B, Qwen3-14B, Qwen3-32B-AWQ, and Llama-2-7B/13B-chat.
- Measured remote model sizes: Qwen3-14B standard weights about 27.5GiB; Qwen3-32B standard weights about 61.0GiB; Qwen3-32B-AWQ safetensors about 18.0GiB.
- Qwen3-32B is not currently cached.
- Qwen3-32B-AWQ complete safetensors are cached.
- Current Python environment has Transformers, Accelerate, BitsAndBytes, Torch, and AutoAWQ/AWQ available. vLLM and SGLang are not installed. Ollama is installed separately.
- Transformers 4.57.6 includes an AWQ quantizer, but it still requires `autoawq` for AWQ model loading in the current environment.
- The CAPE LLM scripts now accept `--quantization native` for pre-quantized models such as AWQ snapshots.
- Current Qwen3-32B-AWQ readiness: `core_run_complete`.
  - JSON: `experiments/cape_kg_eacl_20260627/06_release/qwen3_32b_awq_readiness.json`
  - Report: `experiments/cape_kg_eacl_20260627/06_release/qwen3_32b_awq_readiness.md`

## Prior-Work Model Context

- PAGED evaluates procedural graph extraction with Flan-T5, ChatGPT, and Llama2, and also provides fine-tuning paths for Flan-T5-XXL and Llama2-70B.
- Text2KGBench reports ontology-guided KG generation baselines for Vicuna-13B and Alpaca-LoRA-13B.
- EDC focuses on the Extract-Define-Canonicalize framework and schema retrieval for large-schema KGC, making it a methodological baseline rather than just a single-model baseline.
- SAC-KG is relevant as a Generator/Verifier/Pruner LLM-based domain KG construction framework and is a useful comparison point for precision-oriented KG construction. Its reported backbones include Qwen 7B, Llama2-7B, Llama2-13B, and ChatGPT, with ChatGPT strongest in their reported precision table.
- Ontology-guided KG construction on maintenance short texts evaluates the Llama family and reports Llama-3-70B-Instruct as the strongest inference-only setup, with Llama-3-8B presented as a viable smaller alternative after hallucination pruning.
- This package now includes a deterministic SAC-KG-style verifier/pruner approximation (`B6_sac_kg_verifier_pruner`) built from existing generator candidates. It should be described as an approximation, not a full SAC-KG reproduction.

Primary sources:

- SAC-KG: https://aclanthology.org/2024.acl-long.238/
- EDC: https://aclanthology.org/2024.emnlp-main.548/
- PAGED: https://aclanthology.org/2024.acl-long.583/
- Text2KGBench: https://ar5iv.labs.arxiv.org/html/2308.02357
- Ontology-guided KG Construction from Maintenance Short Texts: https://aclanthology.org/2024.kallm-1.8.pdf
- Qwen3-32B model card: https://huggingface.co/Qwen/Qwen3-32B
- Qwen3-32B-AWQ model card: https://huggingface.co/Qwen/Qwen3-32B-AWQ

## Recommendation

Use the completed Qwen3-32B-AWQ run as the current strongest local open-weight diagnostic. Use standard Qwen3-32B only after freeing substantial disk space.

Rationale:

- Qwen3-14B is materially larger than Qwen3-8B and was executed on the same 120-chunk core B0/B1/B2/P setup.
- Qwen3-32B-AWQ is now executed on the same 120-chunk core B0/B1/B2/P setup and is more practical than standard 32B or 70B models on 8x RTX 3090.
- Qwen3 has stronger multilingual and tool-following behavior than the older Llama2/Vicuna/Alpaca baselines used in earlier work.
- If closed API models are permitted, a modern GPT/Claude/Gemini-class model can be added as an upper-bound baseline; for reproducibility and private-source control, the local open-weight path now includes Qwen3-8B, Qwen3-14B, and Qwen3-32B-AWQ.
- The current local filesystem has only about 34GB free after Qwen3-32B-AWQ caching, which is below the standard Qwen3-32B weight size.
- Qwen3-32B-AWQ was run with Transformers native quantization plus AutoAWQ/AWQ compatibility.
- Do not download Qwen3-32B standard weights on the current disk state. For a standard 32B run, first free at least 80-100GB for safe cache/checkpoint headroom.

## Qwen3-32B-AWQ Readiness Check

- AWQ model: `Qwen/Qwen3-32B-AWQ`
- Model card: https://huggingface.co/Qwen/Qwen3-32B-AWQ
- Snapshot SHA from readiness check: `0499c3ac83fdef8810b907a23894ba91e95eddd8`
- AWQ safetensors size: 18.0GiB.
- Standard Qwen3-32B safetensors size: 61.02GiB.
- `/home` free during latest readiness check: about 34GiB.
- Complete AWQ cached snapshots: 1.
- Partial/config-only AWQ cached snapshots: 0.
- Current blocker: none for the AWQ core run; the full core 120-chunk run is complete.
- Decision: Qwen3-32B-AWQ is available and has already been run for B0/B1/B2/P core conditions.

Check command:

```bash
/home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python scripts/check_qwen3_32b_awq_readiness.py --experiment-dir experiments/cape_kg_eacl_20260627
```

Download command, only if cache is removed and the model must be restored:

```bash
/home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python scripts/check_qwen3_32b_awq_readiness.py --experiment-dir experiments/cape_kg_eacl_20260627 --download
```

Smoke run template, if a quick compatibility check is needed again:

```bash
MODEL=/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-32B-AWQ/snapshots/<snapshot>
PY=/home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python
EXP=experiments/cape_kg_eacl_20260627

CUDA_VISIBLE_DEVICES=0,1 $PY scripts/run_cape_llm_condition_baselines.py \
  --output-dir $EXP \
  --chunk-file 01_data/evaluation_chunks.jsonl \
  --model $MODEL \
  --quantization native \
  --conditions B0_plain_llm,P_cape_kg_actual \
  --output-prefix qwen3_32b_awq_smoke \
  --max-chunks 4 \
  --max-new-tokens 650 \
  --max-prompt-chars 3600
```

## Qwen3-14B Core Run Notes

- Conditions: B0_plain_llm, B1_predicate_constrained, B2_current_project, P_cape_kg_actual.
- Raw/valid rows: 480/480.
- Qwen3-14B P_cape_kg_actual silver proxy metrics: edge_exact_f1=0.001741, predicate_f1=0.060078, node_label_f1=0.029751, evidence_f1=0.060955.
- Comparable Qwen3-8B P_cape_kg_actual silver proxy metrics: edge_exact_f1=0.001786, predicate_f1=0.048214, node_label_f1=0.032597, evidence_f1=0.065527.
- These are silver-reference diagnostics only. They do not replace adjudicated human-gold scoring.

## Qwen3-32B-AWQ Core Run Notes

- Conditions: B0_plain_llm, B1_predicate_constrained, B2_current_project, P_cape_kg_actual.
- Raw/valid rows: 480/480.
- Qwen3-32B-AWQ P_cape_kg_actual silver proxy metrics: edge_exact_f1=0.003441, predicate_f1=0.066237, node_label_f1=0.02835, evidence_f1=0.054153.
- Qwen3-32B-AWQ B1_predicate_constrained silver proxy metrics: edge_exact_f1=0.001569, predicate_f1=0.116078, node_label_f1=0.0, evidence_f1=0.022435.
- These are silver-reference diagnostics only. They do not replace adjudicated human-gold scoring.

## Optional Future Standard Qwen3-32B Template

The Qwen3-32B-AWQ core run is already complete. The following template is only for a future standard-weight Qwen3-32B run after enough disk space is available. Assume the model is available at:

```bash
/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-32B/snapshots/<snapshot>
```

Run four shards, two GPUs per shard:

```bash
MODEL=/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-32B/snapshots/<snapshot>
PY=/home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python
EXP=experiments/cape_kg_eacl_20260627

CUDA_VISIBLE_DEVICES=0,1 $PY scripts/run_cep_onto_llm_extraction.py --output-dir $EXP --chunk-file 01_data/evaluation_chunks.jsonl --model $MODEL --quantization 4bit --source-label qwen3_32b_tool_constrained_extraction --output-prefix qwen3_32b_tool_extractions --num-shards 4 --shard-index 0 --max-new-tokens 800 --max-prompt-chars 3600 &
CUDA_VISIBLE_DEVICES=2,3 $PY scripts/run_cep_onto_llm_extraction.py --output-dir $EXP --chunk-file 01_data/evaluation_chunks.jsonl --model $MODEL --quantization 4bit --source-label qwen3_32b_tool_constrained_extraction --output-prefix qwen3_32b_tool_extractions --num-shards 4 --shard-index 1 --max-new-tokens 800 --max-prompt-chars 3600 &
CUDA_VISIBLE_DEVICES=4,5 $PY scripts/run_cep_onto_llm_extraction.py --output-dir $EXP --chunk-file 01_data/evaluation_chunks.jsonl --model $MODEL --quantization 4bit --source-label qwen3_32b_tool_constrained_extraction --output-prefix qwen3_32b_tool_extractions --num-shards 4 --shard-index 2 --max-new-tokens 800 --max-prompt-chars 3600 &
CUDA_VISIBLE_DEVICES=6,7 $PY scripts/run_cep_onto_llm_extraction.py --output-dir $EXP --chunk-file 01_data/evaluation_chunks.jsonl --model $MODEL --quantization 4bit --source-label qwen3_32b_tool_constrained_extraction --output-prefix qwen3_32b_tool_extractions --num-shards 4 --shard-index 3 --max-new-tokens 800 --max-prompt-chars 3600 &
wait

$PY scripts/run_cep_onto_llm_extraction.py --output-dir $EXP --chunk-file 01_data/evaluation_chunks.jsonl --output-prefix qwen3_32b_tool_extractions --num-shards 4 --merge-shards
```

## Claim Guidance

- Qwen3-8B full run is valid as a local execution-path result, not a strong final baseline.
- Qwen3-14B full core-condition run is valid as a stronger local diagnostic, but not a complete replacement for the Qwen3-8B full ablation matrix.
- Qwen3-32B-AWQ full core-condition run is valid as the strongest completed local open-weight diagnostic, but it is still silver/proxy evidence only.
- Llama-2-13B-chat smoke run is useful for prior-work model-family compatibility, not a paper result.
- Paper-level comparative claims still require human gold annotation, IAA, adjudication, and human-gold scoring.
