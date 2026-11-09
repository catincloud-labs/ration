"""The case a stranger builds for a store of their own, shared by every arm.

The shape the README documents under *Running the suite against your own
store*: a store built fresh for each test, read through `FaultInjector` so the
suite can lose a write's answer, with the store's own clock passed by waiting.
Every arm builds its case here, so two arms differ only in the store they hand
it and the switches their run sets.

`arms.py` copies this file beside each arm's `conftest.py`; it is not imported
from this tree.
"""

from __future__ import annotations

import time
from collections.abc import Callable

from ration.conformance.support.backends import BackendUnderTest, Case
from ration.conformance.support.faults import FaultInjector
from ration.contract import Store


def store_case(name: str, make_store: Callable[[], Store]) -> Case:
    """A case for a store its registrant claims is correct: `violates` is empty."""

    def build() -> BackendUnderTest:
        faults = FaultInjector(make_store())
        return BackendUnderTest(
            case=case,
            store=faults,
            # The store reads its own clock, so its time passes by waiting.
            advance_store_time=time.sleep,
            # The store is never told what time the caller thinks it is.
            skew_client_clock=lambda _seconds: None,
            # In one process there is no substrate to cut, so the harness
            # refuses on the store's behalf. A store with a server points
            # itself somewhere that refuses a connection instead.
            partition=faults.partition,
            ambiguity=faults.ambiguity,
        )

    case = Case(name=name, violates=frozenset(), build=build)
    return case
