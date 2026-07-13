# Mapping Downstream Report

This report tracks the NCS/PCF downstream task proposed in the EACL revision plan.
Expert-confirmed Hit@K/P@5/MRR remain pending until Top-5 source-task groups are reviewed.

## Candidate Coverage

| standard | selected tasks | covered tasks | coverage | Top-5 rows | reason rate | P@5 | MRR |
|---|---:|---:|---:|---:|---:|---|---|
| NCS | 22 | 22 | 1.0 | 110 | 1.0 | pending_human_review | pending_human_review |
| PCF | 22 | 22 | 1.0 | 110 | 1.0 | pending_human_review | pending_human_review |

## Representation-Arm Diagnostic

The table below reranks the already generated Top-5 candidate universe using representation-specific proxy scores.
It is a scaffold for the downstream comparison, not a paper-claimable mapping result.

| standard | arm | source groups | candidate rows | Top-1 agreement with full score | mean top1 proxy | mean margin | claim status |
|---|---|---:|---:|---:|---:|---:|---|
| NCS | text_only_task_description | 22 | 110 | 0.3182 | 0.309732 | 0.101656 | diagnostic_rerank_only_not_expert_reviewed |
| NCS | task_frame_only | 22 | 110 | 0.2727 | 0.339482 | 0.065606 | diagnostic_rerank_only_not_expert_reviewed |
| NCS | flat_triples | 22 | 110 | 0.2273 | 0.34001 | 0.065752 | diagnostic_rerank_only_not_expert_reviewed |
| NCS | procedural_kg_with_evidence | 22 | 110 | 0.3182 | 0.257132 | 0.085955 | diagnostic_rerank_only_not_expert_reviewed |
| PCF | text_only_task_description | 22 | 110 | 0.4091 | 0.324879 | 0.048755 | diagnostic_rerank_only_not_expert_reviewed |
| PCF | task_frame_only | 22 | 110 | 0.3636 | 0.360162 | 0.056744 | diagnostic_rerank_only_not_expert_reviewed |
| PCF | flat_triples | 22 | 110 | 0.3636 | 0.342972 | 0.041811 | diagnostic_rerank_only_not_expert_reviewed |
| PCF | procedural_kg_with_evidence | 22 | 110 | 0.3182 | 0.270977 | 0.043786 | diagnostic_rerank_only_not_expert_reviewed |

## Per-Task Rerank Trace

- Detail CSV: `experiments/cape_kg_eacl_20260627/04_evaluation/mapping_downstream_arm_rerank_details.csv`
- Detail JSON summary: `experiments/cape_kg_eacl_20260627/04_evaluation/mapping_downstream_arm_rerank_summary.json`
- Detail rows: 176
- Standards: NCS, PCF
- Arms: flat_triples, procedural_kg_with_evidence, task_frame_only, text_only_task_description
- Each detail row records the source task, representation arm, selected Top-1 candidate, original full-score Top-1 candidate, proxy score, and margin.

## Claim Scope

- `generated_top5_only` means this diagnostic reranks only the current generated candidate rows.
- It does not regenerate a full candidate universe for each representation arm.
- It does not replace expert review; P@K, P@5, MRR, and accept-rate remain pending.
- After expert review, the same source-task groups can be scored as text-only, task-frame, flat-triple, and procedural-KG variants.
