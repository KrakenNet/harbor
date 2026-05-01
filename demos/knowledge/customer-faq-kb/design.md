# Knowledge · `customer-faq-kb`

A knowledge base of customer-facing FAQs — short Q&A pairs that resolve
the long tail of support questions. The retrieval substrate for the
`faq-answerer` agent and the front line of the `support-triage` workflow.

## Purpose

FAQs are the cheapest unit of support content: one question, one answer,
one canonical phrasing. Most teams keep them in a help-center CMS and
duplicate them in chatbot scripts. The `customer-faq-kb` consolidates
them into a single source so updates propagate to every surface that
answers customers.

## Type

Knowledge Base (markdown documents) with chunked embeddings; one
embedding per Q+A pair (not per page) to keep retrieval tight.

## Schema

Each FAQ document carries frontmatter:

```yaml
---
title: <question phrased canonically>
category: <billing|account|product|integration|policy>
audience: <free|pro|enterprise|all>
last_reviewed: <date>
related: [<other-faq-ids>]
---
```

Body is the answer in markdown, plus a **Variants** block listing other
phrasings of the same question (used as additional embedding seeds to
catch synonym matches).

## Ingest source

- Help-center CMS via integration adapter (Zendesk / Intercom / HelpScout)
- Authored directly in the KB UI by the support enablement team
- The `support-triage` workflow auto-suggests new FAQs from clusters of unresolved tickets

## Retrieval query example

> "my card got declined but my bank says it's fine"

→ retrieves: FAQs in `category=billing` whose embedded variants include
  "card declined", "payment failed", returns the canonical answer plus
  the escalation path if the FAQ doesn't resolve it.

## ACLs

- **Read**: public — these are intentionally customer-visible
- **Write**: support enablement team; product or legal review for sensitive categories
- **Public/customer access**: yes — and it's instrumented to track which FAQs deflect tickets vs. trigger escalations

## Why it's a good demo

It's the highest-ROI customer-facing demo: ticket deflection is a number
the support org already cares about, and a well-tuned FAQ KB moves it
visibly. Composes with `tone-calibrator` (channel-appropriate voice),
`anti-sycophancy` (no "great question!"), and the `meeting-prep`
workflow if support leads brief CSMs on this week's deflection misses.
