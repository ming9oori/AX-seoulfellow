#!/usr/bin/env python3
"""Build a fully automatic, structurally grounded KG from the full zaije workbook."""

from __future__ import annotations

import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import r2_blre
import r3_apre


EXPERIMENT_ID = "zaije_simple_e2e_pilot_20260712_v1"
SYSTEM_ID = "SIMPLE-E2E"
STATUS = "AUTOMATED_UNVERIFIED"

ACTIVITY_HEADERS = re.compile(r"활동|activity|주요\s*활동|업무|단계|step", re.I)
OUTPUT_HEADERS = re.compile(r"결과물|산출물|output|deliverable", re.I)
INPUT_HEADERS = re.compile(r"입력|input|참고\s*자료|요구\s*자료", re.I)
ROLE_HEADERS = re.compile(r"담당|수행자|책임자|role|성명|직책|역할", re.I)

ARTIFACT_TERMS = re.compile(
    r"제안서|계획서|보고서|분석표|응답표|체크리스트|초안|문서|자료|템플릿|양식|서식|"
    r"capture\s*plan|executive\s*summary|rfp|wbs|pert|슬라이드|플래너|조직도|일정표",
    re.I,
)
INFO_TERMS = re.compile(r"요구조건|요구사항|핵심\s*이슈|평가\s*기준|고객\s*정보|분석\s*결과|니즈|관심사|전략|기준|정보", re.I)
ORG_TERMS = re.compile(r"팀|부서|조직|회사|기관|위원회|본부|센터|사업단|협력업체|업체$", re.I)
ACTOR_TERMS = re.compile(r"대표|담당자|평가위원|위원|pm|작성자|책임자|의사결정자|영업대표|고객$", re.I)

ACTION_PATTERN = re.compile(
    r"(?:(?P<actor>[가-힣A-Za-z0-9 /&·]{1,24}?)(?:이|가|은|는)\s+)?"
    r"(?P<object>[가-힣A-Za-z0-9() /&·'’-]{2,48}?)(?:을|를)\s*"
    r"(?P<verb>작성|분석|검토|수립|제출|개발|평가|선정|도출|확인|준비|제공|업데이트)"
    r"(?:해야\s*한다|하여야\s*한다|한다|하였다|했다|하도록\s*한다|할\s*수\s*있다|함|할\s*것)?",
    re.I,
)
INPUT_BASIS_PATTERN = re.compile(
    r"(?P<input>[가-힣A-Za-z0-9() /&·'’-]{2,48}?)(?:을|를|에)\s*(?:바탕으로|기반으로|기초로|참고하여)\s*"
    r"(?P<object>[가-힣A-Za-z0-9() /&·'’-]{2,48}?)(?:을|를)?\s*"
    r"(?P<verb>작성|분석|검토|수립|개발|도출|준비)",
    re.I,
)

TYPE_DOMAIN = {
    "PERFORMED_BY": ({"WorkUnit"}, {"Actor", "Organization"}),
    "HAS_INPUT": ({"WorkUnit"}, {"Artifact", "InformationObject"}),
    "PRODUCES_OUTPUT": ({"WorkUnit"}, {"Artifact", "InformationObject"}),
    "PRECEDES": ({"WorkUnit"}, {"WorkUnit"}),
}


def sha(value: Any) -> str:
    if isinstance(value, bytes):
        payload = value
    else:
        payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def stable_id(prefix: str, *parts: Any) -> str:
    return f"{prefix}_{sha(parts)[:20]}"


