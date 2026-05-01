# Knowledge · `cargo-cult-registry`

A knowledge base of patterns the org currently uses *whose original
justification is lost* — copy-pasted code idioms, ritual processes,
and "we always do X" rules whose authors are gone, whose source
contexts have evaporated, and whose continuing presence has not been
re-justified. Flagged on purpose, scheduled for re-justification or
removal.

The `cargo-cult-registry` is the place where patterns go when the
team can no longer answer "*why* do we do this?" — and the place a
governor can refuse to enforce a rule whose ritual outweighs its
remembered reason.

## Purpose

Every long-lived org accumulates rules nobody can defend. Sometimes
they're load-bearing wisdom whose explanation got lost. Sometimes
they're the surviving artifact of a 2019 outage that nobody on the
current team experienced. Sometimes they're cargo cult — pattern
matching on success without understanding the mechanism. The registry
makes the difference *visible* and *re-derivable*.

The load-bearing innovations:

1. **Provenance is required for inclusion.** A pattern enters the
   registry when an agent or human notes "I see this in the codebase /
   process / governor rules, but I can't find a justifying ADR /
   decision / discussion." The flagging is a structured event, not an
   opinion.
2. **Re-justification is scheduled.** Each entry has a deadline by
   which an owner must either cite a justification (which moves the
   pattern into the `adr-archive`) or accept removal. Indefinite
   "let's keep it just in case" is structurally disallowed.
3. **The `anti-cargo-cult` workflow runs against this registry**,
   periodically forcing the question for everything older than X.

## Type

Knowledge Base (markdown documents) with chunked embeddings; one
document per flagged pattern, immutable findings, append-only
re-justification log.

## Schema

Each registry entry carries frontmatter:

```yaml
---
pattern_id: <uuid>
title: <the pattern, named the way the team names it>
where_seen: [<repo:path | runbook:section | governor-rule-id | process-doc-id>]
flagged_at: <date>
flagged_by: <person|agent>
flag_reason: <prose: where the search for justification dead-ended>
candidate_origins: [<doc-id-or-decision-id>]   // what we *think* but can't confirm
re_justify_by: <date>
status: <flagged|justified|removed|grandfathered>
justification_evidence: [<evidence-id>]   // populated when status flips
removal_diff: <doc-id-or-pr-link-or-null>
---
```

Body sections: **What we found** · **Where we looked** · **Best guess
at origin** · **Risk if removed unknown**.

## Ingest source

- The `cargo-cult-detector` tool scans repos for copy-paste idioms with
  no comments, no ADRs, and no test coverage justifying them
- The `pattern-archaeologist` agent excavates governor rules, runbook
  steps, and process docs whose authors are no longer at the company
- The `naive-newcomer` agent files entries when its "why?" chain
  dead-ends in shoulder-shrugs
- The `time-bomb-scout` agent flags rules whose `re_justify_by` has
  passed

## Retrieval query example

> A team lead asks: "what flagged patterns in the orders service have
  re-justification deadlines this quarter?"

→ filter: `where_seen LIKE 'orders%' AND status='flagged' AND
  re_justify_by < end_of_quarter`
→ returns the entries plus the candidate origins so the lead can chase
  them. Many will resolve into ADRs (good — the team rediscovered the
  reason). Some will resolve into removal PRs (also good — the team
  removed dead ritual). A few will be grandfathered (acknowledged
  unknown, accepted risk).

## ACLs

- **Read**: workspace-wide
- **Write**: append-only — flags cannot be silently retracted; status
  transitions logged with the actor and the evidence
- **Audit**: every status transition produces a span
- **Public/customer access**: never

## Why it's a good demo

1. **It is the structural answer to "knowledge debt."** Every other KB
   accumulates content. This one accumulates *the obligation to
   defend* content. Without an explicit primitive, cargo cult is
   invisible — a pattern persists not because it's right but because no
   one is paid to ask. Making the question schedulable is the
   intervention.

2. **It composes with three other catalog items in a way that gives
   the platform real teeth.** The `cargo-cult-detector` tool finds
   candidates; this KB stores them; the `anti-cargo-cult` workflow
   runs the re-justification loop; the `governor-rule-miner`'s output
   is itself audited against this registry (rules it proposes whose
   justifications later evaporate end up here). That's a four-piece
   self-cleaning loop, none of which is interesting alone.

3. **The "grandfathered with accepted risk" status is the honest
   ending.** Some patterns will not yield a justification and also
   should not be removed without more evidence. The KB lets the team
   say "we explicitly accept that we don't know why we do this and
   we're keeping it anyway" — which is wildly better than the default,
   which is to do the same thing while pretending you remember why.

## Sample read

> The `time-bomb-scout` agent files: `pattern_id=cc_104`, "every
  request to the legacy billing API is preceded by a no-op auth-check
  call." Where seen: `services/billing-gateway/middleware.go` (4
  call-sites). Flagged because no comment, no ADR, no test asserts on
  it; the original author left the company in 2023.

→ candidate origins: an October-2022 outage on the legacy billing
  vendor's auth path. Confidence: low. The runbook from that outage
  was removed two `runbooks-kb` revisions ago.
→ re-justify by: 2026-06-01.

→ During the re-justification window, the platform team runs the
  `time-travel-replayer` against staging *without* the no-op call.
  Behavior identical. The pattern was real once and is now ritual.
  Status flips to `removed`, with the removal PR linked. Four
  call-sites of dead code disappear, and the registry has its first
  closed entry. The next pattern in queue is already loaded.
