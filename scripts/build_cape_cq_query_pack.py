#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build CQ query pack and sample answers for CAPE-KG."""

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_OUTPUTS_DIR = Path("outputs")

CQ_QUERY_SPECS = [
    {
        "cq_id": "CQ1",
        "query_focus": "Task and procedure-step composition/order",
        "predicates": ["HAS_STEP", "PRECEDES"],
        "source": "layer2_edges",
    },
    {
        "cq_id": "CQ2",
        "query_focus": "Input artifacts used by tasks/steps",
        "predicates": ["USES_INPUT"],
        "source": "layer2_edges",
    },
    {
        "cq_id": "CQ3",
        "query_focus": "Output artifacts produced by tasks/steps",
        "predicates": ["PRODUCES"],
        "source": "layer2_edges",
    },
    {
        "cq_id": "CQ4",
        "query_focus": "Responsible roles",
        "predicates": ["PERFORMED_BY"],
        "source": "layer2_edges",
    },
    {
        "cq_id": "CQ5",
        "query_focus": "Decision gateways",
        "predicates": ["HAS_DECISION_GATEWAY"],
        "source": "layer2_edges",
    },
    {
        "cq_id": "CQ6",
        "query_focus": "Guard conditions for decisions",
        "predicates": ["HAS_GUARD_CONDITION"],
        "source": "layer2_edges",
    },
    {
        "cq_id": "CQ7",
        "query_focus": "Artifact flow between tasks",
        "predicates": ["FEEDS_INTO", "USED_AS_INPUT_FOR"],
        "source": "layer2_edges",
    },
    {
        "cq_id": "CQ8",
        "query_focus": "Review checkpoints",
        "predicates": ["HAS_REVIEW_CHECKPOINT"],
        "source": "layer2_edges",
    },
    {
        "cq_id": "CQ9",
        "query_focus": "Principles attached to work items",
        "predicates": ["HAS_PRINCIPLE"],
        "source": "layer2_edges",
    },
    {
        "cq_id": "CQ10",
        "query_focus": "Evidence grounding for accepted KG edges",
        "predicates": ["EVIDENCED_BY"],
        "source": "edge.evidence_anchor_ids",
    },
    {
        "cq_id": "CQ11",
        "query_focus": "Layer2-to-NCS capability candidates",
        "predicates": ["REQUIRES_CAPABILITY", "CANDIDATE_ALIGNS_WITH"],
        "source": "l2_ncs_mapping_candidates",
    },
    {
        "cq_id": "CQ12",
        "query_focus": "Layer2-to-PCF process context candidates",
        "predicates": ["PROCESS_CONTEXT", "CANDIDATE_ALIGNS_WITH"],
        "source": "l2_pcf_mapping_candidates",
    },
]


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
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def rel(path):
    return str(Path(path).as_posix())


def cypher_for(spec):
    source = spec["source"]
    predicates = spec["predicates"]
    if source == "edge.evidence_anchor_ids":
        return (
            "MATCH (s:KGNode)-[r]->(t:KGNode)\n"
            "WHERE r.evidence_anchor_ids_json IS NOT NULL AND r.evidence_anchor_ids_json <> ''\n"
            "RETURN s.node_id AS source_id, s.label AS source_label, type(r) AS predicate,\n"
            "       t.node_id AS target_id, t.label AS target_label,\n"
            "       r.evidence_anchor_ids_json AS evidence_anchor_ids\n"
            "LIMIT 25;"
        )
    if source == "l2_ncs_mapping_candidates":
        return (
            "MATCH (task:KGNode:Layer2)-[r:REQUIRES_CAPABILITY]->(target:KGNode:Layer1NCS)\n"
            "RETURN task.node_id AS task_id, task.label AS task_label,\n"
            "       target.node_id AS ncs_id, target.label AS ncs_label,\n"
            "       r.rank AS rank, r.score AS score, r.reason AS reason\n"
            "ORDER BY task_id, rank\n"
            "LIMIT 25;"
        )
    if source == "l2_pcf_mapping_candidates":
        return (
            "MATCH (task:KGNode:Layer2)-[r:PROCESS_CONTEXT]->(target:KGNode:Layer1PCF)\n"
            "RETURN task.node_id AS task_id, task.label AS task_label,\n"
            "       target.node_id AS pcf_id, target.label AS pcf_label,\n"
            "       r.rank AS rank, r.score AS score, r.reason AS reason\n"
            "ORDER BY task_id, rank\n"
            "LIMIT 25;"
        )
    rel_union = "|".join(predicates)
    return (
        f"MATCH (s:KGNode)-[r:{rel_union}]->(t:KGNode)\n"
        "RETURN s.node_id AS source_id, s.label AS source_label, labels(s) AS source_labels,\n"
        "       type(r) AS predicate,\n"
        "       t.node_id AS target_id, t.label AS target_label, labels(t) AS target_labels,\n"
        "       r.evidence_anchor_ids_json AS evidence_anchor_ids\n"
        "LIMIT 25;"
    )


