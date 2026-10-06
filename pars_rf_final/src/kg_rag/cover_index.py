"""Direct-support-only PARS-Cover view packages; no API calls or graph writes.

Snapshots represent SUPPORTED_BY/MEMBER_OF by endpoint fields, not edge IDs.
Provenance retains these endpoint/type triples and never invents stored IDs.
An explicit property scope adapter may be passed only after validating the
source schema; unknown multi-support scopes default to exclusion.
"""
from __future__ import annotations

from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
import hashlib
import json
from typing import Mapping

from .retrieval import FACT_RELATION_WEIGHT, MAPPING_RELATION_WEIGHT, QPARetriever

TEMPLATE_VERSION = "pars-cover-direct-views-v1"


def _text(value) -> str:
    return value.strip() if isinstance(value, str) else ""


def _first(properties, *names):
    return next((_text(properties.get(k)) for k in names if _text(properties.get(k))), "")


def edge(source, relation, target):
    return {"source": source, "type": relation, "target": target,
            "origin": "stored_snapshot_endpoint"}


@dataclass(frozen=True)
class PropertyView:
    view_id: str
    evidence_id: str
    node_id: str
    node_type: str
    kind: str
    text: str
    support: dict | None


@dataclass
class EvidencePackage:
    evidence: dict
    views: list[PropertyView] = field(default_factory=list)
    taskframe_ids: set[str] = field(default_factory=set)
    pcf_ids: set[str] = field(default_factory=set)
    context_edges: list[dict] = field(default_factory=list)


@dataclass
class CoverIndex:
    packages: dict[str, EvidencePackage]
    views: list[PropertyView]
    pcf_adjacency: dict[str, set[str]]
    audit: dict

    def pcf_distances(self, start: str) -> dict[str, int]:
        """Actual undirected CHILD_OF distance; disconnected roots stay absent."""
        if start not in self.pcf_adjacency:
            return {}
        distances, queue = {start: 0}, deque([start])
        while queue:
            current = queue.popleft()
            for neighbor in sorted(self.pcf_adjacency[current]):
                if neighbor not in distances:
                    distances[neighbor] = distances[current] + 1
                    queue.append(neighbor)
        return distances


def parse_qualifiers(value, audit: Counter) -> list[dict]:
    if value is None or value == "" or value == [] or value == {}:
        audit["qualifier_empty"] += 1
        return []
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (ValueError, TypeError):
            audit["qualifier_invalid_json"] += 1
            return []
    if value is None or value == [] or value == {}:
        audit["qualifier_empty"] += 1
        return []
    if isinstance(value, dict):
        value = [value]
    if not isinstance(value, list):
        audit["qualifier_invalid_shape"] += 1
        return []
    output = []
    for item in value:
        if not isinstance(item, dict) or not _text(item.get("text")):
            audit["qualifier_invalid_item"] += 1
            continue
        output.append({"type": _text(item.get("type")), "text": _text(item["text"])})
    return output


