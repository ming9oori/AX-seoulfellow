# 교수님 보고용 핵심 브리핑: 프롬프트, CQ, Node/Edge 산출 방식

Generated: 2026-06-29  
Related detailed slide draft: `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md`  
Experiment directory: `experiments/cape_kg_eacl_20260627`  
KG output directory: `outputs`

이 문서는 기존 슬라이드 원고와 별개로, 교수님께 핵심만 보고하기 위한 요약본입니다. 특히 다음 질문에 바로 답할 수 있도록 정리했습니다.

1. 어떤 프롬프트로 어떤 산출물을 만들었는가?
2. CQ는 어떻게 만들었고 어떤 예시가 있는가?
3. 최종 KG의 node와 edge는 각각 어떤 방식으로 산출되었는가?
4. 현재까지 어떤 실험이 완료되었고, 무엇이 아직 claim 불가능한가?

---

## 1. 한 장 요약

현재 연구는 한국어 수주/제안 업무 문서에서 근거 기반 procedural KG를 구축하는 CAPE-KG 방법론을 적용한 상태입니다.

핵심 결론:

- Layer 1 표준 KG 구축 완료: NCS 4,109 nodes, PCF 5,301 nodes
- Layer 2 업무 KG 구축 완료: 179 nodes, 906 edges
- accepted Layer 2 edge evidence 누락: 0건
- NCS mapping 후보: 110건
- PCF mapping 후보: 110건
- LLM baseline/proposed/ablation/model-scaling 실행 완료
- Public benchmark adapter 실행 완료
- Human review handoff 준비 완료
- 단, final performance main table은 아직 아님

가장 중요한 해석:

> 현재 결과는 "KG 구축과 실험 인프라가 완료된 pre-human evaluation 상태"입니다. 논문에서 최종 성능 우수성을 주장하려면 human-gold annotation, IAA, adjudication, mapping expert review, NCS-PCF crosswalk expert review, active-review effort evidence가 필요합니다.

---

## 2. 최종 KG와 LLM 실험의 관계

교수님께 설명할 때 가장 주의해야 할 부분은 최종 KG와 LLM prediction을 분리하는 것입니다.

| 구분 | 위치 | 의미 |
| --- | --- | --- |
| 최종 KG 구축 산출물 | `outputs/07_layer2_graph/` | 실제 데이터에 대해 구축된 Layer 2 업무 KG |
| LLM 실험 산출물 | `experiments/cape_kg_eacl_20260627/49_*`, `50_*` | baseline/proposed/ablation 조건별 후보 생성 결과 |
| 평가/claim 산출물 | `experiments/cape_kg_eacl_20260627/04_evaluation/`, `06_release/` | silver diagnostic, structural diagnostic, claim gate, release report |

핵심 표현:

> 최종 KG는 LLM raw output을 그대로 저장한 것이 아니라, OCR evidence anchor, task seed, 용어 사전, 절차 템플릿, schema validator를 사용해 rule/schema/evidence 기반으로 조립한 graph입니다. LLM은 같은 task에서 baseline, proposed, ablation 조건별 후보 생성 능력을 비교하기 위해 별도로 실행했습니다.

---

## 3. CQ는 어떻게 생성했는가

CQ, 즉 Competency Question은 LLM이 자동 생성한 것이 아니라 연구자가 정의한 KG 요구사항입니다.

생성 절차:

1. 연구 문제를 먼저 정함
   - 한국어 수주/제안 업무 문서에서 procedural KG를 구축한다.
   - 단순 entity extraction이 아니라 task, step, input/output, role, decision, guard condition, risk, evidence, standard mapping을 표현한다.
2. KG가 답해야 할 질문 범주를 정함
   - 업무 구성과 순서
   - 입력 자료와 산출물
   - 수행 역할
   - 의사결정과 조건
   - 산출물 흐름
   - 원문 evidence
   - NCS/PCF 표준 연결
3. 각 질문을 schema predicate와 연결함
   - 예: "각 Task는 어떤 산출물을 생성하는가?" -> `PRODUCES`
   - 예: "각 Task는 누가 수행하는가?" -> `PERFORMED_BY`
   - 예: "의사결정 조건은 무엇인가?" -> `HAS_GUARD_CONDITION`
4. 이 CQ를 schema, prompt, validation, CQ answerability evaluation에 재사용함

관련 파일:

