# Knowledge · `runbooks-kb`

A knowledge base of operational runbooks — the procedures on-call
engineers follow when alerts fire. Indexed for RAG retrieval and consumed
by incident-response agents.

## Purpose

Make tribal SRE knowledge first-class and retrievable. When an alert
fires, a runbook agent should be able to retrieve the relevant procedure
(or the closest analog), grounded in the same documents the human team
already trusts.

## Type

Knowledge Base (markdown documents) with chunked embeddings.

## Schema

Each runbook document carries frontmatter:

```yaml
---
title: <runbook name>
service: <service-id>
alert_class: <e.g. high-latency, oom, partition-skew>
severity_max: <P0|P1|P2|P3>
last_drilled: <date>
owner_team: <slack handle>
---
```

Body is markdown with structured sections: **Symptoms** · **Diagnosis** ·
**Mitigation** · **Verification** · **Post-incident**.

## Ingest source

- Git repo (canonical) — PRs gate quality
- Confluence/Notion via the relevant integration adapter (read-only sync)
- New runbook drafts can be authored directly in the KB UI

## Retrieval query example

> "checkout service is paging on partition skew, what do I do?"

→ retrieves: runbooks tagged `service=checkout` and `alert_class=partition-skew`,
  ranked by recency of `last_drilled`.

## ACLs

- **Read**: all engineers in the org
- **Write**: SRE + service-owning teams (per-runbook ACL on `owner_team`)
- **Public/customer access**: never

## Why it's a good demo

Every customer with on-call rotations has runbooks somewhere; most don't
have them retrievable. This demo turns a tier-2 doc dump into a tier-1
RAG source for the `incident-response` workflow and the `runbook-runner`
agent. It's the most valuable knowledge-base demo for SRE-heavy
organizations.
