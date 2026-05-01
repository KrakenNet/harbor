# ML Model · `doc-classifier`

Classifies whole documents (not snippets) into a configurable taxonomy
— e.g. `invoice`, `contract`, `resume`, `receipt`, `report`. Long-text
sibling of `intent-classifier`.

## Purpose

Route uploaded files to the right ingest pipeline. The `doc-ingest-rag`
workflow uses it to pick a chunker and field extractor; the
`invoice-extract-approve` workflow uses it as a preflight gate.

## Task type

Single-label, multi-class text classification over long documents.
Hierarchical: chunk-level scores aggregated to a document label.

## Inputs

| Field        | Type     | Notes                                  |
|--------------|----------|----------------------------------------|
| `text`       | string   | up to model max; longer docs chunked   |
| `metadata`   | map[string]string | optional (filename, mime, source) |
| `taxonomy`   | string   | which configured taxonomy to use       |

## Outputs

| Field         | Type             | Notes                              |
|---------------|------------------|------------------------------------|
| `label`       | string           | top-1 class                        |
| `scores`      | map[string]float | per-class                          |
| `confidence`  | float [0..1]     | top score                          |
| `chunk_votes` | list[(chunk_id, label, score)] | for explainability     |

## Training-data shape

Folder-of-folders or CSV with a path column: `path, label`. Demo seed:
~5k docs across 8 classes (invoices, resumes, contracts, etc).
Per-tenant taxonomies are first-class.

## Eval metric

Macro-F1 across classes plus a top-1 accuracy headline. Confusion
matrix is the operator-facing artifact since misroutes are expensive
downstream.

## Serving target

ONNX runtime (`internal/onnxrt/`) — long-context distilBERT or a
chunk+aggregate pipeline. Throughput-oriented batching since most
calls are batch ingest.

## Why it's a good demo

Bridges the short-text (`sentiment`, `intent-classifier`) and
long-text (`summarization-extractive`) regimes. Drives concrete
routing decisions inside `doc-ingest-rag`, so the demo can show
"upload mixed batch, watch each file go to the right pipeline."
