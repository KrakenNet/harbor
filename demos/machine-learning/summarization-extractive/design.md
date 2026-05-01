# ML Model · `summarization-extractive`

Extractive summarization — selects the most-salient sentences from a
document rather than generating new text. Cheap, faithful, and
LLM-free.

## Purpose

Cut long documents to a budget without hallucination risk. Used as a
preprocessor for the `summarizer` agent (extract → abstractive),
inside `meeting-prep` and `daily-digest` workflows, and on any
"too-long-didn't-read" surface.

## Task type

Sentence-level binary classification (`include` / `exclude`) with a
length / ratio constraint. Optionally re-ranked by a cross-encoder.

## Inputs

| Field          | Type   | Notes                                    |
|----------------|--------|------------------------------------------|
| `text`         | string | document, any length                     |
| `target_ratio` | float  | optional, default 0.15                   |
| `max_sentences`| int    | optional cap                             |
| `query`        | string | optional, for query-focused summarization |

## Outputs

| Field           | Type         | Notes                              |
|-----------------|--------------|------------------------------------|
| `summary`       | string       | concatenated selected sentences    |
| `sentences[]`   | list[(idx, score)] | selections with salience scores |
| `compression`   | float        | observed length ratio              |

## Training-data shape

`{text, summary}` pairs (CNN/DailyMail-style) with sentence-alignment
tools deriving per-sentence labels. Demo seed: a 5k-pair sample with
provided alignment.

## Eval metric

ROUGE-1/2/L against reference summaries; faithfulness check (every
output sentence must appear verbatim in the source — extractive
guarantee).

## Serving target

ONNX runtime (`internal/onnxrt/`) — small encoder with a sentence-pair
ranker head. CPU-fine, latency-friendly.

## Why it's a good demo

The non-LLM, non-hallucinating summarizer. Pairs with the abstractive
`summarizer` agent to demonstrate the "extract first, generate
second" pattern that keeps abstractive summaries grounded. Also shows
up as a preprocessor before context-window-limited LLM calls.
