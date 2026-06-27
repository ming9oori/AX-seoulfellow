# 수주/제안 온톨로지-LLM 연구 실행계획서

작성일: 2026-06-16  
대상 경로: `/home/minjoo/AX_서울펠로우`  
주 대상 데이터: `handoff-hanyang/06_suju_focus`

## 1. 결론부터: 지금 무엇을 하면 되는가

지금 해야 할 연구는 다음 한 문장으로 정리된다.

> 수주/제안 업무 문장을 LLM이 읽고, 적절한 NCS Task, PCF Process, JAO Agent/Action/Artifact/Rule로 자동 연결할 수 있는지 검증한다.

처음부터 전체 온톨로지를 새로 만들 필요는 없다. 이미 AX가 만든 JAO 온톨로지와 수주/제안 subset이 있다. 다만 **수주/제안 문장 단위 정답셋은 아직 없다.** 따라서 연구자가 가장 먼저 해야 할 일은 `수주/제안 문장 → 정답 라벨` 데이터셋을 만드는 것이다.

가장 작은 실행 버전은 다음이다.

```text
수주/제안 문장 50개 준비
→ 사람이 정답 라벨 부여
→ LLM이 같은 라벨을 자동 예측
→ 사람 정답과 비교
→ 방법별 성능 비교
```

여기서 라벨은 다음이다.

```text
NCS Task
PCF Process
JAO Agent
JAO Action
Artifact
Tool
Rule / Approval
```

## 2. 현재 온톨로지가 만들어진 상황인가?

답은 “부분적으로 만들어져 있다”이다.

| 구분 | 현재 상태 | 설명 |
|---|---|---|
| JAO 스키마 | 있음 | `04_jao/schemas/*.json`에 Task, Agent, Action, Process 등의 양식이 있음 |
| JAO 인스턴스 | 있음 | `04_jao/instances/*.json`에 실제 Task, Process, Agent, Action 등이 있음 |
| 수주 NCS 후보 | 있음 | `06_suju_focus/ncs_suju_units.json`에 51개, 핵심 29개 |
| 수주 PCF 후보 | 있음 | `06_suju_focus/pcf_3.0_market_and_sell.json`에 213개 |
| 수주 Agent/Action 예시 | 있음 | `sales-b2b` Agent 1개 + Action 5개 |
| 수주 문장별 정답셋 | 없음 | 연구자가 만들어야 함 |
| NCS↔PCF↔Action 검수 완료 매핑 | 없음 | 자동 매핑 후보는 있으나 검수 필요 |
| 전문가 문서 기반 추출셋 | 없음 또는 미제공 | 쉬플리 자료, 산출물 양식, NCS 학습모듈 등이 추가로 필요 |

즉, “온톨로지의 기본 뼈대와 일부 실제 카드”는 있다. 하지만 “수주/제안 연구용 정답셋”은 아직 없으므로 만들어야 한다.

## 3. 각 데이터가 정확히 무엇을 의미하는가

### 3.1 `ncs_suju_units.json`

이 파일은 수주/제안 업무에 필요한 사람의 능력 목록이다.

예:

```json
{
  "subdCode": "20010501",
  "subdName": "IT기술영업",
  "unitCode": "05",
  "unitName": "수주전략수립",
  "unitDefinition": "수주전략수립이란 사업의 수주를 위하여 고객 요구, 경쟁사 분석, 제안 평가 우위 요소를 도출하여 전략을 수립하는 능력이다.",
  "level": 7,
  "inTargetDomain": true
}
```

쉽게 말하면:

```text
수주전략수립 = 사람이 수행해야 하는 업무 능력 카드
```

이 파일의 실제 상태:

| 항목 | 값 |
|---|---:|
| 전체 능력단위 | 51 |
| `inTargetDomain=true` | 29 |
| `inTargetDomain=false` | 22 |

핵심 세분류:

| subdCode | subdName | 건수 | 연구상 의미 |
|---|---|---:|---|
| `10010101` | 일반영업 | 9 | 일반적인 영업 사이클 |
| `10030101` | 통신판매 | 10 | 채널/고객관리/운영 중심 판매 |
| `20010501` | IT기술영업 | 10 | B2B IT 수주/제안 핵심 |

