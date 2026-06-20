"""Centralized constants configuration for DBForge.

All hardcoded values used across the application are defined here
to provide a single source of truth for configuration defaults.
"""

# ---------------------------------------------------------------------------
# Application metadata
# ---------------------------------------------------------------------------
VERSION = "2.8.0"
APP_NAME = "DBForge"

# ---------------------------------------------------------------------------
# Batch processing defaults
# ---------------------------------------------------------------------------
DEFAULT_BATCH_SIZE = 100
DEFAULT_MAX_FILE_SIZE = 10 * 1024 * 1024       # 10 MB
DEFAULT_MAX_ROWS = 100000
DEFAULT_CSV_MAX_ROWS = 10000000

# ---------------------------------------------------------------------------
# Schema defaults
# ---------------------------------------------------------------------------
DEFAULT_TEMP_SCHEMA = "APPS"
DEFAULT_TARGET_SCHEMA = "APPS"

# ---------------------------------------------------------------------------
# Connection pool defaults
# ---------------------------------------------------------------------------
DEFAULT_TIMEOUT = 30
DEFAULT_POOL_MIN = 2
DEFAULT_POOL_MAX = 10
DEFAULT_POOL_INCREMENT = 1

# ---------------------------------------------------------------------------
# Supported file formats
# ---------------------------------------------------------------------------
SUPPORTED_FILE_FORMATS = ['.xlsx', '.xls', '.csv', '.json', '.jsonl']

# ---------------------------------------------------------------------------
# Retention periods (days)
# ---------------------------------------------------------------------------
AUDIT_LOG_RETENTION_DAYS = 90
BACKUP_RETENTION_DAYS = 30

# ---------------------------------------------------------------------------
# Preview limits
# ---------------------------------------------------------------------------
MAX_PREVIEW_ROWS = 50