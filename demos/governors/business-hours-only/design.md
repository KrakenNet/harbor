# Governor · `business-hours-only`

Restricts certain verbs (customer email, deploy, support callback) to
business hours in the appropriate timezone, with optional on-call
exceptions.

## Purpose

Some automated actions are *technically* fine to execute at 3am but cause
operational pain — deploys without humans awake, emails that arrive in
sleep hours, callback queues that get stale overnight. This governor
draws the line.

## Trigger event

`pre_tool_call`, `pre_workflow_start`.

## Facts asserted

```clips
(deftemplate clock
  (slot trace_id)
  (slot tool)
  (slot tz)               ; e.g. "America/New_York"
  (slot local_hour)       ; 0..23
  (slot weekday)          ; mon..sun
  (slot oncall_override)) ; true | false
```

## Rules

```clips
(defrule defer-after-hours
  (clock (trace_id ?t) (tool ?tool) (local_hour ?h) (oncall_override false))
  (test (or (< ?h 9) (>= ?h 18)))
  =>
  (emit-output (str-cat "defer:after_hours:" ?tool ":h=" ?h))
  (assert (decision (trace_id ?t) (verdict defer))))

(defrule defer-weekend
  (clock (trace_id ?t) (weekday ?d) (oncall_override false))
  (test (or (eq ?d sat) (eq ?d sun)))
  =>
  (emit-output (str-cat "defer:weekend:" ?d))
  (assert (decision (trace_id ?t) (verdict defer))))

(defrule allow-with-oncall
  (clock (trace_id ?t) (oncall_override true))
  =>
  (emit-output "allow:oncall_override"))
```

## Streams

- `clock.local` — current time in target timezone
- `oncall.calendar` — who's on for emergency overrides
- `tool.registry` — which tools are hours-restricted

## Routes

| Verdict | Route                                                |
|---------|------------------------------------------------------|
| defer   | enqueue for next business-hours window               |
| allow   | proceed                                              |

## Sample violation → decision

Workflow tries to send a `customer_email_blast` at 03:14 local with no
on-call override. Output: `defer:after_hours:customer_email_blast:h=3`.
The job is requeued for 09:00.

## Why it's a good demo

The "obvious in hindsight" governor. Shows how time-of-day becomes a
first-class fact rather than something every workflow has to recheck.
