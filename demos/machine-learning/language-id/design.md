# ML Model · `language-id`

Detects the natural language of a text snippet. Tiny, fast, and called
upstream of almost every other text model in the catalog.

## Purpose

Route text to language-appropriate downstream models — the right
`sentiment`, the right `ner`, the right LLM. Also used to enforce the
`tone-calibrator` and locale-gated workflows.

## Task type

Single-label, multi-class text classification over ISO 639-1 codes.

## Inputs

| Field   | Type   | Notes                              |
|---------|--------|------------------------------------|
| `text`  | string | as little as 5 characters works    |

## Outputs

| Field         | Type             | Notes                              |
|---------------|------------------|------------------------------------|
| `language`    | string           | ISO 639-1, e.g. `en`, `es`, `ja`   |
| `scores`      | map[string]float | top-5 candidate languages          |
| `confidence`  | float [0..1]     | top score                          |

## Training-data shape

Pretrained — tenants do not train this. Demo just exercises the served
endpoint and an eval harness on the FLORES-200 test set.

## Eval metric

Accuracy on FLORES-200 held-out, plus a short-text slice (≤ 20 chars)
since that's the hard regime.

## Serving target

ONNX runtime (`internal/onnxrt/`) — fastText-class or tiny transformer
export. Sub-5ms p99 is the bar.

## Why it's a good demo

The smallest, fastest model in the catalog. Useful for demonstrating
the no-train, eval-only path through the platform — some models are
just shipped pretrained and served. Also natural upstream of every
multilingual demo.
