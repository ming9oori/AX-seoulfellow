# CAPE-KG Strong 300+ Return Apply Refusal

Started: `2026-06-29T15:21:02Z`
Ended: `2026-06-29T15:21:03Z`
Experiment: `experiments/cape_kg_eacl_20260627`
APPLY_IMPORTS: `1`

## Status

- Wrapper status: `refused_empty_apply_no_strong_reviewed_files`
- Exit code: 3
- Reason: APPLY_IMPORTS=1 was requested, but no reviewed strong 300+ return files are present.
- Return preflight: `pending_strong_human_returns`
- Present strong return files: 0
- Apply scope: `no_strong_return_files`
- Ready for strong IAA: False
- Ready for strong claim after import: False

## Interpretation

- This is an intentional safety refusal, not an experiment failure.
- The wrapper prevents an accidental no-op strong apply run from being mistaken for imported 300+ human-gold evidence.
- Add reviewed strong return files or set `ALLOW_EMPTY_APPLY=1` only for an explicitly intended no-op refresh.
