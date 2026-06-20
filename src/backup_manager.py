"""P3-4: 备份生命周期管理模块

提供 BackupManager 类，用于管理备份表的完整生命周期：
查找、统计、清理过期备份、从备份恢复数据。

依赖:
    - db_connection: DBConnection 用于数据库操作
    - errors: 异常类
"""

import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from src.errors import ConnectionError, BackupError, ValidationError


class BackupManager:
    """P3-4: 备份生命周期管理器

    管理备份表（匹配 *_BAK_* 模式）的完整生命周期，
    包括查找、统计、清理和恢复。

    Attributes:
        backup_pattern: 备份表名称匹配模式
    """

    # 备份表命名模式: 表名_BAK_时间戳
    _BAK_PATTERN = re.compile(
        r"^(.+)_BAK_(\d{8}_\d{6})$", re.IGNORECASE
    )

    def __init__(self):
        """初始化备份管理器。"""
        self.backup_pattern = self._BAK_PATTERN

    # ------------------------------------------------------------------
    # 备份查找
    # ------------------------------------------------------------------

    def list_backups(self, db: "DBConnection", schema: str = None) -> List[Dict[str, Any]]:
        """查找所有备份表（匹配 *_BAK_* 模式）。

        Args:
            db: DBConnection 实例
            schema: Schema 名称，默认使用当前用户

        Returns:
            List[Dict[str, Any]]: 备份表信息列表，每个元素包含:
                - table_name: 备份表名
                - source_table: 源表名
                - backup_timestamp: 备份时间戳
                - schema: 所属 schema

        Raises:
            ConnectionError: 数据库未连接
        """
        if db is None or not db.is_connected():
            raise ConnectionError("数据库未连接，无法查找备份表")

        # 获取所有用户表
        if schema:
            sql = """
                SELECT table_name FROM all_tables
                WHERE owner = :schema
                ORDER BY table_name
            """
            success, result, error = db.execute_sql(
                sql, {"schema": schema.upper()}, commit=False
            )
        else:
            sql = "SELECT table_name FROM user_tables ORDER BY table_name"
            success, result, error = db.execute_sql(sql, commit=False)

        if not success:
            raise BackupError(f"查询表列表失败: {error}")

        if result is None:
            return []

        backups = []
        for row in result:
            table_name = row[0]
            match = self._BAK_PATTERN.match(table_name)
            if match:
                source_table = match.group(1)
                timestamp_str = match.group(2)
                try:
                    backup_time = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                except ValueError:
                    backup_time = None

                backups.append({
                    "table_name": table_name,
                    "source_table": source_table,
                    "backup_timestamp": timestamp_str,
                    "backup_datetime": backup_time,
                    "schema": schema or "CURRENT_USER",
                })

        # 按备份时间倒序排列
        backups.sort(
            key=lambda b: b["backup_datetime"] or datetime.min,
            reverse=True
        )
        return backups

    # ------------------------------------------------------------------
    # 备份清理
    # ------------------------------------------------------------------

    def cleanup_old_backups(
        self,
        db: "DBConnection",
        schema: str = None,
        retention_days: int = 30,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """删除超过保留期限的备份表。

        Args:
            db: DBConnection 实例
            schema: Schema 名称
            retention_days: 保留天数，超过此天数的备份将被删除
            dry_run: 如果为 True，仅列出将要删除的备份而不实际执行

        Returns:
            Dict[str, Any]: 清理结果，包含:
                - deleted_count: 删除的备份表数量
                - deleted_tables: 被删除的表名列表
                - kept_count: 保留的备份表数量
                - retention_days: 保留天数
                - dry_run: 是否为预演模式

        Raises:
            ConnectionError: 数据库未连接
            ValidationError: 保留天数无效
        """
        if db is None or not db.is_connected():
            raise ConnectionError("数据库未连接，无法执行清理")

        if retention_days < 1:
            raise ValidationError(f"保留天数必须大于 0，当前值: {retention_days}")

        backups = self.list_backups(db, schema)
        cutoff_date = datetime.now() - timedelta(days=retention_days)

        to_delete = []
        to_keep = []

        for backup in backups:
            if backup["backup_datetime"] and backup["backup_datetime"] < cutoff_date:
                to_delete.append(backup)
            else:
                to_keep.append(backup)

        deleted_tables = []

        if not dry_run:
            for backup in to_delete:
                table_name = backup["table_name"]
                full_name = (
                    f"{schema}.{table_name}" if schema else table_name
                )
                sql = f"DROP TABLE {full_name} PURGE"
                success, _, error = db.execute_sql(sql, commit=True)
                if success:
                    deleted_tables.append(table_name)
                else:
                    # 记录失败但不中断，继续清理其他表
                    deleted_tables.append(f"{table_name} (失败: {error})")
        else:
            deleted_tables = [b["table_name"] for b in to_delete]

        return {
            "deleted_count": len(to_delete),
            "deleted_tables": deleted_tables,
            "kept_count": len(to_keep),
            "retention_days": retention_days,
            "dry_run": dry_run,
            "cutoff_date": cutoff_date.strftime("%Y-%m-%d %H:%M:%S"),
        }

    # ------------------------------------------------------------------
    # 备份统计
    # ------------------------------------------------------------------

    def get_backup_stats(
        self, db: "DBConnection", schema: str = None
    ) -> Dict[str, Any]:
        """获取备份表统计信息。

        统计备份表的数量、总大小、最早/最新备份时间等。

        Args:
            db: DBConnection 实例
            schema: Schema 名称

        Returns:
            Dict[str, Any]: 统计信息字典，包含:
                - total_backups: 备份表总数
                - total_size_mb: 备份表总大小 (MB)
                - oldest_backup: 最早备份信息
                - newest_backup: 最新备份信息
                - by_source_table: 按源表分组的统计
                - per_table_sizes: 每个备份表的大小

        Raises:
            ConnectionError: 数据库未连接
        """
        if db is None or not db.is_connected():
            raise ConnectionError("数据库未连接，无法获取统计信息")

        backups = self.list_backups(db, schema)

        if not backups:
            return {
                "total_backups": 0,
                "total_size_mb": 0.0,
                "oldest_backup": None,
                "newest_backup": None,
                "by_source_table": {},
                "per_table_sizes": [],
            }

        # 查询每个备份表的大小
        per_table_sizes = []
        total_size_bytes = 0

        for backup in backups:
            table_name = backup["table_name"]
            size_bytes = self._get_table_size(db, table_name, schema)
            total_size_bytes += size_bytes
            per_table_sizes.append({
                "table_name": table_name,
                "size_mb": round(size_bytes / (1024 * 1024), 4),
                "source_table": backup["source_table"],
                "backup_datetime": (
                    backup["backup_datetime"].strftime("%Y-%m-%d %H:%M:%S")
                    if backup["backup_datetime"] else None
                ),
            })

        # 按源表分组统计
        by_source_table = {}
        for backup in backups:
            src = backup["source_table"]
            if src not in by_source_table:
                by_source_table[src] = {"count": 0, "total_size_mb": 0.0}
            by_source_table[src]["count"] += 1

        for ps in per_table_sizes:
            by_source_table[ps["source_table"]]["total_size_mb"] += ps["size_mb"]

        # 计算最早和最新备份
        valid_backups = [b for b in backups if b["backup_datetime"] is not None]
        oldest = valid_backups[-1] if valid_backups else None
        newest = valid_backups[0] if valid_backups else None

        return {
            "total_backups": len(backups),
            "total_size_mb": round(total_size_bytes / (1024 * 1024), 4),
            "oldest_backup": {
                "table_name": oldest["table_name"],
                "backup_time": oldest["backup_datetime"].strftime("%Y-%m-%d %H:%M:%S"),
                "source_table": oldest["source_table"],
            } if oldest else None,
            "newest_backup": {
                "table_name": newest["table_name"],
                "backup_time": newest["backup_datetime"].strftime("%Y-%m-%d %H:%M:%S"),
                "source_table": newest["source_table"],
            } if newest else None,
            "by_source_table": by_source_table,
            "per_table_sizes": per_table_sizes,
        }

    def _get_table_size(
        self, db: "DBConnection", table_name: str, schema: str = None
    ) -> int:
        """查询单个表的大小（字节）。

        Args:
            db: DBConnection 实例
            table_name: 表名
            schema: Schema 名称

        Returns:
            int: 表大小（字节），查询失败返回 0
        """
        if schema:
            sql = """
                SELECT NVL(SUM(bytes), 0)
                FROM dba_segments
                WHERE owner = :schema AND segment_name = :table_name
            """
            params = {"schema": schema.upper(), "table_name": table_name.upper()}
        else:
            sql = """
                SELECT NVL(SUM(bytes), 0)
                FROM user_segments
                WHERE segment_name = :table_name
            """
            params = {"table_name": table_name.upper()}

        success, result, _ = db.execute_sql(sql, params, commit=False)
        if success and result and result[0][0] is not None:
            return int(result[0][0])
        return 0

    # ------------------------------------------------------------------
    # 从备份恢复
    # ------------------------------------------------------------------

    def restore_from_backup(
        self,
        db: "DBConnection",
        schema: str,
        backup_table: str,
        target_table: str,
        truncate_target: bool = True,
    ) -> Dict[str, Any]:
        """从备份表恢复数据到目标表。

        使用 INSERT INTO ... SELECT FROM 方式将备份数据恢复到目标表。
        如果 truncate_target=True，会先清空目标表。

        Args:
            db: DBConnection 实例
            schema: Schema 名称
            backup_table: 备份表名
            target_table: 目标表名（要恢复到的表）
            truncate_target: 是否先清空目标表

        Returns:
            Dict[str, Any]: 恢复结果，包含:
                - success: 是否成功
                - rows_restored: 恢复的行数
                - backup_table: 备份表名
                - target_table: 目标表名
                - truncated: 是否已清空目标表

        Raises:
            ConnectionError: 数据库未连接
            BackupError: 恢复失败
            ValidationError: 表名无效
        """
        if db is None or not db.is_connected():
            raise ConnectionError("数据库未连接，无法执行恢复")

        # 验证备份表存在
        if not db.table_exists(backup_table, schema):
            raise ValidationError(f"备份表不存在: {schema}.{backup_table}")

        # 验证目标表存在
        if not db.table_exists(target_table, schema):
            raise ValidationError(f"目标表不存在: {schema}.{target_table}")

        full_backup = f"{schema}.{backup_table}"
        full_target = f"{schema}.{target_table}"

        rows_restored = 0
        truncated = False

        try:
            # 截断目标表
            if truncate_target:
                truncate_sql = f"TRUNCATE TABLE {full_target}"
                success, _, error = db.execute_sql(truncate_sql, commit=True)
                if not success:
                    raise BackupError(f"清空目标表失败: {error}")
                truncated = True

            # 获取备份表和目标表的列信息
            backup_columns = db.get_columns(backup_table)
            target_columns = db.get_columns(target_table)

            backup_col_names = {col["name"].upper() for col in backup_columns}
            target_col_names = {col["name"].upper() for col in target_columns}

            # 找出两表共有的列
            common_columns = sorted(backup_col_names & target_col_names)
            if not common_columns:
                raise BackupError("备份表和目标表没有共同的列，无法恢复")

            col_list = ", ".join(common_columns)

            # 从备份插入到目标
            insert_sql = (
                f"INSERT INTO {full_target} ({col_list}) "
                f"SELECT {col_list} FROM {full_backup}"
            )
            success, _, error = db.execute_sql(insert_sql, commit=True)
            if not success:
                raise BackupError(f"恢复数据失败: {error}")

            # 获取恢复的行数
            count_sql = f"SELECT COUNT(*) FROM {full_backup}"
            success, result, error = db.execute_sql(count_sql, commit=False)
            if success and result:
                rows_restored = result[0][0]

            return {
                "success": True,
                "rows_restored": rows_restored,
                "backup_table": full_backup,
                "target_table": full_target,
                "truncated": truncated,
                "columns_restored": common_columns,
            }

        except BackupError:
            raise
        except Exception as e:
            raise BackupError(f"恢复过程中发生异常: {str(e)}")

    # ------------------------------------------------------------------
    # 清理计划
    # ------------------------------------------------------------------

    def schedule_cleanup(
        self,
        db: "DBConnection",
        schema: str = None,
        retention_days: int = 30,
    ) -> Dict[str, Any]:
        """返回建议的清理计划。

        不实际执行删除，仅返回将要清理的备份列表和统计信息。

        Args:
            db: DBConnection 实例
            schema: Schema 名称
            retention_days: 保留天数

        Returns:
            Dict[str, Any]: 清理计划，包含:
                - plan: 建议的清理计划描述
                - to_delete: 将删除的备份列表
                - total_size_to_free_mb: 将释放的空间 (MB)
                - recommended_action: 建议的操作

        Raises:
            ConnectionError: 数据库未连接
        """
        if db is None or not db.is_connected():
            raise ConnectionError("数据库未连接，无法生成清理计划")

        # 先执行 dry_run 获取待删除列表
        dry_result = self.cleanup_old_backups(
            db, schema, retention_days, dry_run=True
        )

        # 计算将释放的空间
        total_size_to_free = 0.0
        to_delete_details = []

        for table_name in dry_result["deleted_tables"]:
            size_bytes = self._get_table_size(db, table_name, schema)
            size_mb = size_bytes / (1024 * 1024)
            total_size_to_free += size_mb
            to_delete_details.append({
                "table_name": table_name,
                "size_mb": round(size_mb, 4),
            })

        plan_lines = [
            f"备份清理计划",
            f"  保留期限: {retention_days} 天",
            f"  截止日期: {dry_result['cutoff_date']}",
            f"  将删除:   {len(dry_result['deleted_tables'])} 个备份表",
            f"  将保留:   {dry_result['kept_count']} 个备份表",
            f"  释放空间: {total_size_to_free:.2f} MB",
        ]

        if dry_result["deleted_count"] == 0:
            recommended = "无需清理，所有备份均在保留期限内。"
        elif total_size_to_free > 100:
            recommended = (
                f"建议执行清理，可释放 {total_size_to_free:.2f} MB 空间。"
            )
        else:
            recommended = (
                f"可考虑清理，将释放 {total_size_to_free:.2f} MB 空间。"
            )

        return {
            "plan": "\n".join(plan_lines),
            "to_delete": to_delete_details,
            "total_size_to_free_mb": round(total_size_to_free, 4),
            "retention_days": retention_days,
            "recommended_action": recommended,
        }