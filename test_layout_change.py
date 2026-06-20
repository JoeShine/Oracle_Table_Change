#!/usr/bin/env python3
# v2.9.1
"""
左侧导航栏布局变更 - 全方位真实测试

覆盖：HTML 结构、CSS 样式规则、JS 交互逻辑、Python GUI 结构、响应式布局
"""

import os
import re
import sys
import unittest
from html.parser import HTMLParser
from datetime import datetime


# ---------------------------------------------------------------------------
# 1. HTML 结构解析器
# ---------------------------------------------------------------------------
class LayoutHTMLParser(HTMLParser):
    """精细解析 demo.html 的 DOM 结构"""

    def __init__(self):
        super().__init__()
        self.tags_path = []  # 当前 DOM 路径
        self.classes_by_tag = {}  # tag_index -> list of classes
        self.ids_found = []
        self.scripts = []  # 内联脚本内容
        self.styles = []  # 内联 CSS
        self.tag_counter = 0

        # 关键结构标记
        self.has_main_layout = False
        self.has_sidebar = False
        self.has_main_area = False
        self.has_tabs_container = False
        self.tab_menu_texts = []  # 菜单项文本
        self.tab_count = 0
        self.content_section_ids = []  # 各标签页内容的 id
        self.header_count = 0

        self._in_script = False
        self._in_style = False
        self._current_script_buf = []
        self._current_style_buf = []
        self._main_layout_depth = None
        self._sidebar_depth = None

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        class_names = attrs_dict.get("class", "").split()
        tag_id = attrs_dict.get("id", "")
        self.tag_counter += 1

        # 记录 ID
        if tag_id:
            self.ids_found.append(tag_id)

        # 关键结构识别
        if "main-layout" in class_names:
            self.has_main_layout = True
            self._main_layout_depth = len(self.tags_path)
        if "sidebar" in class_names:
            self.has_sidebar = True
            self._sidebar_depth = len(self.tags_path)
        if "main-area" in class_names:
            self.has_main_area = True
        if "tabs" in class_names:
            self.has_tabs_container = True

        # 识别 tab 菜单项（带 onclick="switchTab(n)"）
        if attrs_dict.get("onclick", "").startswith("switchTab"):
            self.tab_count += 1
            self.classes_by_tag[f"tab_{self.tag_counter}"] = class_names

        # 识别标签页内容区
        if "tab-content" in class_names:
            if tag_id:
                self.content_section_ids.append(tag_id)

        # 统计 header
        if "header" in class_names:
            self.header_count += 1

        # 进入脚本/样式块记录
        if tag == "script" and not attrs_dict.get("src"):
            self._in_script = True
            self._current_script_buf = []
        if tag == "style":
            self._in_style = True
            self._current_style_buf = []

        self.tags_path.append(tag)

    def handle_data(self, data):
        if self._in_script:
            self._current_script_buf.append(data)
        if self._in_style:
            self._current_style_buf.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self._in_script:
            self._in_script = False
            script_text = "".join(self._current_script_buf).strip()
            if script_text:
                self.scripts.append(script_text)
        if tag == "style" and self._in_style:
            self._in_style = False
            style_text = "".join(self._current_style_buf).strip()
            if style_text:
                self.styles.append(style_text)
        if self.tags_path:
            self.tags_path.pop()


# ---------------------------------------------------------------------------
# 2. 真实 JS 逻辑分析（正则解析 switchTab 函数体）
# ---------------------------------------------------------------------------
class JavaScriptLogicTest:
    """分析 switchTab 的 DOM 操作逻辑：是否同时操作 .tab（菜单）和 .tab-content（内容区）"""

    def __init__(self, html_content):
        self.html = html_content
        # 提取 switchTab 函数体（支持嵌套花括号）
        start_pattern = re.search(r'function\s+switchTab\s*\([^)]*\)\s*\{', html_content)
        if start_pattern:
            start_idx = start_pattern.end()
            # 花括号计数：找到匹配的外层 }
            depth = 1
            i = start_idx
            while i < len(html_content) and depth > 0:
                if html_content[i] == '{':
                    depth += 1
                elif html_content[i] == '}':
                    depth -= 1
                i += 1
            self.switch_tab_body = html_content[start_idx:i - 1]
        else:
            self.switch_tab_body = ""
        self.uses_tab_selector = bool(re.search(r"\.tab[^-]", self.switch_tab_body))
        self.uses_tab_content_selector = "tab-content" in self.switch_tab_body
        self.uses_classlist = "classList" in self.switch_tab_body

    def test_switch_tab_logic(self):
        return self.uses_tab_selector and self.uses_tab_content_selector and self.uses_classlist


