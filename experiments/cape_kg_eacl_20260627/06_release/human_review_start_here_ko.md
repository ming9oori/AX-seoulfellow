# CAPE-KG 사람 검수 시작 안내

Generated for `experiments/cape_kg_eacl_20260627`.
Last synchronized with the refreshed dashboard, release bundle index, and professor-report index on `2026-06-29`.

이 문서는 EACL 제출 gate에서 아직 실패 중인 사람 검수 항목을 실제로 진행하기 위한 시작점이다. 아래 파일은 workflow 보조 자료이며, 사람이 검수하고 import/adjudication을 끝내기 전까지는 논문용 gold evidence가 아니다.

## 빠른 결론

- 현재 claim gate는 `FAIL`이다.
- minimum paper-gate 반환 파일은 `0/11`개, optional/strong claim 반환 파일은 `0/3`개, Required claim/human 반환 파일은 `0/14`개다.
- 선택 structural review 반환 파일은 `0/2`개이며, 이를 포함한 master 추적 반환 파일은 `0/16`개다.
- 자동 파이프라인, handoff bundle, release bundle, pre-human validation은 실행 가능 상태로 정리되어 있다.
- 아직 완료되지 않은 것은 사람이 반환해야 하는 annotation/adjudication/expert review/effort 파일이다.
- 최신 release stamp와 bundle SHA256은 항상 `06_release/latest_release_bundle_index.md`를 기준으로 확인한다.

## 최신 동기화 기준

| 항목 | 기준 파일/상태 |
|---|---|
| 최신 release bundle index | `06_release/latest_release_bundle_index.md` |
| pre-human validation | `06_release/pre_human_handoff_validation.md`에서 `PASS`, `FAIL=0` 확인 |
| 사람 검수 상태판 | `06_release/human_review_status_dashboard_ko.md` |
| claim gate | `06_release/claim_gate_report.md`에서 human-gated `FAIL` 확인 |
| 교수님 보고용 핵심 요약 | `07_reports/professor_report_core_contents_separate_20260629_ko.md` |
| 교수님 발표 슬라이드 원고 | `07_reports/professor_report_slide_contents_current_20260628_ko.md` |
| 발표/보고 문서 index | `07_reports/README_current_reports_ko.md` |

위 상태에서 `pre-human validation PASS`는 제출 성능 주장이 완료되었다는 뜻이 아니다. 현재 의미는 "자동 구축 결과, prompt/LLM trace, KG export, Neo4j/시각화, release/handoff 패키지가 사람 검수에 들어갈 수 있는 상태"라는 것이다.

가장 먼저 볼 파일:

- Claim gate 1-page 운영표: `06_release/human_review_claim_gate_one_page_ko.md`
- 상태 대시보드: `06_release/human_review_status_dashboard_ko.md`
- 실행 체크리스트: `06_release/human_review_launch_checklist_ko.md`
- 첫 배치 실행 카드: `05_review/human_review_first_batch_execution_card_ko.md`
- 역할별 quickstart: `05_review/human_review_role_quickstart_cards_ko.md`
- 전체 master checklist: `06_release/human_review_master_checklist_ko.md`

교수님께 현재 방법론과 산출물을 설명할 때는 아래 순서로 보는 것이 가장 안전하다.

1. `07_reports/professor_report_core_contents_separate_20260629_ko.md`: 실제 prompt, CQ 생성 방식, node/edge 산출 방식, 현재 산출 수치 중심 요약
2. `07_reports/professor_report_slide_contents_current_20260628_ko.md`: 슬라이드별 발표 원고
3. `06_release/pre_human_handoff_validation.md`: 자동 산출물 검증 결과
4. `06_release/claim_gate_report.md`: 아직 주장하면 안 되는 human/expert-gated 항목
5. `06_release/human_review_claim_gate_one_page_ko.md`: claim gate를 열기 위해 실제로 반환해야 하는 파일과 명령

## 현재 막힌 gate

