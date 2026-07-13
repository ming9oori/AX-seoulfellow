#!/usr/bin/env python3
"""Profile public KG/procedural benchmarks for the CAPE-KG EACL package."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")


def read_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read_jsonl(path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            f.write("\n")


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write(text)


def git_revision(repo):
    head = repo / ".git/HEAD"
    if not head.exists():
        return None
    value = head.read_text(encoding="utf-8").strip()
    if value.startswith("ref: "):
        ref_path = repo / ".git" / value.split(" ", 1)[1]
        if ref_path.exists():
            return ref_path.read_text(encoding="utf-8").strip()
    return value


def avg(values):
    return round(sum(values) / len(values), 2) if values else 0.0


def metric(value):
    try:
        return round(float(value), 4)
    except Exception:
        return 0.0


def profile_paged(repo, out_dir, subset_size):
    data_dir = repo / "dataset/procedural_graph_extraction"
    split_profiles = {}
    subset_rows = []
    for split in ["train", "dev", "test"]:
        path = data_dir / f"{split}.json"
        if not path.exists():
            continue
        rows = read_json(path)
        profile = {
            "file": str(path),
            "items": len(rows),
            "avg_paragraph_chars": avg([len(r.get("paragraph", "")) for r in rows]),
            "step_nodes": sum(len(r.get("step_nodes", [])) for r in rows),
            "data_nodes": sum(len(r.get("data_nodes", [])) for r in rows),
            "text_nodes": sum(len(r.get("text_nodes", [])) for r in rows),
            "sequence_flows": sum(len(r.get("SequenceFlow", [])) for r in rows),
            "message_flows": sum(len(r.get("MessageFlow", [])) for r in rows),
            "associations": sum(len(r.get("Association", [])) for r in rows),
        }
        split_profiles[split] = profile

        if split == "test":
            for item in rows[:subset_size]:
                nodes = []
                for source_key, cape_type in [
                    ("step_nodes", "ProcedureStep"),
                    ("data_nodes", "Artifact"),
                    ("text_nodes", "GuardCondition"),
                ]:
                    for node in item.get(source_key, []):
                        nodes.append(
                            {
                                "source_id": node.get("resourceId"),
                                "label": node.get("NodeText", ""),
                                "source_type": node.get("type", ""),
                                "cape_type": cape_type,
                                "role": node.get("agent", ""),
                            }
                        )
                edges = []
                for source_key, predicate in [
                    ("SequenceFlow", "PRECEDES"),
                    ("MessageFlow", "MESSAGE_FLOW"),
                    ("Association", "ASSOCIATED_WITH"),
                ]:
                    for edge in item.get(source_key, []):
                        edges.append(
                            {
                                "source": edge.get("src"),
                                "target": edge.get("tgt"),
                                "predicate": predicate,
                                "condition": edge.get("condition", ""),
                            }
                        )
                subset_rows.append(
                    {
                        "source_benchmark": "PAGED",
                        "source_url": "https://github.com/WitcherLeo/PAGED",
                        "split": "test",
                        "item_id": f"paged_test_{item.get('file_index')}",
                        "text": item.get("paragraph", ""),
                        "task": "procedural_graph_extraction",
                        "gold_nodes": nodes,
                        "gold_edges": edges,
                        "gold_counts": {
                            "nodes": len(nodes),
                            "edges": len(edges),
                            "or_node_num": item.get("or_node_num", 0),
                        },
                    }
                )

    profile = {
        "benchmark": "PAGED",
        "source_url": "https://github.com/WitcherLeo/PAGED",
        "paper_url": "https://aclanthology.org/2024.acl-long.583/",
        "local_repo": str(repo),
        "git_revision": git_revision(repo),
        "splits": split_profiles,
        "adapter_subset_file": str(out_dir / "paged_cape_adapter_subset.jsonl"),
        "adapter_subset_items": len(subset_rows),
        "adapter_status": "gold_graph_reformatted_for_cape_external_subset_no_model_run",
    }
    write_json(out_dir / "paged_profile.json", profile)
    write_jsonl(out_dir / "paged_cape_adapter_subset.jsonl", subset_rows)
    return profile


def count_jsonl(path):
    lines = 0
    triples = 0
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            lines += 1
            try:
                triples += len(json.loads(line).get("triples", []))
            except Exception:
                pass
    return lines, triples


def profile_text2kgbench(repo, out_dir, subset_size):
    data_root = repo / "data"
    dataset_profiles = {}
    subset_rows = []
    for dataset in ["wikidata_tekgen", "dbpedia_webnlg"]:
        root = data_root / dataset
        if not root.exists():
            continue
        ontology_profiles = []
        for ont_path in sorted((root / "ontologies").glob("*.json")):
            ont = read_json(ont_path)
            ontology_profiles.append(
                {
                    "ontology_id": ont.get("id") or ont_path.stem,
                    "title": ont.get("title", ""),
                    "file": str(ont_path),
                    "concepts": len(ont.get("concepts", [])),
                    "relations": len(ont.get("relations", [])),
                }
            )
        split_counts = {}
        for split in ["train", "validation", "test", "ground_truth"]:
            split_dir = root / split
            if not split_dir.exists():
                continue
            files = sorted(split_dir.glob("*.jsonl"))
            row_count = 0
            triple_count = 0
            for path in files:
                lines, triples = count_jsonl(path)
                row_count += lines
                triple_count += triples
            split_counts[split] = {
                "files": len(files),
                "rows": row_count,
                "triples": triple_count,
            }

        dataset_subset_rows = 0
        for gt_path in sorted((root / "ground_truth").glob("*.jsonl")):
            if dataset_subset_rows >= subset_size:
                break
            ontology_key = gt_path.name.replace("_ground_truth.jsonl", "")
            ontology_path = root / "ontologies" / f"{ontology_key.replace('ont_', '')}_ontology.json"
            ontology = read_json(ontology_path) if ontology_path.exists() else {}
            concepts = [c.get("label", "") for c in ontology.get("concepts", [])]
            relations = [r.get("label", "") for r in ontology.get("relations", [])]
            for row in read_jsonl(gt_path):
                if dataset_subset_rows >= subset_size:
                    break
                subset_rows.append(
                    {
                        "source_benchmark": "Text2KGBench",
                        "source_url": "https://github.com/cenguix/Text2KGBench",
                        "dataset": dataset,
                        "ontology_id": ontology.get("id") or ontology_key,
                        "item_id": row.get("id"),
                        "text": row.get("sent", ""),
                        "task": "ontology_guided_kg_generation",
                        "ontology_concepts": concepts,
                        "ontology_relations": relations,
                        "gold_triples": row.get("triples", []),
                    }
                )
                dataset_subset_rows += 1

        dataset_profiles[dataset] = {
            "local_dir": str(root),
            "ontologies": len(ontology_profiles),
            "ontology_profiles": ontology_profiles,
            "split_counts": split_counts,
        }

    profile = {
        "benchmark": "Text2KGBench",
        "source_url": "https://github.com/cenguix/Text2KGBench",
        "paper_url": "https://doi.org/10.1007/978-3-031-47243-5_14",
        "local_repo": str(repo),
        "git_revision": git_revision(repo),
        "datasets": dataset_profiles,
        "adapter_subset_file": str(out_dir / "text2kgbench_cape_adapter_subset.jsonl"),
        "adapter_subset_items": len(subset_rows),
        "adapter_status": "gold_triples_reformatted_for_cape_external_subset_no_model_run",
    }
    write_json(out_dir / "text2kgbench_profile.json", profile)
    write_jsonl(out_dir / "text2kgbench_cape_adapter_subset.jsonl", subset_rows)
    return profile


def collect_public_eval_summaries(out_dir):
    runs = []
    for path in sorted(out_dir.glob("public_*_summary.json")):
        if ".shard" in path.name:
            continue
        data = read_json(path)
        if not (data.get("paged_items") or data.get("text2kg_items")):
            continue
        runs.append(
            {
                "run_id": path.name.replace("_summary.json", ""),
                "summary_file": str(path),
                "model": data.get("model", ""),
                "quantization": data.get("quantization", ""),
                "paged_items": int(data.get("paged_items") or 0),
                "text2kg_items": int(data.get("text2kg_items") or 0),
                "paged_node_f1": metric((data.get("paged") or {}).get("mean_node_label_f1")),
                "paged_edge_f1": metric((data.get("paged") or {}).get("mean_edge_predicate_f1")),
                "text2kg_relation_f1": metric((data.get("text2kg") or {}).get("mean_relation_f1")),
                "text2kg_triple_f1": metric((data.get("text2kg") or {}).get("mean_triple_exact_f1")),
                "raw_rows": int(data.get("raw_rows") or 0),
                "valid_rows": int(data.get("valid_rows") or 0),
                "result_rows": int(data.get("result_rows") or 0),
                "errors": data.get("errors") or {},
                "is_shard": bool(data.get("is_shard")),
            }
        )
    return runs


def summarize_public_crosscheck(runs):
    if not runs:
        return {
            "claim_status": "public_adapter_profiled_no_model_run",
            "run_count": 0,
            "strong_cross_run_present": False,
            "best_paged_edge_f1": 0.0,
            "best_text2kg_relation_f1": 0.0,
            "best_paged_run": "",
            "best_text2kg_run": "",
            "max_single_run_paged_items": 0,
            "max_single_run_text2kg_items": 0,
        }
    best_paged = max(runs, key=lambda row: (row["paged_edge_f1"], row["paged_items"]))
    best_text2kg = max(runs, key=lambda row: (row["text2kg_relation_f1"], row["text2kg_items"]))
    strong_runs = [row for row in runs if row["paged_items"] >= 100 and row["text2kg_items"] >= 200]
    return {
        "claim_status": "public_adapter_model_runs_diagnostic_not_official_leaderboard",
        "run_count": len(runs),
        "strong_cross_run_present": bool(strong_runs),
        "strong_cross_runs": [row["run_id"] for row in strong_runs],
        "best_paged_edge_f1": best_paged["paged_edge_f1"],
        "best_text2kg_relation_f1": best_text2kg["text2kg_relation_f1"],
        "best_paged_run": best_paged["run_id"],
        "best_text2kg_run": best_text2kg["run_id"],
        "max_single_run_paged_items": max(row["paged_items"] for row in runs),
        "max_single_run_text2kg_items": max(row["text2kg_items"] for row in runs),
    }


def build_crosscheck_report(payload):
    summary = payload["summary"]
    lines = [
        "# Public Benchmark Cross-Check Summary",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Claim status: `{summary['claim_status']}`",
        "",
        "This report consolidates public PAGED/Text2KGBench adapter model runs. These are diagnostic adapter runs, not official benchmark leaderboard claims.",
        "",
        "## Gate Evidence",
        "",
        f"- Run count: {summary['run_count']}",
        f"- Strong cross run present: {summary['strong_cross_run_present']}",
        f"- Max single-run PAGED items: {summary['max_single_run_paged_items']}",
        f"- Max single-run Text2KGBench items: {summary['max_single_run_text2kg_items']}",
        f"- Best PAGED edge F1: {summary['best_paged_edge_f1']} (`{summary['best_paged_run']}`)",
        f"- Best Text2KGBench relation F1: {summary['best_text2kg_relation_f1']} (`{summary['best_text2kg_run']}`)",
        "",
        "## Runs",
        "",
        "| run | PAGED n | PAGED node F1 | PAGED edge F1 | Text2KG n | relation F1 | triple F1 | errors |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["runs"]:
        lines.append(
            f"| `{row['run_id']}` | {row['paged_items']} | {row['paged_node_f1']} | {row['paged_edge_f1']} | "
            f"{row['text2kg_items']} | {row['text2kg_relation_f1']} | {row['text2kg_triple_f1']} | {sum((row.get('errors') or {}).values())} |"
        )
    lines += [
        "",
        "## Claim Scope",
        "",
        "- Public adapter runs support external diagnostic coverage only.",
        "- The Korean enterprise main result still requires adjudicated human-gold scoring.",
        "- PAGED and Text2KGBench metrics are not directly comparable to the internal CAPE-KG task because schemas and gold structures differ.",
        "",
    ]
    return "\n".join(lines)


def build_report(manifest):
    paged = manifest["benchmarks"]["PAGED"]
    text2kg = manifest["benchmarks"]["Text2KGBench"]
    eval_runs = manifest.get("public_model_evaluations", [])
    crosscheck = manifest.get("public_crosscheck_summary", {})
    lines = [
        "# Public Benchmark Adapter Report",
        "",
        f"Generated: {manifest['generated_at_utc']}",
        "",
        "## Status",
        "",
        "- PAGED and Text2KGBench repositories were acquired locally.",
        "- Dataset profiles and CAPE-KG adapter subsets were generated.",
        f"- Public model evaluation runs found: {len(eval_runs)}.",
        f"- Strong cross-check run present: {crosscheck.get('strong_cross_run_present', False)}.",
        "",
        "## PAGED",
        "",
        f"- Source: {paged['source_url']}",
        f"- Local repo: `{paged['local_repo']}`",
        f"- Adapter subset items: {paged['adapter_subset_items']}",
    ]
    for split, stats in paged.get("splits", {}).items():
        lines.append(
            f"- {split}: items={stats['items']}, step_nodes={stats['step_nodes']}, "
            f"data_nodes={stats['data_nodes']}, sequence_flows={stats['sequence_flows']}"
        )
    lines += [
        "",
        "## Text2KGBench",
        "",
        f"- Source: {text2kg['source_url']}",
        f"- Local repo: `{text2kg['local_repo']}`",
        f"- Adapter subset items: {text2kg['adapter_subset_items']}",
    ]
    for dataset, stats in text2kg.get("datasets", {}).items():
        split_bits = []
        for split, counts in stats.get("split_counts", {}).items():
            split_bits.append(f"{split}: rows={counts['rows']}, triples={counts['triples']}")
        lines.append(f"- {dataset}: ontologies={stats['ontologies']}; " + "; ".join(split_bits))
    lines += [
        "",
        "## Model Evaluation Runs",
        "",
        "| run | PAGED n | PAGED edge F1 | Text2KG n | relation F1 | triple F1 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in eval_runs:
        lines.append(
            f"| `{row['run_id']}` | {row['paged_items']} | {row['paged_edge_f1']} | "
            f"{row['text2kg_items']} | {row['text2kg_relation_f1']} | {row['text2kg_triple_f1']} |"
        )
    lines += [
        "",
        "## CAPE-KG Use",
        "",
        "- PAGED maps to the procedural graph extraction side of CAPE-KG.",
        "- Text2KGBench maps to ontology-constrained KG extraction and conformance checks.",
        "- These public results are auxiliary diagnostics, not official leaderboard or Korean enterprise human-gold claims.",
        "",
    ]
    return "\n".join(lines)


def run(args):
    exp_dir = Path(args.experiment_dir)
    out_dir = exp_dir / "08_public_benchmarks"
    repo_dir = out_dir / "repos"
    paged_repo = repo_dir / "PAGED"
    text2kg_repo = repo_dir / "Text2KGBench"
    if not paged_repo.exists():
        raise SystemExit(f"Missing PAGED repo: {paged_repo}")
    if not text2kg_repo.exists():
        raise SystemExit(f"Missing Text2KGBench repo: {text2kg_repo}")

    paged = profile_paged(paged_repo, out_dir, args.paged_subset_size)
    text2kg = profile_text2kgbench(text2kg_repo, out_dir, args.text2kg_subset_size)
    eval_runs = collect_public_eval_summaries(out_dir)
    crosscheck_summary = summarize_public_crosscheck(eval_runs)
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "status": "public_benchmarks_acquired_profiled_adapter_subsets_and_model_runs_indexed"
        if eval_runs
        else "public_benchmarks_acquired_profiled_adapter_subsets_generated_no_model_run",
        "benchmarks": {
            "PAGED": paged,
            "Text2KGBench": text2kg,
        },
        "public_model_evaluations": eval_runs,
        "public_crosscheck_summary": crosscheck_summary,
        "next_required_step": "Use public runs as auxiliary diagnostics; final internal claims still require human-gold scoring.",
    }
    write_json(out_dir / "public_benchmark_manifest.json", manifest)
    crosscheck_payload = {
        "generated_at_utc": manifest["generated_at_utc"],
        "experiment_dir": str(exp_dir),
        "summary": crosscheck_summary,
        "runs": eval_runs,
    }
    write_json(out_dir / "public_benchmark_crosscheck_summary.json", crosscheck_payload)
    write_text(out_dir / "public_benchmark_crosscheck_report.md", build_crosscheck_report(crosscheck_payload))
    write_text(out_dir / "public_benchmark_adapter_report.md", build_report(manifest))
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--paged-subset-size", type=int, default=100)
    parser.add_argument("--text2kg-subset-size", type=int, default=100)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
