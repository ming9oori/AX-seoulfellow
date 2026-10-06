from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
from kiwipiepy import Kiwi

from .common import compact_join, normalize_text, parse_jsonish
from .openai_backend import OpenAIBackend
from .unsupervised_aspects import (
    P1B_PROFILE_FREE,
    P1G_PCF_GROUNDED,
    P1G_PROFILE_FREE,
    P1P_PARS,
    P1P_PARS_PROFILE_FREE,
    P1U_ATTENTION_SEEKER,
    UNSUPERVISED_ASPECT_METHODS,
)


METHODS = (
    "B0_VANILLA_DENSE_RAG",
    "B0_EVIDENCE_HYBRID",
    "P0_QPA",
    "A1_FIXED_PROPERTIES",
    "A2_NO_GAP_ADAPTATION",
    "V2_EVIDENCE_GRAPH_LATE_FUSION",
    "P1_QPA_CROSS_ENCODER_MMR",
    "P1A_QPA_ASPECT_CROSS_ENCODER_MMR",
    P1B_PROFILE_FREE,
    P1G_PROFILE_FREE,
    P1P_PARS,
    P1P_PARS_PROFILE_FREE,
    *UNSUPERVISED_ASPECT_METHODS,
)
CONDITIONS = ("D0_ORIGINAL", "D1_PROPERTY_MASK")
ASPECT_METHODS = (
    "P1A_QPA_ASPECT_CROSS_ENCODER_MMR",
    P1G_PROFILE_FREE,
    P1P_PARS,
    P1P_PARS_PROFILE_FREE,
    *UNSUPERVISED_ASPECT_METHODS,
)
P1_RERANK_METHODS = (
    "P1_QPA_CROSS_ENCODER_MMR",
    P1B_PROFILE_FREE,
    *ASPECT_METHODS,
)

# Evidence-only baselines and the final P1-PARS variant never consume a
# Query Profile.  The legacy P1-PARS ID remains profile-aware solely so its
# published run can be reproduced without silently changing the algorithm.
PROFILE_FREE_METHODS = (
    "B0_VANILLA_DENSE_RAG",
    "B0_EVIDENCE_HYBRID",
    P1B_PROFILE_FREE,
    P1G_PROFILE_FREE,
    P1P_PARS_PROFILE_FREE,
)
QUERY_PROFILE_METHODS = tuple(
    method for method in METHODS if method not in PROFILE_FREE_METHODS
)
FIXED_PROPERTY_METHODS = (
    "A1_FIXED_PROPERTIES",
    P1B_PROFILE_FREE,
    P1G_PROFILE_FREE,
    P1P_PARS_PROFILE_FREE,
)

PROFILE_FREE_ASPECT_METHODS = (
    P1G_PROFILE_FREE,
    P1P_PARS_PROFILE_FREE,
)

MAPPING_RELATION_WEIGHT = {
    "MAPS_TO_PCF": 1.0,
    "ALSO_MAPS_TO_PCF": 0.85,
    "HAS_PCF_CONTEXT": 0.70,
}
FACT_RELATION_WEIGHT = {
    "HAS_CORE_FACT": 1.0,
    "HAS_SUPPORTING_FACT": 0.90,
    "HAS_CONTEXT_FACT": 0.72,
}


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _property(properties: Mapping[str, Any], *names: str) -> str:
    return compact_join(properties.get(name) for name in names)


def _qualifier_text(value: Any) -> str:
    parsed = parse_jsonish(value, value)
    if isinstance(parsed, dict):
        parts: list[str] = []
        for key, item in parsed.items():
            if isinstance(item, list):
                item_text = compact_join(item, ", ")
            else:
                item_text = normalize_text(item)
            if item_text:
                parts.append(f"{key}: {item_text}")
        return " | ".join(parts)
    if isinstance(parsed, list):
        return compact_join(parsed)
    return normalize_text(parsed)


class BM25:
    def __init__(self, documents: Sequence[Sequence[str]], *, k1: float = 1.5, b: float = 0.75):
        self.documents = [list(document) for document in documents]
        self.k1 = k1
        self.b = b
        self.lengths = np.asarray([len(document) for document in self.documents], dtype=np.float32)
        self.avg_length = float(self.lengths.mean()) if len(self.lengths) else 1.0
        self.frequencies = [Counter(document) for document in self.documents]
        document_frequency: Counter[str] = Counter()
        for frequency in self.frequencies:
            document_frequency.update(frequency.keys())
        count = max(1, len(self.documents))
        self.idf = {
            token: math.log(1.0 + (count - frequency + 0.5) / (frequency + 0.5))
            for token, frequency in document_frequency.items()
        }

    def scores(self, query_tokens: Sequence[str]) -> np.ndarray:
        scores = np.zeros(len(self.documents), dtype=np.float32)
        for token in set(query_tokens):
            idf = self.idf.get(token)
            if idf is None:
                continue
            for index, frequency in enumerate(self.frequencies):
                count = frequency.get(token, 0)
                if not count:
                    continue
                denominator = count + self.k1 * (
                    1.0 - self.b + self.b * self.lengths[index] / max(self.avg_length, 1e-6)
                )
                scores[index] += idf * (count * (self.k1 + 1.0)) / denominator
        maximum = float(scores.max()) if len(scores) else 0.0
        return scores / maximum if maximum > 0 else scores


@dataclass
class GroupIndex:
    ids: list[str]
    matrices: dict[str, np.ndarray]
    available: dict[str, np.ndarray]


@dataclass(frozen=True)
class StoredGraphEdge:
    edge_id: str
    source: str
    relation: str
    target: str
    semantic_text: str


