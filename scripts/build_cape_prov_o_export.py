#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Export CAPE-KG file/run provenance as a compact PROV-O Turtle graph."""

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_OUTPUTS_DIR = Path("outputs")


FILE_GROUPS = [
    "source_files",
    "prompt_and_schema_files",
    "evaluation_files",
    "human_review_files",
    "release_files",
]


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


def read_csv(path):
    path = Path(path)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def sha256_file(path):
    path = Path(path)
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def short_hash(value, length=16):
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:length]


def rel(path):
    return str(Path(path).as_posix())


def ttl_string(value):
    text = "" if value is None else str(value)
    text = text.replace("\\", "\\\\").replace('"', '\\"')
    text = text.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
    return f'"{text}"'


def ttl_int(value):
    try:
        value = int(value)
    except Exception:
        value = 0
    return f'"{value}"^^xsd:integer'


def ttl_bool(value):
    return f'"{str(bool(value)).lower()}"^^xsd:boolean'


def ttl_datetime(value):
    return f"{ttl_string(value)}^^xsd:dateTime"


def file_uri(path):
    return f"cape:file_{short_hash(path)}"


def activity_uri(value):
    return f"cape:activity_{short_hash(value)}"


def model_uri(value):
    return f"cape:model_{short_hash(value)}"


def safe_json_loads(value, default=None):
    if default is None:
        default = {}
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def model_label(model_path):
    text = str(model_path)
    marker = "models--"
    if marker in text:
        tail = text.split(marker, 1)[1].split("/snapshots/", 1)[0]
        return tail.replace("--", "/")
    return Path(text).name or text


def emit_block(lines, subject, predicates):
    predicates = [(pred, obj) for pred, obj in predicates if obj not in {None, ""}]
    if not predicates:
        return 0
    lines.append(subject)
    for index, (pred, obj) in enumerate(predicates):
        ending = " ." if index == len(predicates) - 1 else " ;"
        lines.append(f"  {pred} {obj}{ending}")
    lines.append("")
    return len(predicates)


def count_records(path):
    path = Path(path)
    if not path.exists() or not path.is_file():
        return ""
    if path.suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            return max(0, sum(1 for _ in f) - 1)
    if path.suffix == ".jsonl":
        with path.open("r", encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())
    return ""


def build_file_record(path, group, role="", required=False, exists=None, bytes_value=None, sha256="", records=""):
    path = str(path)
    path_obj = Path(path)
    if exists is None:
        exists = path_obj.exists() and path_obj.is_file()
    if bytes_value is None:
        bytes_value = path_obj.stat().st_size if exists else 0
    if not sha256 and exists:
        sha256 = sha256_file(path_obj)
    if records == "" and exists:
        records = count_records(path_obj)
    return {
        "path": path,
        "group": group,
        "role": role,
        "required": bool(required),
        "exists": bool(exists),
        "bytes": int(bytes_value or 0),
        "sha256": sha256,
        "records": records,
        "uri": file_uri(path),
    }


def add_file_record(file_records, record):
    path = record["path"]
    current = file_records.get(path)
    if not current:
        file_records[path] = record
        return
    if record.get("role") and record["role"] not in current.get("role", ""):
        current["role"] = ",".join(filter(None, [current.get("role"), record["role"]]))
    if record.get("group") and record["group"] not in current.get("group", ""):
        current["group"] = ",".join(filter(None, [current.get("group"), record["group"]]))
    current["required"] = bool(current.get("required") or record.get("required"))
    current["exists"] = bool(current.get("exists") or record.get("exists"))
    current["bytes"] = current.get("bytes") or record.get("bytes") or 0
    current["sha256"] = current.get("sha256") or record.get("sha256") or ""
    current["records"] = current.get("records") if current.get("records") != "" else record.get("records", "")