def sparql_for(spec):
    source = spec["source"]
    predicates = spec["predicates"]
    prefix = (
        "PREFIX cape: <https://example.org/cape-kg#>\n"
        "PREFIX prov: <http://www.w3.org/ns/prov#>\n"
        "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n"
    )
    if source == "edge.evidence_anchor_ids":
        body = (
            "SELECT ?edge ?predicate ?source ?target ?evidenceAnchorId WHERE {\n"
            "  ?edge a cape:KGEdge ; cape:predicate ?predicate ;\n"
            "        cape:sourceNode ?source ; cape:targetNode ?target ;\n"
            "        prov:wasDerivedFrom ?evidence .\n"
            "  ?evidence cape:evidenceAnchorId ?evidenceAnchorId .\n"
            "}\nLIMIT 25"
        )
    elif source == "l2_ncs_mapping_candidates":
        body = (
            "SELECT ?edge ?source ?target ?rank ?score WHERE {\n"
            "  ?edge a cape:KGEdge ; cape:predicate \"REQUIRES_CAPABILITY\" ;\n"
            "        cape:sourceNode ?source ; cape:targetNode ?target .\n"
            "  OPTIONAL { ?edge cape:rank ?rank }\n"
            "  OPTIONAL { ?edge cape:score ?score }\n"
            "}\nLIMIT 25"
        )
    elif source == "l2_pcf_mapping_candidates":
        body = (
            "SELECT ?edge ?source ?target ?rank ?score WHERE {\n"
            "  ?edge a cape:KGEdge ; cape:predicate \"PROCESS_CONTEXT\" ;\n"
            "        cape:sourceNode ?source ; cape:targetNode ?target .\n"
            "  OPTIONAL { ?edge cape:rank ?rank }\n"
            "  OPTIONAL { ?edge cape:score ?score }\n"
            "}\nLIMIT 25"
        )
    else:
        values = " ".join(f'"{predicate}"' for predicate in predicates)
        body = (
            "SELECT ?edge ?predicate ?source ?target ?evidenceAnchorId WHERE {\n"
            f"  VALUES ?predicate {{ {values} }}\n"
            "  ?edge a cape:KGEdge ; cape:predicate ?predicate ;\n"
            "        cape:sourceNode ?source ; cape:targetNode ?target .\n"
            "  OPTIONAL {\n"
            "    ?edge prov:wasDerivedFrom ?evidence .\n"
            "    ?evidence cape:evidenceAnchorId ?evidenceAnchorId .\n"
            "  }\n"
            "}\nLIMIT 25"
        )
    return prefix + body


def sample_edge_answers(spec, edges, node_by_id, limit):
    predicates = set(spec["predicates"])
    rows = []
    if spec["source"] == "edge.evidence_anchor_ids":
        candidates = [edge for edge in edges if edge.get("evidence_anchor_ids")]
    else:
        candidates = [edge for edge in edges if edge.get("predicate") in predicates]
    for edge in candidates[:limit]:
        source = node_by_id.get(edge.get("source_id"), {})
        target = node_by_id.get(edge.get("target_id"), {})
        rows.append(
            {
                "answer_type": "edge",
                "id": edge.get("edge_id"),
                "source_id": edge.get("source_id"),
                "source_label": source.get("label", ""),
                "source_type": source.get("type", ""),
                "predicate": edge.get("predicate"),
                "target_id": edge.get("target_id"),
                "target_label": target.get("label", ""),
                "target_type": target.get("type", ""),
                "rank": "",
                "score": edge.get("confidence", ""),
                "evidence_anchor_ids": edge.get("evidence_anchor_ids") or [],
                "review_status": edge.get("review_status", ""),
            }
        )
    return rows


def sample_mapping_answers(rows, limit):
    output = []
    for row in rows[:limit]:
        output.append(
            {
                "answer_type": "mapping",
                "id": row.get("mapping_id"),
                "source_id": row.get("source_id"),
                "source_label": row.get("source_label"),
                "source_type": row.get("source_type"),
                "predicate": "REQUIRES_CAPABILITY" if row.get("mapping_type") == "requiresCapability" else "PROCESS_CONTEXT",
                "target_id": row.get("target_id"),
                "target_label": row.get("target_label"),
                "target_type": row.get("target_type"),
                "rank": row.get("rank", ""),
                "score": row.get("score", ""),
                "evidence_anchor_ids": [],
                "review_status": row.get("review_status", ""),
            }
        )
    return output


def answerability_by_cq(exp_dir):
    metrics = read_json(Path(exp_dir) / "04_evaluation/cq_answerability_structural_metrics.json", {}) or {}
    return {row.get("cq_id"): row for row in metrics.get("rows", [])}


