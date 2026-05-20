import logging
import os
from datetime import datetime
from pathlib import Path


class LogManager:
    def __init__(self):
        self.app_dir = Path(__file__).parent.parent
        self.logs_dir = self.app_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        self.log_file = None
        self.logger = None
        self.failed_records = []
        self.init_logger()

    def init_logger(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.logs_dir / f"update_{timestamp}.log"
        self.logger = logging.getLogger('OracleUpdater')
        self.logger.setLevel(logging.INFO)
        if self.logger.handlers:
            self.logger.handlers.clear()
        fh = logging.FileHandler(self.log_file, encoding='utf-8')
        fh.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)

    def info(self, message):
        self.logger.info(message)

    def success(self, message):
        self.logger.info(f"SUCCESS - {message}")

    def error(self, message):
        self.logger.error(f"ERROR - {message}")

    def warning(self, message):
        self.logger.warning(f"WARNING - {message}")

    def add_failed_record(self, key_value, update_value, reason):
        self.failed_records.append({
            "key_value": key_value,
            "update_value": update_value,
            "reason": reason,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    def get_failed_records(self):
        return self.failed_records

    def clear_failed_records(self):
        self.failed_records = []

    def get_log_file_path(self):
        return str(self.log_file)

    def get_all_logs(self):
        if self.log_file and self.log_file.exists():
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    return f.readlines()
            except Exception:
                return []
        return []
