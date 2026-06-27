#!/usr/bin/env python3
"""Run DeepSeek-OCR on selected PDF pages and export Markdown/XLSX.

This script follows the official DeepSeek-OCR Transformers example:
https://github.com/deepseek-ai/DeepSeek-OCR

It first renders PDF pages to PNG files, then passes each page image to
`deepseek-ai/DeepSeek-OCR`, and finally writes:
  - combined Markdown
  - page-level XLSX table

Use `--prepare-only` when the local machine does not have a working CUDA
environment. It will still create the 10 page images and an XLSX manifest.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

import fitz  # PyMuPDF
import pandas as pd


DEFAULT_PROMPT = "<image>\n<|grounding|>Convert the document to markdown. "


def find_default_pdf(repo_root: Path) -> Path:
    matches = glob.glob(
        str(repo_root / "handoff-hanyang" / "**" / "자이제_본문_출력_2018년2월27일수정).pdf"),
        recursive=True,
    )
    if not matches:
        raise FileNotFoundError("자이제 PDF를 찾지 못했습니다. --pdf 로 경로를 지정하세요.")
    return Path(matches[0])


def render_pages(pdf_path: Path, image_dir: Path, start_page: int, num_pages: int, dpi: int) -> List[Dict]:
    image_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(str(pdf_path))
    total_pages = doc.page_count
    end_page = min(total_pages, start_page + num_pages - 1)
    if start_page < 1 or start_page > total_pages:
        raise ValueError(f"start_page={start_page} is outside PDF page range 1..{total_pages}")

    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    rows: List[Dict] = []

    for page_no in range(start_page, end_page + 1):
        page = doc[page_no - 1]
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        image_path = image_dir / f"page_{page_no:04d}.png"
        pix.save(str(image_path))
        rows.append(
            {
                "page": page_no,
                "image_path": str(image_path),
                "width": pix.width,
                "height": pix.height,
                "status": "image_prepared",
                "markdown": "",
                "error": "",
            }
        )

    doc.close()
    return rows


def read_possible_deepseek_output(output_dir: Path, before_files: set, result) -> str:
    if isinstance(result, str) and result.strip():
        return result.strip()

    after_files = set(output_dir.rglob("*"))
    new_files = [p for p in after_files - before_files if p.is_file()]
    text_files = [
        p for p in new_files
        if p.suffix.lower() in {".txt", ".md", ".mmd", ".json"}
    ]
    for p in sorted(text_files, key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            text = p.read_text(encoding="utf-8", errors="ignore").strip()
            if text:
                if p.suffix.lower() == ".json":
                    try:
                        obj = json.loads(text)
                        return json.dumps(obj, ensure_ascii=False, indent=2)
                    except Exception:
                        return text
                return text
        except Exception:
            continue
    return ""


def load_deepseek_model(attn: str, require_cuda: bool):
    try:
        import torch
        from transformers import AutoModel, AutoTokenizer
    except Exception as exc:
        raise RuntimeError(
            "DeepSeek-OCR 실행에 필요한 torch/transformers가 없습니다. "
            "공식 README 환경을 먼저 설치하세요."
        ) from exc

    if require_cuda and not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA GPU를 사용할 수 없습니다. DeepSeek-OCR 공식 예제는 CUDA 실행을 전제로 합니다."
        )

    model_name = "deepseek-ai/DeepSeek-OCR"
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModel.from_pretrained(
        model_name,
        _attn_implementation=attn,
        trust_remote_code=True,
        use_safetensors=True,
    )
    model = model.eval()

    if torch.cuda.is_available():
        model = model.cuda().to(torch.bfloat16)
    else:
        model = model.to("cpu")

    return model, tokenizer


def run_ocr(rows: List[Dict], output_dir: Path, prompt: str, attn: str, require_cuda: bool) -> List[Dict]:
    model, tokenizer = load_deepseek_model(attn=attn, require_cuda=require_cuda)
    page_output_dir = output_dir / "deepseek_page_outputs"
    page_output_dir.mkdir(parents=True, exist_ok=True)

    for row in rows:
        image_path = row["image_path"]
        page_dir = page_output_dir / f"page_{row['page']:04d}"
        page_dir.mkdir(parents=True, exist_ok=True)
        before = set(page_dir.rglob("*"))
        try:
            result = model.infer(
                tokenizer,
                prompt=prompt,
                image_file=image_path,
                output_path=str(page_dir),
                base_size=1024,
                image_size=640,
                crop_mode=True,
                save_results=True,
                test_compress=True,
            )
            markdown = read_possible_deepseek_output(page_dir, before, result)
            row["markdown"] = markdown
            row["status"] = "ocr_done" if markdown else "ocr_done_empty_output"
        except Exception as exc:
            row["status"] = "ocr_failed"
            row["error"] = f"{type(exc).__name__}: {exc}"
    return rows


def write_outputs(rows: List[Dict], output_dir: Path, source_pdf: Path, prompt: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    first_page = min(row["page"] for row in rows)
    last_page = max(row["page"] for row in rows)
    stem = f"jaije_deepseek_ocr_pages_{first_page:03d}_{last_page:03d}"
    md_path = output_dir / f"{stem}.md"
    xlsx_path = output_dir / f"{stem}.xlsx"
    csv_path = output_dir / f"{stem}.csv"

    parts = [
        "# 자이제 PDF DeepSeek-OCR 샘플",
        "",
        f"- source_pdf: `{source_pdf}`",
        f"- pages: {first_page}-{last_page}",
        f"- prompt: `{prompt.strip()}`",
        "",
    ]
    for row in rows:
        parts.extend(
            [
                f"## Page {row['page']}",
                "",
                f"- image: `{row['image_path']}`",
                f"- status: `{row['status']}`",
                "",
                row.get("markdown", "").strip() or f"> OCR text is empty. {row.get('error', '')}".strip(),
                "",
            ]
        )

    md_path.write_text("\n".join(parts), encoding="utf-8")
    df = pd.DataFrame(rows)
    df.insert(0, "source_pdf", str(source_pdf))
    df.insert(1, "model", "deepseek-ai/DeepSeek-OCR")
    df.insert(2, "prompt", prompt)
    df.to_excel(xlsx_path, index=False)
    df.to_csv(csv_path, index=False)
    print(f"Markdown: {md_path}")
    print(f"XLSX:     {xlsx_path}")
    print(f"CSV:      {csv_path}")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=repo_root / "handoff-hanyang" / "ocr_outputs" / "jaije_deepseek_ocr_10p")
    parser.add_argument("--start-page", type=int, default=1)
    parser.add_argument("--num-pages", type=int, default=10)
    parser.add_argument("--dpi", type=int, default=144)
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--attn", default="eager", choices=["eager", "sdpa", "flash_attention_2"])
    parser.add_argument("--prepare-only", action="store_true", help="Render page images and write empty md/xlsx manifest only.")
    parser.add_argument("--allow-cpu", action="store_true", help="Allow CPU model loading. Very slow and not recommended.")
    args = parser.parse_args()

    pdf_path = args.pdf or find_default_pdf(repo_root)
    pdf_path = pdf_path.resolve()
    output_dir = args.output_dir.resolve()
    image_dir = output_dir / "page_images"

    rows = render_pages(pdf_path, image_dir, args.start_page, args.num_pages, args.dpi)

    if not args.prepare_only:
        rows = run_ocr(
            rows,
            output_dir=output_dir,
            prompt=args.prompt,
            attn=args.attn,
            require_cuda=not args.allow_cpu,
        )

    write_outputs(rows, output_dir, pdf_path, args.prompt)


if __name__ == "__main__":
    main()
