# 교수님 보고용 핵심 요약: 프롬프트, CQ, Node/Edge 산출 방식

Generated: 2026-06-29  
Experiment directory: `experiments/cape_kg_eacl_20260627`  
KG output directory: `outputs`

이 문서는 `professor_report_slide_contents_current_20260628_ko.md`와 별개로, 교수님께 가장 먼저 설명해야 할 핵심 내용만 압축한 요약본입니다. 초점은 다음 네 가지입니다.

1. 어떤 방법론으로 연구를 진행했는가
2. 어떤 프롬프트와 CQ를 사용했는가
3. node와 edge가 각각 어떤 방식으로 산출되었는가
4. 현재까지 무엇이 완료되었고, 무엇은 아직 claim하면 안 되는가

---

## 1. 한 문장 요약

본 연구는 한국어 수주/제안 업무 문서에서 `task`, `step`, `role`, `input/output artifact`, `decision`, `risk`를 원문 sentence evidence에 연결한 절차형 KG로 구축하고, 이를 NCS/PCF 표준 taxonomy와 연결하는 CAPE-KG 방법론을 적용한 실험입니다.

중요한 구분은 다음입니다.

| 구분 | 현재 상태 | 해석 |
| --- | --- | --- |
| KG 구축 | 완료 | Layer 1 표준 KG와 Layer 2 업무 KG가 생성됨 |
| LLM baseline/ablation/model scaling | 실행 완료 | Qwen3 계열로 120 evaluation chunks 기준 실행됨 |
| 성능 claim | 아직 불가 | human-gold annotation, IAA, adjudication, expert review 전이므로 최종 F1 claim 불가 |

---

## 2. 현재까지 완료된 핵심 산출물

| 항목 | 결과 |
| --- | ---: |
| OCR clean sentences / evidence anchors | 5,009 |
| Layer 2 chunks | 214 |
| Evaluation chunks | 120 |
| Layer 1 NCS nodes | 4,109 |
| Layer 1 PCF nodes | 5,301 |
| Layer 2 KG nodes | 179 |
| Layer 2 KG edges | 906 |
| Clean triples | 906 |
| Canonical DomainTask | 22 |
| NCS mapping candidates | 110 |
| PCF mapping candidates | 110 |
| NCS-PCF crosswalk candidates | 220 |
| Evidence-missing Layer 2 edges | 0 |
| Dangling edges | 0 |
| Type violations | 0 |

핵심 파일:

| 산출물 | 경로 |
| --- | --- |
| Layer 2 nodes | `outputs/07_layer2_graph/layer2_nodes.jsonl` |
| Layer 2 edges | `outputs/07_layer2_graph/layer2_edges.jsonl` |
| NCS mapping candidates | `outputs/08_mapping/l2_ncs_mapping_candidates.jsonl` |
| PCF mapping candidates | `outputs/08_mapping/l2_pcf_mapping_candidates.jsonl` |
| KG viewer | `outputs/09_visualization/kg_viewer.html` |
| Final build report | `outputs/10_evaluation/final_build_report.md` |
| Claimable table | `experiments/cape_kg_eacl_20260627/06_release/claimable_main_table.md` |
| Paper tables | `experiments/cape_kg_eacl_20260627/06_release/paper_tables.md` |

---

## 3. 방법론 전체 흐름

실험은 단순히 LLM에게 "KG를 만들어 달라"고 요청한 것이 아닙니다. 실제 파이프라인은 다음처럼 구성되었습니다.

1. OCR workbook을 sentence 단위로 정제
2. 각 sentence에 evidence anchor ID 부여
3. NCS와 PCF taxonomy를 Layer 1 표준 KG로 구축
4. 업무 문서를 Layer 2 chunk로 분할
5. Competency Question(CQ)와 procedural schema 정의
6. task seed, alias, keyword, evidence sentence를 이용해 task frame 생성
7. task frame에서 procedure step, artifact, role, decision, guard, risk 후보 생성
8. predicate별 규칙으로 triple과 edge 생성
9. source node, target node, predicate, evidence 조건을 통과한 edge만 최종 graph에 저장
10. Layer 2 업무 KG를 NCS/PCF 후보와 연결
11. 동일 chunk에 대해 LLM baseline/proposed/ablation/model scaling 조건을 실행
12. structural diagnostics, claim gate, human-review handoff 생성

