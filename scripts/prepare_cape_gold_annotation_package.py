#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prepare two-annotator gold annotation work packages for CAPE-KG."""

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

try:
    from build_cape_annotation_workbench import build_workbench
except ImportError:
    build_workbench = None


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
ANNOTATORS = ("A", "B")


def read_jsonl(path):
    rows = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path, rows, fieldnames):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def choose_pilot_rows(rows, size):
    """Pick a small, chapter-spread pilot with both easy and dense chunks."""
    if len(rows) <= size:
        return list(rows)

    by_chapter = {}
    for row in rows:
        by_chapter.setdefault(row.get("chapter_id") or "unknown", []).append(row)
    for chapter_rows in by_chapter.values():
        chapter_rows.sort(key=lambda r: (-int(r.get("silver_candidate_edge_count") or 0), r["chunk_id"]))

    selected = []
    selected_ids = set()
    chapters = sorted(by_chapter)
    while len(selected) < min(size, len(chapters)):
        chapter = chapters[len(selected) % len(chapters)]
        if by_chapter[chapter]:
            row = by_chapter[chapter].pop(0)
            selected.append(row)
            selected_ids.add(row["chunk_id"])

    remaining = [r for r in rows if r["chunk_id"] not in selected_ids]
    remaining.sort(key=lambda r: (-int(r.get("silver_candidate_edge_count") or 0), r["chunk_id"]))
    for row in remaining:
        if len(selected) >= size:
            break
        selected.append(row)
        selected_ids.add(row["chunk_id"])

    selected.sort(key=lambda r: r["chunk_id"])
    return selected


def candidate_summary(edge):
    spans = edge.get("evidence_spans") or []
    first_span = spans[0] if spans else {}
    primary_evidence = {
        "sentence_id": first_span.get("sentence_id"),
        "page": first_span.get("page"),
        "start_char": first_span.get("start_char"),
        "end_char": first_span.get("end_char"),
        "text": first_span.get("text"),
    }
    return {
        "reference_id": edge.get("reference_id"),
        "source_id": edge.get("source_id"),
        "source_label": edge.get("source_label"),
        "source_type": edge.get("source_type"),
        "predicate": edge.get("predicate"),
        "target_id": edge.get("target_id"),
        "target_label": edge.get("target_label"),
        "target_type": edge.get("target_type"),
        "evidence_anchor_ids": edge.get("evidence_anchor_ids", []),
        "primary_evidence": primary_evidence,
        "component_evidence_spans": component_evidence_spans(edge, primary_evidence),
    }


def find_label_span(text, label):
    text = str(text or "")
    label = str(label or "").strip()
    if not text or not label:
        return None
    idx = text.find(label)
    if idx >= 0:
        return idx, idx + len(label), text[idx: idx + len(label)], "exact_label_match"
    lowered_idx = text.lower().find(label.lower())
    if lowered_idx >= 0:
        return lowered_idx, lowered_idx + len(label), text[lowered_idx: lowered_idx + len(label)], "case_insensitive_label_match"
    return None


def component_span_row(edge, component, label, primary_evidence, span, method, exact):
    if span:
        start, end, span_text, method = span
    elif method == "full_sentence_proxy":
        span_text = primary_evidence.get("text") or ""
        start = 0
        end = len(span_text)
    else:
        start = ""
        end = ""
        span_text = ""
    return {
        "component": component,
        "label": label,
        "predicate": edge.get("predicate"),
        "sentence_id": primary_evidence.get("sentence_id"),
        "page": primary_evidence.get("page"),
        "sentence_span_start": start,
        "sentence_span_end": end,
        "text": span_text,
        "span_method": method,
        "span_exact": bool(exact),
        "claim_status": "automatic_candidate_span_suggestion_not_gold",
    }


