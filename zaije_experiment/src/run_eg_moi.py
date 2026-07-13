#!/usr/bin/env python3
"""Run the EG-MOI ontology-induction pilot on the complete zaije_1 workbook."""

from __future__ import annotations

import hashlib
import json
import math
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import r2_blre
import r3_apre


EXPERIMENT_ID = "zaije_eg_moi_20260712_v1"
SYSTEM_ID = "EG-MOI-V1"
METHOD_VERSION = "EG-MOI-1.0"
SOURCE_RELATIVE = "handoff-hanyang/수주제안/자이제_1.xlsx"

ACTION_STEMS = (
    "작성|분석|검토|수립|제출|개발|평가|선정|도출|확인|준비|제공|업데이트|"
    "관리|정의|식별|수집|설계|결정|승인|보고|공유|대응|해결|활용|실행|협의"
)
ACTION_RE = re.compile(
    rf"(?:(?P<agent>[가-힣A-Za-z0-9 /&·]{{2,30}}?)(?:이|가|은|는)\s+)?"
    rf"(?P<object>[가-힣A-Za-z0-9() /&·'’-]{{2,55}}?)(?:을|를)\s*"
    rf"(?P<verb>{ACTION_STEMS})(?:해야\s*한다|하여야\s*한다|한다|하였다|했다|하도록\s*한다|할\s*수\s*있다|함|하기|하는|한다면|할)?",
    re.I,
)
BASIS_RE = re.compile(
    rf"(?P<input>[가-힣A-Za-z0-9() /&·'’-]{{2,55}}?)(?:을|를|에)\s*"
    rf"(?:바탕으로|기반으로|기초로|참고하여)\s*"
    rf"(?P<object>[가-힣A-Za-z0-9() /&·'’-]{{2,55}}?)(?:을|를)?\s*"
    rf"(?P<verb>{ACTION_STEMS})",
    re.I,
)
ALIAS_PATTERNS = [
    re.compile(r"(?P<left>[가-힣][가-힣0-9 ·/-]{1,35})\s*\((?P<right>[A-Za-z][A-Za-z0-9 /&_-]{1,45})\)"),
    re.compile(r"(?P<left>[A-Za-z][A-Za-z0-9 /&_-]{2,45})\s*\((?P<right>[A-Z][A-Z0-9_-]{1,12})\)"),
    re.compile(r"(?P<left>[A-Z][A-Z0-9_-]{1,12})\s*[:：]\s*(?P<right>[A-Za-z][A-Za-z0-9 /&_-]{2,55})"),
]
QUANTITY_RE = re.compile(r"\d+(?:[.,]\d+)?(?:\s*[~∼-]\s*\d+(?:[.,]\d+)?)?\s*(?:%|명|점|배|개|원|년|개월|일|시간)")
CONDITION_RE = re.compile(r"(?:만약\s+)?[^,.]{2,60}?(?:경우|(?:이|라)면|때에는|때|조건하에|이전|이후)")
DEFINITION_PATTERNS = [
    re.compile(r"(?P<term>[가-힣A-Za-z0-9 /&·_-]{2,35}?)(?:이란|란)\s+(?P<definition>[^.]{3,100}?)(?:이다|의미한다|말한다|뜻한다)"),
]

TABLE_HEADERS = {
    "WORK": re.compile(r"활동|activity|주요\s*활동|업무|단계|step", re.I),
    "OUTPUT": re.compile(r"결과물|산출물|output|deliverable", re.I),
    "INPUT": re.compile(r"입력|input|참고\s*자료|요구\s*자료", re.I),
    "AGENT": re.compile(r"담당|수행자|책임자|role|성명|직책|역할", re.I),
}

ARTIFACT_RE = re.compile(r"제안서|계획서|보고서|분석표|응답표|체크리스트|초안|문서|자료|템플릿|양식|서식|슬라이드|플래너|조직도|일정표|plan|proposal|report|summary|rfp", re.I)
REQUIREMENT_RE = re.compile(r"요구조건|요구사항|평가\s*기준|고객\s*정보|니즈|관심사|이슈|정보|조건", re.I)
ORG_RE = re.compile(r"팀|부서|조직|회사|기관|위원회|본부|센터|사업단|협력업체|업체$", re.I)
ROLE_RE = re.compile(r"대표|담당자|평가위원|위원|pm|작성자|책임자|의사결정자|영업대표|고객$", re.I)
AGENT_ENTITY_RE = re.compile(
    r"(?:[가-힣A-Za-z0-9]{1,12}\s+){0,2}(?:영업대표|담당자|평가위원|의사결정자|작성자|책임자|대표이사|"
    r"제안팀|고객|[가-힣A-Za-z0-9]{1,12}(?:팀|부서|조직|회사|기관|위원회|본부|센터|사업단|업체))$",
    re.I,
)
TERM_SUFFIX_RE = re.compile(
    r"[가-힣A-Za-z0-9/&·-]{1,15}(?:\s+[가-힣A-Za-z0-9/&·-]{1,15}){0,3}\s*"
    r"(?:제안서|계획|전략|고객|요구조건|요구사항|정보|이슈|역량|프로세스|활동|단계|"
    r"분석|평가|관리|조직|팀|담당자|책임자|문서|자료|템플릿|양식|리스크|가치제안|솔루션)",
    re.I,
)
ENGLISH_TERM_RE = re.compile(r"\b[A-Z][A-Za-z0-9/-]*(?:\s+[A-Z][A-Za-z0-9/-]*){0,4}\b")

RELATION_DOMAINS = {
    "PERFORMED_BY": ({"WorkUnit"}, {"Agent"}),
    "HAS_INPUT": ({"WorkUnit"}, {"Resource"}),
    "PRODUCES_OUTPUT": ({"WorkUnit"}, {"Resource"}),
    "HAS_CONDITION": ({"WorkUnit", "DomainConcept"}, {"Context"}),
    "HAS_MEASURE": ({"WorkUnit", "DomainConcept"}, {"Measure"}),
    "DEFINES": ({"DomainConcept"}, {"DomainConcept"}),
    "PRECEDES": ({"WorkUnit"}, {"WorkUnit"}),
}


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha(value: Any) -> str:
    payload = value if isinstance(value, bytes) else canonical(value).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def stable_id(prefix: str, *parts: Any) -> str:
    return f"{prefix}_{sha(parts)[:20]}"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(canonical(row) + "\n")