연구에서 쓰는 방식:

- H1의 `Task 정답 후보`로 쓴다.
- 문장에 어떤 NCS 능력단위가 대응되는지 라벨링한다.
- 예: “가격견적과 제안서를 작성한다” → `기술영업 제안 작업`

### 3.2 `pcf_3.0_market_and_sell.json`

이 파일은 회사 업무 프로세스 지도다. NCS가 “사람이 할 수 있어야 하는 능력”이라면, PCF는 “회사가 수행하는 업무 프로세스”다.

예:

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

쉽게 말하면:

```text
3.5 영업 계획 개발·관리 = 회사 프로세스 카드
```

이 파일의 실제 상태:

| level | 건수 | 의미 |
|---:|---:|---|
| 1 | 1 | `3.0` 최상위 Market & Sell |
| 2 | 5 | 큰 프로세스 그룹 |
| 3 | 31 | 중간 프로세스 |
| 4 | 149 | 구체 활동 |
| 5 | 27 | 가장 세부 활동 |

대표 계층:

```text
3.0 제품·서비스 마케팅 및 판매
  -> 3.1 시장, 고객 및 역량 이해
    -> 3.1.1 고객·시장 인텔리전스 분석 수행
      -> 3.1.1.1 고객·시장 조사 수행

3.0 제품·서비스 마케팅 및 판매
  -> 3.5 영업 계획 개발·관리
    -> 3.5.7 현장 영업 수행
```

연구에서 쓰는 방식:

- 문장이 회사 프로세스상 어디에 위치하는지 라벨링한다.
- 예: “시장과 경쟁사를 분석한다” → `3.1 시장, 고객 및 역량 이해`
- 예: “제안 전략을 세우고 영업 계획을 세운다” → `3.5 영업 계획 개발·관리`

### 3.3 `jao_sales_agent_example.json`

이 파일은 B2B 영업 AI 에이전트의 예시다.

구성:

| class | 건수 | 내용 |
|---|---:|---|
| Agent | 1 | `sales-b2b` |
| Action | 5 | 리드 점수, 계정 브리핑, 제안서 작성, 파이프라인 예측, 미팅 일정 |

Agent:

```text
sales-b2b = B2B 영업 에이전트
```

Action:

| Action | 의미 | 입력 | 출력 | 위험도 |
|---|---|---|---|---|
| `score_lead` | 리드 점수 계산 | `leadId` | `score`, `reasons` | low |
| `brief_account` | 계정 브리핑 | `accountId` | `briefDoc` | low |
| `draft_proposal` | 제안서 작성 | `accountId`, `scope`, `budget` | `proposalDoc` | medium |
| `forecast_pipeline` | 파이프라인 예측 | `team`, `quarter` | `forecast`, `risks[]` | low |
| `schedule_meeting` | 미팅 일정 | `attendees[]`, `topic`, `duration` | `meetingLink` | low |

중요한 Action:

```json
{
  "id": "draft_proposal",
  "label": {"ko": "제안서 작성"},
  "riskLevel": "medium",
  "preconditions": ["가격 한도 검증"],
  "approvers": ["sales-mgr"],
  "tools": [
    "jao://Tool/tool/openai-api",
    "jao://Tool/tool/figma"
  ]
}
```

연구에서 쓰는 방식:

- H2에서 일반 RAG와 비교할 Agent 기반 실험의 출발점으로 쓴다.
- H1에서도 문장이 어떤 Action으로 연결되는지 라벨링한다.
- 예: “제안서 초안을 작성한다” → `draft_proposal`

## 4. 지금 정답셋이 있는가?

정답셋은 “부분적으로만 있다.”

| 정답 후보 | 있음/없음 | 설명 |
|---|---|---|
| 수주 관련 NCS Task 후보 | 있음 | `ncs_suju_units.json`의 29개 핵심 항목 |
| PCF Process 후보 | 있음 | `pcf_3.0_market_and_sell.json`의 213개 |
| Agent/Action 후보 | 있음 | `sales-b2b`와 5개 Action |
| 문장별 정답 라벨 | 없음 | 새로 만들어야 함 |
| 전문가 검수 완료 NCS↔PCF 매핑 | 없음 | 사람이 만들어야 함 |
| 전문가 검수 완료 문장↔Action 매핑 | 없음 | 사람이 만들어야 함 |
| H2 업무 성공 정답/루브릭 | 없음 | 새로 만들어야 함 |

