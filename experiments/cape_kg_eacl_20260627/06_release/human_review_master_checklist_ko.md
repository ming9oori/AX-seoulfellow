# CAPE-KG 사람 검수 실행 마스터 체크리스트

Generated: 2026-06-29T18:56:34.048454+00:00
Experiment: `experiments/cape_kg_eacl_20260627`

## 1. 현재 결론

현재 자동 KG 구축, LLM baseline/proposed/ablation, public benchmark adapter, release bundle, pre-human validation은 준비되어 있습니다. 그러나 논문 수준의 최종 성능 claim은 아직 하면 안 됩니다. 이유는 human-gold annotation, IAA, adjudication, proposed-method human-gold scoring이 완료되지 않았기 때문입니다.

| 항목 | 현재 값 |
|---|---:|
| Claim gate | `FAIL` |
| Required claim-gate failures | 4 |
| Optional claim-gate failures | 2 |
| Pre-human handoff validation | `PASS` |
| Required return preflight | `pending_human_returns` |
| Optional structural preflight | `pending_optional_returns` |
| Minimum paper-gate human returns | 0/11 |
| Optional/strong claim returns | 0/3 |
| Required claim/human return files | 0/14 |
| Optional structural review files | 0/2 |
| All master return files | 0/16 |
| Optional strong handoff | `True` |
| Optional strong package | `strong_resegmented_342_max18` |
| Optional strong review units | 342 |
| Goal complete | `False` |

## 2. Claim을 막고 있는 항목

| gate | 필수 | status | requirement | evidence |
|---|---:|---|---|---|
| `gold.completed_chunks` | yes | FAIL | Adjudicated human-gold chunks >= 100 | 0 completed chunks, validation_errors=0, file=experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_validation_summary.json |
| `gold.item_count` | yes | FAIL | Human-gold node/edge/evidence items >= 500 | 0 items, validation_errors=0, file=experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_validation_summary.json |
| `gold.iaa` | yes | FAIL | Two-annotator agreement computed for >= 100 chunks | max_completed_pair_chunks=0, summaries=2 |
| `llm.proposed_human_gold_score` | yes | FAIL | CAPE-KG proposed result is scored against adjudicated human gold | human_gold_scored_conditions=[] |
| `mapping.expert_review` | no | FAIL | NCS/PCF mapping downstream metrics are expert-review claimable | complete_source_groups=0, pending_rows=220, file=experiments/cape_kg_eacl_20260627/04_evaluation/mapping_expert_metrics.json, progress_file=experiments/cape_kg_eacl_20260627/06_release/mapping_review_progress_summary.json, progress_pending_groups=44 |
| `crosswalk.expert_review` | no | FAIL | Layer2-bridged NCS-PCF crosswalk metrics are expert-review claimable | completed_rows=0, pending_rows=220, complete_source_groups=0, file=experiments/cape_kg_eacl_20260627/04_evaluation/crosswalk_expert_metrics.json, manifest_file=experiments/cape_kg_eacl_20260627/01_data/crosswalk_review/crosswalk_review_manifest.json, candidate_rows=220 |

## 3. 실행 순서

- 1. Handoff bundle checksum을 먼저 확인한다.
- 2. Annotator A/B가 priority 100 chunk를 독립적으로 검수한다.
- 3. 10개 annotation reviewed JSONL을 정확한 파일명으로 저장한다.
- 4. required return preflight를 실행해 JSONL 형식, row 수, 완료 상태를 확인한다.
- 5. A/B import 후 IAA를 계산하고 adjudication draft를 생성한다.
- 6. Adjudicator가 adjudication_edited.jsonl을 완성한다.
- 7. APPLY_IMPORTS=1 refresh를 실행해 human-gold metrics와 P_cape_kg_actual scoring을 갱신한다.
- 8. Mapping expert가 top20 group review를 완료하면 mapping metrics를 갱신한다.
- 9. Active-review effort CSV를 채우면 active review efficiency claim을 갱신한다.
- 10. 선택 사항으로 structural review 2개 CSV를 검수하되, 명시적 import/update 전에는 KG를 바꾸지 않는다.
- 11. 선택 사항으로 strong 300+ resegmented package를 검수할 수 있다. 단, minimum gate의 annotation/adjudication 반환 파일을 대체하지 않는다.
- 12. Claim gate, pre-human validation, release checksum을 다시 확인한다.

## 4. Required claim/human 반환 파일 14개

아래 14개 파일은 논문 claim과 직접 연결되는 required claim/human 반환 파일입니다. 이 중 `minimum = yes`인 annotation/adjudication 11개 파일이 minimum paper-gate를 여는 필수 반환 파일이고, mapping expert review, NCS-PCF crosswalk expert review, active-review effort 3개는 optional/strong claim을 위한 반환 파일입니다. 선택 structural review 2개까지 포함한 master manifest 전체는 16개입니다. 파일명은 반드시 표의 `reviewed 파일` 경로와 동일해야 합니다.

