# DEV Prompt Revision Log

## Field v1 cardinality clarification

- Data inspected: `model_bakeoff_24` in `DEV_EXPOSED_60`
- Fresh R2_PILOT accessed: no
- TEST accessed: no
- API transport/schema failures: 0

The initial field prompt used singular wording and did not explicitly require one output per batch item. Strict Structured Outputs guaranteed each returned item's shape but not array cardinality. C02∼C04 omitted batch items.

Before panel selection and before any fresh pilot call, the prompt was clarified to require exactly one output per input item in the same order. Label definitions, models, schemas, candidate generator, and Gate thresholds were not changed.

## Bake-off task-decomposition correction

- Fresh R2_PILOT accessed: no
- TEST accessed: no

The first bake-off implementation reversed candidate order in repeat 2, conflating repeat stability with order audit. It also returned all six fields in one response even though the preregistration requires F1∼F4 separation. The corrected bake-off uses canonical candidate order for both primary repeats, runs reverse order as a separate audit, and executes semantic, deontic/polarity, context, and promotion as four separate Structured Output tasks.

The fifth and final allowed configuration, pinned `gpt-4.1-nano-2025-04-14`, was added before panel selection. No additional configuration may be added after this point.
