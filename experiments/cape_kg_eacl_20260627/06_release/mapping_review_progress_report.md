# CAPE-KG Mapping Review Progress Report

Generated: 2026-06-29T18:55:24.457941+00:00

This is a workflow/progress report for expert mapping review. It does not turn mapping candidates into gold labels by itself.

A source task group becomes evaluable only when every Top-5 candidate in that standard/source group has a completed expert decision.

## Summary

| standard | candidate rows | completed rows | pending rows | source groups | complete groups | pending groups |
|---|---:|---:|---:|---:|---:|---:|
| NCS | 110 | 0 | 110 | 22 | 0 | 22 |
| PCF | 110 | 0 | 110 | 22 | 0 | 22 |

## Top Pending Groups

| priority | standard | source task | pending Top-5 | top score | score gap | reason |
|---:|---|---|---:|---:|---:|---|
| 0.9564 | PCF | PT 전략 개발 | 5 | 0.311 | 0.0109 | 5 Top-5 rows pending; high-scoring candidates |
| 0.9364 | PCF | 경쟁사 분석 | 5 | 0.4117 | 0.0159 | 5 Top-5 rows pending; high-scoring candidates |
| 0.9308 | NCS | 목차 개발 | 5 | 0.2208 | 0.0008 | 5 Top-5 rows pending; close scores; high-scoring candidates |
| 0.926467 | PCF | 제안서 작성 | 5 | 0.2612 | 0.0103 | 5 Top-5 rows pending; high-scoring candidates |
| 0.91685 | NCS | 제안전략 개발 | 5 | 0.2127 | 0.0026 | 5 Top-5 rows pending; close scores; high-scoring candidates |
| 0.910483 | NCS | 레드팀 리뷰 | 5 | 0.1993 | 0.0014 | 5 Top-5 rows pending; close scores; high-scoring candidates |
| 0.91025 | PCF | 제안계획 수립 | 5 | 0.2427 | 0.0105 | 5 Top-5 rows pending; high-scoring candidates |
| 0.90485 | PCF | 킥오프 미팅 | 5 | 0.1983 | 0.0026 | 5 Top-5 rows pending; close scores; high-scoring candidates |
| 0.8667 | PCF | 제안서 리뷰 | 5 | 0.2778 | 0.0287 | 5 Top-5 rows pending; high-scoring candidates |
| 0.8516 | PCF | 수주전략 수립 | 5 | 0.4016 | 0.0371 | 5 Top-5 rows pending; high-scoring candidates |
| 0.8492 | PCF | 기회분석 | 5 | 0.276 | 0.0327 | 5 Top-5 rows pending; high-scoring candidates |
| 0.834 | NCS | 킥오프 미팅 | 5 | 0.1896 | 0.0185 | 5 Top-5 rows pending; high-scoring candidates |
| 0.8112 | PCF | 솔루션 결정 | 5 | 0.3881 | 0.0472 | 5 Top-5 rows pending; high-scoring candidates |
| 0.809883 | PCF | 제안팀 구성 | 5 | 0.2125 | 0.0293 | 5 Top-5 rows pending; high-scoring candidates |
| 0.8 | NCS | 가격 전략 수립 | 5 | 0.4369 | 0.0534 | 5 Top-5 rows pending; high-scoring candidates |
| 0.8 | NCS | 경쟁사 분석 | 5 | 0.365 | 0.0911 | 5 Top-5 rows pending; high-scoring candidates |
| 0.8 | NCS | 고객 니즈 분석 | 5 | 0.3761 | 0.0735 | 5 Top-5 rows pending; high-scoring candidates |
| 0.8 | NCS | 수주전략 수립 | 5 | 0.4713 | 0.1681 | 5 Top-5 rows pending; high-scoring candidates |
| 0.8 | NCS | 제안서 기획 | 5 | 0.3751 | 0.2687 | 5 Top-5 rows pending; high-scoring candidates |
| 0.8 | NCS | 제안서 리뷰 | 5 | 0.3646 | 0.0671 | 5 Top-5 rows pending; high-scoring candidates |
| 0.8 | NCS | 제안서 작성 | 5 | 0.4415 | 0.269 | 5 Top-5 rows pending; high-scoring candidates |
| 0.8 | PCF | 가격 전략 수립 | 5 | 0.5082 | 0.0607 | 5 Top-5 rows pending; high-scoring candidates |
| 0.8 | PCF | 고객 니즈 분석 | 5 | 0.3944 | 0.0582 | 5 Top-5 rows pending; high-scoring candidates |
| 0.8 | PCF | 제안서 기획 | 5 | 0.3058 | 0.054 | 5 Top-5 rows pending; high-scoring candidates |
| 0.8 | PCF | 제안전략 개발 | 5 | 0.4096 | 0.103 | 5 Top-5 rows pending; high-scoring candidates |

## Generated Files

- Progress summary JSON: `experiments/cape_kg_eacl_20260627/06_release/mapping_review_progress_summary.json`
- Group priority CSV: `experiments/cape_kg_eacl_20260627/05_review/mapping_review_priority_queue.csv`
- Group priority JSONL: `experiments/cape_kg_eacl_20260627/05_review/mapping_review_priority_queue.jsonl`
- Next 20 groups CSV: `experiments/cape_kg_eacl_20260627/05_review/mapping_review_next_20_groups.csv`
- Next 60 rows CSV: `experiments/cape_kg_eacl_20260627/05_review/mapping_review_next_60_rows.csv`
- Top-20 group briefing MD: `experiments/cape_kg_eacl_20260627/06_release/mapping_review_group_briefing.md`
- Top-20 group briefing CSV: `experiments/cape_kg_eacl_20260627/05_review/mapping_review_group_briefing_top20.csv`

Use the next-groups file to finish complete Top-5 groups first; use the next-rows file when assigning row-level review tasks.
