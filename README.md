# DBForge（v2.9.0 多数据库支持版）

Oracle Data Batch Modifier - 一款简单易用的Oracle数据库批量更新工具，支持Excel导入、自动备份、失败回滚、审计日志等功能。

**当前版本：v2.8.0** | [更新日志](docs/) | [用户手册](docs/用户手册.md) | [CHM 帮助](docs/DBForge_UserManual.chm)

## 功能特性

### 核心功能
- ✅ 连接管理管理（支持多连接配置）
- ✅ 多格式数据导入（.xlsx / .xls / .csv / .json / .jsonl）
- ✅ 数据预览（前50行）
- ✅ 多列同时更新
- ✅ 自动备份机制
- ✅ 失败自动回滚
- ✅ 实时进度显示（含 ETA 预计剩余时间）

### 增强功能
- ✅ 文件大小限制（10MB）
- ✅ 行数限制（10万行；CSV/JSON 流式可达千万行）
- ✅ 运行日志记录
- ✅ 审计日志记录（HMAC-SHA256 链式防篡改）
- ✅ 操作历史管理
- ✅ 三套主题风格切换（默认深墨琥珀 🖥，另含 Idea 蓝色 💡、清爽浅色 ✨，各支持深浅色模式）
- ✅ 状态栏显示（连接名、用户、数据库、连接状态、操作状态、操作系统版本）
- ✅ 快捷键支持（Ctrl+S保存）
- ✅ 配置场景保存/加载
- ✅ 键盘导航（↑/↓切换左侧菜单，←/→滚动内容区）
- ✅ 国产化适配（麒麟V10操作系统）
- ✅ 数据验证步骤（先验证后执行）
- ✅ Schema下拉选项可配置+手工填写

### 数据处理特性
- ✅ 空字段保留原值（不更新为NULL）
- ✅ 未匹配记录不更新目标表
- ✅ 临时表和目标表支持不同Schema
- ✅ Easy Connect连接方式（无需配置文件）
- ✅ MERGE INTO 批量更新（性能 10x~100x 提升）
- ✅ 临时表列类型自动推断（VARCHAR2/NUMBER/DATE/CLOB）

### 安全特性 (v2.8.0)
- ✅ SQL 注入防御：标识符白名单校验 (`sanitize_identifier`)
- ✅ Schema 白名单：仅允许预注册 Schema
- ✅ 密码 Fernet AES-GCM 加密存储
- ✅ 审计日志 HMAC-SHA256 链式签名（防篡改）
- ✅ 单事务回滚语义
- ✅ 9 类结构化异常体系（含 `CancelledError`）

### v2.8.0 新增功能
- ✅ ORA 错误码中文映射（30+ 错误码）
- ✅ CLI 命令行接口（5 个子命令，支持 `--dry-run`）
- ✅ CSV/JSON 流式数据源
- ✅ 操作员身份认证（4 角色 + 双人审批）
- ✅ 连接池（`oracledb.create_pool`）
- ✅ 操作取消机制
- ✅ Service 层解耦（GUI/CLI 共享业务逻辑）
- ✅ 通知系统（钉钉/企业微信/Webhook/邮件）
- ✅ ETA 进度条 + 预计剩余时间
- ✅ 操作历史查询 UI（多条件搜索 + CSV/JSON 导出）
- ✅ 统计分析模块（多维度导入信息统计）
- ✅ DataCompare 表/Excel 对比
- ✅ 诊断包（环境/数据库/配置/日志 四维度）
- ✅ 多环境配置（DEV/TEST/UAT/PROD）
- ✅ 备份生命周期管理
- ✅ 任务调度器（Cron 表达式）
- ✅ 趋势分析（频率/错误/表活动/性能）

## 界面预览

### 主界面
- 左侧纵向导航栏 + 右侧内容区布局
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
DBForge.exe
```

#### 方式二：便携版（无需安装 Python）

```bash
# 解压即用 — 不需要安装 Python，便携版包含 .exe 可执行文件
1. 解压 DBForge_Portable_v2.8.0.zip
2. 双击 DBForge_Portable.bat
3. 或直接运行 App\DBForge.exe
```

> 便携版使用 PyInstaller 打包，Python 运行时已内嵌在 .exe 中，无需额外安装。
> 仅需单独配置 Oracle Instant Client（如尚未安装）。

#### 方式三：Docker（仅适用于 Windows 10+ / Server 2016+）

```bash
docker-compose up -d
# 浏览器访问 http://localhost:6080
```

#### 方式四：CLI 命令行（v2.8.0 新增）

```bash
# 验证导入效果（不实际执行）
python -m src.cli update --connection DEV --table EMPLOYEE \
    --file data.xlsx --key-column EMP_ID \
    --update-columns NAME,AGE,DEPT --dry-run

