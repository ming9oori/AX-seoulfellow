# 수주/제안 온톨로지-LLM 연구 일정 및 3인 업무분담 계획서

작성일: 2026-06-16  
대상 기간: 2026-06-16 ~ 2026-10-31  
대상 경로: `/home/minjoo/AX_서울펠로우`  
주 대상 데이터: `handoff-hanyang/06_suju_focus`

## 1. 결론

2026년 6월 16일부터 10월까지 남은 기간은 약 4.5개월이다. 이 기간 안에 전체 AX 데이터 전체를 완전한 수준으로 연구하기는 범위가 넓다. 따라서 연구 범위는 다음처럼 잡는 것이 현실적이다.

> 수주/제안 도메인을 1차 대상으로 정하고, LLM이 수주/제안 문서를 읽어 NCS Task, PCF Process, JAO Action, Artifact, Rule을 자동 연결할 수 있는지 검증한다. 그리고 그 온톨로지 연결이 일반 RAG보다 에이전트 업무 수행 성능을 높이는지 평가한다.

즉, 10월까지의 핵심 목표는 다음 3개다.

| 목표 | 10월까지의 현실적 범위 | 최종 산출물 |
|---|---|---|
| H1: 온톨로지 자동 구축 | 수주/제안 문장 200개 내외에 대해 자동 노드/엣지 추출 성능 검증 | 정답셋, 자동 추출 결과, Precision/Recall/F1 |
| H2: 온톨로지 효용 검증 | 일반 RAG, Ontology-RAG, JAO Agent 방식 비교 | 업무 성공률, 환각률, 규정 준수율 비교표 |
| H3: 복제 가능성 근거 | 수주/제안 외 1개 소규모 업무에 20~30개 샘플로 예비 적용 | 확장 가능성 사례, 오류 분석 |

이 연구에서 가장 중요한 것은 “온톨로지를 새로 처음부터 만드는 것”이 아니다. 이미 AX가 만든 JAO 스키마, 인스턴스, 매핑 후보가 있다. 연구자가 해야 하는 일은 다음이다.

```text
기존 AX 온톨로지 초안
+ 수주/제안 전문가 문서
+ 사람이 만든 정답셋
+ LLM 자동 추출 실험
+ 에이전트 업무 수행 비교 실험
= 10월까지 제출 가능한 연구 결과
```

## 2. 현재 사용할 수 있는 데이터

현재 수주/제안 연구에서 바로 사용할 수 있는 핵심 파일은 다음 3개다.

| 파일 | 실제 건수 | 의미 |
|---|---:|---|
| `06_suju_focus/ncs_suju_units.json` | 51개 | 수주/제안 관련 NCS 능력단위 후보 |
| `06_suju_focus/pcf_3.0_market_and_sell.json` | 213개 | PCF 3.0 Market and Sell 프로세스 |
| `06_suju_focus/jao_sales_agent_example.json` | 6개 | `sales-b2b` Agent 1개 + Action 5개 |

NCS 수주 후보 51개 중 `inTargetDomain=true`인 핵심 후보는 29개다.

| NCS 세분류 | 핵심 후보 수 | 연구상 의미 |
|---|---:|---|
| 일반영업 | 9 | 일반 영업 사이클 |
| 통신판매 | 10 | 판매 운영, 고객관리, 상담 |
| IT기술영업 | 10 | B2B 수주/제안 연구의 핵심 |

PCF 프로세스 213개는 `3.0 Market and Sell Products and Services` 하위 프로세스다.

| PCF level | 건수 | 의미 |
|---:|---:|---|
| 1 | 1 | `3.0` 최상위 Market and Sell |
| 2 | 5 | 큰 프로세스 그룹 |
| 3 | 31 | 중간 프로세스 |
| 4 | 149 | 구체 활동 |
| 5 | 27 | 가장 세부 활동 |

JAO Agent 예시는 다음 구조다.

| 항목 | 값 |
|---|---|
| Agent | `sales-b2b` |
| 주요 역할 | 리드 관리, 제안서 작성 보조, 미팅 준비 |
| Action | `score_lead`, `brief_account`, `draft_proposal`, `forecast_pipeline`, `schedule_meeting` |
| 핵심 Action | `draft_proposal` |
| 핵심 출력물 | `proposalDoc` |
| 위험도 | `draft_proposal`은 `medium` |
| 승인자 | `sales-mgr` |

## 3. 연구 질문

10월까지 연구를 정리하려면 연구 질문을 너무 넓게 잡으면 안 된다. 다음 3개로 제한하는 것이 좋다.

### RQ1. LLM은 수주/제안 문서에서 업무 노드를 올바르게 찾을 수 있는가?

예를 들어 다음 문장이 있다고 하자.

```text
고객 RFP를 분석하고 경쟁사 대비 차별화된 제안 전략을 수립한다.
```

LLM이 이 문장을 보고 다음처럼 연결할 수 있는지 본다.

| 구분 | 정답 후보 |
|---|---|
| NCS Task | `20010501-05 수주전략수립` |
| PCF Process | `3.4 영업 전략 수립` 또는 `3.5 영업 계획 개발·관리` |
| JAO Action | `brief_account`, `draft_proposal` |
| Artifact | `proposal-rfp` |
| Rule | 가격 한도 검증, 승인자 확인 |

### RQ2. JAO 스키마를 넣어주면 LLM의 추출 결과가 좋아지는가?

비교 대상은 다음처럼 잡는다.

