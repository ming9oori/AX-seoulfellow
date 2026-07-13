# CAPE-KG Active Review Ablation Diagnostic

Generated: 2026-06-29T18:55:22.691500+00:00

This report makes the revised plan's `P - Active review` ablation explicit.
It is a silver/proxy diagnostic only; final active-review efficiency requires human effort timing and adjudicated labels.

## Summary

- Base condition: `P_cape_kg_actual`
- Compared conditions: `['P_cape_kg_actual_with_active_review', 'P_minus_Active_review_random_expected', 'P_minus_Active_review_uncertainty_only']`
- Row count: 24
- Claim status: `silver_proxy_ablation_not_human_efficiency`

## Ablation Rows

| target | condition | strategy | budget | errors found | precision@k | recall@k | lift |
|---|---|---|---:|---:|---:|---:|---:|
| all_silver_error | P_cape_kg_actual_with_active_review | active_priority | 10 | 10 | 1.0 | 0.03663 | 1.007326 |
| all_silver_error | P_minus_Active_review_random_expected | random_expected | 10 | 9.927273 | 0.992727 | 0.036364 | 1.0 |
| all_silver_error | P_minus_Active_review_uncertainty_only | uncertainty_only | 10 | 10 | 1.0 | 0.03663 | 1.007326 |
| all_silver_error | P_cape_kg_actual_with_active_review | active_priority | 25 | 25 | 1.0 | 0.091575 | 1.007326 |
| all_silver_error | P_minus_Active_review_random_expected | random_expected | 25 | 24.818182 | 0.992727 | 0.090909 | 1.0 |
| all_silver_error | P_minus_Active_review_uncertainty_only | uncertainty_only | 25 | 25 | 1.0 | 0.091575 | 1.007326 |
| all_silver_error | P_cape_kg_actual_with_active_review | active_priority | 55 | 55 | 1.0 | 0.201465 | 1.007326 |
| all_silver_error | P_minus_Active_review_random_expected | random_expected | 55 | 54.6 | 0.992727 | 0.2 | 1.0 |
| all_silver_error | P_minus_Active_review_uncertainty_only | uncertainty_only | 55 | 55 | 1.0 | 0.201465 | 1.007326 |
| all_silver_error | P_cape_kg_actual_with_active_review | active_priority | 100 | 100 | 1.0 | 0.3663 | 1.007326 |
| all_silver_error | P_minus_Active_review_random_expected | random_expected | 100 | 99.272727 | 0.992727 | 0.363636 | 1.0 |
| all_silver_error | P_minus_Active_review_uncertainty_only | uncertainty_only | 100 | 100 | 1.0 | 0.3663 | 1.007326 |
| high_impact_error | P_cape_kg_actual_with_active_review | active_priority | 10 | 6 | 0.6 | 0.034682 | 0.953757 |
| high_impact_error | P_minus_Active_review_random_expected | random_expected | 10 | 6.290909 | 0.629091 | 0.036364 | 1.0 |
| high_impact_error | P_minus_Active_review_uncertainty_only | uncertainty_only | 10 | 6 | 0.6 | 0.034682 | 0.953757 |
| high_impact_error | P_cape_kg_actual_with_active_review | active_priority | 25 | 16 | 0.64 | 0.092486 | 1.017341 |
| high_impact_error | P_minus_Active_review_random_expected | random_expected | 25 | 15.727273 | 0.629091 | 0.090909 | 1.0 |
| high_impact_error | P_minus_Active_review_uncertainty_only | uncertainty_only | 25 | 15 | 0.6 | 0.086705 | 0.953757 |
| high_impact_error | P_cape_kg_actual_with_active_review | active_priority | 55 | 36 | 0.654545 | 0.208092 | 1.040462 |
| high_impact_error | P_minus_Active_review_random_expected | random_expected | 55 | 34.6 | 0.629091 | 0.2 | 1.0 |
| high_impact_error | P_minus_Active_review_uncertainty_only | uncertainty_only | 55 | 38 | 0.690909 | 0.219653 | 1.098266 |
| high_impact_error | P_cape_kg_actual_with_active_review | active_priority | 100 | 56 | 0.56 | 0.323699 | 0.890173 |
| high_impact_error | P_minus_Active_review_random_expected | random_expected | 100 | 62.909091 | 0.629091 | 0.363636 | 1.0 |
| high_impact_error | P_minus_Active_review_uncertainty_only | uncertainty_only | 100 | 72 | 0.72 | 0.416185 | 1.144509 |

## Interpretation

- `P_cape_kg_actual_with_active_review` uses the CAPE active-priority queue.
- `P_minus_Active_review_random_expected` removes active review and uses the random expected baseline.
- `P_minus_Active_review_uncertainty_only` keeps uncertainty ranking but removes the multi-signal active-priority queue.
- Do not report these values as final human-review efficiency until human timing/correction files are returned.
