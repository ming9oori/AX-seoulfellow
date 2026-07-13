# Neo4j Import CSV Validation Report

Generated: 2026-06-29T18:56:41.489319+00:00
Import directory: `outputs/11_neo4j_import_flat`
Overall status: **PASS**

## Summary

- CSV files: 19
- Total rows: 25483
- Files with issues: 0

## Files

| file | rows | status | issues |
|---|---:|---|---|
| `outputs/11_neo4j_import_flat/EVIDENCED_BY.csv` | 3915 | PASS | - |
| `outputs/11_neo4j_import_flat/FEEDS_INTO.csv` | 9 | PASS | - |
| `outputs/11_neo4j_import_flat/HAS_CHILD.csv` | 2639 | PASS | - |
| `outputs/11_neo4j_import_flat/HAS_COMPETENCY_UNIT.csv` | 3450 | PASS | - |
| `outputs/11_neo4j_import_flat/HAS_DECISION_GATEWAY.csv` | 54 | PASS | - |
| `outputs/11_neo4j_import_flat/HAS_GUARD_CONDITION.csv` | 14 | PASS | - |
| `outputs/11_neo4j_import_flat/HAS_METRIC.csv` | 3284 | PASS | - |
| `outputs/11_neo4j_import_flat/HAS_PRINCIPLE.csv` | 64 | PASS | - |
| `outputs/11_neo4j_import_flat/HAS_REVIEW_CHECKPOINT.csv` | 41 | PASS | - |
| `outputs/11_neo4j_import_flat/HAS_RISK.csv` | 39 | PASS | - |
| `outputs/11_neo4j_import_flat/HAS_STEP.csv` | 99 | PASS | - |
| `outputs/11_neo4j_import_flat/PERFORMED_BY.csv` | 120 | PASS | - |
| `outputs/11_neo4j_import_flat/PRECEDES.csv` | 77 | PASS | - |
| `outputs/11_neo4j_import_flat/PROCESS_CONTEXT.csv` | 110 | PASS | - |
| `outputs/11_neo4j_import_flat/PRODUCES.csv` | 220 | PASS | - |
| `outputs/11_neo4j_import_flat/REQUIRES_CAPABILITY.csv` | 110 | PASS | - |
| `outputs/11_neo4j_import_flat/USED_AS_INPUT_FOR.csv` | 9 | PASS | - |
| `outputs/11_neo4j_import_flat/USES_INPUT.csv` | 201 | PASS | - |
| `outputs/11_neo4j_import_flat/nodes.csv` | 11028 | PASS | - |

## Notes

- JSON carrier fields are expected to use `base64:<payload>` values.
- `backslash_escaped_quote` should be zero for Neo4j Desktop compatibility.
- Mapping relationship types should preserve CAPE schema underscores, e.g. `REQUIRES_CAPABILITY` and `PROCESS_CONTEXT`.
