"""Hash utility helpers."""

from __future__ import annotations

import hashlib


def calculate_file_hash(file_path: str) -> str:
    """Calculate MD5 hash for a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as handle:
        for chunk in iter(lambda: handle.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()
