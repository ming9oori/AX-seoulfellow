# 교수님 보고용 핵심본: Prompt, CQ, Node/Edge 산출 방식

Generated: 2026-06-29  
Related slide draft: `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md`  
Experiment directory: `experiments/cape_kg_eacl_20260627`  
KG output directory: `outputs`

이 문서는 위 슬라이드 원고와 별개로 만든 **핵심 내용 중심 요약본**입니다. 목적은 PPT에 바로 복사하기보다, 교수님께 연구 방법론을 설명할 때 반드시 짚어야 할 질문에 빠르게 답하는 것입니다.

핵심 질문은 다음 네 가지입니다.

1. 어떤 연구 방법론을 적용했는가?
2. 어떤 CQ와 prompt를 사용했는가?
3. node와 edge는 각각 어떤 규칙과 evidence로 산출했는가?
4. 현재까지 어떤 결과는 주장 가능하고, 어떤 결과는 아직 주장하면 안 되는가?

---

## 1. 한 문장 요약

본 연구는 한국어 수주/제안 업무 문서에서 업무 task, step, input/output artifact, role, decision, guard condition, risk를 추출하여 **원문 sentence evidence에 연결된 procedural KG**를 구축하고, 이를 NCS/PCF 표준 taxonomy와 연결하는 CAPE-KG 실험입니다.

중요한 점은 다음입니다.

> 최종 Layer 2 KG는 LLM이 생성한 JSON을 그대로 저장한 결과가 아니라, CQ, schema, evidence anchor, validator, deterministic rule, mapping module을 결합해 만든 evidence-grounded KG입니다. LLM은 baseline/proposed/ablation/model-scaling 실험에서 사용되었고, 최종 성능 claim은 human-gold 검수 후에만 가능합니다.

---

## 2. 현재까지 나온 핵심 결과

| 항목 | 현재 값 |
| --- | ---: |
| OCR evidence anchors | 5,009 |
| OCR chunks | 214 |
| Layer 1 NCS nodes | 4,109 |
| Layer 1 PCF nodes | 5,301 |
| Layer 2 KG nodes | 220 |
| Layer 2 KG edges | 947 |
| Canonical DomainTask | 22 |
| ProcedureStep | 99 |
| NCS mapping candidates | 110 |
| PCF mapping candidates | 110 |
| NCS-PCF crosswalk candidates | 220 |
| LLM evaluation chunks | 120 |
| LLM experiment conditions | 14 |

현재 상태 해석:

| 구분 | 상태 | 교수님께 보고할 표현 |
| --- | --- | --- |
| KG 구축 | 완료 | Layer 1 표준 KG와 Layer 2 업무 KG 구축 완료 |
| Evidence grounding | 완료 | 최종 Layer 2 edge 947개 모두 evidence anchor 보유 |
| Ontology conformance | diagnostic 완료 | unknown predicate/type, dangling edge, domain/range violation 없음 |
| CQ answerability | diagnostic 완료 | 12개 CQ 모두 현재 KG 구조상 답변 가능 |
| LLM baseline/ablation | 실행 완료 | Qwen3 기반 14개 조건, 120 chunks 실행 |
| 최종 성능 claim | 아직 불가 | human-gold, IAA, adjudication, expert review 전 |
| Claim gate | FAIL | 실험 실패가 아니라, human evidence 없이 최종 논문 claim을 막는 안전장치 |

---

## 3. 연구 방법론 핵심

CAPE-KG는 단순한 LLM triple extraction이 아니라 다음 구성 요소를 결합한 방법론입니다.

| 구성 요소 | 역할 |
| --- | --- |
| Competency Questions | KG가 답해야 할 연구/업무 질문을 먼저 정의 |
| Procedural Schema | `DomainTask`, `ProcedureStep`, `Artifact`, `Role`, `DecisionGateway` 등 node type 정의 |
| Predicate Constraints | `HAS_STEP`, `USES_INPUT`, `PRODUCES`, `PERFORMED_BY` 등 허용 edge type 제한 |
| Evidence Grounding | node/edge를 OCR sentence/page/chunk evidence anchor에 연결 |
| Validator | unknown type/predicate, domain-range violation, dangling edge, evidence 누락 검증 |
| Standard Bridge | Layer 2 업무 KG를 NCS/PCF taxonomy 후보와 연결 |
| Human Review Handoff | 최종 논문 claim을 위한 gold annotation, IAA, adjudication 준비 |

전체 흐름:

