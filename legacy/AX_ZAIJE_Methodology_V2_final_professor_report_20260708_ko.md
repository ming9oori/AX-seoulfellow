# AX 자이제 데이터 Layer2 KG 방법론 v2 및 최종 실험 결과

작성일: 2026-07-08  
입력 데이터: `자이제_1.xlsx`  
방법론 문서: `AX_ZAIJE_Layer2_KG_Methodology.md`  
LLM 모델: OpenAI API `gpt-4o-mini`  
Run ID: `RUN_2026_07_08_METHOD_V2_REPLAY_001`  
최종 실행 경로: `experiments/ax_zaije_layer2_kg_openai_methodology_v2_20260708/layer2_kg`

---

## 1. 최종 KG 구축 방식

`자이제_1.xlsx` 데이터는 Layer2 업무 중심 지식그래프로 구축되었다. 최종 KG는 원문 근거를 보존하는 `Source Evidence Graph`와 업무 지식을 표현하는 `Domain Ontology Graph`로 구성된다.

```text
Book
→ Chapter
→ Section
→ SourceChunk
→ EvidenceSpan

DomainOntology
→ DomainProcess
→ DomainTask
→ Artifact / InformationObject / Role / Stakeholder / Principle / Risk / ReviewType
```

LLM은 node와 predicate를 자유롭게 생성하지 않았다. 먼저 설계 단계에서 canonical node inventory와 allowed predicate schema를 구성한 뒤, LLM은 해당 후보 집합 안에서만 원문 근거 기반 triple을 제안하도록 제한하였다. 따라서 이 방법론은 “LLM이 읽고 바로 KG를 생성하는 방식”이 아니라, **사전 설계된 schema 위에서 LLM이 evidence-grounded relation 후보를 채우는 방식**이다.

구축 순서는 크게 세 부분으로 나뉜다. 첫째, 원문을 문서 구조와 문장 단위 evidence로 정규화한다. 둘째, 도메인 업무를 표현할 수 있는 node type, canonical concept, predicate를 먼저 설계한다. 셋째, LLM이 원문 chunk를 읽고 이 설계된 schema 안에서만 triple 후보를 제안하면, validation을 거쳐 최종 KG edge로 반영한다.

---

## 2. 설계서 구성 방식

설계서는 다음 순서로 구성되었다.

| 단계 | 설계 내용 | 구축 방식 |
|---|---|---|
| 1 | 원문 추적 구조 정의 | 원문을 바로 업무 관계로 바꾸지 않고 `Book`, `Chapter`, `Section`, `SourceChunk`, `EvidenceSpan`으로 먼저 분해 |
| 2 | 업무 지식 표현 단위 정의 | 업무 흐름, 업무 활동, 산출물, 정보 객체, 역할, 이해관계자를 표현할 node type 정의 |
| 3 | 자이제 도메인 canonical inventory 구성 | 원문에 반복 등장하고 CQ 답변에 필요한 process, task, artifact, information object를 canonical id로 고정 |
| 4 | allowed predicate와 domain/range 정의 | 업무 관계를 표현할 수 있는 predicate를 제한하고 source/target node type을 지정 |
| 5 | LLM prompt 구조 정의 | LLM에게 자유 생성이 아니라 canonical node와 allowed predicate 중 선택하도록 지시 |
| 6 | validation 기준 정의 | canonical id, predicate, evidence, domain/range, confidence 조건을 통과한 것만 반영 |
| 7 | evaluation 기준 정의 | KG가 질의에 답할 수 있는지 CQ와 구조 품질 지표로 점검 |

핵심은 `L2_ARTIFACT_RFP`, `L2_TASK_CAPTURE_PLANNING`, `CONTAINS` 같은 값이 LLM이 즉석에서 만든 값이 아니라는 점이다. 이들은 설계서 단계에서 만든 controlled vocabulary이며, LLM은 이 vocabulary 안에서 relation 후보를 선택했다.

설계서의 역할은 LLM의 출력을 제한하는 “형식적 약속”을 만드는 것이다. 예를 들어 LLM이 “제안요청서”, “RFP”, “요구제안서”를 매번 다른 node로 만들면 그래프가 분산된다. 그래서 설계서에서 이 표현들을 하나의 canonical node인 `L2_ARTIFACT_RFP`로 묶고, LLM에게는 이 id를 사용하도록 제한하였다.

