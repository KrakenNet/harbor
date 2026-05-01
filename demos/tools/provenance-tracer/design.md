# Tool · `provenance-tracer`

Given a claim made anywhere in a Railyard run — a fact in a final answer,
a value pulled from RAG, a number in a generated report — walk the trace
tree backwards to its earliest source span, building a chain of evidence
with model calls, tool calls, retrievals, and human inputs.

This is the "where did this come from?" tool. Most platforms can't answer
it. Railyard can, because every step of an agent's life leaves a span.

## Purpose

Auditability and trust. Compliance reviewers, post-mortems, and curious
users all ask the same question: "how did the system arrive at this?"
Today the answer is "read the logs and reason." This tool replaces that
with a structured chain.

## Inputs

| Field         | Type   | Required | Notes |
|---------------|--------|----------|-------|
| `claim`       | string | yes      | the assertion to trace |
| `trace_id`    | uuid   | yes      | the run that produced it |
| `match_mode`  | enum   | no       | exact / fuzzy / semantic (default fuzzy) |
| `max_depth`   | int    | no, 20   | trace-tree walk depth limit |

## Outputs

| Field          | Type              | Notes |
|----------------|-------------------|-------|
| `chain`        | []ProvenanceNode  | ordered: leaf (claim) → root (source) |
| `confidence`   | float [0..1]      | how certain the match is |
| `gaps`         | []GapNote         | spans skipped or unmatchable |
| `attestations` | []Attestation     | signed evidence items along the chain |

`ProvenanceNode` carries: `span_id`, `span_kind` (model_call / tool_call /
retrieval / human_input / governor_decision), `excerpt`, `model + prompt
hash`, `timestamp`.

## Implementation kind

DSPy tool. The walking algorithm is deterministic; the *matching* between
an output claim and an upstream span uses a small LLM call with grounded
retrieval, which is what makes this a DSPy tool rather than pure Python.

## Dependencies

- `internal/tracing/` — span tree reader
- `pgvector` — embedding-similarity for fuzzy claim matching
- `embed-text` (sibling tool) — to embed the claim
- An LLM judge for the matching step (small, cheap; not the orchestrator's main model)

## Side effects

Read-only against the trace store. Emits its own span (so you can trace
the tracer).

## Failure modes

- Trace not found → returns empty chain with `gap_kind="missing_trace"`
- Claim doesn't match anything → returns empty chain with `gap_kind="no_grounding"` — this is the *useful* signal that the claim may be hallucinated
- Trace tree exceeds `max_depth` → truncated, gap noted
- Span body redacted at write time (PII) → chain still includes node, body marked `[redacted]`

## Why it's a good demo

Three reasons:

1. **It only works because Railyard is what it is.** A platform without
   first-class span trees can't build this. It is the showcase artifact
   for "why use a real agent platform vs. duct-taping LangChain together."
2. **It composes with the `hallucination-scorer` ML model and the
   `conviction-tax` governor.** Together those three primitives form a
   first-class grounding-and-trust pipeline — a single demo that ties the
   platform's pillars together.
3. **It changes how reviewers think.** Once you've seen a final answer
   with a click-through chain back to the source PDF page, every system
   without it feels primitive.

## Sample interaction

> claim: "the Q2 churn rate was 4.7%"
> trace_id: 7fd1...

→ chain:
  1. final answer span (agent: `revenue-summarizer`)
  2. tool call: `sql-query` returning `{churn_rate: 0.047}`
  3. SQL ran against `analytics.churn_v3` view
  4. view definition references `events.subscription_canceled`
  5. (root) data source: Stripe webhook ingestion span at 2026-04-30T14:22Z

→ confidence: 0.96
→ attestations: SQL query SHA-256, model call prompt hash, source-system signature
