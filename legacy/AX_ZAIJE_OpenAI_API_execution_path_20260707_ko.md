# AX 자이제 Layer2 KG OpenAI API 실행 경로

작성일: 2026-07-07  
대상 데이터: `자이제_1.xlsx`  
실행 목적: deterministic MVP를 실제 OpenAI API 기반 LLM 추출 경로로 전환  
기본 모델: `gpt-4o-mini`
실행 결과 문서: `AX_ZAIJE_OpenAI_LLM_experiment_result_20260707_ko.md`

---

## 1. 현재 확정한 실행 경로

이번 실험의 LLM 실행 경로는 **로컬 Qwen/GPU 실행이 아니라 OpenAI API 실행**으로 고정한다.

```text
자이제_1.xlsx
→ Source Evidence Graph 재생성
→ canonical Task / Entity inventory 생성
→ OpenAI API Task Frame linking
→ OpenAI API Triple extraction
→ schema/domain/range/evidence validation
→ Layer2 KG nodes/edges 생성
→ CQ evaluation
→ Neo4j/RDF export
```

이 경로에서 GPU는 사용하지 않는다. LLM 추론은 OpenAI API 서버에서 수행되고, 현재 서버는 입력 chunk 구성, API 요청, 응답 검증, KG materialization만 수행한다.

---

## 2. 실행 스크립트

핵심 스크립트는 다음 두 개이다.

```text
scripts/run_ax_zaije_openai_llm_kg.py
scripts/run_ax_zaije_openai_llm_kg.sh
```

`run_ax_zaije_openai_llm_kg.py`는 실제 파이프라인을 수행한다.  
`run_ax_zaije_openai_llm_kg.sh`는 기본 모델, 출력 경로, Python 경로를 지정해 실행을 단순화한다.

기본 출력 경로는 다음이다.

```text
experiments/ax_zaije_layer2_kg_openai_20260707/layer2_kg
```

---

## 3. OpenAI API key 설정 방식

API key는 파일에 저장하지 않는다.

실행 직전에 셸 환경변수로만 설정한다.

```bash
export OPENAI_API_KEY='quota가_있는_OpenAI_API_key'
```

그 다음 실행한다.

```bash
cd /home/minjoo/AX_서울펠로우
bash scripts/run_ax_zaije_openai_llm_kg.sh
```

다른 모델을 쓰고 싶으면 다음처럼 바꾼다.

```bash
OPENAI_MODEL=gpt-4.1-mini bash scripts/run_ax_zaije_openai_llm_kg.sh
```

기본값은 비용을 고려해 `gpt-4o-mini`이다.

---

## 4. LLM 호출 1단계: Task Frame linking

입력 대상은 `section_summary_chunk`이다.

현재 데이터에서는 section summary chunk가 51개 생성된다.

LLM에는 다음을 제공한다.

| 입력 | 내용 |
|---|---|
| section metadata | chapter, section, chunk id |
| section text | 해당 섹션의 원문 묶음 |
| canonical task catalog | 설계서 기반 15개 DomainTask |
| evidence candidates | 해당 section 안의 EvidenceSpan id와 text |

LLM은 새 ontology를 마음대로 만들지 않고, 기존 canonical task에 evidence를 연결한다.

출력 파일:

```text
19_openai_task_frame_links.raw.jsonl
```

---

## 5. LLM 호출 2단계: Triple extraction

입력 대상은 `paragraph_chunk`이다.

현재 데이터에서는 paragraph chunk가 110개 생성된다.

LLM에는 다음을 제공한다.

| 입력 | 내용 |
|---|---|
| paragraph chunk | 문단 단위 원문 |
| candidate nodes | Process + Task + 관련 canonical Entity |
| allowed predicates | Layer2 schema의 predicate/domain/range |
| evidence candidates | 해당 paragraph 안의 EvidenceSpan |

LLM은 `subject_id`, `predicate`, `object_id`, `evidence_ids`를 JSON으로 반환한다.

출력 파일:

```text
20_openai_triples.raw.jsonl
```

