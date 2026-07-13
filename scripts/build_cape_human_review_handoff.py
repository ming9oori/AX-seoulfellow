#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build internal handoff bundles for CAPE-KG human review work."""

import argparse
import hashlib
import json
import tarfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_OUT_DIR = DEFAULT_EXP_DIR / "06_release/human_review_handoff"
ANNOTATORS = ("A", "B")


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path):
    rows = []
    path = Path(path)
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def add_existing(tar, files):
    added = []
    for path in files:
        path = Path(path)
        if path.exists() and path.is_file():
            tar.add(path, arcname=path.as_posix(), recursive=False)
            added.append(path)
    return added


def annotator_readme(exp_dir, annotator, batches, package_name):
    lines = [
        f"# CAPE-KG Annotator {annotator} Handoff",
        "",
        "이 bundle은 내부 human-gold annotation 작업용이다. 원문 기반 chunk text가 들어 있으므로 외부 공개용이 아니다.",
        "",
        "## 목표",
        "",
        f"- annotator `{annotator}`가 priority batch 001-005, 총 100 chunks를 독립적으로 검수한다.",
        "- chunk text만 근거로 candidate edge를 accept/reject한다.",
        "- 빠진 node/edge가 명시적으로 지지되면 추가한다.",
        "- 모든 accepted edge에는 evidence anchor 또는 exact span을 남긴다.",
        "- 완료한 chunk는 `annotation_status`를 `completed`로 둔다. 불확실하면 `needs_adjudication`을 사용한다.",
        "",
        "## 열 파일",
        "",
        f"- Workbench: `{exp_dir}/01_data/gold_annotation/annotation_workbench.html`",
        f"- Schema: `{exp_dir}/01_data/gold_annotation/annotation_schema.json`",
        f"- Annotation guideline: `{exp_dir}/01_data/annotation_guideline_v1.md`",
        f"- Protocol: `{exp_dir}/01_data/gold_annotation/adjudication_protocol.md`",
        f"- Calibration pack: `{exp_dir}/06_release/annotation_calibration_pack_ko.md`",
        f"- Return field guide: `{exp_dir}/06_release/annotation_return_field_guide_ko.md`",
        f"- Validation error playbook: `{exp_dir}/06_release/human_return_validation_error_playbook_ko.md`",
        f"- Master checklist: `{exp_dir}/06_release/human_review_master_checklist_ko.md`",
        f"- First batch execution card: `{exp_dir}/05_review/human_review_first_batch_execution_card_ko.md`",
        f"- Role quickstart: `{exp_dir}/05_review/human_review_role_quickstart_cards_ko.md`",
        f"- Status dashboard: `{exp_dir}/06_release/human_review_status_dashboard_ko.md`",
        f"- Launch checklist: `{exp_dir}/06_release/human_review_launch_checklist_ko.md`",
        f"- Batch review preview summary: `{exp_dir}/06_release/annotation_batch_review_preview_summary.md`",
        "",
        "## Batch Files",
        "",
    ]
    for batch in batches:
        batch_id = batch["batch_id"]
        in_file = batch["annotator_files"][annotator]
        reviewed_file = batch["reviewed_files"][annotator]
        lines += [
            f"### {batch_id}",
            "",
            f"- Input JSONL: `{in_file}`",
            f"- Save reviewed JSONL as: `{reviewed_file}`",
            f"- Tracking sheet: `{batch['tracking_sheet']}`",
            f"- Review preview: `{Path(batch['tracking_sheet']).parent / 'batch_review_preview.md'}`",
            "",
        ]
    lines += [
        "## Return and Apply Flow",
        "",
        "각 batch를 검수한 뒤에는 reviewed filename 그대로 저장하고 coordinator에게 전달한다.",
        "Coordinator는 개별 파일을 바로 apply하지 않고, 전체 반환 파일 preflight와 안전 wrapper를 먼저 실행한다.",
        "",
        "전체 반환 파일 preflight:",
        "",
        "```bash",
        f"python3 scripts/validate_cape_human_review_returns.py --experiment-dir {exp_dir}",
        "```",
        "",
        "전체 dry-run refresh:",
        "",
        "```bash",
        "PYTHON_BIN=python3 \\",
        "LLM_PYTHON=python3 \\",
        "APPLY_IMPORTS=0 \\",
        "bash scripts/run_cape_human_return_apply.sh",
        "```",
        "",
        "preflight와 dry-run이 통과하고 필요한 reviewed file이 모두 있으면 실제 반영:",
        "",
        "```bash",
        "PYTHON_BIN=python3 \\",
        "LLM_PYTHON=python3 \\",
        "APPLY_IMPORTS=1 \\",
        "bash scripts/run_cape_human_return_apply.sh",
        "```",
        "",
        "## Low-Level Debug Import",
        "",
        "아래 단일 파일 import는 특정 batch file을 디버깅할 때만 사용한다. 운영 반영은 위 wrapper를 기본 경로로 사용한다.",
        "",
        "```bash",
        f"python3 scripts/import_cape_gold_annotation.py \\",
        f"  --experiment-dir {exp_dir} \\",
        f"  --target-file {exp_dir}/01_data/gold_annotation/{package_name}/annotator_{annotator}.jsonl \\",
        f"  --reviewed-file <reviewed_jsonl_from_batch> \\",
        "  --allow-partial",
        "```",
        "",
        "논문용 gold로 인정되려면 annotator A/B import, IAA 계산, adjudication, human-gold scoring까지 완료되어야 한다.",
    ]
    return "\n".join(lines) + "\n"


def coordinator_readme(exp_dir, batches):
    lines = [
        "# CAPE-KG Human Review Coordinator Handoff",
        "",
        "이 bundle은 annotator A/B 결과를 import하고 IAA/adjudication을 진행하기 위한 내부 coordinator용 자료다.",
        "",
        "## Minimum Gate",
        "",
        "- two annotators completed: 100 chunks",
        "- adjudicated human-gold chunks: 100+",
        "- adjudicated node/edge/evidence items: 500+",
        "- IAA report computed",
        "- `P_cape_kg_actual` scored against adjudicated gold",
        "",
        "## Core Guidance Files",
        "",
        f"- Annotation guideline: `{exp_dir}/01_data/annotation_guideline_v1.md`",
        f"- Adjudication protocol: `{exp_dir}/01_data/gold_annotation/adjudication_protocol.md`",
        f"- Calibration pack: `{exp_dir}/06_release/annotation_calibration_pack_ko.md`",
        f"- Return field guide: `{exp_dir}/06_release/annotation_return_field_guide_ko.md`",
        f"- Validation error playbook: `{exp_dir}/06_release/human_return_validation_error_playbook_ko.md`",
        f"- Start-here guide: `{exp_dir}/06_release/human_review_start_here_ko.md`",
        f"- Master checklist: `{exp_dir}/06_release/human_review_master_checklist_ko.md`",
        f"- First batch execution card: `{exp_dir}/05_review/human_review_first_batch_execution_card_ko.md`",
        f"- Role quickstart: `{exp_dir}/05_review/human_review_role_quickstart_cards_ko.md`",
        f"- Status dashboard: `{exp_dir}/06_release/human_review_status_dashboard_ko.md`",
        f"- Launch checklist: `{exp_dir}/06_release/human_review_launch_checklist_ko.md`",
        f"- Batch review preview summary: `{exp_dir}/06_release/annotation_batch_review_preview_summary.md`",
        "",
        "## Recommended Return Preflight and Wrapper",
        "",
        "반환 파일을 받으면 먼저 전체 preflight를 실행한다:",
        "",
        "```bash",
        "python3 scripts/validate_cape_human_review_returns.py \\",
        f"  --experiment-dir {exp_dir}",
        "```",
        "",
        "preflight에서 validation error가 없으면 안전 wrapper로 dry-run refresh를 먼저 실행한다:",
        "",
        "```bash",
        "PYTHON_BIN=python3 \\",
        "LLM_PYTHON=python3 \\",
        "APPLY_IMPORTS=0 \\",
        "bash scripts/run_cape_human_return_apply.sh",
        "```",
        "",
        "dry-run과 preflight가 모두 통과하면 반환 파일을 실제 반영한다:",
        "",
        "```bash",
        "PYTHON_BIN=python3 \\",
        "LLM_PYTHON=python3 \\",
        "APPLY_IMPORTS=1 \\",
        "bash scripts/run_cape_human_return_apply.sh",
        "```",
        "",
        "`APPLY_IMPORTS=1`은 reviewed return file이 없으면 기본적으로 거부된다.",
        "",
        "## Low-Level Debug Batch Import Commands",
        "",
        "아래 batch별 명령은 특정 reviewed file 문제를 디버깅할 때만 사용한다. 운영 반영은 위 wrapper를 기본 경로로 사용한다.",
        "",
    ]
    for batch in batches:
        lines.append(f"### {batch['batch_id']}")
        lines.append("")
        for annotator in ANNOTATORS:
            lines += [
                f"Annotator {annotator} single-file dry run:",
                "",
                "```bash",
                batch["import_commands"][annotator]["dry_run"],
                "```",
                "",
                f"Annotator {annotator} single-file apply for debugging only:",
                "",
                "```bash",
                batch["import_commands"][annotator]["apply"],
                "```",
                "",
            ]
    lines += [
        "## Expected Refreshed Files",
        "",
        "확인 파일:",
        "",
        f"- `{exp_dir}/01_data/gold_annotation/iaa_full_120/iaa_summary.json`",
        f"- `{exp_dir}/01_data/gold_annotation/{batches[0]['package']}/adjudication_draft.jsonl`",
        f"- `{exp_dir}/04_evaluation/human_gold_validation_summary.json`",
        f"- `{exp_dir}/06_release/claim_gate_report.md`",
    ]
    return "\n".join(lines) + "\n"