| 역할 | 파일 |
| --- | --- |
| EACL 실험용 CQ | `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json` |
| 내부 KG build용 CQ | `outputs/03_schema/competency_questions.json` |
| CQ/schema 생성 코드 | `scripts/build_cape_kg_eacl_experiment.py`, `scripts/build_ax_epak_internal_kg.py` |
| Runtime prompt 조립 코드 | `scripts/run_cape_llm_condition_baselines.py` |

---

## 4. 실제 CQ 목록

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

발표 포인트:

> CQ는 "무엇을 추출할 것인가"와 "나중에 KG가 무엇을 답해야 하는가"를 동시에 정의합니다. 따라서 CQ가 schema, prompt, validation, evaluation을 묶는 anchor 역할을 합니다.

---

## 5. 실제 저장된 프롬프트 원문

프롬프트 파일 위치:

`experiments/cape_kg_eacl_20260627/02_schema/prompts/`

아래는 파일에 실제 저장된 원문입니다. 실제 LLM 호출 때는 여기에 chunk sentence, sentence id, allowed schema, JSON shape, strict JSON contract가 자동으로 결합됩니다.

| 조건 | 실제 프롬프트 원문 | 요구 산출물 |
| --- | --- | --- |
| B0_plain_llm | `Extract subject-predicate-object triples from the chunk. Return JSON only.` | `triples` |
| B1_predicate_constrained | `Extract triples using only the allowed predicates. Return JSON only with evidence sentence ids.` | `edges` |
| B2_current_project | `Extract Task Frames, then triples, then post-process into the Layer2 schema.` | `nodes`, `edges` |
| B3_edc_style | `Extract, define, and canonicalize open-schema KG items, then emit CAPE-compatible nodes and edges for scoring.` | `nodes`, `edges` |
| B4_taxonomy_rag | `Retrieve NCS/PCF/task taxonomy snippets, then extract schema-constrained triples with evidence.` | `nodes`, `edges`, `mappings` |
| B5_procedural_prompt | `Extract actions, actors, gateways, guard conditions, artifact flows, and temporal/logical dependencies.` | `nodes`, `edges` |
| B6_sac_kg_verifier_pruner | `Use existing generator candidates, then apply schema/evidence verification and pruning in the style of SAC-KG. This is a deterministic approximation, not a full SAC-KG reproduction.` | `nodes`, `edges` |
| P_cape_kg_actual | `Use CQ-linked schema retrieval, procedural frame extraction, evidence-span constrained relation extraction, span verification, ontology validation, procedural consistency checks, and active review scoring.` | `nodes`, `edges`, `mappings` |
| P_minus_Schema_retrieval | `Run CAPE-KG without chunk-specific schema/taxonomy retrieval; keep CQ, evidence grounding, procedural schema, validation, and mapping output shape.` | `nodes`, `edges`, `mappings` |
| strict_json_contract | JSON object만 반환, markdown/code fence/comment/XML/`<think>`/설명 금지, `/no_think`, compact JSON, 빈 배열 사용 | 출력 형식 안정화 |

---

## 6. 실제 Runtime Prompt의 공통 구조

모든 조건에는 다음 공통 제약이 붙었습니다.

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

Strict JSON 실행에서는 system/user prompt에 다음 제약이 추가되었습니다.

```text
System:
You are a JSON-only evidence-grounded information extraction function.
Strict JSON contract:
- Return exactly one JSON object and nothing else.
- Do not include markdown, code fences, comments, XML tags, <think> blocks, prose, or explanations.
- For Qwen/Qwen-style chat models, obey /no_think; do not emit hidden or visible reasoning.

User prefix/suffix:
/no_think
...
/no_think
Return exactly one compact JSON object now.
```

---

## 7. P_cape_kg_actual의 실제 Runtime Prompt 핵심

