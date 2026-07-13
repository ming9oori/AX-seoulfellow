# CAPE-KG Human Return Validation Error Playbook

Generated: `2026-06-29T18:55:22.906687+00:00`
Claim status: `human_return_error_playbook_ready_pending_human_returns`

이 문서는 human-return 파일을 받은 뒤 preflight/import validator가 내는 대표 error/warning을 coordinator가 빠르게 해석하고 고치기 위한 내부 운영 가이드다. 이 문서 자체는 not human-gold evidence이며, 검수 결과를 대체하지 않는다.

## When To Use

1. 반환 파일을 받은 직후 아래 preflight를 실행한다.
2. `error_count`가 1 이상이면 이 playbook에서 error code 또는 message pattern을 찾는다.
3. 파일을 수정한 뒤 preflight를 다시 실행한다.

```bash
python3 scripts/validate_cape_human_review_returns.py \
  --experiment-dir experiments/cape_kg_eacl_20260627
```

Optional structural review:

```bash
python3 scripts/validate_cape_structural_review_returns.py \
  --experiment-dir experiments/cape_kg_eacl_20260627
```

## First Triage Rule

- `missing_reviewed_file`은 아직 파일이 돌아오지 않았다는 뜻이며, 현재 pre-human 단계에서는 정상적인 pending 상태다.
- `failed_validation`은 반환 파일이 존재하지만 schema/key/decision/coverage 규칙을 만족하지 않는 상태다. 이 경우 apply하지 않는다.
- `warning`은 대부분 claim을 약화시키거나 재확인을 요구하지만, `error`가 없으면 import는 가능할 수 있다. 단, final claim 전에는 warning도 검토한다.

## Quick Fix Table

### active_review_effort

| Error code or pattern | Severity | Common cause | Recommended fix |
| --- | --- | --- | --- |
| `missing_required_fields` | error | active_review_human_effort.reviewed.csv에 필수 컬럼이 없음. | 필수 컬럼을 모두 포함한다: chunk_id, condition, corrected_error, decision, high_impact_correction, included_in_active, included_in_random, included_in_uncertainty, review_item_id, review_seconds, reviewer_id. |
| `duplicate_review_item_ids / extra_review_item_ids` | error | review_item_id가 중복되거나 template에 없는 id가 들어감. | template row set으로 되돌리고 중복/extra row를 제거한다. |
| `missing_template_rows` | warning | template에는 있으나 reviewed CSV에는 없는 row가 있음. | claim을 위해서는 모든 template row를 포함한다. |
| `invalid_boolean_value` | error | boolean field에 허용되지 않는 값이 있음. | 값을 , 0, 1, false, n, no, true, y, yes 중 하나로 수정한다. |
| `invalid_decision` | error | decision 값이 허용 범위를 벗어남. | 값을 , correct, incorrect, invalid, partial, unsupported, unsure 중 하나로 수정한다. |
| `negative_review_seconds` | error | review_seconds가 음수임. | 0보다 큰 실제 검토 시간을 초 단위로 입력한다. |
| `reviewed_row_missing_reviewer_id / reviewed_row_missing_decision` | error | 검수된 row에 reviewer_id 또는 decision이 없음. | reviewer_id와 decision을 모두 채운다. |
| `reviewed_row_missing_positive_review_seconds` | error | 검수된 row에 양수 review_seconds가 없음. | 실제 소요 시간을 초 단위 양수로 입력한다. |
| `reviewed_row_missing_corrected_error / reviewed_row_missing_high_impact_correction` | error | 검수된 row에 correction flag가 비어 있음. | corrected_error와 high_impact_correction을 true/false 또는 1/0로 채운다. |
| `correction_decision_without_corrected_error` | error | decision이 incorrect, invalid, partial, unsupported인데 corrected_error가 false/blank임. | corrected_error=true로 바꾸거나 decision을 correct로 수정한다. |
| `correct_decision_with_corrected_error / high_impact_without_corrected_error` | error | decision/impact flag가 서로 모순됨. | correct면 corrected_error=false, high_impact=true면 corrected_error=true가 되게 맞춘다. |
| `active_review_effort_not_complete_for_claim` | warning | 일부 row 또는 timing이 빠져 active-review claim이 아직 불완전함. | 모든 template row를 검수하고 positive review_seconds를 채운다. |

