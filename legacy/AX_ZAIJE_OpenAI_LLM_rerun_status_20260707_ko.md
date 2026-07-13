# AX 자이제 Layer2 KG OpenAI API LLM 재실행 상태 보고

작성일: 2026-07-07  
대상 데이터: `자이제_1.xlsx`  
참고 설계서: `AX_ZAIJE_Layer2_KG_Methodology.md`  
기존 완료 산출물: `experiments/ax_zaije_layer2_kg_20260706/layer2_kg`  
OpenAI 재실행 목표 경로: `experiments/ax_zaije_layer2_kg_openai_20260707/layer2_kg`
실행 경로 상세 문서: `AX_ZAIJE_OpenAI_API_execution_path_20260707_ko.md`
OpenAI 실행 결과 문서: `AX_ZAIJE_OpenAI_LLM_experiment_result_20260707_ko.md`

---

## 1. 목적

기존 `자이제_1.xlsx` Layer2 KG 구축은 설계서의 LLM 입출력 구조를 보존했지만, 실제 LLM 추론은 사용하지 않은 deterministic MVP였다.

2026-07-07에 OpenAI API quota 충전 후 `gpt-4o-mini` 기반 실제 LLM 재실행을 완료했다. 현재 최신 결과는 다음 경로에 있다.

```text
experiments/ax_zaije_layer2_kg_openai_20260707/layer2_kg
```

이번 수정의 목적은 로컬 Qwen 실행 대신 OpenAI API의 저비용 모델을 사용해 다음 두 단계를 실제 LLM 호출로 수행하는 것이다.

| 단계 | LLM 역할 | 입력 단위 | 출력 |
|---|---|---|---|
| Task Frame linking | 섹션 원문을 기존 canonical Task catalog에 연결 | `section_summary_chunk` | `19_openai_task_frame_links.raw.jsonl` |
| Triple extraction | 문단 원문에서 schema-constrained SPO 관계 추출 | `paragraph_chunk` | `20_openai_triples.raw.jsonl` |

---

## 2. 구현한 실행 방식

새로 추가한 스크립트는 다음이다.

```text
scripts/run_ax_zaije_openai_llm_kg.py
scripts/run_ax_zaije_openai_llm_kg.sh
```

기본 모델은 `gpt-4o-mini`로 설정했다. 이유는 구조화 JSON 출력에 적합하고, 전체 chunk 추출을 반복 호출해야 하는 이번 실험에서 비용 부담이 상대적으로 낮기 때문이다.

API key는 파일에 저장하지 않고 `OPENAI_API_KEY` 환경변수에서만 읽는다.

---

## 3. LLM 프롬프트 설계

### 3.1 Task Frame linking

Task Frame 단계에서는 LLM이 task를 마음대로 새로 만들지 않도록, 먼저 설계서 기반 canonical task catalog 15개를 제공한다.

입력에는 다음 정보가 들어간다.

| 입력 필드 | 의미 |
|---|---|
| `document_metadata` | book, chapter, section, chunk id |
| `section_text` | section summary chunk 원문 |
| `canonical_task_catalog` | 15개 canonical DomainTask |
| `evidence_candidates` | 해당 chunk의 EvidenceSpan 목록 |
| `output_schema` | task 연결 결과 JSON 구조 |

LLM 출력은 다음 구조를 요구한다.

```json
{
  "chunk_id": "ZAIJE_SEC_1_3_1_SUMMARY",
  "task_frame_links": [
    {
      "task_id": "L2_TASK_CAPTURE_PLANNING",
      "evidence_ids": ["EV_ZAIJE_000211"],
      "observed_inputs": [],
      "observed_outputs": [],
      "observed_roles": [],
      "observed_decision_points": [],
      "confidence": 0.85,
      "rationale": "섹션에서 수주영업 프로세스와 준비 활동이 직접 언급됨"
    }
  ],
  "candidate_new_task_frames": [],
  "candidate_terms": [],
  "review_notes": []
}
```

### 3.2 Triple extraction

Triple 단계에서는 LLM이 자유롭게 node와 predicate를 생성하지 못하도록 세 가지 제약을 함께 제공한다.

| 제약 | 내용 |
|---|---|
| `candidate_nodes` | Process + canonical Task + 해당 chunk와 관련 있는 canonical Entity |
| `allowed_predicates` | Layer2 schema에 정의된 predicate/domain/range |
| `evidence_candidates` | 해당 paragraph chunk의 EvidenceSpan |

LLM 출력은 다음 구조를 요구한다.

```json
{
  "chunk_id": "ZAIJE_SEC_1_3_1_CHUNK_001",
  "triples": [
    {
      "subject_id": "L2_TASK_CAPTURE_PLANNING",
      "predicate": "PRODUCES",
      "object_id": "L2_ARTIFACT_CAPTURE_PLAN",
      "frame_task_id": "L2_TASK_CAPTURE_PLANNING",
      "evidence_ids": ["EV_ZAIJE_000217"],
      "evidence_span": "세 분야란 수주영업...",
      "confidence": 0.84,
      "relation_scope": "process_step",
      "rationale": "원문에서 수주영업의 산출/관리 대상이 확인됨"
    }
  ],
  "new_node_candidates": [],
  "review_notes": []
}
```

