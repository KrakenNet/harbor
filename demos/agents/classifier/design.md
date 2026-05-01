# Agent · `classifier`

Takes a piece of text and a fixed label set and returns one label plus a
calibrated confidence. The atom of routing.

## Purpose

The most-reused agent shape in any production system: route inbound
items, tag content, gate downstream verbs. Used by `triage`,
`support-agent`, and most workflows with branching logic.

## DSPy signature

```python
class Classify(dspy.Signature):
    text: str = dspy.InputField()
    labels: list[str] = dspy.InputField(desc="closed label set")
    label_definitions: dict[str, str] = dspy.InputField(
        desc="optional: label → one-sentence definition")
    label: str = dspy.OutputField(desc="must be one of `labels`")
    confidence: float = dspy.OutputField()
    rationale: str = dspy.OutputField(desc="one-sentence justification")
```

## Recommended tools

- `embed-text` — fall back to nearest-neighbor labeling if confidence low
- `vector-search` — retrieve canonical examples per label

## Recommended governors

- `schema-validator` — `label` must be in `labels`, no hallucinated classes
- `confidence-threshold` — escalate or abstain below threshold
- `latency-sla` — classification should be fast; cap aggressively

## Demonstrations sketch

- Inbound email → `{billing, bug, feature_request, abuse, other}`
- Support ticket → severity `{S1, S2, S3, S4}`
- Code-review comment → `{nit, blocking, question, praise}`

## Why it's a good demo

Classification is the simplest agent shape that still benefits from
every Railyard primitive: optimized demonstrations raise accuracy,
governors enforce the closed label set, and the trace shows exactly why
each label was chosen. It's the cleanest "show me the system" demo.
