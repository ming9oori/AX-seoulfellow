# AX 데이터 기반 KG Build 방식 상세 정리

작성일: 2026-06-28  
기준 작업공간: `/home/minjoo/AX_서울펠로우`  
기준 산출물: `outputs/run_summary.json`, `outputs/10_evaluation/final_build_report.md`  
핵심 실행 스크립트: `scripts/build_ax_epak_internal_kg.py`

## 1. 이 문서의 범위

이 문서는 AX 데이터, 즉 NCS, PCF, PCF metrics, 산업별 PCF, 자이제 OCR 전처리 데이터를 이용해 현재 작업공간의 Knowledge Graph를 어떻게 build했는지 정리한다.

정리 대상은 다음이다.

- Layer1 NCS/PCF 표준 KG 구축 방식
- 자이제 OCR 문장과 chunk를 evidence anchor로 정리한 방식
- Layer2 수주·제안 업무 KG 구축 방식
- Task Frame, ProcedureStep, DecisionGateway, GuardCondition, ArtifactFlow를 생성한 방식
- Layer2와 NCS/PCF를 mapping candidate로 연결한 방식
- 품질 리포트와 현재 한계
- Neo4j에서 볼 수 있도록 변환한 방식

중요한 구분은 다음과 같다.

```text
KG build 자체
= scripts/build_ax_epak_internal_kg.py 기반의 결정론적 내부 build
= 외부 LLM 호출 없음

EACL/CAPE-KG 평가 실험
= Qwen 계열 LLM baseline/ablation을 돌리는 별도 실험
= KG build 결과를 평가/비교하기 위한 후속 실험
```

따라서 “현재 Neo4j에 넣어 확인하려는 KG”는 LLM이 직접 생성한 임의 triple이 아니라, 로컬 데이터와 규칙 기반 extractor로 만든 evidence-grounded procedural KG이다.

## 2. 현재 산출물 기준 요약

현재 `outputs/run_summary.json` 기준 주요 수치는 다음과 같다.

| 항목 | 수치 |
|---|---:|
| manifest files | 28 |
| Layer1 NCS nodes | 4,109 |
| Layer1 NCS edges | 4,085 |
| Layer1 PCF nodes | 5,301 |
| Layer1 PCF HAS_CHILD edges | 2,004 |
| Layer1 PCF HAS_METRIC edges | 3,284 |
| OCR sentence rows | 5,009 |
| Layer2 chunks | 214 |
| Layer2 nodes | 179 |
| Layer2 edges | 906 |
| NCS mapping candidates | 110 |
| PCF mapping candidates | 110 |
| visualization nodes | 9,589 |
| visualization edges | 10,499 |

주의할 점은 chunk 수다. 이전 211 서버 진행 요약에는 `Chunks: 460`으로 기록되어 있었지만, 현재 작업공간의 `outputs/run_summary.json`과 `outputs/02_ocr/ocr_quality_report.md` 기준으로는 전처리 workbook의 `llm_chunks` sheet에서 가져온 chunk가 214개다. 이 문서는 현재 작업공간의 `outputs` 산출물 기준으로 작성했다.

## 3. 재현 실행 명령

211 서버에서 사용한 재실행 스크립트는 다음이다.

```bash
cd /home/minjoo/AX_서울펠로우
bash scripts/run_ax_epak_on_211.sh
```

해당 wrapper는 내부적으로 다음을 수행한다.

```bash
export CUDA_VISIBLE_DEVICES=5,7
python -m py_compile scripts/build_cep_onto_kg.py scripts/build_ax_epak_internal_kg.py
python scripts/build_ax_epak_internal_kg.py
```

다만 KG build 자체는 GPU를 쓰는 LLM 호출을 하지 않는다. `CUDA_VISIBLE_DEVICES`는 이 wrapper에 남아 있지만, 실제 `build_ax_epak_internal_kg.py`의 핵심 처리는 JSON, Excel, pandas, TF-IDF, rule matching 기반이다. 현재 서버에서 GPU 0-7을 모두 사용할 수 있다는 점은 EACL/CAPE-KG LLM baseline, ablation, strict JSON 재실행에는 중요하지만, 이 내부 KG build에는 필수 조건이 아니다.

직접 실행하려면 다음 명령으로 충분하다.

```bash
cd /home/minjoo/AX_서울펠로우
/home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python scripts/build_ax_epak_internal_kg.py
```

출력은 기본적으로 `outputs/` 아래에 생성된다.

## 4. 입력 데이터 구성

입력 데이터는 `handoff-hanyang/` 아래에 있다. `build_manifest()` 단계에서 필요한 파일의 존재 여부, record count, field, SHA256을 확인하고 `outputs/00_manifest/`에 저장한다.

주요 입력은 다음이다.

| 데이터 | 입력 파일 | 역할 |
|---|---|---|
| NCS 대분류 | `handoff-hanyang/01_ncs/ncs_lclas.json` | Layer1 NCS 계층 |
| NCS 중분류 | `handoff-hanyang/01_ncs/ncs_mclas.json` | Layer1 NCS 계층 |
| NCS 소분류 | `handoff-hanyang/01_ncs/ncs_sclas.json` | Layer1 NCS 계층 |
| NCS 세분류 | `handoff-hanyang/01_ncs/ncs_dclas.json` | Layer1 NCS 계층 |
| NCS 능력단위 | `handoff-hanyang/01_ncs/ncs_unit.json` | 역량 단위 노드 |
| PCF element | `handoff-hanyang/02_pcf/pcf_data.json` | 프로세스 표준 노드 |
| PCF metric | `handoff-hanyang/02_pcf/pcf_metrics.json` | PCF metric 노드 |
| 산업별 PCF | `handoff-hanyang/02_pcf/industries/*.json` | 산업별 PCF manifest |
| 자이제 OCR | `handoff-hanyang/자이제_ocr_preprocessed.xlsx` | Layer2 업무 KG 원천 문서 |

현재 OCR workbook은 단순 raw Excel이 아니라 전처리 workbook이다. 핵심 sheet는 다음이다.

