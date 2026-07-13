# AX 자이제 Layer 2 KG 구축 방식 및 결과물 예시

작성일: 2026-07-07  
대상 실험: `experiments/ax_zaije_layer2_kg_20260706/layer2_kg`  
입력 데이터: `자이제_1.xlsx` / `clean_sentences` 시트  
참고 설계서: `AX_ZAIJE_Layer2_KG_Methodology.md`  
재현 스크립트: `scripts/build_ax_zaije_layer2_kg.py`
OpenAI LLM 재실행 스크립트: `scripts/run_ax_zaije_openai_llm_kg.py`
OpenAI LLM 실행 결과 문서: `AX_ZAIJE_OpenAI_LLM_experiment_result_20260707_ko.md`

---

## 1. 요약

이번 실험은 `자이제_1.xlsx`의 문장 단위 데이터를 설계서 `AX_ZAIJE_Layer2_KG_Methodology.md`에 맞춰 **Layer 2 업무 중심 지식그래프(KG)**로 구축한 것이다.

핵심 목적은 단순 키워드 그래프가 아니라, 다음 질문에 답할 수 있는 **Task 중심 온톨로지**를 만드는 것이다.

- 수주영업은 어떤 입력을 사용하고 어떤 산출물을 만드는가?
- Capture Plan은 어느 Task에서 생성되고 어느 Task의 입력으로 쓰이는가?
- 제안전략 개발 전 필요한 정보는 무엇인가?
- 평가자 유형에 따라 어떤 분석이 필요한가?
- 리스크 관리는 어떤 차별화 포인트로 연결되는가?

전체 처리 흐름은 다음과 같다.

```text
자이제_1.xlsx
→ 입력 정규화
→ Source Evidence Graph 생성
→ Layer 2 Schema 생성
→ Task Frame Catalog 생성
→ Triple 생성
→ Schema Validation
→ Layer2 KG Nodes/Edges 생성
→ Competency Question 평가
→ Neo4j / RDF / Review Queue 산출
```

중요한 점은, 2026-07-06에 완료된 현재 KG 산출물은 **실제 LLM 추론을 사용하지 않은 deterministic MVP 구축 결과**라는 것이다. 현재 완료본은 설계서의 LLM 출력 구조를 보존하면서 규칙 기반으로 1차 KG를 구축한 결과이며, 실제 LLM 프롬프트는 `18_extraction_prompts.md`에 저장되어 있다.

이후 2026-07-07에 OpenAI API 기반 실제 LLM 재실행 경로를 추가했다. 기본 모델은 비용 대비 성능을 고려해 `gpt-4o-mini`로 설정했고, Task Frame linking과 Triple extraction을 실제 OpenAI Chat Completions API로 호출하도록 `scripts/run_ax_zaije_openai_llm_kg.py`를 만들었다. quota 충전 후 전체 실행까지 완료했으며, OpenAI API 실행 결과는 `experiments/ax_zaije_layer2_kg_openai_20260707/layer2_kg`에 저장되어 있다.

---

## 2. 실험 결과 핵심 수치

| 항목 | 결과 |
|---|---:|
| 유효 문장 행 | 1,366 |
| SourceChunk | 166 |
| EvidenceSpan | 1,366 |
| Raw Task Frame | 15 |
| Canonical Task Frame | 15 |
| Raw Triple | 196 |
| Validated Triple | 188 |
| Graph Node | 1,869 |
| Graph Edge | 2,368 |
| Review Queue | 95 |
| Competency Question 통과 | 7 / 7 |

품질 지표는 다음과 같이 계산되었다.

| 지표 | 값 | 해석 |
|---|---:|---|
| `node_grounded_rate_domain_only` | 1.0000 | Domain node가 모두 evidence를 가짐 |
| `edge_grounded_rate` | 1.0000 | Edge가 모두 evidence 또는 구조 근거를 가짐 |
| `predicate_valid_rate` | 1.0000 | 모든 predicate가 schema에 정의됨 |
| `task_orphan_rate` | 0.0000 | 모든 Task가 Process에 연결됨 |
| `cq_pass_rate` | 1.0000 | CQ 7개 모두 통과 |
| `case_leakage_rate` | 0.0000 | 사례 인물/회사 누출 없음 |

