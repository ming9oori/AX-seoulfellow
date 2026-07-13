# 교수님 보고용 핵심 요약본

Generated: 2026-06-29  
Related full slide draft: `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md`  
Experiment directory: `experiments/cape_kg_eacl_20260627`  
KG output directory: `outputs`

이 문서는 기존 슬라이드별 발표 원고와 별개로, 교수님께 연구 진행 상황을 짧고 정확하게 설명하기 위한 핵심 요약본입니다. 중심 질문은 다음 네 가지입니다.

1. 어떤 방법론으로 연구를 진행했는가?
2. 어떤 CQ와 prompt로 LLM 실험을 구성했는가?
3. node와 edge는 각각 어떤 방식으로 산출했는가?
4. 현재 어떤 결과는 보고 가능하고, 어떤 결과는 아직 human review 이후에만 주장 가능한가?

---

## 1. 한 문장 요약

본 연구는 한국어 수주/제안 업무 문서에서 업무 task, 절차 step, 입력/산출물, 수행 역할, 의사결정, 조건, 위험을 추출하여 원문 sentence evidence에 연결된 procedural KG를 구축하고, 이를 NCS/PCF 표준 taxonomy와 연결하는 CAPE-KG 실험이다.

가장 중요한 해석은 다음이다.

> 현재까지 Layer 1 표준 KG, Layer 2 업무 KG, evidence grounding, NCS/PCF mapping 후보, LLM baseline/ablation/model-scaling diagnostic, Neo4j/HTML 시각화, human-review handoff까지 구축했다. 다만 최종 성능 우수성, mapping 품질, active-review 효율성은 human-gold annotation과 expert review가 완료된 뒤에만 주장할 수 있다.

---

## 2. 현재 핵심 결과

| 항목 | 현재 값 | 근거 파일 |
| --- | ---: | --- |
| OCR evidence anchors | 5,009 | `outputs/10_evaluation/final_build_report.md` |
| Layer 2 chunks | 214 | `outputs/02_ocr/layer2_chunks.jsonl` |
| Layer 1 NCS nodes | 4,109 | `outputs/01_layer1/layer1_quality_report.md` |
| Layer 1 PCF nodes | 5,301 | `outputs/01_layer1/layer1_quality_report.md` |
| Layer 2 nodes | 220 | `outputs/07_layer2_graph/layer2_nodes.jsonl` |
| Layer 2 edges | 947 | `outputs/07_layer2_graph/layer2_edges.jsonl` |
| Clean triples | 947 | `outputs/06_triples/layer2_triples_clean.jsonl` |
| NCS mapping candidates | 110 | `outputs/08_mapping/l2_ncs_mapping_candidates.jsonl` |
| PCF mapping candidates | 110 | `outputs/08_mapping/l2_pcf_mapping_candidates.jsonl` |
| NCS-PCF crosswalk candidates | 220 | `outputs/08_mapping/l2_ncs_pcf_crosswalk_candidates.jsonl` |
| LLM evaluation chunks | 120 | `experiments/cape_kg_eacl_20260627/01_data/evaluation_chunks.jsonl` |
| Pre-human validation | PASS, 92 checks 중 91 PASS / 1 WARN | `experiments/cape_kg_eacl_20260627/06_release/pre_human_handoff_validation.md` |
| Claim gate | FAIL, expected | `experiments/cape_kg_eacl_20260627/06_release/claim_gate_report.md` |

Claim gate가 FAIL인 이유는 자동 실험이 실패했기 때문이 아니다. 아직 adjudicated human-gold chunk 100개, human-gold item 500개, IAA, proposed method human-gold scoring, mapping expert review가 완료되지 않았기 때문에 최종 논문 claim을 막고 있는 것이다.

---

## 3. 방법론 핵심

계획서의 CEP-Onto 방향을 현재 실험 패키지에서는 CAPE-KG 형태로 구현했다. 핵심은 LLM에게 단순히 triple을 자유 생성시키는 것이 아니라, CQ, schema, evidence anchor, validator, mapping module로 출력을 통제하는 것이다.

