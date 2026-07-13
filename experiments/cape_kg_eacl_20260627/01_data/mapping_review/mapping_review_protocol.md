# CAPE-KG NCS/PCF Mapping Expert Review Protocol

Generated: 2026-06-28

이 문서는 Layer 2 업무 KG와 NCS/PCF 표준 체계 간 mapping candidate를 전문가가 검수하기 위한 지침이다. Mapping candidate는 자동 후보이며, expert review가 끝나기 전까지는 downstream mapping 성능 주장에 사용할 수 없다.

---

## 1. Review 목표

Expert reviewer는 각 Layer 2 `DomainTask`에 대해 Top-5 NCS 또는 PCF 후보가 타당한 표준 alignment인지 판정한다.

Review 결과는 다음 metric 계산에 사용된다.

- Hit@1
- Hit@3
- Hit@5
- Precision@5
- MRR
- expert accept rate

현재 후보 파일:

- `experiments/cape_kg_eacl_20260627/01_data/mapping_review/mapping_review_items.jsonl`

우선순위 파일:

- `experiments/cape_kg_eacl_20260627/05_review/mapping_review_next_20_groups.csv`
- `experiments/cape_kg_eacl_20260627/05_review/mapping_review_next_60_rows.csv`

---

## 2. Review 단위

기본 review 단위는 다음 조합이다.

```text
source task + standard
```

예:

```text
source task: 제안서 작성
standard: PCF
Top-5 candidate rows: rank 1-5
```

Top-5 row가 모두 `completed`여야 해당 group이 metric 계산에 들어간다. 일부 row만 완료된 group은 pending group으로 남긴다.

---

## 3. Decision values

`expert_decision` 값:

| 값 | 의미 | Positive로 계산되는가 |
| --- | --- | --- |
| `accepted` | 타당하거나 방어 가능한 mapping | yes |
| `rejected` | 부적절한 mapping | no |
| `unsure` | 근거 부족 또는 전문가 판단 보류 | no |

`relevance_grade` 값:

| 값 | 의미 | Positive로 계산되는가 |
| --- | --- | --- |
| `0` | 무관함 | no |
| `1` | 약하게 관련되지만 mapping으로는 부적절 | no |
| `2` | 수용 가능한 mapping | yes |
| `3` | 가장 적합하거나 강한 mapping | yes |

권장:

- `accepted`이면 relevance grade는 2 또는 3을 사용한다.
- `rejected`이면 relevance grade는 0 또는 1을 사용한다.
- `unsure`이면 comment에 보류 이유를 적는다.

---

## 4. Accept 기준

후보를 `accepted`로 둘 수 있는 경우:

- Layer 2 task의 업무 목적과 표준 항목의 목적이 실질적으로 일치한다.
- task 수행에 필요한 capability/process가 target 표준 항목에 직접 대응된다.
- label은 다르지만 설명/계층/업무 동사가 같은 업무 영역을 가리킨다.
- NCS의 경우 source task 수행에 필요한 직무 능력 단위로 방어 가능하다.
- PCF의 경우 source task가 해당 process element나 process metric context와 자연스럽게 연결된다.

예:

- `제안서 작성` -> 제안/문서 작성 관련 표준 항목
- `가격 전략 수립` -> 가격/원가/견적/재무 분석 관련 표준 항목
- `고객 니즈 분석` -> 고객 요구 분석/시장 분석/영업 기획 관련 표준 항목

---

## 5. Reject 기준

후보를 `rejected`로 두어야 하는 경우:

- 표면 단어만 비슷하고 업무 목적이 다르다.
- 다른 산업/기술 영역의 항목으로 source task와 실질 관련이 낮다.
- source task가 요구하는 capability보다 너무 넓거나 너무 좁아 mapping으로 쓰기 어렵다.
- rank/score가 높아도 설명상 관계가 방어되지 않는다.
- target이 artifact, metric, process context로는 관련 있어도 capability alignment로 보기 어렵다.

주의:

- 자동 score가 높다는 이유만으로 accept하지 않는다.
- domain gap penalty가 있어도 사람이 보기에 명확히 관련되면 accept할 수 있다.
- 반대로 score가 낮아도 label/definition이 강하게 맞으면 accept할 수 있다.

---

## 6. `unsure` 사용 기준

다음 경우에는 `unsure`를 사용할 수 있다.

