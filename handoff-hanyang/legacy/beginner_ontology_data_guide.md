# 온톨로지 초보자를 위한 AX-한양대 데이터 해설서

작성일: 2026-06-16  
대상 경로: `/home/minjoo/AX_서울펠로우`

## 1. 한 문장으로 이해하기

이 데이터는 “기업 업무를 AI 에이전트가 안전하게 수행하도록, 업무 표준과 전문가 지식을 카드와 화살표로 정리한 재료”다.

온톨로지를 모르는 상태에서는 다음 비유로 보면 된다.

| 온톨로지 용어 | 쉬운 비유 | 이 데이터에서의 예 |
|---|---|---|
| Node / Entity | 업무 카드 한 장 | `IT기술영업`, `영업 제안`, `제안서 작성 Action` |
| Edge / Relation | 카드 사이의 화살표 | `Task requires Concept`, `Action uses Tool` |
| Schema | 카드 양식 | `Task`에는 label, description, level, requires가 있어야 함 |
| URI | 카드의 주소 | `jao://Concept/ncs/20010501` |
| Graph | 카드와 화살표 전체 지도 | NCS, PCF, O*NET, Agent, Tool이 연결된 업무 지도 |

예를 들어 “제안서 작성”이라는 업무를 온톨로지로 보면 다음처럼 된다.

```text
Concept: IT기술영업
  <- requires -
Task: 기술영업 제안 작업
  -> enables/mapsTo 후보 ->
Process: PCF 3.0 Market and Sell

Agent: sales-b2b
  -> actions ->
Action: draft_proposal
  -> uses ->
Tool: openai-api, figma
  -> produces ->
Artifact: proposal-rfp
```

즉, 온톨로지는 “AI가 제안서를 그냥 쓰게 하는 것”이 아니라, “어떤 업무인지, 어떤 능력과 프로세스에 근거하는지, 어떤 도구를 써야 하는지, 어떤 산출물을 만들어야 하는지, 어떤 승인과 규정이 필요한지”를 구조화하는 방법이다.

## 2. H1을 쉬운 말로 다시 설명

### 2.1 H1의 원래 표현

H1은 다음 가설이다.

> 표준 체계를 스키마로 주입하고 전문가 자료를 입력하면, 수동 구축 대비 높은 정합성의 직무 온톨로지가 자동 생성된다.

쉽게 말하면 다음과 같다.

> 사람이 읽는 업무 문서와 직무 표준을 LLM에게 주면, LLM이 업무 카드(Node)와 연결 화살표(Edge)를 자동으로 만들어낼 수 있는지 검증한다.

### 2.2 실제로 무엇을 하는 태스크인가

H1은 “문서 요약”이 아니다. H1은 “업무 문장을 정해진 양식의 데이터로 바꾸는 작업”이다.

입력 문장 예시:

```text
고객 요구사항과 경쟁사 제안 전략을 분석하여 평가 우위 요소를 도출하고,
가격견적과 제안서 초안을 작성한 뒤 영업관리자의 검토를 받아 제출한다.
```

LLM이 만들어야 하는 출력 예시:

```json
{
  "nodes": [
    {
      "class": "Task",
      "label": {"ko": "수주전략수립"},
      "requires": ["jao://Concept/ncs/20010501"],
      "confidence": 0.86
    },
    {
      "class": "Action",
      "label": {"ko": "제안서 작성"},
      "riskLevel": "medium",
      "approvers": ["sales-mgr"],
      "tools": ["jao://Tool/tool/openai-api", "jao://Tool/tool/figma"]
    }
  ],
  "edges": [
    {
      "from": "Task:수주전략수립",
      "predicate": "requires",
      "to": "jao://Concept/ncs/20010501"
    },
    {
      "from": "Action:제안서 작성",
      "predicate": "produces",
      "to": "jao://Artifact/art/proposal-rfp"
    }
  ]
}
```

### 2.3 H1의 전체 작업 흐름

H1은 다음 순서로 진행하면 된다.

