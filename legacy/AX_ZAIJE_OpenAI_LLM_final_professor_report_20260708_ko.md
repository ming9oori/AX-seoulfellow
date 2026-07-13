# AX 자이제 데이터 Layer2 KG 최종 반영 내용

작성일: 2026-07-08  
입력 데이터: `자이제_1.xlsx`  
방법론 문서: `AX_ZAIJE_Layer2_KG_Methodology.md`  
LLM 모델: OpenAI API `gpt-4o-mini`  
Run ID: `RUN_2026_07_08_METHOD_V2_REPLAY_001`  
최종 실행 경로: `experiments/ax_zaije_layer2_kg_openai_methodology_v2_20260708/layer2_kg`  
방법론 v2 보고 문서: `AX_ZAIJE_Methodology_V2_final_professor_report_20260708_ko.md`

---

## 0. 방법론 v2 보강 반영

기존 OpenAI LLM 원시 응답은 그대로 유지하고, schema 설계 근거를 명시한 v2 replay build를 수행하였다. v2 보강의 핵심은 node type, canonical process/task/entity, predicate schema가 어떻게 도출되었는지를 방법론 단계로 분리한 것이다.

원 설계서 기준으로는 Task Frame LLM이 핵심 업무 단위와 `inputs`, `outputs`, `roles`, `decision_points`, `principles` 같은 슬롯 후보를 추출하고, 후처리 단계에서 alias 병합, slot-based typing, canonical label 결정을 수행한 뒤 `L2_<NODE_TYPE>_<CANONICAL_LABEL>` 형식의 ID를 부여하는 흐름이다.

이번 실행에서는 이 전체 절차를 새로 자동 수행하지 않고, 설계서 기반 seed canonical inventory를 먼저 고정하였다. 따라서 LLM은 새 canonical ID를 확정하는 역할이 아니라, 고정된 canonical node와 allowed predicate 안에서 task link와 triple 후보를 제안하는 역할로 사용되었다.

Task Frame LLM 원시 응답에는 placeholder evidence id가 포함되어 있었다. v2에서는 LLM의 task 판단 자체는 바꾸지 않고, 해당 section summary chunk의 실제 EvidenceSpan id로 reconciliation하여 evidence grounding을 맞추었다.

---

## 1. 최종 KG 구성

| 항목 | 값 |
|---|---:|
| Graph nodes | 1,869 |
| Graph edges | 2,280 |
| SourceChunk | 166 |
| EvidenceSpan | 1,366 |
| DomainTask | 15 |
| DomainProcess | 6 |
| Review queue rows | 21 |

최종 KG는 다음 두 층으로 구성된다.

| 구성 | 반영 내용 |
|---|---|
| Source Evidence Graph | 원문 문장, section, chunk, evidence span 구조 |
| Domain Ontology Graph | Task, Process, Artifact, InformationObject, Role, Stakeholder, Principle, Risk, ReviewType 등 업무 지식 구조 |

---

## 2. 입력 데이터 반영 내용

| 항목 | 값 |
|---|---:|
| 유효 문장 행 | 1,366 |
| section summary chunk | 51 |
| paragraph chunk | 110 |
| 전체 SourceChunk | 166 |
| EvidenceSpan | 1,366 |

Evidence 구조는 다음과 같이 반영되었다.

```text
Book
→ Chapter
→ Section
→ SourceChunk
→ EvidenceSpan
```

각 `EvidenceSpan`은 page, chapter, section, source row, text span을 포함한다.  
최종 node와 edge는 가능한 한 이 `EvidenceSpan`을 근거로 참조한다.

---

## 3. LLM 반영 내용

| 항목 | 값 |
|---|---:|
| LLM 모델 | `gpt-4o-mini` |
| Task Frame LLM rows | 51 |
| Triple LLM rows | 110 |
| 전체 LLM 호출 | 161 |
| Prompt tokens | 782,179 |
| Completion tokens | 74,562 |
| Total tokens | 856,741 |
| 추정 비용 | USD 0.162064 |

LLM 입력 단위는 다음과 같이 구성하였다.

| LLM 단계 | 입력 단위 | 후속 처리 |
|---|---|---|
| Task Frame linking | section summary chunk | canonical task와 원문 evidence 연결에 사용 |
| Triple extraction | paragraph chunk | validation 후 KG edge 후보로 사용 |

LLM 출력은 자유 생성 결과로 사용하지 않고, 사전에 정의된 canonical node와 allowed predicate 안에서만 KG 후보로 반영하였다.

---

## 4. Triple 반영 결과

| 항목 | 값 |
|---|---:|
| LLM accepted triples | 188 |
| LLM rejected triples | 100 |
| Raw triples | 209 |
| Schema-validated triples | 103 |

