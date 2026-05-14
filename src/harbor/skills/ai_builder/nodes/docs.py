# SPDX-License-Identifier: Apache-2.0
"""DocsChat — Phase C stub.

Full implementation (design §3.4, §9 Phase C):
  Phase C.0 — grep fallback:
    - Extract keywords from turn.
    - Grep /home/sean/leagues/harbor/docs/**/*.md for relevant files.
    - Assemble context window from top matches.
    - Call LLM with assembled context; return response + citations.
  Phase C.1 — embedding upgrade:
    - Switch to RetrievalNode (harbor/nodes/retrieval.py:61) backed by LanceDB.
    - StoreRef(name="harbor_docs", provider="lancedb").
    - Index rebuilt at build time by scripts/ingest_docs.py.

Phase C blocker: docs embedding index and LanceDB store (design §8 Q6).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from harbor.nodes.base import ExecutionContext, NodeBase

if TYPE_CHECKING:
    from pydantic import BaseModel


class DocsChat(NodeBase):
    """Stub — answers Harbor framework documentation questions (Phase C)."""

    # TODO Phase C: implement grep fallback then RetrievalNode upgrade (design §3.4).
    async def execute(self, state: BaseModel, ctx: ExecutionContext) -> dict[str, Any]:
        return {
            "response": "docs not yet implemented (Phase C)",
            "citations": [],
        }
