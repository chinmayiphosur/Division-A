import logging
import os
from logging.handlers import RotatingFileHandler
import json
from datetime import datetime

# Create logs directory if it doesn't exist
LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOGS_DIR, exist_ok=True)
LOG_FILE_PATH = os.path.join(LOGS_DIR, "breach_analytics.log")

class StructuredFormatter(logging.Formatter):
    """
    Custom formatter to output logs in a clean, highly readable, structured format:
    TIMESTAMP | LEVEL | MODULE | MESSAGE | METADATA
    """
    def format(self, record):
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]
        level = record.levelname.ljust(8)
        module = record.name.ljust(15)
        message = record.getMessage()
        
        # Extract custom metadata if provided
        extra = getattr(record, "metadata", None)
        extra_str = f" | {json.dumps(extra)}" if extra else ""
        
        return f"{timestamp} | {level} | {module} | {message}{extra_str}"

def get_logger(name: str) -> logging.Logger:
    """
    Configures and returns a logger instance with console and rotating file handlers.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers if the logger was already configured
    if logger.hasHandlers():
        return logger

    formatter = StructuredFormatter()

    # 1. Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. Rotating File Handler (Max 5MB per file, keeping last 5 backups)
    file_handler = RotatingFileHandler(
        LOG_FILE_PATH, 
        maxBytes=5 * 1024 * 1024, 
        backupCount=5, 
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

def log_incident(logger, org_name: str, sector: str, num_users: int, risk_score: float, severity: str, duration_ms: float = 0.0):
    """
    Helper function to log breach incident assessments with structured telemetry data.
    """
    metadata = {
        "event_type": "breach_assessment",
        "organisation": org_name,
        "sector": sector,
        "affected_users": num_users,
        "risk_score": risk_score,
        "severity": severity,
        "processing_time_ms": round(duration_ms, 2)
    }
    logger.info(
        f"Breach assessed for '{org_name}' [Sector: {sector}, Users: {num_users:,}] - Risk Score: {risk_score}/10 ({severity})",
        extra={"metadata": metadata}
    )

def log_api_call(logger, method: str, endpoint: str, status_code: int, duration_ms: float):
    """
    Helper function to log API traffic telemetry.
    """
    metadata = {
        "event_type": "api_traffic",
        "method": method,
        "endpoint": endpoint,
        "status_code": status_code,
        "latency_ms": round(duration_ms, 2)
    }
    logger.info(
        f"API Request: {method} {endpoint} -> Status {status_code} ({duration_ms:.1f}ms)",
        extra={"metadata": metadata}
    )