| gate | 필요한 완료 상태 | 현재 상태 |
|---|---:|---:|
| Minimum return files | required reviewed files 11개 | 0/11 |
| Human-gold chunks | adjudicated chunk >= 100 | 0 |
| Human-gold items | node/edge/evidence item >= 500 | 0 |
| IAA | 2명 annotator agreement >= 100 chunks | 0 |
| Proposed scoring | `P_cape_kg_actual` vs adjudicated gold | gold 없음 |
| Mapping expert review | NCS/PCF Top-5 group expert decision | 0 complete groups |
| NCS-PCF crosswalk expert review | crosswalk source groups expert decision | 0 complete groups |
| Active-review human effort | effort/timing rows reviewed | 0 reviewed rows |

## Priority-100 선정 근거

minimum gate를 빠르게 열기 위해 먼저 검수할 100개 chunk를 우선순위 batch 5개로 나누었다.

| item | value |
|---|---:|
| Selected chunks | 100/100 |
| Batch count / size | 5 / 20 |
| Candidate edges covered | 1371/1436 |
| Candidate-edge coverage | 0.954735 |
| Active-review chunk coverage | 0.967033 |
| High-impact chunk coverage | 1.000000 |
| Source report | `06_release/gold_sampling_coverage_report.md` |

이 표는 검수 우선순위와 coverage를 설명하는 운영 근거다. 실제 human-gold 성능 claim은 Annotator A/B 검수, IAA, adjudication, human-gold scoring이 끝난 뒤에만 가능하다.

## 1. Human Gold Annotation

먼저 100개 chunk만 완료해도 minimum-accept gate를 열 수 있다.

내부 handoff bundle:

- Annotator A: `06_release/human_review_handoff/cape_human_gold_annotator_A_priority100.tar.gz`
- Annotator B: `06_release/human_review_handoff/cape_human_gold_annotator_B_priority100.tar.gz`
- Coordinator: `06_release/human_review_handoff/cape_human_gold_coordinator_priority100.tar.gz`
- Handoff report: `06_release/human_review_handoff/human_review_handoff_report.md`
- Checksums: `06_release/human_review_handoff/human_review_handoff_checksums.sha256`

검증:

```bash
sha256sum -c experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/human_review_handoff_checksums.sha256
```

시작 파일:

- 전체 annotation workbench: `01_data/gold_annotation/annotation_workbench.html`
- 상세 annotation guideline: `01_data/annotation_guideline_v1.md`
- 전체 annotation protocol: `01_data/gold_annotation/adjudication_protocol.md`
- 첫 배치 실행 카드: `05_review/human_review_first_batch_execution_card_ko.md`
- 역할별 quickstart: `05_review/human_review_role_quickstart_cards_ko.md`
- 우선순위 100개 목록: `05_review/human_gold_next_100_worklist.csv`
- 20개 단위 batch 목록: `05_review/human_gold_batches/full_120_batch_assignment_overview.csv`

가장 먼저 열 batch:

- `05_review/human_gold_batches/full_120_priority_batch_001/README.md`
- annotator A 입력: `05_review/human_gold_batches/full_120_priority_batch_001/annotator_A_full_120_priority_batch_001.jsonl`
- annotator B 입력: `05_review/human_gold_batches/full_120_priority_batch_001/annotator_B_full_120_priority_batch_001.jsonl`

권장 순서:

1. Annotator A와 B가 서로 독립적으로 같은 batch 파일을 검수한다.
2. 각 annotator는 workbench에서 자기 JSONL을 load한다.
3. chunk text만 근거로 candidate edge를 accept/reject하고, 빠진 edge가 있으면 추가한다.
4. 모든 accepted edge에는 evidence anchor 또는 exact span을 남긴다.
5. `annotation_status`를 `completed` 또는 불확실하면 `needs_adjudication`으로 둔다.
6. export 파일명을 batch README의 `.reviewed.jsonl` 이름과 맞춘다.
7. 전체 반환 파일 preflight를 먼저 실행한다.
8. 운영 반영은 안전 wrapper를 기본 경로로 사용한다. 먼저 `APPLY_IMPORTS=0`으로 dry-run을 실행하고, 통과하면 `APPLY_IMPORTS=1`로 실제 반영한다. 개별 import 명령의 `--apply`는 특정 파일 디버깅 때만 사용한다.

