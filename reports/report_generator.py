"""Reporting module for text and HTML reports."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from database import DatabaseManager


def _generate_html_report(stats: dict[str, Any]) -> str:
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Data Processing Report</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
            .section { margin: 20px 0; }
            .stats-table { border-collapse: collapse; width: 100%; }
            .stats-table th, .stats-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            .stats-table th { background-color: #f2f2f2; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Data Processing Report</h1>
            <p>Generated: {timestamp}</p>
        </div>
        
        <div class="section">
            <h2>Processing Summary</h2>
            <table class="stats-table">
                <tr><th>Metric</th><th>Value</th></tr>
    """.format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    for key, value in stats.items():
        html += f"<tr><td>{key}</td><td>{value}</td></tr>"

    html += """
            </table>
        </div>
    </body>
    </html>
    """
    return html


def generate_report(
    report_type: str,
    stats: dict[str, Any],
    reports_directory: str,
    db_manager: DatabaseManager,
    logger: logging.Logger,
) -> str:
    """Create summary/detailed report and persist report metadata."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = Path(reports_directory)
    report_dir.mkdir(parents=True, exist_ok=True)

    if report_type == "summary":
        report_path = report_dir / f"summary_report_{timestamp}.txt"
        lines = [
            "DATA PROCESSING SUMMARY REPORT",
            "=" * 50,
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "PROCESSING STATISTICS:",
            "-" * 25,
        ]
        lines.extend(f"{key}: {value}" for key, value in stats.items())
        lines.extend(["", "FILES PROCESSED:", "-" * 20])
        lines.extend(
            f"File: {row['source_file']}, Rows: {row['row_count']}, Time: {row['timestamp']}"
            for row in db_manager.fetch_recent_files(limit=10)
        )
        report_path.write_text("\n".join(lines))
    else:
        report_path = report_dir / f"detailed_report_{timestamp}.html"
        report_path.write_text(_generate_html_report(stats))

    db_manager.log_report(report_type, str(report_path), status="completed")
    logger.info("Report generated: %s", report_path)
    return str(report_path)
