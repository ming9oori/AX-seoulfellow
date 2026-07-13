# CAPE-KG Human Gold Annotation Guideline v1

Generated: 2026-06-28

이 문서는 CAPE-KG 실험의 human-gold annotation을 위한 상세 지침이다. 목적은 LLM 또는 silver candidate를 그대로 승인하는 것이 아니라, **chunk text에 직접 근거가 있는 절차형 업무 지식만 gold node/edge로 확정**하는 것이다.

현재 상태에서 이 파일은 annotation workflow 보조 자료이며, 사람이 검수하고 IAA/adjudication을 마치기 전까지는 논문용 gold evidence가 아니다.

---

## 1. Annotation 단위

하나의 annotation 단위는 `chunk_id` 하나다.

Annotator는 각 chunk에 대해 다음을 수행한다.

1. `chunk_text`를 읽는다.
2. `silver_candidate_edges`를 하나씩 검토한다.
3. chunk text가 직접 지지하는 candidate만 gold edge로 복사하거나 accept한다.
4. candidate에는 없지만 chunk text가 명확히 지지하는 node/edge가 있으면 추가한다.
5. 모든 accepted edge에 evidence anchor 또는 evidence span을 남긴다.
6. 검토가 끝난 chunk만 `annotation_status`를 `completed`로 바꾼다.
7. 애매한 경우는 `needs_adjudication`으로 남기고 `comments`에 이유를 쓴다.

중요 원칙:

- **chunk text가 유일한 판정 근거**다.
- silver candidate는 제안일 뿐 gold가 아니다.
- 도메인 지식으로 그럴듯하더라도 chunk 안에 근거가 없으면 accept하지 않는다.
- 표준 NCS/PCF mapping은 이 annotation의 주 대상이 아니다. mapping expert review에서 따로 판정한다.

---

## 2. Node type 판정 기준

| Type | 판정 기준 | 예시 표현 |
| --- | --- | --- |
| `DomainTask` | 독립적인 업무 활동 또는 업무 단위 | 제안전략 개발, 킥오프 미팅, 가격 전략 수립 |
| `ProcedureStep` | task 내부의 구체적 단계나 실행 행위 | 요구조건 응답표 작성, 목차 설계 초안 작성 |
| `DecisionGateway` | 다음 진행 여부나 분기 판단 지점 | Bid/No Bid, 최종 입찰 참여 여부 결정 |
| `GuardCondition` | decision이나 branch의 조건/기준 | RFP 확인 후, 가격 승인 후, 고객 요구 충족 시 |
| `Artifact` | 입력/산출 문서, 표, 계획, 리스트, 자료 | 제안서, RFP, PMP, WBS, 섹션기획서 |
| `ArtifactFlow` | artifact가 다음 단계로 전달되는 흐름 자체 | 섹션기획서가 작성자에게 제공됨 |
| `Role` | 수행자, 책임자, 팀, 직무 역할 | 제안 PM, 권별 리더, 섹션 작성자 |
| `ReviewCheckpoint` | 검토/리뷰 활동 또는 품질 점검 지점 | 레드팀 리뷰, 섹션기획서 리뷰 |
| `Principle` | 명시적 원칙, 권고, best practice | 역할은 반드시 정의되어야 한다 |
| `Risk` | 명시적 위험, 실패 요인, 주의사항 | 일정 지연, 고객 니즈 오해 |

판정 팁:

- 한 표현이 업무 단위인지 단계인지 애매하면, chunk에서 독립적으로 반복 수행되는 활동이면 `DomainTask`, 특정 업무의 하위 실행이면 `ProcedureStep`로 둔다.
- “작성자”, “제안 PM”처럼 사람/조직 역할이면 `Role`이다.
- “제안서”, “요구조건 응답표”처럼 만들어지거나 사용되는 문서는 `Artifact`다.
- “결정”, “여부 판단”, “승인”처럼 분기가 생기는 지점은 `DecisionGateway`일 가능성이 높다.

---

## 3. Edge predicate 판정 기준

