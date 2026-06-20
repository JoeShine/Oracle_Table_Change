# v2.9.1
#!/usr/bin/env python3
"""
DBForge - demo.html 测试脚本
测试HTML原型的结构和功能
"""

import os
import re
import sys
import unittest
from html.parser import HTMLParser


class HTMLStructureParser(HTMLParser):
    """解析HTML结构"""
    
    def __init__(self):
        super().__init__()
        self.tags = []
        self.ids = []
        self.classes = []
        self.functions = []
        self.current_depth = 0
    
    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        for attr in attrs:
            if attr[0] == 'id':
                self.ids.append(attr[1])
            elif attr[0] == 'class':
                self.classes.extend(attr[1].split())
    
    def handle_data(self, data):
        # 检测JavaScript函数定义
        if 'function ' in data:
            matches = re.findall(r'function\s+(\w+)\s*\(', data)
            self.functions.extend(matches)


class TestDemoHTML(unittest.TestCase):
    """demo.html 测试"""
    
    def setUp(self):
        self.demo_path = os.path.join(os.path.dirname(__file__), 'demo.html')
        with open(self.demo_path, 'r', encoding='utf-8') as f:
            self.content = f.read()
        self.parser = HTMLStructureParser()
        self.parser.feed(self.content)
    
    def test_01_file_exists(self):
        """测试文件存在"""
        print("\n[测试] demo.html文件存在...")
        self.assertTrue(os.path.exists(self.demo_path))
        print("  ✓ 文件存在")
    
    def test_02_html_structure(self):
        """测试HTML基本结构"""
        print("\n[测试] HTML基本结构...")
        
        # 检查DOCTYPE
        self.assertIn('<!DOCTYPE html>', self.content)
        
        # 检查基本标签
        self.assertIn('html', self.parser.tags)
        self.assertIn('head', self.parser.tags)
        self.assertIn('body', self.parser.tags)
        self.assertIn('title', self.parser.tags)
        
        print("  ✓ HTML结构正确")
    
    def test_03_meta_charset(self):
        """测试字符集设置"""
        print("\n[测试] 字符集设置...")
        self.assertIn('charset="UTF-8"', self.content)
        self.assertIn('lang="zh-CN"', self.content)
        print("  ✓ UTF-8编码和中文语言设置正确")
    
    def test_04_version_number(self):
        """测试版本号"""
        print("\n[测试] 版本号...")
        self.assertIn('v2.8.0', self.content)
        self.assertIn('v2.8.0', self.content)
        print("  ✓ 版本号v2.8.0正确")
    
    def test_05_scenario_feature(self):
        """测试场景功能（原模板）"""
        print("\n[测试] 场景功能...")
        
        # 检查"场景"关键词
        self.assertIn('配置场景', self.content)
        self.assertIn('选择场景', self.content)
        self.assertIn('保存为场景', self.content)
        self.assertIn('SCENARIO', self.content)
        
        # 确保不再有"模板"关键词（已改为场景）
        # 注意：可能还有少量"模板"在注释中，主要检查界面元素
        template_count = len(re.findall(r'模板', self.content))
        # 允许少量残留，但界面元素应全部改为场景
        self.assertTrue(template_count <= 2, f"发现过多'模板'关键词: {template_count}个")
        
        print("  ✓ 场景功能正确")
    
    def test_06_temp_schema_feature(self):
        """测试临时表模式选择"""
        print("\n[测试] 临时表模式选择...")
        
        # 检查临时表模式相关元素
        self.assertIn('临时表模式', self.content)
        self.assertIn('TEMP_SCHEMA', self.content)
        self.assertIn('tempSchema', self.content)
        
        # 检查临时表模式下拉框
        self.assertIn('id="tempSchema"', self.content)
        
        print("  ✓ 临时表模式选择功能正确")
    
    def test_07_tabs_structure(self):
        """测试左侧导航栏结构"""
        print("\n[测试] 左侧导航栏结构...")
        
        # 检查6个菜单项（v2.8.0 从顶部迁移到左侧纵向导航栏）
        tab_count = len(re.findall(r'onclick="switchTab\(\d\)"', self.content))
        self.assertEqual(tab_count, 6, f"应有6个菜单项，实际: {tab_count}")
        
        # 检查左侧布局结构
        self.assertIn('main-layout', self.content)
        self.assertIn('sidebar', self.content)
        self.assertIn('main-area', self.content)
        self.assertIn('tab-content', self.content)
        
        # 检查6个菜单文案
        self.assertIn('批量更新', self.content)
        self.assertIn('运行日志', self.content)
        self.assertIn('连接管理', self.content)
        self.assertIn('操作历史', self.content)
        self.assertIn('统计分析', self.content)
        self.assertIn('系统诊断', self.content)
        
        # 检查左侧导航样式（纵向、宽度、左侧指示条）
        self.assertIn('flex-direction: column', self.content)
        self.assertIn('width: 200px', self.content)
        self.assertIn('border-right: 1px solid var(--bg-line)', self.content)
        
        print("  ✓ 左侧导航栏结构正确")
    
    def test_08_theme_system(self):
        """测试主题系统"""
        print("\n[测试] 主题系统...")
        
        # 检查三套主题
        self.assertIn('theme-terminal', self.content)
        self.assertIn('theme-idea', self.content)
        self.assertIn('theme-light', self.content)
        
        # 检查深色模式
        self.assertIn('dark-mode', self.content)
        
        # 检查主题切换函数
        self.assertIn('setTheme', self.parser.functions)
        self.assertIn('toggleDarkMode', self.parser.functions)
        
        print("  ✓ 三套主题系统正确")
    
    def test_09_javascript_functions(self):
        """测试JavaScript函数"""
        print("\n[测试] JavaScript函数...")
        
        # 必要的函数
        required_functions = [
            'switchTab',
            'loadTemplate',
            'saveAsTemplate',
            'deleteTemplate',
            'checkDuplicates',
            'checkConsistency',
            'showConfirmModal',
            'hideConfirmModal',
            'testConnection',
            'addLog'
        ]
        
        for func in required_functions:
            self.assertIn(func, self.parser.functions, f"缺少函数: {func}")
        
        print(f"  ✓ {len(required_functions)}个必要函数存在")
    
    def test_10_modal_dialogs(self):
        """测试模态框"""
        print("\n[测试] 模态框...")
        
        # 检查模态框
        self.assertIn('modal-overlay', self.content)
        self.assertIn('confirmModal', self.parser.ids)
        self.assertIn('progressModal', self.parser.ids)
        self.assertIn('duplicateModal', self.parser.ids)
        self.assertIn('consistencyModal', self.parser.ids)
        self.assertIn('successModal', self.parser.ids)
        
        print("  ✓ 5个模态框存在")
    
    def test_11_status_bar(self):
        """测试状态栏"""
        print("\n[测试] 状态栏...")
        
        self.assertIn('status-bar', self.content)
        self.assertIn('sbConn', self.parser.ids)
        self.assertIn('sbUser', self.parser.ids)
        self.assertIn('sbDb', self.parser.ids)
        self.assertIn('sbAction', self.parser.ids)
        
        print("  ✓ 状态栏元素正确")
    
    def test_12_log_panel(self):
        """测试日志面板"""
        print("\n[测试] 日志面板...")
        
        self.assertIn('log-panel', self.content)
        self.assertIn('logContent', self.parser.ids)
        
        # 检查日志类型样式
        self.assertIn('log-info', self.content)
        self.assertIn('log-success', self.content)
        self.assertIn('log-error', self.content)
        self.assertIn('log-warning', self.content)
        
        print("  ✓ 日志面板正确")
    
    def test_13_data_table(self):
        """测试数据表格"""
        print("\n[测试] 数据表格...")
        
        self.assertIn('data-table', self.content)
        self.assertIn('previewTable', self.parser.ids)
        
        # 检查错误行样式
        self.assertIn('row-error', self.content)
        
        print("  ✓ 数据表格正确")
    
    def test_14_easy_connect_reference(self):
        """测试Easy Connect引用"""
        print("\n[测试] Easy Connect引用...")
        
        # 检查Easy Connect相关内容
        self.assertIn('Easy Connect', self.content)
        # 检查连接地址格式：IP:端口（如 192.168.1.100:1521）
        self.assertRegex(self.content, r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+')
        
        print("  ✓ Easy Connect连接方式说明正确")
    
    def test_15_empty_field_handling(self):
        """测试空字段处理说明"""
        print("\n[测试] 空字段处理说明...")
        
        # 检查空字段处理相关内容
        self.assertIn('空字段', self.content)
        self.assertIn('保留原值', self.content)
        self.assertIn('不更新', self.content)
        
        print("  ✓ 空字段处理说明正确")
    
    def test_16_unmatched_records(self):
        """测试未匹配记录说明"""
        print("\n[测试] 未匹配记录说明...")
        
        # 检查未匹配记录相关内容
        self.assertIn('未匹配', self.content)
        self.assertIn('key_value', self.content)
        
        print("  ✓ 未匹配记录说明正确")
    
    def test_17_form_elements(self):
        """测试表单元素"""
        print("\n[测试] 表单元素...")
        
        # 检查必要的表单元素ID
        form_ids = [
            'templateSelect',
            'schema',
            'tempSchema',
            'tableName',
            'keyColumn',
            'columnsList',
            'filePath',
            'fileMeta'
        ]
        
        for id_name in form_ids:
            self.assertIn(id_name, self.parser.ids, f"缺少表单元素ID: {id_name}")
        
        print(f"  ✓ {len(form_ids)}个表单元素存在")
    
    def test_18_css_variables(self):
        """测试CSS变量"""
        print("\n[测试] CSS变量...")
        
        # 检查关键CSS变量
        css_vars = [
            '--ink-900',
            '--accent-primary',
            '--color-success',
            '--bg',
            '--text-primary',
            '--radius-sm',
            '--shadow-sm',
            '--font-sans'
        ]
        
        for var in css_vars:
            self.assertIn(var, self.content, f"缺少CSS变量: {var}")
        
        print(f"  ✓ {len(css_vars)}个关键CSS变量存在")
    
    def test_19_responsive_design(self):
        """测试响应式设计"""
        print("\n[测试] 响应式设计...")
        
        # 检查媒体查询
        self.assertIn('@media', self.content)
        self.assertIn('max-width: 780px', self.content)
        self.assertIn('max-width: 380px', self.content)
        
        print("  ✓ 响应式设计媒体查询存在")
    
    def test_20_no_duplicate_switchTab(self):
        """测试switchTab函数无重复定义"""
        print("\n[测试] switchTab函数无重复...")
        
        # 检查switchTab函数定义次数
        switchtab_count = len(re.findall(r'function\s+switchTab\s*\(', self.content))
        self.assertEqual(switchtab_count, 1, f"switchTab函数应只定义一次，实际: {switchtab_count}次")
        
        print("  ✓ switchTab函数定义唯一")


def run_demo_html_tests():
    """运行demo.html测试"""
    import sys
    from datetime import datetime
    
    print("\n" + "=" * 60)
    print("DBForge - demo.html 测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestDemoHTML)
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
        print("✓ 所有测试通过！")
        return True
    else:
        print("✗ 存在测试失败！")
        return False


if __name__ == '__main__':
    success = run_demo_html_tests()
    sys.exit(0 if success else 1)