| 단계 | 하는 일 | 쉽게 말하면 | 사용하는 데이터 |
|---:|---|---|---|
| 1 | 도메인 선택 | 먼저 수주/제안만 잡는다 | `06_suju_focus` |
| 2 | 표준 후보 검색 | 관련 NCS/PCF/O*NET 노드를 찾는다 | `01_ncs`, `02_pcf`, `03_onet` |
| 3 | 문서에서 항목 추출 | 문장 속 업무, 산출물, 규칙을 뽑는다 | 쉬플리 자료, NCS 학습모듈, STT |
| 4 | JAO 양식으로 변환 | 뽑은 내용을 Task/Action/Artifact 등으로 저장한다 | `04_jao/schemas` |
| 5 | 기존 노드와 연결 | 이미 있는 노드와 중복 여부를 확인한다 | `04_jao/instances` |
| 6 | 관계 생성 | requires, uses, produces 같은 화살표를 만든다 | `05_mappings`, `graph_edges_all` |
| 7 | 자동 검증 | JSON 양식과 URI가 맞는지 검사한다 | schemas, validator |
| 8 | 전문가 검수 | 애매한 것은 사람이 확인한다 | AX 전문가 |
| 9 | 성능 평가 | 자동 구축이 얼마나 맞았는지 수치화한다 | precision, recall, F1 |

### 2.4 비교 방법 B0~B5를 쉬운 말로

| 방법 | 쉬운 설명 | 기대 |
|---|---|---|
| B0: manual/AX baseline | AX가 이미 만든 JAO 데이터를 기준 답안처럼 쓴다 | 비교 기준 |
| B1: zero-shot LLM extraction | LLM에게 아무 양식 없이 “업무 지식을 뽑아봐”라고 시킨다 | 가장 단순하지만 오류가 많을 가능성 |
| B2: schema-prompted extraction | LLM에게 JAO 카드 양식을 보여주고 그 형식대로 뽑게 한다 | JSON 구조는 좋아질 가능성 |
| B3: retrieval-augmented schema extraction | 입력 문서와 관련된 NCS/PCF/O*NET/스키마만 찾아서 같이 준다 | 엉뚱한 표준에 연결될 가능성 감소 |
| B4: EDC-style pipeline | 먼저 뽑고, 정의하고, 기존 표준 URI에 정규화한다 | 중복 노드 감소, 표준 연결 강화 |
| B5: validator + human-in-loop | 자동 검증과 전문가 검수를 붙인다 | 실제 운영 가능한 품질 목표 |

### 2.5 평가 지표를 쉬운 말로

| 평가 지표 | 쉬운 의미 |
|---|---|
| JSON Schema validity | 카드 양식에 맞게 썼는가 |
| URI/reference integrity | 화살표가 존재하는 카드 주소를 가리키는가 |
| entity precision | 뽑은 카드 중 맞는 카드 비율 |
| entity recall | 정답 카드 중 얼마나 많이 찾아냈는가 |
| relation precision | 만든 화살표 중 맞는 화살표 비율 |
| relation recall | 있어야 할 화살표 중 얼마나 만들었는가 |
| F1 | precision과 recall의 균형 점수 |
| canonicalization accuracy | 같은 뜻을 중복 카드로 만들지 않았는가 |
| edge precision@k | 추천한 상위 k개 연결이 전문가 판단과 맞는가 |
| graph consistency | 순환, 끊어진 주소, 위험 규칙 위반이 없는가 |
| expert review time reduction | 사람이 검수하는 시간이 얼마나 줄었는가 |

### 2.6 연구자가 실제로 먼저 할 일

처음에는 전체 8만 MB 규모를 한 번에 보지 말고 다음 작은 태스크부터 시작하는 것이 맞다.

1. `06_suju_focus/ncs_suju_units.json`에서 수주 관련 NCS 51개를 읽는다.
2. 그중 `inTargetDomain=true`인 일반영업, 통신판매, IT기술영업 항목을 1차 gold 후보로 둔다.
3. `06_suju_focus/pcf_3.0_market_and_sell.json`에서 PCF 3.0 하위 프로세스를 읽는다.
4. `06_suju_focus/jao_sales_agent_example.json`에서 `sales-b2b`와 5개 Action을 읽는다.
5. 쉬플리/제안서 문서 한 문단을 넣고, LLM이 어떤 Task/Action/Artifact/Edge를 만드는지 본다.
6. 결과가 JAO schema에 맞는지 검사한다.
7. 전문가가 맞다/아니다를 표시한다.
8. B1, B2, B3, B4, B5를 비교한다.

