# ML Model · `embedding-encoder`

A general-purpose text embedding model. Maps strings to dense vectors
suitable for similarity search, clustering, and downstream classifier
heads.

## Purpose

The vector backbone for everything RAG-shaped on the platform. Powers
`vector-search`, the document chunk index, memory retrieval, and any
"find similar" UI.

## Task type

Self-supervised representation learning; serving is a forward pass that
returns a fixed-dimensional vector.

## Inputs

| Field         | Type     | Notes                                |
|---------------|----------|--------------------------------------|
| `text`        | string   | up to model max (typically 8k tokens) |
| `text_batch`  | string[] | optional batched form                |
| `task_hint`   | string   | optional, e.g. `query` vs `passage`  |

## Outputs

| Field      | Type      | Notes                              |
|------------|-----------|------------------------------------|
| `vector`   | float[d]  | unit-normalized, `d` = 384 or 768 default |
| `vectors`  | float[][] | batched form                       |
| `model_id` | string    | echoed for index-version pinning   |

## Training-data shape

Not trained here in the typical case — tenants pick a pretrained
encoder (BGE, E5, gte family). For domain adaptation, the dataset is
contrastive triples `{query, positive, negative}` produced by mining
clicks, citations, or LLM-judge pairs.

## Eval metric

Retrieval recall@k on a held-out query/passage set. MRR for ranking
sensitivity.

## Serving target

ONNX runtime (`internal/onnxrt/`) — encoder export is well-trodden,
batch throughput matters more than per-call latency for index-build.

## Why it's a good demo

Foundational. Almost every other demo in the catalog references this
model directly or transitively; making it a first-class served
primitive (with a model card, a versioned export, and a swap path)
shows the platform takes embedding-version pinning seriously.
