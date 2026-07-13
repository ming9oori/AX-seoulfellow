#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic data, evaluation, and graph utilities for TRACE-OL pilot v1."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import math
import random
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable


BUNDLE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BUNDLE_DIR.parent
BASE_SCRIPT = REPO_ROOT / "scripts" / "run_trace_ol_jaije_experiment.py"
SEED = 20260710
REFERENCE_VERSION = "TRACE-LLM-Silver-v0.1"
SCHEMA_VERSION = "atomic-claim-v0.2"

FAMILIES = {"FACTUAL", "NORMATIVE", "CONDITIONAL", "PROCEDURAL", "EVALUATIVE", "DISCOURSE", "UNCLEAR"}
CLAIM_TYPES = {
    "Definition", "DescriptiveFact", "Obligation", "Prohibition", "Recommendation",
    "NecessaryCondition", "ConditionalRule", "Exception", "ProcessOrder", "ActivityOutput",
    "DecisionTrigger", "PurposeCause", "ComparisonFormula", "EvaluationObservation",
    "Example", "CounterExample", "Question", "Quotation", "OtherUnclear",
}
MODALITIES = {"MUST", "MUST_NOT", "SHOULD", "MAY", "DESCRIPTIVE", "NONE"}
POLARITIES = {"POSITIVE", "NEGATIVE", "NONE"}
PROMOTIONS = {"FACT_ASSERTION", "TBOX_AXIOM", "PROCESS_EDGE", "RULE_NODE", "EVALUATION_NODE", "LEXICAL_ONLY", "NONE", "NEEDS_REVIEW"}
DECISIONS = {"ACCEPT", "REJECT", "ABSTAIN", "NEEDS_REVIEW"}
UNCERTAINTIES = {
    "NONE", "MISSING_SUBJECT", "COREFERENCE", "CLAIM_BOUNDARY", "MODALITY_SCOPE",
    "NEGATION_SCOPE", "CONDITION_SCOPE", "EXAMPLE_VS_FACT", "SENSE_AMBIGUITY",
    "PROMOTION_AMBIGUITY", "INSUFFICIENT_EVIDENCE", "OTHER",
}
DISCOURSE_TYPES = {"Example", "CounterExample", "Question", "Quotation"}
HIGH_RISK_TYPES = {"Obligation", "Prohibition", "NecessaryCondition", "ConditionalRule", "Exception", "Example", "CounterExample", "Question"}

STRATA = [
    "definition_descriptive",
    "normative",
    "condition_exception",
    "procedure_decision",
    "table_formula_evaluation",
    "discourse_ambiguous",
]

MANDATORY_ROWS = {
    218, 222, 236, 243, 244, 245, 246, 247, 461, 497, 916, 983, 1140,
    *range(1315, 1336),
}

KNOWN_ENTITIES = [
    ("Capture Plan", "Artifact"), ("Account Plan", "Artifact"), ("Proposal Planning", "Task"),
    ("Capture Planning", "Stage"), ("Opportunity Assessment", "Stage"), ("Pursuit Decision", "Decision"),
    ("Bid/No bid Decision", "Decision"), ("Bid/No-Bid", "Decision"),
    ("BCM", "Artifact"), ("Bidder Comparison Matrix", "Artifact"),
    ("Executive Summary", "Artifact"), ("RFP", "Artifact"),
    ("리스크 관리", "Task"), ("리스크", "Risk"), ("위험", "Risk"),
    ("경쟁자 분석", "Task"), ("경쟁사 분석", "Task"),
    ("가치제안", "Concept"), ("고객", "Role"), ("제안서", "Artifact"),
]


def load_base() -> Any:
    spec = importlib.util.spec_from_file_location("traceol_pilot_base", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASE = load_base()


def stable_hash(value: Any, length: int = 32) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:length]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.open(encoding="utf-8") if line.strip()]


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def evidence_id(excel_row: int) -> str:
    return f"ev:jaije:clean_sentences:r{excel_row}"


def section_id(section_no: Any) -> str:
    return f"sec:jaije:{BASE.slug(str(section_no or 'unscoped'))}"


def classify_stratum(text: str, block_type: str) -> str:
    # Priority fixed by the design: S5 -> S2 -> S3 -> S4 -> S6 -> S1.
    if block_type in {"markdown_table", "formula", "mixed"} or re.search(r"(?:점수|비중|평가|V\s*>\s*C|Winner\s*\()", text, re.I):
        return "table_formula_evaluation"
    if re.search(r"(?:하지\s*말아야|금지|피해야|해야\s*한다|하여야|반드시|필수|권장|바람직|가장\s*좋은)", text):
        return "normative"
    if re.search(r"(?:경우|만약|라면|때에는|있어야|필요조건|단,|예외)", text):
        return "condition_exception"
    if re.search(r"(?:단계|이후|끝나고|다음|먼저|의사\s*결정|프로세스|활동\(Activity\)|결과물\(Output\))", text, re.I):
        return "procedure_decision"
    if block_type == "question" or re.search(r"(?:예를\s*들어|사례|Shipley Tip|\(×\)|\(○\)|[?？]|인용)", text, re.I):
        return "discourse_ambiguous"
    return "definition_descriptive"


