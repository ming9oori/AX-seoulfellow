# AX 자이제 Layer2 KG OpenAI API 실행 절차 상세 정리

작성일: 2026-07-08  
실행 완료 시각: 2026-07-07T06:50:14Z  
입력 데이터: `자이제_1.xlsx`  
방법론 문서: `AX_ZAIJE_Layer2_KG_Methodology.md`  
실행 스크립트: `scripts/run_ax_zaije_openai_llm_kg.py`  
실행 모델: `gpt-4o-mini`  
최종 산출물 경로: `experiments/ax_zaije_layer2_kg_openai_20260707/layer2_kg`

---

## 1. 이번 실행의 목적

기존 `자이제_1.xlsx` 기반 Layer2 KG는 deterministic MVP였다. 즉, 설계서의 LLM 입출력 구조는 보존했지만 실제 LLM 추론으로 triple을 추출하지는 않았다.

이번 실행에서는 다음 두 부분을 실제 OpenAI API LLM 호출로 교체했다.

| 단계 | 기존 deterministic MVP | 이번 OpenAI API 실행 |
|---|---|---|
| Task Frame 처리 | seed catalog와 규칙 기반 evidence 연결 | section summary chunk를 OpenAI API에 넣어 canonical Task와 evidence 연결 |
| Triple 추출 | 규칙 기반 seed triple 생성 | paragraph chunk를 OpenAI API에 넣어 SPO triple 추출 |

중요한 점은 ontology 전체를 LLM에게 자유 생성시키지 않았다는 것이다. Layer2 schema, canonical task, canonical entity inventory는 설계서 기반으로 고정하고, LLM은 원문 evidence에 근거한 relation 후보를 제안하도록 제한했다.

---

## 2. 실제 실행 전 준비

### 2.1 API key 처리

OpenAI API key는 파일에 저장하지 않았다. 실행 프로세스의 환경변수로만 주입했다.

검증 결과, repository 안에는 API key 문자열이 저장되어 있지 않다.

```bash
rg -n "sk-proj-|sk-[A-Za-z0-9_-]{20,}" .
```

위 검색에서 key 저장 흔적은 발견되지 않았다.

### 2.2 실행 환경

시스템 기본 Python은 3.8이지만, 기존 스크립트의 type hint와 실행 환경을 고려해 conda `py311` 환경을 사용했다.

```bash
/home/minjoo/miniconda3/envs/py311/bin/python
```

문법 검사는 다음으로 수행했다.

```bash
/home/minjoo/miniconda3/envs/py311/bin/python -m py_compile \
  scripts/run_ax_zaije_openai_llm_kg.py \
  scripts/build_ax_zaije_layer2_kg.py
```

---

## 3. 실행 명령

전체 실행은 최종적으로 다음 형태로 수행했다.

```bash
cd /home/minjoo/AX_서울펠로우
rm -rf experiments/ax_zaije_layer2_kg_openai_20260707

read -r -s OPENAI_API_KEY
export OPENAI_API_KEY

/home/minjoo/miniconda3/envs/py311/bin/python \
  scripts/run_ax_zaije_openai_llm_kg.py \
  --model gpt-4o-mini \
  --output-dir experiments/ax_zaije_layer2_kg_openai_20260707/layer2_kg \
  --timeout 240 \
  --sleep 0.02
```

실제 재실행용 wrapper는 다음 파일이다.

```text
scripts/run_ax_zaije_openai_llm_kg.sh
```

일반 재실행은 아래처럼 하면 된다.

```bash
cd /home/minjoo/AX_서울펠로우
export OPENAI_API_KEY='OpenAI_API_key'
bash scripts/run_ax_zaije_openai_llm_kg.sh
```

---

## 4. 실행 진행 순서

전체 파이프라인은 아래 순서로 진행되었다.

