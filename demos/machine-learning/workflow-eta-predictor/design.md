# ML Model · `workflow-eta-predictor`

Predicts time-to-finish for an in-flight workflow, given its current
intermediate state — which steps have completed, which are running,
how the platform is doing on similar runs in the past.

It is not a static SLA timer. It looks at the actual span tree as it
grows, the queue depth, the model latencies right now, and forecasts
completion based on how runs that *looked like this* finished
historically.

## Purpose

Give callers, dashboards, and approval gates a real ETA. Replaces
"running…" with "ETA 14:32 (±2 min)." Drives `latency-sla` governor
decisions and informs queueing UIs whether to wait or escalate.

## Task type

Survival regression / time-to-event forecasting on partially-observed
workflows. The model sees a state vector at time *t* and predicts
remaining duration plus a calibration interval.

## Inputs

| Field                  | Type         | Notes                              |
|------------------------|--------------|------------------------------------|
| `workflow_id`          | uuid         | which workflow definition          |
| `request_id`           | uuid         | which run                          |
| `state`                | dict         | per-run snapshot:                  |
|                        |              | - `steps_completed`                |
|                        |              | - `steps_total` (planned)          |
|                        |              | - `current_step_kind`              |
|                        |              | - `elapsed_ms`                     |
|                        |              | - `tokens_used_so_far`             |
|                        |              | - `tool_call_count_so_far`         |
| `system_load`          | dict         | queue depth, model p99s right now  |

## Outputs

| Field             | Type         | Notes                              |
|-------------------|--------------|------------------------------------|
| `eta_seconds`     | float        | p50 estimate of remaining time     |
| `interval`        | `{p10, p90: float}` | calibrated band             |
| `confidence`      | float [0..1] | derived from interval width        |
| `risk_factors[]`  | list[string] | e.g. "approval pending", "model_X p99 elevated" |

## Training-data shape

Drawn from Railyard's tables:

- `workflow.executions` — start, end, step-by-step timeline
- `workflow.steps` — per-step duration and step kind
- `tracing.spans` — child spans for each step
- `platform.metrics` — concurrent system load at the time

Each training row is a *checkpoint* mid-run: the state at time `t`
and the *actual* remaining duration `T - t`. A single 60-second run
generates ~10 rows. Per-workflow-definition model with cross-workflow
shrinkage for cold-start.

## Eval metric

1. **MAE / RMSE** on remaining-duration prediction, sliced by
   completion percentage (predictions get more accurate as a run
   progresses; eval needs to reward this).
2. **Interval calibration** — fraction of actual completions inside
   the predicted (p10, p90) band should equal 80%.

## Serving target

gomlx (`internal/gomlx/`) — survival head with quantile outputs;
state vectors include sequence features (per-step embedding history)
that benefit from compiled graphs.

## Inference call sites

1. **Per-step**: every workflow step completion triggers a re-score.
   The `workflow.executions.eta_seconds` column gets updated.
2. **UI surfacing**: the workflow-detail page shows a live ETA bar.
3. **Governor integration**: `latency-sla` reads the ETA at each
   step boundary; if predicted finish exceeds the SLA, it can
   bail out early instead of letting the run hit a hard timeout.
4. **Composes with `cost-spike-forecaster`**: ETA × predicted spend
   rate = projected total cost for the run, exposed to approval gates.

## Why it's a good demo

1. **It only works because Railyard captures step-level timing as
   structured data, not log lines.** Most workflow engines emit
   `started`/`finished` events; Railyard's flat-step model with
   per-step span trees gives the model a real state vector to learn
   from.

2. **It's the platform predicting itself.** The training data is
   "every workflow run we've ever done, with every intermediate
   state we ever passed through." That dataset only exists because
   the platform persists step state.

3. **It composes with `cost-spike-forecaster` and `loop-breaker`.**
   ETA + spend rate gives a forward cost projection; an ETA that
   stops decreasing as the run progresses is a strong loop signal
   that `loop-breaker` can act on. The three give the platform a
   "is this run going to finish, when, and how much will it cost"
   view at every step.

## Sample interaction

Workflow `code-review` for PR #142, started 14:00:00. At 14:02:30
(50% through):

→ eta_seconds: 165 (so finish ~14:05:15)
→ interval: (140, 210)
→ confidence: 0.78
→ risk_factors:
  - "model `gpt-4-class` p99 elevated 1.4× normal"
  - "approval-step pending — adds variance"

UI shows: "ETA 14:05 (±35s)." `latency-sla` checks against its
180-second SLA, sees the p90 of 210 exceeds it, escalates to a
notification before the SLA is actually missed.

Compare against the prior trace baseline (median 90 seconds); the
risk factor surfaces the elevated model latency as the cause, so the
operator knows the workflow itself isn't broken — the upstream model
is slow today.
