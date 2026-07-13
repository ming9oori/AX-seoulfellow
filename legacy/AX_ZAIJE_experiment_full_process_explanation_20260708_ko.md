# AX 자이제 Layer2 KG 실험 진행 방식 전체 설명

작성일: 2026-07-08  
입력 데이터: `자이제_1.xlsx`  
방법론 문서: `AX_ZAIJE_Layer2_KG_Methodology.md`  
LLM 모델: OpenAI API `gpt-4o-mini`  
실행 성격: 사람 검수 전 schema-constrained Layer2 KG bootstrap

---

## 1. 전체 실험을 한 문장으로 정리

이번 실험은 `자이제_1.xlsx` 원문을 먼저 원문 근거 단위로 정리하고, 설계서 기반 Layer2 업무 schema를 만든 뒤, OpenAI LLM으로 원문에서 업무 relation 후보를 추출하고, schema validation을 거쳐 Layer2 지식그래프로 만든 실험이다.

```text
자이제_1.xlsx
→ 원문 근거 구조화
→ Layer2 업무 schema 구성
→ OpenAI LLM 기반 task linking / triple extraction
→ schema validation
→ Layer2 KG 생성
→ Neo4j 시각화
```

핵심은 LLM이 그래프를 자유롭게 생성한 것이 아니라, 미리 설계한 canonical node와 allowed predicate 안에서만 relation 후보를 제안하도록 제한했다는 점이다.

---

## 2. 입력 데이터 준비

입력 데이터는 `자이제_1.xlsx`이다. 이 파일에는 자이제 문서의 문장들이 page, chapter, section 정보와 함께 정리되어 있다.

실험에서는 이 원문 문장을 바로 KG relation으로 바꾸지 않았다. 먼저 문서 구조와 근거 문장 단위로 정리했다.

```text
Book
→ Chapter
→ Section
→ SourceChunk
→ EvidenceSpan
```

여기서 가장 중요한 단위는 `EvidenceSpan`이다. `EvidenceSpan`은 원문 문장 또는 근거 문장 단위이며, 예를 들어 `EV_ZAIJE_000007` 같은 ID를 갖는다.

`SourceChunk`는 LLM이 읽기 좋은 크기로 원문을 묶은 입력 단위이다. 원문 전체를 한 번에 LLM에 넣으면 너무 길고, 반대로 문장 하나씩만 넣으면 업무 맥락이 부족하다. 그래서 chapter/section 정보를 기준으로 원문을 중간 크기의 chunk로 나누었다.

이번 실험에서 `SourceChunk`는 크게 두 종류로 사용했다.

| SourceChunk 유형 | 사용 단계 | 의미 |
|---|---|---|
| `section_summary_chunk` | Task Frame linking | 한 section 전체가 어떤 canonical task와 관련되는지 판단하기 위한 요약 단위 |
| `paragraph_chunk` | Triple extraction | 실제 subject-predicate-object relation을 추출하기 위한 문단 단위 |

예를 들어 `1.1.1 제안서를 잘 써야 입찰에 성공한다`라는 section이 있으면, 이 section 아래 문장들을 다음과 같이 묶는다.

```text
ZAIJE_SEC_1_1_1_SUMMARY
ZAIJE_SEC_1_1_1_CHUNK_001
ZAIJE_SEC_1_1_1_CHUNK_002
...
```

각 `SourceChunk` 안에는 여러 개의 `EvidenceSpan`이 들어간다.

```text
ZAIJE_SEC_1_1_1_CHUNK_001
 ├─ EV_ZAIJE_000003
 ├─ EV_ZAIJE_000004
 ├─ EV_ZAIJE_000005
 └─ EV_ZAIJE_000006
```

여기서 `paragraph_chunk`는 원문에서 사람이 표시한 실제 문단을 그대로 의미하지 않는다. 이번 실행에서는 section 안의 원문 row들을 순서대로 누적하다가, 텍스트 길이가 약 1,100자를 넘기 직전에서 나누는 처리 단위로 구성했다.

구성 규칙은 다음과 같다.

```text
Section 안의 원문 row들
→ 원래 순서 유지
→ row text를 하나씩 누적
→ 누적 길이가 약 1,100자를 넘기 직전에서 chunk 분리
→ ZAIJE_SEC_<section_no>_CHUNK_001, 002 ... 형식의 ID 부여
```

