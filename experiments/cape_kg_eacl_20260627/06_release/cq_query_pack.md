# CAPE-KG CQ Query Pack

Generated: 2026-06-29T18:55:48.189844+00:00
Experiment: `experiments/cape_kg_eacl_20260627`

이 문서는 Competency Question(CQ)을 실제 KG query와 sample answer에 연결한 release artifact입니다.
Raw source text는 포함하지 않고, node/edge/mapping label과 evidence anchor id만 포함합니다.

## Summary

- cq_count: `12`
- answerable_cq_count: `12`
- cq_answerability_rate: `1.0`
- sample_answer_rows: `60`
- cq_with_no_support: `[]`
- claim_status: `cq_query_pack_ready_not_human_gold_answer_correctness`

## CQ Query Overview

| CQ | question | support source | support | answerable | gap note |
| --- | --- | --- | ---: | --- | --- |
| CQ1 | 수주·제안 업무는 어떤 주요 Task와 절차 단계로 구성되는가? | `layer2_edges` | 176 | True |  |
| CQ2 | 각 Task는 어떤 입력 자료를 사용하는가? | `layer2_edges` | 201 | True |  |
| CQ3 | 각 Task는 어떤 산출물을 생성하는가? | `layer2_edges` | 220 | True |  |
| CQ4 | 각 Task는 누가 수행하거나 책임지는가? | `layer2_edges` | 120 | True |  |
| CQ5 | 어떤 의사결정 지점이 존재하는가? | `layer2_edges` | 54 | True |  |
| CQ6 | 의사결정에는 어떤 조건이나 판단 기준이 필요한가? | `layer2_edges` | 14 | True |  |
| CQ7 | 산출물은 다음 업무에서 어떻게 사용되는가? | `layer2_edges` | 18 | True |  |
| CQ8 | 제안서 리뷰는 어떤 단계에서 어떻게 수행되는가? | `layer2_edges` | 41 | True |  |
| CQ9 | 각 업무에서 지켜야 할 원칙은 무엇인가? | `layer2_edges` | 64 | True |  |
| CQ10 | 각 지식 항목은 원문 어느 chunk/page/span에 근거가 있는가? | `edge.evidence_anchor_ids` | 947 | True |  |
| CQ11 | 특정 업무는 어떤 NCS 능력단위와 관련되는가? | `l2_ncs_mapping_candidates` | 110 | True |  |
| CQ12 | 특정 업무는 PCF 프로세스 체계상 어디에 위치하는가? | `l2_pcf_mapping_candidates` | 110 | True |  |

## CQ1. Task and procedure-step composition/order

- Question: 수주·제안 업무는 어떤 주요 Task와 절차 단계로 구성되는가?
- Required predicates: `HAS_STEP, PRECEDES`
- Support source: `layer2_edges`
- Supporting item count: `176`
- Answerable by current KG: `True`
- Claim status: `query_pack_structural_diagnostic_not_human_gold`

### Cypher

```cypher
MATCH (s:KGNode)-[r:HAS_STEP|PRECEDES]->(t:KGNode)
RETURN s.node_id AS source_id, s.label AS source_label, labels(s) AS source_labels,
       type(r) AS predicate,
       t.node_id AS target_id, t.label AS target_label, labels(t) AS target_labels,
       r.evidence_anchor_ids_json AS evidence_anchor_ids
LIMIT 25;
```

### SPARQL-style Query

```sparql
PREFIX cape: <https://example.org/cape-kg#>
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?edge ?predicate ?source ?target ?evidenceAnchorId WHERE {
  VALUES ?predicate { "HAS_STEP" "PRECEDES" }
  ?edge a cape:KGEdge ; cape:predicate ?predicate ;
        cape:sourceNode ?source ; cape:targetNode ?target .
  OPTIONAL {
    ?edge prov:wasDerivedFrom ?evidence .
    ?evidence cape:evidenceAnchorId ?evidenceAnchorId .
  }
}
LIMIT 25
```

### Sample Answers

| id | source | predicate | target | evidence anchors | review status |
| --- | --- | --- | --- | --- | --- |
| `EDGE-2ea7b6844813b69d` | 기회분석 (`L2_TASK_OPPORTUNITY_ASSESSMENT`) | `HAS_STEP` | Capture Plan 검토 (`STEP-OPPORTUNITY_ASSESSMENT-01`) | EA-JS-00235 | accepted_by_rule |
| `EDGE-cae313125103de8e` | 기회분석 (`L2_TASK_OPPORTUNITY_ASSESSMENT`) | `HAS_STEP` | 제안전략 검토 (`STEP-OPPORTUNITY_ASSESSMENT-02`) | EA-JS-00235 | accepted_by_rule |
| `EDGE-d74557fac4835dda` | Capture Plan 검토 (`STEP-OPPORTUNITY_ASSESSMENT-01`) | `PRECEDES` | 제안전략 검토 (`STEP-OPPORTUNITY_ASSESSMENT-02`) | EA-JS-00235 | accepted_by_rule |
| `EDGE-614f999dc447e519` | 기회분석 (`L2_TASK_OPPORTUNITY_ASSESSMENT`) | `HAS_STEP` | 제안 요청서 작성 (`STEP-OPPORTUNITY_ASSESSMENT-03`) | EA-JS-00470 | accepted_by_rule |
| `EDGE-cb261f05b340edff` | 제안전략 검토 (`STEP-OPPORTUNITY_ASSESSMENT-02`) | `PRECEDES` | 제안 요청서 작성 (`STEP-OPPORTUNITY_ASSESSMENT-03`) | EA-JS-00470 | accepted_by_rule |

