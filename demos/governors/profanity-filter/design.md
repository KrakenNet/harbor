# Governor · `profanity-filter`

Blocks or rewrites profane, slurred, or otherwise unacceptable language in
both inbound prompts and outbound responses, with per-tenant severity
thresholds.

## Purpose

Brand-safety floor for customer-facing channels. Different tenants want
different thresholds — a B2B legal product wants zero tolerance, a gaming
community manager wants only slurs blocked. The governor centralizes that
policy.

## Trigger event

`pre_model_call`, `post_response`.

## Facts asserted

```clips
(deftemplate profanity-hit
  (slot trace_id)
  (slot stage)
  (slot severity)         ; mild | strong | slur
  (slot count)
  (slot tenant_threshold)) ; mild | strong | slur
```

## Rules

```clips
(defrule block-slurs-always
  (profanity-hit (trace_id ?t) (severity slur))
  =>
  (emit-output "halt:slur_detected")
  (assert (decision (trace_id ?t) (verdict halt))))

(defrule block-above-tenant-threshold
  (profanity-hit (trace_id ?t) (severity ?s) (tenant_threshold ?th))
  (test (or (and (eq ?s strong) (eq ?th mild))
            (and (eq ?s strong) (eq ?th strong))))
  =>
  (emit-output (str-cat "rewrite:profanity:" ?s))
  (assert (decision (trace_id ?t) (verdict rewrite))))

(defrule pass-when-below-threshold
  (profanity-hit (trace_id ?t) (severity mild) (tenant_threshold strong))
  =>
  (emit-output "allow:below_threshold"))
```

## Streams

- `profanity.scanner.hits` — keyword + classifier hits with severity
- `tenant.config` — per-tenant severity threshold

## Routes

| Verdict | Route                                                |
|---------|------------------------------------------------------|
| halt    | abort, return safety error                           |
| rewrite | replace tokens with bowdlerized substitutions        |
| allow   | pass through with no change                          |

## Sample violation → decision

Tenant `acme` (threshold=`strong`); response contains a strong-severity
expletive. Output: `rewrite:profanity:strong`. The token is replaced with
`****` before the response is sent.

## Why it's a good demo

Pairs naturally with `pii-redactor` to form a "minimum egress hygiene"
bundle. Shows how tenant-config facts can drive per-customer policy from
a single rule set.
