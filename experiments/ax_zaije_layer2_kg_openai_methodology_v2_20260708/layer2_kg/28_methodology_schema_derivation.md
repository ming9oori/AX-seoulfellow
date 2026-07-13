# AX ZAIJE Layer2 KG Methodology v2 Schema Derivation

Generated: 2026-07-08T03:12:14+00:00
Run ID: `RUN_2026_07_08_METHOD_V2_REPLAY_001`

## 1. Schema 설계 절차

이번 v2 방법론에서는 KG 구축을 두 단계로 분리했다.

| 단계 | 산출물 | 설명 |
| --- | --- | --- |
| A. Schema/Inventory 설계 | node type, canonical node, predicate schema | LLM이 자유롭게 node/predicate를 만들기 전에 사용할 어휘와 relation type을 정의한다. |
| B. Evidence-grounded LLM extraction | task-frame link, triple 후보 | LLM은 원문 evidence에서 schema 안에 들어맞는 relation 후보만 제안한다. |
| C. Validation/Materialization | 최종 nodes/edges | canonical id, allowed predicate, evidence id, domain/range, confidence threshold를 통과한 항목만 그래프에 반영한다. |

즉 `L2_ARTIFACT_RFP`, `L2_TASK_CAPTURE_PLANNING`, `CONTAINS` 같은 값은 LLM이 즉석에서 만든 값이 아니다. 설계 단계에서 만든 controlled vocabulary이고, LLM은 그 후보 집합 안에서만 subject, predicate, object를 선택했다.

## 2. ID 생성 규칙

| 대상 | 규칙 | 예시 |
| --- | --- | --- |
| DomainProcess | `L2_PROCESS_<업무흐름>` | `L2_PROCESS_CAPTURE_PLANNING` |
| DomainTask | `L2_TASK_<업무활동>` | `L2_TASK_CAPTURE_PLANNING` |
| Artifact | `L2_ARTIFACT_<산출물명>` | `L2_ARTIFACT_RFP` |
| InformationObject | `L2_INFO_<정보객체명>` | `L2_INFO_OFFICIAL_REQUIREMENT` |
| Role | `L2_ROLE_<역할명>` | `L2_ROLE_PROPOSAL_TEAM` |
| Predicate | 대문자 동사/관계구 | `USES_INPUT`, `PRODUCES`, `CONTAINS` |

ID는 사람이 읽을 수 있는 stable canonical id로 설계했다. 동일 개념의 한국어, 영어, 약어는 `AliasTerm`과 `ALIAS_OF`로 연결한다.

## 3. Node Type 도출

| category | count |
| --- | ---: |
| `task_frame_schema` | 14 |
| `source_evidence_graph` | 5 |
| `schema_root` | 1 |
| `domain_metamodel` | 1 |
| `skos_alias_management` | 1 |

Node type은 원문 구조를 추적하기 위한 Source Evidence Graph 유형과, 업무 지식을 표현하기 위한 Task Frame 유형으로 나누었다.

## 4. Canonical Process/Task 도출

- Canonical process: 6개
- Canonical task: 15개

Process는 책의 장/절 흐름을 업무 단계로 묶어 만들었다. Task는 단순 섹션 제목이 아니라, 원문에서 활동, 입력, 산출물, 역할, 의사결정 또는 후속 업무 연결이 확인되는 단위를 후보로 삼았다.

