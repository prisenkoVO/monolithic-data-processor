"""Data export utilities."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def export_data(dataframe: pd.DataFrame, output_path: str, format_type: str = "csv") -> None:
    """Export a DataFrame to a supported format."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    format_lower = format_type.lower()
    if format_lower == "csv":
        dataframe.to_csv(output, index=False)
    elif format_lower == "json":
        dataframe.to_json(output, orient="records", indent=2)
    elif format_lower == "xlsx":
        dataframe.to_excel(output, index=False)
    elif format_lower == "parquet":
        dataframe.to_parquet(output, index=False)
    else:
        raise ValueError(f"Unsupported export format: {format_type}")
