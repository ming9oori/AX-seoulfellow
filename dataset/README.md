# 제안 실무 KG-RAG 검증용 QA 데이터셋

2026-09-30 추가: 자이제 2·3의 검수 원문에서 각각 150문항을 생성했다.
[자이제 2·3 데이터·생성 코드·검증 보고서](jaije2_3/README.md)를 참고한다.
아래 설명과 이 폴더의 `qa_dataset.csv`/`qa_dataset.jsonl`은 기존 자이제 1의
150문항에 관한 내용이다.

## 1. 데이터셋 개요

이 데이터셋은 `자이제_1.xlsx`의 원문을 바탕으로 만든 제안 실무 분야의
질문·답변 150개로 구성되어 있다. 질문과 답변은 `gpt-5.6-terra`로
생성했으며, 장·절·페이지·근거 원문은 모델이 만들지 않고 선택된 Excel
행에서 코드로 복원했다.

이 데이터셋의 목적은 다음 두 가지이다.

1. Excel 원문의 내용이 Neo4j 온톨로지에 올바르게 적재되었는지 검증한다.
2. KG-RAG가 질문에 필요한 노드와 관계를 검색하고 근거에 맞는 답변을
   생성하는지 평가한다.

현재 버전은 **원문 기반 QA 초안**이다. 모든 질문은 Excel 근거를 가지고
있지만, Neo4j의 정답 노드·관계·최소 hop은 아직 라벨링하지 않았다. 따라서
`review_status`는 `pending`, `ontology_answerable`은 `null`, 그래프 Gold
컬럼은 빈 값으로 저장되어 있다.

## 2. 파일 구성

| 파일 | 용도 |
|---|---|
| `qa_dataset.csv` | Excel, Google Sheets 등에서 사람이 검수하기 위한 파일 |
| `qa_dataset.jsonl` | Python 평가 코드와 RAG 실험에서 사용하기 위한 파일 |

두 파일에는 동일한 150개 문항이 들어 있다.

CSV는 Excel에서 한글이 깨지지 않도록 UTF-8 BOM 형식으로 저장했다.
JSONL은 한 줄에 하나의 완전한 JSON 객체가 들어 있다. `page`,
`evidence_text`, `source_row_ids`처럼 값이 여러 개인 컬럼은 JSONL에서는
배열이고, CSV에서는 JSON 배열 모양의 문자열로 표시된다.

예:

```text
page            [21, 22]
source_row_ids  [16, 17, 18]
```

## 3. 데이터 현황

| 항목 | 값 |
|---|---:|
| 전체 QA 수 | 150 |
| 포함된 장 | 3 |
| 포함된 절 | 51 |
| 입찰과 제안 | 53 |
| 수주영업 | 53 |
| 제안서 전략 | 44 |
| 단일 문장 근거 | 64 |
| 복수 문장 근거 | 76 |
| 표 근거 | 10 |

생성 후 수행한 자동 검사에서는 다음 항목을 확인했다.

- QA ID와 질문 150개가 모두 고유함
- 유사도 0.92 이상의 질문 쌍이 없음
- 모든 `source_row_ids`가 실제 Excel 행에 존재함
- 장·절·페이지와 근거 원문이 해당 Excel 행과 일치함
- 모든 답변이 1~2문장임
- 서로 다른 절의 원문을 하나의 답변 근거로 섞지 않음

자동 검사는 사람의 내용 검수를 대체하지 않는다. 최종 평가에 사용하기
전에는 `question`, `answer`, `evidence_text`를 함께 읽고 승인해야 한다.

## 4. 컬럼 설명

### 4.1 질문과 답변

| 컬럼 | 쉬운 설명 |
|---|---|
| `qa_id` | 문항을 구별하는 고유 번호이다. 예: `JAIJE1-QA-0001` |
| `question` | 제안 실무자가 물을 수 있는 자연어 질문이다. |
| `answer` | Excel 근거만 사용해 작성한 1~2문장의 기준 답변이다. |

### 4.2 Excel 출처와 원문 근거

