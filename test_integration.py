#!/usr/bin/env python3
"""
集成测试 - 完整用户流程验证
测试从场景选择到数据更新的完整流程
"""

import unittest
from unittest.mock import MagicMock, Mock, patch
from datetime import datetime
import shutil
import tempfile
import os
import pandas as pd

from src.config_manager import ConfigManager
from src.excel_handler import ExcelHandler
from src.data_updater import DataUpdater
from src.logger import LogManager


class TestCompleteUserWorkflow(unittest.TestCase):
    """测试完整用户流程"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建临时Excel文件
        self.temp_dir = tempfile.mkdtemp()
        self.excel_file = os.path.join(self.temp_dir, "test_data.xlsx")
        
        # 创建测试数据
        df = pd.DataFrame({
            'EMP_ID': ['1001', '1002', '1003'],
            'NAME': ['张三', '李四', '王五'],
            'AGE': [28, 32, 25],
            'DEPT': ['技术部', '市场部', '技术部']
        })
        df.to_excel(self.excel_file, index=False)
        
        # 初始化组件
        self.mock_db = MagicMock()
        self.log_manager = LogManager()
        self.config_manager = ConfigManager()
        self.excel_handler = ExcelHandler()
        self.data_updater = DataUpdater(self.mock_db, self.log_manager)
        
    def tearDown(self):
        """清理测试环境"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_complete_workflow_scenario_to_update(self):
        """测试完整流程：场景选择 → 文件选择 → 预览 → 更新"""
        
        # 步骤1：创建并保存场景
        scenario_name = "测试场景"
        template_info = {
            'name': scenario_name,
            'description': '测试用场景',
            'connection_name': '',
            'target_table': 'EMPLOYEE',
            'key_column': 'EMP_ID',
            'update_columns': ['NAME', 'AGE', 'DEPT'],
            'schema': 'APPS',
            'temp_schema': 'SYSTEM'
        }
        
        success = self.config_manager.add_template(template_info)
        self.assertTrue(success, "场景保存失败")
        
        # 步骤2：加载场景
        loaded_config = self.config_manager.get_template_by_name(scenario_name)
        self.assertIsNotNone(loaded_config, "场景加载失败")
        self.assertEqual(loaded_config['schema'], 'APPS')
        self.assertEqual(loaded_config['temp_schema'], 'SYSTEM')
        self.assertEqual(loaded_config['target_table'], 'EMPLOYEE')
        self.assertEqual(loaded_config['key_column'], 'EMP_ID')
        self.assertEqual(loaded_config['update_columns'], ['NAME', 'AGE', 'DEPT'])
        
        # 步骤3：选择Excel文件并预览
        success, message, preview_data = self.excel_handler.get_multi_column_preview(
            self.excel_file, 
            ['NAME', 'AGE', 'DEPT']
        )
        self.assertTrue(success, f"预览失败: {message}")
        self.assertEqual(len(preview_data['rows']), 3, "预览数据行数不正确")
        self.assertIn('EMP_ID', preview_data['headers'])
        
        # 步骤4：创建临时表
        self.mock_db.execute_sql.return_value = (True, None, None)
        success, temp_table_name = self.data_updater.create_temp_table_multi_column(
            temp_schema=loaded_config['temp_schema'],
            table_name=loaded_config['target_table'],
            key_column=loaded_config['key_column'],
            update_columns=loaded_config['update_columns']
        )
        self.assertTrue(success, "临时表创建失败")
        self.assertIsNotNone(temp_table_name, "临时表名称为空")
        
        # 步骤5：导入数据到临时表
        # 读取Excel数据并转换为字典格式
        df = pd.read_excel(self.excel_file)
        data_rows = []
        for _, row in df.iterrows():
            data_rows.append({
                'key_value': row['EMP_ID'],
                'NAME': row['NAME'],
                'AGE': row['AGE'],
                'DEPT': row['DEPT']
            })
        
        self.mock_db.execute_sql.return_value = (True, None, None)
        success, msg, count = self.data_updater.import_excel_data_multi_column(
            temp_schema=loaded_config['temp_schema'],
            key_column=loaded_config['key_column'],
            update_columns=loaded_config['update_columns'],
            data_rows=data_rows
        )
        self.assertTrue(success, f"数据导入失败: {msg}")
        
        # 步骤6：执行更新
        self.mock_db.execute_sql.reset_mock()
        self.mock_db.execute_sql.side_effect = [
            (True, [("1001",), ("1002",), ("1003",)], None),  # 获取keys
            (True, [
                # key, old_NAME, old_AGE, old_DEPT, cur_NAME, cur_AGE, cur_DEPT, new_NAME, new_AGE, new_DEPT
                ("1001", "张老三", 25, "销售部", "张三", 28, "技术部", "张三", 28, "技术部"),
                ("1002", "李老四", 30, "人事部", "李四", 32, "市场部", "李四", 32, "市场部"),
                ("1003", "王老五", 22, "财务部", "王五", 25, "技术部", "王五", 25, "技术部"),
            ], None),  # 查询匹配记录（旧值≠新值=当前值，验证正确读取新值）
        ]
        
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        self.mock_db.connection.cursor.return_value = mock_cursor
        
        success_count, fail_count, failed_records = self.data_updater.execute_multi_column_update(
            target_schema=loaded_config['schema'],
            temp_schema=loaded_config['temp_schema'],
            target_table=loaded_config['target_table'],
            key_column=loaded_config['key_column'],
            update_columns=loaded_config['update_columns']
        )
        
        # 验证更新结果
        self.assertEqual(success_count, 3, "成功更新数量不正确")
        self.assertEqual(fail_count, 0, "失败数量不为0")
        self.assertEqual(len(failed_records), 0, "不应该有失败记录")
        
        # 验证UPDATE语句被调用3次
        cursor_execute_calls = mock_cursor.execute.call_args_list
        self.assertEqual(len(cursor_execute_calls), 3, "UPDATE语句调用次数不正确")
        
    def test_workflow_with_empty_fields(self):
        """测试包含空字段的完整流程"""
        
        # 创建包含空字段的测试数据
        df_with_empty = pd.DataFrame({
            'EMP_ID': ['2001', '2002'],
            'NAME': ['赵六', None],  # 2002的NAME为空
            'AGE': [None, 35],  # 2001的AGE为空
            'DEPT': ['', '财务部']  # 2001的DEPT为空字符串
        })
        
        excel_file_empty = os.path.join(self.temp_dir, "test_empty.xlsx")
        df_with_empty.to_excel(excel_file_empty, index=False)
        
        try:
            # 预览数据
            success, message, preview_data = self.excel_handler.get_multi_column_preview(
                excel_file_empty,
                ['NAME', 'AGE', 'DEPT']
            )
            self.assertTrue(success, f"预览失败: {message}")
            self.assertEqual(len(preview_data['rows']), 2)
            
            # 创建临时表
            self.mock_db.execute_sql.return_value = (True, None, None)
            success, temp_table_name = self.data_updater.create_temp_table_multi_column(
                temp_schema='SYSTEM',
                table_name='EMPLOYEE',
                key_column='EMP_ID',
                update_columns=['NAME', 'AGE', 'DEPT']
            )
            self.assertTrue(success)
            
            # 导入数据
            df = pd.read_excel(excel_file_empty)
            data_rows = []
            for _, row in df.iterrows():
                data_rows.append({
                    'key_value': row['EMP_ID'],
                    'NAME': row['NAME'],
                    'AGE': row['AGE'],
                    'DEPT': row['DEPT']
                })
            
            success, msg, count = self.data_updater.import_excel_data_multi_column(
                temp_schema='SYSTEM',
                key_column='EMP_ID',
                update_columns=['NAME', 'AGE', 'DEPT'],
                data_rows=data_rows
            )
            self.assertTrue(success, f"数据导入失败: {msg}")
            
            # 执行更新
            self.mock_db.execute_sql.reset_mock()
            self.mock_db.execute_sql.side_effect = [
                (True, [("2001",), ("2002",)], None),  # 获取keys
                (True, [
                    # key, old_NAME, old_AGE, old_DEPT, cur_NAME, cur_AGE, cur_DEPT, new_NAME, new_AGE, new_DEPT
                    ("2001", "赵老六", 30, "销售部", "赵六", None, "", "赵六", None, ""),
                    ("2002", "钱老七", 40, "人事部", None, 35, "财务部", None, 35, "财务部"),
                ], None),
            ]
            
            mock_cursor = MagicMock()
            mock_cursor.rowcount = 1
            self.mock_db.connection.cursor.return_value = mock_cursor
            
            success_count, fail_count, failed_records = self.data_updater.execute_multi_column_update(
                target_schema='APPS',
                temp_schema='SYSTEM',
                target_table='EMPLOYEE',
                key_column='EMP_ID',
                update_columns=['NAME', 'AGE', 'DEPT']
            )
            
            # 验证：两条记录都应该成功
            self.assertEqual(success_count, 2)
            self.assertEqual(fail_count, 0)
            
            # 验证：空字段不应该出现在UPDATE语句中
            cursor_execute_calls = mock_cursor.execute.call_args_list
            
            # 第1条记录（2001）：只有NAME非空
            update_sql_1 = cursor_execute_calls[0][0][0]
            self.assertIn("NAME = :NAME", update_sql_1)
            self.assertNotIn("AGE = :AGE", update_sql_1)
            self.assertNotIn("DEPT = :DEPT", update_sql_1)
            
            # 第2条记录（2002）：AGE和DEPT非空
            update_sql_2 = cursor_execute_calls[1][0][0]
            self.assertNotIn("NAME = :NAME", update_sql_2)
            self.assertIn("AGE = :AGE", update_sql_2)
            self.assertIn("DEPT = :DEPT", update_sql_2)
            
        finally:
            if os.path.exists(excel_file_empty):
                os.remove(excel_file_empty)
    
    def test_workflow_with_unmatched_records(self):
        """测试包含未匹配记录的完整流程"""
        
        # 创建测试数据（包含不存在的EMP_ID）
        df = pd.DataFrame({
            'EMP_ID': ['3001', '3002', '9999'],  # 9999不存在
            'NAME': ['孙七', '周八', '不存在'],
            'AGE': [40, 45, 99],
            'DEPT': ['销售部', '人事部', '未知']
        })
        
        excel_file = os.path.join(self.temp_dir, "test_unmatched.xlsx")
        df.to_excel(excel_file, index=False)
        
        try:
            # 预览数据
            success, message, preview_data = self.excel_handler.get_multi_column_preview(
                excel_file,
                ['NAME', 'AGE', 'DEPT']
            )
            self.assertTrue(success, f"预览失败: {message}")
            self.assertEqual(len(preview_data['rows']), 3)
            
            # 创建临时表
            self.mock_db.execute_sql.return_value = (True, None, None)
            success, temp_table_name = self.data_updater.create_temp_table_multi_column(
                temp_schema='SYSTEM',
                table_name='EMPLOYEE',
                key_column='EMP_ID',
                update_columns=['NAME', 'AGE', 'DEPT']
            )
            self.assertTrue(success)
            
            # 导入数据
            df = pd.read_excel(excel_file)
            data_rows = []
            for _, row in df.iterrows():
                data_rows.append({
                    'key_value': row['EMP_ID'],
                    'NAME': row['NAME'],
                    'AGE': row['AGE'],
                    'DEPT': row['DEPT']
                })
            
            success, msg, count = self.data_updater.import_excel_data_multi_column(
                temp_schema='SYSTEM',
                key_column='EMP_ID',
                update_columns=['NAME', 'AGE', 'DEPT'],
                data_rows=data_rows
            )
            self.assertTrue(success, f"数据导入失败: {msg}")
            
            # 执行更新（只有3001和3002存在）
            self.mock_db.execute_sql.reset_mock()
            self.mock_db.execute_sql.side_effect = [
                (True, [("3001",), ("3002",), ("9999",)], None),  # 获取keys
                (True, [
                    # key, old_NAME, old_AGE, old_DEPT, cur_NAME, cur_AGE, cur_DEPT, new_NAME, new_AGE, new_DEPT
                    ("3001", "孙老七", 38, "后勤部", "孙七", 40, "销售部", "孙七", 40, "销售部"),
                    ("3002", "周老八", 42, "行政部", "周八", 45, "人事部", "周八", 45, "人事部"),
                ], None),  # 只有2条匹配，9999不存在
            ]
            
            mock_cursor = MagicMock()
            mock_cursor.rowcount = 1
            self.mock_db.connection.cursor.return_value = mock_cursor
            
            success_count, fail_count, failed_records = self.data_updater.execute_multi_column_update(
                target_schema='APPS',
                temp_schema='SYSTEM',
                target_table='EMPLOYEE',
                key_column='EMP_ID',
                update_columns=['NAME', 'AGE', 'DEPT']
            )
            
            # 验证：2条成功，0条失败，1条未匹配
            self.assertEqual(success_count, 2)
            self.assertEqual(fail_count, 0)
            self.assertEqual(len(failed_records), 1)
            
            # 验证未匹配记录
            self.assertEqual(failed_records[0]['key_value'], '9999')
            self.assertEqual(failed_records[0]['reason'], '目标表中不存在此key_value')
            
        finally:
            if os.path.exists(excel_file):
                os.remove(excel_file)


def run_integration_tests():
    """运行集成测试"""
    print("\n" + "=" * 60)
    print("集成测试 - 完整用户流程验证")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestCompleteUserWorkflow)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"运行测试: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print("=" * 60)
    
    if result.wasSuccessful():
        print("✓ 所有集成测试通过！")
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
    success = run_integration_tests()
    sys.exit(0 if success else 1)