전체 품질 리포트는 다음 파일에 있다.

```text
experiments/ax_zaije_layer2_kg_20260706/layer2_kg/12_quality_report.md
```

### 2.1 OpenAI API LLM 재실행 결과

| 항목 | 상태 |
|---|---|
| OpenAI API용 재실행 스크립트 | 생성 완료 |
| 기본 모델 | `gpt-4o-mini` |
| API key 저장 방식 | 파일 저장 없음, 실행 프로세스 환경변수로만 사용 |
| Task Frame LLM calls | 51 |
| Triple LLM calls | 110 |
| LLM accepted triples | 188 |
| LLM rejected triples | 100 |
| Validated triples | 103 |
| Graph nodes | 1,869 |
| Graph edges | 2,283 |
| CQ 통과 | 0 / 7 |
| 예상 비용 | USD 0.162064 |
| LLM 기반 KG 전체 재구축 | 완료 |

OpenAI API 실행 결과는 다음 파일에서 확인할 수 있다.

```text
AX_ZAIJE_OpenAI_LLM_experiment_result_20260707_ko.md
experiments/ax_zaije_layer2_kg_openai_20260707/layer2_kg/24_openai_llm_run_report.md
experiments/ax_zaije_layer2_kg_openai_20260707/layer2_kg/12_quality_report.md
```

같은 파이프라인을 다시 실행하려면 다음 명령을 사용한다.

```bash
cd /home/minjoo/AX_서울펠로우
export OPENAI_API_KEY='OpenAI_API_key'
bash scripts/run_ax_zaije_openai_llm_kg.sh
```

실행 결과는 다음 경로에 생성된다.

```text
experiments/ax_zaije_layer2_kg_openai_20260707/layer2_kg
```

---

## 3. 입력 정규화 방식

입력 파일 `자이제_1.xlsx`의 `clean_sentences` 시트에서 다음 6개 컬럼을 사용했다.

| 컬럼 | 사용 목적 |
|---|---|
| `page` | EvidenceSpan의 page locator |
| `chapter_no` | Chapter node 생성 |
| `chapter_title` | Chapter label 생성 |
| `section_no` | Section node 및 SourceChunk grouping |
| `section_title` | Section label 및 Task evidence |
| `text_for_llm_human` | 실제 evidence text |

총 물리 행은 2,366개였고, 실제 텍스트가 있는 유효 문장 행은 1,366개였다.

설계서의 규칙에 따라 `chapter_no` 또는 `section_no`가 비어 있는 3개 행은 **직전 유효 섹션에 귀속**했다. 이 경우 해당 row에 `imputed_section=true`를 남겼다.

장별 프로파일은 다음과 같다.

| 장 | 제목 | 페이지 | 행 수 | 섹션 수 |
|---:|---|---|---:|---:|
| 1 | 입찰과 제안 | 19-56 | 310 | 18 |
| 2 | 수주영업 | 57-118 | 487 | 18 |
| 3 | 제안서 전략 | 119-178 | 569 | 15 |

설계서 원문에서는 2장 486행, 3장 567행으로 적혀 있으나, 이번 실험에서는 누락 메타데이터 3행을 직전 유효 섹션에 귀속했기 때문에 2장과 3장의 행 수가 각각 증가했다.

---

## 4. Source Evidence Graph 구축

먼저 원문을 직접 DomainTask로 바꾸지 않고, 원문 구조를 보존하는 Source Evidence Graph를 만들었다.

Source Evidence Graph의 구조는 다음과 같다.

```text
Book
→ Chapter
→ Section
→ SourceChunk
→ EvidenceSpan
```

### 4.1 EvidenceSpan

