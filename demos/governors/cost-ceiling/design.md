# Governor · `cost-ceiling`

Hard maximum spend per request, per tenant, or per workflow. When projected
spend exceeds the ceiling, the run is halted, escalated, or routed to a
cheaper model.

## Purpose

The unforgiving cost guard. Any agent on a recursive loop or a high-volume
workflow can quietly burn $$ — this is the rule that catches it before the
bill arrives.

## Trigger event

`pre_tool_call`, `pre_model_call` — runs before any expensive verb.

## Facts asserted

```clips
(deftemplate spend
  (slot tenant)
  (slot trace_id)
  (slot dollars_used)
  (slot dollars_projected)
  (slot ceiling))
```

## Rules

```clips
(defrule break-when-projection-exceeds-ceiling
  (spend (trace_id ?t) (dollars_projected ?p) (ceiling ?c) (tenant ?tn))
  (test (>= ?p ?c))
  =>
  (emit-output (str-cat "halt:cost_ceiling:tenant=" ?tn ":projected=" ?p))
  (assert (decision (trace_id ?t) (verdict halt))))

(defrule warn-at-eighty-percent
  (spend (trace_id ?t) (dollars_used ?u) (ceiling ?c))
  (test (>= ?u (* ?c 0.8)))
  =>
  (emit-output (str-cat "warn:cost_ceiling:80pct:trace=" ?t)))
```

## Streams

- `spend.updates` — each tool/model call updates the running total
- `tenant.config` — per-tenant ceilings (loaded once, refreshed on TTL)

## Routes

| Verdict | Route                                                                |
|---------|----------------------------------------------------------------------|
| halt    | abort run, return error envelope                                     |
| warn    | continue, emit alert to ops channel                                  |
| route   | swap model to cheaper alternative (with `escalation-ladder` integration) |

## Sample violation → decision

Input: trace `abc123`, projected $7.50 against tenant ceiling $5.00.
Output: `halt:cost_ceiling:tenant=acme:projected=7.50`.
Span: governor decision recorded; downstream tool call never executes.

## Why it's a good demo

The most boring governor is the most useful one to show first — every
customer immediately understands the value, and it demonstrates the basic
CLIPS-rule + `(emit-output ...)` + route pattern that every other governor
in the catalog inherits.
