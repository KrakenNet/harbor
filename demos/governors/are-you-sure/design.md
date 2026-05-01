# Governor · `are-you-sure`

Before any irreversible verb fires — `delete`, `send_email`, `apply_change`,
`transfer_funds`, `merge_pr`, `post_to_customer` — the agent is forced to
pause, write down what it's about to do, *why*, and what its prior would
have to be to back out. Only then is the verb allowed.

This is not a HITL trigger. The human is not in the loop. The *agent* is
forced to be in the loop with itself.

## Purpose

LLMs are fluent enough to talk themselves into bad actions. The remedy is
a structural pause: a one-shot self-audit step that produces an immutable
rationale before commitment. The same trick a careful human uses when
they catch themselves about to hit Send.

## Trigger event

`pre_tool_call` for any tool tagged `irreversible: true` in its registry
entry.

## Facts asserted

```clips
(deftemplate proposed-action
  (slot trace_id)
  (slot tool)
  (slot args_hash)
  (slot rationale)             ; populated by the self-audit step
  (slot would_undo_if)         ; populated by the self-audit step
  (slot conviction)            ; 0..1, populated by the self-audit step
  (slot prior_attempts))       ; same args_hash seen recently?

(deftemplate decision
  (slot trace_id)
  (slot verdict))               ; allow | force_audit | halt
```

## Rules

```clips
(defrule require-rationale
  (proposed-action (trace_id ?t) (rationale "") (tool ?tool))
  =>
  (emit-output (str-cat "force_audit:" ?tool ":missing_rationale"))
  (assert (decision (trace_id ?t) (verdict force_audit))))

(defrule require-undo-criterion
  (proposed-action (trace_id ?t) (would_undo_if ""))
  =>
  (emit-output "force_audit:missing_undo_criterion")
  (assert (decision (trace_id ?t) (verdict force_audit))))

(defrule reject-low-conviction
  (proposed-action (trace_id ?t) (conviction ?c))
  (test (< ?c 0.5))
  =>
  (emit-output (str-cat "halt:low_conviction:" ?c))
  (assert (decision (trace_id ?t) (verdict halt))))

(defrule reject-repeat-after-failure
  (proposed-action (trace_id ?t) (args_hash ?h) (prior_attempts ?n))
  (test (>= ?n 2))
  =>
  (emit-output "halt:repeat_after_failure")
  (assert (decision (trace_id ?t) (verdict halt))))

(defrule allow
  (proposed-action (trace_id ?t)
                   (rationale ?r&~"")
                   (would_undo_if ?u&~"")
                   (conviction ?c)
                   (prior_attempts ?n))
  (test (and (>= ?c 0.5) (< ?n 2)))
  =>
  (emit-output "allow")
  (assert (decision (trace_id ?t) (verdict allow))))
```

## Streams

- `tool.registry` — sources `irreversible: true` tags
- `recent.attempts` — counts repeat `args_hash` within a 1h window per trace lineage

## Routes

| Verdict      | Route                                                       |
|--------------|-------------------------------------------------------------|
| force_audit  | inject self-audit DSPy step, re-run governor with results   |
| halt         | abort, emit error with diagnostic                           |
| allow        | proceed; rationale + undo criterion are persisted to trace  |

## Sample violation → decision

Tool: `send_email_to_customer`. Tagged irreversible.

First pass:
> proposed-action: rationale="", would_undo_if="", conviction=0
→ `force_audit:send_email_to_customer:missing_rationale`

Self-audit injected; agent fills:
> rationale="We owe a status update on ticket 4471 per SLA at 18:00."
> would_undo_if="The ticket was already resolved or escalated to Tier 2."
> conviction=0.82

Second pass:
→ `allow`. Email sends. Rationale persisted as a span attribute.

## Why it's a good demo

1. **It teaches a non-obvious lesson:** governors aren't only safety
   filters. They can shape the *agent's reasoning structure* by demanding
   artifacts (rationale, undo criterion) it must produce before
   progressing. That's a different mental model than most platforms expose.
2. **The audit trail it produces is real engineering output.** Every
   irreversible action in the system gets a rationale row attached.
   Combined with `decision-journal-kg`, this becomes a longitudinal
   record of why the system did what it did — invaluable for both
   compliance and offline learning.
3. **It pairs with `devils-advocate` and `pre-mortem-first` for a single
   coherent story:** before high-stakes verbs, force the agent to slow
   down, predict, and write down its reasoning. Once the user has seen
   one trace tree decorated with these artifacts, they can't go back.
