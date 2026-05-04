# SPDX-License-Identifier: Apache-2.0
"""Cypher portable-subset linter (FR-12, design §3.2).

POC implementation: regex-based ban-list scanning. The allow-list is
implicit -- anything not matching a ban pattern passes. Queries that
fail :meth:`Linter.check` raise :class:`UnportableCypherError` so a
single seam guards every Cypher string before it reaches RyuGraph or
Neo4j 5.

The linter also exposes :meth:`Linter.requires_write`, a keyword scan
used by FR-20 capability gating to decide whether a query mutates
graph state.
"""

from __future__ import annotations

import re

from harbor.errors import UnportableCypherError

# Ban-list: tuples of (rule name, compiled pattern).
# Order matters only for error-message stability -- the first match wins.
_BAN_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("apoc-call", re.compile(r"apoc\.", re.IGNORECASE)),
    ("gds-call", re.compile(r"gds\.", re.IGNORECASE)),
    (
        "call-in-transactions",
        re.compile(r"CALL\s*\{[^}]*\}\s*IN\s+TRANSACTIONS", re.IGNORECASE | re.DOTALL),
    ),
    ("load-csv", re.compile(r"LOAD\s+CSV", re.IGNORECASE)),
    ("load-from", re.compile(r"LOAD\s+FROM", re.IGNORECASE)),
    ("show-functions", re.compile(r"SHOW\s+FUNCTIONS", re.IGNORECASE)),
    ("show-indexes", re.compile(r"SHOW\s+INDEXES", re.IGNORECASE)),
    ("show-constraints", re.compile(r"SHOW\s+CONSTRAINTS", re.IGNORECASE)),
    ("yield-star", re.compile(r"YIELD\s+\*", re.IGNORECASE)),
    ("shortest-path", re.compile(r"shortestPath", re.IGNORECASE)),
    ("dynamic-label", re.compile(r":\$\(")),
    ("map-projection", re.compile(r"\{\.\w+")),
    ("path-comprehension", re.compile(r"\[\(.+\|.+\]")),
    ("collect-subquery", re.compile(r"COLLECT\s*\{", re.IGNORECASE)),
)

# Variable-length paths must be bounded, e.g. `*1..3`. Bare `*` followed
# by anything other than a digit or dot rejects.
_VARLEN_UNBOUNDED = re.compile(r"\*[^0-9.]")

# Mutating subquery: a CALL { ... } block whose body contains RETURN
# implies a read-side subquery, but combined with mutation keywords in
# the outer scope it's still rejected because RyuGraph does not support
# subqueries in our subset.
_MUTATING_SUBQUERY = re.compile(r"CALL\s*\{[^}]*\bRETURN\b", re.IGNORECASE | re.DOTALL)

_WRITE_KEYWORDS = re.compile(
    r"\b(CREATE|MERGE|SET|DELETE|REMOVE|DROP|ALTER|COPY)\b",
    re.IGNORECASE,
)


class Linter:
    """Cypher portable-subset linter (FR-12).

    Stateless; instances exist only so callers can pass a linter as a
    dependency.
    """

    def check(self, cypher: str) -> None:
        """Reject queries that fall outside the RyuGraph/Neo4j-5 subset.

        Scans ban-list first, then variable-length unbounded paths, then
        mutating subqueries. Raises :class:`UnportableCypherError` with
        the matched substring in ``context['match']`` and the rule name
        in ``context['rule']``.
        """
        for rule, pattern in _BAN_PATTERNS:
            m = pattern.search(cypher)
            if m is not None:
                raise UnportableCypherError(
                    f"Cypher rejected by linter rule {rule!r}: {m.group(0)!r}",
                    cypher=cypher,
                    violation=rule,
                    rule=rule,
                    match=m.group(0),
                )

        m = _VARLEN_UNBOUNDED.search(cypher)
        if m is not None:
            raise UnportableCypherError(
                f"Cypher rejected by linter rule 'varlen-unbounded': {m.group(0)!r}",
                cypher=cypher,
                violation="varlen-unbounded",
                rule="varlen-unbounded",
                match=m.group(0),
            )

        m = _MUTATING_SUBQUERY.search(cypher)
        if m is not None:
            raise UnportableCypherError(
                f"Cypher rejected by linter rule 'mutating-subquery': {m.group(0)!r}",
                cypher=cypher,
                violation="mutating-subquery",
                rule="mutating-subquery",
                match=m.group(0),
            )

    def requires_write(self, cypher: str) -> bool:
        """Return True if ``cypher`` contains any write keyword (FR-20).

        Keyword-scan only -- comments and string literals are not
        stripped, which is acceptable for the capability-gating use
        case (false positives are safe; false negatives would not be).
        """
        return _WRITE_KEYWORDS.search(cypher) is not None
