# Oracle Batch Updater Package
__version__ = "2.8.0"

# ============================================================
# 核心模块 (必须成功导入，否则应用无法启动)
# ============================================================

from src.errors import (
    OracleUpdaterError,
    ConnectionError,
    ValidationError,
    SQLExecutionError,
    BackupError,
    RollbackError,
    CancelledError,
)
from src.constants import DEFAULT_BATCH_SIZE, VERSION, APP_NAME, SUPPORTED_FILE_FORMATS
from src.logger import LogManager
from src.config_manager import ConfigManager
from src.excel_handler import ExcelHandler
from src.db_connection import DBConnection, ConnectionPool
from src.data_updater import DataUpdater
from src.security import sanitize_identifier, validate_schema, SecurityError
from src.progress import ProgressTracker, format_eta, format_progress_bar

# ============================================================
# P1 功能模块 (可选 — 导入失败不影响核心 GUI 启动)
# ============================================================

try:
    from src.ora_errors import translate_ora_error, get_error_hint, extract_ora_code
except ImportError:
    translate_ora_error = lambda e: str(e)
    get_error_hint = lambda code: ""
    extract_ora_code = lambda msg: (None, msg)

try:
    from src.data_source import create_data_source, DataSource, ExcelDataSource, CsvDataSource, JsonDataSource
except ImportError:
    create_data_source = None
    DataSource = None
    ExcelDataSource = None
    CsvDataSource = None
    JsonDataSource = None

try:
    from src.auth import Role, RiskLevel, AuthManager, ApprovalManager
except ImportError:
    Role = None
    RiskLevel = None
    AuthManager = None
    ApprovalManager = None

try:
    from src.notification import NotificationManager
except ImportError:
    NotificationManager = None

try:
    from src.history_viewer import HistoryViewer
except ImportError:
    HistoryViewer = None

# ============================================================
# P2 架构模块 (Service 层 — 可选)
# ============================================================

try:
    from src.service import UpdateService, UpdateConfig, UpdateResult, ValidationResult
except ImportError:
    UpdateService = None
    UpdateConfig = None
    UpdateResult = None
    ValidationResult = None

# ============================================================
# P3 平台模块 (可选 — 导入失败不影响核心 GUI)
# ============================================================

try:
    from src.data_compare import DataCompare
except ImportError:
    DataCompare = None

try:
    from src.diagnostics import DiagnosticsCollector
except ImportError:
    DiagnosticsCollector = None

try:
    from src.env_config import EnvironmentConfig
except ImportError:
    EnvironmentConfig = None

try:
    from src.backup_manager import BackupManager
except ImportError:
    BackupManager = None

try:
    from src.scheduler import TaskScheduler
except ImportError:
    TaskScheduler = None

try:
    from src.trend_analysis import TrendAnalyzer
except ImportError:
    TrendAnalyzer = None

try:
    from src.import_stats import ImportStats
except ImportError:
    ImportStats = None

# ============================================================
# __all__ 导出列表
# ============================================================

__all__ = [
    # Core
    "DataUpdater",
    "DBConnection",
    "ConnectionPool",
    "ConfigManager",
    "LogManager",
    "ExcelHandler",
    # Security
    "sanitize_identifier",
    "validate_schema",
    "SecurityError",
    # P1 Performance & Features
    "translate_ora_error",
    "get_error_hint",
    "extract_ora_code",
    "create_data_source",
    "DataSource",
    "ExcelDataSource",
    "CsvDataSource",
    "JsonDataSource",
    "Role",
    "RiskLevel",
    "AuthManager",
    "ApprovalManager",
    "CancelledError",
    # P2 Architecture
    "UpdateService",
    "UpdateConfig",
    "UpdateResult",
    "ValidationResult",
    "NotificationManager",
    "ProgressTracker",
    "format_eta",
    "format_progress_bar",
    "HistoryViewer",
    # P3 Platform
    "DataCompare",
    "DiagnosticsCollector",
    "EnvironmentConfig",
    "BackupManager",
    "TaskScheduler",
    "TrendAnalyzer",
    "ImportStats",
]