#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build strict-JSON diagnostics and rerun guidance for CAPE-KG LLM baselines."""

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_PYTHON = "/home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python"
DEFAULT_CHUNK_FILE = "01_data/evaluation_chunks.jsonl"

STRICT_JSON_CONTRACT = """
Strict JSON contract:
- Return exactly one JSON object and nothing else.
- The first non-whitespace character must be `{` and the last non-whitespace character must be `}`.
- Do not include markdown, code fences, comments, XML tags, `<think>` blocks, prose, or explanations.
- For Qwen/Qwen-style chat models, obey `/no_think`; do not emit hidden or visible reasoning.
- Output the JSON object immediately without a preamble.
- Use compact JSON without indentation or extra whitespace to reduce truncation risk.
- Use double-quoted JSON strings only.
- Use empty arrays for absent `nodes`, `edges`, `triples`, or `mappings` fields required by the requested shape.
""".strip()


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path):
    path = Path(path)
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path, rows, fieldnames):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def as_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def rate(numer, denom):
    denom = as_int(denom)
    if denom <= 0:
        return 0.0
    return round(as_int(numer) / denom, 6)


def condition_priority(exp_dir, condition, counts, python_bin, chunk_file):
    raw_rows = as_int(counts.get("max_raw_rows_single_run"))
    strict_errors = as_int(counts.get("parse_or_generation_error_rows_at_max_run"))
    repaired = as_int(counts.get("partial_json_repaired_rows_at_max_run"))
    unrepaired = as_int(counts.get("unrepaired_parse_or_generation_error_rows_at_max_run"))
    strict_rate = rate(strict_errors, raw_rows)
    repaired_rate = rate(repaired, raw_rows)
    unrepaired_rate = rate(unrepaired, raw_rows)

    if unrepaired_rate > 0.05:
        mitigation = "requires parser/prompt investigation before claim use"
    elif strict_rate > 0.5:
        mitigation = "strict-json-contract smoke rerun recommended"
    else:
        mitigation = "monitor only"

    command = (
        f"CUDA_VISIBLE_DEVICES=0 {python_bin} scripts/run_cape_llm_condition_baselines.py "
        f"--output-dir {exp_dir} "
        f"--chunk-file {chunk_file} "
        f"--conditions {condition} "
        f"--output-prefix qwen3_8b_strict_json_contract_smoke_{condition} "
        "--max-chunks 4 "
        "--max-new-tokens 1200 "
        "--max-prompt-chars 3600 "
        "--strict-json-contract"
    )

    return {
        "condition": condition,
        "max_raw_rows_single_run": raw_rows,
        "strict_error_rows": strict_errors,
        "strict_error_rate": strict_rate,
        "partial_json_repaired_rows": repaired,
        "partial_json_repaired_rate": repaired_rate,
        "unrepaired_error_rows": unrepaired,
        "unrepaired_error_rate": unrepaired_rate,
        "mitigation": mitigation,
        "recommended_smoke_command": command,
    }


def raw_run_prefix(raw_path):
    name = Path(raw_path).name
    if name.startswith("48_"):
        name = name[3:]
    if "_raw" in name:
        name = name.split("_raw", 1)[0]
    return name