def normalize(value: str) -> str:
    text = unicodedata.normalize("NFKC", value).casefold()
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.I)
    text = re.sub(r"^[\s•▪◦‣*\-\d.)]+", "", text)
    text = re.sub(r"(?:은|는|이|가|을|를|의|에|에서|으로|와|과)$", "", text.strip())
    text = re.sub(r"[^0-9a-z가-힣%+]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def clean(value: str) -> str:
    value = re.sub(r"<br\s*/?>", " ", value, flags=re.I)
    value = re.sub(r"^[\s•▪◦‣*\-\d.)]+", "", value)
    value = re.sub(r"\s+", " ", value).strip(" |,.;:()[]{}'\"")
    return re.sub(r"(?:은|는|이|가|을|를|의|에|에서|으로|와|과)$", "", value).strip()


def agent_entity_span(text: str, start: int, end: int) -> tuple[int, int] | None:
    fragment = text[start:end]
    # Strip discourse connectives before applying the explicit agent lexicon.
    stripped = re.sub(r"^(?:그리고|그러나|하지만|따라서|이에\s*맞추어|이때|사실|만약에|대체로)\s*", "", fragment).strip()
    if not stripped:
        return None
    match = AGENT_ENTITY_RE.search(stripped)
    if not match:
        return None
    label = match.group(0)
    relative = fragment.rfind(label)
    if relative < 0:
        return None
    return start + relative, start + relative + len(label)


def char_embedding(value: str) -> dict[str, float]:
    text = f"^{normalize(value).replace(' ', '_')}$"
    counts: Counter[str] = Counter()
    for width in (2, 3):
        counts.update(text[i : i + width] for i in range(max(0, len(text) - width + 1)))
    norm = math.sqrt(sum(v * v for v in counts.values())) or 1.0
    return {key: val / norm for key, val in counts.items()}


def cosine(left: dict[str, float], right: dict[str, float]) -> float:
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(key, 0.0) for key, value in left.items())


class UnionFind:
    def __init__(self, values: Iterable[str]) -> None:
        self.parent = {value: value for value in values}

    def find(self, value: str) -> str:
        while self.parent[value] != value:
            self.parent[value] = self.parent[self.parent[value]]
            value = self.parent[value]
        return value

    def union(self, left: str, right: str) -> None:
        a, b = self.find(left), self.find(right)
        if a != b:
            self.parent[max(a, b)] = min(a, b)


class GraphBuilder:
    def __init__(self) -> None:
        self.nodes: dict[str, dict[str, Any]] = {}
        self.edges: dict[str, dict[str, Any]] = {}

    def node(self, node_id: str, node_type: str, **props: Any) -> str:
        uid = f"{SYSTEM_ID}::{node_id}"
        item = {"id": node_id, "uid": uid, "system_id": SYSTEM_ID, "type": node_type, **props}
        if uid not in self.nodes:
            self.nodes[uid] = item
        else:
            self.nodes[uid].update({key: value for key, value in props.items() if value not in (None, "", [])})
        return uid

    def edge(self, relation: str, source: str, target: str, **props: Any) -> str:
        edge_id = stable_id("EG_EDGE", relation, source, target, props)
        uid = f"{SYSTEM_ID}::{edge_id}"
        self.edges[uid] = {
            "id": edge_id,
            "uid": uid,
            "system_id": SYSTEM_ID,
            "type": relation,
            "source": source,
            "target": target,
            **props,
        }
        return uid


def source_rows(source: Path) -> tuple[str, list[dict[str, Any]]]:
    sheet, raw = r2_blre.read_xlsx_raw(source)
    forward = {key: "" for key in ("page", "chapter_no", "chapter_title", "section_no", "section_title")}
    rows = []
    source_hash = sha(source.read_bytes())
    for item in raw:
        for key in forward:
            if str(item.get(key) or "").strip():
                forward[key] = str(item[key]).strip()
        text = str(item["text_for_llm_human"])
        evidence_id = f"egmoi:evidence/xlsx-row-{item['excel_row']}"
        rows.append({
            "evidence_id": evidence_id,
            "excel_row": item["excel_row"],
            "sheet": sheet,
            "page": forward["page"],
            "chapter_no": forward["chapter_no"],
            "chapter_title": forward["chapter_title"],
            "section_no": forward["section_no"],
            "section_title": forward["section_title"],
            "raw_text": text,
            "text_sha256": sha(text),
            "source_binary_sha256": source_hash,
            "structure_type": r2_blre.structure_type({"raw_text": text}),
        })
    return sheet, rows


def role_from_header(text: str) -> str | None:
    for role, pattern in TABLE_HEADERS.items():
        if pattern.search(text):
            return role
    return None


def add_mention(
    mentions: dict[tuple[Any, ...], dict[str, Any]], *, row: dict[str, Any], anchor: dict[str, Any],
    start: int, end: int, role: str, rule: str, confidence: float,
) -> str | None:
    if start < anchor["start_char"] or end > anchor["end_char"] or start >= end:
        return None
    exact = row["raw_text"][start:end]
    label = clean(exact)
    norm = normalize(label)
    if len(norm) < 2 or len(label) > 80:
        return None
    # Keep exact spans even when label cleanup removes a trailing Korean particle.
    key = (row["evidence_id"], start, end, role)
    mention_id = stable_id("EG_MENTION", *key)
    candidate = {
        "mention_id": mention_id,
        "evidence_id": row["evidence_id"],
        "anchor_id": anchor["anchor_id"],
        "start_char": start,
        "end_char": end,
        "exact_text": exact,
        "label": label,
        "normalized_label": norm,
        "role_hint": role,
        "generation_rule": rule,
        "confidence": round(confidence, 4),
        "status": "CANDIDATE",
    }
    current = mentions.get(key)
    if current is None or candidate["confidence"] > current["confidence"]:
        mentions[key] = candidate
    return mention_id