각 문장 행을 하나의 `EvidenceSpan`으로 만들었다. `EvidenceSpan`은 이후 Task, Entity, Triple, Edge의 근거로 참조된다.

실제 예시는 다음과 같다.

```json
{
  "id": "EV_ZAIJE_000201",
  "labels": ["EvidenceSpan"],
  "page": 43,
  "chapter_no": "1",
  "chapter_title": "입찰과 제안",
  "section_no": "1.3.1",
  "section_title": "프로세스가 중요하다",
  "chunk_id": "ZAIJE_SEC_1_3_1_CHUNK_001",
  "text_span": "프로세스가 중요하다",
  "source_row_id": "ZAIJE_1_ROW_000201",
  "source_hash": "sha256:aef49d2838b004676fa8e32787c825eea19aa3d3869d8ad2c926dd089605087f",
  "imputed_section": false
}
```

산출물:

```text
04_evidence_spans.jsonl
```

### 4.2 SourceChunk

문장만 있으면 LLM 또는 graph query가 문맥을 잃기 쉽기 때문에, 문장을 섹션 단위와 paragraph 단위로 다시 묶었다.

생성된 SourceChunk 유형은 다음과 같다.

| SourceChunk type | 개수 |
|---|---:|
| `paragraph_chunk` | 110 |
| `section_summary_chunk` | 51 |
| `definition_chunk` | 3 |
| `figure_chunk` | 1 |
| `table_chunk` | 1 |

실제 예시는 다음과 같다.

```json
{
  "id": "ZAIJE_SEC_1_3_1_SUMMARY",
  "labels": ["SourceChunk"],
  "chunk_type": "section_summary_chunk",
  "chapter_no": "1",
  "section_no": "1.3.1",
  "section_title": "프로세스가 중요하다",
  "page_start": 43,
  "page_end": 46,
  "source_row_ids": [
    "ZAIJE_1_ROW_000201",
    "ZAIJE_1_ROW_000202",
    "..."
  ],
  "hash": "sha256:82d8e748871846020f6fce2d600c55245c1f251cebe2084bed2e9653a8964237"
}
```

산출물:

```text
03_source_chunks.jsonl
```

---

## 5. Layer 2 Schema 구축

설계서의 schema 초안을 기반으로 `01_layer2_core_schema.yaml`을 만들었다.

핵심 node type은 다음과 같다.

| Node Type | 의미 |
|---|---|
| `DomainOntology` | 자이제 Layer2 온톨로지 전체 |
| `DomainProcess` | 상위 업무 흐름 |
| `DomainTask` | 반복 수행 가능한 업무 단위 |
| `Artifact` | 산출물, 문서, 도구 |
| `InformationObject` | 분석 대상 정보 |
| `DecisionPoint` | 의사결정 지점 |
| `Role` | 수행자 역할 |
| `Stakeholder` | 고객, 평가자 등 이해관계자 |
| `Principle` | 원칙 또는 지침 |
| `StrategyPattern` | 전략 유형 |
| `Risk` | 리스크 |
| `ReviewType` | 리뷰 단계 |
| `EvidenceSpan` | 원문 근거 |
| `AliasTerm` | 동의어/약어 |

핵심 relation type은 다음과 같다.

| Predicate | 의미 |
|---|---|
| `HAS_PROCESS` | Ontology가 Process를 포함 |
| `HAS_TASK` | Process가 Task를 포함 |
| `PRECEDES` | Task 간 선후행 |
| `USES_INPUT` | Task가 입력 정보/산출물을 사용 |
| `USED_AS_INPUT_FOR` | 산출물이 후속 Task의 입력으로 사용 |
| `PRODUCES` | Task가 산출물을 생성 |
| `ANALYZES` | Task가 정보/이해관계자/리스크를 분석 |
| `DEVELOPS` | Task가 전략 또는 산출물을 개발 |
| `REFINES_INTO` | 산출물/전략이 더 구체화됨 |
| `HAS_DECISION_POINT` | Task가 의사결정 지점을 가짐 |
| `HAS_REVIEW` | Task가 리뷰 단계를 가짐 |
| `HAS_PRINCIPLE` | Task가 원칙을 따름 |
| `MITIGATES` | Task가 리스크를 완화 |
| `MAY_RESULT_IN` | Task가 특정 결과로 이어질 수 있음 |
| `EVIDENCED_BY` | node/edge가 EvidenceSpan으로 근거화됨 |