def component_evidence_spans(edge, primary_evidence):
    text = primary_evidence.get("text") or ""
    source_label = edge.get("source_label") or ""
    target_label = edge.get("target_label") or ""
    source_span = find_label_span(text, source_label)
    target_span = find_label_span(text, target_label)
    return [
        component_span_row(edge, "subject", source_label, primary_evidence, source_span, "label_not_found_in_sentence", bool(source_span)),
        component_span_row(edge, "predicate", edge.get("predicate") or "", primary_evidence, None, "full_sentence_proxy", False),
        component_span_row(edge, "object", target_label, primary_evidence, target_span, "label_not_found_in_sentence", bool(target_span)),
    ]


def effective_candidate_edge_count(row):
    candidates = row.get("silver_candidate_edges")
    if isinstance(candidates, list):
        return len(candidates)
    return int(row.get("silver_candidate_edge_count") or 0)


def annotator_row(row, annotator_id, package_name):
    candidate_edges = [candidate_summary(edge) for edge in row.get("silver_candidate_edges", [])]
    return {
        "package": package_name,
        "annotator_id": annotator_id,
        "chunk_id": row["chunk_id"],
        "chapter_id": row.get("chapter_id"),
        "section_id": row.get("section_id"),
        "page_start": row.get("page_start"),
        "page_end": row.get("page_end"),
        "chunk_text": row.get("chunk_text"),
        "instructions": {
            "use_schema_only": True,
            "copy_candidate_edges_when_correct": True,
            "add_missing_edges_when_directly_supported": True,
            "remove_or_mark_rejected_when_unsupported": True,
            "evidence_required": True,
        },
        "silver_candidate_edge_count": len(candidate_edges),
        "silver_candidate_edges": candidate_edges,
        "gold_nodes": [],
        "gold_edges": [],
        "rejected_candidate_reference_ids": [],
        "missing_but_supported_notes": [],
        "annotation_status": "pending_human_annotation",
        "time_minutes": "",
        "comments": "",
    }


def adjudication_row(row, package_name):
    return {
        "package": package_name,
        "chunk_id": row["chunk_id"],
        "chapter_id": row.get("chapter_id"),
        "section_id": row.get("section_id"),
        "page_start": row.get("page_start"),
        "page_end": row.get("page_end"),
        "chunk_text": row.get("chunk_text"),
        "annotator_a_status": "pending_human_annotation",
        "annotator_b_status": "pending_human_annotation",
        "disagreement_items": [],
        "adjudicated_gold_nodes": [],
        "adjudicated_gold_edges": [],
        "adjudicator_id": "",
        "adjudication_status": "pending_two_annotator_input",
        "adjudication_notes": "",
    }


def tracking_rows(rows, package_name):
    output = []
    for row in rows:
        output.append(
            {
                "package": package_name,
                "chunk_id": row["chunk_id"],
                "chapter_id": row.get("chapter_id"),
                "section_id": row.get("section_id"),
                "page_start": row.get("page_start"),
                "page_end": row.get("page_end"),
                "silver_candidate_edge_count": effective_candidate_edge_count(row),
                "annotator_A_status": "pending_human_annotation",
                "annotator_B_status": "pending_human_annotation",
                "adjudication_status": "pending_two_annotator_input",
                "priority": "pilot" if package_name == "pilot_30" else "full",
                "comment": "",
            }
        )
    return output