이렇게 하면 H1은 추상적인 온톨로지 연구가 아니라 “업무 문서를 정해진 업무 카드와 화살표로 자동 변환하는 실험”이 된다.

## 3. 전체 데이터 지도

작업 경로에는 크게 원본 패키지와 연구자가 만든 설명 문서가 있다.

| 경로 | 의미 |
|---|---|
| `handoff-hanyang/` | AX가 전달한 원본 데이터 패키지 |
| `ontology_llm_research_plan.md` | 이전에 작성한 연구계획서 |
| `beginner_ontology_data_guide.md` | 이 문서 |
| `.vscode/settings.json` | VS Code에서 JSON 줄바꿈을 켜는 작업공간 설정 |
| `.DS_Store` | macOS 메타파일, 연구에는 사용하지 않음 |
| `한양대_전달_데이터_패키지_해설서.docx` | 전달 패키지 해설서 사본 |

이하에서는 `handoff-hanyang` 아래의 모든 연구 데이터 파일을 정리한다.

## 4. `handoff-hanyang/manifest.json`

| 항목 | 내용 |
|---|---|
| 역할 | 전체 파일 목록, 건수, 용량, 출처, 라이선스를 담은 목차 |
| 왜 중요한가 | 논문 공개 가능 범위를 판단할 때 기준이 된다 |
| records | manifest 자체는 1개 JSON 객체 |

예시:

```json
{
  "builtAt": "2026-06-12",
  "scope": "전체 데이터 (full dataset) + 수주 우선 활용 선별본"
}
```

주의:

- APQC PCF 계열은 연구 내부 사용 가능하지만 원문 재배포 주의.
- O*NET은 CC-BY 4.0로 출처 표기 후 공개 가능.
- NCS와 국가법령 계열은 공공데이터 성격.

## 5. `01_ncs`: 한국 국가직무능력표준

NCS는 “사람이 어떤 직무 능력을 갖춰야 하는가”를 정리한 표준이다. 온톨로지에서는 직무와 능력의 뼈대 역할을 한다.

### 5.1 NCS 계층 구조

```text
대분류 L1
  -> 중분류 L2
    -> 소분류 L3
      -> 세분류 L4
        -> 능력단위
```

수주 예시:

```text
영업판매
  -> 영업
    -> 일반·해외영업
      -> 일반영업
        -> 영업 제안
```

### 5.2 파일별 정리

| 파일 | records | 핵심 필드 | 쉬운 설명 | 연구 활용 |
|---|---:|---|---|---|
| `01_ncs/ncs_lclas.json` | 192 | `NCS_LCLAS_CD`, `NCS_LCLAS_CDNM`, `USG_YN` | NCS 대분류 | 큰 직무 영역 선택 |
| `01_ncs/ncs_mclas.json` | 665 | `NCS_MCLAS_CD`, `NCS_MCLAS_CDNM` | 중분류 | 대분류 아래 하위 영역 |
| `01_ncs/ncs_sclas.json` | 2,239 | `NCS_SCLAS_CD`, `NCS_SCLAS_CDNM` | 소분류 | 더 구체적인 직무 영역 |
| `01_ncs/ncs_dclas.json` | 2,165 | `NCS_SUBD_CD`, `NCS_SUBD_CDNM`, `DUTY_DEF` | 세분류, 직무 정의 포함 | 직무 설명 gold 후보 |
| `01_ncs/ncs_unit.json` | 28,666 | `NCS_CL_CD`, `COMPE_UNIT_NAME`, `COMPE_UNIT_DEF`, `COMPE_UNIT_LEVEL` | 능력단위 전체 | H1의 Task 후보 |

### 5.3 실제 예시

`ncs_dclas.json`의 일반영업 예시:

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

`ncs_unit.json`의 수주 관련 예시:

```json
{
  "NCS_CL_CD": "1001010105_20v2",
  "COMPE_UNIT_NAME": "영업 제안",
  "COMPE_UNIT_DEF": "영업 제안이란 계약 체결을 위하여 고객이 요구하는 조건에 맞는 상품을 제안하는 능력이다.",
  "COMPE_UNIT_LEVEL": 3
}
```

### 5.4 분포