산출물:

```text
01_layer2_core_schema.yaml
02_layer2_domain_extension_zaije.yaml
```

---

## 6. Task Frame Catalog 구축

설계서 7장의 Task Catalog를 기준으로 15개 canonical `DomainTask`를 만들었다.

대표 Task는 다음과 같다.

| Task ID | Task |
|---|---|
| `L2_TASK_REQUIREMENT_ICEBERG_ANALYSIS` | 고객 요구조건 구조 분석 |
| `L2_TASK_OPPORTUNITY_PLANNING` | 사전영업 / Opportunity Planning |
| `L2_TASK_CAPTURE_PLANNING` | 수주영업 / Capture Planning |
| `L2_TASK_BID_NO_BID_DECISION` | 제안참여 의사결정 |
| `L2_TASK_PROPOSAL_PLANNING` | 제안서 기획 / Proposal Planning |
| `L2_TASK_PROPOSAL_PREPARING` | 제안서 작성 / Proposal Preparing |
| `L2_TASK_PRESENTATION_PREPARATION` | 프레젠테이션 준비 |
| `L2_TASK_SALES_INFORMATION_MANAGEMENT` | 영업 정보 관리 |
| `L2_TASK_VALUE_PROPOSITION` | 가치제안 개발 |
| `L2_TASK_EVALUATOR_ANALYSIS` | 평가자 분석 |
| `L2_TASK_PERSUASIVE_COMMUNICATION` | 설득 커뮤니케이션 설계 |
| `L2_TASK_PROPOSAL_STRATEGY_DEVELOPMENT` | 제안전략 개발 |
| `L2_TASK_COMPETITOR_ANALYSIS` | 경쟁사 분석 및 차별화 요소 규명 |
| `L2_TASK_TACTIC_DEVELOPMENT_VALIDATION` | 전술 개발 및 효과성 검증 |
| `L2_TASK_RISK_MANAGEMENT` | 리스크 관리 |

### 6.1 Task Frame 예시

`수주영업 / Capture Planning` Task Frame 예시는 다음과 같다.

```json
{
  "id": "L2_TASK_CAPTURE_PLANNING",
  "labels": ["DomainTask"],
  "name_ko": "수주영업 / Capture Planning",
  "name_en": "Capture Planning",
  "aliases": ["수주영업", "Capture Planning", "Capture Plan", "수주계획"],
  "definition": "고객·경쟁사·자사 솔루션 정보를 수집·분석해 Capture Plan과 수주전략을 만드는 업무.",
  "parent_process_id": "L2_PROCESS_CAPTURE_PLANNING",
  "task_scope": "operational",
  "inputs": [
    "L2_INFO_CUSTOMER_INFORMATION",
    "L2_INFO_COMPETITOR_INFORMATION",
    "L2_INFO_OWN_SOLUTION",
    "L2_INFO_CUSTOMER_NEEDS"
  ],
  "outputs": [
    "L2_ARTIFACT_CAPTURE_PLAN",
    "L2_STRATEGY_CAPTURE_STRATEGY"
  ],
  "decision_points": ["L2_DECISION_BID_NO_BID"],
  "roles": [
    "L2_ROLE_SALES_REP",
    "L2_ROLE_PROPOSAL_TEAM"
  ],
  "evidence_sections": [
    "1.3.1",
    "1.3.2",
    "2.1",
    "2.1.1",
    "2.1.2"
  ],
  "confidence": 0.9,
  "review_status": "canonical_seed_needs_human_review"
}
```

산출물:

```text
05_task_frames.raw.jsonl
06_task_frames.canonical.jsonl
```

