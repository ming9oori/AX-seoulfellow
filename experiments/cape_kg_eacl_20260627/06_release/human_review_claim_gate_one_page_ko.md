# CAPE-KG Claim Gate 해제용 사람 검수 1-page 운영표

Generated for `experiments/cape_kg_eacl_20260627`.

이 문서는 revised EACL plan의 남은 gate를 열기 위해 사람이 실제로 반환해야 하는 파일과 반영 명령만 압축한 운영표다. 여기의 모든 항목은 사람 검수 완료 전까지 논문 성능 claim이 아니라 `pending_human_returns` 상태다.

## 현재 결론

| 항목 | 현재 상태 |
|---|---|
| Claim gate | `FAIL` |
| Pre-human validation | `PASS`, 최신 `06_release/pre_human_handoff_validation.md` 기준 |
| Minimum paper-gate return files | 0/11 |
| Required claim/human return files | 0/14 |
| Optional structural return files | 0/2 |
| Latest release stamp | `06_release/latest_release_bundle_index.md` 기준 |

## Minimum Paper Gate를 여는 필수 반환 파일

아래 11개 파일이 정확한 경로와 파일명으로 저장되어야 100 chunk human-gold, IAA, adjudication, proposed-vs-gold scoring으로 넘어갈 수 있다.

| 순서 | 담당 | 열 파일 | 저장할 reviewed file |
|---:|---|---|---|
| 1 | Annotator A | `05_review/human_gold_batches/full_120_priority_batch_001/annotator_A_full_120_priority_batch_001.jsonl` | `05_review/human_gold_batches/full_120_priority_batch_001/annotator_A_full_120_priority_batch_001.reviewed.jsonl` |
| 2 | Annotator B | `05_review/human_gold_batches/full_120_priority_batch_001/annotator_B_full_120_priority_batch_001.jsonl` | `05_review/human_gold_batches/full_120_priority_batch_001/annotator_B_full_120_priority_batch_001.reviewed.jsonl` |
| 3 | Annotator A | `05_review/human_gold_batches/full_120_priority_batch_002/annotator_A_full_120_priority_batch_002.jsonl` | `05_review/human_gold_batches/full_120_priority_batch_002/annotator_A_full_120_priority_batch_002.reviewed.jsonl` |
| 4 | Annotator B | `05_review/human_gold_batches/full_120_priority_batch_002/annotator_B_full_120_priority_batch_002.jsonl` | `05_review/human_gold_batches/full_120_priority_batch_002/annotator_B_full_120_priority_batch_002.reviewed.jsonl` |
| 5 | Annotator A | `05_review/human_gold_batches/full_120_priority_batch_003/annotator_A_full_120_priority_batch_003.jsonl` | `05_review/human_gold_batches/full_120_priority_batch_003/annotator_A_full_120_priority_batch_003.reviewed.jsonl` |
| 6 | Annotator B | `05_review/human_gold_batches/full_120_priority_batch_003/annotator_B_full_120_priority_batch_003.jsonl` | `05_review/human_gold_batches/full_120_priority_batch_003/annotator_B_full_120_priority_batch_003.reviewed.jsonl` |
| 7 | Annotator A | `05_review/human_gold_batches/full_120_priority_batch_004/annotator_A_full_120_priority_batch_004.jsonl` | `05_review/human_gold_batches/full_120_priority_batch_004/annotator_A_full_120_priority_batch_004.reviewed.jsonl` |
| 8 | Annotator B | `05_review/human_gold_batches/full_120_priority_batch_004/annotator_B_full_120_priority_batch_004.jsonl` | `05_review/human_gold_batches/full_120_priority_batch_004/annotator_B_full_120_priority_batch_004.reviewed.jsonl` |
| 9 | Annotator A | `05_review/human_gold_batches/full_120_priority_batch_005/annotator_A_full_120_priority_batch_005.jsonl` | `05_review/human_gold_batches/full_120_priority_batch_005/annotator_A_full_120_priority_batch_005.reviewed.jsonl` |
| 10 | Annotator B | `05_review/human_gold_batches/full_120_priority_batch_005/annotator_B_full_120_priority_batch_005.jsonl` | `05_review/human_gold_batches/full_120_priority_batch_005/annotator_B_full_120_priority_batch_005.reviewed.jsonl` |
| 11 | Adjudicator | `01_data/gold_annotation/full_120/adjudication_draft.jsonl` | `01_data/gold_annotation/full_120/adjudication_edited.jsonl` |

