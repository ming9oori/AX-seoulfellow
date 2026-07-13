#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON_BIN="${PYTHON_BIN:-python3}"
LLM_PYTHON="${LLM_PYTHON:-$PYTHON_BIN}"
EXP_DIR="${EXP_DIR:-experiments/cape_kg_eacl_20260627}"
OUTPUTS_DIR="${OUTPUTS_DIR:-outputs}"
PLAN_FILE="${PLAN_FILE:-AX_EACL_submission_review_revised_plan.md}"
APPLY_IMPORTS="${APPLY_IMPORTS:-0}"
ALLOW_EMPTY_APPLY="${ALLOW_EMPTY_APPLY:-0}"
STARTED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

PREFLIGHT_JSON="$EXP_DIR/06_release/human_review_return_preflight.json"
WRAPPER_SUMMARY_JSON="$EXP_DIR/06_release/human_return_apply_last_run.json"
WRAPPER_SUMMARY_MD="$EXP_DIR/06_release/human_return_apply_last_run.md"
WRAPPER_REFUSAL_JSON="$EXP_DIR/06_release/human_return_apply_refusal_last_run.json"
WRAPPER_REFUSAL_MD="$EXP_DIR/06_release/human_return_apply_refusal_last_run.md"
RELEASE_CHECKSUMS="$EXP_DIR/06_release/release_bundle_checksums.sha256"
HANDOFF_CHECKSUMS="$EXP_DIR/06_release/human_review_handoff/human_review_handoff_checksums.sha256"

echo "CAPE-KG human-return apply wrapper started."
echo "EXP_DIR=$EXP_DIR"
echo "APPLY_IMPORTS=$APPLY_IMPORTS"

"$PYTHON_BIN" scripts/validate_cape_human_review_returns.py --experiment-dir "$EXP_DIR"

preflight_status="$("$PYTHON_BIN" - "$PREFLIGHT_JSON" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
annotation = payload.get("annotation_returns") or {}
adjudication = payload.get("adjudication_return") or {}
mapping = payload.get("mapping_return") or {}
crosswalk = payload.get("crosswalk_return") or {}
active = payload.get("active_review_effort_return") or {}
present = int(annotation.get("present_files") or 0)
present += 1 if adjudication.get("present") else 0
present += 1 if mapping.get("present") else 0
present += 1 if crosswalk.get("present") else 0
present += 1 if active.get("present") else 0
minimum_ready = bool(annotation.get("ready_for_minimum_import") and adjudication.get("ready_for_minimum_adjudication_import"))
mapping_ready = bool(mapping.get("ready_for_expert_metric_import"))
crosswalk_ready = bool(crosswalk.get("ready_for_crosswalk_metric_import"))
active_ready = bool(active.get("ready_for_effort_metric_import"))
if not present:
    apply_scope = "no_return_files"
elif minimum_ready and mapping_ready and crosswalk_ready and active_ready:
    apply_scope = "all_minimum_and_optional_returns_ready"
elif minimum_ready:
    apply_scope = "minimum_annotation_adjudication_ready_optional_pending"
else:
    apply_scope = "partial_valid_returns_only"
if payload.get("present_human_return_files") is not None:
    present = int(payload.get("present_human_return_files") or 0)
if payload.get("apply_scope"):
    apply_scope = payload.get("apply_scope")
if payload.get("minimum_paper_gate_ready_after_preflight") is not None:
    minimum_ready = bool(payload.get("minimum_paper_gate_ready_after_preflight"))
if payload.get("optional_mapping_ready_after_preflight") is not None:
    mapping_ready = bool(payload.get("optional_mapping_ready_after_preflight"))
if payload.get("optional_crosswalk_ready_after_preflight") is not None:
    crosswalk_ready = bool(payload.get("optional_crosswalk_ready_after_preflight"))
if payload.get("optional_active_effort_ready_after_preflight") is not None:
    active_ready = bool(payload.get("optional_active_effort_ready_after_preflight"))
print(json.dumps(
    {
        "overall_status": payload.get("overall_status"),
        "present_human_return_files": present,
        "apply_scope": apply_scope,
        "minimum_paper_gate_ready_after_preflight": minimum_ready,
        "optional_mapping_ready_after_preflight": mapping_ready,
        "optional_crosswalk_ready_after_preflight": crosswalk_ready,
        "optional_active_effort_ready_after_preflight": active_ready,
        "annotation_present_files": annotation.get("present_files"),
        "annotation_ready_for_minimum_import": annotation.get("ready_for_minimum_import"),
        "adjudication_present": adjudication.get("present"),
        "adjudication_ready_for_minimum_import": adjudication.get("ready_for_minimum_adjudication_import"),
        "mapping_present": mapping.get("present"),
        "mapping_ready_for_expert_metric_import": mapping.get("ready_for_expert_metric_import"),
        "crosswalk_present": crosswalk.get("present"),
        "crosswalk_ready_for_expert_metric_import": crosswalk.get("ready_for_crosswalk_metric_import"),
        "active_effort_present": active.get("present"),
        "active_effort_ready_for_metric_import": active.get("ready_for_effort_metric_import"),
    },
    ensure_ascii=False,
))
PY
)"

