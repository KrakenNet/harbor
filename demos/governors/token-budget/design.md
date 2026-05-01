# Governor · `token-budget`

Caps total tokens (prompt + completion) per request, per workflow, or per
tenant window. Sibling to `cost-ceiling` but operates on the unit the
model actually charges.

## Purpose

Tokens are the truer signal than dollars when comparing across providers
and models. This governor halts runaway context-stuffing or recursive
prompt growth before any model call exceeds its allotment.

## Trigger event

`pre_model_call`.

## Facts asserted

```clips
(deftemplate token-usage
  (slot trace_id)
  (slot tenant)
  (slot tokens_used)
  (slot tokens_projected)
  (slot budget))
```

## Rules

```clips
(defrule halt-projection-over-budget
  (token-usage (trace_id ?t) (tokens_projected ?p) (budget ?b))
  (test (>= ?p ?b))
  =>
  (emit-output (str-cat "halt:token_budget:projected=" ?p ":budget=" ?b))
  (assert (decision (trace_id ?t) (verdict halt))))

(defrule trim-context-over-90pct
  (token-usage (trace_id ?t) (tokens_used ?u) (budget ?b))
  (test (>= ?u (* ?b 0.9)))
  =>
  (emit-output "trim:context_window")
  (assert (decision (trace_id ?t) (verdict trim))))

(defrule warn-at-half
  (token-usage (trace_id ?t) (tokens_used ?u) (budget ?b))
  (test (>= ?u (* ?b 0.5)))
  =>
  (emit-output "warn:token_budget:50pct"))
```

## Streams

- `tokens.usage` — running counter from each model call
- `tenant.config` — per-tenant budgets and trimming policy

## Routes

| Verdict | Route                                                        |
|---------|--------------------------------------------------------------|
| halt    | abort run                                                    |
| trim    | drop oldest non-system messages until under 80% of budget    |
| warn    | continue, emit telemetry                                     |

## Sample violation → decision

Trace `xyz789` projected at 145k tokens against an 128k budget.
Output: `halt:token_budget:projected=145000:budget=128000`.

## Why it's a good demo

Shows how a governor can do something more useful than refuse — `trim`
actively repairs the prompt and lets the call proceed. Combine with
`escalation-ladder` to route long-context requests to a larger model.
