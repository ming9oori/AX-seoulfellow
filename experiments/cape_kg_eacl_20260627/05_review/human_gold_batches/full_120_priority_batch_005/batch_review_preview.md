# full_120_priority_batch_005 Review Preview

이 문서는 사람 검수자가 batch를 열기 전에 candidate edge 밀도와 evidence span 품질을 빠르게 확인하기 위한 보조 자료입니다.
자동 후보를 gold로 확정하지 않으며, 최종 판단은 annotator/adjudicator가 원문 chunk text만 근거로 수행해야 합니다.

## Batch Summary

- chunks: 20
- candidate edges: 137
- avg candidate edges per chunk: 6.8500
- exact component ratio: 0.2579
- chunks needing span attention: 13
- dense candidate chunks: 0
- zero candidate chunks: 7
- high-impact chunks: 8

## Chunk Preview

| rank | chunk_id | pages | candidates | exact ratio | top predicates | review focus |
| --- | --- | --- | ---: | ---: | --- | --- |
| 81 | `JZ-CHUNK-0070` | 155-157 | 5 | 0.2667 | USES_INPUT:2; PRODUCES:2; HAS_PRINCIPLE:1 | evidence span repair; high-impact review |
| 82 | `JZ-CHUNK-0068` | 150-152 | 12 | 0.3611 | USES_INPUT:5; PRODUCES:5; PERFORMED_BY:1; HAS_PRINCIPLE:1 | evidence span repair |
| 83 | `JZ-CHUNK-0057` | 127-127 | 23 | 0.2464 | PERFORMED_BY:10; HAS_PRINCIPLE:9; USES_INPUT:2; PRODUCES:2 | evidence span repair |
| 84 | `JZ-CHUNK-0036` | 84-86 | 11 | 0.1515 | PERFORMED_BY:4; HAS_PRINCIPLE:3; USES_INPUT:2; PRODUCES:2 | evidence span repair |
| 85 | `JZ-CHUNK-0001` | 19-19 | 9 | 0.1481 | USES_INPUT:2; PRODUCES:2; HAS_STEP:2; PERFORMED_BY:1 | evidence span repair |
| 86 | `JZ-CHUNK-0060` | 133-136 | 0 | 0.0000 |  | missing-edge scan; high-impact review |
| 87 | `JZ-CHUNK-0147` | 310-311 | 0 | 0.0000 |  | missing-edge scan; high-impact review |
| 88 | `JZ-CHUNK-0011` | 37-37 | 6 | 0.1667 | PERFORMED_BY:3; HAS_PRINCIPLE:3 | evidence span repair |
| 89 | `JZ-CHUNK-0129` | 293-293 | 0 | 0.0000 |  | missing-edge scan; high-impact review |
| 90 | `JZ-CHUNK-0146` | 310-310 | 0 | 0.0000 |  | missing-edge scan; high-impact review |
| 91 | `JZ-CHUNK-0139` | 303-304 | 0 | 0.0000 |  | missing-edge scan; high-impact review |
| 92 | `JZ-CHUNK-0055` | 123-125 | 18 | 0.2778 | USES_INPUT:7; PRODUCES:7; PERFORMED_BY:2; HAS_PRINCIPLE:2 | evidence span repair |
| 93 | `JZ-CHUNK-0067` | 149-150 | 6 | 0.1667 | PERFORMED_BY:3; HAS_PRINCIPLE:3 | evidence span repair |
| 94 | `JZ-CHUNK-0133` | 375-377 | 13 | 0.2564 | PERFORMED_BY:5; USES_INPUT:4; PRODUCES:4 | evidence span repair |
| 95 | `JZ-CHUNK-0052` | 121-121 | 4 | 0.1667 | PERFORMED_BY:2; HAS_PRINCIPLE:2 | evidence span repair |
| 96 | `JZ-CHUNK-0131` | 313-313 | 4 | 0.1667 | USES_INPUT:2; PRODUCES:2 | evidence span repair |
| 97 | `JZ-CHUNK-0066` | 144-145 | 14 | 0.4286 | USES_INPUT:3; PRODUCES:3; PERFORMED_BY:2; HAS_RISK:2 | evidence span repair |
| 98 | `JZ-CHUNK-0062` | 137-139 | 12 | 0.2778 | PERFORMED_BY:4; HAS_PRINCIPLE:3; HAS_RISK:2; HAS_DECISION_GATEWAY:2 | evidence span repair |
| 99 | `JZ-CHUNK-0204` | 435-437 | 0 | 0.0000 |  | missing-edge scan; high-impact review |
| 100 | `JZ-CHUNK-0200` | 424-426 | 0 | 0.0000 |  | missing-edge scan; high-impact review |

## 해석

- `dense candidate pruning`: 후보가 많아 accept/reject 판단 시간이 많이 걸릴 수 있습니다.
- `evidence span repair`: 자동 component span이 exact하지 않으므로 accepted edge에는 사람이 evidence를 더 엄격히 확인해야 합니다.
- `missing-edge scan`: 자동 후보가 거의 없으므로 원문에서 직접 지지되는 빠진 edge가 있는지 확인해야 합니다.
- `high-impact review`: evidence, schema, risk, gateway, central task-flow에 영향을 줄 수 있어 우선 검토합니다.
