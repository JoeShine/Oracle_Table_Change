#!/usr/bin/env python3
"""
核心业务逻辑单元测试
测试空字段处理、未匹配记录检测等关键功能
"""

import unittest
from unittest.mock import MagicMock, Mock, patch
from datetime import datetime
from src.data_updater import DataUpdater
from src.logger import LogManager


class TestEmptyFieldHandling(unittest.TestCase):
    """测试空字段不更新逻辑"""
    
    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()
        self.mock_log = MagicMock()
        self.updater = DataUpdater(self.mock_db, self.mock_log)
        
    def test_empty_string_not_updated(self):
        """测试空字符串字段不更新"""
        # 准备测试数据
        # 模拟数据库查询返回：key=1001, old值≠新值
        # 行结构: key, old_NAME, old_AGE, old_DEPT, cur_NAME, cur_AGE, cur_DEPT, new_NAME, new_AGE, new_DEPT
        mock_result = [
            ("1001", "张老三", 25, "销售部", "张三", None, "", "张三", None, "")
        ]
        
        self.mock_db.execute_sql.side_effect = [
            (True, [("1001",)], None),  # 获取临时表keys
            (True, mock_result, None),  # 查询匹配记录
        ]
        
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        self.mock_db.connection.cursor.return_value = mock_cursor
        
        # 执行更新
        success_count, fail_count, failed_records = self.updater.execute_multi_column_update(
            target_schema="APPS",
            temp_schema="SYSTEM",
            target_table="EMPLOYEE",
            key_column="EMP_ID",
            update_columns=["NAME", "AGE", "DEPT"]
        )
        
        # 验证：只有NAME被更新（非空），AGE和DEPT不更新
        self.assertEqual(success_count, 1)
        self.assertEqual(fail_count, 0)
        
        # 验证UPDATE语句只包含NAME
        execute_calls = mock_cursor.execute.call_args_list
        self.assertTrue(len(execute_calls) > 0)
        
        update_sql = execute_calls[0][0][0]
        self.assertIn("NAME = :NAME", update_sql)
        self.assertNotIn("AGE = :AGE", update_sql)
        self.assertNotIn("DEPT = :DEPT", update_sql)
        
    def test_none_value_not_updated(self):
        """测试None值字段不更新"""
        # 准备测试数据：所有新值字段都是None
        # 行结构: key, old_NAME, old_AGE, old_DEPT, cur_NAME, cur_AGE, cur_DEPT, new_NAME, new_AGE, new_DEPT
        mock_result = [
            ("1002", "老李", 40, "技术部", None, None, None, None, None, None)
        ]
        
        self.mock_db.execute_sql.side_effect = [
            (True, [("1002",)], None),
            (True, mock_result, None),
        ]
        
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        self.mock_db.connection.cursor.return_value = mock_cursor
        
        # 执行更新
        success_count, fail_count, _ = self.updater.execute_multi_column_update(
            target_schema="APPS",
            temp_schema="SYSTEM",
            target_table="EMPLOYEE",
            key_column="EMP_ID",
            update_columns=["NAME", "AGE", "DEPT"]
        )
        
        # 验证：所有字段为空时，计入成功但不执行UPDATE
        self.assertEqual(success_count, 1)
        self.assertEqual(fail_count, 0)
        
        # 验证没有执行UPDATE语句
        execute_calls = mock_cursor.execute.call_args_list
        self.assertEqual(len(execute_calls), 0)
        
        # 验证日志记录了跳过信息
        self.mock_log.info.assert_any_call("key_value=1002: 所有字段为空，跳过更新")
        
    def test_mixed_empty_and_non_empty_fields(self):
        """测试混合空字段和非空字段"""
        # 准备测试数据：NAME非空，AGE和DEPT为空
        # 行结构: key, old_NAME, old_AGE, old_DEPT, cur_NAME, cur_AGE, cur_DEPT, new_NAME, new_AGE, new_DEPT
        mock_result = [
            ("1003", "李老三", 25, "技术部", "李四", None, "", "李四", None, "")
        ]
        
        self.mock_db.execute_sql.side_effect = [
            (True, [("1003",)], None),
            (True, mock_result, None),
        ]
        
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        self.mock_db.connection.cursor.return_value = mock_cursor
        
        # 执行更新
        success_count, fail_count, _ = self.updater.execute_multi_column_update(
            target_schema="APPS",
            temp_schema="SYSTEM",
            target_table="EMPLOYEE",
            key_column="EMP_ID",
            update_columns=["NAME", "AGE", "DEPT"]
        )
        
        # 验证：只有NAME被更新
        self.assertEqual(success_count, 1)
        
        # 验证UPDATE语句只包含NAME
        execute_calls = mock_cursor.execute.call_args_list
        update_sql = execute_calls[0][0][0]
        self.assertIn("NAME = :NAME", update_sql)
        self.assertNotIn("AGE = :AGE", update_sql)
        self.assertNotIn("DEPT = :DEPT", update_sql)
        
        # 验证日志记录了跳过的字段
        self.mock_log.info.assert_any_call("key_value=1003: 跳过空字段 AGE, DEPT")


