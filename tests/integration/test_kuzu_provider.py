# SPDX-License-Identifier: Apache-2.0
"""Kuzu provider integration tests (FR-3, FR-11, AC-12.2/12.3).

Three smoke tests pinning the public Protocol surface of
:class:`~harbor.stores.kuzu.KuzuGraphStore` against a real on-disk
Kuzu database:

1. :func:`test_bootstrap_creates_entity_rel_tables` -- bootstrap
   installs both the ``Entity`` node table and the ``Rel`` edge table
   per design §3.2.
2. :func:`test_add_triple_then_query` -- ``add_triple`` round-trips
   through ``query`` (single triple, single hit).
3. :func:`test_kuzu_async_connection` -- the underlying connection is
   the native :class:`kuzu.AsyncConnection` (smoke check on impl).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import kuzu
import pytest

from harbor.stores.graph import NodeRef
from harbor.stores.kuzu import KuzuGraphStore

if TYPE_CHECKING:
    from pathlib import Path


pytestmark = [pytest.mark.knowledge, pytest.mark.integration]


async def test_bootstrap_creates_entity_rel_tables(tmp_path: Path) -> None:
    """``bootstrap`` installs Entity (NODE) + Rel (REL) tables (design §3.2)."""
    store = KuzuGraphStore(tmp_path / "graph")
    await store.bootstrap()

    rs = await store.query("CALL show_tables() RETURN *")
    table_types = {(row["name"], row["type"]) for row in rs.rows}
    assert ("Entity", "NODE") in table_types
    assert ("Rel", "REL") in table_types


async def test_add_triple_then_query(tmp_path: Path) -> None:
    """``add_triple`` upsert round-trips through ``query`` (FR-3)."""
    store = KuzuGraphStore(tmp_path / "graph")
    await store.bootstrap()

    await store.add_triple(
        NodeRef(id="alice", kind="Person"),
        "knows",
        NodeRef(id="bob", kind="Person"),
    )

    rs = await store.query(
        "MATCH (s:Entity)-[r:Rel]->(o:Entity) "
        "RETURN s.id AS subject, r.predicate AS predicate, o.id AS object"
    )
    assert len(rs.rows) == 1
    row = rs.rows[0]
    assert row["subject"] == "alice"
    assert row["predicate"] == "knows"
    assert row["object"] == "bob"


async def test_kuzu_async_connection(tmp_path: Path) -> None:
    """Underlying connection is the native :class:`kuzu.AsyncConnection` (FR-11)."""
    store = KuzuGraphStore(tmp_path / "graph")
    await store.bootstrap()

    conn = store._require_conn()  # pyright: ignore[reportPrivateUsage]
    assert isinstance(conn, kuzu.AsyncConnection)
