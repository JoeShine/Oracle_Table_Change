# 新增功能说明

## 功能概述

本次更新新增了多个重要功能，包括便携版打包、数据处理优化、系统兼容性增强等。

---

## 系统兼容性说明

### 发布方式兼容性

| 发布方式 | Windows 7 | Windows Server 2008 R2 | Windows 10+ | Windows Server 2016+ |
|---------|-----------|------------------------|-------------|----------------------|
| exe打包 | ✅ 支持 | ✅ 支持 | ✅ 支持 | ✅ 支持 |
| 便携版 | ✅ 支持 | ✅ 支持 | ✅ 支持 | ✅ 支持 |
| Docker | ❌ 不支持 | ❌ 不支持 | ✅ 支持 | ✅ 支持 |

**推荐：** Windows 7 和 Windows Server 2008 R2 用户使用 exe打包 或 便携版方式。

---

## 1. 便携版打包（新增）

### 功能说明
创建无需安装、解压即用的便携版，适合 Windows 7 和 Windows Server 2008 R2 等不支持 Docker 的系统。

### 使用场景
- 在不支持 Docker 的老旧系统上使用
- 需要便携携带工具（U盘、网络共享）
- 无管理员权限的环境

### 使用步骤

**创建便携版：**
```bash
# Windows环境
package.bat                # 先打包exe
scripts\create_portable.bat  # 创建便携版
```

**使用便携版：**
```bash
1. 解压 OracleBatchUpdater_Portable_v2.7.0.zip
2. 双击 OracleBatchUpdater_Portable.bat
```

### 功能特点
- 无需安装，解压即用
- 可放在U盘运行
- 数据完全隔离
- 支持完整便携版（包含Python环境）

---

## 2. 数据处理优化（新增）

### 空字段处理
- Excel中空字段 **保留目标表原值**，不更新为NULL
- 空字符串同样保留原值
- 日志中记录跳过的空字段

### 未匹配记录处理
- Excel中存在但目标表中不存在的key_value **不更新目标表**
- 日志中记录未匹配记录详情
- 统计显示：成功数、失败数、未匹配数

### 临时表Schema独立
- 临时表和目标表支持 **不同的Schema**
- 界面新增"临时表模式"输入框（支持手工填写，可点击⚙配置选项）
- 场景保存时保存临时表Schema配置

---

## 3. Easy Connect连接方式（新增）

### 功能说明
使用 Easy Connect 方式连接Oracle数据库，无需任何配置文件。

### 连接字符串格式
```
host:port/service_name
示例: 192.168.1.100:1521/ORCL
```

### 优势
- 无需配置 tnsnames.ora
- 无需配置 sqlnet.ora
- 无需设置 TNS_ADMIN 环境变量
- 直接使用已安装的Oracle客户端

---

## 4. 配置场景功能（新增）

### 功能说明
将配置保存为场景，方便下次快速加载。

### 使用步骤
1. 配置好目标表模式、临时表模式、表名、列等
2. 点击 **"💾 保存为场景"** 按钮
3. 输入场景名称和描述
4. 下次使用时，选择场景并点击 **"📂 加载"**

### 功能特点
- 场景名称验证（非空、长度限制）
- 场景描述支持
- 保存临时表Schema配置
- 支持覆盖同名场景

---

## 5. 键盘导航功能（新增）

### 功能说明
使用键盘快捷键快速导航界面。

### 支持的快捷键
| 快捷键 | 功能 |
|-------|------|
| ← / → | 切换标签页 |
| ↑ / ↓ | 纵向滚动 |
| Ctrl+S | 保存配置 |

---

## 6. 国产化适配（新增）

### 功能说明
适配国产操作系统，支持麒麟V10。

### 支持的系统
- 麒麟V10操作系统
- Windows Server 2008 R2及以上
- macOS / Linux

### 状态栏显示
- 显示当前操作系统类型
- 自动检测并适配字体

---

## 7. 重复性校验 (🔍 重复性校验按钮)

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

## 8. 一致性校验 (✅ 一致性校验按钮)

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

## 9. 三套主题风格系统 (🎨 主题切换)