def write_protocol(path):
    path = Path(path)
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if "## 8. Adjudicator 판정 기준" in existing and "## 11. Adjudication checklist" in existing:
            return
    text = """# CAPE-KG Gold Annotation and Adjudication Protocol

Generated for two independent human annotators.

## Annotation Unit

Annotate one `chunk_id` at a time. Use the chunk text as the only authority.
Silver candidates are suggestions, not gold labels.
`component_evidence_spans` are automatic aids for locating subject, predicate,
and object evidence in the primary evidence sentence. They are not gold labels;
annotators must still verify the relation directly against the chunk text.

## Required Decisions

For each chunk:

- Accept candidate edges only when the source, predicate, target, and evidence are directly supported.
- Reject unsupported, over-generalized, wrong-direction, or wrong-type candidates.
- Add missing nodes or edges only when they are explicitly supported by the chunk.
- Every accepted edge must include at least one evidence anchor or exact span.
- Keep Korean surface labels when possible and preserve English aliases.

## Status Values

Use `completed` only after all candidate and missing-edge decisions are filled.
Use `needs_adjudication` when the annotator is uncertain. Do not use `completed`
for partially reviewed chunks.

## Optional Workbench

Open `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/annotation_workbench.html`
in a browser, load an annotator or adjudication JSONL file, and export the edited
JSONL after review. The workbench is an editing aid; exported files must still be
validated by the scripts below.

For returned human files, prefer the all-in-one wrapper. First run a dry-run
preflight/import/refresh:

```bash
PYTHON_BIN=python3 \\
LLM_PYTHON=python3 \\
APPLY_IMPORTS=0 \\
bash scripts/run_cape_human_return_apply.sh
```

If validation passes and all expected return files are present, rerun with
`APPLY_IMPORTS=1`. The wrapper checks chunk identity, schema values, evidence
anchors, immutable text fields, IAA/adjudication state, mapping review files,
claim gates, and release/handoff bundle checksums.

```bash
PYTHON_BIN=python3 \\
LLM_PYTHON=python3 \\
APPLY_IMPORTS=1 \\
bash scripts/run_cape_human_return_apply.sh
```

Use `scripts/import_cape_gold_annotation.py --apply` directly only for debugging
a single returned batch after the wrapper has identified a specific problem.

## Adjudication

After both annotators finish, run:

```bash
python3 scripts/compute_cape_annotation_iaa.py \\
  --annotator-a experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/annotator_A.jsonl \\
  --annotator-b experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/annotator_B.jsonl \\
  --output-dir experiments/cape_kg_eacl_20260627/01_data/gold_annotation/iaa_full_120
```

Then adjudicate every chunk with disagreement into `adjudication.jsonl`.
Paper-level scores must use adjudicated gold, not silver candidates.

You can generate an adjudication draft after the A/B files are filled:

```bash
python3 scripts/prepare_cape_adjudication_draft.py \\
  --experiment-dir experiments/cape_kg_eacl_20260627 \\
  --package full_120
```

After adjudication is complete, validate the gold file and score actual LLM
outputs with:

```bash
python3 scripts/import_cape_gold_annotation.py \\
  --experiment-dir experiments/cape_kg_eacl_20260627 \\
  --target-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/adjudication.jsonl \\
  --reviewed-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/adjudication_edited.jsonl
```

```bash
python3 scripts/evaluate_cape_human_gold.py \\
  --experiment-dir experiments/cape_kg_eacl_20260627
```
"""
    Path(path).write_text(text, encoding="utf-8")


def write_schema(path):
    schema = {
        "annotation_file_type": "jsonl",
        "required_chunk_fields": ["chunk_id", "chunk_text", "gold_nodes", "gold_edges", "annotation_status"],
        "gold_node_fields": ["node_id", "type", "label", "evidence"],
        "gold_edge_fields": [
            "source_id",
            "source_label",
            "source_type",
            "predicate",
            "target_id",
            "target_label",
            "target_type",
            "evidence_anchor_ids",
            "evidence_spans",
            "decision",
        ],
        "completed_status_values": ["completed", "needs_adjudication"],
        "paper_claim_requires": [
            "100+ completed/adjudicated chunks",
            "500+ adjudicated node/edge/evidence items",
            "two annotators",
            "IAA report",
            "adjudicated gold file",
        ],
    }
    write_json(path, schema)