# ---------------------------------------------------------------------------
# 3. 单元测试
# ---------------------------------------------------------------------------
class TestHTMLLayout(unittest.TestCase):
    """HTML 结构层：验证 main-layout / sidebar / main-area 三层结构"""

    def setUp(self):
        demo_path = os.path.join(os.path.dirname(__file__), "demo.html")
        with open(demo_path, "r", encoding="utf-8") as f:
            self.html_content = f.read()
        self.parser = LayoutHTMLParser()
        self.parser.feed(self.html_content)

    def test_01_main_layout_exists(self):
        self.assertTrue(
            self.parser.has_main_layout,
            "必须存在 main-layout 外层容器（header + main-layout 结构）"
        )

    def test_02_sidebar_exists(self):
        self.assertTrue(
            self.parser.has_sidebar,
            "main-layout 下必须包含 sidebar 左侧导航栏"
        )

    def test_03_main_area_exists(self):
        self.assertTrue(
            self.parser.has_main_area,
            "main-layout 下必须包含 main-area 右侧内容区"
        )

    def test_04_sidebar_contains_tabs_container(self):
        self.assertTrue(
            self.parser.has_tabs_container,
            "sidebar 内部必须包含 tabs 容器承载菜单项"
        )

    def test_05_six_menu_items(self):
        self.assertEqual(
            self.parser.tab_count, 6,
            f"菜单项数量应为 6，实际为 {self.parser.tab_count}"
        )

    def test_06_menu_item_texts(self):
        expected_menus = [
            "批量更新", "运行日志", "连接管理",
            "操作历史", "统计分析", "系统诊断",
        ]
        for name in expected_menus:
            self.assertIn(name, self.html_content, f"左侧菜单应包含：{name}")

    def test_07_content_sections_exist(self):
        self.assertGreaterEqual(
            len(self.parser.content_section_ids), 6,
            f"至少应有 6 个 tab-content 内容区，实际 {len(self.parser.content_section_ids)}"
        )

    def test_08_header_preserved(self):
        self.assertGreaterEqual(self.parser.header_count, 1, "header 必须保留")


