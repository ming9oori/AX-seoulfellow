# AX ZAIJE Layer2 KG Quality Report

Generated: 2026-07-07T06:10:40+00:00
Experiment dir: `experiments/ax_zaije_layer2_kg_openai_20260707_smoke/layer2_kg`
Run ID: `RUN_2026_07_06_001`

## 1. 실행 성격

- 설계서: `AX_ZAIJE_Layer2_KG_Methodology.md`
- 입력: `자이제_1.xlsx` / `clean_sentences`
- 범위: Layer 2 Source Evidence Graph + Domain Ontology Graph
- 제외: Layer 1 NCS/PCF 매핑, Layer 2→Layer 1 점수화
- LLM 상태: OpenAI Chat Completions API로 `gpt-4o-mini` 실제 추론을 실행했다.
- LLM 원본 응답: `19_openai_task_frame_links.raw.jsonl`, `20_openai_triples.raw.jsonl`.

## 2. Counts

| item | value |
| --- | ---: |
| valid sentence rows | 1366 |
| source chunks | 166 |
| evidence spans | 1366 |
| raw triples | 31 |
| validated triples | 28 |
| graph nodes | 1869 |
| graph edges | 2208 |

## 3. Quality Metrics

| metric | value | MVP target | status |
| --- | ---: | ---: | --- |
| `node_grounded_rate_domain_only` | 1.0000 | 0.95 | PASS |
| `edge_grounded_rate` | 1.0000 | 0.98 | PASS |
| `predicate_valid_rate` | 1.0000 | 1.00 | PASS |
| `task_orphan_rate` | 0.0000 | 0.05 | PASS |
| `cq_pass_rate` | 0.0000 | 0.80 | REVIEW |
| `case_leakage_rate` | 0.0000 | 0.00 | PASS |
| `duplicate_alias_rate` | 0.0796 | trend | INFO |
| `review_resolution_rate` | 0.0000 | 1.00 before release | OPEN |

## 4. Node Type Distribution

| node_type | count |
| --- | ---: |
| `EvidenceSpan` | 1366 |
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

## 5. Predicate Distribution

| predicate | count |
| --- | ---: |
| `EVIDENCED_BY` | 1759 |
| `ALIAS_OF` | 201 |
| `HAS_CHUNK` | 166 |
| `HAS_SECTION` | 51 |
| `HAS_TASK` | 19 |
| `HAS_PROCESS` | 6 |
| `HAS_CHAPTER` | 3 |
| `CONTAINS` | 2 |
| `PART_OF` | 1 |

## 6. Competency Question Evaluation

| CQ | question | passed | checks |
| --- | --- | --- | ---: |
| CQ1 | 제안전략을 세우기 전에 어떤 정보와 산출물이 필요한가? | FAIL | 0/3 |
| CQ2 | Capture Plan은 어떤 업무에서 생성되고 어디에 사용되는가? | FAIL | 0/2 |
| CQ3 | Bid/No-Bid 의사결정은 어느 단계에서 발생하며 어떤 입력을 쓰는가? | FAIL | 0/2 |
| CQ4 | 평가자 유형에 따라 커뮤니케이션은 어떻게 달라지는가? | FAIL | 0/3 |
| CQ5 | 리스크 관리는 어떻게 차별화 포인트로 이어지는가? | FAIL | 0/2 |
| CQ6 | 제안서 작성 단계에서 어떤 리뷰 또는 마일스톤이 필요한가? | FAIL | 0/3 |
| CQ7 | 고객의 공식 요구조건과 비공식 요구조건은 어떻게 구분되는가? | FAIL | 1/2 |

## 7. Claim Boundary

- 이 결과는 설계서 기반 MVP 구축 결과이며 사람 검수를 완료한 gold KG가 아니다.
- `verified`는 schema/domain/range/evidence_refs 기준의 자동 검증 통과를 의미한다.
- Task/edge의 의미적 정확도는 `13_review_queue.xlsx`를 통한 사람 검수 이후에 주장해야 한다.
