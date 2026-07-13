# 교수님 보고용 핵심 요약: Prompt, CQ, Node/Edge 산출 방식

Generated: 2026-06-28  
Experiment: `experiments/cape_kg_eacl_20260627`  
Related detailed slide draft: `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md`

이 문서는 기존의 상세 슬라이드 원고와 별개로, 교수님께 핵심만 보고하기 위한 압축본입니다. 특히 “어떤 프롬프트로 무엇을 산출했는가”, “CQ는 어떻게 만들었는가”, “node와 edge는 어떤 방식으로 만들어졌는가”를 중심으로 정리했습니다.

---

## 1. 한 문장 요약

현재 연구는 한국어 수주·제안 업무 문서에서 **evidence-grounded procedural KG**를 구축하고, 이 KG를 **NCS/PCF 표준 taxonomy**와 연결하는 CAPE-KG 방법론으로 정리되었습니다.

중요한 구분은 다음입니다.

| 구분 | 현재 상태 |
|---|---|
| 최종 Layer 2 KG 구축 | 완료 |
| LLM baseline/proposed/ablation 실행 | 완료 |
| NCS/PCF mapping 후보 생성 | 완료 |
| Neo4j/RDF/HTML 시각화 산출물 | 완료 |
| human-gold annotation | 미완료 |
| IAA/adjudication | 미완료 |
| 최종 main table 성능 claim | 아직 불가 |

따라서 현재 교수님께 보고할 핵심은 “KG 구축과 실험 인프라는 완료되었고, 논문용 최종 성능표는 사람 검수 이후 확정해야 한다”입니다.

---

## 2. 현재 구축된 핵심 결과

| 항목 | 값 | 의미 |
|---|---:|---|
| OCR clean sentences | 5,009 | 원문 업무 문서에서 정제된 sentence |
| Layer 2 chunks | 214 | 전체 업무 KG 구축에 사용한 chunk |
| Evaluation chunks | 120 | LLM baseline/proposed/ablation 평가 subset |
| Layer 1 NCS nodes | 4,109 | NCS 표준 taxonomy node |
| Layer 1 PCF nodes | 5,301 | PCF 표준 taxonomy node |
| Layer 2 KG nodes | 179 | 최종 업무 KG node |
| Layer 2 KG edges | 906 | 최종 업무 KG edge |
| NCS mapping candidates | 110 | Layer 2 task별 NCS Top-K 후보 |
| PCF mapping candidates | 110 | Layer 2 task별 PCF Top-K 후보 |

최종 Layer 2 KG는 LLM 출력물을 그대로 저장한 결과가 아닙니다. 최종 KG는 OCR evidence anchor, task seed, 용어 사전, 절차 템플릿, schema validator를 결합해 만든 rule/schema/evidence 기반 graph입니다.

---

## 3. 방법론의 핵심 구조

CAPE-KG 방법론은 다음 순서로 구성됩니다.

```text
OCR sentence
-> evidence anchor
-> task seed matching
-> procedural frame construction
-> node generation
-> edge/triple generation
-> schema/evidence validation
-> Layer 2 KG assembly
-> NCS/PCF standard bridge
-> LLM baseline/proposed/ablation comparison
-> human review handoff
```

방법론의 핵심 요소는 다음입니다.

| 요소 | 역할 |
|---|---|
| CQ | KG가 답해야 할 질문을 정의 |
| Procedural schema | task, step, artifact, role, decision, risk를 구조화 |
| Evidence grounding | 모든 node/edge가 원문 sentence anchor와 연결되도록 함 |
| Validator | predicate, domain/range, evidence id, JSON 형식을 점검 |
| Standard bridge | Layer 2 업무 KG를 NCS/PCF 표준과 연결 |
| Human review handoff | 최종 논문 claim을 위한 사람 검수 패키지 제공 |

---

## 4. CQ는 어떻게 생성했는가

CQ는 LLM이 자동으로 만든 것이 아니라, 연구자가 먼저 정의한 **KG 요구사항**입니다.

