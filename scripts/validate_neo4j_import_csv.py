#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate Neo4j LOAD CSV export files for parser-risk patterns."""

import argparse
import base64
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


JSON_CARRIER_FIELDS = {
    "aliases_json",
    "evidence_anchor_ids_json",
    "source_triple_ids_json",
    "raw_json",
}

FORBIDDEN_LEGACY_REL_TYPES = {
    "PROCESSCONTEXT": "PROCESS_CONTEXT",
    "REQUIRESCAPABILITY": "REQUIRES_CAPABILITY",
    "CANDIDATEALIGNSWITH": "CANDIDATE_ALIGNS_WITH",
}


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def iter_csv_files(import_dir):
    import_dir = Path(import_dir)
    for path in sorted(import_dir.glob("*.csv")):
        yield path
    rel_dir = import_dir / "relationships"
    if rel_dir.exists():
        for path in sorted(rel_dir.glob("*.csv")):
            yield path


def decode_carrier(value):
    if not value:
        return None, None
    if not value.startswith("base64:"):
        return None, "not_base64_prefixed"
    try:
        raw = base64.urlsafe_b64decode(value[len("base64:") :].encode("ascii")).decode("utf-8")
        json.loads(raw)
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"
    return True, None


def validate_file(path):
    row_count = 0
    issue_counts = Counter()
    carrier_counts = Counter()
    carrier_errors = []
    parser_risk_samples = []
    fieldnames = []

    try:
        with Path(path).open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []
            for row_count, row in enumerate(reader, start=1):
                for field, value in row.items():
                    value = value or ""
                    if "\x00" in value:
                        issue_counts["nul_byte"] += 1
                    if '\\"' in value:
                        issue_counts["backslash_escaped_quote"] += 1
                        if len(parser_risk_samples) < 10:
                            parser_risk_samples.append(
                                {"row": row_count, "field": field, "sample": value[:240]}
                            )
                    if field in JSON_CARRIER_FIELDS and value:
                        carrier_counts[field] += 1
                        _, error = decode_carrier(value)
                        if error:
                            issue_counts[f"{field}.{error}"] += 1
                            if len(carrier_errors) < 10:
                                carrier_errors.append(
                                    {"row": row_count, "field": field, "error": error, "sample": value[:160]}
                                )
    except Exception as exc:
        issue_counts["csv_read_error"] += 1
        parser_risk_samples.append({"row": None, "field": None, "sample": f"{type(exc).__name__}: {exc}"})

    return {
        "file": str(path),
        "rows": row_count,
        "columns": fieldnames,
        "issue_counts": dict(issue_counts),
        "json_carrier_counts": dict(carrier_counts),
        "parser_risk_samples": parser_risk_samples,
        "carrier_errors": carrier_errors,
        "status": "PASS" if not issue_counts else "FAIL",
    }


def render_report(payload):
    lines = [
        "# Neo4j Import CSV Validation Report",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Import directory: `{payload['import_dir']}`",
        f"Overall status: **{payload['overall_status']}**",
        "",
        "## Summary",
        "",
        f"- CSV files: {payload['csv_file_count']}",
        f"- Total rows: {payload['total_rows']}",
        f"- Files with issues: {payload['files_with_issues']}",
        "",
        "## Files",
        "",
        "| file | rows | status | issues |",
        "|---|---:|---|---|",
    ]
    for item in payload["files"]:
        issues = ", ".join(f"{k}={v}" for k, v in sorted(item["issue_counts"].items())) or "-"
        lines.append(f"| `{item['file']}` | {item['rows']} | {item['status']} | {issues} |")
    if payload["issue_counts"]:
        lines += [
            "",
            "## Issue Counts",
            "",
        ]
        lines += [f"- {key}: {value}" for key, value in sorted(payload["issue_counts"].items())]
    if payload.get("relationship_type_issues"):
        lines += [
            "",
            "## Relationship Type Issues",
            "",
        ]
        for issue in payload["relationship_type_issues"]:
            lines.append(f"- `{issue['actual']}` should be `{issue['expected']}`")
    lines += [
        "",
        "## Notes",
        "",
        "- JSON carrier fields are expected to use `base64:<payload>` values.",
        "- `backslash_escaped_quote` should be zero for Neo4j Desktop compatibility.",
        "- Mapping relationship types should preserve CAPE schema underscores, e.g. `REQUIRES_CAPABILITY` and `PROCESS_CONTEXT`.",
    ]
    return "\n".join(lines) + "\n"


def run(args):
    import_dir = Path(args.import_dir)
    files = [validate_file(path) for path in iter_csv_files(import_dir)]
    issue_counts = Counter()
    for item in files:
        issue_counts.update(item["issue_counts"])
    manifest = read_json(import_dir / "manifest.json", {})
    relationship_types = set((manifest.get("relationship_types") or {}).keys())
    relationship_type_issues = []
    for actual, expected in sorted(FORBIDDEN_LEGACY_REL_TYPES.items()):
        if actual in relationship_types:
            issue_counts[f"legacy_relationship_type.{actual}"] += 1
            relationship_type_issues.append({"actual": actual, "expected": expected})
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "import_dir": str(import_dir),
        "manifest": manifest,
        "csv_file_count": len(files),
        "total_rows": sum(item["rows"] for item in files),
        "files_with_issues": sum(1 for item in files if item["issue_counts"]),
        "issue_counts": dict(issue_counts),
        "relationship_type_issues": relationship_type_issues,
        "files": files,
    }
    payload["overall_status"] = "PASS" if not issue_counts else "FAIL"
    write_json(args.output_json, payload)
    write_text(args.output_report, render_report(payload))
    print(json.dumps({
        "overall_status": payload["overall_status"],
        "csv_file_count": payload["csv_file_count"],
        "total_rows": payload["total_rows"],
        "files_with_issues": payload["files_with_issues"],
        "output_json": args.output_json,
        "output_report": args.output_report,
    }, ensure_ascii=False, indent=2))
    if args.fail_on_error and payload["overall_status"] != "PASS":
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--import-dir", default="outputs/11_neo4j_import_flat")
    parser.add_argument("--output-json", default="outputs/11_neo4j_import_flat/neo4j_csv_validation_report.json")
    parser.add_argument("--output-report", default="outputs/11_neo4j_import_flat/neo4j_csv_validation_report.md")
    parser.add_argument("--fail-on-error", action="store_true")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