- `all_tagged`: 전체 OCR row와 전처리 태그
- `clean_sentences`: Layer2에 쓸 수 있는 정제 문장
- `llm_chunks`: chunk 단위 텍스트 묶음
- `section_catalog`: chapter/section 구조
- `excluded_rows`: 제외된 OCR row

## 5. 전체 Build Pipeline

`scripts/build_ax_epak_internal_kg.py`의 `main()`은 다음 순서로 실행된다.

```text
ensure_dirs()
build_manifest()
build_layer1()
build_ocr()
build_schema()
build_task_frames()
build_procedure_and_triples()
build_layer2_graph()
build_mapping()
build_visualization()
build_evaluation()
write outputs/run_summary.json
```

각 단계는 서로 독립적인 파일을 남긴다. 따라서 중간 결과를 직접 확인하거나 Neo4j 변환 전에 JSONL을 검토할 수 있다.

## 6. Phase 00: Manifest 생성

출력 위치:

```text
outputs/00_manifest/data_manifest.csv
outputs/00_manifest/data_manifest.json
outputs/00_manifest/raw_schema_profile.md
```

이 단계는 실제 KG를 만들기 전에 입력 파일을 점검한다.

확인 항목은 다음이다.

- 파일 존재 여부
- 파일 크기
- SHA256 checksum
- JSON record count
- Excel sheet 이름
- column 목록
- OCR workbook이 전처리 형식인지 여부

현재 manifest에는 28개 파일이 기록되어 있다. 이는 NCS/PCF 기본 파일 7개, OCR workbook 1개, 산업별 PCF 20개를 합친 수치다.

## 7. Phase 01: Layer1 NCS/PCF KG 구축

출력 위치:

```text
outputs/01_layer1/layer1_ncs_nodes.jsonl
outputs/01_layer1/layer1_ncs_edges.jsonl
outputs/01_layer1/layer1_pcf_nodes.jsonl
outputs/01_layer1/layer1_pcf_edges.jsonl
outputs/01_layer1/layer1_pcf_metric_edges.jsonl
outputs/01_layer1/pcf_industry_manifest.jsonl
outputs/01_layer1/layer1_quality_report.md
```

### 7.1 NCS 처리 방식

NCS는 current-use만 사용한다. 필터 조건은 다음이다.

```text
NCS_DEGR == 29
USG_YN == "Y"
```

NCS node type은 다음으로 나뉜다.

| Node type | 의미 | ID 형식 |
|---|---|---|
| `NCSLargeClass` | NCS 대분류 | `ncs:L:{대분류코드}` |
| `NCSMiddleClass` | NCS 중분류 | `ncs:M:{대}.{중}` |
| `NCSSmallClass` | NCS 소분류 | `ncs:S:{대}.{중}.{소}` |
| `NCSSubDivision` | NCS 세분류 | `ncs:D:{대}.{중}.{소}.{세}` |
| `NCSSubDivisionPlaceholder` | 능력단위 parent가 current dclas에 없을 때 보존용 placeholder | `ncs:D:{대}.{중}.{소}.{세}` |
| `NCSCompetencyUnit` | NCS 능력단위 | `ncs:CU:{NCS_CL_CD}` |

생성되는 주요 edge는 다음이다.

| Edge predicate | 의미 |
|---|---|
| `HAS_CHILD` | 대분류-중분류-소분류-세분류 계층 연결 |
| `HAS_COMPETENCY_UNIT` | 세분류와 능력단위 연결 |

현재 결과는 다음이다.

- current-use large classes: 24
- current-use middle classes: 84
- current-use small classes: 281
- current-use subdivisions: 269
- current-use competency units: 3,450
- NCSSubDivisionPlaceholder nodes: 1
- endpoint missing count: 0
- duplicate node ID count: 0

### 7.2 PCF 처리 방식

PCF는 `pcf_data.json`과 `pcf_metrics.json`을 사용한다.

PCF node type은 다음이다.

| Node type | 의미 | ID 형식 |
|---|---|---|
| `PCFElement` | PCF process element | `pcf:E:{pcfId}` |
| `PCFMetric` | PCF metric | `pcf:M:{metricId}` |

생성되는 주요 edge는 다음이다.

| Edge predicate | 의미 |
|---|---|
| `HAS_CHILD` | PCF parent-child 계층 |
| `HAS_METRIC` | PCF element와 metric 연결 |

현재 결과는 다음이다.

- PCFElement nodes: 2,017
- PCFMetric nodes: 3,284
- PCF HAS_CHILD edges: 2,004
- PCF HAS_METRIC edges: 3,284
- Metric orphan count: 0
- Industry PCF manifest files: 20

Layer1 품질 게이트 `G2`는 endpoint missing count가 0이므로 PASS다.

## 8. Phase 02: OCR 문장, 문서 구조, chunk 구축

출력 위치:

```text
outputs/02_ocr/ocr_sentences_clean.jsonl
outputs/02_ocr/document_structure_raw.json
outputs/02_ocr/document_structure_reviewed.json
outputs/02_ocr/layer2_chunks.jsonl
outputs/02_ocr/ocr_quality_report.md
```

### 8.1 전처리 workbook 사용

`build_ocr()`는 OCR Excel에 다음 sheet가 모두 있으면 전처리 workbook으로 판단한다.

```text
all_tagged
clean_sentences
llm_chunks
```

현재 workbook은 이 조건을 만족하므로 raw OCR에서 chunk를 다시 만들지 않고, workbook에 저장된 전처리 결과를 그대로 사용한다.

현재 OCR 품질 리포트 기준 수치는 다음이다.

- Total source rows preserved: 5,009
- Clean Layer2 sentences: 4,257
- Excluded rows: 752
- Preprocessed LLM chunks imported: 214
- Chunk mean char length: 1,154.2
- Chunk max char length: 1,800
- Body kept rows: 4,257

### 8.2 sentence record

각 OCR row는 sentence record로 바뀐다. 주요 필드는 다음이다.

| 필드 | 의미 |
|---|---|
| `sentence_id` | 문장 ID. clean_id가 있으면 clean_id 사용 |
| `text_raw` | 원문 OCR 문장 |
| `text_clean` | 정제 문장 |
| `page` | 페이지 |
| `zone` | body, table_of_contents, index 등 문서 구역 |
| `chapter_id` | 본문 chapter ID |
| `section_id` | section ID |
| `subsection_id` | subsection ID |
| `ocr_flags` | OCR 품질/제외/구조 태그 |
| `source_row` | 원래 Excel row |
| `keep_for_layer2` | Layer2 구축에 사용할지 여부 |

