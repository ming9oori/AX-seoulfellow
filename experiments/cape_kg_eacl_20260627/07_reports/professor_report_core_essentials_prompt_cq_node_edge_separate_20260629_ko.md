# 교수님 보고용 핵심 요약: 프롬프트, CQ, Node/Edge 산출 방식

Generated: 2026-06-29  
Experiment directory: `experiments/cape_kg_eacl_20260627`  
KG output directory: `outputs`  
관련 원문 슬라이드: `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md`

이 문서는 위 슬라이드 원고와 별개로, 교수님께 가장 먼저 설명해야 할 핵심만 정리한 별도 요약본입니다. 특히 "어떤 프롬프트를 썼는가", "CQ를 어떻게 만들었는가", "node와 edge를 각각 어떤 방식으로 산출했는가"에 초점을 둡니다.

---

## 1. 한 문장 요약

본 연구는 한국어 수주/제안 업무 OCR 문서에서 task, step, role, artifact, decision, risk를 추출해 evidence-grounded procedural KG를 만들고, 이 KG를 NCS/PCF 표준 taxonomy와 연결한 뒤, LLM baseline/proposed 조건을 비교할 수 있는 평가 패키지로 확장한 실험입니다.

중요한 구분은 다음입니다.

| 구분 | 실제 수행 내용 | LLM 사용 여부 |
| --- | --- | --- |
| 원본 Layer 1/Layer 2 KG 구축 | OCR, seed task, keyword/evidence rule, schema validator로 deterministic KG 구축 | KG 원본 구축에는 LLM 미사용 |
| LLM baseline/proposed 실험 | 120개 evaluation chunks에 대해 B0-B6, proposed, ablation, model scaling 실행 | Qwen3 계열 LLM 사용 |
| 최종 논문 성능 주장 | human-gold annotation, IAA, adjudication, expert review 이후 확정 | 아직 미완료 |

따라서 현재 발표에서는 "KG 구축 및 LLM 진단 실험은 완료"라고 말할 수 있지만, "최종 human-gold 기반 성능 우수성은 아직 claim하지 않는다"고 분리해서 설명해야 합니다.

---

## 2. 현재 산출물 핵심 결과

| 항목 | 결과 |
| --- | ---: |
| OCR clean sentences / evidence anchors | 5,009 |
| Layer 1 NCS nodes | 4,109 |
| Layer 1 PCF nodes | 5,301 |
| Layer 2 nodes | 179 |
| Layer 2 edges | 906 |
| NCS mapping candidates | 110 |
| PCF mapping candidates | 110 |
| Neo4j flat import nodes | 10,946 |
| Neo4j flat import relationships | 14,332 |
| KG structural conformance | 1.000 |
| Domain/range violations | 0 |
| Evidence-missing Layer 2 edges | 0 |
| CQ answerability | 11 / 12 |
| Pre-human handoff validation | PASS, 75 checks: 74 PASS / 1 WARN |

주요 파일은 다음입니다.

| 역할 | 파일 |
| --- | --- |
| Layer 2 nodes | `outputs/07_layer2_graph/layer2_nodes.jsonl` |
| Layer 2 edges | `outputs/07_layer2_graph/layer2_edges.jsonl` |
| Evidence index | `outputs/07_layer2_graph/layer2_evidence_index.jsonl` |
| NCS mapping candidates | `outputs/08_mapping/l2_ncs_mapping_candidates.jsonl` |
| PCF mapping candidates | `outputs/08_mapping/l2_pcf_mapping_candidates.jsonl` |
| KG viewer | `outputs/09_visualization/kg_viewer.html` |
| 최종 build report | `outputs/10_evaluation/final_build_report.md` |
| LLM prompt runner | `scripts/run_cape_llm_condition_baselines.py` |
| KG build script | `scripts/build_ax_epak_internal_kg.py` |

---

## 3. CQ는 어떻게 생성했는가

