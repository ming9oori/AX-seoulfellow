# 자이제 R5-CRSI-V 최종 실험 보고서

## 1. 결론

- 최종 판정: **`DETERMINISTIC_CRSI_ONLY_PASS`**
- 채택 그래프: **`R5-B1 Deterministic CRSI`**
- 의미: 명시적 alias, 문자열 정규화, 타입 충돌 방지, 제한된 관계 registry만 사용한 결정적 방법은 안전성 Gate를 통과했다. 선택적 LLM B2는 품질 수치는 늘렸지만 비용 Gate를 통과하지 못해 canonical graph에는 포함하지 않았다.
- 결과물 명칭: **Evidence-grounded Canonical Work Ontology for Proposal/Capture Management v0.2**
- 주장 범위: provenance·제약·구조·CQ·재현성을 검증한 **engineering-validated ontology**이다. 인간 전문가 Gold에 대한 전체 의미 정확도는 아직 검증하지 않았다.

## 2. 무엇을 실험했는가

R4-B1의 근거 보존 그래프에서 같은 개념을 가리키는 표면어를 묶고, 파편화된 관계를 고정 schema로 정리하는 실험이다. LLM이 온톨로지를 마음대로 만드는 방식과 다음 다섯 시스템을 비교했다.

| 시스템 | 방법 | operational graph 반영 방식 |
|---|---|---|
| R5-B0 | 모든 표면어를 별도 노드로 유지 | baseline |
| R5-B1 | 명시 alias·NFKC/casefold·타입·동일 Evidence·관계 registry | 결정적 gate를 통과한 것만 반영 |
| R5-B2 | B1 + 영향도 상위 gray 후보에 닫힌 선택형 LLM | `SAME_CONCEPT`/등록 관계여도 제약 재검사 |
| R5-B3 | B1 + 모든 gray 후보에 동일 LLM | 전수 LLM 비교용, canonical 불가 |
| R5-B4 | 같은 원문에서 LLM이 직접 개념·관계를 추출 | baseline; 형식 adapter 외 의미 보정 없음 |

## 3. 데이터와 누출 통제

- 사용자 지정 Excel: `handoff-hanyang/수주제안/자이제_1.xlsx`
- 레코드 수: 1,366개. 기존 R4 원본과 바이너리 해시는 달랐지만 워크시트·행 번호·전체 논리 텍스트는 완전히 동일했다.
- DEV: 기존에 노출된 120건. 방법·예산 선택에만 사용했다.
- fresh VALIDATION: 목표 80건이었으나 R1~R4 노출 그룹을 제외하면 **8건·7개 leakage group**만 남았다. 설계서의 부족 규칙에 따라 API 전에 8건 전수를 잠갔다.
- TEST 접근: 0건. INDUCTION 또는 TEST로 부족분을 채우지 않았다.

따라서 confirmatory 결과는 독립성은 지켰지만 표본이 매우 작다. alias recall 1/1의 Wilson 95% CI는 `[0.206543, 1]`로 넓으며, 정밀한 모집단 성능 추정으로 해석할 수 없다.

## 4. 개념 정규화 방법

1. 문자열을 NFKC, casefold, 공백·구두점 규칙으로 정규화했다.
2. 원문 괄호형 alias, 같은 정규형의 명시 alias, 동일 타입 exact match만 hard-positive로 취급했다.
3. WorkUnit–Metric, Template–TemplateField, Actor–Artifact 등 타입 충돌은 hard-negative로 잠갔다.
4. hard merge만 union-find에 넣었다. 단순 유사어·관련어는 자동 병합하지 않았다.
5. 각 canonical concept에 원 surface Mention, MergeActivity, Anchor를 연결해 병합 이유를 역추적할 수 있게 했다.
6. preferred label은 근거가 있는 한국어 표면형을 우선하고 짧은 형식을 선택했다.

DEV에서 hard-positive 34건, hard-negative 4,205건, gray 105건을 만들었다. B1은 명시 alias 32/32를 회수했고 위험 병합 0, 병합 provenance 1.00, 재실행 안정성 1.00이었다.

## 5. 관계 스키마 방법

허용 관계를 `HAS_DEFINITION`, `HAS_ALIAS`, `HAS_INPUT`, `PRODUCES_OUTPUT`, `PERFORMED_BY`, `PRECEDES`, `HAS_CONDITION`, `HAS_EXCEPTION`, `HAS_QUANTITY_CONSTRAINT`, `USES_TEMPLATE`, `HAS_FIELD`, `ILLUSTRATES`, `ADDRESSES_ISSUE`, `SUPPORTS_DECISION`, `PART_OF`, `BROADER`로 잠갔다.

- 명시 순서만 `PRECEDES`로 승격했다.
- 같은 Anchor의 명시 cue·수량만 조건/수량 관계 후보로 사용했다.
- 템플릿 cue와 같은 Evidence의 표 구조만 `HAS_FIELD`로 연결했다.
- 신규 관계명은 자동 생성·승격하지 않았다.
- broader, part-of, procedure를 서로 다른 관계로 유지하고 cycle·동시 부여를 금지했다.

전체 시연 그래프의 registry 관계 Evidence coverage는 1.00, domain/range 위반 0, taxonomy cycle 0이다. 다만 근거가 없어 `BROADER`, `PART_OF`, 역할·입출력 관계는 거의 또는 전혀 승격되지 않았다. 이는 보수적 abstention 결과이지 완성된 업무 schema라는 뜻은 아니다.

## 6. LLM 비교 결과

### DEV

| 지표 | B1 | B2 | B3 | B4 |
|---|---:|---:|---:|---:|
| safe ontology yield | 88 | 104 | 128 | 140 |
| critical violation | 0 | 0 | 0 | 82 |
| unsupported label rate | 0.000 | 0.000 | 0.000 | 0.121 |

