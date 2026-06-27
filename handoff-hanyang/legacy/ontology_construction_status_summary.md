# AX-HYU 온톨로지 구축 현황 종합 정리

작성일: 2026-06-16  
대상 경로: `/home/minjoo/AX_서울펠로우`  
주요 데이터 경로: `/home/minjoo/AX_서울펠로우/handoff-hanyang`

## 1. 가장 중요한 결론

현재 데이터는 “온톨로지가 전혀 없는 상태”가 아니다. AX가 이미 원천 데이터 일부를 JAO 형식으로 정규화해 두었다.

다만 이것을 “연구용으로 완성된 정답 온톨로지”라고 보면 안 된다.

정확한 현재 상태는 다음과 같다.

> JAO 스키마와 상당수 인스턴스는 이미 있다.  
> PCF와 O*NET은 JAO로 비교적 잘 변환되어 있다.  
> NCS 분류체계는 JAO Concept로 구축되어 있다.  
> 그러나 NCS 능력단위 Task는 전체가 아니라 일부만 JAO Task로 들어가 있다.  
> 표준 간 연결 edge는 자동 생성 후보이므로 연구자가 검수해야 한다.  
> 수주/제안 연구에서는 기존 JAO를 초안으로 사용하고, 핵심 Task와 edge를 보강해야 한다.

한 문장으로 정리하면:

```text
현재 온톨로지는 "AX가 만든 JAO 초안 + 자동 매핑 후보"이고,
연구자가 해야 할 일은 이를 수주/제안 도메인에 맞게 보강·검수하여
연구용 온톨로지와 정답셋으로 만드는 것이다.
```

## 2. 전체 데이터 구조

전체 데이터는 크게 원천 데이터, JAO 온톨로지, 매핑 데이터, 수주/제안 선별본으로 나뉜다.

| 폴더 | 역할 | 쉽게 말하면 |
|---|---|---|
| `01_ncs` | NCS 원천 데이터 | 한국 직무 능력 표준 |
| `02_pcf` | PCF 원천 데이터 | 회사 업무 프로세스 표준 |
| `03_onet` | O*NET 원천 데이터 | 미국 직업/과업 표준 |
| `04_jao` | AX JAO 온톨로지 | 원천 데이터를 통합한 온톨로지 형식 |
| `05_mappings` | 표준 간 edge | NCS-PCF-O*NET-법령 연결 후보 |
| `06_suju_focus` | 수주/제안 선별본 | 1차 연구 도메인 |

중요한 구분은 다음이다.

```text
01_ncs, 02_pcf, 03_onet
= 원천 데이터

04_jao/instances
= 원천 데이터를 JAO 형식으로 바꾼 인스턴스

05_mappings
= 노드와 노드를 연결한 edge
```

## 3. 온톨로지를 구성하는 기본 개념

온톨로지는 어렵게 생각할 필요가 없다. 이 연구에서 온톨로지는 다음 세 가지로 보면 된다.

| 구성 | 의미 | 예시 |
|---|---|---|
| Schema | 어떤 종류의 카드를 만들지 정한 양식 | Task는 id, label, description을 가져야 함 |
| Node / Instance | 실제 카드 | `수주전략수립`, `영업 전략 수립`, `draft_proposal` |
| Edge | 카드 사이 연결선 | `수주전략수립 mapsTo 영업 전략 수립` |

예를 들어 다음은 온톨로지의 아주 작은 조각이다.

```text
[수주전략수립]
  mapsTo -> [3.4 영업 전략 수립]
  supportedBy -> [brief_account]
  supportedBy -> [draft_proposal]

[draft_proposal]
  produces -> [proposal-rfp]
  requires -> [가격 한도 검증]
  requiresApproval -> [sales-mgr]
```

이 구조가 있으면 LLM 또는 Agent가 단순히 문서를 읽는 것이 아니라 다음을 알 수 있다.

```text
이 문장은 어떤 업무인가?
그 업무는 회사 프로세스상 어디에 있는가?
어떤 Agent Action으로 실행할 수 있는가?
어떤 산출물이 나와야 하는가?
어떤 승인과 규칙을 지켜야 하는가?
```

## 4. `schemas`와 `instances`의 차이

`04_jao` 안에는 `schemas`와 `instances`가 있다. 둘은 완전히 다르다.

| 구분 | 의미 | 예시 |
|---|---|---|
| `schemas` | 양식, 규칙, 틀 | Task는 어떤 필드를 가져야 하는가 |
| `instances` | 실제 데이터 카드 | `jao://Task/ncs/02.5 기술영업 전략수립` |

비유하면 다음과 같다.

```text
schema = 빈 이력서 양식
instance = 실제 사람이 작성한 이력서
```

JAO 스키마는 19개가 있다.

```text
_base, action, agent, artifact, concept, document, event,
mapping-edge, metric, policy, process, regulation, risk,
role, skill, task, term, tool, workflow
```

