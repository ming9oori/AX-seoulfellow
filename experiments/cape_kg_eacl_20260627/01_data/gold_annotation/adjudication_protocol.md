# CAPE-KG Gold Annotation and Adjudication Protocol

Generated: 2026-06-28

이 문서는 두 명의 독립 annotator가 만든 CAPE-KG annotation을 IAA 계산과 최종 adjudicated gold로 연결하기 위한 운영 프로토콜이다. 최종 논문 성능표는 silver candidate나 annotator 단독 파일이 아니라 **adjudicated gold file**에 대해서만 산출한다.

---

## 1. 역할

| 역할 | 책임 |
| --- | --- |
| Annotator A | priority chunk를 독립적으로 검수하고 `.reviewed.jsonl` 반환 |
| Annotator B | 같은 chunk를 독립적으로 검수하고 `.reviewed.jsonl` 반환 |
| Coordinator | 반환 파일 preflight, import, IAA 계산, draft 생성 |
| Adjudicator | A/B disagreement를 해결하고 final gold 확정 |

분리 원칙:

- Annotator A와 B는 서로의 결정을 보지 않고 독립 검수한다.
- Coordinator는 자동 import와 검증을 담당하며, gold 판단을 임의로 바꾸지 않는다.
- Adjudicator는 chunk text와 A/B 판단을 함께 보고 최종 결정을 내린다.

---

## 2. Annotation 단위와 권위 자료

Annotation 단위는 `chunk_id` 하나다.

권위 자료 우선순위:

1. `chunk_text`
2. chunk 내부 evidence anchor/sentence
3. A/B annotator의 comments
4. silver candidate metadata

주의:

- silver candidate는 gold가 아니라 검토 대상이다.
- 외부 도메인 지식이나 다른 chapter의 기억으로 edge를 accept하면 안 된다.
- adjudication도 chunk text가 직접 지지하는 범위 안에서만 수행한다.
- `component_evidence_spans`는 source/predicate/target 근거 위치를 찾기 위한 자동 제안이며 gold 판정이 아니다.
- `component_evidence_spans.exact=true`는 해당 label 문자열이 evidence sentence 안에서 발견되었다는 뜻일 뿐, predicate 관계가 gold라는 뜻은 아니다.
- `method=full_sentence_proxy`나 `label_not_found_in_sentence`가 있는 candidate는 sentence와 chunk text를 더 보수적으로 확인한다.

---

## 3. Annotator가 완료해야 하는 항목

각 chunk마다 annotator는 다음을 완료해야 한다.

- candidate edge accept/reject 판단
- unsupported candidate의 `reference_id` reject 기록
- missing but supported node/edge 추가
- accepted edge의 evidence anchor 또는 evidence span 기입
- 애매한 쟁점은 `comments`에 기록
- 완료된 경우 `annotation_status=completed`
- 불확실한 경우 `annotation_status=needs_adjudication`

`completed`는 “모든 후보를 검토했고, gold로 남긴 항목은 evidence가 있다”는 의미다. 일부만 본 chunk에는 사용하지 않는다.

---

## 4. 반환 파일 preflight

Annotator가 `.reviewed.jsonl`을 반환하면 Coordinator는 import 전에 preflight를 실행한다.

```bash
/home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python scripts/validate_cape_human_review_returns.py \
  --experiment-dir experiments/cape_kg_eacl_20260627
```

확인 파일:

- `experiments/cape_kg_eacl_20260627/06_release/human_review_return_preflight.md`
- `experiments/cape_kg_eacl_20260627/06_release/human_review_return_preflight.json`

preflight에서 확인해야 할 점:

- expected reviewed file 10개가 모두 존재하는가?
- 각 file의 chunk 수가 batch expected rows와 맞는가?
- `chunk_id`와 immutable field가 변경되지 않았는가?
- accepted edge에 evidence가 있는가?
- status value가 허용된 값인가?
- A/B가 같은 chunk set을 다루고 있는가?

preflight error가 있으면 import하지 않고 annotator에게 반환한다.

---

## 5. Import 절차

권장 절차는 개별 batch import가 아니라 전체 반환 파일 wrapper를 이용하는 것이다. wrapper는 human return preflight, annotator import, adjudication import, mapping review import, IAA, gold evaluation, claim gate, release/handoff bundle 갱신을 한 번에 실행한다.

먼저 dry run으로 누락 파일과 schema error를 확인한다.

```bash
PYTHON_BIN=/home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python \
LLM_PYTHON=/home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python \
APPLY_IMPORTS=0 \
bash scripts/run_cape_human_return_apply.sh
```

dry run이 통과하고 expected return files가 모두 준비되어 있으면 실제 import를 적용한다.

```bash
PYTHON_BIN=/home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python \
LLM_PYTHON=/home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python \
APPLY_IMPORTS=1 \
bash scripts/run_cape_human_return_apply.sh
```

wrapper 실행 후 반드시 다음 파일을 확인한다.

- `experiments/cape_kg_eacl_20260627/06_release/human_return_apply_last_run.md`
- `experiments/cape_kg_eacl_20260627/06_release/human_review_return_preflight.md`
- `experiments/cape_kg_eacl_20260627/06_release/claim_gate_report.md`
- `experiments/cape_kg_eacl_20260627/06_release/claimable_main_table.md`

개별 import 명령은 특정 batch의 문제를 디버깅할 때만 사용한다. 예시는 다음과 같다.