```text
자이제_1.xlsx
→ Excel row 읽기
→ row 정규화
→ SourceChunk / EvidenceSpan 생성
→ deterministic seed Task catalog 생성
→ OpenAI Task Frame linking 실행
→ OpenAI Triple extraction 실행
→ LLM 응답을 accepted/rejected triple로 변환
→ schema scaffold triple과 accepted LLM triple 병합
→ Layer2 schema validator 실행
→ nodes/edges materialization
→ CQ evaluation
→ review queue 생성
→ Neo4j/RDF export
→ run_summary / quality report / OpenAI report 생성
```

---

## 5. 입력 데이터 처리 방식

### 5.1 Excel 입력

입력 파일은 다음이다.

```text
자이제_1.xlsx
```

사용한 주요 컬럼은 다음이다.

| 컬럼 | 사용 목적 |
|---|---|
| `page` | EvidenceSpan page locator |
| `chapter_no` | Chapter node 생성 |
| `chapter_title` | Chapter label |
| `section_no` | Section grouping |
| `section_title` | Section label 및 prompt metadata |
| `text_for_llm_human` | LLM 입력 및 evidence text |

총 유효 문장 행은 1,366개였다.

### 5.2 SourceChunk 생성

문장 단위 evidence만으로는 LLM이 문맥을 잃을 수 있으므로 두 종류의 chunk를 만들었다.

| chunk 유형 | 역할 | 개수 |
|---|---|---:|
| `section_summary_chunk` | Task Frame linking 입력 | 51 |
| `paragraph_chunk` | Triple extraction 입력 | 110 |

전체 SourceChunk 수는 166개이다. section summary와 paragraph 외에 definition/table/figure 성격의 chunk도 일부 포함된다.

### 5.3 EvidenceSpan 생성

각 유효 문장 행을 하나의 `EvidenceSpan`으로 만들었다.

```text
EvidenceSpan 수: 1,366
```

모든 LLM triple은 최종적으로 이 EvidenceSpan id를 참조해야 KG에 들어갈 수 있게 했다.

---

## 6. OpenAI LLM 호출 1단계: Task Frame linking

### 6.1 목적

Task Frame linking은 section 단위 텍스트를 보고, 설계서 기반 canonical Task catalog 15개 중 어떤 task와 관련되는지 evidence와 함께 연결하는 단계이다.

### 6.2 입력

각 section summary chunk마다 다음 정보를 OpenAI API에 제공했다.

| 입력 | 내용 |
|---|---|
| `document_metadata` | book id, chapter, section, chunk id |
| `section_text` | section summary 원문 |
| `canonical_task_catalog` | 설계서 기반 15개 DomainTask |
| `evidence_candidates` | 해당 section 안의 EvidenceSpan 목록 |
| `output_schema` | JSON 응답 구조 |

### 6.3 출력

출력은 다음 파일에 저장했다.

```text
19_openai_task_frame_links.raw.jsonl
```

Task Frame LLM 호출 수는 51회였다.

```text
Task Frame LLM calls: 51
```

---

## 7. OpenAI LLM 호출 2단계: Triple extraction

### 7.1 목적

Triple extraction은 paragraph chunk를 보고 Layer2 KG에 들어갈 수 있는 subject-predicate-object 후보를 추출하는 단계이다.

### 7.2 입력

각 paragraph chunk마다 다음 정보를 OpenAI API에 제공했다.

| 입력 | 내용 |
|---|---|
| `chunk` | paragraph 원문과 metadata |
| `candidate_nodes` | Process + Task + 해당 text와 관련 있는 canonical Entity |
| `allowed_predicates` | Layer2 schema의 predicate/domain/range |
| `evidence_candidates` | 해당 paragraph 안의 EvidenceSpan 목록 |
| `relation_scope_options` | process_step, definition 등 relation scope |
| `output_schema` | JSON triple 응답 구조 |

LLM이 자유롭게 predicate를 만들지 못하도록 allowed predicate 목록 안에서만 선택하게 했다.

### 7.3 출력

출력은 다음 파일에 저장했다.

```text
20_openai_triples.raw.jsonl
```

Triple LLM 호출 수는 110회였다.

