# CAPE-KG 교수님 보고용 핵심 요약본

Generated: 2026-06-29  
Experiment: `experiments/cape_kg_eacl_20260627`  
KG outputs: `outputs`  
Related full slide draft: `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md`

이 문서는 기존 슬라이드별 장문 원고와 별개로, 교수님께 먼저 설명드릴 핵심 내용만 압축한 별도 보고용 파일입니다. 초점은 다음 네 가지입니다.

1. 어떤 연구 방법론을 적용했는가
2. 어떤 prompt와 CQ를 사용했는가
3. node와 edge를 어떤 방식으로 산출했는가
4. 현재까지 어떤 실험이 끝났고 무엇이 아직 남았는가

---

## 1. 한 줄 결론

현재 연구는 한국어 수주·제안 업무 문서에서 **evidence-grounded procedural KG**를 구축하고, 이를 **NCS/PCF 표준 taxonomy**와 연결하는 CAPE-KG 방법론으로 정리되었습니다.

자동 구축 관점에서는 Layer 1 표준 KG, Layer 2 업무 KG, evidence grounding, NCS/PCF mapping 후보, LLM baseline/proposed/ablation, public benchmark adapter, Neo4j/RDF/SHACL/release/human-review handoff까지 준비되었습니다.

다만 논문에서 최종 성능 우수성을 주장하려면 아직 사람이 검수한 human-gold annotation, IAA, adjudication, `P_cape_kg_actual` human-gold scoring, mapping expert review, NCS-PCF crosswalk expert review, active-review effort evidence가 필요합니다. 따라서 현재 상태는 **KG 구축 완료, 최종 성능 claim은 보류**로 보고해야 합니다.

---

## 2. 현재까지 구축된 결과

| 항목 | 현재 값 | 해석 |
|---|---:|---|
| Layer 1 NCS nodes | 4,109 | NCS 표준 taxonomy 기준축 |
| Layer 1 PCF nodes | 5,301 | PCF 표준 taxonomy 기준축 |
| OCR sentences | 5,009 | evidence anchor의 기본 단위 |
| Layer 2 chunks | 214 | Layer 2 업무 KG 구축 단위 |
| Evaluation chunks | 120 | LLM 조건 비교용 평가 subset |
| Layer 2 nodes | 220 | 최종 업무 KG node |
| Layer 2 edges | 947 | 최종 업무 KG edge |
| NCS mapping candidates | 110 | Layer 2 task와 NCS 후보 연결 |
| PCF mapping candidates | 110 | Layer 2 task와 PCF 후보 연결 |
| Dangling edges | 0 | source/target이 없는 edge 없음 |
| Evidence-missing edges | 0 | final edge는 모두 evidence 보유 |
| Automatic CQ answerability | 12/12 | 구조적 자동 점검 기준 |

중요한 해석은 다음입니다. 최종 Layer 2 KG는 LLM이 출력한 JSON을 그대로 저장한 결과가 아닙니다. OCR sentence evidence, task seed, 용어 사전, procedure template, schema rule, validator를 결합해서 만든 **rule/schema/evidence 기반 graph**입니다.

---

## 3. 연구 방법론 요약

방법론 이름은 CAPE-KG로 정리했습니다.

> CAPE-KG: Competency-Question Anchored Procedural Evidence Grounding for Domain Knowledge Graph Construction

핵심 구조는 다음과 같습니다.

```text
OCR sentence evidence
-> Layer 1 NCS/PCF standard KG
-> Layer 2 task seed and chunking
-> Competency Questions
-> Procedural schema
-> Task frame and procedure construction
-> Evidence-grounded node/edge construction
-> Schema/domain-range/evidence validation
-> NCS/PCF mapping candidate generation
-> LLM baseline/proposed/ablation diagnostics
-> Human-gold and expert-review handoff
```

연구 기여로 설명할 수 있는 지점은 LLM 사용 자체가 아니라, LLM과 rule-based build를 다음 제약 안에 넣었다는 점입니다.

