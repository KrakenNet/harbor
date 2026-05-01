# Agent · `meeting-notes`

Takes a meeting transcript, returns structured notes: decisions, action
items (with owners and due dates), open questions, and a TL;DR.

## Purpose

The most-requested productivity agent. Used in `meeting-prep` and
`weekly-roll-up` workflows. Pairs with `email-drafter` to send the
recap, and `triage` to file action items into the right tracker.

## DSPy signature

```python
class TakeNotes(dspy.Signature):
    transcript: str = dspy.InputField(desc="speaker-tagged if possible")
    attendees: list[str] = dspy.InputField()
    tldr: str = dspy.OutputField()
    decisions: list[Decision] = dspy.OutputField()
    action_items: list[ActionItem] = dspy.OutputField()
    open_questions: list[str] = dspy.OutputField()
```

`Decision = {summary, made_by, supporting_quote}`.
`ActionItem = {description, owner, due_date_iso, evidence_quote}`.

## Recommended tools

- `vector-search` — match decisions to prior `decision-journal-kg` rows
- `regex-match` — pull dates and owner mentions reliably

## Recommended governors

- `schema-validator` — every action item must have an owner
- `pii-redactor` — strip non-attendee names mentioned in passing
- `confidence-threshold` — abstain on action items missing owners

## Demonstrations sketch

- Standup transcript → no decisions, several action items, two questions
- Architecture review → 1–2 decisions with supporting quotes, rationale
- Customer call → action items keyed to account-owner, follow-up email queued

## Why it's a good demo

Action-item extraction is the moment most teams realize "we needed
this five years ago." Tying each decision to a `supporting_quote`
prevents the LLM from inventing decisions, and pairs naturally with
`decision-journal-kg` for long-term tracking.
