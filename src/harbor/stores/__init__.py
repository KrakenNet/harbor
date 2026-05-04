# SPDX-License-Identifier: Apache-2.0
"""harbor.stores public surface (design §5).

Re-exports the five Store Protocols, default Providers, value models,
and supporting embedding / reranker / cypher utilities.

``RyuGraphStore`` and ``LanceDBVectorStore`` live behind the ``stores``
optional-dependency group (``ryugraph``, ``lancedb``, ``pyarrow``) so
they are surfaced via PEP 562 module-level ``__getattr__``: the
provider modules are only imported when a caller actually accesses
the name (e.g. ``from harbor.stores import RyuGraphStore``). Engine /
serve subsystems that depend on the lightweight Protocol surface
(``GraphStore`` / ``VectorStore``) can import :mod:`harbor.stores`
without forcing the stores-extra wheels to be installed.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

from harbor.stores._common import MigrationPlan, StoreHealth
from harbor.stores.cypher import Linter
from harbor.stores.doc import DocStore, Document
from harbor.stores.embeddings import Embedding, MiniLMEmbedder
from harbor.stores.fact import Fact, FactPattern, FactStore
from harbor.stores.graph import GraphPath as Path
from harbor.stores.graph import GraphStore, NodeRef, ResultSet
from harbor.stores.memory import (
    AddDelta,
    ConsolidationRule,
    DeleteDelta,
    Episode,
    MemoryDelta,
    MemoryStore,
    NoopDelta,
    UpdateDelta,
)
from harbor.stores.rerankers import Reranker, RRFReranker
from harbor.stores.sqlite_doc import SQLiteDocStore
from harbor.stores.sqlite_fact import SQLiteFactStore
from harbor.stores.sqlite_memory import SQLiteMemoryStore
from harbor.stores.vector import Hit, Row, VectorStore

if TYPE_CHECKING:
    from harbor.stores.lancedb import LanceDBVectorStore
    from harbor.stores.ryugraph import RyuGraphStore


# (attribute name) -> (module path, class name). Resolved lazily by
# :func:`__getattr__` so importing :mod:`harbor.stores` never forces the
# stores-extra wheels (ryugraph / lancedb / pyarrow) to be present.
_OPTIONAL_PROVIDERS: dict[str, tuple[str, str]] = {
    "LanceDBVectorStore": ("harbor.stores.lancedb", "LanceDBVectorStore"),
    "RyuGraphStore": ("harbor.stores.ryugraph", "RyuGraphStore"),
}


def __getattr__(name: str) -> Any:
    spec = _OPTIONAL_PROVIDERS.get(name)
    if spec is None:
        msg = f"module {__name__!r} has no attribute {name!r}"
        raise AttributeError(msg)
    return getattr(importlib.import_module(spec[0]), spec[1])


__all__ = [
    "AddDelta",
    "ConsolidationRule",
    "DeleteDelta",
    "DocStore",
    "Document",
    "Embedding",
    "Episode",
    "Fact",
    "FactPattern",
    "FactStore",
    "GraphStore",
    "Hit",
    "LanceDBVectorStore",
    "Linter",
    "MemoryDelta",
    "MemoryStore",
    "MigrationPlan",
    "MiniLMEmbedder",
    "NodeRef",
    "NoopDelta",
    "Path",
    "RRFReranker",
    "Reranker",
    "ResultSet",
    "Row",
    "RyuGraphStore",
    "SQLiteDocStore",
    "SQLiteFactStore",
    "SQLiteMemoryStore",
    "StoreHealth",
    "UpdateDelta",
    "VectorStore",
]