| 방법 | 설명 |
|---|---|
| B1: Zero-shot LLM | 스키마 없이 바로 추출 |
| B2: Schema-prompted LLM | JAO JSON Schema를 프롬프트에 넣고 추출 |
| B3: Retrieval-augmented extraction | 관련 NCS/PCF/JAO 노드만 검색해서 넣고 추출 |
| B4: Validator + repair | JSON Schema 검증 후 오류 자동 수정 |
| B5: Human-in-loop | 전문가 검수까지 포함 |

핵심 비교는 다음이다.

```text
B1보다 B2/B3/B4가 더 정확한가?
사람 검수 시간이 줄어드는가?
잘못된 노드 연결이 줄어드는가?
```

### RQ3. 온톨로지를 붙인 에이전트가 일반 RAG보다 업무를 더 잘 수행하는가?

예를 들어 “제안서 초안 작성” 업무를 비교한다.

| 방식 | 입력 | 기대 출력 |
|---|---|---|
| 일반 LLM | RFP 텍스트만 입력 | 자유 형식 제안서 초안 |
| 일반 RAG | RFP + 관련 문서 검색 결과 | 근거가 포함된 제안서 초안 |
| Ontology-RAG | RFP + NCS/PCF/JAO 노드 | 업무 단계, 산출물, 승인 규칙이 반영된 제안서 초안 |
| JAO Agent | `draft_proposal` Action 호출 | 입력/출력/위험도/승인자까지 통제된 결과 |

평가는 다음 관점으로 한다.

| 평가 항목 | 설명 |
|---|---|
| 업무 성공률 | 요구된 산출물을 제대로 만들었는가 |
| 환각률 | 없는 정보를 만들어내지 않았는가 |
| 규정 준수율 | 승인자, 가격 한도, 정보공유 제한을 지켰는가 |
| 추적 가능성 | 어떤 NCS/PCF/Action 근거로 답했는지 남겼는가 |
| 실행 가능성 | 실제 Agent Action 입력/출력 구조에 맞는가 |

## 4. 10월까지의 최종 산출물

10월 말까지 다음 산출물을 만들어야 한다.

| 번호 | 산출물 | 파일 또는 형태 | 담당 중심 |
|---:|---|---|---|
| 1 | 수주/제안 후보 노드 목록 | `suju_candidate_nodes.csv` | 연구원 A |
| 2 | 어노테이션 가이드라인 | `suju_annotation_guideline.md` | 연구원 A |
| 3 | 수주/제안 정답셋 v0 | `suju_gold_v0_50.jsonl` | 연구원 A, C |
| 4 | 수주/제안 정답셋 v1 | `suju_gold_v1_200.jsonl` | 연구원 A, C |
| 5 | 자동 추출 프롬프트/파이프라인 | `extract_suju_ontology.py` 또는 노트북 | 연구원 B |
| 6 | JSON Schema 검증 코드 | `validate_jao_outputs.py` | 연구원 B |
| 7 | H1 실험 결과 | `h1_results.csv`, 표/그래프 | 연구원 B, C |
| 8 | H2 에이전트 비교 실험셋 | `suju_agent_eval_set.jsonl` | 연구원 C |
| 9 | H2 실험 결과 | `h2_results.csv`, 오류 분석 | 연구원 B, C |
| 10 | 최종 보고서/논문 초안 | `final_report_october.md` 또는 논문 양식 | 전체 |

## 5. 연구원 3명 업무 분담

연구원은 역할로 나누는 것이 좋다. 이름이 정해지면 아래 A/B/C를 실제 이름으로 바꾸면 된다.

| 역할 | 담당자 | 핵심 책임 |
|---|---|---|
| 연구원 A: 온톨로지/데이터 리드 | A | NCS, PCF, JAO 노드 이해, 후보 노드 정리, 어노테이션 기준 수립 |
| 연구원 B: LLM/시스템 리드 | B | LLM 추출 파이프라인, RAG/Ontology-RAG, JSON Schema 검증, 실험 자동화 |
| 연구원 C: 평가/논문 리드 | C | 정답셋 품질관리, 평가 지표 설계, 오류 분석, 논문/보고서 작성 |

### 5.1 연구원 A가 해야 하는 일

연구원 A는 “무엇이 정답 노드인가”를 책임진다.

주요 작업:

| 작업 | 구체 내용 | 예시 |
|---|---|---|
| 후보 NCS 정리 | `ncs_suju_units.json`에서 핵심 Task 선별 | `수주전략수립`, `기술영업 제안 작업`, `사업계약 협상` |
| 후보 PCF 정리 | `pcf_3.0_market_and_sell.json`에서 관련 프로세스 선별 | `3.4 영업 전략 수립`, `3.5 영업 계획 개발·관리` |
| 후보 Action 정리 | `jao_sales_agent_example.json`에서 에이전트 행동 정리 | `draft_proposal`, `brief_account` |
| 어노테이션 규칙 작성 | 어떤 문장을 어떤 노드에 붙일지 기준 작성 | RFP 분석 문장은 `수주전략수립`으로 라벨 |
| 전문가 검수 조율 | AX 전문가에게 애매한 라벨 확인 | `3.4`와 `3.5` 중 어느 쪽인지 확인 |

연구원 A의 예시 산출물:

```csv
nodeType,nodeId,label,description,source
NCS,20010501-05,수주전략수립,고객 요구와 경쟁사 분석을 바탕으로 수주 전략을 수립,handoff-hanyang/06_suju_focus/ncs_suju_units.json
NCS,20010501-06,기술영업 제안 작업,가격견적/제안서/제안설명을 제공,handoff-hanyang/06_suju_focus/ncs_suju_units.json
PCF,3.4,영업 전략 수립,영업 목표와 로드맵 수립,handoff-hanyang/06_suju_focus/pcf_3.0_market_and_sell.json
PCF,3.5,영업 계획 개발·관리,제품·서비스 판매와 고객 기대치 관리,handoff-hanyang/06_suju_focus/pcf_3.0_market_and_sell.json
Action,draft_proposal,제안서 작성,proposalDoc 생성,handoff-hanyang/06_suju_focus/jao_sales_agent_example.json
```

### 5.2 연구원 B가 해야 하는 일

연구원 B는 “LLM이 자동으로 온톨로지를 만들게 하는 시스템”을 책임진다.

주요 작업:

| 작업 | 구체 내용 | 예시 |
|---|---|---|
| 프롬프트 설계 | 입력 문서에서 Task/Process/Action을 뽑는 프롬프트 작성 | “아래 문장을 JAO JSON으로 변환하라” |
| 검색 모듈 구현 | 입력 문장과 유사한 NCS/PCF/JAO 노드 검색 | `수주`, `제안`, `가격견적` 키워드로 후보 노드 검색 |
| JSON 출력 강제 | LLM 결과를 정해진 스키마로 출력 | `Task`, `Process`, `Action`, `Edge` 필드 |
| 검증기 구현 | JAO Schema와 URI 존재 여부 검사 | 없는 URI, 잘못된 class, 누락된 필드 검출 |
| 실험 자동화 | B1~B4 방법별 결과를 한 번에 생성 | `h1_results.csv` 생성 |

LLM 출력 예시는 다음처럼 잡는다.

```json
{
  "inputText": "고객 RFP를 분석하고 경쟁사 대비 차별화된 제안 전략을 수립한다.",
  "predictedNodes": [
    {
      "type": "Task",
      "id": "20010501-05",
      "label": "수주전략수립"
    },
    {
      "type": "Process",
      "id": "3.4",
      "label": "영업 전략 수립"
    },
    {
      "type": "Action",
      "id": "draft_proposal",
      "label": "제안서 작성"
    }
  ],
  "predictedEdges": [
    {
      "from": "20010501-05",
      "predicate": "mapsTo",
      "to": "3.4"
    },
    {
      "from": "draft_proposal",
      "predicate": "produces",
      "to": "proposal-rfp"
    }
  ]
}
```

### 5.3 연구원 C가 해야 하는 일

연구원 C는 “이 연구가 성능으로 증명되는가”를 책임진다.

주요 작업:

| 작업 | 구체 내용 | 예시 |
|---|---|---|
| 정답셋 품질관리 | A가 만든 라벨을 2차 검수 | 라벨 불일치, 중복 라벨, 애매한 문장 표시 |
| 평가 지표 설계 | H1/H2 평가표 작성 | Precision, Recall, F1, 업무 성공률 |
| H2 시나리오 작성 | 에이전트 업무 수행 테스트 문항 작성 | “제안서 초안을 작성하라” |
| 오류 분석 | LLM이 자주 틀리는 유형 정리 | NCS는 맞추지만 PCF level을 틀림 |
| 논문/보고서 작성 | 방법론, 실험표, 사례 정리 | 9월부터 초안 작성 시작 |

H2 평가 시나리오 예시는 다음과 같다.

```json
{
  "scenarioId": "suju_h2_001",
  "task": "고객 RFP를 바탕으로 제안서 초안을 작성하라.",
  "input": {
    "customer": "공공기관 A",
    "requirements": [
      "AI 기반 민원 분석 시스템",
      "3개월 내 PoC 완료",
      "개인정보 처리 기준 준수",
      "예산 1억 원 이하"
    ]
  },
  "expectedOntology": {
    "ncs": ["20010501-05", "20010501-06"],
    "pcf": ["3.4", "3.5"],
    "action": ["brief_account", "draft_proposal"],
    "artifact": ["proposal-rfp"],
    "rule": ["가격 한도 검증", "승인자 sales-mgr"]
  },
  "evaluationCriteria": [
    "고객 요구사항을 빠뜨리지 않았는가",
    "제안 전략이 포함되었는가",
    "가격/승인 조건을 확인했는가",
    "근거 노드를 명시했는가"
  ]
}
```

## 6. 월별 연구 진행 계획

### 6.1 6월: 데이터 이해, 범위 고정, 정답셋 설계

기간: 2026-06-16 ~ 2026-06-30

6월의 목표는 “무엇을 연구할지 확정하고, 정답셋을 만들 준비를 끝내는 것”이다.

| 주차 | 기간 | 해야 할 일 | 담당 | 완료 기준 |
|---|---|---|---|---|
| 6월 3주 | 6/16~6/21 | 전체 데이터 구조 이해, 수주/제안 subset 분석 | A 중심, 전체 | 핵심 파일 3개 설명 가능 |
| 6월 3주 | 6/16~6/21 | 연구 질문 RQ1~RQ3 확정 | C 중심, 전체 | 연구 질문 문서화 |
| 6월 4주 | 6/22~6/28 | 후보 노드 목록 v0 작성 | A | NCS/PCF/Action 후보 CSV |
| 6월 4주 | 6/22~6/28 | 추출 출력 포맷 v0 설계 | B | JSON 출력 예시 5개 |
| 6월 5주 | 6/29~6/30 | 어노테이션 가이드라인 v0 작성 | A, C | 문장 라벨링 규칙 1차 완성 |

6월 말까지 반드시 끝내야 하는 산출물:

| 산출물 | 최소 기준 |
|---|---|
| `suju_candidate_nodes_v0.csv` | NCS 29개, PCF 핵심 30개, Action 5개 포함 |
| `suju_annotation_guideline_v0.md` | Task/Process/Action 라벨링 기준 포함 |
| `suju_gold_schema_v0.json` | 정답셋 JSONL 구조 정의 |
| `h1_extraction_prompt_v0.md` | LLM 추출 프롬프트 초안 |

6월에 만들 정답셋 구조 예시는 다음이다.

```json
{
  "sampleId": "suju_gold_0001",
  "inputText": "고객 요구사항과 경쟁사 제안 내용을 비교하여 수주 전략을 수립한다.",
  "goldNodes": {
    "ncsTask": ["20010501-05"],
    "pcfProcess": ["3.4", "3.5"],
    "jaoAction": ["brief_account", "draft_proposal"],
    "artifact": ["proposal-rfp"]
  },
  "goldEdges": [
    {
      "from": "20010501-05",
      "predicate": "mapsTo",
      "to": "3.4"
    },
    {
      "from": "draft_proposal",
      "predicate": "produces",
      "to": "proposal-rfp"
    }
  ],
  "annotator": "researcher-a",
  "reviewer": "researcher-c",
  "status": "reviewed"
}
```

### 6.2 7월: 정답셋 구축과 H1 자동 추출 파이프라인

기간: 2026-07-01 ~ 2026-07-31

7월의 목표는 “사람 정답셋을 만들고, LLM 자동 추출 실험을 돌릴 수 있게 만드는 것”이다.

| 주차 | 기간 | 해야 할 일 | 담당 | 완료 기준 |
|---|---|---|---|---|
| 7월 1주 | 7/1~7/5 | 문장/문단 샘플 50개 수집 | A, C | `suju_gold_v0_50.jsonl` 원문 확보 |
| 7월 1주 | 7/1~7/5 | B1 Zero-shot 추출 프롬프트 구현 | B | 50개 샘플 자동 출력 |
| 7월 2주 | 7/6~7/12 | 50개 샘플 라벨링 및 상호검수 | A, C | gold v0 확정 |
| 7월 2주 | 7/6~7/12 | B2 Schema-prompted 추출 구현 | B | JAO 스키마 기반 출력 |
| 7월 3주 | 7/13~7/19 | 샘플 100개로 확장 | A, C | gold v0.5 |
| 7월 3주 | 7/13~7/19 | B3 검색 결합 추출 구현 | B | 후보 노드 검색 후 추출 |
| 7월 4주 | 7/20~7/26 | 1차 H1 실험 실행 | B, C | B1/B2/B3 비교표 |
| 7월 5주 | 7/27~7/31 | 오류 분석 및 가이드라인 수정 | 전체 | 오류 유형 10개 이상 정리 |

7월 말까지 반드시 끝내야 하는 산출물:

| 산출물 | 최소 기준 |
|---|---|
| `suju_gold_v0_50.jsonl` | 검수 완료 샘플 50개 |
| `suju_gold_v0_100.jsonl` | 1차 확장 샘플 100개 |
| `h1_predictions_b1_b2_b3.jsonl` | 방법별 자동 추출 결과 |
| `h1_results_july.csv` | Task/Process/Action별 Precision/Recall/F1 |
| `h1_error_analysis_july.md` | 오류 유형 정리 |

7월 H1 평가표 예시는 다음과 같다.

| 방법 | NCS Task F1 | PCF Process F1 | Action F1 | JSON Validity | URI Integrity |
|---|---:|---:|---:|---:|---:|
| B1 Zero-shot | 0.62 | 0.48 | 0.55 | 72% | 65% |
| B2 Schema-prompted | 0.74 | 0.61 | 0.70 | 91% | 84% |
| B3 Retrieval + Schema | 0.82 | 0.70 | 0.78 | 94% | 90% |

위 숫자는 예시다. 실제 숫자는 7월 실험 후 채워야 한다.

### 6.3 8월: H1 고도화, 검증기, Human-in-loop

기간: 2026-08-01 ~ 2026-08-31

8월의 목표는 “H1을 논문에 넣을 수 있는 수준으로 고도화하는 것”이다.

| 주차 | 기간 | 해야 할 일 | 담당 | 완료 기준 |
|---|---|---|---|---|
| 8월 1주 | 8/1~8/9 | 정답셋 200개로 확장 | A, C | `suju_gold_v1_200.jsonl` |
| 8월 1주 | 8/1~8/9 | JSON Schema 검증기 구현 | B | invalid JSON 자동 검출 |
| 8월 2주 | 8/10~8/16 | URI/reference integrity 검증 | B | 없는 노드 참조 검출 |
| 8월 2주 | 8/10~8/16 | AX 전문가 1차 검수 요청 | A | 애매한 라벨 30개 질의 |
| 8월 3주 | 8/17~8/23 | B4 Validator + repair 구현 | B | 자동 수정 전후 비교 |
| 8월 3주 | 8/17~8/23 | 전문가 검수 시간 측정 | C | 샘플당 검수 시간 기록 |
| 8월 4주 | 8/24~8/31 | H1 최종 실험 실행 | B, C | 최종 H1 결과표 |

8월 말까지 반드시 끝내야 하는 산출물:

| 산출물 | 최소 기준 |
|---|---|
| `suju_gold_v1_200.jsonl` | 검수 완료 샘플 200개 |
| `jao_schema_validation_report.md` | JSON Schema 오류 분석 |
| `h1_results_final.csv` | B1/B2/B3/B4/B5 최종 비교 |
| `h1_human_review_time.csv` | 검수 시간 감소율 |
| `h1_case_studies.md` | 성공 사례 5개, 실패 사례 5개 |

