# Governor · `pii-redactor`

Scrubs personally identifiable information — emails, phone numbers, SSNs,
credit cards, addresses — from prompts before they leave the platform and
from outputs before they reach users or logs.

## Purpose

The default backstop against accidental PII leakage into model providers,
trace logs, or downstream tools. Detection is regex + classifier; the
governor decides whether to redact, halt, or pass through based on risk
class and route.

## Trigger event

`pre_model_call` (inbound prompts), `post_response` (outbound text), and
`pre_tool_call` for tools tagged `external: true`.

## Facts asserted

```clips
(deftemplate pii-scan
  (slot trace_id)
  (slot stage)            ; pre_model | post_response | pre_tool
  (slot category)         ; email | phone | ssn | card | address | name
  (slot count)
  (slot risk))            ; low | medium | high
```

## Rules

```clips
(defrule redact-low-risk-pii
  (pii-scan (trace_id ?t) (category ?c) (risk low) (count ?n))
  (test (> ?n 0))
  =>
  (emit-output (str-cat "redact:" ?c ":count=" ?n))
  (assert (decision (trace_id ?t) (verdict redact))))

(defrule halt-on-high-risk-pii
  (pii-scan (trace_id ?t) (category ?c) (risk high))
  =>
  (emit-output (str-cat "halt:pii_high_risk:" ?c))
  (assert (decision (trace_id ?t) (verdict halt))))

(defrule warn-on-medium
  (pii-scan (trace_id ?t) (category ?c) (risk medium) (count ?n))
  =>
  (emit-output (str-cat "warn:pii_medium:" ?c ":count=" ?n))
  (assert (decision (trace_id ?t) (verdict redact))))
```

## Streams

- `pii.scanner.findings` — regex + NER hits with risk classification
- `tenant.config` — per-tenant overrides for what counts as high risk

## Routes

| Verdict | Route                                                 |
|---------|-------------------------------------------------------|
| redact  | replace matched spans with `[REDACTED:<category>]`    |
| halt    | abort run, return error envelope, alert security team |
| warn    | continue with redaction, append note to trace         |

## Sample violation → decision

Input prompt: `"Look up customer 555-12-3456, email alice@acme.com"`.
Scanner asserts `(pii-scan ... (category ssn) (risk high) (count 1))`.
Output: `halt:pii_high_risk:ssn`. Run aborts before the prompt hits the
model provider.

## Why it's a good demo

A table-stakes governor that every regulated buyer asks about in the first
meeting. Cleanly demonstrates how a single CLIPS rule pack can fire at
multiple lifecycle points (`pre_model_call`, `post_response`, `pre_tool_call`)
without code duplication.
