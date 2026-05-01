# Governor · `echo-chamber-breaker`

Rejects outputs that look too much like the agent's own recent answers.
Anti-rut: forces variety where variety is appropriate, and surfaces the
specific case where the agent has slipped into a stock template.

The diagnosis is uncomfortable but useful: most production agents drift
into a small set of stock answers within a few hundred uses, and nobody
notices until someone looks at five traces in a row and feels the
sameness.

## Purpose

LLMs in production tend to converge. Same opening, same three bullets,
same hedge at the end. For a triage assistant or a researcher this
sameness is a lie about the diversity of the inputs — every ticket
becomes "I see what you mean, here are three steps to try."

This governor compares the proposed response embedding against the
rolling window of recent responses for the same agent / channel /
intent. If it's too similar to the recent past, the run is rejected
and the agent gets one chance to *not* sound like itself.

## Trigger event

`post_response`.

## Facts asserted

```clips
(deftemplate response-similarity
  (slot trace_id)
  (slot agent)
  (slot intent)            ; sourced from intent classifier
  (slot max_cosine)        ; max cosine sim against last N responses
  (slot avg_cosine)        ; mean cosine sim
  (slot window_size)
  (slot retries))

(deftemplate decision
  (slot trace_id)
  (slot verdict))           ; allow | reprompt | flag
```

## Rules

```clips
(defrule reject-near-duplicate
  (response-similarity (trace_id ?t) (max_cosine ?m) (retries ?n))
  (test (and (>= ?m 0.92) (< ?n 2)))
  =>
  (emit-output (str-cat "reprompt:near_duplicate:max=" ?m))
  (assert (decision (trace_id ?t) (verdict reprompt))))

(defrule flag-stock-template
  (response-similarity (trace_id ?t) (avg_cosine ?a) (window_size ?w))
  (test (and (>= ?a 0.85) (>= ?w 10)))
  =>
  (emit-output (str-cat "flag:stock_template:avg=" ?a))
  (assert (decision (trace_id ?t) (verdict flag))))

(defrule allow-when-fresh
  (response-similarity (trace_id ?t) (max_cosine ?m) (avg_cosine ?a))
  (test (and (< ?m 0.92) (< ?a 0.85)))
  =>
  (emit-output "allow:fresh"))
```

## Streams

- `response.embeddings` — last N responses per (agent, intent), TTL'd
- `intent.classifier` — bucket the response into a comparison set
- `agent.config` — per-agent thresholds (low for creative, high for
  customer-status updates where sameness is desired)

## Routes

| Verdict   | Route                                                          |
|-----------|----------------------------------------------------------------|
| reprompt  | re-run agent with hint "your last K responses were too similar — vary structure or wording" |
| flag      | continue, but raise an offline alert that the agent has stalled into a template |
| allow     | pass through                                                   |

## Sample violation → decision

Triage agent has answered eight tickets in a row with: opening pleasantry,
three numbered bullets, "let me know if this works."

A ninth ticket arrives. Proposed response embeds at cosine 0.94 against
the most recent answer. Rolling average over the window is 0.89.

Output:
```
reprompt:near_duplicate:max=0.94
flag:stock_template:avg=0.89
```

Run reprompts; agent produces a structurally different answer that
mentions the actual specifics of ticket nine. The `flag` verdict creates
an alert in the eval dashboard pointing at this agent's recent window.

## Why it's a good demo

1. **It's the kind of bug that doesn't fail any test.** Nothing is
   wrong with any individual response. The pathology only exists across
   the rolling window. A governor with a streaming-fact view (recent
   embeddings) is the natural place to detect it; a one-shot eval can't
   see it.

2. **It produces an honest mirror.** Combined with `decision-journal-kg`
   and `drift-detector`, you get a longitudinal record of when an agent
   started flattening — and you can correlate that with prompt edits,
   model swaps, or fine-tune updates. Most platforms can't even ask the
   question.

3. **It pairs with `anti-sycophancy` and `tone-calibrator` for a
   "responses-with-spine" bundle:** don't agree reflexively, don't open
   every reply the same way, don't slide into channel-mismatched
   register. Three small CLIPS rule packs that together change how the
   agent sounds.
