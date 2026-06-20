import traceback
import oracledb
from typing import Optional, Dict, Any, List, Tuple
from src.security import sanitize_identifier, validate_schema
from src.ora_errors import translate_ora_error
from src.constants import (
    DB_TYPE_ORACLE, DB_TYPE_MYSQL, DB_TYPE_MSSQL,
    DB_DEFAULT_PORTS,
)


class DBConnection:
    def __init__(self):
        self.connection = None
        self.connection_info = None
        self.db_type = DB_TYPE_ORACLE

    def connect(self, host: str, port: int, service: str, username: str,
                password: str, db_type: str = DB_TYPE_ORACLE,
                database: str = "") -> tuple[bool, str]:
        """建立连接（v2.9.0+ 支持多数据库类型）

        Args:
            host: 主机地址
            port: 端口号（None 则自动按数据库类型选择默认端口）
            service: Oracle 使用的 SID/服务名；MySQL/SQLServer 作为数据库名的备用字段
            username: 用户名
            password: 密码
            db_type: 数据库类型：oracle / mysql / mssql
            database: MySQL / SQLServer 的数据库名（优先级高于 service）
        """
        self.db_type = db_type
        # 自动填充默认端口
        if port is None or port == 0:
            port = DB_DEFAULT_PORTS.get(db_type, 1521)
        try:
            if db_type == DB_TYPE_ORACLE:
                dsn = oracledb.makedsn(host, port, service_name=service)
                self.connection = oracledb.connect(user=username, password=password, dsn=dsn)
                self.connection_info = {
                    "host": host, "port": port, "service": service,
                    "username": username, "db_type": db_type,
                }
                return True, "连接成功"
            elif db_type == DB_TYPE_MYSQL:
                import pymysql
                db_name = database or service
                self.connection = pymysql.connect(
                    host=host, port=int(port), user=username,
                    password=password, database=db_name,
                    charset='utf8mb4', connect_timeout=15,
                )
                self.connection_info = {
                    "host": host, "port": port, "service": service,
                    "username": username, "database": db_name, "db_type": db_type,
                }
                return True, "连接成功"
            elif db_type == DB_TYPE_MSSQL:
                import pyodbc
                db_name = database or service
                driver = "ODBC Driver 17 for SQL Server"
                conn_str = f"DRIVER={{{driver}}};SERVER={host},{port};DATABASE={db_name};UID={username};PWD={password};TrustServerCertificate=yes"
                self.connection = pyodbc.connect(conn_str, timeout=15)
                self.connection_info = {
                    "host": host, "port": port, "service": service,
                    "username": username, "database": db_name, "db_type": db_type,
                }
                return True, "连接成功"
            else:
                return False, f"不支持的数据库类型: {db_type}"
        except oracledb.DatabaseError as e:
            error = str(e)
            # 保留 Oracle 专属的 ORA- 错误细分
            if "ORA-01017" in error:
                return False, "连接失败: 用户名或密码无效"
            elif "ORA-12514" in error:
                return False, "连接失败: TNS监听程序无法识别服务名，请检查服务名"
            elif "ORA-12541" in error:
                return False, "连接失败: TNS无监听程序，请检查主机地址和端口"
            elif "ORA-12154" in error:
                return False, "连接失败: 无法解析服务名，请检查服务名配置"
            else:
                return False, f"连接失败: {error}"
        except ImportError as e:
            pkg = "oracledb" if db_type == DB_TYPE_ORACLE else ("pymysql" if db_type == DB_TYPE_MYSQL else "pyodbc")
            return False, f"缺少数据库驱动依赖: {e}。请安装: pip install {pkg}"
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
                if self.db_type == DB_TYPE_ORACLE:
                    self.connection.ping()
                else:
                    cursor = self.connection.cursor()
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                    cursor.close()
                return True
            except Exception:
                return False
        return False

    def get_tables(self) -> List[str]:
        if not self.is_connected():
            return []
        try:
            cursor = self.connection.cursor()
            if self.db_type == DB_TYPE_ORACLE:
                cursor.execute("SELECT table_name FROM user_tables ORDER BY table_name")
            elif self.db_type == DB_TYPE_MYSQL:
                cursor.execute("SHOW TABLES")
            elif self.db_type == DB_TYPE_MSSQL:
                cursor.execute("SELECT name FROM sys.tables ORDER BY name")
            else:
                return []
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
            table_safe = table_name.upper() if self.db_type == DB_TYPE_ORACLE else table_name
            if self.db_type == DB_TYPE_ORACLE:
                cursor.execute(
                    "SELECT column_name, data_type, data_length, nullable FROM user_tab_columns WHERE table_name = :tn ORDER BY column_id",
                    {"tn": table_safe})
            elif self.db_type == DB_TYPE_MYSQL:
                cursor.execute(f"SHOW COLUMNS FROM `{table_safe}`")
                # (Field, Type, Null, Key, Default, Extra) — 只取 Field, Type, Null 即可
                result = cursor.fetchall()
                columns = []
                for row in result:
                    col_type = str(row[1])
                    # MySQL type 可能是 "int(11)", "varchar(50)" 等，尝试提取长度
                    import re
                    m = re.search(r"\((\d+)\)", col_type)
                    length = int(m.group(1)) if m else 0
                    columns.append({"name": row[0], "type": col_type, "length": length, "nullable": row[2] in ('YES', True)})
                cursor.close()
                return columns
            elif self.db_type == DB_TYPE_MSSQL:
                cursor.execute(f"""
                    SELECT c.name, t.name AS type_name, c.max_length, CASE WHEN c.is_nullable = 1 THEN 'Y' ELSE 'N' END
                    FROM sys.columns c JOIN sys.types t ON c.system_type_id = t.system_type_id
                    WHERE c.object_id = OBJECT_ID('{table_safe}')
                """)
            else:
                return []
            columns = [
                {"name": row[0], "type": str(row[1]), "length": row[2], "nullable": row[3] in ('Y', 'YES', True)}
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
            table_safe = table_name.upper() if self.db_type == DB_TYPE_ORACLE else table_name
            schema_safe = schema.upper() if schema and self.db_type == DB_TYPE_ORACLE else (schema or "")
            if self.db_type == DB_TYPE_ORACLE:
                if schema:
                    cursor.execute("SELECT COUNT(*) FROM all_tables WHERE owner = :s AND table_name = :t",
                                   {"s": schema_safe, "t": table_safe})
                else:
                    cursor.execute("SELECT COUNT(*) FROM user_tables WHERE table_name = :t", {"t": table_safe})
            elif self.db_type == DB_TYPE_MYSQL:
                if schema:
                    cursor.execute(f"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '{schema_safe}' AND table_name = '{table_safe}'")
                else:
                    cursor.execute(f"SELECT COUNT(*) FROM information_schema.tables WHERE table_name = '{table_safe}'")
            elif self.db_type == DB_TYPE_MSSQL:
                if schema:
                    cursor.execute(f"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '{schema_safe}' AND table_name = '{table_safe}'")
                else:
                    cursor.execute(f"SELECT COUNT(*) FROM information_schema.tables WHERE table_name = '{table_safe}'")
            else:
                return False
            result = cursor.fetchone()[0] > 0
            cursor.close()
            return result
        except Exception as e:
            print(f"检查表是否存在失败: {str(e)}")
            return False

    def execute_sql(self, sql: str, params: Any = None, commit: bool = True) -> tuple[bool, Any, str]:
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
        except Exception as e:
            return False, None, f"执行失败: {str(e)}"

    def execute_many(self, sql: str, data: list, commit: bool = True) -> tuple[bool, int, str]:
        if not self.is_connected():
            return False, 0, "未连接数据库"
        try:
            cursor = self.connection.cursor()
            cursor.executemany(sql, data)
            row_count = cursor.rowcount if cursor.rowcount is not None else len(data)
            if commit:
                self.connection.commit()
            cursor.close()
            return True, row_count, ""
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
        except Exception as e:
            error_msg = str(e)
            if "ORA-00942" in error_msg:
                return False, f"表或视图不存在: {error_msg}", []
            elif "ORA-00904" in error_msg:
                return False, f"列名无效: {error_msg}", []
            else:
                return False, f"查询失败: {error_msg}", []

    def check_permissions(self, table_name: str) -> Tuple[bool, str, List[str]]:
        if not self.is_connected():
            return False, "未连接数据库", ["CONNECTION"]
        missing = []
        try:
            cursor = self.connection.cursor()
            table_safe = table_name.upper() if self.db_type == DB_TYPE_ORACLE else table_name
            if self.db_type == DB_TYPE_ORACLE:
                cursor.execute("SELECT COUNT(*) FROM session_privs WHERE privilege = 'CREATE TABLE'")
                has_create = cursor.fetchone()[0] > 0
                if not has_create:
                    cursor2 = self.connection.cursor()
                    cursor2.execute("SELECT COUNT(*) FROM user_sys_privs WHERE privilege = 'CREATE TABLE'")
                    has_create = cursor2.fetchone()[0] > 0
                    cursor2.close()
                if not has_create:
                    missing.append("CREATE TABLE")
                cursor3 = self.connection.cursor()
                cursor3.execute("SELECT COUNT(*) FROM user_tables WHERE table_name = :tn", {"tn": table_safe})
                owns_table = cursor3.fetchone()[0] > 0
                cursor3.close()
                if not owns_table:
                    cursor4 = self.connection.cursor()
                    cursor4.execute("SELECT COUNT(*) FROM user_tab_privs WHERE table_name = :tn AND privilege = 'SELECT'", {"tn": table_safe})
                    has_select = cursor4.fetchone()[0] > 0
                    cursor4.close()
                    if not has_select:
                        missing.append("SELECT")
            else:
                # MySQL / SQLServer：简化检查 — 尝试 SELECT 1 判断是否有 SELECT 权限
                try:
                    if self.db_type == DB_TYPE_MSSQL:
                        cursor.execute(f"SELECT TOP 1 1 FROM [{table_safe}]")
                    else:
                        cursor.execute(f"SELECT 1 FROM `{table_safe}` LIMIT 1")
                    cursor.fetchall()
                except Exception:
                    missing.append("SELECT")
            cursor.close()
            if missing:
                return False, f"缺少以下权限: {', '.join(missing)}", missing
            return True, "权限检查通过", []
        except Exception as e:
            return False, f"权限检查失败: {str(e)}", ["CHECK_ERROR"]


class ConnectionPool:
    """P1-9: 连接池 — 提供连接复用（v2.9.0+ 支持多数据库类型）。

    Oracle 模式下尝试使用 oracledb.create_pool()，其他数据库 / 失败时优雅降级为单连接模式。
    """

    def __init__(self, host: str, port: int, service: str, username: str,
                 password: str, min_size: int = 2, max_size: int = 10,
                 increment: int = 1, db_type: str = DB_TYPE_ORACLE,
                 database: str = ""):
        self.host = host
        self.port = port
        self.service = service
        self.username = username
        self.password = password
        self.min_size = min_size
        self.max_size = max_size
        self.increment = increment
        self.db_type = db_type
        self.database = database
        self._pool = None
        self._single_connection = None
        self._pool_enabled = False

        if db_type == DB_TYPE_ORACLE:
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
                self._pool_enabled = False
            except Exception:
                self._pool_enabled = False
        else:
            # MySQL / SQLServer：使用 DBConnection 统一入口，降级为单连接
            self._pool_enabled = False

    def acquire(self) -> Optional[Any]:
        """从连接池获取一个连接。"""
        if self._pool_enabled and self._pool:
            try:
                return self._pool.acquire()
            except Exception:
                return None
        elif self._single_connection:
            return self._single_connection
        else:
            # 降级模式：使用 DBConnection 的统一 connect 接口
            try:
                dbc = DBConnection()
                ok, _ = dbc.connect(
                    self.host, self.port, self.service,
                    self.username, self.password,
                    db_type=self.db_type, database=self.database
                )
                if ok:
                    self._single_connection = dbc.connection
                    return self._single_connection
                return None
            except Exception:
                return None

    def release(self, connection: Any):
        """将连接归还到连接池。"""
        if self._pool_enabled and self._pool:
            try:
                self._pool.release(connection)
            except Exception:
                pass
        # 降级模式下不关闭单连接

    def get_connection(self) -> Optional[Any]:
        """获取连接 — 便捷方法，等同于 acquire()。"""
        return self.acquire()

    def close(self):
        """优雅关闭连接池。"""
        if self._pool_enabled and self._pool:
            try:
                self._pool.close()
            except Exception:
                pass
        if self._single_connection:
            try:
                self._single_connection.close()
            except Exception:
                pass
        self._pool = None
        self._single_connection = None
        self._pool_enabled = False

    @property
    def is_pool_enabled(self) -> bool:
        """是否成功启用了连接池模式。"""
        return self._pool_enabled