def build_cover_index(snapshot: Mapping, legacy_index=None, config=None,
                      *, property_scopes: Mapping | None = None) -> CoverIndex:
    """Build raw packages only. Embedding preparation is a separate stage.

    property_scopes: validated adapter output node -> view kind -> Evidence IDs.
    For multi-support nodes, both anchor and dependent view scopes must agree.
    No scope is inferred from matching words or from sibling Fact/Mention links.
    """
    del legacy_index, config  # API compatibility; neither is used as a Gold source.
    audit = Counter()
    details = []
    packages = {}
    all_evidence = set()
    for row in snapshot["evidence_spans"]:
        props = row["properties"]
        eid = props["id"]
        if eid in all_evidence:
            raise ValueError(f"Duplicate Evidence ID: {eid}")
        all_evidence.add(eid)
        if not isinstance(props.get("name"), str) or not props["name"].strip():
            raise ValueError(f"Empty Evidence body requires an explicit policy: {eid}")
        packages[eid] = EvidencePackage(dict(props))
    frames = {r["properties"]["id"] for r in snapshot["taskframes"]}
    pcfs = {r["properties"]["id"] for r in snapshot["pcf_processes"]}
    adjacency = {p: set() for p in pcfs}
    for rel in snapshot["pcf_child_of"]:
        a, b = rel["child_id"], rel["parent_id"]
        if a not in pcfs or b not in pcfs:
            raise ValueError("Unknown CHILD_OF endpoint")
        adjacency[a].add(b)
        adjacency[b].add(a)
    mappings = defaultdict(list)
    for rel in snapshot["pcf_mappings"]:
        if rel["relationship_type"] not in MAPPING_RELATION_WEIGHT:
            continue
        if rel["taskframe_id"] not in frames or rel["pcf_id"] not in pcfs:
            raise ValueError("Unknown PCF mapping endpoint")
        mappings[rel["taskframe_id"]].append(rel)

    def add(eid, node_id, label, kind, text):
        if not text.strip():
            return
        identity = json.dumps([TEMPLATE_VERSION, eid, node_id, kind, text], ensure_ascii=False)
        vid = hashlib.sha256(identity.encode()).hexdigest()
        packages[eid].views.append(PropertyView(
            vid, eid, node_id, label, kind, text,
            None if label == "EvidenceSpan" else edge(node_id, "SUPPORTED_BY", eid)))

    for eid, package in packages.items():
        add(eid, eid, "EvidenceSpan", "evidence_text", package.evidence["name"])

    scopes = property_scopes or {}
    for rows_key, label, allowed in (
        ("facts", "Fact", QPARetriever._allow_v2_fact),
        ("taskmentions", "TaskMention", QPARetriever._allow_v2_taskmention),
    ):
        seen = set()
        for row in snapshot[rows_key]:
            p = row["properties"]
            node_id = p["id"]
            if node_id in seen:
                raise ValueError(f"Duplicate {label}: {node_id}")
            seen.add(node_id)
            eids = sorted(set(row.get("evidence_ids", [])))
            if set(eids) - all_evidence:
                raise ValueError(f"Unknown SUPPORTED_BY target for {node_id}")
            if not allowed(p):
                audit[f"{label}_quality_excluded"] += 1
                continue
            audit[f"{label}_quality_eligible"] += 1
            if label == "Fact":
                links = [(r["taskframe_id"], r["relationship_type"]) for r in row.get("frame_links", [])
                         if r["relationship_type"] in FACT_RELATION_WEIGHT]
            else:
                links = [(row["taskframe_id"], "MEMBER_OF")]
            for tid, relation in links:
                if tid not in frames:
                    raise ValueError(f"Unknown TaskFrame endpoint: {tid}")
                for eid in eids:
                    package = packages[eid]
                    package.taskframe_ids.add(tid)
                    package.context_edges.append(edge(node_id, "SUPPORTED_BY", eid))
                    package.context_edges.append(edge(node_id, relation, tid) if label == "TaskMention"
                                                 else edge(tid, relation, node_id))
                    for mapping in mappings[tid]:
                        pid = mapping["pcf_id"]
                        package.pcf_ids.add(pid)
                        package.context_edges.append(edge(tid, mapping["relationship_type"], pid))

            multi = len(eids) > 1
            if multi:
                audit[f"{label}_multi_support_nodes"] += 1
            qualifier_items = parse_qualifiers(p.get("qualifiers"), audit) if label == "Fact" else []
            excluded_multi = False
            for eid in eids:
                def scoped(kind):
                    return not multi or eid in scopes.get(node_id, {}).get(kind, [])

                if label == "Fact":
                    if not scoped("claim"):
                        excluded_multi = True
                        continue
                    spo = [_first(p, f"{k}_canonical", f"{k}_raw") for k in ("subject", "predicate", "object")]
                    claim = (f"주어: {spo[0]} | 술어: {spo[1]} | 목적어: {spo[2]}" if all(spo)
                             else _first(p, "name", "displayName", "evidence_quote"))
                    if not claim:
                        audit["fact_missing_claim_anchor"] += 1
                        continue
                    add(eid, node_id, label, "claim", claim)
                    if scoped("qualifier"):
                        for i, qualifier in enumerate(qualifier_items):
                            suffix = ((f" | 조건유형: {qualifier['type']}" if qualifier["type"] else "")
                                      + f" | 조건: {qualifier['text']}")
                            add(eid, node_id, label, f"qualifier_{i}", claim + suffix)
                    elif qualifier_items:
                        excluded_multi = True
                    function = _text(p.get("knowledge_function"))
                    if function and scoped("function"):
                        add(eid, node_id, label, "function", claim + f" | 지식기능: {function}")
                    elif function:
                        excluded_multi = True
                else:
                    if not scoped("mention_base"):
                        excluded_multi = True
                        continue
                    identity, action = _first(p, "name", "displayName"), _text(p.get("action_raw"))
                    base = " | ".join(v for v in (f"업무: {identity}" if identity else "",
                                                   f"행위: {action}" if action else "") if v)
                    if not base:
                        audit["mention_missing_anchor"] += 1
                        continue
                    add(eid, node_id, label, "mention_base", base)
                    for kind, key, title in (("object", "focal_object_raw", "대상"),
                                             ("outcome", "intended_outcome_raw", "결과")):
                        text = _text(p.get(key))
                        if text and scoped(kind):
                            add(eid, node_id, label, kind, base + f" | {title}: {text}")
                        elif text:
                            excluded_multi = True
            if excluded_multi:
                audit[f"{label}_multi_support_property_excluded"] += 1
                details.append({"node_id": node_id, "reason": "unresolved_multi_support_property_scope",
                                "evidence_ids": eids})

    for package in packages.values():
        package.views = sorted({v.view_id: v for v in package.views}.values(), key=lambda v: v.view_id)
        unique = {json.dumps(e, sort_keys=True): e for e in package.context_edges}
        package.context_edges = [unique[k] for k in sorted(unique)]
    views = sorted((v for p in packages.values() for v in p.views), key=lambda v: v.view_id)
    return CoverIndex(packages, views, adjacency, {
        "template_version": TEMPLATE_VERSION, "counts": dict(audit),
        "evidence_count": len(packages), "view_count": len(views),
        "unique_embedding_strings": len({v.text for v in views}),
        "text_only_packages": sum(len(p.views) == 1 for p in packages.values()),
        "without_taskframe_context": sum(not p.taskframe_ids for p in packages.values()),
        "view_kinds": dict(Counter(v.kind.split('_')[0] for v in views)),
        "exclusions": details, "embeddings_computed": False,
        "property_scope_adapter": "explicit_validated_mapping" if property_scopes else "none",
    })
