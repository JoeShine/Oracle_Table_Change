#!/usr/bin/env python3
"""
Oracle数据批量修改工具 - 全面回归测试
测试所有新增功能和核心功能
"""

import sys
import os
import unittest
import tempfile
import json
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config_manager import ConfigManager
from src.logger import LogManager
from src.excel_handler import ExcelHandler
from src.data_updater import DataUpdater
from src.gui import OracleBatchUpdaterGUI, OSCompatibility


class TestConfigManager(unittest.TestCase):
    """配置管理器测试"""
    
    def setUp(self):
        self.config = ConfigManager()  # 不接受参数
    
    def test_01_basic_config(self):
        """测试基本配置功能"""
        print("\n[测试] 配置管理器基本功能...")
        self.assertIsInstance(self.config.config, dict)
        self.assertIn('connections', self.config.config)
        self.assertIn('templates', self.config.config)
        print("  ✓ 基本配置结构正确")
    
    def test_02_template_add(self):
        """测试场景添加"""
        print("\n[测试] 场景添加功能...")
        
        # 测试空名称
        success, msg = self.config.add_template({"name": ""})
        self.assertFalse(success)
        self.assertIn("不能为空", msg)
        print("  ✓ 空名称验证正确")
        
        # 测试过长名称
        success, msg = self.config.add_template({"name": "A" * 101})
        self.assertFalse(success)
        self.assertIn("不能超过100", msg)
        print("  ✓ 名称长度验证正确")
        
        # 测试正常添加
        template = {
            "name": "测试场景",
            "description": "测试描述",
            "target_table": "EMP",
            "schema": "APPS",
            "temp_schema": "SYSTEM"
        }
        success, msg = self.config.add_template(template)
        self.assertTrue(success)
        print("  ✓ 正常添加成功")
        
        # 测试重复添加
        success, msg = self.config.add_template(template)
        self.assertTrue(success)
        self.assertIn("已更新", msg)
        print("  ✓ 重复添加更新成功")
    
    def test_03_template_get(self):
        """测试场景获取"""
        print("\n[测试] 场景获取功能...")
        
        templates = self.config.get_templates()
        self.assertIsInstance(templates, list)
        print("  ✓ 获取场景列表成功")
        
        # 添加场景后获取
        self.config.add_template({"name": "场景1", "schema": "APPS", "temp_schema": "APPS"})
        template = self.config.get_template_by_name("场景1")
        self.assertIsNotNone(template)
        self.assertEqual(template["temp_schema"], "APPS")
        print("  ✓ 按名称获取场景成功")
    
    def test_04_last_used_with_temp_schema(self):
        """测试最后使用配置包含临时表Schema"""
        print("\n[测试] 最后使用配置（含临时表Schema）...")
        
        self.config.set_last_used(
            connection_name="测试连接",
            target_table="EMP",
            key_column="EMP_ID",
            schema="APPS",
            temp_schema="SYSTEM"
        )
        
        last_used = self.config.get_last_used()
        self.assertEqual(last_used.get("temp_schema"), "SYSTEM")
        print("  ✓ 临时表Schema保存成功")
    
    def test_05_create_template_from_current(self):
        """测试从当前配置创建场景"""
        print("\n[测试] 从当前配置创建场景...")
        
        success, msg = self.config.create_template_from_current(
            name="当前配置场景",
            description="从当前配置创建",
            target_table="DEPT",
            schema="APPS",
            temp_schema="SYS"
        )
        self.assertTrue(success)
        
        template = self.config.get_template_by_name("当前配置场景")
        self.assertEqual(template["temp_schema"], "SYS")
        print("  ✓ 创建场景成功，包含临时表Schema")


class TestOSCompatibility(unittest.TestCase):
    """操作系统兼容性测试"""
    
    def test_01_os_detection(self):
        """测试操作系统检测"""
        print("\n[测试] 操作系统检测...")
        
        os_compat = OSCompatibility()
        os_type = os_compat.os_type  # 使用属性而非方法
        
        self.assertIn(os_type, [os_compat.WINDOWS, os_compat.KYLIN, os_compat.LINUX, os_compat.MACOS])
        print(f"  ✓ 检测到操作系统: {os_type}")
    
    def test_02_font_family(self):
        """测试字体获取"""
        print("\n[测试] 字体获取...")
        
        os_compat = OSCompatibility()
        font = os_compat.font_family  # 使用属性
        
        self.assertIsInstance(font, str)
        self.assertTrue(len(font) > 0)
        print(f"  ✓ 获取字体: {font}")
    
    def test_03_os_info(self):
        """测试操作系统信息"""
        print("\n[测试] 操作系统信息...")
        
        os_compat = OSCompatibility()
        os_info = os_compat.get_info()  # 使用get_info方法
        
        self.assertIn('os_type', os_info)  # 实际返回的是os_type而非type
        self.assertIn('font_family', os_info)
        self.assertIn('os_name', os_info)
        print(f"  ✓ OS信息: {os_info['os_name']}")
    
    def test_04_app_version(self):
        """测试应用版本号动态获取"""
        print("\n[测试] 应用版本号...")
        
        from src.gui import OSCompatibility
        
        version = OSCompatibility.get_app_version()
        
        self.assertIsInstance(version, str)
        self.assertTrue(len(version) > 0)
        self.assertNotEqual(version, "unknown", "版本号不应为 unknown")
        
        # 验证版本号格式：x.y.z
        self.assertRegex(version, r'^\d+\.\d+\.\d+$', f"版本号格式错误: {version}")
        print(f"  ✓ 动态获取版本号: v{version}")