---

## 6. 자동 검증 및 KG 생성

OpenAI 응답은 바로 KG에 들어가지 않는다. 다음 조건을 통과한 triple만 사용한다.

| 검증 항목 | 기준 |
|---|---|
| subject 검증 | canonical node id에 존재해야 함 |
| object 검증 | canonical node id에 존재해야 함 |
| predicate 검증 | Layer2 schema에 정의되어 있어야 함 |
| domain/range 검증 | predicate의 허용 node type과 맞아야 함 |
| evidence 검증 | 실제 `EvidenceSpan` id를 참조해야 함 |
| confidence 검증 | 최소 threshold 이상이어야 함 |

검증 결과는 다음 파일로 나뉜다.

```text
21_openai_triples.accepted.jsonl
22_openai_triples.rejected.jsonl
```

이후 accepted triple과 schema scaffold를 합쳐 최종 KG를 만든다.

```text
08_triples.raw.jsonl
09_triples.validated.jsonl
10_nodes.jsonl
11_edges.jsonl
```

---

## 7. Neo4j 실행 경로

OpenAI API 경로로 KG가 정상 생성되면 Neo4j import 파일도 같은 출력 폴더 아래에 생성된다.

```text
14_neo4j_import/nodes.csv
14_neo4j_import/edges.csv
14_neo4j_import/import.cypher
```

Neo4j Browser에서 사용할 때는 `nodes.csv`, `edges.csv`를 Neo4j import directory에 넣고 `import.cypher`를 실행한다.

---

## 8. 실행 완료 상태

초기 smoke test에서는 API 서버가 다음 오류를 반환했다.

```text
HTTP 429
type: insufficient_quota
code: insufficient_quota
message: You exceeded your current quota, please check your plan and billing details.
```

이 의미는 다음 중 하나이다.

| 가능 원인 | 의미 |
|---|---|
| 결제 미등록 | 해당 project/key로 API 과금이 불가능함 |
| 무료 credit 소진 | 사용할 수 있는 credit이 없음 |
| monthly usage limit 도달 | 설정된 월 사용 한도에 도달함 |
| project budget limit 도달 | 해당 project 예산 제한에 걸림 |
| key가 다른 project에 연결됨 | quota가 없는 project의 key를 사용 중 |

이는 KG 코드나 프롬프트 오류가 아니라 **OpenAI 계정/project의 사용 가능량 문제**였다. 이후 quota 충전 후 전체 실행은 완료되었다.

최신 완료 수치는 다음이다.

| 항목 | 값 |
|---|---:|
| Task Frame LLM calls | 51 |
| Triple LLM calls | 110 |
| LLM accepted triples | 188 |
| LLM rejected triples | 100 |
| Validated triples | 103 |
| Graph nodes | 1,869 |
| Graph edges | 2,283 |
| CQ passed | 0 / 7 |
| estimated cost | USD 0.162064 |

---

## 9. 재실행 명령

같은 OpenAI API 실행 경로를 다시 돌리려면 다음을 실행한다.

```bash
cd /home/minjoo/AX_서울펠로우
export OPENAI_API_KEY='OpenAI_API_key'
bash scripts/run_ax_zaije_openai_llm_kg.sh
```

중간에 끊겨도 `--resume`이 기본 적용되어 이미 완료한 chunk는 재사용한다.

---

## 10. 교수님께 보고할 표현

정확한 현재 표현은 다음이다.

```text
자이제 데이터에 대한 Layer2 KG deterministic MVP는 구축 완료되었다.
이후 실제 LLM 추출을 위해 실행 경로를 OpenAI API 기반으로 전환했으며,
gpt-4o-mini를 사용한 Task Frame linking 및 Triple extraction 파이프라인을 구현했다.
quota 충전 후 전체 실행까지 완료했으며,
LLM accepted triple 188개와 schema-validated triple 103개를 얻었다.
다만 CQ exact path 기준은 0/7이므로, 다음 단계는 CQ-aware reprompt와 사람 검수이다.
```