class TestUnmatchedRecords(unittest.TestCase):
    """测试未匹配记录检测"""
    
    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()
        self.mock_log = MagicMock()
        self.updater = DataUpdater(self.mock_db, self.mock_log)
        
    def test_unmatched_records_detected(self):
        """测试未匹配记录被正确检测"""
        # 临时表中有3个key: 1001, 1002, 9999
        # 目标表中只有1001和1002，9999不存在
        # 行结构: key, old_NAME, old_AGE, old_DEPT, cur_NAME, cur_AGE, cur_DEPT, new_NAME, new_AGE, new_DEPT
        
        self.mock_db.execute_sql.side_effect = [
            (True, [("1001",), ("1002",), ("9999",)], None),  # 临时表keys
            (True, [
                ("1001", "张老三", 25, "销售部", "张三", 28, "技术部", "张三", 28, "技术部"),
                ("1002", "李老四", 30, "人事部", "李四", 32, "市场部", "李四", 32, "市场部")
            ], None),  # 匹配的记录（旧值≠新值）
        ]
        
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        self.mock_db.connection.cursor.return_value = mock_cursor
        
        # 执行更新
        success_count, fail_count, failed_records = self.updater.execute_multi_column_update(
            target_schema="APPS",
            temp_schema="SYSTEM",
            target_table="EMPLOYEE",
            key_column="EMP_ID",
            update_columns=["NAME", "AGE", "DEPT"]
        )
        
        # 验证：2条成功，0条失败
        self.assertEqual(success_count, 2)
        self.assertEqual(fail_count, 0)
        
        # 验证：failed_records包含1条未匹配记录
        self.assertEqual(len(failed_records), 1)
        self.assertEqual(failed_records[0]["key_value"], "9999")
        self.assertEqual(failed_records[0]["reason"], "目标表中不存在此key_value")
        
        # 验证日志警告
        self.mock_log.warning.assert_any_call(
            "有 1 条记录未匹配（Excel中存在但目标表中不存在）"
        )
        
    def test_all_records_unmatched(self):
        """测试所有记录都未匹配"""
        # 临时表中有2个key: 9998, 9999
        # 目标表中都不存在
        
        self.mock_db.execute_sql.side_effect = [
            (True, [("9998",), ("9999",)], None),  # 临时表keys
            (True, [], None),  # 没有匹配的记录
        ]
        
        # 执行更新
        success_count, fail_count, failed_records = self.updater.execute_multi_column_update(
            target_schema="APPS",
            temp_schema="SYSTEM",
            target_table="EMPLOYEE",
            key_column="EMP_ID",
            update_columns=["NAME", "AGE"]
        )
        
        # 验证：0条成功，0条失败，2条未匹配
        self.assertEqual(success_count, 0)
        self.assertEqual(fail_count, 0)
        self.assertEqual(len(failed_records), 2)
        
        # 验证未匹配记录
        unmatched_keys = {r["key_value"] for r in failed_records}
        self.assertEqual(unmatched_keys, {"9998", "9999"})
        
        # 验证日志警告
        self.mock_log.warning.assert_any_call("所有 2 条记录未匹配")