예를 들어 `1.1.1 제안서를 잘 써야 입찰에 성공한다` section은 내용이 길기 때문에 다음처럼 여러 `paragraph_chunk`로 나뉘었다.

```text
ZAIJE_SEC_1_1_1_CHUNK_001
ZAIJE_SEC_1_1_1_CHUNK_002
ZAIJE_SEC_1_1_1_CHUNK_003
```

각 `paragraph_chunk`에는 어떤 원문 row가 포함되었는지를 `source_row_ids`로 기록했다.

```json
{
  "chunk_id": "ZAIJE_SEC_1_1_1_CHUNK_001",
  "chunk_type": "paragraph_chunk",
  "chapter_no": "1",
  "section_no": "1.1.1",
  "section_title": "제안서를 잘 써야 입찰에 성공한다",
  "page_start": 21,
  "page_end": 22,
  "source_row_ids": [
    "ZAIJE_1_ROW_000003",
    "ZAIJE_1_ROW_000004",
    "ZAIJE_1_ROW_000005"
  ],
  "text": "여러 원문 row를 줄바꿈으로 이어 붙인 텍스트"
}
```

이번 실행에서 `paragraph_chunk` 구성 통계는 다음과 같다.

| 항목 | 값 |
|---|---:|
| `paragraph_chunk` 개수 | 110 |
| 평균 길이 | 약 809자 |
| 최소/최대 길이 | 59자 / 1,258자 |
| 평균 포함 원문 row 수 | 약 12.4개 |
| 최소/최대 포함 원문 row 수 | 1개 / 29개 |

즉 `SourceChunk`와 `EvidenceSpan`의 차이는 다음과 같다.

| 구분 | SourceChunk | EvidenceSpan |
|---|---|---|
| 크기 | 비교적 큼 | 비교적 작음 |
| 단위 | section summary 또는 paragraph | 원문 문장 또는 근거 문장 |
| 주 용도 | LLM 입력 단위 | node/edge의 근거 추적 단위 |
| 예시 ID | `ZAIJE_SEC_1_1_1_CHUNK_001` | `EV_ZAIJE_000007` |
| 답하는 질문 | LLM이 무엇을 읽었는가? | 이 지식은 원문 어디에서 나왔는가? |

`SourceChunk`가 필요한 이유는 LLM 입력의 크기와 맥락을 조절하기 위해서이다.

| 입력 방식 | 문제 |
|---|---|
| 문서 전체를 한 번에 입력 | 비용이 커지고, 서로 다른 section의 내용이 섞이며, 관계 추적이 어려움 |
| 문장 하나씩 입력 | 맥락이 부족해 task 판단과 relation 추출이 어려움 |
| SourceChunk 단위 입력 | 적절한 맥락을 유지하면서 evidence 단위 추적도 가능 |

이렇게 한 이유는 나중에 어떤 node나 edge가 생기더라도 다음 질문에 답할 수 있게 하기 위해서이다.

```text
이 node는 원문 어디에서 나온 것인가?
이 edge는 어떤 문장을 근거로 만들어졌는가?
```

따라서 이번 KG는 단순히 업무 개념과 관계를 나열한 것이 아니라, 각 지식 요소가 원문 근거로 되돌아갈 수 있도록 설계되었다.

---

## 3. Layer2 업무 Schema 설계

다음 단계에서는 수주·제안 도메인을 표현하기 위한 Layer2 schema를 설계했다.

여기서 schema란 다음을 의미한다.

```text
어떤 종류의 node를 만들 것인가?
어떤 종류의 edge를 허용할 것인가?
각 edge는 어떤 node type 사이에서만 허용할 것인가?
```

대표적인 node type은 다음과 같다.

| node type | 의미 |
|---|---|
| `DomainProcess` | 큰 업무 흐름 |
| `DomainTask` | 실제 업무 단위 |
| `Artifact` | 문서, 산출물, 도구 |
| `InformationObject` | 업무에 필요한 정보 내용 |
| `Role` | 수행자 |
| `Stakeholder` | 이해관계자 |
| `DecisionPoint` | 의사결정 지점 |
| `Principle` | 업무 원칙 |
| `Risk` | 위험 요소 |
| `ReviewType` | 검토 단계 |

대표적인 predicate, 즉 edge type은 다음과 같다.