### 8.3 chunk record

`llm_chunks` sheet의 row는 `outputs/02_ocr/layer2_chunks.jsonl`로 저장된다. 각 chunk는 다음 정보를 가진다.

| 필드 | 의미 |
|---|---|
| `chunk_id` | chunk ID |
| `chapter_id` | chapter |
| `section_id` | section |
| `page_start` | 시작 페이지 |
| `page_end` | 종료 페이지 |
| `sentence_ids` | chunk에 포함된 sentence ID 목록 |
| `sentence_offsets` | chunk 내부 sentence별 character offset |
| `char_count` | chunk 길이 |
| `token_est` | 추정 token 수 |
| `text` | chunk 텍스트 |

품질 게이트 `G3`는 다음을 확인한다.

- 모든 chunk가 sentence id를 갖는가
- 모든 chunk가 page range를 갖는가

현재 결과는 PASS다.

## 9. Phase 03: Ontology Schema와 CQ 생성

출력 위치:

```text
outputs/03_schema/competency_questions.json
outputs/03_schema/layer2_schema.json
outputs/03_schema/allowed_predicates.json
outputs/03_schema/domain_range_constraints.json
outputs/03_schema/ontology_schema.md
```

이 단계는 Layer2 KG가 어떤 node와 edge만 허용할지 정의한다.

### 9.1 Competency Questions

총 12개 CQ가 생성된다.

| CQ | 질문 요약 | 필요한 KG 요소 |
|---|---|---|
| CQ1 | 주요 Task 구성 | `DomainTask`, `HAS_SUBTASK`, `PRECEDES` |
| CQ2 | Task별 입력 자료 | `USES_INPUT`, `Artifact`, `Concept` |
| CQ3 | Task별 산출물 | `PRODUCES`, `Artifact` |
| CQ4 | Task 수행 주체 | `PERFORMED_BY`, `Role` |
| CQ5 | 의사결정 지점 | `DecisionGateway`, `HAS_DECISION_GATEWAY` |
| CQ6 | 의사결정 조건 | `GuardCondition`, `HAS_GUARD_CONDITION` |
| CQ7 | 산출물 흐름 | `ArtifactFlow`, `FEEDS_INTO`, `USED_AS_INPUT_FOR` |
| CQ8 | 제안서 리뷰 | `ReviewCheckpoint`, `HAS_REVIEW` |
| CQ9 | 업무 원칙 | `Principle`, `HAS_PRINCIPLE` |
| CQ10 | 원문 근거 | `EvidenceAnchor`, `EVIDENCED_BY` |
| CQ11 | NCS 관련 능력단위 | `CANDIDATE_REQUIRES_CAPABILITY` |
| CQ12 | PCF 프로세스 위치 | `CANDIDATE_PROCESS_CONTEXT` |

### 9.2 Layer2 node type

현재 schema의 Layer2 node type은 다음이다.

```text
DomainTask
ProcedureStep
DecisionGateway
GuardCondition
Artifact
ArtifactFlow
Role
Principle
ReviewCheckpoint
Risk
Concept
EvidenceAnchor
Chunk
Sentence
```

### 9.3 허용 predicate

주요 predicate는 다음이다.

```text
HAS_STEP
PRECEDES
USES_INPUT
PRODUCES
PERFORMED_BY
HAS_DECISION_GATEWAY
HAS_GUARD_CONDITION
HAS_REVIEW
HAS_PRINCIPLE
HAS_RISK
FEEDS_INTO
USED_AS_INPUT_FOR
EVIDENCED_BY
CANDIDATE_REQUIRES_CAPABILITY
CANDIDATE_PROCESS_CONTEXT
HAS_CHILD
HAS_COMPETENCY_UNIT
HAS_METRIC
```

`domain_range_constraints.json`에는 predicate별 subject type과 object type 제약이 들어 있다. 예를 들어 `PRODUCES`는 `DomainTask` 또는 `ProcedureStep`에서 `Artifact`로 향해야 한다.

## 10. Phase 04: Task Frame 생성

출력 위치:

```text
outputs/04_task_frames/task_frame_candidates_raw.jsonl
outputs/04_task_frames/task_frame_review_sheet.csv
outputs/04_task_frames/canonical_task_catalog.json
outputs/04_task_frames/task_frame_quality_report.md
```

### 10.1 seed task 기반 추출

Task Frame은 `TASK_SEEDS`에 정의된 수주·제안 업무 seed에서 출발한다. 현재 seed는 22개이며, 각 seed는 다음을 가진다.

- `task_id`
- 한국어 task명
- 영어 task명
- alias 목록
- keyword 목록

예시는 다음과 같다.

```text
L2_TASK_OPPORTUNITY_ASSESSMENT: 기회분석
L2_TASK_CAPTURE_PLANNING: 수주영업
L2_TASK_BID_NO_BID_DECISION: 제안참여 의사결정
L2_TASK_CUSTOMER_NEEDS_ANALYSIS: 고객 니즈 분석
L2_TASK_COMPETITOR_ANALYSIS: 경쟁사 분석
L2_TASK_PROPOSAL_WRITING: 제안서 작성
L2_TASK_PROPOSAL_REVIEW: 제안서 리뷰
L2_TASK_COMPLIANCE_CHECK: 충실도 점검
```

### 10.2 evidence 탐색

각 seed의 keyword와 alias를 OCR body 문장에서 찾는다. 이때 다음 문장은 제외한다.

- header/footer
- page number 후보
- `excluded_from_layer2`가 붙은 문장
- body가 아닌 구역의 문장

찾은 문장은 task의 evidence가 된다. evidence ID는 sentence ID에서 만든다.

```text
sentence_id -> evidence_anchor_id
예: SENT-000123 -> EA-000123
```

### 10.3 slot 추출

각 task evidence 주변에서 다음 term dictionary를 이용해 slot을 채운다.

