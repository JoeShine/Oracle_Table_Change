# 新增功能说明

## 功能概述

本次更新新增了两个重要的数据校验功能和一个全新的主题系统，帮助用户在进行数据批量更新前提前发现问题，同时提供更丰富的界面风格选择。

---

## 1. 重复性校验 (🔍 重复性校验按钮)

### 功能说明
检查Excel文件中唯一标识列是否存在重复值。

### 使用场景
- 在执行批量更新前，确保Excel中的唯一标识没有重复
- 避免因为重复数据导致的更新错误

### 使用步骤
1. 选择Excel文件
2. 点击 **"🔍 重复性校验"** 按钮
3. 系统自动检查Excel中第一列（唯一标识列）的重复值
4. 如果发现重复，会弹出对话框显示详细信息（包括重复值和对应的行号）

### 功能特点
- 显示所有重复的唯一标识值
- 显示每个重复值出现的行号
- 支持深色/浅色主题切换
- 在操作日志中记录校验结果

---

## 2. 一致性校验 (✅ 一致性校验按钮)

### 功能说明
检查Excel中的唯一标识列数据是否都存在于目标数据库表中。

### 使用场景
- 确保要更新的数据在数据库中都存在对应的记录
- 避免因为标识不存在导致的更新失败

### 使用步骤
1. 连接数据库
2. 配置目标表名和唯一标识列
3. 选择Excel文件
4. 点击 **"✅ 一致性校验"** 按钮
5. 系统将Excel中的标识与数据库中的标识进行比对
6. 如果有标识在数据库中不存在，会弹出对话框显示详细信息

### 功能特点
- 自动查询目标表的所有唯一标识值
- 比对Excel和数据库中的标识
- 显示数据库中缺失的标识列表
- 支持导出缺失标识到Excel文件
- 支持深色/浅色主题切换
- 在操作日志中记录校验结果

---

## 3. 三套主题风格系统 (🎨 主题切换)

### 功能说明
系统提供三套主题风格，每套均支持浅色/深色模式，共六种视觉方案。**默认风格为深墨琥珀（terminal）**，与 demo.html 原型一致。

### 三种风格
| 风格 | 主色调 | 设计灵感 | 默认 |
|------|--------|----------|------|
| **Idea 蓝色** | #4A86E8 蓝色 | IntelliJ IDEA IDE | - |
| **深墨琥珀** | #E8A44C 琥珀金 | Frontend Design / 终端风格 | ✓ |
| **清爽浅色** | #0066CC 清新蓝 | 极简干净设计 | - |

### 配色键（每套 26 个）
- name / name_en / bg / fg / primary / primary_dark / secondary
- success / error / warning / info
- card_bg / card_border / text_muted / text_heading
- button_bg / button_fg / button_secondary_bg / button_secondary_fg
- entry_bg / entry_border
- tree_bg / tree_alt / log_bg
- scrollbar_bg / status_bg
- tab_bg / tab_selected / tab_border
- header_bg（linear-gradient）/ header_fg

### 主题按钮（与代码 `gui.py` 第 393-397 行一致）
- 风格按钮：`Idea💡` / `深墨🖥` / `清爽✨`
- 深浅色按钮：`🌙 深色模式`（当前浅色时） / `☀️ 浅色模式`（当前深色时）

### 使用步骤
1. 点击顶部控制栏"主题:"标签后的风格按钮切换风格
2. 点击 `🌙 深色模式` / `☀️ 浅色模式` 切换当前风格的明暗模式
3. 主题设置自动保存到 `config.json`，下次启动时自动恢复

### 持久化字段
- `config.json` → `last_used.theme_style`：`idea` / `terminal` / `clean`，默认 `terminal`
- `config.json` → `last_used.theme_dark`：`true` / `false`，默认 `false`

