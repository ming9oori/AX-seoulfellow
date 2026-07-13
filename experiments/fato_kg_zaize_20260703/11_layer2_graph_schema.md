# FATO-KG Layer2 Graph Schema

Generated: 2026-07-03T06:14:56+00:00

This schema follows `layer2_fato_kg_methodology_eacl.md` and is a bootstrap schema, not a human-gold ontology.

## Node Types

| node_type | role |
| --- | --- |
| `Process` | FATO Layer2 node class |
| `Task` | FATO Layer2 node class |
| `Step` | FATO Layer2 node class |
| `Artifact` | FATO Layer2 node class |
| `InformationItem` | FATO Layer2 node class |
| `StrategyArtifact` | FATO Layer2 node class |
| `StrategyElement` | FATO Layer2 node class |
| `Role` | FATO Layer2 node class |
| `Stakeholder` | FATO Layer2 node class |
| `DecisionPoint` | FATO Layer2 node class |
| `Risk` | FATO Layer2 node class |
| `Principle` | FATO Layer2 node class |
| `Condition` | FATO Layer2 node class |
| `Constraint` | FATO Layer2 node class |
| `EvaluationCriterion` | FATO Layer2 node class |
| `EvidenceSpan` | FATO Layer2 node class |

## Relations

| predicate | domain | range |
| --- | --- | --- |
| `HAS_TASK` | `Process` | `Task` |
| `HAS_SUBTASK` | `Task` | `Task` |
| `HAS_STEP` | `Task` | `Step` |
| `PRECEDES` | `Task, Step` | `Task, Step` |
| `TRIGGERED_BY` | `Task` | `Condition, Event` |
| `USES_INPUT` | `Task, Step` | `Artifact, InputArtifact, InformationItem, Concept` |
| `PRODUCES` | `Task, Step` | `Artifact, OutputArtifact, StrategyArtifact, Checklist, Report, StrategyElement` |
| `PERFORMED_BY` | `Task, Step` | `Role` |
| `ACCOUNTABLE_TO` | `Task, Step` | `Role, Stakeholder` |
| `ANALYZES` | `Task, Step` | `Concept, Artifact, InformationItem, Stakeholder, EvaluationCriterion, StrategyElement` |
| `DEVELOPS` | `Task, Step` | `Artifact, StrategyArtifact, StrategyElement, Concept` |
| `EVALUATES` | `Task, Step` | `EvaluationCriterion, Artifact, Concept` |
| `DECIDES` | `Task, Gate` | `DecisionPoint` |
| `HAS_DECISION_POINT` | `Task` | `DecisionPoint` |
| `HAS_CONDITION` | `Task, Rule` | `Condition` |
| `HAS_CONSTRAINT` | `Task, Artifact` | `Constraint` |
| `HAS_RISK` | `Task, Artifact` | `Risk` |
| `MITIGATES` | `Task, Control` | `Risk` |
| `HAS_PRINCIPLE` | `Task` | `Principle` |
| `MAY_RESULT_IN` | `Risk, Condition, Task` | `Risk, Outcome, Concept` |
| `EVIDENCED_BY` | `Any` | `EvidenceSpan` |
| `MENTIONED_IN` | `Any` | `EvidenceSpan` |
| `MAPS_TO` | `Task` | `StandardNode, NCSCompetencyUnit, PCFElement` |
| `REQUIRES_CAPABILITY` | `Task` | `NCSCompetencyUnit, StandardNode` |
| `PROCESS_CONTEXT` | `Task` | `PCFElement, StandardNode` |

## Claim Boundary

- Every edge must keep `frame_task_id`, `evidence_ids`, `confidence`, and `validation_status`.
- `verified` means rule-level evidence/schema checks passed, not human semantic correctness.
- Mapping edges are candidates only and must not merge Layer2 and Layer1 nodes.
