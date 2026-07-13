# R3 Pointwise Model Role Qualification

- Gate R3-2: **PASS**
- Primary: `C04`
- Falsifier: `C01`
- Data: DEV_EXPOSED_24 only
- Fresh API exposure: `0`

| Primary | Claim agreement | Positive F1 | Critical facet | Control BA | Qualified |
|---|---:|---:|---:|---:|---|
| C02 | 1.0000 | 1.0000 | 0.8750 | 0.9583 | False |
| C03 | 0.9583 | 0.9744 | 0.8750 | 0.9167 | False |
| C04 | 0.9583 | 0.9756 | 1.0000 | 0.9583 | True |

| Falsifier | Supported recall | Contradicted recall | BA | Repeat | Qualified |
|---|---:|---:|---:|---:|---|
| C01 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | True |
| C03 | 0.9167 | 0.9583 | 0.9375 | 0.9583 | True |
| C04 | 0.9167 | 1.0000 | 0.9583 | 1.0000 | True |

Actual calls: 936; input tokens: 347259; output tokens: 26449; estimated cost: $0.734520.
