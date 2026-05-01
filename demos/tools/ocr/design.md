# Tool · `ocr`

Image bytes in, recognized text out. Optional layout/box info per
detected line.

## Purpose

Some inputs only exist as pixels: scanned forms, screenshots, photos of
whiteboards. `ocr` is the universal pixels-to-text bridge so other tools
(`pdf-extract`, `invoice-extract-approve`) don't need their own.

## Inputs

| Field        | Type             | Required | Notes |
|--------------|------------------|----------|-------|
| `image`      | url \| bytes \| storage_ref | yes | one-of |
| `language`   | string           | no, "eng"| Tesseract lang code |
| `layout`     | bool             | no, false| return per-line bboxes |
| `psm`        | int              | no, 3    | Tesseract page-segmentation mode |

## Outputs

| Field        | Type            | Notes |
|--------------|-----------------|-------|
| `text`       | string          | full recognized text |
| `lines`      | []OCRLine       | text + bbox + confidence; empty if `layout=false` |
| `confidence` | float [0..1]    | mean across lines |
| `language`   | string          | resolved (post-detection if applicable) |

## Implementation kind

Python tool. `pytesseract` against a system Tesseract install; optional
upgrade path to a hosted OCR API behind the same interface.

## Dependencies

- `pytesseract` + Tesseract binary
- `pillow` — image preprocessing (deskew, threshold)
- Sibling tool: invoked by `pdf-extract` for scanned pages

## Side effects

Spawns the `tesseract` subprocess. May write a temporary preprocessed
image under the sandbox tmp dir.

## Failure modes

- Unsupported image format → `error_kind="format"`
- Empty / blank image → returns empty text, `confidence=0.0`, no error
- Language pack missing → `error_kind="lang_unavailable"`
- Tesseract crash → `error_kind="ocr_engine"`, raw stderr included

## Why it's a good demo

It's the lowest-level vision-to-text primitive and the one that most ML
pipelines secretly need. Pairs with `pdf-extract`, with the
`ocr-model` ML primitive (which can replace Tesseract behind the same
interface), and with image-handling agents.
