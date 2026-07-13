# Public Benchmark Cross-Check Summary

Generated: 2026-06-28T15:59:33.374278+00:00
Claim status: `public_adapter_model_runs_diagnostic_not_official_leaderboard`

This report consolidates public PAGED/Text2KGBench adapter model runs. These are diagnostic adapter runs, not official benchmark leaderboard claims.

## Gate Evidence

- Run count: 4
- Strong cross run present: True
- Max single-run PAGED items: 100
- Max single-run Text2KGBench items: 200
- Best PAGED edge F1: 0.4233 (`public_qwen3_8b_full_adapter_eval`)
- Best Text2KGBench relation F1: 0.6015 (`public_qwen3_8b_full_adapter_eval`)

## Runs

| run | PAGED n | PAGED node F1 | PAGED edge F1 | Text2KG n | relation F1 | triple F1 | errors |
|---|---:|---:|---:|---:|---:|---:|---:|
| `public_qwen3_14b_subset_eval` | 10 | 0.1733 | 0.1446 | 20 | 0.2817 | 0.02 | 14 |
| `public_qwen3_8b_full_adapter_eval` | 100 | 0.2472 | 0.4233 | 200 | 0.6015 | 0.1736 | 100 |
| `public_qwen3_8b_subset_eval` | 10 | 0.1608 | 0.1794 | 20 | 0.45 | 0.05 | 14 |
| `public_qwen3_8b_subset_smoke` | 3 | 0.0 | 0.1333 | 5 | 0.4 | 0.0 | 5 |

## Claim Scope

- Public adapter runs support external diagnostic coverage only.
- The Korean enterprise main result still requires adjudicated human-gold scoring.
- PAGED and Text2KGBench metrics are not directly comparable to the internal CAPE-KG task because schemas and gold structures differ.