---

## 3. 원 설계서 기준 Canonical ID 생성 절차

원 설계서의 의도는 canonical ID를 처음부터 전부 사람이 고정하는 것이 아니라, **Task Frame LLM이 추출한 업무 후보와 슬롯 후보를 후처리하여 canonical ID로 확정**하는 것이다.

설계상 절차는 다음과 같다.

```text
OCR 문서
→ 문서 구조 분할
→ Task Frame LLM으로 핵심 업무 단위 추출
→ Task Frame 슬롯에서 Artifact / Role / DecisionPoint / Principle 후보 도출
→ alias 병합 및 canonicalization
→ node type 결정
→ L2_<NODE_TYPE>_<CANONICAL_LABEL> 형식의 canonical ID 부여
→ 사람 검토로 최종 ID와 정의 확정
```

여기서 중요한 점은 별도의 “전체 엔티티 추출 LLM”을 두는 방식이 아니라는 점이다. 설계서에서는 `roles`, `outputs`, `decision_points`, `inputs`, `principles` 같은 Task Frame 슬롯이 사실상 entity 후보를 제공하도록 되어 있다.

| Task Frame 슬롯 | 후처리 node type | 예시 |
|---|---|---|
| `task_name` | `DomainTask` | 수주영업 → `L2_TASK_CAPTURE_PLANNING` |
| `inputs` | `InformationObject` 또는 `Artifact` | 고객 정보 → `L2_INFO_CUSTOMER_INFORMATION` |
| `outputs` | `Artifact` 또는 `StrategyPattern` | Capture Plan → `L2_ARTIFACT_CAPTURE_PLAN` |
| `roles` | `Role` | 제안팀 → `L2_ROLE_PROPOSAL_TEAM` |
| `decision_points` | `DecisionPoint` | Bid/No-Bid Decision → `L2_DECISION_BID_NO_BID` |
| `principles` | `Principle` | 고객 중심 원칙 → `L2_PRINCIPLE_CUSTOMER_FIRST` |
| `next_tasks`, `subtasks` | `DomainTask` | 제안서 기획 → `L2_TASK_PROPOSAL_PLANNING` |

예를 들어 Task Frame LLM이 다음과 같은 후보를 추출했다고 보면, 후처리에서는 이를 하나의 canonical task로 병합한다.

```text
수주영업
Capture Planning
수주계획
영업 정보 관리
```

후처리 결과는 다음과 같이 정리된다.

```text
canonical label = Capture Planning
node type = DomainTask
canonical id = L2_TASK_CAPTURE_PLANNING
aliases = [수주영업, Capture Planning, 수주계획, 영업 정보 관리]
```

`RFP`도 같은 방식이다.

```text
RFP
제안요청서
요구제안서
Request for Proposal
```

후처리 결과는 다음과 같다.

```text
canonical label = RFP
node type = Artifact
canonical id = L2_ARTIFACT_RFP
aliases = [RFP, 제안요청서, 요구제안서, Request for Proposal]
```

따라서 설계상 seed/canonical ID는 LLM이 자유롭게 확정하는 값도 아니고, 사람이 아무 근거 없이 이름 붙이는 값도 아니다. 원문에서 반복적으로 나타나는 업무 표현과 Task Frame 슬롯 후보를 모은 뒤, alias 병합과 node type 판단을 거쳐 만드는 controlled vocabulary이다.

ID 문자열은 다음 규칙으로 생성되도록 정리할 수 있다.

```text
L2_<NODE_TYPE_PREFIX>_<CANONICAL_LABEL_IN_UPPER_SNAKE_CASE>
```

| node type | ID prefix | 예시 |
|---|---|---|
| `DomainTask` | `L2_TASK_` | `L2_TASK_CAPTURE_PLANNING` |
| `Artifact` | `L2_ARTIFACT_` | `L2_ARTIFACT_RFP` |
| `InformationObject` | `L2_INFO_` | `L2_INFO_OFFICIAL_REQUIREMENT` |
| `Role` | `L2_ROLE_` | `L2_ROLE_PROPOSAL_TEAM` |
| `Stakeholder` | `L2_STAKEHOLDER_` | `L2_STAKEHOLDER_CUSTOMER` |
| `DecisionPoint` | `L2_DECISION_` | `L2_DECISION_BID_NO_BID` |
| `StrategyPattern` | `L2_STRATEGY_` | `L2_STRATEGY_CAPTURE_STRATEGY` |