# 执行批量更新
python -m src.cli update --connection DEV --table EMPLOYEE \
    --file data.csv --key-column EMP_ID \
    --update-columns NAME,AGE --yes

# 验证审计日志完整性
python -m src.cli verify-audit
```

退出码约定：`0=成功, 1=参数错误, 2=连接失败, 3=验证失败, 4=部分失败, 5=全部失败`

### 连接管理

使用 Easy Connect 方式，无需配置文件：

```
连接字符串格式: host:port/service_name
示例: 192.168.1.100:1521/ORCL
```

### 使用流程

1. 配置连接管理
2. 准备Excel数据（使用提供的模板）
3. 选择文件并预览
4. 点击「验证数据」检查Excel和数据库
5. 验证通过后点击「执行」开始更新
6. 查看日志和结果

## Excel模板格式

使用 `DBForge_导入模板.xlsx`：

| EMP_ID (唯一标识) | EMP_NAME | AGE | DEPT |
|------------------|----------|-----|------|
| 1001             | 张三     | 28  | 技术部 |
| 1002             | 李四     | 30  | 市场部 |

**注意：空字段将保留目标表原值，不会被更新为NULL**

## 统计分析 (v2.8.0 新增)

`ImportStats` 类从历史日志自动生成多维度统计报表：

```python
from src.import_stats import ImportStats

stats = ImportStats()

# 总体汇总
summary = stats.overall_summary(days=30)
print(f"30天共 {summary['total_operations']} 次操作，成功率 {summary['success_rate']}%")

# 按 Schema/表/时间分组
by_schema = stats.group_by_schema(days=30)
by_table = stats.group_by_table(days=30, top_n=10)
by_day = stats.group_by_time_bucket(days=30, bucket="day")

# 错误分布 & 数据质量
errors = stats.error_distribution(days=30)
quality = stats.data_quality_metrics(days=30)
print(f"数据质量等级: {quality['quality_grade']}")

# 导出报表
stats.export_report("report.html", days=30, fmt="html")
stats.export_report("report.json", days=30, fmt="json")
```

支持的报表格式：`text` / `html` / `json`，覆盖 7 个维度：总体、Schema、表、时间、错误、状态、质量。

## 项目结构

```
Oracle_Table_Change/
├── main.py                      # 入口文件
├── VERSION                      # 版本号文件 (2.8.0)
├── src/
│   ├── __init__.py
│   ├── gui.py                   # GUI 界面
│   ├── db_connection.py         # 连接管理 + 连接池 + 权限预检
│   ├── excel_handler.py         # Excel 处理
│   ├── data_updater.py          # 数据更新 (MERGE INTO + 取消机制)
│   ├── config_manager.py        # 配置管理 (Fernet 加密)
│   ├── logger.py                # 日志 + HMAC 审计
│   ├── security.py              # 标识符白名单 (P0-1)
│   ├── errors.py                # 结构化异常体系
│   ├── constants.py             # 集中常量 (P2-2)
│   ├── progress.py              # ETA 进度条 (P2-3)
│   ├── ora_errors.py            # ORA 错误码中文映射 (P1-6)
│   ├── data_source.py           # CSV/JSON/Excel 数据源 (P1-5)
│   ├── auth.py                  # 角色/审批/风险评估 (P1-4)
│   ├── cli.py                   # CLI 命令行 (P1-3)
│   ├── notification.py          # 通知系统 (P2-9)
│   ├── service/__init__.py      # Service 层 (P2-1)
│   ├── history_viewer.py        # 操作历史查询 (P2-4)
│   ├── import_stats.py          # 统计分析 (P-Stats)
│   ├── data_compare.py          # 表/Excel 对比 (P3-1)
│   ├── diagnostics.py           # 诊断包 (P3-2)
│   ├── env_config.py            # 多环境配置 (P3-3)
│   ├── backup_manager.py        # 备份生命周期 (P3-4)
│   ├── scheduler.py             # 任务调度 (P3-5)
│   └── trend_analysis.py        # 趋势分析 (P3-6)
├── test_*.py                    # 104+ 项单元测试
├── scripts/
│   ├── create_portable.bat     # 便携版打包脚本
│   ├── create_portable.sh      # Linux便携版脚本
│   └── install_oracle_client.sh # Oracle客户端安装
├── docs/                        # 文档
│   ├── 需求规格说明书.md
│   ├── 设计方案.md
│   ├── 开发方案.md
│   ├── 部署方案.md
│   ├── 用户手册.md
│   └── Windows_Server使用指南.md
├── demo.html                    # 前端原型
├── DBForge_导入模板.xlsx  # Excel模板
├── requirements.txt             # 依赖列表
├── build.bat                    # 构建脚本
├── package.bat                  # 打包脚本
├── Dockerfile                   # Docker镜像
├── docker-compose.yml           # Docker配置
└── README.md                    # 说明
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
pyinstaller --clean DBForge.spec
```

打包结果在 `dist/DBForge/` 目录。

### 运行测试

```bash
# 全部测试
python -m pytest test_*.py -v

