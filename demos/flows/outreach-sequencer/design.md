=============================================================================
                          OUTREACH SEQUENCER
=============================================================================

[Trigger] (new lead, list import, or scheduled re-engage cohort)
             │
             ▼
[1. load_persona]  (knowledge: `customer-account-kg` lookup)
  → industry, role, prior touches, opt-out state
             │
             ▼
[2. governor: `compliance-scan`]
  (CAN-SPAM / GDPR / CCPA — kills the sequence early for protected addresses
   without consent records)
             │
             ▼
[3. select_template]  (rule: persona × campaign → template_id)
             │
             ▼
[4. draft_message]  (agent: `email-drafter`)
  (persona-aware; consumes prior-thread memory for warm contacts)
             │
             ▼
[5. governor: `tone-calibrator`]
  (channel-appropriate tone; loops back to step 4 with feedback on miss)
             │
             ▼
[6. governor: `pii-redactor`]
  (final draft scrubbed before send)
             │
             ▼
[7. send_step]  (tool: `email-send` / LinkedIn API / `slack-post`)
             │
             ▼
[8. wait_or_react]  (loop step with sleep + signal listener)
  ├──► [IF reply detected]  ──► [11. handoff_to_human]
  ├──► [IF unsubscribe]     ──► [12. mark_opted_out + halt]
  ├──► [IF bounce]          ──► [13. mark_invalid + halt]
  └──► [IF timeout]         ──► next sequence step
             │
             ▼
[9. score_engagement]  (gomlx_inference: `intent-classifier` over reply text)
  → intent: interested | objection | not-now | hostile
             │
             ▼
[10. branch_next]  (conditional)
  ├──► interested → handoff
  ├──► objection  → objection-handling sub-sequence
  ├──► not-now    → schedule re-engage in 60d
  └──► hostile    → suppress permanently
             │
             ▼
[11. handoff_to_human]  (tool: CRM task creation + slack ping to AE)
             │
             ▼
[14. write_outcome]
  (memory: each touch → reply intent → eventual meeting/no-meeting;
   feeds future template selection)
=============================================================================

## Inputs

- lead ID + campaign ID
- sequence definition (steps, delays, channels)

## Step types

| #     | Step              | Type             | Notes |
|-------|-------------------|------------------|-------|
| 1     | load_persona      | knowledge        | KG lookup |
| 2     | compliance        | governor         | `compliance-scan` |
| 3     | select_template   | rule             | deterministic |
| 4     | draft_message     | agent            | `email-drafter` |
| 5     | tone_check        | governor         | can loop to 4 |
| 6     | redact            | governor         | `pii-redactor` |
| 7     | send_step         | tool             | channel-specific |
| 8     | wait_or_react     | loop             | timer + signal |
| 9     | score_engagement  | gomlx_inference  | `intent-classifier` |
| 10    | branch_next       | conditional      | per-intent routing |
| 11    | handoff_to_human  | tool             | CRM + Slack |
| 14    | write_outcome     | memory           | trains template selector |

## Outputs

- sent message log per touch
- engagement-scored thread
- handoff record or scheduled re-engage row

## Why it's a good demo

Touches loops, conditionals, scheduled waits, and signals — the parts of
the workflow engine that are hardest to fake with a notebook. Pairs with
`email-drafter`, `intent-classifier`, and `customer-account-kg`.
