#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Oracle数据批量修改工具 - 文档生成脚本
生成开发方案、部署方案、代码生成提示词、用户手册等文档
"""

import os
from datetime import datetime

def create_development_plan():
    """创建开发方案文档"""
    content = '''# Oracle数据批量修改工具 - 开发方案

**文档版本：** v2.0
**最后更新：** 2026-05-20
**文档状态：** 正式版

---

## 1. 项目计划

### 1.1 开发周期

| 阶段 | 任务 | 时间 |
|-----|------|------|
| 需求分析 | 需求调研、需求规格说明书编写 | 1天 |
| 系统设计 | 架构设计、详细设计、技术选型 | 1天 |
| 开发阶段 | 核心功能开发、GUI开发 | 3天 |
| 测试阶段 | 功能测试、性能测试、Bug修复 | 1天 |
| 文档编写 | 用户手册、开发文档、部署文档 | 1天 |
| 打包发布 | PyInstaller打包、发布测试 | 1天 |

### 1.2 里程碑

| 里程碑 | 交付物 |
|-------|-------|
| M1 - 设计完成 | 需求规格说明书、设计方案 |
| M2 - 开发完成 | 可运行的程序代码 |
| M3 - 测试完成 | 测试报告 |
| M4 - 发布完成 | 安装包、文档、用户手册 |

---

## 2. 技术选型

### 2.1 开发语言

- **Python 3.7+**
  - 丰富的第三方库生态
  - 跨平台支持
  - 学习门槛低
  - tkinter GUI库内置

### 2.2 核心依赖库

| 库名 | 用途 | 版本 |
|-----|------|-----|
| oracledb | Oracle数据库连接 | 最新版 |
| openpyxl | Excel文件操作 | 最新版 |
| pyinstaller | 打包成exe | 最新版 |

### 2.3 开发工具

- **IDE**：PyCharm / VS Code
- **版本控制**：Git
- **打包工具**：PyInstaller

---

## 3. 开发规范

### 3.1 代码规范

- 遵循PEP 8代码规范
- 函数和类添加文档字符串
- 关键逻辑添加注释
- 使用有意义的变量名
- 代码模块化，避免重复

### 3.2 Git提交规范

```
<类型>: <描述>

类型：
- feat: 新功能
- fix: 修复bug
- docs: 文档更新
- refactor: 重构
- test: 测试相关
- chore: 构建/工具类改动
```

### 3.3 分支策略

```
main (主分支)
  └── develop (开发分支)
      └── feature-xxx (功能分支)
```

---

## 4. 开发流程

### 4.1 需求阶段

1. 分析用户需求
2. 编写需求规格说明书
3. 需求评审确认

### 4.2 设计阶段

1. 系统架构设计
2. 模块详细设计
3. 设计方案评审

### 4.3 开发阶段

1. 搭建项目结构
2. 逐个模块开发
3. 单元测试
4. 代码Review

### 4.4 集成测试

1. 模块集成
2. 功能测试
3. 性能测试

### 4.5 发布阶段

1. 编写文档
2. 打包
3. 发布

---

## 5. 测试计划

### 5.1 单元测试

- 测试各模块的独立功能
- 重点测试Excel解析、数据库连接、数据更新逻辑
- 测试覆盖率 > 80%

### 5.2 集成测试

- 测试模块间的协作
- 测试完整的数据更新流程
- 测试异常场景

### 5.3 性能测试

| 指标 | 目标 |
|-----|------|
| 启动时间 | < 3秒 |
| Excel处理速度 | 10000条/秒 |
| 更新速度 | 5000条/秒 |
| 内存占用 | < 500MB |

### 5.4 兼容性测试

- Windows 7、10、11
- Oracle 11g、12c、19c

---

## 6. 开发检查清单

### 6.1 功能开发

- [ ] 数据库连接管理
- [ ] Excel导入和验证
- [ ] 数据预览
- [ ] 数据更新
- [ ] 备份和回滚
- [ ] 日志记录
- [ ] 历史记录
- [ ] 审计日志
- [ ] 多列更新
- [ ] 进度显示
- [ ] 主题切换
- [ ] 快捷键

### 6.2 UI开发

- [ ] 主界面布局
- [ ] 标签页
- [ ] 对话框
- [ ] 状态栏
- [ ] 进度窗口
- [ ] 确认对话框

### 6.3 文档

- [ ] 需求规格说明书
- [ ] 设计方案
- [ ] 开发方案（本文件）
- [ ] 部署方案
- [ ] 用户手册
- [ ] 代码注释

---

## 7. 风险和应对

| 风险 | 影响 | 概率 | 应对措施 |
|-----|------|------|---------|
| Oracle驱动兼容性问题 | 高 | 中 | 使用成熟的oracledb库，多版本测试 |
| 大文件处理卡顿 | 中 | 高 | 使用流式处理，分批加载 |
| 性能不达标 | 中 | 中 | 优化SQL，批量提交 |
| 需求变更 | 中 | 中 | 预留扩展接口，模块化设计 |

---

## 8. 变更历史

| 版本 | 日期 | 修改人 | 变更内容 |
|-----|------|-------|---------|
| v1.0 | 2026-05-15 | - | 初版 |
| v2.0 | 2026-05-20 | - | 更新开发计划和任务 |
'''
    with open('docs/开发方案.md', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ 开发方案.md 已创建')


def create_deployment_plan():
    """创建部署方案文档"""
    content = '''# Oracle数据批量修改工具 - 部署方案

**文档版本：** v2.0
**最后更新：** 2026-05-20
**文档状态：** 正式版

---

## 1. 系统要求

### 1.1 硬件要求

| 配置 | 最低配置 | 推荐配置 |
|-----|---------|---------|
| CPU | 双核 2.0GHz | 四核 3.0GHz+ |
| 内存 | 2GB | 4GB+ |
| 硬盘 | 500MB | 1GB+ |
| 网络 | 100Mbps | 1Gbps |

### 1.2 软件要求

| 软件 | 版本要求 |
|-----|---------|
| 操作系统 | Windows 7及以上 |
| Oracle Instant Client | 11g及以上 |
| .NET Framework (某些环境) | 4.5+ |

---

## 2. 部署前准备

### 2.1 获取安装包

方式一：从GitHub下载
```
访问：https://github.com/JoeShine/Oracle_Table_Change
下载：OracleBatchUpdater.zip
```

方式二：自行构建（见构建章节）

### 2.2 安装Oracle Instant Client

1. 下载Oracle Instant Client
   - 地址：https://www.oracle.com/database/technologies/instant-client/downloads.html
   - 选择对应操作系统的版本（Basic或Basic Light）

2. 解压到指定目录
   ```
   C:\\oracle\\instantclient_19_8
   ```

3. 配置环境变量
   ```
   PATH = C:\\oracle\\instantclient_19_8;%PATH%
   ```

4. 验证安装
   - 在命令行运行：`sqlplus -v`

### 2.3 准备数据库账号

需要准备的权限：
- SELECT：查询表结构和数据
- INSERT：向临时表插入数据
- UPDATE：更新目标表
- CREATE TABLE：创建备份表和临时表
- DROP TABLE：删除临时表

---

## 3. 部署步骤

### 3.1 安装程序

1. 解压 `OracleBatchUpdater.zip` 到指定目录
   ```
   C:\\Program Files\\OracleBatchUpdater
   ```

2. 目录结构
   ```
   OracleBatchUpdater/
   ├── OracleBatchUpdater.exe    # 主程序
   ├── Oracle数据批量修改工具_导入模板.xlsx   # Excel模板
   ├── docs/                     # 文档目录
   ├── logs/                     # 日志目录
   ├── README.txt                # 说明文档
   └── LICENSE.txt               # 许可协议
   ```

### 3.2 首次运行

1. 双击 `OracleBatchUpdater.exe` 启动程序
2. 配置数据库连接
3. 测试连接
4. 保存配置

### 3.3 验证部署

测试清单：
- [ ] 程序能正常启动
- [ ] 能连接到数据库
- [ ] 能选择Excel文件
- [ ] 能预览Excel数据
- [ ] 能正常退出程序

---

## 4. 配置说明

### 4.1 配置文件位置

配置文件自动保存到：
```
%APPDATA%\\OracleTableChange\\config.json
```

### 4.2 日志文件位置

日志文件保存到：
```
程序目录\\logs\\
```

日志文件命名规则：
- 普通日志：`update_YYYYMMDD_HHMMSS.log`
- 审计日志：`audit.log`
- 历史记录：`history.json`

---

## 5. 升级步骤

### 5.1 备份

1. 备份配置文件
2. 备份重要日志
3. （可选）备份Excel模板

### 5.2 安装新版本

1. 下载新版本
2. 关闭旧版本程序
3. 解压覆盖安装（保留配置文件）
4. 启动新版本

---

## 6. 卸载步骤

1. 关闭程序
2. 删除安装目录
3. （可选）删除配置目录：`%APPDATA%\\OracleTableChange`
4. （可选）删除日志和历史数据

---

## 7. 故障排查

### 7.1 常见问题

| 问题 | 原因 | 解决方案 |
|-----|------|---------|
| 启动失败 | 缺少依赖库 | 确认已安装Oracle Instant Client |
| 连接失败 | 网络问题 | 检查网络连接、主机地址、端口 |
| 连接失败 | 账号密码错误 | 检查用户名密码 |
| 中文乱码 | 编码问题 | 设置NLS_LANG环境变量 |
| Excel导入失败 | 文件格式错误 | 使用提供的模板 |
| 更新失败 | 权限不足 | 确认数据库账号权限 |

### 7.2 日志查看

1. 打开程序目录下的 `logs` 文件夹
2. 查看最新的日志文件
3. 搜索 ERROR 或 WARNING

---

## 8. 安全建议

1. 定期备份数据库
2. 在测试环境先验证
3. 操作前检查Excel数据
4. 保存审计日志
5. 限制访问权限

---

## 9. 构建说明（高级）

### 9.1 环境准备

```bash
# 安装Python 3.7+
# 安装依赖
pip install -r requirements.txt
```

### 9.2 打包

```bash
# 方式一：使用build.bat
build.bat

# 方式二：手动执行
pyinstaller --clean OracleBatchUpdater.spec
```

### 9.3 输出

打包后的文件在 `dist/` 目录下：
```
dist/OracleBatchUpdater/
└── OracleBatchUpdater.exe
```

---

## 10. 变更历史

| 版本 | 日期 | 修改人 | 变更内容 |
|-----|------|-------|---------|
| v1.0 | 2026-05-15 | - | 初版 |
| v2.0 | 2026-05-20 | - | 完善部署细节 |
'''
    with open('docs/部署方案.md', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ 部署方案.md 已创建')


def create_code_prompt():
    """创建代码生成提示词文档"""
    content = '''# Oracle数据批量修改工具 - 代码生成提示词文档

**文档版本：** v2.0
**最后更新：** 2026-05-20
**文档状态：** 正式版

---

## 概述

本文档提供了使用AI大模型生成完整Oracle数据批量修改工具代码的详细提示词。可以将这些提示词直接提供给ChatGPT、Claude等AI模型，让其协助生成代码。

---

## 1. 项目初始化提示词

### 1.1 项目创建提示词

```
请帮我创建一个Oracle数据批量修改工具项目，使用Python语言开发。

技术栈要求：
- GUI：Python tkinter
- 数据库：oracledb库连接Oracle
- Excel：openpyxl处理.xlsx文件
- 打包：PyInstaller

项目功能需求（按优先级）：

P0（核心功能）：
1. 数据库连接管理（支持多个连接配置）
2. Excel文件导入（第一列唯一标识，第二列开始待更新列）
3. 数据更新（备份 -> 导入临时表 -> 更新 -> 清理）
4. 操作日志记录和显示
5. 错误处理和异常捕获

P1（重要功能）：
6. Excel数据预览
7. 数据验证（重复键、文件大小、行数限制）
8. 更新前二次确认
9. 失败记录导出

P2（增强功能）：
10. 历史记录管理
11. 审计日志
12. 多列同时更新
13. 实时进度显示
14. 深色/浅色主题切换

P3（体验优化）：
15. 快捷键支持（Ctrl+S保存）
16. 状态栏显示
17. 平滑的界面效果

设计风格要求：
- 采用Idea IDE风格配色（蓝色主题）
- 浅色和深色双主题
- 标签页式界面布局

请先输出项目目录结构，再逐个模块实现。
```

---

## 2. 模块开发提示词

### 2.1 配置管理模块

```
请帮我实现配置管理模块 (config_manager.py)，功能需求：

1. JSON格式存储配置
2. 支持多个数据库连接配置
3. 记录最近使用的配置（连接名、表名、列名等）
4. 支持连接的增删改查
5. 配置文件保存到用户目录下的 .OracleTableChange 文件夹

需要实现的类和方法：
- ConfigManager 类
  - __init__()
  - get_config()
  - save_config()
  - get_connections()
  - get_connection_by_name(name)
  - add_connection(connection)
  - delete_connection(name)
  - get_last_used()
  - set_last_used(last_used)

数据结构：
{
  "last_used": {
    "connection_name": "dev",
    "target_table": "EMP",
    "key_column": "EMP_ID",
    "update_column": "EMP_NAME",
    "schema": "APPS"
  },
  "connections": [
    {
      "name": "dev",
      "host": "192.168.1.100",
      "port": 1521,
      "service": "ORCL",
      "username": "scott",
      "password": "tiger"
    }
  ]
}
```

### 2.2 数据库连接模块

```
请帮我实现数据库连接模块 (db_connection.py)，功能需求：

1. 使用oracledb库连接Oracle数据库
2. 连接信息：host, port, service_name, username, password
3. 提供连接测试功能
4. 提供SQL执行功能
5. 提供查询功能
6. 提供获取表结构的功能
7. 事务管理（commit/rollback）
8. 连接状态检查

需要实现的类和方法：
- DBConnection 类
  - __init__()
  - connect(host, port, service, username, password)
  - disconnect()
  - is_connected()
  - execute_sql(sql, params=None, commit=True)
  - get_columns(table_name, schema=None)
  - table_exists(table_name, schema=None)

异常处理：
- 捕获数据库异常
- 返回友好的错误信息
```

### 2.3 Excel处理模块

```
请帮我实现Excel处理模块 (excel_handler.py)，功能需求：

1. 支持.xlsx和.xls格式
2. 验证Excel结构（至少两列）
3. 文件大小限制（10MB）
4. 行数限制（10万行）
5. 数据预览（前50行）
6. 检查重复键
7. 多列数据读取
8. 导出日志和失败记录

常量定义：
- MAX_FILE_SIZE = 10 * 1024 * 1024
- MAX_ROWS = 100000
- MAX_PREVIEW_ROWS = 50

需要实现的方法：
- validate_excel_structure(file_path)
- validate_multi_column_structure(file_path, update_columns)
- get_preview_data(file_path, max_rows=MAX_PREVIEW_ROWS)
- get_multi_column_preview(file_path, update_columns, max_rows=MAX_PREVIEW_ROWS)
- check_duplicate_keys(data_rows)
- export_logs(logs, file_path)
- export_failed_records(failed_records, file_path)
```

### 2.4 数据更新模块

```
请帮我实现数据更新模块 (data_updater.py)，功能需求：

1. 备份目标表（表名_BAK_时间戳）
2. 创建临时表
3. 导入Excel数据到临时表
4. 执行更新
5. 失败回滚
6. 清理临时表
7. 多列同时更新支持
8. 进度回调

需要实现的类和方法：
- DataUpdater 类
  - __init__(db_connection, log_manager)
  - set_progress_callback(callback)
  - backup_table(schema, table_name)
  - create_temp_table_multi_column(schema, table_name, key_column, update_columns)
  - import_excel_data_multi_column(schema, key_column, update_columns, data_rows)
  - execute_multi_column_update(schema, target_table, key_column, update_columns)
  - rollback(schema)
  - cleanup_temp_table(schema)
  - validate_table_and_columns_multi(schema, table_name, key_column, update_columns)
  - get_backup_info()

更新流程：
1. 验证表和列
2. 备份
3. 创建临时表
4. 导入数据
5. 执行更新
6. 清理临时表

注意：更新失败需要回滚！
```

### 2.5 日志模块

```
请帮我实现日志模块 (logger.py)，功能需求：

1. LogManager 主日志管理器
   - 记录日志
   - 导出日志
   - 记录失败记录

2. AuditLogger 审计日志
   - 记录关键操作（连接、更新、导出）
   - JSON格式存储
   - 不可修改

3. HistoryManager 历史记录
   - 记录更新历史
   - 支持查询
   - 支持删除

需要实现的类和方法：
- AuditLogger 类
  - log_action(action_type, details, user, success, error_msg)
  - get_audit_logs(limit, action_type)
  - delete_audit_logs(before_date)

- HistoryManager 类
  - add_record(record)
  - get_records(limit)
  - delete_records(record_ids)
  - clear_all()

- LogManager 类
  - __init__()
  - init_logger()
  - info(message)
  - success(message)
  - error(message)
  - warning(message)
  - add_failed_record(key_value, update_value, reason)
  - get_failed_records()
  - log_connection(...)
  - log_update(...)
  - log_export(...)
  - log_rollback(...)
  - get_audit_logs(...)
  - get_history_records(...)
```

### 2.6 GUI主界面模块

```
请帮我实现完整的GUI模块 (gui.py)，这是最大的模块。

主要功能：
1. 主窗口（1000x800）
2. 标签页：当前配置、操作日志、数据库连接、历史记录
3. 状态栏（从左到右：连接名、用户、数据库、连接状态、操作状态）
4. 主题切换（浅色/深色，Idea风格）
5. 配置表单：数据库模式、目标表、唯一标识列、待更新列（支持添加多个）
6. Excel文件选择和预览
7. 二次确认对话框
8. 进度显示窗口
9. 快捷键（Ctrl+S保存）

核心类：
- ThemeManager 类
  - LIGHT_THEME 配色字典
  - DARK_THEME 配色字典
  - toggle_theme()

- OracleBatchUpdaterGUI 类
  - __init__(root)
  - setup_styles()
  - create_widgets()
  - create_header()
  - create_status_bar()
  - create_config_tab()
  - create_log_tab()
  - create_connection_tab()
  - create_history_tab()
  - add_column_widget()
  - remove_column_widget()
  - get_update_columns()
  - browse_excel()
  - preview_excel()
  - confirm_update()
  - start_update()
  - test_connection()
  - update_status_bar(...)
  - bind_shortcuts()
  - save_config()

主题配色（Idea风格）：
浅色：
- bg: #F5F5F5
- fg: #3C3F41
- primary: #4A86E8
- success: #3592C4
- error: #C75050
- status_bg: #F0F0F0

深色：
- bg: #2B2B2B
- fg: #A9B7C6
- primary: #4A86E8
- success: #4E9A06
- error: #CC6666
- status_bg: #3C3F41

注意事项：
- 使用ttk组件
- 更新操作在后台线程，避免界面卡顿
- 进度通过回调更新
```

---

## 3. 测试提示词

### 3.1 功能测试提示词

```
请帮我编写完整的功能测试，测试以下功能：

1. 配置保存和加载
2. 数据库连接测试
3. Excel文件验证
4. 数据更新流程（成功/失败场景）
5. 日志记录

测试数据准备：
- 测试用的Excel文件
- 测试数据库和表

请输出完整的测试用例和步骤。
```

---

## 4. 文档生成提示词

### 4.1 用户手册提示词

```
请帮我编写一份详细的用户手册（Markdown格式），包含：

1. 产品介绍
2. 快速入门
3. 功能说明（每个功能模块详细说明）
4. 操作步骤（图文并茂的描述）
5. 常见问题FAQ
6. 最佳实践建议

风格要求：
- 通俗易懂
- 步骤清晰
- 对新手友好
- 包含操作建议和注意事项
```

---

## 5. 优化提示词

### 5.1 性能优化提示词

```
请帮我优化以下性能问题：

1. Excel大文件解析慢
2. 数据更新速度慢
3. 界面卡顿问题

当前实现的问题：
- 加载Excel时一次性读入内存
- 数据库更新单条提交
- 日志写入阻塞主线程

请提供优化方案和代码实现。
```

---

## 使用建议

1. 按顺序使用提示词：先初始化项目，再逐个模块开发
2. 每生成一个模块，先测试，再继续下一个
3. 遇到问题时，可以追问AI，提供上下文
4. 保持与AI的对话连贯，让它理解整个项目

---

## 变更历史

| 版本 | 日期 | 修改人 | 变更内容 |
|-----|------|-------|---------|
| v1.0 | 2026-05-15 | - | 初版 |
| v2.0 | 2026-05-20 | - | 完善提示词细节 |
'''
    with open('docs/代码生成提示词.md', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ 代码生成提示词.md 已创建')


def create_user_manual():
    """创建用户手册"""
    content = '''# Oracle数据批量修改工具 - 用户手册

**软件版本：** v2.0
**最后更新：** 2026-05-20

---

## 目录

1. [产品介绍](#1-产品介绍)
2. [安装配置](#2-安装配置)
3. [快速入门](#3-快速入门)
4. [功能详解](#4-功能详解)
5. [常见问题](#5-常见问题)
6. [最佳实践](#6-最佳实践)

---

## 1. 产品介绍

### 1.1 产品简介

Oracle数据批量修改工具是一款简单易用的数据库批量更新工具，通过Excel文件导入数据，实现Oracle数据库表的批量更新操作。

### 1.2 主要功能

- ✅ 数据库连接管理（支持多个连接配置）
- ✅ Excel数据导入（支持.xlsx/.xls格式）
- ✅ 数据预览（显示前50行）
- ✅ 多列同时更新
- ✅ 自动备份机制
- ✅ 失败自动回滚
- ✅ 操作日志和审计
- ✅ 历史记录管理
- ✅ 深色/浅色主题切换
- ✅ 快捷键支持

### 1.3 应用场景

- 批量修改员工信息
- 批量更新价格数据
- 批量同步基础数据
- 数据修正和清洗
- 定期批量数据更新

---

## 2. 安装配置

### 2.1 系统要求

| 配置 | 要求 |
|-----|------|
| 操作系统 | Windows 7及以上 |
| 内存 | 2GB以上 |
| 硬盘 | 500MB以上 |
| Oracle Client | 需要安装Oracle Instant Client |

### 2.2 安装Oracle Instant Client

1. 下载Oracle Instant Client
   - 访问：https://www.oracle.com/database/technologies/instant-client/downloads.html
   - 选择对应Windows版本的Basic或Basic Light

2. 解压到目录，例如：
   ```
   C:\\oracle\\instantclient_19_8
   ```

3. 配置环境变量：
   - 在系统环境变量PATH中添加：`C:\\oracle\\instantclient_19_8`
   - （可选）设置：`NLS_LANG=SIMPLIFIED CHINESE_CHINA.AL32UTF8`

### 2.3 安装本工具

1. 解压安装包到目录
2. 双击 `OracleBatchUpdater.exe` 即可运行
3. 无需安装，绿色便携

---

## 3. 快速入门

### 3.1 三步上手

#### 第一步：配置数据库连接

1. 切换到「数据库连接」标签页
2. 点击「+ 添加连接」
3. 填写连接信息：
   - 连接名称：给连接起个名字（如：开发环境）
   - 主机地址：数据库服务器地址
   - 端口：默认1521
   - 服务名：Oracle服务名
   - 用户名：数据库账号
   - 密码：数据库密码
4. 点击「测试连接」验证配置
5. 保存配置

#### 第二步：准备Excel数据

1. 使用提供的模板：`Oracle数据批量修改工具_导入模板.xlsx`
2. 按格式填写数据：
   - 第1列：唯一标识（如：员工ID）
   - 第2列起：要更新的列
3. 保存Excel文件

示例：
```
EMP_ID | EMP_NAME | AGE | DEPT
-------|----------|-----|-------
1001   | 张三     | 28  | 技术部
1002   | 李四     | 30  | 市场部
```

#### 第三步：执行更新

1. 切换到「当前配置」标签页
2. 填写配置：
   - 数据库模式：如APPS、SYS等
   - 目标表名：要更新的表名
   - 唯一标识列：Excel第1列对应的数据库列
   - 待修改列：点击「+添加列」添加要更新的列
3. 选择Excel文件
4. 点击「预览」查看数据
5. 点击「确认」开始更新
6. 在二次确认对话框中确认
7. 等待更新完成，查看结果

---

## 4. 功能详解

### 4.1 当前配置标签页

这是主要操作界面，包含：

#### 4.1.1 配置区域

- **数据库模式**：选择数据库模式（APPS/SYS/SYSTEM等）
- **目标表名**：输入要更新的数据库表名
- **唯一标识列**：Excel第1列对应的数据库列名，用于匹配记录
- **待修改列**：
  - 可以添加多个列
  - 点击「+」添加列
  - 点击「-」删除列
  - 顺序要与Excel一致

#### 4.1.2 Excel文件区域

- **选择文件**：点击「浏览」选择Excel文件
- **预览**：查看Excel前50行数据
- **提示**：
  - 最大10MB
  - 最多10万行
  - 使用.xlsx格式

#### 4.1.3 预览区域

- 显示Excel前50行数据
- 方便检查数据正确性
- 数据量大时提示「还有更多行」

#### 4.1.4 操作按钮

- **确认**：开始更新操作
- **清空**：清空表单

### 4.2 操作日志标签页

- 显示所有操作日志
- 按时间倒序排列
- 日志级别：
  - INFO：信息
  - SUCCESS：成功（绿色）
  - WARNING：警告（黄色）
  - ERROR：错误（红色）

- **导出日志**：导出所有日志
- **导出失败记录**：导出更新失败的记录
- **清空日志**：清空当前显示

### 4.3 数据库连接标签页

- 连接下拉框：选择已保存的连接
- 测试连接：测试选中的连接
- 添加连接：添加新的数据库连接
- 删除连接：删除当前选中的连接
- 连接信息显示区域：显示当前连接的详细信息

### 4.4 历史记录标签页

- 显示所有更新操作记录
- 包含：时间、表名、总数、成功数、失败数、状态
- 支持刷新
- 支持批量删除

### 4.5 状态栏

从左到右依次显示：

1. **连接名称**（加粗）：当前选中的数据库连接
2. **用户**：当前数据库用户
3. **数据库**：当前连接的数据库
4. **连接状态**：指示灯 + 文字
   - 🔴 未连接
   - 🟢 已连接
5. **操作状态**：当前正在执行的操作

### 4.6 主题切换

点击右上角的「🌙深色模式」或「☀️浅色模式」可以切换界面主题。

### 4.7 快捷键

- **Ctrl + S**：保存当前配置

---

## 5. 常见问题

### 5.1 安装问题

**Q: 启动时提示找不到Oracle客户端？**
A: 请确认已安装Oracle Instant Client，并配置了环境变量PATH。

**Q: 中文显示乱码？**
A: 设置环境变量：`NLS_LANG=SIMPLIFIED CHINESE_CHINA.AL32UTF8`

### 5.2 连接问题

**Q: 测试连接失败怎么办？**
A: 请检查：
1. 网络是否能连接到数据库服务器
2. 主机地址、端口、服务名是否正确
3. 用户名密码是否正确
4. 数据库是否允许远程连接

**Q: 连接超时？**
A: 检查防火墙设置，确认1521端口（或其他端口）已开放。

### 5.3 Excel问题

**Q: Excel导入失败？**
A: 请检查：
1. 是否使用提供的模板格式
2. 第一列是否是唯一标识，不能为空
3. 文件大小是否超过10MB
4. 行数是否超过10万行

**Q: 提示重复键？**
A: Excel第1列有重复值，请检查并去重。

### 5.4 更新问题

**Q: 更新失败了，数据会怎么样？**
A: 更新失败时会自动回滚到初始状态，不用担心数据丢失。但是会保留备份表供检查。

**Q: 如何查看更新失败的记录？**
A: 在「操作日志」标签页点击「导出失败记录」。

**Q: 更新成功后发现改错了怎么办？**
A: 查看日志中的备份表名，手工从备份表恢复数据。

### 5.5 性能问题

**Q: 大数据量更新很慢怎么办？**
A: 建议分批处理，每批不超过1万条。

---

## 6. 最佳实践

### 6.1 操作前准备

1. 在测试环境先验证
2. 备份重要数据
3. 检查Excel数据正确性
4. 确认数据库账号权限

### 6.2 数据更新建议

1. 先小批量测试（几十条数据）
2. 确认没问题再全量更新
3. 操作期间不要关闭程序
4. 保存更新日志

### 6.3 Excel数据建议

1. 使用提供的模板
2. 第一列唯一标识不能为空
3. 数据类型要与数据库一致
4. 避免特殊字符和长文本
5. 使用.xlsx格式

### 6.4 日常维护建议

1. 定期清理历史记录
2. 定期备份配置
3. 保存重要的审计日志
4. 关注日志中的错误和警告

---

## 7. 技术支持

如遇到问题：

1. 查看日志文件（logs目录）
2. 查看本文档的常见问题
3. 查看操作日志排查原因
4. 联系技术支持

---

## 附录

### A. Excel模板说明

Excel包含两个Sheet：
1. **数据更新模板**：数据更新用
   - A列：唯一标识（必填）
   - B列起：待更新列（按需填写）

2. **使用说明**：使用说明和注意事项

### B. 配色说明

**浅色主题：**
- 主色：蓝色 (#4A86E8)
- 背景：浅灰 (#F5F5F5)
- 文字：深灰 (#3C3F41)

**深色主题：**
- 主色：蓝色 (#4A86E8)
- 背景：深灰 (#2B2B2B)
- 文字：浅灰 (#A9B7C6)

---

感谢使用本工具！希望能帮助您高效完成Oracle数据批量更新工作。

---

## 变更历史

| 版本 | 日期 | 说明 |
|-----|------|------|
| v1.0 | 2026-05-15 | 初版 |
| v2.0 | 2026-05-20 | 增加多列更新、状态栏优化 |
'''
    with open('docs/用户手册.md', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ 用户手册.md 已创建')


def create_readme():
    """创建README文档"""
    content = '''# Oracle数据批量修改工具

Oracle Data Batch Modifier - 一款简单易用的Oracle数据库批量更新工具，支持Excel导入、自动备份、失败回滚、审计日志等功能。

## 功能特性

### 核心功能
- ✅ 数据库连接管理（支持多连接配置）
- ✅ Excel数据导入（.xlsx/.xls格式）
- ✅ 数据预览（前50行）
- ✅ 多列同时更新
- ✅ 自动备份机制
- ✅ 失败自动回滚
- ✅ 实时进度显示

### 增强功能
- ✅ 文件大小限制（10MB）
- ✅ 行数限制（10万行）
- ✅ 操作日志记录
- ✅ 审计日志记录
- ✅ 历史记录管理
- ✅ 浅色/深色主题切换（Idea风格）
- ✅ 状态栏显示
- ✅ 快捷键支持（Ctrl+S保存）

## 界面预览

### 主界面
- 标签页式布局
- Idea风格配色
- 状态栏显示连接名、用户、数据库、状态

### 主题
- 浅色主题（默认）
- 深色主题

## 快速开始

### 环境要求
- Windows 7及以上
- Oracle Instant Client 11g+
- Python 3.7+（仅开发时需要）

### 安装步骤

1. **安装Oracle Instant Client**
   - 下载地址：https://www.oracle.com/database/technologies/instant-client/downloads.html
   - 解压并配置PATH环境变量

2. **运行工具**
   - 下载发行版
   - 解压并运行 `OracleBatchUpdater.exe`
   - 或者使用源码运行（见开发章节）

### 使用流程

1. 配置数据库连接
2. 准备Excel数据（使用提供的模板）
3. 选择文件并预览
4. 确认并执行更新
5. 查看日志和结果

## Excel模板格式

使用 `Oracle数据批量修改工具_导入模板.xlsx`：

| EMP_ID (唯一标识) | EMP_NAME | AGE | DEPT |
|------------------|----------|-----|------|
| 1001             | 张三     | 28  | 技术部 |
| 1002             | 李四     | 30  | 市场部 |

## 项目结构

```
Oracle_Table_Change/
├── main.py                      # 入口文件
├── src/
│   ├── __init__.py
│   ├── gui.py                  # GUI界面
│   ├── db_connection.py        # 数据库连接
│   ├── excel_handler.py        # Excel处理
│   ├── data_updater.py         # 数据更新
│   ├── config_manager.py       # 配置管理
│   └── logger.py              # 日志和审计
├── docs/                       # 文档
│   ├── 需求规格说明书.md
│   ├── 设计方案.md
│   ├── 开发方案.md
│   ├── 部署方案.md
│   ├── 用户手册.md
│   └── 代码生成提示词.md
├── Oracle数据批量修改工具_导入模板.xlsx  # Excel模板
├── requirements.txt            # 依赖列表
├── build.bat                  # 构建脚本
├── package.bat                # 打包脚本
└── README.txt                 # 说明
```

## 开发指南

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行

```bash
python main.py
```

### 打包

```bash
# 方式一：使用脚本
package.bat

# 方式二：手动
pyinstaller --clean OracleBatchUpdater.spec
```

打包结果在 `dist/OracleBatchUpdater/` 目录。

## 文档

完整文档在 `docs/` 目录下：

- 📄 需求规格说明书.md - 详细需求说明
- 📄 设计方案.md - 系统设计文档
- 📄 开发方案.md - 开发计划和流程
- 📄 部署方案.md - 部署和安装说明
- 📄 用户手册.md - 用户使用说明
- 📄 代码生成提示词.md - AI代码生成提示词

## 技术栈

- **语言**：Python 3.7+
- **GUI**：tkinter
- **数据库**：oracledb
- **Excel**：openpyxl
- **打包**：PyInstaller

## 安全建议

1. 在测试环境充分验证后再在生产使用
2. 更新前自动备份，失败可回滚
3. 审计日志记录所有操作
4. 定期备份重要数据

## 常见问题

**Q: Excel文件大小有限制吗？**
A: 最大10MB，最多10万行数据。

**Q: 更新失败了怎么办？**
A: 工具会自动回滚到更新前状态，无需担心数据丢失。

**Q: 支持哪些Excel格式？**
A: .xlsx和.xls格式，推荐使用.xlsx。

**Q: 需要安装Oracle Client吗？**
A: 是的，需要安装Oracle Instant Client。

## 许可证

本项目仅供学习和研究使用。

## 贡献

欢迎提出Issue和Pull Request！

## 联系方式

如有问题，请通过GitHub Issue反馈。

---

## 致谢

感谢所有为本项目做出贡献的人！
'''
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ README.md 已创建')


def main():
    """主函数"""
    # 创建docs目录
    os.makedirs('docs', exist_ok=True)
    
    print('开始生成文档...\n')
    
    # 生成各个文档
    create_development_plan()
    create_deployment_plan()
    create_code_prompt()
    create_user_manual()
    create_readme()
    
    print('\n✓ 所有文档生成完成！')
    print('\n生成的文档：')
    print('  - docs/需求规格说明书.md (已存在)')
    print('  - docs/设计方案.md (已存在)')
    print('  - docs/开发方案.md')
    print('  - docs/部署方案.md')
    print('  - docs/代码生成提示词.md')
    print('  - docs/用户手册.md')
    print('  - README.md')


if __name__ == '__main__':
    main()