따라서 최종 KG는 `LLM output 그대로`가 아니라, schema, evidence, rule/template, validator를 거친 구축 산출물입니다. LLM 실험은 별도로 "조건별 후보 생성 성능"을 비교하기 위한 prediction experiment입니다.

---

## 4. CQ는 어떻게 만들었는가

CQ는 LLM이 자동으로 만든 질문이 아니라, 이 KG가 답해야 하는 업무 질문을 먼저 정의한 설계 산출물입니다.

생성 방식:

1. 연구 문제를 "한국어 수주/제안 업무 문서에서 절차형 KG를 구축하는 문제"로 정의
2. 업무 KG가 답해야 할 질문 범주를 정함
   - 업무 구성과 순서
   - 입력 자료와 산출물
   - 수행 역할
   - 의사결정 지점과 조건
   - 산출물 흐름
   - 원문 evidence grounding
   - NCS/PCF 표준 연결
3. 각 질문을 node type과 edge predicate에 연결
4. 같은 CQ 목록을 schema, LLM prompt, ablation, structural evaluation에서 재사용

관련 파일:

| 역할 | 파일 |
| --- | --- |
| EACL 실험용 CQ | `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json` |
| 내부 KG build용 CQ | `outputs/03_schema/competency_questions.json` |
| LLM runtime prompt 구성 코드 | `scripts/run_cape_llm_condition_baselines.py` |
| KG build 코드 | `scripts/build_cape_kg_eacl_experiment.py`, `scripts/build_ax_epak_internal_kg.py` |

---

## 5. 실제 CQ 목록

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

핵심 해석:

- CQ2, CQ3 때문에 `Artifact`와 `USES_INPUT` / `PRODUCES`를 별도로 추출했습니다.
- CQ5, CQ6 때문에 `DecisionGateway`와 `GuardCondition`을 별도 node로 만들었습니다.
- CQ11, CQ12 때문에 Layer 2 업무 KG를 NCS/PCF 표준 taxonomy와 연결했습니다.
- `P_minus_CQ` ablation은 이 CQ anchoring을 제거했을 때의 차이를 보기 위한 조건입니다.

---

## 6. 실제 프롬프트 파일과 산출물 구조

프롬프트 파일 위치:

`experiments/cape_kg_eacl_20260627/02_schema/prompts/`

프롬프트별 핵심 지시문:

| 조건 | 파일 | 저장된 핵심 프롬프트 |
| --- | --- | --- |
| B0_plain_llm | `B0_plain_llm_triple_extraction.txt` | `Extract subject-predicate-object triples from the chunk. Return JSON only.` |
| B1_predicate_constrained | `B1_predicate_constrained_llm.txt` | `Extract triples using only the allowed predicates. Return JSON only with evidence sentence ids.` |
| B2_current_project | `B2_current_project_baseline.txt` | `Extract Task Frames, then triples, then post-process into the Layer2 schema.` |
| B3_edc_style | `B3_edc_style_baseline.txt` | `Extract, define, and canonicalize open-schema KG items, then emit CAPE-compatible nodes and edges for scoring.` |
| B4_taxonomy_rag | `B4_taxonomy_rag_baseline.txt` | `Retrieve NCS/PCF/task taxonomy snippets, then extract schema-constrained triples with evidence.` |
| B5_procedural_prompt | `B5_procedural_prompt_baseline.txt` | `Extract actions, actors, gateways, guard conditions, artifact flows, and temporal/logical dependencies.` |
| B6_sac_kg_verifier_pruner | `B6_sac_kg_verifier_pruner_baseline.txt` | `Use existing generator candidates, then apply schema/evidence verification and pruning in the style of SAC-KG. This is a deterministic approximation, not a full SAC-KG reproduction.` |
| P_cape_kg_actual | `P_cape_kg.txt` | `Use CQ-linked schema retrieval, procedural frame extraction, evidence-span constrained relation extraction, span verification, ontology validation, procedural consistency checks, and active review scoring.` |
| P_minus_Schema_retrieval | `P_minus_Schema_retrieval.txt` | `Run CAPE-KG without chunk-specific schema/taxonomy retrieval; keep CQ, evidence grounding, procedural schema, validation, and mapping output shape.` |
| strict_json_contract | `strict_json_contract.txt` | JSON object만 반환, markdown/설명/XML/`<think>` 금지, `/no_think`, compact JSON, 빈 배열 사용 |