- LLM 반복 일치도: 21/21 = **1.00**
- B2/B1 yield 증가: **18.18%**로 10% Gate 통과
- B2/B3 yield 비율: **81.25%**로 80% Gate 통과
- B2/B3 token 비율: **55.27%**로 35% Gate 실패
- B4: critical domain/range 위반 82건, unsupported label 58건(12.08%)

따라서 LLM 판정 자체는 안정적이었지만, B3의 80% 수준을 얻는 데 후보 40%와 토큰 55.3%가 필요했다. 비용 대비 품질 가설 H5-C는 지지되지 않았다.

### fresh VALIDATION 8건

- gray 후보가 0건이어서 B1=B2=B3이며 selective LLM 효용은 **확인 단계에서 측정 불가**이다.
- B1: critical 0, provenance 1.00, alias 1/1.
- B4: critical 2, unsupported label 6건(19.35%).
- 따라서 직접 LLM보다 보수적 B1이 안전하다는 H5-D는 통과했지만, 작은 표본 한계를 가진다.

## 7. CQ 해석

초기 단순 존재 기반 CQ는 fresh 표본에 규칙·템플릿·절차가 없다는 이유로 B1이 0.60이었다. 설계서 16.6은 불가능한 CQ에 대한 올바른 abstention도 평가하도록 규정하므로, source reference에 해당 사실이 없고 시스템도 답하지 않은 경우를 `CORRECT_ABSTENTION`으로 별도 계산했다.

- B1 abstention-aware answerability: **1.00**
- B4 abstention-aware answerability: **0.67**
- B1 provenance precision: 1.00, unsupported answer rate: 0

두 지표를 모두 보존했으며 초기 0.60을 덮어쓰지 않았다. H5-E 판정은 사전 명시된 correct-abstention 정의를 적용했지만, n=8이라는 한계 때문에 후속 독립 표본에서 재검증해야 한다.

## 8. 최종 그래프와 Neo4j

전체 INDUCTION+VALIDATION 953건은 성능 평가가 아닌 시연용으로 재구축했다.

| 항목 | 값 |
|---|---:|
| nodes | 4,767 |
| relationships | 10,738 |
| canonical concepts | 139 |
| surface mentions | 302 |
| fragmentation reduction | 204 |
| explicit aliases recovered | 166/166 |
| RDF triples | 87,023 |
| SHACL critical violations | 0 |

실제 Neo4j Community 4.4.43에 import하여 4,767개 노드와 10,738개 관계가 일치함을 확인했다. 필수 view query는 6/6 non-empty였고, Rule→Anchor 45/45, Concept→Mention 139/139, registry relation provenance 249/249였다. UID uniqueness constraint와 system/type index도 ONLINE을 확인했다.

## 9. 비용과 보안

- 실제 API logical calls: 256건
- input/output tokens: 122,486 / 32,763
- 총 tokens: 155,249
- 가격 가정 `$2/M input`, `$8/M output` 기준 상한: `$0.507076`
- Batch 50% 가정 추정: `$0.253538`
- API key: getpass TTY로만 전달, 저장 파일 0건, secret scan 0건

B2 토큰은 B3 전수 결과의 부분집합이므로 실제 총비용에서 중복 합산하지 않았다. DEV B4 2건의 첫 응답이 800 token에서 중단되어, 시스템 동결 전에 출력 한도만 1,800으로 조정한 보정 Batch 2건의 비용과 원 실패 비용을 모두 포함했다.

## 10. 현재 문제와 다음 단계

1. **확인 표본 부족**: fresh VALIDATION이 8건뿐이다. 새 leakage group 80건 이상을 별도 구축해야 한다.
2. **인간 Gold 부재**: 구조적 안전성은 검증했지만 `같은 개념인가`, `관계가 의미상 맞는가`를 전문가가 전수 검증하지 않았다.
3. **R4 표면 추출 오염 계승**: 일부 Concept/TemplateField label은 규칙 추출 경계가 길거나 부정확하다. R5는 근거 없는 재명명을 금지했기 때문에 이를 자동 수정하지 않았다.
4. **schema coverage 제한**: 역할, 입력·산출물, taxonomy·partonomy는 명시 근거가 부족해 비어 있다. 그래프가 안전하다는 것과 업무 온톨로지가 완전하다는 것은 다르다.
5. **LLM 비용 효율 실패**: B2가 품질은 늘렸지만 토큰 Gate를 넘었다. 다음 실험은 호출량 확대가 아니라 candidate blocking과 impact score 개선이 우선이다.
6. **후속 human audit**: gray pair와 B4 위반 사례 20~40건을 전문가가 판정해 의미 정확도와 LF 재사용성을 검증해야 한다.

## 11. Gate 요약

| Gate | 결과 | 핵심 근거 |
|---|---|---|
| H5-A 결정적 개념 정규화 | PASS | alias recall 1.00, 위험 병합 0, provenance 1.00 |
| H5-B 관계 schema | PASS | evidence 1.00, domain/range 0, cycle 0 |
| H5-C 선택적 LLM 효용 | **FAIL** | token ratio 55.25% > 35% |
| H5-D Direct-LLM 대비 안전성 | PASS | B1 critical 0 vs B4 2, unsupported 0 vs 19.35% |
| H5-E CQ 활용성 | PASS_WITH_SMALL_N_CAVEAT | abstention-aware 0.80 이상, 초기 presence-only 0.60 병기 |
| H5-F Neo4j readiness | PASS | coverage 1.00, 6/6 views, trace 1.00 |

최종적으로 **결정적 CRSI만 operational canonical graph로 채택**한다. B2/B3/B4 결과는 비교·진단 계층에만 남긴다.
