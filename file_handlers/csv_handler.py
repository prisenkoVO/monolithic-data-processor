"""CSV file loading logic."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd

from database import DatabaseManager
from utils import calculate_file_hash


def load_csv_file(
    file_path: str,
    config: dict[str, Any],
    logger: logging.Logger,
    db_manager: DatabaseManager,
) -> pd.DataFrame | None:
    """Load a CSV into a DataFrame with chunked reading."""
    try:
        logger.info("Loading CSV file: %s", file_path)
        encodings = ["utf-8", "latin1", "cp1252"]
        chunks = None
        for encoding in encodings:
            try:
                chunks = pd.read_csv(
                    file_path,
                    encoding=encoding,
                    chunksize=config["chunk_size"],
                )
                break
            except UnicodeDecodeError:
                continue

        if chunks is None:
            raise ValueError("Could not decode file with any known encoding")

        dataframe = pd.concat(list(chunks), ignore_index=True)
        path = Path(file_path)
        db_manager.log_raw_data(
            source_file=file_path,
            data_hash=calculate_file_hash(file_path),
            row_count=len(dataframe),
            file_size=path.stat().st_size,
        )
        return dataframe
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to load CSV %s: %s", file_path, exc)
        return None