그러나 스키마가 있다고 해서 해당 인스턴스가 모두 만들어진 것은 아니다. 예를 들어 `skill.schema.json`은 있지만 현재 `instances/Skill.json`은 없다.

## 5. 현재 구축 현황 요약

확인한 실제 수치는 다음과 같다.

| 영역 | 원천 데이터 | JAO 변환 결과 | 판단 |
|---|---:|---:|---|
| NCS 분류체계 | L1~L4 원천 다수 | NCS Concept 672개 | 구축됨 |
| NCS 능력단위 | 28,666행, 고유 `NCS_CL_CD` 4,659개 | NCS Task 336개 | 부분 구축 |
| PCF Process | 2,017개 | JAO Process 고유 `hid` 2,017개 | 거의 구축됨 |
| PCF Metric | 3,284개 | JAO Metric 3,284개 | 구축됨 |
| O*NET 직업 | 1,016개 | O*NET Concept 1,039개 | 구축됨 |
| O*NET Task | 18,641개 | JAO Task 18,641개 | 구축됨 |
| Agent | AX 자산 | JAO Agent 10개 | 구축됨 |
| Action | AX 자산 | JAO Action 51개 | 구축됨 |
| MappingEdge | 자동 매핑 | 5,055개 | 검수 필요 |
| Graph Edge | 전체 그래프 edge | 27,962개 | 활용 가능, 검수 필요 |

가장 중요한 판단은 다음이다.

```text
PCF와 O*NET은 온톨로지화가 상당히 되어 있다.
NCS는 분류체계는 되어 있지만 능력단위 Task는 부족하다.
수주/제안 연구에서는 NCS Task 보강이 핵심이다.
```

## 6. NCS 온톨로지 구축 현황

### 6.1 NCS 원천 데이터

NCS 원천 파일은 다음과 같다.

| 파일 | 의미 | 건수 |
|---|---|---:|
| `01_ncs/ncs_lclas.json` | 대분류 | 192행 |
| `01_ncs/ncs_mclas.json` | 중분류 | 665행 |
| `01_ncs/ncs_sclas.json` | 소분류 | 2,239행 |
| `01_ncs/ncs_dclas.json` | 세분류, 직무 | 2,165행 |
| `01_ncs/ncs_unit.json` | 능력단위 | 28,666행 |

원천 데이터에는 연도, 버전, 현행 여부가 섞여 있어 행 수가 실제 고유 개념 수보다 많다.

고유 코드 기준으로 보면 다음과 같다.

| 구분 | 고유 수 |
|---|---:|
| NCS L1 | 24 |
| NCS L2 | 84 |
| NCS L3 | 286 |
| NCS L4 | 278 |
| NCS 능력단위 고유 `NCS_CL_CD` | 4,659 |

### 6.2 NCS 분류체계는 JAO Concept로 변환됨

NCS 분류체계는 `04_jao/instances/Concept.json`에 들어 있다.

JAO NCS Concept 수는 다음과 같다.

| 코드 길이 | 의미 | 건수 |
|---:|---|---:|
| 2자리 | L1 대분류 | 24 |
| 4자리 | L2 중분류 | 84 |
| 6자리 | L3 소분류 | 286 |
| 8자리 | L4 세분류 | 278 |
| 합계 | NCS Concept | 672 |

예를 들어 `IT기술영업`은 다음처럼 변환되어 있다.

원천 NCS:

```json
{
  "NCS_LCLAS_CD": "20",
  "NCS_LCLAS_CDNM": "정보통신",
  "NCS_MCLAS_CD": "01",
  "NCS_MCLAS_CDNM": "정보기술",
  "NCS_SCLAS_CD": "05",
  "NCS_SCLAS_CDNM": "정보기술영업",
  "NCS_SUBD_CD": "01",
  "NCS_SUBD_CDNM": "IT기술영업",
  "DUTY_DEF": "IT기술영업은 사업수주를 위하여..."
}
```

JAO Concept:

```json
{
  "$id": "jao://Concept/ncs/20010501",
  "id": "20010501",
  "class": "Concept",
  "namespace": "ncs",
  "label": {
    "ko": "IT기술영업"
  },
  "broader": [
    "jao://Concept/ncs/200105"
  ],
  "definition": "IT기술영업은 사업수주를 위하여..."
}
```

즉 변환 규칙은 다음과 같다.

| NCS 원천 필드 | JAO 필드 |
|---|---|
| 분류 코드 조합 | `$id`, `id`, `notation` |
| 분류명 | `label.ko` |
| 직무 정의문 | `description.ko`, `definition` |
| 상위 분류 | `broader` |
| 출처 | `source` |

### 6.3 NCS 능력단위는 부분 구축 상태

문제는 NCS 능력단위다.

원천 NCS 능력단위는 고유 `NCS_CL_CD` 기준 4,659개인데, JAO Task에 들어간 NCS Task는 336개뿐이다.