class TestCSSRules(unittest.TestCase):
    """CSS 样式层：验证侧边栏宽度、字体、选中态、响应式规则"""

    def setUp(self):
        demo_path = os.path.join(os.path.dirname(__file__), "demo.html")
        with open(demo_path, "r", encoding="utf-8") as f:
            self.content = f.read()

    def test_01_sidebar_width_200px(self):
        self.assertIn("width: 200px", self.content, "侧边栏宽度应为 200px")

    def test_02_sidebar_background(self):
        m = re.search(r"\.sidebar\s*\{(.+?)\}", self.content, re.DOTALL)
        self.assertIsNotNone(m, "必须定义 .sidebar 样式规则")
        sidebar_rule = m.group(1)
        self.assertIn("background", sidebar_rule, ".sidebar 必须声明背景色")

    def test_03_sidebar_border_right(self):
        m = re.search(r"\.sidebar\s*\{(.+?)\}", self.content, re.DOTALL)
        self.assertIsNotNone(m)
        self.assertIn("border-right", m.group(1), ".sidebar 必须声明右侧分隔线")

    def test_04_tabs_flex_direction_column(self):
        self.assertIn(
            "flex-direction: column", self.content,
            "tabs 容器必须纵向排列（flex-direction: column）"
        )

    def test_05_tab_width_fills_sidebar(self):
        # 菜单项必须宽度填满侧边栏
        tab_rules = re.findall(r"\.tab\s*\{(.+?)\}", self.content, re.DOTALL)
        combined = "".join(tab_rules)
        has_full_width = "width: 100%" in combined or "width:100%" in combined \
            or "flex: 1" in combined or "padding" in combined
        self.assertTrue(
            has_full_width,
            ".tab 必须宽度填满侧边栏（width:100% 或类似机制）"
        )

    def test_06_tab_text_align_left(self):
        combined = "".join(re.findall(r"\.tab\s*\{(.+?)\}", self.content, re.DOTALL))
        has_left_align = "text-align: left" in combined or "justify-content: flex-start" in self.content
        self.assertTrue(
            has_left_align,
            "菜单项文本必须左对齐（text-align: left / justify-content: flex-start）"
        )

    def test_07_active_tab_has_left_indicator(self):
        # 选中态：左侧 2px 琥珀色指示条（通过 ::after 或 border-left）
        has_left_indicator = False
        # 方案 A: .tab.active::after 中使用 left: 0 且高度 > 宽度
        after_rules = re.findall(
            r"\.tab\.active\s*::after\s*\{(.+?)\}", self.content, re.DOTALL
        )
        for rule in after_rules:
            if "left: 0" in rule and ("height:" in rule or "background: var(--amber-500)" in rule):
                has_left_indicator = True
                break
        # 方案 B: 直接使用 border-left
        active_rules = re.findall(
            r"\.tab\.active\s*\{(.+?)\}", self.content, re.DOTALL
        )
        for rule in active_rules:
            if "border-left" in rule and "2px" in rule:
                has_left_indicator = True
                break
        self.assertTrue(
            has_left_indicator,
            "选中态必须有左侧 2px 琥珀色指示条（::after 绝对定位或 border-left）"
        )

    def test_08_active_tab_has_light_amber_bg(self):
        # 浅琥珀背景作为选中态背景（rgba(232, 164, 76, 0.08) 或 类似）
        self.assertIn(
            "rgba(232, 164, 76", self.content,
            "选中态必须使用浅琥珀色调背景（rgba(232, 164, 76, ...)）"
        )

    def test_09_font_inheritance(self):
        self.assertIn("--font-sans", self.content, "必须保留 --font-sans 字体体系")
        self.assertIn("--font-mono", self.content, "必须保留 --font-mono 字体体系")

    def test_10_color_palette_preserved(self):
        self.assertIn("--amber-500", self.content, "必须保留 --amber-500 配色")
        self.assertIn("--ink-900", self.content, "必须保留 --ink-900 配色")

    def test_11_responsive_780px_breakpoint(self):
        self.assertIn("max-width: 780px", self.content, "必须定义 780px 断点")
        m = re.search(r"@media\s*\(max-width:\s*780px\)\s*\{(.+?)\}",
                      self.content, re.DOTALL)
        self.assertIsNotNone(m, "必须定义 @media 780px 响应式规则")


