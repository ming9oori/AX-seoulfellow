# TRACE-OL Jaije run

Reproduce the deterministic run from the repository root:

```bash
python scripts/run_trace_ol_jaije_experiment.py \
+  --input-xlsx "/home/minjoo/AX_서울펠로우/handoff-hanyang/수주제안/자이제_1.xlsx" \
+  --design "/home/minjoo/AX_서울펠로우/TRACE_OL_자이제_Neo4j_전체실험_설계서.md" \
+  --output-dir "/home/minjoo/AX_서울펠로우/experiments/trace_ol_jaije_neo4j_20260710" \
+  --run-id "run:20260710T000000Z:P2_OFFLINE:a9482ce"
```

Load Neo4j after mounting `/home/minjoo/AX_서울펠로우/experiments/trace_ol_jaije_neo4j_20260710/neo4j` as `/import`:

```bash
cypher-shell -u neo4j -p '<password>' -f /import/00_constraints.cypher
cypher-shell -u neo4j -p '<password>' -f /import/10_load.cypher
cypher-shell -u neo4j -p '<password>' -f /import/40_validate.cypher
```
