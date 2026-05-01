=============================================================================
                       CUSTOMER CHURN OUTREACH
=============================================================================

[Trigger] (weekly cron + on-demand from CSM dashboard)
             │
             ▼
[1. score_churn_risk]  (gomlx_inference: `churn-predictor`)
  → per-account: probability + top contributing features
             │
             ▼
[2. enrich_account]
  (knowledge: `customer-account-kg` — usage, contract value, tier, owner,
   recent ticket sentiment, last QBR date)
             │
             ▼
[3. governor: `confidence-threshold`]
  (low-confidence scores held back from outreach to avoid false-alarm
   fatigue; routed instead to a CSM weekly review queue)
             │
             ▼
[4. classify_root_cause]  (agent: `classifier`)
  → cause: feature-gap | competitor-eval | price | service-quality |
    champion-departed | unknown
             │
             ▼
[5. retrieve_playbook]
  (knowledge: `sales-playbook-kb` keyed on root-cause × tier)
             │
             ▼
[6. draft_action_plan]  (agent: `extractor` → action_card)
  → outreach script, exec sponsor ask, internal escalation, save offer
             │
             ▼
[7. governor: `approval-policy`]
  (any monetary save offer above $X requires CRO approval; non-monetary
   actions auto-approved)
             │
             ▼
[8. governor: `tone-calibrator`]
  (matches account tier — enterprise = formal, SMB = direct)
             │
             ▼
[9. governor: `pii-redactor`]
  (final draft scrubbed before any send)
             │
             ▼
[10. branch_send]  (conditional)
  ├──► tier 1 → assign CSM + book exec call
  ├──► tier 2 → CSM email + offer card
  └──► tier 3 → automated email sequence
             │
             ▼
[11. send]  (tool: `email-send` + CRM task creation)
             │
             ▼
[12. wait_outcome]  (loop: 30/60/90-day signal listener for renewal/cancel)
             │
             ▼
[13. write_outcome]
  (memory: account → score → action → eventual renewal/cancel + ARR delta;
   trains next iteration of `churn-predictor`)
=============================================================================

## Inputs

- account-population scope (default: all paying accounts)
- score threshold (default: top decile of churn risk)

## Step types

| #  | Step                  | Type             | Notes |
|----|-----------------------|------------------|-------|
| 1  | score_churn_risk      | gomlx_inference  | `churn-predictor` |
| 2  | enrich_account        | knowledge        | `customer-account-kg` |
| 3  | confidence_gate       | governor         | review queue on low confidence |
| 4  | classify_root_cause   | agent            | `classifier` |
| 5  | retrieve_playbook     | knowledge        | `sales-playbook-kb` |
| 6  | draft_action_plan     | agent            | `extractor` |
| 7  | approval_policy       | governor         | save-offer gate |
| 8  | tone_calibrator       | governor         | per tier |
| 9  | pii_redactor          | governor         | pre-send scrub |
| 10 | branch_send           | conditional      | per tier |
| 11 | send                  | tool             | email + CRM |
| 12 | wait_outcome          | loop             | 30/60/90 wait |
| 13 | write_outcome         | memory           | trains predictor |

## Outputs

- per-account action plan with approver chain
- sent outreach + CRM tasks
- outcome row feeding next training cycle

## Why it's a good demo

Closes the loop between an ML model's prediction and the human business
action that follows. Demonstrates how outcomes get fed back to retrain.
Pairs with `churn-predictor`, `customer-account-kg`, and
`forecast-then-score`.
