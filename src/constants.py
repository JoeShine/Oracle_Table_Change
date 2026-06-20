# v2.9.1
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

# ---------------------------------------------------------------------------
# Multi-database support (v2.9.0+)
# ---------------------------------------------------------------------------
DB_TYPE_ORACLE = "oracle"
DB_TYPE_MYSQL = "mysql"
DB_TYPE_MSSQL = "mssql"

DB_DEFAULT_PORTS = {
    DB_TYPE_ORACLE: 1521,
    DB_TYPE_MYSQL: 3306,
    DB_TYPE_MSSQL: 1433,
}

# ---------------------------------------------------------------------------
# 支持的数据库类型 (v2.9.0+)
# ---------------------------------------------------------------------------
# 数据库类型常量
DB_TYPE_ORACLE = "oracle"
DB_TYPE_MYSQL = "mysql"
DB_TYPE_MSSQL = "mssql"   # MS SQL Server (2003 / 2008 R2 / 2012 等)

# 各数据库默认端口
DB_DEFAULT_PORTS = {
    DB_TYPE_ORACLE: 1521,
    DB_TYPE_MYSQL: 3306,
    DB_TYPE_MSSQL: 1433,
}

# 各数据库显示名称
DB_DISPLAY_NAMES = {
    DB_TYPE_ORACLE: "Oracle (11g / 12c / 19c)",
    DB_TYPE_MYSQL: "MySQL (5.7+ / 8.0+)",
    DB_TYPE_MSSQL: "MS SQL Server (2003 / 2008 R2 / 2012+)",
}

# 支持的数据库类型列表（按字母顺序）
SUPPORTED_DB_TYPES = [DB_TYPE_ORACLE, DB_TYPE_MYSQL, DB_TYPE_MSSQL]

# 默认数据库类型（向后兼容，v2.8.0 之前默认是 Oracle）
DEFAULT_DB_TYPE = DB_TYPE_ORACLE