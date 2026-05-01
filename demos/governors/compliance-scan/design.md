# Governor · `compliance-scan`

Keyword + classifier scan for HIPAA / PCI / SOC2 indicators in prompts
and outputs. Routes flagged content to the appropriate audit log and
optionally halts.

## Purpose

Regulated tenants need an evidence trail showing they detected and
handled protected categories of data. This governor produces the
evidence and enforces the boundary.

## Trigger event

`pre_model_call`, `post_response`, `pre_tool_call`.

## Facts asserted

```clips
(deftemplate compliance-hit
  (slot trace_id)
  (slot framework)        ; hipaa | pci | soc2
  (slot indicator)        ; phi | cardholder_data | access_credential | ...
  (slot tenant_mode))     ; permissive | enforcing
```

## Rules

```clips
(defrule halt-pci-cardholder
  (compliance-hit (trace_id ?t) (framework pci) (indicator cardholder_data))
  =>
  (emit-output "halt:pci:cardholder_data")
  (assert (decision (trace_id ?t) (verdict halt))))

(defrule halt-hipaa-when-enforcing
  (compliance-hit (trace_id ?t) (framework hipaa) (tenant_mode enforcing))
  =>
  (emit-output "halt:hipaa:phi")
  (assert (decision (trace_id ?t) (verdict halt))))

(defrule audit-soc2
  (compliance-hit (trace_id ?t) (framework soc2) (indicator ?i))
  =>
  (emit-output (str-cat "audit:soc2:" ?i))
  (assert (decision (trace_id ?t) (verdict audit))))
```

## Streams

- `compliance.scanner` — keyword + ML classifier hits
- `tenant.config` — framework + mode (permissive vs enforcing)

## Routes

| Verdict | Route                                                       |
|---------|-------------------------------------------------------------|
| halt    | abort, write entry to compliance audit log                  |
| audit   | continue, write entry to compliance audit log               |
| allow   | pass through                                                |

## Sample violation → decision

Outbound response contains a 16-digit card number. Output:
`halt:pci:cardholder_data`. Audit log gets an entry with the trace ID
and indicator class.

## Why it's a good demo

Compliance teams want to see *where* enforcement happens. CLIPS rules
are a much better answer than "buried in some service handler" — they
are an explicit, reviewable artifact.