| 구분 | minimum | 작업 | 담당 | 묶음 | 예상 rows | 현재 | reviewed 파일 |
|---|---|---|---|---|---:|---|---|
| required | yes | human_gold_annotation | annotator_A | full_120_priority_batch_001 | 20 | no / missing_reviewed_file | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_A_full_120_priority_batch_001.reviewed.jsonl` |
| required | yes | human_gold_annotation | annotator_B | full_120_priority_batch_001 | 20 | no / missing_reviewed_file | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_B_full_120_priority_batch_001.reviewed.jsonl` |
| required | yes | human_gold_annotation | annotator_A | full_120_priority_batch_002 | 20 | no / missing_reviewed_file | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_002/annotator_A_full_120_priority_batch_002.reviewed.jsonl` |
| required | yes | human_gold_annotation | annotator_B | full_120_priority_batch_002 | 20 | no / missing_reviewed_file | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_002/annotator_B_full_120_priority_batch_002.reviewed.jsonl` |
| required | yes | human_gold_annotation | annotator_A | full_120_priority_batch_003 | 20 | no / missing_reviewed_file | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_003/annotator_A_full_120_priority_batch_003.reviewed.jsonl` |
| required | yes | human_gold_annotation | annotator_B | full_120_priority_batch_003 | 20 | no / missing_reviewed_file | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_003/annotator_B_full_120_priority_batch_003.reviewed.jsonl` |
| required | yes | human_gold_annotation | annotator_A | full_120_priority_batch_004 | 20 | no / missing_reviewed_file | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_004/annotator_A_full_120_priority_batch_004.reviewed.jsonl` |
| required | yes | human_gold_annotation | annotator_B | full_120_priority_batch_004 | 20 | no / missing_reviewed_file | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_004/annotator_B_full_120_priority_batch_004.reviewed.jsonl` |
| required | yes | human_gold_annotation | annotator_A | full_120_priority_batch_005 | 20 | no / missing_reviewed_file | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/annotator_A_full_120_priority_batch_005.reviewed.jsonl` |
| required | yes | human_gold_annotation | annotator_B | full_120_priority_batch_005 | 20 | no / missing_reviewed_file | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/annotator_B_full_120_priority_batch_005.reviewed.jsonl` |
| required | yes | human_gold_adjudication | adjudicator | full_120_adjudication | 120 | no / missing_reviewed_file | `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/adjudication_edited.jsonl` |
| required | no | mapping_expert_review | mapping_expert | top20_groups_top5_rows | 100 | no / missing_reviewed_file | `experiments/cape_kg_eacl_20260627/01_data/mapping_review/mapping_review_items.reviewed.jsonl` |
| required | no | crosswalk_expert_review | crosswalk_expert | ncs_pcf_crosswalk_candidates | 220 | no / missing_reviewed_file | `experiments/cape_kg_eacl_20260627/01_data/crosswalk_review/crosswalk_review_items.reviewed.jsonl` |
| required | no | active_review_human_effort | active_reviewer | pooled_active_uncertainty_random | 204 | no / missing_reviewed_file | `experiments/cape_kg_eacl_20260627/05_review/active_review_human_effort.reviewed.csv` |

## 5. 선택 구조 검수 파일 2개

아래 2개 파일은 구조 진단 후속 정제를 위한 선택 검수입니다. minimum paper-gate의 annotation/adjudication 반환 파일을 대체하지 않으며, reviewed 파일이 돌아오기 전에는 KG를 자동 수정하지 않습니다.

| 구분 | minimum | 작업 | 담당 | 묶음 | 예상 rows | 현재 | reviewed 파일 |
|---|---|---|---|---|---:|---|---|
| optional_structural | no | structural_review_checkpoint_candidates | structural_reviewer | structural_gap_worklist | 45 | no / ready_for_optional_review | `experiments/cape_kg_eacl_20260627/05_review/structural_review_checkpoint_candidates.reviewed.csv` |
| optional_structural | no | structural_gateway_branch_gaps | structural_reviewer | structural_gap_worklist | 4 | no / ready_for_optional_review | `experiments/cape_kg_eacl_20260627/05_review/structural_gateway_branch_gaps.reviewed.csv` |

## 6. 선택 Strong 300+ 검수 Bundle

이 bundle은 강한 accept 가능권의 300~500 chunk human-gold 목표를 위한 선택 검수 자료입니다. minimum paper-gate의 annotation/adjudication 반환 파일을 대체하지 않습니다.

- Package: `strong_resegmented_342_max18`
- Review units: 342
- Source chunks represented: 214
- Candidate edges: 2087
- Bundle: `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_human_gold_strong_resegmented_342.tar.gz`
- Annotator A reviewed file: `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/annotator_A_edited.jsonl`
- Annotator B reviewed file: `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/annotator_B_edited.jsonl`
- Adjudication reviewed file: `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/adjudication_edited.jsonl`

## 7. 파일별 의미