CQ, 즉 Competency Question은 LLM이 즉석에서 만든 질문이 아닙니다. 연구자가 먼저 "이 KG가 답해야 하는 업무 질문"을 설계하고, 그 질문을 schema node type 및 edge predicate와 연결했습니다. 이후 이 CQ가 schema, LLM prompt, structural evaluation, 발표 framing에 모두 재사용됩니다.

생성 절차는 다음과 같습니다.

1. 연구 문제를 먼저 정의했습니다.
   - 한국어 수주/제안 업무 문서에서 절차형 업무 지식을 KG로 구축한다.
   - 단순 entity extraction이 아니라 task, step, input/output, role, decision, risk, evidence, standard mapping을 표현한다.
2. KG가 답해야 할 질문 범주를 정했습니다.
   - 업무 구성과 순서
   - 입력 자료와 산출물
   - 수행 역할
   - 의사결정 지점과 조건
   - 산출물 흐름
   - evidence grounding
   - NCS/PCF 표준 연결
3. 각 질문을 predicate와 연결했습니다.
   - 예: "각 Task는 어떤 산출물을 생성하는가?" -> `PRODUCES`
   - 예: "각 Task는 누가 수행하는가?" -> `PERFORMED_BY`
   - 예: "원문 어디에 근거하는가?" -> `EVIDENCED_BY`
4. 이 CQ 목록을 JSON schema와 LLM prompt에 넣고, structural answerability 평가에도 사용했습니다.

CQ 정의 파일:

- Internal KG build용: `outputs/03_schema/competency_questions.json`
- EACL experiment용: `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json`

---

## 4. 실제 CQ 목록

| CQ | 질문 | 연결 predicate / schema |
| --- | --- | --- |
| CQ1 | 수주·제안 업무는 어떤 주요 Task와 절차 단계로 구성되는가? | `HAS_STEP`, `PRECEDES` |
| CQ2 | 각 Task는 어떤 입력 자료를 사용하는가? | `USES_INPUT` |
| CQ3 | 각 Task는 어떤 산출물을 생성하는가? | `PRODUCES` |
| CQ4 | 각 Task는 누가 수행하거나 책임지는가? | `PERFORMED_BY` |
| CQ5 | 어떤 의사결정 지점이 존재하는가? | `HAS_DECISION_GATEWAY` |
| CQ6 | 의사결정에는 어떤 조건이나 판단 기준이 필요한가? | `HAS_GUARD_CONDITION` |
| CQ7 | 산출물은 다음 업무에서 어떻게 사용되는가? | `FEEDS_INTO`, `USED_AS_INPUT_FOR` |
| CQ8 | 제안서 리뷰는 어떤 단계에서 어떻게 수행되는가? | `HAS_REVIEW_CHECKPOINT` |
| CQ9 | 각 업무에서 지켜야 할 원칙은 무엇인가? | `HAS_PRINCIPLE` |
| CQ10 | 각 지식 항목은 원문 어느 chunk/page/span에 근거가 있는가? | `EVIDENCED_BY` |
| CQ11 | 특정 업무는 어떤 NCS 능력단위와 관련되는가? | `REQUIRES_CAPABILITY`, `CANDIDATE_ALIGNS_WITH` |
| CQ12 | 특정 업무는 PCF 프로세스 체계상 어디에 위치하는가? | `PROCESS_CONTEXT`, `CANDIDATE_ALIGNS_WITH` |

현재 KG에서는 12개 중 11개 CQ가 구조적으로 answerable입니다. CQ8은 `HAS_REVIEW_CHECKPOINT` evidence가 아직 구조적으로 충분히 생성되지 않아 gap으로 남아 있습니다.

---

## 5. 실제 LLM 프롬프트의 역할

LLM은 원본 KG를 만드는 데 직접 사용한 것이 아니라, 구축된 evaluation chunks에 대해 여러 extraction 조건을 비교하는 데 사용했습니다.

실험 조건은 다음과 같습니다.

