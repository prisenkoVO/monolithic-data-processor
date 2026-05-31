"""File handler dispatching by extension."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd

from database import DatabaseManager

from .csv_handler import load_csv_file
from .json_handler import load_json_file


def load_file(
    file_path: str,
    config: dict[str, Any],
    logger: logging.Logger,
    db_manager: DatabaseManager,
) -> pd.DataFrame | None:
    """Load input file using the proper handler for its extension."""
    extension = Path(file_path).suffix.lower()
    if extension == ".csv":
        return load_csv_file(file_path, config, logger, db_manager)
    if extension == ".json":
        return load_json_file(file_path, config, logger, db_manager)
    logger.warning("Unsupported file type: %s", file_path)
    return None
