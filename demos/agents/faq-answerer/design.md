# Agent · `faq-answerer`

Answers questions whose answers exist in a curated FAQ. Designed to
*refuse* when the question doesn't match the FAQ — leaving harder
questions to `support-agent`.

## Purpose

The cheap, fast tier of customer Q&A. A first-pass filter that handles
the long tail of repeat questions deterministically; pairs with
`support-agent` as the fallback.

## DSPy signature

```python
class AnswerFAQ(dspy.Signature):
    question: str = dspy.InputField()
    faq: list[FAQEntry] = dspy.InputField()
    matched_entry_id: Optional[str] = dspy.OutputField()
    answer: Optional[str] = dspy.OutputField(
        desc="verbatim or near-verbatim from the matched entry")
    confidence: float = dspy.OutputField()
```

`FAQEntry = {id, question, answer, last_verified_at}`.

## Recommended tools

- `vector-search` — over the FAQ corpus only
- `embed-text` — match new questions to canonical phrasings

## Recommended governors

- `confidence-threshold` — below threshold → return null, defer to support-agent
- `output-length-cap` — FAQ answers should not balloon
- `fact-half-life` — block answers from FAQ entries older than X
- `schema-validator` — `answer` must be present iff `matched_entry_id` is

## Demonstrations sketch

- "What are your support hours?" → exact match, high confidence
- "Do you offer student discounts?" → near-match, moderate confidence
- "Can I deploy on Kubernetes 1.32 with cilium?" → no match, returns null

## Why it's a good demo

It demonstrates the most under-used agent behavior: refusing to
answer. Most agent demos show off how much an agent can do; this one
shows the value of staying in its lane.
