# Knowledge · `conversation-history-memory`

A memory store of past conversations between users and agents — the
multi-turn context that lets a chatbot pick up where it left off.
Decaying, consolidated, and partitioned by `(user_id, agent_id)`.

## Purpose

A chatbot without conversation memory is a stranger every session. The
`conversation-history-memory` keeps the recent past hot for fast
context-window recall, summarizes the medium past for token-efficient
catch-up, and decays the distant past unless it carries something the
user explicitly asked to remember.

## Type

Memory (with decay/consolidation via `internal/memory/`); per-turn raw
records collapse into per-thread summaries which then collapse into
per-relationship signals.

## Schema

Three tiers, each a memory record:

```yaml
# Tier 1: turn (raw, decays fast)
---
turn_id: <id>
session_id: <id>
user_id: <uuid>
agent_id: <id>
role: <user|agent|tool>
content: <text>
ts: <timestamp>
---

# Tier 2: thread summary (consolidated nightly)
---
session_id: <id>
user_id: <uuid>
agent_id: <id>
summary: <LLM summary>
topics: [<tag>]
ended_at: <timestamp>
---

# Tier 3: relationship signal (long-lived)
---
user_id: <uuid>
agent_id: <id>
signal: <e.g. "user prefers terse responses", "user is debugging X long-term">
confidence: <0..1>
last_seen: <timestamp>
---
```

**Retention rules**: turns decay on a 14-day half-life; thread summaries
on a 180-day half-life; relationship signals on a 1-year half-life,
with reinforcement extending the timer.

## Ingest source

- Chat platform (Slack / web chat / SDK) writes turns
- Nightly consolidation job collapses turns into thread summaries
- The `extractor` agent promotes recurring patterns into relationship signals

## Retrieval query example

> User opens a new session with `support-agent`:

→ load: relationship signals for `(user_id, agent_id)`
→ load: thread summaries from the last 30 days, top-K by semantic similarity to the new opening message
→ load: turns from the last live session if started < 24h ago
→ feed into the agent's prompt as "what you should remember"

## ACLs

- **Read**: the user themselves, the agent on their behalf, workspace admins (audit only)
- **Write**: ingestion automations and consolidations; no manual edits
- **Public/customer access**: never

## Why it's a good demo

It's the foundational demo for `internal/memory/`'s decay-and-consolidate
machinery — three tiers, visibly different retention, and a measurable
effect on conversation quality. Pairs with `user-preference-memory`,
`echo-chamber-breaker`, and any `chatbot` workflow.
