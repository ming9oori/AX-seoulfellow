#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build Neo4j Browser query pack for CAPE-KG evidence projection."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_OUTPUTS_DIR = Path("outputs")


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


def rel(path):
    return str(Path(path).as_posix())


def md_table(headers, rows):
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        values = []
        for header in headers:
            value = row.get(header, "")
            if isinstance(value, list):
                value = ", ".join(str(v) for v in value)
            values.append(str(value).replace("|", "\\|").replace("\n", " "))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def query(query_id, title_ko, purpose_ko, cypher, expected_signal, source_cq_ids=None):
    return {
        "query_id": query_id,
        "title_ko": title_ko,
        "purpose_ko": purpose_ko,
        "source_cq_ids": source_cq_ids or [],
        "cypher": cypher.strip() + ";",
        "expected_signal": expected_signal,
        "claim_status": "neo4j_structural_or_evidence_diagnostic_not_human_gold_claim",
    }


def build_queries(manifest, evidence_summary, cq_pack):
    relationship_types = manifest.get("relationship_types") or {}
    expected = {
        "node_count": manifest.get("node_count"),
        "relationship_count": manifest.get("relationship_count"),
        "evidence_anchor_node_count": manifest.get("evidence_anchor_node_count"),
        "kg_edge_assertion_node_count": manifest.get("kg_edge_assertion_node_count"),
        "evidenced_by_relationship_count": relationship_types.get("EVIDENCED_BY"),
        "layer2_node_count": evidence_summary.get("layer2_node_count"),
        "layer2_edge_count": evidence_summary.get("layer2_edge_count"),
        "kg_node_evidenced_by_edge_count": evidence_summary.get("kg_node_evidenced_by_edge_count"),
        "kg_edge_evidenced_by_edge_count": evidence_summary.get("kg_edge_evidenced_by_edge_count"),
        "cq_count": (cq_pack.get("summary") or {}).get("cq_count"),
        "answerable_cq_count": (cq_pack.get("summary") or {}).get("answerable_cq_count"),
    }
    cq_edge_predicates = [
        "HAS_STEP",
        "PRECEDES",
        "USES_INPUT",
        "PRODUCES",
        "PERFORMED_BY",
        "HAS_DECISION_GATEWAY",
        "HAS_GUARD_CONDITION",
        "FEEDS_INTO",
        "USED_AS_INPUT_FOR",
        "HAS_PRINCIPLE",
        "REQUIRES_CAPABILITY",
        "PROCESS_CONTEXT",
    ]
    return [
        query(
            "NQ01",
            "전체 노드 layer/type 분포",
            "Layer 1, Layer 2, Evidence projection 노드가 Neo4j에 들어왔는지 확인한다.",
            """
MATCH (n:KGNode)
RETURN n.layer AS layer, n.type AS type, count(n) AS nodes
ORDER BY layer, type
""",
            f"총 노드 수가 manifest node_count={expected['node_count']}와 같은지 확인.",
        ),
        query(
            "NQ02",
            "전체 relationship type 분포",
            "KG edge, NCS/PCF mapping edge, evidence edge가 모두 적재되었는지 확인한다.",
            """
MATCH ()-[r]->()
RETURN type(r) AS relationship_type, count(r) AS relationships
ORDER BY relationships DESC, relationship_type
""",
            f"총 relationship 수가 manifest relationship_count={expected['relationship_count']}와 같은지 확인.",
        ),
        query(
            "NQ03",
            "Evidence projection count sanity check",
            "EvidenceAnchor, KGEdgeAssertion, EVIDENCED_BY 수가 projection summary와 일치하는지 확인한다.",
            """
MATCH (a:EvidenceAnchor)
WITH count(a) AS evidence_anchors
MATCH (e:KGEdgeAssertion)
WITH evidence_anchors, count(e) AS kg_edge_assertions
MATCH ()-[r:EVIDENCED_BY]->()
RETURN evidence_anchors, kg_edge_assertions, count(r) AS evidenced_by_relationships
""",
            (
                "기대값: "
                f"EvidenceAnchor={expected['evidence_anchor_node_count']}, "
                f"KGEdgeAssertion={expected['kg_edge_assertion_node_count']}, "
                f"EVIDENCED_BY={expected['evidenced_by_relationship_count']}."
            ),
            ["CQ10"],
        ),
        query(
            "NQ04",
            "Layer 2 node evidence 확인",
            "DomainTask, ProcedureStep, Artifact 등 Layer 2 노드가 어떤 원문 anchor에 의해 지지되는지 본다.",
            """
MATCH p = (n:Layer2)-[:EVIDENCED_BY]->(a:EvidenceAnchor)
RETURN p
LIMIT 25
""",
            f"Layer 2 KGNode evidence edge 기대값: {expected['kg_node_evidenced_by_edge_count']}.",
            ["CQ10"],
        ),
        query(
            "NQ05",
            "KG edge assertion evidence 확인",
            "관계 자체를 KGEdgeAssertion 노드로 reify한 뒤, 각 관계가 어느 EvidenceAnchor에 근거하는지 본다.",
            """
MATCH (e:KGEdgeAssertion)-[:EVIDENCED_BY]->(a:EvidenceAnchor)
RETURN e.node_id AS kg_edge_id,
       e.label AS kg_edge_label,
       a.evidence_anchor_id AS evidence_anchor_id,
       a.sentence_id AS sentence_id,
       a.chunk_id AS chunk_id,
       a.page AS page,
       a.text_included AS text_included,
       a.text_sha256 AS text_sha256
LIMIT 25
""",
            f"KGEdgeAssertion evidence edge 기대값: {expected['kg_edge_evidenced_by_edge_count']}.",
            ["CQ10"],
        ),
        query(
            "NQ06",
            "절차 구성과 원문 근거 같이 보기",
            "Task -> Step 구조와 Step evidence anchor를 함께 확인한다.",
            """
MATCH p = (task:Layer2 {type: 'DomainTask'})-[:HAS_STEP]->(step:Layer2)-[:EVIDENCED_BY]->(a:EvidenceAnchor)
RETURN p
LIMIT 25
""",
            "Task/Step graph가 원문 anchor까지 이어져야 한다.",
            ["CQ1", "CQ10"],
        ),
        query(
            "NQ07",
            "산출물 흐름 관계와 관계 근거 같이 보기",
            "USES_INPUT/PRODUCES/FEEDS_INTO/USED_AS_INPUT_FOR 관계의 rel_id를 reified KGEdgeAssertion과 연결해 근거 anchor를 확인한다.",
            """
MATCH (s:KGNode)-[r:USES_INPUT|PRODUCES|FEEDS_INTO|USED_AS_INPUT_FOR]->(t:KGNode)
MATCH (edge:KGEdgeAssertion {node_id: r.rel_id})-[:EVIDENCED_BY]->(a:EvidenceAnchor)
RETURN s.label AS source,
       type(r) AS predicate,
       t.label AS target,
       edge.node_id AS kg_edge_id,
       a.evidence_anchor_id AS evidence_anchor_id,
       a.chunk_id AS chunk_id,
       a.page AS page
LIMIT 25
""",
            "Artifact-flow edge와 EvidenceAnchor가 같이 반환되어야 한다.",
            ["CQ2", "CQ3", "CQ7", "CQ10"],
        ),
        query(
            "NQ08",
            "CQ predicate coverage",
            "CQ pack에서 쓰는 핵심 predicate별 edge 수를 Neo4j에서 확인한다.",
            f"""
MATCH ()-[r]->()
WHERE type(r) IN {json.dumps(cq_edge_predicates)}
RETURN type(r) AS predicate, count(r) AS edges
ORDER BY predicate
""",
            f"CQ pack 기준 answerable CQ={expected['answerable_cq_count']}/{expected['cq_count']}. Predicate별 count가 release CQ pack과 일치해야 한다.",
            [f"CQ{i}" for i in range(1, 13)],
        ),
        query(
            "NQ09",
            "NCS mapping 후보 확인",
            "Layer 2 task와 NCS capability 후보의 rank/score/reason을 확인한다.",
            """
MATCH (task:KGNode:Layer2)-[r:REQUIRES_CAPABILITY]->(ncs:KGNode:Layer1NCS)
RETURN task.node_id AS task_id,
       task.label AS task_label,
       ncs.node_id AS ncs_id,
       ncs.label AS ncs_label,
       r.rank AS rank,
       r.score AS score,
       r.reason AS reason
ORDER BY task_id, rank
LIMIT 50
""",
            f"REQUIRES_CAPABILITY 후보 edge 기대값: {relationship_types.get('REQUIRES_CAPABILITY')}.",
            ["CQ11"],
        ),
        query(
            "NQ10",
            "PCF mapping 후보 확인",
            "Layer 2 task와 PCF process context 후보의 rank/score/reason을 확인한다.",
            """
MATCH (task:KGNode:Layer2)-[r:PROCESS_CONTEXT]->(pcf:KGNode:Layer1PCF)
RETURN task.node_id AS task_id,
       task.label AS task_label,
       pcf.node_id AS pcf_id,
       pcf.label AS pcf_label,
       r.rank AS rank,
       r.score AS score,
       r.reason AS reason
ORDER BY task_id, rank
LIMIT 50
""",
            f"PROCESS_CONTEXT 후보 edge 기대값: {relationship_types.get('PROCESS_CONTEXT')}.",
            ["CQ12"],
        ),
        query(
            "NQ11",
            "원문 텍스트 비포함 상태 확인",
            "EvidenceAnchor에는 원문 문장이 아닌 sentence/chunk/page/span/hash만 들어갔는지 확인한다.",
            """
MATCH (a:EvidenceAnchor)
RETURN a.text_included AS text_included,
       count(a) AS evidence_anchors,
       min(a.text_char_count) AS min_text_chars,
       max(a.text_char_count) AS max_text_chars
ORDER BY text_included
""",
            f"source_text_included={evidence_summary.get('source_text_included')}이어야 한다.",
            ["CQ10"],
        ),
        query(
            "NQ12",
            "고립 EvidenceAnchor 확인",
            "현재 Neo4j projection에 들어온 EvidenceAnchor가 모두 최소 하나의 KGNode/KGEdgeAssertion에서 참조되는지 확인한다.",
            """
MATCH (a:EvidenceAnchor)
WHERE NOT ()-[:EVIDENCED_BY]->(a)
RETURN count(a) AS unreferenced_evidence_anchors
""",
            "사용된 anchor만 projection했으므로 0이어야 한다.",
            ["CQ10"],
        ),
        query(
            "NQ13",
            "대표 Task 주변 그래프 탐색",
            "기회분석 task 주변의 step/artifact/role/evidence 연결을 Neo4j Browser graph view로 본다.",
            """
MATCH p = (:Layer2 {node_id: 'L2_TASK_OPPORTUNITY_ASSESSMENT'})-[*1..2]->()
RETURN p
LIMIT 50
""",
            "대표 task의 절차, 산출물, 근거 연결이 graph view에 표시되어야 한다.",
            ["CQ1", "CQ2", "CQ3", "CQ4", "CQ10"],
        ),
    ]


