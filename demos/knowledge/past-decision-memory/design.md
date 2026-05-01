# Knowledge · `past-decision-memory`

A memory store of past decisions paired with their observed outcomes —
what was decided, what happened, and how surprised we were. Smaller and
more retrieval-oriented than the `decision-journal-kg`; this is the
"working memory" that surfaces priors fast, not the full graph of
rationale and objections.

## Purpose

The `decision-journal-kg` is the system of record. The
`past-decision-memory` is its lightweight retrieval companion — a
flat, embedded store that any agent can query without traversing a
Cypher graph, returning the small handful of priors that matter for the
decision in front of it right now.

## Type

Memory (with decay/consolidation via `internal/memory/`); pinned for
high-stakes decisions, decaying for low-stakes ones.

## Schema

Each memory record:

```yaml
---
decision_id: <id, mirror of decision-journal-kg>
title: <short decision phrasing>
made_at: <timestamp>
stakes: <low|medium|high>
outcome_score: <0..1 or null while open>
surprise: <0..1>                # |outcome_score - predicted_score|
takeaway: <one-line learning>
embedding_seed: <decision title + takeaway>
---
```

**Retention rules**: `stakes=high` records are pinned indefinitely;
`medium` decay on a 1-year half-life; `low` decay on a 90-day half-life.
A decision whose `surprise > 0.5` gets re-pinned regardless of stakes —
high-surprise outcomes are exactly the ones the team should not forget.

## Ingest source

- Mirror writes from `decision-journal-kg` on decision finalization
- `decision-journal-loop` workflow updates `outcome_score` and `surprise` at 7d / 30d / 90d
- The `forecast-then-score` workflow contributes the predicted-vs-actual delta

## Retrieval query example

> An agent about to make a decision titled "switch CDN providers":

→ semantic search over `embedding_seed` for the candidate decision title
→ filter: `stakes IN ["medium","high"]`
→ rank by similarity * (1 + surprise) — high-surprise priors win ties
→ returns the top 5 with `takeaway` rendered into the prompt

## ACLs

- **Read**: workspace-wide for non-sensitive decisions (per the `decision-journal-kg` ACL)
- **Write**: only by the decision journal pipeline; no manual edits
- **Public/customer access**: never

## Why it's a good demo

It's the cheap, fast prior-retrieval surface that makes "the platform
compounds" visible at sub-second latency. It's the dependency that lets
agents *quickly* recall the past without taking on the full weight of a
graph query. Composes with `pre-mortem-first`, `forecast-then-score`,
and the `governor-rule-miner` model.
