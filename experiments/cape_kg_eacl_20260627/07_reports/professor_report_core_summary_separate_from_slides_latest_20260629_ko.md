# 교수님 보고용 별도 핵심 요약본

Generated: 2026-06-29  
Related full slide draft: `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md`  
Experiment directory: `experiments/cape_kg_eacl_20260627`  
KG output directory: `outputs`

이 문서는 긴 슬라이드 원고와 별개로, 교수님께 핵심만 빠르게 설명하기 위한 별도 파일입니다. 핵심 질문은 다음 네 가지입니다.

1. 어떤 방법론으로 저의 데이터에 KG를 구축했는가
2. 어떤 프롬프트로 어떤 JSON 산출물을 만들었는가
3. CQ는 어떻게 만들었고 node/edge 설계와 어떻게 연결했는가
4. 현재까지 어떤 실험 결과가 나왔고, 무엇은 아직 주장하면 안 되는가

---

## 1. 결론 요약

본 연구는 한국어 수주/제안 업무 문서에서 업무 절차, 입력/산출물, 수행 역할, 의사결정, 위험, 원문 근거를 함께 표현하는 **evidence-grounded procedural KG**를 구축한 실험입니다.

핵심은 단순한 LLM triple extraction이 아닙니다. 현재 최종 KG는 **OCR sentence evidence + Competency Questions + procedural schema + rule/schema-based assembly + validator**로 구축했고, LLM은 동일 task에서 baseline/proposed/ablation 조건의 후보 생성 능력을 비교하기 위해 별도 실행했습니다.

가장 조심해야 할 표현:

> KG 구축과 자동 진단 인프라는 완료되었지만, 논문에서 최종 성능 우수성을 주장하려면 human-gold annotation, IAA, adjudication, expert review가 아직 필요합니다.

---

## 2. 현재까지 구축된 핵심 산출물

| 구분 | 결과 | 의미 |
| --- | ---: | --- |
| OCR clean sentences / evidence anchors | 5,009 | node/edge 근거 문장 단위 |
| Layer 2 source chunks | 214 | 전체 업무 문서 chunk |
| LLM evaluation chunks | 120 | baseline/proposed/ablation 비교 대상 |
| Layer 1 NCS nodes | 4,109 | NCS 표준 taxonomy 축 |
| Layer 1 PCF nodes | 5,301 | PCF 표준 taxonomy 축 |
| Canonical DomainTask | 22 | 수주/제안 업무 단위 |
| Layer 2 nodes | 179 | 최종 업무 KG node |
| Layer 2 edges | 906 | 최종 업무 KG edge |
| Schema-valid triples | 906 | edge 검증용 SPO/evidence 중간 표현 |
| NCS mapping candidates | 110 | 22 tasks x Top-5 후보 |
| PCF mapping candidates | 110 | 22 tasks x Top-5 후보 |
| Evidence-missing edges | 0 | 최종 accepted edge의 evidence 누락 없음 |
| Dangling edges | 0 | 존재하지 않는 node를 가리키는 edge 없음 |
| Type violations | 0 | domain/range 구조 위반 없음 |

핵심 파일:

| 목적 | 파일 |
| --- | --- |
| 최종 Layer 2 nodes | `outputs/07_layer2_graph/layer2_nodes.jsonl` |
| 최종 Layer 2 edges | `outputs/07_layer2_graph/layer2_edges.jsonl` |
| NCS mapping candidates | `outputs/08_mapping/l2_ncs_mapping_candidates.jsonl` |
| PCF mapping candidates | `outputs/08_mapping/l2_pcf_mapping_candidates.jsonl` |
| KG viewer | `outputs/09_visualization/kg_viewer.html` |
| build report | `outputs/10_evaluation/final_build_report.md` |
| 실험 schema | `experiments/cape_kg_eacl_20260627/02_schema/cape_schema.json` |
| CQ 정의 | `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json` |
| prompt 파일 | `experiments/cape_kg_eacl_20260627/02_schema/prompts/` |

---

## 3. 방법론의 핵심 구조

