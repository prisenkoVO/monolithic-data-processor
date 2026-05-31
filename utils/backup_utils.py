"""Backup and cleanup utilities."""

from __future__ import annotations

import json
import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


def backup_data(config: dict[str, Any], logger: logging.Logger) -> str | None:
    """Create a filesystem backup for db, output and reports."""
    if not config.get("backup_enabled", False):
        return None

    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path("backups") / f"backup_{timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)

        db_path = Path(config["database_path"])
        shutil.copy2(db_path, backup_dir / "database_backup.db")

        output_dir = Path(config["output_directory"])
        if output_dir.exists():
            shutil.copytree(output_dir, backup_dir / "output", dirs_exist_ok=True)

        reports_dir = Path(config["reports_directory"])
        if reports_dir.exists():
            shutil.copytree(reports_dir, backup_dir / "reports", dirs_exist_ok=True)

        backup_info = {
            "timestamp": timestamp,
            "database_size": db_path.stat().st_size,
            "files_backed_up": len(list(backup_dir.iterdir())),
            "backup_size": sum(item.stat().st_size for item in backup_dir.iterdir() if item.is_file()),
        }
        (backup_dir / "backup_info.json").write_text(json.dumps(backup_info, indent=2))

        logger.info("Backup created: %s", backup_dir)
        return str(backup_dir)
    except Exception as exc:  # noqa: BLE001
        logger.error("Backup failed: %s", exc)
        return None


def cleanup_old_files(config: dict[str, Any], logger: logging.Logger, days_old: int = 30) -> None:
    """Remove files older than the provided threshold."""
    cutoff_date = datetime.now() - timedelta(days=days_old)
    for root in [config["output_directory"], config["reports_directory"]]:
        path = Path(root)
        if not path.exists():
            continue
        for file_path in path.rglob("*"):
            if not file_path.is_file():
                continue
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            if mtime < cutoff_date:
                file_path.unlink()
                logger.info("Deleted old file: %s", file_path)
