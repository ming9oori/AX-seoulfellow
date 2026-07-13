# Neo4j Import CSV Validation Report

Generated: 2026-07-10T10:52:38.071503+00:00
Import directory: `trace_ol_pilot_v1/runs/pilot_run_20260710_v1/neo4j`
Overall status: **PASS**

## Summary

- CSV files: 9
- Total rows: 989
- Files with issues: 0

## Files

| file | rows | status | issues |
|---|---:|---|---|
| `trace_ol_pilot_v1/runs/pilot_run_20260710_v1/neo4j/neo4j_assertions.csv` | 52 | PASS | - |
| `trace_ol_pilot_v1/runs/pilot_run_20260710_v1/neo4j/neo4j_claims.csv` | 238 | PASS | - |
| `trace_ol_pilot_v1/runs/pilot_run_20260710_v1/neo4j/neo4j_concepts.csv` | 31 | PASS | - |
| `trace_ol_pilot_v1/runs/pilot_run_20260710_v1/neo4j/neo4j_conditions.csv` | 8 | PASS | - |
| `trace_ol_pilot_v1/runs/pilot_run_20260710_v1/neo4j/neo4j_documents.csv` | 1 | PASS | - |
| `trace_ol_pilot_v1/runs/pilot_run_20260710_v1/neo4j/neo4j_evidence.csv` | 180 | PASS | - |
| `trace_ol_pilot_v1/runs/pilot_run_20260710_v1/neo4j/neo4j_relationships.csv` | 438 | PASS | - |
| `trace_ol_pilot_v1/runs/pilot_run_20260710_v1/neo4j/neo4j_rules.csv` | 5 | PASS | - |
| `trace_ol_pilot_v1/runs/pilot_run_20260710_v1/neo4j/neo4j_sections.csv` | 36 | PASS | - |

## Notes

- JSON carrier fields are expected to use `base64:<payload>` values.
- `backslash_escaped_quote` should be zero for Neo4j Desktop compatibility.
- Mapping relationship types should preserve CAPE schema underscores, e.g. `REQUIRES_CAPABILITY` and `PROCESS_CONTEXT`.
