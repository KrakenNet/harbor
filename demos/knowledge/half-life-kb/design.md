# Knowledge · `half-life-kb`

A knowledge base in which every fact carries a decay date and a
source-trust score, and retrieval refuses to surface a fact whose
half-life has expired without a fresh re-validation. The KB doesn't
just *store* knowledge — it tracks how confident you should still be in
it, and forces a refresh before letting an agent act on stale ground.

Most knowledge bases assume "what was true last quarter is true today."
That's a lie about how the world works, and the lie compounds. The
`half-life-kb` makes the lie structurally impossible: every fact has a
date past which an agent must either re-confirm it or treat it as
unknown.

## Purpose

Stale facts kill agents. A pricing page that changed last week, a
runbook for a service that was retired, a "we always do X" rule whose
author left the company — these are the failure modes that make agents
look stupid. The `half-life-kb` makes freshness a first-class concern.

The two load-bearing innovations:

1. **Each fact owns its own half-life**, set by class. "Engineering
   architecture" decays slowly. "Product pricing" decays fast. "On-call
   rotation" decays in days.
2. **Trust is multi-dimensional**: source trust × recency trust ×
   reinforcement count. Two reinforcing sources beat one trusted source.

## Type

Knowledge Base (markdown documents) with chunked embeddings, plus a
freshness ledger that the retrieval layer consults *before* returning a
chunk.

## Schema

Each fact document carries frontmatter:

```yaml
---
fact_id: <uuid>
title: <fact phrasing>
class: <pricing|architecture|policy|on-call|...>
half_life_days: <int>            # depends on class
asserted_at: <date>
asserted_by: <person|agent|integration>
source_trust: <0..1>             # 1 = primary system of record
reinforcements: [{ at, by, source_trust }]
contradictions: [{ at, by, body }]
expires_at: <derived = asserted_at + 2 * half_life_days>
status: <fresh|stale|expired|contradicted>
---
```

Body is the fact stated in plain language plus the evidence excerpt that
backs it.

The retrieval layer computes `effective_trust = source_trust *
exp(-age / half_life_days)` and refuses any chunk where
`effective_trust < class_threshold`, returning instead a "this fact is
stale, here's the last assertion + the suggested re-check" envelope.

## Ingest source

- Any other KB or KG can publish facts here with a class tag and a source
- The `fact-half-life` governor consumes the `expires_at` field on every retrieval
- The `knowledge-half-life-sweep` workflow runs nightly, emails owners, and queues HITL re-validation
- The `pre-mortem-first` workflow uses `effective_trust` to weight priors

## Retrieval query example

> An agent asks: "what's our published per-seat price for the Pro tier?"

→ semantic search hits a chunk with `class=pricing, half_life_days=14,
  asserted_at=70 days ago` → `effective_trust ≈ 0.04`, well below the
  pricing-class threshold of 0.5
→ retrieval layer **refuses** to return the chunk as authoritative.
  Instead it returns:

```json
{
  "status": "stale",
  "fact_id": "...",
  "last_known_value": "$49/seat/mo",
  "asserted_at": "2026-02-19",
  "expires_at": "2026-03-19",
  "suggested_refresh": "fetch the live pricing page or open a HITL re-validation"
}
```

The downstream agent now has a choice: refuse to answer, fetch fresh, or
flag the question for HITL — but it can no longer accidentally cite a
two-month-old price.

## ACLs

- **Read**: same as the underlying KB the fact was published into; the freshness ledger is workspace-wide
- **Write**: append-only — facts can be reinforced or contradicted, but
  not silently edited; an "edit" is structurally a contradiction + a new
  assertion
- **Audit**: every retrieval that *would have* returned a stale fact
  produces a span — these are the gold for the `governor-rule-miner`

## Why it's a good demo

1. **It is the structural answer to "agents hallucinate stale facts."**
   Most platforms add a citation to a fact and call it grounded. This
   one refuses to cite a fact that's past its expiration. That's a
   sharper guarantee and a more honest one. It composes directly with
   the `fact-half-life` governor and the `conviction-tax` governor —
   high-conviction claims on stale facts get a double penalty.

2. **It is the data substrate for `knowledge-half-life-sweep` and
   `cargo-cult-registry`.** The freshness ledger is exactly the input
   those two need: facts that haven't been reinforced are sweep targets;
   rules whose underlying facts have all expired are cargo-cult
   candidates. Pull the half-life-kb out and both demos collapse.

3. **It makes the "knowledge compounds" claim falsifiable.** A normal
   KB grows, but you can't tell whether it's growing in fresh-and-trusted
   ways or accumulating dead weight. With this KB you can graph
   `effective_trust` over the whole corpus over time. If the line slopes
   down, the team knows. That's epistemic hygiene as a metric.

## Sample read

> Agent calling `support-agent` for a billing question:

→ candidate fact: "annual plan customers get a 15% discount" (class=pricing, asserted 8 months ago, half_life=14)
→ `effective_trust = 0.85 * exp(-240/14) ≈ 1e-7` — effectively zero
→ retrieval returns: `{ status: "expired", last_known_value: "15% discount", asserted_at: "2025-08-15" }`
→ agent's response composes: "I'd want to verify this — our records
  show a 15% annual discount as of August, but that's well past its
  freshness window. Let me pull the current pricing page."
→ a `time-travel-replayer` run with this same query 30 days ago — when
  the fact was still fresh — would have answered confidently. The KB's
  behavior changed because the world's behavior changed. That's the
  point.
