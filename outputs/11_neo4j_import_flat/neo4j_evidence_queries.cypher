// CAPE-KG Neo4j Evidence Query Pack
// Generated: 2026-06-29T18:56:41.524976+00:00
// Run after importing outputs/11_neo4j_import_flat/*.csv.
// Each query is independent; paste one block at a time in Neo4j Browser if the Browser only executes a single statement.

// NQ01 전체 노드 layer/type 분포
// Layer 1, Layer 2, Evidence projection 노드가 Neo4j에 들어왔는지 확인한다.
MATCH (n:KGNode)
RETURN n.layer AS layer, n.type AS type, count(n) AS nodes
ORDER BY layer, type;

// NQ02 전체 relationship type 분포
// KG edge, NCS/PCF mapping edge, evidence edge가 모두 적재되었는지 확인한다.
MATCH ()-[r]->()
RETURN type(r) AS relationship_type, count(r) AS relationships
ORDER BY relationships DESC, relationship_type;

// NQ03 Evidence projection count sanity check
// EvidenceAnchor, KGEdgeAssertion, EVIDENCED_BY 수가 projection summary와 일치하는지 확인한다.
MATCH (a:EvidenceAnchor)
WITH count(a) AS evidence_anchors
MATCH (e:KGEdgeAssertion)
WITH evidence_anchors, count(e) AS kg_edge_assertions
MATCH ()-[r:EVIDENCED_BY]->()
RETURN evidence_anchors, kg_edge_assertions, count(r) AS evidenced_by_relationships;

// NQ04 Layer 2 node evidence 확인
// DomainTask, ProcedureStep, Artifact 등 Layer 2 노드가 어떤 원문 anchor에 의해 지지되는지 본다.
MATCH p = (n:Layer2)-[:EVIDENCED_BY]->(a:EvidenceAnchor)
RETURN p
LIMIT 25;

// NQ05 KG edge assertion evidence 확인
// 관계 자체를 KGEdgeAssertion 노드로 reify한 뒤, 각 관계가 어느 EvidenceAnchor에 근거하는지 본다.
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

// NQ06 절차 구성과 원문 근거 같이 보기
// Task -> Step 구조와 Step evidence anchor를 함께 확인한다.
MATCH p = (task:Layer2 {type: 'DomainTask'})-[:HAS_STEP]->(step:Layer2)-[:EVIDENCED_BY]->(a:EvidenceAnchor)
RETURN p
LIMIT 25;

// NQ07 산출물 흐름 관계와 관계 근거 같이 보기
// USES_INPUT/PRODUCES/FEEDS_INTO/USED_AS_INPUT_FOR 관계의 rel_id를 reified KGEdgeAssertion과 연결해 근거 anchor를 확인한다.
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

// NQ08 CQ predicate coverage
// CQ pack에서 쓰는 핵심 predicate별 edge 수를 Neo4j에서 확인한다.
MATCH ()-[r]->()
WHERE type(r) IN ["HAS_STEP", "PRECEDES", "USES_INPUT", "PRODUCES", "PERFORMED_BY", "HAS_DECISION_GATEWAY", "HAS_GUARD_CONDITION", "FEEDS_INTO", "USED_AS_INPUT_FOR", "HAS_PRINCIPLE", "REQUIRES_CAPABILITY", "PROCESS_CONTEXT"]
RETURN type(r) AS predicate, count(r) AS edges
ORDER BY predicate;

// NQ09 NCS mapping 후보 확인
// Layer 2 task와 NCS capability 후보의 rank/score/reason을 확인한다.
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

// NQ10 PCF mapping 후보 확인
// Layer 2 task와 PCF process context 후보의 rank/score/reason을 확인한다.
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

// NQ11 원문 텍스트 비포함 상태 확인
// EvidenceAnchor에는 원문 문장이 아닌 sentence/chunk/page/span/hash만 들어갔는지 확인한다.
MATCH (a:EvidenceAnchor)
RETURN a.text_included AS text_included,
       count(a) AS evidence_anchors,
       min(a.text_char_count) AS min_text_chars,
       max(a.text_char_count) AS max_text_chars
ORDER BY text_included;

// NQ12 고립 EvidenceAnchor 확인
// 현재 Neo4j projection에 들어온 EvidenceAnchor가 모두 최소 하나의 KGNode/KGEdgeAssertion에서 참조되는지 확인한다.
MATCH (a:EvidenceAnchor)
WHERE NOT ()-[:EVIDENCED_BY]->(a)
RETURN count(a) AS unreferenced_evidence_anchors;

// NQ13 대표 Task 주변 그래프 탐색
// 기회분석 task 주변의 step/artifact/role/evidence 연결을 Neo4j Browser graph view로 본다.
MATCH p = (:Layer2 {node_id: 'L2_TASK_OPPORTUNITY_ASSESSMENT'})-[*1..2]->()
RETURN p
LIMIT 50;