### adjudication

| Error code or pattern | Severity | Common cause | Recommended fix |
| --- | --- | --- | --- |
| `invalid_adjudication_status` | error | adjudication_status가 허용값이 아님. | 값을 accepted, adjudicated, complete, completed, final, in_progress, needs_adjudication, no_disagreement_adjudicated, pending_two_annotator_input 중 하나로 수정한다. |
| `adjudicated_gold_nodes_not_list / adjudicated_gold_edges_not_list` | error | adjudicated_gold_nodes 또는 adjudicated_gold_edges가 list가 아님. | [] 또는 최종 gold item object list로 수정한다. |
| `extra_chunks_not_in_draft` | error | adjudication_edited.jsonl에 draft에 없는 chunk가 포함됨. | draft에 있는 chunk row만 남긴다. |
| `completed_adjudication_missing_adjudicator_id` | error | 완료 adjudication row에 adjudicator_id가 없음. | adjudicator_id를 채운다. |
| `completed_adjudication_without_gold_items` | warning | 완료 adjudication row에 gold node/edge가 하나도 없음. | 정말 해당 chunk에 gold item이 없는지 확인하고 comments/adjudication_notes로 이유를 남긴다. |

### annotation

| Error code or pattern | Severity | Common cause | Recommended fix |
| --- | --- | --- | --- |
| `invalid_annotation_status` | error | annotation_status가 허용값이 아니거나 대소문자/공백이 섞임. | 값을 completed, in_progress, needs_adjudication, pending_human_annotation 중 하나로 수정한다. |
| `gold_nodes_not_list` | error | gold_nodes가 JSON array가 아니라 object/string/null로 저장됨. | gold_nodes를 [] 또는 node object list로 바꾼다. |
| `gold_edges_not_list` | error | gold_edges가 JSON array가 아니라 object/string/null로 저장됨. | gold_edges를 [] 또는 edge object list로 바꾼다. |
| `rejected_refs_not_list` | error | rejected_candidate_reference_ids가 list가 아님. | reject한 reference_id 문자열 list로 수정한다. |
| `unknown_rejected_candidate_ref` | warning | rejected_candidate_reference_ids에 해당 row의 candidate reference_id가 아닌 값이 들어감. | 해당 chunk의 silver_candidate_edges[].reference_id를 확인해 정확한 값으로 바꾼다. |
| `duplicate_reviewed_chunk` | error | reviewed JSONL 안에 같은 chunk_id가 두 번 이상 있음. | 중복 row를 제거하고 하나의 최종 row만 남긴다. |
| `missing_chunk_id` | error | reviewed row에서 chunk_id가 비어 있거나 삭제됨. | 원본 input JSONL의 chunk_id를 그대로 복원한다. |
| `unknown_chunk_id` | error | reviewed file에 target/input에 없는 chunk_id가 있음. | 해당 row를 제거하거나 올바른 batch input 파일에서 다시 작성한다. |
| `mode_mismatch` | error | annotation row와 adjudication row 형식이 섞임. | annotation reviewed file에는 annotation_status/gold_* 형식만, adjudication file에는 adjudication_status/adjudicated_* 형식만 둔다. |
| `immutable_field_changed` | error | chunk_id, chunk_text, package 등 원본 provenance 필드가 바뀜. | 원본 input JSONL의 해당 필드를 그대로 복원한다. |
| `missing_reviewed_chunks / missing_batch_chunks` | error | reviewed file에서 배정된 chunk row 일부가 빠짐. | input batch의 모든 row를 유지하고, 검수하지 않은 row는 pending/in_progress로 남긴다. |
| `extra_chunks_not_in_batch` | error | reviewed file에 해당 batch에 없는 chunk가 섞임. | 다른 batch row를 제거하고 해당 batch input row만 남긴다. |
| `annotator_id_mismatch` | error | A 파일에 annotator_id=B가 들어가거나 반대 상황. | 파일명에 맞춰 annotator_id를 A 또는 B로 수정한다. |
| `completed_annotation_missing_annotator_id` | error | completed 또는 needs_adjudication row에 annotator_id가 없음. | annotator_id를 파일 역할에 맞게 채운다. |
| `completed_chunk_has_unreviewed_candidate_edges` | error | completed row에서 일부 silver candidate edge가 accept/reject 어느 쪽에도 기록되지 않음. | 각 candidate를 gold_edges[]에 accept하거나 rejected_candidate_reference_ids[]에 reject로 넣는다. |
| `completed_chunk_without_accept_or_reject_actions` | error | candidate가 있는데 gold_edges와 rejected_candidate_reference_ids가 모두 비어 있음. | 모든 candidate를 검토해 accept/reject를 기록한다. |
| `needs_adjudication_missing_comments` | error | needs_adjudication으로 표시했지만 comments가 비어 있음. | 애매한 이유를 comments에 구체적으로 쓴다. |