| Slot | 기준 dictionary |
|---|---|
| inputs | `ARTIFACT_TERMS` |
| outputs | `ARTIFACT_TERMS` |
| roles | `ROLE_TERMS` |
| decision_gateways | `DECISION_TERMS` |
| principles | `PRINCIPLE_TERMS` |
| risks | `RISK_TERMS` |

input/output 구분은 evidence 문장에 있는 신호어로 판단한다.

```text
output signal:
작성, 수립, 개발, 도출, 생성, 산출, 결과물, 출력, 배포, 제출, 만들...

input signal:
기반, 바탕, 활용, 입력, 검토, 정보, 요구조건, 참고, 입수, 수집...
```

### 10.4 현재 Task Frame 결과

현재 결과는 다음이다.

- Canonical task candidates: 22
- Duplicate Korean task names: 0
- Tasks with evidence: 22/22
- Chapter coverage:
  - CH01: 22
  - CH02: 12
  - CH03: 14
  - CH04: 15
  - CH05: 9
  - CH06: 1

모든 Task Frame은 `accepted_by_rule_pending_human_review` 상태다. 즉, 시스템 규칙상 채택했지만 사람 검수가 완료된 최종 gold는 아니다.

## 11. Phase 05-06: Procedure KG와 Triple 생성

출력 위치:

```text
outputs/05_procedure/procedure_structures_raw.jsonl
outputs/05_procedure/procedure_structures_clean.jsonl
outputs/05_procedure/procedure_edges.jsonl
outputs/05_procedure/procedure_quality_report.md

outputs/06_triples/layer2_triples_raw.jsonl
outputs/06_triples/layer2_triples_schema_valid.jsonl
outputs/06_triples/layer2_triples_clean.jsonl
outputs/06_triples/evidence_anchors.jsonl
outputs/06_triples/triple_quality_report.md
```

### 11.1 Layer2 node 생성

Task Frame에서 다음 node들이 생성된다.

| Node type | 생성 방식 |
|---|---|
| `DomainTask` | Task seed와 evidence 기반 |
| `Artifact` | task input/output에서 발견된 artifact term |
| `Role` | role term dictionary matching |
| `Principle` | principle term dictionary matching |
| `Risk` | risk term dictionary matching |
| `DecisionGateway` | decision term dictionary matching |
| `GuardCondition` | decision evidence 문장에서 조건 표현 추출 |
| `ProcedureStep` | procedure template 또는 task slot에서 추론 |
| `ArtifactFlow` | artifact flow rule에 따라 생성 |

### 11.2 ProcedureStep 생성

일부 핵심 task는 `PROCEDURE_TEMPLATES`를 사용해 절차 단계를 생성한다. 예를 들어 `L2_TASK_PROPOSAL_WRITING`에는 다음 단계가 들어간다.

```text
섹션기획서 검토
초안 작성
주제문 작성
그래픽 작성
리뷰 의견 반영
최종본 작성
```

생성된 step은 다음 edge로 task에 연결된다.

```text
DomainTask -[HAS_STEP]-> ProcedureStep
ProcedureStep -[PRECEDES]-> ProcedureStep
```

### 11.3 DecisionGateway와 GuardCondition

Bid/No Bid, Pursuit Decision, 입찰타당성 결정, 승인 등은 `DecisionGateway`로 생성된다.

그 주변 evidence 문장에서 다음 표현을 찾으면 `GuardCondition` 후보를 만든다.

```text
경우
조건
가능성
수익성
경쟁
자원
불리한
극복할 수 없는
돌발변수
```

연결은 다음과 같다.

```text
DomainTask -[HAS_DECISION_GATEWAY]-> DecisionGateway
DecisionGateway -[HAS_GUARD_CONDITION]-> GuardCondition
```

### 11.4 ArtifactFlow 생성

일부 산출물은 다음 task의 입력으로 이어진다. 이 관계는 `ARTIFACT_FLOW_RULES`로 정의되어 있다.

예시는 다음과 같다.

```text
Capture Plan -> 제안서 기획
수주전략 -> 제안전략 개발
제안전략 -> 제안서 작성
PMP -> 제안서 작성
제안서 목차 -> 제안서 작성
섹션기획서 -> 제안서 작성
제안서 -> 제안서 리뷰
충실도 체크리스트 -> 제안서 리뷰
제안요약 -> 제안서 리뷰
```

생성 edge는 다음이다.

```text
Artifact -[FEEDS_INTO]-> DomainTask
Artifact -[USED_AS_INPUT_FOR]-> DomainTask
```

### 11.5 EvidenceAnchor 생성

모든 evidence anchor는 OCR sentence에 연결된다. 각 anchor는 다음 정보를 가진다.

| 필드 | 의미 |
|---|---|
| `evidence_anchor_id` | evidence ID |
| `anchor_type` | 현재는 `sentence_anchor` |
| `sentence_id` | 원 sentence ID |
| `chunk_id` | 해당 sentence가 속한 chunk |
| `page` | 페이지 |
| `text` | evidence 문장 |
| `span_start` | sentence 내 시작 offset |
| `span_end` | sentence 내 종료 offset |
| `anchor_exact` | exact anchor 여부 |
| `zone` | 문서 구역 |

현재 exact/sentence anchor ratio는 1.000이다.

### 11.6 Triple 품질

현재 triple 품질 리포트는 다음이다.

- Raw triples: 906
- Schema-valid triples: 906
- Clean triples after SPO dedupe: 906
- Schema violation count: 0
- Allowed predicate violation count: 0
- Accepted triple evidence rate: 1.000
- Exact/sentence anchor ratio: 1.000

단, unsupported triple rate와 direction error rate는 사람 검수 label이 있어야 최종 산정할 수 있다.

## 12. Phase 07: Layer2 Graph 생성

출력 위치:

```text
outputs/07_layer2_graph/layer2_nodes.jsonl
outputs/07_layer2_graph/layer2_edges.jsonl
outputs/07_layer2_graph/layer2_alias_dictionary.json
outputs/07_layer2_graph/layer2_evidence_index.jsonl
outputs/07_layer2_graph/layer2_graph_quality_report.md
```

이 단계는 procedure/triple 단계에서 만들어진 node와 edge를 최종 Layer2 graph로 정리한다.