class GraphIndex:
    def __init__(
        self,
        snapshot: dict[str, Any],
        backend: OpenAIBackend,
        *,
        embedding_batch_size: int = 64,
    ) -> None:
        self.snapshot = snapshot
        self.backend = backend
        self.embedding_batch_size = embedding_batch_size
        self.kiwi = Kiwi()

        self.pcfs = {
            row["properties"]["id"]: row["properties"]
            for row in snapshot["pcf_processes"]
        }
        self.taskframes = {
            row["properties"]["id"]: {
                **row["properties"],
                "_aliases": row.get("aliases", []),
            }
            for row in snapshot["taskframes"]
        }
        self.taskmentions = {
            row["properties"]["id"]: {
                **row["properties"],
                "_taskframe_id": row["taskframe_id"],
                "_evidence_ids": row.get("evidence_ids", []),
            }
            for row in snapshot["taskmentions"]
        }
        self.facts = {
            row["properties"]["id"]: {
                **row["properties"],
                "_frame_links": row.get("frame_links", []),
                "_taskmention_links": row.get("taskmention_links", []),
                "_evidence_ids": row.get("evidence_ids", []),
            }
            for row in snapshot["facts"]
        }
        self.evidence = {
            row["properties"]["id"]: {
                **row["properties"],
                "_sections": row.get("sections", []),
            }
            for row in snapshot["evidence_spans"]
        }
        self.mappings = snapshot["pcf_mappings"]

        self.parent_by_child = {
            edge["child_id"]: edge["parent_id"] for edge in snapshot["pcf_child_of"]
        }
        self.pcf_path_ids = {
            pcf_id: [item["id"] for item in properties.get("computed_path", [])]
            for pcf_id, properties in self.pcfs.items()
        }
        self.mappings_by_tf: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.mappings_by_pcf: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for mapping in self.mappings:
            self.mappings_by_tf[mapping["taskframe_id"]].append(mapping)
            self.mappings_by_pcf[mapping["pcf_id"]].append(mapping)

        self.tm_by_frame: dict[str, list[str]] = defaultdict(list)
        for mention_id, mention in self.taskmentions.items():
            self.tm_by_frame[mention["_taskframe_id"]].append(mention_id)

        self.fact_by_frame: dict[str, list[tuple[str, dict[str, Any]]]] = defaultdict(list)
        for fact_id, fact in self.facts.items():
            for link in fact["_frame_links"]:
                taskframe_id = link.get("taskframe_id")
                if taskframe_id:
                    self.fact_by_frame[taskframe_id].append((fact_id, link))

        self._group_texts = self._make_group_texts()
        self.indices: dict[str, GroupIndex] = {}
        self._build_embedding_indices()
        self._question_vectors: dict[str, np.ndarray] = {}
        self._dense_scores: dict[str, dict[str, float]] = {}
        self._hybrid_scores: dict[str, dict[str, float]] = {}

        evidence_ids = list(self.evidence)
        evidence_documents = [self._tokens(self.evidence[item].get("name", "")) for item in evidence_ids]
        self.evidence_bm25_ids = evidence_ids
        self.evidence_bm25 = BM25(evidence_documents)
        self._build_property_relational_graph()

    def _tokens(self, text: str) -> list[str]:
        return [token.form.lower() for token in self.kiwi.tokenize(normalize_text(text)) if token.form]

    def _representative_frame_evidence(self, frame_id: str, limit: int = 4) -> str:
        values: list[str] = []
        ranked = sorted(
            self.fact_by_frame.get(frame_id, []),
            key=lambda item: -FACT_RELATION_WEIGHT.get(
                item[1].get("relationship_type", ""), 0.5
            ),
        )
        for fact_id, _ in ranked:
            text = normalize_text(self.facts[fact_id].get("evidence_quote"))
            if text and text not in values:
                values.append(text)
            if len(values) >= limit:
                break
        return " ".join(values)

    def _make_group_texts(self) -> dict[str, dict[str, dict[str, str]]]:
        result: dict[str, dict[str, dict[str, str]]] = {
            "pcf": {},
            "taskframe": {},
            "taskmention": {},
            "fact": {},
            "evidence": {},
        }
        for node_id, node in self.pcfs.items():
            result["pcf"][node_id] = {
                "identity": _property(node, "code", "pcfid", "name", "name_en"),
                "description": _property(node, "description_ko", "description_en"),
                "path": normalize_text(node.get("computed_path_text")),
            }
        for node_id, node in self.taskframes.items():
            aliases = [alias.get("name", "") for alias in node.get("_aliases", [])]
            result["taskframe"][node_id] = {
                "identity": _property(node, "name", "displayName"),
                "definition": _property(node, "definition", "scope"),
                "aliases": compact_join(aliases),
                "evidence": self._representative_frame_evidence(node_id),
            }
        for node_id, node in self.taskmentions.items():
            direct_evidence = compact_join(
                self.evidence[evidence_id].get("name", "")
                for evidence_id in node.get("_evidence_ids", [])
                if evidence_id in self.evidence
            )
            result["taskmention"][node_id] = {
                "identity": _property(node, "name", "displayName"),
                "action": normalize_text(node.get("action_raw")),
                "object": normalize_text(node.get("focal_object_raw")),
                "outcome": normalize_text(node.get("intended_outcome_raw")),
                "evidence": direct_evidence,
            }
        for node_id, node in self.facts.items():
            result["fact"][node_id] = {
                "identity": _property(node, "name", "displayName"),
                "evidence": normalize_text(node.get("evidence_quote")),
                "triple": compact_join(
                    [
                        _property(node, "subject_canonical", "subject_raw"),
                        _property(node, "predicate_canonical", "predicate_raw"),
                        _property(node, "object_canonical", "object_raw"),
                    ],
                    " ",
                ),
                "qualifier": _qualifier_text(node.get("qualifiers")),
                "function": normalize_text(node.get("knowledge_function")),
            }
        for node_id, node in self.evidence.items():
            sections = node.get("_sections", [])
            result["evidence"][node_id] = {
                "text": _property(node, "name", "displayName"),
                "metadata": compact_join(
                    [
                        node.get("section_path"),
                        node.get("page"),
                        node.get("evidence_type"),
                        *(section.get("name", "") for section in sections),
                    ]
                ),
            }
        return result

    def _build_embedding_indices(self) -> None:
        for kind, records in self._group_texts.items():
            ids = list(records)
            group_names = sorted({group for value in records.values() for group in value})
            matrices: dict[str, np.ndarray] = {}
            available: dict[str, np.ndarray] = {}
            for group in group_names:
                texts = [normalize_text(records[node_id].get(group, "")) for node_id in ids]
                available[group] = np.asarray([bool(text) for text in texts], dtype=bool)
                vectors = self.backend.embed(
                    texts,
                    batch_size=self.embedding_batch_size,
                    input_type="document",
                )
                matrices[group] = np.asarray(vectors, dtype=np.float32)
            self.indices[kind] = GroupIndex(ids=ids, matrices=matrices, available=available)

    def question_vector(self, question: str) -> np.ndarray:
        key = normalize_text(question)
        if key not in self._question_vectors:
            self._question_vectors[key] = np.asarray(
                self.backend.embed([key], batch_size=1, input_type="query")[0],
                dtype=np.float32,
            )
        return self._question_vectors[key]

    def aspect_vectors(self, aspects: Mapping[str, Any]) -> dict[str, np.ndarray]:
        """Embed stage-specific, question-only aspect views.

        The original question vector remains the dominant signal. These views are
        deliberately limited to concepts extracted from the question and do not
        contain retrieved evidence or answers.
        """

        def values(name: str) -> list[str]:
            raw = aspects.get(name, [])
            if not isinstance(raw, list):
                return []
            return [normalize_text(item) for item in raw if normalize_text(item)]

        direct_views = aspects.get("stage_terms")
        if isinstance(direct_views, Mapping):
            texts = {
                name: compact_join(
                    direct_views.get(name, [])
                    if isinstance(direct_views.get(name, []), list)
                    else [],
                    " ",
                )
                for name in ("pcf", "taskframe", "fact")
            }
        else:
            domain = values("domain_objects")
            actions = values("actions")
            constraints = values("constraints")
            desired = values("desired_information")
            terms = values("search_terms")
            texts = {
                "pcf": compact_join(domain + actions + desired, " "),
                "taskframe": compact_join(actions + domain + desired, " "),
                "fact": compact_join(
                    desired + constraints + actions + domain + terms,
                    " ",
                ),
            }
        vectors = self.backend.embed(
            list(texts.values()),
            batch_size=len(texts),
            input_type="query",
        )
        return {
            name: np.asarray(vector, dtype=np.float32)
            for name, vector in zip(texts, vectors)
        }

    def aspect_multivectors(
        self,
        aspects: Mapping[str, Any],
        *,
        max_terms_per_stage: int = 5,
    ) -> dict[str, list[np.ndarray]]:
        """Embed each stage Aspect independently for late MaxSim aggregation.

        Concatenating several short concepts into one embedding can erase the
        weaker intent.  Independent vectors preserve those intents while the
        original full-question vector remains a separate, dominant branch.
        """
        if max_terms_per_stage < 1:
            raise ValueError("max_terms_per_stage must be positive")
        direct_views = aspects.get("stage_terms")
        by_stage: dict[str, list[str]] = {}
        if isinstance(direct_views, Mapping):
            for stage in ("pcf", "taskframe", "fact"):
                raw = direct_views.get(stage, [])
                values = raw if isinstance(raw, list) else []
                by_stage[stage] = list(
                    dict.fromkeys(
                        normalize_text(value)
                        for value in values
                        if normalize_text(value)
                    )
                )[:max_terms_per_stage]
        else:
            def values(name: str) -> list[str]:
                raw = aspects.get(name, [])
                if not isinstance(raw, list):
                    return []
                return [normalize_text(item) for item in raw if normalize_text(item)]

            domain = values("domain_objects")
            actions = values("actions")
            constraints = values("constraints")
            desired = values("desired_information")
            by_stage = {
                "pcf": list(dict.fromkeys(domain + actions + desired))[:max_terms_per_stage],
                "taskframe": list(dict.fromkeys(actions + domain + desired))[:max_terms_per_stage],
                "fact": list(
                    dict.fromkeys(constraints + actions + domain + desired)
                )[:max_terms_per_stage],
            }

        flattened = [
            (stage, text)
            for stage in ("pcf", "taskframe", "fact")
            for text in by_stage.get(stage, [])
        ]
        if not flattened:
            return {stage: [] for stage in ("pcf", "taskframe", "fact")}
        embedded = self.backend.embed(
            [text for _, text in flattened],
            batch_size=len(flattened),
            input_type="query",
        )
        output: dict[str, list[np.ndarray]] = {
            stage: [] for stage in ("pcf", "taskframe", "fact")
        }
        for (stage, _), vector in zip(flattened, embedded):
            output[stage].append(np.asarray(vector, dtype=np.float32))
        return output

    def group_scores(
        self,
        kind: str,
        query_vector: np.ndarray,
        weights: Mapping[str, float],
        *,
        condition: str,
    ) -> dict[str, float]:
        index = self.indices[kind]
        numerator = np.zeros(len(index.ids), dtype=np.float32)
        denominator = np.zeros(len(index.ids), dtype=np.float32)
        masked = {
            "taskmention": {"action", "object", "outcome"},
            "fact": {"triple", "qualifier", "function"},
        }
        for group, weight in weights.items():
            if weight <= 0 or group not in index.matrices:
                continue
            if condition == "D1_PROPERTY_MASK" and group in masked.get(kind, set()):
                continue
            availability = index.available[group]
            similarities = np.maximum(0.0, index.matrices[group] @ query_vector)
            numerator += similarities * float(weight) * availability
            denominator += float(weight) * availability
        scores = np.divide(
            numerator,
            denominator,
            out=np.zeros_like(numerator),
            where=denominator > 0,
        )
        return {node_id: float(score) for node_id, score in zip(index.ids, scores)}

    def evidence_hybrid_scores(self, question: str, query_vector: np.ndarray) -> dict[str, float]:
        cache_key = normalize_text(question)
        if cache_key in self._hybrid_scores:
            return self._hybrid_scores[cache_key]
        semantic = self.group_scores(
            "evidence", query_vector, {"text": 0.9, "metadata": 0.1}, condition="D0_ORIGINAL"
        )
        lexical_array = self.evidence_bm25.scores(self._tokens(question))
        lexical = dict(zip(self.evidence_bm25_ids, (float(value) for value in lexical_array)))
        result = {
            evidence_id: 0.75 * semantic.get(evidence_id, 0.0)
            + 0.25 * lexical.get(evidence_id, 0.0)
            for evidence_id in self.evidence
        }
        self._hybrid_scores[cache_key] = result
        return result

    def evidence_dense_scores(self, question: str, query_vector: np.ndarray) -> dict[str, float]:
        """Score every EvidenceSpan using only text-embedding cosine similarity.

        Embeddings are L2-normalized by ``OpenAIBackend.embed``, so the dot product
        used by ``group_scores`` is cosine similarity. Metadata, BM25, and graph
        features are intentionally excluded to keep this a vanilla vector-RAG
        baseline.
        """
        cache_key = normalize_text(question)
        if cache_key not in self._dense_scores:
            index = self.indices["evidence"]
            similarities = index.matrices["text"] @ query_vector
            self._dense_scores[cache_key] = {
                evidence_id: float(score)
                for evidence_id, score in zip(index.ids, similarities)
            }
        return self._dense_scores[cache_key]

    @staticmethod
    def _edge_semantic_text(
        relationship_type: str,
        properties: Mapping[str, Any] | None,
    ) -> str:
        """Keep human-semantic edge fields and drop pipeline bookkeeping.

        The graph contains many operational fields (run IDs, colors, hashes,
        timestamps).  Treating those as semantic content would add noise rather
        than "use every property" in a meaningful sense.  Relation type and the
        fields below are the edge attributes that can explain a query/path.
        """
        values: list[Any] = [relationship_type.replace("_", " ")]
        source = properties if isinstance(properties, Mapping) else {}
        for key in (
            "reason",
            "rationale",
            "mapping_role",
            "relation_scope",
            "method",
            "propagation_path",
            "relevance",
            "review_status",
            "validation_status",
        ):
            value = source.get(key)
            if value not in (None, "", [], {}):
                values.append(value)
        return compact_join(values, " ")

    def _build_property_relational_graph(self) -> None:
        """Reconstruct every query-relevant stored node and edge in the snapshot.

        Alias and Section nodes are nested in the snapshot rows, so this method
        restores them as first-class nodes.  The resulting graph is used only
        for read-only query-time subgraph selection; it does not create virtual
        Neo4j edges or mutate the database.
        """
        self.graph_node_labels: dict[str, str] = {}
        self.graph_node_names: dict[str, str] = {}
        for label, records in (
            ("PCFProcess", self.pcfs),
            ("TaskFrame", self.taskframes),
            ("TaskMention", self.taskmentions),
            ("Fact", self.facts),
            ("EvidenceSpan", self.evidence),
        ):
            for node_id, node in records.items():
                self.graph_node_labels[node_id] = label
                self.graph_node_names[node_id] = _property(
                    node, "name", "displayName"
                )

        self.aliases: dict[str, dict[str, Any]] = {}
        self.sections: dict[str, dict[str, Any]] = {}
        for row in self.snapshot.get("taskframes", []):
            for alias in row.get("aliases", []):
                alias_id = normalize_text(alias.get("id"))
                if alias_id:
                    self.aliases[alias_id] = dict(alias)
                    self.graph_node_labels[alias_id] = "TaskFrameAlias"
                    self.graph_node_names[alias_id] = _property(
                        alias, "name", "displayName"
                    )
        for row in self.snapshot.get("evidence_spans", []):
            for section in row.get("sections", []):
                section_id = normalize_text(section.get("id"))
                if section_id:
                    self.sections[section_id] = dict(section)
                    self.graph_node_labels[section_id] = "Section"
                    self.graph_node_names[section_id] = _property(
                        section, "name", "displayName"
                    )

        self.stored_graph_edges: dict[str, StoredGraphEdge] = {}
        self.graph_adjacency: dict[str, list[tuple[str, str]]] = defaultdict(list)
        self._edges_from: dict[str, list[str]] = defaultdict(list)
        self._edges_to: dict[str, list[str]] = defaultdict(list)

        def add_edge(
            source: Any,
            relation: Any,
            target: Any,
            properties: Mapping[str, Any] | None = None,
        ) -> None:
            source_id = normalize_text(source)
            target_id = normalize_text(target)
            relationship = normalize_text(relation)
            if not source_id or not target_id or not relationship:
                return
            raw_id = normalize_text((properties or {}).get("id"))
            base_id = raw_id or f"{relationship}:{source_id}:{target_id}"
            edge_id = base_id
            suffix = 2
            while edge_id in self.stored_graph_edges:
                edge_id = f"{base_id}#{suffix}"
                suffix += 1
            edge = StoredGraphEdge(
                edge_id=edge_id,
                source=source_id,
                relation=relationship,
                target=target_id,
                semantic_text=self._edge_semantic_text(
                    relationship, properties
                ),
            )
            self.stored_graph_edges[edge_id] = edge
            self.graph_adjacency[source_id].append((target_id, edge_id))
            self.graph_adjacency[target_id].append((source_id, edge_id))
            self._edges_from[source_id].append(edge_id)
            self._edges_to[target_id].append(edge_id)

        for row in self.snapshot.get("pcf_child_of", []):
            add_edge(
                row.get("child_id"),
                "CHILD_OF",
                row.get("parent_id"),
                row.get("properties"),
            )
        for row in self.snapshot.get("pcf_mappings", []):
            add_edge(
                row.get("taskframe_id"),
                row.get("relationship_type"),
                row.get("pcf_id"),
                row.get("properties"),
            )
        for row in self.snapshot.get("taskframes", []):
            frame_id = row.get("properties", {}).get("id")
            for alias in row.get("aliases", []):
                add_edge(frame_id, "HAS_ALIAS", alias.get("id"), {})
        for row in self.snapshot.get("taskmentions", []):
            mention_id = row.get("properties", {}).get("id")
            add_edge(mention_id, "MEMBER_OF", row.get("taskframe_id"), {})
            for evidence_id in row.get("evidence_ids", []):
                add_edge(mention_id, "SUPPORTED_BY", evidence_id, {})
        for row in self.snapshot.get("facts", []):
            fact_id = row.get("properties", {}).get("id")
            for link in row.get("frame_links", []):
                add_edge(
                    link.get("taskframe_id"),
                    link.get("relationship_type"),
                    fact_id,
                    link.get("properties"),
                )
            for link in row.get("taskmention_links", []):
                add_edge(
                    fact_id,
                    "RELATED_TO_TASK_MENTION",
                    link.get("taskmention_id"),
                    link.get("properties"),
                )
            for evidence_id in row.get("evidence_ids", []):
                add_edge(fact_id, "SUPPORTED_BY", evidence_id, {})
        for row in self.snapshot.get("evidence_spans", []):
            evidence_id = row.get("properties", {}).get("id")
            for section in row.get("sections", []):
                add_edge(section.get("id"), "HAS_EVIDENCE", evidence_id, {})
        for row in self.snapshot.get("taskframe_relations", []):
            add_edge(
                row.get("source_id"),
                row.get("relationship_type"),
                row.get("target_id"),
                row.get("properties"),
            )

        self.edge_bm25_ids = list(self.stored_graph_edges)
        self.edge_bm25 = BM25(
            [
                self._tokens(self.stored_graph_edges[edge_id].semantic_text)
                for edge_id in self.edge_bm25_ids
            ]
        )
        self.evidence_support_nodes: dict[str, frozenset[str]] = {}
        self.evidence_support_edges: dict[str, frozenset[str]] = {}
        self._build_evidence_support_closures()

    def _build_evidence_support_closures(self) -> None:
        """Build bounded, direction-aware support closures for each EvidenceSpan.

        Traversal follows explanatory relations toward taxonomy/context and never
        fans back down from a TaskFrame into every sibling Fact or TaskMention.
        This keeps the candidate connected and prevents dense frames from winning
        merely because they contain more nodes.
        """
        pcf_parent_edge: dict[str, str] = {}
        for edge_id, edge in self.stored_graph_edges.items():
            if edge.relation == "CHILD_OF":
                pcf_parent_edge[edge.source] = edge_id

        for evidence_id in self.evidence:
            nodes: set[str] = {evidence_id}
            edges: set[str] = set()
            direct_sources: list[str] = []
            for edge_id in self._edges_to.get(evidence_id, []):
                edge = self.stored_graph_edges[edge_id]
                if edge.relation not in {"SUPPORTED_BY", "HAS_EVIDENCE"}:
                    continue
                nodes.add(edge.source)
                edges.add(edge_id)
                direct_sources.append(edge.source)

            frame_ids: set[str] = set()
            related_mentions: set[str] = set()
            for source_id in direct_sources:
                label = self.graph_node_labels.get(source_id)
                if label == "Fact":
                    for edge_id in self._edges_to.get(source_id, []):
                        edge = self.stored_graph_edges[edge_id]
                        if edge.relation in FACT_RELATION_WEIGHT:
                            nodes.add(edge.source)
                            edges.add(edge_id)
                            frame_ids.add(edge.source)
                    for edge_id in self._edges_from.get(source_id, []):
                        edge = self.stored_graph_edges[edge_id]
                        if edge.relation == "RELATED_TO_TASK_MENTION":
                            nodes.add(edge.target)
                            edges.add(edge_id)
                            related_mentions.add(edge.target)
                elif label == "TaskMention":
                    related_mentions.add(source_id)

            for mention_id in related_mentions:
                for edge_id in self._edges_from.get(mention_id, []):
                    edge = self.stored_graph_edges[edge_id]
                    if edge.relation == "MEMBER_OF":
                        nodes.add(edge.target)
                        edges.add(edge_id)
                        frame_ids.add(edge.target)

            # Restore all semantic context attached to a relevant frame: aliases,
            # PCF mappings, and one TaskFrame-to-TaskFrame relation hop.
            related_frames: set[str] = set()
            for frame_id in list(frame_ids):
                for edge_id in (
                    *self._edges_from.get(frame_id, []),
                    *self._edges_to.get(frame_id, []),
                ):
                    edge = self.stored_graph_edges[edge_id]
                    other = edge.target if edge.source == frame_id else edge.source
                    if edge.relation == "HAS_ALIAS" or edge.relation in MAPPING_RELATION_WEIGHT:
                        nodes.add(other)
                        edges.add(edge_id)
                    elif edge.relation in {
                        "PRECEDES",
                        "SUPPORTS",
                        "RELATED_TASK",
                        "SUBTASK_OF",
                    }:
                        nodes.add(other)
                        edges.add(edge_id)
                        related_frames.add(other)

            # Neighboring frames contribute only their own semantic node and
            # directly attached alias/PCF context; their facts are not expanded.
            for frame_id in related_frames:
                for edge_id in self._edges_from.get(frame_id, []):
                    edge = self.stored_graph_edges[edge_id]
                    if edge.relation == "HAS_ALIAS" or edge.relation in MAPPING_RELATION_WEIGHT:
                        nodes.add(edge.target)
                        edges.add(edge_id)

            # Add the full PCF ancestry for every mapped process already in the
            # closure. This is a single parent chain, not an unrestricted BFS.
            pcf_ids = {
                node_id
                for node_id in nodes
                if self.graph_node_labels.get(node_id) == "PCFProcess"
            }
            for pcf_id in list(pcf_ids):
                current = pcf_id
                seen: set[str] = set()
                while current in pcf_parent_edge and current not in seen:
                    seen.add(current)
                    edge_id = pcf_parent_edge[current]
                    edge = self.stored_graph_edges[edge_id]
                    nodes.add(edge.target)
                    edges.add(edge_id)
                    current = edge.target

            self.evidence_support_nodes[evidence_id] = frozenset(nodes)
            self.evidence_support_edges[evidence_id] = frozenset(edges)

    def schema_property_matches(
        self,
        query_vector: np.ndarray,
        *,
        condition: str,
    ) -> dict[str, dict[str, Any]]:
        """Return every primary node's strongest semantic property match."""
        masked = {
            "taskmention": {"action", "object", "outcome"},
            "fact": {"triple", "qualifier", "function"},
        }
        output: dict[str, dict[str, Any]] = {}
        labels = {
            "pcf": "PCFProcess",
            "taskframe": "TaskFrame",
            "taskmention": "TaskMention",
            "fact": "Fact",
            "evidence": "EvidenceSpan",
        }
        for kind, index in self.indices.items():
            best = np.full(len(index.ids), -np.inf, dtype=np.float32)
            best_group = np.full(len(index.ids), "", dtype=object)
            for group, matrix in index.matrices.items():
                if condition == "D1_PROPERTY_MASK" and group in masked.get(kind, set()):
                    continue
                values = np.maximum(0.0, matrix @ query_vector)
                values = np.where(index.available[group], values, -np.inf)
                improved = values > best
                best[improved] = values[improved]
                best_group[improved] = group
            for position, node_id in enumerate(index.ids):
                group = str(best_group[position])
                value = float(best[position])
                if not group or not math.isfinite(value):
                    continue
                output[node_id] = {
                    "score": value,
                    "node_type": labels[kind],
                    "property_view": group,
                    "property_text": normalize_text(
                        self._group_texts[kind][node_id].get(group, "")
                    ),
                }
        return output

    def edge_lexical_scores(self, query_text: str) -> dict[str, float]:
        values = self.edge_bm25.scores(self._tokens(query_text))
        return {
            edge_id: float(score)
            for edge_id, score in zip(self.edge_bm25_ids, values)
        }

    def minimal_evidence_subgraph(
        self,
        evidence_id: str,
        terminal_ids: Sequence[str],
        *,
        required_edge_id: str = "",
    ) -> tuple[list[str], list[str]]:
        """Union shortest stored paths from relevant terminals to EvidenceSpan."""
        allowed_nodes = set(self.evidence_support_nodes.get(evidence_id, {evidence_id}))
        allowed_edges = set(self.evidence_support_edges.get(evidence_id, set()))
        selected_nodes: set[str] = {evidence_id}
        selected_edges: set[str] = set()

        def path_to_root(start: str) -> tuple[list[str], list[str]]:
            if start == evidence_id:
                return [evidence_id], []
            if start not in allowed_nodes:
                return [], []
            queue = [start]
            previous: dict[str, tuple[str, str] | None] = {start: None}
            for current in queue:
                if current == evidence_id:
                    break
                for neighbor, edge_id in self.graph_adjacency.get(current, []):
                    if edge_id not in allowed_edges or neighbor not in allowed_nodes:
                        continue
                    if neighbor in previous:
                        continue
                    previous[neighbor] = (current, edge_id)
                    queue.append(neighbor)
            if evidence_id not in previous:
                return [], []
            nodes = [evidence_id]
            edge_ids: list[str] = []
            current = evidence_id
            while previous[current] is not None:
                parent, edge_id = previous[current]
                nodes.append(parent)
                edge_ids.append(edge_id)
                current = parent
            return nodes, edge_ids

        for terminal_id in dict.fromkeys(terminal_ids):
            nodes, edges = path_to_root(terminal_id)
            selected_nodes.update(nodes)
            selected_edges.update(edges)
        if required_edge_id in allowed_edges:
            edge = self.stored_graph_edges[required_edge_id]
            selected_nodes.update((edge.source, edge.target))
            selected_edges.add(required_edge_id)
            for endpoint in (edge.source, edge.target):
                nodes, edges = path_to_root(endpoint)
                selected_nodes.update(nodes)
                selected_edges.update(edges)

        return (
            sorted(
                selected_nodes,
                key=lambda node_id: (
                    node_id != evidence_id,
                    self.graph_node_labels.get(node_id, ""),
                    node_id,
                ),
            ),
            sorted(selected_edges),
        )

    def pcf_distance(self, left: str, right: str) -> int | None:
        left_path = self.pcf_path_ids.get(left, [])
        right_path = self.pcf_path_ids.get(right, [])
        if not left_path or not right_path:
            return None
        shared = 0
        for left_id, right_id in zip(left_path, right_path):
            if left_id != right_id:
                break
            shared += 1
        return (len(left_path) - shared) + (len(right_path) - shared)