### crosswalk

| Error code or pattern | Severity | Common cause | Recommended fix |
| --- | --- | --- | --- |
| `reviewed row has no matching original key` | error | reviewed file에 원본 후보 pool에 없는 key 조합이 있음. | 원본 review JSONL/CSV에서 시작해 editable field만 채운다. |
| `changed immutable field` | error | source/target label, rank, score, support field 등 immutable field가 바뀜. | 원본 후보 파일의 값을 복원한다. |
| `invalid expert_decision` | error | expert_decision이 허용값이 아님. | 값을 , accepted, rejected, unsure 중 하나로 수정한다. |
| `invalid utility_grade` | error | utility_grade 값이 허용 범위를 벗어남. | 값을 , 0, 1, 2, 3 중 하나로 수정한다. |
| `invalid explanation_quality_score` | error | explanation_quality_score가 허용 범위를 벗어남. | 값을 , 1, 2, 3, 4, 5 중 하나로 수정한다. |
| `invalid review_status` | error | review_status가 허용값이 아님. | 값을 adjudicated, completed, final, pending_expert_review, reviewed 중 하나로 수정한다. |
| `completed/reviewed but has empty expert_decision` | error | 완료로 표시했지만 decision이 비어 있음. | accepted/rejected/unsure 중 하나를 채운다. |
| `completed/reviewed but has empty utility_grade` | error | 완료로 표시했지만 grade가 비어 있음. | utility_grade를 0~3 중 하나로 채운다. |
| `completed/reviewed but has empty explanation_quality_score` | error | 완료로 표시했지만 explanation_quality_score가 비어 있음. | 1~5 점수를 채운다. |
| `completed/reviewed but has empty reviewer_id` | error | 완료 row에 reviewer_id가 없음. | reviewer_id를 채운다. |
| `unsure decision with positive grade` | error | unsure인데 grade가 긍정 수준임. | 정말 긍정이면 accepted로 바꾸고, 애매하면 grade를 낮추고 comment를 남긴다. |
| `unsure decision but empty comment` | error | unsure인데 이유가 없음. | comment에 불확실한 이유를 적는다. |
| `accepted decision with low grade / rejected decision with positive grade` | error | decision과 grade가 서로 모순됨. | accepted는 높은 grade, rejected는 낮은 grade로 정합성을 맞춘다. |
| `completed/reviewed without a comment` | warning | 완료 row에 comment가 없음. | 가능하면 판단 근거를 comment에 짧게 적는다. |

### mapping

