"""The violator that is a real store: `naive`'s defect, in Postgres.

Kept apart from `violators.py` because it is the one violator that needs a
driver. It subclasses `ration.postgres.PostgresStore`, which imports `psycopg`,
so importing it needs `psycopg` installed, and the rest of the suite does not.
A caller that registers it has a Postgres to point it at, and so has the driver;
a caller that does not never imports this module.
"""

from __future__ import annotations

from ration.contract import Applied, Conflict, Outcome, Record, Store
from ration.postgres import PostgresStore

__all__ = ["NaivePostgresStore"]


class NaivePostgresStore(PostgresStore):
    """Violates: `atomicity`. The same defect as `naive`, in a real store.

    This is the violator that matters most. Every other implementation in the
    suite is a fake this repository wrote to be caught, so without this one the
    suite would have shown it could reject **its own fakes** and nothing else,
    and a contract that cannot discriminate between real candidates has bought
    nothing.

    It is also the honest shape of the mistake. Nobody writes the naive version
    on purpose; they write `SELECT` and then `UPDATE` because that is how the
    operation reads in English, and every single-threaded test agrees with them.
    The version column is still there, still incrementing, and still meaning
    nothing, because no statement ever compares it.

    It has no in-process seam, so the deterministic stepper cannot reach it
    and skips. The threaded probe is the only instrument that decides it, which
    makes this the one case where the false-pass rate stated in
    `test_atomicity.py` carries a verdict on its own.
    """

    def compare_and_set(
        self,
        key: str,
        expected_version: int,
        record: Record | None,
        *,
        ttl: float | None = None,
    ) -> Outcome:
        reading = self.read(key)
        if reading.version != expected_version:
            return Conflict(reading.version)
        # A second statement, against a row that has been free to move since the
        # first one committed. `WHERE key = ...` and nothing else.
        row = self._execute(
            """
            INSERT INTO ration_keys (key, version, payload, token, expires_at)
            VALUES (%(key)s, 1, %(payload)s, %(token)s,
                    CASE WHEN %(ttl)s::double precision IS NULL THEN NULL
                         ELSE now() + make_interval(secs => %(ttl)s) END)
            ON CONFLICT (key) DO UPDATE
               SET version    = ration_keys.version + 1,
                   payload    = EXCLUDED.payload,
                   token      = EXCLUDED.token,
                   expires_at = EXCLUDED.expires_at
         RETURNING version
            """,
            {
                "key": key,
                "payload": record.payload if record is not None else None,
                "token": record.token if record is not None else None,
                "ttl": ttl,
            },
        ).fetchone()
        assert row is not None
        return Applied(row[0])
