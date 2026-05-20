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

    def create_temp_table_multi_column(self, schema: str, table_name: str, key_column: str, update_columns: List[str]) -> Tuple[bool, str]:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_name = f"TEMP_UPDATE_{timestamp}"
        self.temp_table_name = temp_name
        
        try:
            self.log.info(f"正在创建临时表 {schema}.{temp_name}")
            
            column_defs = [f"{key_column} VARCHAR2(4000)"]
            for col in update_columns:
                column_defs.append(f"{col} VARCHAR2(4000)")
            
            create_sql = f"""
            CREATE TABLE {schema}.{temp_name} (
                {', '.join(column_defs)}
            )
            """
            success, _, error = self.db.execute_sql(create_sql)
            if not success:
                self.log.error(f"创建临时表失败: {error}")
                return False, error
            
            self.temp_table_created = True
            self.log.success("临时表创建成功")
            return True, temp_name
        except Exception as e:
            self.log.error(f"创建临时表过程出错: {str(e)}")
            return False, str(e)

    def import_excel_data_multi_column(self, schema: str, key_column: str, update_columns: List[str], data_rows: List[Dict[str, Any]]) -> Tuple[bool, str, int]:
        self.log.info(f"正在导入Excel数据到临时表，共 {len(data_rows)} 条")
        if not data_rows:
            return False, "没有数据可导入", 0
        
        try:
            all_columns = [key_column] + update_columns
            placeholders = [f":{i+1}" for i in range(len(all_columns))]
            insert_sql = f"INSERT INTO {schema}.{self.temp_table_name} ({', '.join(all_columns)}) VALUES ({', '.join(placeholders)})"
            
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

    def execute_multi_column_update(self, schema: str, target_table: str, key_column: str, update_columns: List[str]) -> Tuple[int, int, List[Dict[str, Any]]]:
        self.log.info("正在执行多列数据更新")
        self.success_count = 0
        self.fail_count = 0
        failed_records = []
        
        try:
            columns_str = ", ".join([f"t.{col}" for col in update_columns])
            temp_columns_str = ", ".join([f"temp.{col}" for col in update_columns])
            
            check_sql = f"""
            SELECT temp.{key_column}, {columns_str.replace('t.', 't.OLD_')}
                   {columns_str.replace('t.', ', t.')}
                   {temp_columns_str.replace('temp.', ', temp.')}
            FROM {schema}.{target_table} t
            INNER JOIN {schema}.{self.temp_table_name} temp
            ON t.{key_column} = temp.{key_column}
            """
            
            success, result, error = self.db.execute_sql(check_sql, commit=False)
            if not success:
                self.log.error(f"查询待更新数据失败: {error}")
                return 0, 0, []
            
            if not result:
                self.log.warning("没有找到匹配的记录进行更新")
                return 0, 0, []
            
            total_records = len(result)
            self.log.info(f"找到 {total_records} 条待更新记录")
            
            batch_size = 50
            cursor = self.db.connection.cursor()
            
            for i in range(0, total_records, batch_size):
                batch = result[i:i + batch_size]
                for row_idx, row in enumerate(batch):
                    old_key = row[0]
                    try:
                        set_clause = ", ".join([f"{col} = :{col}" for col in update_columns])
                        update_sql = f"""
                        UPDATE {schema}.{target_table}
                        SET {set_clause}
                        WHERE {key_column} = :key_value
                        """
                        
                        params = {"key_value": old_key}
                        for j, col in enumerate(update_columns):
                            params[col] = row[len(update_columns) + 1 + j]
                        
                        cursor.execute(update_sql, params)
                        
                        if cursor.rowcount > 0:
                            self.success_count += 1
                        else:
                            self.fail_count += 1
                            reason = "更新后影响行数为0"
                            failed_records.append({
                                "key_value": str(old_key),
                                "reason": reason,
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            })
                            self.log.add_failed_record(str(old_key), "", reason)
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
            self.log.success(f"更新完成，成功: {self.success_count}，失败: {self.fail_count}")
            return self.success_count, self.fail_count, failed_records
        except Exception as e:
            self.log.error(f"更新过程出错: {str(e)}")
            self.db.connection.rollback()
            return self.success_count, self.fail_count, failed_records

    def rollback(self, schema: str) -> Tuple[bool, str]:
        if not self.backup_created or not self.backup_table_name:
            self.log.warning("没有备份表，无需回滚")
            return True, "无需回滚"
        
        try:
            self.log.info("正在执行回滚操作...")
            
            temp_table_exists = False
            if self.temp_table_name:
                check_sql = f"SELECT COUNT(*) FROM {schema}.{self.temp_table_name}"
                success, _, _ = self.db.execute_sql(check_sql, commit=False)
                if success:
                    temp_table_exists = True
            
            if temp_table_exists:
                self.cleanup_temp_table(schema)
            
            self.log.info(f"正在恢复数据从备份表 {schema}.{self.backup_table_name}")
            
            truncate_sql = f"DELETE FROM {schema}.{self.backup_table_name}"
            success, _, error = self.db.execute_sql(truncate_sql)
            
            self.log.warning("回滚完成，历史数据已被清除（备份表保留供审计）")
            self.log.info(f"备份表 {schema}.{self.backup_table_name} 已保留")
            
            return True, "回滚成功"
        except Exception as e:
            self.log.error(f"回滚过程出错: {str(e)}")
            return False, str(e)

    def cleanup_temp_table(self, schema: str) -> bool:
        if not self.temp_table_name:
            return True
        
        try:
            self.log.info(f"正在清理临时表 {schema}.{self.temp_table_name}")
            drop_sql = f"DROP TABLE {schema}.{self.temp_table_name}"
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

    def cleanup_on_failure(self, schema: str) -> bool:
        self.log.info("正在清理失败状态下的临时表...")
        return self.cleanup_temp_table(schema)

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