# 仅安全测试 (P0)
python -m pytest test_p0_security.py -v

# 仅统计模块
python -m pytest test_import_stats.py -v
```

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
- **数据库**：oracledb (含连接池)
- **Excel**：openpyxl
- **打包**：PyInstaller
- **加密**：cryptography (Fernet AES-GCM)
- **调度**：croniter (可选)

## 安全建议

1. 在测试环境充分验证后再在生产使用
2. 更新前自动备份，失败可回滚
3. 审计日志使用 HMAC-SHA256 链式签名，**任何篡改都会被检测**
4. 密码使用 **Fernet AES-GCM 加密** 存储在本地配置文件
5. 高风险操作（生产环境、大批量）需要 **双人审批**
6. 定期使用 `python -m src.cli verify-audit` 验证审计日志完整性
7. 定期使用 `BackupManager.cleanup_old_backups()` 清理过期备份

## 常见问题

**Q: Excel文件大小有限制吗？**
A: 最大10MB，最多10万行数据。CSV/JSON 支持流式读取，可达千万行。

**Q: 更新失败了怎么办？**
A: 工具自动使用单事务模式，失败时 `connection.rollback()` 天然恢复，备份表保留供人工恢复。

**Q: 支持哪些数据格式？**
A: .xlsx / .xls / .csv / .json / .jsonl 五种格式。

**Q: 需要安装Oracle Client吗？**
A: 是的，需要安装Oracle Instant Client。

**Q: 如何生成导入统计报表？**
A: 使用 `ImportStats` 类，详见 [统计分析](#统计分析-v280-新增) 章节。

**Q: 如何集成到 CI/CD 流水线？**
A: 使用 `python -m src.cli update` 命令行模式，退出码可被 CI 捕获。

**Q: CHM 帮助手册打开后显示空白？**
A: 这是 Windows 安全机制，对下载文件附加了 Zone.Identifier 标记。解决方法：
1. 从 ZIP 包解压（推荐）— `DBForge_UserManual.zip` 解压后自动解除锁定
2. 运行修复脚本 — `chm_unblock.bat`（Win7）或 `chm_unblock.ps1`（Win10/11）
3. 手动解除 — 右键 .chm → 属性 → 勾选「解除锁定」→ 确定

**Q: CHM 在网络共享文件夹中打不开？**
A: Windows 默认阻止从网络路径打开 CHM，请先复制到本地磁盘（C:\ 或 D:\）。

**Q: exe 文件双击后弹出警告，确认后无法打开？**
A: 这是 Windows 安全机制（SmartScreen 或下载标记）。解决方法：
1. 右键 exe → 属性 → 勾选「解除锁定」→ 确定
2. 或将 exe 放在不含中文/特殊字符的短路径中（如 `C:\Tools\DBForge.exe`）
3. 如弹出"Windows 保护了你的电脑"，点击「更多信息」→「仍要运行」

**Q: 弹出 "启动失败 - 缺少依赖" 错误？**
A: 确保以下文件与 exe 在同一目录或 `src/` 子目录中：
- `src/` 目录（包含所有 .py 模块）
- 如仍失败，请安装 Python 3.7+ 后运行 `pip install -r requirements.txt` 再执行 `python main.py`

## 许可证

本项目仅供学习和研究使用。

## 贡献

欢迎提出Issue和Pull Request！

## 联系方式

如有问题，请通过GitHub Issue反馈。