| 수준 | 건수 | 해석 |
|---:|---:|---|
| 1 | 9 | 기초 수준 |
| 2 | 2,860 | 초급 실행 |
| 3 | 6,968 | 실무 실행 |
| 4 | 6,499 | 중급 실무 |
| 5 | 8,214 | 중상급/관리 업무 |
| 6 | 2,717 | 고급 업무 |
| 7 | 1,219 | 전략/전문가 업무 |
| 8 | 180 | 최고난도 업무 |

H1에서는 `COMPE_UNIT_NAME`을 Task 이름 후보로, `COMPE_UNIT_DEF`를 Task 설명 후보로 쓴다.

## 6. `02_pcf`: APQC PCF 프로세스

PCF는 “회사의 업무 프로세스 지도”다. NCS가 사람의 능력을 말한다면, PCF는 회사 업무가 어떤 큰 흐름으로 구성되는지를 말한다.

### 6.1 PCF를 이해하는 핵심

PCF의 `hid`는 계층 주소다.

```text
3.0 제품·서비스 마케팅 및 판매
  -> 3.5 영업 계획 개발·관리
    -> 3.5.7 현장 영업 수행
```

즉 `3.5.7`은 단순 ID가 아니라 `3.0 > 3.5 > 3.5.7`이라는 위치를 뜻한다.

### 6.2 파일별 정리

| 파일 | records | 핵심 필드 | 쉬운 설명 | 연구 활용 |
|---|---:|---|---|---|
| `02_pcf/pcf_data.json` | 2,017 | `pcfId`, `hid`, `nameEn`, `nameKo`, `level`, `parent`, `hasMetrics` | Cross-Industry PCF 전체 프로세스 | JAO Process 원천 |
| `02_pcf/pcf_metrics.json` | 3,284 | `metricId`, `hid`, `metricName`, `formula`, `units`, `metricNameKo` | PCF 성과지표 | H2/H3 평가 지표 후보 |
| `02_pcf/industries/*.json` | 20개 파일 | PCF와 같은 구조 | 산업별 PCF 변형 | 산업별 복제/차이 분석 |

### 6.3 `pcf_data.json` 예시

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

연구 해석:

- 이 프로세스는 PCF 3.0, 즉 Market and Sell 영역 아래에 있다.
- 수주/제안 업무를 회사 프로세스 관점에서 위치시킬 때 사용한다.

### 6.4 `pcf_metrics.json` 예시

```json
{
  "metricId": 109038,
  "hid": "3.0",
  "process": "Market and Sell Products and Services",
  "metricNameKo": "전사 FTE 대비 영업·마케팅 FTE 비율",
  "formulaKo": "((영업 기능 수행 FTE 수 + 마케팅 기능 수행 FTE 수) / 사업체 FTE 수) * 100.0",
  "unitsKo": "퍼센트"
}
```

연구 해석:

- Agent가 만든 결과가 실제 회사 KPI와 어떻게 연결되는지 평가할 때 쓸 수 있다.
- 예를 들어 영업 에이전트가 리드 우선순위를 잘 추천하는지, 영업 효율성이 개선되는지 평가할 때 metric 후보가 된다.

### 6.5 산업별 PCF 파일

| 파일 | records | level 분포 요약 | 설명 |
|---|---:|---|---|
| `aerospace-defense.json` | 2,318 | L1~L5 | 항공우주/방위 산업 프로세스 |
| `airline.json` | 2,058 | L1~L5 | 항공사 프로세스 |
| `automotive.json` | 2,179 | L1~L5 | 자동차 산업 프로세스 |
| `banking.json` | 2,027 | L1~L6 | 은행 산업, 일부 L6까지 있음 |
| `broadcasting.json` | 2,019 | L1~L5 | 방송 산업 |
| `city-government.json` | 2,100 | L1~L5 | 도시정부/공공행정 |
| `consumer-electronics.json` | 2,021 | L1~L5 | 소비자가전 |
| `consumer-products.json` | 1,997 | L1~L5 | 소비재 |
| `corrosion.json` | 1,846 | L1~L5 | 부식/방식 산업 |
| `cross-industry.json` | 2,017 | L1~L5 | 산업 공통 PCF |
| `downstream-petroleum.json` | 2,012 | L1~L5 | 다운스트림 석유 |
| `education.json` | 1,470 | L1~L5 | 교육기관/교육청 |
| `health-insurance.json` | 2,142 | L1~L6 | 건강보험 |
| `healthcare-provider.json` | 1,985 | L1~L5 | 의료 제공기관 |
| `life-sciences.json` | 1,950 | L1~L5 | 생명과학 |
| `pc-insurance.json` | 1,997 | L1~L6 | 손해보험 |
| `retail.json` | 1,708 | L1~L5 | 리테일 |
| `telecommunications.json` | 1,251 | L1~L4 | 통신 |
| `upstream-petroleum.json` | 1,810 | L1~L5 | 업스트림 석유 |
| `utilities.json` | 2,073 | L1~L5 | 유틸리티 |