| 구성 요소 | 역할 |
| --- | --- |
| Competency Questions | KG가 답해야 할 업무 질문을 먼저 정의 |
| Procedural schema | `DomainTask`, `ProcedureStep`, `Artifact`, `Role`, `DecisionGateway`, `GuardCondition` 등 node type 정의 |
| Predicate constraints | `HAS_STEP`, `USES_INPUT`, `PRODUCES`, `PERFORMED_BY`, `PRECEDES` 등 edge type 제한 |
| Evidence grounding | 모든 accepted edge를 OCR sentence evidence anchor에 연결 |
| Validator | unknown type/predicate, domain/range violation, dangling edge, evidence 누락 검증 |
| Standard bridge | Layer 2 업무 KG를 NCS/PCF 후보와 연결 |
| Human-review handoff | human-gold, IAA, adjudication, expert mapping review를 받을 수 있도록 패키지 구성 |

전체 파이프라인은 다음 순서로 진행되었다.

1. OCR workbook 정제 및 sentence evidence anchor 생성
2. NCS/PCF Layer 1 표준 KG 구축
3. Layer 2 chunk 생성
4. CQ와 procedural schema 정의
5. task frame, procedure, triple 후보 생성
6. schema/evidence 검증 후 Layer 2 node/edge 조립
7. NCS/PCF mapping 후보 및 NCS-PCF crosswalk 후보 생성
8. LLM baseline, proposed, ablation, model scaling diagnostic 실행
9. structural evaluation, evidence-span diagnostic, predicate-cue diagnostic 실행
10. Neo4j/HTML/RDF/GraphML 시각화 및 release/handoff 패키지 생성

---

## 4. CQ는 어떻게 생성하고 사용했는가

CQ는 LLM이 자동으로 만든 질문이 아니라, 연구자가 먼저 정의한 KG 요구사항이다. 즉, "이 KG가 어떤 업무 질문에 답할 수 있어야 하는가"를 정하고, 각 질문을 node type과 predicate에 연결했다.

생성 원칙은 다음과 같다.

| 단계 | 내용 |
| --- | --- |
| 연구 문제 정의 | 한국어 수주/제안 업무 문서에서 절차형 업무 KG 구축 |
| 질문 범주 설정 | 업무 구성, 순서, 입력, 산출물, 수행자, 의사결정, 조건, 리뷰, 원칙, 위험, evidence, 표준 연결 |
| schema 연결 | 질문을 `DomainTask`, `ProcedureStep`, `Artifact`, `Role`, `DecisionGateway`, `GuardCondition` 등에 연결 |
| predicate 연결 | 질문을 `HAS_STEP`, `PRECEDES`, `USES_INPUT`, `PRODUCES`, `PERFORMED_BY` 등에 연결 |
| 실험 재사용 | LLM prompt, ablation, CQ answerability, review priority에서 같은 CQ를 사용 |

실제 CQ 목록은 다음과 같다.

| CQ | 질문 | 주요 연결 predicate |
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
| CQ10 | 각 지식 항목은 원문 어느 chunk/page/span에 근거가 있는가? | evidence anchor |
| CQ11 | 특정 업무는 어떤 NCS 능력단위와 관련되는가? | NCS mapping candidate |
| CQ12 | 특정 업무는 PCF 프로세스 체계상 어디에 위치하는가? | PCF mapping candidate |

관련 파일은 다음이다.

| 역할 | 파일 |
| --- | --- |
| EACL 실험용 CQ | `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json` |
| 내부 KG build용 CQ | `outputs/03_schema/competency_questions.json` |
| CQ query pack | `experiments/cape_kg_eacl_20260627/06_release/cq_query_pack.json` |
| CQ answerability report | `outputs/10_evaluation/cq_answerability_report.md` |

---

## 5. 실제 prompt와 LLM 조건

실제 prompt 파일은 다음 위치에 있다.

`experiments/cape_kg_eacl_20260627/02_schema/prompts/`

조건별 prompt 핵심 문장은 다음과 같다.