- target 표준 항목 설명이 부족해 판단할 수 없다.
- source task가 너무 넓어 여러 표준 항목이 모두 부분적으로만 맞는다.
- PCF metric과 process element의 의미를 추가 확인해야 한다.
- NCS 능력단위가 특정 산업에 종속되어 있어 일반화 가능성이 불명확하다.

`unsure`는 positive로 계산하지 않는다. 논문용 metric을 위해서는 가능하면 `accepted` 또는 `rejected`로 확정하는 것이 좋다.

---

## 7. Comment 작성 규칙

각 row에는 간단한 comment를 남기는 것을 권장한다.

좋은 comment 예:

- `업무 목적과 target capability가 모두 가격 산정/원가 분석에 해당하므로 accepted.`
- `단어 유사도는 있으나 BIM 작성 업무로 제안참여 의사결정과 직접 관련이 낮아 rejected.`
- `PCF 항목이 넓은 process context라 부분 관련은 있으나 Top-5 positive로 보기 어려워 grade 1.`

나쁜 comment 예:

- `좋음`
- `애매함`
- `score 높음`

---

## 8. Workbench와 import

Optional browser workbench 생성:

```bash
python3 scripts/build_cape_mapping_review_workbench.py \
  --experiment-dir experiments/cape_kg_eacl_20260627
```

열 파일:

```text
experiments/cape_kg_eacl_20260627/01_data/mapping_review/mapping_review_workbench.html
```

Export file:

```text
experiments/cape_kg_eacl_20260627/01_data/mapping_review/mapping_review_items.reviewed.jsonl
```

Dry-run import:

```bash
/home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python scripts/import_cape_mapping_review.py \
  --experiment-dir experiments/cape_kg_eacl_20260627 \
  --reviewed-file experiments/cape_kg_eacl_20260627/01_data/mapping_review/mapping_review_items.reviewed.jsonl
```

Apply import:

```bash
/home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python scripts/import_cape_mapping_review.py \
  --experiment-dir experiments/cape_kg_eacl_20260627 \
  --reviewed-file experiments/cape_kg_eacl_20260627/01_data/mapping_review/mapping_review_items.reviewed.jsonl \
  --apply
```

Importer가 확인하는 항목:

- immutable row key 변경 여부
- decision/status value 유효성
- reviewer field 형식
- backup 생성

---

## 9. Evaluation

Import 후 mapping metric을 계산한다.

```bash
/home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python scripts/evaluate_cape_mapping_review.py \
  --experiment-dir experiments/cape_kg_eacl_20260627
```

또는 전체 refresh를 실행한다.

```bash
PYTHON_BIN=/home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python \
LLM_PYTHON=/home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python \
APPLY_IMPORTS=0 \
bash scripts/run_cape_post_annotation_refresh.sh
```

확인 파일:

- `experiments/cape_kg_eacl_20260627/04_evaluation/mapping_expert_metrics.json`
- `experiments/cape_kg_eacl_20260627/04_evaluation/mapping_expert_evaluation_report.md`
- `experiments/cape_kg_eacl_20260627/06_release/mapping_review_progress_summary.json`
- `experiments/cape_kg_eacl_20260627/06_release/mapping_review_progress_report.md`

---

## 10. Completion checklist

Mapping downstream claim을 하기 전에 확인한다.

- [ ] priority Top-20 source groups를 모두 검토했다.
- [ ] 각 completed group의 Top-5 row가 모두 `completed`다.
- [ ] `expert_decision`이 비어 있지 않다.
- [ ] `relevance_grade`가 0-3 범위다.
- [ ] accepted row는 comment로 방어 가능하다.
- [ ] import dry run이 통과했다.
- [ ] apply import 후 metric report를 재생성했다.
- [ ] claim gate에서 mapping expert review 상태를 확인했다.

---

## 11. Paper claim 주의사항

다음 전에는 NCS/PCF mapping downstream 성능을 주장하지 않는다.

- expert-reviewed rows가 import됨
- source task + standard Top-5 group이 complete됨
- Hit@K/P@5/MRR metric이 생성됨
- claim gate가 mapping claim을 더 이상 pending으로 표시하지 않음

현재 상태가 `pending_expert_review`이면 mapping 후보 생성 사실만 말하고, mapping 정확도나 성능은 주장하지 않는다.
