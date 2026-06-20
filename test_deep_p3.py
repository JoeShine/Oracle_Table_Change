"""P3 平台模块深度功能测试

覆盖 7 个 P3 模块的所有公开方法：
1. data_compare.py - DataCompare
2. diagnostics.py - DiagnosticsCollector
3. env_config.py - EnvironmentConfig
4. backup_manager.py - BackupManager
5. scheduler.py - TaskScheduler
6. trend_analysis.py - TrendAnalyzer
7. import_stats.py - ImportStats
"""

import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest


# ============================================================================
# 1. DataCompare 测试
# ============================================================================

class TestDataCompare:
    """测试数据比较模块"""

    def test_compare_tables_with_mock_db(self):
        """测试表间比较 - 使用 mock DB"""
        from src.data_compare import DataCompare
        from src.errors import ValidationError, ConnectionError

        # 创建 mock DB
        mock_db = MagicMock()
        mock_db.is_connected.return_value = True
        mock_db.table_exists.return_value = True

        # 模拟表数据
        # 表 A: id=1,2,3
        # 表 B: id=2,3,4
        mock_db.execute_sql.side_effect = [
            (True, [(1, "Alice"), (2, "Bob"), (3, "Charlie")], None),  # 表 A
            (True, [(2, "Bob"), (3, "Charlie"), (4, "David")], None),  # 表 B
        ]
        mock_db.get_columns.side_effect = [
            [{"name": "id"}, {"name": "name"}],  # 表 A 列
            [{"name": "id"}, {"name": "name"}],  # 表 B 列
        ]

        dc = DataCompare(db=mock_db)
        result = dc.compare_tables("TABLE_A", "TABLE_B", ["id"])

        assert "added" in result
        assert "removed" in result
        assert "modified" in result
        assert "unchanged" in result
        assert result["unchanged"] == 2  # id=2,3 相同
        assert len(result["added"]) == 1  # id=4 新增
        assert len(result["removed"]) == 1  # id=1 删除

    def test_compare_tables_empty_data(self):
        """测试空数据场景"""
        from src.data_compare import DataCompare

        mock_db = MagicMock()
        mock_db.is_connected.return_value = True
        mock_db.table_exists.return_value = True
        mock_db.execute_sql.return_value = (True, [], None)
        mock_db.get_columns.return_value = [{"name": "id"}]

        dc = DataCompare(db=mock_db)
        result = dc.compare_tables("TABLE_A", "TABLE_B", ["id"])

        assert result["added"] == []
        assert result["removed"] == []
        assert result["modified"] == []
        assert result["unchanged"] == 0

    def test_compare_tables_no_difference(self):
        """测试无差异场景"""
        from src.data_compare import DataCompare

        mock_db = MagicMock()
        mock_db.is_connected.return_value = True
        mock_db.table_exists.return_value = True
        mock_db.execute_sql.side_effect = [
            (True, [(1, "Alice"), (2, "Bob")], None),
            (True, [(1, "Alice"), (2, "Bob")], None),
        ]
        mock_db.get_columns.side_effect = [
            [{"name": "id"}, {"name": "name"}],
            [{"name": "id"}, {"name": "name"}],
        ]

        dc = DataCompare(db=mock_db)
        result = dc.compare_tables("TABLE_A", "TABLE_B", ["id"])

        assert result["added"] == []
        assert result["removed"] == []
        assert result["modified"] == []
        assert result["unchanged"] == 2

    def test_compare_tables_db_not_connected(self):
        """测试数据库未连接"""
        from src.data_compare import DataCompare
        from src.errors import ConnectionError

        mock_db = MagicMock()
        mock_db.is_connected.return_value = False

        dc = DataCompare(db=mock_db)
        with pytest.raises(ConnectionError):
            dc.compare_tables("TABLE_A", "TABLE_B", ["id"])

    def test_compare_tables_empty_key_columns(self):
        """测试空主键列"""
        from src.data_compare import DataCompare
        from src.errors import ValidationError

        mock_db = MagicMock()
        mock_db.is_connected.return_value = True

        dc = DataCompare(db=mock_db)
        with pytest.raises(ValidationError):
            dc.compare_tables("TABLE_A", "TABLE_B", [])

    def test_compare_with_excel(self):
        """测试与 Excel 比较"""
        from src.data_compare import DataCompare
        from src.errors import ValidationError, ImportError as SrcImportError

        mock_db = MagicMock()
        mock_db.is_connected.return_value = True
        mock_db.table_exists.return_value = True
        mock_db.execute_sql.return_value = (True, [(1, "Alice"), (2, "Bob")], None)
        mock_db.get_columns.return_value = [{"name": "id"}, {"name": "name"}]

        dc = DataCompare(db=mock_db)

        # ExcelHandler 是在方法内部延迟导入的，需要 patch src.excel_handler.ExcelHandler
        with patch("src.excel_handler.ExcelHandler") as MockExcelHandler:
            mock_handler = MagicMock()
            MockExcelHandler.return_value = mock_handler
            mock_handler.read_excel.return_value = [
                {"id": 2, "name": "Bob"},
                {"id": 3, "name": "Charlie"},
            ]

            result = dc.compare_with_excel("TABLE_A", "test.xlsx", "id")

            assert len(result["added"]) == 1  # id=3 在 Excel 中
            assert len(result["removed"]) == 1  # id=1 在数据库中
            assert result["unchanged"] == 1  # id=2 相同

    def test_compare_with_excel_empty_key(self):
        """测试 Excel 比较空主键"""
        from src.data_compare import DataCompare
        from src.errors import ValidationError

        mock_db = MagicMock()
        mock_db.is_connected.return_value = True

        dc = DataCompare(db=mock_db)
        with pytest.raises(ValidationError):
            dc.compare_with_excel("TABLE_A", "test.xlsx", "")

    def test_generate_diff_report_text(self):
        """测试生成文本格式差异报告"""
        from src.data_compare import DataCompare

        mock_db = MagicMock()
        mock_db.is_connected.return_value = True
        mock_db.table_exists.return_value = True
        mock_db.execute_sql.side_effect = [
            (True, [(1, "Alice"), (2, "Bob")], None),
            (True, [(2, "Bob"), (3, "Charlie")], None),
        ]
        mock_db.get_columns.side_effect = [
            [{"name": "id"}, {"name": "name"}],
            [{"name": "id"}, {"name": "name"}],
        ]

        dc = DataCompare(db=mock_db)
        dc.compare_tables("TABLE_A", "TABLE_B", ["id"])
        report = dc.generate_diff_report(format="text")

        assert "数据比较报告" in report
        assert "新增行" in report or "删除行" in report
        assert "主键列" in report

    def test_generate_diff_report_html(self):
        """测试生成 HTML 格式差异报告"""
        from src.data_compare import DataCompare

        mock_db = MagicMock()
        mock_db.is_connected.return_value = True
        mock_db.table_exists.return_value = True
        mock_db.execute_sql.side_effect = [
            (True, [(1, "Alice")], None),
            (True, [(1, "Alice")], None),
        ]
        mock_db.get_columns.side_effect = [
            [{"name": "id"}, {"name": "name"}],
            [{"name": "id"}, {"name": "name"}],
        ]

        dc = DataCompare(db=mock_db)
        dc.compare_tables("TABLE_A", "TABLE_B", ["id"])
        report = dc.generate_diff_report(format="html")

        assert "<!DOCTYPE html>" in report
        assert "数据比较报告" in report
        assert "</html>" in report

    def test_generate_diff_report_no_comparison(self):
        """测试未执行比较时生成报告"""
        from src.data_compare import DataCompare
        from src.errors import ValidationError

        dc = DataCompare()
        with pytest.raises(ValidationError):
            dc.generate_diff_report()