def adjudicator_readme(exp_dir):
    return f"""# CAPE-KG Adjudicator Handoff

이 bundle은 annotator A/B 반환 파일을 import한 뒤 생성되는 adjudication draft를 검수하기 위한 내부 adjudicator용 자료다.

## 열 파일

- Adjudication protocol: `{exp_dir}/01_data/gold_annotation/adjudication_protocol.md`
- Draft JSONL: `{exp_dir}/01_data/gold_annotation/full_120/adjudication_draft.jsonl`
- Draft report: `{exp_dir}/01_data/gold_annotation/full_120/adjudication_draft_report.md`
- Target file: `{exp_dir}/01_data/gold_annotation/full_120/adjudication.jsonl`
- Expected reviewed file: `{exp_dir}/01_data/gold_annotation/full_120/adjudication_edited.jsonl`
- Start-here guide: `{exp_dir}/06_release/human_review_start_here_ko.md`
- Calibration pack: `{exp_dir}/06_release/annotation_calibration_pack_ko.md`
- Return field guide: `{exp_dir}/06_release/annotation_return_field_guide_ko.md`
- Validation error playbook: `{exp_dir}/06_release/human_return_validation_error_playbook_ko.md`
- Master checklist: `{exp_dir}/06_release/human_review_master_checklist_ko.md`
- Status dashboard: `{exp_dir}/06_release/human_review_status_dashboard_ko.md`
- Launch checklist: `{exp_dir}/06_release/human_review_launch_checklist_ko.md`

## Adjudication 규칙

- A/B가 모두 완료된 chunk만 최종 human-gold claim에 사용할 수 있다.
- `disagreement_items`를 확인하고 `adjudicated_gold_nodes`, `adjudicated_gold_edges`를 최종 gold로 정리한다.
- 완료한 chunk는 `adjudication_status`를 `adjudicated`, `completed`, `final`, 또는 `no_disagreement_adjudicated` 중 하나로 둔다.
- 최소 제출 gate를 열려면 completed/adjudicated chunk가 100개 이상이어야 한다.

## Preflight

```bash
python3 scripts/validate_cape_human_review_returns.py \\
  --experiment-dir {exp_dir}
```

## Apply Flow

preflight에서 validation error가 없으면 안전 wrapper로 dry-run refresh를 먼저 실행한다.

```bash
PYTHON_BIN=python3 \\
LLM_PYTHON=python3 \\
APPLY_IMPORTS=0 \\
bash scripts/run_cape_human_return_apply.sh
```

통과하면 `APPLY_IMPORTS=1`로 실제 반영한다.

```bash
PYTHON_BIN=python3 \\
LLM_PYTHON=python3 \\
APPLY_IMPORTS=1 \\
bash scripts/run_cape_human_return_apply.sh
```

## Low-Level Debug Import

아래 단일 파일 import는 adjudication file 문제를 디버깅할 때만 사용한다.

```bash
python3 scripts/import_cape_gold_annotation.py \\
  --experiment-dir {exp_dir} \\
  --target-file {exp_dir}/01_data/gold_annotation/full_120/adjudication.jsonl \\
  --reviewed-file {exp_dir}/01_data/gold_annotation/full_120/adjudication_edited.jsonl \\
  --allow-partial
```
"""


def mapping_readme(exp_dir):
    return f"""# CAPE-KG Mapping Expert Review Handoff

이 bundle은 NCS/PCF mapping downstream claim을 위한 내부 expert review 자료다.

## 열 파일

- Workbench: `{exp_dir}/01_data/mapping_review/mapping_review_workbench.html`
- Protocol: `{exp_dir}/01_data/mapping_review/mapping_review_protocol.md`
- Review JSONL: `{exp_dir}/01_data/mapping_review/mapping_review_items.jsonl`
- Group briefing: `{exp_dir}/06_release/mapping_review_group_briefing.md`
- Group briefing CSV: `{exp_dir}/05_review/mapping_review_group_briefing_top20.csv`
- Next 20 groups: `{exp_dir}/05_review/mapping_review_next_20_groups.csv`
- Next 60 rows: `{exp_dir}/05_review/mapping_review_next_60_rows.csv`
- Validation error playbook: `{exp_dir}/06_release/human_return_validation_error_playbook_ko.md`
- Master checklist: `{exp_dir}/06_release/human_review_master_checklist_ko.md`
- Status dashboard: `{exp_dir}/06_release/human_review_status_dashboard_ko.md`
- Launch checklist: `{exp_dir}/06_release/human_review_launch_checklist_ko.md`

## Review 규칙

- source task + standard별 Top-5 후보 5개를 하나의 group으로 본다.
- `mapping_review_group_briefing.md`에서 Top-20 group의 Top-5 후보를 먼저 비교한다.
- group 5개 row가 모두 `review_status=completed`가 되어야 P@K/MRR 계산에 들어간다.
- decision은 `accepted`, `rejected`, `unsure` 중 하나를 사용한다.
- `relevance_grade`는 0, 1, 2, 3 중 하나를 사용한다.

## Apply Flow

```bash
python3 scripts/validate_cape_human_review_returns.py \\
  --experiment-dir {exp_dir}
```

통과하면 안전 wrapper로 dry-run refresh를 먼저 실행한다.

```bash
PYTHON_BIN=python3 \\
LLM_PYTHON=python3 \\
APPLY_IMPORTS=0 \\
bash scripts/run_cape_human_return_apply.sh
```

dry-run과 preflight가 모두 통과하면 `APPLY_IMPORTS=1`로 실제 반영한다.

```bash
PYTHON_BIN=python3 \\
LLM_PYTHON=python3 \\
APPLY_IMPORTS=1 \\
bash scripts/run_cape_human_return_apply.sh
```

## Low-Level Debug Import

아래 단일 파일 import는 mapping reviewed file 문제를 디버깅할 때만 사용한다.

```bash
python3 scripts/import_cape_mapping_review.py \\
  --experiment-dir {exp_dir} \\
  --reviewed-file {exp_dir}/01_data/mapping_review/mapping_review_items.reviewed.jsonl
```
"""