1. OCR workbook 정제
2. sentence-level evidence anchor 생성
3. NCS/PCF Layer 1 표준 KG 구축
4. 업무 문서를 chunk 단위로 분할
5. CQ와 Layer 2 procedural schema 정의
6. task seed, alias, keyword로 DomainTask 후보 생성
7. task frame에서 step, artifact, role, decision, guard, risk 후보 생성
8. predicate별 규칙으로 triple/edge 생성
9. schema/evidence validator로 검증
10. 최종 Layer 2 nodes/edges 저장
11. NCS/PCF mapping 후보와 NCS-PCF crosswalk 후보 생성
12. LLM baseline/proposed/ablation/model-scaling 실험 실행
13. human review package, claim gate, release bundle 생성

---

## 4. CQ는 어떻게 만들었는가

CQ는 LLM이 자동으로 만든 질문이 아니라, 연구자가 먼저 정의한 **KG 요구사항**입니다. 즉, "이 KG가 어떤 질문에 답할 수 있어야 하는가"를 정하고, 각 질문을 node type과 predicate에 연결했습니다.

생성 원칙:

| 단계 | 내용 |
| --- | --- |
| 연구 문제 정의 | 한국어 수주/제안 업무 문서에서 절차형 업무 KG 구축 |
| 질문 범주 설정 | 업무 구성, 절차 순서, 입력, 산출물, 수행자, 의사결정, 조건, 리뷰, 원칙, 위험, evidence, 표준 연결 |
| schema 연결 | 질문을 `DomainTask`, `ProcedureStep`, `Artifact`, `Role`, `DecisionGateway`, `GuardCondition` 등에 연결 |
| predicate 연결 | 질문을 `HAS_STEP`, `PRECEDES`, `USES_INPUT`, `PRODUCES`, `PERFORMED_BY` 등에 연결 |
| 실험 재사용 | LLM prompt, ablation, structural evaluation, review priority에서 같은 CQ를 사용 |

CQ source files:

| 목적 | 파일 |
| --- | --- |
| EACL 실험 CQ | `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json` |
| 내부 KG build CQ | `outputs/03_schema/competency_questions.json` |
| CQ/schema 생성 코드 | `scripts/build_cape_kg_eacl_experiment.py`, `scripts/build_ax_epak_internal_kg.py` |

---

## 5. 실제 CQ 목록

| CQ | 질문 | 연결 predicate |
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

CQ가 실제 설계에 준 영향:

| CQ | 설계 영향 |
| --- | --- |
| CQ1 | `DomainTask`와 `ProcedureStep`을 분리하고, `HAS_STEP`, `PRECEDES` edge를 둠 |
| CQ2, CQ3 | input/output을 구분하기 위해 `Artifact`, `USES_INPUT`, `PRODUCES`를 둠 |
| CQ4 | 수행자/책임 주체를 표현하기 위해 `Role`, `PERFORMED_BY`를 둠 |
| CQ5, CQ6 | 의사결정과 조건을 분리하기 위해 `DecisionGateway`, `GuardCondition`을 둠 |
| CQ7 | 산출물이 다음 업무 입력으로 흘러가는 구조를 `FEEDS_INTO`, `USED_AS_INPUT_FOR`로 표현 |
| CQ11, CQ12 | 업무 KG를 NCS/PCF 표준 taxonomy와 연결하는 mapping 후보를 생성 |

---

## 6. 실제 prompt와 산출물

Prompt 파일 위치:

`experiments/cape_kg_eacl_20260627/02_schema/prompts/`

조건별 실제 prompt text와 산출물 형태:

| 조건 | 목적 | 실제 prompt file text | 산출 key |
| --- | --- | --- | --- |
| `B0_plain_llm` | schema 없이 plain triple 추출 | `Extract subject-predicate-object triples from the chunk. Return JSON only.` | `triples` |
| `B1_predicate_constrained` | 허용 predicate만 제한 | `Extract triples using only the allowed predicates. Return JSON only with evidence sentence ids.` | `edges` |
| `B2_current_project` | 기존 방식 baseline | `Extract Task Frames, then triples, then post-process into the Layer2 schema.` | `nodes`, `edges` |
| `B3_edc_style` | open-schema EDC-style baseline | `Extract, define, and canonicalize open-schema KG items, then emit CAPE-compatible nodes and edges for scoring.` | `nodes`, `edges` |
| `B4_taxonomy_rag` | taxonomy retrieval baseline | `Retrieve NCS/PCF/task taxonomy snippets, then extract schema-constrained triples with evidence.` | `nodes`, `edges`, `mappings` |
| `B5_procedural_prompt` | 절차형 prompt baseline | `Extract actions, actors, gateways, guard conditions, artifact flows, and temporal/logical dependencies.` | `nodes`, `edges` |
| `B6_sac_kg_verifier_pruner` | SAC-KG-style verifier/pruner baseline | `Use existing generator candidates, then apply schema/evidence verification and pruning in the style of SAC-KG. This is a deterministic approximation, not a full SAC-KG reproduction.` | `nodes`, `edges`, `mappings` |
| `P_cape_kg_actual` | 제안 방법론 | `Use CQ-linked schema retrieval, procedural frame extraction, evidence-span constrained relation extraction, span verification, ontology validation, procedural consistency checks, and active review scoring.` | `nodes`, `edges`, `mappings` |
| `P_minus_CQ` | CQ 제거 ablation | runtime condition only | `nodes`, `edges`, `mappings` |
| `P_minus_Evidence` | evidence 요구 약화 ablation | runtime condition only | `nodes`, `edges`, `mappings` |
| `P_minus_Procedural_schema` | procedural schema 제거 ablation | runtime condition only | `nodes`, `edges`, `mappings` |
| `P_minus_Validator` | validator 제거 ablation | runtime condition only | `nodes`, `edges`, `mappings` |
| `P_minus_Standard_bridge` | NCS/PCF bridge 제거 ablation | runtime condition only | `nodes`, `edges` |
| `P_minus_Schema_retrieval` | chunk-specific schema retrieval 제거 ablation | `Run CAPE-KG without chunk-specific schema/taxonomy retrieval; keep CQ, evidence grounding, procedural schema, validation, and mapping output shape.` | `nodes`, `edges`, `mappings` |

중요한 점:

위 한 줄짜리 prompt 파일만 LLM에 들어간 것이 아닙니다. 실제 실행 시 `scripts/run_cape_llm_condition_baselines.py`가 chunk text, sentence id, allowed node type, allowed edge predicate, CQ block, JSON schema, strict JSON contract를 함께 붙였습니다.

공통 runtime 제약:

```text
Return ONLY one valid JSON object. No markdown. No explanation.
Every extracted item must include at least one evidence_anchor_ids value from the chunk.
Do not use outside knowledge. Keep Korean labels when the source text is Korean.

Chunk metadata:
chunk_id: {chunk_id}
pages: {page_start}..{page_end}
sentence_ids: {sentence_ids}

Chunk sentences:
{sentence_block}
```

strict JSON 실행 제약:

```text
Strict JSON contract:
- Return exactly one JSON object and nothing else.
- The first non-whitespace character must be `{` and the last non-whitespace character must be `}`.
- Do not include markdown, code fences, comments, XML tags, `<think>` blocks, prose, or explanations.
- For Qwen/Qwen-style chat models, obey `/no_think`; do not emit hidden or visible reasoning.
- Use compact JSON without indentation or extra whitespace to reduce truncation risk.
```

제안 방법론 `P_cape_kg_actual`의 핵심 runtime prompt 구조:

```text
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

Allowed node types:
{allowed_node_types}

Allowed edge predicates:
{allowed_edge_predicates}

Return JSON with:
{
  "nodes": [...],
  "edges": [...],
  "mappings": [...]
}
```

---

## 7. Node는 어떻게 산출했는가

최종 Layer 2 node 수: **220개**  
Evidence가 연결된 node: **220 / 220**

Node 생성 원리:

1. 먼저 업무 문서에서 task seed, alias, keyword를 기준으로 관련 sentence evidence를 찾음
2. 찾은 evidence를 바탕으로 `DomainTask`를 생성
3. task별 procedure template과 입력/산출물 표현을 이용해 `ProcedureStep`을 생성
4. sentence 안의 용어 매칭으로 `Artifact`, `Role`, `Principle`, `Risk`를 생성
5. 검토/승인/점검 신호가 있는 step에서 `ReviewCheckpoint`를 생성
6. 의사결정 표현에서 `DecisionGateway`를 만들고, 조건 표현에서 `GuardCondition`을 생성
7. 산출물이 다음 task의 입력으로 쓰이는 경우 `ArtifactFlow`를 생성

Node type별 현재 수량과 생성 규칙:

| node type | count | 생성 방식 |
| --- | ---: | --- |
| `ProcedureStep` | 99 | task별 procedure template 또는 입력/산출물 기반 step 추론 |
| `ReviewCheckpoint` | 41 | 검토/리뷰/점검/승인/확인 신호가 있는 step에서 투영 |
| `DomainTask` | 22 | task seed의 label/alias/keyword로 OCR sentence evidence 검색 |
| `Artifact` | 14 | task evidence 안의 입력물/산출물 용어 매칭 |
| `GuardCondition` | 13 | 의사결정 evidence에서 조건/가능성/경쟁/자원 표현 추출 |
| `Role` | 10 | 수행자/책임 주체 용어 매칭 |
| `ArtifactFlow` | 9 | 특정 산출물이 다음 task 입력으로 쓰이는 규칙에서 생성 |
| `Principle` | 5 | 원칙/품질 기준 용어 매칭 |
| `DecisionGateway` | 4 | 의사결정 관련 용어 매칭 |
| `Risk` | 3 | 위험/불리함/실패 가능성 용어 매칭 |