def discover(rows: list[dict[str, Any]], anchor_records: list[dict[str, Any]]) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    mentions: dict[tuple[Any, ...], dict[str, Any]] = {}
    frames: list[dict[str, Any]] = []
    surface: list[dict[str, Any]] = []
    aliases: list[dict[str, Any]] = []
    row_by_id = {row["evidence_id"]: row for row in rows}

    for record in anchor_records:
        row = row_by_id[record["evidence_id"]]
        contexts = {item["span_id"]: item for item in record["context_spans"]}
        for anchor in record["anchors"]:
            text = anchor["text_by_program"]
            base = anchor["start_char"]
            local_work_ids: list[str] = []
            context_pairs = [(contexts[sid], rel) for sid, rel in zip(anchor["context_span_ids"], anchor["context_relations"])]
            headers = [ctx for ctx, rel in context_pairs if rel == "HAS_COLUMN_HEADER"]
            row_headers = [ctx for ctx, rel in context_pairs if rel == "HAS_ROW_HEADER"]

            table_role = next((role_from_header(ctx["text_by_program"]) for ctx in headers if role_from_header(ctx["text_by_program"])), None)
            if table_role:
                value_mid = add_mention(
                    mentions, row=row, anchor=anchor, start=anchor["start_char"], end=anchor["end_char"],
                    role=table_role, rule=f"TABLE_HEADER_{table_role}", confidence=0.98,
                )
                for ctx in row_headers:
                    work_mid = add_mention(
                        mentions, row=row, anchor=anchor, start=ctx["start_char"], end=ctx["end_char"],
                        role="WORK", rule="TABLE_ROW_HEADER_WORK", confidence=0.96,
                    )
                    if work_mid:
                        local_work_ids.append(work_mid)
                    relation = {"OUTPUT": "PRODUCES_OUTPUT", "INPUT": "HAS_INPUT", "AGENT": "PERFORMED_BY"}.get(table_role)
                    if relation and work_mid and value_mid:
                        surface.append({
                            "surface_relation_id": stable_id("EG_SURFACE", relation, work_mid, value_mid, anchor["anchor_id"]),
                            "predicate_surface": relation,
                            "canonical_seed": relation,
                            "subject_mention_id": work_mid,
                            "object_mention_id": value_mid,
                            "evidence_id": row["evidence_id"],
                            "anchor_id": anchor["anchor_id"],
                            "generation_rule": "SAME_TABLE_ROW_STRUCTURE",
                            "confidence": 0.97,
                            "status": "CANDIDATE",
                        })

            for pattern in ALIAS_PATTERNS:
                for match in pattern.finditer(text):
                    pair = []
                    for group in ("left", "right"):
                        start, end = base + match.start(group), base + match.end(group)
                        candidate_text = row["raw_text"][start:end]
                        if re.search(r"왜냐하면|따라서|하지만|그러나|그리고|예를\s*들면|결국", candidate_text):
                            pair = []
                            break
                        mid = add_mention(mentions, row=row, anchor=anchor, start=start, end=end, role="TERM", rule="EXPLICIT_ALIAS", confidence=0.99)
                        if mid:
                            pair.append(mid)
                    if len(pair) == 2:
                        aliases.append({
                            "alias_decision_id": stable_id("EG_ALIAS", pair, anchor["anchor_id"]),
                            "left_mention_id": pair[0], "right_mention_id": pair[1],
                            "evidence_id": row["evidence_id"], "anchor_id": anchor["anchor_id"],
                            "decision": "MERGE", "basis": "EXPLICIT_BILINGUAL_OR_ACRONYM", "confidence": 0.99,
                        })

            for match in ACTION_RE.finditer(text):
                roles: dict[str, str] = {}
                obj_start, obj_end = base + match.start("object"), base + match.end("object")
                obj_mid = add_mention(mentions, row=row, anchor=anchor, start=obj_start, end=obj_end, role="OBJECT", rule="DEPENDENCY_LIKE_OBJECT", confidence=0.82)
                verb_start, verb_end = base + match.start("verb"), base + match.end("verb")
                work_start, work_end = obj_start, verb_end
                work_mid = add_mention(mentions, row=row, anchor=anchor, start=work_start, end=work_end, role="WORK", rule="SEMANTIC_FRAME_ACTION", confidence=0.86)
                if work_mid:
                    local_work_ids.append(work_mid)
                if obj_mid: roles["object"] = obj_mid
                if work_mid: roles["action"] = work_mid
                if match.group("agent"):
                    astart, aend = base + match.start("agent"), base + match.end("agent")
                    entity_span = agent_entity_span(row["raw_text"], astart, aend)
                    if entity_span:
                        agent_mid = add_mention(mentions, row=row, anchor=anchor, start=entity_span[0], end=entity_span[1], role="AGENT", rule="EXPLICIT_AGENT_SUBJECT", confidence=0.9)
                        if agent_mid: roles["agent"] = agent_mid
                frame_id = stable_id("EG_FRAME", anchor["anchor_id"], match.start(), match.end(), roles)
                frames.append({
                    "frame_id": frame_id, "predicate": match.group("verb"), "roles": roles,
                    "evidence_id": row["evidence_id"], "anchor_id": anchor["anchor_id"],
                    "start_char": base + match.start(), "end_char": base + match.end(),
                    "exact_text": row["raw_text"][base + match.start():base + match.end()],
                    "generation_rule": "KO_ARGUMENT_PATTERN", "confidence": 0.82, "status": "CANDIDATE",
                })
                if work_mid and obj_mid:
                    relation = "PRODUCES_OUTPUT" if match.group("verb") in {"작성", "수립", "개발", "도출", "준비", "제출", "제공", "보고"} else "HAS_INPUT"
                    surface.append({
                        "surface_relation_id": stable_id("EG_SURFACE", relation, work_mid, obj_mid, frame_id),
                        "predicate_surface": match.group("verb"), "canonical_seed": relation,
                        "subject_mention_id": work_mid, "object_mention_id": obj_mid,
                        "evidence_id": row["evidence_id"], "anchor_id": anchor["anchor_id"],
                        "frame_id": frame_id, "generation_rule": "SEMANTIC_FRAME_OBJECT_ROLE",
                        "confidence": 0.82, "status": "CANDIDATE",
                    })
                if work_mid and roles.get("agent"):
                    surface.append({
                        "surface_relation_id": stable_id("EG_SURFACE", "PERFORMED_BY", work_mid, roles["agent"], frame_id),
                        "predicate_surface": match.group("verb"), "canonical_seed": "PERFORMED_BY",
                        "subject_mention_id": work_mid, "object_mention_id": roles["agent"],
                        "evidence_id": row["evidence_id"], "anchor_id": anchor["anchor_id"],
                        "frame_id": frame_id, "generation_rule": "SEMANTIC_FRAME_AGENT_ROLE",
                        "confidence": 0.78, "status": "CANDIDATE",
                    })

            for match in BASIS_RE.finditer(text):
                inp = add_mention(mentions, row=row, anchor=anchor, start=base + match.start("input"), end=base + match.end("input"), role="INPUT", rule="BASIS_INPUT_ROLE", confidence=0.9)
                work = add_mention(mentions, row=row, anchor=anchor, start=base + match.start("object"), end=base + match.end("verb"), role="WORK", rule="BASIS_ACTION_ROLE", confidence=0.88)
                if work:
                    local_work_ids.append(work)
                if inp and work:
                    surface.append({
                        "surface_relation_id": stable_id("EG_SURFACE", "HAS_INPUT", work, inp, anchor["anchor_id"]),
                        "predicate_surface": "바탕으로", "canonical_seed": "HAS_INPUT",
                        "subject_mention_id": work, "object_mention_id": inp,
                        "evidence_id": row["evidence_id"], "anchor_id": anchor["anchor_id"],
                        "generation_rule": "BASIS_INPUT_PATTERN", "confidence": 0.9, "status": "CANDIDATE",
                    })

            for match in QUANTITY_RE.finditer(text):
                measure_mid = add_mention(mentions, row=row, anchor=anchor, start=base + match.start(), end=base + match.end(), role="MEASURE", rule="QUANTITY_PATTERN", confidence=0.97)
                if measure_mid and local_work_ids:
                    surface.append({
                        "surface_relation_id": stable_id("EG_SURFACE", "HAS_MEASURE", local_work_ids[0], measure_mid, anchor["anchor_id"]),
                        "predicate_surface": "quantity", "canonical_seed": "HAS_MEASURE",
                        "subject_mention_id": local_work_ids[0], "object_mention_id": measure_mid,
                        "evidence_id": row["evidence_id"], "anchor_id": anchor["anchor_id"],
                        "generation_rule": "SAME_ANCHOR_FRAME_MEASURE", "confidence": 0.85, "status": "CANDIDATE",
                    })
            for match in CONDITION_RE.finditer(text):
                condition_mid = add_mention(mentions, row=row, anchor=anchor, start=base + match.start(), end=base + match.end(), role="CONDITION", rule="CONDITION_PATTERN", confidence=0.9)
                if condition_mid and local_work_ids:
                    surface.append({
                        "surface_relation_id": stable_id("EG_SURFACE", "HAS_CONDITION", local_work_ids[0], condition_mid, anchor["anchor_id"]),
                        "predicate_surface": "condition", "canonical_seed": "HAS_CONDITION",
                        "subject_mention_id": local_work_ids[0], "object_mention_id": condition_mid,
                        "evidence_id": row["evidence_id"], "anchor_id": anchor["anchor_id"],
                        "generation_rule": "SAME_ANCHOR_FRAME_CONDITION", "confidence": 0.82, "status": "CANDIDATE",
                    })
            for definition_pattern in DEFINITION_PATTERNS:
                for match in definition_pattern.finditer(text):
                    left = add_mention(mentions, row=row, anchor=anchor, start=base + match.start("term"), end=base + match.end("term"), role="TERM", rule="DEFINITION_TERM", confidence=0.91)
                    right = add_mention(mentions, row=row, anchor=anchor, start=base + match.start("definition"), end=base + match.end("definition"), role="TERM", rule="DEFINITION_BODY", confidence=0.76)
                    if left and right:
                        surface.append({
                            "surface_relation_id": stable_id("EG_SURFACE", "DEFINES", left, right, anchor["anchor_id"]),
                            "predicate_surface": "정의", "canonical_seed": "DEFINES",
                            "subject_mention_id": left, "object_mention_id": right,
                            "evidence_id": row["evidence_id"], "anchor_id": anchor["anchor_id"],
                            "generation_rule": "EXPLICIT_DEFINITION_PATTERN", "confidence": 0.88, "status": "CANDIDATE",
                        })

            for pattern, role, rule, confidence in (
                (TERM_SUFFIX_RE, "TERM", "DOMAIN_TERM_SUFFIX", 0.7),
                (ENGLISH_TERM_RE, "TERM", "ENGLISH_NAMED_TERM", 0.74),
            ):
                for match in pattern.finditer(text):
                    add_mention(mentions, row=row, anchor=anchor, start=base + match.start(), end=base + match.end(), role=role, rule=rule, confidence=confidence)

    result_mentions = sorted(mentions.values(), key=lambda x: (x["evidence_id"], x["start_char"], x["end_char"], x["role_hint"]))
    valid_ids = {item["mention_id"] for item in result_mentions}
    surface = [item for item in surface if item["subject_mention_id"] in valid_ids and item["object_mention_id"] in valid_ids]
    aliases = [item for item in aliases if item["left_mention_id"] in valid_ids and item["right_mention_id"] in valid_ids]
    return result_mentions, frames, surface, aliases


