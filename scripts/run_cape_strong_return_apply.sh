#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON_BIN="${PYTHON_BIN:-python3}"
EXP_DIR="${EXP_DIR:-experiments/cape_kg_eacl_20260627}"
APPLY_IMPORTS="${APPLY_IMPORTS:-0}"
ALLOW_EMPTY_APPLY="${ALLOW_EMPTY_APPLY:-0}"
STARTED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

PREFLIGHT_JSON="$EXP_DIR/06_release/strong_review_return_preflight.json"
WRAPPER_SUMMARY_JSON="$EXP_DIR/06_release/strong_return_apply_last_run.json"
WRAPPER_SUMMARY_MD="$EXP_DIR/06_release/strong_return_apply_last_run.md"
WRAPPER_REFUSAL_JSON="$EXP_DIR/06_release/strong_return_apply_refusal_last_run.json"
WRAPPER_REFUSAL_MD="$EXP_DIR/06_release/strong_return_apply_refusal_last_run.md"

echo "CAPE-KG strong 300+ return apply wrapper started."
echo "EXP_DIR=$EXP_DIR"
echo "APPLY_IMPORTS=$APPLY_IMPORTS"

"$PYTHON_BIN" scripts/validate_cape_strong_review_returns.py --experiment-dir "$EXP_DIR"

strong_status="$("$PYTHON_BIN" - "$PREFLIGHT_JSON" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
summary = payload.get("summary") or {}
annotation = payload.get("annotation_returns") or {}
a = annotation.get("A") or {}
b = annotation.get("B") or {}
adjudication = payload.get("adjudication_return") or {}
present = int(bool(a.get("present"))) + int(bool(b.get("present"))) + int(bool(adjudication.get("present")))
if not present:
    apply_scope = "no_strong_return_files"
elif a.get("ready_for_strong_iaa") and b.get("ready_for_strong_iaa") and adjudication.get("ready_for_strong_adjudication_import"):
    apply_scope = "strong_annotation_and_adjudication_ready"
elif a.get("ready_for_strong_iaa") and b.get("ready_for_strong_iaa"):
    apply_scope = "strong_annotation_ready_adjudication_pending"
else:
    apply_scope = "partial_valid_strong_returns_only"
print(json.dumps(
    {
        "overall_status": payload.get("overall_status"),
        "package": payload.get("package"),
        "package_dir": payload.get("package_dir"),
        "present_strong_return_files": present,
        "apply_scope": apply_scope,
        "expected_review_units": summary.get("expected_review_units"),
        "paired_completed_chunks": summary.get("paired_completed_chunks"),
        "ready_for_strong_iaa": summary.get("ready_for_strong_iaa"),
        "ready_for_strong_claim_after_import": summary.get("ready_for_strong_claim_after_import"),
        "annotator_A_present": a.get("present"),
        "annotator_B_present": b.get("present"),
        "adjudication_present": adjudication.get("present"),
        "annotator_A_completed_chunks": a.get("completed_chunks"),
        "annotator_B_completed_chunks": b.get("completed_chunks"),
        "completed_adjudicated_chunks": adjudication.get("completed_adjudicated_chunks"),
        "error_count": summary.get("error_count"),
        "warning_count": summary.get("warning_count"),
    },
    ensure_ascii=False,
))
PY
)"

echo "Strong preflight summary: $strong_status"

if [[ "$APPLY_IMPORTS" == "1" ]]; then
  present_strong_return_files="$("$PYTHON_BIN" - "$strong_status" <<'PY'
import json
import sys
print(json.loads(sys.argv[1])["present_strong_return_files"])
PY
)"
  if [[ "$present_strong_return_files" == "0" && "$ALLOW_EMPTY_APPLY" != "1" ]]; then
    echo "Refusing APPLY_IMPORTS=1 because no reviewed strong 300+ return files are present."
    echo "Set ALLOW_EMPTY_APPLY=1 only if you intentionally want a no-op strong refresh."
    ENDED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    "$PYTHON_BIN" - "$WRAPPER_REFUSAL_JSON" "$WRAPPER_REFUSAL_MD" "$EXP_DIR" "$STARTED_AT" "$ENDED_AT" "$APPLY_IMPORTS" "$strong_status" <<'PY'
import json
import sys
from pathlib import Path

refusal_json = Path(sys.argv[1])
refusal_md = Path(sys.argv[2])
exp_dir = Path(sys.argv[3])
started_at = sys.argv[4]
ended_at = sys.argv[5]
apply_imports = sys.argv[6]
strong_status = json.loads(sys.argv[7])

