# Final Ontology Build Report

Generated: 2026-06-27

## Scope

Built a first-pass CEP-Onto KG using only the local AX-HYU handoff data:
NCS, PCF, PCF metrics, 수주 focus subsets, and `자이제_ocr_sentences.xlsx`.

## OCR And Chunking

- Clean OCR sentences: 5009
- Sentence-window chunks: 1168
- Section-based chunks: 473
- Hybrid semantic chunks: 480
- Anchor candidates: 9589

## Layer2 Graph

- Nodes: 4952
- Edges: 25165
- Verified task frames: 1476

Node class counts:
{
  "DomainTask": 1476,
  "ProcedureStep": 1646,
  "Principle": 19,
  "Artifact": 29,
  "Role": 20,
  "DecisionGateway": 16,
  "GuardCondition": 285,
  "ReviewEvent": 8,
  "Risk": 11,
  "StandardAnchor": 1442
}

Predicate counts:
{
  "HAS_SUBTASK": 1646,
  "EVIDENCED_BY": 3282,
  "HAS_PRINCIPLE": 584,
  "USES_INPUT": 1503,
  "PRODUCES": 1923,
  "PERFORMED_BY": 1740,
  "RESPONSIBLE_FOR": 1715,
  "HAS_DECISION_GATEWAY": 841,
  "HAS_GUARD_CONDITION": 655,
  "HAS_REVIEW": 712,
  "HAS_RISK": 381,
  "PRECEDES": 1334,
  "REQUIRES_CAPABILITY": 1427,
  "CANDIDATE_ALIGNS_WITH": 6577,
  "PROCESS_CONTEXT": 845
}

## Validation

{
  "node_count": 4952,
  "edge_count": 25165,
  "unknown_predicate_count": 0,
  "missing_evidence_edge_count": 0,
  "missing_node_reference_count": 0,
  "domain_range_violation_count": 0,
  "shacl_like_violation_rate": 0.0
}

## Important Limitation

This run does not call an LLM and does not include human adjudicated gold labels.
It is a reproducible draft KG and experiment scaffold aligned with the design document.
The next pass should use `16_tool_schemas.json`, `24_anchor_candidates.jsonl`, and
`33_conflict_review_queue.jsonl` for constrained LLM extraction and expert review.