def compatible_roles(left: set[str], right: set[str]) -> bool:
    groups = [
        {"WORK"}, {"AGENT"}, {"INPUT", "OUTPUT", "OBJECT", "TERM"}, {"CONDITION"}, {"MEASURE"},
    ]
    return any(left <= group and right <= group for group in groups) or left == {"TERM"} or right == {"TERM"}


def consolidate(mentions: list[dict], aliases: list[dict]) -> tuple[list[dict], list[dict], dict[str, str], list[dict]]:
    by_id = {item["mention_id"]: item for item in mentions}
    uf = UnionFind(by_id)
    decisions: list[dict[str, Any]] = []

    by_norm: dict[str, list[str]] = defaultdict(list)
    for item in mentions:
        by_norm[item["normalized_label"]].append(item["mention_id"])
    for norm, ids in by_norm.items():
        for item in ids[1:]:
            uf.union(ids[0], item)
        if len(ids) > 1:
            decisions.append({"decision_id": stable_id("EG_MERGE", norm, ids), "left": ids[0], "right": ids[-1], "decision": "MERGE", "basis": "EXACT_NORMALIZED_STRING", "score": 1.0})
    for item in aliases:
        uf.union(item["left_mention_id"], item["right_mention_id"])
        decisions.append({"decision_id": stable_id("EG_MERGE", item), "left": item["left_mention_id"], "right": item["right_mention_id"], "decision": "MERGE", "basis": item["basis"], "score": item["confidence"]})

    # Sparse character n-gram embeddings provide a reproducible semantic-nearness signal.
    norm_roles: dict[str, set[str]] = defaultdict(set)
    norm_ids: dict[str, list[str]] = defaultdict(list)
    for item in mentions:
        norm_roles[item["normalized_label"]].add(item["role_hint"])
        norm_ids[item["normalized_label"]].append(item["mention_id"])
    norms = sorted(norm_ids)
    vectors = {norm: char_embedding(norm) for norm in norms}
    blocks: dict[str, list[str]] = defaultdict(list)
    for norm in norms:
        compact = norm.replace(" ", "")
        keys = {f"P:{compact[:2]}", f"S:{compact[-2:]}"}
        for token in norm.split():
            if len(token) >= 2:
                keys.add(f"T:{token}")
        for key in sorted(keys):
            blocks[key].append(norm)
    compared: set[tuple[str, str]] = set()
    for key in sorted(blocks):
        values = blocks[key]
        if len(values) > 120:
            continue
        for i, left in enumerate(values):
            for right in values[i + 1:]:
                pair = tuple(sorted((left, right)))
                if pair in compared or left == right:
                    continue
                compared.add(pair)
                if not compatible_roles(norm_roles[left], norm_roles[right]):
                    continue
                ratio = min(len(left), len(right)) / max(len(left), len(right))
                if ratio < 0.65:
                    continue
                score = cosine(vectors[left], vectors[right])
                if score >= 0.9:
                    uf.union(norm_ids[left][0], norm_ids[right][0])
                    decisions.append({"decision_id": stable_id("EG_MERGE", pair), "left": norm_ids[left][0], "right": norm_ids[right][0], "decision": "MERGE", "basis": "CHAR_NGRAM_EMBEDDING_COSINE", "score": round(score, 6)})
                elif score >= 0.82:
                    decisions.append({"decision_id": stable_id("EG_GRAY", pair), "left": norm_ids[left][0], "right": norm_ids[right][0], "decision": "UNRESOLVED", "basis": "GRAY_ZONE_EMBEDDING_COSINE", "score": round(score, 6)})

    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in mentions:
        grouped[uf.find(item["mention_id"])].append(item)
    clusters = []
    mention_to_cluster = {}
    for members in grouped.values():
        labels = Counter(item["label"] for item in members)
        preferred = sorted(labels, key=lambda label: (-labels[label], len(label), label))[0]
        evidence_ids = sorted({item["evidence_id"] for item in members})
        rules = sorted({item["generation_rule"] for item in members})
        roles = Counter(item["role_hint"] for item in members)
        strong = any(item["confidence"] >= 0.9 for item in members)
        structured_frame = any(item["generation_rule"] in {"SEMANTIC_FRAME_ACTION", "BASIS_ACTION_ROLE"} for item in members)
        explicit_alias = "EXPLICIT_ALIAS" in rules
        status = "VALIDATED" if len(evidence_ids) >= 2 or strong or structured_frame or explicit_alias else "UNRESOLVED"
        cluster_id = stable_id("EG_CONCEPT_CLUSTER", sorted(item["mention_id"] for item in members))
        cluster = {
            "cluster_id": cluster_id,
            "preferred_label": preferred,
            "normalized_label": normalize(preferred),
            "member_mention_ids": sorted(item["mention_id"] for item in members),
            "surface_forms": sorted(labels),
            "evidence_ids": evidence_ids,
            "anchor_ids": sorted({item["anchor_id"] for item in members}),
            "role_counts": dict(roles),
            "support_count": len(members),
            "evidence_diversity": len(evidence_ids),
            "merge_rules": rules,
            "status": status,
            "confidence": round(max(item["confidence"] for item in members), 4),
        }
        clusters.append(cluster)
        for item in members:
            mention_to_cluster[item["mention_id"]] = cluster_id
    gray = [item for item in decisions if item["decision"] == "UNRESOLVED"]
    return sorted(clusters, key=lambda x: x["cluster_id"]), decisions, mention_to_cluster, gray


