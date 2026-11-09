"""Stores that are correct on purpose, in a way no other registered store is.

`tests/violators.py` holds the known-negatives: each store there is wrong about
one property and must fail it. This module holds a known-positive of a narrower
kind. Each store here uses latitude the contract grants and the other correct
stores happen not to use, so a test that quietly stopped granting it would turn
red here and nowhere else.

That is the other half of the rule in `AGENTS.md`. A violator shows that an
assertion can reject; a store here shows that a relaxed assertion is relaxed on
purpose. Without one, tightening the assertion back is a change no registered
store can see, and a permission the suite cannot see being withdrawn is one the
suite does not test.

A store here declares no violated property in `backends.py`, so it runs the
whole conformance suite and every test that filters the registry for correct
cases, and it must pass them all.
"""

from __future__ import annotations

from collections.abc import Callable

from ration.contract import ABSENT, Applied, Conflict, Outcome, Record
from ration.memory import MemoryStore

__all__ = ["PreviousVersionStore"]


class PreviousVersionStore(MemoryStore):
    """Correct. A conflict carries the version the key held before its current one.

    `Conflict` promises a version the key has held and not its current one, and
    `PostgresStore` uses that latitude when two writers race. This store uses it
    on every refusal of a key that has been written, racing or not: the version
    such a refusal reports is always one the key held and never the one it
    holds now.
    Before the first write the key has held only `ABSENT`, so that is the answer.

    The previous version is recorded at the moment a write lands rather than
    computed as one less than the current version. That keeps the claim true by
    construction instead of by the counter's step size.

    Every other path is `MemoryStore`'s: the comparison, the refusal without a
    write, the version counter, expiry and the seam the suite parks in.
    """

    def __init__(self, clock: Callable[[], float] | None = None) -> None:
        super().__init__(clock)
        #: The version each key held immediately before its current one. A key
        #: absent from this map has never been written.
        self._previous: dict[str, int] = {}

    def compare_and_set(
        self,
        key: str,
        expected_version: int,
        record: Record | None,
        *,
        ttl: float | None = None,
    ) -> Outcome:
        self._staged()
        with self._lock:
            reading = self._read_locked(key)
            if reading.version != expected_version:
                return Conflict(self._previous.get(key, ABSENT))
            return self._commit_locked(key, record, ttl)

    def _commit_locked(
        self, key: str, record: Record | None, ttl: float | None
    ) -> Applied:
        self._previous[key] = self._versions.get(key, ABSENT)
        return super()._commit_locked(key, record, ttl)
