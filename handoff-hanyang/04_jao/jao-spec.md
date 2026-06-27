# JAO 직무 에이전트 운영 온톨로지 명세서 v0.1

> **Job-Agent Operational Ontology (JAO)** — AI 직무 에이전트가 도메인 컨텍스트를 갖고 안전하게 행동하기 위한 운영 백본.

---

## 1. Executive Summary

JAO는 4종 글로벌 직무 표준(APQC PCF · NCS · O*NET · ESCO)과 12종 보조 데이터(Tools · Regulations · Artifacts · Workflows 등)를 단일 메타-스키마 위에 통합하고, 그 위에서 AI 에이전트가 **사전 정의된 Action만 호출**하며 **사람 검토와 자동화의 균형**을 점진적으로 옮길 수 있도록 한다. 팔란티어 AIP의 Ontology-Aware Generation 패턴과 W3C SKOS · OMG BPMN/DMN/CMMN · Anthropic MCP · GraphRAG 모범사례를 통합한다.

**핵심 원칙 4가지**
1. **도메인 컨텍스트** — 객체와 관계를 검색하라, 자유 텍스트가 아니라.
2. **안전한 행동** — 사전 정의 Action만, 자유 SQL/code 금지.
3. **신뢰 기반 자동화** — Staged → Human → Auto 점진 전환, confidence로 측정.
4. **운영 표준 통합** — MCP·BPMN·SHACL·SKOS 등 사실상 표준 위에서.

---

## 2. 5계층 아키텍처

```
L5  Runtime KG     — 실행 트레이스 + 인스턴스 (audit log + memory)
L4  Agent Layer    — Persona · Skill · Action · Workflow · Guardrail
L3  Operational    — Object · Action · Workflow · MappingEdge (JAO core)
L2  Domain         — PCF · NCS · O*NET · ESCO · Tools · Regulations
L1  Foundation     — SKOS · Schema.org (+ 도메인 ontology 선택)
```

---

## 3. 메타-스키마 (`entity-schemas/_base.schema.json`)

모든 인스턴스는 base를 상속한다.

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `$id` | URI | ✓ | 전역 식별자. 형식 `jao://{class}/{namespace}/{localId}` |
| `id` | string | ✓ | namespace 내 unique |
| `class` | enum | ✓ | 16개 클래스 중 하나 |
| `namespace` | enum | ✓ | pcf · ncs · onet · esco · agent · tool · reg · art · jao · ext |
| `version` | semver | ✓ | major.minor.patch |
| `status` | enum | ✓ | draft → review → published → deprecated |
| `label.{ko,en}` | object | ✓ | 최소 ko 또는 en 하나 |
| `description.{ko,en}` | object | — | 상세 설명 |
| `aliases[]` | array | — | 동의어·약어 |
| `owner` | string | — | RACI 책임자 |
| `steward` | string | — | 데이터 큐레이터 |
| `source` | object | — | provenance (type·ref·url·license) |
| `confidence` | 0~1 | — | 자동 산출 ≤0.7, 검증 후 ≥0.85 |
| `tags[]` | array | — | 분류 태그 |
| `createdAt`/`updatedAt`/`approvedBy`/`approvedAt` | — | 거버넌스 |
| `supersedes`/`supersededBy` | URI | — | 버전 체인 |

---

## 4. 16 엔티티 클래스 카탈로그

### 4.1 Foundation 계층
| 클래스 | 출처/매핑 | 핵심 필드 |
|---|---|---|
| **Concept** | SKOS | broader[], narrower[], related[], definition |
| **Term** | 통합 사전 | pronunciation, partOfSpeech, equivalents[] |

### 4.2 Domain 계층
| 클래스 | 핵심 필드 |
|---|---|
| **Process** ▶ `process.schema.json` | hid, level(1-5), parent, industry[], metrics[], uses[], produces[], governedBy[] |
| **Activity** | tasks[], uses[], produces[], governedBy[] |
| **Task** | unitCode, elemCode, criteria[], ksaCodes[], levelL(1-8) |
| **Metric** | formula, unit, direction, target, frequency |

