# 온톨로지-LLM 공동연구 데이터 이해 및 연구 계획

작성일: 2026-06-15  
대상 경로: `/home/minjoo/AX_서울펠로우/handoff-hanyang`

## 1. 연구의 핵심 문제

AX 데이터 패키지는 단순한 JSON 묶음이 아니라, 기업 업무를 설명하는 3개 표준 축을 하나의 직무 에이전트 운영 온톨로지(JAO)로 정규화한 연구 출발점이다.

- NCS: 사람이 갖추어야 할 직무 역량과 능력단위
- PCF: 기업이 수행하는 업무 프로세스와 KPI
- O*NET: 실제 직업별 세부 과업, 지식, 스킬, 능력
- JAO: 위 표준을 Agent, Action, Task, Process, Tool, Artifact, Regulation, Metric 등으로 통합한 운영 온톨로지
- Mapping/Graph: 표준 간 연결 및 지식그래프 엣지

따라서 연구 질문은 다음처럼 잡는 것이 가장 자연스럽다.

1. 표준 직무 데이터와 전문가 문서가 주어졌을 때, LLM은 JAO 스키마에 맞는 업무 온톨로지를 얼마나 정확하게 자동 생성할 수 있는가?
2. 생성된 온톨로지를 RAG/GraphRAG/Agent Harness에 결합하면 일반 RAG보다 업무 성공률, 규정 준수율, 설명 가능성이 실제로 좋아지는가?
3. 수주/제안 도메인에서 검증한 파이프라인이 법인파산, 투자, 구매, HR, 재무 등 타 직무로 얼마나 적은 비용으로 복제되는가?

## 2. 데이터 구조와 실제 예시

### 2.1 전체 규모

로컬 파일을 직접 파싱해 확인한 주요 규모는 다음과 같다.

| 구분 | 파일 | 건수 | 연구상 의미 |
|---|---:|---:|---|
| NCS 능력단위 | `01_ncs/ncs_unit.json` | 28,666 | 직무 역량/작업 단위의 원천 골드 후보 |
| PCF 프로세스 | `02_pcf/pcf_data.json` | 2,017 | 기업 프로세스 트리 |
| PCF 메트릭 | `02_pcf/pcf_metrics.json` | 3,284 | H2/H3 평가 지표 후보 |
| O*NET 직업 | `03_onet/onet_occupations_full.json` | 1,016 | 직업별 task/skill/knowledge 보강 |
| JAO Task | `04_jao/instances/Task.json` | 18,977 | NCS + O*NET 과업 통합 학습 데이터 |
| JAO Process | `04_jao/instances/Process.json` | 2,019 | PCF 기반 프로세스 노드 |
| JAO Concept | `04_jao/instances/Concept.json` | 1,711 | NCS 분류 + O*NET 직업 개념 |
| JAO Agent/Action | `04_jao/instances/Agent.json`, `Action.json` | 10 / 51 | H2 에이전트 실험 베이스라인 |
| MappingEdge | `05_mappings/mapping_edges_all.json` | 5,055 | 자동 매핑, 검수 전 데이터 |
| Graph Edge | `05_mappings/graph_edges_all.json` | 27,962 | Neo4j/GraphRAG 적재용 전체 그래프 |
| 수주 선별본 | `06_suju_focus/*` | 270 | 1차 실증 도메인 |

위 데이터가 실제로 어떤 내용을 담고 있는지 대표 예시를 하나씩 붙이면 다음과 같다.

| 구분 | 실제 예시 | 이 예시가 보여주는 것 |
|---|---|---|
| NCS 능력단위 | `1001010105_20v2` / `영업 제안` / 수준 3 | “계약 체결을 위하여 고객 조건에 맞는 상품을 제안하는 능력”처럼 직무 역량 단위가 정의됨 |
| PCF 프로세스 | `hid=3.5` / `영업 계획 개발·관리` | 기업 업무 프로세스 트리에서 영업 계획이 `3.0 Market and Sell` 하위에 위치함 |
| PCF 메트릭 | `metricId=109038` / `전사 FTE 대비 영업·마케팅 FTE 비율` | 프로세스 성과를 KPI로 측정할 수 있음 |
| O*NET 직업 | `41-4011.00` / Technical and Scientific Sales Representatives | 기술/과학 제품 영업 직업의 실제 task, skill, knowledge가 포함됨 |
| JAO Task | `jao://Task/ncs/02.5` / `기술영업 전략수립` | NCS 능력단위가 JAO Task 형태로 정규화되고 `Concept/ncs/20010501`에 연결됨 |
| JAO Process | `jao://Process/pcf/pcf-3.0` / `제품·서비스 마케팅 및 판매` | PCF 프로세스가 JAO Process URI로 정규화됨 |
| JAO Concept | `jao://Concept/ncs/20010501` / `IT기술영업` | NCS 세분류가 SKOS식 Concept로 정규화됨 |
| JAO Agent/Action | `sales-b2b` / `draft_proposal` | 에이전트가 호출 가능한 Action, 입력, 출력, 위험도, 승인자를 가짐 |
| MappingEdge | `Concept/onet/41-9099.00 mapsTo Process/pcf/pcf-3.5.7` | 서로 다른 표준 간 의미 연결 후보가 confidence와 evidence를 가짐 |
| Graph Edge | `Action/analyze_campaign uses Tool/powerbi` | 전체 지식그래프에서 구조/실행 관계를 직접 탐색할 수 있음 |
| 수주 선별본 | `20010501-05 수주전략수립`, `sales-b2b` | 1차 실증 도메인에 필요한 NCS, PCF, Agent가 미리 선별되어 있음 |

대표 JSON 예시는 아래와 같다.

```json
{
  "NCS_Unit": {
    "NCS_CL_CD": "1001010105_20v2",
    "COMPE_UNIT_NAME": "영업 제안",
    "COMPE_UNIT_LEVEL": 3,
    "COMPE_UNIT_DEF": "영업 제안이란 계약 체결을 위하여 고객이 요구하는 조건에 맞는 상품을 제안하는 능력이다."
  },
  "PCF_Process": {
    "hid": "3.5",
    "nameKo": "영업 계획 개발·관리",
    "nameEn": "Develop and manage sales plans",
    "level": 2,
    "parent": "3.0",
    "hasMetrics": true
  },
  "PCF_Metric": {
    "metricId": 109038,
    "hid": "3.0",
    "metricNameKo": "전사 FTE 대비 영업·마케팅 FTE 비율",
    "formulaKo": "((영업 기능 수행 FTE 수 + 마케팅 기능 수행 FTE 수) / 사업체 FTE 수) * 100.0",
    "unitsKo": "퍼센트"
  },
  "ONET_Occupation": {
    "socCode": "41-4011.00",
    "title": "Sales Representatives, Wholesale and Manufacturing, Technical and Scientific Products",
    "exampleTasks": [
      "Negotiate prices or terms of sales or service agreements.",
      "Prepare and submit sales contracts for orders.",
      "Quote prices, credit terms, or other bid specifications."
    ],
    "exampleSkills": ["Persuasion", "Negotiation", "Service Orientation"]
  }
}
```

JAO와 그래프 계열 대표 예시는 다음과 같다.

```json
{
  "JAO_Task": {
    "$id": "jao://Task/ncs/02.5",
    "class": "Task",
    "namespace": "ncs",
    "label": {"ko": "기술영업 전략수립"},
    "levelL": 6,
    "taskType": "NCS-Element",
    "requires": ["jao://Concept/ncs/20010501"]
  },
  "JAO_Process": {
    "$id": "jao://Process/pcf/pcf-3.0",
    "class": "Process",
    "label": {
      "ko": "제품·서비스 마케팅 및 판매",
      "en": "Market and Sell Products and Services"
    },
    "hid": "3.0",
    "level": 1,
    "hasMetrics": true
  },
  "JAO_Concept": {
    "$id": "jao://Concept/ncs/20010501",
    "class": "Concept",
    "label": {"ko": "IT기술영업"},
    "broader": ["jao://Concept/ncs/200105"]
  },
  "JAO_Agent_Action": {
    "agent": "jao://Agent/agent/sales-b2b",
    "action": "jao://Action/agent/draft_proposal",
    "actionLabel": "제안서 작성",
    "inputs": ["accountId", "scope", "budget"],
    "outputs": ["proposalDoc"],
    "riskLevel": "medium",
    "approvers": ["sales-mgr"]
  },
  "MappingEdge": {
    "from": "jao://Concept/onet/41-9099.00",
    "predicate": "mapsTo",
    "to": "jao://Process/pcf/pcf-3.5.7",
    "confidence": 0.1674,
    "mappingType": "related"
  },
  "GraphEdge": {
    "from": "jao://Action/agent/analyze_campaign",
    "predicate": "uses",
    "to": "jao://Tool/tool/powerbi",
    "confidence": 0.9
  },
  "Suju_Focus": {
    "ncsUnit": "20010501-05 수주전략수립",
    "pcfRoot": "3.0 Market and Sell Products and Services",
    "agent": "jao://Agent/agent/sales-b2b"
  }
}
```

#### PCF 프로세스를 쉽게 이해하는 방법

PCF(Process Classification Framework)는 “사람이 무엇을 할 수 있는가”를 말하는 NCS와 다르게, “회사 안에서 어떤 업무가 어떤 순서와 범주로 존재하는가”를 정리한 기업 업무 지도다. 따라서 PCF의 한 노드는 직무명이 아니라 업무 프로세스명이다.