| 구분 | 작업 | 왜 필요한가 | 다음 행동 |
|---|---|---|---|
| required | human_gold_annotation | 100 chunk two-annotator gold와 IAA 계산에 필요 | Export edited JSONL with the exact reviewed_file name, then run preflight. |
| required | human_gold_annotation | 100 chunk two-annotator gold와 IAA 계산에 필요 | Export edited JSONL with the exact reviewed_file name, then run preflight. |
| required | human_gold_annotation | 100 chunk two-annotator gold와 IAA 계산에 필요 | Export edited JSONL with the exact reviewed_file name, then run preflight. |
| required | human_gold_annotation | 100 chunk two-annotator gold와 IAA 계산에 필요 | Export edited JSONL with the exact reviewed_file name, then run preflight. |
| required | human_gold_annotation | 100 chunk two-annotator gold와 IAA 계산에 필요 | Export edited JSONL with the exact reviewed_file name, then run preflight. |
| required | human_gold_annotation | 100 chunk two-annotator gold와 IAA 계산에 필요 | Export edited JSONL with the exact reviewed_file name, then run preflight. |
| required | human_gold_annotation | 100 chunk two-annotator gold와 IAA 계산에 필요 | Export edited JSONL with the exact reviewed_file name, then run preflight. |
| required | human_gold_annotation | 100 chunk two-annotator gold와 IAA 계산에 필요 | Export edited JSONL with the exact reviewed_file name, then run preflight. |
| required | human_gold_annotation | 100 chunk two-annotator gold와 IAA 계산에 필요 | Export edited JSONL with the exact reviewed_file name, then run preflight. |
| required | human_gold_annotation | 100 chunk two-annotator gold와 IAA 계산에 필요 | Export edited JSONL with the exact reviewed_file name, then run preflight. |
| required | human_gold_adjudication | 최종 adjudicated human-gold와 proposed human-gold scoring에 필요 | Resolve adjudication_draft rows, save adjudication_edited.jsonl, then run preflight/import. |
| required | mapping_expert_review | NCS/PCF mapping P@K, MRR, nDCG, accept-rate claim에 필요 | Review Top-5 candidates for the 20 priority groups (100 rows), export mapping_review_items.reviewed.jsonl, then run preflight/import. |
| required | crosswalk_expert_review | NCS-PCF crosswalk accept-rate, utility, ranking claim에 필요 | Review NCS-PCF crosswalk candidates, export crosswalk_review_items.reviewed.jsonl, then run preflight/import. |
| required | active_review_human_effort | active review efficiency와 사람 검수 비용 claim에 필요 | Fill reviewer_id, review_seconds, decision, corrected_error, and high_impact_correction in the active-review effort CSV, then run preflight/refresh. |
| optional_structural | structural_review_checkpoint_candidates | ReviewCheckpoint 후보 45개를 구조적으로 정제하기 위한 선택 검수 | Fill human_decision and human_notes, then save with the exact reviewed_file name. |
| optional_structural | structural_gateway_branch_gaps | DecisionGateway branch gap 4개를 검토하기 위한 선택 검수 | Fill human_decision and human_notes; add branch target notes only when source evidence supports the outcome. |

## 8. 실행 명령

Handoff bundle checksum 확인:

```bash
sha256sum -c experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/human_review_handoff_checksums.sha256
```

필수 사람 반환 파일 preflight:

```bash
python3 scripts/validate_cape_human_review_returns.py --experiment-dir experiments/cape_kg_eacl_20260627
```

선택 구조 검수 반환 파일 preflight:

```bash
python3 scripts/validate_cape_structural_review_returns.py --experiment-dir experiments/cape_kg_eacl_20260627
```

권장 dry-run wrapper:

```bash
PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=0 bash scripts/run_cape_human_return_apply.sh
```

권장 apply wrapper:

```bash
PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=1 bash scripts/run_cape_human_return_apply.sh
```

저수준 dry refresh:

```bash
PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=0 bash scripts/run_cape_post_annotation_refresh.sh
```

저수준 apply refresh:

```bash
PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=1 bash scripts/run_cape_post_annotation_refresh.sh
```

최종 검증:

```bash
python3 scripts/validate_cape_pre_human_handoff.py --experiment-dir experiments/cape_kg_eacl_20260627 --outputs-dir outputs
sha256sum -c experiments/cape_kg_eacl_20260627/06_release/release_bundle_checksums.sha256
```

## 9. 발표 및 논문 작성 시 주의 문구

- 말할 수 있음: KG 구축, LLM 실행, baseline/ablation, 구조 진단, handoff 준비는 완료.
- 말할 수 있음: 현재 claim gate 실패는 실험 실패가 아니라 human-gold 미완료를 막는 보수적 안전장치.
- 아직 말하면 안 됨: CAPE-KG가 최종적으로 baseline보다 우수하다는 human-gold 기반 성능 claim.
- 아직 말하면 안 됨: NCS/PCF mapping P@K, MRR, nDCG, expert accept-rate가 확정되었다는 claim.
- 아직 말하면 안 됨: optional strong 342개 검수 단위가 실제 342개 adjudicated gold chunk로 완료되었다는 claim.

## 10. 산출물

- JSON: `experiments/cape_kg_eacl_20260627/06_release/human_review_master_checklist_ko.json`
- Markdown: `experiments/cape_kg_eacl_20260627/06_release/human_review_master_checklist_ko.md`
- CSV: `experiments/cape_kg_eacl_20260627/05_review/human_review_master_return_files.csv`
