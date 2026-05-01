=============================================================================
                       THE FORECAST-THEN-SCORE WORKFLOW
=============================================================================

A workflow that publishes a written forecast of its own outcome before
acting, executes the plan, then — on a deterministic horizon — scores
the forecast against reality. Every action becomes a calibration sample.
The system gets *measurably less wrong over time*, and the score is what
proves it.

The premise: the difference between "the model is confident" and "the
model has been right when this confident" is the difference between
narrative and calibration. The platform should know its own track
record per decision class, and that knowledge should be cheap to inspect.

[Trigger] (any workflow that opts in via `forecast: true`, or any decision
 above a stakes threshold)
             │
             ▼
=============================================================================
            PHASE 1: PRE-COMMITMENT (FORECAST LAYER)
=============================================================================
[1. resolve_decision_class]
  (knowledge: lookup of class → success criteria template, default horizon,
   prior calibration curve for this class)
             │
             ▼
[2. retrieve_priors]
  (knowledge: `past-decision-memory` filtered to the same decision class +
   `decision-journal-kg` for ground truth)
             │
             ▼
[3. agent: `extractor` → forecast]
  → fields:
      • predicted_outcome (categorical or numeric)
      • confidence (0..1)
      • success_criteria[] (each measurable)
      • leading_indicators[] (each with a check_at offset)
      • would_change_my_mind_if (the metric whose value flips the verdict)
      • cost / latency / blast_radius estimates
             │
             ▼
[4. tool: `confidence-bettor`]
  (asks the model to "bet" on its own forecast — returns a calibrated
   probability that's compared to the agent's stated confidence; gap
   triggers a re-write)
             │
             ▼
[5. governor: `conviction-tax`]
  (refuses high confidence without grounding; cited priors required
   above 0.7)
             │
             ▼
[6. governor: `show-your-work`]
  (forecast must include reasoning chain mapping evidence → prediction)
             │
             ▼