주의:

- APQC PCF 계열은 연구 내부 사용 가능하지만 원문 재배포는 피해야 한다.
- 논문에는 긴 원문 대신 `hid`, 통계, 평가 결과 중심으로 쓰는 것이 안전하다.

## 7. `03_onet`: O*NET 직업 데이터

O*NET은 미국 노동부의 직업 데이터다. 직업별로 실제 task, skill, knowledge, ability가 들어 있다.

| 파일 | records | 핵심 필드 | 쉬운 설명 | 연구 활용 |
|---|---:|---|---|---|
| `03_onet/onet_occupations_full.json` | 1,016 직업 | `socCode`, `title`, `description`, `tasks`, `skills`, `knowledge`, `abilities` | 직업별 실제 과업과 역량 | NCS보다 더 구체적인 task 보강 |

예시:

```json
{
  "socCode": "41-4011.00",
  "title": "Sales Representatives, Wholesale and Manufacturing, Technical and Scientific Products",
  "jobZone": 4,
  "tasks": [
    "Negotiate prices or terms of sales or service agreements.",
    "Prepare and submit sales contracts for orders."
  ],
  "skills": ["Persuasion", "Negotiation", "Service Orientation"]
}
```

연구 해석:

- NCS의 `기술영업 제안 작업`은 추상적이다.
- O*NET은 “가격 협상”, “계약서 제출”, “고객 질문 답변”처럼 더 구체적인 행동 문장을 제공한다.
- 이 문장들은 Agent Action 후보를 만들 때 유용하다.

## 8. `04_jao`: AX 직무 에이전트 온톨로지

JAO는 이 패키지의 중심이다. NCS, PCF, O*NET 등을 Agent가 사용할 수 있는 통합 형식으로 바꾼 것이다.

### 8.1 `04_jao/jao-spec.md`

| 항목 | 내용 |
|---|---|
| 역할 | JAO 온톨로지 명세서 |
| 핵심 내용 | 5계층 구조, 클래스 카탈로그, 관계 술어, 검증 규칙 |
| 연구 활용 | 논문 방법론의 schema 설명 근거 |

JAO의 핵심 원칙:

1. 자유 텍스트가 아니라 객체와 관계를 검색한다.
2. Agent는 사전 정의된 Action만 호출한다.
3. confidence와 사람 검수로 자동화 수준을 조절한다.
4. 표준 스키마와 그래프를 기반으로 운영한다.

### 8.2 `04_jao/schemas`: 카드 양식

스키마는 “각 카드가 어떤 필드를 가져야 하는지”를 정한 양식이다.

| 파일 | title | 쉬운 설명 |
|---|---|---|
| `_base.schema.json` | JAO Base Entity | 모든 JAO 카드의 공통 필드 |
| `action.schema.json` | Action | Agent가 실행할 수 있는 행동 양식 |
| `agent.schema.json` | Agent | 직무 에이전트 persona 양식 |
| `artifact.schema.json` | Artifact | 보고서, 제안서, 계약서 같은 산출물 양식 |
| `concept.schema.json` | Concept | 직무/개념 노드 양식 |
| `document.schema.json` | Document | 외부 문서 메타데이터 양식 |
| `event.schema.json` | Event | workflow/action trigger 양식 |
| `mapping-edge.schema.json` | MappingEdge | 표준 간 의미 매핑 양식 |
| `metric.schema.json` | Metric | KPI/성과지표 양식 |
| `policy.schema.json` | Policy | 규제를 prompt/guardrail로 바꾼 양식 |
| `process.schema.json` | Process | PCF 프로세스 양식 |
| `regulation.schema.json` | Regulation | 법령/규제 양식 |
| `risk.schema.json` | Risk | 위험 요인 양식 |
| `role.schema.json` | Role | 승인자/권한자 역할 양식 |
| `skill.schema.json` | Skill | Agent가 장착하는 역량 모듈 양식 |
| `task.schema.json` | Task | NCS/O*NET 작업 양식 |
| `term.schema.json` | Term | 다국어 용어 사전 양식 |
| `tool.schema.json` | Tool | 소프트웨어/시스템 도구 양식 |
| `workflow.schema.json` | Workflow | 여러 Action을 묶은 업무 흐름 양식 |