def crosswalk_readme(exp_dir):
    return f"""# CAPE-KG NCS-PCF Crosswalk Expert Review Handoff

이 bundle은 Layer2 task를 매개로 생성된 NCS-PCF crosswalk 후보를 검수하기 위한 내부 expert review 자료다.

## 열 파일

- Protocol: `{exp_dir}/01_data/crosswalk_review/crosswalk_review_protocol.md`
- Review JSONL: `{exp_dir}/01_data/crosswalk_review/crosswalk_review_items.jsonl`
- Review CSV sheet: `{exp_dir}/01_data/crosswalk_review/crosswalk_review_sheet.csv`
- Manifest: `{exp_dir}/01_data/crosswalk_review/crosswalk_review_manifest.json`
- Candidate report: `{exp_dir}/04_evaluation/ncs_pcf_crosswalk_report.md`
- Candidate CSV: `{exp_dir}/04_evaluation/ncs_pcf_crosswalk_candidates.csv`
- Expert metrics report: `{exp_dir}/04_evaluation/crosswalk_expert_evaluation_report.md`
- Validation error playbook: `{exp_dir}/06_release/human_return_validation_error_playbook_ko.md`
- Master checklist: `{exp_dir}/06_release/human_review_master_checklist_ko.md`
- Status dashboard: `{exp_dir}/06_release/human_review_status_dashboard_ko.md`
- Launch checklist: `{exp_dir}/06_release/human_review_launch_checklist_ko.md`

## Review 규칙

- 각 row는 하나의 Layer2 업무를 공유하는 NCS 후보와 PCF 후보의 pair다.
- `expert_decision`은 `accepted`, `rejected`, `unsure` 중 하나를 사용한다.
- `utility_grade`는 0, 1, 2, 3 중 하나를 사용한다.
- `explanation_quality_score`는 1, 2, 3, 4, 5 중 하나를 사용한다.
- 완료 row는 `review_status=completed`, `reviewer_id`, `comment`를 포함해야 한다.
- 완료 파일은 정확히 `{exp_dir}/01_data/crosswalk_review/crosswalk_review_items.reviewed.jsonl` 경로명으로 저장한다.

## Apply Flow

```bash
python3 scripts/validate_cape_human_review_returns.py \\
  --experiment-dir {exp_dir}
```

통과하면 안전 wrapper로 dry-run refresh를 먼저 실행한다.

```bash
PYTHON_BIN=python3 \\
LLM_PYTHON=python3 \\
APPLY_IMPORTS=0 \\
bash scripts/run_cape_human_return_apply.sh
```

dry-run과 preflight가 모두 통과하면 `APPLY_IMPORTS=1`로 실제 반영한다.

```bash
PYTHON_BIN=python3 \\
LLM_PYTHON=python3 \\
APPLY_IMPORTS=1 \\
bash scripts/run_cape_human_return_apply.sh
```

## Low-Level Debug Import

```bash
python3 scripts/import_cape_crosswalk_review.py \\
  --experiment-dir {exp_dir} \\
  --reviewed-file {exp_dir}/01_data/crosswalk_review/crosswalk_review_items.reviewed.jsonl
```

이 crosswalk review는 mapping expert review와 별개다. NCS/PCF 개별 Top-K mapping claim은 mapping expert review가, NCS-PCF pair utility claim은 이 crosswalk review가 필요하다.
"""


def active_review_readme(exp_dir):
    return f"""# CAPE-KG Active Review Human-Effort Handoff

이 bundle은 active-review efficiency claim을 검증하기 위한 reviewer effort/timing 수집 자료다.

## 열 파일

- Plan: `{exp_dir}/06_release/active_review_human_effort_plan.md`
- Briefing: `{exp_dir}/06_release/active_review_human_effort_briefing.md`
- Briefing CSV: `{exp_dir}/05_review/active_review_human_effort_briefing.csv`
- Template CSV: `{exp_dir}/05_review/active_review_human_effort_template.csv`
- Expected reviewed CSV: `{exp_dir}/05_review/active_review_human_effort.reviewed.csv`
- Active-review queue: `{exp_dir}/05_review/actual_llm_active_review_queue_P_cape_kg_actual.csv`
- Silver diagnostic report: `{exp_dir}/04_evaluation/active_review_efficiency_report.md`
- Validation error playbook: `{exp_dir}/06_release/human_return_validation_error_playbook_ko.md`
- Master checklist: `{exp_dir}/06_release/human_review_master_checklist_ko.md`
- Status dashboard: `{exp_dir}/06_release/human_review_status_dashboard_ko.md`
- Launch checklist: `{exp_dir}/06_release/human_review_launch_checklist_ko.md`

## Review 규칙

- `active_review_human_effort_template.csv`를 열고 각 row를 한 번씩 검토한다.
- `active_review_human_effort_briefing.md`와 `active_review_human_effort_briefing.csv`를 먼저 확인해 high-impact/evidence/schema 항목 순서로 검토한다.
- `reviewer_id`, `review_seconds`, `decision`, `corrected_error`, `high_impact_correction`을 반드시 채운다.
- `decision`은 `correct`, `incorrect`, `partial`, `unsupported`, `invalid`, `unsure` 중 하나를 사용한다.
- `corrected_error=true`는 reviewer가 후보를 수정/거절/부분수정한 경우에 사용한다.
- `high_impact_correction=true`는 evidence, schema, risk, gateway, central task-flow에 영향을 주는 수정에 사용한다.
- 완료 파일은 정확히 `{exp_dir}/05_review/active_review_human_effort.reviewed.csv` 경로명으로 저장한다.

## Preflight

```bash
python3 scripts/validate_cape_human_review_returns.py \\
  --experiment-dir {exp_dir}
```

## Metrics Refresh

preflight 통과 후 안전 wrapper dry-run을 실행하면 `04_evaluation/active_review_human_effort_metrics.json`과 paper tables 갱신 가능 여부를 확인한다.

```bash
PYTHON_BIN=python3 \\
LLM_PYTHON=python3 \\
APPLY_IMPORTS=0 \\
bash scripts/run_cape_human_return_apply.sh
```

dry-run과 preflight가 모두 통과하면 `APPLY_IMPORTS=1`로 실제 반영한다.

```bash
PYTHON_BIN=python3 \\
LLM_PYTHON=python3 \\
APPLY_IMPORTS=1 \\
bash scripts/run_cape_human_return_apply.sh
```

이 파일은 human-gold annotation을 대체하지 않는다. Active-review efficiency claim은 reviewer effort/timing과 adjudicated gold outcome alignment가 모두 있어야 논문 주장으로 사용할 수 있다.
"""


def structural_review_readme(exp_dir):
    return f"""# CAPE-KG Optional Structural Review Handoff

이 bundle은 KG structural diagnostics에서 나온 ReviewCheckpoint 후보와 DecisionGateway branch gap을 선택적으로 검수하기 위한 내부 자료다.

## 열 파일

- Action plan: `{exp_dir}/06_release/structural_review_action_plan.md`
- Return preflight: `{exp_dir}/06_release/structural_review_return_preflight.md`
- Dry-run application plan: `{exp_dir}/06_release/structural_review_application_plan.md`
- ReviewCheckpoint candidates: `{exp_dir}/05_review/structural_review_checkpoint_candidates.csv`
- Gateway branch gaps: `{exp_dir}/05_review/structural_gateway_branch_gaps.csv`
- Dry-run application actions: `{exp_dir}/05_review/structural_review_application_actions.csv`
- Optional return list: `{exp_dir}/05_review/structural_review_optional_returns.csv`
- Validation error playbook: `{exp_dir}/06_release/human_return_validation_error_playbook_ko.md`
- Master checklist: `{exp_dir}/06_release/human_review_master_checklist_ko.md`
- Status dashboard: `{exp_dir}/06_release/human_review_status_dashboard_ko.md`
- Launch checklist: `{exp_dir}/06_release/human_review_launch_checklist_ko.md`

## 저장할 파일

- ReviewCheckpoint reviewed CSV: `{exp_dir}/05_review/structural_review_checkpoint_candidates.reviewed.csv`
- Gateway branch reviewed CSV: `{exp_dir}/05_review/structural_gateway_branch_gaps.reviewed.csv`

## Review 규칙

- ReviewCheckpoint 후보는 실제 검토/승인/품질관문 활동일 때만 `accept_review_checkpoint`로 표시한다.
- 단순히 "리뷰"라는 단어가 들어간 일반 업무는 `keep_current_type` 또는 `reject_candidate`로 표시한다.
- Gateway branch gap은 원문 근거가 명시적인 분기 결과를 지지할 때만 `add_branches_to`로 표시한다.
- 애매한 row는 `needs_discussion`으로 남긴다.
- reviewed CSV가 돌아오기 전에는 KG를 자동 수정하지 않는다.

## Preflight

```bash
python3 scripts/validate_cape_structural_review_returns.py \\
  --experiment-dir {exp_dir}
```

## Dry-run Application Plan

```bash
python3 scripts/build_cape_structural_review_application_plan.py \\
  --experiment-dir {exp_dir}
```

이 계획서는 reviewed CSV의 `human_decision`을 manual KG update 제안으로 변환하지만, KG를 자동 수정하지 않는다.

이 structural review는 minimum paper-gate의 annotation/adjudication 반환 파일을 대체하지 않는다. 논문 최종 성능 claim에는 human-gold annotation, IAA, adjudication, proposed human-gold scoring이 별도로 필요하다.
"""