| Predicate | Source type | Target type | Accept 기준 |
| --- | --- | --- | --- |
| `HAS_STEP` | DomainTask | ProcedureStep | task가 해당 step을 포함한다고 명시됨 |
| `PRECEDES` | DomainTask/ProcedureStep/ReviewCheckpoint | DomainTask/ProcedureStep/ReviewCheckpoint | 순서, 단계 번호, 선후 관계가 명시됨 |
| `USES_INPUT` | DomainTask/ProcedureStep | Artifact | 업무가 해당 자료를 사용/참조/입수한다고 명시됨 |
| `PRODUCES` | DomainTask/ProcedureStep | Artifact | 업무 결과물, 산출물, 작성 대상이 명시됨 |
| `PERFORMED_BY` | DomainTask/ProcedureStep/ReviewCheckpoint | Role | 수행자/책임자가 명시됨 |
| `HAS_DECISION_GATEWAY` | DomainTask/ProcedureStep | DecisionGateway | 업무 안에 결정/판단 지점이 명시됨 |
| `HAS_GUARD_CONDITION` | DecisionGateway/DomainTask/ProcedureStep | GuardCondition | 판단 기준이나 조건이 명시됨 |
| `HAS_PRINCIPLE` | DomainTask/ProcedureStep | Principle | 해당 업무의 원칙/권고가 명시됨 |
| `HAS_RISK` | DomainTask/ProcedureStep | Risk | 해당 업무 관련 위험이 명시됨 |
| `FEEDS_INTO` | Artifact | Artifact/DomainTask/ProcedureStep | 산출물이 후속 업무나 산출물로 전달됨 |
| `USED_AS_INPUT_FOR` | Artifact | DomainTask/ProcedureStep | artifact가 특정 업무의 입력으로 쓰임 |

Reject해야 하는 경우:

- source와 target이 chunk에 없거나, 의미상 너무 멀리 추론해야 한다.
- evidence text가 source나 target 중 하나만 지지하고 관계는 지지하지 않는다.
- predicate 방향이 반대다. 예: RFP가 업무를 사용한다고 되어 있으면 `USES_INPUT` 방향 오류다.
- target type이 predicate domain/range와 맞지 않는다.
- candidate가 전체 교재의 다른 문장 근거만 갖고 있고 현재 chunk text가 직접 지지하지 않는다.

---

## 4. Evidence 판정 기준

모든 accepted edge에는 evidence가 필요하다.

우선순위:

1. Exact span: source, predicate, target 관계를 직접 보여주는 짧은 span
2. Sentence anchor: OCR noise 때문에 exact span이 어렵지만 해당 sentence가 관계를 직접 지지
3. Multiple anchors: 한 문장에 source/target이 나뉘어 있어 두 개 이상의 anchor가 필요한 경우

Evidence가 충분한 경우:

- “활동 결과물(Output) ... 제안관리 계획(PMP)”처럼 활동과 산출물이 같은 문장/표 row에 같이 나온다.
- “제안 PM은 ... 프로세스 관리에 집중”처럼 역할과 수행 업무가 직접 연결된다.
- “단계 7: 최종 RFP 확인 후 최종 입찰 참여 여부 결정”처럼 조건과 decision이 같이 나온다.

Evidence가 불충분한 경우:

- chunk에는 제안서가 나오지만 특정 task가 제안서를 produce한다는 문장은 없다.
- 역할과 산출물이 같은 chunk에 있지만 수행 관계가 명시되지 않았다.
- 일반 배경지식으로는 맞지만 chunk text가 직접 말하지 않는다.

### 자동 component span 제안 사용법

일부 candidate edge에는 `component_evidence_spans`가 포함되어 있다. 이는 자동으로 만든 검토 보조 정보이며 gold label이 아니다.

- `subject`: source label이 primary evidence sentence 안에서 발견된 위치
- `predicate`: 관계 표현 위치를 특정하기 어려운 경우 sentence 전체 proxy
- `object`: target label이 primary evidence sentence 안에서 발견된 위치

Annotator는 이 값을 근거 탐색의 출발점으로만 사용한다. label 위치가 OCR 오류, 번역 alias, 축약 표현 때문에 틀릴 수 있으므로, 최종 accept/reject는 반드시 `chunk_text`와 `primary_evidence.text`를 직접 읽고 결정한다.

`exact=true`이면 해당 label 문자열이 evidence sentence 안에서 발견되었다는 뜻이고, 관계 자체가 gold라는 뜻은 아니다. `method=full_sentence_proxy` 또는 `label_not_found_in_sentence`이면 더 넓은 문맥 확인이 필요하다.

---

## 5. Candidate edge 처리 절차

각 `silver_candidate_edges` row를 다음 순서로 처리한다.

1. `source_label`, `predicate`, `target_label`, `primary_evidence.text`를 확인한다.
2. `component_evidence_spans`가 있으면 source/predicate/target 근거 위치를 빠르게 확인한다.
3. `chunk_text`에서 같은 근거가 실제로 존재하는지 확인한다.
4. source type, target type, predicate가 schema에 맞는지 확인한다.
5. 직접 지지되면 `gold_edges`에 추가한다.
6. 지지되지 않으면 `rejected_candidate_reference_ids`에 candidate의 `reference_id`를 넣는다.
7. 애매하면 reject하거나 `needs_adjudication`으로 두고 `comments`에 이유를 쓴다.

권장 판정 기준:

- Precision을 우선한다. 확신이 낮은 edge를 gold로 넣지 않는다.
- Recall을 위해 누락된 중요한 edge는 추가하되, 반드시 evidence를 붙인다.
- candidate가 많은 chunk에서는 모든 candidate를 자동 accept하지 말고 evidence 단위로 확인한다.

