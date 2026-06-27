# Limitations

This run is an EACL experiment scaffold and silver/proxy evaluation, not a
paper-claimable final result.

- The reference labels are derived from the current AX-EPAK KG and must be
  replaced or adjudicated by two human annotators.
- Baseline rows are deterministic proxies used to validate the metric pipeline.
  Actual B0/B1/B2/B4/B5 LLM generations must be run before making comparative
  claims.
- A small local Qwen3-8B smoke run may be present in this package, but it is
  only an execution-path check unless expanded to the full experimental design.
- PAGED/Text2KGBench cross-benchmark experiments are represented in the plan
  but are not completed in this local run.
- Raw text release still requires copyright review.
