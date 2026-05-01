Stream?
Run TUI
Serve TUI
Finish shipwrite
Finish code-graph
code-graph/shipwrite TUI
Web UI
Implement graph knowledge graphs

## Interactive `harbor run` polish (branch: cli/interactive-run, after commit c091bc8)
Backup for scheduled job df3d9088 (Tue 2026-05-05 9:17am local, session-only — may not survive restart).

- [ ] Phantom empty step line at end of run. `_progress.py:_on_transition` opens a new `_NodeInflight` for the synthetic `__end__` sentinel. Filter out `to_node in _SENTINELS` before opening.
- [ ] `done in 0ms` in summary. `_summary.py` derives duration from `last_step_at - started_at`, but both are stamped at run-end on fast graphs. Capture `ResultEvent.run_duration_ms` in `ProgressPrinter` and pass to `SummaryRenderer.render(duration_ms_override=...)`.
- [ ] `inspect: harbor inspect <ckpt> --run-id <uuid>` line wraps mid-UUID. Print on a continuation line: `\n  inspect:\n    harbor inspect <ckpt> --run-id <uuid>`.

Smoke test after fixes: `rm -rf /tmp/ck && uv run harbor run tests/fixtures/sample-graph.yaml --checkpoint /tmp/ck.sqlite` — no phantom line, real duration, inspect on its own line.