## CQ2. Input artifacts used by tasks/steps

- Question: 각 Task는 어떤 입력 자료를 사용하는가?
- Required predicates: `USES_INPUT`
- Support source: `layer2_edges`
- Supporting item count: `201`
- Answerable by current KG: `True`
- Claim status: `query_pack_structural_diagnostic_not_human_gold`

### Cypher

```cypher
MATCH (s:KGNode)-[r:USES_INPUT]->(t:KGNode)
RETURN s.node_id AS source_id, s.label AS source_label, labels(s) AS source_labels,
       type(r) AS predicate,
       t.node_id AS target_id, t.label AS target_label, labels(t) AS target_labels,
       r.evidence_anchor_ids_json AS evidence_anchor_ids
LIMIT 25;
```

### SPARQL-style Query

```sparql
PREFIX cape: <https://example.org/cape-kg#>
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?edge ?predicate ?source ?target ?evidenceAnchorId WHERE {
  VALUES ?predicate { "USES_INPUT" }
  ?edge a cape:KGEdge ; cape:predicate ?predicate ;
        cape:sourceNode ?source ; cape:targetNode ?target .
  OPTIONAL {
    ?edge prov:wasDerivedFrom ?evidence .
    ?evidence cape:evidenceAnchorId ?evidenceAnchorId .
  }
}
LIMIT 25
```

### Sample Answers

| id | source | predicate | target | evidence anchors | review status |
| --- | --- | --- | --- | --- | --- |
| `EDGE-257c3380629f4d96` | 기회분석 (`L2_TASK_OPPORTUNITY_ASSESSMENT`) | `USES_INPUT` | Capture Plan (`L2_ARTIFACT_ARTIFACT_CAPTURE_PLAN`) | EA-JS-00235, EA-JS-00251 | accepted_by_rule |
| `EDGE-9fe97ab8661898c6` | 기회분석 (`L2_TASK_OPPORTUNITY_ASSESSMENT`) | `USES_INPUT` | 제안전략 (`L2_ARTIFACT_ARTIFACT_PROPOSAL_STRATEGY`) | EA-JS-00275 | accepted_by_rule |
| `EDGE-76ee7bd1733b6063` | 기회분석 (`L2_TASK_OPPORTUNITY_ASSESSMENT`) | `USES_INPUT` | 수주전략 (`L2_ARTIFACT_ARTIFACT_CAPTURE_STRATEGY`) | EA-JS-00275 | accepted_by_rule |
| `EDGE-e4f9a039b8f0bac1` | 기회분석 (`L2_TASK_OPPORTUNITY_ASSESSMENT`) | `USES_INPUT` | 제안서 (`L2_ARTIFACT_ARTIFACT_PROPOSAL`) | EA-JS-00251, EA-JS-00275 | accepted_by_rule |
| `EDGE-7ca0657bc4178067` | 기회분석 (`L2_TASK_OPPORTUNITY_ASSESSMENT`) | `USES_INPUT` | 발표자료 (`L2_ARTIFACT_ARTIFACT_PRESENTATION`) | EA-JS-00235, EA-JS-00251, EA-JS-00275 | accepted_by_rule |

## CQ3. Output artifacts produced by tasks/steps

- Question: 각 Task는 어떤 산출물을 생성하는가?
- Required predicates: `PRODUCES`
- Support source: `layer2_edges`
- Supporting item count: `220`
- Answerable by current KG: `True`
- Claim status: `query_pack_structural_diagnostic_not_human_gold`

### Cypher

```cypher
MATCH (s:KGNode)-[r:PRODUCES]->(t:KGNode)
RETURN s.node_id AS source_id, s.label AS source_label, labels(s) AS source_labels,
       type(r) AS predicate,
       t.node_id AS target_id, t.label AS target_label, labels(t) AS target_labels,
       r.evidence_anchor_ids_json AS evidence_anchor_ids
LIMIT 25;
```

### SPARQL-style Query

```sparql
PREFIX cape: <https://example.org/cape-kg#>
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?edge ?predicate ?source ?target ?evidenceAnchorId WHERE {
  VALUES ?predicate { "PRODUCES" }
  ?edge a cape:KGEdge ; cape:predicate ?predicate ;
        cape:sourceNode ?source ; cape:targetNode ?target .
  OPTIONAL {
    ?edge prov:wasDerivedFrom ?evidence .
    ?evidence cape:evidenceAnchorId ?evidenceAnchorId .
  }
}
LIMIT 25
```

