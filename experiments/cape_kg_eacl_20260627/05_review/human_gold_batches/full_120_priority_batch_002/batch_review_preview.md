# full_120_priority_batch_002 Review Preview

이 문서는 사람 검수자가 batch를 열기 전에 candidate edge 밀도와 evidence span 품질을 빠르게 확인하기 위한 보조 자료입니다.
자동 후보를 gold로 확정하지 않으며, 최종 판단은 annotator/adjudicator가 원문 chunk text만 근거로 수행해야 합니다.

## Batch Summary

- chunks: 20
- candidate edges: 180
- avg candidate edges per chunk: 9.0000
- exact component ratio: 0.2685
- chunks needing span attention: 10
- dense candidate chunks: 1
- zero candidate chunks: 8
- high-impact chunks: 16

## Chunk Preview

| rank | chunk_id | pages | candidates | exact ratio | top predicates | review focus |
| --- | --- | --- | ---: | ---: | --- | --- |
| 21 | `JZ-CHUNK-0102` | 223-223 | 6 | 0.3889 | PERFORMED_BY:3; USES_INPUT:1; PRODUCES:1; HAS_PRINCIPLE:1 | evidence span repair; high-impact review |
| 22 | `JZ-CHUNK-0090` | 225-225 | 30 | 0.2444 | USES_INPUT:10; PRODUCES:10; PERFORMED_BY:4; HAS_PRINCIPLE:3 | evidence span repair |
| 23 | `JZ-CHUNK-0042` | 98-100 | 13 | 0.3077 | PERFORMED_BY:5; USES_INPUT:4; PRODUCES:4 | evidence span repair; high-impact review |
| 24 | `JZ-CHUNK-0106` | 233-236 | 41 | 0.1870 | USES_INPUT:11; PRODUCES:11; HAS_PRINCIPLE:8; HAS_RISK:6 | dense candidate pruning; evidence span repair |
| 25 | `JZ-CHUNK-0013` | 38-39 | 2 | 0.6667 | USES_INPUT:1; PRODUCES:1 | high-impact review |
| 26 | `JZ-CHUNK-0026` | 57-103 | 2 | 0.3333 | USES_INPUT:1; PRODUCES:1 | evidence span repair; high-impact review |
| 27 | `JZ-CHUNK-0093` | 203-205 | 27 | 0.2716 | PERFORMED_BY:10; USES_INPUT:5; PRODUCES:5; HAS_GUARD_CONDITION:2 | evidence span repair |
| 28 | `JZ-CHUNK-0054` | 119-165 | 0 | 0.0000 |  | missing-edge scan; high-impact review |
| 29 | `JZ-CHUNK-0130` | 305-305 | 0 | 0.0000 |  | missing-edge scan; high-impact review |
| 30 | `JZ-CHUNK-0008` | 33-35 | 9 | 0.2593 | USES_INPUT:3; PRODUCES:3; HAS_PRINCIPLE:2; PERFORMED_BY:1 | evidence span repair; high-impact review |
| 31 | `JZ-CHUNK-0199` | 423-424 | 0 | 0.0000 |  | missing-edge scan; high-impact review |
| 32 | `JZ-CHUNK-0037` | 86-88 | 11 | 0.1818 | PERFORMED_BY:4; USES_INPUT:2; PRODUCES:2; HAS_RISK:2 | evidence span repair; high-impact review |
| 33 | `JZ-CHUNK-0205` | 438-440 | 0 | 0.0000 |  | missing-edge scan; high-impact review |
| 34 | `JZ-CHUNK-0107` | 237-238 | 18 | 0.2222 | USES_INPUT:6; PRODUCES:6; PERFORMED_BY:4; HAS_PRINCIPLE:2 | evidence span repair; high-impact review |
| 35 | `JZ-CHUNK-0132` | 355-355 | 0 | 0.0000 |  | missing-edge scan; high-impact review |
| 36 | `JZ-CHUNK-0014` | 39-39 | 4 | 0.6667 | USES_INPUT:2; PRODUCES:2 | high-impact review |
| 37 | `JZ-CHUNK-0024` | 71-71 | 17 | 0.3922 | USES_INPUT:6; PRODUCES:6; PERFORMED_BY:5 | evidence span repair |
| 38 | `JZ-CHUNK-0010` | 37-37 | 0 | 0.0000 |  | missing-edge scan; high-impact review |
| 39 | `JZ-CHUNK-0134` | 291-389 | 0 | 0.0000 |  | missing-edge scan; high-impact review |
| 40 | `JZ-CHUNK-0140` | 307-307 | 0 | 0.0000 |  | missing-edge scan; high-impact review |

## 해석

- `dense candidate pruning`: 후보가 많아 accept/reject 판단 시간이 많이 걸릴 수 있습니다.
- `evidence span repair`: 자동 component span이 exact하지 않으므로 accepted edge에는 사람이 evidence를 더 엄격히 확인해야 합니다.
- `missing-edge scan`: 자동 후보가 거의 없으므로 원문에서 직접 지지되는 빠진 edge가 있는지 확인해야 합니다.
- `high-impact review`: evidence, schema, risk, gateway, central task-flow에 영향을 줄 수 있어 우선 검토합니다.