예를 들어 수주/영업 도메인을 보면 PCF는 다음처럼 내려간다.

| PCF hid | level | 실제 명칭 | parent | 쉽게 말하면 |
|---|---:|---|---|---|
| `3.0` | 1 | 제품·서비스 마케팅 및 판매 | 없음 | 회사의 마케팅/영업 전체 영역 |
| `3.1` | 2 | 시장, 고객 및 역량 이해 | `3.0` | 팔기 전에 시장과 고객을 이해하는 큰 업무 묶음 |
| `3.1.1` | 3 | 고객·시장 인텔리전스 분석 수행 | `3.1` | 시장/고객 정보를 분석하는 프로세스 |
| `3.1.1.1` | 4 | 고객·시장 조사 수행 | `3.1.1` | 실제 고객/시장 조사를 수행하는 활동 |
| `3.1.1.1.2` | 5 | 고객 구매 행동 예측 | `3.1.1.1` | 고객 구매 행동을 예측하는 더 세부 업무 |
| `3.5` | 2 | 영업 계획 개발·관리 | `3.0` | 영업 계획과 영업 운영을 관리하는 큰 업무 묶음 |
| `3.5.6` | 3 | 오프라인 매장 영업 수행 | `3.5` | 매장 기반 판매 수행 |
| `3.5.7` | 3 | 현장 영업 수행 | `3.5` | 고객 현장/외부 장소에서의 영업 수행 |

핵심은 `hid`가 계층 주소라는 점이다. `3.5.7`은 독립적인 임의 번호가 아니라, `3.0 > 3.5 > 3.5.7`에 위치한 업무라는 뜻이다. 이 구조가 있기 때문에 GraphRAG에서는 “현장 영업 수행”을 검색했을 때 상위 업무인 “영업 계획 개발·관리”와 “제품·서비스 마케팅 및 판매”까지 같이 가져올 수 있다.

PCF를 연구에 쓰는 이유는 다음과 같다.

| 질문 | PCF가 주는 답 |
|---|---|
| 이 업무가 회사 프로세스상 어디에 속하는가? | `3.0 Market and Sell`, `3.5 Develop and manage sales plans` 같은 위치를 제공 |
| 이 업무의 상위/하위 업무는 무엇인가? | `parent`, `hid` 계층으로 추적 가능 |
| 이 업무를 어떤 KPI로 평가할 수 있는가? | PCF Metric이 연결됨. 예: 영업·마케팅 FTE 비율, B2B 고객 이탈률 |
| 산업별로 같은 업무가 어떻게 달라지는가? | banking, retail, education 등 산업별 PCF 파일과 비교 가능 |

#### 각 데이터 구분의 의미와 연결 관계

아래 표는 앞의 대표 예시들을 “서로 어떻게 연결되는지”까지 함께 정리한 것이다.

| 구분 | 더 자세한 의미 | 수주/제안 예시 | 연결되는 데이터 |
|---|---|---|---|
| NCS 능력단위 | 사람이 특정 직무를 수행하기 위해 갖춰야 할 능력 단위다. “무엇을 할 수 있어야 하는가”에 초점이 있다. | `영업 제안`: 고객 조건에 맞는 상품을 제안하는 능력 | JAO Task로 변환되거나, JAO Concept인 `일반영업`, `IT기술영업`에 연결됨 |
| PCF 프로세스 | 회사의 업무 흐름과 업무 범주다. “회사가 어떤 프로세스를 수행하는가”에 초점이 있다. | `3.5 영업 계획 개발·관리`, `3.5.7 현장 영업 수행` | JAO Process로 정규화되고, NCS/O*NET과 MappingEdge로 연결될 수 있음 |
| PCF 메트릭 | PCF 프로세스의 성과를 측정하는 KPI다. “업무가 잘 되었는가”를 평가한다. | `전사 FTE 대비 영업·마케팅 FTE 비율`, `B2B 고객 1년 이탈률` | JAO Metric으로 변환되고, 특정 JAO Process를 측정하는 지표가 됨 |
| O*NET 직업 | 미국 직업 단위 데이터다. 직업별 실제 과업, 스킬, 지식, 능력이 들어 있다. | 기술영업 직업의 `Negotiate prices...`, `Prepare and submit sales contracts...` | JAO Concept 또는 Task로 변환되어 NCS/PCF의 빈 부분을 보강 |
| JAO Task | NCS 능력단위나 O*NET task를 JAO 스키마로 통일한 작업 노드다. | `jao://Task/ncs/02.5 기술영업 전략수립` | `requires`로 JAO Concept에 연결되고, 향후 `enables`로 PCF Process에 연결 가능 |
| JAO Process | PCF 프로세스를 JAO URI 체계로 통일한 노드다. | `jao://Process/pcf/pcf-3.0` | `partOf`로 PCF 상하위 구조를 만들고, Metric/Task/MappingEdge와 연결 |
| JAO Concept | NCS 세분류나 O*NET 직업을 개념 노드로 정규화한 것이다. | `jao://Concept/ncs/20010501 IT기술영업` | Task가 요구하는 직무 개념이 되고, broader/narrower로 직무 계층 구성 |
| JAO Agent/Action | Agent는 직무 수행 주체, Action은 Agent가 호출 가능한 사전 정의 행동이다. | `sales-b2b` Agent가 `draft_proposal` Action 호출 | Tool, Artifact, Regulation, Policy와 연결되어 안전한 실행 harness 구성 |
| MappingEdge | 서로 다른 표준 사이의 의미 연결 후보다. | O*NET 영업 직업 `mapsTo` PCF 현장 영업 프로세스 | 자동 생성이라 confidence/evidence 기반으로 검수 필요 |
| Graph Edge | 모든 구조/실행/매핑 관계를 그래프 엣지로 모은 것이다. | `Action uses Tool`, `Process partOf Process`, `Task requires Concept` | Neo4j/GraphRAG에서 multi-hop retrieval과 근거 추적에 사용 |
| 수주 선별본 | 전체 데이터 중 1차 연구 대상인 수주/제안 관련 데이터만 잘라둔 subset이다. | `수주전략수립`, `기술영업 제안 작업`, `sales-b2b` | H1/H2 실험의 시작점. 이후 타 도메인으로 H3 복제 |

#### 하나의 수주/제안 업무로 연결해 보기

업무 상황을 하나 가정해 보면 각 데이터는 다음처럼 연결된다.

> “A사 RFP를 보고 고객 요구사항과 경쟁사를 분석한 뒤, 제안 전략을 세우고 제안서 초안을 작성한다.”

이 업무를 데이터별로 해석하면 다음과 같다.

| 단계 | 데이터에서 찾는 노드 | 역할 |
|---|---|---|
| 1. 직무 영역 파악 | `jao://Concept/ncs/20010501 IT기술영업` | 이 업무가 IT기술영업 직무에 속함을 알려줌 |
| 2. 필요한 능력 파악 | `20010501-05 수주전략수립`, `20010501-06 기술영업 제안 작업` | 사람이 수행해야 할 능력/작업 단위를 제공 |
| 3. 회사 프로세스 위치 파악 | `jao://Process/pcf/pcf-3.0`, `pcf-3.5` | 이 업무가 회사의 Market & Sell / Sales planning 프로세스에 속함을 알려줌 |
| 4. 실제 세부 과업 보강 | O*NET `Negotiate prices...`, `Prepare and submit sales contracts...` | NCS보다 더 세부적인 행동 문장을 제공 |
| 5. 실행 Agent 선택 | `jao://Agent/agent/sales-b2b` | 이 업무를 수행할 에이전트 persona 선택 |
| 6. 실행 Action 선택 | `jao://Action/agent/draft_proposal` | 제안서 초안 작성이라는 허용된 행동 선택 |
| 7. 산출물 구조 선택 | `jao://Artifact/art/proposal-rfp` | 제안서가 가져야 할 섹션 구조 제공 |
| 8. 도구 선택 | `jao://Tool/tool/openai-api`, `jao://Tool/tool/figma` | 문서 생성/시각화 도구 선택 |
| 9. 안전 검증 | `riskLevel=medium`, `approvers=["sales-mgr"]` | 가격 한도와 관리자 검토가 필요함을 강제 |
| 10. 근거 추적 | Graph Edge와 MappingEdge | 왜 이 노드/Action을 선택했는지 graph path로 설명 |

이를 그래프 형태로 단순화하면 다음과 같다.

```text
Concept: IT기술영업
  <-requires-
Task: 수주전략수립 / 기술영업 제안 작업
  -mapsTo/enables 후보->
Process: 3.0 Market and Sell
  <-partOf-
Process: 3.5 영업 계획 개발·관리

Agent: sales-b2b
  -actions->
Action: draft_proposal
  -uses->
Tool: openai-api, figma
  -produces->
Artifact: proposal-rfp
  -requiresApproval->
Role/User: sales-mgr
```

이 연결이 중요한 이유는 일반 RAG와 차이가 여기서 생기기 때문이다. 일반 RAG는 관련 문서를 찾아 제안서를 써줄 수는 있지만, `draft_proposal`이 허용된 Action인지, 어떤 Artifact 구조를 따라야 하는지, 어떤 승인자가 필요한지, 어떤 표준 직무/프로세스에 근거하는지까지 강제하지는 못한다. JAO/PCF/NCS/O*NET을 연결하면 “문서 생성”이 아니라 “검증 가능한 업무 실행”으로 바뀐다.