def render_markdown(payload):
    summary = payload["summary"]
    lines = [
        "# CAPE-KG Neo4j Evidence Query Pack",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Experiment: `{payload['experiment_dir']}`",
        f"Outputs: `{payload['outputs_dir']}`",
        "",
        "이 문서는 Neo4j Browser에서 CAPE-KG의 구조와 원문 근거 연결을 확인하기 위한 실행 질의 모음입니다.",
        "성능 claim이 아니라, 구축된 KG와 EvidenceAnchor projection이 어떤 방식으로 조회 가능한지 보여주는 재현/검수 보조 산출물입니다.",
        "",
        "## Claim Status",
        "",
        f"- Claim status: `{payload['claim_status']}`",
        "- Human-gold correctness, IAA, evidence-span correctness claim은 아직 사람 검수 이후에만 가능합니다.",
        "- EvidenceAnchor 노드는 원문 sentence text를 포함하지 않고, `sentence_id`, `chunk_id`, `page`, `span`, `text_sha256`만 포함합니다.",
        "",
        "## Count Summary",
        "",
        "| 항목 | 값 |",
        "|---|---:|",
        f"| Neo4j nodes | {summary.get('neo4j_node_count')} |",
        f"| Neo4j relationships | {summary.get('neo4j_relationship_count')} |",
        f"| EvidenceAnchor nodes | {summary.get('evidence_anchor_node_count')} |",
        f"| KGEdgeAssertion nodes | {summary.get('kg_edge_assertion_node_count')} |",
        f"| EVIDENCED_BY relationships | {summary.get('evidenced_by_relationship_count')} |",
        f"| Layer2 nodes | {summary.get('layer2_node_count')} |",
        f"| Layer2 edges | {summary.get('layer2_edge_count')} |",
        f"| Query count | {summary.get('query_count')} |",
        "",
        "## Source Files",
        "",
        md_table(["role", "path"], payload["source_files"]),
        "",
        "## Queries",
        "",
    ]
    for item in payload["queries"]:
        cq_text = ", ".join(item.get("source_cq_ids") or []) or "-"
        lines += [
            f"### {item['query_id']} {item['title_ko']}",
            "",
            f"- 목적: {item['purpose_ko']}",
            f"- 관련 CQ: {cq_text}",
            f"- 기대 신호: {item['expected_signal']}",
            "",
            "```cypher",
            item["cypher"],
            "```",
            "",
        ]
    lines += [
        "## Browser 사용 순서",
        "",
        "1. `outputs/11_neo4j_import_flat/neo4j_import_http_8765.cypher` 또는 `neo4j_import.cypher`로 CSV를 먼저 적재합니다.",
        "2. `outputs/11_neo4j_import_flat/neo4j_evidence_queries.cypher`에서 필요한 query block을 Neo4j Browser에 붙여 넣습니다.",
        "3. `RETURN p` 형태의 질의는 Browser의 graph view로 전환해 시각적으로 확인합니다.",
        "",
    ]
    return "\n".join(lines)