따라서 이 연구의 첫 번째 산출물은 다음이어야 한다.

```text
수주/제안 문장 정답셋 v1
```

이 정답셋은 최소한 아래 필드를 가져야 한다.

```json
{
  "sampleId": "suju-001",
  "inputText": "고객 요구사항과 경쟁사 제안 전략을 분석하여 평가 우위 요소를 도출한다.",
  "goldNcsTasks": ["20010501-05 수주전략수립"],
  "goldPcfProcesses": ["3.1", "3.5"],
  "goldAgent": "jao://Agent/agent/sales-b2b",
  "goldActions": ["jao://Action/agent/brief_account"],
  "goldArtifacts": [],
  "goldRules": [],
  "notes": "고객/경쟁사 분석과 제안 전략 수립에 해당"
}
```

## 5. 추가로 필요한 문서가 있는가?

있다. 현재 `06_suju_focus`는 표준과 Agent 예시다. 하지만 “전문가 자료”가 아직 부족하다.

필요한 추가 문서:

| 문서 | 왜 필요한가 | 우선순위 |
|---|---|---:|
| 쉬플리 방법론 자료 | 제안/수주 전문가 지식의 핵심 | 1 |
| 제안서/RFP 산출물 양식 | Artifact 구조와 평가 루브릭 생성 | 1 |
| NCS 학습모듈 PDF | NCS 능력단위의 상세 수행준거 확보 | 1 |
| 실제 또는 익명화 RFP 샘플 | 현실적인 H2 업무 시나리오 생성 | 1 |
| 제안서 샘플 | 좋은 output 기준 정의 | 1 |
| 영업 프로세스 내부 매뉴얼 | 기업 특수성 반영 | 2 |
| 계약/가격 승인 규정 | Action risk/approval rule 검증 | 2 |
| 강의 영상 STT | 암묵지 추출 실험 | 3 |

추가 문서가 없으면 연구가 불가능한 것은 아니다. 그러나 다음이 약해진다.

- 전문가 지식 추출 실험
- 실제 제안서 품질 평가
- H2 업무 성공률 평가
- 기업 특수성 반영

## 6. Annotation은 어떻게 해야 하는가

### 6.1 Annotation 단위

처음에는 문장 또는 짧은 문단 단위로 한다.

예:

```text
가격견적과 제안서 초안을 작성하여 고객에게 제출한다.
```

### 6.2 붙여야 할 라벨

| 라벨 | 필수 여부 | 예 |
|---|---|---|
| NCS Task | 필수 | `20010501-06 기술영업 제안 작업` |
| PCF Process | 필수 | `3.5 영업 계획 개발·관리` |
| JAO Agent | 권장 | `sales-b2b` |
| JAO Action | 필수 | `draft_proposal` |
| Artifact | 권장 | `proposal-rfp` |
| Tool | 선택 | `openai-api`, `figma` |
| Rule/Approval | 권장 | `가격 한도 검증`, `sales-mgr 승인` |
| 근거 문장 | 필수 | 라벨을 선택한 이유 |
| 난이도/확신도 | 권장 | high/medium/low |

### 6.3 Annotation 예시

| inputText | NCS Task | PCF Process | Action | Artifact | Rule |
|---|---|---|---|---|---|
| 고객 요구와 경쟁사를 분석해 평가 우위 요소를 도출한다 | 수주전략수립 | 3.1 시장/고객 이해 | brief_account | briefDoc | 없음 |
| 가격견적과 제안서 초안을 작성한다 | 기술영업 제안 작업 | 3.5 영업 계획 개발·관리 | draft_proposal | proposal-rfp | sales-mgr 승인 |
| 계약 전 업무범위와 가격을 협의한다 | 사업계약 협상 | 3.5 영업 계획 개발·관리 | draft_proposal 또는 신규 협상 Action | sales-contract | 승인 필요 |
| 기존 고객과 지속 관계를 유지해 후속 사업을 발굴한다 | 기술영업 사후관리 | 3.5 영업 계획 개발·관리 | forecast_pipeline | forecast | 없음 |