def build_pack(exp_dir, outputs_dir, sample_limit):
    exp_dir = Path(exp_dir)
    outputs_dir = Path(outputs_dir)
    cqs = read_json(exp_dir / "02_schema/competency_questions.json", []) or []
    cq_by_id = {row.get("cq_id"): row for row in cqs}
    answerability = answerability_by_cq(exp_dir)

    nodes = read_jsonl(outputs_dir / "07_layer2_graph/layer2_nodes.jsonl")
    edges = read_jsonl(outputs_dir / "07_layer2_graph/layer2_edges.jsonl")
    node_by_id = {row.get("node_id"): row for row in nodes}
    predicate_counts = Counter(edge.get("predicate") for edge in edges)
    ncs_rows = read_jsonl(outputs_dir / "08_mapping/l2_ncs_mapping_candidates.jsonl")
    pcf_rows = read_jsonl(outputs_dir / "08_mapping/l2_pcf_mapping_candidates.jsonl")

    query_rows = []
    answer_rows = []
    for spec in CQ_QUERY_SPECS:
        cq_id = spec["cq_id"]
        cq = cq_by_id.get(cq_id, {})
        structural = answerability.get(cq_id, {})
        if spec["source"] == "l2_ncs_mapping_candidates":
            samples = sample_mapping_answers(ncs_rows, sample_limit)
            support_count = len(ncs_rows)
        elif spec["source"] == "l2_pcf_mapping_candidates":
            samples = sample_mapping_answers(pcf_rows, sample_limit)
            support_count = len(pcf_rows)
        elif spec["source"] == "edge.evidence_anchor_ids":
            samples = sample_edge_answers(spec, edges, node_by_id, sample_limit)
            support_count = sum(1 for edge in edges if edge.get("evidence_anchor_ids"))
        else:
            samples = sample_edge_answers(spec, edges, node_by_id, sample_limit)
            support_count = sum(predicate_counts.get(predicate, 0) for predicate in spec["predicates"])

        gap_note = ""
        if cq_id == "CQ8" and support_count == 0:
            gap_note = (
                "Current final KG has no HAS_REVIEW_CHECKPOINT edges. "
                "Review checkpoint extraction is tracked as a structural gap for human/schema follow-up."
            )
        elif not support_count:
            gap_note = "No current KG support found for this CQ."

        query_row = {
            "cq_id": cq_id,
            "question": cq.get("question") or structural.get("question") or "",
            "query_focus": spec["query_focus"],
            "required_predicates": spec["predicates"],
            "support_source": spec["source"],
            "supporting_item_count": support_count,
            "answerable_by_current_kg": bool(structural.get("answerable_by_current_kg")) if structural else support_count > 0,
            "sample_answer_count": len(samples),
            "cypher": cypher_for(spec),
            "sparql": sparql_for(spec),
            "gap_note": gap_note,
            "claim_status": "query_pack_structural_diagnostic_not_human_gold",
            "sample_answers": samples,
        }
        query_rows.append(query_row)
        for index, sample in enumerate(samples, start=1):
            answer_rows.append(
                {
                    "cq_id": cq_id,
                    "sample_rank": index,
                    "answer_type": sample.get("answer_type"),
                    "id": sample.get("id"),
                    "source_id": sample.get("source_id"),
                    "source_label": sample.get("source_label"),
                    "source_type": sample.get("source_type"),
                    "predicate": sample.get("predicate"),
                    "target_id": sample.get("target_id"),
                    "target_label": sample.get("target_label"),
                    "target_type": sample.get("target_type"),
                    "rank": sample.get("rank"),
                    "score": sample.get("score"),
                    "evidence_anchor_ids": json.dumps(sample.get("evidence_anchor_ids") or [], ensure_ascii=False),
                    "review_status": sample.get("review_status"),
                }
            )

    answerable_count = sum(1 for row in query_rows if row["answerable_by_current_kg"])
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": rel(exp_dir),
        "outputs_dir": rel(outputs_dir),
        "source_files": {
            "competency_questions": rel(exp_dir / "02_schema/competency_questions.json"),
            "layer2_nodes": rel(outputs_dir / "07_layer2_graph/layer2_nodes.jsonl"),
            "layer2_edges": rel(outputs_dir / "07_layer2_graph/layer2_edges.jsonl"),
            "ncs_mapping_candidates": rel(outputs_dir / "08_mapping/l2_ncs_mapping_candidates.jsonl"),
            "pcf_mapping_candidates": rel(outputs_dir / "08_mapping/l2_pcf_mapping_candidates.jsonl"),
            "cq_answerability_metrics": rel(exp_dir / "04_evaluation/cq_answerability_structural_metrics.json"),
        },
        "summary": {
            "cq_count": len(query_rows),
            "answerable_cq_count": answerable_count,
            "cq_answerability_rate": round(answerable_count / len(query_rows), 6) if query_rows else 0.0,
            "sample_answer_rows": len(answer_rows),
            "cq_with_no_support": [row["cq_id"] for row in query_rows if row["supporting_item_count"] == 0],
            "claim_status": "cq_query_pack_ready_not_human_gold_answer_correctness",
        },
        "queries": query_rows,
    }
    return payload, answer_rows


