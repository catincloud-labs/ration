"""A stranger who believes a store is correct, and it is not.

The store is the package's `recycling` violator, which drops a key's version
when its value goes, registered under a stranger's name with nothing declared
violated. The suite must fail it on the tests that decide version-monotonic,
the ones it strict-xfails for the package's own `recycling`, and nowhere else.
"""

from __future__ import annotations

from stranger import store_case

from ration.conformance.support.backends import Case
from ration.conformance.violators import RecyclingStore

pytest_plugins = ["ration.conformance.plugin"]


def pytest_ration_cases() -> list[Case]:
    return [store_case("stranger-recycling", RecyclingStore)]
