"""Logging system for Automated File Organizer."""

import logging
from pathlib import Path
from typing import List, Optional

from config import LOG_DIR, LOG_FILE

_logger_instance: Optional[logging.Logger] = None


def setup_logger(log_file: Optional[Path] = None, level: int = logging.INFO) -> logging.Logger:
    """Configures and returns the application logger instance."""
    global _logger_instance
    if _logger_instance is not None:
        return _logger_instance

    target_log_file = log_file or LOG_FILE
    target_log_dir = target_log_file.parent
    target_log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("AutomatedFileOrganizer")
    logger.setLevel(level)

    if not logger.handlers:
        file_handler = logging.FileHandler(target_log_file, encoding="utf-8")
        file_handler.setLevel(level)

        formatter = logging.Formatter(
            fmt="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    _logger_instance = logger
    return logger


def get_logger() -> logging.Logger:
    """Returns the central application logger."""
    global _logger_instance
    if _logger_instance is None:
        return setup_logger()
    return _logger_instance


def get_recent_logs(max_lines: int = 50, log_file: Optional[Path] = None) -> List[str]:
    """Reads and returns the most recent lines from the activity log file."""
    target_file = log_file or LOG_FILE
    if not target_file.exists():
        return []

    try:
        with open(target_file, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
            return [line.rstrip("\r\n") for line in lines[-max_lines:]]
    except Exception as e:
        get_logger().error(f"Failed to read activity log: {e}")
        return []
