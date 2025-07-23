#!/usr/bin/env python3
"""
DataProcessor - A monolithic data processing application
This file contains everything: database operations, file I/O, data transformations, 
reporting, and configuration management all in one place.

This needs to be refactored into proper modular components!
"""

import os
import json
import csv
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import configparser
import hashlib
import requests
from pathlib import Path
import zipfile
import shutil


class DataProcessor:
    """
    Monolithic data processor that handles everything.
    This class is doing way too much and needs to be broken down!
    """
    
    def __init__(self):
        # Configuration management - should be separate
        self.config = {
            'database_path': 'data/analytics.db',
            'input_directory': 'data/input/',
            'output_directory': 'data/output/',
            'reports_directory': 'reports/',
            'log_file': 'logs/processor.log',
            'email_server': 'smtp.gmail.com',
            'email_port': 587,
            'email_user': 'analytics@company.com',
            'email_password': 'secure_password_123',
            'api_base_url': 'https://api.dataservice.com/v1',
            'api_key': 'sk-1234567890abcdef',
            'chunk_size': 10000,
            'max_file_size': 100 * 1024 * 1024,  # 100MB
            'backup_enabled': True,
            'encryption_key': 'my_secret_key_2024'
        }
        
        # Initialize logging - should be separate
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config['log_file']),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Database connection - should be separate
        self.db_connection = None
        self.setup_database()
        
        # Data storage
        self.raw_data = []
        self.processed_data = []
        self.summary_stats = {}
        self.reports_generated = []
        
    def setup_database(self):
        """Initialize database connection and create tables if needed"""
        try:
            os.makedirs(os.path.dirname(self.config['database_path']), exist_ok=True)
            self.db_connection = sqlite3.connect(self.config['database_path'])
            self.db_connection.row_factory = sqlite3.Row
            
            # Create tables - this should be in a separate database module
            cursor = self.db_connection.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS raw_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_file TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    data_hash TEXT NOT NULL,
                    row_count INTEGER,
                    file_size INTEGER,
                    processing_status TEXT DEFAULT 'pending'
                )
            ''')
            
            cursor.execute('''
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
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_type TEXT NOT NULL,
                    generated_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    file_path TEXT,
                    recipient_email TEXT,
                    status TEXT DEFAULT 'generated'
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    user_id TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    details TEXT,
                    ip_address TEXT
                )
            ''')
            
            self.db_connection.commit()
            self.logger.info("Database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Database setup failed: {str(e)}")
            raise
    
    def load_config_from_file(self, config_file):
        """Load configuration from INI file - should be in config module"""
        try:
            config_parser = configparser.ConfigParser()
            config_parser.read(config_file)
            
            for section in config_parser.sections():
                for key, value in config_parser.items(section):
                    # Try to convert to appropriate type
                    if value.lower() in ['true', 'false']:
                        self.config[key] = config_parser.getboolean(section, key)
                    elif value.isdigit():
                        self.config[key] = config_parser.getint(section, key)
                    elif value.replace('.', '').isdigit():
                        self.config[key] = config_parser.getfloat(section, key)
                    else:
                        self.config[key] = value
                        
            self.logger.info(f"Configuration loaded from {config_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to load config: {str(e)}")
    
    def validate_file(self, file_path):
        """Validate input file - should be in file handlers module"""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            file_size = os.path.getsize(file_path)
            if file_size > self.config['max_file_size']:
                raise ValueError(f"File too large: {file_size} bytes")
            
            if file_size == 0:
                raise ValueError("File is empty")
            
            # Check file extension
            valid_extensions = ['.csv', '.json', '.xlsx', '.txt']
            if not any(file_path.lower().endswith(ext) for ext in valid_extensions):
                raise ValueError(f"Unsupported file type: {file_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"File validation failed: {str(e)}")
            return False
    
    def calculate_file_hash(self, file_path):
        """Calculate MD5 hash of file - should be in utilities"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            self.logger.error(f"Hash calculation failed: {str(e)}")
            return None
    
    def load_csv_file(self, file_path):
        """Load CSV file with error handling - should be in file handlers"""
        try:
            self.logger.info(f"Loading CSV file: {file_path}")
            
            if not self.validate_file(file_path):
                return None
            
            # Try different encodings
            encodings = ['utf-8', 'latin1', 'cp1252']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding, 
                                   chunksize=self.config['chunk_size'])
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                raise ValueError("Could not decode file with any encoding")
            
            # Process in chunks
            all_data = []
            for chunk in df:
                all_data.append(chunk)
            
            final_df = pd.concat(all_data, ignore_index=True)
            
            # Log to database
            file_hash = self.calculate_file_hash(file_path)
            cursor = self.db_connection.cursor()
            cursor.execute('''
                INSERT INTO raw_data (source_file, data_hash, row_count, file_size)
                VALUES (?, ?, ?, ?)
            ''', (file_path, file_hash, len(final_df), os.path.getsize(file_path)))
            self.db_connection.commit()
            
            self.logger.info(f"Successfully loaded {len(final_df)} rows from {file_path}")
            return final_df
            
        except Exception as e:
            self.logger.error(f"Failed to load CSV: {str(e)}")
            return None
    
    def load_json_file(self, file_path):
        """Load JSON file - should be in file handlers"""
        try:
            self.logger.info(f"Loading JSON file: {file_path}")
            
            if not self.validate_file(file_path):
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert to DataFrame if it's a list of objects
            if isinstance(data, list) and all(isinstance(item, dict) for item in data):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                df = pd.DataFrame([data])
            else:
                raise ValueError("Unsupported JSON structure")
            
            # Log to database
            file_hash = self.calculate_file_hash(file_path)
            cursor = self.db_connection.cursor()
            cursor.execute('''
                INSERT INTO raw_data (source_file, data_hash, row_count, file_size)
                VALUES (?, ?, ?, ?)
            ''', (file_path, file_hash, len(df), os.path.getsize(file_path)))
            self.db_connection.commit()
            
            self.logger.info(f"Successfully loaded {len(df)} rows from JSON")
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to load JSON: {str(e)}")
            return None
    
    def fetch_data_from_api(self, endpoint, params=None):
        """Fetch data from API - should be in API module"""
        try:
            self.logger.info(f"Fetching data from API: {endpoint}")
            
            headers = {
                'Authorization': f'Bearer {self.config["api_key"]}',
                'Content-Type': 'application/json'
            }
            
            url = f"{self.config['api_base_url']}/{endpoint}"
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Convert to DataFrame
            if isinstance(data, dict) and 'data' in data:
                df = pd.DataFrame(data['data'])
            elif isinstance(data, list):
                df = pd.DataFrame(data)
            else:
                df = pd.DataFrame([data])
            
            self.logger.info(f"Successfully fetched {len(df)} records from API")
            return df
            
        except Exception as e:
            self.logger.error(f"API fetch failed: {str(e)}")
            return None
    
    def clean_data(self, df):
        """Clean and preprocess data - should be in data transformation module"""
        try:
            self.logger.info("Starting data cleaning process")
            original_rows = len(df)
            
            # Remove duplicates
            df = df.drop_duplicates()
            
            # Handle missing values
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            for col in numeric_columns:
                df[col] = df[col].fillna(df[col].median())
            
            text_columns = df.select_dtypes(include=['object']).columns
            for col in text_columns:
                df[col] = df[col].fillna('Unknown')
            
            # Remove outliers using IQR method
            for col in numeric_columns:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]
            
            # Standardize text data
            for col in text_columns:
                df[col] = df[col].str.strip().str.lower()
            
            # Add data quality metrics
            df['quality_score'] = np.random.uniform(0.7, 1.0, len(df))
            df['processed_timestamp'] = datetime.now()
            
            final_rows = len(df)
            self.logger.info(f"Data cleaning complete: {original_rows} -> {final_rows} rows")
            
            return df
            
        except Exception as e:
            self.logger.error(f"Data cleaning failed: {str(e)}")
            return df
    
    def transform_data(self, df, transformation_type='standard'):
        """Apply data transformations - should be in transformation module"""
        try:
            self.logger.info(f"Applying {transformation_type} transformation")
            
            if transformation_type == 'standard':
                # Standard scaling for numeric columns
                numeric_columns = df.select_dtypes(include=[np.number]).columns
                for col in numeric_columns:
                    if col not in ['quality_score']:  # Skip our added columns
                        mean_val = df[col].mean()
                        std_val = df[col].std()
                        if std_val != 0:
                            df[f'{col}_standardized'] = (df[col] - mean_val) / std_val
            
            elif transformation_type == 'normalize':
                # Min-max normalization
                numeric_columns = df.select_dtypes(include=[np.number]).columns
                for col in numeric_columns:
                    if col not in ['quality_score']:
                        min_val = df[col].min()
                        max_val = df[col].max()
                        if max_val != min_val:
                            df[f'{col}_normalized'] = (df[col] - min_val) / (max_val - min_val)
            
            elif transformation_type == 'categorical':
                # Encode categorical variables
                text_columns = df.select_dtypes(include=['object']).columns
                for col in text_columns:
                    if col not in ['processed_timestamp']:
                        df[f'{col}_encoded'] = pd.Categorical(df[col]).codes
            
            # Calculate aggregated features
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            if len(numeric_columns) > 1:
                df['feature_sum'] = df[numeric_columns].sum(axis=1)
                df['feature_mean'] = df[numeric_columns].mean(axis=1)
                df['feature_std'] = df[numeric_columns].std(axis=1)
            
            self.logger.info(f"Transformation complete: {len(df.columns)} columns")
            return df
            
        except Exception as e:
            self.logger.error(f"Data transformation failed: {str(e)}")
            return df
    
    def calculate_statistics(self, df):
        """Calculate summary statistics - should be in analytics module"""
        try:
            self.logger.info("Calculating summary statistics")
            
            stats = {}
            
            # Basic statistics
            stats['total_rows'] = len(df)
            stats['total_columns'] = len(df.columns)
            stats['memory_usage'] = df.memory_usage(deep=True).sum()
            
            # Numeric column statistics
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            for col in numeric_columns:
                stats[f'{col}_mean'] = df[col].mean()
                stats[f'{col}_median'] = df[col].median()
                stats[f'{col}_std'] = df[col].std()
                stats[f'{col}_min'] = df[col].min()
                stats[f'{col}_max'] = df[col].max()
                stats[f'{col}_null_count'] = df[col].isnull().sum()
            
            # Categorical column statistics
            text_columns = df.select_dtypes(include=['object']).columns
            for col in text_columns:
                stats[f'{col}_unique_count'] = df[col].nunique()
                stats[f'{col}_most_common'] = df[col].mode().iloc[0] if not df[col].mode().empty else 'N/A'
                stats[f'{col}_null_count'] = df[col].isnull().sum()
            
            # Data quality metrics
            stats['overall_quality_score'] = df.get('quality_score', pd.Series([0])).mean()
            stats['completeness_ratio'] = 1 - (df.isnull().sum().sum() / (len(df) * len(df.columns)))
            
            self.summary_stats = stats
            self.logger.info("Statistics calculation complete")
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Statistics calculation failed: {str(e)}")
            return {}
    
    def generate_visualizations(self, df, output_dir):
        """Generate data visualizations - should be in visualization module"""
        try:
            self.logger.info("Generating visualizations")
            os.makedirs(output_dir, exist_ok=True)
            
            plt.style.use('seaborn-v0_8')
            
            # Correlation heatmap
            numeric_df = df.select_dtypes(include=[np.number])
            if len(numeric_df.columns) > 1:
                plt.figure(figsize=(12, 8))
                correlation_matrix = numeric_df.corr()
                sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0)
                plt.title('Feature Correlation Heatmap')
                plt.tight_layout()
                plt.savefig(f'{output_dir}/correlation_heatmap.png', dpi=300, bbox_inches='tight')
                plt.close()
            
            # Distribution plots for numeric columns
            numeric_columns = numeric_df.columns[:6]  # Limit to first 6 columns
            if len(numeric_columns) > 0:
                fig, axes = plt.subplots(2, 3, figsize=(15, 10))
                axes = axes.ravel()
                
                for i, col in enumerate(numeric_columns):
                    if i < 6:
                        axes[i].hist(df[col].dropna(), bins=30, alpha=0.7)
                        axes[i].set_title(f'Distribution of {col}')
                        axes[i].set_xlabel(col)
                        axes[i].set_ylabel('Frequency')
                
                plt.tight_layout()
                plt.savefig(f'{output_dir}/distributions.png', dpi=300, bbox_inches='tight')
                plt.close()
            
            # Box plots for outlier detection
            if len(numeric_columns) > 0:
                plt.figure(figsize=(12, 6))
                df[numeric_columns].boxplot()
                plt.title('Box Plots for Outlier Detection')
                plt.xticks(rotation=45)
                plt.tight_layout()
                plt.savefig(f'{output_dir}/boxplots.png', dpi=300, bbox_inches='tight')
                plt.close()
            
            self.logger.info(f"Visualizations saved to {output_dir}")
            
        except Exception as e:
            self.logger.error(f"Visualization generation failed: {str(e)}")
    
    def export_data(self, df, output_path, format_type='csv'):
        """Export processed data - should be in export module"""
        try:
            self.logger.info(f"Exporting data to {output_path} as {format_type}")
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            if format_type.lower() == 'csv':
                df.to_csv(output_path, index=False)
            elif format_type.lower() == 'json':
                df.to_json(output_path, orient='records', indent=2)
            elif format_type.lower() == 'xlsx':
                df.to_excel(output_path, index=False)
            elif format_type.lower() == 'parquet':
                df.to_parquet(output_path, index=False)
            else:
                raise ValueError(f"Unsupported export format: {format_type}")
            
            self.logger.info(f"Data exported successfully to {output_path}")
            
        except Exception as e:
            self.logger.error(f"Data export failed: {str(e)}")
    
    def generate_report(self, report_type='summary'):
        """Generate various types of reports - should be in reporting module"""
        try:
            self.logger.info(f"Generating {report_type} report")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_dir = self.config['reports_directory']
            os.makedirs(report_dir, exist_ok=True)
            
            if report_type == 'summary':
                report_path = f"{report_dir}/summary_report_{timestamp}.txt"
                with open(report_path, 'w') as f:
                    f.write("DATA PROCESSING SUMMARY REPORT\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    
                    f.write("PROCESSING STATISTICS:\n")
                    f.write("-" * 25 + "\n")
                    for key, value in self.summary_stats.items():
                        f.write(f"{key}: {value}\n")
                    
                    f.write("\n\nFILES PROCESSED:\n")
                    f.write("-" * 20 + "\n")
                    cursor = self.db_connection.cursor()
                    cursor.execute("SELECT source_file, timestamp, row_count FROM raw_data ORDER BY timestamp DESC LIMIT 10")
                    for row in cursor.fetchall():
                        f.write(f"File: {row['source_file']}, Rows: {row['row_count']}, Time: {row['timestamp']}\n")
            
            elif report_type == 'detailed':
                report_path = f"{report_dir}/detailed_report_{timestamp}.html"
                html_content = self.generate_html_report()
                with open(report_path, 'w') as f:
                    f.write(html_content)
            
            # Log report generation
            cursor = self.db_connection.cursor()
            cursor.execute('''
                INSERT INTO reports (report_type, file_path, status)
                VALUES (?, ?, 'completed')
            ''', (report_type, report_path))
            self.db_connection.commit()
            
            self.reports_generated.append(report_path)
            self.logger.info(f"Report generated: {report_path}")
            
            return report_path
            
        except Exception as e:
            self.logger.error(f"Report generation failed: {str(e)}")
            return None
    
    def generate_html_report(self):
        """Generate HTML report - should be in reporting module"""
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
        """.format(timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        for key, value in self.summary_stats.items():
            html += f"<tr><td>{key}</td><td>{value}</td></tr>"
        
        html += """
                </table>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def send_email_report(self, report_path, recipient_email):
        """Send report via email - should be in notification module"""
        try:
            self.logger.info(f"Sending report to {recipient_email}")
            
            msg = MIMEMultipart()
            msg['From'] = self.config['email_user']
            msg['To'] = recipient_email
            msg['Subject'] = f"Data Processing Report - {datetime.now().strftime('%Y-%m-%d')}"
            
            body = """
            Dear User,
            
            Please find attached the latest data processing report.
            
            Best regards,
            Data Processing System
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach report file
            with open(report_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {os.path.basename(report_path)}'
            )
            msg.attach(part)
            
            # Send email
            server = smtplib.SMTP(self.config['email_server'], self.config['email_port'])
            server.starttls()
            server.login(self.config['email_user'], self.config['email_password'])
            text = msg.as_string()
            server.sendmail(self.config['email_user'], recipient_email, text)
            server.quit()
            
            self.logger.info("Email sent successfully")
            
        except Exception as e:
            self.logger.error(f"Email sending failed: {str(e)}")
    
    def backup_data(self):
        """Create backup of processed data - should be in backup module"""
        if not self.config['backup_enabled']:
            return
        
        try:
            self.logger.info("Creating data backup")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = f"backups/backup_{timestamp}"
            os.makedirs(backup_dir, exist_ok=True)
            
            # Backup database
            shutil.copy2(self.config['database_path'], f"{backup_dir}/database_backup.db")
            
            # Backup output files
            if os.path.exists(self.config['output_directory']):
                shutil.copytree(self.config['output_directory'], f"{backup_dir}/output", dirs_exist_ok=True)
            
            # Backup reports
            if os.path.exists(self.config['reports_directory']):
                shutil.copytree(self.config['reports_directory'], f"{backup_dir}/reports", dirs_exist_ok=True)
            
            # Create backup info file
            backup_info = {
                'timestamp': timestamp,
                'database_size': os.path.getsize(self.config['database_path']),
                'files_backed_up': len(os.listdir(backup_dir)),
                'backup_size': sum(os.path.getsize(os.path.join(backup_dir, f)) 
                                 for f in os.listdir(backup_dir) 
                                 if os.path.isfile(os.path.join(backup_dir, f)))
            }
            
            with open(f"{backup_dir}/backup_info.json", 'w') as f:
                json.dump(backup_info, f, indent=2)
            
            self.logger.info(f"Backup created: {backup_dir}")
            
        except Exception as e:
            self.logger.error(f"Backup failed: {str(e)}")
    
    def cleanup_old_files(self, days_old=30):
        """Clean up old files - should be in maintenance module"""
        try:
            self.logger.info(f"Cleaning up files older than {days_old} days")
            
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            # Clean up old output files
            if os.path.exists(self.config['output_directory']):
                for file_path in Path(self.config['output_directory']).rglob('*'):
                    if file_path.is_file():
                        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if file_mtime < cutoff_date:
                            file_path.unlink()
                            self.logger.info(f"Deleted old file: {file_path}")
            
            # Clean up old reports
            if os.path.exists(self.config['reports_directory']):
                for file_path in Path(self.config['reports_directory']).rglob('*'):
                    if file_path.is_file():
                        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if file_mtime < cutoff_date:
                            file_path.unlink()
                            self.logger.info(f"Deleted old report: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {str(e)}")
    
    def process_directory(self, input_directory):
        """Process all files in a directory - main orchestration method"""
        try:
            self.logger.info(f"Processing directory: {input_directory}")
            
            all_processed_data = []
            
            for file_path in Path(input_directory).glob('*'):
                if file_path.is_file():
                    self.logger.info(f"Processing file: {file_path}")
                    
                    # Load data based on file type
                    if file_path.suffix.lower() == '.csv':
                        df = self.load_csv_file(str(file_path))
                    elif file_path.suffix.lower() == '.json':
                        df = self.load_json_file(str(file_path))
                    else:
                        self.logger.warning(f"Unsupported file type: {file_path}")
                        continue
                    
                    if df is not None:
                        # Clean and transform data
                        df = self.clean_data(df)
                        df = self.transform_data(df)
                        
                        # Add to processed data
                        all_processed_data.append(df)
                        
                        # Export processed data
                        output_path = f"{self.config['output_directory']}/processed_{file_path.stem}.csv"
                        self.export_data(df, output_path)
            
            # Combine all processed data
            if all_processed_data:
                combined_df = pd.concat(all_processed_data, ignore_index=True)
                
                # Calculate statistics
                self.calculate_statistics(combined_df)
                
                # Generate visualizations
                viz_dir = f"{self.config['output_directory']}/visualizations"
                self.generate_visualizations(combined_df, viz_dir)
                
                # Generate reports
                self.generate_report('summary')
                self.generate_report('detailed')
                
                # Backup data
                self.backup_data()
                
                # Cleanup old files
                self.cleanup_old_files()
                
                self.logger.info("Directory processing completed successfully")
                return combined_df
            
        except Exception as e:
            self.logger.error(f"Directory processing failed: {str(e)}")
            return None
    
    def __del__(self):
        """Cleanup database connection"""
        if self.db_connection:
            self.db_connection.close()


# Main execution function - this should also be separate
def main():
    """Main function to run the data processor"""
    try:
        processor = DataProcessor()
        
        # Load configuration if file exists
        config_file = 'config/settings.ini'
        if os.path.exists(config_file):
            processor.load_config_from_file(config_file)
        
        # Process input directory
        result = processor.process_directory(processor.config['input_directory'])
        
        if result is not None:
            print(f"Processing completed. {len(result)} total rows processed.")
            print(f"Reports generated: {len(processor.reports_generated)}")
        else:
            print("Processing failed.")
    
    except Exception as e:
        print(f"Application failed: {str(e)}")


if __name__ == "__main__":
    main() 