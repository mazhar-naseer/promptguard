"""
Simple SQLite backup helper for PromptGuard.

Usage:
    python scripts/backup_db.py [source_db_path] [backup_dir]

Defaults to app/data/promptguard.db -> app/data/backups/
Run this on a schedule (cron, systemd timer, or your platform's
scheduled-job feature) since SQLite has no built-in replication.
"""

import shutil
import sqlite3
import sys
import time
from pathlib import Path

DEFAULT_SOURCE = "app/data/promptguard.db"
DEFAULT_BACKUP_DIR = "app/data/backups"
KEEP_LAST_N = 14


def backup(source_path: str, backup_dir: str) -> Path:
    source = Path(source_path)
    if not source.exists():
        raise FileNotFoundError(f"No database found at {source}")

    backup_folder = Path(backup_dir)
    backup_folder.mkdir(parents=True, exist_ok=True)

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    dest = backup_folder / f"promptguard-{timestamp}.db"

    src_conn = sqlite3.connect(str(source))
    dest_conn = sqlite3.connect(str(dest))
    with dest_conn:
        src_conn.backup(dest_conn)
    src_conn.close()
    dest_conn.close()

    _prune_old_backups(backup_folder)
    return dest


def _prune_old_backups(backup_folder: Path) -> None:
    backups = sorted(backup_folder.glob("promptguard-*.db"))
    while len(backups) > KEEP_LAST_N:
        oldest = backups.pop(0)
        oldest.unlink()


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SOURCE
    dst = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_BACKUP_DIR
    result = backup(src, dst)
    print(f"Backed up to {result}")