echo "Preflight summary: $preflight_status"

if [[ "$APPLY_IMPORTS" == "1" ]]; then
  present_human_return_files="$("$PYTHON_BIN" - "$preflight_status" <<'PY'
import json
import sys
print(json.loads(sys.argv[1])["present_human_return_files"])
PY
)"
  if [[ "$present_human_return_files" == "0" && "$ALLOW_EMPTY_APPLY" != "1" ]]; then
    echo "Refusing APPLY_IMPORTS=1 because no reviewed human-return files are present."
    echo "Set ALLOW_EMPTY_APPLY=1 only if you intentionally want a no-op apply refresh."
    ENDED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    "$PYTHON_BIN" - "$WRAPPER_SUMMARY_JSON" "$WRAPPER_SUMMARY_MD" "$WRAPPER_REFUSAL_JSON" "$WRAPPER_REFUSAL_MD" "$EXP_DIR" "$STARTED_AT" "$ENDED_AT" "$APPLY_IMPORTS" "$preflight_status" <<'PY'
import json
import sys
from pathlib import Path

summary_json = Path(sys.argv[1])
summary_md = Path(sys.argv[2])
refusal_json = Path(sys.argv[3])
refusal_md = Path(sys.argv[4])
exp_dir = Path(sys.argv[5])
started_at = sys.argv[6]
ended_at = sys.argv[7]
apply_imports = sys.argv[8]
preflight_status = json.loads(sys.argv[9])

payload = {
    "started_at_utc": started_at,
    "ended_at_utc": ended_at,
    "experiment_dir": str(exp_dir),
    "apply_imports": apply_imports,
    "wrapper_status": "refused_empty_apply_no_reviewed_files",
    "exit_code": 3,
    "reason": "APPLY_IMPORTS=1 was requested, but no reviewed human-return files are present.",
    "preflight_overall_status": preflight_status.get("overall_status"),
    "present_human_return_files": preflight_status.get("present_human_return_files"),
    "apply_scope": preflight_status.get("apply_scope"),
    "minimum_paper_gate_ready_after_preflight": preflight_status.get("minimum_paper_gate_ready_after_preflight"),
    "optional_mapping_ready_after_preflight": preflight_status.get("optional_mapping_ready_after_preflight"),
    "optional_crosswalk_ready_after_preflight": preflight_status.get("optional_crosswalk_ready_after_preflight"),
    "optional_active_effort_ready_after_preflight": preflight_status.get("optional_active_effort_ready_after_preflight"),
    "annotation_present_files": preflight_status.get("annotation_present_files"),
    "annotation_ready_for_minimum_import": preflight_status.get("annotation_ready_for_minimum_import"),
    "adjudication_present": preflight_status.get("adjudication_present"),
    "adjudication_ready_for_minimum_import": preflight_status.get("adjudication_ready_for_minimum_import"),
    "mapping_present": preflight_status.get("mapping_present"),
    "mapping_ready_for_expert_metric_import": preflight_status.get("mapping_ready_for_expert_metric_import"),
    "crosswalk_present": preflight_status.get("crosswalk_present"),
    "crosswalk_ready_for_expert_metric_import": preflight_status.get("crosswalk_ready_for_expert_metric_import"),
    "active_effort_present": preflight_status.get("active_effort_present"),
    "active_effort_ready_for_metric_import": preflight_status.get("active_effort_ready_for_metric_import"),
    "release_checksum_status": "not_checked_refused_before_refresh",
    "handoff_checksum_status": "not_checked_refused_before_refresh",
}

refusal_json.parent.mkdir(parents=True, exist_ok=True)
refusal_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

lines = [
    "# CAPE-KG Human Return Apply Refusal",
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
    f"- Present human return files: {payload['present_human_return_files']}",
    f"- Apply scope: `{payload['apply_scope']}`",
    f"- Minimum paper gate ready after preflight: {payload['minimum_paper_gate_ready_after_preflight']}",
    f"- Optional mapping ready after preflight: {payload['optional_mapping_ready_after_preflight']}",
    f"- Optional crosswalk ready after preflight: {payload['optional_crosswalk_ready_after_preflight']}",
    f"- Optional active-effort ready after preflight: {payload['optional_active_effort_ready_after_preflight']}",
    f"- Annotation present files: {payload['annotation_present_files']}",
    f"- Annotation ready for minimum import: {payload['annotation_ready_for_minimum_import']}",
    f"- Adjudication present: {payload['adjudication_present']}",
    f"- Mapping present: {payload['mapping_present']}",
    f"- Crosswalk present: {payload['crosswalk_present']}",
    f"- Active-review effort present: {payload['active_effort_present']}",
    "",
    "## Interpretation",
    "",
    "- This is an intentional safety refusal, not an experiment failure.",
    "- The wrapper prevents an accidental no-op apply run from being mistaken for imported human-gold evidence.",
    "- Add reviewed return files or set `ALLOW_EMPTY_APPLY=1` only for an explicitly intended no-op refresh.",
    "",
]
refusal_md.write_text("\n".join(lines), encoding="utf-8")
PY
    echo "Wrapper refusal summary: $WRAPPER_REFUSAL_MD"
    exit 3
  fi