| Error code or pattern | Severity | Common cause | Recommended fix |
| --- | --- | --- | --- |
| `reviewed row has no matching original key` | error | reviewed file에 원본 후보 pool에 없는 key 조합이 있음. | 원본 review JSONL/CSV에서 시작해 editable field만 채운다. |
| `changed immutable field` | error | source/target label, rank, score, support field 등 immutable field가 바뀜. | 원본 후보 파일의 값을 복원한다. |
| `invalid expert_decision` | error | expert_decision이 허용값이 아님. | 값을 , accepted, rejected, unsure 중 하나로 수정한다. |
| `invalid relevance_grade` | error | relevance_grade 값이 허용 범위를 벗어남. | 값을 , 0, 1, 2, 3 중 하나로 수정한다. |
| `invalid explanation_quality_score` | error | explanation_quality_score가 허용 범위를 벗어남. | 값을 , 1, 2, 3, 4, 5 중 하나로 수정한다. |
| `invalid review_status` | error | review_status가 허용값이 아님. | 값을 adjudicated, completed, final, pending_expert_review, reviewed 중 하나로 수정한다. |
| `completed/reviewed but has empty expert_decision` | error | 완료로 표시했지만 decision이 비어 있음. | accepted/rejected/unsure 중 하나를 채운다. |
| `completed/reviewed but has empty relevance_grade` | error | 완료로 표시했지만 grade가 비어 있음. | relevance_grade를 0~3 중 하나로 채운다. |
| `completed/reviewed but has empty explanation_quality_score` | error | 완료로 표시했지만 explanation_quality_score가 비어 있음. | 1~5 점수를 채운다. |
| `completed/reviewed but has empty reviewer_id` | error | 완료 row에 reviewer_id가 없음. | reviewer_id를 채운다. |
| `unsure decision with positive grade` | error | unsure인데 grade가 긍정 수준임. | 정말 긍정이면 accepted로 바꾸고, 애매하면 grade를 낮추고 comment를 남긴다. |
| `unsure decision but empty comment` | error | unsure인데 이유가 없음. | comment에 불확실한 이유를 적는다. |
| `accepted decision with low grade / rejected decision with positive grade` | error | decision과 grade가 서로 모순됨. | accepted는 높은 grade, rejected는 낮은 grade로 정합성을 맞춘다. |
| `completed/reviewed without a comment` | warning | 완료 row에 comment가 없음. | 가능하면 판단 근거를 comment에 짧게 적는다. |

### structural_review

| Error code or pattern | Severity | Common cause | Recommended fix |
| --- | --- | --- | --- |
| `missing_required_fields` | error | reviewed structural CSV에 원본 field 또는 human_decision/human_notes가 없음. | 원본 CSV header를 유지하고 human_decision/human_notes를 포함한다. |
| `row_count_mismatch / missing_input_keys / extra_reviewed_keys` | error | reviewed structural CSV의 row/key set이 원본과 다름. | 원본 row set으로 되돌리고 모든 row에 decision을 채운다. |
| `duplicate_reviewed_keys` | error | node_id 또는 gateway_id가 중복됨. | 중복 row를 제거하고 원본 key당 하나의 row만 유지한다. |
| `missing_human_decision` | error | human_decision이 비어 있음. | 허용 decision 중 하나를 선택한다. |
| `invalid_human_decision` | error | human_decision이 허용값이 아님. | ReviewCheckpoint는 accept_review_checkpoint, keep_current_type, merge_with_existing_review, needs_discussion, reject_candidate; Gateway는 add_branches_to, keep_gateway_without_branch, needs_discussion, reject_gateway, split_gateway 중 하나를 사용한다. |
| `decision_without_notes` | warning | 구조를 바꾸는 decision인데 human_notes가 비어 있음. | 원문 근거 또는 판단 이유를 human_notes에 적는다. |

## Safe Apply Policy

반환 파일을 실제 반영하기 전에는 항상 dry-run wrapper를 먼저 실행한다.

```bash
PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=0 \
bash scripts/run_cape_human_return_apply.sh
```

dry-run과 preflight가 모두 통과한 뒤에만 `APPLY_IMPORTS=1`을 사용한다.

## Claim Boundary

이 playbook은 오류 수정 절차를 표준화하기 위한 문서다. A/B annotation, IAA, adjudication, expert review, active-effort timing, human-gold scoring이 완료되기 전까지는 최종 논문 성능 claim으로 사용할 수 없다.