| 조건 | 의미 |
| --- | --- |
| B0_plain_llm | schema 없이 일반 subject-predicate-object triple 추출 |
| B1_predicate_constrained | 허용 predicate만 쓰게 제한한 triple/edge 추출 |
| B2_current_project | task frame을 먼저 추론한 뒤 CAPE-KG schema로 변환 |
| B3_edc_style | open-schema KG item을 extract-define-canonicalize 방식으로 추출 |
| B4_taxonomy_rag | NCS/PCF taxonomy hint를 retrieval context로 넣은 baseline |
| B5_procedural_prompt | action, actor, gateway, condition, artifact flow 중심 추출 |
| B6_sac_kg_verifier_pruner | generator candidate를 schema/evidence verifier로 pruning하는 근사 baseline |
| P_cape_kg_actual | CQ, schema retrieval, evidence grounding, validator, NCS/PCF bridge를 결합한 proposed condition |
| P_minus_CQ | CQ anchoring 제거 ablation |
| P_minus_Evidence | evidence requirement 제거 ablation |
| P_minus_Procedural_schema | procedural schema 제거 ablation |
| P_minus_Validator | post-hoc validator 제거 ablation |
| P_minus_Standard_bridge | NCS/PCF bridge 제거 ablation |
| P_minus_Schema_retrieval | chunk-specific schema/taxonomy retrieval 제거 ablation |

사용 모델:

| 모델 | 실행 상태 | 비고 |
| --- | --- | --- |
| Qwen3-8B | full 120-chunk diagnostics 완료 | main local diagnostic |
| Qwen3-14B | core conditions 120-chunk 완료 | stronger local diagnostic |
| Qwen3-32B-AWQ | core conditions 120-chunk 완료 | largest completed local diagnostic |

주의: 위 결과는 silver/proxy reference에 대한 진단 결과입니다. 논문용 최종 성능은 human-gold scoring 이후 별도로 산출해야 합니다.

---

## 6. 실제 프롬프트 템플릿: Strict JSON contract

Qwen 계열 모델에는 JSON 파싱 실패와 `<think>` 출력 문제를 줄이기 위해 strict JSON contract를 적용했습니다.

```text
Strict JSON contract:
- Return exactly one JSON object and nothing else.
- The first non-whitespace character must be `{` and the last non-whitespace character must be `}`.
- Do not include markdown, code fences, comments, XML tags, `<think>` blocks, prose, or explanations.
- For Qwen/Qwen-style chat models, obey `/no_think`; do not emit hidden or visible reasoning.
- Output the JSON object immediately without a preamble.
- Use compact JSON without indentation or extra whitespace to reduce truncation risk.
- Use double-quoted JSON strings only.
- Use empty arrays for absent `nodes`, `edges`, `triples`, or `mappings` fields required by the requested shape.
```

이 프롬프트는 `experiments/cape_kg_eacl_20260627/02_schema/prompts/strict_json_contract.txt`와 `scripts/run_cape_llm_condition_baselines.py`에 들어 있습니다.

---

## 7. 실제 프롬프트 템플릿: Proposed CAPE-KG condition

아래는 `P_cape_kg_actual` 조건에서 실제 런타임에 조립되는 핵심 프롬프트 템플릿입니다. 실제 실행 시 `{taxonomy snippets}`, `{chunk metadata}`, `{chunk sentences}` 위치에 각 chunk별 NCS/PCF candidate와 OCR sentence가 들어갑니다.