---

## 7. Triple 생성 방식

Task Frame을 먼저 만든 뒤, 각 Task의 입력, 산출물, 역할, 원칙, 리스크, 선후행 관계를 triple로 만들었다.

즉, 다음 순서로 구축했다.

```text
Task Frame 먼저 생성
→ Task의 inputs / outputs / roles / risks / principles 확인
→ subject-predicate-object triple 생성
→ evidence_refs 연결
→ schema validation
```

예를 들어 `L2_TASK_CAPTURE_PLANNING`은 다음 triple을 가진다.

```text
수주영업 / Capture Planning
  -USES_INPUT-> 고객 정보
  -USES_INPUT-> 경쟁사 정보
  -USES_INPUT-> 자사 솔루션
  -USES_INPUT-> 고객 니즈
  -PRODUCES-> Capture Plan
  -DEVELOPS-> 수주전략
  -HAS_DECISION_POINT-> Bid/No-Bid Decision
```

### 7.1 Triple 예시 1: Capture Plan 생성

```json
{
  "triple_id": "L2_TRI_000031",
  "subject_id": "L2_TASK_CAPTURE_PLANNING",
  "predicate": "PRODUCES",
  "object_id": "L2_ARTIFACT_CAPTURE_PLAN",
  "frame_task_id": "L2_TASK_CAPTURE_PLANNING",
  "evidence_refs": [
    "EV_ZAIJE_000229",
    "EV_ZAIJE_000448",
    "EV_ZAIJE_000460"
  ],
  "evidence_page": 44,
  "evidence_section": "1.3.1",
  "evidence_span": "수주영업(Capture Planning)은 Capture Plan 작성을 포함한 수주영업 전체의 기획과 실행을 의미한다.",
  "confidence": 0.89,
  "relation_scope": "process_step",
  "validation_status": "verified"
}
```

이 triple은 다음 의미를 가진다.

```text
수주영업 / Capture Planning
  -PRODUCES-> Capture Plan
```

### 7.2 Triple 예시 2: Capture Plan의 후속 사용

```json
{
  "triple_id": "L2_TRI_000189",
  "subject_id": "L2_ARTIFACT_CAPTURE_PLAN",
  "predicate": "USED_AS_INPUT_FOR",
  "object_id": "L2_TASK_PROPOSAL_PLANNING",
  "frame_task_id": "L2_TASK_CAPTURE_PLANNING",
  "evidence_refs": [
    "EV_ZAIJE_000229",
    "EV_ZAIJE_000235",
    "EV_ZAIJE_000242"
  ],
  "evidence_page": 44,
  "evidence_section": "1.3.1",
  "confidence": 0.92,
  "relation_scope": "process_step",
  "validation_status": "verified"
}
```

이 triple은 다음 의미를 가진다.

```text
Capture Plan
  -USED_AS_INPUT_FOR-> 제안서 기획 / Proposal Planning
```

산출물:

```text
08_triples.raw.jsonl
09_triples.validated.jsonl
```

---

## 8. Schema Validation 방식

생성된 triple과 edge는 graph에 넣기 전에 자동 검증했다.

검증 기준은 다음과 같다.

| 검증 항목 | 설명 |
|---|---|
| Predicate 검증 | `predicate`가 schema에 정의된 관계인지 확인 |
| Domain 검증 | subject node type이 predicate의 domain에 맞는지 확인 |
| Range 검증 | object node type이 predicate의 range에 맞는지 확인 |
| Evidence 검증 | `evidence_refs`가 존재하고 실제 EvidenceSpan을 가리키는지 확인 |
| Confidence 검증 | `confidence < 0.60`이면 graph 적재 제외 |
| 중복 검증 | 동일 subject-predicate-object는 evidence_refs 병합 |

예를 들어 `PRODUCES`는 다음 domain/range 제약을 갖는다.

```text
PRODUCES:
  domain: DomainTask 또는 Step
  range: Artifact, InformationObject, StrategyPattern
```