Node 산출 파일:

`outputs/07_layer2_graph/layer2_nodes.jsonl`

---

## 8. Edge는 어떻게 산출했는가

최종 Layer 2 edge 수: **947개**  
Evidence가 연결된 edge: **947 / 947**  
Dangling edge: **0개**

Edge 생성 원리:

1. node가 먼저 생성된 뒤, source node와 target node를 predicate 규칙에 맞게 연결
2. 각 predicate는 domain/range 제약을 가짐
3. 각 edge는 evidence anchor를 가져야 최종 accepted edge가 됨
4. schema-valid triple만 최종 `layer2_edges.jsonl`에 반영
5. 최종 edge는 `source_triple_ids`로 원래 triple 산출물과 연결됨

Predicate별 현재 수량과 생성 규칙:

| predicate | count | 생성 방식 |
| --- | ---: | --- |
| `PRODUCES` | 220 | task/step의 outputs slot을 `Artifact` node로 연결 |
| `USES_INPUT` | 201 | task/step의 inputs slot을 `Artifact` 또는 `Concept`로 연결 |
| `PERFORMED_BY` | 120 | task/step의 roles slot을 `Role` node로 연결 |
| `HAS_STEP` | 99 | `DomainTask`를 해당 `ProcedureStep` 목록에 연결 |
| `PRECEDES` | 77 | 같은 task 안에서 step order 기준으로 순서 연결 |
| `HAS_PRINCIPLE` | 64 | task/step의 principles slot을 `Principle` node로 연결 |
| `HAS_DECISION_GATEWAY` | 54 | task/step에서 발견된 의사결정 node를 연결 |
| `HAS_REVIEW_CHECKPOINT` | 41 | 검토/리뷰/점검/승인/확인 신호 step을 review checkpoint로 연결 |
| `HAS_RISK` | 39 | task/step의 risks slot을 `Risk` node로 연결 |
| `HAS_GUARD_CONDITION` | 14 | `DecisionGateway`에서 추출된 조건 node를 연결 |
| `FEEDS_INTO` | 9 | artifact가 다음 task로 흘러가는 규칙을 연결 |
| `USED_AS_INPUT_FOR` | 9 | artifact가 다음 task 입력으로 사용되는 규칙을 연결 |

Edge 산출 파일:

`outputs/07_layer2_graph/layer2_edges.jsonl`

중간 triple 파일:

`outputs/06_triples/layer2_triples_schema_valid.jsonl`

---

## 9. LLM을 어디에 사용했는가

LLM은 사용했습니다. 다만 역할을 구분해야 합니다.

| 구분 | LLM 사용 여부 | 설명 |
| --- | --- | --- |
| 최종 내부 KG build | 제한적/보조적 | 최종 Layer 2 KG는 rule/schema/evidence 기반 deterministic build로 조립됨 |
| Baseline 실험 | 사용 | plain LLM, predicate-constrained, current-project, taxonomy-RAG, procedural prompt 등 |
| Proposed 실험 | 사용 | `P_cape_kg_actual` 조건에서 CQ/schema/evidence/validator/bridge 결합 prompt 실행 |
| Ablation 실험 | 사용 | CQ, evidence, procedural schema, validator, standard bridge, schema retrieval 제거 조건 실행 |
| Model scaling | 사용 | Qwen3-8B, Qwen3-14B, Qwen3-32B-AWQ 비교 diagnostic 실행 |
| 최종 논문 성능표 | 아직 불가 | human-gold annotation이 없으므로 silver/proxy 결과는 final F1 claim으로 사용 불가 |

현재 실행된 주요 LLM 조건:

| family | conditions |
| --- | --- |
| Baseline | `B0_plain_llm`, `B1_predicate_constrained`, `B2_current_project`, `B3_edc_style`, `B4_taxonomy_rag`, `B5_procedural_prompt`, `B6_sac_kg_verifier_pruner` |
| Proposed | `P_cape_kg_actual` |
| Ablation | `P_minus_CQ`, `P_minus_Evidence`, `P_minus_Procedural_schema`, `P_minus_Validator`, `P_minus_Standard_bridge`, `P_minus_Schema_retrieval` |