8월의 핵심 평가는 다음이다.

| 지표 | 의미 | 목표 |
|---|---|---:|
| Entity F1 | Task/Process/Action을 맞췄는가 | 0.85 근접 |
| Relation F1 | mapsTo/requires/uses/produces를 맞췄는가 | 0.75 이상 |
| JSON validity | 스키마에 맞는 JSON인가 | 95% 이상 |
| URI integrity | 존재하는 URI만 참조하는가 | 95% 이상 |
| Review time reduction | 전문가 검수 시간이 줄었는가 | 30% 이상 |

### 6.4 9월: H2 에이전트 효용 실험과 H3 예비 확장

기간: 2026-09-01 ~ 2026-09-30

9월의 목표는 “온톨로지가 실제 에이전트 업무 성능을 높이는지 보여주는 것”이다.

| 주차 | 기간 | 해야 할 일 | 담당 | 완료 기준 |
|---|---|---|---|---|
| 9월 1주 | 9/1~9/6 | H2 평가 시나리오 30개 작성 | C | `suju_agent_eval_v0_30.jsonl` |
| 9월 1주 | 9/1~9/6 | 일반 RAG baseline 구성 | B | RAG 결과 생성 |
| 9월 2주 | 9/7~9/13 | Ontology-RAG 구성 | B | NCS/PCF/Action 근거 포함 |
| 9월 2주 | 9/7~9/13 | JAO Agent 방식 구성 | B | Action 입력/출력 통제 |
| 9월 3주 | 9/14~9/20 | H2 비교 실험 실행 | B, C | 30개 시나리오 결과 |
| 9월 3주 | 9/14~9/20 | 사람 평가 루브릭 적용 | C, A | 성공/실패 라벨 |
| 9월 4주 | 9/21~9/27 | H3 소규모 도메인 선정 | A, C | 타 도메인 20개 샘플 |
| 9월 5주 | 9/28~9/30 | 논문/보고서 초안 작성 시작 | 전체 | 결과표와 그림 배치 |

H2 평가 시나리오 예시는 다음과 같다.

```json
{
  "scenarioId": "h2_suju_010",
  "userRequest": "아래 RFP 조건을 바탕으로 제안서 초안을 작성하고, 가격 할인 검토가 필요한 부분을 표시해줘.",
  "rfpSummary": {
    "customer": "제조기업 B",
    "goal": "AI 기반 영업 데이터 분석 대시보드 구축",
    "deadline": "8주",
    "budget": "7000만원",
    "constraints": [
      "기존 CRM 연동",
      "개인정보 비식별 처리",
      "임원 보고용 요약 화면 포함"
    ]
  },
  "expectedActions": [
    "brief_account",
    "draft_proposal"
  ],
  "expectedChecks": [
    "가격 한도 검증",
    "sales-mgr 승인 필요 여부 확인"
  ],
  "expectedArtifacts": [
    "proposalDoc"
  ]
}
```

H2 결과표 예시는 다음처럼 작성한다.

| 방법 | 업무 성공률 | 환각률 | 규정 준수율 | 근거 추적 가능률 | 평균 점수 |
|---|---:|---:|---:|---:|---:|
| 일반 LLM | 60% | 25% | 55% | 10% | 2.8/5 |
| 일반 RAG | 72% | 18% | 63% | 45% | 3.4/5 |
| Ontology-RAG | 84% | 10% | 82% | 88% | 4.1/5 |
| JAO Agent | 87% | 8% | 90% | 92% | 4.3/5 |

위 숫자는 예시다. 실제 실험 후 채워야 한다.

H3는 크게 잡지 않는다. 10월까지 시간이 부족하므로 “복제 가능성 예비 실험”으로 제한한다.

H3 후보:

| 후보 도메인 | 장점 | 10월까지 범위 |
|---|---|---|
| 법인파산 | 규칙과 절차가 명확함 | 문장 20개만 예비 라벨링 |
| 스타트업 투자 | 계약서와 조건 규칙이 풍부함 | 문장 20개만 예비 라벨링 |
| 다른 영업 세분류 | 수주와 가까워 확장 쉬움 | NCS/PCF 매핑만 예비 검증 |

### 6.5 10월: 최종 정리, 논문/보고서, 발표자료

기간: 2026-10-01 ~ 2026-10-31

10월의 목표는 “추가 실험을 벌이는 것”이 아니라 “완성된 결과를 정리하는 것”이다. 10월에 새 실험을 크게 시작하면 마감 위험이 커진다.

| 주차 | 기간 | 해야 할 일 | 담당 | 완료 기준 |
|---|---|---|---|---|
| 10월 1주 | 10/1~10/4 | H1/H2 결과표 확정 | B, C | 최종 수치 freeze |
| 10월 2주 | 10/5~10/11 | 오류 분석과 사례 정리 | A, C | 성공/실패 사례 본문 작성 |
| 10월 3주 | 10/12~10/18 | 논문/보고서 전체 초안 완성 | C 중심, 전체 | v0.9 초안 |
| 10월 4주 | 10/19~10/25 | 내부 리뷰, AX/HYU 피드백 반영 | 전체 | 최종본 후보 |
| 10월 5주 | 10/26~10/31 | 최종 제출본, 발표자료, 부록 정리 | 전체 | 최종 패키지 |