`LLM accepted triples`는 다음 조건을 통과한 triple이다.

| 조건 | 반영 기준 |
|---|---|
| subject | canonical node id에 존재 |
| object | canonical node id에 존재 |
| predicate | Layer2 allowed predicate에 포함 |
| evidence | 실제 EvidenceSpan id 참조 |
| frame task | canonical task id 또는 empty |
| duplicate | 동일 SPO 중복 제외 |

`Schema-validated triples`는 accepted triple 중 domain/range/evidence validation까지 통과한 triple이다.

---

## 5. KG 구축 방법론

| 단계 | 방법론 | 최종 반영 방식 |
|---|---|---|
| 1. Source Evidence Graph 구성 | 원문을 바로 업무 지식으로 변환하지 않고, 먼저 근거 그래프를 구성 | `Book → Chapter → Section → SourceChunk → EvidenceSpan` |
| 2. Canonical inventory 고정 | LLM이 node를 자유 생성하지 않도록 설계서 기반 node 후보를 먼저 고정 | Process, DomainTask, Artifact, InformationObject, Role, Stakeholder 등 |
| 3. Schema-constrained LLM extraction | LLM이 predicate를 자유 생성하지 않도록 allowed predicate와 domain/range를 prompt에 포함 | `USES_INPUT`, `PRODUCES`, `HAS_TASK`, `ANALYZES` 등 Layer2 schema predicate |
| 4. Evidence-grounded extraction | LLM 출력마다 evidence id를 요구 | 실제 `EvidenceSpan` id가 없는 triple은 제외 |
| 5. Canonical node validation | LLM의 subject/object가 canonical node id인지 확인 | 없는 node id는 rejected |
| 6. Predicate validation | LLM predicate가 Layer2 allowed predicate인지 확인 | schema 밖 predicate는 rejected |
| 7. Domain/range validation | predicate별 허용 source/target node type 확인 | domain/range 위반 triple은 최종 validation에서 제외 |
| 8. Deduplication | 같은 subject-predicate-object 반복 제거 | 동일 SPO는 하나의 edge 후보로 정리 |
| 9. Graph materialization | validated triple과 source evidence 구조를 결합 | `10_nodes.jsonl`, `11_edges.jsonl` |
| 10. Evaluation | 구조 품질과 CQ exact path 평가 | `12_quality_report.md`, `16_competency_questions.json` |

방법론의 핵심은 LLM이 KG를 자유롭게 생성하는 방식이 아니라, **schema-constrained + evidence-grounded KG construction** 방식이다.

즉, LLM은 원문에서 relation 후보를 제안하지만, 최종 KG 반영 여부는 다음 조건으로 제한된다.

```text
canonical node id 존재
allowed predicate 사용
EvidenceSpan id 존재
predicate domain/range 일치
confidence threshold 통과
중복 SPO 제거
```

이 방식은 LLM의 자유 생성으로 인한 predicate 난립, 근거 없는 triple, 임의 node 생성을 줄이기 위한 구조이다.

---

## 6. Confidence 반영 방식

`confidence`는 별도 통계 모델로 계산한 확률값이 아니라, OpenAI LLM이 각 triple JSON에 함께 출력한 자기평가 점수이다.

LLM prompt에서는 각 triple에 대해 다음과 같은 값을 요구했다.

```json
{
  "subject_id": "canonical node id",
  "predicate": "allowed predicate",
  "object_id": "canonical node id",
  "evidence_ids": ["EV_ZAIJE_000000"],
  "confidence": 0.0,
  "relation_scope": "process_step"
}
```

최종 반영 과정에서는 이 값을 다음 방식으로 처리했다.

| 처리 | 내용 |
|---|---|
| 입력값 | LLM이 생성한 `confidence` |
| 범위 보정 | 0.0보다 작으면 0.0, 1.0보다 크면 1.0으로 제한 |
| 값 누락 시 | 기본값 0.72 사용 |
| schema scaffold edge | LLM 점수가 아니라 내부 고정값 0.95 사용 |
| Task Frame evidence가 LLM으로 확인된 경우 | Task confidence 0.92 사용 |
| 최종 triple threshold | confidence 0.60 미만은 validation에서 제외 |
| validation status | confidence 0.80 이상은 `verified`, 0.80 미만은 `needs_review` |

따라서 문서의 `confidence`는 사람이 검수한 정답 확률이 아니다.  
현재 단계에서는 다음과 같이 해석하는 것이 적절하다.

```text
LLM이 해당 evidence와 schema 조건을 바탕으로 제안한 relation 후보의 자기평가 신뢰도
```

confidence는 자동 필터링과 review 우선순위 산정에는 사용할 수 있지만, 사람 검수 전에는 최종 정답 확률로 주장하면 안 된다.

---

