# SPDX-License-Identifier: Apache-2.0
"""Boot-time config loaders for Harbor (config-dir → typed specs).

Today: ``triggers.py`` reads ``<config_dir>/triggers.yaml`` and returns
typed :class:`~harbor.triggers.cron.CronSpec` /
:class:`~harbor.triggers.webhook.WebhookSpec` lists plus a manual-trigger
descriptor list. The lifespan factory wires those into
``deps={cron_specs, webhook_specs, manual_descriptors, scheduler}`` for
:func:`harbor.plugin.triggers_dispatcher.dispatch_trigger_lifecycle`.
"""

from __future__ import annotations

from harbor.config.triggers import (
    LoadedTriggers,
    ManualDescriptor,
    load_triggers,
)

__all__ = [
    "LoadedTriggers",
    "ManualDescriptor",
    "load_triggers",
]
