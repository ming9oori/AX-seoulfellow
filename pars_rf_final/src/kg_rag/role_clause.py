"""Deterministic raw-offset, question-only Role-Clause extraction. No embeddings."""
from __future__ import annotations

import re
from kiwipiepy import Kiwi


class RoleClauseExtractor:
    def __init__(self, rules, kiwi=None, *, uncapped=False):
        if rules["version"] != "role_clause_v1" or rules["max_aspects"] != 3:
            raise ValueError("Unsupported frozen aspect contract")
        self.rules = rules
        self.uncapped = uncapped
        self.kiwi = kiwi or Kiwi()
        self.cues = re.compile(rules["intent_cues"])
        self.boundary = re.compile(rules["parallel_boundary"])
        self.constraint = re.compile(rules["constraint_cues"])

    def extract(self, question):
        if not isinstance(question, str) or not question.strip():
            raise ValueError("Empty question")
        # Kiwi offsets refer to this exact original string, never normalized text.
        tokens = list(self.kiwi.tokenize(question))
        def span(start, end):
            while start < end and question[start].isspace():
                start += 1
            while end > start and question[end - 1].isspace():
                end -= 1
            return {"start": start, "end": end, "text": question[start:end]}
        domains, current = [], []
        for token in tokens:
            if token.tag in self.rules["noun_tags"] and not self.cues.search(question[token.start:token.start + token.len]):
                if current and question[current[-1].start + current[-1].len:token.start].strip():
                    domains.append(span(current[0].start, current[-1].start + current[-1].len))
                    current = []
                current.append(token)
            elif current:
                domains.append(span(current[0].start, current[-1].start + current[-1].len))
                current = []
        if current:
            domains.append(span(current[0].start, current[-1].start + current[-1].len))
        # A conjunction is a split only when distinct information cues occur on both sides.
        cuts, start = [], 0
        for match in self.boundary.finditer(question):
            if self.cues.search(question[start:match.start()]) and self.cues.search(question[match.end():]):
                cuts.append(match.end())
                start = match.end()
        bounds = [0, *cuts, len(question)]
        clauses = [span(a, b) for a, b in zip(bounds, bounds[1:]) if a < b]
        intents = []
        for clause in clauses:
            cue = self.cues.search(clause["text"])
            if cue:
                # Keep the complete information-request clause, including its explicit
                # actors/objects/modifiers. A nearest noun alone can drop comparisons.
                intents.append(clause)
        constraints, previous_end = [], 0
        for match in self.constraint.finditer(question):
            if match.start() < previous_end:
                continue
            punctuation = max(question.rfind(c, previous_end, match.start()) for c in ",;?")
            left = max(previous_end, punctuation + 1)
            end = match.end()
            if any(c.isdigit() for c in match.group()):
                comparator = re.match(self.rules["numeric_comparator_suffix"], question[end:])
                if comparator:
                    end += comparator.end()
            while end < len(question) and not question[end].isspace() and question[end] not in ",;?":
                end += 1
            if left < end:
                constraints.append(span(left, end))
            previous_end = end
        # Identical spans only; overlapping but distinct constraints are retained.
        constraints = list({(s["start"], s["end"]): s for s in constraints}.values())
        primary_role = "intent" if intents else "action" if any(t.tag in self.rules["action_tags"] for t in tokens) else "domain"
        primary = intents or [span(0, len(question))]
        units = [(primary_role, [s]) for s in primary] + [("constraint", [s]) for s in constraints]
        if len(units) > 3 and not self.uncapped:
            if primary and constraints:
                intent_groups = [[primary[0]], primary[1:]] if len(primary) > 2 else [[s] for s in primary]
                units = [(primary_role, s) for s in intent_groups] + [("constraint", constraints)]
            else:
                role, values = ("intent", intents) if intents else ("constraint", constraints)
                units = [(role, [values[0]]), (role, [values[1]]), (role, values[2:])]
        # Supplement only distinct, uncovered domain text; never pad to three.
        for domain in domains:
            if len(units) >= 3 and not self.uncapped:
                break
            if all(not any(s["start"] <= domain["start"] and domain["end"] <= s["end"] for s in spans) for _, spans in units):
                # Domains preceding an intent are its anchor, not another redundant aspect.
                if intents:
                    continue
                units.append(("domain", [domain]))
        output, seen = [], set()
        for role, sources in units:
            anchors = []
            if role in {"intent", "constraint"}:
                prior = [d for d in domains if d["end"] <= sources[0]["start"]]
                anchor = max(prior, key=lambda d: (d["end"], len(d["text"])), default=domains[0] if domains else None)
                # Parallel clauses inherit the first explicitly stated business topic.
                if role == "intent" and intents and sources[0]["start"] > intents[0]["start"]:
                    first_cue = self.cues.search(intents[0]["text"])
                    topic_end = intents[0]["start"] + first_cue.start()
                    topics = [d for d in domains if d["end"] <= topic_end]
                    anchor = max(topics, key=lambda d: (d["end"], len(d["text"])), default=anchor)
                    local_cue = self.cues.search(sources[0]["text"])
                    if any(sources[0]["start"] <= d["start"] < sources[0]["start"] + local_cue.start() for d in domains):
                        anchor = None
                if anchor and all(not (s["start"] <= anchor["start"] and anchor["end"] <= s["end"]) for s in sources):
                    anchors = [anchor]
            text = " | ".join(s["text"] for s in [*anchors, *sources])
            # A bare cue without an anchor is replaced by the complete question.
            if not anchors and not any(t.tag in self.rules["noun_tags"] + self.rules["action_tags"] and
                                      any(s["start"] <= t.start < s["end"] for s in sources) for t in tokens):
                sources, text = [span(0, len(question))], question
            if text in seen:
                continue
            seen.add(text)
            output.append({"aspect_id": f"a{len(output) + 1}", "roles": [role],
                           "source_spans": sources, "anchor_spans": anchors, "search_text": text,
                           "bundled": len(sources) > 1, "rule_version": self.rules["version"]})
        return output