def strong_resegmented_manifest(exp_dir):
    root = Path(exp_dir) / "01_data/gold_annotation"
    expansion = read_json(root / "annotation_expansion_manifest.json", {}) or {}
    package_name = expansion.get("strong_resegmented_package") or ""
    package_dir = root / package_name if package_name else None
    if not package_name or not package_dir or not package_dir.exists():
        return {
            "available": False,
            "reason": "strong_resegmented_package_missing",
            "package": package_name,
        }

    annotator_a = package_dir / "annotator_A.jsonl"
    annotator_b = package_dir / "annotator_B.jsonl"
    adjudication = package_dir / "adjudication.jsonl"
    rows_a = read_jsonl(annotator_a)
    candidate_counts = [int(row.get("silver_candidate_edge_count") or 0) for row in rows_a]
    split_sentence_counts = [len(row.get("split_sentence_ids") or row.get("sentence_ids") or []) for row in rows_a]
    return {
        "available": True,
        "package": package_name,
        "package_dir": str(package_dir),
        "rows": len(rows_a),
        "annotator_A_file": str(annotator_a),
        "annotator_B_file": str(annotator_b),
        "adjudication_template_file": str(adjudication),
        "tracking_sheet": str(package_dir / "tracking_sheet.csv"),
        "review_preview_csv": str(package_dir / "strong_review_preview.csv"),
        "review_preview_md": str(package_dir / "strong_review_preview.md"),
        "review_preview_summary_json": str(Path(exp_dir) / "06_release/strong_resegmented_review_preview_summary.json"),
        "review_preview_summary_md": str(Path(exp_dir) / "06_release/strong_resegmented_review_preview_summary.md"),
        "expected_reviewed_files": {
            "annotator_A": str(package_dir / "annotator_A_edited.jsonl"),
            "annotator_B": str(package_dir / "annotator_B_edited.jsonl"),
            "adjudication": str(package_dir / "adjudication_edited.jsonl"),
        },
        "candidate_edges_total": sum(candidate_counts),
        "chunks_with_silver_candidates": sum(1 for count in candidate_counts if count > 0),
        "candidate_edges_min": min(candidate_counts) if candidate_counts else 0,
        "candidate_edges_max": max(candidate_counts) if candidate_counts else 0,
        "max_split_sentence_count": max(split_sentence_counts) if split_sentence_counts else 0,
        "source_chunk_count": len({row.get("source_chunk_id") for row in rows_a if row.get("source_chunk_id")}),
        "strong_300_chunk_gap_after_resegmentation": expansion.get("strong_300_chunk_gap_after_resegmentation"),
        "claim_status": "optional_strong_review_handoff_ready_pending_human_review",
    }


def strong_resegmented_readme(exp_dir, manifest):
    package_name = manifest.get("package")
    package_dir = manifest.get("package_dir")
    return f"""# CAPE-KG Optional Strong 300+ Review Handoff

이 bundle은 strong-accept 목표인 300~500 chunk human-gold annotation을 준비하기 위한 선택 검수 자료다.
현재 minimum gate의 annotation/adjudication 반환 파일을 대체하지 않는다. 논문에서 300+ adjudicated chunk로 주장하려면 이 bundle의 A/B 검수, IAA, adjudication, scoring이 실제로 완료되어야 한다.

## Package

- Package: `{package_name}`
- Package directory: `{package_dir}`
- Review units: {manifest.get('rows')}
- Source chunks represented: {manifest.get('source_chunk_count')}
- Max source sentences per review unit: {manifest.get('max_split_sentence_count')}
- Units with silver candidates: {manifest.get('chunks_with_silver_candidates')}
- Candidate edges total: {manifest.get('candidate_edges_total')}
- Strong 300 chunk gap after resegmentation: {manifest.get('strong_300_chunk_gap_after_resegmentation')}

각 review unit은 `source_chunk_id`와 `split_sentence_ids`를 가진다. 따라서 검수 단위가 재분할되었더라도 원래 Layer2 chunk와 source sentence로 다시 추적할 수 있다.

## Input Files

- Annotator A input: `{manifest.get('annotator_A_file')}`
- Annotator B input: `{manifest.get('annotator_B_file')}`
- Adjudication template: `{manifest.get('adjudication_template_file')}`
- Tracking sheet: `{manifest.get('tracking_sheet')}`
- Strong review preview: `{manifest.get('review_preview_md')}`
- Strong review preview summary: `{manifest.get('review_preview_summary_md')}`
- Annotation guideline: `{exp_dir}/01_data/annotation_guideline_v1.md`
- Annotation schema: `{exp_dir}/01_data/gold_annotation/annotation_schema.json`
- Adjudication protocol: `{exp_dir}/01_data/gold_annotation/adjudication_protocol.md`
- Return field guide: `{exp_dir}/06_release/annotation_return_field_guide_ko.md`
- Validation error playbook: `{exp_dir}/06_release/human_return_validation_error_playbook_ko.md`
- Expansion report: `{exp_dir}/01_data/gold_annotation/annotation_expansion_report.md`
- Status dashboard: `{exp_dir}/06_release/human_review_status_dashboard_ko.md`
- Launch checklist: `{exp_dir}/06_release/human_review_launch_checklist_ko.md`

## Expected Reviewed Files

- Annotator A reviewed file: `{manifest.get('expected_reviewed_files', {}).get('annotator_A')}`
- Annotator B reviewed file: `{manifest.get('expected_reviewed_files', {}).get('annotator_B')}`
- Adjudicator reviewed file: `{manifest.get('expected_reviewed_files', {}).get('adjudication')}`

## Review Rules

- Annotator A/B는 독립적으로 같은 342개 review unit을 검수한다.
- candidate edge는 원문 split text와 evidence anchor가 지지할 때만 gold edge로 복사한다.
- `strong_review_preview.md`에서 dense candidate unit과 evidence span repair 대상 unit을 먼저 확인한다.
- 빠진 node/edge가 split text에서 직접 지지되면 추가한다.
- 모든 accepted edge에는 evidence anchor 또는 exact span을 남긴다.
- 완료 row의 `annotation_status`는 `completed` 또는 `needs_adjudication`으로 둔다.
- 애매한 경우에는 임의로 확정하지 말고 `comments`나 `missing_but_supported_notes`에 이유를 남긴다.

## Dry-run Import Commands

Before import dry runs, validate the optional strong return package:

```bash
python3 scripts/validate_cape_strong_review_returns.py \\
  --experiment-dir {exp_dir}
```

## Safe Apply Wrapper

운영 반영은 개별 import 명령보다 strong 전용 wrapper를 기본 경로로 사용한다. 먼저 dry-run을 실행한다.

```bash
PYTHON_BIN=python3 \\
APPLY_IMPORTS=0 \\
bash scripts/run_cape_strong_return_apply.sh
```

preflight와 dry-run이 통과하고 reviewed file이 있으면 실제 반영한다.

```bash
PYTHON_BIN=python3 \\
APPLY_IMPORTS=1 \\
bash scripts/run_cape_strong_return_apply.sh
```

`APPLY_IMPORTS=1`은 reviewed strong return file이 없으면 기본적으로 거부된다.

Annotator A:

```bash
python3 scripts/import_cape_gold_annotation.py \\
  --experiment-dir {exp_dir} \\
  --target-file {manifest.get('annotator_A_file')} \\
  --reviewed-file {manifest.get('expected_reviewed_files', {}).get('annotator_A')} \\
  --report-file {package_dir}/annotator_A_strong_import_report.json \\
  --allow-partial
```

Annotator B:

```bash
python3 scripts/import_cape_gold_annotation.py \\
  --experiment-dir {exp_dir} \\
  --target-file {manifest.get('annotator_B_file')} \\
  --reviewed-file {manifest.get('expected_reviewed_files', {}).get('annotator_B')} \\
  --report-file {package_dir}/annotator_B_strong_import_report.json \\
  --allow-partial
```

Dry run이 통과하면 위 명령에 `--apply`를 붙여 반영한다.

## IAA and Adjudication

```bash
python3 scripts/compute_cape_annotation_iaa.py \\
  --annotator-a {manifest.get('annotator_A_file')} \\
  --annotator-b {manifest.get('annotator_B_file')} \\
  --output-dir {package_dir}/iaa_strong_resegmented

python3 scripts/prepare_cape_adjudication_draft.py \\
  --experiment-dir {exp_dir} \\
  --package {package_name}
```

Adjudicator가 `{package_dir}/adjudication_draft.jsonl`을 검토한 뒤 `{manifest.get('expected_reviewed_files', {}).get('adjudication')}`로 저장한다.

Adjudication dry run:

```bash
python3 scripts/import_cape_gold_annotation.py \\
  --experiment-dir {exp_dir} \\
  --target-file {manifest.get('adjudication_template_file')} \\
  --reviewed-file {manifest.get('expected_reviewed_files', {}).get('adjudication')} \\
  --report-file {package_dir}/adjudication_strong_import_report.json \\
  --allow-partial
```

통과하면 `--apply`를 붙인다. 이 optional strong package는 현재 post-refresh 자동 import 대상이 아니므로, 수동 검증 후 별도 claim table에 반영해야 한다.
"""