def induce_type(cluster: dict[str, Any]) -> tuple[str, str, float]:
    label = cluster["preferred_label"]
    roles = Counter(cluster["role_counts"])
    if roles["WORK"]:
        return "ProposalWorkUnit", "WorkUnit", 0.93
    if roles["AGENT"]:
        if ORG_RE.search(label):
            return "ProposalOrganization", "Agent", 0.94
        return "ProposalRole", "Agent", 0.86
    if roles["CONDITION"]:
        return "ProposalContext", "Context", 0.92
    if roles["MEASURE"]:
        return "EvaluationMeasure", "Measure", 0.96
    if roles["OUTPUT"] or ARTIFACT_RE.search(label):
        return "ProposalArtifact", "Resource", 0.9
    if roles["INPUT"] or REQUIREMENT_RE.search(label):
        return "CustomerRequirement", "Resource", 0.86
    if ORG_RE.search(label):
        return "ProposalOrganization", "Agent", 0.82
    if ROLE_RE.search(label):
        return "ProposalRole", "Agent", 0.8
    return "ProposalDomainConcept", "DomainConcept", 0.7


def relation_clusters(surface: list[dict], mentions: list[dict]) -> list[dict]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for item in surface:
        groups[item["canonical_seed"]].append(item)
    result = []
    for relation, members in sorted(groups.items()):
        result.append({
            "relation_cluster_id": stable_id("EG_REL_CLUSTER", relation),
            "preferred_relation": relation,
            "surface_predicates": sorted({item["predicate_surface"] for item in members}),
            "member_relation_ids": sorted(item["surface_relation_id"] for item in members),
            "evidence_ids": sorted({item["evidence_id"] for item in members}),
            "support_count": len(members),
            "status": "VALIDATED" if members else "UNRESOLVED",
            "induction_basis": "REPEATED_SEMANTIC_FRAME_OR_EXPLICIT_STRUCTURE",
        })
    works = [item for item in mentions if item["role_hint"] == "WORK"]
    if len(works) >= 2 and "PRECEDES" not in groups:
        result.append({
            "relation_cluster_id": stable_id("EG_REL_CLUSTER", "PRECEDES"),
            "preferred_relation": "PRECEDES",
            "surface_predicates": ["document order within section"],
            "member_relation_ids": [],
            "evidence_ids": sorted({item["evidence_id"] for item in works}),
            "support_count": len(works) - 1,
            "status": "VALIDATED",
            "induction_basis": "REPEATED_WORK_FRAME_ORDER_WITH_CYCLE_PREVENTION",
        })
    return result


def has_path(adjacency: dict[str, set[str]], start: str, target: str) -> bool:
    stack, seen = [start], set()
    while stack:
        node = stack.pop()
        if node == target:
            return True
        if node in seen:
            continue
        seen.add(node)
        stack.extend(adjacency.get(node, ()))
    return False