## Minimum Gate 실행 순서

1. Annotator A/B가 batch 001-005를 독립적으로 완료한다.
2. 반환 파일 10개를 위 reviewed filename 그대로 저장한다.
3. preflight를 실행한다.
4. dry-run wrapper를 실행해 import 가능성을 확인한다.
5. adjudicator가 `adjudication_draft.jsonl`을 검토해 `adjudication_edited.jsonl`로 저장한다.
6. preflight를 다시 실행한다.
7. `APPLY_IMPORTS=1`로 실제 반영한다.
8. claim gate, paper table, release bundle을 다시 확인한다.

```bash
python3 scripts/validate_cape_human_review_returns.py \
  --experiment-dir experiments/cape_kg_eacl_20260627

PYTHON_BIN=python3 \
LLM_PYTHON=python3 \
APPLY_IMPORTS=0 \
bash scripts/run_cape_human_return_apply.sh

PYTHON_BIN=python3 \
LLM_PYTHON=python3 \
APPLY_IMPORTS=1 \
bash scripts/run_cape_human_return_apply.sh
```

## Strong/Optional Claim을 여는 추가 반환 파일

| claim | 담당 | 열 파일 | 저장할 reviewed file |
|---|---|---|---|
| NCS/PCF mapping P@K/MRR/nDCG | Mapping expert | `01_data/mapping_review/mapping_review_items.jsonl` | `01_data/mapping_review/mapping_review_items.reviewed.jsonl` |
| NCS-PCF crosswalk utility | Crosswalk expert | `01_data/crosswalk_review/crosswalk_review_items.jsonl` | `01_data/crosswalk_review/crosswalk_review_items.reviewed.jsonl` |
| Active-review efficiency | Active reviewer | `05_review/active_review_human_effort_template.csv` | `05_review/active_review_human_effort.reviewed.csv` |
| Optional 300+ gold review | Annotator A/B + adjudicator | `01_data/gold_annotation/strong_resegmented_342_max18/` | `annotator_A_edited.jsonl`, `annotator_B_edited.jsonl`, `adjudication_edited.jsonl` |

Optional strong package는 아래 wrapper를 별도로 사용한다.

```bash
PYTHON_BIN=python3 \
APPLY_IMPORTS=0 \
bash scripts/run_cape_strong_return_apply.sh

PYTHON_BIN=python3 \
APPLY_IMPORTS=1 \
bash scripts/run_cape_strong_return_apply.sh
```

## 반영 후 반드시 확인할 파일

| 목적 | 파일 |
|---|---|
| gate 결과 | `06_release/claim_gate_report.md` |
| scoring readiness | `06_release/post_human_scoring_readiness.md` |
| paper readiness | `06_release/paper_readiness_checklist.md` |
| 사람 검수 상태 | `06_release/human_review_status_dashboard_ko.md` |
| 최종 검증 | `06_release/pre_human_handoff_validation.md` |
| release bundle | `06_release/latest_release_bundle_index.md` |

## 안전 문구

- reviewed file이 없으면 `APPLY_IMPORTS=1`은 기본적으로 거부된다.
- preflight 오류가 있으면 import하지 않는다.
- silver/proxy score는 human-gold score로 대체할 수 없다.
- claim gate가 `PASS`로 바뀌기 전까지 main table에는 pending 또는 diagnostic-only로 표시한다.