다만 원 설계서에는 `L2_TASK_CAPTURE_PLANNING` 같은 ID 예시와 canonicalization 방향은 제시되어 있지만, 위와 같은 문자열 생성 규칙이 독립된 알고리즘으로 충분히 상세하게 적혀 있지는 않았다. 따라서 본 보고서에서는 논문 작성에 맞게 이 절차를 명시적으로 보완하였다.

---

## 4. 이번 실행에서의 Canonical Node ID 생성 방식

이번 실행에서는 원 설계서의 전체 자동 절차를 처음부터 다시 수행하지 않고, 설계서와 코드에 정의된 seed catalog를 먼저 고정하였다. 즉 Task Frame LLM이 새 canonical ID를 확정한 것이 아니라, 기존 seed inventory를 기준으로 LLM이 task link와 triple 후보를 선택하도록 제한하였다.

Canonical node는 사람이 읽을 수 있고 재현 가능한 stable id로 만들었다.

| 대상 | ID 규칙 | 예시 |
|---|---|---|
| DomainProcess | `L2_PROCESS_<업무흐름>` | `L2_PROCESS_CAPTURE_PLANNING` |
| DomainTask | `L2_TASK_<업무활동>` | `L2_TASK_CAPTURE_PLANNING` |
| Artifact | `L2_ARTIFACT_<산출물명>` | `L2_ARTIFACT_RFP` |
| InformationObject | `L2_INFO_<정보객체명>` | `L2_INFO_OFFICIAL_REQUIREMENT` |
| Role | `L2_ROLE_<역할명>` | `L2_ROLE_PROPOSAL_TEAM` |
| Stakeholder | `L2_STAKEHOLDER_<이해관계자>` | `L2_STAKEHOLDER_CUSTOMER` |

예를 들어 `L2_ARTIFACT_RFP`는 원문에 등장하는 `RFP`, `제안요청서`, `요구제안서`를 하나의 canonical artifact로 묶기 위해 생성되었다. 이때 먼저 개념의 대표 label을 정하고, node type을 `Artifact`로 지정한 뒤, 영어 약어와 한국어 표현을 alias로 붙였다. 한국어, 영어, 약어, 동의어는 `AliasTerm` node로 만들고 `ALIAS_OF` edge로 canonical node에 연결하였다.

이 방식의 목적은 같은 개념이 여러 이름으로 흩어지는 것을 막는 것이다. 예를 들어 LLM이 어떤 문장에서는 “RFP”, 다른 문장에서는 “제안요청서”, 또 다른 문장에서는 “요구제안서”라고 추출하더라도, 최종 KG에서는 모두 같은 canonical node를 가리키게 된다.

Canonical node는 모든 명사를 node로 만든 것이 아니다. 원문에 등장하더라도 업무 흐름, 입력/산출물, 의사결정, 역할, CQ 답변 경로에 기여하지 않는 표현은 canonical inventory로 승격하지 않았다. 반대로 `Capture Plan`, `PMP`, `PDW`, `BCM`처럼 원문에서 업무 산출물로 반복적으로 쓰이고 후속 task와 연결되는 개념은 canonical artifact로 고정하였다.

따라서 이번 실행의 정확한 표현은 다음과 같다.

```text
원 설계: Task Frame LLM 후보 추출 → 슬롯 기반 타입 부여 → alias 병합 → canonical ID 확정
이번 실행: 설계서 기반 seed canonical inventory 고정 → LLM은 해당 inventory 안에서 relation 후보 선택
```

---

## 5. Canonical Inventory 도출 기준

Process는 책의 장/절 구조와 업무 흐름을 기준으로 묶었다.

