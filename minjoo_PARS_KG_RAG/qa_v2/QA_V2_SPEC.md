# 독립 수주·제안 QA V2 파일럿 명세

## 1. 목적

기존 150문항은 원문 행을 먼저 보여주고 질문을 생성했으므로 `Source-derived Direct Evidence Control`로 고정한다. V2 파일럿은 원문과 EvidenceSpan을 보지 않은 상태에서 실제 수주·제안 질문을 먼저 수집하고, 질문을 고정한 뒤 별도 검수자가 Gold 근거와 그래프 경로를 연결한다.

이 파일럿 60문항은 개발·진단용이다. 최종 성능 주장은 V2 검색기와 가중치를 동결한 뒤 별도의 독립 holdout에서만 한다.

## 2. 질문 수집 원칙

질문 작성자에게 다음을 보여주지 않는다.

- `자이제_1.xlsx` 원문
- Neo4j 노드·관계·속성
- 기존 150개 질문과 정답
- B0/P0/V2 검색 결과

허용되는 질문 출처:

- 수주·제안 실무자 인터뷰
- 실제 질의 로그 또는 교육·상담 질문
- 구체적인 실무 시나리오에서 자연스럽게 발생한 질문
- 전문가가 자신의 경험을 바탕으로 작성한 질문

질문을 특정 문장에 맞춰 다시 쓰거나, KG에 있는 관계를 보고 역으로 질문을 만들지 않는다. 개인·회사 비밀정보는 제거한다.

## 3. 60문항 진단 구성

| `query_stratum` | 문항 수 | 의미 |
|---|---:|---|
| `direct_lookup` | 10 | 단일 사실·정의·방법을 묻는 일반 질문 |
| `paraphrase_alias` | 10 | 원문과 다른 표현·약어·별칭을 사용한 질문 |
| `multi_evidence` | 10 | 최소 2개 근거를 결합해야 완전한 답이 되는 질문 |
| `pcf_hierarchy` | 10 | 표준 업무 분류·상하위 PCF 문맥이 필요한 질문 |
| `condition_relation` | 10 | 조건·예외·시점·비교·업무 관계를 묻는 질문 |
| `unanswerable_hard_negative` | 10 | 비슷한 지식은 있으나 현재 근거로 확정할 수 없는 질문 |

균등 구성은 KG가 유리하다는 전체 성능 주장을 위한 것이 아니라 오류 위치를 찾기 위한 진단 설계다.

## 4. Question-first, annotation-second 절차

1. 질문 작성자가 `question`, `question_origin`, `scenario_id`만 작성한다.
2. 질문을 고정하고 수정 이력을 남긴다.
3. 1차 검수자가 원문과 Neo4j를 검색해 답변 가능성을 판정한다.
4. 답변 가능한 경우 최소 충분 정답과 Gold Evidence/노드/경로를 기록한다.
5. 2차 검수자가 질문을 보존한 채 판정과 근거를 독립 확인한다.
6. 의견 불일치는 `review_notes`에 남기고 합의 후 `approved`로 변경한다.

정답을 찾기 쉽도록 질문 표현을 원문에 가깝게 수정하면 안 된다. 질문 자체가 모호하면 `rejected`로 처리하고 새 질문 ID를 발급한다.

## 5. 답변 가능성 판정

| `source_answerable` | `ontology_answerable` | 해석 |
|---|---|---|
| `true` | `true` | 원문과 현재 KG 모두 정답 근거를 가짐 |
| `true` | `false` | 원문에는 있으나 KG 구축 또는 연결이 누락됨 |
| `false` | `true` | 원문 외 구조 지식으로만 답할 수 있음; PCF 질문 등에서 가능 |
| `false` | `false` | 현재 시스템 범위에서는 답변 보류가 정답 |

`ontology_answerable`은 단순히 관련 노드가 있다는 뜻이 아니라, 허용된 경로가 최소 충분 근거에 도달한다는 뜻이다.

## 6. 주요 컬럼

- `question_origin`: `practitioner_interview`, `query_log`, `training_session`, `scenario_workshop` 중 하나
- `scenario_id`: 같은 업무 상황에서 나온 질문을 묶는 식별자
- `expected_behavior`: `answer_with_evidence`, `answer_with_limitation`, `abstain`
- `evidence_only_sufficient`: 원문 직접 검색만으로 충분한 답이 가능한지
- `graph_structure_required`: 분류·관계·복수 경로 등 그래프 구조가 최소 정답에 필요한지
- `gold_*_ids`: JSON 배열 문자열
- `gold_path`: 검수한 최소 충분 경로의 JSON 배열 또는 객체
- `min_hops`: 정답 경로의 최소 hop 수
- `split`: 이 60문항은 모두 `development`; 최종 holdout과 섞지 않음
- `review_status`: `draft`, `question_frozen`, `annotated`, `approved`, `rejected`

## 7. 품질 기준

- 질문은 원문 없이 독립적으로 이해 가능해야 한다.
- 정답의 모든 주장은 Gold Evidence 또는 검수된 구조 관계로 지지되어야 한다.
- 여러 근거가 필요하면 하나만으로 답이 완전해지지 않는 이유를 검수한다.
- PCF 질문은 단순히 코드 암기를 묻지 말고 실제 업무 분류 필요성이 있어야 한다.
- `PRECEDES` 등 관계는 관계 자체를 지지하는 근거가 없으면 Gold로 사용하지 않는다.
- 답변 불가 질문은 사람이 원문과 그래프를 모두 확인한 뒤 확정한다.
- 회사별 승인·규정·시스템 질문은 현재 Layer 3 부재를 명시한다.

## 8. 평가 순서

1. 60문항에서는 답변 생성 전에 검색만 비교한다.
2. B0, P0, V2의 Evidence Hit/Recall, MRR, TaskFrame/PCF Recall을 계산한다.
3. 복수 근거에는 `complete_evidence_set_at_5`, 구조 필수 문항에는 `complete_gold_node_chain`을 계산한다.
4. 관계 edge까지 포함한 Complete Evidence-Chain Recall은 관계 Gold와 검색 출력이 모두 검수된 뒤 추가한다.
5. 오류를 `ONTOLOGY_GAP`, `RETRIEVER_MISS`, `RERANKER_MISS`, `INCOMPLETE_CHAIN`, `CORRECT_ABSTENTION`, `FALSE_POSITIVE`로 분류한다.
6. 검색 개선이 확인된 경우에만 답변 생성과 사람 블라인드 평가를 수행한다.

## 9. V2 개발과 최종 평가의 분리

- 이 60문항에서 후보 수·quota·fusion weight를 조정할 수 있다.
- 조정 완료 후 코드와 설정을 동결한다.
- 실제 사용 분포의 Operational Set과 KG Challenge Set을 새로 수집한다.
- 최종 test 질문은 동결 전 검색·답변·프롬프트 조정에 사용하지 않는다.

## 10. 파일

- 수집 템플릿: `qa_v2_pilot_template.csv`
- 템플릿 검증: `python3 validate_qa_v2.py qa_v2_pilot_template.csv --allow-incomplete`
- 완성본 엄격 검증: `python3 validate_qa_v2.py <완성본.csv>`
- 최종 실험 설정: `../config/experiment.yaml`

검수가 끝난 파일은 다음처럼 검색 전용으로 실행한다.

```bash
python run_experiment.py \
  --config config/experiment.yaml \
  --qa-csv qa_v2/qa_v2_pilot.csv \
  --stage retrieve \
  --run-id v2_independent_pilot_<DATE>
```
