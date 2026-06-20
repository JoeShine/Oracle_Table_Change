"""P3-2: 诊断信息收集模块

提供 DiagnosticsCollector 类，用于收集系统环境信息、数据库信息、配置信息和日志摘要，
并生成综合诊断报告，方便故障排查。

依赖:
    - db_connection: DBConnection 用于数据库诊断查询
    - config_manager: ConfigManager 用于获取配置信息
"""

import os
import sys
import json
import platform
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from src.errors import ConnectionError


class DiagnosticsCollector:
    """P3-2: 诊断信息收集器

    收集系统、数据库、配置和日志信息，生成综合诊断报告。

    Attributes:
        app_dir: 应用程序根目录
        logs_dir: 日志目录
        config_manager: ConfigManager 实例（可选）
    """

    def __init__(self, config_manager: "ConfigManager" = None):
        """初始化诊断信息收集器。

        Args:
            config_manager: ConfigManager 实例，用于获取配置信息
        """
        self.app_dir = Path(__file__).parent.parent
        self.logs_dir = self.app_dir / "logs"
        self.config_manager = config_manager
        self._collected: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # 环境信息收集
    # ------------------------------------------------------------------

    def collect_environment_info(self) -> Dict[str, Any]:
        """收集系统环境信息。

        包括 Python 版本、操作系统、oracledb 版本以及其他依赖库版本。

        Returns:
            Dict[str, Any]: 环境信息字典
        """
        info = {
            "python_version": sys.version,
            "python_executable": sys.executable,
            "platform": platform.platform(),
            "platform_system": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "platform_machine": platform.machine(),
            "platform_processor": platform.processor(),
            "hostname": platform.node(),
            "libraries": {},
        }

        # 收集关键库版本
        _libs = [
            ("oracledb", "oracledb"),
            ("openpyxl", "openpyxl"),
            ("cryptography", "cryptography"),
            ("croniter", "croniter"),
            ("json", "json"),
        ]
        for name, import_name in _libs:
            try:
                mod = __import__(import_name)
                version = getattr(mod, "__version__", "unknown")
                info["libraries"][name] = version
            except ImportError:
                info["libraries"][name] = "未安装"

        self._collected["environment"] = info
        return info

    # ------------------------------------------------------------------
    # 数据库信息收集
    # ------------------------------------------------------------------

    def collect_db_info(self, db: "DBConnection") -> Dict[str, Any]:
        """收集数据库信息。

        包括 Oracle 版本、NLS 设置、表空间使用情况等。

        Args:
            db: DBConnection 实例

        Returns:
            Dict[str, Any]: 数据库信息字典

        Raises:
            ConnectionError: 数据库未连接
        """
        if db is None or not db.is_connected():
            raise ConnectionError("数据库未连接，无法收集数据库信息")

        info = {
            "oracle_version": self._query_oracle_version(db),
            "nls_settings": self._query_nls_settings(db),
            "tablespace_usage": self._query_tablespace_usage(db),
            "instance_info": self._query_instance_info(db),
            "connection_info": db.connection_info if db.connection_info else {},
        }

        self._collected["database"] = info
        return info

    def _query_oracle_version(self, db: "DBConnection") -> str:
        """查询 Oracle 数据库版本。"""
        success, result, error = db.execute_sql(
            "SELECT banner FROM v$version WHERE banner LIKE 'Oracle%'",
            commit=False
        )
        if success and result:
            return result[0][0] if result else "unknown"
        return f"查询失败: {error}"

    def _query_nls_settings(self, db: "DBConnection") -> Dict[str, str]:
        """查询 NLS 设置。"""
        nls = {}
        nls_params = [
            "NLS_CHARACTERSET", "NLS_NCHAR_CHARACTERSET",
            "NLS_LANGUAGE", "NLS_TERRITORY", "NLS_SORT",
            "NLS_DATE_FORMAT", "NLS_TIMESTAMP_FORMAT",
            "NLS_NUMERIC_CHARACTERS",
        ]
        for param in nls_params:
            sql = f"SELECT value FROM v$nls_parameters WHERE parameter = '{param}'"
            success, result, error = db.execute_sql(sql, commit=False)
            if success and result:
                nls[param] = result[0][0]
            else:
                nls[param] = f"查询失败: {error}"
        return nls

    def _query_tablespace_usage(self, db: "DBConnection") -> List[Dict[str, Any]]:
        """查询表空间使用情况。"""
        sql = """
            SELECT
                tablespace_name,
                ROUND(SUM(bytes) / 1024 / 1024, 2) AS total_mb,
                ROUND(SUM(bytes) / 1024 / 1024, 2) - 
                    ROUND(NVL(free_space, 0) / 1024 / 1024, 2) AS used_mb,
                ROUND(NVL(free_space, 0) / 1024 / 1024, 2) AS free_mb
            FROM dba_data_files df
            LEFT JOIN (
                SELECT tablespace_name AS ts_name, SUM(bytes) AS free_space
                FROM dba_free_space
                GROUP BY tablespace_name
            ) fs ON df.tablespace_name = fs.ts_name
            GROUP BY tablespace_name, free_space
            ORDER BY tablespace_name
        """
        success, result, error = db.execute_sql(sql, commit=False)
        if success and result:
            columns = ["tablespace_name", "total_mb", "used_mb", "free_mb"]
            return [dict(zip(columns, row)) for row in result]
        return [{"error": f"查询表空间失败: {error}"}]

    def _query_instance_info(self, db: "DBConnection") -> Dict[str, str]:
        """查询实例信息。"""
        instance = {}
        queries = {
            "instance_name": "SELECT instance_name FROM v$instance",
            "host_name": "SELECT host_name FROM v$instance",
            "version": "SELECT version FROM v$instance",
            "status": "SELECT status FROM v$instance",
            "database_status": "SELECT status FROM v$instance",
            "startup_time": "SELECT startup_time FROM v$instance",
            "logins": "SELECT logins FROM v$instance",
        }
        for key, sql in queries.items():
            success, result, error = db.execute_sql(sql, commit=False)
            if success and result:
                val = result[0][0]
                instance[key] = str(val) if val is not None else "N/A"
            else:
                instance[key] = f"查询失败: {error}"
        return instance

    # ------------------------------------------------------------------
    # 配置信息收集
    # ------------------------------------------------------------------

    def collect_config_info(self) -> Dict[str, Any]:
        """收集当前配置摘要（不含密码）。

        Returns:
            Dict[str, Any]: 配置摘要字典
        """
        info = {}

        if self.config_manager is None:
            info["status"] = "ConfigManager 未提供"
            self._collected["config"] = info
            return info

        config = self.config_manager.config

        # 连接信息（去除密码）
        connections = []
        for conn in config.get("connections", []):
            conn_safe = {
                "name": conn.get("name", ""),
                "host": conn.get("host", ""),
                "port": conn.get("port", ""),
                "service": conn.get("service", ""),
                "username": conn.get("username", ""),
                "password": "***" if conn.get("password") else "",
            }
            connections.append(conn_safe)

        # 最近使用
        last_used = config.get("last_used", {})

        # 模板
        templates = []
        for tpl in config.get("templates", []):
            templates.append({
                "name": tpl.get("name", ""),
                "description": tpl.get("description", ""),
                "target_table": tpl.get("target_table", ""),
                "connection_name": tpl.get("connection_name", ""),
            })

        info = {
            "connections_count": len(connections),
            "connections": connections,
            "templates_count": len(templates),
            "templates": templates,
            "last_used": last_used,
            "config_file": str(self.config_manager.config_file),
            "schema_values": config.get("schema_values", []),
        }

        self._collected["config"] = info
        return info

    # ------------------------------------------------------------------
    # 日志摘要收集
    # ------------------------------------------------------------------

    def collect_log_summary(self, last_n_errors: int = 20) -> Dict[str, Any]:
        """从日志文件中收集最近 N 条错误信息摘要。

        Args:
            last_n_errors: 收集最近 N 条错误

        Returns:
            Dict[str, Any]: 日志摘要字典
        """
        summary = {
            "total_log_files": 0,
            "total_errors": 0,
            "total_warnings": 0,
            "recent_errors": [],
            "recent_warnings": [],
            "log_files": [],
        }

        if not self.logs_dir.exists():
            summary["status"] = "日志目录不存在"
            self._collected["logs"] = summary
            return summary

        log_files = sorted(
            self.logs_dir.glob("update_*.log"),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )
        summary["total_log_files"] = len(log_files)

        errors = []
        warnings = []

        for log_file in log_files[:10]:  # 只扫描最近 10 个日志文件
            file_info = {
                "name": log_file.name,
                "size_bytes": log_file.stat().st_size,
                "modified": datetime.fromtimestamp(
                    log_file.stat().st_mtime
                ).strftime("%Y-%m-%d %H:%M:%S"),
            }
            summary["log_files"].append(file_info)

            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if "ERROR - ERROR -" in line or "ERROR -" in line:
                            errors.append(line.strip())
                        elif "WARNING -" in line:
                            warnings.append(line.strip())
            except Exception:
                continue

        summary["total_errors"] = len(errors)
        summary["total_warnings"] = len(warnings)
        summary["recent_errors"] = errors[-last_n_errors:]
        summary["recent_warnings"] = warnings[-last_n_errors:]

        self._collected["logs"] = summary
        return summary

    # ------------------------------------------------------------------
    # 综合诊断报告
    # ------------------------------------------------------------------

    def generate_diagnostic_report(self) -> str:
        """编译所有收集到的信息，生成综合诊断报告。

        Returns:
            str: 纯文本诊断报告
        """
        lines = []
        lines.append("=" * 70)
        lines.append("  OracleBatchUpdater 诊断报告")
        lines.append("=" * 70)
        lines.append(f"  生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # 环境信息
        env = self._collected.get("environment", {})
        if env:
            lines.append("-" * 70)
            lines.append("  1. 系统环境信息")
            lines.append("-" * 70)
            lines.append(f"  Python 版本:     {env.get('python_version', 'N/A').split()[0]}")
            lines.append(f"  操作系统:         {env.get('platform', 'N/A')}")
            lines.append(f"  主机名:           {env.get('hostname', 'N/A')}")
            lines.append(f"  架构:             {env.get('platform_machine', 'N/A')}")
            lines.append("")
            lines.append("  依赖库版本:")
            for lib, ver in env.get("libraries", {}).items():
                status = " OK" if ver != "未安装" else " [未安装]"
                lines.append(f"    {lib}: {ver}{status}")
            lines.append("")

        # 数据库信息
        db_info = self._collected.get("database", {})
        if db_info:
            lines.append("-" * 70)
            lines.append("  2. 数据库信息")
            lines.append("-" * 70)
            lines.append(f"  Oracle 版本:     {db_info.get('oracle_version', 'N/A')}")
            instance = db_info.get("instance_info", {})
            lines.append(f"  实例名:           {instance.get('instance_name', 'N/A')}")
            lines.append(f"  实例状态:         {instance.get('status', 'N/A')}")
            lines.append(f"  启动时间:         {instance.get('startup_time', 'N/A')}")

            nls = db_info.get("nls_settings", {})
            if nls:
                lines.append("")
                lines.append("  NLS 设置:")
                for param, val in nls.items():
                    lines.append(f"    {param}: {val}")

            tsp = db_info.get("tablespace_usage", [])
            if tsp and "error" not in tsp[0]:
                lines.append("")
                lines.append("  表空间使用情况:")
                lines.append(f"    {'表空间':<25} {'总大小(MB)':>12} {'已用(MB)':>12} {'空闲(MB)':>12}")
                for ts in tsp:
                    lines.append(
                        f"    {ts.get('tablespace_name', ''):<25} "
                        f"{ts.get('total_mb', 0):>12.2f} "
                        f"{ts.get('used_mb', 0):>12.2f} "
                        f"{ts.get('free_mb', 0):>12.2f}"
                    )
            lines.append("")

        # 配置信息
        cfg = self._collected.get("config", {})
        if cfg:
            lines.append("-" * 70)
            lines.append("  3. 配置信息")
            lines.append("-" * 70)
            lines.append(f"  配置文件:         {cfg.get('config_file', 'N/A')}")
            lines.append(f"  连接数:           {cfg.get('connections_count', 0)}")
            lines.append(f"  场景模板数:       {cfg.get('templates_count', 0)}")
            if cfg.get("connections"):
                for conn in cfg["connections"]:
                    lines.append(
                        f"    [{conn['name']}] {conn['username']}@{conn['host']}:"
                        f"{conn['port']}/{conn['service']}"
                    )
            lines.append("")

        # 日志摘要
        log_summary = self._collected.get("logs", {})
        if log_summary:
            lines.append("-" * 70)
            lines.append("  4. 日志摘要")
            lines.append("-" * 70)
            lines.append(f"  日志文件数:       {log_summary.get('total_log_files', 0)}")
            lines.append(f"  错误总数:         {log_summary.get('total_errors', 0)}")
            lines.append(f"  警告总数:         {log_summary.get('total_warnings', 0)}")

            recent_errors = log_summary.get("recent_errors", [])
            if recent_errors:
                lines.append("")
                lines.append(f"  最近 {len(recent_errors)} 条错误:")
                for err in recent_errors:
                    lines.append(f"    {err}")
            lines.append("")

        lines.append("=" * 70)
        lines.append("  诊断报告结束")
        lines.append("=" * 70)
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # 导出诊断报告
    # ------------------------------------------------------------------

    def export_diagnostics(
        self, output_dir: str = None, filename: str = None
    ) -> str:
        """将诊断报告保存到文件。

        Args:
            output_dir: 输出目录，默认为应用根目录
            filename: 文件名，默认使用时间戳命名

        Returns:
            str: 保存的文件路径

        Raises:
            OSError: 文件写入失败
        """
        if output_dir is None:
            output_dir = self.app_dir
        else:
            output_dir = Path(output_dir)

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"diagnostics_{timestamp}.txt"

        filepath = output_dir / filename
        report = self.generate_diagnostic_report()

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)

        return str(filepath)

    # ------------------------------------------------------------------
    # 便捷方法：一键收集所有信息
    # ------------------------------------------------------------------

    def collect_all(self, db: "DBConnection" = None) -> Dict[str, Any]:
        """一键收集所有诊断信息。

        Args:
            db: DBConnection 实例，如果为 None 则跳过数据库信息收集

        Returns:
            Dict[str, Any]: 所有收集到的诊断信息
        """
        self.collect_environment_info()
        self.collect_config_info()
        self.collect_log_summary()

        if db is not None and db.is_connected():
            try:
                self.collect_db_info(db)
            except Exception:
                self._collected["database"] = {"status": "收集失败（数据库连接异常）"}

        return self._collected