| 구성 요소 | 역할 |
|---|---|
| CQ | KG가 답해야 하는 질문을 먼저 정의 |
| Procedural schema | task, step, input, output, role, decision, condition, risk를 구조화 |
| Evidence grounding | 모든 node/edge를 원문 sentence evidence와 연결 |
| Validator | node type, predicate, evidence id, domain/range를 검사 |
| Standard bridge | Layer 2 업무 KG를 NCS/PCF 표준과 연결 |
| Human review gate | silver/proxy 결과를 최종 성능 claim으로 과장하지 않도록 차단 |

---

## 4. CQ는 어떻게 만들었는가

CQ는 LLM이 자동 생성한 것이 아니라, 연구자가 먼저 정의한 **KG 요구사항**입니다. 즉, “이 KG가 어떤 질문에 답해야 하는가”를 정하고, 그 질문을 node type과 edge predicate로 연결했습니다.

생성 절차는 다음과 같습니다.

1. 수주·제안 업무 문서를 단순 entity extraction 문제가 아니라 절차형 업무 지식 추출 문제로 정의했습니다.
2. 업무 지식을 task, step, input, output, role, decision, guard condition, artifact flow, evidence, standard mapping 범주로 분해했습니다.
3. 각 범주를 KG가 답해야 할 question으로 바꾸었습니다.
4. 각 question을 필요한 predicate와 schema element에 연결했습니다.
5. 같은 CQ를 schema 설계, LLM prompt, validation, CQ answerability evaluation에서 재사용했습니다.

CQ 원본 파일은 다음입니다.

- `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json`
- `outputs/03_schema/competency_questions.json`

현재 CQ 12개는 다음과 같습니다.

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

발표에서는 “CQ를 prompt 앞에 붙였다”가 아니라, **CQ가 schema selection, extraction target, validation target, evaluation query를 동시에 통제했다**고 설명하는 것이 중요합니다.

---

## 5. 실제 사용한 prompt 구조

LLM 실험은 baseline, proposed, ablation 조건으로 나누어 실행했습니다. 각 조건은 공통 runtime prompt와 조건별 instruction을 결합합니다.

### 5.1 공통 runtime prompt

모든 LLM 조건에는 다음 공통 제약이 들어갑니다.

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

strict JSON 실행에서는 다음 계약이 system prompt에 추가됩니다.

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

### 5.2 조건별 prompt와 산출 key

| condition | prompt 핵심 문장 | 산출 key |
|---|---|---|
| `B0_plain_llm` | `Extract subject-predicate-object triples from the chunk. Return JSON only.` | `triples` |
| `B1_predicate_constrained` | `Extract triples using only the allowed predicates. Return JSON only with evidence sentence ids.` | `edges` |
| `B2_current_project` | `Extract Task Frames, then triples, then post-process into the Layer2 schema.` | `nodes`, `edges` |
| `B3_edc_style` | `Extract, define, and canonicalize open-schema KG items, then emit CAPE-compatible nodes and edges for scoring.` | `nodes`, `edges` |
| `B4_taxonomy_rag` | `Retrieve NCS/PCF/task taxonomy snippets, then extract schema-constrained triples with evidence.` | `nodes`, `edges`, `mappings` |
| `B5_procedural_prompt` | `Extract actions, actors, gateways, guard conditions, artifact flows, and temporal/logical dependencies.` | `nodes`, `edges` |
| `B6_sac_kg_verifier_pruner` | `Use existing generator candidates, then apply schema/evidence verification and pruning in the style of SAC-KG.` | `nodes`, `edges` |
| `P_cape_kg_actual` | `Use CQ-linked schema retrieval, procedural frame extraction, evidence-span constrained relation extraction, span verification, ontology validation, procedural consistency checks, and active review scoring.` | `nodes`, `edges`, `mappings` |
| `P_minus_CQ` | `P_cape_kg_actual`에서 CQ anchoring 제거 | `nodes`, `edges`, `mappings` |
| `P_minus_Evidence` | `P_cape_kg_actual`에서 evidence anchor 필수 조건 약화 | `nodes`, `edges`, `mappings` |
| `P_minus_Procedural_schema` | procedural schema 대신 flat schema 사용 | `nodes`, `edges`, `mappings` |
| `P_minus_Schema_retrieval` | chunk-specific schema/taxonomy retrieval 제거 | `nodes`, `edges`, `mappings` |
| `P_minus_Standard_bridge` | NCS/PCF mapping 출력 제거 | `nodes`, `edges` |
| `P_minus_Validator` | post-hoc validator rejection 제거 | `nodes`, `edges`, `mappings` |