### 6.4 Annotation 규모

단계적으로 늘린다.

| 버전 | 샘플 수 | 목적 |
|---|---:|---|
| v0 | 20 | 라벨 체계가 맞는지 점검 |
| v1 | 50 | 첫 baseline 실험 |
| v2 | 200 | 논문용 H1 평가 |
| v3 | 500+ | 모델 학습/튜닝 가능성 검토 |

처음부터 500개를 만들지 말고, 20개로 라벨 체계를 먼저 검증해야 한다.

## 7. 구체적인 작업 순서

### Phase 0. 데이터 이해

해야 할 일:

- `06_suju_focus` 3개 파일을 읽는다.
- `inTargetDomain=true` 29개 NCS 항목만 별도 표로 정리한다.
- PCF 3.0 하위 프로세스 중 수주/제안과 강하게 관련된 20~30개를 고른다.
- `sales-b2b`와 5개 Action을 이해한다.

산출물:

```text
suju_candidate_nodes.xlsx 또는 .csv
```

컬럼:

```text
type, id, label, description, source_file, use_for
```

### Phase 1. Annotation guideline 작성

해야 할 일:

- 어떤 문장은 어떤 NCS Task로 볼지 기준을 만든다.
- 어떤 문장은 어떤 PCF Process로 볼지 기준을 만든다.
- 어떤 문장은 어떤 Action으로 볼지 기준을 만든다.
- 애매한 경우 처리 규칙을 만든다.

예:

```text
“고객 요구 분석”이 있으면 기본적으로 3.1 시장, 고객 및 역량 이해에 매핑한다.
“제안서 초안 작성”이 있으면 draft_proposal에 매핑한다.
“계약 전 가격 협의”가 있으면 사업계약 협상에 매핑한다.
```

산출물:

```text
suju_annotation_guideline.md
```

### Phase 2. 정답셋 v0 만들기

해야 할 일:

- 수주/제안 문장 20개를 만든다.
- 각 문장에 사람이 gold label을 붙인다.
- 라벨이 너무 어렵거나 중복되는지 확인한다.

산출물:

```text
suju_eval_v0.jsonl
```

예시 형식:

```json
{"id":"suju-001","inputText":"고객 요구사항을 분석해 제안 전략을 수립한다.","goldNcsTasks":["20010501-05"],"goldPcfProcesses":["3.1","3.5"],"goldActions":["brief_account"],"goldArtifacts":[],"goldRules":[]}
```

### Phase 3. Baseline 실험

해야 할 일:

같은 20개 문장에 대해 아래 방법을 비교한다.

| 방법 | 설명 |
|---|---|
| B1 | LLM에게 문장만 주고 라벨 예측 |
| B2 | JAO schema와 후보 목록을 같이 주고 예측 |
| B3 | 문장과 관련된 후보만 검색해서 주고 예측 |
| B4 | 추출 → 정의 → 기존 URI 매칭을 단계적으로 수행 |
| B5 | 자동 검증 + 사람 검수까지 포함 |

산출물:

```text
predictions_b1.jsonl
predictions_b2.jsonl
predictions_b3.jsonl
predictions_b4.jsonl
predictions_b5_reviewed.jsonl
```

### Phase 4. 평가

해야 할 일:

- gold label과 prediction을 비교한다.
- Task, Process, Action 각각 precision/recall/F1을 계산한다.
- 사람이 검수하는 데 걸린 시간을 기록한다.

평가표:

| 방법 | NCS F1 | PCF F1 | Action F1 | JSON valid | review time |
|---|---:|---:|---:|---:|---:|
| B1 |  |  |  |  |  |
| B2 |  |  |  |  |  |
| B3 |  |  |  |  |  |
| B4 |  |  |  |  |  |
| B5 |  |  |  |  |  |

### Phase 5. 정답셋 확장

해야 할 일:

- v0 20개에서 발견한 문제를 고친다.
- 50개로 늘린다.
- 이후 200개로 늘린다.