# ============================================================================
# 2. DiagnosticsCollector 测试
# ============================================================================

class TestDiagnosticsCollector:
    """测试诊断信息收集模块"""

    def test_collect_environment_info(self):
        """测试收集环境信息"""
        from src.diagnostics import DiagnosticsCollector

        dc = DiagnosticsCollector()
        info = dc.collect_environment_info()

        assert "python_version" in info
        assert "platform" in info
        assert "libraries" in info
        assert isinstance(info["libraries"], dict)

    def test_collect_db_info(self):
        """测试收集数据库信息 - mock DB"""
        from src.diagnostics import DiagnosticsCollector
        from src.errors import ConnectionError

        mock_db = MagicMock()
        mock_db.is_connected.return_value = True
        mock_db.connection_info = {"host": "localhost", "port": 1521}
        mock_db.execute_sql.return_value = (True, [("Oracle Database 19c",)], None)

        dc = DiagnosticsCollector()
        info = dc.collect_db_info(mock_db)

        assert "oracle_version" in info
        assert "nls_settings" in info
        assert "tablespace_usage" in info
        assert "instance_info" in info

    def test_collect_db_info_not_connected(self):
        """测试数据库未连接时收集信息"""
        from src.diagnostics import DiagnosticsCollector
        from src.errors import ConnectionError

        mock_db = MagicMock()
        mock_db.is_connected.return_value = False

        dc = DiagnosticsCollector()
        with pytest.raises(ConnectionError):
            dc.collect_db_info(mock_db)

    def test_collect_config_info_no_config_manager(self):
        """测试无 ConfigManager 时收集配置信息"""
        from src.diagnostics import DiagnosticsCollector

        dc = DiagnosticsCollector(config_manager=None)
        info = dc.collect_config_info()

        assert "status" in info
        assert info["status"] == "ConfigManager 未提供"

    def test_collect_config_info_with_config_manager(self):
        """测试有 ConfigManager 时收集配置信息"""
        from src.diagnostics import DiagnosticsCollector

        mock_config = MagicMock()
        mock_config.config = {
            "connections": [
                {
                    "name": "test",
                    "host": "localhost",
                    "port": 1521,
                    "service": "ORCL",
                    "username": "user",
                    "password": "secret",
                }
            ],
            "templates": [],
            "last_used": {},
            "schema_values": [],
        }
        mock_config.config_file = Path("/tmp/config.json")

        dc = DiagnosticsCollector(config_manager=mock_config)
        info = dc.collect_config_info()

        assert "connections_count" in info
        assert info["connections_count"] == 1
        assert info["connections"][0]["password"] == "***"

    def test_collect_log_summary(self):
        """测试收集日志摘要"""
        from src.diagnostics import DiagnosticsCollector

        dc = DiagnosticsCollector()
        summary = dc.collect_log_summary(last_n_errors=10)

        assert "total_log_files" in summary
        assert "total_errors" in summary
        assert "total_warnings" in summary
        assert "recent_errors" in summary
        assert isinstance(summary["recent_errors"], list)

    def test_generate_diagnostic_report(self):
        """测试生成诊断报告"""
        from src.diagnostics import DiagnosticsCollector

        dc = DiagnosticsCollector()
        dc.collect_environment_info()
        dc.collect_log_summary()

        report = dc.generate_diagnostic_report()

        assert "诊断报告" in report
        assert "系统环境信息" in report
        assert "日志摘要" in report

    def test_export_diagnostics(self):
        """测试导出诊断报告"""
        from src.diagnostics import DiagnosticsCollector

        with tempfile.TemporaryDirectory() as d:
            dc = DiagnosticsCollector()
            dc.collect_environment_info()
            dc.collect_log_summary()

            filepath = dc.export_diagnostics(output_dir=d, filename="test_diag.txt")

            assert os.path.exists(filepath)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            assert "诊断报告" in content


