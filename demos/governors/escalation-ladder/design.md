# Governor · `escalation-ladder`

Cheaper-models-first, by policy. Calls to a small model are tried first;
on failure (low confidence, schema reject, retry exhaustion) the
governor promotes the request up the ladder to a larger model — and
records the cost of having needed the bigger model.

The ladder isn't just a router. It's a *measurement* of which requests
genuinely needed the big model, which is a much more interesting number
than the average cost of a request.

## Purpose

Most production systems either default to the big model (expensive) or
default to the small model and silently fail (worse). The right answer
is "small first, big when needed, *and tell me how often you needed
big*." This governor implements the policy and the telemetry.

The ladder is configurable but typically: small open-weights → mid →
frontier → frontier-with-thinking → frontier-with-thinking-and-tools.
Each rung is tried before the next.

## Trigger event

`pre_model_call`, plus `post_response` for failure detection.

## Facts asserted

```clips
(deftemplate model-attempt
  (slot trace_id)
  (slot rung)              ; 0..N, position on the ladder
  (slot model)
  (slot status)            ; success | low_confidence | schema_fail | timeout | refusal
  (slot retries_at_rung)
  (slot max_retries)
  (slot ladder_length))

(deftemplate decision
  (slot trace_id)
  (slot verdict))            ; promote | retry | accept | exhausted
```

## Rules

```clips
(defrule promote-on-failure
  (model-attempt (trace_id ?t) (rung ?r) (status ?s) (retries_at_rung ?n)
                 (max_retries ?m) (ladder_length ?l))
  (test (and (member ?s (create$ low_confidence schema_fail timeout))
             (>= ?n ?m)
             (< ?r (- ?l 1))))
  =>
  (emit-output (str-cat "promote:rung=" ?r "->" (+ ?r 1) ":reason=" ?s))
  (assert (decision (trace_id ?t) (verdict promote))))

(defrule retry-at-rung
  (model-attempt (trace_id ?t) (rung ?r) (status ?s) (retries_at_rung ?n) (max_retries ?m))
  (test (and (member ?s (create$ low_confidence schema_fail))
             (< ?n ?m)))
  =>
  (emit-output (str-cat "retry:rung=" ?r ":n=" ?n))
  (assert (decision (trace_id ?t) (verdict retry))))

(defrule exhaust-ladder
  (model-attempt (trace_id ?t) (rung ?r) (ladder_length ?l) (status ?s))
  (test (and (= ?r (- ?l 1)) (neq ?s success)))
  =>
  (emit-output (str-cat "exhausted:" ?s))
  (assert (decision (trace_id ?t) (verdict exhausted))))

(defrule refusal-pin-rung
  (model-attempt (trace_id ?t) (status refusal))
  =>
  (emit-output "halt:refusal_no_promote")
  (assert (decision (trace_id ?t) (verdict exhausted))))
```

## Streams

- `model.registry` — defines the ladder per agent / per domain
- `attempt.history` — running tally of which rungs were tried per trace
- `confidence.scorer` — feeds in `low_confidence` status
- `schema.validator` — feeds in `schema_fail` status (same data the
  `schema-validator` governor consumes)

## Routes

| Verdict   | Route                                                              |
|-----------|--------------------------------------------------------------------|
| retry     | re-run at same rung (transient or first-attempt failure)           |
| promote   | re-run at next rung; `cost-ceiling` checked again before the call  |
| accept    | first successful rung wins; record `winning_rung` in span          |
| exhausted | top of ladder failed too — return error envelope, alert eval team  |

## Sample violation → decision

Triage agent declared with ladder = `[haiku, sonnet, opus, opus+thinking]`.

- Rung 0 (`haiku`): two attempts, both `schema_fail`. → `retry`, then
  `promote`.
- Rung 1 (`sonnet`): one attempt, `low_confidence` (score 0.51 vs
  threshold 0.7). → `promote`.
- Rung 2 (`opus`): success.

Trace records `winning_rung=2`. Aggregate dashboard shows: *for this
agent, 23% of requests required rung≥2 this week, up from 11% last week.*
That's a leading indicator that something has gotten harder — a prompt
edit, a content shift, a regression somewhere — and is the kind of
signal you want to surface before it becomes a complaint.

## Why it's a good demo

1. **It converts cost into a signal, not just an expense.** The ratio
   of small-model wins to total requests is a quality metric — when it
   drops, *something* changed. Pair with `cost-ceiling` and you have
   per-request economics that explain themselves.

2. **It works the rule layer hard.** The governor needs facts from the
   confidence scorer, the schema validator, and the model registry, and
   has to coordinate retry/promote/accept/exhaust transitions cleanly.
   It's a good showcase of CLIPS facts as a small state machine, which
   is more flexible than a hand-coded router.

3. **It composes with `confidence-threshold`, `schema-validator`,
   `cost-ceiling`, and `pre-mortem-required`:** the small-model attempts
   feed the failure signals; the big-model promotion respects the cost
   cap; high-stakes plans must pre-mortem before any rung fires. The
   composition is the demo: no single governor does the work alone.