| predicate | 의미 |
|---|---|
| `HAS_PROCESS` | 온톨로지가 process를 가짐 |
| `HAS_TASK` | process가 task를 가짐 |
| `USES_INPUT` | task가 입력 정보를 사용 |
| `PRODUCES` | task가 산출물을 생성 |
| `CONTAINS` | 문서나 정보가 하위 정보를 포함 |
| `ANALYZES` | task가 정보를 분석 |
| `HAS_REVIEW` | task가 review 단계를 가짐 |
| `HAS_PRINCIPLE` | task가 원칙을 따름 |
| `EVIDENCED_BY` | node/edge가 원문 근거와 연결됨 |

중요한 점은 LLM이 predicate를 마음대로 만들지 못하게 했다는 것이다. LLM이 자유롭게 relation 이름을 만들면 `includes`, `has`, `contains_info`, `담고있다`, `관련된다`처럼 비슷한 의미의 edge가 여러 이름으로 생길 수 있다.

그래서 설계서에서 allowed predicate를 미리 고정했다.

---

## 4. 원 설계상 Canonical ID 생성 방식

원래 설계서의 의도는 canonical ID를 처음부터 사람이 모두 고정하는 것이 아니라, Task Frame LLM이 문서를 읽고 핵심 업무 단위와 슬롯 후보를 추출한 뒤, 후처리로 canonical ID를 확정하는 방식이다.

설계상 흐름은 다음과 같다.

```text
OCR 문서
→ 문서 구조 분할
→ Task Frame LLM으로 핵심 업무 단위 추출
→ Task Frame 슬롯에서 node 후보 도출
→ alias 병합 및 canonicalization
→ node type 결정
→ L2_<NODE_TYPE>_<CANONICAL_LABEL> 형식의 canonical ID 부여
→ 사람 검토로 최종 ID와 정의 확정
```

예를 들어 LLM이 다음과 같은 Task Frame을 만들었다고 가정할 수 있다.

```json
{
  "task_name": "수주영업",
  "inputs": ["고객 정보", "경쟁사 정보"],
  "outputs": ["Capture Plan", "수주전략"],
  "roles": ["제안팀"],
  "decision_points": ["Bid/No-Bid Decision"],
  "next_tasks": ["제안서 기획"]
}
```

이때 `task_name`, `inputs`, `outputs`, `roles` 같은 칸을 슬롯이라고 부른다. 설계서에서는 별도의 전체 entity extraction LLM을 두지 않고, 이 Task Frame 슬롯에서 node 후보를 도출하도록 설계했다.

| 슬롯 | 값 | 후처리 node type |
|---|---|---|
| `task_name` | 수주영업 | `DomainTask` |
| `inputs` | 고객 정보 | `InformationObject` |
| `inputs` | 경쟁사 정보 | `InformationObject` |
| `outputs` | Capture Plan | `Artifact` |
| `outputs` | 수주전략 | `StrategyPattern` |
| `roles` | 제안팀 | `Role` |
| `decision_points` | Bid/No-Bid Decision | `DecisionPoint` |
| `next_tasks` | 제안서 기획 | `DomainTask` |

그 다음 canonical ID는 다음 규칙으로 붙인다.

```text
L2_<NODE_TYPE_PREFIX>_<CANONICAL_LABEL_IN_UPPER_SNAKE_CASE>
```

예시는 다음과 같다.

| 표현 | node type | canonical ID |
|---|---|---|
| 수주영업 / Capture Planning | `DomainTask` | `L2_TASK_CAPTURE_PLANNING` |
| 고객 정보 | `InformationObject` | `L2_INFO_CUSTOMER_INFORMATION` |
| Capture Plan | `Artifact` | `L2_ARTIFACT_CAPTURE_PLAN` |
| 제안팀 | `Role` | `L2_ROLE_PROPOSAL_TEAM` |
| Bid/No-Bid Decision | `DecisionPoint` | `L2_DECISION_BID_NO_BID` |

즉 원 설계에서는 다음 흐름이 핵심이다.

```text
Task Frame LLM 후보 추출
→ 슬롯 기반 node type 부여
→ alias 병합
→ canonical ID 생성
→ 사람 검토
```

---

## 5. 이번 실제 실행에서 달라진 점

이번 실제 실행에서는 원 설계서의 전체 절차를 완전히 자동으로 새로 수행하지 않았다.