```text
NCS 원천 능력단위 고유 코드: 4,659개
JAO 안의 NCS Task: 336개
```

따라서 NCS 능력단위 온톨로지는 전체 구축이 아니다.

예를 들어 `기술영업 전략수립`은 JAO Task로 존재한다.

```json
{
  "$id": "jao://Task/ncs/02.5",
  "id": "02.5",
  "class": "Task",
  "namespace": "ncs",
  "label": {
    "ko": "기술영업 전략수립"
  },
  "description": {
    "ko": "기술영업 전략수립이란 시장 현황 정보를 바탕으로..."
  },
  "unitCode": "02",
  "levelL": 6,
  "requires": [
    "jao://Concept/ncs/20010501"
  ]
}
```

그러나 수주/제안 핵심 항목 중 아래는 현재 정확한 JAO Task로 확인되지 않았다.

```text
수주전략수립
기술영업 제안 작업
사업계약 협상
영업 제안
영업 계약체결관리
```

이것이 수주/제안 연구에서 가장 중요한 보강 지점이다.

## 7. PCF 온톨로지 구축 현황

PCF는 가장 잘 변환된 축이다.

| 항목 | 원천 | JAO |
|---|---:|---:|
| PCF Process | 2,017개 | 고유 `hid` 2,017개 |
| PCF Metric | 3,284개 | 3,284개 |

PCF Process는 `04_jao/instances/Process.json`에 들어 있다.

예를 들어 원천 PCF `3.5`는 다음과 같다.

```json
{
  "hid": "3.5",
  "nameKo": "영업 계획 개발·관리",
  "nameEn": "Develop and manage sales plans",
  "level": 2,
  "parent": "3.0",
  "hasMetrics": true
}
```

JAO Process로는 다음처럼 바뀐다.

```json
{
  "$id": "jao://Process/pcf/pcf-3.5",
  "id": "pcf-3.5",
  "class": "Process",
  "namespace": "pcf",
  "label": {
    "ko": "영업 계획 개발·관리",
    "en": "Develop and manage sales plans"
  },
  "hid": "3.5",
  "level": 2,
  "partOf": "jao://Process/pcf/pcf-3.0",
  "source": {
    "type": "apqc",
    "ref": "APQC PCF v8.0 Cross-Industry"
  }
}
```

변환 규칙은 다음과 같다.

| PCF 원천 필드 | JAO 필드 |
|---|---|
| `hid` | `hid`, `$id`, `id` |
| `nameKo`, `nameEn` | `label.ko`, `label.en` |
| `descKo`, `descEn` | `description.ko`, `description.en` |
| `level` | `level` |
| `parent` | `partOf` |
| `pcfId` | `pcfId` |
| `hasMetrics` | `hasMetrics` |

주의할 점도 있다.

```text
Process.json에는 2,019행이 있지만 고유 hid는 2,017개다.
즉 2개 중복이 있다.
중복 hid: 9.0, 9.3
```

연구에는 큰 문제는 아니지만, 최종 그래프 적재 전에는 중복 정리가 필요하다.

## 8. O*NET 온톨로지 구축 현황

O*NET은 직업과 과업 기준으로 잘 변환되어 있다.

| 항목 | 원천 | JAO |
|---|---:|---:|
| O*NET 직업 | 1,016개 | O*NET Concept 1,039개 |
| O*NET Task | 18,641개 | O*NET Task 18,641개 |

O*NET 직업은 JAO Concept가 된다.

예:

```json
{
  "$id": "jao://Concept/onet/41-4011.00",
  "id": "41-4011.00",
  "class": "Concept",
  "namespace": "onet",
  "label": {
    "en": "Sales Representatives, Wholesale and Manufacturing, Technical and Scientific Products"
  },
  "scheme": "onet-soc",
  "notation": "41-4011.00",
  "broader": [
    "jao://Concept/onet/major-41"
  ]
}
```

O*NET task는 JAO Task가 된다.

```json
{
  "$id": "jao://Task/onet/11237",
  "id": "11237",
  "class": "Task",
  "namespace": "onet",
  "label": {
    "en": "Answer customers' questions about products, prices, availability, or credit terms."
  },
  "taskType": "Core",
  "requires": [
    "jao://Concept/onet/41-4011.00"
  ]
}
```

즉 O*NET 변환은 다음과 같다.

```text
O*NET occupation -> JAO Concept
O*NET task -> JAO Task
Task requires Occupation Concept
```

다만 O*NET의 `skills`, `knowledge`, `abilities`가 별도 JAO Skill 인스턴스로 모두 분리된 상태는 아니다. `skill.schema.json`은 있지만 현재 `instances/Skill.json`은 없다.

## 9. Agent와 Action 구축 현황

JAO는 단순 지식 온톨로지가 아니라 “에이전트 운영 온톨로지”다. 그래서 Agent와 Action이 중요하다.

현재 전체 JAO에는 다음이 있다.