### 4.3 Execution 계층
| 클래스 | 핵심 필드 |
|---|---|
| **Tool** | category, vendor, mcpServerUri, apiType, popularity |
| **Artifact** | sections[], template, mimeType, aiAssistable, cycle |
| **Regulation** | code, jurisdiction, enforcer, riskLevel, keyArticles[] |
| **Policy** | sourceRegulation, enforcePrompt, appliesTo, severity |
| **Event** | trigger, schedule, payload |
| **Role** | level, permissions[], reportsTo |
| **Risk** | description, likelihood, impact, mitigation[] |

### 4.4 Agent 계층
| 클래스 | 핵심 필드 |
|---|---|
| **Agent** ▶ `agent.schema.json` | role, jobFamily, embodies{ncs,pcf,onet,esco}, primaryMissions[], actions[], skills[], tools[], guardrails[], escalations[], interventionMode |
| **Action** ▶ `action.schema.json` | category, inputs[], outputs[], preconditions[], sideEffects, riskLevel, approvers[], idempotencyKey, rollback, mcpServer, enforcedBy[] |
| **Skill** | instructionPrompt, examples[], tools[], triggers[] |
| **Workflow** | steps[], gates[](DMN), cases[](CMMN), slaSec, escalationPolicy, interventionMode |

### 4.5 매핑 계층
| 클래스 | 핵심 필드 |
|---|---|
| **MappingEdge** | from(URI), to(URI), predicate, confidence, mappingType, evidence, validatedBy |

---

## 5. 관계 술어 (Typed Predicates)

```
Activity   uses           Tool          (N:M)
Activity   produces       Artifact      (N:M)
Activity   governedBy     Regulation    (N:M)
Activity   measuredBy     Metric        (N:M)
Activity   partOf         Process       (N:1)
Task       enables        Activity      (N:M)   ★PCF↔NCS 다리
Task       requires       Concept(K/S/A) (N:M)
Agent      embodies       Occupation    (N:M)
Agent      executes       Action        (N:M)
Agent      hasSkill       Skill         (N:M)
Action     mutates        Object        (N:1)
Action     triggers       Workflow      (N:M)
Action     enforcedBy     Policy        (N:M)
Action     requiresApproval Role        (N:M)
Workflow   follows        Action        (1:N)
Workflow   triggeredBy    Event         (N:M)
Policy     derivedFrom    Regulation    (N:1)
Term       equivalentTo   Term          (N:M)
*          mapsTo         *             (N:M, MappingEdge로 구체화)
```

---

## 6. 거버넌스 라이프사이클

```
draft ─review→ review ─approve→ published ─deprecate→ deprecated
                                    │
                                    └─supersededBy─→ 새 버전
```

- `published` 엔티티는 `confidence ≥ 0.85` 또는 `approvedBy` 존재 필수
- `audit-log.jsonl` — 모든 변경 행 단위 기록
- `review-queue.json` — status=review 큐
- `intervention-history.jsonl` — 사람 개입 학습용

---

## 7. Action · Workflow · Policy 명세 (운영 핵심)

### 7.1 Action (Palantir AIP 스타일)
```jsonc
{
  "class": "Action", "id": "post_adjustment_entry",
  "inputs":  [{"name":"debit","type":"AccountCode","required":true}, ...],
  "outputs": [{"name":"journalId","type":"string"}],
  "preconditions": ["debit==credit","amount<=$approvalLimit","period.status!=closed"],
  "sideEffects":   [{"system":"sap-erp","mutation":"GL.insert"}],
  "riskLevel":     "high",
  "approvers":     ["finance-mgr"],
  "humanInTheLoop": true,
  "auditLog":      true,
  "idempotencyKey": "hash(period+debit+credit+amount)",
  "rollback":      "reverse_journal",
  "mcpServer":     "mcp://sap-erp",
  "enforcedBy":    ["jao://Policy/jao/sox-control-iv"]
}
```

