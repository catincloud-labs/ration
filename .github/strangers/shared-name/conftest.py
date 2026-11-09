"""A stranger who names a store after one of the package's own cases.

The store is correct; the name is the package's `correct`. Two cases under one
name could not be told apart in the report or by `--ration-require`, so the
plugin must refuse the run before collecting it.
"""

from __future__ import annotations

from stranger import store_case

from ration.conformance.support.backends import Case
from ration.memory import MemoryStore

pytest_plugins = ["ration.conformance.plugin"]


def pytest_ration_cases() -> list[Case]:
    return [store_case("correct", MemoryStore)]