100개 chunk를 채우려면 `full_120_priority_batch_001`부터 `full_120_priority_batch_005`까지 두 annotator가 모두 완료해야 한다.

## 1-A. Optional Strong 300+ Human Gold Review

강한 accept 가능권의 300~500 chunk human-gold 목표를 위해, 같은 원본 corpus를 source sentence 단위로 재분할한 선택 검수 패키지도 준비되어 있다. 이 패키지는 minimum paper-gate의 annotation/adjudication 반환 파일을 대체하지 않는다.

내부 handoff bundle:

- Optional strong 300+ review: `06_release/human_review_handoff/cape_human_gold_strong_resegmented_342.tar.gz`
- Handoff README: `06_release/human_review_handoff/README_strong_resegmented_review_ko.md`
- Package manifest: `06_release/human_review_handoff/strong_resegmented_review_manifest.json`

시작 파일:

- Package: `01_data/gold_annotation/strong_resegmented_342_max18/`
- Annotator A input: `01_data/gold_annotation/strong_resegmented_342_max18/annotator_A.jsonl`
- Annotator B input: `01_data/gold_annotation/strong_resegmented_342_max18/annotator_B.jsonl`
- Tracking sheet: `01_data/gold_annotation/strong_resegmented_342_max18/tracking_sheet.csv`
- Expansion report: `01_data/gold_annotation/annotation_expansion_report.md`

검수 단위:

- review units: 342
- max source sentences per unit: 18
- 각 row는 `source_chunk_id`와 `split_sentence_ids`를 포함한다.

주의:

- 이 패키지를 받았다는 사실만으로 300+ human-gold claim을 할 수 없다.
- Annotator A/B 독립 검수, IAA, adjudication, human-gold scoring까지 완료되어야 한다.
- 현재 post-refresh 자동 import 대상은 minimum gate 중심이므로, strong package는 bundle README의 수동 dry-run/import 명령을 따른다.

## 2. IAA와 Adjudication

두 annotator가 `.reviewed.jsonl` 파일을 반환하면 먼저 아래 preflight를 실행한다. 이 명령은 아직 import하지 않고, 반환 파일의 chunk id, batch coverage, immutable field 변경, schema/evidence 오류를 검사한다.

```bash
python3 scripts/validate_cape_human_review_returns.py \
  --experiment-dir experiments/cape_kg_eacl_20260627
```

preflight 결과 파일:

- `06_release/human_review_return_preflight.md`
- `06_release/human_review_return_preflight.json`

preflight에서 error가 없으면 안전 wrapper로 먼저 dry-run을 실행한다. 이 wrapper는 preflight, refresh, checksum 확인을 함께 수행한다.

```bash
PYTHON_BIN=python3 \
LLM_PYTHON=python3 \
APPLY_IMPORTS=0 \
bash scripts/run_cape_human_return_apply.sh
```

dry-run과 preflight가 모두 통과하면 반환 파일을 실제 반영한다.

```bash
PYTHON_BIN=python3 \
LLM_PYTHON=python3 \
APPLY_IMPORTS=1 \
bash scripts/run_cape_human_return_apply.sh
```

확인할 파일:

- IAA summary: `01_data/gold_annotation/iaa_full_120/iaa_summary.json`
- adjudication draft: `01_data/gold_annotation/full_120/adjudication_draft.jsonl`
- adjudication report: `01_data/gold_annotation/full_120/adjudication_draft_report.md`
- validation summary: `04_evaluation/human_gold_validation_summary.json`

adjudicator는 `adjudication_draft.jsonl`의 disagreement를 해결한 뒤 최종 `adjudication.jsonl`에 import한다. 그 다음 refresh를 다시 실행하면 human-gold scoring과 claim gate가 갱신된다.

Adjudicator 전용 handoff bundle:

- Adjudicator: `06_release/human_review_handoff/cape_human_gold_adjudicator_full120.tar.gz`
- Handoff README: `06_release/human_review_handoff/README_adjudicator_ko.md`

adjudicator가 반환해야 하는 파일명:

```text
experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/adjudication_edited.jsonl
```

이 파일은 `scripts/validate_cape_human_review_returns.py` preflight 대상에 포함되어 있으며, validation error가 없을 때만 import한다.