def collect_strict_contract_runs(exp_dir, selected_prefixes=None):
    exp_dir = Path(exp_dir)
    selected_prefixes = set(selected_prefixes or [])
    runs = []
    for raw_path in sorted(exp_dir.glob("48_*_raw*.jsonl")):
        if "_raw.shard" in raw_path.name:
            combined_name = raw_path.name.split("_raw.shard", 1)[0] + "_raw.jsonl"
            if (exp_dir / combined_name).exists():
                continue
        run_prefix = raw_run_prefix(raw_path)
        rows = [row for row in read_jsonl(raw_path) if row.get("strict_json_contract")]
        if not rows:
            continue
        by_condition = {}
        for row in rows:
            condition = row.get("condition") or "unknown"
            item = by_condition.setdefault(
                condition,
                {
                    "raw_rows": 0,
                    "strict_error_rows": 0,
                    "partial_json_repaired_rows": 0,
                    "unrepaired_error_rows": 0,
                },
            )
            item["raw_rows"] += 1
            strict_error = bool(row.get("parse_error") or row.get("error"))
            if strict_error:
                item["strict_error_rows"] += 1
            if row.get("partial_json_repaired"):
                item["partial_json_repaired_rows"] += 1
            if strict_error and not row.get("partial_json_repaired"):
                item["unrepaired_error_rows"] += 1
        for item in by_condition.values():
            item["strict_error_rate"] = rate(item["strict_error_rows"], item["raw_rows"])
            item["partial_json_repaired_rate"] = rate(item["partial_json_repaired_rows"], item["raw_rows"])
            item["unrepaired_error_rate"] = rate(item["unrepaired_error_rows"], item["raw_rows"])
        valid_path = exp_dir / raw_path.name.replace("_raw", "_valid").replace("48_", "49_", 1)
        report_path = exp_dir / raw_path.name.replace("_raw", "_quality_report").replace(".jsonl", ".md").replace("48_", "50_", 1)
        runs.append(
            {
                "run_prefix": run_prefix,
                "gate_selected": run_prefix in selected_prefixes,
                "raw_file": str(raw_path),
                "valid_file": str(valid_path) if valid_path.exists() else None,
                "report_file": str(report_path) if report_path.exists() else None,
                "raw_rows": len(rows),
                "strict_error_rows": sum(item["strict_error_rows"] for item in by_condition.values()),
                "partial_json_repaired_rows": sum(item["partial_json_repaired_rows"] for item in by_condition.values()),
                "unrepaired_error_rows": sum(item["unrepaired_error_rows"] for item in by_condition.values()),
                "conditions": dict(sorted(by_condition.items())),
            }
        )
    return runs


def classify_strict_json_issue(row):
    raw_text = str(row.get("raw_text") or "")
    parse_error = str(row.get("parse_error") or row.get("error") or "")
    generation_error = str(row.get("generation_error") or "")
    stripped = raw_text.strip()
    if generation_error:
        return "generation_error"
    if not stripped:
        return "empty_output"
    if not stripped.startswith("{"):
        return "preamble_or_non_json_prefix"
    if not stripped.endswith("}"):
        return "truncated_or_non_json_suffix"
    if '"confidence": 00' in raw_text or ": 00." in raw_text:
        return "invalid_numeric_literal"
    if "Expecting ',' delimiter" in parse_error:
        return "malformed_json_delimiter"
    if "No JSON object found" in parse_error:
        return "no_json_object_found"
    return "json_parse_error"


def collect_strict_json_error_rows(exp_dir, selected_prefixes=None, selected_only=False):
    exp_dir = Path(exp_dir)
    selected_prefixes = set(selected_prefixes or [])
    rows = []
    for raw_path in sorted(exp_dir.glob("48_*_raw*.jsonl")):
        if "_raw.shard" in raw_path.name:
            combined_name = raw_path.name.split("_raw.shard", 1)[0] + "_raw.jsonl"
            if (exp_dir / combined_name).exists():
                continue
        run_prefix = raw_run_prefix(raw_path)
        gate_selected = run_prefix in selected_prefixes
        if selected_only and not gate_selected:
            continue
        for row in read_jsonl(raw_path):
            if not row.get("strict_json_contract"):
                continue
            strict_error = bool(row.get("parse_error") or row.get("error") or row.get("generation_error"))
            if not strict_error:
                continue
            raw_text = str(row.get("raw_text") or "")
            rows.append(
                {
                    "run_prefix": run_prefix,
                    "gate_selected": gate_selected,
                    "source_raw_file": str(raw_path),
                    "condition": row.get("condition", ""),
                    "chunk_id": row.get("chunk_id", ""),
                    "parse_error": row.get("parse_error") or row.get("error") or "",
                    "generation_error": row.get("generation_error") or "",
                    "partial_json_repaired": bool(row.get("partial_json_repaired")),
                    "issue_class": classify_strict_json_issue(row),
                    "raw_text_chars": len(raw_text),
                    "raw_text_starts_with_json": raw_text.lstrip().startswith("{"),
                    "raw_text_ends_with_json": raw_text.rstrip().endswith("}"),
                    "raw_text_preview": raw_text.replace("\n", " ")[:500],
                }
            )
    rows.sort(
        key=lambda row: (
            row["run_prefix"],
            row["source_raw_file"],
            row["condition"],
            row["chunk_id"],
        )
    )
    return rows


