"""The coordination contract, expressed as types.

This module is where the contract is stated, and the conformance suite under
`src/ration/conformance/` decides whether a backend implements it. The substrate
is a single key at a time, written by a compare-and-set that names a version,
and nothing more.

The operation comes first and carries no number. A `compare_and_set` writes
one key, and only when that key still holds the version the caller names;
checking the version and writing happen as one indivisible step; and a refused
write leaves the key untouched and says so. The suite judges the operation
under two property names, `compare-and-set` (in `test_compare_and_set.py`) and
`atomicity` (in `test_atomicity.py`).

Beyond the operation, four numbered properties hold. They carry numbers
because other modules here, and the suite, refer to them that way:

1. Each key's version only goes up, and no value is ever handed out twice for
   one key, deletion included.
2. The store decides expiry, by its own clock, at the moment it is asked.
3. A store that cannot be reached is a refusal, never a guess.
4. A write whose outcome was lost can be settled afterwards by a read.

Nothing beyond that is exposed here. A capability the contract refuses does
not turn up in this module merely because it would have been easy to add.

This file is a specification that no class in it implements, on purpose. An
interface written around a single implementation tends to describe that
implementation; one written around none describes only what is required.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Protocol

__all__ = [
    "ABSENT",
    "Ambiguous",
    "Applied",
    "Conflict",
    "Outcome",
    "Record",
    "Reading",
    "Resolution",
    "Store",
    "Unreachable",
    "resolve",
]


#: The version of a key that has never been written. Absence is a version, so
#: creation is not a special case: it is a compare-and-set against this one. A
#: backend that treats an absent key as "any expected version will do" has not
#: implemented the contract, it has implemented an upsert.
ABSENT = 0


@dataclass(frozen=True, slots=True)
class Record:
    """A value in the store, and the token of the caller who wrote it.

    The token is not decoration and is not optional. Property 4 makes an
    ambiguous write resolvable *by reading*, and reading can only answer the
    question if what comes back identifies who wrote it. A store that keeps the
    payload and discards the token has kept the part that is easy to replace.
    """

    payload: bytes
    token: str


@dataclass(frozen=True, slots=True)
class Reading:
    """What `read` returns: a version, and a record if the key holds one.

    A key that is absent, was deleted, or whose lease has expired all read the
    same way -- no record -- but each still reports the version the key has
    reached. Absence is a version.
    """

    version: int
    record: Record | None

    @property
    def present(self) -> bool:
        return self.record is not None


@dataclass(frozen=True, slots=True)
class Applied:
    """The write happened, and the key is now at this version."""

    version: int


@dataclass(frozen=True, slots=True)
class Conflict:
    """The write did not happen, because the key was not at the expected version.

    A conflict is an outcome, not an error: the caller asked a question and got
    an answer. It is reported without writing -- a store that reports a conflict
    and writes anyway has answered honestly and acted otherwise, which is worse
    than either alone.

    **`version` is some version this key has held at some point. It is not a
    promise about the key's current version, and under concurrency it is often
    not the current one.** `PostgresStore`, when it loses a race, hands back
    the version the caller started *from*, because the statement that decides
    the outcome and the statement that reports the version read one snapshot.
    With two updaters starting at version 1, the one that loses gets
    ``Conflict(1)`` and the key sits at 2; with two creators racing from
    absence, the one that loses gets ``Conflict(0)`` and the key sits at 1.

    That is permitted rather than merely tolerated. **The contract's demands
    on a conflict are two: nothing is written, and the version it carries is
    one the key really held.** The current version is not among them, since no
    consumer has needed it, and a promise made before anyone needs it is a
    guess about what they will need. Making the field exact would take a
    second round trip, or an ``ON CONFLICT DO UPDATE`` -- a statement that
    writes so that it can read, which the paragraph above forbids outright.

    So **a caller that needs the current version must read.** Treating this
    number as current is the mistake the field invites, which is why the
    warning lives here rather than only in the backend that revealed it.
    Strengthening the contract to require an exact version is a change to the
    contract itself, and would need a consumer that actually needs it.
    """

    version: int


Outcome = Applied | Conflict


class Unreachable(Exception):
    """The store could not be reached.

    Property 3: silence from the store grants nothing, and the caller must
    stop there. This is raised rather than returned on purpose -- an outcome
    can be ignored by a caller who only checks for the one it wanted, and
    refusing on failure only when each caller remembers to is a habit, not
    something the substrate holds.
    """


class Ambiguous(Exception):
    """A write whose outcome the caller never learned.

    Property 4: a `compare_and_set` that is lost after transmission has an
    outcome the caller has not seen, not an outcome that does not exist. The
    remedy is `resolve`, which reads. Guessing is not a remedy.
    """


class Store(Protocol):
    """The whole substrate. Two operations, and nothing else.

    The contract's refusals are load-bearing and are visible here as absences:
    no second key, no ordering, no watches, no queue, and no lock that
    outlives one call. Adding a method to this Protocol is a change to the contract
    itself, not a convenience.
    """

    def read(self, key: str) -> Reading:
        """Return the key's version, and its record if it holds one.

        Raises `Unreachable` if the store cannot be reached.
        """
        ...

    def compare_and_set(
        self,
        key: str,
        expected_version: int,
        record: Record | None,
        *,
        ttl: float | None = None,
    ) -> Outcome:
        """Write `record` only when the key still holds `expected_version`.

        Checking and writing are indivisible: no other write to the key
        lands between checking the version and writing, so two callers from one
        version cannot both apply. A key not at `expected_version` returns a
        `Conflict`, and nothing is written.

        A `record` of `None` deletes: the key becomes absent, and its version
        advances anyway, because property 1 says versions are never reused and
        deletion is the case it names.

        `ttl` is a duration, not a deadline, and that signature is property 2
        made structural. A caller cannot pass an expiry it computed, because
        there is nowhere to put one -- the store adds the duration to its own
        clock. Passing `None` means the value does not expire.

        Raises `Unreachable` if the store could not be reached, and `Ambiguous`
        if it was reached but the outcome was not learned.
        """
        ...


class Resolution(enum.Enum):
    """What a read can tell a caller about a write it did not see land."""

    #: The caller's token is in the store. The write applied.
    APPLIED = "applied"
    #: The key has not moved since the caller's expected version. It did not.
    NOT_APPLIED = "not-applied"
    #: The key moved, and someone else's token is there. Either the write never
    #: applied or it has already been overwritten -- and the caller does not
    #: hold the key either way, which is the question actually being asked.
    SUPERSEDED = "superseded"


def resolve(
    store: Store, key: str, token: str, expected_version: int
) -> Resolution:
    """Answer, by reading, what an `Ambiguous` write did.

    This is the remedy property 4 exists to make possible, and it is shipped as
    code rather than left to each caller so that a backend is judged against the
    real procedure. It needs both halves of the contract: the token says whether
    the value is ours, and the monotonic version says whether anything moved at
    all. Neither answers alone.

    **The version is tested before the token, and that order is the whole
    correctness of this function.** Token first goes wrong whenever the caller
    already holds the key it is writing. A lease renewing itself is exactly
    that: the previous grant left its token in the store, so if the token were
    checked first, a renewal whose reply went missing would come back
    `APPLIED` because of what the *earlier* write left there, and the holder
    would believe in time it was never given.

    **The token identifies a writer, not a write.** Those coincide only while a
    caller writes a key at most once, and a renewing lease or an advancing
    publisher writes it again and again; `test_ambiguity.py` reaches that case
    in `test_a_rewriters_lost_answer_is_resolved`. Property 1 is what closes
    it: every write advances the version, deletion included, so a key whose
    version has not moved off `expected_version` has had no write since,
    whatever token is sitting there.
    """
    reading = store.read(key)
    if reading.version == expected_version:
        # Nothing has been written by anyone -- not us, not a competitor. This
        # is decided before the token is consulted, because our own token may be
        # sitting there from a write that landed before the one being resolved.
        return Resolution.NOT_APPLIED
    if reading.record is not None and reading.record.token == token:
        return Resolution.APPLIED
    return Resolution.SUPERSEDED
