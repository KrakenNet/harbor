# Agent · `support-agent`

Answers customer questions by retrieving from internal KBs and citing
sources. The canonical RAG agent.

## Purpose

The single most-deployed agent shape in production. Used directly in
chat surfaces, indirectly in `support-triage` workflows, and as a
fallback for `faq-answerer` when the FAQ misses.

## DSPy signature

```python
class AnswerSupport(dspy.Signature):
    question: str = dspy.InputField()
    customer_context: str = dspy.InputField(
        desc="account tier, product version, prior tickets")
    answer: str = dspy.OutputField()
    citations: list[Citation] = dspy.OutputField()
    confidence: float = dspy.OutputField()
    needs_human: bool = dspy.OutputField()
```

`Citation = {kb_article_id, excerpt, last_verified_at}`.

## Recommended tools

- `vector-search` — primary retrieval against `product-docs-kb` and
  `customer-faq-kb`
- `http-fetch` — pull live status/account data when relevant

## Recommended governors

- `confidence-threshold` — set `needs_human=true` below threshold
- `fact-half-life` — refuse to use KB content older than X days for
  fast-moving topics
- `conviction-tax` — penalize answers that lack citations
- `pii-redactor` — never echo PII back into the answer

## Demonstrations sketch

- "How do I reset my password?" → cites help center, high confidence
- "Why is my invoice $X higher this month?" → escalates (account-specific)
- "Does your product support FedRAMP?" → cites compliance KB; if stale, refuses

## Why it's a good demo

Combines retrieval, citation, and confidence-aware escalation in one
agent. The `fact-half-life` governor is the part most platforms can't
demonstrate — it makes "is this answer still true?" a first-class
question.
