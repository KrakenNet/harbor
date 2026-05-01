# Knowledge · `hr-policy-kb`

A knowledge base of HR policies — the canonical employee handbook, leave
rules, conduct guidelines, and benefits documentation. Indexed for RAG
retrieval and consumed by the `faq-answerer` and `support-agent` agents
when employees ask policy questions.

## Purpose

Most HR teams field the same dozen questions hundreds of times: PTO
accrual, parental leave, expense limits, remote-work eligibility. The
`hr-policy-kb` makes the canonical answer retrievable in-channel,
grounded in the version-controlled handbook rather than someone's
recollection of last year's policy.

## Type

Knowledge Base (markdown documents) with chunked embeddings.

## Schema

Each policy document carries frontmatter:

```yaml
---
title: <policy name>
category: <leave|conduct|benefits|compensation|remote|safety>
jurisdiction: <country-or-state, or "global">
effective_date: <date>
supersedes: <doc-id-or-null>
owner: <hr-team-handle>
---
```

Body is markdown with structured sections: **Scope** · **Policy** ·
**Eligibility** · **Process** · **Exceptions** · **Contact**.

## Ingest source

- Git repo (canonical handbook) — PRs gated by HR-leads CODEOWNERS
- Workday / BambooHR / Rippling integration adapter for benefits-tier policies
- Drafts authored in the KB UI, promoted on approval

## Retrieval query example

> "how much parental leave do I get if I'm based in Germany?"

→ retrieves: policies tagged `category=leave` filtered by
  `jurisdiction in ["DE", "global"]`, ordered by `effective_date` desc,
  superseded docs excluded.

## ACLs

- **Read**: all employees; per-jurisdiction filtering enforced server-side
- **Write**: HR-policy team only; legal sign-off required for jurisdictions with works-council requirements
- **Public/customer access**: never

## Why it's a good demo

Every customer with more than ~50 employees has an HR handbook that
nobody reads. Wiring it into an agent that answers in Slack converts a
ticket-deflection problem into a measurable RAG win on day one. Pairs
naturally with `role-gate` (so managers see comp info that ICs don't)
and `compliance-scan` on egress (so private medical-leave details never
leak into shared channels).
