# 현재까지의 CAPE-KG 실험 방법론 및 결과 정리

Generated: 2026-06-28
Updated: 2026-06-28 13:10 UTC

이 문서는 현재까지 실행한 AX/CAPE-KG 실험의 방법론, 실행 내역, 산출물, 주요 결과, 해석 가능한 범위, 남은 human gate를 한국어로 정리한 연구 기록입니다. 교수님께 현재 진행 상황을 설명하거나 질의에 답할 때 사용할 수 있도록 작성했습니다.

가장 중요한 결론은 다음과 같습니다.

> **KG 구축과 실험 인프라는 완료 단계에 도달했습니다. 그러나 human-gold annotation, IAA, adjudication, mapping expert review, active-review human-effort 수집이 아직 끝나지 않았으므로 최종 논문 성능 주장은 아직 할 수 없습니다.**

따라서 현재 결과는 세 범주로 나누어 해석해야 합니다.

| 구분 | 현재 상태 | 발표/논문에서의 사용 |
| --- | --- | --- |
| KG 구축 결과 | 완료 | 구축 규모와 산출물로 설명 가능 |
| LLM 실행 커버리지 | 완료 또는 진단 완료 | 실험이 실행되었다는 setup evidence로 사용 가능 |
| 성능 우수성 주장 | 미완료 | human-gold scoring 이후에만 주장 가능 |

---

## 1. 수정된 연구 방향

초기 방향은 한국어 수주/제안 문서에서 업무 온톨로지와 KG를 구축하는 것이었습니다. 현재는 EACL 제출 가능성을 고려하여 다음과 같이 연구 문제를 재정의했습니다.

> **한국어 장문 업무 문서에서 절차형 업무 지식을 추출하고, 각 노드/엣지/슬롯을 원문 evidence에 grounding하며, 구축된 Layer 2 업무 KG를 NCS/PCF 표준 taxonomy에 연결하는 evidence-grounded procedural KG construction task**

이 재정의의 핵심은 단순히 “도메인 KG를 만들었다”가 아니라, NLP 연구로서 다음 요소를 명시하는 것입니다.

- 원문 근거가 있는 procedural KG extraction
- competency question 기반 schema control
- evidence-span grounding과 hallucination 억제
- ontology/schema conformance validation
- NCS/PCF 표준 taxonomy bridge
- KG structural diagnostics와 structural gap worklist
- human-gold annotation 기반 정량 평가
- public benchmark adapter를 통한 외부 일반화 확인

---

## 2. CAPE-KG 방법론 요약

CAPE-KG는 **Competency-Question Anchored Procedural Evidence Grounding for Domain Knowledge Graph Construction**의 약어로 정리했습니다.

### 2.1 기존 방식과의 차이

| 항목 | 일반 LLM-only KG 추출 | 현재 CAPE-KG 방향 |
| --- | --- | --- |
| 추출 단위 | 문장 또는 paragraph의 일반 triple | 업무 task, 절차 step, 입력, 산출물, 역할, 조건 |
| 스키마 통제 | prompt에 의존 | 명시적 node/edge type, predicate, CQ 기반 schema |
| 근거 관리 | 누락되기 쉬움 | evidence anchor를 node/edge와 연결 |
| 평가 방식 | 생성 결과의 표면 비교 | edge, predicate, node, evidence, ontology, procedural, CQ 평가 |
| 표준 연결 | 별도 후처리 | NCS/PCF mapping candidate와 Layer2-bridged NCS-PCF crosswalk candidate를 실험 파이프라인에 포함 |
| 최종 검증 | 자동 결과 중심 | human-gold annotation, adjudication, expert review gate 필요 |

### 2.2 방법론 모듈 M1-M11

현재 수정된 방법론은 11개 모듈로 관리하고 있습니다. 최신 coverage 검사 결과, **M1-M11 전체 모듈에 필요한 실행 산출물이 존재합니다.**

| 모듈 | 이름 | 현재 상태 | 최종 논문 주장에 필요한 점 |
| --- | --- | --- | --- |
| M1 | Document structure recovery | 산출물 존재 | source-text release는 권리 검토 필요 |
| M2 | CQ generation and selection | 산출물 존재 | human-gold 이후 CQ score 재계산 |
| M3 | CQ-linked schema retrieval | 산출물 존재, claim pending | ablation 결과를 human-gold와 비교 |
| M4 | Procedural frame extraction | 산출물 존재, claim pending | task/step correctness 검수 |
| M5 | Evidence-span constrained triple extraction | 산출물 존재, claim pending | evidence exactness 검수 |
| M6 | Span verifier | 산출물 존재, claim pending | human-gold evidence metric 필요 |
| M7 | Ontology/SHACL validator | 산출물 존재 | final table은 human-gold 기반으로 산출 |
| M8 | Procedural consistency validator | 산출물 존재, claim pending | human-gold 이후 재계산 |
| M9 | Alias/canonicalization | 산출물 존재, claim pending | node canonicalization 검수 |
| M10 | Active review queue | 산출물 존재, claim pending | reviewer effort/outcome 필요 |
| M11 | NCS/PCF mapping evaluator | 산출물 존재, claim pending | mapping/crosswalk expert review 완료 필요 |

