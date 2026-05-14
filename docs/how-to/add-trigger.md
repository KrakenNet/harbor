# How to Add a Custom Trigger

## Goal

Register a custom Harbor [`Trigger`][trigger] plugin that emits
[`TriggerEvent`][trigger] rows into the scheduler queue, with per-plugin
try/except isolation across the lifecycle hooks.

## Prerequisites

- Harbor installed (`pip install stargraph>=0.2`).
- Familiarity with the bundled triggers
  ([`manual`](../serve/triggers.md), `cron`, `webhook`) under
  [`harbor.triggers`][triggers-pkg].
- A signal source you want to wire (filesystem watcher, message queue,
  device event, ...).

## Steps

### 1. Implement the Trigger Protocol

The contract is structural (`@runtime_checkable`); no inheritance
required. Four methods: `init` / `start` / `stop` / `routes`.

```python
# my_triggers/fswatch.py
import asyncio
import hashlib
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from harbor.errors import HarborRuntimeError
from harbor.triggers import TriggerEvent


class FilesystemWatchTrigger:
    """Sketch: poll a directory and emit one TriggerEvent per new file."""

    def __init__(self) -> None:
        self._scheduler = None
        self._watch_path: Path | None = None
        self._graph_id: str | None = None
        self._task: asyncio.Task[None] | None = None
        self._seen: set[str] = set()

    def init(self, deps: dict[str, Any]) -> None:
        scheduler = deps.get("scheduler")
        if scheduler is None:
            raise HarborRuntimeError(
                "FilesystemWatchTrigger.init requires deps['scheduler']"
            )
        self._scheduler = scheduler
        self._watch_path = Path(deps["fswatch_path"])
        self._graph_id = deps["fswatch_graph_id"]

    def start(self) -> None:
        self._task = asyncio.create_task(self._loop())

    def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()

    def routes(self) -> list[Any]:
        return []                                  # cron-style: no HTTP surface

    async def _loop(self) -> None:
        while True:
            for path in sorted(self._watch_path.glob("*")):
                key = str(path.resolve())
                if key in self._seen:
                    continue
                self._seen.add(key)

                idemp = hashlib.sha256(
                    f"fswatch:{self._graph_id}|{key}".encode()
                ).hexdigest()
                event = TriggerEvent(
                    trigger_id=f"fswatch:{self._graph_id}",
                    scheduled_fire=datetime.now(UTC),
                    idempotency_key=idemp,
                    payload={"path": key},
                )
                self._scheduler.enqueue(
                    graph_id=self._graph_id,
                    params=event.payload,
                    idempotency_key=event.idempotency_key,
                )
            await asyncio.sleep(1.0)
```

`TriggerEvent.idempotency_key` is the dedup key the scheduler consults
against `pending_runs` before enqueuing — the field is **required**, not
optional.

**Verify:** `python -c "from harbor.triggers import Trigger;
from my_triggers.fswatch import FilesystemWatchTrigger;
print(isinstance(FilesystemWatchTrigger(), Trigger))"` prints `True`
(structural Protocol check).

### 2. Optional: declare hookimpl wrappers

The bundled triggers double as `pluggy` hookimpls so the dispatcher can
isolate per-plugin failures. Wire one if you want
[`dispatch_trigger_lifecycle`][dispatcher]'s try/except guard:

```python
# my_triggers/_pack.py
from typing import Any

from harbor.plugin._markers import hookimpl

from my_triggers.fswatch import FilesystemWatchTrigger


_INSTANCE = FilesystemWatchTrigger()


@hookimpl
def trigger_init(deps: dict[str, Any]) -> None:
    _INSTANCE.init(deps)


@hookimpl
def trigger_start(deps: dict[str, Any]) -> None:
    _INSTANCE.start()


@hookimpl
def trigger_stop(deps: dict[str, Any]) -> None:
    _INSTANCE.stop()


@hookimpl
def trigger_routes() -> list[Any]:
    return _INSTANCE.routes()
```

