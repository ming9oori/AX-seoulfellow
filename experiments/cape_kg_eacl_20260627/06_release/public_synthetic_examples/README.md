# Public Synthetic CAPE-KG Examples

These files are synthetic examples for public reproducibility checks.
They are not copied, paraphrased, or derived from the private/source corpus.

## Files

- `synthetic_chunks.jsonl`: toy public-safe input chunks.
- `synthetic_gold.jsonl`: toy gold annotation rows using the CAPE node, edge, and evidence-anchor shape.
- `synthetic_predictions.jsonl`: toy prediction rows in the CAPE output shape.
- `synthetic_evaluation_summary.json`: schema validation and count summary.

## Intended Use

Use this package to inspect the expected JSONL structure, evidence anchors, and schema-conformant procedural edges without exposing copyrighted source text.
It is a format and release-safety artifact only; it is not a paper result and must not be mixed with human-gold evaluation.

## Summary

- Synthetic chunks: 2
- Synthetic nodes: 8
- Synthetic edges: 6
- Validation errors: 0
- Claim status: `public_format_example_not_paper_result`
