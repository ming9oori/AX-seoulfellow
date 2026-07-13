# full_120_priority_batch_001 Review Preview

이 문서는 사람 검수자가 batch를 열기 전에 candidate edge 밀도와 evidence span 품질을 빠르게 확인하기 위한 보조 자료입니다.
자동 후보를 gold로 확정하지 않으며, 최종 판단은 annotator/adjudicator가 원문 chunk text만 근거로 수행해야 합니다.

## Batch Summary

- chunks: 20
- candidate edges: 811
- avg candidate edges per chunk: 40.5500
- exact component ratio: 0.3296
- chunks needing span attention: 16
- dense candidate chunks: 16
- zero candidate chunks: 2
- high-impact chunks: 7

## Chunk Preview

| rank | chunk_id | pages | candidates | exact ratio | top predicates | review focus |
| --- | --- | --- | ---: | ---: | --- | --- |
| 1 | `JZ-CHUNK-0094` | 205-208 | 50 | 0.2133 | PERFORMED_BY:17; USES_INPUT:12; PRODUCES:12; HAS_PRINCIPLE:6 | dense candidate pruning; evidence span repair; high-impact review |
| 2 | `JZ-CHUNK-0020` | 51-52 | 50 | 0.2067 | USES_INPUT:17; PRODUCES:17; PERFORMED_BY:7; HAS_PRINCIPLE:4 | dense candidate pruning; evidence span repair; high-impact review |
| 3 | `JZ-CHUNK-0032` | 73-76 | 50 | 0.4800 | USES_INPUT:22; PRODUCES:22; PERFORMED_BY:6 | dense candidate pruning; evidence span repair |
| 4 | `JZ-CHUNK-0016` | 43-44 | 50 | 0.4667 | USES_INPUT:17; PRODUCES:17; HAS_DECISION_GATEWAY:7; PERFORMED_BY:6 | dense candidate pruning; evidence span repair |
| 5 | `JZ-CHUNK-0019` | 49-51 | 50 | 0.3200 | USES_INPUT:27; PRODUCES:20; PERFORMED_BY:1; HAS_PRINCIPLE:1 | dense candidate pruning; evidence span repair |
| 6 | `JZ-CHUNK-0002` | 21-23 | 50 | 0.2467 | USES_INPUT:12; PRODUCES:12; HAS_PRINCIPLE:11; PERFORMED_BY:10 | dense candidate pruning; evidence span repair |
| 7 | `JZ-CHUNK-0099` | 216-217 | 50 | 0.3200 | USES_INPUT:16; PRODUCES:16; PERFORMED_BY:11; HAS_PRINCIPLE:5 | dense candidate pruning; evidence span repair |
| 8 | `JZ-CHUNK-0017` | 45-46 | 50 | 0.5067 | USES_INPUT:19; PRODUCES:14; HAS_DECISION_GATEWAY:9; PERFORMED_BY:4 | dense candidate pruning |
| 9 | `JZ-CHUNK-0108` | 239-241 | 48 | 0.4514 | PRODUCES:20; USES_INPUT:13; PERFORMED_BY:8; HAS_PRINCIPLE:6 | dense candidate pruning; evidence span repair; high-impact review |
| 10 | `JZ-CHUNK-0018` | 47-48 | 50 | 0.2667 | USES_INPUT:17; PRODUCES:14; PERFORMED_BY:8; HAS_PRINCIPLE:6 | dense candidate pruning; evidence span repair |
| 11 | `JZ-CHUNK-0069` | 152-154 | 16 | 0.4167 | PERFORMED_BY:4; USES_INPUT:4; PRODUCES:4; HAS_PRINCIPLE:2 | evidence span repair; high-impact review |
| 12 | `JZ-CHUNK-0033` | 76-79 | 50 | 0.2333 | HAS_STEP:11; PERFORMED_BY:10; PRECEDES:10; USES_INPUT:8 | dense candidate pruning; evidence span repair |
| 13 | `JZ-CHUNK-0098` | 214-216 | 50 | 0.3200 | USES_INPUT:22; PRODUCES:15; PERFORMED_BY:12; HAS_PRINCIPLE:1 | dense candidate pruning; evidence span repair |
| 14 | `JZ-CHUNK-0101` | 219-223 | 50 | 0.4600 | PRODUCES:22; USES_INPUT:20; PERFORMED_BY:4; HAS_DECISION_GATEWAY:3 | dense candidate pruning; evidence span repair |
| 15 | `JZ-CHUNK-0103` | 227-228 | 50 | 0.1733 | USES_INPUT:23; PRODUCES:23; PERFORMED_BY:2; HAS_PRINCIPLE:1 | dense candidate pruning; evidence span repair |
| 16 | `JZ-CHUNK-0104` | 228-230 | 50 | 0.1867 | USES_INPUT:29; PRODUCES:17; PERFORMED_BY:3; HAS_PRINCIPLE:1 | dense candidate pruning; evidence span repair |
| 17 | `JZ-CHUNK-0097` | 212-214 | 43 | 0.3953 | PERFORMED_BY:14; USES_INPUT:10; PRODUCES:10; HAS_PRINCIPLE:5 | dense candidate pruning; evidence span repair |
| 18 | `JZ-CHUNK-0196` | 415-417 | 0 | 0.0000 |  | missing-edge scan; high-impact review |
| 19 | `JZ-CHUNK-0188` | 421-421 | 0 | 0.0000 |  | missing-edge scan; high-impact review |
| 20 | `JZ-CHUNK-0092` | 199-271 | 4 | 0.5000 | USES_INPUT:2; PRODUCES:2 | high-impact review |

## 해석

- `dense candidate pruning`: 후보가 많아 accept/reject 판단 시간이 많이 걸릴 수 있습니다.
- `evidence span repair`: 자동 component span이 exact하지 않으므로 accepted edge에는 사람이 evidence를 더 엄격히 확인해야 합니다.
- `missing-edge scan`: 자동 후보가 거의 없으므로 원문에서 직접 지지되는 빠진 edge가 있는지 확인해야 합니다.
- `high-impact review`: evidence, schema, risk, gateway, central task-flow에 영향을 줄 수 있어 우선 검토합니다.