edge가 최종 `layer2_edges.jsonl`에 들어가려면 다음 조건을 만족해야 한다.

```text
source_id가 존재해야 함
target_id가 존재해야 함
evidence_anchor_ids가 있어야 함
domain/range type constraint를 위반하지 않아야 함
```

현재 결과는 다음이다.

- Layer2 nodes: 179
- Layer2 edges: 906
- Orphan nodes: 9
- Dangling edges: 0
- Evidence-missing edges: 0
- Type violations: 0
- Alias collisions: 13
- Accepted edge evidence 100%: True
- Gate G7: PASS

따라서 “KG 구축” 관점에서는 Layer2 graph까지 생성이 완료되었다. 다만 “논문용 gold 검증 완료”라는 뜻은 아니다.

## 13. Phase 08: Layer2 to NCS/PCF Mapping Candidate 생성

출력 위치:

```text
outputs/08_mapping/l2_ncs_mapping_candidates.jsonl
outputs/08_mapping/l2_pcf_mapping_candidates.jsonl
outputs/08_mapping/mapping_review_sheet.csv
outputs/08_mapping/mapping_quality_report.md
```

이 단계는 Layer2의 `DomainTask`를 Layer1 표준 노드에 연결할 후보를 만든다.

대상은 다음이다.

| Source | Target |
|---|---|
| Layer2 `DomainTask` | NCS `NCSCompetencyUnit` |
| Layer2 `DomainTask` | PCF `PCFElement` |

각 task당 Top-5 후보를 만든다.

### 13.1 유사도 계산

텍스트는 다음 정보를 결합한다.

Task text:

```text
label
label_ko
label_en
definition
aliases
```

Target text:

```text
label
definition
aliases
hierarchy_labels
hid
level
```

유사도 계산에는 다음 요소가 들어간다.

| 요소 | 설명 |
|---|---|
| name similarity | `SequenceMatcher` 기반 이름 유사도 |
| definition similarity | character n-gram TF-IDF cosine similarity |
| action verb similarity | 작성, 분석, 검토, 수립, 결정 등 업무동사 overlap |
| hierarchy context similarity | 수주, 제안, 영업, 고객, 전략 등 도메인 term overlap |
| level compatibility | NCS/PCF level 적합도 |
| domain gap penalty | 도메인 term overlap이 없을 때 penalty |

최종 score는 내부 추천 점수다. 자동 accept가 아니라 review 우선순위를 위한 candidate score다.

### 13.2 현재 mapping 결과

- Canonical tasks: 22
- NCS candidate rows: 110
- PCF candidate rows: 110
- Task coverage with NCS Top-K: 1.000
- Task coverage with PCF Top-K: 1.000
- Candidate reason present: True
- No auto-merge: PASS

즉, 모든 DomainTask에 대해 NCS Top-5와 PCF Top-5 후보가 생성되었다. 하지만 이 후보는 아직 전문가 검수 전이다.

## 14. Phase 09: Visualization 생성

출력 위치:

```text
outputs/09_visualization/kg_full.json
outputs/09_visualization/kg_full.graphml
outputs/09_visualization/kg_static_overview.svg
outputs/09_visualization/kg_viewer.html
outputs/09_visualization/neo4j_nodes.csv
outputs/09_visualization/neo4j_edges.csv
outputs/09_visualization/visualization_readme.md
```

이 단계는 Layer1, Layer2, mapping candidate를 하나의 visualization graph로 합친다.

포함되는 node는 다음이다.

- Layer1 NCS nodes
- Layer1 PCF nodes
- Layer2 nodes

포함되는 edge는 다음이다.

- Layer1 NCS edges
- Layer1 PCF edges
- Layer1 PCF metric edges
- Layer2 edges
- Layer2 to NCS mapping candidate edges
- Layer2 to PCF mapping candidate edges

`kg_viewer.html`은 브라우저에서 바로 열 수 있는 정적 viewer다. 별도 서버 없이도 HTML 파일을 열어 graph를 검색하고 filter할 수 있다.

## 15. Phase 10: 내부 평가 리포트 생성

출력 위치:

```text
outputs/10_evaluation/internal_review_sample.jsonl
outputs/10_evaluation/internal_review_results.csv
outputs/10_evaluation/cq_queries.json
outputs/10_evaluation/cq_answerability_report.md
outputs/10_evaluation/final_build_report.md
```

이 단계는 build 결과를 내부적으로 점검한다.

### 15.1 Review sample

predicate별 일부 edge를 샘플링해 `internal_review_sample.jsonl`로 저장한다. 이 파일은 사람 검수자가 다음 항목을 채울 수 있게 설계되어 있다.

```text
support_label
type_correct
predicate_correct
direction_correct
canonicalization_correct
comment
final_status
```

현재 `internal_review_results.csv`는 header만 생성되어 있다. 즉, 사람 검수 결과는 아직 채워지지 않았다.

### 15.2 CQ answerability

12개 CQ에 대해 관련 predicate나 mapping candidate가 존재하는지 확인한다. 현재 방식은 자동 점검이며, 실제 답변의 정확성까지 사람이 판정한 것은 아니다.

### 15.3 Final Build Report

현재 final build report의 PASS 항목은 다음이다.

- Layer1 NCS/PCF built: PASS
- OCR sentences tracked to chunks/pages: PASS
- Task catalog generated: PASS
- Procedure KG generated: PASS
- Evidence-supported clean triples generated: PASS
- Accepted Layer2 edges carry evidence: PASS
- Layer2 to NCS/PCF Top-K candidates generated: PASS
- HTML/GraphML/JSON visualization generated: PASS
- Internal CQ/evaluation reports generated: PASS

중요한 limitation은 다음 문장으로 정리되어 있다.

```text
This run is a deterministic internal build.
It creates review sheets and marks system decisions transparently,
but it does not replace human validation.
```

## 16. Neo4j Import Package 생성 방식

Neo4j 적재용 변환은 별도 스크립트로 수행했다.

```bash
/home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python scripts/export_kg_to_neo4j.py \
  --outputs-dir outputs \
  --out-dir outputs/11_neo4j_import
```

출력 위치:

