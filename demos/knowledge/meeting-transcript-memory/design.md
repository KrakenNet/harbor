# Knowledge · `meeting-transcript-memory`

A memory store of meeting transcripts and their distillations — action
items, decisions, attendees, and the threaded follow-ups across meetings.
Subject to standard memory decay so noise fades while load-bearing
discussion compounds.

## Purpose

Most teams record meetings and never retrieve them. The
`meeting-transcript-memory` makes the transcript a first-class memory:
agents can recall "what did we decide about X two weeks ago?", action
items get reconciled across recurrences, and decisions surface into the
`decision-journal-kg` for outcome tracking.

## Type

Memory (with decay/consolidation via `internal/memory/`); embedded prose
for retrieval, structured fields for filtering.

## Schema

Each memory record:

```yaml
---
meeting_id: <id>
title: <meeting title>
occurred_at: <timestamp>
duration_minutes: <int>
attendees: [<person-ids>]
recurrence_id: <id-or-null>      # links recurring instances
decisions: [<decision-ids>]      # → decision-journal-kg
action_items: [{ owner, due, text, status }]
chunk_id: <chunk identifier>
---
```

Body is the transcript chunk (utterance-level) plus an LLM-generated
summary used as the dominant retrieval surface.

**Retention rules**: chunks decay on a 90-day half-life by default;
chunks linked to an open `action_item` or a `Decision` node are pinned
(no decay) until the linked entity closes.

## Ingest source

- Meeting recorder integration (Zoom / Google Meet / Otter / Granola)
- Calendar integration for attendee + recurrence metadata
- The `meeting-notes` agent post-processes raw transcripts into structured action items + decisions

## Retrieval query example

> "what did the platform team decide about the auth migration in the last month?"

→ filter: `recurrence_id IN platform_team_meetings AND occurred_at > now() - 30d`
→ semantic search over chunks for "auth migration"
→ join into `decisions[]` to surface decision titles + status

## ACLs

- **Read**: meeting attendees by default; expandable per-meeting via the calendar invite ACL
- **Write**: ingestion only; corrections logged as new chunks, originals immutable
- **Public/customer access**: never (transcripts often include sensitive comp / strategy talk)

## Why it's a good demo

It's the "your meetings finally compound" pitch and pairs naturally with
`inverse-onboarding`, `decision-journal-kg`, and `weekly-roll-up`. The
pinned-vs-decayed distinction (action items vs idle chatter) is a
concrete demonstration of memory consolidation working as designed.