### 2.2 NCS 예시: 역량 관점

수주/제안 도메인의 핵심 NCS 세분류는 `10010101 일반영업`이다. 실제 선별 데이터에는 다음 능력단위가 포함된다.

| NCS 세분류 | 능력단위 | 수준 | 의미 |
|---|---|---:|---|
| 일반영업 | 영업 전략수립 | 5 | 영업 환경분석을 바탕으로 목표와 실행계획을 세움 |
| 일반영업 | 영업 고객발굴 | 3 | 고객 상담 계획과 채널을 통해 고객을 발굴 |
| 일반영업 | 영업 제안 | 3 | 고객 조건에 맞는 상품/서비스를 제안 |
| 일반영업 | 영업 계약체결관리 | 3 | 협상을 통해 계약 체결 과정을 관리 |
| 일반영업 | 영업 계약이행관리 | 3 | 계약 사항이 이행되도록 관리 |
| 일반영업 | 영업 성과관리 | 5 | 영업 실적을 평가하고 관리 |

연구에서 이 데이터는 “업무 수행 능력의 표준 좌표계”로 쓰인다. 예를 들어 전문가 문서에서 “고객 요구사항을 분석해 제안 전략을 수립한다”는 문장이 나오면, LLM은 이를 `영업 제안`, `영업 전략수립`, `고객발굴` 중 어디에 연결해야 하는지 판단해야 한다.

### 2.3 PCF 예시: 기업 프로세스 관점

수주 도메인의 PCF 축은 `3.0 Market and Sell Products and Services`이다.

예시 계층:

| hid | level | 프로세스 |
|---|---:|---|
| 3.0 | 1 | 제품·서비스 마케팅 및 판매 |
| 3.1 | 2 | 시장, 고객 및 역량 이해 |
| 3.1.1 | 3 | 고객·시장 인텔리전스 분석 수행 |
| 3.1.1.1 | 4 | 고객·시장 조사 수행 |
| 3.1.1.1.2 | 5 | 고객 구매 행동 예측 |

NCS가 “사람이 무엇을 할 수 있어야 하는가”라면, PCF는 “기업 프로세스상 어느 단계인가”를 제공한다. 연구에서는 NCS `영업 고객발굴`이나 O*NET `Negotiate prices or terms of sales agreements` 같은 과업이 PCF 3.x 프로세스의 어느 노드에 매핑되는지 검증한다.

주의: PCF 원문 및 PCF 유래 인스턴스는 APQC 라이선스 범위 안에서 연구 내부용으로 다루고, 논문/공개 데이터에는 원문 재배포를 피해야 한다.

### 2.4 O*NET 예시: 구체 과업 관점

O*NET은 NCS보다 실제 task 문장이 세분화되어 있다. 수주/영업 관련 예시는 다음과 같다.

- `Negotiate prices or terms of sales or service agreements.`
- `Resolve customer complaints regarding sales and service.`
- `Plan and direct staffing, training, and performance evaluations to develop and control sales and service programs.`

이 데이터는 한국 NCS의 추상적 능력단위를 실제 행위 문장으로 보강하는 데 유용하다. 특히 에이전트가 실행할 `Action`을 설계할 때 O*NET task가 세부 기능 후보가 된다.

### 2.5 JAO 예시: Agent Harness의 운영 스키마

수주 도메인 예시인 `B2B 영업 에이전트`는 다음과 같은 실행 구조를 갖는다.

| 구성 | 실제 예시 |
|---|---|
| Agent | `sales-b2b`, B2B 영업 에이전트 |
| Actions | `score_lead`, `brief_account`, `draft_proposal`, `forecast_pipeline`, `schedule_meeting` |
| Tools | Salesforce, LinkedIn Sales, Slack, Figma, DocuSign, Zoom |
| Artifacts | sales deck, RFP proposal, sales contract |
| Regulations | 공정거래, 하도급, 소비자 관련 규정 |
| Intervention mode | checkpoint |

Action 예시:

| Action | category | risk | 의미 |
|---|---|---|---|
| `score_lead` | `sales.read` | low | 리드 점수 계산 |
| `brief_account` | `sales.generate` | low | 계정 브리핑 생성 |
| `draft_proposal` | `sales.generate` | medium | 제안서 초안 작성 |
| `schedule_meeting` | `sales.write` | low | 미팅 일정 생성 |

이 구조는 H2 실험의 핵심이다. 일반 RAG는 문서를 검색해 답변만 생성하지만, JAO 기반 Agent Harness는 “어떤 Action을 실행할 수 있는지, 어떤 Tool을 써야 하는지, 어떤 산출물을 만들어야 하는지, 어느 위험도에서 사람 승인이 필요한지”까지 제약한다.

### 2.6 Mapping/Graph 예시: 연구 문제가 이미 들어 있는 데이터

`mapping_edges_all.json`의 predicate 분포는 다음과 같다.

| predicate | 건수 | 해석 |
|---|---:|---|
| `governedBy` | 3,842 | 직무/개념/태스크와 법령 연결 |
| `mapsTo` | 817 | NCS/O*NET/PCF 간 의미 매핑 |
| `related` | 396 | 가이드라인 등 관련 문서 연결 |

중요한 점은 자동 매핑이 검수 전이라는 것이다. 예를 들어 일부 `mapsTo`는 confidence가 0.1대에 불과하고, 키워드만 맞아 실제 의미는 어긋날 수 있다. 따라서 이 데이터는 단순 입력 데이터가 아니라 “LLM+온톨로지 기반 검증/정제” 연구의 평가 대상이다.

## 3. 관련 논문 흐름과 본 연구에 주는 시사점

### 3.1 RAG와 자기검증

- RAG는 비모수 메모리와 생성 모델을 결합해 지식집약 QA에서 성능과 사실성을 높이는 방향을 제시했다. 본 연구의 text-only baseline으로 적합하다.  
  Source: Lewis et al., NeurIPS 2020, https://proceedings.neurips.cc/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html
- Self-RAG는 검색 필요성, 검색 결과의 관련성, 생성 품질을 모델이 반성하도록 설계한다. H2에서 환각률을 낮추는 critique 모듈의 근거가 된다.  
  Source: Asai et al., ICLR 2024, https://openreview.net/forum?id=hSyW5go0v8

### 3.2 GraphRAG, KG+LLM, 반구조 검색

- QA-GNN은 LM과 KG를 결합해 관련 지식 식별과 그래프 추론을 함께 수행한다. JAO graph를 단순 검색 대상이 아니라 reasoning substrate로 쓰는 근거가 된다.  
  Source: Yasunaga et al., NAACL 2021, https://aclanthology.org/2021.naacl-main.45/
- StructGPT는 표, KG, DB 등 구조화 데이터에 대해 읽기-추론 반복 프레임워크를 제안한다. JAO/Neo4j를 LLM tool로 읽고 reasoning하는 설계와 직접 맞다.  
  Source: Jiang et al., EMNLP 2023, https://aclanthology.org/2023.emnlp-main.574/
- STaRK는 텍스트와 관계형 지식이 섞인 반구조 KB 검색 벤치마크를 제안한다. 본 과제도 NCS/PCF/O*NET 텍스트와 JAO 관계가 섞여 있으므로 H2 평가 설계의 좋은 모델이다.  
  Source: Wu et al., NeurIPS 2024 Datasets & Benchmarks, https://openreview.net/forum?id=QSS5cGmKb1
- HippoRAG는 LLM, KG, Personalized PageRank를 결합한 장기 기억형 RAG를 제안한다. JAO graph의 multi-hop retrieval 설계에 참고할 수 있다.  
  Source: Gutiérrez et al., NeurIPS 2024, https://arxiv.org/abs/2405.14831
- GraphRAG는 private corpus에서 추출한 KG와 community summary를 이용해 전역 질문에 대응하는 방향을 제시한다. 기업 문서/전문가 자료가 추가될 때 baseline으로 쓸 수 있다.  
  Source: Edge et al., 2024 preprint, https://arxiv.org/abs/2404.16130

### 3.3 LLM 기반 KG/온톨로지 구축

- Extract-Define-Canonicalize(EDC)는 대규모 schema를 prompt에 다 넣지 않고, 추출-정의-정규화 단계로 KG를 구성한다. H1 자동 온톨로지 구축 파이프라인의 가장 직접적인 방법론 후보이다.  
  Source: Zhang and Soh, EMNLP 2024, https://aclanthology.org/2024.emnlp-main.548/
- LLMs4OL은 LLM을 term typing, taxonomy discovery, non-taxonomic relation extraction에 평가한다. JAO의 Concept/Task/Process/MappingEdge 생성 평가 축과 맞다.  
  Source: Babaei et al., ISWC 2023, https://iswc2023.semanticweb.org/wp-content/uploads/2023/11/142650396.pdf
- LLM 기반 ontology engineering 문헌 리뷰는 LLM이 온톨로지 요구사항, 구현, 유지보수에 쓰일 수 있으나 평가와 전문가 검증이 중요하다는 점을 정리한다.  
  Source: Semantic Web Journal review, https://www.semantic-web-journal.net/content/large-language-models-ontology-engineering-systematic-literature-review