10월 말 최종 패키지는 다음처럼 구성한다.

```text
final_research_package/
  README.md
  paper_or_report.pdf
  slides.pdf
  data/
    suju_candidate_nodes_v1.csv
    suju_gold_v1_200.jsonl
    suju_agent_eval_v1_30.jsonl
  results/
    h1_results_final.csv
    h2_results_final.csv
    h1_error_analysis.md
    h2_error_analysis.md
  prompts/
    h1_extraction_prompt_b1.md
    h1_extraction_prompt_b2_schema.md
    h1_extraction_prompt_b3_retrieval.md
  code/
    extract_suju_ontology.py
    validate_jao_outputs.py
    evaluate_h1.py
    evaluate_h2.py
```

## 7. 주차별 상세 일정표

아래 표는 실제 운영용 체크리스트다.

| 주차 | 기간 | A: 온톨로지/데이터 | B: LLM/시스템 | C: 평가/논문 |
|---|---|---|---|---|
| W1 | 6/16~6/21 | 수주 데이터 3개 파일 완전 이해 | 출력 JSON 형식 초안 | 연구 질문과 평가 프레임 초안 |
| W2 | 6/22~6/28 | 후보 노드 CSV v0 | 추출 프롬프트 v0 | 어노테이션 가이드 v0 |
| W3 | 6/29~7/5 | 샘플 문장 50개 수집 | B1 실행 | 50개 라벨링 품질검수 |
| W4 | 7/6~7/12 | gold v0 확정 | B2 실행 | B1/B2 평가 |
| W5 | 7/13~7/19 | 샘플 100개 확장 | B3 검색 결합 | 오류 유형 1차 정리 |
| W6 | 7/20~7/26 | 애매한 라벨 AX 질의 | B1/B2/B3 일괄 실행 | 7월 중간 결과표 |
| W7 | 7/27~8/2 | 가이드라인 수정 | 실험 코드 정리 | 결과 해석 메모 |
| W8 | 8/3~8/9 | 샘플 200개 확장 | Schema 검증기 | gold v1 품질관리 |
| W9 | 8/10~8/16 | 전문가 검수 질문 정리 | URI 검증기 | 검수 시간 측정 설계 |
| W10 | 8/17~8/23 | 전문가 피드백 반영 | B4 repair 구현 | 검수 시간/성능 비교 |
| W11 | 8/24~8/31 | H1 사례 정리 | H1 최종 실행 | H1 최종 표/그래프 |
| W12 | 9/1~9/6 | H2에 필요한 업무 규칙 정리 | RAG baseline | H2 시나리오 30개 |
| W13 | 9/7~9/13 | Ontology 근거 노드 검수 | Ontology-RAG/JAO Agent | 평가 루브릭 확정 |
| W14 | 9/14~9/20 | H2 결과 검수 | H2 일괄 실행 | 사람 평가 및 통계 |
| W15 | 9/21~9/27 | H3 후보 도메인 정리 | H3 미니 파이프라인 재사용 | H3 샘플 평가 |
| W16 | 9/28~10/4 | 최종 데이터 freeze | 코드 freeze | 논문/보고서 목차 확정 |
| W17 | 10/5~10/11 | 사례 설명 작성 | 재현 명령 정리 | 본문 초안 작성 |
| W18 | 10/12~10/18 | 부록 데이터 설명 | 실험환경 설명 | 전체 초안 v0.9 |
| W19 | 10/19~10/25 | 리뷰 대응 | 수치 재확인 | 최종본 수정 |
| W20 | 10/26~10/31 | 제출 패키지 확인 | 코드/결과 정리 | 발표자료/최종 제출 |

## 8. 어노테이션 작업을 어떻게 해야 하는가

정답셋은 이 연구의 핵심이다. 연구자는 “문장 하나가 어떤 온톨로지 노드와 연결되는지”를 사람이 먼저 정해야 한다.

### 8.1 어노테이션 단위

권장 단위는 문장 또는 짧은 문단이다.

예:

```text
고객 요구사항을 분석하고 경쟁사 제안 내용을 비교하여 수주 가능성을 높일 전략을 수립한다.
```

이 문장을 다음처럼 라벨링한다.

| 라벨 종류 | 정답 |
|---|---|
| NCS Task | `20010501-05 수주전략수립` |
| PCF Process | `3.4 영업 전략 수립` |
| PCF 보조 후보 | `3.1 시장, 고객 및 역량 이해` |
| JAO Action | `brief_account`, `draft_proposal` |
| Artifact | `proposal-rfp` |
| Edge | `Task mapsTo Process`, `Action produces Artifact` |

### 8.2 어노테이션 규칙 예시

| 문장 특징 | 붙일 NCS | 붙일 PCF | 붙일 Action |
|---|---|---|---|
| 고객 요구, 경쟁사, 평가 우위, 수주 전략 | `수주전략수립` | `3.4 영업 전략 수립` | `brief_account` |
| 가격견적, 제안서, 제안설명, 성능테스트 | `기술영업 제안 작업` | `3.5 영업 계획 개발·관리` | `draft_proposal` |
| 업무범위 재정의, 가격 협의, 계약 전 협상 | `사업계약 협상` | `3.5` 또는 계약 관련 프로세스 | `draft_proposal` + 승인 |
| 리드 발굴, 잠재고객, 우선순위 | `영업 고객발굴` | `3.5.1 리드·기회 관리` | `score_lead` |
| 매출 예측, 파이프라인, 분기 전망 | `영업 성과관리` | `3.4.1 영업 예측 수립` | `forecast_pipeline` |

