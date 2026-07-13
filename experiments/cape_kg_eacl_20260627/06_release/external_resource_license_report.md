# CAPE-KG External Resource License and Citation Report

Generated: 2026-06-28T20:20:00.785149+00:00
Claim status: `external_resource_license_report_ready_not_legal_advice`

This report records source, license, citation, and public-release handling for external/public resources and release-sensitive internal resources. It is a reproducibility and release-safety artifact, not legal advice and not human-gold performance evidence.

## Summary

| Item | Value |
|---|---:|
| Resources | 6 |
| Public benchmarks | 2 |
| Rights/redistribution review required | 3 |
| Validation issues | 0 |

## Resource Table

| resource | type | license/status | local status | public-safe release action | citation/rights note |
|---|---|---|---|---|---|
| `PAGED` | public_benchmark | Apache-2.0 | present_dir | release_adapter_outputs_and_cite_original_license; do_not_relicense_original_benchmark | Follow original benchmark license and cite the paper/source URL in any public release. |
| `Text2KGBench` | public_benchmark | Apache-2.0 | present_dir | release_adapter_outputs_and_cite_original_license; do_not_relicense_original_benchmark | Follow original benchmark license and cite the paper/source URL in any public release. |
| `CAPE_public_synthetic_examples` | synthetic_release_artifact | project_defined_synthetic_example | present_dir | public_safe_include | Synthetic only; not copied, paraphrased, or derived from the private/source corpus. |
| `private_bid_proposal_corpus` | private_source_corpus | rights_review_required | present_file | exclude_raw_text_from_public_safe_bundle | Do not externally publish raw OCR/source-derived text unless redistribution rights are explicitly cleared. |
| `NCS_standard_layer` | standard_taxonomy | verify_before_public_redistribution | present_file | cite_source_and_verify_redistribution_terms | Use as a reference layer; verify redistribution terms before including source-derived taxonomy files publicly. |
| `PCF_standard_layer` | standard_taxonomy | verify_before_public_redistribution | present_file | cite_source_and_verify_redistribution_terms | Use as a reference layer; verify redistribution terms before including source-derived taxonomy files publicly. |

## Public Benchmark Details

| benchmark | source | paper | git revision | adapter items | license file |
|---|---|---|---|---:|---|
| PAGED | https://github.com/WitcherLeo/PAGED | https://aclanthology.org/2024.acl-long.583/ | `c0cf4e8552afc6aa0e6ef00e5de01beac0100a05` | 100 | `experiments/cape_kg_eacl_20260627/08_public_benchmarks/repos/PAGED/LICENSE` |
| Text2KGBench | https://github.com/cenguix/Text2KGBench | https://doi.org/10.1007/978-3-031-47243-5_14 | `50a3d255371b8817cdff70fd88459ac82b339cfe` | 200 | `experiments/cape_kg_eacl_20260627/08_public_benchmarks/repos/Text2KGBench/LICENSE` |