따라서 다음 edge는 통과한다.

```text
DomainTask(L2_TASK_CAPTURE_PLANNING)
  -PRODUCES->
Artifact(L2_ARTIFACT_CAPTURE_PLAN)
```

---

## 9. Graph Node / Edge 구축 결과

검증된 triple과 source graph를 합쳐 최종 `10_nodes.jsonl`, `11_edges.jsonl`을 만들었다.

### 9.1 Node 분포

| Node Type | Count |
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

### 9.2 Edge 분포

| Predicate | Count |
|---|---:|
| `EVIDENCED_BY` | 1,759 |
| `ALIAS_OF` | 201 |
| `HAS_CHUNK` | 166 |
| `HAS_SECTION` | 51 |
| `USES_INPUT` | 36 |
| `PERFORMED_BY` | 23 |
| `PRECEDES` | 21 |
| `HAS_TASK` | 15 |
| `ANALYZES` | 15 |
| `PRODUCES` | 15 |
| `HAS_PRINCIPLE` | 14 |
| `TARGETS_STAKEHOLDER` | 12 |
| `HAS_REVIEW` | 9 |
| `DEVELOPS` | 7 |
| `HAS_PROCESS` | 6 |
| `USED_AS_INPUT_FOR` | 4 |

### 9.3 Node 예시: Capture Plan

```json
{
  "id": "L2_ARTIFACT_CAPTURE_PLAN",
  "labels": ["Artifact"],
  "name_ko": "Capture Plan",
  "name_en": "Capture Plan",
  "aliases": [
    "Capture Plan",
    "수주계획",
    "영업정보 관리 도구"
  ],
  "artifact_type": "planning_artifact",
  "evidence_refs": [
    "EV_ZAIJE_000229",
    "EV_ZAIJE_000448",
    "EV_ZAIJE_000460",
    "EV_ZAIJE_000217",
    "EV_ZAIJE_000235",
    "EV_ZAIJE_000242",
    "EV_ZAIJE_000244",
    "EV_ZAIJE_000439"
  ],
  "confidence": 0.84,
  "review_status": "needs_review",
  "schema_version": "L2_SCHEMA_0.1"
}
```

### 9.4 Edge 예시: 수주영업이 Capture Plan을 생성

```json
{
  "edge_id": "L2_EDGE_001818",
  "source_id": "L2_TASK_CAPTURE_PLANNING",
  "predicate": "PRODUCES",
  "target_id": "L2_ARTIFACT_CAPTURE_PLAN",
  "evidence_refs": [
    "EV_ZAIJE_000229",
    "EV_ZAIJE_000448",
    "EV_ZAIJE_000460"
  ],
  "confidence": 0.89,
  "relation_scope": "process_step",
  "frame_task_id": "L2_TASK_CAPTURE_PLANNING",
  "validation_status": "verified"
}
```

산출물:

```text
10_nodes.jsonl
11_edges.jsonl
```

---

## 10. Competency Question 평가

설계서에서 제시한 CQ 7개를 graph path로 평가했다.

| CQ | 질문 | 결과 |
|---|---|---|
| CQ1 | 제안전략을 세우기 전에 어떤 정보와 산출물이 필요한가? | PASS |
| CQ2 | Capture Plan은 어떤 업무에서 생성되고 어디에 사용되는가? | PASS |
| CQ3 | Bid/No-Bid 의사결정은 어느 단계에서 발생하며 어떤 입력을 쓰는가? | PASS |
| CQ4 | 평가자 유형에 따라 커뮤니케이션은 어떻게 달라지는가? | PASS |
| CQ5 | 리스크 관리는 어떻게 차별화 포인트로 이어지는가? | PASS |
| CQ6 | 제안서 작성 단계에서 어떤 리뷰 또는 마일스톤이 필요한가? | PASS |
| CQ7 | 고객의 공식 요구조건과 비공식 요구조건은 어떻게 구분되는가? | PASS |

### 10.1 CQ2 예시

