# ML Model · `object-detector`

Detects multiple objects per image and returns bounding boxes plus
class labels. The "what *and where*" companion to `image-classifier`.

## Purpose

Locate items in images — defects on a part, products on a shelf, faces
in a photo, UI elements in a screenshot. Used by QA workflows,
inventory audits, and screenshot-driven test agents.

## Task type

Object detection: per-image variable-length list of `(class, bbox,
score)` tuples.

## Inputs

| Field           | Type          | Notes                              |
|-----------------|---------------|------------------------------------|
| `image`         | bytes / url   | jpeg/png/webp                      |
| `score_thresh`  | float         | optional, default 0.5              |
| `max_boxes`     | int           | optional, default 100              |

## Outputs

| Field         | Type           | Notes                              |
|---------------|----------------|------------------------------------|
| `detections[]`| list[Detection]| each = `{label, bbox: [x,y,w,h], score}` |
| `image_size`  | `[w, h]`       | echoed for client overlays         |

## Training-data shape

COCO-format JSON or a `{path, boxes: [{class, x, y, w, h}]}`
manifest. Demo seed: a small COCO-subset (~1k images, 5 classes).
Custom-class training expects 200+ images per class.

## Eval metric

mAP at IoU thresholds 0.5 and 0.5:0.95, plus per-class AP.

## Serving target

ONNX runtime (`internal/onnxrt/`) — YOLO / RT-DETR exports.
Inference is GPU-preferred; CPU acceptable for low-throughput cases.

## Why it's a good demo

Variable-length structured output stresses the serving envelope and
the UI overlay rendering. Composes with `ocr-model` for sign-and-text
reading and with the `extractor` agent for image-to-fields flows.