def render_cypher(payload):
    lines = [
        "// CAPE-KG Neo4j Evidence Query Pack",
        f"// Generated: {payload['generated_at_utc']}",
        "// Run after importing outputs/11_neo4j_import_flat/*.csv.",
        "// Each query is independent; paste one block at a time in Neo4j Browser if the Browser only executes a single statement.",
        "",
    ]
    for item in payload["queries"]:
        lines += [
            f"// {item['query_id']} {item['title_ko']}",
            "// " + item["purpose_ko"],
            item["cypher"],
            "",
        ]
    return "\n".join(lines)


def build_payload(exp_dir, outputs_dir):
    exp_dir = Path(exp_dir)
    outputs_dir = Path(outputs_dir)
    release_dir = exp_dir / "06_release"
    flat_dir = outputs_dir / "11_neo4j_import_flat"
    manifest_path = flat_dir / "manifest.json"
    validation_path = flat_dir / "neo4j_csv_validation_report.json"
    evidence_summary_path = outputs_dir / "13_evidence_graph/evidence_graph_projection_summary.json"
    cq_pack_path = release_dir / "cq_query_pack.json"
    manifest = read_json(manifest_path, {}) or {}
    validation = read_json(validation_path, {}) or {}
    evidence_summary = read_json(evidence_summary_path, {}) or {}
    cq_pack = read_json(cq_pack_path, {}) or {}
    relationship_types = manifest.get("relationship_types") or {}
    queries = build_queries(manifest, evidence_summary, cq_pack)
    source_files = [
        {"role": "neo4j_flat_manifest", "path": rel(manifest_path)},
        {"role": "neo4j_csv_validation", "path": rel(validation_path)},
        {"role": "evidence_graph_projection_summary", "path": rel(evidence_summary_path)},
        {"role": "cq_query_pack", "path": rel(cq_pack_path)},
        {"role": "neo4j_import_cypher_http", "path": rel(flat_dir / "neo4j_import_http_8765.cypher")},
        {"role": "neo4j_import_cypher_file", "path": rel(flat_dir / "neo4j_import.cypher")},
    ]
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": rel(exp_dir),
        "outputs_dir": rel(outputs_dir),
        "claim_status": "neo4j_evidence_query_pack_ready_not_human_gold_evidence",
        "summary": {
            "neo4j_node_count": manifest.get("node_count"),
            "neo4j_relationship_count": manifest.get("relationship_count"),
            "neo4j_validation_status": validation.get("overall_status"),
            "neo4j_validation_issue_count": validation.get("issue_count"),
            "relationship_type_count": len(relationship_types),
            "evidence_anchor_node_count": manifest.get("evidence_anchor_node_count"),
            "kg_edge_assertion_node_count": manifest.get("kg_edge_assertion_node_count"),
            "evidenced_by_relationship_count": relationship_types.get("EVIDENCED_BY"),
            "layer2_node_count": evidence_summary.get("layer2_node_count"),
            "layer2_edge_count": evidence_summary.get("layer2_edge_count"),
            "source_text_included": evidence_summary.get("source_text_included"),
            "cq_count": (cq_pack.get("summary") or {}).get("cq_count"),
            "answerable_cq_count": (cq_pack.get("summary") or {}).get("answerable_cq_count"),
            "query_count": len(queries),
        },
        "source_files": source_files,
        "queries": queries,
        "outputs": {
            "json": rel(release_dir / "neo4j_evidence_query_pack.json"),
            "markdown": rel(release_dir / "neo4j_evidence_query_pack.md"),
            "cypher": rel(flat_dir / "neo4j_evidence_queries.cypher"),
        },
    }
    return payload


def run(args):
    payload = build_payload(args.experiment_dir, args.outputs_dir)
    outputs = payload["outputs"]
    write_json(outputs["json"], payload)
    write_text(outputs["markdown"], render_markdown(payload))
    write_text(outputs["cypher"], render_cypher(payload))
    print(json.dumps(outputs, ensure_ascii=False, indent=2))


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--outputs-dir", default=str(DEFAULT_OUTPUTS_DIR))
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
