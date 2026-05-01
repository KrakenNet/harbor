=============================================================================
                          EMPLOYEE ONBOARDING
=============================================================================

[Trigger] (HRIS webhook: employee record created with start_date)
             │
             ▼
[1. fetch_employee_profile]
  (knowledge: `org-chart-kg` + HRIS pull — role, manager, location,
   level, employment_type)
             │
             ▼
[2. resolve_role_template]
  (knowledge: `hr-policy-kb` — required accounts / training / hardware
   per role × level)
             │
             ▼
[3. governor: `compliance-scan`]
  (jurisdiction-specific paperwork: I-9 in US, right-to-work UK, GDPR
   consent in EU — checks all are queued)
             │
             ▼
[4. fan_out_provisioning]  (parallel tool calls)
  ├──► identity: SSO / Okta / AzureAD account creation
  ├──► email: workspace mailbox
  ├──► laptop: ServiceNow request via integration
  ├──► payroll: account creation
  ├──► access groups: per role template
  └──► training: assign LMS courses
             │
             ▼
[5. governor: `role-gate`]
  (each access-group grant validated against the role template; over-grants
   blocked even if a downstream tool offers them)
             │
             ▼
[6. governor: `approval-policy`]
  (sensitive groups — finance, prod admin, HRIS — always require manager
   acknowledgment regardless of role template)
             │
             ▼
[7. HITL Approval Gate]  (manager acks sensitive grants; 48h timeout)
             │
             ▼
[8. draft_welcome_kit]  (agent: `onboarding-guide`)
  → personalized week-1 plan: 1:1s, reading list, buddy intro, first task
             │
             ▼
[9. governor: `tone-calibrator`]
  (matches company-voice profile; defaults to warm-professional)
             │
             ▼
[10. send_welcome]  (tool: `email-send` + calendar invites)
             │
             ▼
[11. schedule_30_60_90]
  (tool: calendar invites + ticket templates for 30/60/90-day check-ins)
             │
             ▼
[12. write_outcome]
  (memory: employee → onboarding completion times → manager satisfaction;
   feeds template improvement)
=============================================================================

## Inputs

- HRIS employee payload (id, role, start_date, manager_id, location)

## Step types

| #  | Step                    | Type        | Notes |
|----|-------------------------|-------------|-------|
| 1  | fetch_employee_profile  | knowledge   | `org-chart-kg` + HRIS |
| 2  | resolve_role_template   | knowledge   | `hr-policy-kb` |
| 3  | compliance_scan         | governor    | jurisdiction-aware |
| 4  | fan_out_provisioning    | tool        | parallel |
| 5  | role_gate               | governor    | over-grant prevention |
| 6  | approval_policy         | governor    | sensitive group gate |
| 7  | hitl_approval           | approval    | manager ack |
| 8  | draft_welcome_kit       | agent       | `onboarding-guide` |
| 9  | tone_calibrator         | governor    | company voice |
| 10 | send_welcome            | tool        | email + calendar |
| 11 | schedule_30_60_90       | tool        | calendar + tickets |
| 12 | write_outcome           | memory      | trains templates |

## Outputs

- provisioned accounts + access grants
- welcome kit + scheduled check-ins
- onboarding completion record

## Why it's a good demo

IT / HR / Security audiences all see their slice. Highlights `role-gate`
preventing over-grants from helpful-but-permissive tools — a very common
real-world failure mode. Pairs with `org-chart-kg` and
`onboarding-guide`.
