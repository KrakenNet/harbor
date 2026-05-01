=============================================================================
                              DAILY DIGEST
=============================================================================

[Trigger] (cron: 07:00 local, per-user timezone)
             │
             ▼
[1. load_user_prefs]
  (knowledge: `user-preference-memory` — sources, tone, length, channel)
             │
             ▼
[2. fan_out_collect]  (parallel tool calls)
  ├──► email inbox (last 24h, threaded)
  ├──► calendar (today + tomorrow)
  ├──► PRs / issues assigned or mentioning user
  ├──► Slack mentions + DMs
  ├──► incident timeline (open + closed in last 24h)
  └──► RSS / news feeds the user follows
             │
             ▼
[3. dedupe_threads]  (rule: hash by thread_id + cluster near-duplicates)
             │
             ▼
[4. classify_each]  (agent: `classifier`)
  → urgency: must-see | should-see | fyi | noise
             │
             ▼
[5. drop_noise]  (rule: filter where urgency == noise)
             │
             ▼
[6. summarize]  (agent: `summarizer`, tiered output)
  → tier1: one-liner per item
  → tier2: 3-bullet rationale per "must-see"
             │
             ▼
[7. governor: `output-length-cap`]
  (digest must fit in <= one screen; trims tier2 first, then tier1)
             │
             ▼
[8. governor: `tone-calibrator`]
  (matches user-pref tone: terse | conversational | formal)
             │
             ▼
[9. render]  (tool: `markdown-html` → email-ready HTML)
             │
             ▼
[10. send]  (tool: `email-send` or `slack-post`, per pref)
             │
             ▼
[11. write_outcome]
  (memory: which items the user clicked / starred / archived;
   feeds back into `memory-utility-scorer` and future urgency classifier)
=============================================================================

## Inputs

- user_id, timezone, channel preferences
- source allowlist (mailboxes, repos, channels)

## Step types

| #  | Step             | Type       | Notes |
|----|------------------|------------|-------|
| 1  | load_user_prefs  | knowledge  | `user-preference-memory` |
| 2  | fan_out_collect  | tool       | parallel calls |
| 3  | dedupe_threads   | rule       | deterministic |
| 4  | classify_each    | agent      | `classifier` |
| 5  | drop_noise       | rule       | filter |
| 6  | summarize        | agent      | `summarizer` (tiered) |
| 7  | length_cap       | governor   | `output-length-cap` |
| 8  | tone_calibrator  | governor   | per user pref |
| 9  | render           | tool       | `markdown-html` |
| 10 | send             | tool       | per channel |
| 11 | write_outcome    | memory     | trains urgency classifier |

## Outputs

- digest sent to user
- click/archive feedback row for personalization

## Why it's a good demo

Personal, tangible, easy to demo on stage. Shows parallel fan-out, the
classifier-summarizer pair, length-cap and tone-calibrator governors, and
preference memory writeback. Pairs with `summarizer`, `tone-calibrator`,
and `user-preference-memory`.