# ============================================================================
# 3. EnvironmentConfig 测试
# ============================================================================

class TestEnvironmentConfig:
    """测试多环境配置管理模块"""

    def test_load_environment(self):
        """测试加载环境配置"""
        from src.env_config import EnvironmentConfig
        from src.errors import ConfigError

        with tempfile.TemporaryDirectory() as d:
            config_file = Path(d) / "environments.json"
            config_file.write_text(json.dumps({
                "active_environment": "DEV",
                "environments": {
                    "DEV": {
                        "description": "开发环境",
                        "connection": {
                            "host": "dev-db",
                            "port": 1521,
                            "service": "ORCLDEV",
                            "username": "dev_user",
                            "password": "dev_pass",
                        },
                        "settings": {"schema": "APPS_DEV"},
                    }
                },
            }))

            ec = EnvironmentConfig(config_file=str(config_file))
            env = ec.load_environment("DEV")

            assert env["description"] == "开发环境"
            assert env["connection"]["host"] == "dev-db"

    def test_load_environment_not_exists(self):
        """测试加载不存在的环境"""
        from src.env_config import EnvironmentConfig
        from src.errors import ConfigError

        with tempfile.TemporaryDirectory() as d:
            config_file = Path(d) / "environments.json"
            config_file.write_text(json.dumps({
                "active_environment": "",
                "environments": {},
            }))

            ec = EnvironmentConfig(config_file=str(config_file))
            with pytest.raises(ConfigError):
                ec.load_environment("PROD")

    def test_switch_environment(self):
        """测试切换环境"""
        from src.env_config import EnvironmentConfig

        with tempfile.TemporaryDirectory() as d:
            config_file = Path(d) / "environments.json"
            config_file.write_text(json.dumps({
                "active_environment": "DEV",
                "environments": {
                    "DEV": {
                        "description": "开发环境",
                        "connection": {
                            "host": "dev-db",
                            "port": 1521,
                            "service": "ORCLDEV",
                            "username": "dev_user",
                            "password": "dev_pass",
                        },
                        "settings": {"schema": "APPS_DEV"},
                    },
                    "TEST": {
                        "description": "测试环境",
                        "connection": {
                            "host": "test-db",
                            "port": 1521,
                            "service": "ORCLTEST",
                            "username": "test_user",
                            "password": "test_pass",
                        },
                        "settings": {"schema": "APPS_TEST"},
                    },
                },
            }))

            ec = EnvironmentConfig(config_file=str(config_file))
            assert ec.active_environment == "DEV"

            ec.switch_environment("TEST")
            assert ec.active_environment == "TEST"

            # 验证配置已保存
            with open(config_file, "r", encoding="utf-8") as f:
                saved = json.load(f)
            assert saved["active_environment"] == "TEST"

    def test_get_current_environment(self):
        """测试获取当前环境"""
        from src.env_config import EnvironmentConfig

        with tempfile.TemporaryDirectory() as d:
            config_file = Path(d) / "environments.json"
            config_file.write_text(json.dumps({
                "active_environment": "DEV",
                "environments": {
                    "DEV": {
                        "description": "开发环境",
                        "connection": {
                            "host": "dev-db",
                            "port": 1521,
                            "service": "ORCLDEV",
                            "username": "dev_user",
                            "password": "dev_pass",
                        },
                        "settings": {},
                    }
                },
            }))

            ec = EnvironmentConfig(config_file=str(config_file))
            current = ec.get_current_environment()

            assert current["active"] is True
            assert current["name"] == "DEV"
            assert current["config"] is not None

    def test_get_current_environment_none(self):
        """测试未设置当前环境"""
        from src.env_config import EnvironmentConfig

        with tempfile.TemporaryDirectory() as d:
            config_file = Path(d) / "environments.json"
            config_file.write_text(json.dumps({
                "active_environment": "",
                "environments": {},
            }))

            ec = EnvironmentConfig(config_file=str(config_file))
            current = ec.get_current_environment()

            assert current["active"] is False
            assert current["name"] == ""

    def test_list_environments(self):
        """测试列出所有环境"""
        from src.env_config import EnvironmentConfig

        with tempfile.TemporaryDirectory() as d:
            config_file = Path(d) / "environments.json"
            config_file.write_text(json.dumps({
                "active_environment": "DEV",
                "environments": {
                    "DEV": {
                        "description": "开发环境",
                        "connection": {"host": "dev-db", "port": 1521, "service": "ORCL", "username": "u"},
                        "settings": {},
                    },
                    "TEST": {
                        "description": "测试环境",
                        "connection": {"host": "test-db", "port": 1521, "service": "ORCL", "username": "u"},
                        "settings": {},
                    },
                },
            }))

            ec = EnvironmentConfig(config_file=str(config_file))
            envs = ec.list_environments()

            assert len(envs) == 2
            assert any(e["name"] == "DEV" and e["is_active"] for e in envs)
            assert any(e["name"] == "TEST" and not e["is_active"] for e in envs)

    def test_add_environment(self):
        """测试添加环境"""
        from src.env_config import EnvironmentConfig

        with tempfile.TemporaryDirectory() as d:
            config_file = Path(d) / "environments.json"
            config_file.write_text(json.dumps({
                "active_environment": "",
                "environments": {},
            }))

            ec = EnvironmentConfig(config_file=str(config_file))
            result = ec.add_environment(
                env_name="PROD",
                description="生产环境",
                host="prod-db",
                port=1521,
                service="ORCLPROD",
                username="prod_user",
                password="prod_pass",
                schema="APPS_PROD",
            )

            assert result is True
            assert "PROD" in ec.config["environments"]

            # 验证已保存
            with open(config_file, "r", encoding="utf-8") as f:
                saved = json.load(f)
            assert "PROD" in saved["environments"]

    def test_remove_environment(self):
        """测试删除环境"""
        from src.env_config import EnvironmentConfig
        from src.errors import ConfigError

        with tempfile.TemporaryDirectory() as d:
            config_file = Path(d) / "environments.json"
            config_file.write_text(json.dumps({
                "active_environment": "DEV",
                "environments": {
                    "DEV": {
                        "description": "开发环境",
                        "connection": {"host": "dev-db", "port": 1521, "service": "ORCL", "username": "u", "password": "p"},
                        "settings": {},
                    },
                    "TEST": {
                        "description": "测试环境",
                        "connection": {"host": "test-db", "port": 1521, "service": "ORCL", "username": "u", "password": "p"},
                        "settings": {},
                    },
                },
            }))

            ec = EnvironmentConfig(config_file=str(config_file))
            result = ec.remove_environment("TEST")

            assert result is True
            assert "TEST" not in ec.config["environments"]

    def test_remove_environment_not_exists(self):
        """测试删除不存在的环境"""
        from src.env_config import EnvironmentConfig
        from src.errors import ConfigError

        with tempfile.TemporaryDirectory() as d:
            config_file = Path(d) / "environments.json"
            config_file.write_text(json.dumps({
                "active_environment": "",
                "environments": {},
            }))

            ec = EnvironmentConfig(config_file=str(config_file))
            with pytest.raises(ConfigError):
                ec.remove_environment("PROD")

    def test_validate_environment_valid(self):
        """测试验证有效环境"""
        from src.env_config import EnvironmentConfig

        with tempfile.TemporaryDirectory() as d:
            config_file = Path(d) / "environments.json"
            config_file.write_text(json.dumps({
                "active_environment": "DEV",
                "environments": {
                    "DEV": {
                        "description": "开发环境",
                        "connection": {
                            "host": "dev-db",
                            "port": 1521,
                            "service": "ORCLDEV",
                            "username": "dev_user",
                            "password": "dev_pass",
                        },
                        "settings": {},
                    }
                },
            }))

            ec = EnvironmentConfig(config_file=str(config_file))
            valid, msg = ec.validate_environment("DEV")

            assert valid is True
            assert "有效" in msg

    def test_validate_environment_invalid_port(self):
        """测试验证无效端口"""
        from src.env_config import EnvironmentConfig

        with tempfile.TemporaryDirectory() as d:
            config_file = Path(d) / "environments.json"
            config_file.write_text(json.dumps({
                "active_environment": "DEV",
                "environments": {
                    "DEV": {
                        "description": "开发环境",
                        "connection": {
                            "host": "dev-db",
                            "port": 99999,  # 无效端口
                            "service": "ORCLDEV",
                            "username": "dev_user",
                            "password": "dev_pass",
                        },
                        "settings": {},
                    }
                },
            }))

            ec = EnvironmentConfig(config_file=str(config_file))
            valid, msg = ec.validate_environment("DEV")

            assert valid is False
            assert "端口" in msg

    def test_validate_environment_missing_field(self):
        """测试验证缺少必需字段"""
        from src.env_config import EnvironmentConfig

        with tempfile.TemporaryDirectory() as d:
            config_file = Path(d) / "environments.json"
            config_file.write_text(json.dumps({
                "active_environment": "DEV",
                "environments": {
                    "DEV": {
                        "description": "开发环境",
                        "connection": {
                            "host": "dev-db",
                            # 缺少 port, service, username, password
                        },
                        "settings": {},
                    }
                },
            }))

            ec = EnvironmentConfig(config_file=str(config_file))
            valid, msg = ec.validate_environment("DEV")

            assert valid is False
            assert "缺少" in msg