```text
Triple LLM calls: 110
```

---

## 8. LLM 응답 변환 방식

OpenAI 응답은 바로 KG에 넣지 않았다. 먼저 자동 변환 단계에서 accepted/rejected로 나누었다.

### 8.1 Accepted 조건

LLM triple이 accepted 되려면 다음을 만족해야 했다.

| 조건 | 설명 |
|---|---|
| subject id 검증 | canonical node id에 존재해야 함 |
| object id 검증 | canonical node id에 존재해야 함 |
| predicate 검증 | Layer2 allowed predicate여야 함 |
| frame task id 검증 | canonical task id이거나 비어 있어야 함 |
| evidence id 검증 | 실제 EvidenceSpan id를 참조해야 함 |
| duplicate 검증 | 동일 SPO가 이미 accepted 되지 않아야 함 |

### 8.2 Accepted / Rejected 결과

| 항목 | 수 |
|---|---:|
| LLM accepted triples | 188 |
| LLM rejected triples | 100 |

Rejected 100개 중 97개는 `duplicate_spo`였다. 즉, 대부분은 LLM이 같은 관계를 여러 evidence에서 반복 제안한 경우이다.

---

## 9. Schema validation 방식

Accepted triple도 최종 KG에 바로 들어가지 않았다. 다음 Layer2 schema validator를 다시 통과해야 했다.

| 검증 | 의미 |
|---|---|
| predicate validation | predicate가 schema에 있는지 확인 |
| domain validation | subject node type이 predicate domain에 맞는지 확인 |
| range validation | object node type이 predicate range에 맞는지 확인 |
| evidence validation | evidence_refs가 실제 EvidenceSpan을 가리키는지 확인 |
| confidence validation | threshold 미만 confidence 제외 |

최종 validated triple 수는 103개였다.

```text
Raw triples: 209
Validated triples: 103
```

여기서 raw triples 209개는 최소 graph connectivity를 위한 schema scaffold triple과 accepted LLM triple을 합친 값이다.

---

## 10. KG materialization 방식

검증된 triple과 source evidence graph를 결합해 최종 graph node와 edge를 만들었다.

### 10.1 Node 생성

최종 node 수는 1,869개이다.

주요 node type 분포는 다음과 같다.

| Node type | Count |
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

### 10.2 Edge 생성

최종 edge 수는 2,283개이다.

주요 predicate 분포는 다음과 같다.

| Predicate | Count |
|---|---:|
| `EVIDENCED_BY` | 1,759 |
| `ALIAS_OF` | 201 |
| `HAS_CHUNK` | 166 |
| `HAS_SECTION` | 51 |
| `HAS_TASK` | 38 |
| `USES_INPUT` | 12 |
| `TARGETS_STAKEHOLDER` | 9 |
| `DISCOVERS` | 9 |
| `PRODUCES` | 7 |
| `HAS_PROCESS` | 6 |

---

## 11. 비용과 사용량

OpenAI API 사용량은 다음과 같다.

| 항목 | 값 |
|---|---:|
| Prompt tokens | 782,179 |
| Completion tokens | 74,562 |
| Total tokens | 856,741 |
| 추정 비용 | USD 0.162064 |

비용은 스크립트에 기록된 `gpt-4o-mini` 기준 단가로 계산한 추정치이며, 실제 청구 금액은 OpenAI project 설정에 따라 달라질 수 있다.

---

## 12. CQ 평가 결과

Competency Question은 7개 모두 exact path 기준으로는 통과하지 못했다.