```text
system:
You are a JSON-only evidence-grounded information extraction function.
Strict JSON contract:
- Return exactly one JSON object and nothing else.
- The first non-whitespace character must be `{` and the last non-whitespace character must be `}`.
- Do not include markdown, code fences, comments, XML tags, `<think>` blocks, prose, or explanations.
- For Qwen/Qwen-style chat models, obey `/no_think`; do not emit hidden or visible reasoning.
- Output the JSON object immediately without a preamble.
- Use compact JSON without indentation or extra whitespace to reduce truncation risk.
- Use double-quoted JSON strings only.
- Use empty arrays for absent `nodes`, `edges`, `triples`, or `mappings` fields required by the requested shape.

user:
/no_think
You are running the P_cape_kg_actual CAPE-KG condition.
Extract a domain procedural knowledge graph from the chunk.

Competency questions:
- CQ1: Identify major bid/proposal tasks and procedural steps.
- CQ2: Identify input artifacts used by each task.
- CQ3: Identify output artifacts produced by each task.
- CQ4: Identify roles responsible for each task.
- CQ5: Identify decision gateways.
- CQ6: Identify guard conditions for decisions or branches.
- CQ7: Identify artifact flows between tasks.
- CQ8: Identify review checkpoints.
- CQ9: Identify principles and risks.
- CQ10: Attach every accepted item to evidence in the chunk.
- CQ11: Link task labels to NCS capability candidates when supported.
- CQ12: Link task labels to PCF process candidates when supported.

Taxonomy snippets:
{retrieved NCS/PCF mapping snippets for the current run}

Rules:
- Every node, edge, and mapping must include evidence_anchor_ids from the chunk.
- Use only the listed node types and edge predicates. Invalid schema terms will be rejected.
- Do not use outside knowledge.
- Keep Korean labels when the source text is Korean.
- Prefer concise, reusable labels.
- Hard limit: return at most 5 nodes, at most 5 edges, and at most 3 mappings.
- If the chunk does not support a field, return an empty array for that field.

Allowed node types for this condition:
["Artifact", "ArtifactFlow", "DecisionGateway", "DomainTask", "GuardCondition", "Principle", "ProcedureStep", "ReviewCheckpoint", "Risk", "Role"]

Allowed edge predicates for this condition:
["BRANCHES_TO", "FEEDS_INTO", "HAS_DECISION_GATEWAY", "HAS_GUARD_CONDITION", "HAS_PRINCIPLE", "HAS_REVIEW_CHECKPOINT", "HAS_RISK", "HAS_STEP", "PRECEDES", "PERFORMED_BY", "PRODUCES", "USED_AS_INPUT_FOR", "USES_INPUT"]

JSON shape:
{
  "nodes": [
    {
      "label": "string",
      "type": "node type",
      "evidence_anchor_ids": ["sentence ids"],
      "confidence": 0.0
    }
  ],
  "edges": [
    {
      "subject": "string",
      "subject_type": "node type",
      "predicate": "edge predicate",
      "object": "string",
      "object_type": "node type",
      "evidence_anchor_ids": ["sentence ids"],
      "confidence": 0.0
    }
  ],
  "mappings": [
    {
      "source_task": "text-supported task label",
      "standard": "NCS|PCF",
      "target_label": "taxonomy label from snippets",
      "evidence_anchor_ids": ["sentence ids"],
      "confidence": 0.0
    }
  ]
}

Return ONLY one valid JSON object. No markdown. No explanation.
Every extracted item must include at least one evidence_anchor_ids value from the chunk.
Do not use outside knowledge. Keep Korean labels when the source text is Korean.

Chunk metadata:
chunk_id: {chunk_id}
pages: {page_start}..{page_end}
sentence_ids: {sentence_ids}

Chunk sentences:
{sentence_id: sentence text}

/no_think
Return exactly one compact JSON object now.
```

핵심은 LLM에게 자유로운 설명을 요청한 것이 아니라, `nodes`, `edges`, `mappings`만 들어 있는 JSON을 강제했다는 점입니다.

---

## 8. Node는 어떤 방식으로 산출했는가

Layer 2 KG의 원본 node는 LLM이 만든 것이 아니라 `scripts/build_ax_epak_internal_kg.py`에서 규칙 기반으로 생성했습니다.

Node 생성 흐름은 다음과 같습니다.

1. OCR 문장을 정제하고 sentence-level evidence anchor를 만듭니다.
   - 예: `EA-JS-00235`
2. 사전에 정의한 task seed catalog를 사용합니다.
   - 예: `기회분석`, `수주영업`, `제안참여 의사결정`, `고객 니즈 분석`, `제안서 기획` 등