[7. governor: `decision-diary`]
  (immutable forecast row written before any side-effecting action;
   this row's plan_hash is the anchor for scoring)
             │
             ▼
=============================================================================
            PHASE 2: EXECUTE + INSTRUMENT (ACTION LAYER)
=============================================================================
[8. install_leading_indicator_watchers]
  (each leading_indicator → CLIPS rule that listens for it during
   execution; tripping mid-flight is itself recorded as a "midway signal")
             │
             ▼
[9. execute_plan]
  (sub-workflow: the actual caller plan; runs inside the watcher governors)
             │
             ▼
[10. schedule_scoring]
  (loop step: sleep until `now + horizon`; persistent across restarts —
   the workflow is the timer)
             │
             ▼
        ─── workflow suspends here ───
             │
             ▼
=============================================================================
            PHASE 3: GROUND TRUTH (MEASUREMENT LAYER)
=============================================================================
[11. wake + fetch_actual]  (parallel tool calls)
  ├──► metric reads against each success_criterion
  ├──► count of fired leading_indicators
  ├──► cost / latency actuals from `tracing`
  ├──► incident events tagged to plan_hash
  └──► customer/external signals if relevant
             │
             ▼
[12. governor: `fact-half-life`]
  (refuses stale facts — the scoring window starts when the forecast was
   written and ends now; older facts are irrelevant)
             │
             ▼
[13. compute_delta]  (rule: per-criterion predicted vs actual; emits
   per-criterion error vectors)
             │
             ▼
[14. classify_forecast]  (agent: `classifier`)
  → verdict: well-calibrated | overconfident | underconfident | wrong-class
             │
             ▼
[15. governor: `anti-sycophancy`]
  (no "we were close" framing on a "wrong-class" verdict — wrong is wrong)
             │
             ▼
=============================================================================
            PHASE 4: CALIBRATION FEEDBACK (LEARNING LAYER)
=============================================================================
[16. update_calibration_curve]
  (gomlx_inference + write: per-decision-class curve updated; tracks
   reliability — when this class predicts 70% confidence, how often
   does it land?)
             │
             ▼
[17. governor: dynamic `confidence-threshold` adjustment]
  (chronic overconfidence in a class auto-tightens the
   `confidence-threshold` governor for that class; chronic
   underconfidence loosens it)
             │
             ▼
[18. write_outcome]
  (knowledge: `decision-journal-kg` outcome edge with full delta vector;
   `past-decision-memory` row with calibration sample)
             │
             ▼
[19. ml_signal: `cost-spike-forecaster`, `workflow-eta-predictor`]
  (when cost / latency forecasts are wrong, those models are retrained;
   when outcome forecasts are wrong, the planner agent gets the delta
   in its episodic buffer)
             │
             ▼
[20. notify_owner]  (tool: Slack — "your N-day-old forecast scored
   well-calibrated / over by X%"; the brag-or-blush moment is the demo)
=============================================================================

## Inputs

- decision class
- forecast horizon (default per-class)
- success criteria (extracted by step 3 if not provided)
- caller plan (executes at step 9)

## Step types

| #     | Step                                | Type                  |
|-------|-------------------------------------|-----------------------|
| 1     | resolve_decision_class              | knowledge             |
| 2     | retrieve_priors                     | knowledge             |
| 3     | extract_forecast                    | agent                 |
| 4     | confidence_bettor                   | tool                  |
| 5     | conviction_tax                      | governor              |
| 6     | show_your_work                      | governor              |
| 7     | decision_diary                      | governor              |
| 8     | install_indicator_watchers          | tool (CLIPS bootstrap)|
| 9     | execute_plan                        | sub-workflow          |
| 10    | schedule_scoring                    | loop (sleep)          |
| 11    | fetch_actual                        | tool (parallel)       |
| 12    | fact_half_life                      | governor              |
| 13    | compute_delta                       | rule                  |
| 14    | classify_forecast                   | agent                 |
| 15    | anti_sycophancy                     | governor              |
| 16    | update_calibration_curve            | gomlx_inference + write |
| 17    | dynamic_confidence_threshold        | governor              |
| 18    | write_outcome                       | knowledge             |
| 19    | retrain_signals                     | gomlx_inference       |
| 20    | notify_owner                        | tool                  |

## Outputs

- per-class calibration curves (queryable, plot-able)
- per-decision delta vectors
- self-tightening `confidence-threshold` governor
- ML retraining signals for cost / ETA predictors

## Pairs naturally with

- `confidence-bettor` (tool) — Phase 1 calibration check
- `conviction-tax` (governor) — Phase 1 enforcement
- `decision-journal-kg` (knowledge) — receives forecast and outcome
- `past-decision-memory` (knowledge) — feeds priors and accumulates samples
- `cost-spike-forecaster` (ML) — retrained from cost-forecast deltas
- `workflow-eta-predictor` (ML) — retrained from latency-forecast deltas
- `trial-and-retro` (workflow) — sister workflow; this one is the
  numeric, multi-criterion variant
- `decision-journal-loop` (workflow) — provides the same anchor pattern

## Why it's a good demo

Three reasons:

1. **Calibration is the killer feature.** Most agent platforms tell you
   the model is "highly confident." This one tells you that, *for this
   decision class, when the model says 70% it's right 64% of the time*.
   The calibration curve is queryable, per-class, and updated by every
   run — that's the demo, not a slide.

2. **It composes ML with governance.** The calibration curve isn't
   passive analytics; it actively retunes the `confidence-threshold`
   governor. A class the platform is bad at automatically gets stricter
   gating. Failing publicly makes the system safer.

3. **It exploits the persistent runtime.** The schedule_scoring step
   sleeps for days inside the workflow engine. No external scheduler,
   no cron job, no human reminding the system to grade itself. The
   workflow *is* the calibration harness.
