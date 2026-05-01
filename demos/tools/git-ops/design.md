# Tool · `git-ops`

Read-mostly git operations: clone, diff, blame, log. Wraps the `git` CLI
with structured outputs and per-operation argument shaping.

## Purpose

A surprising number of agent tasks reduce to "look at the git history" or
"show me the diff." `git-ops` exposes those primitives without giving the
agent a raw shell or write access to a repo.

## Inputs

Dispatched on `op`:

| Field          | Type    | Required | Notes |
|----------------|---------|----------|-------|
| `op`           | enum    | yes      | clone / diff / blame / log |
| `repo`         | string  | yes      | URL for clone, local sandbox path otherwise |
| `ref`          | string  | no       | branch / tag / SHA |
| `from`, `to`   | string  | conditional | required for `diff` |
| `path`         | string  | conditional | required for `blame` |
| `limit`        | int     | no, 100  | log entry cap |

## Outputs

| Field         | Type             | Notes |
|---------------|------------------|-------|
| `op`          | string           | echo |
| `clone_path`  | string           | clone op only |
| `diff`        | []FileDiff       | diff op only; per-file hunks |
| `blame`       | []BlameLine      | blame op only |
| `log`         | []Commit         | log op only |
| `duration_ms` | int              |       |

## Implementation kind

Shell tool, built on top of `shell-exec`. Each `op` is a fixed argv
template — the agent cannot smuggle arbitrary git arguments.

## Dependencies

- System `git` binary
- Sibling tool `shell-exec` — process spawning + sandboxing
- `internal/credential/` — only when cloning private repos

## Side effects

`clone` writes into the sandbox checkout dir. All other ops are
read-only. No pushes, no commits — those are deliberately out of scope
for this primitive.

## Failure modes

- Repo URL not reachable → `error_kind="network"`
- Auth failure on private repo → `error_kind="auth"`
- `from`/`to` ref doesn't exist → `error_kind="bad_ref"`
- Path outside the checkout → rejected pre-call, `error_kind="path_escape"`
- Clone exceeds size limit → killed, `error_kind="too_large"`

## Why it's a good demo

It demonstrates the "thin wrapper around a CLI, but with typed I/O" idiom
that almost every enterprise integration eventually needs. Pairs with the
`code-reviewer` and `pr-describer` agents and with the `pr-review` and
`api-contract-diff-alert` workflows.
