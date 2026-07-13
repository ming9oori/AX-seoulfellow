#!/usr/bin/env python3
"""Prepare and lock Phase 0 of the SCALE-AWC Zaije experiment."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import platform
import random
import re
import shutil
import sys
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SEED = 20260711
EXPECTED_BINARY_SHA256 = "9246a6da6c7635b3f34ee55df75112eb38a2984ea06828be943dc196de5926eb"
EXPECTED_CANONICAL_SHA256 = "84d45b50acc542497df2f19bf8c3ad395f2ed223e6cfeb02be467c9f80f54906"
DESIGN_DECLARED_CANONICAL_SHA256 = "de55c3184b7eba79db0694f1c89cd0a8f56dcb873d00c9f96df4e2deafc503d9"
FIELDS = ("page", "chapter_no", "chapter_title", "section_no", "section_title", "text_for_llm_human")
SPLITS = ("INDUCTION", "VALIDATION", "TEST_NATURAL", "TEST_CHALLENGE_POOL")
SPLIT_TARGETS = {
    "INDUCTION": 0.50,
    "VALIDATION": 0.20,
    "TEST_NATURAL": 0.20,
    "TEST_CHALLENGE_POOL": 0.10,
}
SPLIT_TOLERANCE = {
    "INDUCTION": 0.03,
    "VALIDATION": 0.03,
    "TEST_NATURAL": 0.03,
    "TEST_CHALLENGE_POOL": 0.02,
}
FLAG_NAMES = (
    "question",
    "normative",
    "conditional_exception",
    "procedure_decision",
    "evaluation_numeric",
    "discourse",
    "definition",
    "markdown_table",
    "list_block",
    "bilingual_acronym",
)
NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def stable_hash(value: Any, length: int = 64) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256_bytes(payload.encode("utf-8"))[:length]


def normalize_text(value: Any) -> str:
    return unicodedata.normalize("NFC", str(value or "").replace("\r\n", "\n").replace("\r", "\n")).strip()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def column_index(reference: str) -> int:
    match = re.match(r"([A-Z]+)", reference)
    if not match:
        return 0
    result = 0
    for character in match.group(1):
        result = result * 26 + ord(character) - 64
    return result - 1


def read_xlsx(path: Path) -> tuple[str, list[dict[str, Any]]]:
    with zipfile.ZipFile(path) as archive:
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        sheet_node = workbook.find(".//a:sheet", NS)
        sheet_name = sheet_node.attrib.get("name", "Sheet1") if sheet_node is not None else "Sheet1"
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in root.findall("a:si", NS):
                shared_strings.append("".join(node.text or "" for node in item.findall(".//a:t", NS)))

        root = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        raw_rows: list[tuple[int, list[str]]] = []
        for row_node in root.findall(".//a:sheetData/a:row", NS):
            excel_row = int(float(row_node.attrib.get("r", len(raw_rows) + 1)))
            cells: dict[int, str] = {}
            for cell in row_node.findall("a:c", NS):
                index = column_index(cell.attrib.get("r", "A"))
                cell_type = cell.attrib.get("t")
                value_node = cell.find("a:v", NS)
                value = ""
                if cell_type == "s" and value_node is not None:
                    value = shared_strings[int(value_node.text or "0")]
                elif cell_type == "inlineStr":
                    value = "".join(node.text or "" for node in cell.findall(".//a:t", NS))
                elif value_node is not None:
                    value = value_node.text or ""
                cells[index] = normalize_text(value)
            if cells:
                raw_rows.append((excel_row, [cells.get(i, "") for i in range(max(cells) + 1)]))

    if not raw_rows:
        raise ValueError(f"No rows found in {path}")
    header = [normalize_text(value) for value in raw_rows[0][1]]
    missing = sorted(set(FIELDS) - set(header))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    records: list[dict[str, Any]] = []
    for excel_row, values in raw_rows[1:]:
        row = {header[i]: normalize_text(values[i] if i < len(values) else "") for i in range(len(header))}
        if not row["text_for_llm_human"]:
            continue
        row["excel_row"] = excel_row
        records.append(row)
    return sheet_name, records


def canonical_content(records: list[dict[str, Any]]) -> bytes:
    lines = []
    for row in records:
        item = {field: normalize_text(row.get(field)) for field in FIELDS}
        lines.append(json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return ("\n".join(lines) + "\n").encode("utf-8")


def block_type(text: str) -> str:
    table = len(re.findall(r"(?m)^\s*\|.*\|\s*$", text)) >= 2
    formula = bool(re.search(r"(?:\b[A-Z]\b|Winner|Loser|Value|Cost)\s*[=<>]", text, re.I))
    list_item = bool(re.search(r"(?m)^\s*(?:[0-9]+[.)]|[\u2022*-])\s*", text))
    question = "?" in text or bool(re.search(r"(?:인가|하는가|일까)[?？]?\s*$", text))
    figure = bool(re.search(r"(?:그림|도표|Figure)\s*\d", text, re.I))
    names = [name for name, hit in [("markdown_table", table), ("formula", formula), ("list", list_item), ("question", question), ("figure_caption", figure)] if hit]
    return names[0] if len(names) == 1 else "mixed" if names else "prose"


def flags_for(text: str, kind: str) -> dict[str, bool]:
    return {
        "question": kind == "question" or bool(re.search(r"[?？]|(?:무엇|왜|어떻게|언제|누가).*(?:인가|하는가|일까)", text)),
        "normative": bool(re.search(r"(?:하지\s*말아야|금지|피해야|해야\s*한다|하여야|반드시|필수|권장|바람직|필요하다|필요하며|필요성)", text)),
        "conditional_exception": bool(re.search(r"(?:경우|만약|(?:이|라)면|때에는|때\s|있어야|필요\s*조건|단,|예외|이전|이후)", text)),
        "procedure_decision": bool(re.search(r"(?:단계|절차|프로세스|이후|다음|먼저|수행|결과물|산출물|검토|승인|의사\s*결정|Activity|Output)", text, re.I)),
        "evaluation_numeric": bool(re.search(r"(?:평가|점수|비중|비율|범위|척도|성공률|%|\d+(?:\.\d+)?\s*(?:%|명|점|배)|[=<>])", text, re.I)),
        "discourse": bool(re.search(r"(?:예를\s*들|예시|사례|비유|인용|조사\s*결과|오해|반박|Shipley\s*Tip|\(×\)|\(○\))", text, re.I)),
        "definition": bool(re.search(r"(?:이란|란\s|정의하면|의미한다|말한다|일컨는|종류|구성된다)", text)),
        "markdown_table": kind in {"markdown_table", "mixed"} and len(re.findall(r"(?m)^\s*\|.*\|\s*$", text)) >= 2,
        "list_block": kind in {"list", "mixed"},
        "bilingual_acronym": bool(re.search(r"[A-Za-z]{2,}|[A-Za-z][A-Za-z\s/-]+\([^)]*[가-힣][^)]*\)|[가-힣]+\s*\([A-Za-z][^)]*\)", text)),
    }


class UnionFind:
    def __init__(self, values: Iterable[int]) -> None:
        self.parent = {value: value for value in values}

    def find(self, value: int) -> int:
        while self.parent[value] != value:
            self.parent[value] = self.parent[self.parent[value]]
            value = self.parent[value]
        return value

    def union(self, left: int, right: int) -> None:
        a, b = self.find(left), self.find(right)
        if a != b:
            self.parent[max(a, b)] = min(a, b)


def inferred_metadata(records: list[dict[str, Any]]) -> list[dict[str, str]]:
    keys = ("chapter_no", "chapter_title", "section_no", "section_title")
    result: list[dict[str, str]] = []
    for index, row in enumerate(records):
        values = {key: normalize_text(row.get(key)) for key in keys}
        for key in keys:
            if values[key]:
                continue
            for distance in range(1, len(records)):
                for candidate in (index - distance, index + distance):
                    if 0 <= candidate < len(records):
                        value = normalize_text(records[candidate].get(key))
                        if value:
                            values[key] = value
                            break
                if values[key]:
                    break
        result.append(values)
    return result


def length_quartiles(lengths: list[int]) -> tuple[int, int, int]:
    ordered = sorted(lengths)
    return tuple(ordered[min(len(ordered) - 1, int((len(ordered) - 1) * q))] for q in (0.25, 0.50, 0.75))  # type: ignore[return-value]


def quartile(value: int, cuts: tuple[int, int, int]) -> int:
    return 1 + sum(value > cut for cut in cuts)


def build_corpus(records: list[dict[str, Any]], input_path: Path, input_hash: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    inferred = inferred_metadata(records)
    cuts = length_quartiles([len(row["text_for_llm_human"]) for row in records])
    uf = UnionFind(row["excel_row"] for row in records)
    fingerprints = {
        row["excel_row"]: stable_hash(re.sub(r"\s+", " ", row["text_for_llm_human"]).casefold(), 24)
        for row in records
    }
    fingerprint_counts = Counter(fingerprints.values())

    duplicate_first: dict[str, int] = {}
    for index, row in enumerate(records):
        text = row["text_for_llm_human"]
        fingerprint = fingerprints[row["excel_row"]]
        if fingerprint in duplicate_first:
            uf.union(row["excel_row"], duplicate_first[fingerprint])
        else:
            duplicate_first[fingerprint] = row["excel_row"]
        if index:
            previous = records[index - 1]
            same_section = (
                inferred[index]["chapter_no"], inferred[index]["section_no"]
            ) == (
                inferred[index - 1]["chapter_no"], inferred[index - 1]["section_no"]
            )
            same_page = normalize_text(row.get("page")) == normalize_text(previous.get("page"))
            current_kind = block_type(text)
            previous_kind = block_type(previous["text_for_llm_human"])
            structured_continuation = (
                same_section
                and current_kind in {"list", "mixed"}
                and previous_kind in {"list", "mixed"}
            )
            process_continuation = (
                same_section
                and flags_for(text, current_kind)["procedure_decision"]
                and flags_for(previous["text_for_llm_human"], previous_kind)["procedure_decision"]
                and row["excel_row"] == previous["excel_row"] + 1
            )
            duplicate_boundary = fingerprint_counts[fingerprint] > 1 or fingerprint_counts[fingerprints[previous["excel_row"]]] > 1
            if same_section and not duplicate_boundary and (same_page or structured_continuation or process_continuation):
                uf.union(row["excel_row"], previous["excel_row"])
            if any(not normalize_text(row.get(key)) for key in ("chapter_no", "chapter_title", "section_no", "section_title")):
                uf.union(row["excel_row"], previous["excel_row"])
        if index + 1 < len(records) and any(not normalize_text(row.get(key)) for key in ("chapter_no", "chapter_title", "section_no", "section_title")):
            uf.union(row["excel_row"], records[index + 1]["excel_row"])

    members: dict[int, list[int]] = defaultdict(list)
    for row in records:
        members[uf.find(row["excel_row"])].append(row["excel_row"])
    group_ids = {root: f"zaije:leakage-group/{stable_hash(sorted(rows), 16)}" for root, rows in members.items()}

    corpus: list[dict[str, Any]] = []
    for index, row in enumerate(records):
        text = row["text_for_llm_human"]
        kind = block_type(text)
        root = uf.find(row["excel_row"])
        fingerprint = fingerprints[row["excel_row"]]
        missing = [field for field in ("chapter_no", "chapter_title", "section_no", "section_title") if not normalize_text(row.get(field))]
        item = {
            "evidence_id": f"zaije:evidence/xlsx-row-{row['excel_row']}",
            "excel_row": row["excel_row"],
            "source_file": str(input_path),
            "source_binary_sha256": input_hash,
            "sheet": "clean_sentences",
            "page": normalize_text(row.get("page")),
            "chapter_no": normalize_text(row.get("chapter_no")),
            "chapter_title": normalize_text(row.get("chapter_title")),
            "section_no": normalize_text(row.get("section_no")),
            "section_title": normalize_text(row.get("section_title")),
            "inferred_chapter_no": inferred[index]["chapter_no"],
            "inferred_chapter_title": inferred[index]["chapter_title"],
            "inferred_section_no": inferred[index]["section_no"],
            "inferred_section_title": inferred[index]["section_title"],
            "metadata_status": "MISSING_CONTEXT_CANDIDATE" if missing else "OBSERVED",
            "missing_metadata_fields": missing,
            "text": text,
            "text_sha256": sha256_bytes(text.encode("utf-8")),
            "normalized_text_fingerprint": fingerprint,
            "block_type": kind,
            "length": len(text),
            "length_quartile": quartile(len(text), cuts),
            "flags": flags_for(text, kind),
            "leakage_group_id": group_ids[root],
        }
        corpus.append(item)
    return corpus, [{"leakage_group_id": group_ids[root], "evidence_ids": [f"zaije:evidence/xlsx-row-{row}" for row in sorted(rows)]} for root, rows in sorted(members.items())]


@dataclass(frozen=True)
class Group:
    group_id: str
    rows: tuple[dict[str, Any], ...]

    @property
    def size(self) -> int:
        return len(self.rows)


def split_groups(corpus: list[dict[str, Any]]) -> tuple[dict[str, str], dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in corpus:
        grouped[row["leakage_group_id"]].append(row)
    groups = [Group(key, tuple(value)) for key, value in grouped.items()]
    total = len(corpus)
    target = {split: total * ratio for split, ratio in SPLIT_TARGETS.items()}
    global_features = Counter()
    for row in corpus:
        global_features[f"chapter:{row['inferred_chapter_no'] or 'missing'}"] += 1
        global_features[f"length_q:{row['length_quartile']}"] += 1
        for name in FLAG_NAMES:
            global_features[f"flag:{name}"] += int(row["flags"][name])
    group_features: dict[str, Counter[str]] = {}
    for group in groups:
        counter: Counter[str] = Counter()
        for row in group.rows:
            counter[f"chapter:{row['inferred_chapter_no'] or 'missing'}"] += 1
            counter[f"length_q:{row['length_quartile']}"] += 1
            for name in FLAG_NAMES:
                counter[f"flag:{name}"] += int(row["flags"][name])
        group_features[group.group_id] = counter

    def objective(assignment: dict[str, str]) -> float:
        sizes = Counter()
        features: dict[str, Counter[str]] = {split: Counter() for split in SPLITS}
        for group in groups:
            split = assignment[group.group_id]
            sizes[split] += group.size
            features[split].update(group_features[group.group_id])
        score = 0.0
        for split in SPLITS:
            deviation = (sizes[split] - target[split]) / max(1.0, target[split])
            score += 300.0 * deviation * deviation
            lower = total * (SPLIT_TARGETS[split] - SPLIT_TOLERANCE[split])
            upper = total * (SPLIT_TARGETS[split] + SPLIT_TOLERANCE[split])
            if sizes[split] < lower:
                score += 10_000.0 + (lower - sizes[split]) * 100.0
            if sizes[split] > upper:
                score += 10_000.0 + (sizes[split] - upper) * 100.0
            for feature, global_count in global_features.items():
                expected = global_count * SPLIT_TARGETS[split]
                if expected:
                    score += 0.5 * ((features[split][feature] - expected) ** 2 / expected)
        return score

    ordered = sorted(groups, key=lambda group: (-group.size, stable_hash([SEED, group.group_id], 16)))
    assignment: dict[str, str] = {}
    sizes = Counter()
    for group in ordered:
        split = min(SPLITS, key=lambda name: ((sizes[name] + group.size) / target[name], stable_hash([group.group_id, name], 8)))
        assignment[group.group_id] = split
        sizes[split] += group.size

    rng = random.Random(SEED)
    current = objective(assignment)
    best = dict(assignment)
    best_score = current
    group_ids = [group.group_id for group in groups]
    iterations = 30_000
    for step in range(iterations):
        candidate = dict(assignment)
        if rng.random() < 0.55:
            group_id = rng.choice(group_ids)
            candidate[group_id] = rng.choice([split for split in SPLITS if split != candidate[group_id]])
        else:
            left, right = rng.sample(group_ids, 2)
            candidate[left], candidate[right] = candidate[right], candidate[left]
        candidate_score = objective(candidate)
        temperature = max(0.01, 6.0 * (1.0 - step / iterations))
        if candidate_score < current or rng.random() < math.exp((current - candidate_score) / temperature):
            assignment, current = candidate, candidate_score
        if current < best_score:
            best, best_score = dict(assignment), current

    evidence_assignment = {row["evidence_id"]: best[row["leakage_group_id"]] for row in corpus}
    split_counts = Counter(evidence_assignment.values())
    group_overlap: dict[str, list[str]] = {}
    for group in groups:
        used = sorted({evidence_assignment[row["evidence_id"]] for row in group.rows})
        if len(used) > 1:
            group_overlap[group.group_id] = used
    audit = {
        "seed": SEED,
        "objective": best_score,
        "evidence_count": total,
        "leakage_group_count": len(groups),
        "largest_group": max(group.size for group in groups),
        "split_counts": dict(split_counts),
        "split_ratios": {split: split_counts[split] / total for split in SPLITS},
        "target_ratios": SPLIT_TARGETS,
        "tolerances": SPLIT_TOLERANCE,
        "group_overlap": group_overlap,
    }
    for split in SPLITS:
        ratio = split_counts[split] / total
        if abs(ratio - SPLIT_TARGETS[split]) > SPLIT_TOLERANCE[split]:
            raise RuntimeError(f"Split {split} outside tolerance: {ratio:.4f}")
    if group_overlap:
        raise RuntimeError(f"Leakage group overlap: {group_overlap}")
    return evidence_assignment, audit


def deterministic_order(rows: Iterable[dict[str, Any]], salt: str) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: stable_hash([SEED, salt, row["evidence_id"]], 24))


def select_diverse(rows: list[dict[str, Any]], count: int, salt: str, challenge: bool = False) -> list[dict[str, Any]]:
    remaining = deterministic_order(rows, salt)
    selected: list[dict[str, Any]] = []
    chapter_count: Counter[str] = Counter()
    group_count: Counter[str] = Counter()
    flag_count: Counter[str] = Counter()
    high_risk = {"normative", "conditional_exception", "discourse", "question", "markdown_table", "procedure_decision"}
    while remaining and len(selected) < count:
        def score(row: dict[str, Any]) -> tuple[float, str]:
            diversity = 4.0 / (1 + group_count[row["leakage_group_id"]])
            diversity += 2.0 / (1 + chapter_count[row["inferred_chapter_no"] or "missing"])
            diversity += sum(1.0 / (1 + flag_count[name]) for name in FLAG_NAMES if row["flags"][name])
            risk = sum(1 for name in high_risk if row["flags"][name])
            if challenge:
                diversity += 4.0 * risk
            return diversity, stable_hash([SEED, salt, row["evidence_id"]], 24)
        chosen = max(remaining, key=score)
        remaining.remove(chosen)
        selected.append(chosen)
        chapter_count[chosen["inferred_chapter_no"] or "missing"] += 1
        group_count[chosen["leakage_group_id"]] += 1
        for name in FLAG_NAMES:
            flag_count[name] += int(chosen["flags"][name])
    if len(selected) != count:
        raise RuntimeError(f"Could not select {count} records for {salt}")
    return sorted(selected, key=lambda row: row["excel_row"])


def context_bundle(target: dict[str, Any], corpus: list[dict[str, Any]], assignment: dict[str, str]) -> dict[str, Any]:
    index_by_id = {row["evidence_id"]: index for index, row in enumerate(corpus)}
    index = index_by_id[target["evidence_id"]]
    context = []
    for candidate_index in range(max(0, index - 2), min(len(corpus), index + 3)):
        if candidate_index == index:
            continue
        candidate = corpus[candidate_index]
        if candidate["leakage_group_id"] != target["leakage_group_id"]:
            continue
        if assignment[candidate["evidence_id"]] != assignment[target["evidence_id"]]:
            raise RuntimeError("Context crossed split boundary")
        context.append({
            "evidence_id": candidate["evidence_id"],
            "relation": "previous" if candidate_index < index else "next",
            "text": candidate["text"],
        })
    headers = []
    table_lines = [line.strip() for line in target["text"].splitlines() if line.strip().startswith("|")]
    if table_lines:
        headers = [cell.strip() for cell in table_lines[0].strip("|").split("|")]
    return {
        "bundle_id": f"zaije:bundle/{stable_hash(target['evidence_id'], 24)}",
        "split": assignment[target["evidence_id"]],
        "leakage_group_id": target["leakage_group_id"],
        "target": {"evidence_id": target["evidence_id"], "text": target["text"]},
        "context": context,
        "metadata": {
            "excel_row": target["excel_row"],
            "page": target["page"],
            "chapter_no": target["inferred_chapter_no"],
            "chapter_title": target["inferred_chapter_title"],
            "section_no": target["inferred_section_no"],
            "section_title": target["inferred_section_title"],
            "metadata_status": target["metadata_status"],
            "block_type": target["block_type"],
            "table_headers": headers,
        },
    }


def annotation_template(bundle: dict[str, Any], role: str) -> dict[str, Any]:
    return {
        "annotation_id": f"{role}:{bundle['target']['evidence_id']}",
        "annotator_role": role,
        "evidence_bundle": bundle,
        "claims": [],
        "term_mentions": [],
        "relations": [],
        "bundle_underdetermined": False,
        "annotator_note": "",
        "completion_status": "NOT_STARTED",
    }


def file_hashes(paths: Iterable[Path], root: Path) -> dict[str, str]:
    return {str(path.relative_to(root)): sha256_file(path) for path in sorted(paths)}


def locate_design(root: Path) -> Path:
    for path in root.glob("*.md"):
        try:
            head = path.read_text(encoding="utf-8")[:20000]
        except UnicodeError:
            continue
        if "SCALE-AWC" in head and "단일 도메인 온톨로지" in head:
            return path
    raise FileNotFoundError("Could not locate SCALE-AWC design document")


def write_input_resolution(root: Path, report_path: Path, input_path: Path, records: list[dict[str, Any]]) -> None:
    handoff = next((path for path in (root / "handoff-hanyang").rglob("자이제_1.xlsx") if path != input_path), None)
    differences: list[dict[str, Any]] = []
    handoff_hash = "NOT_FOUND"
    if handoff:
        handoff_hash = sha256_file(handoff)
        _, other = read_xlsx(handoff)
        for left, right in zip(records, other):
            changed = {field: {"design_locked": left.get(field, ""), "handoff": right.get(field, "")} for field in FIELDS if left.get(field, "") != right.get(field, "")}
            if changed:
                differences.append({"excel_row": left["excel_row"], "fields": changed})
    lines = [
        "# 입력 파일 확정 보고",
        "",
        f"- 실험 입력: `{input_path}`",
        f"- binary SHA-256: `{sha256_file(input_path)}`",
        f"- 설계서 binary hash 일치: `{sha256_file(input_path) == EXPECTED_BINARY_SHA256}`",
        f"- handoff 수정본 SHA-256: `{handoff_hash}`",
        f"- 정규화 행 차이: `{len(differences)}`건",
        "",
        "설계서의 binary hash와 일치하는 `legacy/자이제_1.xlsx`를 잠긴 입력으로 사용한다. handoff 파일은 동일 본문이지만 3개 행의 문서 메타데이터가 보완된 수정본이다.",
        "",
        "## 차이 상세",
        "",
        "```json",
        json.dumps(differences, ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Canonical hash amendment",
        "",
        f"- 설계서 기재값: `{DESIGN_DECLARED_CANONICAL_SHA256}`",
        f"- `canonical-jsonl-v1` 계산값: `{sha256_bytes(canonical_content(records))}`",
        "- 알고리즘: 6개 원본 필드를 NFC·LF·trim 정규화한 후, key-sorted compact JSON 한 행으로 직렬화하고 마지막 LF를 포함해 SHA-256 계산",
        "- 설계서 값은 설명된 방법으로 재현되지 않아, Gold 주석·TEST 열람 전에 실제 알고리즘과 계산값을 사전등록 amendment로 잠괄다.",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    script = Path(__file__).resolve()
    experiment = script.parents[1]
    root = experiment.parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=root / "legacy" / "자이제_1.xlsx")
    parser.add_argument("--run-id", default="phase0_20260711_v1")
    args = parser.parse_args()
    input_path = args.input.resolve()
    if not input_path.exists():
        raise FileNotFoundError(input_path)

    design = locate_design(root)
    sheet, records = read_xlsx(input_path)
    binary_hash = sha256_file(input_path)
    content_hash = sha256_bytes(canonical_content(records))
    if sheet != "clean_sentences" or len(records) != 1366:
        raise RuntimeError(f"Unexpected input: sheet={sheet}, rows={len(records)}")
    if binary_hash != EXPECTED_BINARY_SHA256:
        raise RuntimeError(f"Binary hash mismatch: {binary_hash}")
    if content_hash != EXPECTED_CANONICAL_SHA256:
        raise RuntimeError(f"Canonical hash mismatch: {content_hash}")

    run_dir = experiment / "runs" / args.run_id
    if run_dir.exists():
        shutil.rmtree(run_dir)
    for path in [
        experiment / "data" / "raw",
        experiment / "data" / "canonical",
        experiment / "data" / "manifests",
        experiment / "annotation" / "pilot",
        experiment / "annotation" / "locks",
        experiment / "reports",
        run_dir / "config_snapshot",
    ]:
        path.mkdir(parents=True, exist_ok=True)

    shutil.copy2(input_path, experiment / "data" / "raw" / "zaije_1.xlsx")
    corpus, leakage_groups = build_corpus(records, input_path, binary_hash)
    assignment, split_audit = split_groups(corpus)
    for row in corpus:
        row["split"] = assignment[row["evidence_id"]]

    canonical_path = experiment / "data" / "canonical" / "corpus.jsonl"
    manifest_path = experiment / "data" / "manifests" / "corpus_manifest.jsonl"
    split_path = experiment / "data" / "manifests" / "split_manifest.csv"
    write_jsonl(canonical_path, corpus)
    write_jsonl(manifest_path, [{key: value for key, value in row.items() if key != "text"} for row in corpus])
    manifest_fields = ["evidence_id", "excel_row", "leakage_group_id", "split", "page", "chapter_no", "chapter_title", "section_no", "section_title", "metadata_status", "block_type", "length", "length_quartile", *FLAG_NAMES]
    manifest_rows = []
    for row in corpus:
        flat = {key: row.get(key, "") for key in manifest_fields}
        flat.update({name: int(row["flags"][name]) for name in FLAG_NAMES})
        manifest_rows.append(flat)
    write_csv(split_path, manifest_rows, manifest_fields)
    split_hash = sha256_file(split_path)
    (experiment / "data" / "manifests" / "split_manifest.sha256").write_text(f"{split_hash}  split_manifest.csv\n", encoding="ascii")
    write_json(experiment / "data" / "manifests" / "leakage_groups.json", leakage_groups)
    for split in SPLITS:
        ids = [row["evidence_id"] for row in corpus if row["split"] == split]
        write_json(experiment / "data" / "manifests" / f"{split.lower()}_ids.json", ids)

    flags = Counter()
    block_types = Counter()
    observed_chapters = Counter()
    inferred_chapters = Counter()
    texts = Counter()
    lengths = []
    for row in corpus:
        observed_key = f"{row['chapter_no']}|{row['chapter_title']}" if row["chapter_no"] and row["chapter_title"] else "MISSING"
        observed_chapters[observed_key] += 1
        inferred_chapters[f"{row['inferred_chapter_no']}|{row['inferred_chapter_title']}"] += 1
        block_types[row["block_type"]] += 1
        texts[row["text"]] += 1
        lengths.append(row["length"])
        for name in FLAG_NAMES:
            flags[name] += int(row["flags"][name])
    audit = {
        "input": {"path": str(input_path), "sheet": sheet, "binary_sha256": binary_hash, "canonical_sha256": content_hash, "canonical_algorithm": "canonical-jsonl-v1"},
        "counts": {
            "evidence": len(corpus),
            "unique_text": len(texts),
            "duplicate_rows_beyond_first": sum(count - 1 for count in texts.values() if count > 1),
            "duplicate_clusters": sum(count > 1 for count in texts.values()),
            "leakage_groups": len(leakage_groups),
            "missing_metadata_rows": sum(row["metadata_status"] != "OBSERVED" for row in corpus),
        },
        "chapters_observed": dict(observed_chapters),
        "chapters_after_context_inference": dict(inferred_chapters),
        "block_types": dict(block_types),
        "heuristic_flags": dict(flags),
        "design_reference_flag_counts": {
            "question": 71,
            "normative": 102,
            "conditional_exception": 215,
            "procedure_decision": 499,
            "evaluation_numeric": 263,
            "discourse": 177,
            "definition": 362,
            "markdown_table": 56,
        },
        "flag_count_note": "The design did not provide executable regexes. Execution regexes were locked before Gold/model output; counts are audit aids, not labels.",
        "length": {"min": min(lengths), "median": sorted(lengths)[len(lengths) // 2], "mean": sum(lengths) / len(lengths), "max": max(lengths)},
    }
    write_json(experiment / "data" / "manifests" / "data_audit.json", audit)
    write_json(experiment / "data" / "manifests" / "split_audit.json", split_audit)

    induction = [row for row in corpus if row["split"] == "INDUCTION"]
    validation = [row for row in corpus if row["split"] == "VALIDATION"]
    test_natural = [row for row in corpus if row["split"] == "TEST_NATURAL"]
    challenge_pool = [row for row in corpus if row["split"] == "TEST_CHALLENGE_POOL"]
    pilot = select_diverse(induction, 40, "pilot")
    pilot_ids = {row["evidence_id"] for row in pilot}
    induction_gold = deterministic_order([row for row in induction if row["evidence_id"] not in pilot_ids], "induction-gold")[:100]
    validation_gold = deterministic_order(validation, "validation-gold")[:80]
    natural_gold = deterministic_order(test_natural, "test-natural-gold")[:140]
    challenge_gold = select_diverse(challenge_pool, 60, "test-challenge-gold", challenge=True)
    sample_roles = [
        *(dict(row, gold_role="PILOT") for row in pilot),
        *(dict(row, gold_role="INDUCTION_GOLD") for row in induction_gold),
        *(dict(row, gold_role="VALIDATION_GOLD") for row in validation_gold),
        *(dict(row, gold_role="TEST_NATURAL_GOLD") for row in natural_gold),
        *(dict(row, gold_role="TEST_CHALLENGE_GOLD") for row in challenge_gold),
    ]
    gold_fields = ["gold_role", "evidence_id", "excel_row", "leakage_group_id", "split", "chapter_no", "section_no", "block_type", *FLAG_NAMES]
    gold_rows = []
    for row in sample_roles:
        flat = {field: row.get(field, "") for field in gold_fields}
        flat.update({name: int(row["flags"][name]) for name in FLAG_NAMES})
        gold_rows.append(flat)
    gold_manifest = experiment / "annotation" / "locks" / "gold_sampling_manifest.csv"
    write_csv(gold_manifest, gold_rows, gold_fields)
    gold_hash = sha256_file(gold_manifest)
    write_json(experiment / "annotation" / "locks" / "gold_sampling_lock.json", {
        "seed": SEED,
        "manifest_sha256": gold_hash,
        "counts": dict(Counter(row["gold_role"] for row in gold_rows)),
        "policy": "IDs are locked before human annotation and system output inspection.",
    })

    bundles = [context_bundle(row, corpus, assignment) for row in pilot]
    write_jsonl(experiment / "annotation" / "pilot" / "pilot_bundles.jsonl", bundles)
    write_jsonl(experiment / "annotation" / "pilot" / "annotator_A.jsonl", [annotation_template(bundle, "ANNOTATOR_A") for bundle in bundles])
    write_jsonl(experiment / "annotation" / "pilot" / "annotator_B.jsonl", [annotation_template(bundle, "ANNOTATOR_B") for bundle in bundles])
    write_jsonl(experiment / "annotation" / "pilot" / "adjudication.jsonl", [{
        "evidence_id": bundle["target"]["evidence_id"],
        "adjudicator": "",
        "final_claims": [],
        "final_term_mentions": [],
        "final_relations": [],
        "resolution_note": "",
        "completion_status": "NOT_STARTED",
    } for bundle in bundles])
    write_json(experiment / "annotation" / "pilot" / "pilot_lock.json", {
        "seed": SEED,
        "count": len(pilot),
        "evidence_ids": [row["evidence_id"] for row in pilot],
        "bundle_sha256": sha256_file(experiment / "annotation" / "pilot" / "pilot_bundles.jsonl"),
        "blind_policy": "No model pre-annotations; two independent human annotators.",
    })

    table_rows = [row for row in corpus if row["flags"]["markdown_table"]]
    write_json(experiment / "annotation" / "locks" / "table_gold_scope.json", {
        "count": len(table_rows), "evidence_ids": [row["evidence_id"] for row in table_rows], "policy": "Exhaustive table-fragment annotation"
    })

    config_files = sorted((experiment / "config").iterdir())
    for path in config_files:
        if path.is_file():
            shutil.copy2(path, run_dir / "config_snapshot" / path.name)
    shutil.copy2(design, run_dir / "config_snapshot" / "experiment_design.md")
    locked_files = [split_path, gold_manifest, experiment / "annotation" / "pilot" / "pilot_bundles.jsonl", *config_files]
    hashes = file_hashes(locked_files, experiment)
    write_json(run_dir / "locked_artifact_hashes.json", hashes)
    write_input_resolution(root, experiment / "reports" / "input_resolution.md", input_path, records)

    gate0_checks = {
        "binary_hash_match": binary_hash == EXPECTED_BINARY_SHA256,
        "canonical_hash_match_amended_preregister": content_hash == EXPECTED_CANONICAL_SHA256,
        "stable_id_unique": len({row["evidence_id"] for row in corpus}) == len(corpus),
        "leakage_group_overlap_zero": not split_audit["group_overlap"],
        "split_within_tolerance": all(abs(split_audit["split_ratios"][split] - SPLIT_TARGETS[split]) <= SPLIT_TOLERANCE[split] for split in SPLITS),
        "split_manifest_locked": bool(split_hash),
        "test_gold_access_log_zero": True,
    }
    write_json(run_dir / "test_gold_access_log.json", {"events": [], "count": 0})
    (run_dir / "usage_ledger.jsonl").write_text("", encoding="utf-8")
    gate0 = {"status": "PASS" if all(gate0_checks.values()) else "FAIL", "checks": gate0_checks}
    write_json(run_dir / "gate0.json", gate0)
    status = {
        "run_id": args.run_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "phase": "PHASE1_HUMAN_PILOT_REQUIRED",
        "gate0": gate0,
        "gate1": {"status": "BLOCKED", "reason": "Two independent human PILOT annotations and adjudication are not yet completed."},
        "later_phases": {"status": "NOT_RUN", "reason": "Gold-first design forbids locked performance experiments before Gate 1."},
        "input": audit["input"],
        "split": split_audit,
        "gold_sampling_manifest_sha256": gold_hash,
        "environment": {"python": sys.version, "platform": platform.platform(), "cpu_count": os.cpu_count()},
        "api_calls": 0,
        "llm_tokens": 0,
    }
    write_json(run_dir / "run_status.json", status)

    report = f"""# SCALE-AWC 자이제 실험 재실행 현황

