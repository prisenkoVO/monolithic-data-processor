#!/usr/bin/env python3
"""Main entrypoint that orchestrates all refactored modules."""

from __future__ import annotations

import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import pandas as pd
import requests

from config import DEFAULT_CONFIG, ensure_directories, load_config
from database import DatabaseManager
from file_handlers import export_data, load_csv_file, load_json_file
from reports import generate_report
from transformers import calculate_statistics, clean_data, transform_data
from utils import backup_data, calculate_file_hash, cleanup_old_files, setup_logger, validate_file
from visualizations import generate_visualizations


class DataProcessor:
    """Backward-compatible facade preserving legacy orchestration behavior."""

    def __init__(self) -> None:
        self.config = dict(DEFAULT_CONFIG)
        ensure_directories(self.config)
        self.logger = setup_logger(self.config["log_file"])
        self.db_manager = DatabaseManager(self.config["database_path"], self.logger)
        self.summary_stats: dict = {}
        self.reports_generated: list[str] = []
        self.raw_data: list = []
        self.processed_data: list = []

    def setup_database(self) -> None:
        """Compatibility method; DB setup is handled in constructor."""
        return

    def load_config_from_file(self, config_file: str) -> None:
        """Load configuration values from ini file into existing config."""
        loaded = load_config(config_file)
        self.config.update(loaded)

    def validate_file(self, file_path: str) -> bool:
        """Validate file and keep legacy bool-return behavior."""
        try:
            validate_file(file_path, self.config["max_file_size"])
            return True
        except Exception as exc:  # noqa: BLE001
            self.logger.error("File validation failed: %s", exc)
            return False

    def calculate_file_hash(self, file_path: str) -> str | None:
        """Calculate file hash with legacy None-on-error behavior."""
        try:
            return calculate_file_hash(file_path)
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Hash calculation failed: %s", exc)
            return None

    def load_csv_file(self, file_path: str) -> pd.DataFrame | None:
        """Compatibility wrapper for CSV loading."""
        if not self.validate_file(file_path):
            return None
        return load_csv_file(file_path, self.config, self.logger, self.db_manager)

    def load_json_file(self, file_path: str) -> pd.DataFrame | None:
        """Compatibility wrapper for JSON loading."""
        if not self.validate_file(file_path):
            return None
        return load_json_file(file_path, self.config, self.logger, self.db_manager)

    def fetch_data_from_api(self, endpoint: str, params: dict | None = None) -> pd.DataFrame | None:
        """Legacy API fetch behavior."""
        try:
            headers = {
                "Authorization": f"Bearer {self.config['api_key']}",
                "Content-Type": "application/json",
            }
            url = f"{self.config['api_base_url']}/{endpoint}"
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            payload = response.json()
            if isinstance(payload, dict) and "data" in payload:
                return pd.DataFrame(payload["data"])
            if isinstance(payload, list):
                return pd.DataFrame(payload)
            return pd.DataFrame([payload])
        except Exception as exc:  # noqa: BLE001
            self.logger.error("API fetch failed: %s", exc)
            return None

    def clean_data(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        return clean_data(dataframe, self.logger)

    def transform_data(self, dataframe: pd.DataFrame, transformation_type: str = "standard") -> pd.DataFrame:
        return transform_data(dataframe, self.logger, transformation_type=transformation_type)

    def calculate_statistics(self, dataframe: pd.DataFrame) -> dict:
        stats = calculate_statistics(dataframe, self.logger)
        self.summary_stats = stats
        return stats

    def generate_visualizations(self, dataframe: pd.DataFrame, output_dir: str) -> None:
        generate_visualizations(dataframe, output_dir, self.logger)

    def export_data(self, dataframe: pd.DataFrame, output_path: str, format_type: str = "csv") -> None:
        try:
            export_data(dataframe, output_path, format_type=format_type)
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Data export failed: %s", exc)

    def generate_report(self, report_type: str = "summary") -> str | None:
        try:
            report_path = generate_report(
                report_type,
                self.summary_stats,
                self.config["reports_directory"],
                self.db_manager,
                self.logger,
            )
            self.reports_generated.append(report_path)
            return report_path
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Report generation failed: %s", exc)
            return None

    def send_email_report(self, report_path: str, recipient_email: str) -> None:
        """Legacy email delivery behavior."""
        try:
            message = MIMEMultipart()
            message["From"] = self.config["email_user"]
            message["To"] = recipient_email
            message["Subject"] = "Data Processing Report"
            message.attach(MIMEText("Please find attached the latest report.", "plain"))

            with open(report_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={Path(report_path).name}")
            message.attach(part)

            server = smtplib.SMTP(self.config["email_server"], self.config["email_port"])
            server.starttls()
            server.login(self.config["email_user"], self.config["email_password"])
            server.sendmail(self.config["email_user"], recipient_email, message.as_string())
            server.quit()
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Email sending failed: %s", exc)

    def backup_data(self) -> None:
        backup_data(self.config, self.logger)

    def cleanup_old_files(self, days_old: int = 30) -> None:
        cleanup_old_files(self.config, self.logger, days_old=days_old)

    def process_directory(self, input_directory: str) -> pd.DataFrame | None:
        """Process directory with original sequence and side effects."""
        try:
            all_processed_data: list[pd.DataFrame] = []
            for file_path in Path(input_directory).glob("*"):
                if not file_path.is_file():
                    continue
                if file_path.suffix.lower() == ".csv":
                    dataframe = self.load_csv_file(str(file_path))
                elif file_path.suffix.lower() == ".json":
                    dataframe = self.load_json_file(str(file_path))
                else:
                    self.logger.warning("Unsupported file type: %s", file_path)
                    continue
                if dataframe is None:
                    continue
                dataframe = self.clean_data(dataframe)
                dataframe = self.transform_data(dataframe)
                all_processed_data.append(dataframe)
                output_path = f"{self.config['output_directory']}/processed_{file_path.stem}.csv"
                self.export_data(dataframe, output_path)

            if all_processed_data:
                combined_df = pd.concat(all_processed_data, ignore_index=True)
                self.calculate_statistics(combined_df)
                viz_dir = f"{self.config['output_directory']}/visualizations"
                self.generate_visualizations(combined_df, viz_dir)
                self.generate_report("summary")
                self.generate_report("detailed")
                self.backup_data()
                self.cleanup_old_files()
                return combined_df
            return None
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Directory processing failed: %s", exc)
            return None

    def __del__(self) -> None:
        try:
            self.db_manager.close()
        except Exception:  # noqa: BLE001
            pass


def main() -> None:
    """Legacy-compatible entrypoint."""
    try:
        processor = DataProcessor()
        config_file = "config/settings.ini"
        if Path(config_file).exists():
            processor.load_config_from_file(config_file)
        result = processor.process_directory(processor.config["input_directory"])
        if result is not None:
            print(f"Processing completed. {len(result)} total rows processed.")
            print(f"Reports generated: {len(processor.reports_generated)}")
        else:
            print("Processing failed.")
    except Exception as exc:  # noqa: BLE001
        print(f"Application failed: {exc}")


if __name__ == "__main__":
    main()