## 3. NCS/PCF Mapping Expert Review

mapping downstream claim은 expert review가 없으면 아직 논문 주장으로 쓸 수 없다.

내부 handoff bundle:

- Mapping expert: `06_release/human_review_handoff/cape_mapping_expert_review_top20_groups.tar.gz`
- Handoff README: `06_release/human_review_handoff/README_mapping_expert_ko.md`

시작 파일:

- workbench: `01_data/mapping_review/mapping_review_workbench.html`
- protocol: `01_data/mapping_review/mapping_review_protocol.md`
- 전체 row: `01_data/mapping_review/mapping_review_items.jsonl`
- 우선순위 group: `05_review/mapping_review_next_20_groups.csv`
- 우선순위 row: `05_review/mapping_review_next_60_rows.csv`

검수 단위:

- source task + standard별 Top-5 후보 5개를 하나의 group으로 본다.
- group 5개 row가 모두 `completed`가 되어야 P@K/MRR 계산에 들어간다.

결정값:

- `accepted`: 타당한 mapping
- `rejected`: 부적절한 mapping
- `unsure`: 근거 부족
- `relevance_grade`: 0, 1, 2, 3

reviewed JSONL을 export한 뒤 dry-run import를 실행한다.

전체 반환 파일 상태는 human-gold와 동일한 preflight 명령으로 먼저 확인할 수 있다.

```bash
python3 scripts/validate_cape_human_review_returns.py \
  --experiment-dir experiments/cape_kg_eacl_20260627
```

```bash
python3 scripts/import_cape_mapping_review.py \
  --experiment-dir experiments/cape_kg_eacl_20260627 \
  --reviewed-file experiments/cape_kg_eacl_20260627/01_data/mapping_review/mapping_review_items.reviewed.jsonl
```

위 개별 import 명령은 mapping reviewed file 문제를 디버깅할 때만 사용한다. 운영 반영은 전체 반환 파일 preflight 후 아래 wrapper를 기본 경로로 사용한다.

먼저 dry-run:

```bash
PYTHON_BIN=python3 \
LLM_PYTHON=python3 \
APPLY_IMPORTS=0 \
bash scripts/run_cape_human_return_apply.sh
```

통과하면 실제 반영:

```bash
PYTHON_BIN=python3 \
LLM_PYTHON=python3 \
APPLY_IMPORTS=1 \
bash scripts/run_cape_human_return_apply.sh
```

## 4. NCS-PCF Crosswalk Expert Review

NCS-PCF crosswalk claim은 Layer2 task를 매개로 연결한 NCS 후보와 PCF 후보 pair의 유용성을 사람이 검수해야 논문 주장으로 쓸 수 있다.

내부 handoff bundle:

- Crosswalk expert: `06_release/human_review_handoff/cape_crosswalk_expert_review_ncs_pcf.tar.gz`
- Handoff README: `06_release/human_review_handoff/README_crosswalk_expert_ko.md`

시작 파일:

- protocol: `01_data/crosswalk_review/crosswalk_review_protocol.md`
- 전체 row: `01_data/crosswalk_review/crosswalk_review_items.jsonl`
- CSV sheet: `01_data/crosswalk_review/crosswalk_review_sheet.csv`
- 후보 report: `04_evaluation/ncs_pcf_crosswalk_report.md`
- 후보 CSV: `04_evaluation/ncs_pcf_crosswalk_candidates.csv`

검수 단위:

- 각 row는 하나의 Layer2 업무를 공유하는 NCS 후보와 PCF 후보의 pair다.
- `expert_decision`은 `accepted`, `rejected`, `unsure` 중 하나를 사용한다.
- `utility_grade`는 0, 1, 2, 3 중 하나를 사용한다.
- `explanation_quality_score`는 1, 2, 3, 4, 5 중 하나를 사용한다.

완료 파일은 반드시 아래 이름으로 저장한다.

```text
experiments/cape_kg_eacl_20260627/01_data/crosswalk_review/crosswalk_review_items.reviewed.jsonl
```

전체 반환 파일 상태는 human-gold/mapping과 동일한 preflight 명령으로 확인한다.

