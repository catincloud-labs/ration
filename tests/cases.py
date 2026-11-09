"""Every store this repository's run judges, and what each is expected to fail.

The package builds each case and ships its own in-memory ones; which cases a
run judges is the caller's decision, and this file is this repository's. It
starts from the package's `MEMORY_CASES` -- the in-memory store, the correct
store with an unusual answer, and the violators -- and adds the backends that
are not fakes: DuckDB wherever its driver imports, and Postgres with its naive
violator wherever a server is named.

A plain module rather than `conftest.py`, so that a test filtering the
registry for correct cases imports the same list the suite was handed.
"""

from __future__ import annotations

import os

from ration.conformance.support.backends import (
    DUCKDB_AVAILABLE,
    MEMORY_CASES,
    Case,
    duckdb_case,
    postgres_case,
)
from ration.conformance.postgres_violators import NaivePostgresStore
from ration.postgres import PostgresStore

__all__ = ["CASES", "POSTGRES_DSN", "REQUIRE_POSTGRES"]


#: Where the suite expects a Postgres to be. Unset means one is not available
#: and the case is not registered.
POSTGRES_DSN = os.environ.get("RATION_POSTGRES_DSN", "").strip()

#: Set in CI, and the reason a missing backend cannot go quiet. Absence of a
#: DSN is convenient locally and is a **hole** in a gate: a service container
#: that failed to start, or an environment variable dropped from the workflow,
#: leaves a green run in which the only real store was never exercised.
#: `test_the_suite_discriminates.py` asserts the case is registered whenever
#: this is set.
REQUIRE_POSTGRES = bool(os.environ.get("RATION_REQUIRE_POSTGRES", "").strip())

CASES: list[Case] = list(MEMORY_CASES)

if DUCKDB_AVAILABLE:
    # Registered unconditionally where Postgres needs a DSN, and that
    # asymmetry is the first thing this backend demonstrates: there is no
    # server to name, because the store is a file this process opens. It is
    # also, exactly, why it cannot be a coordination store shared between
    # processes -- `tests/test_duckdb_single_process.py` asserts the consequence.
    CASES.append(duckdb_case("duckdb", set()))

if POSTGRES_DSN:
    CASES.append(postgres_case("postgres", set(), PostgresStore, POSTGRES_DSN))
    # The violator that matters most. Without it the suite would only ever
    # reject fakes this repository wrote, and a contract that cannot
    # discriminate between *real* candidates has bought nothing.
    CASES.append(
        postgres_case("postgres-naive", {"atomicity"}, NaivePostgresStore, POSTGRES_DSN)
    )
