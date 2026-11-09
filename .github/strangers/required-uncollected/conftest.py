"""A stranger whose store is registered and whose run never collects the suite.

The arm runs `pytest --ration-require stranger-memory` without
`--pyargs ration.conformance`, so pytest collects the stranger's own test
beside this file and no test that judges a store.
"""

from __future__ import annotations

from stranger import store_case

from ration.conformance.support.backends import Case
from ration.memory import MemoryStore

pytest_plugins = ["ration.conformance.plugin"]


def pytest_ration_cases() -> list[Case]:
    return [store_case("stranger-memory", MemoryStore)]