# ============================================================================
# 4. BackupManager 测试
# ============================================================================

class TestBackupManager:
    """测试备份生命周期管理模块"""

    def test_list_backups(self):
        """测试列出备份表"""
        from src.backup_manager import BackupManager
        from src.errors import ConnectionError

        mock_db = MagicMock()
        mock_db.is_connected.return_value = True
        mock_db.execute_sql.return_value = (True, [
            ("EMPLOYEE_BAK_20260620_120000",),
            ("DEPARTMENT_BAK_20260619_130000",),
            ("EMPLOYEE",),  # 非备份表
        ], None)

        bm = BackupManager()
        backups = bm.list_backups(mock_db)

        assert len(backups) == 2
        assert backups[0]["source_table"] == "EMPLOYEE"
        assert backups[1]["source_table"] == "DEPARTMENT"

    def test_list_backups_not_connected(self):
        """测试数据库未连接时列出备份"""
        from src.backup_manager import BackupManager
        from src.errors import ConnectionError

        mock_db = MagicMock()
        mock_db.is_connected.return_value = False

        bm = BackupManager()
        with pytest.raises(ConnectionError):
            bm.list_backups(mock_db)

    def test_cleanup_old_backups(self):
        """测试清理过期备份"""
        from src.backup_manager import BackupManager
        from src.errors import ValidationError

        mock_db = MagicMock()
        mock_db.is_connected.return_value = True
        mock_db.execute_sql.side_effect = [
            (True, [
                ("EMPLOYEE_BAK_20200101_120000",),  # 过期备份
                ("DEPARTMENT_BAK_20260620_130000",),  # 新备份
            ], None),
            (True, None, None),  # DROP TABLE
        ]

        bm = BackupManager()
        result = bm.cleanup_old_backups(mock_db, retention_days=30, dry_run=False)

        assert "deleted_count" in result
        assert "deleted_tables" in result
        assert "kept_count" in result
        assert result["retention_days"] == 30

    def test_cleanup_old_backups_invalid_retention(self):
        """测试无效保留天数"""
        from src.backup_manager import BackupManager
        from src.errors import ValidationError

        mock_db = MagicMock()
        mock_db.is_connected.return_value = True

        bm = BackupManager()
        with pytest.raises(ValidationError):
            bm.cleanup_old_backups(mock_db, retention_days=0)

    def test_cleanup_old_backups_dry_run(self):
        """测试预演模式清理"""
        from src.backup_manager import BackupManager

        mock_db = MagicMock()
        mock_db.is_connected.return_value = True
        mock_db.execute_sql.return_value = (True, [
            ("EMPLOYEE_BAK_20200101_120000",),
        ], None)

        bm = BackupManager()
        result = bm.cleanup_old_backups(mock_db, retention_days=30, dry_run=True)

        assert result["dry_run"] is True
        assert result["deleted_count"] == 1

    def test_get_backup_stats(self):
        """测试获取备份统计"""
        from src.backup_manager import BackupManager

        mock_db = MagicMock()
        mock_db.is_connected.return_value = True
        mock_db.execute_sql.side_effect = [
            (True, [
                ("EMPLOYEE_BAK_20260620_120000",),
            ], None),
            (True, [(1024 * 1024,)], None),  # 1MB
        ]

        bm = BackupManager()
        stats = bm.get_backup_stats(mock_db)

        assert "total_backups" in stats
        assert "total_size_mb" in stats
        assert "oldest_backup" in stats
        assert "newest_backup" in stats

    def test_get_backup_stats_no_backups(self):
        """测试无备份时的统计"""
        from src.backup_manager import BackupManager

        mock_db = MagicMock()
        mock_db.is_connected.return_value = True
        mock_db.execute_sql.return_value = (True, [], None)

        bm = BackupManager()
        stats = bm.get_backup_stats(mock_db)

        assert stats["total_backups"] == 0
        assert stats["total_size_mb"] == 0.0

    def test_restore_from_backup(self):
        """测试从备份恢复"""
        from src.backup_manager import BackupManager
        from src.errors import ValidationError

        mock_db = MagicMock()
        mock_db.is_connected.return_value = True
        mock_db.table_exists.return_value = True
        mock_db.execute_sql.side_effect = [
            (True, None, None),  # TRUNCATE
            (True, None, None),  # INSERT
            (True, [(100,)], None),  # COUNT
        ]
        mock_db.get_columns.side_effect = [
            [{"name": "ID"}, {"name": "NAME"}],  # 备份表列
            [{"name": "ID"}, {"name": "NAME"}],  # 目标表列
        ]

        bm = BackupManager()
        result = bm.restore_from_backup(
            mock_db, "APPS", "EMPLOYEE_BAK_20260620_120000", "EMPLOYEE"
        )

        assert result["success"] is True
        assert result["rows_restored"] == 100
        assert result["truncated"] is True

    def test_restore_from_backup_table_not_exists(self):
        """测试恢复时表不存在"""
        from src.backup_manager import BackupManager
        from src.errors import ValidationError

        mock_db = MagicMock()
        mock_db.is_connected.return_value = True
        mock_db.table_exists.return_value = False

        bm = BackupManager()
        with pytest.raises(ValidationError):
            bm.restore_from_backup(mock_db, "APPS", "BAK_TABLE", "TARGET")

    def test_schedule_cleanup(self):
        """测试生成清理计划"""
        from src.backup_manager import BackupManager

        mock_db = MagicMock()
        mock_db.is_connected.return_value = True
        mock_db.execute_sql.side_effect = [
            (True, [
                ("EMPLOYEE_BAK_20200101_120000",),
            ], None),
            (True, [(1024 * 1024 * 10,)], None),  # 10MB
        ]

        bm = BackupManager()
        plan = bm.schedule_cleanup(mock_db, retention_days=30)

        assert "plan" in plan
        assert "to_delete" in plan
        assert "total_size_to_free_mb" in plan
        assert "recommended_action" in plan