질문:

```text
Capture Plan은 어떤 업무에서 생성되고 어디에 사용되는가?
```

그래프 경로:

```text
수주영업 / Capture Planning
  -PRODUCES-> Capture Plan

Capture Plan
  -USED_AS_INPUT_FOR-> 제안서 기획 / Proposal Planning
```

이 경로가 존재하기 때문에 CQ2는 PASS로 평가되었다.

산출물:

```text
16_competency_questions.json
17_graph_query_demo.md
```

---

## 11. Neo4j Export 예시

Neo4j import용 파일은 다음 위치에 생성했다.

```text
14_neo4j_import/
  nodes.csv
  edges.csv
  import.cypher
```

Neo4j에서 적재 후 예시 질의는 다음과 같다.

### 11.1 수주영업의 입력과 산출물 조회

```cypher
MATCH (t:DomainTask {id: "L2_TASK_CAPTURE_PLANNING"})-[r:USES_INPUT|PRODUCES|DEVELOPS]->(x)
RETURN t.name_ko AS task, type(r) AS relation, x.name_ko AS target;
```

예상되는 핵심 결과:

```text
수주영업 / Capture Planning -USES_INPUT-> 고객 정보
수주영업 / Capture Planning -USES_INPUT-> 경쟁사 정보
수주영업 / Capture Planning -USES_INPUT-> 자사 솔루션
수주영업 / Capture Planning -USES_INPUT-> 고객 니즈
수주영업 / Capture Planning -PRODUCES-> Capture Plan
수주영업 / Capture Planning -DEVELOPS-> 수주전략
```

### 11.2 Capture Plan의 생성과 사용 경로

```cypher
MATCH (t:DomainTask {id: "L2_TASK_CAPTURE_PLANNING"})-[:PRODUCES]->(a:Artifact {id: "L2_ARTIFACT_CAPTURE_PLAN"})
OPTIONAL MATCH (a)-[:USED_AS_INPUT_FOR]->(next:DomainTask)
RETURN t.name_ko AS produced_by, a.name_ko AS artifact, next.name_ko AS used_by;
```

예상되는 핵심 결과:

```text
produced_by: 수주영업 / Capture Planning
artifact: Capture Plan
used_by: 제안서 기획 / Proposal Planning
```

---

## 12. RDF Export

표준 RDF 계열 도구와도 연결할 수 있도록 Turtle 파일을 생성했다.

```text
15_rdf_export/
  layer2_schema.ttl
  layer2_data.ttl
```

RDF export의 목적은 다음이다.

- Layer2 schema를 W3C 스타일로 표현
- `DomainTask`, `Artifact`, `EvidenceSpan` 등을 RDF class/resource로 표현
- 추후 SPARQL 또는 온톨로지 도구와 연결 가능하게 함

---

## 13. Review Queue

자동 구축 결과를 바로 gold로 주장하지 않기 위해 사람 검수 큐를 만들었다.

검수 큐에는 총 95개 항목이 들어 있다.

주요 검수 대상은 다음이다.

| 검수 대상 | 이유 |
|---|---|
| `DomainTask` 후보 | Task 정의와 범위가 적절한지 확인 필요 |
| `PRECEDES` | 업무 선후행 관계는 방법론 주장에 직접 영향 |
| `REFINES_INTO` | 전략/산출물 구체화 관계 검토 필요 |
| `HAS_DECISION_POINT` | 의사결정 지점의 위치 검토 필요 |
| `HAS_REVIEW` | 리뷰 단계와 Task 연결 검토 필요 |
| `MAY_RESULT_IN` | 결과 가능성 관계는 해석 여지가 있음 |
| `MITIGATES` | 리스크 완화 관계 검토 필요 |

산출물:

```text
13_review_queue.csv
13_review_queue.xlsx
```

---

## 14. 산출물 전체 구조

이번 실험의 전체 산출물은 다음 구조로 생성되었다.

