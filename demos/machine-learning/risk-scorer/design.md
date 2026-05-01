# ML Model · `risk-scorer`

Generic supervised risk model — produces a calibrated probability that
a given entity (transaction, account, request, claim) will result in a
defined adverse outcome.

## Purpose

A reusable scoring template tenants instantiate per use case: payment
fraud, loan default, account abuse, claim fraud. Drives the
`approval-policy` and `hitl-trigger` governors and prioritizes review
queues.

## Task type

Single-label binary classification on mixed tabular + text features.
Calibrated output, monotone constraints supported on selected features.

## Inputs

| Field         | Type             | Notes                              |
|---------------|------------------|------------------------------------|
| `entity_id`   | string           | for feature lookup                 |
| `features`    | map[string]any   | structured features                |
| `text_blob`   | string           | optional free-text (memo, note)    |

## Outputs

| Field            | Type             | Notes                              |
|------------------|------------------|------------------------------------|
| `risk_score`     | float [0..1]     | calibrated                         |
| `risk_band`      | enum: low/med/high/block | thresholded                |
| `top_features[]` | list[(name, contrib)] | SHAP-style                    |
| `policy_action`  | enum: allow/review/block | derived from band + policy |

## Training-data shape

Wide CSV: `entity_id, snapshot_at, [feature_*], outcome, outcome_at`.
Outcome window is configurable (e.g. 30-day chargeback). Demo seed:
synthetic payments dataset (~100k rows) with a 30-day chargeback
label.

## Eval metric

KS statistic and AUROC for ranking; calibration plot and Brier score
for absolute thresholds. Slicing by amount band, geography, channel.

## Serving target

gomlx (`internal/gomlx/`) — GBM with monotone constraints (e.g.
risk monotone in chargeback rate) is the default; deep tabular
optional.

## Why it's a good demo

Demonstrates monotone constraints, calibration as a hard requirement,
and feature-attribution surfacing — all the "production-grade"
boxes that distinguish a real fraud system from a toy classifier.
Drives the most consequential governors in the catalog.