---

## 4. 기존 deterministic MVP와 달라진 점

| 구분 | 기존 2026-07-06 완료본 | OpenAI API 재실행 설계 |
|---|---|---|
| Task Frame 생성 | seed catalog + 규칙 기반 evidence 연결 | OpenAI LLM이 section evidence를 task에 연결 |
| Triple 생성 | 규칙 기반 seed triple 생성 | OpenAI LLM이 paragraph chunk에서 SPO 추출 |
| Predicate 통제 | 코드 validator | prompt 제약 + 코드 validator |
| Evidence 통제 | 규칙 기반 evidence search | LLM evidence id 선택 + 코드 검증 |
| Graph materialization | 기존 코드 | 기존 코드 재사용 |
| Neo4j/RDF export | 생성 완료 | 동일 구조로 생성 예정 |

중요한 점은 OpenAI 재실행에서도 ontology 전체를 LLM에게 자유 생성시키지 않는다는 것이다. 설계서의 Layer2 schema와 canonical node inventory를 먼저 고정한 뒤, LLM은 원문 evidence를 기반으로 relation 후보를 추출한다.

---

## 5. 실제 실행 결과

2026-07-07에 다음 범위로 전체 실행을 진행했다.

| 항목 | 값 |
|---|---:|
| 모델 | `gpt-4o-mini` |
| Task Frame LLM calls | 51 |
| Triple LLM calls | 110 |
| LLM accepted triples | 188 |
| LLM rejected triples | 100 |
| Validated triples | 103 |
| Graph nodes | 1,869 |
| Graph edges | 2,283 |
| CQ passed | 0 / 7 |
| estimated cost | USD 0.162064 |
| API key 저장 | 없음 |
| 실행 방식 | 프로세스 환경변수로만 주입 |

초기 smoke test에서는 quota 오류가 있었지만, 충전 후 전체 실행은 완료되었다.

이전 오류는 다음과 같았다.

```text
HTTP 429
type: insufficient_quota
code: insufficient_quota
message: You exceeded your current quota, please check your plan and billing details.
```

따라서 현재 상태는 다음과 같다.

```text
OpenAI API 기반 LLM 재실행 완료.
다만 CQ exact path 기준은 0/7이므로, 다음 단계에서 CQ-aware reprompt와 사람 검수가 필요함.
```

---

## 6. 재실행 방법

같은 실험을 다시 실행하려면 다음을 사용한다.

```bash
cd /home/minjoo/AX_서울펠로우
export OPENAI_API_KEY='OpenAI_API_key'
bash scripts/run_ax_zaije_openai_llm_kg.sh
```

전체 실행은 기본적으로 다음을 수행한다.

| 처리 | 대상 개수 |
|---|---:|
| section summary chunk 기반 Task Frame linking | 51 |
| paragraph chunk 기반 Triple extraction | 110 |
| Source Evidence Graph 재생성 | 1,366 EvidenceSpan |
| KG node/edge materialization | 기존 구조 유지 |
| CQ evaluation | 7개 |
| Neo4j/RDF export | 생성 |

---

## 7. 정상 실행 시 생성될 핵심 파일

```text
experiments/ax_zaije_layer2_kg_openai_20260707/layer2_kg/
  19_openai_task_frame_links.raw.jsonl
  20_openai_triples.raw.jsonl
  21_openai_triples.accepted.jsonl
  22_openai_triples.rejected.jsonl
  23_openai_usage_and_cost.json
  24_openai_llm_run_report.md
  08_triples.raw.jsonl
  09_triples.validated.jsonl
  10_nodes.jsonl
  11_edges.jsonl
  12_quality_report.md
  14_neo4j_import/nodes.csv
  14_neo4j_import/edges.csv
  14_neo4j_import/import.cypher
```

---

## 8. 교수님께 보고할 때의 정확한 표현

현재까지 확정적으로 말할 수 있는 표현은 다음이다.

```text
자이제 데이터에 대해 Layer2 KG deterministic MVP 구축은 완료되었다.
이후 OpenAI API 기반 실제 LLM 재실행도 완료했다.
gpt-4o-mini로 Task Frame linking 51회와 Triple extraction 110회를 수행했고,
LLM accepted triple 188개, schema-validated triple 103개를 얻었다.
다만 CQ exact path 기준은 0/7이므로, 현재 결과는 gold KG가 아니라 LLM 기반 bootstrap KG이다.
```

피해야 할 표현은 다음이다.

```text
OpenAI LLM 결과가 사람 검수까지 끝난 gold KG이다.
```

이 표현은 아직 사실이 아니다.