### 启动恢复流程
1. `load_last_config` 读取 `theme_style` / `theme_dark`
2. `root.after(50, ...)` 延迟到 UI 渲染完成后应用
3. 调用 `_restore_theme(style_key, is_dark)` 切换主题
4. 异常时回退默认值，不影响程序启动

### 功能特点
- 每套风格有独立的浅色/深色配色方案（26 字段全部独立）
- 风格切换和深浅色切换独立工作，互不影响
- 按钮、输入框、表格、日志、标签页、滚动条、状态栏等所有组件统一配色
- 按钮选中态使用 `primary` 主色，按下态使用 `primary_dark` 加深
- 与 `demo.html` 原型视觉一致（含响应式断点 380px / 780px）

---

## 界面更新

### 按钮位置
两个新按钮位于"浏览"和"预览"按钮的右侧：
- [📁 浏览] [👁 预览] **[🔍 重复性校验]** **[✅ 一致性校验]**

### 状态栏更新
校验过程中会在状态栏显示当前操作状态：
- "正在检查重复值..."
- "正在检查一致性..."

---

## 测试文件

项目目录中提供了两个测试文件：

### 1. test_duplicate_data.xlsx
包含重复值的测试数据，用于测试重复性校验功能。

### 2. test_consistency_data.xlsx
包含数据库中不存在的ID的测试数据，用于测试一致性校验功能。

---

## 技术实现

### 修改的文件
1. `src/excel_handler.py` - 添加了Excel数据读取相关函数
2. `src/db_connection.py` - 添加了数据库查询功能
3. `src/gui.py` - 添加了新按钮和校验逻辑，新增三套主题系统
4. `src/config_manager.py` - 配置持久化增加 theme_style / theme_dark 字段

### 新增函数
- `ExcelHandler.get_key_values_from_excel()` - 获取Excel中唯一标识值
- `ExcelHandler.get_key_values_with_rows()` - 获取带行号的标识数据
- `DBConnection.get_key_values_from_table()` - 获取数据库表中的标识值
- `OracleBatchUpdaterGUI.check_duplicates()` - 重复性校验主逻辑
- `OracleBatchUpdaterGUI.show_duplicate_dialog()` - 显示重复值对话框
- `OracleBatchUpdaterGUI.check_consistency()` - 一致性校验主逻辑
- `OracleBatchUpdaterGUI.show_consistency_dialog()` - 显示一致性问题对话框
- `OracleBatchUpdaterGUI.switch_theme_style()` - 主题风格切换
- `OracleBatchUpdaterGUI.toggle_theme()` - 深浅色切换
- `OracleBatchUpdaterGUI._save_theme_config()` - 主题配置持久化
- `OracleBatchUpdaterGUI._restore_theme(style_key, is_dark)` - 启动时恢复主题
- `OracleBatchUpdaterGUI._update_theme_selector_buttons()` - 风格按钮选中态更新
- `ThemeManager.switch_theme_style()` - 切换风格并保留深浅模式
- `ThemeManager.set_style()` / `set_dark_mode()` / `toggle_dark_mode()` - 风格与模式 API

---

## 使用建议

1. **最佳实践流程**：
   - 配置数据库连接
   - 选择Excel文件
   - 点击"👁 预览"查看数据
   - 点击"🔍 重复性校验"检查重复
   - 点击"✅ 一致性校验"检查数据存在性
   - 确认无误后点击"✅ 确认"执行更新

2. **注意事项**：
   - 一致性校验需要先连接数据库
   - Excel文件的第一列必须是唯一标识列
   - 校验失败时建议先修正数据再执行更新

---

## 更新历史

| 版本 | 日期 | 说明 |
|------|------|------|
| 2.2 | 2026-06-19 | 校正默认风格为深墨琥珀；按代码 26 字段重写配色；补充按钮文字、持久化字段、启动恢复流程 |
| 2.1 | 2026-06-19 | 新增三套主题风格系统（Idea/Terminal/Clean） |
| 2.0 | 2026-05-20 | 新增重复性校验和一致性校验功能 |
