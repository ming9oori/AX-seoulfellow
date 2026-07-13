# R4 Selective LLM DEV Report

- Gate R4-3: **REVISE_BEFORE_CONFIRMATORY**
- Model: `gpt-4.1-2025-04-14`
- Selected B2 budget: `20%`
- Confirmatory API exposure: `0`
- TEST access: `0`

| Metric | Value | Gate |
|---|---:|---:|
| Source mismatch rejection | 0.6000 | >=0.95 |
| Repeat agreement | 0.9750 | >=0.90 |
| Control accuracy | 0.8000 | >=0.95 |
| Unsupported free generation | 0 | 0 |

## Budget sweep

| Budget | Selected | Accepted | Yield ratio to B3 |
|---:|---:|---:|---:|
| 0% | 0 | 0 | 0.0000 |
| 5% | 16 | 16 | 0.0513 |
| 10% | 31 | 31 | 0.0994 |
| 20% | 63 | 63 | 0.2019 |
| 40% | 125 | 125 | 0.4006 |
| 100% | 298 | 297 | 0.9519 |