### Sample Answers

| id | source | predicate | target | evidence anchors | review status |
| --- | --- | --- | --- | --- | --- |
| `EDGE-62177f4ddb1eeea6` | 기회분석 (`L2_TASK_OPPORTUNITY_ASSESSMENT`) | `PRODUCES` | 제안 요청서 (`L2_ARTIFACT_ARTIFACT_RFP`) | EA-JS-00251 | accepted_by_rule |
| `EDGE-daa04d2ed1d22aa8` | 기회분석 (`L2_TASK_OPPORTUNITY_ASSESSMENT`) | `PRODUCES` | Capture Plan (`L2_ARTIFACT_ARTIFACT_CAPTURE_PLAN`) | EA-JS-00235, EA-JS-00251 | accepted_by_rule |
| `EDGE-ae7c1702bcd044e6` | 기회분석 (`L2_TASK_OPPORTUNITY_ASSESSMENT`) | `PRODUCES` | 제안전략 (`L2_ARTIFACT_ARTIFACT_PROPOSAL_STRATEGY`) | EA-JS-00275 | accepted_by_rule |
| `EDGE-8321b1d5d1f3fb82` | 기회분석 (`L2_TASK_OPPORTUNITY_ASSESSMENT`) | `PRODUCES` | 수주전략 (`L2_ARTIFACT_ARTIFACT_CAPTURE_STRATEGY`) | EA-JS-00275 | accepted_by_rule |
| `EDGE-2dc1247db51d5bf9` | 기회분석 (`L2_TASK_OPPORTUNITY_ASSESSMENT`) | `PRODUCES` | 제안서 (`L2_ARTIFACT_ARTIFACT_PROPOSAL`) | EA-JS-00251, EA-JS-00275 | accepted_by_rule |

## CQ4. Responsible roles

- Question: 각 Task는 누가 수행하거나 책임지는가?
- Required predicates: `PERFORMED_BY`
- Support source: `layer2_edges`
- Supporting item count: `120`
- Answerable by current KG: `True`
- Claim status: `query_pack_structural_diagnostic_not_human_gold`

### Cypher

```cypher
MATCH (s:KGNode)-[r:PERFORMED_BY]->(t:KGNode)
RETURN s.node_id AS source_id, s.label AS source_label, labels(s) AS source_labels,
       type(r) AS predicate,
       t.node_id AS target_id, t.label AS target_label, labels(t) AS target_labels,
       r.evidence_anchor_ids_json AS evidence_anchor_ids
LIMIT 25;
```

### SPARQL-style Query

```sparql
PREFIX cape: <https://example.org/cape-kg#>
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?edge ?predicate ?source ?target ?evidenceAnchorId WHERE {
  VALUES ?predicate { "PERFORMED_BY" }
  ?edge a cape:KGEdge ; cape:predicate ?predicate ;
        cape:sourceNode ?source ; cape:targetNode ?target .
  OPTIONAL {
    ?edge prov:wasDerivedFrom ?evidence .
    ?evidence cape:evidenceAnchorId ?evidenceAnchorId .
  }
}
LIMIT 25
```

### Sample Answers

| id | source | predicate | target | evidence anchors | review status |
| --- | --- | --- | --- | --- | --- |
| `EDGE-d726d94ef84162b1` | 기회분석 (`L2_TASK_OPPORTUNITY_ASSESSMENT`) | `PERFORMED_BY` | 고객 (`L2_ROLE_a58673ab1d25`) | EA-JS-00235, EA-JS-00251 | accepted_by_rule |
| `EDGE-5288c65137b15b12` | 기회분석 (`L2_TASK_OPPORTUNITY_ASSESSMENT`) | `PERFORMED_BY` | 경쟁사 (`L2_ROLE_bdcca1c8a14c`) | EA-JS-00235 | accepted_by_rule |
| `EDGE-11416320e05bcb30` | 수주영업 (`L2_TASK_CAPTURE_PLANNING`) | `PERFORMED_BY` | 제안 PM (`L2_ROLE_6f23fc00fb1f`) | EA-JS-00319, EA-JS-00448, EA-JS-00452 | accepted_by_rule |
| `EDGE-f59f5e1e78425bf3` | 수주영업 (`L2_TASK_CAPTURE_PLANNING`) | `PERFORMED_BY` | 영업대표 (`L2_ROLE_9d08dd751bf2`) | EA-JS-00448, EA-JS-00452 | accepted_by_rule |
| `EDGE-9ba38bbd10b16be4` | 수주영업 (`L2_TASK_CAPTURE_PLANNING`) | `PERFORMED_BY` | 작성자 (`L2_ROLE_0be45e6f773d`) | EA-JS-00258, EA-JS-00452 | accepted_by_rule |

## CQ5. Decision gateways

- Question: 어떤 의사결정 지점이 존재하는가?
- Required predicates: `HAS_DECISION_GATEWAY`
- Support source: `layer2_edges`
- Supporting item count: `54`
- Answerable by current KG: `True`
- Claim status: `query_pack_structural_diagnostic_not_human_gold`

