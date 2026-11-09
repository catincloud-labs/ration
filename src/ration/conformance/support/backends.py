"""How each store the suite runs against is built, and what each is expected to fail.

The suite's job is not to validate a backend. It is to **discriminate between
backends**, so the registry a run hands it is the suite's actual subject:
in-memory stores that should pass everything, a set that should each fail a
named property and pass the rest, and the backends that are not fakes at all.
This module builds each kind of case. `MEMORY_CASES` below is the package's
own share of a registry: the in-memory store, the correct store with an
unusual answer, and the violators, each paired with the property it breaks.
Which cases a run judges is its caller's registry; this repository's is
`tests/cases.py` in the source tree.

A new backend is added to a caller's registry and runs what is already
written. It does not get tests of its own, and if it needs a special case to
pass, that is a finding about the backend or the contract rather than a
fixture to write.

## What a real backend demands of the harness

Two assumptions that hold for an in-process fake do not survive contact with a
server:

- **A fake clock is not a clock.** `store_clock.advance(61)` is free against a
  `FakeClock` and impossible against `now()` on a server. Time is passed by
  `advance_store_time()`, which each backend implements the only way it can --
  by moving a fake clock, or by actually waiting.
- **An in-process seam does not exist across a socket.** Postgres has no
  `_staged` to park in, because its atomic step is a single SQL statement on the
  far side of a connection. `stepped()` returns `None` there, and that absence
  is *evidence* rather than an exemption: a store with no window has nowhere to
  be parked. The guard against abusing it lives in the stepper test.
"""

from __future__ import annotations

import os
import tempfile
import time
import uuid
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ration.contract import Store
from ration.memory import MemoryStore

if TYPE_CHECKING:
    # An annotation only, so the suite imports no driver; see `postgres_case`.
    from ration.postgres import PostgresStore

try:
    from ration.duckdb_store import DuckDBStore
except ImportError:  # pragma: no cover - exercised by not having the driver
    DUCKDB_AVAILABLE = False
else:
    DUCKDB_AVAILABLE = True
from ration.conformance.permitted import PreviousVersionStore
from ration.conformance.support.clock import FakeClock
from ration.conformance.support.faults import FaultInjector
from ration.conformance.support.gate import Gate
from ration.conformance.violators import (
    ClientExpiryStore,
    ConflictWritesStore,
    CreateAlwaysStore,
    EchoesExpectedStore,
    FailOpenStore,
    GlobalCounterStore,
    NaiveStore,
    RecyclingStore,
    StaleClockStore,
    TokenDroppingStore,
)

__all__ = [
    "DUCKDB_AVAILABLE",
    "MEMORY_CASES",
    "REAL_TTL",
    "BackendUnderTest",
    "Case",
    "duckdb_case",
    "postgres_case",
]

#: How long the suite is prepared to actually wait when it cannot fake time.
#: Short enough that a full run stays quick; long enough to survive a round trip
#: to a server on a loaded CI runner.
REAL_TTL = 0.5


def _parking(cls: type[MemoryStore], gate: Gate) -> type[MemoryStore]:
    """Subclass `cls` so its staging seam parks in `gate`.

    Done here rather than by handing the store a hook, so that no production
    constructor grows a parameter existing only for a test.
    """
    return type(
        f"Parking{cls.__name__}",
        (cls,),
        {"_staged": lambda self: gate.arrive()},
    )