# ============================================================================
# 5. TaskScheduler 测试
# ============================================================================

class TestTaskScheduler:
    """测试任务调度模块"""

    def test_add_task(self):
        """测试添加任务"""
        from src.scheduler import TaskScheduler
        from src.errors import ValidationError

        with tempfile.TemporaryDirectory() as d:
            tasks_file = Path(d) / "tasks.json"

            ts = TaskScheduler(tasks_file=str(tasks_file))
            result = ts.add_task(
                name="daily_update",
                config={"table": "EMPLOYEE"},
                cron_expression="0 8 * * *",
                description="每日更新",
            )

            assert result is True
            assert "daily_update" in ts.tasks

    def test_add_task_empty_name(self):
        """测试添加空名称任务"""
        from src.scheduler import TaskScheduler
        from src.errors import ValidationError

        with tempfile.TemporaryDirectory() as d:
            tasks_file = Path(d) / "tasks.json"

            ts = TaskScheduler(tasks_file=str(tasks_file))
            with pytest.raises(ValidationError):
                ts.add_task(name="", config={}, cron_expression="0 8 * * *")

    def test_add_task_invalid_cron(self):
        """测试添加无效 cron 表达式任务"""
        from src.scheduler import TaskScheduler, _CRONITER_AVAILABLE
        from src.errors import ValidationError

        with tempfile.TemporaryDirectory() as d:
            tasks_file = Path(d) / "tasks.json"

            ts = TaskScheduler(tasks_file=str(tasks_file))

            # 使用明确无效的 cron 表达式（字段值超出范围）
            # 如果 croniter 可用，它会验证字段值；如果不可用，只检查字段数
            invalid_cron = "60 25 32 13 8"  # 所有字段都超出有效范围

            if _CRONITER_AVAILABLE:
                # croniter 可用时会验证字段值
                with pytest.raises(ValidationError):
                    ts.add_task(
                        name="test",
                        config={"table": "EMPLOYEE"},
                        cron_expression=invalid_cron,
                    )
            else:
                # croniter 不可用时只检查字段数，5 个字段会通过验证
                # 这种情况下任务会被添加成功
                result = ts.add_task(
                    name="test",
                    config={"table": "EMPLOYEE"},
                    cron_expression=invalid_cron,
                )
                assert result is True

    def test_remove_task(self):
        """测试删除任务"""
        from src.scheduler import TaskScheduler
        from src.errors import ConfigError

        with tempfile.TemporaryDirectory() as d:
            tasks_file = Path(d) / "tasks.json"

            ts = TaskScheduler(tasks_file=str(tasks_file))
            ts.add_task(name="task1", config={"t": "1"}, cron_expression="0 8 * * *")
            ts.add_task(name="task2", config={"t": "2"}, cron_expression="0 9 * * *")

            result = ts.remove_task("task1")
            assert result is True
            assert "task1" not in ts.tasks
            assert "task2" in ts.tasks

    def test_remove_task_not_exists(self):
        """测试删除不存在的任务"""
        from src.scheduler import TaskScheduler
        from src.errors import ConfigError

        with tempfile.TemporaryDirectory() as d:
            tasks_file = Path(d) / "tasks.json"

            ts = TaskScheduler(tasks_file=str(tasks_file))
            with pytest.raises(ConfigError):
                ts.remove_task("nonexistent")

    def test_list_tasks(self):
        """测试列出任务"""
        from src.scheduler import TaskScheduler

        with tempfile.TemporaryDirectory() as d:
            tasks_file = Path(d) / "tasks.json"

            ts = TaskScheduler(tasks_file=str(tasks_file))
            ts.add_task(name="task1", config={"t": "1"}, cron_expression="0 8 * * *")
            ts.add_task(name="task2", config={"t": "2"}, cron_expression="0 9 * * *")

            tasks = ts.list_tasks()

            assert len(tasks) == 2
            assert tasks[0]["name"] == "task1"
            assert tasks[1]["name"] == "task2"

    def test_run_task(self):
        """测试执行任务"""
        from src.scheduler import TaskScheduler
        from src.errors import ConfigError

        with tempfile.TemporaryDirectory() as d:
            tasks_file = Path(d) / "tasks.json"

            ts = TaskScheduler(tasks_file=str(tasks_file))
            ts.add_task(name="task1", config={"table": "EMPLOYEE"}, cron_expression="0 8 * * *")

            result = ts.run_task("task1")

            assert result["name"] == "task1"
            assert result["config"]["table"] == "EMPLOYEE"
            assert "executed_at" in result
            assert result["run_count"] == 1

            # 再次执行
            result2 = ts.run_task("task1")
            assert result2["run_count"] == 2

    def test_run_task_not_exists(self):
        """测试执行不存在的任务"""
        from src.scheduler import TaskScheduler
        from src.errors import ConfigError

        with tempfile.TemporaryDirectory() as d:
            tasks_file = Path(d) / "tasks.json"

            ts = TaskScheduler(tasks_file=str(tasks_file))
            with pytest.raises(ConfigError):
                ts.run_task("nonexistent")

    def test_get_next_run(self):
        """测试获取下次执行时间"""
        from src.scheduler import TaskScheduler

        with tempfile.TemporaryDirectory() as d:
            tasks_file = Path(d) / "tasks.json"

            ts = TaskScheduler(tasks_file=str(tasks_file))
            ts.add_task(name="task1", config={"t": "1"}, cron_expression="0 8 * * *")

            next_run = ts.get_next_run("task1")

            assert next_run is not None
            # 验证是日期时间格式
            datetime.strptime(next_run, "%Y-%m-%d %H:%M:%S")

    def test_get_next_run_not_exists(self):
        """测试获取不存在任务的下次执行时间"""
        from src.scheduler import TaskScheduler

        with tempfile.TemporaryDirectory() as d:
            tasks_file = Path(d) / "tasks.json"

            ts = TaskScheduler(tasks_file=str(tasks_file))
            next_run = ts.get_next_run("nonexistent")

            assert next_run is None

    def test_cron_expression_validation(self):
        """测试 cron 表达式解析"""
        from src.scheduler import TaskScheduler

        with tempfile.TemporaryDirectory() as d:
            tasks_file = Path(d) / "tasks.json"

            ts = TaskScheduler(tasks_file=str(tasks_file))

            # 有效 cron
            valid, msg = ts._validate_cron("0 8 * * *")
            assert valid is True

            # 无效 cron
            valid, msg = ts._validate_cron("invalid")
            assert valid is False

    def test_task_persistence(self):
        """测试任务持久化"""
        from src.scheduler import TaskScheduler

        with tempfile.TemporaryDirectory() as d:
            tasks_file = Path(d) / "tasks.json"

            # 创建任务
            ts1 = TaskScheduler(tasks_file=str(tasks_file))
            ts1.add_task(name="task1", config={"t": "1"}, cron_expression="0 8 * * *")

            # 重新加载
            ts2 = TaskScheduler(tasks_file=str(tasks_file))
            assert "task1" in ts2.tasks
            assert ts2.tasks["task1"]["config"]["t"] == "1"