| 조건 | 목적 | 실제 prompt text |
| --- | --- | --- |
| `B0_plain_llm` | schema 없는 plain triple baseline | `Extract subject-predicate-object triples from the chunk. Return JSON only.` |
| `B1_predicate_constrained` | predicate만 제한한 baseline | `Extract triples using only the allowed predicates. Return JSON only with evidence sentence ids.` |
| `B2_current_project` | 기존 task-frame 후처리 방식 baseline | `Extract Task Frames, then triples, then post-process into the Layer2 schema.` |
| `B3_edc_style` | open-schema EDC-style baseline | `Extract, define, and canonicalize open-schema KG items, then emit CAPE-compatible nodes and edges for scoring.` |
| `B4_taxonomy_rag` | taxonomy retrieval baseline | `Retrieve NCS/PCF/task taxonomy snippets, then extract schema-constrained triples with evidence.` |
| `B5_procedural_prompt` | procedural prompt baseline | `Extract actions, actors, gateways, guard conditions, artifact flows, and temporal/logical dependencies.` |
| `B6_sac_kg_verifier_pruner` | verifier/pruner baseline | `Use existing generator candidates, then apply schema/evidence verification and pruning in the style of SAC-KG. This is a deterministic approximation, not a full SAC-KG reproduction.` |
| `P_cape_kg_actual` | 제안 방법론 | `Use CQ-linked schema retrieval, procedural frame extraction, evidence-span constrained relation extraction, span verification, ontology validation, procedural consistency checks, and active review scoring.` |
| `P_minus_CQ` | CQ 제거 ablation | runtime condition에서 CQ anchoring 제거 |
| `P_minus_Evidence` | evidence 요구 약화 ablation | runtime condition에서 evidence grounding 조건 약화 |
| `P_minus_Procedural_schema` | procedural schema 제거 ablation | runtime condition에서 procedural node/edge 제약 제거 |
| `P_minus_Validator` | validator 제거 ablation | runtime condition에서 validator rejection/pruning 제거 |
| `P_minus_Standard_bridge` | 표준 bridge 제거 ablation | NCS/PCF mapping output 제거 |
| `P_minus_Schema_retrieval` | chunk-specific retrieval 제거 ablation | `Run CAPE-KG without chunk-specific schema/taxonomy retrieval; keep CQ, evidence grounding, procedural schema, validation, and mapping output shape.` |

중요한 점은 위 한 줄짜리 prompt만 모델에 들어간 것이 아니라는 점이다. 실제 실행 시 `scripts/run_cape_llm_condition_baselines.py`가 다음 정보를 함께 붙였다.

| runtime prompt 구성 | 내용 |
| --- | --- |
| chunk metadata | `chunk_id`, page range, sentence ids |
| chunk sentences | 해당 chunk의 sentence block |
| allowed node types | schema에서 허용한 node type |
| allowed predicates | schema에서 허용한 edge predicate |
| CQ block | 12개 competency question 요약 |
| output schema | `nodes`, `edges`, `mappings` 또는 `triples` JSON 구조 |
| strict JSON contract | markdown/prose/thinking 없이 JSON object만 반환 |

공통 strict JSON 제약의 핵심은 다음이다.

```text
Return exactly one JSON object and nothing else.
Do not include markdown, code fences, comments, XML tags, <think> blocks, prose, or explanations.
Every extracted item must include at least one evidence_anchor_ids value from the chunk.
Do not use outside knowledge.
Keep Korean labels when the source text is Korean.
```

---

## 6. Node는 어떻게 산출했는가

최종 Layer 2 node는 220개이다. node는 LLM 출력만 그대로 저장한 것이 아니라, task seed, alias, keyword, procedure template, OCR evidence anchor, schema rule을 결합해 생성했다.

Node type별 현재 수량은 다음과 같다.