def build_package(exp_dir, pilot_size):
    exp_dir = Path(exp_dir)
    template_path = exp_dir / "01_data/gold_annotation_template.jsonl"
    if not template_path.exists():
        raise SystemExit(f"Missing annotation template: {template_path}")

    rows = read_jsonl(template_path)
    pilot = choose_pilot_rows(rows, pilot_size)
    packages = {
        "pilot_30": pilot,
        "full_120": rows,
    }
    out_root = exp_dir / "01_data/gold_annotation"
    out_root.mkdir(parents=True, exist_ok=True)

    package_summaries = {}
    all_tracking = []
    for package_name, package_rows in packages.items():
        package_dir = out_root / package_name
        package_dir.mkdir(parents=True, exist_ok=True)
        for annotator in ANNOTATORS:
            write_jsonl(
                package_dir / f"annotator_{annotator}.jsonl",
                [annotator_row(row, annotator, package_name) for row in package_rows],
            )
        write_jsonl(package_dir / "adjudication.jsonl", [adjudication_row(row, package_name) for row in package_rows])
        rows_for_tracking = tracking_rows(package_rows, package_name)
        all_tracking.extend(rows_for_tracking)
        write_csv(
            package_dir / "tracking_sheet.csv",
            rows_for_tracking,
            [
                "package",
                "chunk_id",
                "chapter_id",
                "section_id",
                "page_start",
                "page_end",
                "silver_candidate_edge_count",
                "annotator_A_status",
                "annotator_B_status",
                "adjudication_status",
                "priority",
                "comment",
            ],
        )
        candidate_counts = [effective_candidate_edge_count(row) for row in package_rows]
        package_summaries[package_name] = {
            "chunk_count": len(package_rows),
            "annotator_files": {
                annotator: str(package_dir / f"annotator_{annotator}.jsonl") for annotator in ANNOTATORS
            },
            "adjudication_file": str(package_dir / "adjudication.jsonl"),
            "adjudication_draft_file": str(package_dir / "adjudication_draft.jsonl"),
            "adjudication_draft_summary": str(package_dir / "adjudication_draft_summary.json"),
            "adjudication_draft_report": str(package_dir / "adjudication_draft_report.md"),
            "tracking_sheet": str(package_dir / "tracking_sheet.csv"),
            "candidate_edges_total": sum(candidate_counts),
            "candidate_edges_min": min(candidate_counts) if candidate_counts else 0,
            "candidate_edges_max": max(candidate_counts) if candidate_counts else 0,
            "chapter_distribution": dict(Counter(row.get("chapter_id") or "unknown" for row in package_rows)),
        }

    write_csv(
        out_root / "gold_annotation_master_tracking_sheet.csv",
        all_tracking,
        [
            "package",
            "chunk_id",
            "chapter_id",
            "section_id",
            "page_start",
            "page_end",
            "silver_candidate_edge_count",
            "annotator_A_status",
            "annotator_B_status",
            "adjudication_status",
            "priority",
            "comment",
        ],
    )
    write_protocol(out_root / "adjudication_protocol.md")
    write_schema(out_root / "annotation_schema.json")
    workbench_path = out_root / "annotation_workbench.html"
    if build_workbench:
        build_workbench(workbench_path)

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "ready_for_two_human_annotators_pending_labels",
        "source_template": str(template_path),
        "output_dir": str(out_root),
        "annotators": list(ANNOTATORS),
        "packages": package_summaries,
        "protocol": str(out_root / "adjudication_protocol.md"),
        "annotation_schema": str(out_root / "annotation_schema.json"),
        "annotation_workbench": str(workbench_path),
        "annotator_import_command_template": (
            "python3 scripts/import_cape_gold_annotation.py --experiment-dir "
            "experiments/cape_kg_eacl_20260627 --target-file "
            "{target_annotator_jsonl} --reviewed-file {exported_annotator_jsonl}"
        ),
        "adjudication_import_command_template": (
            "python3 scripts/import_cape_gold_annotation.py --experiment-dir "
            "experiments/cape_kg_eacl_20260627 --target-file "
            "{target_adjudication_jsonl} --reviewed-file {exported_adjudication_jsonl}"
        ),
        "master_tracking_sheet": str(out_root / "gold_annotation_master_tracking_sheet.csv"),
        "claim_status": "not_gold_until_human_completed_and_adjudicated",
    }
    write_json(out_root / "annotation_package_manifest.json", manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--pilot-size", type=int, default=30)
    args = parser.parse_args()
    manifest = build_package(args.experiment_dir, args.pilot_size)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