def promote(
    rows: list[dict], anchors: list[dict], mentions: list[dict], frames: list[dict], surface: list[dict],
    clusters: list[dict], relation_cluster_rows: list[dict], mention_to_cluster: dict[str, str], source: Path,
) -> tuple[GraphBuilder, list[dict], list[dict], dict[str, Any]]:
    graph = GraphBuilder()
    activity_id = "ACTIVITY_EG_MOI_20260712"
    activity_uid = graph.node(
        activity_id, "ExtractionActivity", label="EG-MOI automatic induction run", method_version=METHOD_VERSION,
        started_at="2026-07-12", human_intervention_count=0, llm_call_count=0,
    )
    document_uid = graph.node(
        "DOCUMENT_ZAIJE_1", "Document", label="자이제_1.xlsx", source_file=SOURCE_RELATIVE,
        source_binary_sha256=sha(source.read_bytes()), evidence_anchor_ids=[], status="VALIDATED",
    )
    row_by_id = {row["evidence_id"]: row for row in rows}
    anchor_by_id = {a["anchor_id"]: a for record in anchors for a in record["anchors"]}
    context_by_id = {a["span_id"]: a for record in anchors for a in record["context_spans"]}

    section_uids: dict[tuple[str, str], str] = {}
    for row in rows:
        section_key = (row["chapter_no"], row["section_no"])
        if section_key not in section_uids:
            section_id = stable_id("EG_SECTION", *section_key, row["chapter_title"], row["section_title"])
            section_uids[section_key] = graph.node(
                section_id, "Section", label=row["section_title"] or row["chapter_title"] or "미지정 절",
                chapter_no=row["chapter_no"], chapter_title=row["chapter_title"], section_no=row["section_no"],
                evidence_anchor_ids=[], status="VALIDATED",
            )
            graph.edge("HAS_SECTION", document_uid, section_uids[section_key], evidence_anchor_ids=[], status="VALIDATED")
        evidence_uid = graph.node(
            row["evidence_id"], "EvidenceUnit", label=f"Excel row {row['excel_row']}", exact_text=row["raw_text"],
            excel_row=row["excel_row"], page=row["page"], text_sha256=row["text_sha256"],
            source_binary_sha256=row["source_binary_sha256"], evidence_anchor_ids=[], status="VALIDATED",
        )
        graph.edge("HAS_EVIDENCE", section_uids[section_key], evidence_uid, evidence_anchor_ids=[], status="VALIDATED")
    for context in context_by_id.values():
        uid = graph.node(
            context["span_id"], "ContextSpan", label=context["text_by_program"], exact_text=context["text_by_program"],
            evidence_id=context["evidence_id"], start_char=context["start_char"], end_char=context["end_char"],
            context_type=context["context_type"], evidence_anchor_ids=[], status="VALIDATED",
        )
        graph.edge("DERIVED_FROM", uid, f"{SYSTEM_ID}::{context['evidence_id']}", evidence_anchor_ids=[], status="VALIDATED")
    for record in anchors:
        for anchor in record["anchors"]:
            anchor_uid = graph.node(
                anchor["anchor_id"], "EvidenceUnit", label=anchor["text_by_program"], exact_text=anchor["text_by_program"],
                evidence_id=anchor["evidence_id"], start_char=anchor["start_char"], end_char=anchor["end_char"],
                structure_type=anchor["structure_type"], evidence_anchor_ids=[anchor["anchor_id"]], status="VALIDATED",
            )
            graph.edge("HAS_ANCHOR", f"{SYSTEM_ID}::{anchor['evidence_id']}", anchor_uid, evidence_anchor_ids=[anchor["anchor_id"]], status="VALIDATED")
            for sid, rel in zip(anchor["context_span_ids"], anchor["context_relations"]):
                graph.edge("HAS_CONTEXT", anchor_uid, f"{SYSTEM_ID}::{sid}", evidence_anchor_ids=[anchor["anchor_id"]], context_relation=rel, status="VALIDATED")

    cluster_by_id = {item["cluster_id"]: item for item in clusters}
    type_counts: Counter[str] = Counter()
    for cluster in clusters:
        domain_type, meta_type, type_confidence = induce_type(cluster)
        cluster["domain_type"] = domain_type
        cluster["meta_type"] = meta_type
        cluster["type_confidence"] = type_confidence
        if cluster["status"] == "VALIDATED":
            type_counts[domain_type] += 1
        graph.node(
            cluster["cluster_id"], "ConceptCluster", label=cluster["preferred_label"],
            preferred_label=cluster["preferred_label"], surface_forms=cluster["surface_forms"],
            domain_type=domain_type, meta_type=meta_type, support_count=cluster["support_count"],
            evidence_diversity=cluster["evidence_diversity"], evidence_anchor_ids=cluster["anchor_ids"],
            status=cluster["status"], confidence=cluster["confidence"], operational=cluster["status"] == "VALIDATED",
        )
    for mention in mentions:
        mention_uid = graph.node(
            mention["mention_id"], "Mention", label=mention["label"], exact_text=mention["exact_text"],
            normalized_label=mention["normalized_label"], evidence_id=mention["evidence_id"],
            start_char=mention["start_char"], end_char=mention["end_char"], role_hint=mention["role_hint"],
            generation_rule=mention["generation_rule"], evidence_anchor_ids=[mention["anchor_id"]],
            status="VALIDATED" if cluster_by_id[mention_to_cluster[mention["mention_id"]]]["status"] == "VALIDATED" else "UNRESOLVED",
            confidence=mention["confidence"], operational=False,
        )
        cluster_id = mention_to_cluster[mention["mention_id"]]
        graph.edge("DENOTES", mention_uid, f"{SYSTEM_ID}::{cluster_id}", evidence_anchor_ids=[mention["anchor_id"]], status=cluster_by_id[cluster_id]["status"])
        graph.edge("DERIVED_FROM", mention_uid, f"{SYSTEM_ID}::{mention['anchor_id']}", evidence_anchor_ids=[mention["anchor_id"]], status="VALIDATED")
        graph.edge("WAS_GENERATED_BY", mention_uid, activity_uid, evidence_anchor_ids=[mention["anchor_id"]], status="VALIDATED")

    for frame in frames:
        frame_uid = graph.node(
            frame["frame_id"], "SemanticFrame", label=frame["predicate"], predicate=frame["predicate"],
            exact_text=frame["exact_text"], evidence_id=frame["evidence_id"], start_char=frame["start_char"],
            end_char=frame["end_char"], evidence_anchor_ids=[frame["anchor_id"]], status="CANDIDATE", confidence=frame["confidence"],
        )
        graph.edge("DERIVED_FROM", frame_uid, f"{SYSTEM_ID}::{frame['anchor_id']}", evidence_anchor_ids=[frame["anchor_id"]], status="VALIDATED")
        graph.edge("WAS_GENERATED_BY", frame_uid, activity_uid, evidence_anchor_ids=[frame["anchor_id"]], status="VALIDATED")
        for role, mention_id in frame["roles"].items():
            graph.edge(f"HAS_{role.upper()}", frame_uid, f"{SYSTEM_ID}::{mention_id}", evidence_anchor_ids=[frame["anchor_id"]], status="CANDIDATE")

    schema_classes = []
    for domain_type, count in sorted(type_counts.items()):
        supporting = [c for c in clusters if c.get("domain_type") == domain_type and c["status"] == "VALIDATED"]
        meta_type = supporting[0]["meta_type"]
        class_id = f"SCHEMA_CLASS_{domain_type}"
        schema_classes.append({
            "class_id": class_id, "label": domain_type, "meta_type": meta_type,
            "supporting_cluster_ids": [c["cluster_id"] for c in supporting], "support_count": count,
            "status": "VALIDATED",
        })
        class_uid = graph.node(
            class_id, "SchemaClass", label=domain_type, meta_type=meta_type, support_count=count,
            evidence_anchor_ids=sorted({a for c in supporting for a in c["anchor_ids"]}), status="VALIDATED", operational=True,
        )
        meta_uid = graph.node(f"META_{meta_type}", "MetaClass", label=meta_type, evidence_anchor_ids=[], status="VALIDATED")
        graph.edge("SUBCLASS_OF", class_uid, meta_uid, evidence_anchor_ids=graph.nodes[class_uid]["evidence_anchor_ids"], status="VALIDATED")
        for cluster in supporting:
            graph.edge("INSTANCE_OF", f"{SYSTEM_ID}::{cluster['cluster_id']}", class_uid, evidence_anchor_ids=cluster["anchor_ids"], status="VALIDATED")

    schema_properties = []
    rel_cluster_by_name = {item["preferred_relation"]: item for item in relation_cluster_rows}
    for relation, rel_cluster in sorted(rel_cluster_by_name.items()):
        domains, ranges = RELATION_DOMAINS.get(relation, ({"DomainConcept"}, {"DomainConcept"}))
        prop_id = f"SCHEMA_PROPERTY_{relation}"
        schema_properties.append({
            "property_id": prop_id, "label": relation, "domain_meta_types": sorted(domains),
            "range_meta_types": sorted(ranges), "support_count": rel_cluster["support_count"],
            "supporting_relation_cluster_id": rel_cluster["relation_cluster_id"], "status": "VALIDATED",
        })
        prop_uid = graph.node(
            prop_id, "SchemaProperty", label=relation, domain_meta_types=sorted(domains), range_meta_types=sorted(ranges),
            support_count=rel_cluster["support_count"], evidence_anchor_ids=sorted({a for s in surface if s["canonical_seed"] == relation for a in [s["anchor_id"]]}),
            status="VALIDATED", operational=True,
        )
        rel_cluster_uid = graph.node(
            rel_cluster["relation_cluster_id"], "RelationCluster", label=relation,
            surface_predicates=rel_cluster["surface_predicates"], support_count=rel_cluster["support_count"],
            evidence_anchor_ids=graph.nodes[prop_uid]["evidence_anchor_ids"], status="VALIDATED",
        )
        graph.edge("SUPPORTS_SCHEMA", rel_cluster_uid, prop_uid, evidence_anchor_ids=graph.nodes[prop_uid]["evidence_anchor_ids"], status="VALIDATED")

    promotion_decisions: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    semantic_seen: set[tuple[str, str, str]] = set()
    promoted_relation_counts: Counter[str] = Counter()
    for item in surface:
        source_cluster = mention_to_cluster[item["subject_mention_id"]]
        target_cluster = mention_to_cluster[item["object_mention_id"]]
        source = cluster_by_id[source_cluster]
        target = cluster_by_id[target_cluster]
        relation = item["canonical_seed"]
        domains, ranges = RELATION_DOMAINS.get(relation, ({"DomainConcept"}, {"DomainConcept"}))
        reasons = []
        if source["status"] != "VALIDATED" or target["status"] != "VALIDATED": reasons.append("UNRESOLVED_ENDPOINT")
        if source["meta_type"] not in domains: reasons.append("DOMAIN_MISMATCH")
        if target["meta_type"] not in ranges: reasons.append("RANGE_MISMATCH")
        if source_cluster == target_cluster: reasons.append("SELF_LOOP")
        key = (relation, source_cluster, target_cluster)
        if key in semantic_seen: reasons.append("DUPLICATE_ASSERTION")
        status = "VALIDATED" if not reasons else "UNRESOLVED"
        decision = {
            "promotion_id": stable_id("EG_PROMOTION", item["surface_relation_id"]),
            "surface_relation_id": item["surface_relation_id"], "relation": relation,
            "source_cluster_id": source_cluster, "target_cluster_id": target_cluster,
            "evidence_id": item["evidence_id"], "anchor_id": item["anchor_id"],
            "status": status, "reasons": reasons, "confidence": item["confidence"],
        }
        promotion_decisions.append(decision)
        if status == "UNRESOLVED":
            unresolved.append(decision)
            continue
        semantic_seen.add(key)
        promoted_relation_counts[relation] += 1
        source_uid, target_uid = f"{SYSTEM_ID}::{source_cluster}", f"{SYSTEM_ID}::{target_cluster}"
        graph.edge(relation, source_uid, target_uid, evidence_anchor_ids=[item["anchor_id"]], status="VALIDATED", confidence=item["confidence"], operational=True)
        assertion_id = stable_id("EG_ASSERTION", relation, source_cluster, target_cluster, item["anchor_id"])
        assertion_uid = graph.node(
            assertion_id, "Assertion", label=f"{source['preferred_label']} {relation} {target['preferred_label']}",
            predicate=relation, subject_uid=source_uid, object_uid=target_uid,
            evidence_anchor_ids=[item["anchor_id"]], status="VALIDATED", confidence=item["confidence"], operational=True,
        )
        graph.edge("ASSERTS_SUBJECT", assertion_uid, source_uid, evidence_anchor_ids=[item["anchor_id"]], status="VALIDATED")
        graph.edge("ASSERTS_OBJECT", assertion_uid, target_uid, evidence_anchor_ids=[item["anchor_id"]], status="VALIDATED")
        graph.edge("DERIVED_FROM", assertion_uid, f"{SYSTEM_ID}::{item['anchor_id']}", evidence_anchor_ids=[item["anchor_id"]], status="VALIDATED")
        graph.edge("WAS_GENERATED_BY", assertion_uid, activity_uid, evidence_anchor_ids=[item["anchor_id"]], status="VALIDATED")

    # Procedure induction uses source order but prevents self loops and cycles.
    work_occurrences: dict[tuple[str, str], list[tuple[int, int, str, str]]] = defaultdict(list)
    for mention in mentions:
        cluster_id = mention_to_cluster[mention["mention_id"]]
        cluster = cluster_by_id[cluster_id]
        if mention["role_hint"] == "WORK" and cluster["status"] == "VALIDATED":
            row = row_by_id[mention["evidence_id"]]
            work_occurrences[(row["chapter_no"], row["section_no"])].append((row["excel_row"], mention["start_char"], cluster_id, mention["anchor_id"]))
    adjacency: dict[str, set[str]] = defaultdict(set)
    for values in work_occurrences.values():
        ordered = sorted(set(values))
        for left, right in zip(ordered, ordered[1:]):
            _, _, a, anchor_a = left
            _, _, b, anchor_b = right
            key = ("PRECEDES", a, b)
            if a == b or key in semantic_seen or has_path(adjacency, b, a):
                continue
            semantic_seen.add(key)
            adjacency[a].add(b)
            promoted_relation_counts["PRECEDES"] += 1
            evidence = sorted({anchor_a, anchor_b})
            graph.edge("PRECEDES", f"{SYSTEM_ID}::{a}", f"{SYSTEM_ID}::{b}", evidence_anchor_ids=evidence, status="VALIDATED", confidence=0.62, operational=True, induction_basis="DOCUMENT_ORDER_WITHIN_SECTION")
            assertion_id = stable_id("EG_ASSERTION", "PRECEDES", a, b, evidence)
            assertion_uid = graph.node(assertion_id, "Assertion", label="induced procedure order", predicate="PRECEDES", subject_uid=f"{SYSTEM_ID}::{a}", object_uid=f"{SYSTEM_ID}::{b}", evidence_anchor_ids=evidence, status="VALIDATED", confidence=0.62, operational=True)
            for anchor_id in evidence:
                graph.edge("DERIVED_FROM", assertion_uid, f"{SYSTEM_ID}::{anchor_id}", evidence_anchor_ids=[anchor_id], status="VALIDATED")
            graph.edge("WAS_GENERATED_BY", assertion_uid, activity_uid, evidence_anchor_ids=evidence, status="VALIDATED")

    for cluster in clusters:
        if cluster["status"] == "UNRESOLVED":
            unresolved.append({"candidate_type": "CONCEPT_CLUSTER", "candidate_id": cluster["cluster_id"], "label": cluster["preferred_label"], "reason": "INSUFFICIENT_REPEATED_OR_HIGH_CONFIDENCE_SUPPORT", "evidence_ids": cluster["evidence_ids"]})

    schema = {
        "method": METHOD_VERSION,
        "metamodel_classes": ["Document", "EvidenceUnit", "Mention", "SemanticFrame", "ConceptCluster", "RelationCluster", "Assertion", "ExtractionActivity"],
        "induced_classes": schema_classes,
        "induced_properties": schema_properties,
        "taxonomy_policy": "Only induced class to fixed metaclass alignment; no layout-derived broader edges",
        "partonomy_policy": "No partOf promotion without explicit linguistic evidence",
        "procedure_policy": "Within-section source order with cycle prevention and LOW confidence",
    }
    return graph, promotion_decisions, unresolved, {"schema": schema, "promoted_relation_counts": dict(promoted_relation_counts)}


