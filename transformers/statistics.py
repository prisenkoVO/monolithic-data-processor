"""Statistics calculation helpers."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd


def calculate_statistics(dataframe: pd.DataFrame, logger: logging.Logger) -> dict[str, Any]:
    """Build dataset-wide statistics for reports."""
    try:
        stats: dict[str, Any] = {
            "total_rows": len(dataframe),
            "total_columns": len(dataframe.columns),
            "memory_usage": int(dataframe.memory_usage(deep=True).sum()),
        }

        numeric_columns = dataframe.select_dtypes(include=[np.number]).columns
        for column in numeric_columns:
            stats[f"{column}_mean"] = dataframe[column].mean()
            stats[f"{column}_median"] = dataframe[column].median()
            stats[f"{column}_std"] = dataframe[column].std()
            stats[f"{column}_min"] = dataframe[column].min()
            stats[f"{column}_max"] = dataframe[column].max()
            stats[f"{column}_null_count"] = int(dataframe[column].isnull().sum())

        text_columns = dataframe.select_dtypes(include=["object"]).columns
        for column in text_columns:
            mode = dataframe[column].mode()
            stats[f"{column}_unique_count"] = int(dataframe[column].nunique())
            stats[f"{column}_most_common"] = mode.iloc[0] if not mode.empty else "N/A"
            stats[f"{column}_null_count"] = int(dataframe[column].isnull().sum())

        quality = dataframe.get("quality_score", pd.Series([0.0], dtype=float))
        stats["overall_quality_score"] = float(quality.mean())
        denominator = len(dataframe) * len(dataframe.columns) or 1
        stats["completeness_ratio"] = 1 - (dataframe.isnull().sum().sum() / denominator)
        return stats
    except Exception as exc:  # noqa: BLE001
        logger.error("Statistics calculation failed: %s", exc)
        return {}