조건별 요구 산출물:

| 조건 | 요구한 JSON 출력 |
| --- | --- |
| B0_plain_llm | `triples` |
| B1_predicate_constrained | `edges` |
| B2_current_project | `nodes`, `edges` |
| B3_edc_style | `nodes`, `edges` |
| B4_taxonomy_rag | `nodes`, `edges`, `mappings` |
| B5_procedural_prompt | `nodes`, `edges` |
| B6_sac_kg_verifier_pruner | `nodes`, `edges`, `mappings` |
| P_cape_kg_actual | `nodes`, `edges`, `mappings` |
| P_minus_* ablation | 제거한 구성 요소에 따라 `nodes`, `edges`, `mappings` |

---

## 7. 실제 runtime prompt 공통 template

프롬프트 파일의 한 줄 지시문만 LLM에 들어간 것이 아닙니다. 실제 실행 시에는 chunk 문장, sentence id, evidence 조건, allowed schema, JSON shape가 결합되었습니다.

공통 runtime template:

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

strict JSON contract:

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

## 8. 제안 방법론 `P_cape_kg_actual` 실제 prompt 핵심

`P_cape_kg_actual`은 CQ, taxonomy snippet, evidence requirement, validator rule, allowed schema, JSON shape를 모두 포함한 조건입니다.

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

Taxonomy snippets:
{NCS/PCF/task taxonomy retrieval context}

Rules:
- Every node, edge, and mapping must include evidence_anchor_ids from the chunk.
- Use only the listed node types and edge predicates. Invalid schema terms will be rejected.
- Do not use outside knowledge.
- Keep Korean labels when the source text is Korean.
- Prefer concise, reusable labels.
- Hard limit: return at most 5 nodes, at most 5 edges, and at most 3 mappings.
- If the chunk does not support a field, return an empty array for that field.

Allowed node types for this condition:
["Artifact", "ArtifactFlow", "DecisionGateway", "DomainTask", "GuardCondition",
 "Principle", "ProcedureStep", "ReviewCheckpoint", "Risk", "Role"]

