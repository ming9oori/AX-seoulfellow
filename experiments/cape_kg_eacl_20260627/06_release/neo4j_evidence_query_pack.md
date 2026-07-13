# CAPE-KG Neo4j Evidence Query Pack

Generated: 2026-06-29T18:56:41.524976+00:00
Experiment: `experiments/cape_kg_eacl_20260627`
Outputs: `outputs`

이 문서는 Neo4j Browser에서 CAPE-KG의 구조와 원문 근거 연결을 확인하기 위한 실행 질의 모음입니다.
성능 claim이 아니라, 구축된 KG와 EvidenceAnchor projection이 어떤 방식으로 조회 가능한지 보여주는 재현/검수 보조 산출물입니다.

## Claim Status

- Claim status: `neo4j_evidence_query_pack_ready_not_human_gold_evidence`
- Human-gold correctness, IAA, evidence-span correctness claim은 아직 사람 검수 이후에만 가능합니다.
- EvidenceAnchor 노드는 원문 sentence text를 포함하지 않고, `sentence_id`, `chunk_id`, `page`, `span`, `text_sha256`만 포함합니다.

## Count Summary

| 항목 | 값 |
|---|---:|
| Neo4j nodes | 11028 |
| Neo4j relationships | 14455 |
| EvidenceAnchor nodes | 451 |
| KGEdgeAssertion nodes | 947 |
| EVIDENCED_BY relationships | 3915 |
| Layer2 nodes | 220 |
| Layer2 edges | 947 |
| Query count | 13 |

## Source Files

| role | path |
| --- | --- |
| neo4j_flat_manifest | outputs/11_neo4j_import_flat/manifest.json |
| neo4j_csv_validation | outputs/11_neo4j_import_flat/neo4j_csv_validation_report.json |
| evidence_graph_projection_summary | outputs/13_evidence_graph/evidence_graph_projection_summary.json |
| cq_query_pack | experiments/cape_kg_eacl_20260627/06_release/cq_query_pack.json |
| neo4j_import_cypher_http | outputs/11_neo4j_import_flat/neo4j_import_http_8765.cypher |
| neo4j_import_cypher_file | outputs/11_neo4j_import_flat/neo4j_import.cypher |

## Queries

### NQ01 전체 노드 layer/type 분포

- 목적: Layer 1, Layer 2, Evidence projection 노드가 Neo4j에 들어왔는지 확인한다.
- 관련 CQ: -
- 기대 신호: 총 노드 수가 manifest node_count=11028와 같은지 확인.

```cypher
MATCH (n:KGNode)
RETURN n.layer AS layer, n.type AS type, count(n) AS nodes
ORDER BY layer, type;
```

### NQ02 전체 relationship type 분포

- 목적: KG edge, NCS/PCF mapping edge, evidence edge가 모두 적재되었는지 확인한다.
- 관련 CQ: -
- 기대 신호: 총 relationship 수가 manifest relationship_count=14455와 같은지 확인.

```cypher
MATCH ()-[r]->()
RETURN type(r) AS relationship_type, count(r) AS relationships
ORDER BY relationships DESC, relationship_type;
```

### NQ03 Evidence projection count sanity check

- 목적: EvidenceAnchor, KGEdgeAssertion, EVIDENCED_BY 수가 projection summary와 일치하는지 확인한다.
- 관련 CQ: CQ10
- 기대 신호: 기대값: EvidenceAnchor=451, KGEdgeAssertion=947, EVIDENCED_BY=3915.

```cypher
MATCH (a:EvidenceAnchor)
WITH count(a) AS evidence_anchors
MATCH (e:KGEdgeAssertion)
WITH evidence_anchors, count(e) AS kg_edge_assertions
MATCH ()-[r:EVIDENCED_BY]->()
RETURN evidence_anchors, kg_edge_assertions, count(r) AS evidenced_by_relationships;
```

### NQ04 Layer 2 node evidence 확인

- 목적: DomainTask, ProcedureStep, Artifact 등 Layer 2 노드가 어떤 원문 anchor에 의해 지지되는지 본다.
- 관련 CQ: CQ10
- 기대 신호: Layer 2 KGNode evidence edge 기대값: 742.

```cypher
MATCH p = (n:Layer2)-[:EVIDENCED_BY]->(a:EvidenceAnchor)
RETURN p
LIMIT 25;
```

### NQ05 KG edge assertion evidence 확인

- 목적: 관계 자체를 KGEdgeAssertion 노드로 reify한 뒤, 각 관계가 어느 EvidenceAnchor에 근거하는지 본다.
- 관련 CQ: CQ10
- 기대 신호: KGEdgeAssertion evidence edge 기대값: 3173.

```cypher
MATCH (e:KGEdgeAssertion)-[:EVIDENCED_BY]->(a:EvidenceAnchor)
RETURN e.node_id AS kg_edge_id,
       e.label AS kg_edge_label,
       a.evidence_anchor_id AS evidence_anchor_id,
       a.sentence_id AS sentence_id,
       a.chunk_id AS chunk_id,
       a.page AS page,
       a.text_included AS text_included,
       a.text_sha256 AS text_sha256
LIMIT 25;
```

### NQ06 절차 구성과 원문 근거 같이 보기

- 목적: Task -> Step 구조와 Step evidence anchor를 함께 확인한다.
- 관련 CQ: CQ1, CQ10
- 기대 신호: Task/Step graph가 원문 anchor까지 이어져야 한다.

```cypher
MATCH p = (task:Layer2 {type: 'DomainTask'})-[:HAS_STEP]->(step:Layer2)-[:EVIDENCED_BY]->(a:EvidenceAnchor)
RETURN p
LIMIT 25;
```