CAPE-KG는 LLM에게 자유롭게 graph를 만들게 하는 방식이 아니라, 다음 제약을 결합한 KG 구축 방법론입니다.

| 구성 요소 | 역할 |
| --- | --- |
| Competency Questions | KG가 답해야 하는 업무 질문을 먼저 정의 |
| Procedural schema | `DomainTask`, `ProcedureStep`, `Artifact`, `Role`, `DecisionGateway` 등으로 업무 구조화 |
| Evidence grounding | 모든 accepted node/edge/mapping이 원문 sentence evidence에 연결되도록 강제 |
| Allowed node/edge schema | 사용할 node type과 predicate를 제한 |
| Validator | JSON parse, evidence ID, predicate, domain/range, type 오류 점검 |
| Standard bridge | Layer 2 업무 KG를 NCS/PCF 표준 taxonomy와 연결 |
| Human-review gate | 사람 검수 전 최종 성능 claim을 막는 안전장치 |

전체 흐름:

1. OCR workbook을 sentence 단위로 정제
2. 각 sentence에 evidence anchor ID 부여
3. NCS/PCF 표준 데이터를 Layer 1 KG로 구축
4. 업무 문서를 Layer 2 chunk로 분할
5. CQ와 procedural schema 정의
6. task seed, alias, keyword, evidence sentence로 `DomainTask` 생성
7. procedure template과 입력/산출물/역할/조건 단서로 node 생성
8. predicate별 규칙과 evidence 조건을 만족하는 edge 생성
9. Layer 2 KG를 NCS/PCF Top-K 후보와 연결
10. LLM baseline/proposed/ablation/model-scaling 조건 실행
11. human review handoff, claim gate, release validation 생성

---

## 4. CQ는 어떻게 만들었는가

CQ는 LLM이 생성한 질문이 아니라, 연구자가 먼저 정의한 **KG 요구사항**입니다. 즉, “이 KG가 어떤 질문에 답할 수 있어야 하는가”를 정하고, 각 질문을 node type과 edge predicate로 연결했습니다.

CQ 생성 방식:

| 단계 | 내용 |
| --- | --- |
| 1 | 연구 문제를 “한국어 수주/제안 업무 문서 기반 procedural KG construction”으로 정의 |
| 2 | 업무 사용자가 실제로 물을 질문 범주를 정리 |
| 3 | 각 질문을 필요한 node type과 predicate에 연결 |
| 4 | 같은 CQ를 schema, prompt, ablation, structural evaluation에서 재사용 |

실제 CQ 목록:

| CQ | 질문 | 연결 predicate/schema |
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

CQ가 KG 설계에 미친 영향:

| CQ | 설계 영향 |
| --- | --- |
| CQ1 | `DomainTask`, `ProcedureStep`, `HAS_STEP`, `PRECEDES` 필요 |
| CQ2, CQ3 | `Artifact`, `USES_INPUT`, `PRODUCES` 필요 |
| CQ4 | `Role`, `PERFORMED_BY` 필요 |
| CQ5, CQ6 | `DecisionGateway`, `GuardCondition` 필요 |
| CQ7 | 산출물 흐름을 표현하는 `FEEDS_INTO`, `USED_AS_INPUT_FOR` 필요 |
| CQ10 | 모든 accepted item에 evidence anchor 필요 |
| CQ11, CQ12 | NCS/PCF mapping 후보 생성 필요 |

---

## 5. 실제 프롬프트와 산출물

프롬프트 파일 위치:

`experiments/cape_kg_eacl_20260627/02_schema/prompts/`

실제 LLM 호출은 두 층으로 구성했습니다.

1. 조건별 prompt 파일의 핵심 지시문
2. runtime에서 자동으로 결합되는 chunk sentence, sentence ID, allowed node/edge type, evidence rule, JSON output shape, strict JSON contract

조건별 핵심 prompt와 요구 산출물:

