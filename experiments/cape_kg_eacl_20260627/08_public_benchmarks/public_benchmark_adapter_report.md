# Public Benchmark Adapter Report

Generated: 2026-06-28T15:59:33.374278+00:00

## Status

- PAGED and Text2KGBench repositories were acquired locally.
- Dataset profiles and CAPE-KG adapter subsets were generated.
- Public model evaluation runs found: 4.
- Strong cross-check run present: True.

## PAGED

- Source: https://github.com/WitcherLeo/PAGED
- Local repo: `experiments/cape_kg_eacl_20260627/08_public_benchmarks/repos/PAGED`
- Adapter subset items: 100
- train: items=1697, step_nodes=22993, data_nodes=1792, sequence_flows=23424
- dev: items=543, step_nodes=7153, data_nodes=516, sequence_flows=7224
- test: items=1154, step_nodes=15892, data_nodes=1192, sequence_flows=16388

## Text2KGBench

- Source: https://github.com/cenguix/Text2KGBench
- Local repo: `experiments/cape_kg_eacl_20260627/08_public_benchmarks/repos/Text2KGBench`
- Adapter subset items: 200
- wikidata_tekgen: ontologies=10; train: rows=5335, triples=0; validation: rows=3993, triples=0; test: rows=4062, triples=0; ground_truth: rows=4062, triples=7232
- dbpedia_webnlg: ontologies=19; train: rows=2846, triples=8623; test: rows=2014, triples=0; ground_truth: rows=2014, triples=6259

## Model Evaluation Runs

| run | PAGED n | PAGED edge F1 | Text2KG n | relation F1 | triple F1 |
|---|---:|---:|---:|---:|---:|
| `public_qwen3_14b_subset_eval` | 10 | 0.1446 | 20 | 0.2817 | 0.02 |
| `public_qwen3_8b_full_adapter_eval` | 100 | 0.4233 | 200 | 0.6015 | 0.1736 |
| `public_qwen3_8b_subset_eval` | 10 | 0.1794 | 20 | 0.45 | 0.05 |
| `public_qwen3_8b_subset_smoke` | 3 | 0.1333 | 5 | 0.4 | 0.0 |

## CAPE-KG Use

- PAGED maps to the procedural graph extraction side of CAPE-KG.
- Text2KGBench maps to ontology-constrained KG extraction and conformance checks.
- These public results are auxiliary diagnostics, not official leaderboard or Korean enterprise human-gold claims.
