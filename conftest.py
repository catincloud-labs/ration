"""This repository's registries, handed to the suite the package ships.

The conformance suite, its violators, and the mechanism that makes a passing
violator a failure are `ration.conformance`; the mechanism is the suite's own
`src/ration/conformance/conftest.py`. What this file adds is the one choice the
package leaves to its caller: which cases a run judges. Here that is every
store in `tests/cases.py` and every frame codec the package defines.

It sits at the repository root rather than in `tests/` so that pytest loads it
for every path under the root: a run of one conformance module or one node id,
as the README and the design page cite them, is handed the same cases as a run
of everything.
"""

from __future__ import annotations

import pytest

from ration.conformance.support.codecs import CODECS
from ration.conformance.support.registry import register
from tests.cases import CASES


def pytest_configure(config: pytest.Config) -> None:
    register(backend=CASES, codec=CODECS)
