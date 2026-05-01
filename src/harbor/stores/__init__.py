# SPDX-License-Identifier: Apache-2.0
"""harbor.stores public surface (design §5).

Re-exports the five Store Protocols, default Providers, value models,
and supporting embedding / reranker / cypher utilities.
"""

from __future__ import annotations

from harbor.stores._common import MigrationPlan, StoreHealth
from harbor.stores.cypher import Linter
from harbor.stores.doc import DocStore, Document
from harbor.stores.embeddings import Embedding, MiniLMEmbedder
from harbor.stores.fact import Fact, FactPattern, FactStore
from harbor.stores.graph import GraphPath as Path
from harbor.stores.graph import GraphStore, NodeRef, ResultSet
from harbor.stores.kuzu import KuzuGraphStore
from harbor.stores.lancedb import LanceDBVectorStore
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
    "KuzuGraphStore",
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
    "SQLiteDocStore",
    "SQLiteFactStore",
    "SQLiteMemoryStore",
    "StoreHealth",
    "UpdateDelta",
    "VectorStore",
]
