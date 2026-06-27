# CAPE-KG EACL Experiment Report

Generated: 2026-06-27T15:58:14.798834+00:00

## Scope

This package follows `AX_EACL_submission_review_revised_plan.md` by reframing
the AX task as CAPE-KG: competency-question anchored procedural evidence
grounding for domain KG construction.

## Data

- Source KG directory: `outputs`
- OCR workbook: `handoff-hanyang/자이제_ocr_preprocessed.xlsx`
- Total chunks available: 214
- Evaluation chunks selected: 120
- Silver reference nodes: 169
- Silver reference edges: 861
- Silver evidence anchors: 293

## Main Silver/Proxy Results

These numbers validate the evaluation code path. They are not final paper
claims until the silver reference is replaced with human gold and actual LLM
baseline generations.

- B0_plain_llm_proxy: Edge F1=0.1946, Evidence EM=0.0, Ontology=0.0, Procedural=1.0
- B1_predicate_constrained_proxy: Edge F1=0.889, Evidence EM=1.0, Ontology=0.0, Procedural=0.9223
- B2_current_project_baseline: Edge F1=1.0, Evidence EM=1.0, Ontology=1.0, Procedural=1.0
- B4_taxonomy_rag_proxy: Edge F1=0.8294, Evidence EM=1.0, Ontology=1.0, Procedural=1.0
- B5_procedural_prompt_proxy: Edge F1=0.4514, Evidence EM=1.0, Ontology=1.0, Procedural=1.0
- P_cape_kg_silver: Edge F1=1.0, Evidence EM=1.0, Ontology=1.0, Procedural=1.0
- P_minus_CQ_proxy: Edge F1=0.9087, Evidence EM=1.0, Ontology=1.0, Procedural=1.0
- P_minus_Evidence_proxy: Edge F1=1.0, Evidence EM=0.0, Ontology=1.0, Procedural=1.0
- P_minus_Procedural_schema_proxy: Edge F1=0.8294, Evidence EM=1.0, Ontology=1.0, Procedural=1.0
- P_minus_Validator_proxy: Edge F1=0.9863, Evidence EM=0.9735, Ontology=0.9524, Procedural=1.0
- P_minus_Standard_bridge_proxy: Edge F1=1.0, Evidence EM=1.0, Ontology=1.0, Procedural=1.0

## CQ Answerability

- P_cape_kg_silver mean CQ score: 4.58/5

## Mapping Downstream

- NCS: coverage=1.0 top5_rows=110 reason_rate=1.0
- PCF: coverage=1.0 top5_rows=110 reason_rate=1.0

## Active Review

- Review queue items: 861
- Highest priority: 0.317235

## Local LLM Smoke Run

- Raw chunk rows: 10
- Valid task frames: 8
- Valid procedural relations: 18
- Raw rows with parse/generation errors: 2
- Report: `experiments/cape_kg_eacl_20260627/47_llm_extraction_quality_report.md`

This is a smoke test of the local Qwen3-8B extraction path, not a full baseline result.

## Required Next Step

Human annotation remains the gating step for EACL-ready evidence.