@dataclass
class BackendUnderTest:
    """A built store, plus the handles a conformance test needs to press on it.

    Everything here is a capability of the **harness**, not of the contract.
    None of it is required of a backend and none of it appears in `Store`.
    """

    case: Case
    store: Store
    #: Passes `seconds` of store time, by whatever means this backend has.
    advance_store_time: Callable[[float], None]
    #: Moves a clock on the *caller's* side of the boundary. For a store that
    #: never consults one, this is a no-op -- and that it then changes nothing
    #: is the result rather than a gap.
    skew_client_clock: Callable[[float], None]
    #: Makes the store unreachable, as close to genuinely as the backend allows.
    partition: Callable[[], AbstractContextManager[None]]
    #: Makes the next write raise `Ambiguous`, having done what `applied` says.
    ambiguity: Callable[..., AbstractContextManager[None]]
    #: `None` where the store's atomic step is not in this process.
    _stepped: Callable[[Gate], BackendUnderTest] | None
    _prefix: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    _keys: int = field(default=0, repr=False)

    @property
    def name(self) -> str:
        return self.case.name

    @property
    def supports_stepping(self) -> bool:
        return self._stepped is not None

    def key(self) -> str:
        """A key nothing else has touched, in this run or in a previous one.

        The prefix is per instance and random because a real backend keeps what
        the last run wrote. A suite that reuses key names against a persistent
        store is asserting about someone else's leftovers.
        """
        self._keys += 1
        return f"{self.case.name}/{self._prefix}/key-{self._keys}"

    def stepped(self, gate: Gate) -> BackendUnderTest | None:
        return self._stepped(gate) if self._stepped is not None else None


@dataclass(frozen=True)
class Case:
    """One implementation, and the properties it is expected to fail."""

    name: str
    violates: frozenset[str]
    build: Callable[..., BackendUnderTest]


def _memory_case(
    name: str,
    violates: set[str],
    store_class: type[MemoryStore],
    *,
    wrap: Callable[[Store], Store] | None = None,
    needs_client_clock: bool = False,
) -> Case:
    def build(gate: Gate | None = None) -> BackendUnderTest:
        store_clock = FakeClock()
        client_clock = FakeClock()
        cls = _parking(store_class, gate) if gate is not None else store_class
        kwargs: dict[str, Callable[[], float]] = {"clock": store_clock}
        if needs_client_clock:
            kwargs["client_clock"] = client_clock
        faults = FaultInjector(cls(**kwargs))
        store: Store = wrap(faults) if wrap is not None else faults
        return BackendUnderTest(
            case=case,
            store=store,
            advance_store_time=store_clock.advance,
            skew_client_clock=client_clock.advance,
            partition=faults.partition,
            ambiguity=faults.ambiguity,
            _stepped=lambda g: case.build(g),
        )

    case = Case(name=name, violates=frozenset(violates), build=build)
    return case


def duckdb_case(name: str, violates: set[str]) -> Case:
    """A backend with no server, which is the whole of what makes it interesting."""

    def build(gate: Gate | None = None) -> BackendUnderTest:
        # In-process is not the same as having a seam. DuckDB runs inside this
        # interpreter, but its atomic step is a statement executed by the
        # engine, so there is no Python-level window to park in any more than
        # there is across a socket. Parking would have to happen inside DuckDB's
        # own transaction manager. Handing back a "stepped" instance would give
        # the test a gate that never fires.
        assert gate is None, "the DuckDB store's atomic step is inside the engine"

        directory = tempfile.mkdtemp(prefix="ration-duckdb-")
        address = {"path": os.path.join(directory, "ration.duckdb")}
        store = DuckDBStore(lambda: address["path"])
        store.ensure_schema()

        @contextmanager
        def partition() -> Iterator[None]:
            # A path under a directory that does not exist. DuckDB raises
            # IOException on open, which the backend translates. This is the
            # store genuinely failing to reach its substrate rather than the
            # harness refusing on its behalf -- the same standard the Postgres
            # case holds itself to with an unlistening port.
            was = address["path"]
            address["path"] = os.path.join(directory, "gone", "nowhere.duckdb")
            store.close()
            try:
                yield
            finally:
                address["path"] = was
                store.close()

        faults = FaultInjector(store)

        return BackendUnderTest(
            case=case,
            store=faults,
            # The engine reads its own clock, so time cannot be faked here any
            # more than it can against a server. This is the same honest cost
            # the Postgres case pays, and the reason REAL_TTL is small.
            advance_store_time=time.sleep,
            # DuckDB is never told what time the caller thinks it is. That the
            # assertion then holds trivially is the correct result.
            skew_client_clock=lambda _seconds: None,
            partition=partition,
            ambiguity=faults.ambiguity,
            _stepped=None,
        )

    case = Case(name=name, violates=frozenset(violates), build=build)
    return case