| 파일 | 건수 | 의미 |
|---|---:|---|
| `04_jao/instances/Agent.json` | 10 | 직무 에이전트 |
| `04_jao/instances/Action.json` | 51 | 에이전트가 수행할 수 있는 행동 |

수주/제안 선별본에는 다음이 있다.

| 항목 | 값 |
|---|---|
| Agent | `sales-b2b` |
| Action | `score_lead`, `brief_account`, `draft_proposal`, `forecast_pipeline`, `schedule_meeting` |

핵심 Action은 `draft_proposal`이다.

```json
{
  "$id": "jao://Action/agent/draft_proposal",
  "id": "draft_proposal",
  "class": "Action",
  "label": {
    "ko": "제안서 작성"
  },
  "inputs": [
    {"name": "accountId", "type": "string", "required": true},
    {"name": "scope", "type": "string", "required": true},
    {"name": "budget", "type": "string", "required": true}
  ],
  "outputs": [
    {"name": "proposalDoc", "type": "string", "required": true}
  ],
  "preconditions": [
    "가격 한도 검증"
  ],
  "riskLevel": "medium",
  "approvers": [
    "sales-mgr"
  ],
  "tools": [
    "jao://Tool/tool/openai-api",
    "jao://Tool/tool/figma"
  ]
}
```

이 구조는 H2 실험에서 매우 중요하다.

일반 RAG는 그냥 문서를 검색해 답하지만, JAO Agent는 다음을 안다.

```text
제안서 작성에는 accountId, scope, budget이 필요하다.
출력은 proposalDoc이어야 한다.
가격 한도 검증이 필요하다.
riskLevel은 medium이다.
sales-mgr 승인이 필요하다.
```

## 10. Edge 구축 현황

온톨로지는 노드만 있으면 부족하다. 노드 사이 연결, 즉 edge가 있어야 한다.

현재 edge는 두 파일에 들어 있다.

| 파일 | 건수 | 의미 |
|---|---:|---|
| `05_mappings/mapping_edges_all.json` | 5,055 | 표준 간 자동 매핑 후보 |
| `05_mappings/graph_edges_all.json` | 27,962 | 전체 그래프 edge |

`graph_edges_all.json`의 주요 edge는 다음과 같다.

| predicate | 건수 | 의미 |
|---|---:|---|
| `requires` | 18,977 | Task가 Concept를 요구 |
| `governedBy` | 3,842 | 법령/규정 적용 |
| `partOf` | 2,004 | PCF 프로세스 상하위 |
| `broader` | 1,664 | Concept 상하위 |
| `mapsTo` | 817 | 표준 간 대응 |
| `related` | 396 | 관련 관계 |
| `uses` | 83 | Action이 Tool 사용 |
| `actions` | 51 | Agent가 Action 보유 |

예:

```json
{
  "from": "jao://Process/pcf/pcf-1.1.1.1",
  "to": "jao://Process/pcf/pcf-1.1.1",
  "predicate": "partOf",
  "confidence": 0.99
}
```

```json
{
  "from": "jao://Task/ncs/01.1",
  "to": "jao://Concept/ncs/24040401",
  "predicate": "requires",
  "confidence": 0.9
}
```

```json
{
  "from": "jao://Action/agent/analyze_campaign",
  "to": "jao://Tool/tool/powerbi",
  "predicate": "uses",
  "confidence": 0.9
}
```

## 11. MappingEdge는 자동 후보이므로 주의해야 함

`mapping_edges_all.json`은 특히 주의해야 한다.

상태는 다음과 같다.

| 상태 | 건수 |
|---|---:|
| `published` | 3,864 |
| `review` | 141 |
| `draft` | 1,050 |

출처는 크게 두 가지다.

| source ref | 건수 | 의미 |
|---|---:|---|
| `harvesters/_common/jao_writer.py` | 4,005 | 법령/문서 수집 및 JAO writer 기반 |
| `mapping/auto_mappings.json` | 1,050 | 자동 표준 매핑 |

NCS-PCF, O*NET-PCF 매핑은 confidence가 낮은 사례가 많다.

예:

```json
{
  "from": "jao://Concept/ncs/14070601",
  "to": "jao://Process/pcf/pcf-10.3",
  "predicate": "mapsTo",
  "confidence": 0.104,
  "evidence": "NCS '건설기계정비' → PCF '자산 유지보수'"
}
```

따라서 연구에서는 다음 원칙을 지켜야 한다.

```text
MappingEdge를 정답으로 쓰지 않는다.
MappingEdge는 후보로만 사용한다.
수주/제안 핵심 edge는 사람이 직접 검수한다.
검수된 edge만 gold label로 사용한다.
```

## 12. JAO로 바꾼 방식

현재 패키지 안에는 실제 변환 파이프라인 코드 전체가 포함되어 있지 않다. 하지만 `jao-spec.md`, `manifest.json`, 각 인스턴스의 `source.ref`를 보면 변환 방식은 추정할 수 있다.

