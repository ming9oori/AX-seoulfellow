# CAPE-KG Human Review Launch Checklist

Generated: `2026-06-29T18:56:34.202649+00:00`
Experiment: `experiments/cape_kg_eacl_20260627`

이 문서는 검수자가 바로 시작하기 위한 실행표입니다. 기존 master checklist보다 더 작게, 최소 제출 gate를 여는 데 필요한 파일명과 명령만 앞에 배치합니다.

## Current Gate State

| item | value |
|---|---:|
| Claim gate | `FAIL` |
| Required claim-gate failures | 4 |
| Human return preflight | `pending_human_returns` |
| Minimum return files present | 0/11 |
| Annotation reviewed files present | 0/10 |
| Adjudication reviewed file present | 0/1 |
| Mapping/crosswalk/active optional files present | 0/3 |

## Priority-100 선정 근거

| item | value |
|---|---:|
| Selected chunks | 100/100 |
| Batch count / size | 5 / 20 |
| Candidate edges covered | 1371/1436 |
| Candidate-edge coverage | 0.954735 |
| Active-review chunk coverage | 0.967033 |
| High-impact chunk coverage | 1.000000 |
| Claim status | `gold_sampling_coverage_ready_pending_human_review` |
| Report | `experiments/cape_kg_eacl_20260627/06_release/gold_sampling_coverage_report.md` |

이 표는 100개 chunk 선정이 충분한 coverage를 갖는지 보여주는 운영 근거입니다. 실제 gold claim은 A/B 검수, IAA, adjudication 이후에만 가능합니다.

## Minimum Gate Launch Tasks

| # | phase | actor | open | save as | command |
|---:|---|---|---|---|---|
| 1 | `0_package_integrity` | coordinator | `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/human_review_handoff_checksums.sha256` | `` | `sha256sum -c experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/human_review_handoff_checksums.sha256` |
| 2 | `1_independent_annotation` | annotator_A | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_A_full_120_priority_batch_001.jsonl` | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_A_full_120_priority_batch_001.reviewed.jsonl` |  |
| 3 | `1_independent_annotation` | annotator_B | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_B_full_120_priority_batch_001.jsonl` | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_B_full_120_priority_batch_001.reviewed.jsonl` |  |
| 4 | `1_independent_annotation` | annotator_A | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_002/annotator_A_full_120_priority_batch_002.jsonl` | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_002/annotator_A_full_120_priority_batch_002.reviewed.jsonl` |  |
| 5 | `1_independent_annotation` | annotator_B | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_002/annotator_B_full_120_priority_batch_002.jsonl` | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_002/annotator_B_full_120_priority_batch_002.reviewed.jsonl` |  |
| 6 | `1_independent_annotation` | annotator_A | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_003/annotator_A_full_120_priority_batch_003.jsonl` | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_003/annotator_A_full_120_priority_batch_003.reviewed.jsonl` |  |
| 7 | `1_independent_annotation` | annotator_B | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_003/annotator_B_full_120_priority_batch_003.jsonl` | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_003/annotator_B_full_120_priority_batch_003.reviewed.jsonl` |  |
| 8 | `1_independent_annotation` | annotator_A | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_004/annotator_A_full_120_priority_batch_004.jsonl` | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_004/annotator_A_full_120_priority_batch_004.reviewed.jsonl` |  |
| 9 | `1_independent_annotation` | annotator_B | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_004/annotator_B_full_120_priority_batch_004.jsonl` | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_004/annotator_B_full_120_priority_batch_004.reviewed.jsonl` |  |
| 10 | `1_independent_annotation` | annotator_A | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/annotator_A_full_120_priority_batch_005.jsonl` | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/annotator_A_full_120_priority_batch_005.reviewed.jsonl` |  |
| 11 | `1_independent_annotation` | annotator_B | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/annotator_B_full_120_priority_batch_005.jsonl` | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/annotator_B_full_120_priority_batch_005.reviewed.jsonl` |  |
| 12 | `2_preflight` | coordinator | `experiments/cape_kg_eacl_20260627/05_review/human_gate_required_returns.csv` | `experiments/cape_kg_eacl_20260627/06_release/human_review_return_preflight.md` | `python3 scripts/validate_cape_human_review_returns.py --experiment-dir experiments/cape_kg_eacl_20260627` |
| 13 | `3_dry_run` | coordinator | `` | `experiments/cape_kg_eacl_20260627/06_release/human_return_apply_last_run.md` | `PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=0 bash scripts/run_cape_human_return_apply.sh` |
| 14 | `4_apply_annotation_returns` | coordinator | `` | `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/annotator_A.jsonl; experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/annotator_B.jsonl` | `PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=1 bash scripts/run_cape_human_return_apply.sh` |
| 15 | `5_adjudication` | adjudicator | `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/adjudication_draft.jsonl` | `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/adjudication_edited.jsonl` |  |
| 16 | `6_apply_adjudication` | coordinator | `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/adjudication_edited.jsonl` | `experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_metrics.json` | `PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=1 bash scripts/run_cape_human_return_apply.sh` |
| 17 | `7_final_validation` | coordinator | `experiments/cape_kg_eacl_20260627/06_release/claim_gate_report.md` | `experiments/cape_kg_eacl_20260627/06_release/pre_human_handoff_validation.md` | `python3 scripts/validate_cape_pre_human_handoff.py --experiment-dir experiments/cape_kg_eacl_20260627 --outputs-dir outputs` |
| 18 | `7_final_validation` | coordinator | `experiments/cape_kg_eacl_20260627/06_release/release_bundle_checksums.sha256` | `` | `sha256sum -c experiments/cape_kg_eacl_20260627/06_release/release_bundle_checksums.sha256` |