| Process | 의미 |
|---|---|
| `L2_PROCESS_BID_PROPOSAL_CONTEXT` | 입찰·제안 환경 이해 |
| `L2_PROCESS_PRE_BID_PREPARATION` | 제안참여 전 준비 |
| `L2_PROCESS_CAPTURE_PLANNING` | 수주영업 |
| `L2_PROCESS_EVALUATOR_PERSUASION` | 평가자 공략과 설득 |
| `L2_PROCESS_PROPOSAL_EXECUTION` | 제안서 작성·프레젠테이션 |
| `L2_PROCESS_PROPOSAL_STRATEGY` | 제안전략 개발 |

Task는 단순 섹션 제목이 아니라, 원문에서 반복 가능한 업무 활동, 입력, 산출물, 역할, 의사결정, 후속 업무 연결이 확인되는 단위를 기준으로 구성하였다. 예를 들어 “수주영업 / Capture Planning”은 단순 용어가 아니라 고객 정보, 경쟁사 정보, 자사 솔루션 정보를 입력으로 사용하고 Capture Plan과 수주전략을 산출하는 업무 frame으로 해석되기 때문에 `DomainTask`로 만들었다.

| 항목 | 값 |
|---|---:|
| Canonical Process | 6 |
| Canonical Task | 15 |
| Canonical Entity | 59 |
| 전체 canonical inventory traceability row | 80 |

Entity는 다음 기준으로 포함하였다.

| 기준 | 예시 |
|---|---|
| 설계서에서 우선 인식 대상으로 지정된 산출물 | RFP, Capture Plan, PMP, PDW, BCM |
| Task Frame의 input/output/role slot에 필요한 개념 | 고객 정보, 경쟁사 정보, 제안팀, PM |
| Competency Question 경로 평가에 필요한 정보 객체 | 공식 요구조건, 비공식 요구조건, 고객 니즈 구조 |

Entity 구축은 task slot을 채우는 방식으로 진행하였다. 먼저 각 task에 대해 “무엇을 입력으로 쓰는가”, “무엇을 산출하는가”, “누가 수행하는가”, “어떤 이해관계자를 대상으로 하는가”를 정의했다. 그 결과 input/output에 반복적으로 들어가는 개념은 `Artifact` 또는 `InformationObject`가 되었고, 수행 주체는 `Role`, 대상자는 `Stakeholder`, 업무 원칙은 `Principle`, 위험 요소는 `Risk`로 분류하였다.

예를 들어 `L2_TASK_CAPTURE_PLANNING`은 고객 정보, 경쟁사 정보, 자사 솔루션, 고객 니즈를 입력으로 사용하고, Capture Plan과 수주전략을 산출한다. 따라서 `L2_INFO_CUSTOMER_INFORMATION`, `L2_INFO_COMPETITOR_INFORMATION`, `L2_INFO_OWN_SOLUTION`, `L2_ARTIFACT_CAPTURE_PLAN`, `L2_STRATEGY_CAPTURE_STRATEGY` 같은 canonical node가 필요해진다. 즉 node는 개별 단어를 모은 것이 아니라 task frame의 입력/출력/역할 구조에서 도출되었다.

---

## 6. Predicate 생성 방식

Predicate는 relation과 거의 같은 개념이지만, 더 정확히는 **relation type**이다. 실제 relation instance는 subject-predicate-object 형태의 edge이다.

```text
L2_ARTIFACT_RFP -[CONTAINS]-> L2_INFO_OFFICIAL_REQUIREMENT
```

여기에서 `CONTAINS`는 predicate이고, 전체 triple이 실제 relation instance이다.

Predicate는 업무 지식 표현에 필요한 관계 유형을 먼저 정의하고, 각 predicate마다 허용 가능한 source type과 target type을 지정했다.

| Predicate 유형 | Predicate 예시 | 의미 |
|---|---|---|
| 원문 구조 | `HAS_CHAPTER`, `HAS_SECTION`, `HAS_CHUNK` | 문서 구조 보존 |
| provenance | `EVIDENCED_BY` | node/edge를 원문 근거에 연결 |
| alias 관리 | `ALIAS_OF` | 동의어를 canonical node에 연결 |
| 업무 catalog | `HAS_PROCESS`, `HAS_TASK` | 상위 업무 흐름과 task 연결 |
| 입력/산출물 | `USES_INPUT`, `PRODUCES`, `USED_AS_INPUT_FOR` | task의 입력과 산출물 표현 |
| 업무 순서 | `PRECEDES` | 선후행 업무 관계 |
| 분석/개발 | `ANALYZES`, `DEVELOPS`, `REFINES_INTO` | 업무 활동의 의미 관계 |
| 의사결정 | `HAS_DECISION_POINT`, `DECIDES` | 판단 지점과 결과 |
| 평가/리뷰 | `EVALUATES`, `HAS_REVIEW` | review와 평가 구조 |
| 원칙/리스크 | `HAS_PRINCIPLE`, `MITIGATES`, `INCREASES_RISK` | 원칙 및 위험 관리 |