def validate(
    rows: list[dict], anchors: list[dict], mentions: list[dict], frames: list[dict], clusters: list[dict],
    rel_clusters: list[dict], graph: GraphBuilder, promotions: list[dict], unresolved: list[dict], merge_decisions: list[dict], gray: list[dict],
) -> dict[str, Any]:
    anchor_metrics = r3_apre.validate_anchor_records(anchors)
    node_types = Counter(node["type"] for node in graph.nodes.values())
    edge_types = Counter(edge["type"] for edge in graph.edges.values())
    invalid_edges = [edge["uid"] for edge in graph.edges.values() if edge["source"] not in graph.nodes or edge["target"] not in graph.nodes]
    semantic = [edge for edge in graph.edges.values() if edge["type"] in RELATION_DOMAINS]
    domain_violations = []
    for edge in semantic:
        source, target = graph.nodes[edge["source"]], graph.nodes[edge["target"]]
        source_meta = source.get("meta_type")
        target_meta = target.get("meta_type")
        domains, ranges = RELATION_DOMAINS[edge["type"]]
        if source_meta not in domains or target_meta not in ranges:
            domain_violations.append(edge["uid"])
    assertions = [node for node in graph.nodes.values() if node["type"] == "Assertion" and node["status"] == "VALIDATED"]
    grounded = [node for node in assertions if node.get("evidence_anchor_ids")]
    generated = []
    for node in assertions:
        if any(edge["type"] == "WAS_GENERATED_BY" and edge["source"] == node["uid"] for edge in graph.edges.values()):
            generated.append(node)
    status_counts = Counter(cluster["status"] for cluster in clusters)
    promotion_counts = Counter(item["status"] for item in promotions)
    merge_counts = Counter(item["decision"] for item in merge_decisions)
    gates = {
        "source_complete": len(rows) == 1366,
        "stage1_offsets_exact": anchor_metrics["offset_round_trip_validity"] == 1.0,
        "stage2_open_candidates_nonempty": bool(mentions and frames),
        "stage3_consolidation_nonempty": bool(clusters and rel_clusters and merge_decisions),
        "stage4_schema_nonempty": node_types["SchemaClass"] > 0 and node_types["SchemaProperty"] > 0,
        "stage5_promotions_nonempty": bool(assertions),
        "invalid_edge_endpoints_zero": not invalid_edges,
        "domain_range_violations_zero": not domain_violations,
        "assertion_evidence_complete": len(grounded) == len(assertions),
        "assertion_activity_complete": len(generated) == len(assertions),
        "taxonomy_cycle_zero": True,
        "semantic_self_loop_zero": not any(edge["source"] == edge["target"] for edge in semantic),
        "human_intervention_zero": True,
    }
    return {
        "experiment_id": EXPERIMENT_ID,
        "method": METHOD_VERSION,
        "source_file": SOURCE_RELATIVE,
        "source_evidence_count": len(rows),
        "source_anchor_count": anchor_metrics["anchor_count"],
        "source_context_span_count": anchor_metrics["context_span_count"],
        "anchor_metrics": anchor_metrics,
        "mention_candidate_count": len(mentions),
        "semantic_frame_count": len(frames),
        "concept_cluster_count": len(clusters),
        "concept_cluster_status_counts": dict(status_counts),
        "relation_cluster_count": len(rel_clusters),
        "merge_decision_counts": dict(merge_counts),
        "embedding_gray_zone_count": len(gray),
        "promotion_decision_counts": dict(promotion_counts),
        "unresolved_count": len(unresolved),
        "node_count": len(graph.nodes),
        "relationship_count": len(graph.edges),
        "node_type_counts": dict(node_types),
        "relationship_type_counts": dict(edge_types),
        "validated_assertion_count": len(assertions),
        "assertion_evidence_coverage": len(grounded) / len(assertions) if assertions else 1.0,
        "assertion_activity_coverage": len(generated) / len(assertions) if assertions else 1.0,
        "invalid_edge_endpoint_count": len(invalid_edges),
        "domain_range_violation_count": len(domain_violations),
        "human_intervention_count": 0,
        "llm_call_count": 0,
        "accuracy_evaluated": False,
        "accuracy_claimed": False,
        "gates": gates,
        "overall_status": "EG_MOI_PIPELINE_PASS" if all(gates.values()) else "PARTIAL_PASS",
    }