### Cypher

```cypher
MATCH (s:KGNode)-[r:HAS_DECISION_GATEWAY]->(t:KGNode)
RETURN s.node_id AS source_id, s.label AS source_label, labels(s) AS source_labels,
       type(r) AS predicate,
       t.node_id AS target_id, t.label AS target_label, labels(t) AS target_labels,
       r.evidence_anchor_ids_json AS evidence_anchor_ids
LIMIT 25;
```

### SPARQL-style Query

```sparql
PREFIX cape: <https://example.org/cape-kg#>
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?edge ?predicate ?source ?target ?evidenceAnchorId WHERE {
  VALUES ?predicate { "HAS_DECISION_GATEWAY" }
  ?edge a cape:KGEdge ; cape:predicate ?predicate ;
        cape:sourceNode ?source ; cape:targetNode ?target .
  OPTIONAL {
    ?edge prov:wasDerivedFrom ?evidence .
    ?evidence cape:evidenceAnchorId ?evidenceAnchorId .
  }
}
LIMIT 25
```

### Sample Answers

| id | source | predicate | target | evidence anchors | review status |
| --- | --- | --- | --- | --- | --- |
| `EDGE-ec34b515d3841173` | 기회분석 (`L2_TASK_OPPORTUNITY_ASSESSMENT`) | `HAS_DECISION_GATEWAY` | Bid/No Bid Decision (`L2_DG_DG_BID_NO_BID`) | EA-JS-00251 | accepted_by_rule |
| `EDGE-839646e82de9eb1f` | 기회분석 (`L2_TASK_OPPORTUNITY_ASSESSMENT`) | `HAS_DECISION_GATEWAY` | Pursuit Decision (`L2_DG_DG_PURSUIT`) | EA-JS-00235, EA-JS-00251 | accepted_by_rule |
| `EDGE-5d0333073a11076f` | 기회분석 (`L2_TASK_OPPORTUNITY_ASSESSMENT`) | `HAS_DECISION_GATEWAY` | 입찰타당성 결정 (`L2_DG_DG_BID_VALIDATION`) | EA-JS-00251 | accepted_by_rule |
| `EDGE-5bdb664b4c63d2e4` | 기회분석 (`L2_TASK_OPPORTUNITY_ASSESSMENT`) | `HAS_DECISION_GATEWAY` | 승인 (`L2_DG_DG_APPROVAL`) | EA-JS-00251 | accepted_by_rule |
| `EDGE-ad127f54f19d63c8` | 수주영업 (`L2_TASK_CAPTURE_PLANNING`) | `HAS_DECISION_GATEWAY` | Bid/No Bid Decision (`L2_DG_DG_BID_NO_BID`) | EA-JS-00251, EA-JS-00253 | accepted_by_rule |

## CQ6. Guard conditions for decisions

- Question: 의사결정에는 어떤 조건이나 판단 기준이 필요한가?
- Required predicates: `HAS_GUARD_CONDITION`
- Support source: `layer2_edges`
- Supporting item count: `14`
- Answerable by current KG: `True`
- Claim status: `query_pack_structural_diagnostic_not_human_gold`

### Cypher

```cypher
MATCH (s:KGNode)-[r:HAS_GUARD_CONDITION]->(t:KGNode)
RETURN s.node_id AS source_id, s.label AS source_label, labels(s) AS source_labels,
       type(r) AS predicate,
       t.node_id AS target_id, t.label AS target_label, labels(t) AS target_labels,
       r.evidence_anchor_ids_json AS evidence_anchor_ids
LIMIT 25;
```

### SPARQL-style Query

```sparql
PREFIX cape: <https://example.org/cape-kg#>
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?edge ?predicate ?source ?target ?evidenceAnchorId WHERE {
  VALUES ?predicate { "HAS_GUARD_CONDITION" }
  ?edge a cape:KGEdge ; cape:predicate ?predicate ;
        cape:sourceNode ?source ; cape:targetNode ?target .
  OPTIONAL {
    ?edge prov:wasDerivedFrom ?evidence .
    ?evidence cape:evidenceAnchorId ?evidenceAnchorId .
  }
}
LIMIT 25
```

### Sample Answers

