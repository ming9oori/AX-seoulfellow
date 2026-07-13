# AX ZAIJE Layer2 KG Methodology v2 Replay Run Report

Generated: 2026-07-08T03:12:14+00:00
Run ID: `RUN_2026_07_08_METHOD_V2_REPLAY_001`

## 실행 방식

| 항목 | 내용 |
| --- | --- |
| 입력 데이터 | `자이제_1.xlsx` |
| 방법론 문서 | `AX_ZAIJE_Layer2_KG_Methodology.md` |
| OpenAI 원시 응답 | `experiments/ax_zaije_layer2_kg_openai_20260707/layer2_kg` |
| v2 산출물 | `experiments/ax_zaije_layer2_kg_openai_methodology_v2_20260708/layer2_kg` |
| LLM 재호출 | 없음 |
| 재실행 방식 | 기존 OpenAI raw response를 재사용한 replay build |

## 핵심 보강

| 보강 항목 | 산출물 |
| --- | --- |
| Node type 설계 근거 | `25_node_type_traceability.csv/jsonl` |
| Canonical process/task/entity 도출 근거 | `26_canonical_inventory_traceability.csv/jsonl` |
| Predicate 도출 근거와 domain/range | `27_predicate_schema_traceability.csv/jsonl` |
| 논문용 방법론 설명 | `28_methodology_schema_derivation.md` |

## Task Frame Evidence ID Reconciliation

| 항목 | 값 |
| --- | ---: |
| task frame links | 111 |
| original valid evidence links | 0 |
| reconciled to section chunk evidence | 111 |
| unresolved links | 0 |

원시 OpenAI 응답은 `19_openai_task_frame_links.raw.jsonl`에 그대로 보존했고, evidence id reconciliation 결과는 `19b_openai_task_frame_links.reconciled.jsonl`에 별도로 저장했다.

## 재빌드 결과

| 항목 | 값 |
| --- | ---: |
| valid sentence rows | 1366 |
| source chunks | 166 |
| evidence spans | 1366 |
| task frame LLM rows | 51 |
| triple LLM rows | 110 |
| LLM accepted triples | 188 |
| LLM rejected triples | 100 |
| raw triples | 209 |
| validated triples | 103 |
| graph nodes | 1869 |
| graph edges | 2280 |
| CQ passed | 0/7 |

## Schema Traceability Counts

| 항목 | 값 |
| --- | ---: |
| node type traceability rows | 22 |
| canonical inventory traceability rows | 80 |
| predicate traceability rows | 28 |

## Token/Cost Reference

| 항목 | 값 |
| --- | ---: |
| prompt tokens | 782179 |
| completion tokens | 74562 |
| total tokens | 856741 |
| estimated USD | 0.162064 |

이번 v2 run은 API 비용을 새로 발생시키지 않고, 저장된 OpenAI 응답을 재사용하여 schema derivation traceability를 포함한 최종 KG 산출물을 다시 생성했다.
