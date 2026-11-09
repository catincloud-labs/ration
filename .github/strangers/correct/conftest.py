"""A stranger with a correct store, judged beside the package's own cases.

The store is `ration.memory.MemoryStore` on its own clock, registered under a
stranger's name. The arm runs with `--ration-require stranger-memory`, so its
green also shows the require switch admitting a case that was judged.
"""

from __future__ import annotations

from stranger import store_case

from ration.conformance.support.backends import Case
from ration.memory import MemoryStore

pytest_plugins = ["ration.conformance.plugin"]


def pytest_ration_cases() -> list[Case]:
    return [store_case("stranger-memory", MemoryStore)]