def render_md(payload):
    lines = [
        "# CAPE-KG CQ Query Pack",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Experiment: `{payload['experiment_dir']}`",
        "",
        "이 문서는 Competency Question(CQ)을 실제 KG query와 sample answer에 연결한 release artifact입니다.",
        "Raw source text는 포함하지 않고, node/edge/mapping label과 evidence anchor id만 포함합니다.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- {key}: `{value}`")

    lines.extend(
        [
            "",
            "## CQ Query Overview",
            "",
            "| CQ | question | support source | support | answerable | gap note |",
            "| --- | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in payload["queries"]:
        lines.append(
            f"| {row['cq_id']} | {row['question']} | `{row['support_source']}` | "
            f"{row['supporting_item_count']} | {row['answerable_by_current_kg']} | {row['gap_note']} |"
        )

    for row in payload["queries"]:
        lines.extend(
            [
                "",
                f"## {row['cq_id']}. {row['query_focus']}",
                "",
                f"- Question: {row['question']}",
                f"- Required predicates: `{', '.join(row['required_predicates'])}`",
                f"- Support source: `{row['support_source']}`",
                f"- Supporting item count: `{row['supporting_item_count']}`",
                f"- Answerable by current KG: `{row['answerable_by_current_kg']}`",
                f"- Claim status: `{row['claim_status']}`",
            ]
        )
        if row["gap_note"]:
            lines.append(f"- Gap note: {row['gap_note']}")
        lines.extend(["", "### Cypher", "", "```cypher", row["cypher"], "```", "", "### SPARQL-style Query", "", "```sparql", row["sparql"], "```"])
        lines.extend(["", "### Sample Answers", "", "| id | source | predicate | target | evidence anchors | review status |", "| --- | --- | --- | --- | --- | --- |"])
        if not row["sample_answers"]:
            lines.append("|  |  |  |  |  | no sample answer |")
        for sample in row["sample_answers"]:
            source = f"{sample.get('source_label') or ''} (`{sample.get('source_id')}`)"
            target = f"{sample.get('target_label') or ''} (`{sample.get('target_id')}`)"
            evidence = ", ".join(sample.get("evidence_anchor_ids") or [])
            lines.append(
                f"| `{sample.get('id')}` | {source} | `{sample.get('predicate')}` | {target} | {evidence} | {sample.get('review_status')} |"
            )

    unsupported = payload["summary"].get("cq_with_no_support") or []
    if unsupported:
        support_note = f"- 구조적 support가 없는 CQ: `{', '.join(unsupported)}`."
    else:
        support_note = "- 현재 12개 CQ 모두 KG predicate/support source에 의해 구조적으로 query 가능합니다."
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- 이 query pack은 CQ answerability의 구조적 근거를 사람이 재현 가능한 query 형태로 고정합니다.",
            support_note,
            "- Sample answer는 정답 claim이 아니라 현재 KG가 제공하는 구조적 evidence입니다.",
            "- 최종 CQ answer correctness는 adjudicated human-gold 이후 다시 평가해야 합니다.",
        ]
    )
    return "\n".join(lines) + "\n"


def run(args):
    payload, answer_rows = build_pack(args.experiment_dir, args.outputs_dir, args.sample_limit)
    exp_dir = Path(args.experiment_dir)
    release_dir = exp_dir / "06_release"
    eval_dir = exp_dir / "04_evaluation"
    json_path = release_dir / "cq_query_pack.json"
    md_path = release_dir / "cq_query_pack.md"
    csv_path = eval_dir / "cq_query_sample_answers.csv"
    write_json(json_path, payload)
    write_text(md_path, render_md(payload))
    write_csv(
        csv_path,
        answer_rows,
        [
            "cq_id",
            "sample_rank",
            "answer_type",
            "id",
            "source_id",
            "source_label",
            "source_type",
            "predicate",
            "target_id",
            "target_label",
            "target_type",
            "rank",
            "score",
            "evidence_anchor_ids",
            "review_status",
        ],
    )
    print(json.dumps({"json": rel(json_path), "md": rel(md_path), "csv": rel(csv_path), "summary": payload["summary"]}, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--outputs-dir", default=str(DEFAULT_OUTPUTS_DIR))
    parser.add_argument("--sample-limit", type=int, default=5)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
