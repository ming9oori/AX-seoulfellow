# strong_resegmented_342_max18 Strong Review Preview

이 문서는 optional strong 300+ human review package를 시작하기 전에 review unit별 candidate edge 밀도와 evidence span 품질을 확인하기 위한 보조 자료입니다.
자동 후보를 gold로 확정하지 않으며, 최종 판단은 annotator/adjudicator가 split text와 source sentence evidence만 근거로 수행해야 합니다.

## Package Summary

- review units: 342
- source chunks represented: 214
- candidate edges: 2087
- avg candidate edges per unit: 6.1023
- exact component ratio: 0.2733
- units needing span attention: 87
- dense candidate units: 13
- zero candidate units: 249

## Top Review Attention Units

| rank | review_unit | source_chunk | pages | candidates | exact ratio | top predicates | review focus |
| ---: | --- | --- | --- | ---: | ---: | --- | --- |
| 1 | `JZ-CHUNK-0020-SPLIT-001` | `JZ-CHUNK-0020` | 51-52 | 328 | 0.2133 | USES_INPUT:16; PRODUCES:16; PERFORMED_BY:7; HAS_DECISION_GATEWAY:4 | dense candidate pruning; evidence span repair |
| 2 | `JZ-CHUNK-0016-SPLIT-002` | `JZ-CHUNK-0016` | 44-44 | 137 | 0.3333 | USES_INPUT:18; PRODUCES:16; PERFORMED_BY:8; HAS_DECISION_GATEWAY:6 | dense candidate pruning; evidence span repair |
| 3 | `JZ-CHUNK-0018-SPLIT-001` | `JZ-CHUNK-0018` | 47-48 | 133 | 0.2533 | USES_INPUT:16; PRODUCES:15; PERFORMED_BY:8; HAS_PRINCIPLE:6 | dense candidate pruning; evidence span repair |
| 4 | `JZ-CHUNK-0098-SPLIT-001` | `JZ-CHUNK-0098` | 214-216 | 120 | 0.2267 | USES_INPUT:21; PRODUCES:18; PERFORMED_BY:11 | dense candidate pruning; evidence span repair |
| 5 | `JZ-CHUNK-0101-SPLIT-001` | `JZ-CHUNK-0101` | 219-223 | 99 | 0.4067 | USES_INPUT:21; PRODUCES:21; PERFORMED_BY:6; HAS_DECISION_GATEWAY:2 | dense candidate pruning; evidence span repair |
| 6 | `JZ-CHUNK-0032-SPLIT-001` | `JZ-CHUNK-0032` | 73-76 | 89 | 0.2000 | USES_INPUT:18; PRODUCES:13; PERFORMED_BY:10; HAS_GUARD_CONDITION:3 | dense candidate pruning; evidence span repair |
| 7 | `JZ-CHUNK-0099-SPLIT-001` | `JZ-CHUNK-0099` | 216-217 | 72 | 0.2000 | USES_INPUT:16; PRODUCES:16; PERFORMED_BY:10; HAS_PRINCIPLE:6 | dense candidate pruning; evidence span repair |
| 8 | `JZ-CHUNK-0033-SPLIT-001` | `JZ-CHUNK-0033` | 76-78 | 54 | 0.2933 | HAS_STEP:13; PRECEDES:13; USES_INPUT:7; PRODUCES:7 | dense candidate pruning; evidence span repair |
| 9 | `JZ-CHUNK-0094-SPLIT-001` | `JZ-CHUNK-0094` | 205-208 | 53 | 0.2867 | PERFORMED_BY:17; USES_INPUT:12; PRODUCES:12; HAS_PRINCIPLE:6 | dense candidate pruning; evidence span repair |
| 10 | `JZ-CHUNK-0019-SPLIT-002` | `JZ-CHUNK-0019` | 50-51 | 47 | 0.3830 | PRODUCES:19; USES_INPUT:18; HAS_STEP:3; PERFORMED_BY:2 | dense candidate pruning; evidence span repair |
| 11 | `JZ-CHUNK-0019-SPLIT-001` | `JZ-CHUNK-0019` | 49-50 | 46 | 0.2826 | USES_INPUT:19; PRODUCES:19; PERFORMED_BY:4; HAS_PRINCIPLE:2 | dense candidate pruning; evidence span repair |
| 12 | `JZ-CHUNK-0108-SPLIT-001` | `JZ-CHUNK-0108` | 239-241 | 41 | 0.4715 | PRODUCES:18; USES_INPUT:11; PERFORMED_BY:6; HAS_PRINCIPLE:5 | dense candidate pruning; evidence span repair |
| 13 | `JZ-CHUNK-0104-SPLIT-001` | `JZ-CHUNK-0104` | 228-229 | 34 | 0.1961 | PRODUCES:12; USES_INPUT:11; PERFORMED_BY:5; HAS_PRINCIPLE:4 | evidence span repair |
| 14 | `JZ-CHUNK-0101-SPLIT-002` | `JZ-CHUNK-0101` | 223-223 | 33 | 0.3939 | PRODUCES:14; USES_INPUT:9; PERFORMED_BY:4; HAS_PRINCIPLE:4 | evidence span repair |
| 15 | `JZ-CHUNK-0103-SPLIT-001` | `JZ-CHUNK-0103` | 227-228 | 32 | 0.2083 | USES_INPUT:10; PRODUCES:10; HAS_PRINCIPLE:5; PERFORMED_BY:4 | evidence span repair |
| 16 | `JZ-CHUNK-0002-SPLIT-001` | `JZ-CHUNK-0002` | 21-22 | 28 | 0.1429 | USES_INPUT:4; PRODUCES:4; HAS_PRINCIPLE:4; HAS_STEP:4 | evidence span repair |
| 17 | `JZ-CHUNK-0090-SPLIT-001` | `JZ-CHUNK-0090` | 225-225 | 27 | 0.1111 | USES_INPUT:9; PRODUCES:9; PERFORMED_BY:3; HAS_PRINCIPLE:3 | evidence span repair |
| 18 | `JZ-CHUNK-0016-SPLIT-001` | `JZ-CHUNK-0016` | 43-44 | 26 | 0.3462 | USES_INPUT:8; PRODUCES:8; HAS_STEP:3; HAS_RISK:2 | evidence span repair |
| 19 | `JZ-CHUNK-0097-SPLIT-001` | `JZ-CHUNK-0097` | 212-213 | 26 | 0.3333 | PERFORMED_BY:9; USES_INPUT:6; PRODUCES:6; HAS_PRINCIPLE:3 | evidence span repair |
| 20 | `JZ-CHUNK-0009-SPLIT-001` | `JZ-CHUNK-0009` | 36-36 | 21 | 0.1905 | PERFORMED_BY:6; HAS_PRINCIPLE:6; USES_INPUT:2; PRODUCES:2 | evidence span repair |
| 21 | `JZ-CHUNK-0056-SPLIT-001` | `JZ-CHUNK-0056` | 125-126 | 21 | 0.2698 | USES_INPUT:7; PRODUCES:7; PERFORMED_BY:6; HAS_PRINCIPLE:1 | evidence span repair |
| 22 | `JZ-CHUNK-0002-SPLIT-002` | `JZ-CHUNK-0002` | 22-23 | 16 | 0.1875 | HAS_STEP:6; PRECEDES:4; HAS_REVIEW_CHECKPOINT:3; USES_INPUT:1 | evidence span repair |
| 23 | `JZ-CHUNK-0057-SPLIT-001` | `JZ-CHUNK-0057` | 127-127 | 16 | 0.2292 | PERFORMED_BY:6; HAS_PRINCIPLE:6; USES_INPUT:2; PRODUCES:2 | evidence span repair |
| 24 | `JZ-CHUNK-0106-SPLIT-002` | `JZ-CHUNK-0106` | 234-235 | 15 | 0.1778 | USES_INPUT:6; PRODUCES:6; PERFORMED_BY:1; HAS_PRINCIPLE:1 | evidence span repair |
| 25 | `JZ-CHUNK-0024-SPLIT-001` | `JZ-CHUNK-0024` | 71-71 | 14 | 0.3810 | USES_INPUT:5; PRODUCES:5; PERFORMED_BY:4 | evidence span repair |
| 26 | `JZ-CHUNK-0148-SPLIT-001` | `JZ-CHUNK-0148` | 315-316 | 13 | 0.2821 | PERFORMED_BY:5; USES_INPUT:4; PRODUCES:4 | evidence span repair |
| 27 | `JZ-CHUNK-0001-SPLIT-001` | `JZ-CHUNK-0001` | 19-19 | 11 | 0.1212 | USES_INPUT:2; PRODUCES:2; HAS_STEP:2; HAS_REVIEW_CHECKPOINT:2 | evidence span repair |
| 28 | `JZ-CHUNK-0035-SPLIT-001` | `JZ-CHUNK-0035` | 82-84 | 11 | 0.2424 | PERFORMED_BY:3; HAS_PRINCIPLE:3; USES_INPUT:2; PRODUCES:2 | evidence span repair |
| 29 | `JZ-CHUNK-0042-SPLIT-001` | `JZ-CHUNK-0042` | 98-100 | 11 | 0.3939 | PERFORMED_BY:5; USES_INPUT:3; PRODUCES:3 | evidence span repair |
| 30 | `JZ-CHUNK-0066-SPLIT-001` | `JZ-CHUNK-0066` | 144-145 | 11 | 0.2424 | PERFORMED_BY:2; HAS_RISK:2; USES_INPUT:2; PRODUCES:2 | evidence span repair |
| 31 | `JZ-CHUNK-0093-SPLIT-001` | `JZ-CHUNK-0093` | 203-204 | 11 | 0.3636 | PERFORMED_BY:2; HAS_GUARD_CONDITION:2; USES_INPUT:1; PRODUCES:1 | evidence span repair |
| 32 | `JZ-CHUNK-0106-SPLIT-001` | `JZ-CHUNK-0106` | 233-234 | 11 | 0.1515 | USES_INPUT:3; PRODUCES:3; HAS_PRINCIPLE:2; HAS_RISK:2 | evidence span repair |
| 33 | `JZ-CHUNK-0006-SPLIT-001` | `JZ-CHUNK-0006` | 27-28 | 10 | 0.0000 | HAS_STEP:3; HAS_REVIEW_CHECKPOINT:2; PRECEDES:2; USES_INPUT:1 | evidence span repair |
| 34 | `JZ-CHUNK-0007-SPLIT-001` | `JZ-CHUNK-0007` | 30-31 | 10 | 0.3333 | USES_INPUT:5; PRODUCES:5 | evidence span repair |
| 35 | `JZ-CHUNK-0058-SPLIT-001` | `JZ-CHUNK-0058` | 128-129 | 10 | 0.1333 | PERFORMED_BY:3; USES_INPUT:2; PRODUCES:2; HAS_PRINCIPLE:2 | evidence span repair |
| 36 | `JZ-CHUNK-0097-SPLIT-002` | `JZ-CHUNK-0097` | 213-214 | 10 | 0.1333 | PERFORMED_BY:2; HAS_PRINCIPLE:2; HAS_RISK:2; USES_INPUT:2 | evidence span repair |
| 37 | `JZ-CHUNK-0008-SPLIT-001` | `JZ-CHUNK-0008` | 33-35 | 9 | 0.2593 | USES_INPUT:3; PRODUCES:3; HAS_PRINCIPLE:2; PERFORMED_BY:1 | evidence span repair |
| 38 | `JZ-CHUNK-0069-SPLIT-001` | `JZ-CHUNK-0069` | 152-154 | 9 | 0.2963 | PERFORMED_BY:3; USES_INPUT:2; PRODUCES:2; HAS_PRINCIPLE:1 | evidence span repair |
| 39 | `JZ-CHUNK-0100-SPLIT-001` | `JZ-CHUNK-0100` | 217-218 | 9 | 0.2593 | PERFORMED_BY:3; HAS_RISK:2; HAS_PRINCIPLE:2; USES_INPUT:1 | evidence span repair |
| 40 | `JZ-CHUNK-0005-SPLIT-001` | `JZ-CHUNK-0005` | 25-26 | 8 | 0.3333 | USES_INPUT:2; PRODUCES:2; HAS_STEP:2; PRECEDES:2 | evidence span repair |
| 41 | `JZ-CHUNK-0006-SPLIT-002` | `JZ-CHUNK-0006` | 28-29 | 8 | 0.1250 | HAS_STEP:2; HAS_REVIEW_CHECKPOINT:2; USES_INPUT:1; PRODUCES:1 | evidence span repair |
| 42 | `JZ-CHUNK-0028-SPLIT-001` | `JZ-CHUNK-0028` | 64-65 | 8 | 0.1250 | USES_INPUT:3; PRODUCES:3; PERFORMED_BY:1; HAS_RISK:1 | evidence span repair |
| 43 | `JZ-CHUNK-0034-SPLIT-001` | `JZ-CHUNK-0034` | 79-82 | 8 | 0.2083 | USES_INPUT:3; PRODUCES:3; PERFORMED_BY:1; HAS_PRINCIPLE:1 | evidence span repair |
| 44 | `JZ-CHUNK-0036-SPLIT-001` | `JZ-CHUNK-0036` | 84-86 | 8 | 0.2083 | USES_INPUT:2; PRODUCES:2; PERFORMED_BY:2; HAS_PRINCIPLE:2 | evidence span repair |
| 45 | `JZ-CHUNK-0037-SPLIT-001` | `JZ-CHUNK-0037` | 86-87 | 8 | 0.2083 | USES_INPUT:2; PRODUCES:2; PERFORMED_BY:2; HAS_PRINCIPLE:1 | evidence span repair |
| 46 | `JZ-CHUNK-0107-SPLIT-001` | `JZ-CHUNK-0107` | 237-238 | 8 | 0.2083 | PERFORMED_BY:3; USES_INPUT:2; PRODUCES:2; HAS_PRINCIPLE:1 | evidence span repair |
| 47 | `JZ-CHUNK-0107-SPLIT-002` | `JZ-CHUNK-0107` | 238-238 | 8 | 0.1667 | USES_INPUT:3; PRODUCES:3; PERFORMED_BY:1; HAS_PRINCIPLE:1 | evidence span repair |
| 48 | `JZ-CHUNK-0055-SPLIT-002` | `JZ-CHUNK-0055` | 124-125 | 7 | 0.3810 | USES_INPUT:3; PRODUCES:3; PERFORMED_BY:1 | evidence span repair |
| 49 | `JZ-CHUNK-0058-SPLIT-002` | `JZ-CHUNK-0058` | 129-130 | 7 | 0.0952 | HAS_PRINCIPLE:3; PERFORMED_BY:2; HAS_RISK:2 | evidence span repair |
| 50 | `JZ-CHUNK-0091-SPLIT-001` | `JZ-CHUNK-0091` | 245-247 | 7 | 0.1905 | USES_INPUT:3; PRODUCES:3; PERFORMED_BY:1 | evidence span repair |

## 해석

- `dense candidate pruning`: 후보가 많아 accept/reject 판단 시간이 많이 걸릴 수 있습니다.
- `evidence span repair`: 자동 component span이 exact하지 않으므로 accepted edge에는 사람이 evidence를 더 엄격히 확인해야 합니다.
- `missing-edge scan`: 자동 후보가 거의 없으므로 split text에서 직접 지지되는 빠진 edge가 있는지 확인해야 합니다.
- 이 preview는 300+ strong-paper scale scaffold의 검수 난이도 보조 자료이며, completed human-gold evidence가 아닙니다.