# ============================================================================
# 6. TrendAnalyzer 测试
# ============================================================================

class TestTrendAnalyzer:
    """测试趋势分析模块"""

    def _create_synthetic_logs(self, d):
        """创建合成日志文件"""
        log_content = """[2026-06-20 08:00:00,000] INFO - 目标表: APPS.EMPLOYEE
[2026-06-20 08:00:01,000] INFO - 临时表创建成功: APPS.TEMP_20260620
[2026-06-20 08:00:02,000] INFO - 导入完成，共 100 条记录
[2026-06-20 08:00:03,000] SUCCESS - 更新完成，成功: 95，失败: 3，未匹配: 2
[2026-06-20 08:00:04,000] ERROR - ORA-01722: 类型不匹配
[2026-06-20 08:00:05,000] INFO - 耗时: 5.0s
"""
        (Path(d) / "update_20260620_080000.log").write_text(log_content, encoding="utf-8")

    def test_analyze_update_frequency(self):
        """测试更新频率分析"""
        from src.trend_analysis import TrendAnalyzer

        with tempfile.TemporaryDirectory() as d:
            self._create_synthetic_logs(d)

            ta = TrendAnalyzer(logs_dir=d)
            result = ta.analyze_update_frequency(days=30)

            assert "total_updates" in result
            assert "daily_counts" in result
            assert "hourly_distribution" in result
            assert "weekly_distribution" in result
            assert result["total_updates"] >= 1

    def test_analyze_update_frequency_empty_logs(self):
        """测试空日志的频率分析"""
        from src.trend_analysis import TrendAnalyzer

        with tempfile.TemporaryDirectory() as d:
            ta = TrendAnalyzer(logs_dir=d)
            result = ta.analyze_update_frequency(days=30)

            assert result["total_updates"] == 0

    def test_analyze_error_patterns(self):
        """测试错误模式分析"""
        from src.trend_analysis import TrendAnalyzer

        with tempfile.TemporaryDirectory() as d:
            self._create_synthetic_logs(d)

            ta = TrendAnalyzer(logs_dir=d)
            result = ta.analyze_error_patterns()

            assert "total_errors" in result
            assert "error_types" in result
            assert "error_rate" in result
            assert result["total_errors"] >= 1

    def test_analyze_table_activity(self):
        """测试表活跃度分析"""
        from src.trend_analysis import TrendAnalyzer

        with tempfile.TemporaryDirectory() as d:
            self._create_synthetic_logs(d)

            ta = TrendAnalyzer(logs_dir=d)
            result = ta.analyze_table_activity()

            assert "table_activity" in result
            assert "most_active_table" in result
            assert "total_tables" in result

    def test_analyze_performance_trends(self):
        """测试性能趋势分析"""
        from src.trend_analysis import TrendAnalyzer

        with tempfile.TemporaryDirectory() as d:
            self._create_synthetic_logs(d)

            ta = TrendAnalyzer(logs_dir=d)
            result = ta.analyze_performance_trends()

            assert "daily_throughput" in result
            assert "success_rate_trend" in result
            assert "overall_stats" in result

    def test_generate_trend_report_text(self):
        """测试生成文本趋势报告"""
        from src.trend_analysis import TrendAnalyzer

        with tempfile.TemporaryDirectory() as d:
            self._create_synthetic_logs(d)

            ta = TrendAnalyzer(logs_dir=d)
            report = ta.generate_trend_report(format="text")

            assert "趋势分析报告" in report
            assert "更新频率分析" in report
            assert "错误模式分析" in report

    def test_generate_trend_report_html(self):
        """测试生成 HTML 趋势报告"""
        from src.trend_analysis import TrendAnalyzer

        with tempfile.TemporaryDirectory() as d:
            self._create_synthetic_logs(d)

            ta = TrendAnalyzer(logs_dir=d)
            report = ta.generate_trend_report(format="html")

            assert "<!DOCTYPE html>" in report
            assert "趋势分析报告" in report
            assert "</html>" in report


