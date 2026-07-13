# CAPE-KG Gold Item Feasibility Report

Generated: 2026-06-29T18:56:35.448388+00:00
Claim status: `gold_item_feasibility_ready_pending_human_adjudication`

이 문서는 500개 이상 human-gold item 요건이 이미 충족되었다고 주장하지 않습니다. 현재 priority-100 검수 패키지의 candidate edge 풀이 최소 gold item 목표를 감당할 수 있는지 계산하는 pre-human feasibility artifact입니다.

## Target and Current Human-Gold Status

| Item | Value |
| --- | --- |
| Minimum required chunks | 100 |
| Minimum required gold items | 500 |
| Required gold items per chunk avg | 5.0000 |
| Current completed adjudicated chunks | 0 |
| Current gold item count for readiness | 0 |
| Current human-gold claim status | `pending_human_adjudication` |
| Human-gold gate satisfied | no |

## Candidate Pool Feasibility

| Item | Value |
| --- | --- |
| Assigned priority chunks | 100 |
| Priority-100 candidate edges | 1371 |
| Full-120 candidate edges | 1436 |
| Active-review items total | 264 |
| High-impact chunks | 64 |
| Candidate edges per required gold item | 2.7420 |
| Candidate edges per assigned chunk avg | 13.7100 |
| Candidate pool sufficient for 500-item target | yes |
| First batch meeting 500-candidate proxy | full_120_priority_batch_001 |
| Batch meeting both 100 chunks and 500-candidate proxy | full_120_priority_batch_005 |

## Batch-Level Cumulative Feasibility

| Order | Batch | Chunks | Candidate edges | Cum. chunks | Cum. candidates | Edges/chunk | Cum. edges/chunk | 500 proxy | 100 chunks | Both |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | full_120_priority_batch_001 | 20 | 811 | 20 | 811 | 40.5500 | 40.5500 | yes | no | no |
| 2 | full_120_priority_batch_002 | 20 | 180 | 40 | 991 | 9.0000 | 24.7750 | yes | no | no |
| 3 | full_120_priority_batch_003 | 20 | 152 | 60 | 1143 | 7.6000 | 19.0500 | yes | no | no |
| 4 | full_120_priority_batch_004 | 20 | 91 | 80 | 1234 | 4.5500 | 15.4250 | yes | no | no |
| 5 | full_120_priority_batch_005 | 20 | 137 | 100 | 1371 | 6.8500 | 13.7100 | yes | yes | yes |

## Claim Boundary

- Candidate edges are not gold items: `True`
- Not claimable until: `two annotators complete the selected chunks, IAA is computed, adjudication is imported, and gold_item_count_for_readiness >= 500`
- Safe interpretation: The priority-100 package has enough candidate-edge workload to support the 500-item target if human adjudication accepts enough node/edge/evidence items; the current adjudicated gold count remains zero.

## Input and Output Files

- Assignment summary: `experiments/cape_kg_eacl_20260627/06_release/annotation_batch_assignment_summary.json`
- Gold sampling coverage: `experiments/cape_kg_eacl_20260627/06_release/gold_sampling_coverage_report.json`
- Human-gold validation summary: `experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_validation_summary.json`
- JSON: `experiments/cape_kg_eacl_20260627/06_release/gold_item_feasibility_report.json`
- Batch CSV: `experiments/cape_kg_eacl_20260627/05_review/gold_item_feasibility_by_batch.csv`