Allowed edge predicates for this condition:
["BRANCHES_TO", "FEEDS_INTO", "HAS_DECISION_GATEWAY", "HAS_GUARD_CONDITION",
 "HAS_PRINCIPLE", "HAS_REVIEW_CHECKPOINT", "HAS_RISK", "HAS_STEP",
 "PERFORMED_BY", "PRECEDES", "PRODUCES", "USED_AS_INPUT_FOR", "USES_INPUT"]

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
```

핵심은 프롬프트가 `node`, `edge`, `mapping`을 아무렇게나 생성하지 못하게 했다는 점입니다. 반드시 chunk 안의 sentence id를 evidence로 달고, 허용된 node type과 predicate 안에서만 JSON을 반환하도록 설계했습니다.

---

## 9. 최종 KG node는 어떻게 산출되었는가

최종 `outputs/07_layer2_graph/layer2_nodes.jsonl`의 node는 LLM 출력물을 그대로 저장한 것이 아닙니다. OCR evidence, task seed, alias/keyword, 용어 사전, procedure template을 결합해 생성했습니다.

Node 생성 흐름:

1. OCR sentence를 `EA-JS-*` evidence anchor로 변환
2. `TASK_SEEDS`의 업무 seed label, alias, keyword로 관련 sentence 검색
3. 검색된 sentence에서 Artifact, Role, DecisionGateway, Principle, Risk 후보를 용어 사전으로 추출
4. 각 task frame을 `DomainTask` node로 생성
5. task별 procedure template 또는 입력/산출물 기반 추론으로 `ProcedureStep` node 생성
6. 산출물이 다음 업무로 흘러가는 규칙으로 `ArtifactFlow` node 생성
7. `node_id` 기준으로 중복 제거
8. 모든 node에 evidence와 review status 부여

Node type별 현재 개수:

| Node type | 생성 방식 | 개수 |
| --- | --- | ---: |
| DomainTask | 업무 seed + evidence sentence 검색 | 22 |
| ProcedureStep | task별 procedure template 또는 입력/산출물 기반 step 추론 | 99 |
| Artifact | task evidence 안의 산출물/입력물 용어 매칭 | 14 |
| Role | 수행자/책임 주체 용어 매칭 | 10 |
| DecisionGateway | 의사결정 관련 용어 매칭 | 4 |
| GuardCondition | decision evidence에서 조건/가능성/경쟁/자원 등 조건 표현 추출 | 13 |
| Principle | 원칙/품질 기준 용어 매칭 | 5 |
| Risk | 위험/불리함/실패 가능성 용어 매칭 | 3 |
| ArtifactFlow | 특정 산출물이 다음 task 입력으로 쓰이는 규칙에서 생성 | 9 |

---

## 10. 최종 KG edge는 어떻게 산출되었는가

최종 `outputs/07_layer2_graph/layer2_edges.jsonl`의 edge는 node 사이 업무 관계를 predicate별 규칙으로 만든 뒤, source/target/evidence 검증을 통과한 것만 저장한 결과입니다.

Edge 생성 흐름:

1. task frame의 `inputs`, `outputs`, `roles`, `principles`, `risks` slot을 predicate로 변환
2. decision gateway와 guard condition을 별도 predicate로 연결
3. procedure step은 `HAS_STEP`, step 순서는 `PRECEDES`로 연결
4. artifact flow 규칙은 `FEEDS_INTO`, `USED_AS_INPUT_FOR`로 연결
5. 모든 edge를 triple record로 변환하고 `source_triple_ids` 부여
6. allowed predicate, source node 존재, target node 존재, evidence 존재 조건을 검증
7. 검증을 통과한 edge만 final graph에 저장

Predicate별 현재 개수:

| Predicate | 생성 방식 | 개수 |
| --- | --- | ---: |
| `PRODUCES` | task/step의 outputs slot을 Artifact node로 연결 | 220 |
| `USES_INPUT` | task/step의 inputs slot을 Artifact/Concept node로 연결 | 201 |
| `PERFORMED_BY` | task/step의 roles slot을 Role node로 연결 | 120 |
| `HAS_STEP` | DomainTask를 해당 ProcedureStep 목록에 연결 | 99 |
| `PRECEDES` | 같은 task 안에서 step order 기준으로 순서 연결 | 77 |
| `HAS_PRINCIPLE` | task/step의 principles slot 연결 | 64 |
| `HAS_DECISION_GATEWAY` | task/step에서 발견된 의사결정 node 연결 | 54 |
| `HAS_RISK` | task/step의 risks slot 연결 | 39 |
| `HAS_GUARD_CONDITION` | DecisionGateway에서 추출된 조건 node 연결 | 14 |
| `FEEDS_INTO` | Artifact가 다음 task로 흘러가는 규칙 연결 | 9 |
| `USED_AS_INPUT_FOR` | Artifact가 다음 task 입력으로 사용되는 규칙 연결 | 9 |

검증 결과:

| 검증 항목 | 결과 |
| --- | ---: |
| Final Layer 2 edges | 906 |
| Evidence가 있는 edges | 906 / 906 |
| `source_triple_ids`가 있는 edges | 906 / 906 |
| Dangling edges | 0 |
| Type violations | 0 |

---

## 11. Triple, Node, Edge의 관계

| 개념 | 설명 |
| --- | --- |
| Node | 업무 개념 자체. 예: `기회분석`, `Capture Plan`, `고객 정보 수집` |
| Edge | node 사이 관계. 예: `기회분석 USES_INPUT Capture Plan` |
| Triple | edge를 subject-predicate-object와 evidence text로 평가하기 위한 중간 record |
| Evidence anchor | 해당 node/edge/triple이 근거로 삼은 OCR sentence |

중간 산출물:

| 단계 | 파일 | 의미 |
| --- | --- | --- |
| Task frame | `outputs/04_task_frames/canonical_task_catalog.json` | 22개 canonical 업무 단위 |
| Procedure structure | `outputs/05_procedure/procedure_structures_clean.jsonl` | task별 step, order, decision 구조 |
| Schema-valid triple | `outputs/06_triples/layer2_triples_schema_valid.jsonl` | edge를 SPO/evidence 형식으로 표현한 906개 triple |
| Final nodes | `outputs/07_layer2_graph/layer2_nodes.jsonl` | graph 시각화/Neo4j/RDF에 들어가는 179개 node |
| Final edges | `outputs/07_layer2_graph/layer2_edges.jsonl` | source/target/evidence 검증을 통과한 906개 edge |

현재 triple 수와 edge 수가 906으로 같은 이유는, edge를 먼저 업무 관계로 만들고 이를 triple/evidence 형식으로 검증한 뒤 최종 graph edge로 저장했기 때문입니다.

---

## 12. LLM은 어디에 사용되었는가

LLM은 최종 KG를 통째로 생성한 도구가 아니라, 동일 chunk에 대해 여러 prompt/method condition이 어떤 후보를 생성하는지 비교하기 위한 prediction generator로 사용되었습니다.

사용한 모델:

| 모델 | 목적 | 상태 |
| --- | --- | --- |
| Qwen3-8B | 기본 baseline/proposed/ablation | 실행 완료 |
| Qwen3-14B | model scaling core conditions | 실행 완료 |
| Qwen3-32B-AWQ | 더 큰 모델의 현실적 scaling | 120 chunk core run 완료 |

LLM 조건:

| 조건 | 의미 |
| --- | --- |
| B0_plain_llm | schema 없는 plain triple extraction |
| B1_predicate_constrained | predicate만 제한한 baseline |
| B2_current_project | 기존 프로젝트 방식 baseline |
| B3_edc_style | EDC-style open-schema baseline |
| B4_taxonomy_rag | taxonomy retrieval context를 넣은 baseline |
| B5_procedural_prompt | procedural prompt baseline |
| B6_sac_kg_verifier_pruner | SAC-KG-style verifier/pruner approximation |
| P_cape_kg_actual | CQ + evidence + procedural schema + validator + standard bridge를 결합한 제안 조건 |
| P_minus_* | CQ/evidence/schema/bridge/validator 등을 제거한 ablation |

Qwen3-8B strict JSON full run의 validated output 요약:

| 조건 | Valid rows | Triples | Nodes | Edges | Mappings |
| --- | ---: | ---: | ---: | ---: | ---: |
| B0_plain_llm | 120 | 837 | 1,674 | 0 | 0 |
| B1_predicate_constrained | 120 | 0 | 0 | 663 | 0 |
| B2_current_project | 120 | 0 | 712 | 82 | 0 |
| B3_edc_style | 120 | 0 | 566 | 53 | 0 |
| B4_taxonomy_rag | 120 | 0 | 674 | 128 | 41 |
| B5_procedural_prompt | 120 | 0 | 957 | 119 | 0 |
| B6_sac_kg_verifier_pruner | 120 | 0 | 2,281 | 361 | 107 |
| P_cape_kg_actual | 120 | 0 | 549 | 275 | 52 |

이 표는 산출량 진단입니다. 많이 뽑았다고 성능이 좋다는 뜻은 아니며, 현재는 human-gold 전 silver/proxy diagnostic입니다.

---

## 13. 현재 실험 결과를 어떻게 해석해야 하는가

현재 LLM metric은 `human-gold` 기준이 아니라 KG-derived silver reference 기준입니다. 따라서 최종 논문 성능 claim이 아니라 diagnostic으로만 해석해야 합니다.

Qwen3-8B actual LLM silver diagnostics:

| Condition | Edge F1 | Predicate F1 | Node F1 | Evidence F1 | Parse errors |
| --- | ---: | ---: | ---: | ---: | ---: |
| B0_plain_llm | 0.0000 | 0.0000 | 0.0350 | 0.0239 | 63 |
| B1_predicate_constrained | 0.0000 | 0.1416 | 0.0000 | 0.0291 | 63 |
| B2_current_project | 0.0000 | 0.0068 | 0.0215 | 0.0503 | 97 |
| B6_sac_kg_verifier_pruner | 0.0017 | 0.0774 | 0.0564 | 0.1008 | 0 |
| P_cape_kg_actual | 0.0018 | 0.0482 | 0.0326 | 0.0655 | 113 |

Model scaling core silver diagnostics:

| Model | Condition | Rows | Edge F1 | Predicate F1 | Node F1 | Evidence F1 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Qwen3-8B | P_cape_kg_actual | 120 | 0.0018 | 0.0482 | 0.0326 | 0.0655 |
| Qwen3-14B | P_cape_kg_actual | 120 | 0.0017 | 0.0601 | 0.0298 | 0.0610 |
| Qwen3-32B-AWQ | P_cape_kg_actual | 120 | 0.0034 | 0.0662 | 0.0284 | 0.0542 |

해석:

- Qwen3-32B-AWQ는 8B보다 silver 기준 edge/predicate 일부가 올라갔습니다.
- 그러나 이 차이는 human-gold 기준이 아니므로 최종 성능 우수성 claim으로 쓰면 안 됩니다.
- 현재 단계에서 말할 수 있는 것은 "여러 모델과 조건을 실행했고, human-gold 평가를 위한 prediction artifacts가 준비되었다"입니다.

---

## 14. 구조 진단 결과

KG 자체의 structural quality는 자동 진단 기준으로 안정적으로 나왔습니다.

| 항목 | 결과 |
| --- | ---: |
| Ontology conformance | 1.0000 |
| Domain/range errors | 0 |
| Evidence-missing edges | 0 |
| Procedural consistency | 0.9950 |
| Cycles | 0 |
| CQ answerability | 0.9167 |

해석:

- 이 결과는 "KG 구조가 schema/evidence 관점에서 잘 정리되어 있다"는 자동 진단입니다.
- 하지만 사람 정답과 비교한 extraction 성능은 아직 아닙니다.

---

## 15. NCS/PCF standard bridge 결과

| 항목 | 값 |
| --- | ---: |
| Canonical Layer 2 tasks | 22 |
| NCS mapping candidates | 110 |
| PCF mapping candidates | 110 |
| NCS Top-K coverage | 1.000 |
| PCF Top-K coverage | 1.000 |
| NCS-PCF crosswalk candidates | 220 |
| Shared Layer 2 tasks | 22 |

해석:

- Layer 2 업무 KG를 NCS/PCF 표준축과 연결하는 후보 생성은 완료되었습니다.
- 그러나 mapping/crosswalk는 아직 expert review 전입니다.
- 따라서 "자동 후보를 생성했다"는 말은 가능하지만, "정확한 mapping 성능이 검증되었다"는 claim은 아직 불가합니다.

---

## 16. 현재 claim gate 상태

현재 claim gate는 `FAIL`입니다. 이는 실험 실패가 아니라, human-gold와 expert review 전까지 과도한 성능 claim을 막기 위한 의도된 안전장치입니다.

| Gate | 상태 | 이유 |
| --- | --- | --- |
| Evaluation chunks >= 100 | PASS | 120 chunks 준비 |
| B0/B1/B2 actual LLM baseline | PASS | 각 120 rows 실행 |
| P_cape_kg_actual generation | PASS | 120 rows 실행 |
| Ablations >= 3 | PASS | 6개 ablation 실행 |
| Public subset experiment | PASS | PAGED/Text2KG adapter 실행 |
| Human-gold chunks >= 100 | FAIL | adjudicated chunks 0 |
| Human-gold items >= 500 | FAIL | gold items 0 |
| IAA | FAIL | annotator pair completion 0 |
| Proposed human-gold scoring | FAIL | human-gold 미완료 |
| Mapping expert review | FAIL/pending | NCS/PCF candidate rows 220 pending |
| NCS-PCF crosswalk expert review | FAIL/pending | crosswalk rows 220 pending |
| Active-review human effort | pending | timing/correction evidence 미반환 |

Human review handoff 기준:

| 범주 | 파일 수 | 현재 상태 |
| --- | ---: | --- |
| Minimum paper-gate return files | 11 | 0개 반환 |
| Optional/strong return files | 3 | 0개 반환 |
| 전체 추적 human return files | 14 | 0개 반환 |

---

## 17. 교수님께 보고할 때의 가장 안전한 표현

사용해도 되는 표현:

> 현재까지 한국어 수주/제안 업무 문서에 대해 Layer 1 NCS/PCF 표준 KG와 Layer 2 evidence-grounded procedural KG 구축은 완료했습니다. Layer 2 KG는 179 nodes, 906 edges이며, accepted edge의 evidence 누락은 없습니다. 또한 같은 120 evaluation chunks에 대해 Qwen3-8B/14B/32B-AWQ 기반 baseline, proposed, ablation, public adapter 실험을 실행했고, human-gold 평가를 위한 산출물과 handoff package를 준비했습니다.

아직 쓰면 안 되는 표현:

> CAPE-KG가 baseline보다 최종적으로 우수하다.

> NCS/PCF mapping 정확도가 검증되었다.

> active review가 실제 사람 검수 시간을 줄였다.

이 표현들은 human-gold annotation, IAA, adjudication, mapping/crosswalk expert review, active-review timing/correction evidence가 들어온 뒤에만 주장할 수 있습니다.

---

## 18. 발표에서 강조할 핵심 메시지

1. **KG 구축은 완료되었습니다.**  
   Layer 1 NCS/PCF, Layer 2 업무 KG, evidence grounding, NCS/PCF candidate bridge까지 산출되었습니다.

2. **LLM은 최종 KG를 그대로 만든 것이 아니라, 비교 실험용 후보 생성기로 사용되었습니다.**  
   최종 KG는 evidence, schema, rule/template, validator를 통해 조립되었고, LLM 조건은 baseline/proposed/ablation 비교를 위한 별도 prediction 산출물입니다.

3. **CQ가 연구 설계의 중심입니다.**  
   CQ는 어떤 node와 edge를 뽑을지, 어떤 predicate가 필요한지, 어떤 평가를 해야 하는지 연결하는 anchor입니다.

4. **현재 수치는 대부분 diagnostic입니다.**  
   structural diagnostics와 silver/proxy LLM metrics는 준비 상태를 보여주지만, 최종 성능표는 human-gold 이후 확정해야 합니다.

5. **다음 단계는 사람 검수입니다.**  
   최소 논문 claim을 위해서는 100개 이상 chunk의 two-annotator annotation, IAA, adjudication, proposed human-gold scoring, expert review가 필요합니다.

---

## 19. 교수님 질문에 대한 짧은 답변 예시

### Q. 어떤 프롬프트로 실험했나요?

`P_cape_kg_actual`은 CQ, evidence anchor, allowed node/edge schema, NCS/PCF taxonomy snippet, strict JSON contract를 함께 넣은 prompt입니다. baseline은 여기서 schema, CQ, taxonomy, validator 등을 일부 제거하거나 단순화한 비교군입니다.

### Q. CQ는 누가 만들었나요?

LLM이 자동으로 만든 것이 아니라, 연구자가 이 KG가 답해야 할 업무 질문을 먼저 설계했습니다. 이후 각 CQ를 predicate와 node type에 연결했고, prompt와 structural evaluation에서 동일하게 재사용했습니다.

### Q. Node는 어떻게 만들어졌나요?

업무 seed, alias/keyword, evidence sentence 검색, procedure template, 용어 사전 기반 추출로 만들었습니다. 최종 node는 179개이며, `DomainTask`, `ProcedureStep`, `Artifact`, `Role`, `DecisionGateway`, `GuardCondition`, `Risk` 등으로 구성됩니다.

### Q. Edge는 어떻게 만들어졌나요?

task frame의 input/output/role/risk/principle slot과 procedure order를 predicate로 변환했습니다. source node, target node, allowed predicate, evidence anchor가 모두 있는 edge만 최종 graph에 저장했습니다. 최종 edge는 906개이고 evidence 누락은 0개입니다.

### Q. 지금 main result table이 나왔나요?

논문에 넣을 최종 human-gold main result table은 아직 아닙니다. 현재 table은 silver/proxy diagnostic과 structural diagnostic입니다. human-gold, IAA, adjudication 이후 최종 main table을 확정해야 합니다.

### Q. 지금 교수님께 무엇을 보고하면 되나요?

KG 구축과 실험 인프라는 완료되었고, LLM baseline/proposed/ablation/model scaling도 실행되었습니다. 다만 최종 성능 우수성 claim은 사람 검수 이후에만 가능하다고 보고하는 것이 가장 정확합니다.