3. 각 task seed의 keyword/alias가 OCR body sentence에 등장하는지 찾습니다.
4. 해당 evidence sentence에서 artifact, role, decision, principle, risk term을 찾습니다.
5. 발견된 항목을 node type별로 canonical node로 만듭니다.
6. 각 node에는 반드시 evidence anchor를 연결합니다.
7. 중복 node는 canonical ID 기준으로 병합합니다.

Layer 2 node type별 산출 결과:

| node type | count |
| --- | ---: |
| ProcedureStep | 99 |
| DomainTask | 22 |
| Artifact | 14 |
| GuardCondition | 13 |
| Role | 10 |
| ArtifactFlow | 9 |
| Principle | 5 |
| DecisionGateway | 4 |
| Risk | 3 |
| Total | 179 |

Node record의 핵심 필드는 다음과 같습니다.

```json
{
  "node_id": "L2_TASK_OPPORTUNITY_ASSESSMENT",
  "label": "기회분석",
  "type": "DomainTask",
  "layer": "Layer2",
  "definition": "원문 evidence 기반 정의",
  "label_ko": "기회분석",
  "label_en": "Opportunity Assessment",
  "aliases": ["Opportunity Assessment", "기회 분석"],
  "evidence_anchor_ids": ["EA-JS-00235", "EA-JS-00251"],
  "review_status": "accepted_by_rule_pending_human_review"
}
```

---

## 9. Edge는 어떤 방식으로 산출했는가

Layer 2 edge도 원본 KG build에서는 규칙 기반으로 생성했습니다. 핵심 규칙은 "schema에 허용된 predicate만 쓰고, source/target node가 모두 존재하며, evidence anchor가 있는 edge만 최종 Layer 2 graph에 남긴다"입니다.

Edge 생성 흐름:

1. Task frame에서 input artifact를 찾으면 `DomainTask -USES_INPUT-> Artifact`를 생성합니다.
2. Task frame에서 output artifact를 찾으면 `DomainTask -PRODUCES-> Artifact`를 생성합니다.
3. 수행 role이 있으면 `DomainTask -PERFORMED_BY-> Role`을 생성합니다.
4. decision term이 있으면 `DomainTask -HAS_DECISION_GATEWAY-> DecisionGateway`를 생성합니다.
5. decision evidence에서 조건 문장이 잡히면 `DecisionGateway -HAS_GUARD_CONDITION-> GuardCondition`을 생성합니다.
6. procedure template 또는 inferred step label을 사용해 `DomainTask -HAS_STEP-> ProcedureStep`을 생성합니다.
7. 같은 task 안의 step 순서를 사용해 `ProcedureStep -PRECEDES-> ProcedureStep`을 생성합니다.
8. artifact flow rule에 따라 `Artifact -FEEDS_INTO-> DomainTask`와 `Artifact -USED_AS_INPUT_FOR-> DomainTask`를 생성합니다.
9. 최종적으로 source/target node 존재, allowed predicate, evidence 존재 여부를 검증합니다.

Layer 2 predicate별 산출 결과:

| predicate | count |
| --- | ---: |
| PRODUCES | 220 |
| USES_INPUT | 201 |
| PERFORMED_BY | 120 |
| HAS_STEP | 99 |
| PRECEDES | 77 |
| HAS_PRINCIPLE | 64 |
| HAS_DECISION_GATEWAY | 54 |
| HAS_RISK | 39 |
| HAS_GUARD_CONDITION | 14 |
| FEEDS_INTO | 9 |
| USED_AS_INPUT_FOR | 9 |
| Total | 906 |

Edge record의 핵심 필드는 다음과 같습니다.

```json
{
  "edge_id": "sha1(source_id + predicate + target_id)",
  "source_id": "L2_TASK_OPPORTUNITY_ASSESSMENT",
  "predicate": "USES_INPUT",
  "target_id": "L2_ARTIFACT_ARTIFACT_CAPTURE_PLAN",
  "evidence_anchor_ids": ["EA-JS-00235", "EA-JS-00251"],
  "confidence": 0.785,
  "layer": "Layer2",
  "review_status": "accepted_by_rule"
}
```

