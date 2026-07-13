# CAPE-KG Statistical Diagnostics

Generated: 2026-06-27T20:46:36.514406+00:00

This report uses the current silver reference only. It is not final paper evidence until the same analysis is run against adjudicated human-gold labels.

- Proposed condition: `P_cape_kg_actual`
- Chunks: 120
- Bootstrap iterations: 2000

## Paired Bootstrap Delta

| baseline | metric | proposed mean | baseline mean | delta | 95% CI | p approx |
|---|---|---:|---:|---:|---:|---:|
| B0_plain_llm | predicate_f1 | 0.065814 | 0.0 | 0.065814 | [0.041384, 0.094497] | 0.0 |
| B0_plain_llm | node_label_f1 | 0.038278 | 0.03672 | 0.001558 | [-0.012699, 0.016308] | 0.829 |
| B0_plain_llm | evidence_f1 | 0.051636 | 0.020518 | 0.031118 | [0.022698, 0.040338] | 0.0 |
| B1_predicate_constrained | predicate_f1 | 0.065814 | 0.143338 | -0.077525 | [-0.108769, -0.047902] | 0.0 |
| B1_predicate_constrained | node_label_f1 | 0.038278 | 0.0 | 0.038278 | [0.025367, 0.053309] | 0.0 |
| B1_predicate_constrained | evidence_f1 | 0.051636 | 0.022054 | 0.029582 | [0.022272, 0.037203] | 0.0 |
| B2_current_project | predicate_f1 | 0.065814 | 0.013403 | 0.052411 | [0.028477, 0.079871] | 0.0 |
| B2_current_project | node_label_f1 | 0.038278 | 0.024909 | 0.013369 | [0.002472, 0.025422] | 0.018 |
| B2_current_project | evidence_f1 | 0.051636 | 0.042959 | 0.008677 | [0.004498, 0.01324] | 0.0 |
| B3_edc_style | predicate_f1 | 0.065814 | 0.025747 | 0.040066 | [0.014748, 0.067981] | 0.002 |
| B3_edc_style | node_label_f1 | 0.038278 | 0.02188 | 0.016398 | [0.003792, 0.0306] | 0.009 |
| B3_edc_style | evidence_f1 | 0.051636 | 0.027755 | 0.023881 | [0.017186, 0.030731] | 0.0 |
| B4_taxonomy_rag | predicate_f1 | 0.065814 | 0.021969 | 0.043845 | [0.022175, 0.067886] | 0.0 |
| B4_taxonomy_rag | node_label_f1 | 0.038278 | 0.031632 | 0.006646 | [-0.0026, 0.0176] | 0.191 |
| B4_taxonomy_rag | evidence_f1 | 0.051636 | 0.050781 | 0.000854 | [-0.002604, 0.003991] | 0.597 |
| B5_procedural_prompt | predicate_f1 | 0.065814 | 0.017812 | 0.048001 | [0.018717, 0.079442] | 0.004 |
| B5_procedural_prompt | node_label_f1 | 0.038278 | 0.029521 | 0.008757 | [-0.002724, 0.020937] | 0.156 |
| B5_procedural_prompt | evidence_f1 | 0.051636 | 0.049064 | 0.002572 | [-0.001688, 0.007266] | 0.234 |
| P_minus_CQ | predicate_f1 | 0.065814 | 0.044119 | 0.021694 | [0.00152, 0.043661] | 0.035 |
| P_minus_CQ | node_label_f1 | 0.038278 | 0.030825 | 0.007453 | [0.000716, 0.016364] | 0.034 |
| P_minus_CQ | evidence_f1 | 0.051636 | 0.054367 | -0.002731 | [-0.006581, 0.000905] | 0.144 |
| P_minus_Evidence | predicate_f1 | 0.065814 | 0.067236 | -0.001422 | [-0.014755, 0.011638] | 0.823 |
| P_minus_Evidence | node_label_f1 | 0.038278 | 0.035092 | 0.003186 | [-0.003714, 0.009858] | 0.338 |
| P_minus_Evidence | evidence_f1 | 0.051636 | 0.051953 | -0.000318 | [-0.002949, 0.002186] | 0.831 |
| P_minus_Procedural_schema | predicate_f1 | 0.065814 | 0.138237 | -0.072424 | [-0.104442, -0.042405] | 0.0 |
| P_minus_Procedural_schema | node_label_f1 | 0.038278 | 0.033664 | 0.004614 | [-0.004523, 0.014007] | 0.342 |
| P_minus_Procedural_schema | evidence_f1 | 0.051636 | 0.051632 | 4e-06 | [-0.003304, 0.0033] | 0.989 |
| P_minus_Schema_retrieval | predicate_f1 | 0.065814 | 0.08458 | -0.018767 | [-0.04173, 0.004692] | 0.116 |
| P_minus_Schema_retrieval | node_label_f1 | 0.038278 | 0.0248 | 0.013479 | [0.002183, 0.027165] | 0.02 |
| P_minus_Schema_retrieval | evidence_f1 | 0.051636 | 0.047588 | 0.004048 | [0.00025, 0.007925] | 0.038 |
| P_minus_Standard_bridge | predicate_f1 | 0.065814 | 0.083484 | -0.01767 | [-0.040567, 0.0058] | 0.141 |
| P_minus_Standard_bridge | node_label_f1 | 0.038278 | 0.024449 | 0.013829 | [0.004118, 0.024725] | 0.004 |
| P_minus_Standard_bridge | evidence_f1 | 0.051636 | 0.047924 | 0.003712 | [0.000149, 0.007489] | 0.047 |
| P_minus_Validator | predicate_f1 | 0.065814 | 0.055674 | 0.010139 | [-0.005833, 0.027209] | 0.213 |
| P_minus_Validator | node_label_f1 | 0.038278 | 0.03705 | 0.001228 | [-0.004002, 0.006176] | 0.587 |
| P_minus_Validator | evidence_f1 | 0.051636 | 0.051648 | -1.3e-05 | [-0.001581, 0.001625] | 0.983 |