```text
outputs/11_neo4j_import/nodes.csv
outputs/11_neo4j_import/relationships/*.csv
outputs/11_neo4j_import/neo4j_import.cypher
outputs/11_neo4j_import/manifest.json
outputs/11_neo4j_import/README.md
```

현재 Neo4j package 수치는 다음이다.

- Nodes: 9,589
- Relationships: 10,499
- Relationship types: 16
- Missing relationship endpoints: 0

### 16.1 Browser/Desktop용 flat import package

일부 Neo4j Browser 또는 Neo4j Desktop 환경에서는 `relationships/` 같은 하위 폴더를 import 폴더로 그대로 복사하기 어렵다. 이 경우에는 하위 폴더가 없는 flat package를 사용한다.

생성 명령:

```bash
/home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python scripts/export_kg_to_neo4j.py \
  --outputs-dir outputs \
  --out-dir outputs/11_neo4j_import_flat \
  --flat-relationships
```

출력 위치:

```text
outputs/11_neo4j_import_flat/
```

이 폴더에는 모든 CSV가 같은 위치에 놓인다.

```text
nodes.csv
HAS_CHILD.csv
HAS_COMPETENCY_UNIT.csv
HAS_METRIC.csv
HAS_STEP.csv
PRECEDES.csv
PRODUCES.csv
...
neo4j_import.cypher
manifest.json
README.md
```

Neo4j Desktop에서 직접 복사할 때는 `outputs/11_neo4j_import_flat` 안의 CSV 파일 전체를 DB의 import 폴더에 넣고, `neo4j_import.cypher` 내용을 Browser에 붙여넣어 실행하면 된다. 이 flat Cypher는 `file:///HAS_CHILD.csv`처럼 루트 CSV를 참조하므로 `relationships/` 폴더가 필요 없다.

### 16.2 Neo4j node label

모든 node는 공통 label `KGNode`를 가진다. 여기에 layer별 label이 추가된다.

| layer | Neo4j label |
|---|---|
| `Layer1NCS` | `:Layer1NCS` |
| `Layer1PCF` | `:Layer1PCF` |
| `Layer2` | `:Layer2` |

node property에는 다음이 들어간다.

```text
node_id
label
type
layer
definition
label_ko
label_en
code
hid
parent_hid
source
review_status
aliases_json
evidence_anchor_ids_json
raw_json
```

### 16.3 Neo4j relationship

relationship은 predicate별 CSV로 나뉜다.

예시는 다음이다.

```text
HAS_CHILD
HAS_COMPETENCY_UNIT
HAS_METRIC
HAS_STEP
PRECEDES
USES_INPUT
PRODUCES
PERFORMED_BY
HAS_DECISION_GATEWAY
HAS_GUARD_CONDITION
HAS_PRINCIPLE
HAS_RISK
FEEDS_INTO
USED_AS_INPUT_FOR
PROCESSCONTEXT
REQUIRESCAPABILITY
```

mapping candidate의 원래 `mapping_type`은 `processContext`, `requiresCapability`이며, Neo4j relationship type으로 변환하면서 대문자화되어 `PROCESSCONTEXT`, `REQUIRESCAPABILITY`가 되었다. 이는 Neo4j에서는 유효한 relationship type이다.

relationship property에는 다음이 들어간다.

```text
rel_id
source_id
target_id
predicate
layer
confidence
mapping_type
rank
score
review_status
evidence_anchor_ids_json
source_triple_ids_json
reason
raw_json
```

### 16.4 Cypher import 방식

`neo4j_import.cypher`는 다음 작업을 수행한다.

```text
1. KGNode node_id unique constraint 생성
2. nodes.csv를 LOAD CSV로 읽어 KGNode MERGE
3. layer 값에 따라 Layer1NCS, Layer1PCF, Layer2 label 부여
4. relationship type별 CSV를 LOAD CSV로 읽어 relationship MERGE
5. layer/type index 생성
6. label/definition fulltext index 생성
7. 마지막에 layer/type별 node count 조회
```

## 17. VS Code에서 Neo4j로 보는 방법

이 repository에는 Docker Compose helper가 추가되어 있다.

```text
docker-compose.neo4j.yml
scripts/start_neo4j_kg.sh
```

서버에서 실행:

```bash
cd /home/minjoo/AX_서울펠로우
NEO4J_PASSWORD=axkg2026 bash scripts/start_neo4j_kg.sh
```

스크립트가 하는 일은 다음이다.

```text
1. outputs/11_neo4j_import/neo4j_import.cypher가 없으면 Neo4j import package 생성
2. docker compose -f docker-compose.neo4j.yml up -d
3. Neo4j cypher-shell 접속 가능할 때까지 대기
4. neo4j_import.cypher 실행
5. Browser URL과 접속 정보를 출력
```

접속 정보:

```text
Browser: http://localhost:7474
Bolt: bolt://localhost:7687
User: neo4j
Password: axkg2026
```

VS Code Remote SSH를 쓰는 경우:

```text
1. VS Code에서 해당 서버에 Remote SSH 접속
2. 터미널에서 scripts/start_neo4j_kg.sh 실행
3. VS Code 하단 또는 Ports panel에서 7474 포트 Forward
4. 로컬 브라우저 또는 VS Code simple browser에서 http://localhost:7474 접속
5. neo4j / axkg2026으로 로그인
```

확인용 Cypher:

```cypher
MATCH (n:KGNode)
RETURN n.layer, n.type, count(*) AS c
ORDER BY n.layer, n.type;
```

Layer2 task와 NCS 후보 보기:

```cypher
MATCH (t:Layer2 {type: 'DomainTask'})-[r]->(m:Layer1NCS)
RETURN t.label, type(r), m.label, r.rank, r.score
ORDER BY t.label, r.rank
LIMIT 30;
```

특정 task 주변 graph 보기:

```cypher
MATCH p = (:Layer2 {node_id: 'L2_TASK_OPPORTUNITY_ASSESSMENT'})-[*1..2]->()
RETURN p
LIMIT 25;
```

제안서 작성 task 주변 graph 보기:

```cypher
MATCH p = (:Layer2 {node_id: 'L2_TASK_PROPOSAL_WRITING'})-[*1..2]->()
RETURN p
LIMIT 50;
```

evidence가 붙은 Layer2 edge 확인:

```cypher
MATCH (s:Layer2)-[r]->(t:Layer2)
WHERE r.evidence_anchor_ids_json <> '[]'
RETURN s.label, type(r), t.label, r.evidence_anchor_ids_json
LIMIT 50;
```

### 17.1 Docker 권한 오류가 날 때

다음 오류가 나오면 Neo4j import 파일이나 Cypher를 잘못 만든 것이 아니라, 현재 Linux 계정이 Docker daemon에 접근할 권한이 없다는 뜻이다.

```text
permission denied while trying to connect to the Docker daemon socket
unix:///var/run/docker.sock
```

현재 확인된 서버 상태에서는 `minjoo` 계정이 `docker` 그룹에 들어 있지 않고, `/var/run/docker.sock`은 `root:docker`만 접근할 수 있다. 따라서 일반 사용자 권한으로는 `docker compose`를 실행할 수 없다.

해결 방법은 두 가지다.

방법 1. sudo 권한이 있을 때:

```bash
cd /home/minjoo/AX_서울펠로우
sudo -E NEO4J_PASSWORD=axkg2026 bash scripts/start_neo4j_kg.sh
```

방법 2. 서버 관리자에게 Docker group 추가 요청:

```bash
sudo usermod -aG docker minjoo
```

그룹 추가 후에는 VS Code Remote SSH 세션을 완전히 끊었다가 다시 접속해야 한다. 단순히 터미널만 새로 열면 권한이 반영되지 않을 수 있다.

권한이 반영되었는지는 다음 명령으로 확인한다.

```bash
id
docker ps
```

`id` 출력에 `docker` 그룹이 보이고 `docker ps`가 에러 없이 실행되면 다음 명령으로 Neo4j를 띄우면 된다.

```bash
NEO4J_PASSWORD=axkg2026 bash scripts/start_neo4j_kg.sh
```

## 18. LLM 사용 여부 정리

현재 build 흐름에서 가장 혼동하기 쉬운 지점은 LLM이다.

### 18.1 KG build에는 LLM을 호출하지 않았다

`scripts/build_ax_epak_internal_kg.py` 상단 docstring에도 명시되어 있듯이, 이 build는 local AX handoff data만 사용한다.

```text
It does not call external LLMs;
extraction is a transparent rule-based first pass.
```

즉, 다음 산출물은 LLM 직접 생성물이 아니다.

```text
outputs/01_layer1/*
outputs/02_ocr/*
outputs/03_schema/*
outputs/04_task_frames/*
outputs/05_procedure/*
outputs/06_triples/*
outputs/07_layer2_graph/*
outputs/08_mapping/*
outputs/09_visualization/*
outputs/10_evaluation/*
```

단, OCR workbook의 sheet 이름에 `llm_chunks`가 들어간다. 이것은 “LLM에 넣을 수 있도록 전처리된 chunk”라는 의미에 가깝고, 현재 KG builder가 LLM을 호출했다는 뜻은 아니다.

### 18.2 LLM은 EACL/CAPE-KG 평가 실험에서 사용된다

별도로 진행 중인 EACL/CAPE-KG 실험에서는 Qwen3 계열 모델을 사용해 condition baseline, ablation, strict JSON extraction 등을 비교한다. 이 실험은 다음 목적을 가진다.

```text
1. proposed CAPE-KG 방식과 baseline 비교
2. strict JSON generation 실패율 측정
3. evidence grounding, schema retrieval, validator 등의 ablation 측정
4. 논문용 main table과 quality report 생성
```

따라서 논문 관점에서는 LLM 실험이 중요하지만, Neo4j에 먼저 넣어 확인할 현재 KG의 build provenance는 deterministic internal build로 이해하면 된다.

## 19. 현재 완료된 것과 아직 남은 것

### 19.1 완료된 것

KG 구축 관점에서 완료된 항목은 다음이다.

- Layer1 NCS KG 구축 완료
- Layer1 PCF KG 구축 완료
- OCR sentence/chunk/evidence anchor 정리 완료
- Layer2 schema와 CQ 생성 완료
- Task Frame 후보 생성 완료
- Procedure KG 생성 완료
- Evidence-supported triple 생성 완료
- Layer2 graph 생성 완료
- Layer2 to NCS/PCF Top-K mapping candidate 생성 완료
- HTML/GraphML/JSON visualization 생성 완료
- Neo4j import package 생성 완료

### 19.2 아직 완료되지 않은 것

논문 제출용 검증 관점에서 아직 남은 항목은 다음이다.

- Task Frame과 triple의 사람 검수
- mapping candidate의 전문가 accept/reject 판정
- unsupported triple rate의 human-gold 기반 산정
- direction error rate의 human-gold 기반 산정
- annotator 간 agreement, 즉 IAA 산정
- adjudicated gold set 완성
- LLM baseline/ablation 결과를 반영한 최종 main table 확정
- 논문 claim gate 최종 PASS

따라서 현재 상태를 한 문장으로 요약하면 다음과 같다.

```text
KG build는 완료되었지만, EACL 논문에서 강하게 주장할 human-validated gold evaluation은 아직 완료되지 않았다.
```

## 20. 주요 산출물 빠른 참조

| 목적 | 파일 |
|---|---|
| 전체 실행 요약 | `outputs/run_summary.json` |
| 최종 build report | `outputs/10_evaluation/final_build_report.md` |
| 입력 manifest | `outputs/00_manifest/data_manifest.json` |
| Layer1 품질 | `outputs/01_layer1/layer1_quality_report.md` |
| OCR 품질 | `outputs/02_ocr/ocr_quality_report.md` |
| Layer2 schema | `outputs/03_schema/layer2_schema.json` |
| CQ | `outputs/03_schema/competency_questions.json` |
| Task catalog | `outputs/04_task_frames/canonical_task_catalog.json` |
| Task review sheet | `outputs/04_task_frames/task_frame_review_sheet.csv` |
| Procedure edges | `outputs/05_procedure/procedure_edges.jsonl` |
| Clean triples | `outputs/06_triples/layer2_triples_clean.jsonl` |
| Evidence anchors | `outputs/06_triples/evidence_anchors.jsonl` |
| Layer2 nodes | `outputs/07_layer2_graph/layer2_nodes.jsonl` |
| Layer2 edges | `outputs/07_layer2_graph/layer2_edges.jsonl` |
| NCS mapping candidates | `outputs/08_mapping/l2_ncs_mapping_candidates.jsonl` |
| PCF mapping candidates | `outputs/08_mapping/l2_pcf_mapping_candidates.jsonl` |
| Mapping review sheet | `outputs/08_mapping/mapping_review_sheet.csv` |
| HTML viewer | `outputs/09_visualization/kg_viewer.html` |
| GraphML | `outputs/09_visualization/kg_full.graphml` |
| Neo4j package | `outputs/11_neo4j_import/` |

