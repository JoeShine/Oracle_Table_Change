"""结构化异常体系

替代项目中散布的裸 Exception 和 except Exception: pass 模式。
所有自定义异常均继承自 OracleUpdaterError，便于统一捕获和分类处理。
"""


class OracleUpdaterError(Exception):
    """OracleBatchUpdater 基础异常"""
    exit_code = 1

    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(message)


class ConnectionError(OracleUpdaterError):
    """数据库连接相关异常"""
    exit_code = 2


class ValidationError(OracleUpdaterError):
    """数据校验相关异常"""
    exit_code = 3


class SQLExecutionError(OracleUpdaterError):
    """SQL 执行相关异常"""
    exit_code = 4


class BackupError(OracleUpdaterError):
    """备份操作相关异常"""
    exit_code = 5


class RollbackError(OracleUpdaterError):
    """回滚操作相关异常"""
    exit_code = 6


class ConfigError(OracleUpdaterError):
    """配置相关异常"""
    exit_code = 7


class SecurityError(OracleUpdaterError):
    """安全相关异常（SQL 注入、权限不足等）"""
    exit_code = 8


class ImportError(OracleUpdaterError):
    """数据导入相关异常"""
    exit_code = 9


class CancelledError(OracleUpdaterError):
    """操作被取消异常 (P1-10)"""
    exit_code = 10