def _qpa_weights(profile: Mapping[str, Any]) -> tuple[dict[str, float], dict[str, float]]:
    tm = {"identity": 0.22, "action": 0.20, "object": 0.18, "outcome": 0.12, "evidence": 0.28}
    fact = {"identity": 0.12, "evidence": 0.32, "triple": 0.24, "qualifier": 0.18, "function": 0.14}
    facets = set(profile.get("target_facets", []))
    for facet in facets:
        if facet in tm:
            tm[facet] += 0.28
        if facet == "triple" or facet in {"object", "action", "outcome"}:
            fact["triple"] += 0.24
        if facet in {"qualifier", "condition", "temporal", "comparison"}:
            fact["qualifier"] += 0.34
        if facet in {"procedure", "definition", "cause"}:
            fact["function"] += 0.18
        if facet == "evidence":
            fact["evidence"] += 0.25
            tm["evidence"] += 0.25
    if profile.get("requires_qualifiers"):
        fact["qualifier"] += 0.30
    if profile.get("requires_structured_fact"):
        fact["triple"] += 0.25
    return tm, fact


FIXED_TM_WEIGHTS = {
    "identity": 0.20,
    "action": 0.20,
    "object": 0.20,
    "outcome": 0.20,
    "evidence": 0.20,
}
FIXED_FACT_WEIGHTS = {
    "identity": 0.20,
    "evidence": 0.20,
    "triple": 0.20,
    "qualifier": 0.20,
    "function": 0.20,
}


