# CAPE-KG Annotation Return Field Guide

Generated: `2026-06-29T18:55:22.871714+00:00`
Claim status: `annotation_return_field_guide_ready_pending_human_returns`

이 문서는 CAPE-KG human-gold annotation 반환 JSONL을 작성할 때 어떤 필드를 수정하고 어떤 필드를 보존해야 하는지 정리한 내부 검수 가이드다. 원문 chunk text를 재수록하지 않고 field policy와 validator 규칙만 요약한다.

## Scope

- 대상 파일: priority-100 A/B annotation batch의 `*.reviewed.jsonl` 반환 파일.
- 기준 schema: `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/annotation_schema.json`.
- 반환 파일 목록: `experiments/cape_kg_eacl_20260627/05_review/human_review_master_return_files.csv`.
- 이 문서는 human-gold 결과 자체가 아니며, A/B 검수, IAA, adjudication, human-gold scoring 전에는 논문 성능 claim으로 사용할 수 없다.

## Reviewer-Editable Fields

| Field | 작성 방법 | Validator 영향 |
| --- | --- | --- |
| `annotation_status` | `pending_human_annotation`, `in_progress`, `completed`, `needs_adjudication` 중 하나. 완료 행은 `completed` 또는 `needs_adjudication`. | completed/needs_adjudication만 완료로 집계된다. |
| `annotator_id` | 검수자 ID. A/B 독립 검수 추적을 위해 유지 또는 명시적으로 기입. | import 시 원본 row에 반영되는 editable field다. |
| `gold_nodes` | 원문에서 명시적으로 지지되는 node만 추가. node_id/type/label/evidence를 schema에 맞춘다. | import 시 원본 row에 반영되는 editable field다. |
| `gold_edges` | accept한 candidate edge 또는 원문에서 새로 발견한 edge. candidate accept 시 `reference_id` 또는 `candidate_reference_id`를 보존. | completed row에서 accept된 candidate 또는 추가 edge 근거를 검사한다. |
| `rejected_candidate_reference_ids` | reject한 silver candidate의 `reference_id`를 모두 넣는다. | completed row의 미처리 candidate edge를 막기 위해 사용된다. |
| `missing_but_supported_notes` | candidate에는 없지만 원문 근거가 명확한 누락 node/edge 메모. | import 시 원본 row에 반영되는 editable field다. |
| `comments` | `needs_adjudication`이면 반드시 사유를 작성. | needs_adjudication row에서는 비어 있으면 error다. |
| `time_minutes` | 해당 row 검수 소요 시간. | import 시 원본 row에 반영되는 editable field다. |

## Immutable Fields

아래 필드는 검수자가 원칙적으로 수정하지 않는다. import preflight는 핵심 불변 필드가 원본과 달라지면 실패한다.

| Field | 이유 |
| --- | --- |
| `chunk_id` | 원본 chunk/package provenance 보존. |
| `chunk_text` | 원본 chunk/package provenance 보존. |
| `chapter_id` | 원본 chunk/package provenance 보존. |
| `section_id` | 원본 chunk/package provenance 보존. |
| `page_start` | 원본 chunk/package provenance 보존. |
| `page_end` | 원본 chunk/package provenance 보존. |
| `package` | 원본 chunk/package provenance 보존. |
| `silver_candidate_edges` | candidate 판단 대상이므로 원본을 보존한다. accept/reject 결과는 `gold_edges`와 `rejected_candidate_reference_ids`에 기록한다. |
| `silver_candidate_edge_count` | 원본 candidate 수 확인용이다. |
| `instructions` | batch 작성 지침 원본이다. |

## Completion Rules

1. 완료로 집계하려면 `annotation_status`를 `completed` 또는 `needs_adjudication`으로 둔다.
2. `needs_adjudication`을 사용할 때는 `comments`에 애매한 이유를 반드시 쓴다.
3. candidate edge가 있는 completed row에서는 모든 candidate가 둘 중 하나로 처리되어야 한다: `gold_edges`에서 accept되거나 `rejected_candidate_reference_ids`에 reject로 기록된다.
4. candidate를 accept할 때는 edge triple만 베끼지 말고 `reference_id` 또는 `candidate_reference_id`를 같이 남긴다. reference가 없으면 source/predicate/target key matching으로 일부 확인되지만, reference 보존이 가장 안전하다.
5. `gold_nodes`와 `gold_edges`는 chunk text 안에서 명시적으로 지지되는 항목만 포함한다. 추론만으로 추가하지 않는다.

