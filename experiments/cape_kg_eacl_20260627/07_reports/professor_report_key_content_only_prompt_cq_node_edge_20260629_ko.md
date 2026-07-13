# 교수님 보고용 별도 핵심 요약: Prompt, CQ, Node/Edge 생성 방식

Generated: 2026-06-29  
Experiment directory: `experiments/cape_kg_eacl_20260627`  
KG output directory: `outputs`

이 문서는 `professor_report_slide_contents_current_20260628_ko.md`와 별개로, 교수님께 가장 먼저 설명해야 할 핵심 내용만 압축한 별도 요약본입니다. 초점은 다음 네 가지입니다.

1. 어떤 연구 방법론으로 실험을 진행했는가
2. 실제 어떤 프롬프트 조건으로 어떤 산출물을 만들었는가
3. CQ는 어떻게 정의했고, CQ가 node/edge 설계에 어떻게 연결되었는가
4. 최종 Layer 2 KG의 node와 edge는 각각 어떤 규칙으로 산출되었는가

---

## 1. 한 문장 요약

본 연구는 한국어 수주/제안 업무 문서에서 `DomainTask`, `ProcedureStep`, `Artifact`, `Role`, `DecisionGateway`, `GuardCondition`, `Risk` 등을 원문 sentence evidence에 연결해 절차형 Layer 2 KG로 구축하고, 이를 NCS/PCF 표준 Layer 1 KG와 후보 매핑하는 CAPE-KG 실험입니다.

핵심은 LLM에게 자유롭게 triple을 쓰게 한 것이 아니라, **CQ, schema, allowed predicate, evidence anchor, validator, NCS/PCF bridge**로 LLM 출력과 KG 생성을 통제했다는 점입니다.

---

## 2. 현재까지 완료된 것과 아직 주장하면 안 되는 것

| 구분 | 현재 상태 | 교수님께 설명할 표현 |
| --- | --- | --- |
| Layer 1 NCS KG | 완료 | NCS 표준 taxonomy를 기준축으로 구축 |
| Layer 1 PCF KG | 완료 | PCF process taxonomy와 metric을 기준축으로 구축 |
| Layer 2 업무 KG | 완료 | 수주/제안 문서 기반 procedural KG 구축 |
| Evidence grounding | 완료 | 최종 Layer 2 node/edge가 sentence evidence에 연결됨 |
| NCS/PCF mapping 후보 | 완료 | Layer 2 task별 Top-K 후보 생성, expert review 전 |
| LLM baseline/proposed/ablation | 실행 완료 | Qwen3 기반 조건별 JSON 산출물 생성 |
| 최종 성능 claim | 아직 불가 | human-gold annotation, IAA, adjudication, expert review 이후 가능 |

현재 말할 수 있는 것은 **KG 구축과 실험 인프라가 준비되었다**는 점입니다. 아직 말하면 안 되는 것은 **CAPE-KG가 human-gold 기준으로 기존 방법보다 성능이 높다**는 최종 성능 주장입니다.

---

## 3. 핵심 산출물 수량

| 산출물 | 현재 수량 |
| --- | ---: |
| OCR evidence anchors / clean sentences | 5,009 |
| Layer 2 chunks | 214 |
| LLM evaluation chunks | 120 |
| Layer 1 NCS nodes | 4,109 |
| Layer 1 PCF nodes | 5,301 |
| Layer 2 nodes | 179 |
| Layer 2 edges | 906 |
| Schema-valid clean triples | 906 |
| Canonical DomainTask | 22 |
| NCS mapping candidates | 110 |
| PCF mapping candidates | 110 |
| NCS-PCF crosswalk candidates | 220 |
| Evidence-missing Layer 2 edges | 0 |
| Dangling edges | 0 |
| Type violations | 0 |

핵심 파일은 다음입니다.

| 목적 | 파일 |
| --- | --- |
| 최종 Layer 2 node | `outputs/07_layer2_graph/layer2_nodes.jsonl` |
| 최종 Layer 2 edge | `outputs/07_layer2_graph/layer2_edges.jsonl` |
| evidence index | `outputs/07_layer2_graph/layer2_evidence_index.jsonl` |
| NCS mapping 후보 | `outputs/08_mapping/l2_ncs_mapping_candidates.jsonl` |
| PCF mapping 후보 | `outputs/08_mapping/l2_pcf_mapping_candidates.jsonl` |
| KG viewer | `outputs/09_visualization/kg_viewer.html` |
| build report | `outputs/10_evaluation/final_build_report.md` |
| prompt/node/edge traceability | `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md` |