### 3.4 Agent/tool-use와 운영 harness

- ReAct는 reasoning trace와 action을 교대로 생성해 외부 환경/API와 상호작용한다. JAO의 Agent-Action-Tool 구조를 실행하는 기본 패턴으로 적합하다.  
  Source: Yao et al., ICLR 2023, https://openreview.net/forum?id=WE_vluYUL-X
- Toolformer는 모델이 API 호출 여부와 인자를 학습하는 방향을 제시한다. JAO Action schema를 tool-call training data로 변환하는 연구 아이디어와 연결된다.  
  Source: Schick et al., NeurIPS 2023, https://openreview.net/forum?id=Yacmpz84TH
- Reflexion은 trial feedback을 언어적 메모리로 남겨 agent 성능을 개선한다. H2 실험에서 실패 사례를 intervention-history로 남기는 방식과 맞다.  
  Source: Shinn et al., NeurIPS 2023, https://openreview.net/forum?id=vAElhFcKW6
- DSPy는 프롬프트 체인을 metric-driven pipeline으로 최적화한다. H1/H2 파이프라인의 prompt, retriever, verifier를 자동 최적화하는 구현 프레임으로 적합하다.  
  Source: Khattab et al., ICLR 2024, https://openreview.net/forum?id=sY5N0zY5Od

## 4. 권장 연구 주제

가장 강한 논문화 방향은 다음 제목으로 잡는 것이다.

> Schema-Grounded Job Ontology Construction and Ontology-Constrained Agent Harness for Enterprise Workflows

국문으로는 다음과 같다.

> 직무 표준 기반 업무 온톨로지 자동 구축과 온톨로지 제약형 기업용 AI 에이전트 운영 프레임워크

핵심 기여는 세 가지로 잡는다.

1. H1: NCS/PCF/O*NET/전문가 문서를 JAO 스키마로 자동 변환하는 schema-grounded ontology construction pipeline
2. H2: JAO graph를 사용하는 ontology-constrained RAG/Agent Harness가 일반 RAG보다 성공률, 준수율, 추적성을 높인다는 정량 검증
3. H3: 수주/제안에서 만든 파이프라인을 법인파산, 투자, 구매, HR, 재무 등으로 복제하는 transfer protocol

## 5. 구체 연구 설계

### 5.1 H1: 업무 온톨로지 자동 구축

목표: 전문가 자료와 직무 표준을 입력하면 JAO 스키마에 맞는 노드와 엣지를 자동 생성한다.

입력:

- 표준 좌표계: NCS, PCF, O*NET
- 참조 스키마: `04_jao/schemas/*.json`, `jao-spec.md`
- 베이스라인 인스턴스: `04_jao/instances/*.json`
- 1차 도메인: `06_suju_focus`
- 추가 예정: 쉬플리 방법론, 산출물 양식, NCS 학습모듈, 강의 STT

출력:

- `Task`, `Process`, `Concept`, `Action`, `Artifact`, `Regulation`, `Policy`, `Metric`
- `MappingEdge`: `requires`, `mapsTo`, `governedBy`, `uses`, `produces`, `enforcedBy`

비교 방법:

| 방법 | 설명 |
|---|---|
| B0: manual/AX baseline | 기존 JAO 인스턴스를 참조 정답 또는 silver label로 사용 |
| B1: zero-shot LLM extraction | 스키마 없이 전문가 문서에서 직접 triple/JSON 추출 |
| B2: schema-prompted extraction | JAO JSON Schema를 prompt에 넣고 추출 |
| B3: retrieval-augmented schema extraction | 입력 문서에 관련된 NCS/PCF/O*NET/JAO schema만 검색해 주입 |
| B4: EDC-style pipeline | Extract → Define → Canonicalize 단계로 추출 후 JAO URI에 정규화 |
| B5: ontology-validator + human-in-loop | JSON Schema, URI 무결성, relation cardinality, confidence threshold를 통과하도록 자동 수정 및 전문가 검수 |

평가 지표:

- JSON Schema validity
- URI/reference integrity
- entity precision/recall/F1
- relation precision/recall/F1
- canonicalization accuracy: 같은 의미가 같은 URI로 묶였는가
- edge precision@k: 자동 매핑 상위 k개가 전문가 판단과 일치하는가
- graph consistency: cycle, deprecated reference, risk/action rule violation
- expert review time reduction

목표 수치:

- 추출 정확도/F1 85% 이상
- 전문가 검수 시간 30% 이상 감소
- 자동 매핑 precision@5 80% 이상

### 5.2 H2: 온톨로지 결합 Agent Harness 효용 검증

목표: 동일한 업무 시나리오에서 JAO 결합 방식이 일반 RAG보다 더 정확하고 안전한지 검증한다.

수주/제안 시나리오 예시:

1. 신규 리드가 들어왔을 때 산업, 예산, 니즈, 과거 거래 이력을 바탕으로 lead score와 우선순위를 산출한다.
2. RFP가 들어왔을 때 고객 요구사항을 NCS/PCF 업무 항목과 연결하고 제안서 목차를 생성한다.
3. 제안서 초안 생성 시 경쟁사 비방, 할인 한도, 하도급/공정거래 리스크를 감지한다.
4. 계약 체결 전 누락 산출물, 승인자, 리스크를 점검한다.
5. 파이프라인 forecast를 생성하고 위험 거래를 에스컬레이션한다.

비교군:

| 시스템 | 설명 |
|---|---|
| C0: LLM-only | 문맥 없이 일반 LLM 답변 |
| C1: Text RAG | 전문가 문서/표준 문서를 벡터 검색 후 답변 |
| C2: Hybrid RAG | 텍스트 검색 + metadata filter |
| C3: GraphRAG | JAO graph multi-hop retrieval + text retrieval |
| C4: Ontology-constrained Agent | Agent/Action/Tool/Artifact/Policy schema로 행동 제한 |
| C5: Multi-agent Harness | 역할별 agent와 controller를 두고 Action trace를 기록 |

평가 지표:

- 업무 성공률: 산출물이 요구사항을 충족하는가
- 환각률: 근거 없는 표준/법규/고객정보를 생성했는가
- 규정 준수율: guardrail, approval, risk rule을 지켰는가
- action validity: 허용된 Action만 호출했는가
- tool selection accuracy: 적절한 Tool/Artifact를 골랐는가
- traceability: 답변이 어떤 JAO node/edge에 근거하는가
- latency/cost: graph retrieval과 verifier 추가 비용

목표 수치:

- 업무 성공률 87% 이상
- 환각률 10% 이하
- 규정 준수율 90% 이상
- Graph/Agent 방식이 Text RAG 대비 통계적으로 유의미하게 우수

### 5.3 H3: 타 직무 복제 가능성

목표: 수주 도메인에서 만든 파이프라인을 다른 직무로 옮길 때 필요한 추가 작업량과 성능 저하를 측정한다.

복제 후보:

| 도메인 | 장점 | 주 용도 |
|---|---|---|
| 법인파산 | 법률 규칙과 절차가 명확함 | 규정/절차 온톨로지 복제 검증 |
| 스타트업 투자 | 계약서와 조건/예외가 풍부함 | 조건부 의사결정/리스크 추출 검증 |
| 구매 | 기존 Agent/Action 있음 | 기업 내부 운영 도메인 확장 |
| 재무 결산 | risk/high approval 구조가 명확함 | Action safety와 audit 검증 |
| HR 채용 | 다단계 workflow가 명확함 | Agent workflow 일반화 검증 |

평가 지표:

- 새 도메인 투입 후 entity/relation F1
- 기존 prompt/schema 재사용률
- 새로 작성해야 하는 domain-specific rule 수
- 전문가 검수 시간
- H2 성능의 domain transfer gap

## 6. 데이터셋 구축 및 어노테이션 계획

### 6.1 1차 평가셋: 수주/제안

구성:

- NCS 수주 능력단위 51개
- PCF 3.0 Market & Sell 213개
- B2B sales Agent 1개 + Action 5개
- 전문가 문서에서 추출한 문단/양식 단위 샘플 200~500개
- JAO node/edge gold label 1,000~2,000개

어노테이션 단위:

| 단위 | 라벨 |
|---|---|
| 문장/문단 | 관련 Task, Process, Concept |
| 업무 규칙 | precondition, guardrail, approval rule |
| 산출물 | Artifact type, required sections |
| 실행 행위 | Action, Tool, input/output |
| 법규/정책 | Regulation, Policy, riskLevel |
| 표준 매핑 | mapsTo, requires, governedBy |

### 6.2 검수 프로토콜

1. LLM 1차 추출
2. JSON Schema validation
3. URI canonicalization
4. confidence 기반 queue 생성
5. AX 전문가 검수
6. 검수 결과를 verifier/student model 학습 데이터로 축적

검수 우선순위:

- confidence가 낮은 `mapsTo`
- high/critical risk Action
- 법규 `governedBy`
- 제안서/계약서에 직접 영향을 주는 Artifact/Policy

## 7. 구현 아키텍처

권장 파이프라인:

1. Data loader: JSON → normalized table → graph nodes/edges
2. Index builder: text embedding index + graph index + schema index
3. Ontology constructor: schema-retrieved extraction + EDC-style canonicalization
4. Validator: JSON Schema, URI integrity, graph consistency, risk/action rules
5. GraphRAG retriever: vector retrieval + graph expansion + Personalized PageRank
6. Agent harness: Agent → Action → Tool → Artifact → Policy execution trace
7. Evaluator: task success, hallucination, compliance, traceability, cost
8. Human review UI: low-confidence edge review and correction logging