| CQ | 질문 | 결과 | 체크 |
|---|---|---|---:|
| CQ1 | 제안전략을 세우기 전에 어떤 정보와 산출물이 필요한가? | FAIL | 2/3 |
| CQ2 | Capture Plan은 어떤 업무에서 생성되고 어디에 사용되는가? | FAIL | 1/2 |
| CQ3 | Bid/No-Bid 의사결정은 어느 단계에서 발생하며 어떤 입력을 쓰는가? | FAIL | 1/2 |
| CQ4 | 평가자 유형에 따라 커뮤니케이션은 어떻게 달라지는가? | FAIL | 0/3 |
| CQ5 | 리스크 관리는 어떻게 차별화 포인트로 이어지는가? | FAIL | 0/2 |
| CQ6 | 제안서 작성 단계에서 어떤 리뷰 또는 마일스톤이 필요한가? | FAIL | 1/3 |
| CQ7 | 고객의 공식 요구조건과 비공식 요구조건은 어떻게 구분되는가? | FAIL | 1/2 |

이 결과는 LLM이 evidence-grounded triple은 만들었지만, downstream CQ가 요구하는 특정 graph path를 안정적으로 구성하지는 못했다는 뜻이다.

---

## 13. 최종 산출물

핵심 산출물은 다음 경로에 있다.

```text
experiments/ax_zaije_layer2_kg_openai_20260707/layer2_kg/
```

주요 파일은 다음이다.

| 파일 | 의미 |
|---|---|
| `19_openai_task_frame_links.raw.jsonl` | Task Frame linking 원본 OpenAI 응답 |
| `20_openai_triples.raw.jsonl` | Triple extraction 원본 OpenAI 응답 |
| `21_openai_triples.accepted.jsonl` | 1차 변환 조건 통과 LLM triple |
| `22_openai_triples.rejected.jsonl` | 1차 변환 단계 제외 triple |
| `23_openai_usage_and_cost.json` | token 사용량과 비용 추정 |
| `24_openai_llm_run_report.md` | OpenAI 실행 요약 |
| `08_triples.raw.jsonl` | scaffold + accepted LLM triple |
| `09_triples.validated.jsonl` | schema validator 통과 triple |
| `10_nodes.jsonl` | 최종 KG node |
| `11_edges.jsonl` | 최종 KG edge |
| `12_quality_report.md` | 품질 평가 보고서 |
| `13_review_queue.xlsx` | 사람 검수용 queue |
| `14_neo4j_import/nodes.csv` | Neo4j node import |
| `14_neo4j_import/edges.csv` | Neo4j edge import |
| `14_neo4j_import/import.cypher` | Neo4j import Cypher |

---

## 14. 이번 실행의 의미

이번 실행으로 확인한 것은 다음이다.

1. OpenAI API를 사용해 실제 LLM 기반 Layer2 KG bootstrap을 수행할 수 있었다.
2. LLM 응답을 바로 쓰지 않고 schema, canonical node, evidence id 기준으로 자동 검증했다.
3. Evidence grounding, predicate validity, task orphan 같은 구조 품질은 통과했다.
4. 그러나 CQ exact path 기준은 0/7로, LLM 단독 추출만으로는 downstream graph query 요구사항을 만족하기 어렵다는 점이 확인되었다.

따라서 현재 결과는 다음과 같이 표현하는 것이 정확하다.

```text
OpenAI API LLM 기반 Layer2 KG bootstrap 구축 완료.
단, 사람 검수 및 CQ-aware 보강 전이므로 gold KG는 아님.
```

---

## 15. 다음 단계

다음 단계는 단순 재실행보다 CQ 보강에 초점을 맞추는 것이 적절하다.

1. CQ-aware reprompt
   - 실패한 CQ별 missing edge를 계산한다.
   - 관련 evidence span과 candidate node를 OpenAI에 다시 넣어 보강 triple을 추출한다.

2. duplicate SPO evidence 병합
   - 현재는 duplicate SPO가 rejected 처리된다.
   - 같은 SPO에 여러 evidence_refs를 병합하면 edge grounding이 더 풍부해진다.

3. CQ-critical predicate 보강
   - `USED_AS_INPUT_FOR`
   - `MITIGATES`
   - `MAY_RESULT_IN`
   - `REFINES_INTO`

4. 사람 검수
   - `13_review_queue.xlsx`를 기반으로 task, edge, alias를 검토한다.

