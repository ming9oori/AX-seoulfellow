# Gate 1L Prompt Revision v2

- Revision count: 1/1
- Evidence used for diagnosis: PILOT 40 only
- TEST evidence/reference access: 0
- New evaluation set: fresh INDUCTION 20, no PILOT overlap

## Observed v1 failures

- A/B disagreement bundles: 40/40
- B output paraphrased or concatenated quotes
- A/B family, type, polarity, promotion decision order differed
- argument span granularity was not standardized
- adjudicator rewrote fields while merging
- verifier marked non-applicable checks false

## Locked changes

1. `claim_quote` is one exact contiguous substring and must not concatenate fragments.
2. Claims use a shared family/type decision order.
3. Argument roles are restricted to the schema registry and use minimal exact noun/action spans.
4. `polarity=NEGATIVE` only when the asserted proposition itself is negated; prohibition is `MUST_NOT + NEGATIVE`.
5. Discourse promotion defaults are explicit.
6. Adjudicator must copy candidate claims/fields verbatim and may not rewrite quotes.
7. Verifier returns `true` for preserved constraints that are not applicable; `false` means an actual defect.

No further prompt/guideline revision is allowed in this experiment after the fresh re-pilot.
