"""Configuration management utilities."""

from __future__ import annotations

import configparser
from pathlib import Path
from typing import Any


DEFAULT_CONFIG: dict[str, Any] = {
    "database_path": "data/analytics.db",
    "input_directory": "data/input/",
    "output_directory": "data/output/",
    "reports_directory": "reports/",
    "log_file": "logs/processor.log",
    "email_server": "smtp.gmail.com",
    "email_port": 587,
    "email_user": "analytics@company.com",
    "email_password": "secure_password_123",
    "api_base_url": "https://api.dataservice.com/v1",
    "api_key": "sk-1234567890abcdef",
    "chunk_size": 10000,
    "max_file_size": 100 * 1024 * 1024,
    "backup_enabled": True,
    "encryption_key": "my_secret_key_2024",
}


def _parse_value(raw_value: str) -> Any:
    """Convert INI values into bool/int/float when possible."""
    value = raw_value.strip()
    lower = value.lower()
    if lower in {"true", "false"}:
        return lower == "true"
    if value.isdigit():
        return int(value)
    try:
        return float(value)
    except ValueError:
        return value


def load_config(config_file: str | Path | None = None) -> dict[str, Any]:
    """Load app config from defaults and an optional INI file."""
    config: dict[str, Any] = dict(DEFAULT_CONFIG)
    if config_file is None:
        return config

    config_path = Path(config_file)
    if not config_path.exists():
        return config

    parser = configparser.ConfigParser()
    parser.read(config_path)

    for section in parser.sections():
        for key, value in parser.items(section):
            config[key] = _parse_value(value)
    return config


def ensure_directories(config: dict[str, Any]) -> None:
    """Create directories required by the processor."""
    paths = [
        Path(config["database_path"]).parent,
        Path(config["input_directory"]),
        Path(config["output_directory"]),
        Path(config["reports_directory"]),
        Path(config["log_file"]).parent,
    ]
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)