### NQ07 산출물 흐름 관계와 관계 근거 같이 보기

- 목적: USES_INPUT/PRODUCES/FEEDS_INTO/USED_AS_INPUT_FOR 관계의 rel_id를 reified KGEdgeAssertion과 연결해 근거 anchor를 확인한다.
- 관련 CQ: CQ2, CQ3, CQ7, CQ10
- 기대 신호: Artifact-flow edge와 EvidenceAnchor가 같이 반환되어야 한다.

```cypher
MATCH (s:KGNode)-[r:USES_INPUT|PRODUCES|FEEDS_INTO|USED_AS_INPUT_FOR]->(t:KGNode)
MATCH (edge:KGEdgeAssertion {node_id: r.rel_id})-[:EVIDENCED_BY]->(a:EvidenceAnchor)
RETURN s.label AS source,
       type(r) AS predicate,
       t.label AS target,
       edge.node_id AS kg_edge_id,
       a.evidence_anchor_id AS evidence_anchor_id,
       a.chunk_id AS chunk_id,
       a.page AS page
LIMIT 25;
```

### NQ08 CQ predicate coverage

- 목적: CQ pack에서 쓰는 핵심 predicate별 edge 수를 Neo4j에서 확인한다.
- 관련 CQ: CQ1, CQ2, CQ3, CQ4, CQ5, CQ6, CQ7, CQ8, CQ9, CQ10, CQ11, CQ12
- 기대 신호: CQ pack 기준 answerable CQ=12/12. Predicate별 count가 release CQ pack과 일치해야 한다.

```cypher
MATCH ()-[r]->()
WHERE type(r) IN ["HAS_STEP", "PRECEDES", "USES_INPUT", "PRODUCES", "PERFORMED_BY", "HAS_DECISION_GATEWAY", "HAS_GUARD_CONDITION", "FEEDS_INTO", "USED_AS_INPUT_FOR", "HAS_PRINCIPLE", "REQUIRES_CAPABILITY", "PROCESS_CONTEXT"]
RETURN type(r) AS predicate, count(r) AS edges
ORDER BY predicate;
```

### NQ09 NCS mapping 후보 확인

- 목적: Layer 2 task와 NCS capability 후보의 rank/score/reason을 확인한다.
- 관련 CQ: CQ11
- 기대 신호: REQUIRES_CAPABILITY 후보 edge 기대값: 110.

```cypher
MATCH (task:KGNode:Layer2)-[r:REQUIRES_CAPABILITY]->(ncs:KGNode:Layer1NCS)
RETURN task.node_id AS task_id,
       task.label AS task_label,
       ncs.node_id AS ncs_id,
       ncs.label AS ncs_label,
       r.rank AS rank,
       r.score AS score,
       r.reason AS reason
ORDER BY task_id, rank
LIMIT 50;
```

### NQ10 PCF mapping 후보 확인

- 목적: Layer 2 task와 PCF process context 후보의 rank/score/reason을 확인한다.
- 관련 CQ: CQ12
- 기대 신호: PROCESS_CONTEXT 후보 edge 기대값: 110.

```cypher
MATCH (task:KGNode:Layer2)-[r:PROCESS_CONTEXT]->(pcf:KGNode:Layer1PCF)
RETURN task.node_id AS task_id,
       task.label AS task_label,
       pcf.node_id AS pcf_id,
       pcf.label AS pcf_label,
       r.rank AS rank,
       r.score AS score,
       r.reason AS reason
ORDER BY task_id, rank
LIMIT 50;
```

### NQ11 원문 텍스트 비포함 상태 확인

- 목적: EvidenceAnchor에는 원문 문장이 아닌 sentence/chunk/page/span/hash만 들어갔는지 확인한다.
- 관련 CQ: CQ10
- 기대 신호: source_text_included=False이어야 한다.

```cypher
MATCH (a:EvidenceAnchor)
RETURN a.text_included AS text_included,
       count(a) AS evidence_anchors,
       min(a.text_char_count) AS min_text_chars,
       max(a.text_char_count) AS max_text_chars
ORDER BY text_included;
```

### NQ12 고립 EvidenceAnchor 확인

- 목적: 현재 Neo4j projection에 들어온 EvidenceAnchor가 모두 최소 하나의 KGNode/KGEdgeAssertion에서 참조되는지 확인한다.
- 관련 CQ: CQ10
- 기대 신호: 사용된 anchor만 projection했으므로 0이어야 한다.

```cypher
MATCH (a:EvidenceAnchor)
WHERE NOT ()-[:EVIDENCED_BY]->(a)
RETURN count(a) AS unreferenced_evidence_anchors;
```

### NQ13 대표 Task 주변 그래프 탐색

- 목적: 기회분석 task 주변의 step/artifact/role/evidence 연결을 Neo4j Browser graph view로 본다.
- 관련 CQ: CQ1, CQ2, CQ3, CQ4, CQ10
- 기대 신호: 대표 task의 절차, 산출물, 근거 연결이 graph view에 표시되어야 한다.

```cypher
MATCH p = (:Layer2 {node_id: 'L2_TASK_OPPORTUNITY_ASSESSMENT'})-[*1..2]->()
RETURN p
LIMIT 50;
```

## Browser 사용 순서

1. `outputs/11_neo4j_import_flat/neo4j_import_http_8765.cypher` 또는 `neo4j_import.cypher`로 CSV를 먼저 적재합니다.
2. `outputs/11_neo4j_import_flat/neo4j_evidence_queries.cypher`에서 필요한 query block을 Neo4j Browser에 붙여 넣습니다.
3. `RETURN p` 형태의 질의는 Browser의 graph view로 전환해 시각적으로 확인합니다.