```bash
python3 scripts/import_cape_gold_annotation.py \
  --experiment-dir experiments/cape_kg_eacl_20260627 \
  --target-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/annotator_A.jsonl \
  --reviewed-file experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_A_full_120_priority_batch_001.reviewed.jsonl \
  --allow-partial
```

---

## 6. IAA 계산

A/B import 후 IAA를 계산한다.

```bash
python3 scripts/compute_cape_annotation_iaa.py \
  --annotator-a experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/annotator_A.jsonl \
  --annotator-b experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/annotator_B.jsonl \
  --output-dir experiments/cape_kg_eacl_20260627/01_data/gold_annotation/iaa_full_120
```

확인 파일:

- `iaa_full_120/iaa_summary.json`
- `iaa_full_120/iaa_report.md`
- `iaa_full_120/disagreement_chunks.json`

IAA에서 봐야 할 핵심:

- paired completed chunks >= 100
- node exact agreement
- edge exact agreement
- candidate acceptance kappa
- evidence overlap/Jaccard
- disagreement chunk 목록

IAA는 최종 성능이 아니라 annotation reliability evidence다.

---

## 7. Adjudication draft 생성

IAA 후 adjudication draft를 생성한다.

```bash
python3 scripts/prepare_cape_adjudication_draft.py \
  --experiment-dir experiments/cape_kg_eacl_20260627 \
  --package full_120
```

확인 파일:

- `full_120/adjudication_draft.jsonl`
- `full_120/adjudication_draft_summary.json`
- `full_120/adjudication_draft_report.md`

Draft status 해석:

| Status | 의미 |
| --- | --- |
| `no_disagreement_adjudicated` | A/B가 일치해 자동 draft 가능 |
| `needs_adjudication` | A/B 불일치 또는 annotator uncertainty |
| `pending_two_annotator_input` | A/B 중 하나 이상 미완료 |

---

## 8. Adjudicator 판정 기준

Adjudicator는 다음 순서로 결정한다.

1. chunk text를 먼저 읽는다.
2. A/B accepted edges와 rejected candidate를 비교한다.
3. A/B가 모두 accept했고 evidence가 직접 지지하면 final gold로 둔다.
4. 한 명만 accept한 edge는 chunk text가 직접 지지하는지 재판정한다.
5. A/B가 모두 reject했지만 명확히 missing인 edge가 있으면 추가할 수 있다.
6. evidence가 약하거나 관계가 추론적인 edge는 final gold에서 제외한다.
7. 최종 gold edge에는 evidence anchor/span을 반드시 남긴다.

Adjudication에서 reject해야 하는 대표 사례:

- 관계가 chunk 밖 배경지식에 의존한다.
- source/target은 보이지만 predicate가 직접 지지되지 않는다.
- direction이 잘못되었다.
- role/artifact/task type이 잘못되었다.
- evidence가 너무 넓어 관계를 특정할 수 없다.

Adjudicator는 불확실한 결정을 줄이고, conservative gold를 만든다. 논문 main table은 이 conservative gold와 비교하는 것이 안전하다.

---

## 9. Final adjudication import와 validation

Adjudicator가 `adjudication_edited.jsonl`을 export하면 section 5의 wrapper dry run을 먼저 수행한다.

```bash
PYTHON_BIN=/home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python \
LLM_PYTHON=/home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python \
APPLY_IMPORTS=0 \
bash scripts/run_cape_human_return_apply.sh
```

통과하면 `APPLY_IMPORTS=1`로 import, gold validation, scoring, claim gate 갱신을 함께 실행한다.

```bash
PYTHON_BIN=/home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python \
LLM_PYTHON=/home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python \
APPLY_IMPORTS=1 \
bash scripts/run_cape_human_return_apply.sh
```

개별 adjudication import는 특정 파일 문제를 디버깅할 때만 사용한다.

```bash
python3 scripts/import_cape_gold_annotation.py \
  --experiment-dir experiments/cape_kg_eacl_20260627 \
  --target-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/adjudication.jsonl \
  --reviewed-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/adjudication_edited.jsonl
```

확인 파일:

- `04_evaluation/human_gold_validation_summary.json`
- `04_evaluation/human_gold_validation_report.md`
- `04_evaluation/human_gold_metrics.json`
- `04_evaluation/human_gold_evaluation_report.md`
- `06_release/claim_gate_report.md`
- `06_release/paper_tables.md`
- `06_release/claimable_main_table.md`

---

## 10. Minimum paper gate

다음 조건이 모두 충족되어야 EACL paper main result로 사용할 수 있다.

| Gate | Minimum |
| --- | ---: |
| Adjudicated chunks | 100 |
| Gold node/edge/evidence items | 500 |
| Paired IAA chunks | 100 |
| Validation errors | 0 |
| Proposed condition scored | `P_cape_kg_actual` |

이 조건이 충족되기 전에는 claim gate가 FAIL인 것이 정상이다.

---

## 11. Adjudication checklist

최종 import 전 확인한다.

- [ ] A/B reviewed files 10개가 모두 import되었다.
- [ ] paired completed chunks가 100 이상이다.
- [ ] IAA report가 생성되었다.
- [ ] disagreement chunks를 모두 확인했다.
- [ ] final adjudication file에 pending chunk가 남아 있지 않다.
- [ ] final gold edges는 모두 evidence를 가진다.
- [ ] validation error가 0이다.
- [ ] human-gold metrics가 생성되었다.
- [ ] claim gate를 재실행했다.