생성 방식은 다음과 같습니다.

1. 연구 문제를 “한국어 업무 문서에서 절차형 KG를 구축하는 문제”로 정의했습니다.
2. KG가 답해야 할 업무 질문을 범주화했습니다.
3. 각 질문을 필요한 node type과 edge predicate로 연결했습니다.
4. 이 CQ를 schema 설계, LLM prompt, validation, structural evaluation에서 재사용했습니다.

CQ는 다음 파일에 저장되어 있습니다.

| 목적 | 파일 |
|---|---|
| EACL 실험용 CQ | `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json` |
| 내부 KG build용 CQ | `outputs/03_schema/competency_questions.json` |
| CQ/prompt/node-edge 추적 문서 | `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md` |

---

## 5. 실제 CQ 목록

| CQ | 질문 | 연결 predicate |
|---|---|---|
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

예를 들어 CQ2와 CQ3 때문에 input/output artifact를 따로 추출하고, CQ5와 CQ6 때문에 decision gateway와 guard condition을 별도 node/edge로 표현합니다. CQ11과 CQ12는 Layer 2 업무 KG를 NCS/PCF 표준 taxonomy와 연결하는 이유입니다.

---

## 6. 어떤 프롬프트로 무엇을 산출했는가

LLM 실험은 baseline, proposed, ablation으로 구성했습니다. 프롬프트 파일은 `experiments/cape_kg_eacl_20260627/02_schema/prompts/`에 있습니다.

| condition | 목적 | 주요 산출 key |
|---|---|---|
| `B0_plain_llm` | schema 없는 일반 triple extraction | `triples` |
| `B1_predicate_constrained` | 허용 predicate만 쓰는 relation extraction | `edges` |
| `B2_current_project` | 기존 task frame/triple 방식 baseline | `nodes`, `edges` |
| `B3_edc_style` | extract-define-canonicalize 스타일 baseline | `nodes`, `edges` |
| `B4_taxonomy_rag` | NCS/PCF/task taxonomy retrieval baseline | `nodes`, `edges`, `mappings` |
| `B5_procedural_prompt` | action/actor/gateway/artifact flow 중심 baseline | `nodes`, `edges` |
| `B6_sac_kg_verifier_pruner` | SAC-KG-style verifier/pruner approximation | `nodes`, `edges` |
| `P_cape_kg_actual` | 제안 방법론 | `nodes`, `edges`, `mappings` |
| `P_minus_CQ` | CQ anchoring 제거 ablation | `nodes`, `edges`, `mappings` |
| `P_minus_Evidence` | evidence anchor 요구 약화 ablation | `nodes`, `edges`, `mappings` |
| `P_minus_Procedural_schema` | procedural schema 제거 ablation | `nodes`, `edges`, `mappings` |
| `P_minus_Validator` | post-hoc validator rejection 제거 ablation | `nodes`, `edges`, `mappings` |
| `P_minus_Standard_bridge` | NCS/PCF bridge 제거 ablation | `nodes`, `edges` |
| `P_minus_Schema_retrieval` | chunk-specific schema/taxonomy retrieval 제거 ablation | `nodes`, `edges`, `mappings` |

---

## 7. 실제 저장된 프롬프트 원문

아래는 프롬프트 파일에 실제 저장된 핵심 원문입니다. 실제 LLM 호출 때는 여기에 chunk sentence, sentence id, allowed schema, JSON output shape가 결합됩니다.

