# Tool · `cloud-cli` (`aws-cli` / `gcloud` / `kubectl`)

Thin, structured wrappers around the three big ops CLIs. Each is invoked
through `shell-exec` with a fixed argv shape, JSON output where
available, and credential resolution from Railyard's credential store.

## Purpose

Many ops, FinOps, and incident-response agents reduce to "run an AWS /
GCP / Kubernetes command and read the result." Wrapping the CLIs makes
them tools rather than free-form shell access, with credentials
resolved per-call instead of stuffed into env vars.

## Inputs

Dispatched on `tool`:

| Field         | Type    | Required | Notes |
|---------------|---------|----------|-------|
| `tool`        | enum    | yes      | aws / gcloud / kubectl |
| `args`        | []string | yes     | argv after the binary name |
| `credential`  | string  | yes      | name of a registered credential |
| `output`      | enum    | no       | json (default) / text / table |
| `region` or `project` or `context` | string | no | per-tool scoping |
| `timeout_ms`  | int     | no, 60000 |       |

## Outputs

| Field         | Type    | Notes |
|---------------|---------|-------|
| `tool`        | string  | echo |
| `argv`        | []string | full argv used (creds masked) |
| `parsed`      | json \| null | populated when `output=json` |
| `stdout`      | bytes   | always present |
| `stderr`      | bytes   |       |
| `exit_code`   | int     |       |
| `duration_ms` | int     |       |

## Implementation kind

Shell tool group, layered on `shell-exec`. Each variant has its own
allowlist of subcommands per tool registration to prevent dangerous ops
(`iam delete-user`, `delete cluster`, etc.) without an explicit grant.

## Dependencies

- AWS CLI v2, `gcloud` SDK, `kubectl` — system binaries available to the sandbox
- `shell-exec` — process spawning
- `internal/credential/` — credential resolution; injected via env or
  short-lived config files, never persisted

## Side effects

Spawns the chosen CLI binary. Outbound network to the cloud API. Some
subcommands mutate cloud state; the per-tool allowlist is what keeps
read-only agents read-only.

## Failure modes

- Subcommand not allowlisted → rejected pre-spawn, `error_kind="not_allowed"`
- Credential expired → `error_kind="auth"`
- Region/project/context invalid → surfaced from the CLI, `error_kind="scope"`
- JSON parse failure (CLI emitted non-JSON) → returns `parsed=null` with raw stdout
- Timeout → SIGKILL via `shell-exec`, partial output preserved

## Why it's a good demo

It collapses three of the most-asked-for "give the agent cloud access"
asks into one consistent pattern with proper credential handling and
allowlisting. Pairs with the `cost-ceiling` and `tool-allowlist`
governors, with the `incident-response` workflow, and with the
`cmdb-asset-kg` knowledge graph.