def manifest_for_annotator(exp_dir, annotator, batches):
    chunk_ids = []
    rows_total = 0
    candidate_edges_total = 0
    status_counts = Counter()
    batch_rows = []
    for batch in batches:
        rows = read_jsonl(batch["annotator_files"][annotator])
        row_chunk_ids = [row.get("chunk_id") for row in rows]
        chunk_ids.extend(row_chunk_ids)
        rows_total += len(rows)
        candidate_edges = sum(int(row.get("silver_candidate_edge_count") or 0) for row in rows)
        candidate_edges_total += candidate_edges
        status_counts.update(row.get("annotation_status", "") for row in rows)
        batch_rows.append(
            {
                "batch_id": batch["batch_id"],
                "input_file": batch["annotator_files"][annotator],
                "reviewed_file": batch["reviewed_files"][annotator],
                "rows": len(rows),
                "candidate_edges": candidate_edges,
                "chunk_ids": row_chunk_ids,
            }
        )
    return {
        "annotator": annotator,
        "package": batches[0]["package"] if batches else "",
        "rows": rows_total,
        "unique_chunks": len(set(chunk_ids)),
        "duplicate_chunk_count": rows_total - len(set(chunk_ids)),
        "candidate_edges_total": candidate_edges_total,
        "status_counts": dict(status_counts),
        "batches": batch_rows,
        "ready_for_minimum_gate": rows_total >= 100 and len(set(chunk_ids)) >= 100,
    }


def batch_manifest_path(batch):
    return str(Path(batch["readme"]).parent / "batch_manifest.json")


def build_tar(path, files, generated_files):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(path, "w:gz") as tar:
        added = add_existing(tar, files)
        added += add_existing(tar, generated_files)
    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "file_count": len(added),
    }