제안 방법론 조건인 `P_cape_kg_actual`에는 CQ, taxonomy snippet, evidence requirement, validator rule, allowed schema, JSON shape가 모두 포함되었습니다.

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
- Prefer concise, reusable labels.
- Hard limit: return at most 5 nodes, at most 5 edges, and at most 3 mappings.
- If the chunk does not support a field, return an empty array for that field.
```

출력 JSON shape:

```json
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
```

---

## 8. 조건별 LLM 산출물 수량

아래 표는 Qwen3-8B strict JSON full run 및 SAC-KG-style baseline의 validated output 수량입니다. 이것은 성능표가 아니라 "어떤 조건이 어떤 형식의 산출물을 얼마나 생성했는지"를 보여주는 진단표입니다.

| 조건 | Valid rows | Triples | Nodes | Edges | Mappings |
| --- | ---: | ---: | ---: | ---: | ---: |
| B0_plain_llm | 120 | 1,037 | 0 | 0 | 0 |
| B1_predicate_constrained | 120 | 0 | 0 | 805 | 0 |
| B2_current_project | 120 | 0 | 867 | 334 | 0 |
| B3_edc_style | 120 | 0 | 769 | 263 | 0 |
| B4_taxonomy_rag | 120 | 0 | 719 | 323 | 126 |
| B5_procedural_prompt | 120 | 0 | 1,307 | 302 | 0 |
| B6_sac_kg_verifier_pruner | 120 | 0 | 2,281 | 361 | 107 |
| P_cape_kg_actual | 120 | 0 | 576 | 373 | 227 |
| P_minus_CQ | 120 | 0 | 586 | 391 | 233 |
| P_minus_Evidence | 120 | 0 | 574 | 383 | 227 |
| P_minus_Procedural_schema | 120 | 0 | 558 | 353 | 212 |
| P_minus_Schema_retrieval | 120 | 0 | 568 | 417 | 216 |
| P_minus_Standard_bridge | 120 | 0 | 577 | 405 | 0 |
| P_minus_Validator | 120 | 0 | 570 | 375 | 229 |

해석:

- B0는 자유 SPO triple만 생성합니다.
- B1은 predicate-constrained edge만 생성합니다.
- B2 이후는 CAPE-compatible node/edge를 생성합니다.
- B4와 P 계열은 NCS/PCF mapping 후보까지 생성합니다.
- P_minus_Standard_bridge는 bridge를 제거했기 때문에 mapping이 0입니다.

---

## 9. 최종 KG Node는 어떻게 산출했는가

최종 node 파일:

`outputs/07_layer2_graph/layer2_nodes.jsonl`

핵심 원칙:

- LLM 출력물을 그대로 node로 넣지 않음
- OCR sentence를 `EA-JS-*` evidence anchor로 유지
- task seed, alias, keyword, 용어 사전, 절차 템플릿을 사용
- 모든 final node에 evidence anchor를 연결
- `node_id` 기준으로 중복 제거

Node 생성 흐름:

1. OCR sentence를 evidence anchor로 변환
2. `TASK_SEEDS`의 label, alias, keyword로 관련 sentence 검색
3. 관련 sentence에서 Artifact, Role, DecisionGateway, Principle, Risk 후보를 용어 사전으로 탐지
4. 업무 seed를 `DomainTask` node로 생성
5. task별 절차 템플릿 또는 입력/산출물 기반 추론으로 `ProcedureStep` node 생성
6. 산출물이 다음 업무로 흘러가는 규칙으로 `ArtifactFlow` node 생성
7. evidence와 review status를 부여하고 최종 node로 저장

최종 node type별 생성 방식:

| Node type | 현재 개수 | 생성 방식 |
| --- | ---: | --- |
| ProcedureStep | 99 | task별 procedure template 또는 입력/산출물 기반 step 추론 |
| DomainTask | 22 | `TASK_SEEDS`의 label/alias/keyword로 OCR evidence 검색 |
| Artifact | 14 | task evidence 안의 입력물/산출물 용어 매칭 |
| GuardCondition | 13 | 의사결정 evidence에서 조건/가능성/경쟁/자원 표현 추출 |
| Role | 10 | 수행자/책임 주체 용어 매칭 |
| ArtifactFlow | 9 | 특정 산출물이 다음 task 입력으로 쓰이는 규칙 |
| Principle | 5 | 원칙/품질 기준 용어 매칭 |
| DecisionGateway | 4 | 의사결정 관련 용어 매칭 |
| Risk | 3 | 위험/불리함/실패 가능성 용어 매칭 |

Node 검증 결과:

- Final nodes: 179
- Nodes with evidence: 179 / 179

---

## 10. 최종 KG Edge는 어떻게 산출했는가

최종 edge 파일:

`outputs/07_layer2_graph/layer2_edges.jsonl`

핵심 원칙:

- edge는 source node와 target node가 모두 존재해야 함
- predicate는 allowed schema predicate여야 함
- evidence anchor가 있어야 함
- schema-valid triple에서 source_triple_ids를 추적함

Edge 생성 흐름:

1. task frame의 `inputs`, `outputs`, `roles`, `principles`, `risks` slot을 predicate로 변환
2. decision gateway와 guard condition을 별도 predicate로 연결
3. procedure step은 `HAS_STEP`, step 순서는 `PRECEDES`로 연결
4. artifact flow 규칙은 `FEEDS_INTO`, `USED_AS_INPUT_FOR`로 연결
5. edge를 schema-valid triple record로 변환
6. allowed predicate, source/target node 존재, evidence 존재 조건을 통과한 edge만 최종 저장

Predicate별 생성 방식:

| Predicate | 현재 개수 | 생성 방식 |
| --- | ---: | --- |
| PRODUCES | 220 | task/step의 outputs slot을 Artifact node로 연결 |
| USES_INPUT | 201 | task/step의 inputs slot을 Artifact node로 연결 |
| PERFORMED_BY | 120 | task/step의 roles slot을 Role node로 연결 |
| HAS_STEP | 99 | DomainTask를 해당 ProcedureStep 목록에 연결 |
| PRECEDES | 77 | 같은 task 안에서 step order 기준으로 순서 연결 |
| HAS_PRINCIPLE | 64 | task/step의 principles slot을 Principle node로 연결 |
| HAS_DECISION_GATEWAY | 54 | task/step에서 발견된 의사결정 node를 연결 |
| HAS_RISK | 39 | task/step의 risks slot을 Risk node로 연결 |
| HAS_GUARD_CONDITION | 14 | DecisionGateway에서 추출된 조건 node를 연결 |
| FEEDS_INTO | 9 | Artifact가 다음 task로 흘러가는 규칙 연결 |
| USED_AS_INPUT_FOR | 9 | Artifact가 다음 task 입력으로 사용되는 규칙 연결 |

Edge 검증 결과:

- Final edges: 906
- Edges with evidence: 906 / 906
- Edges with `source_triple_ids`: 906 / 906
- Dangling edges: 0
- Type violations: 0

---

## 11. 중간 산출물 연결

| 단계 | 파일 | 현재 수량 |
| --- | --- | ---: |
| Task frame | `outputs/04_task_frames/canonical_task_catalog.json` | 22 canonical tasks |
| Procedure structure | `outputs/05_procedure/procedure_structures_clean.jsonl` | 22 procedures / 99 steps |
| Schema-valid triple | `outputs/06_triples/layer2_triples_schema_valid.jsonl` | 906 |
| Final nodes | `outputs/07_layer2_graph/layer2_nodes.jsonl` | 179 |
| Final edges | `outputs/07_layer2_graph/layer2_edges.jsonl` | 906 |
| NCS mapping candidates | `outputs/08_mapping/l2_ncs_mapping_candidates.jsonl` | 110 |
| PCF mapping candidates | `outputs/08_mapping/l2_pcf_mapping_candidates.jsonl` | 110 |

설명:

> triple은 최종 graph edge를 평가하고 evidence를 추적하기 위한 중간 표현입니다. 현재 schema-valid triple 906개가 최종 edge 906개로 연결됩니다.

---

## 12. 현재까지 실행한 주요 실험

| 실험/작업 | 상태 | 핵심 산출물 |
| --- | --- | --- |
| Layer 1 NCS/PCF KG build | 완료 | `outputs/01_layer1/` |
| OCR evidence anchor build | 완료 | `outputs/02_ocr/`, `outputs/06_triples/` |
| Layer 2 procedural KG build | 완료 | `outputs/07_layer2_graph/` |
| NCS/PCF mapping candidate build | 완료 | `outputs/08_mapping/` |
| KG visualization/Neo4j export | 완료 | `outputs/09_visualization/`, `outputs/11_neo4j_import_flat/` |
| Qwen3-8B baseline/proposed/ablation | 완료 | `49_*` valid/raw outputs |
| Qwen3-14B core run | 완료 | `qwen3_14b_core_*` evaluation files |
| Qwen3-32B-AWQ core run | 완료 | `qwen3_32b_awq_core_*` evaluation files |
| Public benchmark adapter | 완료 | `08_public_benchmarks/` |
| Structural diagnostics | 완료 | `04_evaluation/structural_*` |
| Human-review handoff | 완료 | `06_release/human_review_handoff/` |
| Claim gate/release bundle | 완료 | `06_release/claim_gate_report.*`, checksums |

---

## 13. 현재 결과를 어떻게 해석해야 하는가

Claimability 기준:

| 결과 | 현재 해석 |
| --- | --- |
| KG 구축 결과 | 구축 완료라고 말할 수 있음 |
| Evidence grounding | accepted edge evidence 누락 0건이라고 말할 수 있음 |
| LLM 조건별 output | 실행 완료 및 diagnostic이라고 말할 수 있음 |
| Silver F1 결과 | 최종 성능이 아니라 silver/proxy diagnostic |
| Model scaling 결과 | Qwen3-8B/14B/32B-AWQ 실행 완료, 최종 claim은 보류 |
| NCS/PCF mapping | 후보 생성 완료, expert review 전 |
| Active review | queue/template 준비 완료, human timing/correction 전 |
| Final main table | 아직 아님, human-gold 이후 생성 |

현재 claim gate의 주요 미완료 항목:

- human-gold completed chunks: 0
- human-gold item count: 0
- IAA: 미계산
- proposed result human-gold scoring: 미완료
- mapping expert review: downstream mapping claim을 위해 필요
- NCS-PCF crosswalk expert review: bridge utility/accept-rate claim을 위해 필요
- active-review human-effort evidence: 검수 효율 claim을 위해 필요

---

## 14. 교수님께 보고할 때 사용할 핵심 문장

가장 안전한 보고 문장:

> 현재까지는 한국어 수주/제안 업무 문서에 대해 Layer 1 표준 KG, Layer 2 procedural 업무 KG, evidence grounding, NCS/PCF mapping 후보, NCS-PCF crosswalk 후보, LLM baseline/proposed/ablation/model-scaling, public benchmark adapter, structural diagnostics, human-review handoff까지 구축 및 실행했습니다. 다만 논문에서 최종 성능 우수성을 주장하려면 human-gold annotation, IAA, adjudication, mapping expert review, NCS-PCF crosswalk expert review, active-review effort evidence가 아직 필요합니다.

프롬프트와 CQ 설명 문장:

> CAPE-KG의 핵심은 LLM에게 단순히 triple을 생성시키는 것이 아니라, CQ로 추출 목표를 정하고, procedural schema로 node/edge type을 제한하고, evidence anchor와 validator를 통해 출력물을 검증 가능한 KG 후보로 만드는 것입니다.

Node/edge 설명 문장:

> 최종 node는 task seed, evidence sentence, 용어 사전, 절차 템플릿을 통해 생성했고, 최종 edge는 input/output/role/principle/risk/decision/step/flow slot을 allowed predicate로 변환한 뒤 source node, target node, evidence가 모두 있는 경우에만 graph에 저장했습니다.

현재 main table 설명 문장:

> 현재 table은 final performance table이 아니라 claimability table입니다. 사람이 검수한 gold label이 들어오면 같은 prediction과 evaluation pipeline을 사용해 최종 precision/recall/F1 main table로 전환할 수 있습니다.

---

## 15. 발표에서 피해야 할 표현

| 피해야 할 표현 | 안전한 표현 |
| --- | --- |
| LLM이 최종 KG를 만들었다 | 최종 KG는 rule/schema/evidence 기반으로 구축했고, LLM은 조건별 prediction generator로 사용했다 |
| 제안 방법론이 baseline보다 우수하다 | 현재는 silver/proxy diagnostic이며 human-gold 이후 최종 비교가 가능하다 |
| mapping이 검증되었다 | mapping 후보가 생성되었고 expert review가 필요하다 |
| active review가 효율적이다 | active-review queue와 template이 준비되었고 human effort 데이터가 필요하다 |
| main table이 완성되었다 | claimability table은 있으며 final performance table은 pending이다 |

---

## 16. 핵심 파일 경로

| 목적 | 경로 |
| --- | --- |
| 상세 슬라이드 원고 | `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md` |
| 프롬프트/CQ/node/edge traceability | `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md` |
| CQ JSON | `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json` |
| 프롬프트 파일 | `experiments/cape_kg_eacl_20260627/02_schema/prompts/` |
| Runtime prompt 코드 | `scripts/run_cape_llm_condition_baselines.py` |
| Final Layer 2 nodes | `outputs/07_layer2_graph/layer2_nodes.jsonl` |
| Final Layer 2 edges | `outputs/07_layer2_graph/layer2_edges.jsonl` |
| Schema-valid triples | `outputs/06_triples/layer2_triples_schema_valid.jsonl` |
| Claimable main table | `experiments/cape_kg_eacl_20260627/06_release/claimable_main_table.md` |
| Claim gate report | `experiments/cape_kg_eacl_20260627/06_release/claim_gate_report.md` |

---

## 17. 최종 한 문장

> 본 연구는 한국어 수주/제안 업무 문서에서 evidence-grounded procedural KG를 구축하기 위해 CQ, procedural schema, evidence anchor, validator, NCS/PCF standard bridge를 결합한 CAPE-KG 방법론을 적용했고, 현재 KG 구축과 LLM 조건 실험은 완료되었으며, 최종 논문 성능 claim은 human-gold 평가 이후 확정할 단계입니다.