전체 predicate는 28개이고, 이 중 LLM triple extraction에 허용한 predicate는 23개이다. `EVIDENCED_BY`, `ALIAS_OF`, `HAS_CHAPTER` 같은 구조/provenance predicate는 LLM 추출 대상이 아니라 graph materialization 과정에서 자동 생성된다.

Predicate를 이렇게 제한한 이유는 relation label이 과도하게 늘어나는 것을 막기 위해서이다. 예를 들어 LLM이 자유롭게 relation을 만들면 `includes`, `has`, `contains_info`, `has requirement`, `담고있다`처럼 의미가 비슷한 edge가 여러 이름으로 생성될 수 있다. 본 방법론에서는 이런 관계를 `CONTAINS`로 통일하고, `CONTAINS`가 허용되는 source와 target type을 `Artifact/InformationObject → InformationObject`로 제한하였다.

따라서 `L2_ARTIFACT_RFP -[CONTAINS]-> L2_INFO_OFFICIAL_REQUIREMENT`는 허용되지만, `Role -[CONTAINS]-> Risk`처럼 domain/range가 맞지 않는 edge는 validation에서 제외된다. 이 방식은 KG의 구조 일관성을 유지하기 위한 schema validation 단계이다.

---

## 7. LLM 적용 방식

OpenAI API `gpt-4o-mini`를 사용하여 두 종류의 LLM 출력을 생성하였다.

| 단계 | 입력 단위 | LLM 출력 | 후속 처리 |
|---|---|---|---|
| Task Frame linking | section summary chunk | canonical task와 원문 evidence 연결 후보 | task별 evidence grounding에 반영 |
| Triple extraction | paragraph chunk | canonical subject-predicate-object 후보 | validation 후 KG edge 후보로 반영 |

Task Frame linking 원시 응답에는 `EV_ZAIJE_000000` placeholder evidence id가 반복적으로 포함되어 있었다. v2에서는 원시 응답을 그대로 유지하되, 해당 section summary chunk의 실제 EvidenceSpan id로 deterministic reconciliation을 수행하였다.

| 항목 | 값 |
|---|---:|
| Task Frame links | 111 |
| 원본에서 바로 유효한 evidence link | 0 |
| section chunk 기준으로 reconciliation된 link | 111 |
| unresolved link | 0 |

이 조정은 LLM의 task 판단 자체를 바꾸는 것이 아니라, LLM이 가리키려던 section-level 근거를 실제 존재하는 EvidenceSpan id로 연결하기 위한 후처리이다.

Task Frame linking 단계에서는 LLM이 “이 section이 어떤 canonical task와 관련되는가”를 판단했다. 이때 LLM은 새로운 task를 마음대로 확정하지 않고, 미리 정의된 15개 canonical task 중 관련 task를 고르게 했다. 예를 들어 특정 section이 고객 니즈, RFP, 공식/비공식 요구조건을 설명하면 `L2_TASK_REQUIREMENT_ICEBERG_ANALYSIS`와 연결될 수 있다.

Triple extraction 단계에서는 paragraph chunk를 입력으로 주고, candidate node 목록과 allowed predicate 목록을 함께 제공했다. LLM은 원문에서 확인되는 관계를 `subject_id`, `predicate`, `object_id`, `evidence_ids`, `confidence` 형태로 출력했다. 예를 들어 RFP가 공식 요구조건을 포함한다는 문장에서는 다음과 같은 후보가 생성된다.

```json
{
  "subject_id": "L2_ARTIFACT_RFP",
  "predicate": "CONTAINS",
  "object_id": "L2_INFO_OFFICIAL_REQUIREMENT",
  "evidence_ids": ["EV_ZAIJE_000007", "EV_ZAIJE_000008"],
  "confidence": 1.0
}
```

