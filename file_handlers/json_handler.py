"""JSON file loading logic."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from database import DatabaseManager
from utils import calculate_file_hash


def load_json_file(
    file_path: str,
    config: dict[str, Any],
    logger: logging.Logger,
    db_manager: DatabaseManager,
) -> pd.DataFrame | None:
    """Load JSON files into DataFrame."""
    try:
        logger.info("Loading JSON file: %s", file_path)
        with open(file_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)

        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            dataframe = pd.DataFrame(data)
        elif isinstance(data, dict):
            dataframe = pd.DataFrame([data])
        else:
            raise ValueError("Unsupported JSON structure")

        path = Path(file_path)
        db_manager.log_raw_data(
            source_file=file_path,
            data_hash=calculate_file_hash(file_path),
            row_count=len(dataframe),
            file_size=path.stat().st_size,
        )
        return dataframe
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to load JSON %s: %s", file_path, exc)
        return None