| condition | prompt file | 실제 prompt 원문 |
|---|---|---|
| `B0_plain_llm` | `B0_plain_llm_triple_extraction.txt` | `Extract subject-predicate-object triples from the chunk. Return JSON only.` |
| `B1_predicate_constrained` | `B1_predicate_constrained_llm.txt` | `Extract triples using only the allowed predicates. Return JSON only with evidence sentence ids.` |
| `B2_current_project` | `B2_current_project_baseline.txt` | `Extract Task Frames, then triples, then post-process into the Layer2 schema.` |
| `B3_edc_style` | `B3_edc_style_baseline.txt` | `Extract, define, and canonicalize open-schema KG items, then emit CAPE-compatible nodes and edges for scoring.` |
| `B4_taxonomy_rag` | `B4_taxonomy_rag_baseline.txt` | `Retrieve NCS/PCF/task taxonomy snippets, then extract schema-constrained triples with evidence.` |
| `B5_procedural_prompt` | `B5_procedural_prompt_baseline.txt` | `Extract actions, actors, gateways, guard conditions, artifact flows, and temporal/logical dependencies.` |
| `B6_sac_kg_verifier_pruner` | `B6_sac_kg_verifier_pruner_baseline.txt` | `Use existing generator candidates, then apply schema/evidence verification and pruning in the style of SAC-KG. This is a deterministic approximation, not a full SAC-KG reproduction.` |
| `P_cape_kg_actual` | `P_cape_kg.txt` | `Use CQ-linked schema retrieval, procedural frame extraction, evidence-span constrained relation extraction, span verification, ontology validation, procedural consistency checks, and active review scoring.` |
| `P_minus_Schema_retrieval` | `P_minus_Schema_retrieval.txt` | `Run CAPE-KG without chunk-specific schema/taxonomy retrieval; keep CQ, evidence grounding, procedural schema, validation, and mapping output shape.` |
| `strict_json_contract` | `strict_json_contract.txt` | JSON object만 반환, markdown/설명/XML/`<think>` block 금지, `/no_think`, compact JSON, 빈 배열 사용 |

`P_minus_CQ`, `P_minus_Evidence`, `P_minus_Procedural_schema`, `P_minus_Validator`, `P_minus_Standard_bridge`는 별도 prompt 파일이 아니라 runtime condition으로 구현했습니다. 즉 `P_cape_kg_actual`의 공통 template에서 CQ, evidence, schema, validator, bridge 중 특정 구성요소를 제거하거나 약화한 조건입니다.

---

## 8. 실제 runtime prompt 공통 구조

실제 LLM 호출은 단순 한 줄 prompt만 넣은 것이 아닙니다. `scripts/run_cape_llm_condition_baselines.py`가 다음 정보를 결합해 runtime prompt를 구성했습니다.

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

Allowed node types:
{allowed_node_types}

Allowed edge predicates:
{allowed_edge_predicates}

