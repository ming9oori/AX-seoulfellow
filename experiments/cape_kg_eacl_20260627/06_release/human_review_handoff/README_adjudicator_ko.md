# CAPE-KG Adjudicator Handoff

이 bundle은 annotator A/B 반환 파일을 import한 뒤 생성되는 adjudication draft를 검수하기 위한 내부 adjudicator용 자료다.

## 열 파일

- Adjudication protocol: `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/adjudication_protocol.md`
- Draft JSONL: `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/adjudication_draft.jsonl`
- Draft report: `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/adjudication_draft_report.md`
- Target file: `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/adjudication.jsonl`
- Expected reviewed file: `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/adjudication_edited.jsonl`
- Start-here guide: `experiments/cape_kg_eacl_20260627/06_release/human_review_start_here_ko.md`
- Calibration pack: `experiments/cape_kg_eacl_20260627/06_release/annotation_calibration_pack_ko.md`
- Return field guide: `experiments/cape_kg_eacl_20260627/06_release/annotation_return_field_guide_ko.md`
- Validation error playbook: `experiments/cape_kg_eacl_20260627/06_release/human_return_validation_error_playbook_ko.md`
- Master checklist: `experiments/cape_kg_eacl_20260627/06_release/human_review_master_checklist_ko.md`
- Status dashboard: `experiments/cape_kg_eacl_20260627/06_release/human_review_status_dashboard_ko.md`
- Launch checklist: `experiments/cape_kg_eacl_20260627/06_release/human_review_launch_checklist_ko.md`

## Adjudication 규칙

- A/B가 모두 완료된 chunk만 최종 human-gold claim에 사용할 수 있다.
- `disagreement_items`를 확인하고 `adjudicated_gold_nodes`, `adjudicated_gold_edges`를 최종 gold로 정리한다.
- 완료한 chunk는 `adjudication_status`를 `adjudicated`, `completed`, `final`, 또는 `no_disagreement_adjudicated` 중 하나로 둔다.
- 최소 제출 gate를 열려면 completed/adjudicated chunk가 100개 이상이어야 한다.

## Preflight

```bash
python3 scripts/validate_cape_human_review_returns.py \
  --experiment-dir experiments/cape_kg_eacl_20260627
```

## Apply Flow

preflight에서 validation error가 없으면 안전 wrapper로 dry-run refresh를 먼저 실행한다.

```bash
PYTHON_BIN=python3 \
LLM_PYTHON=python3 \
APPLY_IMPORTS=0 \
bash scripts/run_cape_human_return_apply.sh
```

통과하면 `APPLY_IMPORTS=1`로 실제 반영한다.

```bash
PYTHON_BIN=python3 \
LLM_PYTHON=python3 \
APPLY_IMPORTS=1 \
bash scripts/run_cape_human_return_apply.sh
```

## Low-Level Debug Import

아래 단일 파일 import는 adjudication file 문제를 디버깅할 때만 사용한다.

```bash
python3 scripts/import_cape_gold_annotation.py \
  --experiment-dir experiments/cape_kg_eacl_20260627 \
  --target-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/adjudication.jsonl \
  --reviewed-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/adjudication_edited.jsonl \
  --allow-partial
```