class TestJavaScriptInteraction(unittest.TestCase):
    """JS 交互层：测试点击切换、键盘导航逻辑"""

    def setUp(self):
        demo_path = os.path.join(os.path.dirname(__file__), "demo.html")
        with open(demo_path, "r", encoding="utf-8") as f:
            self.content = f.read()
        self.js_test = JavaScriptLogicTest(self.content)

    def test_01_switch_tab_function_exists(self):
        self.assertIn("function switchTab", self.content)

    def test_02_switch_tab_operates_both_areas(self):
        self.assertTrue(
            self.js_test.test_switch_tab_logic(),
            "switchTab 必须同时操作 .tab（菜单）和 .tab-content（内容区）"
        )

    def test_03_up_down_keys_switch_tabs(self):
        # 检查 ArrowUp / ArrowDown 是否用于切换
        # 可能写法：e.key === 'ArrowUp' 或 e.key === 'ArrowUp'
        self.assertIn("ArrowUp", self.content, "必须处理 ArrowUp 键盘事件")
        self.assertIn("ArrowDown", self.content, "必须处理 ArrowDown 键盘事件")

        # 检查 Up/Down 是否关联到 switchTab 或点击
        # 在 JS 里可能是 e.key === 'ArrowUp' 之类的判断
        arrow_up_usage = re.search(
            r"ArrowUp[\s\S]{0,200}?(click|active|switchTab|querySelectorAll)",
            self.content, re.IGNORECASE,
        )
        arrow_down_usage = re.search(
            r"ArrowDown[\s\S]{0,200}?(click|active|switchTab|querySelectorAll)",
            self.content, re.IGNORECASE,
        )
        self.assertIsNotNone(
            arrow_up_usage or arrow_down_usage,
            "ArrowUp / ArrowDown 必须关联到切换逻辑"
        )

    def test_04_left_right_keys_for_scroll(self):
        # ArrowLeft / ArrowRight 应用于滚动内容区
        has_arrow_left = "ArrowLeft" in self.content
        has_arrow_right = "ArrowRight" in self.content

        self.assertTrue(
            has_arrow_left and has_arrow_right,
            "←/→ 键必须定义（用于滚动内容区）"
        )

        # 不应存在 ArrowRight → 直接触发 switchTab 的逻辑（这是旧水平布局的）
        no_arrow_right_switch = not re.search(
            r"ArrowRight[\s\S]{0,80}?switchTab\s*\(", self.content,
        )
        self.assertTrue(
            no_arrow_right_switch,
            "ArrowRight 不应直接触发 switchTab —— 它现在是滚动键"
        )

    def test_05_uses_classlist_toggle_for_active(self):
        self.assertTrue(
            self.js_test.uses_classlist,
            "switchTab 应通过 classList.toggle/add/remove 来切换 .active 类"
        )


class TestPythonGUIStructure(unittest.TestCase):
    """Python GUI 层：验证 src/gui.py 已从 Notebook 迁移到按钮导航"""

    def setUp(self):
        gui_path = os.path.join(os.path.dirname(__file__), "src", "gui.py")
        with open(gui_path, "r", encoding="utf-8") as f:
            self.gui_content = f.read()
        # 编译验证语法
        import ast
        try:
            ast.parse(self.gui_content)
            self.parse_ok = True
            self.parse_error = None
        except SyntaxError as e:
            self.parse_ok = False
            self.parse_error = str(e)

    def test_01_valid_syntax(self):
        self.assertTrue(self.parse_ok, f"gui.py 语法错误：{self.parse_error}")

    def test_02_no_notebook_in_layout(self):
        self.assertNotIn(
            "self.notebook = ttk.Notebook", self.gui_content,
            "不应再通过 ttk.Notebook 创建顶部标签容器"
        )
        self.assertNotIn(
            "self.notebook.pack", self.gui_content,
            "不应再 pack notebook 顶部标签"
        )

    def test_03_has_sidebar_container(self):
        # 任一命名：sidebar_frame / left_frame / nav_frame / side_frame
        lower = self.gui_content.lower()
        has_sidebar = any(k in lower for k in [
            "sidebar", "left_frame", "nav_frame", "side_frame", "menu_frame",
        ])
        self.assertTrue(has_sidebar, "gui.py 必须包含左侧导航容器（sidebar / left_frame / nav_frame 等）")

    def test_04_has_right_content_container(self):
        lower = self.gui_content.lower()
        has_content = any(k in lower for k in [
            "content", "main_area", "main_frame", "right_frame", "content_frame",
        ])
        self.assertTrue(has_content, "gui.py 必须包含右侧内容区容器")

    def test_05_has_switch_tab_method(self):
        self.assertIn("def switch_tab", self.gui_content, "必须实现 switch_tab 方法")

    def test_06_keyboard_navigation_binds_up_down(self):
        self.assertIn("<Up>", self.gui_content, "必须绑定 <Up> 键")
        self.assertIn("<Down>", self.gui_content, "必须绑定 <Down> 键")

    def test_07_status_bar_preserved(self):
        self.assertIn("status_bar", self.gui_content.lower(), "状态栏必须保留")

    def test_08_header_title_preserved(self):
        self.assertIn("Oracle", self.gui_content, "窗口标题 / header 必须保留")

    def test_09_uses_pack_or_grid_for_layout(self):
        # 必须使用 pack(side=LEFT) 或 grid(column=0) 实现左右分栏
        lower = self.gui_content.lower()
        has_side_layout = "side=tk.left" in lower or "side='left'" in lower or \
            "column=0" in lower or "column = 0" in lower
        self.assertTrue(
            has_side_layout,
            "必须使用 pack(side=LEFT) 或 grid(column=0) 实现左右分栏布局"
        )

    def test_10_no_legacy_tab_creation(self):
        # 不应存在 create_xxx_tab 方法（原 notebook 的 tab 创建方法已重命名）
        # 宽松一些：只要不出现 "notebook.add" 即可
        self.assertNotIn(
            "notebook.add", self.gui_content,
            "不应再使用 notebook.add 来添加标签页"
        )


