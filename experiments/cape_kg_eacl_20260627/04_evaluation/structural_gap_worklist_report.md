# CAPE-KG Structural Gap Worklist

Generated: 2026-06-29T18:55:37.008168+00:00
Claim status: `structural_gap_worklist_pending_human_review`

This worklist turns structural diagnostics into reviewable repair candidates. It does not modify the KG automatically.

## Summary

| Item | Value |
|---|---:|
| Review checkpoint candidates | 45 |
| Gateway branch gaps | 4 |
| Structural CQ answerability | 1.0 |
| Procedural consistency | 0.995283 |

## Review Checkpoint Candidates

| node | type | label | recommended action |
|---|---|---|---|
| `L2_TASK_COMPLIANCE_CHECK` | DomainTask | 충실도 점검 | consider_retyping_or_linking_as_review_checkpoint |
| `L2_TASK_PROPOSAL_REVIEW` | DomainTask | 제안서 리뷰 | consider_retyping_or_linking_as_review_checkpoint |
| `L2_TASK_RED_TEAM_REVIEW` | DomainTask | 레드팀 리뷰 | consider_retyping_or_linking_as_review_checkpoint |
| `STEP-BID_VALIDATION-01` | ProcedureStep | 제안 요청서 검토 | confirm_projected_review_checkpoint |
| `STEP-BID_VALIDATION-02` | ProcedureStep | 제안전략 검토 | confirm_projected_review_checkpoint |
| `STEP-COMPETITOR_ANALYSIS-01` | ProcedureStep | 제안 요청서 검토 | confirm_projected_review_checkpoint |
| `STEP-COMPETITOR_ANALYSIS-02` | ProcedureStep | Capture Plan 검토 | confirm_projected_review_checkpoint |
| `STEP-COMPLIANCE_CHECK-01` | ProcedureStep | 제안 요청서 검토 | confirm_projected_review_checkpoint |
| `STEP-COMPLIANCE_CHECK-02` | ProcedureStep | Capture Plan 검토 | confirm_projected_review_checkpoint |
| `STEP-CUSTOMER_NEEDS_ANALYSIS-01` | ProcedureStep | 제안 요청서 검토 | confirm_projected_review_checkpoint |
| `STEP-CUSTOMER_NEEDS_ANALYSIS-02` | ProcedureStep | Capture Plan 검토 | confirm_projected_review_checkpoint |
| `STEP-EXECUTIVE_SUMMARY_WRITING-01` | ProcedureStep | 제안 요청서 검토 | confirm_projected_review_checkpoint |
| `STEP-EXECUTIVE_SUMMARY_WRITING-02` | ProcedureStep | Capture Plan 검토 | confirm_projected_review_checkpoint |
| `STEP-KICKOFF_MEETING-01` | ProcedureStep | 제안 요청서 검토 | confirm_projected_review_checkpoint |
| `STEP-KICKOFF_MEETING-02` | ProcedureStep | 제안전략 검토 | confirm_projected_review_checkpoint |
| `STEP-OPPORTUNITY_ASSESSMENT-01` | ProcedureStep | Capture Plan 검토 | confirm_projected_review_checkpoint |
| `STEP-OPPORTUNITY_ASSESSMENT-02` | ProcedureStep | 제안전략 검토 | confirm_projected_review_checkpoint |
| `STEP-OUTLINE_DEVELOPMENT-01` | ProcedureStep | 제안 요청서 검토 | confirm_projected_review_checkpoint |
| `STEP-OUTLINE_DEVELOPMENT-02` | ProcedureStep | 제안전략 검토 | confirm_projected_review_checkpoint |
| `STEP-PMP_DEVELOPMENT-04` | ProcedureStep | 리뷰 방법 정의 | confirm_projected_review_checkpoint |
| `STEP-PRICE_STRATEGY-01` | ProcedureStep | 제안 요청서 검토 | confirm_projected_review_checkpoint |
| `STEP-PRICE_STRATEGY-02` | ProcedureStep | 제안전략 검토 | confirm_projected_review_checkpoint |
| `STEP-PROPOSAL_PLANNING-01` | ProcedureStep | Capture Plan 검토 | confirm_projected_review_checkpoint |
| `STEP-PROPOSAL_REVIEW-01` | ProcedureStep | 리뷰 기준 수립 | confirm_projected_review_checkpoint |
| `STEP-PROPOSAL_REVIEW-02` | ProcedureStep | 핑크팀 리뷰 | confirm_projected_review_checkpoint |
| `STEP-PROPOSAL_REVIEW-03` | ProcedureStep | 레드팀 리뷰 | confirm_projected_review_checkpoint |
| `STEP-PROPOSAL_REVIEW-04` | ProcedureStep | 충실도 점검 | confirm_projected_review_checkpoint |
| `STEP-PROPOSAL_REVIEW-05` | ProcedureStep | 품질 점검 | confirm_projected_review_checkpoint |
| `STEP-PROPOSAL_REVIEW-06` | ProcedureStep | 수정사항 반영 | consider_add_HAS_REVIEW_CHECKPOINT_from_step |
| `STEP-PROPOSAL_STRATEGY_DEVELOPMENT-01` | ProcedureStep | 제안 요청서 검토 | confirm_projected_review_checkpoint |
| `STEP-PROPOSAL_STRATEGY_DEVELOPMENT-02` | ProcedureStep | Capture Plan 검토 | confirm_projected_review_checkpoint |
| `STEP-PROPOSAL_TEAM_FORMATION-01` | ProcedureStep | 제안 요청서 검토 | confirm_projected_review_checkpoint |
| `STEP-PROPOSAL_TEAM_FORMATION-02` | ProcedureStep | Capture Plan 검토 | confirm_projected_review_checkpoint |
| `STEP-PROPOSAL_WRITING-01` | ProcedureStep | 섹션기획서 검토 | confirm_projected_review_checkpoint |
| `STEP-PROPOSAL_WRITING-05` | ProcedureStep | 리뷰 의견 반영 | confirm_projected_review_checkpoint |
| `STEP-PT_STRATEGY-01` | ProcedureStep | 제안 요청서 검토 | confirm_projected_review_checkpoint |
| `STEP-PT_STRATEGY-02` | ProcedureStep | Proposal Management Plan 검토 | confirm_projected_review_checkpoint |
| `STEP-RED_TEAM_REVIEW-01` | ProcedureStep | 제안 요청서 검토 | confirm_projected_review_checkpoint |
| `STEP-RED_TEAM_REVIEW-02` | ProcedureStep | Capture Plan 검토 | confirm_projected_review_checkpoint |
| `STEP-RED_TEAM_REVIEW-03` | ProcedureStep | 제안 요청서 작성 | consider_add_HAS_REVIEW_CHECKPOINT_from_step |
| `STEP-RED_TEAM_REVIEW-04` | ProcedureStep | Capture Plan 작성 | consider_add_HAS_REVIEW_CHECKPOINT_from_step |
| `STEP-SOLUTION_DEFINITION-01` | ProcedureStep | 제안 요청서 검토 | confirm_projected_review_checkpoint |
| `STEP-SOLUTION_DEFINITION-02` | ProcedureStep | Capture Plan 검토 | confirm_projected_review_checkpoint |
| `STEP-WIN_STRATEGY_DEVELOPMENT-01` | ProcedureStep | 제안 요청서 검토 | confirm_projected_review_checkpoint |
| `STEP-WIN_STRATEGY_DEVELOPMENT-02` | ProcedureStep | Capture Plan 검토 | confirm_projected_review_checkpoint |

