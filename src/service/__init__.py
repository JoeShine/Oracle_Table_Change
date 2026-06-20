"""Service 层 — P2-1: GUI 与业务逻辑彻底分离

提供 UpdateConfig / UpdateResult 结构化数据类，
以及 UpdateService 原子编排方法。
GUI 和 CLI 都通过此层调用，不再直接操作 DataUpdater。
"""

import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path

from src.data_updater import DataUpdater
from src.db_connection import DBConnection
from src.logger import LogManager
from src.data_source import create_data_source, DataSource
from src.notification import NotificationManager


# ---------------------------------------------------------------------------
# 结构化数据类
# ---------------------------------------------------------------------------

@dataclass
class UpdateConfig:
    """更新配置"""
    connection_name: str
    schema: str = "APPS"
    temp_schema: str = "APPS"
    target_table: str = ""
    key_column: str = ""
    update_columns: List[str] = field(default_factory=list)
    data_source: Optional[DataSource] = None
    data_file_path: str = ""
    # 选项
    dry_run: bool = False
    auto_confirm: bool = False
    use_merge: bool = True  # P1-1: 默认使用 MERGE
    # 取消
    cancel_event: Optional[Any] = None  # threading.Event


@dataclass
class UpdateResult:
    """更新结果"""
    success: bool
    success_count: int = 0
    fail_count: int = 0
    unmatched_count: int = 0
    total_count: int = 0
    backup_table: str = ""
    elapsed_ms: int = 0
    failed_records: List[Dict[str, Any]] = field(default_factory=list)
    error_msg: str = ""
    sql_preview: str = ""  # P2-7: SQL 预览


@dataclass
class ValidationResult:
    """验证结果"""
    valid: bool
    message: str = ""
    column_types: Dict[str, str] = field(default_factory=dict)
    risk_level: str = "low"
    risk_reason: str = ""


# ---------------------------------------------------------------------------
# Service 层
# ---------------------------------------------------------------------------