| 조건 | 실제 prompt text | 요구 산출물 |
| --- | --- | --- |
| `B0_plain_llm` | `Extract subject-predicate-object triples from the chunk. Return JSON only.` | `triples` |
| `B1_predicate_constrained` | `Extract triples using only the allowed predicates. Return JSON only with evidence sentence ids.` | `edges` |
| `B2_current_project` | `Extract Task Frames, then triples, then post-process into the Layer2 schema.` | `nodes`, `edges` |
| `B3_edc_style` | `Extract, define, and canonicalize open-schema KG items, then emit CAPE-compatible nodes and edges for scoring.` | `nodes`, `edges` |
| `B4_taxonomy_rag` | `Retrieve NCS/PCF/task taxonomy snippets, then extract schema-constrained triples with evidence.` | `nodes`, `edges`, `mappings` |
| `B5_procedural_prompt` | `Extract actions, actors, gateways, guard conditions, artifact flows, and temporal/logical dependencies.` | `nodes`, `edges` |
| `B6_sac_kg_verifier_pruner` | `Use existing generator candidates, then apply schema/evidence verification and pruning in the style of SAC-KG. This is a deterministic approximation, not a full SAC-KG reproduction.` | `nodes`, `edges` |
| `P_cape_kg_actual` | `Use CQ-linked schema retrieval, procedural frame extraction, evidence-span constrained relation extraction, span verification, ontology validation, procedural consistency checks, and active review scoring.` | `nodes`, `edges`, `mappings` |
| `P_minus_Schema_retrieval` | `Run CAPE-KG without chunk-specific schema/taxonomy retrieval; keep CQ, evidence grounding, procedural schema, validation, and mapping output shape.` | `nodes`, `edges`, `mappings` |

추가 ablation 조건:

| 조건 | 제거하거나 약화한 요소 | 산출물 |
| --- | --- | --- |
| `P_minus_CQ` | CQ anchoring 제거 | `nodes`, `edges`, `mappings` |
| `P_minus_Evidence` | evidence anchor 요구 약화 | `nodes`, `edges`, `mappings` |
| `P_minus_Procedural_schema` | procedural schema 제거 | `nodes`, `edges`, `mappings` |
| `P_minus_Validator` | validator rejection 제거 | `nodes`, `edges`, `mappings` |
| `P_minus_Standard_bridge` | NCS/PCF bridge 제거 | `nodes`, `edges` |

---

## 6. Runtime prompt에서 실제로 강제한 것

모든 조건의 실제 prompt에는 다음 공통 instruction이 결합되었습니다.

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

Qwen strict JSON 실행에서는 다음 contract도 붙였습니다.

```text
Strict JSON contract:
- Return exactly one JSON object and nothing else.
- Do not include markdown, code fences, comments, XML tags, <think> blocks, prose, or explanations.
- For Qwen/Qwen-style chat models, obey /no_think; do not emit hidden or visible reasoning.
- Use compact JSON without indentation or extra whitespace to reduce truncation risk.
- Use empty arrays for absent nodes, edges, triples, or mappings fields required by the requested shape.
```

`P_cape_kg_actual`에는 다음 핵심 instruction이 추가되었습니다.

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