fi

PYTHON_BIN="$PYTHON_BIN" \
LLM_PYTHON="$LLM_PYTHON" \
EXP_DIR="$EXP_DIR" \
OUTPUTS_DIR="$OUTPUTS_DIR" \
PLAN_FILE="$PLAN_FILE" \
APPLY_IMPORTS="$APPLY_IMPORTS" \
bash scripts/run_cape_post_annotation_refresh.sh

"$PYTHON_BIN" scripts/validate_cape_pre_human_handoff.py \
  --experiment-dir "$EXP_DIR" \
  --outputs-dir "$OUTPUTS_DIR"

release_checksum_status="not_checked"
handoff_checksum_status="not_checked"
if [[ -f "$RELEASE_CHECKSUMS" ]]; then
  sha256sum -c "$RELEASE_CHECKSUMS"
  release_checksum_status="OK"
fi
if [[ -f "$HANDOFF_CHECKSUMS" ]]; then
  sha256sum -c "$HANDOFF_CHECKSUMS"
  handoff_checksum_status="OK"
fi

ENDED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

"$PYTHON_BIN" - "$WRAPPER_SUMMARY_JSON" "$WRAPPER_SUMMARY_MD" "$PREFLIGHT_JSON" "$EXP_DIR" "$STARTED_AT" "$ENDED_AT" "$APPLY_IMPORTS" "$release_checksum_status" "$handoff_checksum_status" <<'PY'
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
release_checksum_status = sys.argv[8]
handoff_checksum_status = sys.argv[9]


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


preflight = read_json(preflight_json, {}) or {}
refresh = read_json(exp_dir / "06_release/post_annotation_refresh_last_run.json", {}) or {}
claim_gate = read_json(exp_dir / "06_release/claim_gate_report.json", {}) or {}
pre_human = read_json(exp_dir / "06_release/pre_human_handoff_validation.json", {}) or {}
completion = read_json(exp_dir / "06_release/submission_completion_audit_ko.json", {}) or {}
annotation = preflight.get("annotation_returns") or {}
adjudication = preflight.get("adjudication_return") or {}
mapping = preflight.get("mapping_return") or {}
crosswalk = preflight.get("crosswalk_return") or {}
active = preflight.get("active_review_effort_return") or {}

present = int(annotation.get("present_files") or 0)
present += 1 if adjudication.get("present") else 0
present += 1 if mapping.get("present") else 0
present += 1 if crosswalk.get("present") else 0
present += 1 if active.get("present") else 0
minimum_ready = bool(annotation.get("ready_for_minimum_import") and adjudication.get("ready_for_minimum_adjudication_import"))
mapping_ready = bool(mapping.get("ready_for_expert_metric_import"))
crosswalk_ready = bool(crosswalk.get("ready_for_crosswalk_metric_import"))
active_ready = bool(active.get("ready_for_effort_metric_import"))
if not present:
    apply_scope = "no_return_files"
elif minimum_ready and mapping_ready and crosswalk_ready and active_ready:
    apply_scope = "all_minimum_and_optional_returns_ready"
elif minimum_ready:
    apply_scope = "minimum_annotation_adjudication_ready_optional_pending"
else:
    apply_scope = "partial_valid_returns_only"
if preflight.get("present_human_return_files") is not None:
    present = int(preflight.get("present_human_return_files") or 0)
if preflight.get("apply_scope"):
    apply_scope = preflight.get("apply_scope")
if preflight.get("minimum_paper_gate_ready_after_preflight") is not None:
    minimum_ready = bool(preflight.get("minimum_paper_gate_ready_after_preflight"))
if preflight.get("optional_mapping_ready_after_preflight") is not None:
    mapping_ready = bool(preflight.get("optional_mapping_ready_after_preflight"))
if preflight.get("optional_crosswalk_ready_after_preflight") is not None:
    crosswalk_ready = bool(preflight.get("optional_crosswalk_ready_after_preflight"))
if preflight.get("optional_active_effort_ready_after_preflight") is not None:
    active_ready = bool(preflight.get("optional_active_effort_ready_after_preflight"))

