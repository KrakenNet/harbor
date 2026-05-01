# ML Model · `sentiment`

Three-class sentiment classifier (positive / negative / neutral) over short
text. The simplest useful production model; serves as the canonical
onboarding example for Railyard's ML primitives.

## Purpose

Score sentiment of customer messages, support tickets, app-store reviews,
social posts. Used by triage workflows to escalate angry-tone messages
and by analytics to track sentiment over time.

## Task type

Single-label, three-class text classification. Fixed-length input,
softmax output.

## Inputs

| Field    | Type   | Notes                              |
|----------|--------|------------------------------------|
| `text`   | string | up to 512 tokens                   |
| `lang`   | string | optional; auto-detect if absent    |

## Outputs

| Field         | Type | Notes |
|---------------|------|-------|
| `label`       | enum: positive / negative / neutral | |
| `scores`      | `{positive: float, negative: float, neutral: float}` | sum to 1 |
| `confidence`  | float [0..1] | max score |

## Training-data shape

CSV: `text, label, lang`. ~50k labeled examples. The project ships a
small seed dataset (~2k rows) for the demo and supports BYO-data via the
`datasets` page.

## Eval metric

Macro-F1 across the three classes. Per-language slices reported separately.
Calibration error (ECE) reported alongside accuracy.

## Serving target

ONNX runtime (`internal/onnxrt/`) — small distilBERT-class model. CPU-only
inference is acceptable.

## Why it's a good demo

The smallest model that ties Railyard's ML stack end-to-end: dataset
upload, training run, model card, served inference, downstream agent
consumption (the `triage` agent calls it). It is the "hello world" model
that a customer can replicate in their own tenant in under an hour.
