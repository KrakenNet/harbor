# Governor · `hitl-trigger`

Routes high-risk verbs through a human approval step before execution.
The agent pauses; the run resumes when a human approves or denies via
the inbox.

## Purpose

Some actions — wire transfers, prod deploys, customer-facing emails over
a threshold — should never be unilateral. This governor declares the
boundary of human-required and integrates with the approval inbox.

## Trigger event

`pre_tool_call` for tools tagged `hitl_required: true` or matching
risk-class predicates.

## Facts asserted

```clips
(deftemplate hitl-check
  (slot trace_id)
  (slot tool)
  (slot risk_class)       ; low | medium | high | critical
  (slot dollar_amount)    ; optional, for finance verbs
  (slot tenant_policy))   ; threshold-set name
```

## Rules

```clips
(defrule require-hitl-critical
  (hitl-check (trace_id ?t) (risk_class critical))
  =>
  (emit-output "pause:hitl_required:critical")
  (assert (decision (trace_id ?t) (verdict pause))))

(defrule require-hitl-by-amount
  (hitl-check (trace_id ?t) (dollar_amount ?d) (tenant_policy ?p))
  (test (>= ?d (threshold-for ?p)))
  =>
  (emit-output (str-cat "pause:hitl_required:amount=" ?d))
  (assert (decision (trace_id ?t) (verdict pause))))

(defrule allow-low-risk
  (hitl-check (trace_id ?t) (risk_class low))
  =>
  (emit-output "allow:hitl_not_required"))
```

## Streams

- `tool.registry` — risk classes and `hitl_required` tags
- `tenant.config` — dollar thresholds per policy
- `approval.inbox` — outbound routing target

## Routes

| Verdict | Route                                                            |
|---------|------------------------------------------------------------------|
| pause   | suspend run, post approval card to inbox, resume on decision     |
| allow   | proceed                                                          |
| halt    | reject (downstream of denial)                                    |

## Sample violation → decision

Tool `transfer_funds`, amount=$25,000, policy threshold $10,000.
Output: `pause:hitl_required:amount=25000`. Run suspends; approval
card appears in the assigned reviewer's inbox.

## Why it's a good demo

The first governor most customers actually deploy. Pairs with
`approval-policy` (which approver) and `are-you-sure` (which forces the
agent to write a rationale before the human even looks).
