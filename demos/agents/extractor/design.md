# Agent · `extractor`

Takes free-form text and a target schema, returns typed fields. The
unstructured-to-structured workhorse.

## Purpose

Used wherever a human-written artifact needs to become a row in a table:
invoices, resumes, contracts, support tickets, lab reports, intake
forms. Pairs with `form-filler` (which goes the other direction) and
feeds most ETL-shaped workflows.

## DSPy signature

```python
class Extract(dspy.Signature):
    text: str = dspy.InputField()
    schema: dict = dspy.InputField(desc="JSON Schema of target fields")
    fields: dict = dspy.OutputField(desc="conforms to `schema`")
    missing: list[str] = dspy.OutputField(
        desc="fields in schema with no evidence in text")
    field_provenance: dict[str, Span] = dspy.OutputField()
```

`Span = {start, end, excerpt}` indexed into `text`.

## Recommended tools

- `pdf-extract` — upstream for scanned/PDF inputs
- `ocr` — upstream for image inputs
- `regex-match` — fast path for well-formed fields (dates, IDs, currency)

## Recommended governors

- `schema-validator` — output must conform to the requested schema
- `pii-redactor` — strip extracted PII when downstream is non-privileged
- `confidence-threshold` — kick low-confidence rows to `hitl-trigger`

## Demonstrations sketch

- Invoice PDF → `{vendor, total, line_items[], due_date}`
- Resume → `{name, employers[], skills[], years_experience}`
- Lab report → `{patient_id, tests[], abnormal_flags[]}`

## Why it's a good demo

Extraction makes the value of `field_provenance` immediately legible:
every extracted field is traceable back to a span of source text, which
is exactly the auditable behavior compliance teams ask for.
