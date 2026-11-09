"""The cases a run judges, as its caller handed them to the suite.

The suite carries no registry of its own, because which stores a run judges is
the caller's decision. This repository's caller registers the package's
in-memory cases, DuckDB where its driver imports, and Postgres where a server is
named. The caller calls `register` before collection, and the suite's
`conftest.py` reads the registries back here when it parametrises a test.

Deliberately a plain module rather than state on `conftest`, for the reason
`declared.py` gives: pytest imports a conftest under a name of its own choosing,
so state kept on one could be bound twice.

**Empty is refused, not read.** A test that takes `backend` or `codec` in a run
whose caller registered no such case raises at collection. Parametrised over
nothing, pytest would report it as skipped, and a run that judged no store must
not read like one that judged some.
"""

from __future__ import annotations

from collections.abc import Sequence

from ration.conformance.support.backends import Case
from ration.conformance.support.codecs import CodecCase

__all__ = ["FIXTURES", "register", "registered"]

#: The fixture names that run a registry: a store for `backend`, a frame codec
#: for `codec`.
FIXTURES = ("backend", "codec")

_REGISTERED: dict[str, tuple[Case, ...] | tuple[CodecCase, ...]] = {}


def register(*, backend: Sequence[Case], codec: Sequence[CodecCase]) -> None:
    """Hand the suite the stores and the frame codecs this run judges."""
    _REGISTERED["backend"] = tuple(backend)
    _REGISTERED["codec"] = tuple(codec)


def registered(fixture: str) -> tuple[Case, ...] | tuple[CodecCase, ...]:
    """The registry `fixture` runs, refusing one that is missing or empty."""
    cases = _REGISTERED.get(fixture, ())
    if not cases:
        raise LookupError(
            f"no case is registered for the `{fixture}` fixture, so a test "
            "taking it would judge nothing. The caller registers its cases with "
            "`ration.conformance.support.registry.register` before collection."
        )
    return cases
