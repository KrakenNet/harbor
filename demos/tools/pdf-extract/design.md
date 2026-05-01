# Tool · `pdf-extract`

PDF in, structured text + tables out. Handles digital PDFs natively and
falls back to OCR for scanned pages.

## Purpose

PDFs show up everywhere — invoices, contracts, research papers, exported
reports. `pdf-extract` turns them into something an agent can actually
reason over: page-segmented text, recovered table structure, and basic
metadata.

## Inputs

| Field        | Type           | Required | Notes |
|--------------|----------------|----------|-------|
| `source`     | url \| bytes \| storage_ref | yes | one-of |
| `pages`      | string         | no       | range like "1-5,8" (default: all) |
| `tables`     | bool           | no, true | run table detection |
| `ocr_fallback`| bool          | no, true | OCR scanned pages |
| `language`   | string         | no       | hint for OCR |

## Outputs

| Field        | Type             | Notes |
|--------------|------------------|-------|
| `pages`      | []PageBlock      | text + bbox per page |
| `tables`     | []ExtractedTable | rows + cells, with source page |
| `metadata`   | PDFMetadata      | title, author, page count |
| `used_ocr`   | bool             | true if OCR fallback fired |

## Implementation kind

Python tool. `pdfplumber` for digital PDFs, `tesseract` (via the `ocr`
sibling tool) for scanned pages.

## Dependencies

- `pdfplumber` — text + table extraction from digital PDFs
- Sibling tool `ocr` — fallback for image-only pages
- `internal/credential/` — only if `source` is a private storage ref

## Side effects

Reads source bytes (network or storage). May write a transient file under
the sandbox tmp dir. No persistent state.

## Failure modes

- Encrypted PDF without password → `error_kind="encrypted"`
- Page range out of bounds → returns the valid subset with a warning
- OCR disabled but page is scanned → that page returns empty text with `gap_kind="needs_ocr"`
- Corrupt file → `error_kind="parse_failed"`

## Why it's a good demo

It's the smallest viable "real document → typed data" tool, and the one
that most enterprise demos hinge on. Pairs with `ocr` (its fallback),
`embed-text` (downstream chunking), and the `invoice-extract-approve`
workflow.
