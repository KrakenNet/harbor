# SPDX-License-Identifier: Apache-2.0
"""Singleton-per-path semantics for :class:`KuzuGraphStore` (FR-11).

Two ``KuzuGraphStore`` instances pointed at the same on-disk path
share the same underlying :class:`kuzu.Database` + ``AsyncConnection``
pair so concurrent in-process readers don't fight Kuzu's exclusive
write lock at open time. This pin asserts the shared-handle behaviour
through the public observable: after both stores ``bootstrap``, their
``_db`` and ``_conn`` references are identical.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from harbor.stores.kuzu import KuzuGraphStore

if TYPE_CHECKING:
    from pathlib import Path


pytestmark = [pytest.mark.knowledge, pytest.mark.unit]


async def test_singleton_per_path(tmp_path: Path) -> None:
    """Two stores at the same path share one Database + AsyncConnection."""
    path = tmp_path / "graph"

    first = KuzuGraphStore(path)
    await first.bootstrap()

    second = KuzuGraphStore(path)
    await second.bootstrap()

    assert first is not second
    assert first._db is second._db  # pyright: ignore[reportPrivateUsage]
    assert first._conn is second._conn  # pyright: ignore[reportPrivateUsage]
