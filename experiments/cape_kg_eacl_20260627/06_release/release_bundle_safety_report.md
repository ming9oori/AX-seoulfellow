# CAPE-KG Release Bundle Safety Report

Generated: 2026-06-29T19:07:57.601712+00:00

## Bundles

- Internal reproducibility bundle: `experiments/cape_kg_eacl_20260627/06_release/bundles/cape_kg_eacl_internal_repro_return_preflight_sync02_20260629.tar.gz`
  - SHA256: `cfa7764221cbc9aae54c0833d0a74740f46b676bb86f5aa925ab8e533aa3c4b0`
  - Files: 1704
- Public-safe skeleton bundle: `experiments/cape_kg_eacl_20260627/06_release/bundles/cape_kg_eacl_public_safe_skeleton_return_preflight_sync02_20260629.tar.gz`
  - SHA256: `92045dee721c3da3ce3caefa92a8b0c7aead9cbff86459ce3e2fc56d54b2df0a`
  - Files: 383

## Safety Notes

- The internal bundle may contain source-derived chunk text and annotation work files. Treat it as local/internal unless rights are cleared.
- The public-safe skeleton bundle excludes `01_data`, human-gold batch files, annotation JSONL files, and raw source-text workbench inputs.
- Live post-bundle status files such as `latest_release_bundle_index`, `pre_human_handoff_validation`, `human_review_status_dashboard_ko`, `anonymized_submission_prep`, `eacl_submission_package_manifest`, and `post_annotation_refresh_last_run` are regenerated outside the tarball to avoid self-referential checksum drift.
- Public paper claims still require human gold annotation, IAA, adjudication, and human-gold scoring.

## Public-Safe Text-Risk Scan

- No public-safe bundle files matched the conservative text-risk patterns.

## Public-Safe Text-Content Reference Scan

- No public-safe text files mentioned conservative internal path/name patterns.

## Public-Safe Candidate Exclusions

- Files excluded from the public-safe skeleton by conservative text/path filtering: 87
- Excluded-file review queue: `experiments/cape_kg_eacl_20260627/06_release/public_external_release_excluded_review_queue.md`

## Checksum Files

- Internal checksums: `experiments/cape_kg_eacl_20260627/06_release/bundles/cape_kg_eacl_internal_return_preflight_sync02_20260629.sha256`
- Public-safe checksums: `experiments/cape_kg_eacl_20260627/06_release/bundles/cape_kg_eacl_public_safe_return_preflight_sync02_20260629.sha256`
