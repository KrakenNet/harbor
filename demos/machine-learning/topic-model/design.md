# ML Model · `topic-model`

Unsupervised topic discovery over a document corpus. Returns topic
assignments, topic-word distributions, and per-document mixtures.

## Purpose

Summarize what a corpus is *about* without prior labels. Used to bucket
ticket backlogs, cluster research notes, and bootstrap labels for
downstream supervised models.

## Task type

Unsupervised clustering / dimensionality reduction. Supports both
classical LDA and neural BERTopic-style pipelines.

## Inputs

| Field         | Type     | Notes                                |
|---------------|----------|--------------------------------------|
| `documents[]` | string[] | corpus to fit on, or score against   |
| `k`           | int      | optional, target topic count         |
| `seed_terms`  | string[] | optional anchor words per topic      |

## Outputs

| Field             | Type          | Notes                            |
|-------------------|---------------|----------------------------------|
| `topics[]`        | list[Topic]   | each = `{id, top_terms, label?}` |
| `assignments[]`   | list[int]     | one topic id per input document  |
| `mixtures[]`      | list[float[]] | per-doc topic distribution       |

## Training-data shape

Plain text corpus, one document per row. Demo uses a 20k-row tech-news
sample. Topic count `k` either user-supplied or auto-selected via
coherence search.

## Eval metric

Topic coherence (NPMI) on held-out text plus a manual top-terms
inspection. No ground truth, so eval is partly qualitative.

## Serving target

gomlx (`internal/gomlx/`) for neural BERTopic variants;
classical-LDA path can run in-process Go without ML acceleration.

## Why it's a good demo

The first unsupervised model in the catalog. Pairs with
`embedding-encoder` to feed `clustering` and with the `summarizer`
agent for per-topic recap generation.
