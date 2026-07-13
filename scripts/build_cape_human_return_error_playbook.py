#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a troubleshooting playbook for CAPE-KG human-return validation errors."""

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from import_cape_crosswalk_review import (
    ALLOWED_DECISIONS as CROSSWALK_DECISIONS,
    ALLOWED_EXPLANATION_QUALITY as CROSSWALK_EXPLANATION_QUALITY,
    ALLOWED_GRADES as CROSSWALK_GRADES,
    ALLOWED_STATUSES as CROSSWALK_STATUSES,
)
from import_cape_gold_annotation import ANNOTATION_STATUSES, ADJUDICATION_STATUSES, IMMUTABLE_FIELDS
from import_cape_mapping_review import (
    ALLOWED_DECISIONS as MAPPING_DECISIONS,
    ALLOWED_EXPLANATION_QUALITY as MAPPING_EXPLANATION_QUALITY,
    ALLOWED_GRADES as MAPPING_GRADES,
    ALLOWED_STATUSES as MAPPING_STATUSES,
)
from validate_cape_human_review_returns import (
    ACTIVE_REVIEW_ALLOWED_BOOL,
    ACTIVE_REVIEW_ALLOWED_DECISIONS,
    ACTIVE_REVIEW_CORRECTION_DECISIONS,
    ACTIVE_REVIEW_REQUIRED_FIELDS,
    COMPLETED_ANNOTATION_STATUSES,
    COMPLETED_ADJUDICATION_STATUSES,
)
from validate_cape_structural_review_returns import CHECKPOINT_ALLOWED, GATEWAY_ALLOWED


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path, rows, fieldnames):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def row(scope, code, severity, source, cause, fix, prevention, applies_to="minimum_and_optional_returns"):
    return {
        "scope": scope,
        "error_code_or_pattern": code,
        "severity": severity,
        "source_script": source,
        "common_cause": cause,
        "recommended_fix": fix,
        "prevention": prevention,
        "applies_to": applies_to,
    }


