=============================================================================
                       THE TRIAL-AND-RETRO WORKFLOW
=============================================================================

A workflow where every consequential decision automatically schedules a
post-mortem to itself N days in the future. At decision time, predictions
and rationale are written immutably. After the wait, the same workflow
wakes back up, fetches the actual outcome, and scores its past self.

The premise: most retrospectives never happen because they require a
human to remember to write one. Railyard's persistent workflow runtime
removes the "remember" step. Every decision is born with its own
post-mortem already scheduled.

[Trigger] (caller-decision being made, OR sub-workflow invocation by
 `incident-response`, `invoice-extract-approve`, etc.)
             │
             ▼
=============================================================================
            PHASE 1: COMMIT THE DECISION (IMMUTABLE LAYER)
=============================================================================
[1. capture_inputs]
  (records: caller_id, plan_hash, model versions, retrieval fingerprint,
   decision payload, expected timeline)
             │
             ▼
[2. predict_outcome]  (agent: `extractor`)
  → fields: expected_outcome, success_criteria, risk_signals,
    estimated_blast_radius, what_would_change_my_mind
             │
             ▼
[3. governor: `show-your-work`]
  (predictions must include the reasoning chain — bare confidence numbers
   are rejected)
             │
             ▼
[4. governor: `decision-diary`]
  (write immutable rationale row to `decision-journal-kg` BEFORE the
   decision-effect step fires; cannot proceed otherwise)
             │
             ▼
[5. execute_decision]
  (the actual caller payload — could be a single tool call, a sub-flow,
   or a manual handoff; this step's outcome is what we're going to grade)
             │
             ▼
=============================================================================
            PHASE 2: SCHEDULE THE FUTURE SELF (PERSISTENT TIMER)
=============================================================================
[6. schedule_retro]  (loop step with sleep_until = now + retro_horizon)
  (default horizon: 7 days; can be overridden per decision class —
   incidents 14d, deploys 7d, hires 90d, contracts 1y)
             │
             ▼
        ─── workflow suspends here, persistent across restarts ───
             │
             ▼
=============================================================================
            PHASE 3: WAKE + GATHER GROUND TRUTH (RETROSPECTIVE LAYER)
=============================================================================
[7. fetch_actual_outcome]  (parallel tool calls)
  ├──► metrics deltas vs predicted
  ├──► follow-up incidents tagged to this decision
  ├──► user/customer signals (NPS, ticket volume, churn)
  ├──► cost / latency reality vs prediction
  └──► any human comments tagged to the decision
             │
             ▼
[8. governor: `fact-half-life`]
  (refuses to use facts older than the retro window's start — keeps the
   retrospective focused on the actual measurement window)
             │
             ▼
[9. compute_delta]  (rule: predicted vs actual per success criterion)
             │
             ▼
[10. classify_retro]  (agent: `classifier`)
  → verdict: confirmed | partial | wrong | inconclusive | hijacked-by-
    confound
             │
             ▼
[11. agent: `five-whys`]
  (recursive "why?" until first principles, only triggered when
   verdict ∈ {wrong, partial})
             │
             ▼
[12. governor: `anti-sycophancy`]
  (no "in hindsight, the team did great" framing on a "wrong" verdict —
   wrong is wrong)
             │
             ▼
=============================================================================
            PHASE 4: ARCHIVE + LEARN (FEEDBACK LAYER)
=============================================================================
[13. write_retro_record]
  (knowledge: outcome edge appended to the original `decision-journal-kg`
   node; an `anti-pattern-kb` row added on "wrong"; a wins log on
   "confirmed")
             │
             ▼
[14. ml_signal: prediction calibrator]
  (gomlx_inference: scores the agent's calibration over time; persistent
   over-confidence on a class triggers `confidence-threshold` governor
   tightening)
             │
             ▼
[15. propose_template_update]  (agent: `extractor`)
  (if N retros on the same decision class converge on the same root
   cause, propose a workflow-template change)
             │
             ▼
[16. notify_stakeholders]
  (tool: Slack — original decision-makers get tagged with the retro
   they unknowingly committed to N days ago)
=============================================================================

## Inputs

- decision payload (free-form caller content)
- decision class (controls retro_horizon, default 7d)
- predicted_outcome shape (filled by step 2)

## Step types

| #     | Step                      | Type                          |
|-------|---------------------------|-------------------------------|
| 1     | capture_inputs            | rule                          |
| 2     | predict_outcome           | agent                         |
| 3     | show_your_work            | governor                      |
| 4     | decision_diary            | governor                      |
| 5     | execute_decision          | sub-workflow                  |
| 6     | schedule_retro            | loop (sleep_until)            |
| 7     | fetch_actual_outcome      | tool (parallel)               |
| 8     | fact_half_life            | governor                      |
| 9     | compute_delta             | rule                          |
| 10    | classify_retro            | agent                         |
| 11    | five_whys                 | agent (creative tool variant) |
| 12    | anti_sycophancy           | governor                      |
| 13    | write_retro_record        | knowledge                     |
| 14    | calibrator_signal         | gomlx_inference               |
| 15    | propose_template_update   | agent                         |
| 16    | notify_stakeholders       | tool                          |

## Outputs

- immutable decision-diary row at decision time
- outcome edge + verdict at retro time
- calibration update + (sometimes) template-change proposal

## Pairs naturally with

- `decision-journal-kg` (knowledge) — receives the decision row and the outcome edge
- `decision-journal-loop` (workflow) — sister workflow; this one is its time-shifted half
- `anti-pattern-kb` (knowledge) — receives wrong-verdict rows
- `five-whys` (tool) — invoked at step 11
- `incident-response` (workflow) — calls this for SEV1/SEV2 closures
- `forecast-then-score` (workflow) — shares the predict-then-grade philosophy

## Why it's a good demo

Three reasons:

1. **It exploits the persistent workflow runtime.** Most "retrospective"
   tools are spreadsheets that decay. Here, the workflow itself sleeps
   for 7 days inside Railyard's engine and wakes back up with the same
   correlation ID. The platform-as-clock is the demo.

2. **It composes with the platform's other learning loops.** The
   verdict feeds `anti-pattern-kb`; the calibration deltas tighten the
   `confidence-threshold` governor; recurring root causes propose
   template changes. One workflow, three durable learning channels.

3. **It produces an audit trail that survives turnover.** The
   `decision-diary` written at step 4 is immutable; the retro at step
   13 is appended, never replacing. A new team member can replay any
   decision class and read both what we expected and what actually
   happened — folklore captured before the carrier leaves.
