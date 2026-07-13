# CAPE-KG Optional Strong 300+ Review Handoff

이 bundle은 strong-accept 목표인 300~500 chunk human-gold annotation을 준비하기 위한 선택 검수 자료다.
현재 minimum gate의 annotation/adjudication 반환 파일을 대체하지 않는다. 논문에서 300+ adjudicated chunk로 주장하려면 이 bundle의 A/B 검수, IAA, adjudication, scoring이 실제로 완료되어야 한다.

## Package

- Package: `strong_resegmented_342_max18`
- Package directory: `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18`
- Review units: 342
- Source chunks represented: 214
- Max source sentences per review unit: 18
- Units with silver candidates: 93
- Candidate edges total: 2087
- Strong 300 chunk gap after resegmentation: 0

각 review unit은 `source_chunk_id`와 `split_sentence_ids`를 가진다. 따라서 검수 단위가 재분할되었더라도 원래 Layer2 chunk와 source sentence로 다시 추적할 수 있다.

## Input Files

- Annotator A input: `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/annotator_A.jsonl`
- Annotator B input: `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/annotator_B.jsonl`
- Adjudication template: `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/adjudication.jsonl`
- Tracking sheet: `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/tracking_sheet.csv`
- Strong review preview: `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/strong_review_preview.md`
- Strong review preview summary: `experiments/cape_kg_eacl_20260627/06_release/strong_resegmented_review_preview_summary.md`
- Annotation guideline: `experiments/cape_kg_eacl_20260627/01_data/annotation_guideline_v1.md`
- Annotation schema: `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/annotation_schema.json`
- Adjudication protocol: `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/adjudication_protocol.md`
- Return field guide: `experiments/cape_kg_eacl_20260627/06_release/annotation_return_field_guide_ko.md`
- Validation error playbook: `experiments/cape_kg_eacl_20260627/06_release/human_return_validation_error_playbook_ko.md`
- Expansion report: `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/annotation_expansion_report.md`
- Status dashboard: `experiments/cape_kg_eacl_20260627/06_release/human_review_status_dashboard_ko.md`
- Launch checklist: `experiments/cape_kg_eacl_20260627/06_release/human_review_launch_checklist_ko.md`

## Expected Reviewed Files

- Annotator A reviewed file: `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/annotator_A_edited.jsonl`
- Annotator B reviewed file: `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/annotator_B_edited.jsonl`
- Adjudicator reviewed file: `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/adjudication_edited.jsonl`

## Review Rules

- Annotator A/B는 독립적으로 같은 342개 review unit을 검수한다.
- candidate edge는 원문 split text와 evidence anchor가 지지할 때만 gold edge로 복사한다.
- `strong_review_preview.md`에서 dense candidate unit과 evidence span repair 대상 unit을 먼저 확인한다.
- 빠진 node/edge가 split text에서 직접 지지되면 추가한다.
- 모든 accepted edge에는 evidence anchor 또는 exact span을 남긴다.
- 완료 row의 `annotation_status`는 `completed` 또는 `needs_adjudication`으로 둔다.
- 애매한 경우에는 임의로 확정하지 말고 `comments`나 `missing_but_supported_notes`에 이유를 남긴다.

## Dry-run Import Commands

Before import dry runs, validate the optional strong return package:

```bash
python3 scripts/validate_cape_strong_review_returns.py \
  --experiment-dir experiments/cape_kg_eacl_20260627
```

## Safe Apply Wrapper

운영 반영은 개별 import 명령보다 strong 전용 wrapper를 기본 경로로 사용한다. 먼저 dry-run을 실행한다.

```bash
PYTHON_BIN=python3 \
APPLY_IMPORTS=0 \
bash scripts/run_cape_strong_return_apply.sh
```

preflight와 dry-run이 통과하고 reviewed file이 있으면 실제 반영한다.

```bash
PYTHON_BIN=python3 \
APPLY_IMPORTS=1 \
bash scripts/run_cape_strong_return_apply.sh
```

`APPLY_IMPORTS=1`은 reviewed strong return file이 없으면 기본적으로 거부된다.

Annotator A:

```bash
python3 scripts/import_cape_gold_annotation.py \
  --experiment-dir experiments/cape_kg_eacl_20260627 \
  --target-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/annotator_A.jsonl \
  --reviewed-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/annotator_A_edited.jsonl \
  --report-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/annotator_A_strong_import_report.json \
  --allow-partial
```

Annotator B:

```bash
python3 scripts/import_cape_gold_annotation.py \
  --experiment-dir experiments/cape_kg_eacl_20260627 \
  --target-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/annotator_B.jsonl \
  --reviewed-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/annotator_B_edited.jsonl \
  --report-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/annotator_B_strong_import_report.json \
  --allow-partial
```

Dry run이 통과하면 위 명령에 `--apply`를 붙여 반영한다.

## IAA and Adjudication

```bash
python3 scripts/compute_cape_annotation_iaa.py \
  --annotator-a experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/annotator_A.jsonl \
  --annotator-b experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/annotator_B.jsonl \
  --output-dir experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/iaa_strong_resegmented

python3 scripts/prepare_cape_adjudication_draft.py \
  --experiment-dir experiments/cape_kg_eacl_20260627 \
  --package strong_resegmented_342_max18
```

Adjudicator가 `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/adjudication_draft.jsonl`을 검토한 뒤 `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/adjudication_edited.jsonl`로 저장한다.

Adjudication dry run:

```bash
python3 scripts/import_cape_gold_annotation.py \
  --experiment-dir experiments/cape_kg_eacl_20260627 \
  --target-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/adjudication.jsonl \
  --reviewed-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/adjudication_edited.jsonl \
  --report-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/adjudication_strong_import_report.json \
  --allow-partial
```

통과하면 `--apply`를 붙인다. 이 optional strong package는 현재 post-refresh 자동 import 대상이 아니므로, 수동 검증 후 별도 claim table에 반영해야 한다.
