# DeepSeek-OCR 10페이지 샘플 실행 기록

대상 PDF:

```text
/home/minjoo/AX_서울펠로우/handoff-hanyang/수주제안/수주 관련 도서 원본/자이제_본문_출력_2018년2월27일수정).pdf
```

공식 repo:

```text
https://github.com/deepseek-ai/DeepSeek-OCR
```

## 현재 수행한 작업

현재 로컬 환경에서 DeepSeek-OCR 모델 실행까지 완료했다. PDF 1~10페이지를 이미지로 렌더링한 뒤, `deepseek-ai/DeepSeek-OCR`로 OCR을 수행하고 Markdown/XLSX/CSV를 생성했다.

생성 파일:

```text
jaije_deepseek_ocr_pages_001_010.md
jaije_deepseek_ocr_pages_001_010.xlsx
jaije_deepseek_ocr_pages_001_010.csv
page_images/page_0001.png
...
page_images/page_0010.png
```

실행한 명령:

```bash
python3 handoff-hanyang/tools/deepseek_ocr_pdf_to_md_xlsx.py --prepare-only
```

## 현재 환경 확인

공식 README 기준 DeepSeek-OCR 권장 환경은 다음이다.

```text
cuda11.8 + torch2.6.0
python=3.12.9
```

현재 로컬에서 사용한 환경:

```text
conda: /home/minjoo/miniconda3/bin/conda
conda env: agent
Python: 3.11.0
torch: 2.7.1+cu126
transformers: 4.46.3
tokenizers: 0.20.3
CUDA: available
```

GPU 상태:

```text
GPU 0: 사용 중, VLLM 프로세스 점유
GPU 1: 사용 가능
GPU 2: 사용 가능
GPU 3: nvidia-smi handle error
GPU 4: 사용 가능
GPU 5: 사용 중, VLLM 프로세스 점유
GPU 6: 사용 가능
GPU 7: 사용 가능
```

따라서 실제 실행에서는 `CUDA_VISIBLE_DEVICES=1`로 GPU 1을 지정했다.

## 현재 머신에서 실제 실행한 방법

기존 `agent` 환경에 부족한 패키지를 설치했다.

```bash
/home/minjoo/miniconda3/bin/conda run -n agent \
  python -m pip install PyMuPDF==1.24.11

/home/minjoo/miniconda3/bin/conda run -n agent \
  python -m pip install addict einops easydict img2pdf torchvision==0.22.1 \
  --index-url https://download.pytorch.org/whl/cu126 \
  --extra-index-url https://pypi.org/simple

/home/minjoo/miniconda3/bin/conda run -n agent \
  python -m pip install transformers==4.46.3 tokenizers==0.20.3
```

1페이지 테스트:

```bash
CUDA_VISIBLE_DEVICES=1 \
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
/home/minjoo/miniconda3/bin/conda run -n agent \
  python handoff-hanyang/tools/deepseek_ocr_pdf_to_md_xlsx.py \
  --start-page 3 \
  --num-pages 1 \
  --output-dir handoff-hanyang/ocr_outputs/jaije_deepseek_ocr_test_page3 \
  --attn eager
```

10페이지 실행:

```bash
CUDA_VISIBLE_DEVICES=1 \
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
/home/minjoo/miniconda3/bin/conda run -n agent \
  python handoff-hanyang/tools/deepseek_ocr_pdf_to_md_xlsx.py \
  --start-page 1 \
  --num-pages 10 \
  --output-dir handoff-hanyang/ocr_outputs/jaije_deepseek_ocr_10p \
  --attn eager
```

결과:

```text
10 pages processed
all rows status = ocr_done
```

주의:

```text
GPU 0 또는 GPU 5로 실행하면 이미 VLLM 프로세스가 약 21GB를 사용 중이어서 OOM이 날 수 있다.
반드시 비어 있는 GPU를 CUDA_VISIBLE_DEVICES로 지정한다.
```

## 공식 권장 환경에서 실행하는 방법

공식 README 기준으로 별도 GPU 서버에서 환경을 만든다.

```bash
git clone https://github.com/deepseek-ai/DeepSeek-OCR.git
cd DeepSeek-OCR

conda create -n deepseek-ocr python=3.12.9 -y
conda activate deepseek-ocr

pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu118
pip install -r requirements.txt
pip install flash-attn==2.7.3 --no-build-isolation
pip install pandas openpyxl
```

그 다음 이 작업 폴더에서 다음을 실행한다.

```bash
cd /home/minjoo/AX_서울펠로우

python handoff-hanyang/tools/deepseek_ocr_pdf_to_md_xlsx.py \
  --start-page 1 \
  --num-pages 10 \
  --attn flash_attention_2
```

GPU 메모리가 부족하거나 `flash-attn` 설치가 안 되면 우선 다음처럼 실행한다.

```bash
python handoff-hanyang/tools/deepseek_ocr_pdf_to_md_xlsx.py \
  --start-page 1 \
  --num-pages 10 \
  --attn eager
```

## 출력 형식

스크립트는 페이지별 OCR 결과를 다음 컬럼으로 저장한다.

```text
source_pdf
model
prompt
page
image_path
width
height
status
markdown
error
```

최종적으로 다음 파일이 채워진다.

```text
jaije_deepseek_ocr_pages_001_010.md
jaije_deepseek_ocr_pages_001_010.xlsx
```

## 전체 PDF로 확장

10페이지 샘플이 정상 동작하면 전체 476페이지를 다음처럼 확장한다.

```bash
python handoff-hanyang/tools/deepseek_ocr_pdf_to_md_xlsx.py \
  --start-page 1 \
  --num-pages 476 \
  --output-dir handoff-hanyang/ocr_outputs/jaije_deepseek_ocr_full \
  --attn flash_attention_2
```

전체 실행 시에는 페이지별 결과를 먼저 검수한 뒤, 저작권/공개 가능 범위를 확인하고 온톨로지 입력으로 사용해야 한다.