| node type | count | 생성 방식 요약 |
| --- | ---: | --- |
| `DomainTask` | 22 | task seed의 label/alias/keyword로 OCR sentence evidence를 찾고 canonical 업무 단위 생성 |
| `ProcedureStep` | 99 | task별 절차 template과 입력/산출물 근거를 이용해 step 생성 |
| `ReviewCheckpoint` | 41 | 검토, 확인, 점검, 승인 등 review 신호가 있는 step에서 생성 |
| `Artifact` | 14 | 제안서, RFP, 산출물, 분석자료 등 업무 input/output 객체 생성 |
| `Role` | 10 | 수행자, 담당자, 부서, PM 등 책임 주체 표현에서 생성 |
| `GuardCondition` | 13 | 조건, 기준, 충족 여부, 판단 조건 표현에서 생성 |
| `ArtifactFlow` | 9 | 산출물이 다음 업무의 입력으로 쓰이는 흐름에서 생성 |
| `Principle` | 5 | 지켜야 할 원칙, 작성 기준, 품질 기준에서 생성 |
| `DecisionGateway` | 4 | 분기, 판단, 승인 여부 등 의사결정 지점에서 생성 |
| `Risk` | 3 | 리스크, 오류 가능성, 누락 위험 표현에서 생성 |

Node 생성 원칙은 다음이다.

1. OCR sentence를 evidence anchor로 유지한다.
2. 같은 업무 표현은 alias/canonicalization으로 묶는다.
3. node type은 schema에 있는 것만 허용한다.
4. 최종 node는 최소 하나 이상의 evidence 또는 graph relation을 통해 추적 가능해야 한다.
5. 사람이 검수하기 전까지 node correctness를 최종 성능 claim으로 주장하지 않는다.

근거 파일은 `outputs/07_layer2_graph/layer2_nodes.jsonl`이다.

---

## 7. Edge는 어떻게 산출했는가

최종 Layer 2 edge는 947개이다. edge는 source node, target node, predicate, evidence anchor를 함께 가져야 accepted edge로 들어간다.

Predicate별 현재 edge 수는 다음과 같다.

| predicate | count | 의미 |
| --- | ---: | --- |
| `USES_INPUT` | 201 | task/step이 어떤 입력 자료를 사용하는가 |
| `PRODUCES` | 220 | task/step이 어떤 산출물을 생성하는가 |
| `PERFORMED_BY` | 120 | task/step의 수행자 또는 책임 주체 |
| `HAS_STEP` | 99 | task가 어떤 절차 step으로 구성되는가 |
| `PRECEDES` | 77 | step 또는 task 사이의 선후 관계 |
| `HAS_PRINCIPLE` | 64 | 업무 수행 원칙 연결 |
| `HAS_DECISION_GATEWAY` | 54 | 업무와 의사결정 지점 연결 |
| `HAS_REVIEW_CHECKPOINT` | 41 | 검토/확인/승인 지점 연결 |
| `HAS_RISK` | 39 | 업무와 위험 요소 연결 |
| `HAS_GUARD_CONDITION` | 14 | 의사결정 조건 연결 |
| `FEEDS_INTO` | 9 | 산출물이 후속 업무로 흘러가는 관계 |
| `USED_AS_INPUT_FOR` | 9 | 산출물이 다른 업무의 입력으로 쓰이는 관계 |

Edge accepted 조건은 다음이다.

1. predicate가 schema의 allowed predicate 안에 있어야 한다.
2. source node와 target node가 모두 존재해야 한다.
3. domain/range type 제약을 위반하지 않아야 한다.
4. evidence anchor가 있어야 한다.
5. 중복 SPO는 정리한다.
6. mapping edge는 자동 병합하지 않고 candidate로 둔다.

현재 구조 검증 결과는 다음이다.

| 검증 항목 | 결과 |
| --- | --- |
| schema-valid triples | 947 / 947 |
| allowed predicate violation | 0 |
| dangling edges | 0 |
| evidence-missing edges | 0 |
| accepted edge evidence rate | 1.000 |
| type violations | 0 |

근거 파일은 `outputs/07_layer2_graph/layer2_edges.jsonl`, `outputs/06_triples/triple_quality_report.md`, `outputs/07_layer2_graph/layer2_graph_quality_report.md`이다.