payload = {
    "started_at_utc": started_at,
    "ended_at_utc": ended_at,
    "experiment_dir": str(exp_dir),
    "apply_imports": apply_imports,
    "wrapper_status": "refused_empty_apply_no_strong_reviewed_files",
    "exit_code": 3,
    "reason": "APPLY_IMPORTS=1 was requested, but no reviewed strong 300+ return files are present.",
    "preflight_overall_status": strong_status.get("overall_status"),
    "package": strong_status.get("package"),
    "package_dir": strong_status.get("package_dir"),
    "present_strong_return_files": strong_status.get("present_strong_return_files"),
    "apply_scope": strong_status.get("apply_scope"),
    "expected_review_units": strong_status.get("expected_review_units"),
    "paired_completed_chunks": strong_status.get("paired_completed_chunks"),
    "ready_for_strong_iaa": strong_status.get("ready_for_strong_iaa"),
    "ready_for_strong_claim_after_import": strong_status.get("ready_for_strong_claim_after_import"),
    "annotator_A_present": strong_status.get("annotator_A_present"),
    "annotator_B_present": strong_status.get("annotator_B_present"),
    "adjudication_present": strong_status.get("adjudication_present"),
}

refusal_json.parent.mkdir(parents=True, exist_ok=True)
refusal_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

lines = [
    "# CAPE-KG Strong 300+ Return Apply Refusal",
    "",
    f"Started: `{started_at}`",
    f"Ended: `{ended_at}`",
    f"Experiment: `{exp_dir}`",
    f"APPLY_IMPORTS: `{apply_imports}`",
    "",
    "## Status",
    "",
    f"- Wrapper status: `{payload['wrapper_status']}`",
    f"- Exit code: {payload['exit_code']}",
    f"- Reason: {payload['reason']}",
    f"- Return preflight: `{payload['preflight_overall_status']}`",
    f"- Present strong return files: {payload['present_strong_return_files']}",
    f"- Apply scope: `{payload['apply_scope']}`",
    f"- Ready for strong IAA: {payload['ready_for_strong_iaa']}",
    f"- Ready for strong claim after import: {payload['ready_for_strong_claim_after_import']}",
    "",
    "## Interpretation",
    "",
    "- This is an intentional safety refusal, not an experiment failure.",
    "- The wrapper prevents an accidental no-op strong apply run from being mistaken for imported 300+ human-gold evidence.",
    "- Add reviewed strong return files or set `ALLOW_EMPTY_APPLY=1` only for an explicitly intended no-op refresh.",
    "",
]
refusal_md.write_text("\n".join(lines), encoding="utf-8")
PY
    echo "Strong wrapper refusal summary: $WRAPPER_REFUSAL_MD"
    exit 3
  fi
fi

PACKAGE_DIR="$("$PYTHON_BIN" - "$strong_status" <<'PY'
import json
import sys
print(json.loads(sys.argv[1]).get("package_dir") or "")
PY
)"

run_import_if_present() {
  local target_file="$1"
  local reviewed_file="$2"
  local report_file="$3"
  if [[ ! -f "$reviewed_file" ]]; then
    echo "Skipping strong import; reviewed file not found: $reviewed_file"
    return 0
  fi
  local apply_args=()
  if [[ "$APPLY_IMPORTS" == "1" ]]; then
    apply_args+=(--apply)
  fi
  "$PYTHON_BIN" scripts/import_cape_gold_annotation.py \
    --experiment-dir "$EXP_DIR" \
    --target-file "$target_file" \
    --reviewed-file "$reviewed_file" \
    --report-file "$report_file" \
    --allow-partial \
    "${apply_args[@]}"
}

import_reports=()
if [[ -n "$PACKAGE_DIR" ]]; then
  run_import_if_present \
    "$PACKAGE_DIR/annotator_A.jsonl" \
    "$PACKAGE_DIR/annotator_A_edited.jsonl" \
    "$PACKAGE_DIR/annotator_A_import_report.json"
  import_reports+=("$PACKAGE_DIR/annotator_A_import_report.json")

  run_import_if_present \
    "$PACKAGE_DIR/annotator_B.jsonl" \
    "$PACKAGE_DIR/annotator_B_edited.jsonl" \
    "$PACKAGE_DIR/annotator_B_import_report.json"
  import_reports+=("$PACKAGE_DIR/annotator_B_import_report.json")

  if [[ "$APPLY_IMPORTS" == "1" && -f "$PACKAGE_DIR/annotator_A_edited.jsonl" && -f "$PACKAGE_DIR/annotator_B_edited.jsonl" ]]; then
    "$PYTHON_BIN" scripts/compute_cape_annotation_iaa.py \
      --annotator-a "$PACKAGE_DIR/annotator_A.jsonl" \
      --annotator-b "$PACKAGE_DIR/annotator_B.jsonl" \
      --output-dir "$PACKAGE_DIR/iaa_strong_resegmented"

    "$PYTHON_BIN" scripts/prepare_cape_adjudication_draft.py \
      --experiment-dir "$EXP_DIR" \
      --package "$(basename "$PACKAGE_DIR")"
  fi

  run_import_if_present \
    "$PACKAGE_DIR/adjudication.jsonl" \
    "$PACKAGE_DIR/adjudication_edited.jsonl" \
    "$PACKAGE_DIR/adjudication_import_report.json"
  import_reports+=("$PACKAGE_DIR/adjudication_import_report.json")
fi

"$PYTHON_BIN" scripts/validate_cape_strong_review_returns.py --experiment-dir "$EXP_DIR"

ENDED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

