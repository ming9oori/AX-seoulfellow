# SAC-KG-Style Verifier/Pruner Baseline

Generated: 2026-06-27T23:33:17.877526+00:00
Condition: `B6_sac_kg_verifier_pruner`
Raw file: `experiments/cape_kg_eacl_20260627/48_sac_kg_verifier_pruner_baseline_raw.jsonl`
Valid file: `experiments/cape_kg_eacl_20260627/49_sac_kg_verifier_pruner_baseline_valid.jsonl`

This is a deterministic SAC-KG-style approximation. It uses existing LLM outputs as generator candidates and applies schema/evidence verification plus pruning. It is not a full SAC-KG reproduction.

## Summary

- Chunks: 120
- Raw rows: 120
- Valid rows: 120
- Accepted nodes: 2281
- Accepted edges: 361
- Accepted mappings: 107

## Verifier/Pruner Counters

- accepted_edges: 361
- accepted_mappings: 107
- accepted_nodes: 2281
- edge_pruned_domain_range: 454
- edge_pruned_self_loop: 4
- input_candidate_rows: 600