If your trigger raises in `init`, the dispatcher logs the exception and
continues with the other plugins (FR-2, AC-12.2) — Pluggy's default
first-exception-halt is **intentionally overridden** by
`dispatch_trigger_lifecycle`. Direct `pm.hook.trigger_init()` calls do
NOT have this guard; always go through the dispatcher.

### 3. Webhook variants: declare routes

If your trigger receives over HTTP, return FastAPI routes from
`routes()`. The serve app collects routes via `collect_trigger_routes`
during lifespan and mounts them on the app:

```python
from fastapi import APIRouter, Request

router = APIRouter()


@router.post("/v1/triggers/my_event")
async def receive(request: Request) -> dict[str, str]:
    body = await request.body()
    # ... HMAC verify, idempotency, scheduler.enqueue ...
    return {"ok": "true"}


def routes(self) -> list[APIRouter]:
    return [router]
```

For HMAC + nonce + timestamp window, mirror the canonical implementation
in [`harbor.triggers.webhook`][webhook].

## Wire it up

```toml
# pyproject.toml
[project.entry-points."harbor"]
harbor_plugin = "my_triggers._plugin:harbor_plugin"

[project.entry-points."harbor.triggers"]
fswatch = "my_triggers.fswatch:FilesystemWatchTrigger"
```

The entry-point value can be either a class (Harbor instantiates it) or
a module containing `@hookimpl`-decorated functions.

## Verify

```bash
pip install -e .
HARBOR_TRACE_PLUGINS=1 python -c "
from harbor.plugin.loader import build_plugin_manager
pm = build_plugin_manager()
"
```

Expect a `plugin.register` event for `my-triggers:harbor.triggers:fswatch`.

Boot `harbor serve` with the deps wired (see
[serve overview](../serve/overview.md)) and confirm the trigger fires:

```bash
echo "hello" > /tmp/watched/test.txt
curl http://localhost:8000/v1/runs?trigger_source=fswatch
```

## Troubleshooting

!!! warning "Common failure modes"
    - **`HarborRuntimeError: ... requires deps['scheduler']`** —
      `harbor serve` lifespan must build the `Scheduler` before
      initialising triggers; pass `deps={"scheduler": scheduler, ...}`.
    - **Plugin silently skipped at startup** — pluggy's per-plugin
      try/except inside `dispatch_trigger_lifecycle` swallows
      exceptions. Run with `HARBOR_TRACE_PLUGINS=1` and check the log
      for `trigger.lifecycle.failed` events.
    - **Duplicate runs from one event** — your `idempotency_key` isn't
      stable across retries. Hash a tuple that includes a stable
      content fingerprint (file path, message ID, ...).
    - **Routes missing from the FastAPI app** — only routes returned by
      `routes()` are mounted; don't rely on import-time
      `app.include_router` in your module.

## See also

- [Triggers (serve)](../serve/triggers.md)
- [`Trigger` Protocol][trigger]
- [`harbor.plugin.triggers_dispatcher`][dispatcher]
- Bundled triggers:
  [manual](https://github.com/KrakenNet/harbor/blob/main/src/harbor/triggers/manual.py),
  [cron](https://github.com/KrakenNet/harbor/blob/main/src/harbor/triggers/cron.py),
  [webhook](https://github.com/KrakenNet/harbor/blob/main/src/harbor/triggers/webhook.py).

[trigger]: https://github.com/KrakenNet/harbor/blob/main/src/harbor/triggers/__init__.py
[triggers-pkg]: https://github.com/KrakenNet/harbor/tree/main/src/harbor/triggers
[webhook]: https://github.com/KrakenNet/harbor/blob/main/src/harbor/triggers/webhook.py
[dispatcher]: https://github.com/KrakenNet/harbor/blob/main/src/harbor/plugin/triggers_dispatcher.py
