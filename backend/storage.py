from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple, Iterable
import sqlite3


class MappingStore:
    """Abstract store for ORIGINAL -> TOKEN mapping."""

    def load(self) -> Tuple[Dict[str, str], Dict[str, str]]:
        """Return (forward, reverse) where:
        - forward: ORIGINAL -> TOKEN
        - reverse: TOKEN   -> ORIGINAL
        """
        raise NotImplementedError

    def save(self, forward: Dict[str, str]) -> None:
        """Persist ORIGINAL -> TOKEN mapping."""
        raise NotImplementedError


# -------------------------------
# File-backed store (current default)
# -------------------------------
class FileMappingStore(MappingStore):
    """
    Plain-text mapping file with lines "TOKEN = ORIGINAL".
    Stable, human-friendly, CLI-first.
    """

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    @staticmethod
    def _parse_lines(lines: Iterable[str]) -> Tuple[Dict[str, str], Dict[str, str]]:
        reverse: Dict[str, str] = {}
        forward: Dict[str, str] = {}
        for line in lines:
            line = line.strip()
            if not line or "=" not in line:
                continue
            token, original = map(str.strip, line.split("=", 1))
            if token and original:
                reverse[token] = original
                forward[original] = token
        return forward, reverse

    def load(self) -> Tuple[Dict[str, str], Dict[str, str]]:
        if not self.path.exists():
            return {}, {}
        content = self.path.read_text(encoding="utf-8").splitlines()
        return self._parse_lines(content)

    def save(self, forward: Dict[str, str]) -> None:
        # Persist deterministically: sort by ORIGINAL (case-insensitive)
        items = sorted(
            ((tok, orig) for orig, tok in forward.items()), key=lambda x: x[1].lower()
        )
        with self.path.open("w", encoding="utf-8") as f:
            for tok, orig in items:
                f.write(f"{tok} = {orig}\n")


# -------------------------------
# SQLite-backed store (container mode)
# -------------------------------
class SqliteMappingStore(MappingStore):
    """
    Lightweight transactional store for container runtimes.
    Schema:
      mapping(original TEXT PRIMARY KEY, token TEXT NOT NULL)
    """

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self._init_db()

    # --- internals ---
    def _connect(self) -> sqlite3.Connection:
        # isolation_level=None = autocommit off by default -> we commit explicitly
        con = sqlite3.connect(self.db_path)
        # Ensure consistent text handling
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA synchronous=NORMAL")
        return con

    def _init_db(self) -> None:
        con = self._connect()
        try:
            con.execute(
                "CREATE TABLE IF NOT EXISTS mapping ("
                "  original TEXT PRIMARY KEY,"
                "  token    TEXT NOT NULL)"
            )
            con.commit()
        finally:
            con.close()

    # --- public API ---
    def load(self) -> Tuple[Dict[str, str], Dict[str, str]]:
        con = self._connect()
        try:
            cur = con.execute("SELECT original, token FROM mapping")
            rows = cur.fetchall()
        finally:
            con.close()
        forward = {orig: tok for (orig, tok) in rows}
        reverse = {tok: orig for (orig, tok) in rows}
        return forward, reverse

    def save(self, forward: Dict[str, str]) -> None:
        if not forward:
            return
        con = self._connect()
        try:
            con.executemany(
                "INSERT INTO mapping(original, token) VALUES(?, ?) "
                "ON CONFLICT(original) DO UPDATE SET token=excluded.token",
                [(orig, tok) for orig, tok in forward.items()],
            )
            con.commit()
        finally:
            con.close()

    # --- migration helper ---
    def migrate_from_file(self, txt_path: Path) -> int:
        """
        Import legacy mapping from text file (TOKEN = ORIGINAL) exactly once.
        Only runs if DB is currently empty. Returns number of imported rows.
        """
        txt = Path(txt_path)
        if not txt.exists():
            return 0

        # If DB already has rows, do not touch it.
        forward_db, _ = self.load()
        if forward_db:
            return 0

        # Parse file using same rules as FileMappingStore
        content = txt.read_text(encoding="utf-8").splitlines()
        forward_file, _ = FileMappingStore._parse_lines(content)
        if not forward_file:
            return 0

        # Bulk insert
        self.save(forward_file)
        return len(forward_file)
