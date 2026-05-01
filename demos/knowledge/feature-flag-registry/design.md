# Knowledge · `feature-flag-registry`

A knowledge base of feature flags — every flag in every environment,
its purpose, its current state, its targeting rules, its owner, its
expected sunset date. Retrievable by agents that read or modify flag
state and by humans asking "what does this flag do?"

## Purpose

Feature flags accumulate. Most orgs have hundreds, half of them are
permanently-on dead code, and nobody remembers what `enable_v2_path`
actually gates. The `feature-flag-registry` is the canonical retrievable
description of every flag, with a sunset date and an owner — wired so
the absence of those fields is itself queryable.

## Type

Knowledge Base (markdown documents) with chunked embeddings; one
document per flag, keyed on `flag_key`.

## Schema

Each flag document carries frontmatter:

```yaml
---
flag_key: <unique key, e.g. checkout.async-tax-calc>
purpose: <one-sentence intent>
flag_type: <release|experiment|ops|permission|killswitch>
current_state: { prod: <on|off|targeted>, staging: <...>, dev: <...> }
targeting: <plain-language rule summary>
owner: <team-handle>
created_at: <date>
sunset_due: <date-or-null>
last_evaluated_count: <int>          # 0 = candidate for removal
---
```

Body sections: **Why this flag exists** · **How to flip it safely** ·
**What breaks if it's wrong** · **Removal plan**.

## Ingest source

- Feature-flag platform integration adapter (LaunchDarkly / Statsig / Unleash / Flagsmith) for state + evaluation counts
- Git repo for the human-authored body (PRs gate the registry entry alongside the code change)
- The `audit-archive` provides a flip-history trail per flag

## Retrieval query example

> "which release-type flags are older than 90 days, have zero evaluations in prod, and no sunset_due?"

→ filter: `flag_type=release AND created_at < now() - 90d AND current_state.prod_eval_count=0 AND sunset_due IS NULL`
→ returns: candidates for removal, ordered by age, with the owner team for the cleanup PR.

## ACLs

- **Read**: all engineers
- **Write**: flag platform sync for state; engineers via PR for the descriptive body; sunset dates require team-lead sign-off
- **Public/customer access**: never (targeting rules sometimes encode pricing experiments)

## Why it's a good demo

Stale flags are a universal pain and a measurable one — "we removed N
dead flags this quarter" is a metric finance and platform leadership
both like. Composes with the `time-bomb-scout` agent, the
`anti-cargo-cult` workflow, and `pre-mortem-required` for kill-switch
flips.
