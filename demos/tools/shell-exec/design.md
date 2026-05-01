# Tool · `shell-exec`

Sandboxed shell command runner. Executes a single command (or a small
script) inside a constrained environment and returns its captured streams,
exit code, and timing.

## Purpose

Many useful agent tasks reduce to "run this command and read the output":
invoking a CLI, running a build, calling a one-off binary. `shell-exec`
gives agents that capability without exposing a raw shell. It enforces
timeouts, working-directory pinning, environment scrubbing, and an
allowlist of commands per tool registration.

## Inputs

| Field         | Type              | Required | Notes |
|---------------|-------------------|----------|-------|
| `command`     | string            | yes      | argv[0] must match the allowlist |
| `args`        | []string          | no       | passed verbatim, no shell expansion |
| `cwd`         | string            | no       | must resolve under sandbox root |
| `env`         | map[string]string | no       | merged onto a scrubbed base env |
| `stdin`       | bytes             | no       | piped to the child |
| `timeout_ms`  | int               | no, 30000| hard kill via SIGKILL if exceeded |

## Outputs

| Field        | Type   | Notes |
|--------------|--------|-------|
| `exit_code`  | int    | -1 if killed by signal |
| `stdout`     | bytes  | truncated past `max_output_bytes` |
| `stderr`     | bytes  | truncated past `max_output_bytes` |
| `duration_ms`| int    |       |
| `truncated`  | bool   | true if either stream was capped |

## Implementation kind

Shell tool (Go-side `exec.CommandContext` invocation, no `/bin/sh -c`).

## Dependencies

- Go `os/exec` — process spawning with context-based cancellation
- `internal/agent/tool_executor.go` — argv-style invocation contract
- Sandbox root from tool config; allowlist from tool registration

## Side effects

Spawns a child process. Reads/writes inside the sandboxed `cwd`. Network
access depends on the binary invoked.

## Failure modes

- Command not in allowlist → rejected before spawn, surfaced as policy error
- Timeout → SIGTERM then SIGKILL, `exit_code=-1`, `error_kind="timeout"`
- Output cap exceeded → streams truncated, `truncated=true`
- Non-zero exit → returned as-is; not an error from the tool's perspective
- `cwd` escapes sandbox → rejected, `error_kind="path_escape"`

## Why it's a good demo

It's the universal escape hatch for "wrap any CLI as a tool." Pairs with
the `tool-allowlist` governor for per-agent command scoping and with
`shell-exec`-shaped derivatives (`code-format`, `code-quality-runners`,
`cloud-cli`) which are all thin specializations of this primitive.
