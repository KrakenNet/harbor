# Governor · `loop-breaker`

Detects when an agent is repeating the same action with the same arguments
and halts before infinite recursion.

## Purpose

Agents get stuck. ReAct loops, broken tool retries, cyclic reasoning —
they all look alike: same `(tool, args_hash)` reasserted N times.
This governor names the pattern and breaks it.

## Trigger event

`pre_tool_call`, `on_workflow_step`.

## Facts asserted

```clips
(deftemplate action-history
  (slot trace_id)
  (slot tool)
  (slot args_hash)
  (slot count_in_window)
  (slot window_steps))
```

## Rules

```clips
(defrule halt-tight-loop
  (action-history (trace_id ?t) (tool ?tool) (count_in_window ?n))
  (test (>= ?n 3))
  =>
  (emit-output (str-cat "halt:loop_detected:" ?tool ":n=" ?n))
  (assert (decision (trace_id ?t) (verdict halt))))

(defrule warn-repeating-twice
  (action-history (trace_id ?t) (tool ?tool) (count_in_window 2))
  =>
  (emit-output (str-cat "warn:repeat:" ?tool)))
```

## Streams

- `action.history` — last N steps per trace lineage with args hash
- `agent.config` — per-agent window size

## Routes

| Verdict | Route                                              |
|---------|----------------------------------------------------|
| halt    | abort run, mark "loop" in trace, alert ops         |
| warn    | continue, emit telemetry                           |

## Sample violation → decision

Agent calls `search(query="X")` three times in a row with identical
args. Output: `halt:loop_detected:search:n=3`.

## Why it's a good demo

The cheapest possible safety net for any agent that loops — and every
agent eventually does. Easy to explain, visibly useful in demos that
intentionally trigger it.
