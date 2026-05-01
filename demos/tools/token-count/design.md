# Tool · `token-count`

Model-aware token counter. Tells you how many tokens a piece of text
costs against a given model's tokenizer.

## Purpose

Cost estimation, context-window guarding, and prompt-trimming all need
exact token counts — and counts that differ per model family. Hard-coded
"4 chars per token" approximations break in interesting ways. This tool
gives an exact answer.

## Inputs

| Field        | Type     | Required | Notes |
|--------------|----------|----------|-------|
| `text`       | string \| []string | yes | batch supported |
| `model`      | string   | yes      | tenant model id; resolves to a tokenizer family |
| `mode`       | enum     | no       | encode / count (default count) |

## Outputs

| Field          | Type        | Notes |
|----------------|-------------|-------|
| `tokens`       | int \| []int| count per input |
| `encoded`      | [][]int \| null | populated when `mode=encode` |
| `tokenizer`    | string      | resolved tokenizer name |
| `model`        | string      | echo |

## Implementation kind

Python tool. Dispatches to `tiktoken` (OpenAI/GPT family),
`tokenizers` (HF/SentencePiece) per the resolved model.

## Dependencies

- `tiktoken` — OpenAI tokenizer family
- `tokenizers` — HuggingFace fast tokenizers
- LLM-model registry (`internal/agent/` model resolver)

## Side effects

Pure. Loads tokenizer files from disk on first call (cached per process).

## Failure modes

- Unknown model → `error_kind="model_unknown"`
- Tokenizer file missing locally → falls back to a downloaded copy if network is allowed; otherwise `error_kind="tokenizer_unavailable"`
- Empty input → returns 0, not an error

## Why it's a good demo

It's the smallest tool that closes the loop on cost-aware agent
execution and is the data source the `cost-ceiling` and `token-budget`
governors call into. Pairs with `embed-text` and with the
`question-difficulty-router` ML primitive (which uses token counts as a
feature).