요약:

| 항목 | 값 |
| --- | ---: |
| 전체 방법론 모듈 | 11 |
| required artifact가 모두 있는 모듈 | 11 |
| missing required artifact | 0 |
| final claim이 human review에 의존하는 모듈 | 8 |
| claim status | all_m1_m11_artifacts_present_human_claims_pending |

---

## 3. 실제로 실행한 파이프라인

현재까지 다음 파이프라인을 실행했습니다.

1. **Layer 1 NCS/PCF 표준 KG 구축**
   - NCS 직무/능력단위 체계 구축
   - PCF 프로세스/metric 체계 구축
   - 표준 taxonomy를 Layer 2 업무 KG와 직접 병합하지 않고 mapping 대상으로 유지

2. **OCR 문서 정제 및 evidence anchor 생성**
   - OCR workbook의 row, sentence, page, chunk 추적
   - 표지, 목차, header/footer, index 등 KG 구축에 부적절한 row 제외
   - KG edge가 원문 근거로 돌아갈 수 있도록 evidence anchor 생성

3. **Layer 2 업무 절차 KG 구축**
   - DomainTask, ProcedureStep, Artifact, Role, DecisionGateway, GuardCondition, Risk 등 생성
   - USES_INPUT, PRODUCES, PERFORMED_BY, HAS_STEP, PRECEDES 등 절차형 edge 생성

4. **NCS/PCF mapping candidate 생성**
   - Layer 2 업무 task별 NCS Top-K 후보 생성
   - Layer 2 업무 task별 PCF Top-K 후보 생성
   - 같은 Layer 2 task를 공유하는 NCS 후보와 PCF 후보를 연결해 NCS-PCF crosswalk 후보 생성
   - 자동 확정하지 않고 expert review 대상으로 유지

5. **시각화 및 import 산출물 생성**
   - HTML KG viewer
   - GraphML/JSON
   - Neo4j CSV
   - Neo4j Browser용 Cypher

6. **EACL식 실험 패키지 구축**
   - 120개 evaluation chunks 선정
   - silver reference 생성
   - baseline, ablation, model scaling 실행
   - public benchmark adapter 실행
   - paper table, claim gate, release bundle 생성

7. **Human review handoff 구축**
   - annotator A/B용 priority 100 chunk 패키지 생성
   - coordinator bundle 생성
   - adjudicator bundle 생성
   - mapping expert review bundle 생성
   - active-review human-effort bundle 생성
   - 선택적 all-available 214-chunk annotation expansion scaffold 생성
   - return preflight와 human gate action plan 생성

8. **KG structural diagnostics 및 structural gap worklist 생성**
   - ontology/domain-range/evidence 조건 점검
   - procedural consistency와 structural CQ answerability 산출
   - KG를 자동 수정하지 않고, review checkpoint 후보와 gateway branch gap을 human-review worklist로 분리

9. **Pre-human validation 실행**
   - release bundle checksum 확인
   - human handoff artifact 확인
   - Neo4j CSV validation 확인
   - human gate action plan 동기화 확인

---

## 4. 입력 데이터와 OCR 처리 결과

입력 데이터:

- `handoff-hanyang/자이제_ocr_preprocessed.xlsx`

처리 결과:

| 항목 | 값 |
| --- | ---: |
| OCR clean sentence/evidence anchors | 5,009 |
| Layer 2 chunks | 214 |
| Evaluation chunks | 120 |
| Optional all-available annotation chunks | 214 |
| Optional remaining annotation chunks | 94 |
| Silver reference nodes | 169 |
| Silver reference edges | 861 |
| Silver evidence anchors | 293 |

해석:

- OCR row는 단순 텍스트로만 쓰이지 않고, KG evidence anchor의 기반으로 유지됩니다.
- 120개 evaluation chunks는 LLM baseline/ablation 및 human-gold annotation의 중심 단위입니다.
- 현재 reference는 silver/proxy 성격이므로 최종 성능 주장의 gold standard는 아닙니다.

---

## 4.1 Evidence span granularity 진단

계획서에서는 character-level evidence grounding을 중요한 차별점으로 제시했습니다. 현재 KG는 accepted triple에 sentence-level evidence anchor를 연결하고 있으며, 추가로 subject/object label이 evidence sentence 안에서 발견되는 경우 character span을 자동 산출하는 진단 산출물을 만들었습니다.

| 항목 | 값 |
| --- | ---: |
| Layer2 triples | 906 |
| Triple components | 2,718 |
| Exact component spans | 736 |
| Exact component span rate | 0.2708 |
| Subject exact span rate | 0.2395 |
| Object exact span rate | 0.5728 |
| Predicate full-sentence proxy rate | 1.0000 |

해석:

- sentence-level evidence coverage는 이미 KG에 존재합니다.
- subject/object는 lexical exact match가 가능한 경우 character-level span을 추가로 갖습니다.
- predicate evidence는 아직 token-level span이 아니라 sentence-level proxy입니다.
- 따라서 현재 산출물은 **component-level span diagnostic**이며, 최종 evidence exactness claim은 human-gold span annotation 이후에만 가능합니다.

