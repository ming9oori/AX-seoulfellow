# R4 Selective LLM DEV Report

- Gate R4-3: **PASS**
- Model: `gpt-4.1-2025-04-14`
- Selected B2 budget: `20%`
- Confirmatory API exposure: `0`
- TEST access: `0`

| Metric | Value | Gate |
|---|---:|---:|
| Source mismatch rejection | 1.0000 | >=0.95 |
| Repeat agreement | 0.9750 | >=0.90 |
| Control accuracy | 1.0000 | >=0.95 |
| Unsupported free generation | 0 | 0 |

## Budget sweep

| Budget | Selected | Accepted | Yield ratio to B3 |
|---:|---:|---:|---:|
| 0% | 0 | 0 | 0.0000 |
| 5% | 16 | 13 | 0.0421 |
| 10% | 31 | 28 | 0.0906 |
| 20% | 63 | 59 | 0.1909 |
| 40% | 125 | 121 | 0.3916 |
| 100% | 313 | 309 | 1.0000 |
