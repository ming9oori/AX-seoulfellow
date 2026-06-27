# AX KG 실험 인계 요약

작성일: 2026-06-27
작업 경로: `/home/minjoo/AX_서울펠로우`

## 1. 지금까지 진행한 실험

### 실험 A: CEP-Onto 초안

기준 문서: `AX_novel_ontology_experiment_plan.md`

실행 스크립트:

```bash
python3 scripts/build_cep_onto_kg.py
```

주요 산출물:

```text
experiments/cep_onto_jaije_20260627/
```

최종 요약:

```text
OCR sentences: 5,009
Anchor candidates: 9,589
Layer2 nodes: 4,938
Layer2 edges: 25,163
Verified task frames: 1,476
SHACL-like violation rate: 0.0
```

성격:

```text
high-recall draft KG
문장 evidence 기반 rule extraction
NCS/PCF TF-IDF weak standard mapping 포함
```

### 실험 B: AX-EPAK 내부 구축 실험

기준 문서: `AX_internal_KG_experiment_design.md`

실행 스크립트:

```bash
CUDA_VISIBLE_DEVICES=5,7 python3 scripts/build_ax_epak_internal_kg.py
```

GPU는 실제로 사용하지 않는 결정론적 파이프라인이지만, 211 서버에서 GPU가 필요한 후속 단계가 생길 경우 5번과 7번만 사용하도록 환경변수를 고정한다.

주요 산출물:

```text
outputs/
  00_manifest/
  01_layer1/
  02_ocr/
  03_schema/
  04_task_frames/
  05_procedure/
  06_triples/
  07_layer2_graph/
  08_mapping/
  09_visualization/
  10_evaluation/
```

최종 요약:

```text
Manifest files: 28
Layer1 NCS nodes: 4,109
Layer1 PCF nodes: 5,301
OCR sentences: 5,009
Layer2 chunks: 460
Layer2 nodes: 179
Layer2 edges: 906
NCS mapping candidates: 110
PCF mapping candidates: 110
Visualization nodes: 9,589
Visualization edges: 10,499
```

최종 성공 기준 파일:

```text
outputs/07_layer2_graph/layer2_nodes.jsonl
outputs/07_layer2_graph/layer2_edges.jsonl
outputs/08_mapping/l2_ncs_mapping_candidates.jsonl
outputs/08_mapping/l2_pcf_mapping_candidates.jsonl
outputs/09_visualization/kg_viewer.html
outputs/10_evaluation/final_build_report.md
```

## 2. 211 서버에서 재실행

필요 패키지:

```bash
python3 -m pip install --user pandas openpyxl scikit-learn jsonschema pyyaml
```

작업 경로에서 다음을 실행한다.

```bash
bash scripts/run_ax_epak_on_211.sh
```

또는 직접 실행한다.

```bash
export CUDA_VISIBLE_DEVICES=5,7
python3 -m py_compile scripts/build_cep_onto_kg.py scripts/build_ax_epak_internal_kg.py
python3 scripts/build_ax_epak_internal_kg.py
```

## 3. 검수 대상

사람 검수가 필요한 파일:

```text
outputs/04_task_frames/task_frame_review_sheet.csv
outputs/08_mapping/mapping_review_sheet.csv
outputs/10_evaluation/internal_review_sample.jsonl
```

브라우저 시각화:

```text
outputs/09_visualization/kg_viewer.html
```

## 4. 제한 사항

현재 실험은 외부 LLM을 호출하지 않은 결정론적 내부 구축 실험이다.
따라서 산출물은 재현 가능한 1차 KG와 검수 큐이며, 최종 연구용 gold KG로 쓰려면 task frame, procedure, mapping 후보에 대한 사람 검수가 필요하다.