---

## 10. Node/Edge 검증 기준

최종 Layer 2 graph에 들어간 edge는 다음 조건을 통과해야 합니다.

| 검증 항목 | 현재 결과 |
| --- | --- |
| source node 존재 | PASS |
| target node 존재 | PASS |
| allowed predicate 사용 | PASS |
| domain/range constraint 위반 없음 | PASS |
| dangling edge 없음 | PASS |
| evidence-missing edge 없음 | PASS |
| accepted Layer 2 edge evidence coverage | 100% |

Structural evaluation 결과:

| metric | value |
| --- | ---: |
| Ontology conformance rate | 1.000 |
| Domain/range violations | 0 |
| Dangling edges | 0 |
| Evidence-missing edges | 0 |
| Procedural consistency rate | 0.995043 |
| PRECEDES cycle count | 0 |
| CQ answerability rate | 0.916667 |

---

## 11. NCS/PCF mapping은 어떻게 산출했는가

Layer 2의 `DomainTask` 22개를 Layer 1 표준 taxonomy에 연결하기 위해 Top-K candidate mapping을 만들었습니다.

방법:

1. Layer 2 task label, Korean/English label, definition, aliases를 하나의 task text로 만듭니다.
2. NCS target은 `NCSCompetencyUnit`, PCF target은 `PCFElement`를 사용합니다.
3. task text와 target text 사이의 lexical / TF-IDF similarity 기반 점수를 계산합니다.
4. 각 task별 top candidates를 생성합니다.
5. 자동 accept하지 않고 expert review 대상으로 둡니다.

산출 결과:

| mapping | rows | 상태 |
| --- | ---: | --- |
| Layer2 -> NCS candidates | 110 | expert review pending |
| Layer2 -> PCF candidates | 110 | expert review pending |
| Total mapping candidates | 220 | expert review pending |

최근 정리된 review 기준:

| 항목 | 값 |
| --- | ---: |
| 전체 mapping candidate rows | 220 |
| 우선 검수 source-task-standard groups | 20 |
| 우선 검수 top-5 candidate rows | 100 |

즉, mapping expert에게는 "20개 그룹만 본다"가 아니라 "20개 우선 그룹에 대해 각 top-5 후보, 총 100 rows를 검수한다"고 설명해야 합니다.

---

## 12. LLM 실험에서 산출한 것은 무엇인가

LLM 실험은 KG 원본 build가 아니라 evaluation condition별 prediction 생성입니다.

LLM 출력 JSON의 기본 단위:

| 출력 필드 | 의미 |
| --- | --- |
| `nodes` | chunk에서 추출한 candidate node labels/types |
| `edges` | candidate subject-predicate-object relations |
| `mappings` | NCS/PCF taxonomy bridge candidate |
| `evidence_anchor_ids` | 해당 item을 지지하는 sentence IDs |
| `confidence` | 모델 confidence |

주요 결과는 silver reference 기준 진단입니다.

| 모델 | condition | rows | pred edges | exact F1 | predicate F1 | evidence F1 | claim status |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3-8B | P_cape_kg_actual | 120 | 275 | 0.0018 | 0.0482 | 0.0655 | silver/proxy |
| Qwen3-14B | P_cape_kg_actual | 120 | 332 | 0.0017 | 0.0601 | 0.0610 | silver/proxy |
| Qwen3-32B-AWQ | P_cape_kg_actual | 120 | 360 | 0.0034 | 0.0662 | 0.0542 | silver/proxy |

해석:

- 32B-AWQ가 8B보다 proposed condition에서 silver predicate F1과 exact F1은 높습니다.
- 그러나 evidence F1은 8B보다 낮으므로 "큰 모델이면 항상 더 좋다"고 말하면 안 됩니다.
- 이 표는 human-gold가 아니라 silver/proxy 진단이므로 논문 final main table이 아닙니다.

