# ML Model · `intent-classifier`

Classifies short user utterances into a fixed set of intents (e.g.
`book_meeting`, `cancel_order`, `reset_password`, `chitchat`). The
front-door router for chatbot, IVR, and ticket-triage flows.

## Purpose

Route inbound messages to the right handler before paying for a full LLM
call. Used by chat surfaces and the `triage` agent to pick the workflow
or downstream agent that should handle the request.

## Task type

Single-label, multi-class text classification with an `unknown` /
`out-of-domain` fallback class.

## Inputs

| Field      | Type   | Notes                                       |
|------------|--------|---------------------------------------------|
| `text`     | string | up to 256 tokens                            |
| `context`  | string | optional prior turn(s) for conversational disambiguation |
| `locale`   | string | optional, defaults to `en-US`               |

## Outputs

| Field         | Type            | Notes                              |
|---------------|-----------------|------------------------------------|
| `intent`      | enum            | one of the configured intents      |
| `scores`      | map[string]float | per-intent softmax                |
| `confidence`  | float [0..1]    | top score                          |
| `is_ood`      | bool            | true if top score below threshold  |

## Training-data shape

CSV: `text, intent, locale`. Typical tenant ships 30–200 intents with
50–500 examples each. Demo seed has ~12 intents. Active-learning loop
pulls low-confidence production traffic into a labeling queue.

## Eval metric

Macro-F1 across all intents plus a separate OOD detection AUROC.
Confusion matrix is the operator-facing artifact.

## Serving target

ONNX runtime (`internal/onnxrt/`) — distilBERT-class encoder with a
linear head. CPU inference, sub-50ms p99.

## Why it's a good demo

A staple of production NLP stacks; pairs naturally with the `triage`
agent and any chatbot workflow. Demonstrates the OOD pattern, which is
underserved by most off-the-shelf intent kits.