핵심 방식은 다음이다.

```text
원천 JSON
→ JAO 공통 필드로 감싸기
→ class, namespace 부여
→ jao:// URI 부여
→ label, description 정리
→ source, confidence 추가
→ 계층 관계를 broader/partOf로 연결
→ Task와 Concept를 requires로 연결
→ 표준 간 자동 매핑을 MappingEdge로 생성
```

즉, 대부분은 LLM이 자유롭게 새 지식을 만든 것이 아니라 원천 데이터의 필드를 JAO 양식으로 정규화한 것이다.

### 12.1 공통 JAO 필드

거의 모든 JAO 인스턴스는 다음 필드를 가진다.

| 필드 | 의미 |
|---|---|
| `$id` | 전역 URI |
| `id` | 로컬 id |
| `class` | Concept, Task, Process 등 |
| `namespace` | ncs, pcf, onet, agent 등 |
| `version` | 버전 |
| `status` | draft, review, published, deprecated |
| `label` | 표시명 |
| `description` | 설명 |
| `source` | 원천 |
| `confidence` | 신뢰도 |

예:

```json
{
  "$id": "jao://Process/pcf/pcf-3.5",
  "id": "pcf-3.5",
  "class": "Process",
  "namespace": "pcf",
  "version": "1.0.0",
  "status": "draft",
  "label": {
    "ko": "영업 계획 개발·관리",
    "en": "Develop and manage sales plans"
  }
}
```

### 12.2 변환 방식 요약

| 원천 | JAO class | 핵심 변환 |
|---|---|---|
| NCS L1~L4 분류 | Concept | 코드, 명칭, 정의, 상위분류 |
| NCS 능력단위 일부 | Task | 능력단위명, 정의, 수준, 소속 세분류 |
| PCF Process | Process | hid, name, desc, level, parent |
| PCF Metric | Metric | metricId, metricName, formula, units, process |
| O*NET Occupation | Concept | socCode, title, description |
| O*NET Task | Task | taskId, task text, type, occupation |
| Agent Studio 자산 | Agent/Action | role, mission, input/output, tool, risk |
| 자동 매핑 | MappingEdge | from, to, predicate, confidence, evidence |

## 13. 수주/제안 데이터 현황

수주/제안 연구의 시작점은 `06_suju_focus`다.

| 파일 | 건수 | 의미 |
|---|---:|---|
| `ncs_suju_units.json` | 51 | 수주/제안 관련 NCS 후보 |
| `pcf_3.0_market_and_sell.json` | 213 | PCF 3.0 Market and Sell 프로세스 |
| `jao_sales_agent_example.json` | 6 | sales-b2b Agent 1개 + Action 5개 |

NCS 수주 후보 중 핵심 후보는 29개다.

| NCS 세분류 | 핵심 후보 수 | 의미 |
|---|---:|---|
| 일반영업 | 9 | 일반 영업 사이클 |
| 통신판매 | 10 | 판매 운영/상담 |
| IT기술영업 | 10 | B2B IT 수주/제안 핵심 |

특히 IT기술영업의 핵심 Task는 다음이다.

```text
20010501-01 기술영업시장 현황분석
20010501-02 기술영업 전략수립
20010501-03 기술영업 고객 현황분석
20010501-04 사전 기술영업
20010501-05 수주전략수립
20010501-06 기술영업 제안 작업
20010501-07 사업계약 협상
20010501-08 기술영업 사후관리
20010501-09 협력선관리
20010501-10 영업관리 지원
```

그러나 이 중 JAO Task로 정확히 확인된 것은 일부다.

```text
기술영업 전략수립 -> jao://Task/ncs/02.5
기술영업 사후관리 -> jao://Task/ncs/08.5
```

따라서 수주/제안 연구에서는 다음이 필요하다.

```text
수주전략수립
기술영업 제안 작업
사업계약 협상
영업 제안
영업 계약체결관리
```

이 항목들을 JAO Task로 보강하거나, 연구용 후보 Task로 별도 관리해야 한다.

## 14. 현재 온톨로지가 완성되었다고 볼 수 없는 이유

현재 데이터는 출발점으로는 충분하지만, 연구용 완성본은 아니다.

이유는 다음과 같다.

| 문제 | 설명 | 연구상 영향 |
|---|---|---|
| NCS Task 부족 | 능력단위 전체가 JAO Task로 들어가 있지 않음 | 수주 핵심 업무가 빠질 수 있음 |
| Task id 설계 약함 | 일부 NCS Task id가 `02.5`처럼 짧음 | 전체 NCS 고유 식별에 불리 |
| 자동 매핑 미검수 | NCS-PCF-O*NET 연결이 자동 후보 | 정답으로 사용 불가 |
| 수주 문장별 정답셋 없음 | 문장 -> Task/Process/Action 라벨이 없음 | H1 평가 불가 |
| 전문가 문서 미반영 | 쉬플리, RFP, 제안서 양식이 아직 별도 | 실제 업무 온톨로지 부족 |
| Skill 인스턴스 없음 | O*NET skill/knowledge가 별도 JAO Skill로 보이지 않음 | 역량 기반 분석은 추가 작업 필요 |