| task id | label | parent process | grounding evidence | valid LLM links |
| --- | --- | --- | ---: | ---: |
| `L2_TASK_REQUIREMENT_ICEBERG_ANALYSIS` | 고객 요구조건 구조 분석 | `L2_PROCESS_BID_PROPOSAL_CONTEXT` | 20 | 4 |
| `L2_TASK_OPPORTUNITY_PLANNING` | 사전영업 / Opportunity Planning | `L2_PROCESS_PRE_BID_PREPARATION` | 20 | 4 |
| `L2_TASK_CAPTURE_PLANNING` | 수주영업 / Capture Planning | `L2_PROCESS_CAPTURE_PLANNING` | 20 | 15 |
| `L2_TASK_BID_NO_BID_DECISION` | 제안참여 의사결정 | `L2_PROCESS_PRE_BID_PREPARATION` | 20 | 8 |
| `L2_TASK_PROPOSAL_PLANNING` | 제안서 기획 / Proposal Planning | `L2_PROCESS_PROPOSAL_EXECUTION` | 20 | 12 |
| `L2_TASK_PROPOSAL_PREPARING` | 제안서 작성 / Proposal Preparing | `L2_PROCESS_PROPOSAL_EXECUTION` | 20 | 8 |
| `L2_TASK_PRESENTATION_PREPARATION` | 프레젠테이션 준비 | `L2_PROCESS_PROPOSAL_EXECUTION` | 20 | 5 |
| `L2_TASK_SALES_INFORMATION_MANAGEMENT` | 영업 정보 관리 | `L2_PROCESS_CAPTURE_PLANNING` | 20 | 3 |
| `L2_TASK_VALUE_PROPOSITION` | 가치제안 개발 | `L2_PROCESS_CAPTURE_PLANNING` | 20 | 11 |
| `L2_TASK_EVALUATOR_ANALYSIS` | 평가자 분석 | `L2_PROCESS_EVALUATOR_PERSUASION` | 20 | 7 |
| `L2_TASK_PERSUASIVE_COMMUNICATION` | 설득 커뮤니케이션 설계 | `L2_PROCESS_EVALUATOR_PERSUASION` | 20 | 7 |
| `L2_TASK_PROPOSAL_STRATEGY_DEVELOPMENT` | 제안전략 개발 | `L2_PROCESS_PROPOSAL_STRATEGY` | 20 | 12 |
| `L2_TASK_COMPETITOR_ANALYSIS` | 경쟁사 분석 및 차별화 요소 규명 | `L2_PROCESS_PROPOSAL_STRATEGY` | 20 | 9 |
| `L2_TASK_TACTIC_DEVELOPMENT_VALIDATION` | 전술 개발 및 효과성 검증 | `L2_PROCESS_PROPOSAL_STRATEGY` | 16 | 2 |
| `L2_TASK_RISK_MANAGEMENT` | 리스크 관리 | `L2_PROCESS_PROPOSAL_STRATEGY` | 20 | 4 |

## 5. Canonical Entity 도출

| node type | count |
| --- | ---: |
| `InformationObject` | 20 |
| `Artifact` | 10 |
| `StrategyPattern` | 7 |
| `Stakeholder` | 6 |
| `ReviewType` | 4 |
| `Role` | 3 |
| `Principle` | 3 |
| `DecisionOutcome` | 2 |
| `Risk` | 2 |
| `DecisionPoint` | 1 |
| `Metric` | 1 |

Entity는 세 가지 기준으로 포함했다.

1. 설계서에서 우선 인식 대상으로 지정된 Artifact.
2. Task Frame의 input/output/role/stakeholder/principle/risk/review slot에 필요한 개념.
3. Competency Question 경로를 평가하기 위해 필요한 핵심 정보 객체.

각 entity는 alias, keyword, preferred label을 이용해 EvidenceSpan과 자동 연결했고, 이 근거는 사람 검수 전 grounding 및 review queue 생성을 위한 것이다.

## 6. Predicate 도출

- 전체 predicate: 28개
- LLM 추출 허용 predicate: 23개

Predicate는 relation과 거의 같은 개념이지만 정확히는 relation type이다. 예를 들어 `CONTAINS`는 relation type이고, 실제 relation instance는 다음과 같은 edge이다.

```text
L2_ARTIFACT_RFP -[CONTAINS]-> L2_INFO_OFFICIAL_REQUIREMENT
```