payload = {
    "started_at_utc": started_at,
    "ended_at_utc": ended_at,
    "experiment_dir": str(exp_dir),
    "apply_imports": apply_imports,
    "wrapper_status": "completed",
    "exit_code": 0,
    "preflight_overall_status": preflight.get("overall_status"),
    "present_human_return_files": present,
    "apply_scope": apply_scope,
    "minimum_paper_gate_ready_after_preflight": minimum_ready,
    "optional_mapping_ready_after_preflight": mapping_ready,
    "optional_crosswalk_ready_after_preflight": crosswalk_ready,
    "optional_active_effort_ready_after_preflight": active_ready,
    "annotation_present_files": annotation.get("present_files"),
    "annotation_valid_files": annotation.get("valid_files"),
    "annotation_paired_completed_chunks": annotation.get("paired_completed_chunks"),
    "adjudication_present": adjudication.get("present"),
    "adjudication_completed_chunks": adjudication.get("completed_adjudicated_chunks"),
    "mapping_present": mapping.get("present"),
    "mapping_complete_top5_groups": mapping.get("complete_top5_groups"),
    "crosswalk_present": crosswalk.get("present"),
    "crosswalk_complete_source_groups": crosswalk.get("complete_source_groups"),
    "active_review_effort_present": active.get("present"),
    "active_review_timed_rows": active.get("timed_review_rows"),
    "post_refresh_claim_status": refresh.get("claim_status"),
    "claim_gate_overall_status": claim_gate.get("overall_status"),
    "claim_gate_required_failures": claim_gate.get("required_failure_count"),
    "claim_gate_optional_failures": claim_gate.get("optional_failure_count"),
    "pre_human_handoff_status": pre_human.get("overall_status"),
    "pre_human_status_counts": pre_human.get("status_counts"),
    "completion_status": completion.get("overall_completion_status"),
    "release_checksum_status": release_checksum_status,
    "handoff_checksum_status": handoff_checksum_status,
}

summary_json.parent.mkdir(parents=True, exist_ok=True)
summary_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

lines = [
    "# CAPE-KG Human Return Apply Last Run",
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
    f"- Return preflight: `{payload['preflight_overall_status']}`",
    f"- Present human return files: {payload['present_human_return_files']}",
    f"- Apply scope: `{payload['apply_scope']}`",
    f"- Minimum paper gate ready after preflight: {payload['minimum_paper_gate_ready_after_preflight']}",
    f"- Optional mapping ready after preflight: {payload['optional_mapping_ready_after_preflight']}",
    f"- Optional crosswalk ready after preflight: {payload['optional_crosswalk_ready_after_preflight']}",
    f"- Optional active-effort ready after preflight: {payload['optional_active_effort_ready_after_preflight']}",
    f"- Annotation valid files: {payload['annotation_valid_files']}",
    f"- Paired completed annotation chunks: {payload['annotation_paired_completed_chunks']}",
    f"- Adjudication completed chunks: {payload['adjudication_completed_chunks']}",
    f"- Mapping complete Top-5 groups: {payload['mapping_complete_top5_groups']}",
    f"- Crosswalk complete source groups: {payload['crosswalk_complete_source_groups']}",
    f"- Active-review timed rows: {payload['active_review_timed_rows']}",
    f"- Post-refresh claim status: `{payload['post_refresh_claim_status']}`",
    f"- Claim gate: `{payload['claim_gate_overall_status']}`",
    f"- Required claim-gate failures: {payload['claim_gate_required_failures']}",
    f"- Optional claim-gate failures: {payload['claim_gate_optional_failures']}",
    f"- Pre-human handoff validation: `{payload['pre_human_handoff_status']}`; source `{exp_dir / '06_release/pre_human_handoff_validation.md'}`",
    f"- Completion status: `{payload['completion_status']}`",
    f"- Release checksum status: `{payload['release_checksum_status']}`",
    f"- Handoff checksum status: `{payload['handoff_checksum_status']}`",
    "",
    "## Interpretation",
    "",
    "- This wrapper validates returned human-review files before running the post-annotation refresh.",
    "- `APPLY_IMPORTS=0` is a dry-run path; `APPLY_IMPORTS=1` applies validated reviewed files.",
    "- Partial validated returns may be applied incrementally, but only `minimum_annotation_adjudication_ready_optional_pending` or `all_minimum_and_optional_returns_ready` can unlock minimum paper-claim scoring.",
    "- If no reviewed return files are present, `APPLY_IMPORTS=1` is refused unless `ALLOW_EMPTY_APPLY=1` is set.",
    "",
]
summary_md.write_text("\n".join(lines), encoding="utf-8")
PY

echo "Human-return apply wrapper complete."
echo "Wrapper summary: $WRAPPER_SUMMARY_MD"
