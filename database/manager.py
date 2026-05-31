"""SQLite database management module."""

from __future__ import annotations

import logging
import os
import sqlite3
from typing import Any


class DatabaseManager:
    """Handle DB setup and persistence operations."""

    def __init__(self, database_path: str, logger: logging.Logger):
        self.database_path = database_path
        self.logger = logger
        self.connection = self._connect()
        self._setup_tables()

    def _connect(self) -> sqlite3.Connection:
        os.makedirs(os.path.dirname(self.database_path), exist_ok=True)
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _setup_tables(self) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS raw_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_file TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                data_hash TEXT NOT NULL,
                row_count INTEGER,
                file_size INTEGER,
                processing_status TEXT DEFAULT 'pending'
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS processed_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                raw_data_id INTEGER,
                processed_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                transformation_type TEXT,
                output_file TEXT,
                quality_score REAL,
                error_count INTEGER DEFAULT 0,
                FOREIGN KEY (raw_data_id) REFERENCES raw_data (id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_type TEXT NOT NULL,
                generated_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                file_path TEXT,
                recipient_email TEXT,
                status TEXT DEFAULT 'generated'
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                user_id TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                details TEXT,
                ip_address TEXT
            )
            """
        )
        self.connection.commit()
        self.logger.info("Database initialized successfully")

    def log_raw_data(self, source_file: str, data_hash: str, row_count: int, file_size: int) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO raw_data (source_file, data_hash, row_count, file_size)
            VALUES (?, ?, ?, ?)
            """,
            (source_file, data_hash, row_count, file_size),
        )
        self.connection.commit()

    def fetch_recent_files(self, limit: int = 10) -> list[dict[str, Any]]:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT source_file, timestamp, row_count
            FROM raw_data
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def log_report(self, report_type: str, file_path: str, status: str = "completed") -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO reports (report_type, file_path, status)
            VALUES (?, ?, ?)
            """,
            (report_type, file_path, status),
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()
