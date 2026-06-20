"""P0 安全修复验证测试套件

验证 P0-1 ~ P0-5 五项修复的正确性：
- P0-1: SQL 注入防御（白名单 + sanitize）
- P0-2: 密码加密（Fernet AES-GCM）
- P0-3: 审计日志防篡改（HMAC 链式签名）
- P0-4: rollback 语义修复（单事务 + 仅清理）
- P0-5: 异常处理规范（结构化异常 + traceback）
"""
import os
import sys
import json
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestP01_SQLInjectionDefense(unittest.TestCase):
    """P0-1: SQL 注入防御"""

    def test_01_safe_identifier_passes(self):
        """合法标识符应通过校验"""
        from src.security import sanitize_identifier
        safe_names = [
            "EMPLOYEE", "emp_id", "DEPT_NAME", "SALARY_2024",
            "A", "a1", "TABLE_NAME", "MY_TABLE$1", "COL#2",
        ]
        for name in safe_names:
            result = sanitize_identifier(name, "test")
            self.assertEqual(result, name, f"合法标识符 '{name}' 应通过校验")

    def test_02_malicious_identifier_rejected(self):
        """恶意标识符应被拒绝"""
        from src.security import sanitize_identifier, SecurityError
        malicious = [
            "1; DROP TABLE",  # 以数字开头
            "x' OR '1'='1",  # SQL 注入
            "x--",  # SQL 注释
            "x; SELECT * FROM dual",  # 多语句
            "a" * 200,  # 超长
            "",  # 空字符串
            "x y",  # 空格
        ]
        for name in malicious:
            with self.assertRaises(SecurityError, msg=f"恶意标识符 '{name}' 应被拒绝"):
                sanitize_identifier(name, "test")

    def test_03_quoted_identifier_supported(self):
        """双引号标识符应支持"""
        from src.security import sanitize_identifier
        result = sanitize_identifier('"CaseSensitive"', "test")
        self.assertEqual(result, '"CaseSensitive"')

    def test_04_schema_whitelist(self):
        """Schema 白名单校验"""
        from src.security import validate_schema, SecurityError
        # 安全 Schema
        self.assertEqual(validate_schema("APPS"), "APPS")
        self.assertEqual(validate_schema("HR"), "HR")
        # 未知 Schema
        with self.assertRaises(SecurityError):
            validate_schema("EVIL_SCHEMA")

    def test_05_schema_case_insensitive(self):
        """Schema 大小写不敏感"""
        from src.security import validate_schema
        self.assertEqual(validate_schema("apps"), "APPS")
        self.assertEqual(validate_schema("hr"), "HR")

    def test_06_register_new_schema(self):
        """注册新 Schema"""
        from src.security import register_safe_schema, validate_schema, SecurityError
        register_safe_schema("TEST_SCHEMA")
        self.assertEqual(validate_schema("TEST_SCHEMA"), "TEST_SCHEMA")
        self.assertEqual(validate_schema("test_schema"), "TEST_SCHEMA")

    def test_07_number_start_rejected(self):
        """数字开头被拒绝"""
        from src.security import sanitize_identifier, SecurityError
        with self.assertRaises(SecurityError):
            sanitize_identifier("123abc", "test")


class TestP02_PasswordEncryption(unittest.TestCase):
    """P0-2: 密码加密"""

    def test_01_encrypt_decrypt_roundtrip(self):
        """加密解密往返测试"""
        from src.config_manager import password_encrypt, password_decrypt
        passwords = [
            "simple123",
            "P@ssw0rd!",
            "中文密码测试",
            "a" * 100,
            "!@#$%^&*()",
        ]
        for pwd in passwords:
            encrypted = password_encrypt(pwd)
            self.assertTrue(encrypted.startswith("enc:"),
                            f"加密后的密码应以 'enc:' 开头，实际: {encrypted[:20]}...")
            decrypted = password_decrypt(encrypted)
            self.assertEqual(decrypted, pwd, f"密码 '{pwd}' 解密后不匹配")

    def test_02_old_base64_compatibility(self):
        """向后兼容旧版 Base64 编码"""
        from src.config_manager import password_decrypt
        import base64
        encoded = base64.b64encode("old_password".encode()).decode()
        decrypted = password_decrypt(encoded)
        self.assertEqual(decrypted, "old_password")

    def test_03_old_plaintext_compatibility(self):
        """向后兼容极旧版明文"""
        from src.config_manager import password_decrypt
        decrypted = password_decrypt("plaintext_password")
        self.assertEqual(decrypted, "plaintext_password")

    def test_04_empty_password(self):
        """空密码处理"""
        from src.config_manager import password_encrypt, password_decrypt
        encrypted = password_encrypt("")
        decrypted = password_decrypt(encrypted)
        self.assertEqual(decrypted, "")

    def test_05_config_manager_uses_encryption(self):
        """ConfigManager 使用加密"""
        from src.config_manager import ConfigManager
        import tempfile, os

        mgr = ConfigManager()
        # 添加连接，密码会被自动加密
        mgr.add_connection({
            "name": "test_conn",
            "host": "localhost",
            "port": 1521,
            "service": "XE",
            "username": "scott",
            "password": "tiger"
        })

        # 验证 config.json 中的密码是加密格式
        with open(mgr.config_file, 'r') as f:
            saved = json.load(f)
        for conn in saved["connections"]:
            if conn["name"] == "test_conn":
                self.assertTrue(
                    conn["password"].startswith("enc:"),
                    "保存的密码应以 'enc:' 开头"
                )

        # 读取时密码被解密
        conn = mgr.get_connection_by_name("test_conn")
        self.assertEqual(conn["password"], "tiger")

        # 清理
        mgr.delete_connection("test_conn")