H1에서 schema는 매우 중요하다. LLM에게 “아무렇게나 뽑아라”가 아니라 “이 양식에 맞춰 뽑아라”라고 지시하기 때문이다.

### 8.3 `04_jao/instances`: 실제 카드 데이터

| 파일 | records | 핵심 의미 | 대표 예시 | 연구 활용 |
|---|---:|---|---|---|
| `Action.json` | 51 | Agent가 호출할 수 있는 행동 | `캠페인 분석`, `제안서 작성` | H2 실행 단위 |
| `Agent.json` | 10 | 직무별 AI 에이전트 | `B2B 영업 에이전트` | H2 persona |
| `Artifact.json` | 42 | 산출물 템플릿 | `제안서/RFP 응답` | output 구조 |
| `Concept.json` | 1,711 | NCS/O*NET 개념 | `IT기술영업` | 직무 개념 |
| `Document.json` | 163 | 가이드라인 문서 메타 | PDF URL, hash, chunkCount | 외부 문서 연결 |
| `Metric.json` | 3,284 | KPI | `판매주문 정확한 문서화율` | 성과 평가 |
| `Policy.json` | 1 | 정책/가드레일 | SOX 4-eye rule | 규제→검증 prompt |
| `Process.json` | 2,019 | PCF 프로세스 | `pcf-3.0` | 기업 프로세스 |
| `Regulation.json` | 1,371 | 한국 법령 | 표시·광고법 등 | compliance |
| `Task.json` | 18,977 | NCS/O*NET 작업 | `기술영업 전략수립` | H1 추출 대상 |
| `Tool.json` | 93 | 업무 도구 | `OpenAI API`, `Salesforce` | Action 실행 도구 |

### 8.4 핵심 예시

`Concept.json`:

```json
{
  "$id": "jao://Concept/ncs/20010501",
  "class": "Concept",
  "label": {"ko": "IT기술영업"},
  "definition": "IT기술영업은 사업수주를 위하여 정보기술 관련 전반적인 지식을 바탕으로 고객 관리 및 영업기회를 창출하고 고객의 요구에 적합한 솔루션 제안을 통해 협상, 계약, 판매 및 사후관리를 수행하는 일이다."
}
```

`Action.json`:

```json
{
  "$id": "jao://Action/agent/draft_proposal",
  "label": {"ko": "제안서 작성"},
  "category": "sales.generate",
  "inputs": ["accountId", "scope", "budget"],
  "outputs": ["proposalDoc"],
  "riskLevel": "medium",
  "approvers": ["sales-mgr"],
  "tools": ["jao://Tool/tool/openai-api", "jao://Tool/tool/figma"]
}
```

연구 해석:

- `Concept`는 업무가 속한 직무 영역이다.
- `Task`는 해야 하는 작업이다.
- `Action`은 AI 에이전트가 실행할 수 있는 행동이다.
- `Tool`은 행동에 필요한 도구다.
- `Artifact`는 행동의 결과물이다.
- `Policy`와 `Regulation`은 안전장치다.

## 9. `05_mappings`: 표준 간 연결과 전체 그래프

이 폴더는 노드 사이의 연결을 담는다.

| 파일 | records | 핵심 필드 | 쉬운 설명 | 연구 활용 |
|---|---:|---|---|---|
| `mapping_edges_all.json` | 5,055 | `from`, `to`, `predicate`, `confidence`, `evidence` | 표준 간 자동 매핑 후보 | H1 검수/정제 대상 |
| `graph_edges_all.json` | 27,962 | `from`, `to`, `predicate`, `confidence` | 전체 그래프 엣지 | Neo4j/GraphRAG 적재 |