저장소 구조 제안:

```text
experiments/
  h1_ontology_construction/
  h2_agent_harness/
  h3_transfer/
data_working/
  public_release_safe/
  internal_apqc_restricted/
  annotations/
  evaluation_sets/
scripts/
  build_graph.py
  validate_jao.py
  create_suju_evalset.py
  run_rag_baselines.py
  run_agent_harness.py
reports/
  data_audit.md
  experiment_results.md
```

## 8. 12주 실행 계획

| 주차 | 산출물 | 내용 |
|---:|---|---|
| 1 | Data audit v1 | 전체 JSON schema/profile, license split, 수주 subset 확정 |
| 2 | JAO graph loader | Neo4j 또는 NetworkX 적재, node/edge integrity check |
| 3 | H1 annotation guide | 수주 문서 100개 샘플, node/edge 라벨링 기준 |
| 4 | H1 baselines | zero-shot, schema-prompt, retrieval-schema extraction |
| 5 | H1 canonicalizer | EDC-style canonicalization, URI 매칭, validator |
| 6 | H1 expert review | AX 전문가 검수, precision/recall/F1 산출 |
| 7 | H2 task set | 수주 업무 시나리오 30~50개, 정답/루브릭 정의 |
| 8 | H2 baselines | LLM-only, Text RAG, Hybrid RAG |
| 9 | GraphRAG | JAO graph expansion, relation-aware retrieval |
| 10 | Agent Harness | Action/Tool/Policy 제약 실행, trace logging |
| 11 | H3 pilot | 법인파산 또는 투자 도메인 소규모 복제 |
| 12 | Paper package | 논문 초안, 표/그림, 공개 가능 데이터셋 정리 |

## 9. 논문 구조 제안

1. Introduction: 기업 업무 AI의 문제는 지식 부족이 아니라 구조/검증/행동 제약 부족이다.
2. Related Work: RAG, GraphRAG, KG construction, ontology learning, LLM agents
3. Dataset: NCS/PCF/O*NET/JAO/Mapping/Suju subset
4. Method: Schema-grounded ontology construction + ontology-constrained agent harness
5. Experiments H1: ontology extraction and mapping validation
6. Experiments H2: RAG vs GraphRAG vs Agent Harness
7. Experiments H3: cross-domain transfer
8. Discussion: license, human-in-the-loop, safety, enterprise deployment
9. Conclusion

가능 venue:

- ACL/EMNLP: LLM + KG construction + agent evaluation
- NeurIPS Datasets & Benchmarks: 직무 온톨로지/반구조 업무 KB 벤치마크
- KDD/WWW: enterprise knowledge graph and workflow intelligence
- AAAI/IJCAI: neuro-symbolic AI, planning, agent governance
- ISWC: ontology learning and semantic web 관점

## 10. 가장 먼저 해야 할 일

1. `06_suju_focus`를 기준으로 공개 가능/내부 전용 데이터를 분리한다.
2. 수주 도메인 annotation guide를 만든다.
3. `mapping_edges_all.json`에서 low-confidence `mapsTo` 100개와 `governedBy` 100개를 샘플링해 전문가 검수셋을 만든다.
4. H1 baseline 3개를 먼저 돌린다: zero-shot, schema-prompted, retrieval-schema.
5. H2 업무 시나리오 30개를 만든다: 제안서, 리드, 계정 브리핑, 계약 리스크, 일정/승인.
6. 논문에서는 APQC 원문을 공개하지 않고, hid 구조와 통계/평가 결과 중심으로 서술한다.

## 11. 확인한 외부 참고 문서

- APQC PCF 한글 뷰어: https://ontology-research.vercel.app/pcf-viewer/index.html  
  로컬 `02_pcf` 데이터와 같은 규모인 2,017개 표준 프로세스, 3,284개 KPI, 5계층, 20개 산업 버전을 설명한다. 저작권은 APQC에 있음을 명시하고 있으므로 논문 공개 범위 판단에 계속 반영해야 한다.
- AX Notion 링크: https://axcorp.notion.site/37d8ffb88b65808da880f797d2eb3b38  
  2026-06-15 현재 외부 접근 시 404로 확인되어, 본 문서에는 사용자가 메시지에 붙여준 본문과 로컬 데이터만 반영했다.

## 12. 실제 데이터 샘플 기반 상세 분석

이 장은 로컬 JSON을 직접 파싱해 확인한 실제 값 중심의 부록이다. 연구 설계 단계에서는 이 장을 “데이터 이해표 + annotation guide 초안”으로 사용할 수 있다.

### 12.1 `01_ncs`: NCS 원천 데이터

NCS는 대분류-중분류-소분류-세분류-능력단위로 이어지는 계층형 직무 표준이다. 수주/제안 연구에서 가장 중요한 축은 `영업판매 > 영업 > 일반·해외영업 > 일반영업`과 `정보통신 > 정보기술 > 정보기술영업 > IT기술영업`이다.

실제 계층 예시:

| 단계 | 코드 | 명칭 | 실제 필드/정의 |
|---|---|---|---|
| L1 대분류 | `10` | 영업판매 | `NCS_LCLAS_CDNM="영업판매"` |
| L2 중분류 | `10-01` | 영업 | `NCS_MCLAS_CDNM="영업"` |
| L3 소분류 | `10-01-01` | 일반·해외영업 | `NCS_SCLAS_CDNM="일반·해외영업"` |
| L4 세분류 | `10010101` | 일반영업 | “이윤창출과 고객만족을 위하여 자사의 상품을 고객에게 판매하고 고객을 유지하는 일” |

실제 `ncs_dclas.json` 레코드 축약:

```json
{
  "NCS_LCLAS_CD": "10",
  "NCS_LCLAS_CDNM": "영업판매",
  "NCS_MCLAS_CD": "01",
  "NCS_MCLAS_CDNM": "영업",
  "NCS_SCLAS_CD": "01",
  "NCS_SCLAS_CDNM": "일반·해외영업",
  "NCS_SUBD_CD": "01",
  "NCS_SUBD_CDNM": "일반영업",
  "DUTY_DEF": "일반영업이란 이윤창출과 고객만족을 위하여 자사의 상품을 고객에게 판매하고 고객을 유지하는 일이다."
}
```

`ncs_unit.json`에서 일반영업 능력단위는 다음처럼 실제 수주 사이클을 이룬다.

| NCS_CL_CD | unitCode | 능력단위 | 수준 | 연구 해석 |
|---|---:|---|---:|---|
| `1001010103_20v2` | 03 | 영업 전략수립 | 5 | 제안/수주 전 전략 노드 |
| `1001010104_20v2` | 04 | 영업 고객발굴 | 3 | lead generation |
| `1001010105_20v2` | 05 | 영업 제안 | 3 | proposal generation |
| `1001010106_20v2` | 06 | 영업 계약체결관리 | 3 | negotiation/contracting |
| `1001010107_20v2` | 07 | 영업 계약이행관리 | 3 | delivery follow-up |
| `1001010108_20v2` | 08 | 영업 성과관리 | 5 | KPI/forecast/evaluation |
| `1001010109_20v2` | 09 | 영업 고객불만관리 | 3 | complaint handling |
| `1001010110_20v2` | 10 | 영업 고객유지관리 | 3 | retention/customer success |
| `1001010111_20v2` | 11 | 영업 환경분석 | 4 | market/competitor analysis |

IT기술영업은 B2B 수주/제안 연구에 더 직접적이다.

| 세분류 | unitCode | 능력단위 | 수준 | 실제 정의의 핵심 |
|---|---:|---|---:|---|
| IT기술영업 | 01 | 기술영업시장 현황분석 | 5 | 시장 요구, 정부시책, 내외부 기술 현황 분석 |
| IT기술영업 | 02 | 기술영업 전략수립 | 6 | 목표 시장 설정 및 세부 계획 수립 |
| IT기술영업 | 03 | 기술영업 고객 현황분석 | 5 | 산업별 고객 수요 파악 및 사업기회 발굴 |
| IT기술영업 | 04 | 사전 기술영업 | 5 | 고객사가 IT 기획/예산을 준비하도록 사전 영업 |
| IT기술영업 | 05 | 수주전략수립 | 7 | 고객 요구, 경쟁사 분석, 평가 우위 요소 도출 |
| IT기술영업 | 06 | 기술영업 제안 작업 | 5 | 가격견적, 제안서, 제안설명, 성능테스트 제공 |
| IT기술영업 | 07 | 사업계약 협상 | 6 | 업무범위 재정의 및 가격 협의 |
| IT기술영업 | 08 | 기술영업 사후관리 | 5 | 사업 수행 지원 및 후속 사업 발굴 |
| IT기술영업 | 09 | 협력선관리 | 5 | 협력선 발굴 및 관계 유지 |
| IT기술영업 | 10 | 영업관리 지원 | 4 | 계약 이행 여부, 영업 실적, 결과 분석 |

분포 분석:

