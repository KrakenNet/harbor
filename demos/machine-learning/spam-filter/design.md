# ML Model · `spam-filter`

Binary spam / not-spam classifier for email, form submissions, and
chat. The classic supervised text-classification baseline.

## Purpose

Filter inbound noise before it consumes downstream agent budget. Used
by the `triage` agent, the `support-triage` workflow, and any inbound
form handler.

## Task type

Single-label binary text classification. Calibrated probability output.

## Inputs

| Field       | Type            | Notes                              |
|-------------|-----------------|------------------------------------|
| `text`      | string          | message body                       |
| `subject`   | string          | optional (concatenated if present) |
| `sender`    | string          | optional sender hint feature       |
| `headers`   | map[string]string | optional (auth-results, dkim, etc) |

## Outputs

| Field         | Type             | Notes                              |
|---------------|------------------|------------------------------------|
| `is_spam`     | bool             | thresholded                        |
| `score`       | float [0..1]     | calibrated spam probability        |
| `reasons[]`   | string[]         | optional, top contributing features |

## Training-data shape

CSV: `text, subject, sender, is_spam`. Demo seed: Enron-spam +
synthetic modern-phish examples (~20k rows). Tenants typically layer
their own labeled spam/ham on top via the active-learning queue.

## Eval metric

Precision and recall at the configured threshold; calibration error
(ECE) since the score gates the `cost-ceiling` and quota policies.
False-positive rate is the hard SLO.

## Serving target

ONNX runtime (`internal/onnxrt/`) — distilBERT-class. Sub-30ms p99.

## Why it's a good demo

A canonical supervised binary task with a hard FPR SLO. Demonstrates
calibration matters, threshold tuning, and the active-learning loop
end-to-end. Gates real workflows; the cost savings are easy to show.