`mapping_edges_all.json`의 predicate 분포:

| predicate | 건수 | 의미 |
|---|---:|---|
| `governedBy` | 3,842 | 직무/Task/Concept가 법령에 의해 규율됨 |
| `mapsTo` | 817 | 다른 표준의 노드와 의미상 연결됨 |
| `related` | 396 | 문서/가이드라인 등과 관련됨 |

예시:

```json
{
  "from": "jao://Concept/onet/41-9099.00",
  "predicate": "mapsTo",
  "to": "jao://Process/pcf/pcf-3.5.7",
  "confidence": 0.1674,
  "mappingType": "related"
}
```

주의:

- 자동 생성 매핑이므로 정답으로 바로 쓰면 안 된다.
- confidence가 낮은 것은 전문가 검수 queue로 보내는 것이 좋다.

`graph_edges_all.json`의 주요 predicate:

| predicate | 건수 | 의미 |
|---|---:|---|
| `requires` | 18,977 | Task가 Concept를 요구 |
| `governedBy` | 3,842 | 규제 연결 |
| `partOf` | 2,004 | PCF 프로세스 상하위 |
| `broader` | 1,664 | NCS/O*NET 개념 상하위 |
| `mapsTo` | 817 | 표준 간 매핑 |
| `uses` | 83 | Action이 Tool 사용 |
| `actions` | 51 | Agent가 Action 보유 |

## 10. `06_suju_focus`: 수주/제안 1차 실증 데이터

전체 데이터 중 수주/제안 도메인만 잘라둔 시작점이다.

| 파일 | records | 쉬운 설명 | 연구 활용 |
|---|---:|---|---|
| `ncs_suju_units.json` | 51 | 수주 관련 NCS 능력단위 | H1 gold 후보 |
| `pcf_3.0_market_and_sell.json` | 213 | PCF 3.0 Market and Sell 하위 프로세스 | H1/H2 프로세스 후보 |
| `jao_sales_agent_example.json` | 6 | B2B 영업 Agent 1개 + Action 5개 | H2 실험 베이스라인 |

### 10.1 `ncs_suju_units.json`

예시:

```json
{
  "subdCode": "20010501",
  "subdName": "IT기술영업",
  "unitCode": "05",
  "unitName": "수주전략수립",
  "unitDefinition": "수주전략수립이란 사업의 수주를 위하여 고객 요구, 경쟁사 분석, 제안 평가 우위 요소를 도출하여 전략을 수립하는 능력이다.",
  "level": 7
}
```

### 10.2 `pcf_3.0_market_and_sell.json`

예시:

```json
{
  "hid": "3.0",
  "nameKo": "제품·서비스 마케팅 및 판매",
  "level": 1,
  "parent": null
}
```

### 10.3 `jao_sales_agent_example.json`

예시:

```json
{
  "$id": "jao://Agent/agent/sales-b2b",
  "label": {"ko": "B2B 영업 에이전트"},
  "actions": [
    "jao://Action/agent/score_lead",
    "jao://Action/agent/brief_account",
    "jao://Action/agent/draft_proposal",
    "jao://Action/agent/forecast_pipeline",
    "jao://Action/agent/schedule_meeting"
  ],
  "guardrails": [
    "가격 할인 한도 검증",
    "경쟁사 비방 금지",
    "서약서 없는 정보 공유 금지"
  ]
}
```

수주 실험에서는 이 폴더부터 시작하면 된다. 전체 데이터는 크고 넓기 때문에 처음부터 모두 쓰면 연구 설계가 흐려진다.

## 11. 기타 파일

| 파일 | 설명 | 사용 여부 |
|---|---|---|
| `handoff-hanyang/한양대_전달_데이터_패키지_해설서.docx` | AX가 제공한 데이터 패키지 해설서 | 온보딩/인용 참고 |
| `한양대_전달_데이터_패키지_해설서.docx` | 루트에 있는 같은 해설서 사본 | 중복 사본 |
| `ontology_llm_research_plan.md` | 연구계획서 | 계속 업데이트 가능 |
| `.vscode/settings.json` | JSON 파일 줄바꿈 설정 | 편집 편의 |
| `.DS_Store` | macOS 시스템 파일 | 무시 |

## 12. 데이터 간 연결을 하나의 예로 보기

