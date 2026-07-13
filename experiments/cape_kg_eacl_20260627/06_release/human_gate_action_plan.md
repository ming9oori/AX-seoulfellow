# CAPE-KG Human Gate Action Plan

Generated: 2026-06-29T18:55:38.356715+00:00

This is an operational action plan for the remaining human-gold and expert-review gates. It does not create gold labels or paper-claimable evidence by itself.

## Current Gate Status

- Submission readiness: `pending_human_gold_iaa_and_human_gold_scoring`
- Claim gate overall status: `FAIL`
- Return preflight status: `pending_human_returns`
- Minimum-accept blocking items: 4
- Minimum paper-gate return files: 0/11
- Optional/strong claim return files: 0/3
- Required claim/human return files: 0/14
- Optional structural review files are tracked in the 16-file master checklist, but they do not block the minimum paper gate.

## Blocking Items

- `min.gold_chunks`: 100+ adjudicated gold chunks -> Complete two-annotator labeling and adjudication for at least 100 chunks.
- `min.gold_items`: 500+ adjudicated gold node/edge/evidence items -> Adjudicate enough nodes, edges, and evidence anchors to reach 500 gold items.
- `min.iaa`: 2+ annotators and agreement for 100+ chunks -> Import completed annotator A/B files and recompute IAA.
- `min.proposed`: CAPE-KG proposed result completed and scored -> Score P_cape_kg_actual against adjudicated human gold after gold completion.

## Gate Dependency Matrix

