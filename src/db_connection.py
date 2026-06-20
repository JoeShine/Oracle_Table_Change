import traceback
import oracledb
from typing import Optional, Dict, Any, List, Tuple
from src.security import sanitize_identifier, validate_schema
from src.ora_errors import translate_ora_error


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
            # P1-7: 使用 translate_ora_error 统一翻译 ORA 错误
            translated = translate_ora_error(error)
            # 保留原有逻辑作为 fallback — 如果翻译结果与原始错误相同，使用原有细分
            if translated == f"数据库错误: {error}":
                if "ORA-12541" in error:
                    return False, "连接失败: TNS无监听程序，请检查主机地址和端口"
                elif "ORA-12514" in error:
                    return False, "连接失败: TNS监听程序无法识别服务名，请检查服务名"
                elif "ORA-01017" in error:
                    return False, "连接失败: 用户名或密码无效"
                elif "ORA-12154" in error:
                    return False, "连接失败: 无法解析服务名，请检查服务名配置"
                else:
                    return False, f"连接失败: {error}"
            else:
                return False, f"连接失败: {translated}"
        except Exception as e:
            return False, f"连接失败: {str(e)}"

    def disconnect(self):
        """断开连接管理"""
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                pass
            self.connection = None

    def is_connected(self) -> bool:
        """检查连接管理是否有效"""
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
            # P1-7: 使用 translate_ora_error 统一翻译 ORA 错误
            translated = translate_ora_error(error_msg)
            if translated == f"数据库错误: {error_msg}":
                # 未匹配到已知 ORA 错误码，使用原有细分逻辑
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
            else:
                return False, None, f"数据库错误: {translated}"
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
        """从数据库表中获取指定列的所有值（P0-1: 含安全校验）

        P0-1 修复: 所有标识符在使用前均通过安全校验
        """
        if not self.is_connected():
            return False, "未连接数据库", []

        try:
            # P0-1: 安全校验
            table_name = sanitize_identifier(table_name, "get_key_values.table_name")
            key_column = sanitize_identifier(key_column, "get_key_values.key_column")

            cursor = self.connection.cursor()
            if schema:
                schema = validate_schema(schema, "get_key_values.schema")
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

    def check_permissions(self, table_name: str) -> Tuple[bool, str, List[str]]:
        """P1-8: 权限预检查 — 验证当前用户是否拥有执行更新所需的权限。

        检查项：
        - CREATE TABLE 权限（创建临时表需要）
        - SELECT 权限（读取目标表需要）

        Args:
            table_name: 目标表名

        Returns:
            Tuple[bool, str, List[str]]: (是否拥有所有权限, 状态消息, 缺失的权限列表)
        """
        if not self.is_connected():
            return False, "未连接数据库", ["CONNECTION"]

        missing = []
        try:
            # 检查 CREATE TABLE 权限
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM session_privs
                WHERE privilege = 'CREATE TABLE'
            """)
            has_create_table = cursor.fetchone()[0] > 0
            cursor.close()

            if not has_create_table:
                # 回退检查：可能是通过角色授权的
                cursor2 = self.connection.cursor()
                cursor2.execute("""
                    SELECT COUNT(*) FROM user_sys_privs
                    WHERE privilege = 'CREATE TABLE'
                """)
                has_create_table = cursor2.fetchone()[0] > 0
                cursor2.close()

            if not has_create_table:
                missing.append("CREATE TABLE")

            # 检查目标表 SELECT 权限
            table_name_safe = sanitize_identifier(table_name, "check_permissions.table_name")
            cursor3 = self.connection.cursor()
            cursor3.execute("""
                SELECT COUNT(*) FROM user_tables
                WHERE table_name = :tn
            """, {"tn": table_name_safe.upper()})
            owns_table = cursor3.fetchone()[0] > 0
            cursor3.close()

            if not owns_table:
                # 如果不拥有该表，检查是否有 SELECT 权限
                cursor4 = self.connection.cursor()
                cursor4.execute("""
                    SELECT COUNT(*) FROM user_tab_privs
                    WHERE table_name = :tn AND privilege = 'SELECT'
                """, {"tn": table_name_safe.upper()})
                has_select = cursor4.fetchone()[0] > 0
                cursor4.close()

                if not has_select:
                    missing.append("SELECT")

            if missing:
                return False, f"缺少以下权限: {', '.join(missing)}", missing
            else:
                return True, "权限检查通过", []

        except Exception as e:
            return False, f"权限检查失败: {str(e)}", ["CHECK_ERROR"]


class ConnectionPool:
    """P1-9: 连接池 — 封装 oracledb.create_pool() 提供连接复用。

    支持:
    - min/max 池大小参数
    - acquire() / release() 获取和归还连接
    - get_connection() 便捷方法
    - graceful close()

    如果 oracledb 不支持 create_pool，则优雅降级为单连接模式。
    """

    def __init__(self, host: str, port: int, service: str, username: str,
                 password: str, min_size: int = 2, max_size: int = 10,
                 increment: int = 1):
        self.host = host
        self.port = port
        self.service = service
        self.username = username
        self.password = password
        self.min_size = min_size
        self.max_size = max_size
        self.increment = increment
        self._pool = None
        self._single_connection = None
        self._pool_enabled = False

        try:
            dsn = oracledb.makedsn(host, port, service_name=service)
            self._pool = oracledb.create_pool(
                user=username,
                password=password,
                dsn=dsn,
                min=min_size,
                max=max_size,
                increment=increment
            )
            self._pool_enabled = True
        except AttributeError:
            # oracledb 不支持 create_pool，降级为单连接
            self._pool_enabled = False
        except oracledb.DatabaseError:
            self._pool_enabled = False

    def acquire(self) -> Optional[oracledb.Connection]:
        """从连接池获取一个连接。"""
        if self._pool_enabled and self._pool:
            try:
                return self._pool.acquire()
            except oracledb.DatabaseError:
                return None
        elif self._single_connection:
            return self._single_connection
        else:
            # 降级模式：创建单连接
            try:
                dsn = oracledb.makedsn(self.host, self.port, service_name=self.service)
                self._single_connection = oracledb.connect(
                    user=self.username, password=self.password, dsn=dsn
                )
                return self._single_connection
            except oracledb.DatabaseError:
                return None

    def release(self, connection: oracledb.Connection):
        """将连接归还到连接池。"""
        if self._pool_enabled and self._pool:
            try:
                self._pool.release(connection)
            except oracledb.DatabaseError:
                pass
        # 降级模式下不关闭单连接

    def get_connection(self) -> Optional[oracledb.Connection]:
        """获取连接 — 便捷方法，等同于 acquire()。"""
        return self.acquire()

    def close(self):
        """优雅关闭连接池。"""
        if self._pool_enabled and self._pool:
            try:
                self._pool.close()
            except oracledb.DatabaseError:
                pass
        if self._single_connection:
            try:
                self._single_connection.close()
            except oracledb.DatabaseError:
                pass
        self._pool = None
        self._single_connection = None
        self._pool_enabled = False

    @property
    def is_pool_enabled(self) -> bool:
        """是否成功启用了连接池模式。"""
        return self._pool_enabled