---

## 4. 전체 방법론 흐름

실험 파이프라인은 다음 순서로 진행되었습니다.

1. OCR workbook을 sentence 단위로 정제
2. 각 sentence에 evidence anchor ID 부여
3. NCS/PCF 표준 데이터를 Layer 1 KG로 구축
4. 자이제 OCR 문서를 Layer 2 chunk로 분할
5. CQ와 procedural schema를 정의
6. task seed, alias, keyword, evidence sentence로 `DomainTask` 후보 생성
7. task별 procedure template과 입력/산출물/역할/조건 단서로 `ProcedureStep` 및 관련 node 생성
8. predicate별 domain/range와 evidence 조건을 만족하는 edge만 생성
9. 최종 Layer 2 KG를 JSONL, GraphML, HTML viewer, Neo4j CSV로 export
10. 동일 chunk에 대해 LLM baseline, proposed, ablation, model scaling 조건을 실행
11. human review handoff와 claim gate를 만들어 final claim을 보수적으로 통제

중요한 구분:

| 구분 | 의미 |
| --- | --- |
| 최종 KG | rule/schema/evidence 기반으로 조립된 현재 KG |
| LLM 실험 산출물 | 조건별 prompt가 생성한 prediction JSON |
| 최종 논문 성능 | human-gold 반환 후 다시 계산해야 하는 precision/recall/F1 |

---

## 5. CQ는 어떻게 만들었는가

CQ는 LLM에게 자동으로 물어봐서 만든 질문이 아니라, **이 KG가 답해야 하는 업무 질문**을 연구자가 먼저 설계한 것입니다. 즉, CQ는 ontology requirement이자 extraction target이며, 나중에는 evaluation question으로도 쓰입니다.

CQ 생성 방식은 다음과 같습니다.

1. 연구 문제를 "수주/제안 업무 문서에서 절차형 KG를 구축하는 문제"로 정의
2. 업무자가 실제로 물을 질문 범주를 정함
   - 어떤 업무와 단계가 있는가
   - 각 업무는 어떤 입력 자료를 쓰는가
   - 각 업무는 어떤 산출물을 만드는가
   - 누가 수행하거나 책임지는가
   - 어떤 의사결정 지점과 조건이 있는가
   - 산출물이 다음 업무에서 어떻게 쓰이는가
   - 각 지식 항목은 원문 어디에 근거하는가
   - 해당 업무는 NCS/PCF 표준과 어떻게 연결되는가
3. 각 CQ를 필요한 node type과 predicate에 연결
4. 같은 CQ 목록을 schema, LLM prompt, ablation, structural evaluation에서 재사용

CQ source files:

| 역할 | 파일 |
| --- | --- |
| EACL 실험용 CQ | `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json` |
| 내부 KG build용 CQ | `outputs/03_schema/competency_questions.json` |
| CQ/schema generation code | `scripts/build_ax_epak_internal_kg.py`, `scripts/build_cape_kg_eacl_experiment.py` |

---

## 6. 실제 CQ 목록

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

예를 들어 CQ2와 CQ3이 있기 때문에 `Artifact`, `USES_INPUT`, `PRODUCES`가 필요합니다. CQ5와 CQ6이 있기 때문에 `DecisionGateway`, `GuardCondition`, `HAS_DECISION_GATEWAY`, `HAS_GUARD_CONDITION`이 필요합니다. CQ11과 CQ12가 있기 때문에 Layer 2 task를 NCS/PCF 표준과 연결합니다.

---

## 7. 실제 프롬프트 파일과 조건별 산출물

프롬프트 파일 위치:

`experiments/cape_kg_eacl_20260627/02_schema/prompts/`

아래는 실제 저장된 prompt text와 요구한 JSON 산출물입니다.

| 조건 | 실제 prompt text | 요구 산출물 |
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

추가 ablation 조건은 runtime에서 생성되었습니다.

| 조건 | 제거한 요소 | 요구 산출물 |
| --- | --- | --- |
| P_minus_CQ | competency-question anchoring 제거 | `nodes`, `edges`, `mappings` |
| P_minus_Evidence | evidence anchor 요구 약화 | `nodes`, `edges`, `mappings` |
| P_minus_Procedural_schema | 절차형 schema 제거 | `nodes`, `edges`, `mappings` |
| P_minus_Validator | validator rejection 제거 | `nodes`, `edges`, `mappings` |
| P_minus_Standard_bridge | NCS/PCF bridge 제거 | `nodes`, `edges` |

