# Tool · `code-format`

Run a code formatter (prettier / black / gofmt / rustfmt) over source
text or a file path. Returns the formatted result and a diff.

## Purpose

Code-writing agents produce code that "almost compiles." A formatter
pass cleans whitespace, normalizes quotes, and exposes real syntax
errors that would otherwise look like style noise. `code-format` is the
"always run this last" cleanup step.

## Inputs

| Field         | Type    | Required | Notes |
|---------------|---------|----------|-------|
| `language`    | enum    | yes      | js/ts/py/go/rs/json/yaml/etc. |
| `source`      | string \| storage_ref | yes | one-of |
| `formatter`   | enum    | no       | per-language default; can override |
| `config`      | object  | no       | passed through (e.g. prettier rc) |
| `check_only`  | bool    | no, false| true → don't return formatted body, only the diff |

## Outputs

| Field          | Type    | Notes |
|----------------|---------|-------|
| `formatted`    | string  | empty when `check_only=true` |
| `changed`      | bool    | true if input != formatted |
| `diff`         | string  | unified diff |
| `formatter`    | string  | resolved binary used |
| `duration_ms`  | int     |       |

## Implementation kind

Shell tool, layered on `shell-exec`. Each language maps to a known
binary in the sandbox; argv is fixed.

## Dependencies

- `prettier`, `black`, `gofmt`, `rustfmt`, `yamlfmt` — bundled binaries
- Sibling tool `shell-exec` — process spawning + sandboxing

## Side effects

Spawns the formatter subprocess. Writes a temp file inside the sandbox.
No persistent filesystem changes, no network.

## Failure modes

- Source is not parseable in that language → formatter exits non-zero, surfaced as `error_kind="syntax"` with stderr
- Language → formatter unavailable → `error_kind="formatter_unavailable"`
- Formatter timeout → `error_kind="timeout"`
- `check_only` mode finds no changes → returns `changed=false`, empty diff

## Why it's a good demo

It's the simplest "wrap a CLI" tool with real value to a code-writing
agent and an ideal teaching example for the `shell-exec`-derived tool
pattern. Pairs with `code-quality-runners`, the `code-reviewer` agent,
and the `pr-review` workflow.
