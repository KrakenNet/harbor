# Tool · `decision-diary`

Before any irreversible verb fires — a payment, a customer email, a
deletion, a deployment, a schema migration — write an immutable diary
entry: what's about to happen, why, by whose authority, on what
evidence, and with what predicted outcome. The entry is signed,
timestamped, and inserted before the verb is allowed to execute. After
the verb runs, an outcome row is stitched onto the entry. Months later,
the diary lets anyone reconstruct *why* any consequential thing
happened — and grade the prediction.

This is the "show your work, before you do the thing" tool. It is
deliberately a tool and not a governor, so the agent can be required to
*author* the rationale itself rather than have a governor generate one
from outside.

## Purpose

Auditability for irreversible actions. Calibration data for predicted
outcomes. A stable substrate for `decision-journal-kg` and for the
`trial-and-retro` and `decision-journal-loop` workflows. A place where
teams can read, weeks later, what the system was thinking when it did
the thing it did.

## Inputs

| Field            | Type    | Required | Notes |
|------------------|---------|----------|-------|
| `verb`           | string  | yes      | e.g. "send_email", "drop_column", "approve_refund" |
| `target`         | object  | yes      | what the verb acts on |
| `rationale`      | string  | yes      | the agent's own reasoning, in prose |
| `evidence_refs`  | []ref   | no       | spans / KB articles / memories cited |
| `predicted_outcome`| string\| structured | yes | what the agent expects to happen and how it will know |
| `irreversibility`| enum    | yes      | reversible / hard-to-undo / one-way |
| `authority`      | string  | yes      | the actor identity claiming responsibility |
| `confidence`     | float [0..1] | no  | from `confidence-bettor` if available |

## Outputs

| Field            | Type    | Notes |
|------------------|---------|-------|
| `entry_id`       | uuid    | the immutable row's id |
| `signature`      | string  | hash of (entry contents + parent trace) |
| `block_hash`     | string  | append-only hash chain pointer |
| `recorded_at`    | string  | ISO 8601 |
| `outcome_slot`   | string  | reference for the future outcome row |

## Implementation kind

Python tool with a small DSPy preamble. The DSPy step exists to
*enforce* that `rationale` and `predicted_outcome` are non-trivial:
generic LLM output ("we should do this because it's the right thing")
gets re-prompted; rationales without a connection to evidence get
re-prompted; predictions without a falsifiable success criterion get
re-prompted.

## Dependencies

- A `decisions` append-only table — once written, never updated; outcome
  rows are separate, joined by `entry_id`
- Hash-chained block table — each entry's `block_hash` covers the
  previous entry, making post-hoc tampering detectable
- `internal/tracing/` — entry id is captured on the parent span; the
  diary entry is itself a child span
- Sibling tools: `confidence-bettor` (auto-fill `confidence`),
  `provenance-tracer` (auto-fill some `evidence_refs`), `five-whys`
  (when rationale is shallow, this tool suggests running it)
- `decision-journal-kg` — reads from this table; the diary is its
  source of truth

## Side effects

One row inserted into the `decisions` table. One span emitted. The
inserted row is immutable — there is no `update` or `delete` API for
diary entries from agent code; correction is via a *new* entry that
references the old one.

## Failure modes

- Rationale fails the non-triviality DSPy check after one re-prompt →
  `error_kind="rationale_too_thin"` and the verb is *not* recorded;
  the irreversible verb cannot proceed (this is the point)
- Predicted outcome lacks a falsifiable success criterion → re-prompted
  once, then `error_kind="prediction_unfalsifiable"`
- Storage write fails → tool returns an error and the verb is not
  permitted to proceed; failing-open here would defeat the purpose
- Hash chain check on prior block fails → tool refuses to write,
  surfaces `error_kind="chain_corrupted"` to operators (this is a
  high-severity ops alert in its own right)
- Authority not in the allowed-actors list for this verb → rejected,
  `error_kind="authority"`

## Why it's a good demo

Three reasons:

1. **It only matters because Railyard already has the trace, the
   memory, and the KG to bind the entry to.** A diary entry on a
   platform without a trace is a sticky note. A diary entry stitched
   to the parent span, the cited memories, the consulted KB articles,
   and the eventual outcome is an artifact you can audit two years
   later. The platform is what makes this tool useful.
2. **It composes with every safety pillar in the catalog.** Pairs with
   the `pre-mortem-required`, `are-you-sure`, `hitl-trigger`, and
   `approval-policy` governors (any of which can require a diary
   entry as a precondition), with the `confidence-bettor` and
   `provenance-tracer` tools (which feed it), with the
   `decision-journal-kg` and `provenance-graph` knowledge artifacts
   (which read it), and with the `trial-and-retro`,
   `decision-journal-loop`, and `forecast-then-score` workflows
   (which close the loop on outcomes vs. predictions). It is the
   center of the "thinking-before-acting" tool family.
3. **It produces calibration data for free.** Every entry has a
   prediction; outcomes get stitched on automatically by the
   `trial-and-retro` workflow. After a few months, you can compute
   per-agent, per-verb, per-tenant prediction-vs-outcome distributions
   and feed them to the `cost-spike-forecaster` and
   `hallucination-scorer` ML primitives. The platform learns from its
   own diary.

## Sample interaction

> verb: drop_column
> target: { table: "users", column: "legacy_phone" }
> rationale: "Column has been NULL for 100% of rows for 11 months
>   (verified via sql-query span 8a2c…). Migration v17 introduced
>   `phone_e164` as the canonical column. No application code
>   references `legacy_phone` (verified via repo grep span 4d1e…).
>   Dropping it reclaims ~120MB and lets the next index rebuild run
>   online."
> evidence_refs: [span:8a2c…, span:4d1e…, adr-archive/adr-0231]
> predicted_outcome: "Migration completes in <30s. No application
>   error rate change in the following 24h. Storage on `users`
>   drops by 100-150MB. If error rate increases or storage doesn't
>   drop, prediction is failed."
> irreversibility: one-way
> authority: agent:schema-migrator (operator: alex@…)
> confidence: 0.93 (from confidence-bettor)

→ entry_id: 7e1c…
→ signature: sha256:9b…
→ block_hash: chain depth 41822
→ recorded_at: 2026-04-30T18:07:11Z
→ outcome_slot: outcome:7e1c…

The migration runs. 26 hours later, the `trial-and-retro` workflow
writes the outcome row: completion 11s, no error-rate change, storage
dropped 138MB. Prediction graded as `met`. That outcome flows into
`decision-journal-kg` and into the calibration data the
`question-difficulty-router` consults next time the schema-migrator
agent asks for a model.
