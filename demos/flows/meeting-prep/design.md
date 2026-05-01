=============================================================================
                          MEETING PREP
=============================================================================

[Trigger] (calendar webhook 30min before meetings, or `/prep` slash command)
             │
             ▼
[1. fetch_meeting]  (tool: calendar API — title, attendees, body, attachments)
             │
             ▼
[2. classify_meeting_type]  (agent: `classifier`)
  → 1:1 | external-customer | internal-decision | interview | standup |
    QBR | pitch | unknown
             │
             ├──► [IF standup or unknown] ──► [Skip prep — return]
             │
             ▼
[3. parallel_research]
  ├──► attendee_profiles
  │      (knowledge: `org-chart-kg` for internal,
  │       `customer-account-kg` for external)
  ├──► thread_history
  │      (knowledge: `meeting-transcript-memory` + email recap search)
  ├──► open_items
  │      (tool: `sql-query` over CRM tasks + Linear/Jira)
  └──► relevant_docs
         (tool: `vector-search` over docs corpus, gated by attendee scope)
             │
             ▼
[4. governor: `pii-redactor`]
  (any external-attendee prep doc gets PII scrubbed before render)
             │
             ▼
[5. summarize_each]  (agent: `summarizer`, tiered)
             │
             ▼
[6. draft_brief]  (agent: structured-output `extractor`)
  → context_one_liner, attendee_dossiers, key_questions,
    open_items_to_close, suggested_outcomes
             │
             ▼
[7. governor: `output-length-cap`]
  (briefs must fit in <= 1 page on phone; tier-2 detail collapsed)
             │
             ▼
[8. governor: `tone-calibrator`]
  (matches user-pref tone; matches meeting type for external)
             │
             ▼
[9. render]  (tool: `markdown-html` → email/Slack message)
             │
             ▼
[10. send]  (tool: `email-send` or `slack-post` to user, per pref)
             │
             ▼
[11. write_outcome]
  (memory: meeting → brief → user feedback (read / ignored / rated);
   feeds future relevance scoring)
=============================================================================

## Inputs

- calendar event ID + user_id
- prep horizon (default: 30min before)

## Step types

| #  | Step                  | Type        | Notes |
|----|-----------------------|-------------|-------|
| 1  | fetch_meeting         | tool        | calendar API |
| 2  | classify_meeting_type | agent       | `classifier` |
| 3  | parallel_research     | tool + KG   | fan-out |
| 4  | pii_redactor          | governor    | external-attendee scope |
| 5  | summarize_each        | agent       | `summarizer` |
| 6  | draft_brief           | agent       | `extractor` |
| 7  | length_cap            | governor    | mobile-friendly |
| 8  | tone_calibrator       | governor    | per type + pref |
| 9  | render                | tool        | `markdown-html` |
| 10 | send                  | tool        | per pref |
| 11 | write_outcome         | memory      | trains relevance |

## Outputs

- per-meeting brief delivered to user
- read/feedback signal for personalization

## Why it's a good demo

Demos exceptionally well live because the audience can compare the brief
against the actual meeting. Exercises parallel KG queries, the
length-cap governor, and tone-calibration. Pairs with
`meeting-transcript-memory`, `org-chart-kg`, and `customer-account-kg`.