---

## 13. 발표에서 강조해야 할 핵심 메시지

교수님께는 다음 순서로 설명하는 것이 가장 안전합니다.

1. 먼저 KG 구축 자체가 무엇인지 설명합니다.
   - OCR sentence를 evidence anchor로 만들고, task/step/artifact/role/decision/risk node와 edge를 생성했다.
2. 그다음 CQ가 schema와 extraction을 통제하는 설계 장치였다고 설명합니다.
   - "무엇을 뽑을지"를 CQ로 먼저 정의했고, CQ가 predicate 설계와 evaluation으로 이어졌다.
3. Node/edge 생성은 원본 KG build와 LLM 실험을 분리해서 설명합니다.
   - 원본 KG: deterministic rule-based, evidence-grounded, validator 통과
   - LLM 실험: 120 chunks에서 baseline/proposed 비교용 predictions 생성
4. 현재 수치 결과를 제시합니다.
   - Layer 2: 179 nodes, 906 edges
   - Evidence-missing edge: 0
   - CQ answerability: 11/12
   - NCS/PCF mapping candidates: 220
5. 마지막으로 claim gate를 설명합니다.
   - Claim gate FAIL은 실험 실패가 아니라 human-gold가 없기 때문에 최종 성능 claim을 막는 안전장치다.

---

## 14. 아직 남은 일

논문용 final result table을 만들려면 아래가 필요합니다.

| 남은 항목 | 현재 상태 | 필요한 작업 |
| --- | --- | --- |
| Human-gold annotation | 0 completed chunks | 최소 100 chunks A/B annotation |
| IAA | 미계산 | annotator A/B 완료 후 agreement 계산 |
| Adjudication | 0 chunks | adjudicator가 최종 gold 확정 |
| Human-gold scoring | 미완료 | B0-B6, P, ablation을 adjudicated gold로 재평가 |
| Mapping expert review | 220 rows pending | 우선 top-20 groups x top-5 = 100 rows 검수 |
| Crosswalk expert review | 220 rows pending | NCS-PCF crosswalk 후보 검수 |
| Active-review effort evidence | 204 rows pending | 실제 검수 시간/노력 기록 |

따라서 현재 단계의 정확한 표현은 다음입니다.

> "CAPE-KG 방법론에 따라 한국어 수주/제안 업무 문서의 evidence-grounded procedural KG와 LLM 비교 실험 패키지는 구축 완료되었다. 다만 논문에서 최종 성능 우수성을 주장하려면 adjudicated human-gold와 expert review가 아직 필요하다."

---

## 15. 교수님께 보여줄 수 있는 가장 짧은 핵심 표

| 질문 | 답 |
| --- | --- |
| 어떤 연구인가? | 한국어 업무 문서에서 evidence-grounded procedural KG를 구축하고 평가하는 연구 |
| 어떤 프롬프트를 썼는가? | CQ + schema + evidence + validator + NCS/PCF bridge를 강제하는 JSON-only prompt |
| CQ는 어떻게 만들었는가? | 연구자가 KG가 답해야 할 12개 질문을 설계하고 predicate/schema와 연결 |
| node는 어떻게 만들었는가? | task seed, term dictionary, OCR evidence matching으로 canonical node 생성 |
| edge는 어떻게 만들었는가? | input/output/role/decision/step/flow 규칙으로 allowed predicate edge 생성 |
| evidence는 어떻게 붙였는가? | 모든 accepted Layer 2 edge에 sentence-level evidence anchor 연결 |
| 현재 KG는 완성됐는가? | 자동 구축 기준으로 Layer 1/Layer 2 KG는 완료 |
| 최종 논문 성능표가 나왔는가? | 아직 아님. human-gold/adjudication 이후 가능 |
| LLM은 썼는가? | 원본 KG 구축에는 미사용, LLM 비교/진단 실험에는 Qwen3-8B/14B/32B-AWQ 사용 |

