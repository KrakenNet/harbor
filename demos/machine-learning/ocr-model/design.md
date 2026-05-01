# ML Model · `ocr-model`

Optical character recognition. Image of text → string, with bounding
boxes and per-word confidence. Underpins the `ocr` tool and any
PDF-extract workflow with scanned pages.

## Purpose

Turn scanned documents, photographs of receipts, screenshots, and
form images into machine-readable text. Feeds the
`invoice-extract-approve` workflow, `pdf-extract` tool, and any
RAG ingest with non-native PDFs.

## Task type

Sequence prediction over image regions. Two-stage: text detection
(bbox) + recognition (CTC/seq2seq decoding).

## Inputs

| Field        | Type        | Notes                                  |
|--------------|-------------|----------------------------------------|
| `image`      | bytes / url | jpeg/png/pdf-page                      |
| `locale`     | string      | optional language hint                 |
| `mode`       | enum: line / word / paragraph | output granularity      |

## Outputs

| Field         | Type            | Notes                              |
|---------------|-----------------|------------------------------------|
| `text`        | string          | concatenated text in reading order |
| `tokens[]`    | list[Token]     | each = `{text, bbox, score}`       |
| `language`    | string          | detected, may differ from hint     |

## Training-data shape

For fine-tuning: `{image, transcription, [boxes]}`. Most tenants don't
train and use the pretrained model. Demo ships an evaluator harness
(no training run) on a synthetic-receipts test set.

## Eval metric

Character error rate (CER) and word error rate (WER), reported per
language and per document type.

## Serving target

ONNX runtime (`internal/onnxrt/`) — PaddleOCR / TrOCR exports.
Detection and recognition pipelined; recognition batched per page.

## Why it's a good demo

The bridge between the vision and text catalog halves. Used by the
`ocr` tool, by `pdf-extract` for scanned PDFs, and by document-ingest
flows. Demonstrates a multi-stage served pipeline (detect → recognize)
in a single model card.