def postgres_case(
    name: str, violates: set[str], store_class: type[PostgresStore], dsn: str
) -> Case:
    """The backends that are not fakes, and therefore the ones testing this file.

    `dsn` names the server. Which server, and whether there is one, is the
    caller's to say, so the case is built only where one is named.
    """

    def build(gate: Gate | None = None) -> BackendUnderTest:
        # A store whose atomic step is a SQL statement has no seam to park in.
        # Handing back a "stepped" instance anyway would be worse than handing
        # back nothing: the gate would never fire, and the test would pass on a
        # window it never entered.
        assert gate is None, "the Postgres store has no in-process seam"

        # The address is swapped, not intercepted. `partition()` here means the
        # store is pointed somewhere that refuses a connection, so what the
        # suite observes is Postgres failing and the backend translating it --
        # rather than a refusal the harness performed on the store's behalf.
        address = {"dsn": dsn}
        store = store_class(lambda: address["dsn"])
        store.ensure_schema()

        @contextmanager
        def partition() -> Iterator[None]:
            # Port 1 is reserved and nothing listens on it. A DSN that failed to
            # *parse* would raise a different error and prove something else.
            was = address["dsn"]
            address["dsn"] = "postgresql://ration@127.0.0.1:1/ration"
            try:
                yield
            finally:
                address["dsn"] = was

        # Ambiguity stays simulated for every backend, including this one. The
        # write really does reach Postgres and really does commit; what is
        # injected is the loss of the answer, which is the half a caller cannot
        # arrange and the half the property is about.
        faults = FaultInjector(store)

        return BackendUnderTest(
            case=case,
            store=faults,
            # The only honest implementation against a server's clock, and
            # the reason `REAL_TTL` is a fraction of a second rather than the
            # minute a fake clock skips for free.
            advance_store_time=time.sleep,
            # Postgres is never told what time the caller thinks it is, so
            # there is no clock here to skew. That the assertion then holds
            # trivially is the correct result, not a weakened one.
            skew_client_clock=lambda _seconds: None,
            partition=partition,
            ambiguity=faults.ambiguity,
            _stepped=None,
        )

    case = Case(name=name, violates=frozenset(violates), build=build)
    return case


#: The package's own cases: every in-memory store, correct or not. A caller's
#: registry starts from these, so a run that judges any store also shows each
#: violator below failing its property beside the correct store passing.
MEMORY_CASES: tuple[Case, ...] = (
    _memory_case("correct", set(), MemoryStore),
    # Correct as well, and the only registered store whose conflict reports a
    # version the key held before its current one even when nothing races it
    # (`postgres` does so only for the loser of a race). It is what tells the
    # compare-and-set test's "any version the key has held" from "the current
    # version": tighten that assertion and this case alone turns red.
    _memory_case("previous-version", set(), PreviousVersionStore),
    _memory_case("create-always", {"compare-and-set"}, CreateAlwaysStore),
    _memory_case("echoes-expected", {"compare-and-set"}, EchoesExpectedStore),
    _memory_case(
        "conflict-writes", {"compare-and-set", "atomicity"}, ConflictWritesStore
    ),
    _memory_case("naive", {"atomicity"}, NaiveStore),
    _memory_case("recycling", {"version-monotonic"}, RecyclingStore),
    _memory_case("global-counter", {"version-monotonic"}, GlobalCounterStore),
    _memory_case(
        "client-expiry",
        {"store-evaluated-expiry"},
        ClientExpiryStore,
        needs_client_clock=True,
    ),
    _memory_case("stale-clock", {"store-evaluated-expiry"}, StaleClockStore),
    # A correct store behind a layer that swallows the refusal, because that is
    # where failing open is actually written.
    _memory_case("fail-open", {"unreachable-refuses"}, MemoryStore, wrap=FailOpenStore),
    _memory_case("token-dropping", {"ambiguity-resolvable"}, TokenDroppingStore),
)