주요 파일:

- `outputs/06_triples/layer2_triples_component_spans.jsonl`
- `experiments/cape_kg_eacl_20260627/04_evaluation/evidence_span_granularity_report.md`
- `experiments/cape_kg_eacl_20260627/04_evaluation/evidence_span_granularity_metrics.json`

---

## 5. Layer 1 표준 KG 구축 결과

Layer 1은 외부 표준 기준축입니다. 현재 NCS와 PCF를 모두 KG로 구축했습니다.

| 구분 | Nodes | Edges | 주요 구성 |
| --- | ---: | ---: | --- |
| NCS | 4,109 | 4,085 | 능력단위 3,450개 포함 |
| PCF | 5,301 | 5,288 | PCFElement 2,017개, PCFMetric 3,284개 포함 |
| 합계 | 9,410 | 9,373 | Layer 1 표준 grounding layer |

품질 점검:

- NCS endpoint missing count: 0
- NCS node ID duplicate count: 0
- PCF metric orphan count: 0
- Layer 1 gate: PASS

해석:

- Layer 1은 도메인 문서에서 직접 추출한 것이 아니라, 표준 taxonomy를 안정적 기준축으로 구축한 것입니다.
- Layer 2 업무 KG와 NCS/PCF는 직접 병합하지 않고 mapping edge 후보로 연결합니다.

---

## 6. Layer 2 업무 절차 KG 구축 결과

Layer 2는 한국어 수주/제안 업무 문서에서 구축된 업무 절차 KG입니다.

### 6.1 전체 규모

| 항목 | 값 |
| --- | ---: |
| Layer 2 nodes | 179 |
| Layer 2 edges | 906 |
| Evidence anchors | 5,009 |
| Dangling edges | 0 |
| Evidence-missing accepted edges | 0 |
| Type violations | 0 |

### 6.2 Node type 분포

| Node type | Count |
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

### 6.3 Edge predicate 분포

| Predicate | Count | 의미 |
| --- | ---: | --- |
| PRODUCES | 220 | 업무나 단계가 생성하는 산출물 |
| USES_INPUT | 201 | 업무나 단계가 사용하는 입력 |
| PERFORMED_BY | 120 | 수행자/책임자 |
| HAS_STEP | 99 | 업무의 세부 절차 |
| PRECEDES | 77 | 절차 순서 |
| HAS_PRINCIPLE | 64 | 업무 원칙 |
| HAS_DECISION_GATEWAY | 54 | 의사결정 지점 |
| HAS_RISK | 39 | 업무 리스크 |
| HAS_GUARD_CONDITION | 14 | 판단 조건 |
| FEEDS_INTO | 9 | 산출물 흐름 |
| USED_AS_INPUT_FOR | 9 | 산출물이 다음 업무 입력으로 사용됨 |

해석:

- Layer 2는 일반 entity-relation KG가 아니라 업무 수행 구조를 표현하는 procedural KG입니다.
- 특히 `PRODUCES`, `USES_INPUT`, `PERFORMED_BY`, `HAS_STEP`, `PRECEDES`가 큰 비중을 차지해 업무 실행 흐름이 중심임을 보여줍니다.
- accepted edge는 모두 evidence anchor를 가지고 있어, 결과를 원문 근거로 추적할 수 있습니다.

---

## 6.4 KG structural diagnostics와 structural gap worklist

수정된 방향에서는 KG를 만든 뒤 바로 "완성"이라고 주장하지 않고, 구조적으로 확인 가능한 항목과 사람 검수가 필요한 항목을 분리했습니다.

### 6.4.1 구조 진단 결과

| 항목 | 값 | 해석 |
| --- | ---: | --- |
| Ontology conformance rate | 1.0000 | unknown node/edge type, dangling edge, domain-range violation 없음 |
| Domain/range violations | 0 | schema상 허용되지 않은 source-target 조합 없음 |
| Evidence-missing accepted edges | 0 | accepted edge는 evidence anchor 보유 |
| Procedural consistency rate | 0.9950 | precedence cycle 없음, gateway branch warning만 존재 |
| Precedence cycles | 0 | 절차 순환 오류 없음 |
| Gateway without branch | 4 | guard condition은 있으나 explicit branch edge가 없는 gateway |
| Structural CQ answerability | 0.9167 | 12개 CQ 중 11개가 구조적으로 answerable |

해석:

- 현재 KG는 ontology와 evidence grounding 측면에서 구조 오류가 발견되지 않았습니다.
- 다만 decision gateway의 branch 구조와 review checkpoint 타입 표현은 사람이 확인해야 합니다.
- 따라서 구조 진단은 final human-gold 성능표가 아니라, KG 품질과 보강 지점을 보여주는 diagnostic입니다.

### 6.4.2 Structural gap worklist

자동으로 KG를 고치지 않고, 다음 두 종류의 검수 worklist를 만들었습니다.

| Worklist | 값 | 의미 |
| --- | ---: | --- |
| Review checkpoint candidates | 45 | 현재 `DomainTask` 또는 `ProcedureStep`으로 표현된 리뷰/점검 개념 중 `ReviewCheckpoint` 승격 후보 |
| Gateway branch gaps | 4 | `HAS_GUARD_CONDITION`은 있으나 명시적 branch target이 없는 `DecisionGateway` |