Required output JSON shape:
{
  "nodes": [...],
  "edges": [...],
  "mappings": [...]
}
```

strict JSON 조건에서는 위 prompt 앞에 `strict_json_contract.txt`가 추가되어 markdown, 설명문, `<think>` block, JSON 외 텍스트를 금지했습니다.

---

## 9. `P_cape_kg_actual`의 핵심

`P_cape_kg_actual`은 단순히 프롬프트를 길게 쓴 조건이 아니라, 다음 요소를 결합한 proposed method입니다.

```text
CQ anchoring
-> schema/taxonomy retrieval
-> procedural frame extraction
-> evidence-constrained node/edge extraction
-> span/evidence verification
-> ontology validation
-> procedural consistency checks
-> active review scoring
-> NCS/PCF standard bridge
```

제안 방법론의 핵심 제약은 다음입니다.

| 제약 | 내용 |
|---|---|
| CQ anchoring | CQ1-CQ12를 기준으로 추출 대상 고정 |
| Evidence grounding | 각 item은 현재 chunk sentence id를 evidence로 가져야 함 |
| Allowed node types | `DomainTask`, `ProcedureStep`, `Artifact`, `Role`, `DecisionGateway`, `GuardCondition`, `Principle`, `Risk`, `ArtifactFlow` 등 |
| Allowed predicates | `HAS_STEP`, `PRECEDES`, `USES_INPUT`, `PRODUCES`, `PERFORMED_BY`, `HAS_DECISION_GATEWAY`, `HAS_GUARD_CONDITION`, `HAS_PRINCIPLE`, `HAS_RISK`, `FEEDS_INTO`, `USED_AS_INPUT_FOR` 등 |
| Output shape | `nodes`, `edges`, `mappings` |
| Hard limit | chunk당 최대 5 nodes, 5 edges, 3 mappings |
| Standard bridge | NCS/PCF 후보 mapping 출력 |

---

## 10. Node는 어떻게 산출했는가

최종 node 파일은 `outputs/07_layer2_graph/layer2_nodes.jsonl`입니다.

생성 흐름은 다음입니다.

1. OCR sentence를 `EA-*` evidence anchor로 변환했습니다.
2. `TASK_SEEDS`의 label, alias, keyword로 관련 sentence를 찾았습니다.
3. task evidence 안에서 artifact, role, decision, principle, risk 후보를 용어 사전으로 추출했습니다.
4. 각 업무 단위를 `DomainTask` node로 만들었습니다.
5. task별 procedure template과 입력/산출물 구조를 이용해 `ProcedureStep` node를 만들었습니다.
6. 의사결정 문맥에서 `DecisionGateway`와 `GuardCondition`을 만들었습니다.
7. 산출물이 다음 업무 입력으로 쓰이는 경우 `ArtifactFlow`를 만들었습니다.
8. 모든 node에 evidence anchor와 review status를 붙였습니다.

Node type별 결과는 다음입니다.

| node type | count | 생성 방식 |
|---|---:|---|
| `ProcedureStep` | 99 | task별 procedure template 또는 입력/산출물 기반 step 추론 |
| `DomainTask` | 22 | task seed label/alias/keyword와 OCR sentence evidence 매칭 |
| `Artifact` | 14 | task evidence 안의 입력물/산출물 용어 매칭 |
| `GuardCondition` | 13 | 의사결정 evidence에서 조건/가능성/경쟁/자원 표현 추출 |
| `Role` | 10 | 수행자/책임 주체 용어 매칭 |
| `ArtifactFlow` | 9 | 특정 산출물이 다음 task 입력으로 쓰이는 규칙 |
| `Principle` | 5 | 원칙/품질 기준 표현 매칭 |
| `DecisionGateway` | 4 | 의사결정 관련 표현 매칭 |
| `Risk` | 3 | 위험/불리함/실패 가능성 표현 매칭 |

현재 final node는 179개이며, 모두 evidence anchor를 갖도록 구성했습니다.

---

## 11. Edge는 어떻게 산출했는가

최종 edge 파일은 `outputs/07_layer2_graph/layer2_edges.jsonl`입니다.

생성 흐름은 다음입니다.

1. task frame의 `inputs`, `outputs`, `roles`, `principles`, `risks` slot을 edge predicate로 변환했습니다.
2. `DomainTask`와 `ProcedureStep`은 `HAS_STEP`으로 연결했습니다.
3. 같은 task 안의 step 순서는 `PRECEDES`로 연결했습니다.
4. task/step의 입력은 `USES_INPUT`, 산출물은 `PRODUCES`로 연결했습니다.
5. 수행자/책임 주체는 `PERFORMED_BY`로 연결했습니다.
6. 의사결정 지점과 조건은 `HAS_DECISION_GATEWAY`, `HAS_GUARD_CONDITION`으로 연결했습니다.
7. 산출물이 다음 업무로 흘러가면 `FEEDS_INTO`, `USED_AS_INPUT_FOR`로 연결했습니다.
8. source node, target node, allowed predicate, evidence가 모두 확인된 edge만 최종 graph에 남겼습니다.

Predicate별 결과는 다음입니다.

| predicate | count | 생성 방식 |
|---|---:|---|
| `PRODUCES` | 220 | task/step의 output slot을 Artifact node로 연결 |
| `USES_INPUT` | 201 | task/step의 input slot을 Artifact 또는 Concept로 연결 |
| `PERFORMED_BY` | 120 | task/step의 role slot을 Role node로 연결 |
| `HAS_STEP` | 99 | DomainTask를 ProcedureStep 목록에 연결 |
| `PRECEDES` | 77 | 같은 task 안에서 step order 기준으로 연결 |
| `HAS_PRINCIPLE` | 64 | task/step의 principle slot을 Principle node로 연결 |
| `HAS_DECISION_GATEWAY` | 54 | task/step에서 발견된 decision node 연결 |
| `HAS_RISK` | 39 | task/step의 risk slot을 Risk node로 연결 |
| `HAS_GUARD_CONDITION` | 14 | DecisionGateway와 조건 node 연결 |
| `FEEDS_INTO` | 9 | Artifact가 다음 task로 흘러가는 규칙 연결 |
| `USED_AS_INPUT_FOR` | 9 | Artifact가 다음 task 입력으로 쓰이는 규칙 연결 |

검증 결과는 다음입니다.

| 검증 항목 | 값 |
|---|---:|
| Final edges | 906 |
| Evidence가 있는 edges | 906 / 906 |
| `source_triple_ids`가 있는 edges | 906 / 906 |
| Dangling edges | 0 |
| Domain/range violations | 0 |
| Evidence-missing edges | 0 |
| Ontology conformance rate | 1.000 |

---

## 12. Triple, Node, Edge의 관계

중간 산출물 관계는 다음입니다.

| 단계 | 파일 | 의미 |
|---|---|---|
| Task frame | `outputs/04_task_frames/canonical_task_catalog.json` | 22개 canonical 업무 단위 |
| Procedure structure | `outputs/05_procedure/procedure_structures_clean.jsonl` | task별 step/order/decision 구조 |
| Schema-valid triple | `outputs/06_triples/layer2_triples_schema_valid.jsonl` | edge를 SPO/evidence 형식으로 표현한 906개 triple |
| Final nodes | `outputs/07_layer2_graph/layer2_nodes.jsonl` | 최종 graph node 179개 |
| Final edges | `outputs/07_layer2_graph/layer2_edges.jsonl` | 최종 graph edge 906개 |

현재 triple 수와 edge 수가 모두 906인 이유는, 최종 edge를 subject-predicate-object와 evidence로 추적하기 위해 triple record를 중간 표현으로 사용했기 때문입니다.

---

## 13. LLM 출력과 최종 KG의 관계

이 연구에서 가장 오해하기 쉬운 지점은 “LLM이 최종 KG를 만들었는가?”입니다.

정확한 답은 다음입니다.

| 구분 | 설명 |
|---|---|
| 최종 KG | rule/schema/evidence 기반으로 조립한 graph |
| LLM 출력 | baseline/proposed/ablation 조건별 prediction |
| LLM 사용 목적 | 같은 chunk에 대해 방법론 조건별 node/edge/mapping 후보 생성 비교 |
| 최종 신뢰성 근거 | evidence grounding, validator, human-gold evaluation |

따라서 발표에서는 “LLM이 만든 KG”라고 말하기보다, “최종 KG는 evidence/schema 기반으로 구축했고, LLM은 후보 생성 방법론을 비교하기 위한 실험 조건으로 사용했다”고 설명하는 것이 정확합니다.

---

## 14. 현재 실행한 LLM 실험

| 실험 | 상태 |
|---|---|
| Qwen3-8B baseline/proposed/ablation | 실행 완료 |
| Qwen3-14B core condition scaling | 실행 완료 |
| Qwen3-32B-AWQ core condition scaling | 실행 완료 |
| B0/B1/B2 baseline | 120 chunk 실행 완료 |
| B3/B4/B5/B6 baseline family | 실행 완료 |
| `P_cape_kg_actual` | 120 chunk 실행 완료 |
| `P_minus_*` ablation | 6개 조건 실행 완료 |
| strict JSON diagnostics | 실행 완료 |
| public benchmark adapter | PAGED/Text2KG subset 실행 완료 |

단, 현재 LLM 성능 수치는 silver/proxy diagnostic입니다. human-gold annotation이 완료되기 전에는 최종 precision/recall/F1 main table로 주장하면 안 됩니다.

---

## 15. 현재 claim 가능/불가능 구분

| 항목 | 말할 수 있는 것 | 아직 말하면 안 되는 것 |
|---|---|---|
| KG 구축 | Layer 2 KG 179 nodes / 906 edges 구축 완료 | 이 자체가 baseline 대비 성능 우수성을 증명한다는 주장 |
| Evidence | final node/edge가 evidence anchor를 갖도록 구성 | human-gold evidence exact match 우수성 claim |
| LLM 실험 | baseline/proposed/ablation/model scaling 실행 완료 | human-gold F1 우수성 claim |
| NCS/PCF bridge | mapping 후보 110개씩 생성 | expert-confirmed P@K/MRR/nDCG claim |
| Active review | review queue와 effort template 준비 | 실제 검수 시간 절감 claim |
| Release/reproducibility | pre-human validation PASS, public-safe bundle 생성 | 최종 논문 제출 ready claim |

---

## 16. 사람 검수 이후 확정할 것

현재 자동 실험과 handoff는 준비되었지만, 다음 항목이 완료되어야 논문용 main table을 확정할 수 있습니다.

| 남은 항목 | 필요 이유 |
|---|---|
| 100+ chunk human-gold annotation | 최소 제출 claim 기준 |
| 500+ adjudicated node/edge/evidence items | item-level 평가 기준 |
| IAA 계산 | annotator agreement 보고 |
| adjudication | 최종 gold label 확정 |
| `P_cape_kg_actual` human-gold scoring | proposed method 성능표 확정 |
| mapping expert review | NCS/PCF bridge 성능 claim 확정 |

pre-human handoff 검증은 현재 `PASS`이며, 남은 `WARN`은 human-gold/IAA/adjudication이 아직 없다는 의도된 상태 표시입니다.

---

## 17. 교수님께 보고할 핵심 문장

발표에서 다음 문장을 중심으로 설명하면 됩니다.

1. “연구를 단순 업무 온톨로지 구축이 아니라, 한국어 업무 문서 기반 evidence-grounded procedural KG construction task로 재정의했습니다.”
2. “CAPE-KG의 핵심은 CQ, procedural schema, evidence grounding, validator, NCS/PCF bridge를 결합한 것입니다.”
3. “최종 Layer 2 KG는 179 nodes, 906 edges로 구축되었고, 모든 accepted edge는 evidence anchor를 갖습니다.”
4. “LLM은 최종 KG를 그대로 생성한 것이 아니라, baseline/proposed/ablation 조건의 후보 생성기로 사용했습니다.”
5. “실제 prompt는 조건별로 달리 설계했고, `P_cape_kg_actual`은 CQ, schema retrieval, evidence constraint, validator, standard bridge를 결합합니다.”
6. “현재 자동 구축과 실험 실행은 완료되었지만, 논문 main table은 human-gold annotation, IAA, adjudication 이후 확정해야 합니다.”

---

## 18. 같이 열어볼 파일

| 목적 | 파일 |
|---|---|
| 상세 발표 슬라이드 원고 | `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md` |
| 이 핵심 요약본 | `experiments/cape_kg_eacl_20260627/07_reports/professor_report_key_points_prompt_cq_node_edge_20260628_ko.md` |
| prompt/node/edge 추적 | `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md` |
| CQ 원본 | `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json` |
| 최종 node | `outputs/07_layer2_graph/layer2_nodes.jsonl` |
| 최종 edge | `outputs/07_layer2_graph/layer2_edges.jsonl` |
| claimable main table | `experiments/cape_kg_eacl_20260627/06_release/claimable_main_table.md` |
| 제출 완료 감사표 | `experiments/cape_kg_eacl_20260627/06_release/submission_completion_audit_ko.md` |
| human review 시작 안내 | `experiments/cape_kg_eacl_20260627/06_release/human_review_start_here_ko.md` |

