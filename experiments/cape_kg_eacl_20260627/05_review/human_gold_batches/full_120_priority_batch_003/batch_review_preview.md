# full_120_priority_batch_003 Review Preview

이 문서는 사람 검수자가 batch를 열기 전에 candidate edge 밀도와 evidence span 품질을 빠르게 확인하기 위한 보조 자료입니다.
자동 후보를 gold로 확정하지 않으며, 최종 판단은 annotator/adjudicator가 원문 chunk text만 근거로 수행해야 합니다.

## Batch Summary

- chunks: 20
- candidate edges: 152
- avg candidate edges per chunk: 7.6000
- exact component ratio: 0.2632
- chunks needing span attention: 8
- dense candidate chunks: 0
- zero candidate chunks: 12
- high-impact chunks: 15

## Chunk Preview

| rank | chunk_id | pages | candidates | exact ratio | top predicates | review focus |
| --- | --- | --- | ---: | ---: | --- | --- |
| 41 | `JZ-CHUNK-0145` | 309-310 | 0 | 0.0000 |  | missing-edge scan; high-impact review |
| 42 | `JZ-CHUNK-0190` | 441-441 | 0 | 0.0000 |  | missing-edge scan; high-impact review |
| 43 | `JZ-CHUNK-0195` | 413-415 | 0 | 0.0000 |  | missing-edge scan; high-impact review |
| 44 | `JZ-CHUNK-0137` | 299-302 | 5 | 0.1333 | USES_INPUT:2; PRODUCES:2; HAS_PRINCIPLE:1 | evidence span repair; high-impact review |
| 45 | `JZ-CHUNK-0058` | 128-130 | 25 | 0.1467 | HAS_PRINCIPLE:9; PERFORMED_BY:7; USES_INPUT:3; PRODUCES:3 | evidence span repair |
| 46 | `JZ-CHUNK-0143` | 309-309 | 0 | 0.0000 |  | missing-edge scan; high-impact review |
| 47 | `JZ-CHUNK-0198` | 420-420 | 0 | 0.0000 |  | missing-edge scan; high-impact review |
| 48 | `JZ-CHUNK-0187` | 411-411 | 0 | 0.0000 |  | missing-edge scan; high-impact review |
| 49 | `JZ-CHUNK-0189` | 427-427 | 0 | 0.0000 |  | missing-edge scan; high-impact review |
| 50 | `JZ-CHUNK-0009` | 36-36 | 23 | 0.2319 | PERFORMED_BY:10; HAS_PRINCIPLE:6; USES_INPUT:2; PRODUCES:2 | evidence span repair |
| 51 | `JZ-CHUNK-0148` | 315-317 | 35 | 0.2762 | USES_INPUT:13; PRODUCES:13; PERFORMED_BY:9 | evidence span repair |
| 52 | `JZ-CHUNK-0193` | 406-407 | 0 | 0.0000 |  | missing-edge scan; high-impact review |
| 53 | `JZ-CHUNK-0012` | 38-38 | 0 | 0.0000 |  | missing-edge scan; high-impact review |
| 54 | `JZ-CHUNK-0144` | 309-309 | 0 | 0.0000 |  | missing-edge scan; high-impact review |
| 55 | `JZ-CHUNK-0138` | 302-302 | 0 | 0.0000 |  | missing-edge scan; high-impact review |
| 56 | `JZ-CHUNK-0007` | 30-31 | 22 | 0.3030 | USES_INPUT:11; PRODUCES:11 | evidence span repair |
| 57 | `JZ-CHUNK-0053` | 147-147 | 0 | 0.0000 |  | missing-edge scan; high-impact review |
| 58 | `JZ-CHUNK-0034` | 79-82 | 8 | 0.2083 | USES_INPUT:3; PRODUCES:3; PERFORMED_BY:1; HAS_PRINCIPLE:1 | evidence span repair; high-impact review |
| 59 | `JZ-CHUNK-0056` | 125-126 | 32 | 0.3854 | USES_INPUT:10; PRODUCES:10; PERFORMED_BY:9; HAS_PRINCIPLE:3 | evidence span repair |
| 60 | `JZ-CHUNK-0038` | 89-90 | 2 | 0.0000 | PERFORMED_BY:2 | evidence span repair; high-impact review |

## 해석

- `dense candidate pruning`: 후보가 많아 accept/reject 판단 시간이 많이 걸릴 수 있습니다.
- `evidence span repair`: 자동 component span이 exact하지 않으므로 accepted edge에는 사람이 evidence를 더 엄격히 확인해야 합니다.
- `missing-edge scan`: 자동 후보가 거의 없으므로 원문에서 직접 지지되는 빠진 edge가 있는지 확인해야 합니다.
- `high-impact review`: evidence, schema, risk, gateway, central task-flow에 영향을 줄 수 있어 우선 검토합니다.