주요 gateway branch gap:

| Gateway | Guard 수 | Incoming task 수 |
| --- | ---: | ---: |
| `L2_DG_DG_APPROVAL` | 9 | 22 |
| `L2_DG_DG_BID_NO_BID` | 3 | 8 |
| `L2_DG_DG_BID_VALIDATION` | 1 | 17 |
| `L2_DG_DG_PURSUIT` | 1 | 7 |

해석:

- 이 worklist는 현재 14개 human return file 구조를 바꾸지 않습니다. 14개는 minimum paper-gate 반환 11개와 optional/strong 반환 3개(mapping, crosswalk, active-effort)를 합친 전체 추적 대상입니다.
- 다만 다음 human review에서 KG 구조를 더 정교하게 만들기 위한 별도 검토 항목입니다.
- 교수님께는 "구조 진단 결과를 숨기지 않고, KG 보강 후보를 명시적으로 분리했다"고 설명하는 것이 적절합니다.

주요 파일:

- `experiments/cape_kg_eacl_20260627/04_evaluation/structural_evaluation_metrics.json`
- `experiments/cape_kg_eacl_20260627/04_evaluation/structural_evaluation_report.md`
- `experiments/cape_kg_eacl_20260627/04_evaluation/structural_gap_worklist_summary.json`
- `experiments/cape_kg_eacl_20260627/04_evaluation/structural_gap_worklist_report.md`
- `experiments/cape_kg_eacl_20260627/05_review/structural_review_checkpoint_candidates.csv`
- `experiments/cape_kg_eacl_20260627/05_review/structural_gateway_branch_gaps.csv`

---

## 7. NCS/PCF mapping candidate 결과

Layer 2 업무 task를 Layer 1 표준 체계에 연결하기 위해 mapping candidate를 생성했습니다.

| 항목 | 값 |
| --- | ---: |
| NCS mapping candidates | 110 |
| PCF mapping candidates | 110 |
| 전체 mapping review rows | 220 |
| NCS source task groups | 22 |
| PCF source task groups | 22 |
| Shared Layer2 tasks for crosswalk | 22 |
| NCS-PCF all crosswalk pairs | 550 |
| NCS-PCF top crosswalk candidates | 220 |
| Expert-reviewed rows | 0 |
| Pending rows | 220 |

해석:

- 현재 mapping은 자동 확정 결과가 아니라 **expert review 대상 후보**입니다.
- NCS-PCF crosswalk도 Layer2 bridge로 생성한 **candidate**이며, gold crosswalk label이 아닙니다.
- Hit@K, P@5, MRR, nDCG@10, explanation quality, crosswalk accept-rate 같은 downstream 성능은 expert review 완료 후에만 주장할 수 있습니다.
- 현재 mapping gate status는 `pending_expert_review`입니다.

---

## 8. Neo4j 및 시각화 산출물

Neo4j import용 flat CSV와 Cypher를 생성했고 CSV validation을 통과했습니다.

| 항목 | 값 |
| --- | ---: |
| Neo4j import nodes | 9,589 |
| Neo4j import relationships | 10,499 |
| CSV files | 17 |
| CSV total rows | 20,088 |
| Missing endpoint count | 0 |
| CSV validation status | PASS |

주요 파일:

- `outputs/09_visualization/kg_viewer.html`
- `outputs/11_neo4j_import_flat/nodes.csv`
- `outputs/11_neo4j_import_flat/neo4j_import_http_8765.cypher`
- `outputs/11_neo4j_import_flat/neo4j_csv_validation_report.json`

해석:

- KG를 Neo4j Browser에서 조회할 수 있는 CSV/Cypher 경로가 준비되어 있습니다.
- 이전 Neo4j CSV quote 오류를 피하기 위해 flat import CSV와 HTTP-served Cypher 방식을 사용할 수 있습니다.

---

## 9. LLM을 사용한 부분

LLM은 사용했습니다. 다만 현재 최종 논문 성능 주장은 LLM 결과만으로 하지 않고, human-gold scoring 이후로 유보합니다.

### 9.1 사용한 모델과 목적

| 모델 | 실행 목적 | 현재 해석 |
| --- | --- | --- |
| Qwen3-8B | baseline, ablation, strict JSON diagnostics | full 120 chunk 조건 다수 실행 |
| Qwen3-14B | stronger local diagnostic core run | B0/B1/B2/P 120 chunk 실행 |
| Qwen3-32B-AWQ | 더 큰 모델의 현실적 full core run | B0/B1/B2/P 120 chunk 실행 완료 |
| Llama-2-13B-chat | compatibility smoke run | 10 chunk smoke 성격 |

### 9.2 Qwen3 model scaling core run

아래 수치는 생성 커버리지와 silver/proxy 진단용입니다. human-gold 성능표가 아닙니다.

