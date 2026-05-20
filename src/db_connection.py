import oracledb
from typing import Optional, Dict, Any, List


class DBConnection:
    def __init__(self):
        self.connection = None
        self.connection_info = None

    def connect(self, host: str, port: int, service: str, username: str, password: str) -> tuple[bool, str]:
        try:
            dsn = oracledb.makedsn(host, port, service_name=service)
            self.connection = oracledb.connect(user=username, password=password, dsn=dsn)
            self.connection_info = {
                "host": host,
                "port": port,
                "service": service,
                "username": username
            }
            return True, "连接成功"
        except oracledb.DatabaseError as e:
            error = str(e)
            if "ORA-12541" in error:
                return False, f"连接失败: TNS无监听程序，请检查主机地址和端口"
            elif "ORA-12514" in error:
                return False, f"连接失败: TNS监听程序无法识别服务名，请检查服务名"
            elif "ORA-01017" in error:
                return False, f"连接失败: 用户名或密码无效"
            elif "ORA-12154" in error:
                return False, f"连接失败: 无法解析服务名，请检查服务名配置"
            else:
                return False, f"连接失败: {error}"
        except Exception as e:
            return False, f"连接失败: {str(e)}"

    def disconnect(self):
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                pass
            self.connection = None

    def is_connected(self) -> bool:
        if self.connection:
            try:
                self.connection.ping()
                return True
            except Exception:
                return False
        return False

    def get_tables(self) -> List[str]:
        if not self.is_connected():
            return []
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT table_name FROM user_tables
                ORDER BY table_name
            """)
            tables = [row[0] for row in cursor.fetchall()]
            cursor.close()
            return tables
        except Exception as e:
            print(f"获取表列表失败: {str(e)}")
            return []

    def get_columns(self, table_name: str) -> List[Dict[str, Any]]:
        if not self.is_connected():
            return []
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT column_name, data_type, data_length, nullable
                FROM user_tab_columns
                WHERE table_name = :table_name
                ORDER BY column_id
            """, {"table_name": table_name.upper()})
            columns = [
                {
                    "name": row[0],
                    "type": row[1],
                    "length": row[2],
                    "nullable": row[3] == 'Y'
                }
                for row in cursor.fetchall()
            ]
            cursor.close()
            return columns
        except Exception as e:
            print(f"获取列信息失败: {str(e)}")
            return []

    def table_exists(self, table_name: str, schema: str = None) -> bool:
        if not self.is_connected():
            return False
        try:
            cursor = self.connection.cursor()
            if schema:
                cursor.execute("""
                    SELECT COUNT(*) FROM all_tables
                    WHERE owner = :schema AND table_name = :table_name
                """, {"schema": schema.upper(), "table_name": table_name.upper()})
            else:
                cursor.execute("""
                    SELECT COUNT(*) FROM user_tables
                    WHERE table_name = :table_name
                """, {"table_name": table_name.upper()})
            result = cursor.fetchone()[0] > 0
            cursor.close()
            return result
        except Exception as e:
            print(f"检查表是否存在失败: {str(e)}")
            return False

    def execute_sql(self, sql: str, params: dict = None, commit: bool = True) -> tuple[bool, Any, str]:
        if not self.is_connected():
            return False, None, "未连接数据库"
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            result = cursor.fetchall() if cursor.description else None
            if commit:
                self.connection.commit()
            cursor.close()
            return True, result, ""
        except oracledb.DatabaseError as e:
            error_msg = str(e)
            if "ORA-00942" in error_msg:
                return False, None, f"表或视图不存在: {error_msg}"
            elif "ORA-00904" in error_msg:
                return False, None, f"列名无效: {error_msg}"
            elif "ORA-01722" in error_msg:
                return False, None, f"数据类型不匹配: {error_msg}"
            elif "ORA-00001" in error_msg:
                return False, None, f"违反唯一约束: {error_msg}"
            elif "ORA-02292" in error_msg:
                return False, None, f"违反外键约束: {error_msg}"
            else:
                return False, None, f"数据库错误: {error_msg}"
        except Exception as e:
            return False, None, f"执行失败: {str(e)}"

    def execute_many(self, sql: str, data: list, commit: bool = True) -> tuple[bool, int, str]:
        if not self.is_connected():
            return False, 0, "未连接数据库"
        try:
            cursor = self.connection.cursor()
            cursor.executemany(sql, data)
            row_count = cursor.rowcount
            if commit:
                self.connection.commit()
            cursor.close()
            return True, row_count, ""
        except oracledb.DatabaseError as e:
            return False, 0, f"批量执行失败: {str(e)}"
        except Exception as e:
            return False, 0, f"批量执行失败: {str(e)}"

    def commit(self):
        if self.connection:
            self.connection.commit()

    def rollback(self):
        if self.connection:
            self.connection.rollback()
    
    def get_key_values_from_table(self, table_name: str, key_column: str, schema: str = None) -> Tuple[bool, str, List[Any]]:
        """从数据库表中获取指定列的所有值"""
        if not self.is_connected():
            return False, "未连接数据库", []
        
        try:
            cursor = self.connection.cursor()
            if schema:
                sql = f"SELECT {key_column} FROM {schema}.{table_name}"
            else:
                sql = f"SELECT {key_column} FROM {table_name}"
            
            cursor.execute(sql)
            key_values = [row[0] for row in cursor.fetchall()]
            cursor.close()
            return True, f"获取了 {len(key_values)} 个值", key_values
        except oracledb.DatabaseError as e:
            error_msg = str(e)
            if "ORA-00942" in error_msg:
                return False, f"表或视图不存在: {error_msg}", []
            elif "ORA-00904" in error_msg:
                return False, f"列名无效: {error_msg}", []
            else:
                return False, f"查询失败: {error_msg}", []
        except Exception as e:
            return False, f"查询失败: {str(e)}", []