---

## 8. LLM은 어디에 사용되었는가

LLM은 다음 목적에 사용되었다.

| 사용 위치 | 설명 |
| --- | --- |
| baseline extraction | B0-B6 조건에서 triple/node/edge/mapping 후보 생성 |
| proposed method extraction | `P_cape_kg_actual` 조건에서 CQ/schema/evidence 기반 KG 후보 생성 |
| ablation | CQ, evidence, procedural schema, validator, standard bridge, schema retrieval 제거 조건 비교 |
| model scaling | Qwen3-8B, Qwen3-14B, Qwen3-32B-AWQ 비교 |
| silver/proxy diagnostic | human-gold 전 단계에서 출력 구조와 대략적 proxy score 진단 |

현재 완료된 model scaling diagnostic은 다음이다.

| model | 조건 | rows | 해석 |
| --- | --- | ---: | --- |
| Qwen3-8B | B0/B1/B2/P | 480 | main local diagnostic |
| Qwen3-14B | B0/B1/B2/P | 480 | stronger local diagnostic |
| Qwen3-32B-AWQ | B0/B1/B2/P | 480 | largest completed local core diagnostic |

주의할 점은 silver/proxy score가 최종 성능이 아니라는 것이다. 실제 논문 main table의 F1, precision, recall은 human-gold annotation이 돌아온 뒤 다시 계산해야 한다.

---

## 9. 현재 주장 가능한 것과 아직 주장하면 안 되는 것

| 구분 | 현재 표현 가능 | 아직 불가한 표현 |
| --- | --- | --- |
| KG 구축 | Layer 1/Layer 2 KG 구축 완료 | KG 품질이 human-gold 기준으로 우수하다는 claim |
| Evidence grounding | accepted edge 947개가 evidence anchor를 가진다 | evidence span exactness가 사람 기준으로 정확하다는 claim |
| CQ answerability | 12개 CQ가 현재 그래프 구조상 답변 가능하다 | 답변 내용이 사람 평가 기준으로 모두 correct라는 claim |
| LLM 실험 | baseline/proposed/ablation/model scaling을 120 chunks에서 실행했다 | 제안 방법론이 human-gold F1에서 우수하다는 claim |
| NCS/PCF mapping | Top-K 후보를 생성했다 | mapping candidate가 전문가 기준으로 정답이라는 claim |
| Active review | review queue와 pool design을 만들었다 | 전문가 검수 시간이 실제로 줄었다는 claim |
| Release | public-safe bundle과 handoff package를 만들었다 | 익명 제출/공개가 최종 승인되었다는 claim |

교수님께 보고할 때 안전한 핵심 문장은 다음이다.

> 자동 구축 단계는 완료되었고, 현재 산출물은 human review를 시작할 수 있는 상태까지 정리되어 있습니다. 다만 논문에서 최종 성능 우수성을 주장하려면 human-gold annotation, IAA, adjudication, mapping expert review를 완료한 뒤 main table을 다시 산출해야 합니다.

---

## 10. 다음 단계

가장 중요한 다음 단계는 추가 GPU 실험이 아니라 human-gold와 expert review이다.

| 우선순위 | 작업 | 이유 |
| --- | --- | --- |
| 1 | priority-100 chunk human annotation | 최소 논문 claim gate 충족 |
| 2 | 두 명 annotator IAA 계산 | annotation 신뢰도 확보 |
| 3 | adjudication 및 human-gold scoring | 최종 main table 산출 |
| 4 | NCS/PCF mapping expert review | mapping downstream claim 가능화 |
| 5 | NCS-PCF crosswalk expert review | standard bridge utility claim 가능화 |
| 6 | active-review effort 기록 | expert effort reduction claim 가능화 |

현재 상태를 한 줄로 정리하면 다음과 같다.

> CAPE-KG는 현재 자동 구축, LLM diagnostic, 구조 검증, 시각화, handoff/release 준비까지 완료되었고, 논문 성능 claim만 human/expert review를 기다리는 상태이다.
