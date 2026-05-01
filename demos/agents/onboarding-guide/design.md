# Agent · `onboarding-guide`

Takes a user role and a product surface, returns a tailored onboarding
checklist with links and next steps.

## Purpose

The first-touch agent for new users. Used in `employee-onboarding`
workflow and as the chatbot entry-point for free-tier signups. Pairs
with `faq-answerer` for follow-up questions.

## DSPy signature

```python
class GuideOnboarding(dspy.Signature):
    role: str = dspy.InputField(desc="e.g. 'backend-engineer', 'data-analyst'")
    org_context: str = dspy.InputField(
        desc="company name, products in use, team size")
    user_skill_level: Literal["new", "experienced"] = dspy.InputField()
    checklist: list[Step] = dspy.OutputField()
    suggested_first_action: str = dspy.OutputField()
    estimated_time_minutes: int = dspy.OutputField()
```

`Step = {title, description, link, depends_on, optional}`.

## Recommended tools

- `vector-search` — retrieve role-specific docs and runbooks
- `http-fetch` — verify links resolve before returning

## Recommended governors

- `schema-validator` — every step has a link or explicit "no link" reason
- `output-length-cap` — onboarding lists balloon and demoralize new users
- `confidence-threshold` — low confidence → fall back to a generic flow

## Demonstrations sketch

- New backend engineer → repo access, dev env, code-tour, first-task
- New data analyst → BI tool access, sample-query notebook, glossary
- New customer (free tier) → product tour, first-success milestone

## Why it's a good demo

A common but often badly-done agent. The link-verification tool call
inside the agent loop is a small, real example of "the LLM said it,
the trace proves it."
