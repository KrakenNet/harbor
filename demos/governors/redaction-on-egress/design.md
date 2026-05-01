# Governor · `redaction-on-egress`

Last-mile redaction at the boundary where data leaves Railyard — outbound
webhooks, email, third-party tools, log shippers. Catches things every
prior layer missed.

## Purpose

Defense in depth. PII scanners run earlier; this is the final boundary
sweep. The cost of a leak at egress is high; the cost of one extra scan
is trivial.

## Trigger event

`pre_egress` — fires immediately before any outbound transport
(webhook delivery, email send, log forwarder, integration call).

## Facts asserted

```clips
(deftemplate egress-payload
  (slot trace_id)
  (slot destination)      ; webhook | email | log_shipper | integration:<name>
  (slot category)         ; email | phone | ssn | secret | api_key | jwt
  (slot count)
  (slot tenant_strict))   ; true | false
```

## Rules

```clips
(defrule halt-secrets-always
  (egress-payload (trace_id ?t) (category ?c) (count ?n))
  (test (and (member ?c (create$ secret api_key jwt)) (> ?n 0)))
  =>
  (emit-output (str-cat "halt:egress_secret:" ?c))
  (assert (decision (trace_id ?t) (verdict halt))))

(defrule redact-pii-strict
  (egress-payload (trace_id ?t) (category ?c) (tenant_strict true) (count ?n))
  (test (> ?n 0))
  =>
  (emit-output (str-cat "redact:egress_strict:" ?c))
  (assert (decision (trace_id ?t) (verdict redact))))

(defrule warn-pii-permissive
  (egress-payload (trace_id ?t) (category ?c) (tenant_strict false) (count ?n))
  (test (> ?n 0))
  =>
  (emit-output (str-cat "warn:egress_pii:" ?c)))
```

## Streams

- `egress.scanner` — re-scan of every outbound payload
- `tenant.config` — strict vs permissive mode
- `integration.registry` — destination metadata

## Routes

| Verdict | Route                                                 |
|---------|-------------------------------------------------------|
| halt    | drop the payload, alert security, mark trace dirty    |
| redact  | replace matched spans before transport                |
| warn    | continue, emit telemetry                              |

## Sample violation → decision

Outbound webhook payload contains a stray `sk-live-...` API key.
Output: `halt:egress_secret:api_key`. The webhook never fires.

## Why it's a good demo

Pairs with `pii-redactor` to demonstrate defense in depth — same
detection logic, different lifecycle hook, different consequences.
Customers immediately see the value when one of the earlier layers
misses something in a live demo.
