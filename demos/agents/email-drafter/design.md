# Agent · `email-drafter`

Drafts an email given goal, recipient, and context. Honors brand voice
and length budget; never sends.

## Purpose

Drop-in for any workflow that ends with "and now reply to the
customer": `support-triage`, `outreach-sequencer`, `customer-churn-
outreach`. Pairs with `tone-calibrator` (governor) for channel-correct
output.

## DSPy signature

```python
class DraftEmail(dspy.Signature):
    goal: str = dspy.InputField(desc="what the email should accomplish")
    recipient_context: str = dspy.InputField(
        desc="who they are, prior thread, prior interactions")
    tone: Literal["warm", "neutral", "formal", "apologetic"] = dspy.InputField()
    max_words: int = dspy.InputField()
    subject: str = dspy.OutputField()
    body: str = dspy.OutputField()
    suggested_attachments: list[str] = dspy.OutputField()
    confidence: float = dspy.OutputField()
```

## Recommended tools

- `vector-search` — retrieve prior threads with this recipient
- `markdown-html` — produce HTML body for rich-mail clients

## Recommended governors

- `output-length-cap` — enforce `max_words`
- `tone-calibrator` — block tone mismatches for the channel
- `pii-redactor` — strip third-party PII before send
- `hitl-trigger` — never send without human approval on first deployment

## Demonstrations sketch

- Apologetic outage notice → warm tone, ≤120 words, status link
- Cold outreach to a referred lead → formal tone, ≤80 words, calendar link
- Support reply to an angry user → empathetic, mirrors prior thread

## Why it's a good demo

Communication agents are the highest-stakes "low-stakes" demo:
mistakes are visible, embarrassing, and fixable. The HITL governor
makes that risk explicitly bounded — the agent drafts, the human
approves, the trace records both.
