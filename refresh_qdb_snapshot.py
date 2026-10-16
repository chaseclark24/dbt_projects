"""Refresh stable dbt copies of the QDB and video-analytics SQLite databases.

Source locations come from environment variables so the script works on any
machine without edits:

    QDB_BACKUP_DIR     folder containing quantumdb_YYYY-MM-DD_HHMMSS.sqlite backups
    QDB_VIDEO_SOURCE   path to the live youtube.db analytics database

Each variable falls back to the original author's local path when unset.
"""

from __future__ import annotations

import ctypes
import os
import re
import sqlite3
import sys
import tempfile
from contextlib import closing
from ctypes import wintypes
from datetime import datetime, timedelta
from pathlib import Path


DBT_DIR = Path(__file__).resolve().parent
BACKUP_DIR = Path(os.environ.get("QDB_BACKUP_DIR", r"D:\qdb backups"))
VIDEO_SOURCE = Path(
    os.environ.get(
        "QDB_VIDEO_SOURCE",
        str(Path.home() / "OneDrive" / "Documents" / "qdb_video" / "analytics" / "youtube.db"),
    )
)
LOG = DBT_DIR / "logs" / "refresh-qdb-snapshot.log"
BACKUP_NAME = re.compile(r"quantumdb_(\d{4}-\d{2}-\d{2})_(\d{6})\.sqlite$")


def log(message: str) -> None:
    line = f"{datetime.now().astimezone().isoformat(timespec='seconds')} {message}"
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    print(line, flush=True)


def latest_completed_backup() -> Path:
    now = datetime.now()
    candidates: list[tuple[datetime, Path]] = []
    for path in BACKUP_DIR.glob("quantumdb_*.sqlite"):
        match = BACKUP_NAME.fullmatch(path.name)
        if not match or match.group(1) != now.date().isoformat():
            continue
        stamp = datetime.strptime("".join(match.groups()), "%Y-%m-%d%H%M%S")
        if stamp > now:
            continue
        wal = Path(str(path) + "-wal")
        shm = Path(str(path) + "-shm")
        if not wal.is_file() or not shm.is_file() or path.stat().st_size < 1_000_000:
            continue
        # SQLite readers may touch the shared-memory file. The main file and
        # WAL are the parts whose modification times show backup completion.
        if max(path.stat().st_mtime, wal.stat().st_mtime) > (
            now - timedelta(minutes=2)
        ).timestamp():
            continue
        candidates.append((stamp, path))
    if not candidates:
        raise RuntimeError(f"No completed backup dated {now.date()} found in {BACKUP_DIR}")
    return max(candidates)[1]


def check_database(connection: sqlite3.Connection) -> None:
    result = connection.execute("PRAGMA quick_check").fetchone()
    if result is None or result[0] != "ok":
        raise RuntimeError(f"SQLite quick_check failed: {result}")


def stage_snapshot(source: Path, destination: Path) -> Path:
    if not source.is_file():
        raise FileNotFoundError(source)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.stem}-refresh-", suffix=destination.suffix, dir=DBT_DIR
    )
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        # The backup API reads committed WAL transactions from QDB and takes
        # one consistent snapshot even when the video scraper is writing.
        with closing(sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)) as input_db:
            check_database(input_db)
            with closing(sqlite3.connect(temporary)) as output_db:
                input_db.backup(output_db)
                mode = output_db.execute("PRAGMA journal_mode=DELETE").fetchone()
                if mode is None or mode[0] != "delete":
                    raise RuntimeError(f"Could not make standalone SQLite file: {mode}")
                check_database(output_db)
        return temporary
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def ensure_destination_closed(destination: Path) -> None:
    """Fail before replacement if DBeaver or another program holds this file."""
    wal = Path(str(destination) + "-wal")
    if wal.exists() and wal.stat().st_size:
        raise RuntimeError(f"Destination has uncheckpointed WAL data: {wal}")
    if not destination.exists():
        return
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
        wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
    ]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    handle = kernel.CreateFileW(str(destination), 0x80000000, 0, None, 3, 0, None)
    if handle == ctypes.c_void_p(-1).value:
        code = ctypes.get_last_error()
        raise OSError(code, f"Cannot replace open destination {destination}")
    kernel.CloseHandle(handle)


def refresh() -> None:
    sources = [
        (latest_completed_backup(), DBT_DIR / "quantumdb.sqlite"),
        (VIDEO_SOURCE, DBT_DIR / "youtube.db"),
    ]
    staged: list[tuple[Path, Path]] = []
    try:
        for source, destination in sources:
            log(f"Staging {source} -> {destination}")
            staged.append((stage_snapshot(source, destination), destination))
        for _, destination in staged:
            ensure_destination_closed(destination)
        for temporary, destination in staged:
            # Old zero-length WAL and SHM files belong to the previous copy.
            for suffix in ("-wal", "-shm"):
                Path(str(destination) + suffix).unlink(missing_ok=True)
            os.replace(temporary, destination)
            log(f"Refreshed {destination} ({destination.stat().st_size:,} bytes)")
    finally:
        for temporary, _ in staged:
            temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    try:
        refresh()
    except Exception as exc:
        log(f"FAILED: {exc}")
        print(f"Snapshot refresh failed: {exc}", file=sys.stderr)
        sys.exit(1)