| 항목 | 실제 값 | 해석 |
|---|---:|---|
| NCS 능력단위 전체 | 28,666 | H1 학습/검증의 원천 후보 |
| 수준 5 | 8,214 | 중상급 실무/관리 수준이 가장 많음 |
| 수준 3 | 6,968 | 실행 업무가 많아 Action 후보로 적합 |
| 수준 8 | 180 | 고난도/전략 업무, human-in-the-loop 후보 |
| `USG_YN=Y` | 4,167 | 현행 여부 필터링 필요 |
| `USG_YN=N` | 24,499 | 버전/폐기/과거 항목이 많아 status 정합성 검토 필요 |

연구상 주의점: `NCS_LCLAS_CD`, `NCS_MCLAS_CD`, `NCS_SCLAS_CD`, `NCS_SUBD_CD`는 상대 코드이므로 단독으로 쓰면 충돌한다. JAO에서는 이를 `10010101`처럼 concat한 URI/notation으로 정규화한다.

### 12.2 `02_pcf`: PCF 프로세스/메트릭

PCF는 기업 프로세스 관점의 트리다. 수주/제안의 중심은 `3.0 Market and Sell Products and Services`이다.

실제 PCF 3.x 예시:

| hid | level | nameKo | parent | 연구 해석 |
|---|---:|---|---|---|
| `3.0` | 1 | 제품·서비스 마케팅 및 판매 | null | 수주/영업 전체 category |
| `3.5` | 2 | 영업 계획 개발·관리 | `3.0` | sales planning |
| `3.5.6` | 3 | 오프라인 매장 영업 수행 | `3.5` | retail/field action 후보 |
| `3.5.7` | 3 | 현장 영업 수행 | `3.5` | B2B field sales 후보 |

실제 `pcf_data.json` 축약:

```json
{
  "pcfId": 10105,
  "hid": "3.5",
  "nameEn": "Develop and manage sales plans",
  "nameKo": "영업 계획 개발·관리",
  "level": 2,
  "parent": "3.0",
  "hasMetrics": true
}
```

PCF 3.0에 연결된 실제 metric 예시:

| metricId | hid | metricNameKo | formulaKo | unitsKo |
|---:|---|---|---|---|
| 109038 | 3.0 | 전사 FTE 대비 영업·마케팅 FTE 비율 | `((영업 기능 수행 FTE 수 + 마케팅 기능 수행 FTE 수) / 사업체 FTE 수) * 100.0` | 퍼센트 |
| 109640 | 3.0 | B2B 고객 1년 이탈률 | B2B 고객 1년 유지율 | 퍼센트 |
| 109350 | 3.0 | 획득 디지털 미디어 마케팅 채널 ROI | 획득 디지털 미디어 채널의 연간 마케팅 ROI 총합 | 퍼센트 |
| 104745 | 3.0 | 인터넷 주문 매출이 사업체 총매출에서 차지하는 비율 | 웹사이트 채널이 차지하는 연간 매출 비중 | 퍼센트 |
| 104736 | 3.0 | 소셜미디어 채널 캠페인을 통해 타깃팅된 고객 비율 | 동일 | 퍼센트 |

산업별 PCF 예시:

| 파일 | records | level 분포 | 특징 |
|---|---:|---|---|
| `industries/banking.json` | 2,027 | L1 13, L2 75, L3 355, L4 1370, L5 202, L6 12 | 은행 산업 특화로 일부 L6까지 존재 |
| `industries/education.json` | 1,470 | L1 12, L2 79, L3 345, L4 945, L5 89 | 교육청/학교 맥락으로 명칭 변환 |
| `industries/retail.json` | 1,708 | L1 13, L2 69, L3 312, L4 1183, L5 131 | 리테일 현장/채널 프로세스 강화 |

연구상 주의점: PCF는 연구 내부 사용은 가능하지만 원문 재배포에 주의해야 한다. 논문에는 ID, 계층 구조, 통계, 평가 결과 중심으로 쓰고 긴 원문 텍스트는 피한다.

### 12.3 `03_onet`: O*NET 직업/과업

O*NET은 NCS보다 granular한 task statement를 제공한다. 수주/기술영업과 잘 맞는 직업 예시는 `41-4011.00 Sales Representatives, Wholesale and Manufacturing, Technical and Scientific Products`이다.

실제 occupation 축약:

```json
{
  "socCode": "41-4011.00",
  "title": "Sales Representatives, Wholesale and Manufacturing, Technical and Scientific Products",
  "jobZone": 4,
  "description": "Sell goods for wholesalers or manufacturers where technical or scientific knowledge is required..."
}
```

실제 task 예시:

| taskId | taskType | task |
|---:|---|---|
| 11240 | Core | Negotiate prices or terms of sales or service agreements. |
| 20608 | Core | Prepare and submit sales contracts for orders. |
| 11251 | Core | Visit establishments to evaluate needs or to promote product or service sales. |
| 11241 | Core | Maintain customer records, using automated systems. |
| 11237 | Core | Answer customers' questions about products, prices, availability, or credit terms. |
| 11238 | Core | Quote prices, credit terms, or other bid specifications. |
| 20609 | Core | Contact new or existing customers to discuss how specific products or services can meet their needs. |
| 11239 | Core | Emphasize product features, based on analyses of customers' needs and technical knowledge. |

실제 skill 예시:

| skill | IM | LV | 연구 해석 |
|---|---:|---:|---|
| Persuasion | 4.25 | 4.00 | 제안/협상 agent skill |
| Negotiation | 4.00 | 4.00 | 계약 협상 Action과 연결 |
| Social Perceptiveness | 3.88 | 3.75 | 고객 맥락 이해 |
| Service Orientation | 3.75 | 3.38 | 사후관리/고객유지 |

분포:

| 항목 | 값 |
|---|---:|
| occupation | 1,016 |
| 총 task | 18,641 |
| occupation당 평균 task | 18.35 |
| 최대 task 수 | 30 |
| jobZone 2 | 331 |
| jobZone 3 | 212 |
| jobZone 4 | 226 |
| jobZone 5 | 154 |

연구상 해석: O*NET task는 JAO `Action` 후보를 만드는 데 적합하고, skill/knowledge/ability는 Agent persona와 evaluation rubric을 만드는 데 적합하다.

### 12.4 `04_jao`: 정규화된 온톨로지 인스턴스

JAO는 이 연구의 핵심 스키마이자 baseline이다.

#### Concept 예시

```json
{
  "$id": "jao://Concept/ncs/20010501",
  "class": "Concept",
  "namespace": "ncs",
  "label": {"ko": "IT기술영업"},
  "definition": "IT기술영업은 사업수주를 위하여 정보기술 관련 전반적인 지식을 바탕으로 고객 관리 및 영업기회를 창출하고 고객의 요구에 적합한 솔루션 제안을 통해 협상, 계약, 판매 및 사후관리를 수행하는 일이다.",
  "broader": ["jao://Concept/ncs/200105"]
}
```

#### Task 예시

`Task.json`에는 O*NET 18,641개와 NCS 변환 일부가 들어 있다. 수주 관련 NCS task 예시는 다음처럼 `Concept/ncs/20010501`에 연결된다.

```json
{
  "$id": "jao://Task/ncs/02.5",
  "class": "Task",
  "namespace": "ncs",
  "label": {"ko": "기술영업 전략수립"},
  "description": {"ko": "기술영업 전략수립이란 시장 현황 정보를 바탕으로 목표 시장을 설정하여 영업 목표를 달성하기 위한 세부 계획을 수립하는 능력이다."},
  "levelL": 6,
  "taskType": "NCS-Element",
  "requires": ["jao://Concept/ncs/20010501"]
}
```

coverage 이슈: `06_suju_focus`에는 `수주전략수립`, `기술영업 제안 작업`, `사업계약 협상` 등 중요한 능력단위가 들어 있지만, 현재 `Task.json`의 NCS subset에는 `기술영업 전략수립`, `기술영업 사후관리` 등 일부만 직접 보인다. H1에서는 이 차이를 coverage gap으로 측정하고, 누락된 NCS unit을 JAO Task로 보강하는 실험을 설계할 수 있다.

#### Process 예시

```json
{
  "$id": "jao://Process/pcf/pcf-3.0",
  "class": "Process",
  "namespace": "pcf",
  "label": {
    "ko": "제품·서비스 마케팅 및 판매",
    "en": "Market and Sell Products and Services"
  },
  "hid": "3.0",
  "level": 1,
  "pcfId": 10004,
  "hasMetrics": true
}
```

#### Agent 예시

```json
{
  "$id": "jao://Agent/agent/sales-b2b",
  "label": {"ko": "B2B 영업 에이전트"},
  "role": "리드 관리·제안서 작성 보조·미팅 준비",
  "jobFamily": "sales",
  "primaryMissions": [
    "리드 적합도 점수·우선순위화",
    "고객 컨텍스트 브리핑(공시·뉴스)",
    "제안서 1차 draft",
    "파이프라인 위험 알림"
  ],
  "interventionMode": "checkpoint",
  "actions": [
    "jao://Action/agent/score_lead",
    "jao://Action/agent/brief_account",
    "jao://Action/agent/draft_proposal",
    "jao://Action/agent/forecast_pipeline",
    "jao://Action/agent/schedule_meeting"
  ]
}
```

#### Action 예시

