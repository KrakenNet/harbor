# Knowledge · `adr-archive`

A knowledge base of Architecture Decision Records — the immutable log of
significant engineering decisions, their context, the alternatives
weighed, and the consequences accepted. Retrievable by agents proposing
similar decisions and by humans onboarding into an unfamiliar service.

## Purpose

ADRs are most teams' best-kept secret: written once, never indexed, and
forgotten by the next engineer who has to make the same call. The
`adr-archive` makes them retrievable so the next decision-maker
encounters the prior reasoning before — not after — they propose
something the team already rejected.

## Type

Knowledge Base (markdown documents) with chunked embeddings, append-only
(superseded ADRs are linked, not deleted).

## Schema

Each ADR carries frontmatter following the Nygard format:

```yaml
---
adr_id: <ADR-NNNN>
title: <decision phrased as a verb>
status: <proposed|accepted|deprecated|superseded>
date: <decision date>
deciders: [<names-or-handles>]
supersedes: <adr-id-or-null>
superseded_by: <adr-id-or-null>
service_or_domain: <area-affected>
---
```

Body sections: **Context** · **Decision** · **Alternatives considered** ·
**Consequences** · **References**.

## Ingest source

- Git repo `docs/adr/` (canonical) — PRs gate quality and require deciders' sign-off
- Auto-suggested drafts from the `pre-mortem-first` workflow when a high-stakes plan completes
- Manual authoring in the KB UI for retrofits

## Retrieval query example

> "we're considering switching from REST to gRPC for the inventory service"

→ retrieves: ADRs where `service_or_domain=inventory` plus ADRs whose
  embedded text mentions "REST vs gRPC" or "transport choice", ordered
  by `status=accepted` first, then `superseded` for context on what was
  already tried.

## ACLs

- **Read**: all engineers
- **Write**: append-only — new ADRs can be added, status can flip to `superseded`, but body is immutable post-acceptance
- **Public/customer access**: never (some ADRs reference unreleased work)

## Why it's a good demo

It's the cleanest "the platform compounds" story for engineering orgs:
every new ADR makes the next decision better-grounded. Pairs naturally
with the `decision-journal-kg` (which captures live decisions; the ADR
archive captures the curated subset that reaches written form) and with
`pre-mortem-first` as a downstream consumer.