def build_rows():
    annotation_source = "import_cape_gold_annotation.py / validate_cape_human_review_returns.py"
    rows = [
        row(
            "annotation",
            "invalid_annotation_status",
            "error",
            annotation_source,
            "annotation_status가 허용값이 아니거나 대소문자/공백이 섞임.",
            f"값을 {', '.join(sorted(ANNOTATION_STATUSES))} 중 하나로 수정한다.",
            "완료 행은 completed 또는 needs_adjudication만 사용한다.",
        ),
        row(
            "annotation",
            "gold_nodes_not_list",
            "error",
            "import_cape_gold_annotation.py",
            "gold_nodes가 JSON array가 아니라 object/string/null로 저장됨.",
            "gold_nodes를 [] 또는 node object list로 바꾼다.",
            "node를 추가하지 않으면 []를 유지한다.",
        ),
        row(
            "annotation",
            "gold_edges_not_list",
            "error",
            "import_cape_gold_annotation.py",
            "gold_edges가 JSON array가 아니라 object/string/null로 저장됨.",
            "gold_edges를 [] 또는 edge object list로 바꾼다.",
            "candidate accept 결과는 gold_edges[]에만 기록한다.",
        ),
        row(
            "annotation",
            "rejected_refs_not_list",
            "error",
            "import_cape_gold_annotation.py",
            "rejected_candidate_reference_ids가 list가 아님.",
            "reject한 reference_id 문자열 list로 수정한다.",
            "reject가 없으면 빈 list []를 유지한다.",
        ),
        row(
            "annotation",
            "unknown_rejected_candidate_ref",
            "warning",
            "import_cape_gold_annotation.py",
            "rejected_candidate_reference_ids에 해당 row의 candidate reference_id가 아닌 값이 들어감.",
            "해당 chunk의 silver_candidate_edges[].reference_id를 확인해 정확한 값으로 바꾼다.",
            "candidate를 reject할 때 reference_id를 그대로 복사한다.",
        ),
        row(
            "annotation",
            "duplicate_reviewed_chunk",
            "error",
            "import_cape_gold_annotation.py",
            "reviewed JSONL 안에 같은 chunk_id가 두 번 이상 있음.",
            "중복 row를 제거하고 하나의 최종 row만 남긴다.",
            "batch 파일을 줄 단위로 병합하지 말고 원본 row 수를 유지한다.",
        ),
        row(
            "annotation",
            "missing_chunk_id",
            "error",
            "import_cape_gold_annotation.py",
            "reviewed row에서 chunk_id가 비어 있거나 삭제됨.",
            "원본 input JSONL의 chunk_id를 그대로 복원한다.",
            f"불변 필드({', '.join(IMMUTABLE_FIELDS)})는 수정하지 않는다.",
        ),
        row(
            "annotation",
            "unknown_chunk_id",
            "error",
            "import_cape_gold_annotation.py",
            "reviewed file에 target/input에 없는 chunk_id가 있음.",
            "해당 row를 제거하거나 올바른 batch input 파일에서 다시 작성한다.",
            "다른 batch의 row를 복사하지 않는다.",
        ),
        row(
            "annotation",
            "mode_mismatch",
            "error",
            "import_cape_gold_annotation.py",
            "annotation row와 adjudication row 형식이 섞임.",
            "annotation reviewed file에는 annotation_status/gold_* 형식만, adjudication file에는 adjudication_status/adjudicated_* 형식만 둔다.",
            "annotator 파일과 adjudication 파일을 분리해서 저장한다.",
        ),
        row(
            "annotation",
            "immutable_field_changed",
            "error",
            "import_cape_gold_annotation.py",
            "chunk_id, chunk_text, package 등 원본 provenance 필드가 바뀜.",
            "원본 input JSONL의 해당 필드를 그대로 복원한다.",
            "검수자는 editable field만 수정한다.",
        ),
        row(
            "annotation",
            "missing_reviewed_chunks / missing_batch_chunks",
            "error",
            annotation_source,
            "reviewed file에서 배정된 chunk row 일부가 빠짐.",
            "input batch의 모든 row를 유지하고, 검수하지 않은 row는 pending/in_progress로 남긴다.",
            "JSONL line 수와 chunk_id set을 저장 전 비교한다.",
        ),
        row(
            "annotation",
            "extra_chunks_not_in_batch",
            "error",
            "validate_cape_human_review_returns.py",
            "reviewed file에 해당 batch에 없는 chunk가 섞임.",
            "다른 batch row를 제거하고 해당 batch input row만 남긴다.",
            "파일명과 batch id를 맞춰 관리한다.",
        ),
        row(
            "annotation",
            "annotator_id_mismatch",
            "error",
            "validate_cape_human_review_returns.py",
            "A 파일에 annotator_id=B가 들어가거나 반대 상황.",
            "파일명에 맞춰 annotator_id를 A 또는 B로 수정한다.",
            "A/B 파일을 복사해 만들 때 annotator_id를 확인한다.",
        ),
        row(
            "annotation",
            "completed_annotation_missing_annotator_id",
            "error",
            "validate_cape_human_review_returns.py",
            "completed 또는 needs_adjudication row에 annotator_id가 없음.",
            "annotator_id를 파일 역할에 맞게 채운다.",
            "완료 상태로 바꾸기 전 annotator_id를 확인한다.",
        ),
        row(
            "annotation",
            "completed_chunk_has_unreviewed_candidate_edges",
            "error",
            "validate_cape_human_review_returns.py",
            "completed row에서 일부 silver candidate edge가 accept/reject 어느 쪽에도 기록되지 않음.",
            "각 candidate를 gold_edges[]에 accept하거나 rejected_candidate_reference_ids[]에 reject로 넣는다.",
            "completed 전 candidate coverage를 모두 확인한다.",
        ),
        row(
            "annotation",
            "completed_chunk_without_accept_or_reject_actions",
            "error",
            "validate_cape_human_review_returns.py",
            "candidate가 있는데 gold_edges와 rejected_candidate_reference_ids가 모두 비어 있음.",
            "모든 candidate를 검토해 accept/reject를 기록한다.",
            "candidate가 있는 row는 빈 completed row로 두지 않는다.",
        ),
        row(
            "annotation",
            "needs_adjudication_missing_comments",
            "error",
            "validate_cape_human_review_returns.py",
            "needs_adjudication으로 표시했지만 comments가 비어 있음.",
            "애매한 이유를 comments에 구체적으로 쓴다.",
            "불확실 row에는 항상 판단 근거/쟁점을 기록한다.",
        ),
        row(
            "adjudication",
            "invalid_adjudication_status",
            "error",
            "import_cape_gold_annotation.py",
            "adjudication_status가 허용값이 아님.",
            f"값을 {', '.join(sorted(ADJUDICATION_STATUSES))} 중 하나로 수정한다.",
            "최종 완료 row는 adjudicated/completed/final 계열만 사용한다.",
        ),
        row(
            "adjudication",
            "adjudicated_gold_nodes_not_list / adjudicated_gold_edges_not_list",
            "error",
            "import_cape_gold_annotation.py",
            "adjudicated_gold_nodes 또는 adjudicated_gold_edges가 list가 아님.",
            "[] 또는 최종 gold item object list로 수정한다.",
            "A/B disagreement를 정리한 최종 list만 남긴다.",
        ),
        row(
            "adjudication",
            "extra_chunks_not_in_draft",
            "error",
            "validate_cape_human_review_returns.py",
            "adjudication_edited.jsonl에 draft에 없는 chunk가 포함됨.",
            "draft에 있는 chunk row만 남긴다.",
            "adjudication_draft.jsonl을 기준으로 편집한다.",
        ),
        row(
            "adjudication",
            "completed_adjudication_missing_adjudicator_id",
            "error",
            "validate_cape_human_review_returns.py",
            "완료 adjudication row에 adjudicator_id가 없음.",
            "adjudicator_id를 채운다.",
            "완료 상태로 바꾸기 전 adjudicator_id를 확인한다.",
        ),
        row(
            "adjudication",
            "completed_adjudication_without_gold_items",
            "warning",
            "import_cape_gold_annotation.py",
            "완료 adjudication row에 gold node/edge가 하나도 없음.",
            "정말 해당 chunk에 gold item이 없는지 확인하고 comments/adjudication_notes로 이유를 남긴다.",
            "무항목 완료 row는 reviewer가 재확인한다.",
        ),
    ]

    for scope, grade_name, grade_values, source in [
        ("mapping", "relevance_grade", MAPPING_GRADES, "import_cape_mapping_review.py"),
        ("crosswalk", "utility_grade", CROSSWALK_GRADES, "import_cape_crosswalk_review.py"),
    ]:
        decisions = MAPPING_DECISIONS if scope == "mapping" else CROSSWALK_DECISIONS
        statuses = MAPPING_STATUSES if scope == "mapping" else CROSSWALK_STATUSES
        explanation_values = MAPPING_EXPLANATION_QUALITY if scope == "mapping" else CROSSWALK_EXPLANATION_QUALITY
        rows.extend(
            [
                row(
                    scope,
                    "reviewed row has no matching original key",
                    "error",
                    source,
                    "reviewed file에 원본 후보 pool에 없는 key 조합이 있음.",
                    "원본 review JSONL/CSV에서 시작해 editable field만 채운다.",
                    "key/id/rank 계열 필드를 수정하지 않는다.",
                ),
                row(
                    scope,
                    "changed immutable field",
                    "error",
                    source,
                    "source/target label, rank, score, support field 등 immutable field가 바뀜.",
                    "원본 후보 파일의 값을 복원한다.",
                    "expert 판단은 decision/grade/comment/status/reviewer_id에만 기록한다.",
                ),
                row(
                    scope,
                    "invalid expert_decision",
                    "error",
                    source,
                    "expert_decision이 허용값이 아님.",
                    f"값을 {', '.join(sorted(decisions))} 중 하나로 수정한다.",
                    "accept/reject 같은 alias는 importer가 일부 normalize하지만 최종 파일은 accepted/rejected/unsure를 사용한다.",
                ),
                row(
                    scope,
                    f"invalid {grade_name}",
                    "error",
                    source,
                    f"{grade_name} 값이 허용 범위를 벗어남.",
                    f"값을 {', '.join(sorted(grade_values))} 중 하나로 수정한다.",
                    "0~3 rubric을 protocol과 맞춰 사용한다.",
                ),
                row(
                    scope,
                    "invalid explanation_quality_score",
                    "error",
                    source,
                    "explanation_quality_score가 허용 범위를 벗어남.",
                    f"값을 {', '.join(sorted(explanation_values))} 중 하나로 수정한다.",
                    "설명 품질 점수는 1~5만 사용한다.",
                ),
                row(
                    scope,
                    "invalid review_status",
                    "error",
                    source,
                    "review_status가 허용값이 아님.",
                    f"값을 {', '.join(sorted(statuses))} 중 하나로 수정한다.",
                    "완료 row는 completed를 기본으로 사용한다.",
                ),
                row(
                    scope,
                    "completed/reviewed but has empty expert_decision",
                    "error",
                    source,
                    "완료로 표시했지만 decision이 비어 있음.",
                    "accepted/rejected/unsure 중 하나를 채운다.",
                    "grade만 채우고 decision을 비우지 않는다.",
                ),
                row(
                    scope,
                    f"completed/reviewed but has empty {grade_name}",
                    "error",
                    source,
                    "완료로 표시했지만 grade가 비어 있음.",
                    f"{grade_name}를 0~3 중 하나로 채운다.",
                    "decision과 grade를 함께 기록한다.",
                ),
                row(
                    scope,
                    "completed/reviewed but has empty explanation_quality_score",
                    "error",
                    source,
                    "완료로 표시했지만 explanation_quality_score가 비어 있음.",
                    "1~5 점수를 채운다.",
                    "모든 completed expert row에는 설명 품질 점수를 포함한다.",
                ),
                row(
                    scope,
                    "completed/reviewed but has empty reviewer_id",
                    "error",
                    source,
                    "완료 row에 reviewer_id가 없음.",
                    "reviewer_id를 채운다.",
                    "검수자별 파일을 만들 때 reviewer_id 기본값을 지정한다.",
                ),
                row(
                    scope,
                    "unsure decision with positive grade",
                    "error",
                    source,
                    "unsure인데 grade가 긍정 수준임.",
                    "정말 긍정이면 accepted로 바꾸고, 애매하면 grade를 낮추고 comment를 남긴다.",
                    "unsure는 불확실성을 뜻하므로 높은 relevance/utility와 함께 쓰지 않는다.",
                ),
                row(
                    scope,
                    "unsure decision but empty comment",
                    "error",
                    source,
                    "unsure인데 이유가 없음.",
                    "comment에 불확실한 이유를 적는다.",
                    "unsure는 항상 설명을 남긴다.",
                ),
                row(
                    scope,
                    "accepted decision with low grade / rejected decision with positive grade",
                    "error",
                    source,
                    "decision과 grade가 서로 모순됨.",
                    "accepted는 높은 grade, rejected는 낮은 grade로 정합성을 맞춘다.",
                    "protocol rubric에 맞춰 decision과 grade를 같이 결정한다.",
                ),
                row(
                    scope,
                    "completed/reviewed without a comment",
                    "warning",
                    source,
                    "완료 row에 comment가 없음.",
                    "가능하면 판단 근거를 comment에 짧게 적는다.",
                    "특히 accepted/unsure는 comment를 남긴다.",
                ),
            ]
        )

    rows.extend(
        [
            row(
                "active_review_effort",
                "missing_required_fields",
                "error",
                "validate_cape_human_review_returns.py",
                "active_review_human_effort.reviewed.csv에 필수 컬럼이 없음.",
                f"필수 컬럼을 모두 포함한다: {', '.join(sorted(ACTIVE_REVIEW_REQUIRED_FIELDS))}.",
                "template CSV의 header를 보존하고 editable 값만 채운다.",
            ),
            row(
                "active_review_effort",
                "duplicate_review_item_ids / extra_review_item_ids",
                "error",
                "validate_cape_human_review_returns.py",
                "review_item_id가 중복되거나 template에 없는 id가 들어감.",
                "template row set으로 되돌리고 중복/extra row를 제거한다.",
                "template 파일을 기준으로 편집한다.",
            ),
            row(
                "active_review_effort",
                "missing_template_rows",
                "warning",
                "validate_cape_human_review_returns.py",
                "template에는 있으나 reviewed CSV에는 없는 row가 있음.",
                "claim을 위해서는 모든 template row를 포함한다.",
                "partial 검수라도 row는 유지하고 미검수 값만 비운다.",
            ),
            row(
                "active_review_effort",
                "invalid_boolean_value",
                "error",
                "validate_cape_human_review_returns.py",
                "boolean field에 허용되지 않는 값이 있음.",
                f"값을 {', '.join(sorted(ACTIVE_REVIEW_ALLOWED_BOOL))} 중 하나로 수정한다.",
                "true/false 또는 1/0를 일관되게 사용한다.",
            ),
            row(
                "active_review_effort",
                "invalid_decision",
                "error",
                "validate_cape_human_review_returns.py",
                "decision 값이 허용 범위를 벗어남.",
                f"값을 {', '.join(sorted(ACTIVE_REVIEW_ALLOWED_DECISIONS))} 중 하나로 수정한다.",
                "correct/incorrect/partial/unsupported/invalid/unsure 중 하나를 사용한다.",
            ),
            row(
                "active_review_effort",
                "negative_review_seconds",
                "error",
                "validate_cape_human_review_returns.py",
                "review_seconds가 음수임.",
                "0보다 큰 실제 검토 시간을 초 단위로 입력한다.",
                "미검수 row는 시간을 비워두고, 검수 row는 양수로 기록한다.",
            ),
            row(
                "active_review_effort",
                "reviewed_row_missing_reviewer_id / reviewed_row_missing_decision",
                "error",
                "validate_cape_human_review_returns.py",
                "검수된 row에 reviewer_id 또는 decision이 없음.",
                "reviewer_id와 decision을 모두 채운다.",
                "한 row라도 검수 값을 넣으면 필수 검수 필드를 모두 채운다.",
            ),
            row(
                "active_review_effort",
                "reviewed_row_missing_positive_review_seconds",
                "error",
                "validate_cape_human_review_returns.py",
                "검수된 row에 양수 review_seconds가 없음.",
                "실제 소요 시간을 초 단위 양수로 입력한다.",
                "active-review efficiency claim에는 timing evidence가 필수다.",
            ),
            row(
                "active_review_effort",
                "reviewed_row_missing_corrected_error / reviewed_row_missing_high_impact_correction",
                "error",
                "validate_cape_human_review_returns.py",
                "검수된 row에 correction flag가 비어 있음.",
                "corrected_error와 high_impact_correction을 true/false 또는 1/0로 채운다.",
                "검수 row의 binary field는 빈칸으로 두지 않는다.",
            ),
            row(
                "active_review_effort",
                "correction_decision_without_corrected_error",
                "error",
                "validate_cape_human_review_returns.py",
                f"decision이 {', '.join(sorted(ACTIVE_REVIEW_CORRECTION_DECISIONS))}인데 corrected_error가 false/blank임.",
                "corrected_error=true로 바꾸거나 decision을 correct로 수정한다.",
                "수정/오류 판단과 corrected_error flag를 같이 맞춘다.",
            ),
            row(
                "active_review_effort",
                "correct_decision_with_corrected_error / high_impact_without_corrected_error",
                "error",
                "validate_cape_human_review_returns.py",
                "decision/impact flag가 서로 모순됨.",
                "correct면 corrected_error=false, high_impact=true면 corrected_error=true가 되게 맞춘다.",
                "high-impact correction은 실제 오류 수정이 있을 때만 표시한다.",
            ),
            row(
                "active_review_effort",
                "active_review_effort_not_complete_for_claim",
                "warning",
                "validate_cape_human_review_returns.py",
                "일부 row 또는 timing이 빠져 active-review claim이 아직 불완전함.",
                "모든 template row를 검수하고 positive review_seconds를 채운다.",
                "partial active-review 결과를 final efficiency claim으로 사용하지 않는다.",
            ),
        ]
    )

    rows.extend(
        [
            row(
                "structural_review",
                "missing_required_fields",
                "error",
                "validate_cape_structural_review_returns.py",
                "reviewed structural CSV에 원본 field 또는 human_decision/human_notes가 없음.",
                "원본 CSV header를 유지하고 human_decision/human_notes를 포함한다.",
                "CSV를 새로 만들지 말고 제공된 worklist를 편집한다.",
            ),
            row(
                "structural_review",
                "row_count_mismatch / missing_input_keys / extra_reviewed_keys",
                "error",
                "validate_cape_structural_review_returns.py",
                "reviewed structural CSV의 row/key set이 원본과 다름.",
                "원본 row set으로 되돌리고 모든 row에 decision을 채운다.",
                "row 삭제/추가 없이 human_decision/human_notes만 수정한다.",
            ),
            row(
                "structural_review",
                "duplicate_reviewed_keys",
                "error",
                "validate_cape_structural_review_returns.py",
                "node_id 또는 gateway_id가 중복됨.",
                "중복 row를 제거하고 원본 key당 하나의 row만 유지한다.",
                "스프레드시트 정렬/복사 과정 후 key 중복을 확인한다.",
            ),
            row(
                "structural_review",
                "missing_human_decision",
                "error",
                "validate_cape_structural_review_returns.py",
                "human_decision이 비어 있음.",
                "허용 decision 중 하나를 선택한다.",
                "모든 structural row는 decision을 갖도록 한다.",
            ),
            row(
                "structural_review",
                "invalid_human_decision",
                "error",
                "validate_cape_structural_review_returns.py",
                "human_decision이 허용값이 아님.",
                "ReviewCheckpoint는 "
                + ", ".join(sorted(CHECKPOINT_ALLOWED))
                + "; Gateway는 "
                + ", ".join(sorted(GATEWAY_ALLOWED))
                + " 중 하나를 사용한다.",
                "action plan의 Allowed Decisions를 그대로 복사한다.",
            ),
            row(
                "structural_review",
                "decision_without_notes",
                "warning",
                "validate_cape_structural_review_returns.py",
                "구조를 바꾸는 decision인데 human_notes가 비어 있음.",
                "원문 근거 또는 판단 이유를 human_notes에 적는다.",
                "accept/add/split/needs_discussion 계열은 notes를 남긴다.",
            ),
        ]
    )
    return rows


