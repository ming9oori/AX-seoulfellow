# AX ZAIJE Layer2 KG OpenAI LLM Run Report

Generated: 2026-07-07T06:50:14+00:00
Run ID: `RUN_2026_07_07_OPENAI_001`
Model: `gpt-4o-mini`
Output dir: `experiments/ax_zaije_layer2_kg_openai_20260707/layer2_kg`

## 실행 요약

| item | value |
| --- | ---: |
| Task Frame LLM calls | 51 |
| Triple LLM calls | 110 |
| LLM accepted triples | 188 |
| LLM rejected triples | 100 |
| validated triples total | 103 |
| graph nodes | 1869 |
| graph edges | 2283 |
| CQ passed | 0/7 |
| estimated token cost USD | 0.162064 |

## 비용 산정

| field | value |
| --- | ---: |
| prompt tokens | 782179 |
| completion tokens | 74562 |
| total tokens | 856741 |
| input USD / 1M | 0.15 |
| output USD / 1M | 0.6 |

- Estimated from published per-1M token standard prices; actual bill can differ by service tier, caching, or account settings.

## LLM Predicate Distribution

| predicate | LLM triples |
| --- | ---: |
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

## 출력 파일

- `19_openai_task_frame_links.raw.jsonl`: Task Frame linking 원본 LLM 응답
- `20_openai_triples.raw.jsonl`: Triple extraction 원본 LLM 응답
- `21_openai_triples.accepted.jsonl`: schema 후보 ID/evidence 조건을 통과한 LLM triple
- `22_openai_triples.rejected.jsonl`: 자동 변환 단계에서 제외된 LLM triple
- `08_triples.raw.jsonl`: schema scaffold + accepted LLM triples
- `09_triples.validated.jsonl`: KG validator 통과 triple

## 해석 경계

- 이번 실행은 실제 OpenAI API LLM 추론을 사용했다.
- 단, ontology/process/task catalog 자체는 설계서의 canonical seed를 기준으로 유지했다.
- 최소 graph connectivity를 위해 `HAS_PROCESS`, `HAS_TASK` schema scaffold를 포함했고, 그 외 LLM이 제안한 relation 후보는 동일 validator로 자동 검증했다.
- 사람 검수 전이므로 의미적 정답 gold KG로 주장하면 안 된다.