def run(args):
    exp_dir = Path(args.experiment_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = read_json(exp_dir / "06_release/annotation_batch_assignment_summary.json", {})
    batches = summary.get("batches", [])[: args.batch_count]
    if not batches:
        raise SystemExit("No batches found in annotation_batch_assignment_summary.json")

    generated_at = datetime.now(timezone.utc).isoformat()
    common_files = [
        exp_dir / "01_data/annotation_guideline_v1.md",
        exp_dir / "01_data/gold_annotation/annotation_workbench.html",
        exp_dir / "01_data/gold_annotation/annotation_schema.json",
        exp_dir / "01_data/gold_annotation/adjudication_protocol.md",
        exp_dir / "06_release/human_review_start_here_ko.md",
        exp_dir / "06_release/human_review_claim_gate_one_page_ko.md",
        exp_dir / "06_release/annotation_calibration_pack_ko.md",
        exp_dir / "06_release/annotation_calibration_pack.json",
        exp_dir / "06_release/annotation_return_field_guide_ko.md",
        exp_dir / "06_release/annotation_return_field_guide.json",
        exp_dir / "05_review/annotation_return_field_checklist.csv",
        exp_dir / "06_release/human_return_validation_error_playbook_ko.md",
        exp_dir / "06_release/human_return_validation_error_playbook.json",
        exp_dir / "05_review/human_return_validation_error_codes.csv",
        exp_dir / "05_review/annotation_calibration_examples.csv",
        exp_dir / "06_release/annotation_batch_assignment_report.md",
        exp_dir / "06_release/annotation_progress_report.md",
        exp_dir / "06_release/annotation_batch_review_preview_summary.json",
        exp_dir / "06_release/annotation_batch_review_preview_summary.md",
        exp_dir / "06_release/active_review_human_effort_plan.md",
        exp_dir / "06_release/active_review_human_effort_briefing.md",
        exp_dir / "06_release/active_review_human_effort_briefing.json",
        exp_dir / "06_release/human_review_master_checklist_ko.md",
        exp_dir / "06_release/human_review_master_checklist_ko.json",
        exp_dir / "05_review/human_review_first_batch_execution_card_ko.md",
        exp_dir / "05_review/human_review_first_batch_execution_card.json",
        exp_dir / "06_release/human_review_status_dashboard_ko.md",
        exp_dir / "06_release/human_review_status_dashboard_ko.json",
        exp_dir / "06_release/human_review_launch_checklist_ko.md",
        exp_dir / "06_release/human_review_launch_checklist_ko.json",
        exp_dir / "05_review/human_gate_required_returns.csv",
        exp_dir / "05_review/human_review_gate_dependency_matrix.csv",
        exp_dir / "05_review/human_review_master_return_files.csv",
        exp_dir / "05_review/human_review_status_next_actions.csv",
        exp_dir / "05_review/human_review_minimum_gate_launch_tasks.csv",
        exp_dir / "05_review/human_review_role_quickstart_cards_ko.md",
        exp_dir / "05_review/human_review_role_quickstart_cards.json",
        exp_dir / "05_review/human_review_role_quickstart_cards.csv",
        exp_dir / "05_review/annotation_batch_review_preview_summary.csv",
        exp_dir / "05_review/active_review_human_effort_template.csv",
        exp_dir / "05_review/active_review_human_effort_briefing.csv",
        exp_dir / "05_review/human_gold_batches/full_120_batch_assignment_overview.csv",
        Path("scripts/build_cape_active_review_human_effort.py"),
        Path("scripts/build_cape_annotation_batch_review_preview.py"),
        Path("scripts/build_cape_annotation_return_field_guide.py"),
        Path("scripts/build_cape_human_return_error_playbook.py"),
        Path("scripts/build_cape_human_review_status_dashboard.py"),
        Path("scripts/build_cape_human_review_first_batch_card.py"),
        Path("scripts/build_cape_human_review_role_quickstart.py"),
        Path("scripts/build_cape_human_review_launch_checklist.py"),
        Path("scripts/import_cape_gold_annotation.py"),
        Path("scripts/compute_cape_annotation_iaa.py"),
        Path("scripts/prepare_cape_adjudication_draft.py"),
        Path("scripts/validate_cape_human_review_returns.py"),
        Path("scripts/run_cape_human_return_apply.sh"),
        Path("scripts/run_cape_post_annotation_refresh.sh"),
    ]

    annotator_payloads = {}
    bundles = {}
    generated_files = []
    for annotator in ANNOTATORS:
        annotator_manifest = manifest_for_annotator(exp_dir, annotator, batches)
        annotator_payloads[annotator] = annotator_manifest
        readme_path = out_dir / f"README_annotator_{annotator}_ko.md"
        manifest_path = out_dir / f"annotator_{annotator}_priority100_manifest.json"
        write_text(readme_path, annotator_readme(exp_dir, annotator, batches, annotator_manifest["package"]))
        write_json(manifest_path, {"generated_at_utc": generated_at, **annotator_manifest})
        generated_files.extend([readme_path, manifest_path])
        batch_files = []
        for batch in batches:
            batch_files.extend(
                [
                    batch["readme"],
                    batch["tracking_sheet"],
                    str(Path(batch["tracking_sheet"]).parent / "batch_review_preview.csv"),
                    str(Path(batch["tracking_sheet"]).parent / "batch_review_preview.md"),
                    batch["annotator_files"][annotator],
                    batch_manifest_path(batch),
                ]
            )
        bundles[f"annotator_{annotator}"] = build_tar(
            out_dir / f"cape_human_gold_annotator_{annotator}_priority100.tar.gz",
            common_files + batch_files,
            [readme_path, manifest_path],
        )

    coordinator_readme_path = out_dir / "README_coordinator_ko.md"
    write_text(coordinator_readme_path, coordinator_readme(exp_dir, batches))
    coordinator_files = list(common_files)
    for batch in batches:
        coordinator_files.extend(
            [
                batch["readme"],
                batch["tracking_sheet"],
                str(Path(batch["tracking_sheet"]).parent / "batch_review_preview.csv"),
                str(Path(batch["tracking_sheet"]).parent / "batch_review_preview.md"),
                batch["annotator_files"]["A"],
                batch["annotator_files"]["B"],
                batch_manifest_path(batch),
            ]
        )
    bundles["coordinator"] = build_tar(
        out_dir / "cape_human_gold_coordinator_priority100.tar.gz",
        coordinator_files,
        generated_files + [coordinator_readme_path],
    )

    adjudicator_readme_path = out_dir / "README_adjudicator_ko.md"
    write_text(adjudicator_readme_path, adjudicator_readme(exp_dir))
    adjudicator_files = [
        exp_dir / "01_data/annotation_guideline_v1.md",
        exp_dir / "01_data/gold_annotation/adjudication_protocol.md",
        exp_dir / "01_data/gold_annotation/annotation_schema.json",
        exp_dir / "01_data/gold_annotation/full_120/adjudication_draft.jsonl",
        exp_dir / "01_data/gold_annotation/full_120/adjudication_draft_report.md",
        exp_dir / "01_data/gold_annotation/full_120/adjudication_draft_summary.json",
        exp_dir / "01_data/gold_annotation/full_120/adjudication.jsonl",
        exp_dir / "06_release/human_review_start_here_ko.md",
        exp_dir / "06_release/human_review_claim_gate_one_page_ko.md",
        exp_dir / "06_release/annotation_calibration_pack_ko.md",
        exp_dir / "06_release/annotation_calibration_pack.json",
        exp_dir / "06_release/annotation_return_field_guide_ko.md",
        exp_dir / "06_release/annotation_return_field_guide.json",
        exp_dir / "05_review/annotation_return_field_checklist.csv",
        exp_dir / "06_release/human_return_validation_error_playbook_ko.md",
        exp_dir / "06_release/human_return_validation_error_playbook.json",
        exp_dir / "05_review/human_return_validation_error_codes.csv",
        exp_dir / "05_review/annotation_calibration_examples.csv",
        exp_dir / "06_release/human_review_master_checklist_ko.md",
        exp_dir / "06_release/human_review_master_checklist_ko.json",
        exp_dir / "06_release/human_review_status_dashboard_ko.md",
        exp_dir / "06_release/human_review_status_dashboard_ko.json",
        exp_dir / "06_release/human_review_launch_checklist_ko.md",
        exp_dir / "06_release/human_review_launch_checklist_ko.json",
        exp_dir / "05_review/human_gate_required_returns.csv",
        exp_dir / "05_review/human_review_gate_dependency_matrix.csv",
        exp_dir / "05_review/human_review_master_return_files.csv",
        exp_dir / "05_review/human_review_status_next_actions.csv",
        exp_dir / "05_review/human_review_minimum_gate_launch_tasks.csv",
        exp_dir / "05_review/human_review_role_quickstart_cards_ko.md",
        exp_dir / "05_review/human_review_role_quickstart_cards.json",
        exp_dir / "05_review/human_review_role_quickstart_cards.csv",
        Path("scripts/build_cape_human_review_status_dashboard.py"),
        Path("scripts/build_cape_annotation_return_field_guide.py"),
        Path("scripts/build_cape_human_return_error_playbook.py"),
        Path("scripts/build_cape_human_review_role_quickstart.py"),
        Path("scripts/build_cape_human_review_launch_checklist.py"),
        Path("scripts/import_cape_gold_annotation.py"),
        Path("scripts/validate_cape_human_review_returns.py"),
        Path("scripts/run_cape_human_return_apply.sh"),
        Path("scripts/run_cape_post_annotation_refresh.sh"),
    ]
    bundles["adjudicator"] = build_tar(
        out_dir / "cape_human_gold_adjudicator_full120.tar.gz",
        adjudicator_files,
        [adjudicator_readme_path],
    )

    mapping_readme_path = out_dir / "README_mapping_expert_ko.md"
    write_text(mapping_readme_path, mapping_readme(exp_dir))
    mapping_files = [
        exp_dir / "01_data/mapping_review/mapping_review_workbench.html",
        exp_dir / "01_data/mapping_review/mapping_review_protocol.md",
        exp_dir / "01_data/mapping_review/mapping_review_items.jsonl",
        exp_dir / "01_data/mapping_review/mapping_review_sheet.csv",
        exp_dir / "01_data/mapping_review/mapping_review_manifest.json",
        exp_dir / "06_release/mapping_review_group_briefing.md",
        exp_dir / "06_release/mapping_review_group_briefing.json",
        exp_dir / "06_release/human_review_claim_gate_one_page_ko.md",
        exp_dir / "05_review/mapping_review_group_briefing_top20.csv",
        exp_dir / "05_review/mapping_review_next_20_groups.csv",
        exp_dir / "05_review/mapping_review_next_60_rows.csv",
        exp_dir / "06_release/mapping_review_progress_report.md",
        exp_dir / "06_release/mapping_review_progress_summary.json",
        exp_dir / "06_release/human_return_validation_error_playbook_ko.md",
        exp_dir / "06_release/human_return_validation_error_playbook.json",
        exp_dir / "05_review/human_return_validation_error_codes.csv",
        exp_dir / "06_release/human_review_master_checklist_ko.md",
        exp_dir / "06_release/human_review_master_checklist_ko.json",
        exp_dir / "06_release/human_review_status_dashboard_ko.md",
        exp_dir / "06_release/human_review_status_dashboard_ko.json",
        exp_dir / "06_release/human_review_launch_checklist_ko.md",
        exp_dir / "06_release/human_review_launch_checklist_ko.json",
        exp_dir / "05_review/human_gate_required_returns.csv",
        exp_dir / "05_review/human_review_gate_dependency_matrix.csv",
        exp_dir / "05_review/human_review_master_return_files.csv",
        exp_dir / "05_review/human_review_status_next_actions.csv",
        exp_dir / "05_review/human_review_minimum_gate_launch_tasks.csv",
        exp_dir / "05_review/human_review_role_quickstart_cards_ko.md",
        exp_dir / "05_review/human_review_role_quickstart_cards.json",
        exp_dir / "05_review/human_review_role_quickstart_cards.csv",
        Path("scripts/build_cape_human_review_status_dashboard.py"),
        Path("scripts/build_cape_human_return_error_playbook.py"),
        Path("scripts/build_cape_human_review_role_quickstart.py"),
        Path("scripts/build_cape_human_review_launch_checklist.py"),
        Path("scripts/import_cape_mapping_review.py"),
        Path("scripts/evaluate_cape_mapping_review.py"),
        Path("scripts/run_cape_human_return_apply.sh"),
        Path("scripts/run_cape_post_annotation_refresh.sh"),
    ]
    bundles["mapping_expert"] = build_tar(
        out_dir / "cape_mapping_expert_review_top20_groups.tar.gz",
        mapping_files,
        [mapping_readme_path],
    )

    crosswalk_readme_path = out_dir / "README_crosswalk_expert_ko.md"
    write_text(crosswalk_readme_path, crosswalk_readme(exp_dir))
    crosswalk_files = [
        exp_dir / "01_data/crosswalk_review/crosswalk_review_protocol.md",
        exp_dir / "01_data/crosswalk_review/crosswalk_review_items.jsonl",
        exp_dir / "01_data/crosswalk_review/crosswalk_review_sheet.csv",
        exp_dir / "01_data/crosswalk_review/crosswalk_review_manifest.json",
        exp_dir / "04_evaluation/ncs_pcf_crosswalk_report.md",
        exp_dir / "04_evaluation/ncs_pcf_crosswalk_summary.json",
        exp_dir / "04_evaluation/ncs_pcf_crosswalk_candidates.csv",
        exp_dir / "04_evaluation/crosswalk_expert_evaluation_report.md",
        exp_dir / "04_evaluation/crosswalk_expert_metrics.json",
        exp_dir / "04_evaluation/crosswalk_expert_metrics.csv",
        exp_dir / "06_release/human_return_validation_error_playbook_ko.md",
        exp_dir / "06_release/human_return_validation_error_playbook.json",
        exp_dir / "05_review/human_return_validation_error_codes.csv",
        exp_dir / "06_release/human_review_claim_gate_one_page_ko.md",
        exp_dir / "06_release/human_review_master_checklist_ko.md",
        exp_dir / "06_release/human_review_master_checklist_ko.json",
        exp_dir / "06_release/human_review_status_dashboard_ko.md",
        exp_dir / "06_release/human_review_status_dashboard_ko.json",
        exp_dir / "06_release/human_review_launch_checklist_ko.md",
        exp_dir / "06_release/human_review_launch_checklist_ko.json",
        exp_dir / "05_review/human_gate_required_returns.csv",
        exp_dir / "05_review/human_review_gate_dependency_matrix.csv",
        exp_dir / "05_review/human_review_master_return_files.csv",
        exp_dir / "05_review/human_review_status_next_actions.csv",
        exp_dir / "05_review/human_review_minimum_gate_launch_tasks.csv",
        exp_dir / "05_review/human_review_role_quickstart_cards_ko.md",
        exp_dir / "05_review/human_review_role_quickstart_cards.json",
        exp_dir / "05_review/human_review_role_quickstart_cards.csv",
        Path("scripts/build_cape_human_return_error_playbook.py"),
        Path("scripts/build_cape_human_review_role_quickstart.py"),
        Path("scripts/prepare_cape_crosswalk_review_package.py"),
        Path("scripts/import_cape_crosswalk_review.py"),
        Path("scripts/evaluate_cape_crosswalk_review.py"),
        Path("scripts/validate_cape_human_review_returns.py"),
        Path("scripts/run_cape_human_return_apply.sh"),
        Path("scripts/run_cape_post_annotation_refresh.sh"),
    ]
    bundles["crosswalk_expert"] = build_tar(
        out_dir / "cape_crosswalk_expert_review_ncs_pcf.tar.gz",
        crosswalk_files,
        [crosswalk_readme_path],
    )

    active_review_readme_path = out_dir / "README_active_review_effort_ko.md"
    write_text(active_review_readme_path, active_review_readme(exp_dir))
    active_review_files = [
        exp_dir / "06_release/active_review_human_effort_plan.md",
        exp_dir / "06_release/active_review_human_effort_plan.json",
        exp_dir / "06_release/active_review_human_effort_briefing.md",
        exp_dir / "06_release/active_review_human_effort_briefing.json",
        exp_dir / "05_review/active_review_human_effort_template.csv",
        exp_dir / "05_review/active_review_human_effort_briefing.csv",
        exp_dir / "05_review/actual_llm_active_review_queue_P_cape_kg_actual.csv",
        exp_dir / "05_review/actual_llm_active_review_queue_P_cape_kg_actual.jsonl",
        exp_dir / "04_evaluation/active_review_efficiency_report.md",
        exp_dir / "04_evaluation/active_review_efficiency_metrics.json",
        exp_dir / "04_evaluation/active_review_human_effort_report.md",
        exp_dir / "04_evaluation/active_review_human_effort_metrics.json",
        exp_dir / "06_release/human_return_validation_error_playbook_ko.md",
        exp_dir / "06_release/human_return_validation_error_playbook.json",
        exp_dir / "05_review/human_return_validation_error_codes.csv",
        exp_dir / "06_release/human_review_start_here_ko.md",
        exp_dir / "06_release/human_review_claim_gate_one_page_ko.md",
        exp_dir / "06_release/human_review_master_checklist_ko.md",
        exp_dir / "06_release/human_review_master_checklist_ko.json",
        exp_dir / "06_release/human_review_status_dashboard_ko.md",
        exp_dir / "06_release/human_review_status_dashboard_ko.json",
        exp_dir / "06_release/human_review_launch_checklist_ko.md",
        exp_dir / "06_release/human_review_launch_checklist_ko.json",
        exp_dir / "05_review/human_gate_required_returns.csv",
        exp_dir / "05_review/human_review_gate_dependency_matrix.csv",
        exp_dir / "05_review/human_review_master_return_files.csv",
        exp_dir / "05_review/human_review_status_next_actions.csv",
        exp_dir / "05_review/human_review_minimum_gate_launch_tasks.csv",
        exp_dir / "05_review/human_review_role_quickstart_cards_ko.md",
        exp_dir / "05_review/human_review_role_quickstart_cards.json",
        exp_dir / "05_review/human_review_role_quickstart_cards.csv",
        Path("scripts/build_cape_active_review_human_effort.py"),
        Path("scripts/build_cape_human_return_error_playbook.py"),
        Path("scripts/build_cape_human_review_status_dashboard.py"),
        Path("scripts/build_cape_human_review_role_quickstart.py"),
        Path("scripts/build_cape_human_review_launch_checklist.py"),
        Path("scripts/validate_cape_human_review_returns.py"),
        Path("scripts/run_cape_human_return_apply.sh"),
        Path("scripts/run_cape_post_annotation_refresh.sh"),
    ]
    bundles["active_review_effort"] = build_tar(
        out_dir / "cape_active_review_human_effort.tar.gz",
        active_review_files,
        [active_review_readme_path],
    )

    structural_review_readme_path = out_dir / "README_structural_reviewer_ko.md"
    write_text(structural_review_readme_path, structural_review_readme(exp_dir))
    structural_review_files = [
        exp_dir / "06_release/structural_review_action_plan.md",
        exp_dir / "06_release/structural_review_action_plan.json",
        exp_dir / "06_release/structural_review_return_preflight.md",
        exp_dir / "06_release/structural_review_return_preflight.json",
        exp_dir / "06_release/structural_review_application_plan.md",
        exp_dir / "06_release/structural_review_application_plan.json",
        exp_dir / "04_evaluation/structural_gap_worklist_report.md",
        exp_dir / "04_evaluation/structural_gap_worklist_summary.json",
        exp_dir / "05_review/human_gate_required_returns.csv",
        exp_dir / "05_review/human_review_gate_dependency_matrix.csv",
        exp_dir / "05_review/structural_review_checkpoint_candidates.csv",
        exp_dir / "05_review/structural_gateway_branch_gaps.csv",
        exp_dir / "05_review/structural_review_optional_returns.csv",
        exp_dir / "05_review/structural_review_application_actions.csv",
        exp_dir / "06_release/human_return_validation_error_playbook_ko.md",
        exp_dir / "06_release/human_return_validation_error_playbook.json",
        exp_dir / "05_review/human_return_validation_error_codes.csv",
        exp_dir / "06_release/human_review_master_checklist_ko.md",
        exp_dir / "06_release/human_review_claim_gate_one_page_ko.md",
        exp_dir / "06_release/human_review_master_checklist_ko.json",
        exp_dir / "06_release/human_review_status_dashboard_ko.md",
        exp_dir / "06_release/human_review_status_dashboard_ko.json",
        exp_dir / "06_release/human_review_launch_checklist_ko.md",
        exp_dir / "06_release/human_review_launch_checklist_ko.json",
        exp_dir / "05_review/human_review_master_return_files.csv",
        exp_dir / "05_review/human_review_status_next_actions.csv",
        exp_dir / "05_review/human_review_minimum_gate_launch_tasks.csv",
        exp_dir / "05_review/human_review_role_quickstart_cards_ko.md",
        exp_dir / "05_review/human_review_role_quickstart_cards.json",
        exp_dir / "05_review/human_review_role_quickstart_cards.csv",
        Path("scripts/build_cape_structural_gap_worklist.py"),
        Path("scripts/build_cape_structural_review_action_plan.py"),
        Path("scripts/build_cape_human_return_error_playbook.py"),
        Path("scripts/build_cape_human_review_status_dashboard.py"),
        Path("scripts/build_cape_human_review_role_quickstart.py"),
        Path("scripts/build_cape_human_review_launch_checklist.py"),
        Path("scripts/validate_cape_structural_review_returns.py"),
        Path("scripts/build_cape_structural_review_application_plan.py"),
        Path("scripts/run_cape_human_return_apply.sh"),
        Path("scripts/run_cape_post_annotation_refresh.sh"),
    ]
    bundles["structural_reviewer"] = build_tar(
        out_dir / "cape_structural_review_optional.tar.gz",
        structural_review_files,
        [structural_review_readme_path],
    )

    strong_manifest = strong_resegmented_manifest(exp_dir)
    optional_strong = strong_manifest
    if strong_manifest.get("available"):
        strong_readme_path = out_dir / "README_strong_resegmented_review_ko.md"
        strong_manifest_path = out_dir / "strong_resegmented_review_manifest.json"
        write_text(strong_readme_path, strong_resegmented_readme(exp_dir, strong_manifest))
        write_json(strong_manifest_path, {"generated_at_utc": generated_at, **strong_manifest})
        package_dir = Path(strong_manifest["package_dir"])
        strong_files = [
            exp_dir / "01_data/annotation_guideline_v1.md",
            exp_dir / "01_data/gold_annotation/annotation_schema.json",
            exp_dir / "01_data/gold_annotation/adjudication_protocol.md",
            exp_dir / "01_data/gold_annotation/annotation_expansion_manifest.json",
            exp_dir / "01_data/gold_annotation/annotation_expansion_report.md",
            package_dir / "annotator_A.jsonl",
            package_dir / "annotator_B.jsonl",
            package_dir / "adjudication.jsonl",
            package_dir / "adjudication_draft.jsonl",
            package_dir / "adjudication_draft_summary.json",
            package_dir / "adjudication_draft_report.md",
            package_dir / "tracking_sheet.csv",
            package_dir / "strong_review_preview.csv",
            package_dir / "strong_review_preview.md",
            exp_dir / "06_release/strong_resegmented_review_preview_summary.json",
            exp_dir / "06_release/strong_resegmented_review_preview_summary.md",
            exp_dir / "06_release/annotation_calibration_pack_ko.md",
            exp_dir / "06_release/annotation_calibration_pack.json",
            exp_dir / "06_release/annotation_return_field_guide_ko.md",
            exp_dir / "06_release/annotation_return_field_guide.json",
            exp_dir / "05_review/annotation_return_field_checklist.csv",
            exp_dir / "06_release/human_return_validation_error_playbook_ko.md",
            exp_dir / "06_release/human_return_validation_error_playbook.json",
            exp_dir / "05_review/human_return_validation_error_codes.csv",
            exp_dir / "05_review/annotation_calibration_examples.csv",
            exp_dir / "05_review/strong_resegmented_review_preview_summary.csv",
            exp_dir / "06_release/human_review_start_here_ko.md",
            exp_dir / "06_release/human_review_claim_gate_one_page_ko.md",
            exp_dir / "06_release/human_review_master_checklist_ko.md",
            exp_dir / "06_release/human_review_master_checklist_ko.json",
            exp_dir / "06_release/human_review_status_dashboard_ko.md",
            exp_dir / "06_release/human_review_status_dashboard_ko.json",
            exp_dir / "06_release/human_review_launch_checklist_ko.md",
            exp_dir / "06_release/human_review_launch_checklist_ko.json",
            exp_dir / "05_review/human_gate_required_returns.csv",
            exp_dir / "05_review/human_review_gate_dependency_matrix.csv",
            exp_dir / "05_review/human_review_master_return_files.csv",
            exp_dir / "05_review/human_review_status_next_actions.csv",
            exp_dir / "05_review/human_review_minimum_gate_launch_tasks.csv",
            exp_dir / "05_review/human_review_role_quickstart_cards_ko.md",
            exp_dir / "05_review/human_review_role_quickstart_cards.json",
            exp_dir / "05_review/human_review_role_quickstart_cards.csv",
            Path("scripts/build_cape_annotation_batch_review_preview.py"),
            Path("scripts/build_cape_annotation_return_field_guide.py"),
            Path("scripts/build_cape_human_return_error_playbook.py"),
            Path("scripts/build_cape_human_review_status_dashboard.py"),
            Path("scripts/build_cape_human_review_role_quickstart.py"),
            Path("scripts/build_cape_human_review_launch_checklist.py"),
            Path("scripts/import_cape_gold_annotation.py"),
            Path("scripts/validate_cape_strong_review_returns.py"),
            Path("scripts/compute_cape_annotation_iaa.py"),
            Path("scripts/prepare_cape_adjudication_draft.py"),
            Path("scripts/run_cape_strong_return_apply.sh"),
            Path("scripts/run_cape_human_return_apply.sh"),
            Path("scripts/run_cape_post_annotation_refresh.sh"),
        ]
        bundles["strong_resegmented_review"] = build_tar(
            out_dir / "cape_human_gold_strong_resegmented_342.tar.gz",
            strong_files,
            [strong_readme_path, strong_manifest_path],
        )

    checksum_path = out_dir / "human_review_handoff_checksums.sha256"
    checksum_text = "".join(f"{item['sha256']}  {item['path']}\n" for item in bundles.values())
    write_text(checksum_path, checksum_text)

    payload = {
        "generated_at_utc": generated_at,
        "experiment_dir": str(exp_dir),
        "output_dir": str(out_dir),
        "batch_count": len(batches),
        "assigned_chunks": summary.get("assigned_chunks"),
        "candidate_edges_total": summary.get("candidate_edges_total"),
        "claim_status": "handoff_ready_pending_human_review",
        "annotators": annotator_payloads,
        "optional_strong_review": optional_strong,
        "bundles": bundles,
        "checksums": str(checksum_path),
    }
    manifest_path = out_dir / "human_review_handoff_manifest.json"
    report_path = out_dir / "human_review_handoff_report.md"
    write_json(manifest_path, payload)
    write_text(report_path, render_report(payload))
    print(json.dumps({
        "manifest": str(manifest_path),
        "report": str(report_path),
        "checksums": str(checksum_path),
        "bundles": bundles,
    }, ensure_ascii=False, indent=2))


def render_report(payload):
    lines = [
        "# CAPE-KG Human Review Handoff Report",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Claim status: `{payload['claim_status']}`",
        "",
        "## Annotation Handoff",
        "",
    ]
    for annotator, item in payload["annotators"].items():
        lines += [
            f"### Annotator {annotator}",
            "",
            f"- Rows: {item['rows']}",
            f"- Unique chunks: {item['unique_chunks']}",
            f"- Candidate edges: {item['candidate_edges_total']}",
            f"- Ready for minimum gate: {item['ready_for_minimum_gate']}",
            f"- Status counts: `{item['status_counts']}`",
            "",
        ]
    strong = payload.get("optional_strong_review") or {}
    if strong.get("available"):
        lines += [
            "## Optional Strong 300+ Review Handoff",
            "",
            f"- Package: `{strong.get('package')}`",
            f"- Review units: {strong.get('rows')}",
            f"- Source chunks represented: {strong.get('source_chunk_count')}",
            f"- Max source sentences per unit: {strong.get('max_split_sentence_count')}",
            f"- Candidate edges: {strong.get('candidate_edges_total')}",
            "- Status: optional handoff ready; not a completed 300+ adjudicated-gold claim.",
            "",
        ]
    lines += [
        "## Bundles",
        "",
        "| bundle | path | sha256 | bytes | files |",
        "|---|---|---|---:|---:|",
    ]
    for name, bundle in payload["bundles"].items():
        lines.append(
            f"| {name} | `{bundle['path']}` | `{bundle['sha256']}` | {bundle['bytes']} | {bundle['file_count']} |"
        )
    lines += [
        "",
        "## Notes",
        "",
        "- These bundles are internal review handoffs and may contain source-derived chunk text.",
        "- They do not satisfy human-gold, IAA, or adjudication gates by themselves.",
        "- The structural reviewer bundle is optional and does not change the 11-file minimum paper gate.",
        "- The strong resegmented review bundle is optional and does not change the 11-file minimum paper gate.",
        "- After minimum review, validate returned files and run `scripts/run_cape_human_return_apply.sh`.",
        "- After optional strong 300+ review, validate returned files and run `scripts/run_cape_strong_return_apply.sh`.",
    ]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--batch-count", type=int, default=5)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
