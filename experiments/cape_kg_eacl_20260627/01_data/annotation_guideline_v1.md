# CAPE-KG Annotation Guideline v1

## Unit

Annotate one `chunk_id` at a time. Mark every evidence-supported procedural
knowledge item that is relevant to bid/proposal work.

## Entity Types

- DomainTask: coarse work activity, e.g. 수주영업, 제안서 기획
- ProcedureStep: concrete step inside a task
- DecisionGateway: decision point such as Bid/No Bid
- GuardCondition: condition or criterion for a decision or branch
- Artifact: document, plan, checklist, proposal, input/output material
- Role: person/team/actor responsible for an activity
- ReviewCheckpoint: review activity
- Principle/Risk: explicit principle or risk

## Edge Types

Use only the CAPE-KG schema. Every edge must include source/target IDs, type,
and an evidence span. Do not infer missing steps unless the chunk explicitly
supports them.

## Evidence Span

Prefer exact character spans. If OCR noise prevents exact span, use the
sentence anchor and mark `span_quality=sentence_anchor`.

## Labels

Use the Korean surface form when possible and preserve English aliases.
