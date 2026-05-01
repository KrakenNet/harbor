# Knowledge · `counterfactual-memory`

A memory store of the decisions you *almost* made — the alternatives
weighed, the reasons each was rejected, and (when later evidence
arrives) the score on whether the rejection turned out to be wise. The
roads not taken, kept on purpose.

Most teams document the decision they made. The
`counterfactual-memory` documents every decision they *could have*
made, with the rationale for not making it. That's the dataset that
catches systematic blind spots — the categories of options the team
keeps rejecting for the same reason, especially when the reason is
wrong.

## Purpose

Picking option A is half a decision. The other half is the implicit
verdict against options B, C, D. Most teams forget B, C, and D the
moment A is chosen, then re-litigate them every six months because
nobody remembers they were already considered. This memory keeps them
on file, indexed by the original decision, retrievable next time
something similar comes up.

The load-bearing innovations:

1. **Counterfactuals are co-equal nodes**, not footnotes. They embed,
   they retrieve, they accumulate evidence over time.
2. **Rejection reasons are themselves evaluated**: when a rejected
   alternative *would have* worked (per `time-travel-replayer` or
   downstream evidence), the rejection reason gets a downvote.
3. **The same rejection reason cited 5+ times across counterfactuals
   becomes a candidate "lazy heuristic"** that the team gets prompted
   to re-examine.

## Type

Memory (with decay/consolidation via `internal/memory/`); pinned
indefinitely for high-stakes parent decisions, decaying for low-stakes,
linked by `parent_decision_id` to the `decision-journal-kg`.

## Schema

Each counterfactual record:

```yaml
---
counterfactual_id: <uuid>
parent_decision_id: <id, links to decision-journal-kg>
title: <one-line description of the rejected option>
why_not_chosen: <prose, multi-sentence>
rejection_reason_tags: [<e.g. cost, complexity, risk, vendor-lock, team-bandwidth>]
proposed_by: <person|agent>
priors_cited: [<doc-id>]
hindsight: { observed_at, would_have_worked: <true|false|unknown>, evidence }
weight_against_reasons: <int>     # incremented when a rejection reason later proves wrong
embedding_seed: <title + why_not_chosen>
---
```

**Retention rules**: pinned while the parent `Decision` is active;
half-life of 1 year after parent decision closes; *re-pinned* if a
later decision in a similar embedding region reaches a different
verdict — the divergence is itself signal.

## Ingest source

- The `pre-mortem-first` workflow writes counterfactuals during its options-generation phase
- The `devils-advocate` agent writes counterfactuals as part of objection traces
- The `panel-of-five` agent contributes counterfactuals from each archetype's preferred path
- HITL approval gates capture counterfactuals when the human picks one option but mentions others

## Retrieval query example

> A workflow is about to make a decision in the embedding region of "switch primary database":

→ semantic search over `embedding_seed` for the candidate decision
→ filter: `parent_decision_id IN (similar past decisions)`
→ aggregate: histogram of `rejection_reason_tags` across the matches
→ surface: "The last 4 times we considered this kind of switch, we rejected it for `team-bandwidth` (3x) and `vendor-lock` (1x). Both `team-bandwidth` rejections later proved correct; the `vendor-lock` rejection was contradicted in hindsight."

## ACLs

- **Read**: same workspace ACL as the parent decision
- **Write**: append-only; `hindsight` and `weight_against_reasons` can
  be added but the original `why_not_chosen` is immutable — that's the
  whole point
- **Public/customer access**: never

## Why it's a good demo

1. **It catches the failure mode no other primitive catches.** Decision
   journals capture what you did. Anti-pattern KBs capture what went
   wrong. Counterfactual memory is the only one that captures *the
   options you systematically don't take* — and lets you ask whether
   that's wisdom or a rut. That's a higher-order question and a
   distinctive one.

2. **It is the only sane input to `counterfactual-replay`.** That
   workflow re-runs past decisions with alternative paths chosen. It
   needs a corpus of "alternative paths the team actually considered" —
   not LLM-generated alternatives, which would just be hallucinated
   straw options. This memory provides the real ones, with the team's
   real reasons for rejecting them.

3. **It composes with `governor-rule-miner` to find lazy heuristics.**
   When the same `rejection_reason_tag` ("we don't have bandwidth")
   recurs across decades of counterfactuals and increasingly correlates
   with `would_have_worked: true`, the rule-miner can propose:
   "consider whether 'no bandwidth' has become a default excuse." That's
   the kind of meta-finding only a counterfactual record makes
   possible.

## Sample read

> Team is debating: "should we adopt event-sourcing for the orders service?"

→ counterfactuals retrieved (from past similar decisions):
  - "Adopt event-sourcing for inventory" — rejected 2024 for `complexity` + `team-bandwidth`. Hindsight: `would_have_worked: true` (the audit log we built later was a poor man's event log).
  - "Adopt CQRS for billing" — rejected 2023 for `complexity`. Hindsight: `would_have_worked: false` (the simpler approach scaled fine).
  - "Migrate orders to Temporal" — rejected 2025 for `vendor-lock`. Hindsight: `unknown` (orders has not yet hit the failure mode that would test it).

→ pattern surfaced: `complexity` is the dominant rejection reason and is
  60% wrong in hindsight in this region. The decision now must either
  address `complexity` head-on or note that the lazy-heuristic risk has
  been considered.

→ the team didn't forget those three prior debates. The KB didn't.
