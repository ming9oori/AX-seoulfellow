# R3 Segmenter DEV Diagnostic

- Gate R3-1: **REVISE_BEFORE_MODEL_QUALIFICATION**
- This diagnostic used only DEV_EXPOSED_60 and is not reference annotation.
- Fresh API exposure: `0`

| Metric | Value | Threshold |
|---|---:|---:|
| Offset round-trip | 1.0000 | 1.00 |
| Missing anchors / generated anchors | 0.0040 | <=0.05 |
| Over-merged anchors | 0.0726 | <=0.05 |
| Broken structural context | 0.1532 | <=0.02 |
| Deterministic rerun identity | 1.0000 | 1.00 |

Calls: 60; input tokens: 46498; output tokens: 3102; estimated cost: $0.023562.
