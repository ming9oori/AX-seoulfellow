# CAPE-KG NCS-PCF Crosswalk Expert Review Protocol

This package reviews bridge-supported NCS-PCF crosswalk candidates. Each row
connects one Layer2 DomainTask to one NCS candidate and one PCF candidate.

## Decision Values

- `accepted`: the NCS-PCF pair is a defensible crosswalk for the shared Layer2 task.
- `rejected`: the pair is not a valid or useful crosswalk.
- `unsure`: the reviewer cannot decide from the available evidence.

## Utility Grade

- `0`: unrelated or misleading pair
- `1`: weakly related but not useful as a crosswalk
- `2`: useful/defensible crosswalk candidate
- `3`: strong crosswalk candidate

## Explanation Quality Score

- `1`: supporting reasons are misleading or not useful
- `2`: supporting reasons are weak
- `3`: supporting reasons are understandable but incomplete
- `4`: supporting reasons are mostly sufficient
- `5`: supporting reasons clearly justify the decision

Complete rows must include `expert_decision`, `utility_grade`,
`explanation_quality_score`, `review_status=completed`, `reviewer_id`, and a
short `comment`. Completed source-task groups become evaluable only when every
ranked candidate for that source task has been reviewed.

Expected return file:

```text
experiments/cape_kg_eacl_20260627/01_data/crosswalk_review/crosswalk_review_items.reviewed.jsonl
```

Validate/import:

```bash
python3 scripts/import_cape_crosswalk_review.py \
  --experiment-dir experiments/cape_kg_eacl_20260627 \
  --reviewed-file experiments/cape_kg_eacl_20260627/01_data/crosswalk_review/crosswalk_review_items.reviewed.jsonl
```

If the dry run passes, add `--apply`, then refresh the evaluation:

```bash
python3 scripts/evaluate_cape_crosswalk_review.py \
  --experiment-dir experiments/cape_kg_eacl_20260627
```