| id | source | predicate | target | evidence anchors | review status |
| --- | --- | --- | --- | --- | --- |
| `EDGE-73574fefc78279d0` | Pursuit Decision (`L2_DG_DG_PURSUIT`) | `HAS_GUARD_CONDITION` | pportunity Assessment)이 끝나고 나면 고객과 경쟁자 정보수집을 위한 영업활동(Capture Planning, 이 (`L2_GUARD_51c1514e1235`) | EA-JS-00235 | needs_review |
| `EDGE-4c73d2919ee9d696` | Bid/No Bid Decision (`L2_DG_DG_BID_NO_BID`) | `HAS_GUARD_CONDITION` | 한 기회에서 고객의 근원적인 니즈를 분석하고, 이를 기준으로 경쟁사를 파악하여 자사의 솔루션 및 수주전략을 결정함제안 참여 의사 (`L2_GUARD_4b8250093faa`) | EA-JS-00253 | needs_review |
| `EDGE-e37e2cd07189d559` | 승인 (`L2_DG_DG_APPROVAL`) | `HAS_GUARD_CONDITION` | 목적- 제안 환경 분석- 영업 관점에서 고객의 관심사항 파악- 경쟁사와 자사의 솔루션 분석 / 강약점 분석- 전략 개발을 위한 사 (`L2_GUARD_d699f1d1f525`) | EA-JS-00452 | needs_review |
| `EDGE-bfcd3d80c9e30fa5` | 승인 (`L2_DG_DG_APPROVAL`) | `HAS_GUARD_CONDITION` | 성자- 영업대표 - 수행 PM(이미 거래가 있었던 기존 고객의 경우에는 수행 PM도 고객의 정보를 알고 있는 경우가 많음) •주요 (`L2_GUARD_33390f951090`) | EA-JS-00452 | needs_review |
| `EDGE-a03e97e3a9edb87c` | 승인 (`L2_DG_DG_APPROVAL`) | `HAS_GUARD_CONDITION` | 공고일, PT 시행 여부 확인, 주관조직의 영향력, 예상 참여 경쟁사, TFT 구성 인원- 과제(사업) 분석: 사업배경, 평가배점 (`L2_GUARD_a305aa02cd25`) | EA-JS-00452 | needs_review |

## CQ7. Artifact flow between tasks

- Question: 산출물은 다음 업무에서 어떻게 사용되는가?
- Required predicates: `FEEDS_INTO, USED_AS_INPUT_FOR`
- Support source: `layer2_edges`
- Supporting item count: `18`
- Answerable by current KG: `True`
- Claim status: `query_pack_structural_diagnostic_not_human_gold`

### Cypher

```cypher
MATCH (s:KGNode)-[r:FEEDS_INTO|USED_AS_INPUT_FOR]->(t:KGNode)
RETURN s.node_id AS source_id, s.label AS source_label, labels(s) AS source_labels,
       type(r) AS predicate,
       t.node_id AS target_id, t.label AS target_label, labels(t) AS target_labels,
       r.evidence_anchor_ids_json AS evidence_anchor_ids
LIMIT 25;
```

### SPARQL-style Query

```sparql
PREFIX cape: <https://example.org/cape-kg#>
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?edge ?predicate ?source ?target ?evidenceAnchorId WHERE {
  VALUES ?predicate { "FEEDS_INTO" "USED_AS_INPUT_FOR" }
  ?edge a cape:KGEdge ; cape:predicate ?predicate ;
        cape:sourceNode ?source ; cape:targetNode ?target .
  OPTIONAL {
    ?edge prov:wasDerivedFrom ?evidence .
    ?evidence cape:evidenceAnchorId ?evidenceAnchorId .
  }
}
LIMIT 25
```

### Sample Answers

| id | source | predicate | target | evidence anchors | review status |
| --- | --- | --- | --- | --- | --- |
| `EDGE-5f5efce32df44d2b` | Capture Plan (`L2_ARTIFACT_ARTIFACT_CAPTURE_PLAN`) | `FEEDS_INTO` | 제안서 기획 (`L2_TASK_PROPOSAL_PLANNING`) | EA-JS-00258 | accepted_by_rule |
| `EDGE-4d77bc3e682208c9` | Capture Plan (`L2_ARTIFACT_ARTIFACT_CAPTURE_PLAN`) | `USED_AS_INPUT_FOR` | 제안서 기획 (`L2_TASK_PROPOSAL_PLANNING`) | EA-JS-00258 | accepted_by_rule |
| `EDGE-cca83d6e007f74cd` | 수주전략 (`L2_ARTIFACT_ARTIFACT_CAPTURE_STRATEGY`) | `FEEDS_INTO` | 제안전략 개발 (`L2_TASK_PROPOSAL_STRATEGY_DEVELOPMENT`) | EA-JS-00258, EA-JS-00291 | accepted_by_rule |
| `EDGE-1b63f9828e0eb4c7` | 수주전략 (`L2_ARTIFACT_ARTIFACT_CAPTURE_STRATEGY`) | `USED_AS_INPUT_FOR` | 제안전략 개발 (`L2_TASK_PROPOSAL_STRATEGY_DEVELOPMENT`) | EA-JS-00258, EA-JS-00291 | accepted_by_rule |
| `EDGE-bd5169c9c51eae88` | 제안전략 (`L2_ARTIFACT_ARTIFACT_PROPOSAL_STRATEGY`) | `FEEDS_INTO` | 제안서 작성 (`L2_TASK_PROPOSAL_WRITING`) | EA-JS-00291, EA-JS-01788 | accepted_by_rule |

## CQ8. Review checkpoints

- Question: 제안서 리뷰는 어떤 단계에서 어떻게 수행되는가?
- Required predicates: `HAS_REVIEW_CHECKPOINT`
- Support source: `layer2_edges`
- Supporting item count: `41`
- Answerable by current KG: `True`
- Claim status: `query_pack_structural_diagnostic_not_human_gold`

### Cypher

```cypher
MATCH (s:KGNode)-[r:HAS_REVIEW_CHECKPOINT]->(t:KGNode)
RETURN s.node_id AS source_id, s.label AS source_label, labels(s) AS source_labels,
       type(r) AS predicate,
       t.node_id AS target_id, t.label AS target_label, labels(t) AS target_labels,
       r.evidence_anchor_ids_json AS evidence_anchor_ids
LIMIT 25;
```

### SPARQL-style Query

```sparql
PREFIX cape: <https://example.org/cape-kg#>
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?edge ?predicate ?source ?target ?evidenceAnchorId WHERE {
  VALUES ?predicate { "HAS_REVIEW_CHECKPOINT" }
  ?edge a cape:KGEdge ; cape:predicate ?predicate ;
        cape:sourceNode ?source ; cape:targetNode ?target .
  OPTIONAL {
    ?edge prov:wasDerivedFrom ?evidence .
    ?evidence cape:evidenceAnchorId ?evidenceAnchorId .
  }
}
LIMIT 25
```

### Sample Answers

| id | source | predicate | target | evidence anchors | review status |
| --- | --- | --- | --- | --- | --- |
| `EDGE-e60bd43abb66dde1` | Capture Plan 검토 (`STEP-OPPORTUNITY_ASSESSMENT-01`) | `HAS_REVIEW_CHECKPOINT` | Capture Plan 검토 (`REVIEW-STEP-OPPORTUNITY_ASSESSMENT-01`) | EA-JS-00235 | accepted_by_rule |
| `EDGE-32f49e5de246dadf` | 제안전략 검토 (`STEP-OPPORTUNITY_ASSESSMENT-02`) | `HAS_REVIEW_CHECKPOINT` | 제안전략 검토 (`REVIEW-STEP-OPPORTUNITY_ASSESSMENT-02`) | EA-JS-00235 | accepted_by_rule |
| `EDGE-54618c5b9e88998d` | 기회 확인 (`STEP-BID_NO_BID_DECISION-01`) | `HAS_REVIEW_CHECKPOINT` | 기회 확인 checkpoint (`REVIEW-STEP-BID_NO_BID_DECISION-01`) | EA-JS-00233 | accepted_by_rule |
| `EDGE-eb04081d5cc5f120` | 제안 요청서 검토 (`STEP-BID_VALIDATION-01`) | `HAS_REVIEW_CHECKPOINT` | 제안 요청서 검토 (`REVIEW-STEP-BID_VALIDATION-01`) | EA-JS-00241 | accepted_by_rule |
| `EDGE-a13c90062fb21faa` | 제안전략 검토 (`STEP-BID_VALIDATION-02`) | `HAS_REVIEW_CHECKPOINT` | 제안전략 검토 (`REVIEW-STEP-BID_VALIDATION-02`) | EA-JS-00241 | accepted_by_rule |

## CQ9. Principles attached to work items

- Question: 각 업무에서 지켜야 할 원칙은 무엇인가?
- Required predicates: `HAS_PRINCIPLE`
- Support source: `layer2_edges`
- Supporting item count: `64`
- Answerable by current KG: `True`
- Claim status: `query_pack_structural_diagnostic_not_human_gold`

### Cypher

```cypher
MATCH (s:KGNode)-[r:HAS_PRINCIPLE]->(t:KGNode)
RETURN s.node_id AS source_id, s.label AS source_label, labels(s) AS source_labels,
       type(r) AS predicate,
       t.node_id AS target_id, t.label AS target_label, labels(t) AS target_labels,
       r.evidence_anchor_ids_json AS evidence_anchor_ids
LIMIT 25;
```

### SPARQL-style Query

```sparql
PREFIX cape: <https://example.org/cape-kg#>
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?edge ?predicate ?source ?target ?evidenceAnchorId WHERE {
  VALUES ?predicate { "HAS_PRINCIPLE" }
  ?edge a cape:KGEdge ; cape:predicate ?predicate ;
        cape:sourceNode ?source ; cape:targetNode ?target .
  OPTIONAL {
    ?edge prov:wasDerivedFrom ?evidence .
    ?evidence cape:evidenceAnchorId ?evidenceAnchorId .
  }
}
LIMIT 25
```

### Sample Answers

| id | source | predicate | target | evidence anchors | review status |
| --- | --- | --- | --- | --- | --- |
| `EDGE-690233a6aa23699d` | 수주영업 (`L2_TASK_CAPTURE_PLANNING`) | `HAS_PRINCIPLE` | 고객 중심 (`L2_PRINCIPLE_ad76810528c8`) | EA-JS-00171, EA-JS-00258 | accepted_by_rule |
| `EDGE-bac98011d06e8ad5` | 수주영업 (`L2_TASK_CAPTURE_PLANNING`) | `HAS_PRINCIPLE` | 충실도 (`L2_PRINCIPLE_bc6d31b3b7e5`) | EA-JS-00258 | accepted_by_rule |
| `EDGE-1f36977236597108` | 수주영업 (`L2_TASK_CAPTURE_PLANNING`) | `HAS_PRINCIPLE` | 차별화 (`L2_PRINCIPLE_369cb1468674`) | EA-JS-00171, EA-JS-00442, EA-JS-00447 | accepted_by_rule |
| `EDGE-556a38d16648b005` | 제안참여 의사결정 (`L2_TASK_BID_NO_BID_DECISION`) | `HAS_PRINCIPLE` | 차별화 (`L2_PRINCIPLE_369cb1468674`) | EA-JS-01037 | accepted_by_rule |
| `EDGE-5b01f8f329aac5f7` | 입찰타당성 검증 (`L2_TASK_BID_VALIDATION`) | `HAS_PRINCIPLE` | 충실도 (`L2_PRINCIPLE_bc6d31b3b7e5`) | EA-JS-00292 | accepted_by_rule |

## CQ10. Evidence grounding for accepted KG edges

- Question: 각 지식 항목은 원문 어느 chunk/page/span에 근거가 있는가?
- Required predicates: `EVIDENCED_BY`
- Support source: `edge.evidence_anchor_ids`
- Supporting item count: `947`
- Answerable by current KG: `True`
- Claim status: `query_pack_structural_diagnostic_not_human_gold`

### Cypher

```cypher
MATCH (s:KGNode)-[r]->(t:KGNode)
WHERE r.evidence_anchor_ids_json IS NOT NULL AND r.evidence_anchor_ids_json <> ''
RETURN s.node_id AS source_id, s.label AS source_label, type(r) AS predicate,
       t.node_id AS target_id, t.label AS target_label,
       r.evidence_anchor_ids_json AS evidence_anchor_ids
LIMIT 25;
```

### SPARQL-style Query

```sparql
PREFIX cape: <https://example.org/cape-kg#>
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?edge ?predicate ?source ?target ?evidenceAnchorId WHERE {
  ?edge a cape:KGEdge ; cape:predicate ?predicate ;
        cape:sourceNode ?source ; cape:targetNode ?target ;
        prov:wasDerivedFrom ?evidence .
  ?evidence cape:evidenceAnchorId ?evidenceAnchorId .
}
LIMIT 25
```

### Sample Answers

| id | source | predicate | target | evidence anchors | review status |
| --- | --- | --- | --- | --- | --- |
| `EDGE-257c3380629f4d96` | 기회분석 (`L2_TASK_OPPORTUNITY_ASSESSMENT`) | `USES_INPUT` | Capture Plan (`L2_ARTIFACT_ARTIFACT_CAPTURE_PLAN`) | EA-JS-00235, EA-JS-00251 | accepted_by_rule |
| `EDGE-9fe97ab8661898c6` | 기회분석 (`L2_TASK_OPPORTUNITY_ASSESSMENT`) | `USES_INPUT` | 제안전략 (`L2_ARTIFACT_ARTIFACT_PROPOSAL_STRATEGY`) | EA-JS-00275 | accepted_by_rule |
| `EDGE-76ee7bd1733b6063` | 기회분석 (`L2_TASK_OPPORTUNITY_ASSESSMENT`) | `USES_INPUT` | 수주전략 (`L2_ARTIFACT_ARTIFACT_CAPTURE_STRATEGY`) | EA-JS-00275 | accepted_by_rule |
| `EDGE-e4f9a039b8f0bac1` | 기회분석 (`L2_TASK_OPPORTUNITY_ASSESSMENT`) | `USES_INPUT` | 제안서 (`L2_ARTIFACT_ARTIFACT_PROPOSAL`) | EA-JS-00251, EA-JS-00275 | accepted_by_rule |
| `EDGE-7ca0657bc4178067` | 기회분석 (`L2_TASK_OPPORTUNITY_ASSESSMENT`) | `USES_INPUT` | 발표자료 (`L2_ARTIFACT_ARTIFACT_PRESENTATION`) | EA-JS-00235, EA-JS-00251, EA-JS-00275 | accepted_by_rule |

## CQ11. Layer2-to-NCS capability candidates

- Question: 특정 업무는 어떤 NCS 능력단위와 관련되는가?
- Required predicates: `REQUIRES_CAPABILITY, CANDIDATE_ALIGNS_WITH`
- Support source: `l2_ncs_mapping_candidates`
- Supporting item count: `110`
- Answerable by current KG: `True`
- Claim status: `query_pack_structural_diagnostic_not_human_gold`

### Cypher

```cypher
MATCH (task:KGNode:Layer2)-[r:REQUIRES_CAPABILITY]->(target:KGNode:Layer1NCS)
RETURN task.node_id AS task_id, task.label AS task_label,
       target.node_id AS ncs_id, target.label AS ncs_label,
       r.rank AS rank, r.score AS score, r.reason AS reason
ORDER BY task_id, rank
LIMIT 25;
```

### SPARQL-style Query

```sparql
PREFIX cape: <https://example.org/cape-kg#>
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?edge ?source ?target ?rank ?score WHERE {
  ?edge a cape:KGEdge ; cape:predicate "REQUIRES_CAPABILITY" ;
        cape:sourceNode ?source ; cape:targetNode ?target .
  OPTIONAL { ?edge cape:rank ?rank }
  OPTIONAL { ?edge cape:score ?score }
}
LIMIT 25
```

### Sample Answers

| id | source | predicate | target | evidence anchors | review status |
| --- | --- | --- | --- | --- | --- |
| `MAP-7c8bda01000dcab4` | 기회분석 (`L2_TASK_OPPORTUNITY_ASSESSMENT`) | `REQUIRES_CAPABILITY` | 배관 및 Unit 설치(기장) (`ncs:CU:1508030106_17v2`) |  | pending_review |
| `MAP-60e59e4ffc065488` | 기회분석 (`L2_TASK_OPPORTUNITY_ASSESSMENT`) | `REQUIRES_CAPABILITY` | 기본도면 작성 (`ncs:CU:1508010104_23v4`) |  | pending_review |
| `MAP-6e603164498a8fe4` | 기회분석 (`L2_TASK_OPPORTUNITY_ASSESSMENT`) | `REQUIRES_CAPABILITY` | 관광숙박 운영 기획 (`ncs:CU:1203020110_23v2`) |  | pending_review |
| `MAP-418a736365666100` | 기회분석 (`L2_TASK_OPPORTUNITY_ASSESSMENT`) | `REQUIRES_CAPABILITY` | 주기관 해상 시운전 (`ncs:CU:1508060102_15v3`) |  | pending_review |
| `MAP-b937500164ea962e` | 기회분석 (`L2_TASK_OPPORTUNITY_ASSESSMENT`) | `REQUIRES_CAPABILITY` | 반도체 펌웨어 개발 (`ncs:CU:1903060114_23v2`) |  | pending_review |

## CQ12. Layer2-to-PCF process context candidates

- Question: 특정 업무는 PCF 프로세스 체계상 어디에 위치하는가?
- Required predicates: `PROCESS_CONTEXT, CANDIDATE_ALIGNS_WITH`
- Support source: `l2_pcf_mapping_candidates`
- Supporting item count: `110`
- Answerable by current KG: `True`
- Claim status: `query_pack_structural_diagnostic_not_human_gold`

### Cypher

```cypher
MATCH (task:KGNode:Layer2)-[r:PROCESS_CONTEXT]->(target:KGNode:Layer1PCF)
RETURN task.node_id AS task_id, task.label AS task_label,
       target.node_id AS pcf_id, target.label AS pcf_label,
       r.rank AS rank, r.score AS score, r.reason AS reason
ORDER BY task_id, rank
LIMIT 25;
```

### SPARQL-style Query

```sparql
PREFIX cape: <https://example.org/cape-kg#>
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?edge ?source ?target ?rank ?score WHERE {
  ?edge a cape:KGEdge ; cape:predicate "PROCESS_CONTEXT" ;
        cape:sourceNode ?source ; cape:targetNode ?target .
  OPTIONAL { ?edge cape:rank ?rank }
  OPTIONAL { ?edge cape:score ?score }
}
LIMIT 25
```

### Sample Answers

| id | source | predicate | target | evidence anchors | review status |
| --- | --- | --- | --- | --- | --- |
| `MAP-e2ce98c23880cf4b` | 기회분석 (`L2_TASK_OPPORTUNITY_ASSESSMENT`) | `PROCESS_CONTEXT` | 기회 수주 계획 수립 (`pcf:E:18116`) |  | pending_review |
| `MAP-3755551d86c1f42c` | 기회분석 (`L2_TASK_OPPORTUNITY_ASSESSMENT`) | `PROCESS_CONTEXT` | 기회 파이프라인 관리 (`pcf:E:20011`) |  | pending_review |
| `MAP-23bd091ea3b786dd` | 기회분석 (`L2_TASK_OPPORTUNITY_ASSESSMENT`) | `PROCESS_CONTEXT` | 기회를 사업전략에 매칭 (`pcf:E:11773`) |  | pending_review |
| `MAP-b96ec14fcf3cd9f6` | 기회분석 (`L2_TASK_OPPORTUNITY_ASSESSMENT`) | `PROCESS_CONTEXT` | 영업팀에 기회 전달 (`pcf:E:16937`) |  | pending_review |
| `MAP-38f3f1e260f7dfba` | 기회분석 (`L2_TASK_OPPORTUNITY_ASSESSMENT`) | `PROCESS_CONTEXT` | 개선 기회 식별 (`pcf:E:20119`) |  | pending_review |

## Interpretation

- 이 query pack은 CQ answerability의 구조적 근거를 사람이 재현 가능한 query 형태로 고정합니다.
- 현재 12개 CQ 모두 KG predicate/support source에 의해 구조적으로 query 가능합니다.
- Sample answer는 정답 claim이 아니라 현재 KG가 제공하는 구조적 evidence입니다.
- 최종 CQ answer correctness는 adjudicated human-gold 이후 다시 평가해야 합니다.
