# ML Model · `timeseries-forecast`

Univariate and lightly-multivariate time-series forecasting with
prediction intervals. Forecast horizons from minutes (ops metrics) to
quarters (planning).

## Purpose

Predict future values of a metric — request volume, cost, inventory,
revenue — from its history. Powers capacity-planning dashboards and
the upstream signal for `cost-spike-forecaster` and
`workflow-eta-predictor`.

## Task type

Sequence-to-sequence regression with quantile heads (10/50/90).

## Inputs

| Field         | Type        | Notes                                |
|---------------|-------------|--------------------------------------|
| `series`      | float[]     | observed values, evenly spaced       |
| `timestamps`  | int64[]     | unix seconds, same length as series  |
| `covariates`  | float[][]   | optional exogenous regressors        |
| `horizon`     | int         | steps to forecast                    |

## Outputs

| Field        | Type           | Notes                            |
|--------------|----------------|----------------------------------|
| `forecast`   | float[horizon] | p50 mean prediction              |
| `intervals`  | `{p10, p90: float[horizon]}` | prediction bands     |
| `model_id`   | string         | which family produced the result |

## Training-data shape

Long-format CSV: `series_id, timestamp, value, [covariate_*]`. The
serving layer trains a global model across series with series-id
embeddings. Demo seed: M4-style hourly and daily series (~100 series,
~50k rows total).

## Eval metric

MAPE and MASE on held-out future windows; pinball loss for the
interval calibration.

## Serving target

gomlx (`internal/gomlx/`) — N-BEATS / TFT-class architectures
benefit from custom layers, and forecast batching is a natural fit
for the gomlx graph compiler.

## Why it's a good demo

Different task family from text models — exercises numeric
inputs/outputs and prediction intervals. Foundational for several
creative items (`cost-spike-forecaster`, `workflow-eta-predictor`)
that are time-series problems wrapped in platform context.
