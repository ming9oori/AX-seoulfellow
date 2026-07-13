# CAPE-KG Latest Release Bundle Index

Generated: 2026-06-29T19:07:57.601712+00:00
Claim status: `latest_release_bundle_index_ready_not_submission_complete`
Stamp: `return_preflight_sync02_20260629`

## Current Bundles

| bundle | path | sha256 | bytes | files |
| --- | --- | --- | ---: | ---: |
| internal reproducibility | `experiments/cape_kg_eacl_20260627/06_release/bundles/cape_kg_eacl_internal_repro_return_preflight_sync02_20260629.tar.gz` | `cfa7764221cbc9aae54c0833d0a74740f46b676bb86f5aa925ab8e533aa3c4b0` | 43666956 | 1704 |
| public-safe skeleton | `experiments/cape_kg_eacl_20260627/06_release/bundles/cape_kg_eacl_public_safe_skeleton_return_preflight_sync02_20260629.tar.gz` | `92045dee721c3da3ce3caefa92a8b0c7aead9cbff86459ce3e2fc56d54b2df0a` | 1532248 | 383 |

## Verification Commands

```bash
sha256sum -c experiments/cape_kg_eacl_20260627/06_release/release_bundle_checksums.sha256
sha256sum -c experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/human_review_handoff_checksums.sha256
python3 scripts/validate_cape_pre_human_handoff.py --experiment-dir experiments/cape_kg_eacl_20260627 --outputs-dir outputs
```

## Superseded Bundle Counts

- Internal reproducibility bundles older than current: 261
- Public-safe skeleton bundles older than current: 261

## Public Release Note

- Use the public-safe skeleton bundle for external artifact sharing. The internal reproducibility bundle may contain source-derived text and review work files.
- These bundles are release/reproducibility artifacts only. Submission-level performance claims remain pending human-gold annotation, IAA, adjudication, proposed human-gold scoring, mapping expert review, NCS-PCF crosswalk expert review, and active-review effort collection.

## Related Files

- Release manifest: `experiments/cape_kg_eacl_20260627/06_release/release_bundle_manifest.json`
- Release checksums: `experiments/cape_kg_eacl_20260627/06_release/release_bundle_checksums.sha256`
- Safety report: `experiments/cape_kg_eacl_20260627/06_release/release_bundle_safety_report.md`