def render_md(payload):
    rows = payload["error_rows"]
    by_scope = {}
    for item in rows:
        by_scope.setdefault(item["scope"], []).append(item)

    lines = [
        "# CAPE-KG Human Return Validation Error Playbook",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Claim status: `{payload['claim_status']}`",
        "",
        "이 문서는 human-return 파일을 받은 뒤 preflight/import validator가 내는 대표 error/warning을 coordinator가 빠르게 해석하고 고치기 위한 내부 운영 가이드다. 이 문서 자체는 not human-gold evidence이며, 검수 결과를 대체하지 않는다.",
        "",
        "## When To Use",
        "",
        "1. 반환 파일을 받은 직후 아래 preflight를 실행한다.",
        "2. `error_count`가 1 이상이면 이 playbook에서 error code 또는 message pattern을 찾는다.",
        "3. 파일을 수정한 뒤 preflight를 다시 실행한다.",
        "",
        "```bash",
        "python3 scripts/validate_cape_human_review_returns.py \\",
        "  --experiment-dir experiments/cape_kg_eacl_20260627",
        "```",
        "",
        "Optional structural review:",
        "",
        "```bash",
        "python3 scripts/validate_cape_structural_review_returns.py \\",
        "  --experiment-dir experiments/cape_kg_eacl_20260627",
        "```",
        "",
        "## First Triage Rule",
        "",
        "- `missing_reviewed_file`은 아직 파일이 돌아오지 않았다는 뜻이며, 현재 pre-human 단계에서는 정상적인 pending 상태다.",
        "- `failed_validation`은 반환 파일이 존재하지만 schema/key/decision/coverage 규칙을 만족하지 않는 상태다. 이 경우 apply하지 않는다.",
        "- `warning`은 대부분 claim을 약화시키거나 재확인을 요구하지만, `error`가 없으면 import는 가능할 수 있다. 단, final claim 전에는 warning도 검토한다.",
        "",
        "## Quick Fix Table",
        "",
    ]
    for scope in sorted(by_scope):
        lines += [
            f"### {scope}",
            "",
            "| Error code or pattern | Severity | Common cause | Recommended fix |",
            "| --- | --- | --- | --- |",
        ]
        for item in by_scope[scope]:
            lines.append(
                f"| `{item['error_code_or_pattern']}` | {item['severity']} | "
                f"{item['common_cause']} | {item['recommended_fix']} |"
            )
        lines.append("")

    lines += [
        "## Safe Apply Policy",
        "",
        "반환 파일을 실제 반영하기 전에는 항상 dry-run wrapper를 먼저 실행한다.",
        "",
        "```bash",
        "PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=0 \\",
        "bash scripts/run_cape_human_return_apply.sh",
        "```",
        "",
        "dry-run과 preflight가 모두 통과한 뒤에만 `APPLY_IMPORTS=1`을 사용한다.",
        "",
        "## Claim Boundary",
        "",
        "이 playbook은 오류 수정 절차를 표준화하기 위한 문서다. A/B annotation, IAA, adjudication, expert review, active-effort timing, human-gold scoring이 완료되기 전까지는 최종 논문 성능 claim으로 사용할 수 없다.",
    ]
    return "\n".join(lines) + "\n"