이 triple은 subject와 object가 canonical inventory에 있고, `CONTAINS`가 allowed predicate이며, evidence id가 실제 존재하고, domain/range도 `Artifact → InformationObject`로 맞기 때문에 KG 후보로 유지된다.

---

## 8. Validation 및 Materialization

LLM 출력은 다음 조건을 통과한 경우에만 KG 후보로 반영하였다.

| 검증 조건 | 내용 |
|---|---|
| canonical subject 검증 | subject id가 canonical node inventory에 존재해야 함 |
| canonical object 검증 | object id가 canonical node inventory에 존재해야 함 |
| predicate 검증 | predicate가 allowed predicate schema에 있어야 함 |
| evidence 검증 | 실제 `EvidenceSpan` id를 참조해야 함 |
| domain/range 검증 | predicate별 허용 source/target node type과 일치해야 함 |
| confidence threshold | confidence 0.60 미만 제외 |
| deduplication | 동일 subject-predicate-object 반복 제거 |

이 과정을 통과한 triple과 source evidence 구조를 결합하여 최종 node와 edge를 생성하였다.

Node 구축은 세 흐름으로 진행하였다. 첫째, 원문 구조에서 `Book`, `Chapter`, `Section`, `SourceChunk`, `EvidenceSpan` node를 자동 생성했다. 둘째, 설계서의 canonical inventory에서 `DomainProcess`, `DomainTask`, `Artifact`, `InformationObject`, `Role` 등 domain node를 생성했다. 셋째, alias dictionary를 바탕으로 `AliasTerm` node를 생성해 canonical node와 연결했다.

Edge 구축도 세 흐름으로 진행하였다. 첫째, 원문 구조 edge인 `HAS_CHAPTER`, `HAS_SECTION`, `HAS_CHUNK`를 생성했다. 둘째, provenance edge인 `EVIDENCED_BY`를 생성해 domain node/edge가 어떤 원문 evidence에 근거하는지 연결했다. 셋째, LLM이 제안하고 validation을 통과한 업무 relation을 `USES_INPUT`, `PRODUCES`, `CONTAINS`, `ANALYZES` 등으로 materialize했다.

Confidence는 사람이 검수한 정답 확률이 아니라 LLM이 triple과 함께 출력한 자기평가 점수이다. 최종 반영에서는 이 값을 0.0-1.0 범위로 보정하고, 0.60 미만은 제외했다. 동일한 subject-predicate-object가 여러 evidence에서 반복 제안되면 하나의 edge로 합치고, evidence_refs를 병합하였다.

---

## 9. 최종 결과

| 항목 | 값 |
|---|---:|
| 유효 문장 행 | 1,366 |
| SourceChunk | 166 |
| EvidenceSpan | 1,366 |
| Task Frame LLM rows | 51 |
| Triple LLM rows | 110 |
| LLM accepted triples | 188 |
| LLM rejected triples | 100 |
| Raw triples | 209 |
| Schema-validated triples | 103 |
| Graph nodes | 1,869 |
| Graph edges | 2,280 |
| Review queue rows | 21 |

품질 지표는 다음과 같다.

| 지표 | 값 |
|---|---:|
| `node_grounded_rate_domain_only` | 1.0000 |
| `edge_grounded_rate` | 1.0000 |
| `predicate_valid_rate` | 1.0000 |
| `task_orphan_rate` | 0.0000 |
| `duplicate_alias_rate` | 0.0796 |
| `case_leakage_rate` | 0.0000 |
| `cq_pass_rate` | 0.0000 |

CQ exact path 평가는 0/7이다. 이는 KG가 비어 있다는 의미가 아니라, 설계서에 정의한 CQ 경로를 exact path로 모두 만족할 만큼 `USED_AS_INPUT_FOR`, `MITIGATES`, `MAY_RESULT_IN`, `REFINES_INTO` 등의 경로가 충분히 생성되지 않았다는 의미이다.

---

## 10. 최종 Edge Predicate 분포

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

`EVIDENCED_BY`가 많은 이유는 LLM이 업무 relation으로 많이 추출했기 때문이 아니라, 거의 모든 node/edge를 원문 근거 EvidenceSpan과 연결했기 때문이다. 이는 provenance 구조이다.