### 7.2 Workflow (BPMN-lite)
```jsonc
{
  "class": "Workflow", "id": "month-end-close",
  "triggeredBy": ["event:month-end"],
  "steps": [
    {"id":"s1","action":"reconcile_intercompany","onFail":"escalate"},
    {"id":"s2","gate":"all_recon_ok","dmnTable":"recon-check","onTrue":"s3","onFalse":"s2a"},
    {"id":"s2a","action":"post_adjustment_entry","requiresApproval":"finance-mgr"},
    {"id":"s3","action":"generate_closing_report"}
  ],
  "escalations": [{"after":"24h","to":"cfo"}],
  "interventionMode": "checkpoint"
}
```

### 7.3 Policy (Policy-as-Prompt)
```jsonc
{
  "class": "Policy", "id": "sox-control-iv",
  "sourceRegulation": "jao://Regulation/reg/sox",
  "enforcePrompt": "이 액션을 수행하기 전: (1) 직무 분리 (2) 4-eye rule (3) 한도 검증. 위반 시 거부.",
  "appliesTo":  ["jao://Action/agent/post_adjustment_entry"],
  "severity":   "critical"
}
```

---

## 8. Intervention Modes (Vellum 6-mode 패턴)

| Mode | 의미 | 적용 권장 |
|---|---|---|
| full-auto | 모든 단계 자동 | riskLevel ≤ medium + confidence ≥ 0.9 |
| gate-only | 시작 시 1회 승인 | 정기 작업 |
| **checkpoint** | 주요 단계마다 (default) | 신규/고위험 |
| step-by-step | 매 단계마다 | 학습기 |
| co-pilot | 사람 주도 | 전문가 보조 |
| custom | confidence/context 기반 동적 | SmartPause |

---

## 9. URI 규약

```
jao://{class}/{namespace}/{localId}
       ↑       ↑           ↑
       │       │           └─ namespace 내 유일
       │       └─ pcf/ncs/onet/esco/agent/tool/reg/art/jao/ext
       └─ 16 클래스 중 하나 (PascalCase)
```

예:
- `jao://Process/pcf/9.3`
- `jao://Agent/agent/finance-closing`
- `jao://Action/agent/post_adjustment_entry`
- `jao://Tool/tool/sap-erp`
- `jao://Regulation/reg/sox`
- `jao://Policy/jao/sox-control-iv`

---

## 10. 스키마 인덱스

| 파일 | 클래스 | 상태 |
|---|---|---|
| `entity-schemas/_base.schema.json` | (base) | ✅ |
| `entity-schemas/process.schema.json` | Process | ✅ |
| `entity-schemas/agent.schema.json` | Agent | ✅ |
| `entity-schemas/action.schema.json` | Action | ✅ |
| (W2) `task.schema.json` | Task | ⏳ |
| (W2) `tool.schema.json` | Tool | ⏳ |
| (W2) `artifact.schema.json` | Artifact | ⏳ |
| (W2) `regulation.schema.json` | Regulation | ⏳ |
| (W2) `policy.schema.json` | Policy | ⏳ |
| (W2) `workflow.schema.json` | Workflow | ⏳ |
| (W2) `metric.schema.json` | Metric | ⏳ |
| (W2) `skill.schema.json` | Skill | ⏳ |
| (W2) `role.schema.json` | Role | ⏳ |
| (W2) `concept.schema.json` | Concept | ⏳ |
| (W2) `term.schema.json` | Term | ⏳ |
| (W2) `mapping-edge.schema.json` | MappingEdge | ⏳ |
| (W2) `event.schema.json` | Event | ⏳ |
| (W2) `risk.schema.json` | Risk | ⏳ |

---

## 11. 검증 규칙 (`tools/jao_validate.py`)