산출물:

```text
suju_eval_v1_50.jsonl
suju_eval_v2_200.jsonl
```

### Phase 6. H2 Agent 실험

H1이 “문장을 구조화하는가”라면, H2는 “그 구조를 쓰면 Agent가 일을 더 잘하는가”다.

해야 할 일:

- RFP/리드/고객 브리핑/제안서 작성 시나리오를 만든다.
- 일반 RAG와 JAO Agent를 비교한다.

비교:

| 시스템 | 설명 |
|---|---|
| LLM-only | 그냥 LLM에 물어봄 |
| Text RAG | 문서 검색 후 답변 |
| Ontology RAG | NCS/PCF/JAO graph를 같이 검색 |
| JAO Agent | 허용된 Action과 Tool, Rule을 따라 실행 |

평가:

| 지표 | 의미 |
|---|---|
| 업무 성공률 | 요구한 산출물을 제대로 만들었는가 |
| 환각률 | 없는 정보/법규/표준을 만들었는가 |
| 규정 준수율 | 가격 한도, 비방 금지, 승인 필요를 지켰는가 |
| traceability | 어떤 NCS/PCF/JAO 근거를 썼는지 설명 가능한가 |
| action validity | 허용된 Action만 사용했는가 |

## 8. 평가를 구체적으로 어떻게 할 것인가

### 8.1 H1 평가

입력:

```json
{
  "inputText": "가격견적과 제안서 초안을 작성한다."
}
```

정답:

```json
{
  "goldNcsTasks": ["20010501-06"],
  "goldPcfProcesses": ["3.5"],
  "goldActions": ["draft_proposal"],
  "goldArtifacts": ["proposal-rfp"],
  "goldRules": ["sales-mgr approval"]
}
```

예측:

```json
{
  "predNcsTasks": ["20010501-06"],
  "predPcfProcesses": ["3.5"],
  "predActions": ["draft_proposal"],
  "predArtifacts": ["proposal-rfp"],
  "predRules": ["가격 한도 검증"]
}
```

채점:

| 항목 | 정답 | 예측 | 점수 |
|---|---|---|---:|
| NCS Task | `20010501-06` | `20010501-06` | 1 |
| PCF Process | `3.5` | `3.5` | 1 |
| Action | `draft_proposal` | `draft_proposal` | 1 |
| Artifact | `proposal-rfp` | `proposal-rfp` | 1 |
| Rule | sales-mgr approval | 가격 한도 검증 | 부분점수 또는 오답 |

### 8.2 H2 평가

업무 시나리오:

```text
A사 제조 DX RFP에 대해 제안서 초안을 작성하라.
예산은 3억 원이고, 고객은 빠른 구축과 보안 준수를 중시한다.
```

일반 RAG 평가:

- 제안서가 그럴듯한가
- 요구사항을 반영했는가
- 근거 없는 말이 있는가

JAO Agent 평가:

- `draft_proposal` Action을 선택했는가
- `accountId`, `scope`, `budget` 입력을 요구했는가
- `proposal-rfp` 섹션 구조를 따랐는가
- `sales-mgr` 승인 필요를 표시했는가
- 경쟁사 비방 금지를 지켰는가

## 9. 지금 당장 만들어야 하는 파일 목록

연구를 실제로 시작하려면 아래 파일들을 새로 만드는 것이 좋다.

| 파일 | 필수 여부 | 설명 |
|---|---|---|
| `suju_candidate_nodes.csv` | 필수 | NCS/PCF/JAO 후보 노드 목록 |
| `suju_annotation_guideline.md` | 필수 | 사람이 라벨링할 때 기준 |
| `suju_eval_v0_20.jsonl` | 필수 | 문장 20개 정답셋 |
| `suju_eval_v1_50.jsonl` | 필수 | 문장 50개 정답셋 |
| `suju_eval_v2_200.jsonl` | 논문용 | 문장 200개 정답셋 |
| `suju_h2_scenarios_v0.jsonl` | 필수 | Agent 평가용 업무 시나리오 |
| `suju_rubric.md` | 필수 | 제안서/브리핑/리드평가 채점 기준 |
| `predictions_b*.jsonl` | 실험 산출물 | 각 방법의 예측 결과 |
| `evaluation_results.csv` | 실험 산출물 | 성능 점수표 |