class TestDifferentSchemaSupport(unittest.TestCase):
    """测试临时表和目标表使用不同Schema"""
    
    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()
        self.mock_log = MagicMock()
        self.updater = DataUpdater(self.mock_db, self.mock_log)
        
    def test_different_schema_in_sql(self):
        """测试SQL语句使用不同的Schema"""
        # 目标表在APPS，临时表在SYSTEM
        
        # 先创建临时表（设置temp_table_name）
        self.mock_db.execute_sql.return_value = (True, None, None)
        success, temp_name = self.updater.create_temp_table_multi_column(
            temp_schema="SYSTEM",
            table_name="EMPLOYEE",
            key_column="EMP_ID",
            update_columns=["NAME", "AGE", "DEPT"]
        )
        self.assertTrue(success)
        
        # 重置mock以跟踪后续调用
        self.mock_db.execute_sql.reset_mock()
        self.mock_db.execute_sql.side_effect = [
            (True, [("1001",)], None),  # 第1次：获取临时表keys
            (True, [
                # key, old_NAME, old_AGE, old_DEPT, cur_NAME, cur_AGE, cur_DEPT, new_NAME, new_AGE, new_DEPT
                ("1001", "张老三", 25, "销售部", "张三", 28, "技术部", "张三", 28, "技术部")
            ], None),  # 第2次：查询匹配记录（10列）
        ]
        
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        self.mock_db.connection.cursor.return_value = mock_cursor
        
        # 执行更新
        self.updater.execute_multi_column_update(
            target_schema="APPS",
            temp_schema="SYSTEM",
            target_table="EMPLOYEE",
            key_column="EMP_ID",
            update_columns=["NAME", "AGE", "DEPT"]
        )
        
        # 验证execute_sql调用使用正确的Schema
        execute_sql_calls = self.mock_db.execute_sql.call_args_list
        
        # 第1次调用：获取临时表keys（应该使用SYSTEM Schema）
        temp_keys_sql = execute_sql_calls[0][0][0]
        self.assertIn("SYSTEM.", temp_keys_sql)
        self.assertIn(temp_name, temp_keys_sql)
        
        # 第2次调用：查询匹配记录（应该同时使用APPS和SYSTEM）
        query_sql = execute_sql_calls[1][0][0]
        self.assertIn("APPS.EMPLOYEE", query_sql)
        self.assertIn("SYSTEM.", query_sql)
        # 验证SQL使用了AS别名格式
        for col in ["NAME", "AGE", "DEPT"]:
            self.assertIn(f"AS OLD_{col}", query_sql, f"缺少 AS OLD_{col} 别名")
        
        # 验证cursor.execute的UPDATE语句使用目标表Schema
        cursor_execute_calls = mock_cursor.execute.call_args_list
        self.assertTrue(len(cursor_execute_calls) > 0)
        update_sql = cursor_execute_calls[0][0][0]
        self.assertIn("UPDATE APPS.EMPLOYEE", update_sql)