---

## 6. Missing node/edge 추가 기준

candidate에는 없지만 chunk가 명확히 지지하는 중요한 지식은 추가할 수 있다.

추가할 수 있는 경우:

- 표나 단계 목록에 명시된 절차 단계가 빠져 있다.
- 산출물(Output)이 명시되어 있는데 `PRODUCES` edge가 없다.
- 수행자 또는 책임자가 명시되어 있는데 `PERFORMED_BY` edge가 없다.
- decision과 condition이 명시되어 있는데 gateway/guard edge가 없다.

추가하지 말아야 하는 경우:

- 다른 chapter에서 본 지식을 현재 chunk에 보충하는 경우
- 업무상 당연하지만 text에는 없는 경우
- 너무 추상적이어서 node label을 안정적으로 정할 수 없는 경우

Missing item을 추가했다면 `missing_but_supported_notes` 또는 `comments`에 간단히 이유를 적는다.

---

## 7. Label과 ID 작성 규칙

Label:

- 한국어 표면형을 우선 사용한다.
- 원문에 영어 alias가 있으면 보존한다. 예: `제안관리 계획(PMP)`, `Proposal Management Plan`
- OCR 띄어쓰기 오류는 label에서는 읽기 좋게 정리해도 된다.

ID:

- 기존 candidate의 node를 그대로 쓰는 경우 기존 `source_id`/`target_id`를 유지한다.
- 새 node를 추가해야 할 경우 안정적인 prefix를 사용한다.
  - `GOLD_NODE_{chunk_id}_{short_label}`
  - `GOLD_EDGE_{chunk_id}_{serial}`
- ID에는 공백을 넣지 않는다.

주의:

- 같은 chunk 안에서 같은 label/type의 node를 중복 생성하지 않는다.
- 불확실한 canonicalization은 `comments`에 남기고 adjudication에서 해결한다.

---

## 8. Status와 comments

`annotation_status` 값:

| 값 | 사용 시점 |
| --- | --- |
| `pending_human_annotation` | 아직 검수하지 않은 초기 상태 |
| `completed` | candidate 검토, reject 기록, missing edge 추가, evidence 확인이 끝난 상태 |
| `needs_adjudication` | annotator가 판단하기 어려운 쟁점이 있는 상태 |

`completed`로 두면 안 되는 경우:

- candidate edge를 일부만 훑어본 상태
- evidence가 없는 accepted edge가 남아 있는 상태
- source/target type이 불확실한 edge가 남아 있는 상태
- comments에 unresolved question이 있는 상태

`comments`에 남길 내용:

- ambiguous label/type
- evidence가 문장 전체 anchor인지 exact span인지
- candidate를 reject한 대표 이유
- adjudicator가 확인해야 할 쟁점

---

## 9. Quality checklist

각 chunk를 export하기 전에 확인한다.

- [ ] 모든 candidate edge를 검토했다.
- [ ] accept한 edge는 chunk text가 직접 지지한다.
- [ ] accept한 edge마다 evidence anchor 또는 span이 있다.
- [ ] unsupported candidate는 reject list에 넣었다.
- [ ] missing but supported edge를 필요한 만큼 추가했다.
- [ ] node/edge type이 schema와 맞는다.
- [ ] label이 너무 추상적이지 않다.
- [ ] 완료된 chunk만 `completed`로 표시했다.
- [ ] 애매한 chunk는 `needs_adjudication`으로 표시하고 이유를 썼다.

---

## 10. 반환 파일 규칙

Annotator는 batch별로 입력 파일을 수정한 뒤, 같은 batch directory에 `.reviewed.jsonl`로 export한다.

예:

```text
05_review/human_gold_batches/full_120_priority_batch_001/
  annotator_A_full_120_priority_batch_001.reviewed.jsonl
  annotator_B_full_120_priority_batch_001.reviewed.jsonl
```

반환 파일에서 바꾸면 안 되는 값:

- `chunk_id`
- `chunk_text`
- `chapter_id`
- `section_id`
- `page_start`
- `page_end`
- package/batch identity

반환 후에는 반드시 preflight를 실행한다.

```bash
/home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python scripts/validate_cape_human_review_returns.py \
  --experiment-dir experiments/cape_kg_eacl_20260627
```

---

## 11. Paper claim 주의사항

아래가 모두 끝나기 전까지 annotation 결과는 논문용 final evidence가 아니다.

- Annotator A/B가 최소 100 chunk를 독립 검수
- 100 chunk 이상에서 paired completion 확보
- IAA 계산
- adjudicator가 disagreement 해결
- adjudicated gold file 검증
- `P_cape_kg_actual`을 adjudicated gold에 대해 scoring

따라서 현재 annotation package는 `ready_for_review` 상태이며, `paper_claimable_gold` 상태가 아니다.