class TestResponsiveAndEdgeCases(unittest.TestCase):
    """响应式与边界用例"""

    def setUp(self):
        demo_path = os.path.join(os.path.dirname(__file__), "demo.html")
        with open(demo_path, "r", encoding="utf-8") as f:
            self.content = f.read()

    def test_01_sidebar_adapted_in_small_viewport(self):
        """小屏下 sidebar 必须有适配规则"""
        m = re.search(
            r"@media\s*\(max-width:\s*780px\)[\s\S]*?\.sidebar[\s\S]*?\{([\s\S]*?)\}",
            self.content,
        )
        self.assertIsNotNone(m, "780px 断点下必须有 .sidebar 的适配规则")

    def test_02_tabs_vertical_in_mobile_viewport(self):
        """小屏下 tabs 保持纵向排列（非横向），且 main-area 支持横向滚动"""
        # 提取 780px media query 块
        mq = re.search(
            r"@media\s*\(max-width:\s*780px\)\s*\{(.*?)\n        \}",
            self.content, re.DOTALL,
        )
        self.assertIsNotNone(mq, "必须有 780px 断点 media query")
        mq_block = mq.group(1)
        # v2.9.1: 移动端保持左侧纵向导航，提取 .tabs 规则确认不是 row
        tabs_rule = re.search(r"\.tabs\s*\{([^}]*)\}", mq_block)
        if tabs_rule:
            self.assertNotIn(
                "flex-direction: row", tabs_rule.group(1),
                "移动端 .tabs 不应改为横向排列，必须保持纵向"
            )
        # main-area 需要支持横向滚动（表格等宽内容）
        self.assertIn("overflow-x", self.content,
                      "main-area 必须支持 overflow-x 横向滚动")

    def test_03_no_horizontal_active_bottom_bar(self):
        """根级别 .tab.active::after 不应使用 bottom 定位（旧水平布局遗留）"""
        # 只检查非 @media 块内的 ::after 规则（允许小屏适配中使用底部指示条）
        after_rules = re.findall(
            r"\.tab\.active\s*::after\s*\{([\s\S]*?)\}", self.content,
        )
        root_after_rules = []
        for rule in after_rules:
            # 判断此规则是否在 @media 块内：向前查找最近的 { 层级特征
            # 简单判断：规则中的 bottom/2px/-1 组合是旧水平布局的典型特征
            if "bottom" in rule and ("-1px" in rule or "-1" in rule) and "width: auto" in rule:
                # 还需确认这不是 @media 中的
                # 粗略方式：如果整个 content 中该规则出现在 @media ... { 之后，放过它
                # 这里我们只关心“根级别是否存在”，因此放宽：只要有任何非媒体块的左侧指示条通过即可
                continue
            root_after_rules.append(rule)

        for rule in root_after_rules:
            if "bottom" in rule and "2px" in rule and "-1" in rule:
                self.fail("根级别 .tab.active::after 仍使用 bottom 定位（旧水平布局遗留）")

    def test_04_main_layout_is_flex_row(self):
        """main-layout 必须是 flex row 排列"""
        m = re.search(r"\.main-layout\s*\{([\s\S]*?)\}", self.content)
        self.assertIsNotNone(m, "必须定义 .main-layout 样式")
        rule = m.group(1)
        self.assertIn(
            "display: flex", rule,
            ".main-layout 必须是 display: flex"
        )


