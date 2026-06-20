#!/usr/bin/env python3
"""
Oracle数据批量修改工具 - 代码与文档一致性检查
"""

import os
import re
import sys
import unittest


class TestCodeDocConsistency(unittest.TestCase):
    """代码与文档一致性测试"""
    
    def setUp(self):
        self.project_dir = os.path.dirname(__file__)
    
    def test_01_temp_schema_in_gui(self):
        """测试GUI代码包含临时表Schema支持"""
        print("\n[测试] GUI代码临时表Schema...")
        
        gui_path = os.path.join(self.project_dir, 'src', 'gui.py')
        with open(gui_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查临时表Schema变量
        self.assertIn('temp_schema_var', content)
        self.assertIn('临时表模式', content)
        
        print("  ✓ GUI代码包含临时表Schema支持")
    
    def test_02_temp_schema_in_config_manager(self):
        """测试ConfigManager包含临时表Schema"""
        print("\n[测试] ConfigManager临时表Schema...")
        
        config_path = os.path.join(self.project_dir, 'src', 'config_manager.py')
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查set_last_used包含temp_schema参数
        self.assertIn('temp_schema="APPS"', content)
        
        print("  ✓ ConfigManager包含临时表Schema参数")
    
    def test_03_temp_schema_in_data_updater(self):
        """测试DataUpdater支持不同Schema"""
        print("\n[测试] DataUpdater不同Schema支持...")
        
        updater_path = os.path.join(self.project_dir, 'src', 'data_updater.py')
        with open(updater_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查方法签名包含target_schema和temp_schema
        self.assertIn('target_schema: str', content)
        self.assertIn('temp_schema: str', content)
        
        print("  ✓ DataUpdater支持目标表和临时表不同Schema")
    
    def test_04_empty_field_handling_in_code(self):
        """测试代码包含空字段处理逻辑"""
        print("\n[测试] 空字段处理逻辑...")
        
        updater_path = os.path.join(self.project_dir, 'src', 'data_updater.py')
        with open(updater_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查空字段处理注释和逻辑
        self.assertIn('空字段不更新', content)
        self.assertIn('保留目标表原值', content)
        self.assertIn('str(new_value).strip() != \'\'', content)
        
        print("  ✓ 代码包含空字段处理逻辑")
    
    def test_05_unmatched_records_in_code(self):
        """测试代码包含未匹配记录处理"""
        print("\n[测试] 未匹配记录处理...")
        
        updater_path = os.path.join(self.project_dir, 'src', 'data_updater.py')
        with open(updater_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查未匹配记录处理
        self.assertIn('unmatched_records', content)
        self.assertIn('目标表中不存在此key_value', content)
        
        print("  ✓ 代码包含未匹配记录处理")
    
    def test_06_scenario_in_gui(self):
        """测试GUI使用场景而非模板"""
        print("\n[测试] GUI使用场景术语...")
        
        gui_path = os.path.join(self.project_dir, 'src', 'gui.py')
        with open(gui_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查界面文字使用"场景"
        self.assertIn('配置场景', content)
        self.assertIn('保存为场景', content)
        
        # 检查不应有界面上的"模板"（代码中可能有template变量名）
        gui_ui_text = re.findall(r'"[^"]*模板[^"]*"', content)
        # 允许少量残留（如Excel模板文件名）
        self.assertTrue(len(gui_ui_text) <= 2, f"GUI界面发现过多'模板'文字: {gui_ui_text}")
        
        print("  ✓ GUI使用场景术语")
    
    def test_07_scenario_in_config_manager(self):
        """测试ConfigManager使用"场景"术语"""
        print("\n[测试] ConfigManager使用场景术语...")
        
        config_path = os.path.join(self.project_dir, 'src', 'config_manager.py')
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查注释和错误消息使用"场景"
        self.assertIn('场景名称不能为空', content)
        self.assertIn('场景名称不能超过100', content)
        
        print("  ✓ ConfigManager使用场景术语")
    
    def test_08_scenario_in_user_manual(self):
        """测试用户手册使用"场景"术语"""
        print("\n[测试] 用户手册使用场景术语...")
        
        manual_path = os.path.join(self.project_dir, 'docs', '用户手册.md')
        with open(manual_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查配置场景章节
        self.assertIn('配置场景', content)
        self.assertIn('保存为场景', content)
        
        # Excel模板相关不应被修改
        self.assertIn('Excel模板', content)
        
        print("  ✓ 用户手册使用场景术语")
    
    def test_09_easy_connect_in_dockerfile(self):
        """测试Dockerfile包含Easy Connect说明"""
        print("\n[测试] Dockerfile Easy Connect...")
        
        dockerfile_path = os.path.join(self.project_dir, 'Dockerfile')
        with open(dockerfile_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查Easy Connect说明
        self.assertIn('Easy Connect', content)
        self.assertIn('无需配置文件', content)
        
        print("  ✓ Dockerfile包含Easy Connect说明")
    
    def test_10_version_consistency(self):
        """测试版本号一致性"""
        print("\n[测试] 版本号一致性...")
        
        # 检查各文件中的版本号
        files_to_check = [
            ('demo.html', 'v2.7'),
            ('docs/用户手册.md', 'v2.7'),
            ('Dockerfile', 'version="2.7"'),
            ('NEW_FEATURES_README.md', 'v2.7')
        ]
        
        for file_name, version_pattern in files_to_check:
            file_path = os.path.join(self.project_dir, file_name)
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.assertIn(version_pattern, content, f"{file_name}版本号不一致")
        
        print("  ✓ 版本号一致性正确")
    
    def test_11_portable_scripts_exist(self):
        """测试便携版脚本存在"""
        print("\n[测试] 便携版脚本...")
        
        scripts_dir = os.path.join(self.project_dir, 'scripts')
        
        # Windows脚本
        win_script = os.path.join(scripts_dir, 'create_portable.bat')
        self.assertTrue(os.path.exists(win_script))
        
        # Linux脚本
        linux_script = os.path.join(scripts_dir, 'create_portable.sh')
        self.assertTrue(os.path.exists(linux_script))
        
        print("  ✓ 便携版脚本存在")
    
    def test_12_system_compatibility_table(self):
        """测试系统兼容性表存在"""
        print("\n[测试] 系统兼容性表...")
        
        readme_path = os.path.join(self.project_dir, 'README.md')
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查兼容性表内容
        self.assertIn('Windows 7', content)
        self.assertIn('Windows Server 2008 R2', content)
        self.assertIn('便携版', content)
        
        print("  ✓ 系统兼容性表存在")


def run_consistency_tests():
    """运行一致性测试"""
    from datetime import datetime
    
    print("\n" + "=" * 60)
    print("Oracle数据批量修改工具 - 代码与文档一致性检查")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestCodeDocConsistency)
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
        print("✓ 所有测试通过！代码与文档一致。")
        return True
    else:
        print("✗ 存在一致性问题！")
        return False


if __name__ == '__main__':
    success = run_consistency_tests()
    sys.exit(0 if success else 1)