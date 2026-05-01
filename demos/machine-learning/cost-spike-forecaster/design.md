# ML Model · `cost-spike-forecaster`

Predicts dollar-cost blowups N minutes ahead, using the platform's own
trace + token-usage telemetry as a leading indicator. Catches the
spike before the bill arrives, not after.

It is not a cloud-bill anomaly detector running on monthly invoices.
It runs on the live span stream and forecasts cost trajectory from
intermediate signals — token rates, model upgrades, retry storms,
fan-out changes — that show up minutes before cost does.

## Purpose

Stop runaway-cost incidents in flight. The classic case: an agent
enters a retrieval loop on a poorly-scoped query, escalates through
the `escalation-ladder` governor to the biggest model, and burns
$2k before anyone notices. By the time the cost dashboard updates,
the damage is done. This model fires before that.

## Task type

Multivariate time-series forecasting with anomaly classification on
the residual. Outputs both a point forecast and a "spike imminent"
probability.

## Inputs

| Field                | Type        | Notes                                |
|----------------------|-------------|--------------------------------------|
| `tenant_id`          | uuid        | per-tenant model                     |
| `series`             | dict        | rolling windows of:                  |
|                      |             | - `tokens_in_per_min`                |
|                      |             | - `tokens_out_per_min`               |
|                      |             | - `model_mix` (small/med/large $$)   |
|                      |             | - `tool_call_rate`                   |
|                      |             | - `active_traces_count`              |
|                      |             | - `retry_rate`                       |
| `horizon_minutes`    | int         | forecast window, default 15          |

## Outputs

| Field             | Type         | Notes                              |
|-------------------|--------------|------------------------------------|
| `forecast_usd`    | float[h]     | predicted cost per minute, h=15    |
| `spike_prob`      | float [0..1] | calibrated, for the horizon        |
| `attribution[]`   | list[(workflow_id, contribution)] | which flows are the driver |
| `recommended_action` | enum: monitor / throttle / page  | derived from spike_prob   |

## Training-data shape

Drawn entirely from Railyard's tables:

- `tracing.spans` — token counts, model ids, latency per span
- `agents.executions` — workflow / agent / tool relationships
- `governor.decisions` — escalation events
- `platform.cost_ledger` — actual dollar cost per span (ground truth)

Training rows: 1-minute snapshots of the input series with the
*next 15 minutes' actual cost* as the regression target and
"did a spike (> 3 sigma over rolling baseline) occur in the next 15
min" as the binary classification target. Per-tenant models
because cost baselines and traffic shapes vary wildly by deployment.

## Eval metric

1. **MAPE on the dollar forecast** at 5/10/15-minute horizons.
2. **Lead time** for spike detection (median minutes between alarm
   and the actual spike).
3. **False-alarm rate** at the operator's chosen threshold — directly
   tied to pager fatigue.

Lead time is the headline; the others are the constraints.

## Serving target

gomlx (`internal/gomlx/`) — multivariate sequence model, frequent
re-training (nightly), batched per-tenant inference. The compiled
graph runs in a single goroutine per tenant.

## Inference call sites

1. **Streaming**: a per-tenant background goroutine scores every minute.
2. **Governor integration**: `cost-ceiling` and `tenant-quota` governors
   can pre-emptively tighten thresholds when `spike_prob > 0.7`.
3. **Workflow integration**: the `pre-mortem-first` workflow gets the
   forecast as input, so it can budget pre-mortem effort against
   predicted execution cost.

## Why it's a good demo

1. **It only works because Railyard owns both the cost ledger and the
   trace stream.** Cloud-bill tools have the dollars but not the
   semantic features (which workflow, which agent, which retry
   reason). Trace tools have the semantics but no cost ledger.
   Railyard joins them at the span level, which is where the leading
   indicators live.

2. **It demonstrates closed-loop cost control.** The forecast doesn't
   just alert — it parameterizes the `cost-ceiling` governor, which
   pre-emptively throttles the right workflow. Forecast → policy →
   action, all on-platform.

3. **It composes with the creative trio.** `trace-shape-anomaly`
   catches structural drift, `prompt-drift-classifier` catches
   semantic drift, this one catches economic drift. The three
   together cover the failure modes that don't throw exceptions.

## Sample interaction

Tenant `acme` at 14:32 UTC. Current spend rate: $0.40/min (typical
$0.30/min). Forecast at 14:47 UTC: $4.20/min. Spike probability: 0.91.

→ attribution:
  - workflow `daily-digest`: 78% of projected spike
  - 3 traces showing fanout 12× normal, all calling the same agent
  - `escalation-ladder` already fired 7 times in the last 2 minutes
→ recommended_action: throttle
→ `cost-ceiling` governor receives the forecast and tightens
  daily-digest's cap from $50 to $20 for the next 30 minutes
→ on-call gets a Slack ping with the trace links *before* the cost
  shows up on any dashboard.

Result: the spike that would have been $2k becomes a $40 nuisance.