따라서 현재 상태를 이렇게 봐야 한다.

```text
스키마: 있음
원천 표준 데이터: 있음
JAO 인스턴스: 상당 부분 있음
수주/제안 미니 온톨로지: 아직 완성 아님
연구용 gold 정답셋: 아직 없음
```

## 15. 1차 온톨로지 구축 방향

1차 목표는 전체 AX 온톨로지를 완성하는 것이 아니다.

목표는 다음이다.

```text
B2B IT/AI 솔루션 수주·제안 미니 온톨로지 v0.1 구축
```

권장 범위는 다음이다.

| 구분 | 목표 수 |
|---|---:|
| NCS Task | 10개 |
| PCF Process | 10개 |
| Agent | 1개 |
| Action | 5개 |
| Artifact | 3개 |
| Rule/Policy | 5개 |
| 전체 노드 | 약 30개 |
| edge | 약 50개 |
| 라벨링 문장 | v0: 20개, v1: 50개, 최종: 200개 |

## 16. 1차 온톨로지에 넣을 노드

처음에는 노드 유형을 너무 많이 만들지 않는다.

필수 노드 유형은 다음 6개면 충분하다.

| Node 유형 | 의미 | 예시 |
|---|---|---|
| Task | 사람이 해야 하는 업무 능력 | 수주전략수립 |
| Process | 회사 업무 프로세스 위치 | 영업 전략 수립 |
| Agent | 업무를 수행하는 AI 역할 | sales-b2b |
| Action | Agent가 실행할 수 있는 행동 | draft_proposal |
| Artifact | 산출물 | proposal-rfp |
| Rule | 제약/승인/검증 조건 | 가격 한도 검증 |

예시 노드 목록:

| nodeType | nodeId | label | 출처 |
|---|---|---|---|
| Task | `20010501-05` | 수주전략수립 | NCS |
| Task | `20010501-06` | 기술영업 제안 작업 | NCS |
| Task | `20010501-07` | 사업계약 협상 | NCS |
| Process | `3.4` | 영업 전략 수립 | PCF |
| Process | `3.5` | 영업 계획 개발·관리 | PCF |
| Process | `3.5.1` | 리드·기회 관리 | PCF |
| Agent | `sales-b2b` | B2B 영업 에이전트 | JAO |
| Action | `brief_account` | 계정 브리핑 | JAO |
| Action | `draft_proposal` | 제안서 작성 | JAO |
| Action | `score_lead` | 리드 점수 계산 | JAO |
| Artifact | `proposal-rfp` | 제안서/RFP 산출물 | JAO |
| Rule | `price-limit-check` | 가격 한도 검증 | 연구자가 추가 |
| Role | `sales-mgr` | 영업관리자 | 연구자가 추가 |

## 17. 1차 온톨로지에 넣을 edge

처음에는 edge 유형도 제한해야 한다.

권장 edge는 다음이다.

| Edge | 의미 | 예시 |
|---|---|---|
| `mapsTo` | 표준 간 대응 | NCS Task -> PCF Process |
| `partOf` | 상하위 관계 | `3.5.1` -> `3.5` |
| `supports` | Action이 Task를 지원 | `draft_proposal` -> `기술영업 제안 작업` |
| `produces` | 산출물 생성 | `draft_proposal` -> `proposal-rfp` |
| `requires` | 사전 조건 필요 | `draft_proposal` -> `가격 한도 검증` |
| `requiresApproval` | 승인 필요 | `draft_proposal` -> `sales-mgr` |
| `precedes` | 선행 관계 | `brief_account` -> `draft_proposal` |

예시 edge:

| from | predicate | to | 의미 |
|---|---|---|---|
| `20010501-05` | `mapsTo` | `3.4` | 수주전략수립은 영업 전략 수립에 대응 |
| `20010501-06` | `mapsTo` | `3.5` | 제안 작업은 영업 계획/판매 프로세스에 대응 |
| `sales-b2b` | `executes` | `draft_proposal` | B2B 영업 에이전트가 제안서 작성 실행 |
| `draft_proposal` | `supports` | `20010501-06` | 제안서 작성 Action이 기술영업 제안 작업 지원 |
| `draft_proposal` | `produces` | `proposal-rfp` | 제안서 산출물 생성 |
| `draft_proposal` | `requires` | `price-limit-check` | 가격 한도 검증 필요 |
| `draft_proposal` | `requiresApproval` | `sales-mgr` | 영업관리자 승인 필요 |
| `brief_account` | `precedes` | `draft_proposal` | 계정 브리핑 후 제안서 작성 |

## 18. 실제 구축 예시

### 18.1 입력 문장