| 모델 | 조건 | Rows | 생성 결과 요약 |
| --- | --- | ---: | --- |
| Qwen3-8B | B0_plain_llm | 120 | triples 837 |
| Qwen3-8B | B1_predicate_constrained | 120 | edges 663 |
| Qwen3-8B | B2_current_project | 120 | nodes 712, edges 82 |
| Qwen3-8B | P_cape_kg_actual | 120 | nodes 549, edges 275, mappings 52 |
| Qwen3-14B | B0_plain_llm | 120 | triples 892 |
| Qwen3-14B | B1_predicate_constrained | 120 | edges 641 |
| Qwen3-14B | B2_current_project | 120 | nodes 723, edges 60 |
| Qwen3-14B | P_cape_kg_actual | 120 | nodes 574, edges 332, mappings 10 |
| Qwen3-32B-AWQ | B0_plain_llm | 120 | triples 897 |
| Qwen3-32B-AWQ | B1_predicate_constrained | 120 | edges 585 |
| Qwen3-32B-AWQ | B2_current_project | 120 | nodes 719, edges 56 |
| Qwen3-32B-AWQ | P_cape_kg_actual | 120 | nodes 585, edges 360, mappings 5 |

### 9.3 Qwen3-32B-AWQ silver/proxy diagnostic

| 조건 | Edge F1 | Predicate F1 | Node F1 | Evidence F1 | 주의 |
| --- | ---: | ---: | ---: | ---: | --- |
| B0_plain_llm | 0.0000 | 0.0000 | 0.0377 | 0.0273 | silver/proxy |
| B1_predicate_constrained | 0.0016 | 0.1161 | 0.0000 | 0.0224 | silver/proxy |
| B2_current_project | 0.0000 | 0.0099 | 0.0194 | 0.0387 | silver/proxy |
| P_cape_kg_actual | 0.0034 | 0.0662 | 0.0284 | 0.0542 | silver/proxy |

해석:

- 더 큰 모델을 사용해도 현재 silver/proxy 기준에서 곧바로 좋은 final score가 나온다고 말할 수는 없습니다.
- 이 결과는 prompt/schema/parse recovery/평가 스크립트의 동작을 확인하는 진단 자료입니다.
- 최종 성능 비교는 adjudicated human-gold label에 대해 다시 계산해야 합니다.

---

## 10. Baseline, ablation, public benchmark

### 10.1 Baseline 및 ablation coverage

현재 full 120 chunk 기준으로 실행된 주요 조건은 다음과 같습니다.

| 구분 | 조건 |
| --- | --- |
| Baseline | B0_plain_llm, B1_predicate_constrained, B2_current_project, B3_edc_style, B4_taxonomy_rag, B5_procedural_prompt, B6_sac_kg_verifier_pruner |
| Proposed | P_cape_kg_actual |
| Ablation | P_minus_CQ, P_minus_Evidence, P_minus_Procedural_schema, P_minus_Schema_retrieval, P_minus_Standard_bridge, P_minus_Validator, P_minus_Active_review diagnostic |

Claim gate 기준:

- Baselines generated: PASS
- Proposed generation: PASS
- Ablations generated: PASS
- Proposed human-gold score: FAIL, human-gold 미완료 때문

### 10.2 Active-review ablation diagnostic

계획서의 `P - Active review` ablation을 명시적으로 추적하기 위해 active-priority queue와 active review 제거 조건을 비교하는 silver/proxy 진단표를 추가했습니다.

| Condition | Strategy | Budget | High-impact errors | Precision@k | Lift | 상태 |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| P_cape_kg_actual_with_active_review | active_priority | 25 | 16 | 0.6400 | 1.0173 | silver/proxy |
| P_minus_Active_review_random_expected | random_expected | 25 | 15.7273 | 0.6291 | 1.0000 | silver/proxy |
| P_minus_Active_review_uncertainty_only | uncertainty_only | 25 | 15 | 0.6000 | 0.9538 | silver/proxy |
| P_cape_kg_actual_with_active_review | active_priority | 55 | 36 | 0.6545 | 1.0405 | silver/proxy |
| P_minus_Active_review_random_expected | random_expected | 55 | 34.6000 | 0.6291 | 1.0000 | silver/proxy |

해석:

- 이 결과는 active review 효율의 최종 증거가 아니라 계획서상 ablation scaffold입니다.
- 최종 efficiency claim은 adjudicated human label과 active-review human-effort reviewed CSV가 들어온 뒤 다시 계산해야 합니다.

### 10.3 Public benchmark adapter

외부 일반화 진단을 위해 PAGED/Text2KG 계열 public subset 평가도 실행했습니다.

| Run | PAGED n | PAGED edge F1 | Text2KG n | Relation F1 | Triple F1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Qwen3-8B full adapter | 100 | 0.4233 | 200 | 0.6015 | 0.1736 |
| Qwen3-14B subset | 10 | 0.1446 | 20 | 0.2817 | 0.0200 |
| Qwen3-8B subset | 10 | 0.1794 | 20 | 0.4500 | 0.0500 |

해석:

- 이 결과는 내부 한국어 업무 문서의 main result가 아니라, public benchmark에 대한 auxiliary evidence입니다.
- EACL 제출 시 “내부 데이터만의 사례”라는 약점을 줄이는 보조 자료로 사용할 수 있습니다.

---

## 11. Claimable main table 상태

