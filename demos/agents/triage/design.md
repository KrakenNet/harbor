# Agent · `triage`

Takes an inbound item (ticket, email, alert, PR) and returns a category,
priority, and recommended owner.

## Purpose

The traffic cop. Sits in front of `support-agent`, `incident-response`,
and `pr-review` workflows. Pairs with `classifier` (which it uses
internally) and `escalation-ladder` (governor) for confident-vs-
escalate routing.

## DSPy signature

```python
class Triage(dspy.Signature):
    item: str = dspy.InputField(desc="raw inbound payload")
    item_type: Literal["ticket", "email", "alert", "pr", "other"] = dspy.InputField()
    org_taxonomy: dict = dspy.InputField(desc="categories and known owners")
    category: str = dspy.OutputField()
    priority: Literal["P0", "P1", "P2", "P3"] = dspy.OutputField()
    owner: str = dspy.OutputField(desc="user_id or team handle")
    rationale: str = dspy.OutputField()
    confidence: float = dspy.OutputField()
```

## Recommended tools

- `vector-search` — find similar past items and their resolutions
- `embed-text` — for category-similarity scoring

## Recommended governors

- `schema-validator` — `category` must be in `org_taxonomy`
- `confidence-threshold` — low confidence → escalate to human triager
- `escalation-ladder` — P0/P1 always pages, lower priorities batch
- `business-hours-only` — non-urgent assignments respect quiet hours

## Demonstrations sketch

- Inbound "site is down" email → P0, owner=oncall, rationale cites keywords
- Bug report with reproducer → P2, owner=team-frontend
- Feature request → P3, owner=pm, low-confidence escalates to human

## Why it's a good demo

Triage is the cleanest place to show a confidence-based routing loop:
high confidence auto-files, mid kicks to a human, low refuses. That
three-way split is hard to express in a single prompt and trivial to
express as a governor.