Prompt 파일 위치는 다음입니다.

- `experiments/cape_kg_eacl_20260627/02_schema/prompts/`
- Runtime prompt builder: `scripts/run_cape_llm_condition_baselines.py`
- Prompt-node-edge 추적 문서: `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md`

### 5.3 `P_cape_kg_actual`의 실제 제약

`P_cape_kg_actual`은 다음 제약을 동시에 넣습니다.

| 제약 | 의미 |
|---|---|
| Competency questions | CQ1-CQ12를 prompt에 넣어 추출 목표를 고정 |
| Taxonomy snippets | NCS/PCF/task taxonomy retrieval context 제공 |
| Allowed node types | `DomainTask`, `ProcedureStep`, `DecisionGateway`, `GuardCondition`, `Artifact`, `ArtifactFlow`, `Role`, `ReviewCheckpoint`, `Principle`, `Risk` |
| Allowed edge predicates | `HAS_STEP`, `PRECEDES`, `BRANCHES_TO`, `HAS_GUARD_CONDITION`, `USES_INPUT`, `PRODUCES`, `FEEDS_INTO`, `PERFORMED_BY`, `HAS_DECISION_GATEWAY`, `HAS_REVIEW_CHECKPOINT`, `HAS_PRINCIPLE`, `HAS_RISK`, `USED_AS_INPUT_FOR` |
| Evidence rule | 모든 node, edge, mapping은 현재 chunk의 `sentence_ids` 중 최소 1개를 가져야 함 |
| Output shape | `nodes`, `edges`, `mappings` |
| Hard limit | chunk당 최대 5 nodes, 5 edges, 3 mappings |
| Language rule | 원문이 한국어이면 label도 한국어 유지 |
| Outside knowledge ban | chunk 밖 지식 사용 금지 |

---

## 6. LLM 실행 결과는 무엇을 의미하는가

LLM 실험은 최종 KG 자체를 만드는 유일한 단계라기보다, CAPE-KG 조건이 baseline 및 ablation과 비교해 어떤 구조적 품질을 보이는지 진단하기 위한 조건 비교입니다.

| condition | valid rows | triples | nodes | edges | mappings |
|---|---:|---:|---:|---:|---:|
| `B0_plain_llm` | 120 | 1,037 | 0 | 0 | 0 |
| `B1_predicate_constrained` | 120 | 0 | 0 | 805 | 0 |
| `B2_current_project` | 120 | 0 | 867 | 334 | 0 |
| `B3_edc_style` | 120 | 0 | 769 | 263 | 0 |
| `B4_taxonomy_rag` | 120 | 0 | 719 | 323 | 126 |
| `B5_procedural_prompt` | 120 | 0 | 1,307 | 302 | 0 |
| `B6_sac_kg_verifier_pruner` | 120 | 0 | 2,281 | 361 | 107 |
| `P_cape_kg_actual` | 120 | 0 | 576 | 373 | 227 |
| `P_minus_CQ` | 120 | 0 | 586 | 391 | 233 |
| `P_minus_Evidence` | 120 | 0 | 574 | 383 | 227 |
| `P_minus_Procedural_schema` | 120 | 0 | 558 | 353 | 212 |
| `P_minus_Schema_retrieval` | 120 | 0 | 568 | 417 | 216 |
| `P_minus_Standard_bridge` | 120 | 0 | 577 | 405 | 0 |
| `P_minus_Validator` | 120 | 0 | 570 | 375 | 229 |

주의할 점은 이 표가 성능 우수성 표가 아니라는 것입니다. 현재 값은 **valid JSON output quantity**입니다. Precision, recall, F1 같은 논문 main table은 adjudicated human-gold가 들어온 뒤 다시 계산해야 합니다.

---

## 7. Node는 어떻게 산출했는가

최종 node 파일은 `outputs/07_layer2_graph/layer2_nodes.jsonl`입니다.

Node 생성 원칙은 다음입니다.

