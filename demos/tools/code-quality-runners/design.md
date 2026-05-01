# Tool · `code-quality-runners` (`lint-run` / `test-run`)

Two ops, one tool group: run a linter or run a test suite over a
sandboxed checkout, return structured findings.

## Purpose

Code-writing and code-reviewing agents need real feedback, not "looks
good to me." `lint-run` and `test-run` invoke the project's actual
configured tools and parse their results into a stable shape.

## Inputs

Dispatched on `op`:

| Field          | Type    | Required | Notes |
|----------------|---------|----------|-------|
| `op`           | enum    | yes      | lint / test |
| `cwd`          | string  | yes      | sandboxed checkout root |
| `runner`       | enum    | no       | language-aware default (eslint / ruff / golangci-lint; pytest / vitest / go test) |
| `paths`        | []string | no      | scope to subset; default whole repo |
| `extra_args`   | []string | no      | passed through, allowlisted |
| `timeout_ms`   | int     | no, 300000 | hard cap |

## Outputs

| Field           | Type           | Notes |
|-----------------|----------------|-------|
| `op`            | string         | echo |
| `findings`      | []LintFinding  | lint op only; file/line/severity/rule |
| `tests`         | []TestResult   | test op only; name/status/duration/output |
| `summary`       | RunSummary     | totals: passed/failed/errored |
| `exit_code`     | int            |       |
| `duration_ms`   | int            |       |

## Implementation kind

Shell tool, built on `shell-exec`. Output parsers are per-runner (JSON
output preferred where the runner supports it).

## Dependencies

- `shell-exec` — process spawning
- Per-runner adapters that turn `eslint --format json`, `ruff check
  --output-format json`, `pytest --json-report`, `go test -json` etc.
  into the unified output shape

## Side effects

Spawns runner subprocesses inside the sandboxed `cwd`. Linters are
strictly read-only; test runners may write coverage or cache files
inside the checkout.

## Failure modes

- Runner not installed in sandbox → `error_kind="runner_unavailable"`
- Runner crashed (non-finding non-zero exit) → `error_kind="runner_crash"` with stderr
- Timeout → `error_kind="timeout"`, partial findings if any
- Output format unparseable (runner version drift) → returns raw output with `error_kind="parse"`

## Why it's a good demo

It demonstrates how to wrap diverse ecosystem tools behind one Railyard
contract and how to feed results back into agents in a structured way.
Pairs with `code-format`, `git-ops`, and the `pr-review` and `bug-reproducer` flows.