# ============================================================================
# 7. ImportStats 测试
# ============================================================================

class TestImportStats:
    """测试导入统计模块"""

    def _create_synthetic_logs(self, d):
        """创建合成日志文件"""
        log_content = """[2026-06-20 12:00:00,000] INFO - 目标表: APPS.EMPLOYEE
[2026-06-20 12:00:01,000] INFO - 临时表创建成功: APPS.T1
[2026-06-20 12:00:02,000] INFO - 导入完成，共 100 条记录
[2026-06-20 12:00:03,000] SUCCESS - 更新完成，成功: 95，失败: 3，未匹配: 2
[2026-06-20 12:00:04,000] ERROR - ORA-01722: 类型不匹配
[2026-06-20 12:00:05,000] INFO - 耗时: 5.0s
"""
        (Path(d) / "update_20260620_120000.log").write_text(log_content, encoding="utf-8")

    def test_overall_summary(self):
        """测试总体汇总"""
        from src.import_stats import ImportStats

        with tempfile.TemporaryDirectory() as d:
            self._create_synthetic_logs(d)

            stats = ImportStats(logs_dir=d)
            summary = stats.overall_summary(days=30)

            assert "total_operations" in summary
            assert "total_records_processed" in summary
            assert "success_rate" in summary
            assert "avg_duration_seconds" in summary

    def test_group_by_schema(self):
        """测试按 Schema 分组"""
        from src.import_stats import ImportStats

        with tempfile.TemporaryDirectory() as d:
            self._create_synthetic_logs(d)

            stats = ImportStats(logs_dir=d)
            result = stats.group_by_schema(days=30)

            assert len(result) >= 1
            assert "schema" in result[0]
            assert "operations" in result[0]
            assert "success_rate" in result[0]

    def test_group_by_table(self):
        """测试按表分组"""
        from src.import_stats import ImportStats

        with tempfile.TemporaryDirectory() as d:
            self._create_synthetic_logs(d)

            stats = ImportStats(logs_dir=d)
            result = stats.group_by_table(days=30)

            assert len(result) >= 1
            assert "table" in result[0]
            assert "operations" in result[0]

    def test_group_by_time_bucket(self):
        """测试按时间桶分组"""
        from src.import_stats import ImportStats

        with tempfile.TemporaryDirectory() as d:
            self._create_synthetic_logs(d)

            stats = ImportStats(logs_dir=d)
            result = stats.group_by_time_bucket(days=30, bucket="day")

            assert len(result) >= 1
            assert "bucket" in result[0]
            assert "operations" in result[0]

    def test_error_distribution(self):
        """测试错误分布"""
        from src.import_stats import ImportStats

        with tempfile.TemporaryDirectory() as d:
            self._create_synthetic_logs(d)

            stats = ImportStats(logs_dir=d)
            result = stats.error_distribution(days=30)

            assert len(result) >= 1
            assert "ora_code" in result[0]
            assert "count" in result[0]

    def test_status_distribution(self):
        """测试状态分布"""
        from src.import_stats import ImportStats

        with tempfile.TemporaryDirectory() as d:
            self._create_synthetic_logs(d)

            stats = ImportStats(logs_dir=d)
            result = stats.status_distribution(days=30)

            assert "total" in result
            assert "distribution" in result
            assert result["total"] >= 1

    def test_data_quality_metrics(self):
        """测试数据质量指标"""
        from src.import_stats import ImportStats

        with tempfile.TemporaryDirectory() as d:
            self._create_synthetic_logs(d)

            stats = ImportStats(logs_dir=d)
            result = stats.data_quality_metrics(days=30)

            assert "match_rate" in result
            assert "unmatched_rate" in result
            assert "quality_grade" in result

    def test_generate_report_text(self):
        """测试生成文本报表"""
        from src.import_stats import ImportStats

        with tempfile.TemporaryDirectory() as d:
            self._create_synthetic_logs(d)

            stats = ImportStats(logs_dir=d)
            report = stats.generate_report(days=30, fmt="text")

            assert "总体汇总" in report
            assert "数据质量评级" in report

    def test_generate_report_html(self):
        """测试生成 HTML 报表"""
        from src.import_stats import ImportStats

        with tempfile.TemporaryDirectory() as d:
            self._create_synthetic_logs(d)

            stats = ImportStats(logs_dir=d)
            report = stats.generate_report(days=30, fmt="html")

            assert "<!DOCTYPE html>" in report
            assert "统计报表" in report

    def test_generate_report_json(self):
        """测试生成 JSON 报表"""
        from src.import_stats import ImportStats

        with tempfile.TemporaryDirectory() as d:
            self._create_synthetic_logs(d)

            stats = ImportStats(logs_dir=d)
            report = stats.generate_report(days=30, fmt="json")

            data = json.loads(report)
            assert "summary" in data
            assert "by_schema" in data
            assert "by_table" in data

    def test_export_report(self):
        """测试导出报表"""
        from src.import_stats import ImportStats

        with tempfile.TemporaryDirectory() as d:
            self._create_synthetic_logs(d)

            stats = ImportStats(logs_dir=d)
            output_path = os.path.join(d, "report.txt")
            result = stats.export_report(output_path, days=30, fmt="text")

            assert os.path.exists(result)
            with open(result, "r", encoding="utf-8") as f:
                content = f.read()
            assert "总体汇总" in content


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
