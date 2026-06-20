from datetime import datetime
from typing import Tuple, List, Dict, Any, Callable, Optional
import oracledb
from src.db_connection import DBConnection
from src.logger import LogManager


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

    def set_progress_callback(self, callback: Callable):
        self.progress_callback = callback

    def _report_progress(self, current: int, total: int, operation: str):
        if self.progress_callback:
            percentage = int((current / total) * 100) if total > 0 else 0
            self.progress_callback(current, total, percentage, operation)

    def backup_table(self, schema: str, table_name: str) -> Tuple[bool, str]:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{table_name}_BAK_{timestamp}"
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
            return False, str(e)

    def create_temp_table_multi_column(self, temp_schema: str, table_name: str, key_column: str, update_columns: List[str]) -> Tuple[bool, str]:
        """创建临时表，支持指定临时表的Schema
        
        Args:
            temp_schema: 临时表所在的Schema
            table_name: 目标表名（用于日志）
            key_column: 唯一标识列
            update_columns: 待更新列列表
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_name = f"TEMP_UPDATE_{timestamp}"
        self.temp_table_name = temp_name
        
        try:
            self.log.info(f"正在创建临时表 {temp_schema}.{temp_name}")
            
            column_defs = [f"{key_column} VARCHAR2(4000)"]
            for col in update_columns:
                column_defs.append(f"{col} VARCHAR2(4000)")
            
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
            return False, str(e)

    def import_excel_data_multi_column(self, temp_schema: str, key_column: str, update_columns: List[str], data_rows: List[Dict[str, Any]]) -> Tuple[bool, str, int]:
        """导入Excel数据到临时表
        
        Args:
            temp_schema: 临时表所在的Schema
            key_column: 唯一标识列
            update_columns: 待更新列列表
            data_rows: 数据行列表
        """
        self.log.info(f"正在导入Excel数据到临时表 {temp_schema}.{self.temp_table_name}，共 {len(data_rows)} 条")
        if not data_rows:
            return False, "没有数据可导入", 0
        
        try:
            all_columns = [key_column] + update_columns
            placeholders = [f":{i+1}" for i in range(len(all_columns))]
            insert_sql = f"INSERT INTO {temp_schema}.{self.temp_table_name} ({', '.join(all_columns)}) VALUES ({', '.join(placeholders)})"
            
            batch_size = 100
            imported_count = 0
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
            self.db.connection.rollback()
            return False, str(e), imported_count

    def execute_multi_column_update(self, target_schema: str, temp_schema: str, target_table: str, key_column: str, update_columns: List[str]) -> Tuple[int, int, List[Dict[str, Any]]]:
        """执行多列数据更新，支持目标表和临时表使用不同Schema
        
        Args:
            target_schema: 目标表所在的Schema
            temp_schema: 临时表所在的Schema
            target_table: 目标表名
            key_column: 唯一标识列
            update_columns: 待更新列列表
            
        Returns:
            Tuple[int, int, List[Dict]]: (成功数, 失败数, 失败记录列表)
            
        Note:
            - 空字段不更新（保留目标表原值）
            - 未匹配的key_value会被记录但不更新目标表
        """
        self.log.info("正在执行多列数据更新")
        self.log.info(f"目标表: {target_schema}.{target_table}, 临时表: {temp_schema}.{self.temp_table_name}")
        self.success_count = 0
        self.fail_count = 0
        failed_records = []
        unmatched_records = []  # 未匹配记录
        
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
                # 记录所有临时表key_value为未匹配
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
            
            batch_size = 50
            cursor = self.db.connection.cursor()
            
            for i in range(0, total_records, batch_size):
                batch = result[i:i + batch_size]
                for row_idx, row in enumerate(batch):
                    old_key = row[0]
                    matched_key_values.add(str(old_key))
                    
                    try:
                        # 构建更新参数，空字段不更新
                        params = {"key_value": old_key}
                        non_empty_columns = []
                        
                        for j, col in enumerate(update_columns):
                            # 获取临时表中的新值
                            # 行结构: key(0) | old值(1..len) | 当前值(len+1..2*len) | 新值(2*len+1..3*len)
                            new_value = row[len(update_columns) * 2 + 1 + j]
                            
                            # 只有非空值才更新（空字符串和None都不更新）
                            if new_value is not None and str(new_value).strip() != '':
                                non_empty_columns.append(col)
                                params[col] = new_value
                        
                        # 如果有非空字段需要更新，执行更新
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
                                # 记录跳过的空字段
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
                            # 所有字段都是空值，跳过更新但计入成功（匹配成功）
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
                
                self.db.connection.commit()
                
                processed = min(i + batch_size, total_records)
                self._report_progress(processed, total_records, "更新数据")
            
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
                for record in unmatched_records[:10]:  # 只显示前10条
                    self.log.warning(f"未匹配: key_value={record['key_value']}")
                if len(unmatched_records) > 10:
                    self.log.warning(f"... 还有 {len(unmatched_records) - 10} 条未匹配记录")
            
            self.log.success(f"更新完成，成功: {self.success_count}，失败: {self.fail_count}，未匹配: {len(unmatched_records)}")
            
            # 合并失败记录和未匹配记录
            all_problem_records = failed_records + unmatched_records
            
            return self.success_count, self.fail_count, all_problem_records
        except Exception as e:
            self.log.error(f"更新过程出错: {str(e)}")
            self.db.connection.rollback()
            return self.success_count, self.fail_count, failed_records

    def rollback(self, target_schema: str, temp_schema: str) -> Tuple[bool, str]:
        """回滚操作，从备份表恢复数据到目标表"""
        if not self.backup_created or not self.backup_table_name:
            self.log.warning("没有备份表，无需回滚")
            return True, "无需回滚"
        
        try:
            self.log.info("正在执行回滚操作...")
            
            # 1. 清理临时表
            if self.temp_table_name:
                self.cleanup_temp_table(temp_schema)
            
            # 2. 从备份表恢复数据到目标表
            self.log.info(f"正在从备份表 {target_schema}.{self.backup_table_name} 恢复数据")
            
            # 备份表名格式为 TABLE_NAME_BAK_timestamp，需要提取原表名
            backup_suffix = f"_BAK_"
            if backup_suffix in self.backup_table_name:
                original_table = self.backup_table_name.split(backup_suffix)[0]
            else:
                original_table = self.backup_table_name
            
            # 清空目标表
            truncate_target = f"DELETE FROM {target_schema}.{original_table}"
            success, _, error = self.db.execute_sql(truncate_target)
            if not success:
                self.log.error(f"清空目标表失败: {error}")
                return False, f"回滚失败: {error}"
            
            # 从备份表恢复数据
            restore_sql = f"INSERT INTO {target_schema}.{original_table} SELECT * FROM {target_schema}.{self.backup_table_name}"
            success, _, error = self.db.execute_sql(restore_sql)
            if not success:
                self.log.error(f"恢复数据失败: {error}")
                return False, f"回滚失败: {error}"
            
            self.log.success("回滚完成，数据已从备份表恢复")
            self.log.info(f"备份表 {target_schema}.{self.backup_table_name} 已保留供审计")
            
            return True, "回滚成功"
        except Exception as e:
            self.log.error(f"回滚过程出错: {str(e)}")
            return False, str(e)

    def cleanup_temp_table(self, temp_schema: str) -> bool:
        """清理临时表，支持指定临时表的Schema"""
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
            return False

    def cleanup_on_failure(self, temp_schema: str) -> bool:
        """失败时清理临时表"""
        self.log.info("正在清理失败状态下的临时表...")
        return self.cleanup_temp_table(temp_schema)

    def validate_table_and_columns_multi(self, schema: str, table_name: str, key_column: str, update_columns: List[str]) -> Tuple[bool, str]:
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
