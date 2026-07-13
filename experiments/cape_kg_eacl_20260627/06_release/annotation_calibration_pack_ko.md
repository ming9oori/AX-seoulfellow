# CAPE-KG Annotation Calibration Pack

Generated: 2026-06-29T18:56:10.624146+00:00
Experiment: `experiments/cape_kg_eacl_20260627`
Source package: `full_120`

이 파일은 formal priority-100 annotation을 시작하기 전 annotator A/B가 같은 기준을 이해하도록 만든 내부 calibration 자료입니다.
여기에 포함된 예시는 정답지가 아니며, 논문용 human-gold evidence도 아닙니다.

## 사용 원칙

- priority batch 001-005의 formal annotation은 annotator A/B가 독립적으로 수행한다.
- calibration 예시는 formal 100개 priority batch와 겹치지 않는 non-priority rows에서 뽑았다.
- 이 자료는 rule alignment와 edge/evidence 판단 연습용이다.
- 토론하더라도 특정 formal priority chunk의 정답을 만들거나 공유하지 않는다.
- 모든 최종 판단은 `chunk_text`와 evidence span에 직접 근거가 있어야 한다.

## Calibration Focus

| focus | examples | decision rule |
| --- | ---: | --- |
| `risk_requires_explicit_text` | 1 | Risk는 위험, 실패 요인, 주의사항이 명시된 경우에만 gold로 둔다. |
| `role_relation_must_be_direct` | 7 | PERFORMED_BY는 역할과 수행 업무가 같은 문장 또는 직접 연결된 근거에 있을 때만 accept한다. |
| `artifact_flow_direction` | 3 | 입력/산출/전달 방향을 확인한다. 업무가 artifact를 쓰는지, artifact가 업무로 전달되는지 방향을 바꾸지 않는다. |
| `evidence_span_repair` | 1 | label_not_found 또는 full_sentence_proxy는 자동 제안일 뿐이다. source/predicate/target이 실제 근거에 있는지 다시 확인한다. |

## Examples

