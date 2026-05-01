# Governor · `latency-sla`

Halts or downgrades a request when projected end-to-end latency exceeds
the channel's SLA — e.g. a chat endpoint that promises 2s p95 won't tolerate
a deep research workflow.

## Purpose

Protects user-facing latency contracts. Each route declares a budget; the
governor watches accumulated time and the projected cost of the next step.

## Trigger event

`pre_tool_call`, `pre_model_call`, `on_workflow_step`.

## Facts asserted

```clips
(deftemplate latency
  (slot trace_id)
  (slot channel)          ; chat | api | batch
  (slot elapsed_ms)
  (slot projected_ms)
  (slot budget_ms))
```

## Rules

```clips
(defrule halt-when-budget-blown
  (latency (trace_id ?t) (projected_ms ?p) (budget_ms ?b))
  (test (>= ?p ?b))
  =>
  (emit-output (str-cat "halt:latency_sla:projected=" ?p))
  (assert (decision (trace_id ?t) (verdict halt))))

(defrule degrade-near-budget
  (latency (trace_id ?t) (elapsed_ms ?e) (budget_ms ?b))
  (test (>= ?e (* ?b 0.7)))
  =>
  (emit-output "degrade:skip_optional_steps")
  (assert (decision (trace_id ?t) (verdict degrade))))
```

## Streams

- `span.timing` — running elapsed-time per trace
- `route.config` — channel SLAs

## Routes

| Verdict | Route                                                  |
|---------|--------------------------------------------------------|
| halt    | return partial result with timeout envelope            |
| degrade | skip non-critical steps (RAG enrichment, second-opinion) |

## Sample violation → decision

Chat channel budget 2000ms; trace at 1700ms with 600ms projected next
step. Output: `halt:latency_sla:projected=2300`. Caller gets a partial
response with a timeout marker.

## Why it's a good demo

Demonstrates that "policy" includes more than safety — it includes
quality of service. Pairs with `escalation-ladder` (use a fast small
model first) and `cost-ceiling`.
