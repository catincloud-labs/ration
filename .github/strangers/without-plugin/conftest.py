"""A stranger who answers the plugin's hook and never enables the plugin.

There is no `pytest_plugins` line here, and the package declares no entry
point, so nothing loads `ration.conformance.plugin`. pytest then knows no
hook by this name and refuses the run, and the suite, collected with
`--pyargs ration.conformance`, finds its registries empty. A package that
enabled the plugin on install would let this run judge the store and pass.
"""

from __future__ import annotations

from stranger import store_case

from ration.conformance.support.backends import Case
from ration.memory import MemoryStore


def pytest_ration_cases() -> list[Case]:
    return [store_case("stranger-memory", MemoryStore)]