현재 main table은 최종 성능표가 아니라 **claimable main table**입니다. 즉, 어떤 결과를 논문 주장으로 사용할 수 있고 어떤 결과는 아직 보류해야 하는지를 구분하는 표입니다.

| 결과 | 현재 상태 | 해석 |
| --- | --- | --- |
| Core extraction main result | pending_human | human-gold F1 미계산 |
| Actual LLM run coverage | claimable_setup | B0/B1/B2/P 120 rows와 ablation 실행 사실은 주장 가능 |
| Optional annotation expansion | claimable_setup | all_available=214, remaining_optional=94, strong_300_gap=86 |
| CAPE-KG silver diagnostic | diagnostic_only | 디버깅/동기 부여용, 논문 성능 주장 불가 |
| KG structural diagnostics | diagnostic_only | ontology conformance, procedural consistency, CQ answerability의 KG 구조 진단 |
| Structural gap worklist | claimable_setup | review checkpoint 후보 45개, gateway branch gap 4개를 검수 항목으로 분리 |
| Public benchmark adapter | auxiliary_claimable | 보조 일반화 evidence로 사용 가능 |
| NCS/PCF mapping downstream | pending_expert_review | expert review 후 Hit@K/P@5/MRR/nDCG@10/explanation quality/crosswalk accept-rate 주장 가능 |
| Active-review ablation | diagnostic_only | P-minus-active-review scaffold, human-effort 전 성능 주장 불가 |
| Release/reproducibility package | claimable_setup | 재현 패키지 준비 사실은 주장 가능 |
| Submission claim gate | not_ready | human-gold 미완료로 FAIL |

핵심 메시지:

- “현재 main table이 있느냐?”에 대한 답은 **있지만, final performance table이 아니라 claimability table**입니다.
- final main table은 human-gold annotation과 expert review 후 생성해야 합니다.

---

## 12. Human gate action plan

현재 실험은 사람 검수 단계로 넘길 수 있도록 handoff 구조가 준비되어 있습니다.

### 12.1 현재 gate 상태

| 항목 | 상태 |
| --- | --- |
| Submission readiness | pending_human_gold_iaa_and_human_gold_scoring |
| Claim gate overall status | FAIL |
| Return preflight status | pending_human_returns |
| Human gate action plan | human_gate_action_plan_ready_pending_returns |
| Pre-human handoff validation | PASS |

### 12.2 남은 blocking items

| Blocking item | 요구사항 | 현재 |
| --- | --- | --- |
| min.gold_chunks | 100+ adjudicated chunks | 0 |
| min.gold_items | 500+ adjudicated node/edge/evidence items | 0 |
| min.iaa | 100+ paired chunks로 IAA 계산 | 0 |
| min.proposed | P_cape_kg_actual human-gold scoring | 미완료 |

### 12.3 반환받아야 하는 human review 파일

| 구분 | 필요 파일 수 | 현재 present |
| --- | ---: | ---: |
| Annotator A/B reviewed batch files | 10 | 0 |
| Adjudication reviewed file | 1 | 0 |
| Mapping expert reviewed file | 1 | 0 |
| NCS-PCF crosswalk expert reviewed file | 1 | 0 |
| Active-review human-effort reviewed CSV | 1 | 0 |
| 합계 | 14 | 0 |

### 12.4 Optional annotation expansion

현재 claim gate에 필요한 필수 human return 구조는 그대로 유지하면서, 더 강한 full-paper claim을 준비할 수 있도록 선택적 검수 확장 패키지를 추가했습니다.

| 항목 | 값 |
| --- | ---: |
| Current corpus Layer2 chunks | 214 |
| Required full package chunks | 120 |
| Optional remaining chunks | 94 |
| All-available expansion package chunks | 214 |
| Strong 300-chunk target gap | 86 |
| Current required return file 변화 | 0 |

해석:

- 최소 제출 경로는 기존 full120/adjudication 중심 human gate입니다.
- `all_available_214`는 현재 corpus 전체를 검수하고 싶을 때 쓰는 선택 패키지입니다.
- `remaining_94_text_only`는 기존 120개에 포함되지 않은 나머지 chunk입니다.
- 300-500 chunk 수준의 강한 claim은 현재 corpus만으로는 불가능하며, source 추가 또는 chunk 재분할이 필요합니다.
- 이 확장 패키지는 아직 human-gold가 아니므로 성능 주장에는 사용하지 않습니다.

추가 진행 순서:

1. Annotator A/B가 priority 100 chunk를 독립 검수
2. `.reviewed.jsonl` 10개 반환
3. return preflight로 파일 구조 검증
4. A/B annotation import
5. IAA 계산
6. adjudicator가 `adjudication_edited.jsonl` 반환
7. adjudication import 및 human-gold metric 계산
8. mapping expert `.reviewed.jsonl` 반환
9. active-review human-effort `.reviewed.csv` 반환
10. mapping Hit@K, P@5, MRR 계산
11. claim gate 재실행

---

## 13. Release bundle 및 검증 결과

최신 post-annotation refresh와 pre-human validation을 실행했습니다.

### 13.1 Pre-human validation

