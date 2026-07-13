# CAPE-KG Optional Structural Review Handoff

이 bundle은 KG structural diagnostics에서 나온 ReviewCheckpoint 후보와 DecisionGateway branch gap을 선택적으로 검수하기 위한 내부 자료다.

## 열 파일

- Action plan: `experiments/cape_kg_eacl_20260627/06_release/structural_review_action_plan.md`
- Return preflight: `experiments/cape_kg_eacl_20260627/06_release/structural_review_return_preflight.md`
- Dry-run application plan: `experiments/cape_kg_eacl_20260627/06_release/structural_review_application_plan.md`
- ReviewCheckpoint candidates: `experiments/cape_kg_eacl_20260627/05_review/structural_review_checkpoint_candidates.csv`
- Gateway branch gaps: `experiments/cape_kg_eacl_20260627/05_review/structural_gateway_branch_gaps.csv`
- Dry-run application actions: `experiments/cape_kg_eacl_20260627/05_review/structural_review_application_actions.csv`
- Optional return list: `experiments/cape_kg_eacl_20260627/05_review/structural_review_optional_returns.csv`
- Validation error playbook: `experiments/cape_kg_eacl_20260627/06_release/human_return_validation_error_playbook_ko.md`
- Master checklist: `experiments/cape_kg_eacl_20260627/06_release/human_review_master_checklist_ko.md`
- Status dashboard: `experiments/cape_kg_eacl_20260627/06_release/human_review_status_dashboard_ko.md`
- Launch checklist: `experiments/cape_kg_eacl_20260627/06_release/human_review_launch_checklist_ko.md`

## 저장할 파일

- ReviewCheckpoint reviewed CSV: `experiments/cape_kg_eacl_20260627/05_review/structural_review_checkpoint_candidates.reviewed.csv`
- Gateway branch reviewed CSV: `experiments/cape_kg_eacl_20260627/05_review/structural_gateway_branch_gaps.reviewed.csv`

## Review 규칙

- ReviewCheckpoint 후보는 실제 검토/승인/품질관문 활동일 때만 `accept_review_checkpoint`로 표시한다.
- 단순히 "리뷰"라는 단어가 들어간 일반 업무는 `keep_current_type` 또는 `reject_candidate`로 표시한다.
- Gateway branch gap은 원문 근거가 명시적인 분기 결과를 지지할 때만 `add_branches_to`로 표시한다.
- 애매한 row는 `needs_discussion`으로 남긴다.
- reviewed CSV가 돌아오기 전에는 KG를 자동 수정하지 않는다.

## Preflight

```bash
python3 scripts/validate_cape_structural_review_returns.py \
  --experiment-dir experiments/cape_kg_eacl_20260627
```

## Dry-run Application Plan

```bash
python3 scripts/build_cape_structural_review_application_plan.py \
  --experiment-dir experiments/cape_kg_eacl_20260627
```

이 계획서는 reviewed CSV의 `human_decision`을 manual KG update 제안으로 변환하지만, KG를 자동 수정하지 않는다.

이 structural review는 minimum paper-gate의 annotation/adjudication 반환 파일을 대체하지 않는다. 논문 최종 성능 claim에는 human-gold annotation, IAA, adjudication, proposed human-gold scoring이 별도로 필요하다.