def collect_file_records(manifest, llm_runs):
    file_records = {}
    for group in FILE_GROUPS:
        for row in manifest.get(group, []):
            add_file_record(
                file_records,
                build_file_record(
                    row.get("path", ""),
                    group=group,
                    role=row.get("role", ""),
                    required=row.get("required", False),
                    exists=row.get("exists", False),
                    bytes_value=row.get("bytes", 0),
                    sha256=row.get("sha256", ""),
                    records=row.get("records", ""),
                ),
            )
    for row in llm_runs:
        if row.get("raw_file"):
            add_file_record(
                file_records,
                build_file_record(
                    row["raw_file"],
                    group="llm_run_files",
                    role="llm_raw_output",
                    required=True,
                    sha256=row.get("raw_sha256", ""),
                    records=row.get("raw_rows", ""),
                ),
            )
        if row.get("valid_file"):
            add_file_record(
                file_records,
                build_file_record(
                    row["valid_file"],
                    group="llm_run_files",
                    role="llm_validated_output",
                    required=True,
                    sha256=row.get("valid_sha256", ""),
                    records=row.get("valid_rows", ""),
                ),
            )
        if row.get("quality_report"):
            add_file_record(
                file_records,
                build_file_record(
                    row["quality_report"],
                    group="llm_run_files",
                    role="llm_quality_report",
                    required=False,
                ),
            )
    return file_records


def run_time_predicates(row):
    predicates = []
    if row.get("first_generated_at_utc"):
        predicates.append(("prov:startedAtTime", ttl_datetime(row["first_generated_at_utc"])))
    if row.get("last_generated_at_utc"):
        predicates.append(("prov:endedAtTime", ttl_datetime(row["last_generated_at_utc"])))
    return predicates


