# Knowledge · `sales-playbook-kb`

A knowledge base of sales playbooks — discovery questions, objection
handlers, competitive positioning, ICP definitions, and stage-by-stage
plays. Consumed by sales agents, the `email-drafter` for outreach, and
the `meeting-prep` workflow before customer calls.

## Purpose

Sales orgs accumulate institutional knowledge in slide decks, Notion
pages, win/loss reviews, and tribal memory. The `sales-playbook-kb`
collects the operational distillate — the parts an AE actually re-reads
before a call — into a single retrievable surface that an agent can
ground its drafts in.

## Type

Knowledge Base (markdown documents) with chunked embeddings.

## Schema

Each playbook document carries frontmatter:

```yaml
---
title: <play name>
play_type: <discovery|objection|competitive|closing|expansion>
icp_segment: <smb|mid-market|enterprise|all>
competitor: <competitor-name-or-null>
last_validated: <date>
owner: <sales-enablement-handle>
---
```

Body sections: **When to use** · **Setup** · **Script / talk track** ·
**Anticipated responses** · **Disqualification triggers** · **Follow-up**.

## Ingest source

- Sales enablement Notion / Highspot via integration adapter
- Win/loss interview transcripts post-processed by the `extractor` agent
- Manual curation by sales enablement leads

## Retrieval query example

> "prospect just said 'we already use Snowflake, why would we switch?'"

→ retrieves: playbooks with `play_type=competitive` and `competitor=Snowflake`,
  ranked by `last_validated`, returns the talk-track plus the standard
  disqualification triggers if the prospect's answer matches.

## ACLs

- **Read**: GTM org — sales, CS, marketing leadership
- **Write**: sales enablement team
- **Public/customer access**: never (these are internal positioning docs)

## Why it's a good demo

GTM is the second-most-asked-for vertical after support, and most
"AI for sales" pitches stop at "draft an email." This demo grounds the
draft in the same playbook the AE would use, which is the difference
between novelty and adoption. Composes with `business-hours-only`,
`role-gate` (only sellers see competitive plays), and `redaction-on-egress`
to keep competitor naming out of customer-facing surfaces.