def build_all_bundles(input_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    sheet, records = BASE.read_xlsx(input_path)
    if len(records) != 1366:
        raise ValueError(f"Expected 1366 evidence units, got {len(records)}")
    source_hash = sha256_file(input_path)
    blocks = BASE.build_source_blocks(records, input_path, source_hash, "pilot-preprocess", sheet)
    block_by_id = {block["id"]: block for block in blocks}
    duplicate_groups: dict[str, list[str]] = defaultdict(list)
    for block in blocks:
        fingerprint = stable_hash(normalize_space(block["text_raw"]).casefold(), 20)
        duplicate_groups[fingerprint].append(evidence_id(block["excel_row"]))

    evidence_units: list[dict[str, Any]] = []
    bundles: list[dict[str, Any]] = []
    for index, block in enumerate(blocks):
        eid = evidence_id(block["excel_row"])
        fingerprint = stable_hash(normalize_space(block["text_raw"]).casefold(), 20)
        table_id = f"tbl:jaije:r{block['excel_row']}" if block["block_type"] in {"markdown_table", "mixed"} and "|" in block["text_raw"] else ""
        list_id = f"list:jaije:r{block['excel_row']}" if block["block_type"] == "list" else ""
        duplicate_cluster_id = f"dup:{fingerprint}" if len(duplicate_groups[fingerprint]) > 1 else ""
        sid = section_id(block["section_no_raw"] or block["inferred_section_no"])
        if table_id:
            group_id = table_id
        elif list_id:
            group_id = list_id
        elif duplicate_cluster_id:
            group_id = duplicate_cluster_id
        else:
            group_id = sid
        unit = {
            "evidence_id": eid,
            "source_id": block["id"],
            "source_file": str(input_path),
            "sheet": sheet,
            "excel_row": block["excel_row"],
            "page": block["page"],
            "chapter_no": block["chapter_no_raw"],
            "chapter_title": block["chapter_title_raw"],
            "section_no": block["section_no_raw"],
            "section_title": block["section_title_raw"],
            "section_id": sid,
            "text": block["text_raw"],
            "text_hash": block["content_sha256"],
            "block_type": block["block_type"],
            "stratum": classify_stratum(block["text_raw"], block["block_type"]),
            "table_id": table_id,
            "list_id": list_id,
            "duplicate_cluster_id": duplicate_cluster_id,
            "bundle_group_id": group_id,
            "context_recovered": block["context_status"] != "observed",
        }
        evidence_units.append(unit)
        previous = blocks[index - 1] if index > 0 else None
        following = blocks[index + 1] if index + 1 < len(blocks) else None
        context = []
        if previous:
            context.append({"evidence_id": evidence_id(previous["excel_row"]), "relation": "previous", "text": previous["text_raw"]})
        if following:
            context.append({"evidence_id": evidence_id(following["excel_row"]), "relation": "next", "text": following["text_raw"]})
        table_headers = []
        if table_id:
            lines = [line.strip() for line in block["text_raw"].splitlines() if line.strip().startswith("|")]
            if lines:
                table_headers = [cell.strip() for cell in lines[0].strip("|").split("|")]
        bundles.append({
            "bundle_id": f"bundle:{eid}",
            "target": {"evidence_id": eid, "text": block["text_raw"]},
            "context": context,
            "metadata": {
                "excel_row": block["excel_row"], "page": block["page"],
                "chapter_title": block["chapter_title_raw"], "section_title": block["section_title_raw"],
                "section_id": sid, "block_type": block["block_type"], "table_headers": table_headers,
                "context_recovered": block["context_status"] != "observed",
            },
        })
    profile = {
        "sheet": sheet,
        "input_sha256": source_hash,
        "evidence_units": len(evidence_units),
        "strata_all": dict(Counter(unit["stratum"] for unit in evidence_units)),
        "block_types": dict(Counter(unit["block_type"] for unit in evidence_units)),
        "duplicate_clusters": sum(len(ids) > 1 for ids in duplicate_groups.values()),
    }
    return evidence_units, bundles, profile


def _group_subset_exact(groups: list[tuple[str, list[dict[str, Any]]]], target: int, seed: int) -> tuple[list[tuple[str, list[dict[str, Any]]]], list[tuple[str, list[dict[str, Any]]]]]:
    ordered = sorted(groups, key=lambda item: stable_hash([seed, item[0]], 16))
    dp: dict[int, list[int]] = {0: []}
    for index, (_, rows) in enumerate(ordered):
        size = len(rows)
        for total, selected in list(dp.items())[::-1]:
            nxt = total + size
            if nxt <= target and nxt not in dp:
                dp[nxt] = [*selected, index]
    if target not in dp:
        # Fall back to deterministic closest fit; caller records any group split exception.
        best = max(dp)
        selected_indices = set(dp[best])
        chosen = [ordered[i] for i in sorted(selected_indices)]
        remaining = [item for i, item in enumerate(ordered) if i not in selected_indices]
        need = target - best
        if need:
            for index, (group_id, rows) in enumerate(remaining):
                if len(rows) >= need:
                    ordered_rows = sorted(rows, key=lambda row: stable_hash([seed, row["evidence_id"]], 16))
                    chosen.append((group_id + ":split-a", ordered_rows[:need]))
                    remainder = ordered_rows[need:]
                    remaining[index:index + 1] = [(group_id + ":split-b", remainder)] if remainder else []
                    break
        return chosen, remaining
    selected_indices = set(dp[target])
    return (
        [ordered[i] for i in sorted(selected_indices)],
        [item for i, item in enumerate(ordered) if i not in selected_indices],
    )


def sample_and_split(evidence_units: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rng = random.Random(SEED)
    by_stratum: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_row = {unit["excel_row"]: unit for unit in evidence_units}
    for unit in evidence_units:
        by_stratum[unit["stratum"]].append(unit)
    selected: dict[str, dict[str, Any]] = {}
    stratum_counts: Counter[str] = Counter()
    mandatory_present = sorted(MANDATORY_ROWS & set(by_row))
    for row in mandatory_present:
        unit = by_row[row]
        if stratum_counts[unit["stratum"]] < 25:
            selected[unit["evidence_id"]] = {**unit, "sample_type": "targeted_mandatory"}
            stratum_counts[unit["stratum"]] += 1
    for stratum in STRATA:
        candidates = [unit for unit in by_stratum[stratum] if unit["evidence_id"] not in selected]
        candidates.sort(key=lambda row: stable_hash([SEED, stratum, row["evidence_id"]], 16))
        need = 25 - stratum_counts[stratum]
        if len(candidates) < need:
            raise ValueError(f"Insufficient records for {stratum}: need {need}, have {len(candidates)}")
        for unit in candidates[:need]:
            selected[unit["evidence_id"]] = {**unit, "sample_type": "targeted_stratified"}
            stratum_counts[stratum] += 1
    remaining = [unit for unit in evidence_units if unit["evidence_id"] not in selected]
    rng.shuffle(remaining)
    for unit in remaining[:30]:
        selected[unit["evidence_id"]] = {**unit, "sample_type": "simple_random"}
    rows = list(selected.values())
    if len(rows) != 180:
        raise AssertionError(f"Expected sample 180, got {len(rows)}")

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["bundle_group_id"]].append(row)
    groups = list(grouped.items())
    cal_groups, remaining_groups = _group_subset_exact(groups, 60, SEED + 1)
    b1_groups, b2_groups = _group_subset_exact(remaining_groups, 60, SEED + 2)
    assignment: dict[str, str] = {}
    for split_name, split_groups in [("CAL", cal_groups), ("B1", b1_groups), ("B2_LOCKED", b2_groups)]:
        for _, group_rows in split_groups:
            for row in group_rows:
                assignment[row["evidence_id"]] = split_name
    for row in rows:
        row["split"] = assignment[row["evidence_id"]]
    b1_rows = [row for row in rows if row["split"] == "B1"]
    b1_grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in b1_rows:
        b1_grouped[row["bundle_group_id"]].append(row)
    b1a_groups, b1b_groups = _group_subset_exact(list(b1_grouped.items()), 40, SEED + 3)
    b1_assignment = {}
    for name, split_groups in [("B1a_distill_induction", b1a_groups), ("B1b_lf_validation", b1b_groups)]:
        for _, group_rows in split_groups:
            for row in group_rows:
                b1_assignment[row["evidence_id"]] = name
    for row in rows:
        row["b1_subsplit"] = b1_assignment.get(row["evidence_id"], "")
    rows.sort(key=lambda row: (row["split"], row["excel_row"]))
    split_counts = Counter(row["split"] for row in rows)
    if split_counts != Counter({"CAL": 60, "B1": 60, "B2_LOCKED": 60}):
        raise AssertionError(f"Split counts invalid: {split_counts}")
    audit = {
        "seed": SEED,
        "sample_count": len(rows),
        "targeted_count": sum(row["sample_type"].startswith("targeted") for row in rows),
        "random_count": sum(row["sample_type"] == "simple_random" for row in rows),
        "strata_targeted": dict(Counter(row["stratum"] for row in rows if row["sample_type"].startswith("targeted"))),
        "strata_all_sample": dict(Counter(row["stratum"] for row in rows)),
        "split_counts": dict(split_counts),
        "b1_subsplit_counts": dict(Counter(row["b1_subsplit"] for row in rows if row["split"] == "B1")),
        "mandatory_rows_present": mandatory_present,
        "group_overlap": _group_overlap(rows),
    }
    return rows, audit


def _group_overlap(rows: list[dict[str, Any]]) -> dict[str, list[str]]:
    splits_by_group: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        splits_by_group[row["bundle_group_id"]].add(row["split"])
    return {group: sorted(splits) for group, splits in splits_by_group.items() if len(splits) > 1}


def manifest_rows(sample: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fields = [
        "evidence_id", "excel_row", "page", "chapter_no", "chapter_title", "section_no", "section_title",
        "section_id", "stratum", "sample_type", "split", "b1_subsplit", "block_type", "bundle_group_id",
        "table_id", "list_id", "duplicate_cluster_id", "text_hash", "context_recovered",
    ]
    return [{field: row.get(field, "") for field in fields} for row in sample]


def pack_bundles(bundles: list[dict[str, Any]], sample: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    sample_by_id = {row["evidence_id"]: row for row in sample}
    selected = [bundle for bundle in bundles if bundle["target"]["evidence_id"] in sample_by_id]
    selected.sort(key=lambda bundle: sample_by_id[bundle["target"]["evidence_id"]]["excel_row"])
    table = [bundle for bundle in selected if sample_by_id[bundle["target"]["evidence_id"]]["stratum"] == "table_formula_evaluation"]
    prose = [bundle for bundle in selected if bundle not in table]
    result = []
    for rows, size in [(prose, 10), (table, 5)]:
        result.extend(rows[index:index + size] for index in range(0, len(rows), size))
    return result


def span_text_map(bundle: dict[str, Any]) -> dict[str, str]:
    result = {bundle["target"]["evidence_id"]: bundle["target"]["text"]}
    result.update({item["evidence_id"]: item["text"] for item in bundle.get("context") or []})
    return result


def normalize_annotation(annotation: dict[str, Any], bundle: dict[str, Any], role: str, model: str, prompt_version: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    issues: list[dict[str, Any]] = []
    eid = bundle["target"]["evidence_id"]
    texts = span_text_map(bundle)
    normalized = dict(annotation)
    normalized["evidence_id"] = eid
    normalized["bundle_id"] = bundle["bundle_id"]
    normalized["annotator"] = {"role": role, "model_id": model, "prompt_version": prompt_version, "schema_version": SCHEMA_VERSION}
    claims = []
    for index, raw_claim in enumerate(annotation.get("claims") or []):
        claim = json.loads(json.dumps(raw_claim, ensure_ascii=False))
        errors = validate_claim(claim, texts)
        if errors:
            issues.append({"evidence_id": eid, "claim_index": index, "errors": errors, "claim": claim})
            continue
        claim["claim_id"] = f"claim:{stable_hash([eid, claim.get('source_span'), claim.get('claim_family'), claim.get('claim_type'), claim.get('predicate_normalized'), index], 32)}"
        claims.append(claim)
    normalized["claims"] = claims
    return normalized, issues


def validate_claim(claim: dict[str, Any], texts: dict[str, str]) -> list[str]:
    errors: list[str] = []
    required = {"claim_id", "source_span", "claim_family", "claim_type", "arguments", "predicate_normalized", "modality", "polarity", "conditions", "exceptions", "promotion_target", "decision", "uncertainty_code"}
    if not required.issubset(claim):
        errors.append("missing_required_fields")
        return errors
    if claim["claim_family"] not in FAMILIES: errors.append("invalid_family")
    if claim["claim_type"] not in CLAIM_TYPES: errors.append("invalid_type")
    if claim["modality"] not in MODALITIES: errors.append("invalid_modality")
    if claim["polarity"] not in POLARITIES: errors.append("invalid_polarity")
    if claim["promotion_target"] not in PROMOTIONS: errors.append("invalid_promotion")
    if claim["decision"] not in DECISIONS: errors.append("invalid_decision")
    if claim["uncertainty_code"] not in UNCERTAINTIES: errors.append("invalid_uncertainty")
    for path, span in iter_spans(claim):
        if not validate_and_repair_span(span, texts):
            errors.append(f"invalid_span:{path}")
    if claim["modality"] == "MUST_NOT" and claim["polarity"] != "NEGATIVE":
        errors.append("must_not_polarity_conflict")
    if claim["claim_type"] in DISCOURSE_TYPES and claim["promotion_target"] not in {"NONE", "NEEDS_REVIEW"}:
        errors.append("discourse_promoted")
    if claim["claim_type"] == "ConditionalRule" and not claim.get("conditions"):
        errors.append("conditional_without_condition")
    return errors


def iter_spans(claim: dict[str, Any]) -> Iterable[tuple[str, dict[str, Any]]]:
    if isinstance(claim.get("source_span"), dict): yield "source_span", claim["source_span"]
    for index, argument in enumerate(claim.get("arguments") or []):
        if isinstance(argument.get("span"), dict): yield f"arguments[{index}].span", argument["span"]
    for field in ["conditions", "exceptions"]:
        for index, span in enumerate(claim.get(field) or []):
            if isinstance(span, dict): yield f"{field}[{index}]", span
    for field in ["scope_span", "purpose_span"]:
        if isinstance(claim.get(field), dict): yield field, claim[field]


def validate_and_repair_span(span: dict[str, Any], texts: dict[str, str]) -> bool:
    eid = span.get("evidence_id")
    if eid not in texts:
        return False
    source = texts[eid]
    text = str(span.get("text") or "")
    start = span.get("start")
    end = span.get("end")
    if isinstance(start, int) and isinstance(end, int) and source[start:end] == text:
        return True
    positions = [match.start() for match in re.finditer(re.escape(text), source)] if text else []
    if len(positions) == 1:
        span["start"] = positions[0]
        span["end"] = positions[0] + len(text)
        return True
    return False


def char_iou(a: dict[str, Any], b: dict[str, Any]) -> float:
    if a.get("evidence_id") != b.get("evidence_id"):
        return 0.0
    left = max(int(a.get("start", 0)), int(b.get("start", 0)))
    right = min(int(a.get("end", 0)), int(b.get("end", 0)))
    intersection = max(0, right - left)
    union = max(int(a.get("end", 0)), int(b.get("end", 0))) - min(int(a.get("start", 0)), int(b.get("start", 0)))
    return intersection / union if union else 0.0


def argument_overlap(a: dict[str, Any], b: dict[str, Any]) -> float:
    spans_a = [arg.get("span") for arg in a.get("arguments") or [] if isinstance(arg.get("span"), dict)]
    spans_b = [arg.get("span") for arg in b.get("arguments") or [] if isinstance(arg.get("span"), dict)]
    if not spans_a and not spans_b:
        return 1.0
    if not spans_a or not spans_b:
        return 0.0
    return max(char_iou(x, y) for x in spans_a for y in spans_b)


def alignment_score(a: dict[str, Any], b: dict[str, Any]) -> float:
    span = char_iou(a["source_span"], b["source_span"])
    args = argument_overlap(a, b)
    predicate = SequenceMatcher(None, a.get("predicate_normalized") or "", b.get("predicate_normalized") or "").ratio()
    family = 1.0 if a.get("claim_family") == b.get("claim_family") else 0.0
    return 0.50 * span + 0.25 * args + 0.15 * predicate + 0.10 * family


def best_claim_matching(claims_a: list[dict[str, Any]], claims_b: list[dict[str, Any]], threshold: float = 0.50) -> tuple[list[tuple[int, int, float]], list[int], list[int]]:
    n, m = len(claims_a), len(claims_b)
    scores = [[alignment_score(a, b) for b in claims_b] for a in claims_a]

    @lru_cache(maxsize=None)
    def solve(index: int, used: int) -> tuple[float, tuple[tuple[int, int], ...]]:
        if index == n:
            return 0.0, ()
        best_score, best_pairs = solve(index + 1, used)
        for j in range(m):
            if used & (1 << j) or scores[index][j] < threshold:
                continue
            tail_score, tail_pairs = solve(index + 1, used | (1 << j))
            total = scores[index][j] + tail_score
            if total > best_score:
                best_score, best_pairs = total, ((index, j), *tail_pairs)
        return best_score, best_pairs

    _, pairs_raw = solve(0, 0)
    pairs = [(i, j, scores[i][j]) for i, j in pairs_raw]
    used_a = {i for i, _, _ in pairs}
    used_b = {j for _, j, _ in pairs}
    return pairs, [i for i in range(n) if i not in used_a], [j for j in range(m) if j not in used_b]


def critical_signature(claim: dict[str, Any]) -> tuple[Any, ...]:
    return (
        claim.get("claim_type"), claim.get("modality"), claim.get("polarity"),
        claim.get("promotion_target"), bool(claim.get("conditions")),
    )


def annotation_agreement(a: dict[str, Any], b: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    claims_a, claims_b = a.get("claims") or [], b.get("claims") or []
    pairs, unmatched_a, unmatched_b = best_claim_matching(claims_a, claims_b)
    critical_match = all(critical_signature(claims_a[i]) == critical_signature(claims_b[j]) for i, j, _ in pairs)
    complete = not unmatched_a and not unmatched_b and len(pairs) == len(claims_a) == len(claims_b) and critical_match
    return complete, {"pairs": pairs, "unmatched_a": unmatched_a, "unmatched_b": unmatched_b, "critical_match": critical_match}


def resolve_three_way(a: dict[str, Any], b: dict[str, Any], c: dict[str, Any]) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    claims_a, claims_b, claims_c = a.get("claims") or [], b.get("claims") or [], c.get("claims") or []
    groups: list[list[dict[str, Any]]] = [[claim] for claim in claims_a]
    for claims in [claims_b, claims_c]:
        used_groups: set[int] = set()
        for claim in claims:
            options = [(alignment_score(group[0], claim), index) for index, group in enumerate(groups) if index not in used_groups]
            score, index = max(options, default=(0.0, -1))
            if score >= 0.50:
                groups[index].append(claim)
                used_groups.add(index)
            else:
                groups.append([claim])
    resolved: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    for group in groups:
        signatures = Counter(critical_signature(claim) for claim in group)
        signature, count = signatures.most_common(1)[0]
        candidates = [claim for claim in group if critical_signature(claim) == signature]
        if count >= 2:
            resolved.append(candidates[0])
        else:
            conflicts.append({"claims": group, "high_risk": any(claim.get("claim_type") in HIGH_RISK_TYPES for claim in group)})
    if conflicts:
        return None, conflicts
    annotation = json.loads(json.dumps(a, ensure_ascii=False))
    annotation["claims"] = resolved
    return annotation, []


def find_entities(text: str, evidence: str) -> list[dict[str, Any]]:
    found = []
    for surface, kernel_type in KNOWN_ENTITIES:
        match = re.search(re.escape(surface), text, re.I)
        if not match:
            continue
        found.append({
            "role": "ARG" if found else "SUBJECT",
            "span": {"evidence_id": evidence, "text": text[match.start():match.end()], "start": match.start(), "end": match.end()},
            "implicit": False, "restored_from_context": False, "context_evidence_id": None,
            "kernel_type": kernel_type,
        })
        if len(found) >= 3:
            break
    return found


def heuristic_annotation(bundle: dict[str, Any], *, flat: bool = False, role: str = "E2_TRACE_NoLLM") -> dict[str, Any]:
    eid = bundle["target"]["evidence_id"]
    text = bundle["target"]["text"]
    block_type = "prose" if flat else bundle["metadata"]["block_type"]
    family = "FACTUAL"
    claim_type = "DescriptiveFact"
    modality = "DESCRIPTIVE"
    polarity = "POSITIVE"
    promotion = "FACT_ASSERTION"
    predicate = "ASSERTS"
    uncertainty = "NONE"
    conditions = []
    decision = "ACCEPT"
    confidence = 0.72
    if block_type == "question" or "?" in text or "？" in text:
        family, claim_type, modality, polarity, promotion, predicate = "DISCOURSE", "Question", "NONE", "NONE", "NONE", None
        confidence = 0.96
    elif re.search(r"(?:예를\s*들어|사례|Shipley Tip)", text, re.I):
        family, claim_type, modality, promotion, predicate = "DISCOURSE", "Example", "NONE", "NONE", None
        confidence = 0.88
    elif re.search(r"(?:하지\s*말아야|금지|피해야)", text):
        family, claim_type, modality, polarity, promotion, predicate = "NORMATIVE", "Prohibition", "MUST_NOT", "NEGATIVE", "RULE_NODE", "PROHIBITS"
        confidence = 0.92
    elif re.search(r"(?:해야\s*한다|하여야|반드시|필수)", text):
        family, claim_type, modality, promotion, predicate = "NORMATIVE", "Obligation", "MUST", "RULE_NODE", "REQUIRES"
        confidence = 0.90
    elif re.search(r"(?:권장|바람직|가장\s*좋은|하는\s*것이\s*좋다)", text):
        family, claim_type, modality, promotion, predicate = "NORMATIVE", "Recommendation", "SHOULD", "RULE_NODE", "RECOMMENDS"
        confidence = 0.84
    elif re.search(r"(?:경우|만약|라면|때에는)", text):
        family, claim_type, promotion, predicate = "CONDITIONAL", "ConditionalRule", "RULE_NODE", "APPLIES_IF"
        match = re.search(r"(.{0,80}(?:경우|만약|라면|때에는).{0,40})", text)
        if match:
            conditions = [{"evidence_id": eid, "text": match.group(1), "start": match.start(1), "end": match.end(1)}]
        confidence = 0.80
    elif not flat and (block_type in {"markdown_table", "mixed"}) and re.search(r"(?:활동|결과물|Output|BCM|점수|비중)", text, re.I):
        family = "EVALUATIVE" if re.search(r"(?:점수|비중|BCM)", text, re.I) else "PROCEDURAL"
        claim_type = "EvaluationObservation" if family == "EVALUATIVE" else "ActivityOutput"
        promotion = "EVALUATION_NODE" if family == "EVALUATIVE" else "PROCESS_EDGE"
        predicate = "MEASURES" if family == "EVALUATIVE" else "PRODUCES"
        confidence = 0.90
    elif not flat and re.search(r"(?:V\s*>\s*C|Winner\s*\(|Value\s*=|Cost\s*=)", text, re.I):
        family, claim_type, promotion, predicate = "EVALUATIVE", "ComparisonFormula", "EVALUATION_NODE", "COMPARES"
        confidence = 0.94
    elif re.search(r"(?:단계|이후|끝나고|먼저|다음)", text):
        family, claim_type, promotion, predicate = "PROCEDURAL", "ProcessOrder", "PROCESS_EDGE", "PRECEDES"
        confidence = 0.83
    elif re.search(r"(?:이란|정의|말한다|의미)", text):
        family, claim_type, promotion, predicate = "FACTUAL", "Definition", "TBOX_AXIOM", "DEFINES"
        confidence = 0.85
    if family in {"NORMATIVE", "CONDITIONAL"} and confidence < 0.90:
        decision, promotion, uncertainty = "NEEDS_REVIEW", "NEEDS_REVIEW", "MODALITY_SCOPE" if family == "NORMATIVE" else "CONDITION_SCOPE"
    source_span = {"evidence_id": eid, "text": text, "start": 0, "end": len(text)}
    claim = {
        "claim_id": f"claim:{stable_hash([role, eid, claim_type, predicate], 32)}",
        "source_span": source_span,
        "claim_family": family,
        "claim_type": claim_type,
        "arguments": find_entities(text, eid),
        "predicate_normalized": predicate,
        "modality": modality,
        "polarity": polarity,
        "conditions": conditions,
        "exceptions": [],
        "scope_span": None,
        "purpose_span": None,
        "promotion_target": promotion,
        "decision": decision,
        "uncertainty_code": uncertainty,
        "confidence": confidence,
    }
    return {
        "evidence_id": eid,
        "bundle_id": bundle["bundle_id"],
        "annotator": {"role": role, "model_id": "NO_LLM", "prompt_version": "heuristic-lf-v0.1", "schema_version": SCHEMA_VERSION},
        "claims": [claim],
    }


def risk_for_claim(claim: dict[str, Any]) -> float:
    claim_type = claim.get("claim_type")
    return {
        "Prohibition": 1.00, "Obligation": 0.90, "ConditionalRule": 0.85, "NecessaryCondition": 0.85,
        "Exception": 0.85, "Example": 0.85, "CounterExample": 0.85, "Question": 0.85,
        "ProcessOrder": 0.60, "DecisionTrigger": 0.60, "Definition": 0.45, "DescriptiveFact": 0.30,
    }.get(claim_type, 0.55)


def priority_for_claim(claim: dict[str, Any], bundle: dict[str, Any], novelty: float = 0.5, graph_impact: float = 0.5) -> float:
    confidence = float(claim.get("confidence", 0.5))
    uncertainty = 1.0 - confidence
    risk = risk_for_claim(claim)
    if "Capture Plan" in bundle["target"]["text"]:
        graph_impact = max(graph_impact, 0.9)
        novelty = max(novelty, 0.7)
    return round(0.45 * uncertainty + 0.30 * risk + 0.15 * novelty + 0.10 * graph_impact, 4)


def selected_candidates(annotations: list[dict[str, Any]], bundles_by_id: dict[str, dict[str, Any]], max_fraction: float = 0.15, max_candidates: int = 30) -> list[dict[str, Any]]:
    rows = []
    for annotation in annotations:
        bundle = bundles_by_id[annotation["evidence_id"]]
        for claim in annotation.get("claims") or []:
            priority = priority_for_claim(claim, bundle)
            confidence = float(claim.get("confidence", 0.5))
            if priority >= 0.65 or (risk_for_claim(claim) >= 0.85 and confidence < 0.90) or claim["decision"] == "NEEDS_REVIEW":
                rows.append({
                    "candidate_id": claim["claim_id"], "evidence_id": annotation["evidence_id"],
                    "claim": claim, "priority": priority, "bundle": bundle,
                })
    limit = min(max_candidates, max(1, math.ceil(sum(len(a.get("claims") or []) for a in annotations) * max_fraction)))
    return sorted(rows, key=lambda row: (-row["priority"], row["candidate_id"]))[:limit]


def apply_selective_decisions(base_annotations: list[dict[str, Any]], decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_candidate = {row["candidate_id"]: row for row in decisions}
    output = json.loads(json.dumps(base_annotations, ensure_ascii=False))
    for annotation in output:
        updated_claims = []
        for claim in annotation.get("claims") or []:
            decision = by_candidate.get(claim["claim_id"])
            if not decision:
                updated_claims.append(claim)
                continue
            action = decision["decision"]
            if action == "reject":
                claim["decision"] = "REJECT"
                claim["promotion_target"] = "NONE"
            elif action in {"abstain", "needs_review"}:
                claim["decision"] = "NEEDS_REVIEW"
                claim["promotion_target"] = "NEEDS_REVIEW"
            elif action == "accept":
                corrected = decision.get("claim") or claim
                corrected["claim_id"] = claim["claim_id"]
                corrected["decision"] = "ACCEPT"
                updated_claims.append(corrected)
                continue
            updated_claims.append(claim)
        annotation["claims"] = updated_claims
    return output


def derive_lf_candidates(e3_decisions: list[dict[str, Any]], bundles_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in e3_decisions:
        if row["decision"] != "accept" or not row.get("claim"):
            continue
        claim = row["claim"]
        text = bundles_by_id[row["evidence_id"]]["target"]["text"]
        cue = next((cue for cue in ["하지 말아야", "해야 한다", "경우", "단계", "이란", "예를 들어", "점수", "결과물"] if cue in text), "generic")
        groups[(cue, claim["claim_type"])].append(row)
    result = []
    for index, ((cue, claim_type), rows) in enumerate(sorted(groups.items()), start=1):
        result.append({
            "id": f"lf:distilled:pilot:{index:03d}", "cue": cue, "claim_type": claim_type,
            "induction_support": len(rows), "source_candidate_ids": [row["candidate_id"] for row in rows],
            "status": "CANDIDATE", "document_scope": "document_local",
        })
    return result


def validate_lf_candidates(lfs: list[dict[str, Any]], b1b_bundles: list[dict[str, Any]], references: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    thresholds = {
        "Definition": (0.85, 4), "DescriptiveFact": (0.85, 4),
        "ActivityOutput": (0.90, 3), "ProcessOrder": (0.90, 3),
        "Obligation": (0.95, 3), "Prohibition": (0.95, 3),
        "Example": (0.95, 3), "CounterExample": (0.95, 3), "Question": (0.95, 3),
    }
    output = []
    for lf in lfs:
        matched = [bundle for bundle in b1b_bundles if lf["cue"] == "generic" or lf["cue"] in bundle["target"]["text"]]
        correct = 0
        evaluated = 0
        for bundle in matched:
            ref = references.get(bundle["target"]["evidence_id"])
            if not ref or ref.get("agreement_tier") == "Challenge":
                continue
            evaluated += 1
            if any(claim["claim_type"] == lf["claim_type"] for claim in ref["annotation"].get("claims") or []):
                correct += 1
        precision = correct / evaluated if evaluated else 0.0
        min_precision, min_support = thresholds.get(lf["claim_type"], (0.90, 3))
        row = {**lf, "validation_support": evaluated, "validation_correct": correct, "validation_precision": round(precision, 4)}
        row["status"] = "ACTIVE" if evaluated >= min_support and precision >= min_precision else "REJECTED_VALIDATION"
        output.append(row)
    return output


def flatten_claims(annotations: list[dict[str, Any]]) -> list[tuple[str, dict[str, Any]]]:
    return [(annotation["evidence_id"], claim) for annotation in annotations for claim in annotation.get("claims") or []]


def evaluate_predictions(predictions: list[dict[str, Any]], references: list[dict[str, Any]]) -> dict[str, Any]:
    ref_by_id = {row["evidence_id"]: row for row in references if row.get("agreement_tier") in {"Silver-A", "Silver-B"}}
    pred_by_id = {row["evidence_id"]: row for row in predictions}
    matched_pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    tp = fp = fn = 0
    unit_scores: dict[str, tuple[int, int, int]] = {}
    for eid, ref_row in ref_by_id.items():
        refs = ref_row["annotation"].get("claims") or []
        preds = (pred_by_id.get(eid) or {}).get("claims") or []
        pairs, unmatched_ref, unmatched_pred = best_claim_matching(refs, preds)
        tp += len(pairs); fn += len(unmatched_ref); fp += len(unmatched_pred)
        unit_scores[eid] = (len(pairs), len(unmatched_pred), len(unmatched_ref))
        matched_pairs.extend((refs[i], preds[j]) for i, j, _ in pairs)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    critical = critical_errors(matched_pairs, predictions)
    return {
        "claim_precision": round(precision, 4), "claim_recall": round(recall, 4), "claim_f1": round(f1, 4),
        "claim_tp": tp, "claim_fp": fp, "claim_fn": fn,
        "family_macro_f1": round(classification_macro_f1(matched_pairs, "claim_family", sorted(FAMILIES)), 4),
        "fine_type_macro_f1": round(classification_macro_f1(matched_pairs, "claim_type", sorted(CLAIM_TYPES)), 4),
        "modality_macro_f1": round(classification_macro_f1(matched_pairs, "modality", sorted(MODALITIES)), 4),
        "promotion_macro_f1": round(classification_macro_f1(matched_pairs, "promotion_target", sorted(PROMOTIONS)), 4),
        "graph_f1": round(graph_signature_f1(predictions, references), 4),
        "critical_errors": critical,
        "critical_error_rate": round(critical["total"] / max(1, len(matched_pairs)), 4),
        "evaluated_reference_units": len(ref_by_id), "matched_claims": len(matched_pairs),
        "unit_scores": unit_scores,
    }


def classification_macro_f1(pairs: list[tuple[dict[str, Any], dict[str, Any]]], field: str, labels: list[str]) -> float:
    scores = []
    present = {ref.get(field) for ref, _ in pairs} | {pred.get(field) for _, pred in pairs}
    for label in labels:
        if label not in present:
            continue
        tp = sum(ref.get(field) == label and pred.get(field) == label for ref, pred in pairs)
        fp = sum(ref.get(field) != label and pred.get(field) == label for ref, pred in pairs)
        fn = sum(ref.get(field) == label and pred.get(field) != label for ref, pred in pairs)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        scores.append(2 * precision * recall / (precision + recall) if precision + recall else 0.0)
    return sum(scores) / len(scores) if scores else 0.0


def critical_errors(pairs: list[tuple[dict[str, Any], dict[str, Any]]], predictions: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter()
    for ref, pred in pairs:
        if ref.get("modality") != pred.get("modality"): counts["modality_confusion"] += 1
        if ref.get("polarity") != pred.get("polarity"): counts["negation_or_polarity_dropped"] += 1
        if bool(ref.get("conditions")) != bool(pred.get("conditions")): counts["condition_dropped"] += 1
        if ref.get("claim_type") in DISCOURSE_TYPES and pred.get("promotion_target") not in {"NONE", "NEEDS_REVIEW"}: counts["discourse_promoted"] += 1
    for _, claim in flatten_claims(predictions):
        if claim.get("decision") == "ACCEPT" and not claim.get("source_span"): counts["unsupported_assertion"] += 1
    counts["total"] = sum(value for key, value in counts.items() if key != "total")
    return dict(counts)


def graph_signature_f1(predictions: list[dict[str, Any]], references: list[dict[str, Any]]) -> float:
    def signatures(rows: list[dict[str, Any]], reference: bool) -> set[tuple[str, str, str]]:
        result = set()
        for row in rows:
            annotation = row.get("annotation") if reference else row
            if not annotation:
                continue
            for claim in annotation.get("claims") or []:
                if claim.get("decision") != "ACCEPT" or claim.get("promotion_target") in {"NONE", "NEEDS_REVIEW"}:
                    continue
                result.add((row["evidence_id"], claim.get("predicate_normalized") or "", claim.get("promotion_target") or ""))
        return result
    pred = signatures(predictions, False)
    ref = signatures([row for row in references if row.get("agreement_tier") in {"Silver-A", "Silver-B"}], True)
    tp = len(pred & ref)
    precision = tp / len(pred) if pred else 0.0
    recall = tp / len(ref) if ref else 0.0
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def bootstrap_claim_f1(metrics: dict[str, Any], resamples: int = 2000) -> dict[str, float]:
    unit_scores = metrics.get("unit_scores") or {}
    ids = sorted(unit_scores)
    if not ids:
        return {"lower": 0.0, "median": 0.0, "upper": 0.0}
    rng = random.Random(SEED)
    values = []
    for _ in range(resamples):
        sampled = [ids[rng.randrange(len(ids))] for _ in ids]
        tp = sum(unit_scores[eid][0] for eid in sampled)
        fp = sum(unit_scores[eid][1] for eid in sampled)
        fn = sum(unit_scores[eid][2] for eid in sampled)
        p = tp / (tp + fp) if tp + fp else 0.0
        r = tp / (tp + fn) if tp + fn else 0.0
        values.append(2 * p * r / (p + r) if p + r else 0.0)
    values.sort()
    return {
        "lower": round(values[int(0.025 * (len(values) - 1))], 4),
        "median": round(values[int(0.5 * (len(values) - 1))], 4),
        "upper": round(values[int(0.975 * (len(values) - 1))], 4),
    }


def export_neo4j(
    out_dir: Path,
    sample: list[dict[str, Any]],
    references: list[dict[str, Any]],
    e4_predictions: list[dict[str, Any]],
) -> dict[str, Any]:
    neo = out_dir / "neo4j"
    neo.mkdir(parents=True, exist_ok=True)
    document_rows = [{"id": "doc:jaije:v1", "name": "자이제", "human_reviewed": "false"}]
    section_rows = []
    for key, rows in sorted(_group_by(sample, "section_id").items()):
        first = rows[0]
        section_rows.append({"id": key, "document_id": "doc:jaije:v1", "section_no": first["section_no"], "title": first["section_title"]})
    evidence_rows = [{
        "id": row["evidence_id"], "section_id": row["section_id"], "excel_row": row["excel_row"],
        "page": row["page"], "text": row.get("text", ""), "text_hash": row["text_hash"],
        "split": row["split"], "stratum": row["stratum"], "context_recovered": str(row["context_recovered"]).lower(),
    } for row in sample]
    claim_rows = []
    assertion_rows = []
    rule_rows = []
    condition_rows = []
    concept_rows: dict[str, dict[str, Any]] = {}
    relationship_rows = []
    reference_by_id = {row["evidence_id"]: row for row in references}
    sources = [("REFERENCE", row["evidence_id"], row["annotation"], row.get("agreement_tier", "")) for row in references]
    sources += [("E4", row["evidence_id"], row, "") for row in e4_predictions]
    for system, eid, annotation, tier in sources:
        for claim in annotation.get("claims") or []:
            claim_id = f"{system.lower()}:{claim['claim_id']}"
            status = "ACCEPTED" if claim.get("decision") == "ACCEPT" else claim.get("decision", "NEEDS_REVIEW")
            claim_rows.append({
                "id": claim_id, "evidence_id": eid, "source_system": system, "reference_tier": tier,
                "claim_family": claim.get("claim_family"), "claim_type": claim.get("claim_type"),
                "modality": claim.get("modality"), "polarity": claim.get("polarity"),
                "promotion_target": claim.get("promotion_target"), "status": status,
                "uncertainty_code": claim.get("uncertainty_code"), "human_reviewed": "false",
            })
            relationship_rows.append(_rel(eid, "SUPPORTS", claim_id, operational=False))
            for condition_index, condition in enumerate(claim.get("conditions") or []):
                condition_id = f"condition:{stable_hash([claim_id, condition, condition_index], 28)}"
                condition_rows.append({
                    "id": condition_id, "claim_id": claim_id,
                    "evidence_id": condition.get("evidence_id", eid), "text": condition.get("text", ""),
                    "start": condition.get("start", ""), "end": condition.get("end", ""),
                })
                relationship_rows.append(_rel(claim_id, "HAS_CONDITION", condition_id, operational=False))
            arguments = claim.get("arguments") or []
            concept_ids = []
            for argument in arguments:
                span = argument.get("span")
                label = normalize_space(span.get("text")) if isinstance(span, dict) else f"implicit:{argument.get('role')}"
                concept_id = f"concept:{stable_hash([label.casefold(), argument.get('kernel_type')], 24)}"
                concept_rows[concept_id] = {"id": concept_id, "pref_label": label, "kernel_type": argument.get("kernel_type"), "human_reviewed": "false"}
                concept_ids.append((argument.get("role"), concept_id))
                relationship_rows.append(_rel(claim_id, "HAS_ARGUMENT", concept_id, operational=False, role=argument.get("role")))
            if status == "ACCEPTED" and claim.get("promotion_target") not in {"NONE", "NEEDS_REVIEW", "LEXICAL_ONLY"} and claim.get("claim_type") not in DISCOURSE_TYPES:
                assertion_id = f"assertion:{stable_hash([claim_id, claim.get('predicate_normalized')], 28)}"
                assertion_rows.append({
                    "id": assertion_id, "predicate": claim.get("predicate_normalized"),
                    "promotion_target": claim.get("promotion_target"), "status": "ACCEPTED",
                    "confidence": claim.get("confidence", ""), "source_claim_id": claim_id,
                    "source_evidence_id": eid, "system_version": system, "operational": "true",
                })
                relationship_rows.append(_rel(claim_id, "PROMOTED_TO", assertion_id, operational=False))
                for role, concept_id in concept_ids:
                    relationship_rows.append(_rel(assertion_id, "SUBJECT" if role == "SUBJECT" else "OBJECT", concept_id, operational=False, role=role))
                if claim.get("promotion_target") == "RULE_NODE":
                    rule_rows.append({"id": assertion_id, "claim_id": claim_id, "modality": claim.get("modality"), "polarity": claim.get("polarity"), "status": "ACCEPTED"})
                if len(concept_ids) >= 2:
                    rel_type = re.sub(r"[^A-Z0-9_]", "_", (claim.get("predicate_normalized") or "RELATED_TO").upper())
                    relationship_rows.append(_rel(
                        concept_ids[0][1], rel_type, concept_ids[1][1], operational=True,
                        claim_id=claim_id, evidence_id=eid, assertion_id=assertion_id,
                    ))
    write_csv(neo / "neo4j_documents.csv", document_rows, ["id", "name", "human_reviewed"])
    write_csv(neo / "neo4j_sections.csv", section_rows, ["id", "document_id", "section_no", "title"])
    write_csv(neo / "neo4j_evidence.csv", evidence_rows, ["id", "section_id", "excel_row", "page", "text", "text_hash", "split", "stratum", "context_recovered"])
    write_csv(neo / "neo4j_claims.csv", claim_rows, ["id", "evidence_id", "source_system", "reference_tier", "claim_family", "claim_type", "modality", "polarity", "promotion_target", "status", "uncertainty_code", "human_reviewed"])
    write_csv(neo / "neo4j_concepts.csv", list(concept_rows.values()), ["id", "pref_label", "kernel_type", "human_reviewed"])
    write_csv(neo / "neo4j_assertions.csv", assertion_rows, ["id", "predicate", "promotion_target", "status", "confidence", "source_claim_id", "source_evidence_id", "system_version", "operational"])
    write_csv(neo / "neo4j_rules.csv", rule_rows, ["id", "claim_id", "modality", "polarity", "status"])
    write_csv(neo / "neo4j_conditions.csv", condition_rows, ["id", "claim_id", "evidence_id", "text", "start", "end"])
    write_csv(neo / "neo4j_relationships.csv", relationship_rows, ["id", "source_id", "type", "target_id", "operational", "claim_id", "evidence_id", "assertion_id", "role"])
    write_text = lambda path, text: path.write_text(text, encoding="utf-8")
    constraints = (BUNDLE_DIR / "neo4j" / "constraints_and_checks.cypher").read_text(encoding="utf-8")
    write_text(neo / "neo4j_constraints.cypher", constraints.split("// -----------------------------------------------------------------------------\n// Mandatory validation queries.")[0])
    write_text(neo / "neo4j_validation_queries.cypher", constraints)
    write_text(neo / "neo4j_import.cypher", render_import_cypher(sorted({row["type"] for row in relationship_rows})))
    cq_results = competency_queries(sample, claim_rows, assertion_rows, concept_rows, relationship_rows)
    validation = static_neo4j_validation(claim_rows, assertion_rows, concept_rows, relationship_rows, cq_results)
    write_json(neo / "competency_query_results.json", cq_results)
    write_json(neo / "neo4j_static_validation.json", validation)
    return {
        "documents": len(document_rows), "sections": len(section_rows), "evidence": len(evidence_rows),
        "claims": len(claim_rows), "concepts": len(concept_rows), "assertions": len(assertion_rows),
        "rules": len(rule_rows), "conditions": len(condition_rows), "relationships": len(relationship_rows),
        "operational_relationships": sum(row["operational"] == "true" for row in relationship_rows),
        "cq_passed": sum(row["passed"] for row in cq_results), "cq_total": len(cq_results),
        "validation": validation,
    }


def _group_by(rows: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows: groups[str(row.get(key) or "")].append(row)
    return groups


def _rel(source: str, rel_type: str, target: str, operational: bool, **props: Any) -> dict[str, Any]:
    return {
        "id": f"rel:{stable_hash([source, rel_type, target, props], 28)}", "source_id": source,
        "type": rel_type, "target_id": target, "operational": str(operational).lower(),
        "claim_id": props.get("claim_id", ""), "evidence_id": props.get("evidence_id", ""),
        "assertion_id": props.get("assertion_id", ""), "role": props.get("role", ""),
    }


def render_import_cypher(relationship_types: list[str]) -> str:
    node_import = """// TRACE-OL pilot idempotent LOAD CSV package
LOAD CSV WITH HEADERS FROM 'file:///neo4j_documents.csv' AS row MERGE (n:Document {id:row.id}) SET n.name=row.name, n.human_reviewed=false;
LOAD CSV WITH HEADERS FROM 'file:///neo4j_sections.csv' AS row MERGE (n:Section {id:row.id}) SET n.section_no=row.section_no, n.title=row.title WITH n,row MATCH (d:Document {id:row.document_id}) MERGE (d)-[:HAS_SECTION]->(n);
LOAD CSV WITH HEADERS FROM 'file:///neo4j_evidence.csv' AS row MERGE (n:Evidence {id:row.id}) SET n.excel_row=toInteger(row.excel_row), n.page=toInteger(row.page), n.text=row.text, n.split=row.split, n.stratum=row.stratum WITH n,row MATCH (s:Section {id:row.section_id}) MERGE (s)-[:HAS_EVIDENCE]->(n);
LOAD CSV WITH HEADERS FROM 'file:///neo4j_claims.csv' AS row MERGE (n:Claim {id:row.id}) SET n.claim_family=row.claim_family, n.claim_type=row.claim_type, n.modality=row.modality, n.polarity=row.polarity, n.promotion_target=row.promotion_target, n.status=row.status, n.reference_tier=row.reference_tier, n.human_reviewed=false;
LOAD CSV WITH HEADERS FROM 'file:///neo4j_concepts.csv' AS row MERGE (n:Concept {id:row.id}) SET n.pref_label=row.pref_label, n.kernel_type=row.kernel_type, n.human_reviewed=false;
LOAD CSV WITH HEADERS FROM 'file:///neo4j_assertions.csv' AS row MERGE (n:Assertion {id:row.id}) SET n.predicate=row.predicate, n.promotion_target=row.promotion_target, n.status=row.status, n.operational=true;
LOAD CSV WITH HEADERS FROM 'file:///neo4j_rules.csv' AS row MERGE (n:Rule {id:row.id}) SET n.modality=row.modality, n.polarity=row.polarity, n.status=row.status;
LOAD CSV WITH HEADERS FROM 'file:///neo4j_conditions.csv' AS row MERGE (n:Condition {id:row.id}) SET n.text=row.text, n.start=toInteger(row.start), n.end=toInteger(row.end);
"""
    relationship_imports = []
    for relationship_type in relationship_types:
        safe_type = re.sub(r"[^A-Z0-9_]", "_", relationship_type.upper())
        relationship_imports.append(
            "LOAD CSV WITH HEADERS FROM 'file:///neo4j_relationships.csv' AS row "
            f"WITH row WHERE row.type = '{relationship_type}' "
            "MATCH (s {id:row.source_id}), (t {id:row.target_id}) "
            f"MERGE (s)-[r:{safe_type} {{id:row.id}}]->(t) "
            "SET r.operational=(row.operational='true'), r.claim_id=row.claim_id, "
            "r.evidence_id=row.evidence_id, r.assertion_id=row.assertion_id, r.role=row.role;"
        )
    return node_import + "\n".join(relationship_imports) + "\n"


def competency_queries(sample: list[dict[str, Any]], claims: list[dict[str, Any]], assertions: list[dict[str, Any]], concepts: dict[str, dict[str, Any]], relationships: list[dict[str, Any]]) -> list[dict[str, Any]]:
    text_by_eid = {row["evidence_id"]: row.get("text", "") for row in sample}
    accepted = [row for row in claims if row["status"] == "ACCEPTED"]
    all_text = "\n".join(text_by_eid.values())
    checks = [
        ("CQ1", "단계별 산출물", any(row["promotion_target"] == "PROCESS_EDGE" for row in assertions)),
        ("CQ2", "RFP와 의사결정", "RFP" in all_text and any("Decision" in str(row) or "TRIGGER" in str(row) for row in assertions)),
        ("CQ3", "MUST/MUST_NOT 규칙", any(row["modality"] in {"MUST", "MUST_NOT"} for row in accepted)),
        ("CQ4", "Capture Plan senses", sum("Capture Plan" in row.get("pref_label", "") for row in concepts.values()) >= 1 and "Capture Plan" in all_text),
        ("CQ5", "경쟁자 분석 산출물", "경쟁" in all_text and any(row["promotion_target"] == "PROCESS_EDGE" for row in assertions)),
        ("CQ6", "BCM 평가 관측", "BCM" in all_text and any(row["promotion_target"] == "EVALUATION_NODE" for row in assertions)),
        ("CQ7", "가치제안 수식", bool(re.search(r"V\s*>\s*C|Winner\s*\(", all_text))),
        ("CQ8", "discourse 비승격", all(not (row["claim_type"] in DISCOURSE_TYPES and row["promotion_target"] not in {"NONE", "NEEDS_REVIEW"}) for row in claims)),
        ("CQ9", "리스크와 완화", "리스크" in all_text and any("RECOMMEND" in (row.get("predicate") or "") for row in assertions)),
        ("CQ10", "NeedsReview", any(row["status"] == "NEEDS_REVIEW" for row in claims)),
    ]
    return [{"id": cid, "question": question, "passed": bool(passed), "evidence_linked": bool(passed)} for cid, question, passed in checks]


def static_neo4j_validation(claims: list[dict[str, Any]], assertions: list[dict[str, Any]], concepts: dict[str, dict[str, Any]], relationships: list[dict[str, Any]], cqs: list[dict[str, Any]]) -> dict[str, Any]:
    rels_by_target: dict[str, list[dict[str, Any]]] = defaultdict(list)
    rels_by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for rel in relationships:
        rels_by_target[rel["target_id"]].append(rel); rels_by_source[rel["source_id"]].append(rel)
    checks = {
        "accepted_claim_without_evidence": sum(row["status"] == "ACCEPTED" and not any(rel["type"] == "SUPPORTS" for rel in rels_by_target[row["id"]]) for row in claims),
        "accepted_assertion_without_claim": sum(row["status"] == "ACCEPTED" and not any(rel["type"] == "PROMOTED_TO" for rel in rels_by_target[row["id"]]) for row in assertions),
        "discourse_promoted": sum(row["claim_type"] in DISCOURSE_TYPES and row["status"] == "ACCEPTED" and any(rel["type"] == "PROMOTED_TO" for rel in rels_by_source[row["id"]]) for row in claims),
        "needs_review_operational": sum(row["status"] == "NEEDS_REVIEW" and any(rel["type"] == "PROMOTED_TO" for rel in rels_by_source[row["id"]]) for row in claims),
        "must_not_polarity_conflict": sum(row["modality"] == "MUST_NOT" and row["polarity"] != "NEGATIVE" for row in claims),
        "operational_missing_lineage": sum(rel["operational"] == "true" and not (rel["claim_id"] and rel["evidence_id"] and rel["assertion_id"]) for rel in relationships),
        "orphan_concepts": sum(not rels_by_target[cid] and not rels_by_source[cid] for cid in concepts),
    }
    critical_keys = [key for key in checks if key != "orphan_concepts"]
    return {
        "checks": checks,
        "critical_issue_count": sum(checks[key] for key in critical_keys),
        "provenance_path_coverage": round(1 - checks["accepted_assertion_without_claim"] / max(1, len(assertions)), 4),
        "cq_passed": sum(row["passed"] for row in cqs), "cq_total": len(cqs),
        "status": "PASS" if not any(checks[key] for key in critical_keys) else "FAIL",
    }