```text
experiments/ax_zaije_layer2_kg_20260706/layer2_kg/
  00_source_profile.md
  01_layer2_core_schema.yaml
  02_layer2_domain_extension_zaije.yaml
  03_source_chunks.jsonl
  04_evidence_spans.jsonl
  05_task_frames.raw.jsonl
  06_task_frames.canonical.jsonl
  07_terms_alias_dictionary.json
  08_triples.raw.jsonl
  09_triples.validated.jsonl
  10_nodes.jsonl
  11_edges.jsonl
  12_quality_report.md
  13_review_queue.csv
  13_review_queue.xlsx
  14_neo4j_import/
    nodes.csv
    edges.csv
    import.cypher
  15_rdf_export/
    layer2_schema.ttl
    layer2_data.ttl
  16_competency_questions.json
  17_graph_query_demo.md
  18_extraction_prompts.md
  run_summary.json
```

---

## 15. 이번 구축의 핵심 의의

이번 실험에서 확인한 것은 다음이다.

1. `자이제_1.xlsx`의 문장 데이터를 `Book → Chapter → Section → Chunk → EvidenceSpan` 구조로 보존할 수 있었다.
2. 설계서의 Layer2 Task 중심 ontology를 실제 데이터에 적용해 15개 canonical `DomainTask`를 만들 수 있었다.
3. Task의 입력, 산출물, 역할, 원칙, 리스크, 선후행 관계를 triple로 표현할 수 있었다.
4. 모든 graph edge가 schema와 evidence 기준으로 자동 검증되었다.
5. CQ 7개에 대해 graph path 기반 답변이 가능했다.
6. Neo4j와 RDF 양쪽으로 export할 수 있었다.

즉, 이번 결과는 **Layer 2 KG MVP 구축이 설계서대로 작동한다는 proof-of-concept**이다.

---

## 16. 한계와 다음 단계

이번 실험의 가장 중요한 한계는 다음이다.

```text
deterministic MVP는 CQ를 만족했지만, OpenAI LLM 단독 추출 결과는 CQ exact path 기준을 아직 만족하지 못했다.
```

초기에는 Qwen 계열 로컬 모델 실행을 검토했으나, 현재는 사용자의 요청에 따라 OpenAI API 기반의 저비용 LLM 재실행 방향으로 수정했다. 로컬 GPU나 `torch/transformers/vllm` 설치 없이 OpenAI API를 호출해 Task Frame linking과 Triple extraction을 수행하도록 별도 스크립트를 만들었다.

2026-07-07 초기 smoke test에서는 OpenAI API가 다음 오류를 반환했다.

```text
HTTP 429 insufficient_quota
You exceeded your current quota, please check your plan and billing details.
```

이후 quota 충전 후 전체 실행은 완료되었다. 현재 상태는 다음과 같이 정리해야 한다.

```text
OpenAI API 기반 LLM 재실행 완료.
단, CQ exact path 기준은 0/7이므로 CQ-aware reprompt와 사람 검수가 필요함.
```

다음 단계는 다음 순서가 적절하다.

1. CQ-aware reprompt
   - CQ별 missing edge를 추출한다.
   - 관련 evidence와 candidate node를 넣고 OpenAI API에 보강 질의한다.

2. Evidence aggregation 개선
   - duplicate SPO를 reject만 하지 않고 evidence_refs를 병합한다.

3. Predicate balancing
   - `USED_AS_INPUT_FOR`, `MITIGATES`, `MAY_RESULT_IN`, `REFINES_INTO` 등 CQ-critical predicate를 별도 prompt로 보강한다.

4. 사람 검수
   - `13_review_queue.xlsx` 기반 검토
   - Task/edge/alias 승인, 병합, 수정

검수 전까지는 이번 결과를 **gold KG**라고 주장하면 안 된다. 현재 단계의 정확한 표현은 다음이다.

```text
AX 자이제 Layer2 KG 설계서 기반 deterministic MVP 구축 결과
및 OpenAI API 기반 LLM bootstrap KG 구축 결과
```
