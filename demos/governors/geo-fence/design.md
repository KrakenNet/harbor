# Governor · `geo-fence`

Restricts requests, model calls, or data egress based on the geographic
origin of the principal or the destination of the data.

## Purpose

GDPR, data-residency contracts, US-export controls — all need to enforce
"this data stays in this region" or "this user cannot trigger this verb
from that country." Centralized in one rule pack.

## Trigger event

`pre_request`, `pre_model_call`, `pre_tool_call`.

## Facts asserted

```clips
(deftemplate geo
  (slot trace_id)
  (slot principal_country)
  (slot data_residency)   ; eu | us | apac
  (slot model_region)     ; eu | us | apac
  (slot tool_egress))     ; country code or "any"
```

## Rules

```clips
(defrule halt-cross-border-eu
  (geo (trace_id ?t) (data_residency eu) (model_region ?r))
  (test (neq ?r eu))
  =>
  (emit-output (str-cat "halt:residency:eu_data->" ?r))
  (assert (decision (trace_id ?t) (verdict halt))))

(defrule halt-export-controlled
  (geo (trace_id ?t) (principal_country ?c))
  (test (member ?c (create$ ir kp ru sy)))
  =>
  (emit-output (str-cat "halt:export_control:" ?c))
  (assert (decision (trace_id ?t) (verdict halt))))
```

## Streams

- `geo.principal` — IP geolocation + JWT claim cross-check
- `route.config` — model regions per provider
- `tool.registry` — egress destinations

## Routes

| Verdict | Route                                                      |
|---------|------------------------------------------------------------|
| halt    | abort, log compliance event, return policy error envelope  |
| route   | force model selection to the correct region (when possible)|

## Sample violation → decision

EU-residency tenant inadvertently configured to use a US-region model.
Output: `halt:residency:eu_data->us`. Admin gets an alert.

## Why it's a good demo

One of the few governors where the *correct* answer is sometimes "switch
which model you're using" rather than refuse. Pairs with
`escalation-ladder` and `tenant-quota` for region-aware routing.