class TestExcelHandler(unittest.TestCase):
    """Excel处理器测试"""
    
    def test_01_import_test(self):
        """测试Excel模块导入"""
        print("\n[测试] Excel处理器导入...")
        
        handler = ExcelHandler()
        self.assertIsNotNone(handler)
        print("  ✓ Excel处理器导入成功")


class TestLogger(unittest.TestCase):
    """日志管理器测试"""
    
    def setUp(self):
        self.logger = LogManager()  # 不接受参数
    
    def test_01_log_methods(self):
        """测试日志方法"""
        print("\n[测试] 日志方法...")
        
        # 验证日志方法存在且可调用
        self.assertTrue(hasattr(self.logger, 'info'))
        self.assertTrue(hasattr(self.logger, 'success'))
        self.assertTrue(hasattr(self.logger, 'warning'))
        self.assertTrue(hasattr(self.logger, 'error'))
        
        # 调用方法并验证不抛出异常
        self.logger.info("测试信息")
        self.logger.success("测试成功")
        self.logger.warning("测试警告")
        self.logger.error("测试错误")
        
        # 验证日志文件被创建
        self.assertTrue(self.logger.log_file.exists(), "日志文件应被创建")
        log_content = self.logger.log_file.read_text(encoding='utf-8')
        self.assertIn("测试信息", log_content)
        self.assertIn("SUCCESS - 测试成功", log_content)
        self.assertIn("WARNING - 测试警告", log_content)
        self.assertIn("ERROR - 测试错误", log_content)
        print(f"  ✓ 日志文件已创建并包含正确内容")


class TestDataUpdater(unittest.TestCase):
    """数据更新器测试"""
    
    def test_01_import_test(self):
        """测试数据更新器导入"""
        print("\n[测试] 数据更新器导入...")
        
        # 需要mock数据库连接
        from unittest.mock import MagicMock
        mock_db = MagicMock()
        mock_log = MagicMock()
        
        updater = DataUpdater(mock_db, mock_log)
        self.assertIsNotNone(updater)
        print("  ✓ 数据更新器导入成功")


class TestGUIComponents(unittest.TestCase):
    """GUI组件测试"""
    
    def test_01_gui_import(self):
        """测试GUI导入"""
        print("\n[测试] GUI模块导入...")
        
        # 只测试导入，不启动GUI
        self.assertTrue(hasattr(OracleBatchUpdaterGUI, '__init__'))
        print("  ✓ GUI模块导入成功")
    
    def test_02_keyboard_navigation_methods(self):
        """测试键盘导航方法"""
        print("\n[测试] 键盘导航方法...")
        
        # 检查键盘绑定方法（公开方法，不含_前缀的私有方法）
        methods = [m for m in dir(OracleBatchUpdaterGUI) if not m.startswith('_')]
        expected_methods = ['bind_shortcuts']
        for method in expected_methods:
            self.assertIn(method, methods)
        print("  ✓ 键盘绑定方法存在")


class TestPortableScripts(unittest.TestCase):
    """便携版脚本测试"""
    
    def test_01_portable_script_exists(self):
        """测试便携版脚本存在"""
        print("\n[测试] 便携版脚本文件...")
        
        scripts_dir = os.path.join(os.path.dirname(__file__), 'scripts')
        
        # Windows脚本
        win_script = os.path.join(scripts_dir, 'create_portable.bat')
        self.assertTrue(os.path.exists(win_script), f"Windows便携版脚本不存在: {win_script}")
        print("  ✓ Windows便携版脚本存在")
        
        # Linux脚本
        linux_script = os.path.join(scripts_dir, 'create_portable.sh')
        self.assertTrue(os.path.exists(linux_script), f"Linux便携版脚本不存在: {linux_script}")
        print("  ✓ Linux便携版脚本存在")
    
    def test_02_oracle_client_script_exists(self):
        """测试Oracle客户端安装脚本"""
        print("\n[测试] Oracle客户端安装脚本...")
        
        scripts_dir = os.path.join(os.path.dirname(__file__), 'scripts')
        script = os.path.join(scripts_dir, 'install_oracle_client.sh')
        
        self.assertTrue(os.path.exists(script))
        print("  ✓ Oracle客户端安装脚本存在")


