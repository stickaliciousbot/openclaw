#!/usr/bin/env python3
"""Disposable SQLite acceleration for canonical journal idempotency.

This database never decides a proposal. Callers first verify and reconstruct the
canonical journal map, then rebuild this index whenever identity, schema, bytes,
or indexed head do not match that verified journal.
"""
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Mapping

PROGRESS_APPLICATION_ID = 0x43415031  # CAP1
PROGRESS_USER_VERSION = 1
PROGRESS_SCHEMA = "critical_apply.progressdb.v1"


class ProgressDBError(RuntimeError):
    pass


class ProgressDB:
    def __init__(self, path: Path):
        self.path = Path(path)

    def _discard(self) -> None:
        for suffix in ("", "-wal", "-shm"):
            try:
                (Path(str(self.path) + suffix)).unlink()
            except FileNotFoundError:
                pass

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.path, timeout=1.0)
        con.execute("PRAGMA busy_timeout=1000")
        return con

    @staticmethod
    def _head_matches(con: sqlite3.Connection, transaction_id: str, sequence: int, event_sha256: str) -> bool:
        rows = dict(con.execute("SELECT key,value FROM metadata"))
        return (
            rows.get("schema") == PROGRESS_SCHEMA
            and rows.get("transaction_id") == transaction_id
            and rows.get("head_sequence") == str(sequence)
            and rows.get("head_event_sha256") == event_sha256
            and con.execute("PRAGMA application_id").fetchone()[0] == PROGRESS_APPLICATION_ID
            and con.execute("PRAGMA user_version").fetchone()[0] == PROGRESS_USER_VERSION
            and con.execute("PRAGMA quick_check").fetchone()[0] == "ok"
        )

    @staticmethod
    def _canonical_rows(entries: Mapping[tuple[str, str], Mapping[str, Any]]) -> list[tuple[Any, ...]]:
        return sorted(
            (
                txid,
                event_id,
                str(item["proposal_sha256"]),
                int(item["sequence"]),
                str(item["event_sha256"]),
                json.dumps(item["ack"], sort_keys=True, separators=(",", ":")),
            )
            for (txid, event_id), item in entries.items()
        )

    @classmethod
    def _content_matches(cls, con: sqlite3.Connection, entries: Mapping[tuple[str, str], Mapping[str, Any]]) -> bool:
        actual = con.execute(
            "SELECT transaction_id,event_id,proposal_sha256,sequence,event_sha256,ack_json "
            "FROM idempotency ORDER BY transaction_id,event_id"
        ).fetchall()
        return actual == cls._canonical_rows(entries)

    def rebuild(
        self,
        *,
        transaction_id: str,
        head_sequence: int,
        head_event_sha256: str,
        entries: Mapping[tuple[str, str], Mapping[str, Any]],
    ) -> None:
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        tmp = self.path.with_name(self.path.name + f".rebuild-{os.getpid()}-{os.urandom(8).hex()}")
        con = sqlite3.connect(tmp, timeout=1.0)
        con.execute("PRAGMA busy_timeout=1000")
        try:
            con.executescript(
                """
                PRAGMA journal_mode=DELETE;
                PRAGMA synchronous=FULL;
                CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL) WITHOUT ROWID;
                CREATE TABLE idempotency(
                    transaction_id TEXT NOT NULL,
                    event_id TEXT NOT NULL,
                    proposal_sha256 TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    event_sha256 TEXT NOT NULL,
                    ack_json TEXT NOT NULL,
                    PRIMARY KEY(transaction_id,event_id)
                ) WITHOUT ROWID;
                """
            )
            con.execute(f"PRAGMA application_id={PROGRESS_APPLICATION_ID}")
            con.execute(f"PRAGMA user_version={PROGRESS_USER_VERSION}")
            con.execute("BEGIN IMMEDIATE")
            con.executemany(
                "INSERT INTO metadata(key,value) VALUES(?,?)",
                (
                    ("schema", PROGRESS_SCHEMA),
                    ("transaction_id", transaction_id),
                    ("head_sequence", str(head_sequence)),
                    ("head_event_sha256", head_event_sha256),
                ),
            )
            for txid, event_id, proposal_sha, sequence, event_sha, ack_json in self._canonical_rows(entries):
                con.execute(
                    "INSERT INTO idempotency VALUES(?,?,?,?,?,?)",
                    (txid, event_id, proposal_sha, sequence, event_sha, ack_json),
                )
            con.commit()
            con.close()
            os.chmod(tmp, 0o600)
            fd = os.open(tmp, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
            for suffix in ("-wal", "-shm"):
                try:
                    Path(str(self.path) + suffix).unlink()
                except FileNotFoundError:
                    pass
            os.replace(tmp, self.path)
            parent_fd = os.open(self.path.parent, os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0))
            try:
                os.fsync(parent_fd)
            finally:
                os.close(parent_fd)
        except Exception:
            try:
                con.close()
            except Exception:
                pass
            try:
                tmp.unlink()
            except FileNotFoundError:
                pass
            raise

    def ensure_current(
        self,
        *,
        transaction_id: str,
        head_sequence: int,
        head_event_sha256: str,
        canonical_entries: Mapping[tuple[str, str], Mapping[str, Any]],
    ) -> bool:
        """Return True only when an existing valid index was reused."""
        reused = False
        if self.path.exists() and not self.path.is_symlink():
            try:
                con = self._connect()
                try:
                    reused = self._head_matches(con, transaction_id, head_sequence, head_event_sha256)
                    if reused:
                        reused = self._content_matches(con, canonical_entries)
                finally:
                    con.close()
            except (sqlite3.Error, OSError, KeyError, TypeError):
                reused = False
        if not reused:
            self.rebuild(
                transaction_id=transaction_id,
                head_sequence=head_sequence,
                head_event_sha256=head_event_sha256,
                entries=canonical_entries,
            )
        return reused

    def lookup_if_current(
        self, *, transaction_id: str, event_id: str, head_sequence: int, head_event_sha256: str
    ) -> Mapping[str, Any] | None:
        """Acceleration-only lookup. A head mismatch raises; it never decides."""
        con = self._connect()
        try:
            if not self._head_matches(con, transaction_id, head_sequence, head_event_sha256):
                raise ProgressDBError("PROGRESSDB_HEAD_NOT_VERIFIED")
            row = con.execute(
                "SELECT proposal_sha256,sequence,event_sha256,ack_json FROM idempotency WHERE transaction_id=? AND event_id=?",
                (transaction_id, event_id),
            ).fetchone()
            if row is None:
                return None
            return {
                "proposal_sha256": row[0],
                "sequence": row[1],
                "event_sha256": row[2],
                "ack": json.loads(row[3]),
            }
        finally:
            con.close()
