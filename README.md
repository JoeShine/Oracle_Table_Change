# Oracle数据批量修改工具

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
