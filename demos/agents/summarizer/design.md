# Agent · `summarizer`

Takes a long document and returns tiered bullets — TL;DR, key points,
and detail — so the same artifact can be read at three depths.

## Purpose

A reusable building block for any workflow that handles long-form text:
meeting transcripts, RFCs, customer-call notes, research papers, support
threads. Downstream agents can consume the TL;DR while humans drill into
detail.

## DSPy signature

```python
class Summarize(dspy.Signature):
    document: str = dspy.InputField(desc="raw text, up to model context limit")
    audience: Literal["exec", "engineer", "support", "generic"] = dspy.InputField()
    max_tldr_words: int = dspy.InputField()
    tldr: str = dspy.OutputField(desc="single-sentence summary")
    key_points: list[str] = dspy.OutputField(desc="3–7 bullets")
    detail: list[Section] = dspy.OutputField(desc="optional deeper sections")
    coverage_score: float = dspy.OutputField(desc="0–1 self-estimate of fidelity")
```

`Section = {heading, bullets, source_offsets}`. `source_offsets` records
character ranges in the input so consumers can verify each bullet.

## Recommended tools

- `token-count` — chunk the input when it exceeds the model window
- `pdf-extract` — upstream extractor for PDF inputs
- `markdown-html` — produce a rendered version for sharing

## Recommended governors

- `output-length-cap` — prevent runaway summaries that defeat the point
- `schema-validator` — enforce the tiered structure
- `redaction-on-egress` — strip PII before sharing summaries externally

## Demonstrations sketch

- 30-page RFC → exec-flavored TL;DR + 5 key points + 3 detail sections
- 90-minute meeting transcript → engineer-flavored bullets, with action
  items inferred but not invented
- Long Slack thread → support-flavored summary keyed on customer pain

## Why it's a good demo

It's the most-requested LLM behavior in any deployment, and the tiered
output makes it composable: other agents (`triage`, `meeting-notes`,
`email-drafter`) can consume just the `tldr` without re-reading the
whole document.
