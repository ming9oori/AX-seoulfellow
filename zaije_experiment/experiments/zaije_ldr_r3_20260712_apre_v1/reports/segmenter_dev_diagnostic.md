# R3 Segmenter DEV Diagnostic

- Gate R3-1: **PASS**
- This diagnostic used only DEV_EXPOSED_60 and is not reference annotation.
- Fresh API exposure: `0`

| Metric | Value | Threshold |
|---|---:|---:|
| Offset round-trip | 1.0000 | 1.00 |
| Missing anchors / generated anchors | 0.0000 | <=0.05 |
| Over-merged anchors | 0.0453 | <=0.05 |
| Broken structural context | 0.0000 | <=0.02 |
| Deterministic rerun identity | 1.0000 | 1.00 |

Calls: 60; input tokens: 52945; output tokens: 2610; estimated cost: $0.025354.