class UpdateService:
    """批量更新业务编排服务"""

    def __init__(self, log: LogManager):
        self.log = log
        self.notification = NotificationManager()

    def validate(self, config: UpdateConfig, db: DBConnection) -> ValidationResult:
        """验证更新配置的合法性。

        Returns:
            ValidationResult: 验证结果 + 列类型 + 风险等级
        """
        # 1. 基本检查
        if not config.target_table:
            return ValidationResult(False, "未指定目标表")
        if not config.key_column:
            return ValidationResult(False, "未指定唯一标识列")
        if not config.update_columns:
            return ValidationResult(False, "未指定待更新列")

        # 2. 数据源检查
        if config.data_source is None and config.data_file_path:
            try:
                config.data_source = create_data_source(config.data_file_path)
            except Exception as e:
                return ValidationResult(False, f"无法加载数据文件: {e}")

        if config.data_source is None:
            return ValidationResult(False, "未指定数据源")

        row_count = config.data_source.get_row_count()
        if row_count == 0:
            return ValidationResult(False, "数据文件为空")

        # 3. 数据库验证
        if not db.is_connected():
            return ValidationResult(False, "未连接数据库")

        updater = DataUpdater(db, self.log)
        valid, msg = updater.validate_table_and_columns_multi(
            config.schema, config.target_table,
            config.key_column, config.update_columns
        )
        if not valid:
            return ValidationResult(False, msg)

        # 4. 获取列类型 (P1-2)
        column_types = {}
        columns = db.get_columns(config.target_table)
        for col in columns:
            column_types[col["name"]] = col["type"]

        # 5. 风险评估 (P1-4)
        from src.auth import RiskLevel
        risk, reason = RiskLevel.assess(
            config.connection_name, config.target_table, row_count
        )

        return ValidationResult(
            valid=True,
            message=f"验证通过: {row_count} 行数据, {len(config.update_columns)} 列",
            column_types=column_types,
            risk_level=risk,
            risk_reason=reason,
        )

    def generate_sql_preview(self, config: UpdateConfig, db: DBConnection) -> str:
        """生成 SQL 预览 (P2-7)"""
        if not config.target_table or not config.key_column or not config.update_columns:
            return ""

        if config.use_merge:
            # MERGE 语句预览
            lines = ["-- ====== MERGE 语句预览 ======"]
            lines.append(f"MERGE INTO {config.schema}.{config.target_table} t")
            lines.append(f"USING TEMP_TABLE s")
            lines.append(f"ON (t.{config.key_column} = s.{config.key_column})")
            lines.append("WHEN MATCHED THEN UPDATE SET")
            for col in config.update_columns:
                lines.append(f"    t.{col} = CASE WHEN s.{col} IS NULL THEN t.{col} ELSE s.{col} END")
            lines.append(f"-- ====== 预计影响 {config.data_source.get_row_count() if config.data_source else '?'} 行 ======")
        else:
            # 逐行 UPDATE 预览
            lines = ["-- ====== 逐行 UPDATE 语句预览 ======"]
            lines.append(f"UPDATE {config.schema}.{config.target_table}")
            lines.append(f"SET {', '.join(f'{c} = :{c}' for c in config.update_columns)}")
            lines.append(f"WHERE {config.key_column} = :key_value")
            lines.append(f"-- ====== 预计执行 {config.data_source.get_row_count() if config.data_source else '?'} 次 ======")

        return "\n".join(lines)

    def execute(self, config: UpdateConfig, db: DBConnection,
                progress_callback: Optional[Callable] = None) -> UpdateResult:
        """执行完整的批量更新流程。

        步骤: 验证 → 备份 → 创建临时表 → 导入 → 更新 → 清理

        Returns:
            UpdateResult: 更新结果
        """
        t_start = time.time()

        # 1. 验证
        validation = self.validate(config, db)
        if not validation.valid:
            return UpdateResult(
                success=False, error_msg=validation.message,
                elapsed_ms=int((time.time() - t_start) * 1000)
            )

        # 2. 生成 SQL 预览
        sql_preview = self.generate_sql_preview(config, db)

        # Dry-run 模式
        if config.dry_run:
            return UpdateResult(
                success=True,
                total_count=config.data_source.get_row_count() if config.data_source else 0,
                sql_preview=sql_preview,
                elapsed_ms=int((time.time() - t_start) * 1000),
            )

        updater = DataUpdater(db, self.log)
        if progress_callback:
            updater.set_progress_callback(progress_callback)

        # 3. 备份
        self.log.info(f"正在备份表 {config.schema}.{config.target_table}")
        backup_ok, backup_msg = updater.backup_table(config.schema, config.target_table)
        if not backup_ok:
            return UpdateResult(
                success=False, error_msg=f"备份失败: {backup_msg}",
                sql_preview=sql_preview,
                elapsed_ms=int((time.time() - t_start) * 1000),
            )

        # 4. 创建临时表
        self.log.info(f"正在创建临时表")
        temp_ok, temp_msg = updater.create_temp_table_multi_column(
            config.temp_schema, config.target_table,
            config.key_column, config.update_columns
        )
        if not temp_ok:
            updater.cleanup_on_failure(config.temp_schema)
            return UpdateResult(
                success=False, error_msg=f"创建临时表失败: {temp_msg}",
                backup_table=backup_msg,
                sql_preview=sql_preview,
                elapsed_ms=int((time.time() - t_start) * 1000),
            )

        # 5. 导入数据
        self.log.info(f"正在导入数据")
        data_rows = list(config.data_source.read_rows())
        import_ok, import_msg, imported = updater.import_excel_data_multi_column(
            config.temp_schema, config.key_column,
            config.update_columns, data_rows
        )
        if not import_ok:
            updater.cleanup_on_failure(config.temp_schema)
            return UpdateResult(
                success=False, error_msg=f"导入失败: {import_msg}",
                backup_table=backup_msg,
                sql_preview=sql_preview,
                elapsed_ms=int((time.time() - t_start) * 1000),
            )

        # 6. 执行更新
        self.log.info(f"正在执行更新")
        if config.use_merge:
            success_count, fail_count, problem_records = updater.execute_merge_update(
                config.schema, config.temp_schema, config.target_table,
                config.key_column, config.update_columns
            )
        else:
            success_count, fail_count, problem_records = updater.execute_multi_column_update(
                config.schema, config.temp_schema, config.target_table,
                config.key_column, config.update_columns
            )

        # 7. 清理临时表
        updater.cleanup_temp_table(config.temp_schema)

        # 8. 统计
        unmatched = [r for r in problem_records if "目标表中不存在" in str(r.get("reason", ""))]
        elapsed_ms = int((time.time() - t_start) * 1000)

        # 9. 审计日志
        backup_info = updater.get_backup_info()
        self.log.log_update(
            schema=config.schema,
            table=config.target_table,
            key_column=config.key_column,
            update_columns=config.update_columns,
            total_count=len(data_rows),
            success_count=success_count,
            fail_count=fail_count,
            success=(fail_count == 0),
            backup_table=backup_info["backup_table_name"] if backup_info else "",
            sql_summary=sql_preview[:500],
            elapsed_ms=elapsed_ms,
        )

        # 10. 通知
        self.notification.notify_update_result(
            schema=config.schema,
            table=config.target_table,
            success_count=success_count,
            fail_count=fail_count,
            unmatched_count=len(unmatched),
            elapsed_ms=elapsed_ms,
            backup_table=backup_info["backup_table_name"] if backup_info else "",
        )

        return UpdateResult(
            success=(fail_count == 0),
            success_count=success_count,
            fail_count=fail_count,
            unmatched_count=len(unmatched),
            total_count=len(data_rows),
            backup_table=backup_info["backup_table_name"] if backup_info else "",
            elapsed_ms=elapsed_ms,
            failed_records=problem_records,
            sql_preview=sql_preview,
        )