def build(exp_dir, python_bin, chunk_file):
    exp_dir = Path(exp_dir)
    release_dir = exp_dir / "06_release"
    review_dir = exp_dir / "05_review"
    prompt_dir = exp_dir / "02_schema/prompts"
    claim_gate = read_json(release_dir / "claim_gate_report.json", default={})
    condition_counts = claim_gate.get("condition_counts") or {}
    if not condition_counts:
        raise SystemExit(f"No condition_counts found in {release_dir / 'claim_gate_report.json'}")

    rows = [
        condition_priority(exp_dir, condition, counts, python_bin, chunk_file)
        for condition, counts in sorted(condition_counts.items())
        if as_int(counts.get("max_raw_rows_single_run")) > 0
    ]
    rows.sort(
        key=lambda row: (
            -float(row["strict_error_rate"]),
            -float(row["unrepaired_error_rate"]),
            row["condition"],
        )
    )
    for idx, row in enumerate(rows, start=1):
        row["priority_rank"] = idx

    strict_warn_gate = next(
        (gate for gate in claim_gate.get("gates", []) if gate.get("gate_id") == "llm.strict_json_rate"),
        {},
    )
    recovery_gate = next(
        (gate for gate in claim_gate.get("gates", []) if gate.get("gate_id") == "llm.revalidated_output_recovery"),
        {},
    )

    warning_rows = [row for row in rows if float(row["strict_error_rate"]) > 0.5]
    unrepaired_rows = [row for row in rows if float(row["unrepaired_error_rate"]) > 0.05]
    top_conditions = [row["condition"] for row in warning_rows[:6]]
    selected_prefixes = sorted(
        {
            counts.get("selected_max_run_prefix")
            for counts in condition_counts.values()
            if counts.get("selected_max_run_prefix")
        }
    )
    strict_contract_runs = collect_strict_contract_runs(exp_dir, selected_prefixes)
    gate_selected_strict_contract_runs = [run for run in strict_contract_runs if run.get("gate_selected")]
    gate_selected_strict_prefixes = sorted(
        {run["run_prefix"] for run in gate_selected_strict_contract_runs if run.get("run_prefix")}
    )
    error_rows = collect_strict_json_error_rows(exp_dir, selected_prefixes)
    gate_selected_error_rows = collect_strict_json_error_rows(exp_dir, selected_prefixes, selected_only=True)
    error_class_counts = {}
    for row in error_rows:
        error_class_counts[row["issue_class"]] = error_class_counts.get(row["issue_class"], 0) + 1
    gate_selected_error_class_counts = {}
    for row in gate_selected_error_rows:
        gate_selected_error_class_counts[row["issue_class"]] = gate_selected_error_class_counts.get(row["issue_class"], 0) + 1

    smoke_conditions = ",".join(top_conditions[:4]) if top_conditions else "B0_plain_llm,P_cape_kg_actual"
    combined_smoke_command = (
        f"CUDA_VISIBLE_DEVICES=0 {python_bin} scripts/run_cape_llm_condition_baselines.py "
        f"--output-dir {exp_dir} "
        f"--chunk-file {chunk_file} "
        f"--conditions {smoke_conditions} "
        "--output-prefix qwen3_8b_strict_json_contract_smoke "
        "--max-chunks 4 "
        "--max-new-tokens 1200 "
        "--max-prompt-chars 3600 "
        "--strict-json-contract"
    )

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "source_claim_gate_report": str(release_dir / "claim_gate_report.json"),
        "strict_json_gate_status": strict_warn_gate.get("status"),
        "strict_json_gate_evidence": strict_warn_gate.get("evidence"),
        "revalidated_output_recovery_status": recovery_gate.get("status"),
        "revalidated_output_recovery_evidence": recovery_gate.get("evidence"),
        "conditions_with_full_runs": len(rows),
        "conditions_over_strict_json_warning_threshold": len(warning_rows),
        "conditions_over_unrepaired_error_threshold": len(unrepaired_rows),
        "top_strict_json_reprompt_conditions": top_conditions,
        "strict_json_contract_prompt_file": str(prompt_dir / "strict_json_contract.txt"),
        "priority_queue_file": str(review_dir / "strict_json_reprompt_priority.csv"),
        "combined_smoke_command": combined_smoke_command,
        "gate_selected_run_prefixes": selected_prefixes,
        "gate_selected_strict_json_run_prefixes": gate_selected_strict_prefixes,
        "gate_selected_strict_json_contract_runs": gate_selected_strict_contract_runs,
        "gate_selected_strict_json_error_rows_file": str(review_dir / "strict_json_gate_selected_error_rows.csv"),
        "gate_selected_strict_json_error_row_count": len(gate_selected_error_rows),
        "gate_selected_strict_json_error_class_counts": dict(sorted(gate_selected_error_class_counts.items())),
        "strict_json_contract_runs": strict_contract_runs,
        "strict_json_error_rows_file": str(review_dir / "strict_json_error_rows.csv"),
        "strict_json_error_row_count": len(error_rows),
        "strict_json_error_class_counts": dict(sorted(error_class_counts.items())),
        "condition_rows": rows,
        "interpretation": (
            "Existing generated outputs are not changed by this diagnostic. High strict JSON error rates indicate "
            "that many rows required conservative partial-JSON recovery, while the unrepaired recovery gate tracks "
            "whether usable validated outputs remain after repair."
        ),
    }

    fieldnames = [
        "priority_rank",
        "condition",
        "max_raw_rows_single_run",
        "strict_error_rows",
        "strict_error_rate",
        "partial_json_repaired_rows",
        "partial_json_repaired_rate",
        "unrepaired_error_rows",
        "unrepaired_error_rate",
        "mitigation",
        "recommended_smoke_command",
    ]
    write_csv(review_dir / "strict_json_reprompt_priority.csv", rows, fieldnames)
    write_csv(
        review_dir / "strict_json_error_rows.csv",
        error_rows,
        [
            "run_prefix",
            "gate_selected",
            "source_raw_file",
            "condition",
            "chunk_id",
            "parse_error",
            "generation_error",
            "partial_json_repaired",
            "issue_class",
            "raw_text_chars",
            "raw_text_starts_with_json",
            "raw_text_ends_with_json",
            "raw_text_preview",
        ],
    )
    write_csv(
        review_dir / "strict_json_gate_selected_error_rows.csv",
        gate_selected_error_rows,
        [
            "run_prefix",
            "gate_selected",
            "source_raw_file",
            "condition",
            "chunk_id",
            "parse_error",
            "generation_error",
            "partial_json_repaired",
            "issue_class",
            "raw_text_chars",
            "raw_text_starts_with_json",
            "raw_text_ends_with_json",
            "raw_text_preview",
        ],
    )
    write_text(prompt_dir / "strict_json_contract.txt", STRICT_JSON_CONTRACT + "\n")
    write_json(release_dir / "strict_json_diagnostics.json", payload)
    write_text(release_dir / "strict_json_diagnostics.md", render_report(payload, rows, combined_smoke_command))
    return payload