```text
고객 RFP를 분석하고 경쟁사 대비 차별화된 제안 전략을 수립한다.
```

### 18.2 사람이 붙일 정답 노드

| 구분 | 정답 |
|---|---|
| Task | `20010501-05 수주전략수립` |
| Process | `3.4 영업 전략 수립` |
| Action | `brief_account`, `draft_proposal` |
| Artifact | `proposal-rfp` |
| Rule | `price-limit-check` |

### 18.3 사람이 붙일 정답 edge

```text
20010501-05 mapsTo 3.4
brief_account precedes draft_proposal
draft_proposal produces proposal-rfp
draft_proposal requires price-limit-check
```

### 18.4 JSONL 정답셋 예시

```json
{
  "sampleId": "suju_gold_0001",
  "inputText": "고객 RFP를 분석하고 경쟁사 대비 차별화된 제안 전략을 수립한다.",
  "goldNodes": {
    "Task": ["20010501-05"],
    "Process": ["3.4"],
    "Action": ["brief_account", "draft_proposal"],
    "Artifact": ["proposal-rfp"],
    "Rule": ["price-limit-check"]
  },
  "goldEdges": [
    ["20010501-05", "mapsTo", "3.4"],
    ["brief_account", "precedes", "draft_proposal"],
    ["draft_proposal", "produces", "proposal-rfp"],
    ["draft_proposal", "requires", "price-limit-check"]
  ],
  "status": "reviewed"
}
```

이런 정답셋이 있어야 LLM이 자동으로 온톨로지를 잘 구축하는지 평가할 수 있다.

## 19. 연구자가 해야 할 작업

연구자가 해야 하는 일은 크게 7단계다.

### 19.1 1단계: 수주/제안 범위 확정

범위는 다음처럼 제한한다.

```text
B2B IT/AI 솔루션 수주·제안
```

포함:

```text
고객 현황분석
RFP 분석
경쟁사 분석
수주전략수립
기술영업 제안 작업
가격 조건 검토
사업계약 협상
제안서 초안 작성
```

제외:

```text
건설 수주 전체
금융권 특수 규제 전체
의료/제약 제안 전체
전체 영업/마케팅 프로세스
```

### 19.2 2단계: 후보 노드 표 작성

파일 예:

```text
suju_candidate_nodes_v0.csv
```

필드 예:

```csv
nodeType,nodeId,label,description,source,status
Task,20010501-05,수주전략수립,고객 요구와 경쟁사 분석을 바탕으로 수주 전략 수립,NCS,candidate
Process,3.4,영업 전략 수립,영업 목표와 로드맵 수립,PCF,candidate
Action,draft_proposal,제안서 작성,proposalDoc 생성,JAO,candidate
Rule,price-limit-check,가격 한도 검증,제안서 작성 전 가격 조건 확인,manual,new
```

### 19.3 3단계: 후보 edge 표 작성

파일 예:

```text
suju_candidate_edges_v0.csv
```

필드 예:

```csv
from,predicate,to,confidence,status,reason
20010501-05,mapsTo,3.4,0.90,reviewed,수주 전략과 영업 전략 수립이 직접 대응
draft_proposal,produces,proposal-rfp,0.95,reviewed,Action 출력이 proposalDoc
draft_proposal,requires,price-limit-check,0.95,reviewed,JAO Action precondition에 가격 한도 검증 존재
```

### 19.4 4단계: 문장/문단 샘플 수집

처음에는 20개만 만든다.

예:

```text
고객 요구사항과 경쟁사 제안 내용을 비교하여 수주 전략을 수립한다.
제안서에는 고객 예산, 수행 범위, 일정, 기대효과를 포함해야 한다.
계약 전 가격 조건과 업무 범위를 고객과 협의한다.
잠재 고객의 의사결정 구조와 도입 가능성을 분석한다.
```

### 19.5 5단계: 사람이 정답 라벨 부여

각 문장에 다음을 붙인다.

```text
Task
Process
Action
Artifact
Rule
Edge
```

### 19.6 6단계: LLM 자동 추출 실험

비교할 방법은 다음이다.

| 방법 | 설명 |
|---|---|
| B1 | 스키마 없이 LLM에게 바로 추출 |
| B2 | JAO 스키마를 넣고 추출 |
| B3 | 관련 후보 노드를 검색해서 넣고 추출 |
| B4 | JSON Schema 검증 후 자동 수정 |
| B5 | 전문가 검수 포함 |

### 19.7 7단계: 평가

평가 지표는 다음이다.

| 지표 | 의미 |
|---|---|
| Entity Precision/Recall/F1 | Task, Process, Action을 맞췄는가 |
| Relation Precision/Recall/F1 | edge를 맞췄는가 |
| JSON validity | JAO 스키마에 맞는가 |
| URI integrity | 없는 URI를 참조하지 않는가 |
| Review time reduction | 사람 검수 시간이 줄었는가 |

## 20. 연구 일정상 우선순위

