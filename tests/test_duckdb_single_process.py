"""DuckDB passes the contract and cannot hold it. Both halves are asserted here.

This is not a conformance test and declares no property, so
`tests/test_the_suite_discriminates.py` never counts it. It exists because the
conformance suite returned an answer that is true and dangerously incomplete.

**THE RESULT THIS FILE EXISTS FOR: `duckdb` passes every conformance test.**
Not a subset -- all of them, registered as a `Case` with an empty `violates` set
the way `postgres` is, running the tests that reject every registered violator.
On the suite's own evidence it qualifies.

**And it cannot be a coordination store shared between processes, for a reason
the conformance suite is structurally unable to see.** DuckDB is embedded: the
database is a file, and one process owns it. A coordination store exists *so
that other processes can reach it*; there is nothing here to reach. It does not
fail at the second host. It fails at the second **process**, which is why
`pool.py` -- N simultaneous holders, each its own process -- could not be built
on it even on one box.

**This is the sharpest thing this repository can say about its own
instruments.** Every violator in `src/ration/conformance/violators.py` is wrong *logically*: it
computes an answer the contract forbids, in one process, where the suite is
looking. DuckDB is wrong *structurally*, and the in-process suite is exactly the
wrong shape to notice. A backend can be correct in one interpreter and
undeployable, and a green conformance run says nothing about the difference.

So the suite is not weakened by this and should not be "fixed" to reject DuckDB
by adding a property. There is no contract property being violated. What the
suite decides is whether a backend implements the contract, and DuckDB does. The
missing judgement is about **deployment topology**, which the contract
deliberately does not govern -- and putting it in the contract would be
inventing a clause with no caller.

## Why the assertions are the way they are

The refusal is asserted from a **separate interpreter under `spawn`**, because
that is the only population in which the claim means anything. It is asserted
against raw `duckdb.connect`, so the verdict is about the engine rather than
about this repository's wrapper, and beside it the same child is shown to open
the same file once the holder lets go.
"""

from __future__ import annotations

import multiprocessing as mp
import os
import tempfile

import pytest

from ration.contract import ABSENT, Applied, Record
from ration.conformance.support.backends import DUCKDB_AVAILABLE
from tests.support.crossprocess import duckdb_open_attempt

pytestmark = pytest.mark.skipif(
    not DUCKDB_AVAILABLE, reason="duckdb is not installed"
)

if DUCKDB_AVAILABLE:
    from ration.duckdb_store import DuckDBStore


@pytest.fixture
def held_store(tmp_path_factory: pytest.TempPathFactory):
    """A store this process holds open, with a key written through it."""
    path = str(tmp_path_factory.mktemp("duckdb-held") / "ration.duckdb")
    store = DuckDBStore(path)
    store.ensure_schema()
    outcome = store.compare_and_set("held", ABSENT, Record(b"1", "owner"))
    assert isinstance(outcome, Applied), "setup failed before the probe ran"
    yield store, path
    store.close()


def test_a_second_process_cannot_open_the_database_at_all(held_store) -> None:
    """The disqualifying fact, measured from a real second interpreter.

    Asserted against raw `duckdb.connect`, so the verdict is about the engine
    rather than about `DuckDBStore`.
    """
    _store, path = held_store

    ctx = mp.get_context("spawn")
    with ctx.Pool(1) as pool:
        child_pid, verdict = pool.apply(duckdb_open_attempt, (path,))

    # The harness before the store, the rule this repository already applies to
    # its cross-process probe: a child that silently ran in the parent would
    # produce a verdict about nothing.
    assert child_pid != os.getpid(), (
        "the probe ran in the parent interpreter, so it measured nothing about "
        f"a second process (pid {child_pid})"
    )
    assert verdict.startswith("REFUSED"), (
        "a second process opened a DuckDB database this process holds. The "
        "objection to DuckDB as a shared coordination store is that an embedded, "
        "single-process database cannot serve a second process; if this fails, "
        f"that objection has gone away. Verdict: {verdict}"
    )


def test_the_file_is_openable_once_this_process_lets_go(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """The control, and without it the two tests above prove far less.

    A path that could never be opened by anyone -- a bad filename, a missing
    directory, a permissions error -- would satisfy both assertions above while
    demonstrating nothing about DuckDB's concurrency model. This asserts the
    same child succeeds against the same path the moment the lock is released,
    which is what makes the refusal *exclusivity* rather than breakage.
    """
    path = str(tmp_path_factory.mktemp("duckdb-released") / "ration.duckdb")
    store = DuckDBStore(path)
    store.ensure_schema()
    store.close()

    ctx = mp.get_context("spawn")
    with ctx.Pool(1) as pool:
        child_pid, verdict = pool.apply(duckdb_open_attempt, (path,))

    assert child_pid != os.getpid(), "the probe ran in the parent interpreter"
    assert verdict == "OPENED", (
        "the control failed: a child could not open the database even with no "
        f"holder, so the refusals above may be breakage rather than exclusivity: {verdict}"
    )