def render_report(payload, rows, combined_smoke_command):
    lines = [
        "# Strict JSON Diagnostics",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Experiment: `{payload['experiment_dir']}`",
        f"Source claim gate: `{payload['source_claim_gate_report']}`",
        "",
        "## Status",
        "",
        f"- Strict JSON gate: {payload.get('strict_json_gate_status')}",
        f"- Recovery gate: {payload.get('revalidated_output_recovery_status')}",
        f"- Conditions with full/smoke rows: {payload.get('conditions_with_full_runs')}",
        f"- Conditions over strict JSON warning threshold: {payload.get('conditions_over_strict_json_warning_threshold')}",
        f"- Conditions over unrepaired error threshold: {payload.get('conditions_over_unrepaired_error_threshold')}",
        "",
        "Gate status is computed from the claim-gate-selected run for each condition. Historical strict-contract runs are retained separately for debugging and traceability.",
        "",
        "Existing generated outputs and metrics are not modified by this diagnostic. The strict rate counts rows that did not parse as a clean JSON object before conservative partial-JSON recovery.",
        "",
        "## Top Priority Conditions",
        "",
    ]
    for row in rows[:12]:
        lines.append(
            f"- {row['priority_rank']}. {row['condition']}: strict={row['strict_error_rate']}, "
            f"repaired={row['partial_json_repaired_rate']}, unrepaired={row['unrepaired_error_rate']} "
            f"({row['mitigation']})"
        )
    lines += [
        "",
        "## Strict Contract",
        "",
        f"Prompt contract file: `{payload['strict_json_contract_prompt_file']}`",
        "",
        "```text",
        STRICT_JSON_CONTRACT,
        "```",
        "",
        "## Smoke Rerun Template",
        "",
        "```bash",
        combined_smoke_command,
        "```",
        "",
        f"Priority CSV: `{payload['priority_queue_file']}`",
    ]
    if payload.get("strict_json_error_rows_file"):
        lines += [
            "",
            "## Gate-Selected Row-Level Errors",
            "",
            f"Selected strict JSON run prefixes: {', '.join(payload.get('gate_selected_strict_json_run_prefixes') or [])}",
            f"Gate-selected error row CSV: `{payload.get('gate_selected_strict_json_error_rows_file')}`",
            f"Gate-selected error rows: {payload.get('gate_selected_strict_json_error_row_count')}",
            "",
            "Gate-selected issue class counts:",
            "",
        ]
        for issue_class, count in (payload.get("gate_selected_strict_json_error_class_counts") or {}).items():
            lines.append(f"- {issue_class}: {count}")
        lines += [
            "",
            "## Historical Row-Level Error Worklist",
            "",
            f"Error row CSV: `{payload['strict_json_error_rows_file']}`",
            f"Error rows across all strict-contract runs: {payload.get('strict_json_error_row_count')}",
            "",
            "Issue class counts:",
            "",
        ]
        for issue_class, count in (payload.get("strict_json_error_class_counts") or {}).items():
            lines.append(f"- {issue_class}: {count}")
    strict_runs = payload.get("strict_json_contract_runs") or []
    if strict_runs:
        lines += [
            "",
            "## All Executed Strict-Contract Runs",
            "",
        ]
        for run in strict_runs:
            raw_rows = run.get("raw_rows") or 0
            strict_errors = run.get("strict_error_rows") or 0
            repaired = run.get("partial_json_repaired_rows") or 0
            unrepaired = run.get("unrepaired_error_rows") or 0
            selected_marker = " gate-selected" if run.get("gate_selected") else ""
            lines.append(
                f"- `{run.get('raw_file')}`{selected_marker}: raw_rows={raw_rows}, strict_error_rows={strict_errors}, "
                f"partial_json_repaired_rows={repaired}, unrepaired_error_rows={unrepaired}"
            )
            for condition, counts in sorted((run.get("conditions") or {}).items()):
                lines.append(
                    f"  - {condition}: raw_rows={counts.get('raw_rows')}, "
                    f"strict_error_rate={counts.get('strict_error_rate')}, "
                    f"repaired_rate={counts.get('partial_json_repaired_rate')}, "
                    f"unrepaired_rate={counts.get('unrepaired_error_rate')}"
                )
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--python-bin", default=DEFAULT_PYTHON)
    parser.add_argument("--chunk-file", default=DEFAULT_CHUNK_FILE)
    args = parser.parse_args()
    payload = build(args.experiment_dir, args.python_bin, args.chunk_file)
    print(
        json.dumps(
            {
                "event": "strict_json_diagnostics_written",
                "experiment_dir": payload["experiment_dir"],
                "conditions_over_strict_json_warning_threshold": payload["conditions_over_strict_json_warning_threshold"],
                "conditions_over_unrepaired_error_threshold": payload["conditions_over_unrepaired_error_threshold"],
                "report_file": str(Path(args.experiment_dir) / "06_release/strict_json_diagnostics.md"),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
