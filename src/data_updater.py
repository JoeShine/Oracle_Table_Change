import threading
import traceback
from datetime import datetime
from typing import Tuple, List, Dict, Any, Callable, Optional
import oracledb
from src.db_connection import DBConnection
from src.logger import LogManager
from src.security import sanitize_identifier, sanitize_identifier_list, validate_schema
from src.errors import (
    BackupError, ValidationError, SQLExecutionError, RollbackError,
    ImportError as ImportErrorEx, CancelledError
)
from src.progress import ProgressTracker


class DataUpdater:
    def __init__(self, db_connection: DBConnection, log_manager: LogManager):
        self.db = db_connection
        self.log = log_manager
        self.temp_table_name = None
        self.backup_table_name = None
        self.success_count = 0
        self.fail_count = 0
        self.backup_created = False
        self.temp_table_created = False
        self.progress_callback = None
        self.progress_tracker = ProgressTracker()
        # P0-4: 单事务模式 — 整个更新操作在一个事务中完成
        self._use_single_transaction = True
        # P1-10: 取消机制 — 可随时取消正在执行的更新操作
        self.cancel_event = threading.Event()

    def set_progress_callback(self, callback: Callable):
        self.progress_callback = callback

    def _report_progress(self, current: int, total: int, operation: str):
        """P2-3: 使用 ProgressTracker 计算 ETA 并回调"""
        if self.progress_callback:
            percentage = int((current / total) * 100) if total > 0 else 0
            eta = self.progress_tracker.update(current, total)
            try:
                self.progress_callback(current, total, percentage, operation, eta)
            except TypeError:
                # 向后兼容: 回调函数不接受 eta 参数
                self.progress_callback(current, total, percentage, operation)

    def cancel(self):
        """P1-10: 取消正在执行的更新操作"""
        self.cancel_event.set()
        self.log.warning("收到取消请求，正在中止当前操作...")

    # ------------------------------------------------------------------
    # P1-2: 列类型推断辅助函数
    # ------------------------------------------------------------------

    @staticmethod
    def _map_oracle_type_to_temp_type(data_type: str, data_length: int) -> str:
        """将目标表的 Oracle 列类型映射为临时表列类型。

        Args:
            data_type: Oracle 列类型 (如 VARCHAR2, NUMBER, DATE 等)
            data_length: 列数据长度

        Returns:
            临时表列定义字符串 (如 "VARCHAR2(4000)", "NUMBER", "DATE")
        """
        dt = data_type.upper() if data_type else ""

        if dt in ('VARCHAR2', 'NVARCHAR2', 'CHAR', 'NCHAR'):
            length = data_length if data_length and data_length > 0 else 4000
            return f"VARCHAR2({length})"
        elif dt in ('NUMBER', 'INTEGER', 'FLOAT', 'BINARY_FLOAT', 'BINARY_DOUBLE'):
            return "NUMBER"
        elif dt in ('DATE', 'TIMESTAMP', 'TIMESTAMP WITH TIME ZONE',
                     'TIMESTAMP WITH LOCAL TIME ZONE'):
            return "DATE"
        elif dt in ('CLOB', 'NCLOB', 'LONG'):
            return "CLOB"
        else:
            return "VARCHAR2(4000)"

    # ------------------------------------------------------------------
    # P0-1: SQL 注入防御 — 所有标识符在使用前均通过 sanitize 校验
    # ------------------------------------------------------------------

    def backup_table(self, schema: str, table_name: str) -> Tuple[bool, str]:
        """备份目标表，使用 P0-1 安全校验"""
        schema = validate_schema(schema, "backup_table.schema")
        table_name = sanitize_identifier(table_name, "backup_table.table_name")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{table_name}_BAK_{timestamp}"
        sanitize_identifier(backup_name, "backup_table.backup_name")
        self.backup_table_name = backup_name
        self.log.info(f"正在备份表 {schema}.{table_name} 到 {schema}.{backup_name}")
        try:
            create_sql = f"CREATE TABLE {schema}.{backup_name} AS SELECT * FROM {schema}.{table_name}"
            success, _, error = self.db.execute_sql(create_sql)
            if success:
                check_sql = f"SELECT COUNT(*) FROM {schema}.{backup_name}"
                success, result, error = self.db.execute_sql(check_sql, commit=False)
                if success and result:
                    count = result[0][0]
                    self.log.success(f"备份完成，共 {count} 条记录")
                    self.backup_created = True
                    return True, backup_name
                else:
                    self.log.info(f"备份成功但无法获取记录数: {error}")
                    self.backup_created = True
                    return True, backup_name
            else:
                self.log.error(f"备份失败: {error}")
                return False, error
        except Exception as e:
            self.log.error(f"备份过程出错: {str(e)}")
            self.log.error(f"Traceback: {traceback.format_exc()}")
            return False, str(e)

    def create_temp_table_multi_column(self, temp_schema: str, table_name: str, key_column: str, update_columns: List[str]) -> Tuple[bool, str]:
        """创建临时表，支持指定临时表的Schema

        P0-1: 所有标识符均通过安全校验
        P1-2: 从目标表推断列类型，而非统一 VARCHAR2(4000)
        """
        temp_schema = validate_schema(temp_schema, "create_temp.temp_schema")
        key_column = sanitize_identifier(key_column, "create_temp.key_column")
        update_columns = sanitize_identifier_list(update_columns, "create_temp.update_columns")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_name = f"TEMP_UPDATE_{timestamp}"
        sanitize_identifier(temp_name, "create_temp.temp_name")
        self.temp_table_name = temp_name

        try:
            self.log.info(f"正在创建临时表 {temp_schema}.{temp_name}")

            # P1-2: 从目标表获取真实列类型，构建类型映射
            target_columns = self.db.get_columns(table_name)
            type_map = {}
            for col_info in target_columns:
                col_name = col_info.get("name", "").upper()
                type_map[col_name] = self._map_oracle_type_to_temp_type(
                    col_info.get("type", ""),
                    col_info.get("length", 0)
                )

            # 构建列定义：key_column 和 update_columns 均从类型映射推断
            all_columns = [key_column] + update_columns
            column_defs = []
            for col in all_columns:
                col_type = type_map.get(col.upper(), "VARCHAR2(4000)")
                column_defs.append(f"{col} {col_type}")

            create_sql = f"""
            CREATE TABLE {temp_schema}.{temp_name} (
                {', '.join(column_defs)}
            )
            """
            success, _, error = self.db.execute_sql(create_sql)
            if not success:
                self.log.error(f"创建临时表失败: {error}")
                return False, error

            self.temp_table_created = True
            self.log.success(f"临时表创建成功: {temp_schema}.{temp_name}")
            return True, temp_name
        except Exception as e:
            self.log.error(f"创建临时表过程出错: {str(e)}")
            self.log.error(f"Traceback: {traceback.format_exc()}")
            return False, str(e)

    def import_excel_data_multi_column(self, temp_schema: str, key_column: str, update_columns: List[str], data_rows: List[Dict[str, Any]]) -> Tuple[bool, str, int]:
        """导入Excel数据到临时表

        P0-1: 所有标识符均通过安全校验
        """
        temp_schema = validate_schema(temp_schema, "import_excel.temp_schema")
        key_column = sanitize_identifier(key_column, "import_excel.key_column")
        update_columns = sanitize_identifier_list(update_columns, "import_excel.update_columns")

        self.log.info(f"正在导入Excel数据到临时表 {temp_schema}.{self.temp_table_name}，共 {len(data_rows)} 条")
        if not data_rows:
            return False, "没有数据可导入", 0

        imported_count = 0
        try:
            all_columns = [key_column] + update_columns
            placeholders = [f":{i+1}" for i in range(len(all_columns))]
            insert_sql = f"INSERT INTO {temp_schema}.{self.temp_table_name} ({', '.join(all_columns)}) VALUES ({', '.join(placeholders)})"

            batch_size = 100
            total = len(data_rows)

            cursor = self.db.connection.cursor()
            for i in range(0, len(data_rows), batch_size):
                batch = data_rows[i:i + batch_size]
                data_for_insert = []
                for row in batch:
                    row_values = [row.get("key_value")]
                    for col in update_columns:
                        row_values.append(row.get(col))
                    data_for_insert.append(tuple(row_values))

                cursor.executemany(insert_sql, data_for_insert)
                imported_count += len(batch)
                self.db.connection.commit()

                self._report_progress(imported_count, total, "导入Excel数据")

            cursor.close()
            self.log.success(f"导入完成，共 {imported_count} 条记录")
            return True, "", imported_count
        except Exception as e:
            self.log.error(f"导入数据失败: {str(e)}")
            self.log.error(f"Traceback: {traceback.format_exc()}")
            try:
                self.db.connection.rollback()
            except Exception:
                pass
            return False, str(e), imported_count

    def execute_multi_column_update(self, target_schema: str, temp_schema: str, target_table: str, key_column: str, update_columns: List[str]) -> Tuple[int, int, List[Dict[str, Any]]]:
        """执行多列数据更新，支持目标表和临时表使用不同Schema

        P0-1: 所有标识符均通过安全校验
        P0-4: 单事务模式 — 整个更新在单一事务中完成，失败由 connection.rollback() 天然恢复
        P1-10: 支持通过 cancel() 方法取消操作

        Args:
            target_schema: 目标表所在的Schema
            temp_schema: 临时表所在的Schema
            target_table: 目标表名
            key_column: 唯一标识列
            update_columns: 待更新列列表

        Returns:
            Tuple[int, int, List[Dict]]: (成功数, 失败数, 失败记录列表)
        """
        # P1-10: 重置取消事件
        self.cancel_event.clear()

        # P0-1: 安全校验
        target_schema = validate_schema(target_schema, "execute_update.target_schema")
        temp_schema = validate_schema(temp_schema, "execute_update.temp_schema")
        target_table = sanitize_identifier(target_table, "execute_update.target_table")
        key_column = sanitize_identifier(key_column, "execute_update.key_column")
        update_columns = sanitize_identifier_list(update_columns, "execute_update.update_columns")

        self.log.info("正在执行多列数据更新")
        self.log.info(f"目标表: {target_schema}.{target_table}, 临时表: {temp_schema}.{self.temp_table_name}")
        self.success_count = 0
        self.fail_count = 0
        failed_records = []
        unmatched_records = []

        try:
            # 1. 获取临时表中所有key_value（用于检测未匹配记录）
            temp_keys_sql = f"SELECT {key_column} FROM {temp_schema}.{self.temp_table_name}"
            success, temp_keys_result, error = self.db.execute_sql(temp_keys_sql, commit=False)
            if not success:
                self.log.error(f"获取临时表key_value失败: {error}")
                return 0, 0, []

            temp_key_values = set()
            for row in temp_keys_result:
                key_val = row[0]
                if key_val is not None:
                    temp_key_values.add(str(key_val))

            self.log.info(f"临时表中共有 {len(temp_key_values)} 个key_value")

            # 2. 查询匹配的记录进行更新
            columns_str = ", ".join([f"t.{col}" for col in update_columns])
            old_columns_str = ", ".join([f"t.{col} AS OLD_{col}" for col in update_columns])
            temp_columns_str = ", ".join([f"temp.{col}" for col in update_columns])

            check_sql = f"""
            SELECT temp.{key_column}, {old_columns_str},
                   {columns_str},
                   {temp_columns_str}
            FROM {target_schema}.{target_table} t
            INNER JOIN {temp_schema}.{self.temp_table_name} temp
            ON t.{key_column} = temp.{key_column}
            """

            success, result, error = self.db.execute_sql(check_sql, commit=False)
            if not success:
                self.log.error(f"查询待更新数据失败: {error}")
                return 0, 0, []

            if not result:
                self.log.warning("没有找到匹配的记录进行更新")
                for key_val in temp_key_values:
                    unmatched_records.append({
                        "key_value": key_val,
                        "reason": "目标表中不存在此key_value",
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                self.log.warning(f"所有 {len(unmatched_records)} 条记录未匹配")
                return 0, 0, unmatched_records

            matched_key_values = set()
            total_records = len(result)
            self.log.info(f"找到 {total_records} 条匹配记录待更新")

            # P0-4: 单事务模式 — 统一使用一个 cursor，不中途 commit
            cursor = self.db.connection.cursor()

            for row_idx, row in enumerate(result):
                old_key = row[0]
                matched_key_values.add(str(old_key))

                try:
                    # 构建更新参数，空字段不更新
                    params = {"key_value": old_key}
                    non_empty_columns = []

                    for j, col in enumerate(update_columns):
                        # 行结构: key(0) | old值(1..len) | 当前值(len+1..2*len) | 新值(2*len+1..3*len)
                        new_value = row[len(update_columns) * 2 + 1 + j]

                        # 只有非空值才更新（空字符串和None都不更新）
                        if new_value is not None and str(new_value).strip() != '':
                            non_empty_columns.append(col)
                            params[col] = new_value

                    if non_empty_columns:
                        set_clause = ", ".join([f"{col} = :{col}" for col in non_empty_columns])
                        update_sql = f"""
                        UPDATE {target_schema}.{target_table}
                        SET {set_clause}
                        WHERE {key_column} = :key_value
                        """

                        cursor.execute(update_sql, params)

                        if cursor.rowcount > 0:
                            self.success_count += 1
                            skipped_columns = [col for col in update_columns if col not in non_empty_columns]
                            if skipped_columns:
                                self.log.info(f"key_value={old_key}: 跳过空字段 {', '.join(skipped_columns)}")
                        else:
                            self.fail_count += 1
                            reason = "更新后影响行数为0"
                            failed_records.append({
                                "key_value": str(old_key),
                                "reason": reason,
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            })
                            self.log.add_failed_record(str(old_key), "", reason)
                    else:
                        self.success_count += 1
                        self.log.info(f"key_value={old_key}: 所有字段为空，跳过更新")

                except oracledb.DatabaseError as e:
                    self.fail_count += 1
                    error_msg = str(e)
                    if "ORA-01722" in error_msg:
                        reason = "数据类型不匹配"
                    elif "ORA-01407" in error_msg:
                        reason = "无法设置为NULL（列可能不允许NULL）"
                    else:
                        reason = error_msg
                    failed_records.append({
                        "key_value": str(old_key),
                        "reason": reason,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    self.log.add_failed_record(str(old_key), "", reason)
                except Exception as e:
                    self.fail_count += 1
                    reason = str(e)
                    failed_records.append({
                        "key_value": str(old_key),
                        "reason": reason,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    self.log.add_failed_record(str(old_key), "", reason)

                # 进度汇报
                if (row_idx + 1) % 50 == 0 or row_idx == total_records - 1:
                    self._report_progress(row_idx + 1, total_records, "更新数据")

                # P1-10: 检查取消事件
                if self.cancel_event.is_set():
                    self.log.warning("操作已被用户取消，正在回滚...")
                    try:
                        self.db.connection.rollback()
                    except Exception:
                        pass
                    raise CancelledError("操作已被用户取消")

            # P0-4: 单事务模式 — 所有更新完成后一次性 commit
            self.db.connection.commit()
            cursor.close()

            # 3. 记录未匹配的key_value
            unmatched_key_values = temp_key_values - matched_key_values
            for key_val in unmatched_key_values:
                unmatched_records.append({
                    "key_value": key_val,
                    "reason": "目标表中不存在此key_value",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

            if unmatched_records:
                self.log.warning(f"有 {len(unmatched_records)} 条记录未匹配（Excel中存在但目标表中不存在）")
                for record in unmatched_records[:10]:
                    self.log.warning(f"未匹配: key_value={record['key_value']}")
                if len(unmatched_records) > 10:
                    self.log.warning(f"... 还有 {len(unmatched_records) - 10} 条未匹配记录")

            self.log.success(f"更新完成，成功: {self.success_count}，失败: {self.fail_count}，未匹配: {len(unmatched_records)}")

            all_problem_records = failed_records + unmatched_records
            return self.success_count, self.fail_count, all_problem_records

        except Exception as e:
            self.log.error(f"更新过程出错: {str(e)}")
            self.log.error(f"Traceback: {traceback.format_exc()}")
            # P0-4: 单事务 — 失败时由 connection.rollback() 天然恢复
            try:
                self.db.connection.rollback()
                self.log.info("事务已回滚，备份表已保留供人工恢复")
            except Exception:
                pass
            return self.success_count, self.fail_count, failed_records

    def execute_merge_update(self, target_schema: str, temp_schema: str, target_table: str,
                              key_column: str, update_columns: List[str]) -> Tuple[int, int, List[Dict[str, Any]]]:
        """P1-1: 使用 MERGE INTO 一次性完成全部更新，性能 10x~100x 提升。

        与 execute_multi_column_update 不同，这个方法使用单条 MERGE INTO SQL
        替代逐行 UPDATE，大幅减少网络往返。空字段不更新由 CASE WHEN 处理。
        P1-10: 支持通过 cancel() 方法取消操作。
        """
        # P1-10: 重置取消事件
        self.cancel_event.clear()

        target_schema = validate_schema(target_schema, "merge_update.target_schema")
        temp_schema = validate_schema(temp_schema, "merge_update.temp_schema")
        target_table = sanitize_identifier(target_table, "merge_update.target_table")
        key_column = sanitize_identifier(key_column, "merge_update.key_column")
        update_columns = sanitize_identifier_list(update_columns, "merge_update.update_columns")

        self.log.info("正在使用 MERGE INTO 模式执行批量更新")
        self.success_count = 0
        self.fail_count = 0
        failed_records = []
        unmatched_records = []

        try:
            # 1. 获取临时表中所有 key_value
            temp_keys_sql = f"SELECT {key_column} FROM {temp_schema}.{self.temp_table_name}"
            success, temp_keys_result, error = self.db.execute_sql(temp_keys_sql, commit=False)
            temp_key_values = set()
            if success and temp_keys_result:
                for row in temp_keys_result:
                    if row[0] is not None:
                        temp_key_values.add(str(row[0]))

            self.log.info(f"临时表中共有 {len(temp_key_values)} 个 key_value")

            # 2. 构建 MERGE INTO 语句
            # SET 子句: 空字段保留原值
            set_clauses = []
            for col in update_columns:
                set_clauses.append(
                    f"t.{col} = CASE WHEN s.{col} IS NOT NULL AND TRIM(s.{col}) != '' "
                    f"THEN s.{col} ELSE t.{col} END"
                )

            merge_sql = f"""
            MERGE INTO {target_schema}.{target_table} t
            USING {temp_schema}.{self.temp_table_name} s
            ON (t.{key_column} = s.{key_column})
            WHEN MATCHED THEN UPDATE SET
                {', '.join(set_clauses)}
            """

            self.log.info(f"MERGE SQL: {merge_sql[:200]}...")

            # 3. 执行 MERGE
            cursor = self.db.connection.cursor()
            cursor.execute(merge_sql)
            merged_count = cursor.rowcount
            self.db.connection.commit()
            cursor.close()

            self.success_count = merged_count if merged_count else 0
            self.log.success(f"MERGE 完成，更新 {self.success_count} 条记录")

            # 4. 检测未匹配记录
            if self.success_count < len(temp_key_values):
                # 找出未匹配的 key_value
                target_vals_sql = f"SELECT {key_column} FROM {target_schema}.{target_table}"
                _, target_vals_result, _ = self.db.execute_sql(target_vals_sql, commit=False)
                target_key_values = set()
                if target_vals_result:
                    for row in target_vals_result:
                        if row[0] is not None:
                            target_key_values.add(str(row[0]))

                unmatched = temp_key_values - target_key_values
                for key_val in unmatched:
                    unmatched_records.append({
                        "key_value": key_val,
                        "reason": "目标表中不存在此key_value",
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                if unmatched_records:
                    self.log.warning(f"有 {len(unmatched_records)} 条记录未匹配")

            all_problem_records = failed_records + unmatched_records
            return self.success_count, self.fail_count, all_problem_records

        except Exception as e:
            self.log.error(f"MERGE 更新出错: {str(e)}")
            self.log.error(f"Traceback: {traceback.format_exc()}")
            try:
                self.db.connection.rollback()
                self.log.info("事务已回滚")
            except Exception:
                pass
            return self.success_count, self.fail_count, failed_records

    def rollback(self, target_schema: str, temp_schema: str) -> Tuple[bool, str]:
        """回滚操作 — P0-4 修复：不再使用 DELETE+INSERT 恢复

        新行为：
        - 如果在单事务模式中操作失败，connection.rollback() 已自动恢复
        - 本方法仅清理临时表，备份表保留供审计
        - 如需从备份表恢复数据，需人工在 SQL*Plus 中执行
        """
        target_schema = validate_schema(target_schema, "rollback.target_schema")
        temp_schema = validate_schema(temp_schema, "rollback.temp_schema")

        if not self.backup_created or not self.backup_table_name:
            self.log.warning("没有备份表，无需回滚")
            return True, "无需回滚"

        try:
            self.log.info("正在执行回滚操作...")

            # 1. 清理临时表
            if self.temp_table_name:
                self.cleanup_temp_table(temp_schema)

            # 2. 备份表保留供审计，提示用户
            self.log.success(
                f"回滚完成。备份表 {target_schema}.{self.backup_table_name} 已保留。"
                f"如上次操作已 commit，需从备份表手动恢复数据："
                f"INSERT INTO {target_schema}.<原表名> SELECT * FROM {target_schema}.{self.backup_table_name}"
            )

            return True, f"回滚完成，备份表 {target_schema}.{self.backup_table_name} 已保留供审计"

        except Exception as e:
            self.log.error(f"回滚过程出错: {str(e)}")
            self.log.error(f"Traceback: {traceback.format_exc()}")
            return False, str(e)

    def cleanup_temp_table(self, temp_schema: str) -> bool:
        """清理临时表，支持指定临时表的Schema"""
        temp_schema = validate_schema(temp_schema, "cleanup_temp.temp_schema")
        if not self.temp_table_name:
            return True

        try:
            self.log.info(f"正在清理临时表 {temp_schema}.{self.temp_table_name}")
            drop_sql = f"DROP TABLE {temp_schema}.{self.temp_table_name}"
            success, _, error = self.db.execute_sql(drop_sql)
            if success:
                self.log.success("临时表已清理")
                self.temp_table_created = False
                return True
            else:
                self.log.warning(f"清理临时表失败: {error}")
                return False
        except Exception as e:
            self.log.error(f"清理临时表出错: {str(e)}")
            self.log.error(f"Traceback: {traceback.format_exc()}")
            return False

    def cleanup_on_failure(self, temp_schema: str) -> bool:
        """失败时清理临时表"""
        self.log.info("正在清理失败状态下的临时表...")
        return self.cleanup_temp_table(temp_schema)

    def validate_table_and_columns_multi(self, schema: str, table_name: str, key_column: str, update_columns: List[str]) -> Tuple[bool, str]:
        """P0-1: 校验表与列（含安全校验）"""
        schema = validate_schema(schema, "validate.target_schema")
        table_name = sanitize_identifier(table_name, "validate.table_name")
        key_column = sanitize_identifier(key_column, "validate.key_column")
        update_columns = sanitize_identifier_list(update_columns, "validate.update_columns")

        if not self.db.table_exists(table_name, schema):
            return False, f"表 {schema}.{table_name} 不存在"

        columns = self.db.get_columns(table_name)
        column_names = [col["name"].upper() for col in columns]

        if key_column.upper() not in column_names:
            return False, f"唯一标识列 '{key_column}' 不存在于表 {table_name} 中"

        missing_columns = []
        for col in update_columns:
            if col.upper() not in column_names:
                missing_columns.append(col)

        if missing_columns:
            return False, f"待修改列 '{', '.join(missing_columns)}' 不存在于表 {table_name} 中"

        return True, ""

    def get_backup_info(self) -> Optional[Dict[str, Any]]:
        if not self.backup_created:
            return None
        return {
            "backup_table_name": self.backup_table_name,
            "backup_created": self.backup_created
        }