업무: “고객 요구사항을 분석해서 제안서 초안을 작성한다.”

| 단계 | 쓰는 데이터 | 찾는 항목 |
|---:|---|---|
| 1 | NCS | `수주전략수립`, `기술영업 제안 작업` |
| 2 | PCF | `3.0 Market and Sell`, `3.5 영업 계획 개발·관리` |
| 3 | O*NET | 계약 협상, 가격 조건 제시, 고객 질문 응답 task |
| 4 | JAO Concept | `jao://Concept/ncs/20010501 IT기술영업` |
| 5 | JAO Task | `기술영업 전략수립` 또는 신규 Task 후보 |
| 6 | JAO Agent | `jao://Agent/agent/sales-b2b` |
| 7 | JAO Action | `jao://Action/agent/draft_proposal` |
| 8 | JAO Tool | `openai-api`, `figma` |
| 9 | JAO Artifact | `proposal-rfp` |
| 10 | Regulation/Policy | 가격, 광고, 하도급, 소비자 관련 guardrail |
| 11 | Mapping/Graph Edge | 위 노드들을 화살표로 연결 |

최종적으로 만들고 싶은 것은 이런 구조다.

```text
IT기술영업 Concept
  <-requires-
수주전략수립 Task
  ->mapsTo/enables->
PCF 3.5 영업 계획 개발·관리

sales-b2b Agent
  ->actions->
draft_proposal Action
  ->uses->
openai-api Tool
  ->produces->
proposal-rfp Artifact
  ->requiresApproval->
sales-mgr
```

## 13. 연구 진행을 위한 현실적인 첫 번째 태스크

초보 연구자가 바로 시작할 수 있는 첫 태스크는 다음이다.

### 태스크: 수주 문장 50개를 JAO 카드와 화살표로 바꾸기

입력:

- `06_suju_focus/ncs_suju_units.json`
- `06_suju_focus/pcf_3.0_market_and_sell.json`
- `06_suju_focus/jao_sales_agent_example.json`
- 쉬플리/제안서/수주 관련 문장 50개

출력:

- Task 후보
- Action 후보
- Artifact 후보
- Concept 연결
- Process 연결
- Tool 연결
- 승인/위험 규칙

평가:

- JSON 양식이 맞는가
- 기존 JAO URI와 잘 연결했는가
- 사람이 봤을 때 맞는가
- LLM 단독, 스키마 포함, 검색 포함, 검증 포함 방식 중 무엇이 가장 좋은가

이 작업이 H1의 최소 실행 버전이다.

## 14. 이 문서 기준 추천 작업 순서

1. `06_suju_focus`만 읽고 수주 도메인 mini ontology를 손으로 이해한다.
2. `04_jao/schemas/task.schema.json`, `action.schema.json`, `agent.schema.json`, `artifact.schema.json`만 먼저 읽는다.
3. `04_jao/instances/Agent.json`, `Action.json`, `Artifact.json`, `Tool.json`을 연결해서 B2B 영업 Agent를 이해한다.
4. `01_ncs/ncs_unit.json`에서 `20010501` 관련 능력단위를 찾는다.
5. `02_pcf/pcf_data.json`에서 `3.0`, `3.5` 관련 프로세스를 찾는다.
6. `05_mappings`는 정답이 아니라 검수 대상 pool로 본다.
7. H1 실험은 작은 문장 50개로 시작한다.
8. H2 실험은 `sales-b2b` Agent가 제안서/리드/미팅/forecast 업무를 수행하게 해서 일반 RAG와 비교한다.

## 15. 결론

이 데이터는 처음 보면 파일이 많지만, 연구 관점에서는 다음 네 덩어리로 보면 된다.

1. 원천 표준: NCS, PCF, O*NET
2. 통합 온톨로지: JAO schema와 instances
3. 연결 데이터: MappingEdge와 GraphEdge
4. 실험 출발점: `06_suju_focus`

H1은 이 네 덩어리를 이용해 “업무 문서에서 업무 카드와 관계 화살표를 자동으로 만들어내는가”를 검증하는 연구다. 가장 먼저 할 일은 수주/제안 도메인에서 작은 입력 문장들을 JAO 형식의 Task, Action, Artifact, Process, Concept, Edge로 변환해 보고, 그 결과를 전문가가 평가하는 것이다.