| gate | type | minimum | claim status | current progress | missing return files | next action |
|---|---|---:|---|---|---|---|
| `min.iaa` | minimum_accept | yes | pending_human | 0/10 annotation reviewed files present; 0/100 paired completed chunks. | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_A_full_120_priority_batch_001.reviewed.jsonl; experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_B_full_120_priority_batch_001.reviewed.jsonl; experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_002/annotator_A_full_120_priority_batch_002.reviewed.jsonl; experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_002/annotator_B_full_120_priority_batch_002.reviewed.jsonl; experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_003/annotator_A_full_120_priority_batch_003.reviewed.jsonl; experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_003/annotator_B_full_120_priority_batch_003.reviewed.jsonl; experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_004/annotator_A_full_120_priority_batch_004.reviewed.jsonl; experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_004/annotator_B_full_120_priority_batch_004.reviewed.jsonl; experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/annotator_A_full_120_priority_batch_005.reviewed.jsonl; experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/annotator_B_full_120_priority_batch_005.reviewed.jsonl` | Import completed annotator A/B files and recompute IAA. |
| `min.gold_chunks` | minimum_accept | yes | pending_human | 0/100 adjudicated chunks. | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_A_full_120_priority_batch_001.reviewed.jsonl; experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_B_full_120_priority_batch_001.reviewed.jsonl; experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_002/annotator_A_full_120_priority_batch_002.reviewed.jsonl; experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_002/annotator_B_full_120_priority_batch_002.reviewed.jsonl; experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_003/annotator_A_full_120_priority_batch_003.reviewed.jsonl; experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_003/annotator_B_full_120_priority_batch_003.reviewed.jsonl; experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_004/annotator_A_full_120_priority_batch_004.reviewed.jsonl; experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_004/annotator_B_full_120_priority_batch_004.reviewed.jsonl; experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/annotator_A_full_120_priority_batch_005.reviewed.jsonl; experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/annotator_B_full_120_priority_batch_005.reviewed.jsonl; experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/adjudication_edited.jsonl` | Complete two-annotator labeling and adjudication for at least 100 chunks. |
| `min.gold_items` | minimum_accept | yes | pending_human | 0/500 adjudicated node/edge/evidence items in current validation summary. | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_A_full_120_priority_batch_001.reviewed.jsonl; experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_B_full_120_priority_batch_001.reviewed.jsonl; experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_002/annotator_A_full_120_priority_batch_002.reviewed.jsonl; experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_002/annotator_B_full_120_priority_batch_002.reviewed.jsonl; experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_003/annotator_A_full_120_priority_batch_003.reviewed.jsonl; experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_003/annotator_B_full_120_priority_batch_003.reviewed.jsonl; experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_004/annotator_A_full_120_priority_batch_004.reviewed.jsonl; experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_004/annotator_B_full_120_priority_batch_004.reviewed.jsonl; experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/annotator_A_full_120_priority_batch_005.reviewed.jsonl; experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/annotator_B_full_120_priority_batch_005.reviewed.jsonl; experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/adjudication_edited.jsonl` | Adjudicate enough nodes, edges, and evidence anchors to reach 500 gold items. |
| `min.proposed` | minimum_accept | yes | partial | P_cape_kg_actual generated for 120 rows; human-gold scored conditions=[] until adjudication exists. | `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/adjudication_edited.jsonl` | Score P_cape_kg_actual against adjudicated human gold after gold completion. |
| `mapping.expert_review` | optional_strong | no | pending_expert_review | 0/44 source-task-standard groups complete; 0/20 priority Top-5 groups complete; 220 candidate rows pending. | `experiments/cape_kg_eacl_20260627/01_data/mapping_review/mapping_review_items.reviewed.jsonl` | Review Top-5 candidates for the 20 priority groups (100 rows), then run preflight/import. |
| `crosswalk.expert_review` | optional_strong | no | pending_crosswalk_expert_review | 0/22 source-task groups complete; 0/220 rows complete. | `experiments/cape_kg_eacl_20260627/01_data/crosswalk_review/crosswalk_review_items.reviewed.jsonl` | Review crosswalk_review_items.reviewed.jsonl, then run preflight/import. |
| `strong.active_review_effort` | strong_or_auxiliary | no | pending_human_effort_timing | 0/204 reviewed rows; 0 timed rows. | `experiments/cape_kg_eacl_20260627/05_review/active_review_human_effort.reviewed.csv` | Fill active_review_human_effort.reviewed.csv and rerun preflight/refresh. |

## Minimum Thresholds

- Adjudicated chunks: 100
- Gold node/edge/evidence items: 500
- Paired IAA chunks: 100
- Proposed condition to score: `P_cape_kg_actual`
- Mapping review: Top-5 candidates for priority source-task groups; expert P@K/MRR claims require completed groups.

## Current Progress

- Full annotation package chunks: 120
- Annotator A completed chunks: 0
- Annotator B completed chunks: 0
- Paired completed chunks: 0
- Adjudicated chunks: 0
- Annotation reviewed files present: 0/10
- Adjudication reviewed file present: `False`
- Adjudication completed chunks in reviewed return: 0
- Mapping review completed rows: 0
- Mapping review pending rows: 220
- Mapping complete source groups: 0
- Crosswalk review completed/expected rows: 0/220
- Crosswalk complete source groups: 0
- Crosswalk reviewed file present: `False`
- Active-review effort reviewed file present: `False`
- Active-review effort expected/reviewed/timed rows: 204/0/0
- Optional strong package: `strong_resegmented_342_max18`
- Optional strong review units/source chunks: 342/214
- Optional strong candidate edges: 2087
- Optional strong status: `optional_strong_review_handoff_ready_pending_human_review`

## Handoff Files

- Annotator A bundle: `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_human_gold_annotator_A_priority100.tar.gz`
- Annotator B bundle: `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_human_gold_annotator_B_priority100.tar.gz`
- Coordinator bundle: `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_human_gold_coordinator_priority100.tar.gz`
- Adjudicator bundle: `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_human_gold_adjudicator_full120.tar.gz`
- Mapping expert bundle: `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_mapping_expert_review_top20_groups.tar.gz`
- Crosswalk expert bundle: `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_crosswalk_expert_review_ncs_pcf.tar.gz`
- Active-review effort bundle: `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_active_review_human_effort.tar.gz`
- Optional strong 300+ bundle: `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_human_gold_strong_resegmented_342.tar.gz`
- Handoff report: `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/human_review_handoff_report.md`
- Checksums: `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/human_review_handoff_checksums.sha256`

## Tracked Return Files

| minimum | task | owner | batch/group | expected rows | present | status | reviewed file |
|---:|---|---|---|---:|---:|---|---|
| yes | human_gold_annotation | annotator_A | full_120_priority_batch_001 | 20 | no | missing_reviewed_file | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_A_full_120_priority_batch_001.reviewed.jsonl` |
| yes | human_gold_annotation | annotator_B | full_120_priority_batch_001 | 20 | no | missing_reviewed_file | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_B_full_120_priority_batch_001.reviewed.jsonl` |
| yes | human_gold_annotation | annotator_A | full_120_priority_batch_002 | 20 | no | missing_reviewed_file | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_002/annotator_A_full_120_priority_batch_002.reviewed.jsonl` |
| yes | human_gold_annotation | annotator_B | full_120_priority_batch_002 | 20 | no | missing_reviewed_file | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_002/annotator_B_full_120_priority_batch_002.reviewed.jsonl` |
| yes | human_gold_annotation | annotator_A | full_120_priority_batch_003 | 20 | no | missing_reviewed_file | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_003/annotator_A_full_120_priority_batch_003.reviewed.jsonl` |
| yes | human_gold_annotation | annotator_B | full_120_priority_batch_003 | 20 | no | missing_reviewed_file | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_003/annotator_B_full_120_priority_batch_003.reviewed.jsonl` |
| yes | human_gold_annotation | annotator_A | full_120_priority_batch_004 | 20 | no | missing_reviewed_file | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_004/annotator_A_full_120_priority_batch_004.reviewed.jsonl` |
| yes | human_gold_annotation | annotator_B | full_120_priority_batch_004 | 20 | no | missing_reviewed_file | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_004/annotator_B_full_120_priority_batch_004.reviewed.jsonl` |
| yes | human_gold_annotation | annotator_A | full_120_priority_batch_005 | 20 | no | missing_reviewed_file | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/annotator_A_full_120_priority_batch_005.reviewed.jsonl` |
| yes | human_gold_annotation | annotator_B | full_120_priority_batch_005 | 20 | no | missing_reviewed_file | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/annotator_B_full_120_priority_batch_005.reviewed.jsonl` |
| yes | human_gold_adjudication | adjudicator | full_120_adjudication | 120 | no | missing_reviewed_file | `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/adjudication_edited.jsonl` |
| no | mapping_expert_review | mapping_expert | top20_groups_top5_rows | 100 | no | missing_reviewed_file | `experiments/cape_kg_eacl_20260627/01_data/mapping_review/mapping_review_items.reviewed.jsonl` |
| no | crosswalk_expert_review | crosswalk_expert | ncs_pcf_crosswalk_candidates | 220 | no | missing_reviewed_file | `experiments/cape_kg_eacl_20260627/01_data/crosswalk_review/crosswalk_review_items.reviewed.jsonl` |
| no | active_review_human_effort | active_reviewer | pooled_active_uncertainty_random | 204 | no | missing_reviewed_file | `experiments/cape_kg_eacl_20260627/05_review/active_review_human_effort.reviewed.csv` |

## Annotation Batch Order

| batch | rank | chunks | candidate edges | high-impact chunks | A file | B file |
|---|---|---:|---:|---:|---|---|
| full_120_priority_batch_001 | 1-20 | 20 | 811 | 7 | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_A_full_120_priority_batch_001.jsonl` | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_B_full_120_priority_batch_001.jsonl` |
| full_120_priority_batch_002 | 21-40 | 20 | 180 | 16 | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_002/annotator_A_full_120_priority_batch_002.jsonl` | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_002/annotator_B_full_120_priority_batch_002.jsonl` |
| full_120_priority_batch_003 | 41-60 | 20 | 152 | 15 | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_003/annotator_A_full_120_priority_batch_003.jsonl` | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_003/annotator_B_full_120_priority_batch_003.jsonl` |
| full_120_priority_batch_004 | 61-80 | 20 | 91 | 18 | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_004/annotator_A_full_120_priority_batch_004.jsonl` | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_004/annotator_B_full_120_priority_batch_004.jsonl` |
| full_120_priority_batch_005 | 81-100 | 20 | 137 | 8 | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/annotator_A_full_120_priority_batch_005.jsonl` | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/annotator_B_full_120_priority_batch_005.jsonl` |

## Mapping Review Priority

| priority | standard | source task | pending top5 | top score | score gap |
|---:|---|---|---:|---:|---:|
| 0.9564 | PCF | PT 전략 개발 | 5 | 0.311 | 0.0109 |
| 0.9364 | PCF | 경쟁사 분석 | 5 | 0.4117 | 0.0159 |
| 0.9308 | NCS | 목차 개발 | 5 | 0.2208 | 0.0008 |
| 0.926467 | PCF | 제안서 작성 | 5 | 0.2612 | 0.0103 |
| 0.91685 | NCS | 제안전략 개발 | 5 | 0.2127 | 0.0026 |
| 0.910483 | NCS | 레드팀 리뷰 | 5 | 0.1993 | 0.0014 |
| 0.91025 | PCF | 제안계획 수립 | 5 | 0.2427 | 0.0105 |
| 0.90485 | PCF | 킥오프 미팅 | 5 | 0.1983 | 0.0026 |
| 0.8667 | PCF | 제안서 리뷰 | 5 | 0.2778 | 0.0287 |
| 0.8516 | PCF | 수주전략 수립 | 5 | 0.4016 | 0.0371 |
| 0.8492 | PCF | 기회분석 | 5 | 0.276 | 0.0327 |
| 0.834 | NCS | 킥오프 미팅 | 5 | 0.1896 | 0.0185 |
| 0.8112 | PCF | 솔루션 결정 | 5 | 0.3881 | 0.0472 |
| 0.809883 | PCF | 제안팀 구성 | 5 | 0.2125 | 0.0293 |
| 0.8 | NCS | 가격 전략 수립 | 5 | 0.4369 | 0.0534 |
| 0.8 | NCS | 경쟁사 분석 | 5 | 0.365 | 0.0911 |
| 0.8 | NCS | 고객 니즈 분석 | 5 | 0.3761 | 0.0735 |
| 0.8 | NCS | 수주전략 수립 | 5 | 0.4713 | 0.1681 |
| 0.8 | NCS | 제안서 기획 | 5 | 0.3751 | 0.2687 |
| 0.8 | NCS | 제안서 리뷰 | 5 | 0.3646 | 0.0671 |

## Commands

Verify handoff bundle checksums:

```bash
sha256sum -c experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/human_review_handoff_checksums.sha256
```

Check returned review files before applying imports:

```bash
python3 scripts/validate_cape_human_review_returns.py --experiment-dir experiments/cape_kg_eacl_20260627
```

Recommended dry-run wrapper before applying returned files:

```bash
PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=0 bash scripts/run_cape_human_return_apply.sh
```

Recommended apply wrapper after preflight passes:

```bash
PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=1 bash scripts/run_cape_human_return_apply.sh
```

Low-level dry refresh without applying returned files:

```bash
APPLY_IMPORTS=0 bash scripts/run_cape_post_annotation_refresh.sh
```

Low-level apply refresh after preflight passes:

```bash
APPLY_IMPORTS=1 bash scripts/run_cape_post_annotation_refresh.sh
```

Verify final handoff and release checksums:

```bash
python3 scripts/validate_cape_pre_human_handoff.py --experiment-dir experiments/cape_kg_eacl_20260627 --outputs-dir outputs
sha256sum -c experiments/cape_kg_eacl_20260627/06_release/release_bundle_checksums.sha256
```

## Output Files

- JSON: `experiments/cape_kg_eacl_20260627/06_release/human_gate_action_plan.json`
- Markdown: `experiments/cape_kg_eacl_20260627/06_release/human_gate_action_plan.md`
- Required returns CSV: `experiments/cape_kg_eacl_20260627/05_review/human_gate_required_returns.csv`
- Gate dependency matrix CSV: `experiments/cape_kg_eacl_20260627/05_review/human_review_gate_dependency_matrix.csv`
