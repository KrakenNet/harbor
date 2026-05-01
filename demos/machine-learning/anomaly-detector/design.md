# ML Model · `anomaly-detector`

Generic univariate / low-dimensional anomaly detection. Flags points
that deviate from learned normal behavior. The off-the-shelf cousin of
`trace-shape-anomaly`.

## Purpose

Catch outliers in metrics streams — error rates, latency, throughput,
business KPIs — without writing per-metric thresholds. Used by ops
dashboards and the `incident-response` workflow.

## Task type

Unsupervised anomaly detection. Default: isolation forest + a recurrent
reconstruction model for streams; user-selectable.

## Inputs

| Field         | Type        | Notes                                |
|---------------|-------------|--------------------------------------|
| `series`      | float[]     | observed values                      |
| `timestamps`  | int64[]     | optional, for seasonal models        |
| `context`     | float[]     | optional exogenous features          |

## Outputs

| Field            | Type        | Notes                            |
|------------------|-------------|----------------------------------|
| `scores`         | float[]     | anomaly score per input point    |
| `is_anomaly`     | bool[]      | thresholded                      |
| `threshold_used` | float       | echoed for tuning UIs            |

## Training-data shape

Time-aligned CSV: `timestamp, value, [feature_*]`. Trains on whatever
the tenant ships, assumed to be mostly-normal. Demo seed: synthetic
sinusoidal+drift series with injected anomalies for eval.

## Eval metric

Precision@k against curated labels where available; otherwise
operator-flagged retro-accuracy (sample top-k anomalies weekly,
operators mark real/not-real, log AUROC).

## Serving target

gomlx (`internal/gomlx/`) for the deep variants; CPU isolation forest
runs in-process Go for the classical path.

## Why it's a good demo

The generic counterpart to `trace-shape-anomaly` — same task family
(unsupervised, reconstruction-driven), different inputs (numbers vs.
graphs). Useful for showing tenants the cheap option before they reach
for the bespoke graph model.
