# ML Model · `ner`

Named-entity recognition over free text. Tags spans as `PERSON`, `ORG`,
`LOC`, `DATE`, `MONEY`, `PRODUCT`, plus tenant-configurable custom
types.

## Purpose

Extract structured entities from emails, tickets, contracts, and chat.
Feeds the `extractor` agent, `lead-enrichment` workflow, and any
downstream KG ingest pipeline.

## Task type

Sequence labeling with BIO tagging. Token-level multi-class
classification.

## Inputs

| Field        | Type     | Notes                                    |
|--------------|----------|------------------------------------------|
| `text`       | string   | up to 2048 tokens                        |
| `entity_set` | string[] | optional override of which types to emit |
| `locale`     | string   | optional                                 |

## Outputs

| Field        | Type            | Notes                              |
|--------------|-----------------|------------------------------------|
| `entities[]` | list[Entity]    | each = `{type, text, start, end, score}` |
| `tokens[]`   | list[TokenTag]  | optional, for debugging            |

## Training-data shape

CoNLL-format BIO files or JSON spans: `{text, entities: [{type, start,
end}]}`. ~10k–100k labeled sentences per language. Demo ships an
English seed (~5k sentences) and a domain-customization recipe.

## Eval metric

Span-level F1 (exact match) and partial-match F1, sliced by entity type.

## Serving target

ONNX runtime (`internal/onnxrt/`) — token-classification head on a
distilBERT encoder. Standard, well-supported export path.

## Why it's a good demo

Covers a different task family (sequence labeling) than `sentiment` and
`intent-classifier`, exercising the per-token output path of the
serving stack. Useful upstream of the `extractor` agent and any
KG-ingest workflow.