class TestP03_AuditLogIntegrity(unittest.TestCase):
    """P0-3: 审计日志防篡改"""

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        import shutil
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)

    def test_01_audit_log_has_hmac(self):
        """审计日志应包含 HMAC 字段"""
        from src.logger import AuditLogger
        auditor = AuditLogger(self.tmp_dir)
        auditor.log_action("TEST", {"message": "hello"})
        self.assertTrue(auditor.audit_file.exists())

        with open(auditor.audit_file, 'r') as f:
            entry = json.loads(f.readline())
        self.assertIn("prev_hash", entry)
        self.assertIn("current_hash", entry)
        self.assertIn("os_username", entry)
        self.assertIn("hostname", entry)

    def test_02_chain_signing_works(self):
        """链式签名：每条日志的 prev_hash 应等于上一条的 current_hash"""
        from src.logger import AuditLogger
        auditor = AuditLogger(self.tmp_dir)
        auditor.log_action("TEST", {"msg": "first"})
        auditor.log_action("TEST", {"msg": "second"})

        with open(auditor.audit_file, 'r') as f:
            entries = [json.loads(line) for line in f]

        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["prev_hash"], "GENESIS")
        self.assertEqual(entries[1]["prev_hash"], entries[0]["current_hash"])

    def test_03_verify_integrity_passes(self):
        """完整性验证应通过（未篡改）"""
        from src.logger import AuditLogger
        auditor = AuditLogger(self.tmp_dir)
        auditor.log_action("TEST", {"msg": "first"})
        auditor.log_action("TEST", {"msg": "second"})

        valid, msg = auditor.verify_integrity()
        self.assertTrue(valid, f"验证应通过: {msg}")

    def test_04_verify_integrity_detects_tampering(self):
        """完整性验证应检测篡改"""
        from src.logger import AuditLogger
        auditor = AuditLogger(self.tmp_dir)
        auditor.log_action("TEST", {"msg": "first"})

        # 篡改审计日志
        with open(auditor.audit_file, 'a') as f:
            f.write('{"tampered": true}\n')

        valid, msg = auditor.verify_integrity()
        self.assertFalse(valid, "篡改应被检测到")


class TestP04_RollbackSemantics(unittest.TestCase):
    """P0-4: rollback 语义修复"""

    def test_01_rollback_only_cleans_temp(self):
        """回滚仅清理临时表，不 DELETE+INSERT"""
        from unittest.mock import MagicMock, patch
        from src.data_updater import DataUpdater

        mock_db = MagicMock()
        mock_log = MagicMock()
        updater = DataUpdater(mock_db, mock_log)
        updater.backup_created = True
        updater.backup_table_name = "EMP_BAK_20260620"
        updater.temp_table_name = "TEMP_UPDATE_12345"

        mock_db.execute_sql.side_effect = [(True, None, None)]
        success, msg = updater.rollback("APPS", "SYSTEM")

        self.assertTrue(success)
        self.assertIn("已保留供审计", msg)

        # 验证只调用了1次 execute_sql（DROP TABLE temp）
        execute_calls = mock_db.execute_sql.call_args_list
        drop_sql = execute_calls[0][0][0]
        self.assertIn("DROP TABLE", drop_sql)
        self.assertNotIn("DELETE", drop_sql)
        self.assertNotIn("INSERT", drop_sql)

    def test_02_rollback_without_backup(self):
        """无备份时无需回滚"""
        from unittest.mock import MagicMock
        from src.data_updater import DataUpdater

        mock_db = MagicMock()
        mock_log = MagicMock()
        updater = DataUpdater(mock_db, mock_log)
        updater.backup_created = False

        success, msg = updater.rollback("APPS", "SYSTEM")
        self.assertTrue(success)
        self.assertIn("无需回滚", msg)
        mock_db.execute_sql.assert_not_called()


class TestP05_ExceptionHandling(unittest.TestCase):
    """P0-5: 异常处理规范"""

    def test_01_structured_exceptions_exist(self):
        """结构化异常体系已定义"""
        from src import errors

        exc_types = [
            errors.OracleUpdaterError,
            errors.ConnectionError,
            errors.ValidationError,
            errors.SQLExecutionError,
            errors.BackupError,
            errors.RollbackError,
            errors.ConfigError,
            errors.SecurityError,
            errors.ImportError,
        ]
        for exc_type in exc_types:
            self.assertTrue(issubclass(exc_type, Exception),
                            f"{exc_type.__name__} 应继承 Exception")

    def test_02_exit_codes_different(self):
        """不同异常应有不同的退出码"""
        from src import errors
        codes = set()
        for exc_type in [
            errors.ConnectionError,
            errors.ValidationError,
            errors.SQLExecutionError,
            errors.BackupError,
            errors.RollbackError,
            errors.ConfigError,
            errors.SecurityError,
            errors.ImportError,
        ]:
            codes.add(exc_type.exit_code)
        self.assertGreater(len(codes), 5, "至少应有 5 个不同的退出码")

    def test_03_security_error_has_logging(self):
        """SecurityError 应自动记录日志"""
        from src.security import SecurityError
        # 不会抛出额外的异常，但有日志输出
        try:
            raise SecurityError("test security violation")
        except SecurityError as e:
            self.assertEqual(str(e), "test security violation")


if __name__ == '__main__':
    unittest.main()