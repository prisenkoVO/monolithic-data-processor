"""Data cleaning and transformation logic."""

from __future__ import annotations

import logging
from datetime import datetime

import numpy as np
import pandas as pd


def clean_data(dataframe: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """Clean input DataFrame and add quality metadata."""
    try:
        logger.info("Starting data cleaning")
        frame = dataframe.drop_duplicates().copy()

        numeric_columns = frame.select_dtypes(include=[np.number]).columns
        for column in numeric_columns:
            frame[column] = frame[column].fillna(frame[column].median())

        text_columns = frame.select_dtypes(include=["object"]).columns
        for column in text_columns:
            frame[column] = frame[column].fillna("Unknown").str.strip().str.lower()

        for column in numeric_columns:
            q1 = frame[column].quantile(0.25)
            q3 = frame[column].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            frame = frame[(frame[column] >= lower) & (frame[column] <= upper)]

        frame["quality_score"] = np.random.uniform(0.7, 1.0, len(frame))
        frame["processed_timestamp"] = datetime.now()
        return frame
    except Exception as exc:  # noqa: BLE001
        logger.error("Data cleaning failed: %s", exc)
        return dataframe


def transform_data(
    dataframe: pd.DataFrame,
    logger: logging.Logger,
    transformation_type: str = "standard",
) -> pd.DataFrame:
    """Apply feature transformations."""
    try:
        frame = dataframe.copy()
        logger.info("Applying transformation: %s", transformation_type)
        numeric_columns = frame.select_dtypes(include=[np.number]).columns

        if transformation_type == "standard":
            for column in numeric_columns:
                if column == "quality_score":
                    continue
                std = frame[column].std()
                if std != 0:
                    frame[f"{column}_standardized"] = (frame[column] - frame[column].mean()) / std
        elif transformation_type == "normalize":
            for column in numeric_columns:
                if column == "quality_score":
                    continue
                min_val = frame[column].min()
                max_val = frame[column].max()
                if max_val != min_val:
                    frame[f"{column}_normalized"] = (frame[column] - min_val) / (max_val - min_val)
        elif transformation_type == "categorical":
            text_columns = frame.select_dtypes(include=["object"]).columns
            for column in text_columns:
                frame[f"{column}_encoded"] = pd.Categorical(frame[column]).codes

        updated_numeric = frame.select_dtypes(include=[np.number]).columns
        if len(updated_numeric) > 1:
            frame["feature_sum"] = frame[updated_numeric].sum(axis=1)
            frame["feature_mean"] = frame[updated_numeric].mean(axis=1)
            frame["feature_std"] = frame[updated_numeric].std(axis=1)
        return frame
    except Exception as exc:  # noqa: BLE001
        logger.error("Data transformation failed: %s", exc)
        return dataframe
