# Governor · `confidence-threshold`

Rejects or escalates outputs whose self-reported (or externally scored)
confidence falls below a per-task threshold.

## Purpose

Low-confidence answers are worse than no answer in many domains
(medical, legal, finance). This governor makes the threshold explicit
and enforced rather than implicit and ignored.

## Trigger event

`post_response`.

## Facts asserted

```clips
(deftemplate confidence
  (slot trace_id)
  (slot agent)
  (slot score)            ; 0..1
  (slot source)           ; self_report | classifier | ensemble
  (slot threshold))
```

## Rules

```clips
(defrule reject-below-threshold
  (confidence (trace_id ?t) (score ?s) (threshold ?th))
  (test (< ?s ?th))
  =>
  (emit-output (str-cat "halt:low_confidence:" ?s "<" ?th))
  (assert (decision (trace_id ?t) (verdict halt))))

(defrule escalate-when-borderline
  (confidence (trace_id ?t) (score ?s) (threshold ?th))
  (test (and (>= ?s ?th) (< ?s (+ ?th 0.1))))
  =>
  (emit-output (str-cat "escalate:borderline:" ?s))
  (assert (decision (trace_id ?t) (verdict escalate))))
```

## Streams

- `confidence.scorer` — self-report or external classifier
- `agent.registry` — per-agent thresholds

## Routes

| Verdict   | Route                                              |
|-----------|----------------------------------------------------|
| halt      | suppress response, return "uncertain" envelope     |
| escalate  | re-run on bigger model (`escalation-ladder` hook)  |
| allow     | pass through                                       |

## Sample violation → decision

Agent `medical-triage` returns score 0.42 against threshold 0.75.
Output: `halt:low_confidence:0.42<0.75`.

## Why it's a good demo

Sets up the `escalation-ladder` and `conviction-tax` creative items.
Shows the platform treats confidence as a first-class governance signal,
not an afterthought.
