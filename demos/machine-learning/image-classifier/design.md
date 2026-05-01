# ML Model · `image-classifier`

Single-label image classification. Tenants ship a label set and
example images; the platform fine-tunes a vision encoder and serves
softmax predictions.

## Purpose

Tag photos, screenshots, scans, and product imagery. Used by document
ingest pipelines (page-type detection), inventory workflows
(SKU recognition), and any UI that surfaces "what is this image?"

## Task type

Single-label, multi-class image classification.

## Inputs

| Field        | Type            | Notes                              |
|--------------|-----------------|------------------------------------|
| `image`      | bytes / url     | jpeg/png/webp                      |
| `model_size` | enum: s/m/l     | optional accuracy/latency knob     |

## Outputs

| Field         | Type             | Notes                              |
|---------------|------------------|------------------------------------|
| `label`       | string           | top-1 class                        |
| `top_k`       | list[(label, score)] | default k=5                    |
| `confidence`  | float [0..1]     | top score                          |

## Training-data shape

Folder-of-folders convention: `dataset/<class>/<file>.jpg`, or a CSV
manifest `{path, label}`. Demo seed: a 10-class general-purpose set
(~2k images). Tenants typically ship 50–500 images per class for
fine-tuning.

## Eval metric

Top-1 and top-5 accuracy, plus per-class precision/recall (the long
tail is where models fail).

## Serving target

ONNX runtime (`internal/onnxrt/`) — pretrained ViT / EfficientNet
exports are well-supported, GPU inference optional but supported.

## Why it's a good demo

The first non-text model in the catalog. Exercises image preprocessing,
GPU optionality, and the dataset upload UI's image-mode. Pairs with
`object-detector` and `ocr-model` to cover the vision basics.
