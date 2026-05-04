# Stores

Five `Protocol` classes describe Harbor's storage contracts; three default
Providers ship in-tree as embeddable Python backends. The shape mirrors
`Checkpointer` — every store implements the same `bootstrap / health /
migrate` lifecycle on top of CRUD specific to its data model.

## The five Protocols

| Protocol | Data model | Default Provider | Backed by |
|---|---|---|---|
| `VectorStore` | dense vectors + metadata + FTS | `LanceDBVectorStore` | LanceDB (Lance columnar format) |
| `GraphStore` | labeled property graph | `RyuGraphStore` | RyuGraph single-file embedded graph DB (community fork of Kuzu) |
| `DocStore` | binary / text blobs + metadata | `SQLiteDocStore` | SQLite (WAL) |
| `MemoryStore` | episodic events scoped `(user, session, agent)` | `SQLiteMemoryStore` | SQLite (WAL) |
| `FactStore` | semantic facts scoped `(user, agent)` | `SQLiteFactStore` | SQLite (WAL) + `FathomAdapter` |

```python
from harbor.stores import (
    VectorStore, GraphStore, DocStore, MemoryStore, FactStore,
    StoreHealth, MigrationPlan,
)
```

Every Protocol exposes the same lifecycle:

```python
class VectorStore(Protocol):
    async def bootstrap(self) -> None: ...
    async def health(self) -> StoreHealth: ...
    async def migrate(self, plan: MigrationPlan) -> None: ...
    # ...store-specific CRUD
```

`bootstrap()` is idempotent; `health()` returns a `StoreHealth` record the
runtime can poll; `migrate()` accepts the IR migration block from
`Graph(ir).migrations`. Schema evolution is **add-nullable-column only** —
type narrows and renames are rejected loudly.

## Three default Providers

- **`LanceDBVectorStore`** (`harbor.stores.lancedb`) — async-first LanceDB
  client; native Lance FTS (`use_tantivy=False`); hybrid search fuses vector
  + FTS via the configured reranker (default `RRFReranker()`).
- **`RyuGraphStore`** (`harbor.stores.ryugraph`) — single-file embedded graph
  DB (RyuGraph: community fork of Kuzu after the Kuzu repo was archived
  2025-10-10); portable Cypher subset enforced by `harbor.stores.cypher.Linter`;
  Cypher-write keyword scan applies on `query()`.
- **SQLite trio** (`harbor.stores.sqlite_doc`, `sqlite_memory`,
  `sqlite_fact`) — shared pragma block inherited from engine FR-17:

  ```sql
  PRAGMA journal_mode=WAL;
  PRAGMA synchronous=NORMAL;
  PRAGMA busy_timeout=5000;
  PRAGMA foreign_keys=ON;
  ```

  JSONB columns serialize through the canonical orjson codec at
  `harbor.checkpoint._codec` — no second codec.

## Embed-hash drift gate

Embedding model drift silently corrupts retrieval — same vector dim,
incompatible vector space. The gate eliminates the failure class:

1. At `VectorStore.bootstrap()` the Provider writes
   `(model_id, revision, content_hash, ndims)` into table-level metadata.
2. On every re-entry the same tuple is re-computed and compared.
3. Mismatch raises `IncompatibleEmbeddingHashError` — a subclass of
   `HarborError` carrying `expected` / `actual` tuples.

```python
class IncompatibleEmbeddingHashError(HarborError):
    """The embedder loaded at runtime does not match the one that wrote the
    table. Continuing would silently corrupt retrieval results."""
```

The error mirrors the engine's `IncompatibleModelHashError` — same shape,
same force-loud contract (FR-6).

## Single-writer concurrency

All three embedded backends — LanceDB on local FS (issues #213, #1077,
#2002), RyuGraph's documented single-writer model (inherited from Kuzu), SQLite on WAL — assume one
writer per file path. Harbor enforces this in-process:

- Each Provider holds an `asyncio.Lock` keyed by absolute store path.
- `health()` warns when the path resolves to a network filesystem
  (`nfs / smb / cifs`) — file locks are not reliable across NFS (LanceDB
  #1433).
- Multi-process write is a v1 deferral; the Protocol leaves room for a
  future advisory-lock or transactional layer.

Single-writer is **the** safety contract for embedded storage. The locks
are not an optimization; they are the only correct concurrency model.

## Reuse map

| External | Reused from | Why |
|---|---|---|
| JSONB serialization | `harbor.checkpoint._codec` | One canonical orjson codec |
| Migration mechanism | `_migrations` hand-roll, engine FR-17 | No Alembic |
| Provenance writes | `FathomAdapter.assert_with_provenance` | Single seam for fact promotion |
| Force-loud errors | `harbor.errors._hierarchy` | One hierarchy across stack |

See [design §3.1–3.5](https://github.com/KrakenNet/harbor/blob/main/specs/harbor-knowledge/design.md)
for the full Protocol method tables and Provider implementation notes.