### 8.3 라벨링 시 주의점

| 문제 | 해결 방식 |
|---|---|
| 하나의 문장이 여러 업무를 포함함 | 복수 라벨 허용 |
| NCS는 맞는데 PCF가 애매함 | level 2 또는 level 3의 넓은 프로세스로 우선 라벨 |
| Action이 직접 대응되지 않음 | 가장 가까운 Action을 붙이고 `needs_new_action=true` 표시 |
| 기존 JAO에 없는 업무가 나옴 | 후보 신규 노드로 표시 |
| APQC 원문 공개 제한 | 논문에는 원문 전체가 아니라 hid, 통계, 짧은 설명만 사용 |

## 9. 실제 연구 진행 예시

### 9.1 입력 문서 예시

아래와 같은 전문가 문서 문단이 들어온다고 가정한다.

```text
제안 초기 단계에서는 고객의 사업 목표, 예산, 의사결정 구조, 경쟁사 참여 여부를 파악해야 한다. 이후 고객 요구사항과 평가 기준을 분석하여 수주 가능성이 높은 차별화 전략을 수립하고, 가격 조건과 수행 범위를 검토한 뒤 제안서 초안을 작성한다.
```

### 9.2 사람이 만든 정답 예시

```json
{
  "sampleId": "suju_gold_0021",
  "inputText": "제안 초기 단계에서는 고객의 사업 목표, 예산, 의사결정 구조, 경쟁사 참여 여부를 파악해야 한다. 이후 고객 요구사항과 평가 기준을 분석하여 수주 가능성이 높은 차별화 전략을 수립하고, 가격 조건과 수행 범위를 검토한 뒤 제안서 초안을 작성한다.",
  "goldNodes": {
    "ncsTask": [
      "20010501-03",
      "20010501-05",
      "20010501-06"
    ],
    "pcfProcess": [
      "3.1",
      "3.4",
      "3.5"
    ],
    "jaoAction": [
      "brief_account",
      "draft_proposal"
    ],
    "artifact": [
      "proposal-rfp"
    ],
    "rule": [
      "가격 한도 검증",
      "sales-mgr 승인"
    ]
  },
  "goldEdges": [
    {
      "from": "20010501-05",
      "predicate": "mapsTo",
      "to": "3.4"
    },
    {
      "from": "20010501-06",
      "predicate": "supportedBy",
      "to": "draft_proposal"
    },
    {
      "from": "draft_proposal",
      "predicate": "produces",
      "to": "proposal-rfp"
    },
    {
      "from": "draft_proposal",
      "predicate": "requires",
      "to": "가격 한도 검증"
    }
  ]
}
```

### 9.3 LLM이 해야 하는 출력 예시

```json
{
  "extractedNodes": [
    {
      "class": "Task",
      "id": "20010501-05",
      "label": "수주전략수립",
      "confidence": 0.91
    },
    {
      "class": "Task",
      "id": "20010501-06",
      "label": "기술영업 제안 작업",
      "confidence": 0.86
    },
    {
      "class": "Process",
      "id": "3.4",
      "label": "영업 전략 수립",
      "confidence": 0.82
    },
    {
      "class": "Action",
      "id": "draft_proposal",
      "label": "제안서 작성",
      "confidence": 0.88
    }
  ],
  "extractedEdges": [
    {
      "from": "20010501-05",
      "predicate": "mapsTo",
      "to": "3.4",
      "confidence": 0.80
    },
    {
      "from": "draft_proposal",
      "predicate": "produces",
      "to": "proposal-rfp",
      "confidence": 0.87
    }
  ],
  "validation": {
    "jsonSchemaValid": true,
    "uriIntegrityValid": true,
    "needsHumanReview": false
  }
}
```

### 9.4 평가 예시

사람 정답과 LLM 예측을 비교한다.

| 항목 | 사람 정답 | LLM 예측 | 판정 |
|---|---|---|---|
| NCS `20010501-05` | 있음 | 있음 | TP |
| NCS `20010501-03` | 있음 | 없음 | FN |
| NCS `20010501-06` | 있음 | 있음 | TP |
| PCF `3.4` | 있음 | 있음 | TP |
| PCF `3.1` | 있음 | 없음 | FN |
| Action `brief_account` | 있음 | 없음 | FN |
| Action `draft_proposal` | 있음 | 있음 | TP |

이런 식으로 전체 샘플에 대해 Precision, Recall, F1을 계산한다.

## 10. 회의 운영 방식

3명이 연구를 할 때는 매주 2번 짧은 회의를 권장한다.

| 회의 | 주기 | 시간 | 목적 |
|---|---|---:|---|
| 주간 계획 회의 | 매주 월요일 | 30분 | 이번 주 산출물 확정 |
| 실험/라벨 리뷰 | 매주 목요일 | 60분 | 라벨 애매함, 실험 오류, 결과 검토 |
| 월말 마일스톤 리뷰 | 매월 마지막 주 | 90분 | 다음 달로 넘길 일과 버릴 일 결정 |

월요일 회의에서 반드시 확인할 질문:

| 질문 | 담당 |
|---|---|
| 이번 주에 반드시 끝낼 파일은 무엇인가 | 전체 |
| 라벨링 샘플 수 목표는 몇 개인가 | A, C |
| 실험 코드가 어느 baseline까지 돌아가는가 | B |
| AX 전문가에게 물어봐야 할 질문은 무엇인가 | A |
| 논문 표/그림으로 남길 결과가 있는가 | C |

## 11. 리스크와 대응

