# full_120_priority_batch_005 Human-Gold Annotation Batch

This directory contains partial annotation inputs for independent annotators A and B.
The files are not gold labels until reviewers edit them, import them, compute IAA, and adjudicate the final file.

## Files

- Annotator A input: `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/annotator_A_full_120_priority_batch_005.jsonl`
- Annotator B input: `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/annotator_B_full_120_priority_batch_005.jsonl`
- Tracking sheet: `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/batch_tracking_sheet.csv`

## Workflow

1. Open the static workbench:
   `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/annotation_workbench.html`
2. Load the annotator input JSONL for A or B.
3. Review each chunk using only the chunk text as authority.
4. Export the edited JSONL into this batch directory using the reviewed filename shown below.
5. Run the return preflight first after reviewed files are exported.
6. Use the human-return wrapper for dry-run/apply once the required return files are ready.
7. Use individual import commands only for debugging a specific batch file.

## Required Reviewed Filenames

### Annotator A

Save reviewed JSONL as: `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/annotator_A_full_120_priority_batch_005.reviewed.jsonl`

### Annotator B

Save reviewed JSONL as: `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/annotator_B_full_120_priority_batch_005.reviewed.jsonl`

## Recommended Return Preflight and Wrapper

Validate returned files without importing:

```bash
python3 scripts/validate_cape_human_review_returns.py --experiment-dir experiments/cape_kg_eacl_20260627
```

Dry-run the complete post-return refresh:

```bash
PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=0 bash scripts/run_cape_human_return_apply.sh
```

Apply returned files only after preflight passes and the reviewed files are present:

```bash
PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=1 bash scripts/run_cape_human_return_apply.sh
```

## Low-Level Debug Import Commands

The following commands validate a single reviewed batch file. Prefer the wrapper above for operational imports.

### Annotator A

Single-file dry run:

```bash
python3 scripts/import_cape_gold_annotation.py --experiment-dir experiments/cape_kg_eacl_20260627 --target-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/annotator_A.jsonl --reviewed-file experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/annotator_A_full_120_priority_batch_005.reviewed.jsonl --allow-partial
```

Single-file apply for debugging only:

```bash
python3 scripts/import_cape_gold_annotation.py --experiment-dir experiments/cape_kg_eacl_20260627 --target-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/annotator_A.jsonl --reviewed-file experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/annotator_A_full_120_priority_batch_005.reviewed.jsonl --allow-partial --apply
```

### Annotator B

Single-file dry run:

```bash
python3 scripts/import_cape_gold_annotation.py --experiment-dir experiments/cape_kg_eacl_20260627 --target-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/annotator_B.jsonl --reviewed-file experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/annotator_B_full_120_priority_batch_005.reviewed.jsonl --allow-partial
```

Single-file apply for debugging only:

```bash
python3 scripts/import_cape_gold_annotation.py --experiment-dir experiments/cape_kg_eacl_20260627 --target-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/annotator_B.jsonl --reviewed-file experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/annotator_B_full_120_priority_batch_005.reviewed.jsonl --allow-partial --apply
```

After both annotators are imported for enough chunks, recompute IAA and prepare adjudication drafts.