## Required Reviewed Filenames

| task | owner | batch | expected rows | reviewed filename | present |
|---|---|---|---:|---|---|
| human_gold_annotation | annotator_A | full_120_priority_batch_001 | 20 | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_A_full_120_priority_batch_001.reviewed.jsonl` | no |
| human_gold_annotation | annotator_B | full_120_priority_batch_001 | 20 | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_B_full_120_priority_batch_001.reviewed.jsonl` | no |
| human_gold_annotation | annotator_A | full_120_priority_batch_002 | 20 | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_002/annotator_A_full_120_priority_batch_002.reviewed.jsonl` | no |
| human_gold_annotation | annotator_B | full_120_priority_batch_002 | 20 | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_002/annotator_B_full_120_priority_batch_002.reviewed.jsonl` | no |
| human_gold_annotation | annotator_A | full_120_priority_batch_003 | 20 | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_003/annotator_A_full_120_priority_batch_003.reviewed.jsonl` | no |
| human_gold_annotation | annotator_B | full_120_priority_batch_003 | 20 | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_003/annotator_B_full_120_priority_batch_003.reviewed.jsonl` | no |
| human_gold_annotation | annotator_A | full_120_priority_batch_004 | 20 | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_004/annotator_A_full_120_priority_batch_004.reviewed.jsonl` | no |
| human_gold_annotation | annotator_B | full_120_priority_batch_004 | 20 | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_004/annotator_B_full_120_priority_batch_004.reviewed.jsonl` | no |
| human_gold_annotation | annotator_A | full_120_priority_batch_005 | 20 | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/annotator_A_full_120_priority_batch_005.reviewed.jsonl` | no |
| human_gold_annotation | annotator_B | full_120_priority_batch_005 | 20 | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/annotator_B_full_120_priority_batch_005.reviewed.jsonl` | no |
| human_gold_adjudication | adjudicator | full_120_adjudication | 120 | `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/adjudication_edited.jsonl` | no |

## Optional Strong/Utility Tasks

| actor | task | open | save as | note |
|---|---|---|---|---|
| mapping_expert | mapping_expert_review | `experiments/cape_kg_eacl_20260627/01_data/mapping_review/mapping_review_items.jsonl` | `experiments/cape_kg_eacl_20260627/01_data/mapping_review/mapping_review_items.reviewed.jsonl` | optional/strong claim용이며 minimum human-gold gate를 대체하지 않습니다. |
| crosswalk_expert | crosswalk_expert_review | `experiments/cape_kg_eacl_20260627/01_data/crosswalk_review/crosswalk_review_items.jsonl` | `experiments/cape_kg_eacl_20260627/01_data/crosswalk_review/crosswalk_review_items.reviewed.jsonl` | optional/strong claim용이며 minimum human-gold gate를 대체하지 않습니다. |
| active_reviewer | active_review_human_effort | `experiments/cape_kg_eacl_20260627/05_review/active_review_human_effort_template.csv` | `experiments/cape_kg_eacl_20260627/05_review/active_review_human_effort.reviewed.csv` | optional/strong claim용이며 minimum human-gold gate를 대체하지 않습니다. |

## Commands

### verify_handoff_checksums

```bash
sha256sum -c experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/human_review_handoff_checksums.sha256
```

### validate_returns

```bash
python3 scripts/validate_cape_human_review_returns.py --experiment-dir experiments/cape_kg_eacl_20260627
```

### dry_apply

```bash
PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=0 bash scripts/run_cape_human_return_apply.sh
```

### apply_returns

```bash
PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=1 bash scripts/run_cape_human_return_apply.sh
```

### validate_pre_human

```bash
python3 scripts/validate_cape_pre_human_handoff.py --experiment-dir experiments/cape_kg_eacl_20260627 --outputs-dir outputs
```

### release_checksums

```bash
sha256sum -c experiments/cape_kg_eacl_20260627/06_release/release_bundle_checksums.sha256
```

## Claim Safety

- 이 checklist는 작업 시작을 위한 운영 산출물이며 human-gold evidence가 아닙니다.
- `P_cape_kg_actual`의 최종 성능 claim은 adjudication 완료 후 human-gold scoring이 다시 생성될 때만 가능합니다.
- mapping P@K/MRR/nDCG, NCS-PCF crosswalk utility, active-review efficiency는 각각 expert review와 effort CSV가 돌아온 뒤에만 claim할 수 있습니다.