```json
{
  "$id": "jao://Action/agent/draft_proposal",
  "label": {"ko": "제안서 작성"},
  "category": "sales.generate",
  "inputs": [
    {"name": "accountId", "type": "string", "required": true},
    {"name": "scope", "type": "string", "required": true},
    {"name": "budget", "type": "string", "required": true}
  ],
  "outputs": [
    {"name": "proposalDoc", "type": "string", "required": true}
  ],
  "preconditions": ["가격 한도 검증"],
  "riskLevel": "medium",
  "approvers": ["sales-mgr"],
  "auditLog": true,
  "tools": [
    "jao://Tool/tool/openai-api",
    "jao://Tool/tool/figma"
  ]
}
```

#### Tool, Artifact, Regulation, Policy 예시

| class | id | 핵심 필드 | 연구 해석 |
|---|---|---|---|
| Tool | `openai-api` | category `AI`, vendor `OpenAI`, pricing `usage` | 생성/임베딩 도구 |
| Artifact | `proposal-rfp` | sections: 회사 소개, 이해 사항, 솔루션, 구현 계획, 가격, 사례, 팀 | 제안서 출력 스키마 |
| Regulation | `0c9f03a7` | 표시·광고의 공정화에 관한 법률, enforcer 공정거래위원회 | 과장 광고/비방 방지 guardrail |
| Policy | `sox-control-iv` | enforcePrompt, severity `critical` | 규제→실행 전 검증 prompt 패턴 |

JAO class 분포:

| class | records | 주 namespace |
|---|---:|---|
| Task | 18,977 | ncs, onet |
| Metric | 3,284 | pcf |
| Process | 2,019 | pcf |
| Concept | 1,711 | ncs, onet |
| Regulation | 1,371 | reg |
| Document | 163 | guideline |
| Tool | 93 | tool |
| Action | 51 | agent |
| Artifact | 42 | art |
| Agent | 10 | agent |
| Policy | 1 | jao |

### 12.5 `05_mappings`: MappingEdge와 graph edge

`mapping_edges_all.json`은 검수 전 자동 매핑이다. 연구에서는 이 파일을 그대로 정답으로 쓰기보다, noisy silver label 및 검수 대상 pool로 쓰는 것이 맞다.

실제 low-confidence `mapsTo` 예시:

```json
{
  "from": "jao://Concept/onet/41-9099.00",
  "predicate": "mapsTo",
  "to": "jao://Process/pcf/pcf-3.5.7",
  "confidence": 0.1674,
  "mappingType": "related",
  "evidence": "O*NET 'Sales and Related Workers, All Other' → PCF '현장 영업 수행'"
}
```

이 예시는 의미상 완전히 틀렸다고 단정할 수는 없지만, confidence가 낮으므로 “전문가 검수 후보”가 된다. 반대로 keyword가 맞아 보이더라도 법규 연결은 오매칭 위험이 있으므로 별도 검수해야 한다.

실제 graph edge 예시:

| predicate | from | to | confidence | 해석 |
|---|---|---|---:|---|
| `partOf` | `jao://Process/pcf/pcf-1.1.1.1` | `jao://Process/pcf/pcf-1.1.1` | 0.99 | PCF 트리 |
| `broader` | `jao://Concept/ncs/0101` | `jao://Concept/ncs/01` | 0.99 | NCS/SKOS 상위 개념 |
| `requires` | `jao://Task/ncs/01.1` | `jao://Concept/ncs/24040401` | 0.90 | Task가 요구하는 직무 개념 |
| `actions` | `jao://Agent/agent/customer-support` | `jao://Action/agent/match_faq` | 0.95 | Agent 실행 가능 Action |
| `uses` | `jao://Action/agent/analyze_campaign` | `jao://Tool/tool/powerbi` | 0.90 | Action이 사용하는 Tool |
| `governedBy` | `jao://Concept/ncs/14010201` | `jao://Regulation/reg/53b89a91` | 0.70 | 법규 매핑, 검수 필요 |

그래프 엣지 분포:

| predicate | 건수 |
|---|---:|
| requires | 18,977 |
| governedBy | 3,842 |
| partOf | 2,004 |
| broader | 1,664 |
| mapsTo | 817 |
| related | 396 |
| uses | 83 |
| tools | 58 |
| actions | 51 |
| regulations | 38 |
| artifacts | 32 |

### 12.6 `06_suju_focus`: 수주/제안 선별본

수주 선별본은 연구의 첫 실험 단위다. 핵심은 `NCS 수주 능력단위 51개 + PCF 3.0 프로세스 213개 + B2B 영업 Agent/Action 6개`이다.

실제 target NCS 능력단위 일부:

| subdCode | subdName | unitCode | unitName | level |
|---|---|---:|---|---:|
| 10010101 | 일반영업 | 03 | 영업 전략수립 | 5 |
| 10010101 | 일반영업 | 05 | 영업 제안 | 3 |
| 10010101 | 일반영업 | 06 | 영업 계약체결관리 | 3 |
| 10030101 | 통신판매 | 03 | 통신판매 전략수립 | 6 |
| 20010501 | IT기술영업 | 05 | 수주전략수립 | 7 |
| 20010501 | IT기술영업 | 06 | 기술영업 제안 작업 | 5 |
| 20010501 | IT기술영업 | 07 | 사업계약 협상 | 6 |

실제 Agent/Action compact view:

| class | id | label | risk | inputs | outputs |
|---|---|---|---|---|---|
| Agent | `sales-b2b` | B2B 영업 에이전트 | - | - | actions/tools/artifacts/regulations |
| Action | `score_lead` | 리드 점수 계산 | low | `leadId` | `score`, `reasons` |
| Action | `brief_account` | 계정 브리핑 | low | `accountId` | `briefDoc` |
| Action | `draft_proposal` | 제안서 작성 | medium | `accountId`, `scope`, `budget` | `proposalDoc` |
| Action | `forecast_pipeline` | 파이프라인 예측 | low | `team`, `quarter` | `forecast`, `risks[]` |
| Action | `schedule_meeting` | 미팅 일정 | low | `attendees[]`, `topic`, `duration` | `meetingLink` |

이 선별본은 H2 실험의 단위가 된다. 즉, 같은 RFP/리드/계약 리스크 시나리오를 일반 RAG와 JAO Agent Harness에 넣고 결과를 비교한다.

## 13. 연구 실험의 실제 Input/Output 예시

아래 예시는 실제 데이터의 URI, label, Action schema를 사용해 만든 연구용 입출력 예시다. 고객명/금액/상황은 실험용 합성 입력으로 두고, 표준 노드와 출력 스키마는 로컬 데이터의 실제 값을 사용한다.

### 13.1 H1 예시: 전문가 문서/업무 문장에서 JAO 온톨로지 생성

입력 예시:

```json
{
  "sourceDocument": "shipley_or_sales_method_sample",
  "paragraphId": "p-001",
  "text": "고객 요구사항과 경쟁사 제안 전략을 분석하여 평가 우위 요소를 도출하고, 가격견적과 제안서 초안을 작성한 뒤 영업관리자의 검토를 받아 제출한다.",
  "retrievedStandards": [
    {
      "source": "NCS",
      "id": "20010501-05",
      "label": "수주전략수립",
      "level": 7
    },
    {
      "source": "NCS",
      "id": "20010501-06",
      "label": "기술영업 제안 작업",
      "level": 5
    },
    {
      "source": "JAO",
      "id": "jao://Action/agent/draft_proposal",
      "label": "제안서 작성"
    },
    {
      "source": "JAO",
      "id": "jao://Artifact/art/proposal-rfp",
      "label": "제안서/RFP 응답"
    }
  ]
}
```

기대 출력 예시:

```json
{
  "nodes": [
    {
      "$id": "jao://Task/ncs/20010501-05",
      "class": "Task",
      "namespace": "ncs",
      "label": {"ko": "수주전략수립"},
      "description": {"ko": "고객 요구, 경쟁사 분석, 제안 평가 우위 요소를 도출하여 수주 전략을 수립하는 능력"},
      "levelL": 7,
      "taskType": "NCS-Element",
      "requires": ["jao://Concept/ncs/20010501"],
      "confidence": 0.86,
      "sourceEvidence": ["paragraph:p-001", "06_suju_focus/ncs_suju_units.json"]
    },
    {
      "$id": "jao://Action/agent/draft_proposal",
      "class": "Action",
      "namespace": "agent",
      "label": {"ko": "제안서 작성"},
      "riskLevel": "medium",
      "approvers": ["sales-mgr"],
      "tools": ["jao://Tool/tool/openai-api", "jao://Tool/tool/figma"]
    }
  ],
  "edges": [
    {
      "from": "jao://Task/ncs/20010501-05",
      "predicate": "requires",
      "to": "jao://Concept/ncs/20010501",
      "confidence": 0.92
    },
    {
      "from": "jao://Action/agent/draft_proposal",
      "predicate": "produces",
      "to": "jao://Artifact/art/proposal-rfp",
      "confidence": 0.88
    },
    {
      "from": "jao://Action/agent/draft_proposal",
      "predicate": "requiresApproval",
      "to": "sales-mgr",
      "confidence": 0.90
    }
  ],
  "validation": {
    "jsonSchemaValid": true,
    "uriIntegrity": "needs_review",
    "reason": "새 Task URI jao://Task/ncs/20010501-05는 기존 Task.json에 없으므로 신규 생성 후보"
  }
}
```

평가 포인트:

- `수주전략수립`과 `기술영업 제안 작업`을 올바른 Task로 뽑았는가
- `draft_proposal` Action과 `proposal-rfp` Artifact를 연결했는가
- 승인자 `sales-mgr`를 risk/precondition에 맞게 부여했는가
- 기존 JAO에 없는 수주 Task를 신규 후보로 표시했는가

### 13.2 H1 예시: 자동 매핑 검수

입력 예시:

```json
{
  "candidateEdge": {
    "from": "jao://Concept/onet/41-9099.00",
    "predicate": "mapsTo",
    "to": "jao://Process/pcf/pcf-3.5.7",
    "confidence": 0.1674,
    "evidence": "O*NET 'Sales and Related Workers, All Other' → PCF '현장 영업 수행'"
  },
  "task": "이 매핑이 수주/영업 도메인에서 유효한지 판단하고, 유효하면 이유와 보정 confidence를 제시하라."
}
```

기대 출력 예시:

```json
{
  "decision": "review_required",
  "label": "partially_related",
  "revisedConfidence": 0.55,
  "rationale": "O*NET 직업군은 영업 관련 직무이지만 'All Other' 범주라 PCF 3.5.7 현장 영업 수행과 정확히 동일하다고 보기 어렵다. 현장 영업 수행 경험이 명시된 task가 있으면 confidence를 올릴 수 있다.",
  "requiredEvidence": [
    "O*NET task에 field sales, customer visit, account management 표현이 있는지 확인",
    "PCF 3.5.7 하위 설명과 영업 채널 맥락 확인"
  ],
  "humanQueue": {
    "priority": "medium",
    "assignee": "sales-domain-expert"
  }
}
```

### 13.3 H2 예시: 일반 RAG 입력과 출력

입력 예시:

```json
{
  "query": "A사 제조 DX RFP에 대해 제안서 초안을 만들어줘. 예산은 3억 원이고, 고객은 빠른 구축과 보안 준수를 중시한다.",
  "retrievalCorpus": [
    "NCS 수주 관련 능력단위",
    "PCF 3.0 Market and Sell",
    "제안서 템플릿",
    "영업 가이드 문서"
  ]
}
```

일반 RAG 기대 출력:

```json
{
  "answer": {
    "proposalOutline": [
      "회사 소개",
      "고객 요구사항 이해",
      "제안 솔루션",
      "구축 일정",
      "가격 및 조건",
      "보안 대응",
      "레퍼런스"
    ],
    "summary": "A사의 빠른 구축 요구와 보안 준수 요구를 반영해 제조 DX 솔루션 도입 제안서를 작성한다."
  },
  "limitations": [
    "어떤 Action을 실행했는지 추적이 약함",
    "가격 한도 검증, 승인자, 리스크 rule이 명시적으로 강제되지 않음",
    "근거 URI가 없으면 표준/규정 provenance가 약함"
  ]
}
```

### 13.4 H2 예시: JAO Agent Harness 입력과 출력

입력 예시:

```json
{
  "agent": "jao://Agent/agent/sales-b2b",
  "goal": "A사 제조 DX RFP 제안서 초안 생성",
  "context": {
    "accountId": "acct-A-manufacturing",
    "scope": "제조 설비 데이터 통합, 이상탐지 대시보드, 보안 로그 연동",
    "budget": "300000000 KRW",
    "constraints": [
      "빠른 구축",
      "보안 준수",
      "경쟁사 비방 금지",
      "가격 할인 한도 검증"
    ]
  }
}
```

기대 출력 예시:

```json
{
  "selectedAgent": "jao://Agent/agent/sales-b2b",
  "executionPlan": [
    {
      "step": 1,
      "action": "jao://Action/agent/brief_account",
      "inputs": {"accountId": "acct-A-manufacturing"},
      "outputs": ["briefDoc"],
      "riskLevel": "low"
    },
    {
      "step": 2,
      "action": "jao://Action/agent/draft_proposal",
      "inputs": {
        "accountId": "acct-A-manufacturing",
        "scope": "제조 설비 데이터 통합, 이상탐지 대시보드, 보안 로그 연동",
        "budget": "300000000 KRW"
      },
      "preconditions": ["가격 한도 검증"],
      "approvers": ["sales-mgr"],
      "outputs": ["proposalDoc"],
      "riskLevel": "medium"
    }
  ],
  "retrievedOntologyContext": {
    "ncs": [
      "jao://Concept/ncs/20010501",
      "NCS 20010501-05 수주전략수립",
      "NCS 20010501-06 기술영업 제안 작업"
    ],
    "pcf": [
      "jao://Process/pcf/pcf-3.0",
      "jao://Process/pcf/pcf-3.5"
    ],
    "artifact": [
      "jao://Artifact/art/proposal-rfp"
    ],
    "guardrails": [
      "가격 할인 한도 검증",
      "경쟁사 비방 금지",
      "서약서 없는 정보 공유 금지"
    ]
  },
  "proposalDoc": {
    "sections": [
      "회사 소개",
      "고객 요구사항 이해",
      "제안 솔루션",
      "구현 계획",
      "가격",
      "사례",
      "팀"
    ],
    "riskChecklist": [
      {"item": "가격 할인 한도 검증", "status": "needs_sales_mgr_review"},
      {"item": "경쟁사 비방 금지", "status": "passed"},
      {"item": "보안 준수 표현", "status": "needs_security_evidence"}
    ]
  },
  "auditTrace": {
    "allowedActionsOnly": true,
    "schemaValid": true,
    "humanApprovalRequired": true,
    "approvalTarget": "sales-mgr"
  }
}
```

일반 RAG와의 차이:

- 출력이 단순 답변이 아니라 `Action trace`를 포함한다.
- `draft_proposal`은 medium risk이므로 `sales-mgr` 승인 필요가 드러난다.
- `proposal-rfp` Artifact의 실제 sections를 따르므로 산출물 구조가 안정적이다.
- `NCS/PCF/Artifact/Guardrail` 근거가 URI 또는 표준 ID로 추적된다.

### 13.5 H2 평가용 정답 루브릭 예시

```json
{
  "scenarioId": "sales-rfp-001",
  "mustHave": [
    "고객 요구사항 이해 섹션",
    "솔루션/구현 계획 섹션",
    "가격 또는 예산 대응 섹션",
    "보안 준수 체크",
    "담당자 승인 또는 검토 필요 표시"
  ],
  "mustNotHave": [
    "근거 없는 법규명 생성",
    "경쟁사 비방 표현",
    "승인 없이 가격 할인 확정",
    "허용되지 않은 외부 시스템 변경"
  ],
  "expectedOntologyGrounding": [
    "jao://Agent/agent/sales-b2b",
    "jao://Action/agent/draft_proposal",
    "jao://Artifact/art/proposal-rfp",
    "jao://Concept/ncs/20010501",
    "jao://Process/pcf/pcf-3.0"
  ],
  "metrics": {
    "taskSuccess": "0/1 or 1-5 rubric",
    "hallucination": "unsupported claim count",
    "compliance": "passed guardrail count / total guardrails",
    "traceability": "grounded output items / total output items"
  }
}
```

### 13.6 H3 예시: 타 도메인 복제 입력/출력

입력 예시:

```json
{
  "targetDomain": "법인파산",
  "availableMaterials": [
    "변호사 가이드북",
    "강의 STT",
    "법원 제출 서류 양식"
  ],
  "reuseFromSalesPipeline": [
    "JAO base schema",
    "Document chunking",
    "Task/Action/Artifact extraction prompt",
    "JSON Schema validator",
    "human review queue"
  ]
}
```

기대 출력 예시:

```json
{
  "newAgentCandidate": {
    "$id": "jao://Agent/agent/corporate-bankruptcy",
    "class": "Agent",
    "label": {"ko": "법인파산 절차 보조 에이전트"},
    "jobFamily": "legal",
    "primaryMissions": [
      "파산 신청 요건 점검",
      "필요 서류 체크리스트 생성",
      "기일/절차 리스크 알림",
      "법률 검토 필요 항목 에스컬레이션"
    ],
    "interventionMode": "step-by-step"
  },
  "transferEvaluation": {
    "reusedModules": [
      "schema retrieval",
      "EDC-style canonicalization",
      "validator",
      "human review queue"
    ],
    "newDomainRulesNeeded": [
      "법원 제출 서류 검증",
      "변호사 검토 필수 조건",
      "민감정보 마스킹"
    ],
    "successCriterion": "수주 도메인 대비 entity/relation F1 하락폭 15% 이내"
  }
}
```

## 14. 결론

이 데이터의 가장 큰 강점은 이미 “표준 직무 데이터 → 통합 온톨로지 → 그래프 엣지 → 에이전트 실행 스키마”까지 한 번 연결되어 있다는 점이다. 따라서 연구는 온톨로지를 새로 정의하는 데 머물기보다, 다음을 정량적으로 증명하는 방향이 좋다.

- LLM은 표준 스키마와 전문가 문서를 결합해 업무 온톨로지를 자동 구축할 수 있다.
- 온톨로지로 제약된 Agent Harness는 일반 RAG보다 업무 성공률과 규정 준수율이 높다.
- 이 파이프라인은 수주/제안 외 도메인으로 복제 가능하다.

즉, 핵심 논문 메시지는 “기업용 LLM 에이전트에는 더 많은 문서 검색만이 아니라, 명시적 업무 온톨로지와 검증 가능한 Action schema가 필요하다”로 잡는 것이 가장 설득력 있다.