class QPARetriever:
    def __init__(
        self,
        graph: GraphIndex,
        config: Mapping[str, Any],
        *,
        cross_encoder: Any | None = None,
    ) -> None:
        self.graph = graph
        self.config = config
        self.cross_encoder = cross_encoder

    @staticmethod
    def _top(scores: Mapping[str, float], limit: int) -> list[tuple[str, float]]:
        return sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:limit]

    @staticmethod
    def _blend_scores(
        base_scores: Mapping[str, float],
        aspect_scores: Mapping[str, float] | None,
        aspect_weight: float,
    ) -> dict[str, float]:
        if aspect_scores is None or aspect_weight <= 0:
            return dict(base_scores)
        if not 0.0 <= aspect_weight <= 1.0:
            raise ValueError("Aspect semantic_blend_weight must be between zero and one")
        return {
            item: (1.0 - aspect_weight) * float(base_scores.get(item, 0.0))
            + aspect_weight * float(aspect_scores.get(item, 0.0))
            for item in set(base_scores) | set(aspect_scores)
        }

    def _aspect_group_scores(
        self,
        kind: str,
        aspect_vectors: np.ndarray | Sequence[np.ndarray] | None,
        weights: Mapping[str, float],
        *,
        condition: str,
    ) -> dict[str, float] | None:
        if aspect_vectors is None:
            return None
        if isinstance(aspect_vectors, np.ndarray) and aspect_vectors.ndim == 1:
            return self.graph.group_scores(
                kind,
                aspect_vectors,
                weights,
                condition=condition,
            )
        vectors = [
            np.asarray(vector, dtype=np.float32)
            for vector in aspect_vectors
            if np.asarray(vector).size
        ]
        if not vectors:
            return None
        per_view = [
            self.graph.group_scores(kind, vector, weights, condition=condition)
            for vector in vectors
        ]
        config = self._aspect_config()
        max_weight = float(config.get("multivector_max_weight", 0.70))
        top_n = max(1, int(config.get("multivector_top_n", 2)))
        if not 0.0 <= max_weight <= 1.0:
            raise ValueError("multivector_max_weight must be between zero and one")
        output: dict[str, float] = {}
        node_ids = set().union(*(scores.keys() for scores in per_view))
        for node_id in node_ids:
            values = sorted(
                (float(scores.get(node_id, 0.0)) for scores in per_view),
                reverse=True,
            )
            strongest = values[0]
            top_mean = float(np.mean(values[:top_n]))
            output[node_id] = max_weight * strongest + (1.0 - max_weight) * top_mean
        return output

    def _pcf_candidates(
        self,
        query_vector: np.ndarray,
        *,
        aspect_vector: np.ndarray | Sequence[np.ndarray] | None = None,
        aspect_weight: float = 0.0,
    ) -> list[dict[str, Any]]:
        weights = {"identity": 0.35, "description": 0.45, "path": 0.20}
        base_scores = self.graph.group_scores(
            "pcf",
            query_vector,
            weights,
            condition="D0_ORIGINAL",
        )
        aspect_scores = self._aspect_group_scores(
            "pcf",
            aspect_vector,
            weights,
            condition="D0_ORIGINAL",
        )
        scores = self._blend_scores(base_scores, aspect_scores, aspect_weight)
        return [
            {
                "id": node_id,
                "score": score,
                "name": self.graph.pcfs[node_id].get("name", ""),
                "code": self.graph.pcfs[node_id].get("code", ""),
                "level": self.graph.pcfs[node_id].get("level"),
                "path": self.graph.pcfs[node_id].get("computed_path_text", ""),
            }
            for node_id, score in self._top(scores, int(self.config["pcf_top_k"]))
        ]

    def _v2_config(self) -> Mapping[str, Any]:
        value = self.config.get("late_fusion", {})
        return value if isinstance(value, Mapping) else {}

    def _p1_config(self) -> Mapping[str, Any]:
        value = self.config.get("p0_cross_encoder_rerank", {})
        return value if isinstance(value, Mapping) else {}

    def _aspect_config(self) -> Mapping[str, Any]:
        value = self.config.get("aspect_analysis", {})
        return value if isinstance(value, Mapping) else {}

    def _aspect_stage_weights(self) -> dict[str, float]:
        config = self._aspect_config()
        default = float(config.get("semantic_blend_weight", 0.25))
        configured = config.get("stage_semantic_blend_weights", {})
        if not isinstance(configured, Mapping):
            raise ValueError("stage_semantic_blend_weights must be a mapping")
        weights = {
            stage: float(configured.get(stage, default))
            for stage in ("pcf", "taskframe", "fact")
        }
        if any(not 0.0 <= value <= 1.0 for value in weights.values()):
            raise ValueError("All Aspect stage blend weights must be between zero and one")
        return weights

    def _pcf_candidates_v2(self, query_vector: np.ndarray) -> list[dict[str, Any]]:
        """Return global PCF candidates plus a mapped-subgraph branch.

        The extra branch is only a soft signal for TaskFrame ranking.  It never
        removes a directly retrieved TaskFrame.
        """
        scores = self.graph.group_scores(
            "pcf",
            query_vector,
            {"identity": 0.35, "description": 0.45, "path": 0.20},
            condition="D0_ORIGINAL",
        )
        global_limit = int(self.config["pcf_top_k"])
        connected_limit = int(
            self._v2_config().get("connected_pcf_candidate_k", global_limit)
        )
        global_ranked = self._top(scores, global_limit)

        connected_ids: set[str] = set()
        for mapping in self.graph.mappings:
            pcf_id = mapping.get("pcf_id")
            if pcf_id:
                connected_ids.add(pcf_id)
                connected_ids.update(self.graph.pcf_path_ids.get(pcf_id, []))
        connected_scores = {
            pcf_id: scores.get(pcf_id, 0.0)
            for pcf_id in connected_ids
            if pcf_id in self.graph.pcfs
        }
        connected_ranked = self._top(connected_scores, connected_limit)

        merged: dict[str, dict[str, Any]] = {}
        for source, ranked in (
            ("global", global_ranked),
            ("connected_subgraph", connected_ranked),
        ):
            for node_id, score in ranked:
                if node_id not in merged:
                    node = self.graph.pcfs[node_id]
                    merged[node_id] = {
                        "id": node_id,
                        "score": score,
                        "name": node.get("name", ""),
                        "code": node.get("code", ""),
                        "level": node.get("level"),
                        "path": node.get("computed_path_text", ""),
                        "candidate_source": source,
                    }
                elif source not in merged[node_id]["candidate_source"]:
                    merged[node_id]["candidate_source"] = "global+connected_subgraph"
        return sorted(merged.values(), key=lambda item: (-item["score"], item["id"]))

    def _mapping_prior(
        self,
        pcf_candidates: Sequence[Mapping[str, Any]],
        *,
        condition: str,
    ) -> dict[str, float]:
        maximum_distance = int(self.config["pcf_hierarchy_max_distance"])
        priors: dict[str, float] = defaultdict(float)
        for mapping in self.graph.mappings:
            mapped_pcf = mapping["pcf_id"]
            relation_weight = MAPPING_RELATION_WEIGHT.get(mapping["relationship_type"], 0.5)
            properties = mapping.get("properties", {})
            if condition == "D0_ORIGINAL":
                confidence = _float(properties.get("confidence"), 0.5)
                coverage = _float(properties.get("coverage_score"), 0.5)
                metadata_weight = 0.55 + 0.25 * confidence + 0.20 * coverage
            else:
                metadata_weight = 1.0
            for candidate in pcf_candidates:
                distance = self.graph.pcf_distance(candidate["id"], mapped_pcf)
                if distance is None or distance > maximum_distance:
                    continue
                score = (
                    float(candidate["score"])
                    * math.exp(-0.55 * distance)
                    * relation_weight
                    * metadata_weight
                )
                taskframe_id = mapping["taskframe_id"]
                priors[taskframe_id] = max(priors[taskframe_id], score)
        return dict(priors)

    def _taskframe_candidates(
        self,
        query_vector: np.ndarray,
        pcf_candidates: Sequence[Mapping[str, Any]],
        *,
        condition: str,
        allow_gap_adaptation: bool,
        aspect_vector: np.ndarray | Sequence[np.ndarray] | None = None,
        aspect_weight: float = 0.0,
    ) -> tuple[list[dict[str, Any]], bool]:
        weights = {"identity": 0.25, "definition": 0.25, "aliases": 0.15, "evidence": 0.35}
        base_semantic = self.graph.group_scores(
            "taskframe",
            query_vector,
            weights,
            condition=condition,
        )
        aspect_semantic = self._aspect_group_scores(
            "taskframe",
            aspect_vector,
            weights,
            condition=condition,
        )
        semantic = self._blend_scores(base_semantic, aspect_semantic, aspect_weight)
        priors = self._mapping_prior(pcf_candidates, condition=condition)
        candidate_ids = set(priors)
        used_gap_adaptation = False
        target_count = int(self.config["taskframe_top_k"])
        if allow_gap_adaptation and len(candidate_ids) < target_count:
            used_gap_adaptation = True
            for taskframe_id, _ in self._top(semantic, target_count):
                candidate_ids.add(taskframe_id)
        scores: dict[str, float] = {}
        for taskframe_id in candidate_ids:
            prior = priors.get(taskframe_id, 0.0)
            scores[taskframe_id] = 0.75 * semantic.get(taskframe_id, 0.0) + 0.25 * prior
        selected = []
        for taskframe_id, score in self._top(scores, target_count):
            node = self.graph.taskframes[taskframe_id]
            selected.append(
                {
                    "id": taskframe_id,
                    "name": node.get("name", ""),
                    "score": score,
                    "semantic_score": semantic.get(taskframe_id, 0.0),
                    "pcf_prior": priors.get(taskframe_id, 0.0),
                    "candidate_source": "pcf" if taskframe_id in priors else "global_fallback",
                }
            )
        return selected, used_gap_adaptation

    def _taskframe_candidates_v2(
        self,
        query_vector: np.ndarray,
        pcf_candidates: Sequence[Mapping[str, Any]],
        *,
        condition: str,
    ) -> list[dict[str, Any]]:
        """Rank every TaskFrame directly and use PCF only as a soft feature."""
        semantic = self.graph.group_scores(
            "taskframe",
            query_vector,
            {"identity": 0.25, "definition": 0.25, "aliases": 0.15, "evidence": 0.35},
            condition=condition,
        )
        priors = self._mapping_prior(pcf_candidates, condition=condition)
        v2 = self._v2_config()
        semantic_weight = float(v2.get("taskframe_semantic_weight", 0.85))
        pcf_weight = float(v2.get("taskframe_pcf_weight", 0.15))
        total = semantic_weight + pcf_weight
        if total <= 0:
            raise ValueError("late_fusion TaskFrame weights must sum to a positive value")
        semantic_weight /= total
        pcf_weight /= total
        scores = {
            taskframe_id: semantic_weight * semantic_score
            + pcf_weight * priors.get(taskframe_id, 0.0)
            for taskframe_id, semantic_score in semantic.items()
        }
        selected: list[dict[str, Any]] = []
        for taskframe_id, score in self._top(scores, int(self.config["taskframe_top_k"])):
            node = self.graph.taskframes[taskframe_id]
            selected.append(
                {
                    "id": taskframe_id,
                    "name": node.get("name", ""),
                    "score": score,
                    "semantic_score": semantic.get(taskframe_id, 0.0),
                    "pcf_prior": priors.get(taskframe_id, 0.0),
                    "candidate_source": (
                        "direct_semantic+pcf_prior"
                        if taskframe_id in priors
                        else "direct_semantic"
                    ),
                }
            )
        return selected

    @staticmethod
    def _explicitly_false(value: Any) -> bool:
        if value is False or value == 0:
            return True
        return normalize_text(value).lower() in {"false", "0", "no", "inactive"}

    @classmethod
    def _allow_v2_taskmention(cls, mention: Mapping[str, Any]) -> bool:
        if cls._explicitly_false(mention.get("active")):
            return False
        quality = normalize_text(
            mention.get("quality_status") or mention.get("review_status")
        ).lower()
        return quality not in {"review_required", "quarantined", "rejected"}

    @classmethod
    def _allow_v2_fact(cls, fact: Mapping[str, Any]) -> bool:
        if cls._explicitly_false(fact.get("active")):
            return False
        lifecycle = normalize_text(
            fact.get("lifecycleStatus") or fact.get("lifecycle_status")
        ).lower()
        quality = normalize_text(fact.get("quality_status")).lower()
        return lifecycle != "superseded" and quality not in {"quarantined", "rejected"}

    def _fact_bonus(self, fact: Mapping[str, Any], profile: Mapping[str, Any]) -> float:
        bonus = 0.0
        requested = set(profile.get("knowledge_functions", []))
        function = normalize_text(fact.get("knowledge_function")).lower()
        if function and function in requested:
            bonus += 0.08
        quality = normalize_text(fact.get("quality_status")).lower()
        if quality == "accepted":
            bonus += 0.04
        elif quality in {"quarantined", "rejected"}:
            bonus -= 0.18
        return bonus

    def _graph_evidence(
        self,
        *,
        query_vector: np.ndarray,
        question: str,
        taskframes: Sequence[Mapping[str, Any]],
        profile: Mapping[str, Any],
        condition: str,
        fixed_properties: bool,
        filter_low_quality: bool = False,
        aspect_vector: np.ndarray | Sequence[np.ndarray] | None = None,
        aspect_weight: float = 0.0,
    ) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        if fixed_properties:
            tm_weights, fact_weights = FIXED_TM_WEIGHTS, FIXED_FACT_WEIGHTS
        else:
            tm_weights, fact_weights = _qpa_weights(profile)
        tm_base_semantic = self.graph.group_scores(
            "taskmention", query_vector, tm_weights, condition=condition
        )
        fact_base_semantic = self.graph.group_scores(
            "fact", query_vector, fact_weights, condition=condition
        )
        tm_aspect_semantic = self._aspect_group_scores(
            "taskmention",
            aspect_vector,
            tm_weights,
            condition=condition,
        )
        fact_aspect_semantic = self._aspect_group_scores(
            "fact",
            aspect_vector,
            fact_weights,
            condition=condition,
        )
        tm_semantic = self._blend_scores(
            tm_base_semantic, tm_aspect_semantic, aspect_weight
        )
        fact_semantic = self._blend_scores(
            fact_base_semantic, fact_aspect_semantic, aspect_weight
        )
        evidence_hybrid = self.graph.evidence_hybrid_scores(question, query_vector)
        frame_score = {item["id"]: float(item["score"]) for item in taskframes}

        taskmention_ranked: list[dict[str, Any]] = []
        allowed_mentions: set[str] = set()
        for frame_id in frame_score:
            allowed_mentions.update(self.graph.tm_by_frame.get(frame_id, []))
        for mention_id in allowed_mentions:
            mention = self.graph.taskmentions[mention_id]
            if filter_low_quality and not self._allow_v2_taskmention(mention):
                continue
            score = 0.82 * tm_semantic.get(mention_id, 0.0) + 0.18 * frame_score.get(
                mention["_taskframe_id"], 0.0
            )
            taskmention_ranked.append(
                {
                    "id": mention_id,
                    "taskframe_id": mention["_taskframe_id"],
                    "name": mention.get("name", ""),
                    "score": score,
                }
            )
        taskmention_ranked.sort(key=lambda item: (-item["score"], item["id"]))
        taskmention_ranked = taskmention_ranked[:12]
        top_mentions = {item["id"] for item in taskmention_ranked[:8]}

        fact_ranked: list[dict[str, Any]] = []
        fact_best_link: dict[str, dict[str, Any]] = {}
        for frame_id in frame_score:
            for fact_id, link in self.graph.fact_by_frame.get(frame_id, []):
                fact = self.graph.facts[fact_id]
                if filter_low_quality and not self._allow_v2_fact(fact):
                    continue
                role_weight = FACT_RELATION_WEIGHT.get(link.get("relationship_type", ""), 0.6)
                linked_mentions = {
                    item.get("taskmention_id") for item in fact.get("_taskmention_links", [])
                }
                mention_bonus = 0.05 if linked_mentions & top_mentions else 0.0
                score = (
                    0.73 * fact_semantic.get(fact_id, 0.0)
                    + 0.17 * frame_score.get(frame_id, 0.0)
                    + 0.10 * role_weight
                    + mention_bonus
                    + self._fact_bonus(fact, profile)
                )
                if fact_id not in fact_best_link or score > fact_best_link[fact_id]["score"]:
                    fact_best_link[fact_id] = {
                        "score": score,
                        "taskframe_id": frame_id,
                        "relationship_type": link.get("relationship_type", ""),
                    }
        for fact_id, best in fact_best_link.items():
            fact = self.graph.facts[fact_id]
            fact_ranked.append(
                {
                    "id": fact_id,
                    "name": fact.get("name", ""),
                    "score": best["score"],
                    "taskframe_id": best["taskframe_id"],
                    "relationship_type": best["relationship_type"],
                    "knowledge_function": fact.get("knowledge_function", ""),
                    "quality_status": fact.get("quality_status", ""),
                }
            )
        fact_ranked.sort(key=lambda item: (-item["score"], item["id"]))
        fact_ranked = fact_ranked[:30]

        candidates: dict[str, dict[str, Any]] = {}
        for fact_item in fact_ranked:
            fact = self.graph.facts[fact_item["id"]]
            for evidence_id in fact.get("_evidence_ids", []):
                if evidence_id not in self.graph.evidence:
                    continue
                score = 0.68 * fact_item["score"] + 0.32 * evidence_hybrid.get(evidence_id, 0.0)
                candidate = {
                    "evidence_id": evidence_id,
                    "score": score,
                    "source": "fact_path",
                    "taskframe_id": fact_item["taskframe_id"],
                    "fact_id": fact_item["id"],
                    "fact_relationship": fact_item["relationship_type"],
                    "taskmention_id": "",
                }
                if evidence_id not in candidates or score > candidates[evidence_id]["score"]:
                    candidates[evidence_id] = candidate

        for mention_item in taskmention_ranked:
            mention = self.graph.taskmentions[mention_item["id"]]
            for evidence_id in mention.get("_evidence_ids", []):
                if evidence_id not in self.graph.evidence:
                    continue
                score = 0.62 * mention_item["score"] + 0.38 * evidence_hybrid.get(evidence_id, 0.0)
                candidate = {
                    "evidence_id": evidence_id,
                    "score": score,
                    "source": "taskmention_path",
                    "taskframe_id": mention_item["taskframe_id"],
                    "fact_id": "",
                    "fact_relationship": "",
                    "taskmention_id": mention_item["id"],
                }
                if evidence_id not in candidates or score > candidates[evidence_id]["score"]:
                    candidates[evidence_id] = candidate
        return candidates, taskmention_ranked, fact_ranked

    def _late_fusion_candidates(
        self,
        graph_candidates: Mapping[str, Mapping[str, Any]],
        hybrid_scores: Mapping[str, float],
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Fuse independent global and graph ranks while preserving B0 candidates.

        Weighted reciprocal-rank fusion is deliberately deterministic and has no
        additional model dependency.  A cross-encoder can later replace this
        function without changing candidate generation or output fields.
        """
        v2 = self._v2_config()
        reranker = normalize_text(v2.get("reranker", "weighted_rrf")).lower()
        if reranker != "weighted_rrf":
            raise ValueError(f"Unsupported late_fusion reranker: {reranker}")

        evidence_top_k = int(self.config["evidence_top_k"])
        global_k = max(evidence_top_k, int(v2.get("global_candidate_k", 20)))
        graph_k = max(evidence_top_k, int(v2.get("graph_candidate_k", 20)))
        global_quota = min(
            evidence_top_k,
            max(0, int(v2.get("global_evidence_quota", min(3, evidence_top_k)))),
        )
        rrf_k = float(v2.get("rrf_k", 60.0))
        if rrf_k < 0:
            raise ValueError("late_fusion rrf_k must be non-negative")
        global_weight = float(v2.get("global_weight", 1.0))
        graph_weight = float(v2.get("graph_weight", 1.0))
        preserve_global_order = bool(v2.get("preserve_global_order", True))
        if global_weight < 0 or graph_weight < 0 or global_weight + graph_weight <= 0:
            raise ValueError("late_fusion branch weights must be non-negative and not both zero")

        global_ranked = self._top(hybrid_scores, global_k)
        graph_ranked = sorted(
            graph_candidates.items(),
            key=lambda item: (-float(item[1].get("score", 0.0)), item[0]),
        )[:graph_k]
        global_rank = {evidence_id: rank for rank, (evidence_id, _) in enumerate(global_ranked, 1)}
        graph_rank = {evidence_id: rank for rank, (evidence_id, _) in enumerate(graph_ranked, 1)}
        global_score = dict(global_ranked)

        fused: dict[str, dict[str, Any]] = {}
        for evidence_id in set(global_rank) | set(graph_rank):
            score = 0.0
            if evidence_id in global_rank:
                score += global_weight / (rrf_k + global_rank[evidence_id])
            if evidence_id in graph_rank:
                score += graph_weight / (rrf_k + graph_rank[evidence_id])
            graph_item = graph_candidates.get(evidence_id)
            if graph_item:
                item = dict(graph_item)
            else:
                item = {
                    "evidence_id": evidence_id,
                    "taskframe_id": "",
                    "fact_id": "",
                    "fact_relationship": "",
                    "taskmention_id": "",
                }
            in_global = evidence_id in global_rank
            in_graph = evidence_id in graph_rank
            item.update(
                {
                    "score": score,
                    "source": (
                        "late_fusion_both"
                        if in_global and in_graph
                        else "late_fusion_global"
                        if in_global
                        else "late_fusion_graph"
                    ),
                    "global_rank": global_rank.get(evidence_id),
                    "graph_rank": graph_rank.get(evidence_id),
                    "global_score": float(global_score.get(evidence_id, 0.0)),
                    "graph_score": (
                        float(graph_item.get("score", 0.0)) if graph_item else 0.0
                    ),
                }
            )
            fused[evidence_id] = item

        fused_ranked = sorted(
            fused.values(), key=lambda item: (-float(item["score"]), item["evidence_id"])
        )
        selected_ids = [evidence_id for evidence_id, _ in global_ranked[:global_quota]]
        for item in fused_ranked:
            evidence_id = item["evidence_id"]
            if evidence_id not in selected_ids:
                selected_ids.append(evidence_id)
            if len(selected_ids) >= evidence_top_k:
                break
        selected = [fused[evidence_id] for evidence_id in selected_ids if evidence_id in fused]
        if not preserve_global_order:
            selected.sort(key=lambda item: (-float(item["score"]), item["evidence_id"]))
        telemetry = {
            "reranker": reranker,
            "global_candidate_count": len(global_ranked),
            "graph_candidate_count": len(graph_ranked),
            "union_candidate_count": len(fused),
            "global_evidence_quota": global_quota,
            "preserve_global_order": preserve_global_order,
            "selected_global_count": sum(item["global_rank"] is not None for item in selected),
            "selected_graph_count": sum(item["graph_rank"] is not None for item in selected),
        }
        return selected, telemetry

    def _dual_path_candidates(
        self,
        base_candidates: Mapping[str, Mapping[str, Any]],
        aspect_candidates: Mapping[str, Mapping[str, Any]],
    ) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
        """Fuse the original-query base branch and an Aspect branch.

        The Aspect branch can be the legacy PCF-first path or the simplified
        direct-Evidence path. Rank/union fusion avoids treating their differently
        calibrated raw scores as if they were on the same scale.
        """
        config = self._aspect_config()
        fusion_mode = normalize_text(
            config.get("dual_path_fusion", "weighted_rrf")
        ).lower()
        if fusion_mode not in {"weighted_rrf", "base_preserving_union"}:
            raise ValueError(
                "dual_path_fusion must be weighted_rrf or base_preserving_union"
            )
        limit = max(
            int(self.config["evidence_top_k"]),
            int(config.get("dual_path_branch_candidate_k", 30)),
        )
        rrf_k = float(config.get("dual_path_rrf_k", 60.0))
        weights = {
            "base": float(config.get("dual_path_base_weight", 1.0)),
            "aspect": float(config.get("dual_path_aspect_weight", 1.0)),
        }
        if rrf_k < 0 or any(value < 0 for value in weights.values()):
            raise ValueError("Dual-path RRF settings must be non-negative")
        if sum(weights.values()) <= 0:
            raise ValueError("At least one dual-path branch weight must be positive")

        def ranked(
            candidates: Mapping[str, Mapping[str, Any]],
        ) -> list[tuple[str, Mapping[str, Any]]]:
            return sorted(
                candidates.items(),
                key=lambda item: (-float(item[1].get("score", 0.0)), item[0]),
            )[:limit]

        base_ranked = ranked(base_candidates)
        aspect_ranked = ranked(aspect_candidates)
        base_rank = {
            evidence_id: rank
            for rank, (evidence_id, _) in enumerate(base_ranked, start=1)
        }
        aspect_rank = {
            evidence_id: rank
            for rank, (evidence_id, _) in enumerate(aspect_ranked, start=1)
        }
        output: dict[str, dict[str, Any]] = {}
        novel_scale = float(config.get("dual_path_aspect_novel_scale", 1.0))
        if novel_scale < 0:
            raise ValueError("dual_path_aspect_novel_scale must be non-negative")
        for evidence_id in set(base_rank) | set(aspect_rank):
            base_item = base_candidates.get(evidence_id)
            aspect_item = aspect_candidates.get(evidence_id)
            available = [item for item in (base_item, aspect_item) if item is not None]
            preferred = max(
                available,
                key=lambda item: (
                    bool(
                        item.get("fact_id")
                        or item.get("taskmention_id")
                        or item.get("taskframe_id")
                    ),
                    normalize_text(item.get("source"))
                    != "global_evidence_fallback",
                    float(item.get("score", 0.0)),
                ),
            )
            # A P1-PARS candidate carries the exact stored-node/edge explanation
            # selected for this EvidenceSpan.  When the same evidence also
            # appears in the base PCF branch, keep that subgraph's representative
            # TaskFrame/Fact/TaskMention so the rendered path and provenance do
            # not accidentally describe a different base-branch route.
            if aspect_item is not None and aspect_item.get("subgraph_nodes"):
                preferred = aspect_item
            if fusion_mode == "base_preserving_union":
                if base_item is not None:
                    score = float(base_item.get("score", 0.0))
                else:
                    score = novel_scale * float(
                        (aspect_item or {}).get("score", 0.0)
                    )
            else:
                score = 0.0
                if evidence_id in base_rank:
                    score += weights["base"] / (rrf_k + base_rank[evidence_id])
                if evidence_id in aspect_rank:
                    score += weights["aspect"] / (rrf_k + aspect_rank[evidence_id])
            item = dict(preferred)
            item.update(
                {
                    "score": score,
                    "source": (
                        "dual_path_both"
                        if evidence_id in base_rank and evidence_id in aspect_rank
                        else "dual_path_base"
                        if evidence_id in base_rank
                        else "dual_path_aspect"
                    ),
                    "base_path_rank": base_rank.get(evidence_id),
                    "aspect_path_rank": aspect_rank.get(evidence_id),
                    "base_path_source": normalize_text(
                        (base_item or {}).get("source")
                    ),
                    "aspect_path_source": normalize_text(
                        (aspect_item or {}).get("source")
                    ),
                    "matched_aspect": normalize_text(
                        (aspect_item or {}).get("matched_aspect")
                    ),
                    "aspect_evidence_score": (aspect_item or {}).get(
                        "aspect_evidence_score"
                    ),
                    "subgraph_aspects": (aspect_item or {}).get(
                        "subgraph_aspects", []
                    ),
                    "subgraph_nodes": (aspect_item or {}).get(
                        "subgraph_nodes", []
                    ),
                    "subgraph_edges": (aspect_item or {}).get(
                        "subgraph_edges", []
                    ),
                    "subgraph_signals": (aspect_item or {}).get(
                        "subgraph_signals", {}
                    ),
                    "subgraph_rrf_score": (aspect_item or {}).get(
                        "subgraph_rrf_score"
                    ),
                    "subgraph_node_count": (aspect_item or {}).get(
                        "subgraph_node_count", 0
                    ),
                    "subgraph_edge_count": (aspect_item or {}).get(
                        "subgraph_edge_count", 0
                    ),
                }
            )
            output[evidence_id] = item
        telemetry = {
            "enabled": True,
            "reranker": fusion_mode,
            "rrf_k": rrf_k,
            "weights": weights,
            "branch_candidate_k": limit,
            "base_candidate_count": len(base_ranked),
            "aspect_candidate_count": len(aspect_ranked),
            "union_candidate_count": len(output),
            "intersection_candidate_count": len(set(base_rank) & set(aspect_rank)),
        }
        return output, telemetry

    def _p1p_three_path_candidates(
        self,
        base_candidates: Mapping[str, Mapping[str, Any]],
        direct_candidates: Mapping[str, Mapping[str, Any]],
        pars_candidates: Mapping[str, Mapping[str, Any]],
    ) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
        """Fuse PCF-first, direct-Aspect, and PARS branches without tuned weights.

        Direct Aspect retrieval protects candidate recall while PARS contributes
        graph-property precision and a stored-path explanation.  Equal RRF keeps
        the three differently calibrated raw scores comparable.  The branch
        candidate limit and RRF constant reuse the existing dual-path settings;
        this method introduces no additional numeric hyperparameter.
        """
        config = self._aspect_config()
        limit = max(
            int(self.config["evidence_top_k"]),
            int(config.get("dual_path_branch_candidate_k", 20)),
        )
        rrf_k = float(config.get("dual_path_rrf_k", 60.0))
        if rrf_k < 0:
            raise ValueError("P1-PARS three-path RRF k must be non-negative")

        def ranked(
            candidates: Mapping[str, Mapping[str, Any]],
        ) -> list[tuple[str, Mapping[str, Any]]]:
            return sorted(
                candidates.items(),
                key=lambda item: (-float(item[1].get("score", 0.0)), item[0]),
            )[:limit]

        branch_ranked = {
            "base": ranked(base_candidates),
            "direct": ranked(direct_candidates),
            "pars": ranked(pars_candidates),
        }
        branch_ranks = {
            name: {
                evidence_id: rank
                for rank, (evidence_id, _) in enumerate(values, start=1)
            }
            for name, values in branch_ranked.items()
        }
        evidence_ids = set().union(*(set(values) for values in branch_ranks.values()))
        output: dict[str, dict[str, Any]] = {}
        for evidence_id in evidence_ids:
            base_item = base_candidates.get(evidence_id)
            direct_item = direct_candidates.get(evidence_id)
            pars_item = pars_candidates.get(evidence_id)
            available = [
                item
                for item in (base_item, direct_item, pars_item)
                if item is not None
            ]
            preferred = max(
                available,
                key=lambda item: (
                    bool(
                        item.get("fact_id")
                        or item.get("taskmention_id")
                        or item.get("taskframe_id")
                    ),
                    normalize_text(item.get("source"))
                    != "global_evidence_fallback",
                    float(item.get("score", 0.0)),
                ),
            )
            if pars_item is not None and pars_item.get("subgraph_nodes"):
                preferred = pars_item
            score = sum(
                1.0 / (rrf_k + ranks[evidence_id])
                for ranks in branch_ranks.values()
                if evidence_id in ranks
            )
            present = [
                name for name, ranks in branch_ranks.items() if evidence_id in ranks
            ]
            item = dict(preferred)
            item.update(
                {
                    "score": score,
                    "source": "p1p_three_path_" + "_".join(present),
                    "base_path_rank": branch_ranks["base"].get(evidence_id),
                    "direct_aspect_path_rank": branch_ranks["direct"].get(
                        evidence_id
                    ),
                    "pars_path_rank": branch_ranks["pars"].get(evidence_id),
                    "aspect_path_rank": branch_ranks["pars"].get(evidence_id),
                    "base_path_source": normalize_text(
                        (base_item or {}).get("source")
                    ),
                    "direct_aspect_path_source": normalize_text(
                        (direct_item or {}).get("source")
                    ),
                    "pars_path_source": normalize_text(
                        (pars_item or {}).get("source")
                    ),
                    "matched_aspect": normalize_text(
                        (direct_item or {}).get("matched_aspect")
                    ),
                    "aspect_evidence_score": (direct_item or {}).get(
                        "aspect_evidence_score"
                    ),
                    "subgraph_aspects": (pars_item or {}).get(
                        "subgraph_aspects", []
                    ),
                    "subgraph_nodes": (pars_item or {}).get(
                        "subgraph_nodes", []
                    ),
                    "subgraph_edges": (pars_item or {}).get(
                        "subgraph_edges", []
                    ),
                    "subgraph_signals": (pars_item or {}).get(
                        "subgraph_signals", {}
                    ),
                    "subgraph_rrf_score": (pars_item or {}).get(
                        "subgraph_rrf_score"
                    ),
                    "subgraph_node_count": (pars_item or {}).get(
                        "subgraph_node_count", 0
                    ),
                    "subgraph_edge_count": (pars_item or {}).get(
                        "subgraph_edge_count", 0
                    ),
                }
            )
            output[evidence_id] = item

        return output, {
            "enabled": True,
            "reranker": "equal_weight_three_path_rrf",
            "rrf_k": rrf_k,
            "weights": {"base": 1.0, "direct_aspect": 1.0, "pars": 1.0},
            "branch_candidate_k": limit,
            "base_candidate_count": len(branch_ranked["base"]),
            "direct_aspect_candidate_count": len(branch_ranked["direct"]),
            "pars_candidate_count": len(branch_ranked["pars"]),
            "union_candidate_count": len(output),
            "triple_intersection_candidate_count": len(
                set(branch_ranks["base"])
                & set(branch_ranks["direct"])
                & set(branch_ranks["pars"])
            ),
        }

    def _direct_aspect_evidence_candidates(
        self,
        aspect_queries: Sequence[str],
    ) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
        """Search EvidenceSpan directly with a small set of Aspect queries.

        This is a query-time semantic/lexical association, not a Neo4j edge.
        Each EvidenceSpan keeps the score and text of its strongest matching
        Aspect. The final cross-encoder still compares all candidates against
        the original question, so this branch only broadens candidate recall.
        """
        config = self._aspect_config()
        query_limit = max(1, int(config.get("direct_evidence_query_k", 3)))
        candidate_limit = max(
            int(self.config["evidence_top_k"]),
            int(
                config.get(
                    "direct_evidence_candidate_k",
                    config.get("dual_path_branch_candidate_k", 30),
                )
            ),
        )
        queries = list(
            dict.fromkeys(
                normalize_text(value)
                for value in aspect_queries
                if normalize_text(value)
            )
        )[:query_limit]

        best: dict[str, tuple[float, str]] = {}
        for aspect_query in queries:
            vector = self.graph.question_vector(aspect_query)
            scores = self.graph.evidence_hybrid_scores(aspect_query, vector)
            for evidence_id, score in scores.items():
                value = float(score)
                previous = best.get(evidence_id)
                if previous is None or value > previous[0]:
                    best[evidence_id] = (value, aspect_query)

        ranked = sorted(
            best.items(),
            key=lambda item: (-item[1][0], item[0]),
        )[:candidate_limit]
        candidates = {
            evidence_id: {
                "evidence_id": evidence_id,
                "score": score,
                "source": "aspect_evidence_direct",
                "taskframe_id": "",
                "fact_id": "",
                "fact_relationship": "",
                "taskmention_id": "",
                "matched_aspect": matched_aspect,
                "aspect_evidence_score": score,
            }
            for evidence_id, (score, matched_aspect) in ranked
        }
        return candidates, {
            "mode": "query_time_direct_evidence",
            "queries": queries,
            "query_count": len(queries),
            "candidate_count": len(candidates),
            "candidate_k": candidate_limit,
            "stored_as_neo4j_edge": False,
        }

    def _materialize_property_relational_candidate(
        self,
        evidence_id: str,
        state: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Build a compact stored-path explanation for one ranked evidence."""
        queries = state["queries"]
        question_matches = state["question_matches"]
        aspect_matches = state["aspect_matches"]
        edge_scores = state["edge_scores"]
        details = state["details"]
        signal_names = state["signal_names"]
        ranks = state["ranks"]
        fused_score = state["fused_score"]
        value = details[evidence_id]
        terminal_ids = [
            value["question_node"],
            *value["aspect_nodes"],
            value["pcf_node"],
        ]
        node_ids, edge_ids = self.graph.minimal_evidence_subgraph(
            evidence_id,
            [node_id for node_id in terminal_ids if node_id],
            required_edge_id=value["best_edge_id"],
        )

        node_rows: list[dict[str, Any]] = []
        for node_id in node_ids:
            match_candidates: list[tuple[str, Mapping[str, Any]]] = []
            if node_id in question_matches:
                match_candidates.append(("question", question_matches[node_id]))
            for aspect, matches in zip(queries, aspect_matches):
                if node_id in matches:
                    match_candidates.append((f"aspect:{aspect}", matches[node_id]))
            matched_by = ""
            matched: Mapping[str, Any] = {}
            if match_candidates:
                matched_by, matched = max(
                    match_candidates,
                    key=lambda item: float(item[1].get("score", 0.0)),
                )
            node_rows.append(
                {
                    "label": self.graph.graph_node_labels.get(node_id, "Node"),
                    "id": node_id,
                    "name": self.graph.graph_node_names.get(node_id, ""),
                    "matched_by": matched_by,
                    "matched_property": matched.get("property_view", ""),
                    "matched_property_text": matched.get("property_text", ""),
                    "matched_score": float(matched.get("score", 0.0)),
                }
            )
        edge_rows = [
            {
                "id": edge_id,
                "from": self.graph.stored_graph_edges[edge_id].source,
                "type": self.graph.stored_graph_edges[edge_id].relation,
                "to": self.graph.stored_graph_edges[edge_id].target,
                "semantic_text": self.graph.stored_graph_edges[
                    edge_id
                ].semantic_text,
                "query_score": float(edge_scores.get(edge_id, 0.0)),
            }
            for edge_id in edge_ids
        ]

        selected_set = set(node_ids)
        fact_ids = [
            node_id
            for node_id in node_ids
            if self.graph.graph_node_labels.get(node_id) == "Fact"
        ]
        mention_ids = [
            node_id
            for node_id in node_ids
            if self.graph.graph_node_labels.get(node_id) == "TaskMention"
        ]
        frame_ids = [
            node_id
            for node_id in node_ids
            if self.graph.graph_node_labels.get(node_id) == "TaskFrame"
        ]

        def strongest(ids: Sequence[str]) -> str:
            return max(
                ids,
                key=lambda node_id: float(
                    question_matches.get(node_id, {}).get("score", 0.0)
                ),
                default="",
            )

        mention_id = strongest(mention_ids)
        frame_id = strongest(frame_ids)
        fact_id = ""
        fact_relationship = ""
        linked_facts: list[tuple[str, str, str]] = []
        for edge_id in edge_ids:
            edge = self.graph.stored_graph_edges[edge_id]
            if (
                edge.target in fact_ids
                and edge.source in selected_set
                and edge.relation in FACT_RELATION_WEIGHT
            ):
                linked_facts.append((edge.target, edge.source, edge.relation))
        if linked_facts:
            fact_id, frame_id, fact_relationship = max(
                linked_facts,
                key=lambda item: float(
                    question_matches.get(item[0], {}).get("score", 0.0)
                ),
            )

        return {
            "evidence_id": evidence_id,
            "score": fused_score[evidence_id],
            "source": "property_relational_subgraph",
            "taskframe_id": frame_id,
            "fact_id": fact_id,
            "fact_relationship": fact_relationship,
            "taskmention_id": mention_id,
            "subgraph_aspects": queries,
            "subgraph_nodes": node_rows,
            "subgraph_edges": edge_rows,
            "subgraph_signals": {
                name: {
                    "value": float(value[name]),
                    "rank": ranks[name][evidence_id],
                }
                for name in signal_names
            },
            "subgraph_rrf_score": fused_score[evidence_id],
            "subgraph_node_count": len(node_rows),
            "subgraph_edge_count": len(edge_rows),
        }

    def _property_relational_subgraph_candidates(
        self,
        *,
        question: str,
        query_vector: np.ndarray,
        aspect_queries: Sequence[str],
        pcf_candidates: Sequence[Mapping[str, Any]],
        condition: str,
    ) -> tuple[dict[str, dict[str, Any]], dict[str, Any], dict[str, Any]]:
        """Rank compact Evidence-rooted subgraphs across the complete schema.

        P1-PARS treats node-property relevance, Aspect coverage, semantic edge
        support, PCF-anchor consistency, and direct Evidence relevance as five
        separate rankings. Their reciprocal ranks are averaged without learned
        or hand-tuned feature weights. The selected explanation is a union of
        shortest *stored* paths from each winning terminal to its EvidenceSpan.
        """
        config = self._aspect_config()
        query_limit = max(1, int(config.get("direct_evidence_query_k", 3)))
        queries = list(
            dict.fromkeys(
                normalize_text(value)
                for value in aspect_queries
                if normalize_text(value)
            )
        )[:query_limit]
        aspect_vectors = [self.graph.question_vector(value) for value in queries]
        question_matches = self.graph.schema_property_matches(
            query_vector,
            condition=condition,
        )
        aspect_matches = [
            self.graph.schema_property_matches(vector, condition=condition)
            for vector in aspect_vectors
        ]
        edge_scores = self.graph.edge_lexical_scores(
            compact_join([question, *queries], " ")
        )
        evidence_scores = self.graph.evidence_hybrid_scores(
            question,
            query_vector,
        )

        def allowed_node(node_id: str) -> bool:
            label = self.graph.graph_node_labels.get(node_id)
            if label == "Fact":
                return self._allow_v2_fact(self.graph.facts[node_id])
            if label == "TaskMention":
                return self._allow_v2_taskmention(
                    self.graph.taskmentions[node_id]
                )
            return True

        def best_node(
            node_ids: Iterable[str],
            matches: Mapping[str, Mapping[str, Any]],
        ) -> tuple[str, float]:
            values = [
                (node_id, float(matches[node_id]["score"]))
                for node_id in node_ids
                if node_id in matches and allowed_node(node_id)
            ]
            if not values:
                return "", 0.0
            return max(values, key=lambda item: (item[1], item[0]))

        details: dict[str, dict[str, Any]] = {}
        anchor_ids = [
            normalize_text(item.get("id"))
            for item in pcf_candidates
            if normalize_text(item.get("id"))
        ]
        for evidence_id in self.graph.evidence:
            closure_nodes = self.graph.evidence_support_nodes.get(
                evidence_id, frozenset({evidence_id})
            )
            closure_edges = self.graph.evidence_support_edges.get(
                evidence_id, frozenset()
            )
            question_node, question_score = best_node(
                closure_nodes,
                question_matches,
            )
            aspect_nodes: list[str] = []
            aspect_values: list[float] = []
            for matches in aspect_matches:
                node_id, value = best_node(closure_nodes, matches)
                aspect_nodes.append(node_id)
                aspect_values.append(value)
            aspect_coverage = (
                float(np.mean(aspect_values)) if aspect_values else question_score
            )
            best_edge_id = ""
            edge_support = 0.0
            if closure_edges:
                best_edge_id = max(
                    closure_edges,
                    key=lambda edge_id: (
                        float(edge_scores.get(edge_id, 0.0)),
                        edge_id,
                    ),
                )
                edge_support = float(edge_scores.get(best_edge_id, 0.0))

            pcf_node = ""
            pcf_anchor = 0.0
            for node_id in closure_nodes:
                if self.graph.graph_node_labels.get(node_id) != "PCFProcess":
                    continue
                for anchor_id in anchor_ids:
                    distance = self.graph.pcf_distance(anchor_id, node_id)
                    if distance is None:
                        continue
                    value = 1.0 / (1.0 + float(distance))
                    if value > pcf_anchor:
                        pcf_anchor = value
                        pcf_node = node_id

            details[evidence_id] = {
                "question_property": question_score,
                "aspect_coverage": aspect_coverage,
                "edge_support": edge_support,
                "pcf_anchor": pcf_anchor,
                "evidence_relevance": float(
                    evidence_scores.get(evidence_id, 0.0)
                ),
                "question_node": question_node,
                "aspect_nodes": aspect_nodes,
                "aspect_values": aspect_values,
                "pcf_node": pcf_node,
                "best_edge_id": best_edge_id,
            }

        signal_names = (
            "question_property",
            "aspect_coverage",
            "edge_support",
            "pcf_anchor",
            "evidence_relevance",
        )

        def dense_ranks(name: str) -> dict[str, int]:
            distinct = sorted(
                {float(value[name]) for value in details.values()},
                reverse=True,
            )
            by_value = {
                value: rank for rank, value in enumerate(distinct, start=1)
            }
            return {
                evidence_id: by_value[float(value[name])]
                for evidence_id, value in details.items()
            }

        ranks = {name: dense_ranks(name) for name in signal_names}
        fused_score = {
            evidence_id: sum(
                1.0 / ranks[name][evidence_id] for name in signal_names
            )
            / len(signal_names)
            for evidence_id in details
        }
        limit = max(
            int(self.config["evidence_top_k"]),
            int(config.get("dual_path_branch_candidate_k", 20)),
        )
        ranked_ids = sorted(
            details,
            key=lambda evidence_id: (
                -fused_score[evidence_id],
                evidence_id,
            ),
        )[:limit]

        state: dict[str, Any] = {
            "queries": queries,
            "question_matches": question_matches,
            "aspect_matches": aspect_matches,
            "edge_scores": edge_scores,
            "details": details,
            "signal_names": signal_names,
            "ranks": ranks,
            "fused_score": fused_score,
        }
        candidates = {
            evidence_id: self._materialize_property_relational_candidate(
                evidence_id, state
            )
            for evidence_id in ranked_ids
        }

        return candidates, {
            "mode": "pcf_anchored_property_relational_subgraph",
            "method": "PARS-KG-RAG",
            "queries": queries,
            "signal_names": list(signal_names),
            "aggregation": "equal_weight_reciprocal_rank_sum",
            "candidate_count": len(candidates),
            "candidate_k": limit,
            "stored_node_types": sorted(
                set(self.graph.graph_node_labels.values())
            ),
            "stored_edge_types": sorted(
                {edge.relation for edge in self.graph.stored_graph_edges.values()}
            ),
            "virtual_edges_created": 0,
        }, state

    def _p0_cross_encoder_mmr_candidates(
        self,
        *,
        question: str,
        p0_candidates: Mapping[str, Mapping[str, Any]],
        candidate_k_override: int | None = None,
        quota_rank_field: str = "",
        aspect_queries: Sequence[str] | None = None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Rerank P0's own candidate list without changing its retrieval path."""
        if self.cross_encoder is None:
            raise RuntimeError("P1 requires a configured cross-encoder reranker")
        p1 = self._p1_config()
        evidence_top_k = int(self.config["evidence_top_k"])
        candidate_k = max(
            evidence_top_k,
            int(
                candidate_k_override
                if candidate_k_override is not None
                else p1.get("candidate_k", 20)
            ),
        )
        configured_quota = p1.get("p0_evidence_quota", 2)
        if aspect_queries:
            configured_quota = self._aspect_config().get(
                "rerank_base_path_quota", configured_quota
            )
        p0_quota = min(
            evidence_top_k,
            max(0, int(configured_quota)),
        )
        rrf_k = float(p1.get("rrf_k", 60.0))
        weights = {
            "p0": float(p1.get("p0_weight", 1.0)),
            "cross_encoder": float(p1.get("cross_encoder_weight", 2.0)),
            "aspect_cross_encoder": float(
                self._aspect_config().get("rerank_cross_encoder_weight", 0.0)
                if aspect_queries
                else 0.0
            ),
        }
        if rrf_k < 0 or any(value < 0 for value in weights.values()):
            raise ValueError("P1 RRF settings must be non-negative")
        if sum(weights.values()) <= 0:
            raise ValueError("At least one P1 RRF branch weight must be positive")
        configured_mmr_lambda = p1.get("mmr_lambda", 0.90)
        if aspect_queries:
            configured_mmr_lambda = self._aspect_config().get(
                "rerank_mmr_lambda", configured_mmr_lambda
            )
        mmr_lambda = float(configured_mmr_lambda)
        if not 0.0 <= mmr_lambda <= 1.0:
            raise ValueError("P1 mmr_lambda must be between zero and one")

        p0_ranked = sorted(
            p0_candidates.items(),
            key=lambda item: (-float(item[1].get("score", 0.0)), item[0]),
        )[:candidate_k]
        p0_rank = {
            evidence_id: rank for rank, (evidence_id, _) in enumerate(p0_ranked, 1)
        }
        p0_score = {
            evidence_id: float(item.get("score", 0.0))
            for evidence_id, item in p0_ranked
        }
        candidate_ids = sorted(p0_rank)
        passages = [normalize_text(self.graph.evidence[item].get("name")) for item in candidate_ids]
        cross_values = self.cross_encoder.score(question, passages)
        cross_score = dict(zip(candidate_ids, cross_values))
        cross_ranked = sorted(candidate_ids, key=lambda item: (-cross_score[item], item))
        cross_rank = {evidence_id: rank for rank, evidence_id in enumerate(cross_ranked, 1)}

        aspect_query_limit = max(
            1,
            int(self._aspect_config().get("rerank_query_k", 3)),
        )
        cleaned_aspect_queries = list(
            dict.fromkeys(
                normalize_text(value)
                for value in (aspect_queries or [])
                if normalize_text(value)
                and normalize_text(value) != normalize_text(question)
            )
        )[:aspect_query_limit]
        aspect_cross_score: dict[str, float] = {}
        aspect_cross_rank: dict[str, int] = {}
        if cleaned_aspect_queries and weights["aspect_cross_encoder"] > 0:
            per_query: list[dict[str, float]] = []
            for aspect_query in cleaned_aspect_queries:
                raw = dict(
                    zip(
                        candidate_ids,
                        self.cross_encoder.score(aspect_query, passages),
                    )
                )
                minimum = min(raw.values()) if raw else 0.0
                maximum = max(raw.values()) if raw else 0.0
                denominator = maximum - minimum
                per_query.append(
                    {
                        evidence_id: (
                            (value - minimum) / denominator
                            if denominator > 0
                            else 1.0
                        )
                        for evidence_id, value in raw.items()
                    }
                )
            max_weight = float(
                self._aspect_config().get("rerank_max_weight", 0.75)
            )
            top_n = max(1, int(self._aspect_config().get("rerank_top_n", 2)))
            if not 0.0 <= max_weight <= 1.0:
                raise ValueError("rerank_max_weight must be between zero and one")
            for evidence_id in candidate_ids:
                values = sorted(
                    (scores[evidence_id] for scores in per_query),
                    reverse=True,
                )
                aspect_cross_score[evidence_id] = (
                    max_weight * values[0]
                    + (1.0 - max_weight) * float(np.mean(values[:top_n]))
                )
            aspect_ranked = sorted(
                candidate_ids,
                key=lambda item: (-aspect_cross_score[item], item),
            )
            aspect_cross_rank = {
                evidence_id: rank
                for rank, evidence_id in enumerate(aspect_ranked, 1)
            }

        fused: dict[str, dict[str, Any]] = {}
        for evidence_id in candidate_ids:
            score = weights["cross_encoder"] / (rrf_k + cross_rank[evidence_id])
            score += weights["p0"] / (rrf_k + p0_rank[evidence_id])
            if evidence_id in aspect_cross_rank:
                score += weights["aspect_cross_encoder"] / (
                    rrf_k + aspect_cross_rank[evidence_id]
                )
            item = dict(p0_candidates[evidence_id])
            original_source = normalize_text(item.get("source"))
            item.update(
                {
                    "score": score,
                    "source": f"p1_reranked_{original_source}",
                    "original_source": original_source,
                    "p0_rank": p0_rank[evidence_id],
                    "cross_encoder_rank": cross_rank[evidence_id],
                    "p0_score": p0_score[evidence_id],
                    "cross_encoder_score": cross_score[evidence_id],
                    "aspect_cross_encoder_rank": aspect_cross_rank.get(evidence_id),
                    "aspect_cross_encoder_score": aspect_cross_score.get(evidence_id),
                }
            )
            fused[evidence_id] = item

        fused_values = [float(item["score"]) for item in fused.values()]
        minimum = min(fused_values) if fused_values else 0.0
        maximum = max(fused_values) if fused_values else 0.0
        denominator = maximum - minimum
        relevance = {
            evidence_id: (
                (float(item["score"]) - minimum) / denominator if denominator > 0 else 1.0
            )
            for evidence_id, item in fused.items()
        }

        if quota_rank_field:
            quota_ranked = sorted(
                (
                    (evidence_id, int(item[quota_rank_field]))
                    for evidence_id, item in p0_ranked
                    if item.get(quota_rank_field) is not None
                ),
                key=lambda value: (value[1], value[0]),
            )
            required_ids = [
                evidence_id for evidence_id, _ in quota_ranked[:p0_quota]
            ]
        else:
            required_ids = [evidence_id for evidence_id, _ in p0_ranked[:p0_quota]]
        selected_ids = list(dict.fromkeys(required_ids))
        evidence_index = self.graph.indices["evidence"]
        positions = {item: index for index, item in enumerate(evidence_index.ids)}
        text_matrix = evidence_index.matrices["text"]
        use_section_penalty = bool(p1.get("same_section_penalty", True))

        while len(selected_ids) < evidence_top_k and len(selected_ids) < len(candidate_ids):
            best_id = ""
            best_key: tuple[float, float, float, str] | None = None
            for evidence_id in candidate_ids:
                if evidence_id in selected_ids:
                    continue
                redundancy = 0.0
                candidate_vector = text_matrix[positions[evidence_id]]
                candidate_section = normalize_text(
                    self.graph.evidence[evidence_id].get("section_path")
                )
                for selected_id in selected_ids:
                    similarity = max(
                        0.0,
                        float(candidate_vector @ text_matrix[positions[selected_id]]),
                    )
                    redundancy = max(redundancy, similarity)
                    selected_section = normalize_text(
                        self.graph.evidence[selected_id].get("section_path")
                    )
                    if (
                        use_section_penalty
                        and candidate_section
                        and candidate_section == selected_section
                    ):
                        redundancy = 1.0
                mmr_score = mmr_lambda * relevance[evidence_id] - (
                    1.0 - mmr_lambda
                ) * redundancy
                key = (
                    mmr_score,
                    relevance[evidence_id],
                    cross_score[evidence_id],
                    evidence_id,
                )
                if best_key is None or key > best_key:
                    best_key = key
                    best_id = evidence_id
            if not best_id:
                break
            selected_ids.append(best_id)

        selected = [fused[evidence_id] for evidence_id in selected_ids]
        selected.sort(key=lambda item: (-float(item["score"]), item["evidence_id"]))
        telemetry = {
            "reranker": "p0_cross_encoder_weighted_rrf_mmr",
            "model": getattr(self.cross_encoder, "model_id", "test-double"),
            "revision": getattr(self.cross_encoder, "revision", "test-double"),
            "candidate_count": len(candidate_ids),
            "p0_candidate_count": len(p0_ranked),
            "p0_evidence_quota": p0_quota,
            "quota_rank_field": quota_rank_field,
            "rrf_k": rrf_k,
            "weights": weights,
            "aspect_queries": cleaned_aspect_queries,
            "mmr_lambda": mmr_lambda,
            "same_section_penalty": use_section_penalty,
            "selected_original_graph_count": sum(
                item.get("original_source") in {"fact_path", "taskmention_path"}
                for item in selected
            ),
            "selected_global_fallback_count": sum(
                item.get("original_source") == "global_evidence_fallback"
                for item in selected
            ),
        }
        if bool(self._aspect_config().get("emit_candidate_diagnostics", False)):
            telemetry["candidate_diagnostics"] = [
                {
                    "evidence_id": evidence_id,
                    "source": normalize_text(
                        p0_candidates[evidence_id].get("source")
                    ),
                    "p0_rank": p0_rank[evidence_id],
                    "p0_score": p0_score[evidence_id],
                    "cross_encoder_rank": cross_rank[evidence_id],
                    "cross_encoder_score": cross_score[evidence_id],
                    "aspect_cross_encoder_rank": aspect_cross_rank.get(evidence_id),
                    "aspect_cross_encoder_score": aspect_cross_score.get(evidence_id),
                    "base_path_rank": p0_candidates[evidence_id].get(
                        "base_path_rank"
                    ),
                    "aspect_path_rank": p0_candidates[evidence_id].get(
                        "aspect_path_rank"
                    ),
                    "section_path": normalize_text(
                        self.graph.evidence[evidence_id].get("section_path")
                    ),
                }
                for evidence_id in candidate_ids
            ]
        return selected, telemetry

    def _add_global_fallback(
        self,
        candidates: dict[str, dict[str, Any]],
        hybrid_scores: Mapping[str, float],
    ) -> bool:
        evidence_top_k = int(self.config["evidence_top_k"])
        graph_ids = set(candidates)
        for evidence_id, candidate in candidates.items():
            candidate["score"] = (
                0.55 * float(candidate["score"])
                + 0.45 * float(hybrid_scores.get(evidence_id, 0.0))
                + 0.03
            )
        for evidence_id, score in self._top(hybrid_scores, max(20, evidence_top_k * 4)):
            adjusted = score * 0.85
            if evidence_id not in candidates or adjusted > candidates[evidence_id]["score"]:
                candidates[evidence_id] = {
                    "evidence_id": evidence_id,
                    "score": adjusted,
                    "source": "global_evidence_fallback",
                    "taskframe_id": "",
                    "fact_id": "",
                    "fact_relationship": "",
                    "taskmention_id": "",
                }
        return any(evidence_id not in graph_ids for evidence_id in candidates)

    def _render_context(
        self,
        *,
        method: str,
        condition: str,
        profile: Mapping[str, Any],
        pcf_candidates: Sequence[Mapping[str, Any]],
        taskframes: Sequence[Mapping[str, Any]],
        selected: Sequence[dict[str, Any]],
    ) -> str:
        max_chars = int(self.config["context_max_chars"])
        signal_chunks: list[str] = []
        if method not in {"B0_VANILLA_DENSE_RAG", "B0_EVIDENCE_HYBRID"}:
            signal_chunks.append(
                "[PCF CLASSIFICATION; not standalone factual evidence]\n"
                + "\n".join(
                    f"- {item['id']} | {item['name']} | level={item['level']} | path={item['path']}"
                    for item in pcf_candidates
                )
            )
            signal_chunks.append(
                "[TASKFRAME CANDIDATES]\n"
                + ("\n".join(f"- {item['id']} | {item['name']}" for item in taskframes) or "- none")
            )
            if method in QUERY_PROFILE_METHODS and method in {
                "P0_QPA",
                "A2_NO_GAP_ADAPTATION",
                "V2_EVIDENCE_GRAPH_LATE_FUSION",
                *P1_RERANK_METHODS,
            }:
                signal_chunks.append(
                    "[QUERY-ACTIVATED FACETS]\n"
                    f"- answer_shape={profile.get('answer_shape')}\n"
                    f"- facets={', '.join(profile.get('target_facets', []))}\n"
                    f"- knowledge_functions={', '.join(profile.get('knowledge_functions', []))}"
                )

        evidence_chunks: list[str] = []
        for index, item in enumerate(selected, start=1):
            evidence = self.graph.evidence[item["evidence_id"]]
            lines = [
                f"[E{index}]",
                f"text: {normalize_text(evidence.get('name'))}",
                f"source: {evidence.get('source_file', '')}; page={evidence.get('page', '')}; section={evidence.get('section_path', '')}",
                f"evidence_id: {item['evidence_id']}",
            ]
            subgraph_nodes = item.get("subgraph_nodes", [])
            subgraph_edges = item.get("subgraph_edges", [])
            if isinstance(subgraph_nodes, list) and subgraph_nodes:
                matched = sorted(
                    (
                        node
                        for node in subgraph_nodes
                        if normalize_text(node.get("matched_by"))
                    ),
                    key=lambda node: (
                        -float(node.get("matched_score", 0.0)),
                        normalize_text(node.get("id")),
                    ),
                )[:3]
                if matched:
                    def clipped_property(node: Mapping[str, Any]) -> str:
                        text = normalize_text(node.get("matched_property_text"))
                        return text if len(text) <= 180 else text[:177] + "..."

                    lines.append(
                        "matched_node_properties: "
                        + " | ".join(
                            f"{node.get('label')}({node.get('id')})."
                            f"{node.get('matched_property')}="
                            f"{clipped_property(node)}"
                            for node in matched
                        )
                    )
            if isinstance(subgraph_edges, list) and subgraph_edges:
                lines.append(
                    "stored_subgraph_edges: "
                    + " | ".join(
                        f"{edge.get('from')}-[{edge.get('type')}]->{edge.get('to')}"
                        for edge in subgraph_edges[:8]
                    )
                )
            matched_aspect = normalize_text(item.get("matched_aspect"))
            if matched_aspect:
                lines.append(
                    "query_route: "
                    f'Aspect("{matched_aspect}") -> EvidenceSpan '
                    "(query-time match; not a stored Neo4j edge)"
                )
            frame_id = item.get("taskframe_id")
            if frame_id and frame_id in self.graph.taskframes:
                lines.append(
                    f"graph_path: TaskFrame({self.graph.taskframes[frame_id].get('name', frame_id)})"
                )
            fact_id = item.get("fact_id")
            if fact_id and fact_id in self.graph.facts:
                fact = self.graph.facts[fact_id]
                lines[-1] += (
                    f" -[{item.get('fact_relationship', '')}]-> Fact({fact_id})"
                    " -[SUPPORTED_BY]-> EvidenceSpan"
                )
                if condition == "D0_ORIGINAL":
                    lines.extend(
                        [
                            f"fact_triple: {compact_join([fact.get('subject_canonical'), fact.get('predicate_canonical'), fact.get('object_canonical')], ' / ')}",
                            f"fact_qualifiers: {_qualifier_text(fact.get('qualifiers'))}",
                            f"knowledge_function: {fact.get('knowledge_function', '')}",
                        ]
                    )
            mention_id = item.get("taskmention_id")
            if mention_id and mention_id in self.graph.taskmentions:
                mention = self.graph.taskmentions[mention_id]
                lines[-1] += " -[MEMBER_OF]-(TaskMention)-[SUPPORTED_BY]-> EvidenceSpan"
                if condition == "D0_ORIGINAL":
                    lines.append(
                        "task_slots: "
                        + compact_join(
                            [
                                mention.get("action_raw"),
                                mention.get("focal_object_raw"),
                                mention.get("intended_outcome_raw"),
                            ],
                            " / ",
                        )
                    )
            chunk = "\n".join(line for line in lines if not line.endswith(": "))
            evidence_chunks.append(chunk)

        if method != "V2_EVIDENCE_GRAPH_LATE_FUSION":
            # Preserve the v1 context construction exactly for reproducibility.
            chunks = list(signal_chunks)
            for chunk in evidence_chunks:
                if sum(len(value) for value in chunks) + len(chunk) > max_chars:
                    break
                chunks.append(chunk)
            return "\n\n".join(chunks)[:max_chars]

        # V2 presents factual evidence before classification metadata so the
        # answer model cannot spend the context budget on soft graph signals.
        ordered = evidence_chunks + signal_chunks
        chunks: list[str] = []
        current_length = 0
        for chunk in ordered:
            separator_length = 2 if chunks else 0
            if current_length + separator_length + len(chunk) > max_chars:
                break
            chunks.append(chunk)
            current_length += separator_length + len(chunk)
        return "\n\n".join(chunks)

    def retrieve(
        self,
        *,
        qid: str,
        question: str,
        method: str,
        condition: str,
        profile: Mapping[str, Any] | None = None,
        aspects: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        if method not in METHODS:
            raise ValueError(f"Unknown method: {method}")
        if condition not in CONDITIONS:
            raise ValueError(f"Unknown condition: {condition}")
        query_vector = self.graph.question_vector(question)
        pcf_candidates: list[dict[str, Any]] = []
        taskframes: list[dict[str, Any]] = []
        taskmentions: list[dict[str, Any]] = []
        facts: list[dict[str, Any]] = []
        used_tf_gap = False
        used_evidence_gap = False
        selected: list[dict[str, Any]] | None = None
        fusion_telemetry: dict[str, Any] = {}
        pars_state: dict[str, Any] | None = None
        retrieval_strategy = ""
        query_profile_used = method in QUERY_PROFILE_METHODS
        active_profile = dict(profile or {}) if query_profile_used else {}
        if query_profile_used and not active_profile:
            raise ValueError(f"{method} requires a non-empty Query Profile")
        aspect_used = method in ASPECT_METHODS
        if aspect_used and not aspects:
            raise ValueError(f"{method} requires a non-empty question Aspect profile")

        if method == "B0_VANILLA_DENSE_RAG":
            dense_scores = self.graph.evidence_dense_scores(question, query_vector)
            candidates = {
                evidence_id: {
                    "evidence_id": evidence_id,
                    "score": score,
                    "source": "global_evidence_dense",
                    "taskframe_id": "",
                    "fact_id": "",
                    "fact_relationship": "",
                    "taskmention_id": "",
                }
                for evidence_id, score in dense_scores.items()
            }
            retrieval_strategy = "evidence_text_embedding_cosine_only"
        elif method == "B0_EVIDENCE_HYBRID":
            hybrid_scores = self.graph.evidence_hybrid_scores(question, query_vector)
            candidates = {
                evidence_id: {
                    "evidence_id": evidence_id,
                    "score": score,
                    "source": "global_evidence_hybrid",
                    "taskframe_id": "",
                    "fact_id": "",
                    "fact_relationship": "",
                    "taskmention_id": "",
                }
                for evidence_id, score in hybrid_scores.items()
            }
            retrieval_strategy = "evidence_dense_bm25_hybrid"
        elif method == "V2_EVIDENCE_GRAPH_LATE_FUSION":
            hybrid_scores = self.graph.evidence_hybrid_scores(question, query_vector)
            pcf_candidates = self._pcf_candidates_v2(query_vector)
            taskframes = self._taskframe_candidates_v2(
                query_vector,
                pcf_candidates,
                condition=condition,
            )
            candidates, taskmentions, facts = self._graph_evidence(
                query_vector=query_vector,
                question=question,
                taskframes=taskframes,
                profile=active_profile,
                condition=condition,
                fixed_properties=False,
                filter_low_quality=bool(
                    self._v2_config().get("filter_low_quality_nodes", True)
                ),
            )
            selected, fusion_telemetry = self._late_fusion_candidates(
                candidates, hybrid_scores
            )
            retrieval_strategy = "evidence_graph_late_fusion"
        else:
            hybrid_scores = self.graph.evidence_hybrid_scores(question, query_vector)
            aspect_vectors: dict[
                str, np.ndarray | Sequence[np.ndarray]
            ] = {}
            aspect_weights = {"pcf": 0.0, "taskframe": 0.0, "fact": 0.0}
            aspect_applicability = 0.0
            aspect_applied = False
            aspect_rerank_queries: list[str] = []
            aspect_routing_mode = "none"
            if aspect_used:
                aspect_config = self._aspect_config()
                aspect_routing_mode = normalize_text(
                    aspect_config.get("routing_mode", "layered")
                ).lower()
                if aspect_routing_mode not in {"layered", "direct_evidence"}:
                    raise ValueError(
                        "aspect routing_mode must be layered or direct_evidence"
                    )
                if method in PROFILE_FREE_ASPECT_METHODS:
                    # Profile-free Aspect methods have no routing gate:
                    # all selected P1-G Aspects (up to three) enter both
                    # Aspect branches.
                    aspect_applicability = 1.0
                    aspect_applied = True
                else:
                    applicability = (aspects or {}).get("applicability", {})
                    if isinstance(applicability, Mapping):
                        aspect_applicability = float(applicability.get("score", 1.0))
                    else:
                        aspect_applicability = 1.0
                    gate_threshold = float(
                        aspect_config.get("selective_gate_threshold", 0.0)
                    )
                    if not 0.0 <= gate_threshold <= 1.0:
                        raise ValueError(
                            "aspect selective_gate_threshold must be between zero and one"
                        )
                    aspect_applied = aspect_applicability >= gate_threshold
                if aspect_applied:
                    raw_queries = (aspects or {}).get(
                        "rerank_terms",
                        (aspects or {}).get("search_terms", []),
                    )
                    if isinstance(raw_queries, list):
                        aspect_rerank_queries = [
                            normalize_text(value)
                            for value in raw_queries
                            if normalize_text(value)
                        ]
                    if not aspect_rerank_queries:
                        for field in (
                            "desired_information",
                            "constraints",
                            "actions",
                            "domain_objects",
                        ):
                            raw_values = (aspects or {}).get(field, [])
                            if isinstance(raw_values, list):
                                aspect_rerank_queries.extend(
                                    normalize_text(value)
                                    for value in raw_values
                                    if normalize_text(value)
                                )
                    aspect_rerank_queries = list(
                        dict.fromkeys(aspect_rerank_queries)
                    )
                if aspect_routing_mode == "layered":
                    if aspect_applied and bool(
                        aspect_config.get("multivector_enabled", False)
                    ):
                        aspect_vectors = self.graph.aspect_multivectors(
                            aspects or {},
                            max_terms_per_stage=int(
                                aspect_config.get("multivector_max_terms_per_stage", 5)
                            ),
                        )
                    elif aspect_applied:
                        aspect_vectors = self.graph.aspect_vectors(aspects or {})
                    aspect_weights = self._aspect_stage_weights()
                    if not aspect_applied:
                        aspect_weights = {
                            "pcf": 0.0,
                            "taskframe": 0.0,
                            "fact": 0.0,
                        }
            pcf_candidates = self._pcf_candidates(
                query_vector,
                aspect_vector=aspect_vectors.get("pcf"),
                aspect_weight=aspect_weights["pcf"],
            )
            allow_gap = method != "A2_NO_GAP_ADAPTATION"
            taskframes, used_tf_gap = self._taskframe_candidates(
                query_vector,
                pcf_candidates,
                condition=condition,
                allow_gap_adaptation=allow_gap,
                aspect_vector=aspect_vectors.get("taskframe"),
                aspect_weight=aspect_weights["taskframe"],
            )
            candidates, taskmentions, facts = self._graph_evidence(
                query_vector=query_vector,
                question=question,
                taskframes=taskframes,
                profile=active_profile,
                condition=condition,
                fixed_properties=method in FIXED_PROPERTY_METHODS,
                aspect_vector=aspect_vectors.get("fact"),
                aspect_weight=aspect_weights["fact"],
            )
            if allow_gap:
                used_evidence_gap = self._add_global_fallback(candidates, hybrid_scores)
            dual_path_telemetry: dict[str, Any] = {}
            uses_aspect_branch = (
                method in ASPECT_METHODS
                and aspect_applied
                and bool(self._aspect_config().get("dual_path_enabled", False))
            )
            if uses_aspect_branch:
                if aspect_routing_mode == "direct_evidence":
                    if method in {P1P_PARS, P1P_PARS_PROFILE_FREE}:
                        pars_candidates, pars_telemetry, pars_state = (
                            self._property_relational_subgraph_candidates(
                                question=question,
                                query_vector=query_vector,
                                aspect_queries=aspect_rerank_queries,
                                pcf_candidates=pcf_candidates,
                                condition=condition,
                            )
                        )
                        direct_candidates, direct_telemetry = (
                            self._direct_aspect_evidence_candidates(
                                aspect_rerank_queries
                            )
                        )
                        candidates, dual_path_telemetry = (
                            self._p1p_three_path_candidates(
                                candidates,
                                direct_candidates,
                                pars_candidates,
                            )
                        )
                        dual_path_telemetry["aspect_route"] = {
                            "mode": "pcf_anchored_property_relational_subgraph_with_direct_recall",
                            "direct_aspect": direct_telemetry,
                            "pars": pars_telemetry,
                            "virtual_edges_created": 0,
                        }
                    else:
                        aspect_candidates, direct_telemetry = (
                            self._direct_aspect_evidence_candidates(
                                aspect_rerank_queries
                            )
                        )
                        candidates, dual_path_telemetry = self._dual_path_candidates(
                            candidates,
                            aspect_candidates,
                        )
                        dual_path_telemetry["aspect_route"] = direct_telemetry
                else:
                    base_pcfs = self._pcf_candidates(query_vector)
                    base_taskframes, base_tf_gap = self._taskframe_candidates(
                        query_vector,
                        base_pcfs,
                        condition=condition,
                        allow_gap_adaptation=allow_gap,
                    )
                    base_candidates, _, _ = self._graph_evidence(
                        query_vector=query_vector,
                        question=question,
                        taskframes=base_taskframes,
                        profile=active_profile,
                        condition=condition,
                        fixed_properties=method in FIXED_PROPERTY_METHODS,
                    )
                    base_evidence_gap = False
                    if allow_gap:
                        base_evidence_gap = self._add_global_fallback(
                            base_candidates,
                            hybrid_scores,
                        )
                    candidates, dual_path_telemetry = self._dual_path_candidates(
                        base_candidates,
                        candidates,
                    )
                    used_tf_gap = used_tf_gap or base_tf_gap
                    used_evidence_gap = used_evidence_gap or base_evidence_gap
            if method in P1_RERANK_METHODS:
                dual_candidate_k = None
                quota_rank_field = ""
                if uses_aspect_branch:
                    dual_candidate_k = int(
                        self._aspect_config().get(
                            "dual_path_rerank_candidate_k",
                            self._p1_config().get("candidate_k", 20),
                        )
                    )
                    if normalize_text(
                        self._aspect_config().get("dual_path_fusion")
                    ).lower() == "base_preserving_union":
                        quota_rank_field = "base_path_rank"
                selected, fusion_telemetry = self._p0_cross_encoder_mmr_candidates(
                    question=question,
                    p0_candidates=candidates,
                    candidate_k_override=dual_candidate_k,
                    quota_rank_field=quota_rank_field,
                    aspect_queries=aspect_rerank_queries,
                )
                if dual_path_telemetry:
                    fusion_telemetry["dual_path"] = dual_path_telemetry
                if aspect_used:
                    aspect_source = (
                        "llm_question_decomposition"
                        if method == "P1A_QPA_ASPECT_CROSS_ENCODER_MMR"
                        else "pcf_anchored_property_relational_subgraph"
                        if method in {P1P_PARS, P1P_PARS_PROFILE_FREE}
                        else "pcf_graph_grounded_rank_fusion"
                        if method in {P1G_PCF_GROUNDED, P1G_PROFILE_FREE}
                        else "unsupervised_question_only"
                    )
                    fusion_telemetry["aspect_analysis"] = {
                        "used": True,
                        "source": aspect_source,
                        "variant": method,
                        "semantic_blend_weights": aspect_weights,
                        "applicability_score": aspect_applicability,
                        "selective_gate_applied": aspect_applied,
                        "selective_gate_enabled": (
                            method not in PROFILE_FREE_ASPECT_METHODS
                        ),
                        "multivector_enabled": bool(
                            self._aspect_config().get("multivector_enabled", False)
                        )
                        if aspect_routing_mode == "layered"
                        else False,
                        "routing_mode": aspect_routing_mode,
                        "aspect_branch_enabled": uses_aspect_branch,
                        "stages": (
                            ["pcf_first_base", "direct_evidence"]
                            if aspect_routing_mode == "direct_evidence"
                            else ["pcf", "taskframe", "taskmention_fact"]
                        ),
                    }
                    extractor_name = (
                        "llm"
                        if method == "P1A_QPA_ASPECT_CROSS_ENCODER_MMR"
                        else "property_relational_subgraph"
                        if method in {P1P_PARS, P1P_PARS_PROFILE_FREE}
                        else "pcf_grounded"
                        if method in {P1G_PCF_GROUNDED, P1G_PROFILE_FREE}
                        else "unsupervised"
                    )
                    if aspect_routing_mode == "direct_evidence":
                        strategy_prefix = (
                            "profile_free"
                            if method in PROFILE_FREE_ASPECT_METHODS
                            else "qpa"
                        )
                        retrieval_strategy = (
                            f"{strategy_prefix}_pcf_anchor_direct_evidence_"
                            f"{extractor_name}_aspect_cross_encoder_mmr"
                        )
                    else:
                        retrieval_strategy = (
                            "qpa_layered_graph_dual_path_"
                            f"{extractor_name}_aspect_cross_encoder_mmr"
                            if uses_aspect_branch
                            else "qpa_layered_graph_"
                            f"{extractor_name}_aspect_cross_encoder_mmr"
                        )
                else:
                    retrieval_strategy = "qpa_layered_graph_cross_encoder_mmr"
            else:
                retrieval_strategy = "qpa_layered_graph"

        if (
            method in {P1P_PARS, P1P_PARS_PROFILE_FREE}
            and pars_state is not None
            and selected is not None
        ):
            explanation_fields = (
                "taskframe_id",
                "fact_id",
                "fact_relationship",
                "taskmention_id",
                "subgraph_aspects",
                "subgraph_nodes",
                "subgraph_edges",
                "subgraph_signals",
                "subgraph_rrf_score",
                "subgraph_node_count",
                "subgraph_edge_count",
            )
            for item in selected:
                explanation = self._materialize_property_relational_candidate(
                    item["evidence_id"], pars_state
                )
                for field in explanation_fields:
                    item[field] = explanation[field]

        evidence_top_k = int(self.config["evidence_top_k"])
        if selected is None:
            selected = [value for _, value in sorted(
                candidates.items(), key=lambda item: (-item[1]["score"], item[0])
            )[:evidence_top_k]]
        for rank, item in enumerate(selected, start=1):
            item["rank"] = rank
            evidence = self.graph.evidence[item["evidence_id"]]
            item["text"] = normalize_text(evidence.get("name"))
            item["source_file"] = evidence.get("source_file", "")
            item["page"] = evidence.get("page")
            item["section_path"] = evidence.get("section_path", "")
            nodes = [
                {
                    "label": "EvidenceSpan",
                    "id": item["evidence_id"],
                    "name": normalize_text(evidence.get("name")),
                }
            ]
            edges: list[dict[str, str]] = []
            frame_id = normalize_text(item.get("taskframe_id"))
            fact_id = normalize_text(item.get("fact_id"))
            mention_id = normalize_text(item.get("taskmention_id"))
            if frame_id and frame_id in self.graph.taskframes:
                nodes.append(
                    {
                        "label": "TaskFrame",
                        "id": frame_id,
                        "name": _property(
                            self.graph.taskframes[frame_id], "name", "displayName"
                        ),
                    }
                )
            if fact_id and fact_id in self.graph.facts:
                nodes.append(
                    {
                        "label": "Fact",
                        "id": fact_id,
                        "name": _property(
                            self.graph.facts[fact_id], "name", "displayName"
                        ),
                    }
                )
                relationship = normalize_text(item.get("fact_relationship"))
                if frame_id and relationship:
                    edges.append(
                        {
                            "from": frame_id,
                            "type": relationship,
                            "to": fact_id,
                        }
                    )
                edges.append(
                    {
                        "from": fact_id,
                        "type": "SUPPORTED_BY",
                        "to": item["evidence_id"],
                    }
                )
            if mention_id and mention_id in self.graph.taskmentions:
                nodes.append(
                    {
                        "label": "TaskMention",
                        "id": mention_id,
                        "name": _property(
                            self.graph.taskmentions[mention_id], "name", "displayName"
                        ),
                    }
                )
                if frame_id:
                    edges.append(
                        {
                            "from": mention_id,
                            "type": "MEMBER_OF",
                            "to": frame_id,
                        }
                    )
                edges.append(
                    {
                        "from": mention_id,
                        "type": "SUPPORTED_BY",
                        "to": item["evidence_id"],
                    }
                )
            matched_aspect = normalize_text(item.get("matched_aspect"))
            item["provenance"] = {
                "stored_graph_nodes": (
                    [
                        {
                            "label": node.get("label", "Node"),
                            "id": node.get("id", ""),
                            "name": node.get("name", ""),
                            "matched_property": node.get(
                                "matched_property", ""
                            ),
                            "matched_property_text": node.get(
                                "matched_property_text", ""
                            ),
                        }
                        for node in item.get("subgraph_nodes", [])
                    ]
                    if item.get("subgraph_nodes")
                    else nodes
                ),
                "stored_graph_edges": (
                    [
                        {
                            "from": edge.get("from", ""),
                            "type": edge.get("type", ""),
                            "to": edge.get("to", ""),
                        }
                        for edge in item.get("subgraph_edges", [])
                    ]
                    if item.get("subgraph_edges")
                    else edges
                ),
                "query_time_route": (
                    {
                        "from_type": "Aspect",
                        "from_text": matched_aspect,
                        "to_type": "EvidenceSpan",
                        "to_id": item["evidence_id"],
                        "stored_as_neo4j_edge": False,
                    }
                    if matched_aspect
                    else None
                ),
                "query_time_subgraph_selection": (
                    {
                        "method": "PARS-KG-RAG",
                        "aspects": item.get("subgraph_aspects", []),
                        "signal_ranks": item.get("subgraph_signals", {}),
                        "virtual_edges_created": 0,
                    }
                    if item.get("subgraph_nodes")
                    else None
                ),
            }
        context = self._render_context(
            method=method,
            condition=condition,
            profile=active_profile,
            pcf_candidates=pcf_candidates,
            taskframes=taskframes,
            selected=selected,
        )
        return {
            "qid": qid,
            "question": question,
            "method": method,
            "condition": condition,
            "query_profile": active_profile,
            "question_aspects": dict(aspects or {}) if aspect_used else {},
            "pcf_candidates": pcf_candidates,
            "taskframe_candidates": taskframes,
            "taskmention_candidates": taskmentions[:8],
            "fact_candidates": facts[:12],
            "evidence": selected,
            "context": context,
            "status": "RETRIEVED" if selected else "NO_CONTEXT",
            "telemetry": {
                "pcf_count": len(pcf_candidates),
                "taskframe_count": len(taskframes),
                "taskmention_count": len(taskmentions),
                "fact_count": len(facts),
                "evidence_count": len(selected),
                "taskframe_gap_adaptation": used_tf_gap,
                "evidence_gap_adaptation": used_evidence_gap,
                "context_chars": len(context),
                "retrieval_strategy": retrieval_strategy,
                "query_profile_used": query_profile_used,
                "property_weighting": (
                    "fixed_equal"
                    if method in FIXED_PROPERTY_METHODS
                    else "query_profile_dynamic"
                    if query_profile_used
                    else "not_applicable"
                ),
                "aspect_analysis_used": aspect_used,
                "graph_used": method not in {
                    "B0_VANILLA_DENSE_RAG",
                    "B0_EVIDENCE_HYBRID",
                },
                "bm25_used": method != "B0_VANILLA_DENSE_RAG",
                "late_fusion": fusion_telemetry,
            },
        }