1. OCR sentence를 evidence anchor로 만들었습니다.
2. 수주·제안 업무의 task seed를 정의했습니다.
3. task seed의 label, alias, keyword를 OCR evidence와 매칭해 `DomainTask`를 만들었습니다.
4. task별 procedure template과 입력/산출물 구조를 이용해 `ProcedureStep`을 만들었습니다.
5. 입력물, 산출물, 역할, 의사결정, 조건, 원칙, 위험 표현을 schema type별로 정규화했습니다.
6. 각 node에는 evidence anchor를 붙였습니다.

현재 최종 node 분포는 다음입니다.

| node type | count | 생성 방식 |
|---|---:|---|
| `ProcedureStep` | 99 | task별 procedure template 또는 입력/산출물 기반 step 추론 |
| `DomainTask` | 22 | TASK_SEEDS의 label, alias, keyword를 OCR sentence evidence와 매칭 |
| `Artifact` | 14 | task evidence 안의 입력물/산출물 용어 추출 |
| `GuardCondition` | 13 | 의사결정 evidence에서 조건, 가능성, 경쟁, 자원 표현 추출 |
| `Role` | 10 | 수행자/책임 주체 용어 매칭 |
| `ArtifactFlow` | 9 | 특정 산출물이 다음 task 입력으로 쓰이는 규칙에서 생성 |
| `Principle` | 5 | 원칙/품질 기준 용어 매칭 |
| `DecisionGateway` | 4 | 의사결정 관련 용어 매칭 |
| `Risk` | 3 | 위험, 불리함, 실패 가능성 표현 매칭 |

검증 결과:

- final nodes: 220
- nodes with evidence: 220/220

---

## 8. Edge는 어떻게 산출했는가

최종 edge 파일은 `outputs/07_layer2_graph/layer2_edges.jsonl`입니다.

Edge 생성 원칙은 다음입니다.

1. `DomainTask -> ProcedureStep`은 `HAS_STEP`으로 연결했습니다.
2. 같은 task 내부 step 순서는 `PRECEDES`로 연결했습니다.
3. task/step의 input slot은 `USES_INPUT`으로 연결했습니다.
4. task/step의 output slot은 `PRODUCES`로 연결했습니다.
5. role slot은 `PERFORMED_BY`로 연결했습니다.
6. decision, guard condition, principle, risk는 각각 schema predicate로 연결했습니다.
7. 산출물이 다음 task 입력으로 쓰이는 경우 `FEEDS_INTO`, `USED_AS_INPUT_FOR`로 연결했습니다.
8. 모든 edge에 evidence와 `source_triple_ids`를 붙였습니다.
9. source/target node가 없는 dangling edge는 제거했습니다.

현재 최종 edge 분포는 다음입니다.

| predicate | count | 생성 방식 |
|---|---:|---|
| `PRODUCES` | 220 | task/step의 outputs slot을 Artifact node로 연결 |
| `USES_INPUT` | 201 | task/step의 inputs slot을 Artifact 또는 Concept node로 연결 |
| `PERFORMED_BY` | 120 | task/step의 roles slot을 Role node로 연결 |
| `HAS_STEP` | 99 | DomainTask를 해당 ProcedureStep 목록에 연결 |
| `PRECEDES` | 77 | 같은 task 안에서 step order 기준으로 순서 연결 |
| `HAS_PRINCIPLE` | 64 | task/step의 principles slot을 Principle node로 연결 |
| `HAS_DECISION_GATEWAY` | 54 | task/step에서 발견된 의사결정 node를 연결 |
| `HAS_RISK` | 39 | task/step의 risks slot을 Risk node로 연결 |
| `HAS_GUARD_CONDITION` | 14 | DecisionGateway에서 추출된 조건 node를 연결 |
| `FEEDS_INTO` | 9 | Artifact가 다음 task로 흘러가는 규칙을 연결 |
| `USED_AS_INPUT_FOR` | 9 | Artifact가 다음 task 입력으로 사용되는 규칙을 연결 |

검증 결과:

- final edges: 947
- edges with evidence: 947/947
- edges with `source_triple_ids`: 947/947
- dangling edges: 0
- type violations: 0

---

## 9. 지금까지 실행한 실험

