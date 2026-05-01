# ML Model · `recommender`

User-to-item collaborative-filtering recommender. Returns ranked item
lists given a user id, with optional in-context candidate filtering.

## Purpose

Power "you might also like," next-best-action panels, and content feed
ranking. Used by chat surfaces (suggested replies), the
`outreach-sequencer` workflow, and any UI that surfaces ranked items.

## Task type

Learning-to-rank from implicit feedback. Two-tower retrieval + a
gradient-boosted reranker.

## Inputs

| Field         | Type            | Notes                              |
|---------------|-----------------|------------------------------------|
| `user_id`     | string          | for embedding lookup               |
| `candidates`  | string[]        | optional, restrict to a pool       |
| `context`     | map[string]any  | optional (page, time, device)      |
| `k`           | int             | how many to return                 |

## Outputs

| Field        | Type                       | Notes                            |
|--------------|----------------------------|----------------------------------|
| `items[]`    | list[(item_id, score)]     | length k, sorted desc            |
| `model_id`   | string                     | for A/B logging                  |

## Training-data shape

Implicit feedback log: `user_id, item_id, event_type, ts, [context_*]`.
Demo seed: MovieLens-25M sample. Negative sampling done at training
time with in-batch negatives + hard negatives.

## Eval metric

Recall@k and NDCG@k on held-out future interactions. A/B test
infrastructure logs business CTR alongside.

## Serving target

gomlx (`internal/gomlx/`) — two-tower retrieval (compiled inference
graph + ANN index) plus an ONNX-served reranker. The retrieval index
is the operationally interesting piece.

## Why it's a good demo

Covers the retrieval+rerank pattern that shows up in RAG and
recommendation alike. The two-tower → ANN → reranker pipeline is the
same shape as `vector-search` + an LLM judge; making both
first-class shows the platform handles heterogeneous serving.
