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
- ✅ 三套主题风格切换（默认深墨琥珀 🖥，另含 Idea 蓝色 💡、清爽浅色 ✨，各支持深浅色模式）
- ✅ 状态栏显示（连接名、用户、数据库、连接状态、操作状态、操作系统版本）
- ✅ 快捷键支持（Ctrl+S保存）
- ✅ 配置场景保存/加载
- ✅ 键盘导航（←/→切换标签页，↑/↓滚动）
- ✅ 国产化适配（麒麟V10操作系统）
- ✅ 数据验证步骤（先验证后执行）
- ✅ Schema下拉选项可配置+手工填写

### 数据处理特性
- ✅ 空字段保留原值（不更新为NULL）
- ✅ 未匹配记录不更新目标表
- ✅ 临时表和目标表支持不同Schema
- ✅ Easy Connect连接方式（无需配置文件）

## 界面预览

### 主界面
- 标签页式布局
- 深墨琥珀风格配色（默认）
- 状态栏显示连接名、用户、数据库、状态、操作系统版本

### 主题
- **深墨琥珀**：琥珀金配色，灵感源自经典终端界面（默认）
- **Idea 蓝色**：蓝色系配色，灵感源自 IntelliJ IDEA
- **清爽浅色**：蓝白配色，简洁干净
- 每套风格均支持浅色/深色模式，共六种视觉方案

## 系统兼容性

| 发布方式 | Windows 7 | Windows Server 2008 R2 | Windows 10+ | Windows Server 2016+ |
|---------|-----------|------------------------|-------------|----------------------|
| exe打包 | ✅ 支持 | ✅ 支持 | ✅ 支持 | ✅ 支持 |
| 便携版 | ✅ 支持 | ✅ 支持 | ✅ 支持 | ✅ 支持 |
| Docker | ❌ 不支持 | ❌ 不支持 | ✅ 支持 | ✅ 支持 |

**推荐：** Windows 7 和 Windows Server 2008 R2 用户使用 exe打包 或 便携版方式。

## 快速开始

### 环境要求
- Windows 7及以上 / Windows Server 2008 R2及以上 / macOS / Linux / 麒麟V10
- Oracle Instant Client 11g+（或使用已安装的Oracle客户端）
- Python 3.7+（仅开发时需要）

### 安装方式

#### 方式一：exe打包（推荐）

```bash
# 直接运行
OracleBatchUpdater.exe
```

#### 方式二：便携版

```bash
# 解压即用
1. 解压 OracleBatchUpdater_Portable_v2.7.0.zip
2. 双击 OracleBatchUpdater_Portable.bat
```

#### 方式三：Docker（仅适用于 Windows 10+ / Server 2016+）

```bash
docker-compose up -d
# 浏览器访问 http://localhost:6080
```

### 数据库连接

使用 Easy Connect 方式，无需配置文件：

```
连接字符串格式: host:port/service_name
示例: 192.168.1.100:1521/ORCL
```

### 使用流程

1. 配置数据库连接
2. 准备Excel数据（使用提供的模板）
3. 选择文件并预览
4. 点击「验证数据」检查Excel和数据库
5. 验证通过后点击「执行」开始更新
6. 查看日志和结果

## Excel模板格式

使用 `Oracle数据批量修改工具_导入模板.xlsx`：

| EMP_ID (唯一标识) | EMP_NAME | AGE | DEPT |
|------------------|----------|-----|------|
| 1001             | 张三     | 28  | 技术部 |
| 1002             | 李四     | 30  | 市场部 |

**注意：空字段将保留目标表原值，不会被更新为NULL**

## 项目结构

```
Oracle_Table_Change/
├── main.py                      # 入口文件
├── VERSION                      # 版本号文件
├── src/
│   ├── __init__.py
│   ├── gui.py                  # GUI界面（含OS兼容性检测）
│   ├── db_connection.py        # 数据库连接
│   ├── excel_handler.py        # Excel处理
│   ├── data_updater.py         # 数据更新
│   ├── config_manager.py       # 配置管理
│   └── logger.py              # 日志和审计
├── scripts/
│   ├── create_portable.bat     # 便携版打包脚本
│   ├── create_portable.sh      # Linux便携版脚本
│   └── install_oracle_client.sh # Oracle客户端安装
├── docs/                       # 文档
│   ├── 需求规格说明书.md
│   ├── 设计方案.md
│   ├── 开发方案.md
│   ├── 部署方案.md
│   ├── 用户手册.md
│   └── Windows_Server使用指南.md
├── demo.html                   # 前端原型
├── Oracle数据批量修改工具_导入模板.xlsx  # Excel模板
├── requirements.txt            # 依赖列表
├── build.bat                  # 构建脚本
├── package.bat                # 打包脚本
├── Dockerfile                 # Docker镜像
├── docker-compose.yml         # Docker配置
└── README.md                  # 说明
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
4. 密码以编码形式存储在本地配置文件
5. 定期备份重要数据

## 常见问题

**Q: Excel文件大小有限制吗？**
A: 最大10MB，最多10万行数据。

**Q: 更新失败了怎么办？**
A: 工具会自动回滚到更新前状态，无需担心数据丢失。

**Q: 支持哪些Excel格式？**
A: .xlsx和.xls格式，推荐使用.xlsx。不支持.xlsm（宏文件）。

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