| ID | 규칙 | W1 | W2 |
|---|---|:---:|:---:|
| R1 | 필수 필드 (id, class, namespace, version, status, label) | ✅ | |
| R2 | $id 전역 유일 | ✅ | |
| R3 | 참조 무결성 (모든 jao:// URI 끝점 존재) | ✅ | |
| R4 | partOf · supersedes 사이클 금지 | | ⏳ |
| R5 | 카디널리티 위반 검사 | | ⏳ |
| R6 | deprecated → published 참조 금지 | | ⏳ |
| R7 | published 엔티티 confidence ≥ 0.85 또는 approvedBy 존재 | | ⏳ |
| R8 | Action riskLevel≥high → approvers[] 필수 | | ⏳ |
| R9 | label.ko 또는 label.en 둘 다 가능, 최소 1개 | ✅ | |
| R10 | exact 매핑 양방향 일관성 | | ⏳ |

검증기 출력: `validation-report.json` + 콘솔 요약. errors=0이면 성공.

---

## 12. W1 Minimal Loop 결과 (PoC 완료)

| 산출 | 위치 | 비고 |
|---|---|---|
| 디렉터리 구조 | `entity-schemas/`, `entities/{raw,normalized,edges}/`, `tools/`, `mcp-servers/`, `evals/`, `jao-viewer/` | ✅ |
| Base + 3 클래스 스키마 | `entity-schemas/_base.schema.json`, `process.schema.json`, `agent.schema.json`, `action.schema.json` | ✅ |
| finance-closing 인스턴스 | `entities/normalized/Agent/finance-closing.json` | ✅ |
| 6 Action 인스턴스 | `entities/normalized/Action/{query_gl, post_adjustment_entry, reconcile_intercompany, generate_closing_report, flag_anomaly, compute_kpi}.json` | ✅ |
| 2 Process 인스턴스 | `entities/normalized/Process/{9.0, 9.3}.json` | ✅ |
| 외부 stub 15건 | `entities/normalized/{Tool,Artifact,Regulation,Policy}/*` | ✅ |
| 검증기 v0 | `tools/jao_validate.py` (R1·R2·R3·R9) | ✅ |
| 외부 stub 생성기 | `tools/migrate/stub_externals.py` | ✅ |
| 검증 보고서 | `validation-report.json` (24 인스턴스 검증, errors=0, warnings=15) | ✅ |

**E2E 검증 명령:**
```bash
cd "온톨로지 연구"
python tools/jao_validate.py
# 기대: ✅ 검증 통과 (0 errors)
```

---

## 13. 마이그레이션 가이드 (W3에서 본격화)

| Step | 작업 | 산출물 |
|---|---|---|
| M1 | 어댑터 작성 (기존 JSON → base 스키마 래핑) | `entities/raw/*.json` |
| M2 | 필드 표준화 (`hid`→`id` 등) | `entities/normalized/*.json` |
| M3 | 매핑 → MappingEdge 변환 | `entities/edges/*.json` |
| M4 | 검증·승인 | status: review→published |
| M5 | 기존 페이지 데이터 소스 전환 | 사용자 노출 변화 없음 |

원본 205개 파일은 **삭제하지 않고 `_legacy/`로 격리**, 새 디렉터리가 단일 정답.

---

## 부록 A. 재사용 가능한 기존 자산

- `agent-studio/data/{agents,actions,tools,regulations,artifacts}.json` — 인스턴스 원천
- `mapping/{auto_mappings,three_way_mapping,onet_pcf_mappings}.json` — MappingEdge 변환 소스
- `connections/build_data.py` — `jao-viewer/build.py` 패턴 참조
- `docs/ontology-plan.md` — 1차 설계 (본 문서가 후속)

## 부록 B. 참고 자료

- Palantir AIP — Ontology + AIP Logic + Agent Studio
- W3C SKOS, JSON Schema Draft-07, JSON-LD
- OMG BPMN 2.0, DMN 1.3, CMMN 1.1
- Anthropic MCP (Model Context Protocol)
- Microsoft GraphRAG / Neo4j GraphRAG
- NIST AI RMF — Govern/Map/Measure/Manage
- NeOn Methodology (오ntology 네트워크 구축법)
- arXiv 2509.23994 — Policy-as-Prompt