## 21. 연구 방법론 관점의 핵심 특징

현재 build 방식의 핵심은 다음 네 가지다.

### 21.1 Layer1은 표준 기준축으로 얇게 구축

NCS와 PCF는 업무 문서에서 새로 추출한 개념이 아니라 외부 표준 taxonomy다. 따라서 Layer1은 추론을 많이 하지 않고, 원천 JSON의 계층과 metric 구조를 보존하는 방식으로 구축했다.

이 설계의 장점은 다음이다.

- 표준 taxonomy provenance가 명확하다.
- 도메인 문서의 불확실한 추출 결과와 표준 체계가 섞이지 않는다.
- Layer2 task를 표준 역량/프로세스와 느슨하게 연결할 수 있다.

### 21.2 Layer2는 수주·제안 업무를 깊게 표현

Layer2는 단순 entity-relation graph가 아니다. 수주·제안 업무의 절차성을 표현하기 위해 다음 요소를 포함한다.

```text
DomainTask
ProcedureStep
DecisionGateway
GuardCondition
Artifact
ArtifactFlow
Role
Principle
Risk
EvidenceAnchor
```

이 구조는 “제안서 작성” 같은 업무가 어떤 입력을 사용하고, 어떤 산출물을 만들고, 누가 수행하고, 어떤 절차를 거치며, 어떤 evidence에 근거하는지 볼 수 있게 한다.

### 21.3 Evidence-first build

현재 Layer2 edge는 evidence anchor가 없으면 최종 graph에 들어가지 않는다. `layer2_edges.jsonl`에 들어간 edge는 모두 `evidence_anchor_ids`를 가진다.

이 원칙의 장점은 다음이다.

- 검수자가 원문 문장으로 되돌아갈 수 있다.
- hallucination 여부를 나중에 평가할 수 있다.
- Neo4j에서도 edge property로 evidence ID를 확인할 수 있다.

### 21.4 Layer1과 Layer2는 병합하지 않고 candidate mapping으로 연결

Layer2 task를 NCS/PCF node에 직접 확정 연결하지 않았다. 대신 Top-K candidate를 만들고 review sheet를 생성했다.

이 설계의 이유는 다음이다.

- NCS/PCF mapping은 의미 해석이 필요해 자동 확정 위험이 크다.
- Top-K 후보는 유용하지만 전문가 검수가 필요하다.
- 논문 평가에서는 mapping precision/recall을 별도 측정해야 한다.

## 22. 현재 build의 한계

현재 build는 재현성과 투명성을 중시한 deterministic first pass다. 따라서 다음 한계가 있다.

1. Rule-based keyword matching에 의존한다.  
   표현이 다르거나 암시적인 업무 지식은 누락될 수 있다.

2. Procedure template이 일부 task에 사전 정의되어 있다.  
   완전히 문서에서만 귀납한 절차 graph는 아니다.

3. Evidence anchor는 sentence 수준이다.  
   계획서에서 목표로 한 subject/predicate/object slot별 character span grounding까지는 아직 완전 구현된 상태가 아니다.

4. Mapping candidate는 자동 추천이다.  
   `l2_ncs_mapping_candidates.jsonl`, `l2_pcf_mapping_candidates.jsonl`의 후보는 아직 expert-reviewed final mapping이 아니다.

5. Human validation이 완료되지 않았다.  
   review sheet는 생성되었지만, gold annotation, adjudication, IAA가 아직 논문 claim 수준으로 완료되지 않았다.

6. LLM 기반 proposed method 평가와 deterministic KG build가 분리되어 있다.  
   논문에서는 이 둘의 관계를 명확히 설명해야 한다. 현재 KG build는 검증 가능한 내부 baseline/asset이며, EACL 실험은 별도 LLM extraction 평가다.

## 23. 다음 작업 권장 순서

현재 상태에서 연구를 이어가려면 다음 순서가 합리적이다.

1. Neo4j에 KG를 import해서 구조를 눈으로 확인한다.
2. `DomainTask` 중심으로 task, step, artifact, role, evidence 연결이 타당한지 검토한다.
3. `outputs/08_mapping/mapping_review_sheet.csv`에서 NCS/PCF mapping 후보를 검수한다.
4. `outputs/04_task_frames/task_frame_review_sheet.csv`와 `outputs/10_evaluation/internal_review_sample.jsonl`을 이용해 human validation을 시작한다.
5. 검수 결과를 import하는 script를 만들거나 기존 EACL annotation flow에 연결한다.
6. LLM baseline/ablation 결과가 완료되면 `paper_tables.md`, `main_results.csv`, claim gate report를 갱신한다.
7. 논문에는 deterministic build 수치와 human-gold 평가 수치를 분리해 보고한다.

## 24. 결론

현재 AX 데이터 기반 KG build는 다음 구조로 완료되어 있다.

```text
NCS/PCF 표준 데이터
  -> Layer1 표준 KG

자이제 OCR 전처리 workbook
  -> sentence/chunk/evidence anchor
  -> Task Frame
  -> ProcedureStep/DecisionGateway/ArtifactFlow
  -> evidence-supported Layer2 KG

Layer2 DomainTask
  -> NCS/PCF Top-K mapping candidate

전체 KG
  -> HTML/GraphML/JSON viewer
  -> Neo4j import package
```

즉, 구축된 내용부터 Neo4j에 넣어 탐색하는 것은 가능하다. 다만 현재 graph를 논문 최종 결과로 주장하려면 사람 검수, mapping expert review, human-gold evaluation, IAA가 추가로 필요하다.