| 실험/산출물 | 상태 | 해석 |
|---|---|---|
| OCR sentence evidence | 완료 | 5,009 sentence anchor 생성 |
| Layer 1 NCS KG | 완료 | 4,109 nodes |
| Layer 1 PCF KG | 완료 | 5,301 nodes |
| Layer 2 procedural KG | 완료 | 220 nodes, 947 edges |
| CQ answerability report | 완료 | 12/12 structural CQs answerable |
| NCS mapping candidates | 완료 | 110 candidates |
| PCF mapping candidates | 완료 | 110 candidates |
| Neo4j CSV export | 완료 | flat import 포함 |
| RDF/SHACL export | 완료 | SHACL-style validation PASS |
| LLM B0/B1/B2 baselines | 완료 | 120 chunks |
| LLM B3/B4/B5/B6 baselines | 완료 | EDC/Taxonomy-RAG/Procedural/SAC-KG-style |
| `P_cape_kg_actual` | 완료 | 120 chunks |
| Ablation 6개 | 완료 | CQ, evidence, procedural schema, schema retrieval, bridge, validator 제거 비교 |
| Public benchmark adapter | 완료 | PAGED/Text2KG subset 진단 |
| Release bundle | 완료 | internal/public-safe bundle 생성 |
| Human review handoff | 완료 | annotation, adjudication, mapping, active-review 패키지 준비 |
| Claim gate | FAIL | expected fail, human-gold 미완료 때문 |

---

## 10. 현재 남은 일

현재 pre-human validation은 PASS입니다. 그러나 논문 제출 수준의 성능 claim은 아직 막혀 있습니다.

| 항목 | 현재 상태 |
|---|---:|
| Pre-human validation | PASS |
| Pre-human checks | 92 |
| Minimum paper-gate return files | 0/11 |
| Optional/strong claim return files | 0/3 |
| Required claim/human return files | 0/14 |
| Optional structural review files | 0/2 |
| All master return files | 0/16 |
| Adjudicated chunks | 0 |
| Gold item count | 0 |
| Mapping pending rows | 220 |
| Claim gate | FAIL |

남은 핵심 작업은 다음입니다.

1. annotator A/B가 최소 100 chunk를 검수합니다.
2. IAA를 계산합니다.
3. adjudication을 통해 human-gold를 확정합니다.
4. `P_cape_kg_actual` 및 baseline/ablation을 human-gold 기준으로 scoring합니다.
5. NCS/PCF mapping 후보 220개에 대해 expert review를 수행합니다.
6. 그 뒤에 precision, recall, F1, mapping P@K/MRR/nDCG 같은 final main table을 확정합니다.

---

## 11. 교수님께 보고할 때의 핵심 표현

보고 시 다음과 같이 말하는 것이 가장 정확합니다.

> 본 연구는 한국어 수주·제안 업무 문서에서 task, step, input/output, role, decision, condition, risk를 evidence-grounded procedural KG로 구축하는 방법론입니다. 현재 Layer 1 NCS/PCF 표준 KG와 Layer 2 업무 KG 구축은 완료되었고, LLM baseline, proposed condition, ablation, public benchmark adapter, release/handoff까지 실행했습니다. 다만 현재 수치는 silver/proxy diagnostic이므로, 최종 논문 성능표는 human-gold annotation, IAA, adjudication, mapping expert review, NCS-PCF crosswalk expert review, active-review effort evidence 이후에 확정해야 합니다.

---

## 12. 관련 핵심 파일

| 역할 | 파일 |
|---|---|
| 전체 슬라이드 원고 | `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md` |
| Prompt/node/edge traceability | `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md` |
| CQ 원본 | `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json` |
| Prompt 파일 | `experiments/cape_kg_eacl_20260627/02_schema/prompts/` |
| Runtime prompt builder | `scripts/run_cape_llm_condition_baselines.py` |
| Final Layer 2 nodes | `outputs/07_layer2_graph/layer2_nodes.jsonl` |
| Final Layer 2 edges | `outputs/07_layer2_graph/layer2_edges.jsonl` |
| Final build report | `outputs/10_evaluation/final_build_report.md` |
| Claim gate report | `experiments/cape_kg_eacl_20260627/06_release/claim_gate_report.md` |
| Human review handoff report | `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/human_review_handoff_report.md` |