class TestBackupAndTempTableCreation(unittest.TestCase):
    """测试备份表和临时表创建"""
    
    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()
        self.mock_log = MagicMock()
        self.updater = DataUpdater(self.mock_db, self.mock_log)
        
    def test_backup_table_creation(self):
        """测试备份表创建"""
        # 第一次调用：CREATE TABLE
        # 第二次调用：COUNT检查
        self.mock_db.execute_sql.side_effect = [
            (True, None, None),        # CREATE TABLE
            (True, [("5",)], None),    # COUNT检查返回5条记录
        ]
        
        # 执行备份
        success, backup_name = self.updater.backup_table("APPS", "EMPLOYEE")
        
        # 验证
        self.assertTrue(success)
        self.assertTrue(backup_name.startswith("EMPLOYEE_BAK_"))
        self.assertTrue(self.updater.backup_created)
        
        # 验证SQL语句
        execute_calls = self.mock_db.execute_sql.call_args_list
        create_sql = execute_calls[0][0][0]
        self.assertIn("CREATE TABLE APPS.EMPLOYEE_BAK_", create_sql)
        self.assertIn("AS SELECT * FROM APPS.EMPLOYEE", create_sql)
        
        # 验证COUNT检查SQL
        count_sql = execute_calls[1][0][0]
        self.assertIn("SELECT COUNT(*)", count_sql)
        self.assertIn("EMPLOYEE_BAK_", count_sql)
        
    def test_temp_table_creation_with_schema(self):
        """测试临时表创建使用指定Schema"""
        self.mock_db.execute_sql.return_value = (True, None, None)
        
        # 执行创建
        success, temp_name = self.updater.create_temp_table_multi_column(
            temp_schema="SYSTEM",
            table_name="EMPLOYEE",
            key_column="EMP_ID",
            update_columns=["NAME", "AGE", "DEPT"]
        )
        
        # 验证
        self.assertTrue(success)
        self.assertTrue(temp_name.startswith("TEMP_UPDATE_"))
        self.assertTrue(self.updater.temp_table_created)
        
        # 验证SQL语句使用SYSTEM Schema
        execute_calls = self.mock_db.execute_sql.call_args_list
        create_sql = execute_calls[0][0][0]
        self.assertIn("CREATE TABLE SYSTEM.TEMP_UPDATE_", create_sql)
        self.assertIn("EMP_ID VARCHAR2(4000)", create_sql)
        self.assertIn("NAME VARCHAR2(4000)", create_sql)
        self.assertIn("AGE VARCHAR2(4000)", create_sql)
        self.assertIn("DEPT VARCHAR2(4000)", create_sql)


class TestRollback(unittest.TestCase):
    """测试回滚功能"""
    
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_log = MagicMock()
        self.updater = DataUpdater(self.mock_db, self.mock_log)
    
    def test_rollback_without_backup(self):
        """测试无备份表时回滚"""
        self.updater.backup_created = False
        success, msg = self.updater.rollback("APPS", "SYSTEM")
        self.assertTrue(success)
        self.assertIn("无需回滚", msg)
    
    def test_rollback_restores_data(self):
        """P0-4: 测试回滚不再 DELETE+INSERT，改为仅清理临时表并保留备份"""
        # 设置备份状态
        self.updater.backup_created = True
        self.updater.backup_table_name = "EMPLOYEE_BAK_20260620"
        self.updater.temp_table_name = "TEMP_UPDATE_12345"
        
        # Mock execute_sql 返回
        # P0-4: 新行为 — 仅清理临时表（1次 DROP TABLE），备份表保留
        self.mock_db.execute_sql.side_effect = [
            (True, None, None),  # 清理临时表
        ]
        
        success, msg = self.updater.rollback("APPS", "SYSTEM")
        
        # 验证
        self.assertTrue(success)
        self.assertIn("回滚完成", msg)
        self.assertIn("已保留供审计", msg)
        
        # 验证SQL调用 — 只有1次 DROP TABLE
        execute_calls = self.mock_db.execute_sql.call_args_list
        self.assertEqual(len(execute_calls), 1)
        
        # 第1次：DROP TABLE temp
        drop_sql = execute_calls[0][0][0]
        self.assertIn("DROP TABLE", drop_sql)
        self.assertIn("TEMP_UPDATE_12345", drop_sql)


def run_core_logic_tests():
    """运行核心业务逻辑测试"""
    print("\n" + "=" * 60)
    print("核心业务逻辑单元测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试类
    test_classes = [
        TestEmptyFieldHandling,
        TestUnmatchedRecords,
        TestDifferentSchemaSupport,
        TestBackupAndTempTableCreation,
        TestRollback
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"运行测试: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print("=" * 60)
    
    if result.wasSuccessful():
        print("✓ 所有核心业务逻辑测试通过！")
        return True
    else:
        print("✗ 存在测试失败！")
        for test, traceback in result.failures:
            print(f"\n失败: {test}")
            print(traceback)
        for test, traceback in result.errors:
            print(f"\n错误: {test}")
            print(traceback)
        return False


if __name__ == '__main__':
    import sys
    success = run_core_logic_tests()
    sys.exit(0 if success else 1)