| 컬럼 | 쉬운 설명 |
|---|---|
| `chapter_no` | 근거가 나온 장의 번호이다. |
| `chapter_title` | 근거가 나온 장의 제목이다. 예: `입찰과 제안` |
| `section_no` | 근거가 나온 절의 번호이다. 예: `1.1.1` |
| `section_title` | 근거가 나온 절의 제목이다. |
| `page` | 근거가 있는 모든 페이지 번호이다. 여러 페이지이면 배열로 저장된다. |
| `page_start` | 근거 페이지 중 가장 앞 페이지이다. |
| `page_end` | 근거 페이지 중 가장 뒤 페이지이다. |
| `evidence_text` | 답변을 직접 뒷받침하는 Excel 원문이다. 복수 근거이면 배열로 저장된다. |
| `source_row_ids` | `자이제_1.xlsx`에서 근거가 위치한 원본 행 번호이다. 원문을 다시 찾고 검증할 때 사용한다. |

`source_row_ids`는 Excel의 행을 가리키고, 아래에 나오는
`gold_evidence_span_ids`는 Neo4j의 EvidenceSpan 노드를 가리킨다. 두 값은
서로 다른 식별자이다.

### 4.3 문항 유형과 난이도

| 컬럼 | 쉬운 설명 |
|---|---|
| `question_type` | 질문의 유형이다. 아래 유형표를 참고한다. |
| `difficulty` | 원문에서 답을 찾고 결합하는 난이도이다. `easy`, `medium`, `hard` 중 하나이다. |
| `evidence_mode` | 근거 형태이다. `single_sentence`, `multi_sentence`, `table` 중 하나이다. |

`question_type` 값의 의미는 다음과 같다.

| 값 | 의미 |
|---|---|
| `fact` | 특정 사실이나 항목을 묻는 질문 |
| `numeric` | 금액, 비율, 개수 등 수치를 묻는 질문 |
| `definition` | 용어나 개념의 뜻을 묻는 질문 |
| `reason` | 원인이나 이유를 묻는 질문 |
| `method` | 수행 방법이나 권장 방법을 묻는 질문 |
| `comparison` | 둘 이상의 개념이나 방식을 비교하는 질문 |
| `procedure` | 순서나 절차를 묻는 질문 |
| `misconception` | 제안 실무의 오해가 맞는지 확인하고 바로잡는 질문 |

### 4.4 답변 가능 여부와 기대 동작

| 컬럼 | 쉬운 설명 |
|---|---|
| `answerable` | 현재 평가 문항에서 답변 가능한 질문인지 나타낸다. |
| `source_answerable` | Excel 원문만 보면 답이 존재하는지 나타낸다. 현재 150개는 모두 `true`이다. |
| `ontology_answerable` | 현재 Neo4j 온톨로지에서 정답과 근거 경로를 찾을 수 있는지 나타낸다. 아직 대조 전이므로 `null`이다. |
| `expected_behavior` | 시스템에 기대하는 동작이다. 현재 문항은 `answer_with_evidence`, 즉 근거를 사용한 답변을 기대한다. |
| `unanswerable_reason` | 답변 불가 질문이라면 그 이유를 기록한다. 현재 문항에서는 비어 있다. |
| `ontology_gap_reason` | Excel에는 답이 있지만 온톨로지에 없다면 누락 이유를 기록한다. |

`source_answerable=true`인데 `ontology_answerable=false`라면 Excel에는 정답이
있지만 그래프에서 찾을 수 없다는 뜻이다. 이 경우 RAG의 답변 생성 문제보다
온톨로지 적재 누락이나 관계 연결 오류를 먼저 확인해야 한다.

### 4.5 Neo4j 정답 경로 컬럼

다음 컬럼의 `gold`는 사람이 실제 Neo4j를 확인해 확정한 정답이라는 뜻이다.
이 값들은 모델이 추측해서 채우면 안 된다. 현재 버전에서는 비어 있으며,
온톨로지 대조 단계에서 안정적인 도메인 ID를 사용해 라벨링한다.

| 컬럼 | 쉬운 설명 |
|---|---|
| `gold_taskframe` | 질문이 연결되어야 하는 정답 TaskFrame의 안정적인 ID 또는 이름이다. |
| `gold_fact_ids` | 답변을 직접 나타내는 정답 Fact 노드의 안정적인 ID 목록이다. |
| `gold_evidence_span_ids` | 원문 근거에 해당하는 정답 EvidenceSpan 노드의 안정적인 ID 목록이다. |
| `gold_node_ids` | 검색기가 정답을 위해 찾아야 하는 전체 핵심 노드 ID 목록이다. |
| `gold_relation_types` | 정답 경로에 포함되어야 하는 관계 유형이다. 예: `HAS_CORE_FACT`, `SUPPORTED_BY` |
| `gold_path` | 정답에 도달하는 노드와 관계의 순서를 기록한 최소 충분 경로이다. |
| `min_hops` | 정답 경로에 필요한 최소 관계 이동 횟수이다. 관계 하나를 이동하면 1-hop이다. |