## Candidate Edge Handling

| 판단 | 기록 위치 | 최소 기록 |
| --- | --- | --- |
| Accept | `gold_edges[]` | source/target id 또는 label, predicate, evidence anchor/span, decision, reference_id 또는 candidate_reference_id |
| Reject | `rejected_candidate_reference_ids[]` | silver candidate의 reference_id |
| Ambiguous | `annotation_status=needs_adjudication`, `comments` | 왜 accept/reject가 어려운지 구체적으로 기록 |
| Missing but supported | `gold_edges[]` 또는 `gold_nodes[]`, `missing_but_supported_notes` | 원문 exact evidence와 추가 사유 |

## Gold Node Fields

`gold_nodes[]` field set: `node_id, type, label, evidence`

## Gold Edge Fields

`gold_edges[]` field set: `source_id, source_label, source_type, predicate, target_id, target_label, target_type, evidence_anchor_ids, evidence_spans, decision`

권장 추가 key: candidate를 accept한 edge에는 `reference_id` 또는 `candidate_reference_id`를 보존한다.

## JSON Shape Examples

Candidate accept/reject가 섞인 completed row의 핵심 shape:

```json
{
  "annotation_status": "completed",
  "annotator_id": "A",
  "gold_edges": [
    {
      "source_id": "node_id_or_blank",
      "source_label": "source label",
      "source_type": "DomainTask",
      "predicate": "USES_INPUT",
      "target_id": "node_id_or_blank",
      "target_label": "target label",
      "target_type": "Artifact",
      "evidence_anchor_ids": [
        "anchor_id"
      ],
      "evidence_spans": [
        {
          "text": "short exact span",
          "sentence_id": "sentence_id"
        }
      ],
      "decision": "accepted",
      "reference_id": "candidate_reference_id"
    }
  ],
  "rejected_candidate_reference_ids": [
    "candidate_reference_id_to_reject"
  ],
  "comments": "",
  "time_minutes": 6
}
```

`needs_adjudication` row의 핵심 shape:

```json
{
  "annotation_status": "needs_adjudication",
  "gold_edges": [],
  "rejected_candidate_reference_ids": [],
  "comments": "source와 target은 보이지만 predicate 방향이 불명확함."
}
```

## Validation Commands

반환 파일을 실제 반영하기 전 반드시 preflight를 먼저 실행한다.

```bash
python3 scripts/validate_cape_human_review_returns.py \
  --experiment-dir experiments/cape_kg_eacl_20260627
```

dry-run wrapper:

```bash
PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=0 \
bash scripts/run_cape_human_return_apply.sh
```

실제 반영은 preflight와 dry-run이 모두 통과한 뒤 `APPLY_IMPORTS=1`로 실행한다.

## Field Inventory Observed in Current Batch

- Sample file: `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_A_full_120_priority_batch_001.jsonl`
- Top-level fields: `annotation_status, annotator_id, chapter_id, chunk_id, chunk_text, comments, gold_edges, gold_nodes, instructions, missing_but_supported_notes, package, page_end, page_start, rejected_candidate_reference_ids, section_id, silver_candidate_edge_count, silver_candidate_edges, time_minutes`
- Silver candidate edge fields: `component_evidence_spans, evidence_anchor_ids, predicate, primary_evidence, reference_id, source_id, source_label, source_type, target_id, target_label, target_type`
- Component evidence span fields: `claim_status, component, label, page, predicate, sentence_id, sentence_span_end, sentence_span_start, span_exact, span_method, text`

## Claim Boundary

이 guide는 반환 파일 작성 오류를 줄이기 위한 운영 산출물이다. 현재 상태는 not human-gold이며, human-gold claim은 다음이 모두 끝난 뒤에만 가능하다: A/B annotation 반환, IAA 계산, adjudication 완료, adjudicated gold 기준 scoring.
