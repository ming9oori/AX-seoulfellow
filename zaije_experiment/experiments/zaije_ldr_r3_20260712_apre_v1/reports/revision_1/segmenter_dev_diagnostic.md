# R3 Segmenter DEV Diagnostic

- Gate R3-1: **REVISE_BEFORE_MODEL_QUALIFICATION**
- This diagnostic used only DEV_EXPOSED_60 and is not reference annotation.
- Fresh API exposure: `0`

| Metric | Value | Threshold |
|---|---:|---:|
| Offset round-trip | 1.0000 | 1.00 |
| Missing anchors / generated anchors | 0.0132 | <=0.05 |
| Over-merged anchors | 0.1060 | <=0.05 |
| Broken structural context | 0.1589 | <=0.02 |
| Deterministic rerun identity | 1.0000 | 1.00 |

Calls: 60; input tokens: 32224; output tokens: 2908; estimated cost: $0.017542.