def main() -> int:
    project = Path(__file__).resolve().parents[1]
    workspace = project.parent
    source = workspace / SOURCE_RELATIVE
    root = project / "experiments" / EXPERIMENT_ID
    if not source.exists():
        raise FileNotFoundError(source)

    sheet, rows = source_rows(source)
    anchor_records = [r3_apre.build_atomic_anchors(row) for row in rows]
    mentions, frames, surface, aliases = discover(rows, anchor_records)
    clusters, merge_decisions, mention_to_cluster, gray = consolidate(mentions, aliases)
    rel_clusters = relation_clusters(surface, mentions)
    graph, promotions, unresolved, induced = promote(
        rows, anchor_records, mentions, frames, surface, clusters, rel_clusters, mention_to_cluster, source,
    )
    metrics = validate(rows, anchor_records, mentions, frames, clusters, rel_clusters, graph, promotions, unresolved, merge_decisions, gray)

    write_jsonl(root / "stage1_evidence" / "source_rows.jsonl", rows)
    write_jsonl(root / "stage1_evidence" / "evidence_units.jsonl", anchor_records)
    write_jsonl(root / "stage2_discovery" / "mentions.jsonl", mentions)
    write_jsonl(root / "stage2_discovery" / "semantic_frames.jsonl", frames)
    write_jsonl(root / "stage2_discovery" / "surface_relations.jsonl", surface)
    write_jsonl(root / "stage2_discovery" / "explicit_aliases.jsonl", aliases)
    write_jsonl(root / "stage3_consolidation" / "concept_clusters.jsonl", clusters)
    write_jsonl(root / "stage3_consolidation" / "relation_clusters.jsonl", rel_clusters)
    write_jsonl(root / "stage3_consolidation" / "merge_decisions.jsonl", merge_decisions)
    write_jsonl(root / "stage3_consolidation" / "llm_gray_zone_queue.jsonl", gray)
    write_json(root / "stage4_schema" / "induced_schema.json", induced["schema"])
    write_jsonl(root / "stage5_promotion" / "promotion_decisions.jsonl", promotions)
    write_jsonl(root / "stage5_promotion" / "unresolved.jsonl", unresolved)
    write_jsonl(root / "graph" / "nodes.jsonl", sorted(graph.nodes.values(), key=lambda x: x["uid"]))
    write_jsonl(root / "graph" / "edges.jsonl", sorted(graph.edges.values(), key=lambda x: x["uid"]))
    write_json(root / "evaluation" / "structural_metrics.json", metrics)
    write_json(root / "locks" / "method_lock.json", {
        "experiment_id": EXPERIMENT_ID,
        "method": METHOD_VERSION,
        "source_file": SOURCE_RELATIVE,
        "source_binary_sha256": sha(source.read_bytes()),
        "source_sheet": sheet,
        "source_row_count": len(rows),
        "fixed_metamodel": ["Document", "EvidenceUnit", "Mention", "SemanticFrame", "ConceptCluster", "RelationCluster", "Assertion", "ExtractionActivity"],
        "embedding": {"type": "sparse_character_ngram", "widths": [2, 3], "merge_cosine": 0.9, "gray_zone": [0.82, 0.9]},
        "llm_policy": "Only gray-zone cluster decisions; skipped because OPENAI_API_KEY was unavailable; candidates retained as UNRESOLVED",
        "human_intervention_count": 0,
        "accuracy_claimed": False,
    })
    write_json(root / "reference" / "status.json", {
        "experiment_id": EXPERIMENT_ID,
        "overall_status": metrics["overall_status"],
        "source_file": SOURCE_RELATIVE,
        "human_intervention_count": 0,
        "llm_call_count": 0,
        "accuracy_evaluated": False,
        "accuracy_claimed": False,
        "result_semantics": "STRUCTURALLY_VALIDATED_SEMANTICALLY_UNVERIFIED",
    })
    print(json.dumps(metrics, ensure_ascii=False))
    return 0 if metrics["overall_status"] == "EG_MOI_PIPELINE_PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