## Chunk-Level Success McNemar Diagnostic

| baseline | metric | proposed-only | baseline-only | both | neither | exact p |
|---|---|---:|---:|---:|---:|---:|
| B0_plain_llm | predicate_f1 | 33 | 0 | 0 | 87 | 0.0 |
| B0_plain_llm | node_label_f1 | 13 | 11 | 31 | 65 | 0.83882 |
| B0_plain_llm | evidence_f1 | 13 | 1 | 57 | 49 | 0.001831 |
| B1_predicate_constrained | predicate_f1 | 2 | 33 | 31 | 54 | 0.0 |
| B1_predicate_constrained | node_label_f1 | 44 | 0 | 0 | 76 | 0.0 |
| B1_predicate_constrained | evidence_f1 | 14 | 1 | 56 | 49 | 0.000977 |
| B2_current_project | predicate_f1 | 30 | 2 | 3 | 85 | 0.0 |
| B2_current_project | node_label_f1 | 16 | 4 | 28 | 72 | 0.011818 |
| B2_current_project | evidence_f1 | 3 | 1 | 67 | 49 | 0.625 |
| B3_edc_style | predicate_f1 | 27 | 3 | 6 | 84 | 8e-06 |
| B3_edc_style | node_label_f1 | 19 | 5 | 25 | 71 | 0.006611 |
| B3_edc_style | evidence_f1 | 11 | 2 | 59 | 48 | 0.022461 |
| B4_taxonomy_rag | predicate_f1 | 26 | 3 | 7 | 84 | 1.5e-05 |
| B4_taxonomy_rag | node_label_f1 | 6 | 3 | 38 | 73 | 0.507812 |
| B4_taxonomy_rag | evidence_f1 | 0 | 1 | 70 | 49 | 1.0 |
| B5_procedural_prompt | predicate_f1 | 29 | 3 | 4 | 84 | 3e-06 |
| B5_procedural_prompt | node_label_f1 | 14 | 7 | 30 | 69 | 0.189247 |
| B5_procedural_prompt | evidence_f1 | 3 | 1 | 67 | 49 | 0.625 |
| P_minus_CQ | predicate_f1 | 15 | 9 | 18 | 78 | 0.307456 |
| P_minus_CQ | node_label_f1 | 4 | 2 | 40 | 74 | 0.6875 |
| P_minus_CQ | evidence_f1 | 1 | 1 | 69 | 49 | 1.0 |
| P_minus_Evidence | predicate_f1 | 1 | 3 | 32 | 84 | 0.625 |
| P_minus_Evidence | node_label_f1 | 3 | 2 | 41 | 74 | 1.0 |
| P_minus_Evidence | evidence_f1 | 0 | 0 | 70 | 50 | 1.0 |
| P_minus_Procedural_schema | predicate_f1 | 4 | 16 | 29 | 71 | 0.011818 |
| P_minus_Procedural_schema | node_label_f1 | 4 | 4 | 40 | 72 | 1.0 |
| P_minus_Procedural_schema | evidence_f1 | 3 | 0 | 67 | 50 | 0.25 |
| P_minus_Schema_retrieval | predicate_f1 | 5 | 17 | 28 | 70 | 0.016901 |
| P_minus_Schema_retrieval | node_label_f1 | 11 | 4 | 33 | 72 | 0.118469 |
| P_minus_Schema_retrieval | evidence_f1 | 2 | 0 | 68 | 50 | 0.5 |
| P_minus_Standard_bridge | predicate_f1 | 5 | 16 | 28 | 71 | 0.026604 |
| P_minus_Standard_bridge | node_label_f1 | 15 | 5 | 29 | 71 | 0.041389 |
| P_minus_Standard_bridge | evidence_f1 | 3 | 1 | 67 | 49 | 0.625 |
| P_minus_Validator | predicate_f1 | 8 | 6 | 25 | 81 | 0.790527 |
| P_minus_Validator | node_label_f1 | 3 | 0 | 41 | 76 | 0.25 |
| P_minus_Validator | evidence_f1 | 1 | 0 | 69 | 50 | 1.0 |

## Files

- JSON: `experiments/cape_kg_eacl_20260627/04_evaluation/statistical_analysis_metrics.json`
- Bootstrap CSV: `experiments/cape_kg_eacl_20260627/04_evaluation/statistical_analysis_bootstrap.csv`
- McNemar CSV: `experiments/cape_kg_eacl_20260627/04_evaluation/statistical_analysis_mcnemar.csv`
- Per-chunk CSV: `experiments/cape_kg_eacl_20260627/04_evaluation/statistical_analysis_chunk_scores.csv`
