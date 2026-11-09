"""This repository's cases, handed to the suite the way any caller's are.

The conformance suite, its violators, and the mechanism that makes a passing
violator a failure are `ration.conformance`; the mechanism is the suite's own
`src/ration/conformance/conftest.py`. This file enables the plugin a stranger
enables, `ration.conformance.plugin`, and answers its one hook with every store
in `tests/cases.py`. The plugin registers the package's own cases and frame
codecs whatever a caller returns, and registers once a case returned again, so
the run judges `CASES` exactly, through the same way in as anyone else's store.

It sits at the repository root rather than in `tests/` so that pytest loads it
for every path under the root: a run of one conformance module or one node id,
as the README and the design page cite them, is handed the same cases as a run
of everything. pytest also reads `pytest_plugins` only from a conftest it loads
before configuring, which this one is.
"""

from __future__ import annotations

from ration.conformance.support.backends import Case
from tests.cases import CASES

pytest_plugins = ["ration.conformance.plugin"]


def pytest_ration_cases() -> list[Case]:
    return CASES