def build_turtle(manifest, llm_runs, file_records, output_paths):
    lines = [
        "@prefix prov: <http://www.w3.org/ns/prov#> .",
        "@prefix dcterms: <http://purl.org/dc/terms/> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .",
        "@prefix cape: <https://example.org/cape-kg#> .",
        "",
    ]
    triple_count = 0
    entity_uris = set()
    activity_uris = set()
    agent_uris = set()

    agent_uris.add("cape:pipeline_agent")
    triple_count += emit_block(
        lines,
        "cape:pipeline_agent",
        [
            ("a", "prov:SoftwareAgent"),
            ("rdfs:label", ttl_string("CAPE-KG executable pipeline")),
        ],
    )
    agent_uris.add("cape:human_review_process")
    triple_count += emit_block(
        lines,
        "cape:human_review_process",
        [
            ("a", "prov:Agent"),
            ("rdfs:label", ttl_string("CAPE-KG human review process")),
        ],
    )

    model_agents = {}
    for row in llm_runs:
        for model_path in safe_json_loads(row.get("models"), {}).keys():
            uri = model_uri(model_path)
            model_agents[model_path] = uri
            agent_uris.add(uri)
    for model_path, uri in sorted(model_agents.items(), key=lambda item: item[1]):
        triple_count += emit_block(
            lines,
            uri,
            [
                ("a", "prov:SoftwareAgent"),
                ("rdfs:label", ttl_string(model_label(model_path))),
                ("cape:modelPath", ttl_string(model_path)),
            ],
        )

    experiment_activity = "cape:experiment_activity"
    activity_uris.add(experiment_activity)
    experiment_predicates = [
        ("a", "prov:Activity"),
        ("rdfs:label", ttl_string("CAPE-KG pre-human experiment package")),
        ("dcterms:created", ttl_datetime(manifest.get("generated_at_utc", ""))),
        ("cape:experimentDir", ttl_string(manifest.get("experiment_dir", ""))),
        ("cape:outputsDir", ttl_string(manifest.get("outputs_dir", ""))),
        ("cape:claimStatus", ttl_string(manifest.get("claim_status", ""))),
        ("prov:wasAssociatedWith", "cape:pipeline_agent"),
    ]
    for group in ["source_files", "prompt_and_schema_files"]:
        for row in manifest.get(group, []):
            if row.get("path") in file_records:
                experiment_predicates.append(("prov:used", file_records[row["path"]]["uri"]))
    triple_count += emit_block(lines, experiment_activity, experiment_predicates)

    for record in sorted(file_records.values(), key=lambda item: item["path"]):
        entity_uris.add(record["uri"])
        predicates = [
            ("a", "prov:Entity"),
            ("rdfs:label", ttl_string(Path(record["path"]).name)),
            ("cape:path", ttl_string(record["path"])),
            ("cape:fileGroup", ttl_string(record.get("group", ""))),
            ("cape:fileRole", ttl_string(record.get("role", ""))),
            ("cape:required", ttl_bool(record.get("required"))),
            ("cape:exists", ttl_bool(record.get("exists"))),
            ("cape:byteSize", ttl_int(record.get("bytes", 0))),
            ("cape:sha256", ttl_string(record.get("sha256", ""))),
            ("prov:wasAttributedTo", "cape:pipeline_agent"),
        ]
        if record.get("records") != "":
            predicates.append(("cape:recordCount", ttl_int(record.get("records"))))
        triple_count += emit_block(lines, record["uri"], predicates)

    for row in llm_runs:
        uri = activity_uri(f"llm::{row.get('logical_run')}")
        activity_uris.add(uri)
        predicates = [
            ("a", "prov:Activity"),
            ("a", "cape:LLMExtractionRun"),
            ("rdfs:label", ttl_string(row.get("logical_run", ""))),
            ("prov:wasAssociatedWith", "cape:pipeline_agent"),
            ("cape:logicalRun", ttl_string(row.get("logical_run", ""))),
            ("cape:rawRows", ttl_int(row.get("raw_rows", 0))),
            ("cape:validRows", ttl_int(row.get("valid_rows", 0))),
            ("cape:parseErrorRows", ttl_int(row.get("parse_error_rows", 0))),
            ("cape:repairedRows", ttl_int(row.get("repaired_rows", 0))),
            ("cape:conditionsJson", ttl_string(row.get("conditions", ""))),
            ("cape:modelsJson", ttl_string(row.get("models", ""))),
        ]
        predicates.extend(run_time_predicates(row))
        for model_path in safe_json_loads(row.get("models"), {}).keys():
            predicates.append(("prov:wasAssociatedWith", model_agents[model_path]))
        for key in ["raw_file", "valid_file", "quality_report"]:
            if row.get(key) and row[key] in file_records:
                predicates.append(("prov:generated", file_records[row[key]]["uri"]))
        triple_count += emit_block(lines, uri, predicates)

    handoff_activity = "cape:human_review_handoff_activity"
    activity_uris.add(handoff_activity)
    handoff_predicates = [
        ("a", "prov:Activity"),
        ("rdfs:label", ttl_string("CAPE-KG human review handoff preparation")),
        ("prov:wasAssociatedWith", "cape:human_review_process"),
        ("cape:claimStatus", ttl_string("handoff_ready_pending_human_review")),
    ]
    for row in manifest.get("human_review_files", []):
        if row.get("path") in file_records:
            handoff_predicates.append(("prov:generated", file_records[row["path"]]["uri"]))
    triple_count += emit_block(lines, handoff_activity, handoff_predicates)

    release_activity = "cape:release_bundle_activity"
    activity_uris.add(release_activity)
    release_predicates = [
        ("a", "prov:Activity"),
        ("rdfs:label", ttl_string("CAPE-KG release and reproducibility bundle preparation")),
        ("prov:wasAssociatedWith", "cape:pipeline_agent"),
        ("cape:claimStatus", ttl_string("release_bundles_ready_not_submission_complete")),
    ]
    for row in manifest.get("release_files", []):
        if row.get("path") in file_records:
            release_predicates.append(("prov:generated", file_records[row["path"]]["uri"]))
    triple_count += emit_block(lines, release_activity, release_predicates)

    ttl_entity = file_uri(output_paths["ttl"])
    entity_uris.add(ttl_entity)
    triple_count += emit_block(
        lines,
        ttl_entity,
        [
            ("a", "prov:Entity"),
            ("rdfs:label", ttl_string("CAPE-KG PROV-O Turtle export")),
            ("cape:path", ttl_string(output_paths["ttl"])),
            ("cape:fileRole", ttl_string("prov_o_turtle_export")),
            ("prov:wasGeneratedBy", experiment_activity),
            ("prov:wasAttributedTo", "cape:pipeline_agent"),
        ],
    )

    return "\n".join(lines), {
        "entity_count": len(entity_uris),
        "activity_count": len(activity_uris),
        "agent_count": len(agent_uris),
        "triple_count": triple_count,
        "llm_run_count": len(llm_runs),
        "file_entity_count": len(file_records),
    }


