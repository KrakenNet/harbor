# Governor · `drift-detector`

Watches the *embedding distance* between an agent's recent behavior and
its declared identity (system prompt + role spec). When the cloud of
recent responses moves too far from the anchor, the agent is — by
definition — off-policy.

The premise: agents drift. Sometimes the drift is good (improvement
from feedback). Often it isn't (prompt erosion, tool injection, slow
slide into a different persona). This governor names the drift in a
unit that can be plotted.

## Purpose

Most "off-policy" failures are not single bad responses. They're the
slow accumulation of small deviations until the agent is, somehow,
doing a different job than it was hired for. The classic case: a
support agent slowly starts giving sales advice because its tool list
includes an upsell tool and the dialogue context keeps mentioning
pricing.

The detector runs continuously, comparing each response embedding (and
the rolling cluster centroid of the last N) against the embedding of
the anchor (the system prompt + role description). When the centroid
exceeds a threshold distance from the anchor, the agent gets flagged
or paused.

## Trigger event

`post_response`, plus an offline `on_schedule` sweep for trend analysis.

## Facts asserted

```clips
(deftemplate drift
  (slot agent)
  (slot trace_id)
  (slot anchor_distance)    ; cosine distance, single response vs anchor
  (slot centroid_distance)  ; cosine distance, last-N centroid vs anchor
  (slot window_size)
  (slot rate_per_day))      ; trend slope (1/day cosine units)

(deftemplate decision
  (slot trace_id)
  (slot agent)
  (slot verdict))            ; allow | flag | pause
```

## Rules

```clips
(defrule pause-runaway-drift
  (drift (agent ?a) (trace_id ?t) (centroid_distance ?d))
  (test (>= ?d 0.4))
  =>
  (emit-output (str-cat "pause:drift:agent=" ?a ":centroid=" ?d))
  (assert (decision (trace_id ?t) (agent ?a) (verdict pause))))

(defrule flag-fast-trend
  (drift (agent ?a) (trace_id ?t) (rate_per_day ?r))
  (test (>= ?r 0.05))
  =>
  (emit-output (str-cat "flag:drift_trend:agent=" ?a ":rate=" ?r))
  (assert (decision (trace_id ?t) (agent ?a) (verdict flag))))

(defrule flag-single-outlier
  (drift (trace_id ?t) (anchor_distance ?d) (agent ?a))
  (test (>= ?d 0.55))
  =>
  (emit-output (str-cat "flag:outlier:" ?d))
  (assert (decision (trace_id ?t) (agent ?a) (verdict flag))))
```

## Streams

- `response.embeddings` — same stream `echo-chamber-breaker` uses,
  reused here
- `agent.anchor_embedding` — cached embedding of system prompt + role
- `agent.history` — rolling window of last N response embeddings, with
  centroid maintained incrementally

## Routes

| Verdict | Route                                                            |
|---------|------------------------------------------------------------------|
| pause   | take agent offline for review, alert owner with a 2D map of recent vs anchor (uses `embedding-cartographer`) |
| flag    | continue, post warning to eval dashboard with the drift trace    |
| allow   | pass through                                                     |

## Sample violation → decision

Agent `support-bot` was anchored to a support-only system prompt. Over
a week, its centroid distance from the anchor crept from 0.18 to 0.43,
a rate of ~0.04/day, with most responses now mentioning upsell paths.

Today's centroid_distance hits 0.41:
```
pause:drift:agent=support-bot:centroid=0.41
flag:drift_trend:agent=support-bot:rate=0.04
```

The agent is paused. The owner gets a 2D scatter showing the cloud has
visibly migrated toward "sales" territory.

## Why it's a good demo

1. **It treats agent identity as a measurable thing.** The system
   prompt isn't aspirational — it's the anchor in embedding space, and
   the platform can quantitatively answer "is this agent still itself?"
   Most platforms can't even pose the question.

2. **It produces a visualization, not just a verdict.** Combined with
   `embedding-cartographer`, the drift report includes a map. That map
   is the kind of artifact that ends up screenshotted in postmortems
   and pinned in the on-call doc.

3. **It pairs with `tone-calibrator`, `anti-sycophancy`, and
   `decision-journal-kg`:** the first two stop micro-deviations per
   turn; the journal records *why* the agent did what it did; this one
   integrates over time. The four together turn agent governance into
   something with a longitudinal arc, not a one-shot guardrail.
