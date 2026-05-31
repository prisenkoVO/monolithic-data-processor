"""Visualization generation module."""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


def generate_visualizations(dataframe: pd.DataFrame, output_dir: str, logger: logging.Logger) -> None:
    """Generate summary visualization assets for the dataset."""
    try:
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        plt.style.use("seaborn-v0_8")

        numeric_df = dataframe.select_dtypes(include=[np.number])
        if len(numeric_df.columns) > 1:
            plt.figure(figsize=(12, 8))
            sns.heatmap(numeric_df.corr(), annot=True, cmap="coolwarm", center=0)
            plt.title("Feature Correlation Heatmap")
            plt.tight_layout()
            plt.savefig(output / "correlation_heatmap.png", dpi=300, bbox_inches="tight")
            plt.close()

        columns = numeric_df.columns[:6]
        if len(columns) > 0:
            fig, axes = plt.subplots(2, 3, figsize=(15, 10))
            for idx, column in enumerate(columns):
                axis = axes.ravel()[idx]
                axis.hist(dataframe[column].dropna(), bins=30, alpha=0.7)
                axis.set_title(f"Distribution of {column}")
                axis.set_xlabel(column)
                axis.set_ylabel("Frequency")
            plt.tight_layout()
            plt.savefig(output / "distributions.png", dpi=300, bbox_inches="tight")
            plt.close(fig)

            plt.figure(figsize=(12, 6))
            dataframe[columns].boxplot()
            plt.title("Box Plots for Outlier Detection")
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(output / "boxplots.png", dpi=300, bbox_inches="tight")
            plt.close()
    except Exception as exc:  # noqa: BLE001
        logger.error("Visualization generation failed: %s", exc)
