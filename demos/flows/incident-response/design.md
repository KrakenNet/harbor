=============================================================================
                          INCIDENT RESPONSE
=============================================================================

[Triggers] (PagerDuty page, alertmanager webhook, Slack /incident, log anomaly)
             │
             ▼
[1. classify_severity]  (agent: `classifier`)
  → SEV1 | SEV2 | SEV3 | SEV4 (drives every downstream gate)
             │
             ▼
[2. open_incident_channel]  (tool: `slack-post` — creates dedicated channel,
   pins runbook link, invites on-call group)
             │
             ▼
[3. retrieve_runbooks]
  (knowledge: `runbooks-kb` keyed on alert signature; falls back to
   `past-decision-memory` for similar incidents)
             │
             ▼
[4. correlate_signals]  (tool: `sql-query` against metrics + log store)
  → recent deploys, related alerts, dependency-graph blast radius
             │
             ▼
[5. governor: `business-hours-only`]  ← inverted
  (out-of-hours: skip non-essential notifications; SEV1/SEV2 always page)
             │
             ▼
[6. propose_actions]  (agent: `runbook-runner`)
  → ranked list of mitigations with rollback plan per item
             │
             ▼
[7. governor: `hitl-trigger`]
  (any irreversible action — restart, rollback, traffic shift —
   requires human ack for SEV1/SEV2; SEV3/SEV4 may auto-execute pre-approved)
             │
             ▼
[8. execute_mitigation]  (tool dispatch: `kubectl`, `aws-cli`, feature-flag flip)
             │
             ▼
[9. verify_recovery]  (loop: poll metrics until green or timeout)
  ├──► [IF timeout] ──► [Escalate one tier + return to step 6]
             │
             ▼
[10. write_timeline]  (memory: minute-by-minute action log)
             │
             ▼
[11. governor: `decision-diary`]
  (immutable rationale row before incident closes — required for audit)
             │
             ▼
[12. close_incident]  (tool: PagerDuty resolve + Slack channel archive)
             │
             ▼
[13. spawn_postmortem]
  (kicks off `trial-and-retro` workflow with 7-day delay; outcome edge
   appended to `decision-journal-kg`)
=============================================================================

## Inputs

- alert payload (signature, severity hint, source system)
- on-call roster snapshot

## Step types

| #  | Step                  | Type      | Notes |
|----|-----------------------|-----------|-------|
| 1  | classify_severity     | agent     | `classifier` |
| 2  | open_channel          | tool      | `slack-post` |
| 3  | retrieve_runbooks     | knowledge | `runbooks-kb` + memory |
| 4  | correlate_signals     | tool      | metrics + logs |
| 5  | hours_gate            | governor  | `business-hours-only` |
| 6  | propose_actions       | agent     | `runbook-runner` |
| 7  | hitl_trigger          | governor  | severity-aware |
| 8  | execute_mitigation    | tool      | dispatch by action type |
| 9  | verify_recovery       | loop      | poll until green/timeout |
| 10 | write_timeline        | memory    | append-only |
| 11 | decision_diary        | governor  | immutable rationale |
| 12 | close_incident        | tool      | PagerDuty + Slack |
| 13 | spawn_postmortem      | sub-flow  | calls `trial-and-retro` |

## Outputs

- mitigation actions executed with audit trail
- incident timeline + decision diary row
- scheduled post-mortem

## Why it's a good demo

High-stakes workflow that exercises severity-aware gating, the loop
primitive (recovery polling), and the cross-workflow handoff to
`trial-and-retro`. Pairs with `runbooks-kb`, `decision-journal-kg`, and
`anomaly-detector`.
