# ML Model · `outlier-detector`

Static (non-temporal) outlier detection over tabular rows. The
single-snapshot cousin of `anomaly-detector`.

## Purpose

Flag weird rows in a dataset — bad sensor reads, fraudulent
transactions, mis-keyed data entry. Used by the
`data-quality-sweep` workflow and by ML-pipeline data validators.

## Task type

Unsupervised outlier detection on tabular data. Default ensemble:
isolation forest + local outlier factor + autoencoder reconstruction.

## Inputs

| Field         | Type             | Notes                              |
|---------------|------------------|------------------------------------|
| `rows[]`      | list[map[string]float] | feature rows                  |
| `feature_set` | string[]         | optional column subset             |

## Outputs

| Field            | Type        | Notes                              |
|------------------|-------------|------------------------------------|
| `scores`         | float[]     | one per input row                  |
| `is_outlier`     | bool[]      | thresholded                        |
| `top_features[]` | list[list[(name, contrib)]] | per-row contributions |

## Training-data shape

Tabular CSV. Trains on the dataset itself (mostly-normal assumption).
Demo seed: a credit-card-transaction sample (~50k rows) with injected
outliers for eval.

## Eval metric

Where labels exist (synthetic eval, audit subsets), precision@k and
ROC-AUC. Where they don't, operator-flagged retro-accuracy.

## Serving target

gomlx (`internal/gomlx/`) for the autoencoder path; in-process Go for
isolation forest / LOF.

## Why it's a good demo

Distinct from `anomaly-detector` (which is temporal) and
`trace-shape-anomaly` (which is graph-structured). Drives
`data-quality-sweep` and shows up early in any ML pipeline as a
preflight check. Demonstrates ensemble scoring with per-feature
attribution.
