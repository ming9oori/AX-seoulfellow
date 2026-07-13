# CAPE-KG Human Return Apply Refusal

Started: `2026-06-29T03:44:03Z`
Ended: `2026-06-29T03:44:04Z`
Experiment: `experiments/cape_kg_eacl_20260627`
APPLY_IMPORTS: `1`

## Status

- Wrapper status: `refused_empty_apply_no_reviewed_files`
- Exit code: 3
- Reason: APPLY_IMPORTS=1 was requested, but no reviewed human-return files are present.
- Return preflight: `pending_human_returns`
- Present human return files: 0
- Apply scope: `no_return_files`
- Minimum paper gate ready after preflight: False
- Optional mapping ready after preflight: False
- Optional crosswalk ready after preflight: False
- Optional active-effort ready after preflight: False
- Annotation present files: 0
- Annotation ready for minimum import: False
- Adjudication present: False
- Mapping present: False
- Crosswalk present: False
- Active-review effort present: False

## Interpretation

- This is an intentional safety refusal, not an experiment failure.
- The wrapper prevents an accidental no-op apply run from being mistaken for imported human-gold evidence.
- Add reviewed return files or set `ALLOW_EMPTY_APPLY=1` only for an explicitly intended no-op refresh.