---

## 11. 구축 절차 상세 설명

전체 구축 절차는 “원문 근거화 → schema 설계 → LLM 추출 → validation → graph materialization”의 순서로 진행되었다.

첫 번째 단계에서는 엑셀의 문장 행을 그대로 업무 relation으로 변환하지 않았다. 문장마다 chapter, section, page, source row, text span을 유지하여 `EvidenceSpan`으로 만들었다. 이렇게 한 이유는 나중에 어떤 node나 edge가 생기더라도 “이 지식은 원문 어디에서 왔는가”를 추적하기 위해서이다.

두 번째 단계에서는 도메인 schema를 먼저 설계했다. 이 단계에서 `DomainTask`, `Artifact`, `InformationObject`, `Role`, `Stakeholder` 같은 node type을 정의하고, 자이제 도메인에 필요한 canonical task와 entity를 만들었다. 이 작업은 LLM이 문장을 읽고 임의의 node를 생성하기 전에, 사용할 수 있는 개념 목록을 정하는 단계이다.

세 번째 단계에서는 predicate schema를 만들었다. `USES_INPUT`, `PRODUCES`, `CONTAINS`, `ANALYZES`, `HAS_REVIEW`처럼 업무 관계를 표현할 수 있는 relation type을 미리 정하고, 각 predicate가 어떤 node type 사이에서만 쓰일 수 있는지 domain/range를 정의했다. 이 때문에 LLM이 의미상 비슷한 관계를 여러 이름으로 만드는 문제가 줄어든다.

네 번째 단계에서는 LLM을 적용했다. LLM은 먼저 section summary chunk를 읽고 어떤 canonical task와 관련되는지 연결했다. 이후 paragraph chunk를 읽고 canonical node와 allowed predicate를 사용해 triple 후보를 생성했다. 이때 evidence id를 반드시 함께 출력하도록 하여, 근거 없는 relation은 최종 반영될 수 없게 했다.

다섯 번째 단계에서는 validation을 수행했다. LLM이 제안한 triple이라도 subject나 object가 canonical inventory에 없으면 제외했다. predicate가 allowed schema에 없거나, domain/range가 맞지 않거나, evidence id가 실제 존재하지 않거나, confidence가 너무 낮으면 제외했다. 같은 SPO가 반복되면 하나로 병합했다.

마지막 단계에서는 검증된 triple과 원문 provenance 구조를 결합해 KG를 만들었다. 이때 업무 relation뿐 아니라 `EVIDENCED_BY` edge를 함께 생성하여 graph element가 원문 evidence로 되돌아갈 수 있게 했다. 결과적으로 KG는 단순 relation 모음이 아니라, 원문 근거와 schema 제약을 함께 가진 Layer2 업무 지식 구조가 된다.

---

## 12. 논문 방법론 문장 초안

```text
본 연구는 LLM을 지식그래프 schema author로 자유롭게 사용하지 않고, schema-constrained evidence-grounded extractor로 사용하였다. 원 설계에서는 Task Frame LLM이 문서에서 핵심 업무 단위와 input/output/role/decision/principle 슬롯 후보를 추출하고, alias 병합 및 slot-based typing을 통해 L2_<NODE_TYPE>_<CANONICAL_LABEL> 형식의 canonical ID를 부여하도록 하였다. 이번 실행에서는 사람 검수 전 안정성을 위해 설계서 기반 seed canonical inventory를 먼저 고정하고, OpenAI gpt-4o-mini가 각 chunk에서 canonical subject, allowed predicate, canonical object, evidence id를 포함한 triple 후보를 생성하도록 제한하였다. 최종 KG 반영은 canonical id validation, predicate validation, evidence validation, domain/range validation, confidence threshold, duplicate SPO 제거를 통과한 경우로 한정하였다.
```

현재 결과는 사람 검수 전 Layer2 KG bootstrap이다. 구조적 grounding, predicate validity, task orphan 측면에서는 자동 검증을 통과했지만, CQ exact path 기준은 아직 낮으므로 다음 단계에서는 CQ-aware prompt/rule 보강과 사람 검수가 필요하다.
