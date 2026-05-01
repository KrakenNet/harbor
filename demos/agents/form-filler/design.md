# Agent · `form-filler`

Takes a form definition and a user-supplied context, fills the form.
The structured-to-structured workhorse (inverse of `extractor`).

## Purpose

Used wherever a workflow needs to populate a downstream system: ERP
invoice creation, CRM contact creation, ticket-to-Jira translation,
HRIS new-hire setup. Pairs with `extractor` (often upstream) and
`integrations` to write into target systems.

## DSPy signature

```python
class FillForm(dspy.Signature):
    form_schema: dict = dspy.InputField(desc="JSON Schema with field hints")
    context: str = dspy.InputField(desc="source material to draw from")
    known_values: dict = dspy.InputField(
        desc="fields already known, must not be overwritten")
    filled: dict = dspy.OutputField(desc="conforms to form_schema")
    missing: list[str] = dspy.OutputField()
    needs_confirmation: list[str] = dspy.OutputField(
        desc="filled but with low confidence")
```

## Recommended tools

- `regex-match` — high-confidence matches for codes/dates/IDs
- `vector-search` — pull historical fills for similar contexts

## Recommended governors

- `schema-validator` — output must conform; reject malformed
- `confidence-threshold` — low-confidence fields land in `needs_confirmation`
- `hitl-trigger` — irreversible system writes need approval

## Demonstrations sketch

- Email → Jira ticket (title, description, labels, priority)
- Invoice extract → ERP line items
- Resume → ATS candidate record

## Why it's a good demo

The combination of "fill what you know, flag what you don't" is
exactly the contract enterprise customers ask for and rarely get. The
`needs_confirmation` field plus `hitl-trigger` is the primitive that
makes agentic data-entry safe.
