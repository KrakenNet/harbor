# Agent · `researcher`

Takes a research question, plans queries, fetches sources, and returns a
cited brief. The "hello world" of agent demos.

## Purpose

A reusable building block for any workflow that needs grounded synthesis:
market research, customer-question RAG fallback, sales prep, technical
investigation.

## DSPy signature

```python
class Research(dspy.Signature):
    question: str = dspy.InputField()
    depth: Literal["quick", "standard", "deep"] = dspy.InputField()
    brief: str = dspy.OutputField(desc="200–800 word synthesized answer")
    citations: list[Citation] = dspy.OutputField()
    confidence: float = dspy.OutputField()
```

`Citation = {title, url_or_doc_id, excerpt, retrieved_at}`.

## Recommended tools

- `web-scrape` — public web sources
- `vector-search` — internal KB retrieval
- `http-fetch` — direct API queries (e.g. arXiv, PubMed)
- `embed-text` — for claim-to-source matching

## Recommended governors

- `cost-ceiling` — research can blow budgets quickly
- `tool-allowlist` — restrict to read-only tools
- `conviction-tax` — penalize high-confidence claims with no citations

## Demonstrations sketch

3–5 tagged exemplars, e.g.:

- "What's the typical gross margin for a vertical SaaS company?" → quick, public sources only
- "Summarize our last six churn-related support tickets." → vector-search over support KB
- "What are the leading approaches to RAG evaluation in 2026?" → deep, mixed sources

## Why it's a good demo

Almost every customer's first agent looks like this. It's the smallest
end-to-end example that touches retrieval, tool use, citation, and
governor enforcement — making it the natural anchor for an onboarding
tutorial.