대신 사람 검수 전 단계에서 그래프를 안정적으로 만들기 위해, 설계서와 코드에 있는 seed canonical inventory를 먼저 고정했다.

이번 실행의 흐름은 다음에 가깝다.

```text
설계서 기반 seed canonical inventory 고정
→ LLM은 그 안에서만 task와 relation 후보 선택
→ validation으로 최종 반영
```

따라서 이번 실행에서 LLM의 역할은 다음이 아니다.

```text
새 node ID를 확정하는 것
```

이번 실행에서 LLM의 실제 역할은 다음이다.

```text
이미 정해진 canonical node와 allowed predicate 안에서
원문에 근거한 relation 후보를 추출하는 것
```

이 방식은 사람 검수 전 bootstrap 단계에서는 더 안정적이다. LLM이 새 node와 predicate를 자유롭게 만들면 graph가 빠르게 지저분해질 수 있기 때문이다.

### 5-1. 이번 실행에서 사용한 15개 canonical task

이번 실행에서 LLM은 task를 새로 확정하지 않고, 아래 15개 canonical task 중에서 원문 section과 관련 있는 task를 선택했다. 즉 Task linking은 "새 업무를 만드는 단계"가 아니라, "원문 근거를 이미 정의된 업무 단위에 연결하는 단계"였다.

| No. | task id | 업무명 | 상위 process | 정의 |
|---:|---|---|---|---|
| 1 | `L2_TASK_REQUIREMENT_ICEBERG_ANALYSIS` | 고객 요구조건 구조 분석 | 입찰·제안 환경 이해 | RFP의 공식 요구조건과 원문 뒤에 숨은 비공식 요구조건을 구분하여 고객 니즈 구조를 파악하는 업무 |
| 2 | `L2_TASK_OPPORTUNITY_PLANNING` | 사전영업 / Opportunity Planning | 제안참여 전 준비 | 고객 관계와 기회 정보를 바탕으로 제안 참여 전 사업 기회의 성격과 준비 방향을 판단하는 업무 |
| 3 | `L2_TASK_CAPTURE_PLANNING` | 수주영업 / Capture Planning | 수주영업 | 고객·경쟁사·자사 솔루션 정보를 수집·분석해 Capture Plan과 수주전략을 만드는 업무 |
| 4 | `L2_TASK_BID_NO_BID_DECISION` | 제안참여 의사결정 | 제안참여 전 준비 | 기회분석, Capture Plan, RFP 정보를 토대로 제안 참여 여부를 판단하는 의사결정 업무 |
| 5 | `L2_TASK_PROPOSAL_PLANNING` | 제안서 기획 / Proposal Planning | 제안서 작성·프레젠테이션 | Capture Plan과 수주전략을 바탕으로 제안서 구조, 일정, 역할, 관리계획을 수립하는 업무 |
| 6 | `L2_TASK_PROPOSAL_PREPARING` | 제안서 작성 / Proposal Preparing | 제안서 작성·프레젠테이션 | 제안전략, 섹션 기획, 리뷰 계획을 반영해 제안서 초안과 완성본을 작성하는 업무 |
| 7 | `L2_TASK_PRESENTATION_PREPARATION` | 프레젠테이션 준비 | 제안서 작성·프레젠테이션 | 제안전략과 평가자 정보를 바탕으로 PT 자료와 발표전략을 준비하는 업무 |
| 8 | `L2_TASK_SALES_INFORMATION_MANAGEMENT` | 영업 정보 관리 | 수주영업 | 고객성향, 의사결정 프로세스, 경쟁 정보를 체계적으로 축적하고 관리하는 업무 |
| 9 | `L2_TASK_VALUE_PROPOSITION` | 가치제안 개발 | 수주영업 | 고객 효용, 비용, 경쟁자 대비 가치를 조합해 고객에게 설득력 있는 가치제안을 개발하는 업무 |
| 10 | `L2_TASK_EVALUATOR_ANALYSIS` | 평가자 분석 | 평가자 공략과 설득 | 의사결정자, 영향자, 기술전문가, 사용자, 구매/행정 그룹 등 평가자 유형별 관심과 관점을 분석하는 업무 |
| 11 | `L2_TASK_PERSUASIVE_COMMUNICATION` | 설득 커뮤니케이션 설계 | 평가자 공략과 설득 | 고객 구매단계, 신뢰도, 커뮤니케이션 스타일, 구매심리를 반영해 평가자 맞춤 메시지를 설계하는 업무 |
| 12 | `L2_TASK_PROPOSAL_STRATEGY_DEVELOPMENT` | 제안전략 개발 | 제안전략 개발 | 고객 이슈, 경쟁사 분석, 자사 차별화 요소를 연결해 제안전략과 전략기술서를 개발하는 업무 |
| 13 | `L2_TASK_COMPETITOR_ANALYSIS` | 경쟁사 분석 및 차별화 요소 규명 | 제안전략 개발 | 경쟁사 정보, 고객 평가 기준, 자사 강약점을 비교하여 핵심 차별화 요소와 BCM을 도출하는 업무 |
| 14 | `L2_TASK_TACTIC_DEVELOPMENT_VALIDATION` | 전술 개발 및 효과성 검증 | 제안전략 개발 | 전략기술서를 바탕으로 솔루션과 커뮤니케이션 방법을 구체화하고 전술의 효과성을 검증하는 업무 |
| 15 | `L2_TASK_RISK_MANAGEMENT` | 리스크 관리 | 제안전략 개발 | 사업 리스크와 경쟁자 약점을 분석하고 대응 전략을 만들어 차별화 포인트로 전환하는 업무 |

