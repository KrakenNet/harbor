# CLI Reference

Harbor ships a 7-subcommand CLI (Phase-4 final): `run`, `inspect`,
`simulate`, `counterfactual`, `replay`, `respond`, `serve`. The `serve`
subcommand boots the FastAPI surface; the other six are operator
commands that talk to a running serve (or operate directly against the
checkpointer for read-only commands).

The CLI uses Typer; help text is auto-generated. Every subcommand is
profile-aware via the `--profile` flag or `HARBOR_PROFILE` env-var.

## Topics

- TODO: `harbor serve` flag reference (--profile, --port, --tls-*, ...).
- TODO: `harbor run <ir.yml>` quick-start.
- TODO: `harbor inspect <run_id>` timeline + state-at-step.
- TODO: `harbor counterfactual <ir.yml> <mutation.json>`.
- TODO: `harbor replay <run_id> --diff`.
- TODO: `harbor respond <run_id> --response @file.json --actor <name>`.
- TODO: exit-code conventions.