### 功能说明
系统提供三套主题风格，每套均支持浅色/深色模式，共六种视觉方案。**默认风格为深墨琥珀（terminal）**，与 demo.html 原型一致。

### 三种风格
| 风格 | 主色调 | 设计灵感 | 默认 |
|------|--------|----------|------|
| **Idea 蓝色** | #4A86E8 蓝色 | IntelliJ IDEA IDE | - |
| **深墨琥珀** | #E8A44C 琥珀金 | Frontend Design / 终端风格 | ✓ |
| **清爽浅色** | #0066CC 清新蓝 | 极简干净设计 | - |

### 配色键（每套 30 个）
- name / name_en / bg / fg / primary / primary_dark / secondary
- success / error / warning / info
- card_bg / card_border / text_muted / text_heading
- button_bg / button_fg / button_secondary_bg / button_secondary_fg
- entry_bg / entry_border
- tree_bg / tree_alt / log_bg
- scrollbar_bg / status_bg
- tab_bg / tab_selected / tab_border
- header_bg（linear-gradient）/ header_fg

### 主题按钮（与代码 `gui.py` 一致）
- 风格按钮：`深墨🖥` / `Idea💡` / `清爽✨`
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
- 每套风格有独立的浅色/深色配色方案（30 字段全部独立）
- 风格切换和深浅色切换独立工作，互不影响
- 按钮、输入框、表格、日志、标签页、滚动条、状态栏等所有组件统一配色
- 按钮选中态使用 `primary` 主色，由 `_update_theme_selector_buttons()` 统一维护；tkinter 按钮无原生 hover/press 分离态
- 与 `demo.html` 原型视觉一致（含响应式断点 380px / 780px）

---

## 界面更新

### 按钮位置
操作按钮位于配置区域下方：
- [📁 浏览] [👁 预览] **[🔍 重复性校验]** **[✅ 一致性校验]**
- [🔍 验证数据] **[✅ 执行]**（初始禁用，验证通过后启用）

### 状态栏更新
校验过程中会在状态栏显示当前操作状态：
- "正在检查重复值..."
- "正在检查一致性..."
- "正在验证数据..."
- 右下角显示操作系统版本（如 Linux 6.8.0）

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
3. `src/gui.py` - 添加了新按钮和校验逻辑，新增三套主题系统，新增数据验证和Schema配置
4. `src/config_manager.py` - 配置持久化增加 theme_style / theme_dark 字段，新增 schema_values 配置
5. `src/data_updater.py` - SQL生成修复（AS别名），回滚逻辑修复

### 新增函数
- `ExcelHandler.get_key_values_from_excel()` - 获取Excel中唯一标识值
- `ExcelHandler.get_key_values_with_rows()` - 获取带行号的标识数据
- `DBConnection.get_key_values_from_table()` - 获取数据库表中的标识值
- `OracleBatchUpdaterGUI.check_duplicates()` - 重复性校验主逻辑
- `OracleBatchUpdaterGUI.show_duplicate_dialog()` - 显示重复值对话框
- `OracleBatchUpdaterGUI.check_consistency()` - 一致性校验主逻辑
- `OracleBatchUpdaterGUI.show_consistency_dialog()` - 显示一致性问题对话框
- `OracleBatchUpdaterGUI.validate_data()` - 数据验证（Excel+DB表/列）
- `OracleBatchUpdaterGUI.configure_schema_values()` - 配置Schema下拉选项
- `OracleBatchUpdaterGUI.refresh_schema_combos()` - 刷新Schema下拉列表
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
   - 点击"🔍 验证数据"验证Excel和数据库
   - 验证通过后点击"✅ 执行"执行更新

2. **注意事项**：
   - 一致性校验需要先连接数据库
   - Excel文件的第一列必须是唯一标识列
   - 校验失败时建议先修正数据再执行更新

---

## 更新历史

| 版本 | 日期 | 说明 |
|------|------|------|
| 2.2 | 2026-06-19 | 校正默认风格为深墨琥珀；按代码 30 字段重写配色；补充按钮文字、持久化字段、set_dark_mode 启动恢复 |
| 2.1 | 2026-06-19 | 新增三套主题风格系统（Idea/Terminal/Clean） |
| 2.0 | 2026-05-20 | 新增重复性校验和一致性校验功能 |