---

## 8. 실제 runtime prompt 공통 제약

프롬프트 파일의 한 줄 문장만 LLM에 들어간 것이 아닙니다. 실제 실행 시에는 해당 조건 프롬프트에 chunk sentence, sentence ID, allowed node type, allowed predicate, JSON shape, strict JSON contract가 결합되었습니다.

공통 제약은 다음입니다.

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

Qwen 계열 strict JSON 실행에서는 다음 contract를 추가했습니다.

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

---

## 9. 제안 방법론 P_cape_kg_actual의 의미

`P_cape_kg_actual`은 본 연구의 제안 방법론 조건입니다. 핵심 구성은 다음입니다.

| 구성 | 역할 |
| --- | --- |
| CQ anchoring | 어떤 업무 질문에 답하기 위한 추출인지 통제 |
| Schema retrieval | chunk에 필요한 schema/taxonomy snippet만 제공 |
| Procedural schema | task, step, role, artifact, decision, guard, risk를 구분 |
| Evidence grounding | 모든 node/edge/mapping에 chunk-local evidence anchor 요구 |
| Ontology validation | allowed node type, predicate, domain/range 위반을 거부 |
| Standard bridge | NCS/PCF 후보 mapping을 함께 산출 |
| Active review scoring | 사람 검수가 필요한 후보를 우선순위화 |

즉, 제안 방법론은 "좋은 프롬프트 하나"가 아니라, CQ와 schema와 evidence 검증을 결합한 extraction condition입니다.

---

## 10. LLM 조건별 validated output 수량

아래 수량은 Qwen3-8B strict JSON full run과 SAC-KG-style baseline valid output을 합산한 release traceability 기준입니다.

| condition | valid rows | triples | nodes | edges | mappings |
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

주의할 점은 이 표가 성능표가 아니라는 것입니다. 이 표는 각 조건에서 JSON이 정상 생성되었고, 어떤 key를 얼마나 산출했는지를 보여주는 traceability 표입니다. 최종 성능 평가는 human-gold 이후에 해야 합니다.

---

## 11. 최종 Layer 2 node는 어떻게 생성했는가

최종 Layer 2 KG node는 총 179개이고, 179개 모두 evidence anchor를 가집니다.

| node type | count | 생성 방식 |
| --- | ---: | --- |
| ProcedureStep | 99 | task별 procedure template 또는 입력/산출물 기반 step 추론으로 생성 |
| DomainTask | 22 | `TASK_SEEDS`의 label, alias, keyword로 OCR sentence evidence를 검색해 생성 |
| Artifact | 14 | task evidence 안의 입력물/산출물 용어 매칭으로 생성 |
| GuardCondition | 13 | 의사결정 evidence에서 조건, 가능성, 경쟁, 자원 등 조건 표현을 정규식으로 추출 |
| Role | 10 | 수행자/책임 주체 용어 매칭으로 생성 |
| ArtifactFlow | 9 | 특정 산출물이 다음 task 입력으로 쓰이는 규칙에서 생성 |
| Principle | 5 | 원칙/품질 기준 용어 매칭으로 생성 |
| DecisionGateway | 4 | 의사결정 관련 용어 매칭으로 생성 |
| Risk | 3 | 위험, 불리함, 실패 가능성 용어 매칭으로 생성 |

해석:

- `DomainTask`는 업무의 중심 단위입니다.
- `ProcedureStep`은 task 내부 실행 절차입니다.
- `Artifact`는 입력물과 산출물입니다.
- `Role`은 수행자 또는 책임 주체입니다.
- `DecisionGateway`와 `GuardCondition`은 업무 분기와 판단 조건입니다.
- `Risk`와 `Principle`은 업무 수행상의 위험과 원칙입니다.

---

## 12. 최종 Layer 2 edge는 어떻게 생성했는가

최종 Layer 2 KG edge는 총 906개이고, 906개 모두 evidence anchor와 source triple ID를 가집니다. dangling edge는 0개입니다.

