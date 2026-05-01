# Knowledge · `user-preference-memory`

A memory store of per-user preferences — tone, formats, units, default
filters, channel choices, the small idiosyncrasies that make an agent
feel like it knows you. Long-lived, slowly decaying, consolidated as
patterns repeat.

## Purpose

Generic agents are exhausting because they make every user re-state
context every session. The `user-preference-memory` captures stable
preferences once, lets them decay if contradicted, and consolidates
when the same preference is reinforced — so the agent gets the small
things right (you want metric, you hate emoji, you prefer Monday
digests) without you re-typing them.

## Type

Memory (with decay/consolidation via `internal/memory/`); short
structured records, retrievable by user_id + tag.

## Schema

Each preference record:

```yaml
---
user_id: <uuid>
tag: <units|tone|format|channel|locale|opt-out|...>
key: <e.g. units.measurement, tone.formality>
value: <e.g. metric, formal>
confidence: <0..1>
source: <user-stated|inferred|default>
last_reinforced: <timestamp>
contradicted_count: <int>
---
```

**Retention rules**: half-life of 180 days; each reinforcement resets
the timer and bumps confidence; a contradiction halves confidence and
spawns a new candidate record. When two records under the same key
diverge by more than `contradicted_count >= 3`, a HITL nudge fires
asking the user to disambiguate.

## Ingest source

- Explicit user settings (highest confidence, source=`user-stated`)
- Implicit inference from `conversation-history-memory` (source=`inferred`, lower confidence)
- Defaults from workspace policy (source=`default`, lowest confidence)

## Retrieval query example

> Before the agent renders a weekly digest for `user_42`:

→ filter: `user_id = user_42 AND tag IN ["tone","format","channel","locale"]`
→ select highest-confidence record per `key`
→ feed into the agent's system prompt as a structured preference block

## ACLs

- **Read**: the user themselves, the agent acting on their behalf, workspace admins (audit only)
- **Write**: append-only; consolidations and decays are events, not edits
- **Public/customer access**: never

## Why it's a good demo

Personalization that survives a session is one of the most-asked-for and
worst-implemented agent features. The decay-and-consolidation mechanic
is exactly what `internal/memory/` was built for, and showing it visibly
adapt over a week is a strong demo. Composes with `tone-calibrator`,
`anti-sycophancy`, and the `onboarding-guide` agent.
