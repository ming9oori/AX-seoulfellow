# CAPE-KG Human Return Apply Last Run

Started: `2026-06-29T18:55:20Z`
Ended: `2026-06-29T18:57:01Z`
Experiment: `experiments/cape_kg_eacl_20260627`
APPLY_IMPORTS: `0`

## Status

- Wrapper status: `completed`
- Exit code: 0
- Return preflight: `pending_human_returns`
- Present human return files: 0
- Apply scope: `no_return_files`
- Minimum paper gate ready after preflight: False
- Optional mapping ready after preflight: False
- Optional crosswalk ready after preflight: False
- Optional active-effort ready after preflight: False
- Annotation valid files: 0
- Paired completed annotation chunks: 0
- Adjudication completed chunks: 0
- Mapping complete Top-5 groups: 0
- Crosswalk complete source groups: 0
- Active-review timed rows: 0
- Post-refresh claim status: `post_annotation_refresh_success_pending_human_returns`
- Claim gate: `FAIL`
- Required claim-gate failures: 4
- Optional claim-gate failures: 2
- Pre-human handoff validation: `PASS`; source `experiments/cape_kg_eacl_20260627/06_release/pre_human_handoff_validation.md`
- Completion status: `not_complete_pending_human_gold_iaa_adjudication_and_expert_review`
- Release checksum status: `OK`
- Handoff checksum status: `OK`

## Interpretation

- This wrapper validates returned human-review files before running the post-annotation refresh.
- `APPLY_IMPORTS=0` is a dry-run path; `APPLY_IMPORTS=1` applies validated reviewed files.
- Partial validated returns may be applied incrementally, but only `minimum_annotation_adjudication_ready_optional_pending` or `all_minimum_and_optional_returns_ready` can unlock minimum paper-claim scoring.
- If no reviewed return files are present, `APPLY_IMPORTS=1` is refused unless `ALLOW_EMPTY_APPLY=1` is set.
