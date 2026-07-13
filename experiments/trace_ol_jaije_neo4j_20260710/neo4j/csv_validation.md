# Neo4j Import CSV Validation Report

Generated: 2026-07-10T07:17:20.173673+00:00
Import directory: `experiments/trace_ol_jaije_neo4j_20260710/neo4j`
Overall status: **PASS**

## Summary

- CSV files: 2
- Total rows: 12258
- Files with issues: 0

## Files

| file | rows | status | issues |
|---|---:|---|---|
| `experiments/trace_ol_jaije_neo4j_20260710/neo4j/nodes.csv` | 4975 | PASS | - |
| `experiments/trace_ol_jaije_neo4j_20260710/neo4j/relationships.csv` | 7283 | PASS | - |

## Notes

- JSON carrier fields are expected to use `base64:<payload>` values.
- `backslash_escaped_quote` should be zero for Neo4j Desktop compatibility.
- Mapping relationship types should preserve CAPE schema underscores, e.g. `REQUIRES_CAPABILITY` and `PROCESS_CONTEXT`.