2026년 6월 16일부터 10월까지 정리해야 하므로 범위를 줄여야 한다.

우선순위는 다음이다.

| 우선순위 | 작업 | 이유 |
|---:|---|---|
| 1 | 수주/제안 미니 온톨로지 v0.1 | 연구의 기준점 |
| 2 | 문장 20~50개 gold 정답셋 | H1 실험 시작 가능 |
| 3 | NCS Task 보강 | 현재 가장 큰 결손 |
| 4 | NCS-PCF-Action edge 검수 | 자동 매핑을 연구 정답으로 바꾸기 |
| 5 | LLM 자동 추출 비교 | 연구 기여점 |
| 6 | 일반 RAG vs Ontology-RAG 비교 | H2 효용 검증 |

지금 하지 말아야 할 일도 있다.

| 하지 말아야 할 일 | 이유 |
|---|---|
| 전체 NCS 4,659개 능력단위를 모두 정리 | 10월까지 과도함 |
| 전체 PCF level 5까지 정답화 | 라벨링 난이도 높음 |
| 전체 Agent 10개를 모두 실험 | 수주/제안 범위에서 벗어남 |
| Student 모델 학습부터 시작 | 정답셋 없이 학습해도 평가 불가 |
| 자동 MappingEdge를 그대로 정답으로 사용 | 오매칭 가능성 높음 |

## 21. 월별 큰 방향

| 월 | 해야 할 일 | 핵심 산출물 |
|---|---|---|
| 6월 | 데이터 이해, 범위 확정, 후보 노드/edge 설계 | candidate nodes/edges v0 |
| 7월 | 50~100개 정답셋, 1차 LLM 추출 실험 | gold v0, H1 중간 결과 |
| 8월 | 200개 정답셋, 검증기, H1 최종 실험 | gold v1, H1 final |
| 9월 | 일반 RAG vs Ontology-RAG vs JAO Agent 비교 | H2 결과 |
| 10월 | 결과 정리, 오류 분석, 보고서/논문/발표자료 | 최종 패키지 |

## 22. 연구원 3명 역할 분담

3명은 다음처럼 나누는 것이 가장 안정적이다.

| 역할 | 담당 | 책임 |
|---|---|---|
| 연구원 A | 온톨로지/데이터 | 후보 노드, edge, 라벨링 기준 |
| 연구원 B | LLM/시스템 | 추출 파이프라인, RAG, 검증 코드 |
| 연구원 C | 평가/논문 | 정답셋 품질, 평가표, 오류 분석, 보고서 |

작업 예시는 다음이다.

```text
A: 이 문장은 수주전략수립인가, 기술영업 제안 작업인가?
B: LLM이 이 문장을 보고 같은 라벨을 출력하게 할 수 있는가?
C: LLM 결과가 사람 정답과 얼마나 일치하는가?
```

## 23. 최종적으로 만들어야 할 파일

1차 연구를 위해 실제로 만들어야 할 파일은 다음이다.

```text
suju_candidate_nodes_v0.csv
suju_candidate_edges_v0.csv
suju_annotation_guideline_v0.md
suju_gold_v0_20.jsonl
suju_gold_v1_50.jsonl
suju_gold_final_200.jsonl
h1_extraction_prompt_b1.md
h1_extraction_prompt_b2_schema.md
h1_extraction_prompt_b3_retrieval.md
h1_results.csv
h1_error_analysis.md
h2_agent_eval_set.jsonl
h2_results.csv
```

## 24. 최종 요약

현재 온톨로지 구축 현황을 최종적으로 정리하면 다음과 같다.

```text
1. JAO 스키마는 이미 있다.
2. PCF Process와 Metric은 거의 JAO로 변환되어 있다.
3. O*NET 직업과 Task도 JAO로 변환되어 있다.
4. NCS 분류체계는 JAO Concept로 변환되어 있다.
5. NCS 능력단위 Task는 전체가 아니라 일부만 변환되어 있다.
6. 수주/제안 핵심 NCS Task는 보강이 필요하다.
7. mapping edge는 자동 후보라서 검수해야 한다.
8. 연구용 gold 정답셋은 아직 만들어야 한다.
9. 1차 연구는 전체 온톨로지가 아니라 수주/제안 미니 온톨로지 v0.1을 구축하는 것이 맞다.
10. 그 후 LLM 자동 구축 결과와 사람이 만든 정답셋을 비교하면 H1 연구가 된다.
```

따라서 지금 해야 할 가장 작은 시작점은 다음이다.

```text
수주/제안 핵심 업무 10개 선정
→ NCS Task 10개 정리
→ PCF Process 10개 정리
→ JAO Action 5개 연결
→ Artifact/Rule 5~10개 추가
→ node 30개, edge 50개짜리 미니 온톨로지 구축
→ 문장 20개에 사람이 직접 정답 라벨 부여
```

이것이 1차 온톨로지 구축의 현실적인 시작점이다.
