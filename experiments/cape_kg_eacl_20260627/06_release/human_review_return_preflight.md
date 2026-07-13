# CAPE-KG Human Review Return Preflight

Generated: 2026-06-29T19:03:13.389417+00:00
Overall status: `pending_human_returns`

This preflight checks returned `.reviewed.jsonl` files before applying imports. It does not create paper-claimable human-gold metrics.

## Validation Policy

- Annotator file identity check: `True`
- Completed candidate coverage check: `True`
- Needs-adjudication comments required: `True`
- Completed adjudication adjudicator id required: `True`
- Mapping completed rows require explanation quality score: `True`
- Crosswalk completed rows require utility and explanation scores: `True`

## Return Scope

- Present human return files: 0
- Apply scope: `no_return_files`
- Minimum paper gate ready after preflight: `False`
- Optional mapping ready after preflight: `False`
- Optional crosswalk ready after preflight: `False`
- Optional active-effort ready after preflight: `False`

## Human Annotation Returns

- Expected reviewed files: 10
- Present reviewed files: 0
- Valid reviewed files: 0
- Completed chunks by annotator: `{'A': 0, 'B': 0}`
- Paired completed chunks: 0
- Ready for minimum import: `False`
- Errors / warnings: 0 / 0

## Adjudication Return

- Reviewed file present: `False`
- Reviewed rows: 0
- Completed adjudicated chunks: 0
- Ready for minimum adjudication import: `False`
- Errors / warnings: 0 / 0

## Mapping Return

- Reviewed file present: `False`
- Reviewed rows: 0
- Completed rows after merge: 0
- Complete Top-5 groups after merge: 0
- Ready for expert metric import: `False`
- Errors / warnings: 0 / 0

## Crosswalk Return

- Reviewed file present: `False`
- Reviewed rows: 0
- Completed rows after merge: 0
- Complete source groups after merge: 0
- Ready for crosswalk metric import: `False`
- Errors / warnings: 0 / 0

## Active-Review Human-Effort Return

- Reviewed CSV present: `False`
- Reviewed rows: 0
- Completed review rows: 0
- Timed review rows: 0
- Total review seconds: 0.0
- Ready for effort metric import: `False`
- Errors / warnings: 0 / 0

## Apply Command After Ready

```bash
PYTHON_BIN=python3 \
LLM_PYTHON=python3 \
APPLY_IMPORTS=1 \
bash scripts/run_cape_human_return_apply.sh
```

Low-level refresh script for debugging only: `scripts/run_cape_post_annotation_refresh.sh`.
