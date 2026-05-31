"""Validation utilities."""

from __future__ import annotations

from pathlib import Path


VALID_EXTENSIONS = {".csv", ".json", ".xlsx", ".txt"}


def validate_file(file_path: str, max_file_size: int) -> bool:
    """Validate file existence, size and extension."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    file_size = path.stat().st_size
    if file_size > max_file_size:
        raise ValueError(f"File too large: {file_size} bytes")
    if file_size == 0:
        raise ValueError("File is empty")
    if path.suffix.lower() not in VALID_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {file_path}")
    return True
