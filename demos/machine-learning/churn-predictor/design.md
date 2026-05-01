# ML Model · `churn-predictor`

Predicts the probability a customer churns within a configurable
horizon (30 / 60 / 90 days). Tabular features over account and usage
data.

## Purpose

Surface at-risk accounts to CSMs and trigger outreach via the
`customer-churn-outreach` workflow. The canonical structured-data
classifier in the catalog.

## Task type

Single-label binary classification on tabular data. Calibrated
probability output.

## Inputs

| Field           | Type             | Notes                              |
|-----------------|------------------|------------------------------------|
| `account_id`    | string           | for feature lookup                 |
| `features`      | map[string]float | optional override; otherwise pulled |
| `horizon_days`  | int              | 30 / 60 / 90                       |

## Outputs

| Field            | Type             | Notes                              |
|------------------|------------------|------------------------------------|
| `churn_prob`     | float [0..1]     | calibrated                         |
| `risk_band`      | enum: low/med/high | thresholded                      |
| `top_features[]` | list[(name, contrib)] | SHAP-style attributions       |

## Training-data shape

Wide CSV: `account_id, snapshot_date, [feature_*], churned_within_h`.
Tenants ship a feature manifest; the platform handles
training-snapshot construction. Demo seed: 50k synthetic accounts with
60+ features.

## Eval metric

AUROC and PR-AUC, sliced by tenure band and plan tier. Calibration
plot is the operator-facing artifact since CSM workflows trigger on
absolute thresholds.

## Serving target

gomlx (`internal/gomlx/`) — tabular GBM / TabNet path. Per-row
inference is cheap; explanation generation (SHAP) is the more
expensive op and is batched.

## Why it's a good demo

The canonical tabular use case. Different feature plumbing from the
text models — exercises feature-store lookup, snapshot training, and
explanation surfacing. Drives a real workflow (`customer-churn-
outreach`) where the model's score sets the priority.