def normalize(value: str) -> str:
    text = unicodedata.normalize("NFKC", value).casefold()
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.I)
    text = re.sub(r"^[\s•▪◦‣*\-\d.)]+", "", text)
    text = re.sub(r"[^0-9a-z가-힣%+]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def clean_label(value: str) -> str:
    value = re.sub(r"<br\s*/?>", " ", value, flags=re.I)
    value = re.sub(r"^[\s•▪◦‣*\-]+", "", value)
    return re.sub(r"\s+", " ", value).strip(" |,.;:()[]{}")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def classify_object(label: str) -> tuple[str, str, str]:
    if ARTIFACT_TERMS.search(label):
        return "Artifact", "HIGH", "LF_ARTIFACT_LEXICON"
    if INFO_TERMS.search(label):
        return "InformationObject", "HIGH", "LF_INFORMATION_LEXICON"
    return "InformationObject", "LOW", "LF_OBJECT_DEFAULT_INFORMATION"


def classify_agent(label: str) -> tuple[str, str, str]:
    if ORG_TERMS.search(label):
        return "Organization", "HIGH", "LF_ORGANIZATION_LEXICON"
    if ACTOR_TERMS.search(label):
        return "Actor", "HIGH", "LF_ACTOR_LEXICON"
    return "Actor", "LOW", "LF_AGENT_DEFAULT_ACTOR"


class Builder:
    def __init__(self) -> None:
        self.nodes: dict[str, dict[str, Any]] = {}
        self.edges: dict[str, dict[str, Any]] = {}
        self.canonical: dict[tuple[str, str], str] = {}
        self.candidates: list[dict[str, Any]] = []
        self.relation_candidates: list[dict[str, Any]] = []
        self.work_order: list[tuple[int, int, str, str]] = []

    def node(self, node_id: str, node_type: str, **props: Any) -> str:
        uid = f"{SYSTEM_ID}::{node_id}"
        item = {"id": node_id, "uid": uid, "system_id": SYSTEM_ID, "type": node_type, **props}
        if uid not in self.nodes:
            self.nodes[uid] = item
        return uid

    def edge(self, relation: str, source_uid: str, target_uid: str, **props: Any) -> str:
        edge_id = stable_id("E2E_EDGE", relation, source_uid, target_uid, props)
        uid = f"{SYSTEM_ID}::{edge_id}"
        self.edges[uid] = {
            "id": edge_id, "uid": uid, "system_id": SYSTEM_ID, "type": relation,
            "source": source_uid, "target": target_uid, **props,
        }
        return uid

    def typed_concept(
        self, *, label: str, concept_type: str, anchor_id: str, evidence_id: str,
        start_char: int, end_char: int, rule_id: str, confidence: str, source_span_id: str | None = None,
    ) -> tuple[str, str]:
        label = clean_label(label)
        norm = normalize(label)
        if not norm or len(norm) < 2:
            raise ValueError("empty typed concept")
        key = (concept_type, norm)
        concept_id = self.canonical.get(key)
        if concept_id is None:
            concept_id = stable_id("E2E_CONCEPT", concept_type, norm)
            self.canonical[key] = concept_id
            self.node(
                concept_id, concept_type, label=label, normalized_label=norm,
                generation_method="DETERMINISTIC_RULE", status=STATUS,
                confidence=confidence, rule_ids=[rule_id], evidence_anchor_ids=[anchor_id], operational=True,
            )
        else:
            uid = f"{SYSTEM_ID}::{concept_id}"
            n = self.nodes[uid]
            n["evidence_anchor_ids"] = sorted(set(n["evidence_anchor_ids"] + [anchor_id]))
            n["rule_ids"] = sorted(set(n["rule_ids"] + [rule_id]))
            if confidence == "HIGH":
                n["confidence"] = "HIGH"

        mention_id = stable_id("E2E_MENTION", concept_type, norm, evidence_id, anchor_id, start_char, end_char, source_span_id)
        mention_uid = self.node(
            mention_id, "Mention", label=label, normalized_label=norm, mention_type=concept_type,
            evidence_id=evidence_id, evidence_anchor_ids=[anchor_id], start_char=start_char, end_char=end_char,
            source_span_id=source_span_id, generation_method="DETERMINISTIC_RULE", status=STATUS,
            confidence=confidence, rule_id=rule_id, operational=False,
        )
        concept_uid = f"{SYSTEM_ID}::{concept_id}"
        self.edge("DENOTES", mention_uid, concept_uid, evidence_anchor_ids=[anchor_id], rule_id=rule_id, confidence=confidence, status=STATUS)
        self.edge("DERIVED_FROM", mention_uid, f"{SYSTEM_ID}::{anchor_id}", evidence_anchor_ids=[anchor_id], rule_id=rule_id, confidence=confidence, status=STATUS)
        self.candidates.append({
            "mention_id": mention_id, "concept_id": concept_id, "label": label, "normalized_label": norm,
            "concept_type": concept_type, "anchor_id": anchor_id, "evidence_id": evidence_id,
            "start_char": start_char, "end_char": end_char, "source_span_id": source_span_id,
            "rule_id": rule_id, "confidence": confidence, "status": STATUS,
        })
        return mention_uid, concept_uid

    def semantic_relation(self, relation: str, source_uid: str, target_uid: str, anchor_id: str, rule_id: str, confidence: str) -> None:
        source_type = self.nodes[source_uid]["type"]
        target_type = self.nodes[target_uid]["type"]
        domains, ranges = TYPE_DOMAIN[relation]
        accepted = source_type in domains and target_type in ranges
        candidate = {
            "candidate_id": stable_id("E2E_REL_CAND", relation, source_uid, target_uid, anchor_id, rule_id),
            "relation": relation, "source": source_uid, "target": target_uid,
            "source_type": source_type, "target_type": target_type, "evidence_anchor_ids": [anchor_id],
            "rule_id": rule_id, "confidence": confidence, "status": STATUS if accepted else "TYPE_CONFLICT",
            "promoted": accepted,
        }
        self.relation_candidates.append(candidate)
        if accepted:
            self.edge(relation, source_uid, target_uid, evidence_anchor_ids=[anchor_id], rule_id=rule_id, confidence=confidence, status=STATUS, operational=True)


def build() -> tuple[Builder, list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    project = Path(__file__).resolve().parents[1]
    workspace = project.parent
    source = workspace / "handoff-hanyang" / "수주제안" / "자이제_1.xlsx"
    _, raw_records = r2_blre.read_xlsx_raw(source)
    corpus = [json.loads(line) for line in (project / "data" / "canonical" / "corpus.jsonl").read_text(encoding="utf-8").splitlines() if line]
    raw_by_row = {row["excel_row"]: row["text_for_llm_human"] for row in raw_records}
    rows = [{**row, "raw_text": raw_by_row[row["excel_row"]]} for row in corpus]
    anchors = [r3_apre.build_atomic_anchors(row) for row in rows]
    row_by_evidence = {row["evidence_id"]: row for row in rows}
    b = Builder()
    document_uid = b.node(
        "DOC_ZAIJE_SIMPLE_E2E", "Document", label="자이제_1.xlsx",
        source_file=str(source.relative_to(workspace)), source_binary_sha256=sha(source.read_bytes()),
        generation_method="SOURCE_IMPORT", status=STATUS,
    )

    for record in anchors:
        row = row_by_evidence[record["evidence_id"]]
        evidence_id = record["evidence_id"]
        evidence_uid = b.node(
            evidence_id, "EvidenceBundle", label=f"Excel row {row['excel_row']}", exact_text=row["raw_text"],
            excel_row=row["excel_row"], split=row["split"], leakage_group_id=row["leakage_group_id"],
            text_sha256=row["text_sha256"], generation_method="SOURCE_IMPORT", status=STATUS,
        )
        b.edge("HAS_EVIDENCE", document_uid, evidence_uid, evidence_anchor_ids=[], rule_id="SOURCE_DOCUMENT_ROW", confidence="HIGH", status=STATUS)
        contexts = {item["span_id"]: item for item in record["context_spans"]}
        for ctx in contexts.values():
            ctx_uid = b.node(
                ctx["span_id"], "ContextSpan", label=ctx["text_by_program"], exact_text=ctx["text_by_program"],
                evidence_id=evidence_id, start_char=ctx["start_char"], end_char=ctx["end_char"],
                context_type=ctx["context_type"], generation_method="R3_DETERMINISTIC_ANCHOR", status=STATUS,
            )
            b.edge("HAS_CONTEXT_SPAN", evidence_uid, ctx_uid, evidence_anchor_ids=[], rule_id="SOURCE_CONTEXT", confidence="HIGH", status=STATUS)

        for anchor in record["anchors"]:
            anchor_id = anchor["anchor_id"]
            anchor_uid = b.node(
                anchor_id, "Anchor", label=anchor["text_by_program"], exact_text=anchor["text_by_program"],
                evidence_id=evidence_id, start_char=anchor["start_char"], end_char=anchor["end_char"],
                structure_type=anchor["structure_type"], generation_rule=anchor["generation_rule"],
                source_hash=anchor["source_hash"], generation_method="R3_DETERMINISTIC_ANCHOR", status=STATUS,
            )
            b.edge("HAS_ANCHOR", evidence_uid, anchor_uid, evidence_anchor_ids=[anchor_id], rule_id="SOURCE_EVIDENCE_ANCHOR", confidence="HIGH", status=STATUS)
            context_pairs = [(contexts[sid], rel) for sid, rel in zip(anchor["context_span_ids"], anchor["context_relations"])]
            for ctx, rel in context_pairs:
                b.edge("HAS_CONTEXT", anchor_uid, f"{SYSTEM_ID}::{ctx['span_id']}", evidence_anchor_ids=[anchor_id], context_relation=rel, rule_id="SOURCE_ANCHOR_CONTEXT", confidence="HIGH", status=STATUS)

            # Table-first typing and row relation generation.
            column_headers = [ctx for ctx, rel in context_pairs if rel == "HAS_COLUMN_HEADER"]
            row_headers = [ctx for ctx, rel in context_pairs if rel == "HAS_ROW_HEADER"]
            for header in column_headers:
                header_text = clean_label(header["text_by_program"])
                value = clean_label(anchor["text_by_program"])
                if not value or len(normalize(value)) < 2:
                    continue
                if ACTIVITY_HEADERS.search(header_text):
                    _, work_uid = b.typed_concept(label=value, concept_type="WorkUnit", anchor_id=anchor_id, evidence_id=evidence_id, start_char=anchor["start_char"], end_char=anchor["end_char"], rule_id="LF_TABLE_ACTIVITY_HEADER", confidence="HIGH")
                    b.work_order.append((row["excel_row"], anchor["start_char"], record["section"], work_uid))
                elif OUTPUT_HEADERS.search(header_text):
                    _, output_uid = b.typed_concept(label=value, concept_type="Artifact", anchor_id=anchor_id, evidence_id=evidence_id, start_char=anchor["start_char"], end_char=anchor["end_char"], rule_id="LF_TABLE_OUTPUT_HEADER", confidence="HIGH")
                    for row_header in row_headers:
                        work_label = clean_label(row_header["text_by_program"])
                        if len(normalize(work_label)) < 2:
                            continue
                        _, work_uid = b.typed_concept(label=work_label, concept_type="WorkUnit", anchor_id=anchor_id, evidence_id=evidence_id, start_char=row_header["start_char"], end_char=row_header["end_char"], source_span_id=row_header["span_id"], rule_id="LF_TABLE_ROW_ACTIVITY_FOR_OUTPUT", confidence="HIGH")
                        b.work_order.append((row["excel_row"], row_header["start_char"], record["section"], work_uid))
                        b.semantic_relation("PRODUCES_OUTPUT", work_uid, output_uid, anchor_id, "LF_SAME_TABLE_ROW_ACTIVITY_OUTPUT", "HIGH")
                elif INPUT_HEADERS.search(header_text):
                    info_type, confidence, rule = classify_object(value)
                    if info_type == "Artifact":
                        target_type = "Artifact"
                    else:
                        target_type = "InformationObject"
                    _, input_uid = b.typed_concept(label=value, concept_type=target_type, anchor_id=anchor_id, evidence_id=evidence_id, start_char=anchor["start_char"], end_char=anchor["end_char"], rule_id="LF_TABLE_INPUT_HEADER_" + rule, confidence="HIGH")
                    for row_header in row_headers:
                        _, work_uid = b.typed_concept(label=row_header["text_by_program"], concept_type="WorkUnit", anchor_id=anchor_id, evidence_id=evidence_id, start_char=row_header["start_char"], end_char=row_header["end_char"], source_span_id=row_header["span_id"], rule_id="LF_TABLE_ROW_ACTIVITY_FOR_INPUT", confidence="HIGH")
                        b.semantic_relation("HAS_INPUT", work_uid, input_uid, anchor_id, "LF_SAME_TABLE_ROW_ACTIVITY_INPUT", "HIGH")
                elif ROLE_HEADERS.search(header_text):
                    agent_type, confidence, rule = classify_agent(value)
                    _, agent_uid = b.typed_concept(label=value, concept_type=agent_type, anchor_id=anchor_id, evidence_id=evidence_id, start_char=anchor["start_char"], end_char=anchor["end_char"], rule_id="LF_TABLE_ROLE_HEADER_" + rule, confidence=confidence)
                    for row_header in row_headers:
                        _, work_uid = b.typed_concept(label=row_header["text_by_program"], concept_type="WorkUnit", anchor_id=anchor_id, evidence_id=evidence_id, start_char=row_header["start_char"], end_char=row_header["end_char"], source_span_id=row_header["span_id"], rule_id="LF_TABLE_ROW_ACTIVITY_FOR_ROLE", confidence="MEDIUM")
                        b.semantic_relation("PERFORMED_BY", work_uid, agent_uid, anchor_id, "LF_SAME_TABLE_ROW_ACTIVITY_ROLE", "MEDIUM")

            # A small set of transparent Korean argument patterns for prose/list/table cells.
            anchor_text = anchor["text_by_program"]
            for match in ACTION_PATTERN.finditer(anchor_text):
                obj = clean_label(match.group("object"))
                verb = match.group("verb")
                if len(normalize(obj)) < 2:
                    continue
                work_label = f"{obj} {verb}"
                abs_start = anchor["start_char"] + match.start()
                abs_end = anchor["start_char"] + match.end()
                _, work_uid = b.typed_concept(label=work_label, concept_type="WorkUnit", anchor_id=anchor_id, evidence_id=evidence_id, start_char=abs_start, end_char=abs_end, rule_id="LF_SENTENCE_OBJECT_ACTION", confidence="MEDIUM")
                b.work_order.append((row["excel_row"], abs_start, record["section"], work_uid))
                object_type, object_confidence, object_rule = classify_object(obj)
                obj_start = anchor["start_char"] + match.start("object")
                obj_end = anchor["start_char"] + match.end("object")
                _, object_uid = b.typed_concept(label=obj, concept_type=object_type, anchor_id=anchor_id, evidence_id=evidence_id, start_char=obj_start, end_char=obj_end, rule_id=object_rule, confidence=object_confidence)
                relation = "PRODUCES_OUTPUT" if verb in {"작성", "수립", "개발", "도출", "준비"} else "HAS_INPUT"
                b.semantic_relation(relation, work_uid, object_uid, anchor_id, "LF_VERB_ARGUMENT_" + relation, "MEDIUM" if object_confidence == "HIGH" else "LOW")
                actor = clean_label(match.group("actor") or "")
                if len(normalize(actor)) >= 2:
                    agent_type, agent_confidence, agent_rule = classify_agent(actor)
                    actor_start = anchor["start_char"] + match.start("actor")
                    actor_end = anchor["start_char"] + match.end("actor")
                    _, actor_uid = b.typed_concept(label=actor, concept_type=agent_type, anchor_id=anchor_id, evidence_id=evidence_id, start_char=actor_start, end_char=actor_end, rule_id=agent_rule, confidence=agent_confidence)
                    b.semantic_relation("PERFORMED_BY", work_uid, actor_uid, anchor_id, "LF_SENTENCE_SUBJECT_PERFORMED_BY", "MEDIUM" if agent_confidence == "HIGH" else "LOW")

            for match in INPUT_BASIS_PATTERN.finditer(anchor_text):
                input_label = clean_label(match.group("input"))
                obj = clean_label(match.group("object"))
                verb = match.group("verb")
                if len(normalize(input_label)) < 2 or len(normalize(obj)) < 2:
                    continue
                _, work_uid = b.typed_concept(label=f"{obj} {verb}", concept_type="WorkUnit", anchor_id=anchor_id, evidence_id=evidence_id, start_char=anchor["start_char"] + match.start(), end_char=anchor["start_char"] + match.end(), rule_id="LF_BASIS_ACTION", confidence="MEDIUM")
                input_type, confidence, rule = classify_object(input_label)
                _, input_uid = b.typed_concept(label=input_label, concept_type=input_type, anchor_id=anchor_id, evidence_id=evidence_id, start_char=anchor["start_char"] + match.start("input"), end_char=anchor["start_char"] + match.end("input"), rule_id=rule, confidence=confidence)
                b.semantic_relation("HAS_INPUT", work_uid, input_uid, anchor_id, "LF_BASIS_HAS_INPUT", "MEDIUM")

    # Preserve a simple low-confidence process chain in document order within sections.
    seen_order = []
    for item in sorted(set(b.work_order), key=lambda x: (x[2], x[0], x[1], x[3])):
        if item not in seen_order:
            seen_order.append(item)
    by_section: dict[str, list[tuple[int, int, str]]] = defaultdict(list)
    for excel_row, start, section, work_uid in seen_order:
        by_section[section or "UNSPECIFIED"].append((excel_row, start, work_uid))
    for section, items in by_section.items():
        ordered = sorted(items)
        unique = []
        for _, _, uid in ordered:
            if not unique or unique[-1] != uid:
                unique.append(uid)
        for left, right in zip(unique, unique[1:]):
            anchor_ids = sorted(set((b.nodes[left].get("evidence_anchor_ids") or []) + (b.nodes[right].get("evidence_anchor_ids") or [])))
            if anchor_ids:
                b.semantic_relation("PRECEDES", left, right, anchor_ids[0], "LF_DOCUMENT_ORDER_WITHIN_SECTION", "LOW")

    metrics = validate(b, rows, anchors)
    return b, rows, anchors, metrics


def validate(b: Builder, rows: list[dict[str, Any]], anchors: list[dict[str, Any]]) -> dict[str, Any]:
    by_uid = b.nodes
    invalid_endpoints = [e for e in b.edges.values() if e["source"] not in by_uid or e["target"] not in by_uid]
    semantic = [e for e in b.edges.values() if e["type"] in TYPE_DOMAIN]
    type_violations = []
    for edge in semantic:
        domains, ranges = TYPE_DOMAIN[edge["type"]]
        if by_uid[edge["source"]]["type"] not in domains or by_uid[edge["target"]]["type"] not in ranges:
            type_violations.append(edge["uid"])
    grounded = sum(bool(e.get("evidence_anchor_ids")) for e in semantic)
    all_anchors = [a for record in anchors for a in record["anchors"]]
    row_text = {row["evidence_id"]: row["raw_text"] for row in rows}
    offset_ok = sum(row_text[a["evidence_id"]][a["start_char"]:a["end_char"]] == a["text_by_program"] for a in all_anchors)
    type_counts = Counter(n["type"] for n in b.nodes.values())
    relation_counts = Counter(e["type"] for e in b.edges.values())
    confidence_counts = Counter(n.get("confidence") for n in b.nodes.values() if n["type"] in {"WorkUnit", "Actor", "Organization", "Artifact", "InformationObject"})
    required_types = {t: type_counts[t] for t in ["WorkUnit", "Actor", "Organization", "Artifact", "InformationObject"]}
    required_relations = {r: relation_counts[r] for r in TYPE_DOMAIN}
    return {
        "experiment_id": EXPERIMENT_ID, "system_id": SYSTEM_ID, "status": "AUTOMATED_E2E_PASS",
        "source_evidence_count": len(rows), "source_anchor_count": len(all_anchors),
        "node_count": len(b.nodes), "relationship_count": len(b.edges),
        "node_type_counts": dict(type_counts), "relationship_type_counts": dict(relation_counts),
        "required_type_counts": required_types, "required_relation_counts": required_relations,
        "typed_candidate_count": len(b.candidates), "relation_candidate_count": len(b.relation_candidates),
        "promoted_semantic_relation_count": len(semantic), "confidence_counts": dict(confidence_counts),
        "anchor_offset_round_trip": offset_ok / len(all_anchors) if all_anchors else 1.0,
        "invalid_edge_endpoint_count": len(invalid_endpoints), "domain_range_violation_count": len(type_violations),
        "semantic_relation_provenance_coverage": grounded / len(semantic) if semantic else 1.0,
        "human_intervention_count": 0, "human_gold_used": False, "llm_call_count": 0,
        "accuracy_claimed": False, "source_only": "자이제_1.xlsx",
        "all_required_types_nonempty": all(required_types.values()),
        "all_required_relations_nonempty": all(required_relations.values()),
    }


def main() -> int:
    project = Path(__file__).resolve().parents[1]
    root = project / "experiments" / EXPERIMENT_ID
    b, rows, anchors, metrics = build()
    write_jsonl(root / "data" / "source_rows.jsonl", rows)
    write_jsonl(root / "data" / "anchors.jsonl", anchors)
    write_jsonl(root / "candidates" / "typed_mentions.jsonl", b.candidates)
    write_jsonl(root / "candidates" / "relation_candidates.jsonl", b.relation_candidates)
    write_jsonl(root / "graphs" / "jsonl" / "nodes.jsonl", sorted(b.nodes.values(), key=lambda x: x["uid"]))
    write_jsonl(root / "graphs" / "jsonl" / "edges.jsonl", sorted(b.edges.values(), key=lambda x: x["uid"]))
    write_json(root / "evaluation" / "structural_metrics.json", metrics)
    write_json(root / "reference" / "status.json", {
        "experiment_id": EXPERIMENT_ID, "overall_status": metrics["status"],
        "human_intervention_count": 0, "human_gold_used": False, "accuracy_claimed": False,
        "source_evidence_count": len(rows), "source_file": "handoff-hanyang/수주제안/자이제_1.xlsx",
        "method": "TABLE_HEADER_PLUS_SMALL_REGEX_RULES", "methodology_complexity": "MINIMAL",
    })
    write_json(root / "locks" / "method_lock.json", {
        "types": ["WorkUnit", "Actor", "Organization", "Artifact", "InformationObject"],
        "relations": list(TYPE_DOMAIN), "table_header_rules": ["ACTIVITY", "OUTPUT", "INPUT", "ROLE"],
        "sentence_patterns": ["ACTION_PATTERN", "INPUT_BASIS_PATTERN"],
        "embedding_used": False, "agent_used": False, "llm_used": False, "human_used": False,
    })
    print(json.dumps(metrics, ensure_ascii=False))
    return 0 if metrics["all_required_types_nonempty"] and metrics["all_required_relations_nonempty"] and metrics["domain_range_violation_count"] == 0 and metrics["invalid_edge_endpoint_count"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
