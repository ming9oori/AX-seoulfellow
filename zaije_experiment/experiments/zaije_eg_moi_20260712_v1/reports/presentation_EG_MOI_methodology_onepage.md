---
marp: true
paginate: false
size: 16:9
title: EG-MOI 전체 방법론 1페이지 요약
style: |
  section { font-family: "Noto Sans KR", sans-serif; padding: 38px 50px; color: #172033; font-size: 20px; }
  h1 { color: #173B57; font-size: 36px; margin: 0 0 18px; }
  h2 { color: #245B78; font-size: 23px; margin: 12px 0 8px; }
  strong { color: #9B3D32; }
  table { font-size: 17px; margin: 8px 0; }
  th { background: #E8F0F5; }
  code { font-size: 0.9em; }
  blockquote { border-left: 5px solid #D69B42; background: #FFF8E8; padding: 5px 14px; margin: 10px 0; }
---

# EG-MOI: 자이제 문서에서 근거 있는 KG를 만드는 전체 방법

**핵심 생각:** 최소 분류 틀만 먼저 두고, 실제 개념은 데이터에서 찾으며, 원문 근거를 확인할 수 있는 관계만 그래프로 승격한다.

| 1. 최소 틀 | 2. 원문 보존 | 3. 표현 발견 | 4. 개념 통합 |
|---|---|---|---|
| `업무·수행자·자료·조건·수치`와 연결 종류만 사전 정의 | Excel 1행을 `EvidenceUnit`으로 보존하고 `Anchor`와 표 문맥으로 분리 | **Mention**(개별 표현)과 **SemanticFrame**(주체·행위·대상 구조) 추출 | 같은 표현·한영 병기·약어를 `ConceptCluster`로 통합 |

| 5. 스키마 귀납 | 6. 관계 생성 | 7. 보수적 검증 | 8. KG 변환 |
|---|---|---|---|
| 반복 역할에서 `ProposalWorkUnit`, `ProposalArtifact` 등 8개 구체 유형 구성 | 표 구조와 한국어 패턴을 `HAS_INPUT`, `PRODUCES_OUTPUT` 등으로 표준화 | 근거·주체/객체 타입·중복·순환·SHACL 검사. 불확실하면 `UNRESOLVED` | 개념·관계·Assertion·Evidence를 RDF/Neo4j로 저장 |

## 하나의 문장이 그래프가 되는 예

> “제안팀이 고객 요구사항을 바탕으로 제안서를 작성한다.”

```text
Mention: 제안팀 / 고객 요구사항 / 제안서 작성
SemanticFrame: 주체=제안팀, 행위=작성, 입력=고객 요구사항, 산출물=제안서
그래프: 제안서 작성 ─PERFORMED_BY→ 제안팀
          제안서 작성 ─HAS_INPUT→ 고객 요구사항
          제안서 작성 ─PRODUCES_OUTPUT→ 제안서
          각 관계 ─DERIVED_FROM→ 원문 Evidence
```

**최종 결과:** 1,366행 → Mention 2,954개 → ConceptCluster 2,188개 → Assertion 261개 → Neo4j 노드 11,053개·관계 19,502개. **파이프라인은 완주했지만 의미 정확도는 후속 전문가 검증이 필요하다.**