| predicate | category | domain | range | LLM allowed |
| --- | --- | --- | --- | --- |
| `HAS_CHAPTER` | `source_structure` | `["Book"]` | `["Chapter"]` | no |
| `HAS_SECTION` | `source_structure` | `["Chapter"]` | `["Section"]` | no |
| `HAS_CHUNK` | `source_structure` | `["Section"]` | `["SourceChunk"]` | no |
| `HAS_PROCESS` | `schema_scaffold` | `["DomainOntology"]` | `["DomainProcess"]` | yes |
| `HAS_TASK` | `task_catalog` | `["DomainProcess"]` | `["DomainTask"]` | yes |
| `HAS_SUBTASK` | `task_decomposition` | `["DomainTask"]` | `["DomainTask", "Step"]` | yes |
| `CONTAINS` | `document_information_composition` | `["Artifact", "InformationObject"]` | `["InformationObject"]` | yes |
| `PART_OF` | `document_information_composition` | `["InformationObject", "Artifact"]` | `["InformationObject", "Artifact"]` | yes |
| `DISCOVERS` | `task_information_flow` | `["DomainTask"]` | `["InformationObject"]` | yes |
| `PRECEDES` | `workflow_order` | `["DomainTask", "Step"]` | `["DomainTask", "Step"]` | yes |
| `USES_INPUT` | `task_io` | `["DomainTask", "Step"]` | `["Artifact", "InformationObject", "StrategyPattern"]` | yes |
| `USED_AS_INPUT_FOR` | `task_io` | `["Artifact", "InformationObject", "StrategyPattern"]` | `["DomainTask"]` | yes |
| `PRODUCES` | `task_io` | `["DomainTask", "Step"]` | `["Artifact", "InformationObject", "StrategyPattern"]` | yes |
| `PERFORMED_BY` | `responsibility` | `["DomainTask", "Step"]` | `["Role"]` | yes |
| `TARGETS_STAKEHOLDER` | `stakeholder_targeting` | `["DomainTask", "StrategyPattern"]` | `["Stakeholder"]` | yes |
| `ANALYZES` | `analysis_activity` | `["DomainTask", "Step"]` | `["InformationObject", "Stakeholder", "Risk"]` | yes |
| `DEVELOPS` | `development_activity` | `["DomainTask", "Step"]` | `["Artifact", "StrategyPattern"]` | yes |
| `REFINES_INTO` | `strategy_refinement` | `["Artifact", "StrategyPattern"]` | `["Artifact", "StrategyPattern"]` | yes |
| `DECIDES` | `decision_model` | `["DecisionPoint", "Role"]` | `["DecisionOutcome"]` | yes |
| `HAS_DECISION_POINT` | `decision_model` | `["DomainTask", "DomainProcess"]` | `["DecisionPoint"]` | yes |
| `EVALUATES` | `review_evaluation` | `["DomainTask", "Step", "Role"]` | `["Artifact", "StrategyPattern", "Metric"]` | yes |
| `HAS_REVIEW` | `review_evaluation` | `["DomainTask", "Artifact"]` | `["ReviewType"]` | yes |
| `HAS_PRINCIPLE` | `principle_alignment` | `["DomainTask", "StrategyPattern"]` | `["Principle"]` | yes |
| `MITIGATES` | `risk_management` | `["DomainTask", "StrategyPattern"]` | `["Risk"]` | yes |
| `INCREASES_RISK` | `risk_management` | `["Condition"]` | `["Risk"]` | yes |
| `MAY_RESULT_IN` | `outcome_link` | `["DomainTask", "StrategyPattern"]` | `["InformationObject", "Artifact", "Metric"]` | yes |
| `ALIAS_OF` | `skos_alias_management` | `["AliasTerm"]` | `["Any"]` | no |
| `EVIDENCED_BY` | `provenance` | `["Any"]` | `["EvidenceSpan"]` | no |

## 7. 논문 작성 시 표현

본 연구에서는 LLM을 schema author로 사용하지 않고, schema-constrained extractor로 사용했다. 먼저 문헌 기반/도메인 기반 설계 절차를 통해 Layer2 node type, canonical inventory, allowed predicate, domain/range constraint를 구성했다. 이후 OpenAI LLM은 각 chunk에서 evidence id와 함께 canonical subject, allowed predicate, canonical object를 선택하도록 제한되었다. 최종 KG 반영은 canonical id validation, predicate validation, domain/range validation, evidence validation, confidence threshold, SPO deduplication을 통과한 경우로 한정했다.
