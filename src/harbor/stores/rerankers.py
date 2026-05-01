# SPDX-License-Identifier: Apache-2.0
"""Reranker Protocol + RRFReranker default (FR-16, design §3.8).

Defines the structural contract used by ``RetrievalNode`` to fuse per-store
hit lists into a single ranked list. The default :class:`RRFReranker`
implements Reciprocal Rank Fusion -- score = ``Σ 1/(k_param + rank_i)``
across each store's per-list rank -- a model-free, API-key-free fusion
rule appropriate for the default ``mode="hybrid"`` path.

Heavier rerankers (cross-encoder, Cohere, Jina) live behind the
``harbor.rerankers`` entry-point group and are opt-in; this module ships
only the always-available default.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from harbor.stores.vector import Hit

__all__ = [
    "CrossEncoderReranker",
    "RRFReranker",
    "Reranker",
]


@runtime_checkable
class Reranker(Protocol):
    """Structural contract for rerankers (design §3.8).

    Implementations fuse ``per_store`` (one ranked list per store) into a
    single ranked list of length ``<= k``. Async by convention so that
    network-bound rerankers (Cohere / Jina) share the same shape as the
    pure-Python default.
    """

    async def fuse(self, per_store: list[list[Hit]], *, k: int) -> list[Hit]:
        """Fuse per-store ranked lists into a single top-``k`` list."""
        ...


class RRFReranker:
    """Reciprocal Rank Fusion reranker (design §3.8).

    For each :class:`Hit` appearing in any per-store list, the fused
    score is ``Σ_lists 1/(k_param + rank_in_list)`` where ``rank_in_list``
    is 1-based. Hits sharing an ``id`` across stores are de-duplicated
    and their RRF contributions summed; the first-seen ``metadata`` is
    retained. Output is sorted by fused score desc and truncated to
    ``k``.
    """

    def __init__(self, k_param: int = 60) -> None:
        self.k_param = k_param

    async def fuse(self, per_store: list[list[Hit]], *, k: int) -> list[Hit]:
        # Collect per-id contributions as a list, then sum in sorted order.
        # Float addition is non-associative, so ordering the addends makes
        # the fused score depend only on the multiset of contributions --
        # required for the permutation-invariance guarantee in design §3.8.
        contributions: dict[str, list[float]] = {}
        first_seen: dict[str, Hit] = {}
        for hits in per_store:
            for rank, hit in enumerate(hits, start=1):
                contributions.setdefault(hit.id, []).append(1.0 / (self.k_param + rank))
                if hit.id not in first_seen:
                    first_seen[hit.id] = hit
        scores = {hit_id: sum(sorted(parts)) for hit_id, parts in contributions.items()}
        ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
        return [
            Hit(id=hit_id, score=score, metadata=first_seen[hit_id].metadata)
            for hit_id, score in ranked[:k]
        ]


class CrossEncoderReranker:
    """Cross-encoder reranker stub (Phase 3 will implement).

    Placeholder for the opt-in cross-encoder reranker registered under
    the ``harbor.rerankers`` entry-point group. Phase 3 fills in the
    sentence-transformers-backed ``.fuse()`` body.
    """

    async def fuse(self, per_store: list[list[Hit]], *, k: int) -> list[Hit]:
        raise NotImplementedError("CrossEncoderReranker is implemented in Phase 3")