---

## 6. LLM 적용 방식

OpenAI API `gpt-4o-mini`를 사용했다.

LLM은 두 단계로 사용했다.

| 단계 | 입력 | 출력 |
|---|---|---|
| Task Frame linking | section summary chunk | 이 section이 어떤 canonical task와 관련되는지 |
| Triple extraction | paragraph chunk | subject-predicate-object relation 후보 |

Task Frame linking은 다음 질문에 답하는 단계이다.

```text
이 section은 수주영업과 관련이 있는가?
이 section은 제안서 기획과 관련이 있는가?
이 section은 제안전략 개발과 관련이 있는가?
```

Triple extraction은 다음 질문에 답하는 단계이다.

```text
이 문장에서 어떤 업무 relation을 추출할 수 있는가?
```

예를 들어 원문에 RFP와 공식 요구조건이 나온다면 LLM은 다음과 같은 triple 후보를 만들 수 있다.

```json
{
  "subject_id": "L2_ARTIFACT_RFP",
  "predicate": "CONTAINS",
  "object_id": "L2_INFO_OFFICIAL_REQUIREMENT",
  "evidence_ids": ["EV_ZAIJE_000007", "EV_ZAIJE_000008"],
  "confidence": 1.0
}
```

이 triple의 의미는 다음과 같다.

```text
RFP는 공식 요구조건을 포함한다.
이 관계의 근거는 EV_ZAIJE_000007, EV_ZAIJE_000008이다.
```

---

## 7. Validation

LLM이 만든 triple을 바로 KG에 넣지 않았다. 다음 조건을 검사했다.

| 검증 | 기준 |
|---|---|
| subject 검증 | subject가 canonical node인지 |
| object 검증 | object가 canonical node인지 |
| predicate 검증 | allowed predicate인지 |
| evidence 검증 | 실제 EvidenceSpan id가 있는지 |
| domain/range 검증 | predicate가 허용된 node type 사이에서 쓰였는지 |
| confidence 검증 | 0.60 이상인지 |
| 중복 제거 | 같은 subject-predicate-object는 하나로 병합 |

예를 들어 다음 관계는 허용된다.

```text
L2_ARTIFACT_RFP -[CONTAINS]-> L2_INFO_OFFICIAL_REQUIREMENT
```

허용되는 이유는 다음과 같다.

```text
RFP = Artifact
공식 요구조건 = InformationObject
CONTAINS = Artifact/InformationObject → InformationObject 허용
```

반대로 다음과 같은 관계는 제외된다.

```text
Role -[CONTAINS]-> Risk
```

이유는 `CONTAINS`의 domain/range와 맞지 않기 때문이다.

---

## 8. Graph Materialization

검증을 통과한 node와 edge를 최종 KG로 만들었다.

node는 크게 세 종류이다.

| node 그룹 | 예시 |
|---|---|
| 원문 구조 node | `Book`, `Chapter`, `Section`, `SourceChunk`, `EvidenceSpan` |
| 업무 지식 node | `DomainProcess`, `DomainTask`, `Artifact`, `InformationObject` |
| 보조 node | `AliasTerm`, `Role`, `Stakeholder`, `Principle`, `Risk` |