## 7. Rejected Triple 분포

| reject issue | count |
|---|---:|
| `duplicate_spo` | 97 |
| `subject_not_in_candidate_nodes` | 1 |
| `object_not_in_candidate_nodes` | 1 |
| `frame_task_id_not_canonical` | 1 |

Rejected triple의 대부분은 동일한 subject-predicate-object가 여러 evidence에서 반복 제안된 경우이다.

---

## 8. Node Type 분포

| Node type | Count |
|---|---:|
| `EvidenceSpan` | 1,366 |
| `AliasTerm` | 201 |
| `SourceChunk` | 166 |
| `Section` | 51 |
| `InformationObject` | 20 |
| `DomainTask` | 15 |
| `Artifact` | 10 |
| `StrategyPattern` | 7 |
| `DomainProcess` | 6 |
| `Stakeholder` | 6 |
| `ReviewType` | 4 |
| `Chapter` | 3 |
| `Role` | 3 |
| `Principle` | 3 |
| `DecisionOutcome` | 2 |
| `Risk` | 2 |
| `DomainOntology` | 1 |
| `Book` | 1 |
| `DecisionPoint` | 1 |
| `Metric` | 1 |

---

## 9. Edge Predicate 분포

| Predicate | Count |
|---|---:|
| `EVIDENCED_BY` | 1,756 |
| `ALIAS_OF` | 201 |
| `HAS_CHUNK` | 166 |
| `HAS_SECTION` | 51 |
| `HAS_TASK` | 38 |
| `USES_INPUT` | 12 |
| `TARGETS_STAKEHOLDER` | 9 |
| `DISCOVERS` | 9 |
| `PRODUCES` | 7 |
| `HAS_PROCESS` | 6 |
| `CONTAINS` | 4 |
| `HAS_SUBTASK` | 4 |
| `HAS_PRINCIPLE` | 4 |
| `HAS_CHAPTER` | 3 |
| `PART_OF` | 2 |
| `PERFORMED_BY` | 2 |
| `HAS_DECISION_POINT` | 2 |
| `HAS_REVIEW` | 2 |
| `ANALYZES` | 2 |

---

## 10. LLM Accepted Predicate 분포

| Predicate | LLM accepted triples |
|---|---:|
| `HAS_TASK` | 93 |
| `DISCOVERS` | 20 |
| `HAS_PROCESS` | 12 |
| `TARGETS_STAKEHOLDER` | 12 |
| `USES_INPUT` | 12 |
| `PRODUCES` | 8 |
| `HAS_SUBTASK` | 7 |
| `PERFORMED_BY` | 5 |
| `CONTAINS` | 4 |
| `HAS_PRINCIPLE` | 4 |
| `PART_OF` | 3 |
| `HAS_DECISION_POINT` | 2 |
| `HAS_REVIEW` | 2 |
| `ANALYZES` | 2 |
| `DECIDES` | 1 |
| `DEVELOPS` | 1 |

---

## 11. 품질 지표

| 지표 | 값 | 상태 |
|---|---:|---|
| `node_grounded_rate_domain_only` | 1.0000 | PASS |
| `edge_grounded_rate` | 1.0000 | PASS |
| `predicate_valid_rate` | 1.0000 | PASS |
| `task_orphan_rate` | 0.0000 | PASS |
| `case_leakage_rate` | 0.0000 | PASS |
| `duplicate_alias_rate` | 0.0796 | INFO |
| `review_resolution_rate` | 0.0000 | OPEN |
| `cq_pass_rate` | 0.0000 | REVIEW |

---

## 12. Competency Question 결과

| CQ | 질문 | 결과 | 체크 |
|---|---|---|---:|
| CQ1 | 제안전략을 세우기 전에 어떤 정보와 산출물이 필요한가? | FAIL | 2/3 |
| CQ2 | Capture Plan은 어떤 업무에서 생성되고 어디에 사용되는가? | FAIL | 1/2 |
| CQ3 | Bid/No-Bid 의사결정은 어느 단계에서 발생하며 어떤 입력을 쓰는가? | FAIL | 1/2 |
| CQ4 | 평가자 유형에 따라 커뮤니케이션은 어떻게 달라지는가? | FAIL | 0/3 |
| CQ5 | 리스크 관리는 어떻게 차별화 포인트로 이어지는가? | FAIL | 0/2 |
| CQ6 | 제안서 작성 단계에서 어떤 리뷰 또는 마일스톤이 필요한가? | FAIL | 1/3 |
| CQ7 | 고객의 공식 요구조건과 비공식 요구조건은 어떻게 구분되는가? | FAIL | 1/2 |

CQ exact path 기준에서 부족한 predicate는 다음과 같다.

