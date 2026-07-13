# CAPE-KG Gold Subset Sampling and Coverage Report

Generated: 2026-06-29T18:56:35.393928+00:00
Claim status: `gold_sampling_coverage_ready_pending_human_review`

이 문서는 human-gold annotation을 대체하지 않습니다. 현재 선택된 검수 subset이 어떤 근거로 구성되었고, corpus/chapter/candidate edge/active-review 관점에서 어떤 범위를 덮는지 설명하는 pre-human sampling evidence입니다.

## Selection Policy

- Minimum paper gate target: `100` chunks
- Selected chunks assigned to A/B batches: `100`
- Batch count/size: `5` batches x `20` chunks
- Priority formula: `0.4*candidate_edge_density + 0.4*active_review_priority + 0.2*high_impact_error_presence`
- Claim boundary (`not_gold_until`): `two annotators complete the selected chunks, IAA is computed, and adjudication is imported`

## Coverage Summary

- Priority-100 candidate-edge coverage within full-120 package: `0.954735`
- Priority-100 active-review chunk coverage within full-120 package: `0.967033`
- Priority-100 high-impact chunk coverage within full-120 package: `1.0`
- Full-120 candidate edges: `1436`
- Priority-100 candidate edges: `1371`
- Optional all-available-214 candidate edges: `2004`
- Optional strong package candidate edges: `2087`
- Strong 300+ chunk gap after resegmentation: `0`

## Package-Level Coverage

| Package | Chunks | Source chunks | Chapters | Sections | Pages | Candidate edges | Edges/chunk | Active-review chunks | High-impact chunks | Zero-candidate chunks |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| source_layer2_chunks | 214 | 214 | 6 | 133 | 19-470 | 0 | 0.0000 | 91 | 64 | 214 |
| full_120_gold_package | 120 | 120 | 6 | 84 | 19-453 | 1436 | 11.9667 | 91 | 64 | 48 |
| priority_100_assigned | 100 | 100 | 6 | 77 | 19-453 | 1371 | 13.7100 | 88 | 64 | 40 |
| remaining_20_in_full_120 | 20 | 20 | 5 | 17 | 61-433 | 65 | 3.2500 | 3 | 0 | 8 |
| all_available_214_optional | 214 | 214 | 6 | 133 | 19-470 | 2004 | 9.3645 | 91 | 64 | 142 |
| strong_resegmented_342_max18_optional_strong | 342 | 214 | 6 | 133 | 19-470 | 2087 | 6.1023 | 119 | 82 | 249 |

## Chapter Coverage

| Chapter | source_layer2_chunks | full_120_gold_package | priority_100_assigned | remaining_20_in_full_120 | all_available_214_optional | strong_resegmented_342_max18_optional_strong |
| --- | --- | --- | --- | --- | --- | --- |
| CH01 | 22 | 20 | 20 | 0 | 22 | 28 |
| CH02 | 29 | 20 | 15 | 5 | 29 | 43 |
| CH03 | 37 | 20 | 16 | 4 | 37 | 60 |
| CH04 | 40 | 20 | 16 | 4 | 40 | 73 |
| CH05 | 57 | 20 | 18 | 2 | 57 | 88 |
| CH06 | 29 | 20 | 15 | 5 | 29 | 50 |

## Top Selected Priority Chunks

| Rank | Chunk | Chapter | Section | Candidate edges | Active items | High-impact | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | JZ-CHUNK-0094 | CH04 | CH04-SEC4_1_1 | 50 | 3 | 3 | active_review,high_impact,dense_candidates |
| 2 | JZ-CHUNK-0020 | CH01 | CH01-SEC1_3_3 | 50 | 5 | 1 | active_review,high_impact,dense_candidates |
| 3 | JZ-CHUNK-0032 | CH02 | CH02-SEC2_2_1 | 50 | 4 | 0 | active_review,dense_candidates |
| 4 | JZ-CHUNK-0016 | CH01 | CH01-SEC1_3_1 | 50 | 3 | 0 | active_review,dense_candidates |
| 5 | JZ-CHUNK-0019 | CH01 | CH01-SEC1_3_3 | 50 | 2 | 0 | active_review,dense_candidates |
| 6 | JZ-CHUNK-0002 | CH01 | CH01-SEC1_1_1 | 50 | 1 | 0 | active_review,dense_candidates |
| 7 | JZ-CHUNK-0099 | CH04 | CH04-SEC4_1_2 | 50 | 1 | 0 | active_review,dense_candidates |
| 8 | JZ-CHUNK-0017 | CH01 | CH01-SEC1_3_1 | 50 | 4 | 0 | active_review,dense_candidates |
| 9 | JZ-CHUNK-0108 | CH04 | CH04-SEC4_2_4 | 48 | 1 | 1 | active_review,high_impact,dense_candidates |
| 10 | JZ-CHUNK-0018 | CH01 | CH01-SEC1_3_2 | 50 | 3 | 0 | active_review,dense_candidates |
| 11 | JZ-CHUNK-0069 | CH03 | CH03-SEC3_2_2 | 16 | 2 | 2 | active_review,high_impact,dense_candidates |
| 12 | JZ-CHUNK-0033 | CH02 | CH02-SEC2_2_1 | 50 | 0 | 0 | dense_candidates |
| 13 | JZ-CHUNK-0098 | CH04 | CH04-SEC4_1_2 | 50 | 0 | 0 | dense_candidates |
| 14 | JZ-CHUNK-0101 | CH04 | CH04-SEC4_1_3 | 50 | 0 | 0 | dense_candidates |
| 15 | JZ-CHUNK-0103 | CH04 | CH04-SEC4_2_1 | 50 | 0 | 0 | dense_candidates |
| 16 | JZ-CHUNK-0104 | CH04 | CH04-SEC4_2_2 | 50 | 0 | 0 | dense_candidates |
| 17 | JZ-CHUNK-0097 | CH04 | CH04-SEC4_1_2 | 43 | 2 | 0 | active_review,dense_candidates |
| 18 | JZ-CHUNK-0196 | CH06 | CH06-SEC6_2_1 | 0 | 3 | 3 | active_review,high_impact |
| 19 | JZ-CHUNK-0188 | CH06 | CH06-SEC6_3 | 0 | 3 | 3 | active_review,high_impact |
| 20 | JZ-CHUNK-0092 | CH04 | CH04-SEC4_4 | 4 | 4 | 3 | active_review,high_impact |

## Output Files

- JSON: `experiments/cape_kg_eacl_20260627/06_release/gold_sampling_coverage_report.json`
- Chapter CSV: `experiments/cape_kg_eacl_20260627/05_review/gold_sampling_coverage_by_chapter.csv`
- Selected chunks CSV: `experiments/cape_kg_eacl_20260627/05_review/gold_sampling_priority100_selected_chunks.csv`