| 항목 | 값 |
| --- | --- |
| Overall status | PASS |
| Claim status | pre_human_handoff_ready_not_submission_complete |
| Check count | 21 |
| PASS | 20 |
| WARN | 1 |
| FAIL | 0 |

WARN 1개는 예상된 상태입니다.

- Human gold, IAA, adjudication, human-gold scoring이 아직 완료되지 않았음을 알리는 경고입니다.
- 이 WARN은 자동 산출물 오류가 아니라 논문 성능 claim을 보류해야 한다는 표시입니다.

### 13.2 Release bundle checksum

| Bundle | SHA256 |
| --- | --- |
| Internal repro | `250a70c7ddb003cf16adeb7b55ecdca722b38b9024d07c42add96b6ea00d9e3f` |
| Public-safe skeleton | `ec76c3a4d1a20bd7d8539eb980ef23467f92e91717ef9014ec2ae7bf90f270b9` |

검증:

- `sha256sum -c experiments/cape_kg_eacl_20260627/06_release/release_bundle_checksums.sha256`: OK
- public-safe tar content scan: PASS
- source text와 internal review handoff 파일은 public-safe bundle에서 제외됨

---

## 14. 주요 산출물 위치

### 14.1 KG 구축 산출물

| 산출물 | 경로 |
| --- | --- |
| Layer 2 nodes | `outputs/07_layer2_graph/layer2_nodes.jsonl` |
| Layer 2 edges | `outputs/07_layer2_graph/layer2_edges.jsonl` |
| NCS mapping candidates | `outputs/08_mapping/l2_ncs_mapping_candidates.jsonl` |
| PCF mapping candidates | `outputs/08_mapping/l2_pcf_mapping_candidates.jsonl` |
| NCS-PCF crosswalk candidates | `outputs/08_mapping/l2_ncs_pcf_crosswalk_candidates.jsonl` |
| Component evidence spans | `outputs/06_triples/layer2_triples_component_spans.jsonl` |
| Evidence span granularity report | `experiments/cape_kg_eacl_20260627/04_evaluation/evidence_span_granularity_report.md` |
| Structural evaluation report | `experiments/cape_kg_eacl_20260627/04_evaluation/structural_evaluation_report.md` |
| Structural gap worklist report | `experiments/cape_kg_eacl_20260627/04_evaluation/structural_gap_worklist_report.md` |
| Structural review checkpoint candidates | `experiments/cape_kg_eacl_20260627/05_review/structural_review_checkpoint_candidates.csv` |
| Structural gateway branch gaps | `experiments/cape_kg_eacl_20260627/05_review/structural_gateway_branch_gaps.csv` |
| NCS-PCF crosswalk report | `experiments/cape_kg_eacl_20260627/04_evaluation/ncs_pcf_crosswalk_report.md` |
| Active-review ablation report | `experiments/cape_kg_eacl_20260627/04_evaluation/active_review_ablation_report.md` |
| KG viewer | `outputs/09_visualization/kg_viewer.html` |
| Final build report | `outputs/10_evaluation/final_build_report.md` |

### 14.2 Neo4j 산출물

| 산출물 | 경로 |
| --- | --- |
| Flat Neo4j nodes CSV | `outputs/11_neo4j_import_flat/nodes.csv` |
| Flat Neo4j Cypher | `outputs/11_neo4j_import_flat/neo4j_import_http_8765.cypher` |
| CSV validation report | `outputs/11_neo4j_import_flat/neo4j_csv_validation_report.json` |

### 14.3 EACL 실험 산출물

| 산출물 | 경로 |
| --- | --- |
| Final EACL experiment report | `experiments/cape_kg_eacl_20260627/07_reports/final_eacl_experiment_report.md` |
| Paper tables | `experiments/cape_kg_eacl_20260627/06_release/paper_tables.md` |
| Claimable main table | `experiments/cape_kg_eacl_20260627/06_release/claimable_main_table.md` |
| Submission readiness audit | `experiments/cape_kg_eacl_20260627/06_release/submission_readiness_audit.md` |
| Submission completion audit | `experiments/cape_kg_eacl_20260627/06_release/submission_completion_audit_ko.md` |
| Claim gate report | `experiments/cape_kg_eacl_20260627/06_release/claim_gate_report.md` |
| Method module coverage | `experiments/cape_kg_eacl_20260627/06_release/method_module_coverage.md` |
| Pre-human validation | `experiments/cape_kg_eacl_20260627/06_release/pre_human_handoff_validation.md` |

### 14.4 Human review 산출물

| 산출물 | 경로 |
| --- | --- |
| Human gate action plan | `experiments/cape_kg_eacl_20260627/06_release/human_gate_action_plan.md` |
| Required returns CSV | `experiments/cape_kg_eacl_20260627/05_review/human_gate_required_returns.csv` |
| Human handoff report | `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/human_review_handoff_report.md` |
| Annotator A bundle | `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_human_gold_annotator_A_priority100.tar.gz` |
| Annotator B bundle | `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_human_gold_annotator_B_priority100.tar.gz` |
| Coordinator bundle | `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_human_gold_coordinator_priority100.tar.gz` |
| Adjudicator bundle | `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_human_gold_adjudicator_full120.tar.gz` |
| Mapping expert bundle | `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_mapping_expert_review_top20_groups.tar.gz` |
| Active-review effort bundle | `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_active_review_human_effort.tar.gz` |
| Optional annotation expansion report | `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/annotation_expansion_report.md` |
| Optional all-available 214 package | `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/all_available_214/` |
| Optional remaining 94 package | `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/remaining_94_text_only/` |