"$PYTHON_BIN" - "$WRAPPER_SUMMARY_JSON" "$WRAPPER_SUMMARY_MD" "$PREFLIGHT_JSON" "$EXP_DIR" "$STARTED_AT" "$ENDED_AT" "$APPLY_IMPORTS" "${import_reports[@]}" <<'PY'
import json
import sys
from pathlib import Path

summary_json = Path(sys.argv[1])
summary_md = Path(sys.argv[2])
preflight_json = Path(sys.argv[3])
exp_dir = Path(sys.argv[4])
started_at = sys.argv[5]
ended_at = sys.argv[6]
apply_imports = sys.argv[7]
import_reports = [str(Path(path)) for path in sys.argv[8:]]

preflight = json.loads(preflight_json.read_text(encoding="utf-8"))
summary = preflight.get("summary") or {}
annotation = preflight.get("annotation_returns") or {}
a = annotation.get("A") or {}
b = annotation.get("B") or {}
adjudication = preflight.get("adjudication_return") or {}
present = int(bool(a.get("present"))) + int(bool(b.get("present"))) + int(bool(adjudication.get("present")))
if not present:
    apply_scope = "no_strong_return_files"
elif a.get("ready_for_strong_iaa") and b.get("ready_for_strong_iaa") and adjudication.get("ready_for_strong_adjudication_import"):
    apply_scope = "strong_annotation_and_adjudication_ready"
elif a.get("ready_for_strong_iaa") and b.get("ready_for_strong_iaa"):
    apply_scope = "strong_annotation_ready_adjudication_pending"
else:
    apply_scope = "partial_valid_strong_returns_only"

payload = {
    "started_at_utc": started_at,
    "ended_at_utc": ended_at,
    "experiment_dir": str(exp_dir),
    "apply_imports": apply_imports,
    "wrapper_status": "completed",
    "exit_code": 0,
    "preflight_overall_status": preflight.get("overall_status"),
    "package": preflight.get("package"),
    "package_dir": preflight.get("package_dir"),
    "present_strong_return_files": present,
    "apply_scope": apply_scope,
    "expected_review_units": summary.get("expected_review_units"),
    "paired_completed_chunks": summary.get("paired_completed_chunks"),
    "ready_for_strong_iaa": summary.get("ready_for_strong_iaa"),
    "ready_for_strong_claim_after_import": summary.get("ready_for_strong_claim_after_import"),
    "annotator_A_present": a.get("present"),
    "annotator_B_present": b.get("present"),
    "adjudication_present": adjudication.get("present"),
    "annotator_A_completed_chunks": a.get("completed_chunks"),
    "annotator_B_completed_chunks": b.get("completed_chunks"),
    "completed_adjudicated_chunks": adjudication.get("completed_adjudicated_chunks"),
    "error_count": summary.get("error_count"),
    "warning_count": summary.get("warning_count"),
    "import_reports": [
        {"path": path, "exists": Path(path).exists()}
        for path in import_reports
    ],
    "claim_status": "strong_return_apply_success_not_paper_evidence_until_human_gold_scoring",
}

summary_json.parent.mkdir(parents=True, exist_ok=True)
summary_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

lines = [
    "# CAPE-KG Strong 300+ Return Apply Last Run",
    "",
    f"Started: `{started_at}`",
    f"Ended: `{ended_at}`",
    f"Experiment: `{exp_dir}`",
    f"APPLY_IMPORTS: `{apply_imports}`",
    "",
    "## Status",
    "",
    f"- Wrapper status: `{payload['wrapper_status']}`",
    f"- Exit code: {payload['exit_code']}",
    f"- Strong return preflight: `{payload['preflight_overall_status']}`",
    f"- Package: `{payload['package']}`",
    f"- Present strong return files: {payload['present_strong_return_files']}",
    f"- Apply scope: `{payload['apply_scope']}`",
    f"- Expected review units: {payload['expected_review_units']}",
    f"- Paired completed chunks: {payload['paired_completed_chunks']}",
    f"- Ready for strong IAA: {payload['ready_for_strong_iaa']}",
    f"- Ready for strong claim after import: {payload['ready_for_strong_claim_after_import']}",
    f"- Error count: {payload['error_count']}",
    f"- Warning count: {payload['warning_count']}",
    "",
    "## Import Reports",
    "",
]
for item in payload["import_reports"]:
    lines.append(f"- `{item['path']}`: exists={item['exists']}")
lines += [
    "",
    "## Interpretation",
    "",
    "- This wrapper only handles the optional strong 300+ resegmented package.",
    "- `APPLY_IMPORTS=0` validates and dry-runs any present import files without mutating the package targets.",
    "- `APPLY_IMPORTS=1` is refused when no reviewed strong return files are present unless `ALLOW_EMPTY_APPLY=1` is set.",
    "- Strong 300+ paper claims still require imported A/B annotations, IAA, adjudication, and human-gold scoring.",
    "",
]
summary_md.write_text("\n".join(lines), encoding="utf-8")
PY

echo "Strong return apply wrapper complete."
echo "Strong wrapper summary: $WRAPPER_SUMMARY_MD"
