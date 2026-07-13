# AX 자이제 Layer2 KG OpenAI API LLM 실험 결과

작성일: 2026-07-07  
입력 데이터: `자이제_1.xlsx`  
방법론 문서: `AX_ZAIJE_Layer2_KG_Methodology.md`  
실행 스크립트: `scripts/run_ax_zaije_openai_llm_kg.py`  
모델: `gpt-4o-mini`  
최종 산출물 경로: `experiments/ax_zaije_layer2_kg_openai_20260707/layer2_kg`

---

## 1. 실행 완료 요약

OpenAI API quota 충전 후, `gpt-4o-mini`를 사용해 Layer2 KG 구축 실험을 처음부터 다시 실행했다.

이번 실행은 기존 deterministic MVP와 달리 다음 두 단계에서 실제 OpenAI API LLM 추론을 사용했다.

| 단계 | 입력 | LLM 역할 | 호출 수 |
|---|---|---|---:|
| Task Frame linking | section summary chunk | 원문 section을 canonical Task catalog에 evidence 기반으로 연결 | 51 |
| Triple extraction | paragraph chunk | 원문 paragraph에서 schema-constrained SPO triple 추출 | 110 |

총 OpenAI API 호출 수는 161회였다.

---

## 2. 주요 정량 결과

| 항목 | 결과 |
|---|---:|
| 유효 문장 행 | 1,366 |
| SourceChunk | 166 |
| EvidenceSpan | 1,366 |
| Task Frame LLM rows | 51 |
| Triple LLM rows | 110 |
| LLM accepted triples | 188 |
| LLM rejected triples | 100 |
| Raw triples | 209 |
| Validated triples | 103 |
| Graph nodes | 1,869 |
| Graph edges | 2,283 |
| Review queue rows | 21 |
| CQ 통과 | 0 / 7 |

`LLM accepted triples`는 OpenAI 응답 중 canonical node id, allowed predicate, evidence id 등 1차 변환 조건을 통과한 triple이다.  
`Validated triples`는 그 이후 Layer2 schema validator의 domain/range/evidence 조건까지 통과한 triple이다.

---

## 3. OpenAI API 사용량과 비용 추정

| 항목 | 값 |
|---|---:|
| Prompt tokens | 782,179 |
| Completion tokens | 74,562 |
| Total tokens | 856,741 |
| 추정 비용 | USD 0.162064 |

비용은 스크립트에 기록된 `gpt-4o-mini` 기준 단가로 계산한 추정치이다. 실제 청구 금액은 OpenAI project 설정, service tier, caching 여부에 따라 달라질 수 있다.

---

## 4. LLM이 추출한 predicate 분포

| Predicate | Accepted LLM triples |
|---|---:|
| `HAS_TASK` | 93 |
| `DISCOVERS` | 20 |
| `HAS_PROCESS` | 12 |
| `TARGETS_STAKEHOLDER` | 12 |
| `USES_INPUT` | 12 |
| `PRODUCES` | 8 |
| `HAS_SUBTASK` | 7 |
| `PERFORMED_BY` | 5 |
| `CONTAINS` | 4 |
| `HAS_PRINCIPLE` | 4 |
| `PART_OF` | 3 |
| `HAS_DECISION_POINT` | 2 |
| `HAS_REVIEW` | 2 |
| `ANALYZES` | 2 |
| `DECIDES` | 1 |
| `DEVELOPS` | 1 |

LLM은 `HAS_TASK`, `DISCOVERS`, `TARGETS_STAKEHOLDER`, `USES_INPUT` 계열 관계를 많이 제안했다. 반면 `MITIGATES`, `MAY_RESULT_IN`, `REFINES_INTO`, `USED_AS_INPUT_FOR`처럼 CQ 경로에 중요한 일부 predicate는 충분히 생성하지 못했다.

---

## 5. Triple 예시

### 예시 1. RFP와 공식 요구조건

```json
{
  "subject_id": "L2_ARTIFACT_RFP",
  "predicate": "CONTAINS",
  "object_id": "L2_INFO_OFFICIAL_REQUIREMENT",
  "evidence_refs": ["EV_ZAIJE_000007", "EV_ZAIJE_000008"],
  "confidence": 1.0,
  "relation_scope": "process_step",
  "evidence_span": "아래 <그림 1>처럼 제안 요청서상 고객의 공식적인 요구조건은 실제 고객의 요구조건을 100% 모두 다루고 있지 않기 때문이다."
}
```

### 예시 2. 제안 역량과 제안전략 개발

```json
{
  "subject_id": "L2_PROCESS_PRE_BID_PREPARATION",
  "predicate": "HAS_TASK",
  "object_id": "L2_TASK_PROPOSAL_STRATEGY_DEVELOPMENT",
  "evidence_refs": ["EV_ZAIJE_000002"],
  "confidence": 1.0,
  "relation_scope": "process_step",
  "evidence_span": "경쟁력 있는 제안 역량이란 차별화된 정보를 수집할 줄 아는 전문가 영업 역량, 고객의 정보를 이기는 전략으로 만들 수 있는 전략 개발 역량, 이를 고객과 소통할 줄 아는 제안서 역량, PT 역량을 의미한다."
}
```

### 예시 3. LLM rejected triple의 주요 원인

Rejected triple은 총 100개였고, 대부분은 중복 SPO였다.

| Reject issue | Count |
|---|---:|
| `duplicate_spo` | 97 |
| `subject_not_in_candidate_nodes` | 1 |
| `object_not_in_candidate_nodes` | 1 |
| `frame_task_id_not_canonical` | 1 |

