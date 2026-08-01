from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass
import json
from pathlib import Path
import re
import sqlite3
from typing import Any, Mapping
from uuid import UUID


class JournalError(RuntimeError):
    """Base class for local PCCC journal failures."""


class JournalConflict(JournalError):
    """The same job identity was reused with different immutable input."""


class JournalStateError(JournalError):
    """A local state transition was not legal."""


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
TERMINAL_LOCAL_STATES = frozenset(
    {"COMPLETE", "FAILED", "CANCELLED"}
)
ALL_LOCAL_STATES = frozenset(
    {"RECEIVED", "EFFECT_STARTED", *TERMINAL_LOCAL_STATES}
)
MAX_RECEIPT_BYTES = 1024 * 1024


@dataclass(frozen=True)
class LocalJob:
    job_id: str
    immutable_digest: str
    state: str
    receipt: dict[str, Any] | None
    created_at: str
    updated_at: str


class JobJournal:
    """Durable local idempotency journal.

    An EFFECT_STARTED row is never automatically replayed. Recovery code must
    reconcile control-plane state and operation-specific evidence first.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.path,
            timeout=10,
            isolation_level=None,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = FULL")
        connection.execute("PRAGMA busy_timeout = 10000")
        return connection

    def _initialize(self) -> None:
        with closing(self._connect()) as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS pccc_local_meta (
                    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                    schema_version TEXT NOT NULL
                );
                INSERT INTO pccc_local_meta(singleton, schema_version)
                VALUES (1, 'VERA_PCCC_LOCAL_JOURNAL_V1')
                ON CONFLICT(singleton) DO NOTHING;
                CREATE TABLE IF NOT EXISTS pccc_local_jobs (
                    job_id TEXT PRIMARY KEY,
                    immutable_digest TEXT NOT NULL CHECK (
                        length(immutable_digest) = 64
                        AND immutable_digest NOT GLOB '*[^0-9a-f]*'
                    ),
                    state TEXT NOT NULL CHECK (
                        state IN (
                            'RECEIVED',
                            'EFFECT_STARTED',
                            'COMPLETE',
                            'FAILED',
                            'CANCELLED'
                        )
                    ),
                    receipt_json TEXT,
                    created_at TEXT NOT NULL DEFAULT (
                        strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
                    ),
                    updated_at TEXT NOT NULL DEFAULT (
                        strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
                    ),
                    CHECK (
                        (
                            state IN ('COMPLETE', 'FAILED', 'CANCELLED')
                            AND receipt_json IS NOT NULL
                        )
                        OR
                        (
                            state IN ('RECEIVED', 'EFFECT_STARTED')
                            AND receipt_json IS NULL
                        )
                    )
                );
                """
            )
            row = connection.execute(
                "SELECT schema_version FROM pccc_local_meta "
                "WHERE singleton = 1"
            ).fetchone()
            if (
                row is None
                or row["schema_version"]
                != "VERA_PCCC_LOCAL_JOURNAL_V1"
            ):
                raise JournalError("unsupported local journal schema")

    @staticmethod
    def _identity(
        job_id: str,
        immutable_digest: str,
    ) -> tuple[str, str]:
        try:
            canonical_job_id = str(UUID(job_id))
        except (TypeError, ValueError) as exc:
            raise JournalError(
                "job_id must be a canonical UUID"
            ) from exc
        if (
            not isinstance(immutable_digest, str)
            or not _SHA256.fullmatch(immutable_digest)
        ):
            raise JournalError(
                "immutable_digest must be lowercase SHA-256 hex"
            )
        return canonical_job_id, immutable_digest

    @staticmethod
    def _row(row: sqlite3.Row) -> LocalJob:
        receipt = (
            None
            if row["receipt_json"] is None
            else json.loads(row["receipt_json"])
        )
        return LocalJob(
            job_id=row["job_id"],
            immutable_digest=row["immutable_digest"],
            state=row["state"],
            receipt=receipt,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def begin(self, job_id: str, immutable_digest: str) -> LocalJob:
        job_id, immutable_digest = self._identity(
            job_id,
            immutable_digest,
        )
        with closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM pccc_local_jobs WHERE job_id = ?",
                (job_id,),
            ).fetchone()
            if row is None:
                connection.execute(
                    "INSERT INTO pccc_local_jobs("
                    "job_id, immutable_digest, state"
                    ") VALUES (?, ?, 'RECEIVED')",
                    (job_id, immutable_digest),
                )
                row = connection.execute(
                    "SELECT * FROM pccc_local_jobs WHERE job_id = ?",
                    (job_id,),
                ).fetchone()
            elif row["immutable_digest"] != immutable_digest:
                connection.execute("ROLLBACK")
                raise JournalConflict(
                    "job_id reused with changed immutable digest"
                )
            connection.execute("COMMIT")
            assert row is not None
            return self._row(row)

    def get(self, job_id: str) -> LocalJob | None:
        try:
            job_id = str(UUID(job_id))
        except (TypeError, ValueError) as exc:
            raise JournalError(
                "job_id must be a canonical UUID"
            ) from exc
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT * FROM pccc_local_jobs WHERE job_id = ?",
                (job_id,),
            ).fetchone()
            return None if row is None else self._row(row)

    def mark_effect_started(
        self,
        job_id: str,
        immutable_digest: str,
    ) -> LocalJob:
        job_id, immutable_digest = self._identity(
            job_id,
            immutable_digest,
        )
        with closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM pccc_local_jobs WHERE job_id = ?",
                (job_id,),
            ).fetchone()
            if row is None:
                connection.execute("ROLLBACK")
                raise JournalStateError(
                    "job must be journaled before effect"
                )
            if row["immutable_digest"] != immutable_digest:
                connection.execute("ROLLBACK")
                raise JournalConflict(
                    "job_id reused with changed immutable digest"
                )
            if row["state"] == "RECEIVED":
                connection.execute(
                    "UPDATE pccc_local_jobs SET "
                    "state = 'EFFECT_STARTED', "
                    "updated_at = strftime("
                    "'%Y-%m-%dT%H:%M:%SZ', 'now'"
                    ") WHERE job_id = ?",
                    (job_id,),
                )
            elif row["state"] != "EFFECT_STARTED":
                connection.execute("ROLLBACK")
                raise JournalStateError(
                    f"cannot start effect from {row['state']}"
                )
            row = connection.execute(
                "SELECT * FROM pccc_local_jobs WHERE job_id = ?",
                (job_id,),
            ).fetchone()
            connection.execute("COMMIT")
            assert row is not None
            return self._row(row)

    def record_terminal(
        self,
        job_id: str,
        immutable_digest: str,
        state: str,
        receipt: Mapping[str, Any],
    ) -> LocalJob:
        job_id, immutable_digest = self._identity(
            job_id,
            immutable_digest,
        )
        if state not in TERMINAL_LOCAL_STATES:
            raise JournalStateError("state must be terminal")
        if not isinstance(receipt, Mapping):
            raise JournalError("receipt must be an object")
        try:
            receipt_json = json.dumps(
                dict(receipt),
                allow_nan=False,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
        except (TypeError, ValueError) as exc:
            raise JournalError(
                "receipt is not canonical JSON"
            ) from exc
        if len(receipt_json.encode("utf-8")) > MAX_RECEIPT_BYTES:
            raise JournalError(
                "receipt exceeds local journal size limit"
            )

        with closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM pccc_local_jobs WHERE job_id = ?",
                (job_id,),
            ).fetchone()
            if row is None:
                connection.execute("ROLLBACK")
                raise JournalStateError(
                    "job must be journaled before terminal"
                )
            if row["immutable_digest"] != immutable_digest:
                connection.execute("ROLLBACK")
                raise JournalConflict(
                    "job_id reused with changed immutable digest"
                )
            if row["state"] in TERMINAL_LOCAL_STATES:
                if (
                    row["state"] == state
                    and row["receipt_json"] == receipt_json
                ):
                    connection.execute("COMMIT")
                    return self._row(row)
                connection.execute("ROLLBACK")
                raise JournalConflict(
                    "terminal result already exists and differs"
                )
            connection.execute(
                "UPDATE pccc_local_jobs SET "
                "state = ?, receipt_json = ?, "
                "updated_at = strftime("
                "'%Y-%m-%dT%H:%M:%SZ', 'now'"
                ") WHERE job_id = ?",
                (state, receipt_json, job_id),
            )
            row = connection.execute(
                "SELECT * FROM pccc_local_jobs WHERE job_id = ?",
                (job_id,),
            ).fetchone()
            connection.execute("COMMIT")
            assert row is not None
            return self._row(row)

    def recover_incomplete(self) -> tuple[LocalJob, ...]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT * FROM pccc_local_jobs "
                "WHERE state IN ('RECEIVED', 'EFFECT_STARTED') "
                "ORDER BY created_at, job_id"
            ).fetchall()
            return tuple(self._row(row) for row in rows)


__all__ = [
    "ALL_LOCAL_STATES",
    "JobJournal",
    "JournalConflict",
    "JournalError",
    "JournalStateError",
    "LocalJob",
    "MAX_RECEIPT_BYTES",
    "TERMINAL_LOCAL_STATES",
]