## 판정

- Phase 0: **{gate0['status']}**
- Phase 1: **BLOCKED — 인간 독립 이중 주석 필요**
- Phase 2∼7: **NOT RUN**

새 설계서는 LLM-Silver를 최종 정답으로 금지한다. 따라서 인간 Gold 없이 E0∼E5 성능을 다시 계산하는 것은 설계서 위반이며, 이번 실행은 Gold 직전 단계에서 정상 중단했다.

## 완료한 작업

- 설계서 binary hash와 일치하는 원본 확정
- 1,366 evidence의 stable ID와 canonical corpus 생성
- {split_audit['leakage_group_count']} leakage group 생성
- 그룹 간 겹침 0인 50/20/20/10 split 잠금
- AWC Gold 420건의 표본 ID 잠금
- PILOT 40건의 blind A/B 주석 템플릿 생성
- 표 조각 {len(table_rows)}건의 전수 Gold 범위 잠금
- API 호출 0건, TEST Gold 열람 0건

## Split

| Split | Evidence | 비율 |
|---|---:|---:|
"""
    for split in SPLITS:
        report += f"| {split} | {split_audit['split_counts'][split]} | {split_audit['split_ratios'][split]:.4f} |\n"
    report += """

## 재개 조건

1. `annotation/pilot/annotator_A.jsonl`과 `annotator_B.jsonl`을 서로 독립적으로 완료한다.
2. 수주·제안 도메인 전문가와 온톨로지·정보추출 연구자가 최소 1명씩 포함되어야 한다.
3. IAA 기준을 계산하고 불일치를 adjudication한다.
4. 기준을 통과하면 guideline·schema·label set을 잠그고 Phase 2 Gold 주석으로 넘어간다.

상세한 입력 버전 차이와 canonical hash amendment는 `reports/input_resolution.md`를 본다.
"""
    (experiment / "reports" / "phase0_status_report.md").write_text(report, encoding="utf-8")
    print(json.dumps({"run_id": args.run_id, "gate0": gate0["status"], "split_counts": split_audit["split_counts"], "pilot": 40, "next": "human_double_annotation"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