---

## 15. 지금까지 무엇을 실행했는가

실행 내역은 다음과 같이 요약할 수 있습니다.

| 단계 | 실행 내용 | 결과 |
| --- | --- | --- |
| KG build | Layer 1 NCS/PCF, OCR, Layer 2 KG, mapping candidate 생성 | PASS |
| Visualization | HTML viewer, GraphML, JSON, Neo4j CSV 생성 | PASS |
| Neo4j validation | flat CSV parser/endpoint/JSON carrier 점검 | PASS |
| CAPE experiment package | 120 evaluation chunks, silver reference, schema, prompts 생성 | PASS |
| LLM baselines | Qwen3-8B baseline/ablation, Qwen3-14B core, Qwen3-32B-AWQ core | 실행 완료 |
| Public benchmark | PAGED/Text2KG adapter 평가 | 실행 완료 |
| Structural diagnostics | ontology/procedural/CQ 구조 진단 및 structural gap worklist 생성 | 생성 완료 |
| Paper tables | paper table, claimable main table 생성 | 생성 완료 |
| Submission completion audit | 계획서 요구사항별 완료 여부와 다음 명령 정리 | 생성 완료 |
| Claim gate | 제출 주장 가능성 점검 | FAIL, human-gold 미완료 때문 |
| Human handoff | annotator/coordinator/adjudicator/mapping/active-effort bundle 생성 | 준비 완료 |
| Optional annotation expansion | all-available 214, remaining 94 scaffold 생성 | 준비 완료 |
| Human gate action plan | 반환 필요 파일과 다음 명령 정리 | 생성 완료 |
| Pre-human validation | handoff/release/Neo4j/action plan 통합 검증 | PASS; current check count: see `../06_release/pre_human_handoff_validation.md` |

최근 실행한 refresh 명령:

```bash
PYTHON_BIN=/home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python \
LLM_PYTHON=/home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python \
APPLY_IMPORTS=0 \
bash scripts/run_cape_post_annotation_refresh.sh
```

검증 명령:

```bash
sha256sum -c experiments/cape_kg_eacl_20260627/06_release/release_bundle_checksums.sha256
```

---

## 16. 현재 상태를 한 문장으로 말하면

현재 연구는 다음과 같이 말하는 것이 가장 정확합니다.

> **한국어 수주/제안 문서에서 evidence-grounded procedural KG를 구축하고, NCS/PCF 표준 bridge, LLM baseline/ablation, public benchmark adapter, human review handoff까지 갖춘 상태입니다. 다만 논문에서 성능 우수성을 주장하기 위한 human-gold annotation, IAA, adjudication, mapping expert review, NCS-PCF crosswalk expert review, active-review human-effort 수집은 아직 남아 있습니다.**

교수님께 발표할 때 피해야 할 표현:

- “최종 성능이 좋게 나왔다.”
- “CAPE-KG가 baseline보다 우수하다고 입증됐다.”
- “main table이 완성됐다.”
- “mapping 성능이 검증됐다.”

교수님께 말해도 되는 표현:

- “KG 구축 결과는 완료되었고 evidence가 연결되어 있습니다.”
- “LLM baseline과 ablation 실행 커버리지는 확보했습니다.”
- “현재 main table은 final performance table이 아니라 claimability table입니다.”
- “human-gold 검수 후 최종 성능표를 만들 수 있는 인프라는 준비되었습니다.”
- “NCS/PCF mapping 후보와 Layer2 bridge 기반 NCS-PCF crosswalk 후보는 생성되었고 expert review를 기다리고 있습니다.”

---

## 17. 다음 단계

가장 중요한 다음 단계는 자동 실험이 아니라 **사람 검수**입니다.

1. Annotator A/B에게 priority 100 chunk bundle 전달
2. A/B `.reviewed.jsonl` 10개 회수
3. adjudicator `adjudication_edited.jsonl` 1개 회수
4. mapping expert `.reviewed.jsonl` 1개 회수
5. NCS-PCF crosswalk `.reviewed.jsonl` 1개 회수
6. active-review human-effort `.reviewed.csv` 1개 회수
7. structural gap worklist에서 review checkpoint 후보와 gateway branch gap 검토
8. return preflight 실행
9. `APPLY_IMPORTS=1 bash scripts/run_cape_post_annotation_refresh.sh` 실행
10. IAA, adjudication, human-gold scoring 재계산
11. mapping Hit@K/P@5/MRR/nDCG@10/explanation quality 및 crosswalk accept-rate 재계산
12. claim gate 재실행
13. final main table 생성
14. 논문 초안의 실험 결과 섹션 갱신

이 단계가 끝나야 “성능 결과”를 교수님께 최종적으로 보고하고 논문 main table로 사용할 수 있습니다.
