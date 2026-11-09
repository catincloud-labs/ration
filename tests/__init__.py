"""This repository's own tests, and its caller of the suite the package ships.

A suite that cannot reject is not a suite. Every property in
`src/ration/conformance/` ships alongside an implementation in
`src/ration/conformance/violators.py` or `frame_violators.py` that breaks
exactly that property and is expected to fail it. What is here holds this
repository's cases (`cases.py`, which the root `conftest.py` hands that suite
through its plugin), checks that the pairing is complete in both directions
(`test_the_suite_discriminates.py`), and tests this repository's own modules.
"""