```bash
python3 scripts/validate_cape_human_review_returns.py \
  --experiment-dir experiments/cape_kg_eacl_20260627
```

개별 import 명령은 crosswalk reviewed file 문제를 디버깅할 때만 사용한다.

```bash
python3 scripts/import_cape_crosswalk_review.py \
  --experiment-dir experiments/cape_kg_eacl_20260627 \
  --reviewed-file experiments/cape_kg_eacl_20260627/01_data/crosswalk_review/crosswalk_review_items.reviewed.jsonl
```

운영 반영은 전체 반환 파일 preflight 후 wrapper로 dry-run을 먼저 실행한다.

```bash
PYTHON_BIN=python3 \
LLM_PYTHON=python3 \
APPLY_IMPORTS=0 \
bash scripts/run_cape_human_return_apply.sh
```

통과하면 실제 반영한다.

```bash
PYTHON_BIN=python3 \
LLM_PYTHON=python3 \
APPLY_IMPORTS=1 \
bash scripts/run_cape_human_return_apply.sh
```

## 5. Active Review Human-Effort

active-review efficiency claim은 reviewer가 실제로 얼마나 빨리/정확하게 오류를 찾는지 측정해야 하므로 별도 timing CSV가 필요하다.

내부 handoff bundle:

- Active-review effort: `06_release/human_review_handoff/cape_active_review_human_effort.tar.gz`
- Handoff README: `06_release/human_review_handoff/README_active_review_effort_ko.md`

시작 파일:

- plan: `06_release/active_review_human_effort_plan.md`
- template CSV: `05_review/active_review_human_effort_template.csv`
- expected reviewed CSV: `05_review/active_review_human_effort.reviewed.csv`
- active-review queue: `05_review/actual_llm_active_review_queue_P_cape_kg_actual.csv`

검수자가 채워야 하는 핵심 열:

- `reviewer_id`
- `review_seconds`
- `decision`
- `corrected_error`
- `high_impact_correction`

완료 파일은 반드시 아래 이름으로 저장한다.

```text
experiments/cape_kg_eacl_20260627/05_review/active_review_human_effort.reviewed.csv
```

전체 반환 파일 상태는 human-gold/mapping과 동일한 preflight 명령으로 확인한다.

```bash
python3 scripts/validate_cape_human_review_returns.py \
  --experiment-dir experiments/cape_kg_eacl_20260627
```

검증 후 전체 metrics를 갱신할 때는 동일한 wrapper를 사용한다. 먼저 dry-run을 실행한다.

```bash
PYTHON_BIN=python3 \
LLM_PYTHON=python3 \
APPLY_IMPORTS=0 \
bash scripts/run_cape_human_return_apply.sh
```

통과하면 실제 반영한다.

```bash
PYTHON_BIN=python3 \
LLM_PYTHON=python3 \
APPLY_IMPORTS=1 \
bash scripts/run_cape_human_return_apply.sh
```

주의: active-review timing 결과만으로는 최종 논문 주장이 되지 않는다. reviewer effort/timing과 adjudicated human-gold outcome alignment가 모두 있어야 active-review efficiency claim으로 사용할 수 있다.

## 6. Gate 확인

사람 검수 import 후 항상 아래 파일을 확인한다.

- `06_release/claim_gate_report.md`
- `06_release/pre_human_handoff_validation.md`
- `06_release/submission_completion_audit_ko.md`
- `06_release/submission_readiness_audit.md`
- `06_release/paper_tables.md`
- `06_release/human_review_status_dashboard_ko.md`
- `06_release/latest_release_bundle_index.md`
- `07_reports/final_eacl_experiment_report.md`

minimum accept gate는 human-gold 100 chunk, 500 item, IAA, proposed-vs-gold score가 모두 채워질 때까지 계속 FAIL로 남는 것이 정상이다.

최신 bundle 무결성 확인:

```bash
sha256sum -c experiments/cape_kg_eacl_20260627/06_release/release_bundle_checksums.sha256
sha256sum -c experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/human_review_handoff_checksums.sha256
python3 scripts/validate_cape_pre_human_handoff.py \
  --experiment-dir experiments/cape_kg_eacl_20260627 \
  --outputs-dir outputs
```