| predicate | count | 생성 방식 |
| --- | ---: | --- |
| PRODUCES | 220 | task/step의 outputs slot을 `Artifact` node로 연결 |
| USES_INPUT | 201 | task/step의 inputs slot을 `Artifact` 또는 concept성 node로 연결 |
| PERFORMED_BY | 120 | task/step의 roles slot을 `Role` node로 연결 |
| HAS_STEP | 99 | `DomainTask`를 해당 `ProcedureStep` 목록에 연결 |
| PRECEDES | 77 | 같은 task 안에서 step order 기준으로 순서 연결 |
| HAS_PRINCIPLE | 64 | task/step의 principles slot을 `Principle` node로 연결 |
| HAS_DECISION_GATEWAY | 54 | task/step에서 발견된 의사결정 node를 연결 |
| HAS_RISK | 39 | task/step의 risks slot을 `Risk` node로 연결 |
| HAS_GUARD_CONDITION | 14 | `DecisionGateway`에서 추출된 조건 node를 연결 |
| FEEDS_INTO | 9 | `Artifact`가 다음 task로 흘러가는 규칙을 연결 |
| USED_AS_INPUT_FOR | 9 | `Artifact`가 다음 task 입력으로 사용되는 규칙을 연결 |

edge 생성 시에는 다음 조건을 만족해야 합니다.

1. source node와 target node가 실제 node 파일에 존재해야 함
2. predicate가 허용된 schema predicate여야 함
3. predicate별 domain/range가 맞아야 함
4. source triple ID가 있어야 함
5. evidence anchor ID가 있어야 함
6. evidence anchor가 OCR sentence/chunk에 연결되어야 함

---

## 13. Layer 1과 Layer 2는 어떻게 연결했는가

Layer 1은 표준 기준축이고, Layer 2는 실제 업무 문서 기반 KG입니다. 두 레이어를 직접 병합하지 않고 후보 mapping edge로 느슨하게 연결했습니다.

| 연결 | 현재 산출물 | 해석 |
| --- | --- | --- |
| Layer 2 task -> NCS | `l2_ncs_mapping_candidates.jsonl` | 업무 task가 어떤 NCS 능력단위와 관련될 수 있는지 Top-K 후보 |
| Layer 2 task -> PCF | `l2_pcf_mapping_candidates.jsonl` | 업무 task가 어떤 PCF process와 관련될 수 있는지 Top-K 후보 |
| NCS <-> PCF crosswalk | `l2_ncs_pcf_crosswalk_candidates.jsonl` | Layer 2 task를 bridge로 활용한 표준 간 후보 연결 |

현재 mapping은 **후보 추천**입니다. expert review가 끝나기 전에는 정답 mapping으로 주장하면 안 됩니다.

---

## 14. 교수님께 설명할 때의 핵심 문장

다음 표현이 가장 정확합니다.

> 현재 저는 한국어 수주/제안 업무 문서에서 절차형 업무 지식을 추출해 Layer 2 KG로 구축했고, NCS/PCF 표준 taxonomy를 Layer 1 기준축으로 만들어 두 레이어를 후보 mapping으로 연결했습니다. 이때 KG 구축은 LLM 자유 생성이 아니라 CQ, schema, evidence anchor, allowed predicate, validator를 결합한 CAPE-KG 방식으로 통제했습니다. 자동 구축과 LLM 조건별 실험은 완료되었지만, 논문에서 최종 성능 우수성을 주장하려면 human-gold annotation, IAA, adjudication, mapping expert review가 아직 필요합니다.

---

## 15. 남은 핵심 작업

| 작업 | 현재 상태 | 필요한 이유 |
| --- | --- | --- |
| Human-gold annotation | 미완료 | node/edge/evidence F1 계산 필요 |
| IAA 계산 | 미완료 | annotator 간 일치도 필요 |
| Adjudication | 미완료 | 최종 gold label 확정 필요 |
| Proposed human-gold scoring | 미완료 | CAPE-KG 최종 성능표 산출 필요 |
| Mapping expert review | 미완료 | NCS/PCF mapping claim 필요 |
| Crosswalk expert review | 미완료 | Layer 2 bridge 기반 NCS-PCF 연결 claim 필요 |
| Active-review effort evidence | 미완료 | 검수 효율성 claim 필요 |

따라서 현재 발표에서는 **구축 방법론, 산출물, traceability, claim gate**를 강조하고, 최종 성능 우수성은 사람 검수 이후 확정한다고 설명하는 것이 안전합니다.