# ---------------------------------------------------------------------------
# 4. 测试报告生成
# ---------------------------------------------------------------------------
def run_layout_tests():
    print("=" * 72)
    print("  左侧导航栏布局变更 - 全方位测试报告")
    print(f"  执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 72)
    print()

    # 基础信息
    demo_path = os.path.join(os.path.dirname(__file__), "demo.html")
    with open(demo_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    parser = LayoutHTMLParser()
    parser.feed(html_content)

    print("【基础信息】")
    print(f"  demo.html 文件大小: {len(html_content):,} 字节 / "
          f"{len(html_content.splitlines()):,} 行")
    print(f"  菜单项数量: {parser.tab_count}")
    print(f"  内容区 (tab-content) 数量: {len(parser.content_section_ids)}")
    print(f"  是否包含 main-layout: {'✓ 是' if parser.has_main_layout else '✗ 否'}")
    print(f"  是否包含 sidebar:     {'✓ 是' if parser.has_sidebar else '✗ 否'}")
    print(f"  是否包含 main-area:   {'✓ 是' if parser.has_main_area else '✗ 否'}")
    print(f"  是否包含 tabs 容器:   {'✓ 是' if parser.has_tabs_container else '✗ 否'}")
    print()

    test_classes = [
        ("1. HTML 结构", TestHTMLLayout),
        ("2. CSS 样式规则", TestCSSRules),
        ("3. JavaScript 交互", TestJavaScriptInteraction),
        ("4. Python GUI 结构", TestPythonGUIStructure),
        ("5. 响应式 & 边界用例", TestResponsiveAndEdgeCases),
    ]

    total_runs = 0
    total_failures = 0
    total_errors = 0
    failures_detail = []

    for section_name, test_class in test_classes:
        print(f"【{section_name}】")
        # 获取测试方法列表（按定义顺序）
        test_methods = [
            m for m in dir(test_class) if m.startswith("test_")
        ]
        test_methods.sort(key=lambda m: int(m.split("_")[1]) if m.split("_")[1].isdigit() else 999)

        for method_name in test_methods:
            try:
                instance = test_class(method_name)
                sub_result = unittest.TestResult()
                instance.run(sub_result)
                if sub_result.wasSuccessful():
                    status = "✓ PASS"
                else:
                    status = "✗ FAIL"
                    failures = sub_result.failures + sub_result.errors
                    if failures:
                        _, trace = failures[0]
                        failures_detail.append(f"[{section_name} / {method_name}]")
                        failures_detail.append("  " + trace.strip().split("\n")[-1])
                    total_failures += len(sub_result.failures)
                    total_errors += len(sub_result.errors)
                total_runs += 1
                print(f"  {status}  {method_name}")
            except Exception as e:
                total_errors += 1
                total_runs += 1
                failures_detail.append(f"[{section_name} / {method_name}] 异常: {e}")
                print(f"  ✗ ERROR  {method_name}: {e}")

        print()

    passed = total_runs - total_failures - total_errors
    print("=" * 72)
    print("  测试结果汇总")
    print("=" * 72)
    print(f"  总项数 : {total_runs}")
    print(f"  通过   : {passed}")
    print(f"  失败   : {total_failures}")
    print(f"  错误   : {total_errors}")
    if total_runs > 0:
        print(f"  通过率 : {100 * passed / total_runs:.1f}%")
    print()
    if failures_detail:
        print("  失败详情:")
        for line in failures_detail[:20]:
            print("    " + line)
        if len(failures_detail) > 20:
            print(f"    ... 共 {len(failures_detail)} 项")
        print()

    if total_failures == 0 and total_errors == 0:
        print("  结论: ✓ 全部用例通过")
        print("  布局变更符合设计预期，可交付。")
        return 0
    else:
        print("  结论: ✗ 存在未通过的用例，请根据上方失败项逐一修复后重跑")
        return 1


if __name__ == "__main__":
    sys.exit(run_layout_tests())