def run(args):
    exp_dir = Path(args.experiment_dir)
    release_dir = exp_dir / "06_release"
    review_dir = exp_dir / "05_review"
    generated_at = datetime.now(timezone.utc).isoformat()
    error_rows = build_rows()
    payload = {
        "generated_at_utc": generated_at,
        "experiment_dir": str(exp_dir),
        "claim_status": "human_return_error_playbook_ready_pending_human_returns",
        "error_rows": error_rows,
        "scope_counts": {scope: sum(1 for row in error_rows if row["scope"] == scope) for scope in sorted({row["scope"] for row in error_rows})},
        "validation_commands": {
            "human_return_preflight": f"python3 scripts/validate_cape_human_review_returns.py --experiment-dir {exp_dir}",
            "structural_return_preflight": f"python3 scripts/validate_cape_structural_review_returns.py --experiment-dir {exp_dir}",
            "dry_run_wrapper": "PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=0 bash scripts/run_cape_human_return_apply.sh",
        },
        "claim_boundary": "not_human_gold_evidence",
    }
    md_path = release_dir / "human_return_validation_error_playbook_ko.md"
    json_path = release_dir / "human_return_validation_error_playbook.json"
    csv_path = review_dir / "human_return_validation_error_codes.csv"
    write_text(md_path, render_md(payload))
    write_json(json_path, payload)
    write_csv(
        csv_path,
        error_rows,
        [
            "scope",
            "error_code_or_pattern",
            "severity",
            "source_script",
            "common_cause",
            "recommended_fix",
            "prevention",
            "applies_to",
        ],
    )
    print(json.dumps({"markdown": str(md_path), "json": str(json_path), "csv": str(csv_path)}, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    run(parser.parse_args())


if __name__ == "__main__":
    main()