| Predicate | 관련 경로 |
|---|---|
| `USED_AS_INPUT_FOR` | Capture Plan → 후속 Task 입력 |
| `MITIGATES` | 리스크 관리 → 리스크 완화 |
| `MAY_RESULT_IN` | 리스크 관리 → 차별화 포인트 |
| `REFINES_INTO` | 수주전략 → 제안전략 정교화 |

---

## 13. Triple 예시

### 예시 1

```json
{
  "subject_id": "L2_ARTIFACT_RFP",
  "predicate": "CONTAINS",
  "object_id": "L2_INFO_OFFICIAL_REQUIREMENT",
  "evidence_refs": ["EV_ZAIJE_000007", "EV_ZAIJE_000008"],
  "confidence": 1.0,
  "relation_scope": "process_step",
  "evidence_span": "아래 <그림 1>처럼 제안 요청서상 고객의 공식적인 요구조건은 실제 고객의 요구조건을 100% 모두 다루고 있지 않기 때문이다."
}
```

### 예시 2

```json
{
  "subject_id": "L2_PROCESS_PRE_BID_PREPARATION",
  "predicate": "HAS_TASK",
  "object_id": "L2_TASK_PROPOSAL_STRATEGY_DEVELOPMENT",
  "evidence_refs": ["EV_ZAIJE_000002"],
  "confidence": 1.0,
  "relation_scope": "process_step",
  "evidence_span": "경쟁력 있는 제안 역량이란 차별화된 정보를 수집할 줄 아는 전문가 영업 역량, 고객의 정보를 이기는 전략으로 만들 수 있는 전략 개발 역량, 이를 고객과 소통할 줄 아는 제안서 역량, PT 역량을 의미한다."
}
```

---

## 14. KG 구축 논리 요약

이 KG는 원문 문장을 바로 relation으로 변환한 것이 아니라, 먼저 원문을 evidence 단위로 고정한 뒤 그 위에 업무 지식을 얹는 방식으로 구축하였다.

첫째, 원문은 `Book → Chapter → Section → SourceChunk → EvidenceSpan` 구조로 정규화하였다. 이 단계의 목적은 모든 node와 edge가 원문 근거로 되돌아갈 수 있게 만드는 것이다.

둘째, 업무 지식 schema를 먼저 설계하였다. `DomainTask`, `Artifact`, `InformationObject`, `Role`, `Stakeholder` 같은 node type을 정하고, 자이제 도메인에서 필요한 canonical process, task, entity를 고정하였다. 이 때문에 LLM이 임의의 node를 생성하지 않고, 정해진 canonical id 안에서만 relation을 제안하게 된다.

셋째, predicate도 사전에 제한하였다. `USES_INPUT`, `PRODUCES`, `CONTAINS`, `ANALYZES`, `HAS_REVIEW`처럼 업무 관계를 표현할 수 있는 relation type을 정하고, 각 predicate마다 가능한 source/target node type을 지정하였다. 예를 들어 `CONTAINS`는 `Artifact/InformationObject → InformationObject` 관계로 제한된다.

넷째, LLM은 schema를 만드는 역할이 아니라 evidence-grounded extractor 역할을 수행하였다. 즉 paragraph chunk를 읽고, canonical subject와 object, allowed predicate, evidence id, confidence를 포함한 triple 후보를 제안하였다.

다섯째, 최종 반영은 validation을 통과한 경우로 제한하였다. canonical id가 없거나, predicate가 schema 밖이거나, evidence id가 없거나, domain/range가 맞지 않거나, confidence가 낮은 triple은 제외하였다. 동일 subject-predicate-object가 반복된 경우 하나로 병합하고 evidence만 누적하였다.

---

## 15. 최종 상태

| 항목 | 상태 |
|---|---|
| OpenAI API LLM 반영 | 완료 |
| Layer2 KG bootstrap | 완료 |
| Evidence 기반 자동 검증 | 완료 |
| Schema 기반 자동 검증 | 완료 |
| Neo4j export | 완료 |
| RDF export | 완료 |
| Schema 설계 traceability | 완료 |
| 사람 검수 | 미완료 |
| Gold KG 주장 | 보류 |
| CQ-aware 보강 | 필요 |

---

## 16. 보고용 핵심 문장

```text
최종 KG는 node 1,869개와 edge 2,280개로 구성됩니다.
OpenAI API gpt-4o-mini를 통해 Task Frame row 51개와 Triple row 110개가 반영되었고,
LLM accepted triple 188개 중 schema-validated triple 103개가 최종 반영되었습니다.
모든 graph element는 evidence id와 Layer2 schema 기준으로 자동 검증되었습니다.
현재 결과는 사람 검수 전 Layer2 KG bootstrap이며,
CQ exact path 기준은 0/7로 다음 단계에서 CQ-aware 보강이 필요합니다.
```