이는 LLM이 서로 다른 evidence에서 같은 관계를 반복 제안했음을 의미한다. 중복 자체는 심각한 오류라기보다 evidence aggregation 전략으로 개선할 수 있는 부분이다.

---

## 6. 품질 평가 결과

| 지표 | 값 | 상태 |
|---|---:|---|
| `node_grounded_rate_domain_only` | 1.0000 | PASS |
| `edge_grounded_rate` | 1.0000 | PASS |
| `predicate_valid_rate` | 1.0000 | PASS |
| `task_orphan_rate` | 0.0000 | PASS |
| `cq_pass_rate` | 0.0000 | REVIEW |
| `case_leakage_rate` | 0.0000 | PASS |

중요한 해석은 다음이다.

1. Schema와 evidence grounding 관점에서는 OpenAI LLM 결과가 자동 검증을 통과했다.
2. 그러나 CQ 7개는 모두 완전 통과하지 못했다.
3. CQ 실패는 그래프가 완전히 틀렸다는 뜻이 아니라, 사전에 정의한 exact path 조건을 충족하는 predicate 조합이 부족했다는 뜻이다.
4. 특히 `USED_AS_INPUT_FOR`, `MITIGATES`, `MAY_RESULT_IN`, `REFINES_INTO` 같은 연결 관계가 부족했다.

---

## 7. Competency Question 결과

| CQ | 질문 | 결과 | 체크 |
|---|---|---|---:|
| CQ1 | 제안전략을 세우기 전에 어떤 정보와 산출물이 필요한가? | FAIL | 2/3 |
| CQ2 | Capture Plan은 어떤 업무에서 생성되고 어디에 사용되는가? | FAIL | 1/2 |
| CQ3 | Bid/No-Bid 의사결정은 어느 단계에서 발생하며 어떤 입력을 쓰는가? | FAIL | 1/2 |
| CQ4 | 평가자 유형에 따라 커뮤니케이션은 어떻게 달라지는가? | FAIL | 0/3 |
| CQ5 | 리스크 관리는 어떻게 차별화 포인트로 이어지는가? | FAIL | 0/2 |
| CQ6 | 제안서 작성 단계에서 어떤 리뷰 또는 마일스톤이 필요한가? | FAIL | 1/3 |
| CQ7 | 고객의 공식 요구조건과 비공식 요구조건은 어떻게 구분되는가? | FAIL | 1/2 |

이번 결과는 LLM 단독 추출이 evidence-grounded triple은 만들 수 있지만, downstream CQ를 만족하는 path 구조를 안정적으로 보장하지는 않는다는 점을 보여준다.

---

## 8. 핵심 산출물

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
  13_review_queue.xlsx
  14_neo4j_import/nodes.csv
  14_neo4j_import/edges.csv
  14_neo4j_import/import.cypher
```

---

## 9. 기존 deterministic MVP와 비교

| 구분 | deterministic MVP | OpenAI API LLM 실행 |
|---|---:|---:|
| 실제 LLM 사용 | 아니오 | 예 |
| Task Frame 처리 | 규칙 기반 seed | OpenAI API linking |
| Triple 추출 | 규칙 기반 seed | OpenAI API extraction |
| Raw triples | 196 | 209 |
| Validated triples | 188 | 103 |
| Nodes | 1,869 | 1,869 |
| Edges | 2,368 | 2,283 |
| CQ 통과 | 7/7 | 0/7 |
| 해석 | 설계서 기반 proof-of-concept | 실제 LLM 추출의 엄격 검증 결과 |

이 비교에서 중요한 점은 deterministic MVP가 CQ를 잘 통과한 이유는 설계서의 핵심 path를 규칙 기반으로 명시했기 때문이라는 것이다. OpenAI LLM 실행은 더 실제적인 추출 실험이지만, CQ 경로를 안정적으로 만들기 위해서는 추가 prompt 또는 verifier 단계가 필요하다.

---

## 10. 다음 개선 방향

1. CQ-aware reprompt 추가
   - 현재 실패한 CQ별 missing edge를 추출한다.
   - 해당 edge 후보를 evidence와 함께 OpenAI에 재질의한다.

2. Evidence aggregation 개선
   - duplicate SPO를 단순 reject하지 않고, 같은 SPO의 evidence_refs를 병합한다.

3. Predicate balancing 개선
   - `USED_AS_INPUT_FOR`, `MITIGATES`, `MAY_RESULT_IN`, `REFINES_INTO` 같은 관계를 별도 prompt로 보강한다.

4. 사람 검수 연결
   - `13_review_queue.xlsx`에서 낮은 confidence 또는 CQ-critical edge를 우선 검토한다.

---

## 11. 교수님께 보고할 정확한 표현

```text
자이제 데이터에 대해 OpenAI API 기반 실제 LLM 추출 실험을 완료했다.
gpt-4o-mini로 section summary 51개와 paragraph chunk 110개를 처리했고,
LLM accepted triple 188개, schema-validated triple 103개를 얻었다.
모든 node/edge는 evidence와 schema 기준으로 검증되었으나,
사전에 정의한 CQ 7개는 exact path 기준으로는 아직 통과하지 못했다.
따라서 현재 결과는 gold KG가 아니라 OpenAI LLM 기반 bootstrap KG이며,
다음 단계는 CQ-aware reprompt와 사람 검수이다.
```

