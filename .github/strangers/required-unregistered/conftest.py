"""A stranger whose store is registered only where its server is named.

The shape this repository gives Postgres: a run that names no server registers
no case. The arm runs with `--ration-require stranger-store` and without
`STRANGER_STORE_ADDRESS`, as a CI job that lost the variable would. It also
requires `correct`, a case of the package's own: every run judges that one,
and it must not satisfy a switch that is about the caller's store.
"""

from __future__ import annotations

import os

from stranger import store_case

from ration.conformance.support.backends import Case
from ration.memory import MemoryStore

pytest_plugins = ["ration.conformance.plugin"]


def pytest_ration_cases() -> list[Case]:
    if not os.environ.get("STRANGER_STORE_ADDRESS", "").strip():
        return []
    return [store_case("stranger-store", MemoryStore)]
