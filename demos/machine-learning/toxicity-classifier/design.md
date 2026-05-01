# ML Model · `toxicity-classifier`

Multi-label classifier for toxic-language categories: `insult`,
`threat`, `harassment`, `sexual`, `self_harm`, `hate`. Returns
independent probabilities per class.

## Purpose

Pre-screen user-generated content and agent outputs before they hit
public channels. Used by the `profanity-filter` and
`compliance-scan` governors and by moderation queues.

## Task type

Multi-label binary classification (sigmoid head per class).

## Inputs

| Field    | Type   | Notes                              |
|----------|--------|------------------------------------|
| `text`   | string | up to 1024 tokens                  |
| `locale` | string | optional                           |

## Outputs

| Field         | Type             | Notes                              |
|---------------|------------------|------------------------------------|
| `scores`      | map[string]float | per-category probability           |
| `flagged[]`   | string[]         | categories above threshold         |
| `severity`    | enum: low/med/high | derived from max score            |

## Training-data shape

CSV: `text, insult, threat, harassment, sexual, self_harm, hate`
(0/1 per column). Demo seed pulls from public Jigsaw-style corpora
(~30k rows). Tenants can layer policy-specific examples on top.

## Eval metric

Per-category AUROC plus PR-AUC at the operating threshold. False-positive
rate at the threshold is a hard SLO since it gates user-visible
moderation.

## Serving target

ONNX runtime (`internal/onnxrt/`) — distilBERT-class. Inference is on
the request hot path so latency budget is tight.

## Why it's a good demo

Demonstrates multi-label heads (vs. the single-label `sentiment`) and
shows direct integration with a governor (`profanity-filter`) — a model
output drives a policy decision drives a workflow halt. The
end-to-end loop is the whole pitch.
