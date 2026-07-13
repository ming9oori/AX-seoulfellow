# Evidence Grounding Report

Claim status: `silver_proxy_evidence_grounding_diagnostic_not_human_gold`

This report summarizes evidence-grounding behavior for the silver/proxy scaffold.
The EM, IoU, and unsupported-edge values below are not paper-claimable human-gold evidence metrics.
Use adjudicated human-gold spans and `human_gold_span_iou_metrics.json` for final evidence exactness claims.

## Summary Table

| condition | evidence EM | evidence IoU | unsupported edge rate | claim status |
|---|---:|---:|---:|---|
| B0_plain_llm_proxy | 0.0 | 0.0 | 0.0 | silver/proxy only |
| B1_predicate_constrained_proxy | 1.0 | 1.0 | 0.0 | silver/proxy only |
| B2_current_project_baseline | 1.0 | 1.0 | 0.0 | silver/proxy only |
| B4_taxonomy_rag_proxy | 1.0 | 1.0 | 0.0 | silver/proxy only |
| B5_procedural_prompt_proxy | 1.0 | 1.0 | 0.0 | silver/proxy only |
| P_cape_kg_silver | 1.0 | 1.0 | 0.0 | silver/proxy only |
| P_minus_CQ_proxy | 1.0 | 1.0 | 0.0 | silver/proxy only |
| P_minus_Evidence_proxy | 0.0 | 0.0 | 1.0 | silver/proxy only |
| P_minus_Procedural_schema_proxy | 1.0 | 1.0 | 0.0 | silver/proxy only |
| P_minus_Validator_proxy | 0.9725 | 1.0 | 0.0 | silver/proxy only |
| P_minus_Standard_bridge_proxy | 1.0 | 1.0 | 0.0 | silver/proxy only |

## Interpretation

- `P_minus_Evidence_proxy` is expected to expose the evidence-removal ablation behavior.
- Conditions with high proxy evidence scores are showing attachment to the silver scaffold, not adjudicated correctness.
- Final paper claims require completed human-gold annotation, adjudication, and component/span IoU scoring.