Rules:
- Every node, edge, and mapping must include evidence_anchor_ids from the chunk.
- Use only the listed node types and edge predicates. Invalid schema terms will be rejected.
- Do not use outside knowledge.
- Keep Korean labels when the source text is Korean.
- Hard limit: return at most 5 nodes, at most 5 edges, and at most 3 mappings.
```

출력 JSON shape:

```json
{
  "nodes": [],
  "edges": [],
  "mappings": []
}
```

따라서 `P_cape_kg_actual`은 CQ, evidence, schema, validator, NCS/PCF bridge를 동시에 반영한 제안 조건입니다.

---

## 7. Node는 어떻게 산출했는가

최종 node 파일:

`outputs/07_layer2_graph/layer2_nodes.jsonl`

중요한 점은 최종 KG node가 LLM raw output을 그대로 저장한 것이 아니라는 점입니다. 최종 node는 OCR sentence evidence, task seed, alias/keyword, 용어 사전, procedure template, schema constraint를 이용해 조립했습니다.

Node 생성 흐름:

1. OCR sentence를 `EA-JS-*` evidence anchor로 변환
2. `TASK_SEEDS`의 업무 label, alias, keyword로 관련 sentence 검색
3. sentence 안에서 artifact, role, decision, principle, risk 후보 추출
4. 관련 evidence가 있는 업무를 `DomainTask` node로 생성
5. task별 procedure template 또는 입력/산출물 단서로 `ProcedureStep` node 생성
6. 산출물이 다음 업무 입력으로 흐르는 경우 `ArtifactFlow` node 생성
7. `node_id` 기준으로 중복 제거
8. 모든 node에 evidence와 review status 부여

Node type별 결과:

| Node type | 개수 | 생성 방식 |
| --- | ---: | --- |
| `ProcedureStep` | 99 | task별 procedure template 또는 입력/산출물 기반 step 추론 |
| `DomainTask` | 22 | task seed label/alias/keyword와 evidence sentence 매칭 |
| `Artifact` | 14 | 입력물/산출물 용어 매칭 |
| `GuardCondition` | 13 | 의사결정 evidence에서 조건 표현 추출 |
| `Role` | 10 | 수행자/책임 주체 용어 매칭 |
| `ArtifactFlow` | 9 | 산출물이 다음 업무 입력으로 쓰이는 흐름 규칙 |
| `Principle` | 5 | 원칙/품질 기준 용어 매칭 |
| `DecisionGateway` | 4 | 의사결정 관련 표현 매칭 |
| `Risk` | 3 | 위험/실패 가능성 표현 매칭 |
| 합계 | 179 |  |

---

## 8. Edge는 어떻게 산출했는가

최종 edge 파일:

`outputs/07_layer2_graph/layer2_edges.jsonl`

Edge는 node 사이 업무 관계를 나타냅니다. 최종 graph에 들어가려면 source node와 target node가 실제로 존재해야 하고, predicate가 허용 목록에 있어야 하며, evidence anchor가 있어야 합니다.

Edge 생성 흐름:

1. task frame의 `inputs`, `outputs`, `roles`, `principles`, `risks` slot을 predicate로 변환
2. decision gateway와 guard condition을 별도 edge로 연결
3. procedure step은 `HAS_STEP`, step 순서는 `PRECEDES`로 연결
4. artifact flow는 `FEEDS_INTO`, `USED_AS_INPUT_FOR`로 연결
5. edge를 triple record로 변환하고 `source_triple_ids` 부여
6. source/target 존재, allowed predicate, evidence 존재 여부 검증
7. 검증을 통과한 edge만 `layer2_edges.jsonl`에 저장

Predicate별 edge 수:

| Predicate | 의미 | 개수 |
| --- | --- | ---: |
| `PRODUCES` | 업무/단계가 산출물을 생성 | 220 |
| `USES_INPUT` | 업무/단계가 입력물을 사용 | 201 |
| `PERFORMED_BY` | 업무/단계의 수행 주체 | 120 |
| `HAS_STEP` | task와 procedure step 연결 | 99 |
| `PRECEDES` | 같은 task 안의 step 순서 | 77 |
| `HAS_PRINCIPLE` | 원칙/품질 기준 연결 | 64 |
| `HAS_DECISION_GATEWAY` | 의사결정 지점 연결 | 54 |
| `HAS_RISK` | 위험 요소 연결 | 39 |
| `HAS_GUARD_CONDITION` | 의사결정 조건 연결 | 14 |
| `FEEDS_INTO` | 산출물이 다음 업무로 흐름 | 9 |
| `USED_AS_INPUT_FOR` | 산출물이 다음 task 입력으로 사용 | 9 |
| 합계 |  | 906 |

검증 결과:

| 검증 항목 | 결과 |
| --- | ---: |
| Final Layer 2 edges | 906 |
| Evidence가 있는 edges | 906 / 906 |
| `source_triple_ids`가 있는 edges | 906 / 906 |
| Dangling edges | 0 |
| Type violations | 0 |

---

## 9. 실행한 LLM 실험

LLM은 최종 KG를 그대로 만든 도구가 아니라, 각 방법론 조건이 같은 chunk에서 어떤 후보 JSON을 만드는지 비교하기 위해 사용했습니다.

실행 모델:

| 모델 | 사용 목적 | 상태 |
| --- | --- | --- |
| Qwen3-8B | 기본 baseline/proposed/ablation | 실행 완료 |
| Qwen3-14B | model scaling core conditions | 실행 완료 |
| Qwen3-32B-AWQ | 현실적인 대형 모델 scaling | 120 chunk core run 완료 |

실행 조건:

| 범주 | 조건 |
| --- | --- |
| Baseline | `B0_plain_llm`, `B1_predicate_constrained`, `B2_current_project`, `B3_edc_style`, `B4_taxonomy_rag`, `B5_procedural_prompt`, `B6_sac_kg_verifier_pruner` |
| Proposed | `P_cape_kg_actual` |
| Ablation | `P_minus_CQ`, `P_minus_Evidence`, `P_minus_Procedural_schema`, `P_minus_Validator`, `P_minus_Standard_bridge`, `P_minus_Schema_retrieval` |
| Scaling | Qwen3-8B, Qwen3-14B, Qwen3-32B-AWQ core conditions |

Qwen3-8B actual LLM output 규모:

| 조건 | chunks | pred nodes | pred edges | pred triples | pred mappings |
| --- | ---: | ---: | ---: | ---: | ---: |
| `B0_plain_llm` | 120 | 1,674 | 0 | 837 | 0 |
| `B1_predicate_constrained` | 120 | 0 | 663 | 0 | 0 |
| `B2_current_project` | 120 | 712 | 82 | 0 | 0 |
| `B3_edc_style` | 120 | 566 | 53 | 0 | 0 |
| `B4_taxonomy_rag` | 120 | 674 | 128 | 0 | 41 |
| `B5_procedural_prompt` | 120 | 957 | 119 | 0 | 0 |
| `B6_sac_kg_verifier_pruner` | 120 | 2,281 | 361 | 0 | 107 |
| `P_cape_kg_actual` | 120 | 549 | 275 | 0 | 52 |

주의: 이 표는 산출물의 양과 구조를 보여주는 진단표입니다. 많이 뽑았다고 좋은 성능이라는 뜻은 아닙니다.

---

## 10. 현재 평가 결과를 어떻게 해석해야 하는가

현재 자동 평가표와 silver/proxy diagnostic은 있습니다. 그러나 human-gold가 아직 없기 때문에 final main performance table로 주장하면 안 됩니다.

Qwen3 계열 `P_cape_kg_actual` silver/proxy diagnostic:

| 모델 | chunks | edge exact F1 | predicate F1 | node label F1 | evidence F1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Qwen3-8B | 120 | 0.0018 | 0.0482 | 0.0326 | 0.0655 |
| Qwen3-14B | 120 | 0.0017 | 0.0601 | 0.0298 | 0.0610 |
| Qwen3-32B-AWQ | 120 | 0.0034 | 0.0662 | 0.0284 | 0.0542 |

해석:

- 이 수치는 human-gold 기준 성능이 아니라 silver/proxy diagnostic입니다.
- edge exact F1은 label, predicate, evidence가 동시에 맞아야 하므로 매우 엄격합니다.
- 현재 claim gate가 FAIL인 이유는 이 결과가 틀렸기 때문이 아니라, human-gold annotation과 IAA가 아직 없기 때문입니다.

---

## 11. 지금 claim 가능한 것과 불가능한 것

| 구분 | 현재 말할 수 있는 것 | 아직 말하면 안 되는 것 |
| --- | --- | --- |
| KG 구축 | Layer 1/Layer 2 KG 구축 완료 | human-gold 정답 대비 성능 우수성 |
| Evidence | 최종 accepted edge 906개 모두 evidence 보유 | evidence span 정확도가 human-gold에서 높다는 claim |
| LLM 실험 | baseline/proposed/ablation/model-scaling 실행 완료 | proposed method가 최종적으로 baseline보다 우수하다는 claim |
| Mapping | NCS/PCF Top-K 후보 생성 완료 | expert review 기준 P@K/MRR/nDCG 우수성 |
| Active review | queue와 template 준비 완료 | 실제 사람 검수 시간을 줄였다는 efficiency claim |
| 제출 준비 | pre-human handoff validation PASS | EACL 제출용 final main table 완료 |

현재 pre-human validation 상태:

| 항목 | 상태 |
| --- | --- |
| Pre-human handoff validation | PASS |
| Checks | 65 |
| PASS | 64 |
| WARN | 1 |
| FAIL | 0 |
| Claim gate | FAIL, expected |
| FAIL 이유 | human-gold, IAA, adjudication, proposed human-gold scoring, expert review 미완료 |

---

## 12. 교수님께 보고할 때의 추천 발표 흐름

1. 연구 문제: 한국어 수주/제안 업무 문서를 procedural KG로 만드는 문제
2. 핵심 방법론: CQ, schema, evidence, validator, standard bridge를 결합한 CAPE-KG
3. 구축 결과: Layer 1 NCS/PCF와 Layer 2 업무 KG 구축 완료
4. 프롬프트: baseline, proposed, ablation별로 서로 다른 JSON 산출물 요구
5. CQ: 12개 질문을 node/edge 설계와 연결
6. Node 생성: task seed, evidence, template, 용어 사전 기반으로 179개 node 구축
7. Edge 생성: predicate별 규칙과 evidence 검증으로 906개 edge 구축
8. LLM 실험: Qwen3-8B/14B/32B-AWQ로 후보 생성 실험 수행
9. 현재 한계: human-gold 전이므로 최종 성능 claim은 보류
10. 다음 단계: 사람 검수, IAA, adjudication, expert review, final main table 생성

---

## 13. 발표에서 그대로 쓸 수 있는 핵심 문장

> 본 연구에서는 한국어 수주/제안 업무 문서에서 절차형 업무 지식을 추출하기 위해 CAPE-KG 방법론을 설계했습니다. CAPE-KG는 단순 LLM triple extraction이 아니라, Competency Question, procedural schema, evidence grounding, validator, NCS/PCF standard bridge를 결합해 node와 edge가 원문 evidence에 연결되도록 만든 방법론입니다.

> 현재 Layer 1 NCS/PCF KG와 Layer 2 업무 KG 구축은 완료되었습니다. Layer 2 KG는 179개 node와 906개 edge로 구성되며, 최종 accepted edge는 모두 evidence anchor를 갖고 dangling edge와 type violation은 없습니다.

> LLM은 최종 KG를 그대로 생성한 도구가 아니라, baseline, proposed, ablation 조건에서 어떤 후보 node/edge/mapping JSON을 생성하는지 비교하기 위해 사용했습니다. 현재 Qwen3-8B, Qwen3-14B, Qwen3-32B-AWQ까지 실행했지만, 이 결과는 human-gold 전 silver/proxy diagnostic으로 해석해야 합니다.

> 최종 논문 성능표를 만들려면 100개 이상 chunk에 대해 두 명 이상의 annotator가 human-gold annotation을 수행하고, IAA와 adjudication을 완료한 뒤 proposed method를 human-gold 기준으로 다시 scoring해야 합니다.

---

## 14. 다음 단계

| 우선순위 | 작업 | 결과물 |
| --- | --- | --- |
| 1 | Annotator A/B가 priority 100 chunks 검수 | reviewed JSONL |
| 2 | IAA 계산 | agreement report |
| 3 | adjudication 수행 | adjudicated gold JSONL |
| 4 | proposed/baseline human-gold scoring | final main table |
| 5 | mapping expert review | NCS/PCF P@K, MRR, nDCG |
| 6 | active-review effort 기록 | active review efficiency table |

human return 이후 refresh 명령:

```bash
PYTHON_BIN=/home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python \
LLM_PYTHON=/home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python \
APPLY_IMPORTS=1 \
bash scripts/run_cape_human_return_apply.sh
```