## 10. 추가로 요청해야 하는 자료

AX 또는 연구 협력자로부터 요청하면 좋은 자료:

| 자료 | 목적 | 우선순위 |
|---|---|---:|
| 쉬플리 방법론 자료 | 전문가 지식 추출 | 1 |
| 제안서/RFP 템플릿 | Artifact와 H2 평가 | 1 |
| 좋은 제안서 샘플 | output quality 기준 | 1 |
| 실패한 제안서 샘플 | negative case 평가 | 2 |
| 실제 RFP 샘플 | 현실적인 H2 시나리오 | 1 |
| 가격/할인 승인 규정 | Action rule 검증 | 1 |
| 계약 검토 체크리스트 | 계약/협상 Action 확장 | 2 |
| 영업 CRM 필드 정의 | `score_lead`, `forecast_pipeline` 실험 | 2 |

## 11. 가장 중요한 리스크

| 리스크 | 설명 | 대응 |
|---|---|---|
| 정답셋 부재 | 현재 문장별 gold label이 없음 | v0 20개부터 직접 구축 |
| PCF 라이선스 | APQC 원문 공개 제한 | 논문에는 통계/ID/평가 중심 |
| 자동 매핑 오염 | `mapping_edges_all`은 검수 전 | 정답으로 쓰지 말고 후보로만 사용 |
| Action 부족 | `sales-b2b` Action은 5개뿐 | H1 후 필요한 Action 후보를 추가 제안 |
| 전문가 자료 부족 | 쉬플리/실제 RFP가 없으면 H2가 약함 | 자료 요청 필요 |
| 라벨 기준 모호 | 한 문장이 여러 Task/Process에 걸칠 수 있음 | multi-label 허용, guideline 작성 |

## 12. 4주 실행 계획

| 주차 | 해야 할 일 | 산출물 |
|---:|---|---|
| 1주차 | 후보 노드 정리, annotation guideline 작성 | `suju_candidate_nodes.csv`, `suju_annotation_guideline.md` |
| 2주차 | 문장 20개 v0 정답셋 작성, 라벨 기준 수정 | `suju_eval_v0_20.jsonl` |
| 3주차 | B1/B2/B3 baseline 실행, 오류 분석 | `predictions_b1/b2/b3.jsonl`, 오류표 |
| 4주차 | 정답셋 50개 확장, H1 1차 평가표 작성 | `suju_eval_v1_50.jsonl`, `evaluation_results.csv` |

그 다음 4주는 H2 Agent 실험으로 넘어가면 된다.

## 13. 최종적으로 논문에서 주장할 수 있는 것

H1 결과가 잘 나오면:

> 스키마와 표준 후보를 함께 제공하면, LLM은 수주/제안 문장을 NCS Task, PCF Process, JAO Action으로 더 정확하게 구조화한다.

H2 결과가 잘 나오면:

> 이렇게 구조화된 온톨로지를 사용하는 Agent는 일반 RAG보다 제안서 작성, 리드 평가, 계정 브리핑에서 더 높은 성공률과 더 낮은 환각률을 보인다.

H3까지 확장하면:

> 수주/제안에서 검증한 pipeline은 법인파산, 투자, 구매, HR 등 타 업무에도 재사용 가능하다.

## 14. 매우 간단한 요약

지금 상황:

```text
온톨로지 뼈대: 있음
수주 NCS 후보: 있음
수주 PCF 후보: 있음
수주 Agent 예시: 있음
문장별 정답셋: 없음
전문가 검수 완료 매핑: 없음
```

따라서 지금 해야 할 일:

```text
1. 수주 후보 노드 목록 만들기
2. annotation 기준 만들기
3. 문장 20개 정답셋 만들기
4. LLM이 자동 라벨링하게 하기
5. 정답과 비교해 H1 평가하기
6. 이후 Agent 업무 수행 H2로 확장하기
```

가장 먼저 만들 파일:

```text
suju_candidate_nodes.csv
suju_annotation_guideline.md
suju_eval_v0_20.jsonl
```
