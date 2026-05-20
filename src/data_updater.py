from datetime import datetime
from typing import Tuple, List, Dict, Any, Callable
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

    def backup_table(self, schema: str, table_name: str) -> Tuple[bool, str]:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%SS")
        backup_name = f"{table_name}_BAK_{timestamp}"
        self.backup_table_name = backup_name
        self.log.info(f"正在备份表 {schema}.{table_name} 到 {schema}.{backup_name}")
        create_sql = f"CREATE TABLE {schema}.{backup_name} AS SELECT * FROM {schema}.{table_name}"
        success, _, error = self.db.execute_sql(create_sql)
        if success:
            check_sql = f"SELECT COUNT(*) FROM {schema}.{backup_name}"
            success, result, error = self.db.execute_sql(check_sql, commit=False)
            if success and result:
                count = result[0][0]
                self.log.success(f"备份完成，共 {count} 条记录")
                return True, backup_name
            else:
                self.log.error(f"备份成功但无法获取记录数: {error}")
                return True, backup_name
        else:
            self.log.error(f"备份失败: {error}")
            return False, error

    def create_temp_table(self, schema: str, table_name: str, key_column: str, update_column: str) -> Tuple[bool, str]:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%SS")
        temp_name = f"TEMP_UPDATE_{timestamp}"
        self.temp_table_name = temp_name
        self.log.info(f"正在创建临时表 {schema}.{temp_name}")
        check_sql = f"SELECT COUNT(*) FROM {schema}.{temp_name}"
        success, result, _ = self.db.execute_sql(check_sql, commit=False)
        if success:
            self.log.info("临时表已存在，将清除数据")
            truncate_sql = f"TRUNCATE TABLE {schema}.{temp_name}"
            success, _, error = self.db.execute_sql(truncate_sql)
            if not success:
                self.log.error(f"清空临时表失败: {error}")
                return False, error
        else:
            create_sql = f"""
            CREATE TABLE {schema}.{temp_name} (
                {key_column} VARCHAR2(4000),
                {update_column} VARCHAR2(4000)
            )
            """
            success, _, error = self.db.execute_sql(create_sql)
            if not success:
                self.log.error(f"创建临时表失败: {error}")
                return False, error
        self.log.success("临时表创建成功")
        return True, temp_name

    def import_excel_data(self, schema: str, key_column: str, update_column: str, data_rows: List[Dict[str, Any]], progress_callback: Callable = None) -> Tuple[bool, str, int]:
        self.log.info(f"正在导入Excel数据到临时表，共 {len(data_rows)} 条")
        if not data_rows:
            return False, "没有数据可导入", 0
        insert_sql = f"INSERT INTO {schema}.{self.temp_table_name} ({key_column}, {update_column}) VALUES (:1, :2)"
        batch_size = 100
        imported_count = 0
        try:
            for i in range(0, len(data_rows), batch_size):
                batch = data_rows[i:i + batch_size]
                data_for_insert = [
                    (row["key_value"], row["update_value"])
                    for row in batch
                ]
                cursor = self.db.connection.cursor()
                cursor.executemany(insert_sql, data_for_insert)
                imported_count += len(batch)
                cursor.close()
                self.db.connection.commit()
                if progress_callback:
                    progress_callback(imported_count, len(data_rows), "导入Excel数据")
            self.log.success(f"导入完成，共 {imported_count} 条记录")
            return True, "", imported_count
        except Exception as e:
            self.log.error(f"导入数据失败: {str(e)}")
            self.db.connection.rollback()
            return False, str(e), imported_count

    def execute_update(self, schema: str, target_table: str, key_column: str, update_column: str, progress_callback: Callable = None) -> Tuple[int, int, List[Dict[str, Any]]]:
        self.log.info("正在执行数据更新")
        self.success_count = 0
        self.fail_count = 0
        failed_records = []
        try:
            check_sql = f"""
            SELECT t.{key_column}, t.{update_column}, temp.{update_column}
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
            update_sql = f"""
            UPDATE {schema}.{target_table} t
            SET t.{update_column} = (
                SELECT temp.{update_column}
                FROM {schema}.{self.temp_table_name} temp
                WHERE temp.{key_column} = t.{key_column}
            )
            WHERE EXISTS (
                SELECT 1 FROM {schema}.{self.temp_table_name} temp
                WHERE temp.{key_column} = t.{key_column}
            )
            """
            cursor = self.db.connection.cursor()
            batch_size = 100
            for i in range(0, total_records, batch_size):
                batch = result[i:i + batch_size]
                for row in batch:
                    old_key = row[0]
                    old_value = row[1]
                    new_value = row[2]
                    try:
                        single_update_sql = f"""
                        UPDATE {schema}.{target_table}
                        SET {update_column} = :new_value
                        WHERE {key_column} = :old_key
                        """
                        cursor.execute(single_update_sql, {"new_value": new_value, "old_key": old_key})
                        if cursor.rowcount > 0:
                            self.success_count += 1
                        else:
                            self.fail_count += 1
                            reason = "更新后影响行数为0"
                            failed_records.append({
                                "key_value": old_key,
                                "update_value": new_value,
                                "reason": reason,
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            })
                            self.log.add_failed_record(old_key, new_value, reason)
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
                            "key_value": old_key,
                            "update_value": new_value,
                            "reason": reason,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                        self.log.add_failed_record(old_key, new_value, reason)
                if i + batch_size < total_records:
                    self.db.connection.commit()
                if progress_callback:
                    progress_callback(i + len(batch), total_records, "更新数据")
            self.db.connection.commit()
            cursor.close()
            self.log.success(f"更新完成，成功: {self.success_count}，失败: {self.fail_count}")
            return self.success_count, self.fail_count, failed_records
        except Exception as e:
            self.log.error(f"更新过程出错: {str(e)}")
            self.db.connection.rollback()
            return self.success_count, self.fail_count, failed_records

    def cleanup_temp_table(self, schema: str) -> bool:
        if self.temp_table_name:
            self.log.info(f"正在清理临时表 {schema}.{self.temp_table_name}")
            drop_sql = f"DROP TABLE {schema}.{self.temp_table_name}"
            success, _, error = self.db.execute_sql(drop_sql)
            if success:
                self.log.success("临时表已清理")
                return True
            else:
                self.log.warning(f"清理临时表失败: {error}")
                return False
        return True

    def validate_table_and_columns(self, schema: str, table_name: str, key_column: str, update_column: str) -> Tuple[bool, str]:
        if not self.db.table_exists(table_name, schema):
            return False, f"表 {schema}.{table_name} 不存在"
        columns = self.db.get_columns(table_name)
        column_names = [col["name"].upper() for col in columns]
        if key_column.upper() not in column_names:
            return False, f"唯一标识列 '{key_column}' 不存在于表 {table_name} 中"
        if update_column.upper() not in column_names:
            return False, f"待修改列 '{update_column}' 不存在于表 {table_name} 中"
        return True, ""