edge도 크게 세 종류이다.

| edge 그룹 | 예시 |
|---|---|
| 문서 구조 edge | `HAS_CHAPTER`, `HAS_SECTION`, `HAS_CHUNK` |
| 업무 관계 edge | `HAS_TASK`, `USES_INPUT`, `PRODUCES`, `CONTAINS`, `ANALYZES` |
| 근거 연결 edge | `EVIDENCED_BY`, `ALIAS_OF` |

`EVIDENCED_BY`가 많은 이유는 LLM이 업무 relation으로 많이 추출했기 때문이 아니다. 거의 모든 node와 edge가 원문 근거로 연결되기 때문이다. 즉 `EVIDENCED_BY`는 provenance 구조이다.

---

## 9. 최종 결과

최종 결과는 다음과 같다.

| 항목 | 값 |
|---|---:|
| EvidenceSpan | 1,366 |
| SourceChunk | 166 |
| DomainTask | 15 |
| DomainProcess | 6 |
| LLM accepted triples | 188 |
| Schema-validated triples | 103 |
| Nodes | 1,869 |
| Edges | 2,280 |

LLM이 제안한 triple 중 일부만 최종 KG에 들어갔다.

```text
LLM accepted triples: 188
Schema-validated triples: 103
```

차이가 나는 이유는 중복 제거, domain/range validation, evidence validation 등을 거쳤기 때문이다.

---

## 10. Neo4j 시각화

Neo4j 시각화를 위해 clean CSV를 만들었다.

사용하는 파일은 다음이다.

```text
zaije_v2_clean_nodes.csv
zaije_v2_clean_edges.csv
zaije_v2_clean_import.cypher
```

clean 버전은 `raw_json`과 긴 원문 텍스트를 제거한 버전이다. Neo4j CSV parser가 긴 JSON 문자열과 따옴표 때문에 오류를 냈기 때문에, 시각화용으로는 clean 버전을 사용하는 것이 적절하다.

Neo4j에서 시각화할 때는 `EVIDENCED_BY`, `ALIAS_OF`, `HAS_CHUNK`까지 모두 보면 너무 복잡하다. 따라서 처음에는 업무 관계만 보는 것이 좋다.

예시 쿼리는 다음과 같다.

```cypher
MATCH p=(n)-[r]->(m)
WHERE type(r) IN [
  'HAS_PROCESS',
  'HAS_TASK',
  'USES_INPUT',
  'PRODUCES',
  'CONTAINS',
  'ANALYZES',
  'DISCOVERS',
  'HAS_REVIEW',
  'HAS_PRINCIPLE',
  'TARGETS_STAKEHOLDER'
]
RETURN p
LIMIT 200;
```

---

## 11. 현재 결과의 의미

현재 결과는 사람 검수 전 bootstrap KG이다.

즉 다음이 아니다.

```text
완성된 gold KG
```

현재 결과는 다음에 가깝다.

```text
설계서 기반 schema-constrained LLM KG 초안
```

현재 강점은 다음과 같다.

```text
원문 근거 추적 가능
schema validation 적용
LLM 자유 생성 억제
canonical node/predicate 사용
Neo4j 시각화 가능
```

현재 한계는 다음과 같다.

```text
canonical inventory는 seed 기반
사람 검수 미완료
CQ exact path는 아직 낮음
일부 relation은 추가 보강 필요
```

---

## 12. 최종 요약

이번 실험은 `자이제_1.xlsx` 원문을 `EvidenceSpan`으로 정리하고, 설계서 기반 canonical node와 predicate schema를 고정한 뒤, OpenAI LLM으로 원문 근거 기반 triple 후보를 추출하고, validation을 통과한 후보만 Layer2 KG로 만든 실험이다.

원 설계는 Task Frame LLM을 통해 canonical 후보를 만들고 사람 검토로 확정하는 방식이다. 그러나 이번 실행은 사람 검토 전 안정성을 위해 seed inventory를 고정한 bootstrap 방식으로 진행되었다.

따라서 한 문장으로 정리하면 다음과 같다.

```text
이번 실험은 LLM이 KG를 자유 생성한 것이 아니라,
설계된 Layer2 업무 schema 안에서 원문 근거 기반 relation 후보를 채우고,
검증을 통과한 후보만 KG로 반영한 schema-constrained KG 구축 실험이다.
```
