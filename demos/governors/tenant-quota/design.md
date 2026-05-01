# Governor · `tenant-quota`

Total billable units (requests, tokens, dollars, executions) per tenant
per billing period. Differs from `rate-limit` (short-window throttling)
and `cost-ceiling` (per-request cap).

## Purpose

Multi-tenant SaaS needs a per-tenant ceiling that matches the contract.
Hitting the quota produces a billing-aware response rather than a
generic 429.

## Trigger event

`pre_request`.

## Facts asserted

```clips
(deftemplate quota
  (slot trace_id)
  (slot tenant)
  (slot units_used)
  (slot units_allowed)
  (slot unit_kind)        ; requests | tokens | dollars | executions
  (slot period_end))      ; ISO-8601
```

## Rules

```clips
(defrule halt-when-exhausted
  (quota (trace_id ?t) (tenant ?tn) (units_used ?u) (units_allowed ?a) (unit_kind ?k))
  (test (>= ?u ?a))
  =>
  (emit-output (str-cat "halt:quota_exhausted:" ?tn ":" ?k))
  (assert (decision (trace_id ?t) (verdict halt))))

(defrule warn-near-quota
  (quota (trace_id ?t) (tenant ?tn) (units_used ?u) (units_allowed ?a))
  (test (>= ?u (* ?a 0.9)))
  =>
  (emit-output (str-cat "warn:quota_90pct:" ?tn)))
```

## Streams

- `billing.counters` — period-to-date counters per tenant
- `tenant.config` — quota per kind

## Routes

| Verdict | Route                                                          |
|---------|----------------------------------------------------------------|
| halt    | return 402 / quota-exhausted envelope, link to upgrade         |
| warn    | continue, emit notification to tenant admin                    |

## Sample violation → decision

Tenant `acme` has used 500k of 500k requests this billing period. New
request arrives. Output: `halt:quota_exhausted:acme:requests`.

## Why it's a good demo

The governor that customers ask about the moment they consider going to
production. Pairs with `cost-ceiling` (instantaneous) and `rate-limit`
(short-window) to form the full billing-protection bundle.