| 리스크 | 발생 가능성 | 영향 | 대응 |
|---|---:|---:|---|
| 쉬플리 자료 전달 지연 | 높음 | H1 입력 문서 부족 | 임시로 NCS 정의문, RFP mock 문장, 공개 제안서 구조로 v0 구성 |
| 정답셋 품질 불안정 | 높음 | 평가 신뢰도 하락 | A 라벨링, C 2차 검수, 애매한 항목 AX 질의 |
| PCF 라벨이 너무 어려움 | 중간 | Process F1 저하 | level 2/3 중심으로 평가하고 level 4/5는 보조 분석 |
| LLM 출력 JSON 오류 | 중간 | 자동 평가 불가 | B가 schema validation + repair 구현 |
| H2 에이전트 실험 범위 과다 | 높음 | 10월 마감 위험 | Action 5개 중 `draft_proposal`, `brief_account`, `score_lead` 중심으로 제한 |
| APQC 라이선스 문제 | 중간 | 논문 공개 제한 | 원문 재배포 금지, hid와 통계 중심 공개 |
| H3까지 완전 검증 어려움 | 높음 | 연구 범위 초과 | H3는 예비 확장 실험으로 명시 |

## 12. 10월까지 버려야 할 일과 해야 할 일

시간이 제한되어 있으므로 다음 기준을 지키는 것이 좋다.

### 반드시 해야 할 일

| 해야 할 일 | 이유 |
|---|---|
| 수주/제안 정답셋 200개 | H1 평가의 핵심 |
| B1/B2/B3/B4 비교 | 연구 기여점이 명확해짐 |
| JSON Schema/URI 검증 | 온톨로지 연구다운 검증 요소 |
| 일반 RAG vs Ontology-RAG 비교 | H2의 핵심 |
| 오류 분석 | 논문 설득력 확보 |

### 시간이 부족하면 줄여야 할 일

| 줄일 일 | 이유 |
|---|---|
| 전체 27,722개 JAO 인스턴스 전수 분석 | 10월까지 과도함 |
| PCF level 5까지 완전 정답화 | 라벨링 난이도 높음 |
| Agent 28개 전체 실험 | 현재 제공된 subset은 `sales-b2b` 중심 |
| H3 다도메인 대규모 실험 | 10월 마감에 부적합 |
| Student 모델 학습 | 데이터/시간/평가 설계가 추가로 많이 필요 |

## 13. 최종 논문 또는 보고서 구조

10월 최종 문서는 다음 구조로 작성하면 된다.

```text
1. Introduction
   - 기업 업무 자동화를 위해 온톨로지 기반 Agent Harness가 필요한 이유
   - 수주/제안 도메인을 대상으로 한 이유

2. Data
   - NCS, PCF, O*NET, JAO, 06_suju_focus 설명
   - 수주/제안 subset의 실제 건수

3. Ontology Schema and Task Definition
   - Node: Task, Process, Agent, Action, Artifact, Rule
   - Edge: mapsTo, requires, uses, produces, governedBy
   - 입력 문서를 JAO 구조로 바꾸는 문제 정의

4. Method
   - B1 Zero-shot
   - B2 Schema-prompted
   - B3 Retrieval-augmented schema extraction
   - B4 Validator + repair
   - B5 Human-in-loop

5. H1 Evaluation
   - 정답셋 구성
   - Entity/Relation Precision, Recall, F1
   - JSON validity, URI integrity
   - 검수 시간 감소

6. H2 Evaluation
   - 일반 LLM, 일반 RAG, Ontology-RAG, JAO Agent 비교
   - 업무 성공률, 환각률, 규정 준수율

7. H3 Preliminary Transfer
   - 타 도메인 소규모 적용
   - 수주/제안에서 만든 절차가 재사용 가능한지 논의

8. Error Analysis
   - NCS/PCF 혼동
   - 너무 넓은/좁은 프로세스 선택
   - 없는 Action 생성
   - 규정/승인 누락

9. Conclusion
   - AX JAO 자산의 연구적 의미
   - 기업용 멀티 AI 에이전트 자동 생성 가능성
```

## 14. 최종 체크리스트

10월 말 제출 전 다음 항목을 확인한다.

| 체크 항목 | 완료 여부 |
|---|---|
| 수주/제안 정답셋 200개가 있는가 |  |
| 각 샘플에 NCS, PCF, Action 라벨이 있는가 |  |
| 라벨링 가이드라인이 문서화되어 있는가 |  |
| B1/B2/B3/B4/B5 실험 결과가 있는가 |  |
| JSON Schema validity 결과가 있는가 |  |
| URI integrity 결과가 있는가 |  |
| H2 비교 실험 결과가 있는가 |  |
| 성공 사례와 실패 사례가 각각 5개 이상 있는가 |  |
| APQC 원문 공개 제한을 확인했는가 |  |
| 코드와 결과 파일을 재현 가능하게 정리했는가 |  |
| 최종 보고서/논문 초안이 10월 중순까지 완성되었는가 |  |
| 발표자료가 10월 마지막 주 전에 완성되었는가 |  |

## 15. 한 문장으로 정리

6월에는 범위를 확정하고 정답셋 설계를 끝낸다. 7월에는 50~100개 정답셋과 1차 LLM 추출 실험을 만든다. 8월에는 200개 정답셋과 H1 최종 실험을 끝낸다. 9월에는 온톨로지 기반 에이전트가 실제로 더 잘하는지 H2를 검증한다. 10월에는 새 일을 벌이지 않고 결과, 오류 분석, 논문, 발표자료를 완성한다.