| id | chunk | pages | focus | candidate | evidence excerpt | check |
| --- | --- | --- | --- | --- | --- | --- |
| CAL-01 | `JZ-CHUNK-0100` | 217-219 | `risk_requires_explicit_text` | 제안팀 구성 --HAS_RISK--> 약점 | 필자는 제안 PM에게 민주적이고 토론 중심의 조직관리가 제안팀에서는 매우 위험함을 경고한다. | Risk는 위험, 실패 요인, 주의사항이 명시된 경우에만 gold로 둔다. |
| CAL-02 | `JZ-CHUNK-0029` | 65-67 | `role_relation_must_be_direct` | 경쟁사 분석 --PERFORMED_BY--> 경쟁사 | 그러나 수주영업에서는 ‘관계구축’이 전부가 아니라 관계구축을 통해 ‘고객과 경쟁자 정보’를 수집하여 전략적으로 세일즈하는 것이 중요하다. | PERFORMED_BY는 역할과 수행 업무가 같은 문장 또는 직접 연결된 근거에 있을 때만 accept한다. |
| CAL-03 | `JZ-CHUNK-0030` | 67-70 | `role_relation_must_be_direct` | 경쟁사 분석 --PERFORMED_BY--> 경쟁사 | 그러나 수주영업에서는 ‘관계구축’이 전부가 아니라 관계구축을 통해 ‘고객과 경쟁자 정보’를 수집하여 전략적으로 세일즈하는 것이 중요하다. | PERFORMED_BY는 역할과 수행 업무가 같은 문장 또는 직접 연결된 근거에 있을 때만 accept한다. |
| CAL-04 | `JZ-CHUNK-0096` | 210-211 | `artifact_flow_direction` | PT 전략 개발 --USES_INPUT--> 발표자료 | '- 9~10시: 평가위원 도착 및 오리엔테이션- 10~12시: 제안 평가- 12~1시: 점심 - 1~3시: 제안 프레젠테이션- 3~5시: 점수 제출 및 검증몇 백억, 몇 천억 원 규모의 구매절차를 진행하는 국가방위사업도 평가기간이 점점 짧아지고 있다. | 입력/산출/전달 방향을 확인한다. 업무가 artifact를 쓰는지, artifact가 업무로 전달되는지 방향을 바꾸지 않는다. |
| CAL-05 | `JZ-CHUNK-0064` | 141-142 | `role_relation_must_be_direct` | 고객 니즈 분석 --PERFORMED_BY--> 경쟁사 | 수주영업은 고객 정보를 통해 고객의 니즈를 파악하고 경쟁자 정보를 통해 경쟁자보다 차별화된 솔루션을 제시하는 것이며, 이 활동을 SBS(Solution Based Selling)라고 부른다. | PERFORMED_BY는 역할과 수행 업무가 같은 문장 또는 직접 연결된 근거에 있을 때만 accept한다. |
| CAL-06 | `JZ-CHUNK-0095` | 208-210 | `artifact_flow_direction` | 제안팀 구성 --USES_INPUT--> 제안서 | 단계 4: 제안서 작성 준비 활동(Activity) 결과물(Output) 제안팀 멤버 및 업무 분장 결정제 안 관 리 계 획 (Proposal Management Plan) 수립목차 설계 초안제안관리 계획(PMP) 단계 5: 입찰 가격 구체화 활동(Activity) 결과물(Output) 가격 정보 업데이트, 원가 정의 및 목표 가격 결정 단계 6: 섹션기획서 준비 및 작성 활동(Activity) 결과물(Output) 섹션기획서 준비, 작성자 정보제공 내용... | 입력/산출/전달 방향을 확인한다. 업무가 artifact를 쓰는지, artifact가 업무로 전달되는지 방향을 바꾸지 않는다. |
| CAL-07 | `JZ-CHUNK-0136` | 297-299 | `role_relation_must_be_direct` | 제안서 기획 --PERFORMED_BY--> 제안 PM | PM(또는 Core T eam)은 작성된 제안서를 검토할 때 섹션기획서로 충실도와 전략이 잘 구현되었는지를 검토한다(상세 내용은 ‘4부 제안서 기획’ 참고). | PERFORMED_BY는 역할과 수행 업무가 같은 문장 또는 직접 연결된 근거에 있을 때만 accept한다. |
| CAL-08 | `JZ-CHUNK-0089` | 201-202 | `artifact_flow_direction` | 제안팀 구성 --USES_INPUT--> Capture Plan | 단계 1: 팀 구성 활동(Activity) 결과물(Output) 프로젝트 담당자 혹은 전담 팀 구성 프로젝트 조직도단계 2: 고객과 관계 형성 활동(Activity) 결과물(Output) 고객 접촉 확대, 솔루션 관련 정보 수집 고객미팅 플래너단계 3: 수주전략 수립 활동(Activity) 결과물(Output) 수주전략 초안 개발 / 리뷰 (리뷰된 수주전략을 Capture Plan에 포함) 수주전략의 실행계획 적용수주전략 업데이트 및 제안... | 입력/산출/전달 방향을 확인한다. 업무가 artifact를 쓰는지, artifact가 업무로 전달되는지 방향을 바꾸지 않는다. |
| CAL-09 | `JZ-CHUNK-0059` | 131-133 | `role_relation_must_be_direct` | 고객 니즈 분석 --PERFORMED_BY--> 고객 | 쉬플리의 조사에 따르면 고객의 제안 요청서(RFP: Request for Proposal)상의 요구조건을 100% 충족시킨 제안서라 하더라도 그 성공률은 100%가 아니라 52%라고 한다. | PERFORMED_BY는 역할과 수행 업무가 같은 문장 또는 직접 연결된 근거에 있을 때만 accept한다. |
| CAL-10 | `JZ-CHUNK-0071` | 157-157 | `role_relation_must_be_direct` | 고객 니즈 분석 --PERFORMED_BY--> 고객 | 쉬플리의 조사에 따르면 고객의 제안 요청서(RFP: Request for Proposal)상의 요구조건을 100% 충족시킨 제안서라 하더라도 그 성공률은 100%가 아니라 52%라고 한다. | PERFORMED_BY는 역할과 수행 업무가 같은 문장 또는 직접 연결된 근거에 있을 때만 accept한다. |
| CAL-11 | `JZ-CHUNK-0063` | 139-141 | `evidence_span_repair` | 충실도 점검 --HAS_PRINCIPLE--> 충실도 | 쉬플리의 조사에 따르면 고객의 제안 요청서(RFP: Request for Proposal)상의 요구조건을 100% 충족시킨 제안서라 하더라도 그 성공률은 100%가 아니라 52%라고 한다. | label_not_found 또는 full_sentence_proxy는 자동 제안일 뿐이다. source/predicate/target이 실제 근거에 있는지 다시 확인한다. |
| CAL-12 | `JZ-CHUNK-0027` | 61-63 | `role_relation_must_be_direct` | 수주영업 --PERFORMED_BY--> 제안 PM | 수주영업을 비즈니스 개발(Business Development, 이하 B/D)이라고 한다. | PERFORMED_BY는 역할과 수행 업무가 같은 문장 또는 직접 연결된 근거에 있을 때만 accept한다. |

## 반환 파일과의 관계

- 이 calibration pack은 `.reviewed.jsonl` 반환 파일을 만들지 않는다.
- minimum paper gate는 여전히 10개 A/B reviewed JSONL, adjudication edited JSONL, IAA, human-gold scoring이 필요하다.
- 이 파일을 근거로 silver candidate를 자동 accept하면 안 된다.
