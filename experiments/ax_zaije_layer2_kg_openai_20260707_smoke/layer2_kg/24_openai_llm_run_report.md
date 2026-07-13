# AX ZAIJE Layer2 KG OpenAI LLM Run Report

Generated: 2026-07-07T06:10:40+00:00
Run ID: `RUN_2026_07_07_OPENAI_001`
Model: `gpt-4o-mini`
Output dir: `experiments/ax_zaije_layer2_kg_openai_20260707_smoke/layer2_kg`

## 실행 요약

| item | value |
| --- | ---: |
| Task Frame LLM calls | 1 |
| Triple LLM calls | 3 |
| LLM accepted triples | 10 |
| LLM rejected triples | 0 |
| validated triples total | 28 |
| graph nodes | 1869 |
| graph edges | 2208 |
| CQ passed | 0/7 |
| estimated token cost USD | 0.004353 |

## 비용 산정

| field | value |
| --- | ---: |
| prompt tokens | 18882 |
| completion tokens | 2535 |
| total tokens | 21417 |
| input USD / 1M | 0.15 |
| output USD / 1M | 0.6 |

- Estimated from published per-1M token standard prices; actual bill can differ by service tier, caching, or account settings.

## LLM Predicate Distribution

| predicate | LLM triples |
| --- | ---: |
| `HAS_TASK` | 7 |
| `CONTAINS` | 2 |
| `PART_OF` | 1 |

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
- `HAS_PROCESS`, `HAS_TASK`는 LLM 추론이 아니라 schema scaffold이며, 나머지 domain relation은 LLM 결과를 자동 검증한 것이다.
- 사람 검수 전이므로 의미적 정답 gold KG로 주장하면 안 된다.