## Gateway Branch Gaps

| gateway | label | guards | incoming tasks | candidate branch targets |
|---|---|---:|---:|---|
| `L2_DG_DG_APPROVAL` | 승인 | 9 | 22 | `L2_TASK_BID_NO_BID_DECISION:제안참여 의사결정 | L2_TASK_BID_VALIDATION:입찰타당성 검증 | L2_TASK_CAPTURE_PLANNING:수주영업 | L2_TASK_COMPETITOR_ANALYSIS:경쟁사 분석 | L2_TASK_COMPLIANCE_CHECK:충실도 점검 | L2_TASK_CUSTOMER_NEEDS_ANALYSIS:고객 니즈 분석 | L2_TASK_EXECUTIVE_SUMMARY_WRITING:제안요약 작성 | L2_TASK_KICKOFF_MEETING:킥오프 미팅 | L2_TASK_OPPORTUNITY_ASSESSMENT:기회분석 | L2_TASK_OUTLINE_DEVELOPMENT:목차 개발 | L2_TASK_PMP_DEVELOPMENT:제안계획 수립 | L2_TASK_PRICE_STRATEGY:가격 전략 수립` |
| `L2_DG_DG_BID_NO_BID` | Bid/No Bid Decision | 3 | 8 | `L2_TASK_BID_NO_BID_DECISION:제안참여 의사결정 | L2_TASK_BID_VALIDATION:입찰타당성 검증 | L2_TASK_CAPTURE_PLANNING:수주영업 | L2_TASK_COMPETITOR_ANALYSIS:경쟁사 분석 | L2_TASK_OPPORTUNITY_ASSESSMENT:기회분석 | L2_TASK_PROPOSAL_PLANNING:제안서 기획 | L2_TASK_PROPOSAL_WRITING:제안서 작성 | L2_TASK_WIN_STRATEGY_DEVELOPMENT:수주전략 수립` |
| `L2_DG_DG_BID_VALIDATION` | 입찰타당성 결정 | 1 | 17 | `L2_TASK_BID_NO_BID_DECISION:제안참여 의사결정 | L2_TASK_BID_VALIDATION:입찰타당성 검증 | L2_TASK_CAPTURE_PLANNING:수주영업 | L2_TASK_COMPLIANCE_CHECK:충실도 점검 | L2_TASK_CUSTOMER_NEEDS_ANALYSIS:고객 니즈 분석 | L2_TASK_KICKOFF_MEETING:킥오프 미팅 | L2_TASK_OPPORTUNITY_ASSESSMENT:기회분석 | L2_TASK_OUTLINE_DEVELOPMENT:목차 개발 | L2_TASK_PMP_DEVELOPMENT:제안계획 수립 | L2_TASK_PRICE_STRATEGY:가격 전략 수립 | L2_TASK_PROPOSAL_PLANNING:제안서 기획 | L2_TASK_PROPOSAL_REVIEW:제안서 리뷰` |
| `L2_DG_DG_PURSUIT` | Pursuit Decision | 1 | 7 | `L2_TASK_BID_NO_BID_DECISION:제안참여 의사결정 | L2_TASK_BID_VALIDATION:입찰타당성 검증 | L2_TASK_CAPTURE_PLANNING:수주영업 | L2_TASK_COMPETITOR_ANALYSIS:경쟁사 분석 | L2_TASK_OPPORTUNITY_ASSESSMENT:기회분석 | L2_TASK_PROPOSAL_PLANNING:제안서 기획 | L2_TASK_PROPOSAL_WRITING:제안서 작성` |

## Interpretation

- Review-signaled `ProcedureStep` rows are now projected to `ReviewCheckpoint` through `HAS_REVIEW_CHECKPOINT`; this list remains for human confirmation and possible cleanup.
- Gateway branch edges should not be synthesized automatically unless source evidence clearly states branch outcomes.
- Human review can use these rows to confirm projected checkpoints, retype a node, or add `BRANCHES_TO` edges.
