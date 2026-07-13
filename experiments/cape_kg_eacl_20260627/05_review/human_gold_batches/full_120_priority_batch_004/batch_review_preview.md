# full_120_priority_batch_004 Review Preview

이 문서는 사람 검수자가 batch를 열기 전에 candidate edge 밀도와 evidence span 품질을 빠르게 확인하기 위한 보조 자료입니다.
자동 후보를 gold로 확정하지 않으며, 최종 판단은 annotator/adjudicator가 원문 chunk text만 근거로 수행해야 합니다.

## Batch Summary

- chunks: 20
- candidate edges: 91
- avg candidate edges per chunk: 4.5500
- exact component ratio: 0.2161
- chunks needing span attention: 8
- dense candidate chunks: 0
- zero candidate chunks: 11
- high-impact chunks: 18

## Chunk Preview

| rank | chunk_id | pages | candidates | exact ratio | top predicates | review focus |
| --- | --- | --- | ---: | ---: | --- | --- |
| 61 | `JZ-CHUNK-0091` | 245-247 | 11 | 0.4848 | USES_INPUT:5; PRODUCES:5; PERFORMED_BY:1 | evidence span repair; high-impact review |
| 62 | `JZ-CHUNK-0191` | 399-453 | 2 | 0.0000 | USES_INPUT:1; PRODUCES:1 | evidence span repair; high-impact review |
| 63 | `JZ-CHUNK-0028` | 64-65 | 14 | 0.1190 | USES_INPUT:6; PRODUCES:6; PERFORMED_BY:1; HAS_RISK:1 | evidence span repair; high-impact review |
| 64 | `JZ-CHUNK-0061` | 136-136 | 0 | 0.0000 |  | missing-edge scan; high-impact review |
| 65 | `JZ-CHUNK-0031` | 70-70 | 0 | 0.0000 |  | missing-edge scan; high-impact review |
| 66 | `JZ-CHUNK-0141` | 308-308 | 0 | 0.0000 |  | missing-edge scan; high-impact review |
| 67 | `JZ-CHUNK-0006` | 27-29 | 17 | 0.0588 | HAS_STEP:5; USES_INPUT:3; PRODUCES:3; PERFORMED_BY:3 | evidence span repair |
| 68 | `JZ-CHUNK-0035` | 82-84 | 17 | 0.1569 | PERFORMED_BY:8; HAS_PRINCIPLE:4; USES_INPUT:2; PRODUCES:2 | evidence span repair; high-impact review |
| 69 | `JZ-CHUNK-0142` | 308-308 | 0 | 0.0000 |  | missing-edge scan; high-impact review |
| 70 | `JZ-CHUNK-0186` | 401-403 | 2 | 0.0000 | USES_INPUT:1; PRODUCES:1 | evidence span repair; high-impact review |
| 71 | `JZ-CHUNK-0003` | 23-23 | 7 | 0.5714 | USES_INPUT:3; PRODUCES:3; PERFORMED_BY:1 | high-impact review |
| 72 | `JZ-CHUNK-0105` | 230-233 | 7 | 0.1429 | USES_INPUT:2; PRODUCES:2; PERFORMED_BY:1; HAS_PRINCIPLE:1 | evidence span repair; high-impact review |
| 73 | `JZ-CHUNK-0203` | 434-434 | 0 | 0.0000 |  | missing-edge scan; high-impact review |
| 74 | `JZ-CHUNK-0004` | 24-24 | 0 | 0.0000 |  | missing-edge scan; high-impact review |
| 75 | `JZ-CHUNK-0025` | 91-91 | 0 | 0.0000 |  | missing-edge scan; high-impact review |
| 76 | `JZ-CHUNK-0023` | 59-59 | 0 | 0.0000 |  | missing-edge scan; high-impact review |
| 77 | `JZ-CHUNK-0065` | 143-143 | 0 | 0.0000 |  | missing-edge scan; high-impact review |
| 78 | `JZ-CHUNK-0015` | 41-41 | 0 | 0.0000 |  | missing-edge scan; high-impact review |
| 79 | `JZ-CHUNK-0040` | 95-95 | 0 | 0.0000 |  | missing-edge scan; high-impact review |
| 80 | `JZ-CHUNK-0005` | 25-27 | 14 | 0.2857 | USES_INPUT:4; PRODUCES:4; HAS_STEP:2; PRECEDES:2 | evidence span repair |

## 해석

- `dense candidate pruning`: 후보가 많아 accept/reject 판단 시간이 많이 걸릴 수 있습니다.
- `evidence span repair`: 자동 component span이 exact하지 않으므로 accepted edge에는 사람이 evidence를 더 엄격히 확인해야 합니다.
- `missing-edge scan`: 자동 후보가 거의 없으므로 원문에서 직접 지지되는 빠진 edge가 있는지 확인해야 합니다.
- `high-impact review`: evidence, schema, risk, gateway, central task-flow에 영향을 줄 수 있어 우선 검토합니다.