class TestDockerFiles(unittest.TestCase):
    """Docker文件测试"""
    
    def test_01_dockerfile_exists(self):
        """测试Dockerfile存在"""
        print("\n[测试] Dockerfile...")
        
        dockerfile = os.path.join(os.path.dirname(__file__), 'Dockerfile')
        self.assertTrue(os.path.exists(dockerfile))
        print("  ✓ Dockerfile存在")
        
        # 检查关键内容
        with open(dockerfile, 'r') as f:
            content = f.read()
            self.assertIn('FROM ubuntu:22.04', content)
            self.assertIn('EXPOSE 6080 5900', content)  # 两个端口在同一行
            self.assertIn('HEALTHCHECK', content)
        print("  ✓ Dockerfile内容正确")
    
    def test_02_docker_compose_exists(self):
        """测试docker-compose.yml存在"""
        print("\n[测试] docker-compose.yml...")
        
        compose_file = os.path.join(os.path.dirname(__file__), 'docker-compose.yml')
        self.assertTrue(os.path.exists(compose_file))
        print("  ✓ docker-compose.yml存在")
        
        # 检查YAML语法
        import yaml
        with open(compose_file, 'r') as f:
            config = yaml.safe_load(f)
            self.assertIn('services', config)
            self.assertIn('oracle-batch-updater', config['services'])
        print("  ✓ docker-compose.yml语法正确")
    
    def test_03_docker_ignore_exists(self):
        """测试.dockerignore存在"""
        print("\n[测试] .dockerignore...")
        
        ignore_file = os.path.join(os.path.dirname(__file__), '.dockerignore')
        self.assertTrue(os.path.exists(ignore_file))
        print("  ✓ .dockerignore存在")


class TestDocumentation(unittest.TestCase):
    """文档测试"""
    
    def test_01_readme_exists(self):
        """测试README存在"""
        print("\n[测试] README.md...")
        
        readme = os.path.join(os.path.dirname(__file__), 'README.md')
        self.assertTrue(os.path.exists(readme))
        
        with open(readme, 'r') as f:
            content = f.read()
            # 检查系统兼容性表
            self.assertIn('Windows 7', content)
            self.assertIn('Windows Server 2008 R2', content)
            self.assertIn('便携版', content)
        print("  ✓ README.md包含系统兼容性说明")
    
    def test_02_docs_exist(self):
        """测试文档目录"""
        print("\n[测试] 文档目录...")
        
        docs_dir = os.path.join(os.path.dirname(__file__), 'docs')
        self.assertTrue(os.path.exists(docs_dir))
        
        expected_docs = [
            '部署方案.md',
            '用户手册.md',
            'Windows_Server使用指南.md'
        ]
        
        for doc in expected_docs:
            doc_path = os.path.join(docs_dir, doc)
            self.assertTrue(os.path.exists(doc_path), f"文档不存在: {doc}")
        print("  ✓ 所有文档存在")


class TestDemoHTML(unittest.TestCase):
    """原型HTML测试"""
    
    def test_01_demo_exists(self):
        """测试demo.html存在"""
        print("\n[测试] demo.html...")
        
        demo_file = os.path.join(os.path.dirname(__file__), 'demo.html')
        self.assertTrue(os.path.exists(demo_file))
        print("  ✓ demo.html存在")
        
        with open(demo_file, 'r') as f:
            content = f.read()
            # 检查版本号
            self.assertIn('v2.7', content)
            # 检查场景功能
            self.assertIn('配置场景', content)
            self.assertIn('临时表模式', content)
        print("  ✓ demo.html包含新功能")


def run_full_regression_test():
    """运行完整回归测试"""
    print("\n" + "=" * 60)
    print("Oracle数据批量修改工具 - 全面回归测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试类
    test_classes = [
        TestConfigManager,
        TestOSCompatibility,
        TestExcelHandler,
        TestLogger,
        TestDataUpdater,
        TestGUIComponents,
        TestPortableScripts,
        TestDockerFiles,
        TestDocumentation,
        TestDemoHTML
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
    
    if result.failures:
        print("\n失败详情:")
        for test, traceback in result.failures:
            print(f"\n  {test}:")
            print(f"  {traceback}")
    
    if result.errors:
        print("\n错误详情:")
        for test, traceback in result.errors:
            print(f"\n  {test}:")
            print(f"  {traceback}")
    
    print("=" * 60)
    
    if result.wasSuccessful():
        print("✓ 所有测试通过！")
        return True
    else:
        print("✗ 存在测试失败！")
        return False


if __name__ == '__main__':
    success = run_full_regression_test()
    sys.exit(0 if success else 1)