예를 들어 정답 경로가 다음과 같다면:

```text
TaskFrame
  → HAS_CORE_FACT
Fact
  → SUPPORTED_BY
EvidenceSpan
```

`gold_relation_types`는 `["HAS_CORE_FACT", "SUPPORTED_BY"]`이고,
`min_hops`는 노드 수가 아닌 관계 수를 세므로 `2`이다.

사람이 읽는 QA 검수에 이 컬럼들이 불필요하면 Excel에서 숨겨도 된다.
깊이 조절 연구에서는 적절한 1-hop, 2-hop 등을 평가하기 위해 `gold_path`와
`min_hops`를 나중에 채우는 것이 좋다. Neo4j를 다시 적재하면 바뀔 수 있는
내부 `elementId()`보다는 데이터에 저장된 안정적인 업무 ID나 근거 ID를
사용해야 한다.

### 4.6 데이터 분리와 사람 검수

| 컬럼 | 쉬운 설명 |
|---|---|
| `split` | 문항을 `train`, `dev`, `test` 중 어디에 사용할지 표시한다. 현재는 `unassigned`이다. |
| `review_status` | 사람 검수 상태이다. `pending`, `approved`, `revised`, `rejected` 등으로 관리한다. |
| `reviewer` | 문항을 검수한 사람의 이름이나 식별자이다. |
| `review_notes` | 수정 이유, 오류 내용, 판단 근거 등 검수 메모이다. |

깊이 정책이나 검색 임계값을 조정하는 문항은 `dev`, 조정이 끝난 시스템을
마지막으로 평가하는 문항은 `test`로 구분한다. 비슷한 원문이 양쪽에 섞여
성능이 과대평가되지 않도록 문항 단위보다 `section_no` 단위 분리를 권장한다.

### 4.7 생성 이력

| 컬럼 | 쉬운 설명 |
|---|---|
| `source_file` | QA 생성에 사용한 원본 파일명이다. |
| `sheet_name` | 원본 Excel에서 사용한 시트명이다. |
| `chunk_id` | 모델에 함께 전달한 원문 묶음의 식별자이다. 생성 과정을 추적할 때 사용한다. |
| `generation_model` | 질문과 답변 초안을 만든 OpenAI 모델명이다. |
| `generation_response_id` | 해당 생성 요청의 OpenAI 응답 식별자이다. 문제 발생 시 요청 단위를 추적하는 용도이다. |
| `prompt_version` | 생성에 사용한 프롬프트 버전이다. |
| `generated_at` | 문항을 생성한 UTC 시각이다. |

API 키는 데이터셋이나 생성 이력에 저장하지 않는다.

## 5. 권장 검수 순서

1. `question`, `answer`, `evidence_text`를 나란히 읽는다.
2. 답변의 모든 내용이 근거 원문에 포함되어 있는지 확인한다.
3. 질문이 실제 제안 실무자가 사용할 법한 자연어인지 확인한다.
4. 적합하면 `review_status=approved`로 변경한다.
5. 수정이 필요하면 답변이나 질문을 고치고 `review_status=revised`와
   `review_notes`를 기록한다.
6. 승인된 QA를 Neo4j와 대조해 `ontology_answerable`, `gold_path`,
   `min_hops`를 라벨링한다.
7. 최종적으로 section 단위 `dev`/`test` 분할을 확정한다.

## 6. CSV를 Excel에서 보는 방법

1. Excel에서 **데이터 → 텍스트/CSV에서**를 선택한다.
2. `qa_dataset.csv`를 선택하고 파일 원본은 UTF-8, 구분 기호는 쉼표로
   설정한다.
3. 첫 행 고정, 필터, 텍스트 줄 바꿈을 적용한다.
4. 우선 `qa_id`, `question`, `answer`, `chapter_title`, `section_no`,
   `page`, `evidence_text`, `source_row_ids`, `review_status`, `review_notes`
   컬럼만 표시하면 검수하기 쉽다.