def render_report(summary, manifest, output_paths):
    lines = [
        "# CAPE-KG PROV-O Export Report",
        "",
        f"Generated: {summary['generated_at_utc']}",
        f"Claim status: `{summary['claim_status']}`",
        "",
        "This report accompanies the W3C PROV-O Turtle export for the CAPE-KG experiment package. It records provenance for source files, prompt/schema files, LLM raw and validated outputs, evaluation files, human-review handoff files, and release artifacts.",
        "",
        "## Outputs",
        "",
        f"- Turtle: `{output_paths['ttl']}`",
        f"- Summary JSON: `{output_paths['summary_json']}`",
        f"- Report: `{output_paths['report_md']}`",
        "",
        "## Counts",
        "",
        "| Item | Value |",
        "|---|---:|",
        f"| Entities | {summary['entity_count']} |",
        f"| Activities | {summary['activity_count']} |",
        f"| Agents | {summary['agent_count']} |",
        f"| File entities | {summary['file_entity_count']} |",
        f"| LLM runs | {summary['llm_run_count']} |",
        f"| Turtle predicate statements | {summary['triple_count']} |",
        "",
        "## Interpretation",
        "",
        "- `prov:Entity` nodes represent files and derived artifacts, identified by path and SHA-256 when available.",
        "- `prov:Activity` nodes represent the experiment package, LLM extraction runs, human-review handoff preparation, and release-bundle preparation.",
        "- `prov:SoftwareAgent` nodes represent the executable CAPE-KG pipeline and indexed model paths.",
        "- This is reproducibility and lineage evidence. It is not human-gold performance evidence.",
        "",
        "## Source Manifest",
        "",
        f"- Manifest status: `{manifest.get('claim_status')}`",
        f"- Manifest generated at: `{manifest.get('generated_at_utc')}`",
        f"- Missing required provenance files: `{(manifest.get('summary') or {}).get('missing_required_count')}`",
        "",
    ]
    return "\n".join(lines)


def build_payload(exp_dir, outputs_dir):
    exp_dir = Path(exp_dir)
    release_dir = exp_dir / "06_release"
    manifest_path = release_dir / "provenance_manifest.json"
    run_index_path = exp_dir / "04_evaluation/provenance_llm_run_index.csv"
    manifest = read_json(manifest_path, {}) or {}
    llm_runs = read_csv(run_index_path)
    if not llm_runs:
        llm_runs = manifest.get("llm_runs", [])
    file_records = collect_file_records(manifest, llm_runs)
    output_paths = {
        "ttl": rel(release_dir / "provenance_prov_o.ttl"),
        "report_md": rel(release_dir / "provenance_prov_o_report.md"),
        "summary_json": rel(release_dir / "provenance_prov_o_summary.json"),
    }
    turtle, counts = build_turtle(manifest, llm_runs, file_records, output_paths)
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "outputs_dir": str(outputs_dir),
        "source_manifest": rel(manifest_path),
        "source_llm_run_index": rel(run_index_path),
        "claim_status": "prov_o_export_ready_not_human_gold_evidence",
        **counts,
        "outputs": output_paths,
    }
    return manifest, turtle, summary, output_paths


def run(args):
    manifest, turtle, summary, output_paths = build_payload(args.experiment_dir, args.outputs_dir)
    write_text(output_paths["ttl"], turtle)
    write_json(output_paths["summary_json"], summary)
    write_text(output_paths["report_md"], render_report(summary, manifest, output_paths))
    print(json.dumps({
        "ttl": output_paths["ttl"],
        "summary_json": output_paths["summary_json"],
        "report_md": output_paths["report_md"],
        "claim_status": summary["claim_status"],
        "entity_count": summary["entity_count"],
        "activity_count": summary["activity_count"],
        "agent_count": summary["agent_count"],
        "llm_run_count": summary["llm_run_count"],
    }, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--outputs-dir", default=str(DEFAULT_OUTPUTS_DIR))
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
