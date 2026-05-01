# Governor · `rate-limit`

Enforces request-per-second / minute / hour caps per tenant, per user, or
per API key. Token bucket fed from a shared counter stream.

## Purpose

Prevents abuse and protects upstream provider quotas. Distinct from
`tenant-quota` (which is total billable units) — this is short-window
throttling.

## Trigger event

`pre_request` (workflow / chat ingress), `pre_model_call`.

## Facts asserted

```clips
(deftemplate rate-window
  (slot trace_id)
  (slot tenant)
  (slot principal)
  (slot scope)            ; rps | rpm | rph
  (slot count)
  (slot limit))
```

## Rules

```clips
(defrule throttle-when-over-limit
  (rate-window (trace_id ?t) (scope ?s) (count ?c) (limit ?l) (principal ?p))
  (test (>= ?c ?l))
  =>
  (emit-output (str-cat "halt:rate_limit:" ?s ":principal=" ?p))
  (assert (decision (trace_id ?t) (verdict halt))))

(defrule queue-near-limit
  (rate-window (trace_id ?t) (scope ?s) (count ?c) (limit ?l))
  (test (and (>= ?c (* ?l 0.9)) (< ?c ?l)))
  =>
  (emit-output (str-cat "queue:rate_limit:" ?s))
  (assert (decision (trace_id ?t) (verdict queue))))
```

## Streams

- `rate.counters` — sliding-window counters by tenant/principal/scope
- `tenant.config` — per-tenant limits

## Routes

| Verdict | Route                                                    |
|---------|----------------------------------------------------------|
| halt    | return 429 with `Retry-After`                            |
| queue   | enqueue request, dispatch when window opens              |

## Sample violation → decision

Principal `user_42` issues an 11th request in a 10-rpm window.
Output: `halt:rate_limit:rpm:principal=user_42`. Caller gets 429.

## Why it's a good demo

The simplest governor that demonstrably needs *streams* — counters live
outside the rule engine and feed in continuously. Shows the
stream-and-fact separation cleanly.
