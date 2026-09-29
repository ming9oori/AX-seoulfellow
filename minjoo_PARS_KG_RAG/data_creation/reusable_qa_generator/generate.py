#!/usr/bin/env python3
"""Generate a traceable QA dataset from tabular or JSON source records.

The model creates only question, answer, source_ids, question_type, and
difficulty. Evidence text and metadata are copied from the source by code.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import time
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG = SCRIPT_DIR / "config.example.json"
OUTPUT_FIELDS = (
    "qa_id",
    "question",
    "answer",
    "source_ids",
    "evidence_text",
    "evidence_metadata",
    "group_key",
    "question_type",
    "difficulty",
    "review_status",
    "reviewer",
    "review_notes",
    "source_file",
    "chunk_id",
    "generation_model",
    "generation_response_id",
    "prompt_version",
    "generated_at",
)


@dataclass(frozen=True)
class DatasetConfig:
    name: str
    language: str
    domain: str
    qa_id_prefix: str


@dataclass(frozen=True)
class InputConfig:
    path: Path
    format: str
    sheet: str | None
    id_column: str | None
    text_column: str
    group_columns: tuple[str, ...]
    metadata_columns: tuple[str, ...]


@dataclass(frozen=True)
class PromptConfig:
    system_prompt_path: Path
    few_shots_path: Path | None
    version: str


@dataclass(frozen=True)
class GenerationConfig:
    model: str
    target_size: int
    qas_per_chunk: int
    max_source_rows: int
    max_source_chars: int
    max_source_ids_per_qa: int
    max_answer_sentences: int
    duplicate_threshold: float
    max_output_tokens: int
    max_retries: int
    retry_base_seconds: float
    timeout_seconds: float
    question_types: tuple[str, ...]
    difficulties: tuple[str, ...]


@dataclass(frozen=True)
class AppConfig:
    config_path: Path
    dataset: DatasetConfig
    input: InputConfig
    prompt: PromptConfig
    generation: GenerationConfig


@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    text: str
    group_key: tuple[str, ...]
    metadata: dict[str, str]

    def to_prompt_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "text": self.text,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class SourceChunk:
    chunk_id: str
    group_key: tuple[str, ...]
    records: tuple[SourceRecord, ...]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_space(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def clean_source_text(value: Any) -> str:
    """Strip outer whitespace while preserving meaningful line and table structure."""
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value).replace("\r\n", "\n").replace("\r", "\n").strip()


def normalize_scalar(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(int(value)) if value.is_integer() else format(value, "g")
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return normalize_space(value)


def normalize_question(value: str) -> str:
    text = unicodedata.normalize("NFKC", value).casefold()
    return "".join(character for character in text if character.isalnum())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def stable_hash(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256_text(payload)


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    temporary.replace(path)


def write_jsonl_atomic(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    temporary.replace(path)


def append_jsonl(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False) + "\n")


def csv_value(value: Any) -> Any:
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    if value is None:
        return ""
    return value


def write_csv_atomic(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    fields = list(rows[0]) if rows else list(OUTPUT_FIELDS)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: csv_value(row.get(field)) for field in fields})
    temporary.replace(path)


def _require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def _required_text(value: Any, label: str) -> str:
    text = normalize_space(value)
    if not text:
        raise ValueError(f"{label} must be a non-empty string")
    return text


def _string_list(value: Any, label: str, *, allow_empty: bool = True) -> tuple[str, ...]:
    if value is None and allow_empty:
        return ()
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a JSON array")
    output = tuple(_required_text(item, f"{label} item") for item in value)
    if not allow_empty and not output:
        raise ValueError(f"{label} cannot be empty")
    if len(output) != len(set(output)):
        raise ValueError(f"{label} contains duplicates")
    return output


def resolve_config_path(config_path: Path, value: Any, label: str) -> Path:
    raw = _required_text(value, label)
    path = Path(raw)
    if not path.is_absolute():
        path = config_path.parent / path
    return path.resolve()


def load_config(
    path: Path,
    *,
    model_override: str = "",
    target_size_override: int | None = None,
) -> AppConfig:
    config_path = path.resolve()
    payload = _require_object(read_json(config_path), "config root")
    dataset_raw = _require_object(payload.get("dataset"), "dataset")
    input_raw = _require_object(payload.get("input"), "input")
    prompt_raw = _require_object(payload.get("prompt"), "prompt")
    generation_raw = _require_object(payload.get("generation"), "generation")

    dataset = DatasetConfig(
        name=_required_text(dataset_raw.get("name"), "dataset.name"),
        language=_required_text(dataset_raw.get("language"), "dataset.language"),
        domain=_required_text(dataset_raw.get("domain"), "dataset.domain"),
        qa_id_prefix=_required_text(
            dataset_raw.get("qa_id_prefix"), "dataset.qa_id_prefix"
        ),
    )
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", dataset.qa_id_prefix):
        raise ValueError(
            "dataset.qa_id_prefix may contain only letters, digits, '_' and '-', "
            "and must start with a letter or digit"
        )

    source_format = normalize_space(input_raw.get("format", "auto")).lower() or "auto"
    if source_format not in {"auto", "csv", "jsonl", "json", "xlsx"}:
        raise ValueError("input.format must be auto, csv, jsonl, json, or xlsx")
    id_column_text = normalize_space(input_raw.get("id_column"))
    sheet_text = normalize_space(input_raw.get("sheet"))
    input_config = InputConfig(
        path=resolve_config_path(config_path, input_raw.get("path"), "input.path"),
        format=source_format,
        sheet=sheet_text or None,
        id_column=id_column_text or None,
        text_column=_required_text(input_raw.get("text_column"), "input.text_column"),
        group_columns=_string_list(
            input_raw.get("group_columns", []), "input.group_columns"
        ),
        metadata_columns=_string_list(
            input_raw.get("metadata_columns", []), "input.metadata_columns"
        ),
    )

    few_shots_value = prompt_raw.get("few_shots_path")
    few_shots_path = (
        resolve_config_path(config_path, few_shots_value, "prompt.few_shots_path")
        if normalize_space(few_shots_value)
        else None
    )
    prompt = PromptConfig(
        system_prompt_path=resolve_config_path(
            config_path,
            prompt_raw.get("system_prompt_path"),
            "prompt.system_prompt_path",
        ),
        few_shots_path=few_shots_path,
        version=_required_text(prompt_raw.get("version"), "prompt.version"),
    )

    default_question_types = [
        "fact",
        "numeric",
        "definition",
        "reason",
        "method",
        "comparison",
        "procedure",
        "misconception",
    ]
    model = model_override or os.getenv("OPENAI_MODEL", "") or _required_text(
        generation_raw.get("model"), "generation.model"
    )
    configured_target = int(generation_raw.get("target_size", 100))
    generation = GenerationConfig(
        model=model,
        target_size=(
            target_size_override
            if target_size_override is not None
            else configured_target
        ),
        qas_per_chunk=int(generation_raw.get("qas_per_chunk", 3)),
        max_source_rows=int(generation_raw.get("max_source_rows", 18)),
        max_source_chars=int(generation_raw.get("max_source_chars", 5000)),
        max_source_ids_per_qa=int(
            generation_raw.get("max_source_ids_per_qa", 4)
        ),
        max_answer_sentences=int(
            generation_raw.get("max_answer_sentences", 2)
        ),
        duplicate_threshold=float(
            generation_raw.get("duplicate_threshold", 0.92)
        ),
        max_output_tokens=int(generation_raw.get("max_output_tokens", 1600)),
        max_retries=int(generation_raw.get("max_retries", 2)),
        retry_base_seconds=float(
            generation_raw.get("retry_base_seconds", 2.0)
        ),
        timeout_seconds=float(generation_raw.get("timeout_seconds", 120.0)),
        question_types=_string_list(
            generation_raw.get("question_types", default_question_types),
            "generation.question_types",
            allow_empty=False,
        ),
        difficulties=_string_list(
            generation_raw.get("difficulties", ["easy", "medium", "hard"]),
            "generation.difficulties",
            allow_empty=False,
        ),
    )
    validate_config(dataset, input_config, prompt, generation)
    return AppConfig(
        config_path=config_path,
        dataset=dataset,
        input=input_config,
        prompt=prompt,
        generation=generation,
    )


def validate_config(
    dataset: DatasetConfig,
    input_config: InputConfig,
    prompt: PromptConfig,
    generation: GenerationConfig,
) -> None:
    if not input_config.path.is_file():
        raise FileNotFoundError(f"Source file not found: {input_config.path}")
    if not prompt.system_prompt_path.is_file():
        raise FileNotFoundError(
            f"System prompt not found: {prompt.system_prompt_path}"
        )
    if prompt.few_shots_path is not None and not prompt.few_shots_path.is_file():
        raise FileNotFoundError(f"Few-shot file not found: {prompt.few_shots_path}")
    numeric_positive = {
        "target_size": generation.target_size,
        "qas_per_chunk": generation.qas_per_chunk,
        "max_source_rows": generation.max_source_rows,
        "max_source_chars": generation.max_source_chars,
        "max_source_ids_per_qa": generation.max_source_ids_per_qa,
        "max_answer_sentences": generation.max_answer_sentences,
        "max_output_tokens": generation.max_output_tokens,
    }
    invalid = [name for name, value in numeric_positive.items() if value <= 0]
    if invalid:
        raise ValueError(f"Generation values must be positive: {invalid}")
    if generation.qas_per_chunk > 10:
        raise ValueError("generation.qas_per_chunk must be at most 10")
    if generation.max_source_ids_per_qa > generation.max_source_rows:
        raise ValueError(
            "max_source_ids_per_qa cannot exceed max_source_rows"
        )
    if generation.max_retries < 0 or generation.retry_base_seconds <= 0:
        raise ValueError("Retry settings are invalid")
    if generation.timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    if not 0 < generation.duplicate_threshold <= 1:
        raise ValueError("duplicate_threshold must be in (0, 1]")
    referenced_columns = [
        input_config.text_column,
        *input_config.group_columns,
        *input_config.metadata_columns,
    ]
    if input_config.id_column:
        referenced_columns.append(input_config.id_column)
    if any(not column for column in referenced_columns):
        raise ValueError("Configured column names cannot be blank")
    if len(set(input_config.metadata_columns)) != len(input_config.metadata_columns):
        raise ValueError("metadata_columns contains duplicates")
    if not dataset.name or not dataset.language or not dataset.domain:
        raise ValueError("Dataset identity fields cannot be blank")


def infer_format(path: Path, configured: str) -> str:
    if configured != "auto":
        return configured
    suffix = path.suffix.lower()
    formats = {".csv": "csv", ".jsonl": "jsonl", ".json": "json", ".xlsx": "xlsx"}
    if suffix not in formats:
        raise ValueError(
            f"Cannot infer input format from {suffix!r}; set input.format explicitly"
        )
    return formats[suffix]


def read_tabular_rows(config: InputConfig) -> tuple[list[dict[str, Any]], list[str]]:
    source_format = infer_format(config.path, config.format)
    if source_format == "csv":
        with config.path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            headers = list(reader.fieldnames or [])
            if not headers or any(not normalize_space(header) for header in headers):
                raise ValueError("CSV header row contains a blank column")
            if len(headers) != len(set(headers)):
                raise ValueError("CSV header row contains duplicate columns")
            rows = []
            for row_number, row in enumerate(reader, start=2):
                rows.append({**row, "__source_position__": f"row:{row_number}"})
        return rows, headers
    if source_format == "jsonl":
        rows = []
        headers: list[str] = []
        with config.path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError(f"JSONL line {line_number} is not an object")
                for key in value:
                    if key not in headers:
                        headers.append(key)
                rows.append({**value, "__source_position__": f"line:{line_number}"})
        return rows, headers
    if source_format == "json":
        value = read_json(config.path)
        if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
            raise ValueError("JSON input must be an array of objects")
        headers: list[str] = []
        for item in value:
            for key in item:
                if key not in headers:
                    headers.append(key)
        return [
            {**item, "__source_position__": f"item:{index}"}
            for index, item in enumerate(value, start=1)
        ], headers
    if source_format == "xlsx":
        try:
            from openpyxl import load_workbook
        except ImportError as exc:
            raise RuntimeError(
                "XLSX input requires openpyxl; install requirements.txt"
            ) from exc
        workbook = load_workbook(config.path, read_only=True, data_only=True)
        sheet = workbook[config.sheet] if config.sheet else workbook.active
        raw_headers = [
            normalize_space(cell.value)
            for cell in next(sheet.iter_rows(min_row=1, max_row=1))
        ]
        while raw_headers and not raw_headers[-1]:
            raw_headers.pop()
        if not raw_headers or any(not header for header in raw_headers):
            workbook.close()
            raise ValueError("XLSX header row contains a blank column")
        if len(raw_headers) != len(set(raw_headers)):
            workbook.close()
            raise ValueError("XLSX header row contains duplicate columns")
        rows = []
        for row_number, values in enumerate(
            sheet.iter_rows(
                min_row=2,
                max_col=len(raw_headers),
                values_only=True,
            ),
            start=2,
        ):
            rows.append(
                {
                    **dict(zip(raw_headers, values)),
                    "__source_position__": f"row:{row_number}",
                }
            )
        workbook.close()
        return rows, raw_headers
    raise AssertionError(f"Unhandled input format: {source_format}")


def load_source_records(config: InputConfig) -> tuple[list[SourceRecord], list[str]]:
    raw_rows, headers = read_tabular_rows(config)
    required = {
        config.text_column,
        *config.group_columns,
        *config.metadata_columns,
    }
    if config.id_column:
        required.add(config.id_column)
    missing_headers = sorted(required - set(headers))
    if missing_headers:
        raise ValueError(f"Source is missing configured columns: {missing_headers}")

    metadata_columns = list(
        dict.fromkeys([*config.group_columns, *config.metadata_columns])
    )
    records: list[SourceRecord] = []
    seen_ids: set[str] = set()
    for raw in raw_rows:
        text = clean_source_text(raw.get(config.text_column))
        if not text:
            continue
        position = normalize_space(raw.get("__source_position__"))
        source_id = (
            normalize_scalar(raw.get(config.id_column))
            if config.id_column
            else f"ROW-{len(records) + 1:06d}"
        )
        if not source_id:
            raise ValueError(f"Empty source ID at {position}")
        if source_id in seen_ids:
            raise ValueError(f"Duplicate source ID {source_id!r} at {position}")
        seen_ids.add(source_id)

        if config.group_columns:
            group_key = tuple(
                normalize_scalar(raw.get(column)) for column in config.group_columns
            )
            blank_groups = [
                column
                for column, value in zip(config.group_columns, group_key)
                if not value
            ]
            if blank_groups:
                raise ValueError(
                    f"Blank group values at {position}: {blank_groups}"
                )
        else:
            group_key = ("__ALL__",)
        metadata = {
            column: normalize_scalar(raw.get(column))
            for column in metadata_columns
        }
        metadata["source_position"] = position
        records.append(
            SourceRecord(
                source_id=source_id,
                text=text,
                group_key=group_key,
                metadata=metadata,
            )
        )
    if not records:
        raise ValueError("No non-empty source records were found")
    return records, headers


def build_chunks(
    records: Sequence[SourceRecord],
    *,
    max_rows: int,
    max_chars: int,
) -> list[SourceChunk]:
    grouped: dict[tuple[str, ...], list[SourceRecord]] = {}
    for record in records:
        if len(record.text) > max_chars:
            raise ValueError(
                f"Source {record.source_id} has {len(record.text)} characters, which exceeds "
                f"max_source_chars={max_chars}. Split the source unit or raise the limit."
            )
        grouped.setdefault(record.group_key, []).append(record)

    chunks_by_group: dict[tuple[str, ...], list[tuple[SourceRecord, ...]]] = {}
    for group_key, group_records in grouped.items():
        chunks: list[tuple[SourceRecord, ...]] = []
        current: list[SourceRecord] = []
        current_chars = 0
        for record in group_records:
            exceeds = current and (
                len(current) >= max_rows
                or current_chars + len(record.text) > max_chars
            )
            if exceeds:
                chunks.append(tuple(current))
                current = []
                current_chars = 0
            current.append(record)
            current_chars += len(record.text)
        if current:
            chunks.append(tuple(current))
        chunks_by_group[group_key] = chunks

    ordered: list[tuple[tuple[str, ...], tuple[SourceRecord, ...]]] = []
    max_rounds = max(len(chunks) for chunks in chunks_by_group.values())
    for round_index in range(max_rounds):
        for group_key, chunks in chunks_by_group.items():
            if round_index < len(chunks):
                ordered.append((group_key, chunks[round_index]))
    return [
        SourceChunk(
            chunk_id=f"CHUNK-{index:04d}",
            group_key=group_key,
            records=chunk_records,
        )
        for index, (group_key, chunk_records) in enumerate(ordered, start=1)
    ]


def render_system_prompt(config: AppConfig) -> tuple[str, str]:
    template = config.prompt.system_prompt_path.read_text(encoding="utf-8").strip()
    replacements = {
        "{{DATASET_NAME}}": config.dataset.name,
        "{{LANGUAGE}}": config.dataset.language,
        "{{DOMAIN}}": config.dataset.domain,
        "{{MAX_SOURCE_IDS}}": str(config.generation.max_source_ids_per_qa),
        "{{MAX_ANSWER_SENTENCES}}": str(config.generation.max_answer_sentences),
        "{{QUESTION_TYPES}}": ", ".join(config.generation.question_types),
        "{{DIFFICULTIES}}": ", ".join(config.generation.difficulties),
    }
    rendered = template
    for placeholder, value in replacements.items():
        rendered = rendered.replace(placeholder, value)
    unresolved = sorted(set(re.findall(r"\{\{[A-Z0-9_]+\}\}", rendered)))
    if unresolved:
        raise ValueError(f"Unresolved system-prompt placeholders: {unresolved}")
    return template, rendered


def load_few_shots(
    path: Path | None,
    generation: GenerationConfig,
) -> list[dict[str, Any]]:
    if path is None:
        return []
    value = read_json(path)
    if not isinstance(value, list):
        raise ValueError("Few-shot file must be a JSON array")
    output: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    seen_questions: set[str] = set()
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Few-shot {index} is not an object")
        name = _required_text(item.get("name", f"example-{index}"), "few-shot name")
        if name in seen_names:
            raise ValueError(f"Duplicate few-shot name: {name!r}")
        seen_names.add(name)
        source_records = item.get("source_records")
        expected = item.get("expected")
        if not isinstance(source_records, list) or not source_records:
            raise ValueError(f"Few-shot {name!r} needs source_records")
        if not isinstance(expected, dict):
            raise ValueError(f"Few-shot {name!r} needs an expected object")
        source_ids = []
        normalized_records = []
        for record in source_records:
            if not isinstance(record, dict):
                raise ValueError(f"Few-shot {name!r} has a non-object source record")
            source_id = _required_text(record.get("source_id"), "few-shot source_id")
            text = clean_source_text(record.get("text"))
            if not text:
                raise ValueError(f"Few-shot {name!r} text cannot be empty")
            metadata = record.get("metadata", {})
            if not isinstance(metadata, dict):
                raise ValueError(f"Few-shot {name!r} metadata must be an object")
            source_ids.append(source_id)
            normalized_records.append(
                {
                    "source_id": source_id,
                    "text": text,
                    "metadata": {
                        str(key): normalize_scalar(value)
                        for key, value in metadata.items()
                    },
                }
            )
        if len(source_ids) != len(set(source_ids)):
            raise ValueError(f"Few-shot {name!r} has duplicate source_ids")
        expected_ids = expected.get("source_ids")
        if not isinstance(expected_ids, list) or not expected_ids:
            raise ValueError(f"Few-shot {name!r} needs expected.source_ids")
        expected_ids = [normalize_space(value) for value in expected_ids]
        if not set(expected_ids).issubset(set(source_ids)):
            raise ValueError(
                f"Few-shot {name!r} expected source_ids are outside source_records"
            )
        question_type = _required_text(
            expected.get("question_type"), "few-shot question_type"
        )
        difficulty = _required_text(expected.get("difficulty"), "few-shot difficulty")
        if question_type not in generation.question_types:
            raise ValueError(f"Few-shot {name!r} has unsupported question_type")
        if difficulty not in generation.difficulties:
            raise ValueError(f"Few-shot {name!r} has unsupported difficulty")
        question = _required_text(expected.get("question"), "few-shot question")
        if not question.endswith(("?", "？")):
            raise ValueError(f"Few-shot {name!r} question must end with '?' or '？'")
        normalized_question = normalize_question(question)
        if not normalized_question or normalized_question in seen_questions:
            raise ValueError(f"Duplicate or empty few-shot question in {name!r}")
        seen_questions.add(normalized_question)
        answer = _required_text(expected.get("answer"), "few-shot answer")
        if count_sentences(answer) > generation.max_answer_sentences:
            raise ValueError(f"Few-shot {name!r} answer has too many sentences")
        output.append(
            {
                "name": name,
                "source_records": normalized_records,
                "expected": {
                    "question": question,
                    "answer": answer,
                    "source_ids": expected_ids,
                    "question_type": question_type,
                    "difficulty": difficulty,
                },
            }
        )
    return output


def format_generation_request(
    source_records: Sequence[Mapping[str, Any]],
    target_count: int,
    *,
    dataset_name: str,
    chunk_id: str,
) -> str:
    context = json.dumps(source_records, ensure_ascii=False, indent=2)
    return (
        f"dataset={dataset_name}\n"
        f"chunk_id={chunk_id}\n"
        f"Generate at most {target_count} QA items from SOURCE_RECORDS. "
        "Return fewer items when the evidence is insufficient.\n\n"
        f"SOURCE_RECORDS:\n{context}"
    )


def build_messages(
    *,
    system_prompt: str,
    few_shots: Sequence[Mapping[str, Any]],
    chunk: SourceChunk,
    target_count: int,
    dataset_name: str,
) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [
        {"role": "system", "content": system_prompt}
    ]
    for example in few_shots:
        messages.append(
            {
                "role": "user",
                "content": format_generation_request(
                    example["source_records"],
                    1,
                    dataset_name=dataset_name,
                    chunk_id=f"FEW-SHOT::{example['name']}",
                ),
            }
        )
        messages.append(
            {
                "role": "assistant",
                "content": json.dumps(
                    {"items": [example["expected"]]},
                    ensure_ascii=False,
                ),
            }
        )
    messages.append(
        {
            "role": "user",
            "content": format_generation_request(
                [record.to_prompt_dict() for record in chunk.records],
                target_count,
                dataset_name=dataset_name,
                chunk_id=chunk.chunk_id,
            ),
        }
    )
    return messages


def build_response_model(config: GenerationConfig) -> tuple[Any, Any]:
    try:
        from pydantic import ConfigDict, Field, create_model
        from typing import Annotated, Literal
    except ImportError as exc:
        raise RuntimeError(
            "Generation requires pydantic>=2; install requirements.txt"
        ) from exc

    question_type_literal = Literal.__getitem__(config.question_types)
    difficulty_literal = Literal.__getitem__(config.difficulties)
    source_ids_type = Annotated[
        list[str],
        Field(min_length=1, max_length=config.max_source_ids_per_qa),
    ]
    generated_qa = create_model(
        "GeneratedQA",
        __config__=ConfigDict(extra="forbid"),
        question=(Annotated[str, Field(min_length=5, max_length=500)], ...),
        answer=(Annotated[str, Field(min_length=1, max_length=1200)], ...),
        source_ids=(source_ids_type, ...),
        question_type=(question_type_literal, ...),
        difficulty=(difficulty_literal, ...),
    )
    items_type = Annotated[
        list[generated_qa],
        Field(max_length=config.qas_per_chunk),
    ]
    batch = create_model(
        "QABatch",
        __config__=ConfigDict(extra="forbid"),
        items=(items_type, ...),
    )
    return generated_qa, batch


def call_openai(
    client: Any,
    response_model: Any,
    *,
    model: str,
    messages: list[dict[str, str]],
    max_output_tokens: int,
    max_retries: int,
    retry_base_seconds: float,
) -> tuple[str, list[dict[str, Any]]]:
    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            response = client.responses.parse(
                model=model,
                input=messages,
                text_format=response_model,
                max_output_tokens=max_output_tokens,
                store=False,
            )
            parsed = response.output_parsed
            if parsed is None:
                status = getattr(response, "status", "unknown")
                raise RuntimeError(
                    f"Structured output is empty (response status={status})"
                )
            return response.id, [
                item.model_dump(mode="json") for item in parsed.items
            ]
        except Exception as exc:
            last_error = exc
            if attempt >= max_retries:
                break
            delay = retry_base_seconds * (2**attempt)
            print(
                f"  API error: {type(exc).__name__}; retrying in {delay:.1f}s "
                f"({attempt + 1}/{max_retries})"
            )
            time.sleep(delay)
    assert last_error is not None
    raise last_error


def count_sentences(text: str) -> int:
    stripped = text.strip()
    if not stripped:
        return 0
    boundaries = re.findall(r"[.!?。！？]+(?=\s|$)", stripped)
    return max(1, len(boundaries))


def is_near_duplicate(
    question: str,
    accepted: Sequence[Mapping[str, Any]],
    blocked_questions: set[str],
    *,
    threshold: float,
) -> bool:
    normalized = normalize_question(question)
    if not normalized or normalized in blocked_questions:
        return True
    for item in accepted:
        existing = normalize_question(normalize_space(item.get("question")))
        if normalized == existing:
            return True
        if SequenceMatcher(None, normalized, existing).ratio() >= threshold:
            return True
    return False


def validate_and_enrich(
    candidate: Mapping[str, Any],
    chunk: SourceChunk,
    *,
    app_config: AppConfig,
    response_id: str,
    generated_at: str,
) -> tuple[dict[str, Any] | None, str | None]:
    question = normalize_space(candidate.get("question"))
    answer = normalize_space(candidate.get("answer"))
    if not question.endswith(("?", "？")):
        return None, "question_without_question_mark"
    if not 5 <= len(question) <= 500:
        return None, "invalid_question_length"
    if not answer:
        return None, "empty_answer"
    if count_sentences(answer) > app_config.generation.max_answer_sentences:
        return None, "answer_has_too_many_sentences"

    raw_source_ids = candidate.get("source_ids")
    if not isinstance(raw_source_ids, list):
        return None, "invalid_source_ids"
    source_ids = list(
        dict.fromkeys(normalize_space(value) for value in raw_source_ids)
    )
    if not 1 <= len(source_ids) <= app_config.generation.max_source_ids_per_qa:
        return None, "invalid_source_id_count"
    chunk_by_id = {record.source_id: record for record in chunk.records}
    if any(source_id not in chunk_by_id for source_id in source_ids):
        return None, "source_id_outside_chunk"
    evidence_records = [chunk_by_id[source_id] for source_id in source_ids]

    question_type = normalize_space(candidate.get("question_type"))
    difficulty = normalize_space(candidate.get("difficulty"))
    if question_type not in app_config.generation.question_types:
        return None, "invalid_question_type"
    if difficulty not in app_config.generation.difficulties:
        return None, "invalid_difficulty"
    return (
        {
            "qa_id": "",
            "question": question,
            "answer": answer,
            "source_ids": source_ids,
            "evidence_text": [record.text for record in evidence_records],
            "evidence_metadata": [record.metadata for record in evidence_records],
            "group_key": list(chunk.group_key),
            "question_type": question_type,
            "difficulty": difficulty,
            "review_status": "pending",
            "reviewer": "",
            "review_notes": "",
            "source_file": app_config.input.path.name,
            "chunk_id": chunk.chunk_id,
            "generation_model": app_config.generation.model,
            "generation_response_id": response_id,
            "prompt_version": app_config.prompt.version,
            "generated_at": generated_at,
        },
        None,
    )


def load_resume_log(
    path: Path,
) -> tuple[set[str], list[dict[str, Any]], Counter[str]]:
    processed: set[str] = set()
    accepted: list[dict[str, Any]] = []
    rejected: Counter[str] = Counter()
    if not path.exists():
        return processed, accepted, rejected
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"Invalid log object at line {line_number}")
            if value.get("status") != "ok":
                continue
            processed.add(normalize_space(value.get("chunk_id")))
            batch = value.get("accepted", [])
            if not isinstance(batch, list):
                raise ValueError(f"Invalid accepted list at log line {line_number}")
            accepted.extend(batch)
            reasons = value.get("rejected", {})
            if not isinstance(reasons, dict):
                raise ValueError(f"Invalid rejected counts at log line {line_number}")
            rejected.update(
                {
                    normalize_space(key): int(count)
                    for key, count in reasons.items()
                }
            )
    return processed, accepted, rejected


def with_stable_ids(
    rows: Sequence[Mapping[str, Any]], prefix: str
) -> list[dict[str, Any]]:
    return [
        {**row, "qa_id": f"{prefix}-{index:04d}"}
        for index, row in enumerate(rows, start=1)
    ]


def serializable_config(config: AppConfig) -> dict[str, Any]:
    def relative(path: Path) -> str:
        return Path(
            os.path.relpath(path.resolve(), config.config_path.parent.resolve())
        ).as_posix()

    return {
        "dataset": asdict(config.dataset),
        "input": {
            **asdict(config.input),
            "path": relative(config.input.path),
        },
        "prompt": {
            **asdict(config.prompt),
            "system_prompt_path": relative(config.prompt.system_prompt_path),
            "few_shots_path": (
                relative(config.prompt.few_shots_path)
                if config.prompt.few_shots_path
                else None
            ),
        },
        "generation": asdict(config.generation),
    }


def build_run_identity(
    config: AppConfig,
    *,
    prompt_template: str,
    rendered_prompt: str,
) -> dict[str, Any]:
    few_shot_hash = (
        sha256_file(config.prompt.few_shots_path)
        if config.prompt.few_shots_path
        else None
    )
    identity = {
        "schema_version": "generic-grounded-qa-run-v1",
        "dataset_name": config.dataset.name,
        "input_sha256": sha256_file(config.input.path),
        "system_prompt_template_sha256": sha256_text(prompt_template),
        "rendered_system_prompt_sha256": sha256_text(rendered_prompt),
        "few_shots_sha256": few_shot_hash,
        "effective_config": serializable_config(config),
    }
    return {**identity, "fingerprint": stable_hash(identity)}


def build_manifest(
    *,
    identity: Mapping[str, Any],
    status: str,
    source_records: Sequence[SourceRecord],
    chunks: Sequence[SourceChunk],
    rows: Sequence[Mapping[str, Any]],
    rejection_reasons: Counter[str],
    started_at: str,
) -> dict[str, Any]:
    return {
        **identity,
        "status": status,
        "started_at": started_at,
        "updated_at": utc_now(),
        "source_record_count": len(source_records),
        "source_group_count": len({record.group_key for record in source_records}),
        "chunk_count": len(chunks),
        "qa_count": len(rows),
        "question_types": dict(Counter(row["question_type"] for row in rows)),
        "difficulties": dict(Counter(row["difficulty"] for row in rows)),
        "rejection_reasons": dict(rejection_reasons),
        "outputs": {
            "jsonl": "qa_dataset.jsonl",
            "csv": "qa_dataset.csv",
            "generation_log": "generation_log.jsonl",
        },
        "review_warning": (
            "Generated reference answers and source selections are pending human review."
        ),
    }


def print_dry_run(
    config: AppConfig,
    records: Sequence[SourceRecord],
    chunks: Sequence[SourceChunk],
    headers: Sequence[str],
    few_shot_count: int,
) -> None:
    print("[Dry run: no API calls]")
    print(f"dataset: {config.dataset.name}")
    print(f"source: {config.input.path}")
    print(f"columns: {', '.join(headers)}")
    print(f"valid source records: {len(records)}")
    print(f"groups: {len({record.group_key for record in records})}")
    print(f"chunks: {len(chunks)}")
    print(f"few-shot examples: {few_shot_count}")
    print(f"target QA count: {config.generation.target_size}")
    print("first chunks:")
    for chunk in chunks[:8]:
        print(
            f"  {chunk.chunk_id}: group={list(chunk.group_key)!r}, "
            f"records={len(chunk.records)}, chars={sum(len(r.text) for r in chunk.records)}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate an evidence-traceable QA dataset from CSV/JSON/JSONL/XLSX"
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--model", default="", help="Override generation.model")
    parser.add_argument(
        "--target-size",
        type=int,
        default=None,
        help="Override generation.target_size",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        from dotenv import load_dotenv

        load_dotenv(args.config.resolve().parent / ".env", override=False)
    except ImportError:
        pass
    config = load_config(
        args.config,
        model_override=args.model,
        target_size_override=args.target_size,
    )

    records, headers = load_source_records(config.input)
    chunks = build_chunks(
        records,
        max_rows=config.generation.max_source_rows,
        max_chars=config.generation.max_source_chars,
    )
    prompt_template, system_prompt = render_system_prompt(config)
    few_shots = load_few_shots(config.prompt.few_shots_path, config.generation)
    if args.dry_run:
        print_dry_run(config, records, chunks, headers, len(few_shots))
        return

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Run --dry-run first, then set the key in "
            "the environment or a .env file next to the config."
        )
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("Install requirements.txt before generation") from exc

    output_dir = (
        args.output_dir.resolve()
        if args.output_dir
        else (config.config_path.parent / "outputs" / config.dataset.name).resolve()
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / "generation_log.jsonl"
    manifest_path = output_dir / "manifest.json"
    identity = build_run_identity(
        config,
        prompt_template=prompt_template,
        rendered_prompt=system_prompt,
    )
    started_at = utc_now()
    if args.resume:
        if not manifest_path.exists():
            raise FileNotFoundError(
                f"Cannot resume without an existing manifest: {manifest_path}"
            )
        existing_manifest = read_json(manifest_path)
        if existing_manifest.get("fingerprint") != identity["fingerprint"]:
            raise ValueError(
                "Resume fingerprint mismatch: source, prompt, few-shots, model, or "
                "generation settings changed. Use a new output directory."
            )
        started_at = normalize_space(existing_manifest.get("started_at")) or started_at
        processed_chunks, accepted, rejection_reasons = load_resume_log(log_path)
        print(
            f"[resume] processed chunks={len(processed_chunks)}, "
            f"accepted QA={len(accepted)}"
        )
    else:
        if manifest_path.exists() or log_path.exists():
            raise FileExistsError(
                f"Output already contains a run: {output_dir}. "
                "Use --resume or choose another --output-dir."
            )
        existing_files = [
            path for path in output_dir.iterdir() if path.name != ".gitkeep"
        ]
        if existing_files:
            raise FileExistsError(
                f"Output directory is not empty: {output_dir}. "
                "Choose a new --output-dir."
            )
        processed_chunks, accepted, rejection_reasons = set(), [], Counter()

    _, response_model = build_response_model(config.generation)
    client = OpenAI(timeout=config.generation.timeout_seconds)
    blocked_questions = {
        normalize_question(example["expected"]["question"])
        for example in few_shots
    }
    initial_rows = with_stable_ids(
        accepted[: config.generation.target_size],
        config.dataset.qa_id_prefix,
    )
    write_json_atomic(
        manifest_path,
        build_manifest(
            identity=identity,
            status="running",
            source_records=records,
            chunks=chunks,
            rows=initial_rows,
            rejection_reasons=rejection_reasons,
            started_at=started_at,
        ),
    )

    for chunk in chunks:
        if len(accepted) >= config.generation.target_size:
            break
        if chunk.chunk_id in processed_chunks:
            continue
        remaining = config.generation.target_size - len(accepted)
        requested = min(config.generation.qas_per_chunk, remaining)
        messages = build_messages(
            system_prompt=system_prompt,
            few_shots=few_shots,
            chunk=chunk,
            target_count=requested,
            dataset_name=config.dataset.name,
        )
        print(
            f"[{chunk.chunk_id}] group={list(chunk.group_key)!r} "
            f"records={len(chunk.records)} requested={requested}"
        )
        started = time.perf_counter()
        try:
            response_id, candidates = call_openai(
                client,
                response_model,
                model=config.generation.model,
                messages=messages,
                max_output_tokens=config.generation.max_output_tokens,
                max_retries=config.generation.max_retries,
                retry_base_seconds=config.generation.retry_base_seconds,
            )
        except Exception as exc:
            append_jsonl(
                log_path,
                {
                    "status": "error",
                    "chunk_id": chunk.chunk_id,
                    "source_ids": [record.source_id for record in chunk.records],
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "logged_at": utc_now(),
                },
            )
            print(f"  failed: {type(exc).__name__}: {exc}")
            continue

        generated_at = utc_now()
        accepted_this_chunk: list[dict[str, Any]] = []
        rejected_this_chunk: Counter[str] = Counter()
        for candidate in candidates[:requested]:
            enriched, reason = validate_and_enrich(
                candidate,
                chunk,
                app_config=config,
                response_id=response_id,
                generated_at=generated_at,
            )
            if reason is not None or enriched is None:
                rejected_this_chunk[reason or "unknown_validation_error"] += 1
                continue
            if is_near_duplicate(
                enriched["question"],
                [*accepted, *accepted_this_chunk],
                blocked_questions,
                threshold=config.generation.duplicate_threshold,
            ):
                rejected_this_chunk["duplicate_question"] += 1
                continue
            accepted_this_chunk.append(enriched)
        accepted.extend(accepted_this_chunk)
        rejection_reasons.update(rejected_this_chunk)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
        append_jsonl(
            log_path,
            {
                "status": "ok",
                "chunk_id": chunk.chunk_id,
                "source_ids": [record.source_id for record in chunk.records],
                "response_id": response_id,
                "candidate_count": len(candidates),
                "accepted": accepted_this_chunk,
                "rejected": dict(rejected_this_chunk),
                "elapsed_ms": elapsed_ms,
                "logged_at": utc_now(),
            },
        )
        print(
            f"  candidates={len(candidates)} accepted={len(accepted_this_chunk)} "
            f"total={len(accepted)}/{config.generation.target_size}"
        )

    final_rows = with_stable_ids(
        accepted[: config.generation.target_size],
        config.dataset.qa_id_prefix,
    )
    write_jsonl_atomic(output_dir / "qa_dataset.jsonl", final_rows)
    write_csv_atomic(output_dir / "qa_dataset.csv", final_rows)
    status = (
        "complete"
        if len(final_rows) >= config.generation.target_size
        else "partial"
    )
    write_json_atomic(
        manifest_path,
        build_manifest(
            identity=identity,
            status=status,
            source_records=records,
            chunks=chunks,
            rows=final_rows,
            rejection_reasons=rejection_reasons,
            started_at=started_at,
        ),
    )
    print(f"[{status}] QA={len(final_rows)} output={output_dir}")
    if status == "partial":
        print(
            "The target was not reached. Review generation_log.jsonl, source coverage, "
            "and prompt quality before changing settings."
        )


if __name__ == "__main__":
    main()