실행 모델:

| 모델 | 용도 |
| --- | --- |
| Qwen3-8B | 주요 baseline/proposed/ablation 120 chunk 실행 |
| Qwen3-14B | core condition model-scaling diagnostic |
| Qwen3-32B-AWQ | 더 큰 모델 diagnostic |

---

## 10. 현재 주장 가능한 것과 아직 주장하면 안 되는 것

발표에서 주장 가능한 것:

| 주장 | 근거 |
| --- | --- |
| Layer 1 NCS/PCF KG 구축 완료 | `outputs/01_layer1/` |
| Layer 2 업무 KG 구축 완료 | `outputs/07_layer2_graph/` |
| 최종 Layer 2 edge가 모두 evidence anchor를 가짐 | `outputs/07_layer2_graph/layer2_edges.jsonl` |
| 12개 CQ가 현재 KG 구조상 답변 가능 | `experiments/cape_kg_eacl_20260627/04_evaluation/cq_answerability_structural_metrics.json` |
| ontology conformance diagnostic에서 violation 0 | `experiments/cape_kg_eacl_20260627/04_evaluation/ontology_conformance_metrics.json` |
| NCS/PCF mapping 후보 생성 완료 | `outputs/08_mapping/` |
| LLM baseline/proposed/ablation/model-scaling 실행 완료 | `experiments/cape_kg_eacl_20260627/06_release/experiment_reproduction_card.md` |
| human-review handoff 준비 완료 | `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/` |

아직 주장하면 안 되는 것:

| 아직 불가한 주장 | 이유 |
| --- | --- |
| 제안 방법론이 최종 F1에서 baseline보다 우수하다 | adjudicated human-gold가 아직 없음 |
| mapping 후보가 실제 전문가 기준으로 정확하다 | NCS/PCF expert review가 아직 없음 |
| active review가 사람 검수 시간을 줄였다 | human effort/timing evidence가 아직 없음 |
| silver/proxy score를 논문 main result로 사용 | silver는 자동 기준이므로 final claim 불가 |

현재 claim gate 상태:

| 항목 | 상태 |
| --- | --- |
| Pre-human handoff validation | PASS, 92 checks 중 91 PASS / 1 WARN |
| Revised plan completion | not complete, human evidence pending |
| Claim gate | FAIL |
| 해석 | 실험 실패가 아니라 human-gold 없이 과도한 논문 claim을 막는 보수적 gate |

---

## 11. 교수님께 설명할 때의 핵심 문장

1. "저희 방법론은 LLM에게 자유롭게 triple을 만들게 한 것이 아니라, CQ와 schema로 무엇을 뽑을지 먼저 정의하고, evidence anchor와 validator로 통제했습니다."
2. "CQ는 생성 결과가 아니라 설계 요구사항입니다. CQ가 node type과 edge predicate를 결정했고, prompt와 evaluation에도 같은 CQ를 재사용했습니다."
3. "Node는 task seed, alias, keyword, procedure template, 용어 매칭, evidence sentence를 기반으로 만들었고, edge는 predicate별 domain/range 규칙과 evidence 조건을 통과한 것만 채택했습니다."
4. "현재 KG 구축과 LLM 실험은 완료되었지만, 최종 논문 성능표는 human-gold, IAA, adjudication 이후에만 확정할 수 있습니다."
5. "따라서 지금 발표에서는 구축 완료와 실험 인프라 완료를 주장하고, 성능 우수성 claim은 보류하는 것이 정확합니다."

---

## 12. 바로 확인할 핵심 파일

| 목적 | 파일 |
| --- | --- |
| 최종 Layer 2 nodes | `outputs/07_layer2_graph/layer2_nodes.jsonl` |
| 최종 Layer 2 edges | `outputs/07_layer2_graph/layer2_edges.jsonl` |
| Schema-valid triples | `outputs/06_triples/layer2_triples_schema_valid.jsonl` |
| CQ 파일 | `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json` |
| Prompt 파일 폴더 | `experiments/cape_kg_eacl_20260627/02_schema/prompts/` |
| Prompt-node-edge traceability | `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md` |
| LLM 재현 카드 | `experiments/cape_kg_eacl_20260627/06_release/experiment_reproduction_card.md` |
| Claim 가능한 table | `experiments/cape_kg_eacl_20260627/06_release/claimable_main_table.md` |
| Pre-human validation | `experiments/cape_kg_eacl_20260627/06_release/pre_human_handoff_validation.json` |
| KG viewer | `outputs/09_visualization/kg_viewer.html` |
